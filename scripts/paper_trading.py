"""
Paper Trading Engine - DRL vs Scanner Performance Tracking
1 haftalık simülasyon ile gerçek test
"""

from datetime import datetime, timedelta

import pandas as pd
from drl.config import DEFAULT_CONFIG
from drl.feature_pipeline import FeatureFrame, FeaturePipeline
from scanner import add_indicators, fetch
from scanner.signals import analyze_price_momentum, check_volume_spike, safe_float
from stable_baselines3 import PPO


class PaperTradingEngine:
    """Sanal portföy ile performance tracking"""

    def __init__(self, initial_capital: float = 10000.0, strategy: str = "scanner"):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.strategy = strategy  # "scanner", "drl", "hybrid"

        self.positions: dict[str, dict] = {}  # {symbol: {shares, entry_price, entry_date}}
        self.trades: list[dict] = []
        self.daily_portfolio_value: list[dict] = []

        self.model = None
        if strategy in ["drl", "hybrid"]:
            try:
                self.model = PPO.load("models/ppo_balanced_20260217_171208.zip")
                print(f"✅ DRL model yüklendi ({strategy} mode)")
            except Exception as e:
                print(f"⚠️  DRL model yüklenemedi: {e}")
                self.strategy = "scanner"

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> dict:
        """Scanner ve/veya DRL sinyali üret"""

        df = add_indicators(df)
        latest = df.iloc[-1]

        # Scanner signal
        volume_spike = check_volume_spike(df)
        momentum = analyze_price_momentum(df)
        rsi = safe_float(latest.get("rsi", 50))
        close = safe_float(latest.get("Close", 0))
        ema_20 = safe_float(latest.get("ema_20", close))
        ema_50 = safe_float(latest.get("ema_50", close))

        score = 0
        if rsi < 35:
            score += 2
        elif rsi < 45:
            score += 1
        elif rsi > 65:
            score -= 2
        elif rsi > 55:
            score -= 1

        if close > ema_20 > ema_50:
            score += 2
        elif close > ema_20:
            score += 1
        elif close < ema_20 < ema_50:
            score -= 2
        elif close < ema_20:
            score -= 1

        if momentum.get("momentum_bias") == "BULLISH":
            score += 1
        elif momentum.get("momentum_bias") == "BEARISH":
            score -= 1
        if volume_spike:
            score += 1

        if score >= 2:
            scanner_action = "BUY"
        elif score <= -2:
            scanner_action = "SELL"
        else:
            scanner_action = "HOLD"

        scanner_confidence = min(0.9, abs(score) / 8 + 0.5)

        # DRL signal
        drl_action = "HOLD"
        drl_confidence = 0.5

        if self.model:
            try:
                drl_df = (
                    pd.DataFrame(
                        {
                            "close": df["Close"],
                            "ema_20": df.get("ema_20", df["Close"]),
                            "ema_50": df.get("ema_50", df["Close"]),
                            "ema_200": df.get("ema_200", df["Close"]),
                            "rsi": df.get("rsi", 50),
                            "macd": df.get("macd", 0),
                            "macd_signal": df.get("macd_signal", 0),
                            "macd_hist": df.get("macd_hist", 0),
                            "atr": df.get("atr", 1),
                            "bb_upper": df.get("bb_upper", df["Close"] * 1.02),
                            "bb_lower": df.get("bb_lower", df["Close"] * 0.98),
                            "volume": df["Volume"],
                            "volume_avg_20": df.get("vol_avg10", df["Volume"]),
                            "regime_trend": (df["Close"].pct_change(20) > 0).astype(int),
                            "regime_range": 0,
                            "regime_volatility": 0,
                            "cash_ratio": self.capital / self.initial_capital,
                            "position_ratio": len(self.positions) / 10,  # Max 10 pozisyon
                            "open_risk": 0.0,
                            "kelly_fraction": 0.25,
                        },
                        index=df.index,
                    )
                    .ffill()
                    .fillna(0)
                )

                pipeline = FeaturePipeline(DEFAULT_CONFIG)
                feature_frame = FeatureFrame(data=drl_df)
                pipeline.fit(feature_frame)
                transformed = pipeline.transform(feature_frame)
                state = transformed[-1]

                action, _ = self.model.predict(state, deterministic=True)
                action_val = action.flatten()[0]

                if action_val > 0.3:
                    drl_action = "BUY"
                elif action_val < -0.3:
                    drl_action = "SELL"
                else:
                    drl_action = "HOLD"

                drl_confidence = abs(action_val)

            except Exception as e:
                print(f"⚠️  DRL prediction error for {symbol}: {e}")

        # Final decision based on strategy
        if self.strategy == "scanner":
            final_action = scanner_action
            final_confidence = scanner_confidence
        elif self.strategy == "drl":
            final_action = drl_action
            final_confidence = drl_confidence
        else:  # hybrid
            if scanner_action == drl_action:
                final_action = scanner_action
                final_confidence = (scanner_confidence + drl_confidence) / 2
            else:
                # DRL ağırlığı daha fazla (%60)
                final_action = drl_action
                final_confidence = drl_confidence * 0.6 + scanner_confidence * 0.4

        return {
            "scanner_action": scanner_action,
            "scanner_confidence": scanner_confidence,
            "drl_action": drl_action,
            "drl_confidence": drl_confidence,
            "final_action": final_action,
            "final_confidence": final_confidence,
            "rsi": rsi,
            "close": close,
        }

    def execute_trade(self, symbol: str, action: str, price: float, date: datetime):
        """Trade gerçekleştir"""

        if action == "BUY" and symbol not in self.positions:
            # Pozisyon aç
            position_size = self.capital * 0.1  # Sermayenin %10'u
            if position_size < price:
                return  # Yetersiz sermaye

            shares = int(position_size / price)
            cost = shares * price * 1.001  # 0.1% commission

            if cost <= self.capital:
                self.capital -= cost
                self.positions[symbol] = {
                    "shares": shares,
                    "entry_price": price,
                    "entry_date": date,
                }

                self.trades.append(
                    {
                        "date": date,
                        "symbol": symbol,
                        "action": "BUY",
                        "shares": shares,
                        "price": price,
                        "cost": cost,
                    }
                )

        elif action == "SELL" and symbol in self.positions:
            # Pozisyon kapat
            position = self.positions[symbol]
            shares = position["shares"]
            revenue = shares * price * 0.999  # 0.1% commission

            self.capital += revenue

            profit = revenue - (shares * position["entry_price"])
            profit_pct = (price - position["entry_price"]) / position["entry_price"] * 100

            self.trades.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "action": "SELL",
                    "shares": shares,
                    "price": price,
                    "revenue": revenue,
                    "profit": profit,
                    "profit_pct": profit_pct,
                    "hold_days": (date - position["entry_date"]).days,
                }
            )

            del self.positions[symbol]

    def update_portfolio_value(self, date: datetime, prices: dict[str, float]):
        """Günlük portföy değeri güncelle"""

        position_value = sum(
            pos["shares"] * prices.get(symbol, pos["entry_price"])
            for symbol, pos in self.positions.items()
        )

        total_value = self.capital + position_value

        self.daily_portfolio_value.append(
            {
                "date": date,
                "cash": self.capital,
                "positions_value": position_value,
                "total_value": total_value,
                "return_pct": (total_value - self.initial_capital) / self.initial_capital * 100,
            }
        )

    def get_performance_metrics(self) -> dict:
        """Performance metrikleri hesapla"""

        if not self.daily_portfolio_value:
            return {}

        df = pd.DataFrame(self.daily_portfolio_value)

        total_return = (
            (df["total_value"].iloc[-1] - self.initial_capital) / self.initial_capital * 100
        )

        # Sharpe ratio (basitleştirilmiş)
        returns = df["return_pct"].diff().dropna()
        sharpe = returns.mean() / (returns.std() + 1e-6) if len(returns) > 1 else 0

        # Max drawdown
        cummax = df["total_value"].cummax()
        drawdown = (df["total_value"] - cummax) / cummax * 100
        max_drawdown = drawdown.min()

        # Win rate
        closed_trades = [t for t in self.trades if t["action"] == "SELL"]
        if closed_trades:
            wins = sum(1 for t in closed_trades if t["profit"] > 0)
            win_rate = wins / len(closed_trades) * 100
        else:
            win_rate = 0

        return {
            "total_return_pct": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": max_drawdown,
            "win_rate_pct": win_rate,
            "total_trades": len(closed_trades),
            "open_positions": len(self.positions),
            "final_capital": df["total_value"].iloc[-1],
        }


