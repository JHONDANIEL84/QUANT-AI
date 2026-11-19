"""Contextual Chat API — Fase 10 QUANT AI.

Endpoints:
  POST /api/v1/chat/message  — Envía mensaje y recibe análisis contextualizado
  GET  /api/v1/chat/context  — Retorna el contexto cuantitativo estructurado actual
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from data_providers.manager import market_data_manager
from ai_engine.context.builder import build_chart_quantitative_context
from ai_engine.chat.service import chat_service

router = APIRouter(prefix="/chat", tags=["AI Contextual Chat"])


# ---------------------------------------------------------------------------
# Request & Response Models
# ---------------------------------------------------------------------------

class ChatMessageItem(BaseModel):
    role: str = Field(..., description="'user' o 'assistant'")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Pregunta o instrucción del operador")
    symbol: str = Field("BTCUSDT", description="Símbolo del gráfico activo")
    interval: str = Field("1d", description="Temporalidad del gráfico activo")
    market: str = Field("crypto", description="Mercado: crypto, stock, bvc")
    history: Optional[List[ChatMessageItem]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str
    symbol: str
    interval: str
    model: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_summary: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/message",
    response_model=ChatResponse,
    summary="Envía mensaje al asistente QUANT AI con contexto del gráfico",
    description=(
        "Ensambla en tiempo real el estado cuantitativo actual del gráfico activo "
        "(estructura, indicadores, SMC, liquidez, scanner) y retorna una respuesta "
        "con estricta separación epistémica: Hechos verificados vs Hipótesis con invalidación explícita."
    ),
)
async def post_chat_message(req: ChatRequest) -> ChatResponse:
    """Procesa el mensaje del usuario con inyección del contexto cuantitativo."""
    # 1. Obtener barras recientes para construir el contexto
    try:
        bars = await market_data_manager.get_historical_bars(
            symbol=req.symbol,
            interval=req.interval,
            limit=100,
        )
    except Exception as exc:
        bars = []

    # 2. Construir snapshot contextual cuantitativo
    context_data = build_chart_quantitative_context(
        symbol=req.symbol,
        interval=req.interval,
        bars=bars or [],
        market=req.market,
    )

    # 3. Formatear historial
    formatted_history = (
        [{"role": m.role, "content": m.content} for m in req.history]
        if req.history
        else []
    )

    # 4. Generar respuesta
    result = chat_service.generate_response(
        user_message=req.message,
        context_data=context_data,
        history=formatted_history,
    )

    return ChatResponse(
        response=result["response"],
        symbol=req.symbol.upper(),
        interval=req.interval,
        model=result["model"],
        source=result["source"],
        context_summary={
            "price": context_data.get("current_price"),
            "trend": context_data.get("trend"),
            "rsi": context_data.get("rsi"),
            "dealing_zone": context_data.get("dealing_zone"),
            "scanner_score": context_data.get("scanner_score"),
        },
    )


@router.get(
    "/context",
    summary="Obtiene snapshot del contexto cuantitativo del activo",
    description="Retorna el contexto técnico estructurado sin invocar generación de texto.",
)
async def get_chart_context(
    symbol: str = Query("BTCUSDT"),
    interval: str = Query("1d"),
    market: str = Query("crypto"),
) -> Dict[str, Any]:
    """Retorna el contexto cuantitativo ensamblado para el símbolo especificado."""
    try:
        bars = await market_data_manager.get_historical_bars(
            symbol=symbol,
            interval=interval,
            limit=100,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error obteniendo barras: {exc}")

    return build_chart_quantitative_context(
        symbol=symbol,
        interval=interval,
        bars=bars or [],
        market=market,
    )
