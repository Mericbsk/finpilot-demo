# 🏥 FinPilot Günlük Sağlık Raporu — 2026-04-18

> **Rapor Notu:** Görev dosyasındaki hedef yol (`/sessions/kind-jolly-galileo/mnt/Borsa/`) bu oturumda erişilebilir değil. Rapor, gerçek proje konumu olan `/sessions/blissful-laughing-johnson/mnt/Borsa/data/reports_cache/` altına kaydedilmiştir.

---

## Özet

| Metrik | Değer | Durum |
|--------|-------|-------|
| Log Hata Sayısı (aktif loglar) | 5 hata, 3 failed (api+web) | ⚠️ |
| Veri Tazeliği — Shortlists | 42 saat | ⚠️ |
| Veri Tazeliği — Suggestions | ~1941 saat (~80 gün) | 🚨 |
| Test Dosyası Sayısı | 24 | ✅ |
| Test Fonksiyon Sayısı | 472 | ✅ |
| Model Artifact (ZIP) | 19 model dizini, tümünde ZIP mevcut | ✅ |
| .env Konfigürasyonu | Tüm key'ler tanımlı | ✅ |
| user_settings.json | Geçerli JSON | ✅ |
| Güvenlik — SECRET_KEY | Placeholder değil | ✅ |
| Güvenlik — Pinned deps | 32/33 pinned | ⚠️ |

---

## Detaylar

### 1. 🔍 Log Anomali Taraması

**Taranan log dosyaları:** `api.log`, `web.log`, `auto_scan_trade.log`, `full_scan_20260302_2018.log`

#### api.log (son çalışma: 16 Nisan 2026)
| Pattern | Sayı |
|---------|------|
| ERROR | 1 |
| Failed | 1 |
| CRITICAL | 0 |
| Exception | 0 |

**Kritik hata:** Redis bağlantısı başarısız — `Error 111 connecting to localhost:6379. Connection refused.` Sistem bellek-only moda geçti. API çalışmaya devam ediyor.

#### web.log (son çalışma: 16 Nisan 2026)
| Pattern | Sayı |
|---------|------|
| ERROR | 4 |
| Failed | 2 |

**Tekrarlayan hatalar:**
- `Failed to proxy http://localhost:8000/api/v1/scan Error: socket hang up` (2 kez)
- Node.js `util._extend` deprecation uyarısı

#### auto_scan_trade.log (2 Mart 2026)
| Pattern | Sayı |
|---------|------|
| ERROR | 234 |
| Failed | 12 |

**Top-5 Hata Deseni:**
1. `yfinance | $SUMO: possibly delisted; no price data found` (period=60d, 400d, 10d — 3 varyant, her biri 3 kez)
2. `yfinance | ERROR` genel (7 kez)
3. `1 Failed download:` (7 kez)
4. Diğer muhtemelen-delisted ticker hataları
5. Genel yfinance bağlantı/veri hataları

#### Genel Değerlendirme
- **Aktif loglar** (api.log, web.log) düşük hata sayısıyla sağlıklı görünüyor.
- Redis sunucusu çalışmıyor — önbellek performansı etkilenmiş olabilir.
- Scan loglarındaki hatalar büyük ölçüde hisse senetlerinin delistesi nedeniyle; veri kaynağı (yfinance) sorunları beklenebilir nitelikte.

---

### 2. 📅 Veri Tazelik Kontrolü

#### data/shortlists/
- **En yeni dosya:** `shortlist_20260416_1759.csv` (16 Nisan 2026, 19:59)
- **Yaş:** ~42 saat
- **Durum:** ⚠️ 24 saatten eski — tarama yenilenmesi gerekiyor

