"""
Optimized SQLite connection with production PRAGMAs
Significant performance improvements for production workloads
"""
import sqlite3
import threading
import time
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
from core.config import settings

DB_PATH = Path(settings.DATABASE_URL.replace("sqlite:///", ""))

# Thread-local storage for connections
_local = threading.local()

# Production SQLite PRAGMAs for maximum performance
PRODUCTION_PRAGMAS = {
    # WAL mode - allows concurrent reads/writes
    "journal_mode": "WAL",

    # Synchronous mode - balance between safety and performance
    "synchronous": "NORMAL",

    # Cache size - 64MB of cache
    "cache_size": -64000,

    # Memory mapping - map database into memory
    "mmap_size": 268435456,  # 256MB

    # Temporary storage - memory instead of disk
    "temp_store": "MEMORY",

    # Page size - optimal for SSD/NVMe
    "page_size": 32768,

    # Locking mode - allow multiple readers
    "locking_mode": "NORMAL",

    # Query optimizer settings
    "optimize": "ON",
    "query_only": "OFF",

    # Foreign key enforcement
    "foreign_keys": "ON",

    # Integrity checks
    "integrity_check": "OFF",  # Skip for performance

    # Auto-vacuum settings
    "auto_vacuum": "INCREMENTAL",

    # Write-ahead log checkpoint
    "wal_autocheckpoint": 1000,

    # Busy timeout - wait for locks
    "busy_timeout": 30000,  # 30 seconds

    # Recursive triggers
    "recursive_triggers": "OFF",

    # Secure delete - faster deletes
    "secure_delete": "FAST",

    # Analysis limit for query planner
    "analysis_limit": 1000,
}

class OptimizedSQLiteConnection:
    """Thread-safe optimized SQLite connection manager"""

    def __init__(self):
        self._connection_count = 0
        self._last_optimization = time.time()
        self._optimization_interval = 3600  # 1 hour

    def _apply_pragmas(self, conn: sqlite3.Connection):
        """Apply production PRAGMAs to connection"""
        cursor = conn.cursor()

        try:
            for pragma, value in PRODUCTION_PRAGMAS.items():
                cursor.execute(f"PRAGMA {pragma} = {value}")

            # Additional one-time optimizations
            if time.time() - self._last_optimization > self._optimization_interval:
                cursor.execute("PRAGMA optimize")
                cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                self._last_optimization = time.time()

        except Exception as e:
            # Fallback to basic settings if PRAGMAs fail
            print(f"Warning: Could not apply all PRAGMAs: {e}")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA cache_size = -32000")

        finally:
            cursor.close()

    def get_connection(self) -> sqlite3.Connection:
        """Get thread-local optimized connection"""
        if not hasattr(_local, 'connection') or _local.connection is None:
            _local.connection = sqlite3.connect(
                DB_PATH,
                timeout=30.0,
                check_same_thread=False
            )
            _local.connection.row_factory = sqlite3.Row

            # Apply production optimizations
            self._apply_pragmas(_local.connection)

            self._connection_count += 1

        return _local.connection

    def close_connection(self):
        """Close thread-local connection"""
        if hasattr(_local, 'connection') and _local.connection is not None:
            try:
                _local.connection.close()
            except:
                pass
            finally:
                _local.connection = None

# Global optimized connection manager
optimized_db = OptimizedSQLiteConnection()

def get_conn() -> sqlite3.Connection:
    """Get optimized database connection"""
    return optimized_db.get_connection()

@contextmanager
def get_transaction():
    """Context manager for transactions with automatic rollback on error"""
    conn = get_conn()
    try:
        # Begin transaction
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        # Don't close connection - keep it in thread-local pool
        pass

def get_connection_stats() -> dict:
    """Get database connection statistics"""
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # Get page count and database size
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]

        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]

        cursor.close()

        return {
            "connections_opened": optimized_db._connection_count,
            "database_size_bytes": page_count * page_size,
            "database_size_mb": round((page_count * page_size) / (1024 * 1024), 2),
            "page_count": page_count,
            "page_size": page_size,
            "wal_mode": True,
            "last_optimization": optimized_db._last_optimization
        }

    except Exception as e:
        return {
            "error": str(e),
            "connections_opened": optimized_db._connection_count
        }

def optimize_database():
    """Run database optimization and maintenance"""
    try:
        conn = get_conn()
        cursor = conn.cursor()

        print("🔧 Running database optimization...")

        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()

        # Analyze tables for query optimizer
        cursor.execute("ANALYZE")

        # Incremental vacuum
        cursor.execute("PRAGMA incremental_vacuum")

        # Optimize query plans
        cursor.execute("PRAGMA optimize")

        # Checkpoint WAL
        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        cursor.close()
        conn.commit()

        optimized_db._last_optimization = time.time()

        return {
            "status": "success",
            "integrity_check": integrity_result[0] if integrity_result else "unknown",
            "optimization_time": time.time()
        }

    except Exception as e:
        print(f"❌ Database optimization failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def cleanup_connections():
    """Cleanup all thread-local connections (for shutdown)"""
    try:
        optimized_db.close_connection()
        print("✅ Database connections cleaned up")
    except Exception as e:
        print(f"❌ Error cleaning up connections: {e}")

# Connection pool for high-load scenarios
class ConnectionPool:
    """Simple connection pool for high-load scenarios"""

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._pool = []
        self._used = set()
        self._lock = threading.Lock()

    def get_connection(self) -> sqlite3.Connection:
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
            elif len(self._used) < self.max_connections:
                conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                optimized_db._apply_pragmas(conn)
            else:
                raise RuntimeError("Connection pool exhausted")

            self._used.add(conn)
            return conn

    def return_connection(self, conn: sqlite3.Connection):
        with self._lock:
            if conn in self._used:
                self._used.remove(conn)
                try:
                    # Reset connection state
                    conn.rollback()
                    self._pool.append(conn)
                except:
                    conn.close()

# Optional connection pool (can be enabled for high-load scenarios)
connection_pool = ConnectionPool(max_connections=5)