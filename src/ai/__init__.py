"""
AI Module - Semantic Safety, Confidence Calibration, Explainability, Approval Workflow

This module provides AI augmentation features for the security analysis platform.
"""

from ai.semantic_safety import (
    SafetyLevel,
    SafetyCheck,
    SemanticSafetyAnalyzer,
    ExploitTemplateLibrary,
    analyze_payload_safety,
    get_safety_analyzer,
)

from ai.confidence import (
    PredictionRecord,
    CalibrationMetrics,
    ConfidenceCalibrator,
    calibrate_confidence,
    get_calibrator,
)

from ai.explainability import (
    ReasoningStepType,
    ReasoningStep,
    ReasoningTrace,
    DecisionNode,
    ExplainabilityEngine,
    get_explainability_engine,
)

from ai.approval import (
    ApprovalStatus,
    ApprovalPriority,
    ApprovalRequest,
    ApprovalRule,
    ApprovalWorkflow,
    should_require_approval,
    get_approval_workflow,
)


__all__ = [
    'SafetyLevel',
    'SafetyCheck',
    'SemanticSafetyAnalyzer',
    'ExploitTemplateLibrary',
    'analyze_payload_safety',
    'get_safety_analyzer',
    'PredictionRecord',
    'CalibrationMetrics',
    'ConfidenceCalibrator',
    'calibrate_confidence',
    'get_calibrator',
    'ReasoningStepType',
    'ReasoningStep',
    'ReasoningTrace',
    'DecisionNode',
    'ExplainabilityEngine',
    'get_explainability_engine',
    'ApprovalStatus',
    'ApprovalPriority',
    'ApprovalRequest',
    'ApprovalRule',
    'ApprovalWorkflow',
    'should_require_approval',
    'get_approval_workflow',
]
