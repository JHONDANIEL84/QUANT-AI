"""Smart Money Concepts (SMC) API Endpoint — Phase 5 QUANT AI.

GET /api/v1/smc/analysis
    Runs the complete Smart Money Concepts analysis (BOS, CHOCH, Order Blocks, FVGs, Premium/Discount)
    for a given asset symbol and timeframe.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from data_providers.base.models import MarketBar
from data_providers.manager import MarketDataManager, market_data_manager
from quantitative_engine.smc.analyzer import run_smc_analysis
from quantitative_engine.smc.models import SMCAnalysis

router = APIRouter(prefix="/smc", tags=["Smart Money Concepts"])


class SMCAnalysisResponse(BaseModel):
    """SMC API Response Schema."""

    symbol: str
    interval: str
    bars_analyzed: int
    structure_breaks: List[Dict[str, Any]] = Field(default_factory=list)
    order_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    fair_value_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    premium_discount: Optional[Dict[str, Any]] = None
    observation: str
    hypothesis: str
    data_status: str = "observation"


def analyze_smc_data(
    symbol: str,
    interval: str,
    bars: List[MarketBar],
) -> SMCAnalysisResponse:
    """Executes SMC engine synchronously over provided MarketBar list and serializes response."""
    smc: SMCAnalysis = run_smc_analysis(symbol=symbol, interval=interval, bars=bars)

    breaks_dicts = [
        {
            "break_type": b.break_type.value,
            "direction": b.direction.value,
            "broken_pivot_price": b.broken_pivot_price,
            "breaking_bar_index": b.breaking_bar_index,
            "breaking_bar_timestamp": b.breaking_bar_timestamp.isoformat(),
            "breaking_price": b.breaking_price,
            "invalidation_level": b.invalidation_level,
            "rule_applied": b.rule_applied,
        }
        for b in smc.structure_breaks
    ]

    ob_dicts = [
        {
            "direction": ob.direction.value,
            "bar_index": ob.bar_index,
            "timestamp": ob.timestamp.isoformat(),
            "top_price": ob.top_price,
            "bottom_price": ob.bottom_price,
            "body_top": ob.body_top,
            "body_bottom": ob.body_bottom,
            "status": ob.status.value,
            "mitigated_at": ob.mitigated_at.isoformat() if ob.mitigated_at else None,
            "mitigated_bar_index": ob.mitigated_bar_index,
            "is_breaker": ob.is_breaker,
            "quality_score": ob.quality_score,
            "volume": ob.volume,
            "rule_applied": ob.rule_applied,
        }
        for ob in smc.order_blocks
    ]

    fvg_dicts = [
        {
            "direction": f.direction.value,
            "bar_index": f.bar_index,
            "timestamp": f.timestamp.isoformat(),
            "top_price": f.top_price,
            "bottom_price": f.bottom_price,
            "gap_size": f.gap_size,
            "consequent_encroachment": f.consequent_encroachment,
            "status": f.status.value,
            "mitigated_pct": f.mitigated_pct,
            "mitigated_at": f.mitigated_at.isoformat() if f.mitigated_at else None,
            "rule_applied": f.rule_applied,
        }
        for f in smc.fair_value_gaps
    ]

    pd_dict = None
    if smc.premium_discount:
        pd_dict = {
            "swing_high": smc.premium_discount.swing_high,
            "swing_low": smc.premium_discount.swing_low,
            "equilibrium": smc.premium_discount.equilibrium,
            "current_price": smc.premium_discount.current_price,
            "current_position_pct": smc.premium_discount.current_position_pct,
            "zone": smc.premium_discount.zone,
            "observation": smc.premium_discount.observation,
        }

    return SMCAnalysisResponse(
        symbol=smc.symbol,
        interval=smc.interval,
        bars_analyzed=smc.bars_analyzed,
        structure_breaks=breaks_dicts,
        order_blocks=ob_dicts,
        fair_value_gaps=fvg_dicts,
        premium_discount=pd_dict,
        observation=smc.observation,
        hypothesis=smc.hypothesis,
        data_status=smc.data_status,
    )


@router.get("/analysis", response_model=SMCAnalysisResponse, summary="Análisis institucional Smart Money Concepts (SMC)")
async def get_smc_analysis(
    symbol: str = Query("BTCUSDT", description="Símbolo del activo (ej: BTCUSDT, AAPL, ECOPETROL)"),
    interval: str = Query("1d", description="Temporalidad (1d, 4h, 1h, 15m)"),
    limit: int = Query(200, ge=20, le=1000, description="Número de barras a analizar"),
):
    """Calculates BOS, CHOCH, Order Blocks, FVGs, and Premium/Discount dealing range.

    Strictly causal without look-ahead bias. Differentiates verified facts from forward hypotheses.
    """
    try:
        bars = await market_data_manager.get_historical_bars(symbol=symbol, interval=interval, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Error al obtener datos de mercado: {exc}") from exc

    if not bars or len(bars) < 10:
        raise HTTPException(
            status_code=422,
            detail=f"Datos insuficientes para {symbol} en temporalidad {interval}. Se recibieron {len(bars) if bars else 0} barras.",
        )

    return analyze_smc_data(symbol=symbol, interval=interval, bars=bars)
