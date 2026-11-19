"""Unit and integration tests for Smart Money Concepts (SMC) — Phase 5 QUANT AI.

Covers:
  - BOS (Break of Structure) & CHOCH (Change of Character) detection
  - Fair Value Gap (FVG) 3-candle identification and mitigation tracking
  - Order Block (OB) identification, quality scoring, mitigation and Breaker conversion
  - Premium vs. Discount dealing range and Equilibrium calculation
  - Serialization and API response verification
"""

import math
from datetime import datetime, timedelta, timezone
from typing import List
import pytest

from data_providers.base.models import MarketBar
from quantitative_engine.market_structure.models import StructurePivot, StructureType
from quantitative_engine.market_structure.swings import detect_market_structure
from quantitative_engine.smc.models import (
    SMCZoneType,
    SMCDirection,
    MitigationStatus,
    StructureBreak,
    OrderBlock,
    FairValueGap,
    PremiumDiscountRange,
    SMCAnalysis,
)
from quantitative_engine.smc.bos_choch import detect_structure_breaks
from quantitative_engine.smc.fvg import detect_fair_value_gaps
from quantitative_engine.smc.order_blocks import detect_order_blocks
from quantitative_engine.smc.premium_discount import compute_premium_discount
from quantitative_engine.smc.analyzer import run_smc_analysis
from backend.api.v1.smc import analyze_smc_data, SMCAnalysisResponse


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


def _bullish_trend_with_bos_bars() -> List[MarketBar]:
    """Generates bars forming a confirmed swing high at 110, swing low at 95, then a break above 110."""
    bars: List[MarketBar] = []
    # k=3 fractal window: 3 bars before, pivot at 4, 3 bars after
    # Base bars 0-3 around 100
    for i in range(4):
        bars.append(_bar(100.0, 102.0, 98.0, 100.0, len(bars)))

    # Bar 4: Swing High at 110
    bars.append(_bar(100.0, 110.0, 99.0, 108.0, len(bars)))

    # Bars 5-7: 3 bars lower than 110 to confirm Swing High at bar 4 (confirmed at bar 7)
    for i in range(3):
        bars.append(_bar(105.0, 107.0, 101.0, 104.0, len(bars)))

    # Bar 8: Swing Low at 95
    bars.append(_bar(102.0, 103.0, 95.0, 96.0, len(bars)))

    # Bars 9-11: 3 bars to confirm Swing Low at bar 8
    for i in range(3):
        bars.append(_bar(98.0, 104.0, 97.0, 103.0, len(bars)))

    # Bar 12: Impulsive breakout candle closing at 115 (above Swing High of 110)
    bars.append(_bar(104.0, 116.0, 103.0, 115.0, len(bars), volume=3_000_000.0))

    # Follow-through bars 13-15
    for i in range(3):
        bars.append(_bar(114.0, 118.0, 112.0, 116.0, len(bars)))

    return bars


# ---------------------------------------------------------------------------
# 1. BOS & CHOCH Tests
# ---------------------------------------------------------------------------

class TestBOSandCHOCH:

    def test_bullish_break_detected(self):
        """Verify that price closing above a confirmed Swing High registers a structural break."""
        bars = _bullish_trend_with_bos_bars()
        struct = detect_market_structure(bars, k=3)
        assert len(struct.pivots) > 0

        breaks = detect_structure_breaks(bars, struct.pivots, k=3)
        assert len(breaks) > 0
        brk = breaks[0]
        assert brk.direction == SMCDirection.BULLISH
        assert brk.broken_pivot_price == 110.0
        assert brk.breaking_price == 115.0
        assert brk.breaking_bar_index == 12

    def test_invalidation_level_defined(self):
        """Every structural break must have an explicit invalidation level."""
        bars = _bullish_trend_with_bos_bars()
        struct = detect_market_structure(bars, k=3)
        breaks = detect_structure_breaks(bars, struct.pivots, k=3)
        for b in breaks:
            assert b.invalidation_level > 0
            assert len(b.rule_applied) > 0


# ---------------------------------------------------------------------------
# 2. Fair Value Gap (FVG) Tests
# ---------------------------------------------------------------------------

