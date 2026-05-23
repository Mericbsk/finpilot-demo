"""FinPilot Research Pipeline.

Orchestrates the weekly quality-improvement cycle:

  1. Walk-forward cross-validation (12 folds)
  2. Optuna weight sweep (200 trials)
  3. Register best weights as challenger in ModelRegistry
  4. Auto-promote challenger if it beats the current champion

Results are persisted in data/ and can be inspected via the research API.

Usage::

    from research.pipeline import run_research_pipeline
    summary = run_research_pipeline()
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def run_research_pipeline(
    n_optuna_trials: int = 200,
    min_brier_improvement: float = 0.01,
) -> dict[str, Any]:
    """Run WF + sweep + registry update. Returns a combined summary dict."""
    summary: dict[str, Any] = {}

    # --- 1. Walk-forward ---
    try:
        from research.walkforward import run_default_wf

        wf_summary = run_default_wf()
        summary["walkforward"] = wf_summary
        logger.info(
            "pipeline: walk-forward done — avg_brier=%.4f n_valid=%d",
            wf_summary.get("avg_brier", float("nan")),
            wf_summary.get("n_folds_valid", 0),
        )
    except Exception as exc:
        logger.warning("pipeline: walk-forward failed: %s", exc)
        summary["walkforward"] = {"status": "error", "error": str(exc)}

    # --- 2. Optuna sweep ---
    best_weights: dict[str, float] | None = None
    try:
        from research.sweep import best_weights_from_study, run_sweep, save_best_weights

        study = run_sweep(n_trials=n_optuna_trials)
        best_weights = best_weights_from_study(study)
        if best_weights:
            save_best_weights(best_weights)
            n_pareto = len(study.best_trials) if study else 0
            summary["sweep"] = {
                "status": "ok",
                "n_trials": len(study.trials) if study else 0,
                "n_pareto": n_pareto,
                "best_weights": best_weights,
            }
            logger.info(
                "pipeline: sweep done — %d trials, best_weights=%s",
                summary["sweep"]["n_trials"],
                best_weights,
            )
        else:
            summary["sweep"] = {"status": "insufficient_data"}
    except Exception as exc:
        logger.warning("pipeline: optuna sweep failed: %s", exc)
        summary["sweep"] = {"status": "error", "error": str(exc)}

    # --- 3. Register challenger in ModelRegistry ---
    if best_weights:
        try:
            from research.registry import ModelRegistry
            from research.walkforward import load_last_results

            wf_data = load_last_results() or {}
            avg_brier = float(wf_data.get("avg_brier") or 0.25)
            avg_wr = float(wf_data.get("avg_win_rate") or 0.5)

            reg = ModelRegistry()

            # Ensure there is at least one champion (seed current calibration if empty)
            if reg.get_champion() is None:
                _seed_initial_champion(reg)

            row_id = reg.register_candidate(
                weights=best_weights,
                brier_score=avg_brier,
                win_rate=avg_wr,
                profit_factor=1.0,
                n_samples=wf_data.get("n_folds_valid") or 0,
                name=f"sweep_{__import__('datetime').datetime.utcnow().strftime('%Y%m%d')}",
            )
            summary["registry"] = {"challenger_id": row_id, "status": "registered"}

            # --- 4. Auto-promote if better ---
            promoted = reg.auto_promote_best(min_brier_improvement=min_brier_improvement)
            summary["registry"]["promoted"] = promoted
            if promoted:
                logger.info("pipeline: challenger id=%d promoted to champion", row_id)
        except Exception as exc:
            logger.warning("pipeline: registry update failed: %s", exc)
            summary["registry"] = {"status": "error", "error": str(exc)}
    else:
        summary["registry"] = {"status": "skipped", "reason": "no best_weights"}

    return summary


def _seed_initial_champion(reg: Any) -> None:
    """Register current calibration weights as the baseline champion."""
    try:
        from research.sweep import WEIGHT_KEYS

        default_weights = {k: round(1.0 / len(WEIGHT_KEYS), 4) for k in WEIGHT_KEYS}
        row_id = reg.register_candidate(
            weights=default_weights,
            brier_score=0.25,
            win_rate=0.5,
            profit_factor=1.0,
            n_samples=0,
            name="baseline_uniform",
        )
        reg.promote(row_id)
        logger.info("pipeline: seeded initial champion (uniform weights, id=%d)", row_id)
    except Exception as exc:
        logger.warning("pipeline: could not seed initial champion: %s", exc)
