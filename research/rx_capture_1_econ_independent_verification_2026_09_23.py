"""RX-CAPTURE-1-ECON INDEPENDENT RESULT VERIFICATION (Master Orchestrator v2 §30-32).

NOT a new research run. Verifies the locked B1 result using:
  same locked input (SHA-verified) + same locked protocol + DIFFERENT
  implementation path:
    - csv module + dict dedup (not pandas read_csv/groupby)
    - ordinal-day arithmetic for the T+1..T+5 boundary (not string compare)
    - statistics.median (not numpy)
    - cost grid applied to recomputed gross returns with the locked E1 rules
  No new hypothesis, threshold, metric, or cohort is introduced.

Locked under verification (prereg SHA 6b210259...):
  - E1 +3% / +5% first-touch gross return (entry = export price; T+1..T+5 high
    first-touch of entry*(1+target); else T+5 close)
  - cost grid C = {0.25..2.00}; NC_i(c)=G_i-c; M(c)=Median(NC_i(c))
  - breakeven = smallest c in C with M(c)<=0; else BETWEEN_GRID_POINTS
  - temporal: early 40% / late 40%; sign consistency at c in {0.55, 1.00}
  - verdicts: FURTHER_VALIDATION_SUPPORTED / NOT_SUPPORTED / INCONCLUSIVE

Output: data/backtest_out/rx_capture_1_econ_independent_verification_2026-09-23.json
Verdict vocabulary: VERIFICATION_PASS / VERIFICATION_MISMATCH /
VERIFICATION_INCONCLUSIVE. PASS != production approval. READ-ONLY. H4 UNTOUCHED.
"""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "backtest_out" / "full_universe_enriched_eod_only.csv"
CACHE = ROOT / "data" / "price_cache"
LOCKED = ROOT / "data" / "backtest_out" / "research_x_capture_1_econ_2026-09-23.json"
OUT = ROOT / "data" / "backtest_out" / "rx_capture_1_econ_independent_verification_2026-09-23.json"

EXPECTED_INPUT_SHA = "87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad"
EXPECTED_LOCKED_SHA = "04a43868e794ec871d41fea4389316c6f425a177184b8229a1332c2309467afd"
HORIZON = 5
COST_GRID = [0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00]
CANDS = {"E1_t3": 0.03, "E1_t5": 0.05}
TOL = 1e-6


def sha256_file(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def to_ord(s: str) -> int:
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d)).toordinal()


