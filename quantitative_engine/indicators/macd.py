"""Moving Average Convergence Divergence (MACD) implementation.
Formulas:
    FastEMA = EMA(Close, 12)
    SlowEMA = EMA(Close, 26)
    MACD_Line = FastEMA - SlowEMA
    Signal_Line = EMA(MACD_Line, 9)
    Histogram = MACD_Line - Signal_Line
"""

from typing import List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from quantitative_engine.indicators.base import MACDPoint


def compute_macd(
    close_series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Computes MACD line, Signal line, and Histogram series."""
    if len(close_series) < slow_period:
        nan_series = pd.Series([np.nan] * len(close_series), index=close_series.index)
        return nan_series, nan_series, nan_series

    fast_ema = close_series.ewm(span=fast_period, adjust=False).mean()
    slow_ema = close_series.ewm(span=slow_period, adjust=False).mean()

    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def compute_macd_points(
    timestamps: List[Any],
    close_series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> List[Optional[MACDPoint]]:
    """Returns typed MACDPoint list matching timestamps."""
    macd_l, sig_l, hist = compute_macd(close_series, fast_period, slow_period, signal_period)
    points: List[Optional[MACDPoint]] = []

    for i in range(len(close_series)):
        m = macd_l.iloc[i]
        s = sig_l.iloc[i]
        h = hist.iloc[i]
        if np.isnan(m) or np.isnan(s) or np.isnan(h):
            points.append(None)
        else:
            points.append(
                MACDPoint(
                    timestamp=timestamps[i],
                    macd=round(float(m), 4),
                    signal=round(float(s), 4),
                    histogram=round(float(h), 4),
                )
            )
    return points
