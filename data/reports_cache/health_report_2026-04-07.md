# 🏥 FinPilot Günlük Sağlık Raporu — 2026-04-07

## Özet

| Metrik | Değer | Durum |
|--------|-------|-------|
| Log Hata Sayısı (toplam) | 3.230 | ⚠️ |
| Log Hata Sayısı (api.log) | 6 | ✅ |
| Shortlist Tazeliği | ~95 saat | ⚠️ |
| Suggestions Tazeliği | ~1.676 saat (~70 gün) | 🚨 |
| Test Dosyası | 24 dosya, 466 fonksiyon | ✅ |
| Model Artifact | 40 ZIP, 21 klasör | ✅ |
| Config (.env) | Tüm anahtarlar mevcut | ✅ |
| user_settings.json | Geçerli JSON | ✅ |
| API Endpoint Sayısı | 28 endpoint | ✅ |
| Güvenlik (SECRET_KEY) | Özelleştirilmiş | ✅ |
| requirements.txt | 29/29 pinned | ✅ |

---

## Detaylar

### 1. 📋 Log Anomali Taraması

**Taranan log dosyaları:** `api.log`, `web.log`, `auto_scan_trade.log`, `full_scan_20260302_2018.log`, `retrain_swing_optuna2.log`, `retrain_volatile_v2.log` + diğerleri

**Toplam hata sayısı:** 3.230

En yüksek hata yükü `full_scan_20260302_2018.log` (2.930 hata) ve `auto_scan_trade.log` (241 hata) dosyalarındadır — bunlar geçmiş tarama operasyonlarına ait ve anlık sistemi yansıtmıyor.

Aktif log dosyaları (api.log, web.log) açısından durum daha iyi:
- `api.log`: 6 hata
- `web.log`: 47 hata (çoğu bağlantı reddi)

**Top-5 En Sık Tekrarlanan Hata Paterni:**

| Sıra | Tekrar | Hata Mesajı |
|------|--------|-------------|
| 1 | 78x | `yfinance: $TICKER: possibly delisted; no price data found (period=100d)` |
| 2 | 78x | `yfinance: $TICKER: possibly delisted; no price data found (period=60d)` |
| 3 | 78x | `yfinance: $TICKER: possibly delisted; no price data found (period=10d)` |
| 4 | 78x | `yfinance: $TICKER: possibly delisted; no price data found (period=400d)` |
| 5 | 42x | `yfinance: $TICKER: possibly delisted; no price data found (period=10d)` |

Ek kritik hatalar (aktif log dosyalarından):
- `Failed to load model from path: No module named 'stable_baselines3'` — 2x (api.log)
- `Failed to load model from path: No module named 'sb3_contrib'` — 1x (api.log)
- `Exception in ASGI application` — 2x (api.log)
- `Failed to proxy http://localhost:8000/api/v1/scan Error: socket hang up` — 19x (web.log)
- `Failed to proxy http://localhost:8000/api/v1/health Error: connect ECONNREFUSED` — 6x (web.log)

**Değerlendirme:** ⚠️ Delisted ticker hataları önemli — tarama listelerinde aktif olmayan semboller mevcut. `stable_baselines3` modül hatası kritik: model inference çalışmıyor olabilir.

---

### 2. 💾 Veri Tazelik Kontrolü

