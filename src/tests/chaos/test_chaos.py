"""
Chaos Tests - Failure Injection and Resilience Testing

Tests system resilience under various failure scenarios.
"""

import pytest
import asyncio
import random
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class FailureType(str, Enum):
    """Types of failures to inject."""
    REDIS_CONNECTION = "redis_connection"
    POSTGRES_CONNECTION = "postgres_connection"
    ANALYZER_TIMEOUT = "analyzer_timeout"
    NETWORK_PARTITION = "network_partition"
    MEMORY_PRESSURE = "memory_pressure"
    DISK_FULL = "disk_full"
    RATE_LIMIT = "rate_limit"


@dataclass
class ChaosEvent:
    """A chaos event that was injected."""
    type: FailureType
    timestamp: str
    duration_ms: float
    recovered: bool
    impact: str


class ChaosMonkey:
    """
    Injects failures to test system resilience.
    
    Usage:
        monkey = ChaosMonkey()
        monkey.enable(FailureType.REDIS_CONNECTION)
        
        # System should handle Redis failure gracefully
        result = await system_operation()
        
        monkey.disable(FailureType.REDIS_CONNECTION)
    """
    
    def __init__(self, failure_probability: float = 0.3):
        self._enabled_failures: set = set()
        self._failure_probability = failure_probability
        self._events: List[ChaosEvent] = []
    
    def enable(self, failure_type: FailureType) -> None:
        """Enable a specific failure type."""
        self._enabled_failures.add(failure_type)
    
    def disable(self, failure_type: FailureType) -> None:
        """Disable a specific failure type."""
        self._enabled_failures.discard(failure_type)
    
    def disable_all(self) -> None:
        """Disable all failures."""
        self._enabled_failures.clear()
    
    def should_fail(self, failure_type: FailureType) -> bool:
        """Determine if a failure should occur."""
        return (
            failure_type in self._enabled_failures and
            random.random() < self._failure_probability
        )
    
    def record_event(
        self,
        type: FailureType,
        duration_ms: float,
        recovered: bool,
        impact: str,
    ) -> None:
        """Record a chaos event."""
        self._events.append(ChaosEvent(
            type=type,
            timestamp=datetime.utcnow().isoformat(),
            duration_ms=duration_ms,
            recovered=recovered,
            impact=impact,
        ))
    
    def get_events(self) -> List[ChaosEvent]:
        """Get all recorded events."""
        return self._events.copy()


class TestRedisFailure:
    """Tests for Redis failure scenarios."""
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure(self):
        """Test handling of Redis connection failure."""
        monkey = ChaosMonkey(failure_probability=1.0)
        monkey.enable(FailureType.REDIS_CONNECTION)
        
        class MockRedisQueue:
            def __init__(self, chaos: ChaosMonkey):
                self._chaos = chaos
            
            async def enqueue(self, job_id: str, **kwargs):
                if self._chaos.should_fail(FailureType.REDIS_CONNECTION):
                    raise ConnectionError("Redis connection refused")
                return True
            
            async def enqueue_with_fallback(self, job_id: str, **kwargs):
                try:
                    return await self.enqueue(job_id, **kwargs)
                except ConnectionError:
                    return await self._fallback_enqueue(job_id)
            
            async def _fallback_enqueue(self, job_id: str):
                return {'fallback': True, 'job_id': job_id}
        
        queue = MockRedisQueue(monkey)
        
        with pytest.raises(ConnectionError):
            await queue.enqueue('job-001')
        
        result = await queue.enqueue_with_fallback('job-001')
        assert result['fallback'] is True
    
    @pytest.mark.asyncio
    async def test_redis_reconnection(self):
        """Test Redis reconnection after failure."""
        connection_state = {'connected': False}
        reconnect_attempts = 0
        
        async def check_connection():
            if not connection_state['connected']:
                nonlocal reconnect_attempts
                reconnect_attempts += 1
                if reconnect_attempts >= 3:
                    connection_state['connected'] = True
                raise ConnectionError("Not connected")
            return True
        
        for _ in range(10):
            try:
                result = await check_connection()
                break
            except ConnectionError:
                await asyncio.sleep(0.01)
        
        assert connection_state['connected'] is True
        assert reconnect_attempts == 3


