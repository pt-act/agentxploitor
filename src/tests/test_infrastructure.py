"""
Tests for Infrastructure Components - Group 0

Tests for Redis queue, circuit breaker, database, and health checks.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from models import JobSession, JobStatus

from infrastructure.config import RedisConfig, PostgresConfig, CircuitBreakerConfig
from infrastructure.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    CircuitBreakerRegistry,
)
from infrastructure.redis_queue import RedisJobQueue, QueuePriority
from infrastructure.outbox import OutboxEvent, EventType
from infrastructure.health import HealthChecker, HealthStatus, ComponentHealth


class TestCircuitBreaker:
    """Tests for circuit breaker pattern."""
    
    def test_initial_state_is_closed(self):
        breaker = CircuitBreaker("test-service")
        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed is True
    
    @pytest.mark.asyncio
    async def test_success_increments_success_counter(self):
        breaker = CircuitBreaker("test")
        
        async def successful_call():
            return "success"
        
        result = await breaker.call(successful_call)
        
        assert result == "success"
        assert breaker.stats.successful_calls == 1
        assert breaker.stats.consecutive_successes == 1
    
    @pytest.mark.asyncio
    async def test_failure_increments_failure_counter(self):
        breaker = CircuitBreaker("test")
        
        async def failing_call():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            await breaker.call(failing_call)
        
        assert breaker.stats.failed_calls == 1
        assert breaker.stats.consecutive_failures == 1
    
    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self):
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60.0)
        breaker = CircuitBreaker("test", config)
        
        async def failing_call():
            raise ValueError("test error")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_call)
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.is_open is True
    
    @pytest.mark.asyncio
    async def test_rejects_when_open(self):
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60.0)
        breaker = CircuitBreaker("test", config)
        
        async def failing_call():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            await breaker.call(failing_call)
        
        assert breaker.state == CircuitState.OPEN
        
        with pytest.raises(CircuitOpenError) as exc_info:
            await breaker.call(lambda: "success")
        
        assert exc_info.value.circuit_name == "test"
    
    @pytest.mark.asyncio
    async def test_decorator_protects_function(self):
        breaker = CircuitBreaker("test")
        
        @breaker.protect
        async def protected_call():
            return "protected"
        
        result = await protected_call()
        assert result == "protected"
        assert breaker.stats.successful_calls == 1
    
    def test_reset_returns_to_closed(self):
        breaker = CircuitBreaker("test")
        breaker._state = CircuitState.OPEN
        
        breaker.reset()
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.consecutive_failures == 0
    
    def test_to_dict_exports_state(self):
        breaker = CircuitBreaker("test")
        data = breaker.to_dict()
        
        assert data['name'] == "test"
        assert data['state'] == "closed"
        assert 'stats' in data
        assert 'config' in data


class TestCircuitBreakerRegistry:
    """Tests for circuit breaker registry."""
    
    def test_get_or_create_returns_same_instance(self):
        registry = CircuitBreakerRegistry()
        
        breaker1 = registry.get_or_create("service-a")
        breaker2 = registry.get_or_create("service-a")
        
        assert breaker1 is breaker2
    
    def test_get_or_create_different_names(self):
        registry = CircuitBreakerRegistry()
        
        breaker1 = registry.get_or_create("service-a")
        breaker2 = registry.get_or_create("service-b")
        
        assert breaker1 is not breaker2
    
    def test_reset_all_resets_all_breakers(self):
        registry = CircuitBreakerRegistry()
        
        breaker1 = registry.get_or_create("service-a")
        breaker2 = registry.get_or_create("service-b")
        
        breaker1._state = CircuitState.OPEN
        breaker2._state = CircuitState.OPEN
        
        registry.reset_all()
        
        assert breaker1.state == CircuitState.CLOSED
        assert breaker2.state == CircuitState.CLOSED


class TestRedisJobQueue:
    """Tests for Redis job queue."""
    
    @pytest.fixture
    def mock_pool(self):
        pool = MagicMock()
        pool.connected = True
        return pool
    
    @pytest.fixture
    def mock_client(self):
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def job(self):
        return JobSession(
            id="job-test-001",
            target_url="https://example.com",
            status=JobStatus.QUEUED,
        )
    
    def test_calculate_score_higher_priority_lower_score(self):
        queue = RedisJobQueue()
        
        low_score = queue._calculate_score(QueuePriority.LOW)
        high_score = queue._calculate_score(QueuePriority.HIGH)
        critical_score = queue._calculate_score(QueuePriority.CRITICAL)
        
        assert critical_score < high_score < low_score
    
    def test_reconstruct_job_from_dict(self):
        queue = RedisJobQueue()
        
        data = {
            'id': 'job-test-002',
            'target_url': 'https://example.com',
            'status': 'in_progress',
            'created_at': '2026-01-01T00:00:00',
            'updated_at': '2026-01-01T00:01:00',
            'state_history': [],
            'payment_tx_hash': None,
            'payment_amount': None,
            'wallet_address': None,
            'findings_count': None,
            'report_path': None,
            'error': None,
        }
        
        job = queue._reconstruct_job(data)
        
        assert job.id == 'job-test-002'
        assert job.status == JobStatus.IN_PROGRESS
        assert job.target_url == 'https://example.com'


class TestOutboxEvent:
    """Tests for outbox event model."""
    
    def test_create_outbox_event(self):
        event = OutboxEvent(
            aggregate_type="job",
            aggregate_id="job-001",
            event_type=EventType.JOB_CREATED.value,
            payload={"target_url": "https://example.com"},
        )
        
        assert event.aggregate_type == "job"
        assert event.event_type == "job_created"
        assert event.published is False
    
    def test_to_dict(self):
        event = OutboxEvent(
            id=1,
            aggregate_type="job",
            aggregate_id="job-001",
            event_type=EventType.JOB_STATE_CHANGED.value,
            payload={"from": "queued", "to": "in_progress"},
            destination="default",
        )
        
        data = event.to_dict()
        
        assert data['id'] == 1
        assert data['aggregate_type'] == "job"
        assert data['payload']['from'] == "queued"


class TestHealthChecker:
    """Tests for health checker."""
    
    @pytest.fixture
    def health_checker(self):
        return HealthChecker()
    
    @pytest.mark.asyncio
    async def test_check_live_returns_true(self, health_checker):
        result = await health_checker.check_live()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_live_response(self, health_checker):
        response = await health_checker.get_live_response()
        
        assert response['alive'] is True
        assert 'timestamp' in response
    
    @pytest.mark.asyncio
    async def test_check_all_returns_system_health(self, health_checker):
        health = await health_checker.check_all()
        
        assert isinstance(health.healthy, bool)
        assert isinstance(health.components, list)
        assert health.version == HealthChecker.VERSION
        assert health.uptime_seconds >= 0
    
    def test_register_custom_checker(self, health_checker):
        async def custom_check():
            return ComponentHealth(
                name="custom",
                status=HealthStatus.HEALTHY,
                healthy=True,
            )
        
        health_checker.register_checker("custom", custom_check)
        
        assert "custom" in health_checker._checkers


class TestComponentHealth:
    """Tests for component health model."""
    
    def test_healthy_component(self):
        health = ComponentHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            healthy=True,
            latency_ms=1.5,
        )
        
        assert health.healthy is True
        assert health.status == HealthStatus.HEALTHY
    
    def test_unhealthy_component(self):
        health = ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            healthy=False,
            message="Connection refused",
        )
        
        assert health.healthy is False
        assert health.message == "Connection refused"
    
    def test_to_dict(self):
        health = ComponentHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            healthy=True,
            latency_ms=1.5,
            details={"version": "7.0"},
        )
        
        data = health.to_dict()
        
        assert data['name'] == "redis"
        assert data['status'] == "healthy"
        assert data['latency_ms'] == 1.5
        assert data['details']['version'] == "7.0"


class TestConfig:
    """Tests for configuration classes."""
    
    def test_redis_config_defaults(self):
        config = RedisConfig()
        
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
    
    def test_redis_config_url(self):
        config = RedisConfig(host="redis.example.com", port=6380)
        assert "redis.example.com" in config.url
        assert "6380" in config.url
    
    def test_postgres_config_defaults(self):
        config = PostgresConfig()
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "agentxploitor"
    
    def test_circuit_breaker_config_defaults(self):
        config = CircuitBreakerConfig()
        
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60.0


class TestQueuePriority:
    """Tests for queue priority enum."""
    
    def test_priority_ordering(self):
        assert QueuePriority.CRITICAL > QueuePriority.HIGH
        assert QueuePriority.HIGH > QueuePriority.NORMAL
        assert QueuePriority.NORMAL > QueuePriority.LOW
    
    def test_priority_values(self):
        assert QueuePriority.CRITICAL.value == 20
        assert QueuePriority.HIGH.value == 10
        assert QueuePriority.NORMAL.value == 5
        assert QueuePriority.LOW.value == 1


class TestEventType:
    """Tests for event type enum."""
    
    def test_event_types_defined(self):
        assert EventType.JOB_CREATED.value == "job_created"
        assert EventType.JOB_STATE_CHANGED.value == "job_state_changed"
        assert EventType.PAYMENT_VERIFIED.value == "payment_verified"
        assert EventType.SCAN_STARTED.value == "scan_started"
        assert EventType.FINDING_DISCOVERED.value == "finding_discovered"
        assert EventType.JOB_COMPLETED.value == "job_completed"
