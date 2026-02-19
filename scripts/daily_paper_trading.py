#!/usr/bin/env python3
"""
Günlük Paper Trading Script
Her gün çalıştırılacak - cron job ile otomatize edilebilir
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from paper_trading import PaperTradingEngine, run_paper_trading_day

# Config
SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
STATE_FILE = Path("logs/paper_trading/state.json")
RESULTS_FILE = Path("logs/paper_trading/daily_results.json")


def load_state():
    """Önceki durumu yükle"""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "start_date": datetime.now().isoformat(),
        "strategies": {
            "Scanner": {"capital": 10000, "positions": {}, "trades": []},
            "DRL": {"capital": 10000, "positions": {}, "trades": []},
            "Hybrid": {"capital": 10000, "positions": {}, "trades": []},
        },
    }


def save_state(engines):
    """Durumu kaydet"""
    state = {"last_update": datetime.now().isoformat(), "strategies": {}}

    for name, engine in engines.items():
        state["strategies"][name] = {
            "capital": engine.capital,
            "positions": engine.positions,
            "trades": [
                {
                    **t,
                    "date": t["date"].isoformat()
                    if isinstance(t.get("date"), datetime)
                    else t.get("date"),
                }
                for t in engine.trades
            ],
            "daily_values": engine.daily_portfolio_value,
        }

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def main():
    print("=" * 70)
    print("📊 GÜNLÜK PAPER TRADING")
    print("=" * 70)
    print(f"🗓️  {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Engine'leri oluştur
    engines = {
        "Scanner": PaperTradingEngine(10000, "scanner"),
        "DRL": PaperTradingEngine(10000, "drl"),
        "Hybrid": PaperTradingEngine(10000, "hybrid"),
    }

    # Önceki state'i yükle (varsa)
    state = load_state()
    for name, engine in engines.items():
        if name in state["strategies"]:
            prev = state["strategies"][name]
            engine.capital = prev.get("capital", 10000)
            engine.positions = prev.get("positions", {})
            # Trades restore (opsiyonel)

    # Bugünkü scan
    print(f"\n📊 Semboller: {', '.join(SYMBOLS)}")

    daily_signals = run_paper_trading_day(engines, SYMBOLS, datetime.now())

    # Sonuçlar
    print("\n" + "=" * 70)
    print("📈 GÜNLÜK SONUÇLAR")
    print("=" * 70)

    results = {}
    for name, engine in engines.items():
        metrics = engine.get_performance_metrics()
        results[name] = metrics

        print(f"\n{name}:")
        if metrics:
            print(f"   Return:      {metrics['total_return_pct']:+.2f}%")
            print(f"   Sharpe:      {metrics['sharpe_ratio']:.2f}")
            print(f"   Max DD:      {metrics['max_drawdown_pct']:.2f}%")
            print(f"   Win Rate:    {metrics['win_rate_pct']:.0f}%")
            print(f"   Trades:      {metrics['total_trades']}")
            print(f"   Open Pos:    {metrics['open_positions']}")
        else:
            print("   Henüz veri yok")

    # State kaydet
    save_state(engines)

    # Sonuçları kaydet
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            all_results = json.load(f)
    else:
        all_results = []

    all_results.append(
        {
            "date": datetime.now().isoformat(),
            "results": results,
            "signals": daily_signals,
        }
    )

    with open(RESULTS_FILE, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n💾 State kaydedildi: {STATE_FILE}")
    print(f"💾 Results kaydedildi: {RESULTS_FILE}")

    print("\n" + "=" * 70)
    print("✅ GÜNLÜK PAPER TRADING TAMAMLANDI")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
