# Sprint 23 — Trend Agent Yeniden Eğitimi

## 🎯 Amaç

Sprint 16'da eğitilen `ppo_trend_20260225_181020` modeli, Sprint 19'da tanımlanan Specialist mimarisinden **önce** oluşturulduğu için şu kritik eksikliklere sahip:

| Sorun | Sprint 16 (mevcut) | Sprint 19 (hedef) |
|---|---|---|
| Feature pipeline | 24 ham kolon (`close`, `ema_20`…) | 22 normalize ratio (`close_ema20_ratio`…) |
| Observation stacking | n_stack=1 (temporal bağlam yok) | n_stack=4 (son 4 bar görülür) |
| Scaler | zscore ama stats=None → scaling çalışmıyor | robust, fit edilmiş |
| Reward profili | Generic (pnl=10, dd=0.3) | Trend-özel (pnl=12, dd=0.2, cost=0.05) |
| Data filter | Tüm rejimler (unfiltered) | Sadece `regime_focus="trend"`, `trend_strength_min=0.005` |
| Feature boost | Yok | technicals×1.2, regime×1.5, portfolio×2.25 |
| Eğitim adımı | 500K (yetersiz) | 3M (önerilen) |
| log_std | -0.06 (≈ rastgele) | Hedef: < -0.5 (converge) |

**Hedef:** Trend agentini Sprint 19 specialist profiline göre yeniden eğitip, ensemble router'a aktif olarak geri kazandırmak.

---

## 🏗️ Mimari

```
Ensemble Router
├── trend_ppo   ← BU SPRINT'İN KONUSU
├── range_ppo   (mevcut aktif — karşılaştırma referansı)
└── volatile_ppo (mevcut)

Trend Agent Rolü:
  - HMM regime_trend = 1.0 olduğunda yüksek ağırlık alır
  - Süregelen yönlü hareketleri takip eder (momentum-following)
  - Pullback'lere dayanıklı (düşük drawdown cezası)
  - Az sayıda ama uzun süreli pozisyon (düşük turnover)

Specialist Config (drl/specialists.py → SpecialistTag.TREND):
  RewardProfile:  pnl=12.0, drawdown=0.2, cost=0.05, regime_bonus=0.1
  DataFilter:     regime_focus="trend", trend_strength_min=0.005
  FeatureBoost:   technicals=1.2, regime=1.5, portfolio=2.25
  n_stack:        4
  recommended:    3,000,000 timesteps
```

---

## 📋 Görevler

### Faz 1: Veri & Pipeline Hazırlığı (Gün 1)

| # | Görev | Detay | Dosya |
|---|---|---|---|
| 1.1 | Sembol evreni doğrulama | Mevcut 15 sembol yeterli, ancak Sprint 19 sembollerini (48) kontrol et | `scripts/train_sprint18.py` |
| 1.2 | Veri indirme & regime tagging | yfinance 2y period, HMM regime detection uygula | `drl/data_loader.py` |
| 1.3 | Data filter test | `filter_multi_symbol(data, trend.data_filter)` ile kaç satır kalıyor kontrol et | `drl/specialists.py` |
| 1.4 | Pipeline fit doğrulama | `FeaturePipeline(config).fit()` sonrası scaler_stats'ın dolu olduğunu doğrula | `drl/feature_pipeline.py` |

**Kabul kriteri:** `scaler_stats` tüm gruplar için None değil, en az 5000 trend-only satır mevcut.

### Faz 2: Eğitim (Gün 1-2)

| # | Görev | Detay |
|---|---|---|
| 2.1 | train_sprint18.py ile eğitim başlat | `python scripts/train_sprint18.py --agent trend --timesteps 1500000 --curriculum --n-stack 4 --symbol-set sp500_top` |
| 2.2 | İlk 1.5M adım kontrol | Orta noktada log_std, avg_reward, action diversity kontrol et |
| 2.3 | İkinci faz 1.5M (isteğe bağlı) | İlk faz iyi ise `--timesteps 3000000` ile tekrar eğit, yoksa hyperparameter ayarla |

**Eğitim komutu:**
```bash
python scripts/train_sprint18.py \
  --agent trend \
  --algorithm PPO \
  --timesteps 1500000 \
  --n-stack 4 \
  --lr 0.0003 \
  --curriculum \
  --symbol-set sp500_top \
  --period 2y \
  --seed 42
```

**Kabul kriteri:**
- `log_std < -0.5` (politika yakınsamış)
- `avg_reward > 0` (kârlı)
- `action_diversity < 0.5` (kararlı ama monoton değil)
- `sharpe > 0.05`

### Faz 3: Değerlendirme (Gün 2)

| # | Görev | Detay |
|---|---|---|
| 3.1 | Test seti metrikleri | Sharpe, return, max_dd, n_trades — eski model ile karşılaştır |
| 3.2 | Inference testi | 1000 rastgele obs ile aksiyon dağılımı kontrol (AL/BEKLE/SAT) |
| 3.3 | Regime alignment testi | `regime_trend=1` satırlarında doğru mu davranıyor? `regime_range=1` satırlarında sessiz mi? |
| 3.4 | Feature importance | SHAP / permutation importance — technicals ve regime grupları baskın mı? |

