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
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Header, Depends, Query
# from fastapi.middleware.cors import CORSMiddleware  # Moved to Cloudflare
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal

# Import existing modules
from core.config import settings
from core.logging import setup_logging
from core.db import get_conn
from models.dao import init_db, upsert_job

# Import video model configuration from enterprise manager
from worker.enterprise_manager import (
    get_video_model, 
    get_available_models, 
    get_style_model_mapping,
    VIDEO_MODELS_INFO,
    STYLE_TO_MODEL,
    enterprise_job_manager
)

# Simple request model that accepts frontend format
class QuickCreateRequest(BaseModel):
    idea_text: str = Field(..., min_length=5, max_length=500)
    duration: str = Field(..., description="Duration from frontend")
    style_key: str = Field(..., description="Style identifier")
    auto_create_universe: bool = Field(True)
    # Campos opcionales para selección de modelo
    video_model: Optional[str] = Field(None, description="Override: specific video model ID")
    video_duration: Optional[int] = Field(5, description="Video duration in seconds (5-10)")
    video_quality: Optional[str] = Field("720p", description="Video quality: 720p or 1080p")
    aspect_ratio: Optional[str] = Field("16:9", description="Aspect ratio: 16:9, 9:16, 1:1")

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

def update_state(conn, job_id, state, progress):
    conn.execute(
        "UPDATE jobs SET state = ?, progress = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
        (state, progress, job_id)
    )
    conn.commit()

def update_job_state(conn, job_id, state, progress):
    try:
        conn.execute(
            "UPDATE jobs SET state = ?, progress = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
            (state, progress, job_id)
        )
        conn.commit()
    except Exception:
        conn.execute(
            "UPDATE jobs SET state = ?, progress = ? WHERE job_id = ?",
            (state, progress, job_id)
        )
        conn.commit()

class SecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        # Rutas públicas que NO requieren autenticación
        public_paths = ["/health", "/api/", "/files/"]
        if any(request.url.path.startswith(path) for path in public_paths):
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

# Create lifespan context manager
# Create lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    log.info("🚀 Initializing Enterprise Job Manager...")
    await enterprise_job_manager.initialize()
    await enterprise_job_manager.start_workers(num_workers=4)
    log.info("✅ Enterprise Job Manager started with 4 workers")
    yield
    # Shutdown
    log.info("🔌 Shutting down Enterprise Job Manager...")
    await enterprise_job_manager.close()

app = FastAPI(title="Gen Scene Studio Backend", version="0.2.0", lifespan=lifespan)

# ALLOWED_ORIGINS = [
#     "https://app.genscenestudio.com",
#     "http://localhost:3000",
#     "http://localhost:5173",
#     "http://localhost:8000",
#     "http://127.0.0.1:3000",
#     "http://127.0.0.1:5173",
#     "http://127.0.0.1:8000",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=ALLOWED_ORIGINS,
#     allow_origin_regex=r"https://([a-z0-9-]+\.)*genscenestudio\.com",
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#     allow_headers=["*"],
# )
# CORS handled by Cloudflare

init_conn = get_conn()
init_db(init_conn)
app.add_middleware(SecurityMiddleware)
app.mount("/files", StaticFiles(directory=settings.MEDIA_DIR), name="files")
log.info(f"MEDIA_DIR: {settings.MEDIA_DIR}")

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

queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

async def worker():
    log.info("Worker started - waiting for jobs...")
    while True:
      try:
        job = await queue.get()
        job_id = job.get("payload", {}).get("job_id", "unknown")
        job_type = job.get("type", "unknown")
        log.info(f"Processing job: {job_id} of type {job_type}")

        conn = get_conn()
        update_job_state(conn, job_id, "running", 10)
        await asyncio.sleep(3)
        update_job_state(conn, job_id, "running", 50)
        await asyncio.sleep(4)
        update_job_state(conn, job_id, "running", 90)
        await asyncio.sleep(2)
        update_job_state(conn, job_id, "done", 100)
        conn.close()

      except Exception as e:
        log.exception("Error en worker: %s", e)
        try:
            job_id = job.get("payload", {}).get("job_id", "unknown")
            conn = get_conn()
            update_job_state(conn, job_id, "error", 0)
            conn.close()
        except:
            pass
      finally:
        queue.task_done()

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = str(uuid.uuid4())
    start = time.time()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    log.info(f"{rid} {request.method} {request.url.path} -> {response.status_code} in {int((time.time()-start)*1000)}ms")
    return response