**data/shortlists/**
- En son dosya: `shortlist_20260403_1239.csv`
- Son değiştirilme: 3 Nisan 2026, 14:39
- Bugünden farkı: **~95 saat** (4 günden fazla)
- Toplam dosya sayısı: 104 CSV
- Durum: ⚠️ 24 saatten eski

**data/suggestions/**
- En son dosya: `suggestions_fromcsv_...20250916_1811.csv`
- Son değiştirilme: 27 Ocak 2026
- Bugünden farkı: **~1.676 saat (~70 gün)**
- Toplam dosya sayısı: 63 CSV
- Durum: 🚨 Kritik şekilde eski — suggestions çıktısı üretilmiyor olabilir

---

### 3. 🧪 Test Envanteri

| Metrik | Değer |
|--------|-------|
| Test dosyası sayısı | 24 |
| Toplam test fonksiyonu (`def test_`) | 466 |
| En son eklenen test dosyası | `test_db_backend.py` (3 Nisan 2026) |

**Dosya başına test sayısı (en yüksekten):**

| Dosya | Test Sayısı |
|-------|-------------|
| test_social.py | 40 |
| test_validation.py | 37 |
| test_auth.py | 31 |
| test_prometheus.py | 31 |
| test_websocket_feeds.py | 30 |
| test_llm.py | 32 |
| test_core.py | 38 |
| test_sentry.py | 22 |
| test_signals.py | 23 |
| test_plugins.py | 23 |

**Değerlendirme:** ✅ Test envanteri güçlü, geniş kapsam alanı mevcut.

---

### 4. 🤖 Model Artifact Kontrolü

| Metrik | Değer |
|--------|-------|
| Toplam ZIP dosyası | 40 |
| Model klasörü sayısı | 21 |
| En iyi model (best/) | `best_model.zip` — 166K (26 Şubat 2026) |
| En güncel model | `ppo_conservative_20260306_063457` (6 Mart 2026) |
| Checkpoints | 20 ZIP dosyası (ppo_balanced + ppo_production serileri) |

**Model boyutları:**
- Küçük modeller (ppo_aggressive, ppo_breakout vb.): ~272K
- Orta modeller (ppo_conservative, ppo_trend vb.): ~700K
- Büyük modeller (rppo_swing): ~7.1M

**Değerlendirme:** ✅ ZIP artifact'ler mevcut. Ancak api.log'daki `stable_baselines3` modül hatası, modellerin production ortamında yüklenemediğine işaret ediyor — paket bağımlılık sorunu olabilir.

---

### 5. ⚙️ Konfigürasyon Kontrolü

| Kontrol | Durum |
|---------|-------|
| `.env` dosyası varlığı | ✅ Mevcut |
| `.env.example` dosyası varlığı | ✅ Mevcut |
| `user_settings.json` geçerliliği | ✅ Geçerli JSON |
| `.env.example` anahtarlarının `.env`'de varlığı | ✅ Tüm 11 anahtar mevcut |

**`.env`'deki mevcut anahtarlar:**
`ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `FINPILOT_SECRET_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `MLFLOW_TRACKING_URI`, `NEWS_API_KEY`, `POLYGON_API_KEY`, `REDIS_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

**`user_settings.json` anahtarları:**
`risk_score`, `portfolio_size`, `max_loss_pct`, `strategy`, `market`, `telegram_active`, `telegram_id`, `timeframe`, `indicators`

---

### 6. 🔌 API Router Envanteri

| Router | Endpoint Sayısı |
|--------|----------------|
| trade.py | 5 |
| history.py | 4 |
| models.py | 4 |
| optuna.py | 4 |
| backtest.py | 1 |
| ensemble.py | 1 |
| inference.py | 2 |
| llm.py | 2 |
| scan.py | 2 |
| user.py | 3 |
| **TOPLAM** | **28** |

---

### 7. 🔐 Güvenlik Kontrol Listesi

| Kontrol | Durum | Açıklama |
|---------|-------|----------|
| `FINPILOT_SECRET_KEY` placeholder'da mı? | ✅ Hayır | Özelleştirilmiş değer atanmış |
| `requirements.txt` pinned versiyonlar | ✅ 29/29 pinned | Tüm paketler `==` ile sabitlenmiş |

---

## 🚨 Eylem Gerektirenler

### Kritik (Hemen Müdahale)

1. **`stable_baselines3` ve `sb3_contrib` kurulu değil** — API sunucusu model yükleyemiyor. `pip install stable-baselines3 sb3-contrib` komutu ile ortama kurulmalı. `api.log`'da 3 ayrı model yükleme hatası görülmüş.

2. **Suggestions verisi ~70 gündür güncellenmemiş** — `data/suggestions/` içindeki en güncel CSV Ocak 2026'dan. Suggestion pipeline çalışmıyor veya çıktı başka bir yere yazılıyor olabilir.

### Uyarı (Yakın Zamanda Kontrol Et)

3. **Shortlist verisi ~95 saattir güncellenmemiş** — Son shortlist 3 Nisan tarihli. Sistem aktif ise günlük üretilmeli; hafta sonu tatili olabilir ancak bugünkü tarih Salı.

4. **Delisted ticker'lar tarama listesinde** — yfinance'ten 78'er adet (4 farklı period için) delisted uyarısı geliyor. `$SUMO`, `$SPLK` gibi semboller kaldırılmış hisseler; tarama listesinden temizlenmeli.

5. **API sunucusu bazen ulaşılamıyor** — `web.log`'da `ECONNREFUSED 127.0.0.1:8000` ve `socket hang up` hataları var. API servisi kararsız görünüyor.

---

*Rapor otomatik olarak oluşturulmuştur — 2026-04-07 (FinPilot Health Bot)*
