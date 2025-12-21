from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class JobState(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"

class RenderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class RenderQuality(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"

class Job(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    state: JobState = Field(default=JobState.QUEUED, description="Current job state")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    created_at: int = Field(description="Creation timestamp")
    updated_at: Optional[int] = Field(None, description="Last update timestamp")

    class Config:
        use_enum_values = True

class Render(BaseModel):
    job_id: str = Field(..., description="Associated job ID")
    item_id: str = Field(..., description="Unique item identifier within job")
    hash: str = Field(..., description="Content hash for caching")
    quality: RenderQuality = Field(description="Render quality level")
    url: Optional[str] = Field(None, description="Render output URL")
    status: RenderStatus = Field(default=RenderStatus.PENDING, description="Render status")
    created_at: Optional[int] = Field(None, description="Creation timestamp")
    updated_at: Optional[int] = Field(None, description="Last update timestamp")

    class Config:
        use_enum_values = True

class AssetsCache(BaseModel):
    hash: str = Field(..., description="Content hash as primary key")
    url: str = Field(..., description="Cached asset URL")
    created_at: int = Field(description="Cache creation timestamp")

    class Config:
        use_enum_values = True