@app.get("/health")
def health():
    return {
        "status": "ok",
        "ffmpeg": _bin_ok("ffmpeg"),
        "ffprobe": _bin_ok("ffprobe"),
        "db": True
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
        }
    ]
    return json.dumps(styles)

# ============================================================================
# VIDEO MODELS ENDPOINTS
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
        "default_model": "runway-gen3"
    }

@app.get("/api/style-model-mapping")
def get_style_model_mapping_endpoint():
    """
    Get the mapping of styles to their default video models.
    Frontend can use this to show which model will be used for each style.
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
    model_info = VIDEO_MODELS_INFO.get(model_id, VIDEO_MODELS_INFO["runway-gen3"])
    
    return {
        "style_key": style_key,
        "recommended_model": model_id,
        "model_info": model_info,
        "can_override": True,
        "available_models": list(VIDEO_MODELS_INFO.keys())
    }

# NEW ENDPOINT 1: Status with query parameter (for frontend compatibility)
@app.get("/api/status")
def get_job_status_query(job_id: str = Query(..., description="Job ID to check"), _k=Depends(require_api_key)):
    """Get job status using query parameter - compatible with frontend"""
    try:
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

        # Determine status message based on state
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
            "progress_pct": row[2],  # Alternative field name
            "created_at": row[3],
            "updated_at": row[3],
            "message": message,
            "error_message": error_message,
            "output_assets": None  # Placeholder for frontend compatibility
        }

    except HTTPException:
        raise
    except Exception as e:
        log.exception("Failed to get job status")
        raise HTTPException(status_code=500, detail=str(e))

# NEW ENDPOINT 1B: Status with path parameter (REST-compliant)
@app.get("/api/status/{job_id}")
def get_job_status_path(job_id: str, _k=Depends(require_api_key)):
    """Get job status using path parameter - REST-compliant endpoint"""
    # Reuse the same logic as query parameter version
    return get_job_status_query(job_id=job_id, _k=_k)


# NEW ENDPOINT 2: Jobs Hub (for frontend Jobs Hub page)
@app.get("/api/jobs-hub")
def get_jobs_hub():
    """Get all jobs for Jobs Hub frontend - includes quick-create-full-universe jobs"""
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

            # Determine job type from job_id prefix
            job_type = "unknown"
            if job_id.startswith("qc_"):
                job_type = "quick_create"
            elif job_id.startswith("qcf_"):
                job_type = "quick_create_full_universe"
            elif job_id.startswith("compose-"):
                job_type = "compose"
            elif job_id.startswith("render-"):
                job_type = "render"
            elif job_id.startswith("tts-"):
                job_type = "tts"

            # Calculate duration if available (placeholder)
            duration = None
            if job_type in ["quick_create", "quick_create_full_universe"]:
                # Extract duration from job type or use default
                duration = 30  # placeholder

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

@app.post("/api/quick-create-full-universe", response_model=QuickCreateResponse)
async def quick_create_full_universe(request: QuickCreateRequest, _api_key=Depends(require_api_key)):
    try:
        job_id = f"qcf-{uuid.uuid4().hex[:12]}"
        episode_id = f"ep-{uuid.uuid4().hex[:8]}"
        series_id = f"sr-{uuid.uuid4().hex[:8]}"
        character_id = f"ch-{uuid.uuid4().hex[:8]}"

        # Simple duration mapping
        duration_map = {"30s": 30, "45s": 45, "2min": 120, "3min": 180}
        target_duration = duration_map.get(request.duration, 30)
        estimated_time = target_duration * 2  # Simple estimation

        # Enqueue job using enterprise manager
        await enterprise_job_manager.enqueue_job(
            job_type="quick_create_full_universe",
            payload={
                "job_id": job_id,
                "request": request.dict()
            }
        )

        log.info(f"Quick Create Full Universe job {job_id} queued for idea: {request.idea_text[:50]}...")

        return QuickCreateResponse(
            job_id=job_id,
            episode_id=episode_id,
            series_id=series_id,
            character_id=character_id,
            status="queued",
            estimated_time_sec=estimated_time,
            message=f"Successfully queued full universe creation job. Estimated processing time: {estimated_time}s"
        )

    except Exception as e:
        log.exception("Failed to create quick create full universe job")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.post("/api/compose")
async def compose_api(compose_data: dict, _k=Depends(require_api_key)):
    try:
        job_id = compose_data.get("job_id", f"compose-{uuid.uuid4().hex[:12]}")
        conn = get_conn()
        upsert_job(conn, job_id, "compose", 0)
        queue.put_nowait({"type": "compose", "payload": {"job_id": job_id, **compose_data}})
        conn.close()
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
                "state": row[1],
                "progress": row[2],
                "created_at": row[3],
                "updated_at": row[3]
            })
        conn.close()
        return {"jobs": jobs}
    except Exception as e:
        log.exception("Failed to list jobs")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
def get_job_status_path(job_id: str, _k=Depends(require_api_key)):
    try:
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
        return {
            "job_id": row[0],
            "state": row[1],
            "progress": row[2],
            "created_at": row[3],
            "updated_at": row[3]
        }
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Failed to get job status")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tts")
async def create_tts_job(tts_data: dict, _k=Depends(require_api_key)):
    try:
        job_id = f"tts-{uuid.uuid4().hex[:12]}"
        text = tts_data.get("text", "")
        duration = len(text) / 150.0
        audio_url = f"/files/{job_id}/tts_output.wav"
        media_dir = Path(settings.MEDIA_DIR) / job_id
        media_dir.mkdir(parents=True, exist_ok=True)
        placeholder_file = media_dir / "tts_output.wav"
        placeholder_file.write_text(f"TTS placeholder: {text[:100]}...")
        return {
            "job_id": job_id,
            "audio_url": audio_url,
            "duration_s": duration
        }
    except Exception as e:
        log.exception("Failed to process TTS job")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/delete-job")
async def delete_job(request: DeleteJobRequest, _k=Depends(require_api_key)):
    """Delete a job from the database permanently"""
    try:
        job_id = request.job_id

        # Check if job exists first
        conn = get_conn()
        cursor = conn.execute("SELECT job_id FROM jobs WHERE job_id = ?", (job_id,))
        job_exists = cursor.fetchone()

        if not job_exists:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Delete the job from database
        cursor = conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        deleted_rows = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted_rows > 0:
            log.info(f"✅ Job {job_id} deleted successfully from database")
            return {
                "success": True,
                "message": f"Job {job_id} deleted successfully",
                "job_id": job_id
            }
        else:
            log.warning(f"⚠️ Job {job_id} was not deleted (0 rows affected)")
            raise HTTPException(status_code=500, detail="Failed to delete job")

    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Failed to delete job {request.job_id}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/jobs/{job_id}")
async def delete_job_by_id(job_id: str, _k=Depends(require_api_key)):
    """Delete a job from the database permanently by job_id in URL"""
    try:
        # Check if job exists first
        conn = get_conn()
        cursor = conn.execute("SELECT job_id FROM jobs WHERE job_id = ?", (job_id,))
        job_exists = cursor.fetchone()

        if not job_exists:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Delete the job from database
        cursor = conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        deleted_rows = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted_rows > 0:
            log.info(f"✅ Job {job_id} deleted successfully from database via DELETE")
            return {
                "success": True,
                "message": f"Job {job_id} deleted successfully",
                "job_id": job_id
            }
        else:
            log.warning(f"⚠️ Job {job_id} was not deleted (0 rows affected)")
            raise HTTPException(status_code=500, detail="Failed to delete job")

    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Failed to delete job {job_id}")
        raise HTTPException(status_code=500, detail=str(e))