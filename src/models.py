"""
AgentxploiTor Domain Models

Typed domain objects with validation for the security agent.
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal, Protocol, runtime_checkable

from exceptions import AgentError, SafetyViolationError


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PENDING_PAYMENT = "pending_payment"
    PAYMENT_VERIFIED = "payment_verified"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


VALID_TRANSITIONS: Dict[JobStatus, List[JobStatus]] = {
    JobStatus.QUEUED: [JobStatus.PENDING_PAYMENT, JobStatus.IN_PROGRESS, JobStatus.CANCELLED],
    JobStatus.PENDING_PAYMENT: [JobStatus.PAYMENT_VERIFIED, JobStatus.CANCELLED],
    JobStatus.PAYMENT_VERIFIED: [JobStatus.IN_PROGRESS, JobStatus.CANCELLED],
    JobStatus.IN_PROGRESS: [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED],
    JobStatus.COMPLETED: [],
    JobStatus.FAILED: [JobStatus.QUEUED],
    JobStatus.CANCELLED: [JobStatus.QUEUED],
}


def generate_session_id(seed: Optional[str] = None) -> str:
    if seed:
        return f"session-{hashlib.sha256(seed.encode()).hexdigest()[:16]}"
    return f"session-{uuid.uuid4().hex[:16]}"


def generate_job_id() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"job-{timestamp}-{uuid.uuid4().hex[:8]}"


def sanitize_filename(name: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return safe[:200]


def validate_cvss_score(score: float) -> float:
    if not 0.0 <= score <= 10.0:
        raise ValueError(f"CVSS score {score} out of range [0.0, 10.0]")
    return round(score, 1)


@runtime_checkable
class PerceptionProvider(Protocol):
    """Protocol for browser perception providers (enables dependency injection)."""
    
    async def navigate(self, url: str) -> None: ...
    async def capture_perception(self) -> "VisualPerception": ...
    async def click(self, selector: str) -> None: ...
    async def type_text(self, selector: str, text: str) -> None: ...
    async def screenshot(self, path: str) -> None: ...
    async def visual_diff(self, before: str, after: str) -> Dict[str, Any]: ...
    async def close(self) -> None: ...


@dataclass
class VisualPerception:
    """Captured visual state of a page."""
    url: str
    screenshot_base64: str
    dom_tree: Optional[Dict[str, Any]] = None
    viewport: Optional[Dict[str, int]] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'url': self.url,
            'screenshot_base64': self.screenshot_base64[:100] + '...' if len(self.screenshot_base64) > 100 else self.screenshot_base64,
            'dom_tree': self.dom_tree,
            'viewport': self.viewport,
            'timestamp': self.timestamp
        }


@dataclass
class ProofMetadata:
    """Metadata describing proof artifacts."""
    output_dir: str
    vulnerability_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    before_screenshot: Optional[str] = None
    after_screenshot: Optional[str] = None
    diff_percentage: Optional[float] = None
    diff_pixels: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'output_dir': self.output_dir,
            'vulnerability_id': self.vulnerability_id,
            'created_at': self.created_at,
            'before_screenshot': self.before_screenshot,
            'after_screenshot': self.after_screenshot,
            'diff_percentage': self.diff_percentage,
            'diff_pixels': self.diff_pixels,
        }


@dataclass
class Vulnerability:
    """Discovered vulnerability with validated fields."""
    id: str
    title: str
    description: str
    severity: Severity
    cvss_score: float
    location: str
    exploit_scenario: str
    expected_outcome: str
    target_url: Optional[str] = None
    analyzer: Optional[str] = None
    confidence: float = 1.0
    
    def __post_init__(self):
        if isinstance(self.severity, str):
            self.severity = Severity(self.severity.upper())
        self.cvss_score = validate_cvss_score(self.cvss_score)
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence {self.confidence} out of range [0.0, 1.0]")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'cvss_score': self.cvss_score,
            'location': self.location,
            'exploit_scenario': self.exploit_scenario,
            'expected_outcome': self.expected_outcome,
            'target_url': self.target_url,
            'analyzer': self.analyzer,
            'confidence': self.confidence
        }


@dataclass
class Exploit:
    """Generated exploit with safety constraints."""
    vulnerability_id: str
    technique: str
    payload: str
    steps: List[str]
    success_indicators: List[str]
    safety_constraints: List[str] = field(default_factory=lambda: [
        "no_real_fund_movement",
        "no_destructive_actions",
        "sandbox_execution_only"
    ])
    
    def __post_init__(self):
        if not self.safety_constraints:
            self.safety_constraints = [
                "no_real_fund_movement",
                "no_destructive_actions",
                "sandbox_execution_only"
            ]
    
    def validate_safety(self) -> bool:
        dangerous_patterns = [
            "mainnet",
            "production",
            "real funds",
            "actual transfer"
        ]
        payload_lower = self.payload.lower()
        for pattern in dangerous_patterns:
            if pattern in payload_lower:
                raise SafetyViolationError(
                    f"Exploit violates safety constraint: contains '{pattern}'",
                    constraint_violated="sandbox_execution_only",
                    vulnerability_id=self.vulnerability_id
                )
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'vulnerability_id': self.vulnerability_id,
            'technique': self.technique,
            'payload': self.payload,
            'steps': self.steps,
            'success_indicators': self.success_indicators,
            'safety_constraints': self.safety_constraints
        }


@dataclass
class VerificationResult:
    """Visual verification result"""
    success: bool
    before_state: Optional[VisualPerception]
    after_state: Optional[VisualPerception]
    visual_diff: float
    proof_path: str
    evidence: List[str]
    reason: Optional[str] = None
    vulnerability_id: Optional[str] = None
    
    def __post_init__(self):
        if self.visual_diff < 0:
            raise ValueError(f"Visual diff cannot be negative: {self.visual_diff}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'visual_diff': self.visual_diff,
            'proof_path': self.proof_path,
            'evidence': self.evidence,
            'reason': self.reason,
            'before_url': self.before_state.url if self.before_state else None,
            'after_url': self.after_state.url if self.after_state else None,
            'vulnerability_id': self.vulnerability_id,
        }


@dataclass
class SelfEvaluation:
    """Agent's self-evaluation with weighted scoring."""
    satisfactory: bool
    confidence: float
    issues: List[str]
    evidence: List[str]
    issue_weights: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence {self.confidence} out of range [0.0, 1.0]")
    
    @classmethod
    def calculate_confidence(
        cls, 
        evidence: List[str], 
        issues: List[str],
        issue_weights: Optional[Dict[str, float]] = None
    ) -> float:
        prior = 0.5
        if issue_weights is None:
            issue_weights = {}
        
        for issue in issues:
            weight = issue_weights.get(issue, 0.3)
            prior = max(0.0, prior - weight * 0.5)
        
        for ev in evidence:
            prior = min(1.0, prior + 0.1)
        
        return round(prior, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'satisfactory': self.satisfactory,
            'confidence': self.confidence,
            'issues': self.issues,
            'evidence': self.evidence,
            'issue_weights': self.issue_weights
        }


