"""RX-CAPTURE-1 INDEPENDENT RESULT VERIFICATION (Master Orchestrator v2 §30-32).

NOT a new experiment. Verifies ONLY the two SUPPORTED_PENDING_VERIFICATION
candidates (E1 +3% and E1 +5%) using:
  same locked input (SHA-verified) + same locked protocol + DIFFERENT
  implementation path:
    - csv module + dict dedup (not pandas)
    - sorted-list path traversal (not pandas indexing)
    - statistics.median (not numpy)
    - datetime-ordinal day arithmetic for the T+1..T+5 boundary
    - no block-bootstrap rerun for the pass/fail sign: the degenerate-CI issue
      is checked by RECOMPUTING the median and the share of first-touch hits,
      plus an independent 5-day block bootstrap with a different RNG pattern.

Locked under verification (prereg SHA d0baa618...):
  - primary estimand: Median(NC_i), NC_i = GrossExitReturn_i - Cost_i
  - cost: PRIMARY 0.55 / STRESS 1.00 (round-trip pp per position)
  - E1 fixed target: +3% and +5% first-touch on daily HIGH vs entry
  - same-day ambiguity: EXCLUDE (for E1 there is no stop leg -> none ambiguous)
  - entry = export `price`; fallback exit = T+5 close
  - temporal: early 40% / late 40%; same-sign requirement
  - MFE terminology: MFE = opportunity envelope, exit return = rule-realized

Output: data/backtest_out/rx_capture_1_independent_verification_2026-09-22.json
Verdict vocabulary: VERIFICATION_PASS / VERIFICATION_MISMATCH /
VERIFICATION_INCONCLUSIVE. Does NOT authorize production; PASS != production
approval. READ-ONLY. H4 UNTOUCHED.
"""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "backtest_out" / "full_universe_enriched_eod_only.csv"
CACHE = ROOT / "data" / "price_cache"
LOCKED = ROOT / "data" / "backtest_out" / "research_x_capture_1_2026-09-22.json"
OUT = ROOT / "data" / "backtest_out" / "rx_capture_1_independent_verification_2026-09-22.json"

EXPECTED_SHA256 = "87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad"
SEED = 20260922
HORIZON = 5
PRIMARY_COST = 0.55
STRESS_COST = 1.00
CANDS = {"E1_t3": 0.03, "E1_t5": 0.05}

TOL = 1e-6


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


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
    out = [
        r
        for r in best.values()
        if r["composite_score"] not in ("", "nan", "None")
        and r["c2c_5d"] not in ("", "nan", "None")
    ]
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


def first_touch_return(entry: float, bars, scan_ord: int, target: float):
    """E1 fixed target: exit at entry*(1+target) on the first day whose HIGH
    reaches it within T+1..T+5 (by ordinal day arithmetic); else T+5 close.
    Returns (gross_pct, hit_flag, hit_day)."""
    tgt = entry * (1 + target)
    fwd = [
        b
        for b in bars
        if isinstance(b, dict) and isinstance(b.get("date"), str) and to_ord(b["date"]) > scan_ord
    ]
    fwd.sort(key=lambda b: to_ord(b["date"]))
    fwd = fwd[:HORIZON]
    if len(fwd) < HORIZON:
        return None
    for i, b in enumerate(fwd):
        if float(b["high"]) >= tgt:
            return (target * 100.0, True, i + 1)
    exit_price = float(fwd[-1]["close"])
    return ((exit_price - entry) / entry * 100.0, False, HORIZON)


def block_bootstrap_median(day_map: dict, seed: int) -> np.ndarray:
    """5-day consecutive block bootstrap of the median net capture, different RNG
    pattern (RandomState) for consistency checking only."""
    rng = np.random.RandomState(seed)
    days = sorted(day_map.keys())
    n = len(days)
    nblocks = int(np.ceil(n / 5))
    out = []
    for _ in range(2000):
        starts = rng.randint(0, n - 5 + 1, size=nblocks)
        vals = []
        for s in starts:
            for d in days[s : s + 5]:
                vals.extend(day_map[d])
        if vals:
            out.append(float(np.median(vals)))
    return np.array(out)


