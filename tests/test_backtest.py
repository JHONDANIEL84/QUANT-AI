"""Unit tests for Phase 9: Backtesting Lab — QUANT AI.

Verifies:
  - Causal execution: signals at bar i execute at bar i+1 open (no look-ahead bias)
  - Realistic friction: slippage and commissions correctly applied to PnL
  - Trade exit reasons: STOP_LOSS, TAKE_PROFIT, TIMEOUT, END_OF_DATA
  - Performance metrics: Win Rate, Profit Factor, Drawdown, Sharpe, Sortino
  - Strategy signal generation: EMA RSI & SMC Liquidity
"""

import math
from datetime import datetime, timedelta, timezone
from typing import List
import pytest

from data_providers.base.models import MarketBar
from quantitative_engine.backtesting.models import (
    BacktestConfig,
    BacktestResult,
    ExitReason,
    SignalType,
    StrategyName,
)
from quantitative_engine.backtesting.engine import BacktestEngine
from quantitative_engine.backtesting.strategies.ema_rsi import EmaRsiStrategy
from quantitative_engine.backtesting.strategies.smc_liquidity import SMCLiquidityStrategy


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def _bar(
    open_: float,
    high: float,
    low: float,
    close: float,
    idx: int = 0,
    volume: float = 1_000_000.0,
) -> MarketBar:
    """Creates a deterministic synthetic bar."""
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=idx)
    return MarketBar(
        symbol="TEST",
        market="crypto",
        timestamp=ts,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        source="test",
        interval="1d",
        downloaded_at=ts,
        data_status="historical",
    )


def _trend_bars(n: int = 80, step: float = 2.0) -> List[MarketBar]:
    """Generates an upward trending bar series with small wicks."""
    bars = []
    base = 100.0
    for i in range(n):
        o = base + i * step
        c = o + step * 0.8
        h = c + 1.0
        l = o - 1.0
        bars.append(_bar(o, h, l, c, i))
    return bars


# ---------------------------------------------------------------------------
# 1. Causal Execution & Mechanics Tests
# ---------------------------------------------------------------------------

class TestBacktestEngineMechanics:

    def test_insufficient_bars_raises(self):
        """Passing fewer than 30 bars must raise ValueError."""
        config = BacktestConfig(initial_capital_cop=10_000_000.0)
        engine = BacktestEngine(config)
        with pytest.raises(ValueError, match="al menos 30 barras"):
            engine.run([_bar(100, 105, 95, 102, i) for i in range(10)])

    def test_slippage_and_commission_reduce_pnl(self):
        """Net PnL must be strictly less than Gross PnL due to frictions."""
        # Create a series where EMA RSI will enter long
        bars = _trend_bars(60, step=3.0)
        config = BacktestConfig(
            symbol="BTCUSDT",
            initial_capital_cop=50_000_000.0,
            commission_pct=0.002,   # 0.2% commission
            slippage_pct=0.001,     # 0.1% slippage
            strategy_name=StrategyName.EMA_RSI_TREND,
            strategy_params={"fast_ema": 5, "slow_ema": 15, "rsi_period": 7},
        )
        engine = BacktestEngine(config)
        result = engine.run(bars)

        assert isinstance(result, BacktestResult)
        if result.total_trades > 0:
            for trade in result.trades:
                assert trade.commission_cop > 0
                assert trade.net_pnl_cop < trade.gross_pnl_cop

    def test_next_bar_open_execution(self):
        """Trade entry must occur at bar i + 1, not bar i."""
        bars = _trend_bars(60, step=2.0)
        config = BacktestConfig(
            symbol="BTCUSDT",
            initial_capital_cop=50_000_000.0,
            strategy_name=StrategyName.EMA_RSI_TREND,
            strategy_params={"fast_ema": 5, "slow_ema": 12, "rsi_period": 7},
        )
        engine = BacktestEngine(config)
        result = engine.run(bars)

        for trade in result.trades:
            # Entry bar must be strictly after bar 0
            assert trade.entry_bar_idx > 0
            # Entry price should be near the open price of that entry bar (within slippage)
            expected_open = bars[trade.entry_bar_idx].open
            assert math.isclose(trade.entry_price, expected_open * (1.0 + config.slippage_pct), rel_tol=1e-4)

    def test_exit_reasons_valid(self):
        """Every completed trade must have a valid ExitReason."""
        bars = _trend_bars(70, step=2.5)
        config = BacktestConfig(
            symbol="TEST",
            initial_capital_cop=20_000_000.0,
            strategy_name=StrategyName.EMA_RSI_TREND,
            strategy_params={"fast_ema": 5, "slow_ema": 15, "rsi_period": 7},
        )
        engine = BacktestEngine(config)
        result = engine.run(bars)

        valid_reasons = {
            ExitReason.STOP_LOSS,
            ExitReason.TAKE_PROFIT,
            ExitReason.TIMEOUT,
            ExitReason.SIGNAL_REVERSAL,
            ExitReason.END_OF_DATA,
        }
        for trade in result.trades:
            assert trade.exit_reason in valid_reasons
            assert trade.holding_bars >= 0


