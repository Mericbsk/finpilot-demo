"""FinPilot Research — Walk-Forward Cross Validation.

Splits signal history into (train, val) folds and evaluates Brier score
per fold to detect model drift and tune calibration weights.

Usage::

    from research.walkforward import WalkForwardCV, run_default_wf
    results = run_default_wf()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

N_FOLDS = 12
TRAIN_MONTHS = 24
VAL_MONTHS = 6


@dataclass
class WFResult:
    fold: int
    train_start: str
    train_end: str
    val_start: str
    val_end: str
    n_train: int
    n_val: int
    brier_score: float
    win_rate: float
    extra: dict = field(default_factory=dict)


def _brier_score(signals: list[dict]) -> float:
    """Compute Brier score: mean((p_win - outcome_01)^2)."""
    resolved = [
        s for s in signals if s.get("outcome") in ("win", "loss") and s.get("p_win") is not None
    ]
    if not resolved:
        return float("nan")
    total = 0.0
    for s in resolved:
        p = float(s["p_win"])
        y = 1.0 if s["outcome"] == "win" else 0.0
        total += (p - y) ** 2
    return total / len(resolved)


class WalkForwardCV:
    """Walk-forward cross-validation over KPI tracker signals.

    Parameters
    ----------
    n_folds : int
        Number of folds to evaluate.
    train_months : int
        Training window length in calendar months.
    val_months : int
        Validation window length in calendar months.
    """

    def __init__(
        self,
        n_folds: int = N_FOLDS,
        train_months: int = TRAIN_MONTHS,
        val_months: int = VAL_MONTHS,
    ):
        self.n_folds = n_folds
        self.train_months = train_months
        self.val_months = val_months

    def _signals(self) -> list[dict]:
        from core.kpi_tracker import _load_all_signals

        return _load_all_signals()

    def run(self) -> list[WFResult]:
        """Run all folds and return results."""
        signals = self._signals()
        if not signals:
            logger.warning("walkforward: no signals found")
            return []

        now = datetime.now(tz=UTC)
        results: list[WFResult] = []

        for fold in range(self.n_folds):
            # Validation window ends at: now - fold * val_months
            val_end = now - timedelta(days=fold * self.val_months * 30)
            val_start = val_end - timedelta(days=self.val_months * 30)
            train_end = val_start
            train_start = train_end - timedelta(days=self.train_months * 30)

            def in_window(sig: dict, start: datetime, end: datetime) -> bool:
                ts_ms = int(sig.get("ts", 0))
                dt = datetime.fromtimestamp(ts_ms / 1000, tz=UTC)
                return start <= dt < end

            train_sigs = [s for s in signals if in_window(s, train_start, train_end)]
            val_sigs = [s for s in signals if in_window(s, val_start, val_end)]

            brier = _brier_score(val_sigs)
            val_resolved = [s for s in val_sigs if s.get("outcome") in ("win", "loss")]
            win_rate = (
                sum(1 for s in val_resolved if s["outcome"] == "win") / len(val_resolved)
                if val_resolved
                else 0.0
            )

            results.append(
                WFResult(
                    fold=fold + 1,
                    train_start=train_start.strftime("%Y-%m-%d"),
                    train_end=train_end.strftime("%Y-%m-%d"),
                    val_start=val_start.strftime("%Y-%m-%d"),
                    val_end=val_end.strftime("%Y-%m-%d"),
                    n_train=len(train_sigs),
                    n_val=len(val_sigs),
                    brier_score=round(brier, 4) if brier == brier else float("nan"),
                    win_rate=round(win_rate, 4),
                )
            )

        return results

    def summary(self) -> dict[str, Any]:
        """Run walk-forward and return aggregate statistics."""
        results = self.run()
        valid = [r for r in results if r.brier_score == r.brier_score]  # exclude NaN
        if not valid:
            return {"status": "insufficient_data", "n_folds": self.n_folds}

        avg_brier = sum(r.brier_score for r in valid) / len(valid)
        avg_wr = sum(r.win_rate for r in valid) / len(valid)
        return {
            "status": "ok",
            "n_folds_run": len(results),
            "n_folds_valid": len(valid),
            "avg_brier": round(avg_brier, 4),
            "avg_win_rate": round(avg_wr, 4),
            "folds": [
                {
                    "fold": r.fold,
                    "val_start": r.val_start,
                    "val_end": r.val_end,
                    "n_val": r.n_val,
                    "brier": r.brier_score,
                    "win_rate": r.win_rate,
                }
                for r in results
            ],
        }


_WF_RESULTS_PATH = Path("data/walkforward_results.json")


def save_results(summary: dict[str, Any]) -> None:
    """Persist walk-forward summary to data/walkforward_results.json."""
    _WF_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    from datetime import UTC, datetime

    summary["saved_at"] = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
    _WF_RESULTS_PATH.write_text(
        __import__("json").dumps(summary, indent=2, default=str),
        encoding="utf-8",
    )
    logger.info("walkforward: results saved to %s", _WF_RESULTS_PATH)


def load_last_results() -> dict[str, Any] | None:
    """Load the most recently saved walk-forward results, or None."""
    if not _WF_RESULTS_PATH.exists():
        return None
    try:
        return __import__("json").loads(_WF_RESULTS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("walkforward: could not load results: %s", exc)
        return None


def run_default_wf() -> dict[str, Any]:
    """Run walk-forward with default parameters, save and return summary."""
    cv = WalkForwardCV()
    summary = cv.summary()
    save_results(summary)
    return summary
