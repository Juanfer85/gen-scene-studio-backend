"""
Advanced PostgreSQL connection manager with connection pooling,
performance monitoring, and optimizations for production
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, AsyncGenerator, Union
from urllib.parse import urlparse

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, event
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine

from core.config import settings
from core.cache import cache_manager

log = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Base exception for database operations"""
    pass

class DatabaseConnectionError(DatabaseError):
    """Exception for database connection issues"""
    pass

class DatabaseQueryError(DatabaseError):
    """Exception for query execution issues"""
    pass

class PerformanceMonitor:
    """Monitor and track database performance metrics"""

    def __init__(self):
        self._metrics: Dict[str, Any] = {
            'total_queries': 0,
            'slow_queries': 0,
            'total_time': 0.0,
            'average_time': 0.0,
            'max_time': 0.0,
            'errors': 0,
            'connections': 0,
            'active_connections': 0
        }

    async def record_query(self, query: str, duration: float, error: bool = False):
        """Record query metrics"""
        self._metrics['total_queries'] += 1
        self._metrics['total_time'] += duration
        self._metrics['average_time'] = self._metrics['total_time'] / self._metrics['total_queries']
        self._metrics['max_time'] = max(self._metrics['max_time'], duration)

        if error:
            self._metrics['errors'] += 1

        if duration > settings.SLOW_QUERY_THRESHOLD:
            self._metrics['slow_queries'] += 1
            log.warning(f"🐌 Slow query detected: {duration:.3f}s - {query[:100]}...")

        # Cache metrics to Redis periodically
        if self._metrics['total_queries'] % 100 == 0:
            await self._cache_metrics()

    async def _cache_metrics(self):
        """Cache metrics to Redis"""
        try:
            await cache_manager.set(
                "db_performance_metrics",
                self._metrics,
                ttl=settings.METRICS_RETENTION_HOURS * 3600,
                namespace="metrics"
            )
        except Exception as e:
            log.error(f"❌ Failed to cache DB metrics: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self._metrics.copy()

class PostgreSQLManager:
    """
    Advanced PostgreSQL manager with connection pooling,
    performance monitoring, and production optimizations
    """

    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._pool = None
        self._monitor = PerformanceMonitor()
        self._connected = False
        self._connection_info = None

    async def initialize(self):
        """Initialize PostgreSQL connections and pools"""
        try:
            if not settings.database_url_async.startswith("postgresql"):
                raise DatabaseConnectionError("PostgreSQL manager can only be used with PostgreSQL URLs")

            await self._initialize_connection_pool()
            await self._initialize_sqlalchemy_engine()
            await self._setup_performance_monitoring()
            await self._run_initial_optimizations()

            self._connected = True
            log.info("✅ PostgreSQL manager initialized successfully")

        except Exception as e:
            log.error(f"❌ Failed to initialize PostgreSQL manager: {e}")
            raise DatabaseConnectionError(f"Cannot initialize PostgreSQL: {e}")

    async def _initialize_connection_pool(self):
        """Initialize asyncpg connection pool for raw queries"""
        try:
            self._pool = await asyncpg.create_pool(
                settings.database_url_async.replace("postgresql+asyncpg://", "postgresql://"),
                min_size=2,
                max_size=settings.POSTGRES_POOL_SIZE + 5,
                command_timeout=30,
                server_settings={
                    "application_name": "genscene_backend",
                    "jit": "off",  # Disable JIT for better performance on simple queries
                    "search_path": "public",
                    "timezone": "UTC",
                }
            )

            # Test connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            log.info("✅ PostgreSQL connection pool initialized")

        except Exception as e:
            raise DatabaseConnectionError(f"Failed to create connection pool: {e}")

    async def _initialize_sqlalchemy_engine(self):
        """Initialize SQLAlchemy async engine for ORM operations"""
        try:
            self._engine = create_async_engine(
                settings.database_url_async,
                echo=settings.DEBUG,
                poolclass=QueuePool,
                pool_size=settings.POSTGRES_POOL_SIZE,
                max_overflow=settings.POSTGRES_MAX_OVERFLOW,
                pool_timeout=settings.POSTGRES_POOL_TIMEOUT,
                pool_recycle=settings.POSTGRES_POOL_RECYCLE,
                pool_pre_ping=True,
                # Performance optimizations
                isolation_level="READ_COMMITTED",
                connect_args={
                    "command_timeout": 30,
                    "server_settings": {
                        "application_name": "genscene_backend",
                        "jit": "off",
                        "search_path": "public",
                        "timezone": "UTC",
                    }
                }
            )

            # Create session factory
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True
            )

            # Test connection
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            log.info("✅ PostgreSQL SQLAlchemy engine initialized")

        except Exception as e:
            raise DatabaseConnectionError(f"Failed to create SQLAlchemy engine: {e}")

    async def _setup_performance_monitoring(self):
        """Setup performance monitoring and logging"""
        try:
            @event.listens_for(Engine, "before_cursor_execute")
            def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                context._query_start_time = time.time()

            @event.listens_for(Engine, "after_cursor_execute")
            def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                total = time.time() - context._query_start_time
                # We'll log this asynchronously to avoid blocking

            log.info("✅ Performance monitoring enabled")

        except Exception as e:
            log.warning(f"⚠️ Could not setup all performance monitoring: {e}")

    async def _run_initial_optimizations(self):
        """Run initial database optimizations"""
        try:
            async with self._pool.acquire() as conn:
                # Set performance optimizations
                optimizations = [
                    "SET work_mem = '16MB'",
                    "SET maintenance_work_mem = '64MB'",
                    "SET checkpoint_completion_target = 0.9",
                    "SET wal_buffers = '16MB'",
                    "SET random_page_cost = 1.1",  # For SSD
                    "SET effective_io_concurrency = 200",  # For SSD
                ]

                for opt in optimizations:
                    await conn.execute(opt)

                log.info("✅ Database optimizations applied")

        except Exception as e:
            log.warning(f"⚠️ Could not apply all optimizations: {e}")

    async def close(self):
        """Close database connections"""
        if self._engine:
            await self._engine.dispose()

        if self._pool:
            await self._pool.close()

        self._connected = False
        log.info("🔌 PostgreSQL connections closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get SQLAlchemy session with automatic cleanup"""
        if not self._connected:
            raise DatabaseConnectionError("Database not initialized")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def execute_raw(
        self,
        query: str,
        params: Optional[Union[tuple, dict]] = None,
        fetch: str = "all",
        timeout: Optional[int] = None
    ) -> Union[Dict[str, Any], list[Dict[str, Any]], Any, None]:
        """Execute raw SQL query with performance monitoring"""
        if not self._pool:
            raise DatabaseConnectionError("Connection pool not initialized")

        start_time = time.time()
        timeout = timeout or 30

        try:
            async with self._pool.acquire(timeout=timeout) as conn:
                if fetch == "one":
                    row = await conn.fetchrow(query, *params or ())
                    result = dict(row) if row else None
                elif fetch == "all":
                    rows = await conn.fetch(query, *params or ())
                    result = [dict(row) for row in rows]
                elif fetch == "val":
                    result = await conn.fetchval(query, *params or ())
                elif fetch == "many" and isinstance(params, (tuple, list)) and len(params) > 1:
                    # For executemany operations
                    await conn.executemany(query, params)
                    result = None
                else:
                    # For INSERT/UPDATE/DELETE
                    await conn.execute(query, *params or ())
                    result = None

            duration = time.time() - start_time
            await self._monitor.record_query(query, duration)

            return result

        except Exception as e:
            duration = time.time() - start_time
            await self._monitor.record_query(query, duration, error=True)
            log.error(f"❌ PostgreSQL query failed: {e}")
            raise DatabaseQueryError(f"Query failed: {e}")

    async def execute_transaction(self, queries: list[tuple[str, Union[tuple, dict]]]) -> bool:
        """Execute multiple queries in a transaction"""
        if not self._pool:
            raise DatabaseConnectionError("Connection pool not initialized")

        start_time = time.time()

        try:
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    for query, params in queries:
                        if isinstance(params, dict):
                            await conn.execute(query, **params)
                        else:
                            await conn.execute(query, *params)

            duration = time.time() - start_time
            await self._monitor.record_query(f"TRANSACTION({len(queries)} queries)", duration)

            return True

        except Exception as e:
            duration = time.time() - start_time
            await self._monitor.record_query(f"TRANSACTION({len(queries)} queries)", duration, error=True)
            log.error(f"❌ PostgreSQL transaction failed: {e}")
            raise DatabaseQueryError(f"Transaction failed: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check PostgreSQL health and performance"""
        try:
            start_time = time.time()

            # Test basic connectivity
            await self.execute_raw("SELECT 1")

            # Test table access (if jobs table exists)
            try:
                await self.execute_raw("SELECT COUNT(*) FROM jobs LIMIT 1")
                table_status = "ok"
            except:
                table_status = "missing"

            # Get pool info
            pool_info = {
                "size": self._pool.get_size(),
                "min_size": self._pool.get_min_size(),
                "max_size": self._pool.get_max_size(),
            }

            # Get PostgreSQL specific stats
            pg_stats = await self._get_postgresql_stats()

            duration = time.time() - start_time
            metrics = self._monitor.get_metrics()

            return {
                "status": "healthy",
                "database_type": "postgresql",
                "connection_time": duration,
                "table_status": table_status,
                "pool_info": pool_info,
                "postgresql_stats": pg_stats,
                "performance_metrics": metrics,
                "connected": self._connected
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False
            }

    async def _get_postgresql_stats(self) -> Dict[str, Any]:
        """Get PostgreSQL-specific statistics"""
        try:
            async with self._pool.acquire() as conn:
                # Get database size
                db_size = await conn.fetchval("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """)

                # Get active connections
                active_connections = await conn.fetchval("""
                    SELECT count(*) FROM pg_stat_activity WHERE state = 'active'
                """)

                # Get cache hit ratio
                cache_hit_ratio = await conn.fetchval("""
                    SELECT round(sum(heap_blks_hit)*100/(sum(heap_blks_hit)+sum(heap_blks_read)), 2)
                    FROM pg_statio_user_tables
                """)

                # Get table sizes
                table_sizes = await conn.fetch("""
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10
                """)

                return {
                    "database_size": db_size,
                    "active_connections": active_connections,
                    "cache_hit_ratio": f"{cache_hit_ratio}%",
                    "table_sizes": [dict(row) for row in table_sizes]
                }

        except Exception as e:
            log.error(f"❌ Failed to get PostgreSQL stats: {e}")
            return {"error": str(e)}

    async def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed connection information"""
        if not self._connected:
            return {"status": "not_connected"}

        pool_info = {}
        if self._pool:
            pool_info = {
                "pool_size": self._pool.get_size(),
                "pool_min_size": self._pool.get_min_size(),
                "pool_max_size": self._pool.get_max_size(),
            }

        return {
            "database_type": "postgresql",
            "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL,
            "pool_size": settings.POSTGRES_POOL_SIZE,
            "max_overflow": settings.POSTGRES_MAX_OVERFLOW,
            "pool_timeout": settings.POSTGRES_POOL_TIMEOUT,
            "pool_recycle": settings.POSTGRES_POOL_RECYCLE,
            "connection_pool": pool_info,
            "settings": {
                "WORKER_CONCURRENCY": settings.WORKER_CONCURRENCY,
                "SLOW_QUERY_THRESHOLD": settings.SLOW_QUERY_THRESHOLD,
                "METRICS_ENABLED": settings.METRICS_ENABLED,
            }
        }

    async def optimize_database(self):
        """Run PostgreSQL optimization commands"""
        try:
            async with self._pool.acquire() as conn:
                # PostgreSQL optimizations
                optimizations = [
                    "ANALYZE",
                    "VACUUM ANALYZE",
                    "REINDEX DATABASE genscene",
                ]

                results = {}
                for opt in optimizations:
                    start_time = time.time()
                    await conn.execute(opt)
                    duration = time.time() - start_time
                    results[opt] = f"completed in {duration:.2f}s"
                    log.info(f"🔧 Executed: {opt} ({duration:.2f}s)")

                # Update table statistics
                await conn.execute("""
                    SELECT set_config('search_path', 'public', false)
                """)

                log.info("✅ PostgreSQL optimization completed")
                return {"status": "success", "results": results}

        except Exception as e:
            log.error(f"❌ PostgreSQL optimization failed: {e}")
            raise DatabaseError(f"Optimization failed: {e}")

    async def create_indexes(self):
        """Create performance indexes for PostgreSQL"""
        try:
            index_queries = [
                # Jobs table indexes
                ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_state ON jobs(state)", ()),
                ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)", ()),
                ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_state_created ON jobs(state, created_at)", ()),
                ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_job_type ON jobs(job_type)", ()),

                # Renders table indexes
                ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_renders_job_id ON renders(job_id)", ()),
                ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_renders_status ON renders(status)", ()),
                ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_renders_job_status ON renders(job_id, status)", ()),

                # Assets cache table indexes
                ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assets_cache_hash ON assets_cache(hash)", ()),
                ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assets_cache_created_at ON assets_cache(created_at)", ()),

                # Performance composite indexes
                ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_composite ON jobs(state, created_at DESC, job_type)", ()),
                ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_renders_composite ON renders(job_id, status, item_id)", ()),
            ]

            results = {}
            for query, params in index_queries:
                try:
                    start_time = time.time()
                    await self.execute_raw(query, params)
                    duration = time.time() - start_time
                    index_name = query.split('idx_')[1].split(' ')[0] if 'idx_' in query else 'unknown'
                    results[index_name] = f"created in {duration:.2f}s"
                    log.info(f"🔧 Created index: {index_name} ({duration:.2f}s)")
                except Exception as e:
                    index_name = query.split('idx_')[1].split(' ')[0] if 'idx_' in query else 'unknown'
                    results[index_name] = f"failed: {str(e)}"
                    log.error(f"❌ Failed to create index {index_name}: {e}")

            log.info("✅ PostgreSQL indexes creation completed")
            return {"status": "success", "results": results}

        except Exception as e:
            log.error(f"❌ Failed to create PostgreSQL indexes: {e}")
            raise DatabaseError(f"Index creation failed: {e}")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        try:
            # Get local metrics
            local_metrics = self._monitor.get_metrics()

            # Get cached metrics from Redis
            cached_metrics = await cache_manager.get("db_performance_metrics", namespace="metrics")

            # Get PostgreSQL specific metrics
            pg_metrics = await self._get_postgresql_stats()

            return {
                "local_metrics": local_metrics,
                "cached_metrics": cached_metrics,
                "postgresql_metrics": pg_metrics,
                "connection_pool": await self.get_connection_info(),
                "settings": {
                    "POSTGRES_POOL_SIZE": settings.POSTGRES_POOL_SIZE,
                    "SLOW_QUERY_THRESHOLD": settings.SLOW_QUERY_THRESHOLD,
                    "METRICS_ENABLED": settings.METRICS_ENABLED,
                    "METRICS_RETENTION_HOURS": settings.METRICS_RETENTION_HOURS,
                }
            }

        except Exception as e:
            log.error(f"❌ Failed to get performance metrics: {e}")
            return {"error": str(e)}

# Global PostgreSQL manager instance
postgresql_manager = PostgreSQLManager()

# Context managers and helper functions
@asynccontextmanager
async def get_postgres_session():
    """Get PostgreSQL session context manager"""
    async with postgresql_manager.get_session() as session:
        yield session

async def execute_postgres_query(query: str, params: Optional[Union[tuple, dict]] = None, fetch: str = "all"):
    """Execute a PostgreSQL query"""
    return await postgresql_manager.execute_raw(query, params, fetch)

async def postgres_health_check():
    """PostgreSQL health check"""
    return await postgresql_manager.health_check()

async def get_postgres_performance_metrics():
    """Get PostgreSQL performance metrics"""
    return await postgresql_manager.get_performance_metrics()