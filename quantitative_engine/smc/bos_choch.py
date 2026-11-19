"""Break of Structure (BOS) and Change of Character (CHOCH) Engine.

Strictly causal:
  - Swing pivots at index `p` with window `k` are only visible/confirmed at bar index `p + k`.
  - A break is only registered when a candle close strictly penetrates the confirmed pivot level.
  - Differentiates continuation (BOS) from structural reversal (CHOCH).
"""

from typing import List, Optional
from datetime import datetime

from data_providers.base.models import MarketBar
from quantitative_engine.market_structure.models import StructurePivot, StructureType, TrendDirection
from quantitative_engine.smc.models import StructureBreak, SMCZoneType, SMCDirection


def detect_structure_breaks(
    bars: List[MarketBar],
    pivots: List[StructurePivot],
    k: int = 3,
) -> List[StructureBreak]:
    """Detects causal BOS and CHOCH occurrences across the bar series.

    Args:
        bars: Chronological list of MarketBar items.
        pivots: Confirmed swing pivots from detect_market_structure.
        k: Fractal confirmation window size.

    Returns:
        List of StructureBreak items chronologically ordered.
    """
    if len(bars) < 2 * k + 1 or not pivots:
        return []

    breaks: List[StructureBreak] = []

    # Map each pivot to its confirmation bar index:
    # A pivot at bar p is confirmed at p + k.
    # We sort pivots by confirmation index.
    confirmed_pivots = []
    for p in pivots:
        conf_idx = p.bar_index + k
        if conf_idx < len(bars):
            confirmed_pivots.append((conf_idx, p))
    confirmed_pivots.sort(key=lambda x: x[0])

    if not confirmed_pivots:
        return []

    # State tracking
    current_high_pivot: Optional[StructurePivot] = None
    current_low_pivot: Optional[StructurePivot] = None
    prevailing_trend: SMCDirection = SMCDirection.NEUTRAL
    pivot_ptr = 0

    # Track broken price levels so we don't trigger multiple breaks on the same level
    broken_levels = set()

    for i in range(len(bars)):
        current_time = bars[i].timestamp
        bar = bars[i]

        # Ingest any pivots confirmed up to index i
        while pivot_ptr < len(confirmed_pivots) and confirmed_pivots[pivot_ptr][0] <= i:
            _, p = confirmed_pivots[pivot_ptr]
            if p.is_high:
                current_high_pivot = p
            else:
                current_low_pivot = p
            pivot_ptr += 1

        # Check for Bullish Break (price breaks above current confirmed Swing High)
        if current_high_pivot is not None:
            high_level = current_high_pivot.price
            pivot_key = ("HIGH", current_high_pivot.bar_index)

            # Check if this high was not yet broken and current bar closes above it
            if pivot_key not in broken_levels and bar.close > high_level:
                # If we were BEARISH or NEUTRAL, this is a Change of Character (CHOCH)
                if prevailing_trend == SMCDirection.BEARISH or prevailing_trend == SMCDirection.NEUTRAL:
                    b_type = SMCZoneType.CHOCH
                    rule = (
                        f"Bullish CHOCH: Cierre ({bar.close:.2f}) supera Swing High confirmado ({high_level:.2f}). "
                        f"Primer cambio de carácter de bajista a alcista."
                    )
                else:
                    b_type = SMCZoneType.BOS
                    rule = (
                        f"Bullish BOS: Cierre ({bar.close:.2f}) supera Swing High confirmado ({high_level:.2f}). "
                        f"Continuación de tendencia alcista."
                    )

                invalidation = current_low_pivot.price if current_low_pivot else bar.low

                breaks.append(
                    StructureBreak(
                        break_type=b_type,
                        direction=SMCDirection.BULLISH,
                        broken_pivot_price=high_level,
                        breaking_bar_index=i,
                        breaking_bar_timestamp=bar.timestamp,
                        breaking_price=bar.close,
                        invalidation_level=invalidation,
                        rule_applied=rule,
                    )
                )
                prevailing_trend = SMCDirection.BULLISH
                broken_levels.add(pivot_key)

        # Check for Bearish Break (price breaks below current confirmed Swing Low)
        if current_low_pivot is not None:
            low_level = current_low_pivot.price
            pivot_key = ("LOW", current_low_pivot.bar_index)

            # Check if this low was not yet broken and current bar closes below it
            if pivot_key not in broken_levels and bar.close < low_level:
                # If we were BULLISH or NEUTRAL, this is a Change of Character (CHOCH)
                if prevailing_trend == SMCDirection.BULLISH or prevailing_trend == SMCDirection.NEUTRAL:
                    b_type = SMCZoneType.CHOCH
                    rule = (
                        f"Bearish CHOCH: Cierre ({bar.close:.2f}) perfora Swing Low confirmado ({low_level:.2f}). "
                        f"Primer cambio de carácter de alcista a bajista."
                    )
                else:
                    b_type = SMCZoneType.BOS
                    rule = (
                        f"Bearish BOS: Cierre ({bar.close:.2f}) perfora Swing Low confirmado ({low_level:.2f}). "
                        f"Continuación de tendencia bajista."
                    )

                invalidation = current_high_pivot.price if current_high_pivot else bar.high

                breaks.append(
                    StructureBreak(
                        break_type=b_type,
                        direction=SMCDirection.BEARISH,
                        broken_pivot_price=low_level,
                        breaking_bar_index=i,
                        breaking_bar_timestamp=bar.timestamp,
                        breaking_price=bar.close,
                        invalidation_level=invalidation,
                        rule_applied=rule,
                    )
                )
                prevailing_trend = SMCDirection.BEARISH
                broken_levels.add(pivot_key)

    return breaks
