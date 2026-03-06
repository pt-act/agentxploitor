"""
Health Check

System health monitoring for infrastructure components.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from enum import Enum

from infrastructure.redis_pool import get_redis_pool
from infrastructure.database import get_db_pool
from infrastructure.circuit_breaker import get_circuit_registry
from infrastructure.migrations import check_migrations

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status for a single component."""
    name: str
    status: HealthStatus
    healthy: bool
    message: Optional[str] = None
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    last_check: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status.value,
            'healthy': self.healthy,
            'message': self.message,
            'latency_ms': self.latency_ms,
            'details': self.details,
            'last_check': self.last_check,
        }


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: HealthStatus
    healthy: bool
    components: List[ComponentHealth]
    version: str
    uptime_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'healthy': self.healthy,
            'components': [c.to_dict() for c in self.components],
            'version': self.version,
            'uptime_seconds': round(self.uptime_seconds, 2),
            'timestamp': self.timestamp,
        }


class HealthChecker:
    """
    System health checker for all infrastructure components.
    
    Provides:
    - /health/live - Liveness probe (is the service running?)
    - /health/ready - Readiness probe (can the service handle requests?)
    - /health - Full health check with all components
    """
    
    VERSION = "2.0.0"
    START_TIME = datetime.utcnow()
    
    def __init__(self):
        self._checkers: Dict[str, Callable] = {}
        self._register_default_checkers()
    
    def _register_default_checkers(self) -> None:
        """Register default component health checkers."""
        self._checkers['redis'] = self._check_redis
        self._checkers['database'] = self._check_database
        self._checkers['migrations'] = self._check_migrations
        self._checkers['circuit_breakers'] = self._check_circuit_breakers
    
    def register_checker(self, name: str, checker: Callable) -> None:
        """Register a custom health checker."""
        self._checkers[name] = checker
    
    async def check_redis(self) -> ComponentHealth:
        """Check Redis connectivity."""
        return await self._check_redis()
    
    async def _check_redis(self) -> ComponentHealth:
        """Check Redis health."""
        try:
            pool = get_redis_pool()
            
            if not pool.available:
                return ComponentHealth(
                    name='redis',
                    status=HealthStatus.HEALTHY,
                    healthy=True,
                    message='Redis not configured (using in-memory fallback)',
                )
            
            if not pool.connected:
                return ComponentHealth(
                    name='redis',
                    status=HealthStatus.UNHEALTHY,
                    healthy=False,
                    message='Redis not connected',
                )
            
            health = await pool.health_check()
            
            if health.get('healthy'):
                return ComponentHealth(
                    name='redis',
                    status=HealthStatus.HEALTHY,
                    healthy=True,
                    latency_ms=health.get('latency_ms'),
                    details={
                        'version': health.get('version'),
                        'connected_clients': health.get('connected_clients'),
                        'used_memory': health.get('used_memory_human'),
                    },
                )
            else:
                return ComponentHealth(
                    name='redis',
                    status=HealthStatus.UNHEALTHY,
                    healthy=False,
                    message=health.get('error', 'Unknown error'),
                )
                
        except Exception as e:
            return ComponentHealth(
                name='redis',
                status=HealthStatus.UNHEALTHY,
                healthy=False,
                message=str(e),
            )
    
    async def _check_database(self) -> ComponentHealth:
        """Check PostgreSQL health."""
        try:
            pool = get_db_pool()
            
            if not pool.available:
                return ComponentHealth(
                    name='database',
                    status=HealthStatus.HEALTHY,
                    healthy=True,
                    message='PostgreSQL not configured (using in-memory fallback)',
                )
            
            if not pool.connected:
                return ComponentHealth(
                    name='database',
                    status=HealthStatus.UNHEALTHY,
                    healthy=False,
                    message='Database not connected',
                )
            
            health = await pool.health_check()
            
            if health.get('healthy'):
                return ComponentHealth(
                    name='database',
                    status=HealthStatus.HEALTHY,
                    healthy=True,
                    latency_ms=health.get('latency_ms'),
                    details={
                        'version': health.get('version'),
                        'pool_size': health.get('pool_size'),
                        'idle_connections': health.get('idle_connections'),
                    },
                )
            else:
                return ComponentHealth(
                    name='database',
                    status=HealthStatus.UNHEALTHY,
                    healthy=False,
                    message=health.get('error', 'Unknown error'),
                )
                
        except Exception as e:
            return ComponentHealth(
                name='database',
                status=HealthStatus.UNHEALTHY,
                healthy=False,
                message=str(e),
            )
    
    async def _check_migrations(self) -> ComponentHealth:
        """Check database migrations status."""
        try:
            status = await check_migrations()
            
            pending = status.get('pending', 0)
            
            if pending == 0:
                return ComponentHealth(
                    name='migrations',
                    status=HealthStatus.HEALTHY,
                    healthy=True,
                    details={
                        'current_version': status.get('current_version'),
                        'applied': status.get('applied'),
                    },
                )
            else:
                return ComponentHealth(
                    name='migrations',
                    status=HealthStatus.DEGRADED,
                    healthy=True,
                    message=f'{pending} pending migrations',
                    details=status,
                )
                
        except Exception as e:
            return ComponentHealth(
                name='migrations',
                status=HealthStatus.DEGRADED,
                healthy=True,
                message=f'Could not check migrations: {e}',
            )
    
    async def _check_circuit_breakers(self) -> ComponentHealth:
        """Check circuit breaker states."""
        try:
            registry = get_circuit_registry()
            circuits = registry.to_dict()
            
            open_circuits = [
                name for name, data in circuits.items()
                if data['state'] == 'open'
            ]
            
            half_open_circuits = [
                name for name, data in circuits.items()
                if data['state'] == 'half_open'
            ]
            
            if open_circuits:
                return ComponentHealth(
                    name='circuit_breakers',
                    status=HealthStatus.DEGRADED,
                    healthy=True,
                    message=f'Open circuits: {", ".join(open_circuits)}',
                    details={
                        'total': len(circuits),
                        'open': open_circuits,
                        'half_open': half_open_circuits,
                    },
                )
            
            return ComponentHealth(
                name='circuit_breakers',
                status=HealthStatus.HEALTHY,
                healthy=True,
                details={
                    'total': len(circuits),
                    'half_open': half_open_circuits,
                },
            )
            
        except Exception as e:
            return ComponentHealth(
                name='circuit_breakers',
                status=HealthStatus.HEALTHY,
                healthy=True,
                message=f'Could not check circuit breakers: {e}',
            )
    
    async def check_all(self) -> SystemHealth:
        """Run all health checks."""
        components = []
        
        for name, checker in self._checkers.items():
            try:
                if asyncio.iscoroutinefunction(checker):
                    component = await checker()
                else:
                    component = checker()
                components.append(component)
            except Exception as e:
                components.append(ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    healthy=False,
                    message=str(e),
                ))
        
        all_healthy = all(c.healthy for c in components)
        any_degraded = any(c.status == HealthStatus.DEGRADED for c in components)
        
        if all_healthy and not any_degraded:
            status = HealthStatus.HEALTHY
        elif all_healthy:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY
        
        uptime = (datetime.utcnow() - self.START_TIME).total_seconds()
        
        return SystemHealth(
            status=status,
            healthy=all_healthy,
            components=components,
            version=self.VERSION,
            uptime_seconds=uptime,
        )
    
    async def check_live(self) -> bool:
        """Liveness probe - is the service running?"""
        return True
    
    async def check_ready(self) -> bool:
        """Readiness probe - can the service handle requests?"""
        health = await self.check_all()
        return health.healthy
    
    async def get_live_response(self) -> Dict[str, Any]:
        """Get liveness probe response."""
        return {
            'alive': True,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    async def get_ready_response(self) -> Dict[str, Any]:
        """Get readiness probe response."""
        ready = await self.check_ready()
        return {
            'ready': ready,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    async def get_health_response(self) -> Dict[str, Any]:
        """Get full health check response."""
        health = await self.check_all()
        return health.to_dict()


_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
