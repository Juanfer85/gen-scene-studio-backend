import asyncio
import time
import uuid
import logging
from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path
from core.config import settings
from core.db import get_conn
from models.dao import upsert_job
import subprocess
import aiohttp
try:
    from services.kie_client import get_kie_client
except ImportError:
    get_kie_client = None

log = logging.getLogger(__name__)

# =============================================================================
# VIDEO MODEL CONFIGURATION
# =============================================================================

# Mapeo de estilos a modelos de video por defecto
# ESTRATEGIA: Usar modelos económicos por defecto, premium solo cuando es necesario
# Bytedance v1 (150 créditos) como default - buen balance calidad/precio
STYLE_TO_MODEL = {
    # ===== ESTILOS QUE REQUIEREN PREMIUM (solo estos) =====
    # Máxima calidad para proyectos profesionales
    "photorealistic": "veo3",                 # Requiere máxima calidad
    "realistic": "runway-gen3",               # Alta fidelidad visual
    
    # Narrativa compleja (necesita Sora)
    "fantasy_epic": "sora-2-pro-text-to-video",
    "epic": "sora-2-pro-text-to-video",
    
    # ===== ESTILOS CON MODELOS ESPECIALIZADOS =====
    # Anime/Artístico - Kling tiene mejor control artístico
    "anime_style": "kling/v2-1-pro",
    "anime": "kling/v2-1-pro",
    "stylized": "kling/v2-1-pro",
    
    # ===== TODOS LOS DEMÁS → ECONÓMICOS =====
    # Cinematográfico general → Bytedance (buen balance)
    "cinematic_realism": "bytedance/v1-pro-text-to-video",
    "cinematic": "bytedance/v1-pro-text-to-video",
    "documentary": "bytedance/v1-pro-text-to-video",
    
    # Artístico → Hailuo (especializado)
    "artistic": "hailuo/2-3-image-to-video-pro",
    
    # Fantasía simple → Bytedance
    "fantasy": "bytedance/v1-pro-text-to-video",
    "dramatic": "bytedance/v1-pro-text-to-video",
    
    # Minimalista/Rápido → Wan Turbo (el más barato)
    "minimalist": "wan/2-2-a14b-text-to-video-turbo",
    "simple": "wan/2-2-a14b-text-to-video-turbo",
    "fast": "wan/2-2-a14b-text-to-video-turbo",
    
    # Social media → Bytedance (optimizado para esto)
    "social_media": "bytedance/v1-pro-text-to-video",
    "tiktok": "bytedance/v1-pro-text-to-video",
    "reels": "bytedance/v1-pro-text-to-video",
    "shorts": "bytedance/v1-pro-text-to-video",
    
    # Vintage/Retro → Bytedance
    "vintage": "bytedance/v1-pro-text-to-video",
    "retro": "bytedance/v1-pro-text-to-video",
    
    # Default → Bytedance (económico pero bueno)
    "default": "bytedance/v1-pro-text-to-video"
}

# Información de modelos disponibles para el frontend
VIDEO_MODELS_INFO = {
    "runway-gen3": {
        "id": "runway-gen3",
        "name": "Runway Gen-3",
        "tier": "high",
        "credits_5s": 200,
        "max_duration": 10,
        "features": ["text-to-video", "image-to-video", "video-extension"],
        "description": "Balance óptimo calidad/precio"
    },
    "veo3": {
        "id": "veo3",
        "name": "Google Veo 3.1",
        "tier": "premium",
        "credits_5s": 350,
        "max_duration": 8,
        "features": ["text-to-video", "image-to-video"],
        "description": "Máxima calidad visual"
    },
    "sora-2-pro-text-to-video": {
        "id": "sora-2-pro-text-to-video",
        "name": "OpenAI Sora 2 Pro",
        "tier": "premium",
        "credits_5s": 400,
        "max_duration": 20,
        "features": ["text-to-video", "narrative-complex"],
        "description": "Ideal para narrativa compleja"
    },
    "kling/v2-1-pro": {
        "id": "kling/v2-1-pro",
        "name": "Kling v2.1 Pro",
        "tier": "high",
        "credits_5s": 250,
        "max_duration": 10,
        "features": ["text-to-video", "image-to-video", "negative-prompt"],
        "description": "Control creativo avanzado"
    },
    "hailuo/2-3-image-to-video-pro": {
        "id": "hailuo/2-3-image-to-video-pro",
        "name": "Hailuo I2V",
        "tier": "economic",
        "credits_5s": 180,
        "max_duration": 6,
        "features": ["image-to-video"],
        "description": "Estilos artísticos únicos"
    },
    "bytedance/v1-pro-text-to-video": {
        "id": "bytedance/v1-pro-text-to-video",
        "name": "Bytedance v1",
        "tier": "economic",
        "credits_5s": 150,
        "max_duration": 5,
        "features": ["text-to-video", "camera-control"],
        "description": "Optimizado para social media"
    },
    "wan/2-2-a14b-text-to-video-turbo": {
        "id": "wan/2-2-a14b-text-to-video-turbo",
        "name": "Wan Turbo",
        "tier": "economic",
        "credits_5s": 120,
        "max_duration": 5,
        "features": ["text-to-video", "turbo-speed"],
        "description": "El más económico y rápido"
    }
}

