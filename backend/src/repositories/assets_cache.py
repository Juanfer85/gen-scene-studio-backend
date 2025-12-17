import time
from typing import Dict, List, Optional
from .base import BaseRepository
from models.entities import AssetsCache

class AssetsCacheRepository(BaseRepository[AssetsCache]):
    """Repository for cached assets with TTL and cleanup functionality"""

    def create_table(self) -> None:
        """Create assets_cache table if it doesn't exist"""
        query = """
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
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)

            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_cache_created_at ON assets_cache(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_cache_expires_at ON assets_cache(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_cache_last_accessed ON assets_cache(last_accessed)")
            conn.commit()

    def create(self, asset: AssetsCache, ttl_hours: int = 24) -> str:
        """Create a new cached asset with optional TTL"""
        now = int(time.time())
        expires_at = now + (ttl_hours * 3600)

        query = """
        INSERT OR REPLACE INTO assets_cache
        (hash, url, created_at, expires_at, last_accessed)
        VALUES (?, ?, ?, ?, ?)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                asset.hash,
                asset.url,
                asset.created_at or now,
                expires_at,
                now
            ))
            conn.commit()
        return asset.hash

    def get_by_id(self, hash_value: str) -> Optional[AssetsCache]:
        """Get a cached asset by hash and update access tracking"""
        now = int(time.time())

        # First check if expired
        if self._is_expired(hash_value, now):
            return None

        query = """
        SELECT * FROM assets_cache
        WHERE hash = ? AND (expires_at IS NULL OR expires_at > ?)
        """
        result = self._execute_query(query, (hash_value, now), fetch_one=True)

        if result:
            # Update access tracking
            self._update_access_stats(hash_value, now)
            return AssetsCache(**result)

        return None

    def update(self, hash_value: str, updates: Dict[str, any]) -> bool:
        """Update cached asset"""
        if not updates:
            return False

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [hash_value]

        query = f"UPDATE assets_cache SET {set_clause} WHERE hash = ?"
        affected_rows = self._execute_update(query, tuple(values))
        return affected_rows > 0

    def update_url(self, hash_value: str, url: str) -> bool:
        """Update cached asset URL"""
        return self.update(hash_value, {"url": url, "last_accessed": int(time.time())})

    def update_expires(self, hash_value: str, ttl_hours: int = 24) -> bool:
        """Update asset expiration time"""
        now = int(time.time())
        expires_at = now + (ttl_hours * 3600)
        return self.update(hash_value, {"expires_at": expires_at})

    def delete(self, hash_value: str) -> bool:
        """Delete a cached asset"""
        query = "DELETE FROM assets_cache WHERE hash = ?"
        affected_rows = self._execute_update(query, (hash_value,))
        return affected_rows > 0

    def delete_expired(self, older_than_hours: int = 24) -> int:
        """Delete all expired assets older than specified hours"""
        cutoff_time = int(time.time()) - (older_than_hours * 3600)
        query = "DELETE FROM assets_cache WHERE (expires_at IS NOT NULL AND expires_at < ?) OR created_at < ?"
        affected_rows = self._execute_update(query, (cutoff_time, cutoff_time))
        return affected_rows

    def delete_by_url_pattern(self, url_pattern: str) -> int:
        """Delete assets matching URL pattern"""
        query = "DELETE FROM assets_cache WHERE url LIKE ?"
        affected_rows = self._execute_update(query, (f"%{url_pattern}%",))
        return affected_rows

    def list_all(self, limit: Optional[int] = None, offset: Optional[int] = None,
                 include_expired: bool = False) -> List[AssetsCache]:
        """List all cached assets with optional pagination"""
        now = int(time.time())
        query = "SELECT * FROM assets_cache"
        params = []

        if not include_expired:
            query += " WHERE (expires_at IS NULL OR expires_at > ?)"
            params.append(now)

        query += " ORDER BY last_accessed DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        if offset:
            query += " OFFSET ?"
            params.append(offset)

        results = self._execute_query(query, tuple(params))
        return [AssetsCache(**result) for result in results]

    def get_recently_used(self, hours: int = 24, limit: int = 100) -> List[AssetsCache]:
        """Get recently used assets"""
        cutoff_time = int(time.time()) - (hours * 3600)
        now = int(time.time())

        query = """
        SELECT * FROM assets_cache
        WHERE last_accessed >= ?
        AND (expires_at IS NULL OR expires_at > ?)
        ORDER BY last_accessed DESC
        LIMIT ?
        """
        results = self._execute_query(query, (cutoff_time, now, limit))
        return [AssetsCache(**result) for result in results]

    def get_most_used(self, limit: int = 50) -> List[AssetsCache]:
        """Get most frequently accessed assets"""
        now = int(time.time())
        query = """
        SELECT * FROM assets_cache
        WHERE (expires_at IS NULL OR expires_at > ?)
        ORDER BY access_count DESC, last_accessed DESC
        LIMIT ?
        """
        results = self._execute_query(query, (now, limit))
        return [AssetsCache(**result) for result in results]

    def get_largest(self, limit: int = 50) -> List[AssetsCache]:
        """Get largest cached assets by size"""
        now = int(time.time())
        query = """
        SELECT * FROM assets_cache
        WHERE size IS NOT NULL
        AND (expires_at IS NULL OR expires_at > ?)
        ORDER BY size DESC
        LIMIT ?
        """
        results = self._execute_query(query, (now, limit))
        return [AssetsCache(**result) for result in results]

    def count(self, include_expired: bool = False) -> int:
        """Count all cached assets"""
        query = "SELECT COUNT(*) as count FROM assets_cache"

        if not include_expired:
            now = int(time.time())
            query += " WHERE (expires_at IS NULL OR expires_at > ?)"
            result = self._execute_query(query, (now,), fetch_one=True)
        else:
            result = self._execute_query(query, fetch_one=True)

        return result['count'] if result else 0

    def get_cache_statistics(self) -> Dict[str, any]:
        """Get comprehensive cache statistics"""
        now = int(time.time())

        # Overall stats
        overall_query = """
        SELECT
            COUNT(*) as total_assets,
            COUNT(CASE WHEN size IS NOT NULL THEN 1 END) as assets_with_size,
            SUM(CASE WHEN size IS NOT NULL THEN size ELSE 0 END) as total_size,
            AVG(access_count) as avg_access_count,
            MAX(access_count) as max_access_count,
            COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at > ? THEN 1 END) as non_expired,
            COUNT(CASE WHEN expires_at IS NULL OR expires_at <= ? THEN 1 END) as expired
        FROM assets_cache
        """
        overall_stats = self._execute_query(overall_query, (now, now), fetch_one=True)

        # Access distribution
        access_query = """
        SELECT
            CASE
                WHEN access_count = 0 THEN 'never'
                WHEN access_count <= 5 THEN 'rare'
                WHEN access_count <= 20 THEN 'occasional'
                ELSE 'frequent'
            END as access_category,
            COUNT(*) as count
        FROM assets_cache
        GROUP BY access_category
        """
        access_stats = self._execute_query(access_query)

        # Age distribution
        age_query = """
        SELECT
            CASE
                WHEN created_at >= ? THEN 'last_hour'
                WHEN created_at >= ? THEN 'last_day'
                WHEN created_at >= ? THEN 'last_week'
                WHEN created_at >= ? THEN 'last_month'
                ELSE 'older'
            END as age_category,
            COUNT(*) as count
        FROM assets_cache
        GROUP BY age_category
        """
        now = int(time.time())
        hour_ago = now - 3600
        day_ago = now - 86400
        week_ago = now - 604800
        month_ago = now - 2592000

        age_stats = self._execute_query(age_query, (hour_ago, day_ago, week_ago, month_ago))

        return {
            'overall': overall_stats or {},
            'access_distribution': {row['access_category']: row['count'] for row in access_stats},
            'age_distribution': {row['age_category']: row['count'] for row in age_stats}
        }

    def _is_expired(self, hash_value: str, now: int) -> bool:
        """Check if an asset is expired"""
        query = "SELECT expires_at FROM assets_cache WHERE hash = ?"
        result = self._execute_query(query, (hash_value,), fetch_one=True)
        return result and result['expires_at'] and result['expires_at'] <= now

    def _update_access_stats(self, hash_value: str, now: int) -> None:
        """Update access statistics for an asset"""
        query = """
        UPDATE assets_cache
        SET access_count = access_count + 1, last_accessed = ?
        WHERE hash = ?
        """
        self._execute_update(query, (now, hash_value))

    def exists(self, hash_value: str) -> bool:
        """Check if an asset exists (including expired)"""
        query = "SELECT 1 FROM assets_cache WHERE hash = ?"
        result = self._execute_query(query, (hash_value,), fetch_one=True)
        return result is not None

    def exists_fresh(self, hash_value: str) -> bool:
        """Check if a non-expired asset exists"""
        now = int(time.time())
        query = """
        SELECT 1 FROM assets_cache
        WHERE hash = ? AND (expires_at IS NULL OR expires_at > ?)
        """
        result = self._execute_query(query, (hash_value, now), fetch_one=True)
        return result is not None

    def get_by_url(self, url: str) -> Optional[AssetsCache]:
        """Get cached asset by URL"""
        now = int(time.time())
        query = """
        SELECT * FROM assets_cache
        WHERE url = ? AND (expires_at IS NULL OR expires_at > ?)
        """
        result = self._execute_query(query, (url, now), fetch_one=True)
        return AssetsCache(**result) if result else None

    def get_expired_assets(self, limit: int = 1000) -> List[AssetsCache]:
        """Get expired assets for cleanup"""
        now = int(time.time())
        query = """
        SELECT * FROM assets_cache
        WHERE expires_at IS NOT NULL AND expires_at <= ?
        ORDER BY expires_at ASC
        LIMIT ?
        """
        results = self._execute_query(query, (now, limit))
        return [AssetsCache(**result) for result in results]

    def get_old_unused_assets(self, days_unused: int = 30, limit: int = 1000) -> List[AssetsCache]:
        """Get old assets that haven't been accessed recently"""
        cutoff_time = int(time.time()) - (days_unused * 86400)
        now = int(time.time())

        query = """
        SELECT * FROM assets_cache
        WHERE last_accessed <= ?
        AND (expires_at IS NULL OR expires_at > ?)
        ORDER BY last_accessed ASC
        LIMIT ?
        """
        results = self._execute_query(query, (cutoff_time, now, limit))
        return [AssetsCache(**result) for result in results]

    def cleanup_expired(self, dry_run: bool = False) -> Dict[str, int]:
        """Perform cleanup of expired and old assets"""
        stats = {
            'expired_deleted': 0,
            'old_unused_deleted': 0,
            'total_freed_size': 0
        }

        if dry_run:
            # Just count what would be deleted
            expired = self.get_expired_assets(limit=10000)
            old_unused = self.get_old_unused_assets(limit=10000)

            stats['expired_deleted'] = len(expired)
            stats['old_unused_deleted'] = len(old_unused)

            # Calculate total size (if size info available)
            for asset in expired + old_unused:
                if hasattr(asset, 'size') and asset.size:
                    stats['total_freed_size'] += asset.size
        else:
            # Actually delete
            stats['expired_deleted'] = self.delete_expired(older_than_hours=24)
            stats['old_unused_deleted'] = len(self.get_old_unused_assets(days_unused=30))

            # Delete old unused assets
            for asset in self.get_old_unused_assets(days_unused=30, limit=1000):
                if self.delete(asset.hash):
                    if hasattr(asset, 'size') and asset.size:
                        stats['total_freed_size'] += asset.size

        return stats

    def optimize_cache(self, target_size_mb: int = 1000, dry_run: bool = False) -> Dict[str, int]:
        """Optimize cache by removing least recently used items to reach target size"""
        # Get current cache size
        current_stats = self.get_cache_statistics()
        current_size_bytes = current_stats['overall'].get('total_size', 0)
        target_size_bytes = target_size_mb * 1024 * 1024

        if current_size_bytes <= target_size_bytes:
            return {'deleted_count': 0, 'freed_bytes': 0}

        # Get assets sorted by last access time (oldest first)
        query = """
        SELECT hash, size, last_accessed
        FROM assets_cache
        WHERE (expires_at IS NULL OR expires_at > ?)
        ORDER BY last_accessed ASC
        """
        now = int(time.time())
        assets = self._execute_query(query, (now,))

        deleted_count = 0
        freed_bytes = 0

        for asset in assets:
            if current_size_bytes <= target_size_bytes:
                break

            if dry_run:
                deleted_count += 1
                freed_bytes += asset['size'] or 0
                current_size_bytes -= asset['size'] or 0
            else:
                if self.delete(asset['hash']):
                    deleted_count += 1
                    freed_bytes += asset['size'] or 0
                    current_size_bytes -= asset['size'] or 0

        return {'deleted_count': deleted_count, 'freed_bytes': freed_bytes}