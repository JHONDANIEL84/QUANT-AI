"""Unit tests for Liquidity Intelligence & Sweeps — Phase 6 QUANT AI.

Covers:
  - Equal Highs (EQH) and Equal Lows (EQL) clustering
  - Buy-side (BSL) and Sell-side (SSL) pools
  - Session benchmarks (PDH, PDL, PWH, PWL)
  - Confirmed Liquidity Sweeps / Hunts with institutional rejection
  - Master analysis pipeline and API serialization
"""

from datetime import datetime, timedelta, timezone
from typing import List
import pytest

from data_providers.base.models import MarketBar
from quantitative_engine.market_structure.models import StructurePivot, StructureType
from quantitative_engine.liquidity.models import (
    LiquidityType,
    SweepStatus,
    LiquidityPool,
    LiquiditySweepEvent,
    SessionLevels,
    LiquidityAnalysis,
)
from quantitative_engine.liquidity.equal_levels import detect_equal_levels_and_pools
from quantitative_engine.liquidity.session_levels import compute_session_levels
from quantitative_engine.liquidity.sweeps import detect_liquidity_sweeps
from quantitative_engine.liquidity.analyzer import run_liquidity_analysis
from backend.api.v1.liquidity import analyze_liquidity_data, LiquidityAnalysisResponse


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
    """Creates a synthetic MarketBar."""
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


# ---------------------------------------------------------------------------
# 1. Equal Levels (EQH / EQL) Tests
# ---------------------------------------------------------------------------

class TestEqualLevels:

    def test_equal_highs_clustered(self):
        """Two swing highs within tolerance should cluster into an EQH pool."""
        bars = [_bar(100.0, 101.0, 99.0, 100.0, i) for i in range(10)]
        # Two swing highs at 120.00 and 120.08 (within 0.2% tolerance)
        pivots = [
            StructurePivot(
                bar_index=2,
                timestamp=bars[2].timestamp,
                confirmed_at=bars[5].timestamp,
                price=120.00,
                is_high=True,
                structure_type=StructureType.HH,
                rule_applied="Peak 1",
            ),
            StructurePivot(
                bar_index=6,
                timestamp=bars[6].timestamp,
                confirmed_at=bars[9].timestamp,
                price=120.08,
                is_high=True,
                structure_type=StructureType.HH,
                rule_applied="Peak 2",
            ),
        ]
        pools = detect_equal_levels_and_pools(bars, pivots, atr_val=1.5, tolerance_pct=0.002)
        eqh_pools = [p for p in pools if p.pool_type == LiquidityType.EQH]
        assert len(eqh_pools) == 1
        pool = eqh_pools[0]
        assert pool.touch_count == 2
        assert pool.price_level == 120.08
        assert pool.liquidity_score >= 70.0
        assert pool.status == SweepStatus.ACTIVE

    def test_equal_lows_clustered(self):
        """Two swing lows within tolerance should cluster into an EQL pool."""
        bars = [_bar(100.0, 101.0, 99.0, 100.0, i) for i in range(10)]
        pivots = [
            StructurePivot(
                bar_index=2,
                timestamp=bars[2].timestamp,
                confirmed_at=bars[5].timestamp,
                price=90.00,
                is_high=False,
                structure_type=StructureType.HL,
                rule_applied="Valley 1",
            ),
            StructurePivot(
                bar_index=6,
                timestamp=bars[6].timestamp,
                confirmed_at=bars[9].timestamp,
                price=90.05,
                is_high=False,
                structure_type=StructureType.HL,
                rule_applied="Valley 2",
            ),
        ]
        pools = detect_equal_levels_and_pools(bars, pivots, atr_val=1.5, tolerance_pct=0.002)
        eql_pools = [p for p in pools if p.pool_type == LiquidityType.EQL]
        assert len(eql_pools) == 1
        pool = eql_pools[0]
        assert pool.touch_count == 2
        assert pool.price_level == 90.00
        assert pool.liquidity_score >= 70.0


# ---------------------------------------------------------------------------
# 2. Liquidity Sweeps / Hunts Tests
# ---------------------------------------------------------------------------

