"""Ensemble Router — Regime-Weighted Multi-Agent Inference.

Sprint 16b: Loads all regime-specific DRL agents (trend / range / volatile)
and routes predictions based on current regime detection weights.

Sprint 18 Phase 4.1: Added LearnableEnsembleWeights — an online Exp3-style
meta-learner that blends regime priors with learned per-agent performance
weights.  The router updates weights after each trade outcome so the best
agent for current market conditions receives increasing allocation.

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
              LearnableEnsembleWeights → final_action, confidence
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
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
# Sprint 18 Phase 4.1: Learnable Ensemble Weights
# ---------------------------------------------------------------------------


class LearnableEnsembleWeights:
    """Online meta-learner for ensemble agent weighting.

    Combines two signals:
    1. **Regime prior** — one-hot regime detection from HMM/rule-based system
    2. **Performance EMA** — exponential moving average of each agent's reward

    The final weight vector is ``regime_prior * (1 - alpha) + perf_ema * alpha``
    where ``alpha`` increases from 0→max_alpha as more updates are received.

    Attributes
    ----------
    tags : list[str]
        Agent identifiers, e.g. ``["trend", "range", "volatile"]``.
    lr : float
        Learning rate for EMA update (default 0.1).
    max_alpha : float
        Maximum blend ratio for performance weights (default 0.6).
    min_updates : int
        Minimum updates before performance weights kick in (warm-up).
    """

    def __init__(
        self,
        tags: list[str] | None = None,
        lr: float = 0.1,
        max_alpha: float = 0.6,
        min_updates: int = 10,
    ) -> None:
        self.tags = tags or ["trend", "range", "volatile"]
        self.lr = lr
        self.max_alpha = max_alpha
        self.min_updates = min_updates

        # Per-agent EMA of reward (initialised equally)
        self._perf_ema: dict[str, float] = dict.fromkeys(self.tags, 0.0)
        self._update_count: dict[str, int] = dict.fromkeys(self.tags, 0)
        self._total_updates: int = 0

    @property
    def alpha(self) -> float:
        """Blend ratio: grows from 0 to max_alpha as updates accumulate."""
        if self._total_updates < self.min_updates:
            return 0.0
        ramp = min((self._total_updates - self.min_updates) / 50.0, 1.0)
        return self.max_alpha * ramp

    def update(self, tag: str, reward: float) -> None:
        """Update performance EMA for an agent after observing trade reward.

        Parameters
        ----------
        tag : str
            Agent tag, e.g. ``"trend"``.
        reward : float
            Observed reward (positive = profitable prediction).
        """
        if tag not in self._perf_ema:
            return
        old = self._perf_ema[tag]
        self._perf_ema[tag] = old + self.lr * (reward - old)
        self._update_count[tag] += 1
        self._total_updates += 1

    def get_weights(self, regime_prior: dict[str, float]) -> dict[str, float]:
        """Return blended weight vector for the current step.

        Parameters
        ----------
        regime_prior : dict[str, float]
            Regime-based weights (should sum to ~1).

        Returns
        -------
        dict[str, float]
            Blended weights (summing to 1).
        """
        alpha = self.alpha

        # Softmax over performance EMA to get a probability distribution
        emas = np.array([self._perf_ema.get(t, 0.0) for t in self.tags])
        # Temperature-scaled softmax (temperature=1 → standard softmax)
        ema_max = emas.max() if len(emas) > 0 else 0.0
        exp_emas = np.exp(emas - ema_max)  # numerical stability
        perf_weights = exp_emas / (exp_emas.sum() + 1e-8)

        # Regime prior (ensure same ordering)
        regime_arr = np.array([regime_prior.get(t, 1.0 / len(self.tags)) for t in self.tags])
        regime_sum = regime_arr.sum()
        if regime_sum > 0:
            regime_arr = regime_arr / regime_sum

        # Blend
        blended = (1.0 - alpha) * regime_arr + alpha * perf_weights

        # Normalise
        total = blended.sum()
        if total > 0:
            blended = blended / total

        return {t: float(w) for t, w in zip(self.tags, blended, strict=False)}

    # Persistence
    def export_state(self) -> dict[str, Any]:
        return {
            "perf_ema": dict(self._perf_ema),
            "update_count": dict(self._update_count),
            "total_updates": self._total_updates,
            "lr": self.lr,
            "max_alpha": self.max_alpha,
        }

    def load_state(self, state: dict[str, Any]) -> None:
        self._perf_ema = state.get("perf_ema", self._perf_ema)
        self._update_count = state.get("update_count", self._update_count)
        self._total_updates = state.get("total_updates", 0)
        if "lr" in state:
            self.lr = state["lr"]
        if "max_alpha" in state:
            self.max_alpha = state["max_alpha"]

    def save(self, path: str | Path) -> None:
        """Persist weights to a JSON file."""
        Path(path).write_text(json.dumps(self.export_state(), indent=2))
        logger.info("Ensemble weights saved to %s", path)

    @classmethod
    def load(cls, path: str | Path, **kwargs: Any) -> LearnableEnsembleWeights:
        """Load weights from a JSON file."""
        p = Path(path)
        instance = cls(**kwargs)
        if p.exists():
            state = json.loads(p.read_text())
            instance.load_state(state)
            logger.info(
                "Ensemble weights loaded from %s (%d updates)", path, instance._total_updates
            )
        return instance


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

# Legacy tag → model name mapping (kept for backward compat)
_TAG_TO_NAME = {
    "trend": "ppo_trend",
    "range": "ppo_range",
    "volatile": "ppo_volatile",
}

# Tag → regime feature column mapping (used for regime-based prior)
_TAG_TO_REGIME_COL = {
    "trend": "regime_trend",
    "range": "regime_range",
    "volatile": "regime_volatility",
}


# Sprint 19: build dynamic tag → model name mapping from specialist catalog
def _build_tag_to_name() -> dict[str, str]:
    """Build tag → model_name mapping from specialist catalog + legacy."""
    mapping = dict(_TAG_TO_NAME)  # start with legacy
    try:
        from .specialists import SPECIALIST_CATALOG

        for tag, spec in SPECIALIST_CATALOG.items():
            mapping[tag.value] = spec.model_name
    except ImportError:
        pass
    return mapping


class EnsembleRouter:
    """
    Routes predictions through multiple specialist DRL agents
    and produces a weighted consensus.

    Sprint 19: supports any number of specialist agents (regime, strategy,
    timeframe, risk style).  Falls back to the original 3 regime agents
    if no specialist models are found.

    Usage:
        router = EnsembleRouter()
        router.load_agents()  # loads all available specialist models

        result = router.predict("AAPL")
        print(result.final_action, result.final_confidence)

        # Or specify which specialists to use
        router = EnsembleRouter(agent_tags=["trend", "momentum", "conservative"])
    """

    def __init__(
        self,
        registry: ModelRegistry | None = None,
        config: MarketEnvConfig | None = None,
        min_regime_weight: float = 0.01,
        disagreement_hold_threshold: float = 0.3,
        learnable_weights: LearnableEnsembleWeights | None = None,
        agent_tags: list[str] | None = None,
    ):
        self.registry = registry or get_registry()
        self.config = config or DEFAULT_CONFIG
        self.min_regime_weight = min_regime_weight
        self.disagreement_hold_threshold = disagreement_hold_threshold

        self._agents: dict[str, DRLInference] = {}
        self._model_ids: dict[str, str] = {}
        self._loaded = False

        # Sprint 19: dynamic tag → model name from specialist catalog
        self._all_tag_names = _build_tag_to_name()
        # If specific tags requested, filter; otherwise try all available
        self._requested_tags = agent_tags  # None = auto-discover

        # Sprint 18 Phase 4.1: learnable ensemble weighting
        tags_for_learner = agent_tags or list(self._all_tag_names.keys())
        self._learnable = learnable_weights or LearnableEnsembleWeights(tags=tags_for_learner)

    @property
    def is_loaded(self) -> bool:
        return self._loaded and len(self._agents) > 0

    @property
    def n_agents(self) -> int:
        return len(self._agents)

    def load_agents(self) -> int:
        """
        Load all available specialist models from registry.

        Sprint 19: dynamically discovers models for any specialist tag
        (regime, strategy, timeframe, risk).  Falls back to legacy 3-agent
        mapping if specialist catalog is unavailable.

        Returns:
            Number of agents successfully loaded.
        """
        # Determine which tags to try
        if self._requested_tags:
            tags_to_try = {t: self._all_tag_names.get(t, f"ppo_{t}") for t in self._requested_tags}
        else:
            tags_to_try = dict(self._all_tag_names)

        loaded = 0
        for tag, model_name in tags_to_try.items():
            try:
                # Try both ppo_ and rppo_ prefixed names
                models = self.registry.list_models(name=model_name)
                if not models:
                    # Try alternate algorithm prefix
                    alt_name = (
                        model_name.replace("ppo_", "rppo_", 1)
                        if model_name.startswith("ppo_")
                        else model_name.replace("rppo_", "ppo_", 1)
                    )
                    models = self.registry.list_models(name=alt_name)
                if not models:
                    logger.debug("No model found for tag=%s name=%s", tag, model_name)
                    continue

                # Pick the latest model for this name
                latest = models[0]  # already sorted desc by created_at
                engine = DRLInference(registry=self.registry, config=self.config)
                algo = latest.algorithm if latest.algorithm else "PPO"
                success = engine.load_from_path(latest.model_path + ".zip", algorithm=algo)
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

        # Update learnable weights to match actually loaded agents
        loaded_tags = list(self._agents.keys())
        if loaded_tags and set(loaded_tags) != set(self._learnable.tags):
            self._learnable = LearnableEnsembleWeights(tags=loaded_tags)

        logger.info(
            "Ensemble: %d/%d agents loaded (%s)",
            loaded,
            len(tags_to_try),
            ", ".join(self._agents.keys()),
        )
        return loaded

    def _detect_regime_weights(self, df: pd.DataFrame) -> dict[str, float]:
        """
        Compute a prior weight for every loaded agent, then blend with
        learned performance weights via LearnableEnsembleWeights.

        Sprint 19: multi-domain prior computation:
        - Regime agents   → weight from regime detection columns (HMM)
        - Strategy agents  → heuristic from feature signals (RSI, MACD, BB)
        - Timeframe agents → equal prior (no natural preference)
        - Risk agents      → weighted by user risk_appetite

        Returns dict mapping tag → weight (sums to 1).
        """
        loaded_tags = list(self._agents.keys())
        last_row = df.iloc[-1] if len(df) > 0 else pd.Series(dtype=float)

        prior: dict[str, float] = {}

        for tag in loaded_tags:
            # --- Regime domain: use HMM regime columns ---
            if tag in _TAG_TO_REGIME_COL:
                col = _TAG_TO_REGIME_COL[tag]
                prior[tag] = max(float(last_row.get(col, 0.0)), 0.0)

            # --- Momentum: high when MACD histogram positive + volume surge ---
            elif tag == "momentum":
                macd_h = float(last_row.get("macd_hist_norm", 0.0))
                vol_r = float(last_row.get("volume_ratio", 1.0))
                prior[tag] = max(0.0, abs(macd_h) * min(vol_r, 2.0))

            # --- Mean-reversion: high when RSI at extremes ---
            elif tag == "meanrev":
                rsi = float(last_row.get("rsi", 50.0))
                prior[tag] = max(0.0, abs(rsi - 50.0) / 50.0)  # 0→1 at extremes

            # --- Breakout: high when BB width compressed + volume spike ---
            elif tag == "breakout":
                bb_w = float(last_row.get("bb_width", 0.03))
                vol_r = float(last_row.get("volume_ratio", 1.0))
                # Small width + high volume → breakout
                compression = max(0.0, 1.0 - bb_w / 0.05)  # <5% width = compressed
                prior[tag] = compression * min(vol_r / 1.5, 1.0)

            # --- Scalper: always ready with baseline weight ---
            elif tag == "scalper":
                prior[tag] = 0.3  # constant — always applicable

            # --- Swing: higher in stable trending environments ---
            elif tag == "swing":
                trend_str = abs(float(last_row.get("ema20_ema50_ratio", 0.0)))
                atr = float(last_row.get("atr_pct", 0.02))
                prior[tag] = trend_str * 10.0 * max(0.0, 1.0 - atr / 0.04)

            # --- Conservative: higher in volatile / uncertain markets ---
            elif tag == "conservative":
                vol_regime = float(last_row.get("regime_volatility", 0.0))
                atr = float(last_row.get("atr_pct", 0.02))
                prior[tag] = vol_regime * 0.5 + min(atr / 0.03, 1.0) * 0.5

            # --- Aggressive: higher in trending low-vol markets ---
            elif tag == "aggressive":
                trend_regime = float(last_row.get("regime_trend", 0.0))
                atr = float(last_row.get("atr_pct", 0.02))
                prior[tag] = trend_regime * max(0.0, 1.0 - atr / 0.04)

            # --- Unknown tag: equal prior ---
            else:
                prior[tag] = 0.5

        # Enforce minimum floor per agent (so no agent is completely silenced)
        n = max(len(prior), 1)
        floor = 0.10 / n  # each agent gets at least ~3% in a 3-agent setup
        for k in prior:
            prior[k] = max(prior[k], floor)

        # Normalize to sum=1
        total = sum(prior.values())
        if total > 0:
            prior = {k: v / total for k, v in prior.items()}
        else:
            prior = dict.fromkeys(prior, 1.0 / n)

        # Blend with learnable performance weights
        return self._learnable.get_weights(prior)

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
                1
                if v.prediction.action == ActionType.BUY  # type: ignore[union-attr]
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

    def batch_predict(self, symbols: list[str], risk_appetite: int = 5) -> list[EnsembleResult]:
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

    # ------------------------------------------------------------------
    # Sprint 18 Phase 4.1: Online learning feedback
    # ------------------------------------------------------------------

    def record_outcome(
        self,
        result: EnsembleResult,
        realised_pnl: float,
    ) -> None:
        """Feed trade outcome back to the meta-learner.

        Call this after a trade has closed to update per-agent performance
        weights.  Each agent that voted is updated proportionally to its
        contribution (regime weight) so that agents who contributed more
        to a losing trade are penalised more.

        Parameters
        ----------
        result : EnsembleResult
            The original ensemble prediction (contains per-agent votes).
        realised_pnl : float
            Signed PnL of the closed trade (positive = profit).
        """
        for vote in result.votes:
            if vote.prediction is None:
                continue
            # Reward = signed PnL × direction agreement
            # If agent predicted BUY and we made money → positive reward
            agent_dir = (
                1.0
                if vote.prediction.action == ActionType.BUY
                else (-1.0 if vote.prediction.action == ActionType.SELL else 0.0)
            )
            pnl_sign = 1.0 if realised_pnl > 0 else (-1.0 if realised_pnl < 0 else 0.0)
            agreement = agent_dir * pnl_sign  # +1 correct, -1 wrong, 0 neutral
            # Scale by confidence so confident wrong predictions are penalised more
            reward = agreement * vote.prediction.confidence
            self._learnable.update(vote.tag, reward)

        logger.debug(
            "Ensemble weights updated: pnl=%.4f → %s",
            realised_pnl,
            {t: f"{w:.3f}" for t, w in self._learnable._perf_ema.items()},
        )

    def save_weights(self, path: str | Path | None = None) -> None:
        """Persist learned ensemble weights."""
        if path is None:
            path = Path("models") / "ensemble_weights.json"
        self._learnable.save(path)

    def load_weights(self, path: str | Path | None = None) -> None:
        """Load previously learned ensemble weights."""
        if path is None:
            path = Path("models") / "ensemble_weights.json"
        p = Path(path)
        if p.exists():
            self._learnable = LearnableEnsembleWeights.load(p)
        else:
            logger.debug("No saved ensemble weights at %s, using fresh", path)

    def get_status(self) -> dict[str, Any]:
        """Return router status for UI display."""
        all_tags = set(self._all_tag_names.keys())
        return {
            "loaded": self._loaded,
            "n_agents": self.n_agents,
            "available_specialists": sorted(all_tags),
            "agents": {
                tag: {
                    "model_id": self._model_ids.get(tag, "N/A"),
                    "loaded": tag in self._agents,
                    "domain": self._get_agent_domain(tag),
                }
                for tag in all_tags
            },
        }

    @staticmethod
    def _get_agent_domain(tag: str) -> str:
        """Get the specialist domain for a tag."""
        try:
            from .specialists import get_specialist

            return get_specialist(tag).domain.value
        except (ImportError, KeyError, ValueError):
            return "regime"  # legacy default


# ---------------------------------------------------------------------------
# Module-level singleton for convenience
# ---------------------------------------------------------------------------

_router_instance: EnsembleRouter | None = None


def get_ensemble_router(
    agent_tags: list[str] | None = None,
) -> EnsembleRouter:
    """Get or create the global EnsembleRouter singleton.

    Uses the recommended trio (momentum + swing + conservative) by default.
    Pass *agent_tags* to override.
    """
    global _router_instance
    if _router_instance is None or not _router_instance.is_loaded:
        from .specialists import get_default_ensemble_tags

        tags = agent_tags or get_default_ensemble_tags()
        _router_instance = EnsembleRouter(agent_tags=tags)
        _router_instance.load_agents()
        _router_instance.load_weights()  # Sprint 18: restore learned weights
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
    "LearnableEnsembleWeights",
    "get_ensemble_router",
    "get_ensemble_predictions",
]
