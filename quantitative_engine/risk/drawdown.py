"""Drawdown Calculator — Fase 8 QUANT AI.

Calcula métricas de riesgo históricas sobre una curva de equity:
  - Máximo Drawdown (absoluto y %)
  - Drawdown actual
  - Duración del drawdown más largo
  - Recovery Factor y Calmar Ratio

Principio causal: las métricas se calculan estrictamente sobre datos históricos
confirmados (sin look-ahead bias).
"""

from __future__ import annotations

import numpy as np
from typing import List

from quantitative_engine.risk.models import DrawdownMetrics


def calculate_drawdown_metrics(
    equity_curve: List[float],
    periods_per_year: int = 252,
) -> DrawdownMetrics:
    """Calcula métricas de drawdown sobre la curva de equity.

    Args:
        equity_curve: Lista de valores de equity en COP (cronológica).
        periods_per_year: Número de periodos por año para Calmar Ratio
                          (252 = días hábiles, 52 = semanas, 12 = meses).

    Returns:
        DrawdownMetrics con todas las métricas de riesgo históricas.

    Raises:
        ValueError: Si la curva tiene menos de 2 puntos.
    """
    if len(equity_curve) < 2:
        raise ValueError("La curva de equity debe tener al menos 2 puntos de datos.")

    eq = np.array(equity_curve, dtype=float)
    n = len(eq)

    # --- Peak y Drawdown running ---
    running_max = np.maximum.accumulate(eq)
    dd_abs = running_max - eq                     # Drawdown absoluto por periodo
    dd_pct = np.where(running_max > 0, dd_abs / running_max * 100.0, 0.0)

    # --- Máximo Drawdown ---
    max_dd_pct = float(np.max(dd_pct))
    max_dd_cop = float(np.max(dd_abs))
    max_dd_end_idx = int(np.argmax(dd_pct))
    # Buscar el peak antes del end_idx
    max_dd_start_idx = int(np.argmax(eq[:max_dd_end_idx + 1])) if max_dd_end_idx > 0 else 0

    # --- Drawdown actual (desde el último peak hasta el último punto) ---
    current_peak = float(np.max(eq))
    current_equity = float(eq[-1])
    current_dd_cop = max(0.0, current_peak - current_equity)
    current_dd_pct = (current_dd_cop / current_peak * 100.0) if current_peak > 0 else 0.0

    # --- Duración del drawdown más largo ---
    # Buscar el periodo más largo por debajo del peak anterior
    in_drawdown = dd_pct > 0
    max_duration = 0
    current_duration = 0
    for d in in_drawdown:
        if d:
            current_duration += 1
            max_duration = max(max_duration, current_duration)
        else:
            current_duration = 0

    # --- Recovery Factor ---
    total_return = eq[-1] - eq[0]
    recovery_factor = (total_return / max_dd_cop) if max_dd_cop > 0 else float("inf")

    # --- Calmar Ratio = CAGR / Max Drawdown% ---
    if n > 1:
        total_return_pct = (eq[-1] / eq[0] - 1.0) if eq[0] > 0 else 0.0
        years = n / periods_per_year
        cagr = ((1.0 + total_return_pct) ** (1.0 / years) - 1.0) if years > 0 else 0.0
    else:
        cagr = 0.0

    calmar = (cagr / (max_dd_pct / 100.0)) if max_dd_pct > 0 else float("inf")

    return DrawdownMetrics(
        max_drawdown_pct=round(max_dd_pct, 4),
        max_drawdown_cop=round(max_dd_cop, 2),
        max_drawdown_start_idx=max_dd_start_idx,
        max_drawdown_end_idx=max_dd_end_idx,
        current_drawdown_pct=round(current_dd_pct, 4),
        current_drawdown_cop=round(current_dd_cop, 2),
        longest_drawdown_bars=max_duration,
        recovery_factor=round(recovery_factor, 4) if recovery_factor != float("inf") else 9999.0,
        calmar_ratio=round(calmar, 4) if calmar != float("inf") else 9999.0,
        peak_equity_cop=round(current_peak, 2),
        trough_equity_cop=round(float(np.min(eq)), 2),
    )
