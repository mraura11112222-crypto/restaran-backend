"""
Fleet router — Drone/Robot/Vehicle fleet management and delivery routing.
"""

import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_admin
from app.models.fleet import DeliveryFleet, DeliveryRoute

router = APIRouter()


# --- Schemas ---

class FleetVehicleCreate(BaseModel):
    restaurant_id: uuid.UUID
    vehicle_type: str  # CAR, BIKE, DRONE, ROBOT
    license_plate: Optional[str] = None

class FleetVehicleResponse(BaseModel):
    id: uuid.UUID
    vehicle_type: str
    status: str
    current_lat: Optional[float]
    current_lng: Optional[float]

    class Config:
        from_attributes = True

class RouteAssign(BaseModel):
    fleet_id: uuid.UUID
    order_id: uuid.UUID
    estimated_arrival: Optional[datetime] = None

class LocationUpdate(BaseModel):
    lat: float
    lng: float


# --- Fleet Endpoints ---

@router.get("/vehicles/{restaurant_id}", summary="Avtopark ro'yxati", dependencies=[Depends(allow_admin)])
async def list_fleet(
    restaurant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return [
        {
          "id": "1",
          "name": "Drone-01",
          "type": "drone",
          "status": "delivering",
          "battery": 85,
          "location": { "lat": 41.311081, "lng": 69.240562 },
          "current_order": "#1042",
          "distance_km": 1.2
        },
        {
          "id": "2",
          "name": "Robot-01",
          "type": "robot",
          "status": "idle",
          "battery": 100,
          "location": { "lat": 41.312081, "lng": 69.241562 },
          "distance_km": 0
        },
        {
          "id": "3",
          "name": "Scooter-01",
          "type": "scooter",
          "status": "charging",
          "battery": 15,
          "location": { "lat": 41.310081, "lng": 69.239562 },
          "distance_km": 0
        }
    ]


@router.post("/vehicles", summary="Transport qo'shish", dependencies=[Depends(allow_admin)])
async def add_vehicle(
    body: FleetVehicleCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    vehicle = DeliveryFleet(
        restaurant_id=body.restaurant_id,
        vehicle_type=body.vehicle_type.upper(),
        license_plate=body.license_plate,
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


@router.put("/vehicles/{vehicle_id}/location", summary="GPS lokatsiyani yangilash")
async def update_vehicle_location(
    vehicle_id: uuid.UUID,
    body: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(select(DeliveryFleet).where(DeliveryFleet.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Transport topilmadi")
    vehicle.current_lat = body.lat
    vehicle.current_lng = body.lng
    vehicle.last_ping = datetime.utcnow()
    await db.commit()
    return {"detail": "Lokatsiya yangilandi"}


@router.put("/vehicles/{vehicle_id}/status", summary="Transport holatini o'zgartirish", dependencies=[Depends(allow_admin)])
async def update_vehicle_status(
    vehicle_id: uuid.UUID,
    new_status: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(select(DeliveryFleet).where(DeliveryFleet.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Transport topilmadi")
    vehicle.status = new_status.upper()
    await db.commit()
    return {"detail": f"Status {new_status} ga o'zgartirildi"}


# --- Route Endpoints ---

@router.post("/routes", summary="Marshrutni biriktirish", dependencies=[Depends(allow_admin)])
async def assign_route(
    body: RouteAssign,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    route = DeliveryRoute(
        fleet_id=body.fleet_id,
        order_id=body.order_id,
        estimated_arrival=body.estimated_arrival,
        route_status="IN_PROGRESS",
    )
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return route


@router.put("/routes/{route_id}/complete", summary="Marshrutni yakunlash")
async def complete_route(
    route_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(select(DeliveryRoute).where(DeliveryRoute.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Marshrut topilmadi")
    route.route_status = "COMPLETED"
    await db.commit()
    return {"detail": "Marshrut yakunlandi"}
