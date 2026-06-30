"""
Shortlist View — birleşik per-sembol görünüm
============================================

run_cycle state'ini (scan + social + bull/bear + enrichment) tek bir
per-sembol sözlüğe birleştirir. Saf fonksiyon — ağır bağımlılık yok,
kolay test edilir. API/UI bu görünümü tüketir.
"""

from __future__ import annotations

from typing import Any


def merge_shortlist_view(state: dict[str, Any]) -> dict[str, Any]:
    """run_cycle state'inden top-N için birleşik görünüm üretir.

    Dönen yapı: {symbol: {scan, social, bull, bear, enrichment}} —
    eksik bölümler boş dict olarak gelir (kısmi sonuçlara dayanıklı).
    """
    scan = state.get("scan_results", {}) or {}
    social = state.get("social_results", {}) or {}
    bull = state.get("bull_cases", {}) or {}
    bear = state.get("bear_cases", {}) or {}
    enrich = state.get("enrichment", {}) or {}

    top = state.get("top_symbols") or list(scan.keys())

    view: dict[str, Any] = {}
    for sym in top:
        view[sym] = {
            "symbol": sym,
            "scan": scan.get(sym, {}),
            "social": social.get(sym, {}),
            "bull": bull.get(sym, {}),
            "bear": bear.get(sym, {}),
            "enrichment": enrich.get(sym, {}),
        }
    return view
