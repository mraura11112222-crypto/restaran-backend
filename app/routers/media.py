"""
Media router — image and video upload/delete via Cloudinary.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_admin
from app.services.media_service import MediaService

router = APIRouter()


@router.post(
    "/upload/image",
    status_code=status.HTTP_201_CREATED,
    summary="Rasm yuklash",
    dependencies=[Depends(allow_admin)],
)
async def upload_image(
    file: UploadFile = File(..., description="Rasm fayli (JPEG, PNG, WebP, GIF — max 10MB)"),
    entity_type: str = Form(default="general", description="Nima uchun: menu_item, restaurant, review"),
    entity_id: Optional[uuid.UUID] = Form(default=None, description="Tegishli element ID"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Rasmni Cloudinary'ga yuklash.
    Avtomatik ravishda optimize va resize qilinadi.
    """
    service = MediaService(db)
    media = await service.upload_image(
        file=file,
        restaurant_id=current_user.restaurant_id,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return {
        "id": str(media.id),
        "url": media.url,
        "public_id": media.public_id,
        "media_type": media.media_type.value,
        "entity_type": media.entity_type,
        "file_size": media.file_size,
        "message": "Rasm muvaffaqiyatli yuklandi ✅",
    }


@router.post(
    "/upload/video",
    status_code=status.HTTP_201_CREATED,
    summary="Video yuklash",
    dependencies=[Depends(allow_admin)],
)
async def upload_video(
    file: UploadFile = File(..., description="Video fayli (MP4, WebM, MOV — max 100MB)"),
    entity_type: str = Form(default="general", description="Nima uchun: menu_item, restaurant"),
    entity_id: Optional[uuid.UUID] = Form(default=None, description="Tegishli element ID"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Videoni Cloudinary'ga yuklash.
    Avtomatik MP4/H264 formatga konvertatsiya.
    """
    service = MediaService(db)
    media = await service.upload_video(
        file=file,
        restaurant_id=current_user.restaurant_id,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return {
        "id": str(media.id),
        "url": media.url,
        "public_id": media.public_id,
        "media_type": media.media_type.value,
        "entity_type": media.entity_type,
        "file_size": media.file_size,
        "message": "Video muvaffaqiyatli yuklandi ✅",
    }


@router.delete(
    "/{media_id}",
    summary="Media o'chirish",
    dependencies=[Depends(allow_admin)],
)
async def delete_media(
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Rasm yoki videoni Cloudinary va bazadan o'chirish."""
    service = MediaService(db)
    await service.delete_media(media_id, current_user.restaurant_id)
    return {"message": "Media o'chirildi ✅"}


@router.get(
    "/gallery",
    summary="Barcha media",
)
async def get_gallery(
    entity_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Restoran media galereyasi (rasmlar va videolar)."""
    service = MediaService(db)
    result = await service.get_media_list(
        restaurant_id=current_user.restaurant_id,
        entity_type=entity_type,
        page=page,
        per_page=per_page,
    )
    return {
        "items": [
            {
                "id": str(m.id),
                "url": m.url,
                "media_type": m.media_type.value,
                "entity_type": m.entity_type,
                "file_size": m.file_size,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in result["items"]
        ],
        "total": result["total"],
    }
