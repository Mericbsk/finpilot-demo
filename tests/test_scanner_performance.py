from __future__ import annotations

import asyncio
import json
import threading

import pandas as pd
import pytest
from agents.base import AgentContext
from api.routers import scan as scan_router
from auth.tokens import TokenPayload
from fastapi import Request
from scanner import data_fetcher, performance

from core import scan_coordinator, scan_observability


@pytest.fixture(autouse=True)
def isolate_scan_observation(tmp_path, monkeypatch):
    monkeypatch.setenv("FINPILOT_DIST_DIR", str(tmp_path))
    monkeypatch.setenv("FINPILOT_SCAN_OBSERVABILITY", "1")
    monkeypatch.setenv("FINPILOT_SCAN_COORDINATOR", "0")
    yield
    assert scan_observability._ACTIVE_JOBS == {}


def test_stage_timing_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("FINPILOT_SCAN_STAGE_TIMING", raising=False)
    performance.reset()

    with performance.timer("test.stage", count=1):
        pass

    assert performance.snapshot() == []


def test_stage_timing_records_opt_in_events(monkeypatch):
    monkeypatch.setenv("FINPILOT_SCAN_STAGE_TIMING", "1")
    performance.reset()

    with performance.timer("test.stage", count=3, timeframe="1d", path="fixture"):
        pass

    events = performance.snapshot()
    assert len(events) == 1
    assert events[0]["stage"] == "test.stage"
    assert events[0]["count"] == 3
    assert events[0]["timeframe"] == "1d"
    assert events[0]["path"] == "fixture"
    assert events[0]["outcome"] == "ok"
    assert events[0]["elapsed_s"] >= 0


def test_stage_timing_records_error_outcome(monkeypatch):
    monkeypatch.setenv("FINPILOT_SCAN_STAGE_TIMING", "1")
    performance.reset()

    try:
        with performance.timer("test.error"):
            raise ValueError("fixture")
    except ValueError:
        pass

    assert performance.snapshot()[0]["outcome"] == "error"


def test_bulk_yfinance_call_is_counted_separately(monkeypatch):
    """TOPLU yfinance kullanimi gorunur olmali — ama AYRI sayacta.

    Tasarim notu (2026-09-21): bu testin onceki hali `yf_fetch_count() == 1`
    bekliyordu, yani toplu yolu mevcut `yf_fallback` sayacina katiyordu.
    Bu YAPILMADI, cunku:
      1) `yf_fallback` alani 315 gecmis kayitta mevcut; anlamini degistirmek
         eski ve yeni kayitlari karsilastirilamaz hale getirir.
      2) "200 sembol servis eden 1 toplu cagri" ile "1 sembol ceken 1 cagri"
         ayni sayiya yazilirsa maliyet ayrimi kaybolur.
    Testin NIYETI (toplu kullanim gorunur olsun) korundu, MEKANIZMASI degisti.
    """
    monkeypatch.setattr(data_fetcher.yf, "download", lambda *args, **kwargs: pd.DataFrame())
    data_fetcher.reset_yf_fetch_count()

    result = data_fetcher._bulk_yf_download(["AAA", "BBB"], "1d", 5, False)

    assert result == {}
    # Sembol-basina sayac DEGISMEZ — geriye donuk karsilastirilabilirlik.
    assert data_fetcher.yf_fetch_count() == 0
    # Toplu kullanim ayri sayacta gorunur.
    assert data_fetcher.yf_bulk_counts() == {"requests": 1, "symbols": 2}


def test_yf_bulk_counters_reset_between_scans(monkeypatch):
    monkeypatch.setattr(data_fetcher.yf, "download", lambda *args, **kwargs: pd.DataFrame())
    data_fetcher.reset_yf_fetch_count()
    data_fetcher._bulk_yf_download(["AAA"], "1d", 5, False)
    assert data_fetcher.yf_bulk_counts()["requests"] == 1

    data_fetcher.reset_yf_fetch_count()

    assert data_fetcher.yf_bulk_counts() == {"requests": 0, "symbols": 0}


def test_intraday_coverage_counts_final_history_thresholds():
    data_fetcher.reset_yf_fetch_count()
    result = {
        "AAA": {
            "15m": pd.DataFrame(index=range(15)),
            "1h": pd.DataFrame(index=range(9)),
        },
        "BBB": {
            "15m": pd.DataFrame(index=range(14)),
            "1h": pd.DataFrame(index=range(10)),
        },
    }

    data_fetcher._note_intraday_coverage(result, ["AAA", "BBB"])

    assert data_fetcher.intraday_coverage() == {"15m": 1, "1h": 1}


def test_intraday_coverage_is_reset_between_scans():
    data_fetcher._note_intraday_coverage({"AAA": {"15m": pd.DataFrame(index=range(15))}}, ["AAA"])
    assert data_fetcher.intraday_coverage() == {"15m": 1, "1h": 0}

    data_fetcher.reset_yf_fetch_count()

    assert data_fetcher.intraday_coverage() == {}


def test_alpaca_total_failure_is_flagged_on_the_real_production_path(monkeypatch):
    """REGRESYON TESTI — 2026-09-21'de bulunan olu-kod hatasi icin.

    `_note_alpaca_total_failure()` cagrisi `return alpaca_result`'in ALTINDA
    duruyordu, yani hicbir zaman calismiyordu. Mevcut birim testi fonksiyonu
    DOGRUDAN cagirdigi icin bunu yakalayamadi (IMPLEMENTED != ACTIVE).
    Bu test uretim yolunu kullanir: Alpaca None dondugunde bayrak True olmali.
    """
    monkeypatch.setattr(data_fetcher, "_prefetch_alpaca_bulk", lambda *args, **kwargs: None)
    monkeypatch.setattr(data_fetcher.yf, "download", lambda *args, **kwargs: pd.DataFrame())
    data_fetcher.reset_yf_fetch_count()
    assert data_fetcher.alpaca_total_failure() is False

    data_fetcher.prefetch_symbols_multi_timeframe(
        ["AAA"], timeframes=[("1d", 5)], with_indicators=False, max_workers=1
    )

    assert data_fetcher.alpaca_total_failure() is True


def test_alpaca_total_failure_resets_and_is_recorded(monkeypatch):
    data_fetcher.reset_yf_fetch_count()
    data_fetcher._note_alpaca_total_failure()
    assert data_fetcher.alpaca_total_failure() is True

    data_fetcher.reset_yf_fetch_count()

    assert data_fetcher.alpaca_total_failure() is False


