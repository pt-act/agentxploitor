"""
Multi-Tenancy - Workspace Isolation

Provides tenant isolation at the application and database level.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


# ============================================================================
# Workspace
# ============================================================================

class WorkspaceStatus(str, Enum):
    """Workspace status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


@dataclass
class Workspace:
    """
    A workspace represents a tenant/organization.
    
    Workspaces provide isolation between different organizations
    using the platform.
    """
    id: str
    name: str
    slug: str
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE
    settings: Dict[str, Any] = field(default_factory=dict)
    created_by: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    deleted_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'status': self.status.value,
            'settings': self.settings,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'deleted_at': self.deleted_at,
        }
    
    @classmethod
    def create(cls, name: str, slug: str, created_by: Optional[str] = None) -> 'Workspace':
        """Create a new workspace."""
        workspace_id = str(uuid.uuid4())
        return cls(
            id=workspace_id,
            name=name,
            slug=slug.lower().replace(' ', '-').replace('_', '-'),
            created_by=created_by,
        )
    
    def is_active(self) -> bool:
        return self.status == WorkspaceStatus.ACTIVE and self.deleted_at is None


# ============================================================================
# User
# ============================================================================

class UserRole(str, Enum):
    """User roles within a workspace."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API = "api"


ROLE_PERMISSIONS: Dict[UserRole, List[str]] = {
    UserRole.ADMIN: [
        'workspace:read', 'workspace:write', 'workspace:delete',
        'user:read', 'user:write', 'user:delete',
        'job:read', 'job:write', 'job:delete',
        'finding:read', 'finding:write',
        'report:read', 'report:write',
        'webhook:read', 'webhook:write',
        'audit_log:read',
        'api_key:create', 'api_key:revoke',
    ],
    UserRole.ANALYST: [
        'job:read', 'job:write',
        'finding:read', 'finding:write',
        'report:read', 'report:write',
        'webhook:read',
    ],
    UserRole.VIEWER: [
        'job:read',
        'finding:read',
        'report:read',
    ],
    UserRole.API: [
        'job:read', 'job:write',
        'finding:read', 'finding:write',
        'report:read', 'report:write',
    ],
}


@dataclass
class User:
    """
    User within a workspace.
    
    Users are scoped to a workspace and have a role
    that determines their permissions.
    """
    id: str
    workspace_id: str
    role: UserRole
    external_id: Optional[str] = None  # Farcaster FID, etc.
    email: Optional[str] = None
    display_name: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    api_key_hash: Optional[str] = None
    api_key_scopes: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_active_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'role': self.role.value,
            'external_id': self.external_id,
            'email': self.email,
            'display_name': self.display_name,
            'settings': self.settings,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_active_at': self.last_active_at,
        }
    
    @classmethod
    def create(
        cls,
        workspace_id: str,
        role: UserRole,
        external_id: Optional[str] = None,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> 'User':
        """Create a new user."""
        user_id = str(uuid.uuid4())
        return cls(
            id=user_id,
            workspace_id=workspace_id,
            role=role,
            external_id=external_id,
            email=email,
            display_name=display_name,
        )
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        role_permissions = ROLE_PERMISSIONS.get(self.role, [])
        return permission in role_permissions
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(self.has_permission(p) for p in permissions)
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Check if user has all specified permissions."""
        return all(self.has_permission(p) for p in permissions)


# ============================================================================
# API Key
# ============================================================================

@dataclass
class APIKey:
    """
    API key for programmatic access.
    
    API keys are scoped to a user and have specific permissions.
    """
    id: str
    user_id: str
    workspace_id: str
    name: str
    key_hash: str
    scopes: List[str] = field(default_factory=list)
    active: bool = True
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'workspace_id': self.workspace_id,
            'name': self.name,
            'scopes': self.scopes,
            'active': self.active,
            'last_used_at': self.last_used_at,
            'expires_at': self.expires_at,
            'created_at': self.created_at,
        }
    
    def is_valid(self) -> bool:
        """Check if API key is valid."""
        if not self.active:
            return False
        
        if self.expires_at:
            expires = datetime.fromisoformat(self.expires_at)
            if datetime.utcnow() > expires:
                return False
        
        return True
    
    def has_scope(self, scope: str) -> bool:
        """Check if key has a specific scope."""
        if '*' in self.scopes:
            return True
        return scope in self.scopes


# ============================================================================
# Workspace Context
# ============================================================================

class WorkspaceContext:
    """
    Context for the current request/workspace.
    
    Provides workspace isolation throughout the application.
    """
    
    _current: Optional['WorkspaceContext'] = None
    
    def __init__(
        self,
        workspace: Workspace,
        user: Optional[User] = None,
        api_key: Optional[APIKey] = None,
    ):
        self.workspace = workspace
        self.user = user
        self.api_key = api_key
    
    @classmethod
    def set_current(cls, context: 'WorkspaceContext') -> None:
        """Set current context (for request scope)."""
        cls._current = context
    
    @classmethod
    def get_current(cls) -> Optional['WorkspaceContext']:
        """Get current context."""
        return cls._current
    
    @classmethod
    def clear_current(cls) -> None:
        """Clear current context."""
        cls._current = None
    
    @property
    def workspace_id(self) -> str:
        return self.workspace.id
    
    @property
    def user_id(self) -> Optional[str]:
        return self.user.id if self.user else None
    
    def check_permission(self, permission: str) -> bool:
        """Check if current user has permission."""
        if self.user:
            return self.user.has_permission(permission)
        if self.api_key:
            return self.api_key.has_scope(permission)
        return False
    
    def require_permission(self, permission: str) -> None:
        """Require permission, raise if not available."""
        if not self.check_permission(permission):
            from security.rbac import PermissionError as RBACPermissionError
            raise RBACPermissionError(permission)


