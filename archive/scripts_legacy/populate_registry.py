#!/usr/bin/env python3
"""Populate models/registry.json from existing PPO checkpoint .zip files.

Sprint 13 — Critical item #1.

This script scans models/ for PPO .zip files, constructs ModelMetadata entries,
writes registry.json, and validates each model can be loaded by SB3.

Run once:
    python scripts/populate_registry.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drl.config import DEFAULT_CONFIG  # noqa: E402
from drl.model_registry import ModelMetadata  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model definitions — ordered chronologically by training time
# ---------------------------------------------------------------------------
MODELS: list[dict] = [
    {
        "file": "ppo_first_20260217_163541.zip",
        "model_id": "ppo_first_20260217_163541",
        "name": "finpilot_ppo",
        "version": "v1",
        "created_at": "2026-02-17T16:35:41",
        "tags": ["initial", "baseline"],
        "notes": "First PPO training run — baseline model.",
        "total_timesteps": 50_000,
    },
    {
        "file": "ppo_real_20260217_164307.zip",
        "model_id": "ppo_real_20260217_164307",
        "name": "finpilot_ppo",
        "version": "v2",
        "created_at": "2026-02-17T16:43:07",
        "tags": ["real-data"],
        "notes": "Real market data training run.",
        "total_timesteps": 50_000,
    },
    {
        "file": "ppo_production_20260217_165440.zip",
        "model_id": "ppo_production_20260217_165440",
        "name": "finpilot_ppo",
        "version": "v3",
        "created_at": "2026-02-17T16:54:40",
        "tags": ["production"],
        "notes": "Production-grade training with full pipeline.",
        "total_timesteps": 100_000,
    },
    {
        "file": "ppo_balanced_20260217_171208.zip",
        "model_id": "ppo_balanced_20260217_171208",
        "name": "finpilot_ppo",
        "version": "v4",
        "created_at": "2026-02-17T17:12:08",
        "tags": ["balanced"],
        "notes": "Balanced reward weights for Sharpe / drawdown trade-off.",
        "total_timesteps": 150_000,
    },
    {
        "file": "ppo_aggressive_20260217_173313.zip",
        "model_id": "ppo_aggressive_20260217_173313",
        "name": "finpilot_ppo",
        "version": "v5",
        "created_at": "2026-02-17T17:33:13",
        "tags": ["aggressive"],
        "notes": "Aggressive reward weighting — higher PnL emphasis.",
        "total_timesteps": 150_000,
        "is_active": True,  # latest ⇒ active by default
    },
]

# Default hyperparameters mirroring WalkForwardConfig defaults
DEFAULT_HYPERPARAMS = {
    "algorithm": "PPO",
    "learning_rate": 3e-4,
    "gamma": 0.99,
    "gae_lambda": 0.95,
    "ent_coef": 0.001,
    "vf_coef": 0.5,
}

# Training symbols used across runs (per inference.json history)
TRAINING_SYMBOLS = ["AAPL", "BTC-USD", "NVDA", "TSLA", "ETH-USD"]

# Feature columns from DEFAULT_CONFIG
FEATURE_COLUMNS = DEFAULT_CONFIG.feature_columns


def build_registry(models_dir: Path) -> dict[str, dict]:
    """Construct registry entries for all known models."""
    registry: dict[str, dict] = {}

    for defn in MODELS:
        zip_path = models_dir / defn["file"]
        if not zip_path.exists():
            logger.warning("SKIP  %s — file not found", defn["file"])
            continue

        # SB3 model_path is the path without .zip extension
        model_path = str(zip_path.with_suffix(""))

        metadata = ModelMetadata(
            model_id=defn["model_id"],
            name=defn["name"],
            algorithm="PPO",
            version=defn["version"],
            created_at=defn["created_at"],
            total_timesteps=defn.get("total_timesteps", 50_000),
            training_symbols=TRAINING_SYMBOLS,
            train_start="2025-01-01",
            train_end="2026-02-17",
            metrics={},  # Will be populated by walk-forward validation
            hyperparameters=DEFAULT_HYPERPARAMS,
            feature_columns=FEATURE_COLUMNS,
            model_path=model_path,
            pipeline_path=None,
            is_active=defn.get("is_active", False),
            tags=defn.get("tags", []),
            notes=defn.get("notes", ""),
        )

        registry[metadata.model_id] = metadata.to_dict()
        logger.info(
            "  ✓  %-45s  %s  active=%s",
            metadata.model_id,
            metadata.version,
            metadata.is_active,
        )

    return registry


def validate_loading(registry: dict[str, dict]) -> int:
    """Try to load each registered model with SB3.  Returns failure count."""
    failures = 0
    try:
        from stable_baselines3 import PPO
    except ImportError:
        logger.warning("stable-baselines3 not installed — skipping validation")
        return 0

    for model_id, meta in registry.items():
        model_path = meta["model_path"]
        try:
            _model = PPO.load(model_path)
            logger.info("  ✓  load OK  %s", model_id)
        except Exception as exc:
            logger.error("  ✗  load FAIL  %s — %s", model_id, exc)
            failures += 1

    return failures


def main() -> None:
    models_dir = ROOT / "models"
    registry_path = models_dir / "registry.json"

    logger.info("═" * 60)
    logger.info("Model Registry Population — Sprint 13")
    logger.info("═" * 60)
    logger.info("models dir : %s", models_dir)
    logger.info("registry   : %s", registry_path)
    logger.info("")

    # Build entries
    logger.info("Scanning model checkpoints …")
    registry = build_registry(models_dir)
    logger.info("Registered %d models", len(registry))
    logger.info("")

    # Write registry.json
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2, default=str)
    logger.info("Wrote %s (%d bytes)", registry_path, registry_path.stat().st_size)
    logger.info("")

    # Validate
    logger.info("Validating model loading …")
    failures = validate_loading(registry)
    if failures:
        logger.error("%d model(s) failed to load!", failures)
        sys.exit(1)

    logger.info("")
    logger.info("═" * 60)
    logger.info("✓  Registry populated successfully — %d models", len(registry))
    logger.info("═" * 60)


if __name__ == "__main__":
    main()
