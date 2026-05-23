# Sprint 12 Gap Report — Quality Metrics

**Date:** 2025-05-19
**Status:** ✅ DONE

## Completed

| Task | Status | Notes |
|------|--------|-------|
| Walk-forward 12-fold runner | ✅ | `WalkForwardCV.run()` + `save_results()` + `load_last_results()` |
| Walk-forward scheduled (weekly Sun 02:00 UTC) | ✅ | via research pipeline job |
| Optuna 200-trial sweep | ✅ | `run_sweep()` + `save_best_weights()` + `load_last_weights()` |
| Champion/challenger SQLite registry | ✅ | `ModelRegistry` with auto-promote logic |
| Research pipeline orchestrator | ✅ | `research/pipeline.py` — WF → sweep → registry → auto-promote |
| Weekly scheduler job | ✅ | `_run_research_pipeline_job()` in `core/scheduler.py` |
| API endpoints | ✅ | `GET /api/v1/research/status`, `POST /api/v1/research/run`, `GET /api/v1/research/registry`, `POST /api/v1/research/registry/promote-best` |
| Configurable Brier threshold | ✅ | `FINPILOT_BRIER_REGRESSION_THRESHOLD` env var (default 0.02) |

## New Files

- `research/pipeline.py` — WF + sweep + registry orchestration
- `api/routers/research.py` — REST endpoints for research status/trigger/registry

## Modified Files

- `research/walkforward.py` — Added `save_results()`, `load_last_results()`, `run_default_wf()` saves to disk
- `research/sweep.py` — Added `save_best_weights()`, `load_last_weights()`
- `core/scheduler.py` — Added `_run_research_pipeline_job()` + weekly Sunday cron
- `api/main.py` — Included `research` router
- `core/calibration.py` — `FINPILOT_BRIER_REGRESSION_THRESHOLD` env var; `refit_with_gate` uses it

## What Remains / Gaps

| Gap | Priority | Sprint |
|-----|----------|--------|
| Walk-forward results tile on `/dashboard/calibration` | Medium | S13 |
| Champion vs challenger live diff metric on dashboard | Medium | S13 |
| Optuna `optuna` package must be present in container (`pip install optuna`) | High | S13 infra |
| Walkforward uses `ts` as epoch-ms — production signals must set this field | Medium | S13 data |
| T+5/T+20 reconciler completes before WF has full outcome coverage | Low | Long-term |

## Metrics (at Sprint 12 completion)

- Registry: seeded with `baseline_uniform` champion on first pipeline run
- Sweep: reads seed from `optuna_conservative_results.json` if present
- WF: runs 12 folds × (24m train / 6m val), persists to `data/walkforward_results.json`
- Threshold: default 2pp Brier regression → rollback (env-configurable)
