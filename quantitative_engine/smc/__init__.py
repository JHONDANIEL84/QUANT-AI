"""Smart Money Concepts (SMC) Module — Phase 5 QUANT AI."""

from quantitative_engine.smc.models import (
    SMCZoneType,
    SMCDirection,
    MitigationStatus,
    StructureBreak,
    OrderBlock,
    FairValueGap,
    PremiumDiscountRange,
    SMCAnalysis,
)
from quantitative_engine.smc.bos_choch import detect_structure_breaks
from quantitative_engine.smc.fvg import detect_fair_value_gaps
from quantitative_engine.smc.order_blocks import detect_order_blocks
from quantitative_engine.smc.premium_discount import compute_premium_discount
from quantitative_engine.smc.analyzer import run_smc_analysis

__all__ = [
    "SMCZoneType",
    "SMCDirection",
    "MitigationStatus",
    "StructureBreak",
    "OrderBlock",
    "FairValueGap",
    "PremiumDiscountRange",
    "SMCAnalysis",
    "detect_structure_breaks",
    "detect_fair_value_gaps",
    "detect_order_blocks",
    "compute_premium_discount",
    "run_smc_analysis",
]
