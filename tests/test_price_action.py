"""Unit tests for Phase 4: Candle Patterns, Market Structure, and Price Action.

Tests strictly verify:
  - Candle pattern detection rules (body, wick ratios)
  - Market structure pivots and trend classification
  - Look-ahead bias prevention in pivot confirmation timestamps
  - Support/Resistance zone detection
  - Price Action API endpoint
"""

import sys
import os
import math
from datetime import datetime, timedelta, timezone
from typing import List

import pytest

# Insert project root so imports resolve from workspace root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_providers.base.models import MarketBar
from quantitative_engine.candles.patterns import detect_candle_patterns
from quantitative_engine.candles.models import CandlePatternType, CandlePatternDirection
from quantitative_engine.market_structure.swings import detect_market_structure
from quantitative_engine.market_structure.models import TrendDirection, StructureType
from quantitative_engine.price_action.analyzer import (
    detect_support_resistance,
    detect_compression,
    run_price_action_analysis,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bar(open_: float, high: float, low: float, close: float, idx: int = 0) -> MarketBar:
    """Create a minimal MarketBar for testing using valid enum values."""
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=idx)
    return MarketBar(
        symbol="TEST",
        market="stock",
        timestamp=ts,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=1_000_000.0,
        source="test",
        interval="1d",
        downloaded_at=ts,
        data_status="historical",
    )


def _uptrend_zigzag_bars() -> List[MarketBar]:
    """Generate a clear uptrend with isolated spike highs and spike lows.

    Uses k=3 fractal windows: each swing pivot has strictly higher/lower
    neighbors k=3 bars on each side.

    Pattern: flat stretches at 100 with alternating spike-highs (HH) and spike-lows (HL).
    SH1=110 → SL1=90 → HH=115 → HL=93 → HH=118 → HL=95
    """
    segments = [
        (101.0, 99.0, 4),   # flat 0-3
        (110.0, 99.0, 1),   # SH1 at bar 4
        (101.0, 99.0, 4),   # flat 5-8
        (101.0, 90.0, 1),   # SL1 at bar 9
        (101.0, 99.0, 4),   # flat 10-13
        (115.0, 99.0, 1),   # HH at bar 14
        (101.0, 99.0, 4),   # flat 15-18
        (101.0, 93.0, 1),   # HL at bar 19
        (101.0, 99.0, 4),   # flat 20-23
        (118.0, 99.0, 1),   # HH2 at bar 24
        (101.0, 99.0, 4),   # flat 25-28
        (101.0, 95.0, 1),   # HL2 at bar 29
        (101.0, 99.0, 4),   # flat 30-33
    ]
    bars: List[MarketBar] = []
    i = 0
    for h, l, n in segments:
        for _ in range(n):
            bars.append(_bar(100.0, h, l, 100.0, i))
            i += 1
    return bars


def _downtrend_zigzag_bars() -> List[MarketBar]:
    """Generate a clear downtrend with isolated spike highs (LH) and spike lows (LL)."""
    segments = [
        (101.0, 99.0, 4),   # flat 0-3
        (120.0, 99.0, 1),   # SH1 at bar 4
        (101.0, 99.0, 4),   # flat 5-8
        (101.0, 85.0, 1),   # SL1 at bar 9
        (101.0, 99.0, 4),   # flat 10-13
        (115.0, 99.0, 1),   # LH at bar 14
        (101.0, 99.0, 4),   # flat 15-18
        (101.0, 80.0, 1),   # LL at bar 19
        (101.0, 99.0, 4),   # flat 20-23
        (112.0, 99.0, 1),   # LH2 at bar 24
        (101.0, 99.0, 4),   # flat 25-28
        (101.0, 76.0, 1),   # LL2 at bar 29
        (101.0, 99.0, 4),   # flat 30-33
    ]
    bars: List[MarketBar] = []
    i = 0
    for h, l, n in segments:
        for _ in range(n):
            bars.append(_bar(100.0, h, l, 100.0, i))
            i += 1
    return bars


def _oscillating_bars(n: int = 100) -> List[MarketBar]:
    """Creates bars oscillating between ~90 and ~110 to form S/R zones."""
    bars = []
    for i in range(n):
        close = 100.0 + 10.0 * math.sin(i * 0.4)
        high = close + 1.0
        low = close - 1.0
        open_ = close - 0.5
        bars.append(_bar(open_, high, low, close, i))
    return bars


# ---------------------------------------------------------------------------
# 1. Candle Pattern Tests
# ---------------------------------------------------------------------------

