"""Live Inference Module for FinPilot DRL agents.

Provides real-time predictions using trained models.
Handles feature preparation, model loading, and action interpretation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from .config import DEFAULT_CONFIG, MarketEnvConfig
from .model_registry import ModelRegistry, get_registry

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Trading action types from the DRL agent."""

    HOLD = 0
    BUY = 1
    SELL = 2

    @classmethod
    def from_continuous(cls, action: float, threshold: float = 0.3) -> "ActionType":
        """Convert continuous action to discrete ActionType."""
        if action > threshold:
            return cls.BUY
        elif action < -threshold:
            return cls.SELL
        else:
            return cls.HOLD

    @classmethod
    def from_discrete(cls, action: int) -> "ActionType":
        """Convert discrete action index to ActionType."""
        if action == 1:
            return cls.BUY
        elif action == 2:
            return cls.SELL
        else:
            return cls.HOLD


@dataclass
class PredictionResult:
    """Result of a DRL model prediction."""

    symbol: str
    action: ActionType
    raw_action: Union[float, int, np.ndarray]
    confidence: float

    # Position sizing suggestions
    suggested_position: float
    kelly_fraction: float

    # Risk metrics
    expected_return: Optional[float] = None
    risk_score: Optional[float] = None

    # Context
    regime: Optional[str] = None
    timestamp: Optional[str] = None
    model_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "action": self.action.name,
            "raw_action": (
                float(self.raw_action)
                if isinstance(self.raw_action, (np.ndarray, np.floating))
                else self.raw_action
            ),
            "confidence": self.confidence,
            "suggested_position": self.suggested_position,
            "kelly_fraction": self.kelly_fraction,
            "expected_return": self.expected_return,
            "risk_score": self.risk_score,
            "regime": self.regime,
            "timestamp": self.timestamp,
            "model_id": self.model_id,
        }

    @property
    def is_actionable(self) -> bool:
        """Whether the prediction suggests taking action."""
        return self.action != ActionType.HOLD and self.confidence > 0.5


