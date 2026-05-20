"""FinPilot startup smoke test.

Sprint 6 / s6-startup-smoke. Cross-platform sanity check that exercises the
critical startup paths without needing Docker or a real broker:

  1. Core imports resolve
  2. Scheduler can run a single cycle (CEO graph -> downstream agents)
  3. FastAPI app boots (TestClient)
  4. Health + closed-loop uptime endpoints respond

Exit codes:
  0 - all checks passed
  1 - one or more checks failed

Run:
    python scripts/smoke_test.py
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _step(name: str, fn: Callable[[], None]) -> bool:
    t0 = time.time()
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        dt = time.time() - t0
        print(f"[FAIL] {name} ({dt:.2f}s): {exc}")
        traceback.print_exc()
        return False
    dt = time.time() - t0
    print(f"[ OK ] {name} ({dt:.2f}s)")
    return True


def check_imports() -> None:
    import core.scheduler  # noqa: F401
    import api.main  # noqa: F401
    import agents.ceo  # noqa: F401


def check_scheduler_cycle() -> None:
    from core.scheduler import run_cycle_once

    res = run_cycle_once(["AAPL"])
    assert isinstance(res, dict), f"expected dict, got {type(res)!r}"
    assert "ceo" in res, f"missing 'ceo' in cycle result: {list(res)}"
    assert "scan" in res, f"missing 'scan' in cycle result: {list(res)}"
    errors = res.get("errors") or []
    if errors:
        raise AssertionError(f"cycle reported errors: {errors[:3]}")


def check_fastapi_boot() -> None:
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        r = client.get("/api/v1/health")
        assert r.status_code == 200, f"/health -> {r.status_code} {r.text[:200]}"


def check_uptime_endpoint() -> None:
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        r = client.get("/api/v1/loop/uptime")
        assert r.status_code == 200, f"/loop/uptime -> {r.status_code} {r.text[:200]}"
        body = r.json()
        for key in ("running", "healthy", "cycle_count"):
            assert key in body, f"missing '{key}' in uptime response: {body}"


def main() -> int:
    print("=" * 60)
    print("FinPilot Startup Smoke Test")
    print("=" * 60)

    checks = [
        ("imports resolve", check_imports),
        ("scheduler cycle (CEO graph)", check_scheduler_cycle),
        ("FastAPI app boots + /health", check_fastapi_boot),
        ("/loop/uptime endpoint", check_uptime_endpoint),
    ]

    results = [_step(name, fn) for name, fn in checks]

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Smoke result: {passed}/{total} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
