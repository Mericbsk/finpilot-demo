"""Feature lineage schema (Gate 1.3) — research-only, Level A.

Defines the per-feature provenance contract: for every feature in the
enriched export, when it was knowable (timestamp/age), its source field, and
its computation window. This is the schema only; wiring it into the export is
a separate Level B data-contract change.

The point: a feature's predictive value is meaningless if we cannot say what
was knowable at scan time. This schema makes that explicit per feature.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureLineage:
    """Provenance for a single feature.

    knowable_at: when the feature's inputs become available relative to the
        scan bar. "scan_close" = at the scan bar's close; "scan_open" = at the
        scan bar's open; "prior_close" = knowable the day before.
    lookback_bars: how many bars back the feature's window extends (0 = same bar).
    source: the raw field(s) the feature derives from.
    leakage_risk: "none" | "low" | "high" — high if the feature could encode
        information from after the scan bar.
    """

    name: str
    knowable_at: str
    lookback_bars: int
    source: tuple[str, ...]
    leakage_risk: str = "low"


# The enriched export's feature set, with provenance. This is the contract
# that Gate 1.3 requires before any confirmatory run.
FEATURE_LINEAGE: tuple[FeatureLineage, ...] = (
    FeatureLineage("price", "scan_close", 0, ("close",), "none"),
    FeatureLineage("score", "scan_close", 0, ("close", "volume"), "low"),
    FeatureLineage("composite_score", "scan_close", 0, ("close", "volume"), "low"),
    FeatureLineage("finpilot_score", "scan_close", 0, ("close", "volume"), "low"),
    FeatureLineage("gap_pct", "scan_open", 0, ("open", "prior_close"), "none"),
    FeatureLineage("rvol", "scan_close", 20, ("volume",), "none"),
    FeatureLineage("atr_pct_real", "scan_close", 14, ("high", "low", "close"), "none"),
    FeatureLineage("dist_52w_high", "scan_close", 252, ("high", "close"), "none"),
    # Outcome/label fields — these are FORWARD-looking and must never be used
    # as features. Marked high leakage risk by construction.
    FeatureLineage("resolved_pct_t5", "forward", 5, ("high",), "high"),
    FeatureLineage("resolved_pct_1d", "forward", 1, ("close",), "high"),
    FeatureLineage("c2c_1d", "forward", 1, ("close",), "high"),
    FeatureLineage("c2c_5d", "forward", 5, ("close",), "high"),
    FeatureLineage("mae_t5", "forward", 5, ("low",), "high"),
)


def feature_lineage_map() -> dict[str, FeatureLineage]:
    return {f.name: f for f in FEATURE_LINEAGE}


def forward_looking_fields() -> set[str]:
    """Fields that encode future information and must never be features."""
    return {f.name for f in FEATURE_LINEAGE if f.knowable_at == "forward"}


def validate_feature_set(feature_names: list[str]) -> dict:
    """Check a proposed feature set for leakage against the lineage contract."""
    fwd = forward_looking_fields()
    leaked = [f for f in feature_names if f in fwd]
    unknown = [f for f in feature_names if f not in feature_lineage_map()]
    return {
        "ok": not leaked and not unknown,
        "leaked_forward_fields": leaked,
        "unknown_fields": unknown,
    }
