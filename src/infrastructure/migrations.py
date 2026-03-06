"""
Database Migrations

Simple migration runner for PostgreSQL schema management.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from infrastructure.database import DatabasePool, get_db_pool

logger = logging.getLogger(__name__)


class MigrationRunner:
    """
    Simple migration runner for PostgreSQL.
    
    Migrations are SQL files in the migrations/ directory.
    They are applied in order based on filename prefix.
    """
    
    def __init__(
        self,
        db: Optional[DatabasePool] = None,
        migrations_dir: Optional[Path] = None,
    ):
        self._db = db
        self._migrations_dir = migrations_dir or Path(__file__).parent.parent / "migrations"
    
    @property
    def db(self) -> DatabasePool:
        if self._db is None:
            self._db = get_db_pool()
        return self._db
    
    def list_migrations(self) -> List[Tuple[str, Path]]:
        """List available migration files in order."""
        migrations = []
        
        if not self._migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self._migrations_dir}")
            return migrations
        
        for file in sorted(self._migrations_dir.glob("*.sql")):
            version = file.stem
            migrations.append((version, file))
        
        return migrations
    
    async def get_applied_versions(self) -> List[str]:
        """Get list of applied migration versions."""
        try:
            rows = await self.db.fetch(
                "SELECT version FROM schema_migrations ORDER BY version"
            )
            return [row['version'] for row in rows]
        except Exception:
            return []
    
    async def get_pending_migrations(self) -> List[Tuple[str, Path]]:
        """Get migrations that haven't been applied yet."""
        all_migrations = self.list_migrations()
        applied = await self.get_applied_versions()
        
        return [
            (version, path)
            for version, path in all_migrations
            if version not in applied
        ]
    
    async def apply_migration(self, version: str, path: Path) -> bool:
        """Apply a single migration."""
        logger.info(f"Applying migration: {version}")
        
        try:
            sql = path.read_text()
            
            async with self.db.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(sql)
            
            logger.info(f"Migration applied successfully: {version}")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed {version}: {e}")
            return False
    
    async def migrate(self, target: Optional[str] = None) -> Tuple[int, int]:
        """
        Apply all pending migrations up to target version.
        
        Returns (applied_count, failed_count).
        """
        pending = await self.get_pending_migrations()
        
        if target:
            pending = [
                (v, p) for v, p in pending
                if v <= target
            ]
        
        if not pending:
            logger.info("No pending migrations")
            return (0, 0)
        
        logger.info(f"Found {len(pending)} pending migrations")
        
        applied = 0
        failed = 0
        
        for version, path in pending:
            success = await self.apply_migration(version, path)
            if success:
                applied += 1
            else:
                failed += 1
                break  # Stop on first failure
        
        return (applied, failed)
    
    async def rollback(self, version: str) -> bool:
        """
        Rollback a specific migration (if down migration exists).
        
        Note: This requires a corresponding .down.sql file.
        """
        down_path = self._migrations_dir / f"{version}.down.sql"
        
        if not down_path.exists():
            logger.error(f"No rollback file found for migration {version}")
            return False
        
        try:
            sql = down_path.read_text()
            
            async with self.db.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(sql)
                    await conn.execute(
                        "DELETE FROM schema_migrations WHERE version = $1",
                        version
                    )
            
            logger.info(f"Rollback successful: {version}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed {version}: {e}")
            return False
    
    async def status(self) -> dict:
        """Get migration status."""
        all_migrations = self.list_migrations()
        applied = await self.get_applied_versions()
        pending = await self.get_pending_migrations()
        
        return {
            'total_migrations': len(all_migrations),
            'applied': len(applied),
            'pending': len(pending),
            'applied_versions': applied,
            'pending_versions': [v for v, _ in pending],
            'current_version': applied[-1] if applied else None,
        }


async def run_migrations(target: Optional[str] = None) -> Tuple[int, int]:
    """Run all pending migrations."""
    runner = MigrationRunner()
    return await runner.migrate(target)


async def check_migrations() -> dict:
    """Check migration status."""
    runner = MigrationRunner()
    return await runner.status()
