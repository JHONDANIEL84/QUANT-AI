"""System health and status schemas."""

from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime


class ServiceHealth(BaseModel):
    name: str
    status: str = Field(description="'healthy', 'degraded', or 'unreachable'")
    latency_ms: float = 0.0
    details: str = ""


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    app_name: str = "QUANT AI"
    timestamp: datetime
    timezone: str = "America/Bogota"
    currency: str = "COP"
    environment: str = "development"


class SystemStatusResponse(BaseModel):
    status: str = "operational"
    timestamp: datetime
    timezone: str = "America/Bogota"
    default_currency: str = "COP"
    services: List[ServiceHealth]
    capabilities: Dict[str, bool] = Field(
        default_factory=lambda: {
            "market_data_yahoo": True,
            "market_data_binance": True,
            "market_data_bvc": True,
            "market_data_macro": True,
            "quantitative_engine": True,
            "liquidity_intelligence": True,
            "ai_engine": True,
            "live_vision": True,
            "live_voice": True,
        }
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
