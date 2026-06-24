"""HR models – work schedules, performance, and salary."""

import enum
import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class PerformanceType(str, enum.Enum):
    """Тип оценки."""

    BONUS = "BONUS"
    PENALTY = "PENALTY"
    RATING = "RATING"


class WorkSchedule(Base):
    """Work schedule for staff members (AI generated or manual)."""

    __tablename__ = "work_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    work_date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<WorkSchedule {self.work_date} {self.start_time}-{self.end_time}>"


class StaffPerformance(Base):
    """Staff performance, bonuses, and penalties."""

    __tablename__ = "staff_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evaluator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Who gave this evaluation"
    )
    record_type = Column(
        SAEnum(PerformanceType, name="performance_type", create_constraint=True),
        nullable=False,
    )
    amount = Column(Numeric(10, 2), nullable=True, comment="Bonus or penalty amount")
    points = Column(Integer, nullable=True, comment="Rating points")
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<StaffPerformance {self.record_type} amount={self.amount}>"


class Payroll(Base):
    """Payroll and salary calculation records."""
    __tablename__ = "payrolls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    base_salary = Column(Numeric(10, 2), default=0)
    total_bonuses = Column(Numeric(10, 2), default=0)
    total_penalties = Column(Numeric(10, 2), default=0)
    taxes = Column(Numeric(10, 2), default=0)
    net_pay = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, PAID
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

