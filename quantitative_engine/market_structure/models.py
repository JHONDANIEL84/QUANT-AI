"""Market Structure Models (Pivots, HH, HL, LH, LL, and Trends)."""

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class StructureType(str, Enum):
    HH = "HH"  # Higher High
    HL = "HL"  # Higher Low
    LH = "LH"  # Lower High
    LL = "LL"  # Lower Low
    SWING_HIGH = "SWING_HIGH"
    SWING_LOW = "SWING_LOW"


class TrendDirection(str, Enum):
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    CONSOLIDATION = "CONSOLIDATION"


class StructurePivot(BaseModel):
    """Confirmed structural swing pivot."""

    bar_index: int
    timestamp: datetime = Field(description="Timestamp of the pivot bar itself")
    confirmed_at: datetime = Field(description="Timestamp when pivot was confirmed (t + k bars later, prevents lookahead bias)")
    price: float
    is_high: bool
    structure_type: StructureType
    rule_applied: str


class ConsolidationRange(BaseModel):
    top: float
    bottom: float
    mean: float
    duration_bars: int


class MarketStructureResult(BaseModel):
    """Complete structural market analysis."""

    trend: TrendDirection
    last_swing_high: Optional[float] = None
    last_swing_low: Optional[float] = None
    pivots: List[StructurePivot]
    consolidation: Optional[ConsolidationRange] = None
    summary: str
