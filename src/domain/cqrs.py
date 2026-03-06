"""
CQRS - Command Query Responsibility Segregation

Separates read models (optimized for queries) from write models (event-sourced).
Projections update read models in response to events.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, TypeVar, Generic
from enum import Enum

from domain.event_sourcing import (
    DomainEvent,
    EventType,
    EventStore,
    get_event_store,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Read Models
# ============================================================================

@dataclass
class JobReadModel:
    """
    Denormalized read model for Job queries.
    
    Optimized for:
    - Listing jobs by status/workspace
    - Quick status checks
    - Dashboard displays
    """
    id: str
    workspace_id: Optional[str] = None
    target_url: str = ""
    status: str = ""
    priority: str = "normal"
    
    wallet_address: Optional[str] = None
    payment_verified: bool = False
    
    findings_count: Dict[str, int] = field(default_factory=dict)
    critical_findings: int = 0
    high_findings: int = 0
    
    created_at: str = ""
    updated_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    error: Optional[str] = None
    report_path: Optional[str] = None
    
    version: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'target_url': self.target_url,
            'status': self.status,
            'priority': self.priority,
            'wallet_address': self.wallet_address,
            'payment_verified': self.payment_verified,
            'findings_count': self.findings_count,
            'critical_findings': self.critical_findings,
            'high_findings': self.high_findings,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'error': self.error,
            'report_path': self.report_path,
            'version': self.version,
        }


@dataclass
class FindingReadModel:
    """
    Read model for vulnerability findings.
    
    Optimized for:
    - Finding by severity
    - Full-text search
    - Assignment tracking
    """
    id: str
    job_id: str
    workspace_id: Optional[str] = None
    
    title: str = ""
    description: str = ""
    severity: str = "MEDIUM"
    cvss_score: float = 5.0
    
    location: str = ""
    analyzer: str = ""
    confidence: float = 1.0
    
    status: str = "open"
    assigned_to: Optional[str] = None
    
    exploit_generated: bool = False
    verification_status: Optional[str] = None
    
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'job_id': self.job_id,
            'workspace_id': self.workspace_id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'cvss_score': self.cvss_score,
            'location': self.location,
            'analyzer': self.analyzer,
            'confidence': self.confidence,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'exploit_generated': self.exploit_generated,
            'verification_status': self.verification_status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


@dataclass
class WorkspaceReadModel:
    """
    Read model for workspace/team.
    """
    id: str
    name: str = ""
    slug: str = ""
    member_count: int = 0
    job_count: int = 0
    active_jobs: int = 0
    created_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'member_count': self.member_count,
            'job_count': self.job_count,
            'active_jobs': self.active_jobs,
            'created_at': self.created_at,
        }


# ============================================================================
# Projections
# ============================================================================

class Projection(ABC):
    """
    Base class for projections.
    
    Projections:
    - Subscribe to events
    - Update read models in response
    - Can be rebuilt from event history
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Projection name for logging."""
        pass
    
    @property
    @abstractmethod
    def subscribed_events(self) -> List[str]:
        """Events this projection handles."""
        pass
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle an event and update read model."""
        pass
    
    @abstractmethod
    async def rebuild(self) -> None:
        """Rebuild projection from all events."""
        pass


