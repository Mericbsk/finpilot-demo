# DRL Parallel Testing - Integration Guide

## 🎯 Entegrasyon Yol Haritası

### Aşama 1: Setup (Hafta 1-2)

#### 1.1 DRL Model Eğitimi
```bash
# İlk modeli eğit
python ml_agent.py --algorithm PPO \
    --timesteps 100000 \
    --track-mlflow \
    --mlflow-experiment "FinPilot-Parallel-Test"

# Model kayıt yeri: models/ppo_YYYYMMDD_HHMMSS.zip
```

#### 1.2 Test Ortamı Hazırlığı
```bash
# Log klasörü oluştur
mkdir -p logs/parallel_testing

# Test sembolleri hazırla (küçük watchlist ile başla)
echo "AAPL
MSFT
GOOGL
TSLA
NVDA" > test_symbols.txt
```

### Aşama 2: Parallel Testing (Hafta 3-6)

#### 2.1 Mod 1: Scanner Only (Baseline)
```bash
# Mevcut scanner performansını kaydet
python parallel_scanner.py \
    --mode scanner_only \
    --symbols test_symbols.txt \
    --log-dir logs/parallel_testing/baseline
```

**Beklenen Çıktı:**
- `logs/parallel_testing/baseline/YYYYMMDD_HHMMSS_signals.csv`
- `logs/parallel_testing/baseline/YYYYMMDD_HHMMSS_metadata.json`

#### 2.2 Mod 2: DRL Only
```bash
# DRL agent sinyallerini kaydet
python parallel_scanner.py \
    --mode drl_only \
    --model models/ppo_latest.zip \
    --symbols test_symbols.txt \
    --log-dir logs/parallel_testing/drl_only
```

#### 2.3 Mod 3: Hybrid (Scanner + DRL)
```bash
# Hybrid sinyaller (DRL ağırlığı %60)
python parallel_scanner.py \
    --mode hybrid \
    --model models/ppo_latest.zip \
    --drl-weight 0.6 \
    --symbols test_symbols.txt \
    --log-dir logs/parallel_testing/hybrid
```

### Aşama 3: Dashboard İzleme (Sürekli)

```bash
# Dashboard'u başlat
streamlit run drl_comparison_dashboard.py
```

**Dashboard Özellikleri:**
- ✅ Scanner vs DRL anlaşma oranı
- ✅ Sinyal kalitesi karşılaştırması
- ✅ Pozisyon sizing analizi
- ✅ Confidence dağılımı
- ⚠️ Performance tracking (paper trading sonrası)

### Aşama 4: Cron Job / Scheduler Kurulumu

#### 4.1 Günlük Tarama
```bash
# crontab -e
# Her gün 09:00'da tara
0 9 * * * cd /workspaces/Borsa && python parallel_scanner.py --mode hybrid --model models/ppo_latest.zip
```

#### 4.2 Docker Compose İçin
```yaml
# docker-compose.yml ekle
services:
  parallel-scanner:
    build: .
    command: python parallel_scanner.py --mode hybrid --model models/ppo_latest.zip
    volumes:
      - ./logs:/app/logs
    environment:
      - MODE=hybrid
      - DRL_MODEL=/app/models/ppo_latest.zip
```

### Aşama 5: Telegram Entegrasyonu

#### 5.1 Hybrid Sinyalleri Telegram'a Gönder
```python
# telegram_alerts.py'a ekle

from drl.hybrid_engine import HybridSignal

def send_hybrid_signal(signal: HybridSignal):
    """Send hybrid signal to Telegram."""
    agreement_icon = "✅" if signal.agreement else "⚠️"
    action_icon = {"BUY": "📈", "SELL": "📉", "HOLD": "⏸️"}[signal.final_action]
    
    message = f"""
{agreement_icon} {action_icon} **{signal.symbol}** - {signal.final_action}

**Scanner:**
- Action: {signal.scanner_signal.action}
- Score: {signal.scanner_signal.score}/4
- Reason: {signal.scanner_signal.reason}

**DRL Agent:**
- Action: {signal.drl_prediction.action.name if signal.drl_prediction else 'N/A'}
- Confidence: {signal.drl_prediction.confidence:.1%} if signal.drl_prediction else 'N/A'}

**Final Decision:**
- Action: {signal.final_action}
- Confidence: {signal.final_confidence:.1%}
- Position Size: {signal.risk_adjusted_size:.1%}
- Agreement: {'YES' if signal.agreement else 'NO'}
"""
    
    send_telegram_message(message)
```

### Aşama 6: Paper Trading (Hafta 7-12)

