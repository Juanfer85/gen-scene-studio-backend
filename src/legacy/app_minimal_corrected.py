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
from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Literal

# Import existing modules
from core.config import settings
from core.logging import setup_logging
from core.db import get_conn
from models.dao import init_db, upsert_job

# Quick Create models
class QuickCreateOptions(BaseModel):
    voice: Optional[str] = None
    music: Optional[str] = None
    targets: List[str] = Field(default_factory=list)
    variations: int = Field(default=1, ge=1, le=10)

class QuickCreateRequest(BaseModel):
    mode: Literal["idea", "script"] = Field(default="idea", description="Creation mode")
    idea_text: str = Field(..., min_length=5, max_length=500, description="Base idea or script text")

    # Accept both formats from frontend
    duration_label: Optional[Literal["30s", "45s", "2min", "3min"]] = Field(None, description="Duration label")
    duration: Optional[str] = Field(None, description="Duration string from frontend")
    target_duration_sec: Optional[int] = Field(None, ge=30, le=180, description="Target duration in seconds")

    # More flexible pattern for style_key
    style_key: str = Field(..., pattern=r"^[a-z_-]+$", description="Style identifier")
    auto_create_universe: bool = Field(True, description="Whether to auto-create universe")

    options: QuickCreateOptions = Field(default_factory=QuickCreateOptions)

    @validator('duration_label', pre=True, always=True)
    def extract_duration_label(cls, v, values):
        # If duration_label is not provided but duration is, use duration
        if v is None and 'duration' in values and values['duration']:
            return values['duration']
        return v

    @validator('target_duration_sec', pre=True, always=True)
    def extract_target_duration(cls, v, values):
        # If target_duration_sec is not provided, extract from duration_label
        if v is None:
            duration = values.get('duration_label') or values.get('duration', '30s')
            duration_map = {
                '30s': 30,
                '45s': 45,
                '2min': 120,
                '3min': 180
            }
            return duration_map.get(duration, 30)
        return v

class QuickCreateResponse(BaseModel):
    job_id: str
    episode_id: Optional[str] = None
    series_id: Optional[str] = None
    character_id: Optional[str] = None
    status: Literal["queued", "processing", "error"] = "queued"
    estimated_time_sec: Optional[int] = None
    message: str

def update_state(conn, job_id, state, progress):
    """Simple update function"""
    conn.execute(
        "UPDATE jobs SET state = ?, progress = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
        (state, progress, job_id)
    )
    conn.commit()

def update_job_state(conn, job_id, state, progress):
    """Update job state with fallback"""
    try:
        conn.execute(
            "UPDATE jobs SET state = ?, progress = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
            (state, progress, job_id)
        )
        conn.commit()
    except Exception:
        # Fallback for databases without updated_at column
        conn.execute(
            "UPDATE jobs SET state = ?, progress = ? WHERE job_id = ?",
            (state, progress, job_id)
        )
        conn.commit()

# Simplified security middleware without external dependencies
class SecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        request = Request(scope, receive)

        # Excluir endpoints públicos
        if request.url.path in ["/health", "/styles", "/styles/categories"]:
            await self.app(scope, receive, send)
            return

        # Validar API key
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

# CORS estricto con lista específica + regex para subdominios
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

# Initialize the database once
init_conn = get_conn()
init_db(init_conn)

# Middleware de seguridad para validar API key
app.add_middleware(SecurityMiddleware)

app.mount("/files", StaticFiles(directory=settings.MEDIA_DIR), name="files")
log.info(f"MEDIA_DIR: {settings.MEDIA_DIR}")

