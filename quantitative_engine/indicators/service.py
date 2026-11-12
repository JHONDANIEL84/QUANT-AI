"""Central Quantitative Indicator Engine.
Computes all requested technical indicators in a high-performance vectorized pass.
"""

from typing import List, Optional
import pandas as pd
import numpy as np

from data_providers.base.models import MarketBar
from quantitative_engine.indicators.base import (
    ComputedIndicatorsResponse,
    FibonacciLevels,
)
from quantitative_engine.indicators.ema import compute_all_emas
from quantitative_engine.indicators.rsi import compute_rsi_list
from quantitative_engine.indicators.macd import compute_macd_points
from quantitative_engine.indicators.atr import compute_atr_list
from quantitative_engine.indicators.vwap import compute_vwap_list
from quantitative_engine.indicators.bollinger import compute_bollinger_points
from quantitative_engine.indicators.fibonacci import compute_fibonacci_levels


class IndicatorEngine:
    """Service for computing vector indicators on market bars."""

    @staticmethod
    def compute_all(
        bars: List[MarketBar],
        symbol: str = "ASSET",
        interval: str = "1d",
    ) -> ComputedIndicatorsResponse:
        """Computes all technical indicators for the provided bar list."""
        if not bars:
            return ComputedIndicatorsResponse(
                symbol=symbol,
                interval=interval,
                timestamps=[],
            )

        # Convert to pandas DataFrame for vectorization
        df = pd.DataFrame(
            [
                {
                    "timestamp": b.timestamp,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                }
                for b in bars
            ]
        )

        timestamps = df["timestamp"].tolist()
        close = df["close"]
        high = df["high"]
        low = df["low"]
        vol = df["volume"]

        # 1. EMAs (20, 50, 100, 200)
        emas = compute_all_emas(close, periods=[20, 50, 100, 200])

        # 2. RSI 14
        rsi_14 = compute_rsi_list(close, period=14)

        # 3. MACD 12-26-9
        macd_points = compute_macd_points(timestamps, close, 12, 26, 9)

        # 4. ATR 14
        atr_14 = compute_atr_list(high, low, close, period=14)

        # 5. VWAP
        vwap = compute_vwap_list(high, low, close, vol)

        # 6. Bollinger Bands
        bollinger = compute_bollinger_points(timestamps, close, period=20, std_multiplier=2.0)

        # 7. Fibonacci (over visible high and low)
        max_h = float(high.max())
        min_l = float(low.min())
        is_up = close.iloc[-1] >= close.iloc[0] if len(close) > 0 else True
        fib = compute_fibonacci_levels(high=max_h, low=min_l, is_uptrend=is_up)

        return ComputedIndicatorsResponse(
            symbol=symbol,
            interval=interval,
            timestamps=timestamps,
            ema_20=emas.get("ema_20"),
            ema_50=emas.get("ema_50"),
            ema_100=emas.get("ema_100"),
            ema_200=emas.get("ema_200"),
            rsi_14=rsi_14,
            macd=macd_points,
            atr_14=atr_14,
            vwap=vwap,
            bollinger_bands=bollinger,
            fibonacci=fib,
        )


indicator_engine = IndicatorEngine()
