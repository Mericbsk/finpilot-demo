# FinPilot DRL Agent — Kapsamlı Analiz Raporu

**Tarih:** 2026-02-25
**Versiyon:** 1.0
**Kapsam:** 5 PPO Ajan × 3 Sembol × 24 Feature

---

## İçindekiler

1. [Mevcut Ajanların Genel Durumu](#1-mevcut-ajanların-genel-durumu)
2. [Performans Analizi](#2-performans-analizi)
3. [Blind Point (Kör Nokta) Tespiti](#3-blind-point-kör-nokta-tespiti)
4. [Ödül Fonksiyonu Analizi](#4-ödül-fonksiyonu-analizi)
5. [Veri Kalitesi ve State Representation](#5-veri-kalitesi-ve-state-representation)
6. [Maksimum Verim İçin Gerekli Ajan Sayısı](#6-maksimum-verim-için-gerekli-ajan-sayısı)
7. [Eğitim Stratejisi](#7-eğitim-stratejisi)
8. [Performans Optimizasyonu](#8-performans-optimizasyonu)
9. [Aktif Kullanım Stratejisi](#9-aktif-kullanım-stratejisi)
10. [Riskler ve Sınırlamalar](#10-riskler-ve-sınırlamalar)
11. [Yol Haritası](#11-yol-haritası)
12. [Genel Özet (Executive Summary)](#12-genel-özet-executive-summary)

---

## 1. Mevcut Ajanların Genel Durumu

### 1.1 Registry Özeti

| Model | Timesteps | LR | γ | ent_coef | Curriculum | Aktif |
|---|---|---|---|---|---|---|
| **ppo_conservative** | 80K | 1e-4 | 0.995 | 0.005 | ✅ | ❌ |
| **ppo_balanced** | 60K | 3e-4 | 0.990 | 0.010 | ✅ | ❌ |
| **ppo_aggressive** | 60K | 5e-4 | 0.970 | 0.020 | ✅ | ❌ |
| **ppo_explorer** | 60K | 3e-4 | 0.990 | 0.050 | ❌ | ❌ |
| **ppo_longhorizon** ★ | 100K | 2e-4 | 0.995 | 0.010 | ✅ | ✅ |

- **Algoritma:** Tüm ajanlar PPO (Proximal Policy Optimization), `MlpPolicy`
- **Eğitim Sembolleri:** AAPL, NVDA, TSLA (yalnızca 3 sembol)
- **Feature Boyutu:** 24 (13 teknik + 3 regime + 2 sentiment + 2 onchain + 4 portfolio state)
- **Action Space:** Continuous Box(−0.75, +0.75) — pozisyon fraksiyonu

### 1.2 Mimari

```
Observation (24-dim float32)
   → MLP Policy (SB3 default: 64×64 hidden layers, tanh activation)
   → Action (1-dim continuous: −0.75 to +0.75)
   → MarketEnv.step() → reward shaping → next observation
```

### 1.3 Kritik Bulgu

**5 modelin 3'ü tamamen ÖLÜ:**

| Model | Test Sharpe | Test Return | Max DD | Win Rate | Durum |
|---|---|---|---|---|---|
| ppo_conservative | 0.000 | 0.000 | 0.000 | 0.000 | 🔴 **ÖLÜ** |
| ppo_balanced | 0.000 | 0.000 | 0.000 | 0.000 | 🔴 **ÖLÜ** |
| ppo_aggressive | 0.000 | 0.000 | 0.000 | 0.000 | 🔴 **ÖLÜ** |
| ppo_explorer | −0.119 | 0.009 | 0.023 | 0.317 | 🟡 **ZAYIF** |
| ppo_longhorizon | **0.735** | **0.023** | 0.026 | 0.302 | 🟢 **AKTİF** |

> **Yorum:** Conservative, balanced ve aggressive modellerin tüm metrikleri sıfır. Bu, eğitim sırasında policy'nin collapse ettiğini (constant HOLD) gösteriyor. Explorer zayıf ama işlem yapabiliyor. Sadece longhorizon modeli anlamlı bir policy öğrenmiş.

---

## 2. Performans Analizi

### 2.1 Çalışan Model: ppo_longhorizon

| Metrik | Değer | Yorum |
|---|---|---|
| Test Sharpe | 0.735 | Kabul edilebilir ama yüksek değil |
| Train Sharpe | 1.459 | İyi eğitim performansı |
| Sharpe Degradation | 49.6% | ⚠️ Yüksek — overfitting göstergesi |
| Total Return | 2.26% | Düşük — 2yr veri üzerinde |
| Max Drawdown | 2.57% | Conservative — risk kontrolü iyi |
| Win Rate | 30.2% | ⚠️ Düşük — 3 işlemden 1'i kazanıyor |
| Profit Factor | ∞ | Veri sorunu (muhtemelen 0 zarar) |
| Overfit Folds | 9/15 | ⚠️ %60 fold'da overfitting |

### 2.2 Performans Derecelendirmesi

```
ÜSTÜN   : Sharpe > 2.0, degrad < 20%
İYİ     : Sharpe 1.0-2.0, degrad < 30%
KABUL   : Sharpe 0.5-1.0, degrad < 50%  ← ppo_longhorizon BURASI
ZAYIF   : Sharpe 0.0-0.5
BAŞARISIZ: Sharpe ≤ 0.0 veya sıfır return  ← 3 ölü model + explorer
```

### 2.3 Sorunların Kök Neden Analizi

1. **3 ÖLÜ model neden öldü?**
   - `sharpe_train = -1.86e16` → NaN/Inf hesaplama hatası (muhtemelen tüm PnL = 0)
   - Constant HOLD behaviour: model hiç pozisyon almıyor
   - **Kök neden:** 60K-80K timestep, 3 sembol verisinde (toplam ~1500 satır) çok az episode var. PPO her episode'da birkaç yüz step görüyor. Curriculum learning başlangıçta maliyetleri düşük tutsa da, agent HOLD'da sıkışıp kalıyor.

2. **Longhorizon neden çalışıyor?**
   - 100K timestep → %25 daha fazla deneyim
   - Curriculum'un son aşamasına (hard phase) ulaşabilmiş
   - LR=2e-4 ile gamma=0.995 dengeli bir combo

3. **%49.6 Sharpe degradation:**
   - Train'de 1.46, test'te 0.74 — modelin train verisine partial overfit olduğu açık
   - 9/15 fold'da overfit → Walk-forward validation güvenilmez

---

## 3. Blind Point (Kör Nokta) Tespiti

### 3.1 Varlık Sınıfı Körlüğü 🔴 KRİTİK

- **Sadece 3 ABD teknoloji hissesi ile eğitilmiş:** AAPL, NVDA, TSLA
- Farklı korelasyon yapıları görmemiş:
  - ❌ Enerji, Sağlık, Finans sektörleri
  - ❌ ETF'ler (SPY, QQQ, IWM)
  - ❌ Kripto (BTC-USD, ETH-USD)
  - ❌ Emtia
  - ❌ Uluslararası hisseler
- Sonuç: agent, yalnızca yüksek-beta tech davranışını öğrenmiş

### 3.2 Market Regime Körlüğü 🔴 KRİTİK

- Regime detection basit kural tabanlı: `ATR/Close > 0.02 → volatility`, `Close > EMA50 > EMA200 → trend`
- 2yr daily veri → 2020 crash, 2022 bear market gibi extreme eventleri görmemiş olabilir (tarih bağımlı)
- Agent hiç **bear market uzun süreli düşüş** görmemiş olabilir
- Regime geçiş noktalarında (transition) özel davranış öğrenmemiş

### 3.3 Zaman Dilimi Körlüğü 🟡 ORTA

- Sadece **günlük (1d)** verilerle eğitilmiş
- Intraday (1h, 15m) dinamiklere tamamen kör
- Multi-timeframe analiz kapasitesi yok

### 3.4 Likidite Körlüğü 🟡 ORTA

- Volume sadece bir feature olarak mevcut, ama stochastic slippage basit
- Düşük hacimli piyasa koşullarına gerçek tepki öğrenmemiş
- Pre/post market, earnings gaps gibi likidite eventleri yok

### 3.5 Makroekonomik Körlük 🟡 ORTA

- Fed faiz kararları, CPI, GDP gibi makro veri yok
- VIX, yield curve gibi risk göstergeleri eksik
- Sector rotation görmemiş

### 3.6 Portfolio İnteraction Körlüğü 🟢 DÜŞÜK (kısmen çözülmüş)

- `cash_ratio, position_ratio, open_risk, kelly_fraction` feature'ları var
- **Ama eğitimde hep statik:** cash_ratio=1.0, position_ratio=0.0, open_risk=0.0
- Agent, portfolio state değişimlerine gerçek tepki öğrenememiş

### 3.7 Korelasyon Körlüğü 🔴 KRİTİK

- Her sembol bağımsız eğitiliyor (concat multi-asset)
- Cross-asset korelasyon yok (AAPL-NVDA birlikte düşerken ne yapılmalı?)
- Portföy çeşitlendirme kavramı eksik

---

## 4. Ödül Fonksiyonu Analizi

### 4.1 Mevcut Ödül Yapısı

```python
reward = pnl_weight(1.0) × PnL
       − cost_weight(0.1) × transaction_cost
       − drawdown_weight(1.0) × drawdown
       − leverage_weight(0.2) × leverage_penalty
       + regime_bonus(0.05) × regime_alignment
       − turnover_penalty(0.02) × |position_change|
       − inactivity_penalty(0.003)  # if |position| < 0.05
       + position_bonus(0.002) × |position|
       + sharpe_bonus(0.10) × clip(rolling_sharpe, −2, 2)  # if buffer ≥ 20
```

### 4.2 Güçlü Yönler ✅

1. **Multi-signal reward:** PnL, risk, regime, turnover hepsi var
2. **Curriculum learning:** Maliyet multiplier'ı aşamalı artıyor (0.2 → 0.6 → 1.0)
3. **Inactivity penalty:** Constant HOLD'u cezalandırıyor (Sprint 14 eklendi)
4. **Rolling Sharpe bonus:** Risk-adjusted getiri teşvik ediliyor
5. **Stochastic slippage:** Volume-dependent maliyet gerçekçi

### 4.3 Zayıf Yönler ve Sorunlar ⚠️

| Sorun | Seviye | Açıklama |
|---|---|---|
| **Reward ölçek dengesizliği** | 🔴 | PnL tipik olarak ±0.001-0.01 aralığında. Drawdown 0-1 aralığında. Drawdown reward'ı domine ediyor |
| **Inactivity penalty çok küçük** | 🟡 | 0.003/step yeterli değil — 3 ölü model kanıtı |
| **Profit factor hesaplanmıyor** | 🟡 | Reward'da kazanç/kayıp oranı yok |
| **Time-based incentive yok** | 🟡 | Agent, ne zaman işlem açacağını değil HER step'te ne yapacağını öğreniyor |
| **Win streak/Loss streak** | 🟡 | Ardışık kayıptan sonra pozisyon küçültme yok |
| **Terminal reward yok** | 🟡 | Episode sonunda toplam performansa bonus/ceza yok |
| **Reward clipping yok** | 🟡 | Extreme PnL veya drawdown spike'ları gradient'i bozabilir |

### 4.4 Curriculum Learning Detayı

```
Phase A (0-30%):  cost×0.2, pos_limit×0.5, PnL×1.5, DD×0.3, explore=0.05
Phase B (30-70%): cost×0.6, pos_limit×0.8, PnL×1.2, DD×0.7, explore=0.02
Phase C (70-100%): cost×1.0, pos_limit×1.0, PnL×1.0, DD×1.2, explore=0.0
```

**Problem:** Phase A çok kolay, Phase C'ye geçişte agent şok yaşıyor. Smooth interpolation var ama geçiş hâlâ sert.

---

## 5. Veri Kalitesi ve State Representation

### 5.1 Feature Matrisi (24 boyut)

| Grup | Features | Scaler | Kalite |
|---|---|---|---|
| **Teknik** (13) | close, ema_20/50/200, rsi, macd, macd_signal, macd_hist, atr, bb_upper/lower, volume, volume_avg_20 | zscore | ✅ İyi |
| **Regime** (3) | regime_trend, regime_range, regime_volatility | none (binary) | ⚠️ Basit |
| **Sentiment** (2) | sentiment_score, news_sentiment | robust | 🟡 Genellikle 0 |
| **Onchain** (2) | onchain_active_addresses, onchain_tx_volume | robust | 🔴 Hep 0 |
| **Portfolio** (4) | cash_ratio, position_ratio, open_risk, kelly_fraction | minmax | 🔴 Statik |

### 5.2 Kritik Veri Sorunları

1. **Onchain features tamamen placeholder (0.0):**
   - Equities için onchain verisi mantıksız
   - 2/24 feature boş → agent bu boyutları ignore ediyor
   - Feature space gereksiz büyük

2. **Sentiment genellikle 0:**
   - `_add_placeholder_features()` sentiment'ı 0.0 ile dolduruyor
   - DDG scraping bazen başarısız, fallback = 0
   - Eğitimde çoğu satır sentiment=0 → Agent sentiment'ı ignore ediyor

3. **Portfolio state eğitimde statik:**
   - `cash_ratio=1.0, position_ratio=0.0, open_risk=0.0, kelly_fraction=0.0` sabit
   - Agent bu feature'ları hiç öğrenememiş
   - 4/24 feature etkisiz

4. **Feature Scaling sorunları:**
   - `close` fiyatı zscore ile scale ediliyor ama AAPL ($150-200) vs TSLA ($180-400) çok farklı
   - Multi-asset concat'te istatistikler karışıyor
   - ATR, volume gibi magnitude-sensitive feature'lar semboller arası tutarsız

5. **Toplam etki:** 24 feature'ın yalnızca ~16'sı gerçekten bilgi taşıyor. Etkili feature ratio: **~67%**

### 5.3 FeaturePipeline Değerlendirmesi

| Bileşen | Durum |
|---|---|
| zscore normalization | ✅ İyi |
| robust (median/IQR) | ✅ İyi |
| minmax scaling | ✅ İyi |
| NaN/Inf handling | ✅ `nan_to_num + clip(−10, 10)` |
| Feature validation | ✅ `fit()` sırasında column check |
| Pipeline serialization | ✅ JSON artifact olarak kayıt |

---

## 6. Maksimum Verim İçin Gerekli Ajan Sayısı

### 6.1 Mevcut Durum: 5 ajan, 1 çalışıyor

5 modelin 4'ü ya ölü ya zayıf. Bu, "çok ajan eğitin, en iyisini seçin" yaklaşımının **naive versiyonu**. Hyperparametre farklılıkları yeterli değil.

### 6.2 Önerilen Ajan Mimarisi: **3 Katmanlı Ensemble (9 Ajan)**

```
KATMAN 1: REGIME-SPECIFIC AJANLAR (3 ajan)
  ├── trend_agent   — Trend piyasalarda uzmanlaşmış
  ├── range_agent   — Yatay (mean-revert) piyasalarda uzman
  └── volatile_agent — Yüksek volatilite dönemlerinde uzman

KATMAN 2: ASSET CLASS AJANLAR (3 ajan)
  ├── tech_agent    — US Teknoloji (AAPL, NVDA, MSFT, GOOGL, META)
  ├── broad_agent   — ETF + Diversified (SPY, QQQ, IWM)
  └── momentum_agent — Yüksek-beta momentum (TSLA, AMD, COIN)

KATMAN 3: META-AJAN / ROUTER (3 ajan → 1 ensemble)
  ├── conservative_ensemble — Düşük risk, düşük turnover
  ├── aggressive_ensemble  — Yüksek frekans, yüksek risk
  └── adaptive_router      — Hangi ajanı ne zaman dinleyeceğine karar verir
```

### 6.3 Neden 9?

| Ölçüt | Açıklama |
|---|---|
| **Regime çeşitliliği** | En az 3 piyasa koşulu (trend/range/volatile) → 3 uzman ajan |
| **Asset çeşitliliği** | Korelasyon grupları ayrı eğitim → 3 asset ajan |
| **Risk profili** | Conservative + Aggressive + Adaptive → 3 ensemble ajan |
| **Computational budget** | Her ajan 200K-500K step, 3 sembol minimum → 9 × ~30dk = ~4.5 saat |

### 6.4 Minimum Viable: **3 Ajan**

Budget kısıtlı ise **minimum 3 ajan**:
1. `trend_ppo` — Trend rejimde aktif, başka zaman HOLD
2. `meanrevert_ppo` — Range rejimde aktif
3. `defensive_ppo` — Volatilite rejimde risk azaltan

Bu 3'lü bile mevcut 5 ajan × tek rejim yaklaşımından **çok daha etkili** olacaktır.

---

## 7. Eğitim Stratejisi

### 7.1 Mevcut Eğitim Sorunları

| Sorun | Sebep | Çözüm |
|---|---|---|
| 3/5 model ölü | Yetersiz timestep + veri | Min 200K step, 10+ sembol |
| Sadece 3 sembol | Generalization = 0 | 15-20 sembol, sektör çeşitliliği |
| Multi-asset concat | İstatistikler karışıyor | Per-symbol normalization |
| train/test aynı semboller | Data leakage riski | Train/test farklı semboller |
| 80/20 kronolojik split | Tek dönem test | Walk-forward 5+ fold |

### 7.2 Önerilen Eğitim Pipeline'ı

```
1. VERİ HAZIRLIK
   ├── 20 sembol × 3yr daily veri (≈15,000 satır/sembol)
   ├── Train symbols: AAPL, MSFT, GOOGL, AMZN, NVDA, META, AMD, CRM
   ├── Validation symbols: ADBE, INTC, QCOM, PYPL
   ├── Test symbols (hiç eğitimde kullanılmayan): TSLA, NFLX, SPY, QQQ
   └── Feature engineering: 24 → 30+ feature (makro ekle)

2. EĞİTİM
   ├── Per-regime data split (trend/range/volatile günleri ayrı)
   ├── 500K timestep minimum
   ├── Curriculum: 5-phase (exploration → easy → medium → hard → adversarial)
   ├── Early stopping on validation Sharpe plateau
   └── Hyperparameter search: Optuna Bayesian (50 trial)

3. DOĞRULAMA
   ├── Walk-forward: 10 fold, anchored
   ├── Overfitting test: train Sharpe / test Sharpe < 1.5×
   ├── Out-of-distribution test: hiç görülmemiş sembollerle
   ├── Regime transition test: trend→range geçiş gücü
   └── Sharpe confidence interval (bootstrap)

4. DEPLOYMENT
   ├── Ensemble voting (3+ ajan consensus)
   ├── Rolling retrain: ayda 1 — son 6 ay verisiyle
   └── Shadow mode: 2 hafta paper trade → canlı
```

### 7.3 Hyperparametre Önerileri

| Parametre | Mevcut (longhorizon) | Önerilen |
|---|---|---|
| total_timesteps | 100K | 500K-1M |
| learning_rate | 2e-4 | 1e-4 → cosine anneal |
| gamma | 0.995 | 0.99 (regime-dependent) |
| ent_coef | 0.01 | 0.02 (daha fazla exploration) |
| n_steps | default (2048) | 4096 |
| batch_size | default (64) | 256 |
| n_epochs | default (10) | 5 (overfitting azaltma) |
| clip_range | default (0.2) | 0.15 |
| max_grad_norm | default (0.5) | 0.3 |
| network | [64, 64] | [256, 128, 64] |

---

## 8. Performans Optimizasyonu

### 8.1 Kısa Vadeli İyileştirmeler (1-2 hafta)

1. **Ölü feature'ları temizle:**
   - `onchain_active_addresses`, `onchain_tx_volume` → kaldır (veya gerçek veri bağla)
   - Eğitimde statik olan `cash_ratio, position_ratio, open_risk, kelly_fraction` → simüle et

2. **Reward rebalancing:**
   ```python
   # Mevcut: drawdown 0-1 aralığında, PnL 0.001 aralığında → drawdown domine ediyor
   # Çözüm: PnL'yi scale et
   reward.pnl = 10.0  # 1.0 → 10.0
   reward.drawdown = 0.5  # 1.0 → 0.5
   reward.inactivity_penalty = 0.01  # 0.003 → 0.01
   reward.position_bonus = 0.005  # 0.002 → 0.005
   ```

3. **Veri artırma:**
   - 3 sembol → 15 sembol (AAPL, MSFT, GOOGL, AMZN, NVDA, META, AMD, CRM, ADBE, INTC, SPY, QQQ, IWM, TSLA, NFLX)
   - 2yr → 5yr veri
   - Timestep: 100K → 500K

4. **Terminal reward:**
   ```python
   if terminated:
       final_sharpe = np.mean(returns_buffer) / (np.std(returns_buffer) + 1e-8)
       reward += 5.0 * np.clip(final_sharpe, -2, 2)  # Episode sonu Sharpe bonus
   ```

### 8.2 Orta Vadeli İyileştirmeler (2-4 hafta)

1. **Per-symbol normalization:** Multi-asset concat yerine her sembolü kendi istatistikleriyle normalize et
2. **Regime-conditioned training:** Trend günlerinde ayrı eğitim, range günlerinde ayrı
3. **LSTM/Transformer:** MlpPolicy → RecurrentPPO (sequential dependency öğrenme)
4. **Prioritized Experience Replay:** Zor market koşullarını daha çok öğret
5. **Makro features ekle:** VIX, 10yr yield, DXY

### 8.3 Uzun Vadeli İyileştirmeler (1-3 ay)

1. **Multi-agent ensemble:** 9 uzman ajan + router
2. **Sim-to-real transfer:** Sintetik veri (GAN) + gerçek veri karışım
3. **Online learning:** Canlı piyasadan sürekli öğrenme (micro-batch)
4. **Risk parity integration:** Ajan çıktılarını risk parity ile ağırlıklandır

---

## 9. Aktif Kullanım Stratejisi

### 9.1 Mevcut Durum

- Aktif model: **ppo_longhorizon** (tek ajan)
- Inference: `DRLInference.predict(symbol)` → `PredictionResult`
- Hybrid engine: Scanner + DRL consensus
- Güven eşiği: 0.3 (continuous action → BUY/SELL/HOLD)

### 9.2 Önerilen Kullanım Hiyerarşisi

```
SINYAL ÜRETME
  Scanner (kural tabanlı) ─────────────────────┐
  DRL Agent (ppo_longhorizon) ─────────────────┤
  AI Research (Groq/Gemini) ──────────────────┤
                                                ▼
                                      Hybrid Consensus
                                        │
                        ┌───────────────┼────────────────┐
                        ▼               ▼                ▼
                    3/3 AGREE      2/3 AGREE         DISAGREE
                    → EXECUTE      → CAUTION          → HOLD
                    (Full pos)     (½ position)       (No trade)
```

### 9.3 DRL Güven Seviyesi Haritalama

| DRL Confidence | Eylem | Pozisyon Boyutu |
|---|---|---|
| > 0.8 | Güçlü sinyal, Scanner ile uyunca execute | %15-20 portföy |
| 0.6-0.8 | Orta sinyal, yalnızca Scanner onaylarsa | %10 portföy |
| 0.4-0.6 | Zayıf sinyal, yalnızca bilgi amaçlı | %5 veya bekle |
| < 0.4 | Ses/noise — ignore et | %0 |

### 9.4 Risk Kontrol Kuralları

1. **Max single-position:** %20 (PilotShield max_absolute_position = 0.75 → normalize)
2. **Max drawdown stop:** Equity %10 düşerse tüm pozisyonları kapat
3. **Daily trade limit:** Max 5 işlem/gün (turnover penalty'nin canlı karşılığı)
4. **Regime check:** Volatility rejimde pozisyon boyutunu %50 azalt
5. **Model confidence decay:** Son 30 günde DRL win_rate < %25 ise ajan'ı devre dışı bırak

---

## 10. Riskler ve Sınırlamalar

### 10.1 Yüksek Riskler 🔴

| Risk | Olasılık | Etki | Mitigasyon |
|---|---|---|---|
| **Overfitting** — 9/15 fold overfit | Yüksek | Gerçek piyasada kayıp | Walk-forward + OOD test |
| **Distribution shift** — Piyasa rejimi değişimi | Yüksek | Policy geçersiz olur | Rolling retrain + regime filter |
| **Single model dependency** — 1 aktif ajan | Yüksek | Tek nokta arıza | Ensemble (3+ ajan) |
| **Data quality** — Placeholder features | Kesin | Yanlış sinyaller | Feature audit + temizlik |

### 10.2 Orta Riskler 🟡

| Risk | Açıklama |
|---|---|
| **Liquidity** | Gerçek piyasa slippage modelden çok farklı olabilir |
| **Latency** | Inference latency > market move hızı |
| **Concept drift** | Piyasa yapısal değişim (AI trading artışı vb.) |
| **Regulatory** | Algoritmic trading düzenlemeleri |

### 10.3 Düşük Riskler 🟢

| Risk | Açıklama |
|---|---|
| **Infrastructure** | SB3 + PyTorch stack stabil |
| **Computation** | CPU inference yeterli (GPU gereksiz) |
| **API limits** | yfinance + DDG rate limiting mevcut |

### 10.4 Kritik Uyarı

> ⚠️ **Bu DRL ajanları ARAŞTIRMA durumundadır.** Gerçek para ile kullanılmamalıdır. Mevcut performans metrikleri (Sharpe 0.735) sınırlı veri ve basit backtest ile elde edilmiştir. Live trading'e geçmeden önce minimum 6 ay paper trading gereklidir.

---

## 11. Yol Haritası

### Sprint 16: Foundation Fix (1 hafta)
- [ ] Ölü feature'ları temizle (onchain → kaldır veya mock)
- [ ] Reward function rebalancing (PnL×10, DD×0.5)
- [ ] Eğitim verisi genişlet (3 → 15 sembol)
- [ ] Portfolio state simülasyonu ekle (eğitimde dinamik cash_ratio)
- [ ] Timestep artışı: 100K → 500K
- [ ] Terminal reward ekle

### Sprint 17: Multi-Regime Training (1 hafta)
- [ ] Regime-specific veri bölümleme
- [ ] 3 regime uzman ajan eğit (trend, range, volatile)
- [ ] Per-symbol normalization
- [ ] Optuna hyperparameter search (50 trial)

### Sprint 18: Ensemble & Validation (1 hafta)
- [ ] Regime-router ajan eğit
- [ ] Ensemble voting mekanizması
- [ ] 10-fold walk-forward validation
- [ ] Out-of-distribution test (hiç görülmemiş sembollerle)
- [ ] Bootstrap confidence intervals

### Sprint 19: Advanced Features (2 hafta)
- [ ] Makro features ekle (VIX, yield curve, DXY)
- [ ] RecurrentPPO (LSTM policy)
- [ ] Multi-timeframe features (1d + 1h)
- [ ] Improved sentiment (FinBERT → VADER yerine)

### Sprint 20: Production Readiness (2 hafta)
- [ ] Paper trading pipeline
- [ ] A/B testing framework (Scanner vs DRL vs Ensemble)
- [ ] Automated retrain cron job (haftalık)
- [ ] Monitoring dashboard (Sharpe decay, drift detection)
- [ ] Alerting (win_rate < %25 → model disable)

---

## 12. Genel Özet (Executive Summary)

### Mevcut Durum

FinPilot DRL stack'i **erken araştırma aşamasındadır.** 5 PPO ajandan yalnızca 1 tanesi (ppo_longhorizon) anlamlı bir trading policy öğrenmiştir. Diğer 3'ü tamamen ölü (constant HOLD), 1'i zayıf. Tek çalışan model Test Sharpe 0.735 ile kabul edilebilir ama güvenilir değildir (%49.6 overfitting, 9/15 fold fail).

### Temel Bulgular

| Alan | Değerlendirme | Skor |
|---|---|---|
| Model çeşitliliği | 5 ajan var, 1 çalışıyor → **yetersiz** | ★☆☆☆☆ |
| Performans | Sharpe 0.735 → kabul edilebilir ama güvenilmez | ★★☆☆☆ |
| Veri kalitesi | 8/24 feature boş veya statik → **kötü** | ★★☆☆☆ |
| Reward tasarımı | Multi-signal ama dengesiz → **orta** | ★★★☆☆ |
| Eğitim altyapısı | Curriculum + WFO + registry → **iyi** | ★★★★☆ |
| Risk kontrolü | PilotShield + confidence + hybrid → **iyi** | ★★★★☆ |
| Production readiness | Paper trade yok, tek model → **düşük** | ★☆☆☆☆ |

### Öncelik Sıralaması

1. **🔴 ACİL:** Reward rebalancing + veri genişletme + 500K timestep retrain
2. **🟡 KISA VADE:** Ölü feature temizliği + 15 sembol + per-symbol normalization
3. **🟢 ORTA VADE:** Regime-specific ajanlar + ensemble + validation
4. **🔵 UZUN VADE:** RecurrentPPO + makro features + production pipeline

### Tahmini Hedefler

| Metrik | Mevcut | Hedef (3 ay) | Hedef (6 ay) |
|---|---|---|---|
| Aktif Ajan | 1/5 | 3/3 (regime uzmanlar) | 9 (full ensemble) |
| Test Sharpe | 0.735 | >1.2 | >1.5 |
| Win Rate | 30% | >45% | >50% |
| Overfit Rate | 60% | <30% | <20% |
| Sembol Coverage | 3 | 15 | 30+ |
| Feature Utilization | 67% | 90%+ | 95%+ |

---

*Bu rapor `/workspaces/Borsa/docs/DRL_AGENT_ANALYSIS.md` olarak kaydedilmiştir.*
*Son güncelleme: 2026-02-25*
