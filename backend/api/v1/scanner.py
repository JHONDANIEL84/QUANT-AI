"""Market Scanner & Multi-Timeframe API Router — Phase 7 QUANT AI.

GET /api/v1/scanner/scan
    Executes a multi-asset quantitative screening sweep across selected markets.

GET /api/v1/scanner/mtf
    Analyzes structural multi-timeframe confluence between higher and lower timeframes.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional, Any
import asyncio

from data_providers.base.models import MarketBar
from data_providers.manager import MarketDataManager, market_data_manager
from quantitative_engine.scanner.models import (
    MarketScanResponse,
    MTFConfluenceResult,
    ScanOpportunity,
)
from quantitative_engine.scanner.scanner_engine import (
    CRYPTO_UNIVERSE,
    STOCK_UNIVERSE,
    BVC_UNIVERSE,
    scan_asset_bars_collection,
)
from quantitative_engine.scanner.mtf import analyze_mtf_confluence

router = APIRouter(prefix="/scanner", tags=["Market Scanner & MTF"])


def get_symbols_for_market(market: str) -> List[str]:
    """Returns candidate tickers for a given market filter."""
    m = market.lower()
    if m == "crypto":
        return CRYPTO_UNIVERSE
    elif m == "stock":
        return STOCK_UNIVERSE
    elif m == "bvc":
        return BVC_UNIVERSE
    else:
        # Default 'all': blend top assets from each market
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AAPL", "NVDA", "SPY", "ECOPETROL", "PFBCOLO"]


@router.get("/scan", response_model=MarketScanResponse, summary="Barrido cuantitativo multiactivo")
async def scan_market(
    market: str = Query("all", description="Filtro de mercado: all, crypto, stock, bvc"),
    interval: str = Query("1d", description="Temporalidad: 1d, 4h, 1h"),
    min_score: float = Query(45.0, ge=0.0, le=100.0, description="Puntuación mínima de oportunidad"),
    limit: int = Query(20, ge=1, le=50, description="Número máximo de oportunidades a retornar"),
):
    """Scans financial instruments and ranks high-conviction swing opportunities."""
    symbols = get_symbols_for_market(market)

    # Fetch bars concurrently
    tasks = [
        market_data_manager.get_historical_bars(symbol=sym, interval=interval, limit=120)
        for sym in symbols
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    bars_by_symbol: Dict[str, List[MarketBar]] = {}
    for sym, res in zip(symbols, results):
        if isinstance(res, list) and len(res) >= 15:
            bars_by_symbol[sym] = res

    if not bars_by_symbol:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudieron obtener datos históricos para los activos del mercado '{market}'.",
        )

    scan_res = scan_asset_bars_collection(
        bars_by_symbol=bars_by_symbol,
        market_filter=market,
        interval=interval,
        min_score=min_score,
    )
    scan_res.opportunities = scan_res.opportunities[:limit]
    return scan_res


@router.get("/mtf", response_model=MTFConfluenceResult, summary="Confluencia multitemporal (HTF vs LTF)")
async def get_mtf_confluence(
    symbol: str = Query("BTCUSDT", description="Símbolo del activo (ej: BTCUSDT, AAPL)"),
    htf: str = Query("1d", description="Temporalidad mayor (ej: 1d, 1w)"),
    ltf: str = Query("4h", description="Temporalidad menor (ej: 4h, 1h)"),
):
    """Evaluates trend and structural alignment between HTF and LTF."""
    try:
        htf_bars = await market_data_manager.get_historical_bars(symbol=symbol, interval=htf, limit=100)
        ltf_bars = await market_data_manager.get_historical_bars(symbol=symbol, interval=ltf, limit=100)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Error obteniendo barras para MTF: {exc}") from exc

    if not htf_bars or len(htf_bars) < 15 or not ltf_bars or len(ltf_bars) < 15:
        raise HTTPException(
            status_code=422,
            detail=f"Datos insuficientes para análisis multitemporal de {symbol}.",
        )

    return analyze_mtf_confluence(
        symbol=symbol,
        htf_interval=htf,
        htf_bars=htf_bars,
        ltf_interval=ltf,
        ltf_bars=ltf_bars,
    )
