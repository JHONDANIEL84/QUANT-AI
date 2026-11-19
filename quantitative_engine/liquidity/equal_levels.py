"""Equal Highs (EQH) & Equal Lows (EQL) Detection Engine — Phase 6 QUANT AI.

Identifies resting institutional liquidity clusters where multiple highs or lows align within
a dynamic volatility tolerance (ATR-based).
"""

from typing import List, Tuple
from datetime import datetime
import numpy as np

from data_providers.base.models import MarketBar
from quantitative_engine.market_structure.models import StructurePivot
from quantitative_engine.liquidity.models import LiquidityPool, LiquidityType, SweepStatus


def detect_equal_levels_and_pools(
    bars: List[MarketBar],
    pivots: List[StructurePivot],
    atr_val: float = 1.0,
    tolerance_pct: float = 0.002,  # 0.20% tolerance
) -> List[LiquidityPool]:
    """Clusters swing pivots into Equal Highs (EQH), Equal Lows (EQL), BSL, and SSL pools.

    Args:
        bars: Chronological list of MarketBars.
        pivots: Confirmed structural pivots.
        atr_val: Current Average True Range for dynamic zone padding.
        tolerance_pct: Maximum relative price difference between equal extrema.

    Returns:
        List of LiquidityPool items.
    """
    if len(pivots) < 2:
        return []

    pools: List[LiquidityPool] = []

    # Separate swing highs and swing lows
    high_pivots = [p for p in pivots if p.is_high]
    low_pivots = [p for p in pivots if not p.is_high]

    # 1. Cluster Swing Highs into EQH or standalone BSL
    used_highs = set()
    for i in range(len(high_pivots)):
        if i in used_highs:
            continue

        p1 = high_pivots[i]
        cluster = [p1]
        used_highs.add(i)

        tol = max(p1.price * tolerance_pct, atr_val * 0.3)

        for j in range(i + 1, len(high_pivots)):
            if j in used_highs:
                continue
            p2 = high_pivots[j]
            if abs(p1.price - p2.price) <= tol:
                cluster.append(p2)
                used_highs.add(j)

        prices = [p.price for p in cluster]
        max_p = max(prices)
        min_p = min(prices)
        touch_count = len(cluster)
        first_t = min(p.timestamp for p in cluster)
        last_t = max(p.timestamp for p in cluster)

        if touch_count >= 2:
            # Equal Highs (EQH)
            score = min(100.0, 50.0 + (touch_count - 1) * 20.0)
            pool = LiquidityPool(
                pool_type=LiquidityType.EQH,
                price_level=round(max_p, 4),
                top_price=round(max_p + tol * 0.25, 4),
                bottom_price=round(min_p - tol * 0.25, 4),
                touch_count=touch_count,
                first_touch_at=first_t,
                last_touch_at=last_t,
                liquidity_score=score,
                status=SweepStatus.ACTIVE,
                rule_applied=(
                    f"Equal Highs (EQH): {touch_count} máximos alineados en torno a {max_p:.2f} "
                    f"(Tolerancia: ±{tol:.2f}). Acumulación de Buy-side Liquidity."
                ),
            )
            pools.append(pool)
        else:
            # Standalone Buy-side Liquidity (BSL)
            pool = LiquidityPool(
                pool_type=LiquidityType.BSL,
                price_level=round(p1.price, 4),
                top_price=round(p1.price + tol * 0.25, 4),
                bottom_price=round(p1.price - tol * 0.25, 4),
                touch_count=1,
                first_touch_at=p1.timestamp,
                last_touch_at=p1.timestamp,
                liquidity_score=40.0,
                status=SweepStatus.ACTIVE,
                rule_applied=f"Buy-side Liquidity (BSL): Swing High aislado en {p1.price:.2f}.",
            )
            pools.append(pool)

    # 2. Cluster Swing Lows into EQL or standalone SSL
    used_lows = set()
    for i in range(len(low_pivots)):
        if i in used_lows:
            continue

        p1 = low_pivots[i]
        cluster = [p1]
        used_lows.add(i)

        tol = max(p1.price * tolerance_pct, atr_val * 0.3)

        for j in range(i + 1, len(low_pivots)):
            if j in used_lows:
                continue
            p2 = low_pivots[j]
            if abs(p1.price - p2.price) <= tol:
                cluster.append(p2)
                used_lows.add(j)

        prices = [p.price for p in cluster]
        max_p = max(prices)
        min_p = min(prices)
        touch_count = len(cluster)
        first_t = min(p.timestamp for p in cluster)
        last_t = max(p.timestamp for p in cluster)

        if touch_count >= 2:
            # Equal Lows (EQL)
            score = min(100.0, 50.0 + (touch_count - 1) * 20.0)
            pool = LiquidityPool(
                pool_type=LiquidityType.EQL,
                price_level=round(min_p, 4),
                top_price=round(max_p + tol * 0.25, 4),
                bottom_price=round(min_p - tol * 0.25, 4),
                touch_count=touch_count,
                first_touch_at=first_t,
                last_touch_at=last_t,
                liquidity_score=score,
                status=SweepStatus.ACTIVE,
                rule_applied=(
                    f"Equal Lows (EQL): {touch_count} mínimos alineados en torno a {min_p:.2f} "
                    f"(Tolerancia: ±{tol:.2f}). Acumulación de Sell-side Liquidity."
                ),
            )
            pools.append(pool)
        else:
            # Standalone Sell-side Liquidity (SSL)
            pool = LiquidityPool(
                pool_type=LiquidityType.SSL,
                price_level=round(p1.price, 4),
                top_price=round(p1.price + tol * 0.25, 4),
                bottom_price=round(p1.price - tol * 0.25, 4),
                touch_count=1,
                first_touch_at=p1.timestamp,
                last_touch_at=p1.timestamp,
                liquidity_score=40.0,
                status=SweepStatus.ACTIVE,
                rule_applied=f"Sell-side Liquidity (SSL): Swing Low aislado en {p1.price:.2f}.",
            )
            pools.append(pool)

    return pools
