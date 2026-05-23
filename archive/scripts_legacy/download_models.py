#!/usr/bin/env python3
"""
Download / restore trained DRL models from external storage.

This script exists because model weight files (.zip) are excluded from git
to keep the repository lightweight (<5 MB vs ~23 MB with weights).

Usage:
    # Retrain locally (recommended for dev):
    python scripts/retrain_models.py

    # Or restore from a team-shared backup:
    python scripts/download_models.py --source /path/to/backup

Future:
    Integrate with S3/GCS for automated CI model publishing.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
REGISTRY_PATH = MODELS_DIR / "registry.json"


def check_models() -> dict:
    """Report which models are present and which are missing."""
    if not REGISTRY_PATH.exists():
        print("⚠️  No registry.json found. Run training first.")
        return {}

    with open(REGISTRY_PATH) as f:
        registry = json.load(f)

    present = []
    missing = []
    for model_id, _meta in registry.items():
        model_dir = MODELS_DIR / model_id
        if model_dir.exists() and any(model_dir.iterdir()):
            present.append(model_id)
        else:
            missing.append(model_id)

    print(f"\n📊 Model Status: {len(present)} present, {len(missing)} missing")
    if present:
        print(f"   ✅ Present: {', '.join(present[:5])}{'...' if len(present) > 5 else ''}")
    if missing:
        print(f"   ❌ Missing: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}")

    return {"present": present, "missing": missing}


def restore_from_backup(source: str) -> None:
    """Copy model directories from a local backup path."""
    src = Path(source)
    if not src.exists():
        print(f"❌ Source path not found: {source}")
        sys.exit(1)

    copied = 0
    for model_dir in src.iterdir():
        if model_dir.is_dir() and model_dir.name.startswith(("ppo_", "rppo_")):
            dest = MODELS_DIR / model_dir.name
            if not dest.exists():
                shutil.copytree(model_dir, dest)
                copied += 1
                print(f"   📥 Restored: {model_dir.name}")

    print(f"\n✅ Restored {copied} model(s) from {source}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download/check DRL model artifacts")
    parser.add_argument("--check", action="store_true", help="Check model status only")
    parser.add_argument("--source", type=str, help="Local backup path to restore from")
    args = parser.parse_args()

    if args.check or not args.source:
        check_models()
    if args.source:
        restore_from_backup(args.source)
