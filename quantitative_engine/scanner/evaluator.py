"""Single Asset Opportunity Evaluator — Phase 7 QUANT AI.

Evaluates an asset's price action, SMC zones, liquidity sweeps, and technical indicators
to compute an objective composite opportunity score (0 - 100).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from data_providers.base.models import MarketBar
from quantitative_engine.indicators import compute_ema, compute_rsi
from quantitative_engine.market_structure.swings import detect_market_structure
from quantitative_engine.market_structure.models import TrendDirection
from quantitative_engine.smc.analyzer import run_smc_analysis
from quantitative_engine.smc.models import SMCDirection, MitigationStatus
from quantitative_engine.liquidity.analyzer import run_liquidity_analysis
from quantitative_engine.liquidity.models import SweepStatus, LiquidityType
from quantitative_engine.scanner.models import ScanOpportunity, SetupDirection, ConvictionLevel


def evaluate_asset_opportunity(
    symbol: str,
    market: str,
    interval: str,
    bars: List[MarketBar],
) -> Optional[ScanOpportunity]:
    """Computes technical and institutional confluence score for a given asset.

    Returns:
        ScanOpportunity with verified facts, matched criteria, score, and invalidation level.
    """
    if len(bars) < 20:
        return None

    current_bar = bars[-1]
    current_price = current_bar.close

    matched: List[str] = []
    unmatched: List[str] = []
    evidence: Dict[str, Any] = {}
    bullish_points = 0.0
    bearish_points = 0.0

    # -------------------------------------------------------------
    # 1. Technical Indicators (EMAs, RSI, Volume)
    # -------------------------------------------------------------
    import pandas as pd
    closes_series = pd.Series([b.close for b in bars], dtype=float)
    volumes = np.array([b.volume for b in bars], dtype=float)
    avg_vol = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else float(np.mean(volumes))
    vol_ratio = current_bar.volume / avg_vol if avg_vol > 0 else 1.0
    evidence["volume_ratio"] = round(vol_ratio, 2)

    # RSI
    rsi_vals = compute_rsi(closes_series, period=14)
    current_rsi = float(rsi_vals.iloc[-1]) if not np.isnan(rsi_vals.iloc[-1]) else 50.0
    evidence["rsi_14"] = round(current_rsi, 1)

    if current_rsi <= 38.0:
        matched.append(f"RSI en zona de sobreventa ({current_rsi:.1f} <= 38)")
        bullish_points += 10.0
    elif current_rsi >= 62.0:
        matched.append(f"RSI en zona de sobrecompra ({current_rsi:.1f} >= 62)")
        bearish_points += 10.0
    else:
        unmatched.append(f"RSI en rango neutral ({current_rsi:.1f})")

    # EMAs (20, 50, 200)
    ema20 = float(compute_ema(closes_series, 20).iloc[-1])
    ema50 = float(compute_ema(closes_series, 50).iloc[-1])
    evidence["ema_20"] = round(ema20, 2)
    evidence["ema_50"] = round(ema50, 2)

    if current_price > ema20 > ema50:
        matched.append("Alineación alcista de medias móviles (Precio > EMA 20 > EMA 50)")
        bullish_points += 10.0
    elif current_price < ema20 < ema50:
        matched.append("Alineación bajista de medias móviles (Precio < EMA 20 < EMA 50)")
        bearish_points += 10.0
    else:
        unmatched.append("Medias móviles sin alineación tendencial clara")

    if vol_ratio >= 1.25:
        matched.append(f"Expansión de volumen institucional (+{(vol_ratio - 1)*100:.0f}% vs promedio)")
        bullish_points += 5.0
        bearish_points += 5.0

    # -------------------------------------------------------------
    # 2. Market Structure (HH, HL, LH, LL)
    # -------------------------------------------------------------
    struct = detect_market_structure(bars, k=3)
    evidence["trend"] = struct.trend.value

    if struct.trend == TrendDirection.UPTREND:
        matched.append("Estructura de mercado alcista (HH + HL confirmados)")
        bullish_points += 20.0
    elif struct.trend == TrendDirection.DOWNTREND:
        matched.append("Estructura de mercado bajista (LH + LL confirmados)")
        bearish_points += 20.0
    else:
        unmatched.append("Estructura de mercado en rango o consolidación")

    # -------------------------------------------------------------
    # 3. Smart Money Concepts (BOS, CHOCH, OB, FVG, Dealing Range)
    # -------------------------------------------------------------
    smc = run_smc_analysis(symbol, interval, bars)

    # Premium / Discount
    if smc.premium_discount:
        pd_range = smc.premium_discount
        evidence["dealing_range_position_pct"] = pd_range.current_position_pct
        evidence["equilibrium_50"] = pd_range.equilibrium

        if pd_range.zone == "DISCOUNT":
            matched.append(f"Precio en zona DISCOUNT ({pd_range.current_position_pct:.1f}% del rango)")
            bullish_points += 15.0
        elif pd_range.zone == "PREMIUM":
            matched.append(f"Precio en zona PREMIUM ({pd_range.current_position_pct:.1f}% del rango)")
            bearish_points += 15.0
        else:
            unmatched.append("Precio en equilibrio (50%); relación riesgo/beneficio neutral")

    # Order Blocks proximity
    active_obs = [ob for ob in smc.order_blocks if ob.status == MitigationStatus.UNMITIGATED]
    evidence["unmitigated_obs_count"] = len(active_obs)

    # Check for nearby bullish OB below current price (within 3%)
    bullish_obs_near = [
        ob for ob in active_obs
        if ob.direction == SMCDirection.BULLISH
        and ob.top_price <= current_price
        and (current_price - ob.top_price) / current_price <= 0.035
    ]
    if bullish_obs_near:
        best_near_ob = max(bullish_obs_near, key=lambda x: x.quality_score)
        matched.append(
            f"Proximidad a Bullish Order Block activo [{best_near_ob.bottom_price:.2f} - {best_near_ob.top_price:.2f}] "
            f"(Score: {best_near_ob.quality_score:.0f})"
        )
        bullish_points += 15.0

    # Check for nearby bearish OB above current price (within 3%)
    bearish_obs_near = [
        ob for ob in active_obs
        if ob.direction == SMCDirection.BEARISH
        and ob.bottom_price >= current_price
        and (ob.bottom_price - current_price) / current_price <= 0.035
    ]
    if bearish_obs_near:
        best_near_ob = max(bearish_obs_near, key=lambda x: x.quality_score)
        matched.append(
            f"Proximidad a Bearish Order Block activo [{best_near_ob.bottom_price:.2f} - {best_near_ob.top_price:.2f}] "
            f"(Score: {best_near_ob.quality_score:.0f})"
        )
        bearish_points += 15.0

    # Fair Value Gaps
    unfilled_fvgs = [f for f in smc.fair_value_gaps if f.status != MitigationStatus.MITIGATED]
    evidence["unfilled_fvgs_count"] = len(unfilled_fvgs)

    # Recent BOS/CHOCH
    if smc.structure_breaks:
        last_brk = smc.structure_breaks[-1]
        bars_since_brk = len(bars) - 1 - last_brk.breaking_bar_index
        if bars_since_brk <= 8:
            matched.append(
                f"Ruptura estructural reciente: {last_brk.break_type.value} {last_brk.direction.value} "
                f"hace {bars_since_brk} barras"
            )
            if last_brk.direction == SMCDirection.BULLISH:
                bullish_points += 15.0
            else:
                bearish_points += 15.0

    # -------------------------------------------------------------
    # 4. Liquidity Intelligence & Sweeps
    # -------------------------------------------------------------
    liq = run_liquidity_analysis(symbol, interval, bars)

    if liq.sweeps:
        last_sw = liq.sweeps[-1]
        bars_since_sw = len(bars) - 1 - last_sw.sweep_bar_index
        if bars_since_sw <= 6:
            matched.append(
                f"Barrido de liquidez reciente ({last_sw.pool_type.value}) con rechazo en {last_sw.rejection_close:.2f}"
            )
            if last_sw.pool_type in (LiquidityType.EQL, LiquidityType.SSL, LiquidityType.PDL, LiquidityType.PWL):
                # Sell-side sweep -> Bullish reaction expected
                bullish_points += 20.0
            else:
                # Buy-side sweep -> Bearish reaction expected
                bearish_points += 20.0

    # -------------------------------------------------------------
    # 5. Composite Score & Direction Classification
    # -------------------------------------------------------------
    if bullish_points >= bearish_points and bullish_points >= 40.0:
        direction = SetupDirection.BULLISH
        score = min(100.0, bullish_points)
        invalidation = struct.last_swing_low if struct.last_swing_low else current_price * 0.96
        obs_text = (
            f"{symbol.upper()} presenta confluencia ALCISTA con score cuantitativo de {score:.0f}/100. "
            f"Factores clave: {'; '.join(matched[:3])}."
        )
        hypo_text = (
            f"HIPÓTESIS DE SWING ALCISTA: Proyección hacia objetivos superiores de liquidez. "
            f"Nivel de invalidación cuantitativo: Cierre por debajo de {invalidation:.2f}."
        )
    elif bearish_points > bullish_points and bearish_points >= 40.0:
        direction = SetupDirection.BEARISH
        score = min(100.0, bearish_points)
        invalidation = struct.last_swing_high if struct.last_swing_high else current_price * 1.04
        obs_text = (
            f"{symbol.upper()} presenta confluencia BAJISTA con score cuantitativo de {score:.0f}/100. "
            f"Factores clave: {'; '.join(matched[:3])}."
        )
        hypo_text = (
            f"HIPÓTESIS DE SWING BAJISTA: Proyección hacia objetivos inferiores de liquidez. "
            f"Nivel de invalidación cuantitativo: Cierre por encima de {invalidation:.2f}."
        )
    else:
        direction = SetupDirection.NEUTRAL
        score = max(bullish_points, bearish_points)
        invalidation = None
        obs_text = f"{symbol.upper()} en consolidación o confluencias mixtas (Score: {score:.0f}/100)."
        hypo_text = "Se recomienda permanecer al margen hasta resolución direccional clara."

    # Conviction
    if score >= 80.0:
        conviction = ConvictionLevel.HIGH
    elif score >= 60.0:
        conviction = ConvictionLevel.MODERATE
    else:
        conviction = ConvictionLevel.LOW

    return ScanOpportunity(
        symbol=symbol.upper(),
        market=market,
        interval=interval,
        direction=direction,
        conviction=conviction,
        score=round(score, 1),
        current_price=round(current_price, 4),
        matched_criteria=matched,
        unmatched_criteria=unmatched,
        evidence=evidence,
        invalidation_level=round(invalidation, 4) if invalidation else None,
        observation=obs_text,
        hypothesis=hypo_text,
        scanned_at=datetime.utcnow(),
    )
