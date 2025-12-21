import sqlite3
import time
import hashlib
from typing import List, Dict, Optional, Callable, Any
from pathlib import Path
from contextlib import contextmanager
import logging
from core.config import settings

log = logging.getLogger(__name__)

class Migration:
    """Base migration class"""

    def __init__(self, version: str, description: str,
                 upgrade_sql: Optional[str] = None,
                 downgrade_sql: Optional[str] = None,
                 upgrade_func: Optional[Callable] = None,
                 downgrade_func: Optional[Callable] = None):
        self.version = version
        self.description = description
        self.upgrade_sql = upgrade_sql
        self.downgrade_sql = downgrade_sql
        self.upgrade_func = upgrade_func
        self.downgrade_func = downgrade_func
        self.created_at = int(time.time())

    def upgrade(self, conn: sqlite3.Connection) -> None:
        """Execute upgrade migration"""
        log.info(f"Executing migration {self.version}: {self.description}")

        if self.upgrade_func:
            self.upgrade_func(conn)
        elif self.upgrade_sql:
            try:
                cursor = conn.cursor()
                cursor.executescript(self.upgrade_sql)
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise Exception(f"Migration {self.version} failed: {e}")
        else:
            raise Exception(f"Migration {self.version} has no upgrade defined")

    def downgrade(self, conn: sqlite3.Connection) -> None:
        """Execute downgrade migration"""
        log.info(f"Rolling back migration {self.version}: {self.description}")

        if self.downgrade_func:
            self.downgrade_func(conn)
        elif self.downgrade_sql:
            try:
                cursor = conn.cursor()
                cursor.executescript(self.downgrade_sql)
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise Exception(f"Rollback of {self.version} failed: {e}")
        else:
            raise Exception(f"Migration {self.version} has no downgrade defined")

    def __repr__(self):
        return f"Migration({self.version}: {self.description})"