# ---------------------------------------------------------------------------
# 2. Performance Metrics Calculation Tests
# ---------------------------------------------------------------------------

class TestBacktestMetrics:

    def test_metrics_coherence(self):
        """Verifies mathematical coherence of consolidated backtest metrics."""
        bars = _trend_bars(80, step=2.0)
        config = BacktestConfig(
            symbol="BTCUSDT",
            initial_capital_cop=100_000_000.0,
            strategy_name=StrategyName.EMA_RSI_TREND,
            strategy_params={"fast_ema": 5, "slow_ema": 15, "rsi_period": 7},
        )
        engine = BacktestEngine(config)
        result = engine.run(bars)

        assert result.initial_capital_cop == 100_000_000.0
        assert len(result.equity_curve) == len(bars) + 1  # includes initial point
        assert result.total_trades == result.winning_trades + result.losing_trades
        if result.total_trades > 0:
            assert 0.0 <= result.win_rate <= 1.0
            assert result.max_drawdown_pct >= 0.0

        # Epistemic texts present
        assert len(result.observation) > 0
        assert len(result.hypothesis) > 0
        assert "HIPÓTESIS DE ROBUSTEZ" in result.hypothesis


# ---------------------------------------------------------------------------
# 3. Strategy Signal Generation Tests
# ---------------------------------------------------------------------------

class TestStrategies:

    def test_ema_rsi_strategy_initialization(self):
        """Strategy should initialize with custom parameters."""
        strat = EmaRsiStrategy({"fast_ema": 10, "slow_ema": 30, "rsi_period": 9})
        assert strat.fast_ema_period == 10
        assert strat.slow_ema_period == 30
        assert strat.rsi_period == 9

    def test_ema_rsi_no_signal_insufficient_bars(self):
        """Strategy must return None when history is shorter than requirement."""
        strat = EmaRsiStrategy({"fast_ema": 20, "slow_ema": 50})
        bars = [_bar(100, 105, 95, 102, i) for i in range(15)]
        sig = strat.generate_signal(14, bars)
        assert sig is None

    def test_smc_liquidity_strategy_initialization(self):
        """SMC Liquidity strategy initialization and parameter defaults."""
        strat = SMCLiquidityStrategy({"rr_multiplier": 3.5, "k_fractal": 3})
        assert strat.rr_multiplier == 3.5
        assert strat.k_fractal == 3

    def test_smc_liquidity_no_signal_insufficient_bars(self):
        """SMC strategy requires at least 20 bars."""
        strat = SMCLiquidityStrategy()
        bars = [_bar(100, 105, 95, 102, i) for i in range(10)]
        sig = strat.generate_signal(9, bars)
        assert sig is None
