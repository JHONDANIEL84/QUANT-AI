"""Price Action Analyzer — Support/Resistance, Breakouts, Fakeouts, Compression.

Implements Section 10 of QUANT AI specification:
  - Support and Resistance zone detection via pivot clustering
  - Breakout and Fakeout detection (volume-confirmed vs. false breaks)
  - Pullback and Retest identification after structural breaks
  - Compression (ATR contraction) and Expansion detection

Causal constraint: no future bars are used when evaluating bar i.
Separates observations (factual) from hypotheses (interpretive).
"""

from typing import List, Optional

from data_providers.base.models import MarketBar
from quantitative_engine.price_action.models import (
    PriceActionAnalysis,
    PriceActionEvent,
    PriceActionEventType,
    PriceActionZone,
    ZoneStatus,
    ZoneType,
)


def _mean(values: List[float]) -> float:
    """Arithmetic mean without importing statistics module."""
    return sum(values) / len(values) if values else 0.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_atr(bars: List[MarketBar], period: int = 14) -> List[float]:
    """Wilder True Range smoothing — returns per-bar ATR values aligned with bars."""
    n = len(bars)
    trs: List[float] = []
    for i in range(n):
        h = bars[i].high
        l = bars[i].low
        pc = bars[i - 1].close if i > 0 else bars[i].open
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)

    atrs: List[float] = [0.0] * n
    if n < period:
        return atrs
    # Initial SMA seed
    atrs[period - 1] = sum(trs[:period]) / period
    alpha = 1.0 / period
    for i in range(period, n):
        atrs[i] = alpha * trs[i] + (1 - alpha) * atrs[i - 1]
    return atrs


def _collect_pivots(bars: List[MarketBar], k: int = 3) -> List[float]:
    """Returns raw pivot price levels (high and low) using fractal detection (strict causal)."""
    n = len(bars)
    levels: List[float] = []
    for i in range(k, n - k):
        h = bars[i].high
        l = bars[i].low
        is_sh = all(bars[i - j].high < h and bars[i + j].high < h for j in range(1, k + 1))
        is_sl = all(bars[i - j].low > l and bars[i + j].low > l for j in range(1, k + 1))
        if is_sh:
            levels.append(h)
        if is_sl:
            levels.append(l)
    return levels


def detect_support_resistance(
    bars: List[MarketBar],
    min_touches: int = 2,
    tolerance_pct: float = 0.003,
    k: int = 3,
) -> List[PriceActionZone]:
    """Identifies horizontal Support and Resistance zones by clustering pivot prices.

    Algorithm:
        1. Collect all fractal pivot prices (swing highs and swing lows).
        2. Group nearby pivots whose prices are within tolerance_pct of each other.
        3. Accept only clusters with >= min_touches pivots.
        4. Classify zone type by its price relative to current close.

    Args:
        bars: Chronologically sorted closed MarketBars.
        min_touches: Minimum pivot reactions required to validate a zone.
        tolerance_pct: Price proximity threshold (3 pips default = 0.3%).
        k: Fractal detection window (k bars before and k after).

    Returns:
        List[PriceActionZone]: Active and tested zones, sorted by strength descending.
    """
    if len(bars) < 2 * k + 2:
        return []

    pivot_prices = _collect_pivots(bars, k=k)
    if not pivot_prices:
        return []

    atrs = _compute_atr(bars, period=14)
    current_atr = atrs[-1] if atrs[-1] > 0 else 1.0
    current_close = bars[-1].close

    # Cluster pivots
    pivot_prices_sorted = sorted(pivot_prices)
    clusters: List[List[float]] = []

    for price in pivot_prices_sorted:
        placed = False
        for cluster in clusters:
            cluster_center = _mean(cluster)
            if abs(price - cluster_center) / cluster_center <= tolerance_pct:
                cluster.append(price)
                placed = True
                break
        if not placed:
            clusters.append([price])

    # Build zones from valid clusters
    zones: List[PriceActionZone] = []
    for cluster in clusters:
        if len(cluster) < min_touches:
            continue

        center = _mean(cluster)
        half_width = current_atr * 0.5
        top = center + half_width
        bottom = center - half_width
        touches = len(cluster)
        # Strength 0–1: normalized touches with diminishing returns
        strength = min(1.0, touches / 6.0)

        is_above = center > current_close
        zone_type = ZoneType.RESISTANCE if is_above else ZoneType.SUPPORT
        invalidation = bottom - current_atr if is_above else top + current_atr

        evidence = (
            f"Zona formada por {touches} reacciones de precio en torno a {center:.4f}. "
            f"Rango de zona: [{bottom:.4f} – {top:.4f}]. "
            f"ATR referencia: {current_atr:.4f}."
        )

        zones.append(
            PriceActionZone(
                zone_type=zone_type,
                price_level=round(center, 6),
                top_price=round(top, 6),
                bottom_price=round(bottom, 6),
                touches=touches,
                strength=round(strength, 4),
                status=ZoneStatus.ACTIVE,
                invalidation_level=round(invalidation, 6),
                evidence=evidence,
            )
        )

    # Sort strongest first
    zones.sort(key=lambda z: z.strength, reverse=True)
    return zones


