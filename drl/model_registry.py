"""Model Registry for FinPilot DRL agents.

Provides model versioning, persistence, and loading capabilities.
Stores trained models with metadata for tracking and comparison.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a registered model."""

    model_id: str
    name: str
    algorithm: str
    version: str
    created_at: str

    # Training info
    total_timesteps: int = 0
    training_symbols: List[str] = field(default_factory=list)
    train_start: Optional[str] = None
    train_end: Optional[str] = None

    # Performance metrics
    metrics: Dict[str, float] = field(default_factory=dict)

    # Configuration
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    feature_columns: List[str] = field(default_factory=list)

    # Paths
    model_path: Optional[str] = None
    pipeline_path: Optional[str] = None

    # Status
    is_active: bool = False
    tags: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelMetadata":
        return cls(**data)


class ModelRegistry:
    """
    Central registry for DRL models.

    Manages model versions, stores metadata, and provides
    easy access to trained models.

    Example:
        >>> registry = ModelRegistry("models/")
        >>>
        >>> # Save a model
        >>> model_id = registry.save_model(
        ...     model=trained_model,
        ...     name="finpilot_ppo",
        ...     algorithm="PPO",
        ...     metrics={"sharpe": 1.5, "total_return": 0.25}
        ... )
        >>>
        >>> # Load the best model
        >>> model = registry.load_best("finpilot_ppo", metric="sharpe")
        >>>
        >>> # List all versions
        >>> versions = registry.list_models("finpilot_ppo")
    """

    REGISTRY_FILE = "registry.json"

    def __init__(self, storage_path: str = "models/"):
        """
        Initialize the model registry.

        Args:
            storage_path: Base directory for model storage
        """
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.storage_path / self.REGISTRY_FILE
        self._registry: Dict[str, ModelMetadata] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Load registry from disk."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r") as f:
                    data = json.load(f)
                    self._registry = {k: ModelMetadata.from_dict(v) for k, v in data.items()}
                logger.info(f"Loaded {len(self._registry)} models from registry")
            except Exception as e:
                logger.warning(f"Could not load registry: {e}")
                self._registry = {}
        else:
            self._registry = {}

    def _save_registry(self) -> None:
        """Persist registry to disk."""
        try:
            with open(self.registry_file, "w") as f:
                data = {k: v.to_dict() for k, v in self._registry.items()}
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save registry: {e}")

    def _generate_model_id(self, name: str) -> str:
        """Generate a unique model ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{name}_{timestamp}"

    def _get_model_dir(self, model_id: str) -> Path:
        """Get the storage directory for a model."""
        return self.storage_path / model_id

    def save_model(
        self,
        model: Any,
        name: str,
        algorithm: str,
        metrics: Optional[Dict[str, float]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        training_symbols: Optional[List[str]] = None,
        total_timesteps: int = 0,
        train_start: Optional[str] = None,
        train_end: Optional[str] = None,
        feature_columns: Optional[List[str]] = None,
        pipeline: Optional[Any] = None,
        tags: Optional[List[str]] = None,
        notes: str = "",
        set_active: bool = False,
    ) -> str:
        """
        Save a trained model to the registry.

        Args:
            model: Trained SB3 model (PPO, SAC, etc.)
            name: Model name (e.g., "finpilot_ppo")
            algorithm: Algorithm type ("PPO", "SAC")
            metrics: Performance metrics dict
            hyperparameters: Training hyperparameters
            training_symbols: Symbols used for training
            total_timesteps: Number of training steps
            train_start: Training data start date
            train_end: Training data end date
            feature_columns: List of feature columns
            pipeline: FeaturePipeline artifact (optional)
            tags: List of tags for filtering
            notes: Free-form notes
            set_active: Whether to set as active model

        Returns:
            model_id: Unique identifier for the saved model
        """
        model_id = self._generate_model_id(name)
        model_dir = self._get_model_dir(model_id)
        model_dir.mkdir(parents=True, exist_ok=True)

        # Save the SB3 model
        model_path = model_dir / "model"
        try:
            model.save(str(model_path))
            logger.info(f"Model saved to {model_path}")
        except Exception as e:
            logger.error(f"Could not save model: {e}")
            raise

        # Save pipeline if provided
        pipeline_path = None
        if pipeline is not None:
            from .persistence import build_artifact, save_artifact

            pipeline_path_obj = model_dir / "pipeline.json"
            try:
                artifact = build_artifact(pipeline)
                save_artifact(artifact, pipeline_path_obj)
                pipeline_path = str(pipeline_path_obj)
            except Exception as e:
                logger.warning(f"Could not save pipeline: {e}")

        # Determine version
        existing = [m for m in self._registry.values() if m.name == name]
        version = f"v{len(existing) + 1}"

        # Create metadata
        metadata = ModelMetadata(
            model_id=model_id,
            name=name,
            algorithm=algorithm,
            version=version,
            created_at=datetime.now().isoformat(),
            total_timesteps=total_timesteps,
            training_symbols=training_symbols or [],
            train_start=train_start,
            train_end=train_end,
            metrics=metrics or {},
            hyperparameters=hyperparameters or {},
            feature_columns=feature_columns or [],
            model_path=str(model_path),
            pipeline_path=pipeline_path,
            is_active=set_active,
            tags=tags or [],
            notes=notes,
        )

        # If setting as active, deactivate others
        if set_active:
            for m in self._registry.values():
                if m.name == name:
                    m.is_active = False

        # Register
        self._registry[model_id] = metadata
        self._save_registry()

        logger.info(f"Model registered: {model_id} ({version})")
        return model_id

    def load_model(self, model_id: str) -> Any:
        """
        Load a model by its ID.

        Args:
            model_id: Unique model identifier

        Returns:
            Loaded SB3 model

        Raises:
            KeyError: If model not found
            ImportError: If SB3 not installed
        """
        if model_id not in self._registry:
            raise KeyError(f"Model not found: {model_id}")

        metadata = self._registry[model_id]

        if metadata.model_path is None:
            raise ValueError(f"Model path not set for: {model_id}")

        try:
            if metadata.algorithm == "PPO":
                from stable_baselines3 import PPO

                return PPO.load(metadata.model_path)
            elif metadata.algorithm == "SAC":
                from stable_baselines3 import SAC

                return SAC.load(metadata.model_path)
            else:
                raise ValueError(f"Unknown algorithm: {metadata.algorithm}")
        except ImportError:
            raise ImportError(
                "stable-baselines3 required. Install: pip install stable-baselines3[extra]"
            )

    def load_best(
        self, name: str, metric: str = "sharpe_ratio", higher_is_better: bool = True
    ) -> Any:
        """
        Load the best performing model by a metric.

        Args:
            name: Model name to filter
            metric: Metric key to compare
            higher_is_better: Whether higher metric values are better

        Returns:
            Loaded SB3 model
        """
        candidates = [m for m in self._registry.values() if m.name == name]

        if not candidates:
            raise KeyError(f"No models found with name: {name}")

        # Filter by metric availability
        with_metric = [m for m in candidates if metric in m.metrics]

        if not with_metric:
            logger.warning(f"No models with metric '{metric}', using latest")
            best = max(candidates, key=lambda m: m.created_at)
        else:
            if higher_is_better:
                best = max(with_metric, key=lambda m: m.metrics.get(metric, 0))
            else:
                best = min(with_metric, key=lambda m: m.metrics.get(metric, float("inf")))

        logger.info(
            f"Loading best model: {best.model_id} ({metric}={best.metrics.get(metric, 'N/A')})"
        )
        return self.load_model(best.model_id)

    def load_active(self, name: str) -> Any:
        """
        Load the active model for a given name.

        Args:
            name: Model name

        Returns:
            Loaded SB3 model
        """
        for m in self._registry.values():
            if m.name == name and m.is_active:
                return self.load_model(m.model_id)

        raise KeyError(f"No active model found for: {name}")

    def set_active(self, model_id: str) -> None:
        """Set a model as the active version."""
        if model_id not in self._registry:
            raise KeyError(f"Model not found: {model_id}")

        metadata = self._registry[model_id]
        name = metadata.name

        # Deactivate others
        for m in self._registry.values():
            if m.name == name:
                m.is_active = False

        metadata.is_active = True
        self._save_registry()
        logger.info(f"Set active: {model_id}")

    def list_models(
        self,
        name: Optional[str] = None,
        algorithm: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[ModelMetadata]:
        """
        List registered models with optional filtering.

        Args:
            name: Filter by model name
            algorithm: Filter by algorithm
            tags: Filter by tags (any match)

        Returns:
            List of matching ModelMetadata
        """
        results = list(self._registry.values())

        if name:
            results = [m for m in results if m.name == name]

        if algorithm:
            results = [m for m in results if m.algorithm == algorithm]

        if tags:
            results = [m for m in results if any(t in m.tags for t in tags)]

        # Sort by created_at descending
        results.sort(key=lambda m: m.created_at, reverse=True)
        return results

    def get_metadata(self, model_id: str) -> ModelMetadata:
        """Get metadata for a model."""
        if model_id not in self._registry:
            raise KeyError(f"Model not found: {model_id}")
        return self._registry[model_id]

    def delete_model(self, model_id: str, force: bool = False) -> None:
        """
        Delete a model from the registry.

        Args:
            model_id: Model to delete
            force: Skip confirmation
        """
        if model_id not in self._registry:
            raise KeyError(f"Model not found: {model_id}")

        metadata = self._registry[model_id]

        if metadata.is_active and not force:
            raise ValueError("Cannot delete active model without force=True")

        # Remove files
        model_dir = self._get_model_dir(model_id)
        if model_dir.exists():
            shutil.rmtree(model_dir)

        # Remove from registry
        del self._registry[model_id]
        self._save_registry()
        logger.info(f"Deleted model: {model_id}")

    def compare_models(
        self, model_ids: List[str], metrics: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare multiple models by their metrics.

        Args:
            model_ids: List of model IDs to compare
            metrics: Specific metrics to compare (None = all)

        Returns:
            Dict[model_id, Dict[metric, value]]
        """
        result = {}
        for model_id in model_ids:
            if model_id not in self._registry:
                continue
            m = self._registry[model_id]
            if metrics:
                result[model_id] = {k: v for k, v in m.metrics.items() if k in metrics}
            else:
                result[model_id] = m.metrics.copy()
        return result

    def get_latest(self, name: str) -> Optional[ModelMetadata]:
        """Get the latest model version for a name."""
        candidates = [m for m in self._registry.values() if m.name == name]
        if not candidates:
            return None
        return max(candidates, key=lambda m: m.created_at)

    def summary(self) -> Dict[str, Any]:
        """Get a summary of the registry."""
        models_by_name = {}
        for m in self._registry.values():
            if m.name not in models_by_name:
                models_by_name[m.name] = []
            models_by_name[m.name].append(m)

        return {
            "total_models": len(self._registry),
            "model_names": list(models_by_name.keys()),
            "versions_per_name": {k: len(v) for k, v in models_by_name.items()},
            "algorithms": list(set(m.algorithm for m in self._registry.values())),
            "storage_path": str(self.storage_path),
        }


# Singleton instance for convenience
_default_registry: Optional[ModelRegistry] = None


def get_registry(storage_path: str = "models/") -> ModelRegistry:
    """Get or create the default model registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ModelRegistry(storage_path)
    return _default_registry


__all__ = ["ModelRegistry", "ModelMetadata", "get_registry"]