#### 6.1 Sanal Portföy Oluştur
```python
# paper_trading.py
from drl.hybrid_engine import HybridEngine

class PaperTradingEngine:
    def __init__(self, initial_capital=10000):
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
    
    def execute_signal(self, signal: HybridSignal):
        """Execute hybrid signal in paper trading."""
        if signal.final_action == "BUY":
            self.buy(signal.symbol, signal.risk_adjusted_size)
        elif signal.final_action == "SELL":
            self.sell(signal.symbol)
    
    def get_performance(self):
        """Calculate paper trading returns."""
        return {
            "total_return": self.capital / 10000 - 1,
            "num_trades": len(self.trades),
            "win_rate": self.calculate_win_rate()
        }
```

#### 6.2 Günlük Paper Trading Raporu
```bash
# Her gün 17:00'de rapor gönder
0 17 * * * cd /workspaces/Borsa && python scripts/paper_trading_report.py
```

### Aşama 7: A/B Testing Analizi (Hafta 13+)

#### 7.1 Metrikleri Karşılaştır
```python
# scripts/ab_analysis.py
import pandas as pd

def compare_strategies():
    """Compare scanner vs DRL vs hybrid performance."""
    
    # Load logs
    scanner_df = pd.read_csv("logs/parallel_testing/baseline/...")
    drl_df = pd.read_csv("logs/parallel_testing/drl_only/...")
    hybrid_df = pd.read_csv("logs/parallel_testing/hybrid/...")
    
    # Calculate metrics
    metrics = {
        "scanner": calculate_metrics(scanner_df),
        "drl": calculate_metrics(drl_df),
        "hybrid": calculate_metrics(hybrid_df)
    }
    
    # Statistical significance test
    p_value = ttest_ind(scanner_returns, drl_returns)
    
    return metrics, p_value
```

#### 7.2 Karar Kriterleri
```
DRL'yi Production'a Alma Kriterleri:
✅ Win rate > Scanner'dan %10 yüksek
✅ Sharpe ratio > 1.5
✅ Max drawdown < Scanner'ın %80'i
✅ 3+ ay paper trading verisi
✅ Statistical significance (p < 0.05)
```

### Aşama 8: Production Deployment

#### 8.1 Aşamalı Geçiş
```python
# config.py
STRATEGY_CONFIG = {
    "mode": "hybrid",  # scanner_only -> hybrid -> drl_only
    "drl_weight": 0.3,  # Başlangıç: %30 DRL, %70 Scanner
    # Her 2 haftada bir +0.1 artır
}
```

#### 8.2 Monitoring
```bash
# Prometheus metrics
drl_predictions_total
scanner_signals_total
hybrid_agreement_rate
position_sizing_avg
```

## 📊 Beklenen Timeline

| Hafta | Aktivite | Beklenen Sonuç |
|-------|----------|----------------|
| 1-2 | Model eğitimi + setup | İlk model hazır |
| 3-6 | Parallel testing | 1000+ sinyal kaydı |
| 7-12 | Paper trading | Performance data |
| 13-16 | A/B analysis | İstatistiksel karşılaştırma |
| 17+ | Production (gradual) | %100 DRL (opsiyonel) |

## 🎯 Başarı Metrikleri

### Kısa Vadeli (1 ay)
- ✅ 500+ paralel sinyal
- ✅ Agreement rate > %60
- ✅ Dashboard operational

### Orta Vadeli (3 ay)
- ✅ Paper trading complete
- ✅ DRL win rate > Scanner
- ✅ Statistical significance

### Uzun Vadeli (6+ ay)
- ✅ Production deployment
- ✅ Live performance tracking
- ✅ Continuous model retraining

## 🚨 Risk Yönetimi

### Kill Switch Kriterleri
```python
# Auto-disable DRL if:
- Consecutive losses > 5
- Drawdown > 15%
- Model confidence < 40%
- Agreement rate drops < 30%
```

## 📝 Önerilen İlk Adımlar

1. **Bu hafta:**
   ```bash
   # Model eğit
   python ml_agent.py --algorithm PPO --timesteps 50000
   
   # İlk parallel test
   python parallel_scanner.py --mode hybrid --model models/ppo_latest.zip --symbols "AAPL,MSFT,GOOGL"
   
   # Dashboard kontrol
   streamlit run drl_comparison_dashboard.py
   ```

2. **Gelecek hafta:**
   - Günlük 1 kez parallel scan
   - Sonuçları dashboard'da izle
   - Agreement rate ve confidence trendlerini analiz et

3. **Ay sonunda:**
   - Paper trading başlat
   - İlk performance comparison raporu
   - Model retrain (gerekirse)
