# Sprint 11 Gap Report

## Completed

### 1. `finpilot up` single command (`fp` script)
- `./fp up`  — docker compose --profile scanner --profile telegram up -d --build
- `./fp down` — stops all services
- `./fp ps` / `./fp logs` — container inspect
- `./fp status` now includes docker container listing
- SENTRY_DSN warning emitted if not set in .env
- Makefile `docker-full` fixed (removed wrong --profile cache)

### 2. `core/services.py` service registry
- Thread-safe singleton `registry` (ServiceRegistry)
- `register()`, `get()`, `set_healthy()`, `deregister()`, `all()`, `health_summary()`
- Wired in `api/main.py` lifespan: registers `sentry` + `scheduler` at boot
- New endpoint: `GET /api/v1/services` → {status, services: {name: bool}}

### 3. Sentry DSN runtime validation (`api/main.py`)
- If SENTRY_DSN env var is missing: WARNING logged at startup
- `registry.register("sentry", healthy=bool(SENTRY_DSN))` — visible in /api/v1/services

## Gaps / Not Done This Sprint

| Item | Status | Note |
|------|--------|------|
| Subscription gate (Stripe) | Skipped per user | Will revisit later |
| redis/telegram registered in service registry | sentry+scheduler only | Wire others as needed |
| `fp up` tested in CI | Not automated | Smoke test pending |

## Next Sprint (S12) — Quality Metrics Dashboard
- Brier/ECE/WR auto-disable threshold tuning
- Walk-forward 12-fold actual run
- Optuna 200-trial sweep execution
