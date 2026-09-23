"""GATE B1 — Controlled live production instrumentation validation (Level B, approved).

MEASURE FIRST. CHANGE NOTHING. No predictive test. No backfill. No synthetic data.

Runs a SMALL controlled live scan (8 liquid symbols) through the REAL production
path (evaluate_symbols_parallel) twice:
  Phase A: instrumentation OFF (baseline snapshot, no artifact expected)
  Phase B: instrumentation ON  (persist artifact)
Then applies T1-T10: coverage, schema, raw fidelity, score/rank non-regression,
exact reconstruction, flag snapshot. Flag is process-local only; .env untouched.
"""

from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, ".")

SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "AMD"]
OUT_DIR = "data/backtest_out/production_instrumentation"


def reconstruct_reco(si: dict) -> float:
    vr = si.get("vol_regime")
    vr = int(vr) if vr is not None else 1
    momw = {0: 2.5, 1: 2.0, 2: 1.5}.get(vr, 2.0)
    return (
        2.0 * float(bool(si.get("regime")))
        + 2.0 * float(bool(si.get("direction")))
        + 0.5 * float(si.get("score", 0) or 0)
        + 1.5 * float(si.get("filter_score", 0) or 0)
        + 2.0 * float(si.get("alignment_ratio", 0.0) or 0.0)
        + momw * float(si.get("momentum_ratio", 0.0) or 0.0)
        + 0.5 * float(bool(si.get("volume_spike")))
        + 0.5 * float(bool(si.get("price_momentum")))
        + 0.5 * float(bool(si.get("trend_strength")))
    )


def snap(results):
    return {
        r["symbol"]: (r.get("score"), r.get("composite_score"), r.get("recommendation_score"))
        for r in results
    }


def main() -> int:
    from scanner.evaluate import evaluate_symbols_parallel

    print("=== Phase A: instrumentation OFF (baseline) ===")
    os.environ.pop("FINPILOT_INSTRUMENT_BASELINE", None)
    before = glob.glob(os.path.join(OUT_DIR, "baseline_inputs_*.jsonl"))
    res_off = evaluate_symbols_parallel(SYMBOLS, use_prefetch=True)
    after_off = glob.glob(os.path.join(OUT_DIR, "baseline_inputs_*.jsonl"))
    new_off = [f for f in after_off if f not in before]
    print(f"OFF: {len(res_off)} results; new artifacts = {len(new_off)} (expect 0)")
    baseline = snap(res_off)

    print("\n=== Phase B: instrumentation ON ===")
    os.environ["FINPILOT_INSTRUMENT_BASELINE"] = "1"
    res_on = evaluate_symbols_parallel(SYMBOLS, use_prefetch=True)
    os.environ.pop("FINPILOT_INSTRUMENT_BASELINE", None)
    after_on = glob.glob(os.path.join(OUT_DIR, "baseline_inputs_*.jsonl"))
    new_on = [f for f in after_on if f not in before]
    print(f"ON: {len(res_on)} results; new artifacts = {len(new_on)}")
    latest = sorted(new_on)[-1] if new_on else None

    report = {
        "symbols_requested": len(SYMBOLS),
        "results_off": len(res_off),
        "results_on": len(res_on),
        "artifact": latest,
    }

    # T6/T7 score+rank non-regression (same symbols, OFF vs ON)
    on_map = snap(res_on)
    common = set(baseline) & set(on_map)
    score_delta = sum(1 for s in common if baseline[s][0] != on_map[s][0])
    comp_delta = sum(1 for s in common if baseline[s][1] != on_map[s][1])
    report["non_regression"] = {
        "common_symbols": len(common),
        "score_changed": score_delta,
        "composite_changed": comp_delta,
    }

    # T1/T3/T4/T5/T8/T9 on persisted artifact
    if not latest:
        report["error"] = "no artifact written"
        print(json.dumps(report, indent=2))
        return 2

    recs = [json.loads(x) for x in open(latest, encoding="utf-8").read().splitlines() if x.strip()]
    report["records"] = len(recs)
    required = [
        "run_id",
        "scan_basis",
        "scan_ts_utc",
        "scan_date",
        "symbol",
        "regime",
        "direction",
        "score",
        "filter_score",
        "alignment_ratio",
        "momentum_ratio",
        "volume_spike",
        "price_momentum",
        "trend_strength",
        "vol_regime",
        "composite_score",
        "score_input",
        "instrumentation_version",
    ]
    field_missing = {k: sum(1 for r in recs if r.get(k) is None) for k in required}
    schema_missing = [k for r in recs for k in required if k not in r]
    report["schema_ok"] = len(schema_missing) == 0
    report["field_null_counts"] = field_missing
    report["scan_basis_ok"] = all(r.get("scan_basis") == "EOD" for r in recs)
    report["flag_snapshot_sample"] = recs[0].get("score_feature_flags")

    # T8 exact reconstruction
    recon = []
    for r in recs:
        si = r.get("score_input") or {}
        reco = reconstruct_reco(si)
        prod = r.get("recommendation_score")
        comp_sum = (r.get("score_component_breakdown") or {}).get("total")
        comp = round(max(0.0, min(1.0, reco / 16.5)) * 100)
        recon.append(
            {
                "symbol": r.get("symbol"),
                "reco": round(reco, 3),
                "prod_reco": prod,
                "reco_match": prod is not None and abs(reco - prod) < 1e-6,
                "component_sum": comp_sum,
                "comp_sum_match": comp_sum is not None and abs(comp_sum - reco) < 1e-6,
                "recon_composite": comp,
                "prod_composite": r.get("composite_score"),
                "composite_match": comp == r.get("composite_score"),
            }
        )
    report["reconstruction"] = recon
    report["recon_exact_rate"] = sum(1 for x in recon if x["reco_match"]) / max(1, len(recon))
    report["composite_exact_rate"] = sum(1 for x in recon if x["composite_match"]) / max(
        1, len(recon)
    )

    print("\n" + json.dumps(report, indent=2, default=str))
    with open("reports/gate_b1_live_result_2026_09_09.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
