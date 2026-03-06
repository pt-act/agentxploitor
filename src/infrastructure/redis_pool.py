"""
Redis Connection Pool

Async Redis connection pool with health checks.
"""

import asyncio
from typing import Optional, Any, Dict
import logging

try:
    import redis.asyncio as aioredis
    from redis.asyncio.connection import ConnectionPool
    from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    ConnectionPool = None
    RedisError = Exception
    RedisConnectionError = Exception
    REDIS_AVAILABLE = False

from infrastructure.config import RedisConfig

logger = logging.getLogger(__name__)


class RedisPool:
    """
    Async Redis connection pool with automatic reconnection.
    
    Usage:
        pool = RedisPool(config)
        await pool.connect()
        
        async with pool.get() as conn:
            await conn.set('key', 'value')
        
        await pool.disconnect()
    """
    
    def __init__(self, config: Optional[RedisConfig] = None):
        self.config = config or RedisConfig()
        self._pool: Optional[Any] = None
        self._client: Optional[Any] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._connected = False
    
    @property
    def available(self) -> bool:
        """Check if Redis is available."""
        return REDIS_AVAILABLE
    
    @property
    def connected(self) -> bool:
        """Check if pool is connected."""
        return self._connected and self._pool is not None
    
    async def connect(self) -> None:
        """Initialize connection pool."""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis library not installed. Run: pip install redis[hiredis]")
        
        if self._connected:
            return
        
        try:
            self._pool = ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                decode_responses=True,
            )
            
            self._client = aioredis.Redis(connection_pool=self._pool)
            
            await self._client.ping()
            self._connected = True
            
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info(f"Redis connected: {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            raise
    
    async def disconnect(self) -> None:
        """Close all connections."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._client:
            await self._client.aclose()
        
        if self._pool:
            await self._pool.aclose()
        
        self._connected = False
        logger.info("Redis disconnected")
    
    def get_client(self) -> Any:
        """Get Redis client."""
        if not self._connected or self._client is None:
            raise RuntimeError("Redis pool not connected. Call connect() first.")
        return self._client
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        if not self._connected or self._client is None:
            return {
                'healthy': False,
                'error': 'Not connected',
            }
        
        try:
            start = asyncio.get_event_loop().time()
            await self._client.ping()
            latency = (asyncio.get_event_loop().time() - start) * 1000
            
            info = await self._client.info('server')
            
            return {
                'healthy': True,
                'latency_ms': round(latency, 2),
                'version': info.get('redis_version', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'unknown'),
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
            }
    
    async def _health_check_loop(self) -> None:
        """Periodic health check."""
        while self._connected:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                health = await self.health_check()
                if not health['healthy']:
                    logger.warning(f"Redis health check failed: {health.get('error')}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")


_redis_pool: Optional[RedisPool] = None


def get_redis_pool() -> RedisPool:
    """Get global Redis pool instance."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = RedisPool()
    return _redis_pool


async def init_redis(config: Optional[RedisConfig] = None) -> RedisPool:
    """Initialize global Redis pool."""
    global _redis_pool
    _redis_pool = RedisPool(config)
    await _redis_pool.connect()
    return _redis_pool


async def close_redis() -> None:
    """Close global Redis pool."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
