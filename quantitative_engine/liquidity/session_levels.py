"""Session & Benchmark Levels Engine (PDH, PDL, PWH, PWL) — Phase 6 QUANT AI.

Calculates rolling session anchor levels:
  - PDH / PDL: Previous Day High & Low
  - PWH / PWL: Previous Week High & Low
"""

from typing import List, Optional
from datetime import datetime, timedelta

from data_providers.base.models import MarketBar
from quantitative_engine.liquidity.models import SessionLevels


def compute_session_levels(bars: List[MarketBar]) -> SessionLevels:
    """Computes PDH, PDL, PWH, and PWL based on chronological bars."""
    if len(bars) < 2:
        return SessionLevels()

    last_bar = bars[-1]
    last_date = last_bar.timestamp.date()

    # 1. Previous Day Bars
    # Group bars by date and find the most recent completed day prior to last_date
    days_data = {}
    for b in bars:
        d = b.timestamp.date()
        if d not in days_data:
            days_data[d] = {"high": b.high, "low": b.low}
        else:
            days_data[d]["high"] = max(days_data[d]["high"], b.high)
            days_data[d]["low"] = min(days_data[d]["low"], b.low)

    sorted_dates = sorted(days_data.keys())

    pdh: Optional[float] = None
    pdl: Optional[float] = None

    if len(sorted_dates) >= 2:
        # If last bar date has data, previous day is the date before it
        prev_date = sorted_dates[-2]
        pdh = round(days_data[prev_date]["high"], 4)
        pdl = round(days_data[prev_date]["low"], 4)
    elif len(sorted_dates) == 1 and len(bars) >= 10:
        # Single day intraday: split first half as previous reference
        mid = len(bars) // 2
        pdh = round(max(b.high for b in bars[:mid]), 4)
        pdl = round(min(b.low for b in bars[:mid]), 4)

    # 2. Previous Week Bars
    # Group by calendar week (isocalendar)
    weeks_data = {}
    for b in bars:
        iso_year, iso_week, _ = b.timestamp.isocalendar()
        key = (iso_year, iso_week)
        if key not in weeks_data:
            weeks_data[key] = {"high": b.high, "low": b.low}
        else:
            weeks_data[key]["high"] = max(weeks_data[key]["high"], b.high)
            weeks_data[key]["low"] = min(weeks_data[key]["low"], b.low)

    sorted_weeks = sorted(weeks_data.keys())

    pwh: Optional[float] = None
    pwl: Optional[float] = None

    if len(sorted_weeks) >= 2:
        prev_week = sorted_weeks[-2]
        pwh = round(weeks_data[prev_week]["high"], 4)
        pwl = round(weeks_data[prev_week]["low"], 4)
    elif len(bars) >= 20:
        # Fallback to 5-day lookback window prior to current week
        pwh = round(max(b.high for b in bars[-20:-5]), 4)
        pwl = round(min(b.low for b in bars[-20:-5]), 4)

    return SessionLevels(
        pdh=pdh,
        pdl=pdl,
        pwh=pwh,
        pwl=pwl,
    )
