"""Meta-Labeler Training Script (Faz 1, P2)

Trains a logistic regression meta-labeler on DB-resolved signals.
The meta-labeler predicts P(win | features) given that the primary
scanner already issued a BUY signal — this is the "meta-labeling" step
from López de Prado's Advances in Financial Machine Learning (ch. 3).

Features:
    - score_norm     : min(score / 18.0, 1.0)  — primary model strength
    - regime         : 1.0 = Bull (price > EMA200), 0.0 = Bear
    - rr_norm        : min(risk_reward, 5.0) / 5.0  — quality of setup
    - regime_x_score : interaction term regime × score_norm

Output:
    data/meta_labeler.json  — intercept + coefficients + feature names + eval metrics

Usage:
    python scripts/fit_meta_labeler.py

The JSON output is loaded by core/calibration.py's calibrated_probability_ml().
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "finpilot.db"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "meta_labeler.json"
MIN_SAMPLES = 200  # Minimum resolved signals to train


def _load_data() -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT id, score, payload_json, resolved_pct_barrier, resolved_status_barrier
        FROM signals_archive
        WHERE resolved_pct_barrier IS NOT NULL
          AND resolved_status_barrier IN ('resolved_win', 'resolved_loss', 'expired_win', 'expired_loss')
        """
    ).fetchall()
    con.close()
    return rows


def _parse_features(rows) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Extract feature matrix X and label vector y from DB rows."""
    records = []
    for row in rows:
        try:
            payload = json.loads(row["payload_json"]) if row["payload_json"] else {}
        except Exception:
            payload = {}

        score = float(row["score"] or 0)
        regime_raw = payload.get("regime", None)
        rr_raw = payload.get("risk_reward", None)

        # Normalize features
        score_norm = min(score / 18.0, 1.0)
        if regime_raw is None:
            regime = 0.5  # unknown → neutral
        else:
            regime = 1.0 if regime_raw in (True, 1, "True", "true", "1") else 0.0
        rr_norm = min(float(rr_raw or 0), 5.0) / 5.0

        win = 1 if row["resolved_status_barrier"] in ("resolved_win", "expired_win") else 0
        records.append(
            {
                "score_norm": score_norm,
                "regime": regime,
                "rr_norm": rr_norm,
                "regime_x_score": regime * score_norm,
                "win": win,
            }
        )

    df = pd.DataFrame(records)
    feature_names = ["score_norm", "regime", "rr_norm", "regime_x_score"]
    X = df[feature_names].values.astype(float)
    y = df["win"].values.astype(int)
    return X, y, feature_names


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _brier(y_true: np.ndarray, p_pred: np.ndarray) -> float:
    return float(np.mean((p_pred - y_true) ** 2))


def main() -> None:
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import roc_auc_score
        from sklearn.model_selection import StratifiedKFold
    except ImportError:
        print("ERROR: scikit-learn is required for training. pip install scikit-learn")
        return

    rows = _load_data()
    print(f"Loaded {len(rows):,} barrier-resolved signals from DB")

    if len(rows) < MIN_SAMPLES:
        print(f"Only {len(rows)} signals — need {MIN_SAMPLES}. Aborting.")
        return

    X, y, feature_names = _parse_features(rows)
    print(f"Features: {feature_names}, n={len(y)}, win_rate={y.mean():.3f}")

    # ── Cross-validation (5-fold stratified) ──────────────────────────────────
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_brier, cv_auc = [], []
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        clf = LogisticRegression(C=1.0, max_iter=300, solver="lbfgs")
        clf.fit(X[train_idx], y[train_idx])
        p_val = clf.predict_proba(X[val_idx])[:, 1]
        cv_brier.append(_brier(y[val_idx], p_val))
        try:
            cv_auc.append(roc_auc_score(y[val_idx], p_val))
        except Exception:
            cv_auc.append(float("nan"))
        print(f"  Fold {fold+1}: brier={cv_brier[-1]:.4f} auc={cv_auc[-1]:.4f}")

    avg_brier = float(np.nanmean(cv_brier))
    avg_auc = float(np.nanmean(cv_auc))
    print(
        f"\nCV avg brier={avg_brier:.4f} (baseline={y.mean()*(1-y.mean()):.4f}) auc={avg_auc:.4f}"
    )

    # Band-baseline Brier for comparison
    band_brier = float(y.mean() * (1 - y.mean()))
    lift = (band_brier - avg_brier) / band_brier
    print(f"Brier lift over naive baseline: {lift*100:.2f}%")

    # ── Final model fit on all data ───────────────────────────────────────────
    clf_final = LogisticRegression(C=1.0, max_iter=300, solver="lbfgs")
    clf_final.fit(X, y)

    coef = clf_final.coef_[0].tolist()
    intercept = float(clf_final.intercept_[0])

    # Manual predict to verify consistency
    p_train = _sigmoid(X @ np.array(coef) + intercept)
    train_brier = _brier(y, p_train)
    print(f"Final model train brier={train_brier:.4f}")
    print(f"Intercept={intercept:.4f}")
    for fname, c in zip(feature_names, coef, strict=False):
        print(f"  {fname}: {c:+.4f}")

    # Feature importance (|coefficient| relative)
    abs_coef = [abs(c) for c in coef]
    total = sum(abs_coef) or 1.0
    importance = {
        fname: round(abs_c / total, 4)
        for fname, abs_c in zip(feature_names, abs_coef, strict=False)
    }

    result = {
        "model_type": "LogisticRegression",
        "feature_names": feature_names,
        "intercept": round(intercept, 6),
        "coefficients": [round(c, 6) for c in coef],
        "feature_importance": importance,
        "n_samples": len(y),
        "win_rate": round(float(y.mean()), 4),
        "cv_brier_avg": round(avg_brier, 4),
        "cv_auc_avg": round(avg_auc, 4),
        "naive_brier": round(band_brier, 4),
        "brier_lift_pct": round(lift * 100, 2),
        "fitted_at": pd.Timestamp.now().isoformat(timespec="seconds"),
        "min_samples_to_retrain": MIN_SAMPLES,
        "verdict": (
            "USEFUL"
            if lift > 0.01 and avg_auc > 0.52
            else "MARGINAL"
            if lift >= 0
            else "NO_IMPROVEMENT"
        ),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved → {OUT_PATH}")
    print(f"Verdict: {result['verdict']}")


if __name__ == "__main__":
    main()
