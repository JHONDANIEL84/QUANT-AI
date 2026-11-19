"""Live Vision Models — Fase 11 QUANT AI.

Estructuras de datos para análisis visual multimodal de gráficos financieros,
detección de patrones chartistas, anotaciones y correlación cuantitativa.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VisualPatternCategory(str, Enum):
    CHART_PATTERN = "chart_pattern"           # Hombro-Cabeza-Hombro, Doble Techo/Suelo, Triángulo, Bandera
    CANDLESTICK = "candlestick"               # Pinbar, Envolvente, Doji, Martillo
    MARKET_STRUCTURE = "market_structure"     # Swing High, Swing Low, Rango lateral
    SMC_ZONE = "smc_zone"                     # Order Block visual, FVG / Desequilibrio visual
    LIQUIDITY_ZONE = "liquidity_zone"         # Equal Highs, Equal Lows, Mechas de barrido


class VisualBias(str, Enum):
    BULLISH = "alcista"
    BEARISH = "bajista"
    NEUTRAL = "neutral"


# ---------------------------------------------------------------------------
# Detected Pattern & Annotations
# ---------------------------------------------------------------------------

class VisualBoundingBox(BaseModel):
    """Coordenadas normalizadas [0, 1] o píxeles de una zona detectada en el gráfico."""
    ymin: float = Field(..., ge=0, le=1)
    xmin: float = Field(..., ge=0, le=1)
    ymax: float = Field(..., ge=0, le=1)
    xmax: float = Field(..., ge=0, le=1)


class DetectedVisualPattern(BaseModel):
    """Patrón visual identificado en la captura del gráfico."""
    name: str = Field(..., description="Nombre del patrón (ej. 'Order Block Alcista', 'Doble Suelo', 'Barrido de Liquidez')")
    category: VisualPatternCategory
    bias: VisualBias
    confidence: float = Field(..., ge=0, le=1, description="Nivel de confianza visual (0.0 a 1.0)")
    bounding_box: Optional[VisualBoundingBox] = None
    price_level_approx: Optional[float] = Field(None, description="Precio aproximado asociado a la zona si es legible")
    description: str = Field(..., description="Descripción detallada de la observación visual")


# ---------------------------------------------------------------------------
# Request & Response
# ---------------------------------------------------------------------------

class VisionAnalysisRequest(BaseModel):
    """Entrada para análisis visual multimodal de un frame del gráfico."""
    image_base64: str = Field(..., description="Imagen del gráfico en formato base64 (PNG o JPEG)")
    symbol: Optional[str] = Field("BTCUSDT", description="Símbolo del activo en el gráfico")
    interval: Optional[str] = Field("1d", description="Temporalidad del gráfico")
    custom_prompt: Optional[str] = Field(
        None,
        description="Pregunta específica o enfoque del operador (ej. '¿Detectas un Order Block alcista?')",
    )


class VisionAnalysisResponse(BaseModel):
    """Resultado del análisis multimodal de visión."""
    symbol: str
    interval: str
    dominant_bias: VisualBias
    patterns_detected: List[DetectedVisualPattern] = Field(default_factory=list)

    # Bloques epistémicos
    observation: str = Field(..., description="🔬 OBSERVACIÓN: Hechos visuales verificados en la imagen del gráfico")
    hypothesis: str = Field(..., description="💡 HIPÓTESIS: Proyección del patrón detectado con niveles cuantitativos")
    risk_guidance: str = Field(..., description="🛡️ RIESGO EN COP: Reglas de invalidación y gestión de capital")

    source: str = Field(..., description="'gemini_vision' o 'quantitative_vision_engine'")
    model: str = Field(..., description="Modelo utilizado para el análisis")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
