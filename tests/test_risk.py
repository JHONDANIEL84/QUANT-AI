"""Tests unitarios para Gestión del Riesgo y Portafolio — Fase 8 QUANT AI.

Cobertura:
  - Cálculo de tamaño de posición (4 métodos)
  - Validaciones de coherencia (stop arriba/abajo del entry)
  - R:R y rating de riesgo
  - Métricas de drawdown (max DD, actual, duración, Calmar)
  - Simulador de portafolio (apertura, cierre, P&L, estadísticas)
"""

import pytest
import math
from datetime import datetime, timezone

from quantitative_engine.risk.models import (
    PositionSizeRequest,
    PositionSizingMethod,
    TradeDirection,
    RiskRating,
)
from quantitative_engine.risk.position_sizer import calculate_position_size
from quantitative_engine.risk.drawdown import calculate_drawdown_metrics
from quantitative_engine.risk.portfolio import PortfolioSimulator


# ---------------------------------------------------------------------------
# 1. Position Sizing — Fixed Percent
# ---------------------------------------------------------------------------

class TestFixedPercentSizing:

    def test_basic_long_position(self):
        """Posición LONG básica: capital 50M COP, 1% riesgo, BTC a 300M COP."""
        req = PositionSizeRequest(
            capital_cop=50_000_000.0,
            entry_price=300_000_000.0,   # ~BTC en COP
            stop_loss_price=285_000_000.0,
            target_price=330_000_000.0,
            risk_percent=1.0,
            method=PositionSizingMethod.FIXED_PERCENT,
            direction=TradeDirection.LONG,
        )
        result = calculate_position_size(req)
        assert result.direction == TradeDirection.LONG
        assert result.risk_amount_cop > 0
        assert result.risk_percent_actual <= 1.05  # margen tolerancia
        assert result.risk_reward_ratio is not None
        assert result.risk_reward_ratio == pytest.approx(2.0, abs=0.01)
        assert result.risk_rating == RiskRating.MODERATE
        assert result.units > 0
        assert len(result.observation) > 0
        assert len(result.hypothesis) > 0

    def test_basic_short_position(self):
        """Posición SHORT: precio de entrada por encima del stop."""
        req = PositionSizeRequest(
            capital_cop=100_000_000.0,
            entry_price=50_000.0,
            stop_loss_price=52_000.0,    # Stop arriba para SHORT
            target_price=44_000.0,
            risk_percent=2.0,
            method=PositionSizingMethod.FIXED_PERCENT,
            direction=TradeDirection.SHORT,
        )
        result = calculate_position_size(req)
        assert result.direction == TradeDirection.SHORT
        assert result.units > 0
        # R:R: reward = 50000 - 44000 = 6000; risk = 52000 - 50000 = 2000 → R:R = 3.0
        assert result.risk_reward_ratio == pytest.approx(3.0, abs=0.01)
        assert result.risk_rating == RiskRating.LOW

    def test_long_invalid_stop_raises(self):
        """Stop por ENCIMA del entry en LONG debe levantar ValueError."""
        req = PositionSizeRequest(
            capital_cop=10_000_000.0,
            entry_price=100.0,
            stop_loss_price=110.0,       # Incoherente para LONG
            risk_percent=1.0,
            direction=TradeDirection.LONG,
        )
        with pytest.raises(ValueError, match="LONG"):
            calculate_position_size(req)

    def test_short_invalid_stop_raises(self):
        """Stop por DEBAJO del entry en SHORT debe levantar ValueError."""
        req = PositionSizeRequest(
            capital_cop=10_000_000.0,
            entry_price=100.0,
            stop_loss_price=90.0,        # Incoherente para SHORT
            risk_percent=1.0,
            direction=TradeDirection.SHORT,
        )
        with pytest.raises(ValueError, match="SHORT"):
            calculate_position_size(req)

    def test_risk_hardcap_5pct(self):
        """El riesgo nunca debe superar el 5% del capital."""
        req = PositionSizeRequest(
            capital_cop=10_000_000.0,
            entry_price=100.0,
            stop_loss_price=50.0,
            risk_percent=10.0,           # Pide 10%, hard-cap → 5%
            method=PositionSizingMethod.FIXED_PERCENT,
            direction=TradeDirection.LONG,
        )
        result = calculate_position_size(req)
        assert result.risk_percent_actual <= 5.0 + 0.001

    def test_no_target_null_rr(self):
        """Sin precio objetivo, risk_reward_ratio debe ser None."""
        req = PositionSizeRequest(
            capital_cop=10_000_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
            risk_percent=1.0,
            direction=TradeDirection.LONG,
        )
        result = calculate_position_size(req)
        assert result.risk_reward_ratio is None
        assert "No se definió precio objetivo" in result.hypothesis

    def test_high_rr_gives_very_low_risk_rating(self):
        """R:R >= 4 debe clasificarse como RiskRating.VERY_LOW."""
        req = PositionSizeRequest(
            capital_cop=10_000_000.0,
            entry_price=100.0,
            stop_loss_price=98.0,        # Risk = 2
            target_price=108.0,          # Reward = 8 → R:R = 4
            risk_percent=1.0,
            direction=TradeDirection.LONG,
        )
        result = calculate_position_size(req)
        assert result.risk_reward_ratio == pytest.approx(4.0, abs=0.01)
        assert result.risk_rating == RiskRating.VERY_LOW


