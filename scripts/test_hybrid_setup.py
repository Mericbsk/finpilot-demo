"""Quick Start Script - Test DRL Integration

Test the hybrid engine without running full parallel scanner.
Useful for validating setup.

Usage:
    python scripts/test_hybrid_setup.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from drl.config import DEFAULT_CONFIG
from drl.hybrid_engine import HybridEngine, ScannerSignal
from scanner import add_indicators, fetch


def test_hybrid_engine():
    """Test hybrid engine with sample data."""
    print("🧪 Testing Hybrid Engine Setup...")
    print("=" * 60)

    # Initialize engine in scanner-only mode (no model required)
    print("\n1️⃣ Testing Scanner-Only Mode...")
    engine = HybridEngine(
        env_config=DEFAULT_CONFIG,
        strategy_mode="scanner_only",
    )
    print("✅ Scanner-only engine initialized")

    # Create sample scanner signal
    test_signal = ScannerSignal(
        symbol="AAPL",
        action="BUY",
        score=3,
        confidence=0.75,
        reason="Volume spike + RSI oversold + Bullish momentum",
        metadata={"rsi": 28, "volume_spike": True},
    )

    # Fetch sample data
    print("\n2️⃣ Fetching market data for AAPL...")
    df = fetch("AAPL", "1d", 60)
    if df.empty:
        print("❌ Failed to fetch data")
        return False

    df = add_indicators(df)
    print(f"✅ Fetched {len(df)} days of data with indicators")

    # Process signal
    print("\n3️⃣ Processing signal through hybrid engine...")
    hybrid_signal = engine.process_signal(
        scanner_signal=test_signal,
        market_data=df,
    )

    print("\n📊 HYBRID SIGNAL RESULTS:")
    print("-" * 60)
    print(f"Symbol:            {hybrid_signal.symbol}")
    print(f"Scanner Action:    {hybrid_signal.scanner_signal.action}")
    print(f"Scanner Score:     {hybrid_signal.scanner_signal.score}/4")
    print(f"DRL Prediction:    {hybrid_signal.drl_prediction.action.name if hybrid_signal.drl_prediction else 'N/A'}")
    print(f"Final Action:      {hybrid_signal.final_action}")
    print(f"Final Confidence:  {hybrid_signal.final_confidence:.1%}")
    print(f"Agreement:         {'✅ YES' if hybrid_signal.agreement else '⚠️ NO'}")
    print(f"Position Size:     {hybrid_signal.position_size:.2%}")
    print(f"Risk Adjusted:     {hybrid_signal.risk_adjusted_size:.2%}")
    print("-" * 60)

    print("\n✅ Hybrid engine test PASSED!")
    print("\n📝 Next Steps:")
    print("   1. Train DRL model: python ml_agent.py --algorithm PPO --timesteps 50000")
    print("   2. Test with DRL:   python parallel_scanner.py --mode hybrid --model models/ppo_latest.zip")
    print("   3. View dashboard:  streamlit run drl_comparison_dashboard.py")

    return True


def test_requirements():
    """Check if required packages are installed."""
    print("\n🔍 Checking Requirements...")
    print("=" * 60)

    required_packages = {
        "scanner": "✅ Scanner package",
        "drl": "✅ DRL package",
        "pandas": "✅ Pandas",
        "numpy": "✅ NumPy",
    }

    missing = []
    for package, message in required_packages.items():
        try:
            __import__(package)
            print(message)
        except ImportError:
            print(f"❌ {package} not found")
            missing.append(package)

    # Optional packages
    print("\n📦 Optional Packages (for full DRL):")
    optional_packages = {
        "stable_baselines3": "Stable-Baselines3 (for DRL training)",
        "gymnasium": "Gymnasium (for DRL environment)",
    }

    for package, description in optional_packages.items():
        try:
            __import__(package)
            print(f"✅ {description}")
        except ImportError:
            print(f"⚠️  {description} - Install with: pip install -r requirements-rl.txt")

    if missing:
        print(f"\n❌ Missing required packages: {', '.join(missing)}")
        return False

    print("\n✅ All required packages installed!")
    return True


if __name__ == "__main__":
    print("🚀 FinPilot DRL Integration - Setup Test")
    print("=" * 60)

    # Check requirements
    if not test_requirements():
        print("\n❌ Please install missing packages first")
        sys.exit(1)

    # Test hybrid engine
    try:
        if test_hybrid_engine():
            print("\n🎉 SUCCESS! Hybrid engine is ready.")
            sys.exit(0)
        else:
            print("\n❌ Test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
