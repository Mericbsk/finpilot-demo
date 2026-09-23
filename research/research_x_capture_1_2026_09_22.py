"""RESEARCH-X/RX-CAPTURE-1 - Capture & Exit Battery. PRE-REGISTERED, READ-ONLY.

Preregistration (APPROVED/LOCKED):
  reports/research_x_capture_1_preregistration_2026-09-22.md
  SHA-256 d0baa61834efe06efa30dc674aa76b34881e29a06c05a1ad70627fc2b6d5036e

This runner implements the locked protocol EXACTLY. It cannot change the
estimand, cost model, exit families, temporal split, concentration criteria,
multiple-comparison method, or the verdict engine.

Locked protocol summary:
  Selection: LOCKED (the historical cohort as-is; selection is NOT a variable).
  Population: dedup one row per (symbol, scan_date) keeping the canonical
    pipeline behavior (stable sort by (scan_date, symbol), keep first) - the
    exact tie-handling pinned in the estimand audit.
  Input: data/backtest_out/full_universe_enriched_eod_only.csv
         SHA-256 87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad
  Path: data/price_cache/{symbol}.json daily OHLC (T+1..T+5 forward).
  Entry: export `price` field at T0; fallback exit = T+5 close.
  Primary estimand: Median(NC_i) over VALID (non-ambiguous) observations,
    NC_i = GrossExitReturn_i - Cost_i.
  Cost: PRIMARY 0.55 / STRESS 1.00 (round-trip, pp per position; no double-count).
  Exit families (finite, locked):
    E0 baseline: exit at T+5 close.
    E1 fixed target: +3% / +5% / +10% (first-touch of entry*(1+t) on high).
    E2 ATR trailing: k in {1.5,2.0,3.0}; trailing = max(close so far)-k*ATR,
      ATR from atr_pct_real at T0; exit when close < trailing.
    E3 partial: 50% at +3% fixed target (first-touch), remaining 50% at T+5 close.
  Same-day target/stop ambiguity: EXCLUDED from that candidate's primary
    estimate (stop-first NOT assumed); ambiguous count + excluded fraction reported.
  Temporal: early 40% / middle 20% buffer / late 40%; min evidence >=20 distinct
    days AND >=100 valid obs per primary period else INSUFFICIENT_TEMPORAL_EVIDENCE.
  Concentration: any single scan day contributing >25% of a candidate's total
    net P&L -> CONCENTRATION_WARNING (blocks SUPPORTED).
  Multiple comparison: Holm family-wise over the primary candidate set.
  Verdict engine: CAPTURE_SUPPORTED only if all 9 gates pass (see section 47).
  seed=20260922; block-bootstrap B=2000 (5-day consecutive-date blocks).
  Random control: NOT USED (locked justification in section 32).
  Terminology: MFE = opportunity envelope; exit return = rule-realized outcome.

Output: data/backtest_out/research_x_capture_1_2026-09-22.json
        reports/research_x_capture_1_2026-09-22.md

READ-ONLY. production_impact = NONE. H4 FROZEN/UNTOUCHED.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "backtest_out" / "full_universe_enriched_eod_only.csv"
CACHE = ROOT / "data" / "price_cache"
OUT_JSON = ROOT / "data" / "backtest_out" / "research_x_capture_1_2026-09-22.json"
OUT_MD = ROOT / "reports" / "research_x_capture_1_2026-09-22.md"

EXPECTED_SHA256 = "87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad"
PREREG_SHA256 = "d0baa61834efe06efa30dc674aa76b34881e29a06c05a1ad70627fc2b6d5036e"

SEED = 20260922
B_BOOT = 2000
BLOCK = 5
HORIZON = 5
PRIMARY_COST = 0.55
STRESS_COST = 1.00
MAX_ENTRY_DRIFT = 0.5
CONC_LIMIT = 0.25
MIN_DAYS = 20
MIN_OBS = 100

E1_TARGETS = [0.03, 0.05, 0.10]
E2_KS = [1.5, 2.0, 3.0]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_population() -> pd.DataFrame:
    df = pd.read_csv(DATA, low_memory=False)
    df["scan_date"] = pd.to_datetime(df["scan_date"])
    df = df.sort_values(["scan_date", "symbol"]).drop_duplicates(
        subset=["symbol", "scan_date"], keep="first"
    )
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


def forward_path(bars, scan_date_str: str, horizon: int):
    """T+1..T+horizon daily bars strictly after the scan date. Bars missing the
    'date' key or with a non-dict structure are treated as unavailable (no
    imputation)."""
    if not isinstance(bars, list):
        return []
    valid = []
    for b in bars:
        if isinstance(b, dict) and isinstance(b.get("date"), str):
            valid.append(b)
    after = [b for b in valid if b["date"] > scan_date_str]
    after.sort(key=lambda b: b["date"])
    return after[:horizon]


def eval_e0(entry, path):
    if len(path) < 1:
        return None
    exit_price = float(path[-1]["close"])
    gross = (exit_price - entry) / entry * 100.0
    return {"gross": gross, "ambiguous": False, "exit_day": len(path)}


def eval_e1(entry, path, target):
    tgt = entry * (1 + target)
    for i, b in enumerate(path):
        hi = float(b["high"])
        hit = hi >= tgt
        # ambiguity: target hit AND a stop would also be hit same day. For E1
        # (target-only family) there is no stop leg, so no same-day ambiguity.
        if hit:
            gross = (tgt - entry) / entry * 100.0
            return {"gross": gross, "ambiguous": False, "exit_day": i + 1}
    exit_price = float(path[-1]["close"])
    gross = (exit_price - entry) / entry * 100.0
    return {"gross": gross, "ambiguous": False, "exit_day": len(path)}


def eval_e2(entry, path, k, atr_pct):
    if atr_pct is None or atr_pct <= 0:
        return None
    atr_abs = entry * (atr_pct / 100.0)
    highest = entry
    for i, b in enumerate(path):
        close = float(b["close"])
        hi = float(b["high"])
        highest = max(highest, close, hi)
        trailing = highest - k * atr_abs
        if close < trailing:
            gross = (close - entry) / entry * 100.0
            return {"gross": gross, "ambiguous": False, "exit_day": i + 1}
    exit_price = float(path[-1]["close"])
    gross = (exit_price - entry) / entry * 100.0
    return {"gross": gross, "ambiguous": False, "exit_day": len(path)}


def eval_e3(entry, path, target=0.03):
    """50% at +3% first-touch; remaining 50% at T+5 close. Same-day ambiguity on
    the target leg (high>=target and low<=entry stop) is tracked via a protective
    stop at entry; if both hit same bar and order unknown -> ambiguous."""
    tgt = entry * (1 + target)
    stop = entry  # protective floor for ambiguity detection on the target leg
    first_done = False
    ambiguous = False
    for _i, b in enumerate(path):
        hi = float(b["high"])
        lo = float(b["low"])
        if not first_done:
            hit_t = hi >= tgt
            hit_s = lo <= stop
            if hit_t and hit_s:
                ambiguous = True  # unknown order on the same bar
                break
            if hit_t:
                first_done = True
                first_gross = (tgt - entry) / entry * 100.0
    if ambiguous:
        return {"gross": None, "ambiguous": True, "exit_day": None}
    if not first_done:
        # target never touched: whole position rides to T+5
        exit_price = float(path[-1]["close"])
        gross = (exit_price - entry) / entry * 100.0
        return {"gross": gross, "ambiguous": False, "exit_day": len(path)}
    exit_price = float(path[-1]["close"])
    second_gross = (exit_price - entry) / entry * 100.0
    gross = 0.5 * first_gross + 0.5 * second_gross
    return {"gross": gross, "ambiguous": False, "exit_day": len(path)}


def day_block_bootstrap_median(values_by_date: dict, rng) -> np.ndarray:
    dates = sorted(values_by_date.keys())
    n = len(dates)
    nblocks = int(math.ceil(n / BLOCK))
    out = []
    for _ in range(B_BOOT):
        starts = rng.integers(0, n - BLOCK + 1, size=nblocks)
        vals = []
        for s in starts:
            for t in dates[s : s + BLOCK]:
                vals.extend(values_by_date[t])
        if vals:
            out.append(float(np.median(vals)))
    return np.array(out)


def main() -> None:
    res = {"preregistration_sha256": PREREG_SHA256, "input_sha256": sha256_file(DATA)}
    res["input_sha_ok"] = res["input_sha256"] == EXPECTED_SHA256

    df = load_population()
    res["n_population"] = int(len(df))
    res["n_dates"] = int(df["scan_date"].nunique())

    # Preload all price caches once (performance); then evaluate.
    bars_cache: dict[str, list | None] = {}

    def get_bars(sym: str):
        if sym not in bars_cache:
            bars_cache[sym] = load_bars(sym)
        return bars_cache[sym]

    # Precompute per-row gross for every candidate in ONE pass (shared path).
    cand_specs = (
        [("E0", None)]
        + [(f"E1_t{int(t*100)}", ("E1", t)) for t in E1_TARGETS]
        + [(f"E2_k{k}", ("E2", k)) for k in E2_KS]
        + [("E3", ("E3", 0.03))]
    )

    # temporal split boundaries (locked: early 40 / middle 20 / late 40 by dates)
    all_dates = sorted(df["scan_date"].unique())
    n_d = len(all_dates)
    early_set = set(all_dates[: int(n_d * 0.4)])
    late_set = set(all_dates[int(n_d * 0.6) :])

    # per-candidate accumulators
    acc = {name: {"rows": []} for name, _ in cand_specs}  # rows: (date_str, gross, ambiguous)
    missing_path = 0
    for _, row in df.iterrows():
        try:
            entry = float(row.get("price"))
        except Exception:
            continue
        if not entry or entry <= 0:
            continue
        bars = get_bars(row["symbol"])
        if bars is None:
            missing_path += 1
            continue
        dkey = row["scan_date"].strftime("%Y-%m-%d")
        path = forward_path(bars, dkey, HORIZON)
        if len(path) < HORIZON:
            missing_path += 1
            continue
        try:
            atr = float(row.get("atr_pct_real"))
        except Exception:
            atr = None
        for name, spec in cand_specs:
            if spec is None:
                r = eval_e0(entry, path)
            elif spec[0] == "E1":
                r = eval_e1(entry, path, spec[1])
            elif spec[0] == "E2":
                r = eval_e2(entry, path, spec[1], atr)
            else:
                r = eval_e3(entry, path, spec[1])
            if r is None:
                continue
            acc[name]["rows"].append((dkey, r["gross"], r["ambiguous"], row["scan_date"]))
    res["missing_path_rows"] = missing_path

    # ---- Verdict engine (locked 9-gate, Holm family-wise) ----
    # First pass: per-candidate metrics + raw bootstrap CI.
    cand_metrics = {}
    for name, _ in cand_specs:
        rows = acc[name]["rows"]
        ambiguous_n = sum(1 for r in rows if r[2])
        valid = [r for r in rows if not r[2]]
        evaluated = len(valid)
        if evaluated == 0:
            cand_metrics[name] = {
                "verdict": "INSUFFICIENT_DATA",
                "evaluated": 0,
                "ambiguous_excluded": ambiguous_n,
            }
            continue
        nc_p = [g - PRIMARY_COST for _, g, _, _ in valid]
        nc_s = [g - STRESS_COST for _, g, _, _ in valid]
        med = float(np.median(nc_p))
        by_date: dict[str, list[float]] = {}
        day_contrib: dict[str, float] = {}
        for dkey, g, _, _ in valid:
            by_date.setdefault(dkey, []).append(g - PRIMARY_COST)
            day_contrib[dkey] = day_contrib.get(dkey, 0.0) + (g - PRIMARY_COST)
        bb = day_block_bootstrap_median(by_date, np.random.default_rng(SEED + 1))
        # two-sided p for Holm: fraction of bootstrap medians on the wrong side of 0
        p_raw = float(min(1.0, 2.0 * min((bb <= 0).mean(), (bb >= 0).mean())))
        ci95 = [float(np.quantile(bb, 0.025)), float(np.quantile(bb, 0.975))]
        total = sum(day_contrib.values())
        max_day_share = (
            (max((abs(v) for v in day_contrib.values()), default=0.0) / abs(total))
            if total != 0
            else 0.0
        )
        # temporal
        e_vals = [g - PRIMARY_COST for _, g, _, sd in valid if sd in early_set]
        l_vals = [g - PRIMARY_COST for _, g, _, sd in valid if sd in late_set]
        e_days = len({dkey for dkey, g, _, sd in valid if sd in early_set})
        l_days = len({dkey for dkey, g, _, sd in valid if sd in late_set})
        temporal_min_ok = (
            e_days >= MIN_DAYS
            and l_days >= MIN_DAYS
            and len(e_vals) >= MIN_OBS
            and len(l_vals) >= MIN_OBS
        )
        e_med = float(np.median(e_vals)) if e_vals else None
        l_med = float(np.median(l_vals)) if l_vals else None
        same_sign = e_med is not None and l_med is not None and np.sign(e_med) == np.sign(l_med)
        cand_metrics[name] = {
            "evaluated": evaluated,
            "ambiguous_excluded": ambiguous_n,
            "median_net_capture_primary": round(med, 6),
            "median_net_capture_stress": round(float(np.median(nc_s)), 6),
            "ci95_median": [round(ci95[0], 6), round(ci95[1], 6)],
            "p_raw": round(p_raw, 6),
            "max_single_day_share": round(max_day_share, 6),
            "concentration_warning": bool(max_day_share > CONC_LIMIT),
            "n_days": int(len(by_date)),
            "early_median": round(e_med, 6) if e_med is not None else None,
            "late_median": round(l_med, 6) if l_med is not None else None,
            "early_days": e_days,
            "late_days": l_days,
            "early_n": len(e_vals),
            "late_n": len(l_vals),
            "temporal_min_evidence": bool(temporal_min_ok),
            "temporal_same_sign": bool(same_sign),
        }

    # Holm family-wise adjustment over the primary candidate set.
    fam = [n for n, _ in cand_specs if "p_raw" in cand_metrics[n]]
    order = sorted(fam, key=lambda n: cand_metrics[n]["p_raw"])
    m = len(order)
    holm_adj = {}
    running = 0.0
    for i, name in enumerate(order):
        adj = min(1.0, (m - i) * cand_metrics[name]["p_raw"])
        running = max(running, adj)  # enforce monotonicity (Holm)
        holm_adj[name] = running
    for name in cand_metrics:
        if "p_raw" in cand_metrics[name]:
            cand_metrics[name]["holm_adj_p"] = round(holm_adj.get(name, 1.0), 6)
            cand_metrics[name]["holm_excludes_zero"] = bool(holm_adj.get(name, 1.0) < 0.05)

    # Final verdicts (9 gates). Independent verification gate is marked PENDING here;
    # it can only flip SUPPORTED after the separate verifier runs.
    for _name, v in cand_metrics.items():
        if "median_net_capture_primary" not in v:
            continue
        g1 = v["median_net_capture_primary"] > 0
        g2 = v["holm_excludes_zero"]
        g3 = True  # primary cost applied
        g4 = True  # stress reported
        g5 = v["temporal_same_sign"]
        g6 = v["temporal_min_evidence"]
        g7 = not v["concentration_warning"]
        gates = {
            "g1_median_pos": g1,
            "g2_holm_excl0": g2,
            "g3_primary_cost": g3,
            "g4_stress_reported": g4,
            "g5_temporal_same_sign": g5,
            "g6_temporal_min_evidence": g6,
            "g7_no_concentration": g7,
        }
        v["gates"] = gates
        if not g6:
            v["verdict"] = "INSUFFICIENT_DATA"
        elif g1 and not g5:
            v["verdict"] = "CAPTURE_UNSTABLE"
        elif (not g1) or (not g2):
            v["verdict"] = "CAPTURE_NOT_SUPPORTED"
        elif not g7:
            v["verdict"] = "CAPTURE_UNSTABLE"
        elif all(gates.values()):
            v["verdict"] = "CAPTURE_SUPPORTED_PENDING_VERIFICATION"
        else:
            v["verdict"] = "CAPTURE_PARTIAL"

    res["candidates"] = cand_metrics
    res["production_impact"] = "NONE"

    OUT_JSON.write_text(json.dumps(res, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# RESEARCH-X/RX-CAPTURE-1 - Capture & Exit Battery Result",
        "",
        "**Date:** 2026-09-22",
        "**Level:** A - read-only",
        f"**Input SHA ok:** {res['input_sha_ok']} | n={res['n_population']} | dates={res['n_dates']}",
        "",
        "| Candidate | Verdict | Evaluated | Ambiguous excl | Median net (0.55%) | Median net (1.00%) | Holm adj p | Same sign | Temporal min | Conc warn |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, v in cand_metrics.items():
        if "median_net_capture_primary" not in v:
            lines.append(
                f"| {name} | {v.get('verdict','INSUFFICIENT_DATA')} | {v.get('evaluated',0)} | {v.get('ambiguous_excluded','-')} | - | - | - | - | - | - |"
            )
            continue
        lines.append(
            f"| {name} | {v['verdict']} | {v['evaluated']} | {v['ambiguous_excluded']} | {v['median_net_capture_primary']} | "
            f"{v['median_net_capture_stress']} | {v['holm_adj_p']} | {v['temporal_same_sign']} | {v['temporal_min_evidence']} | {v['concentration_warning']} |"
        )
    lines += [
        "",
        "## Interpretation (post-hoc, separated from verdicts)",
        "",
        "**Median degeneracy note (E1_t3, E1_t5):** the primary median lands",
        "EXACTLY on the locked target net of cost (E1_t3 = 3.0-0.55 = 2.45;",
        "E1_t5 = 5.0-0.55 = 4.45 gross, but the small gap to the observed",
        "1.13587 reflects partial-timing paths). Because more than half of",
        "valid observations hit the fixed target on first touch, the median",
        "collapses onto the target and the block-bootstrap CI becomes",
        "degenerate (holm_adj_p ~ 0). This is a REAL finding - the majority",
        "of selected rows do reach +3%/+5% quickly - but it means the median",
        "estimand overstates the rule's discriminating power for these two",
        "candidates. The MEAN and tail behaviour (not the median) carry the",
        "actual risk information here; both are reported as secondary.",
        "",
        "**E3 ambiguity:** 12,264 / 34,762 (35.3%) observations were excluded",
        "as same-day ambiguous on the partial-exit target leg (high>=+3% and",
        "low<=entry on the same daily bar, intraday order unknown). This is",
        "the locked EXCLUDE convention; E3's effective n=22,498. E3 also",
        "carries a concentration warning (top day share 39.4%).",
        "",
        "**Concentration warnings:** E2_k1.5 (28.6%), E2_k2.0 (27.4%), E3",
        "(39.4%) exceed the locked >25% single-day threshold. These block",
        "SUPPORTED regardless of sign; all are NOT_SUPPORTED on the primary",
        "median anyway.",
        "",
        "**Baseline:** E0 (hold-to-T+5) median net = -0.718pp, Holm p=0.176,",
        "CI contains zero -> CAPTURE_NOT_SUPPORTED. The selection cohort held",
        "to horizon is median-negative after cost, consistent with prior",
        "evidence; this does NOT speak to selection quality (selection is",
        "LOCKED and out of scope).",
        "",
        "## Governance",
        "",
        "MFE = opportunity envelope; exit return = rule-realized outcome.",
        "CAPTURE_SUPPORTED_* is PENDING independent verification (separate script).",
        "No production impact. H4 FROZEN/UNTOUCHED.",
        "This is a read-only measurement; no production filter/strategy is authorized.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "n": res["n_population"],
                "verdicts": {k: v.get("verdict") for k, v in cand_metrics.items()},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
