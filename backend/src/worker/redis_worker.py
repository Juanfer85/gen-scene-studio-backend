"""
Redis-based high-performance worker system with persistence,
retry logic, and concurrent processing
"""
import asyncio
import json
import time
import uuid
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
from dataclasses import dataclass, asdict
import logging

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from core.config import settings
from core.cache import cache_manager, CacheError
from core.logging import setup_logging

log = setup_logging()

class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class JobPriority(int, Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Job:
    """Job data structure"""
    job_id: str
    job_type: str
    payload: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3
    current_retry: int = 0
    timeout: int = 300  # seconds
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: JobStatus = JobStatus.QUEUED
    error_message: Optional[str] = None
    progress: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create Job from dictionary"""
        data = data.copy()
        # Convert string timestamps back to datetime objects
        for field in ['created_at', 'started_at', 'completed_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])

        # Convert string enums back to enums
        if data.get('status'):
            data['status'] = JobStatus(data['status'])
        if data.get('priority'):
            data['priority'] = JobPriority(data['priority'])

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Job to dictionary"""
        result = asdict(self)
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'started_at', 'completed_at']:
            if result.get(field):
                result[field] = result[field].isoformat()

        # Convert enums to strings
        result['status'] = self.status.value
        result['priority'] = self.priority.value

        return result

class WorkerError(Exception):
    """Base exception for worker operations"""
    pass

class WorkerConnectionError(WorkerError):
    """Exception for worker connection issues"""
    pass

class JobProcessingError(WorkerError):
    """Exception for job processing failures"""
    pass

