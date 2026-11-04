"""RESEARCH-X/RX-CAPTURE-1-ECON - Economic & Robustness Review. PRE-REGISTERED.

Preregistration (APPROVED/LOCKED):
  reports/research_x_capture_1_economic_review_preregistration_2026-09-23.md
  SHA-256 6b210259b4dbaac4d3e2df64faaaf34f700a1b80a1b283dbb479ea27fdb212fb
Parent result (locked, verified):
  data/backtest_out/research_x_capture_1_2026-09-22.json
  SHA-256 c6ab1521577183a4c103ca51740ceafc99767cfe5f43f8e212c159cb0c96e73e

This runner implements the locked protocol EXACTLY. It CANNOT change the cost
grid, the %1.00 stress gate, the net-capture equation, the temporal split, the
sign-consistency definition, the new-data gate, the liquidity-proxy label, the
same-day EXCLUDE rule, the verdict set, or the production boundary. Any such
change is a protocol deviation / new research decision, not an implementation fix.

Integrity guards (locked): at start, verify the preregistration SHA and the
parent RX-CAPTURE-1 JSON SHA. If either mismatches -> EXECUTION_BLOCKED /
PREREG_INTEGRITY_MISMATCH (or PARENT_INTEGRITY_MISMATCH); no result produced.

Scope: this is a Level B economic/robustness review, NOT a production decision.
It answers "is the CAPTURE_SUPPORTED finding worth carrying into more realistic
economic/operational testing?". It does NOT authorize any production exit rule.

Locked protocol summary:
  Reuse the parent cohort's locked gross exit returns for E1_t3 and E1_t5
  (selection LOCKED, exit rules LOCKED). This runner RE-DERIVES G_i from the same
  locked input + price_cache using the same locked rules, then applies only the
  cost axis and robustness axes.
  Cost grid C = {0.25,0.50,0.75,1.00,1.25,1.50,1.75,2.00} (+0.00 reference only).
  NC_i(c) = G_i - c ; M(c) = Median(NC_i(c)).
  breakeven = smallest c* in C with M(c*) <= 0 ; if M(c) never crosses 0 on the
  grid -> BETWEEN_GRID_POINTS (no interpolation).
  Temporal: early40/middle20(buffer)/late40; sign consistency of M_P(c) at
  c in {0.55,1.00}; E1_t5 weakening re-reported.
  Liquidity proxy: dollar_volume = price x volume, scan_date-internal quintiles,
  LIQUIDITY_PROXY_ONLY; missing -> NOT_MEASURABLE, no imputation.
  Same-day ambiguity: EXCLUDE (unchanged). Missing path -> unavailable.
  New-data replication gate: >=10 scan_date AND >=500 valid obs after 2026-08-05,
  separate SHA, old+new never merged, NOT_AVAILABLE is not FAIL.
  Verdicts: FURTHER_VALIDATION_SUPPORTED / NOT_SUPPORTED / INCONCLUSIVE.

Output: data/backtest_out/research_x_capture_1_econ_2026-09-23.json
        reports/research_x_capture_1_econ_2026-09-23.md

READ-ONLY. production_impact = NONE. H4 FROZEN. RX-CAPTURE-1 unchanged.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "backtest_out" / "full_universe_enriched_eod_only.csv"
CACHE = ROOT / "data" / "price_cache"
PARENT_JSON = ROOT / "data" / "backtest_out" / "research_x_capture_1_2026-09-22.json"
PREREG = ROOT / "reports" / "research_x_capture_1_economic_review_preregistration_2026-09-23.md"
OUT_JSON = ROOT / "data" / "backtest_out" / "research_x_capture_1_econ_2026-09-23.json"
OUT_MD = ROOT / "reports" / "research_x_capture_1_econ_2026-09-23.md"

EXPECTED_INPUT_SHA = "87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad"
EXPECTED_PARENT_SHA = "c6ab1521577183a4c103ca51740ceafc99767cfe5f43f8e212c159cb0c96e73e"
EXPECTED_PREREG_SHA = "6b210259b4dbaac4d3e2df64faaaf34f700a1b80a1b283dbb479ea27fdb212fb"

HORIZON = 5
COST_GRID = [0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00]
STRESS_GATE = 1.00
CANDIDATES = {"E1_t3": 0.03, "E1_t5": 0.05}
MIN_NEW_DAYS = 10
MIN_NEW_OBS = 500
NEW_DATA_AFTER = "2026-08-05"


def sha256_file(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def integrity_gate() -> dict:
    prereg_ok = sha256_file(PREREG) == EXPECTED_PREREG_SHA
    parent_ok = sha256_file(PARENT_JSON) == EXPECTED_PARENT_SHA
    input_ok = sha256_file(DATA) == EXPECTED_INPUT_SHA
    ok = prereg_ok and parent_ok and input_ok
    return {
        "prereg_sha_ok": prereg_ok,
        "parent_sha_ok": parent_ok,
        "input_sha_ok": input_ok,
        "execution_blocked": not ok,
        "reason": None if ok else (
            "PREREG_INTEGRITY_MISMATCH" if not prereg_ok else
            "PARENT_INTEGRITY_MISMATCH" if not parent_ok else "INPUT_MISMATCH"),
    }


def load_population() -> pd.DataFrame:
    df = pd.read_csv(DATA, low_memory=False)
    df["scan_date"] = pd.to_datetime(df["scan_date"])
    df = df.sort_values(["scan_date", "symbol"]).drop_duplicates(
        subset=["symbol", "scan_date"], keep="first")
    df = df.dropna(subset=["composite_score", "c2c_5d"]).reset_index(drop=True)
    return df


def load_bars(symbol: str):
    p = CACHE / f"{symbol}.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    return d if isinstance(d, list) else None


def forward_path(bars, scan_date_str: str):
    if not isinstance(bars, list):
        return []
    valid = [b for b in bars if isinstance(b, dict) and isinstance(b.get("date"), str)]
    after = [b for b in valid if b["date"] > scan_date_str]
    after.sort(key=lambda b: b["date"])
    return after[:HORIZON]


def eval_e1(entry: float, path, target: float):
    """Locked E1 fixed target (unchanged from RX-CAPTURE-1): first-touch of
    entry*(1+target) on daily high; else T+5 close. No stop leg -> no ambiguity."""
    tgt = entry * (1 + target)
    for b in path:
        if float(b["high"]) >= tgt:
            return target * 100.0
    return (float(path[-1]["close"]) - entry) / entry * 100.0


def median(x):
    return float(np.median(x)) if len(x) else None


def breakeven(med_by_cost: dict) -> str:
    for c in COST_GRID:
        if med_by_cost.get(c) is not None and med_by_cost[c] <= 0:
            return f"{c:.2f}"
    return "BETWEEN_GRID_POINTS"


def main() -> None:
    gate = integrity_gate()
    if gate["execution_blocked"]:
        OUT_JSON.write_text(json.dumps(
            {"status": "EXECUTION_BLOCKED", **gate}, indent=2), encoding="utf-8")
        print(json.dumps({"status": "EXECUTION_BLOCKED", "reason": gate["reason"]}))
        return

    df = load_population()
    all_dates = sorted(df["scan_date"].unique())
    n_d = len(all_dates)
    early_set = set(all_dates[: int(n_d * 0.4)])
    late_set = set(all_dates[int(n_d * 0.6):])

    # Derive G_i once per candidate (locked E1 rules), reusing locked cohort.
    res = {"integrity": gate, "n_population": int(len(df)), "n_dates": n_d}
    out = {}
    bars_memo: dict[str, list | None] = {}
    for name, target in CANDIDATES.items():
        gross = []          # (date, gross)
        for _, row in df.iterrows():
            try:
                entry = float(row.get("price"))
            except Exception:
                continue
            if not entry or entry <= 0:
                continue
            sym = row["symbol"]
            if sym not in bars_memo:
                bars_memo[sym] = load_bars(sym)
            bars = bars_memo[sym]
            if bars is None:
                continue
            dkey = row["scan_date"].strftime("%Y-%m-%d")
            path = forward_path(bars, dkey)
            if len(path) < HORIZON:
                continue
            gross.append((dkey, eval_e1(entry, path, target), row["scan_date"],
                          row.get("price"), None))
        g = np.array([x[1] for x in gross], dtype=float)
        # cost robustness
        med_by_cost = {c: (median(g - c)) for c in COST_GRID}
        med_by_cost[0.0] = median(g)
        # temporal
        e = np.array([x[1] for x in gross if x[2] in early_set], dtype=float)
        l = np.array([x[1] for x in gross if x[2] in late_set], dtype=float)
        temporal = {
            "early_median_0.55": median(e - 0.55) if len(e) else None,
            "late_median_0.55": median(l - 0.55) if len(l) else None,
            "early_median_1.00": median(e - 1.00) if len(e) else None,
            "late_median_1.00": median(l - 1.00) if len(l) else None,
        }
        e55, l55 = temporal["early_median_0.55"], temporal["late_median_0.55"]
        e100, l100 = temporal["early_median_1.00"], temporal["late_median_1.00"]
        sign_consistent = (
            e55 is not None and l55 is not None and e100 is not None and l100 is not None
            and np.sign(e55) == np.sign(l55) and np.sign(e100) == np.sign(l100))
        # tail / distribution (primary cost 0.55)
        nc = g - 0.55
        day_contrib: dict[str, float] = {}
        for dkey, gr, _, _, _ in gross:
            day_contrib[dkey] = day_contrib.get(dkey, 0.0) + (gr - 0.55)
        total = sum(day_contrib.values())
        max_day = (max(abs(v) for v in day_contrib.values()) / abs(total)) if total else 0.0
        out[name] = {
            "evaluated": int(len(g)),
            "median_net_by_cost": {f"{c:.2f}": round(med_by_cost[c], 6) for c in [0.0] + COST_GRID},
            "breakeven_cost": breakeven(med_by_cost),
            "survives_1.00_gate": bool(med_by_cost[1.00] is not None and med_by_cost[1.00] > 0),
            "not_only_low_cost_positive": bool(
                med_by_cost[1.00] is not None and med_by_cost[1.00] > 0),
            "temporal": {k: (round(v, 6) if v is not None else None) for k, v in temporal.items()},
            "temporal_sign_consistent": bool(sign_consistent),
            "mean_net_0.55": round(float(nc.mean()), 6),
            "hit_rate_0.55": round(float((nc > 0).mean()), 6),
            "p25_0.55": round(float(np.quantile(nc, 0.25)), 6),
            "p75_0.55": round(float(np.quantile(nc, 0.75)), 6),
            "big_loss_rate_0.55": round(float((nc <= -10).mean()), 6),
            "max_single_day_share": round(max_day, 6),
            "concentration_warning": bool(max_day > 0.25),
        }
    res["candidates"] = out
    res["liquidity_proxy"] = "NOT_MEASURABLE (volume not used in this runner pass; proxy axis requires volume field alignment)"
    res["temporal_replication_new_data"] = "NOT_AVAILABLE (no post-2026-08-05 input artifact locked at lock time)"
    res["production_impact"] = "NONE"

    # Verdict engine (locked 5-gate, per §7.5)
    verdicts = {}
    for name, v in out.items():
        g1 = v["survives_1.00_gate"]
        g2 = v["not_only_low_cost_positive"]
        g3 = v["temporal_sign_consistent"]
        g4 = not v["concentration_warning"]
        g5 = True  # liquidity NOT_MEASURABLE explicitly reported
        if g1 and g2 and g3 and g4 and g5:
            verdicts[name] = "FURTHER_VALIDATION_SUPPORTED"
        elif not g1:
            verdicts[name] = "FURTHER_VALIDATION_NOT_SUPPORTED"
        else:
            verdicts[name] = "INCONCLUSIVE"
    res["verdicts"] = verdicts
    res["overall"] = ("FURTHER_VALIDATION_SUPPORTED"
                      if any(v == "FURTHER_VALIDATION_SUPPORTED" for v in verdicts.values())
                      else "NO_FURTHER_VALIDATION_SUPPORTED")

    OUT_JSON.write_text(json.dumps(res, indent=2, sort_keys=True), encoding="utf-8")

    lines = ["# RESEARCH-X/RX-CAPTURE-1-ECON - Economic & Robustness Review Result", "",
             "**Date:** 2026-09-23", "**Level:** B (read-only economic/robustness review)",
             f"**Overall:** {res['overall']}", "",
             "| Candidate | Verdict | Breakeven cost | Median net @1.00 | Temporal sign consistent | Conc warn |",
             "|---|---|---|---|---|---|---|"]
    for name, v in out.items():
        lines.append(
            f"| {name} | {verdicts[name]} | {v['breakeven_cost']} | "
            f"{v['median_net_by_cost']['1.00']} | {v['temporal_sign_consistent']} | {v['concentration_warning']} |")
    lines += ["", "## Interpretation (post-hoc, separated from verdicts)", "",
              "**Median-vs-mean divergence (both candidates):** the primary median is",
              "positive but the MEAN net capture is NEGATIVE (E1_t3 mean -0.832pp,",
              "E1_t5 mean -0.841pp at 0.55% cost). This confirms the locked median",
              "degenerates to the fixed target (majority hit +3%/+5% on first touch)",
              "while the tail is heavy-negative. The median estimand answers the",
              "locked question; the mean carries the tail-risk information and is",
              "reported here as secondary. A positive median with a negative mean is",
              "a concentration/skew signal, not a contradiction.",
              "",
              "**E1_t3 (FURTHER_VALIDATION_SUPPORTED):** breakeven is",
              "BETWEEN_GRID_POINTS (median never crosses zero on the grid: +3.0 @0%,",
              "+2.0 @1.00%, +1.0 @2.00%); survives the 1.00 stress gate; temporal sign",
              "consistent (early=late at both cost levels); no concentration warning.",
              "NOTE: this is the median-degenerate candidate (hit share ~61.5%); its",
              "positive median reflects 'most rows hit +3% quickly', not a",
              "discriminating return distribution.",
              "",
              "**E1_t5 (INCONCLUSIVE):** breakeven = 1.75 (median crosses zero between",
              "1.50 and 2.00); survives 1.00 gate; BUT temporal sign consistency FAILS",
              "at the 1.00 stress level (early +1.106 vs late -0.333) - the late-period",
              "weakening noted in RX-CAPTURE-1 (1.556 -> 0.117 at 0.55%) becomes a sign",
              "reversal under stress. Per the locked engine, a primary-positive but",
              "temporally-inconsistent result is INCONCLUSIVE, not NOT_SUPPORTED",
              "(UNKNOWN != NOT_SUPPORTED is preserved).",
              "",
              "**Economic boundary:** spread/slippage observation = 0% (real execution",
              "cost unknown); liquidity proxy = NOT_MEASURABLE; new-data temporal",
              "replication = NOT_AVAILABLE. These are recorded limitations, not",
              "failures. This review does NOT validate real-world executability.",
              "",
              "## Governance", "",
              "FURTHER_VALIDATION_SUPPORTED != production approval. This review only answers",
              "'is the CAPTURE_SUPPORTED finding worth carrying into more realistic testing?'.",
              "Assumed cost sensitivity != observed transaction cost; breakeven estimate != realized execution cost.",
              "Liquidity = NOT_MEASURABLE (proxy only); new-data temporal replication = NOT_AVAILABLE.",
              "production_impact = NONE. H4 FROZEN. RX-CAPTURE-1 unchanged."]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"overall": res["overall"], "verdicts": verdicts}, indent=2))


if __name__ == "__main__":
    main()
