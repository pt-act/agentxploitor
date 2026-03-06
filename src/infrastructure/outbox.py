"""
Outbox Pattern

Reliable event publishing with the outbox pattern.
Ensures state changes and events are written atomically.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from enum import Enum

from infrastructure.database import DatabasePool, get_db_pool

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Domain event types."""
    JOB_CREATED = "job_created"
    JOB_STATE_CHANGED = "job_state_changed"
    PAYMENT_VERIFIED = "payment_verified"
    SCAN_STARTED = "scan_started"
    FINDING_DISCOVERED = "finding_discovered"
    EXPLOIT_GENERATED = "exploit_generated"
    VERIFICATION_COMPLETED = "verification_completed"
    REPORT_FINALIZED = "report_finalized"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"


@dataclass
class OutboxEvent:
    """Event stored in outbox."""
    id: Optional[int] = None
    aggregate_type: str = ""
    aggregate_id: str = ""
    event_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    destination: str = "default"
    published: bool = False
    published_at: Optional[str] = None
    retry_count: int = 0
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'aggregate_type': self.aggregate_type,
            'aggregate_id': self.aggregate_id,
            'event_type': self.event_type,
            'payload': self.payload,
            'destination': self.destination,
            'published': self.published,
            'published_at': self.published_at,
            'retry_count': self.retry_count,
            'error': self.error,
            'created_at': self.created_at,
        }


class OutboxWriter:
    """
    Write events to outbox atomically with state changes.
    
    Usage:
        async with outbox.transaction() as tx:
            await tx.execute("UPDATE jobs SET status = $1", "in_progress")
            await tx.write_event(
                aggregate_type="job",
                aggregate_id=job_id,
                event_type=EventType.JOB_STATE_CHANGED,
                payload={"from": "queued", "to": "in_progress"}
            )
    """
    
    def __init__(self, db: Optional[DatabasePool] = None):
        self._db = db
        self._conn = None
        self._tx = None
        self._events: List[OutboxEvent] = []
    
    @property
    def db(self) -> DatabasePool:
        if self._db is None:
            self._db = get_db_pool()
        return self._db
    
    async def transaction(self):
        """Start a new transaction context."""
        self._conn = await self.db.pool.acquire()
        self._tx = self._conn.transaction()
        await self._tx.start()
        return self
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query within the transaction."""
        if not self._conn:
            raise RuntimeError("No active transaction")
        return await self._conn.execute(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch a row within the transaction."""
        if not self._conn:
            raise RuntimeError("No active transaction")
        row = await self._conn.fetchrow(query, *args)
        return dict(row) if row else None
    
    async def write_event(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: EventType,
        payload: Dict[str, Any],
        destination: str = "default",
    ) -> OutboxEvent:
        """Write event to outbox within the transaction."""
        if not self._conn:
            raise RuntimeError("No active transaction")
        
        event = OutboxEvent(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type.value,
            payload=payload,
            destination=destination,
        )
        
        result = await self._conn.fetchrow(
            """
            INSERT INTO outbox 
                (aggregate_type, aggregate_id, event_type, payload, destination)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            event.aggregate_type,
            event.aggregate_id,
            event.event_type,
            json.dumps(event.payload),
            event.destination,
        )
        
        event.id = result['id']
        self._events.append(event)
        
        return event
    
    async def commit(self) -> List[OutboxEvent]:
        """Commit the transaction and return events."""
        if not self._tx:
            raise RuntimeError("No active transaction")
        
        await self._tx.commit()
        await self.db.pool.release(self._conn)
        
        events = self._events.copy()
        self._events = []
        self._conn = None
        self._tx = None
        
        return events
    
    async def rollback(self) -> None:
        """Rollback the transaction."""
        if not self._tx:
            raise RuntimeError("No active transaction")
        
        await self._tx.rollback()
        await self.db.pool.release(self._conn)
        
        self._events = []
        self._conn = None
        self._tx = None
    
    async def __aenter__(self) -> 'OutboxWriter':
        await self.transaction()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        return False


class OutboxProcessor:
    """
    Process unpublished events from outbox.
    
    Publishes events to handlers and marks them as published.
    """
    
    def __init__(
        self,
        db: Optional[DatabasePool] = None,
        batch_size: int = 100,
        max_retries: int = 10,
    ):
        self._db = db
        self._batch_size = batch_size
        self._max_retries = max_retries
        self._handlers: Dict[str, List[Callable]] = {}
        self._running = False
    
    @property
    def db(self) -> DatabasePool:
        if self._db is None:
            self._db = get_db_pool()
        return self._db
    
    def register_handler(
        self,
        event_type: str,
        handler: Callable[[OutboxEvent], Any],
    ) -> None:
        """Register a handler for an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def fetch_unpublished(self) -> List[OutboxEvent]:
        """Fetch unpublished events."""
        rows = await self.db.fetch(
            """
            SELECT * FROM outbox
            WHERE published = FALSE AND retry_count < $1
            ORDER BY created_at ASC
            LIMIT $2
            """,
            self._max_retries,
            self._batch_size,
        )
        
        return [
            OutboxEvent(
                id=row['id'],
                aggregate_type=row['aggregate_type'],
                aggregate_id=row['aggregate_id'],
                event_type=row['event_type'],
                payload=row['payload'],
                destination=row['destination'],
                published=row['published'],
                published_at=row['published_at'],
                retry_count=row['retry_count'],
                error=row['error'],
                created_at=row['created_at'].isoformat() if row['created_at'] else None,
            )
            for row in rows
        ]
    
    async def publish_event(self, event: OutboxEvent) -> bool:
        """Publish event to handlers."""
        handlers = self._handlers.get(event.event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers for event type: {event.event_type}")
            return True
        
        try:
            for handler in handlers:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            
            await self._mark_published(event.id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.id}: {e}")
            await self._mark_failed(event.id, str(e))
            return False
    
    async def _mark_published(self, event_id: int) -> None:
        """Mark event as published."""
        await self.db.execute(
            """
            UPDATE outbox
            SET published = TRUE, published_at = NOW()
            WHERE id = $1
            """,
            event_id,
        )
    
    async def _mark_failed(self, event_id: int, error: str) -> None:
        """Mark event as failed with error."""
        await self.db.execute(
            """
            UPDATE outbox
            SET retry_count = retry_count + 1, error = $2
            WHERE id = $1
            """,
            event_id,
            error,
        )
    
    async def process_batch(self) -> int:
        """Process a batch of unpublished events."""
        events = await self.fetch_unpublished()
        
        published = 0
        for event in events:
            if await self.publish_event(event):
                published += 1
        
        return published
    
    async def run(self, interval: float = 1.0) -> None:
        """Run processor loop."""
        self._running = True
        
        while self._running:
            try:
                published = await self.process_batch()
                if published == 0:
                    await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Outbox processor error: {e}")
                await asyncio.sleep(interval)
    
    def stop(self) -> None:
        """Stop the processor."""
        self._running = False


_outbox_writer: Optional[OutboxWriter] = None
_outbox_processor: Optional[OutboxProcessor] = None


def get_outbox_writer() -> OutboxWriter:
    """Get global outbox writer instance."""
    global _outbox_writer
    if _outbox_writer is None:
        _outbox_writer = OutboxWriter()
    return _outbox_writer


def get_outbox_processor() -> OutboxProcessor:
    """Get global outbox processor instance."""
    global _outbox_processor
    if _outbox_processor is None:
        _outbox_processor = OutboxProcessor()
    return _outbox_processor
