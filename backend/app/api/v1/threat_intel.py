"""Threat Intelligence API -- ingests and serves real IOC data from
abuse.ch ThreatFox (see app/data_sources/threat_feed.py)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data_sources.threat_feed import ThreatFeedClient
from app.db.base import get_db
from app.db.models.threat_indicator import ThreatIndicator
from app.schemas.threat_intel import ThreatFeedSyncResult, ThreatIndicatorRead

router = APIRouter(prefix="/threat-intel", tags=["threat-intelligence"])


@router.post("/sync", response_model=ThreatFeedSyncResult)
async def sync_threat_feed(
    days: int = Query(default=3, ge=1, le=7),
    db: AsyncSession = Depends(get_db),
) -> ThreatFeedSyncResult:
    client = ThreatFeedClient()
    indicators = await client.get_recent_iocs(days=days)

    stored_new = 0
    updated = 0
    for ind in indicators:
        existing = await db.execute(
            select(ThreatIndicator).where(ThreatIndicator.ioc_value == ind.ioc_value)
        )
        row = existing.scalar_one_or_none()
        if row is None:
            db.add(
                ThreatIndicator(
                    ioc_value=ind.ioc_value,
                    ioc_type=ind.ioc_type,
                    threat_type=ind.threat_type,
                    malware=ind.malware,
                    confidence_level=ind.confidence_level,
                    tags=ind.tags,
                    source_reference=ind.source_reference,
                    first_seen=ind.first_seen,
                    last_seen=ind.last_seen,
                )
            )
            stored_new += 1
        else:
            row.confidence_level = ind.confidence_level
            row.last_seen = ind.last_seen
            row.tags = ind.tags
            updated += 1

    await db.commit()

    return ThreatFeedSyncResult(
        fetched=len(indicators),
        stored_new=stored_new,
        updated=updated,
        fetched_at=ThreatFeedClient.fetched_at(),
    )


@router.get("/iocs", response_model=list[ThreatIndicatorRead])
async def list_indicators(
    threat_type: str | None = None,
    malware: str | None = None,
    limit: int = Query(default=50, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[ThreatIndicator]:
    stmt = (
        select(ThreatIndicator)
        .order_by(ThreatIndicator.ingested_at.desc())
        .limit(limit)
    )
    if threat_type:
        stmt = stmt.where(ThreatIndicator.threat_type == threat_type)
    if malware:
        stmt = stmt.where(ThreatIndicator.malware == malware)

    result = await db.execute(stmt)
    return result.scalars().all()
