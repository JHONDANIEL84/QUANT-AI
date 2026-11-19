"""Data models for Liquidity Intelligence & Sweeps — Phase 6 QUANT AI.

Defines:
  - Equal Highs (EQH) & Equal Lows (EQL)
  - Buy-side (BSL) & Sell-side (SSL) Liquidity Pools
  - Liquidity Sweeps / Hunts with confirmed rejection
  - Previous Day / Week Levels (PDH, PDL, PWH, PWL)
  - Liquidity Scoring & Master Analysis Response
"""

from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class LiquidityType(str, Enum):
    EQH = "EQH"  # Equal Highs (Buy-side Liquidity pool)
    EQL = "EQL"  # Equal Lows (Sell-side Liquidity pool)
    BSL = "BSL"  # Buy-side Liquidity (Swing High stops)
    SSL = "SSL"  # Sell-side Liquidity (Swing Low stops)
    PDH = "PDH"  # Previous Day High
    PDL = "PDL"  # Previous Day Low
    PWH = "PWH"  # Previous Week High
    PWL = "PWL"  # Previous Week Low


class SweepStatus(str, Enum):
    ACTIVE = "ACTIVE"        # Liquidity pool untouched, resting stops present
    SWEPT = "SWEPT"          # Wick penetrated level and candle closed inside (confirmed sweep)
    EXPANDED = "EXPANDED"    # Closed through level (trend continuation, not a sweep)


class LiquidityPool(BaseModel):
    """Institutional Liquidity Pool representing clustered stops or equal levels."""

    pool_type: LiquidityType
    price_level: float = Field(description="Nominal anchor price of the liquidity pool")
    top_price: float = Field(description="Upper boundary of the liquidity zone")
    bottom_price: float = Field(description="Lower boundary of the liquidity zone")
    touch_count: int = Field(default=2, description="Number of touches within tolerance")
    first_touch_at: datetime
    last_touch_at: datetime
    liquidity_score: float = Field(ge=0.0, le=100.0, description="Score based on touches, volume, and importance")
    status: SweepStatus = Field(default=SweepStatus.ACTIVE)
    swept_at: Optional[datetime] = None
    swept_bar_index: Optional[int] = None
    sweep_penetration_pct: float = Field(default=0.0, description="Percentage penetrated past level during sweep")
    rule_applied: str


class LiquiditySweepEvent(BaseModel):
    """Confirmed liquidity sweep / stop hunt event."""

    pool_type: LiquidityType
    price_level: float = Field(description="The swept liquidity pool price")
    sweep_bar_index: int
    sweep_timestamp: datetime
    penetration_price: float = Field(description="Extreme price reached by the wick during the sweep")
    rejection_close: float = Field(description="Close price showing institutional rejection")
    penetration_pct: float = Field(description="Relative penetration percentage")
    invalidation_level: float = Field(description="Extreme of the sweep candle (SL anchor)")
    rule_applied: str


class SessionLevels(BaseModel):
    """Key macroeconomic and timeframe session benchmarks."""

    pdh: Optional[float] = Field(default=None, description="Previous Day High")
    pdl: Optional[float] = Field(default=None, description="Previous Day Low")
    pwh: Optional[float] = Field(default=None, description="Previous Week High")
    pwl: Optional[float] = Field(default=None, description="Previous Week Low")


class LiquidityAnalysis(BaseModel):
    """Complete Liquidity Intelligence and Sweeps analysis for an asset."""

    symbol: str
    interval: str
    bars_analyzed: int
    pools: List[LiquidityPool] = Field(default_factory=list)
    sweeps: List[LiquiditySweepEvent] = Field(default_factory=list)
    session_levels: SessionLevels
    observation: str = Field(description="Objective, factual summary of liquidity pools and sweeps")
    hypothesis: str = Field(description="Actionable forward-looking hypothesis with invalidation criteria")
    data_status: str = "observation"
