"""Ensemble Router — Regime-Weighted Multi-Agent Inference.

Sprint 16b: Loads all regime-specific DRL agents (trend / range / volatile)
and routes predictions based on current regime detection weights.

Architecture:
    Market Data → Regime Detector (feature-based)
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      trend_ppo    range_ppo    volatile_ppo
          │            │            │
          ▼            ▼            ▼
       action_t     action_r     action_v
          │            │            │
          └────────────┼────────────┘
                       ▼
              Weighted Voting → final_action, confidence
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from .config import DEFAULT_CONFIG, MarketEnvConfig
from .inference import ActionType, DRLInference, PredictionResult
from .model_registry import ModelRegistry, get_registry

logger = logging.getLogger(__name__)

# Flag indicating successful module load (consumed by UI layers)
ENSEMBLE_AVAILABLE = True


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class AgentVote:
    """Single agent's prediction + regime weight."""

    tag: str  # "trend", "range", "volatile"
    prediction: PredictionResult | None
    regime_weight: float  # 0.0-1.0 from regime detector
    raw_action: float = 0.0

    @property
    def weighted_action(self) -> float:
        if self.prediction is None:
            return 0.0
        raw = (
            float(self.prediction.raw_action[0])
            if isinstance(self.prediction.raw_action, np.ndarray)
            else float(self.prediction.raw_action)
        )
        return raw * self.regime_weight

    @property
    def weighted_confidence(self) -> float:
        if self.prediction is None:
            return 0.0
        return self.prediction.confidence * self.regime_weight


@dataclass
class EnsembleResult:
    """Result from ensemble voting across all regime agents."""

    symbol: str
    final_action: ActionType
    final_confidence: float
    raw_ensemble_action: float

    # Position sizing
    suggested_position: float
    kelly_fraction: float

    # Per-agent breakdown
    votes: list[AgentVote] = field(default_factory=list)

    # Context
    dominant_regime: str = "unknown"
    regime_weights: dict[str, float] = field(default_factory=dict)
    agreement_score: float = 0.0  # 0-1, how much agents agree
    model_ids: list[str] = field(default_factory=list)
    timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "action": self.final_action.name,
            "confidence": round(self.final_confidence, 3),
            "raw_action": round(self.raw_ensemble_action, 4),
            "suggested_position": round(self.suggested_position, 3),
            "kelly_fraction": round(self.kelly_fraction, 3),
            "dominant_regime": self.dominant_regime,
            "regime_weights": {k: round(v, 3) for k, v in self.regime_weights.items()},
            "agreement_score": round(self.agreement_score, 3),
            "votes": [
                {
                    "tag": v.tag,
                    "action": v.prediction.action.name if v.prediction else "N/A",
                    "confidence": round(v.prediction.confidence, 3) if v.prediction else 0,
                    "regime_weight": round(v.regime_weight, 3),
                }
                for v in self.votes
            ],
            "model_ids": self.model_ids,
            "timestamp": self.timestamp,
        }

    @property
    def is_actionable(self) -> bool:
        return self.final_action != ActionType.HOLD and self.final_confidence > 0.4

    def to_prediction_result(self) -> PredictionResult:
        """Convert to PredictionResult for backward compatibility."""
        return PredictionResult(
            symbol=self.symbol,
            action=self.final_action,
            raw_action=self.raw_ensemble_action,
            confidence=self.final_confidence,
            suggested_position=self.suggested_position,
            kelly_fraction=self.kelly_fraction,
            regime=self.dominant_regime,
            timestamp=self.timestamp,
            model_id=f"ensemble({','.join(self.model_ids)})",
        )


# ---------------------------------------------------------------------------
# Ensemble Router
# ---------------------------------------------------------------------------

# Tag → model name mapping
_TAG_TO_NAME = {
    "trend": "ppo_trend",
    "range": "ppo_range",
    "volatile": "ppo_volatile",
}

# Tag → regime feature column mapping
_TAG_TO_REGIME_COL = {
    "trend": "regime_trend",
    "range": "regime_range",
    "volatile": "regime_volatility",
}


