"""Data models for Market Scanner & Multi-Timeframe (MTF) Confluence — Phase 7 QUANT AI.

Defines:
  - Scanner Criteria & Filter enums
  - Opportunity Score and Setup Direction
  - MTF Confluence models (HTF vs LTF alignment)
  - Scanner Result item and Consolidated Scan Response
"""

from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SetupDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class ConvictionLevel(str, Enum):
    HIGH = "HIGH"          # Score >= 80
    MODERATE = "MODERATE"  # Score 60 - 79
    LOW = "LOW"            # Score < 60


class MTFConfluenceResult(BaseModel):
    """Multi-timeframe confluence between higher and lower timeframes."""

    symbol: str
    htf_interval: str = "1d"
    ltf_interval: str = "4h"
    htf_trend: str
    ltf_trend: str
    is_aligned: bool
    confluence_score: float = Field(ge=0.0, le=100.0)
    summary: str


class ScanOpportunity(BaseModel):
    """An individual scanned market opportunity with institutional evidence."""

    symbol: str
    market: str  # "crypto", "stock", "bvc", "etf"
    interval: str
    direction: SetupDirection
    conviction: ConvictionLevel
    score: float = Field(ge=0.0, le=100.0, description="Composite score (0-100)")
    current_price: float
    matched_criteria: List[str] = Field(default_factory=list)
    unmatched_criteria: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    invalidation_level: Optional[float] = None
    observation: str
    hypothesis: str
    scanned_at: datetime = Field(default_factory=datetime.utcnow)


class MarketScanResponse(BaseModel):
    """Response containing ranked scanner opportunities and execution metadata."""

    scan_name: str
    market_filter: str
    interval: str
    total_assets_scanned: int
    opportunities_found: int
    min_score_applied: float
    opportunities: List[ScanOpportunity] = Field(default_factory=list)
    data_status: str = "observation"
