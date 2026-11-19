"""Live Vision API — Fase 11 QUANT AI.

Endpoint:
  POST /api/v1/vision/analyze-frame — Analiza visualmente capturas o frames del gráfico
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from ai_engine.vision.models import (
    VisionAnalysisRequest,
    VisionAnalysisResponse,
)
from ai_engine.vision.analyzer import vision_analyzer

router = APIRouter(prefix="/vision", tags=["Live Vision"])


@router.post(
    "/analyze-frame",
    response_model=VisionAnalysisResponse,
    summary="Analiza frame o captura del gráfico con IA multimodal",
    description=(
        "Recibe una imagen base64 del gráfico (canvas, pantalla o archivo) y detecta "
        "patrones visuales, Order Blocks, mechas de barrido y soportes/resistencias. "
        "Genera bloques epistémicos estructurados: Hechos visuales verificados vs "
        "Hipótesis falsable con nivel explícito de invalidación."
    ),
)
def post_analyze_frame(req: VisionAnalysisRequest) -> VisionAnalysisResponse:
    """Procesa el frame visual utilizando Gemini Vision o el analizador heurístico fallback."""
    if not req.image_base64 or len(req.image_base64.strip()) < 50:
        raise HTTPException(
            status_code=422,
            detail="La imagen provista en 'image_base64' no es válida o está vacía.",
        )

    try:
        return vision_analyzer.analyze_frame(req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al analizar frame visual: {exc}")