def run_paper_trading_day(
    engines: dict[str, PaperTradingEngine], symbols: list[str], test_date: datetime
) -> dict:
    """Bir günlük paper trading simülasyonu"""

    print(f"\n📅 {test_date.date()}")
    print("-" * 60)

    daily_signals = {}
    current_prices = {}

    for symbol in symbols:
        try:
            # Veri çek (test_date'e kadar)
            end_date = test_date
            end_date - timedelta(days=90)

            df = fetch(symbol, "1d", 90)
            if df.empty or len(df) < 30:
                continue

            # Test date'e kadarki veriyi kullan (simülasyon)
            df = df[df.index <= test_date]
            if len(df) < 30:
                continue

            current_price = float(df["Close"].iloc[-1])
            current_prices[symbol] = current_price

            # Her strateji için sinyal üret
            signals = {}
            for name, engine in engines.items():
                signal = engine.generate_signal(symbol, df)
                signals[name] = signal

                # Trade execution
                if signal["final_action"] in ["BUY", "SELL"]:
                    engine.execute_trade(symbol, signal["final_action"], current_price, test_date)

            daily_signals[symbol] = signals

        except Exception as e:
            print(f"⚠️  {symbol}: {e}")
            continue

    # Portföy değerlerini güncelle
    for engine in engines.values():
        engine.update_portfolio_value(test_date, current_prices)

    # Günlük özet
    for name, engine in engines.items():
        if engine.daily_portfolio_value:
            latest = engine.daily_portfolio_value[-1]
            print(f"   {name:8s}: ${latest['total_value']:,.0f} ({latest['return_pct']:+.1f}%)")

    return daily_signals