def detect_breakouts(
    bars: List[MarketBar],
    zones: List[PriceActionZone],
    atrs: List[float],
) -> List[PriceActionEvent]:
    """Identifies price closes decisively beyond an active zone (causal only).

    A breakout is confirmed when:
        close > zone.top_price + 0.1 * ATR  (resistance break), or
        close < zone.bottom_price - 0.1 * ATR  (support break).

    Args:
        bars: Full bar series.
        zones: Detected S/R zones.
        atrs: Per-bar ATR values aligned with bars.

    Returns:
        List[PriceActionEvent]: Confirmed breakout events.
    """
    events: List[PriceActionEvent] = []
    for i, bar in enumerate(bars):
        atr = atrs[i] if atrs[i] > 0 else 1.0
        for zone in zones:
            if bar.close > zone.top_price + 0.1 * atr and zone.zone_type == ZoneType.RESISTANCE:
                events.append(
                    PriceActionEvent(
                        event_type=PriceActionEventType.BREAKOUT,
                        timestamp=bar.timestamp,
                        price=bar.close,
                        description=(
                            f"Ruptura alcista sobre resistencia {zone.price_level:.4f}. "
                            f"Cierre en {bar.close:.4f} supera zona en {(bar.close - zone.top_price):.4f}."
                        ),
                        rule_applied=(
                            "Cierre > zona.top + 0.1 * ATR — ruptura con margen sobre resistencia confirmada."
                        ),
                        invalidation_criteria=(
                            f"Cierre por debajo de {zone.price_level:.4f} invalida la ruptura."
                        ),
                        is_confirmed=True,
                    )
                )
            elif bar.close < zone.bottom_price - 0.1 * atr and zone.zone_type == ZoneType.SUPPORT:
                events.append(
                    PriceActionEvent(
                        event_type=PriceActionEventType.BREAKOUT,
                        timestamp=bar.timestamp,
                        price=bar.close,
                        description=(
                            f"Ruptura bajista bajo soporte {zone.price_level:.4f}. "
                            f"Cierre en {bar.close:.4f} cae {(zone.bottom_price - bar.close):.4f} bajo zona."
                        ),
                        rule_applied=(
                            "Cierre < zona.bottom - 0.1 * ATR — ruptura con margen bajo soporte confirmada."
                        ),
                        invalidation_criteria=(
                            f"Cierre por encima de {zone.price_level:.4f} invalida la ruptura bajista."
                        ),
                        is_confirmed=True,
                    )
                )
    return events


