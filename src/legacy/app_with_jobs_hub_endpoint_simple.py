import asyncio
import json
import os
import time
import uuid
import subprocess
import hmac
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Header, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime

# Import existing modules
from core.config import settings
from core.logging import setup_logging
from core.db import get_conn
from models.dao import init_db, upsert_job

# Simple request model that accepts frontend format
class QuickCreateRequest(BaseModel):
    idea_text: str = Field(..., min_length=5, max_length=500)
    duration: str = Field(..., description="Duration from frontend")
    style_key: str = Field(..., description="Style identifier")
    auto_create_universe: bool = Field(True)

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

def safe_timestamp_to_iso(timestamp):
    """Safely convert timestamp to ISO format"""
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(timestamp).isoformat()
    except (ValueError, OSError, OverflowError) as e:
        log.error(f"Error converting timestamp {timestamp} to ISO format: {e}")
        return None

class SecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        request = Request(scope, receive)

        if request.url.path in ["/health", "/styles", "/styles/categories"]:
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
app = FastAPI(title="Gen Scene Studio Backend", version="1.0.0-SIMPLE")

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

# Worker processing function
def process_job_background(job_id: str, job_type: str):
    """Process a job in background - this runs synchronously"""
    try:
        log.info(f"🚀 Starting to process job: {job_id} of type: {job_type}")

        conn = get_conn()

        # Phase 1: 0% -> 30%
        update_job_state(conn, job_id, "processing", 30)
        time.sleep(3)
        log.info(f"📈 Job {job_id} progress: 30%")

        # Phase 2: 30% -> 70%
        update_job_state(conn, job_id, "processing", 70)
        time.sleep(4)
        log.info(f"📈 Job {job_id} progress: 70%")

        # Phase 3: 70% -> 100%
        update_job_state(conn, job_id, "processing", 100)
        time.sleep(2)

        # Mark as completed
        update_job_state(conn, job_id, "completed", 100)
        log.info(f"✅ Job {job_id} completed successfully!")

        conn.close()

    except Exception as e:
        log.error(f"❌ Error processing job {job_id}: {e}")
        try:
            conn = get_conn()
            update_job_state(conn, job_id, "error", 0)
            conn.close()
        except:
            pass

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = str(uuid.uuid4())
    start = time.time()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    log.info(f"{rid} {request.method} {request.url.path} -> {response.status_code} in {int((time.time()-start)*1000)}ms")
    return response

# Global flag to prevent multiple worker instances
worker_task_running = False

@app.get("/health")
def health():
    return {
        "status": "ok",
        "ffmpeg": _bin_ok("ffmpeg"),
        "ffprobe": _bin_ok("ffprobe"),
        "db": True,
        "worker_active": worker_task_running,
        "version": "1.0.0-SIMPLE"
    }

