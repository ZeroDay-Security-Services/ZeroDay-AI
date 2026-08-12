from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class VulnerabilityRequest(BaseModel):
    cve_id: str = Field(pattern=r"^CVE-\d{4}-\d{4,}$")
    asset_criticality: int = Field(ge=1, le=10)
    is_internet_facing: bool = False
    framework: str = "enhanced"

    preventive_controls: List[str] = Field(default_factory=list)
    detective_controls: List[str] = Field(default_factory=list)
    response_controls: List[str] = Field(default_factory=list)


class RiskScoreResponse(BaseModel):
    cve_id: str
    risk_score: float
    priority: str
    timeline_days: int
    explanation: str
    components: Dict[str, float]
    calculation_breakdown: Dict[str, Any]
    confidence_score: float
    data_freshness: Dict[str, str]
    recommendations: List[str]
    audit_trail: Dict[str, Any]
    cve_intelligence: Dict[str, Any] = Field(default_factory=dict)


class RiskAssessmentRead(BaseModel):
    id: str
    cve_id: str
    framework: str
    risk_score: float
    priority: str
    timeline_days: int
    asset_criticality: int
    is_internet_facing: bool
    created_at: str
