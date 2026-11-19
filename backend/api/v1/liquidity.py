"""Liquidity Intelligence API Endpoint — Phase 6 QUANT AI.

GET /api/v1/liquidity/analysis
    Runs full Liquidity Intelligence analysis (EQH, EQL, BSL, SSL, PDH, PDL, Sweeps)
    for a given asset symbol and timeframe.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from data_providers.base.models import MarketBar
from data_providers.manager import MarketDataManager, market_data_manager
from quantitative_engine.liquidity.analyzer import run_liquidity_analysis
from quantitative_engine.liquidity.models import LiquidityAnalysis

router = APIRouter(prefix="/liquidity", tags=["Liquidity Intelligence"])


class LiquidityAnalysisResponse(BaseModel):
    """Liquidity Intelligence API Response Schema."""

    symbol: str
    interval: str
    bars_analyzed: int
    pools: List[Dict[str, Any]] = Field(default_factory=list)
    sweeps: List[Dict[str, Any]] = Field(default_factory=list)
    session_levels: Dict[str, Any] = Field(default_factory=dict)
    observation: str
    hypothesis: str
    data_status: str = "observation"


def analyze_liquidity_data(
    symbol: str,
    interval: str,
    bars: List[MarketBar],
) -> LiquidityAnalysisResponse:
    """Synchronously executes the Liquidity Intelligence engine and serializes response."""
    liq: LiquidityAnalysis = run_liquidity_analysis(symbol=symbol, interval=interval, bars=bars)

    pool_dicts = [
        {
            "pool_type": p.pool_type.value,
            "price_level": p.price_level,
            "top_price": p.top_price,
            "bottom_price": p.bottom_price,
            "touch_count": p.touch_count,
            "first_touch_at": p.first_touch_at.isoformat(),
            "last_touch_at": p.last_touch_at.isoformat(),
            "liquidity_score": p.liquidity_score,
            "status": p.status.value,
            "swept_at": p.swept_at.isoformat() if p.swept_at else None,
            "swept_bar_index": p.swept_bar_index,
            "sweep_penetration_pct": p.sweep_penetration_pct,
            "rule_applied": p.rule_applied,
        }
        for p in liq.pools
    ]

    sweep_dicts = [
        {
            "pool_type": s.pool_type.value,
            "price_level": s.price_level,
            "sweep_bar_index": s.sweep_bar_index,
            "sweep_timestamp": s.sweep_timestamp.isoformat(),
            "penetration_price": s.penetration_price,
            "rejection_close": s.rejection_close,
            "penetration_pct": s.penetration_pct,
            "invalidation_level": s.invalidation_level,
            "rule_applied": s.rule_applied,
        }
        for s in liq.sweeps
    ]

    session_dict = {
        "pdh": liq.session_levels.pdh,
        "pdl": liq.session_levels.pdl,
        "pwh": liq.session_levels.pwh,
        "pwl": liq.session_levels.pwl,
    }

    return LiquidityAnalysisResponse(
        symbol=liq.symbol,
        interval=liq.interval,
        bars_analyzed=liq.bars_analyzed,
        pools=pool_dicts,
        sweeps=sweep_dicts,
        session_levels=session_dict,
        observation=liq.observation,
        hypothesis=liq.hypothesis,
        data_status=liq.data_status,
    )


@router.get("/analysis", response_model=LiquidityAnalysisResponse, summary="Análisis de Liquidity Intelligence & Sweeps")
async def get_liquidity_analysis(
    symbol: str = Query("BTCUSDT", description="Símbolo del activo (ej: BTCUSDT, AAPL, ECOPETROL)"),
    interval: str = Query("1d", description="Temporalidad (1d, 4h, 1h, 15m)"),
    limit: int = Query(200, ge=20, le=1000, description="Número de barras a analizar"),
):
    """Identifies EQH, EQL, BSL, SSL pools, session benchmarks, and confirmed liquidity sweeps with rejection."""
    try:
        bars = await market_data_manager.get_historical_bars(symbol=symbol, interval=interval, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Error al obtener datos de mercado: {exc}") from exc

    if not bars or len(bars) < 10:
        raise HTTPException(
            status_code=422,
            detail=f"Datos insuficientes para {symbol} en temporalidad {interval}. Se recibieron {len(bars) if bars else 0} barras.",
        )

    return analyze_liquidity_data(symbol=symbol, interval=interval, bars=bars)
