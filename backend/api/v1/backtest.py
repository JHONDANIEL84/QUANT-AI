"""Backtesting Lab API — Fase 9 QUANT AI.

Endpoint:
  POST /api/v1/backtest/run   — Ejecuta simulación cuantitativa reproducible
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from data_providers.base.models import MarketBar
from data_providers.manager import market_data_manager
from quantitative_engine.backtesting.models import (
    BacktestConfig,
    BacktestResult,
)
from quantitative_engine.backtesting.engine import BacktestEngine

router = APIRouter(prefix="/backtest", tags=["Backtesting Lab"])


class BacktestRunRequest(BaseModel):
    """Payload para ejecutar un backtest."""

    config: BacktestConfig = Field(..., description="Parámetros de capital, riesgo y estrategia")
    bars: Optional[List[MarketBar]] = Field(
        None,
        description="Barras históricas opcionales. Si se omiten, se descargan mediante market_data_manager.",
    )
    limit_bars: int = Field(250, ge=30, le=1000, description="Cantidad de barras si se descargan automáticamente")


@router.post(
    "/run",
    response_model=BacktestResult,
    summary="Ejecuta backtesting walk-forward causal",
    description=(
        "Simula una estrategia cuantitativa sobre datos históricos con ejecución estricta "
        "en la siguiente barra (no look-ahead bias), modelando comisiones y slippage. "
        "Calcula métricas completas (Win Rate, Profit Factor, Drawdown, Sharpe, Sortino) en COP."
    ),
)
async def run_backtest(req: BacktestRunRequest) -> BacktestResult:
    """Ejecuta la simulación con las barras provistas o descargadas."""
    bars = req.bars

    if not bars:
        try:
            bars = await market_data_manager.get_historical_bars(
                symbol=req.config.symbol,
                interval=req.config.interval,
                limit=req.limit_bars,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Error al obtener datos de mercado para '{req.config.symbol}': {exc}",
            )

    if not bars or len(bars) < 30:
        raise HTTPException(
            status_code=400,
            detail=f"Se requieren al menos 30 barras históricas para backtesting (obtenidas: {len(bars) if bars else 0}).",
        )

    try:
        engine = BacktestEngine(req.config)
        return engine.run(bars)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error en ejecución del backtest: {exc}")
