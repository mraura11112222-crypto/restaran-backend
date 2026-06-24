"""Analytics models – market trends, competitors."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class MarketTrend(Base):
    """AI predicted market trends and segments."""

    __tablename__ = "market_trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trend_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    data = Column(JSON, nullable=True, comment="Trend data points")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<MarketTrend {self.trend_name!r}>"


class CompetitorData(Base):
    """AI tracked competitor information."""

    __tablename__ = "competitor_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    competitor_name = Column(String(255), nullable=False)
    metrics = Column(JSON, nullable=True, comment="e.g. estimated pricing, popularity")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<CompetitorData {self.competitor_name!r}>"


class CustomerSegment(Base):
    """AI predicted customer segments (e.g., VIP, Churn risk)."""
    __tablename__ = "customer_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    customer_ids = Column(JSON, default=list, comment="List of user IDs in this segment")
    created_at = Column(DateTime, default=datetime.utcnow)


class InvestorReport(Base):
    """Integrated investor reports."""
    __tablename__ = "investor_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    report_url = Column(String(512), nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    data_summary = Column(JSON, nullable=True)