# ============================================================================
# Workspace Repository
# ============================================================================

class WorkspaceRepository:
    """Repository for workspace operations."""
    
    def __init__(self, db_pool=None):
        self._db = db_pool
    
    async def get(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace by ID."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return None
        
        row = await db.fetchrow(
            "SELECT * FROM workspaces WHERE id = $1 AND deleted_at IS NULL",
            workspace_id,
        )
        
        if row:
            return Workspace(
                id=str(row['id']),
                name=row['name'],
                slug=row['slug'],
                status=WorkspaceStatus(row['status']) if row.get('status') else WorkspaceStatus.ACTIVE,
                settings=row['settings'] or {},
                created_by=str(row['created_by']) if row.get('created_by') else None,
                created_at=row['created_at'].isoformat() if row['created_at'] else '',
                updated_at=row['updated_at'].isoformat() if row['updated_at'] else '',
            )
        
        return None
    
    async def get_by_slug(self, slug: str) -> Optional[Workspace]:
        """Get workspace by slug."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return None
        
        row = await db.fetchrow(
            "SELECT * FROM workspaces WHERE slug = $1 AND deleted_at IS NULL",
            slug,
        )
        
        if row:
            return Workspace(
                id=str(row['id']),
                name=row['name'],
                slug=row['slug'],
                status=WorkspaceStatus(row['status']) if row.get('status') else WorkspaceStatus.ACTIVE,
                settings=row['settings'] or {},
                created_by=str(row['created_by']) if row.get('created_by') else None,
                created_at=row['created_at'].isoformat() if row['created_at'] else '',
                updated_at=row['updated_at'].isoformat() if row['updated_at'] else '',
            )
        
        return None
    
    async def save(self, workspace: Workspace) -> None:
        """Save workspace."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return
        
        await db.execute(
            """
            INSERT INTO workspaces (id, name, slug, status, settings, created_by, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                status = EXCLUDED.status,
                settings = EXCLUDED.settings,
                updated_at = EXCLUDED.updated_at
            """,
            workspace.id,
            workspace.name,
            workspace.slug,
            workspace.status.value,
            workspace.settings,
            workspace.created_by,
            workspace.created_at,
            workspace.updated_at,
        )


class UserRepository:
    """Repository for user operations."""
    
    def __init__(self, db_pool=None):
        self._db = db_pool
    
    async def get(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return None
        
        row = await db.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id,
        )
        
        if row:
            return User(
                id=str(row['id']),
                workspace_id=str(row['workspace_id']),
                role=UserRole(row['role']),
                external_id=row.get('external_id'),
                email=row.get('email'),
                display_name=row.get('display_name'),
                settings=row['settings'] or {},
                created_at=row['created_at'].isoformat() if row['created_at'] else '',
                updated_at=row['updated_at'].isoformat() if row['updated_at'] else '',
                last_active_at=row['last_active_at'].isoformat() if row.get('last_active_at') else None,
            )
        
        return None
    
    async def get_by_external_id(self, external_id: str, workspace_id: str) -> Optional[User]:
        """Get user by external ID within workspace."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return None
        
        row = await db.fetchrow(
            "SELECT * FROM users WHERE external_id = $1 AND workspace_id = $2",
            external_id,
            workspace_id,
        )
        
        if row:
            return User(
                id=str(row['id']),
                workspace_id=str(row['workspace_id']),
                role=UserRole(row['role']),
                external_id=row.get('external_id'),
                email=row.get('email'),
                display_name=row.get('display_name'),
                settings=row['settings'] or {},
                created_at=row['created_at'].isoformat() if row['created_at'] else '',
                updated_at=row['updated_at'].isoformat() if row['updated_at'] else '',
            )
        
        return None
    
    async def list_by_workspace(self, workspace_id: str) -> List[User]:
        """List users in a workspace."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return []
        
        rows = await db.fetch(
            "SELECT * FROM users WHERE workspace_id = $1 ORDER BY created_at DESC",
            workspace_id,
        )
        
        return [
            User(
                id=str(row['id']),
                workspace_id=str(row['workspace_id']),
                role=UserRole(row['role']),
                external_id=row.get('external_id'),
                email=row.get('email'),
                display_name=row.get('display_name'),
                settings=row['settings'] or {},
                created_at=row['created_at'].isoformat() if row['created_at'] else '',
                updated_at=row['updated_at'].isoformat() if row['updated_at'] else '',
            )
            for row in rows
        ]
    
    async def save(self, user: User) -> None:
        """Save user."""
        from infrastructure.database import get_db_pool
        
        db = self._db or get_db_pool()
        
        if not db.connected:
            return
        
        await db.execute(
            """
            INSERT INTO users (id, workspace_id, role, external_id, email, display_name, settings, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (id) DO UPDATE SET
                role = EXCLUDED.role,
                email = EXCLUDED.email,
                display_name = EXCLUDED.display_name,
                settings = EXCLUDED.settings,
                updated_at = EXCLUDED.updated_at,
                last_active_at = NOW()
            """,
            user.id,
            user.workspace_id,
            user.role.value,
            user.external_id,
            user.email,
            user.display_name,
            user.settings,
            user.created_at,
            user.updated_at,
        )


# ============================================================================
# Singleton instances
# ============================================================================

_workspace_repository: Optional[WorkspaceRepository] = None
_user_repository: Optional[UserRepository] = None


def get_workspace_repository() -> WorkspaceRepository:
    """Get global workspace repository."""
    global _workspace_repository
    if _workspace_repository is None:
        _workspace_repository = WorkspaceRepository()
    return _workspace_repository


def get_user_repository() -> UserRepository:
    """Get global user repository."""
    global _user_repository
    if _user_repository is None:
        _user_repository = UserRepository()
    return _user_repository