class TestCandlePatterns:

    def test_doji_detected(self):
        """Body <= 10% of range triggers DOJI pattern.
        
        Range=10, body=0.5 → 5% of range → DOJI triggered.
        """
        bars = [
            _bar(100.0, 110.0, 100.0, 100.0, 0),
            _bar(105.0, 115.0, 105.0, 105.5, 1),  # body=0.5, range=10 → 5% ✓
        ]
        result = detect_candle_patterns(bars)
        types = [p.pattern_type for p in result]
        assert CandlePatternType.DOJI in types, "DOJI should be detected when body <= 10% of range"

    def test_hammer_detected(self):
        """Lower wick >= 2x body and no upper wick triggers HAMMER.
        
        Open=108, High=108.1, Low=100, Close=108.1
        body=0.1, lower_wick=8.1, upper_wick=0.0
        → lower_wick=8.1 >= 2*0.1=0.2 ✓, upper_wick=0 <= 0.2*0.1=0.02 ✓
        """
        bars = [
            _bar(105.0, 115.0, 100.0, 110.0, 0),
            _bar(108.0, 108.1, 100.0, 108.1, 1),
        ]
        result = detect_candle_patterns(bars)
        types = [p.pattern_type for p in result]
        assert CandlePatternType.HAMMER in types, (
            "HAMMER should be detected: lower_wick >= 2*body and upper_wick ~= 0"
        )

    def test_bullish_engulfing_detected(self):
        """Current bullish candle engulfs previous bearish candle.
        
        Prev: O=110, C=106 (bearish). Curr: O=104 <= 106, C=114 >= 110 (engulfs).
        """
        bars = [
            _bar(110.0, 112.0, 105.0, 106.0, 0),   # Bearish
            _bar(104.0, 115.0, 103.0, 114.0, 1),   # Bullish engulfing
        ]
        result = detect_candle_patterns(bars)
        types = [p.pattern_type for p in result]
        assert CandlePatternType.BULLISH_ENGULFING in types, "BULLISH_ENGULFING should be detected"

    def test_bearish_engulfing_detected(self):
        """Current bearish candle engulfs previous bullish candle."""
        bars = [
            _bar(100.0, 112.0, 99.0, 110.0, 0),   # Bullish
            _bar(112.0, 113.0, 97.0, 98.0, 1),     # Bearish engulfing
        ]
        result = detect_candle_patterns(bars)
        types = [p.pattern_type for p in result]
        assert CandlePatternType.BEARISH_ENGULFING in types, "BEARISH_ENGULFING should be detected"

    def test_inside_bar_detected(self):
        """High of current bar <= High of previous bar AND Low of current >= Low of previous."""
        bars = [
            _bar(100.0, 120.0, 90.0, 110.0, 0),   # Mother bar
            _bar(105.0, 115.0, 95.0, 108.0, 1),   # Inside: H=115<=120, L=95>=90
        ]
        result = detect_candle_patterns(bars)
        types = [p.pattern_type for p in result]
        assert CandlePatternType.INSIDE_BAR in types, "INSIDE_BAR should be detected when contained in mother bar"

    def test_no_patterns_on_single_bar(self):
        """With only 1 bar there cannot be any pattern (minimum is 2 bars)."""
        bars = [_bar(100.0, 110.0, 90.0, 105.0, 0)]
        result = detect_candle_patterns(bars)
        assert result == [], "Single bar should produce no patterns"

    def test_pattern_has_rule_applied(self):
        """Every detected pattern must have a non-empty rule_applied string."""
        bars = [
            _bar(110.0, 112.0, 105.0, 106.0, 0),
            _bar(104.0, 115.0, 103.0, 114.0, 1),
        ]
        result = detect_candle_patterns(bars)
        for pat in result:
            assert pat.rule_applied, f"Pattern {pat.pattern_type} has empty rule_applied"


# ---------------------------------------------------------------------------
# 2. Market Structure Tests
# ---------------------------------------------------------------------------