def _bin_ok(name: str) -> bool:
    """Check if binary exists and is executable."""
    try:
        subprocess.run([name, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return True
    except Exception:
        return False

def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    """Dependency to validate API key with timing attack protection."""
    expected = settings.BACKEND_API_KEY.strip()
    if not expected:
        return  # no key → dev mode

    if x_api_key is None or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="invalid api key")

# Jobs queue
queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

async def worker():
    log.info("Worker started - waiting for jobs...")
    while True:
      try:
        job = await queue.get()
        job_id = job.get("payload", {}).get("job_id", "unknown")
        log.info(f"Processing job: {job_id} of type {job.get('type', 'unknown')}")

        if job["type"] == "render_batch":
            conn = get_conn()
            update_job_state(conn, job_id, "running", 10)
            await asyncio.sleep(2)  # Simulated processing step 1
            update_job_state(conn, job_id, "running", 40)
            await asyncio.sleep(3)  # Simulated processing step 2
            update_job_state(conn, job_id, "running", 80)
            await asyncio.sleep(2)  # Simulated processing step 3
            update_job_state(conn, job_id, "done", 100)
            conn.close()

        elif job["type"] == "compose":
            conn = get_conn()
            update_job_state(conn, job_id, "running", 15)
            await asyncio.sleep(1.5)  # Simulated processing step 1
            update_job_state(conn, job_id, "running", 50)
            await asyncio.sleep(2)  # Simulated processing step 2
            update_job_state(conn, job_id, "running", 85)
            await asyncio.sleep(1.5)  # Simulated processing step 3
            update_job_state(conn, job_id, "done", 100)
            conn.close()

        elif job["type"] == "quick_create_full_universe":
            conn = get_conn()
            update_job_state(conn, job_id, "running", 10)
            await asyncio.sleep(3)  # Simulated AI processing
            update_job_state(conn, job_id, "running", 40)
            await asyncio.sleep(4)  # Simulated content generation
            update_job_state(conn, job_id, "running", 80)
            await asyncio.sleep(3)  # Simulated final assembly
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

# --- STYLES ENDPOINTS ---
@app.get("/styles")
def get_styles_endpoint():
    """Complete styles catalog with all styles from original plan"""
    styles = [
        {
            "id": "cinematic_realism",
            "label": "Cinematic Realism",
            "prompt": "cinematic, realistic lighting, soft depth of field, high dynamic range, subtle film grain",
            "negative": "cartoon, overexposed, blurry, plastic skin, oversaturated, watermark, text",
            "meta": {
                "category": "realistic",
                "motion": "kenburns",
                "grain": "subtle",
                "aspectRatio": "9:16"
            }
        },
        {
            "id": "stylized_3d",
            "label": "Stylized 3D (Pixar-lite)",
            "prompt": "stylized 3D, soft subsurface scattering, studio lighting, clean materials, expressive characters",
            "negative": "photorealism, harsh shadows, grain, text, watermark",
            "meta": {
                "category": "animated",
                "motion": "kenburns",
                "grain": "none",
                "aspectRatio": "9:16"
            }
        },
        {
            "id": "anime",
            "label": "Anime",
            "prompt": "anime style, cel shading, crisp line art, expressive eyes, painterly background, high contrast",
            "negative": "photorealistic, 3D render noise, text overlay",
            "meta": {
                "category": "animated",
                "motion": "kenburns",
                "grain": "none",
                "aspectRatio": "9:16"
            }
        },
        {
            "id": "documentary_grit",
            "label": "Documentary Grit",
            "prompt": "documentary style, handheld feel, available light, authentic textures, minimal grading",
            "negative": "overpolished, studio glamour, artificial lighting look",
            "meta": {
                "category": "realistic",
                "motion": "handheld",
                "grain": "subtle",
                "aspectRatio": "9:16"
            }
        },
        {
            "id": "film_noir",
            "label": "Film Noir",
            "prompt": "black and white film noir, hard light, deep shadows, high contrast, venetian blinds shadows",
            "negative": "color, low contrast, flat lighting, text",
            "meta": {
                "category": "vintage",
                "motion": "kenburns",
                "grain": "heavy",
                "aspectRatio": "9:16"
            }
        },
        {
            "id": "retro_vhs",
            "label": "Retro VHS 90s",
            "prompt": "retro 90s vhs aesthetic, chromatic aberration, scanlines, analog noise, soft focus",
            "negative": "ultra sharp, modern digital clarity",
            "meta": {
                "category": "vintage",
                "motion": "handheld",
                "grain": "heavy",
                "aspectRatio": "9:16"
            }
        },
        {
            "id": "fantasy_illustration",
            "label": "Fantasy Illustration",
            "prompt": "epic fantasy illustration, painterly brushwork, volumetric lighting, ornate details, dramatic composition",
            "negative": "photorealistic, flat colors, text",
            "meta": {
                "category": "artistic",
                "motion": "kenburns",
                "grain": "none",
                "aspectRatio": "9:16"
            }
        }
    ]

    # Generate ETag for caching
    styles_json = json.dumps(styles, sort_keys=True)
    etag = hashlib.md5(styles_json.encode()).hexdigest()

    from fastapi import Response
    return Response(
        content=json.dumps(styles),
        media_type="application/json",
        headers={
            "ETag": f'"{etag}"',
            "Cache-Control": "public, max-age=3600"
        }
    )

@app.get("/styles/{style_id}")
def get_style_endpoint(style_id: str):
    """Get a specific style by ID"""
    styles = {
        "cinematic_realism": {
            "prompt": "cinematic, realistic lighting, soft depth of field, high dynamic range, subtle film grain",
            "negative": "cartoon, overexposed, blurry, plastic skin, oversaturated, watermark, text"
        }
    }

    style = styles.get(style_id, styles["cinematic_realism"])
    return {"id": style_id, **style}

@app.get("/styles/categories")
def get_categories_endpoint():
    """Get all available categories"""
    return {"categories": ["realistic", "animated", "vintage", "artistic"]}

# --- QUICK CREATE FULL UNIVERSE ENDPOINT ---
@app.post("/api/quick-create-full-universe", response_model=QuickCreateResponse)
async def quick_create_full_universe(request: QuickCreateRequest, _api_key=Depends(require_api_key)):
    """Quick Create Full Universe endpoint - creates episode, character and series from idea"""
    try:
        # Generate unique IDs
        job_id = f"qcf-{uuid.uuid4().hex[:12]}"
        episode_id = f"ep-{uuid.uuid4().hex[:8]}"
        series_id = f"sr-{uuid.uuid4().hex[:8]}"
        character_id = f"ch-{uuid.uuid4().hex[:8]}"

        # Estimation based on complexity
        base_time = 60  # 1 minute base
        complexity_multiplier = 1.5 if request.mode == "script" else 1.0
        duration_factor = request.target_duration_sec / 30  # Normalize to 30 seconds
        estimated_time = int(base_time * complexity_multiplier * duration_factor)

        # Create job in database
        conn = get_conn()
        upsert_job(conn, job_id, "quick_create_full_universe", 0)
        conn.close()

        # Queue for processing
        queue.put_nowait({
            "type": "quick_create_full_universe",
            "payload": {
                "job_id": job_id,
                "episode_id": episode_id,
                "series_id": series_id,
                "character_id": character_id,
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

# --- API ENDPOINTS ---
@app.post("/api/compose")
async def compose_api(compose_data: dict, _k=Depends(require_api_key)):
    """Compose endpoint - accepts dict for flexibility"""
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
    """List all jobs"""
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
                "updated_at": row[3]  # Use created_at as fallback
            })
        conn.close()
        return {"jobs": jobs}
    except Exception as e:
        log.exception("Failed to list jobs")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str, _k=Depends(require_api_key)):
    """Get status of a specific job"""
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

# SSE endpoint for real-time job updates
@app.get("/api/jobs/{job_id}/events")
async def job_events_stream(job_id: str, _k=Depends(require_api_key)):
    """Server-Sent Events for real-time job status updates"""

    async def event_generator():
        # Set initial status
        last_status = None

        try:
            while True:
                conn = get_conn()
                cursor = conn.execute("""
                    SELECT state, progress FROM jobs WHERE job_id = ?
                """, (job_id,))

                row = cursor.fetchone()
                conn.close()

                if not row:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
                    break

                current_state, current_progress = row[0], row[1]
                current_status = f"{current_state}:{current_progress}"

                # Only send update if status changed
                if current_status != last_status:
                    event_data = {
                        'type': 'job_update',
                        'job_id': job_id,
                        'state': current_state,
                        'progress': current_progress,
                        'timestamp': time.time()
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                    last_status = current_status

                # If job is complete or error, close stream
                if current_state in ['done', 'error']:
                    yield f"data: {json.dumps({'type': 'stream_complete', 'job_id': job_id})}\n\n"
                    break

                # Poll every 2 seconds
                await asyncio.sleep(2)

        except Exception as e:
            error_data = {
                'type': 'error',
                'message': f'Stream error: {str(e)}',
                'job_id': job_id
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

# Simple TTS endpoint
@app.post("/api/tts")
async def create_tts_job(tts_data: dict, _k=Depends(require_api_key)):
    """TTS endpoint - accepts dict for flexibility"""
    try:
        job_id = f"tts-{uuid.uuid4().hex[:12]}"
        text = tts_data.get("text", "")
        voice = tts_data.get("voice", "default")
        wpm = tts_data.get("wpm", 160)

        # Simulated TTS processing
        duration = len(text) / 150.0  # Estimated duration
        audio_url = f"/files/{job_id}/tts_output.wav"

        # Create directory structure
        media_dir = Path(settings.MEDIA_DIR) / job_id
        media_dir.mkdir(parents=True, exist_ok=True)

        # Create placeholder file
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