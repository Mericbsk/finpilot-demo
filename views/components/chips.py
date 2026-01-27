# -*- coding: utf-8 -*-
"""
FinPilot Status Chips
=====================
UI bileşenleri: status chip'leri ve sinyal göstergeleri.
"""

import math
from html import escape
from typing import Any

import pandas as pd

import scanner
from views.components.helpers import get_regime_hint


def build_status_chip(
    label: str, variant: str = "neutral", icon: str | None = None, tooltip: str | None = None
) -> str:
    """Return HTML for a status chip with safe escaping."""
    if not label:
        return ""
    safe_label = escape(str(label))
    tooltip_attr = f" title='{escape(str(tooltip))}'" if tooltip else ""
    icon_html = f"<span class='chip-icon'>{icon}</span>" if icon else ""
    return f"<span class='status-chip {variant}'{tooltip_attr}>{icon_html}{safe_label}</span>"


def build_zscore_chip(data: dict) -> str:
    """Build a z-score chip showing momentum strength."""
    z_value = data.get("momentum_best_zscore")
    if z_value in (None, "", "NaN"):
        return ""
    try:
        z_val = float(z_value)
    except (TypeError, ValueError):
        return ""

    threshold = data.get("momentum_z_effective") or scanner.SETTINGS.get(
        "momentum_z_threshold", 1.5
    )
    try:
        threshold_val = float(threshold)
    except (TypeError, ValueError):
        threshold_val = float(scanner.SETTINGS.get("momentum_z_threshold", 1.5))

    baseline = data.get("momentum_baseline_window") or scanner.SETTINGS.get(
        "momentum_baseline_window", 60
    )
    try:
        baseline = int(baseline)
    except (TypeError, ValueError):
        baseline = scanner.SETTINGS.get("momentum_baseline_window", 60)

    horizon = data.get("momentum_best_horizon")
    try:
        horizon = int(horizon) if horizon is not None else None
    except (TypeError, ValueError):
        horizon = None

    segment_key = data.get("momentum_liquidity_segment")
    if segment_key in (None, ""):
        segment_key_cast = None
    else:
        segment_key_cast = str(segment_key)
    segment_labels = {
        "high_liquidity": "Yüksek hacim",
        "mid_liquidity": "Orta hacim",
        "low_liquidity": "Düşük hacim",
    }
    if segment_key_cast:
        segment_label = segment_labels.get(segment_key_cast, segment_key_cast)
    else:
        segment_label = ""

    z_abs = abs(z_val)
    if math.isfinite(z_abs):
        cdf = 0.5 * (1 + math.erf(z_abs / math.sqrt(2)))
        unusual_pct = cdf * 100.0
    else:
        unusual_pct = None

    if z_abs >= threshold_val:
        variant = "success" if z_val >= 0 else "warning"
    else:
        variant = "neutral"

    horizon_text = f"{horizon} periyot" if horizon else "Son getiri"
    baseline_text = f"{baseline} periyot"
    rarity_text = (
        f"Bu hareket, geçmiş dağılımın %{unusual_pct:.1f} dilimi içinde."
        if unusual_pct is not None
        else ""
    )
    threshold_text = f"Eşik: ±{threshold_val:.1f}σ"
    if segment_label:
        threshold_text += f" · Segment: {segment_label}"

    tooltip = (
        f"Z-Skoru, {horizon_text} getirinin {baseline_text} ortalama ve volatilitesine göre "
        f"normalize edilmiş değeridir. {rarity_text} {threshold_text}"
    ).strip()

    label = f"Z · {z_val:+.1f}σ"
    return build_status_chip(label, variant=variant, icon="σ", tooltip=tooltip)


def build_signal_strength_chip(data: dict) -> str:
    """Build a signal strength chip showing recommendation power."""
    strength = data.get("strength")
    if strength in (None, "", "-", "NaN") or (hasattr(pd, "isna") and pd.isna(strength)):
        strength = scanner.compute_recommendation_strength(data)
    try:
        strength_val = float(strength)
        if strength_val <= 1:
            strength_val *= 100
    except Exception:
        strength_val = float(scanner.compute_recommendation_strength(data))
    strength_val = max(0, min(100, int(round(strength_val))))

    if strength_val >= 75:
        variant, descriptor = "success", "Güçlü"
    elif strength_val >= 55:
        variant, descriptor = "warning", "Takip"
    else:
        variant, descriptor = "neutral", "İzle"

    tooltip = "Makine öğrenimi skoru: ≥75 güçlü, 55-74 takip edilmesi gereken, <55 beklemede."
    label = f"{descriptor} · {strength_val}"
    return build_status_chip(label, variant=variant, icon="⚡", tooltip=tooltip)


def build_regime_chip(data: dict) -> str:
    """Build a market regime chip."""
    regime = data.get("regime")
    if regime in (None, "", "NaN", "-"):
        return build_status_chip(
            "Rejim · —", variant="neutral", icon="🧭", tooltip="Rejim bilgisi mevcut değil."
        )

    regime_text = str(regime)
    lower = regime_text.lower()
    if any(token in lower for token in ["bull", "trend", "up"]):
        variant, descriptor = "success", "Prospektif"
    elif any(token in lower for token in ["bear", "down", "risk"]):
        variant, descriptor = "warning", "Savunma"
    else:
        variant, descriptor = "neutral", "Nötr"

    tooltip = get_regime_hint(regime)
    label = f"{descriptor} · {regime_text.upper()}"
    return build_status_chip(label, variant=variant, icon="🧭", tooltip=tooltip)


def build_risk_reward_chip(data: dict) -> str:
    """Build a risk/reward ratio chip."""
    rr = data.get("risk_reward") or data.get("risk_reward_ratio")
    if rr is None:
        return ""
    try:
        rr_val = float(rr)
    except Exception:
        return ""

    if rr_val >= 2.0:
        variant, descriptor = "success", "R/R"
    elif rr_val >= 1.2:
        variant, descriptor = "warning", "R/R"
    else:
        variant, descriptor = "neutral", "R/R"

    tooltip = "Risk/ödül oranı. ≥2 güçlü, 1.2-1.99 dikkatle izlenmeli."
    label = f"{descriptor} · {rr_val:.2f}x"
    return build_status_chip(label, variant=variant, icon="📊", tooltip=tooltip)


def compose_signal_chips(data: dict) -> list[str]:
    """Compose all signal chips for a data row."""
    chips = [
        build_zscore_chip(data),
        build_signal_strength_chip(data),
        build_regime_chip(data),
        build_risk_reward_chip(data),
    ]
    return [chip for chip in chips if chip]