# ---------------------------------------------------------------------------
# 2. Position Sizing — Kelly Criterion
# ---------------------------------------------------------------------------

class TestKellySizing:

    def test_kelly_half_applied(self):
        """Kelly debe usar Half-Kelly y respetar hard-cap de 5%."""
        req = PositionSizeRequest(
            capital_cop=50_000_000.0,
            entry_price=1000.0,
            stop_loss_price=950.0,
            win_rate=0.60,
            avg_win_loss_ratio=1.5,
            risk_percent=1.0,
            method=PositionSizingMethod.KELLY,
            direction=TradeDirection.LONG,
        )
        result = calculate_position_size(req)
        # Kelly completo = (0.6*1.5 - 0.4) / 1.5 = (0.9-0.4)/1.5 = 0.333
        # Half Kelly = 0.1667 → >5% hard-cap → risk = 5% = 2.5M COP
        assert result.risk_percent_actual <= 5.01
        assert result.units > 0


# ---------------------------------------------------------------------------
# 3. Drawdown Calculator
# ---------------------------------------------------------------------------

class TestDrawdownMetrics:

    def _flat_then_drop(self):
        """Curva que sube, se mantiene, y luego cae un 20%."""
        eq = [100_000.0] * 10
        eq += [120_000.0] * 10   # +20%
        eq += [96_000.0] * 5     # -20% desde peak
        return eq

    def test_max_drawdown_calculated(self):
        """Max drawdown debe ser ~20% desde 120k → 96k."""
        eq = self._flat_then_drop()
        metrics = calculate_drawdown_metrics(eq)
        assert metrics.max_drawdown_pct == pytest.approx(20.0, abs=0.5)
        assert metrics.max_drawdown_cop == pytest.approx(24_000.0, abs=100.0)

    def test_no_drawdown_flat_curve(self):
        """Curva perfectamente plana: drawdown = 0."""
        eq = [50_000.0] * 20
        metrics = calculate_drawdown_metrics(eq)
        assert metrics.max_drawdown_pct == pytest.approx(0.0, abs=0.001)
        assert metrics.current_drawdown_pct == pytest.approx(0.0, abs=0.001)

    def test_monotone_up_no_drawdown(self):
        """Curva siempre creciente: drawdown actual = 0."""
        eq = [float(i * 1000 + 10_000) for i in range(50)]
        metrics = calculate_drawdown_metrics(eq)
        assert metrics.current_drawdown_pct == pytest.approx(0.0, abs=0.001)

    def test_minimum_bars_raises(self):
        """Curva de un solo punto debe levantar ValueError."""
        with pytest.raises(ValueError):
            calculate_drawdown_metrics([100_000.0])

    def test_recovery_factor_positive(self):
        """Recovery factor debe ser positivo cuando hay retorno total positivo."""
        eq = [100_000.0, 80_000.0, 120_000.0]
        metrics = calculate_drawdown_metrics(eq)
        assert metrics.recovery_factor > 0

    def test_longest_drawdown_duration(self):
        """Detecta la duración correcta del drawdown más largo."""
        # 5 periodos en drawdown
        eq = [100.0, 90.0, 85.0, 88.0, 92.0, 100.0, 110.0]
        metrics = calculate_drawdown_metrics(eq)
        assert metrics.longest_drawdown_bars >= 4


