"""API package that assembles FastAPI routers."""

from .routers.alexa import router as alexa_router

__all__ = ["alexa_router"]
