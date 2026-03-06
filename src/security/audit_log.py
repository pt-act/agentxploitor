"""
Audit Log - Immutable Audit Trail

Provides immutable audit logging with cryptographic hash chains
for compliance and security tracking.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, AsyncIterator
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Standard audit actions."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"
    PERMISSION_CHANGE = "permission_change"
    JOB_START = "job_start"
    JOB_CANCEL = "job_cancel"
    FINDING_ACKNOWLEDGE = "finding_acknowledge"
    FINDING_RESOLVE = "finding_resolve"


@dataclass
class AuditEntry:
    """
    Immutable audit log entry.

    Entries are linked via cryptographic hash chain for integrity verification.
    """

    id: Optional[int] = None
    workspace_id: str = ""
    action: str = ""
    resource_type: str = ""
    actor_id: Optional[str] = None
    resource_id: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    prev_hash: Optional[str] = None
    hash: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def compute_hash(self, prev_hash: Optional[str] = None) -> str:
        """Compute hash for this entry."""
        data = (
            (prev_hash or "")
            + self.action
            + self.resource_type
            + (self.resource_id or "")
            + json.dumps(self.old_value or {}, sort_keys=True)
            + json.dumps(self.new_value or {}, sort_keys=True)
            + self.created_at
        )
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "actor_id": self.actor_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "hash": self.hash,
            "created_at": self.created_at,
        }

    @classmethod
    def create(
        cls,
        workspace_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> "AuditEntry":
        """Create a new audit entry."""
        return cls(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
        )


class AuditLogRepository:
    """Repository for audit log operations."""

    def __init__(self, db_pool=None):
        self._db = db_pool

    async def append(self, entry: AuditEntry) -> AuditEntry:
        """Append entry to audit log."""
        from infrastructure.database import get_db_pool

        db = self._db or get_db_pool()

        if not db.connected:
            logger.warning("Database not connected, audit entry not persisted")
            return entry

        prev_hash = await self._get_last_hash(db, entry.workspace_id)
        entry.prev_hash = prev_hash

        row = await db.fetchrow(
            """
            INSERT INTO audit_log (
                workspace_id, actor_id, action, resource_type, resource_id,
                old_value, new_value, ip_address, user_agent, prev_hash
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, hash, created_at
            """,
            entry.workspace_id,
            entry.actor_id,
            entry.action,
            entry.resource_type,
            entry.resource_id,
            entry.old_value,
            entry.new_value,
            entry.ip_address,
            entry.user_agent,
            entry.prev_hash,
        )

        if row:
            entry.id = row["id"]
            entry.hash = row["hash"]
            entry.created_at = row["created_at"].isoformat()

        logger.debug(f"Audit entry created: {entry.action} on {entry.resource_type}")
        return entry

    async def _get_last_hash(self, db, workspace_id: str) -> Optional[str]:
        """Get the hash of the last entry for chain continuity."""
        row = await db.fetchrow(
            """
            SELECT hash FROM audit_log
            WHERE workspace_id = $1
            ORDER BY id DESC
            LIMIT 1
            """,
            workspace_id,
        )
        return row["hash"] if row else None

    async def get(self, entry_id: int) -> Optional[AuditEntry]:
        """Get audit entry by ID."""
        from infrastructure.database import get_db_pool

        db = self._db or get_db_pool()

        if not db.connected:
            return None

        row = await db.fetchrow(
            "SELECT * FROM audit_log WHERE id = $1",
            entry_id,
        )

        return self._row_to_entry(row) if row else None

    async def list_by_workspace(
        self,
        workspace_id: str,
        limit: int = 100,
        offset: int = 0,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[AuditEntry]:
        """List audit entries for workspace with filters."""
        from infrastructure.database import get_db_pool

        db = self._db or get_db_pool()

        if not db.connected:
            return []

        conditions = ["workspace_id = $1"]
        params = [workspace_id]
        param_idx = 2

        if action:
            conditions.append(f"action = ${param_idx}")
            params.append(action)
            param_idx += 1

        if resource_type:
            conditions.append(f"resource_type = ${param_idx}")
            params.append(resource_type)
            param_idx += 1

        if actor_id:
            conditions.append(f"actor_id = ${param_idx}")
            params.append(actor_id)
            param_idx += 1

        if start_date:
            conditions.append(f"created_at >= ${param_idx}")
            params.append(start_date)
            param_idx += 1

        if end_date:
            conditions.append(f"created_at <= ${param_idx}")
            params.append(end_date)
            param_idx += 1

        params.extend([limit, offset])

        query = f"""
            SELECT * FROM audit_log
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """

        rows = await db.fetch(query, *params)
        return [self._row_to_entry(row) for row in rows]

    async def list_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        workspace_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """List audit entries for a specific resource."""
        from infrastructure.database import get_db_pool

        db = self._db or get_db_pool()

        if not db.connected:
            return []

        if workspace_id:
            rows = await db.fetch(
                """
                SELECT * FROM audit_log
                WHERE resource_type = $1 AND resource_id = $2 AND workspace_id = $3
                ORDER BY created_at DESC
                LIMIT $4
                """,
                resource_type,
                resource_id,
                workspace_id,
                limit,
            )
        else:
            rows = await db.fetch(
                """
                SELECT * FROM audit_log
                WHERE resource_type = $1 AND resource_id = $2
                ORDER BY created_at DESC
                LIMIT $3
                """,
                resource_type,
                resource_id,
                limit,
            )

        return [self._row_to_entry(row) for row in rows]

    async def iter_all(
        self,
        workspace_id: str,
        batch_size: int = 1000,
    ) -> AsyncIterator[List[AuditEntry]]:
        """Iterate all entries for export."""
        from infrastructure.database import get_db_pool

        db = self._db or get_db_pool()

        if not db.connected:
            return

        offset = 0
        while True:
            entries = await self.list_by_workspace(
                workspace_id,
                limit=batch_size,
                offset=offset,
            )

            if not entries:
                break

            yield entries
            offset += batch_size

    async def verify_chain(self, workspace_id: str) -> Dict[str, Any]:
        """Verify hash chain integrity."""
        from infrastructure.database import get_db_pool

        db = self._db or get_db_pool()

        if not db.connected:
            return {"valid": False, "error": "Database not connected"}

        entries = await db.fetch(
            """
            SELECT id, prev_hash, hash, action, resource_type, resource_id,
                   old_value, new_value, created_at
            FROM audit_log
            WHERE workspace_id = $1
            ORDER BY id ASC
            """,
            workspace_id,
        )

        if not entries:
            return {"valid": True, "entries_checked": 0}

        errors = []
        prev_hash = None

        for row in entries:
            expected_hash = hashlib.sha256(
                (
                    (prev_hash or "")
                    + row["action"]
                    + row["resource_type"]
                    + (row["resource_id"] or "")
                    + json.dumps(row["old_value"] or {}, sort_keys=True)
                    + json.dumps(row["new_value"] or {}, sort_keys=True)
                    + (row["created_at"].isoformat() if row["created_at"] else "")
                ).encode()
            ).hexdigest()

            if row["hash"] != expected_hash:
                errors.append(
                    {
                        "entry_id": row["id"],
                        "expected": expected_hash,
                        "actual": row["hash"],
                    }
                )

            prev_hash = row["hash"]

        return {
            "valid": len(errors) == 0,
            "entries_checked": len(entries),
            "errors": errors,
        }

    def _row_to_entry(self, row) -> AuditEntry:
        """Convert database row to AuditEntry."""
        return AuditEntry(
            id=row["id"],
            workspace_id=str(row["workspace_id"]),
            actor_id=str(row["actor_id"]) if row.get("actor_id") else None,
            action=row["action"],
            resource_type=row["resource_type"],
            resource_id=row.get("resource_id"),
            old_value=row.get("old_value"),
            new_value=row.get("new_value"),
            ip_address=row.get("ip_address"),
            user_agent=row.get("user_agent"),
            prev_hash=row.get("prev_hash"),
            hash=row["hash"],
            created_at=row["created_at"].isoformat() if row["created_at"] else "",
        )


class AuditLogger:
    """
    High-level audit logging service.

    Usage:
        audit = AuditLogger()
        await audit.log(
            workspace_id=ws_id,
            action=AuditAction.CREATE,
            resource_type='job',
            resource_id=job_id,
            new_value={'status': 'queued'},
            actor_id=user_id,
        )
    """

    def __init__(self, repository: Optional[AuditLogRepository] = None):
        self._repo = repository or AuditLogRepository()

    async def log(
        self,
        workspace_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditEntry:
        """Log an audit event."""
        entry = AuditEntry.create(
            workspace_id=workspace_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_id=actor_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return await self._repo.append(entry)

    async def log_create(
        self,
        workspace_id: str,
        resource_type: str,
        resource_id: str,
        value: Dict[str, Any],
        actor_id: Optional[str] = None,
        **kwargs,
    ) -> AuditEntry:
        """Log a creation event."""
        return await self.log(
            workspace_id=workspace_id,
            action=AuditAction.CREATE.value,
            resource_type=resource_type,
            resource_id=resource_id,
            new_value=value,
            actor_id=actor_id,
            **kwargs,
        )

    async def log_update(
        self,
        workspace_id: str,
        resource_type: str,
        resource_id: str,
        old_value: Dict[str, Any],
        new_value: Dict[str, Any],
        actor_id: Optional[str] = None,
        **kwargs,
    ) -> AuditEntry:
        """Log an update event."""
        return await self.log(
            workspace_id=workspace_id,
            action=AuditAction.UPDATE.value,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            actor_id=actor_id,
            **kwargs,
        )

    async def log_delete(
        self,
        workspace_id: str,
        resource_type: str,
        resource_id: str,
        old_value: Dict[str, Any],
        actor_id: Optional[str] = None,
        **kwargs,
    ) -> AuditEntry:
        """Log a deletion event."""
        return await self.log(
            workspace_id=workspace_id,
            action=AuditAction.DELETE.value,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            actor_id=actor_id,
            **kwargs,
        )

    async def query(
        self,
        workspace_id: str,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEntry]:
        """Query audit log entries."""
        return await self._repo.list_by_workspace(
            workspace_id=workspace_id,
            action=action,
            resource_type=resource_type,
            actor_id=actor_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

    async def export(
        self,
        workspace_id: str,
        format: str = "json",
    ) -> str:
        """Export audit log as JSON."""
        entries = []
        async for batch in self._repo.iter_all(workspace_id):
            entries.extend([e.to_dict() for e in batch])

        return json.dumps(entries, indent=2)

    async def verify_integrity(self, workspace_id: str) -> Dict[str, Any]:
        """Verify audit log hash chain integrity."""
        return await self._repo.verify_chain(workspace_id)


_audit_repository: Optional[AuditLogRepository] = None
_audit_logger: Optional[AuditLogger] = None


def get_audit_repository() -> AuditLogRepository:
    """Get global audit repository."""
    global _audit_repository
    if _audit_repository is None:
        _audit_repository = AuditLogRepository()
    return _audit_repository


def get_audit_logger() -> AuditLogger:
    """Get global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(get_audit_repository())
    return _audit_logger
