"""
HR Extended router — Skill Matrix, Staff Training, Recruitment.
"""

import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_admin
from app.models.hr_extended import SkillMatrix, StaffTraining, RecruitmentCandidate

router = APIRouter()


# --- Schemas ---

class SkillEntry(BaseModel):
    skill: str
    level: int  # 1-5

class SkillMatrixUpdate(BaseModel):
    skills: List[SkillEntry]

class TrainingCreate(BaseModel):
    user_id: uuid.UUID
    course_name: str

class CandidateCreate(BaseModel):
    restaurant_id: uuid.UUID
    first_name: str
    last_name: str
    phone: str
    applied_role: str
    resume_url: Optional[str] = None


# --- Skill Matrix Endpoints ---

@router.get("/skills/{user_id}", summary="Xodim malakalari", dependencies=[Depends(allow_admin)])
async def get_skill_matrix(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(SkillMatrix).where(SkillMatrix.user_id == user_id)
    )
    matrix = result.scalar_one_or_none()
    if not matrix:
        return {"user_id": str(user_id), "skills": [], "message": "Hali baholanmagan"}
    return matrix


@router.put("/skills/{user_id}", summary="Malakani yangilash", dependencies=[Depends(allow_admin)])
async def update_skills(
    user_id: uuid.UUID,
    body: SkillMatrixUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(SkillMatrix).where(SkillMatrix.user_id == user_id)
    )
    matrix = result.scalar_one_or_none()
    skills_data = [s.model_dump() for s in body.skills]

    if matrix:
        matrix.skills = skills_data
    else:
        matrix = SkillMatrix(user_id=user_id, skills=skills_data)
        db.add(matrix)

    await db.commit()
    return {"detail": "Malakalar yangilandi"}


# --- Training Endpoints ---

@router.get("/trainings/{user_id}", summary="Xodim treninglari")
async def get_trainings(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(StaffTraining).where(StaffTraining.user_id == user_id)
    )
    return result.scalars().all()


@router.post("/trainings", summary="Trening tayinlash", dependencies=[Depends(allow_admin)])
async def assign_training(
    body: TrainingCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    training = StaffTraining(
        user_id=body.user_id,
        course_name=body.course_name,
        status="NOT_STARTED",
    )
    db.add(training)
    await db.commit()
    await db.refresh(training)
    return training


@router.put("/trainings/{training_id}/progress", summary="Trening progressini yangilash")
async def update_training_progress(
    training_id: uuid.UUID,
    progress: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(select(StaffTraining).where(StaffTraining.id == training_id))
    training = result.scalar_one_or_none()
    if not training:
        raise HTTPException(status_code=404, detail="Trening topilmadi")
    training.progress_percent = min(progress, 100)
    if progress >= 100:
        training.status = "COMPLETED"
        from datetime import datetime
        training.completed_at = datetime.utcnow()
    else:
        training.status = "IN_PROGRESS"
    await db.commit()
    return {"detail": f"Progress {progress}% ga yangilandi"}


# --- Recruitment Endpoints ---

@router.get("/candidates/{restaurant_id}", summary="Nomzodlar ro'yxati", dependencies=[Depends(allow_admin)])
async def list_candidates(
    restaurant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(RecruitmentCandidate).where(
            RecruitmentCandidate.restaurant_id == restaurant_id
        )
    )
    return result.scalars().all()


@router.post("/candidates", summary="Nomzod qo'shish", dependencies=[Depends(allow_admin)])
async def create_candidate(
    body: CandidateCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    candidate = RecruitmentCandidate(
        restaurant_id=body.restaurant_id,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
        applied_role=body.applied_role,
        resume_url=body.resume_url,
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate


@router.put("/candidates/{candidate_id}/status", summary="Nomzod statusini o'zgartirish", dependencies=[Depends(allow_admin)])
async def update_candidate_status(
    candidate_id: uuid.UUID,
    new_status: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(RecruitmentCandidate).where(RecruitmentCandidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Nomzod topilmadi")
    candidate.status = new_status.upper()
    await db.commit()
    return {"detail": f"Nomzod statusi {new_status} ga o'zgartirildi"}
