"""Price Action API endpoint — Fase 4 QUANT AI.

GET /api/v1/price-action/analysis
    Runs the full Price Action pipeline (candle patterns + market structure + S/R zones)
    for a given symbol and interval, returning structured JSON.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

from data_providers.base.models import MarketBar
from data_providers.manager import MarketDataManager, market_data_manager
from quantitative_engine.candles.patterns import detect_candle_patterns
from quantitative_engine.market_structure.swings import detect_market_structure
from quantitative_engine.price_action.analyzer import run_price_action_analysis
from quantitative_engine.candles.models import CandlePattern
from quantitative_engine.market_structure.models import MarketStructureResult
from quantitative_engine.price_action.models import PriceActionAnalysis

router = APIRouter(prefix="/price-action", tags=["Price Action"])


class PriceActionResponse(BaseModel):
    """Full price action analysis response returned to the frontend."""

    symbol: str
    interval: str
    bars_analyzed: int
    candle_patterns: List[dict] = Field(default_factory=list)
    market_structure: dict = Field(default_factory=dict)
    price_action: dict = Field(default_factory=dict)
    data_status: str = "observation"


def analyze_price_action_data(
    symbol: str,
    interval: str,
    bars: List[MarketBar],
) -> PriceActionResponse:
    """Analyzes a list of MarketBar objects and constructs the complete PriceActionResponse.

    Strictly causal, separated observations and hypotheses, no look-ahead bias.
    """
    # Run all three engines
    candle_pats: List[CandlePattern] = detect_candle_patterns(bars)
    market_struct: MarketStructureResult = detect_market_structure(bars)
    pa_analysis: PriceActionAnalysis = run_price_action_analysis(bars)

    # Serialize to dicts (Pydantic v2 compatible)
    candle_dicts = [
        {
            "pattern_type": p.pattern_type.value,
            "direction": p.direction.value,
            "timestamp": p.timestamp.isoformat(),
            "bar_index": p.bar_index,
            "price": p.price,
            "confirmed_at": p.confirmed_at.isoformat(),
            "confidence": p.confidence,
            "rule_applied": p.rule_applied,
            "invalidation_level": p.invalidation_level,
        }
        for p in candle_pats
    ]

    structure_dict = {
        "trend": market_struct.trend.value,
        "last_swing_high": market_struct.last_swing_high,
        "last_swing_low": market_struct.last_swing_low,
        "summary": market_struct.summary,
        "pivot_count": len(market_struct.pivots),
        "pivots": [
            {
                "bar_index": p.bar_index,
                "timestamp": p.timestamp.isoformat(),
                "confirmed_at": p.confirmed_at.isoformat(),
                "price": p.price,
                "is_high": p.is_high,
                "structure_type": p.structure_type.value,
                "rule_applied": p.rule_applied,
            }
            for p in market_struct.pivots[-20:]  # Return last 20 pivots max
        ],
        "consolidation": (
            {
                "top": market_struct.consolidation.top,
                "bottom": market_struct.consolidation.bottom,
                "mean": market_struct.consolidation.mean,
                "duration_bars": market_struct.consolidation.duration_bars,
            }
            if market_struct.consolidation
            else None
        ),
    }

    pa_dict = {
        "zones": [
            {
                "zone_type": z.zone_type.value,
                "price_level": z.price_level,
                "top_price": z.top_price,
                "bottom_price": z.bottom_price,
                "touches": z.touches,
                "strength": z.strength,
                "status": z.status.value,
                "invalidation_level": z.invalidation_level,
                "evidence": z.evidence,
            }
            for z in pa_analysis.zones
        ],
        "events": [
            {
                "event_type": e.event_type.value,
                "timestamp": e.timestamp.isoformat(),
                "price": e.price,
                "description": e.description,
                "rule_applied": e.rule_applied,
                "invalidation_criteria": e.invalidation_criteria,
                "is_confirmed": e.is_confirmed,
            }
            for e in pa_analysis.events
        ],
        "is_compressed": pa_analysis.is_compressed,
        "observation": pa_analysis.observation,
        "hypothesis": pa_analysis.hypothesis,
    }

    return PriceActionResponse(
        symbol=symbol.upper(),
        interval=interval,
        bars_analyzed=len(bars),
        candle_patterns=candle_dicts,
        market_structure=structure_dict,
        price_action=pa_dict,
        data_status="observation",
    )


@router.get("/analysis", response_model=PriceActionResponse, summary="Análisis completo de Price Action")
async def get_price_action_analysis(
    symbol: str = Query("AAPL", description="Símbolo del activo (ej: AAPL, BTCUSDT)"),
    interval: str = Query("1d", description="Temporalidad (1d, 1h, 15m, etc.)"),
    limit: int = Query(200, ge=20, le=1000, description="Número de barras a analizar"),
):
    """Returns candle patterns, market structure pivots, and price action zones.

    - **symbol**: Asset symbol routed to Yahoo Finance, Binance, or BVC provider.
    - **interval**: OHLCV bar interval.
    - **limit**: Number of historical bars to analyze.

    All calculations are strictly causal (no look-ahead bias).
    Observations and hypotheses are explicitly separated in the response.
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

    return analyze_price_action_data(symbol=symbol, interval=interval, bars=bars)
