"""Quantitative Context Builder — Fase 10 QUANT AI.

Construye un snapshot contextual unificado del activo a partir de todos los motores
cuantitativos (Indicadores, Estructura, SMC, Liquidez, Scanner y Riesgo) para
alimentar el prompt del Asistente QUANT AI.

Garantiza observabilidad estricta: todos los datos son hechos cuantitativos verificados.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime

from data_providers.base.models import MarketBar
from quantitative_engine.indicators import indicator_engine
from quantitative_engine.market_structure.swings import detect_market_structure
from quantitative_engine.market_structure.models import MarketStructureResult
from quantitative_engine.smc.analyzer import run_smc_analysis
from quantitative_engine.smc.models import SMCAnalysis, MitigationStatus
from quantitative_engine.liquidity.analyzer import run_liquidity_analysis
from quantitative_engine.liquidity.models import LiquidityAnalysis
from quantitative_engine.scanner.evaluator import evaluate_asset_opportunity
from quantitative_engine.scanner.models import ScanOpportunity


def build_chart_quantitative_context(
    symbol: str,
    interval: str,
    bars: List[MarketBar],
    market: str = "crypto",
) -> Dict[str, Any]:
    """Genera un contexto cuantitativo enriquecido a partir de la serie de barras.

    Args:
        symbol: Símbolo del activo (ej. 'BTCUSDT', 'ECOPETROL').
        interval: Temporalidad (ej. '1d', '4h', '1h').
        bars: Lista de barras históricas.
        market: Mercado ('crypto', 'stock', 'bvc').

    Returns:
        Diccionario con datos técnicos estructurados y texto formateado para el LLM.
    """
    if not bars:
        return {
            "symbol": symbol,
            "interval": interval,
            "error": "No hay barras de mercado disponibles.",
            "prompt_text": f"Activo {symbol} ({interval}): Sin datos de mercado disponibles.",
        }

    current_bar = bars[-1]
    current_price = current_bar.close

    # 1. Indicadores Técnicos
    indicators = indicator_engine.compute_all(bars, symbol, interval)
    ema20 = indicators.ema_20[-1] if indicators.ema_20 else None
    ema50 = indicators.ema_50[-1] if indicators.ema_50 else None
    ema200 = indicators.ema_200[-1] if indicators.ema_200 else None
    rsi14 = indicators.rsi_14[-1] if indicators.rsi_14 else None
    atr14 = indicators.atr_14[-1] if indicators.atr_14 else None

    # 2. Estructura de Mercado
    struct: MarketStructureResult = detect_market_structure(bars, k=3)

    # 3. Smart Money Concepts (SMC)
    smc: SMCAnalysis = run_smc_analysis(symbol, interval, bars)
    active_obs = [ob for ob in smc.order_blocks if ob.status == MitigationStatus.UNMITIGATED]
    unfilled_fvgs = [f for f in smc.fair_value_gaps if f.status != MitigationStatus.MITIGATED]

    # 4. Liquidez Institucional
    liq: LiquidityAnalysis = run_liquidity_analysis(symbol, interval, bars)

    # 5. Oportunidad del Scanner
    opportunity: Optional[ScanOpportunity] = evaluate_asset_opportunity(symbol, market, interval, bars)

    # --- Construir bloque Markdown para el LLM ---
    lines = [
        f"### ESTADO CUANTITATIVO DEL ACTIVO: {symbol.upper()} ({interval})",
        f"- **Precio Actual**: {current_price:,.4f}",
        f"- **Fecha/Hora Cierre**: {current_bar.timestamp.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "#### 1. Estructura de Mercado y Price Action:",
        f"- **Tendencia Estructural**: {struct.trend.value}",
        f"- **Último Swing High**: {struct.last_swing_high if struct.last_swing_high else 'N/A'}",
        f"- **Último Swing Low**: {struct.last_swing_low if struct.last_swing_low else 'N/A'}",
        f"- **Resumen Estructural**: {struct.summary}",
        "",
        "#### 2. Indicadores Técnicos:",
        f"- **EMA 20**: {f'{ema20:,.2f}' if ema20 else 'N/A'}",
        f"- **EMA 50**: {f'{ema50:,.2f}' if ema50 else 'N/A'}",
        f"- **EMA 200**: {f'{ema200:,.2f}' if ema200 else 'N/A'}",
        f"- **RSI (14)**: {f'{rsi14:.1f}' if rsi14 else 'N/A'}",
        f"- **ATR (14)**: {f'{atr14:,.2f}' if atr14 else 'N/A'}",
        "",
        "#### 3. Smart Money Concepts (SMC):",
    ]

    if smc.premium_discount:
        pd_range = smc.premium_discount
        lines.append(
            f"- **Rango de Negociación**: Zona {pd_range.zone} ({pd_range.current_position_pct:.1f}% del rango) | "
            f"Equilibrio (50%): {pd_range.equilibrium:,.2f}"
        )
    else:
        lines.append("- **Rango de Negociación**: Sin rango activo definido.")

    lines.append(f"- **Order Blocks Activos (Sin Mitigar)**: {len(active_obs)}")
    for ob in active_obs[:3]:
        lines.append(
            f"  * OB {ob.direction.value}: [{ob.bottom_price:,.2f} - {ob.top_price:,.2f}] "
            f"(Score de calidad: {ob.quality_score:.0f}/100)"
        )

    lines.append(f"- **Fair Value Gaps (FVG) Abiertos**: {len(unfilled_fvgs)}")

    if smc.structure_breaks:
        last_break = smc.structure_breaks[-1]
        lines.append(
            f"- **Última Ruptura Estructural**: {last_break.break_type.value} {last_break.direction.value} "
            f"en {last_break.broken_level:,.2f}"
        )

    lines.extend([
        "",
        "#### 4. Liquidez Institucional y Barridos:",
        f"- **Piscinas de Liquidez Activas**: {len(liq.pools)}",
        f"- **Barridos Confirmados**: {len(liq.sweeps)}",
    ])
    if liq.sweeps:
        last_sw = liq.sweeps[-1]
        lines.append(
            f"  * Último barrido: {last_sw.pool_type.value} en {last_sw.sweep_price:,.2f} "
            f"con rechazo en {last_sw.rejection_close:,.2f}"
        )

    if opportunity:
        lines.extend([
            "",
            "#### 5. Evaluación del Scanner Cuantitativo:",
            f"- **Dirección**: {opportunity.direction.value}",
            f"- **Convicción**: {opportunity.conviction.value}",
            f"- **Score Compuesto**: {opportunity.score:.1f}/100",
            f"- **Nivel de Invalidación**: {opportunity.invalidation_level if opportunity.invalidation_level else 'N/A'}",
            f"- **Criterios Cumplidos**: {', '.join(opportunity.matched_criteria[:4]) if opportunity.matched_criteria else 'Ninguno'}",
        ])

    prompt_text = "\n".join(lines)

    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "current_price": current_price,
        "trend": struct.trend.value,
        "rsi": rsi14,
        "ema20": ema20,
        "ema50": ema50,
        "dealing_zone": smc.premium_discount.zone if smc.premium_discount else "UNKNOWN",
        "active_obs_count": len(active_obs),
        "scanner_score": opportunity.score if opportunity else None,
        "prompt_text": prompt_text,
    }
