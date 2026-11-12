"""Exponential Moving Average (EMA) implementation.
Formula:
    alpha = 2 / (period + 1)
    EMA_t = (Close_t * alpha) + (EMA_{t-1} * (1 - alpha))
"""

from typing import List, Optional
import pandas as pd
import numpy as np


def compute_ema(series: pd.Series, period: int = 20) -> pd.Series:
    """Computes Exponential Moving Average using exact smoothing factor alpha = 2 / (period + 1).

    Args:
        series: Pandas series of closing prices.
        period: Smoothing period (e.g. 20, 50, 100, 200).

    Returns:
        pd.Series: EMA values matching index of input series.
    """
    if len(series) == 0:
        return pd.Series(dtype=float)
    if period <= 0:
        raise ValueError("Period must be greater than zero.")

    return series.ewm(span=period, adjust=False).mean()


def compute_all_emas(
    close_series: pd.Series,
    periods: List[int] = [20, 50, 100, 200],
) -> dict[str, List[Optional[float]]]:
    """Computes standard EMAs (20, 50, 100, 200) and formats output as clean floats with NaNs converted to None."""
    results = {}
    for p in periods:
        ema_vals = compute_ema(close_series, p)
        # Convert NaN to None for JSON serialization
        results[f"ema_{p}"] = [
            None if np.isnan(v) else round(float(v), 4) for v in ema_vals
        ]
    return results
