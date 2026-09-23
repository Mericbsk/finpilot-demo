"""Level B instrumentation validation — schema / non-regression / reconstruction.

READ-ONLY verification of the observability hook. Does NOT modify production.
Tests:
  T1 Schema: emitted record has all required fields.
  T2 Score non-regression: instrumentation does not alter compute_recommendation_score.
  T3 Rank non-regression: ranks unchanged on a synthetic universe.
  T4 Reconstruction: from persisted components, reco/composite reconstruct exactly.
Run: python -m research.instrumentation_validation_2026_09_09
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, ".")
from scanner.score_engine import (  # noqa: E402
    compute_recommendation_score,
    compute_recommendation_strength,
    score_component_breakdown,
)

SAMPLE = {
    "regime": True,
    "direction": True,
    "score": 2,
    "filter_score": 3,
    "alignment_ratio": 0.75,
    "momentum_ratio": 0.67,
    "volume_spike": True,
    "price_momentum": True,
    "trend_strength": True,
    "vol_regime": 1,
    "squeeze_factor": 0.0,
    "catalyst_factor": 0.0,
    "lottery_factor": 0.0,
    "overnight_gap_factor": 0.0,
}


def reconstruct_reco(rec: dict) -> float:
    """Recompute reco from persisted score_input/components (FLAG-OFF, as persisted)."""
    si = rec.get("score_input") or {}
    vr = si.get("vol_regime")
    vr = int(vr) if vr is not None else 1
    momw = {0: 2.5, 1: 2.0, 2: 1.5}.get(vr, 2.0)
    reco = (
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
    return reco


def main() -> int:
    ok = True

    # T2/T3: score + rank non-regression (instrumentation not in compute path).
    base = compute_recommendation_score(dict(SAMPLE))
    strength_before = compute_recommendation_strength(dict(SAMPLE))
    # Simulate instrumentation flag ON and re-run (emit path is separate from compute).
    os.environ["FINPILOT_INSTRUMENT_BASELINE"] = "1"
    base2 = compute_recommendation_score(dict(SAMPLE))
    strength_after = compute_recommendation_strength(dict(SAMPLE))
    os.environ.pop("FINPILOT_INSTRUMENT_BASELINE", None)
    score_delta = abs(base - base2)
    rank_ok = strength_before == strength_after
    print(
        f"T2 score non-regression: before={base} after={base2} delta={score_delta} -> {'PASS' if score_delta==0 else 'FAIL'}"
    )
    print(
        f"T3 rank non-regression (strength): {strength_before}=={strength_after} -> {'PASS' if rank_ok else 'FAIL'}"
    )
    ok &= (score_delta == 0) and rank_ok

    # T4: reconstruction from persisted components.
    rec = {"score_input": dict(SAMPLE)}
    reco = reconstruct_reco(rec)
    comp = score_component_breakdown(dict(SAMPLE))
    # production reco == sum of components
    prod_reco = compute_recommendation_score(dict(SAMPLE))
    recon_match = abs(reco - prod_reco) < 1e-6
    comp_total_match = abs(comp["total"] - prod_reco) < 1e-6
    print(
        f"T4 reconstruction: reco={reco} production={prod_reco} match={recon_match} -> {'PASS' if recon_match else 'FAIL'}"
    )
    print(
        f"   components sum={comp['total']} == production {prod_reco} -> {'PASS' if comp_total_match else 'FAIL'}"
    )
    # composite = round(clamp(reco/16.5,0,1)*100)
    comp_score = round(max(0.0, min(1.0, reco / 16.5)) * 100)
    print(
        f"   reconstructed composite={comp_score} production strength={strength_before} -> {'PASS' if comp_score==strength_before else 'FAIL'}"
    )
    ok &= recon_match and comp_total_match and (comp_score == strength_before)

    # T1: schema check via a synthetic emit (to temp dir, then remove).
    from scanner import instrumentation as inst

    os.environ["FINPILOT_INSTRUMENT_BASELINE"] = "1"
    res = dict(SAMPLE)
    res.update({"symbol": "TEST", "timestamp": "2026-09-09 15:30"})
    res["score_input"] = dict(SAMPLE)
    run_id = inst.emit_baseline_inputs([res], scan_basis="EOD")
    os.environ.pop("FINPILOT_INSTRUMENT_BASELINE", None)
    if run_id:
        import glob
        import json

        f = sorted(
            glob.glob(
                f"data/backtest_out/production_instrumentation/baseline_inputs_{run_id}.jsonl"
            )
        )[-1]
        row = json.loads(open(f, encoding="utf-8").readline())
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
        missing = [k for k in required if k not in row]
        print(
            f"T1 schema: run_id={run_id} missing={missing} -> {'PASS' if not missing else 'FAIL'}"
        )
        ok &= not missing
        os.remove(f)
    else:
        print("T1 schema: emit returned None -> FAIL")
        ok = False

    print("\nOVERALL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