if __name__ == "__main__":
    print("=" * 70)
    print("📊 PAPER TRADING SETUP")
    print("=" * 70)

    # Test sembolleri
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

    # 3 strateji
    engines = {
        "Scanner": PaperTradingEngine(10000, "scanner"),
        "DRL": PaperTradingEngine(10000, "drl"),
        "Hybrid": PaperTradingEngine(10000, "hybrid"),
    }

    print("\n✅ Setup tamamlandı")
    print("   Sermaye: $10,000")
    print(f"   Semboller: {', '.join(symbols)}")
    print(f"   Stratejiler: {', '.join(engines.keys())}")

    print("\n" + "=" * 70)
    print("📝 PAPER TRADING KULLANIMI")
    print("=" * 70)

    print("""
Günlük Çalıştırma:
    python scripts/daily_paper_trading.py

Haftalık Rapor:
    python scripts/weekly_paper_trading_report.py

Manual Test (Bugün):
    python -c "from paper_trading import run_paper_trading_day, PaperTradingEngine
    from datetime import datetime

    engines = {
        'Scanner': PaperTradingEngine(10000, 'scanner'),
        'DRL': PaperTradingEngine(10000, 'drl'),
    }

    symbols = ['AAPL', 'MSFT', 'GOOGL']
    run_paper_trading_day(engines, symbols, datetime.now())

    for name, engine in engines.items():
        print(f'{name}: {engine.get_performance_metrics()}')"

Dosya kaydedildi: paper_trading.py
""")

    print("=" * 70)
    print("✅ PAPER TRADING ENGINE HAZIR!")
    print("=" * 70)
