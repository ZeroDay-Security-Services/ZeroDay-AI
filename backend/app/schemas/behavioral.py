from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class ActivityEventRequest(BaseModel):
    user_id: str
    activity_level: float
    label: str = ""


class BehavioralAnalysisRequest(BaseModel):
    events: List[ActivityEventRequest] = Field(min_length=1)
    z_threshold: float = Field(
        default=3.5,
        ge=0.5,
        le=10.0,
        description="Modified z-score (median/MAD based) threshold. 3.5 is the standard Iglewicz & Hoaglin recommendation.",
    )


class AnomalyResultResponse(BaseModel):
    user_id: str
    activity_level: float
    z_score: float
    is_anomaly: bool
    label: str


class BehavioralAnalysisResponse(BaseModel):
    total_events: int
    anomalies_found: int
    results: List[AnomalyResultResponse]
