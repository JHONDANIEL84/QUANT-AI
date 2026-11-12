"""Market Data API endpoints for QUANT AI.
Exposes historical bars, real-time tickers, order book depth, corporate fundamentals, and macro indicators.
"""

from fastapi import APIRouter, Query, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional
import asyncio
import json
import logging

from data_providers.base.models import (
    MarketBar,
    TickerSnapshot,
    OrderBookDepth,
    CompanyInfo,
    MacroIndicator,
    MarketStatus,
)
from data_providers.manager import market_data_manager

logger = logging.getLogger("quant_ai.api.market")
router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/bars", response_model=List[MarketBar])
async def get_market_bars(
    symbol: str = Query(..., description="Ticker symbol, e.g., AAPL, BTCUSDT, ECOPETROL"),
    interval: str = Query("1d", description="Timeframe interval: 1m, 5m, 15m, 1h, 4h, 1d, 1w"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of bars to return"),
) -> List[MarketBar]:
    """Retrieve normalized historical OHLCV bars across any supported market."""
    bars = await market_data_manager.get_historical_bars(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )
    if not bars:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron datos históricos para el símbolo '{symbol}' en el intervalo '{interval}'.",
        )
    return bars


@router.get("/ticker", response_model=TickerSnapshot)
async def get_ticker(
    symbol: str = Query(..., description="Ticker symbol, e.g., BTCUSDT, NVDA, ECOPETROL"),
) -> TickerSnapshot:
    """Retrieve 24-hour summary price snapshot for a symbol."""
    snapshot = await market_data_manager.get_ticker_snapshot(symbol)
    if not snapshot:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudo obtener información de precio para el símbolo '{symbol}'.",
        )
    return snapshot


@router.get("/orderbook", response_model=OrderBookDepth)
async def get_order_book(
    symbol: str = Query("BTCUSDT", description="Cryptocurrency symbol, e.g., BTCUSDT, ETHUSDT"),
    limit: int = Query(20, ge=5, le=100, description="Order book depth per side"),
) -> OrderBookDepth:
    """Retrieve real-time order book depth and bid/ask volume imbalance ratio."""
    ob = await market_data_manager.get_order_book(symbol=symbol, limit=limit)
    if not ob:
        raise HTTPException(
            status_code=400,
            detail=f"El libro de órdenes no está disponible para '{symbol}'. Actualmente disponible para criptomonedas (Binance).",
        )
    return ob


@router.get("/company", response_model=Optional[CompanyInfo])
async def get_company_info(
    symbol: str = Query(..., description="Stock symbol, e.g., AAPL, MSFT, NVDA"),
) -> Optional[CompanyInfo]:
    """Retrieve fundamental corporate profile, valuation ratios, and description."""
    info = await market_data_manager.get_company_info(symbol)
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró información fundamental para '{symbol}'.",
        )
    return info


@router.get("/macro", response_model=List[MacroIndicator])
async def get_macro_indicators(
    country: str = Query("CO", description="Country code: 'CO' (Colombia) or 'US' (Estados Unidos)"),
) -> List[MacroIndicator]:
    """Retrieve official macroeconomic indicators (inflation, policy rate, GDP, TRM, unemployment)."""
    return await market_data_manager.get_macro_indicators(country)


@router.get("/providers", response_model=List[MarketStatus])
async def get_providers_status() -> List[MarketStatus]:
    """Inspect connectivity and latency across all market data adapters."""
    return await market_data_manager.get_all_providers_status()


@router.websocket("/ws/stream")
async def websocket_market_stream(websocket: WebSocket, symbol: str = "BTCUSDT"):
    """WebSocket stream emitting periodic simulated or real-time ticker ticks."""
    await websocket.accept()
    logger.info("Client connected to market WebSocket stream for %s", symbol)
    try:
        while True:
            snapshot = await market_data_manager.get_ticker_snapshot(symbol)
            if snapshot:
                await websocket.send_text(snapshot.model_dump_json())
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        logger.info("Client disconnected from market WebSocket stream for %s", symbol)
    except Exception as e:
        logger.error("WebSocket stream error for %s: %s", symbol, str(e))
        await websocket.close()
