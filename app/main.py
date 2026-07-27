"""
FastAPI application entrypoint.

Wires together routers, middleware, and startup/shutdown lifecycle.
Feature routers (dashboard, funnel, retention, etc.) get added here
as each vertical slice is built in later phases.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.funnel import router as funnel_router
from app.api.retention import router as retention_router
from app.core.config import get_settings
from app.core.redis_client import check_redis_connection, close_redis
from app.database.connection import check_database_connection, close_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: fail loudly if Redis isn't reachable, rather than
    # letting the app boot and only discover it on the first
    # rate-limited or cached request.
    settings = get_settings()
    redis_ok = await check_redis_connection()
    if not redis_ok:
        logger.error("Startup check failed: Redis is not reachable at %s", settings.REDIS_URL)
    else:
        logger.info("Startup checks passed (environment=%s)", settings.ENVIRONMENT)

    yield

    # Shutdown: close pools cleanly.
    await close_pool()
    await close_redis()
    logger.info("Shutdown complete")


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for the Custom Analytics Dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Normalizes every HTTPException into a consistent JSON shape.
    If a route raised detail as a plain string (not our {message, code}
    dict), wrap it so the response shape is always the same.
    """
    detail = exc.detail
    if isinstance(detail, str):
        detail = {"message": detail, "code": "ERROR"}
    return JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=exc.headers)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches anything not already handled -- ensures a raw stack trace
    or internal error message never reaches the client, which could
    leak file paths, query structure, or library internals.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": {"message": "Internal server error", "code": "INTERNAL_ERROR"}},
    )


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Basic liveness/readiness check -- includes Redis status."""
    redis_ok = await check_redis_connection()
    db_ok = await check_database_connection()
    return {
        "status": "ok" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "unreachable",
        "database": "connected" if db_ok else "not_configured",
    }


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(funnel_router)
app.include_router(retention_router)