"""Backtesting Data Models — Fase 9 QUANT AI.

Estructuras de datos para simulación histórica walk-forward causal,
señales cuantitativas, ejecución de órdenes y métricas de desempeño.
Todas las métricas monetarias en COP.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SignalType(str, Enum):
    BUY = "buy"          # Entrada en largo (Long)
    SELL = "sell"        # Entrada en corto (Short)
    EXIT_LONG = "exit_long"
    EXIT_SHORT = "exit_short"
    HOLD = "hold"


class ExitReason(str, Enum):
    STOP_LOSS = "stop_loss"               # Stop loss alcanzado en mecha/cierre
    TAKE_PROFIT = "take_profit"           # Objetivo alcanzado
    SIGNAL_REVERSAL = "signal_reversal"   # Señal opuesta detectada
    TRAILING_STOP = "trailing_stop"       # Trailing stop dinámico
    TIMEOUT = "timeout"                   # Límite máximo de barras en posición
    END_OF_DATA = "end_of_data"           # Fin de la serie histórica


class StrategyName(str, Enum):
    SMC_LIQUIDITY = "smc_liquidity"       # BOS/CHOCH + Order Blocks + Sweeps
    EMA_RSI_TREND = "ema_rsi_trend"       # Cruce de EMA 20/50 + confirmación RSI
    BREAKOUT_MOMENTUM = "breakout_momentum" # Ruptura de zonas de compresión


# ---------------------------------------------------------------------------
# Signals & Trades
# ---------------------------------------------------------------------------

class BacktestSignal(BaseModel):
    """Señal emitida por una estrategia en la barra t."""

    bar_index: int
    timestamp: datetime
    signal_type: SignalType
    price: float = Field(..., description="Precio de referencia en el momento de la señal")
    stop_loss: Optional[float] = Field(None, description="Precio de invalidación / stop loss")
    take_profit: Optional[float] = Field(None, description="Precio objetivo / take profit")
    rationale: str = Field(..., description="Justificación cuantitativa de la señal")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BacktestTrade(BaseModel):
    """Registro de una operación completada durante el backtest."""

    trade_id: int
    symbol: str
    direction: str = Field(..., description="'long' o 'short'")

    entry_bar_idx: int
    exit_bar_idx: int
    entry_time: datetime
    exit_time: datetime

    entry_price: float
    exit_price: float
    units: float

    # Costos de ejecución modelados
    commission_cop: float = Field(0.0, description="Comisiones totales pagadas en COP")
    slippage_cop: float = Field(0.0, description="Costo de deslizamiento en COP")

    # Resultados monetarios en COP
    gross_pnl_cop: float
    net_pnl_cop: float
    pnl_percent: float
    r_multiple: Optional[float] = None

    is_winner: bool
    exit_reason: ExitReason
    holding_bars: int = Field(..., description="Número de barras en posición")


# ---------------------------------------------------------------------------
# Configuration & Result
# ---------------------------------------------------------------------------

class BacktestConfig(BaseModel):
    """Configuración del experimento de backtesting."""

    symbol: str = "BTCUSDT"
    interval: str = "1d"
    initial_capital_cop: float = Field(50_000_000.0, gt=0, description="Capital inicial en COP")

    # Gestión de riesgo
    risk_per_trade_pct: float = Field(1.5, gt=0, le=5.0, description="% de capital arriesgado por trade")
    max_holding_bars: int = Field(60, ge=1, le=500, description="Máximo de barras por operación")

    # Fricciones de mercado realistas
    commission_pct: float = Field(0.001, ge=0, le=0.01, description="Comisión por operación (0.1% = 0.001)")
    slippage_pct: float = Field(0.0005, ge=0, le=0.005, description="Deslizamiento estimado (0.05% = 0.0005)")

    # Estrategia
    strategy_name: StrategyName = StrategyName.SMC_LIQUIDITY
    strategy_params: Dict[str, Any] = Field(default_factory=dict)

    # TRM si cotiza en USD
    usd_cop_rate: Optional[float] = Field(None, gt=0, description="TRM USD/COP si activo en USD")


class BacktestResult(BaseModel):
    """Resultados consolidados de la simulación histórica."""

    config: BacktestConfig

    # Métricas de operaciones
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # PnL en COP
    initial_capital_cop: float
    final_equity_cop: float
    gross_profit_cop: float
    gross_loss_cop: float
    net_profit_cop: float
    net_profit_percent: float

    # Ratios cuantitativos
    profit_factor: float
    expectancy_cop: float
    cagr_percent: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # Drawdown
    max_drawdown_pct: float
    max_drawdown_cop: float
    avg_trade_duration_bars: float

    # Curva de equity y registro de trades
    equity_curve: List[float] = Field(default_factory=list, description="Serie temporal de equity en COP")
    trades: List[BacktestTrade] = Field(default_factory=list)

    # Epistémico: Hechos vs Hipótesis
    observation: str = Field(..., description="Hechos verificados del backtest")
    hypothesis: str = Field(..., description="Validez estadística y condiciones de invalidación")

    executed_at: datetime = Field(default_factory=datetime.utcnow)
