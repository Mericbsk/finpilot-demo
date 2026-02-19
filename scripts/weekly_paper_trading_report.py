#!/usr/bin/env python3
"""
Haftalık Paper Trading Raporu
1 haftalık performans karşılaştırması
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

STATE_FILE = Path("logs/paper_trading/state.json")
RESULTS_FILE = Path("logs/paper_trading/daily_results.json")


def generate_weekly_report():
    """Haftalık rapor oluştur"""

    print("=" * 70)
    print("📊 HAFTALIK PAPER TRADING RAPORU")
    print("=" * 70)
    print(f"🗓️  {datetime.now().strftime('%Y-%m-%d')}\n")

    # Sonuçları yükle
    if not RESULTS_FILE.exists():
        print("❌ Henüz veri yok. Günlük scan çalıştırın.")
        return

    with open(RESULTS_FILE) as f:
        all_results = json.load(f)

    if not all_results:
        print("❌ Henüz veri yok.")
        return

    print(f"📅 Toplam {len(all_results)} günlük veri\n")

    # DataFrame'e dönüştür
    data = []
    for entry in all_results:
        date = entry["date"]
        for strategy, metrics in entry["results"].items():
            if metrics:
                data.append({"date": date, "strategy": strategy, **metrics})

    if not data:
        print("❌ Metrik verisi yok.")
        return

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])

    # Strateji bazında özet
    print("=" * 70)
    print("📈 STRATEJİ PERFORMANSLARI")
    print("=" * 70)

    for strategy in df["strategy"].unique():
        strategy_df = df[df["strategy"] == strategy].iloc[-1]  # En son değer

        print(f"\n🎯 {strategy}:")
        print(f"   Total Return:    {strategy_df['total_return_pct']:+.2f}%")
        print(f"   Sharpe Ratio:    {strategy_df['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown:    {strategy_df['max_drawdown_pct']:.2f}%")
        print(f"   Win Rate:        {strategy_df['win_rate_pct']:.0f}%")
        print(f"   Total Trades:    {strategy_df['total_trades']:.0f}")
        print(f"   Final Capital:   ${strategy_df['final_capital']:,.0f}")

    # Karşılaştırma
    print("\n" + "=" * 70)
    print("🏆 KARŞILAŞTIRMA")
    print("=" * 70)

    latest = df.groupby("strategy").last()

    best_return = latest["total_return_pct"].idxmax()
    best_sharpe = latest["sharpe_ratio"].idxmax()
    best_drawdown = latest["max_drawdown_pct"].idxmax()  # En az negatif

    print(
        f"\n   En İyi Return:    {best_return} ({latest.loc[best_return, 'total_return_pct']:+.2f}%)"
    )
    print(f"   En İyi Sharpe:    {best_sharpe} ({latest.loc[best_sharpe, 'sharpe_ratio']:.2f})")
    print(
        f"   En İyi DD:        {best_drawdown} ({latest.loc[best_drawdown, 'max_drawdown_pct']:.2f}%)"
    )

    # Günlük portfolio value grafiği
    if len(all_results) > 1:
        print("\n" + "=" * 70)
        print("📊 PORTFOLIO VALUE TRENDİ")
        print("=" * 70)

        plt.figure(figsize=(12, 6))

        for strategy in df["strategy"].unique():
            strategy_df = df[df["strategy"] == strategy].sort_values("date")
            plt.plot(
                strategy_df["date"],
                strategy_df["final_capital"],
                label=strategy,
                marker="o",
                linewidth=2,
            )

        plt.axhline(y=10000, color="gray", linestyle="--", label="Initial Capital")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value ($)")
        plt.title("Paper Trading Performance - Scanner vs DRL vs Hybrid")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        chart_file = Path("logs/paper_trading/weekly_chart.png")
        plt.savefig(chart_file, dpi=150, bbox_inches="tight")
        print(f"\n   📊 Grafik kaydedildi: {chart_file}")
        plt.close()

    # Detaylı tablo
    print("\n" + "=" * 70)
    print("📋 GÜNLÜK DETAY")
    print("=" * 70)

    pivot = df.pivot_table(
        index="date", columns="strategy", values="total_return_pct", aggfunc="last"
    ).round(2)

    print(f"\n{pivot.to_string()}")

    # State bilgisi
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)

        print("\n" + "=" * 70)
        print("💼 AÇIK POZİSYONLAR")
        print("=" * 70)

        for strategy_name, strategy_data in state["strategies"].items():
            positions = strategy_data.get("positions", {})
            if positions:
                print(f"\n{strategy_name}:")
                for symbol, pos in positions.items():
                    print(f"   {symbol}: {pos['shares']} shares @ ${pos['entry_price']:.2f}")
            else:
                print(f"\n{strategy_name}: Açık pozisyon yok")

    # Sonuç ve öneriler
    print("\n" + "=" * 70)
    print("🎯 SONUÇ VE ÖNERİLER")
    print("=" * 70)

    days_count = len(df["date"].unique())

    if days_count < 5:
        print(f"""
⏳ Henüz erken ({days_count} gün)
   
   Öneriler:
   - En az 5-7 gün daha test edin
   - Günlük scan'leri düzenli çalıştırın
   - Trend oluşmasını bekleyin
""")
    else:
        scanner_return = latest.loc["Scanner", "total_return_pct"]
        drl_return = latest.loc["DRL", "total_return_pct"]
        hybrid_return = latest.loc["Hybrid", "total_return_pct"]

        if hybrid_return > scanner_return and hybrid_return > drl_return:
            result = "🟢 HYBRID EN İYİ"
        elif drl_return > scanner_return * 1.2:
            result = "🟢 DRL ÜSTÜNNo"
        elif scanner_return > drl_return * 1.2:
            result = "🔵 SCANNER ÜSTÜN"
        else:
            result = "🟡 BENZER PERFORMANS"

        print(f"\n   {result}")
        print(f"""
   Scanner:  {scanner_return:+.2f}%
   DRL:      {drl_return:+.2f}%
   Hybrid:   {hybrid_return:+.2f}%
   
   ➡️  {"DRL production-ready!" if drl_return > scanner_return else "Daha fazla test gerekli"}
""")

    print("=" * 70)
    print("✅ HAFTALIK RAPOR TAMAMLANDI")
    print("=" * 70)


if __name__ == "__main__":
    try:
        generate_weekly_report()
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