# ---------------------------------------------------------------------------
# 4. Portfolio Simulator
# ---------------------------------------------------------------------------

class TestPortfolioSimulator:

    def test_initial_state(self):
        """El portafolio recién creado tiene equity = capital inicial."""
        sim = PortfolioSimulator(initial_capital_cop=50_000_000.0)
        state = sim.get_state()
        assert state.initial_capital_cop == 50_000_000.0
        assert state.total_trades == 0
        assert state.win_rate == 0.0

    def test_open_and_close_winning_trade(self):
        """Trade ganador incrementa equity y se registra correctamente."""
        sim = PortfolioSimulator(initial_capital_cop=10_000_000.0, commission_pct=0.0)
        trade = sim.open_trade(
            symbol="AAPL",
            direction=TradeDirection.LONG,
            entry_price=100.0,
            units=1000.0,
            risk_amount_cop=100_000.0,
        )
        assert trade.symbol == "AAPL"

        closed = sim.close_trade("AAPL", exit_price=110.0)
        assert closed.pnl_cop == pytest.approx(10_000.0, abs=1.0)   # 1000 u × (110-100)
        assert closed.is_winner is True

        state = sim.get_state()
        assert state.total_trades == 1
        assert state.winning_trades == 1
        assert state.win_rate == pytest.approx(1.0, abs=0.001)

    def test_losing_trade(self):
        """Trade perdedor reduce equity."""
        sim = PortfolioSimulator(initial_capital_cop=10_000_000.0, commission_pct=0.0)
        sim.open_trade("BTC", TradeDirection.LONG, 300_000.0, 10.0)
        closed = sim.close_trade("BTC", exit_price=280_000.0)
        assert closed.pnl_cop == pytest.approx(-200_000.0, abs=10.0)
        assert closed.is_winner is False

    def test_open_duplicate_raises(self):
        """Intentar abrir la misma posición dos veces debe levantar ValueError."""
        sim = PortfolioSimulator(initial_capital_cop=10_000_000.0)
        sim.open_trade("NVDA", TradeDirection.LONG, 500.0, 100.0)
        with pytest.raises(ValueError, match="NVDA"):
            sim.open_trade("NVDA", TradeDirection.LONG, 510.0, 100.0)

    def test_close_nonexistent_raises(self):
        """Cerrar posición inexistente debe levantar KeyError."""
        sim = PortfolioSimulator(initial_capital_cop=5_000_000.0)
        with pytest.raises(KeyError):
            sim.close_trade("ETHUSDT", exit_price=2000.0)

    def test_insufficient_capital_raises(self):
        """Superar el capital disponible debe levantar ValueError."""
        sim = PortfolioSimulator(initial_capital_cop=1_000.0)
        with pytest.raises(ValueError, match="Capital insuficiente"):
            sim.open_trade("GOLD", TradeDirection.LONG, 5000.0, 10.0)

    def test_profit_factor_calculation(self):
        """Profit factor = gross_profit / gross_loss."""
        sim = PortfolioSimulator(initial_capital_cop=100_000_000.0, commission_pct=0.0)
        # 2 ganadoras de 10k, 1 perdedora de 5k → PF = 20k/5k = 4.0
        sim.open_trade("A", TradeDirection.LONG, 100.0, 1000.0)
        sim.close_trade("A", 110.0)   # +10k
        sim.open_trade("B", TradeDirection.LONG, 100.0, 1000.0)
        sim.close_trade("B", 110.0)   # +10k
        sim.open_trade("C", TradeDirection.LONG, 100.0, 1000.0)
        sim.close_trade("C", 95.0)    # -5k

        state = sim.get_state()
        assert state.profit_factor == pytest.approx(4.0, abs=0.01)

    def test_r_multiple_recorded(self):
        """El R-múltiplo se registra correctamente cuando risk_amount_cop está definido."""
        sim = PortfolioSimulator(initial_capital_cop=50_000_000.0, commission_pct=0.0)
        sim.open_trade(
            symbol="SPY",
            direction=TradeDirection.LONG,
            entry_price=400.0,
            units=250.0,
            risk_amount_cop=1_000.0,
        )
        # Ganancia = 250 u × (420 - 400) = 5000 COP → 5R
        closed = sim.close_trade("SPY", exit_price=420.0)
        assert closed.r_multiple == pytest.approx(5.0, abs=0.01)
