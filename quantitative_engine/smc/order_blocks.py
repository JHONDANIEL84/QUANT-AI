"""Order Block (OB) and Breaker Block Engine — Phase 5 QUANT AI.

Implements institutional Order Block identification with:
  - Bullish OB: Last down candle prior to an impulsive expansion that broke structure or formed an FVG.
  - Bearish OB: Last up candle prior to an impulsive drop that broke structure or formed an FVG.
  - Objective Quality Scoring (0 - 100).
  - Mitigation lifecycle tracking (Unmitigated -> Mitigated -> Breaker Block).
"""

from typing import List, Optional
from datetime import datetime
import numpy as np

from data_providers.base.models import MarketBar
from quantitative_engine.smc.models import OrderBlock, SMCDirection, MitigationStatus, StructureBreak, FairValueGap


def detect_order_blocks(
    bars: List[MarketBar],
    breaks: Optional[List[StructureBreak]] = None,
    fvgs: Optional[List[FairValueGap]] = None,
    max_scan_bars: int = 5,
) -> List[OrderBlock]:
    """Identifies institutional Order Blocks and tracks their mitigation status.

    Args:
        bars: Chronological list of MarketBar items.
        breaks: Optional pre-computed StructureBreak items.
        fvgs: Optional pre-computed FairValueGap items.
        max_scan_bars: Window of bars to search backwards for the origin candle.

    Returns:
        List of OrderBlock objects sorted chronologically.
    """
    n = len(bars)
    if n < 4:
        return []

    order_blocks: List[OrderBlock] = []

    # Pre-calculate rolling average volume and ATR for quality scoring
    vols = np.array([b.volume for b in bars], dtype=float)
    avg_vol = np.mean(vols) if len(vols) > 0 and np.mean(vols) > 0 else 1.0

    highs = np.array([b.high for b in bars], dtype=float)
    lows = np.array([b.low for b in bars], dtype=float)
    closes = np.array([b.close for b in bars], dtype=float)

    # Simplified True Range calculation
    tr = np.maximum(highs[1:] - lows[1:], np.abs(highs[1:] - closes[:-1]))
    avg_tr = np.mean(tr) if len(tr) > 0 and np.mean(tr) > 0 else 1.0

    # Collect break indices and FVG bar indices for correlation
    break_indices = {b.breaking_bar_index: b for b in (breaks or [])}
    fvg_indices = {f.bar_index: f for f in (fvgs or [])}

    # Scan for impulsive displacements
    for i in range(2, n):
        curr_bar = bars[i]
        prev_bar = bars[i - 1]

        # 1. Bullish Displacement Check
        # Candle is strong green with displacement >= 1.2 * avg_tr or has FVG/BOS
        is_bullish_impulse = (
            curr_bar.close > curr_bar.open
            and (curr_bar.close - curr_bar.open) >= 0.8 * avg_tr
        ) or (i in break_indices and break_indices[i].direction == SMCDirection.BULLISH) \
          or (i in fvg_indices and fvg_indices[i].direction == SMCDirection.BULLISH)

        if is_bullish_impulse:
            # Look back for the last down (bearish) candle that initiated this move
            ob_idx = None
            for lookback in range(1, min(i, max_scan_bars + 1)):
                candidate = bars[i - lookback]
                if candidate.close <= candidate.open:
                    ob_idx = i - lookback
                    break

            if ob_idx is not None and not any(ob.bar_index == ob_idx and ob.direction == SMCDirection.BULLISH for ob in order_blocks):
                ob_bar = bars[ob_idx]

                # Compute quality score
                score = 30.0  # Base score for valid impulse
                if any(b.breaking_bar_index >= ob_idx and b.breaking_bar_index <= i for b in (breaks or [])):
                    score += 30.0  # Caused structural break
                if any(f.bar_index >= ob_idx and f.bar_index <= i for f in (fvgs or [])):
                    score += 20.0  # Accompanied by FVG
                if ob_bar.volume > 1.2 * avg_vol or curr_bar.volume > 1.2 * avg_vol:
                    score += 20.0  # High institutional volume

                ob = OrderBlock(
                    direction=SMCDirection.BULLISH,
                    bar_index=ob_idx,
                    timestamp=ob_bar.timestamp,
                    top_price=round(ob_bar.high, 4),
                    bottom_price=round(ob_bar.low, 4),
                    body_top=round(max(ob_bar.open, ob_bar.close), 4),
                    body_bottom=round(min(ob_bar.open, ob_bar.close), 4),
                    status=MitigationStatus.UNMITIGATED,
                    mitigated_at=None,
                    mitigated_bar_index=None,
                    is_breaker=False,
                    quality_score=round(min(100.0, score), 1),
                    volume=round(ob_bar.volume, 2),
                    rule_applied=(
                        f"Bullish Order Block: Última vela bajista en barra {ob_idx} previa al impulso alcista. "
                        f"Rango [{ob_bar.low:.2f} - {ob_bar.high:.2f}]."
                    ),
                )
                order_blocks.append(ob)

        # 2. Bearish Displacement Check
        # Candle is strong red with displacement >= 1.2 * avg_tr or has FVG/BOS
        is_bearish_impulse = (
            curr_bar.close < curr_bar.open
            and (curr_bar.open - curr_bar.close) >= 0.8 * avg_tr
        ) or (i in break_indices and break_indices[i].direction == SMCDirection.BEARISH) \
          or (i in fvg_indices and fvg_indices[i].direction == SMCDirection.BEARISH)

        if is_bearish_impulse:
            # Look back for the last up (bullish) candle that initiated this drop
            ob_idx = None
            for lookback in range(1, min(i, max_scan_bars + 1)):
                candidate = bars[i - lookback]
                if candidate.close >= candidate.open:
                    ob_idx = i - lookback
                    break

            if ob_idx is not None and not any(ob.bar_index == ob_idx and ob.direction == SMCDirection.BEARISH for ob in order_blocks):
                ob_bar = bars[ob_idx]

                score = 30.0
                if any(b.breaking_bar_index >= ob_idx and b.breaking_bar_index <= i for b in (breaks or [])):
                    score += 30.0
                if any(f.bar_index >= ob_idx and f.bar_index <= i for f in (fvgs or [])):
                    score += 20.0
                if ob_bar.volume > 1.2 * avg_vol or curr_bar.volume > 1.2 * avg_vol:
                    score += 20.0

                ob = OrderBlock(
                    direction=SMCDirection.BEARISH,
                    bar_index=ob_idx,
                    timestamp=ob_bar.timestamp,
                    top_price=round(ob_bar.high, 4),
                    bottom_price=round(ob_bar.low, 4),
                    body_top=round(max(ob_bar.open, ob_bar.close), 4),
                    body_bottom=round(min(ob_bar.open, ob_bar.close), 4),
                    status=MitigationStatus.UNMITIGATED,
                    mitigated_at=None,
                    mitigated_bar_index=None,
                    is_breaker=False,
                    quality_score=round(min(100.0, score), 1),
                    volume=round(ob_bar.volume, 2),
                    rule_applied=(
                        f"Bearish Order Block: Última vela alcista en barra {ob_idx} previa al impulso bajista. "
                        f"Rango [{ob_bar.low:.2f} - {ob_bar.high:.2f}]."
                    ),
                )
                order_blocks.append(ob)

    # 3. Track mitigation and Breaker status across all subsequent bars
    for ob in order_blocks:
        for j in range(ob.bar_index + 2, n):
            chk_bar = bars[j]

            if ob.direction == SMCDirection.BULLISH:
                # Price drops into Bullish OB range [bottom_price, top_price]
                if chk_bar.close < ob.bottom_price:
                    # Broken through completely -> Invalidated and flipped into a Bearish Breaker
                    ob.status = MitigationStatus.INVALIDATED
                    ob.is_breaker = True
                    ob.mitigated_at = chk_bar.timestamp
                    ob.mitigated_bar_index = j
                    ob.rule_applied += f" Perforado a la baja en barra {j} -> Convertido en Bearish Breaker Block."
                    break
                elif chk_bar.low <= ob.top_price:
                    # Touched or entered the block -> Mitigated
                    if ob.status == MitigationStatus.UNMITIGATED:
                        ob.status = MitigationStatus.MITIGATED
                        ob.mitigated_at = chk_bar.timestamp
                        ob.mitigated_bar_index = j

            else:  # Bearish OB
                # Price rises into Bearish OB range [bottom_price, top_price]
                if chk_bar.close > ob.top_price:
                    # Broken through completely -> Invalidated and flipped into a Bullish Breaker
                    ob.status = MitigationStatus.INVALIDATED
                    ob.is_breaker = True
                    ob.mitigated_at = chk_bar.timestamp
                    ob.mitigated_bar_index = j
                    ob.rule_applied += f" Perforado al alza en barra {j} -> Convertido en Bullish Breaker Block."
                    break
                elif chk_bar.high >= ob.bottom_price:
                    # Touched or entered the block -> Mitigated
                    if ob.status == MitigationStatus.UNMITIGATED:
                        ob.status = MitigationStatus.MITIGATED
                        ob.mitigated_at = chk_bar.timestamp
                        ob.mitigated_bar_index = j

    return order_blocks
