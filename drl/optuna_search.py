"""Optuna hyperparameter search for FinPilot DRL agents.

Wraps the existing :class:`WalkForwardTrainer` with an Optuna study to
systematically explore the hyperparameter space.  Unlike external
implementations this module always uses the production
:class:`~drl.market_env.MarketEnv` so that optimised parameters are valid for
deployment.

Example::

    from drl.optuna_search import OptunaSearchConfig, run_optuna_search
    from drl.config import DEFAULT_CONFIG
    from drl.training import WalkForwardSplit

    results = run_optuna_search(
        env_config=DEFAULT_CONFIG,
        splits=my_splits,
        search_config=OptunaSearchConfig(n_trials=30),
    )
    print(results.best_params)
    print(results.best_metrics)
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from .config import (
    MarketEnvConfig,
    PilotShieldLimits,
    RewardWeights,
)
from .training import (
    EvaluationMetrics,
    TrainResult,
    WalkForwardConfig,
    WalkForwardSplit,
    WalkForwardTrainer,
)

try:
    import optuna  # type: ignore
    from optuna import Trial  # type: ignore

    HAS_OPTUNA = True
except Exception:
    optuna = None  # type: ignore
    Trial = None  # type: ignore
    HAS_OPTUNA = False

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

SUPPORTED_ALGORITHMS = ("PPO", "SAC", "TD3", "A2C")


@dataclass
class OptunaSearchConfig:
    """Configuration for the hyperparameter search."""

    # Study settings
    n_trials: int = 30
    timeout_seconds: float | None = None
    study_name: str = "finpilot-drl-hpo"
    direction: str = "maximize"
    sampler: str = "tpe"  # "tpe", "cmaes", "random"
    pruner: str = "median"  # "median", "hyperband", "none"

    # Objective metric
    objective_metric: str = "sharpe_ratio"  # "sharpe_ratio", "total_return", "average_reward"

    # Fixed training settings
    total_timesteps: int = 20_000
    seed: int | None = 42

    # Algorithm search space
    search_algorithm: bool = False  # include algorithm in search space
    algorithms: Sequence[str] = ("PPO", "SAC")

    # Parameter space bounds
    lr_range: tuple[float, float] = (1e-5, 1e-3)
    gamma_range: tuple[float, float] = (0.9, 0.999)
    gae_lambda_range: tuple[float, float] = (0.9, 0.99)
    ent_coef_range: tuple[float, float] = (1e-4, 0.1)
    vf_coef_range: tuple[float, float] = (0.1, 0.9)

    # Reward weight search
    search_reward_weights: bool = True
    pnl_weight_range: tuple[float, float] = (0.5, 2.0)
    drawdown_weight_range: tuple[float, float] = (0.5, 2.0)
    cost_weight_range: tuple[float, float] = (0.01, 0.5)
    leverage_weight_range: tuple[float, float] = (0.05, 0.5)
    regime_bonus_range: tuple[float, float] = (0.0, 0.2)

    # PilotShield search
    search_pilotshield: bool = False
    max_position_range: tuple[float, float] = (0.3, 1.0)
    risk_appetite_range: tuple[int, int] = (3, 8)

    # Callbacks
    show_progress_bar: bool = True
    verbose: bool = True


@dataclass
class OptunaSearchResult:
    """Results from the hyperparameter search."""

    best_params: dict[str, Any]
    best_value: float
    best_metrics: EvaluationMetrics
    best_train_result: TrainResult | None
    all_trials: list[dict[str, Any]]
    study_name: str
    n_trials_completed: int
    objective_metric: str

    def summary(self) -> str:
        """Human-readable summary of the search results."""
        lines = [
            "=" * 60,
            "  OPTUNA HİPERPARAMETRE ARAMA SONUÇLARI",
            "=" * 60,
            f"  Study: {self.study_name}",
            f"  Tamamlanan deneme: {self.n_trials_completed}",
            f"  Objektif metrik: {self.objective_metric}",
            f"  En iyi değer: {self.best_value:.4f}",
            "-" * 60,
            "  EN İYİ PARAMETRELER:",
        ]
        for k, v in sorted(self.best_params.items()):
            if isinstance(v, float):
                lines.append(f"    {k}: {v:.6f}")
            else:
                lines.append(f"    {k}: {v}")
        lines.append("-" * 60)
        if self.best_metrics:
            lines.extend(
                [
                    "  EN İYİ METRİKLER:",
                    f"    Sharpe Ratio: {self.best_metrics.sharpe_ratio:.4f}",
                    f"    Total Return: {self.best_metrics.total_return:.4f}",
                    f"    Max Drawdown: {self.best_metrics.max_drawdown:.4f}",
                    f"    Avg Reward:   {self.best_metrics.average_reward:.4f}",
                ]
            )
        lines.append("=" * 60)
        return "\n".join(lines)


# ============================================================================
# OBJECTIVE FUNCTION
# ============================================================================


def _create_objective(
    env_config: MarketEnvConfig,
    splits: Sequence[WalkForwardSplit],
    search_config: OptunaSearchConfig,
):
    """Create the Optuna objective function.

    The returned callable uses the **same** MarketEnv that production training
    uses, avoiding the Discrete-vs-Continuous mismatch found in external
    implementations.
    """

    def objective(trial: Trial) -> float:
        # --- Algorithm selection ---
        if search_config.search_algorithm:
            algorithm = trial.suggest_categorical("algorithm", list(search_config.algorithms))
        else:
            algorithm = search_config.algorithms[0]

        # --- Core hyperparameters ---
        learning_rate = trial.suggest_float(
            "learning_rate",
            search_config.lr_range[0],
            search_config.lr_range[1],
            log=True,
        )
        gamma = trial.suggest_float(
            "gamma",
            search_config.gamma_range[0],
            search_config.gamma_range[1],
        )

        # PPO/A2C specific
        gae_lambda = 0.95
        ent_coef = 0.001
        vf_coef = 0.5
        if algorithm in ("PPO", "A2C"):
            gae_lambda = trial.suggest_float(
                "gae_lambda",
                search_config.gae_lambda_range[0],
                search_config.gae_lambda_range[1],
            )
            ent_coef = trial.suggest_float(
                "ent_coef",
                search_config.ent_coef_range[0],
                search_config.ent_coef_range[1],
                log=True,
            )
            vf_coef = trial.suggest_float(
                "vf_coef",
                search_config.vf_coef_range[0],
                search_config.vf_coef_range[1],
            )

        # --- Reward weights ---
        reward_weights = env_config.reward
        if search_config.search_reward_weights:
            reward_weights = RewardWeights(
                pnl=trial.suggest_float(
                    "reward_pnl",
                    search_config.pnl_weight_range[0],
                    search_config.pnl_weight_range[1],
                ),
                drawdown=trial.suggest_float(
                    "reward_drawdown",
                    search_config.drawdown_weight_range[0],
                    search_config.drawdown_weight_range[1],
                ),
                cost=trial.suggest_float(
                    "reward_cost",
                    search_config.cost_weight_range[0],
                    search_config.cost_weight_range[1],
                ),
                leverage=trial.suggest_float(
                    "reward_leverage",
                    search_config.leverage_weight_range[0],
                    search_config.leverage_weight_range[1],
                ),
                regime_bonus=trial.suggest_float(
                    "reward_regime_bonus",
                    search_config.regime_bonus_range[0],
                    search_config.regime_bonus_range[1],
                ),
            )

        # --- PilotShield limits ---
        pilotshield = env_config.pilotshield
        if search_config.search_pilotshield:
            pilotshield = PilotShieldLimits(
                max_absolute_position=trial.suggest_float(
                    "max_absolute_position",
                    search_config.max_position_range[0],
                    search_config.max_position_range[1],
                ),
                max_leverage=env_config.pilotshield.max_leverage,
                risk_appetite=trial.suggest_int(
                    "risk_appetite",
                    search_config.risk_appetite_range[0],
                    search_config.risk_appetite_range[1],
                ),
                confidence_threshold=env_config.pilotshield.confidence_threshold,
                allow_shorting=env_config.pilotshield.allow_shorting,
            )

        # --- Build trial-specific configs ---
        trial_env_config = MarketEnvConfig(
            feature_specs=env_config.feature_specs,
            reward=reward_weights,
            transaction_costs=env_config.transaction_costs,
            pilotshield=pilotshield,
            schema_version=env_config.schema_version,
            target_dtype=env_config.target_dtype,
        )

        algo_config = WalkForwardConfig(
            algorithm=algorithm,
            total_timesteps=search_config.total_timesteps,
            learning_rate=learning_rate,
            gamma=gamma,
            gae_lambda=gae_lambda,
            ent_coef=ent_coef,
            vf_coef=vf_coef,
            seed=search_config.seed,
            track_mlflow=False,  # disable MLflow during search
        )

        # --- Train and evaluate ---
        try:
            trainer = WalkForwardTrainer(trial_env_config, algo_config)
            results = trainer.train(splits)

            if not results:
                return float("-inf")

            # Average metrics across all splits
            metric_values = []
            for r in results:
                val = getattr(r.metrics, search_config.objective_metric, None)
                if val is not None:
                    metric_values.append(float(val))

            if not metric_values:
                return float("-inf")

            objective_value = float(np.mean(metric_values))

            # Store metrics for later retrieval
            trial.set_user_attr(
                "avg_sharpe", float(np.mean([r.metrics.sharpe_ratio for r in results]))
            )
            trial.set_user_attr(
                "avg_return", float(np.mean([r.metrics.total_return for r in results]))
            )
            trial.set_user_attr(
                "avg_drawdown", float(np.mean([r.metrics.max_drawdown for r in results]))
            )
            trial.set_user_attr(
                "avg_reward", float(np.mean([r.metrics.average_reward for r in results]))
            )

            if search_config.verbose:
                logger.info(
                    f"Trial {trial.number}: {search_config.objective_metric}="
                    f"{objective_value:.4f} | algo={algorithm} lr={learning_rate:.6f} "
                    f"gamma={gamma:.4f}"
                )

            return objective_value

        except Exception as e:
            logger.warning(f"Trial {trial.number} failed: {e}")
            return float("-inf")

    return objective


# ============================================================================
# PUBLIC API
# ============================================================================


def run_optuna_search(
    env_config: MarketEnvConfig,
    splits: Sequence[WalkForwardSplit],
    search_config: OptunaSearchConfig | None = None,
) -> OptunaSearchResult:
    """Run an Optuna hyperparameter search over the FinPilot DRL training loop.

    Parameters
    ----------
    env_config:
        Base environment configuration. Reward weights and PilotShield limits
        may be overridden by the search if enabled in *search_config*.
    splits:
        Walk-forward data splits used for both training and evaluation during
        the search.
    search_config:
        Search parameters. Uses sensible defaults when ``None``.

    Returns
    -------
    OptunaSearchResult
        Contains the best parameters, metrics, and full trial history.
    """
    if not HAS_OPTUNA:
        raise ImportError(
            "Optuna is not installed. Run 'pip install optuna' to enable hyperparameter search."
        )

    if search_config is None:
        search_config = OptunaSearchConfig()

    # Create sampler
    if search_config.sampler == "tpe":
        sampler = optuna.samplers.TPESampler(seed=search_config.seed)
    elif search_config.sampler == "cmaes":
        sampler = optuna.samplers.CmaEsSampler(seed=search_config.seed)
    elif search_config.sampler == "random":
        sampler = optuna.samplers.RandomSampler(seed=search_config.seed)
    else:
        sampler = optuna.samplers.TPESampler(seed=search_config.seed)

    # Create pruner
    if search_config.pruner == "median":
        pruner = optuna.pruners.MedianPruner()
    elif search_config.pruner == "hyperband":
        pruner = optuna.pruners.HyperbandPruner()
    else:
        pruner = optuna.pruners.NopPruner()

    # Create study
    study = optuna.create_study(
        study_name=search_config.study_name,
        direction=search_config.direction,
        sampler=sampler,
        pruner=pruner,
    )

    # Create and run objective
    objective = _create_objective(env_config, splits, search_config)

    optuna.logging.set_verbosity(
        optuna.logging.WARNING if not search_config.verbose else optuna.logging.INFO
    )

    study.optimize(
        objective,
        n_trials=search_config.n_trials,
        timeout=search_config.timeout_seconds,
        show_progress_bar=search_config.show_progress_bar,
    )

    # Extract results
    best_trial = study.best_trial
    best_params = dict(best_trial.params)

    # Build best metrics from user attrs
    best_metrics = EvaluationMetrics(
        average_reward=best_trial.user_attrs.get("avg_reward", 0.0),
        sharpe_ratio=best_trial.user_attrs.get("avg_sharpe", 0.0),
        max_drawdown=best_trial.user_attrs.get("avg_drawdown", 0.0),
        total_return=best_trial.user_attrs.get("avg_return", 0.0),
    )

    # Collect all trial info
    all_trials = []
    for t in study.trials:
        trial_info: dict[str, Any] = {
            "number": t.number,
            "value": t.value,
            "params": dict(t.params),
            "state": str(t.state),
            "user_attrs": dict(t.user_attrs),
        }
        all_trials.append(trial_info)

    result = OptunaSearchResult(
        best_params=best_params,
        best_value=float(best_trial.value) if best_trial.value is not None else 0.0,
        best_metrics=best_metrics,
        best_train_result=None,
        all_trials=all_trials,
        study_name=search_config.study_name,
        n_trials_completed=len(study.trials),
        objective_metric=search_config.objective_metric,
    )

    logger.info(f"\n{result.summary()}")
    return result


def build_config_from_best(
    base_config: MarketEnvConfig,
    best_params: dict[str, Any],
) -> tuple[MarketEnvConfig, WalkForwardConfig]:
    """Reconstruct production-ready configs from Optuna's best parameters.

    Parameters
    ----------
    base_config:
        The original base configuration.
    best_params:
        ``OptunaSearchResult.best_params`` dictionary.

    Returns
    -------
    (MarketEnvConfig, WalkForwardConfig)
        Ready-to-use configuration pair for production training.
    """
    # Reward weights
    reward = RewardWeights(
        pnl=best_params.get("reward_pnl", base_config.reward.pnl),
        drawdown=best_params.get("reward_drawdown", base_config.reward.drawdown),
        cost=best_params.get("reward_cost", base_config.reward.cost),
        leverage=best_params.get("reward_leverage", base_config.reward.leverage),
        regime_bonus=best_params.get("reward_regime_bonus", base_config.reward.regime_bonus),
    )

    # PilotShield
    pilotshield = PilotShieldLimits(
        max_absolute_position=best_params.get(
            "max_absolute_position", base_config.pilotshield.max_absolute_position
        ),
        max_leverage=base_config.pilotshield.max_leverage,
        risk_appetite=best_params.get("risk_appetite", base_config.pilotshield.risk_appetite),
        confidence_threshold=base_config.pilotshield.confidence_threshold,
        allow_shorting=base_config.pilotshield.allow_shorting,
    )

    env_config = MarketEnvConfig(
        feature_specs=base_config.feature_specs,
        reward=reward,
        transaction_costs=base_config.transaction_costs,
        pilotshield=pilotshield,
        schema_version=base_config.schema_version,
        target_dtype=base_config.target_dtype,
    )

    algo_config = WalkForwardConfig(
        algorithm=best_params.get("algorithm", "PPO"),
        learning_rate=best_params.get("learning_rate", 3e-4),
        gamma=best_params.get("gamma", 0.99),
        gae_lambda=best_params.get("gae_lambda", 0.95),
        ent_coef=best_params.get("ent_coef", 0.001),
        vf_coef=best_params.get("vf_coef", 0.5),
    )

    return env_config, algo_config


__all__ = [
    "OptunaSearchConfig",
    "OptunaSearchResult",
    "run_optuna_search",
    "build_config_from_best",
    "SUPPORTED_ALGORITHMS",
]
