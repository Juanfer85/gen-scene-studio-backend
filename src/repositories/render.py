import time
from typing import Dict, List, Optional
from .base import BaseRepository
from models.entities import Render, RenderStatus, RenderQuality

class RenderRepository(BaseRepository[Render]):
    """Repository for Render entities with CRUD operations"""

    def create_table(self) -> None:
        """Create renders table if it doesn't exist"""
        query = """
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
        )
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)

            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_renders_job_id ON renders(job_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_renders_status ON renders(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_renders_hash ON renders(hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_renders_quality ON renders(quality)")
            conn.commit()

    def create(self, render: Render) -> str:
        """Create a new render or update if exists"""
        now = int(time.time())
        query = """
        INSERT INTO renders (job_id, item_id, hash, quality, url, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_id, item_id) DO UPDATE SET
            hash = excluded.hash,
            quality = excluded.quality,
            url = excluded.url,
            status = excluded.status,
            updated_at = excluded.updated_at
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                render.job_id,
                render.item_id,
                render.hash,
                render.quality.value,
                render.url,
                render.status.value,
                render.created_at or now,
                render.updated_at or now
            ))
            conn.commit()
        return f"{render.job_id}:{render.item_id}"

    def get_by_id(self, entity_id: str) -> Optional[Render]:
        """Get a render by its composite ID (job_id:item_id)"""
        job_id, item_id = entity_id.split(':', 1)
        query = "SELECT * FROM renders WHERE job_id = ? AND item_id = ?"
        result = self._execute_query(query, (job_id, item_id), fetch_one=True)
        return Render(**result) if result else None

    def get_by_job_and_item(self, job_id: str, item_id: str) -> Optional[Render]:
        """Get a render by job_id and item_id"""
        query = "SELECT * FROM renders WHERE job_id = ? AND item_id = ?"
        result = self._execute_query(query, (job_id, item_id), fetch_one=True)
        return Render(**result) if result else None

    def update(self, entity_id: str, updates: Dict[str, any]) -> bool:
        """Update a render"""
        job_id, item_id = entity_id.split(':', 1)

        if not updates:
            return False

        # Always update updated_at timestamp
        updates['updated_at'] = int(time.time())

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [job_id, item_id]

        # Convert enum values to strings
        for i, (key, value) in enumerate(updates.items()):
            if isinstance(value, (RenderStatus, RenderQuality)):
                values[i] = value.value

        query = f"UPDATE renders SET {set_clause} WHERE job_id = ? AND item_id = ?"
        affected_rows = self._execute_update(query, tuple(values))
        return affected_rows > 0

    def update_by_job_and_item(self, job_id: str, item_id: str, updates: Dict[str, any]) -> bool:
        """Update a render by job_id and item_id"""
        if not updates:
            return False

        updates['updated_at'] = int(time.time())
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [job_id, item_id]

        # Convert enum values to strings
        for i, (key, value) in enumerate(updates.items()):
            if isinstance(value, (RenderStatus, RenderQuality)):
                values[i] = value.value

        query = f"UPDATE renders SET {set_clause} WHERE job_id = ? AND item_id = ?"
        affected_rows = self._execute_update(query, tuple(values))
        return affected_rows > 0

    def update_status(self, job_id: str, item_id: str, status: RenderStatus) -> bool:
        """Update render status"""
        return self.update_by_job_and_item(job_id, item_id, {"status": status})

    def update_url(self, job_id: str, item_id: str, url: str) -> bool:
        """Update render URL"""
        return self.update_by_job_and_item(job_id, item_id, {"url": url})

    def delete(self, entity_id: str) -> bool:
        """Delete a render"""
        job_id, item_id = entity_id.split(':', 1)
        query = "DELETE FROM renders WHERE job_id = ? AND item_id = ?"
        affected_rows = self._execute_update(query, (job_id, item_id))
        return affected_rows > 0

    def delete_by_job_and_item(self, job_id: str, item_id: str) -> bool:
        """Delete a render by job_id and item_id"""
        query = "DELETE FROM renders WHERE job_id = ? AND item_id = ?"
        affected_rows = self._execute_update(query, (job_id, item_id))
        return affected_rows > 0

    def delete_by_job_id(self, job_id: str) -> int:
        """Delete all renders for a job"""
        query = "DELETE FROM renders WHERE job_id = ?"
        affected_rows = self._execute_update(query, (job_id,))
        return affected_rows

    def list_all(self, limit: Optional[int] = None, offset: Optional[int] = None,
                 status_filter: Optional[RenderStatus] = None,
                 quality_filter: Optional[RenderQuality] = None) -> List[Render]:
        """List renders with optional filtering and pagination"""
        query = "SELECT * FROM renders"
        params = []
        where_clauses = []

        if status_filter:
            where_clauses.append("status = ?")
            params.append(status_filter.value)

        if quality_filter:
            where_clauses.append("quality = ?")
            params.append(quality_filter.value)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        if offset:
            query += " OFFSET ?"
            params.append(offset)

        results = self._execute_query(query, tuple(params))
        return [Render(**result) for result in results]

    def get_by_job_id(self, job_id: str, status_filter: Optional[RenderStatus] = None) -> List[Render]:
        """Get all renders for a specific job"""
        query = "SELECT * FROM renders WHERE job_id = ?"
        params = [job_id]

        if status_filter:
            query += " AND status = ?"
            params.append(status_filter.value)

        query += " ORDER BY item_id"

        results = self._execute_query(query, tuple(params))
        return [Render(**result) for result in results]

    def get_job_outputs(self, job_id: str) -> List[Dict[str, any]]:
        """Get job outputs with simplified format (for API compatibility)"""
        query = """
        SELECT item_id as id, quality, hash, url, status
        FROM renders
        WHERE job_id = ?
        ORDER BY item_id
        """
        return self._execute_query(query, (job_id,))

    def get_by_hash(self, hash_value: str) -> List[Render]:
        """Get all renders with a specific hash"""
        query = "SELECT * FROM renders WHERE hash = ? ORDER BY created_at DESC"
        results = self._execute_query(query, (hash_value,))
        return [Render(**result) for result in results]

    def get_pending_renders(self) -> List[Render]:
        """Get all renders that are pending processing"""
        return self.list_all(status_filter=RenderStatus.PENDING)

    def get_processing_renders(self) -> List[Render]:
        """Get all renders that are currently processing"""
        return self.list_all(status_filter=RenderStatus.PROCESSING)

    def get_completed_renders(self, limit: int = 100) -> List[Render]:
        """Get recently completed renders"""
        return self.list_all(
            status_filter=RenderStatus.COMPLETED,
            limit=limit
        )

    def get_failed_renders(self, limit: int = 50) -> List[Render]:
        """Get recently failed renders"""
        return self.list_all(
            status_filter=RenderStatus.ERROR,
            limit=limit
        )

    def count(self, status_filter: Optional[RenderStatus] = None,
              quality_filter: Optional[RenderQuality] = None) -> int:
        """Count renders with optional filtering"""
        query = "SELECT COUNT(*) as count FROM renders"
        params = []
        where_clauses = []

        if status_filter:
            where_clauses.append("status = ?")
            params.append(status_filter.value)

        if quality_filter:
            where_clauses.append("quality = ?")
            params.append(quality_filter.value)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        result = self._execute_query(query, tuple(params), fetch_one=True)
        return result['count'] if result else 0

    def get_renders_statistics(self) -> Dict[str, any]:
        """Get comprehensive render statistics"""
        query = """
        SELECT
            status,
            quality,
            COUNT(*) as count,
            AVG(CASE WHEN url IS NOT NULL THEN 1 ELSE 0 END) * 100 as completion_rate
        FROM renders
        GROUP BY status, quality
        ORDER BY status, quality
        """
        results = self._execute_query(query)

        stats = {}
        for row in results:
            key = f"{row['status']}_{row['quality']}"
            stats[key] = {
                'count': row['count'],
                'completion_rate': round(row['completion_rate'], 2)
            }

        return stats

    def exists(self, entity_id: str) -> bool:
        """Check if a render exists"""
        job_id, item_id = entity_id.split(':', 1)
        query = "SELECT 1 FROM renders WHERE job_id = ? AND item_id = ?"
        result = self._execute_query(query, (job_id, item_id), fetch_one=True)
        return result is not None

    def exists_by_job_and_item(self, job_id: str, item_id: str) -> bool:
        """Check if a render exists by job_id and item_id"""
        query = "SELECT 1 FROM renders WHERE job_id = ? AND item_id = ?"
        result = self._execute_query(query, (job_id, item_id), fetch_one=True)
        return result is not None

    def get_stuck_renders(self, minutes_ago: int = 60) -> List[Render]:
        """Find renders that have been processing for too long"""
        cutoff_time = int(time.time()) - (minutes_ago * 60)
        query = """
        SELECT * FROM renders
        WHERE status = 'processing'
        AND updated_at < ?
        ORDER BY updated_at ASC
        """
        results = self._execute_query(query, (cutoff_time,))
        return [Render(**result) for result in results]

    def get_render_count_by_job(self) -> Dict[str, int]:
        """Get render count for each job"""
        query = """
        SELECT job_id, COUNT(*) as render_count
        FROM renders
        GROUP BY job_id
        ORDER BY render_count DESC
        """
        results = self._execute_query(query)
        return {row['job_id']: row['render_count'] for row in results}