"""Indicator API endpoints.
Provides computed technical indicators and ready-to-render chart series.
"""

from fastapi import APIRouter, Query, HTTPException, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from data_providers.base.models import MarketBar
from data_providers.manager import market_data_manager
from quantitative_engine.indicators import (
    indicator_engine,
    ComputedIndicatorsResponse,
)

router = APIRouter(prefix="/indicators", tags=["Technical Indicators"])


class ChartDataResponse(BaseModel):
    symbol: str
    interval: str
    bars: List[MarketBar]
    indicators: ComputedIndicatorsResponse
    computed_at: datetime


class ComputeRequest(BaseModel):
    symbol: str = "CUSTOM"
    interval: str = "1d"
    bars: List[MarketBar]


@router.get("/chart-data", response_model=ChartDataResponse)
async def get_chart_data(
    symbol: str = Query(..., description="Ticker symbol, e.g. BTCUSDT, AAPL, ECOPETROL"),
    interval: str = Query("1d", description="Timeframe: 1m, 5m, 15m, 1h, 4h, 1d, 1w"),
    limit: int = Query(150, ge=20, le=1000, description="Number of bars to calculate over"),
) -> ChartDataResponse:
    """Retrieves normalized OHLCV bars and pre-computed indicators (EMAs, RSI, MACD, ATR, VWAP, Bollinger, Fib) in a single call."""
    bars = await market_data_manager.get_historical_bars(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )
    if not bars:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudieron obtener datos históricos para '{symbol}'.",
        )

    computed = indicator_engine.compute_all(
        bars=bars,
        symbol=symbol,
        interval=interval,
    )

    return ChartDataResponse(
        symbol=symbol,
        interval=interval,
        bars=bars,
        indicators=computed,
        computed_at=datetime.now(),
    )


@router.post("/compute", response_model=ComputedIndicatorsResponse)
async def compute_indicators_from_bars(
    request: ComputeRequest = Body(...),
) -> ComputedIndicatorsResponse:
    """Directly computes technical indicators from an uploaded list of MarketBars."""
    if not request.bars:
        raise HTTPException(
            status_code=400,
            detail="La lista de barras OHLCV no puede estar vacía.",
        )

    return indicator_engine.compute_all(
        bars=request.bars,
        symbol=request.symbol,
        interval=request.interval,
    )
