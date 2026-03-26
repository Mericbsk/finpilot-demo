# Momentum + Swing + Conservative Üçlü Ensemble İyileştirme Yol Haritası

> **Mevcut Durum (Baseline):**
> | Agent | Sharpe | Return | Max DD | Trades |
> |-------|--------|--------|--------|--------|
> | momentum | +0.0519 | +22.0% | 23.3% | 118 |
> | swing (LSTM) | +0.0221 | +22.6% | 22.2% | 150 |
> | conservative | +0.0115 | +3.8% | 12.5% | 153 |
> | **Ensemble tahmini** | **~+1.19** | — | — | — |

---

## Faz 1 — Eğitim Derinliği (Sprint 20, ~2 gün)

### 1.1 Daha Uzun Eğitim (3M steps)
- **Ne:** Her ajanı 500K → **3M step** ile yeniden eğit
- **Neden:** 500K step yeterli convergence sağlamıyor, özellikle swing (LSTM) modeli daha fazla step'e ihtiyaç duyar
- **Beklenen etki:** Sharpe %20-40 artış, drawdown azalma
- **Yöntem:**
  ```python
  # train_sprint18.py'de total_timesteps güncelle
  total_timesteps = 3_000_000
  # swing için: 5_000_000 (LSTM daha yavaş öğrenir)
  ```

### 1.2 Curriculum Training
- **Ne:** Kolay → zor piyasa koşullarında kademeli eğitim
- **Neden:** Agent önce düşük volatilite dönemlerinde öğrenir, sonra kriz dönemlerine geçer
- **Uygulama:**
  1. **Faz A (1M step):** 2019-2021 bull market verileri
  2. **Faz B (1M step):** 2018+2022 correction verileri eklenir
  3. **Faz C (1M step):** Tam veri seti (2017-2025)
- **Beklenen etki:** Max drawdown %15-20 azalma

### 1.3 Sembol Çeşitliliği Artırma
- **Mevcut:** ~20 sembol üzerinde eğitim
- **Hedef:** 50-100 sembol (sektör dengelemeli):
  - Tech: AAPL, MSFT, GOOGL, NVDA, META (5)
  - Finance: JPM, BAC, GS, V, MA (5)
  - Healthcare: JNJ, UNH, PFE, LLY, ABBV (5)
  - Energy: XOM, CVX, COP, SLB (4)
  - Consumer: AMZN, WMT, COST, PG, NKE (5)
  - ETF: SPY, QQQ, IWM, XLF, XLK, TLT (6)
- **Neden:** Symbol-agnostic features zaten var; daha fazla sembol = daha robust features

---

## Faz 2 — Hiperparametre Optimizasyonu (Sprint 21, ~2 gün)

### 2.1 Optuna ile Agent-Spesifik Tuning
Her agent için ayrı Optuna çalışması:

| Parametre | Momentum Aralık | Swing Aralık | Conservative Aralık |
|-----------|-----------------|--------------|---------------------|
| learning_rate | 1e-5 → 5e-4 | 1e-5 → 3e-4 | 5e-5 → 5e-4 |
| n_steps | 1024 → 4096 | 2048 → 8192 | 512 → 2048 |
| batch_size | 64 → 512 | 128 → 512 | 64 → 256 |
| gamma | 0.97 → 0.999 | 0.98 → 0.999 | 0.99 → 0.9999 |
| ent_coef | 0.001 → 0.05 | 0.001 → 0.03 | 0.01 → 0.1 |
| clip_range | 0.1 → 0.3 | 0.1 → 0.3 | 0.15 → 0.4 |
| gae_lambda | 0.9 → 0.99 | 0.92 → 0.99 | 0.9 → 0.98 |

- **Yöntem:** Walk-Forward Optimization (WFO) ile 5-fold rolling split
- **Trial sayısı:** Her agent 100 trial × 500K step = ~12 saat/agent
- **Beklenen etki:** Sharpe %30-50 artış

### 2.2 Reward Function Tuning
Her agent'ın reward weights'ini speciality'sine göre optimize et:

