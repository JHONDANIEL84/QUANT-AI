# ai_engine/speech_to_text — Fase 12 QUANT AI
from ai_engine.speech_to_text.models import (
    TranscriptionRequest,
    TranscriptionResponse,
)
from ai_engine.speech_to_text.transcriber import SpeechTranscriber, speech_transcriber

__all__ = [
    "TranscriptionRequest",
    "TranscriptionResponse",
    "SpeechTranscriber",
    "speech_transcriber",
]