class EnsembleRouter:
    """
    Routes predictions through multiple regime-specialist DRL agents
    and produces a weighted consensus.

    Usage:
        router = EnsembleRouter()
        router.load_agents()  # loads all 3 regime models

        result = router.predict("AAPL")
        print(result.final_action, result.final_confidence)

        results = router.batch_predict(["AAPL", "MSFT", "NVDA"])
    """

    def __init__(
        self,
        registry: ModelRegistry | None = None,
        config: MarketEnvConfig | None = None,
        min_regime_weight: float = 0.05,
        disagreement_hold_threshold: float = 0.3,
    ):
        self.registry = registry or get_registry()
        self.config = config or DEFAULT_CONFIG
        self.min_regime_weight = min_regime_weight
        self.disagreement_hold_threshold = disagreement_hold_threshold

        self._agents: dict[str, DRLInference] = {}
        self._model_ids: dict[str, str] = {}
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded and len(self._agents) > 0

    @property
    def n_agents(self) -> int:
        return len(self._agents)

    def load_agents(self) -> int:
        """
        Load all available regime-specialist models from registry.

        Returns:
            Number of agents successfully loaded.
        """
        loaded = 0
        for tag, model_name in _TAG_TO_NAME.items():
            try:
                models = self.registry.list_models(name=model_name)
                if not models:
                    logger.debug("No model found for tag=%s name=%s", tag, model_name)
                    continue

                # Pick the latest model for this name
                latest = models[0]  # already sorted desc by created_at
                engine = DRLInference(registry=self.registry, config=self.config)
                success = engine.load_from_path(latest.model_path + ".zip")
                if not success or not engine.is_loaded:
                    logger.warning("Ensemble: model file load failed for %s", tag)
                    continue
                self._agents[tag] = engine
                self._model_ids[tag] = latest.model_id
                loaded += 1
                logger.info("Ensemble: loaded %s → %s", tag, latest.model_id)
            except Exception as e:
                logger.warning("Ensemble: failed to load %s: %s", tag, e)

        self._loaded = loaded > 0
        logger.info("Ensemble: %d/%d agents loaded", loaded, len(_TAG_TO_NAME))
        return loaded

    def _detect_regime_weights(self, df: pd.DataFrame) -> dict[str, float]:
        """
        Extract regime weights from the feature DataFrame.

        Returns dict like {"trend": 0.7, "range": 0.2, "volatile": 0.1}.
        """
        weights: dict[str, float] = {}
        last_row = df.iloc[-1]

        for tag, col in _TAG_TO_REGIME_COL.items():
            val = float(last_row.get(col, 0.0))
            weights[tag] = max(val, 0.0)

        # Normalize to sum=1
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        else:
            # Equal weights fallback
            n = len(weights)
            weights = dict.fromkeys(weights, 1.0 / n)

        return weights

    def predict(
        self,
        symbol: str,
        df: pd.DataFrame | None = None,
        risk_appetite: int = 5,
    ) -> EnsembleResult | None:
        """
        Generate ensemble prediction for a single symbol.

        Each agent predicts independently, then results are combined
        using regime-detected weights.
        """
        if not self.is_loaded:
            logger.warning("Ensemble not loaded. Call load_agents() first.")
            return None

        # Prepare features (use first available agent's preprocessing)
        if df is None:
            for engine in self._agents.values():
                df = engine._prepare_features(symbol)
                if df is not None:
                    break
            if df is None:
                logger.warning("Could not prepare features for %s", symbol)
                return None

        # Detect regime weights
        regime_weights = self._detect_regime_weights(df)

        # Collect votes from each agent
        votes: list[AgentVote] = []
        for tag, engine in self._agents.items():
            weight = regime_weights.get(tag, 0.0)
            if weight < self.min_regime_weight:
                # Skip near-zero weight agents
                votes.append(AgentVote(tag=tag, prediction=None, regime_weight=weight))
                continue

            pred = engine.predict(symbol, df=df)
            votes.append(AgentVote(tag=tag, prediction=pred, regime_weight=weight))

        # Weighted consensus
        total_weighted_action = sum(v.weighted_action for v in votes)
        total_weighted_confidence = sum(v.weighted_confidence for v in votes)

        # Determine final action
        final_action = ActionType.from_continuous(total_weighted_action, threshold=0.2)

        # Agreement score: how aligned are the agents?
        active_votes = [v for v in votes if v.prediction is not None]
        if len(active_votes) >= 2:
            actions = [
                1 if v.prediction.action == ActionType.BUY  # type: ignore[union-attr]
                else (-1 if v.prediction.action == ActionType.SELL else 0)  # type: ignore[union-attr]
                for v in active_votes
            ]
            # If all same sign → agreement=1, mixed → lower
            if (
                all(a > 0 for a in actions)
                or all(a < 0 for a in actions)
                or all(a == 0 for a in actions)
            ):
                agreement = 1.0
            else:
                # Count majority
                n_buy = sum(1 for a in actions if a > 0)
                n_sell = sum(1 for a in actions if a < 0)
                n_hold = sum(1 for a in actions if a == 0)
                majority = max(n_buy, n_sell, n_hold)
                agreement = majority / len(actions)
        else:
            agreement = 1.0

        # Disagreement filter: if agents strongly disagree, default to HOLD
        if agreement < self.disagreement_hold_threshold:
            final_action = ActionType.HOLD
            total_weighted_confidence *= 0.5

        # Final confidence scaling
        final_confidence = min(total_weighted_confidence * agreement, 1.0)

        # Position sizing
        action_magnitude = abs(total_weighted_action)
        risk_mult = risk_appetite / 10.0
        kelly = min(action_magnitude * final_confidence * risk_mult * 0.5, 0.5)
        position = min(kelly * 2, 0.25)

        # Dominant regime
        dominant_regime = max(regime_weights, key=regime_weights.get)  # type: ignore[arg-type]

        # Timestamp
        timestamp = None
        if hasattr(df.index[-1], "isoformat"):
            timestamp = df.index[-1].isoformat()

        return EnsembleResult(
            symbol=symbol,
            final_action=final_action,
            final_confidence=round(final_confidence, 3),
            raw_ensemble_action=round(total_weighted_action, 4),
            suggested_position=round(position, 3),
            kelly_fraction=round(kelly, 3),
            votes=votes,
            dominant_regime=dominant_regime,
            regime_weights=regime_weights,
            agreement_score=round(agreement, 3),
            model_ids=list(self._model_ids.values()),
            timestamp=timestamp,
        )

    def batch_predict(
        self, symbols: list[str], risk_appetite: int = 5
    ) -> list[EnsembleResult]:
        """
        Generate ensemble predictions for multiple symbols.

        Returns list sorted by confidence (highest first).
        """
        results: list[EnsembleResult] = []
        for symbol in symbols:
            result = self.predict(symbol, risk_appetite=risk_appetite)
            if result is not None:
                results.append(result)

        results.sort(key=lambda r: r.final_confidence, reverse=True)
        return results

    def get_status(self) -> dict[str, Any]:
        """Return router status for UI display."""
        return {
            "loaded": self._loaded,
            "n_agents": self.n_agents,
            "agents": {
                tag: {
                    "model_id": self._model_ids.get(tag, "N/A"),
                    "loaded": tag in self._agents,
                }
                for tag in _TAG_TO_NAME
            },
        }


