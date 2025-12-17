import sqlite3
import threading
import time
import weakref
from contextlib import contextmanager
from typing import Optional, Dict, Any, Set
from pathlib import Path
from queue import Queue, Empty
from dataclasses import dataclass
from core.config import settings
import logging

log = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    """Information about a database connection"""
    connection: sqlite3.Connection
    created_at: float
    last_used: float
    thread_id: int
    is_active: bool = True
    use_count: int = 0

class DatabaseConnectionPool:
    """Advanced connection pool with thread safety and connection reuse"""

    def __init__(self,
                 db_path: Optional[str] = None,
                 max_connections: int = 20,
                 max_idle_time: int = 300,  # 5 minutes
                 max_lifetime: int = 3600):  # 1 hour
        self.db_path = Path(db_path or settings.DATABASE_URL.replace("sqlite:///", ""))
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.max_lifetime = max_lifetime

        # Thread-safe structures
        self._pool: Queue[ConnectionInfo] = Queue(maxsize=max_connections)
        self._active_connections: Dict[int, ConnectionInfo] = {}
        self._all_connections: weakref.WeakSet = weakref.WeakSet()
        self._pool_lock = threading.RLock()

        # Statistics
        self._stats = {
            'created': 0,
            'reused': 0,
            'expired': 0,
            'closed': 0,
            'active_count': 0,
            'pool_size': 0
        }

        # Initialize database directory
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self._cleanup_thread.start()

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool with automatic return"""
        conn_info = self._acquire_connection()
        thread_id = threading.get_ident()

        try:
            # Register as active for this thread
            with self._pool_lock:
                self._active_connections[thread_id] = conn_info

            # Configure connection if needed
            self._configure_connection(conn_info.connection)

            yield conn_info.connection

        finally:
            # Mark as inactive and return to pool
            conn_info.is_active = False
            self._return_to_pool(conn_info)

    def _acquire_connection(self) -> ConnectionInfo:
        """Acquire a connection from pool or create new one"""
        thread_id = threading.get_ident()
        now = time.time()

        with self._pool_lock:
            # Check if thread already has active connection
            if thread_id in self._active_connections:
                conn_info = self._active_connections[thread_id]
                conn_info.last_used = now
                conn_info.use_count += 1
                self._stats['reused'] += 1
                return conn_info

            # Try to get from pool
            try:
                conn_info = self._pool.get_nowait()

                # Check if connection is still valid
                if self._is_connection_valid(conn_info, now):
                    conn_info.last_used = now
                    conn_info.is_active = True
                    conn_info.use_count += 1
                    self._stats['reused'] += 1
                    return conn_info
                else:
                    # Connection expired, create new
                    self._close_connection(conn_info.connection)
                    self._stats['expired'] += 1

            except Empty:
                pass

            # Create new connection if under limit
            if len(self._all_connections) < self.max_connections:
                return self._create_connection(thread_id, now)

            # Pool full, wait for available connection
            return self._wait_for_connection(thread_id, now)

    def _create_connection(self, thread_id: int, now: float) -> ConnectionInfo:
        """Create a new database connection"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0,
            isolation_level=None  # Autocommit mode
        )

        conn.row_factory = sqlite3.Row

        # SQLite optimizations
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = 10000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB

        conn_info = ConnectionInfo(
            connection=conn,
            created_at=now,
            last_used=now,
            thread_id=thread_id,
            is_active=True,
            use_count=1
        )

        with self._pool_lock:
            self._all_connections.add(conn_info)
            self._stats['created'] += 1
            self._stats['active_count'] += 1

        return conn_info

    def _wait_for_connection(self, thread_id: int, now: float) -> ConnectionInfo:
        """Wait for an available connection from the pool"""
        timeout = 30  # Maximum wait time

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                conn_info = self._pool.get(timeout=1)

                if self._is_connection_valid(conn_info, now):
                    conn_info.last_used = now
                    conn_info.is_active = True
                    conn_info.use_count += 1
                    return conn_info
                else:
                    self._close_connection(conn_info.connection)

            except Empty:
                continue

        raise TimeoutError(f"Could not acquire database connection within {timeout} seconds")

    def _return_to_pool(self, conn_info: ConnectionInfo):
        """Return a connection to the pool"""
        thread_id = threading.get_ident()

        with self._pool_lock:
            # Remove from active connections
            self._active_connections.pop(thread_id, None)

            # Return to pool if valid and space available
            if (self._is_connection_valid(conn_info, time.time()) and
                not self._pool.full()):
                conn_info.is_active = False
                self._pool.put(conn_info)
            else:
                # Close connection
                self._close_connection(conn_info.connection)
                self._stats['closed'] += 1

    def _is_connection_valid(self, conn_info: ConnectionInfo, now: float) -> bool:
        """Check if connection is still valid"""
        try:
            # Check age
            if now - conn_info.created_at > self.max_lifetime:
                return False

            # Check idle time
            if not conn_info.is_active and now - conn_info.last_used > self.max_idle_time:
                return False

            # Test connection
            cursor = conn_info.connection.cursor()
            cursor.execute("SELECT 1")
            return True

        except (sqlite3.Error, sqlite3.OperationalError):
            return False

    def _configure_connection(self, conn: sqlite3.Connection):
        """Configure connection settings"""
        try:
            # Set busy timeout
            conn.execute("PRAGMA busy_timeout = 30000")  # 30 seconds

            # Additional optimizations
            conn.execute("PRAGMA optimize")

        except sqlite3.Error as e:
            log.warning(f"Failed to configure connection: {e}")

    def _close_connection(self, conn: sqlite3.Connection):
        """Close a connection safely"""
        try:
            conn.close()
        except sqlite3.Error:
            pass  # Connection already closed

    def _cleanup_expired(self):
        """Background thread to cleanup expired connections"""
        while True:
            try:
                time.sleep(60)  # Check every minute
                self._cleanup_pool()

            except Exception as e:
                log.error(f"Error in cleanup thread: {e}")

    def _cleanup_pool(self):
        """Remove expired connections from pool"""
        now = time.time()
        to_remove = []

        # Check pool connections
        temp_connections = []
        while not self._pool.empty():
            try:
                conn_info = self._pool.get_nowait()

                if self._is_connection_valid(conn_info, now):
                    temp_connections.append(conn_info)
                else:
                    to_remove.append(conn_info)

            except Empty:
                break

        # Return valid connections to pool
        for conn_info in temp_connections:
            self._pool.put(conn_info)

        # Close invalid connections
        for conn_info in to_remove:
            self._close_connection(conn_info.connection)
            self._stats['expired'] += 1

    def get_statistics(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self._pool_lock:
            self._stats['active_count'] = len(self._active_connections)
            self._stats['pool_size'] = self._pool.qsize()

        return dict(self._stats)

    def close_all(self):
        """Close all connections (cleanup)"""
        with self._pool_lock:
            # Close active connections
            for conn_info in self._active_connections.values():
                self._close_connection(conn_info.connection)

            # Close pool connections
            while not self._pool.empty():
                try:
                    conn_info = self._pool.get_nowait()
                    self._close_connection(conn_info.connection)
                except Empty:
                    break

            # Clear tracking
            self._active_connections.clear()
            self._all_connections.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()

class DatabaseManager:
    """High-level database manager with connection pooling and migrations"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_URL.replace("sqlite:///", "")
        self.connection_pool = DatabaseConnectionPool(db_path)

        # Initialize repositories
        self._repositories = {}

    def get_connection(self):
        """Get a connection from the pool"""
        return self.connection_pool.get_connection()

    @contextmanager
    def transaction(self):
        """Execute operations in a transaction"""
        with self.get_connection() as conn:
            try:
                # Start transaction
                conn.execute("BEGIN")
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def get_repository(self, repository_class):
        """Get or create a repository instance"""
        if repository_class not in self._repositories:
            self._repositories[repository_class] = repository_class(self.db_path)
        return self._repositories[repository_class]

    # Quick access to common repositories
    def jobs(self):
        """Get job repository"""
        from .job import JobRepository
        return self.get_repository(JobRepository)

    def renders(self):
        """Get render repository"""
        from .render import RenderRepository
        return self.get_repository(RenderRepository)

    def assets_cache(self):
        """Get assets cache repository"""
        from .assets_cache import AssetsCacheRepository
        return self.get_repository(AssetsCacheRepository)

    def initialize_database(self):
        """Initialize all database tables"""
        with self.get_connection() as conn:
            # Use individual repositories to create tables
            self.jobs().create_table()
            self.renders().create_table()
            self.assets_cache().create_table()

    def backup_database(self, backup_path: str):
        """Create a backup of the database"""
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        with self.get_connection() as source_conn:
            backup_conn = sqlite3.connect(backup_path)

            try:
                source_conn.backup(backup_conn)
            finally:
                backup_conn.close()

    def get_database_info(self) -> Dict[str, Any]:
        """Get comprehensive database information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            # Get table sizes
            table_info = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_info[table] = count

            # Get database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]

            # Get pool statistics
            pool_stats = self.connection_pool.get_statistics()

            return {
                'database_path': str(self.db_path),
                'database_size_bytes': db_size,
                'tables': table_info,
                'connection_pool': pool_stats,
                'repositories': list(self._repositories.keys())
            }

    def optimize_database(self):
        """Optimize the database"""
        with self.get_connection() as conn:
            # Analyze tables
            cursor = conn.cursor()
            tables = ['jobs', 'renders', 'assets_cache']

            for table in tables:
                cursor.execute(f"ANALYZE {table}")

            # VACUUM for defragmentation
            conn.execute("VACUUM")

    def close(self):
        """Close the database manager and all connections"""
        self.connection_pool.close_all()
        self._repositories.clear()

    def __enter__(self):
        self.initialize_database()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Global database manager instance
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def close_database_manager():
    """Close the global database manager"""
    global _db_manager
    if _db_manager is not None:
        _db_manager.close()
        _db_manager = None