"""Standardized financial market data models."""

from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


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
    """Standard normalized OHLCV bar across all providers.
    Follows Section 4.5 of QUANT AI specification.
    """

    symbol: str = Field(description="Ticker symbol, e.g., AAPL, BTCUSDT, ECOPETROL")
    market: MarketType = Field(description="Market classification")
    timestamp: datetime = Field(description="Bar open or close timestamp in UTC")
    open: float = Field(ge=0, description="Opening price")
    high: float = Field(ge=0, description="Highest price during bar interval")
    low: float = Field(ge=0, description="Lowest price during bar interval")
    close: float = Field(ge=0, description="Closing price")
    volume: float = Field(ge=0, description="Traded volume during bar interval")
    source: str = Field(description="Data provider source, e.g., 'yahoo', 'binance', 'bvc'")
    interval: str = Field(description="Timeframe interval, e.g., '1m', '5m', '1h', '1d', '1w'")
    downloaded_at: datetime = Field(description="Timestamp when data was retrieved")
    data_status: DataStatus = Field(default=DataStatus.HISTORICAL, description="Data state")

    trades_count: Optional[int] = Field(default=None, description="Number of trades in bar if provided")
    quote_volume: Optional[float] = Field(default=None, description="Traded quote asset volume if provided")
    is_closed: bool = Field(default=True, description="Whether the candle is confirmed and closed")


class MarketStatus(BaseModel):
    """Real-time provider connectivity and delay tracking."""

    source: str
    symbol: str
    is_connected: bool
    data_status: DataStatus
    last_update: datetime
    latency_ms: float = 0.0
    notes: Optional[str] = None
