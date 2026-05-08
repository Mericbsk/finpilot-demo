"""FinPilot API — FastAPI backend bridging Python ML models to Next.js frontend."""

import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure project root is on sys.path so we can import scanner, drl, core, etc.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Load .env file into environment variables
_env_path = Path(_PROJECT_ROOT) / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                _key, _val = _key.strip(), _val.strip()
                if _key and _key not in os.environ:
                    os.environ[_key] = _val

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.middleware.pii_filter import PIIFilterMiddleware
from api.routers import (
    auth,
    backtest,
    ensemble,
    history,
    inference,
    llm,
    models,
    optuna,
    scan,
    trade,
    user,
)
from auth.database import Database
from core.monitoring import health_check, metrics, sentry_client
from core.prometheus_exporter import get_metrics_output

# ---------------------------------------------------------------------------
# Rate limiter — 60 requests/minute per IP
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    Database().initialize()
    sentry_client.init(
        environment=os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENVIRONMENT", "development")),
        release=os.getenv("SENTRY_RELEASE", "finpilot-api@1.0.0"),
    )
    yield


app = FastAPI(title="FinPilot API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import logging as _logging

    _logging.getLogger(__name__).exception(
        "Unhandled exception on %s %s", request.method, request.url.path
    )
    sentry_client.capture_exception(
        exc,
        endpoint=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


@app.middleware("http")
async def instrument_requests(request: Request, call_next):
    start = time.perf_counter()
    raw_endpoint = request.url.path

    response = await call_next(request)

    route = request.scope.get("route")
    endpoint = getattr(route, "path", raw_endpoint)
    metrics.api_requests.inc(endpoint=endpoint, status_code=str(response.status_code))
    metrics.api_latency.observe(time.perf_counter() - start, endpoint=endpoint)
    return response


# ---------------------------------------------------------------------------
# CORS — whitelist only known origins
# CORS_ORIGINS env var (comma-separated) overrides defaults in production.
# Example: CORS_ORIGINS=https://finpilot.at,https://www.finpilot.at
# ---------------------------------------------------------------------------
_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000",
]
_env_origins = os.getenv("CORS_ORIGINS", "")
_ALLOWED_ORIGINS = (
    [o.strip() for o in _env_origins.split(",") if o.strip()] if _env_origins else _DEFAULT_ORIGINS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PIIFilterMiddleware)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(models.router, prefix="/api/v1")
app.include_router(inference.router, prefix="/api/v1")
app.include_router(ensemble.router, prefix="/api/v1")
app.include_router(optuna.router, prefix="/api/v1")
app.include_router(scan.router, prefix="/api/v1")
app.include_router(trade.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(llm.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/ready")
def ready():
    result = health_check.run()
    status_code = 200 if result.get("status") != "unhealthy" else 503
    return JSONResponse(content=result, status_code=status_code)


@app.get("/api/v1/metrics")
def metrics_endpoint():
    return PlainTextResponse(
        content=get_metrics_output(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
