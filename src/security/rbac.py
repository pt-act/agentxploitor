"""
RBAC - Role-Based Access Control

Permission checking middleware and utilities for secure access control.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Set
from enum import Enum
from functools import wraps
import asyncio

from security.multi_tenancy import (
    User, UserRole, WorkspaceContext,
    get_user_repository,
)

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """System permissions."""
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_WRITE = "workspace:write"
    WORKSPACE_DELETE = "workspace:delete"
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    JOB_READ = "job:read"
    JOB_WRITE = "job:write"
    JOB_DELETE = "job:delete"
    FINDING_READ = "finding:read"
    FINDING_WRITE = "finding:write"
    REPORT_READ = "report:read"
    REPORT_WRITE = "report:write"
    WEBHOOK_READ = "webhook:read"
    WEBHOOK_WRITE = "webhook:write"
    AUDIT_LOG_READ = "audit_log:read"
    API_KEY_CREATE = "api_key:create"
    API_KEY_REVOKE = "api_key:revoke"


ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        Permission.WORKSPACE_READ, Permission.WORKSPACE_WRITE, Permission.WORKSPACE_DELETE,
        Permission.USER_READ, Permission.USER_WRITE, Permission.USER_DELETE,
        Permission.JOB_READ, Permission.JOB_WRITE, Permission.JOB_DELETE,
        Permission.FINDING_READ, Permission.FINDING_WRITE,
        Permission.REPORT_READ, Permission.REPORT_WRITE,
        Permission.WEBHOOK_READ, Permission.WEBHOOK_WRITE,
        Permission.AUDIT_LOG_READ,
        Permission.API_KEY_CREATE, Permission.API_KEY_REVOKE,
    },
    UserRole.ANALYST: {
        Permission.JOB_READ, Permission.JOB_WRITE,
        Permission.FINDING_READ, Permission.FINDING_WRITE,
        Permission.REPORT_READ, Permission.REPORT_WRITE,
        Permission.WEBHOOK_READ,
    },
    UserRole.VIEWER: {
        Permission.JOB_READ,
        Permission.FINDING_READ,
        Permission.REPORT_READ,
    },
    UserRole.API: {
        Permission.JOB_READ, Permission.JOB_WRITE,
        Permission.FINDING_READ, Permission.FINDING_WRITE,
        Permission.REPORT_READ, Permission.REPORT_WRITE,
    },
}


class PermissionError(Exception):
    """Raised when permission check fails."""
    
    def __init__(self, permission: str, user_id: Optional[str] = None):
        self.permission = permission
        self.user_id = user_id
        super().__init__(f"Permission denied: {permission}")


@dataclass
class PermissionCheck:
    """Result of a permission check."""
    granted: bool
    permission: str
    user_id: Optional[str] = None
    role: Optional[str] = None
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'granted': self.granted,
            'permission': self.permission,
            'user_id': self.user_id,
            'role': self.role,
            'reason': self.reason,
        }


class PermissionChecker:
    """
    Permission checking service.
    
    Usage:
        checker = PermissionChecker()
        
        if await checker.check(user, Permission.JOB_WRITE):
            ...
    """
    
    def __init__(self):
        self._custom_checks: Dict[str, Callable] = {}
    
    def register_custom_check(
        self,
        permission: str,
        checker: Callable[[User, Dict[str, Any]], bool],
    ) -> None:
        """Register a custom permission check function."""
        self._custom_checks[permission] = checker
    
    def check(
        self,
        user: Optional[User],
        permission: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> PermissionCheck:
        """Check if user has permission."""
        if user is None:
            return PermissionCheck(
                granted=False,
                permission=permission,
                reason="No user context",
            )
        
        perm = Permission(permission)
        role_permissions = ROLE_PERMISSIONS.get(user.role, set())
        
        if perm in role_permissions:
            return PermissionCheck(
                granted=True,
                permission=permission,
                user_id=user.id,
                role=user.role.value,
            )
        
        if permission in self._custom_checks:
            try:
                custom_result = self._custom_checks[permission](user, context or {})
                if custom_result:
                    return PermissionCheck(
                        granted=True,
                        permission=permission,
                        user_id=user.id,
                        role=user.role.value,
                        reason="Custom check passed",
                    )
            except Exception as e:
                logger.error(f"Custom permission check error: {e}")
        
        return PermissionCheck(
            granted=False,
            permission=permission,
            user_id=user.id,
            role=user.role.value,
            reason=f"Role {user.role.value} does not have {permission}",
        )
    
    def check_any(
        self,
        user: Optional[User],
        permissions: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> PermissionCheck:
        """Check if user has any of the permissions."""
        if user is None:
            return PermissionCheck(
                granted=False,
                permission=",".join(permissions),
                reason="No user context",
            )
        
        for perm in permissions:
            result = self.check(user, perm, context)
            if result.granted:
                return result
        
        return PermissionCheck(
            granted=False,
            permission=",".join(permissions),
            user_id=user.id,
            role=user.role.value,
            reason=f"None of {permissions} granted",
        )
    
    def check_all(
        self,
        user: Optional[User],
        permissions: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> PermissionCheck:
        """Check if user has all permissions."""
        if user is None:
            return PermissionCheck(
                granted=False,
                permission=",".join(permissions),
                reason="No user context",
            )
        
        for perm in permissions:
            result = self.check(user, perm, context)
            if not result.granted:
                return PermissionCheck(
                    granted=False,
                    permission=perm,
                    user_id=user.id,
                    role=user.role.value,
                    reason=f"Missing permission: {perm}",
                )
        
        return PermissionCheck(
            granted=True,
            permission=",".join(permissions),
            user_id=user.id,
            role=user.role.value,
        )
    
    def require(
        self,
        user: Optional[User],
        permission: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Require permission, raise if not granted."""
        result = self.check(user, permission, context)
        if not result.granted:
            raise PermissionError(permission, user.id if user else None)
    
    def get_permissions(self, role: UserRole) -> Set[Permission]:
        """Get all permissions for a role."""
        return ROLE_PERMISSIONS.get(role, set())