class JobProjection(Projection):
    """
    Projection for Job read models.
    
    Handles all job-related events to maintain denormalized view.
    """
    
    NAME = "job_projection"
    
    def __init__(self, db_pool=None, event_store: Optional[EventStore] = None):
        self._db = db_pool
        self._event_store = event_store or get_event_store()
        self._cache: Dict[str, JobReadModel] = {}
    
    @property
    def name(self) -> str:
        return self.NAME
    
    @property
    def subscribed_events(self) -> List[str]:
        return [
            EventType.JOB_CREATED.value,
            EventType.JOB_STATE_CHANGED.value,
            EventType.PAYMENT_VERIFIED.value,
            EventType.SCAN_STARTED.value,
            EventType.FINDING_DISCOVERED.value,
            EventType.JOB_COMPLETED.value,
            EventType.JOB_FAILED.value,
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        """Handle event and update read model."""
        job_id = event.aggregate_id
        
        if event.event_type == EventType.JOB_CREATED.value:
            read_model = JobReadModel(
                id=job_id,
                target_url=event.payload.get('target_url', ''),
                status=event.payload.get('initial_status', 'pending_payment'),
                priority=event.payload.get('priority', 'normal'),
                wallet_address=event.payload.get('wallet_address'),
                created_at=event.timestamp,
                updated_at=event.timestamp,
                version=1,
            )
            await self._save(read_model)
        
        elif event.event_type == EventType.JOB_STATE_CHANGED.value:
            read_model = await self._get(job_id)
            if read_model:
                read_model.status = event.payload.get('to_status', '')
                read_model.updated_at = event.timestamp
                read_model.version += 1
                
                if read_model.status == 'in_progress':
                    read_model.started_at = event.timestamp
                elif read_model.status == 'completed':
                    read_model.completed_at = event.timestamp
                
                await self._save(read_model)
        
        elif event.event_type == EventType.PAYMENT_VERIFIED.value:
            read_model = await self._get(job_id)
            if read_model:
                read_model.payment_verified = True
                read_model.status = 'payment_verified'
                read_model.updated_at = event.timestamp
                read_model.version += 1
                await self._save(read_model)
        
        elif event.event_type == EventType.FINDING_DISCOVERED.value:
            read_model = await self._get(job_id)
            if read_model:
                severity = event.payload.get('severity', 'MEDIUM')
                
                if severity == 'CRITICAL':
                    read_model.critical_findings += 1
                elif severity == 'HIGH':
                    read_model.high_findings += 1
                
                count_key = severity.lower()
                read_model.findings_count[count_key] = read_model.findings_count.get(count_key, 0) + 1
                read_model.updated_at = event.timestamp
                read_model.version += 1
                await self._save(read_model)
        
        elif event.event_type == EventType.JOB_COMPLETED.value:
            read_model = await self._get(job_id)
            if read_model:
                read_model.status = 'completed'
                read_model.findings_count = event.payload.get('findings_count', {})
                read_model.report_path = event.payload.get('report_path')
                read_model.completed_at = event.timestamp
                read_model.updated_at = event.timestamp
                read_model.version += 1
                await self._save(read_model)
        
        elif event.event_type == EventType.JOB_FAILED.value:
            read_model = await self._get(job_id)
            if read_model:
                read_model.status = 'failed'
                read_model.error = event.payload.get('error')
                read_model.updated_at = event.timestamp
                read_model.version += 1
                await self._save(read_model)
    
    async def _get(self, job_id: str) -> Optional[JobReadModel]:
        """Get read model from cache or database."""
        if job_id in self._cache:
            return self._cache[job_id]
        
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return self._cache.get(job_id)
        
        row = await db.fetchrow(
            "SELECT * FROM jobs WHERE id = $1",
            job_id
        )
        
        if row:
            read_model = JobReadModel(
                id=row['id'],
                workspace_id=str(row['workspace_id']) if row['workspace_id'] else None,
                target_url=row['target_url'],
                status=row['status'],
                priority=row['priority'],
                wallet_address=row['wallet_address'],
                payment_verified=row['payment_verified'],
                findings_count=row['findings_count'] or {},
                critical_findings=(row['findings_count'] or {}).get('critical', 0),
                high_findings=(row['findings_count'] or {}).get('high', 0),
                created_at=row['created_at'].isoformat() if row['created_at'] else '',
                updated_at=row['updated_at'].isoformat() if row['updated_at'] else '',
                started_at=row['started_at'].isoformat() if row['started_at'] else None,
                completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                error=row['error'],
                report_path=row['report_path'],
                version=row['version'],
            )
            self._cache[job_id] = read_model
            return read_model
        
        return None
    
    async def _save(self, read_model: JobReadModel) -> None:
        """Save read model to database."""
        self._cache[read_model.id] = read_model
        
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return
        
        await db.execute(
            """
            INSERT INTO jobs 
                (id, target_url, status, priority, wallet_address, payment_verified,
                 findings_count, created_at, updated_at, started_at, completed_at,
                 error, report_path, version)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                payment_verified = EXCLUDED.payment_verified,
                findings_count = EXCLUDED.findings_count,
                updated_at = EXCLUDED.updated_at,
                started_at = EXCLUDED.started_at,
                completed_at = EXCLUDED.completed_at,
                error = EXCLUDED.error,
                report_path = EXCLUDED.report_path,
                version = EXCLUDED.version
            """,
            read_model.id,
            read_model.target_url,
            read_model.status,
            read_model.priority,
            read_model.wallet_address,
            read_model.payment_verified,
            read_model.findings_count,
            read_model.created_at,
            read_model.updated_at,
            read_model.started_at,
            read_model.completed_at,
            read_model.error,
            read_model.report_path,
            read_model.version,
        )
    
    async def rebuild(self) -> None:
        """Rebuild all job read models from events."""
        logger.info(f"Rebuilding {self.name}...")
        
        self._cache.clear()
        
        events = await self._event_store.get_events_by_type(
            EventType.JOB_CREATED.value,
            limit=10000,
        )
        
        for event in events:
            await self.handle(event)
        
        logger.info(f"Rebuilt {self.name}: {len(self._cache)} models")


class FindingProjection(Projection):
    """
    Projection for Finding read models.
    """
    
    NAME = "finding_projection"
    
    def __init__(self, db_pool=None):
        self._db = db_pool
        self._cache: Dict[str, FindingReadModel] = {}
    
    @property
    def name(self) -> str:
        return self.NAME
    
    @property
    def subscribed_events(self) -> List[str]:
        return [
            EventType.FINDING_DISCOVERED.value,
            EventType.EXPLOIT_GENERATED.value,
            EventType.VERIFICATION_COMPLETED.value,
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        """Handle finding-related events."""
        if event.event_type == EventType.FINDING_DISCOVERED.value:
            finding_id = event.payload.get('finding_id')
            if not finding_id:
                return
            
            read_model = FindingReadModel(
                id=finding_id,
                job_id=event.aggregate_id,
                title=event.payload.get('title', ''),
                severity=event.payload.get('severity', 'MEDIUM'),
                cvss_score=event.payload.get('cvss_score', 5.0),
                analyzer=event.payload.get('analyzer', ''),
                created_at=event.timestamp,
                updated_at=event.timestamp,
            )
            
            self._cache[finding_id] = read_model
            await self._save_to_db(read_model)
    
    async def _save_to_db(self, read_model: FindingReadModel) -> None:
        """Save finding to database."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return
        
        await db.execute(
            """
            INSERT INTO findings 
                (id, job_id, title, severity, cvss_score, analyzer, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                severity = EXCLUDED.severity,
                cvss_score = EXCLUDED.cvss_score,
                updated_at = EXCLUDED.updated_at
            """,
            read_model.id,
            read_model.job_id,
            read_model.title,
            read_model.severity,
            read_model.cvss_score,
            read_model.analyzer,
            read_model.created_at,
            read_model.updated_at,
        )
    
    async def rebuild(self) -> None:
        """Rebuild all finding read models."""
        logger.info(f"Rebuilding {self.name}...")
        self._cache.clear()
        logger.info(f"Rebuilt {self.name}")


# ============================================================================
# Projection Manager
# ============================================================================

class ProjectionManager:
    """
    Manages all projections and routes events to them.
    """
    
    def __init__(self, event_store: Optional[EventStore] = None):
        self._event_store = event_store or get_event_store()
        self._projections: List[Projection] = []
        self._event_to_projections: Dict[str, List[Projection]] = {}
    
    def register(self, projection: Projection) -> None:
        """Register a projection."""
        self._projections.append(projection)
        
        for event_type in projection.subscribed_events:
            if event_type not in self._event_to_projections:
                self._event_to_projections[event_type] = []
            self._event_to_projections[event_type].append(projection)
        
        self._event_store.register_handler(
            event_type="*",  # Subscribe to all events
            handler=self._handle_event,
        )
        
        logger.info(f"Registered projection: {projection.name}")
    
    async def _handle_event(self, event: DomainEvent) -> None:
        """Route event to registered projections."""
        projections = self._event_to_projections.get(event.event_type, [])
        
        for projection in projections:
            try:
                await projection.handle(event)
            except Exception as e:
                logger.error(f"Projection {projection.name} error: {e}")
    
    async def rebuild_all(self) -> None:
        """Rebuild all projections from event history."""
        logger.info("Rebuilding all projections...")
        
        for projection in self._projections:
            try:
                await projection.rebuild()
            except Exception as e:
                logger.error(f"Failed to rebuild {projection.name}: {e}")
        
        logger.info("All projections rebuilt")


# ============================================================================
# Read Model Repositories (Query Side)
# ============================================================================

class JobReadRepository:
    """
    Repository for querying Job read models.
    
    Optimized for common query patterns.
    """
    
    def __init__(self, db_pool=None, projection: Optional[JobProjection] = None):
        self._db = db_pool
        self._projection = projection
    
    async def get(self, job_id: str) -> Optional[JobReadModel]:
        """Get job by ID."""
        if self._projection:
            return await self._projection._get(job_id)
        
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return None
        
        row = await db.fetchrow(
            "SELECT * FROM jobs WHERE id = $1",
            job_id
        )
        
        if row:
            return JobReadModel(
                id=row['id'],
                workspace_id=str(row['workspace_id']) if row['workspace_id'] else None,
                target_url=row['target_url'],
                status=row['status'],
                priority=row['priority'],
                wallet_address=row['wallet_address'],
                payment_verified=row['payment_verified'],
                findings_count=row['findings_count'] or {},
                created_at=row['created_at'].isoformat() if row['created_at'] else '',
                updated_at=row['updated_at'].isoformat() if row['updated_at'] else '',
                error=row['error'],
                report_path=row['report_path'],
                version=row['version'],
            )
        
        return None
    
    async def list_by_status(
        self,
        status: str,
        limit: int = 100,
    ) -> List[JobReadModel]:
        """List jobs by status."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return []
        
        rows = await db.fetch(
            """
            SELECT * FROM jobs
            WHERE status = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            status,
            limit,
        )
        
        return [
            JobReadModel(
                id=row['id'],
                target_url=row['target_url'],
                status=row['status'],
                priority=row['priority'],
                created_at=row['created_at'].isoformat() if row['created_at'] else '',
                updated_at=row['updated_at'].isoformat() if row['updated_at'] else '',
            )
            for row in rows
        ]
    
    async def list_by_wallet(
        self,
        wallet_address: str,
        limit: int = 20,
    ) -> List[JobReadModel]:
        """List jobs by wallet address."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return []
        
        rows = await db.fetch(
            """
            SELECT * FROM jobs
            WHERE wallet_address = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            wallet_address.lower(),
            limit,
        )
        
        return [
            JobReadModel(
                id=row['id'],
                target_url=row['target_url'],
                status=row['status'],
                priority=row['priority'],
                wallet_address=row['wallet_address'],
                findings_count=row['findings_count'] or {},
                created_at=row['created_at'].isoformat() if row['created_at'] else '',
                updated_at=row['updated_at'].isoformat() if row['updated_at'] else '',
            )
            for row in rows
        ]
    
    async def count_by_status(self) -> Dict[str, int]:
        """Count jobs by status."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return {}
        
        rows = await db.fetch(
            """
            SELECT status, count(*) as count
            FROM jobs
            GROUP BY status
            """
        )
        
        return {row['status']: row['count'] for row in rows}


# ============================================================================
# Singleton instances
# ============================================================================

_job_projection: Optional[JobProjection] = None
_finding_projection: Optional[FindingProjection] = None
_projection_manager: Optional[ProjectionManager] = None
_job_read_repository: Optional[JobReadRepository] = None


def get_job_projection() -> JobProjection:
    """Get global job projection instance."""
    global _job_projection
    if _job_projection is None:
        _job_projection = JobProjection()
    return _job_projection


def get_finding_projection() -> FindingProjection:
    """Get global finding projection instance."""
    global _finding_projection
    if _finding_projection is None:
        _finding_projection = FindingProjection()
    return _finding_projection


def get_projection_manager() -> ProjectionManager:
    """Get global projection manager instance."""
    global _projection_manager
    if _projection_manager is None:
        _projection_manager = ProjectionManager()
        _projection_manager.register(get_job_projection())
        _projection_manager.register(get_finding_projection())
    return _projection_manager


def get_job_read_repository() -> JobReadRepository:
    """Get global job read repository instance."""
    global _job_read_repository
    if _job_read_repository is None:
        _job_read_repository = JobReadRepository(projection=get_job_projection())
    return _job_read_repository
