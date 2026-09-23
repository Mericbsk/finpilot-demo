from __future__ import annotations

import json

import pandas as pd
from api.routers import scan as scan_router
from scanner import data_fetcher, performance


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
