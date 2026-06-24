"""
Support router — Customer & Restaurant support tickets.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_admin
from app.models.support import SupportTicket

router = APIRouter()


# --- Schemas ---

class TicketCreate(BaseModel):
    restaurant_id: Optional[uuid.UUID] = None
    subject: str
    message: str

class TicketResponse(BaseModel):
    id: uuid.UUID
    subject: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Endpoints ---

@router.post("/tickets", summary="Murojaat yaratish", response_model=TicketResponse)
async def create_ticket(
    body: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    ticket = SupportTicket(
        user_id=current_user.id,
        restaurant_id=body.restaurant_id,
        subject=body.subject,
        message=body.message,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/tickets/my", summary="Mening murojaatlarim")
async def my_tickets(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/tickets/all/{restaurant_id}", summary="Barcha murojaatlar", dependencies=[Depends(allow_admin)])
async def all_tickets(
    restaurant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.restaurant_id == restaurant_id)
    )
    return result.scalars().all()


@router.put("/tickets/{ticket_id}/resolve", summary="Murojaatni yopish", dependencies=[Depends(allow_admin)])
async def resolve_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Murojaat topilmadi")
    ticket.status = "CLOSED"
    ticket.resolved_at = datetime.utcnow()
    await db.commit()
    return {"detail": "Murojaat yopildi"}
