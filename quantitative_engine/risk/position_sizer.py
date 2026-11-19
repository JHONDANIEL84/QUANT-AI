"""Position Sizing Engine — Fase 8 QUANT AI.

Calcula el tamaño óptimo de posición usando 4 métodos:
  1. Fixed Percent — % fijo del capital en riesgo
  2. Kelly Criterion — Fracción óptima según tasa de acierto e historial
  3. ATR-Based — Ajuste dinámico por volatilidad actual
  4. Fixed COP — Monto fijo definido por el operador

Restricciones:
  - Kelly fraccionado (mitad del Kelly completo) para control de drawdown
  - Riesgo máximo hard-cap: 5% del capital por operación
  - Todas las cantidades monetarias en COP
"""

from __future__ import annotations

import math
from typing import Optional

from quantitative_engine.risk.models import (
    PositionSizeRequest,
    PositionSizeResult,
    PositionSizingMethod,
    TradeDirection,
    RiskRating,
)


def _risk_rating(rr: Optional[float]) -> RiskRating:
    """Clasifica el riesgo según el ratio R:R (Recompensa/Riesgo)."""
    if rr is None:
        return RiskRating.MODERATE
    if rr >= 4.0:
        return RiskRating.VERY_LOW
    if rr >= 3.0:
        return RiskRating.LOW
    if rr >= 2.0:
        return RiskRating.MODERATE
    if rr >= 1.0:
        return RiskRating.HIGH
    return RiskRating.EXCESSIVE