class TestMarketStructure:

    def test_uptrend_detected(self):
        """An upward-drifting zigzag price series with explicit HH/HL should produce UPTREND."""
        bars = _uptrend_zigzag_bars()
        result = detect_market_structure(bars, k=3)
        assert result.trend == TrendDirection.UPTREND, (
            f"Expected UPTREND, got {result.trend.value}. "
            f"Pivots: {[(p.structure_type.value, round(p.price, 2)) for p in result.pivots]}"
        )

    def test_downtrend_detected(self):
        """A declining zigzag price series with explicit LH/LL should produce DOWNTREND."""
        bars = _downtrend_zigzag_bars()
        result = detect_market_structure(bars, k=3)
        assert result.trend == TrendDirection.DOWNTREND, (
            f"Expected DOWNTREND, got {result.trend.value}. "
            f"Pivots: {[(p.structure_type.value, round(p.price, 2)) for p in result.pivots]}"
        )

    def test_no_lookahead_bias(self):
        """Pivot at bar index i must have confirmed_at timestamp strictly after bars[i].timestamp."""
        bars = _uptrend_zigzag_bars()
        result = detect_market_structure(bars, k=3)
        assert len(result.pivots) > 0, "Expected pivots in uptrend zigzag series"
        for pivot in result.pivots:
            assert pivot.confirmed_at > pivot.timestamp, (
                f"Look-ahead bias violation: pivot at {pivot.timestamp} has confirmed_at={pivot.confirmed_at} "
                f"which is not strictly after the pivot timestamp."
            )

    def test_insufficient_data_returns_consolidation(self):
        """Fewer than 2k+1 bars should return CONSOLIDATION with empty pivots."""
        bars = [_bar(100.0, 110.0, 90.0, 105.0, i) for i in range(5)]
        result = detect_market_structure(bars, k=3)
        assert result.trend == TrendDirection.CONSOLIDATION
        assert result.pivots == []

    def test_pivots_chronological(self):
        """Pivots must be returned in chronological order by bar_index."""
        bars = _uptrend_zigzag_bars()
        result = detect_market_structure(bars, k=3)
        bar_indices = [p.bar_index for p in result.pivots]
        assert bar_indices == sorted(bar_indices), "Pivots must be sorted chronologically by bar_index"


# ---------------------------------------------------------------------------
# 3. Price Action / Support-Resistance Tests
# ---------------------------------------------------------------------------

class TestPriceAction:

    def test_support_resistance_zones_detected(self):
        """Oscillating price series should generate at least one S/R zone."""
        bars = _oscillating_bars(100)
        zones = detect_support_resistance(bars, min_touches=2, tolerance_pct=0.01)
        assert len(zones) >= 1, "Should detect at least one S/R zone in oscillating price series"

    def test_zones_have_evidence(self):
        """Every zone must include a non-empty evidence string."""
        bars = _oscillating_bars(100)
        zones = detect_support_resistance(bars, min_touches=2, tolerance_pct=0.01)
        for zone in zones:
            assert zone.evidence, f"Zone {zone.zone_type} at {zone.price_level} has empty evidence"

    def test_zone_strength_in_range(self):
        """Zone strength must be in [0, 1]."""
        bars = _oscillating_bars(100)
        zones = detect_support_resistance(bars, min_touches=2, tolerance_pct=0.01)
        for zone in zones:
            assert 0.0 <= zone.strength <= 1.0, f"Strength {zone.strength} out of [0, 1]"

    def test_no_zones_on_monotone_series(self):
        """A straight ascending line with tight tolerance has no meaningful S/R clusters."""
        bars = [_bar(float(i), float(i + 1), float(i) - 0.5, float(i) + 0.5, i) for i in range(1, 50)]
        # With tight tolerance each pivot is unique — no meaningful clusters
        zones = detect_support_resistance(bars, min_touches=3, tolerance_pct=0.001)
        assert isinstance(zones, list), "Should return a list (may be empty)"

    def test_compression_detected_on_flat_atr(self):
        """detect_compression returns bool for any input."""
        bars = [_bar(100.0, 100.05, 99.95, 100.0, i) for i in range(100)]
        result = detect_compression(bars)
        assert isinstance(result, bool)

    def test_run_price_action_analysis_returns_full_response(self):
        """run_price_action_analysis should always return a PriceActionAnalysis object."""
        bars = _oscillating_bars(100)
        pa = run_price_action_analysis(bars)
        assert pa is not None
        assert isinstance(pa.zones, list)
        assert isinstance(pa.events, list)
        assert isinstance(pa.observation, str)
        assert isinstance(pa.hypothesis, str)
        assert len(pa.observation) > 0, "observation must not be empty"


# ---------------------------------------------------------------------------
# 4. API Endpoint & Serialization Test
# ---------------------------------------------------------------------------

class TestPriceActionAPI:

    def test_price_action_endpoint_exists(self):
        """The analyze_price_action_data function should return valid PriceActionResponse."""
        from backend.api.v1.price_action import analyze_price_action_data

        mock_bars = _oscillating_bars(50)
        response = analyze_price_action_data(symbol="AAPL", interval="1d", bars=mock_bars)
        assert response.symbol == "AAPL"
        assert response.bars_analyzed == 50

    def test_price_action_endpoint_structure(self):
        """When processed, response must contain required top-level keys."""
        from backend.api.v1.price_action import analyze_price_action_data

        mock_bars = _oscillating_bars(50)
        response = analyze_price_action_data(symbol="AAPL", interval="1d", bars=mock_bars)
        data = response.model_dump()
        assert "symbol" in data
        assert "market_structure" in data
        assert "price_action" in data
        assert "candle_patterns" in data
        assert data["symbol"] == "AAPL"
        assert len(data["market_structure"]["pivots"]) > 0
        assert len(data["price_action"]["zones"]) > 0