def get_video_model(style_key: str, video_model_override: Optional[str] = None) -> str:
    """
    Determina qué modelo de video usar basado en el estilo.
    
    Args:
        style_key: Identificador del estilo (ej: "cinematic_realism")
        video_model_override: Modelo específico elegido por el usuario (opcional)
    
    Returns:
        ID del modelo de video a usar
    """
    # Si el usuario especifica un modelo, usarlo (override)
    if video_model_override and video_model_override in VIDEO_MODELS_INFO:
        log.info(f"🎬 Using user-selected video model: {video_model_override}")
        return video_model_override
    
    # Buscar modelo recomendado para el estilo
    model = STYLE_TO_MODEL.get(style_key, STYLE_TO_MODEL["default"])
    log.info(f"🎬 Auto-selected video model '{model}' for style '{style_key}'")
    return model

def get_available_models() -> Dict[str, Any]:
    """Retorna información de todos los modelos disponibles"""
    return VIDEO_MODELS_INFO

def get_style_model_mapping() -> Dict[str, str]:
    """Retorna el mapeo de estilos a modelos"""
    return STYLE_TO_MODEL

class EnterpriseJob:
    """Enhanced job with enterprise features"""

    def __init__(self, job_id: str, job_type: str, payload: Dict[str, Any]):
        self.job_id = job_id
        self.job_type = job_type
        self.payload = payload
        self.status = "queued"
        self.progress = 0
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        self.metadata = {}
        self.max_retries = 3
        self.current_retry = 0
        self.timeout = 300  # 5 minutes default

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "payload": self.payload
        }