@app.get("/worker-status")
def get_worker_status():
    return {
        "worker_active": worker_task_running,
        "message": "Worker using BackgroundTasks approach - no ASGI lifespan issues"
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

@app.post("/api/quick-create-full-universe", response_model=QuickCreateResponse)
async def quick_create_full_universe(request: QuickCreateRequest, background_tasks: BackgroundTasks, _api_key=Depends(require_api_key)):
    global worker_task_running

    try:
        job_id = f"qcf-{uuid.uuid4().hex[:12]}"
        episode_id = f"ep-{uuid.uuid4().hex[:8]}"
        series_id = f"sr-{uuid.uuid4().hex[:8]}"
        character_id = f"ch-{uuid.uuid4().hex[:8]}"

        # Simple duration mapping
        duration_map = {"30s": 30, "45s": 45, "2min": 120, "3min": 180}
        target_duration = duration_map.get(request.duration, 30)
        estimated_time = target_duration * 2  # Simple estimation

        conn = get_conn()
        upsert_job(conn, job_id, "quick_create_full_universe", 0)
        conn.close()

        # Add job to background tasks - this avoids ASGI lifespan issues!
        background_tasks.add_task(process_job_background, job_id, "quick_create_full_universe")

        worker_task_running = True

        log.info(f"📝 Quick Create Full Universe job {job_id} queued for idea: {request.idea_text[:50]}...")
        log.info(f"🔄 Background task added for job {job_id}")

        return QuickCreateResponse(
            job_id=job_id,
            episode_id=episode_id,
            series_id=series_id,
            character_id=character_id,
            status="processing",  # Changed from "queued" to "processing" since background task starts immediately
            estimated_time_sec=estimated_time,
            message=f"Job created and processing started. Estimated completion time: {estimated_time}s"
        )

    except Exception as e:
        log.exception("Failed to create quick create full universe job")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.post("/api/compose")
async def compose_api(compose_data: dict, background_tasks: BackgroundTasks, _k=Depends(require_api_key)):
    try:
        job_id = compose_data.get("job_id", f"compose-{uuid.uuid4().hex[:12]}")
        conn = get_conn()
        upsert_job(conn, job_id, "compose", 0)
        background_tasks.add_task(process_job_background, job_id, "compose")
        conn.close()
        worker_task_running = True
        return {"job_id": job_id, "status": "processing"}
    except Exception as e:
        log.exception("Failed to queue compose job")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs")
def list_jobs(_k=Depends(require_api_key)):
    try:
        conn = get_conn()
        cursor = conn.execute("""
            SELECT job_id, state, progress, created_at, updated_at
            FROM jobs
            ORDER BY created_at DESC
            LIMIT 100
        """)
        jobs = []
        for row in cursor.fetchall():
            # Handle different column counts safely
            created_at_iso = safe_timestamp_to_iso(row[2])  # created_at is at index 2
            updated_at_iso = safe_timestamp_to_iso(row[3]) if len(row) > 3 else created_at_iso  # updated_at is at index 3 if exists

            jobs.append({
                "job_id": row[0],
                "state": row[1],
                "progress": row[2],
                "created_at": created_at_iso,
                "updated_at": updated_at_iso
            })
        conn.close()
        return {"jobs": jobs}
    except Exception as e:
        log.exception("Failed to list jobs")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs-hub")
def list_jobs_hub(_k=Depends(require_api_key)):
    """Hub Jobs endpoint - Enhanced version with simple date handling"""
    try:
        conn = get_conn()
        cursor = conn.execute("""
            SELECT job_id, state, progress, created_at, updated_at
            FROM jobs
            ORDER BY created_at DESC
            LIMIT 50
        """)
        jobs = []
        for row in cursor.fetchall():
            # Handle column indices safely
            created_at_iso = safe_timestamp_to_iso(row[2]) if len(row) > 2 else None
            updated_at_iso = safe_timestamp_to_iso(row[3]) if len(row) > 3 else created_at_iso

            # Enhanced processing for hub display
            job_info = {
                "job_id": row[0],
                "state": row[1],
                "progress": row[2],
                "created_at": created_at_iso,
                "updated_at": updated_at_iso
            }

            # Add display-friendly fields
            if row[1] in ["processing", "running"] and row[2] > 0:
                job_info["display_status"] = "processing"
                job_info["status_color"] = "blue"
            elif row[1] == "completed":
                job_info["display_status"] = "completed"
                job_info["status_color"] = "green"
            elif row[1] == "error":
                job_info["display_status"] = "error"
                job_info["status_color"] = "red"
            elif row[1] in ["queued", "quick_create_full_universe", "compose"]:
                job_info["display_status"] = "queued" if row[2] == 0 else "processing"
                job_info["status_color"] = "orange" if row[2] == 0 else "blue"
            else:
                job_info["display_status"] = row[1]
                job_info["status_color"] = "gray"

            # Add friendly display name
            job_info["display_name"] = f"Quick Create {row[0][:8]}"
            job_info["type"] = "quick_create_full_universe"
            job_info["status_message"] = f"Status: {job_info['display_status']} - Progress: {row[2]}%"

            jobs.append(job_info)

        conn.close()
        return {"jobs": jobs}
    except Exception as e:
        log.exception("Failed to list jobs for hub")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str, _k=Depends(require_api_key)):
    try:
        conn = get_conn()
        cursor = conn.execute("""
            SELECT job_id, state, progress, created_at, updated_at
            FROM jobs
            WHERE job_id = ?
        """, (job_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")

        # Safe timestamp conversion
        created_at_iso = safe_timestamp_to_iso(row[2]) if len(row) > 2 else None
        updated_at_iso = safe_timestamp_to_iso(row[3]) if len(row) > 3 else created_at_iso

        return {
            "job_id": row[0],
            "state": row[1],
            "progress": row[2],
            "created_at": created_at_iso,
            "updated_at": updated_at_iso
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

@app.get("/")
async def root():
    return {
        "message": "Gen Scene Studio Backend - Worker Fixed + Hub Jobs + Simple Date Handling!",
        "version": "1.0.0-SIMPLE",
        "worker_method": "BackgroundTasks (No ASGI lifespan issues)",
        "hub_jobs_endpoint": "/api/jobs-hub",
        "date_fix": "Simple and robust timestamp conversion",
        "docs": "/docs",
        "health": "/health",
        "worker_status": "/worker-status"
    }