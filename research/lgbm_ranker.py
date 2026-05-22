"""LightGBM Layer 2 Ranker — Sprint 15 PoC

Layer 1: scanner/finpilot_score.py  (rule-based composite, 0-100)
Layer 2: LGBMRanker                 (learns signal-to-outcome mapping)

The ranker takes Layer-1 features as input and outputs a *ranking score*
that re-orders signals before they are shown in the dashboard.

Walk-forward evaluation
-----------------------
Uses research.walkforward.WalkForwardEngine to produce per-fold AUC scores.
Each fold trains on 24 months of labelled signal outcomes and evaluates on
the following 6 months.  Results are written to ``data/lgbm_ranker_wf.json``.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def is_enabled() -> bool:
    """Sprint 16 (S16-09): LGBM ranker feature flag.

    Disabled by default. Set ``FINPILOT_ENABLE_LGBM_RANKER=1`` to enable.
    Until a live edge is demonstrated, the ranker stays opt-in.
    See ``docs/feature_flags.md``.
    """
    return os.getenv("FINPILOT_ENABLE_LGBM_RANKER", "0").lower() in ("1", "true", "yes", "on")

_WF_RESULTS_PATH = Path("data/lgbm_ranker_wf.json")
_MODEL_PATH = Path("data/lgbm_ranker.pkl")

# ─────────────────────────────────────────────
# Feature engineering
# ─────────────────────────────────────────────

FEATURE_COLS = [
    "score",           # Layer-1 FinPilot score (0-100)
    "rsi",             # RSI-14
    "macd_hist",       # MACD histogram
    "volume_ratio",    # volume / 20d avg volume
    "sector_rs",       # sector relative strength vs SPY
    "vol_regime",      # realised vol regime (0=low, 1=normal, 2=high)
    "regime_encoded",  # market regime (0=bull, 1=range, 2=bear)
    "p_win_calib",     # calibrated p_win from isotonic model
]


def _signals_to_df(signals: list[dict[str, Any]]) -> "pd.DataFrame":  # type: ignore[name-defined]
    """Convert raw signal dicts into a feature DataFrame for the ranker."""
    import pandas as pd  # noqa: PLC0415

    rows = []
    for s in signals:
        row: dict[str, Any] = {}
        for col in FEATURE_COLS:
            row[col] = float(s.get(col) or 0.0)
        # Label: 1 if outcome is positive, 0 otherwise
        outcome = s.get("outcome")
        row["label"] = int(outcome == "win") if outcome is not None else -1
        row["ts"] = float(s.get("ts") or s.get("timestamp") or 0)
        rows.append(row)
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# Training
# ─────────────────────────────────────────────

class LGBMRanker:
    """Thin wrapper around lightgbm.LGBMClassifier for Layer-2 ranking."""

    def __init__(self) -> None:
        self._model: Any = None

    def fit(self, X: "pd.DataFrame", y: "pd.Series") -> None:  # type: ignore[name-defined]
        """Train the ranker on labelled signals."""
        import lightgbm as lgb  # type: ignore[import]

        self._model = lgb.LGBMClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=4,
            num_leaves=15,
            min_child_samples=10,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1,
        )
        self._model.fit(X[FEATURE_COLS], y)

    def predict_proba(self, X: "pd.DataFrame") -> "np.ndarray":  # type: ignore[name-defined]
        """Return P(win) for each row."""
        if self._model is None:
            raise RuntimeError("LGBMRanker not fitted — call fit() first")
        return self._model.predict_proba(X[FEATURE_COLS])[:, 1]

    def save(self, path: Path = _MODEL_PATH) -> None:
        import pickle  # noqa: PLC0415

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(self._model, fh)

    def load(self, path: Path = _MODEL_PATH) -> bool:
        import pickle  # noqa: PLC0415

        if not path.exists():
            return False
        with open(path, "rb") as fh:
            self._model = pickle.load(fh)  # noqa: S301
        return True


# ─────────────────────────────────────────────
# Walk-forward evaluation
# ─────────────────────────────────────────────

def _auc(y_true: list[int], y_score: list[float]) -> float:
    """Simple trapezoidal AUC without sklearn dependency."""
    from collections import defaultdict  # noqa: PLC0415

    try:
        from sklearn.metrics import roc_auc_score  # type: ignore[import]
        return float(roc_auc_score(y_true, y_score))
    except ImportError:
        pass

    # Fallback: Wilcoxon-Mann-Whitney estimate
    pos = [s for s, l in zip(y_score, y_true) if l == 1]
    neg = [s for s, l in zip(y_score, y_true) if l == 0]
    if not pos or not neg:
        return float("nan")
    n_correct = sum(1 for p in pos for n in neg if p > n)
    n_tie = sum(1 for p in pos for n in neg if p == n)
    return (n_correct + 0.5 * n_tie) / (len(pos) * len(neg))


def run_walkforward_eval(
    signals: list[dict[str, Any]] | None = None,
    n_folds: int = 12,
    train_months: int = 24,
    val_months: int = 6,
) -> dict[str, Any]:
    """Walk-forward AUC evaluation for the LightGBM ranker.

    Parameters
    ----------
    signals:
        List of signal dicts (with ``outcome`` field). If None, loaded
        from ``core.kpi_tracker._load_all_signals()``.
    n_folds:
        Number of walk-forward folds.
    train_months / val_months:
        Training and validation window sizes in months.

    Returns
    -------
    dict with ``fold_aucs``, ``avg_auc``, ``n_folds``, ``ts``.
    """
    if signals is None:
        try:
            from core.kpi_tracker import _load_all_signals  # type: ignore

            signals = _load_all_signals()
        except Exception as exc:
            return {"error": str(exc), "fold_aucs": [], "avg_auc": None}

    import pandas as pd  # noqa: PLC0415

    df = _signals_to_df(signals)
    # Keep only labelled rows
    df = df[df["label"] >= 0].copy()
    df = df.sort_values("ts").reset_index(drop=True)

    if len(df) < (train_months + val_months) * 5:
        return {
            "error": f"insufficient_data: {len(df)} labelled signals",
            "fold_aucs": [],
            "avg_auc": None,
        }

    # Convert timestamps to months since earliest
    t_min = df["ts"].min()
    df["month"] = ((df["ts"] - t_min) / (30 * 86400)).astype(int)
    max_month = df["month"].max()

    fold_aucs: list[float] = []
    for fold in range(n_folds):
        val_end = max_month - fold * val_months
        val_start = val_end - val_months
        train_end = val_start
        train_start = train_end - train_months

        train_df = df[(df["month"] >= train_start) & (df["month"] < train_end)]
        val_df = df[(df["month"] >= val_start) & (df["month"] < val_end)]

        if len(train_df) < 20 or len(val_df) < 5:
            continue
        if train_df["label"].nunique() < 2 or val_df["label"].nunique() < 2:
            continue

        ranker = LGBMRanker()
        try:
            ranker.fit(train_df, train_df["label"])
            proba = ranker.predict_proba(val_df)
            auc = _auc(val_df["label"].tolist(), proba.tolist())
            if auc == auc:  # not nan
                fold_aucs.append(round(auc, 4))
        except Exception as exc:
            logger.warning("lgbm_wf: fold %d failed: %s", fold, exc)

    avg_auc = round(sum(fold_aucs) / len(fold_aucs), 4) if fold_aucs else None

    result: dict[str, Any] = {
        "fold_aucs": fold_aucs,
        "avg_auc": avg_auc,
        "n_folds": len(fold_aucs),
        "ts": int(time.time()),
    }

    _WF_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_WF_RESULTS_PATH, "w") as fh:
        json.dump(result, fh, indent=2)
    logger.info("lgbm_wf: avg_auc=%.4f across %d folds", avg_auc or 0, len(fold_aucs))
    return result


# ─────────────────────────────────────────────
# Production predict (used by scanner)
# ─────────────────────────────────────────────

_ranker_instance: LGBMRanker | None = None
_ranker_lock = __import__("threading").Lock()


def get_ranker() -> LGBMRanker:
    """Return the global ranker instance, loading from disk if needed."""
    global _ranker_instance
    with _ranker_lock:
        if _ranker_instance is None:
            _ranker_instance = LGBMRanker()
            _ranker_instance.load()
        return _ranker_instance


def rank_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Re-rank signals using Layer-2 LightGBM ranker.

    Adds ``lgbm_score`` field to each signal and returns them sorted
    descending by that score. Falls back to original order if ranker
    is unavailable or not fitted.
    """
    try:
        ranker = get_ranker()
        if ranker._model is None:
            return signals

        import pandas as pd  # noqa: PLC0415

        df = _signals_to_df(signals)
        proba = ranker.predict_proba(df)
        for sig, p in zip(signals, proba):
            sig["lgbm_score"] = round(float(p), 4)
        return sorted(signals, key=lambda s: s.get("lgbm_score", 0.0), reverse=True)
    except Exception as exc:
        logger.debug("lgbm rank_signals failed (non-fatal): %s", exc)
        return signals