class TestLiquiditySweeps:

    def test_buy_side_sweep_with_rejection(self):
        """A high wick penetrates EQH at 120 (reaches 122), but close is 119 -> Confirmed Sweep."""
        bars = [
            _bar(100.0, 101.0, 99.0, 100.0, 0),
            _bar(110.0, 120.0, 109.0, 118.0, 1), # establishes EQH pool at bar 1
            _bar(118.0, 119.0, 115.0, 117.0, 2),
            # Bar 3: Sweep candle! High=122.50 (>120), Close=119.00 (<=120)
            _bar(117.0, 122.5, 116.0, 119.0, 3),
        ]
        pool = LiquidityPool(
            pool_type=LiquidityType.EQH,
            price_level=120.0,
            top_price=120.5,
            bottom_price=119.5,
            touch_count=2,
            first_touch_at=bars[0].timestamp,
            last_touch_at=bars[1].timestamp,
            liquidity_score=80.0,
            status=SweepStatus.ACTIVE,
            rule_applied="EQH pool",
        )
        sweeps = detect_liquidity_sweeps(bars, [pool])
        assert len(sweeps) == 1
        sw = sweeps[0]
        assert sw.pool_type == LiquidityType.EQH
        assert sw.price_level == 120.0
        assert sw.penetration_price == 122.5
        assert sw.rejection_close == 119.0
        assert sw.invalidation_level == 122.5
        assert pool.status == SweepStatus.SWEPT

    def test_sell_side_sweep_with_rejection(self):
        """A low wick penetrates EQL at 90 (reaches 87), but close is 91 -> Confirmed Sweep."""
        bars = [
            _bar(100.0, 101.0, 99.0, 100.0, 0),
            _bar(95.0, 96.0, 90.0, 92.0, 1),
            _bar(92.0, 94.0, 91.0, 93.0, 2),
            # Bar 3: Low=87.50 (<90), Close=91.00 (>=90)
            _bar(93.0, 95.0, 87.5, 91.0, 3),
        ]
        pool = LiquidityPool(
            pool_type=LiquidityType.EQL,
            price_level=90.0,
            top_price=90.5,
            bottom_price=89.5,
            touch_count=2,
            first_touch_at=bars[0].timestamp,
            last_touch_at=bars[1].timestamp,
            liquidity_score=80.0,
            status=SweepStatus.ACTIVE,
            rule_applied="EQL pool",
        )
        sweeps = detect_liquidity_sweeps(bars, [pool])
        assert len(sweeps) == 1
        sw = sweeps[0]
        assert sw.pool_type == LiquidityType.EQL
        assert sw.penetration_price == 87.5
        assert sw.rejection_close == 91.0
        assert pool.status == SweepStatus.SWEPT


# ---------------------------------------------------------------------------
# 3. Session Levels Tests
# ---------------------------------------------------------------------------

class TestSessionLevels:

    def test_pdh_pdl_calculation(self):
        """Verify PDH and PDL extraction across different days."""
        bars = [
            _bar(100.0, 110.0, 95.0, 105.0, 0), # Day 1: High 110, Low 95
            _bar(105.0, 108.0, 102.0, 106.0, 1), # Day 2 (current)
        ]
        levels = compute_session_levels(bars)
        assert levels.pdh == 110.0
        assert levels.pdl == 95.0


# ---------------------------------------------------------------------------
# 4. Master Orchestrator & API Tests
# ---------------------------------------------------------------------------

class TestLiquidityOrchestratorAndAPI:

    def test_run_liquidity_analysis_pipeline(self):
        """run_liquidity_analysis returns populated LiquidityAnalysis object."""
        bars = [_bar(100.0 + (i % 4) * 5.0, 105.0 + (i % 4) * 5.0, 95.0, 100.0, i) for i in range(25)]
        analysis = run_liquidity_analysis(symbol="BTCUSDT", interval="1d", bars=bars)
        assert analysis.symbol == "BTCUSDT"
        assert analysis.bars_analyzed == 25
        assert isinstance(analysis.pools, list)
        assert isinstance(analysis.sweeps, list)
        assert len(analysis.observation) > 0
        assert len(analysis.hypothesis) > 0

    def test_analyze_liquidity_data_serialization(self):
        """analyze_liquidity_data serializes to valid LiquidityAnalysisResponse."""
        bars = [_bar(100.0 + (i % 4) * 5.0, 105.0 + (i % 4) * 5.0, 95.0, 100.0, i) for i in range(25)]
        resp = analyze_liquidity_data(symbol="BTCUSDT", interval="1d", bars=bars)
        assert isinstance(resp, LiquidityAnalysisResponse)
        data = resp.model_dump()
        assert "symbol" in data
        assert "pools" in data
        assert "sweeps" in data
        assert "session_levels" in data
        assert "observation" in data
        assert "hypothesis" in data
        assert data["symbol"] == "BTCUSDT"
