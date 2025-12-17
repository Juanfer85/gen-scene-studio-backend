"""
Redis-based caching system for high-performance operations
"""
import json
import pickle
import asyncio
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio import ConnectionPool
import logging
import hashlib
import time

from core.config import settings

log = logging.getLogger(__name__)

class CacheError(Exception):
    """Base exception for cache operations"""
    pass

class CacheConnectionError(CacheError):
    """Exception for cache connection issues"""
    pass

class CacheSerializationError(CacheError):
    """Exception for serialization issues"""
    pass

class CacheManager:
    """
    High-performance Redis cache manager with serialization,
    compression, and intelligent key management
    """

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._redis: Optional[redis.Redis] = None
        self._default_ttl = settings.REDIS_CACHE_TTL
        self._prefix = "genscene_cache:"
        self._compression_enabled = True
        self._serializer = "pickle"  # or "json"
        self._max_retries = 3
        self._retry_delay = 1

    async def initialize(self):
        """Initialize Redis connection pool"""
        try:
            self._pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                health_check_interval=30
            )

            self._redis = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._redis.ping()
            log.info("✅ Redis cache initialized successfully")

        except Exception as e:
            log.error(f"❌ Failed to initialize Redis cache: {e}")
            raise CacheConnectionError(f"Cannot connect to Redis: {e}")

    async def close(self):
        """Close Redis connections"""
        if self._pool:
            await self._pool.disconnect()
            log.info("🔌 Redis cache connections closed")

    def _make_key(self, key: str, namespace: str = "default") -> str:
        """Create a namespaced cache key with hash for long keys"""
        # If key is too long, hash it
        if len(key) > 100:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            return f"{self._prefix}{namespace}:{key_hash[:8]}:{key_hash[-8:]}"

        return f"{self._prefix}{namespace}:{key}"

    def _serialize(self, data: Any) -> bytes:
        """Serialize data for storage"""
        try:
            if self._serializer == "json":
                if isinstance(data, (dict, list, str, int, float, bool)):
                    return json.dumps(data).encode('utf-8')
                else:
                    raise CacheSerializationError("JSON serialization requires JSON-serializable data")
            else:
                return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            raise CacheSerializationError(f"Failed to serialize data: {e}")

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from storage"""
        try:
            if self._serializer == "json":
                return json.loads(data.decode('utf-8'))
            else:
                return pickle.loads(data)
        except Exception as e:
            raise CacheSerializationError(f"Failed to deserialize data: {e}")

    async def _execute_with_retry(self, operation, *args, **kwargs):
        """Execute Redis operation with retry logic"""
        last_exception = None

        for attempt in range(self._max_retries):
            try:
                return await operation(*args, **kwargs)
            except (redis.ConnectionError, redis.TimeoutError) as e:
                last_exception = e
                log.warning(f"⚠️ Redis operation failed (attempt {attempt + 1}): {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))
            except Exception as e:
                # Don't retry on non-connection errors
                raise CacheError(f"Redis operation failed: {e}")

        raise CacheConnectionError(f"Redis operation failed after {self._max_retries} retries: {last_exception}")

    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get value from cache"""
        if not self._redis:
            raise CacheConnectionError("Cache not initialized")

        cache_key = self._make_key(key, namespace)

        try:
            data = await self._execute_with_retry(self._redis.get, cache_key)
            if data is None:
                return None

            return self._deserialize(data)
        except CacheError:
            raise
        except Exception as e:
            log.error(f"❌ Cache get error for key {cache_key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "default"
    ) -> bool:
        """Set value in cache with optional TTL"""
        if not self._redis:
            raise CacheConnectionError("Cache not initialized")

        cache_key = self._make_key(key, namespace)
        ttl = ttl or self._default_ttl

        try:
            serialized_data = self._serialize(value)
            success = await self._execute_with_retry(
                self._redis.setex, cache_key, ttl, serialized_data
            )
            return bool(success)
        except CacheError:
            raise
        except Exception as e:
            log.error(f"❌ Cache set error for key {cache_key}: {e}")
            return False

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete key from cache"""
        if not self._redis:
            raise CacheConnectionError("Cache not initialized")

        cache_key = self._make_key(key, namespace)

        try:
            result = await self._execute_with_retry(self._redis.delete, cache_key)
            return result > 0
        except CacheError:
            raise
        except Exception as e:
            log.error(f"❌ Cache delete error for key {cache_key}: {e}")
            return False

    async def delete_pattern(self, pattern: str, namespace: str = "default") -> int:
        """Delete keys matching pattern"""
        if not self._redis:
            raise CacheConnectionError("Cache not initialized")

        cache_pattern = self._make_key(pattern.replace('*', '*'), namespace)
        cache_pattern = cache_pattern.replace('*', '*')

        try:
            keys = await self._execute_with_retry(self._redis.keys, cache_pattern)
            if keys:
                return await self._execute_with_retry(self._redis.delete, *keys)
            return 0
        except CacheError:
            raise
        except Exception as e:
            log.error(f"❌ Cache delete pattern error for {cache_pattern}: {e}")
            return 0

    async def exists(self, key: str, namespace: str = "default") -> bool:
        """Check if key exists in cache"""
        if not self._redis:
            raise CacheConnectionError("Cache not initialized")

        cache_key = self._make_key(key, namespace)

        try:
            result = await self._execute_with_retry(self._redis.exists, cache_key)
            return result > 0
        except CacheError:
            raise
        except Exception as e:
            log.error(f"❌ Cache exists error for key {cache_key}: {e}")
            return False

    async def get_ttl(self, key: str, namespace: str = "default") -> Optional[int]:
        """Get TTL for key (returns seconds remaining or None if key doesn't exist)"""
        if not self._redis:
            raise CacheConnectionError("Cache not initialized")

        cache_key = self._make_key(key, namespace)

        try:
            ttl = await self._execute_with_retry(self._redis.ttl, cache_key)
            return ttl if ttl > 0 else None
        except CacheError:
            raise
        except Exception as e:
            log.error(f"❌ Cache TTL error for key {cache_key}: {e}")
            return None

    async def get_many(self, keys: List[str], namespace: str = "default") -> Dict[str, Any]:
        """Get multiple values from cache"""
        if not self._redis:
            raise CacheConnectionError("Cache not initialized")

        if not keys:
            return {}

        cache_keys = [self._make_key(key, namespace) for key in keys]

        try:
            values = await self._execute_with_retry(self._redis.mget, cache_keys)
            result = {}

            for i, (key, value) in enumerate(zip(keys, values)):
                if value is not None:
                    try:
                        result[key] = self._deserialize(value)
                    except CacheSerializationError:
                        log.warning(f"⚠️ Failed to deserialize cached value for key {key}")
                        # Delete corrupted key
                        await self.delete(key, namespace)

            return result
        except CacheError:
            raise
        except Exception as e:
            log.error(f"❌ Cache get_many error: {e}")
            return {}

    async def set_many(
        self,
        data: Dict[str, Any],
        ttl: Optional[int] = None,
        namespace: str = "default"
    ) -> bool:
        """Set multiple values in cache (uses pipeline for performance)"""
        if not self._redis:
            raise CacheConnectionError("Cache not initialized")

        if not data:
            return True

        ttl = ttl or self._default_ttl

        try:
            pipeline = self._redis.pipeline()

            for key, value in data.items():
                cache_key = self._make_key(key, namespace)
                serialized_data = self._serialize(value)
                pipeline.setex(cache_key, ttl, serialized_data)

            await self._execute_with_retry(pipeline.execute)
            return True
        except CacheError:
            raise
        except Exception as e:
            log.error(f"❌ Cache set_many error: {e}")
            return False

    async def increment(self, key: str, amount: int = 1, namespace: str = "counters") -> int:
        """Increment a counter in cache"""
        if not self._redis:
            raise CacheConnectionError("Cache not initialized")

        cache_key = self._make_key(key, namespace)

        try:
            result = await self._execute_with_retry(self._redis.incrby, cache_key, amount)
            # Set TTL if it's a new key
            if await self._redis.ttl(cache_key) == -1:
                await self._execute_with_retry(self._redis.expire, cache_key, self._default_ttl)
            return result
        except CacheError:
            raise
        except Exception as e:
            log.error(f"❌ Cache increment error for key {cache_key}: {e}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        if not self._redis:
            raise CacheConnectionError("Cache not initialized")

        try:
            info = await self._execute_with_retry(self._redis.info)

            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "used_memory_peak": info.get("used_memory_peak_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) /
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                ) * 100,
                "expired_keys": info.get("expired_keys", 0),
                "evicted_keys": info.get("evicted_keys", 0)
            }
        except CacheError:
            raise
        except Exception as e:
            log.error(f"❌ Cache stats error: {e}")
            return {}

    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace"""
        if not self._redis:
            raise CacheConnectionError("Cache not initialized")

        pattern = f"{self._prefix}{namespace}:*"

        try:
            keys = await self._execute_with_retry(self._redis.keys, pattern)
            if keys:
                return await self._execute_with_retry(self._redis.delete, *keys)
            return 0
        except CacheError:
            raise
        except Exception as e:
            log.error(f"❌ Clear namespace error for {namespace}: {e}")
            return 0

# Global cache manager instance
cache_manager = CacheManager()

# Decorator for caching function results
def cache_result(
    key_template: str,
    ttl: Optional[int] = None,
    namespace: str = "functions",
    serialize_args: bool = True
):
    """
    Decorator to cache function results

    Args:
        key_template: Template for cache key, can use function arguments
        ttl: Time to live in seconds
        namespace: Cache namespace
        serialize_args: Whether to include arguments in cache key
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            if not cache_manager._redis:
                return await func(*args, **kwargs)

            # Generate cache key
            if serialize_args:
                import inspect
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                args_str = "_".join(str(v) for v in bound_args.arguments.values())
                cache_key = f"{func.__name__}:{hashlib.md5(args_str.encode()).hexdigest()[:8]}"
            else:
                cache_key = key_template

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key, namespace)
            if cached_result is not None:
                log.debug(f"🎯 Cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl, namespace)
            log.debug(f"💾 Cached result for {func.__name__}")

            return result

        def sync_wrapper(*args, **kwargs):
            if not cache_manager._redis:
                return func(*args, **kwargs)

            # For synchronous functions, run async wrapper in event loop
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(async_wrapper(*args, **kwargs))
            except RuntimeError:
                # No event loop running, create one
                return asyncio.run(async_wrapper(*args, **kwargs))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator