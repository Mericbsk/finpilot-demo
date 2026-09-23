"""FLAG IMPACT MEASUREMENT — observability only (no predictive test).

Measures each real score-affecting flag's BEHAVIORAL effect (score delta, rank delta,
affected symbols) on the LATEST full export, by RE-RUNNING the actual production
compute_recommendation_score with one flag toggled at a time (process-local env).
No re-implementation of the formula; production code does the scoring.

NOT_A_FLAG (per Section 4, verified in code — these are always-on baseline inputs,
not env-gated flags): filter_score, alignment_ratio, momentum_ratio, volume_spike,
price_momentum, trend_strength. Excluded from flag ablation.

Measured flags (score-affecting, env-gated):
  SQUEEZE (FINPILOT_ENABLE_SQUEEZE_FACTOR), EDGAR_CATALYST, LOTTERY_FADE,
  OVERNIGHT_GAP, FRED_MACRO (multiplier).

OFF semantics (production): gated factor contributes 0 (factor treated as absent).
ON semantics: factor contributes per production weights. Production code decides.
No synthetic data, no imputation, no historical backfill. Read-only on the export.

Rank: computed per the export's own ordering (composite_score desc) within the
full universe. rank_delta = rank_on - rank_off (negative = improved, §11).

Output: reports/flag_impact/flag_impact_{summary.json,symbol_level.csv,report.md}
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from datetime import UTC, datetime

sys.path.insert(0, ".")

EXPORT = "data/distribution/scan_export_latest.json"
OUT_DIR = "reports/flag_impact"

# Real env-gated score flags -> the score_input factor key they gate
FLAGS = {
    "SQUEEZE": ("FINPILOT_ENABLE_SQUEEZE_FACTOR", "squeeze_factor"),
    "EDGAR_CATALYST": ("FINPILOT_ENABLE_EDGAR_CATALYST", "catalyst_factor"),
    "LOTTERY_FADE": ("FINPILOT_ENABLE_LOTTERY_FADE", "lottery_factor"),
    "OVERNIGHT_GAP": ("FINPILOT_ENABLE_OVERNIGHT_GAP", "overnight_gap_factor"),
    "FRED_MACRO": ("FINPILOT_ENABLE_FRED_MACRO", None),  # multiplier, no direct factor
}

# production current (.env) state for these flags
ENV_NOW = {
    "FINPILOT_ENABLE_SQUEEZE_FACTOR": "1",
    "FINPILOT_ENABLE_EDGAR_CATALYST": "1",
    "FINPILOT_ENABLE_FRED_MACRO": "1",
    "FINPILOT_ENABLE_LOTTERY_FADE": "1",
    "FINPILOT_ENABLE_OVERNIGHT_GAP": "1",
}

# Score-change tolerance: production rounds recommendation_score to 3 decimals and
# composite_score is an int (0-100). A real change = composite int change OR |reco| > 1e-2
# (matches production's own 3dp rounding; avoids FP noise). Documented, not invented.
SCORE_TOL = 1e-2


def load_rows():
    d = json.load(open(EXPORT, encoding="utf-8"))
    rows = d["results"]
    meta = {
        k: d.get(k)
        for k in (
            "date",
            "generated_at",
            "run_id",
            "universe",
            "scan_id",
            "scan_complete",
            "result_count",
        )
    }
    return rows, meta


def set_env(state: dict[str, str]) -> dict[str, str | None]:
    prev = {k: os.environ.get(k) for k in ENV_NOW}
    for k, v in state.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    return prev


def compute_scores(rows):
    """Run production compute_recommendation_score over each row's score_input.

    CRITICAL (verified 2026-09-10): the stored export recommendation_score was
    computed with sentiment_score=None (sentiment contribution = 0), even though a
    `sentiment` field exists on the row. Recompute with sentiment=None reproduces the
    stored value 100% exactly; passing the row sentiment adds a spurious ±0.5 offset.
    So we pass sentiment_score=None to match production, and we MEASURE only flag deltas.
    """
    from scanner.score_engine import compute_recommendation_score

    out = {}
    for r in rows:
        si = r.get("score_input") or {}
        out[r["symbol"]] = compute_recommendation_score(dict(si), sentiment_score=None)
    return out


def ranks_of(scores: dict[str, float]) -> dict[str, int]:
    order = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return {sym: i + 1 for i, (sym, _) in enumerate(order)}


def main() -> int:
    rows, meta = load_rows()
    os.makedirs(OUT_DIR, exist_ok=True)
    git = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    universe = [r["symbol"] for r in rows]

    # integrity: duplicate/missing symbols, NaN
    seen = set()
    dup = [s for s in universe if s in seen or seen.add(s)]
    missing_si = sum(1 for r in rows if not r.get("score_input"))

    summary = {
        "export": EXPORT,
        "export_meta": meta,
        "git_commit": git,
        "measurement_ts_utc": datetime.now(UTC).isoformat(),
        "symbols": len(rows),
        "duplicate_symbols": dup,
        "missing_score_input": missing_si,
        "score_tolerance": SCORE_TOL,
        "flag_semantics": "OFF = gated factor contributes 0 (production env-gate); "
        "ON = factor active per production weights. Production code decides.",
        "env_now": ENV_NOW,
    }

    # Baseline = ALL score flags OFF (the flag-free baseline). Flag impact is then
    # measured as flag-ON vs this OFF baseline (production semantics: OFF = factor 0).
    # We ALSO record the production current state (all-ON per .env) for reference and
    # verify recompute(all-ON) == stored recommendation_score (sentiment=None) exactly.
    set_env(ENV_NOW)
    allon_scores = compute_scores(rows)
    stored = {r["symbol"]: r.get("recommendation_score") for r in rows}
    recon_match = sum(
        1
        for s in universe
        if stored[s] is not None and abs(allon_scores[s] - stored[s]) < SCORE_TOL
    )
    summary["recompute_allon_vs_stored"] = {
        "n": sum(1 for s in universe if stored[s] is not None),
        "exact_match": recon_match,
    }
    set_env({k: "0" for k in ENV_NOW})
    base_scores = compute_scores(rows)
    base_ranks = ranks_of(base_scores)

    symbol_rows = []
    flag_summary = []

    for flag, (envkey, factor) in FLAGS.items():
        # Flag-ON (only this flag) vs all-OFF baseline. Others stay OFF.
        state = {k: "0" for k in ENV_NOW}
        state[envkey] = "1"
        set_env(state)
        on_scores = compute_scores(rows)
        set_env({k: "0" for k in ENV_NOW})  # restore OFF baseline
        on_ranks = ranks_of(on_scores)

        deltas = {s: on_scores[s] - base_scores[s] for s in universe}
        abs_d = [abs(v) for v in deltas.values()]
        rank_d = {s: on_ranks[s] - base_ranks[s] for s in universe}
        abs_rd = [abs(v) for v in rank_d.values()]

        score_changed = sum(1 for s in universe if abs(deltas[s]) > SCORE_TOL)
        rank_changed = sum(1 for s in universe if rank_d[s] != 0)
        any_effect = sum(1 for s in universe if abs(deltas[s]) > SCORE_TOL or rank_d[s] != 0)

        # classification (§13) — qualitative; no invented material threshold
        if score_changed == 0 and rank_changed == 0:
            cls = "NO_EFFECT"
        elif rank_changed == 0:
            cls = "SCORE_ONLY_EFFECT"
        else:
            cls = "RANK_EFFECT"

        import statistics as st

        flag_summary.append(
            {
                "flag": flag,
                "env": envkey,
                "gated_factor": factor,
                "score_delta_mean": round(st.mean(deltas.values()), 4),
                "score_delta_min": round(min(deltas.values()), 4),
                "score_delta_max": round(max(deltas.values()), 4),
                "score_abs_delta_mean": round(st.mean(abs_d), 4),
                "score_abs_delta_max": round(max(abs_d), 4),
                "score_delta_median": round(st.median(deltas.values()), 4),
                "symbols_score_changed": score_changed,
                "symbols_score_unchanged": len(universe) - score_changed,
                "mean_abs_rank_delta": round(st.mean(abs_rd), 3),
                "median_abs_rank_delta": round(st.median(abs_rd), 3),
                "max_abs_rank_delta": max(abs_rd),
                "symbols_rank_changed": rank_changed,
                "symbols_any_effect": any_effect,
                "classification": cls,
            }
        )

        for s in universe:
            if abs(deltas[s]) > SCORE_TOL or rank_d[s] != 0:
                symbol_rows.append(
                    {
                        "flag": flag,
                        "symbol": s,
                        "score_off": round(base_scores[s], 4),
                        "score_on": round(on_scores[s], 4),
                        "score_delta": round(deltas[s], 4),
                        "rank_off": base_ranks[s],
                        "rank_on": on_ranks[s],
                        "rank_delta": rank_d[s],
                    }
                )

    summary["flags"] = flag_summary
    summary["total_flag_changes_logged"] = len(symbol_rows)

    with open(os.path.join(OUT_DIR, "flag_impact_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    with open(
        os.path.join(OUT_DIR, "flag_impact_symbol_level.csv"), "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "flag",
                "symbol",
                "score_off",
                "score_on",
                "score_delta",
                "rank_off",
                "rank_on",
                "rank_delta",
            ],
        )
        w.writeheader()
        w.writerows(symbol_rows)

    print(json.dumps({k: v for k, v in summary.items() if k != "flags"}, indent=2, default=str))
    print("\n=== FLAG SUMMARY ===")
    for fs in flag_summary:
        print(json.dumps(fs, default=str))
    print("\nsymbol-level rows:", len(symbol_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
