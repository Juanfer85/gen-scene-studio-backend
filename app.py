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
from typing import Dict, Any, Optional, Literal
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Import existing modules
from core.config import settings
from core.logging import setup_logging
from core.db import get_conn
from models.dao import init_db, upsert_job

# Import Enterprise Manager with video models
try:
    from worker.enterprise_manager import (
        EnterpriseJobManager,
        get_video_model,
        get_available_models,
        get_style_model_mapping,
        VIDEO_MODELS_INFO,
        STYLE_TO_MODEL
    )
except ImportError:
    # Fallback if path issues
    import sys
    current_dir = Path(__file__).parent
    backend_dir = current_dir / "backend" / "src"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    from worker.enterprise_manager import (
        EnterpriseJobManager,
        get_video_model,
        get_available_models,
        get_style_model_mapping,
        VIDEO_MODELS_INFO,
        STYLE_TO_MODEL
    )

# Initialize Instance
enterprise_job_manager = EnterpriseJobManager()

# Models - Updated with video_model support
class QuickCreateRequest(BaseModel):
    idea_text: str = Field(..., min_length=5, max_length=500)
    duration: str = Field(..., description="Duration from frontend")
    style_key: str = Field(..., description="Style identifier")
    auto_create_universe: bool = Field(True)
    # Optional video model fields
    video_model: Optional[str] = Field(None, description="Override: specific video model ID")
    video_duration: Optional[int] = Field(5, description="Video duration in seconds (5-10)")
    video_quality: Optional[str] = Field("720p", description="Video quality: 720p or 1080p")
    aspect_ratio: Optional[str] = Field("9:16", description="Aspect ratio: 9:16 (shorts), 16:9, 1:1")

class DeleteJobRequest(BaseModel):
    job_id: str = Field(..., description="Job ID to delete")

class QuickCreateResponse(BaseModel):
    job_id: str
    episode_id: Optional[str] = None
    series_id: Optional[str] = None
    character_id: Optional[str] = None
    status: Literal["queued", "processing", "error", "completed"] = "queued"
    estimated_time_sec: Optional[int] = None
    message: str

class SecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        request = Request(scope, receive)

        # Routes that don't require API key
        public_routes = ["/health", "/api/", "/styles", "/files/", "/docs", "/redoc", "/openapi.json"]
        if any(request.url.path.startswith(route) for route in public_routes):
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

log = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start workers and initialize DB on startup, and cleanup on shutdown"""
    # STARTUP
    log.info("🚀 Starting Gen Scene Studio Enterprise Backend...")
    try:
        # Initialize DB
        init_db(get_conn())
        log.info("📊 Database initialized successfully")

        # Initialize and start Enterprise Manager
        worker_concurrency = getattr(settings, "WORKER_CONCURRENCY", 4)
        await enterprise_job_manager.initialize()
        await enterprise_job_manager.start_workers(worker_concurrency)
        log.info(f"✅ Enterprise Workers started successfully (concurrency={worker_concurrency})")
    except Exception as e:
        log.error(f"❌ Failed to start enterprise backend: {e}")
    
    yield
    
    # SHUTDOWN
    log.info("🛑 Shutting down Enterprise Backend...")
    try:
        await enterprise_job_manager.close()
        log.info("✅ Enterprise backend shut down successfully")
    except Exception as e:
        log.error(f"❌ Error during shutdown: {e}")

app = FastAPI(
    title="Gen Scene Studio Backend",
    version="1.1.0",  # Updated version
    description="Backend for Gen Scene Studio with Enterprise Features and Video Model Selection",
    lifespan=lifespan
)

# --- Manual Kickstart Endpoint ---
@app.get("/api/debug/kickstart")
async def debug_kickstart(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Force start workers manually"""
    expected = "genscene_api_key_prod_2025_secure"
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        log.info("🥾 Kicking workers manually...")
        await enterprise_job_manager.initialize()
        await enterprise_job_manager.start_workers(4)
        return {"status": "ok", "message": "Workers started manually"}
    except Exception as e:
        log.error(f"Kickstart failed: {e}")
        return {"status": "error", "message": str(e)}

ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(SecurityMiddleware)
app.mount("/files", StaticFiles(directory=settings.MEDIA_DIR), name="files")

