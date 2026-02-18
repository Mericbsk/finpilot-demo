#!/usr/bin/env python3
"""
Geçmiş Verilerle Paper Trading Backtest
Son 30 gün gibi bir periyodu hızlıca test et
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from paper_trading import PaperTradingEngine, run_paper_trading_day

def historical_backtest(
    symbols: list,
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 10000
):
    """
    Geçmiş tarihler için paper trading simülasyonu
    
    Args:
        symbols: Test edilecek semboller
        start_date: Başlangıç tarihi
        end_date: Bitiş tarihi
        initial_capital: Başlangıç sermayesi
    """
    
    print("=" * 70)
    print("📊 GEÇMİŞ VERİLERLE PAPER TRADING BACKTEST")
    print("=" * 70)
    print(f"📅 Tarih Aralığı: {start_date.date()} → {end_date.date()}")
    print(f"💰 Başlangıç Sermayesi: ${initial_capital:,.0f}")
    print(f"📊 Semboller: {', '.join(symbols)}")
    print()
    
    # Engine'leri oluştur
    engines = {
        "Scanner": PaperTradingEngine(initial_capital, "scanner"),
        "DRL": PaperTradingEngine(initial_capital, "drl"),
        "Hybrid": PaperTradingEngine(initial_capital, "hybrid"),
    }
    
    # Her işlem günü için simülasyon
    current_date = start_date
    trading_days = 0
    
    print("🔄 Backtest çalışıyor...\n")
    
    while current_date <= end_date:
        # Sadece hafta içi (basit kontrol)
        if current_date.weekday() < 5:  # 0=Pazartesi, 4=Cuma
            try:
                daily_signals = run_paper_trading_day(
                    engines, 
                    symbols, 
                    current_date
                )
                trading_days += 1
                
            except Exception as e:
                print(f"⚠️  {current_date.date()}: {e}")
        
        current_date += timedelta(days=1)
    
    # Sonuçları göster
    print("\n" + "=" * 70)
    print("📈 BACKTEST SONUÇLARI")
    print("=" * 70)
    print(f"📅 Trading Days: {trading_days}")
    print()
    
    results = {}
    
    for name, engine in engines.items():
        metrics = engine.get_performance_metrics()
        results[name] = metrics
        
        print(f"🎯 {name}:")
        if metrics:
            print(f"   Total Return:    {metrics['total_return_pct']:+.2f}%")
            print(f"   Sharpe Ratio:    {metrics['sharpe_ratio']:.2f}")
            print(f"   Max Drawdown:    {metrics['max_drawdown_pct']:.2f}%")
            print(f"   Win Rate:        {metrics['win_rate_pct']:.0f}%")
            print(f"   Total Trades:    {metrics['total_trades']}")
            print(f"   Open Positions:  {metrics['open_positions']}")
            print(f"   Final Capital:   ${metrics['final_capital']:,.0f}")
        else:
            print("   No data")
        print()
    
    # Karşılaştırma
    if all(results.values()):
        print("=" * 70)
        print("🏆 KARŞILAŞTIRMA")
        print("=" * 70)
        
        best_return = max(results.items(), key=lambda x: x[1]['total_return_pct'])
        best_sharpe = max(results.items(), key=lambda x: x[1]['sharpe_ratio'])
        best_drawdown = max(results.items(), key=lambda x: x[1]['max_drawdown_pct'])
        
        print(f"   En İyi Return:    {best_return[0]} ({best_return[1]['total_return_pct']:+.2f}%)")
        print(f"   En İyi Sharpe:    {best_sharpe[0]} ({best_sharpe[1]['sharpe_ratio']:.2f})")
        print(f"   En İyi Drawdown:  {best_drawdown[0]} ({best_drawdown[1]['max_drawdown_pct']:.2f}%)")
        
        # Winner belirleme
        scanner_return = results['Scanner']['total_return_pct']
        drl_return = results['DRL']['total_return_pct']
        hybrid_return = results['Hybrid']['total_return_pct']
        
        print(f"\n🎯 SONUÇ:")
        
        if hybrid_return > scanner_return and hybrid_return > drl_return:
            winner = "🟢 HYBRID EN İYİ"
            recommendation = "Hybrid stratejisini kullanın!"
        elif drl_return > scanner_return * 1.2:
            winner = "🟢 DRL ÜSTÜN"
            recommendation = "DRL production-ready!"
        elif scanner_return > drl_return * 1.2:
            winner = "🔵 SCANNER ÜSTÜN"
            recommendation = "Mevcut sistemi kullanmaya devam edin"
        else:
            winner = "🟡 BENZER PERFORMANS"
            recommendation = "Daha uzun test periyodu gerekli"
        
        print(f"   {winner}")
        print(f"   {recommendation}")
        
        print(f"\n   Scanner:  {scanner_return:+.2f}%")
        print(f"   DRL:      {drl_return:+.2f}%")
        print(f"   Hybrid:   {hybrid_return:+.2f}%")
    
    # Detaylı trade history
    print("\n" + "=" * 70)
    print("💼 TRADE HISTORY")
    print("=" * 70)
    
    for name, engine in engines.items():
        closed_trades = [t for t in engine.trades if t['action'] == 'SELL']
        if closed_trades:
            print(f"\n{name} ({len(closed_trades)} trades):")
            for trade in closed_trades[-5:]:  # Son 5 trade
                print(f"   {trade['symbol']:5s} {trade['profit']:+7.2f} ({trade['profit_pct']:+.1f}%) - {trade['hold_days']} days")
        else:
            print(f"\n{name}: No closed trades")
    
    # Portfolio value over time
    print("\n" + "=" * 70)
    print("📊 PORTFOLIO VALUE TRENDİ")
    print("=" * 70)
    
    for name, engine in engines.items():
        if len(engine.daily_portfolio_value) > 0:
            values = [d['total_value'] for d in engine.daily_portfolio_value]
            dates = [d['date'].strftime('%Y-%m-%d') for d in engine.daily_portfolio_value]
            
            print(f"\n{name}:")
            print(f"   Start: ${values[0]:,.0f}")
            print(f"   End:   ${values[-1]:,.0f}")
            print(f"   Min:   ${min(values):,.0f}")
            print(f"   Max:   ${max(values):,.0f}")
    
    print("\n" + "=" * 70)
    print("✅ BACKTEST TAMAMLANDI")
    print("=" * 70)
    
    return results, engines


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Geçmiş verilerle paper trading backtest")
    parser.add_argument("--days", type=int, default=30, help="Kaç gün geriye git (default: 30)")
    parser.add_argument("--symbols", type=str, default="AAPL,MSFT,GOOGL", 
                       help="Semboller (virgülle ayrılmış)")
    parser.add_argument("--capital", type=float, default=10000, 
                       help="Başlangıç sermayesi (default: 10000)")
    
    args = parser.parse_args()
    
    # Tarih aralığı
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    # Semboller
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    # Backtest çalıştır
    results, engines = historical_backtest(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_capital=args.capital
    )
    
    print(f"""
📝 Kullanım Örnekleri:

# Son 30 gün (default)
python scripts/historical_backtest.py

# Son 60 gün
python scripts/historical_backtest.py --days 60

# Farklı semboller
python scripts/historical_backtest.py --symbols "TSLA,NVDA,AMD"

# Büyük sermaye
python scripts/historical_backtest.py --capital 50000

# Kombine
python scripts/historical_backtest.py --days 90 --symbols "AAPL,MSFT,GOOGL,TSLA,NVDA" --capital 50000
""")
