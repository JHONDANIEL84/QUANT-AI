"""Liquidity Sweeps & Stop Hunts Engine — Phase 6 QUANT AI.

Identifies institutional stop hunts where extreme price wicks penetrate a key liquidity pool
(EQH, EQL, BSL, SSL, PDH, PDL) but candle bodies close inside with immediate rejection.
"""

from typing import List, Tuple
from datetime import datetime

from data_providers.base.models import MarketBar
from quantitative_engine.liquidity.models import (
    LiquidityPool,
    LiquiditySweepEvent,
    LiquidityType,
    SweepStatus,
)


def detect_liquidity_sweeps(
    bars: List[MarketBar],
    pools: List[LiquidityPool],
) -> List[LiquiditySweepEvent]:
    """Scans price series for confirmed liquidity sweeps across identified liquidity pools.

    Args:
        bars: Chronological list of MarketBars.
        pools: Detected liquidity pools (EQH, EQL, BSL, SSL).

    Returns:
        List of confirmed LiquiditySweepEvent items. Also updates pools in-place.
    """
    if len(bars) < 3 or not pools:
        return []

    sweeps: List[LiquiditySweepEvent] = []

    for pool in pools:
        # Only inspect bars that closed after the pool was established
        for i in range(len(bars)):
            bar = bars[i]
            if bar.timestamp <= pool.last_touch_at:
                continue

            lvl = pool.price_level

            # 1. Buy-side Sweep (EQH / BSL): High penetrates above level, but Close stays at or below
            if pool.pool_type in (LiquidityType.EQH, LiquidityType.BSL, LiquidityType.PDH, LiquidityType.PWH):
                if bar.high > lvl:
                    if bar.close <= lvl:
                        # Confirmed Rejection Sweep
                        pen_pct = ((bar.high - lvl) / lvl) * 100.0 if lvl > 0 else 0.0

                        event = LiquiditySweepEvent(
                            pool_type=pool.pool_type,
                            price_level=lvl,
                            sweep_bar_index=i,
                            sweep_timestamp=bar.timestamp,
                            penetration_price=round(bar.high, 4),
                            rejection_close=round(bar.close, 4),
                            penetration_pct=round(pen_pct, 2),
                            invalidation_level=round(bar.high, 4),
                            rule_applied=(
                                f"Bullish Liquidity Sweep (Hunt) en {pool.pool_type.value}: Mecha alcanzó {bar.high:.2f} "
                                f"(+{pen_pct:.2f}%), pero el cuerpo cerró por debajo en {bar.close:.2f}. "
                                f"Rechazo bajista institucional confirmado."
                            ),
                        )
                        sweeps.append(event)

                        # Update pool status
                        pool.status = SweepStatus.SWEPT
                        pool.swept_at = bar.timestamp
                        pool.swept_bar_index = i
                        pool.sweep_penetration_pct = round(pen_pct, 2)
                        break
                    else:
                        # Full Expansion breakout (not a sweep rejection)
                        pool.status = SweepStatus.EXPANDED
                        break

            # 2. Sell-side Sweep (EQL / SSL): Low penetrates below level, but Close stays at or above
            elif pool.pool_type in (LiquidityType.EQL, LiquidityType.SSL, LiquidityType.PDL, LiquidityType.PWL):
                if bar.low < lvl:
                    if bar.close >= lvl:
                        # Confirmed Rejection Sweep
                        pen_pct = ((lvl - bar.low) / lvl) * 100.0 if lvl > 0 else 0.0

                        event = LiquiditySweepEvent(
                            pool_type=pool.pool_type,
                            price_level=lvl,
                            sweep_bar_index=i,
                            sweep_timestamp=bar.timestamp,
                            penetration_price=round(bar.low, 4),
                            rejection_close=round(bar.close, 4),
                            penetration_pct=round(pen_pct, 2),
                            invalidation_level=round(bar.low, 4),
                            rule_applied=(
                                f"Bearish Liquidity Sweep (Hunt) en {pool.pool_type.value}: Mecha perforó hasta {bar.low:.2f} "
                                f"(-{pen_pct:.2f}%), pero el cuerpo cerró por encima en {bar.close:.2f}. "
                                f"Rechazo alcista institucional confirmado."
                            ),
                        )
                        sweeps.append(event)

                        # Update pool status
                        pool.status = SweepStatus.SWEPT
                        pool.swept_at = bar.timestamp
                        pool.swept_bar_index = i
                        pool.sweep_penetration_pct = round(pen_pct, 2)
                        break
                    else:
                        pool.status = SweepStatus.EXPANDED
                        break

    return sweeps
