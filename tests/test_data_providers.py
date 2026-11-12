"""Unit and integration tests for QUANT AI Data Providers (Phase 2).
Verifies Yahoo Finance, Binance, BVC CSV, Macroeconomic providers, and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from data_providers.base.models import MarketType, DataStatus
from data_providers.yahoo.yahoo_provider import YahooFinanceProvider
from data_providers.binance.binance_provider import BinanceProvider
from data_providers.bvc.bvc_provider import BVCFileProvider
from data_providers.macro.macro_provider import MacroDataProvider
from data_providers.manager import MarketDataManager, market_data_manager

client = TestClient(app)


# -------------------------------------------------------------
# 1. YAHOO FINANCE PROVIDER TESTS
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_yahoo_provider_bars_normalization():
    provider = YahooFinanceProvider(cache_ttl_seconds=10)
    bars = await provider.get_historical_bars(symbol="AAPL", interval="1d", limit=10)
    assert len(bars) > 0
    bar = bars[-1]
    assert bar.symbol == "AAPL"
    assert bar.market == MarketType.STOCK
    assert bar.source == "yahoo"
    assert bar.interval == "1d"
    assert bar.high >= bar.low
    assert bar.open > 0
    assert bar.close > 0
    assert bar.data_status in [DataStatus.DELAYED, DataStatus.HISTORICAL]


@pytest.mark.asyncio
async def test_yahoo_provider_etf_classification():
    provider = YahooFinanceProvider(cache_ttl_seconds=10)
    bars = await provider.get_historical_bars(symbol="SPY", interval="1d", limit=5)
    assert len(bars) > 0
    assert bars[0].market == MarketType.ETF


@pytest.mark.asyncio
async def test_yahoo_provider_ticker_snapshot():
    provider = YahooFinanceProvider(cache_ttl_seconds=10)
    snapshot = await provider.get_ticker_snapshot("NVDA")
    assert snapshot is not None
    assert snapshot.symbol == "NVDA"
    assert snapshot.price > 0
    assert snapshot.currency == "USD"


# -------------------------------------------------------------
# 2. BINANCE PROVIDER TESTS
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_binance_provider_bars():
    provider = BinanceProvider(cache_ttl_seconds=10)
    bars = await provider.get_historical_bars(symbol="BTCUSDT", interval="1h", limit=10)
    assert len(bars) > 0
    bar = bars[-1]
    assert bar.symbol == "BTCUSDT"
    assert bar.market == MarketType.CRYPTO
    assert bar.source == "binance"
    assert bar.close > 0
    assert bar.high >= bar.low


@pytest.mark.asyncio
async def test_binance_provider_order_book_and_imbalance():
    provider = BinanceProvider(cache_ttl_seconds=10)
    ob = await provider.get_order_book(symbol="BTCUSDT", limit=10)
    assert ob is not None
    assert ob.symbol == "BTCUSDT"
    assert ob.source == "binance"
    assert len(ob.bids) > 0
    assert len(ob.asks) > 0
    assert ob.best_ask >= ob.best_bid
    assert ob.spread >= 0
    # Imbalance must be between -1.0 and 1.0
    assert -1.0 <= ob.imbalance_ratio <= 1.0


# -------------------------------------------------------------
# 3. BVC CSV PROVIDER TESTS
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_bvc_csv_parser_and_validation():
    provider = BVCFileProvider(data_path="./data/bvc")
    bars = await provider.get_historical_bars(symbol="ECOPETROL", interval="1d", limit=20)
    assert len(bars) > 0
    bar = bars[-1]
    assert bar.symbol == "ECOPETROL"
    assert bar.market == MarketType.STOCK
    assert bar.source == "bvc"
    assert bar.high >= bar.low
    assert bar.close > 1000.0  # COP expected in thousands


@pytest.mark.asyncio
async def test_bvc_ticker_snapshot():
    provider = BVCFileProvider(data_path="./data/bvc")
    snapshot = await provider.get_ticker_snapshot("PFBCOLO")
    assert snapshot is not None
    assert snapshot.symbol == "PFBCOLO"
    assert snapshot.currency == "COP"
    assert snapshot.price > 20000.0


# -------------------------------------------------------------
# 4. MACRO DATA PROVIDER TESTS
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_macro_provider_indicators():
    provider = MacroDataProvider()
    colombia_inds = await provider.get_indicators_by_country("CO")
    assert len(colombia_inds) >= 4

    codes = [i.indicator_code for i in colombia_inds]
    assert "POLICY_RATE" in codes
    assert "INFLATION_IPC" in codes
    assert "TRM_USD_COP" in codes

    us_inds = await provider.get_indicators_by_country("US")
    assert len(us_inds) >= 3
    us_codes = [i.indicator_code for i in us_inds]
    assert "FED_FUNDS_RATE" in us_codes


# -------------------------------------------------------------
# 5. UNIFIED MARKET DATA MANAGER ROUTING TESTS
# -------------------------------------------------------------
def test_market_manager_routing():
    manager = MarketDataManager()
    # Crypto routes to Binance
    assert manager.route_provider("BTCUSDT").name == "binance"
    assert manager.route_provider("ethusdt").name == "binance"

    # US Stocks and ETFs route to Yahoo
    assert manager.route_provider("AAPL").name == "yahoo"
    assert manager.route_provider("SPY").name == "yahoo"

    # Colombian Equities route to BVC
    assert manager.route_provider("ECOPETROL").name == "bvc"
    assert manager.route_provider("PFBCOLO").name == "bvc"


# -------------------------------------------------------------
# 6. FASTAPI API MARKET ENDPOINT TESTS
# -------------------------------------------------------------
def test_api_get_market_bars():
    res = client.get("/api/v1/market/bars?symbol=AAPL&interval=1d&limit=5")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["symbol"] == "AAPL"


def test_api_get_market_ticker():
    res = client.get("/api/v1/market/ticker?symbol=BTCUSDT")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "BTCUSDT"
    assert data["price"] > 0


def test_api_get_order_book():
    res = client.get("/api/v1/market/orderbook?symbol=BTCUSDT&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "BTCUSDT"
    assert "imbalance_ratio" in data
    assert len(data["bids"]) > 0


def test_api_get_macro():
    res = client.get("/api/v1/market/macro?country=CO")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    assert any(item["indicator_code"] == "TRM_USD_COP" for item in data)


def test_api_get_providers_status():
    res = client.get("/api/v1/market/providers")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    sources = [p["source"] for p in data]
    assert "yahoo" in sources
    assert "binance" in sources
    assert "bvc" in sources