class TestPostgreSQLFailure:
    """Tests for PostgreSQL failure scenarios."""
    
    @pytest.mark.asyncio
    async def test_postgres_connection_failure(self):
        """Test handling of PostgreSQL connection failure."""
        class MockDatabase:
            def __init__(self):
                self.connected = False
            
            async def connect(self):
                if not self.connected:
                    raise ConnectionError("PostgreSQL connection refused")
            
            async def connect_with_retry(self, max_retries: int = 3):
                for attempt in range(max_retries):
                    try:
                        await self.connect()
                        return True
                    except ConnectionError:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(0.01)
                return False
        
        db = MockDatabase()
        
        with pytest.raises(ConnectionError):
            await db.connect()
        
        db.connected = True
        result = await db.connect_with_retry()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_postgres_query_timeout(self):
        """Test handling of query timeout."""
        class MockDatabase:
            async def slow_query(self):
                await asyncio.sleep(5)
                return "result"
            
            async def query_with_timeout(self, timeout: float = 1.0):
                try:
                    return await asyncio.wait_for(
                        self.slow_query(),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    return {'error': 'timeout', 'fallback': True}
        
        db = MockDatabase()
        result = await db.query_with_timeout(timeout=0.1)
        
        assert result['error'] == 'timeout'
        assert result['fallback'] is True


class TestAnalyzerTimeout:
    """Tests for analyzer timeout scenarios."""
    
    @pytest.mark.asyncio
    async def test_analyzer_timeout_handling(self):
        """Test handling of analyzer timeout."""
        async def slow_analyzer(contract: str):
            await asyncio.sleep(120)
            return {'findings': []}
        
        async def analyze_with_timeout(contract: str, timeout: float = 60.0):
            try:
                return await asyncio.wait_for(
                    slow_analyzer(contract),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                return {
                    'findings': [],
                    'error': 'timeout',
                    'partial_results': True,
                }
        
        result = await analyze_with_timeout('contract code', timeout=0.1)
        
        assert result['error'] == 'timeout'
        assert result['partial_results'] is True
    
    @pytest.mark.asyncio
    async def test_analyzer_crash_recovery(self):
        """Test recovery from analyzer crash."""
        class MockAnalyzer:
            def __init__(self):
                self.crashed = False
            
            async def analyze(self, contract: str):
                if self.crashed:
                    raise Exception("Analyzer crashed")
                return {'findings': ['finding1']}
            
            async def analyze_with_recovery(self, contract: str):
                try:
                    return await self.analyze(contract)
                except Exception as e:
                    self.crashed = False
                    await asyncio.sleep(0.1)
                    return await self.analyze(contract)
        
        analyzer = MockAnalyzer()
        analyzer.crashed = True
        
        result = await analyzer.analyze_with_recovery('contract')
        
        assert 'findings' in result


class TestNetworkPartition:
    """Tests for network partition scenarios."""
    
    @pytest.mark.asyncio
    async def test_network_partition_simulation(self):
        """Test handling of network partition."""
        class NetworkSimulator:
            def __init__(self):
                self.partitioned = False
            
            async def fetch(self, url: str):
                if self.partitioned:
                    raise ConnectionError("Network partition")
                return {'data': 'response'}
            
            async def fetch_with_circuit_breaker(self, url: str):
                from infrastructure.circuit_breaker import CircuitBreaker
                breaker = CircuitBreaker('network')
                
                async def _fetch():
                    return await self.fetch(url)
                
                try:
                    return await breaker.call(_fetch)
                except Exception:
                    return {'data': None, 'error': 'unavailable'}
        
        network = NetworkSimulator()
        network.partitioned = True
        
        with pytest.raises(ConnectionError):
            await network.fetch('https://api.example.com')
        
        result = await network.fetch_with_circuit_breaker('https://api.example.com')
        assert result['error'] == 'unavailable'


class TestGracefulDegradation:
    """Tests for graceful degradation under failure."""
    
    @pytest.mark.asyncio
    async def test_degraded_service_mode(self):
        """Test operation in degraded mode."""
        class Service:
            def __init__(self):
                self.features = {
                    'full_analysis': True,
                    'quick_scan': True,
                    'ai_suggestions': True,
                }
            
            def degrade(self, feature: str):
                self.features[feature] = False
            
            async def analyze(self, contract: str):
                if not self.features['full_analysis']:
                    return await self._quick_scan(contract)
                return await self._full_analysis(contract)
            
            async def _full_analysis(self, contract: str):
                return {
                    'findings': ['finding1', 'finding2'],
                    'ai_suggestions': self.features['ai_suggestions'],
                }
            
            async def _quick_scan(self, contract: str):
                return {
                    'findings': ['finding1'],
                    'ai_suggestions': False,
                    'degraded': True,
                }
        
        service = Service()
        
        full_result = await service.analyze('contract')
        assert full_result['ai_suggestions'] is True
        
        service.degrade('full_analysis')
        degraded_result = await service.analyze('contract')
        assert degraded_result['degraded'] is True
        assert degraded_result['ai_suggestions'] is False
    
    @pytest.mark.asyncio
    async def test_cascading_failure_prevention(self):
        """Test prevention of cascading failures."""
        class ServiceRegistry:
            def __init__(self):
                self.services = {
                    'primary': {'healthy': True},
                    'secondary': {'healthy': True},
                    'tertiary': {'healthy': True},
                }
            
            async def call(self, service_name: str):
                if not self.services[service_name]['healthy']:
                    raise Exception(f"{service_name} unhealthy")
                return f"{service_name} response"
            
            async def call_with_failover(self):
                for name in ['primary', 'secondary', 'tertiary']:
                    if self.services[name]['healthy']:
                        try:
                            return await self.call(name)
                        except Exception:
                            continue
                raise Exception("All services unavailable")
        
        registry = ServiceRegistry()
        registry.services['primary']['healthy'] = False
        registry.services['secondary']['healthy'] = False
        
        result = await registry.call_with_failover()
        assert 'tertiary' in result


class TestChaosScenarios:
    """Complex chaos scenarios combining multiple failures."""
    
    @pytest.mark.asyncio
    async def test_combined_failures(self):
        """Test handling of multiple simultaneous failures."""
        monkey = ChaosMonkey(failure_probability=0.5)
        monkey.enable(FailureType.REDIS_CONNECTION)
        monkey.enable(FailureType.ANALYZER_TIMEOUT)
        
        events = []
        
        async def resilient_operation():
            try:
                if monkey.should_fail(FailureType.REDIS_CONNECTION):
                    raise ConnectionError("Redis down")
                events.append('redis_ok')
            except ConnectionError:
                events.append('redis_fallback')
            
            try:
                if monkey.should_fail(FailureType.ANALYZER_TIMEOUT):
                    await asyncio.sleep(10)
                events.append('analyzer_ok')
            except asyncio.TimeoutError:
                events.append('analyzer_fallback')
        
        task = asyncio.create_task(resilient_operation())
        
        try:
            await asyncio.wait_for(task, timeout=0.1)
        except asyncio.TimeoutError:
            events.append('timeout_handled')
        
        assert len(events) > 0
    
    @pytest.mark.asyncio
    async def test_recovery_after_chaos(self):
        """Test system recovers after chaos is removed."""
        monkey = ChaosMonkey(failure_probability=1.0)
        monkey.enable(FailureType.REDIS_CONNECTION)
        
        class System:
            def __init__(self, chaos: ChaosMonkey):
                self._chaos = chaos
                self._healthy = True
            
            async def health_check(self):
                if self._chaos.should_fail(FailureType.REDIS_CONNECTION):
                    self._healthy = False
                    return False
                self._healthy = True
                return True
        
        system = System(monkey)
        
        result = await system.health_check()
        assert result is False
        
        monkey.disable(FailureType.REDIS_CONNECTION)
        
        result = await system.health_check()
        assert result is True


class TestFailureMetrics:
    """Tests for failure tracking and metrics."""
    
    @pytest.mark.asyncio
    async def test_failure_count_tracking(self):
        """Test that failures are tracked."""
        monkey = ChaosMonkey(failure_probability=1.0)
        monkey.enable(FailureType.REDIS_CONNECTION)
        
        failure_count = 0
        
        for _ in range(10):
            if monkey.should_fail(FailureType.REDIS_CONNECTION):
                failure_count += 1
                monkey.record_event(
                    type=FailureType.REDIS_CONNECTION,
                    duration_ms=10.0,
                    recovered=True,
                    impact='degraded',
                )
        
        assert failure_count == 10
        assert len(monkey.get_events()) == 10
    
    @pytest.mark.asyncio
    async def test_recovery_time_measurement(self):
        """Test that recovery time is measured."""
        events = []
        
        async def simulate_failure_and_recovery():
            start = asyncio.get_event_loop().time()
            events.append(('failure', start))
            
            await asyncio.sleep(0.05)
            
            end = asyncio.get_event_loop().time()
            events.append(('recovery', end))
            
            return (end - start) * 1000
        
        duration = await simulate_failure_and_recovery()
        
        assert duration >= 50
        assert len(events) == 2
