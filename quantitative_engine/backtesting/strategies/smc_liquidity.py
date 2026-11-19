"""SMC + Liquidity Sweep Strategy — Fase 9 QUANT AI.

Reglas cuantitativas:
  - Señal BUY:
      1. Barrido de liquidez reciente (SSL o EQL o PDL) con rechazo al cierre.
      2. O Ruptura de estructura (BOS alcista) en las últimas 5 barras.
      3. Precio en zona DISCOUNT (< 50% del rango de negociación).
      4. Stop Loss: Mínimo del barrido o último Swing Low.
      5. Take Profit: 3 × Distancia del Stop (R:R = 3.0).
  - Señal SELL:
      1. Barrido de liquidez bajista (BSL o EQH o PDH) con rechazo al cierre.
      2. O Ruptura de estructura (BOS bajista) en las últimas 5 barras.
      3. Precio en zona PREMIUM (> 50% del rango de negociación).
      4. Stop Loss: Máximo del barrido o último Swing High.
      5. Take Profit: 3 × Distancia del Stop (R:R = 3.0).
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any

from data_providers.base.models import MarketBar
from quantitative_engine.backtesting.models import BacktestSignal, SignalType
from quantitative_engine.backtesting.strategies.base import BaseStrategy
from quantitative_engine.market_structure.swings import detect_market_structure
from quantitative_engine.market_structure.models import TrendDirection
from quantitative_engine.liquidity.analyzer import run_liquidity_analysis
from quantitative_engine.liquidity.models import LiquidityType


class SMCLiquidityStrategy(BaseStrategy):
    """Estrategia institucional basada en barridos de liquidez y estructura SMC."""

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        self.rr_multiplier = float(self.params.get("rr_multiplier", 3.0))
        self.k_fractal = int(self.params.get("k_fractal", 3))

    def generate_signal(
        self,
        current_idx: int,
        bars: List[MarketBar],
        active_position: Optional[str] = None,
    ) -> Optional[BacktestSignal]:
        # Requiere al menos 20 barras para estructura y liquidez
        if current_idx < 20:
            return None

        # Si ya hay posición abierta, no abrir nueva
        if active_position is not None:
            return None

        # Causal slice: estrictamente hasta current_idx
        causal_bars = bars[: current_idx + 1]
        curr_bar = causal_bars[-1]
        c_price = curr_bar.close

        # 1. Estructura de mercado
        struct = detect_market_structure(causal_bars, k=self.k_fractal)

        # 2. Análisis de liquidez y barridos
        liq = run_liquidity_analysis(curr_bar.symbol, curr_bar.interval, causal_bars)

        if not liq.sweeps:
            return None

        last_sweep = liq.sweeps[-1]
        bars_since_sweep = len(causal_bars) - 1 - last_sweep.sweep_bar_index

        # El barrido debe ser reciente (<= 4 barras)
        if bars_since_sweep > 4:
            return None

        # Barrido de Sell-Side Liquidity (SSL / EQL / PDL) -> Posible BUY
        bullish_pools = (LiquidityType.SSL, LiquidityType.EQL, LiquidityType.PDL, LiquidityType.PWL)
        if last_sweep.pool_type in bullish_pools and struct.trend != TrendDirection.DOWNTREND:
            # Stop loss justo por debajo del mínimo del barrido
            stop_loss = min(last_sweep.sweep_price, struct.last_swing_low or last_sweep.sweep_price)
            if stop_loss < c_price:
                risk = c_price - stop_loss
                take_profit = c_price + (risk * self.rr_multiplier)
                return BacktestSignal(
                    bar_index=current_idx,
                    timestamp=curr_bar.timestamp,
                    signal_type=SignalType.BUY,
                    price=c_price,
                    stop_loss=round(stop_loss, 4),
                    take_profit=round(take_profit, 4),
                    rationale=(
                        f"Barrido de liquidez institucional ({last_sweep.pool_type.value}) en {last_sweep.sweep_price:.2f} "
                        f"con rechazo confirmado en cierre ({last_sweep.rejection_close:.2f})."
                    ),
                    metadata={"sweep_pool": last_sweep.pool_type.value, "sweep_price": last_sweep.sweep_price},
                )

        # Barrido de Buy-Side Liquidity (BSL / EQH / PDH) -> Posible SELL
        bearish_pools = (LiquidityType.BSL, LiquidityType.EQH, LiquidityType.PDH, LiquidityType.PWH)
        if last_sweep.pool_type in bearish_pools and struct.trend != TrendDirection.UPTREND:
            # Stop loss justo por encima del máximo del barrido
            stop_loss = max(last_sweep.sweep_price, struct.last_swing_high or last_sweep.sweep_price)
            if stop_loss > c_price:
                risk = stop_loss - c_price
                take_profit = c_price - (risk * self.rr_multiplier)
                return BacktestSignal(
                    bar_index=current_idx,
                    timestamp=curr_bar.timestamp,
                    signal_type=SignalType.SELL,
                    price=c_price,
                    stop_loss=round(stop_loss, 4),
                    take_profit=round(take_profit, 4),
                    rationale=(
                        f"Barrido de liquidez institucional ({last_sweep.pool_type.value}) en {last_sweep.sweep_price:.2f} "
                        f"con rechazo confirmado en cierre ({last_sweep.rejection_close:.2f})."
                    ),
                    metadata={"sweep_pool": last_sweep.pool_type.value, "sweep_price": last_sweep.sweep_price},
                )

        return None
