import asyncio
import json
import os
import time
import uuid
import subprocess
import hmac
import hashlib
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from datetime import datetime

# Import refactored modules
from core.config import settings
from core.logging import setup_logging
from repositories.connection_manager import get_database_manager, DatabaseManager
from repositories.job import JobRepository
from repositories.render import RenderRepository
from repositories.assets_cache import AssetsCacheRepository
from models.entities import Job, JobState, Render, RenderStatus, RenderQuality, AssetsCache
from migrations.manager import MigrationManager
from migrations.versions import MIGRATIONS

# Setup logging
log = setup_logging()

# Request/Response models
class QuickCreateRequest(BaseModel):
    idea_text: str = Field(..., min_length=5, max_length=500)
    duration: str = Field(..., description="Duration from frontend")
    style_key: str = Field(..., description="Style identifier")
    auto_create_universe: bool = Field(True)

class DeleteJobRequest(BaseModel):
    job_id: str = Field(..., description="Job ID to delete")

class QuickCreateResponse(BaseModel):
    job_id: str
    episode_id: Optional[str] = None
    series_id: Optional[str] = None
    character_id: Optional[str] = None
    status: Literal["queued", "processing", "error"] = "queued"
    estimated_time_sec: Optional[int] = None
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    state: str
    progress: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    outputs: Optional[List[Dict[str, Any]]] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# Security Middleware (unchanged)
class SecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        request = Request(scope, receive)

        if request.url.path.startswith("/health") or request.url.path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        api_key = request.headers.get("x-api-key")
        expected = os.getenv("BACKEND_API_KEY", "").strip()

        if not expected:
            await self.app(scope, receive, send)
            return

        if not api_key or api_key != expected:
            from fastapi import Response
            response = Response("Invalid API key", status_code=401)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

# Global database manager
_db_manager: Optional[DatabaseManager] = None

