"""Aggregates all v1 API routers."""

from fastapi import APIRouter

from app.api.v1.agents import router as agents_router
from app.api.v1.assistant import router as assistant_router
from app.api.v1.auth import router as auth_router
from app.api.v1.behavioral import router as behavioral_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.edr import router as edr_router
from app.api.v1.health import router as health_router
from app.api.v1.indian_compliance import router as indian_compliance_router
from app.api.v1.risk import router as risk_router
from app.api.v1.threat_intel import router as threat_intel_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(risk_router)
api_router.include_router(threat_intel_router)
api_router.include_router(edr_router)
api_router.include_router(compliance_router)
api_router.include_router(indian_compliance_router)
api_router.include_router(behavioral_router)
api_router.include_router(assistant_router)
api_router.include_router(agents_router)
