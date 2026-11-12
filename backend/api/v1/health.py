"""Health check endpoint for QUANT AI."""

from fastapi import APIRouter
from datetime import datetime, timezone
import zoneinfo
from backend.core.config import settings
from backend.schemas.system import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Returns basic health status of the QUANT AI backend."""
    try:
        tz = zoneinfo.ZoneInfo(settings.DEFAULT_TIMEZONE)
        now = datetime.now(tz)
    except Exception:
        now = datetime.now(timezone.utc)

    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        app_name=settings.APP_NAME,
        timestamp=now,
        timezone=settings.DEFAULT_TIMEZONE,
        currency=settings.DEFAULT_CURRENCY,
        environment=settings.ENVIRONMENT,
    )
