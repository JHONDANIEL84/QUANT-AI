"""Data models for Japanese candlestick pattern recognition."""

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CandlePatternType(str, Enum):
    DOJI = "DOJI"
    HAMMER = "HAMMER"
    SHOOTING_STAR = "SHOOTING_STAR"
    BULLISH_ENGULFING = "BULLISH_ENGULFING"
    BEARISH_ENGULFING = "BEARISH_ENGULFING"
    PIN_BAR = "PIN_BAR"
    INSIDE_BAR = "INSIDE_BAR"
    OUTSIDE_BAR = "OUTSIDE_BAR"
    MARUBOZU = "MARUBOZU"
    MORNING_STAR = "MORNING_STAR"
    EVENING_STAR = "EVENING_STAR"


class CandlePatternDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class CandlePattern(BaseModel):
    """Normalized detected candlestick pattern with formal audit rules."""

    pattern_type: CandlePatternType
    direction: CandlePatternDirection
    timestamp: datetime = Field(description="Timestamp of pattern completion bar")
    bar_index: int
    price: float = Field(description="Trigger / close price of pattern")
    confirmed_at: datetime = Field(description="Time when bar officially closed")
    confidence: float = Field(ge=0.0, le=1.0, description="Algorithmic confidence score (0.0 to 1.0)")
    rule_applied: str = Field(description="Explicit mathematical rule applied")
    invalidation_level: Optional[float] = Field(default=None, description="Price level invalidating pattern hypothesis")
