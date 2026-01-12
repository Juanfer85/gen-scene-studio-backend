from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env"],
        extra="ignore",
        case_sensitive=False
    )

    # Environment
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = Field(default=False, env="DEBUG")

    # API Configuration
    KIE_API_KEY: str = Field(..., env="KIE_API_KEY") # Required
    ELEVEN_API_KEY: Optional[str] = Field(default="", env="ELEVEN_API_KEY") # Optional
    ELEVEN_VOICE_ID: str = Field(default="21m00Tcm4TlvDq8ikWAM", env="ELEVEN_VOICE_ID")
    BACKEND_BASE_URL: str = Field(default="http://localhost:8000", env="BACKEND_BASE_URL")

    # ... (skipping unchanged lines)

    # Security
    BACKEND_API_KEY: str = Field(..., env="BACKEND_API_KEY") # Required
    CORS_ALLOW_ORIGINS: str = Field(default="*", env="CORS_ALLOW_ORIGINS")
    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES: int = Field(default=60, env="JWT_EXPIRE_MINUTES")

    # Video Composition
    COMPOSE_FADE_IN_MS: int = Field(default=500, env="COMPOSE_FADE_IN_MS")
    COMPOSE_FADE_OUT_MS: int = Field(default=500, env="COMPOSE_FADE_OUT_MS")
    COMPOSE_AUDIO_LOUDNORM: bool = Field(default=True, env="COMPOSE_AUDIO_LOUDNORM")
    COMPOSE_LOGO_PATH: str = Field(default="", env="COMPOSE_LOGO_PATH")
    COMPOSE_LOGO_SCALE: int = Field(default=320, env="COMPOSE_LOGO_SCALE")
    COMPOSE_LUT_PATH: str = Field(default="", env="COMPOSE_LUT_PATH")
    COMPOSE_MARGIN: int = Field(default=24, env="COMPOSE_MARGIN")
    COMPOSE_WIDTH: int = Field(default=1080, env="COMPOSE_WIDTH")
    COMPOSE_HEIGHT: int = Field(default=1920, env="COMPOSE_HEIGHT")
    COMPOSE_FPS: int = Field(default=30, env="COMPOSE_FPS")
    COMPOSE_CRF: int = Field(default=18, env="COMPOSE_CRF")
    COMPOSE_PRESET: str = Field(default="veryfast", env="COMPOSE_PRESET")
    COMPOSE_PROFILE: str = Field(default="high", env="COMPOSE_PROFILE")
    COMPOSE_FASTSTART: bool = Field(default=True, env="COMPOSE_FASTSTART")

    # Audio Configuration
    AUDIO_SAMPLE_RATE: int = Field(default=48000, env="AUDIO_SAMPLE_RATE")
    AUDIO_BITRATE: str = Field(default="AAC_192K", env="AUDIO_BITRATE")
    AUDIO_CHANNELS: int = Field(default=2, env="AUDIO_CHANNELS")

    # TTS Configuration
    TTS_PROVIDER: str = Field(default="piper", env="TTS_PROVIDER")
    PIPER_MODEL: str = Field(default="es_ES-carlfm-high.onnx", env="PIPER_MODEL")
    PIPER_SPEAKER_ID: int = Field(default=0, env="PIPER_SPEAKER_ID")
    PIPER_SPEED: float = Field(default=1.0, env="PIPER_SPEED")
    TTS_WPM: int = Field(default=160, env="TTS_WPM")

    # Features and Options
    SAFE_COMPOSE: bool = Field(default=True, env="SAFE_COMPOSE")
    THUMBNAIL_ENABLE: bool = Field(default=True, env="THUMBNAIL_ENABLE")
    RETENTION_DAYS: int = Field(default=14, env="RETENTION_DAYS")

    # Webhook notifications
    NOTIFY_URL: str = Field(default="", env="NOTIFY_URL")
    NOTIFY_SECRET: str = Field(default="change-me-super-secret", env="NOTIFY_SECRET")
    NOTIFY_EVENTS: str = Field(default="render_done,compose_done", env="NOTIFY_EVENTS")
    ALLOW_DEBUG: bool = Field(default=False, env="ALLOW_DEBUG")

    # Performance Monitoring
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    METRICS_REDIS_PREFIX: str = Field(default="metrics:", env="METRICS_REDIS_PREFIX")
    METRICS_RETENTION_HOURS: int = Field(default=24, env="METRICS_RETENTION_HOURS")
    SLOW_QUERY_THRESHOLD: float = Field(default=1.0, env="SLOW_QUERY_THRESHOLD")

    # Health Check Configuration
    HEALTH_CHECK_INTERVAL: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    HEALTH_CHECK_TIMEOUT: int = Field(default=10, env="HEALTH_CHECK_TIMEOUT")
    HEALTH_CHECK_RETRIES: int = Field(default=3, env="HEALTH_CHECK_RETRIES")

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for SQLAlchemy"""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL
        elif self.DATABASE_URL.startswith("sqlite://"):
            return self.DATABASE_URL
        # Construct PostgreSQL URL if individual components are provided
        if not self.DATABASE_URL.startswith("sqlite://"):
            return (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self.DATABASE_URL

    @property
    def database_url_async(self) -> str:
        """Get asynchronous database URL for asyncpg"""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        elif self.DATABASE_URL.startswith("sqlite://"):
            return self.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
        # Construct async PostgreSQL URL
        if not self.DATABASE_URL.startswith("sqlite://"):
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

    @property
    def redis_url(self) -> str:
        """Get Redis URL with password if provided"""
        if self.REDIS_URL and self.REDIS_URL != "redis://localhost:6379/0":
            return self.REDIS_URL

        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        if not self.CORS_ALLOW_ORIGINS or self.CORS_ALLOW_ORIGINS == "*":
            return ["*"]
        results = []
        for origin in self.CORS_ALLOW_ORIGINS.split(","):
             clean_origin = origin.strip()
             if clean_origin: 
                  results.append(clean_origin)
        return results

settings = Settings()

# Ensure required directories exist
os.makedirs(settings.MEDIA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.RATE_LIMIT_DB_PATH), exist_ok=True)