"""
Tables router — Table/QR code management for branches.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_admin
from app.models.restaurant import Table

router = APIRouter()


# --- Schemas ---

class TableCreate(BaseModel):
    branch_id: uuid.UUID
    table_number: int
    capacity: int = 4

class TableResponse(BaseModel):
    id: uuid.UUID
    table_number: int
    capacity: int
    status: str
    qr_code_url: Optional[str]

    class Config:
        from_attributes = True


# --- Endpoints ---

@router.get("/branch/{branch_id}", summary="Filial stollari")
async def list_tables(
    branch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return [
        { "id": "1", "table_number": 1, "capacity": 4, "status": "available" },
        { "id": "2", "table_number": 2, "capacity": 2, "status": "occupied", "current_order": "#1045", "time_seated": "14:20" },
        { "id": "3", "table_number": 3, "capacity": 6, "status": "reserved", "time_seated": "18:00" },
        { "id": "4", "table_number": 4, "capacity": 4, "status": "available" },
        { "id": "5", "table_number": 5, "capacity": 8, "status": "occupied", "current_order": "#1046", "time_seated": "14:45" },
        { "id": "6", "table_number": 6, "capacity": 2, "status": "available" },
    ]


@router.post("/", summary="Stol qo'shish", dependencies=[Depends(allow_admin)])
async def create_table(
    body: TableCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # Generate QR code URL (placeholder for QR generator integration)
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data=table-{body.branch_id}-{body.table_number}&size=300x300"

    table = Table(
        branch_id=body.branch_id,
        table_number=body.table_number,
        capacity=body.capacity,
        qr_code_url=qr_url,
    )
    db.add(table)
    await db.commit()
    await db.refresh(table)
    return table


@router.put("/{table_id}/status", summary="Stol holatini o'zgartirish")
async def update_table_status(
    table_id: uuid.UUID,
    new_status: str,  # AVAILABLE, OCCUPIED, RESERVED
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(select(Table).where(Table.id == table_id))
    table = result.scalar_one_or_none()
    if not table:
        raise HTTPException(status_code=404, detail="Stol topilmadi")
    table.status = new_status.upper()
    await db.commit()
    return {"detail": f"Stol #{table.table_number} statusi: {new_status}"}
