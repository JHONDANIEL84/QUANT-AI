"""Liquidity Intelligence Master Orchestrator — Phase 6 QUANT AI.

Combines:
  - Equal Highs (EQH) & Equal Lows (EQL)
  - Buy-side (BSL) & Sell-side (SSL) pools
  - Session benchmarks (PDH, PDL, PWH, PWL)
  - Confirmed Liquidity Sweeps / Hunts with rejection
  - Strict separation of factual observations from testable hypotheses.
"""

from typing import List, Optional
import numpy as np

from data_providers.base.models import MarketBar
from quantitative_engine.market_structure.swings import detect_market_structure
from quantitative_engine.liquidity.models import (
    LiquidityAnalysis,
    LiquidityPool,
    LiquiditySweepEvent,
    SessionLevels,
    SweepStatus,
    LiquidityType,
)
from quantitative_engine.liquidity.equal_levels import detect_equal_levels_and_pools
from quantitative_engine.liquidity.session_levels import compute_session_levels
from quantitative_engine.liquidity.sweeps import detect_liquidity_sweeps


def run_liquidity_analysis(
    symbol: str,
    interval: str,
    bars: List[MarketBar],
) -> LiquidityAnalysis:
    """Runs the complete Liquidity Intelligence analysis on the given bar series.

    Args:
        symbol: Ticker symbol (e.g. BTCUSDT, AAPL, ECOPETROL).
        interval: Bar interval (1d, 4h, 1h, 15m).
        bars: Chronological list of MarketBars.

    Returns:
        LiquidityAnalysis with mapped pools, sweeps, and session levels.
    """
    if len(bars) < 10:
        return LiquidityAnalysis(
            symbol=symbol.upper(),
            interval=interval,
            bars_analyzed=len(bars),
            pools=[],
            sweeps=[],
            session_levels=SessionLevels(),
            observation="Datos insuficientes para análisis de Liquidity Intelligence (mínimo 10 barras requeridas).",
            hypothesis="Se requiere una serie temporal más extensa para proyectar tomas de liquidez.",
            data_status="observation",
        )

    # 1. Compute rolling ATR for dynamic tolerance
    highs = np.array([b.high for b in bars], dtype=float)
    lows = np.array([b.low for b in bars], dtype=float)
    closes = np.array([b.close for b in bars], dtype=float)
    tr = np.maximum(highs[1:] - lows[1:], np.abs(highs[1:] - closes[:-1]))
    atr_val = float(np.mean(tr[-14:])) if len(tr) >= 14 else float(np.mean(tr)) if len(tr) > 0 else 1.0

    # 2. Extract confirmed structural pivots
    struct_res = detect_market_structure(bars, k=3)
    pivots = struct_res.pivots

    # 3. Detect Equal Highs, Equal Lows, BSL and SSL pools
    pools = detect_equal_levels_and_pools(bars, pivots, atr_val=atr_val)

    # 4. Compute Session Anchor Levels (PDH, PDL, PWH, PWL)
    session_levels = compute_session_levels(bars)

    # Add active session levels as pools if available
    last_t = bars[-1].timestamp
    if session_levels.pdh:
        pools.append(
            LiquidityPool(
                pool_type=LiquidityType.PDH,
                price_level=session_levels.pdh,
                top_price=session_levels.pdh + atr_val * 0.2,
                bottom_price=session_levels.pdh - atr_val * 0.2,
                touch_count=1,
                first_touch_at=last_t,
                last_touch_at=last_t,
                liquidity_score=60.0,
                status=SweepStatus.ACTIVE,
                rule_applied=f"Previous Day High (PDH) en {session_levels.pdh:.2f}.",
            )
        )
    if session_levels.pdl:
        pools.append(
            LiquidityPool(
                pool_type=LiquidityType.PDL,
                price_level=session_levels.pdl,
                top_price=session_levels.pdl + atr_val * 0.2,
                bottom_price=session_levels.pdl - atr_val * 0.2,
                touch_count=1,
                first_touch_at=last_t,
                last_touch_at=last_t,
                liquidity_score=60.0,
                status=SweepStatus.ACTIVE,
                rule_applied=f"Previous Day Low (PDL) en {session_levels.pdl:.2f}.",
            )
        )

    # 5. Detect Confirmed Liquidity Sweeps / Hunts
    sweeps = detect_liquidity_sweeps(bars, pools)

    # 6. Synthesize Factual Observation
    active_pools = [p for p in pools if p.status == SweepStatus.ACTIVE]
    swept_pools = [p for p in pools if p.status == SweepStatus.SWEPT]
    eqh_pools = [p for p in active_pools if p.pool_type == LiquidityType.EQH]
    eql_pools = [p for p in active_pools if p.pool_type == LiquidityType.EQL]

    obs_parts = [
        f"Activo {symbol.upper()} ({interval}): {len(bars)} barras analizadas con ATR de {atr_val:.2f}."
    ]

    obs_parts.append(
        f"Pools de liquidez activos: {len(active_pools)} ({len(eqh_pools)} EQH por encima, {len(eql_pools)} EQL por debajo)."
    )

    if sweeps:
        last_sw = sweeps[-1]
        obs_parts.append(
            f"Último barrido institucional confirmado: {last_sw.pool_type.value} en precio {last_sw.price_level:.2f} "
            f"(Extremo mecha: {last_sw.penetration_price:.2f}, Cierre rechazo: {last_sw.rejection_close:.2f})."
        )
    else:
        obs_parts.append("No se registran barridos con rechazo activo en las últimas barras.")

    if session_levels.pdh and session_levels.pdl:
        obs_parts.append(
            f"Niveles de sesión: PDH={session_levels.pdh:.2f}, PDL={session_levels.pdl:.2f}."
        )

    observation_text = " ".join(obs_parts)

    # 7. Formulate Testable Hypotheses
    hypo_parts = []
    current_price = bars[-1].close

    if sweeps:
        last_sw = sweeps[-1]
        if last_sw.pool_type in (LiquidityType.EQH, LiquidityType.BSL, LiquidityType.PDH, LiquidityType.PWH):
            hypo_parts.append(
                f"HIPÓTESIS DE GIRO BAJISTA POST-SWEEP: Barrido de Buy-side Liquidity en {last_sw.price_level:.2f} con absorción. "
                f"Probable rotación hacia pools de Sell-side inferiores. "
                f"Criterio de invalidación: Cierre por encima de {last_sw.invalidation_level:.2f}."
            )
        else:
            hypo_parts.append(
                f"HIPÓTESIS DE GIRO ALCISTA POST-SWEEP: Barrido de Sell-side Liquidity en {last_sw.price_level:.2f} con absorción. "
                f"Probable rotación hacia pools de Buy-side superiores. "
                f"Criterio de invalidación: Cierre por debajo de {last_sw.invalidation_level:.2f}."
            )
    else:
        # Distance to closest active EQH and EQL
        above_pools = [p for p in active_pools if p.price_level > current_price]
        below_pools = [p for p in active_pools if p.price_level < current_price]

        if above_pools and below_pools:
            closest_above = min(above_pools, key=lambda x: x.price_level - current_price)
            closest_below = min(below_pools, key=lambda x: current_price - x.price_level)
            hypo_parts.append(
                f"HIPÓTESIS DE ATRACCIÓN DE LIQUIDEZ: Precio actual ({current_price:.2f}) contenido entre "
                f"Buy-side {closest_above.pool_type.value} ({closest_above.price_level:.2f}) y "
                f"Sell-side {closest_below.pool_type.value} ({closest_below.price_level:.2f}). "
                f"Monitorear cuál pool es barrido primero como catalizador de entrada."
            )
        elif above_pools:
            closest_above = min(above_pools, key=lambda x: x.price_level - current_price)
            hypo_parts.append(
                f"HIPÓTESIS DE PROYECCIÓN ALCISTA: Objetivo de liquidez superior en {closest_above.price_level:.2f} ({closest_above.pool_type.value})."
            )
        elif below_pools:
            closest_below = min(below_pools, key=lambda x: current_price - x.price_level)
            hypo_parts.append(
                f"HIPÓTESIS DE PROYECCIÓN BAJISTA: Objetivo de liquidez inferior en {closest_below.price_level:.2f} ({closest_below.pool_type.value})."
            )
        else:
            hypo_parts.append("Estructura sin pools de liquidez concentrados; operar con niveles de sesión.")

    hypothesis_text = " ".join(hypo_parts)

    return LiquidityAnalysis(
        symbol=symbol.upper(),
        interval=interval,
        bars_analyzed=len(bars),
        pools=pools,
        sweeps=sweeps,
        session_levels=session_levels,
        observation=observation_text,
        hypothesis=hypothesis_text,
        data_status="observation",
    )
