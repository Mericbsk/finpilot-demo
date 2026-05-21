# Sprint 10 Gap Report

## Completed

### 1. Slippage + Fee Model (`core/paper_portfolio.py`)
- SLIPPAGE_BPS=5.0, COMMISSION_BPS=5.0 (10 bps round-trip)
- close_position() applies cost model; trade records include gross_pnl_pct, pnl_pct (net), cost_bps

### 2. Auto-Disable on Brier Regression (`core/calibration.py`)
- refit_with_gate() calls quality_gate.set_degraded() when new_brier > old_brier + 0.02
- Added _ece(), _append_brier_history(), get_brier_history(), get_calibration_stats()
- Brier history stored in data/calibration_brier_history.json (max 90 entries)

### 3. /calibration/stats Endpoint (`api/routers/closed_loop.py`)
- Returns {fitted, n_samples, brier, ece, bands, decile_lift, brier_history}

### 4. Live P&L Tile (`web/src/app/dashboard/page.tsx`)
- Fetches from /py-api/loop/portfolio
- Shows equity, win rate, profit factor, open positions

### 5. Calibration Quality Page (`web/src/app/dashboard/calibration/page.tsx`)
- Quality gate banner, KPI row (Brier/ECE/Top Lift/Win Rate)
- Brier trend bars, Score Band calibration bars, Decile Lift chart
- Sidebar link added with Gauge icon

### 6. Research Skeleton
- research/walkforward.py, research/sweep.py, research/registry.py (committed 868bbef)

### 7. Decile Lift (core/kpi_tracker.py)
- compute_decile_lift() added in Sprint 9

## Gaps / Not Done This Sprint

| Item | Status | Next Sprint |
|------|--------|-------------|
| Walk-forward actual 12-fold run | skeleton only | S11+ |
| Optuna 200-trial sweep execution | skeleton only | S11+ |
| Champion/challenger DB population | SQLite table defined, no data | S11+ |
| T+5/T+20 reconciler in prod | code complete, monitoring | ongoing |

## Next Sprint (S11) — Integration
- `finpilot up` single command (docker + scheduler + telegram)
- core/services.py service registry
- Subscription gate skeleton (Stripe test mode)
