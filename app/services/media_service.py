"""
Media service — Cloudinary upload/delete for images and videos.
"""

import uuid
from datetime import datetime
from typing import Optional

import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import BadRequestException, NotFoundException

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

# Allowed file types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB


class MediaService:
    """Handles file uploads to Cloudinary and metadata storage in DB."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_image(
        self,
        file: UploadFile,
        restaurant_id: uuid.UUID,
        entity_type: str = "general",
        entity_id: Optional[uuid.UUID] = None,
    ) -> "Media":
        """
        Upload an image to Cloudinary and store metadata in DB.
        Supports: JPEG, PNG, WebP, GIF (max 10MB).
        """
        from app.models.media import Media, MediaType

        # Validate file type
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise BadRequestException(
                f"Rasm formati qo'llab-quvvatlanmaydi: {file.content_type}. "
                f"Ruxsat etilgan: JPEG, PNG, WebP, GIF"
            )

        # Read file content
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_IMAGE_SIZE:
            raise BadRequestException("Rasm hajmi 10MB dan oshmasligi kerak")

        # Upload to Cloudinary
        folder = f"restaurants/{restaurant_id}/{entity_type}"
        result = cloudinary.uploader.upload(
            content,
            folder=folder,
            resource_type="image",
            transformation=[
                {"quality": "auto", "fetch_format": "auto"},
                {"width": 1200, "crop": "limit"},
            ],
        )

        # Save metadata to DB
        media = Media(
            id=uuid.uuid4(),
            restaurant_id=restaurant_id,
            url=result["secure_url"],
            public_id=result["public_id"],
            media_type=MediaType.IMAGE,
            entity_type=entity_type,
            entity_id=entity_id,
            file_size=file_size,
            created_at=datetime.utcnow(),
        )
        self.db.add(media)
        await self.db.flush()

        return media

    async def upload_video(
        self,
        file: UploadFile,
        restaurant_id: uuid.UUID,
        entity_type: str = "general",
        entity_id: Optional[uuid.UUID] = None,
    ) -> "Media":
        """
        Upload a video to Cloudinary and store metadata in DB.
        Supports: MP4, WebM, QuickTime (max 100MB).
        """
        from app.models.media import Media, MediaType

        if file.content_type not in ALLOWED_VIDEO_TYPES:
            raise BadRequestException(
                f"Video formati qo'llab-quvvatlanmaydi: {file.content_type}. "
                f"Ruxsat etilgan: MP4, WebM, MOV"
            )

        content = await file.read()
        file_size = len(content)

        if file_size > MAX_VIDEO_SIZE:
            raise BadRequestException("Video hajmi 100MB dan oshmasligi kerak")

        folder = f"restaurants/{restaurant_id}/{entity_type}"
        result = cloudinary.uploader.upload(
            content,
            folder=folder,
            resource_type="video",
            eager=[
                {"format": "mp4", "video_codec": "h264", "quality": "auto"},
            ],
            eager_async=True,
        )

        media = Media(
            id=uuid.uuid4(),
            restaurant_id=restaurant_id,
            url=result["secure_url"],
            public_id=result["public_id"],
            media_type=MediaType.VIDEO,
            entity_type=entity_type,
            entity_id=entity_id,
            file_size=file_size,
            created_at=datetime.utcnow(),
        )
        self.db.add(media)
        await self.db.flush()

        return media

    async def delete_media(self, media_id: uuid.UUID, restaurant_id: uuid.UUID) -> bool:
        """Delete media from Cloudinary and DB."""
        from app.models.media import Media

        result = await self.db.execute(
            select(Media).where(
                Media.id == media_id,
                Media.restaurant_id == restaurant_id,
            )
        )
        media = result.scalar_one_or_none()
        if not media:
            raise NotFoundException("Media topilmadi")

        # Delete from Cloudinary
        resource_type = "video" if media.media_type.value == "VIDEO" else "image"
        try:
            cloudinary.uploader.destroy(media.public_id, resource_type=resource_type)
        except Exception:
            pass  # Continue even if Cloudinary delete fails

        # Delete from DB
        await self.db.delete(media)
        await self.db.flush()
        return True

    async def get_media_list(
        self,
        restaurant_id: uuid.UUID,
        entity_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """Get paginated media list for a restaurant."""
        from app.models.media import Media
        from sqlalchemy import func

        query = select(Media).where(Media.restaurant_id == restaurant_id)
        if entity_type:
            query = query.where(Media.entity_type == entity_type)

        # Count
        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        # Paginate
        query = query.order_by(Media.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {
            "items": items,
            "total": total,
        }
