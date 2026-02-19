"""Feature importance utilities based on SHAP analyses.

The helpers in this module are designed to operate on walk-forward training
results without introducing hard dependencies.  Optional packages such as
``scikit-learn`` and ``shap`` are imported lazily; when they are missing the
caller receives a descriptive ``RuntimeError``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..config import MarketEnvConfig
from ..training import TrainResult


@dataclass
class PolicyDataset:
    """Container holding flattened feature/action observations."""

    features: np.ndarray
    feature_names: Sequence[str]
    actions: np.ndarray
    rewards: np.ndarray
    regimes: Sequence[str]
    timestamps: Sequence[str | None]

    def sample(self, size: int, *, seed: int | None = None) -> PolicyDataset:
        if size >= len(self.features):
            return self
        rng = np.random.default_rng(seed)
        indices = rng.choice(len(self.features), size=size, replace=False)
        return PolicyDataset(
            features=self.features[indices],
            feature_names=self.feature_names,
            actions=self.actions[indices],
            rewards=self.rewards[indices],
            regimes=[self.regimes[i] for i in indices],
            timestamps=[self.timestamps[i] for i in indices],
        )


@dataclass
class FeatureImportanceSummary:
    """Aggregated feature importance report."""

    global_importance: pd.DataFrame
    regime_importance: dict[str, pd.DataFrame]
    shap_values: np.ndarray
    base_values: np.ndarray


def collect_policy_dataset(
    results: Sequence[TrainResult],
    config: MarketEnvConfig,
    *,
    include_rewards: bool = True,
    min_reward: float | None = None,
) -> PolicyDataset:
    """Flatten walk-forward histories into a policy dataset."""

    feature_names = list(config.feature_columns)
    feature_rows: list[np.ndarray] = []
    actions: list[float] = []
    rewards: list[float] = []
    regimes: list[str] = []
    timestamps: list[str | None] = []

    for result in results:
        for step in result.history:
            feature_vector = step.get("features")
            if feature_vector is None:
                continue
            reward = float(step.get("reward", 0.0))
            if min_reward is not None and reward < min_reward:
                continue
            feature_rows.append(np.asarray(feature_vector, dtype=float))
            actions.append(float(step.get("position", 0.0)))
            rewards.append(reward if include_rewards else 0.0)
            regimes.append(str(step.get("regime", "unknown")))
            timestamps.append(step.get("timestamp"))

    if not feature_rows:
        raise ValueError("No feature observations were found in the training results.")

    features = np.vstack(feature_rows)
    if features.shape[1] != len(feature_names):
        raise ValueError(
            "Feature dimensionality mismatch between history records and configuration."
        )

    return PolicyDataset(
        features=features,
        feature_names=feature_names,
        actions=np.asarray(actions, dtype=float),
        rewards=np.asarray(rewards, dtype=float),
        regimes=regimes,
        timestamps=timestamps,
    )


def fit_surrogate_policy(
    dataset: PolicyDataset,
    *,
    n_estimators: int = 300,
    max_depth: int | None = None,
    random_state: int = 42,
):
    """Train a tree-based surrogate model approximating the policy.

    Returns the fitted estimator. Requires ``scikit-learn`` to be installed.
    """

    try:  # Imported lazily to keep dependency optional
        from sklearn.ensemble import RandomForestRegressor  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "scikit-learn is required to train the surrogate policy model. "
            "Install it via 'pip install scikit-learn'."
        ) from exc

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
    )
    model.fit(dataset.features, dataset.actions)
    return model


def compute_shap_summary(
    model,
    dataset: PolicyDataset,
    *,
    sample_size: int = 1024,
    seed: int | None = 42,
) -> FeatureImportanceSummary:
    """Compute global and regime-specific SHAP importances."""

    try:
        import shap  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "shap package is required to compute feature importance. "
            "Install it via 'pip install shap'."
        ) from exc

    sampled = dataset.sample(sample_size, seed=seed)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(sampled.features)

    if isinstance(shap_values, list):  # multi-output case
        shap_values = shap_values[0]

    mean_abs = np.abs(shap_values).mean(axis=0)
    global_df = (
        pd.DataFrame({"feature": sampled.feature_names, "importance": mean_abs})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )

    regime_importance: dict[str, pd.DataFrame] = {}
    regimes = np.asarray(sampled.regimes)
    for regime in sorted(set(regimes)):
        mask = regimes == regime
        if not mask.any():
            continue
        importance = np.abs(shap_values[mask]).mean(axis=0)
        regime_importance[regime] = (
            pd.DataFrame({"feature": sampled.feature_names, "importance": importance})
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )

    base_values = np.atleast_1d(getattr(explainer, "expected_value", np.array([])))

    return FeatureImportanceSummary(
        global_importance=global_df,
        regime_importance=regime_importance,
        shap_values=shap_values,
        base_values=base_values,
    )
