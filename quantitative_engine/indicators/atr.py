"""Average True Range (ATR) implementation.
Measures market volatility using Welles Wilder's True Range smoothing.

Formulas:
    TR = max(High - Low, abs(High - Close_{prev}), abs(Low - Close_{prev}))
    ATR_t = (ATR_{t-1} * (period - 1) + TR_t) / period
"""

from typing import List, Optional
import pandas as pd
import numpy as np


def compute_true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Computes True Range for each bar."""
    prev_close = close.shift(1)
    hl = high - low
    hc = (high - prev_close).abs()
    lc = (low - prev_close).abs()

    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr


def compute_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Computes Wilder's smoothed ATR over specified period."""
    if len(close) < period:
        return pd.Series([np.nan] * len(close), index=close.index)

    tr = compute_true_range(high, low, close)
    # Wilder's smoothing using alpha = 1 / period
    atr = tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    return atr


def compute_atr_list(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> List[Optional[float]]:
    """Returns JSON-serializable list of ATR floats."""
    atr_series = compute_atr(high, low, close, period)
    return [None if np.isnan(v) else round(float(v), 4) for v in atr_series]
