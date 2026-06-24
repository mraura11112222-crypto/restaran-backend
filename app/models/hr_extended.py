"""Extended HR models - Training, Skills, and Recruitment."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    JSON,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class SkillMatrix(Base):
    """Staff skills mapping for productivity."""
    __tablename__ = "skill_matrices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    skills = Column(JSON, default=list, comment='[{"skill": "Barista", "level": 5}]')
    last_assessed = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class StaffTraining(Base):
    """Training management for onboarding and continuous learning."""
    __tablename__ = "staff_trainings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_name = Column(String(255), nullable=False)
    progress_percent = Column(Integer, default=0)
    status = Column(String(50), default="NOT_STARTED")  # IN_PROGRESS, COMPLETED
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User")


class RecruitmentCandidate(Base):
    """Recruitment and onboarding."""
    __tablename__ = "recruitment_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
    )
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    applied_role = Column(String(50), nullable=False)
    resume_url = Column(String(512), nullable=True)
    status = Column(String(50), default="APPLIED")  # INTERVIEWING, HIRED, REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)