def _bin_ok(name: str) -> bool:
    try:
        subprocess.run([name, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return True
    except Exception:
        return False

def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    expected = settings.BACKEND_API_KEY.strip()
    if not expected:
        return
    if x_api_key is None or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="invalid api key")

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = str(uuid.uuid4())
    start = time.time()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    log.info(f"{rid} {request.method} {request.url.path} -> {response.status_code} in {int((time.time()-start)*1000)}ms")
    return response

@app.get("/health")
async def health():
    # Auto-start workers if not running (self-healing)
    workers_running = enterprise_job_manager._running
    if not workers_running:
        try:
            log.info("🔄 Health check: Workers not running, auto-starting...")
            await enterprise_job_manager.initialize()
            await enterprise_job_manager.start_workers(4)
            workers_running = True
            log.info("✅ Health check: Workers started successfully")
        except Exception as e:
            log.error(f"❌ Health check: Failed to start workers: {e}")
    
    return {
        "status": "ok",
        "version": "1.1.0-video-models",
        "components": {
            "ffmpeg": _bin_ok("ffmpeg"),
            "ffprobe": _bin_ok("ffprobe"),
            "database": "sqlite_enterprise",
            "workers": workers_running,
            "job_manager": "enterprise_memory",
            "video_models": len(VIDEO_MODELS_INFO)
        },
        "environment": getattr(settings, "ENVIRONMENT", "production")
    }

@app.get("/styles")
def get_styles_endpoint():
    styles = [
        {
            "id": "cinematic_realism",
            "label": "Cinematic Realism",
            "prompt": "cinematic, realistic lighting, soft depth of field",
            "negative": "cartoon, overexposed, blurry"
        },
        {
            "id": "stylized_3d",
            "label": "Stylized 3D (Pixar-lite)",
            "prompt": "stylized 3D, soft subsurface scattering, studio lighting",
            "negative": "photorealism, harsh shadows"
        },
        {
            "id": "anime_style",
            "label": "Anime Style",
            "prompt": "anime, vibrant colors, clean line art, dynamic angles",
            "negative": "photorealism, western animation, realistic textures"
        },
        {
            "id": "documentary",
            "label": "Documentary",
            "prompt": "documentary style, natural lighting, handheld camera feel",
            "negative": "overly polished, cinematic lighting, artificial look"
        }
    ]
    return json.dumps(styles)

# ============================================================================
# VIDEO MODELS ENDPOINTS - NEW
# ============================================================================

@app.get("/api/video-models")
def get_video_models_endpoint():
    """
    Get all available video models with their details.
    The frontend can use this to populate a model selector.
    """
    models_list = [
        {
            **model_info,
            "recommended_for": [style for style, model in STYLE_TO_MODEL.items() if model == model_id]
        }
        for model_id, model_info in VIDEO_MODELS_INFO.items()
    ]
    
    return {
        "models": models_list,
        "total": len(models_list),
        "default_model": "bytedance/v1-pro-text-to-video"
    }

@app.get("/api/style-model-mapping")
def get_style_model_mapping_endpoint():
    """
    Get the mapping of styles to their default video models.
    """
    return {
        "mapping": STYLE_TO_MODEL,
        "available_styles": list(STYLE_TO_MODEL.keys()),
        "note": "When video_model is not specified, the model is auto-selected based on style_key"
    }

@app.get("/api/recommended-model/{style_key}")
def get_recommended_model_endpoint(style_key: str):
    """
    Get the recommended model for a specific style.
    """
    model_id = get_video_model(style_key)
    model_info = VIDEO_MODELS_INFO.get(model_id, VIDEO_MODELS_INFO.get("bytedance/v1-pro-text-to-video", {}))
    
    return {
        "style_key": style_key,
        "recommended_model": model_id,
        "model_info": model_info,
        "can_override": True,
        "available_models": list(VIDEO_MODELS_INFO.keys())
    }

# ============================================================================
# JOB STATUS ENDPOINTS
# ============================================================================

@app.get("/api/status")
async def get_job_status_query(job_id: str = Query(..., description="Job ID to check"), _k=Depends(require_api_key)):
    """Get job status using query parameter - compatible with frontend"""
    try:
        # Try enterprise manager first
        enterprise_job = await enterprise_job_manager.get_job_status(job_id)
        if enterprise_job:
            message = enterprise_job.metadata.get('current_phase')
            if not message:
                 if enterprise_job.status == "queued": message = "Job is queued for processing"
                 elif enterprise_job.status == "processing": message = "Job is in progress"
                 elif enterprise_job.status == "done" or enterprise_job.status == "completed": message = "Job completed successfully"
                 elif enterprise_job.status == "error": message = "Job failed"

            return {
                "job_id": enterprise_job.job_id,
                "status": enterprise_job.status if enterprise_job.status != "completed" else "done",
                "progress": enterprise_job.progress,
                "progress_pct": enterprise_job.progress,
                "created_at": datetime.fromtimestamp(enterprise_job.created_at).isoformat() if enterprise_job.created_at else None,
                "updated_at": datetime.fromtimestamp(enterprise_job.started_at).isoformat() if enterprise_job.started_at else None,
                "message": message,
                "error_message": enterprise_job.error_message,
                "output_assets": enterprise_job.metadata if enterprise_job.metadata else None,
                "video_model": enterprise_job.metadata.get("video_model") if enterprise_job.metadata else None,
                "source": "enterprise_memory"
            }

        conn = get_conn()
        cursor = conn.execute("""
            SELECT job_id, state, progress, created_at
            FROM jobs
            WHERE job_id = ?
        """, (job_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Job not found")

        status = row[1]
        message = None
        error_message = None

        if status == "queued":
            message = "Job is queued for processing"
        elif status == "running":
            message = f"Job is in progress ({row[2]}% complete)"
        elif status == "done":
            message = "Job completed successfully"
        elif status == "error":
            error_message = "Job failed during processing"
            message = "Job failed during processing"

        return {
            "job_id": row[0],
            "status": status,
            "progress": row[2],
            "progress_pct": row[2],
            "created_at": row[3],
            "updated_at": row[3],
            "message": message,
            "error_message": error_message,
            "output_assets": None
        }

    except HTTPException:
        raise
    except Exception as e:
        log.exception("Failed to get job status")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs-hub")
async def get_jobs_hub(_k=Depends(require_api_key)):
    try:
        conn = get_conn()
        cursor = conn.execute("""
            SELECT job_id, state, progress, created_at
            FROM jobs
            ORDER BY created_at DESC
            LIMIT 100
        """)

        jobs = []
        for row in cursor.fetchall():
            job_id = row[0]
            state = row[1]
            progress = row[2]
            created_at = row[3]

            job_type = "unknown"
            if job_id.startswith("qc_") or job_id.startswith("qc-"):
                job_type = "quick_create"
            elif job_id.startswith("qcf_") or job_id.startswith("qcf-"):
                job_type = "quick_create_full_universe"
            elif job_id.startswith("compose-"):
                job_type = "compose"
            elif job_id.startswith("render-"):
                job_type = "render"
            elif job_id.startswith("tts-"):
                job_type = "tts"

            duration = 30
            
            jobs.append({
                "job_id": job_id,
                "status": state,
                "progress": progress,
                "progress_pct": progress,
                "type": job_type,
                "created_at": created_at,
                "updated_at": created_at,
                "duration": duration,
                "message": f"Job {job_id} - {state}"
            })

        conn.close()
        return {
            "jobs": jobs,
            "total": len(jobs)
        }

    except Exception as e:
        log.exception("Failed to list jobs")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# JOB CREATION ENDPOINTS
# ============================================================================

@app.post("/api/quick-create", response_model=QuickCreateResponse)
async def quick_create_simple(request: QuickCreateRequest, _api_key=Depends(require_api_key)):
    """Simple quick create - enterprise version"""
    try:
        duration_map = {"30s": 30, "45s": 45, "2min": 120, "3min": 180}
        target_duration = duration_map.get(request.duration, 30)
        estimated_time = target_duration * 2

        job_payload = {
            "idea_text": request.idea_text,
            "duration": request.duration,
            "style_key": request.style_key,
            "auto_create_universe": False,
            "video_model": request.video_model,
            "video_duration": request.video_duration,
            "video_quality": request.video_quality,
            "aspect_ratio": request.aspect_ratio
        }

        job_id = await enterprise_job_manager.enqueue_job(
            job_type="quick_create",
            payload=job_payload
        )

        log.info(f"🎬 Quick Create job {job_id} queued (model={request.video_model or 'auto'})")

        return QuickCreateResponse(
            job_id=job_id,
            status="queued",
            estimated_time_sec=estimated_time,
            message=f"Quick create queued successfully. Estimated time: {estimated_time}s"
        )

    except Exception as e:
        log.exception("Failed to create quick create job")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.post("/api/quick-create-full-universe", response_model=QuickCreateResponse)
async def quick_create_full_universe(request: QuickCreateRequest, _api_key=Depends(require_api_key)):
    try:
        episode_id = f"ep-{uuid.uuid4().hex[:8]}"
        series_id = f"sr-{uuid.uuid4().hex[:8]}"
        character_id = f"ch-{uuid.uuid4().hex[:8]}"

        duration_map = {"30s": 30, "45s": 45, "2min": 120, "3min": 180}
        target_duration = duration_map.get(request.duration, 30)
        estimated_time = target_duration * 3

        # Include video model in payload
        job_payload = {
            "request": {
                "idea_text": request.idea_text,
                "duration": request.duration,
                "style_key": request.style_key,
                "auto_create_universe": request.auto_create_universe,
                "video_model": request.video_model,
                "video_duration": request.video_duration,
                "video_quality": request.video_quality,
                "aspect_ratio": request.aspect_ratio
            },
            "episode_id": episode_id,
            "series_id": series_id,
            "character_id": character_id
        }

        job_id = await enterprise_job_manager.enqueue_job(
            job_type="quick_create_full_universe",
            payload=job_payload
        )

        # Log which model will be used
        selected_model = get_video_model(request.style_key, request.video_model)
        log.info(f"🌌 Full Universe job {job_id} queued (style={request.style_key}, model={selected_model})")

        return QuickCreateResponse(
            job_id=job_id,
            episode_id=episode_id,
            series_id=series_id,
            character_id=character_id,
            status="queued",
            estimated_time_sec=estimated_time,
            message=f"Full universe creation queued. Model: {selected_model}. Estimated time: {estimated_time}s"
        )

    except Exception as e:
        log.exception("Failed to create quick create full universe job")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.post("/api/compose")
async def compose_api(compose_data: dict, _k=Depends(require_api_key)):
    try:
        job_id = await enterprise_job_manager.enqueue_job(
            job_type="compose",
            payload=compose_data
        )
        return {"job_id": job_id, "status": "queued"}
    except Exception as e:
        log.exception("Failed to queue compose job")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs")
def list_jobs(_k=Depends(require_api_key)):
    try:
        conn = get_conn()
        cursor = conn.execute("""
            SELECT job_id, state, progress, created_at
            FROM jobs
            ORDER BY created_at DESC
            LIMIT 100
        """)

        jobs = []
        for row in cursor.fetchall():
            jobs.append({
                "job_id": row[0],
                "status": row[1],
                "progress": row[2],
                "progress_pct": row[2],
                "created_at": row[3].replace(" ", "T") if row[3] and isinstance(row[3], str) else datetime.now().isoformat(),
                "updated_at": row[3].replace(" ", "T") if row[3] and isinstance(row[3], str) else datetime.now().isoformat(),
                "message": f"Job {row[1]}"
            })
        conn.close()
        return {"jobs": jobs}
    except Exception as e:
        log.exception("Failed to list jobs")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
async def get_job_status_path(job_id: str, _k=Depends(require_api_key)):
    return await get_job_status_query(job_id, _k)

@app.post("/api/tts")
async def create_tts_job(tts_data: dict, _k=Depends(require_api_key)):
    try:
        job_payload = {
            "text": tts_data.get("text", "")
        }
        job_id = await enterprise_job_manager.enqueue_job(
            job_type="tts",
            payload=job_payload
        )
        return {
             "job_id": job_id,
             "status": "queued"
        }
    except Exception as e:
        log.exception("Failed to process TTS job")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/delete-job")
async def delete_job(request: DeleteJobRequest, _k=Depends(require_api_key)):
    try:
        job_id = request.job_id
        conn = get_conn()
        cursor = conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted > 0:
            return {"success": True, "message": f"Job {job_id} deleted", "job_id": job_id}
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    except Exception as e:
         log.exception(f"Failed to delete job {request.job_id}")
         raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/jobs/{job_id}")
async def delete_job_by_id(job_id: str, _k=Depends(require_api_key)):
    return await delete_job(DeleteJobRequest(job_id=job_id), _k)
