"""QUANT AI - Main FastAPI Application Server."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.core.errors import (
    QuantAIException,
    quant_ai_exception_handler,
    global_exception_handler,
)
from backend.api.v1.router import api_v1_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("quant_ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown management."""
    logger.info("Initializing QUANT AI Quantitative Engine & API...")
    logger.info("Default Timezone: %s | Currency: %s", settings.DEFAULT_TIMEZONE, settings.DEFAULT_CURRENCY)
    logger.info("CORS Origins: %s", settings.CORS_ORIGINS)
    yield
    logger.info("Shutting down QUANT AI...")


app = FastAPI(
    title="QUANT AI - Intelligent Quantitative Swing Trading & AI Analysis Platform",
    description="Professional Quantitative Analysis, SMC, Liquidity Intelligence, and AI Assistant Backend API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handlers
app.add_exception_handler(QuantAIException, quant_ai_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Include API Routers
app.include_router(api_v1_router)


@app.get("/")
async def root():
    """Root endpoint verifying API availability."""
    return {
        "app": "QUANT AI",
        "description": "Intelligent Quantitative Swing Trading & AI Analysis Platform",
        "status": "online",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
        "system": "/api/v1/system/status",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.QUANT_API_HOST,
        port=settings.QUANT_API_PORT,
        reload=settings.DEBUG,
    )