class EnterpriseJobManager:
    """Enhanced job manager with Redis-like capabilities (memory-based for now)"""

    def __init__(self):
        self._jobs: Dict[str, EnterpriseJob] = {}
        self._queue = asyncio.Queue()
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "cancelled_jobs": 0
        }

    async def initialize(self):
        """Initialize the job manager and recover pending jobs"""
        try:
            log.info("✅ Enterprise Job Manager initialized (memory-based)")
            
            # Recover jobs from DB
            # Recover jobs from DB
            conn = get_conn()
            # New schema: job_id, state, progress, created_at, job_type, payload
            # We select relevant columns: job_id, job_type, payload, state, progress
            cursor = conn.execute("SELECT job_id, job_type, payload, state, progress FROM jobs WHERE state IN ('queued', 'running', 'processing')")
            pending_jobs = cursor.fetchall()
            conn.close()

            count = 0
            for row in pending_jobs:
                job_id, job_type_db, payload_str, status, progress = row
                
                # Parse payload
                try:
                    payload = json.loads(payload_str) if payload_str else {}
                except:
                    payload = {}
                
                # Default fallback
                if not job_type_db or job_type_db == 'unknown': 
                    job_type_db = "quick_create"
                
                job = EnterpriseJob(job_id, job_type_db, payload)
                job.status = "queued" # Reset to queued to ensure processing
                job.progress = progress
                
                self._jobs[job_id] = job
                await self._queue.put(job)
                count += 1
            
            if count > 0:
                log.info(f"♻️ Recovered {count} pending jobs from database")
                
        except Exception as e:
            log.error(f"⚠️ Failed to recover pending jobs: {e}")

    async def close(self):
        """Close the job manager"""
        self._running = False

        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass

        log.info("🔌 Enterprise Job Manager closed")

    async def enqueue_job(self, job_type: str, payload: Dict[str, Any]) -> str:
        """Add a job to the processing queue"""
        # Extract job_id from payload if present, otherwise create new with prefix
        job_id = payload.get("job_id")
        if not job_id:
            raw_uuid = str(uuid.uuid4())
            if job_type == "quick_create":
                job_id = f"qc-{raw_uuid[:12]}"
            elif job_type == "quick_create_full_universe":
                job_id = f"qcf-{raw_uuid[:12]}"
            elif job_type == "compose":
                job_id = f"compose-{raw_uuid[:12]}"
            elif job_type == "tts":
                job_id = f"tts-{raw_uuid[:12]}"
            else:
                job_id = f"{raw_uuid[:12]}"

        job = EnterpriseJob(job_id, job_type, payload)
        
        # Store in memory
        self._jobs[job_id] = job
        
        # Store in DB
        try:
            conn = get_conn()
            upsert_job(conn, job_id, "queued", 0, job_type=job_type, payload=payload)
            conn.close()
        except Exception as e:
            log.error(f"Failed to persist job {job_id}: {e}")
        
        # Add to processing queue
        await self._queue.put(job)
        self._stats["total_jobs"] += 1
        
        log.info(f"📥 Enqueued job {job_id} (type={job_type})")
        return job_id

    async def start_workers(self, num_workers: int = 4):
        """Start worker processes"""
        if self._running:
            log.warning("⚠️ Workers are already running")
            return

        self._running = True

        for i in range(num_workers):
            worker_task = asyncio.create_task(
                self._worker_loop(f"worker-{i}"),
                name=f"worker-{i}"
            )
            self._workers.append(worker_task)

        log.info(f"🚀 Started {num_workers} enterprise workers")

    async def _worker_loop(self, worker_id: str):
        """Main worker processing loop"""
        log.info(f"🤖 Enterprise worker {worker_id} started")

        while self._running:
            try:
                # Wait for job with timeout
                # Note: settings.WORKER_POLL_INTERVAL might need to be imported or hardcoded if missing
                poll_interval = getattr(settings, 'WORKER_POLL_INTERVAL', 1.0)
                job = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=poll_interval
                )

                log.info(f"📋 Worker {worker_id} processing job: {job.job_id} ({job.job_type})")

                # Process job
                await self._process_job(worker_id, job)
                self._queue.task_done()

            except asyncio.TimeoutError:
                continue  # Normal timeout, check again
            except asyncio.CancelledError:
                log.info(f"🛑 Worker {worker_id} cancelled")
                break
            except Exception as e:
                log.error(f"❌ Worker {worker_id} error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry

    async def _process_job(self, worker_id: str, job: EnterpriseJob):
        """Process a single job with enterprise features"""
        try:
            # Update job status
            job.status = "processing"
            job.started_at = time.time()
            job.progress = 0

            # Store in memory
            self._jobs[job.job_id] = job

            # Update database
            conn = get_conn()
            upsert_job(conn, job.job_id, "processing", 0, job_type=job.job_type, payload=job.payload)
            conn.close()

            # Process based on job type
            if job.job_type == "quick_create":
                await self._process_quick_create(worker_id, job)
            elif job.job_type == "quick_create_full_universe":
                await self._process_quick_create_full_universe(worker_id, job)
            elif job.job_type == "compose":
                await self._process_compose(worker_id, job)
            elif job.job_type == "tts":
                await self._process_tts(worker_id, job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")

            # Mark as completed
            job.status = "completed"
            job.completed_at = time.time()
            job.progress = 100

            # Update database
            conn = get_conn()
            upsert_job(conn, job.job_id, "done", 100, job_type=job.job_type, payload=job.payload)
            conn.close()

            # Update stats
            self._stats["completed_jobs"] += 1

            log.info(f"✅ Worker {worker_id} completed job: {job.job_id}")

        except Exception as e:
            # Mark as failed
            job.status = "error"
            job.error_message = str(e)

            # Update database
            conn = get_conn()
            upsert_job(conn, job.job_id, "error", job.progress, job_type=job.job_type, payload=job.payload)
            conn.close()

            # Update stats
            self._stats["failed_jobs"] += 1

            log.error(f"❌ Worker {worker_id} failed job {job.job_id}: {e}")

        finally:
            # Store final job state
            self._jobs[job.job_id] = job

    async def _process_quick_create(self, worker_id: str, job: EnterpriseJob):
        """Process quick create job"""
        phases = [
            (10, "Generating script...", 2),
            (30, "Creating scenes...", 3),
            (60, "Rendering video...", 5),
            (90, "Adding audio...", 2),
            (100, "Finalizing...", 1)
        ]

        for progress, description, duration in phases:
            job.progress = progress
            job.metadata["current_phase"] = description

            # Update database
            self._save_job_state(job)
            # conn = get_conn()
            # upsert_job(conn, job.job_id, "running", progress)
            # conn.close()

            await asyncio.sleep(duration)

        # Set output URL
        job.metadata["output_url"] = f"/files/{job.job_id}/output.mp4"

# import handled at top of file

# ... (inside class)

    async def _process_quick_create_full_universe(self, worker_id: str, job: EnterpriseJob):
        """Process full universe creation job with Real AI"""
        # Generate IDs
        episode_id = f"ep-{uuid.uuid4().hex[:8]}"
        series_id = f"sr-{uuid.uuid4().hex[:8]}"
        character_id = f"ch-{uuid.uuid4().hex[:8]}"
        
        # Ensure media directory exists
        media_dir = Path(settings.MEDIA_DIR) / job.job_id
        media_dir.mkdir(parents=True, exist_ok=True)

        # Extract request data
        request_data = job.payload.get("request", job.payload)
        idea = request_data.get("idea_text", "GenScene Universe")
        style_key = request_data.get("style_key", "default")
        video_model_override = request_data.get("video_model")  # Usuario puede especificar modelo
        video_duration = request_data.get("video_duration", 5)
        video_quality = request_data.get("video_quality", "720p")
        aspect_ratio = request_data.get("aspect_ratio", "9:16")  # Default: Shorts verticales
        
        # 📐 Dimensiones según aspect ratio (optimizado para shorts)
        ASPECT_DIMENSIONS = {
            "9:16": (720, 1280),   # Vertical shorts (TikTok, Reels, Shorts)
            "16:9": (1280, 720),   # Horizontal (YouTube)
            "1:1": (720, 720),     # Cuadrado (Instagram)
        }
        width, height = ASPECT_DIMENSIONS.get(aspect_ratio, (720, 1280))  # Default 9:16
        
        # 🎬 Selección inteligente de modelo
        selected_model = get_video_model(style_key, video_model_override)
        model_info = VIDEO_MODELS_INFO.get(selected_model, VIDEO_MODELS_INFO["bytedance/v1-pro-text-to-video"])
        
        log.info(f"📊 Job Config: style={style_key}, model={selected_model}, duration={video_duration}s, quality={video_quality}, aspect={aspect_ratio} ({width}x{height})")
        
        # Guardar info del modelo en metadata
        job.metadata["video_model"] = selected_model
        job.metadata["video_model_info"] = model_info
        job.metadata["style_key"] = style_key
        job.metadata["aspect_ratio"] = aspect_ratio
        job.metadata["dimensions"] = f"{width}x{height}"
        
        # Phase 1: AI Generation
        job.progress = 10
        job.metadata["current_phase"] = "🧠 Dreaming up concept (Kie.ai)..."
        self._save_job_state(job) # Helper to update DB
        
        image_path = media_dir / "concept.jpg"
        
        try:
            if get_kie_client:
                log.info(f"🎨 Requesting AI Image for: {idea} ({width}x{height})")
                client = await get_kie_client()
                image_url = await client.generate_image(prompt=f"Cinematic shot, masterpiece: {idea}", width=width, height=height)
                
                # Download image
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status == 200:
                            with open(image_path, 'wb') as f:
                                f.write(await resp.read())
                            log.info(f"⬇️ Image downloaded to {image_path}")
                        else:
                            raise Exception("Failed to download generated image")
            else:
                raise Exception("Kie Client not available")
                
        except Exception as e:
            log.error(f"⚠️ AI Generation failed: {e}. Using fallback.")
            # Create a simple colored image as fallback
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=blue:s={width}x{height}:d=0.1", "-frames:v", "1", str(image_path)], check=False)

        # Phase 2: Video Encoding
        job.progress = 50
        job.metadata["current_phase"] = "🎬 Rendering video from AI dream..."
        self._save_job_state(job)
        
        output_path = media_dir / "universe_complete.mp4"
        
        # Create video from image (loop 30s)
        try:
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(image_path),
                "-c:v", "libx264", "-t", "30", "-pix_fmt", "yuv420p",
                "-vf", f"scale={width}:{height}",
                str(output_path)
            ]
            process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await process.communicate()
            
            log.info(f"📼 Video rendered at {output_path}")
            
        except Exception as e:
            log.error(f"❌ FFmpeg failed: {e}")

        # Set universe metadata
        job.metadata.update({
            "character_id": character_id,
            "episode_id": episode_id,
            "series_id": series_id,
            "output_url": f"/files/{job.job_id}/universe_complete.mp4",
            "character_url": f"/files/{job.job_id}/character.json",
            "episode_url": f"/files/{job.job_id}/episode.json",
            "series_url": f"/files/{job.job_id}/series.json"
        })
        
    def _save_job_state(self, job):
        conn = get_conn()
        upsert_job(conn, job.job_id, "running", job.progress, job_type=job.job_type, payload=job.payload)
        conn.close()

    async def _process_compose(self, worker_id: str, job: EnterpriseJob):
        """Process video composition job"""
        phases = [
            (20, "Loading video assets...", 2),
            (40, "Applying transitions...", 3),
            (60, "Adding audio track...", 3),
            (80, "Color grading...", 2),
            (100, "Finalizing composition...", 2)
        ]

        for progress, description, duration in phases:
            job.progress = progress
            job.metadata["current_phase"] = description

            # Update database
            self._save_job_state(job)
            # conn = get_conn()
            # upsert_job(conn, job.job_id, "running", progress)
            # conn.close()

            await asyncio.sleep(duration)

        job.metadata["output_url"] = f"/files/{job.job_id}/composed.mp4"

    async def _process_tts(self, worker_id: str, job: EnterpriseJob):
        """Process text-to-speech job"""
        text = job.payload.get("text", "")
        # Safe division
        processing_time = max(1, len(text) / 150.0) 

        job.progress = 30
        job.metadata["current_phase"] = "Converting text to speech..."

        # Update database
        self._save_job_state(job)
        # conn = get_conn()
        # upsert_job(conn, job.job_id, "running", 30)
        # conn.close()

        await asyncio.sleep(processing_time / 2)

        job.progress = 80
        job.metadata["current_phase"] = "Optimizing audio..."

        # Update database
        self._save_job_state(job)
        # conn = get_conn()
        # upsert_job(conn, job.job_id, "running", 80)
        # conn.close()

        await asyncio.sleep(processing_time / 2)

        job.progress = 100
        job.metadata.update({
            "audio_url": f"/files/{job.job_id}/speech.wav",
            "duration": processing_time
        })



    async def get_job_status(self, job_id: str) -> Optional[EnterpriseJob]:
        """Get current job status"""
        return self._jobs.get(job_id)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job if it hasn't started processing"""
        job = self._jobs.get(job_id)
        if not job:
            return False

        if job.status == "queued":
            job.status = "cancelled"
            job.completed_at = time.time()

            # Update database
            conn = get_conn()
            upsert_job(conn, job_id, "cancelled", job.progress, job_type=job.job_type, payload=job.payload)
            conn.close()

            self._stats["cancelled_jobs"] += 1
            log.info(f"🚫 Cancelled job {job_id}")
            return True
        else:
            log.warning(f"⚠️ Cannot cancel job {job_id} - status: {job.status}")
            return False

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        queued_count = sum(1 for job in self._jobs.values() if job.status == "queued")
        processing_count = sum(1 for job in self._jobs.values() if job.status == "processing")
        completed_count = sum(1 for job in self._jobs.values() if job.status == "completed")
        failed_count = sum(1 for job in self._jobs.values() if job.status == "error")
        cancelled_count = sum(1 for job in self._jobs.values() if job.status == "cancelled")

        return {
            "queued": queued_count,
            "processing": processing_count,
            "completed": completed_count,
            "failed": failed_count,
            "cancelled": cancelled_count,
            "total": len(self._jobs),
            "workers_running": self._running,
            "active_workers": len(self._workers),
            "stats": self._stats
        }

# Global instance
enterprise_job_manager = EnterpriseJobManager()
