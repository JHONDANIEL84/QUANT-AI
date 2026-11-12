"""Unit and integration tests for FastAPI backend routes using TestClient."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.config import settings
from data_providers.base.models import MarketBar, MarketType, DataStatus
from datetime import datetime, timezone

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "QUANT AI"
    assert data["status"] == "online"
    assert "version" in data


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["timezone"] == "America/Bogota"
    assert data["currency"] == "COP"
    assert "timestamp" in data


def test_system_status_endpoint():
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert len(data["services"]) > 0
    service_names = [s["name"] for s in data["services"]]
    assert "quantitative_engine" in service_names
    assert "liquidity_intelligence" in service_names
    assert "provider_binance" in service_names
    assert "provider_yahoo" in service_names


def test_market_bar_normalization():
    """Verify that MarketBar model validates required financial fields."""
    now = datetime.now(timezone.utc)
    bar = MarketBar(
        symbol="BTCUSDT",
        market=MarketType.CRYPTO,
        timestamp=now,
        open=90000.0,
        high=91500.0,
        low=89500.0,
        close=91000.0,
        volume=1254.55,
        source="binance",
        interval="1h",
        downloaded_at=now,
        data_status=DataStatus.REALTIME,
    )

    assert bar.symbol == "BTCUSDT"
    assert bar.market == MarketType.CRYPTO
    assert bar.close == 91000.0
    assert bar.high >= bar.low
    assert bar.is_closed is True


def test_config_defaults():
    """Verify default financial configurations (COP, America/Bogota)."""
    assert settings.DEFAULT_CURRENCY == "COP"
    assert settings.DEFAULT_TIMEZONE == "America/Bogota"