# ---------------------------------------------------------------------------
# Module-level singleton for convenience
# ---------------------------------------------------------------------------

_router_instance: EnsembleRouter | None = None


def get_ensemble_router() -> EnsembleRouter:
    """Get or create the global EnsembleRouter singleton."""
    global _router_instance
    if _router_instance is None or not _router_instance.is_loaded:
        _router_instance = EnsembleRouter()
        _router_instance.load_agents()
    return _router_instance


def get_ensemble_predictions(
    symbols: list[str], max_symbols: int = 20
) -> dict[str, dict[str, Any]]:
    """
    Quick function: get ensemble predictions as a dict keyed by symbol.

    Returns format compatible with get_drl_predictions() for drop-in replacement.
    """
    try:
        router = get_ensemble_router()
        if not router.is_loaded:
            return {}

        results = router.batch_predict(symbols[:max_symbols])
        return {
            r.symbol: {
                "action": r.final_action.name,
                "confidence": r.final_confidence,
                "suggested_position": r.suggested_position,
                "regime": r.dominant_regime,
                "is_actionable": r.is_actionable,
                "raw_action": r.raw_ensemble_action,
                "agreement_score": r.agreement_score,
                "ensemble": True,
            }
            for r in results
        }
    except Exception as e:
        logger.error("Ensemble prediction error: %s", e)
        return {}


__all__ = [
    "ENSEMBLE_AVAILABLE",
    "EnsembleRouter",
    "EnsembleResult",
    "AgentVote",
    "get_ensemble_router",
    "get_ensemble_predictions",
]
