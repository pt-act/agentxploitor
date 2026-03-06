"""
Explainable AI

Provides reasoning traces and explanations for AI decisions.
Makes the "why" behind exploit generation transparent.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class ReasoningStepType(str, Enum):
    """Types of reasoning steps."""
    OBSERVATION = "observation"
    HYPOTHESIS = "hypothesis"
    ANALYSIS = "analysis"
    DECISION = "decision"
    ACTION = "action"
    VERIFICATION = "verification"


@dataclass
class ReasoningStep:
    """A single step in the reasoning trace."""
    id: str
    step_type: ReasoningStepType
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence: Optional[float] = None
    evidence: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'step_type': self.step_type.value,
            'content': self.content,
            'timestamp': self.timestamp,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'alternatives': self.alternatives,
            'metadata': self.metadata,
        }


@dataclass
class ReasoningTrace:
    """Complete reasoning trace for a decision."""
    id: str
    decision_type: str
    target: str
    steps: List[ReasoningStep] = field(default_factory=list)
    conclusion: Optional[str] = None
    final_confidence: Optional[float] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def add_step(self, step: ReasoningStep) -> None:
        """Add a reasoning step."""
        self.steps.append(step)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'decision_type': self.decision_type,
            'target': self.target,
            'steps': [s.to_dict() for s in self.steps],
            'conclusion': self.conclusion,
            'final_confidence': self.final_confidence,
            'created_at': self.created_at,
        }


@dataclass
class DecisionNode:
    """Node in a decision tree."""
    id: str
    question: str
    answer: Optional[str] = None
    children: List['DecisionNode'] = field(default_factory=list)
    outcome: Optional[str] = None
    confidence: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'children': [c.to_dict() for c in self.children],
            'outcome': self.outcome,
            'confidence': self.confidence,
        }


class ExplainabilityEngine:
    """
    Provides explainability for AI decisions.
    
    Tracks reasoning traces and generates human-readable explanations.
    """

    EXPLOIT_STRATEGY_DECISIONS = [
        {
            'question': 'Is this a state manipulation vulnerability?',
            'yes_outcome': 'reentrancy_strategy',
            'no_question': 'Is this an access control issue?',
        },
        {
            'question': 'Is this an access control issue?',
            'yes_outcome': 'access_control_strategy',
            'no_question': 'Is this an arithmetic issue?',
        },
        {
            'question': 'Is this an arithmetic issue?',
            'yes_outcome': 'overflow_strategy',
            'no_question': 'Is this a logic flaw?',
        },
        {
            'question': 'Is this a logic flaw?',
            'yes_outcome': 'logic_exploit_strategy',
            'no_outcome': 'generic_strategy',
        },
    ]

    STRATEGY_EXPLANATIONS = {
        'reentrancy_strategy': 'This exploit targets reentrancy by recursively calling the vulnerable function before state updates complete.',
        'access_control_strategy': 'This exploit bypasses access controls by exploiting missing or weak permission checks.',
        'overflow_strategy': 'This exploit triggers integer overflow/underflow to manipulate contract state unexpectedly.',
        'logic_exploit_strategy': 'This exploit takes advantage of flawed business logic in the contract.',
        'generic_strategy': 'This exploit uses a general approach targeting the identified vulnerability pattern.',
    }

    def __init__(self):
        self._traces: Dict[str, ReasoningTrace] = {}

    def start_trace(
        self,
        decision_type: str,
        target: str,
    ) -> ReasoningTrace:
        """Start a new reasoning trace."""
        import uuid
        trace_id = f"trace-{uuid.uuid4().hex[:12]}"
        
        trace = ReasoningTrace(
            id=trace_id,
            decision_type=decision_type,
            target=target,
        )
        
        self._traces[trace_id] = trace
        return trace

    def add_observation(
        self,
        trace: ReasoningTrace,
        content: str,
        evidence: Optional[List[str]] = None,
        confidence: Optional[float] = None,
    ) -> ReasoningStep:
        """Add an observation step."""
        import uuid
        step = ReasoningStep(
            id=f"step-{uuid.uuid4().hex[:8]}",
            step_type=ReasoningStepType.OBSERVATION,
            content=content,
            evidence=evidence or [],
            confidence=confidence,
        )
        trace.add_step(step)
        return step

    def add_hypothesis(
        self,
        trace: ReasoningTrace,
        content: str,
        alternatives: Optional[List[str]] = None,
        confidence: Optional[float] = None,
    ) -> ReasoningStep:
        """Add a hypothesis step."""
        import uuid
        step = ReasoningStep(
            id=f"step-{uuid.uuid4().hex[:8]}",
            step_type=ReasoningStepType.HYPOTHESIS,
            content=content,
            alternatives=alternatives or [],
            confidence=confidence,
        )
        trace.add_step(step)
        return step

    def add_analysis(
        self,
        trace: ReasoningTrace,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReasoningStep:
        """Add an analysis step."""
        import uuid
        step = ReasoningStep(
            id=f"step-{uuid.uuid4().hex[:8]}",
            step_type=ReasoningStepType.ANALYSIS,
            content=content,
            metadata=metadata or {},
        )
        trace.add_step(step)
        return step

    def add_decision(
        self,
        trace: ReasoningTrace,
        content: str,
        confidence: float,
    ) -> ReasoningStep:
        """Add a decision step."""
        import uuid
        step = ReasoningStep(
            id=f"step-{uuid.uuid4().hex[:8]}",
            step_type=ReasoningStepType.DECISION,
            content=content,
            confidence=confidence,
        )
        trace.add_step(step)
        return step

    def finalize_trace(
        self,
        trace: ReasoningTrace,
        conclusion: str,
        confidence: float,
    ) -> None:
        """Finalize a reasoning trace."""
        trace.conclusion = conclusion
        trace.final_confidence = confidence

    def get_trace(self, trace_id: str) -> Optional[ReasoningTrace]:
        """Get a reasoning trace by ID."""
        return self._traces.get(trace_id)

    def build_decision_tree(
        self,
        vulnerability_type: str,
        context: Dict[str, Any],
    ) -> DecisionNode:
        """Build a decision tree for exploit strategy selection."""
        import uuid
        root = DecisionNode(
            id=f"decision-{uuid.uuid4().hex[:8]}",
            question=f"What is the nature of the {vulnerability_type} vulnerability?",
        )
        
        for decision in self.EXPLOIT_STRATEGY_DECISIONS:
            child = DecisionNode(
                id=f"decision-{uuid.uuid4().hex[:8]}",
                question=decision['question'],
            )
            root.children.append(child)
            
            yes_node = DecisionNode(
                id=f"decision-{uuid.uuid4().hex[:8]}",
                question="Apply this strategy?",
                outcome=decision.get('yes_outcome'),
            )
            child.children.append(yes_node)
        
        return root

    def generate_explanation(
        self,
        trace: ReasoningTrace,
        verbosity: str = 'normal',
    ) -> str:
        """Generate human-readable explanation from trace."""
        parts = []
        
        parts.append(f"## Decision: {trace.decision_type}")
        parts.append(f"**Target:** {trace.target}\n")
        
        if verbosity == 'verbose':
            parts.append("### Reasoning Steps:\n")
            for i, step in enumerate(trace.steps, 1):
                parts.append(f"{i}. **{step.step_type.value.title()}**: {step.content}")
                if step.evidence:
                    parts.append(f"   - Evidence: {', '.join(step.evidence)}")
                if step.confidence is not None:
                    parts.append(f"   - Confidence: {step.confidence:.0%}")
                if step.alternatives:
                    parts.append(f"   - Alternatives considered: {', '.join(step.alternatives)}")
                parts.append("")
        
        elif verbosity == 'normal':
            key_steps = [s for s in trace.steps if s.step_type in (
                ReasoningStepType.OBSERVATION,
                ReasoningStepType.DECISION,
            )]
            parts.append("### Key Reasoning:\n")
            for step in key_steps[-5:]:
                parts.append(f"- {step.content}")
            parts.append("")
        
        if trace.conclusion:
            parts.append(f"### Conclusion:\n{trace.conclusion}")
        
        if trace.final_confidence is not None:
            parts.append(f"\n**Confidence:** {trace.final_confidence:.0%}")
        
        return "\n".join(parts)

    def generate_why_explanation(
        self,
        strategy: str,
        vulnerability: Dict[str, Any],
    ) -> str:
        """Generate 'why this exploit' explanation."""
        explanation = self.STRATEGY_EXPLANATIONS.get(
            strategy,
            "This exploit was selected based on the vulnerability characteristics."
        )
        
        parts = [
            f"### Why this exploit strategy?\n",
            explanation,
            "",
            f"**Vulnerability matched:** {vulnerability.get('title', 'Unknown')}",
            f"**Severity:** {vulnerability.get('severity', 'Unknown')}",
            f"**Pattern:** {vulnerability.get('pattern', 'General')}",
        ]
        
        return "\n".join(parts)

    def export_trace(self, trace_id: str) -> Optional[str]:
        """Export a trace as JSON."""
        trace = self._traces.get(trace_id)
        if trace:
            return json.dumps(trace.to_dict(), indent=2)
        return None


_explainability_engine: Optional[ExplainabilityEngine] = None


def get_explainability_engine() -> ExplainabilityEngine:
    """Get global explainability engine."""
    global _explainability_engine
    if _explainability_engine is None:
        _explainability_engine = ExplainabilityEngine()
    return _explainability_engine
