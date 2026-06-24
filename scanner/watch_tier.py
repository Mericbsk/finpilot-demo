"""Early-detection ladder — WATCH → SETUP → TRIGGER → CONFIRM.

Rationale (docs/audit-2026-06-12/10-scanner-analiz-ve-arastirma-degerlendirme.md):
the existing scanner only emits the bottom rung — CONFIRM (score==3 + multi-
timeframe EMA alignment) — which is a *lagging* confirmation: by the time all
indicators agree the move has started. This module adds the three earlier rungs
so the system can surface a name *before* it is entry-ready:

    WATCH    contraction (coiling) + early relative-volume acceleration
    SETUP    + a leading trigger: fresh catalyst OR first range-expansion bar
    TRIGGER  + price/volume breakout confirmation (level break + volume)
    CONFIRM  the existing entry_ok gate (full multi-timeframe alignment)

Design constraints (deliberate):
  * PURE and side-effect-free — takes a feature dict, returns a dict.
  * Does NOT change entry_ok or the live composite score. It is an additive,
    measurement-first classification layer. Position-size suggestions are
    advisory only (the report's staged-sizing recommendation) and never wire
    into execution.
  * "NONE" is a valid, common output — most symbols are not setting up.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Tier ordering for comparisons / sorting.
TIER_ORDER: dict[str, int] = {"NONE": 0, "WATCH": 1, "SETUP": 2, "TRIGGER": 3, "CONFIRM": 4}

# Advisory staged position-size fraction per tier (of full Kelly size).
# Advisory ONLY — never used to place orders. Surfaces the report's
# "scale-in on confirmation" idea to the user/UI.
TIER_SIZE_FRACTION: dict[str, float] = {
    "NONE": 0.0,
    "WATCH": 0.0,  # observe only
    "SETUP": 0.25,  # small starter
    "TRIGGER": 0.50,  # add on breakout
    "CONFIRM": 1.00,  # full size (still subject to risk gates downstream)
}

# Thresholds (tunable; conservative defaults). These gate the EARLY rungs only.
_CONTRACTION_MIN: float = 0.60  # "coiled" — contraction_factor at/above this
_RVOL_ACCEL_MIN: float = 0.30  # relative-volume rising
_CATALYST_MIN: float = 0.30  # signed catalyst_factor considered "fresh+bullish"
_RANGE_EXPANSION_MIN: float = 1.5  # today's range vs recent median body (×)
_VOLUME_CONFIRM_MIN: float = 2.0  # breakout volume multiple vs average


@dataclass
class TierResult:
    tier: str
    score: float  # 0-1 confidence within the early ladder
    reasons: list[str] = field(default_factory=list)
    suggested_size_fraction: float = 0.0

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "tier_score": round(self.score, 4),
            "tier_reasons": self.reasons,
            "suggested_size_fraction": self.suggested_size_fraction,
        }


def classify_tier(
    *,
    contraction_factor: float = 0.0,
    rvol_acceleration: float = 0.0,
    catalyst_factor: float = 0.0,
    range_expansion: float = 0.0,
    volume_multiple: float = 0.0,
    breakout_confirmed: bool = False,
    entry_ok: bool = False,
) -> TierResult:
    """Classify a symbol on the early-detection ladder.

    Args:
        contraction_factor: 0-1 from features.compute_contraction_factor.
        rvol_acceleration:  0-1 from features.compute_rvol_acceleration.
        catalyst_factor:    signed -1..1 from scanner.catalyst (positive=bullish).
        range_expansion:    today's true range / recent median range (×).
        volume_multiple:    today's volume / average (the scanner already has this).
        breakout_confirmed: level break + volume confirmation (caller-supplied).
        entry_ok:           the existing full-confirmation gate.

    Returns:
        TierResult with the highest rung whose conditions are met. Higher rungs
        do NOT require lower-rung flags to remain true (a clean confirmed entry
        can be CONFIRM even without a prior coiled base), but the early rungs
        capture the pre-event setup the lagging gate misses.
    """
    reasons: list[str] = []

    coiled = contraction_factor >= _CONTRACTION_MIN
    rising_vol = rvol_acceleration >= _RVOL_ACCEL_MIN
    fresh_catalyst = catalyst_factor >= _CATALYST_MIN
    expanding = range_expansion >= _RANGE_EXPANSION_MIN
    vol_confirm = volume_multiple >= _VOLUME_CONFIRM_MIN

    # ── CONFIRM: existing full-confirmation gate (lagging, highest certainty) ──
    if entry_ok:
        reasons.append("entry_ok: tam çok-zaman-dilimi onayı")
        score = 0.85 + 0.15 * min(1.0, contraction_factor + rvol_acceleration)
        return TierResult("CONFIRM", min(1.0, score), reasons, TIER_SIZE_FRACTION["CONFIRM"])

    # ── TRIGGER: breakout confirmed by price level + volume ───────────────────
    if breakout_confirmed and vol_confirm:
        reasons.append(f"kırılım + hacim teyidi (vol ×{volume_multiple:.1f})")
        if rising_vol:
            reasons.append("RVOL ivmesi sürüyor")
        score = 0.6 + 0.4 * min(1.0, rvol_acceleration + 0.5 * contraction_factor)
        return TierResult("TRIGGER", min(1.0, score), reasons, TIER_SIZE_FRACTION["TRIGGER"])

    # ── SETUP: a leading trigger present on top of (or instead of) a coil ─────
    leading = []
    if fresh_catalyst:
        leading.append(f"taze katalizör ({catalyst_factor:+.2f})")
    if expanding:
        leading.append(f"ilk genişleme barı (×{range_expansion:.1f})")
    if leading and (coiled or rising_vol):
        reasons.extend(leading)
        if coiled:
            reasons.append(f"sıkışma {contraction_factor:.2f}")
        if rising_vol:
            reasons.append(f"RVOL ivmesi {rvol_acceleration:.2f}")
        score = 0.4 + 0.3 * contraction_factor + 0.3 * rvol_acceleration
        return TierResult("SETUP", min(1.0, score), reasons, TIER_SIZE_FRACTION["SETUP"])

    # ── WATCH: coiling + early volume interest, nothing triggered yet ─────────
    if coiled and rising_vol:
        reasons.append(f"sıkışma {contraction_factor:.2f} + RVOL ivmesi {rvol_acceleration:.2f}")
        score = 0.2 + 0.3 * contraction_factor + 0.2 * rvol_acceleration
        return TierResult("WATCH", min(1.0, score), reasons, TIER_SIZE_FRACTION["WATCH"])
    if coiled:
        reasons.append(f"sıkışma {contraction_factor:.2f} (hacim ivmesi bekleniyor)")
        return TierResult(
            "WATCH", 0.2 + 0.2 * contraction_factor, reasons, TIER_SIZE_FRACTION["WATCH"]
        )

    return TierResult("NONE", 0.0, ["erken kurulum yok"], 0.0)


def compute_early_tier(
    df_1d,
    *,
    catalyst_factor: float = 0.0,
    volume_multiple: float = 0.0,
    entry_ok: bool = False,
    breakout_confirmed: bool = False,
) -> dict:
    """Convenience glue: daily OHLCV → early-detection tier dict.

    Computes contraction + RVOL-acceleration from ``df_1d`` (via
    scanner.features), derives a simple range-expansion ratio, then classifies.
    Returns a dict ready to merge into a scanner result row. Pure / best-effort:
    any failure degrades to a NONE tier rather than raising.

    Intended to be called behind an env flag (e.g. FINPILOT_ENABLE_EARLY_TIER)
    from scanner.evaluate so live behaviour is unchanged until explicitly on.
    """
    try:
        from scanner.features import (  # noqa: PLC0415
            compute_contraction_factor,
            compute_rvol_acceleration,
        )

        contraction = compute_contraction_factor(df_1d)
        rvol_accel = compute_rvol_acceleration(df_1d)

        # Range expansion: today's true range vs the median of the last 10 bars.
        range_expansion = 0.0
        try:
            if (
                hasattr(df_1d, "iloc")
                and len(df_1d) >= 11
                and {"High", "Low"}.issubset(df_1d.columns)
            ):
                rng = df_1d["High"].astype(float) - df_1d["Low"].astype(float)
                med = float(rng.iloc[-11:-1].median())
                if med > 0:
                    range_expansion = float(rng.iloc[-1]) / med
        except Exception:
            range_expansion = 0.0

        result = classify_tier(
            contraction_factor=contraction,
            rvol_acceleration=rvol_accel,
            catalyst_factor=catalyst_factor,
            range_expansion=range_expansion,
            volume_multiple=volume_multiple,
            breakout_confirmed=breakout_confirmed,
            entry_ok=entry_ok,
        )
        out = result.to_dict()
        out["contraction_factor"] = contraction
        out["rvol_acceleration"] = rvol_accel
        out["range_expansion"] = round(range_expansion, 3)
        return out
    except Exception:
        return {
            "tier": "NONE",
            "tier_score": 0.0,
            "tier_reasons": ["hesaplanamadı"],
            "suggested_size_fraction": 0.0,
        }
