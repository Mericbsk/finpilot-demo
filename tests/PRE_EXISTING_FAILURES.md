# Pre-existing Test Failures (updated 2026-06-12)

Baseline updated after FAZ 1 implementation and P0 auth fix.

| Test | Failure | Category | Action |
|------|---------|----------|--------|
| `tests/test_new_endpoints.py::TestFetchPriceSync::test_returns_expected_keys` | `assert 1.0 == 150.0` | yfinance live data shape changed | Mock yfinance in test (Sprint 4 paid API work) |
| `tests/test_new_endpoints.py::TestFetchPriceSync::test_rounds_price_to_four_decimals` | `assert 1.0 == 123.4568` | Same as above | Same as above |
| `tests/test_prometheus.py::TestEdgeCases::test_server_port_in_use` | `DID NOT RAISE OSError` | Flaky on Windows (port reuse semantics) | Skip on Windows or use `socket.SO_EXCLUSIVEADDRUSE` |

**Total**: 3 pre-existing failures, 514 passing, 6 skipped (out of 523 collected).

## Fixed since last baseline

| Test | Fix | Commit note |
|------|-----|-------------|
| `test_compute_surface_requires_auth[/api/v1/scan-payload0]` | `auth/database.py` now re-reads `FINPILOT_DB_PATH` at call time — monkeypatch env var now propagates | 2026-06-12 |
| `test_auth_register_login_and_me_flow` | Same fix as above — test DB isolation restored | 2026-06-12 |
| `test_require_auth_passes_with_valid_token` | `api/middleware/auth.py` lazy-init JWT handler — no more module-level key snapshot | 2026-06-12 |
| `test_calibration_gate_rollback_on_insufficient_samples` | `test_autonomy.py` fixture now disables Redis to prevent cross-test data pollution | 2026-06-12 |

## Permanently retired (moved to `archive/legacy/`)

These tests were removed from the active suite in Sprint 6 because their target code
(legacy Streamlit `views/` package) was dropped:

- `tests/test_views_smoke.py` — replaced by Next.js dashboard E2E
- `tests/test_views_integration.py` — replaced by Next.js dashboard E2E

## Already-ignored

Configured at the run level via `--ignore`:

- `tests/scanner_rollout/` — under-construction rollout harness (Sprint 5/6 backlog)
- `tests/test_signals.py` — depends on legacy signal contract (Sprint 3 advisory rewrite)

## Green-build command

```bash
pytest tests/ \
  --ignore=tests/scanner_rollout \
  --ignore=tests/test_signals.py \
  -p no:warnings
```

Expected outcome until Sprint 1 lands: **4 failed, 494 passed, 10 skipped**.