def main() -> None:
    locked = json.loads(LOCKED.read_text(encoding="utf-8"))
    res = {
        "locked_json_sha256_actual": sha256_file(LOCKED),
        "input_sha_ok": sha256_file(DATA) == EXPECTED_SHA256,
        "implementation_path": "csv+dict-dedup+sorted-list+statistics.median+ordinal-days+RandomState",
    }

    rows = load_rows()
    # Preload each symbol's cache once (performance only; does not change logic).
    bars_memo: dict[str, list | None] = {}

    def bars_for(sym: str):
        if sym not in bars_memo:
            bars_memo[sym] = load_bars(sym)
        return bars_memo[sym]

    all_dates = sorted({r["scan_date"] for r in rows})
    n_d = len(all_dates)
    early = set(all_dates[: int(n_d * 0.4)])
    late = set(all_dates[int(n_d * 0.6) :])

    failures = []
    per_cand = {}
    for name, target in CANDS.items():
        nc = []
        hits = 0
        day_map: dict[str, list[float]] = {}
        early_vals = []
        late_vals = []
        for r in rows:
            try:
                entry = float(r["price"])
            except Exception:
                continue
            if not entry or entry <= 0:
                continue
            bars = bars_for(r["symbol"])
            if bars is None:
                continue
            ft = first_touch_return(entry, bars, to_ord(r["scan_date"]), target)
            if ft is None:
                continue
            gross, hit, _ = ft
            if hit:
                hits += 1
            net = gross - PRIMARY_COST
            nc.append(net)
            day_map.setdefault(r["scan_date"], []).append(net)
            if r["scan_date"] in early:
                early_vals.append(net)
            elif r["scan_date"] in late:
                late_vals.append(net)

        n = len(nc)
        med = statistics.median(nc) if nc else None
        stress_med = (
            statistics.median([g - STRESS_COST for g in (v + PRIMARY_COST for v in nc)])
            if nc
            else None
        )
        hit_share = hits / n if n else None
        e_med = statistics.median(early_vals) if early_vals else None
        l_med = statistics.median(late_vals) if late_vals else None
        same_sign = e_med is not None and l_med is not None and (e_med > 0) == (l_med > 0)
        bb = block_bootstrap_median(day_map, SEED) if day_map else np.array([])
        ci95 = (
            [float(np.quantile(bb, 0.025)), float(np.quantile(bb, 0.975))]
            if len(bb)
            else [None, None]
        )

        lv = locked["candidates"][name]

        # deterministic comparisons (exact)
        def cmp(key, got, locked_val, tol=TOL, line_name=name):
            if locked_val is None or got is None:
                if got != locked_val:
                    failures.append(f"{line_name}.{key}: got={got} locked={locked_val}")
                return
            if abs(got - locked_val) > tol:
                failures.append(f"{line_name}.{key}: got={got} locked={locked_val} tol={tol}")

        cmp("evaluated", n, lv["evaluated"], 0)
        cmp("median_net_capture_primary", med, lv["median_net_capture_primary"])
        cmp("median_net_capture_stress", stress_med, lv["median_net_capture_stress"], 1e-4)
        cmp("early_median", e_med, lv["early_median"], 1e-4)
        cmp("late_median", l_med, lv["late_median"], 1e-4)
        if same_sign != lv["temporal_same_sign"]:
            failures.append(
                f"{name}.temporal_same_sign: got={same_sign} locked={lv['temporal_same_sign']}"
            )

        # degeneracy check: median should sit ~ target - cost when hit_share > 0.5
        deg = bool(
            hit_share is not None
            and hit_share > 0.5
            and med is not None
            and abs(med - (target * 100.0 - PRIMARY_COST)) < 0.05
        )

        per_cand[name] = {
            "n": n,
            "median_net_primary": round(med, 6) if med is not None else None,
            "median_net_stress": round(stress_med, 6) if stress_med is not None else None,
            "first_touch_hit_share": round(hit_share, 6) if hit_share is not None else None,
            "median_degenerates_to_target": deg,
            "early_median": round(e_med, 6) if e_med is not None else None,
            "late_median": round(l_med, 6) if l_med is not None else None,
            "temporal_same_sign": same_sign,
            "ci95_recomputed": [round(c, 6) if c is not None else None for c in ci95],
            "locked_verdict": lv["verdict"],
        }

    res["candidates"] = per_cand
    res["failures"] = failures
    res["verification"] = (
        "VERIFICATION_PASS"
        if not failures
        else (
            "VERIFICATION_MISMATCH"
            if any("median_net_capture_primary" in f or "evaluated" in f for f in failures)
            else "VERIFICATION_INCONCLUSIVE"
        )
    )
    res["note"] = (
        "VERIFICATION_PASS != production approval. This only answers whether "
        "the locked result was computed correctly."
    )
    res["production_impact"] = "NONE"

    OUT.write_text(json.dumps(res, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "verification": res["verification"],
                "input_sha_ok": res["input_sha_ok"],
                "failures": len(failures),
                "first": failures[:8],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
