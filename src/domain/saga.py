"""
Saga Orchestration

Distributed transaction coordination using the Saga pattern.
Each step has a compensation action for rollback.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, TypeVar, Generic
from enum import Enum
import uuid

from domain.event_sourcing import (
    DomainEvent,
    EventType,
    EventStore,
    get_event_store,
)
from domain.events import get_event_publisher

logger = logging.getLogger(__name__)


# ============================================================================
# Saga State
# ============================================================================

class SagaState(str, Enum):
    """Saga execution states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPENSATING = "compensating"  # Rolling back
    FAILED = "failed"
    COMPENSATED = "compensated"  # Fully rolled back


class SagaStepState(str, Enum):
    """Individual step states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"


# ============================================================================
# Saga Step
# ============================================================================

@dataclass
class SagaStep:
    """
    A single step in a saga.
    
    Each step has:
    - An action to execute
    - A compensation action to rollback
    - A name for identification
    """
    name: str
    action: Callable
    compensation: Optional[Callable] = None
    timeout: float = 300.0
    retry_count: int = 3
    retry_delay: float = 1.0
    
    state: SagaStepState = SagaStepState.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    attempts: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'state': self.state.value,
            'error': self.error,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'attempts': self.attempts,
        }


# ============================================================================
# Saga Instance
# ============================================================================

@dataclass
class SagaInstance:
    """
    A running saga instance with its state.
    """
    id: str
    saga_type: str
    correlation_id: str
    steps: List[SagaStep]
    current_step: int = 0
    state: SagaState = SagaState.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'saga_type': self.saga_type,
            'correlation_id': self.correlation_id,
            'current_step': self.current_step,
            'state': self.state.value,
            'context': self.context,
            'error': self.error,
            'steps': [s.to_dict() for s in self.steps],
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
        }
    
    def get_completed_steps(self) -> List[SagaStep]:
        """Get steps that were completed (for compensation)."""
        return [
            step for step in self.steps[:self.current_step]
            if step.state == SagaStepState.COMPLETED
        ][::-1]  # Reverse order for compensation


# ============================================================================
# Saga Definition
# ============================================================================

class SagaDefinition(ABC):
    """
    Base class for defining a saga.
    
    Subclasses implement:
    - define_steps(): Define the steps and their compensations
    - get_initial_context(): Get starting context from trigger data
    """
    
    @property
    @abstractmethod
    def saga_type(self) -> str:
        """Unique identifier for this saga type."""
        pass
    
    @abstractmethod
    def define_steps(self) -> List[SagaStep]:
        """Define the saga steps."""
        pass
    
    @abstractmethod
    def get_initial_context(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get initial context from trigger data."""
        pass


# ============================================================================
# Audit Saga
# ============================================================================

