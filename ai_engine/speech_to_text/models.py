"""Speech to Text (STT) Models — Fase 12 QUANT AI.

Estructuras de datos para transcripción de audio en español (Colombia).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TranscriptionRequest(BaseModel):
    """Solicitud de transcripción de audio."""
    audio_base64: str = Field(..., description="Audio codificado en base64 (WAV, MP3, WebM, OGG)")
    format: str = Field("webm", description="Formato del contenedor de audio: webm, wav, mp3, ogg")
    language: str = Field("es-CO", description="Código de idioma objetivo (default es-CO para Colombia)")
    prompt_hint: Optional[str] = Field(
        None,
        description="Pistas de vocabulario financiero (ej. 'Order Block, FVG, Stop Loss, COP')",
    )


class TranscriptionResponse(BaseModel):
    """Resultado de la transcripción de audio."""
    text: str = Field(..., description="Texto transcrito en español")
    language: str = Field("es-CO", description="Idioma detectado o utilizado")
    duration_seconds: float = Field(..., ge=0, description="Duración estimada del audio en segundos")
    confidence: float = Field(..., ge=0, le=1.0, description="Nivel de confianza en la transcripción (0 a 1)")
    source: str = Field(..., description="Motor utilizado: 'gemini_stt' o 'heuristic_stt_fallback'")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
