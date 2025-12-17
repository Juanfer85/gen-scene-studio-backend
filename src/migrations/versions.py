"""
Database migration definitions for Gen Scene Studio

Migration versioning scheme: MAJOR.MINOR.PATCH
- MAJOR: Major database structure changes
- MINOR: New tables or columns
- PATCH: Indexes, constraints, or performance changes
"""

from .manager import Migration

# Migration definitions
MIGRATIONS = [
    Migration(
        version="1.0.0",
        description="Initial database schema with jobs, renders, and assets_cache tables",
        upgrade_sql="""
        -- Create jobs table
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            state TEXT NOT NULL CHECK (state IN ('queued', 'processing', 'completed', 'error', 'cancelled')),
            progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
            created_at INTEGER NOT NULL,
            updated_at INTEGER,
            CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100)
        );

        -- Create renders table
        CREATE TABLE IF NOT EXISTS renders (
            job_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            hash TEXT NOT NULL,
            quality TEXT NOT NULL CHECK (quality IN ('low', 'medium', 'high', 'ultra')),
            url TEXT,
            status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'error')),
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            updated_at INTEGER DEFAULT (strftime('%s', 'now')),
            PRIMARY KEY (job_id, item_id),
            FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
        );

        -- Create assets_cache table
        CREATE TABLE IF NOT EXISTS assets_cache (
            hash TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            size INTEGER,
            content_type TEXT,
            expires_at INTEGER,
            access_count INTEGER DEFAULT 0,
            last_accessed INTEGER DEFAULT (strftime('%s', 'now'))
        );

        -- Create indexes for jobs table
        CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(state);
        CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
        CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at);

        -- Create indexes for renders table
        CREATE INDEX IF NOT EXISTS idx_renders_job_id ON renders(job_id);
        CREATE INDEX IF NOT EXISTS idx_renders_status ON renders(status);
        CREATE INDEX IF NOT EXISTS idx_renders_hash ON renders(hash);
        CREATE INDEX IF NOT EXISTS idx_renders_quality ON renders(quality);

        -- Create indexes for assets_cache table
        CREATE INDEX IF NOT EXISTS idx_assets_cache_created_at ON assets_cache(created_at);
        CREATE INDEX IF NOT EXISTS idx_assets_cache_expires_at ON assets_cache(expires_at);
        CREATE INDEX IF NOT EXISTS idx_assets_cache_last_accessed ON assets_cache(last_accessed);
        """,
        downgrade_sql="""
        -- Drop indexes first
        DROP INDEX IF EXISTS idx_jobs_state;
        DROP INDEX IF EXISTS idx_jobs_created_at;
        DROP INDEX IF EXISTS idx_jobs_updated_at;
        DROP INDEX IF EXISTS idx_renders_job_id;
        DROP INDEX IF EXISTS idx_renders_status;
        DROP INDEX IF EXISTS idx_renders_hash;
        DROP INDEX IF EXISTS idx_renders_quality;
        DROP INDEX IF EXISTS idx_assets_cache_created_at;
        DROP INDEX IF EXISTS idx_assets_cache_expires_at;
        DROP INDEX IF EXISTS idx_assets_cache_last_accessed;

        -- Drop tables
        DROP TABLE IF EXISTS assets_cache;
        DROP TABLE IF EXISTS renders;
        DROP TABLE IF EXISTS jobs;
        """
    ),

    Migration(
        version="1.0.1",
        description="Add performance indexes and constraints",
        upgrade_sql="""
        -- Add composite indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_renders_job_quality ON renders(job_id, quality);
        CREATE INDEX IF NOT EXISTS idx_renders_job_status ON renders(job_id, status);
        CREATE INDEX IF NOT EXISTS idx_jobs_state_created ON jobs(state, created_at);

        -- Add partial index for active jobs only
        CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(created_at) WHERE state IN ('queued', 'processing');

        -- Add partial index for completed renders
        CREATE INDEX IF NOT EXISTS idx_renders_completed ON renders(created_at) WHERE status = 'completed' AND url IS NOT NULL;
        """,
        downgrade_sql="""
        -- Drop composite indexes
        DROP INDEX IF EXISTS idx_renders_job_quality;
        DROP INDEX IF EXISTS idx_renders_job_status;
        DROP INDEX IF EXISTS idx_jobs_state_created;
        DROP INDEX IF EXISTS idx_jobs_active;
        DROP INDEX IF EXISTS idx_renders_completed;
        """
    ),

    Migration(
        version="1.1.0",
        description="Add job metadata and render statistics",
        upgrade_sql="""
        -- Add metadata columns to jobs table
        ALTER TABLE jobs ADD COLUMN job_type TEXT DEFAULT 'quick_create';
        ALTER TABLE jobs ADD COLUMN config_json TEXT;
        ALTER TABLE jobs ADD COLUMN error_message TEXT;
        ALTER TABLE jobs ADD COLUMN retry_count INTEGER DEFAULT 0;
        ALTER TABLE jobs ADD COLUMN priority INTEGER DEFAULT 0;

        -- Add metadata columns to renders table
        ALTER TABLE renders ADD COLUMN processing_time_ms INTEGER;
        ALTER TABLE renders ADD COLUMN file_size INTEGER;
        ALTER TABLE renders ADD COLUMN thumbnail_url TEXT;
        ALTER TABLE renders ADD COLUMN metadata_json TEXT;

        -- Create indexes for new columns
        CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(job_type);
        CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority DESC);
        CREATE INDEX IF NOT EXISTS idx_jobs_retry_count ON jobs(retry_count);
        CREATE INDEX IF NOT EXISTS idx_renders_processing_time ON renders(processing_time_ms);
        """,
        downgrade_sql="""
        -- Drop new indexes
        DROP INDEX IF EXISTS idx_jobs_type;
        DROP INDEX IF EXISTS idx_jobs_priority;
        DROP INDEX IF EXISTS idx_jobs_retry_count;
        DROP INDEX IF EXISTS idx_renders_processing_time;

        -- Remove new columns (SQLite doesn't support DROP COLUMN, so recreate table)
        CREATE TABLE jobs_backup AS SELECT job_id, state, progress, created_at, updated_at FROM jobs;
        DROP TABLE jobs;
        CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY,
            state TEXT NOT NULL CHECK (state IN ('queued', 'processing', 'completed', 'error', 'cancelled')),
            progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
            created_at INTEGER NOT NULL,
            updated_at INTEGER,
            CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100)
        );
        INSERT INTO jobs SELECT * FROM jobs_backup;
        DROP TABLE jobs_backup;

        CREATE TABLE renders_backup AS SELECT job_id, item_id, hash, quality, url, status, created_at, updated_at FROM renders;
        DROP TABLE renders;
        CREATE TABLE renders (
            job_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            hash TEXT NOT NULL,
            quality TEXT NOT NULL CHECK (quality IN ('low', 'medium', 'high', 'ultra')),
            url TEXT,
            status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'error')),
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            updated_at INTEGER DEFAULT (strftime('%s', 'now')),
            PRIMARY KEY (job_id, item_id),
            FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
        );
        INSERT INTO renders SELECT * FROM renders_backup;
        DROP TABLE renders_backup;
        """
    ),

    Migration(
        version="1.1.1",
        description="Add audit trail and optimization fields",
        upgrade_sql="""
        -- Create job_audit table for tracking changes
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
            FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
        );

        -- Create render_performance table for performance tracking
        CREATE TABLE IF NOT EXISTS render_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            quality TEXT NOT NULL,
            processing_time_ms INTEGER,
            queue_time_ms INTEGER,
            render_time_ms INTEGER,
            upload_time_ms INTEGER,
            total_time_ms INTEGER,
            file_size INTEGER,
            success BOOLEAN NOT NULL,
            error_code TEXT,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
        );

        -- Create indexes for audit tables
        CREATE INDEX IF NOT EXISTS idx_job_audit_job_id ON job_audit(job_id);
        CREATE INDEX IF NOT EXISTS idx_job_audit_changed_at ON job_audit(changed_at);
        CREATE INDEX IF NOT EXISTS idx_render_performance_job_id ON render_performance(job_id);
        CREATE INDEX IF NOT EXISTS idx_render_performance_quality ON render_performance(quality);
        CREATE INDEX IF NOT EXISTS idx_render_performance_success ON render_performance(success);
        """,
        downgrade_sql="""
        -- Drop audit and performance tables
        DROP INDEX IF EXISTS idx_job_audit_job_id;
        DROP INDEX IF EXISTS idx_job_audit_changed_at;
        DROP INDEX IF EXISTS idx_render_performance_job_id;
        DROP INDEX IF EXISTS idx_render_performance_quality;
        DROP INDEX IF EXISTS idx_render_performance_success;

        DROP TABLE IF EXISTS render_performance;
        DROP TABLE IF EXISTS job_audit;
        """
    ),

    Migration(
        version="1.2.0",
        description="Add database optimization and cleanup utilities",
        upgrade_sql="""
        -- Create database_stats table for monitoring
        CREATE TABLE IF NOT EXISTS database_stats (
            id INTEGER PRIMARY KEY,
            table_name TEXT NOT NULL,
            record_count INTEGER,
            total_size_mb REAL,
            last_analyzed INTEGER,
            last_vacuumed INTEGER,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        );

        -- Create cleanup_queue table for automated cleanup
        CREATE TABLE IF NOT EXISTS cleanup_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id TEXT,
            cleanup_type TEXT NOT NULL CHECK (cleanup_type IN ('expired', 'orphaned', 'duplicate')),
            priority INTEGER DEFAULT 0,
            scheduled_at INTEGER DEFAULT (strftime('%s', 'now')),
            processed_at INTEGER,
            processed BOOLEAN DEFAULT 0,
            error_message TEXT
        );

        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_database_stats_table_name ON database_stats(table_name);
        CREATE INDEX IF NOT EXISTS idx_cleanup_queue_priority ON cleanup_queue(priority DESC);
        CREATE INDEX IF NOT EXISTS idx_cleanup_queue_scheduled ON cleanup_queue(scheduled_at);
        CREATE INDEX IF NOT EXISTS idx_cleanup_queue_unprocessed ON cleanup_queue(processed, priority DESC);
        """,
        downgrade_sql="""
        -- Drop optimization tables
        DROP INDEX IF EXISTS idx_database_stats_table_name;
        DROP INDEX IF EXISTS idx_cleanup_queue_priority;
        DROP INDEX IF EXISTS idx_cleanup_queue_scheduled;
        DROP INDEX IF EXISTS idx_cleanup_queue_unprocessed;

        DROP TABLE IF EXISTS cleanup_queue;
        DROP TABLE IF EXISTS database_stats;
        """
    )
]

# Helper function to get migrations up to specific version
def get_migrations_up_to(version: str) -> list:
    """Get all migrations up to and including specified version"""
    return [m for m in MIGRATIONS if m.version <= version]

# Helper function to get migrations after version
def get_migrations_after(version: str) -> list:
    """Get all migrations after specified version"""
    return [m for m in MIGRATIONS if m.version > version]

# Helper function to get latest version
def get_latest_version() -> str:
    """Get the latest migration version"""
    return max(m.version for m in MIGRATIONS) if MIGRATIONS else "0.0.0"