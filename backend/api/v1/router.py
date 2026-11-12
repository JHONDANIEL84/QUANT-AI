"""Consolidated API v1 router."""

from fastapi import APIRouter
from backend.api.v1.health import router as health_router
from backend.api.v1.system import router as system_router

api_v1_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(system_router)
