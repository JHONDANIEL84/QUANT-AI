"""Abstract Base Market Data Provider.
Guarantees consistent, normalized data extraction across Yahoo Finance, Binance, BVC, and Macro sources.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from data_providers.base.models import MarketBar, MarketStatus, TickerSnapshot


class BaseMarketDataProvider(ABC):
    """Abstract interface that all data providers must implement."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def get_historical_bars(
        self,
        symbol: str,
        interval: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 500,
    ) -> List[MarketBar]:
        """Fetch historical normalized OHLCV bars."""
        pass

    @abstractmethod
    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest available trade price for a symbol."""
        pass

    @abstractmethod
    async def get_ticker_snapshot(self, symbol: str) -> Optional[TickerSnapshot]:
        """Get 24h ticker summary (price, change, high, low, volume)."""
        pass

    @abstractmethod
    async def get_status(self) -> MarketStatus:
        """Report connectivity, latency, and operational health."""
        pass
