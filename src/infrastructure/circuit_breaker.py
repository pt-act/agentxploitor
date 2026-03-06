"""
Circuit Breaker Pattern

Implements circuit breaker for external service calls with automatic recovery.
"""

import asyncio
import functools
import logging
import time
from enum import Enum
from typing import Optional, Callable, Any, Dict, TypeVar, ParamSpec
from dataclasses import dataclass, field
from datetime import datetime

from infrastructure.config import CircuitBreakerConfig

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"      # Failing, requests are blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitStats:
    """Circuit breaker statistics."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    timeout_calls: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    last_state_change: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class CircuitBreaker:
    """
    Circuit breaker for external service calls.
    
    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Service failing, all requests rejected immediately
    - HALF_OPEN: Testing recovery, limited requests allowed
    
    Usage:
        breaker = CircuitBreaker("my-service", config)
        
        @breaker.protect
        async def call_external_service():
            return await external_api.call()
        
        # Or manual:
        try:
            async with breaker:
                result = await external_api.call()
        except CircuitOpenError:
            # Handle gracefully
            pass
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._lock = asyncio.Lock()
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._on_state_change = on_state_change
    
    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state
    
    @property
    def stats(self) -> CircuitStats:
        """Circuit statistics."""
        return self._stats
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking)."""
        return self._state == CircuitState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing)."""
        return self._state == CircuitState.HALF_OPEN
    
    async def __aenter__(self) -> 'CircuitBreaker':
        """Enter context manager."""
        await self._check_state()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context manager."""
        if exc_type is not None:
            await self._record_failure(exc_val)
        else:
            await self._record_success()
        return False  # Don't suppress exceptions
    
    def protect(self, func: Callable[P, T]) -> Callable[P, T]:
        """Decorator to protect a function with circuit breaker."""
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            async with self:
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if self.is_open:
                raise CircuitOpenError(
                    f"Circuit breaker '{self.name}' is open",
                    circuit_name=self.name,
                    stats=self._stats,
                )
            try:
                result = func(*args, **kwargs)
                self._record_success_sync()
                return result
            except Exception as e:
                self._record_failure_sync(e)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    async def call(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        """Execute function through circuit breaker."""
        async with self:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
    
    async def _check_state(self) -> None:
        """Check and potentially transition state."""
        async with self._lock:
            if self._state == CircuitState.OPEN:
                elapsed = time.time() - (self._last_failure_time or 0)
                
                if elapsed >= self.config.recovery_timeout:
                    await self._transition_to(CircuitState.HALF_OPEN)
                    logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN")
                else:
                    self._stats.rejected_calls += 1
                    raise CircuitOpenError(
                        f"Circuit breaker '{self.name}' is open",
                        circuit_name=self.name,
                        stats=self._stats,
                        retry_after=self.config.recovery_timeout - elapsed,
                    )
            
            elif self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._stats.rejected_calls += 1
                    raise CircuitOpenError(
                        f"Circuit breaker '{self.name}' is half-open with max calls reached",
                        circuit_name=self.name,
                        stats=self._stats,
                    )
                self._half_open_calls += 1
    
    async def _record_success(self) -> None:
        """Record successful call."""
        async with self._lock:
            self._stats.total_calls += 1
            self._stats.successful_calls += 1
            self._stats.last_success_time = time.time()
            self._stats.consecutive_failures = 0
            self._stats.consecutive_successes += 1
            
            if self._state == CircuitState.HALF_OPEN:
                if self._stats.consecutive_successes >= self.config.success_threshold:
                    await self._transition_to(CircuitState.CLOSED)
                    logger.info(f"Circuit '{self.name}' recovered, transitioning to CLOSED")
    
    def _record_success_sync(self) -> None:
        """Record successful call (sync version)."""
        self._stats.total_calls += 1
        self._stats.successful_calls += 1
        self._stats.last_success_time = time.time()
        self._stats.consecutive_failures = 0
        self._stats.consecutive_successes += 1
        
        if self._state == CircuitState.HALF_OPEN:
            if self._stats.consecutive_successes >= self.config.success_threshold:
                self._transition_to_sync(CircuitState.CLOSED)
    
    async def _record_failure(self, error: Exception) -> None:
        """Record failed call."""
        async with self._lock:
            self._stats.total_calls += 1
            self._stats.failed_calls += 1
            self._stats.last_failure_time = time.time()
            self._stats.consecutive_successes = 0
            self._stats.consecutive_failures += 1
            self._last_failure_time = time.time()
            
            if isinstance(error, asyncio.TimeoutError):
                self._stats.timeout_calls += 1
            
            if self._state == CircuitState.HALF_OPEN:
                await self._transition_to(CircuitState.OPEN)
                logger.warning(f"Circuit '{self.name}' failed in half-open, back to OPEN")
            
            elif self._state == CircuitState.CLOSED:
                if self._stats.consecutive_failures >= self.config.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)
                    logger.warning(f"Circuit '{self.name}' failed threshold, opening")
    
    def _record_failure_sync(self, error: Exception) -> None:
        """Record failed call (sync version)."""
        self._stats.total_calls += 1
        self._stats.failed_calls += 1
        self._stats.last_failure_time = time.time()
        self._stats.consecutive_successes = 0
        self._stats.consecutive_failures += 1
        self._last_failure_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            self._transition_to_sync(CircuitState.OPEN)
        
        elif self._state == CircuitState.CLOSED:
            if self._stats.consecutive_failures >= self.config.failure_threshold:
                self._transition_to_sync(CircuitState.OPEN)
    
    async def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state."""
        old_state = self._state
        self._state = new_state
        self._stats.last_state_change = time.time()
        
        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._stats.consecutive_successes = 0
        
        if self._on_state_change:
            try:
                if asyncio.iscoroutinefunction(self._on_state_change):
                    await self._on_state_change(old_state, new_state)
                else:
                    self._on_state_change(old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
    
    def _transition_to_sync(self, new_state: CircuitState) -> None:
        """Transition to new state (sync version)."""
        old_state = self._state
        self._state = new_state
        self._stats.last_state_change = time.time()
        
        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._stats.consecutive_successes = 0
        
        if self._on_state_change:
            try:
                self._on_state_change(old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
    
    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._last_failure_time = None
        self._half_open_calls = 0
        logger.info(f"Circuit '{self.name}' reset to CLOSED")
    
    def to_dict(self) -> Dict[str, Any]:
        """Export circuit state for monitoring."""
        return {
            'name': self.name,
            'state': self._state.value,
            'stats': {
                'total_calls': self._stats.total_calls,
                'successful_calls': self._stats.successful_calls,
                'failed_calls': self._stats.failed_calls,
                'rejected_calls': self._stats.rejected_calls,
                'timeout_calls': self._stats.timeout_calls,
                'consecutive_failures': self._stats.consecutive_failures,
                'consecutive_successes': self._stats.consecutive_successes,
                'failure_rate': (
                    self._stats.failed_calls / self._stats.total_calls
                    if self._stats.total_calls > 0 else 0
                ),
            },
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'recovery_timeout': self.config.recovery_timeout,
                'half_open_max_calls': self.config.half_open_max_calls,
                'success_threshold': self.config.success_threshold,
            },
        }


class CircuitOpenError(Exception):
    """Raised when circuit is open."""
    
    def __init__(
        self,
        message: str,
        circuit_name: str,
        stats: CircuitStats,
        retry_after: Optional[float] = None,
    ):
        super().__init__(message)
        self.circuit_name = circuit_name
        self.stats = stats
        self.retry_after = retry_after


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self, default_config: Optional[CircuitBreakerConfig] = None):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._default_config = default_config or CircuitBreakerConfig()
    
    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """Get or create circuit breaker by name."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                config=config or self._default_config,
                on_state_change=lambda old, new: self._on_state_change(name, old, new),
            )
        return self._breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self._breakers.get(name)
    
    def all(self) -> Dict[str, CircuitBreaker]:
        """Get all circuit breakers."""
        return self._breakers.copy()
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()
    
    def _on_state_change(self, name: str, old_state: CircuitState, new_state: CircuitState) -> None:
        """Handle state changes."""
        logger.info(f"Circuit '{name}' state change: {old_state.value} -> {new_state.value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all circuits for monitoring."""
        return {
            name: breaker.to_dict()
            for name, breaker in self._breakers.items()
        }


_circuit_registry: Optional[CircuitBreakerRegistry] = None


def get_circuit_registry() -> CircuitBreakerRegistry:
    """Get global circuit breaker registry."""
    global _circuit_registry
    if _circuit_registry is None:
        _circuit_registry = CircuitBreakerRegistry()
    return _circuit_registry


def circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """Get or create circuit breaker by name."""
    return get_circuit_registry().get_or_create(name, config)
