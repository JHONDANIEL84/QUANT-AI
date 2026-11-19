"""Smart Money Concepts (SMC) Master Orchestrator — Phase 5 QUANT AI.

Orchestrates:
  - BOS (Break of Structure) & CHOCH (Change of Character)
  - Order Blocks (Bullish, Bearish, Breakers) with Mitigation tracking
  - Fair Value Gaps (FVG) with Consequent Encroachment (50%)
  - Premium vs. Discount Dealing Range
  - Strict separation between facts (observations) and hypotheses.
"""

from typing import List, Optional
from datetime import datetime

from data_providers.base.models import MarketBar
from quantitative_engine.market_structure.swings import detect_market_structure
from quantitative_engine.smc.models import (
    SMCAnalysis,
    StructureBreak,
    OrderBlock,
    FairValueGap,
    PremiumDiscountRange,
    MitigationStatus,
    SMCDirection,
)
from quantitative_engine.smc.bos_choch import detect_structure_breaks
from quantitative_engine.smc.fvg import detect_fair_value_gaps
from quantitative_engine.smc.order_blocks import detect_order_blocks
from quantitative_engine.smc.premium_discount import compute_premium_discount


def run_smc_analysis(
    symbol: str,
    interval: str,
    bars: List[MarketBar],
) -> SMCAnalysis:
    """Executes the complete Smart Money Concepts analysis pipeline.

    Args:
        symbol: Ticker symbol (e.g. BTCUSDT, AAPL, ECOPETROL).
        interval: Bar interval (1d, 4h, 1h, etc.).
        bars: Chronological list of MarketBar items.

    Returns:
        SMCAnalysis with all active and historical SMC structures.
    """
    if len(bars) < 10:
        return SMCAnalysis(
            symbol=symbol.upper(),
            interval=interval,
            bars_analyzed=len(bars),
            observation="Datos insuficientes para análisis institucional SMC (mínimo 10 barras requeridas).",
            hypothesis="Se requieren más datos históricos normalizados para formular hipótesis cuantitativas.",
            data_status="observation",
        )

    # 1. Detect market structure pivots
    struct_result = detect_market_structure(bars, k=3)
    pivots = struct_result.pivots

    # 2. Detect BOS & CHOCH
    breaks = detect_structure_breaks(bars, pivots, k=3)

    # 3. Detect FVGs
    fvgs = detect_fair_value_gaps(bars)

    # 4. Detect Order Blocks
    order_blocks = detect_order_blocks(bars, breaks, fvgs)

    # 5. Compute Premium / Discount
    prem_disc = compute_premium_discount(bars, pivots)

    # 6. Synthesize Factual Observation
    active_obs = [ob for ob in order_blocks if ob.status == MitigationStatus.UNMITIGATED]
    unfilled_fvgs = [f for f in fvgs if f.status != MitigationStatus.MITIGATED]
    recent_breaks = breaks[-3:] if breaks else []

    obs_parts = []
    obs_parts.append(f"Activo {symbol.upper()} ({interval}) con {len(bars)} barras analizadas.")

    if recent_breaks:
        last_brk = recent_breaks[-1]
        obs_parts.append(
            f"Última ruptura estructural: {last_brk.break_type.value} {last_brk.direction.value} "
            f"en precio {last_brk.breaking_price:.2f} (Pivote roto: {last_brk.broken_pivot_price:.2f})."
        )
    else:
        obs_parts.append("Estructura en rango sin rupturas BOS/CHOCH recientes confirmadas.")

    obs_parts.append(
        f"Order Blocks activos sin mitigar: {len(active_obs)} (de un total de {len(order_blocks)} detectados)."
    )
    obs_parts.append(
        f"FVGs abiertos/parciales: {len(unfilled_fvgs)} (de {len(fvgs)} detectados)."
    )

    if prem_disc:
        obs_parts.append(prem_disc.observation)

    observation_text = " ".join(obs_parts)

    # 7. Formulate Testable Hypotheses
    hypo_parts = []
    if prem_disc:
        if prem_disc.zone == "DISCOUNT":
            bullish_obs = [ob for ob in active_obs if ob.direction == SMCDirection.BULLISH]
            if bullish_obs:
                best_ob = max(bullish_obs, key=lambda x: x.quality_score)
                hypo_parts.append(
                    f"HIPÓTESIS ALCISTA: Precio en DISCOUNT ({prem_disc.current_position_pct:.1f}%). "
                    f"Probable reacción compradora en Bullish Order Block [{best_ob.bottom_price:.2f} - {best_ob.top_price:.2f}] "
                    f"(Score: {best_ob.quality_score}). Criterio de invalidación: Cierre por debajo de {best_ob.bottom_price:.2f}."
                )
            else:
                hypo_parts.append(
                    f"HIPÓTESIS ALCISTA: Precio en DISCOUNT ({prem_disc.current_position_pct:.1f}%). "
                    f"Buscar confluencia con mitigación de FVGs inferiores o confirmación de CHOCH alcista."
                )
        elif prem_disc.zone == "PREMIUM":
            bearish_obs = [ob for ob in active_obs if ob.direction == SMCDirection.BEARISH]
            if bearish_obs:
                best_ob = max(bearish_obs, key=lambda x: x.quality_score)
                hypo_parts.append(
                    f"HIPÓTESIS BAJISTA: Precio en PREMIUM ({prem_disc.current_position_pct:.1f}%). "
                    f"Probable reacción vendedora en Bearish Order Block [{best_ob.bottom_price:.2f} - {best_ob.top_price:.2f}] "
                    f"(Score: {best_ob.quality_score}). Criterio de invalidación: Cierre por encima de {best_ob.top_price:.2f}."
                )
            else:
                hypo_parts.append(
                    f"HIPÓTESIS BAJISTA: Precio en PREMIUM ({prem_disc.current_position_pct:.1f}%). "
                    f"Buscar confluencia con mitigación de FVGs superiores o confirmación de CHOCH bajista."
                )
        else:
            hypo_parts.append(
                f"HIPÓTESIS NEUTRAL / EQUILIBRIO: Precio oscila cercano al 50% ({prem_disc.equilibrium:.2f}). "
                f"Se desaconsejan entradas tempranas de swing hasta que el precio se desplace a zonas de Premium o Discount."
            )
    else:
        hypo_parts.append("Estructura en compresión; esperar expansión direccional clara.")

    hypothesis_text = " ".join(hypo_parts)

    return SMCAnalysis(
        symbol=symbol.upper(),
        interval=interval,
        bars_analyzed=len(bars),
        structure_breaks=breaks,
        order_blocks=order_blocks,
        fair_value_gaps=fvgs,
        premium_discount=prem_disc,
        observation=observation_text,
        hypothesis=hypothesis_text,
        data_status="observation",
    )
