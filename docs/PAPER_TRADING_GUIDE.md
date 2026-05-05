# 📊 Paper Trading Sistemi

## Genel Bakış

Bu sistem Scanner, DRL ve Hybrid stratejilerini gerçek zamanlı olarak test eder.
Sanal $10,000 sermaye ile performans karşılaştırması yapar.

---

## 🚀 Hızlı Başlangıç

### 1. İlk Çalıştırma (Manual)

```bash
# Günlük scan
python scripts/daily_paper_trading.py

# Haftalık rapor
python scripts/weekly_paper_trading_report.py
```

### 2. Otomatik Çalıştırma (Cron Job)

**Linux/Mac:**

```bash
# Crontab düzenle
crontab -e

# Her gün piyasa kapanışında (17:00)
0 17 * * 1-5 cd /workspaces/Borsa && python scripts/daily_paper_trading.py >> logs/paper_trading/cron.log 2>&1

# Her Pazar rapor
0 20 * * 0 cd /workspaces/Borsa && python scripts/weekly_paper_trading_report.py >> logs/paper_trading/report.log 2>&1
```

**Windows (Task Scheduler):**

```powershell
# daily_paper_trading.bat oluştur
@echo off
cd C:\path\to\Borsa
python scripts\daily_paper_trading.py
```

---

## 📁 Dosya Yapısı

```
logs/paper_trading/
├── state.json              # Güncel portföy durumu
├── daily_results.json      # Tüm günlük sonuçlar
├── weekly_chart.png        # Performans grafiği
├── cron.log               # Cron job logları
└── report.log             # Rapor logları
```

---

## 📊 Metrikler

### Temel Metrikler:
- **Total Return %**: Toplam getiri
- **Sharpe Ratio**: Risk-adjusted return
- **Max Drawdown %**: En büyük düşüş
- **Win Rate %**: Kazanan trade oranı
- **Total Trades**: Toplam işlem sayısı

### Karşılaştırma:
- **Scanner**: Kural-tabanlı teknik analiz
- **DRL**: Deep reinforcement learning
- **Hybrid**: Scanner + DRL (60/40 ağırlık)

---

## 🎯 Kullanım Senaryoları

### Senaryo 1: Günlük Takip (Önerilen)
```bash
# Her gün
python scripts/daily_paper_trading.py

# Haftalık kontrol
python scripts/weekly_paper_trading_report.py
```

**Beklenen:**
- 1 hafta → İlk trendler
- 1 ay → İstatistiksel anlamlılık
- 3 ay → Production kararı

### Senaryo 2: Backtest Simülasyonu
```bash
# Geçmiş tarihleri test et
# (manual olarak test_date parametresi değiştir)
```

### Senaryo 3: Multi-Symbol Test
```bash
# SYMBOLS listesini genişlet
# scripts/daily_paper_trading.py içinde
SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN"]
```

---

## 📈 Performans Kriterleri

### ✅ Production-Ready Kriterleri:
```
DRL Total Return > Scanner + 20%
DRL Sharpe Ratio > 1.5
DRL Max Drawdown < Scanner * 0.8
Win Rate > 60%
Test Period ≥ 3 months
Statistical Significance: p < 0.05
```

### ⚠️ Uyarı Sinyalleri:
```
Consecutive Losses > 5
Max Drawdown > 25%
Sharpe Ratio < 0.5
Win Rate < 45%
```

---

## 🔧 Özelleştirme

### Sermaye Değiştirme:
```python
# scripts/daily_paper_trading.py içinde
engines = {
    "Scanner": PaperTradingEngine(50000, "scanner"),  # $50K
    "DRL": PaperTradingEngine(50000, "drl"),
}
```

### Pozisyon Sizing:
```python
# paper_trading.py içinde
position_size = self.capital * 0.2  # %20 yerine %10
```

### Model Değiştirme:
```python
# Başka model kullan
self.model = PPO.load("models/ppo_production_20260217_165440.zip")
```

---

## 📊 Örnek Çıktı

```
📊 HAFTALIK PAPER TRADING RAPORU
═══════════════════════════════════════════════════════════════════

🎯 Scanner:
   Total Return:    +2.34%
   Sharpe Ratio:    1.12
   Max Drawdown:    -3.45%
   Win Rate:        58%
   Total Trades:    12
   Final Capital:   $10,234

🎯 DRL:
   Total Return:    +3.87%
   Sharpe Ratio:    1.65
   Max Drawdown:    -2.11%
   Win Rate:        67%
   Total Trades:    8
   Final Capital:   $10,387

🎯 Hybrid:
   Total Return:    +3.21%
   Sharpe Ratio:    1.48
   Max Drawdown:    -2.67%
   Win Rate:        62%
   Total Trades:    10
   Final Capital:   $10,321

🏆 KARŞILAŞTIRMA
═══════════════════════════════════════════════════════════════════

   En İyi Return:    DRL (+3.87%)
   En İyi Sharpe:    DRL (1.65)
   En İyi DD:        DRL (-2.11%)

🎯 SONUÇ: 🟢 DRL ÜSTÜN
```

---

## 🐛 Troubleshooting

### Problem: Günlük scan çalışmıyor
```bash
# Log kontrol
cat logs/paper_trading/cron.log

# Manuel çalıştır
python scripts/daily_paper_trading.py
```

### Problem: Model yüklenemiyor
```bash
# Model path kontrol
ls -lh models/ppo_balanced_*.zip

# paper_trading.py içinde path güncelle
```

### Problem: Veri çekemiyor
```bash
# İnternet kontrolü
# yfinance version kontrolü
pip list | grep yfinance
```

---

## 📚 İlgili Dosyalar

- `paper_trading.py` - Ana engine
- `scripts/daily_paper_trading.py` - Günlük scan
- `scripts/weekly_paper_trading_report.py` - Haftalık rapor
- `docs/DRL_WORKFLOW_ALTERNATIF.md` - DRL workflow
- `docs/DRL_COMPREHENSIVE_ANALYSIS.md` - Detaylı analiz

---

## 🎓 Sonraki Adımlar

1. **Hafta 1**: Günlük scan çalıştır, sonuçları izle
2. **Hafta 2-4**: Trendleri analiz et, model iyileştir
3. **Ay 2-3**: İstatistiksel significance test
4. **Ay 4+**: Production deployment kararı

---

**Oluşturulma:** 2026-02-17
**Versiyon:** 1.0
**Durum:** ✅ Production-ready
