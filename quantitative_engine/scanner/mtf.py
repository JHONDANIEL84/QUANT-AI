"""Multi-Timeframe (MTF) Confluence Engine — Phase 7 QUANT AI.

Analyzes structural alignment between a Higher Timeframe (HTF, e.g. 1D)
and a Lower Execution Timeframe (LTF, e.g. 4H or 1H).
"""

from typing import List, Optional

from data_providers.base.models import MarketBar
from quantitative_engine.market_structure.swings import detect_market_structure
from quantitative_engine.market_structure.models import TrendDirection
from quantitative_engine.smc.analyzer import run_smc_analysis
from quantitative_engine.scanner.models import MTFConfluenceResult


def analyze_mtf_confluence(
    symbol: str,
    htf_interval: str,
    htf_bars: List[MarketBar],
    ltf_interval: str,
    ltf_bars: List[MarketBar],
) -> MTFConfluenceResult:
    """Computes structural alignment between HTF and LTF.

    Args:
        symbol: Ticker symbol.
        htf_interval: Higher timeframe (e.g. '1d').
        htf_bars: Bars on higher timeframe.
        ltf_interval: Lower timeframe (e.g. '4h').
        ltf_bars: Bars on lower timeframe.

    Returns:
        MTFConfluenceResult with alignment status and score.
    """
    if len(htf_bars) < 15 or len(ltf_bars) < 15:
        return MTFConfluenceResult(
            symbol=symbol.upper(),
            htf_interval=htf_interval,
            ltf_interval=ltf_interval,
            htf_trend="UNKNOWN",
            ltf_trend="UNKNOWN",
            is_aligned=False,
            confluence_score=0.0,
            summary="Datos insuficientes para análisis multitemporal.",
        )

    # 1. Higher Timeframe Analysis
    htf_struct = detect_market_structure(htf_bars, k=3)
    htf_trend = htf_struct.trend

    # 2. Lower Timeframe Analysis
    ltf_struct = detect_market_structure(ltf_bars, k=3)
    ltf_trend = ltf_struct.trend

    # 3. SMC Dealing Range on HTF
    htf_smc = run_smc_analysis(symbol, htf_interval, htf_bars)

    score = 50.0  # Base neutral
    is_aligned = False
    summary_parts = []

    if htf_trend == TrendDirection.UPTREND:
        summary_parts.append(f"HTF ({htf_interval}) en TENDENCIA ALCISTA (Higher Highs / Higher Lows).")
        if ltf_trend == TrendDirection.UPTREND:
            score += 35.0
            is_aligned = True
            summary_parts.append(f"LTF ({ltf_interval}) ALINEADO ALCISTA. Fuerte confluencia direccional.")
        elif ltf_trend == TrendDirection.DOWNTREND:
            # Check if LTF is pulling back into an HTF discount zone
            if htf_smc.premium_discount and htf_smc.premium_discount.zone == "DISCOUNT":
                score += 25.0
                is_aligned = True
                summary_parts.append(
                    f"LTF ({ltf_interval}) en retroceso hacia zona DISCOUNT del HTF. "
                    f"Oportunidad de swing en descuento antes de reanudación alcista."
                )
            else:
                score -= 15.0
                summary_parts.append(f"LTF ({ltf_interval}) divergente a la baja; posible consolidación extendida.")
        else:
            score += 10.0
            summary_parts.append(f"LTF ({ltf_interval}) en compresión/rango; esperar expansión.")

    elif htf_trend == TrendDirection.DOWNTREND:
        summary_parts.append(f"HTF ({htf_interval}) en TENDENCIA BAJISTA (Lower Highs / Lower Lows).")
        if ltf_trend == TrendDirection.DOWNTREND:
            score += 35.0
            is_aligned = True
            summary_parts.append(f"LTF ({ltf_interval}) ALINEADO BAJISTA. Fuerte confluencia direccional vendedora.")
        elif ltf_trend == TrendDirection.UPTREND:
            if htf_smc.premium_discount and htf_smc.premium_discount.zone == "PREMIUM":
                score += 25.0
                is_aligned = True
                summary_parts.append(
                    f"LTF ({ltf_interval}) en rebote hacia zona PREMIUM del HTF. "
                    f"Oportunidad de swing en premium antes de reanudación bajista."
                )
            else:
                score -= 15.0
                summary_parts.append(f"LTF ({ltf_interval}) divergente al alza; esperar resolución.")
        else:
            score += 10.0
            summary_parts.append(f"LTF ({ltf_interval}) en compresión/rango.")

    else:
        summary_parts.append(f"HTF ({htf_interval}) en CONSOLIDACIÓN. Mercado sin tendencia de orden superior.")
        score = 40.0

    final_score = max(0.0, min(100.0, score))

    return MTFConfluenceResult(
        symbol=symbol.upper(),
        htf_interval=htf_interval,
        ltf_interval=ltf_interval,
        htf_trend=htf_trend.value,
        ltf_trend=ltf_trend.value,
        is_aligned=is_aligned,
        confluence_score=round(final_score, 1),
        summary=" ".join(summary_parts),
    )
