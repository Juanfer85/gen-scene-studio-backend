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
from fastapi import FastAPI, HTTPException, Request, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
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
app = FastAPI(title="Gen Scene Studio Backend", version="0.2.0")

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

@app.on_event("startup")
async def _startup():
    log.info("Starting worker task...")
    asyncio.create_task(worker())
    log.info("Worker task started")

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

# NEW ENDPOINT: Status with query parameter (for frontend compatibility)
@app.get("/api/status")
def get_job_status_query(job_id: str = Query(..., description="Job ID to check"), _k=Depends(require_api_key)):
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

# NEW ENDPOINT: Jobs Hub (for frontend Jobs Hub page)
@app.get("/api/jobs-hub")
def get_jobs_hub(_k=Depends(require_api_key)):
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

        # Create job in database
        conn = get_conn()
        upsert_job(conn, job_id, "quick_create_full_universe", 0)
        conn.close()

        queue.put_nowait({
            "type": "quick_create_full_universe",
            "payload": {
                "job_id": job_id,
                "request": request.dict()
            }
        })

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