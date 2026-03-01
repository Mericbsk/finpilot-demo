"""Walk-forward training harness for FinPilot's DRL agents.

The implementation keeps dependencies optional: Stable-Baselines3, Optuna, and
MLflow are imported lazily so that the dashboard can run without them.  When the
libraries are unavailable the public API raises a descriptive error instructing
users how to install the extra requirements.
"""

from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING

import numpy as np

from .config import MarketEnvConfig
from .feature_pipeline import FeaturePipeline
from .market_env import EpisodeData, MarketEnv
from .observability import (
    MLflowSettings,
    configure_mlflow,
    mlflow_log_artifact,
    mlflow_log_dict,
    mlflow_log_metrics,
    mlflow_log_params,
    mlflow_run,
    record_inference_event,
)
from .persistence import (
    FeaturePipelineArtifact,
    build_artifact,
    load_artifact,
    restore_pipeline,
    save_artifact,
)

try:  # pragma: no cover - optional heavy dependency
    from stable_baselines3 import A2C, PPO, SAC, TD3  # type: ignore
    from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack  # type: ignore
except Exception:  # pragma: no cover - missing SB3 is handled at runtime
    PPO = None
    SAC = None
    TD3 = None
    A2C = None
    DummyVecEnv = None
    VecFrameStack = None

if TYPE_CHECKING:  # pragma: no cover - for static type checking only
    import mlflow  # type: ignore
else:
    mlflow_spec = importlib.util.find_spec("mlflow")
    mlflow = importlib.import_module("mlflow") if mlflow_spec else None  # type: ignore


@dataclass
class WalkForwardSplit:
    """Represents a single walk-forward window."""

    train: EpisodeData
    test: EpisodeData
    label: str


@dataclass
class WalkForwardConfig:
    algorithm: str = "PPO"
    total_timesteps: int = 50_000
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    ent_coef: float = 0.001
    vf_coef: float = 0.5
    seed: int | None = None
    track_mlflow: bool = False
    mlflow_experiment: str = "FinPilot-DRL"
    mlflow_tracking_uri: str | None = None
    mlflow_tags: dict[str, str] = field(default_factory=dict)
    feature_contract_path: str | None = None
    save_pipeline_artifacts: bool = False
    pipeline_artifact_dir: str | None = None
    load_pipeline_artifact: str | None = None
    allow_pipeline_signature_mismatch: bool = False
    n_stack: int = 4  # Sprint 18: observation stacking — agent sees last N timesteps


@dataclass
class EvaluationMetrics:
    average_reward: float
    sharpe_ratio: float
    max_drawdown: float
    total_return: float


@dataclass
class TrainResult:
    split: WalkForwardSplit
    metrics: EvaluationMetrics
    model_path: str | None
    history: list[dict[str, float | str]] = field(default_factory=list)
    pipeline_artifact_path: str | None = None


