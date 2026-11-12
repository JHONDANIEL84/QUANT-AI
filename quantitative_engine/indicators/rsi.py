"""Relative Strength Index (RSI) implementation.
Implements J. Welles Wilder Jr.'s original smoothed RSI algorithm.

Formulas:
    Change = Close_t - Close_{t-1}
    Gain = max(Change, 0)
    Loss = max(-Change, 0)
    SmoothedGain_t = (SmoothedGain_{t-1} * (period - 1) + Gain_t) / period
    SmoothedLoss_t = (SmoothedLoss_{t-1} * (period - 1) + Loss_t) / period
    RS = SmoothedGain / SmoothedLoss
    RSI = 100 - (100 / (1 + RS))
"""

from typing import List, Optional
import pandas as pd
import numpy as np


def compute_rsi(close_series: pd.Series, period: int = 14) -> pd.Series:
    """Computes Wilder's Smoothed RSI over specified period.

    Args:
        close_series: Series of close prices.
        period: Number of periods (default 14).

    Returns:
        pd.Series: RSI values bounded in [0.0, 100.0].
    """
    if len(close_series) < period:
        return pd.Series([np.nan] * len(close_series), index=close_series.index)

    delta = close_series.diff()

    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    # Wilder's smoothing using alpha = 1 / period
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))

    # Handle division by zero edge cases
    rsi = rsi.where(avg_loss != 0, 100.0)
    rsi = rsi.where(avg_gain != 0, 0.0)

    # Clip to absolute bounds [0, 100]
    return rsi.clip(lower=0.0, upper=100.0)


def compute_rsi_list(close_series: pd.Series, period: int = 14) -> List[Optional[float]]:
    """Convenience helper returning JSON-serializable list of floats or None."""
    rsi_series = compute_rsi(close_series, period)
    return [None if np.isnan(v) else round(float(v), 2) for v in rsi_series]
