"""
Infrastructure Configuration

Configuration for Redis, PostgreSQL, and other infrastructure components.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RedisConfig:
    """Redis connection configuration."""
    host: str = field(default_factory=lambda: os.getenv('REDIS_HOST', 'localhost'))
    port: int = field(default_factory=lambda: int(os.getenv('REDIS_PORT', '6379')))
    db: int = field(default_factory=lambda: int(os.getenv('REDIS_DB', '0')))
    password: Optional[str] = field(default_factory=lambda: os.getenv('REDIS_PASSWORD'))
    max_connections: int = field(default_factory=lambda: int(os.getenv('REDIS_MAX_CONNECTIONS', '50')))
    socket_timeout: float = field(default_factory=lambda: float(os.getenv('REDIS_SOCKET_TIMEOUT', '5.0')))
    socket_connect_timeout: float = field(default_factory=lambda: float(os.getenv('REDIS_CONNECT_TIMEOUT', '5.0')))
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


@dataclass
class PostgresConfig:
    """PostgreSQL connection configuration."""
    host: str = field(default_factory=lambda: os.getenv('POSTGRES_HOST', 'localhost'))
    port: int = field(default_factory=lambda: int(os.getenv('POSTGRES_PORT', '5432')))
    database: str = field(default_factory=lambda: os.getenv('POSTGRES_DB', 'agentxploitor'))
    user: str = field(default_factory=lambda: os.getenv('POSTGRES_USER', 'agentxploitor'))
    password: str = field(default_factory=lambda: os.getenv('POSTGRES_PASSWORD', ''))
    min_connections: int = field(default_factory=lambda: int(os.getenv('POSTGRES_MIN_CONN', '5')))
    max_connections: int = field(default_factory=lambda: int(os.getenv('POSTGRES_MAX_CONN', '20')))
    command_timeout: float = field(default_factory=lambda: float(os.getenv('POSTGRES_TIMEOUT', '60.0')))
    
    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = field(default_factory=lambda: int(os.getenv('CIRCUIT_FAILURE_THRESHOLD', '5')))
    recovery_timeout: float = field(default_factory=lambda: float(os.getenv('CIRCUIT_RECOVERY_TIMEOUT', '60.0')))
    half_open_max_calls: int = field(default_factory=lambda: int(os.getenv('CIRCUIT_HALF_OPEN_CALLS', '3')))
    success_threshold: int = field(default_factory=lambda: int(os.getenv('CIRCUIT_SUCCESS_THRESHOLD', '3')))


@dataclass
class InfrastructureConfig:
    """Combined infrastructure configuration."""
    redis: RedisConfig = field(default_factory=RedisConfig)
    postgres: PostgresConfig = field(default_factory=PostgresConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    
    @classmethod
    def from_env(cls) -> 'InfrastructureConfig':
        """Load configuration from environment variables."""
        return cls(
            redis=RedisConfig(),
            postgres=PostgresConfig(),
            circuit_breaker=CircuitBreakerConfig(),
        )