class MigrationManager:
    """Database migration manager with version tracking and rollback"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.DATABASE_URL.replace("sqlite:///", ""))
        self.migrations_table = "schema_migrations"
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Create migrations tracking table if it doesn't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                    version TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    execution_time_ms INTEGER
                )
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT version FROM {self.migrations_table} ORDER BY version")
            return [row[0] for row in cursor.fetchall()]

    def get_migration_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific migration"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM {self.migrations_table}
                WHERE version = ?
            """, (version,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def record_migration(self, migration: Migration, execution_time_ms: int):
        """Record that a migration has been applied"""
        checksum = self._get_migration_checksum(migration)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {self.migrations_table}
                (version, description, applied_at, checksum, execution_time_ms)
                VALUES (?, ?, ?, ?, ?)
            """, (
                migration.version,
                migration.description,
                int(time.time()),
                checksum,
                execution_time_ms
            ))
            conn.commit()

    def remove_migration_record(self, version: str):
        """Remove migration record (used for rollbacks)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.migrations_table} WHERE version = ?", (version,))
            conn.commit()

    def _get_migration_checksum(self, migration: Migration) -> str:
        """Generate checksum for migration integrity checking"""
        content = f"{migration.version}:{migration.description}"
        if migration.upgrade_sql:
            content += migration.upgrade_sql
        if migration.downgrade_sql:
            content += migration.downgrade_sql

        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _verify_migration_integrity(self, migration: Migration) -> bool:
        """Verify that migration hasn't been modified since application"""
        applied_info = self.get_migration_info(migration.version)
        if not applied_info:
            return True  # Not applied yet

        current_checksum = self._get_migration_checksum(migration)
        return applied_info['checksum'] == current_checksum

    def run_migrations(self, migrations: List[Migration],
                       target_version: Optional[str] = None,
                       dry_run: bool = False) -> Dict[str, Any]:
        """Run pending migrations up to target version"""
        applied_versions = set(self.get_applied_migrations())
        migration_map = {m.version: m for m in migrations}

        # Sort migrations by version
        pending_migrations = []
        for migration in migrations:
            if migration.version not in applied_versions:
                if target_version is None or migration.version <= target_version:
                    pending_migrations.append(migration)

        pending_migrations.sort(key=lambda m: m.version)

        if not pending_migrations:
            return {
                'status': 'up_to_date',
                'migrations_applied': 0,
                'execution_time_ms': 0,
                'message': 'No pending migrations'
            }

        if dry_run:
            return {
                'status': 'dry_run',
                'migrations_applied': len(pending_migrations),
                'execution_time_ms': 0,
                'pending_migrations': [m.version for m in pending_migrations],
                'message': f'Would apply {len(pending_migrations)} migrations'
            }

        # Execute migrations
        total_time = 0
        applied_count = 0

        for migration in pending_migrations:
            if not self._verify_migration_integrity(migration):
                raise Exception(f"Migration {migration.version} integrity check failed")

            start_time = time.time()

            try:
                migration.upgrade(self._get_connection().__enter__())
                execution_time = int((time.time() - start_time) * 1000)
                self.record_migration(migration, execution_time)

                total_time += execution_time
                applied_count += 1

                log.info(f"Migration {migration.version} applied successfully ({execution_time}ms)")

            except Exception as e:
                log.error(f"Migration {migration.version} failed: {e}")
                raise Exception(f"Migration failed at version {migration.version}: {e}")

        return {
            'status': 'success',
            'migrations_applied': applied_count,
            'execution_time_ms': total_time,
            'applied_migrations': [m.version for m in pending_migrations],
            'message': f'Applied {applied_count} migrations successfully'
        }

    def rollback_to_version(self, migrations: List[Migration],
                          target_version: str,
                          dry_run: bool = False) -> Dict[str, Any]:
        """Rollback migrations to target version"""
        applied_versions = set(self.get_applied_migrations())
        migration_map = {m.version: m for m in migrations}

        # Get migrations to rollback (newer than target version)
        rollback_migrations = []
        for version in sorted(applied_versions, reverse=True):
            if version > target_version and version in migration_map:
                rollback_migrations.append(migration_map[version])

        if not rollback_migrations:
            return {
                'status': 'nothing_to_rollback',
                'migrations_rolled_back': 0,
                'execution_time_ms': 0,
                'message': f'Already at or before version {target_version}'
            }

        if dry_run:
            return {
                'status': 'dry_run',
                'migrations_rolled_back': len(rollback_migrations),
                'execution_time_ms': 0,
                'rollback_migrations': [m.version for m in rollback_migrations],
                'message': f'Would rollback {len(rollback_migrations)} migrations to {target_version}'
            }

        # Execute rollbacks
        total_time = 0
        rolled_back_count = 0

        for migration in rollback_migrations:
            start_time = time.time()

            try:
                migration.downgrade(self._get_connection().__enter__())
                execution_time = int((time.time() - start_time) * 1000)
                self.remove_migration_record(migration.version)

                total_time += execution_time
                rolled_back_count += 1

                log.info(f"Migration {migration.version} rolled back successfully ({execution_time}ms)")

            except Exception as e:
                log.error(f"Rollback of {migration.version} failed: {e}")
                raise Exception(f"Rollback failed at version {migration.version}: {e}")

        return {
            'status': 'success',
            'migrations_rolled_back': rolled_back_count,
            'execution_time_ms': total_time,
            'rolled_back_migrations': [m.version for m in rollback_migrations],
            'message': f'Rolled back {rolled_back_count} migrations to {target_version}'
        }

    def get_migration_status(self, migrations: List[Migration]) -> Dict[str, Any]:
        """Get current migration status"""
        applied_versions = set(self.get_applied_migrations())
        migration_map = {m.version: m for m in migrations}

        current_version = max(applied_versions) if applied_versions else '0'

        pending = []
        applied = []

        for migration in migrations:
            if migration.version in applied_versions:
                info = self.get_migration_info(migration.version)
                applied.append({
                    'version': migration.version,
                    'description': migration.description,
                    'applied_at': info['applied_at'] if info else None,
                    'execution_time_ms': info['execution_time_ms'] if info else None
                })
            else:
                pending.append({
                    'version': migration.version,
                    'description': migration.description
                })

        return {
            'current_version': current_version,
            'pending_count': len(pending),
            'applied_count': len(applied),
            'pending_migrations': pending,
            'applied_migrations': applied,
            'needs_migration': len(pending) > 0
        }

    def reset_migrations(self):
        """Reset all migration records (for development)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.migrations_table}")
            conn.commit()

    def validate_migrations(self, migrations: List[Migration]) -> Dict[str, Any]:
        """Validate all migrations for integrity and correctness"""
        issues = []
        warnings = []

        for migration in migrations:
            # Check version format
            if not migration.version.replace('.', '').isdigit():
                issues.append(f"Migration {migration.version}: Invalid version format")

            # Check for required upgrade
            if not migration.upgrade_sql and not migration.upgrade_func:
                issues.append(f"Migration {migration.version}: No upgrade defined")

            # Check description
            if not migration.description or len(migration.description.strip()) == 0:
                issues.append(f"Migration {migration.version}: No description provided")

            # Check if migration needs integrity verification
            applied_info = self.get_migration_info(migration.version)
            if applied_info:
                if not self._verify_migration_integrity(migration):
                    issues.append(f"Migration {migration.version}: Migration has been modified since application")

        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'total_migrations': len(migrations)
        }

    def export_migrations(self, output_file: str):
        """Export current database schema as migration"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get table schemas
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            schemas = cursor.fetchall()

            # Generate migration
            current_time = int(time.time())
            migration_content = f"""# Auto-generated schema migration
# Generated on: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}
# Current schema tables: {[row[0] for row in schemas]}

class AutoSchemaMigration(Migration):
    version = "auto.{current_time}"
    description = "Auto-generated schema export"

    upgrade_sql = '''
-- Create tables
{'\\n\\n'.join(row[0] + ';' if not row[0].strip().endswith(';') else row[0] for row in schemas)}
    '''

    def upgrade(self, conn):
        conn.execute(self.upgrade_sql)

MIGRATIONS.append(AutoSchemaMigration())
"""

            # Write to file
            with open(output_file, 'w') as f:
                f.write(migration_content)

            return {
                'status': 'success',
                'output_file': output_file,
                'tables_exported': len(schemas)
            }