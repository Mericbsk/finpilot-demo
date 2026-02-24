"""Hybrid Trading Engine - Scanner + DRL Integration

Combines rule-based scanner signals with DRL agent predictions for parallel testing.
Enables A/B testing between traditional signals and ML-based strategies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from .config import MarketEnvConfig
from .inference import DRLInference, PredictionResult

logger = logging.getLogger(__name__)


@dataclass
class ScannerSignal:
    """Signal from traditional rule-based scanner."""

    symbol: str
    action: str  # "BUY", "SELL", "HOLD"
    score: int
    confidence: float
    reason: str
    timestamp: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HybridSignal:
    """Combined signal from both scanner and DRL agent."""

    symbol: str
    scanner_signal: ScannerSignal
    drl_prediction: PredictionResult | None

    # Consensus decision
    final_action: str
    final_confidence: float
    agreement: bool

    # Position sizing
    position_size: float
    risk_adjusted_size: float

    # Metadata
    timestamp: str
    strategy_mode: str  # "scanner_only", "drl_only", "hybrid"

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "scanner_action": self.scanner_signal.action,
            "scanner_score": self.scanner_signal.score,
            "drl_action": self.drl_prediction.action.name if self.drl_prediction else None,
            "drl_confidence": self.drl_prediction.confidence if self.drl_prediction else None,
            "final_action": self.final_action,
            "final_confidence": self.final_confidence,
            "agreement": self.agreement,
            "position_size": self.position_size,
            "risk_adjusted_size": self.risk_adjusted_size,
            "timestamp": self.timestamp,
            "strategy_mode": self.strategy_mode,
        }


class HybridEngine:
    """Orchestrates parallel testing between scanner and DRL agent."""

    def __init__(
        self,
        env_config: MarketEnvConfig | None = None,
        model_path: str | None = None,
        strategy_mode: str = "hybrid",
        drl_weight: float = 0.5,
        agreement_threshold: float = 0.7,
    ):
        """
        Initialize hybrid engine.

        Args:
            env_config: DRL environment configuration
            model_path: Path to trained DRL model
            strategy_mode: "scanner_only", "drl_only", or "hybrid"
            drl_weight: Weight for DRL in hybrid mode (0.0-1.0)
            agreement_threshold: Minimum confidence for disagreement handling
        """
        self.strategy_mode = strategy_mode
        self.drl_weight = drl_weight
        self.agreement_threshold = agreement_threshold

        self.inference_engine: DRLInference | None = None
        if strategy_mode in ["drl_only", "hybrid"] and model_path:
            try:
                self.inference_engine = DRLInference(config=env_config)
                self.inference_engine.load_from_path(model_path)
                logger.info(f"✅ DRL inference engine loaded from {model_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load DRL model: {e}")
                if strategy_mode == "drl_only":
                    raise

        # Performance tracking
        self._performance: dict[str, list[float]] = {
            "scanner_returns": [],
            "drl_returns": [],
            "hybrid_returns": [],
        }

    def process_signal(
        self,
        scanner_signal: ScannerSignal,
        market_data: pd.DataFrame,
        features: dict[str, float] | None = None,
    ) -> HybridSignal:
        """
        Process a scanner signal and optionally get DRL prediction.

        Args:
            scanner_signal: Signal from rule-based scanner
            market_data: Historical price data
            features: Precomputed features (optional)

        Returns:
            HybridSignal with consensus decision
        """
        timestamp = datetime.now().isoformat()
        drl_prediction: PredictionResult | None = None

        # Get DRL prediction if enabled
        if self.strategy_mode in ["drl_only", "hybrid"] and self.inference_engine:
            try:
                drl_prediction = self.inference_engine.predict(
                    symbol=scanner_signal.symbol,
                    features=features or self._extract_features(market_data),
                )
            except Exception as e:
                logger.warning(f"DRL prediction failed for {scanner_signal.symbol}: {e}")

        # Decision logic based on strategy mode
        if self.strategy_mode == "scanner_only":
            final_action = scanner_signal.action
            final_confidence = scanner_signal.confidence
            agreement = True

        elif self.strategy_mode == "drl_only" and drl_prediction:
            final_action = drl_prediction.action.name
            final_confidence = drl_prediction.confidence
            agreement = True

        elif self.strategy_mode == "hybrid" and drl_prediction:
            final_action, final_confidence, agreement = self._hybrid_consensus(
                scanner_signal, drl_prediction
            )

        else:
            # Fallback to scanner
            final_action = scanner_signal.action
            final_confidence = scanner_signal.confidence
            agreement = False

        # Position sizing
        position_size = self._calculate_position_size(
            scanner_signal, drl_prediction, final_confidence
        )
        risk_adjusted_size = self._apply_risk_adjustment(position_size, final_confidence)

        return HybridSignal(
            symbol=scanner_signal.symbol,
            scanner_signal=scanner_signal,
            drl_prediction=drl_prediction,
            final_action=final_action,
            final_confidence=final_confidence,
            agreement=agreement,
            position_size=position_size,
            risk_adjusted_size=risk_adjusted_size,
            timestamp=timestamp,
            strategy_mode=self.strategy_mode,
        )

    def _hybrid_consensus(
        self, scanner_signal: ScannerSignal, drl_prediction: PredictionResult
    ) -> tuple[str, float, bool]:
        """
        Determine consensus between scanner and DRL.

        Returns:
            (final_action, final_confidence, agreement)
        """
        scanner_action = scanner_signal.action
        drl_action = drl_prediction.action.name

        # Check agreement
        if scanner_action == drl_action:
            # Both agree - high confidence
            combined_confidence = (
                scanner_signal.confidence * (1 - self.drl_weight)
                + drl_prediction.confidence * self.drl_weight
            )
            return scanner_action, combined_confidence, True

        # Disagreement - use weighted voting
        if scanner_signal.confidence > self.agreement_threshold:
            # High scanner confidence
            return scanner_action, scanner_signal.confidence * 0.8, False

        if drl_prediction.confidence > self.agreement_threshold:
            # High DRL confidence
            return drl_action, drl_prediction.confidence * 0.8, False

        # Low confidence on both - hold
        return "HOLD", 0.5, False

    def _calculate_position_size(
        self,
        scanner_signal: ScannerSignal,
        drl_prediction: PredictionResult | None,
        confidence: float,
    ) -> float:
        """Calculate base position size (0.0 - 1.0)."""
        if drl_prediction:
            # Use DRL's suggested position
            return abs(drl_prediction.suggested_position)

        # Use scanner score mapping
        score_mapping = {1: 0.25, 2: 0.5, 3: 0.75, 4: 1.0}
        return score_mapping.get(scanner_signal.score, 0.25)

    def _apply_risk_adjustment(self, position_size: float, confidence: float) -> float:
        """Apply risk-adjusted scaling to position size."""
        # Kelly criterion-like adjustment
        risk_factor = max(0.5, confidence)
        return position_size * risk_factor

    def _extract_features(self, df: pd.DataFrame) -> dict[str, float]:
        """Extract features from market data for DRL inference."""
        if len(df) < 2:
            return {}

        latest = df.iloc[-1]
        features = {
            "close": float(latest.get("Close", 0)),
            "volume": float(latest.get("Volume", 0)),
            "rsi": float(latest.get("rsi", 50)),
            "macd": float(latest.get("macd", 0)),
            "atr": float(latest.get("atr", 0)),
        }

        # Add EMA features if available
        for ema in ["ema_20", "ema_50", "ema_200"]:
            if ema in latest:
                features[ema] = float(latest[ema])

        return features

    def get_performance_report(self) -> dict[str, Any]:
        """Generate performance comparison report."""
        report = {
            "scanner_avg_return": (
                np.mean(self._performance["scanner_returns"])
                if self._performance["scanner_returns"]
                else 0.0
            ),
            "drl_avg_return": (
                np.mean(self._performance["drl_returns"])
                if self._performance["drl_returns"]
                else 0.0
            ),
            "hybrid_avg_return": (
                np.mean(self._performance["hybrid_returns"])
                if self._performance["hybrid_returns"]
                else 0.0
            ),
            "total_signals": len(self._performance["scanner_returns"]),
        }

        # Calculate improvement
        if report["scanner_avg_return"] != 0:
            report["hybrid_improvement_pct"] = (
                (report["hybrid_avg_return"] - report["scanner_avg_return"])
                / abs(report["scanner_avg_return"])
                * 100
            )

        return report


__all__ = ["HybridEngine", "ScannerSignal", "HybridSignal"]
