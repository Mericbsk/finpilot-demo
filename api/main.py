"""FinPilot API — FastAPI backend bridging Python ML models to Next.js frontend."""

import os
import sys
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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.routers import (
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

# ---------------------------------------------------------------------------
# Rate limiter — 60 requests/minute per IP
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(title="FinPilot API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# CORS — whitelist only known origins
# ---------------------------------------------------------------------------
_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
