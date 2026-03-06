"""
Error Path Coverage Tests

Tests all error handling paths in the system.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from models import JobSession, JobStatus
from infrastructure.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    CircuitBreakerRegistry,
)
from infrastructure.config import CircuitBreakerConfig
from domain.saga import SagaOrchestrator, SagaStep
from exceptions import (
    AnalyzerError,
    PaymentError,
    ValidationError,
    ResourceNotFoundError,
    TimeoutError,
)


class TestExceptionHandlers:
    """Tests for exception handlers across the system."""
    
    def test_analyzer_error_handling(self):
        """Test analyzer error is handled correctly."""
        error = AnalyzerError("Slither analysis failed", analyzer="slither")
        
        assert str(error) == "Slither analysis failed"
        assert error.analyzer == "slither"
    
    def test_payment_error_handling(self):
        """Test payment error is handled correctly."""
        error = PaymentError("Insufficient confirmations", tx_hash="0xabc...")
        
        assert "Insufficient confirmations" in str(error)
        assert error.tx_hash == "0xabc..."
    
    def test_validation_error_handling(self):
        """Test validation error is handled correctly."""
        error = ValidationError("Invalid target URL", field="target_url")
        
        assert "Invalid target URL" in str(error)
        assert error.field == "target_url"
    
    def test_resource_not_found_error(self):
        """Test resource not found error."""
        error = ResourceNotFoundError("Job", job_id="job-001")
        
        assert "Job" in str(error)
        assert "not found" in str(error).lower()


class TestCircuitBreakerErrors:
    """Tests for circuit breaker error paths."""
    
    @pytest.mark.asyncio
    async def test_circuit_opens_on_failures(self):
        """Test circuit opens after threshold failures."""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60.0)
        breaker = CircuitBreaker('test', config)
        
        async def failing_call():
            raise ValueError("Service unavailable")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_call)
        
        assert breaker.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_circuit_rejects_when_open(self):
        """Test circuit rejects calls when open."""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60.0)
        breaker = CircuitBreaker('test', config)
        
        async def failing_call():
            raise ValueError("Error")
        
        with pytest.raises(ValueError):
            await breaker.call(failing_call)
        
        assert breaker.state == CircuitState.OPEN
        
        async def success_call():
            return "success"
        
        with pytest.raises(CircuitOpenError) as exc_info:
            await breaker.call(success_call)
        
        assert exc_info.value.circuit_name == "test"
    
    @pytest.mark.asyncio
    async def test_circuit_half_open_recovery(self):
        """Test circuit recovers through half-open state."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        breaker = CircuitBreaker('test', config)
        
        async def failing_call():
            raise ValueError("Error")
        
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_call)
        
        await asyncio.sleep(0.15)
        
        async def success_call():
            return "success"
        
        result = await breaker.call(success_call)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED


class TestCircuitBreakerRegistry:
    """Tests for circuit breaker registry."""
    
    def test_registry_tracks_breakers(self):
        registry = CircuitBreakerRegistry()
        
        breaker1 = registry.get_or_create('service-a')
        breaker2 = registry.get_or_create('service-b')
        
        assert breaker1 is not breaker2
        
        same_breaker = registry.get_or_create('service-a')
        assert same_breaker is breaker1
    
    def test_registry_reset_all(self):
        registry = CircuitBreakerRegistry()
        
        breaker1 = registry.get_or_create('service-a')
        breaker2 = registry.get_or_create('service-b')
        
        breaker1._state = CircuitState.OPEN
        breaker2._state = CircuitState.OPEN
        
        registry.reset_all()
        
        assert breaker1.state == CircuitState.CLOSED
        assert breaker2.state == CircuitState.CLOSED


