"""EMA + RSI Trend Strategy — Fase 9 QUANT AI.

Reglas cuantitativas:
  - Señal BUY:
      1. EMA 20 > EMA 50 (tendencia alcista)
      2. RSI 14 entre 45 y 65 (momentum favorable, no sobrecomprado)
      3. Cierre > EMA 20
      4. Stop Loss: Mínimo de las últimas 5 barras (o 2 × ATR)
      5. Take Profit: Entrada + 2.5 × Riesgo (R:R = 2.5)
  - Señal SELL (Short):
      1. EMA 20 < EMA 50 (tendencia bajista)
      2. RSI 14 entre 35 y 55 (momentum bajista, no sobrevendido)
      3. Cierre < EMA 20
      4. Stop Loss: Máximo de las últimas 5 barras (o 2 × ATR)
      5. Take Profit: Entrada - 2.5 × Riesgo (R:R = 2.5)
  - Salida:
      1. Cierre opuesto de medias móviles
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np

from data_providers.base.models import MarketBar
from quantitative_engine.backtesting.models import BacktestSignal, SignalType
from quantitative_engine.backtesting.strategies.base import BaseStrategy
from quantitative_engine.indicators.ema import compute_ema
from quantitative_engine.indicators.rsi import compute_rsi


class EmaRsiStrategy(BaseStrategy):
    """Estrategia de seguimiento de tendencia con EMA y confirmación de RSI."""

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        self.fast_ema_period = int(self.params.get("fast_ema", 20))
        self.slow_ema_period = int(self.params.get("slow_ema", 50))
        self.rsi_period = int(self.params.get("rsi_period", 14))
        self.rr_multiplier = float(self.params.get("rr_multiplier", 2.5))
        self.lookback_stop = int(self.params.get("lookback_stop", 5))

    def generate_signal(
        self,
        current_idx: int,
        bars: List[MarketBar],
        active_position: Optional[str] = None,
    ) -> Optional[BacktestSignal]:
        # Requiere al menos slow_ema_period + 5 barras de historia
        min_required = max(self.slow_ema_period, self.fast_ema_period) + 5
        if current_idx < min_required:
            return None

        # Segmento causal estrictamente hasta current_idx
        causal_bars = bars[: current_idx + 1]
        closes = pd.Series([b.close for b in causal_bars], dtype=float)

        ema_fast = compute_ema(closes, self.fast_ema_period)
        ema_slow = compute_ema(closes, self.slow_ema_period)
        rsi = compute_rsi(closes, self.rsi_period)

        c_fast = float(ema_fast.iloc[-1])
        c_slow = float(ema_slow.iloc[-1])
        c_rsi = float(rsi.iloc[-1])
        curr_bar = causal_bars[-1]
        c_price = curr_bar.close

        # Verificación de salida si ya hay posición
        if active_position == "long" and c_fast < c_slow:
            return BacktestSignal(
                bar_index=current_idx,
                timestamp=curr_bar.timestamp,
                signal_type=SignalType.EXIT_LONG,
                price=c_price,
                rationale=f"Cruce bajista de medias: EMA {self.fast_ema_period} ({c_fast:.2f}) < EMA {self.slow_ema_period} ({c_slow:.2f}).",
            )
        if active_position == "short" and c_fast > c_slow:
            return BacktestSignal(
                bar_index=current_idx,
                timestamp=curr_bar.timestamp,
                signal_type=SignalType.EXIT_SHORT,
                price=c_price,
                rationale=f"Cruce alcista de medias: EMA {self.fast_ema_period} ({c_fast:.2f}) > EMA {self.slow_ema_period} ({c_slow:.2f}).",
            )

        # Si ya hay posición abierta, no generar nueva entrada
        if active_position is not None:
            return None

        # Señal BUY
        if c_fast > c_slow and c_price > c_fast and 45.0 <= c_rsi <= 65.0:
            recent_lows = [b.low for b in causal_bars[-self.lookback_stop:]]
            stop_loss = min(recent_lows)
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
                        f"Tendencia alcista: EMA {self.fast_ema_period} > EMA {self.slow_ema_period}, "
                        f"RSI en momentum saludable ({c_rsi:.1f}), precio sobre EMA rápida."
                    ),
                    metadata={"ema_fast": c_fast, "ema_slow": c_slow, "rsi": c_rsi},
                )

        # Señal SELL
        if c_fast < c_slow and c_price < c_fast and 35.0 <= c_rsi <= 55.0:
            recent_highs = [b.high for b in causal_bars[-self.lookback_stop:]]
            stop_loss = max(recent_highs)
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
                        f"Tendencia bajista: EMA {self.fast_ema_period} < EMA {self.slow_ema_period}, "
                        f"RSI en debilidad controlada ({c_rsi:.1f}), precio bajo EMA rápida."
                    ),
                    metadata={"ema_fast": c_fast, "ema_slow": c_slow, "rsi": c_rsi},
                )

        return None
