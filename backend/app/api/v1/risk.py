"""CVE Intelligence & Risk Scoring API.

Fuses live NVD (CVSS) and FIRST.org (EPSS) data through the contextual
risk-scoring engine to produce a transparent, auditable risk score for a
given CVE against a given asset's context. Ported and adapted from the
uploaded VulnRisk scoring service: same NVD/EPSS clients and scoring
engine, wired to this project's own auth (Phase 3) and persistence layer
instead of the original's Auth0 + standalone-sqlite3 dependencies.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.core.exceptions import AppError, NotFoundError
from app.core_risk import context as ctx
from app.core_risk.risk_calculator import (
    EnhancedContextualFramework,
    RiskBasedFramework,
    VulnerabilityData,
)
from app.data_sources.epss import EPSSClient
from app.data_sources.nvd import NVDClient
from app.db.base import get_db
from app.db.models.risk_assessment import RiskAssessment
from app.db.models.user import User
from app.schemas.risk import RiskAssessmentRead, RiskScoreResponse, VulnerabilityRequest

router = APIRouter(prefix="/risk", tags=["risk"])

_FRAMEWORKS = {
    "enhanced": EnhancedContextualFramework,
    "mitigation-contextual": EnhancedContextualFramework,
    "risk-based": RiskBasedFramework,
}


def _build_vulnerability_data(
    request: VulnerabilityRequest, cve_data, epss_data
) -> VulnerabilityData:
    has_exploit = cve_data.has_exploit_references or epss_data.epss_score >= 0.3
    return VulnerabilityData(
        cve_id=request.cve_id,
        cvss_score=cve_data.cvss_score,
        asset_criticality=request.asset_criticality,
        epss_score=epss_data.epss_score,
        is_internet_facing=request.is_internet_facing,
        has_exploit=has_exploit,
        is_kev=cve_data.cisa_kev,
        network_exposure=(
            "internet-facing" if request.is_internet_facing else "internal"
        ),
        cia_impact=ctx.determine_cia_impact(cve_data),
        attack_path_complexity=ctx.determine_attack_complexity(
            cve_data, request.is_internet_facing
        ),
        exploit_availability=ctx.determine_exploit_availability(cve_data, epss_data),
        discovery_difficulty=ctx.determine_discovery_difficulty(
            cve_data, request.is_internet_facing
        ),
        exploitation_frequency=ctx.determine_exploitation_frequency(
            cve_data, epss_data
        ),
        target_attractiveness=ctx.determine_target_attractiveness(
            request.asset_criticality
        ),
        threat_actor_sophistication=ctx.determine_threat_actor_sophistication(
            cve_data, epss_data
        ),
        resource_level=ctx.determine_resource_level(
            cve_data, request.asset_criticality
        ),
        vulnerability_age_days=cve_data.vulnerability_age_days,
        patch_availability=ctx.determine_patch_availability(
            cve_data.vulnerability_age_days
        ),
        disclosure_timeline=ctx.determine_disclosure_timeline(
            cve_data.vulnerability_age_days
        ),
        preventive_controls=request.preventive_controls,
        detective_controls=request.detective_controls,
        response_controls=request.response_controls,
    )


@router.get("/frameworks")
async def list_frameworks() -> dict:
    return {
        "frameworks": [
            {
                "id": "enhanced",
                "name": "Enhanced Contextual",
                "description": "Balances technical severity with business context.",
            },
            {
                "id": "mitigation-contextual",
                "name": "Mitigation Contextual",
                "description": "CVE-aware security controls assessment.",
            },
            {
                "id": "risk-based",
                "name": "Risk Based",
                "description": "Complete master formula with context, threat, and temporal multipliers.",
            },
        ]
    }


@router.post("/score", response_model=RiskScoreResponse)
async def score_vulnerability(
    request: VulnerabilityRequest,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> RiskScoreResponse:
    framework_cls = _FRAMEWORKS.get(request.framework)
    if framework_cls is None:
        raise AppError(
            f"Unknown framework: {request.framework}",
            code="UNKNOWN_FRAMEWORK",
            status_code=400,
        )

    nvd_client = NVDClient(api_key=os.getenv("NVD_API_KEY"))
    epss_client = EPSSClient()

    cve_data = await nvd_client.get_rich_cve_data(request.cve_id)
    epss_data = await epss_client.get_rich_epss_data(request.cve_id)

    if not cve_data or not epss_data:
        raise NotFoundError(
            "Vulnerability data not found",
            details={"cve_id": request.cve_id},
        )

    vuln_data = _build_vulnerability_data(request, cve_data, epss_data)
    calculator = framework_cls()
    result = calculator.calculate_risk(vuln_data)
    cve_intelligence = ctx.build_cve_intelligence(cve_data, epss_data)

    if user:
        assessment = RiskAssessment(
            user_id=user.id,
            cve_id=request.cve_id,
            framework=request.framework,
            risk_score=result.score,
            priority=result.priority,
            timeline_days=result.timeline_days,
            explanation=result.explanation,
            asset_criticality=request.asset_criticality,
            is_internet_facing=request.is_internet_facing,
            components=result.components,
            calculation_breakdown=result.calculation_breakdown,
            confidence_score=result.confidence_score,
            recommendations=result.recommendations,
            audit_trail=result.audit_trail,
            cve_intelligence=cve_intelligence,
        )
        db.add(assessment)
        await db.commit()

    return RiskScoreResponse(
        cve_id=request.cve_id,
        risk_score=result.score,
        priority=result.priority,
        timeline_days=result.timeline_days,
        explanation=result.explanation,
        components=result.components,
        calculation_breakdown=result.calculation_breakdown,
        confidence_score=result.confidence_score,
        data_freshness=result.data_freshness,
        recommendations=result.recommendations,
        audit_trail=result.audit_trail,
        cve_intelligence=cve_intelligence,
    )


@router.get("/history", response_model=list[RiskAssessmentRead])
async def assessment_history(
    user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=200),
) -> list[RiskAssessment]:
    if not user:
        return []

    result = await db.execute(
        select(RiskAssessment)
        .where(RiskAssessment.user_id == user.id)
        .order_by(RiskAssessment.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        RiskAssessmentRead(
            id=r.id,
            cve_id=r.cve_id,
            framework=r.framework,
            risk_score=r.risk_score,
            priority=r.priority,
            timeline_days=r.timeline_days,
            asset_criticality=r.asset_criticality,
            is_internet_facing=r.is_internet_facing,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]
