"""Premium vs. Discount Dealing Range Engine — Phase 5 QUANT AI.

Calculates the active dealing range, Equilibrium (50%), and classifies current price
into Premium (institutional sell zone) or Discount (institutional buy zone).
"""

from typing import List, Optional

from data_providers.base.models import MarketBar
from quantitative_engine.market_structure.models import StructurePivot
from quantitative_engine.smc.models import PremiumDiscountRange


def compute_premium_discount(
    bars: List[MarketBar],
    pivots: Optional[List[StructurePivot]] = None,
) -> Optional[PremiumDiscountRange]:
    """Calculates the dealing range and Equilibrium level based on confirmed swings.

    Args:
        bars: Chronological list of MarketBar objects.
        pivots: Confirmed swing pivots from market structure engine.

    Returns:
        PremiumDiscountRange or None if insufficient swings.
    """
    if len(bars) < 5:
        return None

    current_price = bars[-1].close

    # Identify the most recent confirmed swing high and swing low
    high_candidates = [p for p in (pivots or []) if p.is_high]
    low_candidates = [p for p in (pivots or []) if not p.is_high]

    if high_candidates and low_candidates:
        swing_high = high_candidates[-1].price
        swing_low = low_candidates[-1].price
    else:
        # Fallback: calculate over the recent lookback window of bars
        lookback = min(len(bars), 50)
        recent_bars = bars[-lookback:]
        swing_high = max(b.high for b in recent_bars)
        swing_low = min(b.low for b in recent_bars)

    if swing_high <= swing_low:
        return None

    equilibrium = (swing_high + swing_low) / 2.0
    range_span = swing_high - swing_low
    position_pct = max(0.0, min(100.0, ((current_price - swing_low) / range_span) * 100.0))

    if position_pct > 55.0:
        zone = "PREMIUM"
        obs = (
            f"Precio en zona PREMIUM ({position_pct:.1f}% del rango [{swing_low:.2f} - {swing_high:.2f}]). "
            f"Favorece búsqueda de ofertas institucionales (Shorts / Mitigación de Supply)."
        )
    elif position_pct < 45.0:
        zone = "DISCOUNT"
        obs = (
            f"Precio en zona DISCOUNT ({position_pct:.1f}% del rango [{swing_low:.2f} - {swing_high:.2f}]). "
            f"Favorece búsqueda de demandas institucionales (Longs / Mitigación de Demand)."
        )
    else:
        zone = "EQUILIBRIUM"
        obs = (
            f"Precio en zona de EQUILIBRIUM ({position_pct:.1f}% del rango, 50% = {equilibrium:.2f}). "
            f"Mercado en equilibrio; baja probabilidad para nuevas posiciones de swing."
        )

    return PremiumDiscountRange(
        swing_high=round(swing_high, 4),
        swing_low=round(swing_low, 4),
        equilibrium=round(equilibrium, 4),
        current_price=round(current_price, 4),
        current_position_pct=round(position_pct, 1),
        zone=zone,
        observation=obs,
    )
