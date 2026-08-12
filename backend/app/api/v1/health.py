"""Health and readiness endpoints used by Render/Docker health checks."""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }


@router.get("/config/features")
def config_features() -> dict:
    from app.core.feature_flags import feature_flags

    return feature_flags.get_environment_config()
