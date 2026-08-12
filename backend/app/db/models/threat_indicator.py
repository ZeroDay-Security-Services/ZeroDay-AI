from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ThreatIndicator(Base):
    """A cached IOC ingested from a threat intelligence feed (ThreatFox)."""

    __tablename__ = "threat_indicators"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    ioc_value: Mapped[str] = mapped_column(
        String(512), index=True, unique=True, nullable=False
    )
    ioc_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    threat_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    malware: Mapped[str | None] = mapped_column(String(128), nullable=True)
    confidence_level: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    source_reference: Mapped[str] = mapped_column(String(512), default="")

    first_seen: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_seen: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
