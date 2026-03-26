"""Parallel Scanner - Scanner + DRL Hybrid Testing

Run scanner and DRL agent in parallel to compare performance.
Logs all signals to a database for A/B testing analysis.

Usage:
    python parallel_scanner.py --mode hybrid --model models/ppo_latest.zip
    python parallel_scanner.py --mode scanner_only
    python parallel_scanner.py --mode drl_only --model models/sac_best.zip
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

# DRL imports
from drl.config import DEFAULT_CONFIG
from drl.hybrid_engine import HybridEngine, HybridSignal, ScannerSignal

# Scanner imports
from scanner import (
    add_indicators,
    analyze_price_momentum,
    check_volume_spike,
    fetch,
    load_symbols,
)
from scanner.signals import safe_float

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ParallelScanner:
    """Orchestrates parallel testing between scanner and DRL."""

    def __init__(
        self,
        strategy_mode: str = "hybrid",
        model_path: str | None = None,
        drl_weight: float = 0.6,
        log_dir: str = "logs/parallel_testing",
    ):
        """
        Initialize parallel scanner.

        Args:
            strategy_mode: "scanner_only", "drl_only", or "hybrid"
            model_path: Path to trained DRL model
            drl_weight: Weight for DRL predictions in hybrid mode
            log_dir: Directory for saving test results
        """
        self.strategy_mode = strategy_mode
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize hybrid engine
        self.hybrid_engine = HybridEngine(
            env_config=DEFAULT_CONFIG,
            model_path=model_path,
            strategy_mode=strategy_mode,
            drl_weight=drl_weight,
        )

        # Results storage
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results: list[dict[str, Any]] = []

        logger.info(f"🚀 Parallel Scanner initialized - Mode: {strategy_mode}")
        logger.info(f"📁 Logging to: {self.log_dir / self.session_id}")

    def scan_symbol(
        self, symbol: str, period: str = "1d", lookback: int = 90
    ) -> HybridSignal | None:
        """
        Scan a single symbol and get hybrid signal.

        Args:
            symbol: Stock ticker
            period: Data period (1d, 1h, etc.)
            lookback: Days of historical data

        Returns:
            HybridSignal or None if scan failed
        """
        try:
            # Fetch data with indicators
            df = fetch(symbol, period, lookback)
            if df.empty or len(df) < 30:
                logger.warning(f"Insufficient data for {symbol}")
                return None

            df = add_indicators(df)

            # Generate scanner signal
            scanner_signal = self._generate_scanner_signal(symbol, df)

            # Process through hybrid engine
            hybrid_signal = self.hybrid_engine.process_signal(
                scanner_signal=scanner_signal,
                market_data=df,
            )

            # Log result
            self.results.append(hybrid_signal.to_dict())

            return hybrid_signal

        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            return None

    def _generate_scanner_signal(self, symbol: str, df: pd.DataFrame) -> ScannerSignal:
        """Generate traditional scanner signal from indicators."""
        latest = df.iloc[-1]

        # Check signal conditions
        volume_spike = check_volume_spike(df)
        momentum = analyze_price_momentum(df)
        trend_strength = self._check_trend_strength(df)

        # Calculate score
        score = 0
        reasons = []

        # Volume condition
        if volume_spike:
            score += 1
            reasons.append("Volume spike detected")

        # Momentum condition
        if momentum.get("momentum_bias") == "BULLISH":
            score += 1
            reasons.append("Bullish momentum")
        elif momentum.get("momentum_bias") == "BEARISH":
            score -= 1
            reasons.append("Bearish momentum")

        # Trend condition
        if trend_strength > 0.6:
            score += 1
            reasons.append("Strong uptrend")
        elif trend_strength < -0.6:
            score -= 1
            reasons.append("Strong downtrend")

        # RSI condition
        rsi = safe_float(latest.get("rsi", 50))
        if rsi < 30:
            score += 1
            reasons.append("RSI oversold")
        elif rsi > 70:
            score -= 1
            reasons.append("RSI overbought")

        # Determine action
        if score >= 2:
            action = "BUY"
            confidence = min(0.95, 0.5 + (score / 8))
        elif score <= -2:
            action = "SELL"
            confidence = min(0.95, 0.5 + (abs(score) / 8))
        else:
            action = "HOLD"
            confidence = 0.5

        return ScannerSignal(
            symbol=symbol,
            action=action,
            score=abs(score),
            confidence=confidence,
            reason=" | ".join(reasons) if reasons else "No clear signal",
            timestamp=datetime.now().isoformat(),
            metadata={
                "rsi": rsi,
                "volume_spike": volume_spike,
                "trend_strength": trend_strength,
            },
        )

    def _check_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate trend strength (-1 to +1)."""
        if len(df) < 50:
            return 0.0

        latest = df.iloc[-1]
        ema_20 = safe_float(latest.get("ema_20", 0))
        ema_50 = safe_float(latest.get("ema_50", 0))
        close = safe_float(latest.get("Close", 0))

        if ema_20 == 0 or ema_50 == 0:
            return 0.0

        # Calculate trend score
        if ema_20 > ema_50 and close > ema_20:
            return 0.8  # Strong uptrend
        elif ema_20 < ema_50 and close < ema_20:
            return -0.8  # Strong downtrend
        elif close > ema_20:
            return 0.4  # Mild uptrend
        elif close < ema_20:
            return -0.4  # Mild downtrend

        return 0.0

    def scan_watchlist(self, symbols: list[str]) -> pd.DataFrame:
        """
        Scan multiple symbols and return results DataFrame.

        Args:
            symbols: List of stock tickers

        Returns:
            DataFrame with all signals
        """
        logger.info(f"📊 Scanning {len(symbols)} symbols...")

        signals = []
        for symbol in symbols:
            signal = self.scan_symbol(symbol)
            if signal:
                signals.append(signal)
                self._print_signal_summary(signal)

        # Convert to DataFrame
        if signals:
            df = pd.DataFrame([s.to_dict() for s in signals])
            self._save_results(df)
            return df

        logger.warning("No valid signals generated")
        return pd.DataFrame()

    def _print_signal_summary(self, signal: HybridSignal) -> None:
        """Print formatted signal summary."""
        agreement_icon = "✅" if signal.agreement else "⚠️"
        action_icon = {"BUY": "📈", "SELL": "📉", "HOLD": "⏸️"}.get(signal.final_action, "")

        print(f"\n{agreement_icon} {signal.symbol}")
        print(f"   Scanner: {signal.scanner_signal.action} (score: {signal.scanner_signal.score})")

        if signal.drl_prediction:
            print(
                f"   DRL:     {signal.drl_prediction.action.name} (conf: {signal.drl_prediction.confidence:.2%})"
            )

        print(
            f"   {action_icon} FINAL: {signal.final_action} (conf: {signal.final_confidence:.2%})"
        )
        print(f"   Position: {signal.risk_adjusted_size:.2%}")

    def _save_results(self, df: pd.DataFrame) -> None:
        """Save results to CSV and JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save CSV
        csv_path = self.log_dir / f"{self.session_id}_signals.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"💾 Saved results to {csv_path}")

        # Save JSON with metadata
        json_path = self.log_dir / f"{self.session_id}_metadata.json"
        metadata = {
            "session_id": self.session_id,
            "timestamp": timestamp,
            "strategy_mode": self.strategy_mode,
            "total_signals": len(df),
            "buy_signals": len(df[df["final_action"] == "BUY"]),
            "sell_signals": len(df[df["final_action"] == "SELL"]),
            "hold_signals": len(df[df["final_action"] == "HOLD"]),
            "agreement_rate": float(df["agreement"].mean()) if len(df) > 0 else 0.0,
            "avg_confidence": float(df["final_confidence"].mean()) if len(df) > 0 else 0.0,
        }

        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"📋 Metadata: {metadata}")

    def generate_comparison_report(self) -> dict[str, Any]:
        """Generate detailed comparison report between scanner and DRL."""
        return self.hybrid_engine.get_performance_report()


def main():
    parser = argparse.ArgumentParser(description="Parallel Scanner - Scanner + DRL Testing")

    parser.add_argument(
        "--mode",
        choices=["scanner_only", "drl_only", "hybrid"],
        default="hybrid",
        help="Testing mode",
    )

    parser.add_argument(
        "--model", type=str, help="Path to trained DRL model (required for drl/hybrid)"
    )

    parser.add_argument(
        "--symbols",
        type=str,
        help="Comma-separated symbols to scan (default: load from symbols.txt)",
    )

    parser.add_argument("--drl-weight", type=float, default=0.6, help="DRL weight in hybrid mode")

    parser.add_argument(
        "--log-dir", type=str, default="logs/parallel_testing", help="Log directory"
    )

    args = parser.parse_args()

    # Validate model path for DRL modes
    if args.mode in ["drl_only", "hybrid"] and not args.model:
        parser.error(f"--model is required for {args.mode} mode")

    # Load symbols
    symbols = [s.strip() for s in args.symbols.split(",")] if args.symbols else load_symbols()

    logger.info(f"🎯 Running in {args.mode} mode")
    logger.info(f"📊 Symbols: {len(symbols)}")

    # Initialize and run scanner
    scanner = ParallelScanner(
        strategy_mode=args.mode,
        model_path=args.model,
        drl_weight=args.drl_weight,
        log_dir=args.log_dir,
    )

    results_df = scanner.scan_watchlist(symbols)

    # Generate report
    if not results_df.empty:
        print("\n" + "=" * 60)
        print("📊 SCAN SUMMARY")
        print("=" * 60)
        print(f"Total Signals: {len(results_df)}")
        print(f"BUY Signals:   {len(results_df[results_df['final_action'] == 'BUY'])}")
        print(f"SELL Signals:  {len(results_df[results_df['final_action'] == 'SELL'])}")
        print(f"HOLD Signals:  {len(results_df[results_df['final_action'] == 'HOLD'])}")
        print(f"Agreement Rate: {results_df['agreement'].mean():.1%}")
        print(f"Avg Confidence: {results_df['final_confidence'].mean():.1%}")
        print("=" * 60)


if __name__ == "__main__":
    main()
