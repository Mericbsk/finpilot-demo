"""Analysis utilities for FinPilot's DRL stack."""

from .explainability import (
    AlternativeSignal,
    NarrativePayload,
    RegimeStats,
    build_narrative_payload,
    estimate_regime_success,
    summarize_alternative_signals,
)
from .feature_importance import (
    FeatureImportanceSummary,
    PolicyDataset,
    collect_policy_dataset,
    compute_shap_summary,
    fit_surrogate_policy,
)

__all__ = [
    "PolicyDataset",
    "FeatureImportanceSummary",
    "collect_policy_dataset",
    "fit_surrogate_policy",
    "compute_shap_summary",
    "AlternativeSignal",
    "NarrativePayload",
    "RegimeStats",
    "summarize_alternative_signals",
    "build_narrative_payload",
    "estimate_regime_success",
]
