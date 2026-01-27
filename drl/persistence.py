"""Persistence helpers for DRL preprocessing artefacts.

This module centralises the logic for serialising and deserialising
:class:`~drl.feature_pipeline.FeaturePipeline` state.  Persisting the
scaler statistics alongside a lightweight signature of the feature
configuration makes it possible to reuse trained pipelines across
walk-forward windows, paper trading jobs and production deployments.

The helpers deliberately operate on plain dictionaries so they can be stored as
JSON/MsgPack artefacts in MLflow, Weights & Biases or a simple object store.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Sequence, Union

from .config import FeatureSpec, MarketEnvConfig
from .feature_pipeline import FeaturePipeline, ScalerStats

_ARTIFACT_VERSION = "1.0.0"


@dataclass(frozen=True)
class FeaturePipelineArtifact:
    """Canonical representation of a fitted feature pipeline."""

    artifact_version: str
    feature_signature: str
    config_schema_version: str
    feature_specs: Sequence[Mapping[str, Any]]
    scaler_stats: ScalerStats

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_version": self.artifact_version,
            "feature_signature": self.feature_signature,
            "config_schema_version": self.config_schema_version,
            "feature_specs": [dict(spec) for spec in self.feature_specs],
            "scaler_stats": self.scaler_stats,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> FeaturePipelineArtifact:
        try:
            return cls(
                artifact_version=str(payload["artifact_version"]),
                feature_signature=str(payload["feature_signature"]),
                config_schema_version=str(payload["config_schema_version"]),
                feature_specs=tuple(payload["feature_specs"]),
                scaler_stats=payload["scaler_stats"],
            )
        except KeyError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Missing key in feature pipeline artefact: {exc}") from exc


def _feature_signature_from_specs(specs: Sequence[FeatureSpec]) -> str:
    parts: Iterable[str] = (
        "|".join(
            [spec.name, spec.scaler, "1" if spec.required else "0", str(spec.weight)]
            + list(spec.columns)
        )
        for spec in specs
    )
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest


def build_artifact(pipeline: FeaturePipeline) -> FeaturePipelineArtifact:
    """Create an artefact for the currently fitted pipeline."""

    if not pipeline._stats:  # pragma: no cover - runtime guard
        raise RuntimeError("FeaturePipeline must be fitted before building an artefact.")

    config = pipeline.config
    signature = _feature_signature_from_specs(config.feature_specs)
    specs_payload = [
        {
            "name": spec.name,
            "columns": list(spec.columns),
            "scaler": spec.scaler,
            "required": spec.required,
            "weight": spec.weight,
        }
        for spec in config.feature_specs
    ]
    return FeaturePipelineArtifact(
        artifact_version=_ARTIFACT_VERSION,
        feature_signature=signature,
        config_schema_version=config.schema_version,
        feature_specs=tuple(specs_payload),
        scaler_stats=pipeline.export_state(),
    )


def save_artifact(artifact: FeaturePipelineArtifact, destination: Union[str, Path]) -> Path:
    """Persist the artefact as a JSON file on disk."""

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(artifact.to_dict(), handle, indent=2, sort_keys=True)
    return path


def load_artifact(source: Union[str, Path]) -> FeaturePipelineArtifact:
    """Load a previously saved artefact from disk."""

    path = Path(source)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return FeaturePipelineArtifact.from_dict(payload)


def restore_pipeline(
    pipeline: FeaturePipeline,
    artifact: FeaturePipelineArtifact,
    *,
    allow_signature_mismatch: bool = False,
) -> None:
    """Load stats into an existing pipeline, validating configuration integrity."""

    expected_signature = _feature_signature_from_specs(pipeline.config.feature_specs)
    if artifact.feature_signature != expected_signature and not allow_signature_mismatch:
        raise ValueError(
            "Feature specification mismatch between artefact and current pipeline."
            f" expected={expected_signature} got={artifact.feature_signature}"
        )
    pipeline.load_state(artifact.scaler_stats)


__all__ = [
    "FeaturePipelineArtifact",
    "build_artifact",
    "save_artifact",
    "load_artifact",
    "restore_pipeline",
]
