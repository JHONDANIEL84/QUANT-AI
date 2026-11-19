"""Risk Management API — Fase 8 QUANT AI.

Endpoints:
  POST /api/v1/risk/position-size   — Calcula tamaño óptimo de posición en COP
  GET  /api/v1/risk/drawdown        — Calcula métricas de drawdown sobre serie de equity
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from quantitative_engine.risk.models import (
    PositionSizeRequest,
    PositionSizeResult,
    DrawdownMetrics,
)
from quantitative_engine.risk.position_sizer import calculate_position_size
from quantitative_engine.risk.drawdown import calculate_drawdown_metrics

router = APIRouter(prefix="/risk", tags=["risk"])


# ---------------------------------------------------------------------------
# 1. Position Sizing
# ---------------------------------------------------------------------------

@router.post(
    "/position-size",
    response_model=PositionSizeResult,
    summary="Calcula tamaño de posición óptimo en COP",
    description=(
        "Recibe parámetros del trade (capital, entrada, stop, objetivo) y retorna "
        "el número de unidades, el monto en riesgo en COP y el ratio R:R con "
        "contexto epistémico (observación + hipótesis con invalidación explícita)."
    ),
)
def post_position_size(req: PositionSizeRequest) -> PositionSizeResult:
    """Calcula posición usando el método seleccionado (fixed_percent, kelly, atr_based, fixed_cop)."""
    try:
        return calculate_position_size(req)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error interno en cálculo de posición: {exc}")


# ---------------------------------------------------------------------------
# 2. Drawdown Calculator
# ---------------------------------------------------------------------------

class DrawdownRequest(BaseModel):
    """Serie de equity para cálculo de drawdown."""
    equity_curve: List[float] = Field(..., min_length=2, description="Curva de equity en COP (cronológica)")
    periods_per_year: int = Field(252, ge=1, le=365, description="Periodos anuales (252=diario, 52=semanal)")


@router.post(
    "/drawdown",
    response_model=DrawdownMetrics,
    summary="Calcula métricas de drawdown sobre curva de equity",
    description=(
        "Recibe una curva de equity en COP y retorna máximo drawdown, "
        "drawdown actual, duración máxima, Recovery Factor y Calmar Ratio."
    ),
)
def post_drawdown(req: DrawdownRequest) -> DrawdownMetrics:
    """Calcula todas las métricas de drawdown sobre la curva de equity."""
    try:
        return calculate_drawdown_metrics(req.equity_curve, req.periods_per_year)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error en cálculo de drawdown: {exc}")
