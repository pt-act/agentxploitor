"""
Tests for AgentxploiTor Domain Models
"""

import pytest
from datetime import datetime

from models import (
    Severity,
    JobStatus,
    VALID_TRANSITIONS,
    Vulnerability,
    Exploit,
    VerificationResult,
    SelfEvaluation,
    JobSession,
    AuditReport,
    VisualPerception,
    generate_session_id,
    generate_job_id,
    sanitize_filename,
    validate_cvss_score,
)
from exceptions import SafetyViolationError, JobStateError


class TestSeverity:
    """Tests for Severity enum."""
    
    def test_all_severities_defined(self):
        assert Severity.CRITICAL.value == "CRITICAL"
        assert Severity.HIGH.value == "HIGH"
        assert Severity.MEDIUM.value == "MEDIUM"
        assert Severity.LOW.value == "LOW"
        assert Severity.INFO.value == "INFO"
    
    def test_severity_from_string(self):
        assert Severity("CRITICAL") == Severity.CRITICAL
        assert Severity("high") == Severity.HIGH


class TestJobStatus:
    """Tests for JobStatus enum."""
    
    def test_all_statuses_defined(self):
        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.PENDING_PAYMENT.value == "pending_payment"
        assert JobStatus.PAYMENT_VERIFIED.value == "payment_verified"
        assert JobStatus.IN_PROGRESS.value == "in_progress"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"


class TestValidTransitions:
    """Tests for job state transitions."""
    
    def test_queued_can_transition_to_in_progress(self):
        assert JobStatus.IN_PROGRESS in VALID_TRANSITIONS[JobStatus.QUEUED]
    
    def test_queued_can_transition_to_cancelled(self):
        assert JobStatus.CANCELLED in VALID_TRANSITIONS[JobStatus.QUEUED]
    
    def test_completed_has_no_transitions(self):
        assert len(VALID_TRANSITIONS[JobStatus.COMPLETED]) == 0
    
    def test_failed_can_retry(self):
        assert JobStatus.QUEUED in VALID_TRANSITIONS[JobStatus.FAILED]
    
    def test_in_progress_can_complete_or_fail(self):
        transitions = VALID_TRANSITIONS[JobStatus.IN_PROGRESS]
        assert JobStatus.COMPLETED in transitions
        assert JobStatus.FAILED in transitions
        assert JobStatus.CANCELLED in transitions


class TestGenerateSessionId:
    """Tests for session ID generation."""
    
    def test_generates_unique_ids(self):
        id1 = generate_session_id()
        id2 = generate_session_id()
        
        assert id1 != id2
        assert id1.startswith("session-")
        assert id2.startswith("session-")
    
    def test_deterministic_with_seed(self):
        seed = "test-seed-123"
        id1 = generate_session_id(seed)
        id2 = generate_session_id(seed)
        
        assert id1 == id2
    
    def test_different_seeds_produce_different_ids(self):
        id1 = generate_session_id("seed1")
        id2 = generate_session_id("seed2")
        
        assert id1 != id2


class TestGenerateJobId:
    """Tests for job ID generation."""
    
    def test_generates_valid_id(self):
        job_id = generate_job_id()
        
        assert job_id.startswith("job-")
        assert len(job_id) > 10
    
    def test_includes_timestamp(self):
        job_id = generate_job_id()
        now = datetime.utcnow().strftime("%Y%m%d%H")
        
        assert now in job_id


class TestSanitizeFilename:
    """Tests for filename sanitization."""
    
    def test_removes_special_characters(self):
        assert sanitize_filename("test@file#name") == "test_file_name"
    
    def test_preserves_alphanumeric_and_underscore(self):
        assert sanitize_filename("test_file-name123") == "test_file-name123"
    
    def test_truncates_long_names(self):
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        
        assert len(result) <= 200
    
    def test_handles_empty_string(self):
        assert sanitize_filename("") == ""


class TestValidateCvssScore:
    """Tests for CVSS score validation."""
    
    def test_valid_scores(self):
        assert validate_cvss_score(0.0) == 0.0
        assert validate_cvss_score(5.5) == 5.5
        assert validate_cvss_score(10.0) == 10.0
    
    def test_rounds_to_one_decimal(self):
        assert validate_cvss_score(5.123) == 5.1
        assert validate_cvss_score(7.678) == 7.7
    
    def test_rejects_negative_scores(self):
        with pytest.raises(ValueError) as exc_info:
            validate_cvss_score(-1.0)
        
        assert "out of range" in str(exc_info.value)
    
    def test_rejects_scores_above_ten(self):
        with pytest.raises(ValueError):
            validate_cvss_score(10.5)


