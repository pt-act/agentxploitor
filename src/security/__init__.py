"""
Security Module - Multi-Tenancy, RBAC, and Audit Logging

This module provides enterprise-grade security features:
- Workspace isolation (multi-tenancy)
- Role-based access control (RBAC)
- Immutable audit logging
"""

from security.multi_tenancy import (
    Workspace,
    WorkspaceStatus,
    User,
    UserRole,
    APIKey,
    WorkspaceContext,
    WorkspaceRepository,
    UserRepository,
    get_workspace_repository,
    get_user_repository,
    ROLE_PERMISSIONS as USER_ROLE_PERMISSIONS,
)

from security.rbac import (
    Permission,
    PermissionError,
    PermissionCheck,
    PermissionChecker,
    RBACMiddleware,
    require_permission,
    require_any_permission,
    get_role_permissions,
    get_user_permissions,
    has_permission,
    get_permission_checker,
    ROLE_PERMISSIONS,
)

from security.audit_log import (
    AuditAction,
    AuditEntry,
    AuditLogRepository,
    AuditLogger,
    get_audit_repository,
    get_audit_logger,
)


__all__ = [
    'Workspace',
    'WorkspaceStatus',
    'User',
    'UserRole',
    'APIKey',
    'WorkspaceContext',
    'WorkspaceRepository',
    'UserRepository',
    'get_workspace_repository',
    'get_user_repository',
    'USER_ROLE_PERMISSIONS',
    'Permission',
    'PermissionError',
    'PermissionCheck',
    'PermissionChecker',
    'RBACMiddleware',
    'require_permission',
    'require_any_permission',
    'get_role_permissions',
    'get_user_permissions',
    'has_permission',
    'get_permission_checker',
    'ROLE_PERMISSIONS',
    'AuditAction',
    'AuditEntry',
    'AuditLogRepository',
    'AuditLogger',
    'get_audit_repository',
    'get_audit_logger',
]
