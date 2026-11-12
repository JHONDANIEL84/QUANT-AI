"""Standardized financial market data models across all providers.
Follows Section 4 and 4.5 of QUANT AI specification.
"""

from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class MarketType(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    CRYPTO = "crypto"
    FOREX = "forex"
    INDEX = "index"
    MACRO = "macro"


class DataStatus(str, Enum):
    REALTIME = "realtime"
    DELAYED = "delayed"
    HISTORICAL = "historical"
    PROVISIONAL = "provisional"
    INCOMPLETE = "incomplete"


class MarketBar(BaseModel):
    """Standard normalized OHLCV bar across all providers."""

    symbol: str = Field(description="Ticker symbol, e.g., AAPL, BTCUSDT, ECOPETROL")
    market: MarketType = Field(description="Market classification")
    timestamp: datetime = Field(description="Bar timestamp in UTC")
    open: float = Field(ge=0, description="Opening price")
    high: float = Field(ge=0, description="Highest price during bar interval")
    low: float = Field(ge=0, description="Lowest price during bar interval")
    close: float = Field(ge=0, description="Closing price")
    volume: float = Field(ge=0, description="Traded volume during bar interval")
    source: str = Field(description="Data provider source: 'yahoo', 'binance', 'bvc'")
    interval: str = Field(description="Timeframe interval, e.g., '1m', '5m', '15m', '1h', '4h', '1d', '1w'")
    downloaded_at: datetime = Field(description="Timestamp when data was retrieved")
    data_status: DataStatus = Field(default=DataStatus.HISTORICAL, description="Data state")

    trades_count: Optional[int] = Field(default=None, description="Number of trades in bar if available")
    quote_volume: Optional[float] = Field(default=None, description="Traded quote asset volume if available")
    is_closed: bool = Field(default=True, description="Whether candle is confirmed and closed")


class MarketStatus(BaseModel):
    """Real-time provider connectivity, latency, and operational health."""

    source: str
    symbol: Optional[str] = None
    is_connected: bool
    data_status: DataStatus
    last_update: datetime
    latency_ms: float = 0.0
    notes: Optional[str] = None


class TickerSnapshot(BaseModel):
    """Real-time / latest price snapshot for a financial instrument."""

    symbol: str
    market: MarketType
    price: float
    change_24h: float = 0.0
    change_24h_percent: float = 0.0
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    source: str
    data_status: DataStatus
    timestamp: datetime
    currency: str = "USD"


class OrderBookLevel(BaseModel):
    """Single price level in order book."""

    price: float
    quantity: float


class OrderBookDepth(BaseModel):
    """Order book snapshot with depth, spread and imbalance ratio."""

    symbol: str
    source: str
    timestamp: datetime
    best_bid: float
    best_ask: float
    spread: float
    spread_percentage: float
    imbalance_ratio: float = Field(
        description="Imbalance: (BidVol - AskVol) / (BidVol + AskVol). Positive = bid dominant, Negative = ask dominant."
    )
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    total_bid_volume: float
    total_ask_volume: float
    data_status: DataStatus = DataStatus.REALTIME


class PublicTrade(BaseModel):
    """Public execution trade in market."""

    id: str
    symbol: str
    price: float
    quantity: float
    timestamp: datetime
    is_buyer_maker: bool
    source: str


class CompanyInfo(BaseModel):
    """Corporate fundamentals and metadata."""

    symbol: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: str = "USD"
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    dividend_yield: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    description: Optional[str] = None
    source: str = "yahoo"
    downloaded_at: datetime


class MacroIndicator(BaseModel):
    """Macroeconomic data point."""

    country: str  # 'CO' (Colombia), 'US' (Estados Unidos)
    indicator_code: str  # 'INFLATION_IPC', 'POLICY_RATE', 'UNEMPLOYMENT', 'GDP', 'TRM_USD_COP'
    name: str
    value: float
    unit: str  # '%', 'COP/USD', 'Index'
    period: str  # '2024-Q3', '2024-10'
    publication_date: datetime
    source: str  # 'banrep', 'dane', 'fred'
    is_official: bool = True
