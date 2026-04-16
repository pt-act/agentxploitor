"""
Human-in-the-Loop Approval Workflow

Implements approval workflows for high-impact AI actions.
Ensures human oversight for critical decisions.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalPriority(str, Enum):
    """Priority levels for approvals."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalRequest:
    """A request for human approval."""
    id: str
    action_type: str
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    priority: ApprovalPriority = ApprovalPriority.MEDIUM
    status: ApprovalStatus = ApprovalStatus.PENDING
    requester: Optional[str] = None
    approver: Optional[str] = None
    reason: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None
    resolved_at: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if request has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > datetime.fromisoformat(self.expires_at)
    
    def is_pending(self) -> bool:
        """Check if request is still pending."""
        return self.status == ApprovalStatus.PENDING and not self.is_expired()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'action_type': self.action_type,
            'description': self.description,
            'context': self.context,
            'confidence': self.confidence,
            'priority': self.priority.value,
            'status': self.status.value,
            'requester': self.requester,
            'approver': self.approver,
            'reason': self.reason,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'resolved_at': self.resolved_at,
        }


@dataclass
class ApprovalRule:
    """Rule for determining if approval is needed."""
    action_type: str
    confidence_threshold: float
    requires_approval: bool
    auto_approve_after: Optional[int] = None
    approver_roles: List[str] = field(default_factory=list)
    priority: ApprovalPriority = ApprovalPriority.MEDIUM


DEFAULT_RULES: List[ApprovalRule] = [
    ApprovalRule(
        action_type='exploit_generation',
        confidence_threshold=0.8,
        requires_approval=True,
        approver_roles=['admin', 'analyst'],
        priority=ApprovalPriority.HIGH,
    ),
    ApprovalRule(
        action_type='exploit_execution',
        confidence_threshold=1.0,
        requires_approval=True,
        approver_roles=['admin'],
        priority=ApprovalPriority.CRITICAL,
    ),
    ApprovalRule(
        action_type='report_submission',
        confidence_threshold=0.9,
        requires_approval=True,
        approver_roles=['admin', 'analyst'],
        priority=ApprovalPriority.MEDIUM,
    ),
    ApprovalRule(
        action_type='finding_dismissal',
        confidence_threshold=0.7,
        requires_approval=True,
        approver_roles=['admin'],
        priority=ApprovalPriority.LOW,
    ),
]


