"""Configuration module for QUANT AI backend.
Reads configuration from environment variables with strong typing via Pydantic.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "QUANT AI Backend"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", validation_alias="NEXT_PUBLIC_APP_ENV")
    DEBUG: bool = True

    # Regional & Localization
    DEFAULT_CURRENCY: str = "COP"
    DEFAULT_TIMEZONE: str = "America/Bogota"
    DEFAULT_LOCALE: str = "es-CO"

    # Server Configuration
    QUANT_API_HOST: str = "0.0.0.0"
    QUANT_API_PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    # Supabase Configuration
    NEXT_PUBLIC_SUPABASE_URL: str = ""
    NEXT_PUBLIC_SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Market Data Providers
    BINANCE_MARKET_DATA_URL: str = "https://data-api.binance.vision"
    BINANCE_WS_BASE_URL: str = "wss://stream.binance.com:9443/ws"
    YAHOO_FINANCE_ENABLED: bool = True
    YAHOO_CACHE_TTL_SECONDS: int = 60
    BVC_DATA_PATH: str = "./data/bvc/"
    MACRO_DATA_PATH: str = "./data/macro/"

    # AI Configuration (Optional / decoupled)
    AI_PROVIDER: str = "gemini"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gemini-1.5-pro"
    AI_VISION_PROVIDER: str = "gemini"
    AI_VISION_MODEL: str = "gemini-1.5-flash"
    AI_STT_PROVIDER: str = "web_speech_api"
    AI_TTS_PROVIDER: str = "web_speech_synthesis"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
