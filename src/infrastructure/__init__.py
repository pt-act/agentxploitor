"""
Infrastructure Module

Critical infrastructure components for AgentxploiTor A+ Roadmap.

Components:
- config: Configuration management
- redis_pool: Redis connection pooling
- redis_queue: Distributed job queue
- circuit_breaker: Circuit breaker pattern for resilience
- database: PostgreSQL connection pooling
- migrations: Database migration runner
- outbox: Outbox pattern for reliable events
- health: Health check endpoints
"""

from infrastructure.config import (
    RedisConfig,
    PostgresConfig,
    CircuitBreakerConfig,
    InfrastructureConfig,
)

from infrastructure.redis_pool import (
    RedisPool,
    get_redis_pool,
    init_redis,
    close_redis,
)

from infrastructure.redis_queue import (
    RedisJobQueue,
    QueuePriority,
    create_redis_queue,
)

from infrastructure.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    CircuitBreakerRegistry,
    get_circuit_registry,
    circuit_breaker,
)

from infrastructure.database import (
    DatabasePool,
    get_db_pool,
    init_database,
    close_database,
)

from infrastructure.migrations import (
    MigrationRunner,
    run_migrations,
    check_migrations,
)

from infrastructure.outbox import (
    OutboxWriter,
    OutboxProcessor,
    OutboxEvent,
    EventType,
    get_outbox_writer,
    get_outbox_processor,
)

from infrastructure.health import (
    HealthChecker,
    HealthStatus,
    ComponentHealth,
    SystemHealth,
    get_health_checker,
)


__all__ = [
    # Config
    'RedisConfig',
    'PostgresConfig',
    'CircuitBreakerConfig',
    'InfrastructureConfig',
    
    # Redis
    'RedisPool',
    'get_redis_pool',
    'init_redis',
    'close_redis',
    
    # Queue
    'RedisJobQueue',
    'QueuePriority',
    'create_redis_queue',
    
    # Circuit Breaker
    'CircuitBreaker',
    'CircuitState',
    'CircuitOpenError',
    'CircuitBreakerRegistry',
    'get_circuit_registry',
    'circuit_breaker',
    
    # Database
    'DatabasePool',
    'get_db_pool',
    'init_database',
    'close_database',
    
    # Migrations
    'MigrationRunner',
    'run_migrations',
    'check_migrations',
    
    # Outbox
    'OutboxWriter',
    'OutboxProcessor',
    'OutboxEvent',
    'EventType',
    'get_outbox_writer',
    'get_outbox_processor',
    
    # Health
    'HealthChecker',
    'HealthStatus',
    'ComponentHealth',
    'SystemHealth',
    'get_health_checker',
]