class WalkForwardTrainer:
    """Coordinates the RL training loop across walk-forward windows."""

    def __init__(self, env_config: MarketEnvConfig, algo_config: WalkForwardConfig):
        self.env_config = env_config
        self.algo_config = algo_config

        self._loaded_artifact: FeaturePipelineArtifact | None = None
        if self.algo_config.load_pipeline_artifact:
            artifact_path = Path(self.algo_config.load_pipeline_artifact).expanduser()
            self._loaded_artifact = load_artifact(artifact_path)

        self._artifact_dir: Path | None = None
        if self.algo_config.save_pipeline_artifacts:
            target_dir = (
                Path(self.algo_config.pipeline_artifact_dir).expanduser()
                if self.algo_config.pipeline_artifact_dir
                else Path.cwd() / "artifacts"
            )
            target_dir.mkdir(parents=True, exist_ok=True)
            self._artifact_dir = target_dir

        _SUPPORTED = {"PPO", "SAC", "TD3", "A2C"}
        if self.algo_config.algorithm not in _SUPPORTED:
            raise ValueError(f"algorithm must be one of {_SUPPORTED}")

        self._mlflow_settings = MLflowSettings(
            enabled=self.algo_config.track_mlflow,
            tracking_uri=self.algo_config.mlflow_tracking_uri,
            experiment=self.algo_config.mlflow_experiment,
            tags=dict(self.algo_config.mlflow_tags),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def train(self, splits: Sequence[WalkForwardSplit]) -> list[TrainResult]:
        """Execute walk-forward training for the supplied splits."""

        results: list[TrainResult] = []
        configure_mlflow(self._mlflow_settings)
        common_params = dict(
            algorithm=self.algo_config.algorithm,
            total_timesteps=self.algo_config.total_timesteps,
            learning_rate=self.algo_config.learning_rate,
            gamma=self.algo_config.gamma,
            gae_lambda=self.algo_config.gae_lambda,
            ent_coef=self.algo_config.ent_coef,
            vf_coef=self.algo_config.vf_coef,
            seed=self.algo_config.seed,
        )
        for split in splits:
            pipeline = FeaturePipeline(self.env_config)
            if self._loaded_artifact is not None:
                restore_pipeline(
                    pipeline,
                    self._loaded_artifact,
                    allow_signature_mismatch=self.algo_config.allow_pipeline_signature_mismatch,
                )
            else:
                pipeline.fit(split.train.features)

            model = self._create_model(pipeline, split.train)
            history = self._evaluate(model, pipeline, split.test)
            metrics = self._compute_metrics(history)
            artifact_payload = build_artifact(pipeline)

            model_path = None
            with mlflow_run(
                self._mlflow_settings,
                run_name=f"walkforward-{split.label}",
                tags={"split": split.label, **self._mlflow_settings.tags},
                params={**common_params, "split_label": split.label},
            ) as run:
                if run is not None and self.algo_config.track_mlflow and mlflow is not None:
                    mlflow_log_metrics(
                        {
                            "avg_reward": metrics.average_reward,
                            "sharpe": metrics.sharpe_ratio,
                            "max_drawdown": metrics.max_drawdown,
                            "total_return": metrics.total_return,
                        }
                    )
                    mlflow_log_params(
                        {
                            "rows_test": len(split.test.features.data),
                            "rows_train": len(split.train.features.data),
                        }
                    )
                    mlflow_log_dict(
                        artifact_payload.to_dict(),
                        f"feature_pipeline/{split.label}_artifact.json",
                    )
                    if self.algo_config.feature_contract_path:
                        contract_path = Path(self.algo_config.feature_contract_path).expanduser()
                        if contract_path.exists():
                            mlflow_log_artifact(contract_path, artifact_path="feature_contract")
                    model_path = self._log_to_mlflow(model, split.label)

            artifact_path: str | None = None
            if self._artifact_dir is not None:
                destination = self._artifact_dir / f"{split.label}_pipeline.json"
                save_artifact(artifact_payload, destination)
                artifact_path = str(destination.resolve())

            results.append(
                TrainResult(
                    split=split,
                    metrics=metrics,
                    model_path=model_path,
                    history=history,
                    pipeline_artifact_path=artifact_path,
                )
            )
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _create_model(
        self,
        pipeline: FeaturePipeline,
        split: EpisodeData,
        callbacks: list | None = None,
    ):
        if PPO is None or DummyVecEnv is None:
            raise ImportError(
                "stable-baselines3 is not installed. Run 'pip install stable-baselines3'"
            )

        def _make_env():
            return MarketEnv(split, pipeline, self.env_config)

        vec_env = DummyVecEnv([_make_env])

        # Sprint 18: observation stacking — gives the agent temporal context
        # Without stacking the MlpPolicy sees only 1 timestep (no momentum sense)
        n_stack = self.algo_config.n_stack
        if n_stack > 1 and VecFrameStack is not None:
            vec_env = VecFrameStack(vec_env, n_stack=n_stack)
            logger.info("Observation stacking: n_stack=%d (obs_dim: %d → %d)",
                        n_stack,
                        len(self.env_config.feature_columns),
                        len(self.env_config.feature_columns) * n_stack)

        algo = self.algo_config.algorithm.upper()
        common = dict(
            learning_rate=self.algo_config.learning_rate,
            gamma=self.algo_config.gamma,
        )
        on_policy_extras = dict(
            gae_lambda=self.algo_config.gae_lambda,
            ent_coef=self.algo_config.ent_coef,
            vf_coef=self.algo_config.vf_coef,
        )

        if algo == "PPO":
            model = PPO(
                "MlpPolicy",
                vec_env,
                verbose=0,
                seed=self.algo_config.seed,
                **common,
                **on_policy_extras,
            )
        elif algo == "A2C":
            if A2C is None:
                raise ImportError("stable-baselines3 A2C not available.")
            model = A2C(
                "MlpPolicy",
                vec_env,
                verbose=0,
                seed=self.algo_config.seed,
                **common,
                **on_policy_extras,
            )
        elif algo == "SAC":
            if SAC is None:
                raise ImportError(
                    "stable-baselines3 SAC extras required. "
                    "Install 'pip install stable-baselines3[extra]'"
                )
            model = SAC(
                "MlpPolicy",
                vec_env,
                verbose=0,
                seed=self.algo_config.seed,
                **common,
            )
        elif algo == "TD3":
            if TD3 is None:
                raise ImportError(
                    "stable-baselines3 TD3 extras required. "
                    "Install 'pip install stable-baselines3[extra]'"
                )
            model = TD3(
                "MlpPolicy",
                vec_env,
                verbose=0,
                seed=self.algo_config.seed,
                **common,
            )
        else:
            raise ValueError(f"Unsupported algorithm: {algo}")

        model.learn(
            total_timesteps=self.algo_config.total_timesteps,
            callback=callbacks,
        )
        return model

    def _evaluate(
        self, model, pipeline: FeaturePipeline, split: EpisodeData
    ) -> list[dict[str, float | str]]:
        eval_env = MarketEnv(split, pipeline, self.env_config)
        obs, _info = eval_env.reset()
        done = False
        while not done:
            infer_started = perf_counter()
            action, _state = model.predict(obs, deterministic=True)
            latency = perf_counter() - infer_started
            record_inference_event(
                model=self.algo_config.algorithm.upper(),
                latency_seconds=latency,
            )
            step_result = eval_env.step(action)
            if len(step_result) == 5:
                obs, _reward, terminated, truncated, _info = step_result
                done = bool(terminated or truncated)
            else:
                obs, _reward, done, _info = step_result
                done = bool(done)
            if done:
                break
        return eval_env.get_history()

    def _compute_metrics(self, history: list[dict[str, float | str]]) -> EvaluationMetrics:
        if not history:
            return EvaluationMetrics(0.0, 0.0, 0.0, 0.0)
        pnl = np.array(
            [
                float(entry.get("pnl", 0.0)) if isinstance(entry.get("pnl"), (int, float)) else 0.0
                for entry in history
            ]
        )
        rewards = np.array(
            [
                (
                    float(entry.get("reward", 0.0))
                    if isinstance(entry.get("reward"), (int, float))
                    else 0.0
                )
                for entry in history
            ]
        )
        equity = np.array(
            [
                (
                    float(entry.get("equity", 1.0))
                    if isinstance(entry.get("equity"), (int, float))
                    else 1.0
                )
                for entry in history
            ]
        )
        total_return = float(equity[-1] - equity[0]) if equity.size > 1 else float(np.sum(pnl))

        pnl_std = float(np.std(pnl)) or 1e-6
        sharpe = float(np.mean(pnl) / pnl_std)
        max_equity = np.maximum.accumulate(equity)
        drawdowns = (max_equity - equity) / max_equity
        max_dd = float(np.max(drawdowns)) if drawdowns.size else 0.0
        avg_reward = float(np.mean(rewards))
        return EvaluationMetrics(avg_reward, sharpe, max_dd, total_return)

    def _log_to_mlflow(self, model, label: str) -> str | None:
        if mlflow is None:
            return None
        artifact_path = f"models/{label}"
        try:
            mlflow.sklearn.log_model(model, artifact_path)  # type: ignore[arg-type]
            return artifact_path
        except Exception:
            return None


__all__ = [
    "WalkForwardTrainer",
    "WalkForwardConfig",
    "WalkForwardSplit",
    "TrainResult",
    "EvaluationMetrics",
]
