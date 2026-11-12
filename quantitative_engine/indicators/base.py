"""Base classes and typing for quantitative indicators."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class IndicatorPoint(BaseModel):
    """Single time-value pair for an indicator."""
    timestamp: datetime
    value: float


class MACDPoint(BaseModel):
    timestamp: datetime
    macd: float
    signal: float
    histogram: float


class BollingerPoint(BaseModel):
    timestamp: datetime
    upper: float
    middle: float
    lower: float
    bandwidth: float
    percent_b: float


class FibonacciLevels(BaseModel):
    high: float
    low: float
    is_uptrend: bool
    levels: Dict[str, float] = Field(
        description="Key is ratio (e.g. '0.236', '0.382', '0.5', '0.618', '0.786', '1.0'), value is price"
    )


class ComputedIndicatorsResponse(BaseModel):
    symbol: str
    interval: str
    timestamps: List[datetime]
    ema_20: Optional[List[Optional[float]]] = None
    ema_50: Optional[List[Optional[float]]] = None
    ema_100: Optional[List[Optional[float]]] = None
    ema_200: Optional[List[Optional[float]]] = None
    rsi_14: Optional[List[Optional[float]]] = None
    macd: Optional[List[Optional[MACDPoint]]] = None
    atr_14: Optional[List[Optional[float]]] = None
    vwap: Optional[List[Optional[float]]] = None
    bollinger_bands: Optional[List[Optional[BollingerPoint]]] = None
    fibonacci: Optional[FibonacciLevels] = None