class TestFairValueGaps:

    def test_bullish_fvg_detection(self):
        """Bullish FVG: bar[i].low > bar[i-2].high with strong green middle bar."""
        bars = [
            _bar(100.0, 102.0, 98.0, 100.0, 0),  # bar 0: high = 102.0
            _bar(101.0, 115.0, 101.0, 114.0, 1), # bar 1: impulse green candle
            _bar(114.0, 118.0, 106.0, 117.0, 2), # bar 2: low = 106.0 (> 102.0)
        ]
        fvgs = detect_fair_value_gaps(bars, min_gap_pct=0.01)
        assert len(fvgs) == 1
        fvg = fvgs[0]
        assert fvg.direction == SMCDirection.BULLISH
        assert fvg.top_price == 106.0
        assert fvg.bottom_price == 102.0
        assert fvg.gap_size == 4.0
        assert fvg.consequent_encroachment == 104.0
        assert fvg.status == MitigationStatus.UNMITIGATED

    def test_bearish_fvg_detection(self):
        """Bearish FVG: bar[i-2].low > bar[i].high with strong red middle bar."""
        bars = [
            _bar(120.0, 122.0, 115.0, 118.0, 0), # bar 0: low = 115.0
            _bar(118.0, 118.0, 102.0, 103.0, 1), # bar 1: impulse red candle
            _bar(103.0, 110.0, 100.0, 102.0, 2), # bar 2: high = 110.0 (< 115.0)
        ]
        fvgs = detect_fair_value_gaps(bars, min_gap_pct=0.01)
        assert len(fvgs) == 1
        fvg = fvgs[0]
        assert fvg.direction == SMCDirection.BEARISH
        assert fvg.top_price == 115.0
        assert fvg.bottom_price == 110.0
        assert fvg.gap_size == 5.0
        assert fvg.consequent_encroachment == 112.5

    def test_fvg_mitigation_lifecycle(self):
        """Verify FVG transitions from UNMITIGATED -> PARTIAL -> MITIGATED as price retraces."""
        bars = [
            _bar(100.0, 102.0, 98.0, 100.0, 0),  # bar 0: high = 102
            _bar(101.0, 115.0, 101.0, 114.0, 1), # bar 1: impulse
            _bar(114.0, 118.0, 106.0, 117.0, 2), # bar 2: low = 106 (gap 102-106, CE 104)
            # Subsequent bar 3 tests CE (low = 103)
            _bar(117.0, 117.0, 103.0, 105.0, 3),
        ]
        fvgs = detect_fair_value_gaps(bars, min_gap_pct=0.01)
        assert len(fvgs) == 1
        assert fvgs[0].status == MitigationStatus.PARTIAL
        assert fvgs[0].mitigated_pct >= 50.0

        # Bar 4 completely fills the gap down to 101
        bars.append(_bar(105.0, 106.0, 101.0, 102.0, 4))
        fvgs_filled = detect_fair_value_gaps(bars, min_gap_pct=0.01)
        assert len(fvgs_filled) == 1
        assert fvgs_filled[0].status == MitigationStatus.MITIGATED
        assert fvgs_filled[0].mitigated_pct == 100.0


# ---------------------------------------------------------------------------
# 3. Order Block (OB) Tests
# ---------------------------------------------------------------------------

class TestOrderBlocks:

    def test_bullish_order_block_detected(self):
        """Bullish OB: Last down candle before strong expansion."""
        bars = [
            _bar(100.0, 101.0, 99.0, 100.0, 0),
            _bar(100.0, 101.0, 96.0, 97.0, 1, volume=500_000.0), # Down candle at bar 1
            _bar(97.0, 115.0, 97.0, 114.0, 2, volume=2_500_000.0), # Strong expansion
            _bar(114.0, 118.0, 112.0, 116.0, 3),
        ]
        obs = detect_order_blocks(bars)
        bullish_obs = [o for o in obs if o.direction == SMCDirection.BULLISH]
        assert len(bullish_obs) > 0
        ob = bullish_obs[0]
        assert ob.bar_index == 1
        assert ob.top_price == 101.0
        assert ob.bottom_price == 96.0
        assert ob.quality_score >= 30.0

    def test_bearish_order_block_detected(self):
        """Bearish OB: Last up candle before strong drop."""
        bars = [
            _bar(100.0, 101.0, 99.0, 100.0, 0),
            _bar(100.0, 105.0, 99.0, 104.0, 1, volume=500_000.0), # Up candle at bar 1
            _bar(104.0, 104.0, 85.0, 86.0, 2, volume=2_500_000.0), # Strong drop
            _bar(86.0, 88.0, 83.0, 84.0, 3),
        ]
        obs = detect_order_blocks(bars)
        bearish_obs = [o for o in obs if o.direction == SMCDirection.BEARISH]
        assert len(bearish_obs) > 0
        ob = bearish_obs[0]
        assert ob.bar_index == 1
        assert ob.top_price == 105.0
        assert ob.bottom_price == 99.0

    def test_breaker_block_conversion(self):
        """When price completely closes through an OB, it flips to an invalidated Breaker."""
        bars = [
            _bar(100.0, 101.0, 99.0, 100.0, 0),
            _bar(100.0, 102.0, 98.0, 99.0, 1), # Down candle (Bullish OB candidate [98 - 102])
            _bar(99.0, 115.0, 99.0, 114.0, 2), # Strong pump
            _bar(114.0, 116.0, 112.0, 115.0, 3),
            # Violent dump closing at 90 (below OB low of 98)
            _bar(115.0, 115.0, 88.0, 90.0, 4),
        ]
        obs = detect_order_blocks(bars)
        bullish_obs = [o for o in obs if o.direction == SMCDirection.BULLISH]
        assert len(bullish_obs) > 0
        ob = bullish_obs[0]
        assert ob.status == MitigationStatus.INVALIDATED
        assert ob.is_breaker is True


