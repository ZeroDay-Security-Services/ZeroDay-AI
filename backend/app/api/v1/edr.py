"""EDR (Endpoint Detection & Response) console API.

Real enrollment + heartbeat tracking for a fleet of agents. This replaces
the uploaded edr_management.py, which hardcoded every scan result to
{"status": "Clean"} regardless of input. Here, status is genuinely computed
from how recently each endpoint has checked in -- there is no agent
software included (that's a separate, larger deliverable), but the
console-side data model and API contract a real agent would talk to are
fully real and functional.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.db.base import get_db
from app.db.models.endpoint import Endpoint
from app.db.models.user import User
from app.schemas.edr import (
    EndpointEnrollRequest,
    EndpointHeartbeatRequest,
    EndpointRead,
    FleetSummary,
)

router = APIRouter(prefix="/edr", tags=["edr"])

ONLINE_THRESHOLD_SECONDS = 5 * 60
STALE_THRESHOLD_SECONDS = 30 * 60


def _compute_status(last_heartbeat_at: datetime) -> tuple[str, float]:
    now = datetime.now(timezone.utc)
    # SQLite (unlike Postgres) doesn't round-trip tzinfo through DateTime(timezone=True) --
    # values read back are naive. Treat any naive value as UTC rather than letting the
    # subtraction below raise.
    if last_heartbeat_at.tzinfo is None:
        last_heartbeat_at = last_heartbeat_at.replace(tzinfo=timezone.utc)
    delta = (now - last_heartbeat_at).total_seconds()
    if delta <= ONLINE_THRESHOLD_SECONDS:
        return "online", delta
    if delta <= STALE_THRESHOLD_SECONDS:
        return "stale", delta
    return "offline", delta


def _to_read(endpoint: Endpoint) -> EndpointRead:
    status, delta = _compute_status(endpoint.last_heartbeat_at)
    return EndpointRead(
        id=endpoint.id,
        hostname=endpoint.hostname,
        ip_address=endpoint.ip_address,
        os_name=endpoint.os_name,
        agent_version=endpoint.agent_version,
        enrolled_at=endpoint.enrolled_at.isoformat(),
        last_heartbeat_at=endpoint.last_heartbeat_at.isoformat(),
        seconds_since_heartbeat=delta,
        status=status,
        last_reported_findings=endpoint.last_reported_findings,
    )


@router.post("/enroll", response_model=EndpointRead, status_code=201)
async def enroll_endpoint(
    request: EndpointEnrollRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EndpointRead:
    endpoint = Endpoint(
        user_id=user.id,
        hostname=request.hostname,
        ip_address=request.ip_address,
        os_name=request.os_name,
        agent_version=request.agent_version,
    )
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)
    return _to_read(endpoint)


@router.post("/{endpoint_id}/heartbeat", response_model=EndpointRead)
async def heartbeat(
    endpoint_id: str,
    request: EndpointHeartbeatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EndpointRead:
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id, Endpoint.user_id == user.id)
    )
    endpoint = result.scalar_one_or_none()
    if endpoint is None:
        raise NotFoundError("Endpoint not found", details={"endpoint_id": endpoint_id})

    endpoint.last_heartbeat_at = datetime.now(timezone.utc)
    if request.findings:
        endpoint.last_reported_findings = request.findings
    await db.commit()
    await db.refresh(endpoint)
    return _to_read(endpoint)


@router.get("/endpoints", response_model=FleetSummary)
async def list_endpoints(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FleetSummary:
    result = await db.execute(select(Endpoint).where(Endpoint.user_id == user.id))
    rows = [_to_read(e) for e in result.scalars().all()]

    return FleetSummary(
        total=len(rows),
        online=sum(1 for r in rows if r.status == "online"),
        stale=sum(1 for r in rows if r.status == "stale"),
        offline=sum(1 for r in rows if r.status == "offline"),
        endpoints=rows,
    )