class ApprovalWorkflow:
    """
    Manages approval workflows for AI actions.
    
    Features:
    - Configurable approval rules
    - Timeout and expiration
    - Notification callbacks
    - Override capability for admins
    """

    def __init__(
        self,
        rules: Optional[List[ApprovalRule]] = None,
        default_timeout_minutes: int = 60,
    ):
        self._rules = rules or DEFAULT_RULES
        self._default_timeout = default_timeout_minutes
        self._requests: Dict[str, ApprovalRequest] = {}
        self._callbacks: Dict[str, List[Callable]] = {
            'on_request': [],
            'on_approve': [],
            'on_reject': [],
            'on_expire': [],
        }

    def request_approval(
        self,
        action_type: str,
        description: str,
        context: Dict[str, Any],
        confidence: float,
        requester: Optional[str] = None,
        expires_in_minutes: Optional[int] = None,
    ) -> Optional[ApprovalRequest]:
        """
        Request approval for an action.
        
        Returns None if auto-approval applies.
        """
        rule = self._get_rule(action_type)
        
        if rule and not rule.requires_approval:
            return None
        
        if rule and confidence >= rule.confidence_threshold:
            if rule.auto_approve_after:
                pass
            else:
                return None
        
        request_id = f"approval-{uuid.uuid4().hex[:12]}"
        
        timeout = expires_in_minutes or self._default_timeout
        expires_at = datetime.utcnow() + timedelta(minutes=timeout)
        
        request = ApprovalRequest(
            id=request_id,
            action_type=action_type,
            description=description,
            context=context,
            confidence=confidence,
            priority=rule.priority if rule else ApprovalPriority.MEDIUM,
            requester=requester,
            expires_at=expires_at.isoformat(),
        )
        
        self._requests[request_id] = request
        
        self._notify('on_request', request)
        
        logger.info(f"Approval request created: {request_id} for {action_type}")
        return request

    def approve(
        self,
        request_id: str,
        approver: str,
        reason: Optional[str] = None,
    ) -> Optional[ApprovalRequest]:
        """Approve a request."""
        request = self._requests.get(request_id)
        
        if not request:
            logger.warning(f"Approval request not found: {request_id}")
            return None
        
        if not request.is_pending():
            logger.warning(f"Approval request not pending: {request_id}")
            return None
        
        request.status = ApprovalStatus.APPROVED
        request.approver = approver
        request.reason = reason
        request.resolved_at = datetime.utcnow().isoformat()
        
        self._notify('on_approve', request)
        
        logger.info(f"Approval request approved: {request_id} by {approver}")
        return request

    def reject(
        self,
        request_id: str,
        approver: str,
        reason: str,
    ) -> Optional[ApprovalRequest]:
        """Reject a request."""
        request = self._requests.get(request_id)
        
        if not request:
            return None
        
        if not request.is_pending():
            return None
        
        request.status = ApprovalStatus.REJECTED
        request.approver = approver
        request.reason = reason
        request.resolved_at = datetime.utcnow().isoformat()
        
        self._notify('on_reject', request)
        
        logger.info(f"Approval request rejected: {request_id} by {approver}")
        return request

    def cancel(self, request_id: str) -> Optional[ApprovalRequest]:
        """Cancel a request."""
        request = self._requests.get(request_id)
        
        if not request:
            return None
        
        request.status = ApprovalStatus.CANCELLED
        request.resolved_at = datetime.utcnow().isoformat()
        
        return request

    def override(
        self,
        request_id: str,
        admin_user: str,
        approve: bool,
        reason: str,
    ) -> Optional[ApprovalRequest]:
        """Admin override of approval status."""
        request = self._requests.get(request_id)
        
        if not request:
            return None
        
        request.status = ApprovalStatus.APPROVED if approve else ApprovalStatus.REJECTED
        request.approver = admin_user
        request.reason = f"[OVERRIDE] {reason}"
        request.resolved_at = datetime.utcnow().isoformat()
        request.context['override'] = True
        
        return request

    def check_expired(self) -> List[ApprovalRequest]:
        """Check and expire timed-out requests."""
        expired = []
        
        for request in self._requests.values():
            if request.status == ApprovalStatus.PENDING and request.is_expired():
                request.status = ApprovalStatus.EXPIRED
                request.resolved_at = datetime.utcnow().isoformat()
                expired.append(request)
                self._notify('on_expire', request)
        
        return expired

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific request."""
        return self._requests.get(request_id)

    def get_pending(self, action_type: Optional[str] = None) -> List[ApprovalRequest]:
        """Get all pending requests."""
        pending = [
            r for r in self._requests.values()
            if r.is_pending()
        ]
        
        if action_type:
            pending = [r for r in pending if r.action_type == action_type]
        
        return sorted(pending, key=lambda r: r.created_at, reverse=True)

    def get_by_status(
        self,
        status: ApprovalStatus,
        limit: int = 100,
    ) -> List[ApprovalRequest]:
        """Get requests by status."""
        requests = [
            r for r in self._requests.values()
            if r.status == status
        ]
        return sorted(requests, key=lambda r: r.created_at, reverse=True)[:limit]

    def register_callback(
        self,
        event: str,
        callback: Callable,
    ) -> None:
        """Register a callback for approval events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def add_rule(self, rule: ApprovalRule) -> None:
        """Add an approval rule."""
        self._rules.append(rule)

    def _get_rule(self, action_type: str) -> Optional[ApprovalRule]:
        """Get rule for an action type."""
        for rule in self._rules:
            if rule.action_type == action_type:
                return rule
        return None

    def _notify(self, event: str, request: ApprovalRequest) -> None:
        """Notify callbacks of an event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(request)
            except Exception as e:
                logger.error(f"Approval callback error: {e}")


def should_require_approval(
    action_type: str,
    confidence: float,
) -> bool:
    """Quick check if an action requires approval."""
    workflow = get_approval_workflow()
    rule = workflow._get_rule(action_type)
    
    if not rule:
        return False
    
    if not rule.requires_approval:
        return False
    
    return confidence < rule.confidence_threshold


_approval_workflow: Optional[ApprovalWorkflow] = None


def get_approval_workflow() -> ApprovalWorkflow:
    """Get global approval workflow."""
    global _approval_workflow
    if _approval_workflow is None:
        _approval_workflow = ApprovalWorkflow()
    return _approval_workflow
