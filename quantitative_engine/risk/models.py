"""Risk Engine Models — Fase 8 QUANT AI.

Tipos de datos para cálculo de posición, gestión de riesgo y portafolio simulado.
Todas las cantidades monetarias están en COP (pesos colombianos) excepto donde se indique.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PositionSizingMethod(str, Enum):
    FIXED_PERCENT = "fixed_percent"      # % fijo del capital
    KELLY = "kelly"                       # Criterio de Kelly
    ATR_BASED = "atr_based"              # Volatilidad ATR para ajustar tamaño
    FIXED_COP = "fixed_cop"              # Monto fijo en COP


class TradeDirection(str, Enum):
    LONG = "long"
    SHORT = "short"


class RiskRating(str, Enum):
    VERY_LOW = "muy_bajo"       # R:R >= 4
    LOW = "bajo"                # R:R 3-4
    MODERATE = "moderado"       # R:R 2-3
    HIGH = "alto"               # R:R 1-2
    EXCESSIVE = "excesivo"      # R:R < 1


# ---------------------------------------------------------------------------
# Position Sizing
# ---------------------------------------------------------------------------

class PositionSizeRequest(BaseModel):
    """Parámetros de entrada para calcular tamaño de posición."""

    # Capital disponible en COP
    capital_cop: float = Field(..., gt=0, description="Capital total disponible en COP")

    # Precio de entrada y stop loss
    entry_price: float = Field(..., gt=0, description="Precio de entrada del activo")
    stop_loss_price: float = Field(..., gt=0, description="Precio de stop loss (invalidación)")

    # Precio objetivo (take profit)
    target_price: Optional[float] = Field(None, gt=0, description="Precio objetivo (take profit)")

    # Parámetros de riesgo
    risk_percent: float = Field(1.0, gt=0, le=10, description="% de capital a arriesgar por operación")
    method: PositionSizingMethod = Field(PositionSizingMethod.FIXED_PERCENT)

    # Parámetros Kelly (solo para método Kelly)
    win_rate: Optional[float] = Field(None, ge=0, le=1, description="Tasa de acierto histórica (0-1)")
    avg_win_loss_ratio: Optional[float] = Field(None, gt=0, description="Ratio promedio ganancia/pérdida")

    # Parámetros ATR (solo para método ATR)
    atr_value: Optional[float] = Field(None, gt=0, description="Valor ATR actual del activo")
    atr_multiplier: float = Field(2.0, gt=0, description="Multiplicador de ATR para stop dinámico")

    # Tipo de cambio USD→COP (si el activo cotiza en USD)
    usd_cop_rate: Optional[float] = Field(None, gt=0, description="TRM COP/USD si activo cotiza en USD")

    direction: TradeDirection = Field(TradeDirection.LONG)


class PositionSizeResult(BaseModel):
    """Resultado del cálculo de tamaño de posición."""

    method: PositionSizingMethod
    direction: TradeDirection

    # Cantidades
    units: float = Field(..., description="Número de unidades/contratos/acciones")
    position_value_cop: float = Field(..., description="Valor total de la posición en COP")
    position_value_usd: Optional[float] = Field(None, description="Valor en USD si aplica")

    # Riesgo calculado
    risk_amount_cop: float = Field(..., description="Monto en riesgo en COP")
    risk_percent_actual: float = Field(..., description="% real del capital en riesgo")

    # Niveles de precio
    entry_price: float
    stop_loss_price: float
    target_price: Optional[float] = None

    # R:R
    risk_reward_ratio: Optional[float] = Field(None, description="Ratio Riesgo:Recompensa")
    risk_rating: RiskRating

    # Texto epistémico
    observation: str = Field(..., description="Hechos verificados del cálculo")
    hypothesis: str = Field(..., description="Proyección con invalidación explícita")

    calculated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Drawdown & Equity Curve
# ---------------------------------------------------------------------------

class DrawdownMetrics(BaseModel):
    """Métricas de drawdown de una curva de equity."""

    max_drawdown_pct: float = Field(..., description="Máximo drawdown en %")
    max_drawdown_cop: float = Field(..., description="Máximo drawdown en COP")
    max_drawdown_start_idx: int
    max_drawdown_end_idx: int

    current_drawdown_pct: float = Field(..., description="Drawdown actual desde el último pico")
    current_drawdown_cop: float

    longest_drawdown_bars: int = Field(..., description="Duración más larga de drawdown (en barras/periodos)")
    recovery_factor: float = Field(..., description="Retorno total / Max Drawdown")
    calmar_ratio: float = Field(..., description="CAGR / Max Drawdown absoluto")

    peak_equity_cop: float
    trough_equity_cop: float


# ---------------------------------------------------------------------------
# Portfolio Simulator
# ---------------------------------------------------------------------------

class PortfolioTrade(BaseModel):
    """Registro de una operación individual en el portafolio simulado."""

    symbol: str
    direction: TradeDirection
    entry_date: datetime
    exit_date: Optional[datetime] = None
    entry_price: float
    exit_price: Optional[float] = None
    units: float
    commission_cop: float = Field(0.0, description="Comisión en COP")

    # Resultados (calculados al cerrar)
    pnl_cop: Optional[float] = None
    pnl_percent: Optional[float] = None
    is_winner: Optional[bool] = None
    r_multiple: Optional[float] = Field(None, description="Resultado en múltiplos de R")

    # Riesgo original
    stop_loss_price: Optional[float] = None
    risk_amount_cop: Optional[float] = None


class PortfolioState(BaseModel):
    """Estado actual del portafolio simulado en COP."""

    initial_capital_cop: float
    current_equity_cop: float
    cash_cop: float
    unrealized_pnl_cop: float = 0.0
    realized_pnl_cop: float = 0.0

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    avg_win_cop: float = 0.0
    avg_loss_cop: float = 0.0
    profit_factor: float = 0.0
    expectancy_cop: float = Field(0.0, description="Esperanza matemática por operación en COP")

    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0

    open_positions: List[PortfolioTrade] = Field(default_factory=list)
    closed_trades: List[PortfolioTrade] = Field(default_factory=list)

    equity_curve: List[float] = Field(default_factory=list, description="Curva de equity en COP")

    observation: str = "Portafolio simulado en COP. Sin historial de operaciones aún."
    last_updated: datetime = Field(default_factory=datetime.utcnow)
