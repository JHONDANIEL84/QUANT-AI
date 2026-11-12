"""Unified Market Data Manager.
Orchestrates Yahoo Finance, Binance, BVC, and Macroeconomic providers through a single facade.
Follows Section 4.5 of QUANT AI specification.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from data_providers.base.base_provider import BaseMarketDataProvider
from data_providers.base.models import (
    MarketBar,
    MarketStatus,
    MarketType,
    DataStatus,
    TickerSnapshot,
    OrderBookDepth,
    CompanyInfo,
    MacroIndicator,
)
from data_providers.yahoo.yahoo_provider import YahooFinanceProvider, KNOWN_ETFS
from data_providers.binance.binance_provider import BinanceProvider
from data_providers.bvc.bvc_provider import BVCFileProvider
from data_providers.macro.macro_provider import MacroDataProvider

logger = logging.getLogger("quant_ai.providers.manager")

# Set of Colombian BVC symbols
KNOWN_BVC_SYMBOLS = {
    "ECOPETROL", "PFBCOLO", "BCOLOMBIA", "ISA", "GEB", "GRUPOAVAL", 
    "PFGRUPSURA", "GRUPOSURA", "NUTRESA", "CELSIA", "CORFICOLCF"
}

# Set of standard Crypto symbols
KNOWN_CRYPTO_SYMBOLS = {
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"
}


class MarketDataManager:
    """Central gateway routing financial requests to appropriate provider."""

    def __init__(
        self,
        bvc_data_path: str = "./data/bvc",
        fred_api_key: Optional[str] = None,
    ):
        self.yahoo = YahooFinanceProvider()
        self.binance = BinanceProvider()
        self.bvc = BVCFileProvider(data_path=bvc_data_path)
        self.macro = MacroDataProvider(fred_api_key=fred_api_key)

    def route_provider(self, symbol: str) -> BaseMarketDataProvider:
        """Determines best provider based on symbol conventions."""
        s = symbol.upper().replace("/", "").replace("-", "")

        # Check BVC
        if s in KNOWN_BVC_SYMBOLS or s.endswith(".BVC") or s.startswith("PF"):
            return self.bvc

        # Check Crypto
        if s in KNOWN_CRYPTO_SYMBOLS or s.endswith("USDT") or s.endswith("BUSD"):
            return self.binance

        # Default to Yahoo Finance for US Stocks and ETFs
        return self.yahoo

    async def get_historical_bars(
        self,
        symbol: str,
        interval: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 500,
    ) -> List[MarketBar]:
        """Fetch historical bars with automatic provider routing."""
        provider = self.route_provider(symbol)
        return await provider.get_historical_bars(
            symbol=symbol,
            interval=interval,
            start=start,
            end=end,
            limit=limit,
        )

    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """Fetch latest price from designated provider."""
        provider = self.route_provider(symbol)
        return await provider.get_latest_price(symbol)

    async def get_ticker_snapshot(self, symbol: str) -> Optional[TickerSnapshot]:
        """Fetch 24h ticker summary."""
        provider = self.route_provider(symbol)
        return await provider.get_ticker_snapshot(symbol)

    async def get_order_book(self, symbol: str, limit: int = 20) -> Optional[OrderBookDepth]:
        """Fetch order book depth if available (Crypto / Binance)."""
        provider = self.route_provider(symbol)
        if isinstance(provider, BinanceProvider):
            return await provider.get_order_book(symbol, limit=limit)
        return None

    async def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        """Fetch fundamental company info (Yahoo Finance)."""
        provider = self.route_provider(symbol)
        if isinstance(provider, YahooFinanceProvider):
            return await provider.get_company_info(symbol)
        return None

    async def get_macro_indicators(self, country: str = "CO") -> List[MacroIndicator]:
        """Fetch macroeconomic indicators."""
        return await self.macro.get_indicators_by_country(country)

    async def get_all_providers_status(self) -> List[MarketStatus]:
        """Query and consolidate operational health of all data providers."""
        statuses: List[MarketStatus] = []
        for p in [self.yahoo, self.binance, self.bvc]:
            try:
                st = await p.get_status()
                statuses.append(st)
            except Exception as e:
                statuses.append(
                    MarketStatus(
                        source=p.name,
                        is_connected=False,
                        data_status=DataStatus.INCOMPLETE,
                        last_update=datetime.now(),
                        latency_ms=0.0,
                        notes=f"Provider check failed: {str(e)}",
                    )
                )

        # Macro status
        try:
            macro_st = await self.macro.get_status()
            statuses.append(macro_st)
        except Exception as e:
            logger.error("Error checking macro provider: %s", str(e))

        return statuses


# Singleton instance for backend application
market_data_manager = MarketDataManager()
