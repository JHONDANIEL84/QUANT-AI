"""Fibonacci Retracements and Extensions module.
Ratios:
    0.0 (Extreme)
    0.236 (23.6%)
    0.382 (38.2%)
    0.500 (Equilibrium / Dow 50%)
    0.618 (Golden Ratio)
    0.786 (Deep Retracement)
    1.000 (100% Retracement)
    1.618 (Golden Extension)
"""

from typing import Dict
from quantitative_engine.indicators.base import FibonacciLevels

FIBONACCI_RATIOS = [0.0, 0.236, 0.382, 0.500, 0.618, 0.786, 1.000, 1.618]


def compute_fibonacci_levels(
    high: float,
    low: float,
    is_uptrend: bool = True,
) -> FibonacciLevels:
    """Computes exact Fibonacci price levels between high and low extremes.

    Args:
        high: Highest swing price.
        low: Lowest swing price.
        is_uptrend: True if impulse moved from low to high; False if moved from high to low.

    Returns:
        FibonacciLevels: Dict of ratio -> price level.
    """
    diff = high - low
    levels: Dict[str, float] = {}

    for ratio in FIBONACCI_RATIOS:
        if is_uptrend:
            # Retracement down from High
            price = high - (diff * ratio)
        else:
            # Retracement up from Low
            price = low + (diff * ratio)
        levels[str(ratio)] = round(price, 4)

    return FibonacciLevels(
        high=high,
        low=low,
        is_uptrend=is_uptrend,
        levels=levels,
    )
