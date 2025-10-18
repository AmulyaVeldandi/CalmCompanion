"""Individual FastAPI routers grouped by domain."""

from .alexa import router as alexa_router

__all__ = ["alexa_router"]