def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = get_database_manager()
    return _db_manager

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with database initialization and worker"""
    db_manager = get_db_manager()

    log.info("Initializing database...")

    # Run migrations
    migration_manager = MigrationManager()
    migration_status = migration_manager.get_migration_status(MIGRATIONS)

    if migration_status['needs_migration']:
        log.info(f"Running {migration_status['pending_count']} migrations...")
        result = migration_manager.run_migrations(MIGRATIONS)
        log.info(f"Migration result: {result['message']}")
    else:
        log.info("Database is up to date")

    # Initialize database schema
    db_manager.initialize_database()

    log.info("Starting worker task...")
    asyncio.create_task(worker_with_repositories())
    log.info("Worker task started")

    yield

    # Cleanup
    log.info("Shutting down...")
    db_manager.close()

# Create FastAPI app
app = FastAPI(
    title="Gen Scene Studio Backend - Refactored",
    version="1.0.0",
    description="Backend with Repository Pattern and Connection Pooling",
    lifespan=lifespan
)

# CORS configuration
ALLOWED_ORIGINS = [
    "https://app.genscenestudio.com",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://([a-z0-9-]+\.)*genscenestudio\.com",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add middleware
app.add_middleware(SecurityMiddleware)
app.mount("/files", StaticFiles(directory=settings.MEDIA_DIR), name="files")

log.info(f"MEDIA_DIR: {settings.MEDIA_DIR}")

# Authentication dependency
def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    """Validate API key if configured"""
    expected = settings.BACKEND_API_KEY.strip()
    if not expected:
        return
    if x_api_key is None or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")

# Worker queue
queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

# Helper functions
def format_timestamp(timestamp: Optional[int]) -> Optional[str]:
    """Format Unix timestamp for API response"""
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp).isoformat()

def format_job(job: Job) -> Dict[str, Any]:
    """Format job entity for API response"""
    return {
        'job_id': job.job_id,
        'state': job.state.value,
        'progress': job.progress,
        'created_at': format_timestamp(job.created_at),
        'updated_at': format_timestamp(job.updated_at)
    }

def format_render(render: Render) -> Dict[str, Any]:
    """Format render entity for API response"""
    return {
        'id': render.item_id,
        'item_id': render.item_id,
        'hash': render.hash,
        'quality': render.quality.value,
        'url': render.url,
        'status': render.status.value,
        'created_at': format_timestamp(render.created_at),
        'updated_at': format_timestamp(render.updated_at)
    }

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_manager = get_db_manager()

    # Check database connection
    try:
        jobs_count = db_manager.jobs().count()
        db_status = "healthy"
    except Exception as e:
        log.error(f"Database health check failed: {e}")
        db_status = f"error: {str(e)}"
        jobs_count = None

    # Check binaries
    ffmpeg_ok = _bin_ok("ffmpeg")
    ffprobe_ok = _bin_ok("ffprobe")

    return {
        "status": "healthy" if all([ffmpeg_ok, ffprobe_ok, db_status == "healthy"]) else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "ffmpeg": "available" if ffmpeg_ok else "unavailable",
            "ffprobe": "available" if ffprobe_ok else "unavailable"
        },
        "statistics": {
            "total_jobs": jobs_count if jobs_count is not None else "unknown"
        } if jobs_count is not None else {}
    }

@app.get("/styles")
async def get_styles():
    """Get available video styles"""
    # This should be moved to a configuration file or database
    return {
        "styles": [
            {"key": "cinematic", "name": "Cinematic", "description": "Movie-like appearance"},
            {"key": "anime", "name": "Anime", "description": "Japanese animation style"},
            {"key": "documentary", "name": "Documentary", "description": "Non-fiction style"},
            {"key": "vintage", "name": "Vintage", "description": "Classic film look"},
            {"key": "modern", "name": "Modern", "description": "Contemporary style"},
            {"key": "noir", "name": "Film Noir", "description": "Black and white mystery style"},
        ]
    }

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str, db_manager: DatabaseManager = Depends(lambda: get_db_manager())):
    """Get detailed status for a specific job"""
    job_repo = db_manager.jobs()
    render_repo = db_manager.renders()

    # Get job
    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get renders
    renders = render_repo.get_by_job_id(job_id)
    outputs = [format_render(r) for r in renders]

    return JobStatusResponse(
        job_id=job.job_id,
        state=job.state.value,
        progress=job.progress,
        created_at=format_timestamp(job.created_at),
        updated_at=format_timestamp(job.updated_at),
        outputs=outputs
    )

@app.get("/api/jobs")
async def list_jobs(
    limit: Optional[int] = Query(100, le=1000),
    offset: Optional[int] = Query(0, ge=0),
    state: Optional[str] = Query(None),
    db_manager: DatabaseManager = Depends(lambda: get_db_manager())
):
    """List jobs with pagination and filtering"""
    job_repo = db_manager.jobs()

    # Parse state filter
    state_filter = None
    if state:
        try:
            state_filter = JobState(state)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid state: {state}")

    # Get jobs
    jobs = job_repo.list_all(limit=limit, offset=offset, state_filter=state_filter)

    return {
        "jobs": [format_job(job) for job in jobs],
        "total": job_repo.count(state_filter),
        "limit": limit,
        "offset": offset,
        "has_more": len(jobs) == limit
    }

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, db_manager: DatabaseManager = Depends(lambda: get_db_manager())):
    """Get a specific job by ID"""
    job_repo = db_manager.jobs()

    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return format_job(job)

@app.get("/api/jobs-hub")
async def get_jobs_hub(db_manager: DatabaseManager = Depends(lambda: get_db_manager())):
    """Get jobs for the Jobs Hub frontend"""
    job_repo = db_manager.jobs()
    render_repo = db_manager.renders()

    # Get recent jobs
    recent_jobs = job_repo.get_recent_jobs(hours=24)

    # Format for hub
    jobs_data = []
    for job in recent_jobs:
        renders = render_repo.get_by_job_id(job.job_id)
        completed_renders = [r for r in renders if r.status == RenderStatus.COMPLETED]

        jobs_data.append({
            'id': job.job_id,
            'title': f"Job {job.job_id[:8]}",  # Should come from job metadata
            'status': job.state.value,
            'progress': job.progress,
            'createdAt': format_timestamp(job.created_at),
            'updatedAt': format_timestamp(job.updated_at),
            'rendersCount': len(renders),
            'completedRendersCount': len(completed_renders),
            'thumbnailUrl': completed_renders[0].url if completed_renders else None
        })

    return {
        'jobs': jobs_data,
        'total': len(jobs_data),
        'timestamp': datetime.now().isoformat()
    }

@app.post("/api/quick-create-full-universe")
async def quick_create_universe(
    request: QuickCreateRequest,
    api_key: str = Depends(require_api_key),
    db_manager: DatabaseManager = Depends(lambda: get_db_manager())
):
    """Quick create universe endpoint"""
    job_repo = db_manager.jobs()

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Create job
    job = Job(
        job_id=job_id,
        state=JobState.QUEUED,
        progress=0,
        created_at=int(time.time())
    )

    job_repo.create(job)

    # Add to queue
    await queue.put({
        'type': 'quick_create_full_universe',
        'job_id': job_id,
        'data': request.dict()
    })

    log.info(f"Queued quick create job: {job_id}")

    return QuickCreateResponse(
        job_id=job_id,
        status="queued",
        message="Job created successfully",
        estimated_time_sec=60  # Estimate based on complexity
    )

@app.post("/api/compose")
async def compose_videos(
    job_id: str,
    api_key: str = Depends(require_api_key),
    db_manager: DatabaseManager = Depends(lambda: get_db_manager())
):
    """Compose videos for a job"""
    job_repo = db_manager.jobs()
    render_repo = db_manager.renders()

    # Check job exists
    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get renders
    renders = render_repo.get_by_job_id(job_id)
    completed_renders = [r for r in renders if r.status == RenderStatus.COMPLETED]

    if len(completed_renders) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 completed renders to compose")

    # Add to queue
    await queue.put({
        'type': 'compose',
        'job_id': job_id,
        'data': {
            'renders': [format_render(r) for r in completed_renders]
        }
    })

    log.info(f"Queued compose job: {job_id}")

    return {
        'job_id': job_id,
        'status': 'queued',
        'message': f'Composing {len(completed_renders)} renders'
    }

@app.post("/api/tts")
async def text_to_speech(
    job_id: str,
    item_id: str,
    text: str,
    voice: str = "default",
    api_key: str = Depends(require_api_key),
    db_manager: DatabaseManager = Depends(lambda: get_db_manager())
):
    """Text-to-speech endpoint"""
    render_repo = db_manager.renders()

    # Check render exists
    render = render_repo.get_by_job_and_item(job_id, item_id)
    if not render:
        raise HTTPException(status_code=404, detail="Render not found")

    # Add to queue
    await queue.put({
        'type': 'tts',
        'job_id': job_id,
        'data': {
            'item_id': item_id,
            'text': text,
            'voice': voice
        }
    })

    log.info(f"Queued TTS job: {job_id}/{item_id}")

    return {
        'job_id': job_id,
        'item_id': item_id,
        'status': 'queued',
        'message': 'Text-to-speech job queued'
    }

@app.delete("/api/jobs/{job_id}")
async def delete_job(
    job_id: str,
    api_key: str = Depends(require_api_key),
    db_manager: DatabaseManager = Depends(lambda: get_db_manager())
):
    """Delete a job and all its related data"""
    job_repo = db_manager.jobs()

    # Check job exists
    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete job and related renders (cascades)
    success = job_repo.delete(job_id)

    if success:
        log.info(f"Deleted job: {job_id}")
        return {
            'job_id': job_id,
            'status': 'deleted',
            'message': 'Job and related data deleted successfully'
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to delete job")

@app.post("/api/delete-job")
async def delete_job_post(
    request: DeleteJobRequest,
    api_key: str = Depends(require_api_key),
    db_manager: DatabaseManager = Depends(lambda: get_db_manager())
):
    """Alternative endpoint to delete job via POST"""
    return await delete_job(request.job_id, api_key, db_manager)

@app.get("/api/database/stats")
async def get_database_stats(db_manager: DatabaseManager = Depends(lambda: get_db_manager())):
    """Get database statistics for monitoring"""
    job_repo = db_manager.jobs()
    render_repo = db_manager.renders()
    cache_repo = db_manager.assets_cache()

    # Get statistics
    job_stats = job_repo.get_job_statistics()
    render_stats = render_repo.get_renders_statistics()
    cache_stats = cache_repo.get_cache_statistics()
    db_info = db_manager.get_database_info()

    return {
        'database': db_info,
        'jobs': job_stats,
        'renders': render_stats,
        'cache': cache_stats,
        'timestamp': datetime.now().isoformat()
    }

@app.post("/api/database/optimize")
async def optimize_database(
    api_key: str = Depends(require_api_key),
    db_manager: DatabaseManager = Depends(lambda: get_db_manager())
):
    """Optimize database performance"""
    try:
        db_manager.optimize_database()
        return {
            'status': 'success',
            'message': 'Database optimization completed',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Database optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

# Worker implementation with repositories
async def worker_with_repositories():
    """Enhanced worker using repository pattern"""
    db_manager = get_db_manager()
    job_repo = db_manager.jobs()
    render_repo = db_manager.renders()
    cache_repo = db_manager.assets_cache()

    log.info("Repository-based worker started - waiting for jobs...")

    while True:
        try:
            # Get job from queue
            task = await queue.get()
            job_id = task.get('job_id')
            task_type = task.get('type')

            if not job_id:
                log.error(f"Task missing job_id: {task}")
                continue

            log.info(f"Processing {task_type} job: {job_id}")

            # Update job state to processing
            job_repo.update_state(job_id, JobState.PROCESSING, 10)

            try:
                # Process based on task type
                if task_type == 'quick_create_full_universe':
                    await process_quick_create(db_manager, task)
                elif task_type == 'compose':
                    await process_compose(db_manager, task)
                elif task_type == 'tts':
                    await process_tts(db_manager, task)
                else:
                    log.error(f"Unknown task type: {task_type}")
                    job_repo.update_state(job_id, JobState.ERROR)
                    continue

                # Mark job as completed
                job_repo.update_state(job_id, JobState.COMPLETED, 100)
                log.info(f"Completed {task_type} job: {job_id}")

            except Exception as e:
                log.error(f"Error processing {task_type} job {job_id}: {e}")
                job_repo.update_state(job_id, JobState.ERROR)
                continue

        except Exception as e:
            log.error(f"Worker error: {e}")
            await asyncio.sleep(1)  # Prevent tight error loops

async def process_quick_create(db_manager: DatabaseManager, task: Dict[str, Any]):
    """Process quick create universe job"""
    job_id = task['job_id']
    data = task['data']
    job_repo = db_manager.jobs()
    render_repo = db_manager.renders()

    # Update progress
    job_repo.update_progress(job_id, 20)

    # Simulate creating renders based on duration and style
    duration = data.get('duration', '30s')
    num_scenes = max(3, int(duration.replace('s', '')) // 10)

    for i in range(num_scenes):
        # Update progress
        progress = 30 + (60 * (i + 1) // num_scenes)
        job_repo.update_progress(job_id, progress)

        # Create render
        render = Render(
            job_id=job_id,
            item_id=f"scene_{i+1:03d}",
            hash=hashlib.md5(f"{job_id}_{i}".encode()).hexdigest(),
            quality=RenderQuality.HIGH,
            status=RenderStatus.PROCESSING
        )
        render_repo.create(render)

        # Simulate processing time
        await asyncio.sleep(0.5)

        # Update render status
        render_repo.update_status(job_id, f"scene_{i+1:03d}", RenderStatus.COMPLETED)
        render_repo.update_url(job_id, f"scene_{i+1:03d}", f"/files/renders/{job_id}/scene_{i+1:03d}.mp4")

    # Final progress update
    job_repo.update_progress(job_id, 95)
    await asyncio.sleep(0.1)

async def process_compose(db_manager: DatabaseManager, task: Dict[str, Any]):
    """Process video composition job"""
    job_id = task['job_id']
    data = task['data']
    job_repo = db_manager.jobs()

    # Update progress
    job_repo.update_progress(job_id, 50)

    # Simulate composition time
    await asyncio.sleep(2)

    # Update progress
    job_repo.update_progress(job_id, 90)

    # Create final composed video
    await asyncio.sleep(1)

    # Update progress
    job_repo.update_progress(job_id, 95)

async def process_tts(db_manager: DatabaseManager, task: Dict[str, Any]):
    """Process text-to-speech job"""
    job_id = task['job_id']
    data = task['data']
    job_repo = db_manager.jobs()

    # Update progress
    job_repo.update_progress(job_id, 80)

    # Simulate TTS processing
    await asyncio.sleep(1)

    # Update progress
    job_repo.update_progress(job_id, 95)

# Utility functions
def _bin_ok(name: str) -> bool:
    """Check if binary is available"""
    try:
        subprocess.run([name, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return True
    except Exception:
        return False

# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_refactored:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False  # Disable reload for production
    )