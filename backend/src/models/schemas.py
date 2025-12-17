from typing import List, Literal, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

Quality = Literal["draft", "upscale"]

class RenderItemIn(BaseModel):
    id: str
    prompt: str
    negative: str
    seed: int
    quality: Quality

class RenderBatchIn(BaseModel):
    job_id: str
    model: str
    aspectRatio: str
    enableTranslation: bool = False
    planos: List[RenderItemIn]

class RenderItemOut(BaseModel):
    id: str
    quality: Quality
    hash: str
    url: Optional[str] = None
    status: Literal["queued", "running", "done", "error"] = "queued"

class JobStatusOut(BaseModel):
    job_id: str
    state: Literal["idle","queued","running","done","error"] = "idle"
    progress: int = 0
    outputs: List[RenderItemOut] = Field(default_factory=list)

class ComposeImage(BaseModel):
    url: str
    duration: int
    kenburns: str
    text: str = ""
    pos: str = "bottom"

class ComposeIn(BaseModel):
    job_id: str
    images: List[ComposeImage]
    audio: str
    srt: str
    out: str

    # polish opcional
    fade_in_ms: int | None = None
    fade_out_ms: int | None = None
    loudnorm: bool | None = None
    logo_path: str | None = None
    logo_scale: int | None = None
    lut_path: str | None = None
    margin: int | None = None

class TTSIn(BaseModel):
    job_id: str
    text: str
    voice: str | None = None
    wpm: int | None = None

class TTSOut(BaseModel):
    audio_url: str
    duration_s: float

# --- QUICK CREATE MODELS ---

class QuickCreateOptions(BaseModel):
    voice: Optional[str] = None
    music: Optional[str] = None
    targets: List[str] = Field(default_factory=list)
    variations: int = Field(default=1, ge=1, le=10)

class QuickCreateRequest(BaseModel):
    mode: Literal["idea", "script"] = Field(default="idea", description="Creation mode")
    idea_text: str = Field(..., min_length=5, max_length=500, description="Base idea or script text")
    duration_label: Literal["30s", "45s", "2min", "3min"] = Field(..., description="Duration label")
    target_duration_sec: int = Field(..., ge=30, le=180, description="Target duration in seconds")
    style_key: str = Field(..., pattern=r"^[a-z_]+$", description="Style identifier")
    options: QuickCreateOptions = Field(default_factory=QuickCreateOptions)

class StyleMetadata(BaseModel):
    style_id: str
    label: str
    category: str
    description: str
    motion_type: str
    grain_level: str
    aspect_ratio: str
    processing_complexity: Literal["low", "medium", "high"] = "medium"

class TimeEstimation(BaseModel):
    total_estimated_seconds: int
    breakdown: dict = Field(default_factory=dict)
    confidence_level: Literal["low", "medium", "high"] = "medium"
    estimated_completion: Optional[str] = None

class ProcessingStep(BaseModel):
    step_id: str
    name: str
    description: str
    estimated_seconds: int
    status: Literal["pending", "running", "completed", "skipped"] = "pending"
    dependencies: List[str] = Field(default_factory=list)

class ContentPreview(BaseModel):
    suggested_scenes: List[str] = Field(default_factory=list)
    suggested_mood: Optional[str] = None
    suggested_visual_themes: List[str] = Field(default_factory=list)
    estimated_scene_count: int
    content_category: Optional[str] = None

class QueueInfo(BaseModel):
    queue_position: Optional[int] = None
    total_jobs_ahead: int = 0
    estimated_wait_seconds: int = 0
    processing_capacity: str = "normal"

class PlatformOptimization(BaseModel):
    target_platforms: List[str]
    format_optimizations: List[str]
    recommended_hashtags: List[str] = Field(default_factory=list)
    aspect_ratio_optimized: str
    audio_optimization: Optional[str] = None

class QuickCreateResponse(BaseModel):
    job_id: str
    episode_id: Optional[str] = None
    series_id: Optional[str] = None
    character_id: Optional[str] = None
    status: Literal["queued", "processing", "error"] = "queued"

    # Enhanced metadata
    style_metadata: StyleMetadata
    time_estimation: TimeEstimation
    content_preview: ContentPreview
    queue_info: QueueInfo
    platform_optimization: PlatformOptimization
    processing_steps: List[ProcessingStep] = Field(default_factory=list)

    # Original fields for compatibility
    estimated_time_sec: Optional[int] = None
    message: str

    # Additional enhanced fields
    processing_pipeline: List[str] = Field(default_factory=list)
    quality_tier: Literal["draft", "standard", "premium"] = "standard"
    content_tags: List[str] = Field(default_factory=list)
    estimated_complexity: Literal["simple", "moderate", "complex"] = "moderate"


# --- FASE 3 - EPISODE/CHARACTER/SERIES MODELS ---

class Character(BaseModel):
    character_id: str
    name: str
    visual_description: str
    personality_traits: List[str]
    style_consistency: Dict[str, str]
    created_from_idea: str


class Series(BaseModel):
    series_id: str
    name: str  # Auto-generated desde idea
    description: str
    main_character_id: str
    style_key: str
    episodes_count: int
    created_date: datetime


class Episode(BaseModel):
    episode_id: str
    series_id: str
    episode_number: int
    title: str
    idea_text: str
    duration: str
    style_key: str
    character_consistency: bool
    job_id: str
    status: str


# --- AI CHARACTER GENERATION MODELS ---

class CharacterFromIdeaRequest(BaseModel):
    idea_text: str = Field(..., min_length=5, max_length=500, description="Idea base para generar personaje")
    style_key: str = Field(..., pattern=r"^[a-z_]+$", description="Identificador del estilo visual")


class CharacterFromIdeaResponse(BaseModel):
    character: Character
    series_name: str


# --- QUICK CREATE FULL UNIVERSE MODELS ---

class QuickCreateFullUniverseRequest(BaseModel):
    idea_text: str = Field(..., min_length=5, max_length=500, description="Idea base para generar universo completo")
    duration: str = Field(..., pattern=r"^(30s|45s|2min|3min)$", description="Duración del episodio")
    style_key: str = Field(..., pattern=r"^[a-z_]+$", description="Identificador del estilo visual")
    auto_create_universe: bool = Field(default=True, description="Crear automáticamente personaje y serie")


class QuickCreateFullUniverseResponse(BaseModel):
    job_id: str
    status: str
    estimated_time_sec: Optional[int] = None
    message: Optional[str] = None
    episode: Episode
    character: Character
    series: Series