class RedisWorkerManager:
    """
    High-performance worker manager using Redis queues
    with persistence, retry logic, and concurrent processing
    """

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._redis: Optional[redis.Redis] = None
        self._running = False
        self._workers: List[asyncio.Task] = []
        self._job_handlers: Dict[str, Callable] = {}
        self._queue_name = "genscene_jobs"
        self._processing_queue_name = "genscene_processing"
        self._failed_queue_name = "genscene_failed"
        self._stats_queue_name = "genscene_stats"
        self._lock_name = "genscene_worker_lock"

    async def initialize(self):
        """Initialize Redis connection and setup queues"""
        try:
            self._pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_timeout=30,
                socket_connect_timeout=10,
                health_check_interval=30
            )

            self._redis = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._redis.ping()
            log.info("✅ Redis worker manager initialized")

            # Initialize cache manager if not already done
            if not cache_manager._redis:
                await cache_manager.initialize()

        except Exception as e:
            log.error(f"❌ Failed to initialize Redis worker manager: {e}")
            raise WorkerConnectionError(f"Cannot connect to Redis: {e}")

    async def close(self):
        """Close worker manager and cleanup"""
        self._running = False

        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass

        # Close connections
        if self._pool:
            await self._pool.disconnect()
        log.info("🔌 Redis worker manager closed")

    def register_handler(self, job_type: str, handler: Callable):
        """Register a handler function for a job type"""
        self._job_handlers[job_type] = handler
        log.info(f"📝 Registered handler for job type: {job_type}")

    async def start_workers(self, num_workers: Optional[int] = None):
        """Start worker processes"""
        if num_workers is None:
            num_workers = settings.WORKER_CONCURRENCY

        if self._running:
            log.warning("⚠️ Workers are already running")
            return

        self._running = True

        # Start worker tasks
        for i in range(num_workers):
            worker_task = asyncio.create_task(
                self._worker_loop(f"worker-{i}"),
                name=f"worker-{i}"
            )
            self._workers.append(worker_task)

        log.info(f"🚀 Started {num_workers} worker processes")

    async def _worker_loop(self, worker_id: str):
        """Main worker processing loop"""
        log.info(f"🤖 Worker {worker_id} started")

        while self._running:
            try:
                # Wait for job with timeout
                job_data = await self._redis.brpop(
                    self._queue_name,
                    timeout=settings.WORKER_POLL_INTERVAL
                )

                if not job_data:
                    continue

                # Parse job data
                _, job_json = job_data
                job_dict = json.loads(job_json.decode('utf-8'))
                job = Job.from_dict(job_dict)

                log.info(f"📋 Worker {worker_id} processing job: {job.job_id} ({job.job_type})")

                # Process job
                await self._process_job(worker_id, job)

            except asyncio.CancelledError:
                log.info(f"🛑 Worker {worker_id} cancelled")
                break
            except Exception as e:
                log.error(f"❌ Worker {worker_id} error: {e}")
                traceback.print_exc()
                await asyncio.sleep(1)  # Brief pause before retry

    async def _process_job(self, worker_id: str, job: Job):
        """Process a single job with error handling and retries"""
        processing_key = f"{self._processing_queue_name}:{job.job_id}"

        try:
            # Mark job as processing
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            job.progress = 0

            # Add to processing queue with timeout
            await self._redis.setex(
                processing_key,
                job.timeout,
                json.dumps(job.to_dict())
            )

            # Update job status in cache
            await cache_manager.set(f"job:{job.job_id}", job.to_dict(), namespace="jobs")

            # Check if handler exists
            handler = self._job_handlers.get(job.job_type)
            if not handler:
                raise JobProcessingError(f"No handler registered for job type: {job.job_type}")

            # Execute job handler with timeout
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await asyncio.wait_for(
                        handler(job),
                        timeout=job.timeout
                    )
                else:
                    # For sync handlers, run in thread pool
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, handler, job),
                        timeout=job.timeout
                    )

                # Mark job as completed
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.progress = 100
                job.metadata['result'] = result

                log.info(f"✅ Worker {worker_id} completed job: {job.job_id}")

            except asyncio.TimeoutError:
                job.status = JobStatus.FAILED
                job.error_message = f"Job timed out after {job.timeout} seconds"
                log.warning(f"⏱️ Job {job.job_id} timed out")

            except Exception as e:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                log.error(f"❌ Job {job.job_id} failed: {e}")
                traceback.print_exc()

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = f"Worker error: {str(e)}"
            log.error(f"❌ Critical error processing job {job.job_id}: {e}")

        finally:
            # Remove from processing queue
            await self._redis.delete(processing_key)

            # Handle job completion/failure
            await self._finalize_job(job)

    async def _finalize_job(self, job: Job):
        """Finalize job processing (handle retries, cleanup, etc.)"""
        try:
            # Update job status in cache
            await cache_manager.set(f"job:{job.job_id}", job.to_dict(), namespace="jobs")

            # Record statistics
            await self._record_job_stats(job)

            if job.status == JobStatus.FAILED and job.current_retry < job.max_retries:
                # Retry job with exponential backoff
                retry_job = Job(
                    job_id=job.job_id,
                    job_type=job.job_type,
                    payload=job.payload,
                    priority=job.priority,
                    max_retries=job.max_retries,
                    current_retry=job.current_retry + 1,
                    timeout=job.timeout,
                    created_at=job.created_at,
                    metadata=job.metadata.copy()
                )

                retry_job.status = JobStatus.RETRYING

                # Calculate retry delay (exponential backoff)
                retry_delay = min(
                    settings.WORKER_RETRY_DELAY * (2 ** retry_job.current_retry),
                    300  # Max 5 minutes
                )

                # Schedule retry
                await self._redis.zadd(
                    f"{self._queue_name}_retry",
                    {json.dumps(retry_job.to_dict()): time.time() + retry_delay}
                )

                log.info(f"🔄 Job {job.job_id} scheduled for retry #{retry_job.current_retry} in {retry_delay}s")

            elif job.status == JobStatus.FAILED:
                # Move to failed queue
                await self._redis.lpush(
                    self._failed_queue_name,
                    json.dumps(job.to_dict())
                )

                log.error(f"💀 Job {job.job_id} moved to failed queue after {job.max_retries} retries")

        except Exception as e:
            log.error(f"❌ Error finalizing job {job.job_id}: {e}")

    async def _record_job_stats(self, job: Job):
        """Record job processing statistics"""
        try:
            stats = {
                'job_id': job.job_id,
                'job_type': job.job_type,
                'status': job.status.value,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'duration': None,
                'retries': job.current_retry
            }

            if job.started_at and job.completed_at:
                stats['duration'] = (job.completed_at - job.started_at).total_seconds()

            # Add to stats queue
            await self._redis.lpush(
                self._stats_queue_name,
                json.dumps(stats)
            )

            # Trim stats queue to prevent memory issues
            await self._redis.ltrim(self._stats_queue_name, 0, 10000)

            # Update counters
            counter_key = f"{self._stats_queue_name}:counters"
            await self._redis.hincrby(counter_key, f"total_{job.job_type}", 1)
            await self._redis.hincrby(counter_key, f"total_{job.status.value}", 1)

        except Exception as e:
            log.error(f"❌ Error recording job stats: {e}")

    async def enqueue_job(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None
    ) -> str:
        """Enqueue a new job"""
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type=job_type,
            payload=payload,
            priority=priority,
            timeout=timeout or settings.WORKER_TIMEOUT,
            max_retries=max_retries or settings.WORKER_MAX_RETRIES
        )

        job_data = json.dumps(job.to_dict())

        # Add to priority queue
        queue_key = f"{self._queue_name}:{priority.value}"
        await self._redis.lpush(queue_key, job_data)

        # Cache job status
        await cache_manager.set(f"job:{job.job_id}", job.to_dict(), namespace="jobs")

        log.info(f"📝 Enqueued job {job.job_id} of type {job_type} with priority {priority.value}")

        return job_id

    async def get_job_status(self, job_id: str) -> Optional[Job]:
        """Get current job status"""
        try:
            job_data = await cache_manager.get(f"job:{job_id}", namespace="jobs")
            if job_data:
                return Job.from_dict(job_data)

            # Check if job is in processing queue
            processing_key = f"{self._processing_queue_name}:{job_id}"
            processing_data = await self._redis.get(processing_key)
            if processing_data:
                return Job.from_dict(json.loads(processing_data.decode('utf-8')))

            return None
        except Exception as e:
            log.error(f"❌ Error getting job status {job_id}: {e}")
            return None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job if it hasn't started processing"""
        try:
            job = await self.get_job_status(job_id)
            if not job:
                return False

            if job.status == JobStatus.QUEUED:
                job.status = JobStatus.CANCELLED
                await cache_manager.set(f"job:{job_id}", job.to_dict(), namespace="jobs")
                log.info(f"🚫 Cancelled job {job_id}")
                return True
            else:
                log.warning(f"⚠️ Cannot cancel job {job_id} - status: {job.status}")
                return False

        except Exception as e:
            log.error(f"❌ Error cancelling job {job_id}: {e}")
            return False

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            stats = {
                'queued': {},
                'processing': 0,
                'failed': 0,
                'retry': 0
            }

            # Count queued jobs by priority
            for priority in JobPriority:
                queue_key = f"{self._queue_name}:{priority.value}"
                count = await self._redis.llen(queue_key)
                stats['queued'][priority.name.lower()] = count

            # Count processing jobs
            processing_pattern = f"{self._processing_queue_name}:*"
            processing_keys = await self._redis.keys(processing_pattern)
            stats['processing'] = len(processing_keys)

            # Count failed jobs
            stats['failed'] = await self._redis.llen(self._failed_queue_name)

            # Count retry jobs
            retry_queue_key = f"{self._queue_name}_retry"
            stats['retry'] = await self._redis.zcard(retry_queue_key)

            return stats

        except Exception as e:
            log.error(f"❌ Error getting queue stats: {e}")
            return {}

    async def process_retry_queue(self):
        """Process retry queue for jobs that are ready to be retried"""
        try:
            retry_queue_key = f"{self._queue_name}_retry"
            current_time = time.time()

            # Get jobs ready for retry
            retry_jobs = await self._redis.zrangebyscore(
                retry_queue_key,
                0,
                current_time,
                withscores=True
            )

            for job_json, retry_time in retry_jobs:
                job_dict = json.loads(job_json.decode('utf-8'))
                job = Job.from_dict(job_dict)

                # Re-queue the job
                queue_key = f"{self._queue_name}:{job.priority.value}"
                await self._redis.lpush(queue_key, json.dumps(job.to_dict()))

                # Remove from retry queue
                await self._redis.zrem(retry_queue_key, job_json)

                log.info(f"🔄 Re-queued job {job.job_id} for retry")

        except Exception as e:
            log.error(f"❌ Error processing retry queue: {e}")

    async def cleanup_old_jobs(self, days: int = 7):
        """Clean up old completed/failed jobs from cache"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)

            # Get all job keys from cache
            job_keys = await cache_manager._redis.keys(f"{cache_manager._prefix}jobs:job:*")

            cleaned = 0
            for key in job_keys:
                try:
                    job_data = await cache_manager._redis.get(key)
                    if job_data:
                        job_dict = json.loads(job_data.decode('utf-8'))
                        job = Job.from_dict(job_dict)

                        if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and
                            job.created_at < cutoff_time):
                            await cache_manager._redis.delete(key)
                            cleaned += 1
                except Exception:
                    continue

            log.info(f"🧹 Cleaned up {cleaned} old jobs from cache")

        except Exception as e:
            log.error(f"❌ Error cleaning up old jobs: {e}")

# Global worker manager instance
worker_manager = RedisWorkerManager()

# Decorator for job handlers
def job_handler(job_type: str):
    """Decorator to register a function as a job handler"""
    def decorator(func):
        worker_manager.register_handler(job_type, func)
        return func
    return decorator