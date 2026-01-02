"""
Text-to-Speech Provider System
Modular TTS system with support for multiple providers (Edge TTS, ElevenLabs, Google)
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class Voice:
    """Voice configuration"""
    id: str
    name: str
    gender: str
    locale: str
    age: str
    tone: str
    provider: str
    preview_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "locale": self.locale,
            "age": self.age,
            "tone": self.tone,
            "provider": self.provider,
            "preview_url": self.preview_url
        }


class TTSProvider(ABC):
    """Base class for TTS providers"""
    
    @abstractmethod
    async def generate_speech(
        self,
        text: str,
        voice_id: str,
        **kwargs
    ) -> bytes:
        """
        Generate speech from text
        
        Args:
            text: Text to convert to speech
            voice_id: Voice identifier
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Audio data as bytes (MP3 format)
        """
        pass
    
    @abstractmethod
    async def get_available_voices(self) -> List[Voice]:
        """
        Get list of available voices
        
        Returns:
            List of Voice objects
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available/configured"""
        pass


class TTSFactory:
    """Factory for creating TTS providers"""
    
    _providers = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class):
        """Register a TTS provider"""
        cls._providers[name] = provider_class
    
    @classmethod
    def get_provider(cls, provider_name: str = "edge") -> TTSProvider:
        """
        Get TTS provider instance
        
        Args:
            provider_name: Provider name ("edge", "elevenlabs", "google")
            
        Returns:
            TTSProvider instance
        """
        if provider_name not in cls._providers:
            log.warning(f"Provider {provider_name} not found, falling back to edge")
            provider_name = "edge"
        
        provider_class = cls._providers.get(provider_name)
        if provider_class:
            return provider_class()
        
        raise ValueError(f"No TTS provider available")
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of registered providers"""
        return list(cls._providers.keys())


# Default provider selection based on environment
def get_default_provider() -> str:
    """
    Get default TTS provider based on environment configuration
    
    Priority:
    1. ELEVENLABS_API_KEY -> elevenlabs (premium)
    2. GOOGLE_APPLICATION_CREDENTIALS -> google (free tier)
    3. Always available -> edge (free unlimited)
    """
    if os.getenv("ELEVENLABS_API_KEY"):
        return "elevenlabs"
    elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return "google"
    else:
        return "edge"  # Default to free unlimited
