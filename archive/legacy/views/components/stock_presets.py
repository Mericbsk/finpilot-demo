"""
FinPilot Hazır Hisse Senedi Setleri
===================================

Kullanıcıların tek tıkla tarayabileceği hazır kategori listeleri.

Sprint 22: Preset verileri artık data/stock_presets.json dosyasından yükleniyor.
Bu dosya 1.613 LOC'luk hardcoded Python verisini ~150 LOC'a düşürmüştür.

Usage:
    from views.components.stock_presets import STOCK_PRESETS, render_preset_selector

    selected = render_preset_selector()
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ============================================
# DATA MODEL
# ============================================


@dataclass
class StockPreset:
    """Hazır hisse senedi seti."""

    name: str
    icon: str
    description: str
    symbols: list[str]
    category: str


# ============================================
# JSON DATA LOADING
# ============================================

_PRESETS_JSON = Path(__file__).resolve().parent.parent.parent / "data" / "stock_presets.json"


@lru_cache(maxsize=1)
def _load_presets_from_json() -> dict[str, StockPreset]:
    """Load preset data from JSON file (cached, loaded once)."""
    if not _PRESETS_JSON.exists():
        logger.warning(
            "stock_presets.json not found at %s — returning empty presets", _PRESETS_JSON
        )
        return {}

    try:
        with open(_PRESETS_JSON, encoding="utf-8") as f:
            raw: dict[str, dict] = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load stock_presets.json: %s", e)
        return {}

    presets: dict[str, StockPreset] = {}
    for key, data in raw.items():
        try:
            presets[key] = StockPreset(
                name=data["name"],
                icon=data.get("icon", "📊"),
                description=data.get("description", ""),
                symbols=data.get("symbols", []),
                category=data.get("category", "Genel"),
            )
        except (KeyError, TypeError) as e:
            logger.warning("Skipping malformed preset %s: %s", key, e)

    logger.debug(
        "Loaded %d presets (%d total symbols)",
        len(presets),
        sum(len(p.symbols) for p in presets.values()),
    )
    return presets


# Module-level constant — backward compatible
STOCK_PRESETS: dict[str, StockPreset] = _load_presets_from_json()


# ============================================
# PUBLIC API — unchanged signatures
# ============================================


def get_preset_symbols(preset_key: str) -> list[str]:
    """Belirtilen preset'in sembollerini döndür."""
    if preset_key in STOCK_PRESETS:
        return STOCK_PRESETS[preset_key].symbols
    return []


def list_all_presets() -> dict[str, str]:
    """Tüm presetlerin listesi (key: name)."""
    return {key: f"{p.icon} {p.name}" for key, p in STOCK_PRESETS.items()}


def get_finpilot_sector_symbols() -> list[str]:
    """Tüm FinPilot sektör sembollerini birleştirilmiş liste olarak döndür."""
    seen: set[str] = set()
    result: list[str] = []
    for key, preset in STOCK_PRESETS.items():
        if key.startswith("fp_"):
            for s in preset.symbols:
                if s not in seen:
                    seen.add(s)
                    result.append(s)
    return result


def load_sectors_from_index() -> dict[str, dict]:
    """data/tickers/sectors/sector_index.json dosyasından dinamik sektör yükle."""
    index_path = os.path.join(os.getcwd(), "data", "tickers", "sectors", "sector_index.json")
    if not os.path.exists(index_path):
        return {}
    try:
        with open(index_path) as f:
            return json.load(f)
    except Exception:
        return {}


# ============================================
# 📊 İSTATİSTİKLER
# ============================================


def get_preset_stats() -> dict[str, Any]:
    """Preset istatistikleri."""
    total_presets = len(STOCK_PRESETS)
    total_symbols = sum(len(p.symbols) for p in STOCK_PRESETS.values())
    unique_symbols = len({s for p in STOCK_PRESETS.values() for s in p.symbols})

    categories: dict[str, int] = {}
    for p in STOCK_PRESETS.values():
        categories[p.category] = categories.get(p.category, 0) + 1

    return {
        "total_presets": total_presets,
        "total_symbols": total_symbols,
        "unique_symbols": unique_symbols,
        "categories": categories,
    }
