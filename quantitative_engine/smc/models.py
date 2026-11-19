"""Data models for Smart Money Concepts (SMC) — Phase 5 QUANT AI.

Defines Pydantic models for:
  - BOS (Break of Structure) & CHOCH (Change of Character)
  - Order Blocks (Bullish, Bearish, Breakers) with mitigation status
  - Fair Value Gaps (FVG) with Consequent Encroachment (CE 50%) and mitigation
  - Premium & Discount Dealing Range (Equilibrium 50%)
  - Complete SMCAnalysis response
"""

from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SMCZoneType(str, Enum):
    BOS = "BOS"
    CHOCH = "CHOCH"
    ORDER_BLOCK = "ORDER_BLOCK"
    FVG = "FVG"
    BREAKER = "BREAKER"
    PREMIUM_DISCOUNT = "PREMIUM_DISCOUNT"


class SMCDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class MitigationStatus(str, Enum):
    UNMITIGATED = "UNMITIGATED"  # Fresh, untouched zone
    PARTIAL = "PARTIAL"          # Tested / partially mitigated
    MITIGATED = "MITIGATED"      # Fully mitigated / filled
    INVALIDATED = "INVALIDATED"  # Broken through (may become breaker)


class StructureBreak(BaseModel):
    """Represents a Break of Structure (BOS) or Change of Character (CHOCH)."""

    break_type: SMCZoneType = Field(description="BOS or CHOCH")
    direction: SMCDirection = Field(description="BULLISH or BEARISH")
    broken_pivot_price: float = Field(description="Price level of the broken swing pivot")
    breaking_bar_index: int = Field(description="Bar index where the break candle closed")
    breaking_bar_timestamp: datetime = Field(description="Timestamp when the break candle closed")
    breaking_price: float = Field(description="Close price of the breaking candle")
    invalidation_level: float = Field(description="Structural invalidation level")
    rule_applied: str = Field(description="Human-readable rule explaining the structural break")


class OrderBlock(BaseModel):
    """Institutional Order Block (OB).

    The last contrary candle immediately preceding a violent move that broke structure or created an FVG.
    """

    direction: SMCDirection = Field(description="BULLISH (demand) or BEARISH (supply)")
    bar_index: int = Field(description="Index of the order block candle")
    timestamp: datetime = Field(description="Timestamp of the order block candle")
    top_price: float = Field(description="High of the order block range")
    bottom_price: float = Field(description="Low of the order block range")
    body_top: float = Field(description="Max(open, close) of the order block candle")
    body_bottom: float = Field(description="Min(open, close) of the order block candle")
    status: MitigationStatus = Field(default=MitigationStatus.UNMITIGATED)
    mitigated_at: Optional[datetime] = None
    mitigated_bar_index: Optional[int] = None
    is_breaker: bool = Field(default=False, description="True if price blew through this block and flipped it")
    quality_score: float = Field(ge=0.0, le=100.0, description="Quality score based on volume, displacement and BOS")
    volume: float = Field(default=0.0)
    rule_applied: str


class FairValueGap(BaseModel):
    """Fair Value Gap (FVG) / Liquidity Imbalance.

    3-candle formation where a gap exists between candle 1 and candle 3 wicks.
    """

    direction: SMCDirection = Field(description="BULLISH or BEARISH")
    bar_index: int = Field(description="Index of the impulse candle (middle bar i-1)")
    timestamp: datetime = Field(description="Timestamp of the impulse candle")
    top_price: float = Field(description="Upper boundary of the gap")
    bottom_price: float = Field(description="Lower boundary of the gap")
    gap_size: float = Field(description="top_price - bottom_price")
    consequent_encroachment: float = Field(description="50% midpoint of the gap (CE)")
    status: MitigationStatus = Field(default=MitigationStatus.UNMITIGATED)
    mitigated_pct: float = Field(default=0.0, ge=0.0, le=100.0, description="Percentage of gap filled")
    mitigated_at: Optional[datetime] = None
    rule_applied: str


class PremiumDiscountRange(BaseModel):
    """Current dealing range divided into Premium, Equilibrium, and Discount."""

    swing_high: float
    swing_low: float
    equilibrium: float = Field(description="50% equilibrium level: (high + low) / 2")
    current_price: float
    current_position_pct: float = Field(
        description="Position in range: 0% = swing_low, 50% = equilibrium, 100% = swing_high"
    )
    zone: str = Field(description="'PREMIUM', 'EQUILIBRIUM', or 'DISCOUNT'")
    observation: str


class SMCAnalysis(BaseModel):
    """Complete Smart Money Concepts analysis result for a given asset and interval."""

    symbol: str
    interval: str
    bars_analyzed: int
    structure_breaks: List[StructureBreak] = Field(default_factory=list)
    order_blocks: List[OrderBlock] = Field(default_factory=list)
    fair_value_gaps: List[FairValueGap] = Field(default_factory=list)
    premium_discount: Optional[PremiumDiscountRange] = None
    observation: str = Field(description="Objective factual summary of active institutional zones")
    hypothesis: str = Field(description="Forward-looking hypothesis with invalidation criteria")
    data_status: str = "observation"