class TestVulnerability:
    """Tests for Vulnerability dataclass."""
    
    def test_create_vulnerability(self):
        vuln = Vulnerability(
            id="VULN-001",
            title="Test Vulnerability",
            description="Test description",
            severity=Severity.HIGH,
            cvss_score=7.5,
            location="test.sol:10",
            exploit_scenario="Test scenario",
            expected_outcome="Test outcome",
        )
        
        assert vuln.id == "VULN-001"
        assert vuln.severity == Severity.HIGH
        assert vuln.cvss_score == 7.5
    
    def test_validates_cvss_score_on_creation(self):
        with pytest.raises(ValueError):
            Vulnerability(
                id="VULN-002",
                title="Test",
                description="Test",
                severity=Severity.HIGH,
                cvss_score=15.0,
                location="test",
                exploit_scenario="Test",
                expected_outcome="Test",
            )
    
    def test_validates_confidence_range(self):
        with pytest.raises(ValueError):
            Vulnerability(
                id="VULN-003",
                title="Test",
                description="Test",
                severity=Severity.HIGH,
                cvss_score=7.5,
                location="test",
                exploit_scenario="Test",
                expected_outcome="Test",
                confidence=1.5,
            )
    
    def test_accepts_string_severity(self):
        vuln = Vulnerability(
            id="VULN-004",
            title="Test",
            description="Test",
            severity="CRITICAL",
            cvss_score=9.0,
            location="test",
            exploit_scenario="Test",
            expected_outcome="Test",
        )
        
        assert vuln.severity == Severity.CRITICAL
    
    def test_to_dict(self):
        vuln = Vulnerability(
            id="VULN-005",
            title="Test",
            description="Test",
            severity=Severity.HIGH,
            cvss_score=7.5,
            location="test",
            exploit_scenario="Test",
            expected_outcome="Test",
        )
        
        result = vuln.to_dict()
        
        assert result["severity"] == "HIGH"
        assert result["cvss_score"] == 7.5


class TestExploit:
    """Tests for Exploit dataclass."""
    
    def test_create_exploit(self):
        exploit = Exploit(
            vulnerability_id="VULN-001",
            technique="authorization_bypass",
            payload="test_payload",
            steps=["Step 1", "Step 2"],
            success_indicators=["Success"],
        )
        
        assert exploit.vulnerability_id == "VULN-001"
        assert len(exploit.steps) == 2
    
    def test_default_safety_constraints(self):
        exploit = Exploit(
            vulnerability_id="VULN-001",
            technique="test",
            payload="test",
            steps=[],
            success_indicators=[],
        )
        
        assert len(exploit.safety_constraints) == 3
        assert "no_real_fund_movement" in exploit.safety_constraints
    
    def test_validate_safety_passes_for_safe_payload(self):
        exploit = Exploit(
            vulnerability_id="VULN-001",
            technique="test",
            payload="safe testnet operation",
            steps=[],
            success_indicators=[],
        )
        
        assert exploit.validate_safety() is True
    
    def test_validate_safety_fails_for_mainnet(self):
        exploit = Exploit(
            vulnerability_id="VULN-001",
            technique="test",
            payload="execute on mainnet with real funds",
            steps=[],
            success_indicators=[],
        )
        
        with pytest.raises(SafetyViolationError):
            exploit.validate_safety()


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""
    
    def test_create_verification_result(self):
        result = VerificationResult(
            success=True,
            before_state=None,
            after_state=None,
            visual_diff=15.5,
            proof_path="/tmp/proof.png",
            evidence=["Visual change detected"],
        )
        
        assert result.success is True
        assert result.visual_diff == 15.5
    
    def test_rejects_negative_visual_diff(self):
        with pytest.raises(ValueError):
            VerificationResult(
                success=False,
                before_state=None,
                after_state=None,
                visual_diff=-5.0,
                proof_path="/tmp/proof.png",
                evidence=[],
            )
    
    def test_to_dict(self):
        result = VerificationResult(
            success=True,
            before_state=None,
            after_state=None,
            visual_diff=10.0,
            proof_path="/tmp/proof.png",
            evidence=["Evidence 1"],
            reason=None,
        )
        
        data = result.to_dict()
        
        assert data["success"] is True
        assert data["visual_diff"] == 10.0


class TestSelfEvaluation:
    """Tests for SelfEvaluation dataclass."""
    
    def test_create_evaluation(self):
        eval = SelfEvaluation(
            satisfactory=True,
            confidence=0.85,
            issues=[],
            evidence=["Page loaded"],
        )
        
        assert eval.satisfactory is True
        assert eval.confidence == 0.85
    
    def test_validates_confidence_range(self):
        with pytest.raises(ValueError):
            SelfEvaluation(
                satisfactory=False,
                confidence=1.5,
                issues=["Issue"],
                evidence=[],
            )
    
    def test_calculate_confidence_reduces_with_issues(self):
        confidence = SelfEvaluation.calculate_confidence(
            evidence=["Evidence 1"],
            issues=["Issue 1", "Issue 2"],
        )
        
        assert confidence < 0.5
    
    def test_calculate_confidence_increases_with_evidence(self):
        confidence = SelfEvaluation.calculate_confidence(
            evidence=["Evidence 1", "Evidence 2", "Evidence 3"],
            issues=[],
        )
        
        assert confidence > 0.5


