"""Live Assistant Copilot Models — Fase 13 QUANT AI.

Estructuras de datos para la orquestación multimodal unificada (Voz + Visión + Datos Cuantitativos)
y sistema de alertas proactivas en tiempo real.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CopilotMode(str, Enum):
    STANDBY = "standby"             # En espera
    MONITORING = "monitoring"       # Monitoreo continuo proactivo
    ALERT = "alert"                 # Alerta activa detectada
    INTERACTING = "interacting"     # Conversación activa en progreso


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    INVALIDATION_NEAR = "invalidation_near"       # Precio a < 1% del nivel de invalidación
    INVALIDATION_TRIGGERED = "invalidation_hit"   # Nivel de invalidación alcanzado
    OB_TESTED = "ob_tested"                       # Precio mitigando un Order Block activo
    LIQUIDITY_SWEPT = "liquidity_swept"           # Barrido de liquidez reciente
    MTF_DIVERGENCE = "mtf_divergence"             # Marco temporal menor contradice al mayor
    VOLATILITY_EXPANSION = "volatility_expansion" # Expansión anómala de ATR o volumen


# ---------------------------------------------------------------------------
# Copilot Alert & Turn Models
# ---------------------------------------------------------------------------

class CopilotAlert(BaseModel):
    """Alerta cuantitativa proactiva emitida por el copiloto."""
    alert_type: AlertType
    severity: AlertSeverity
    symbol: str
    interval: str
    message: str
    price_level: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MultimodalTurnRequest(BaseModel):
    """Solicitud de turno multimodal completo al copiloto."""
    symbol: str = Field("BTCUSDT", description="Símbolo del gráfico activo")
    interval: str = Field("1d", description="Temporalidad del gráfico activo")
    market: str = Field("crypto", description="Mercado: crypto, stock, bvc")

    # Modales opcionales (cualquiera o todos pueden combinarse)
    audio_base64: Optional[str] = Field(None, description="Audio de la pregunta del operador")
    image_base64: Optional[str] = Field(None, description="Captura del gráfico para análisis visual")
    text_prompt: Optional[str] = Field(None, description="Texto escrito de la pregunta o comando")

    history: Optional[List[Dict[str, str]]] = Field(default_factory=list)


class MultimodalTurnResponse(BaseModel):
    """Respuesta unificada del copiloto combinando todos los modales."""
    symbol: str
    interval: str
    mode: CopilotMode

    # Transcripción si hubo audio
    user_transcript: Optional[str] = None

    # Visión si hubo imagen
    visual_patterns_detected_count: int = 0
    visual_dominant_bias: Optional[str] = None

    # Respuesta estructurada del copiloto
    assistant_response_text: str
    assistant_audio_base64: Optional[str] = None
    audio_duration_seconds: float = 0.0

    # Alertas proactivas
    active_alerts: List[CopilotAlert] = Field(default_factory=list)

    # Estado cuantitativo del activo
    current_price: float
    trend: str
    dealing_zone: str
    scanner_score: Optional[float] = None

    timestamp: datetime = Field(default_factory=datetime.utcnow)
