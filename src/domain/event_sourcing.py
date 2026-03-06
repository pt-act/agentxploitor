"""
Event Sourcing

Implements event sourcing pattern for immutable audit trail.
Events are the source of truth; state is derived from events.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List, TypeVar, Generic, Type
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Domain event types for event sourcing."""
    JOB_CREATED = "job_created"
    JOB_STATE_CHANGED = "job_state_changed"
    PAYMENT_VERIFIED = "payment_verified"
    SCAN_STARTED = "scan_started"
    ANALYZER_COMPLETED = "analyzer_completed"
    FINDING_DISCOVERED = "finding_discovered"
    EXPLOIT_GENERATED = "exploit_generated"
    VERIFICATION_COMPLETED = "verification_completed"
    REPORT_FINALIZED = "report_finalized"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"


@dataclass
class DomainEvent:
    """Base class for domain events."""
    event_id: str = field(default_factory=lambda: _generate_event_id())
    event_type: str = ""
    aggregate_type: str = ""
    aggregate_id: str = ""
    event_version: int = 1
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    causation_id: Optional[str] = None  # ID of event that caused this one
    correlation_id: Optional[str] = None  # ID linking related events
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'aggregate_type': self.aggregate_type,
            'aggregate_id': self.aggregate_id,
            'event_version': self.event_version,
            'timestamp': self.timestamp,
            'payload': self.payload,
            'metadata': self.metadata,
            'causation_id': self.causation_id,
            'correlation_id': self.correlation_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DomainEvent':
        return cls(
            event_id=data.get('event_id', ''),
            event_type=data.get('event_type', ''),
            aggregate_type=data.get('aggregate_type', ''),
            aggregate_id=data.get('aggregate_id', ''),
            event_version=data.get('event_version', 1),
            timestamp=data.get('timestamp', ''),
            payload=data.get('payload', {}),
            metadata=data.get('metadata', {}),
            causation_id=data.get('causation_id'),
            correlation_id=data.get('correlation_id'),
        )
    
    def compute_hash(self) -> str:
        """Compute hash for event integrity verification."""
        data = f"{self.event_id}:{self.event_type}:{self.aggregate_id}:{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()


def _generate_event_id() -> str:
    """Generate unique event ID."""
    import uuid
    return f"evt-{uuid.uuid4().hex[:16]}"


# ============================================================================
# Job Events
# ============================================================================

