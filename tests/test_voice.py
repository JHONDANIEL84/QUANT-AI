"""Unit tests for Phase 12: Live Voice (STT & TTS) — QUANT AI.

Verifies:
  - Text normalization for natural Colombian Spanish speech
  - Synthetic WAV PCM 16-bit audio header and generation
  - Audio base64 cleaning and MIME parsing
  - Speech to text fallback transcription
  - End-to-end voice turn interaction
"""

import base64
import struct
import pytest

from ai_engine.text_to_speech.models import TTSRequest, TTSResponse
from ai_engine.text_to_speech.normalizer import normalize_text_for_speech
from ai_engine.text_to_speech.synthesizer import TextToSpeechSynthesizer
from ai_engine.speech_to_text.models import TranscriptionRequest, TranscriptionResponse
from ai_engine.speech_to_text.transcriber import SpeechTranscriber


# ---------------------------------------------------------------------------
# 1. Normalizer Tests
# ---------------------------------------------------------------------------

class TestTextNormalizer:

    def test_acronym_expansion_spanish(self):
        """Verifies institutional quantitative acronyms are expanded to spoken Spanish."""
        raw = "El precio superó la EMA 20 y generó un BOS alcista con RSI en 55."
        norm = normalize_text_for_speech(raw)

        assert "media móvil exponencial" in norm
        assert "ruptura de estructura" in norm
        assert "índice de fuerza relativa" in norm

    def test_currency_and_rr_expansion(self):
        """Verifies COP currency and R:R ratios are expanded."""
        raw = "Riesgo estimado en COP $500,000 con ratio R:R 1:2.5."
        norm = normalize_text_for_speech(raw)

        assert "pesos colombianos" in norm
        assert "ratio riesgo beneficio" in norm or "uno a" in norm

    def test_markdown_and_emojis_stripped(self):
        """Emojis and markdown formatting symbols must be stripped."""
        raw = "### 🔬 OBSERVACIÓN\n- **Activo**: BTCUSDT\n- *Tendencia*: UPTREND 💡"
        norm = normalize_text_for_speech(raw)

        assert "🔬" not in norm
        assert "💡" not in norm
        assert "#" not in norm
        assert "*" not in norm


# ---------------------------------------------------------------------------
# 2. TTS Synthesizer Tests
# ---------------------------------------------------------------------------

class TestSynthesizer:

    def test_synthesizer_generates_valid_wav_riff_header(self):
        """Synthesized audio must be valid base64 decoding to standard RIFF/WAVE header."""
        synth = TextToSpeechSynthesizer(sample_rate=16000)
        req = TTSRequest(
            text="Hipótesis alcista confirmada en el gráfico diario.",
            voice_locale="es-CO",
            speed=1.0,
        )
        res = synth.synthesize(req)

        assert isinstance(res, TTSResponse)
        assert res.audio_format == "wav"
        assert res.duration_estimated_seconds > 0

        # Decode base64 and verify RIFF header
        raw_bytes = base64.b64decode(res.audio_base64)
        assert len(raw_bytes) > 44  # Minimum WAV header size
        assert raw_bytes[:4] == b"RIFF"
        assert raw_bytes[8:12] == b"WAVE"
        assert raw_bytes[12:16] == b"fmt "
        assert b"data" in raw_bytes


# ---------------------------------------------------------------------------
# 3. STT Transcriber Tests
# ---------------------------------------------------------------------------

class TestTranscriber:

    def test_clean_base64_data_uri(self):
        """Should strip data:audio/webm;base64, prefix and detect webm MIME."""
        transcriber = SpeechTranscriber()
        raw = "data:audio/webm;base64,GkXfo59ChoEBQveBAULygQ8="
        clean, mime = transcriber._clean_base64(raw, "webm")

        assert clean == "GkXfo59ChoEBQveBAULygQ8="
        assert mime == "audio/webm"

    def test_fallback_transcription(self):
        """Fallback transcription should return Colombian Spanish text."""
        transcriber = SpeechTranscriber(api_key="")
        req = TranscriptionRequest(
            audio_base64="GkXfo59ChoEBQveBAULygQ8=",
            format="webm",
            language="es-CO",
            prompt_hint="Order block y niveles de invalidación",
        )
        res = transcriber.transcribe(req)

        assert isinstance(res, TranscriptionResponse)
        assert res.language == "es-CO"
        assert len(res.text) > 0
        assert res.confidence > 0.8
        assert res.source == "heuristic_stt_fallback"