```python
# Momentum: getiriyi ödüllendir, drawdown toleransı yüksek
momentum_rewards = RewardWeights(
    sharpe_weight=0.4,    # ↓ sharpe, ↑ raw return
    return_weight=0.5,    # momentum = maximize gains
    drawdown_weight=0.1,  # drawdown tolerance
)

# Conservative: drawdown cezasını ağırlaştır
conservative_rewards = RewardWeights(
    sharpe_weight=0.3,
    return_weight=0.1,    # düşük return beklentisi
    drawdown_weight=0.6,  # ↑ capital preservation
)

# Swing: orta yol + trend ödülü
swing_rewards = RewardWeights(
    sharpe_weight=0.5,
    return_weight=0.3,
    drawdown_weight=0.2,
)
```

### 2.3 Observation Stacking Tuning
- **Mevcut:** n_stack=4 (tüm agentlar)
- **Test:** Momentum n_stack=2 (hızlı reaksiyon), swing n_stack=8 (daha uzun trend), conservative n_stack=4
- **Yöntem:** Her kombinasyon için WFO backtest

---

## Faz 3 — Ensemble Ağırlık Optimizasyonu (Sprint 22, ~1-2 gün)

### 3.1 Learnable Weights Warm-Start
- **Ne:** EMA tabanlı LearnableEnsembleWeights'i backtested verilerle ön-eğit
- **Yöntem:**
  1. Her agentı 2023 verisi üzerinde backtest et
  2. Haftalık Sharpe ratio'larını kaydet
  3. Optimal ağırlıkları hesapla (Markowitz mean-variance)
  4. LearnableEnsembleWeights'in initial weights'i olarak set et
- **Beklenen etki:** Cold-start sorunu ortadan kalkar

### 3.2 Regime Prior Kalibrasyonu
- **Mevcut sorun:** Conservative regime_weight ~0.87, diğerleri ~0.06
- **Hedef:** Daha dengeli priorlar (min %15 her agnete)
- **Uygulama:**
  - Momentum: `abs(MACD) × volume_ratio × 3.0` (amplify sinyali)
  - Swing: `trend_strength × 10.0 × stability × 2.0` (stability bonus)
  - Conservative: `vol_regime × 0.3 + atr_risk × 0.3` (azalt dominansı)
- **Beklenen etki:** Üçlünün daha aktif katılımı

### 3.3 Bayesian Ensemble Weights
```python
# Thompson Sampling ile adaptif ağırlıklar
class BayesianEnsembleWeights:
    def __init__(self, tags):
        self.alpha = {t: 1.0 for t in tags}  # Beta dist params
        self.beta = {t: 1.0 for t in tags}

    def sample_weights(self):
        samples = {t: np.random.beta(self.alpha[t], self.beta[t]) for t in self.alpha}
        total = sum(samples.values())
        return {t: v/total for t, v in samples.items()}

    def update(self, tag, reward):
        if reward > 0:
            self.alpha[tag] += 1
        else:
            self.beta[tag] += 1
```

---

## Faz 4 — Feature Engineering (Sprint 23, ~2 gün)

### 4.1 Agent-Spesifik Feature Boost
Her agent'a kendi uzmanlık alanına özel ek feature'lar:

| Agent | Ek Feature'lar | Açıklama |
|-------|---------------|----------|
| momentum | ADX, ROC(5), ROC(20), OBV_slope | Trend gücü + momentum devamlılığı |
| swing | Fibo_retracement, pivot_points, swing_high_low | Dönüş noktaları tespiti |
| conservative | VIX_proxy, correlation_spy, beta_60d | Risk metrikleri + hedging sinyalleri |

- **Uygulama:** `FeatureBoost` zaten specialists catalog'da tanımlı, weight'leri artır
- **Dikkat:** Feature sayısı artarsa obs_dim değişir → yeniden eğitim gerekir

### 4.2 Temporal Feature'lar
```python
# Gün içi ve haftalık pattern'lar
temporal_features = [
    'day_of_week_sin',     # 0-1, Pazartesi etkisi
    'day_of_week_cos',     # 0-1
    'month_sin',           # Seasonality
    'month_cos',           # Seasonality
    'days_to_earnings',    # Earnings proximity (0-90 gün)
    'quarter_progress',    # Q1/Q2/Q3/Q4 hangi noktada
]
```

### 4.3 Cross-Asset Signal'lar
```python
# Makro rejim tespiti
cross_asset_features = [
    'spy_return_5d',       # S&P 500 momentum
    'vix_level',           # Korku endeksi
    'dxy_return_5d',       # Dolar endeksi
    'tnx_return_5d',       # 10-year yield momentum
    'sector_relative',     # Sektöre göre relatif güç
]
```

