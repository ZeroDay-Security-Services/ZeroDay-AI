"""Behavioral anomaly detection API -- backed by app/analytics/behavioral.py."""

from __future__ import annotations

from fastapi import APIRouter

from app.analytics.behavioral import ActivityEvent, detect_anomalies
from app.schemas.behavioral import (
    AnomalyResultResponse,
    BehavioralAnalysisRequest,
    BehavioralAnalysisResponse,
)

router = APIRouter(prefix="/analytics/behavioral", tags=["behavioral-analytics"])


@router.post("/anomalies", response_model=BehavioralAnalysisResponse)
async def analyze_behavior(
    request: BehavioralAnalysisRequest,
) -> BehavioralAnalysisResponse:
    events = [
        ActivityEvent(user_id=e.user_id, activity_level=e.activity_level, label=e.label)
        for e in request.events
    ]
    results = detect_anomalies(events, z_threshold=request.z_threshold)

    return BehavioralAnalysisResponse(
        total_events=len(results),
        anomalies_found=sum(1 for r in results if r.is_anomaly),
        results=[
            AnomalyResultResponse(
                user_id=r.user_id,
                activity_level=r.activity_level,
                z_score=r.z_score,
                is_anomaly=r.is_anomaly,
                label=r.label,
            )
            for r in results
        ],
    )
