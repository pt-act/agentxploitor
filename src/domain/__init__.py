"""
Domain Module

Domain-driven design components for AgentxploiTor:
- Event Sourcing: Immutable audit trail
- CQRS: Command-Query Responsibility Segregation
- Events: Domain events and event bus
- Saga: Distributed transaction orchestration
"""

from domain.event_sourcing import (
    EventType,
    DomainEvent,
    EventStore,
    AggregateRoot,
    JobAggregate,
    JobRepository,
    JobCreatedEvent,
    JobStateChangedEvent,
    PaymentVerifiedEvent,
    ScanStartedEvent,
    FindingDiscoveredEvent,
    ExploitGeneratedEvent,
    JobCompletedEvent,
    JobFailedEvent,
    get_event_store,
    get_job_repository,
)

from domain.cqrs import (
    JobReadModel,
    FindingReadModel,
    WorkspaceReadModel,
    Projection,
    JobProjection,
    FindingProjection,
    ProjectionManager,
    JobReadRepository,
    get_job_projection,
    get_finding_projection,
    get_projection_manager,
    get_job_read_repository,
)

from domain.events import (
    EventBus,
    WebhookConfig,
    WebhookRegistry,
    WebhookSender,
    WebhookDelivery,
    EventPublisher,
    create_slack_webhook,
    create_discord_webhook,
    create_generic_webhook,
    get_event_bus,
    get_webhook_registry,
    get_webhook_sender,
    get_event_publisher,
)

from domain.saga import (
    SagaState,
    SagaStepState,
    SagaStep,
    SagaInstance,
    SagaDefinition,
    SagaOrchestrator,
    AuditSagaDefinition,
    get_saga_orchestrator,
    get_audit_saga_definition,
)


__all__ = [
    # Event Sourcing
    'EventType',
    'DomainEvent',
    'EventStore',
    'AggregateRoot',
    'JobAggregate',
    'JobRepository',
    'JobCreatedEvent',
    'JobStateChangedEvent',
    'PaymentVerifiedEvent',
    'ScanStartedEvent',
    'FindingDiscoveredEvent',
    'ExploitGeneratedEvent',
    'JobCompletedEvent',
    'JobFailedEvent',
    'get_event_store',
    'get_job_repository',
    
    # CQRS
    'JobReadModel',
    'FindingReadModel',
    'WorkspaceReadModel',
    'Projection',
    'JobProjection',
    'FindingProjection',
    'ProjectionManager',
    'JobReadRepository',
    'get_job_projection',
    'get_finding_projection',
    'get_projection_manager',
    'get_job_read_repository',
    
    # Events
    'EventBus',
    'WebhookConfig',
    'WebhookRegistry',
    'WebhookSender',
    'WebhookDelivery',
    'EventPublisher',
    'create_slack_webhook',
    'create_discord_webhook',
    'create_generic_webhook',
    'get_event_bus',
    'get_webhook_registry',
    'get_webhook_sender',
    'get_event_publisher',
    
    # Saga
    'SagaState',
    'SagaStepState',
    'SagaStep',
    'SagaInstance',
    'SagaDefinition',
    'SagaOrchestrator',
    'AuditSagaDefinition',
    'get_saga_orchestrator',
    'get_audit_saga_definition',
]
