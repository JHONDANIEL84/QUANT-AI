"""Market Structure and Swing Pivot Analysis Engine.
Identifies fractal Swing Highs, Swing Lows, HH, HL, LH, LL, and overall market trend.
Strict look-ahead bias prevention: Pivots at index i are strictly marked as confirmed at index i + k.
"""

from typing import List, Optional
from datetime import datetime

from data_providers.base.models import MarketBar
from quantitative_engine.market_structure.models import (
    StructurePivot,
    StructureType,
    TrendDirection,
    ConsolidationRange,
    MarketStructureResult,
)


def detect_market_structure(
    bars: List[MarketBar],
    k: int = 3,
) -> MarketStructureResult:
    """Scans price series for confirmed Swing Highs and Swing Lows.

    Args:
        bars: Chronological list of MarketBars.
        k: Window size for fractal swing detection (k bars before and k bars after).

    Returns:
        MarketStructureResult: Trend, confirmed pivots, and structure summary.
    """
    n = len(bars)
    if n < 2 * k + 1:
        return MarketStructureResult(
            trend=TrendDirection.CONSOLIDATION,
            pivots=[],
            summary="Datos insuficientes para determinar estructura de mercado (mínimo 2k + 1 barras requeridas).",
        )

    pivots: List[StructurePivot] = []
    prev_high_price: Optional[float] = None
    prev_low_price: Optional[float] = None

    # Scan bars from index k to n - 1 - k (only bars that have k closed bars to the right can be confirmed)
    for i in range(k, n - k):
        curr_bar = bars[i]
        curr_h = curr_bar.high
        curr_l = curr_bar.low

        # Confirmation timestamp is strictly the bar index i + k close
        confirmed_time = bars[i + k].timestamp

        # Check for Swing High
        is_swing_high = True
        for j in range(1, k + 1):
            if bars[i - j].high >= curr_h or bars[i + j].high >= curr_h:
                is_swing_high = False
                break

        if is_swing_high:
            if prev_high_price is None:
                st = StructureType.SWING_HIGH
                rule = "Primer Swing High identificado."
            elif curr_h > prev_high_price:
                st = StructureType.HH
                rule = f"Higher High (HH): Máximo actual ({curr_h:.2f}) > Máximo previo ({prev_high_price:.2f})."
            else:
                st = StructureType.LH
                rule = f"Lower High (LH): Máximo actual ({curr_h:.2f}) < Máximo previo ({prev_high_price:.2f})."

            prev_high_price = curr_h
            pivots.append(
                StructurePivot(
                    bar_index=i,
                    timestamp=curr_bar.timestamp,
                    confirmed_at=confirmed_time,
                    price=curr_h,
                    is_high=True,
                    structure_type=st,
                    rule_applied=rule,
                )
            )

        # Check for Swing Low
        is_swing_low = True
        for j in range(1, k + 1):
            if bars[i - j].low <= curr_l or bars[i + j].low <= curr_l:
                is_swing_low = False
                break

        if is_swing_low:
            if prev_low_price is None:
                st = StructureType.SWING_LOW
                rule = "Primer Swing Low identificado."
            elif curr_l > prev_low_price:
                st = StructureType.HL
                rule = f"Higher Low (HL): Mínimo actual ({curr_l:.2f}) > Mínimo previo ({prev_low_price:.2f})."
            else:
                st = StructureType.LL
                rule = f"Lower Low (LL): Mínimo actual ({curr_l:.2f}) < Mínimo previo ({prev_low_price:.2f})."

            prev_low_price = curr_l
            pivots.append(
                StructurePivot(
                    bar_index=i,
                    timestamp=curr_bar.timestamp,
                    confirmed_at=confirmed_time,
                    price=curr_l,
                    is_high=False,
                    structure_type=st,
                    rule_applied=rule,
                )
            )

    # Sort all pivots chronologically by bar index
    pivots.sort(key=lambda p: p.bar_index)

    # Determine trend from the last 4 confirmed pivots
    trend = TrendDirection.CONSOLIDATION
    summary = "Mercado en fase de consolidación o transición estructural."

    recent_pivots = pivots[-4:] if len(pivots) >= 4 else pivots
    highs = [p for p in recent_pivots if p.is_high]
    lows = [p for p in recent_pivots if not p.is_high]

    has_hh = any(p.structure_type == StructureType.HH for p in highs)
    has_hl = any(p.structure_type == StructureType.HL for p in lows)
    has_lh = any(p.structure_type == StructureType.LH for p in highs)
    has_ll = any(p.structure_type == StructureType.LL for p in lows)

    if has_hh and has_hl and not has_ll:
        trend = TrendDirection.UPTREND
        summary = "Estructura alcista confirmada por secuencia de Higher Highs (HH) y Higher Lows (HL)."
    elif has_lh and has_ll and not has_hh:
        trend = TrendDirection.DOWNTREND
        summary = "Estructura bajista confirmada por secuencia de Lower Highs (LH) y Lower Lows (LL)."
    else:
        trend = TrendDirection.CONSOLIDATION
        summary = "Estructura en rango lateral / consolidación sin tendencia direccional dominante."

    last_high = highs[-1].price if highs else None
    last_low = lows[-1].price if lows else None

    # Calculate consolidation metrics if ranging
    consolidation: Optional[ConsolidationRange] = None
    if trend == TrendDirection.CONSOLIDATION and last_high and last_low:
        consolidation = ConsolidationRange(
            top=last_high,
            bottom=last_low,
            mean=(last_high + last_low) / 2.0,
            duration_bars=min(30, n),
        )

    return MarketStructureResult(
        trend=trend,
        last_swing_high=last_high,
        last_swing_low=last_low,
        pivots=pivots,
        consolidation=consolidation,
        summary=summary,
    )
