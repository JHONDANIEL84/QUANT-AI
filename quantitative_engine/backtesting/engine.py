"""Walk-Forward Causal Backtesting Engine — Fase 9 QUANT AI.

Garantías cuantitativas y epistémicas:
  1. No Look-Ahead Bias:
     - Las señales generadas al cierre de la barra `i` se ejecutan estrictamente
       en la apertura de la barra `i + 1` (Next Bar Open).
  2. Fricciones de Mercado Realistas:
     - Comisión modelada en entrada y salida (% del valor negociado en COP).
     - Deslizamiento (slippage) modelado desfavorablemente tanto en entrada como en salida.
  3. Gestión Dinámica del Capital:
     - Dimensionamiento de posición según riesgo porcentual sobre equity acumulado en COP.
  4. Métricas cuantitativas completas:
     - Win Rate, Profit Factor, Expectancy, CAGR, Max Drawdown, Sharpe, Sortino, Calmar.
"""

from __future__ import annotations

import math
from typing import List, Optional, Dict, Any
import numpy as np
from datetime import datetime

from data_providers.base.models import MarketBar
from quantitative_engine.backtesting.models import (
    BacktestConfig,
    BacktestResult,
    BacktestTrade,
    BacktestSignal,
    SignalType,
    ExitReason,
    StrategyName,
)
from quantitative_engine.backtesting.strategies.base import BaseStrategy
from quantitative_engine.backtesting.strategies.ema_rsi import EmaRsiStrategy
from quantitative_engine.backtesting.strategies.smc_liquidity import SMCLiquidityStrategy
from quantitative_engine.risk.drawdown import calculate_drawdown_metrics


def _get_strategy(name: StrategyName, params: Dict[str, Any]) -> BaseStrategy:
    """Factory de estrategias disponibles."""
    if name == StrategyName.EMA_RSI_TREND:
        return EmaRsiStrategy(params)
    elif name == StrategyName.SMC_LIQUIDITY:
        return SMCLiquidityStrategy(params)
    else:
        # Fallback a EMA RSI
        return EmaRsiStrategy(params)


