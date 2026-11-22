"""Text to Speech (TTS) Models — Fase 12 QUANT AI.

Estructuras de datos para síntesis de voz en español (Colombia).
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """Solicitud de síntesis de voz."""
    text: str = Field(..., min_length=1, description="Texto a sintetizar en audio")
    voice_locale: str = Field("es-CO", description="Acento/idioma: es-CO (Colombia)")
    voice_gender: str = Field("neutral", description="'female', 'male' o 'neutral'")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Velocidad de reproducción (0.5x a 2.0x)")
    audio_format: str = Field("wav", description="Formato de audio de salida: 'wav' o 'mp3'")


class TTSResponse(BaseModel):
    """Resultado de la síntesis de voz."""
    audio_base64: str = Field(..., description="Audio sintetizado en base64")
    audio_format: str = Field("wav", description="Formato de audio: 'wav'")
    duration_estimated_seconds: float = Field(..., ge=0, description="Duración estimada en segundos")
    cleaned_text: str = Field(..., description="Texto normalizado fonéticamente para lectura")
    source: str = Field(..., description="'tts_synthesizer' o 'browser_tts_recommended'")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