#### data/suggestions/
- **En yeni dosya:** `suggestions_fromcsv_...20250916_1811.csv` (27 Ocak 2026'da son değiştirilmiş)
- **Yaş:** ~1941 saat (~80 gün)
- **Durum:** 🚨 Kritik — Suggestions klasörü çok uzun süredir güncellenmemiş. Bu klasörün artık aktif kullanılmadığı ya da otomasyonun koptuğu anlamına gelebilir.

---

### 3. 🧪 Test Envanteri

| Metrik | Değer |
|--------|-------|
| Test dosyası sayısı | 24 |
| Toplam `def test_` sayısı | 472 |
| Son eklenen test dosyası | `test_api_runtime.py` (16 Nisan 2026, 19:08) |

**Test dosyaları (alfabetik):**
`test_alignment_helpers.py`, `test_api_runtime.py`, `test_auth.py`, `test_backtest.py`, `test_broker.py`, `test_core.py`, `test_data_fetcher.py`, `test_db_backend.py`, `test_db_repos.py`, `test_drl_integration.py`, `test_evaluate.py`, `test_explainability.py`, `test_feature_generators.py`, `test_indicators.py`, `test_llm.py`, `test_plugins.py`, `test_prometheus.py`, `test_sentry.py`, `test_signals.py`, `test_social.py`, `test_validation.py`, `test_views_integration.py`, `test_views_smoke.py`, `test_websocket_feeds.py`

Test kapsamı geniş; DRL entegrasyonu, auth, broker, veri çekimi, LLM, Prometheus, Sentry gibi kritik modüller kapsanmış.

---

### 4. 🤖 Model Artifact Kontrolü

**Toplam model dizini:** 19
**ZIP dosyası durumu:** Tüm model dizinlerinde `model.zip` mevcut ✅
**best_model.zip:** Mevcut (`models/best/best_model.zip`, 169 KB, 26 Şubat 2026) ✅

| Model | Boyut | Son Güncelleme |
|-------|-------|----------------|
| ppo_aggressive_20260302_215335 | 272K | 2026-03-02 |
| ppo_breakout_20260302_191605 | 272K | 2026-03-02 |
| ppo_conservative_20260302_214206 | 272K | 2026-03-02 |
| ppo_conservative_20260304_232440 | 700K | 2026-03-05 |
| ppo_conservative_20260306_063457 | 700K | 2026-03-06 |
| ppo_meanrev_20260302_190334 | 272K | 2026-03-02 |
| ppo_momentum_20260302_184945 | 272K | 2026-03-02 |
| ppo_momentum_20260303_191357 | 272K | 2026-03-03 |
| ppo_momentum_20260306_001305 | 700K | 2026-03-06 |
| ppo_range_20260226_170853 | 176K | 2026-02-26 |
| ppo_scalper_20260302_200828 | 408K | 2026-03-02 |
| ppo_trend_20260225_181020 | 176K | 2026-02-26 |
| ppo_trend_20260304_193141 | 272K | 2026-03-04 |
| ppo_trend_20260304_221324 | 700K | 2026-03-04 |
| ppo_trend_20260304_233619 | 700K | 2026-03-05 |
| ppo_trend_20260305_233633 | 700K | 2026-03-06 |
| ppo_volatile_20260225_192559 | 176K | 2026-02-26 |
| rppo_swing_20260302_212140 | 7.1M | 2026-03-02 |
| rppo_swing_20260304_220401 | 7.1M | 2026-03-04 |

Ayrıca `models/checkpoints/` altında 20 checkpoint ZIP dosyası (ppo_balanced ve ppo_production serileri) mevcut.

**Not:** Tüm modeller Şubat-Mart 2026'dan itibaren güncellenmemiş. Son 6 haftada yeni model eğitimi yapılmamış.

---

### 5. ⚙️ Konfigürasyon Kontrolü

| Kontrol | Sonuç |
|---------|-------|
| `.env` dosyası mevcut? | ✅ Evet |
| `user_settings.json` geçerli JSON? | ✅ Evet |
| `.env.example` key'leri `.env`'de mevcut? | ✅ Tüm key'ler karşılanmış |

**.env.example'daki key'ler ve karşılık durumu:**

| Key | .env'de Mevcut |
|-----|---------------|
| ALPACA_API_KEY | ✅ |
| ALPACA_SECRET_KEY | ✅ |
| FINPILOT_SECRET_KEY | ✅ |
| GOOGLE_API_KEY | ✅ |
| GROQ_API_KEY | ✅ |
| MLFLOW_TRACKING_URI | ✅ |
| NEWS_API_KEY | ✅ |
| POLYGON_API_KEY | ✅ |
| REDIS_URL | ✅ |
| TELEGRAM_BOT_TOKEN | ✅ |
| TELEGRAM_CHAT_ID | ✅ |

Ek olarak `.env`'de `CACHE__REDIS_ENABLED` key'i de tanımlı (örnek dosyada yok ama sorun değil).

---

### 6. 🛣️ API Router Envanteri

**Toplam router dosyası:** 11
**Toplam endpoint sayısı:** 30

| Router | Endpoint Sayısı |
|--------|----------------|
| auth.py | 4 |
| backtest.py | 1 |
| ensemble.py | 1 |
| history.py | 4 |
| inference.py | 2 |
| llm.py | 2 |
| models.py | 4 |
| optuna.py | 4 |
| scan.py | 2 |
| trade.py | 5 |
| user.py | 1 |
| **TOPLAM** | **30** |

---

### 7. 🔒 Güvenlik Kontrol Listesi

| Kontrol | Sonuç | Detay |
|---------|-------|-------|
| `FINPILOT_SECRET_KEY` placeholder mı? | ✅ Hayır | Gerçek değer atanmış |
| `requirements.txt` pinned versiyonlar | ⚠️ 32/33 | `mkdocs-material` versiyonsuz |

**Pinned olmayan paket:**
```
mkdocs-material
```
Bu paket bir geliştirici aracıdır (dokümantasyon). Production güvenliği için kritik değil, ancak repro edilebilirlik için versiyon eklenmesi önerilir.

---

## ⚡ Eylem Gerektirenler

### 🚨 Kritik
1. **`data/suggestions/` güncellenmemiş (80 gün)** — Suggestions pipeline'ının çalışıp çalışmadığı doğrulanmalı. Son üretim tarihi: 27 Ocak 2026. Otomatik öneri üretimi durmuş olabilir.

### ⚠️ Uyarı
2. **Redis sunucusu çalışmıyor** — `localhost:6379` bağlantı hatası. Sistem bellek-only cache modunda. Performans ve ölçeklenebilirlik etkilenebilir. Redis başlatılması veya `CACHE__REDIS_ENABLED=false` durumunun kasıtlı olduğunun teyidi gerekli.
3. **`data/shortlists/` 42 saat eski** — Son tarama 16 Nisan 2026 tarihli. Günlük tarama otomasyonu çalışıyorsa bugün tetiklenmemiş olabilir.
4. **web.log'da scan proxy hatası** — `socket hang up` hatası, `/api/v1/scan` endpoint'inin zaman aşımına uğradığını gösteriyor. Uzun süren tarama istekleri için timeout değerleri gözden geçirilmeli.
5. **`mkdocs-material` versiyonu pinlenmemiş** — `requirements.txt`'e versiyon eklenmeli.

### ℹ️ Bilgi
6. **Model eğitimi 6+ haftadır yapılmamış** — Son model: 6 Mart 2026. Piyasa koşulları değiştiyse yeniden eğitim değerlendirilebilir.

---

*Rapor otomatik olarak 2026-04-18 tarihinde üretilmiştir.*
