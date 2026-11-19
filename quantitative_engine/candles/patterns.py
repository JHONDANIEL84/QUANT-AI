"""Japanese Candlestick Pattern Detection Engine.
Follows Section 9 of QUANT AI specification.
Strict causal execution: patterns are verified only upon bar close without future information.
"""

from typing import List, Optional
import numpy as np
from datetime import datetime

from data_providers.base.models import MarketBar
from quantitative_engine.candles.models import (
    CandlePattern,
    CandlePatternType,
    CandlePatternDirection,
)


def detect_candle_patterns(bars: List[MarketBar]) -> List[CandlePattern]:
    """Scans historical OHLCV bars and identifies confirmed candlestick patterns.

    Args:
        bars: Chronologically sorted list of closed MarketBar objects.

    Returns:
        List[CandlePattern]: Chronologically ordered detected patterns with mathematical rules.
    """
    patterns: List[CandlePattern] = []
    n = len(bars)
    if n < 2:
        return patterns

    for i in range(1, n):
        curr = bars[i]
        prev = bars[i - 1]

        o = curr.open
        h = curr.high
        l = curr.low
        c = curr.close
        rng = h - l
        if rng <= 0:
            continue

        body = abs(c - o)
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        is_bullish = c > o
        is_bearish = c < o

        po = prev.open
        ph = prev.high
        pl = prev.low
        pc = prev.close
        prev_body = abs(pc - po)
        prev_is_bullish = pc > po
        prev_is_bearish = pc < po

        # -------------------------------------------------------------
        # 1. DOJI (|Close - Open| <= 10% of total range)
        # -------------------------------------------------------------
        if body <= 0.10 * rng:
            patterns.append(
                CandlePattern(
                    pattern_type=CandlePatternType.DOJI,
                    direction=CandlePatternDirection.NEUTRAL,
                    timestamp=curr.timestamp,
                    bar_index=i,
                    price=c,
                    confirmed_at=curr.timestamp,
                    confidence=0.85,
                    rule_applied="|C - O| <= 0.10 * (H - L) — Indecisión de mercado en equilibrio.",
                    invalidation_level=h if is_bearish else l,
                )
            )

        # -------------------------------------------------------------
        # 2. HAMMER (Lower shadow >= 2x body, tiny upper shadow, close near top)
        # -------------------------------------------------------------
        if lower_wick >= 2.0 * body and upper_wick <= 0.20 * body and body > 0:
            patterns.append(
                CandlePattern(
                    pattern_type=CandlePatternType.HAMMER,
                    direction=CandlePatternDirection.BULLISH,
                    timestamp=curr.timestamp,
                    bar_index=i,
                    price=c,
                    confirmed_at=curr.timestamp,
                    confidence=0.88,
                    rule_applied="Sombra inferior >= 2 * Cuerpo y sombra superior <= 0.2 * Cuerpo — Fuerte rechazo a precios bajos.",
                    invalidation_level=l,
                )
            )

        # -------------------------------------------------------------
        # 3. SHOOTING STAR (Upper shadow >= 2x body, tiny lower shadow, close near bottom)
        # -------------------------------------------------------------
        if upper_wick >= 2.0 * body and lower_wick <= 0.20 * body and body > 0:
            patterns.append(
                CandlePattern(
                    pattern_type=CandlePatternType.SHOOTING_STAR,
                    direction=CandlePatternDirection.BEARISH,
                    timestamp=curr.timestamp,
                    bar_index=i,
                    price=c,
                    confirmed_at=curr.timestamp,
                    confidence=0.88,
                    rule_applied="Sombra superior >= 2 * Cuerpo y sombra inferior <= 0.2 * Cuerpo — Fuerte rechazo a precios altos.",
                    invalidation_level=h,
                )
            )

        # -------------------------------------------------------------
        # 4. BULLISH ENGULFING (Current green body engulfs previous red body)
        # -------------------------------------------------------------
        if is_bullish and prev_is_bearish and o <= pc and c >= po and body > prev_body:
            patterns.append(
                CandlePattern(
                    pattern_type=CandlePatternType.BULLISH_ENGULFING,
                    direction=CandlePatternDirection.BULLISH,
                    timestamp=curr.timestamp,
                    bar_index=i,
                    price=c,
                    confirmed_at=curr.timestamp,
                    confidence=0.92,
                    rule_applied="Vela actual alcista envuelve cuerpo bajista previo (O_t <= C_{t-1} y C_t >= O_{t-1}).",
                    invalidation_level=l,
                )
            )

        # -------------------------------------------------------------
        # 5. BEARISH ENGULFING (Current red body engulfs previous green body)
        # -------------------------------------------------------------
        if is_bearish and prev_is_bullish and o >= pc and c <= po and body > prev_body:
            patterns.append(
                CandlePattern(
                    pattern_type=CandlePatternType.BEARISH_ENGULFING,
                    direction=CandlePatternDirection.BEARISH,
                    timestamp=curr.timestamp,
                    bar_index=i,
                    price=c,
                    confirmed_at=curr.timestamp,
                    confidence=0.92,
                    rule_applied="Vela actual bajista envuelve cuerpo alcista previo (O_t >= C_{t-1} y C_t <= O_{t-1}).",
                    invalidation_level=h,
                )
            )

        # -------------------------------------------------------------
        # 6. PIN BAR (Rejection wick >= 60% of total range, body <= 30% of range)
        # -------------------------------------------------------------
        if body <= 0.30 * rng:
            if lower_wick >= 0.60 * rng:
                patterns.append(
                    CandlePattern(
                        pattern_type=CandlePatternType.PIN_BAR,
                        direction=CandlePatternDirection.BULLISH,
                        timestamp=curr.timestamp,
                        bar_index=i,
                        price=c,
                        confirmed_at=curr.timestamp,
                        confidence=0.90,
                        rule_applied="Pin Bar alcista: mecha inferior >= 60% del rango total con cuerpo <= 30%.",
                        invalidation_level=l,
                    )
                )
            elif upper_wick >= 0.60 * rng:
                patterns.append(
                    CandlePattern(
                        pattern_type=CandlePatternType.PIN_BAR,
                        direction=CandlePatternDirection.BEARISH,
                        timestamp=curr.timestamp,
                        bar_index=i,
                        price=c,
                        confirmed_at=curr.timestamp,
                        confidence=0.90,
                        rule_applied="Pin Bar bajista: mecha superior >= 60% del rango total con cuerpo <= 30%.",
                        invalidation_level=h,
                    )
                )

        # -------------------------------------------------------------
        # 7. INSIDE BAR (H_t <= H_{t-1} and L_t >= L_{t-1})
        # -------------------------------------------------------------
        if h <= ph and l >= pl:
            patterns.append(
                CandlePattern(
                    pattern_type=CandlePatternType.INSIDE_BAR,
                    direction=CandlePatternDirection.NEUTRAL,
                    timestamp=curr.timestamp,
                    bar_index=i,
                    price=c,
                    confirmed_at=curr.timestamp,
                    confidence=0.80,
                    rule_applied="Inside Bar: rango completamente contenido dentro de la vela previa (H_t <= H_{t-1} y L_t >= L_{t-1}).",
                    invalidation_level=ph,
                )
            )

        # -------------------------------------------------------------
        # 8. OUTSIDE BAR (H_t > H_{t-1} and L_t < L_{t-1})
        # -------------------------------------------------------------
        if h > ph and l < pl:
            dir_outside = CandlePatternDirection.BULLISH if is_bullish else CandlePatternDirection.BEARISH
            patterns.append(
                CandlePattern(
                    pattern_type=CandlePatternType.OUTSIDE_BAR,
                    direction=dir_outside,
                    timestamp=curr.timestamp,
                    bar_index=i,
                    price=c,
                    confirmed_at=curr.timestamp,
                    confidence=0.82,
                    rule_applied="Outside Bar: rango expandido superando simultáneamente el máximo y mínimo previos.",
                    invalidation_level=l if is_bullish else h,
                )
            )

        # -------------------------------------------------------------
        # 9. MARUBOZU (Body >= 90% of total range)
        # -------------------------------------------------------------
        if body >= 0.90 * rng:
            dir_maru = CandlePatternDirection.BULLISH if is_bullish else CandlePatternDirection.BEARISH
            patterns.append(
                CandlePattern(
                    pattern_type=CandlePatternType.MARUBOZU,
                    direction=dir_maru,
                    timestamp=curr.timestamp,
                    bar_index=i,
                    price=c,
                    confirmed_at=curr.timestamp,
                    confidence=0.93,
                    rule_applied="Marubozu: cuerpo ocupa >= 90% del rango total sin mechas significativas. Alta convicción institucional.",
                    invalidation_level=o,
                )
            )

        # -------------------------------------------------------------
        # 10. 3-BAR PATTERNS: MORNING STAR & EVENING STAR
        # -------------------------------------------------------------
        if i >= 2:
            p2 = bars[i - 2]
            p2_o, p2_c = p2.open, p2.close
            p2_body = abs(p2_c - p2_o)
            p2_is_bear = p2_c < p2_o
            p2_is_bull = p2_c > p2_o

            # Morning Star: Bearish Bar -> Indecision/Star -> Strong Bullish closing > 50% into Bar 1
            if p2_is_bear and prev_body <= 0.40 * p2_body and is_bullish and c >= (p2_o + p2_c) / 2.0:
                patterns.append(
                    CandlePattern(
                        pattern_type=CandlePatternType.MORNING_STAR,
                        direction=CandlePatternDirection.BULLISH,
                        timestamp=curr.timestamp,
                        bar_index=i,
                        price=c,
                        confirmed_at=curr.timestamp,
                        confidence=0.94,
                        rule_applied="Morning Star: reversión en 3 velas (Vela bajista -> Vela estrella pequeña -> Vela alcista con cierre > 50% de vela 1).",
                        invalidation_level=min(p2.low, prev.low, l),
                    )
                )

            # Evening Star: Bullish Bar -> Indecision/Star -> Strong Bearish closing < 50% into Bar 1
            if p2_is_bull and prev_body <= 0.40 * p2_body and is_bearish and c <= (p2_o + p2_c) / 2.0:
                patterns.append(
                    CandlePattern(
                        pattern_type=CandlePatternType.EVENING_STAR,
                        direction=CandlePatternDirection.BEARISH,
                        timestamp=curr.timestamp,
                        bar_index=i,
                        price=c,
                        confirmed_at=curr.timestamp,
                        confidence=0.94,
                        rule_applied="Evening Star: reversión en 3 velas (Vela alcista -> Vela estrella pequeña -> Vela bajista con cierre < 50% de vela 1).",
                        invalidation_level=max(p2.high, prev.high, h),
                    )
                )

    return patterns