def test_alpaca_disabled_defaults_to_off(monkeypatch):
    """Kisit 1: bayrak yoksa Alpaca ACIK — varsayilan davranis korunur."""
    monkeypatch.delenv("FINPILOT_DISABLE_ALPACA", raising=False)
    monkeypatch.setenv("ALPACA_API_KEY", "dummy-not-a-real-key")

    assert data_fetcher.alpaca_disabled() is False
    assert data_fetcher._alpaca_available() is True


def test_alpaca_flag_closes_all_three_gates(monkeypatch):
    """ALPACA_API_KEY UC ayri yerde kapi: _get_alpaca_client,
    fetch_symbols_batch auto-detect, _prefetch_alpaca_bulk.
    Bayrak UCUNU birden kapatmali — biri acik kalirsa A/B Kol B'si
    'kismen Alpaca acik' kosar ve deney gecersiz olur."""
    monkeypatch.setenv("ALPACA_API_KEY", "dummy-not-a-real-key")
    monkeypatch.setenv("FINPILOT_DISABLE_ALPACA", "1")

    assert data_fetcher.alpaca_disabled() is True
    # Ortak kaynak
    assert data_fetcher._alpaca_available() is False
    # Kapi 1
    assert data_fetcher._get_alpaca_client() is None
    # Kapi 3
    assert data_fetcher._prefetch_alpaca_bulk(["AAA"], [("1d", 5)], False) is None


def test_alpaca_flag_overrides_explicit_use_alpaca(monkeypatch):
    """Kapi 2: cagiran acikca use_alpaca=True gecse bile bayrak EZER.
    Deney kolu mutlak olmali."""
    monkeypatch.setenv("ALPACA_API_KEY", "dummy-not-a-real-key")
    monkeypatch.setenv("FINPILOT_DISABLE_ALPACA", "1")
    monkeypatch.setattr(data_fetcher.yf, "download", lambda *a, **k: pd.DataFrame())

    # Alpaca yoluna GIRILIRSE patlasin — boylece "girilmedi"yi kanitlariz.
    def _boom(*_a, **_k):
        raise AssertionError("Alpaca yoluna girildi — bayrak EZMEDI")

    monkeypatch.setattr(data_fetcher, "_get_alpaca_client", _boom)
    monkeypatch.setattr(data_fetcher, "_prefetch_alpaca_bulk", _boom)

    data_fetcher.reset_yf_fetch_count()
    # use_alpaca=True acikca gecildi; bayrak bunu ezmeli ve Alpaca'ya HIC
    # dokunmadan yfinance tarafina dusmeli. _boom tetiklenirse test patlar.
    data_fetcher.fetch_symbols_batch(["AAA"], use_alpaca=True)


def test_scan_timing_log_includes_experiment_arm(tmp_path, monkeypatch):
    """Kisit 5: hangi kolun urettigi kaydin KENDISINDEN anlasilmali."""
    monkeypatch.setenv("FINPILOT_DIST_DIR", str(tmp_path))

    scan_router._append_scan_timing_log(
        {
            "symbols": 2,
            "total_s": 1.1,
            "alpaca_disabled": True,
            "experiment_arm": "B_alpaca_disabled",
            "result_symbols": 2,
        },
        universe=2,
    )

    record = json.loads((tmp_path / "scan_timing.jsonl").read_text(encoding="utf-8"))
    assert record["experiment_arm"] == "B_alpaca_disabled"
    assert record["alpaca_disabled"] is True
    assert record["result_symbols"] == 2


def test_scan_timing_log_includes_persistence_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("FINPILOT_DIST_DIR", str(tmp_path))

    scan_router._append_scan_timing_log(
        {
            "symbols": 2,
            "eval_s": 1.0,
            "enrich_s": 0.1,
            "total_s": 1.1,
            "persist_s": 0.2,
            "yf_fallback": 1,
            "yf_bulk_requests": 3,
            "yf_bulk_symbols": 600,
            "intraday_coverage": {"15m": 1, "1h": 2},
            "alpaca_total_failure": True,
        },
        universe=2,
    )

    record = json.loads((tmp_path / "scan_timing.jsonl").read_text(encoding="utf-8"))
    assert record["total_s"] == 1.1
    assert record["persist_s"] == 0.2
    assert record["alpaca_total_failure"] is True
    # `total_s` kalicilastirmayi ICERMEZ — gecmis 315 kayitla karsilastirilabilir
    # kalmasi icin anlami degistirilmedi; `persist_s` AYRI alandir.
    assert record["total_s"] == 1.1
    assert record["yf_bulk_requests"] == 3
    assert record["yf_bulk_symbols"] == 600
    assert record["intraday_coverage"] == {"15m": 1, "1h": 2}


