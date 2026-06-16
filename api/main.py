"""FinPilot API — FastAPI backend bridging Python ML models to Next.js frontend."""

import logging as _logging
import os
import sys
import time
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
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

from auth.database import Database
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.middleware.pii_filter import PIIFilterMiddleware
from api.routers import (
    advisory,
    agent,
    ai_explain,
    analytics,
    auth,
    backtest,
    closed_loop,
    ensemble,
    history,
    inference,
    llm,
    market_data,
    models,
    optuna,
    prices,
    profitcore,
    research,
    scan,
    trade,
    user,
    waitlist_signup,
    watchlist,
)
from core.monitoring import health_check, metrics, sentry_client
from core.prometheus_exporter import get_metrics_output

# ---------------------------------------------------------------------------
# Rate limiter — 60 requests/minute per IP
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


def _archive_yesterday_on_startup() -> None:
    """Archive signals from the previous day on container start (idempotent)."""
    import json
    from datetime import UTC, datetime, timedelta

    from core.config import DATA_DIR, SIGNAL_ARCHIVE_DIR

    watchlist_file = DATA_DIR / "watchlist.json"
    archive_dir = SIGNAL_ARCHIVE_DIR
    yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    archive_path = archive_dir / f"{yesterday}.json"

    if archive_path.exists():
        return  # Already archived

    if not watchlist_file.exists():
        return

    try:
        data = json.loads(watchlist_file.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else []
        yesterday_items = [i for i in items if i.get("signal_date", "")[:10] == yesterday]
        if yesterday_items:
            archive_dir.mkdir(parents=True, exist_ok=True)
            archive_path.write_text(
                json.dumps(yesterday_items, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            import logging

            logging.getLogger(__name__).info(
                "Startup archive: %d signals saved for %s", len(yesterday_items), yesterday
            )
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning("Startup archive failed: %s", exc)


def _register_health_checks() -> None:
    """Register liveness/readiness checks (DB + Redis)."""
    from core.monitoring import HealthCheckResult, HealthStatus

    @health_check.register("database")
    def _check_db() -> HealthCheckResult:
        try:
            db = Database()
            with db.connection() as conn:
                conn.execute("SELECT 1")
            return HealthCheckResult(name="database", status=HealthStatus.HEALTHY)
        except Exception as exc:  # noqa: BLE001
            return HealthCheckResult(
                name="database", status=HealthStatus.UNHEALTHY, message=str(exc)
            )

    @health_check.register("redis")
    def _check_redis() -> HealthCheckResult:
        try:
            from core import agent_state

            client = getattr(agent_state, "_redis", None)
            if client is None:
                return HealthCheckResult(
                    name="redis",
                    status=HealthStatus.DEGRADED,
                    message="Redis unavailable; using in-memory fallback",
                )
            client.ping()
            return HealthCheckResult(name="redis", status=HealthStatus.HEALTHY)
        except Exception as exc:  # noqa: BLE001
            return HealthCheckResult(name="redis", status=HealthStatus.DEGRADED, message=str(exc))


@asynccontextmanager
async def lifespan(app: FastAPI):
    _setup_log_rotation()
    Database().initialize()
    _register_health_checks()

    # ── Watchlist DB table + one-time JSON migration ─────────────────
    try:
        from pathlib import Path as _Path

        from api.services import watchlist_db as _wdb

        _wdb.ensure_table()
        migrated = _wdb.migrate_from_json(_Path("data/watchlist.json"))
        if migrated:
            _logging.getLogger(__name__).info(
                "watchlist_db: migrated %d signals from JSON on startup", migrated
            )
    except Exception as _exc:
        _logging.getLogger(__name__).warning("watchlist_db init failed: %s", _exc)

    # ── Sentry init + DSN warning ──────────────────────────────
    if not os.getenv("SENTRY_DSN"):
        _logging.getLogger(__name__).warning(
            "SENTRY_DSN not set — error tracking disabled. "
            "Set SENTRY_DSN in .env to enable Sentry."
        )
    sentry_client.init(
        environment=os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENVIRONMENT", "development")),
        release=os.getenv("SENTRY_RELEASE", "finpilot-api@1.0.0"),
    )

    # ── Service registry bootstrap ─────────────────────────────
    from core.services import registry as _svc_registry

    # Register core services (health probed during healthcheck polling)
    _svc_registry.register("sentry", healthy=bool(os.getenv("SENTRY_DSN")))

    # Archive yesterday's signals on startup (idempotent — runs once per day)
    _archive_yesterday_on_startup()
    # Start watchlist background price refresh
    from api.routers.watchlist import start_price_refresh_task

    await start_price_refresh_task()

    # Sprint 5 (S5-2): single bootstrap — start the autonomous scheduler from lifespan
    if os.getenv("FINPILOT_AUTOSTART_SCHEDULER", "1") == "1":
        try:
            from core.scheduler import start_scheduler

            symbols_env = os.getenv(
                "FINPILOT_SCHEDULER_SYMBOLS",
                "AAPL,MSFT,NVDA,GOOGL,META,AMZN,TSLA,AMD",
            )
            symbols = [s.strip() for s in symbols_env.split(",") if s.strip()]
            interval = int(os.getenv("FINPILOT_SCHEDULER_INTERVAL_MIN", "60"))
            started = start_scheduler(symbols=symbols, interval_minutes=interval)
            _svc_registry.register(
                "scheduler",
                healthy=started,
                meta={"symbols": len(symbols), "interval_min": interval},
            )
            _logging.getLogger(__name__).info(
                "Scheduler autostart: started=%s symbols=%s interval=%dm",
                started,
                symbols,
                interval,
            )
        except Exception as exc:  # noqa: BLE001
            _svc_registry.register("scheduler", healthy=False, meta={"error": str(exc)})
            _logging.getLogger(__name__).warning("Scheduler autostart failed: %s", exc)

    # Load champion weights from model registry into finpilot_score (if available)
    try:
        from scanner.finpilot_score import load_weights  # noqa: PLC0415

        loaded = load_weights()
        if loaded:
            _logging.getLogger(__name__).info(
                "startup: champion weights loaded — %d keys", len(loaded)
            )
    except Exception as exc:
        _logging.getLogger(__name__).debug("startup: champion weights not loaded: %s", exc)

    yield


def _setup_log_rotation() -> None:
    """Attach a RotatingFileHandler (10 MB × 5 backups) to the root logger."""
    import logging

    log_dir = Path(_PROJECT_ROOT) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "api.log"

    handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    handler.setLevel(logging.INFO)

    root = logging.getLogger()
    if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        root.addHandler(handler)


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

    # Track page views for known frontend paths (fire-and-forget, never raises)
    try:
        _FRONTEND_PREFIXES = ("/dashboard", "/agent", "/scanner", "/research", "/portfolio")
        if raw_endpoint.startswith(_FRONTEND_PREFIXES) and response.status_code < 400:
            from core.analytics import increment_page_view

            increment_page_view(raw_endpoint)
    except Exception:
        pass

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
app.include_router(agent.router, prefix="/api/v1")
app.include_router(advisory.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")
app.include_router(inference.router, prefix="/api/v1")
app.include_router(ensemble.router, prefix="/api/v1")
app.include_router(optuna.router, prefix="/api/v1")
app.include_router(scan.router, prefix="/api/v1")
app.include_router(prices.router, prefix="/api/v1")
app.include_router(trade.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(llm.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(watchlist.router, prefix="/api/v1")
app.include_router(ai_explain.router, prefix="/api/v1")
app.include_router(market_data.router, prefix="/api/v1")
app.include_router(closed_loop.router, prefix="/api/v1")
app.include_router(research.router, prefix="/api/v1")
app.include_router(profitcore.router, prefix="/api/v1")
app.include_router(waitlist_signup.router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/live")
def liveness():
    """K8s liveness probe — process is alive (no dependency checks)."""
    return {"status": "alive"}


@app.get("/api/v1/ready")
def ready():
    """K8s readiness probe — dependencies (DB, Redis) reachable."""
    result = health_check.run()
    status_code = 200 if result.get("status") != "unhealthy" else 503
    return JSONResponse(content=result, status_code=status_code)


@app.get("/api/v1/services")
def services_endpoint():
    """Service registry — shows health of all registered FinPilot services."""
    from core.services import registry as _svc_registry

    summary = _svc_registry.health_summary()
    all_healthy = all(summary.values()) if summary else True
    return {"status": "ok" if all_healthy else "degraded", "services": summary}


# Top-level aliases for K8s probes (/live, /ready) — common convention
@app.get("/live")
def liveness_root():
    return {"status": "alive"}


@app.get("/ready")
def ready_root():
    result = health_check.run()
    status_code = 200 if result.get("status") != "unhealthy" else 503
    return JSONResponse(content=result, status_code=status_code)


@app.get("/api/v1/metrics")
def metrics_endpoint():
    return PlainTextResponse(
        content=get_metrics_output(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
