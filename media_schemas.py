"""
Media Options Schemas
Pydantic models for voice, music, and subtitle requests/responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ============================================================================
# VOICE SCHEMAS
# ============================================================================

class VoiceInfo(BaseModel):
    """Voice information"""
    id: str
    name: str
    gender: str
    locale: str
    age: str
    tone: str
    provider: str
    preview_url: Optional[str] = None
    use_cases: Optional[List[str]] = None


class VoicesByStyleResponse(BaseModel):
    """Response for voices by style"""
    success: bool = True
    style: str
    style_name: str
    description: str
    voices: List[VoiceInfo]
    default_voice: str


class VoicePreviewRequest(BaseModel):
    """Request to generate voice preview"""
    voice_id: str
    text: str = Field(
        default="This is a preview of the voice",
        max_length=200,
        description="Text to preview (max 200 characters)"
    )
    rate: str = Field(default="+0%", description="Speech rate")
    volume: str = Field(default="+0%", description="Volume")
    pitch: str = Field(default="+0Hz", description="Pitch")


# ============================================================================
# MUSIC SCHEMAS
# ============================================================================

class MusicTrackInfo(BaseModel):
    """Music track information"""
    id: str
    name: str
    description: str
    mood: str
    tempo: str
    duration: str
    preview_url: Optional[str] = None
    full_url: Optional[str] = None
    volume: float = Field(default=0.3, ge=0.0, le=1.0)


class MusicByStyleResponse(BaseModel):
    """Response for music by style"""
    success: bool = True
    style: str
    style_name: str
    tracks: List[MusicTrackInfo]
    default_track: str


# ============================================================================
# SUBTITLE SCHEMAS
# ============================================================================

class SubtitleStyleConfig(BaseModel):
    """Subtitle style configuration"""
    position: str
    font_family: str
    font_size: str
    font_weight: str
    text_color: str
    stroke_color: str
    stroke_width: str
    background_color: str
    text_align: str
    max_width: str
    animation: str
    shadow: str
    background_padding: Optional[str] = None
    background_radius: Optional[str] = None
    background_border: Optional[str] = None
    text_transform: Optional[str] = None
    letter_spacing: Optional[str] = None
    word_highlight: Optional[bool] = None
    highlight_color: Optional[str] = None
    highlight_scale: Optional[str] = None
    text_shadow: Optional[str] = None
    fill_color: Optional[str] = None


class SubtitleStyleInfo(BaseModel):
    """Subtitle style information"""
    id: str
    name: str
    description: str
    preview_image: str
    config: SubtitleStyleConfig


class SubtitleStylesResponse(BaseModel):
    """Response for subtitle styles"""
    success: bool = True
    styles: List[SubtitleStyleInfo]
    default_style: str


# ============================================================================
# VIDEO GENERATION WITH MEDIA OPTIONS
# ============================================================================

class MediaOptionsRequest(BaseModel):
    """Media options for video generation"""
    voice_id: Optional[str] = Field(
        default=None,
        description="Voice ID for narration"
    )
    narration_text: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Text to narrate (max 500 characters)"
    )
    music_track_id: Optional[str] = Field(
        default=None,
        description="Music track ID"
    )
    music_volume: Optional[float] = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Music volume (0.0 to 1.0)"
    )
    subtitle_style: Optional[str] = Field(
        default=None,
        description="Subtitle style ID"
    )
    subtitle_text: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Subtitle text (if different from narration)"
    )


class QuickCreateWithMediaRequest(BaseModel):
    """Quick create request with media options"""
    idea_text: str = Field(..., min_length=3, max_length=500)
    style_key: str = Field(default="default")
    video_duration: int = Field(default=5, ge=3, le=10)
    video_quality: str = Field(default="720p")
    aspect_ratio: str = Field(default="9:16")
    video_model: Optional[str] = None
    
    # Media options (optional)
    media_options: Optional[MediaOptionsRequest] = None


# ============================================================================
# PROVIDER INFO
# ============================================================================

class ProviderInfo(BaseModel):
    """TTS Provider information"""
    name: str
    display_name: str
    is_available: bool
    is_free: bool
    description: str


class ProvidersResponse(BaseModel):
    """Response for available providers"""
    success: bool = True
    providers: List[ProviderInfo]
    default_provider: str
    current_provider: str