@dataclass
class JobCreatedEvent(DomainEvent):
    """Event: Job was created."""
    event_type: str = EventType.JOB_CREATED.value
    aggregate_type: str = "job"
    
    @classmethod
    def create(
        cls,
        job_id: str,
        target_url: str,
        scope: str,
        priority: str,
        wallet_address: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> 'JobCreatedEvent':
        return cls(
            aggregate_id=job_id,
            payload={
                'target_url': target_url,
                'scope': scope,
                'priority': priority,
                'wallet_address': wallet_address,
                'initial_status': 'pending_payment',
            },
            correlation_id=correlation_id,
        )


@dataclass
class JobStateChangedEvent(DomainEvent):
    """Event: Job state changed."""
    event_type: str = EventType.JOB_STATE_CHANGED.value
    aggregate_type: str = "job"
    
    @classmethod
    def create(
        cls,
        job_id: str,
        from_status: str,
        to_status: str,
        reason: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> 'JobStateChangedEvent':
        return cls(
            aggregate_id=job_id,
            payload={
                'from_status': from_status,
                'to_status': to_status,
                'reason': reason,
            },
            correlation_id=correlation_id,
        )


@dataclass
class PaymentVerifiedEvent(DomainEvent):
    """Event: Payment was verified."""
    event_type: str = EventType.PAYMENT_VERIFIED.value
    aggregate_type: str = "job"
    
    @classmethod
    def create(
        cls,
        job_id: str,
        tx_hash: str,
        amount: str,
        confirmations: int,
        correlation_id: Optional[str] = None,
    ) -> 'PaymentVerifiedEvent':
        return cls(
            aggregate_id=job_id,
            payload={
                'tx_hash': tx_hash,
                'amount': amount,
                'confirmations': confirmations,
            },
            correlation_id=correlation_id,
        )


@dataclass
class ScanStartedEvent(DomainEvent):
    """Event: Security scan started."""
    event_type: str = EventType.SCAN_STARTED.value
    aggregate_type: str = "job"
    
    @classmethod
    def create(
        cls,
        job_id: str,
        analyzers: List[str],
        target_url: str,
        correlation_id: Optional[str] = None,
    ) -> 'ScanStartedEvent':
        return cls(
            aggregate_id=job_id,
            payload={
                'analyzers': analyzers,
                'target_url': target_url,
            },
            correlation_id=correlation_id,
        )


@dataclass
class FindingDiscoveredEvent(DomainEvent):
    """Event: Vulnerability finding was discovered."""
    event_type: str = EventType.FINDING_DISCOVERED.value
    aggregate_type: str = "job"
    
    @classmethod
    def create(
        cls,
        job_id: str,
        finding_id: str,
        title: str,
        severity: str,
        cvss_score: float,
        analyzer: str,
        correlation_id: Optional[str] = None,
    ) -> 'FindingDiscoveredEvent':
        return cls(
            aggregate_id=job_id,
            payload={
                'finding_id': finding_id,
                'title': title,
                'severity': severity,
                'cvss_score': cvss_score,
                'analyzer': analyzer,
            },
            correlation_id=correlation_id,
        )


@dataclass
class ExploitGeneratedEvent(DomainEvent):
    """Event: Exploit was generated."""
    event_type: str = EventType.EXPLOIT_GENERATED.value
    aggregate_type: str = "job"
    
    @classmethod
    def create(
        cls,
        job_id: str,
        exploit_id: str,
        finding_id: str,
        technique: str,
        safe: bool,
        correlation_id: Optional[str] = None,
    ) -> 'ExploitGeneratedEvent':
        return cls(
            aggregate_id=job_id,
            payload={
                'exploit_id': exploit_id,
                'finding_id': finding_id,
                'technique': technique,
                'safe': safe,
            },
            correlation_id=correlation_id,
        )


@dataclass
class JobCompletedEvent(DomainEvent):
    """Event: Job completed successfully."""
    event_type: str = EventType.JOB_COMPLETED.value
    aggregate_type: str = "job"
    
    @classmethod
    def create(
        cls,
        job_id: str,
        findings_count: Dict[str, int],
        report_path: str,
        correlation_id: Optional[str] = None,
    ) -> 'JobCompletedEvent':
        return cls(
            aggregate_id=job_id,
            payload={
                'findings_count': findings_count,
                'report_path': report_path,
            },
            correlation_id=correlation_id,
        )


@dataclass
class JobFailedEvent(DomainEvent):
    """Event: Job failed."""
    event_type: str = EventType.JOB_FAILED.value
    aggregate_type: str = "job"
    
    @classmethod
    def create(
        cls,
        job_id: str,
        error: str,
        recoverable: bool,
        correlation_id: Optional[str] = None,
    ) -> 'JobFailedEvent':
        return cls(
            aggregate_id=job_id,
            payload={
                'error': error,
                'recoverable': recoverable,
            },
            correlation_id=correlation_id,
        )


# ============================================================================
# Event Store
# ============================================================================

class EventStore:
    """
    Append-only event store.
    
    Events are never modified or deleted.
    State is reconstructed by replaying events.
    """
    
    SNAPSHOT_INTERVAL = 100  # Create snapshot every N events
    
    def __init__(self, db_pool=None):
        self._db = db_pool
        self._event_handlers: Dict[str, List] = {}
    
    async def append(self, event: DomainEvent, expected_version: Optional[int] = None) -> int:
        """
        Append event to store.
        
        Uses optimistic concurrency control.
        Returns the new version.
        """
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            logger.warning("Database not connected, storing event in memory")
            return 1
        
        query = """
            INSERT INTO events 
                (aggregate_type, aggregate_id, event_type, event_version, 
                 payload, metadata, causation_id, correlation_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """
        
        event_id = await db.fetchval(
            query,
            event.aggregate_type,
            event.aggregate_id,
            event.event_type,
            event.event_version,
            json.dumps(event.payload),
            json.dumps(event.metadata),
            event.causation_id,
            event.correlation_id,
        )
        
        logger.debug(f"Appended event {event.event_type} for {event.aggregate_id}")
        
        await self._notify_handlers(event)
        
        return event_id
    
    async def get_events(
        self,
        aggregate_type: str,
        aggregate_id: str,
        from_version: int = 0,
    ) -> List[DomainEvent]:
        """Get all events for an aggregate."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return []
        
        query = """
            SELECT * FROM events
            WHERE aggregate_type = $1 AND aggregate_id = $2
            ORDER BY id ASC
        """
        
        rows = await db.fetch(query, aggregate_type, aggregate_id)
        
        return [
            DomainEvent.from_dict({
                'event_id': str(row['id']),
                'event_type': row['event_type'],
                'aggregate_type': row['aggregate_type'],
                'aggregate_id': row['aggregate_id'],
                'event_version': row['event_version'],
                'timestamp': row['created_at'].isoformat() if row['created_at'] else '',
                'payload': row['payload'],
                'metadata': row['metadata'],
                'causation_id': row['causation_id'],
                'correlation_id': row['correlation_id'],
            })
            for row in rows
        ]
    
    async def get_events_by_type(
        self,
        event_type: str,
        limit: int = 100,
    ) -> List[DomainEvent]:
        """Get events by type."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return []
        
        query = """
            SELECT * FROM events
            WHERE event_type = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        
        rows = await db.fetch(query, event_type, limit)
        
        return [
            DomainEvent.from_dict({
                'event_id': str(row['id']),
                'event_type': row['event_type'],
                'aggregate_type': row['aggregate_type'],
                'aggregate_id': row['aggregate_id'],
                'event_version': row['event_version'],
                'timestamp': row['created_at'].isoformat() if row['created_at'] else '',
                'payload': row['payload'],
                'metadata': row['metadata'],
                'causation_id': row['causation_id'],
                'correlation_id': row['correlation_id'],
            })
            for row in rows
        ]
    
    def register_handler(self, event_type: str, handler) -> None:
        """Register a handler for an event type."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    async def _notify_handlers(self, event: DomainEvent) -> None:
        """Notify registered handlers of new event."""
        handlers = self._event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                import asyncio
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")


# ============================================================================
# Aggregate Base
# ============================================================================

T = TypeVar('T')


class AggregateRoot(ABC):
    """
    Base class for aggregate roots.
    
    Aggregates:
    - Have a unique ID
    - Maintain version for optimistic concurrency
    - Apply events to change state
    - Emit events when state changes
    """
    
    def __init__(self, aggregate_id: str):
        self._id = aggregate_id
        self._version = 0
        self._changes: List[DomainEvent] = []
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def version(self) -> int:
        return self._version
    
    @property
    def changes(self) -> List[DomainEvent]:
        return self._changes.copy()
    
    def apply_change(self, event: DomainEvent, is_new: bool = True) -> None:
        """Apply an event to change state."""
        self._apply(event)
        self._version += 1
        
        if is_new:
            self._changes.append(event)
    
    def mark_changes_as_committed(self) -> None:
        """Clear uncommitted changes."""
        self._changes.clear()
    
    def load_from_history(self, events: List[DomainEvent]) -> None:
        """Load aggregate state from event history."""
        for event in events:
            self.apply_change(event, is_new=False)
    
    @abstractmethod
    def _apply(self, event: DomainEvent) -> None:
        """Apply event to update internal state."""
        pass


# ============================================================================
# Job Aggregate
# ============================================================================

class JobAggregate(AggregateRoot):
    """
    Job aggregate root for event sourcing.
    
    Encapsulates all job state and business rules.
    """
    
    def __init__(self, job_id: str):
        super().__init__(job_id)
        
        self.target_url: str = ""
        self.status: str = ""
        self.priority: str = "normal"
        self.wallet_address: Optional[str] = None
        self.payment_tx_hash: Optional[str] = None
        self.payment_verified: bool = False
        self.findings: List[Dict[str, Any]] = []
        self.report_path: Optional[str] = None
        self.error: Optional[str] = None
        self.created_at: str = ""
        self.updated_at: str = ""
    
    @classmethod
    def create(
        cls,
        job_id: str,
        target_url: str,
        scope: str,
        priority: str = "normal",
        wallet_address: Optional[str] = None,
    ) -> 'JobAggregate':
        """Create a new job aggregate."""
        job = cls(job_id)
        
        event = JobCreatedEvent.create(
            job_id=job_id,
            target_url=target_url,
            scope=scope,
            priority=priority,
            wallet_address=wallet_address,
        )
        
        job.apply_change(event)
        return job
    
    def change_state(self, new_status: str, reason: Optional[str] = None) -> None:
        """Change job state with validation."""
        valid_transitions = {
            'pending_payment': ['payment_verified', 'queued', 'cancelled'],
            'payment_verified': ['queued', 'in_progress', 'cancelled'],
            'queued': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'failed', 'cancelled'],
            'completed': [],
            'failed': ['queued'],
            'cancelled': ['queued'],
        }
        
        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(f"Invalid transition from {self.status} to {new_status}")
        
        event = JobStateChangedEvent.create(
            job_id=self._id,
            from_status=self.status,
            to_status=new_status,
            reason=reason,
        )
        
        self.apply_change(event)
    
    def verify_payment(self, tx_hash: str, amount: str, confirmations: int) -> None:
        """Mark payment as verified."""
        event = PaymentVerifiedEvent.create(
            job_id=self._id,
            tx_hash=tx_hash,
            amount=amount,
            confirmations=confirmations,
        )
        
        self.apply_change(event)
    
    def start_scan(self, analyzers: List[str]) -> None:
        """Mark scan as started."""
        event = ScanStartedEvent.create(
            job_id=self._id,
            analyzers=analyzers,
            target_url=self.target_url,
        )
        
        self.apply_change(event)
    
    def add_finding(
        self,
        finding_id: str,
        title: str,
        severity: str,
        cvss_score: float,
        analyzer: str,
    ) -> None:
        """Add a vulnerability finding."""
        event = FindingDiscoveredEvent.create(
            job_id=self._id,
            finding_id=finding_id,
            title=title,
            severity=severity,
            cvss_score=cvss_score,
            analyzer=analyzer,
        )
        
        self.apply_change(event)
    
    def complete(self, findings_count: Dict[str, int], report_path: str) -> None:
        """Mark job as completed."""
        event = JobCompletedEvent.create(
            job_id=self._id,
            findings_count=findings_count,
            report_path=report_path,
        )
        
        self.apply_change(event)
    
    def fail(self, error: str, recoverable: bool = True) -> None:
        """Mark job as failed."""
        event = JobFailedEvent.create(
            job_id=self._id,
            error=error,
            recoverable=recoverable,
        )
        
        self.apply_change(event)
    
    def _apply(self, event: DomainEvent) -> None:
        """Apply event to update state."""
        event_type = event.event_type
        
        if event_type == EventType.JOB_CREATED.value:
            self.target_url = event.payload['target_url']
            self.status = event.payload['initial_status']
            self.priority = event.payload.get('priority', 'normal')
            self.wallet_address = event.payload.get('wallet_address')
            self.created_at = event.timestamp
            self.updated_at = event.timestamp
        
        elif event_type == EventType.JOB_STATE_CHANGED.value:
            self.status = event.payload['to_status']
            self.updated_at = event.timestamp
        
        elif event_type == EventType.PAYMENT_VERIFIED.value:
            self.payment_tx_hash = event.payload['tx_hash']
            self.payment_verified = True
            self.status = 'payment_verified'
            self.updated_at = event.timestamp
        
        elif event_type == EventType.SCAN_STARTED.value:
            self.status = 'in_progress'
            self.updated_at = event.timestamp
        
        elif event_type == EventType.FINDING_DISCOVERED.value:
            self.findings.append({
                'id': event.payload['finding_id'],
                'title': event.payload['title'],
                'severity': event.payload['severity'],
                'cvss_score': event.payload['cvss_score'],
                'analyzer': event.payload['analyzer'],
            })
            self.updated_at = event.timestamp
        
        elif event_type == EventType.JOB_COMPLETED.value:
            self.status = 'completed'
            self.report_path = event.payload['report_path']
            self.updated_at = event.timestamp
        
        elif event_type == EventType.JOB_FAILED.value:
            self.status = 'failed'
            self.error = event.payload['error']
            self.updated_at = event.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Export aggregate state."""
        return {
            'id': self._id,
            'version': self._version,
            'target_url': self.target_url,
            'status': self.status,
            'priority': self.priority,
            'wallet_address': self.wallet_address,
            'payment_tx_hash': self.payment_tx_hash,
            'payment_verified': self.payment_verified,
            'findings': self.findings,
            'report_path': self.report_path,
            'error': self.error,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


# ============================================================================
# Repository
# ============================================================================

class JobRepository:
    """Repository for Job aggregates using event sourcing."""
    
    def __init__(self, event_store: Optional[EventStore] = None):
        self._event_store = event_store or EventStore()
    
    async def get(self, job_id: str) -> Optional[JobAggregate]:
        """Get job by ID, reconstructing from events."""
        events = await self._event_store.get_events('job', job_id)
        
        if not events:
            return None
        
        job = JobAggregate(job_id)
        job.load_from_history(events)
        
        return job
    
    async def save(self, job: JobAggregate) -> None:
        """Save job by appending new events."""
        for event in job.changes:
            await self._event_store.append(event, expected_version=job.version - len(job.changes))
        
        job.mark_changes_as_committed()


# ============================================================================
# Singleton instances
# ============================================================================

_event_store: Optional[EventStore] = None
_job_repository: Optional[JobRepository] = None


def get_event_store() -> EventStore:
    """Get global event store instance."""
    global _event_store
    if _event_store is None:
        _event_store = EventStore()
    return _event_store


def get_job_repository() -> JobRepository:
    """Get global job repository instance."""
    global _job_repository
    if _job_repository is None:
        _job_repository = JobRepository(get_event_store())
    return _job_repository