@dataclass
class JobSession:
    """Persistent job session with state history."""
    id: str
    target_url: str
    status: JobStatus
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    state_history: List[Dict[str, Any]] = field(default_factory=list)
    payment_tx_hash: Optional[str] = None
    payment_amount: Optional[str] = None
    wallet_address: Optional[str] = None
    findings_count: Optional[Dict[str, int]] = None
    report_path: Optional[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = JobStatus(self.status.lower())
        if not self.state_history:
            self.state_history = [{
                'status': self.status.value,
                'timestamp': self.created_at
            }]
    
    def transition_to(self, new_status: JobStatus, reason: Optional[str] = None) -> None:
        if new_status not in VALID_TRANSITIONS.get(self.status, []):
            from exceptions import JobStateError
            raise JobStateError(
                f"Invalid transition from {self.status.value} to {new_status.value}",
                current_state=self.status.value,
                attempted_state=new_status.value,
                job_id=self.id
            )
        
        self.status = new_status
        self.updated_at = datetime.utcnow().isoformat()
        self.state_history.append({
            'status': new_status.value,
            'timestamp': self.updated_at,
            'reason': reason
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'target_url': self.target_url,
            'status': self.status.value,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'state_history': self.state_history,
            'payment_tx_hash': self.payment_tx_hash,
            'payment_amount': self.payment_amount,
            'wallet_address': self.wallet_address,
            'findings_count': self.findings_count,
            'report_path': self.report_path,
            'error': self.error
        }


@dataclass
class AuditReport:
    """Complete audit report with all findings and evidence."""
    id: str
    job_id: str
    target_url: str
    vulnerabilities: List[Vulnerability]
    exploits: List[Exploit]
    verifications: List[VerificationResult]
    evaluation: SelfEvaluation
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @property
    def summary(self) -> Dict[str, int]:
        counts = {s.value: 0 for s in Severity}
        for v in self.vulnerabilities:
            counts[v.severity.value] += 1
        return counts
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'job_id': self.job_id,
            'target_url': self.target_url,
            'summary': self.summary,
            'vulnerabilities': [v.to_dict() for v in self.vulnerabilities],
            'exploits': [e.to_dict() for e in self.exploits],
            'verifications': [v.to_dict() for v in self.verifications],
            'evaluation': self.evaluation.to_dict(),
            'created_at': self.created_at
        }