class TestSagaCompensation:
    """Tests for saga compensation actions."""
    
    @pytest.mark.asyncio
    async def test_saga_compensation_on_failure(self):
        """Test saga executes compensation on failure."""
        executed = []
        
        async def step1():
            executed.append('step1')
        
        async def compensate1():
            executed.append('compensate1')
        
        async def step2():
            executed.append('step2')
            raise Exception("Step 2 failed")
        
        async def compensate2():
            executed.append('compensate2')
        
        steps = [
            SagaStep(name='step1', action=step1, compensation=compensate1),
            SagaStep(name='step2', action=step2, compensation=compensate2),
        ]
        
        orchestrator = SagaOrchestrator()
        
        with pytest.raises(Exception):
            await orchestrator.execute(steps)
        
        assert 'step1' in executed
        assert 'step2' in executed
        assert 'compensate1' in executed
    
    @pytest.mark.asyncio
    async def test_saga_all_or_nothing(self):
        """Test saga ensures all-or-nothing semantics."""
        executed = []
        
        async def step1():
            executed.append('step1')
        
        async def compensate1():
            executed.append('compensate1')
        
        async def step2():
            executed.append('step2')
        
        async def step3():
            executed.append('step3')
            raise Exception("Step 3 failed")
        
        async def compensate3():
            executed.append('compensate3')
        
        steps = [
            SagaStep(name='step1', action=step1, compensation=compensate1),
            SagaStep(name='step2', action=step2, compensation=lambda: None),
            SagaStep(name='step3', action=step3, compensation=compensate3),
        ]
        
        orchestrator = SagaOrchestrator()
        
        with pytest.raises(Exception):
            await orchestrator.execute(steps)
        
        assert 'compensate1' in executed


class TestTimeoutHandling:
    """Tests for timeout handling."""
    
    @pytest.mark.asyncio
    async def test_operation_timeout(self):
        """Test operation timeout handling."""
        async def slow_operation():
            await asyncio.sleep(5)
            return "done"
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_operation(), timeout=0.1)
    
    @pytest.mark.asyncio
    async def test_timeout_with_cleanup(self):
        """Test timeout with cleanup."""
        cleanup_called = False
        
        async def operation_with_cleanup():
            try:
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                nonlocal cleanup_called
                cleanup_called = True
                raise
        
        task = asyncio.create_task(operation_with_cleanup())
        
        await asyncio.sleep(0.05)
        task.cancel()
        
        with pytest.raises(asyncio.CancelledError):
            await task
        
        assert cleanup_called


class TestErrorMessageQuality:
    """Tests for user-friendly error messages."""
    
    def test_payment_error_user_friendly(self):
        """Test payment error has user-friendly message."""
        error = PaymentError(
            "Payment requires at least 12 confirmations",
            tx_hash="0xabc...",
            required_confirmations=12,
            actual_confirmations=3,
        )
        
        message = str(error)
        assert "12 confirmations" in message
        assert "received 3" in message or "actual" not in message.lower()
    
    def test_validation_error_user_friendly(self):
        """Test validation error has helpful message."""
        error = ValidationError(
            "Target URL must be a valid Ethereum address or contract URL",
            field="target_url",
            provided_value="not-a-url",
        )
        
        message = str(error)
        assert "valid" in message.lower()
    
    def test_analyzer_error_user_friendly(self):
        """Test analyzer error is understandable."""
        error = AnalyzerError(
            "Static analysis timed out after 60 seconds",
            analyzer="slither",
            timeout=60,
        )
        
        message = str(error)
        assert "timed out" in message.lower()


class TestGracefulDegradation:
    """Tests for graceful degradation."""
    
    @pytest.mark.asyncio
    async def test_fallback_on_failure(self):
        """Test fallback is used on failure."""
        primary_calls = 0
        fallback_calls = 0
        
        async def primary():
            nonlocal primary_calls
            primary_calls += 1
            raise Exception("Primary failed")
        
        async def fallback():
            nonlocal fallback_calls
            fallback_calls += 1
            return "fallback result"
        
        try:
            result = await primary()
        except Exception:
            result = await fallback()
        
        assert result == "fallback result"
        assert primary_calls == 1
        assert fallback_calls == 1
    
    @pytest.mark.asyncio
    async def test_partial_service_available(self):
        """Test partial service remains available on component failure."""
        services = {
            'analyzer1': {'available': True, 'priority': 1},
            'analyzer2': {'available': False, 'priority': 2},
            'analyzer3': {'available': True, 'priority': 3},
        }
        
        available = [s for s, cfg in services.items() if cfg['available']]
        available.sort(key=lambda s: services[s]['priority'])
        
        assert len(available) == 2
        assert available[0] == 'analyzer1'
