
import json
import logging
import redis.asyncio as redis
from typing import Dict, Any, Optional
from core.config import settings

log = logging.getLogger(__name__)

class RedisQueue:
    def __init__(self):
        self.client = None
        self.queue_key = "genscene:jobs"
        
    async def connect(self):
        try:
            self.client = redis.from_url(settings.redis_url, decode_responses=True)
            await self.client.ping()
            log.info(f"✅ Connected to Redis (Async) at {settings.REDIS_HOST}")
        except Exception as e:
            log.error(f"❌ Failed to connect to Redis: {e}")
            raise

    async def enqueue(self, job_id: str, job_type: str, payload: Dict[str, Any]):
        """Push a job to the queue"""
        if not self.client:
            await self.connect()
            
        message = {
            "job_id": job_id,
            "type": job_type,
            "payload": payload
        }
        # RPUSH adds to the tail
        await self.client.rpush(self.queue_key, json.dumps(message))
        log.info(f"📥 Enqueued job {job_id} ({job_type})")

    async def dequeue(self, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """Blocking pop from the queue"""
        if not self.client:
            await self.connect()
            
        try:
            # BLPOP returns tuple (key, value) or None
            result = await self.client.blpop(self.queue_key, timeout=timeout)
            
            if result:
                queue_name, message_json = result
                try:
                    return json.loads(message_json)
                except json.JSONDecodeError:
                    log.error(f"❌ Failed to decode message from Redis: {message_json}")
                    return None
            return None
        except Exception as e:
             # Redis timeout or connect error
             return None

    async def close(self):
        if self.client:
            await self.client.close()

# Global instance
job_queue = RedisQueue()
