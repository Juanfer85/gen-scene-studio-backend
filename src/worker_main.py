
import asyncio
import logging
import signal
import sys
from typing import Dict, Any

from core.logging import setup_logging
from core.queue import job_queue
from worker.enterprise_manager import enterprise_job_manager, EnterpriseJob

# Configure Logging
log = setup_logging()

async def shutdown(signal, loop):
    """Cleanup tasks tied to the service's shutdown."""
    log.info(f"Received exit signal {signal.name}...")
    
    log.info("Closing Redis connection...")
    await job_queue.close()
    
    log.info("Closing Enterprise Manager...")
    await enterprise_job_manager.close()
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    
    log.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

async def worker_loop():
    """Main worker loop consuming from Redis"""
    log.info("🚀 Worker started. Waiting for jobs in Redis queue...")
    
    # Initialize Manager (DB connection, etc)
    await enterprise_job_manager.initialize()
    
    while True:
        try:
            # Blocking pop with 5s timeout to allow clean shutdown checks
            job_data = await job_queue.dequeue(timeout=5)
            
            if not job_data:
                continue
                
            job_id = job_data.get("job_id")
            job_type = job_data.get("type")
            payload = job_data.get("payload", {})
            
            log.info(f"📥 Received job: {job_id} ({job_type})")
            
            # Reconstruct Job Object
            # EnterpriseJob expects (job_id, job_type, payload)
            job = EnterpriseJob(job_id, job_type, payload)
            
            # Inject into manager's processing pipeline
            # We call the internal dispatcher directly
            # Note: In a cleaner refactor, this would be a public 'handle_job' method
            try:
                # Add to local tracking so manager knows about it (for logging/stats)
                enterprise_job_manager._jobs[job_id] = job
                
                # Dispatch depending on type
                if job_type == "quick_create_full_universe":
                     await enterprise_job_manager._process_quick_create_full_universe("worker-redis", job)
                elif job_type == "compose":
                     await enterprise_job_manager._process_compose("worker-redis", job)
                elif job_type == "tts":
                     await enterprise_job_manager._process_tts("worker-redis", job)
                else:
                    log.error(f"❌ Unknown job type: {job_type}")
                    
                log.info(f"✅ Job {job_id} processed successfully")
                
            except Exception as e:
                log.error(f"❌ Error processing job {job_id}: {e}", exc_info=True)
                # Ideally, move to Dead Letter Queue (DLQ)
            
            # Clean up local memory
            if job_id in enterprise_job_manager._jobs:
                del enterprise_job_manager._jobs[job_id]
                
        except asyncio.CancelledError:
            log.info("Worker loop cancelled")
            break
        except Exception as e:
            log.error(f"Unexpected worker error: {e}")
            await asyncio.sleep(1)

def main():
    loop = asyncio.get_event_loop()
    
    # Signals
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s, loop))
        )
    
    try:
        loop.run_until_complete(worker_loop())
    except KeyboardInterrupt:
        log.info("Keyboard interrupt")
    finally:
        log.info("Worker shutdown complete")

if __name__ == "__main__":
    main()