class DRLInference:
    """
    Live inference engine for DRL models.

    Handles:
    - Model loading from registry
    - Feature preparation for inference
    - Action prediction with confidence scoring
    - Batch predictions for multiple symbols

    Example:
        >>> inference = DRLInference()
        >>> inference.load_model("finpilot_ppo")
        >>>
        >>> # Single prediction
        >>> result = inference.predict("AAPL")
        >>> print(f"{result.symbol}: {result.action.name} (conf={result.confidence:.2f})")
        >>>
        >>> # Batch prediction
        >>> results = inference.batch_predict(["AAPL", "MSFT", "NVDA"])
        >>> for r in results:
        ...     print(f"{r.symbol}: {r.action.name}")
    """

    def __init__(
        self, registry: Optional[ModelRegistry] = None, config: Optional[MarketEnvConfig] = None
    ):
        """
        Initialize the inference engine.

        Args:
            registry: Model registry instance (uses default if None)
            config: Environment config (uses default if None)
        """
        self.registry = registry or get_registry()
        self.config = config or DEFAULT_CONFIG
        self.model = None
        self.model_id: Optional[str] = None
        self.pipeline = None
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        """Check if a model is loaded."""
        return self._is_loaded and self.model is not None

    def load_model(
        self, model_name: str = "finpilot_ppo", version: str = "best", metric: str = "sharpe_ratio"
    ) -> bool:
        """
        Load a model for inference.

        Args:
            model_name: Name of the model to load
            version: "best", "latest", "active", or specific model_id
            metric: Metric to use for "best" selection

        Returns:
            True if loaded successfully
        """
        try:
            if version == "best":
                self.model = self.registry.load_best(model_name, metric=metric)
                metadata = self.registry.get_latest(model_name)
                self.model_id = metadata.model_id if metadata else None
            elif version == "latest":
                metadata = self.registry.get_latest(model_name)
                if metadata:
                    self.model = self.registry.load_model(metadata.model_id)
                    self.model_id = metadata.model_id
                else:
                    raise KeyError(f"No models found for: {model_name}")
            elif version == "active":
                self.model = self.registry.load_active(model_name)
                for m in self.registry.list_models(name=model_name):
                    if m.is_active:
                        self.model_id = m.model_id
                        break
            else:
                # Assume version is a model_id
                self.model = self.registry.load_model(version)
                self.model_id = version

            self._is_loaded = True
            logger.info(f"Model loaded: {self.model_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._is_loaded = False
            return False

    def load_from_path(self, model_path: str, algorithm: str = "PPO") -> bool:
        """
        Load a model directly from file path.

        Args:
            model_path: Path to the saved model
            algorithm: Algorithm type ("PPO" or "SAC")

        Returns:
            True if loaded successfully
        """
        try:
            if algorithm.upper() == "PPO":
                from stable_baselines3 import PPO

                self.model = PPO.load(model_path)
            elif algorithm.upper() == "SAC":
                from stable_baselines3 import SAC

                self.model = SAC.load(model_path)
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")

            self._is_loaded = True
            self.model_id = f"direct:{model_path}"
            logger.info(f"Model loaded from path: {model_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model from path: {e}")
            return False

    def _prepare_features(self, symbol: str) -> Optional[pd.DataFrame]:
        """Prepare features for a symbol."""
        from .data_loader import _add_placeholder_features, fetch_market_data

        try:
            df = fetch_market_data(symbol, period="3mo", interval="1d")
            if df.empty:
                logger.warning(f"No data for {symbol}")
                return None

            df = _add_placeholder_features(df)

            # Ensure all config columns exist
            for col in self.config.feature_columns:
                if col not in df.columns:
                    df[col] = 0.0

            return df

        except Exception as e:
            logger.error(f"Error preparing features for {symbol}: {e}")
            return None

    def _prepare_observation(self, df: pd.DataFrame) -> np.ndarray:
        """Convert DataFrame to model observation."""
        # Get the last row as observation
        last_row = df.iloc[-1]

        # Extract feature columns in order
        obs = np.array(
            [float(last_row.get(col, 0.0)) for col in self.config.feature_columns], dtype=np.float32
        )

        # Handle NaN/Inf
        obs = np.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)

        return obs

    def _compute_confidence(self, action: Union[float, int, np.ndarray], df: pd.DataFrame) -> float:
        """
        Compute confidence score for the prediction.

        Uses action magnitude and market regime alignment.
        """
        # Base confidence from action magnitude
        if isinstance(action, np.ndarray):
            action_val = float(action[0]) if action.size > 0 else 0.0
        else:
            action_val = float(action)

        # Normalize to 0-1 range (assuming action in [-1, 1])
        action_magnitude = abs(action_val)
        base_confidence = min(action_magnitude, 1.0)

        # Adjust by regime clarity
        regime_confidence = 0.0
        if "regime_trend" in df.columns:
            last_row = df.iloc[-1]
            regime_trend = float(last_row.get("regime_trend", 0))
            regime_range = float(last_row.get("regime_range", 0))
            regime_volatility = float(last_row.get("regime_volatility", 0))

            # Clear regime = higher confidence
            regime_max = max(regime_trend, regime_range, regime_volatility)
            regime_confidence = regime_max * 0.2  # Up to 20% boost

        # RSI extremes boost confidence for contrarian signals
        rsi_boost = 0.0
        if "rsi" in df.columns:
            rsi = float(df.iloc[-1].get("rsi", 50))
            if rsi > 70 and action_val < 0:  # Overbought + Sell
                rsi_boost = 0.1
            elif rsi < 30 and action_val > 0:  # Oversold + Buy
                rsi_boost = 0.1

        total_confidence = min(base_confidence + regime_confidence + rsi_boost, 1.0)
        return round(total_confidence, 3)

    def _compute_suggested_position(
        self, action: Union[float, int, np.ndarray], confidence: float, risk_appetite: int = 5
    ) -> Tuple[float, float]:
        """
        Compute suggested position size and Kelly fraction.

        Returns:
            (position_fraction, kelly_fraction)
        """
        if isinstance(action, np.ndarray):
            action_val = float(action[0]) if action.size > 0 else 0.0
        else:
            action_val = float(action)

        # Base position from action magnitude
        base_position = abs(action_val)

        # Scale by confidence
        confidence_scaled = base_position * confidence

        # Apply risk appetite (1-10 scale)
        risk_multiplier = risk_appetite / 10.0

        # Kelly fraction (simplified)
        # Full Kelly is often too aggressive, use fractional
        kelly = confidence_scaled * risk_multiplier * 0.5  # Half Kelly

        # Position as fraction of portfolio
        position = min(kelly * 2, 0.25)  # Max 25% per position

        return round(position, 3), round(kelly, 3)

    def _get_regime(self, df: pd.DataFrame) -> Optional[str]:
        """Extract current market regime from features."""
        if "regime" in df.columns:
            return str(df.iloc[-1]["regime"])

        if "regime_trend" in df.columns:
            last_row = df.iloc[-1]
            if float(last_row.get("regime_trend", 0)) > 0.5:
                return "trend"
            elif float(last_row.get("regime_volatility", 0)) > 0.5:
                return "volatility"
            else:
                return "range"

        return None

    def predict(self, symbol: str, df: Optional[pd.DataFrame] = None) -> Optional[PredictionResult]:
        """
        Generate a prediction for a single symbol.

        Args:
            symbol: Stock ticker symbol
            df: Pre-computed feature DataFrame (optional)

        Returns:
            PredictionResult or None if prediction fails
        """
        if not self.is_loaded:
            logger.warning("No model loaded. Call load_model() first.")
            return None

        # Prepare features if not provided
        if df is None:
            df = self._prepare_features(symbol)
            if df is None:
                return None

        try:
            # Guard against None model
            if self.model is None:
                raise RuntimeError("Model not loaded")

            # Get observation
            obs = self._prepare_observation(df)

            # Predict
            action, _states = self.model.predict(obs, deterministic=True)

            # Interpret action
            if isinstance(action, np.ndarray):
                action_val = float(action[0]) if action.size > 0 else 0.0
            else:
                action_val = float(action)

            action_type = ActionType.from_continuous(action_val)

            # Compute confidence
            confidence = self._compute_confidence(action, df)

            # Compute position sizing
            position, kelly = self._compute_suggested_position(
                action, confidence, risk_appetite=self.config.pilotshield.risk_appetite
            )

            # Get regime
            regime = self._get_regime(df)

            return PredictionResult(
                symbol=symbol,
                action=action_type,
                raw_action=action_val,
                confidence=confidence,
                suggested_position=position,
                kelly_fraction=kelly,
                regime=regime,
                timestamp=(
                    df.index[-1].isoformat()
                    if hasattr(df.index[-1], "isoformat")
                    else str(df.index[-1])
                ),
                model_id=self.model_id,
            )

        except Exception as e:
            logger.error(f"Prediction error for {symbol}: {e}")
            return None

    def batch_predict(self, symbols: List[str], parallel: bool = False) -> List[PredictionResult]:
        """
        Generate predictions for multiple symbols.

        Args:
            symbols: List of stock ticker symbols
            parallel: Use parallel processing (not yet implemented)

        Returns:
            List of PredictionResult objects
        """
        results = []

        for symbol in symbols:
            result = self.predict(symbol)
            if result is not None:
                results.append(result)

        # Sort by confidence (highest first)
        results.sort(key=lambda r: r.confidence, reverse=True)

        return results

    def get_top_signals(
        self,
        symbols: List[str],
        action_filter: Optional[ActionType] = None,
        min_confidence: float = 0.5,
        top_n: int = 10,
    ) -> List[PredictionResult]:
        """
        Get top trading signals from a list of symbols.

        Args:
            symbols: List of symbols to scan
            action_filter: Filter by action type (None = all)
            min_confidence: Minimum confidence threshold
            top_n: Maximum number of results

        Returns:
            Top N filtered and sorted predictions
        """
        all_predictions = self.batch_predict(symbols)

        # Filter by action type
        if action_filter is not None:
            all_predictions = [p for p in all_predictions if p.action == action_filter]

        # Filter by confidence
        filtered = [p for p in all_predictions if p.confidence >= min_confidence]

        # Sort by confidence
        filtered.sort(key=lambda p: p.confidence, reverse=True)

        return filtered[:top_n]

    def explain_prediction(self, result: PredictionResult) -> str:
        """
        Generate a human-readable explanation for a prediction.

        Args:
            result: PredictionResult to explain

        Returns:
            Explanation string
        """
        action_explanations = {
            ActionType.BUY: "ALIŞ sinyali",
            ActionType.SELL: "SATIŞ sinyali",
            ActionType.HOLD: "BEKLE sinyali",
        }

        base = f"{result.symbol}: {action_explanations[result.action]}"

        confidence_text = (
            "çok yüksek"
            if result.confidence > 0.8
            else (
                "yüksek"
                if result.confidence > 0.6
                else "orta" if result.confidence > 0.4 else "düşük"
            )
        )

        explanation = f"{base} (Güven: {confidence_text}, %{result.confidence*100:.0f})"

        if result.regime:
            regime_tr = {"trend": "Trend", "range": "Yatay", "volatility": "Volatil"}
            explanation += f" | Rejim: {regime_tr.get(result.regime, result.regime)}"

        if result.is_actionable:
            explanation += f" | Önerilen Pozisyon: %{result.suggested_position*100:.0f}"

        return explanation


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def get_drl_signals(
    symbols: List[str], model_name: str = "finpilot_ppo", min_confidence: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Quick function to get DRL signals for a list of symbols.

    Args:
        symbols: List of stock symbols
        model_name: Model to use
        min_confidence: Minimum confidence threshold

    Returns:
        List of signal dictionaries
    """
    inference = DRLInference()

    if not inference.load_model(model_name):
        logger.warning("Could not load model, returning empty signals")
        return []

    signals = inference.get_top_signals(symbols, min_confidence=min_confidence)

    return [s.to_dict() for s in signals]


def has_trained_model(model_name: str = "finpilot_ppo") -> bool:
    """Check if a trained model exists."""
    registry = get_registry()
    models = registry.list_models(name=model_name)
    return len(models) > 0


__all__ = ["DRLInference", "PredictionResult", "ActionType", "get_drl_signals", "has_trained_model"]
