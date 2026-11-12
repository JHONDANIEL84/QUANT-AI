"""Global error handling and custom exceptions for QUANT AI."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("quant_ai.errors")


class QuantAIException(Exception):
    """Base exception for all domain-specific QUANT AI errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ProviderConnectionError(QuantAIException):
    """Raised when an external market data provider cannot be reached."""

    def __init__(self, provider: str, details: str = ""):
        super().__init__(
            message=f"No se pudo establecer conexión con el proveedor de mercado '{provider}': {details}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"provider": provider, "error": details},
        )


class DataNormalizationError(QuantAIException):
    """Raised when data received from a provider cannot be normalized to standard schema."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Error en la normalización de datos financieros: {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"reason": reason},
        )


async def quant_ai_exception_handler(request: Request, exc: QuantAIException) -> JSONResponse:
    """Handles domain-specific exceptions."""
    logger.warning("Domain exception at %s: %s", request.url.path, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__,
                "details": exc.details,
            },
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unhandled exceptions."""
    logger.exception("Unhandled server error at %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "message": "Error interno del servidor. Por favor consulte los registros del sistema.",
                "type": "InternalServerError",
            },
        },
    )
