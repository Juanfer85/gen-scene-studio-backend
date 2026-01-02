"""
Media Options API Endpoints
REST API for voices, music, and subtitles
"""
import os
import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional
import io

# Import schemas (will be in models/)
try:
    from models.media_schemas import (
        VoicesByStyleResponse,
        VoiceInfo,
        VoicePreviewRequest,
        MusicByStyleResponse,
        MusicTrackInfo,
        SubtitleStylesResponse,
        SubtitleStyleInfo,
        SubtitleStyleConfig,
        ProvidersResponse,
        ProviderInfo
    )
except ImportError:
    # Fallback for development
    from media_schemas import (
        VoicesByStyleResponse,
        VoiceInfo,
        VoicePreviewRequest,
        MusicByStyleResponse,
        MusicTrackInfo,
        SubtitleStylesResponse,
        SubtitleStyleInfo,
        SubtitleStyleConfig,
        ProvidersResponse,
        ProviderInfo
    )

# Import TTS provider
try:
    from services.tts_provider import TTSFactory, get_default_provider
    from services.edge_tts_client import EdgeTTSProvider
except ImportError:
    TTSFactory = None
    EdgeTTSProvider = None

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["media"])


# ============================================================================
# VOICE ENDPOINTS
# ============================================================================

def load_voice_library():
    """Load voice library from JSON file"""
    try:
        # Try multiple locations
        possible_paths = [
            Path(__file__).parent.parent / "data" / "voices" / "voice_library.json",
            Path("voice_library.json"),
            Path("data/voices/voice_library.json"),
        ]
        
        for path in possible_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        log.warning("Voice library not found, using default")
        return {"styles": {}, "default_provider": "edge"}
    except Exception as e:
        log.error(f"Error loading voice library: {e}")
        return {"styles": {}, "default_provider": "edge"}


@router.get("/voices/{style_key}", response_model=VoicesByStyleResponse)
async def get_voices_by_style(style_key: str):
    """
    Get available voices for a specific video style
    
    Args:
        style_key: Video style (e.g., "cinematic_realism", "cyberpunk")
        
    Returns:
        List of voices suitable for that style
    """
    try:
        library = load_voice_library()
        
        # Get style or default
        style_data = library.get("styles", {}).get(style_key)
        if not style_data:
            style_data = library.get("styles", {}).get("default", {})
            style_key = "default"
        
        # Convert to VoiceInfo objects
        voices = []
        for voice_data in style_data.get("voices", []):
            voice = VoiceInfo(**voice_data)
            voices.append(voice)
        
        return VoicesByStyleResponse(
            style=style_key,
            style_name=style_data.get("name", style_key),
            description=style_data.get("description", ""),
            voices=voices,
            default_voice=style_data.get("default_voice", voices[0].id if voices else "")
        )
        
    except Exception as e:
        log.error(f"Error getting voices for style {style_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview-voice")