---

## Faz 5 — Backtesting & Validation (Sprint 24, ~2 gün)

### 5.1 Walk-Forward Backtesting
```
Veri: 2017-2025 (8 yıl)

  Train Window    Test Window
  ├─2017──2020──┤ ├─2020──2021──┤  → Fold 1
       ├─2018──2021──┤ ├─2021──2022──┤  → Fold 2
            ├─2019──2022──┤ ├─2022──2023──┤  → Fold 3
                 ├─2020──2023──┤ ├─2023──2024──┤  → Fold 4
                      ├─2021──2024──┤ ├─2024──2025──┤  → Fold 5
```

- Her fold'da: Train → Validate → Out-of-sample test
- Metrikler: Sharpe, Sortino, Max DD, Calmar, Win Rate, Profit Factor

### 5.2 Monte Carlo Stress Testing
- 1000 random bootstrap ile return dağılımı
- %5 VaR ve %1 CVaR hesapla
- "En kötü ay" analizi

### 5.3 Regime-Spesifik Performance
- Bull market (SPY >EMA200): Her agent ayrı ayrı
- Bear market (SPY <EMA200): Her agent ayrı ayrı
- Yatay piyasa (ATR düşük): Her agent ayrı ayrı
- High volatility (VIX >25): Her agent ayrı ayrı

---

## Faz 6 — Production Hardening (Sprint 25, ~2 gün)

### 6.1 Confidence Calibration
- **Sorun:** Şu anda confidence = raw_action magnitude → kalibre değil
- **Çözüm:** Platt Scaling (logistic regression) ile confidence'ı gerçek doğruluk oranına kalibre et
- **Yöntem:** Backtest sonuçlarındaki (confidence, was_profitable) çiftlerini kullanarak sigmoid fit

### 6.2 Position Sizing Optimizasyonu
```python
# Kelly Criterion + ensemble agreement multiplier
position = kelly_fraction * agreement_score * risk_multiplier
# agreement < 0.6 → %50 position cut
# agreement < 0.4 → HOLD (mevcut)
```

### 6.3 Dynamic Agent Rotation
- Haftalık rolling Sharpe bazında en kötü performans gösteren agent'ı devre dışı bırak
- 2-agent ensemble'a düş, performans toparlanınca geri al
- Logging + Prometheus metrikleri

### 6.4 Transaction Cost Modelling
- Mevcut: Transaction cost yok
- Ekle: %0.1 komisyon + %0.01 slippage/trade
- **Etki:** Scalper-tarzı davranışı cezalandırır, daha az trade → daha iyi net return

---

## Öncelik Sıralaması ve Tahmini Etki

| Faz | Effort | Tahmini Sharpe İyileşme | Öncelik |
|-----|--------|-------------------------|---------|
| 1. Eğitim Derinliği (3M) | 2 gün | +40-60% | 🔴 P0 |
| 2. Hyperparameter Tuning | 2 gün | +30-50% | 🔴 P0 |
| 3. Ensemble Weights | 1 gün | +15-25% | 🟡 P1 |
| 4. Feature Engineering | 2 gün | +10-20% | 🟡 P1 |
| 5. Backtesting | 2 gün | Validation only | 🟢 P2 |
| 6. Production Hardening | 2 gün | Risk reduction | 🟢 P2 |

**Toplam:** ~11 gün (5-6 sprint)

---

## Hedef Metrikler (Faz 6 sonrası)

| Metrik | Mevcut | Hedef |
|--------|--------|-------|
| Ensemble Sharpe | ~0.03 | >0.10 |
| Yıllık Return | ~15% | >25% |
| Max Drawdown | ~20% | <15% |
| Agreement > 66% oranı | ~60% | >75% |
| Win Rate | ~50% | >55% |
| Profit Factor | ~1.0 | >1.3 |

---

## Hemen Yapılabilecekler (Quick Wins)

1. ✅ **Trio aktif edildi** — momentum + swing + conservative
2. ✅ **Obs stacking fix** — inference artık 88-dim obs üretiyor
3. ✅ **Floor weights** — her agent minimum %3 ağırlık alıyor
4. 🔜 **3M step re-train** — en büyük etki, hemen başlanabilir
5. 🔜 **Reward tuning** — agent-spesifik reward weights
