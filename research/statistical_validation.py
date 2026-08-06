"""Research-only statistical validation primitives.

The functions in this module operate on already materialized return arrays.
They do not read production state, select a live model, or promote a score.
Missing observations are represented by ``NaN`` and are never replaced with a
synthetic return.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np
from scipy.stats import norm, t


def _valid(values: np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=float)[np.isfinite(values)]


def _mean(values: np.ndarray) -> float:
    valid = _valid(values)
    return float(np.mean(valid)) if valid.size else float("nan")


def _block_indices(n: int, block_size: int, rng: np.random.Generator) -> np.ndarray:
    starts = rng.integers(0, n, size=max(1, int(np.ceil(n / block_size))))
    indices = np.concatenate([np.mod(start + np.arange(block_size), n) for start in starts])
    return indices[:n]


def newey_west_mean(values: np.ndarray, max_lag: int | None = None) -> dict[str, float | int]:
    """HAC/Newey-West inference for a mean return."""
    clean = _valid(values)
    n = clean.size
    if n < 3:
        return {
            "n": int(n),
            "mean": float("nan"),
            "se": float("nan"),
            "t": float("nan"),
            "p": float("nan"),
        }
    centered = clean - np.mean(clean)
    lag = min(max_lag if max_lag is not None else int(np.sqrt(n)), n - 1)
    gamma0 = float(np.dot(centered, centered) / n)
    variance = gamma0
    for k in range(1, lag + 1):
        gamma = float(np.dot(centered[k:], centered[:-k]) / n)
        variance += 2.0 * (1.0 - k / (lag + 1.0)) * gamma
    se = float(np.sqrt(max(variance, 0.0) / n))
    statistic = float(np.mean(clean) / se) if se > 0 else float("nan")
    p_value = (
        float(2.0 * t.sf(abs(statistic), df=n - 1)) if np.isfinite(statistic) else float("nan")
    )
    return {
        "n": int(n),
        "lag": int(lag),
        "mean": float(np.mean(clean)),
        "se": se,
        "t": statistic,
        "p": p_value,
    }


def benjamini_hochberg(p_values: dict[str, float], alpha: float = 0.05) -> dict[str, Any]:
    """Apply program-wide Benjamini-Hochberg FDR correction."""
    finite = sorted((name, value) for name, value in p_values.items() if np.isfinite(value))
    m = len(finite)
    adjusted: dict[str, float] = {}
    for rank, (name, value) in enumerate(finite, start=1):
        adjusted[name] = min(1.0, value * m / rank)
    discoveries = [name for name, value in adjusted.items() if value <= alpha]
    return {
        "alpha": alpha,
        "tested": m,
        "adjusted_p": adjusted,
        "discoveries": discoveries,
    }


def deflated_sharpe(values: np.ndarray, trials: int, block_size: int = 5) -> dict[str, float | int]:
    """Estimate a deflated Sharpe ratio against a multiple-testing hurdle."""
    clean = _valid(values)
    n = clean.size
    if n < 3 or trials < 1:
        return {"n": int(n), "trials": int(trials), "sharpe": float("nan"), "dsr": float("nan")}
    std = float(np.std(clean, ddof=1))
    sharpe = float(np.mean(clean) / std * np.sqrt(252.0)) if std > 0 else float("nan")
    skew = float(np.mean(((clean - np.mean(clean)) / std) ** 3)) if std > 0 else 0.0
    kurtosis = float(np.mean(((clean - np.mean(clean)) / std) ** 4)) if std > 0 else 3.0
    expected_max = float(norm.ppf(1.0 - 1.0 / max(trials, 2))) * np.sqrt(252.0 / n)
    denominator = np.sqrt(max(1.0 - skew * sharpe + (kurtosis - 1.0) * sharpe**2 / 4.0, 1e-12) / n)
    dsr = float(norm.cdf((sharpe - expected_max) / denominator))
    return {
        "n": int(n),
        "trials": int(trials),
        "block_size": int(block_size),
        "sharpe": sharpe,
        "expected_max_sharpe": expected_max,
        "dsr": dsr,
    }


def cpcv_pbo(
    returns: np.ndarray,
    dates: list[str],
    n_groups: int = 6,
    test_groups: int = 2,
    purge_days: int = 1,
) -> dict[str, Any]:
    """Run combinatorial purged CV and estimate probability of overfitting.

    ``returns`` is rows-by-candidate with NaN for rows where a candidate did
    not select an observation. Train winners are scored on held-out groups.
    """
    matrix = np.asarray(returns, dtype=float)
    if matrix.ndim != 2 or len(dates) != matrix.shape[0]:
        raise ValueError("returns must be a 2D matrix aligned with dates")
    unique_dates = sorted(set(dates))
    groups = np.array_split(np.array(unique_dates, dtype=object), n_groups)
    paths: list[dict[str, Any]] = []
    overfit = 0
    for test_choice in combinations(range(len(groups)), test_groups):
        test_dates = {date for index in test_choice for date in groups[index]}
        test_date_values = sorted(test_dates)
        purge_dates = set()
        for date_value in unique_dates:
            if any(
                abs(unique_dates.index(date_value) - unique_dates.index(test_date)) <= purge_days
                for test_date in test_date_values
            ):
                purge_dates.add(date_value)
        train_mask = np.array(
            [(date not in test_dates and date not in purge_dates) for date in dates]
        )
        test_mask = np.array([date in test_dates for date in dates])
        train_values = np.where(train_mask[:, None], matrix, np.nan)
        test_values = np.where(test_mask[:, None], matrix, np.nan)
        train_counts = np.isfinite(train_values).sum(axis=0)
        test_counts = np.isfinite(test_values).sum(axis=0)
        train_means = np.divide(
            np.nansum(train_values, axis=0),
            train_counts,
            out=np.full(matrix.shape[1], np.nan),
            where=train_counts > 0,
        )
        test_means = np.divide(
            np.nansum(test_values, axis=0),
            test_counts,
            out=np.full(matrix.shape[1], np.nan),
            where=test_counts > 0,
        )
        if not np.isfinite(train_means).any():
            continue
        winner = int(np.nanargmax(train_means))
        test_rank = (
            float(np.mean(test_means <= test_means[winner]))
            if np.isfinite(test_means[winner])
            else float("nan")
        )
        if np.isfinite(test_rank) and test_rank < 0.5:
            overfit += 1
        paths.append(
            {
                "test_groups": list(test_choice),
                "winner": winner,
                "train_mean": float(train_means[winner]),
                "test_mean": float(test_means[winner]),
                "test_percentile": test_rank,
            }
        )
    return {
        "n_observations": int(matrix.shape[0]),
        "n_candidates": int(matrix.shape[1]),
        "n_groups": int(n_groups),
        "test_groups": int(test_groups),
        "purge_days": int(purge_days),
        "paths": paths,
        "pbo": float(overfit / len(paths)) if paths else float("nan"),
    }


def _bootstrap_max_statistic(
    matrix: np.ndarray,
    repetitions: int,
    block_size: int,
    seed: int,
) -> tuple[float, float, list[float]]:
    values = np.nan_to_num(np.asarray(matrix, dtype=float), nan=0.0)
    centered = values - np.mean(values, axis=0)
    observed = float(np.max(np.mean(values, axis=0)))
    rng = np.random.default_rng(seed)
    bootstrap_max = []
    for _ in range(repetitions):
        indices = _block_indices(values.shape[0], block_size, rng)
        bootstrap_max.append(float(np.max(np.mean(centered[indices], axis=0))))
    p_value = float(
        (1 + sum(value >= observed for value in bootstrap_max)) / (len(bootstrap_max) + 1)
    )
    return observed, p_value, bootstrap_max


def white_reality_check(
    returns: np.ndarray,
    repetitions: int = 200,
    block_size: int = 5,
    seed: int = 42,
) -> dict[str, Any]:
    """Block-bootstrap White Reality Check on candidate excess returns."""
    observed, p_value, bootstrap = _bootstrap_max_statistic(returns, repetitions, block_size, seed)
    return {
        "observed_max_mean": observed,
        "p": p_value,
        "repetitions": repetitions,
        "block_size": block_size,
        "seed": seed,
        "bootstrap_max_mean": float(np.mean(bootstrap)) if bootstrap else float("nan"),
    }


def hansen_spa(
    returns: np.ndarray,
    repetitions: int = 200,
    block_size: int = 5,
    seed: int = 43,
) -> dict[str, Any]:
    """Positive-part block-bootstrap SPA-style statistic."""
    values = np.nan_to_num(np.asarray(returns, dtype=float), nan=0.0)
    centered = values - np.mean(values, axis=0)
    observed = float(np.max(np.maximum(np.mean(values, axis=0), 0.0)))
    rng = np.random.default_rng(seed)
    bootstrap = []
    for _ in range(repetitions):
        indices = _block_indices(values.shape[0], block_size, rng)
        bootstrap.append(float(np.max(np.maximum(np.mean(centered[indices], axis=0), 0.0))))
    p_value = float((1 + sum(value >= observed for value in bootstrap)) / (len(bootstrap) + 1))
    return {
        "observed_positive_max_mean": observed,
        "p": p_value,
        "repetitions": repetitions,
        "block_size": block_size,
        "seed": seed,
    }


def gaussian_hmm_two_state(values: np.ndarray, iterations: int = 40) -> dict[str, Any]:
    """Fit a small two-state Gaussian HMM without production dependencies."""
    observations = _valid(values)
    if observations.size < 20:
        return {"status": "insufficient_data", "n": int(observations.size)}
    means = np.array(
        [np.quantile(observations, 0.25), np.quantile(observations, 0.75)], dtype=float
    )
    variances = np.full(2, max(float(np.var(observations)), 1e-8))
    transition = np.array([[0.95, 0.05], [0.05, 0.95]], dtype=float)
    initial = np.array([0.5, 0.5], dtype=float)
    for _ in range(iterations):
        emission = np.exp(-0.5 * (observations[:, None] - means) ** 2 / variances) / np.sqrt(
            2 * np.pi * variances
        )
        forward = np.zeros_like(emission)
        scales = np.zeros(observations.size)
        forward[0] = initial * emission[0]
        scales[0] = max(np.sum(forward[0]), 1e-300)
        forward[0] /= scales[0]
        for index in range(1, observations.size):
            forward[index] = emission[index] * (forward[index - 1] @ transition)
            scales[index] = max(np.sum(forward[index]), 1e-300)
            forward[index] /= scales[index]
        backward = np.ones_like(emission)
        for index in range(observations.size - 2, -1, -1):
            backward[index] = transition @ (emission[index + 1] * backward[index + 1])
            backward[index] /= max(scales[index + 1], 1e-300)
        posterior = forward * backward
        posterior /= np.maximum(posterior.sum(axis=1, keepdims=True), 1e-300)
        weights = posterior.sum(axis=0)
        means = (posterior * observations[:, None]).sum(axis=0) / np.maximum(weights, 1e-300)
        variances = (posterior * (observations[:, None] - means) ** 2).sum(axis=0) / np.maximum(
            weights, 1e-300
        )
        variances = np.maximum(variances, 1e-8)
        initial = posterior[0]
        transitions = np.zeros((2, 2))
        for index in range(observations.size - 1):
            pair = (
                forward[index, :, None]
                * transition
                * emission[index + 1][None, :]
                * backward[index + 1][None, :]
            )
            transitions += pair / max(pair.sum(), 1e-300)
        transition = transitions / np.maximum(transitions.sum(axis=1, keepdims=True), 1e-300)
    states = np.argmax(posterior, axis=1)
    return {
        "status": "ok",
        "n": int(observations.size),
        "iterations": int(iterations),
        "means": means.tolist(),
        "volatility": np.sqrt(variances).tolist(),
        "transition": transition.tolist(),
        "state_counts": np.bincount(states, minlength=2).tolist(),
        "state_sequence_tail": states[-20:].tolist(),
    }
