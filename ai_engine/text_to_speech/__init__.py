# ai_engine/text_to_speech — Fase 12 QUANT AI
from ai_engine.text_to_speech.models import TTSRequest, TTSResponse
from ai_engine.text_to_speech.normalizer import normalize_text_for_speech
from ai_engine.text_to_speech.synthesizer import TextToSpeechSynthesizer, tts_synthesizer

__all__ = [
    "TTSRequest",
    "TTSResponse",
    "normalize_text_for_speech",
    "TextToSpeechSynthesizer",
    "tts_synthesizer",
]
