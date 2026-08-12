"""Persisted risk assessment results.

This intentionally replaces the uploaded database.py's standalone sqlite3
singleton: that file opened its own separate SQLite connection/schema
outside our async SQLAlchemy engine (and had a DynamoDB branch for AWS
Lambda), which would have meant two disconnected databases in one service.
This model captures the same fields through the app's existing async
session/engine from Phase 3, scoped to the authenticated user via a real
foreign key instead of a loose string column.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )

    cve_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    framework: Mapped[str] = mapped_column(String(32), nullable=False)

    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    timeline_days: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(String, nullable=False)

    asset_criticality: Mapped[int] = mapped_column(Integer, nullable=False)
    is_internet_facing: Mapped[bool] = mapped_column(Boolean, default=False)

    components: Mapped[dict] = mapped_column(JSON, default=dict)
    calculation_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    recommendations: Mapped[list] = mapped_column(JSON, default=list)
    audit_trail: Mapped[dict] = mapped_column(JSON, default=dict)
    cve_intelligence: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
