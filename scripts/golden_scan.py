"""Golden-dataset regression harness — P0.2 (2026-07-31 scanner audit).

The safety net that lets us change the scanner's DATA path (P1: staged funnel,
EODHD bulk, cache, parallelism) WITHOUT silently changing its DECISIONS. It
captures a golden baseline (per-symbol composite_score / eligibility / tier +
top-N ranking) on a fixed symbol set, and later re-runs and diffs against it.

Governance: a data-path optimisation is "safe" only if `compare` reports ZERO
differences. Any change to composite_score, eligibility, or top-N is NOT a pure
optimisation — it is a Level B product/strategy change requiring separate backtest.

Usage:
    python scripts/golden_scan.py capture              # write golden baseline
    python scripts/golden_scan.py capture --symbols A,B,C
    python scripts/golden_scan.py compare              # re-run + diff (exit 1 if changed)

The pure diff logic (`snapshot_from_results`, `diff_snapshots`) has no network
dependency and is unit-tested by `python scripts/golden_scan.py --selftest`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:  # Python 3.11+ (repo runtime); fall back on 3.10 so the harness is portable.
    from datetime import UTC
except ImportError:  # pragma: no cover
    UTC = UTC

# Allow `python scripts/golden_scan.py` from the repo root: put the repo root on
# sys.path so `from scanner import ...` resolves (script dir alone is not enough).
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# A fixed, representative universe: liquid large caps + mid + a few thinner names
# (the thin ones are exactly where the IEX-intraday fallback bites, so they must
# be in the golden set). Kept small so a capture/compare runs quickly.
DEFAULT_SYMBOLS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "AMD",
    "NFLX",
    "AVGO",
    "JPM",
    "BAC",
    "XOM",
    "PFE",
    "KO",
    "INTC",
    "CSCO",
    "ABNB",
    "SOFI",
    "PLTR",
]

_GOLDEN_PATH = Path("data/golden/golden_baseline.json")

# The per-symbol fields that DEFINE a scan decision. If any of these change for
# any symbol, the optimisation altered behaviour and must be escalated.
_DECISION_FIELDS = (
    "composite_score",
    "filter_score",
    "selection_eligible",
    "entry_ok",
    "conviction_tier",
    "direction",
)


def snapshot_from_results(results: list[dict] | dict) -> dict:
    """Reduce raw scanner results to the decision-defining snapshot (pure).

    Returns {"by_symbol": {sym: {field: value}}, "top_n": [sym, ...]} where
    top_n is ordered by composite_score desc (ties broken by symbol for
    determinism). No network, no side effects — safe to unit-test.
    """
    rows = list(results.values()) if isinstance(results, dict) else list(results)
    by_symbol: dict[str, dict] = {}
    for r in rows:
        sym = str(r.get("symbol") or r.get("ticker") or "").upper()
        if not sym:
            continue
        by_symbol[sym] = {f: r.get(f) for f in _DECISION_FIELDS}
    top_n = sorted(
        by_symbol,
        key=lambda s: (-(by_symbol[s].get("composite_score") or 0), s),
    )
    return {"by_symbol": by_symbol, "top_n": top_n}


def diff_snapshots(old: dict, new: dict, top_k: int = 10) -> list[str]:
    """Return a list of human-readable differences (empty == identical). Pure.

    Checks: symbol set, every decision field per symbol, and the top-K ordering.
    """
    diffs: list[str] = []
    old_by, new_by = old.get("by_symbol", {}), new.get("by_symbol", {})

    missing = sorted(set(old_by) - set(new_by))
    added = sorted(set(new_by) - set(old_by))
    if missing:
        diffs.append(f"Kaybolan sembol(ler): {missing}")
    if added:
        diffs.append(f"Yeni sembol(ler): {added}")

    for sym in sorted(set(old_by) & set(new_by)):
        for field in _DECISION_FIELDS:
            ov, nv = old_by[sym].get(field), new_by[sym].get(field)
            if ov != nv:
                diffs.append(f"{sym}.{field}: {ov!r} → {nv!r}")

    old_top, new_top = old.get("top_n", [])[:top_k], new.get("top_n", [])[:top_k]
    if old_top != new_top:
        diffs.append(f"Top-{top_k} sıralaması değişti:\n    eski: {old_top}\n    yeni: {new_top}")
    return diffs


def _write_timing_probe(
    symbols: list[str], eval_s: float, yf_fallback: int, alpaca_miss: dict
) -> None:
    """Append a P0.1 telemetry line so a golden run doubles as a timing probe.

    Lets us get REAL per-timeframe Alpaca(IEX) miss counts without a full-universe
    scan. Best-effort — never breaks capture/compare.
    """
    try:
        path = Path("data/distribution/scan_timing.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "date": datetime.now(tz=UTC).strftime("%Y-%m-%d"),
            "universe": len(symbols),
            "symbols": len(symbols),
            "eval_s": eval_s,
            "enrich_s": 0.0,
            "total_s": eval_s,
            "yf_fallback": yf_fallback,
            "alpaca_miss": alpaca_miss,
            "source": "golden",
        }
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except Exception:  # pragma: no cover
        pass


def _run_scanner(symbols: list[str]) -> dict:
    """Run the real scanner on `symbols`. Imported lazily so --selftest and the
    pure functions never require pandas/yfinance/alpaca. Also emits a P0.1 timing
    probe (real Alpaca-miss counts) so the golden run feeds the timing report."""
    import time as _time  # noqa: PLC0415

    from scanner import evaluate_symbols_parallel  # noqa: PLC0415

    try:
        from scanner.data_fetcher import (  # noqa: PLC0415
            alpaca_miss_by_tf,
            reset_yf_fetch_count,
            yf_fetch_count,
        )

        reset_yf_fetch_count()
        _counters = True
    except Exception:
        _counters = False

    _t0 = _time.perf_counter()
    results = evaluate_symbols_parallel(symbols=symbols, kelly_fraction=0.5)
    _eval_s = round(_time.perf_counter() - _t0, 2)

    if _counters:
        _write_timing_probe(symbols, _eval_s, yf_fetch_count(), alpaca_miss_by_tf())
    return snapshot_from_results(results)


def capture(symbols: list[str], out_path: Path) -> int:
    snap = _run_scanner(symbols)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "captured_at": datetime.now(tz=UTC).isoformat(),
        "symbols": symbols,
        "snapshot": snap,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: golden baseline yazıldı → {out_path} ({len(snap['by_symbol'])} sembol)")
    return 0


def compare(baseline_path: Path) -> int:
    if not baseline_path.exists():
        print(f"HATA: baseline yok ({baseline_path}). Önce `capture` çalıştır.")
        return 2
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    symbols = baseline.get("symbols") or DEFAULT_SYMBOLS
    new_snap = _run_scanner(symbols)
    diffs = diff_snapshots(baseline.get("snapshot", {}), new_snap)
    if not diffs:
        print("✓ GEÇTI: golden ile birebir aynı — davranış değişmedi (salt performans).")
        return 0
    print(f"✗ FARK VAR ({len(diffs)}) — bu SALT performans DEĞİL, Level B strateji değişikliği:")
    for d in diffs:
        print("  -", d)
    return 1


def _selftest() -> int:
    """Offline unit test of the pure diff logic — no scanner run needed."""
    base = snapshot_from_results(
        [
            {
                "symbol": "AAPL",
                "composite_score": 70,
                "selection_eligible": True,
                "entry_ok": True,
                "conviction_tier": "A",
                "direction": True,
                "filter_score": 3,
            },
            {
                "symbol": "MSFT",
                "composite_score": 55,
                "selection_eligible": False,
                "entry_ok": False,
                "conviction_tier": "C",
                "direction": True,
                "filter_score": 2,
            },
        ]
    )
    # Identical → no diff
    assert diff_snapshots(base, base) == [], "aynı snapshot fark üretmemeli"
    # Score change → detected
    changed = snapshot_from_results(
        [
            {
                "symbol": "AAPL",
                "composite_score": 70,
                "selection_eligible": True,
                "entry_ok": True,
                "conviction_tier": "A",
                "direction": True,
                "filter_score": 3,
            },
            {
                "symbol": "MSFT",
                "composite_score": 80,
                "selection_eligible": True,
                "entry_ok": False,
                "conviction_tier": "C",
                "direction": True,
                "filter_score": 2,
            },
        ]
    )
    d = diff_snapshots(base, changed)
    assert any("MSFT.composite_score" in x for x in d), d
    assert any("MSFT.selection_eligible" in x for x in d), d
    assert any("Top-10" in x for x in d), d  # MSFT now outranks AAPL
    # Missing symbol → detected
    dropped = snapshot_from_results([{"symbol": "AAPL", "composite_score": 70}])
    assert any("Kaybolan" in x for x in diff_snapshots(base, dropped)), "kayıp sembol yakalanmalı"
    # top_n determinism (tie broken by symbol)
    tie = snapshot_from_results(
        [{"symbol": "ZZZ", "composite_score": 50}, {"symbol": "AAA", "composite_score": 50}]
    )
    assert tie["top_n"] == ["AAA", "ZZZ"], tie["top_n"]
    print("OK: golden diff mantığı (selftest) — 5/5 doğrulandı")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Golden scanner regression harness")
    parser.add_argument("mode", nargs="?", choices=["capture", "compare"], help="capture|compare")
    parser.add_argument(
        "--symbols", help="virgülle ayrılmış sembol listesi (varsayılan: sabit set)"
    )
    parser.add_argument("--path", default=str(_GOLDEN_PATH), help="baseline dosya yolu")
    parser.add_argument("--selftest", action="store_true", help="offline diff testini çalıştır")
    args = parser.parse_args(argv[1:])

    if args.selftest:
        return _selftest()
    symbols = (
        [s.strip().upper() for s in args.symbols.split(",")] if args.symbols else DEFAULT_SYMBOLS
    )
    path = Path(args.path)
    if args.mode == "capture":
        return capture(symbols, path)
    if args.mode == "compare":
        return compare(path)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
