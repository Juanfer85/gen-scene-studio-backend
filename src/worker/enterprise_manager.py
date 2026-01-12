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
    from services.kie_client import generate_image as kie_generate_image
    KIE_AVAILABLE = True
except ImportError:
    kie_generate_image = None
    KIE_AVAILABLE = False

try:
    from services.kie_unified_video_client import generate_video as kie_generate_video
    VIDEO_AVAILABLE = True
except ImportError:
    kie_generate_video = None
    VIDEO_AVAILABLE = False

log = logging.getLogger(__name__)

# =============================================================================
# VIDEO MODEL CONFIGURATION
# =============================================================================

# Mapeo de estilos a modelos de video por defecto
# ESTRATEGIA: Usar Wan 2.6 (60 créditos) como default - MÁS ECONÓMICO
# Premium solo cuando es necesario
STYLE_TO_MODEL = {
    # ===== ESTILOS QUE REQUIEREN PREMIUM (solo estos) =====
    # Máxima calidad para proyectos profesionales
    "photorealistic": "runway-gen3",           # Alta fidelidad visual (200 créditos)
    "realistic": "runway-gen3",                # Alta fidelidad visual
    
    # Narrativa compleja
    "fantasy_epic": "runway-gen3",
    "epic": "runway-gen3",
    
    # ===== TODOS LOS DEMÁS → WAN 2.6 (MÁS ECONÓMICO: 60 créditos/5s) =====
    # Anime/Artístico
    "anime_style": "wan/2-6-text-to-video",
    "anime": "wan/2-6-text-to-video",
    "stylized": "wan/2-6-text-to-video",
    
    # Cinematográfico general
    "cinematic_realism": "wan/2-6-text-to-video",
    "cinematic": "wan/2-6-text-to-video",
    "documentary": "wan/2-6-text-to-video",
    
    # Artístico
    "artistic": "wan/2-6-text-to-video",
    
    # Fantasía simple
    "fantasy": "wan/2-6-text-to-video",
    "dramatic": "wan/2-6-text-to-video",
    
    # Minimalista/Rápido
    "minimalist": "wan/2-6-text-to-video",
    "simple": "wan/2-6-text-to-video",
    "fast": "wan/2-6-text-to-video",
    
    # Social media
    "social_media": "wan/2-6-text-to-video",
    "tiktok": "wan/2-6-text-to-video",
    "reels": "wan/2-6-text-to-video",
    "shorts": "wan/2-6-text-to-video",
    
    # Vintage/Retro
    "vintage": "wan/2-6-text-to-video",
    "retro": "wan/2-6-text-to-video",
    
    # Default → Wan 2.6 (MÁS ECONÓMICO)
    "default": "wan/2-6-text-to-video"
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
    "wan/2-6-text-to-video": {
        "id": "wan/2-6-text-to-video",
        "name": "Wan 2.6",
        "tier": "economic",
        "credits_5s": 60,
        "max_duration": 10,
        "features": ["text-to-video", "high-quality"],
        "description": "Excelente balance calidad/costo"
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

        # =========================================================================
        # CREDITS SYSTEM: VALIDATION AND DEDUCTION
        # =========================================================================
        try:
            # Default user if not specified (for now, until auth is fully implemented)
            user_id = payload.get("user_id", "default_user")
            payload["user_id"] = user_id
            
            from services.credits_calculator import calculate_job_cost
            from repositories.credits_repository import CreditsRepository
            
            # Calculate estimated cost
            job_cost = calculate_job_cost(job_type, payload)
            
            if job_cost > 0:
                conn = get_conn()
                credits_repo = CreditsRepository(conn)
                
                # Attempt to deduct credits
                idea_text = payload.get('request', {}).get('idea_text', '') or payload.get('idea_text', 'No description')
                description = f"Job {job_type}: {str(idea_text)[:40]}"
                
                success, message = credits_repo.deduct_credits(
                    user_id=user_id,
                    amount=job_cost,
                    job_id=job_id,
                    description=description
                )
                
                conn.close()
                
                if not success:
                    log.warning(f"❌ Insufficient credits for user {user_id}: {message}")
                    raise ValueError(f"Insufficient credits: {message}")
                
                log.info(f"💰 Deducted {job_cost} credits for user {user_id} (Job: {job_id})")
                
                # Store cost in payload for reference
                payload["credits_cost"] = job_cost
            
        except ImportError:
             log.warning("⚠️ Credits system modules not found, skipping validation")
        except ValueError as ve:
             raise ve
        except Exception as e:
             log.error(f"⚠️ Error in credits validation: {e}")
             # We allow the job to proceed if it's a system error, but log it.
             # Ideally we should probably fail safe, but for now specific ValueError handles the balance check.

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

            # =====================================================================
            # AUTOMATIC REFUND ON FAILURE
            # =====================================================================
            try:
                credits_cost = job.payload.get("credits_cost", 0)
                user_id = job.payload.get("user_id")
                
                if credits_cost > 0 and user_id:
                    log.info(f"💸 Refunding {credits_cost} credits to {user_id} due to job failure")
                    
                    # We need to import here to avoid circular dependencies if possible or ensure availability
                    from repositories.credits_repository import CreditsRepository
                    
                    conn = get_conn()
                    repo = CreditsRepository(conn)
                    
                    repo.add_credits(
                        user_id=user_id,
                        amount=credits_cost,
                        transaction_type="refund",
                        description=f"Refund for failed job {job.job_id}: {str(e)[:50]}"
                    )
                    conn.close()
                    log.info(f"✅ Refund processed successfully for {job.job_id}")
                    
            except Exception as refund_error:
                log.error(f"❌ Failed to process refund for job {job.job_id}: {refund_error}")

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
        # Preserve image URL for video generation
        concept_image_url = None
        
        try:
            if KIE_AVAILABLE:
                log.info(f"🎨 Requesting AI Image for: {idea} ({width}x{height})")
                concept_image_url = await kie_generate_image(
                    prompt=f"Cinematic shot, masterpiece: {idea}",
                    negative="",
                    seed=42,
                    aspect_ratio=aspect_ratio,
                    quality=video_quality,
                    model="gpt4o"
                )
                
                # Download image
                async with aiohttp.ClientSession() as session:
                    async with session.get(concept_image_url) as resp:
                        if resp.status == 200:
                            with open(image_path, 'wb') as f:
                                f.write(await resp.read())
                            log.info(f"⬇️ Image downloaded to {image_path}")
                            log.info(f"🔗 Image URL preserved for video generation: {concept_image_url[:50]}...")
                        else:
                            raise Exception("Failed to download generated image")
            else:
                raise Exception("KIE_AVAILABLE is False")
                
        except Exception as e:
            log.error(f"⚠️ AI Generation failed: {e}. Using fallback.")
            # Create a simple colored image as fallback
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=blue:s={width}x{height}:d=0.1", "-frames:v", "1", str(image_path)], check=False)

        # Phase 1.5: Normalize Image for Vertical Video (CRITICAL FIX)
        # Force crop to ensure 9:16 if requested, preventing horizontal images in vertical video
        if aspect_ratio == "9:16" and image_path.exists():
            try:
                log.info(f"📐 Enforcing 9:16 Aspect Ratio ({width}x{height}) on source image...")
                temp_crop_path = media_dir / "concept_cropped.jpg"
                
                # force 720:1280 crop from center
                cmd_crop = [
                    "ffmpeg", "-y",
                    "-i", str(image_path),
                    "-vf", f"scale=1280:720,crop={width}:{height}", # Ensure enough resolution then crop
                    str(temp_crop_path)
                ]
                
                # Alternative safer crop: scale to cover
                # scale=-1:1280 (height 1280, width auto) -> crop 720:1280
                cmd_smart_crop = [
                    "ffmpeg", "-y",
                    "-i", str(image_path),
                    "-vf", "scale=-1:1280,crop=720:1280", # FORCE 9:16 Vertical
                    str(temp_crop_path)
                ]
                
                process = await asyncio.create_subprocess_exec(*cmd_smart_crop, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await process.communicate()
                
                if temp_crop_path.exists() and temp_crop_path.stat().st_size > 0:
                    os.replace(temp_crop_path, image_path)
                    log.info("✅ Image successfully transformed to 9:16 vertical format")
                    
                    # Force usage of local cropped image
                    # Ensure path matches where FastAPI serves static files
                    relative_path = f"media/{job_id}/{image_filename}"
                    concept_image_url = f"{settings.PUBLIC_BASE_URL}/{relative_path}"
                    log.info(f"🔄 Switched to local cropped image URL: {concept_image_url}")
            except Exception as e:
                log.error(f"❌ Failed to crop image: {e}")

        # Phase 2: AI Video Generation
        job.progress = 50
        job.metadata["current_phase"] = "🎬 Generating AI video with motion..."
        self._save_job_state(job)
        
        output_path = media_dir / "universe_complete.mp4"
        video_generated = False
        
        # Try AI video generation first
        try:
            if VIDEO_AVAILABLE and concept_image_url:  # Use image-to-video if we have the image
                # KIE.ai Wan 2.6 only supports 5s or 10s blocks. Force 5s to save credits.
                final_duration = 5
                # if video_duration > 5:
                #    final_duration = 10
                
                log.info(f"🎬 DEBUG: Calling kie_generate_video with model={selected_model}, duration={final_duration}, url={concept_image_url[:20]}...")
                log.info(f"🎬 Generating AI video from image (Duration: {final_duration}s)...")
                video_url = await kie_generate_video(
                    prompt=f"Cinematic motion, slow camera movement: {idea}",
                    model=selected_model,
                    duration=final_duration,
                    quality=video_quality,
                    aspect_ratio=aspect_ratio,
                    image_url=concept_image_url  # Use the generated image URL
                )
                
                if video_url:
                    # Download video
                    async with aiohttp.ClientSession() as session:
                        async with session.get(video_url) as resp:
                            if resp.status == 200:
                                with open(output_path, 'wb') as f:
                                    f.write(await resp.read())
                                log.info(f"✅ AI Video downloaded to {output_path}")
                                video_generated = True
                                job.metadata["video_source"] = "ai_generated"
                            else:
                                log.warning(f"⚠️ Failed to download video: {resp.status}")
                else:
                    log.warning("⚠️ AI Video generation returned no URL")
            else:
                log.info("⚠️ VIDEO_AVAILABLE is False or no image_url")
                
        except Exception as e:
            log.error(f"⚠️ AI Video generation failed: {e}")
        
        # Fallback: Create video from image (loop)
        if not video_generated:
            log.info("📼 Using fallback: Creating video from image loop...")
            job.metadata["video_source"] = "image_loop_fallback"
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
                log.info(f"📼 Fallback video rendered at {output_path}")
            except Exception as e:
                log.error(f"❌ FFmpeg failed: {e}")

        # Phase 3: Audio & Finalizing (Music Mixing)
        job.progress = 80
        job.metadata["current_phase"] = "🎵 Adding soundtrack..."
        self._save_job_state(job)
        
        final_output_path = media_dir / "universe_final.mp4"
        
        # Audio Styles Mapping (Royalty Free Placeholders)
        AUDIO_MAPPING = {
            "cinematic_realism": "https://cdn.pixabay.com/download/audio/2022/03/24/audio_c8c8a73467.mp3", # Cyberpunk/SciFi vibe
            "documentary": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3", # Epic Cinematic
            "anime_style": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3", # Fantasy/Dreamy
            "default": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"
        }
        
        audio_url = AUDIO_MAPPING.get(style_key, AUDIO_MAPPING["default"])
        audio_path = media_dir / "soundtrack.mp3"
        
        has_audio = False
        try:
            log.info(f"🎵 Downloading audio for style '{style_key}': {audio_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as resp:
                    if resp.status == 200:
                        with open(audio_path, 'wb') as f:
                            f.write(await resp.read())
                        has_audio = True
                    else:
                        log.warning(f"⚠️ Failed to download audio: {resp.status}")
        except Exception as e:
            log.warning(f"⚠️ Audio download failed: {e}")

        # Mix Audio with Video
        if has_audio and os.path.exists(output_path):
            try:
                log.info("🎛️ Mixing audio and video...")
                # Mix video (output_path) + audio (audio_path) -> final_output_path
                # -shortest: cuts audio to video length
                # -map 0:v -map 1:a: use video from 0 and audio from 1
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(output_path),
                    "-i", str(audio_path),
                    "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest",
                    str(final_output_path)
                ]
                
                process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await process.communicate()
                
                # Verify success
                if final_output_path.exists() and final_output_path.stat().st_size > 0:
                    log.info(f"✅ Audio mix successful: {final_output_path}")
                    # Replace origin output with final version for the user
                    os.replace(final_output_path, output_path) 
            except Exception as e:
                log.error(f"❌ Audio mix failed: {e}")
        
        
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
