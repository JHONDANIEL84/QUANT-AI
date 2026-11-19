"""Unit tests for Phase 10: Contextual AI Chat — QUANT AI.

Verifies:
  - Quantitative context builder from chart bars
  - Epistemic separation (Observation vs Hypothesis vs Risk in COP)
  - Chat service fallback when running offline/without API key
  - Prompt templates and user message injection
"""

from datetime import datetime, timedelta, timezone
from typing import List
import pytest

from data_providers.base.models import MarketBar
from ai_engine.context.builder import build_chart_quantitative_context
from ai_engine.chat.prompts import QUANT_AI_SYSTEM_PROMPT, build_chat_user_prompt
from ai_engine.chat.service import ChatService


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def _make_bars(n: int = 50) -> List[MarketBar]:
    bars = []
    base = 100.0
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(n):
        o = base + i * 1.5
        c = o + 1.0
        h = c + 1.0
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestContextBuilder:

    def test_build_context_with_valid_bars(self):
        """Context builder should extract indicators, structure, SMC and format Markdown."""
        bars = _make_bars(50)
        ctx = build_chart_quantitative_context("BTCUSDT", "1d", bars, market="crypto")

        assert ctx["symbol"] == "BTCUSDT"
        assert ctx["interval"] == "1d"
        assert ctx["current_price"] > 0
        assert "trend" in ctx
        assert "prompt_text" in ctx
        assert "ESTADO CUANTITATIVO DEL ACTIVO" in ctx["prompt_text"]
        assert "Estructura de Mercado" in ctx["prompt_text"]
        assert "Smart Money Concepts" in ctx["prompt_text"]

    def test_build_context_empty_bars_graceful(self):
        """Empty bars list should return fallback dict without crashing."""
        ctx = build_chart_quantitative_context("ETHUSDT", "1h", [], market="crypto")
        assert ctx["symbol"] == "ETHUSDT"
        assert "error" in ctx
        assert "Sin datos" in ctx["prompt_text"]


class TestPrompts:

    def test_system_prompt_rules(self):
        """System prompt must enforce COP, epistemic separation and no look-ahead."""
        assert "OBSERVACIÓN (HECHOS VERIFICADOS)" in QUANT_AI_SYSTEM_PROMPT
        assert "HIPÓTESIS (PROYECCIÓN CUANTITATIVA)" in QUANT_AI_SYSTEM_PROMPT
        assert "COP" in QUANT_AI_SYSTEM_PROMPT
        assert "America/Bogota" in QUANT_AI_SYSTEM_PROMPT
        assert "NO LOOK-AHEAD BIAS" in QUANT_AI_SYSTEM_PROMPT

    def test_build_chat_user_prompt(self):
        """User prompt combines user query with quantitative context."""
        msg = "¿Cuál es la estructura actual?"
        ctx_text = "Precio: 90000 | Tendencia: UPTREND"
        full = build_chat_user_prompt(msg, ctx_text)
        assert msg in full
        assert ctx_text in full
        assert "CONTEXTO EN TIEMPO REAL" in full


class TestChatService:

    def test_fallback_generates_epistemic_structure(self):
        """Deterministic expert fallback must always generate Observation, Hypothesis, and Risk in COP."""
        service = ChatService(api_key="")  # force fallback
        bars = _make_bars(50)
        ctx = build_chart_quantitative_context("BTCUSDT", "1d", bars)

        result = service.generate_response(
            user_message="Evalúa una oportunidad de swing trade",
            context_data=ctx,
        )

        assert "response" in result
        assert result["source"] == "quantitative_expert_system"
        resp = result["response"]

        # Check required epistemic sections
        assert "### 🔬 OBSERVACIÓN" in resp
        assert "### 💡 HIPÓTESIS" in resp
        assert "### 🛡️ GESTIÓN DE RIESGO EN COP" in resp

        # Check directional fields
        assert "Nivel de Invalidación" in resp
        assert "Ratio Riesgo:Recompensa" in resp or "Recomendación Cuantitativa" in resp

    def test_fallback_no_context(self):
        """Without context, assistant instructs operator to select an asset."""
        service = ChatService(api_key="")
        result = service.generate_response("Hola", context_data={})
        resp = result["response"]
        assert "OBSERVACIÓN" in resp
        assert "HIPÓTESIS" in resp