# ---------------------------------------------------------------------------
# 4. Premium vs. Discount Tests
# ---------------------------------------------------------------------------

class TestPremiumDiscount:

    def test_equilibrium_at_50_percent(self):
        """Equilibrium must equal (high + low) / 2 and current_position_pct calculated correctly."""
        bars = [_bar(150.0, 150.0, 150.0, 150.0, i) for i in range(10)]
        pivots = [
            StructurePivot(
                bar_index=1,
                timestamp=bars[1].timestamp,
                confirmed_at=bars[4].timestamp,
                price=200.0,
                is_high=True,
                structure_type=StructureType.HH,
                rule_applied="High",
            ),
            StructurePivot(
                bar_index=2,
                timestamp=bars[2].timestamp,
                confirmed_at=bars[5].timestamp,
                price=100.0,
                is_high=False,
                structure_type=StructureType.HL,
                rule_applied="Low",
            ),
        ]
        pd_range = compute_premium_discount(bars, pivots)
        assert pd_range is not None
        assert pd_range.swing_high == 200.0
        assert pd_range.swing_low == 100.0
        assert pd_range.equilibrium == 150.0
        assert pd_range.current_position_pct == 50.0
        assert pd_range.zone == "EQUILIBRIUM"

    def test_discount_classification(self):
        """Price below 45% of range must classify as DISCOUNT."""
        bars = [_bar(120.0, 120.0, 120.0, 120.0, i) for i in range(10)]
        # Range 100 to 200, price 120 -> position 20%
        pivots = [
            StructurePivot(
                bar_index=1,
                timestamp=bars[1].timestamp,
                confirmed_at=bars[4].timestamp,
                price=200.0,
                is_high=True,
                structure_type=StructureType.HH,
                rule_applied="High",
            ),
            StructurePivot(
                bar_index=2,
                timestamp=bars[2].timestamp,
                confirmed_at=bars[5].timestamp,
                price=100.0,
                is_high=False,
                structure_type=StructureType.HL,
                rule_applied="Low",
            ),
        ]
        pd_range = compute_premium_discount(bars, pivots)
        assert pd_range is not None
        assert pd_range.current_position_pct == 20.0
        assert pd_range.zone == "DISCOUNT"


# ---------------------------------------------------------------------------
# 5. Master SMC Orchestrator & API Tests
# ---------------------------------------------------------------------------

class TestSMCOrchestratorAndAPI:

    def test_run_smc_analysis_full_pipeline(self):
        """run_smc_analysis returns a fully populated SMCAnalysis."""
        bars = _bullish_trend_with_bos_bars()
        res = run_smc_analysis(symbol="BTCUSDT", interval="1d", bars=bars)
        assert res.symbol == "BTCUSDT"
        assert res.bars_analyzed == len(bars)
        assert isinstance(res.structure_breaks, list)
        assert isinstance(res.order_blocks, list)
        assert isinstance(res.fair_value_gaps, list)
        assert len(res.observation) > 0
        assert len(res.hypothesis) > 0

    def test_analyze_smc_data_serialization(self):
        """analyze_smc_data serializes to SMCAnalysisResponse cleanly."""
        bars = _bullish_trend_with_bos_bars()
        resp = analyze_smc_data(symbol="BTCUSDT", interval="1d", bars=bars)
        assert isinstance(resp, SMCAnalysisResponse)
        data = resp.model_dump()
        assert "symbol" in data
        assert "structure_breaks" in data
        assert "order_blocks" in data
        assert "fair_value_gaps" in data
        assert "premium_discount" in data
        assert "observation" in data
        assert "hypothesis" in data
        assert data["symbol"] == "BTCUSDT"