class TestJobSession:
    """Tests for JobSession dataclass."""
    
    def test_create_job_session(self):
        job = JobSession(
            id="job-001",
            target_url="https://example.com",
            status=JobStatus.QUEUED,
        )
        
        assert job.id == "job-001"
        assert job.status == JobStatus.QUEUED
        assert len(job.state_history) == 1
    
    def test_valid_transition(self):
        job = JobSession(
            id="job-002",
            target_url="https://example.com",
            status=JobStatus.QUEUED,
        )
        
        job.transition_to(JobStatus.IN_PROGRESS, "Worker picked up job")
        
        assert job.status == JobStatus.IN_PROGRESS
        assert len(job.state_history) == 2
    
    def test_invalid_transition_raises_error(self):
        job = JobSession(
            id="job-003",
            target_url="https://example.com",
            status=JobStatus.COMPLETED,
        )
        
        with pytest.raises(JobStateError) as exc_info:
            job.transition_to(JobStatus.IN_PROGRESS)
        
        assert "Invalid transition" in str(exc_info.value)
    
    def test_accepts_string_status(self):
        job = JobSession(
            id="job-004",
            target_url="https://example.com",
            status="queued",
        )
        
        assert job.status == JobStatus.QUEUED


class TestAuditReport:
    """Tests for AuditReport dataclass."""
    
    def create_test_vulnerability(self) -> Vulnerability:
        return Vulnerability(
            id="VULN-TEST",
            title="Test",
            description="Test",
            severity=Severity.HIGH,
            cvss_score=7.5,
            location="test",
            exploit_scenario="Test",
            expected_outcome="Test",
        )
    
    def create_test_exploit(self) -> Exploit:
        return Exploit(
            vulnerability_id="VULN-TEST",
            technique="test",
            payload="test",
            steps=[],
            success_indicators=[],
        )
    
    def create_test_verification(self) -> VerificationResult:
        return VerificationResult(
            success=True,
            before_state=None,
            after_state=None,
            visual_diff=10.0,
            proof_path="/tmp/proof.png",
            evidence=[],
        )
    
    def create_test_evaluation(self) -> SelfEvaluation:
        return SelfEvaluation(
            satisfactory=True,
            confidence=0.85,
            issues=[],
            evidence=[],
        )
    
    def test_create_report(self):
        report = AuditReport(
            id="report-001",
            job_id="job-001",
            target_url="https://example.com",
            vulnerabilities=[self.create_test_vulnerability()],
            exploits=[self.create_test_exploit()],
            verifications=[self.create_test_verification()],
            evaluation=self.create_test_evaluation(),
        )
        
        assert report.id == "report-001"
        assert len(report.vulnerabilities) == 1
    
    def test_summary_counts_by_severity(self):
        vulns = [
            self.create_test_vulnerability(),
            Vulnerability(
                id="VULN-002",
                title="Test",
                description="Test",
                severity=Severity.CRITICAL,
                cvss_score=9.5,
                location="test",
                exploit_scenario="Test",
                expected_outcome="Test",
            ),
        ]
        
        report = AuditReport(
            id="report-002",
            job_id="job-002",
            target_url="https://example.com",
            vulnerabilities=vulns,
            exploits=[],
            verifications=[],
            evaluation=self.create_test_evaluation(),
        )
        
        summary = report.summary
        
        assert summary["HIGH"] == 1
        assert summary["CRITICAL"] == 1
    
    def test_to_dict(self):
        report = AuditReport(
            id="report-003",
            job_id="job-003",
            target_url="https://example.com",
            vulnerabilities=[self.create_test_vulnerability()],
            exploits=[self.create_test_exploit()],
            verifications=[self.create_test_verification()],
            evaluation=self.create_test_evaluation(),
        )
        
        data = report.to_dict()
        
        assert data["id"] == "report-003"
        assert "summary" in data
        assert "vulnerabilities" in data


class TestVisualPerception:
    """Tests for VisualPerception dataclass."""
    
    def test_create_perception(self):
        perception = VisualPerception(
            url="https://example.com",
            screenshot_base64="abc123",
        )
        
        assert perception.url == "https://example.com"
        assert perception.screenshot_base64 == "abc123"
    
    def test_to_dict_truncates_long_base64(self):
        long_base64 = "a" * 200
        perception = VisualPerception(
            url="https://example.com",
            screenshot_base64=long_base64,
        )
        
        data = perception.to_dict()
        
        assert "..." in data["screenshot_base64"]
        assert len(data["screenshot_base64"]) < 200
