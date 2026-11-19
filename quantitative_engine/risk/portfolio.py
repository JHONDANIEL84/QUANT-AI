"""Portfolio Simulator — Fase 8 QUANT AI.

Simulador de portafolio en COP para backtesting y paper trading.
Registra operaciones, actualiza equity y calcula estadísticas en tiempo real.

Principios:
  - Capital inicial en COP (Pesos Colombianos)
  - Comisiones configurables por operación
  - Estadísticas: Win Rate, Profit Factor, Expectancy, Sharpe, Max DD
  - Separación observación/hipótesis en cada estado del portafolio
"""

from __future__ import annotations

import numpy as np
from datetime import datetime
from typing import List, Optional, Dict

from quantitative_engine.risk.models import (
    PortfolioTrade,
    PortfolioState,
    TradeDirection,
)
from quantitative_engine.risk.drawdown import calculate_drawdown_metrics


class PortfolioSimulator:
    """Simulador de portafolio cuantitativo en COP.

    Uso:
        sim = PortfolioSimulator(initial_capital_cop=50_000_000)
        sim.open_trade(symbol="BTCUSDT", direction="long", ...)
        sim.close_trade(symbol="BTCUSDT", exit_price=...)
        state = sim.get_state()
    """

    def __init__(
        self,
        initial_capital_cop: float,
        commission_pct: float = 0.001,  # 0.1% por operación (ida y vuelta = 0.2%)
    ) -> None:
        if initial_capital_cop <= 0:
            raise ValueError("El capital inicial debe ser mayor a cero.")

        self._initial_capital = initial_capital_cop
        self._cash = initial_capital_cop
        self._commission_pct = commission_pct
        self._open: Dict[str, PortfolioTrade] = {}
        self._closed: List[PortfolioTrade] = []
        self._equity_curve: List[float] = [initial_capital_cop]

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def open_trade(
        self,
        symbol: str,
        direction: TradeDirection,
        entry_price: float,
        units: float,
        entry_date: Optional[datetime] = None,
        stop_loss_price: Optional[float] = None,
        risk_amount_cop: Optional[float] = None,
        usd_cop_rate: Optional[float] = None,
    ) -> PortfolioTrade:
        """Registra la apertura de una posición.

        Args:
            symbol: Símbolo del activo (ej. 'BTCUSDT', 'NVDA').
            direction: LONG o SHORT.
            entry_price: Precio de entrada en la moneda nativa del activo.
            units: Número de unidades a adquirir.
            entry_date: Fecha/hora de entrada (UTC); default = ahora.
            stop_loss_price: Precio de invalidación (stop loss).
            risk_amount_cop: Monto en riesgo en COP para cálculo de R-múltiplos.
            usd_cop_rate: TRM si el activo cotiza en USD.

        Returns:
            PortfolioTrade recién creado.

        Raises:
            ValueError: Si ya existe posición abierta para ese símbolo o si el capital es insuficiente.
        """
        if symbol in self._open:
            raise ValueError(f"Ya existe posición abierta para {symbol}. Ciérrela antes de abrir una nueva.")

        # Calcular valor de la posición en COP
        value_native = units * entry_price
        value_cop = value_native * usd_cop_rate if usd_cop_rate else value_native
        commission_cop = value_cop * self._commission_pct

        if value_cop + commission_cop > self._cash:
            raise ValueError(
                f"Capital insuficiente: se requieren COP ${value_cop + commission_cop:,.0f} "
                f"pero solo hay COP ${self._cash:,.0f} disponibles."
            )

        self._cash -= value_cop + commission_cop

        trade = PortfolioTrade(
            symbol=symbol,
            direction=direction,
            entry_date=entry_date or datetime.utcnow(),
            entry_price=entry_price,
            units=units,
            commission_cop=commission_cop,
            stop_loss_price=stop_loss_price,
            risk_amount_cop=risk_amount_cop,
        )
        self._open[symbol] = trade
        self._update_equity_curve(usd_cop_rate=usd_cop_rate)
        return trade

    def close_trade(
        self,
        symbol: str,
        exit_price: float,
        exit_date: Optional[datetime] = None,
        usd_cop_rate: Optional[float] = None,
    ) -> PortfolioTrade:
        """Cierra una posición abierta y registra el P&L.

        Args:
            symbol: Símbolo del activo a cerrar.
            exit_price: Precio de cierre en moneda nativa.
            exit_date: Fecha/hora de cierre; default = ahora.
            usd_cop_rate: TRM si el activo cotiza en USD.

        Returns:
            PortfolioTrade cerrado con P&L calculado.

        Raises:
            KeyError: Si no existe posición abierta para ese símbolo.
        """
        if symbol not in self._open:
            raise KeyError(f"No hay posición abierta para {symbol}.")

        trade = self._open.pop(symbol)
        trade.exit_date = exit_date or datetime.utcnow()
        trade.exit_price = exit_price

        # P&L bruto en la moneda nativa
        if trade.direction == TradeDirection.LONG:
            pnl_native = (exit_price - trade.entry_price) * trade.units
        else:
            pnl_native = (trade.entry_price - exit_price) * trade.units

        # Convertir a COP
        pnl_cop = pnl_native * usd_cop_rate if usd_cop_rate else pnl_native
        exit_commission = trade.units * exit_price * (usd_cop_rate or 1.0) * self._commission_pct
        pnl_cop -= exit_commission
        trade.commission_cop += exit_commission

        # Recuperar valor de la posición
        exit_value_cop = trade.units * exit_price * (usd_cop_rate or 1.0)
        self._cash += exit_value_cop + pnl_cop  # = cash + position_value + net_gain

        # Registrar resultados
        trade.pnl_cop = round(pnl_cop, 2)
        initial_value = trade.units * trade.entry_price * (usd_cop_rate or 1.0)
        trade.pnl_percent = round((pnl_cop / initial_value) * 100.0, 4) if initial_value > 0 else 0.0
        trade.is_winner = pnl_cop > 0

        # R-múltiplo
        if trade.risk_amount_cop and trade.risk_amount_cop > 0:
            trade.r_multiple = round(pnl_cop / trade.risk_amount_cop, 3)

        self._closed.append(trade)
        self._update_equity_curve(usd_cop_rate=usd_cop_rate)
        return trade

    def mark_to_market(
        self,
        prices: Dict[str, float],
        usd_cop_rate: Optional[float] = None,
    ) -> float:
        """Actualiza el valor unrealized de las posiciones abiertas.

        Args:
            prices: Diccionario {symbol: current_price_native}.
            usd_cop_rate: TRM si las posiciones cotizan en USD.

        Returns:
            Equity total actual en COP (realizado + no realizado).
        """
        unrealized = 0.0
        for symbol, trade in self._open.items():
            current_price = prices.get(symbol, trade.entry_price)
            if trade.direction == TradeDirection.LONG:
                unreal_native = (current_price - trade.entry_price) * trade.units
            else:
                unreal_native = (trade.entry_price - current_price) * trade.units
            unrealized += unreal_native * (usd_cop_rate or 1.0)

        equity = self._cash + unrealized
        self._equity_curve.append(round(equity, 2))
        return round(equity, 2)

    def get_state(self) -> PortfolioState:
        """Retorna el estado actual del portafolio con todas las estadísticas."""
        closed = self._closed
        n_total = len(closed)
        winners = [t for t in closed if t.is_winner]
        losers = [t for t in closed if not t.is_winner]

        n_win = len(winners)
        n_loss = len(losers)
        win_rate = n_win / n_total if n_total > 0 else 0.0

        avg_win = float(np.mean([t.pnl_cop for t in winners])) if winners else 0.0
        avg_loss = float(np.mean([abs(t.pnl_cop) for t in losers])) if losers else 0.0

        gross_profit = sum(t.pnl_cop for t in winners if t.pnl_cop)
        gross_loss = sum(abs(t.pnl_cop) for t in losers if t.pnl_cop)
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        # Max Drawdown
        max_dd_pct = 0.0
        if len(self._equity_curve) >= 2:
            try:
                dd_metrics = calculate_drawdown_metrics(self._equity_curve)
                max_dd_pct = dd_metrics.max_drawdown_pct
            except Exception:
                pass

        # Sharpe Ratio simplificado (sobre los retornos de las operaciones cerradas)
        sharpe = 0.0
        if len(closed) >= 2:
            returns = np.array([t.pnl_percent for t in closed if t.pnl_percent is not None])
            if len(returns) > 1:
                mean_r = np.mean(returns)
                std_r = np.std(returns, ddof=1)
                sharpe = round(float(mean_r / std_r * np.sqrt(252)) if std_r > 0 else 0.0, 4)

        current_equity = self._cash + sum(
            # Aproximación: posiciones abiertas valoradas al precio de entrada
            t.units * t.entry_price for t in self._open.values()
        )

        obs = (
            f"Portafolio simulado QUANT AI en COP. Capital inicial: ${self._initial_capital:,.0f} COP. "
            f"Equity actual: ${current_equity:,.0f} COP. "
            f"Operaciones cerradas: {n_total} (Ganadoras: {n_win}, Perdedoras: {n_loss}). "
            f"Win Rate: {win_rate:.1%} | Profit Factor: {profit_factor:.2f} | Max DD: {max_dd_pct:.2f}%."
        )

        return PortfolioState(
            initial_capital_cop=self._initial_capital,
            current_equity_cop=round(current_equity, 2),
            cash_cop=round(self._cash, 2),
            realized_pnl_cop=round(sum(t.pnl_cop for t in closed if t.pnl_cop), 2),
            total_trades=n_total,
            winning_trades=n_win,
            losing_trades=n_loss,
            win_rate=round(win_rate, 4),
            avg_win_cop=round(avg_win, 2),
            avg_loss_cop=round(avg_loss, 2),
            profit_factor=round(min(profit_factor, 9999.0), 4),
            expectancy_cop=round(expectancy, 2),
            max_drawdown_pct=round(max_dd_pct, 4),
            sharpe_ratio=sharpe,
            open_positions=list(self._open.values()),
            closed_trades=closed[-50:],  # Últimas 50 para limitar payload
            equity_curve=self._equity_curve[-500:],  # Últimos 500 puntos
            observation=obs,
        )

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _update_equity_curve(self, usd_cop_rate: Optional[float] = None) -> None:
        """Agrega punto de equity (solo con cash + posiciones al precio de entrada)."""
        open_value = sum(
            t.units * t.entry_price * (usd_cop_rate or 1.0)
            for t in self._open.values()
        )
        equity = self._cash + open_value
        self._equity_curve.append(round(equity, 2))