def calculate_position_size(req: PositionSizeRequest) -> PositionSizeResult:
    """Calcula el tamaño óptimo de posición en COP.

    Args:
        req: PositionSizeRequest con parámetros del trade y del capital.

    Returns:
        PositionSizeResult con unidades, montos, R:R y contexto epistémico.

    Raises:
        ValueError: Si los parámetros de precio son incoherentes para la dirección.
    """
    capital = req.capital_cop
    entry = req.entry_price
    stop = req.stop_loss_price
    target = req.target_price
    direction = req.direction

    # --- Validar coherencia direccional ---
    if direction == TradeDirection.LONG and stop >= entry:
        raise ValueError(
            f"Para posición LONG el stop ({stop}) debe estar por debajo del precio de entrada ({entry})."
        )
    if direction == TradeDirection.SHORT and stop <= entry:
        raise ValueError(
            f"Para posición SHORT el stop ({stop}) debe estar por encima del precio de entrada ({entry})."
        )

    # --- Riesgo por unidad (en la moneda del activo) ---
    risk_per_unit = abs(entry - stop)

    # --- Calcular monto en riesgo (COP) según método ---
    method = req.method

    if method == PositionSizingMethod.FIXED_PERCENT:
        # Riesgo = capital × risk_percent%
        risk_amount_cop = capital * (req.risk_percent / 100.0)

    elif method == PositionSizingMethod.KELLY:
        # Kelly completo = (p * b - q) / b, donde b = avg_win/avg_loss
        # Usamos Half-Kelly para controlar drawdown
        p = req.win_rate or 0.5
        q = 1.0 - p
        b = req.avg_win_loss_ratio or 1.5

        kelly_full = (p * b - q) / b if b > 0 else 0.0
        half_kelly = max(0.0, min(kelly_full * 0.5, 0.05))  # Hard-cap 5%
        risk_amount_cop = capital * half_kelly

    elif method == PositionSizingMethod.ATR_BASED:
        # El stop dinámico = atr_multiplier × ATR; ajusta el riesgo real
        atr = req.atr_value or risk_per_unit
        dynamic_stop_distance = req.atr_multiplier * atr
        risk_amount_cop = capital * (req.risk_percent / 100.0)
        # Recalcula risk_per_unit con el stop dinámico ATR
        risk_per_unit = dynamic_stop_distance

    elif method == PositionSizingMethod.FIXED_COP:
        # Monto fijo en COP especificado por risk_percent como valor absoluto
        # Interpretación: risk_percent% del capital = monto fijo
        risk_amount_cop = capital * (req.risk_percent / 100.0)

    else:
        risk_amount_cop = capital * (req.risk_percent / 100.0)

    # Hard-cap: nunca arriesgar más del 5% del capital
    risk_amount_cop = min(risk_amount_cop, capital * 0.05)
    risk_amount_cop = max(risk_amount_cop, 0.01)

    # --- Convertir riesgo a unidades ---
    # Si el activo cotiza en USD, convertir COP a USD para calcular unidades
    usd_rate = req.usd_cop_rate
    if usd_rate and usd_rate > 0:
        risk_amount_native = risk_amount_cop / usd_rate  # en USD
    else:
        risk_amount_native = risk_amount_cop  # ya en COP

    # Número de unidades: Riesgo_nativo / riesgo_por_unidad
    if risk_per_unit <= 0:
        risk_per_unit = entry * 0.01  # Fallback: 1% del precio de entrada

    units = risk_amount_native / risk_per_unit
    units = max(units, 0.0)

    # --- Valor total de la posición ---
    position_value_native = units * entry
    if usd_rate and usd_rate > 0:
        position_value_cop = position_value_native * usd_rate
        position_value_usd: Optional[float] = round(position_value_native, 2)
    else:
        position_value_cop = position_value_native
        position_value_usd = None

    # Limitar a capital disponible (no apalancamiento por defecto)
    if position_value_cop > capital:
        units = units * (capital / position_value_cop)
        position_value_cop = units * entry if not usd_rate else units * entry * usd_rate
        if position_value_usd:
            position_value_usd = units * entry

    # Riesgo real post-ajuste
    actual_risk_cop = units * risk_per_unit if not (usd_rate and usd_rate > 0) else units * risk_per_unit * usd_rate
    actual_risk_pct = (actual_risk_cop / capital) * 100.0 if capital > 0 else 0.0

    # --- R:R ---
    rr: Optional[float] = None
    if target is not None:
        reward_per_unit = abs(target - entry)
        if risk_per_unit > 0:
            rr = round(reward_per_unit / risk_per_unit, 2)

    rating = _risk_rating(rr)

    # --- Texto epistémico ---
    obs = (
        f"Cálculo de posición ({method.value}) sobre capital de "
        f"COP ${capital:,.0f}. Entrada: {entry:.4f} | Stop: {stop:.4f} | "
        f"Riesgo por unidad: {risk_per_unit:.4f}. "
        f"Unidades calculadas: {units:.4f} ({position_value_cop:,.0f} COP en posición). "
        f"Riesgo real: {actual_risk_cop:,.0f} COP ({actual_risk_pct:.2f}% del capital)."
    )

    if rr is not None:
        hypo = (
            f"HIPÓTESIS: Si el precio alcanza el objetivo ({target:.4f}), "
            f"la operación produce un resultado de R:R {rr:.2f} "
            f"({(units * abs((target or entry) - entry)):,.0f} COP bruto estimado). "
            f"Invalidación cuantitativa: Cierre {'por debajo' if direction == TradeDirection.LONG else 'por encima'} "
            f"de {stop:.4f}."
        )
    else:
        hypo = (
            f"Hipótesis incompleta: No se definió precio objetivo (take profit). "
            f"Define el target para calcular R:R y validar la asimetría de la operación. "
            f"Invalidación: precio {'por debajo' if direction == TradeDirection.LONG else 'por encima'} de {stop:.4f}."
        )

    return PositionSizeResult(
        method=method,
        direction=direction,
        units=round(units, 6),
        position_value_cop=round(position_value_cop, 2),
        position_value_usd=round(position_value_usd, 2) if position_value_usd else None,
        risk_amount_cop=round(actual_risk_cop, 2),
        risk_percent_actual=round(actual_risk_pct, 4),
        entry_price=entry,
        stop_loss_price=stop,
        target_price=target,
        risk_reward_ratio=rr,
        risk_rating=rating,
        observation=obs,
        hypothesis=hypo,
    )
