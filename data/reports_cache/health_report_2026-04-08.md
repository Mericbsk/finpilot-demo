# 🏥 FinPilot Günlük Sağlık Raporu — 2026-04-08

## Özet
| Metrik | Değer | Durum |
|--------|-------|-------|
| Log Hata Sayısı (ERROR) | 453 | ⚠️ |
| Log Failed Sayısı | 2758 | ⚠️ |
| Log CRITICAL | 0 | ✅ |
| Shortlist Veri Tazeliği | ~22 saat | ✅ |
| Suggestions Veri Tazeliği | ~1701 saat (~71 gün) | 🚨 |
| Test Dosyası | 23 dosya / 466 fonksiyon | ✅ |
| Model Artifact | 40 ZIP dosyası | ✅ |
| Config (.env) | Tüm 11 key mevcut | ✅ |
| API Endpoint | 10 router / 27 endpoint | ✅ |
| Secret Key | Özelleştirilmiş | ✅ |
| Pinned Dependencies | 28/28 | ✅ |

---

## Detaylar

### 1. Log Anomali Taraması

**Taranan log dosyaları:** `logs/` klasöründeki tüm `.log` dosyaları (api.log, auto_scan_trade.log, full_scan_20260302_2018.log, optuna_*.log, retrain_*.log, vb.)

| Pattern | Sayı |
|---------|------|
| ERROR | 453 |
| CRITICAL | 0 |
| Exception | 0 |
| Failed | 2758 |
| **Toplam** | **3211** |

**Top-5 En Sık Tekrarlanan Hata:**

1. **yfinance Delisted Ticker (uzun format)** — *312 tekrar*
   - `ERROR | yfinance | $TICKER: possibly delisted; no price data found (Yahoo error = "No data found, symbol may be delisted")`
   - Etkilenen örnekler: $SUMO, $SPLK, $TICKER.B sınıfı kağıtlar

2. **yfinance Delisted Ticker (kısa format)** — *68 tekrar*
   - `ERROR | yfinance | $TICKER: possibly delisted; no price data found`

3. **Failed download (genel)** — *15 tekrar*
   - `1 Failed download:` — yfinance batch indirme hatası

4. **yfinance Generic ERROR** — *13 tekrar*
   - `ERROR | yfinance |` — mesaj gövdesi boş veya ayrıştırılamayan format

5. **API Socket Hang Up** — *4 tekrar*
   - `Failed to proxy http://localhost:8000/api/v1/scan Error: socket hang up`
   - API servis geçici bağlantı kopması

**Ek Dikkat Notu:** `Warning: Failed to fetch real altdata` mesajları `ndarray of shape (24, 1)` boyut uyumsuzluğuyla birlikte görülmekte; ZM, ZS, ZTEK gibi tickerlar için sentetik veriye düşüyor.

---

### 2. Veri Tazelik Kontrolü

**`data/shortlists/`**
- En son dosya: `shortlist_20260407_1317.csv`
- Son değiştirilme: 2026-04-07 15:17
- Yaş: **~22 saat** → ✅ (24 saatten az, sınıra yakın)

**`data/suggestions/`**
- En son dosya: `suggestions_fromcsv_...20250916_1811.csv`
- Son değiştirilme: **2026-01-27**
- Yaş: **~1701 saat (~71 gün)** → 🚨 KRİTİK UYARI
- Suggestions klasörü 71 gündür güncellenmemiş. Bu klasörün hâlâ aktif kullanımda olup olmadığı netleştirilmeli.

---

### 3. Test Envanteri

| Dosya | Test Sayısı |
|-------|------------|
| test_social.py | 40 |
| test_core.py | 38 |
| test_validation.py | 37 |
| test_llm.py | 32 |
| test_prometheus.py | 31 |
| test_auth.py | 31 |
| test_websocket_feeds.py | 30 |
| test_signals.py | 23 |
| test_plugins.py | 23 |
| test_sentry.py | 22 |
| test_backtest.py | 22 |
| test_data_fetcher.py | 21 |
| test_indicators.py | 19 |
| test_broker.py | 18 |
| test_db_repos.py | 17 |
| test_views_smoke.py | 16 |
| test_evaluate.py | 14 |
| test_views_integration.py | 8 |
| test_db_backend.py | 8 |
| test_feature_generators.py | 5 |
| test_drl_integration.py | 5 |
| test_explainability.py | 3 |
| test_alignment_helpers.py | 3 |
| **TOPLAM** | **466** |

- **En son eklenen test dosyası:** `test_db_backend.py` (2026-04-03)

---

### 4. Model Artifact Kontrolü

**Toplam ZIP dosyası:** 40 adet ✅

