"""Fair Value Gap (FVG) / Liquidity Imbalance Detection Engine.

Implements institutional 3-candle imbalance detection with:
  - Bullish FVG: bar[i-2].high < bar[i].low
  - Bearish FVG: bar[i-2].low > bar[i].high
  - Consequent Encroachment (CE 50% equilibrium of the gap)
  - Dynamic mitigation tracking across all subsequent bars
"""

from typing import List, Optional
from datetime import datetime

from data_providers.base.models import MarketBar
from quantitative_engine.smc.models import FairValueGap, SMCDirection, MitigationStatus


def detect_fair_value_gaps(
    bars: List[MarketBar],
    min_gap_pct: float = 0.001,  # Minimum 0.1% price gap to avoid micro-noise
) -> List[FairValueGap]:
    """Scans price series for institutional Fair Value Gaps and tracks their mitigation.

    Args:
        bars: Chronological list of MarketBar objects.
        min_gap_pct: Minimum relative size (gap / price) to qualify as a significant FVG.

    Returns:
        List of FairValueGap objects with updated mitigation status.
    """
    n = len(bars)
    if n < 3:
        return []

    fvgs: List[FairValueGap] = []

    # 1. Identify 3-candle imbalances
    for i in range(2, n):
        b_prev2 = bars[i - 2]
        b_mid = bars[i - 1]
        b_curr = bars[i]

        mid_price = b_mid.close if b_mid.close > 0 else 1.0

        # Bullish FVG: Gap between b_prev2.high and b_curr.low
        # Middle candle must be strongly bullish (close > open)
        if b_curr.low > b_prev2.high and b_mid.close > b_mid.open:
            gap_size = b_curr.low - b_prev2.high
            if gap_size / mid_price >= min_gap_pct:
                top = b_curr.low
                bottom = b_prev2.high
                ce = (top + bottom) / 2.0

                fvg = FairValueGap(
                    direction=SMCDirection.BULLISH,
                    bar_index=i - 1,
                    timestamp=b_mid.timestamp,
                    top_price=round(top, 4),
                    bottom_price=round(bottom, 4),
                    gap_size=round(gap_size, 4),
                    consequent_encroachment=round(ce, 4),
                    status=MitigationStatus.UNMITIGATED,
                    mitigated_pct=0.0,
                    mitigated_at=None,
                    rule_applied=(
                        f"Bullish FVG: Mínimo de barra {i} ({top:.2f}) > Máximo de barra {i-2} ({bottom:.2f}). "
                        f"CE (50%): {ce:.2f}."
                    ),
                )
                fvgs.append(fvg)

        # Bearish FVG: Gap between b_curr.high and b_prev2.low
        # Middle candle must be strongly bearish (close < open)
        elif b_prev2.low > b_curr.high and b_mid.close < b_mid.open:
            gap_size = b_prev2.low - b_curr.high
            if gap_size / mid_price >= min_gap_pct:
                top = b_prev2.low
                bottom = b_curr.high
                ce = (top + bottom) / 2.0

                fvg = FairValueGap(
                    direction=SMCDirection.BEARISH,
                    bar_index=i - 1,
                    timestamp=b_mid.timestamp,
                    top_price=round(top, 4),
                    bottom_price=round(bottom, 4),
                    gap_size=round(gap_size, 4),
                    consequent_encroachment=round(ce, 4),
                    status=MitigationStatus.UNMITIGATED,
                    mitigated_pct=0.0,
                    mitigated_at=None,
                    rule_applied=(
                        f"Bearish FVG: Mínimo de barra {i-2} ({top:.2f}) > Máximo de barra {i} ({bottom:.2f}). "
                        f"CE (50%): {ce:.2f}."
                    ),
                )
                fvgs.append(fvg)

    # 2. Track subsequent mitigation for each identified FVG
    for fvg in fvgs:
        creation_idx = fvg.bar_index + 1  # The gap is established when bar i closes
        max_fill_pct = 0.0

        for j in range(creation_idx + 1, n):
            chk_bar = bars[j]

            if fvg.direction == SMCDirection.BULLISH:
                # In a bullish FVG, price pulls back DOWN into the gap
                if chk_bar.low < fvg.top_price:
                    # Calculate how deeply it probed into [bottom_price, top_price]
                    depth = fvg.top_price - chk_bar.low
                    fill_pct = min(100.0, max(0.0, (depth / fvg.gap_size) * 100.0))
                    if fill_pct > max_fill_pct:
                        max_fill_pct = fill_pct

                    if chk_bar.low <= fvg.bottom_price:
                        # 100% completely filled
                        fvg.status = MitigationStatus.MITIGATED
                        fvg.mitigated_pct = 100.0
                        fvg.mitigated_at = chk_bar.timestamp
                        break
                    elif chk_bar.low <= fvg.consequent_encroachment:
                        # Tested past CE (50%)
                        fvg.status = MitigationStatus.PARTIAL
                        fvg.mitigated_at = chk_bar.timestamp
                    elif chk_bar.low < fvg.top_price:
                        # Probed into the gap
                        if fvg.status == MitigationStatus.UNMITIGATED:
                            fvg.status = MitigationStatus.PARTIAL

            else:  # Bearish FVG
                # In a bearish FVG, price pulls back UP into the gap
                if chk_bar.high > fvg.bottom_price:
                    depth = chk_bar.high - fvg.bottom_price
                    fill_pct = min(100.0, max(0.0, (depth / fvg.gap_size) * 100.0))
                    if fill_pct > max_fill_pct:
                        max_fill_pct = fill_pct

                    if chk_bar.high >= fvg.top_price:
                        # 100% completely filled
                        fvg.status = MitigationStatus.MITIGATED
                        fvg.mitigated_pct = 100.0
                        fvg.mitigated_at = chk_bar.timestamp
                        break
                    elif chk_bar.high >= fvg.consequent_encroachment:
                        # Tested past CE (50%)
                        fvg.status = MitigationStatus.PARTIAL
                        fvg.mitigated_at = chk_bar.timestamp
                    elif chk_bar.high > fvg.bottom_price:
                        if fvg.status == MitigationStatus.UNMITIGATED:
                            fvg.status = MitigationStatus.PARTIAL

        if fvg.status != MitigationStatus.MITIGATED:
            fvg.mitigated_pct = round(max_fill_pct, 1)

    return fvgs