def _observation_records(tmp_path):
    return [
        json.loads(line)
        for line in (tmp_path / "scan_timing.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def test_scan_observation_remembers_transient_overlap(tmp_path):
    first = scan_observability.ScanObservation("api_scan", 2, "request-a")
    second = scan_observability.ScanObservation("scanner_agent", 2)
    first.start_job()
    second.start_job()
    second.end_job("ok")
    first.end_job("ok")

    completed = [row for row in _observation_records(tmp_path) if row["event"] == "job_finished"]
    assert all(row["counters_unreliable"] for row in completed)
    assert all(row["peak_active_jobs"] == 2 for row in completed)
    assert first.active_jobs_at_start == first.active_jobs_at_end == 1
    assert second.active_jobs_at_start == second.active_jobs_at_end == 2


def test_counter_reset_marks_running_job_unreliable(tmp_path):
    observation = scan_observability.ScanObservation("script", 2)
    observation.start_job()
    data_fetcher.reset_yf_fetch_count()
    observation.end_job("ok")

    record = _observation_records(tmp_path)[-1]
    assert record["peak_active_jobs"] == 1
    assert record["counters_unreliable"] is True


def test_observed_function_preserves_result_and_signature(tmp_path):
    import inspect

    def evaluate(symbols, kelly_fraction=0.5):
        return symbols

    observed = scan_observability.observe_scan(evaluate)
    symbols = ["AAA"]
    assert observed(symbols) is symbols
    assert inspect.signature(observed) == inspect.signature(evaluate)
    record = _observation_records(tmp_path)[-1]
    assert record["caller"] == "script"
    assert record["request_id"] is None
    assert record["outcome"] == "ok"
    assert record["counters_unreliable"] is False


def test_observed_error_is_not_swallowed(tmp_path):
    failure = ValueError("artificial work")

    @scan_observability.observe_scan
    def evaluate(symbols):
        raise failure

    with pytest.raises(ValueError) as caught:
        evaluate(["AAA"])
    assert caught.value is failure
    record = _observation_records(tmp_path)[-1]
    assert record["outcome"] == "error"
    assert record["error_type"] == "ValueError"


def test_observation_can_be_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("FINPILOT_SCAN_OBSERVABILITY", "0")
    observed = scan_observability.observe_scan(lambda symbols: symbols)
    symbols = ["AAA"]
    assert observed(symbols) is symbols
    assert not (tmp_path / "scan_timing.jsonl").exists()


def test_log_failure_cannot_break_observed_work(tmp_path, monkeypatch):
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("fixture", encoding="utf-8")
    monkeypatch.setenv("FINPILOT_DIST_DIR", str(blocked))
    observed = scan_observability.observe_scan(lambda symbols: symbols)
    symbols = ["AAA"]
    assert observed(symbols) is symbols


def test_actual_evaluator_is_observed_for_direct_scripts(tmp_path):
    from scanner import evaluate_symbols_parallel

    assert evaluate_symbols_parallel([], use_prefetch=False) == []
    records = _observation_records(tmp_path)
    assert [row["event"] for row in records] == ["job_started", "job_finished"]
    assert records[-1]["caller"] == "script"


class _ConnectedRequest(Request):
    def __init__(self):
        super().__init__({"type": "http", "method": "POST", "path": "/scan", "headers": []})

    async def is_disconnected(self):
        return False


def _stub_scan_dependencies(monkeypatch, evaluate):
    import scanner

    import core.analytics

    monkeypatch.setattr(
        scanner, "evaluate_symbols_parallel", scan_observability.observe_scan(evaluate)
    )
    monkeypatch.setattr(scan_router, "_load_drl_cache", lambda: ({}, False))
    monkeypatch.setattr(
        scan_router, "_enrich_results", lambda rows, *_args: {"AAA": rows[0]} if rows else {}
    )
    persisted = []
    for name in (
        "_persist_shortlist",
        "_persist_shadow_ledger",
        "_auto_add_watchlist",
        "_persist_distribution_export",
    ):

        def persist(*_args, _name=name, **_kwargs):
            persisted.append(_name)

        monkeypatch.setattr(scan_router, name, persist)
    monkeypatch.setattr(core.analytics, "increment_event", lambda *_args: None)
    return persisted


def test_api_success_has_one_request_record_and_unchanged_persistence(tmp_path, monkeypatch):
    row = {"symbol": "AAA"}
    persisted = _stub_scan_dependencies(monkeypatch, lambda symbols, **_kwargs: [row])
    out = asyncio.run(
        scan_router.run_scan(
            scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
            _scan_auth(),
            _ConnectedRequest(),
        )
    )

    assert out == {"AAA": row}
    assert len(persisted) == 4
    assert len(set(persisted)) == 4
    records = _observation_records(tmp_path)
    assert [record["event"] for record in records] == [
        "job_started",
        "job_finished",
        "request_finished",
    ]
    assert len({record["job_id"] for record in records}) == 1
    assert len({record["request_id"] for record in records}) == 1
    assert records[-1]["request_id"] != records[-1]["job_id"]
    assert records[-1]["caller"] == "api_scan"
    assert records[-1]["outcome"] == "ok"
    assert records[-1]["counters_unreliable"] is False
    assert records[-1]["total_s"] == round(records[-1]["eval_s"] + records[-1]["enrich_s"], 2)
    assert records[-1]["persist_s"] >= 0


def test_api_observation_disabled_preserves_legacy_log(tmp_path, monkeypatch):
    monkeypatch.setenv("FINPILOT_SCAN_OBSERVABILITY", "0")
    _stub_scan_dependencies(monkeypatch, lambda symbols, **_kwargs: [])
    assert (
        asyncio.run(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=[], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
        == {}
    )
    records = _observation_records(tmp_path)
    assert len(records) == 1
    assert "event" not in records[0]
    assert records[0]["total_s"] >= 0


def test_api_observation_works_with_real_fastapi_request(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    _stub_scan_dependencies(monkeypatch, lambda symbols, **_kwargs: [])
    app = FastAPI()
    app.include_router(scan_router.router)
    app.dependency_overrides[scan_router.require_auth] = lambda: None
    with TestClient(app) as client:
        response = client.post("/scan", json={"symbols": ["AAA"]})
    assert response.status_code == 200
    assert response.json() == {}
    record = _observation_records(tmp_path)[-1]
    assert record["event"] == "request_finished"
    assert record["outcome"] == "ok"
    assert record["request_id"]


def test_api_error_records_request_and_worker(tmp_path, monkeypatch):
    def evaluate(symbols, **_kwargs):
        raise ValueError("artificial work")

    persisted = _stub_scan_dependencies(monkeypatch, evaluate)
    with pytest.raises(scan_router.HTTPException) as caught:
        asyncio.run(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
    assert caught.value.status_code == 500
    assert persisted == []
    records = _observation_records(tmp_path)
    assert records[-2]["job_outcome"] == records[-1]["request_outcome"] == "error"


def test_api_import_failure_is_recorded(tmp_path, monkeypatch):
    import scanner

    monkeypatch.delattr(scanner, "evaluate_symbols_parallel")
    with pytest.raises(scan_router.HTTPException) as caught:
        asyncio.run(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
    assert caught.value.status_code == 503
    record = _observation_records(tmp_path)[-1]
    assert record["outcome"] == "error"
    assert record["worker_started"] is False
    assert record["active_jobs_at_start"] is None


@pytest.mark.parametrize("cancel_waiter", [False, True])
def test_api_timeout_or_cancellation_does_not_end_worker(tmp_path, monkeypatch, cancel_waiter):
    started = threading.Event()
    release = threading.Event()
    completed = threading.Event()
    write_record = scan_observability.append_scan_timing_log

    def record(timing, universe):
        write_record(timing, universe)
        if timing.get("event") == "job_finished":
            completed.set()

    def evaluate(symbols, **_kwargs):
        started.set()
        assert release.wait(5)
        return []

    monkeypatch.setattr(scan_observability, "append_scan_timing_log", record)
    monkeypatch.setattr(scan_router, "_SCAN_TIMEOUT_SECONDS", 0.1)
    persisted = _stub_scan_dependencies(monkeypatch, evaluate)

    async def scenario():
        task = asyncio.create_task(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
        try:
            assert await asyncio.to_thread(started.wait, 5)
            if cancel_waiter:
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            else:
                with pytest.raises(scan_router.HTTPException) as caught:
                    await task
                assert caught.value.status_code == 504
            assert len(scan_observability._ACTIVE_JOBS) == 1
            request_record = _observation_records(tmp_path)[-1]
            assert request_record["outcome"] == ("client_gone" if cancel_waiter else "timeout")
            assert request_record["worker_finished"] is False
        finally:
            release.set()
            assert await asyncio.to_thread(completed.wait, 5)

    asyncio.run(scenario())
    assert persisted == []
    records = _observation_records(tmp_path)
    assert records[-1]["event"] == "job_finished"
    assert records[-1]["job_outcome"] == "ok"
    assert records[-1]["request_outcome"] == ("client_gone" if cancel_waiter else "timeout")
    assert len({record["job_id"] for record in records}) == 1


def test_detected_disconnect_is_observation_only(tmp_path, monkeypatch):
    release = threading.Event()
    _stub_scan_dependencies(monkeypatch, lambda symbols, **_kwargs: [] if release.wait(5) else None)

    async def scenario():
        disconnected = asyncio.Event()

        class DisconnectedRequest(_ConnectedRequest):
            async def is_disconnected(self):
                disconnected.set()
                return True

        task = asyncio.create_task(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                DisconnectedRequest(),
            )
        )
        try:
            await asyncio.wait_for(disconnected.wait(), 2)
            assert not task.done()
        finally:
            release.set()
        assert await task == {}

    asyncio.run(scenario())
    records = _observation_records(tmp_path)
    assert any(record["event"] == "request_disconnected" for record in records)
    assert records[-1]["request_outcome"] == "client_gone"
    assert records[-1]["job_outcome"] == "ok"


@pytest.mark.parametrize("fails", [False, True])
def test_scanner_agent_uses_shared_observation(tmp_path, monkeypatch, fails):
    import scanner
    from agents import scanner_agent

    def evaluate(symbols, **_kwargs):
        if fails:
            raise ValueError("artificial work")
        return []

    monkeypatch.setattr(
        scanner, "evaluate_symbols_parallel", scan_observability.observe_scan(evaluate)
    )
    monkeypatch.setattr(scanner_agent, "_load_drl_cache", lambda: ({}, False))
    result = scanner_agent.ScannerAgent().run(AgentContext(symbols=["AAA"]))
    assert result.success is not fails
    records = _observation_records(tmp_path)
    assert all(record["caller"] == "scanner_agent" for record in records)
    assert len({record["job_id"] for record in records}) == 1
    assert records[-1]["outcome"] == ("error" if fails else "ok")
    assert records[-1]["request_id"] is None


def test_api_and_agent_overlap_share_registry_without_serialization(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    from agents import scanner_agent

    barrier = threading.Barrier(2)

    def evaluate(symbols, **_kwargs):
        barrier.wait(timeout=5)
        return []

    _stub_scan_dependencies(monkeypatch, evaluate)
    monkeypatch.setattr(scanner_agent, "_load_drl_cache", lambda: ({}, False))
    with ThreadPoolExecutor(max_workers=2) as pool:
        api_result = pool.submit(
            asyncio.run,
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            ),
        )
        agent_result = pool.submit(scanner_agent.ScannerAgent().run, AgentContext(symbols=["AAA"]))
        assert api_result.result(timeout=5) == {}
        assert agent_result.result(timeout=5).success
    finished = [row for row in _observation_records(tmp_path) if row["event"] == "job_finished"]
    assert {row["caller"] for row in finished} == {"api_scan", "scanner_agent"}
    assert len({row["job_id"] for row in finished}) == 2
    assert all(row["peak_active_jobs"] == 2 and row["counters_unreliable"] for row in finished)


@pytest.mark.parametrize("queue_capacity", [0, 1])
@pytest.mark.parametrize("estimated_job_seconds", [1, 600])
def test_coordinator_idle_job_allows_zero_queue_wait(queue_capacity, estimated_job_seconds):
    coordinator = scan_coordinator.ScanCoordinator(
        queue_capacity=queue_capacity,
        queue_wait_seconds=0,
        estimated_job_seconds=estimated_job_seconds,
    )
    try:
        handle = coordinator.submit(
            "idle", lambda: "completed", budget_seconds=estimated_job_seconds
        )
        assert handle.result(timeout=5) == "completed"
        assert coordinator._jobs == {}
    finally:
        coordinator.shutdown()


def test_coordinator_timeout_keeps_actual_job_slot():
    started = threading.Event()
    release = threading.Event()
    second_started = threading.Event()
    coordinator = scan_coordinator.ScanCoordinator(
        estimated_job_seconds=0.01, cooperative_cancel=False
    )

    def first_work():
        started.set()
        assert release.wait(5)
        return "first"

    try:
        first = coordinator.submit("first", first_work)
        assert started.wait(5)
        with pytest.raises(TimeoutError):
            first.result(timeout=0.01)
        second = coordinator.submit("second", lambda: second_started.set() or "second")
        assert not second_started.is_set()
        assert len(coordinator._jobs) == 2
        release.set()
        assert first.future.result(timeout=5) == "first"
        assert second.result(timeout=5) == "second"
    finally:
        release.set()
        coordinator.shutdown()


def test_coordinator_dedupe_and_last_waiter_cancel():
    started = threading.Event()
    release = threading.Event()
    calls = []
    coordinator = scan_coordinator.ScanCoordinator(estimated_job_seconds=0.01)

    def work():
        calls.append("work")
        started.set()
        assert release.wait(5)
        scan_coordinator.check_cancelled()
        return "result"

    try:
        first = coordinator.submit("same", work)
        assert started.wait(5)
        second = coordinator.submit("same", work)
        assert first.job is second.job
        first.detach()
        assert not first.job.cancelled.is_set()
        second.detach()
        assert first.job.cancelled.is_set()
        release.set()
        with pytest.raises(scan_coordinator.ScanCancelled):
            second.future.result(timeout=5)
        assert calls == ["work"]
        assert coordinator._jobs == {}
    finally:
        release.set()
        coordinator.shutdown()


def test_coordinator_bounded_queue_and_execution_budget():
    started = threading.Event()
    release = threading.Event()
    coordinator = scan_coordinator.ScanCoordinator(estimated_job_seconds=0.01)

    def work():
        started.set()
        assert release.wait(5)

    try:
        first = coordinator.submit("first", work)
        assert started.wait(5)
        second = coordinator.submit("second", lambda: None)
        with pytest.raises(scan_coordinator.ScanBusy, match="full"):
            coordinator.submit("third", lambda: None)
        assert coordinator.submit("first", work).job is first.job
        release.set()
        first.result(timeout=5)
        second.result(timeout=5)
        with pytest.raises(scan_coordinator.ScanBusy, match="budget"):
            coordinator.submit("budget", lambda: None, budget_seconds=0.001)
    finally:
        release.set()
        coordinator.shutdown()


def test_coordinator_shared_errors_reach_every_waiter():
    started = threading.Event()
    release = threading.Event()
    error = ValueError("artificial shared failure")
    coordinator = scan_coordinator.ScanCoordinator(estimated_job_seconds=0.01)

    def work():
        started.set()
        assert release.wait(5)
        raise error

    try:
        first = coordinator.submit("same", work)
        assert started.wait(5)
        second = coordinator.submit("same", work)
        release.set()
        for handle in (first, second):
            with pytest.raises(ValueError) as caught:
                handle.result(timeout=5)
            assert caught.value is error
        assert coordinator._jobs == {}
    finally:
        release.set()
        coordinator.shutdown()


def test_coordinator_job_and_waiter_observations_are_separate(tmp_path):
    started = threading.Event()
    release = threading.Event()
    coordinator = scan_coordinator.ScanCoordinator(estimated_job_seconds=0.01)
    first_observation = scan_observability.ScanObservation("api_scan", 1, "request-one")
    second_observation = scan_observability.ScanObservation("api_scan", 1, "request-two")

    @scan_observability.observe_scan
    def work(symbols):
        started.set()
        assert release.wait(5)
        return symbols

    try:
        first = coordinator.submit("same", lambda: work(["AAA"]), observation=first_observation)
        assert started.wait(5)
        second = coordinator.submit("same", lambda: work(["AAA"]), observation=second_observation)
        first.detach()
        first_observation.finish_request("timeout")
        release.set()
        assert second.result(timeout=5) == ["AAA"]
        second_observation.finish_request("ok")
        records = _observation_records(tmp_path)
        assert len([row for row in records if row["event"] == "job_started"]) == 1
        assert len([row for row in records if row["event"] == "job_finished"]) == 1
        assert len({row["job_id"] for row in records}) == 1
        waiters = [row for row in records if row["event"] == "request_finished"]
        assert {row["request_id"] for row in waiters} == {"request-one", "request-two"}
        assert [row["outcome"] for row in waiters] == ["timeout", "ok"]
        assert all(row["job_outcome"] == "ok" for row in waiters[1:])
    finally:
        release.set()
        coordinator.shutdown()


def test_coordinator_identity_preserves_scope_parameters_and_effective_settings(monkeypatch):
    from scanner import config

    key = scan_coordinator.make_key("api", ["AAA"], {"kelly": 0.5}, ("user-one", "free"))
    assert key == scan_coordinator.make_key("api", ["AAA"], {"kelly": 0.5}, ("user-one", "free"))
    assert key != scan_coordinator.make_key("api", ["AAA"], {"kelly": 0.4}, ("user-one", "free"))
    assert key != scan_coordinator.make_key("api", ["AAA"], {"kelly": 0.5}, ("user-two", "free"))
    assert key != scan_coordinator.make_key("agent", ["AAA"], {"kelly": 0.5}, ("user-one", "free"))
    monkeypatch.setitem(config.SETTINGS, "min_signal_score", 7)
    assert key != scan_coordinator.make_key("api", ["AAA"], {"kelly": 0.5}, ("user-one", "free"))


def test_coordinator_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("FINPILOT_SCAN_COORDINATOR", raising=False)
    assert not scan_coordinator.enabled()


@pytest.fixture
def coordinated_scans(monkeypatch):
    coordinator = scan_coordinator.ScanCoordinator(estimated_job_seconds=0.01)
    monkeypatch.setenv("FINPILOT_SCAN_COORDINATOR", "1")
    monkeypatch.setattr(scan_coordinator, "_COORDINATOR", coordinator)
    yield coordinator
    coordinator.shutdown()
    assert coordinator._jobs == {}


def _scan_auth(user="test-user"):
    return TokenPayload(sub=user, role="free", type="access", exp=0, iat=0, jti="fixture")


def test_coordinated_api_dedupes_and_persists_once(tmp_path, monkeypatch, coordinated_scans):
    started = threading.Event()
    release = threading.Event()
    calls = []

    def evaluate(symbols, **_kwargs):
        calls.append(symbols)
        started.set()
        assert release.wait(5)
        return [{"symbol": "AAA"}]

    persisted = _stub_scan_dependencies(monkeypatch, evaluate)

    async def scenario():
        first = asyncio.create_task(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
        assert await asyncio.to_thread(started.wait, 5)
        second = asyncio.create_task(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
        await asyncio.to_thread(lambda: None)
        try:
            assert len(coordinated_scans._jobs) == 1
            assert len(next(iter(coordinated_scans._jobs.values())).waiters) == 2
        finally:
            release.set()
        assert await first == await second == {"AAA": {"symbol": "AAA"}}

    asyncio.run(scenario())
    assert calls == [["AAA"]]
    assert len(persisted) == len(set(persisted)) == 4
    records = _observation_records(tmp_path)
    assert len([row for row in records if row["event"] == "job_finished"]) == 1
    waiters = [row for row in records if row["event"] == "request_finished"]
    assert len(waiters) == 2 and len({row["request_id"] for row in waiters}) == 2
    assert len({row["job_id"] for row in records}) == 1


def test_coordinated_evaluator_and_agent_use_shared_slots(monkeypatch, coordinated_scans):
    from agents import scanner_agent
    from scanner import evaluate

    monkeypatch.setattr(scanner_agent, "_load_drl_cache", lambda: ({}, False))
    assert evaluate.evaluate_symbols_parallel([], use_prefetch=False) == []
    assert scanner_agent.ScannerAgent().run(AgentContext(symbols=[])).success
    assert coordinated_scans._jobs == {}


def test_coordinated_cancelled_api_skips_persistence(tmp_path, monkeypatch, coordinated_scans):
    started = threading.Event()
    release = threading.Event()

    def evaluate(symbols, **_kwargs):
        started.set()
        assert release.wait(5)
        return []

    persisted = _stub_scan_dependencies(monkeypatch, evaluate)

    async def scenario():
        task = asyncio.create_task(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
        try:
            assert await asyncio.to_thread(started.wait, 5)
            job = next(iter(coordinated_scans._jobs.values()))
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert job.cancelled.is_set()
            assert len(coordinated_scans._jobs) == 1
            release.set()
            with pytest.raises(scan_coordinator.ScanCancelled):
                await asyncio.to_thread(job.future.result, 5)
        finally:
            release.set()

    asyncio.run(scenario())
    assert persisted == []
    finished = [row for row in _observation_records(tmp_path) if row["event"] == "job_finished"]
    assert finished[-1]["job_outcome"] == "client_gone"


def test_coordinator_returns_independent_waiter_results():
    started = threading.Event()
    release = threading.Event()
    coordinator = scan_coordinator.ScanCoordinator(estimated_job_seconds=0.01)

    def work():
        started.set()
        assert release.wait(5)
        return [{"nested": {"value": 1}}]

    try:
        first = coordinator.submit("same", work)
        assert started.wait(5)
        second = coordinator.submit("same", work)
        release.set()
        first_result = first.result(timeout=5)
        first_result[0]["nested"]["value"] = 2
        assert second.result(timeout=5) == [{"nested": {"value": 1}}]
    finally:
        release.set()
        coordinator.shutdown()


def test_coordinator_queue_wait_expiry_skips_work(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(scan_coordinator.time, "monotonic", lambda: clock[0])
    started = threading.Event()
    release = threading.Event()
    called = []
    coordinator = scan_coordinator.ScanCoordinator(estimated_job_seconds=0.01)

    def work():
        started.set()
        assert release.wait(5)

    try:
        first = coordinator.submit("first", work)
        assert started.wait(5)
        second = coordinator.submit("second", lambda: called.append("second"))
        clock[0] = 221.0
        release.set()
        first.result(timeout=5)
        with pytest.raises(scan_coordinator.ScanBusy, match="expired"):
            second.result(timeout=5)
        assert called == []
    finally:
        release.set()
        coordinator.shutdown()


def test_coordinator_estimated_wait_rejects_before_work():
    started = threading.Event()
    release = threading.Event()
    coordinator = scan_coordinator.ScanCoordinator()

    def work():
        started.set()
        assert release.wait(5)

    try:
        first = coordinator.submit("first", work)
        assert started.wait(5)
        with pytest.raises(scan_coordinator.ScanBusy, match="budget"):
            coordinator.submit("second", lambda: None)
        release.set()
        first.result(timeout=5)
    finally:
        release.set()
        coordinator.shutdown()


def test_coordinator_cancelled_queued_job_never_runs():
    started = threading.Event()
    release = threading.Event()
    called = []
    coordinator = scan_coordinator.ScanCoordinator(estimated_job_seconds=0.01)

    def work():
        started.set()
        assert release.wait(5)

    try:
        first = coordinator.submit("first", work)
        assert started.wait(5)
        second = coordinator.submit("second", lambda: called.append("second"))
        second.detach()
        release.set()
        first.result(timeout=5)
        with pytest.raises(scan_coordinator.ScanCancelled):
            second.future.result(timeout=5)
        assert called == []
    finally:
        release.set()
        coordinator.shutdown()


def test_coordinated_one_waiter_cancel_does_not_stop_shared_job(
    tmp_path, monkeypatch, coordinated_scans
):
    started = threading.Event()
    release = threading.Event()

    def evaluate(symbols, **_kwargs):
        started.set()
        assert release.wait(5)
        return [{"symbol": "AAA"}]

    persisted = _stub_scan_dependencies(monkeypatch, evaluate)

    async def scenario():
        first = asyncio.create_task(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
        assert await asyncio.to_thread(started.wait, 5)
        second = asyncio.create_task(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
        await asyncio.to_thread(lambda: None)
        try:
            job = next(iter(coordinated_scans._jobs.values()))
            assert len(job.waiters) == 2
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
            assert not job.cancelled.is_set()
            release.set()
            assert await second == {"AAA": {"symbol": "AAA"}}
        finally:
            release.set()

    asyncio.run(scenario())
    assert len(persisted) == len(set(persisted)) == 4
    records = _observation_records(tmp_path)
    waiters = [row for row in records if row["event"] == "request_finished"]
    assert [row["outcome"] for row in waiters] == ["client_gone", "ok"]
    assert len({row["job_id"] for row in records}) == 1


def test_coordinated_api_timeout_retains_worker_and_skips_persistence(
    tmp_path, monkeypatch, coordinated_scans
):
    started = threading.Event()
    release = threading.Event()

    def evaluate(symbols, **_kwargs):
        started.set()
        assert release.wait(5)
        return []

    monkeypatch.setattr(scan_router, "_SCAN_TIMEOUT_SECONDS", 0.1)
    persisted = _stub_scan_dependencies(monkeypatch, evaluate)

    async def scenario():
        task = asyncio.create_task(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
        try:
            assert await asyncio.to_thread(started.wait, 5)
            job = next(iter(coordinated_scans._jobs.values()))
            with pytest.raises(scan_router.HTTPException) as caught:
                await task
            assert caught.value.status_code == 504
            assert len(coordinated_scans._jobs) == 1
            assert job.cancelled.is_set()
            release.set()
            with pytest.raises(scan_coordinator.ScanCancelled):
                await asyncio.to_thread(job.future.result, 5)
        finally:
            release.set()

    asyncio.run(scenario())
    assert persisted == []
    records = _observation_records(tmp_path)
    assert any(row["outcome"] == "timeout" for row in records)


def test_coordinated_busy_api_is_retryable_and_does_not_reset_active_counters(
    monkeypatch, coordinated_scans
):
    started = threading.Event()
    release = threading.Event()
    resets = []
    monkeypatch.setattr(coordinated_scans, "queue_capacity", 0)
    monkeypatch.setattr(data_fetcher, "reset_yf_fetch_count", lambda: resets.append("reset"))

    def evaluate(symbols, **_kwargs):
        started.set()
        assert release.wait(5)
        return []

    _stub_scan_dependencies(monkeypatch, evaluate)

    async def scenario():
        first = asyncio.create_task(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
        assert await asyncio.to_thread(started.wait, 5)
        try:
            with pytest.raises(scan_router.HTTPException) as caught:
                await scan_router.run_scan(
                    scan_router.ScanRequest(symbols=["BBB"], kelly_fraction=0.5),
                    _scan_auth(),
                    _ConnectedRequest(),
                )
            assert caught.value.status_code == 503
            assert caught.value.headers == {"Retry-After": "5"}
            assert resets == ["reset"]
        finally:
            release.set()
        assert await first == {}

    asyncio.run(scenario())


def test_coordinated_prefetch_cancel_stops_before_evaluation(monkeypatch, coordinated_scans):
    from scanner import evaluate

    started = threading.Event()
    release = threading.Event()
    evaluated = []

    def prefetch(symbols, **_kwargs):
        started.set()
        assert release.wait(5)
        return {}

    monkeypatch.setattr(evaluate, "prefetch_symbols_multi_timeframe", prefetch)
    monkeypatch.setattr(evaluate, "evaluate_symbol", lambda *args, **kwargs: evaluated.append(args))
    persisted = _stub_scan_dependencies(monkeypatch, evaluate.evaluate_symbols_parallel)

    async def scenario():
        task = asyncio.create_task(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA", "BBB"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
        try:
            assert await asyncio.to_thread(started.wait, 5)
            job = next(iter(coordinated_scans._jobs.values()))
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            release.set()
            with pytest.raises(scan_coordinator.ScanCancelled):
                await asyncio.to_thread(job.future.result, 5)
        finally:
            release.set()

    asyncio.run(scenario())
    assert evaluated == []
    assert persisted == []


def test_coordinated_sequential_cancel_stops_before_next_symbol(monkeypatch, coordinated_scans):
    from scanner import evaluate

    started = threading.Event()
    release = threading.Event()
    evaluated = []

    def evaluate_one(symbol, *_args, **_kwargs):
        evaluated.append(symbol)
        started.set()
        assert release.wait(5)
        return {"symbol": symbol}

    monkeypatch.setattr(evaluate, "evaluate_symbol", evaluate_one)
    handle = coordinated_scans.submit(
        "sequential", lambda: evaluate.evaluate_symbols_parallel(["AAA", "BBB"], use_prefetch=False)
    )
    try:
        assert started.wait(5)
        handle.detach()
        release.set()
        with pytest.raises(scan_coordinator.ScanCancelled):
            handle.future.result(timeout=5)
        assert evaluated == ["AAA"]
    finally:
        release.set()


def test_coordinated_api_works_with_fastapi_request(monkeypatch, coordinated_scans):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    _stub_scan_dependencies(monkeypatch, lambda symbols, **_kwargs: [])
    app = FastAPI()
    app.include_router(scan_router.router)
    app.dependency_overrides[scan_router.require_auth] = _scan_auth
    with TestClient(app) as client:
        response = client.post("/scan", json={"symbols": ["AAA"]})
    assert response.status_code == 200
    assert response.json() == {}


def test_coordinated_api_tcp_restart_preserves_job_ownership(
    tmp_path, monkeypatch, coordinated_scans
):
    import socket
    from concurrent.futures import ThreadPoolExecutor
    from contextlib import contextmanager

    import httpx
    import uvicorn
    from fastapi import FastAPI

    started = threading.Event()
    attached = threading.Event()
    release = threading.Event()
    calls = []
    submit = coordinated_scans.submit

    def evaluate(symbols, **_kwargs):
        calls.append(symbols)
        started.set()
        assert release.wait(5)
        return [{"symbol": "AAA"}]

    def tracked_submit(*args, **kwargs):
        handle = submit(*args, **kwargs)
        if len(handle.job.waiters) == 2:
            attached.set()
        return handle

    persisted = _stub_scan_dependencies(monkeypatch, evaluate)
    monkeypatch.setattr(coordinated_scans, "submit", tracked_submit)

    @contextmanager
    def serve():
        ready = threading.Event()
        app = FastAPI()
        app.include_router(scan_router.router)
        app.dependency_overrides[scan_router.require_auth] = _scan_auth

        class ReadyServer(uvicorn.Server):
            async def startup(self, sockets: list[socket.socket] | None = None) -> None:
                await super().startup(sockets=sockets)
                ready.set()

        config = uvicorn.Config(app, lifespan="off", log_level="error", access_log=False)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            server = ReadyServer(config)
            worker = threading.Thread(
                target=server.run, kwargs={"sockets": [listener]}, daemon=True
            )
            worker.start()
            try:
                assert ready.wait(5)
                yield f"http://127.0.0.1:{listener.getsockname()[1]}/scan"
            finally:
                release.set()
                server.should_exit = True
                worker.join(5)
                assert not worker.is_alive()

    def post(url):
        with httpx.Client(timeout=10, trust_env=False) as client:
            response = client.post(url, json={"symbols": ["AAA"], "kelly_fraction": 0.5})
            assert response.status_code == 200
            return response.json()

    for _generation in range(2):
        started.clear()
        attached.clear()
        release.clear()
        with serve() as url, ThreadPoolExecutor(max_workers=2) as clients:
            first = clients.submit(post, url)
            try:
                assert started.wait(5)
                second = clients.submit(post, url)
                assert attached.wait(5)
            finally:
                release.set()
            assert (
                first.result(timeout=10) == second.result(timeout=10) == {"AAA": {"symbol": "AAA"}}
            )
        assert coordinated_scans._jobs == {}

    assert calls == [["AAA"], ["AAA"]]
    assert len(persisted) == 8
    assert all(persisted.count(name) == 2 for name in set(persisted))
    records = _observation_records(tmp_path)
    jobs = [row for row in records if row["event"] == "job_finished"]
    waiters = [row for row in records if row["event"] == "request_finished"]
    assert len(jobs) == len({row["job_id"] for row in jobs}) == 2
    assert len(waiters) == len({row["request_id"] for row in waiters}) == 4
    assert all(sum(row["job_id"] == job["job_id"] for row in waiters) == 2 for job in jobs)
    assert all(row["peak_active_jobs"] == 1 for row in jobs)


def test_coordinated_api_does_not_require_observation(tmp_path, monkeypatch, coordinated_scans):
    monkeypatch.setenv("FINPILOT_SCAN_OBSERVABILITY", "0")
    persisted = _stub_scan_dependencies(monkeypatch, lambda symbols, **_kwargs: [])
    assert (
        asyncio.run(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
        == {}
    )
    assert len(persisted) == 4
    records = _observation_records(tmp_path)
    assert len(records) == 1
    assert "observation_version" not in records[0]


def test_coordinated_api_and_agent_never_overlap(tmp_path, monkeypatch, coordinated_scans):
    from agents import scanner_agent

    started = threading.Event()
    release = threading.Event()
    agent_queued = threading.Event()
    calls = []
    submit = coordinated_scans.submit

    def tracked_submit(*args, **kwargs):
        handle = submit(*args, **kwargs)
        observation = kwargs.get("observation")
        if observation is not None and observation.caller == "scanner_agent":
            agent_queued.set()
        return handle

    def evaluate(symbols, **_kwargs):
        calls.append(symbols)
        if symbols == ["AAA"]:
            started.set()
            assert release.wait(5)
        return []

    monkeypatch.setattr(coordinated_scans, "submit", tracked_submit)
    _stub_scan_dependencies(monkeypatch, evaluate)
    monkeypatch.setattr(scanner_agent, "_load_drl_cache", lambda: ({}, False))

    async def scenario():
        api_task = asyncio.create_task(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                _ConnectedRequest(),
            )
        )
        assert await asyncio.to_thread(started.wait, 5)
        agent_task = asyncio.create_task(
            asyncio.to_thread(scanner_agent.ScannerAgent().run, AgentContext(symbols=["BBB"]))
        )
        try:
            assert await asyncio.to_thread(agent_queued.wait, 5)
            assert calls == [["AAA"]]
        finally:
            release.set()
        assert await api_task == {}
        assert (await agent_task).success

    asyncio.run(scenario())
    finished = [row for row in _observation_records(tmp_path) if row["event"] == "job_finished"]
    assert len(finished) == 2
    assert all(row["peak_active_jobs"] == 1 for row in finished)
    assert {row["caller"] for row in finished} == {"api_scan", "scanner_agent"}
    assert all(row["coordinator_version"] == 1 for row in finished)


def test_coordinated_disconnect_detaches_last_waiter(monkeypatch, coordinated_scans):
    started = threading.Event()
    release = threading.Event()
    disconnected = threading.Event()

    def evaluate(symbols, **_kwargs):
        started.set()
        assert release.wait(5)
        return []

    class DisconnectedRequest(_ConnectedRequest):
        async def is_disconnected(self):
            assert await asyncio.to_thread(started.wait, 5)
            disconnected.set()
            return True

    persisted = _stub_scan_dependencies(monkeypatch, evaluate)

    async def scenario():
        task = asyncio.create_task(
            scan_router.run_scan(
                scan_router.ScanRequest(symbols=["AAA"], kelly_fraction=0.5),
                _scan_auth(),
                DisconnectedRequest(),
            )
        )
        try:
            assert await asyncio.to_thread(started.wait, 5)
            assert await asyncio.to_thread(disconnected.wait, 5)
            job = next(iter(coordinated_scans._jobs.values()))
            assert job.cancelled.is_set()
            assert len(coordinated_scans._jobs) == 1
            release.set()
            with pytest.raises(scan_router.HTTPException) as caught:
                await task
            assert caught.value.status_code == 499
        finally:
            release.set()

    asyncio.run(scenario())
    assert persisted == []


def test_coordinator_finished_work_is_not_reused():
    coordinator = scan_coordinator.ScanCoordinator(estimated_job_seconds=0.01)
    calls = []
    try:
        first = coordinator.submit("same", lambda: calls.append(1) or len(calls))
        assert first.result(timeout=5) == 1
        second = coordinator.submit("same", lambda: calls.append(1) or len(calls))
        assert second.result(timeout=5) == 2
        assert first.job.job_id != second.job.job_id
    finally:
        coordinator.shutdown()


def test_coordinator_dedupe_flag_and_two_slots_are_respected():
    barrier = threading.Barrier(2)
    release = threading.Event()
    coordinator = scan_coordinator.ScanCoordinator(
        max_concurrent=2, dedupe=False, estimated_job_seconds=0.01
    )

    def work():
        barrier.wait(timeout=5)
        assert release.wait(5)
        return "done"

    try:
        first = coordinator.submit("same", work)
        second = coordinator.submit("same", work)
        assert first.job is not second.job
        release.set()
        assert first.result(timeout=5) == second.result(timeout=5) == "done"
    finally:
        release.set()
        coordinator.shutdown()


def test_coordinator_refresh_rejoins_orphan_before_cancellation_boundary():
    started = threading.Event()
    release = threading.Event()
    coordinator = scan_coordinator.ScanCoordinator(estimated_job_seconds=0.01)
    calls = []

    def work():
        calls.append("work")
        started.set()
        assert release.wait(5)
        scan_coordinator.check_cancelled()
        return "result"

    try:
        first = coordinator.submit("same", work)
        assert started.wait(5)
        first.detach()
        assert first.job.cancelled.is_set()
        refreshed = coordinator.submit("same", work)
        assert refreshed.job is first.job
        assert not first.job.cancelled.is_set()
        release.set()
        assert refreshed.result(timeout=5) == "result"
        assert calls == ["work"]
    finally:
        release.set()
        coordinator.shutdown()


def test_coordinator_refresh_cannot_rejoin_committed_cancellation():
    started = threading.Event()
    reach_boundary = threading.Event()
    committed = threading.Event()
    release = threading.Event()
    coordinator = scan_coordinator.ScanCoordinator(estimated_job_seconds=0.01)

    def work():
        started.set()
        assert reach_boundary.wait(5)
        try:
            scan_coordinator.check_cancelled()
        except scan_coordinator.ScanCancelled:
            committed.set()
            assert release.wait(5)
            raise

    try:
        first = coordinator.submit("same", work)
        assert started.wait(5)
        first.detach()
        reach_boundary.set()
        assert committed.wait(5)
        refreshed = coordinator.submit("same", lambda: "new result")
        assert refreshed.job is not first.job
        release.set()
        with pytest.raises(scan_coordinator.ScanCancelled):
            first.future.result(timeout=5)
        assert refreshed.result(timeout=5) == "new result"
    finally:
        reach_boundary.set()
        release.set()
        coordinator.shutdown()
