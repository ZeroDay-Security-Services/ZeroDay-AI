"""Cloud compliance scanning API -- backed by app/compliance_engine/cloud_rules.py."""

from __future__ import annotations

from fastapi import APIRouter

from app.compliance_engine.cloud_rules import evaluate_cloud_config
from app.schemas.compliance import CloudComplianceResult, CloudConfigScanRequest

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post("/cloud/scan", response_model=CloudComplianceResult)
async def scan_cloud_config(request: CloudConfigScanRequest) -> CloudComplianceResult:
    result = evaluate_cloud_config(request.config)
    return CloudComplianceResult(**result)