async def preview_voice(request: VoicePreviewRequest):
    """
    Generate a preview of a voice
    
    Args:
        request: Voice preview request with voice_id and text
        
    Returns:
        Audio file (MP3)
    """
    try:
        if not TTSFactory:
            raise HTTPException(status_code=503, detail="TTS service not available")
        
        # Get TTS provider
        provider = TTSFactory.get_provider("edge")
        
        if not provider.is_available():
            raise HTTPException(status_code=503, detail="TTS provider not available")
        
        # Generate speech
        log.info(f"Generating preview for voice: {request.voice_id}")
        audio_data = await provider.generate_speech(
            text=request.text,
            voice_id=request.voice_id,
            rate=request.rate,
            volume=request.volume,
            pitch=request.pitch
        )
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=preview_{request.voice_id}.mp3"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error generating voice preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices/all/list")
async def get_all_voices():
    """Get all available voices across all styles"""
    try:
        library = load_voice_library()
        
        all_voices = []
        seen_ids = set()
        
        for style_key, style_data in library.get("styles", {}).items():
            for voice_data in style_data.get("voices", []):
                voice_id = voice_data.get("id")
                if voice_id not in seen_ids:
                    voice = VoiceInfo(**voice_data)
                    all_voices.append(voice)
                    seen_ids.add(voice_id)
        
        return {
            "success": True,
            "total": len(all_voices),
            "voices": all_voices
        }
        
    except Exception as e:
        log.error(f"Error getting all voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MUSIC ENDPOINTS
# ============================================================================

def load_music_library():
    """Load music library from JSON file"""
    try:
        possible_paths = [
            Path(__file__).parent.parent / "data" / "music" / "music_library.json",
            Path("music_library.json"),
            Path("data/music/music_library.json"),
        ]
        
        for path in possible_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        log.warning("Music library not found, using empty")
        return {"styles": {}}
    except Exception as e:
        log.error(f"Error loading music library: {e}")
        return {"styles": {}}


@router.get("/music/{style_key}", response_model=MusicByStyleResponse)
async def get_music_by_style(style_key: str):
    """
    Get available music tracks for a specific video style
    
    Args:
        style_key: Video style
        
    Returns:
        List of music tracks suitable for that style
    """
    try:
        library = load_music_library()
        
        # Get style or default
        style_data = library.get("styles", {}).get(style_key)
        if not style_data:
            style_data = library.get("styles", {}).get("default", {})
            style_key = "default"
        
        # Convert to MusicTrackInfo objects
        tracks = []
        for track_data in style_data.get("music_tracks", []):
            track = MusicTrackInfo(**track_data)
            tracks.append(track)
        
        return MusicByStyleResponse(
            style=style_key,
            style_name=style_data.get("name", style_key),
            tracks=tracks,
            default_track=style_data.get("default_track", tracks[0].id if tracks else "")
        )
        
    except Exception as e:
        log.error(f"Error getting music for style {style_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SUBTITLE ENDPOINTS
# ============================================================================

def load_subtitle_styles():
    """Load subtitle styles from JSON file"""
    try:
        possible_paths = [
            Path(__file__).parent.parent / "data" / "subtitles" / "subtitle_styles.json",
            Path("subtitle_styles.json"),
            Path("data/subtitles/subtitle_styles.json"),
        ]
        
        for path in possible_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        log.warning("Subtitle styles not found, using empty")
        return {"styles": [], "default_style": "classic"}
    except Exception as e:
        log.error(f"Error loading subtitle styles: {e}")
        return {"styles": [], "default_style": "classic"}


@router.get("/subtitle-styles", response_model=SubtitleStylesResponse)
async def get_subtitle_styles():
    """
    Get all available subtitle styles
    
    Returns:
        List of subtitle styles with configurations
    """
    try:
        data = load_subtitle_styles()
        
        # Convert to SubtitleStyleInfo objects
        styles = []
        for style_data in data.get("styles", []):
            config = SubtitleStyleConfig(**style_data.get("config", {}))
            style = SubtitleStyleInfo(
                id=style_data.get("id"),
                name=style_data.get("name"),
                description=style_data.get("description"),
                preview_image=style_data.get("preview_image"),
                config=config
            )
            styles.append(style)
        
        return SubtitleStylesResponse(
            styles=styles,
            default_style=data.get("default_style", "classic")
        )
        
    except Exception as e:
        log.error(f"Error getting subtitle styles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROVIDER INFO ENDPOINTS
# ============================================================================

@router.get("/tts-providers", response_model=ProvidersResponse)
async def get_tts_providers():
    """Get information about available TTS providers"""
    try:
        if not TTSFactory:
            return ProvidersResponse(
                providers=[],
                default_provider="edge",
                current_provider="none"
            )
        
        providers = []
        
        # Edge TTS
        providers.append(ProviderInfo(
            name="edge",
            display_name="Microsoft Edge TTS",
            is_available=True,
            is_free=True,
            description="Free unlimited TTS with 400+ voices"
        ))
        
        # ElevenLabs (if configured)
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        providers.append(ProviderInfo(
            name="elevenlabs",
            display_name="ElevenLabs",
            is_available=bool(elevenlabs_key),
            is_free=False,
            description="Premium quality TTS (requires API key)"
        ))
        
        # Google TTS (if configured)
        google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        providers.append(ProviderInfo(
            name="google",
            display_name="Google Cloud TTS",
            is_available=bool(google_creds),
            is_free=True,
            description="Google TTS with free tier"
        ))
        
        default = get_default_provider()
        
        return ProvidersResponse(
            providers=providers,
            default_provider=default,
            current_provider=default
        )
        
    except Exception as e:
        log.error(f"Error getting TTS providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/media/health")
async def media_health():
    """Health check for media services"""
    return {
        "success": True,
        "services": {
            "tts": TTSFactory is not None,
            "voice_library": load_voice_library() is not None,
            "music_library": load_music_library() is not None,
            "subtitle_styles": load_subtitle_styles() is not None
        }
    }
