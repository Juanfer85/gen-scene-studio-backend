"""
Edge TTS Client - Microsoft Edge Text-to-Speech
FREE unlimited TTS service using Microsoft Edge voices
"""
import logging
import asyncio
from typing import List, Optional
from services.tts_provider import TTSProvider, Voice, TTSFactory

log = logging.getLogger(__name__)

# Try to import edge-tts
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    log.warning("edge-tts not installed. Install with: pip install edge-tts")


class EdgeTTSProvider(TTSProvider):
    """Microsoft Edge TTS Provider - FREE unlimited"""
    
    def __init__(self):
        self.name = "edge"
        self._voices_cache = None
    
    def is_available(self) -> bool:
        """Check if Edge TTS is available"""
        return EDGE_TTS_AVAILABLE
    
    async def generate_speech(
        self,
        text: str,
        voice_id: str,
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        **kwargs
    ) -> bytes:
        """
        Generate speech using Edge TTS
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID (e.g., "en-US-GuyNeural")
            rate: Speech rate (e.g., "+10%", "-10%")
            volume: Volume (e.g., "+10%", "-10%")
            pitch: Pitch (e.g., "+10Hz", "-10Hz")
            
        Returns:
            Audio data as bytes (MP3 format)
        """
        if not self.is_available():
            raise Exception("Edge TTS not available. Install: pip install edge-tts")
        
        try:
            log.info(f"🎙️ Generating speech with Edge TTS: {voice_id}")
            log.info(f"   Text: {text[:50]}...")
            
            # Create communicate object
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_id,
                rate=rate,
                volume=volume,
                pitch=pitch
            )
            
            # Stream audio data
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            log.info(f"✅ Generated {len(audio_data)} bytes of audio")
            return audio_data
            
        except Exception as e:
            log.error(f"❌ Edge TTS error: {e}")
            raise
    
    async def get_available_voices(self) -> List[Voice]:
        """Get all available Edge TTS voices"""
        if not self.is_available():
            return []
        
        # Use cache if available
        if self._voices_cache:
            return self._voices_cache
        
        try:
            log.info("📋 Fetching Edge TTS voices...")
            voices_data = await edge_tts.list_voices()
            
            voices = []
            for v in voices_data:
                voice = Voice(
                    id=v["ShortName"],
                    name=v["FriendlyName"],
                    gender=v["Gender"],
                    locale=v["Locale"],
                    age="adult",  # Edge doesn't provide age
                    tone=v.get("VoicePersonalities", ["neutral"])[0] if v.get("VoicePersonalities") else "neutral",
                    provider="edge",
                    preview_url=None  # We'll generate previews on demand
                )
                voices.append(voice)
            
            self._voices_cache = voices
            log.info(f"✅ Found {len(voices)} Edge TTS voices")
            return voices
            
        except Exception as e:
            log.error(f"❌ Error fetching Edge voices: {e}")
            return []
    
    async def get_voices_by_locale(self, locale: str) -> List[Voice]:
        """Get voices for a specific locale"""
        all_voices = await self.get_available_voices()
        return [v for v in all_voices if v.locale.startswith(locale)]
    
    async def get_recommended_voices(self) -> List[Voice]:
        """Get recommended high-quality voices"""
        all_voices = await self.get_available_voices()
        
        # Recommended voice IDs (high quality)
        recommended_ids = [
            # English
            "en-US-GuyNeural",      # Deep male narrator
            "en-US-AriaNeural",     # Friendly female
            "en-US-DavisNeural",    # Professional male
            "en-US-JennyNeural",    # Warm female
            "en-GB-RyanNeural",     # British male
            
            # Spanish
            "es-ES-AlvaroNeural",   # Spanish male
            "es-ES-ElviraNeural",   # Spanish female
            "es-MX-DaliaNeural",    # Mexican female
            "es-MX-JorgeNeural",    # Mexican male
        ]
        
        return [v for v in all_voices if v.id in recommended_ids]


# Register Edge TTS provider
if EDGE_TTS_AVAILABLE:
    TTSFactory.register_provider("edge", EdgeTTSProvider)
    log.info("✅ Edge TTS provider registered")
else:
    log.warning("⚠️ Edge TTS provider not available")
