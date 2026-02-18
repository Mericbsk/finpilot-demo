"""
FinPilot Financial Agent - Hemen Kullan! 🚀
===========================================
En basit kullanım örneği
"""

from drl.financial_agent import FinancialAgent
import pandas as pd


def basit_analiz():
    """En basit kullanım - Kopyala yapıştır!"""
    
    print("\n" + "="*70)
    print("🚀 FinPilot Financial Agent - Basit Kullanım")
    print("="*70)
    
    # 1. AGENT OLUŞTUR (Ollama - Ücretsiz!)
    print("\n1️⃣  Agent oluşturuluyor...")
    agent = FinancialAgent(
        provider="ollama",
        model="llama3.2:latest",
        temperature=0.1,
    )
    print("   ✅ Agent hazır!")
    
    # 2. VERİ HAZIRLA
    print("\n2️⃣  Piyasa verisi hazırlanıyor...")
    
    # Örnek veri (Gerçek kullanımda yfinance ile çekersiniz)
    piyasa_verisi = pd.DataFrame({
        # Fiyat verileri
        'close': [237.85],      # Güncel fiyat
        'ema_20': [235.20],     # 20 günlük EMA
        'ema_50': [230.50],     # 50 günlük EMA
        'ema_200': [220.00],    # 200 günlük EMA
        
        # Momentum göstergeleri
        'rsi': [67.5],          # RSI (0-100)
        'macd': [1.25],         # MACD
        'macd_signal': [0.85],  # MACD sinyal hattı
        'macd_hist': [0.40],    # MACD histogram
        
        # Volatilite
        'atr': [3.75],          # Average True Range
        'bb_upper': [242.00],   # Bollinger üst
        'bb_lower': [232.00],   # Bollinger alt
        
        # Hacim
        'volume': [52_000_000],         # Güncel hacim
        'volume_avg_20': [45_000_000],  # 20 gün ort hacim
    })
    
    print("   ✅ Veri hazır!")
    
    # 3. ANALİZ YAP
    print("\n3️⃣  Analiz yapılıyor...")
    print("   ⏳ Bekleyin... (İlk seferde 30-60 saniye sürebilir)\n")
    
    sonuc = agent.analyze_market(
        symbol="AAPL",           # Hangi hisse/kripto
        timeframe="1d",          # Zaman dilimi (1d, 4h, 1h vs)
        df=piyasa_verisi,        # Yukarıdaki veri
        regime="trend",          # Piyasa rejimi: trend/range/volatility
        risk_appetite=5,         # Risk iştahı 1-10 (5=orta)
    )
    
    # 4. SONUÇLARI GÖSTER
    print("\n" + "="*70)
    print("📊 ANALİZ SONUCU")
    print("="*70)
    
    print(f"\n🎯 KARAR: {sonuc.decision}")
    print(f"   (AL / SAT / BEKLE / KAPAT)")
    
    print(f"\n📊 SİNYAL GÜCÜ: {sonuc.signal_strength:.1f} / 10")
    print(f"🎲 GÜVENİRLİK: {sonuc.confidence:.0%}")
    print(f"📈 PİYASA REJİMİ: {sonuc.regime}")
    
    if sonuc.entry_price:
        print(f"\n💰 POZİSYON DETAYLARI:")
        print(f"   Giriş Fiyatı: ${sonuc.entry_price:.2f}")
        
        if sonuc.stop_loss:
            kayip_yuzdesi = ((sonuc.stop_loss / sonuc.entry_price - 1) * 100)
            print(f"   Stop-Loss: ${sonuc.stop_loss:.2f} ({kayip_yuzdesi:+.1f}%)")
        
        if sonuc.take_profit:
            kazanc_yuzdesi = ((sonuc.take_profit / sonuc.entry_price - 1) * 100)
            print(f"   Take-Profit: ${sonuc.take_profit:.2f} ({kazanc_yuzdesi:+.1f}%)")
        
        if sonuc.position_size_pct:
            print(f"   Pozisyon Boyutu: %{sonuc.position_size_pct:.1f}")
        
        if sonuc.risk_reward_ratio:
            print(f"   Risk/Reward: 1:{sonuc.risk_reward_ratio:.1f}")
    
    if sonuc.analysis_summary:
        print(f"\n📋 ANALİZ ÖZETİ:")
        print(f"   {sonuc.analysis_summary[:300]}")
    
    if sonuc.risks:
        print(f"\n⚠️  RİSKLER:")
        for i, risk in enumerate(sonuc.risks[:3], 1):
            print(f"   {i}. {risk}")
    
    print(f"\n🤖 Model: {sonuc.model_used}")
    print(f"📊 Token Kullanımı: {sonuc.tokens_used}")
    print(f"💰 Maliyet: $0.00 (Ücretsiz!)\n")
    
    return sonuc


if __name__ == "__main__":
    try:
        basit_analiz()
        
        print("="*70)
        print("✅ İŞLEM TAMAMLANDI!")
        print("="*70)
        print()
        print("📚 Daha fazlası için:")
        print("   - Detaylı örnekler: python demo_ollama_agent.py")
        print("   - Dokümantasyon: docs/FINANCIAL_AGENT_GUIDE.md")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⏸️  İşlem durduruldu.")
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        print()
        print("💡 Sorun giderme:")
        print("   1. Ollama çalışıyor mu? → ollama serve")
        print("   2. Model var mı? → ollama list")
        print("   3. Model indir → ollama pull llama3.2")
        print()
