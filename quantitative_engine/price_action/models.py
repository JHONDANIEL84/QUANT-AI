"""Data models for Price Action analysis."""

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class ZoneType(str, Enum):
    SUPPORT = "SUPPORT"
    RESISTANCE = "RESISTANCE"
    SUPPLY = "SUPPLY"
    DEMAND = "DEMAND"


class ZoneStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TESTED = "TESTED"
    BROKEN = "BROKEN"
    RETESTED = "RETESTED"


class PriceActionZone(BaseModel):
    """Identified key price action horizontal zone."""

    zone_type: ZoneType
    price_level: float = Field(description="Center / median price of the zone")
    top_price: float
    bottom_price: float
    touches: int = Field(ge=1, description="Number of independent price reactions at this zone")
    strength: float = Field(ge=0.0, le=1.0, description="Calculated strength based on touches and volume")
    status: ZoneStatus = ZoneStatus.ACTIVE
    invalidation_level: float = Field(description="Level beyond which this zone is invalidated")
    evidence: str = Field(description="Observable factual evidence justifying the zone")


class PriceActionEventType(str, Enum):
    BREAKOUT = "BREAKOUT"
    FAKEOUT = "FAKEOUT"
    PULLBACK = "PULLBACK"
    RETEST = "RETEST"
    REJECTION = "REJECTION"
    COMPRESSION = "COMPRESSION"
    EXPANSION = "EXPANSION"


class PriceActionEvent(BaseModel):
    """Dynamic price action event with rule and hypothesis."""

    event_type: PriceActionEventType
    timestamp: datetime
    price: float
    description: str
    rule_applied: str
    invalidation_criteria: str
    is_confirmed: bool = True


class PriceActionAnalysis(BaseModel):
    """Consolidated price action scan result."""

    zones: List[PriceActionZone]
    events: List[PriceActionEvent]
    is_compressed: bool = False
    observation: str
    hypothesis: str
