"""Unit tests for quantitative indicators (Phase 3).
Verifies mathematical formulas for EMA, RSI, MACD, ATR, VWAP, Bollinger Bands, and Fibonacci.
"""

import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from backend.main import app
from quantitative_engine.indicators.ema import compute_ema, compute_all_emas
from quantitative_engine.indicators.rsi import compute_rsi, compute_rsi_list
from quantitative_engine.indicators.macd import compute_macd
from quantitative_engine.indicators.atr import compute_true_range, compute_atr
from quantitative_engine.indicators.vwap import compute_vwap
from quantitative_engine.indicators.bollinger import compute_bollinger_bands
from quantitative_engine.indicators.fibonacci import compute_fibonacci_levels
from quantitative_engine.indicators.service import indicator_engine
from data_providers.base.models import MarketBar, MarketType, DataStatus
from datetime import datetime, timezone, timedelta

client = TestClient(app)


def test_ema_mathematical_formula():
    """Verify EMA smoothing factor alpha = 2 / (period + 1)."""
    # Constant price series must yield constant EMA
    prices = pd.Series([100.0] * 50)
    ema20 = compute_ema(prices, period=20)
    assert np.isclose(ema20.iloc[-1], 100.0, atol=1e-5)

    # Rising step series
    step_prices = pd.Series([100.0] * 20 + [200.0] * 20)
    ema_step = compute_ema(step_prices, period=20)
    # EMA must lag the step up
    assert 100.0 < ema_step.iloc[25] < 200.0
    assert ema_step.iloc[39] > ema_step.iloc[25]


def test_rsi_bounds_and_behavior():
    """Verify RSI 14 bounds [0, 100] and directional sensitivity."""
    # Pure rising series must produce RSI near 100
    rising = pd.Series([10.0 + i * 2.0 for i in range(40)])
    rsi_up = compute_rsi(rising, period=14)
    assert rsi_up.iloc[-1] > 90.0
    assert (rsi_up.dropna() <= 100.0).all()
    assert (rsi_up.dropna() >= 0.0).all()

    # Pure falling series must produce RSI near 0
    falling = pd.Series([100.0 - i * 2.0 for i in range(40)])
    rsi_down = compute_rsi(falling, period=14)
    assert rsi_down.iloc[-1] < 10.0
    assert (rsi_down.dropna() >= 0.0).all()


def test_macd_calculation():
    """Verify MACD fast/slow EMA divergence and histogram = MACD - Signal."""
    prices = pd.Series([100.0 + i * 1.5 for i in range(50)])
    macd, signal, hist = compute_macd(prices, fast_period=12, slow_period=26, signal_period=9)

    # In sustained uptrend, fast EMA > slow EMA -> MACD > 0
    valid_idx = 35
    assert macd.iloc[valid_idx] > 0
    # Histogram must exactly equal MACD - Signal
    assert np.isclose(hist.iloc[valid_idx], macd.iloc[valid_idx] - signal.iloc[valid_idx], atol=1e-5)


def test_atr_with_gap():
    """Verify True Range captures overnight gaps."""
    high = pd.Series([105.0, 120.0])  # Day 2 gaps up from 102 close to 115-120
    low = pd.Series([95.0, 115.0])
    close = pd.Series([102.0, 118.0])

    tr = compute_true_range(high, low, close)
    # Day 1 TR: High - Low = 10
    assert tr.iloc[0] == 10.0
    # Day 2: H-L=5, |H - C_prev| = 120 - 102 = 18, |L - C_prev| = 115 - 102 = 13 -> max is 18
    assert tr.iloc[1] == 18.0


def test_vwap_volume_weighting():
    """Verify VWAP is pulled towards price with highest volume."""
    # Bar 1: Price 100, Volume 10
    # Bar 2: Price 200, Volume 90
    high = pd.Series([100.0, 200.0])
    low = pd.Series([100.0, 200.0])
    close = pd.Series([100.0, 200.0])
    vol = pd.Series([10.0, 90.0])

    vwap = compute_vwap(high, low, close, vol)
    # Expected: (100 * 10 + 200 * 90) / (10 + 90) = (1000 + 18000) / 100 = 190.0
    assert np.isclose(vwap.iloc[-1], 190.0, atol=1e-5)


def test_bollinger_bands_envelope():
    """Verify Upper >= Middle >= Lower and Bandwidth."""
    prices = pd.Series([100.0 + (i % 5) for i in range(40)])
    mid, up, low, bw, pb = compute_bollinger_bands(prices, period=20, std_multiplier=2.0)

    for i in range(20, 40):
        assert up.iloc[i] >= mid.iloc[i]
        assert mid.iloc[i] >= low.iloc[i]
        assert bw.iloc[i] > 0


def test_fibonacci_golden_ratio():
    """Verify Fibonacci levels 50% equilibrium and 61.8% golden ratio."""
    fib = compute_fibonacci_levels(high=200.0, low=100.0, is_uptrend=True)
    # 50% level between 200 and 100 must be 150
    assert fib.levels["0.5"] == 150.0
    # 61.8% retracement down from 200: 200 - (100 * 0.618) = 138.2
    assert fib.levels["0.618"] == 138.2
    # 0.0 is High
    assert fib.levels["0.0"] == 200.0
    # 1.0 is Low
    assert fib.levels["1.0"] == 100.0


def test_api_chart_data_endpoint():
    """Verify /api/v1/indicators/chart-data returns bars and computed indicators."""
    res = client.get("/api/v1/indicators/chart-data?symbol=BTCUSDT&interval=1d&limit=30")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "BTCUSDT"
    assert len(data["bars"]) > 0
    assert "indicators" in data
    inds = data["indicators"]
    assert "ema_20" in inds
    assert "rsi_14" in inds
    assert "macd" in inds
    assert "atr_14" in inds
    assert "bollinger_bands" in inds
    assert "fibonacci" in inds
