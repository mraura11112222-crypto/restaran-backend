"""Media model – загруженные файлы (Cloudinary)."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class MediaType(str, enum.Enum):
    """Тип медиафайла."""

    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class Media(Base):
    """Uploaded media file stored in Cloudinary."""

    __tablename__ = "media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url = Column(String(1024), nullable=False)
    public_id = Column(String(255), nullable=False, comment="Cloudinary public_id")
    media_type = Column(
        SAEnum(MediaType, name="media_type", create_constraint=True),
        nullable=False,
    )
    entity_type = Column(
        String(50), nullable=False, comment="e.g. menu_item, restaurant, category"
    )
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    file_size = Column(Integer, nullable=True, comment="Size in bytes")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # --- Relationships ---
    restaurant = relationship("Restaurant", back_populates="media")

    def __repr__(self) -> str:
        return f"<Media {self.media_type} entity={self.entity_type}:{self.entity_id}>"
