"""
Database fixtures for testing.

Provides pre-configured database states, test data,
and utility functions for database testing scenarios.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Generator
from datetime import datetime

from models.entities import Job, JobState, Render, RenderStatus, RenderQuality, AssetsCache
from tests.conftest import TestDataFactory


@pytest.fixture
def empty_test_database() -> Generator[str, None]:
    """Fixture providing an empty test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        db_path = temp_file.name

        # Initialize empty database
        conn = sqlite3.connect(db_path)
        conn.close()

        yield db_path

        # Cleanup
        try:
            Path(db_path).unlink()
        except FileNotFoundError:
            pass


@pytest.fixture
def populated_test_database() -> Generator[str, None]:
    """Fixture providing a test database with sample data."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        db_path = temp_file.name

        # Initialize database with sample data
        conn = sqlite3.connect(db_path)

        # Create tables
        cursor = conn.cursor()

        # Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL,
                updated_at INTEGER
            )
        """)

        # Renders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS renders (
                job_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                hash TEXT NOT NULL,
                quality TEXT NOT NULL,
                url TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                PRIMARY KEY (job_id, item_id)
            )
        """)

        # Assets cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets_cache (
                hash TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                size INTEGER,
                content_type TEXT,
                expires_at INTEGER,
                access_count INTEGER DEFAULT 0,
                last_accessed INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)

        # Insert sample data
        sample_jobs = [
            ("job-001", "queued", 0, 1609459200, 1609459200),
            ("job-002", "processing", 25, 1609459260, 1609459260),
            ("job-003", "completed", 100, 1609459200, 1609459800),
            ("job-004", "error", 50, 1609459300, 1609459300),
            ("job-005", "cancelled", 0, 1609459400, 1609459400),
        ]

        cursor.executemany("""
            INSERT INTO jobs (job_id, state, progress, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, sample_jobs)

        sample_renders = [
            ("job-001", "render-001", "hash001", "low", None, "pending", 1609459200, 1609459200),
            ("job-002", "render-001", "hash002", "high", "http://example.com/render1.mp4", "completed", 1609459260, 1609459270),
            ("job-002", "render-002", "hash003", "medium", "http://example.com/render2.mp4", "processing", 1609459260, 1609459280),
            ("job-003", "render-001", "hash004", "high", "http://example.com/render3.mp4", "completed", 1609459200, 1609459900),
            ("job-003", "render-002", "hash005", "ultra", "http://example.com/render4.mp4", "completed", 1609459200, 1609459500),
        ]

        cursor.executemany("""
            INSERT INTO renders (job_id, item_id, hash, quality, url, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_renders)

        sample_assets = [
            ("hash001", "http://example.com/asset1.mp4", 1609459200, 1024000, "video/mp4", 1609542800),
            ("hash002", "http://example.com/asset2.mp4", 1609459200, 2048000, "video/mp4", 1609629200),
            ("hash003", "http://example.com/asset3.mp4", 1609459200, 5120000, "video/mp4", 1609542800),
        ]

        cursor.executemany("""
            INSERT INTO assets_cache (hash, url, created_at, size, content_type, expires_at, access_count, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_assets)

        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        try:
            Path(db_path).unlink()
        except FileNotFoundError:
            pass


@pytest.fixture
def performance_test_database() -> Generator[str, None]:
    """Fixture providing a large database for performance testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        db_path = temp_file.name

        # Initialize database with large dataset
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create optimized tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                state TEXT NOT NULL CHECK (state IN ('queued', 'processing', 'completed', 'error', 'cancelled')),
                progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
                created_at INTEGER NOT NULL,
                updated_at INTEGER,
                job_type TEXT DEFAULT 'quick_create',
                config_json TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                priority INTEGER DEFAULT 0
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(state)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(job_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority DESC)")

        # Insert large dataset
        batch_size = 1000
        jobs_data = []

        for i in range(batch_size):
            job_id = f"perf-job-{i:04d}"
            state = ["queued", "processing", "completed", "error"][i % 4]
            progress = (i % 101)
            created_at = 1609459200 + (i * 60)  # 1 minute apart
            updated_at = created_at + 300  # 5 minutes later

            jobs_data.append((
                job_id, state, progress, created_at, updated_at,
                "quick_create", f"{{\"test_data\": \"{job_id}\"}}",
                None if state != "error" else f"Test error for {job_id}",
                i % 5,  # retry count
                i % 10   # priority
            ))

        cursor.executemany("""
            INSERT INTO jobs (job_id, state, progress, created_at, updated_at,
                              job_type, config_json, error_message, retry_count, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, jobs_data)

        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        try:
            Path(db_path).unlink()
        except FileNotFoundError:
            pass


@pytest.fixture
def concurrent_test_database() -> Generator[str, None]:
    """Fixture providing database configured for concurrency testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        db_path = temp_file.name

        # Configure for WAL mode (better concurrency)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = 10000")
        cursor.execute("PRAGMA temp_store = MEMORY")
        cursor.execute("PRAGMA mmap_size = 268435456")

        # Create tables with proper constraints
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL,
                updated_at INTEGER,
                version INTEGER DEFAULT 1,
                UNIQUE(job_id, version)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                old_state TEXT,
                new_state TEXT NOT NULL,
                old_progress INTEGER,
                new_progress INTEGER,
                changed_at INTEGER DEFAULT (strftime('%s', 'now')),
                changed_by TEXT,
                reason TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(state)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_audit_job_id ON job_audit(job_id)")

        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        try:
            Path(db_path).unlink()
        except FileNotFoundError:
            pass


class DatabaseTestScenarios:
    """Pre-configured database test scenarios."""

    @staticmethod
    def create_stuck_jobs(db_path: str, count: int = 5):
        """Create jobs that appear to be stuck (processing for too long)."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        old_timestamp = int((datetime.now().timestamp()) - 3600)  # 1 hour ago

        stuck_jobs = []
        for i in range(count):
            job_id = f"stuck-job-{i:03d}"
            stuck_jobs.append((job_id, old_timestamp, old_timestamp))

        cursor.executemany("""
            UPDATE jobs SET state = 'processing', updated_at = ?
            WHERE job_id = ?
        """, [(timestamp, job_id) for timestamp, job_id in stuck_jobs])

        conn.commit()
        conn.close()

        return [job_id for job_id, _, _ in stuck_jobs]

    @staticmethod
    def create_expired_assets(db_path: str, count: int = 10):
        """Create expired assets for cache cleanup testing."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        expired_timestamp = int((datetime.now().timestamp()) - 86400)  # 24 hours ago

        expired_assets = []
        for i in range(count):
            hash_value = f"expired-hash-{i:03d}"
            expired_assets.append((hash_value, expired_timestamp))

        cursor.executemany("""
            INSERT OR REPLACE INTO assets_cache (hash, url, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        """, [
            (hash_val, f"http://example.com/expired-{i}.mp4", expired_timestamp - 86400, expired_timestamp)
            for i, hash_val in enumerate(expired_assets)
        ])

        conn.commit()
        conn.close()

        return len(expired_assets)

    @staticmethod
    def create_database_corruption(db_path: str):
        """Intentionally corrupt database for testing error handling."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table with valid data
        cursor.execute("""
            CREATE TABLE jobs (
                job_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                progress INTEGER DEFAULT 0
            )
        """)

        # Insert valid data
        cursor.execute("""
            INSERT INTO jobs (job_id, state, progress)
            VALUES ('valid-job', 'queued', 0)
        """)

        # Create corrupted data (invalid state)
        cursor.execute("""
            INSERT INTO jobs (job_id, state, progress)
            VALUES ('invalid-job', 'invalid_state', 0)
        """)

        conn.commit()
        conn.close()

    @staticmethod
    def populate_with_relationships(db_path: str, job_count: int = 100, renders_per_job: int = 5):
        """Populate database with jobs and their related renders."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables with foreign keys
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL,
                updated_at INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS renders (
                job_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                hash TEXT NOT NULL,
                quality TEXT NOT NULL,
                url TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                PRIMARY KEY (job_id, item_id),
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            )
        """)

        # Insert jobs
        base_timestamp = 1609459200
        jobs_data = []
        renders_data = []

        for i in range(job_count):
            job_id = f"rel-job-{i:04d}"
            state = ["queued", "processing", "completed"][i % 3]
            progress = (i % 101)
            created_at = base_timestamp + (i * 60)

            jobs_data.append((job_id, state, progress, created_at, created_at))

            # Create related renders
            for j in range(renders_per_job):
                item_id = f"render-{j:03d}"
                hash_val = f"hash-{i}-{j}"
                quality = ["low", "medium", "high", "ultra"][j % 4]
                status = "pending" if j % 2 == 0 else "completed"
                url = f"http://example.com/{job_id}-{item_id}.mp4" if status == "completed" else None

                renders_data.append((job_id, item_id, hash_val, quality, url, status))

        cursor.executemany("""
            INSERT INTO jobs (job_id, state, progress, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, jobs_data)

        cursor.executemany("""
            INSERT INTO renders (job_id, item_id, hash, quality, url, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (job_id, item_id, hash_val, quality, url, status, created_at, created_at)
            for job_id, item_id, hash_val, quality, url, status in renders_data
        ])

        conn.commit()
        conn.close()

        return job_count, len(renders_data)


class DatabaseTestUtilities:
    """Utilities for database testing operations."""

    @staticmethod
    def assert_table_exists(db_path: str, table_name: str):
        """Assert that a table exists in the database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table_name,))

        result = cursor.fetchone()
        conn.close()

        assert result is not None, f"Table {table_name} does not exist"

    @staticmethod
    def assert_table_count(db_path: str, table_name: str, expected_count: int):
        """Assert that a table has the expected number of rows."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        actual_count = cursor.fetchone()[0]

        conn.close()

        assert actual_count == expected_count, \
            f"Table {table_name} has {actual_count} rows, expected {expected_count}"

    @staticmethod
    def assert_index_exists(db_path: str, index_name: str):
        """Assert that an index exists in the database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name=?
        """, (index_name,))

        result = cursor.fetchone()
        conn.close()

        assert result is not None, f"Index {index_name} does not exist"

    @staticmethod
    def get_table_schema(db_path: str, table_name: str) -> str:
        """Get the CREATE statement for a table."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        result = cursor.fetchone()

        conn.close()

        return result[0] if result else ""

    @staticmethod
    def assert_foreign_key_enforcement(db_path: str):
        """Assert that foreign key constraints are enabled."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()

        conn.close()

        assert result[0] == 1, "Foreign key constraints are not enabled"

    @staticmethod
    def measure_query_performance(db_path: str, query: str, params: tuple = ()) -> float:
        """Measure execution time of a database query."""
        import time

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        start_time = time.time()
        cursor.execute(query, params)
        cursor.fetchall()
        end_time = time.time()

        conn.close()

        return end_time - start_time

    @staticmethod
    def simulate_database_lock(db_path: str, duration: float = 5.0):
        """Simulate a database lock for testing timeout behavior."""
        import threading
        import time

        def lock_database():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Start exclusive transaction
            cursor.execute("BEGIN EXCLUSIVE")
            time.sleep(duration)
            cursor.execute("COMMIT")
            conn.close()

        lock_thread = threading.Thread(target=lock_database)
        lock_thread.start()

        return lock_thread

    @staticmethod
    def create_test_backup(db_path: str, backup_path: str = None):
        """Create a test database backup."""
        if backup_path is None:
            backup_path = db_path.replace('.db', '_backup.db')

        source_conn = sqlite3.connect(db_path)
        backup_conn = sqlite3.connect(backup_path)

        source_conn.backup(backup_conn)

        source_conn.close()
        backup_conn.close()

        return backup_path