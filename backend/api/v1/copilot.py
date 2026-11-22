"""Live Assistant Copilot API — Fase 13 QUANT AI.

Endpoints:
  POST /api/v1/copilot/turn   — Ejecuta turno multimodal completo (Voz + Visión + Datos)
  GET  /api/v1/copilot/alerts — Evalúa alertas cuantitativas proactivas en tiempo real
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException, Query
from data_providers.manager import market_data_manager
from ai_engine.orchestration.models import (
    MultimodalTurnRequest,
    MultimodalTurnResponse,
    CopilotAlert,
)
from ai_engine.orchestration.copilot import live_copilot

router = APIRouter(prefix="/copilot", tags=["Live Copilot Assistant"])


@router.post(
    "/turn",
    response_model=MultimodalTurnResponse,
    summary="Ejecuta turno multimodal unificado del Copiloto",
    description=(
        "Fusión síncrona en un solo ciclo: recibe audio (STT), captura visual del gráfico "
        "y contexto cuantitativo. Evalúa alertas proactivas, formula respuesta analítica "
        "con disciplina epistémica y sintetiza audio de respuesta (TTS)."
    ),
)
async def post_copilot_turn(req: MultimodalTurnRequest) -> MultimodalTurnResponse:
    try:
        bars = await market_data_manager.get_historical_bars(
            symbol=req.symbol,
            interval=req.interval,
            limit=100,
        )
    except Exception:
        bars = []

    if not bars:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudieron obtener datos de mercado para '{req.symbol}'.",
        )

    try:
        return live_copilot.execute_multimodal_turn(req, bars)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error en orquestación del copiloto: {exc}")


@router.get(
    "/alerts",
    response_model=List[CopilotAlert],
    summary="Monitoreo de alertas proactivas en tiempo real",
    description="Evalúa si el precio actual ha mitigado un Order Block, barrido liquidez o está cerca de invalidación.",
)
async def get_copilot_alerts(
    symbol: str = Query("BTCUSDT"),
    interval: str = Query("1d"),
    market: str = Query("crypto"),
) -> List[CopilotAlert]:
    try:
        bars = await market_data_manager.get_historical_bars(
            symbol=symbol,
            interval=interval,
            limit=100,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error al obtener datos: {exc}")

    if not bars:
        return []

    return live_copilot.check_proactive_alerts(symbol, interval, bars, market)
