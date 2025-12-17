import sqlite3
import time
from typing import Dict, List, Optional
from .base import BaseRepository
from models.entities import Job, JobState

class JobRepository(BaseRepository[Job]):
    """Repository for Job entities with CRUD operations and business logic"""

    def create_table(self) -> None:
        """Create jobs table if it doesn't exist"""
        query = """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            state TEXT NOT NULL CHECK (state IN ('queued', 'processing', 'completed', 'error', 'cancelled')),
            progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
            created_at INTEGER NOT NULL,
            updated_at INTEGER,
            CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100)
        )
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)

            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(state)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at)")
            conn.commit()

    def create(self, job: Job) -> str:
        """Create a new job"""
        now = int(time.time())
        job_data = job.dict()
        job_data['created_at'] = job_data.get('created_at', now)
        job_data['updated_at'] = now

        query = """
        INSERT INTO jobs (job_id, state, progress, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
            state = excluded.state,
            progress = excluded.progress,
            updated_at = excluded.updated_at
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                job.job_id,
                job.state.value,
                job.progress,
                job_data['created_at'],
                job_data['updated_at']
            ))
            conn.commit()
        return job.job_id

    def create_new(self, job_id: str, state: JobState = JobState.QUEUED, progress: int = 0) -> str:
        """Create a new job with minimal parameters"""
        now = int(time.time())
        query = """
        INSERT INTO jobs (job_id, state, progress, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (job_id, state.value, progress, now, now))
            conn.commit()
        return job_id

    def get_by_id(self, job_id: str) -> Optional[Job]:
        """Get a job by its ID"""
        query = "SELECT * FROM jobs WHERE job_id = ?"
        result = self._execute_query(query, (job_id,), fetch_one=True)
        return Job(**result) if result else None

    def update(self, job_id: str, updates: Dict[str, any]) -> bool:
        """Update job fields"""
        if not updates:
            return False

        # Always update updated_at timestamp
        updates['updated_at'] = int(time.time())

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [job_id]

        # Convert enum values to strings
        for i, (key, value) in enumerate(updates.items()):
            if isinstance(value, (JobState)):
                values[i] = value.value

        query = f"UPDATE jobs SET {set_clause} WHERE job_id = ?"
        affected_rows = self._execute_update(query, tuple(values))
        return affected_rows > 0

    def update_state(self, job_id: str, state: JobState, progress: Optional[int] = None) -> bool:
        """Update job state and optionally progress"""
        updates = {"state": state}
        if progress is not None:
            updates["progress"] = progress
        return self.update(job_id, updates)

    def update_progress(self, job_id: str, progress: int) -> bool:
        """Update job progress"""
        if not (0 <= progress <= 100):
            raise ValueError("Progress must be between 0 and 100")
        return self.update(job_id, {"progress": progress})

    def delete(self, job_id: str) -> bool:
        """Delete a job and its related renders"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Delete related renders first (foreign key relationship)
            cursor.execute("DELETE FROM renders WHERE job_id = ?", (job_id,))

            # Delete the job
            cursor.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))

            conn.commit()
            return cursor.rowcount > 0

    def list_all(self, limit: Optional[int] = None, offset: Optional[int] = None,
                 state_filter: Optional[JobState] = None) -> List[Job]:
        """List jobs with optional filtering and pagination"""
        query = "SELECT * FROM jobs"
        params = []

        if state_filter:
            query += " WHERE state = ?"
            params.append(state_filter.value)

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        if offset:
            query += " OFFSET ?"
            params.append(offset)

        results = self._execute_query(query, tuple(params))
        return [Job(**result) for result in results]

    def get_active_jobs(self) -> List[Job]:
        """Get jobs that are currently processing or queued"""
        query = """
        SELECT * FROM jobs
        WHERE state IN ('queued', 'processing')
        ORDER BY created_at ASC
        """
        results = self._execute_query(query)
        return [Job(**result) for result in results]

    def get_jobs_by_state(self, state: JobState) -> List[Job]:
        """Get jobs filtered by state"""
        return self.list_all(state_filter=state)

    def count(self, state_filter: Optional[JobState] = None) -> int:
        """Count total jobs or jobs by state"""
        query = "SELECT COUNT(*) as count FROM jobs"
        params = []

        if state_filter:
            query += " WHERE state = ?"
            params.append(state_filter.value)

        result = self._execute_query(query, tuple(params), fetch_one=True)
        return result['count'] if result else 0

    def get_stuck_jobs(self, minutes_ago: int = 30) -> List[Job]:
        """Find jobs that have been processing for too long"""
        cutoff_time = int(time.time()) - (minutes_ago * 60)
        query = """
        SELECT * FROM jobs
        WHERE state = 'processing'
        AND updated_at < ?
        ORDER BY updated_at ASC
        """
        results = self._execute_query(query, (cutoff_time,))
        return [Job(**result) for result in results]

    def get_recent_jobs(self, hours: int = 24) -> List[Job]:
        """Get jobs from the last N hours"""
        cutoff_time = int(time.time()) - (hours * 3600)
        query = """
        SELECT * FROM jobs
        WHERE created_at >= ?
        ORDER BY created_at DESC
        """
        results = self._execute_query(query, (cutoff_time,))
        return [Job(**result) for result in results]

    def get_job_statistics(self) -> Dict[str, any]:
        """Get comprehensive job statistics"""
        query = """
        SELECT
            state,
            COUNT(*) as count,
            AVG(progress) as avg_progress,
            MIN(created_at) as earliest,
            MAX(created_at) as latest
        FROM jobs
        GROUP BY state
        """
        results = self._execute_query(query)

        stats = {}
        for row in results:
            stats[row['state']] = {
                'count': row['count'],
                'avg_progress': round(row['avg_progress'] or 0, 2),
                'earliest': row['earliest'],
                'latest': row['latest']
            }

        return stats