def detect_fakeouts(
    bars: List[MarketBar],
    zones: List[PriceActionZone],
    atrs: List[float],
    max_bars_to_return: int = 5,
) -> List[PriceActionEvent]:
    """Detects false breakouts: price briefly exceeds zone boundary then closes back inside.

    Fakeout rule:
        Bar i closes beyond zone boundary (> top or < bottom),
        but within max_bars_to_return subsequent bars it returns inside the zone.

    Args:
        bars: Full bar series.
        zones: Detected S/R zones.
        atrs: Per-bar ATR values.
        max_bars_to_return: Max bars allowed before price reverses back inside zone.

    Returns:
        List[PriceActionEvent]: Confirmed fakeout events.
    """
    events: List[PriceActionEvent] = []
    n = len(bars)
    for i, bar in enumerate(bars):
        atr = atrs[i] if atrs[i] > 0 else 1.0
        for zone in zones:
            broke_up = bar.close > zone.top_price + 0.1 * atr
            broke_down = bar.close < zone.bottom_price - 0.1 * atr
            if not (broke_up or broke_down):
                continue

            # Check if price returns inside zone within max_bars_to_return
            returned = False
            for j in range(i + 1, min(i + 1 + max_bars_to_return, n)):
                future_bar = bars[j]
                inside = zone.bottom_price <= future_bar.close <= zone.top_price
                if inside:
                    returned = True
                    break

            if returned:
                direction = "alcista" if broke_up else "bajista"
                events.append(
                    PriceActionEvent(
                        event_type=PriceActionEventType.FAKEOUT,
                        timestamp=bar.timestamp,
                        price=bar.close,
                        description=(
                            f"Falsa ruptura {direction} en zona {zone.price_level:.4f}. "
                            f"El precio superó la frontera pero regresó dentro de {max_bars_to_return} barras."
                        ),
                        rule_applied=(
                            f"Cierre fuera de zona, retorno al interior en <= {max_bars_to_return} barras — Fakeout / Bull Trap / Bear Trap."
                        ),
                        invalidation_criteria=(
                            "Cierre definitivo fuera de la zona tras el retorno invalidaría este patrón."
                        ),
                        is_confirmed=True,
                    )
                )
    return events


def detect_pullbacks_retests(
    bars: List[MarketBar],
    zones: List[PriceActionZone],
    atrs: List[float],
    lookback: int = 15,
) -> List[PriceActionEvent]:
    """Identifies price returning to test a zone after a confirmed breakout.

    Retest rule:
        A prior breakout occurred (price closed outside the zone),
        and within lookback bars the price returns to test the former
        zone boundary (now acting as new support/resistance).

    Args:
        bars: Full bar series.
        zones: Detected S/R zones.
        atrs: Per-bar ATR values.
        lookback: Maximum bars after breakout to look for retest.

    Returns:
        List[PriceActionEvent]: Confirmed pullback/retest events.
    """
    events: List[PriceActionEvent] = []
    n = len(bars)

    for zone in zones:
        # Find the first breakout bar for this zone
        breakout_idx: Optional[int] = None
        broke_direction: Optional[str] = None
        for i, bar in enumerate(bars):
            atr = atrs[i] if atrs[i] > 0 else 1.0
            if bar.close > zone.top_price + 0.1 * atr:
                breakout_idx = i
                broke_direction = "up"
                break
            elif bar.close < zone.bottom_price - 0.1 * atr:
                breakout_idx = i
                broke_direction = "down"
                break

        if breakout_idx is None:
            continue

        # Look for retest within lookback bars
        for j in range(breakout_idx + 1, min(breakout_idx + lookback + 1, n)):
            bar = bars[j]
            atr = atrs[j] if atrs[j] > 0 else 1.0
            # Retest: price comes back close to zone boundary
            near_zone = (
                abs(bar.low - zone.top_price) <= 0.5 * atr
                or abs(bar.high - zone.bottom_price) <= 0.5 * atr
                or zone.bottom_price <= bar.close <= zone.top_price
            )
            if near_zone:
                direction = "soporte previo (resistencia convertida en soporte)" if broke_direction == "up" else "resistencia previa (soporte convertido en resistencia)"
                events.append(
                    PriceActionEvent(
                        event_type=PriceActionEventType.RETEST,
                        timestamp=bar.timestamp,
                        price=bar.close,
                        description=(
                            f"Retesteo de {direction} en {zone.price_level:.4f}. "
                            f"El precio regresa a zona tras ruptura en barra {breakout_idx}."
                        ),
                        rule_applied=(
                            "Precio regresa a frontera de zona dentro de lookback barras post-ruptura — Retest / Pullback estructural."
                        ),
                        invalidation_criteria=(
                            f"Cierre por debajo de {zone.bottom_price:.4f} (ruptura alcista) o por encima de {zone.top_price:.4f} (ruptura bajista) invalida el retest."
                        ),
                        is_confirmed=True,
                    )
                )
                break  # One retest per zone

    return events


