"""Unit and integration tests for Market Scanner & Multi-Timeframe Confluence — Phase 7 QUANT AI.

Covers:
  - Single asset opportunity evaluation (technical + SMC + liquidity)
  - Multi-Timeframe (MTF) alignment and divergence scoring
  - Universe collection scanner with score filtering and sorting
  - Model serialization and API response integrity
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict
import pytest

from data_providers.base.models import MarketBar
from quantitative_engine.scanner.models import (
    SetupDirection,
    ConvictionLevel,
    MTFConfluenceResult,
    ScanOpportunity,
    MarketScanResponse,
)
from quantitative_engine.scanner.evaluator import evaluate_asset_opportunity
from quantitative_engine.scanner.mtf import analyze_mtf_confluence
from quantitative_engine.scanner.scanner_engine import scan_asset_bars_collection


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


def _bullish_bars(count: int = 55) -> List[MarketBar]:
    """Genera una serie alcista con HH + HL confirmados por el detector fractal k=3.

    Estructura por ciclo (10 barras):
      3 barras planas al nivel medio
      1 spike HIGH (HH — cada ciclo más alto)
      3 barras planas al nivel medio
      1 spike LOW (HL — mínimos ascendentes)
      2 barras planas tras el mínimo
    Total: 5 ciclos × 11 barras = 55 barras
    """
    bars: List[MarketBar] = []

    for cycle in range(5):
        base_mid = 100.0 + cycle * 15.0
        base_high = base_mid + 10.0
        base_low = base_mid - 2.0
        spike_high = base_mid + 25.0
        # Rising lows across cycles (HL pattern): start at 95, ascend
        pullback_low = 95.0 + cycle * 2.5

        # 3 barras planas antes del pico alto
        for _ in range(3):
            idx = len(bars)
            bars.append(_bar(base_mid, base_high, base_low, base_mid + 2, idx))

        # 1 spike HIGH aislado
        idx = len(bars)
        bars.append(_bar(base_mid + 2, spike_high, base_mid, spike_high - 2, idx, volume=3_000_000.0))

        # 3 barras planas tras el pico alto
        for _ in range(3):
            idx = len(bars)
            bars.append(_bar(base_mid, base_high, base_low, base_mid + 2, idx))

        # 1 spike LOW aislado (mínimo ascendente por ciclo)
        idx = len(bars)
        bars.append(_bar(base_mid, base_mid + 2, pullback_low, pullback_low + 3, idx, volume=2_000_000.0))

        # 2 barras planas tras el mínimo
        for _ in range(2):
            idx = len(bars)
            bars.append(_bar(base_mid, base_high, base_low, base_mid + 2, idx))

    return bars


def _bearish_bars(count: int = 55) -> List[MarketBar]:
    """Genera una serie bajista con LH + LL confirmados por el detector fractal k=3.

    Estructura por ciclo (10 barras):
      3 barras planas al nivel medio
      1 spike LOW (LL — cada ciclo más bajo)
      3 barras planas al nivel medio
      1 spike HIGH (LH — máximos descendentes)
      2 barras planas tras el máximo
    Total: 5 ciclos × 11 barras = 55 barras
    """
    bars: List[MarketBar] = []

    for cycle in range(5):
        base_mid = 250.0 - cycle * 15.0
        base_high = base_mid + 2.0
        base_low = base_mid - 10.0
        spike_low = base_mid - 25.0
        # Falling highs across cycles (LH pattern): start at 265, descend
        pullback_high = 265.0 - cycle * 2.5

        # 3 barras planas antes del pico bajo
        for _ in range(3):
            idx = len(bars)
            bars.append(_bar(base_mid, base_high, base_low, base_mid - 2, idx))

        # 1 spike LOW aislado
        idx = len(bars)
        bars.append(_bar(base_mid - 2, base_mid, spike_low, spike_low + 2, idx, volume=3_000_000.0))

        # 3 barras planas tras el pico bajo
        for _ in range(3):
            idx = len(bars)
            bars.append(_bar(base_mid, base_high, base_low, base_mid - 2, idx))

        # 1 spike HIGH aislado (máximo descendente por ciclo)
        idx = len(bars)
        bars.append(_bar(base_mid, pullback_high, base_mid - 2, pullback_high - 3, idx, volume=2_000_000.0))

        # 2 barras planas tras el máximo
        for _ in range(2):
            idx = len(bars)
            bars.append(_bar(base_mid, base_high, base_low, base_mid - 2, idx))

    return bars


# ---------------------------------------------------------------------------
# 1. Opportunity Evaluator Tests
# ---------------------------------------------------------------------------

class TestOpportunityEvaluator:

    def test_evaluate_bullish_asset(self):
        """Bullish trending asset should score with BULLISH direction."""
        bars = _bullish_bars(60)
        opp = evaluate_asset_opportunity("BTCUSDT", "crypto", "1d", bars)
        assert opp is not None
        assert opp.symbol == "BTCUSDT"
        assert opp.direction == SetupDirection.BULLISH
        assert opp.score >= 40.0
        assert len(opp.matched_criteria) > 0
        assert opp.invalidation_level is not None
        assert len(opp.observation) > 0
        assert len(opp.hypothesis) > 0

    def test_evaluate_bearish_asset(self):
        """Bearish trending asset should score with BEARISH direction."""
        bars = _bearish_bars(60)
        opp = evaluate_asset_opportunity("NVDA", "stock", "1d", bars)
        assert opp is not None
        assert opp.symbol == "NVDA"
        assert opp.direction == SetupDirection.BEARISH
        assert opp.score >= 40.0
        assert opp.invalidation_level is not None


# ---------------------------------------------------------------------------
# 2. Multi-Timeframe (MTF) Confluence Tests
# ---------------------------------------------------------------------------

class TestMTFConfluence:

    def test_mtf_alignment(self):
        """When HTF and LTF are both bullish, MTF confluence is high and aligned."""
        htf = _bullish_bars(60)
        ltf = _bullish_bars(60)
        res = analyze_mtf_confluence("BTCUSDT", "1d", htf, "4h", ltf)
        assert res.symbol == "BTCUSDT"
        assert res.is_aligned is True
        assert res.confluence_score >= 70.0
        assert "ALINEADO ALCISTA" in res.summary

    def test_mtf_insufficient_bars(self):
        """Should safely handle short series without throwing errors (menos de 15 barras)."""
        # Crear exactamente 5 barras para disparar el guard len < 15 en analyze_mtf_confluence
        tiny_bars = [_bar(100.0, 105.0, 98.0, 102.0, i) for i in range(5)]
        res = analyze_mtf_confluence("AAPL", "1d", tiny_bars, "4h", tiny_bars)
        assert res.confluence_score == 0.0
        assert res.is_aligned is False


# ---------------------------------------------------------------------------
# 3. Market Universe Collection Scanner Tests
# ---------------------------------------------------------------------------

class TestUniverseScanner:

    def test_scan_collection_filtering_and_sorting(self):
        """Should scan collection of assets, filter by min_score, and sort descending."""
        bars_dict: Dict[str, List[MarketBar]] = {
            "BTCUSDT": _bullish_bars(60),
            "ETHUSDT": _bullish_bars(60),
            "AAPL": _bearish_bars(60),
            "SPY": _bearish_bars(60),
        }
        res = scan_asset_bars_collection(
            bars_by_symbol=bars_dict,
            market_filter="all",
            interval="1d",
            min_score=40.0,
        )
        assert isinstance(res, MarketScanResponse)
        assert res.total_assets_scanned == 4
        assert res.opportunities_found >= 1
        # Check that list is sorted descending by score
        scores = [opp.score for opp in res.opportunities]
        assert scores == sorted(scores, reverse=True)

    def test_market_filter_crypto_only(self):
        """Market filter 'crypto' should only retain crypto symbols."""
        bars_dict: Dict[str, List[MarketBar]] = {
            "BTCUSDT": _bullish_bars(60),
            "AAPL": _bearish_bars(60),
        }
        res = scan_asset_bars_collection(
            bars_by_symbol=bars_dict,
            market_filter="crypto",
            interval="1d",
            min_score=30.0,
        )
        for opp in res.opportunities:
            assert opp.market == "crypto"
            assert opp.symbol.endswith("USDT")
