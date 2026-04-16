"""
Tests for Security Components - Group 2

Tests for multi-tenancy, RBAC, and audit logging.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from security.multi_tenancy import (
    Workspace,
    WorkspaceStatus,
    User,
    UserRole,
    APIKey,
    WorkspaceContext,
    ROLE_PERMISSIONS,
)
from security.rbac import (
    Permission,
    PermissionError,
    PermissionCheck,
    PermissionChecker,
    RBACMiddleware,
    require_permission,
    get_permission_checker,
    has_permission,
    ROLE_PERMISSIONS as RBAC_ROLE_PERMISSIONS,
)
from security.audit_log import (
    AuditAction,
    AuditEntry,
    AuditLogger,
    AuditLogRepository,
)


class TestWorkspace:
    """Tests for Workspace model."""
    
    def test_create_workspace(self):
        workspace = Workspace.create(
            name="Test Workspace",
            slug="test-workspace",
            created_by="user-001",
        )
        
        assert workspace.id is not None
        assert workspace.name == "Test Workspace"
        assert workspace.slug == "test-workspace"
        assert workspace.status == WorkspaceStatus.ACTIVE
        assert workspace.created_by == "user-001"
    
    def test_slug_normalization(self):
        workspace = Workspace.create(
            name="Test Workspace",
            slug="Test_Workspace Here",
        )
        
        assert workspace.slug == "test-workspace-here"
    
    def test_is_active(self):
        workspace = Workspace.create("Test", "test")
        assert workspace.is_active() is True
        
        workspace.status = WorkspaceStatus.SUSPENDED
        assert workspace.is_active() is False
        
        workspace.status = WorkspaceStatus.ACTIVE
        workspace.deleted_at = datetime.utcnow().isoformat()
        assert workspace.is_active() is False
    
    def test_to_dict(self):
        workspace = Workspace.create("Test", "test")
        data = workspace.to_dict()
        
        assert data['name'] == "Test"
        assert data['slug'] == "test"
        assert data['status'] == "active"


class TestUser:
    """Tests for User model."""
    
    @pytest.fixture
    def workspace(self):
        return Workspace.create("Test", "test")
    
    def test_create_user(self, workspace):
        user = User.create(
            workspace_id=workspace.id,
            role=UserRole.ANALYST,
            external_id="fid-12345",
            email="test@example.com",
            display_name="Test User",
        )
        
        assert user.id is not None
        assert user.workspace_id == workspace.id
        assert user.role == UserRole.ANALYST
        assert user.external_id == "fid-12345"
    
    def test_has_permission_admin(self, workspace):
        user = User.create(workspace.id, UserRole.ADMIN)
        
        assert user.has_permission("job:read") is True
        assert user.has_permission("job:write") is True
        assert user.has_permission("user:delete") is True
        assert user.has_permission("workspace:delete") is True
    
    def test_has_permission_analyst(self, workspace):
        user = User.create(workspace.id, UserRole.ANALYST)
        
        assert user.has_permission("job:read") is True
        assert user.has_permission("job:write") is True
        assert user.has_permission("user:delete") is False
        assert user.has_permission("workspace:delete") is False
    
    def test_has_permission_viewer(self, workspace):
        user = User.create(workspace.id, UserRole.VIEWER)
        
        assert user.has_permission("job:read") is True
        assert user.has_permission("job:write") is False
        assert user.has_permission("finding:read") is True
        assert user.has_permission("finding:write") is False
    
    def test_has_any_permission(self, workspace):
        user = User.create(workspace.id, UserRole.VIEWER)
        
        assert user.has_any_permission(["job:read", "job:write"]) is True
        assert user.has_any_permission(["job:write", "user:delete"]) is False
    
    def test_has_all_permissions(self, workspace):
        user = User.create(workspace.id, UserRole.ANALYST)
        
        assert user.has_all_permissions(["job:read", "job:write"]) is True
        assert user.has_all_permissions(["job:read", "user:delete"]) is False


class TestAPIKey:
    """Tests for APIKey model."""
    
    @pytest.fixture
    def user(self):
        workspace = Workspace.create("Test", "test")
        return User.create(workspace.id, UserRole.API)
    
    def test_create_api_key(self, user):
        import hashlib
        key = APIKey(
            id="key-001",
            user_id=user.id,
            workspace_id=user.workspace_id,
            name="Test Key",
            key_hash=hashlib.sha256(b"secret").hexdigest(),
            scopes=["job:read", "job:write"],
        )
        
        assert key.id == "key-001"
        assert key.name == "Test Key"
        assert key.active is True
    
    def test_is_valid(self, user):
        key = APIKey(
            id="key-001",
            user_id=user.id,
            workspace_id=user.workspace_id,
            name="Test Key",
            key_hash="hash",
        )
        
        assert key.is_valid() is True
        
        key.active = False
        assert key.is_valid() is False
    
    def test_is_valid_with_expiry(self, user):
        key = APIKey(
            id="key-001",
            user_id=user.id,
            workspace_id=user.workspace_id,
            name="Test Key",
            key_hash="hash",
            expires_at="2020-01-01T00:00:00",
        )
        
        assert key.is_valid() is False
    
    def test_has_scope(self, user):
        key = APIKey(
            id="key-001",
            user_id=user.id,
            workspace_id=user.workspace_id,
            name="Test Key",
            key_hash="hash",
            scopes=["job:read", "finding:read"],
        )
        
        assert key.has_scope("job:read") is True
        assert key.has_scope("job:write") is False
        
        key.scopes = ["*"]
        assert key.has_scope("anything") is True


class TestWorkspaceContext:
    """Tests for WorkspaceContext."""
    
    def test_set_and_get_current(self):
        workspace = Workspace.create("Test", "test")
        user = User.create(workspace.id, UserRole.ADMIN)
        context = WorkspaceContext(workspace, user)
        
        WorkspaceContext.set_current(context)
        
        assert WorkspaceContext.get_current() is context
        
        WorkspaceContext.clear_current()
        assert WorkspaceContext.get_current() is None
    
    def test_check_permission(self):
        workspace = Workspace.create("Test", "test")
        user = User.create(workspace.id, UserRole.ANALYST)
        context = WorkspaceContext(workspace, user)
        
        assert context.check_permission("job:read") is True
        assert context.check_permission("user:delete") is False
    
    def test_require_permission_success(self):
        workspace = Workspace.create("Test", "test")
        user = User.create(workspace.id, UserRole.ADMIN)
        context = WorkspaceContext(workspace, user)
        
        context.require_permission("job:write")
    
    def test_require_permission_failure(self):
        workspace = Workspace.create("Test", "test")
        user = User.create(workspace.id, UserRole.VIEWER)
        context = WorkspaceContext(workspace, user)
        
        with pytest.raises(PermissionError):
            context.require_permission("job:write")


class TestPermissionChecker:
    """Tests for PermissionChecker."""
    
    @pytest.fixture
    def checker(self):
        return PermissionChecker()
    
    @pytest.fixture
    def admin_user(self):
        workspace = Workspace.create("Test", "test")
        return User.create(workspace.id, UserRole.ADMIN)
    
    @pytest.fixture
    def viewer_user(self):
        workspace = Workspace.create("Test", "test")
        return User.create(workspace.id, UserRole.VIEWER)
    
    def test_check_admin_has_all_permissions(self, checker, admin_user):
        result = checker.check(admin_user, Permission.JOB_WRITE.value)
        
        assert result.granted is True
        assert result.permission == Permission.JOB_WRITE.value
    
    def test_check_viewer_limited_permissions(self, checker, viewer_user):
        result = checker.check(viewer_user, Permission.JOB_WRITE.value)
        
        assert result.granted is False
        assert result.permission == Permission.JOB_WRITE.value
        assert "does not have" in result.reason
    
    def test_check_no_user(self, checker):
        result = checker.check(None, Permission.JOB_READ.value)
        
        assert result.granted is False
        assert result.reason == "No user context"
    
    def test_check_any_permission(self, checker, viewer_user):
        result = checker.check_any(
            viewer_user,
            [Permission.JOB_WRITE.value, Permission.JOB_READ.value],
        )
        
        assert result.granted is True
    
    def test_check_all_permissions(self, checker, admin_user):
        result = checker.check_all(
            admin_user,
            [Permission.JOB_READ.value, Permission.JOB_WRITE.value],
        )
        
        assert result.granted is True
    
    def test_require_raises_on_denied(self, checker, viewer_user):
        with pytest.raises(PermissionError):
            checker.require(viewer_user, Permission.USER_DELETE.value)
    
    def test_get_permissions_for_role(self, checker):
        perms = checker.get_permissions(UserRole.ADMIN)
        
        assert Permission.JOB_WRITE in perms
        assert Permission.USER_DELETE in perms


class TestAuditEntry:
    """Tests for AuditEntry model."""
    
    def test_create_audit_entry(self):
        entry = AuditEntry.create(
            workspace_id="ws-001",
            action=AuditAction.CREATE.value,
            resource_type="job",
            resource_id="job-001",
            actor_id="user-001",
            new_value={"status": "queued"},
        )
        
        assert entry.workspace_id == "ws-001"
        assert entry.action == "create"
        assert entry.resource_type == "job"
        assert entry.resource_id == "job-001"
    
    def test_compute_hash(self):
        entry = AuditEntry.create(
            workspace_id="ws-001",
            action=AuditAction.CREATE.value,
            resource_type="job",
        )
        
        hash1 = entry.compute_hash("prev-hash-123")
        hash2 = entry.compute_hash("prev-hash-456")
        
        assert hash1 != hash2
        assert len(hash1) == 64
    
    def test_to_dict(self):
        entry = AuditEntry.create(
            workspace_id="ws-001",
            action=AuditAction.UPDATE.value,
            resource_type="finding",
            resource_id="finding-001",
            old_value={"status": "open"},
            new_value={"status": "fixed"},
        )
        
        data = entry.to_dict()
        
        assert data['action'] == "update"
        assert data['resource_type'] == "finding"
        assert data['old_value']['status'] == "open"
        assert data['new_value']['status'] == "fixed"


class TestAuditLogger:
    """Tests for AuditLogger service."""
    
    @pytest.fixture
    def audit_logger(self):
        mock_repo = MagicMock(spec=AuditLogRepository)
        # append must return the entry passed to it (not a mock object)
        mock_repo.append = AsyncMock(side_effect=lambda entry: entry)
        return AuditLogger(mock_repo)
    
    @pytest.mark.asyncio
    async def test_log_create(self, audit_logger):
        entry = await audit_logger.log_create(
            workspace_id="ws-001",
            resource_type="job",
            resource_id="job-001",
            value={"status": "queued"},
            actor_id="user-001",
        )
        
        assert entry.action == AuditAction.CREATE.value
        assert entry.new_value == {"status": "queued"}
    
    @pytest.mark.asyncio
    async def test_log_update(self, audit_logger):
        entry = await audit_logger.log_update(
            workspace_id="ws-001",
            resource_type="finding",
            resource_id="finding-001",
            old_value={"status": "open"},
            new_value={"status": "fixed"},
            actor_id="user-001",
        )
        
        assert entry.action == AuditAction.UPDATE.value
        assert entry.old_value == {"status": "open"}
        assert entry.new_value == {"status": "fixed"}
    
    @pytest.mark.asyncio
    async def test_log_delete(self, audit_logger):
        entry = await audit_logger.log_delete(
            workspace_id="ws-001",
            resource_type="api_key",
            resource_id="key-001",
            old_value={"name": "Old Key"},
            actor_id="user-001",
        )
        
        assert entry.action == AuditAction.DELETE.value


class TestRolePermissions:
    """Tests for role permission mappings."""
    
    def test_admin_has_all_permissions(self):
        admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        
        assert len(admin_perms) >= 15
        
    def test_analyst_has_job_permissions(self):
        analyst_perms = ROLE_PERMISSIONS[UserRole.ANALYST]
        
        assert "job:read" in analyst_perms
        assert "job:write" in analyst_perms
        assert "finding:read" in analyst_perms
        assert "finding:write" in analyst_perms
    
    def test_viewer_readonly(self):
        viewer_perms = ROLE_PERMISSIONS[UserRole.VIEWER]
        
        assert "job:read" in viewer_perms
        assert "job:write" not in viewer_perms
        assert "finding:read" in viewer_perms
        assert "finding:write" not in viewer_perms
    
    def test_api_role_has_write_access(self):
        api_perms = ROLE_PERMISSIONS[UserRole.API]
        
        assert "job:write" in api_perms
        assert "finding:write" in api_perms


class TestPermissionDecorator:
    """Tests for permission decorators."""
    
    @pytest.mark.asyncio
    async def test_require_permission_passes(self):
        workspace = Workspace.create("Test", "test")
        user = User.create(workspace.id, UserRole.ADMIN)
        context = WorkspaceContext(workspace, user)
        WorkspaceContext.set_current(context)
        
        @require_permission(Permission.JOB_WRITE.value)
        async def protected_function():
            return "success"
        
        result = await protected_function()
        assert result == "success"
        
        WorkspaceContext.clear_current()
    
    @pytest.mark.asyncio
    async def test_require_permission_fails(self):
        workspace = Workspace.create("Test", "test")
        user = User.create(workspace.id, UserRole.VIEWER)
        context = WorkspaceContext(workspace, user)
        WorkspaceContext.set_current(context)
        
        @require_permission(Permission.JOB_WRITE.value)
        async def protected_function():
            return "success"
        
        with pytest.raises(PermissionError):
            await protected_function()
        
        WorkspaceContext.clear_current()


class TestAuditAction:
    """Tests for AuditAction enum."""
    
    def test_audit_actions_defined(self):
        assert AuditAction.CREATE.value == "create"
        assert AuditAction.UPDATE.value == "update"
        assert AuditAction.DELETE.value == "delete"
        assert AuditAction.JOB_START.value == "job_start"
        assert AuditAction.FINDING_ACKNOWLEDGE.value == "finding_acknowledge"