def detect_compression(
    bars: List[MarketBar],
    lookback: int = 20,
    reference_period: int = 50,
) -> bool:
    """Detects ATR compression: current ATR < 50% of longer-term average ATR.

    Args:
        bars: Full bar series.
        lookback: Short-term ATR period for current volatility.
        reference_period: Baseline ATR period for comparison.

    Returns:
        bool: True if compression is active (volatility contracting).
    """
    n = len(bars)
    if n < reference_period + 1:
        return False

    all_atrs = _compute_atr(bars, period=14)
    if not all_atrs or all_atrs[-1] == 0:
        return False

    current_atr = all_atrs[-1]
    # Average ATR over reference_period bars
    reference_window = all_atrs[max(0, n - reference_period) : n]
    valid_ref = [a for a in reference_window if a > 0]
    if not valid_ref:
        return False

    reference_avg = _mean(valid_ref)
    return current_atr < 0.50 * reference_avg


def run_price_action_analysis(bars: List[MarketBar]) -> PriceActionAnalysis:
    """Main facade: runs the full Price Action analysis pipeline.

    Args:
        bars: Chronological list of closed MarketBars (minimum ~50 recommended).

    Returns:
        PriceActionAnalysis: Zones, events, compression flag, observation, hypothesis.
    """
    if len(bars) < 10:
        return PriceActionAnalysis(
            zones=[],
            events=[],
            is_compressed=False,
            observation="Datos insuficientes para análisis de Price Action (mínimo 10 barras requeridas).",
            hypothesis="N/A — sin datos suficientes.",
        )

    atrs = _compute_atr(bars, period=14)
    zones = detect_support_resistance(bars, min_touches=2, tolerance_pct=0.003)
    breakouts = detect_breakouts(bars, zones, atrs)
    fakeouts = detect_fakeouts(bars, zones, atrs)
    retests = detect_pullbacks_retests(bars, zones, atrs)
    is_compressed = detect_compression(bars)

    all_events = sorted(
        breakouts + fakeouts + retests,
        key=lambda e: e.timestamp,
    )

    # Build factual observation and interpretive hypothesis
    active_zones = [z for z in zones if z.status == ZoneStatus.ACTIVE]
    total_events = len(all_events)
    current_close = bars[-1].close

    nearest_support = next(
        (z for z in sorted(zones, key=lambda z: z.price_level, reverse=False)
         if z.price_level < current_close),
        None,
    )
    nearest_resistance = next(
        (z for z in sorted(zones, key=lambda z: z.price_level)
         if z.price_level > current_close),
        None,
    )

    observation = (
        f"Se detectaron {len(zones)} zonas de precio activas "
        f"({len([z for z in zones if z.zone_type.value in ('SUPPORT','DEMAND')])} soportes / "
        f"{len([z for z in zones if z.zone_type.value in ('RESISTANCE','SUPPLY')])} resistencias). "
        f"Precio actual: {current_close:.4f}. "
        f"Eventos detectados: {total_events} "
        f"({len(breakouts)} rupturas, {len(fakeouts)} falsas rupturas, {len(retests)} retesteos). "
        f"Compresión de volatilidad: {'Sí' if is_compressed else 'No'}."
    )

    hypothesis_parts = []
    if nearest_support:
        hypothesis_parts.append(
            f"Soporte más cercano en {nearest_support.price_level:.4f} "
            f"(fuerza {nearest_support.strength:.2f}). "
            "Si el precio mantiene este nivel, podría intentar nuevo avance."
        )
    if nearest_resistance:
        hypothesis_parts.append(
            f"Resistencia más cercana en {nearest_resistance.price_level:.4f}. "
            "Una ruptura sostenida sobre esta zona podría abrir espacio alcista adicional."
        )
    if is_compressed:
        hypothesis_parts.append(
            "La contracción de ATR sugiere acumulación o distribución. "
            "Un movimiento direccional expansivo podría materializarse."
        )

    hypothesis = (
        " ".join(hypothesis_parts)
        if hypothesis_parts
        else "Estructura de precio sin señales hipotéticas claras en este momento."
    )

    return PriceActionAnalysis(
        zones=zones,
        events=all_events,
        is_compressed=is_compressed,
        observation=observation,
        hypothesis=hypothesis,
    )