def require_permission(permission: str):
    """
    Decorator for permission checks.
    
    Usage:
        @require_permission(Permission.JOB_WRITE.value)
        async def create_job(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = WorkspaceContext.get_current()
            user = context.user if context else None
            
            checker = get_permission_checker()
            checker.require(user, permission)
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = WorkspaceContext.get_current()
            user = context.user if context else None
            
            checker = get_permission_checker()
            checker.require(user, permission)
            
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def require_any_permission(permissions: List[str]):
    """Decorator requiring any of the specified permissions."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = WorkspaceContext.get_current()
            user = context.user if context else None
            
            checker = get_permission_checker()
            result = checker.check_any(user, permissions)
            if not result.granted:
                raise PermissionError(",".join(permissions), user.id if user else None)
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = WorkspaceContext.get_current()
            user = context.user if context else None
            
            checker = get_permission_checker()
            result = checker.check_any(user, permissions)
            if not result.granted:
                raise PermissionError(",".join(permissions), user.id if user else None)
            
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class RBACMiddleware:
    """
    Middleware for RBAC checks.
    
    Can be used with web frameworks to enforce permissions.
    """
    
    def __init__(
        self,
        permission_checker: Optional[PermissionChecker] = None,
        get_user_func: Optional[Callable] = None,
    ):
        self._checker = permission_checker or get_permission_checker()
        self._get_user = get_user_func
    
    async def check_permission(
        self,
        permission: str,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> PermissionCheck:
        """Check permission from request context."""
        user = None
        
        if self._get_user:
            user = await self._get_user(request_context)
        elif request_context:
            user = request_context.get('user')
        
        return self._checker.check(user, permission, request_context)
    
    async def require_permission(
        self,
        permission: str,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Require permission, raise if not granted."""
        result = await self.check_permission(permission, request_context)
        if not result.granted:
            raise PermissionError(permission, result.user_id)


def get_role_permissions(role: UserRole) -> Set[Permission]:
    """Get permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())


def get_user_permissions(user: User) -> Set[Permission]:
    """Get all permissions for a user."""
    return ROLE_PERMISSIONS.get(user.role, set())


def has_permission(user: User, permission: str) -> bool:
    """Quick check if user has permission."""
    try:
        perm = Permission(permission)
        return perm in ROLE_PERMISSIONS.get(user.role, set())
    except ValueError:
        return False


_permission_checker: Optional[PermissionChecker] = None


def get_permission_checker() -> PermissionChecker:
    """Get global permission checker."""
    global _permission_checker
    if _permission_checker is None:
        _permission_checker = PermissionChecker()
    return _permission_checker
