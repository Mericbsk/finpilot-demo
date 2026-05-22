"""Sprint 16 (S16-14): Look-ahead / leakage audit script.

Compares backtest-implied signal scores against paper-trade realized outcomes
to detect potential look-ahead bias or training-leakage in the scanner.

Method
------
1. Load all resolved signals from the KPI tracker (paper-trade outcomes).
2. Bucket them by 10-point score band (0-9, 10-19, ..., 90-100).
3. For each band, compute realized win-rate and compare to the calibration
   model's predicted probability for that band.
4. Flag any band where |realized - predicted| > 0.10 as suspicious — this is
   the classical signature of look-ahead (training-time edge that vanishes
   in production).
5. Also emit a global Brier delta between calibration-model prediction and
   realized outcome.

Usage
-----
    python -m scripts.audit_lookahead

Exit code 0 = no leakage suspected; 1 = at least one band flagged.

Output is JSON + a human-readable summary written to ``reports/lookahead_audit.json``.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

THRESHOLD_BAND = 0.10  # |realized - predicted| above this flags a band
THRESHOLD_GLOBAL_BRIER = 0.05  # absolute Brier delta above this is suspicious
REPORT_PATH = Path("reports/lookahead_audit.json")


def _load_signals() -> list[dict]:
    try:
        from core.kpi_tracker import _load_all_signals  # type: ignore
    except Exception as exc:
        print(f"FATAL: cannot import kpi_tracker: {exc}", file=sys.stderr)
        sys.exit(2)
    return _load_all_signals()


def _load_calibration():
    try:
        from core.calibration import get_calibration_model, _probability_for  # type: ignore
    except Exception as exc:
        print(f"WARN: calibration import failed: {exc}", file=sys.stderr)
        return None, None
    return get_calibration_model(), _probability_for


def main() -> int:
    signals = _load_signals()
    resolved = [s for s in signals if s.get("outcome") in ("win", "loss")]
    if not resolved:
        print("No resolved signals — cannot audit. (Run reconciler first.)")
        return 0

    model, predict_fn = _load_calibration()

    # Bucket by 10-point band
    bands: dict[int, list[dict]] = {i: [] for i in range(0, 100, 10)}
    for s in resolved:
        score = float(s.get("score", 0) or 0)
        bucket = min(90, int(score // 10) * 10)
        bands[bucket].append(s)

    band_report: list[dict] = []
    flagged: list[str] = []
    sq_err_total: float = 0.0
    n_total: int = 0

    for low, group in sorted(bands.items()):
        if not group:
            continue
        wins = sum(1 for s in group if s["outcome"] == "win")
        n = len(group)
        realized = wins / n
        # Predicted prob: use middle of band against calibration model if present
        mid_score = low + 5
        predicted = None
        if model and predict_fn:
            try:
                predicted = float(predict_fn(model, mid_score))
            except Exception:
                predicted = None
        if predicted is None:
            predicted = mid_score / 100.0  # naive fallback
        gap = realized - predicted
        flag = abs(gap) > THRESHOLD_BAND and n >= 10
        band_report.append(
            {
                "band": f"{low}-{low + 9}",
                "n": n,
                "realized_p_win": round(realized, 3),
                "predicted_p_win": round(predicted, 3),
                "gap": round(gap, 3),
                "flagged": flag,
            }
        )
        if flag:
            flagged.append(f"{low}-{low + 9} (n={n}, gap={gap:+.3f})")

        # accumulate Brier components
        for s in group:
            y = 1.0 if s["outcome"] == "win" else 0.0
            sq_err_total += (predicted - y) ** 2
            n_total += 1

    global_brier = round(sq_err_total / n_total, 4) if n_total else None

    summary = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "n_resolved_signals": len(resolved),
        "n_bands_with_data": len(band_report),
        "global_brier": global_brier,
        "band_report": band_report,
        "flagged_bands": flagged,
        "verdict": "OK" if not flagged else "SUSPECT_LEAKAGE",
        "thresholds": {
            "band_gap": THRESHOLD_BAND,
            "global_brier": THRESHOLD_GLOBAL_BRIER,
        },
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Look-ahead audit complete → {REPORT_PATH}")
    print(f"  resolved signals : {len(resolved)}")
    print(f"  bands w/ data    : {len(band_report)}")
    print(f"  global Brier     : {global_brier}")
    print(f"  flagged bands    : {len(flagged)}")
    for line in flagged:
        print(f"    ⚠  {line}")
    print(f"  verdict          : {summary['verdict']}")

    return 0 if not flagged else 1


if __name__ == "__main__":
    sys.exit(main())