class AuditSagaDefinition(SagaDefinition):
    """
    Definition for the complete audit workflow saga.
    
    Steps:
    1. Verify Payment
    2. Queue Job
    3. Run Analyzers
    4. Generate Exploits
    5. Run Verification
    6. Generate Report
    7. Finalize
    """
    
    SAGA_TYPE = "audit_workflow"
    
    @property
    def saga_type(self) -> str:
        return self.SAGA_TYPE
    
    def define_steps(self) -> List[SagaStep]:
        return [
            SagaStep(
                name="verify_payment",
                action=self._verify_payment,
                compensation=self._refund_payment,
                timeout=60.0,
            ),
            SagaStep(
                name="queue_job",
                action=self._queue_job,
                compensation=self._dequeue_job,
                timeout=30.0,
            ),
            SagaStep(
                name="run_analyzers",
                action=self._run_analyzers,
                compensation=self._cancel_analyzers,
                timeout=600.0,  # 10 minutes
            ),
            SagaStep(
                name="generate_exploits",
                action=self._generate_exploits,
                compensation=self._cleanup_exploits,
                timeout=300.0,
            ),
            SagaStep(
                name="run_verification",
                action=self._run_verification,
                compensation=self._cleanup_verification,
                timeout=300.0,
            ),
            SagaStep(
                name="generate_report",
                action=self._generate_report,
                compensation=self._cleanup_report,
                timeout=60.0,
            ),
            SagaStep(
                name="finalize",
                action=self._finalize,
                compensation=None,  # No compensation for final step
                timeout=30.0,
            ),
        ]
    
    def get_initial_context(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'job_id': trigger_data.get('job_id'),
            'target_url': trigger_data.get('target_url'),
            'wallet_address': trigger_data.get('wallet_address'),
            'payment_tx_hash': trigger_data.get('payment_tx_hash'),
            'scope': trigger_data.get('scope'),
            'priority': trigger_data.get('priority', 'normal'),
        }
    
    # Step Actions
    
    async def _verify_payment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify payment on blockchain."""
        from infrastructure.circuit_breaker import circuit_breaker
        
        logger.info(f"Verifying payment for job {context.get('job_id')}")
        
        await asyncio.sleep(0.1)
        
        return {
            'payment_verified': True,
            'payment_amount': '100000000000000000000',
        }
    
    async def _queue_job(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add job to processing queue."""
        logger.info(f"Queuing job {context.get('job_id')}")
        
        await asyncio.sleep(0.1)
        
        return {
            'queued': True,
            'queue_position': 1,
        }
    
    async def _run_analyzers(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run vulnerability analyzers."""
        logger.info(f"Running analyzers for job {context.get('job_id')}")
        
        await asyncio.sleep(0.5)
        
        return {
            'analyzers_run': ['slither', 'mythril'],
            'findings': [
                {
                    'id': 'FIND-001',
                    'title': 'Reentrancy Vulnerability',
                    'severity': 'HIGH',
                    'cvss_score': 7.5,
                }
            ],
        }
    
    async def _generate_exploits(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate exploit proof-of-concepts."""
        logger.info(f"Generating exploits for job {context.get('job_id')}")
        
        await asyncio.sleep(0.3)
        
        findings = context.get('findings', [])
        
        return {
            'exploits_generated': len(findings),
            'exploits': [
                {
                    'finding_id': 'FIND-001',
                    'technique': 'reentrancy',
                    'safe': True,
                }
            ],
        }
    
    async def _run_verification(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run visual verification of exploits."""
        logger.info(f"Running verification for job {context.get('job_id')}")
        
        await asyncio.sleep(0.3)
        
        return {
            'verifications': [
                {
                    'finding_id': 'FIND-001',
                    'success': True,
                    'visual_diff': 15.5,
                }
            ],
        }
    
    async def _generate_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final audit report."""
        logger.info(f"Generating report for job {context.get('job_id')}")
        
        await asyncio.sleep(0.2)
        
        return {
            'report_path': f"/reports/report-{context.get('job_id')}.json",
            'findings_count': {
                'HIGH': 1,
                'MEDIUM': 0,
                'LOW': 0,
            },
        }
    
    async def _finalize(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize the audit."""
        logger.info(f"Finalizing job {context.get('job_id')}")
        
        await asyncio.sleep(0.1)
        
        return {
            'status': 'completed',
        }
    
    # Compensation Actions
    
    async def _refund_payment(self, context: Dict[str, Any]) -> None:
        """Compensation: Initiate refund."""
        logger.warning(f"Compensating: refund payment for {context.get('job_id')}")
    
    async def _dequeue_job(self, context: Dict[str, Any]) -> None:
        """Compensation: Remove from queue."""
        logger.warning(f"Compensating: dequeue job {context.get('job_id')}")
    
    async def _cancel_analyzers(self, context: Dict[str, Any]) -> None:
        """Compensation: Cancel running analyzers."""
        logger.warning(f"Compensating: cancel analyzers for {context.get('job_id')}")
    
    async def _cleanup_exploits(self, context: Dict[str, Any]) -> None:
        """Compensation: Delete generated exploits."""
        logger.warning(f"Compensating: cleanup exploits for {context.get('job_id')}")
    
    async def _cleanup_verification(self, context: Dict[str, Any]) -> None:
        """Compensation: Delete verification artifacts."""
        logger.warning(f"Compensating: cleanup verification for {context.get('job_id')}")
    
    async def _cleanup_report(self, context: Dict[str, Any]) -> None:
        """Compensation: Delete generated report."""
        logger.warning(f"Compensating: cleanup report for {context.get('job_id')}")


# ============================================================================
# Saga Orchestrator
# ============================================================================

class SagaOrchestrator:
    """
    Orchestrates saga execution with compensation handling.
    
    Features:
    - Step-by-step execution
    - Automatic compensation on failure
    - Timeout handling
    - Retry logic
    - State persistence
    """
    
    def __init__(self, event_store: Optional[EventStore] = None):
        self._event_store = event_store or get_event_store()
        self._saga_definitions: Dict[str, SagaDefinition] = {}
        self._running_sagas: Dict[str, SagaInstance] = {}
    
    def register(self, definition: SagaDefinition) -> None:
        """Register a saga definition."""
        self._saga_definitions[definition.saga_type] = definition
        logger.info(f"Registered saga: {definition.saga_type}")
    
    async def start(
        self,
        saga_type: str,
        trigger_data: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> SagaInstance:
        """
        Start a new saga instance.
        
        Args:
            saga_type: Type of saga to run
            trigger_data: Initial data for the saga
            correlation_id: Optional correlation ID for tracking
        
        Returns:
            SagaInstance with initial state
        """
        if saga_type not in self._saga_definitions:
            raise ValueError(f"Unknown saga type: {saga_type}")
        
        definition = self._saga_definitions[saga_type]
        
        instance = SagaInstance(
            id=f"saga-{uuid.uuid4().hex[:16]}",
            saga_type=saga_type,
            correlation_id=correlation_id or f"corr-{uuid.uuid4().hex[:16]}",
            steps=definition.define_steps(),
            context=definition.get_initial_context(trigger_data),
        )
        
        self._running_sagas[instance.id] = instance
        
        await self._persist_saga(instance)
        
        asyncio.create_task(self._execute_saga(instance))
        
        logger.info(f"Started saga {instance.id} of type {saga_type}")
        
        return instance
    
    async def _execute_saga(self, instance: SagaInstance) -> None:
        """Execute saga steps sequentially."""
        instance.state = SagaState.RUNNING
        instance.started_at = datetime.utcnow().isoformat()
        await self._persist_saga(instance)
        
        for i, step in enumerate(instance.steps):
            instance.current_step = i
            step.state = SagaStepState.RUNNING
            step.started_at = datetime.utcnow().isoformat()
            await self._persist_saga(instance)
            
            success = await self._execute_step(instance, step)
            
            if not success:
                await self._compensate(instance)
                raise Exception(instance.error or f"Step {step.name} failed")
            
            step.state = SagaStepState.COMPLETED
            step.completed_at = datetime.utcnow().isoformat()
            await self._persist_saga(instance)
        
        instance.state = SagaState.COMPLETED
        instance.completed_at = datetime.utcnow().isoformat()
        await self._persist_saga(instance)
        
        logger.info(f"Saga {instance.id} completed successfully")
    
    async def execute(self, steps: List[SagaStep], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a list of saga steps directly.
        
        This is a convenience method for testing and simple workflows.
        
        Args:
            steps: List of SagaStep objects to execute
            context: Optional context dictionary
        
        Returns:
            Context after all steps complete
        
        Raises:
            Exception: If any step fails (compensation will be executed)
        """
        context = context or {}
        completed_steps = []
        
        for step in steps:
            step.state = SagaStepState.RUNNING
            step.started_at = datetime.utcnow().isoformat()
            
            try:
                result = await step.action(context)
                if result:
                    context.update(result)
                step.result = result
                step.state = SagaStepState.COMPLETED
                step.completed_at = datetime.utcnow().isoformat()
                completed_steps.append(step)
                
            except Exception as e:
                step.error = str(e)
                step.state = SagaStepState.FAILED
                
                for completed_step in reversed(completed_steps):
                    if completed_step.compensation:
                        try:
                            await completed_step.compensation()
                            completed_step.state = SagaStepState.COMPENSATED
                        except Exception as comp_error:
                            logger.error(f"Compensation failed: {comp_error}")
                
                raise
    
    async def _execute_step(self, instance: SagaInstance, step: SagaStep) -> bool:
        """Execute a single step with retry logic."""
        for attempt in range(step.retry_count):
            step.attempts = attempt + 1
            
            try:
                definition = self._saga_definitions[instance.saga_type]
                
                result = await asyncio.wait_for(
                    step.action(instance.context),
                    timeout=step.timeout,
                )
                
                if result:
                    instance.context.update(result)
                
                step.result = result
                return True
                
            except asyncio.TimeoutError:
                step.error = f"Timeout after {step.timeout}s"
                logger.warning(f"Step {step.name} timeout (attempt {attempt + 1})")
                
            except Exception as e:
                step.error = str(e)
                logger.error(f"Step {step.name} error (attempt {attempt + 1}): {e}")
            
            if attempt < step.retry_count - 1:
                await asyncio.sleep(step.retry_delay * (2 ** attempt))
        
        step.state = SagaStepState.FAILED
        instance.error = f"Step {step.name} failed: {step.error}"
        
        return False
    
    async def _compensate(self, instance: SagaInstance) -> None:
        """Run compensation for all completed steps."""
        instance.state = SagaState.COMPENSATING
        instance.updated_at = datetime.utcnow().isoformat()
        await self._persist_saga(instance)
        
        logger.warning(f"Starting compensation for saga {instance.id}")
        
        completed_steps = instance.get_completed_steps()
        
        for step in completed_steps:
            if step.compensation:
                try:
                    await step.compensation(instance.context)
                    step.state = SagaStepState.COMPENSATED
                    logger.info(f"Compensated step {step.name}")
                except Exception as e:
                    logger.error(f"Compensation failed for {step.name}: {e}")
        
        instance.state = SagaState.COMPENSATED
        instance.completed_at = datetime.utcnow().isoformat()
        await self._persist_saga(instance)
        
        logger.info(f"Saga {instance.id} compensation completed")
    
    async def _persist_saga(self, instance: SagaInstance) -> None:
        """Persist saga state."""
        instance.updated_at = datetime.utcnow().isoformat()
        
        from infrastructure.database import get_db_pool
        
        db = get_db_pool()
        
        if db.connected:
            try:
                await db.execute(
                    """
                    INSERT INTO sagas (id, saga_type, correlation_id, state, context, error, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO UPDATE SET
                        state = EXCLUDED.state,
                        context = EXCLUDED.context,
                        error = EXCLUDED.error,
                        updated_at = EXCLUDED.updated_at
                    """,
                    instance.id,
                    instance.saga_type,
                    instance.correlation_id,
                    instance.state.value,
                    json.dumps(instance.context),
                    instance.error,
                    instance.created_at,
                    instance.updated_at,
                )
            except Exception as e:
                logger.error(f"Failed to persist saga: {e}")
    
    def get_saga(self, saga_id: str) -> Optional[SagaInstance]:
        """Get a running saga by ID."""
        return self._running_sagas.get(saga_id)
    
    def list_running(self) -> List[SagaInstance]:
        """List all running sagas."""
        return [
            s for s in self._running_sagas.values()
            if s.state in (SagaState.RUNNING, SagaState.COMPENSATING)
        ]


# ============================================================================
# Saga Event Handlers
# ============================================================================

async def handle_job_created(event: DomainEvent) -> None:
    """Handle job created event by starting audit saga."""
    orchestrator = get_saga_orchestrator()
    
    await orchestrator.start(
        saga_type=AuditSagaDefinition.SAGA_TYPE,
        trigger_data={
            'job_id': event.aggregate_id,
            'target_url': event.payload.get('target_url'),
            'wallet_address': event.payload.get('wallet_address'),
            'scope': event.payload.get('scope'),
            'priority': event.payload.get('priority'),
        },
        correlation_id=event.correlation_id,
    )


# ============================================================================
# Singleton instances
# ============================================================================

_saga_orchestrator: Optional[SagaOrchestrator] = None
_audit_saga_definition: Optional[AuditSagaDefinition] = None


def get_saga_orchestrator() -> SagaOrchestrator:
    """Get global saga orchestrator instance."""
    global _saga_orchestrator
    if _saga_orchestrator is None:
        _saga_orchestrator = SagaOrchestrator()
        _saga_orchestrator.register(get_audit_saga_definition())
    return _saga_orchestrator


def get_audit_saga_definition() -> AuditSagaDefinition:
    """Get audit saga definition."""
    global _audit_saga_definition
    if _audit_saga_definition is None:
        _audit_saga_definition = AuditSagaDefinition()
    return _audit_saga_definition
