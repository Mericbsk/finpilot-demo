# Pre-existing Test Failures (Sprint 6 Phase 1 baseline)

Baseline captured at the start of Sprint 6 stabilization, **after** archiving the
legacy Streamlit `views/` package and its targeted tests.

| Test | Failure | Category | Action |
|------|---------|----------|--------|
| `tests/test_api_runtime.py::test_compute_surface_requires_auth[/api/v1/scan-payload0]` | `assert 200 == 401` | Auth regression | Defer to S1-6 (re-add `require_auth` to protected endpoints) |
| `tests/test_new_endpoints.py::TestFetchPriceSync::test_returns_expected_keys` | `assert 1.0 == 150.0` | yfinance live data shape changed | Mock yfinance in test (Sprint 4 paid API work) |
| `tests/test_new_endpoints.py::TestFetchPriceSync::test_rounds_price_to_four_decimals` | `assert 1.0 == 123.4568` | Same as above | Same as above |
| `tests/test_prometheus.py::TestEdgeCases::test_server_port_in_use` | `DID NOT RAISE OSError` | Flaky on Windows (port reuse semantics) | Skip on Windows or use `socket.SO_EXCLUSIVEADDRUSE` |

**Total**: 4 pre-existing failures, 494 passing, 10 skipped (out of 511 collected after view tests archived).

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