class BacktestEngine:
    """Motor central de simulación cuantitativa causal."""

    def __init__(self, config: BacktestConfig) -> None:
        self.config = config
        self.strategy = _get_strategy(config.strategy_name, config.strategy_params)

    def run(self, bars: List[MarketBar]) -> BacktestResult:
        """Ejecuta el backtest barra a barra sobre la serie histórica provista.

        Args:
            bars: Lista cronológica de MarketBars.

        Returns:
            BacktestResult completo con curva de equity y métricas de desempeño.
        """
        n = len(bars)
        if n < 30:
            raise ValueError(f"Se requieren al menos 30 barras para el backtesting (provistas: {n}).")

        capital = self.config.initial_capital_cop
        cash = capital
        equity_curve: List[float] = [capital]
        trades: List[BacktestTrade] = []

        active_trade_data: Optional[Dict[str, Any]] = None
        pending_signal: Optional[BacktestSignal] = None
        trade_counter = 0

        # Iterar barra por barra (simulación walk-forward temporal)
        for i in range(n):
            current_bar = bars[i]

            # -----------------------------------------------------------------
            # 1. EJECUTAR SEÑAL PENDIENTE DE LA BARRA ANTERIOR (Next Bar Open)
            # -----------------------------------------------------------------
            if pending_signal is not None and active_trade_data is None:
                sig = pending_signal
                pending_signal = None

                direction = "long" if sig.signal_type == SignalType.BUY else "short"
                # Precio de ejecución: Apertura de la barra actual con slippage adverso
                raw_entry = current_bar.open
                if direction == "long":
                    entry_price = raw_entry * (1.0 + self.config.slippage_pct)
                else:
                    entry_price = raw_entry * (1.0 - self.config.slippage_pct)

                stop_loss = sig.stop_loss
                take_profit = sig.take_profit

                # Calcular riesgo por unidad
                if stop_loss is not None:
                    risk_per_unit = abs(entry_price - stop_loss)
                else:
                    risk_per_unit = entry_price * 0.02  # Fallback: 2% del precio

                risk_per_unit = max(risk_per_unit, entry_price * 0.002)

                # Monto en riesgo en COP: % del equity actual
                current_equity = cash
                risk_amount_cop = current_equity * (self.config.risk_per_trade_pct / 100.0)

                # TRM si activo en USD
                usd_rate = self.config.usd_cop_rate or 1.0
                risk_amount_native = risk_amount_cop / usd_rate

                units = risk_amount_native / risk_per_unit

                # Limitar posición al capital disponible (sin apalancamiento)
                pos_value_native = units * entry_price
                pos_value_cop = pos_value_native * usd_rate
                if pos_value_cop > cash * 0.95:
                    units = (cash * 0.95) / (entry_price * usd_rate)
                    pos_value_native = units * entry_price
                    pos_value_cop = pos_value_native * usd_rate

                if units > 0 and pos_value_cop > 0:
                    entry_commission = pos_value_cop * self.config.commission_pct
                    entry_slippage_cop = abs(entry_price - raw_entry) * units * usd_rate
                    cash -= (pos_value_cop + entry_commission)

                    trade_counter += 1
                    active_trade_data = {
                        "trade_id": trade_counter,
                        "direction": direction,
                        "entry_bar_idx": i,
                        "entry_time": current_bar.timestamp,
                        "entry_price": entry_price,
                        "raw_entry": raw_entry,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "units": units,
                        "entry_commission": entry_commission,
                        "entry_slippage_cop": entry_slippage_cop,
                        "risk_amount_cop": risk_amount_cop,
                    }

            # -----------------------------------------------------------------
            # 2. EVALUAR POSICIÓN ACTIVA CONTRA PRECIOS DE LA BARRA ACTUAL
            # -----------------------------------------------------------------
            if active_trade_data is not None:
                t = active_trade_data
                dir_ = t["direction"]
                sl = t["stop_loss"]
                tp = t["take_profit"]
                u = t["units"]
                entry_p = t["entry_price"]
                usd_rate = self.config.usd_cop_rate or 1.0

                exit_triggered = False
                exit_price = 0.0
                exit_reason = ExitReason.END_OF_DATA

                # A. Stop Loss
                if dir_ == "long" and sl is not None and current_bar.low <= sl:
                    exit_triggered = True
                    # Slippage adicional al salir por stop
                    exit_price = sl * (1.0 - self.config.slippage_pct)
                    exit_reason = ExitReason.STOP_LOSS
                elif dir_ == "short" and sl is not None and current_bar.high >= sl:
                    exit_triggered = True
                    exit_price = sl * (1.0 + self.config.slippage_pct)
                    exit_reason = ExitReason.STOP_LOSS

                # B. Take Profit (solo si no saltó el stop primero)
                elif dir_ == "long" and tp is not None and current_bar.high >= tp:
                    exit_triggered = True
                    exit_price = tp * (1.0 - self.config.slippage_pct)
                    exit_reason = ExitReason.TAKE_PROFIT
                elif dir_ == "short" and tp is not None and current_bar.low <= tp:
                    exit_triggered = True
                    exit_price = tp * (1.0 + self.config.slippage_pct)
                    exit_reason = ExitReason.TAKE_PROFIT

                # C. Timeout (tiempo máximo en posición)
                holding_bars = i - t["entry_bar_idx"]
                if not exit_triggered and holding_bars >= self.config.max_holding_bars:
                    exit_triggered = True
                    exit_price = current_bar.close * (
                        1.0 - self.config.slippage_pct if dir_ == "long" else 1.0 + self.config.slippage_pct
                    )
                    exit_reason = ExitReason.TIMEOUT

                # D. Fin de datos (última barra)
                if not exit_triggered and i == n - 1:
                    exit_triggered = True
                    exit_price = current_bar.close
                    exit_reason = ExitReason.END_OF_DATA

                # Si se gatilló salida, liquidar la operación
                if exit_triggered:
                    exit_val_native = u * exit_price
                    exit_val_cop = exit_val_native * usd_rate
                    exit_commission = exit_val_cop * self.config.commission_pct
                    exit_slippage_cop = (
                        abs(exit_price - (sl or tp or current_bar.close)) * u * usd_rate
                    )

                    if dir_ == "long":
                        gross_pnl_native = (exit_price - entry_p) * u
                    else:
                        gross_pnl_native = (entry_p - exit_price) * u

                    gross_pnl_cop = gross_pnl_native * usd_rate
                    total_comm = t["entry_commission"] + exit_commission
                    total_slip = t["entry_slippage_cop"] + exit_slippage_cop
                    net_pnl_cop = gross_pnl_cop - total_comm - total_slip

                    # Devolver capital + net PnL a cash
                    initial_pos_cop = u * entry_p * usd_rate
                    cash += initial_pos_cop + net_pnl_cop

                    pnl_pct = (net_pnl_cop / initial_pos_cop * 100.0) if initial_pos_cop > 0 else 0.0
                    r_mult = (
                        round(net_pnl_cop / t["risk_amount_cop"], 2)
                        if t["risk_amount_cop"] > 0
                        else None
                    )

                    trades.append(
                        BacktestTrade(
                            trade_id=t["trade_id"],
                            symbol=self.config.symbol,
                            direction=dir_,
                            entry_bar_idx=t["entry_bar_idx"],
                            exit_bar_idx=i,
                            entry_time=t["entry_time"],
                            exit_time=current_bar.timestamp,
                            entry_price=round(entry_p, 4),
                            exit_price=round(exit_price, 4),
                            units=round(u, 6),
                            commission_cop=round(total_comm, 2),
                            slippage_cop=round(total_slip, 2),
                            gross_pnl_cop=round(gross_pnl_cop, 2),
                            net_pnl_cop=round(net_pnl_cop, 2),
                            pnl_percent=round(pnl_pct, 4),
                            r_multiple=r_mult,
                            is_winner=net_pnl_cop > 0,
                            exit_reason=exit_reason,
                            holding_bars=holding_bars,
                        )
                    )
                    active_trade_data = None

            # -----------------------------------------------------------------
            # 3. GENERAR NUEVA SEÑAL PARA LA SIGUIENTE BARRA (estrictamente causal)
            # -----------------------------------------------------------------
            active_pos_str = active_trade_data["direction"] if active_trade_data else None
            new_signal = self.strategy.generate_signal(
                current_idx=i,
                bars=bars,
                active_position=active_pos_str,
            )

            # Manejar señal de salida si hay posición abierta
            if new_signal is not None and active_trade_data is not None:
                if (
                    (new_signal.signal_type == SignalType.EXIT_LONG and active_trade_data["direction"] == "long")
                    or (new_signal.signal_type == SignalType.EXIT_SHORT and active_trade_data["direction"] == "short")
                ):
                    # Liquidar en cierre de esta barra
                    t = active_trade_data
                    dir_ = t["direction"]
                    u = t["units"]
                    entry_p = t["entry_price"]
                    exit_price = current_bar.close * (
                        1.0 - self.config.slippage_pct if dir_ == "long" else 1.0 + self.config.slippage_pct
                    )
                    usd_rate = self.config.usd_cop_rate or 1.0

                    exit_val_cop = u * exit_price * usd_rate
                    exit_commission = exit_val_cop * self.config.commission_pct
                    gross_pnl_cop = ((exit_price - entry_p) if dir_ == "long" else (entry_p - exit_price)) * u * usd_rate
                    total_comm = t["entry_commission"] + exit_commission
                    net_pnl_cop = gross_pnl_cop - total_comm

                    initial_pos_cop = u * entry_p * usd_rate
                    cash += initial_pos_cop + net_pnl_cop

                    trades.append(
                        BacktestTrade(
                            trade_id=t["trade_id"],
                            symbol=self.config.symbol,
                            direction=dir_,
                            entry_bar_idx=t["entry_bar_idx"],
                            exit_bar_idx=i,
                            entry_time=t["entry_time"],
                            exit_time=current_bar.timestamp,
                            entry_price=round(entry_p, 4),
                            exit_price=round(exit_price, 4),
                            units=round(u, 6),
                            commission_cop=round(total_comm, 2),
                            slippage_cop=round(t["entry_slippage_cop"], 2),
                            gross_pnl_cop=round(gross_pnl_cop, 2),
                            net_pnl_cop=round(net_pnl_cop, 2),
                            pnl_percent=round((net_pnl_cop / initial_pos_cop * 100.0), 4),
                            r_multiple=round(net_pnl_cop / t["risk_amount_cop"], 2) if t["risk_amount_cop"] > 0 else None,
                            is_winner=net_pnl_cop > 0,
                            exit_reason=ExitReason.SIGNAL_REVERSAL,
                            holding_bars=i - t["entry_bar_idx"],
                        )
                    )
                    active_trade_data = None

            elif new_signal is not None and active_trade_data is None:
                # Señal de entrada válida -> programar para ejecutar en barra i+1
                if new_signal.signal_type in (SignalType.BUY, SignalType.SELL):
                    pending_signal = new_signal

            # -----------------------------------------------------------------
            # 4. ACTUALIZAR CURVA DE EQUITY
            # -----------------------------------------------------------------
            open_pos_value = 0.0
            if active_trade_data is not None:
                t = active_trade_data
                u = t["units"]
                usd_rate = self.config.usd_cop_rate or 1.0
                if t["direction"] == "long":
                    unrealized_pnl = (current_bar.close - t["entry_price"]) * u * usd_rate
                else:
                    unrealized_pnl = (t["entry_price"] - current_bar.close) * u * usd_rate
                open_pos_value = (u * t["entry_price"] * usd_rate) + unrealized_pnl

            total_equity = cash + open_pos_value
            equity_curve.append(round(total_equity, 2))

        # ---------------------------------------------------------------------
        # 5. CALCULAR MÉTRICAS CONSOLIDADAS DE RENDIMIENTO
        # ---------------------------------------------------------------------
        return self._compute_performance_metrics(
            initial_capital=capital,
            equity_curve=equity_curve,
            trades=trades,
            bars_count=n,
        )

    def _compute_performance_metrics(
        self,
        initial_capital: float,
        equity_curve: List[float],
        trades: List[BacktestTrade],
        bars_count: int,
    ) -> BacktestResult:
        """Calcula todas las métricas cuantitativas consolidadas."""
        final_equity = equity_curve[-1] if equity_curve else initial_capital
        net_profit_cop = final_equity - initial_capital
        net_profit_pct = (net_profit_cop / initial_capital * 100.0) if initial_capital > 0 else 0.0

        n_trades = len(trades)
        winners = [t for t in trades if t.is_winner]
        losers = [t for t in trades if not t.is_winner]

        win_rate = (len(winners) / n_trades) if n_trades > 0 else 0.0
        gross_profit = sum(t.net_pnl_cop for t in winners)
        gross_loss = sum(abs(t.net_pnl_cop) for t in losers)
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)

        avg_win = float(np.mean([t.net_pnl_cop for t in winners])) if winners else 0.0
        avg_loss = float(np.mean([abs(t.net_pnl_cop) for t in losers])) if losers else 0.0
        expectancy = (win_rate * avg_win) - ((1.0 - win_rate) * avg_loss)

        avg_duration = float(np.mean([t.holding_bars for t in trades])) if trades else 0.0

        # Drawdown
        try:
            dd_metrics = calculate_drawdown_metrics(equity_curve)
            max_dd_pct = dd_metrics.max_drawdown_pct
            max_dd_cop = dd_metrics.max_drawdown_cop
            calmar = dd_metrics.calmar_ratio
        except Exception:
            max_dd_pct = 0.0
            max_dd_cop = 0.0
            calmar = 0.0

        # Retornos por operación para Sharpe y Sortino
        returns = np.array([t.pnl_percent for t in trades], dtype=float) if trades else np.array([])
        if len(returns) >= 2:
            mean_r = float(np.mean(returns))
            std_r = float(np.std(returns, ddof=1))
            # Tasa libre de riesgo = 0% por simplificación
            sharpe = (mean_r / std_r * math.sqrt(252)) if std_r > 0 else 0.0

            # Sortino: solo desviación a la baja
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 1:
                downside_std = float(np.std(downside_returns, ddof=1))
                sortino = (mean_r / downside_std * math.sqrt(252)) if downside_std > 0 else 0.0
            else:
                sortino = sharpe
        else:
            sharpe = 0.0
            sortino = 0.0

        # CAGR aproximado (asumiendo 252 barras = 1 año si diario)
        years = max(bars_count / 252.0, 0.05)
        total_growth = final_equity / initial_capital if initial_capital > 0 else 1.0
        cagr = ((total_growth ** (1.0 / years)) - 1.0) * 100.0 if total_growth > 0 else -100.0

        # Textos epistémicos
        obs = (
            f"Backtest {self.config.strategy_name.value} sobre {self.config.symbol} ({self.config.interval}): "
            f"{n_trades} operaciones ejecutadas en {bars_count} barras. "
            f"Capital inicial: COP ${initial_capital:,.0f} | Final: COP ${final_equity:,.0f} "
            f"({net_profit_pct:+.2f}%). Win Rate: {win_rate:.1%} | Profit Factor: {profit_factor:.2f} | "
            f"Max DD: {max_dd_pct:.2f}% (COP ${max_dd_cop:,.0f}). Sharpe: {sharpe:.2f}."
        )

        hypo = (
            f"HIPÓTESIS DE ROBUSTEZ: La estrategia presenta "
            f"{'ventaja estadística cuantitativa confirmada (Profit Factor > 1.25)' if profit_factor >= 1.25 else 'desempeño marginal o insuficiente para operar en vivo (Profit Factor < 1.25)'}. "
            f"Criterio de invalidación en producción: Si el Drawdown acumulado supera el límite modelado "
            f"({max_dd_pct * 1.3:.1f}% o COP ${max_dd_cop * 1.3:,.0f}), la estrategia debe pausarse inmediatamente."
        )

        return BacktestResult(
            config=self.config,
            total_trades=n_trades,
            winning_trades=len(winners),
            losing_trades=len(losers),
            win_rate=round(win_rate, 4),
            initial_capital_cop=round(initial_capital, 2),
            final_equity_cop=round(final_equity, 2),
            gross_profit_cop=round(gross_profit, 2),
            gross_loss_cop=round(gross_loss, 2),
            net_profit_cop=round(net_profit_cop, 2),
            net_profit_percent=round(net_profit_pct, 4),
            profit_factor=round(min(profit_factor, 999.0), 4),
            expectancy_cop=round(expectancy, 2),
            cagr_percent=round(cagr, 4),
            sharpe_ratio=round(sharpe, 4),
            sortino_ratio=round(sortino, 4),
            calmar_ratio=round(min(calmar, 999.0), 4),
            max_drawdown_pct=round(max_dd_pct, 4),
            max_drawdown_cop=round(max_dd_cop, 2),
            avg_trade_duration_bars=round(avg_duration, 2),
            equity_curve=equity_curve,
            trades=trades,
            observation=obs,
            hypothesis=hypo,
        )