**Eski model referans:**
```
ppo_trend_20260225 (Sprint 16):
  sharpe=0.028, return=79.25%, max_dd=15.88%, avg_reward=-0.006
  log_std=-0.064, 170 trades
```

**Kabul kriteri:** Her 4 metrikte de eski modelden iyi, özellikle sharpe > 0.05 ve avg_reward > 0.

### Faz 4: Ensemble Entegrasyon (Gün 3)

| # | Görev | Detay | Dosya |
|---|---|---|---|
| 4.1 | Registry'ye kaydet | `is_active=True`, eski modeli `is_active=False` tut | `models/registry.json` |
| 4.2 | Ensemble router testi | 3 ajan birlikte yükle, 10 sembol üzerinde batch_predict çalıştır | `drl/ensemble_router.py` |
| 4.3 | Regime routing doğrulama | `regime_trend=1` → trend ajan yüksek ağırlık, `regime_range=1` → düşük ağırlık | ensemble_router test |
| 4.4 | Agreement score kontrolü | 3 ajan arasında ciddi anlaşmazlık var mı? Varsa threshold ayarla | `disagreement_hold_threshold` |

**Kabul kriteri:** Ensemble batch_predict çalışıyor, trend ajanı regime_trend periyotlarında dominant.

### Faz 5: Canlı Onay & Monitoring (Gün 3-4)

| # | Görev | Detay |
|---|---|---|
| 5.1 | Dashboard'da görüntüleme | AI Lab tabında yeni model registry'de görünüyor | Streamlit UI |
| 5.2 | Paper trading testi | 1 gün paper trade ile ensemble prediction'ları izle | `scripts/auto_scan_trade.py` |
| 5.3 | LearnableWeights reset | Ensemble meta-learner sıfırdan başlasın (eski performans bias'ı temizle) | `ensemble_router.py` |

---

## 🔢 Sprint 16 vs Sprint 23 — Beklenen Fark

| Metrik | Sprint 16 (mevcut) | Sprint 23 (hedef) | Neden? |
|---|---|---|---|
| **obs space** | 24 (raw) | 22×4=88 (stacked, normalized) | Temporal bağlam + proper scaling |
| **scaler_stats** | None (5/5 grup) | Fitted (4/5 grup, onchain=0) | `pipeline.fit()` düzgün çalışacak |
| **reward** | Generic 3-term | Specialist (pnl=12, dd=0.2, cost=0.05) | Trend davranışını ödüllendiren profil |
| **data** | Tüm rejimler | Sadece trend periyotları | Ajanın sadece kendi uzmanlık alanını görmesi |
| **timesteps** | 500K | 1.5M–3M | Convergence için yeterli süre |
| **log_std** | -0.06 (random) | < -0.5 (converged) | Kararlı politika |
| **action dist** | 53% AL / 41% SAT / 5% BEKLE | ~45% AL / 20% BEKLE / 35% SAT | Daha dengeli karar dağılımı |

---

## ⚠️ Riskler & Çözümler

| Risk | Olasılık | Etki | Çözüm |
|---|---|---|---|
| Trend-only data çok az (< 5000 satır) | Orta | Eğitim yetersiz | Sembol evrenini genişlet (48→100) veya `trend_strength_min` düşür (0.005→0.003) |
| Yeni model de converge etmez | Düşük | Sprint boşa gider | Fazlı yaklaşım: önce 1.5M → kontrol → sonra 3M |
| Ensemble'da mevcut ajanlarla çakışma | Düşük | Agreement score düşer | `disagreement_hold_threshold` kalibrasyonu |
| Curriculum learning instability | Orta | Eğitim salınım yapar | `smooth=True` + reward clipping + curriculum phase 1 uzun tut |

---

## 📎 İlgili Dosyalar

| Dosya | Rol |
|---|---|
| `scripts/train_sprint18.py` | Ana eğitim betiği (Sprint 19 specialist desteği mevcut) |
| `drl/specialists.py` | `SPECIALIST_CATALOG[SpecialistTag.TREND]` — tüm config burada |
| `drl/ensemble_router.py` | Ensemble routing + regime prior hesaplama |
| `drl/feature_pipeline.py` | Feature scaling / pipeline fit |
| `drl/market_env.py` | Gymnasium env — reward hesaplama burada |
| `drl/config.py` | `DEFAULT_CONFIG`, `RewardWeights`, `FeatureSpec` |
| `models/registry.json` | Model kayıt defteri |

---

## ✅ Tamamlanma Kriteri

- [ ] Yeni trend modeli `models/ppo_trend_{timestamp}/` altında kaydedildi
- [ ] `pipeline.json` içinde `scaler_stats` tüm aktif gruplar için dolu
- [ ] Test seti Sharpe > 0.05
- [ ] avg_reward > 0
- [ ] log_std < -0.5
- [ ] Ensemble router 3 ajan ile çalışıyor
- [ ] `regime_trend=1` periyotlarında trend ajan dominant
- [ ] Eski model pasif, yeni model `is_active=True` olarak registry'de
