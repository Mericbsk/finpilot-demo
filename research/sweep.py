"""FinPilot Research — Optuna Weight Sweep.

Multi-objective Optuna study to optimize 10 score component weights
minimizing Brier score and maximizing profit factor simultaneously.

Reads existing optuna_conservative_results.json if available to seed
the initial trial population.

Usage::

    from research.sweep import run_sweep
    study = run_sweep(n_trials=200)
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Score component weight keys (must match scanner/score_engine.py features)
WEIGHT_KEYS = [
    "w_rsi",
    "w_macd",
    "w_volume",
    "w_trend",
    "w_momentum",
    "w_volatility",
    "w_support",
    "w_sector_rs",
    "w_earnings_safety",
    "w_pattern",
]

OPTUNA_RESULTS_PATH = Path("optuna_conservative_results.json")
_SWEEP_RESULTS_PATH = Path("data/optuna_best_weights.json")


def save_best_weights(weights: dict[str, float]) -> None:
    """Persist best weights to data/optuna_best_weights.json."""
    _SWEEP_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "weights": weights,
        "saved_at": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"),
    }
    _SWEEP_RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("sweep: best weights saved to %s", _SWEEP_RESULTS_PATH)


def load_last_weights() -> dict[str, float] | None:
    """Load the most recently saved best weights, or None."""
    if not _SWEEP_RESULTS_PATH.exists():
        return None
    try:
        return json.loads(_SWEEP_RESULTS_PATH.read_text(encoding="utf-8")).get("weights")
    except Exception as exc:
        logger.warning("sweep: could not load weights: %s", exc)
        return None


def _load_seed_trials() -> list[dict[str, float]]:
    """Load prior Optuna results to warm-start the study."""
    if not OPTUNA_RESULTS_PATH.exists():
        return []
    try:
        data = json.loads(OPTUNA_RESULTS_PATH.read_text())
        # Expect list of {weight_key: value, ...} dicts or {"params": {...}} dicts
        trials = []
        if isinstance(data, list):
            for item in data:
                params = item.get("params", item)
                if isinstance(params, dict) and any(k in params for k in WEIGHT_KEYS):
                    trials.append({k: float(params.get(k, 1.0)) for k in WEIGHT_KEYS})
        elif isinstance(data, dict):
            params = data.get("best_params", data.get("params", data))
            if isinstance(params, dict):
                trials.append({k: float(params.get(k, 1.0)) for k in WEIGHT_KEYS})
        logger.info("sweep: loaded %d seed trials from %s", len(trials), OPTUNA_RESULTS_PATH)
        return trials
    except Exception as exc:
        logger.warning("sweep: could not load seed trials: %s", exc)
        return []


def _objective(trial: Any, signals: list[dict]) -> tuple[float, float]:
    """Optuna objective — returns (brier_score, -profit_factor)."""
    # Sample weights
    weights = {k: trial.suggest_float(k, 0.0, 3.0) for k in WEIGHT_KEYS}
    total_w = sum(weights.values()) or 1.0
    norm_w = {k: v / total_w for k, v in weights.items()}

    # Re-score signals using proposed weights
    resolved = [s for s in signals if s.get("outcome") in ("win", "loss")]
    if len(resolved) < 10:
        return 0.25, -1.0  # neutral when insufficient data

    # Compute re-weighted score for each signal
    brier_total = 0.0
    profit_sum = 0.0
    loss_sum = 0.0

    for sig in resolved:
        # Use norm_w as blend against existing score (simplified: scale p_win)
        base_score = float(sig.get("score", 0.0))
        # Weight-adjusted score: sum(w_i * feature_i) — features not stored on signal,
        # so proxy by scaling existing score with top-weight ratio
        top_w = max(norm_w.values())
        adj_score = base_score * top_w * len(WEIGHT_KEYS)
        # Clamp to [0, 18.3] (MAX_RECO_SCORE)
        adj_score = min(max(adj_score, 0.0), 18.3)
        p_win = adj_score / 18.3  # naive linear calibration
        y = 1.0 if sig["outcome"] == "win" else 0.0
        brier_total += (p_win - y) ** 2
        profit_pct = float(sig.get("profit_pct") or 0.0)
        if profit_pct > 0:
            profit_sum += profit_pct
        else:
            loss_sum += abs(profit_pct)

    brier = brier_total / len(resolved)
    profit_factor = profit_sum / loss_sum if loss_sum > 0 else profit_sum or 1.0
    return round(brier, 6), round(-profit_factor, 6)


def run_sweep(n_trials: int = 200, study_name: str = "finpilot_weight_sweep") -> Any:
    """Run Optuna multi-objective sweep.

    Returns the Optuna study object. Best parameters can be extracted via
    ``study.best_trials``.
    """
    try:
        import optuna
    except ImportError:
        logger.error("sweep: optuna not installed — pip install optuna")
        return None

    from core.kpi_tracker import _load_all_signals

    signals = _load_all_signals()

    study = optuna.create_study(
        study_name=study_name,
        directions=["minimize", "minimize"],  # brier ↓, -PF ↓ (i.e. PF ↑)
        sampler=optuna.samplers.TPESampler(seed=42),
    )

    # Seed with prior results
    for seed_params in _load_seed_trials():
        try:
            study.enqueue_trial(seed_params)
        except Exception:
            pass

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(lambda trial: _objective(trial, signals), n_trials=n_trials)

    logger.info(
        "sweep: completed %d trials, %d Pareto-optimal",
        len(study.trials),
        len(study.best_trials),
    )
    return study


def best_weights_from_study(study: Any) -> dict[str, float] | None:
    """Extract best-brier weights from a completed study's Pareto front."""
    if study is None or not study.best_trials:
        return None
    # Pick trial with lowest Brier from Pareto front
    best = min(study.best_trials, key=lambda t: t.values[0])
    total_w = sum(best.params.values()) or 1.0
    return {k: round(v / total_w, 4) for k, v in best.params.items()}
