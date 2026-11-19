"""Market Structure module."""

from quantitative_engine.market_structure.models import (
    StructureType,
    TrendDirection,
    StructurePivot,
    ConsolidationRange,
    MarketStructureResult,
)
from quantitative_engine.market_structure.swings import detect_market_structure

__all__ = [
    "StructureType",
    "TrendDirection",
    "StructurePivot",
    "ConsolidationRange",
    "MarketStructureResult",
    "detect_market_structure",
]
