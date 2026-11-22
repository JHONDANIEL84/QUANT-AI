"""Live Voice API — Fase 12 QUANT AI.

Endpoints:
  POST /api/v1/voice/transcribe — Convierte audio de voz a texto (STT)
  POST /api/v1/voice/synthesize — Sintetiza texto analítico a audio (TTS)
  POST /api/v1/voice/interact   — Turno bidireccional completo (Audio -> Análisis -> Audio)
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from data_providers.manager import market_data_manager
from ai_engine.speech_to_text.models import (
    TranscriptionRequest,
    TranscriptionResponse,
)
from ai_engine.speech_to_text.transcriber import speech_transcriber
from ai_engine.text_to_speech.models import (
    TTSRequest,
    TTSResponse,
)
from ai_engine.text_to_speech.synthesizer import tts_synthesizer
from ai_engine.context.builder import build_chart_quantitative_context
from ai_engine.chat.service import chat_service

router = APIRouter(prefix="/voice", tags=["Live Voice"])


# ---------------------------------------------------------------------------
# Interaction Models
# ---------------------------------------------------------------------------

class VoiceInteractionRequest(BaseModel):
    """Solicitud de conversación bidireccional por voz."""
    audio_base64: str = Field(..., description="Audio de la pregunta del operador")
    audio_format: str = Field("webm", description="Formato del audio: webm, wav, mp3")
    symbol: str = Field("BTCUSDT", description="Símbolo del gráfico activo")
    interval: str = Field("1d", description="Temporalidad del gráfico activo")
    market: str = Field("crypto", description="Mercado: crypto, stock, bvc")
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list)


class VoiceInteractionResponse(BaseModel):
    """Respuesta de la conversación bidireccional por voz."""
    user_transcript: str = Field(..., description="Transcripción reconocida de la voz del usuario")
    assistant_text: str = Field(..., description="Respuesta cuantitativa estructurada generada")
    assistant_audio_base64: str = Field(..., description="Audio sintetizado de la respuesta en base64 (WAV)")
    audio_duration_seconds: float = Field(..., description="Duración estimada del audio")
    symbol: str
    interval: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe audio de voz a texto (STT)",
    description="Convierte grabaciones de audio a texto en español de Colombia.",
)
def post_transcribe(req: TranscriptionRequest) -> TranscriptionResponse:
    if not req.audio_base64 or len(req.audio_base64.strip()) < 10:
        raise HTTPException(status_code=422, detail="Audio base64 inválido o vacío.")
    try:
        return speech_transcriber.transcribe(req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al transcribir audio: {exc}")


@router.post(
    "/synthesize",
    response_model=TTSResponse,
    summary="Sintetiza texto a voz (TTS)",
    description="Normaliza texto financiero y genera audio WAV reproducible.",
)
def post_synthesize(req: TTSRequest) -> TTSResponse:
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="El texto a sintetizar no puede estar vacío.")
    try:
        return tts_synthesizer.synthesize(req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al sintetizar voz: {exc}")


@router.post(
    "/interact",
    response_model=VoiceInteractionResponse,
    summary="Interacción de voz completa bidireccional",
    description="Transcribe la pregunta en audio del operador, ejecuta el análisis contextual y retorna tanto texto como audio sintetizado.",
)
async def post_voice_interact(req: VoiceInteractionRequest) -> VoiceInteractionResponse:
    # 1. Transcribir audio de entrada
    transcribe_req = TranscriptionRequest(
        audio_base64=req.audio_base64,
        format=req.audio_format,
        language="es-CO",
        prompt_hint=f"{req.symbol} {req.interval} swing trading order blocks",
    )
    stt_res = speech_transcriber.transcribe(transcribe_req)
    user_text = stt_res.text

    # 2. Obtener contexto cuantitativo del gráfico
    try:
        bars = await market_data_manager.get_historical_bars(
            symbol=req.symbol,
            interval=req.interval,
            limit=100,
        )
    except Exception:
        bars = []

    context_data = build_chart_quantitative_context(
        symbol=req.symbol,
        interval=req.interval,
        bars=bars or [],
        market=req.market,
    )

    # 3. Generar respuesta analítica
    chat_res = chat_service.generate_response(
        user_message=user_text,
        context_data=context_data,
        history=req.history,
    )
    assistant_text = chat_res["response"]

    # 4. Sintetizar respuesta en audio
    tts_req = TTSRequest(
        text=assistant_text,
        voice_locale="es-CO",
        speed=1.0,
    )
    tts_res = tts_synthesizer.synthesize(tts_req)

    return VoiceInteractionResponse(
        user_transcript=user_text,
        assistant_text=assistant_text,
        assistant_audio_base64=tts_res.audio_base64,
        audio_duration_seconds=tts_res.duration_estimated_seconds,
        symbol=req.symbol.upper(),
        interval=req.interval,
        source=chat_res["source"],
    )
