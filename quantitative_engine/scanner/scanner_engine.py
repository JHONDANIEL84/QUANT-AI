"""Market Universe Scanner Orchestrator — Phase 7 QUANT AI.

Executes screening sweeps across multi-asset universes (Crypto, US Stocks/ETFs, BVC Colombia),
filters opportunities by minimum score, and returns sorted ranking.
"""

from typing import List, Dict, Optional
from datetime import datetime

from data_providers.base.models import MarketBar
from quantitative_engine.scanner.models import (
    ScanOpportunity,
    MarketScanResponse,
    SetupDirection,
    ConvictionLevel,
)
from quantitative_engine.scanner.evaluator import evaluate_asset_opportunity

# Standard asset universes
CRYPTO_UNIVERSE = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]
STOCK_UNIVERSE = ["AAPL", "NVDA", "MSFT", "AMZN", "SPY", "QQQ"]
BVC_UNIVERSE = ["ECOPETROL", "PFBCOLO", "BCOLOMBIA", "ISA", "GEB"]


def scan_asset_bars_collection(
    bars_by_symbol: Dict[str, List[MarketBar]],
    market_filter: str = "all",
    interval: str = "1d",
    min_score: float = 50.0,
) -> MarketScanResponse:
    """Evaluates a pre-collected dictionary of bars by symbol.

    Args:
        bars_by_symbol: Dict mapping symbol -> List[MarketBar].
        market_filter: 'all', 'crypto', 'stock', or 'bvc'.
        interval: Bar timeframe.
        min_score: Minimum threshold to include an opportunity.

    Returns:
        MarketScanResponse with ranked opportunities.
    """
    opportunities: List[ScanOpportunity] = []
    total_scanned = 0

    for sym, bars in bars_by_symbol.items():
        total_scanned += 1

        # Determine market category
        s_upper = sym.upper()
        if s_upper.endswith("USDT") or s_upper in CRYPTO_UNIVERSE:
            mkt = "crypto"
        elif s_upper in BVC_UNIVERSE or s_upper.startswith("PF") or s_upper.endswith(".BVC"):
            mkt = "bvc"
        else:
            mkt = "stock"

        # Apply market filter
        if market_filter != "all" and mkt != market_filter.lower():
            continue

        opp = evaluate_asset_opportunity(
            symbol=s_upper,
            market=mkt,
            interval=interval,
            bars=bars,
        )

        if opp and opp.score >= min_score:
            opportunities.append(opp)

    # Sort descending by score
    opportunities.sort(key=lambda x: x.score, reverse=True)

    return MarketScanResponse(
        scan_name=f"Barrido Cuantitativo Multiactivo ({market_filter.upper()})",
        market_filter=market_filter,
        interval=interval,
        total_assets_scanned=total_scanned,
        opportunities_found=len(opportunities),
        min_score_applied=min_score,
        opportunities=opportunities,
        data_status="observation",
    )
