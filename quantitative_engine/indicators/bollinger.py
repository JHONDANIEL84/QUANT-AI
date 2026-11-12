"""Bollinger Bands implementation.
Formulas:
    MiddleBand = SMA(Close, period=20)
    StdDev = StandardDeviation(Close, period=20)
    UpperBand = MiddleBand + (std_multiplier * StdDev)
    LowerBand = MiddleBand - (std_multiplier * StdDev)
    Bandwidth = (UpperBand - LowerBand) / MiddleBand
    PercentB = (Close - LowerBand) / (UpperBand - LowerBand)
"""

from typing import List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from quantitative_engine.indicators.base import BollingerPoint


def compute_bollinger_bands(
    close_series: pd.Series,
    period: int = 20,
    std_multiplier: float = 2.0,
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """Computes Middle, Upper, Lower, Bandwidth, and %B series."""
    if len(close_series) < period:
        nan_s = pd.Series([np.nan] * len(close_series), index=close_series.index)
        return nan_s, nan_s, nan_s, nan_s, nan_s

    middle = close_series.rolling(window=period).mean()
    std = close_series.rolling(window=period).std(ddof=0)

    upper = middle + (std_multiplier * std)
    lower = middle - (std_multiplier * std)

    bandwidth = (upper - lower) / middle.replace(0, np.nan)
    denom = upper - lower
    percent_b = (close_series - lower) / denom.replace(0, np.nan)

    return middle, upper, lower, bandwidth, percent_b


def compute_bollinger_points(
    timestamps: List[Any],
    close_series: pd.Series,
    period: int = 20,
    std_multiplier: float = 2.0,
) -> List[Optional[BollingerPoint]]:
    """Returns typed BollingerPoint list matching timestamps."""
    mid, up, low, bw, pb = compute_bollinger_bands(close_series, period, std_multiplier)
    points: List[Optional[BollingerPoint]] = []

    for i in range(len(close_series)):
        m = mid.iloc[i]
        u = up.iloc[i]
        l = low.iloc[i]
        b = bw.iloc[i]
        p = pb.iloc[i]

        if np.isnan(m) or np.isnan(u) or np.isnan(l):
            points.append(None)
        else:
            points.append(
                BollingerPoint(
                    timestamp=timestamps[i],
                    middle=round(float(m), 4),
                    upper=round(float(u), 4),
                    lower=round(float(l), 4),
                    bandwidth=round(float(b), 4) if not np.isnan(b) else 0.0,
                    percent_b=round(float(p), 4) if not np.isnan(p) else 0.5,
                )
            )
    return points
