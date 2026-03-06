"""
PostgreSQL Database Pool

Async PostgreSQL connection pool with health checks.
"""

import asyncio
import logging
from typing import Optional, Any, Dict, List, AsyncGenerator
from contextlib import asynccontextmanager

try:
    import asyncpg
    from asyncpg import Pool, Connection
    from asyncpg.exceptions import PostgresError
    POSTGRES_AVAILABLE = True
except ImportError:
    asyncpg = None
    Pool = None
    Connection = None
    PostgresError = Exception
    POSTGRES_AVAILABLE = False

from infrastructure.config import PostgresConfig

logger = logging.getLogger(__name__)


class DatabasePool:
    """
    Async PostgreSQL connection pool.
    
    Usage:
        db = DatabasePool(config)
        await db.connect()
        
        async with db.acquire() as conn:
            result = await conn.fetch("SELECT * FROM jobs")
        
        await db.disconnect()
    """
    
    def __init__(self, config: Optional[PostgresConfig] = None):
        self.config = config or PostgresConfig()
        self._pool: Optional[Any] = None
        self._connected = False
    
    @property
    def available(self) -> bool:
        """Check if asyncpg is available."""
        return POSTGRES_AVAILABLE
    
    @property
    def connected(self) -> bool:
        """Check if pool is connected."""
        return self._connected and self._pool is not None
    
    async def connect(self) -> None:
        """Initialize connection pool."""
        if not POSTGRES_AVAILABLE:
            raise RuntimeError("asyncpg not installed. Run: pip install asyncpg")
        
        if self._connected:
            return
        
        try:
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
            )
            
            async with self._pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            self._connected = True
            logger.info(f"PostgreSQL connected: {self.config.host}:{self.config.port}/{self.config.database}")
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self._connected = False
            raise
    
    async def disconnect(self) -> None:
        """Close all connections."""
        if self._pool:
            await self._pool.close()
        
        self._connected = False
        logger.info("PostgreSQL disconnected")
    
    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[Any, None]:
        """Acquire a connection from the pool."""
        if not self._connected or self._pool is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        async with self._pool.acquire() as conn:
            yield conn
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query and return status."""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a query and return rows as dicts."""
        async with self.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute a query and return first row as dict."""
        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetchval(self, query: str, *args) -> Any:
        """Execute a query and return first value."""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        if not self._connected or self._pool is None:
            return {
                'healthy': False,
                'error': 'Not connected',
            }
        
        try:
            start = asyncio.get_event_loop().time()
            
            async with self.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                result = await conn.fetchrow("""
                    SELECT 
                        count(*) as connections,
                        (SELECT count(*) FROM pg_stat_activity 
                         WHERE datname = $1) as active_connections
                    FROM pg_stat_activity
                    WHERE datname = $1
                """, self.config.database)
            
            latency = (asyncio.get_event_loop().time() - start) * 1000
            
            return {
                'healthy': True,
                'latency_ms': round(latency, 2),
                'version': version.split(',')[0] if version else 'unknown',
                'pool_size': self._pool.get_size() if self._pool else 0,
                'idle_connections': self._pool.get_idle_size() if self._pool else 0,
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
            }
    
    async def transaction(self):
        """Start a transaction."""
        if not self._connected or self._pool is None:
            raise RuntimeError("Database not connected")
        return self._pool.acquire()


_db_pool: Optional[DatabasePool] = None


def get_db_pool() -> DatabasePool:
    """Get global database pool instance."""
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabasePool()
    return _db_pool


async def init_database(config: Optional[PostgresConfig] = None) -> DatabasePool:
    """Initialize global database pool."""
    global _db_pool
    _db_pool = DatabasePool(config)
    await _db_pool.connect()
    return _db_pool


async def close_database() -> None:
    """Close global database pool."""
    global _db_pool
    if _db_pool:
        await _db_pool.disconnect()
        _db_pool = None
