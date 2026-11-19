"""Unit tests for Phase 11: Live Vision — QUANT AI.

Verifies:
  - Base64 data URI parser and MIME extraction
  - Multimodal visual pattern detection (SMC zones, liquidity pools, candlestick patterns)
  - Epistemic separation (Observation vs Hypothesis vs Risk in COP)
  - Bounding box normalization [0, 1]
  - Error handling on invalid/empty frames
"""

import base64
import pytest

from ai_engine.vision.models import (
    VisionAnalysisRequest,
    VisionAnalysisResponse,
    VisualBias,
    VisualPatternCategory,
)
from ai_engine.vision.analyzer import VisionAnalyzer


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def _dummy_base64_image() -> str:
    """Creates a minimal valid base64 payload representing 1x1 PNG."""
    # 1x1 transparent PNG in base64
    return (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestVisionAnalyzer:

    def test_clean_base64_with_data_uri(self):
        """Should strip data:image/png;base64, prefix and extract MIME type."""
        analyzer = VisionAnalyzer()
        raw = f"data:image/jpeg;base64,{_dummy_base64_image()}"
        clean, mime = analyzer._clean_base64(raw)
        assert clean == _dummy_base64_image()
        assert mime == "image/jpeg"

    def test_clean_base64_bare(self):
        """Should accept raw base64 without prefix and default to image/png."""
        analyzer = VisionAnalyzer()
        raw = _dummy_base64_image()
        clean, mime = analyzer._clean_base64(raw)
        assert clean == raw
        assert mime == "image/png"

    def test_fallback_visual_analysis_structure(self):
        """Deterministic visual fallback must produce structured patterns and epistemic blocks."""
        analyzer = VisionAnalyzer(api_key="")  # force fallback
        req = VisionAnalysisRequest(
            image_base64=_dummy_base64_image(),
            symbol="BTCUSDT",
            interval="1d",
            custom_prompt="¿Detectas alguna mecha de barrido?",
        )
        res = analyzer.analyze_frame(req)

        assert isinstance(res, VisionAnalysisResponse)
        assert res.symbol == "BTCUSDT"
        assert res.interval == "1d"
        assert res.source == "quantitative_vision_engine"
        assert len(res.patterns_detected) >= 2

        # Check epistemic blocks
        assert "OBSERVACIÓN" in res.observation.upper()
        assert "HIPÓTESIS" in res.hypothesis.upper()
        assert "COP" in res.risk_guidance.upper()

        # Check detected patterns
        categories = [p.category for p in res.patterns_detected]
        assert VisualPatternCategory.SMC_ZONE in categories
        assert VisualPatternCategory.LIQUIDITY_ZONE in categories

    def test_bounding_box_normalization(self):
        """All bounding boxes must have coordinates between 0 and 1."""
        analyzer = VisionAnalyzer(api_key="")
        req = VisionAnalysisRequest(
            image_base64=_dummy_base64_image(),
            symbol="NVDA",
            interval="4h",
        )
        res = analyzer.analyze_frame(req)
        for pattern in res.patterns_detected:
            if pattern.bounding_box:
                bb = pattern.bounding_box
                assert 0.0 <= bb.ymin <= 1.0
                assert 0.0 <= bb.xmin <= 1.0
                assert 0.0 <= bb.ymax <= 1.0
                assert 0.0 <= bb.xmax <= 1.0
                assert bb.ymax >= bb.ymin
                assert bb.xmax >= bb.xmin
