"""Consolidated API v1 router."""

from fastapi import APIRouter
from backend.api.v1.health import router as health_router
from backend.api.v1.system import router as system_router
from backend.api.v1.market import router as market_router
from backend.api.v1.indicators import router as indicators_router
from backend.api.v1.price_action import router as price_action_router
from backend.api.v1.smc import router as smc_router
from backend.api.v1.liquidity import router as liquidity_router
from backend.api.v1.scanner import router as scanner_router
from backend.api.v1.risk import router as risk_router
from backend.api.v1.backtest import router as backtest_router
from backend.api.v1.chat import router as chat_router

api_v1_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(system_router)
api_v1_router.include_router(market_router)
api_v1_router.include_router(indicators_router)
api_v1_router.include_router(price_action_router)
api_v1_router.include_router(smc_router)
api_v1_router.include_router(liquidity_router)
api_v1_router.include_router(scanner_router)
api_v1_router.include_router(risk_router)
api_v1_router.include_router(backtest_router)
api_v1_router.include_router(chat_router)
