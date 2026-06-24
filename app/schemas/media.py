"""Media / file upload Pydantic v2 schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MediaUploadResponse(BaseModel):
    """Schema returned after a successful file upload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str = Field(..., description="Public URL of the uploaded file")
    public_id: str = Field(
        ..., description="Cloud storage public ID (e.g. Cloudinary)"
    )
    media_type: str = Field(
        ..., description="MIME type or category: image, video, etc."
    )
    entity_type: str = Field(
        ...,
        description="Entity this media belongs to (menu_item, category …)",
    )
    entity_id: UUID = Field(..., description="ID of the owning entity")
    file_size: Optional[int] = Field(
        default=None, ge=0, description="File size in bytes"
    )
    created_at: datetime


class MediaListResponse(BaseModel):
    """Paginated list of media items."""

    items: List[MediaUploadResponse] = Field(default_factory=list)
    total: int = Field(default=0, description="Total matching items")