def load_rows():
    with open(DATA, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows = sorted(rows, key=lambda r: (r["scan_date"], r["symbol"]))
    best = {}
    for r in rows:
        best.setdefault((r["symbol"], r["scan_date"]), r)
    out = [r for r in best.values()
           if r["composite_score"] not in ("", "nan", "None")
           and r["c2c_5d"] not in ("", "nan", "None")]
    out.sort(key=lambda r: (r["scan_date"], r["symbol"]))
    return out


def load_bars(symbol: str):
    p = CACHE / f"{symbol}.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    return d if isinstance(d, list) else None


def gross_return(entry: float, bars, scan_ord: int, target: float):
    tgt = entry * (1 + target)
    fwd = [b for b in bars if isinstance(b, dict) and isinstance(b.get("date"), str)
           and to_ord(b["date"]) > scan_ord]
    fwd.sort(key=lambda b: to_ord(b["date"]))
    fwd = fwd[:HORIZON]
    if len(fwd) < HORIZON:
        return None
    for b in fwd:
        if float(b["high"]) >= tgt:
            return target * 100.0
    return (float(fwd[-1]["close"]) - entry) / entry * 100.0


def breakeven(med_by_cost: dict) -> str:
    for c in COST_GRID:
        if med_by_cost.get(c) is not None and med_by_cost[c] <= 0:
            return f"{c:.2f}"
    return "BETWEEN_GRID_POINTS"


def main() -> None:
    res = {
        "locked_json_sha256_actual": sha256_file(LOCKED),
        "locked_json_sha_matches": sha256_file(LOCKED) == EXPECTED_LOCKED_SHA,
        "input_sha_ok": sha256_file(DATA) == EXPECTED_INPUT_SHA,
        "implementation_path": "csv+dict-dedup+ordinal-days+statistics.median",
    }
    locked = json.loads(LOCKED.read_text(encoding="utf-8"))
    rows = load_rows()
    all_dates = sorted({r["scan_date"] for r in rows})
    n_d = len(all_dates)
    early = set(all_dates[: int(n_d * 0.4)])
    late = set(all_dates[int(n_d * 0.6):])

    bars_memo: dict[str, list | None] = {}
    failures = []
    per_cand = {}
    for name, target in CANDS.items():
        gross = []  # (scan_date_str, gross)
        for r in rows:
            try:
                entry = float(r["price"])
            except Exception:
                continue
            if not entry or entry <= 0:
                continue
            sym = r["symbol"]
            if sym not in bars_memo:
                bars_memo[sym] = load_bars(sym)
            bars = bars_memo[sym]
            if bars is None:
                continue
            gr = gross_return(entry, bars, to_ord(r["scan_date"]), target)
            if gr is None:
                continue
            gross.append((r["scan_date"], gr))
        g = [x[1] for x in gross]
        med_by_cost = {c: (statistics.median([v - c for v in g]) if g else None) for c in COST_GRID}
        be = breakeven(med_by_cost)
        m100 = med_by_cost[1.00]
        e = [v - 0.55 for d, v in gross if d in early]
        l = [v - 0.55 for d, v in gross if d in late]
        e100 = [v - 1.00 for d, v in gross if d in early]
        l100 = [v - 1.00 for d, v in gross if d in late]
        e55m = statistics.median(e) if e else None
        l55m = statistics.median(l) if l else None
        e100m = statistics.median(e100) if e100 else None
        l100m = statistics.median(l100) if l100 else None
        sign_consistent = (
            e55m is not None and l55m is not None and e100m is not None and l100m is not None
            and (e55m > 0) == (l55m > 0) and (e100m > 0) == (l100m > 0))

        lv = locked["candidates"][name]
        def cmp(key, got, locked_val, tol=TOL):
            if locked_val is None or got is None:
                if got != locked_val:
                    failures.append(f"{name}.{key}: got={got} locked={locked_val}")
                return
            if abs(got - locked_val) > tol:
                failures.append(f"{name}.{key}: got={got} locked={locked_val} tol={tol}")

        cmp("evaluated", len(g), lv["evaluated"], 0)
        cmp("median_net@1.00", m100, lv["median_net_by_cost"]["1.00"])
        cmp("mean_net@0.55", (statistics.fmean([v - 0.55 for v in g]) if g else None), lv["mean_net_0.55"], 1e-4)
        if be != lv["breakeven_cost"]:
            failures.append(f"{name}.breakeven: got={be} locked={lv['breakeven_cost']}")
        if sign_consistent != lv["temporal_sign_consistent"]:
            failures.append(f"{name}.temporal_sign_consistent: got={sign_consistent} locked={lv['temporal_sign_consistent']}")
        cmp("early_median_0.55", e55m, lv["temporal"]["early_median_0.55"], 1e-4)
        cmp("late_median_0.55", l55m, lv["temporal"]["late_median_0.55"], 1e-4)

        per_cand[name] = {
            "evaluated": len(g),
            "median_net@1.00": round(m100, 6) if m100 is not None else None,
            "breakeven_cost": be,
            "temporal_sign_consistent": sign_consistent,
            "mean_net@0.55": round(statistics.fmean([v - 0.55 for v in g]), 6) if g else None,
            "locked_verdict": locked["verdicts"][name],
        }

    res["candidates"] = per_cand
    res["failures"] = failures
    res["verification"] = "VERIFICATION_PASS" if not failures else "VERIFICATION_MISMATCH"
    res["note"] = ("VERIFICATION_PASS != production approval. Only answers whether the "
                   "locked B1 result was computed correctly.")
    res["production_impact"] = "NONE"
    OUT.write_text(json.dumps(res, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"verification": res["verification"], "input_sha_ok": res["input_sha_ok"],
                      "locked_sha_matches": res["locked_json_sha_matches"],
                      "failures": len(failures), "first": failures[:8]}, indent=2))


if __name__ == "__main__":
    main()