| Klasör | Boyut | Son Güncelleme |
|--------|-------|----------------|
| best/best_model.zip | 168K | 2026-02-26 |
| checkpoints/ (10 zip) | 3.3M toplam | 2026-02-17 |
| ppo_aggressive_20260302 | 264K | 2026-03-02 |
| ppo_breakout_20260302 | 264K | 2026-03-02 |
| ppo_conservative_20260302 | 264K | 2026-03-02 |
| ppo_conservative_20260304 | 692K | 2026-03-05 |
| ppo_conservative_20260306 | 692K | 2026-03-06 |
| ppo_meanrev_20260302 | 264K | 2026-03-02 |
| ppo_momentum_20260302 | 264K | 2026-03-02 |
| ppo_momentum_20260303 | 264K | 2026-03-03 |
| ppo_momentum_20260306 | 692K | 2026-03-06 |
| ppo_range_20260226 | 168K | 2026-02-26 |
| ppo_scalper_20260302 | 400K | 2026-03-02 |
| ppo_trend_20260225 | 168K | 2026-02-26 |
| ppo_trend_20260304 (x2) | 692K her biri | 2026-03-04 |
| ppo_trend_20260304_233619 | 692K | 2026-03-05 |
| ppo_trend_20260305_233633 | 692K | 2026-03-06 |
| ppo_volatile_20260225 | 168K | 2026-02-26 |
| rppo_swing_20260302 | 7.1M | 2026-03-02 |
| rppo_swing_20260304 | 7.1M | 2026-03-04 |

- **En yeni model:** ppo_conservative_20260306 / ppo_momentum_20260306 (2026-03-06)
- **Tüm modeller mevcut** — eksik artifact yok ✅

---

### 5. Konfigürasyon Kontrolü

| Kontrol | Sonuç |
|---------|-------|
| `.env` dosyası varlığı | ✅ Mevcut |
| `user_settings.json` geçerliliği | ✅ Geçerli JSON |
| `.env.example` ↔ `.env` key eşleşmesi | ✅ Tüm 11 key mevcut |

**`.env` Keys (11 adet):** `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `FINPILOT_SECRET_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `MLFLOW_TRACKING_URI`, `NEWS_API_KEY`, `POLYGON_API_KEY`, `REDIS_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

**`user_settings.json` içerdiği alanlar:** `risk_score`, `portfolio_size`, `max_loss_pct`, `strategy`, `market`, `telegram_active`, `telegram_id`, `timeframe`, `indicators`

---

### 6. API Router Envanteri

| Router Dosyası | Endpoint Sayısı |
|----------------|----------------|
| trade.py | 5 |
| history.py | 4 |
| models.py | 4 |
| optuna.py | 4 |
| inference.py | 2 |
| scan.py | 2 |
| user.py | 3 |
| backtest.py | 1 |
| ensemble.py | 1 |
| llm.py | 1 |
| **TOPLAM** | **27** |

---

### 7. Güvenlik Kontrol Listesi

| Kontrol | Sonuç |
|---------|-------|
| `FINPILOT_SECRET_KEY` placeholder değil mi? | ✅ Özelleştirilmiş (64-char hex) |
| `requirements.txt` pinned versiyonlar | ✅ 28/28 paket `==` ile sabitlenmiş |

---

## Eylem Gerektirenler

### 🚨 Kritik
1. **`data/suggestions/` klasörü 71 gündür güncellenmemiş** (son güncelleme: 2026-01-27).
   - Bu klasör hâlâ aktif pipeline'a bağlıysa, suggestions akışı duraklamış demektir.
   - Kontrol: suggestions üretiminden sorumlu süreç hâlâ çalışıyor mu?

### ⚠️ Uyarı
2. **yfinance delisted ticker hataları yoğun** — 312+ hata kaydı.
   - $SUMO ve $SPLK gibi delisted (delistenmiş) semboller hâlâ tarama listesinde.
   - Aksiyon: `scanner.py` veya tarama listesi kaynaklarındaki stale ticker'lar temizlenmeli.

3. **API Socket Hang Up (4 tekrar)** — `localhost:8000/api/v1/scan` endpoint'ine proxy bağlantısı kesildi.
   - API servisi anlık duraksama yaşıyor olabilir; log zaman damgalarına bakılarak pattern netleştirilebilir.

4. **`data/shortlists/` tazeliği 22 saat** — henüz 24h sınırını geçmedi ama bugün güncellenmedi.
   - Günlük tarama işleminin zamanında çalışıp çalışmadığı izlenmeli.

5. **altdata ndarray boyut uyumsuzluğu** — ZM, ZS, ZTEK ve muhtemelen diğer tickerlar için `(24, 1)` shape beklenen `1D` array'e düşürülüyor; sentetik fallback aktif.
   - Gerçek altdata kaynağında şekil normalizasyonu eksik olabilir.

---

*Rapor otomatik olarak üretilmiştir — 2026-04-08*
