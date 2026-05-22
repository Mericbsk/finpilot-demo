# Sprint 15 — Gap Report

## Tamamlanan İşler

### 1. `requirements.txt` — ML bağımlılıkları eklendi
- `scipy>=1.13.0` — KS-test drift detection için (Sprint 14 eksikti)
- `optuna>=3.6.0` — Optuna sweep için
- `lightgbm>=4.3.0` — Layer-2 ranker için

### 2. `research/lgbm_ranker.py` — LightGBM Layer 2 Ranker PoC
- `LGBMRanker` sınıfı: `LGBMClassifier` wrapper, `fit()`, `predict_proba()`, `save()`, `load()`
- `run_walkforward_eval()`: 12 fold, 24m train / 6m val, AUC hesaplama
- `rank_signals()`: production API — `lgbm_score` field ekler, sinyalleri sıralar
- `get_ranker()`: global singleton, diskten lazy load
- Sonuçlar `data/lgbm_ranker_wf.json`'a yazılır
- Fallback: LightGBM yoksa orijinal sıralama korunur (hata yutulur)

### 3. `core/regime_weights.py` — Per-regime weight set
- 3 rejim × 10 named weight: `bull`, `bear`, `range`
- `data/regime_weights.json`'da persist edilir
- `detect_current_regime()`: SPY 200-day SMA heuristic (1h TTL cache)
- `get_active_weights()`: aktif rejim için weight dict döner
- `set_regime_weights()`: kalibrasyon tarafından güncellenecek (Sprint 16)

### 4. `scanner/features.py` — Sector RS + Vol Regime alpha features
- `compute_sector_rs(sector)`: ETF (XLK, XLV, vb.) 20d return − SPY 20d return
- `compute_vol_regime(symbol)`: 20d realised vol annualised → 0/1/2 bucket
- `get_alpha_features(symbol, sector)`: 1 saatlik in-memory cache ile ikisini birleştirir
- 11 sektör → ETF mapping (GICS)

### 5. `scanner/earnings_blackout.py` — Earnings blackout filter
- `is_earnings_blackout(symbol, days_before=2, days_after=1)`: True → sinyal baskılama
- `earnings_proximity(symbol, decay_days=7)`: [0,1] yakınlık skoru (LightGBM feature)
- 6 saatlik yfinance calendar cache

### 6. `scanner/evaluate.py` — Entegrasyon
- Earnings blackout: `entry_ok = False` yapılır, `earnings_blackout`, `earnings_proximity` alanları eklendi
- Alpha features: `sector_rs`, `vol_regime` alanları eklendi
- Tüm yeni alanlar return dict'e eklendi

## Eksikler / Sonraki Sprint

| Konu | Durum | Not |
|------|-------|-----|
| LightGBM walk-forward gerçek veriyle test | ❌ | Labelled outcome verisi yeterli olunca çalışır |
| Per-regime weight calibration (otomatik) | ❌ | Sprint 16: Optuna ile haftalık tune |
| `sector_rs` feature evaluate.py'de sektör bilgisi | ⚠️ | evaluate.py sektör bilgisi yfinance'ten alınmalı |
| Regime weights → LightGBM ranker entegrasyonu | ❌ | `get_active_weights()` ranker feature multiplier olarak |
| API endpoint: `/py-api/research/lgbm-wf` | ❌ | Walk-forward sonuçlarını UI'a sunan endpoint |
| Dashboard: LGBM vs Layer-1 AUC karşılaştırması | ❌ | Sprint 16 |
| `optuna` container kurulumu verify | ⚠️ | `pip install optuna lightgbm scipy` gerekli |

## Sonraki Sprint (S16) Önerisi
- Confidence Card UI (Brier-derived güvenilirlik %)
- Stripe paywall (test mode + 7 günlük trial)
- Per-regime Optuna weight tuning (haftalık, audit'li)
- LGBM walk-forward API endpoint + dashboard tile
- LightGBM ranker → scanner entegrasyonu (sinyal sıralaması)
