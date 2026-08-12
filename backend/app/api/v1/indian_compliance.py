"""Indian regulatory compliance API -- CERT-In Directions 2022 and the
Digital Personal Data Protection (DPDP) Act, 2023.

Compliance-posture checking against real, publicly documented obligations
-- not legal advice. Mirrors the pattern used for /compliance/cloud/scan.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.compliance_engine.cert_in import (
    MANDATORY_INCIDENT_CATEGORIES,
    calculate_reporting_deadline,
    evaluate_cert_in_compliance,
)
from app.compliance_engine.dpdp import evaluate_dpdp_compliance
from app.schemas.indian_compliance import (
    ComplianceResult,
    ComplianceScanRequest,
    IncidentDeadlineRequest,
    IncidentDeadlineResponse,
)

router = APIRouter(prefix="/compliance/india", tags=["compliance-india"])


@router.post("/cert-in/scan", response_model=ComplianceResult)
async def scan_cert_in(request: ComplianceScanRequest) -> ComplianceResult:
    result = evaluate_cert_in_compliance(request.config)
    return ComplianceResult(**result)


@router.get("/cert-in/incident-categories")
async def cert_in_incident_categories() -> dict:
    return {
        "reporting_window_hours": 6,
        "categories": MANDATORY_INCIDENT_CATEGORIES,
    }


@router.post("/cert-in/incident-deadline", response_model=IncidentDeadlineResponse)
async def cert_in_incident_deadline(
    request: IncidentDeadlineRequest,
) -> IncidentDeadlineResponse:
    result = calculate_reporting_deadline(request.detected_at)
    return IncidentDeadlineResponse(
        **result, incident_category=request.incident_category
    )


@router.post("/dpdp/scan", response_model=ComplianceResult)
async def scan_dpdp(request: ComplianceScanRequest) -> ComplianceResult:
    result = evaluate_dpdp_compliance(request.config)
    return ComplianceResult(**result)
