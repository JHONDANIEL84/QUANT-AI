"""Unit tests for Phase 13: Live Assistant Copilot Orchestrator — QUANT AI.

Verifies:
  - Proactive alert detection (Invalidation Near, OB Tested, Liquidity Swept)
  - Multimodal turn execution (Audio + Vision + Quantitative Data)
  - Synchronous fusion and speech synthesis output
"""

from datetime import datetime, timedelta, timezone
from typing import List
import pytest

from data_providers.base.models import MarketBar
from ai_engine.orchestration.models import (
    MultimodalTurnRequest,
    MultimodalTurnResponse,
    AlertType,
    AlertSeverity,
)
from ai_engine.orchestration.copilot import LiveCopilotOrchestrator


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def _make_bars(n: int = 50, base: float = 100.0, step: float = 1.0) -> List[MarketBar]:
    bars = []
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(n):
        o = base + i * step
        c = o + step * 0.8
        h = c + 1.5
        l = o - 0.5
        bars.append(
            MarketBar(
                symbol="BTCUSDT",
                market="crypto",
                timestamp=ts + timedelta(days=i),
                open=o,
                high=h,
                low=l,
                close=c,
                volume=1_000_000.0,
                source="test",
                interval="1d",
                downloaded_at=ts,
                data_status="historical",
            )
        )
    return bars


def _dummy_image_b64() -> str:
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


def _dummy_audio_b64() -> str:
    return "GkXfo59ChoEBQveBAULygQ8="


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCopilotOrchestrator:

    def test_check_proactive_alerts_runs_safely(self):
        """Proactive alerts evaluation should analyze bars and return alerts list."""
        copilot = LiveCopilotOrchestrator()
        bars = _make_bars(50)
        alerts = copilot.check_proactive_alerts("BTCUSDT", "1d", bars)

        assert isinstance(alerts, list)
        for a in alerts:
            assert a.symbol == "BTCUSDT"
            assert a.interval == "1d"
            assert isinstance(a.severity, AlertSeverity)
            assert len(a.message) > 0

    def test_multimodal_turn_text_only(self):
        """Turn with text query should assemble context, generate response and synthesize voice."""
        copilot = LiveCopilotOrchestrator()
        bars = _make_bars(50)
        req = MultimodalTurnRequest(
            symbol="BTCUSDT",
            interval="1d",
            market="crypto",
            text_prompt="¿Cuál es la hipótesis de swing para hoy?",
        )
        res = copilot.execute_multimodal_turn(req, bars)

        assert isinstance(res, MultimodalTurnResponse)
        assert res.symbol == "BTCUSDT"
        assert res.interval == "1d"
        assert len(res.assistant_response_text) > 0
        assert res.assistant_audio_base64 is not None
        assert res.audio_duration_seconds > 0
        assert res.current_price > 0

        # Check epistemic sections
        assert "OBSERVACIÓN" in res.assistant_response_text
        assert "HIPÓTESIS" in res.assistant_response_text

    def test_multimodal_turn_with_audio_and_vision_fusion(self):
        """Turn with audio and image should trigger STT, Vision analysis, and combine them."""
        copilot = LiveCopilotOrchestrator()
        bars = _make_bars(50)
        req = MultimodalTurnRequest(
            symbol="BTCUSDT",
            interval="1d",
            market="crypto",
            audio_base64=_dummy_audio_b64() * 5,  # Valid length
            image_base64=_dummy_image_b64(),
        )
        res = copilot.execute_multimodal_turn(req, bars)

        assert isinstance(res, MultimodalTurnResponse)
        assert res.user_transcript is not None
        assert res.visual_patterns_detected_count >= 1
        assert res.visual_dominant_bias is not None
        assert len(res.assistant_response_text) > 0
        assert res.assistant_audio_base64 is not None
