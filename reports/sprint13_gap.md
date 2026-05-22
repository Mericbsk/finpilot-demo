# Sprint 13 Gap Report — Promotion Gate & Strategies UI

## Sprint Goal
Add a 2-condition promotion gate (Brier + win rate), 2-strike automatic rollback
to the last registry champion, and a champion/challenger diff page in the dashboard.

## Completed Tasks

### ✅ s13-promotion-gate — 2-condition promotion gate
- **File**: `research/registry.py`
- `auto_promote_best()` now requires **both** conditions to pass before promoting:
  1. Challenger Brier < champion Brier − `min_brier_improvement` (default 0.01)
  2. Challenger `win_rate` ≥ `min_win_rate` (default 0.50)
- If the gate fails, challenger's `strike_count` is incremented.
- After `max_strikes_before_retire` (default 2) consecutive failures, the
  challenger is retired automatically.
- Added `add_strike()`, `reset_strikes()` instance methods.
- Schema migration: `strike_count INTEGER DEFAULT 0` and `promotion_notes TEXT`
  columns added to existing DBs via `ALTER TABLE … ADD COLUMN` (idempotent).
- `promote_best` API endpoint updated with `min_win_rate` + `max_strikes` params.

### ✅ s13-rollback — 2-strike automatic rollback
- **File**: `core/calibration.py`
- Added `_ROLLBACK_STRIKES_PATH` constant: `data/calibration_rollback_strikes.json`
- Added `_get_rollback_strikes()`, `_increment_rollback_strikes()`,
  `_reset_rollback_strikes()` helpers.
- `refit_with_gate()` now:
  - Increments strike counter on every Brier regression rollback.
  - After `_MAX_ROLLBACK_STRIKES` (= 2) consecutive rollbacks, fetches the
    current registry champion's weights from `research.registry.ModelRegistry`
    and restores them via `scanner.finpilot_score.set_weights()`.
  - Resets strike counter on successful promotion.
- Audit log payloads now include `consecutive_rollbacks`.

### ✅ s13-strategies-page — /dashboard/strategies
- **File**: `web/src/app/dashboard/strategies/page.tsx` (NEW)
- Full champion vs challenger UI:
  - Champion card with golden border and trophy icon
  - Live diff table: Brier, win rate, profit factor comparison with Δ indicator
  - Challenger cards with strike badges
  - "Evaluate Gate" button triggers `POST /py-api/research/registry/promote-best`
  - Auto-refreshes every 30 seconds
- **File**: `web/src/components/dashboard/Sidebar.tsx`
  - Added `Strategies` link (Swords icon) below Calibration

## Gaps / Known Issues

| # | Issue | Severity | Notes |
|---|-------|----------|-------|
| 1 | `scanner.finpilot_score.set_weights()` doesn't exist yet | Medium | 2-strike rollback logs a warning on failure; no crash. Implement in Sprint 15. |
| 2 | `promotion_notes` column not yet exposed in the registry GET endpoint | Low | Stored in DB, not surfaced in UI. Add to `get_challengers()` return dict if needed. |
| 3 | `min_win_rate` defaults to 0.50 — may be too strict in early data | Low | Env var override planned for Sprint 14. |

## Next Sprint
**Sprint 14 — Self-Evaluation & Telegram CEO Report**
- CEO agent weekly summary → Telegram (champion metrics, Brier trend, top signals)
- Auto-approve threshold (calibrated p_win > 0.65 + env normal → auto)
- `finpilot_score.set_weights()` for weight hot-reload
