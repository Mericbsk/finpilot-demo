# 🏥 FinPilot Günlük Sağlık Raporu — 2026-04-02

> Otomatik olarak üretilmiştir. Rapor tarihi: 2 Nisan 2026 | Scheduled Task: `finpilot-daily-health`

---

## Özet

| Metrik | Değer | Durum |
|--------|-------|-------|
| Log Hata Satırı (ERROR/Failed) | 438 ERROR + 2.749 Failed | ⚠️ |
| Log CRITICAL | 0 | ✅ |
| Log Exception/Traceback | 0 | ✅ |
| Veri Tazeliği (shortlists) | ~1.553 saat (~64,7 gün) | 🚨 |
| Veri Tazeliği (suggestions) | ~1.553 saat (~64,7 gün) | 🚨 |
| Test Dosyası | 24 | ✅ |
| Test Fonksiyonu | 466 | ✅ |
| Model Artifact (ZIP) | 40 ZIP dosyası | ✅ |
| Registry Kayıtlı Model | 19 | ✅ |
| `.env` Varlığı | Mevcut | ✅ |
| `user_settings.json` | Geçerli JSON | ✅ |
| `.env` Eksik Key | Eksik yok | ✅ |
| Toplam API Endpoint | 22 | ✅ |
| Secret Key Güvenliği | Placeholder değil | ✅ |
| Requirements Pinning | 13 paket range-pinned | ⚠️ |

---

## Detaylar

### 1. 🔍 Log Anomali Taraması

**Taranan log dosyaları:** `logs/*.log` — toplam **16 `.log` dosyası**

En son değiştirilen dosyalar:
- `retrain_swing_optuna2.log` — 07 Mar 2026
- `retrain_conservative_optuna.log` — 06 Mar 2026
- `retrain_swing_optuna.log` — 06 Mar 2026
- `retrain_momentum_optuna.log` — 06 Mar 2026
- `optuna_conservative.log` — 05 Mar 2026

**Hata Özeti:**

| Kategori | Sayı |
|----------|------|
| ERROR (toplam) | 438 |
| CRITICAL | 0 |
| Exception / Traceback | 0 |
| Failed | 2.749 |
| Hata içeren dosya sayısı | 4 |

**Top-5 Tekrarlayan Hata Paterni:**

1. **`yfinance ERROR: possibly delisted (period=400d)`** — 78 tekrar
   → Delist edilmiş tickerlar için 400 günlük veri çekilememesi. Sembollerin taranmasında filtreleme önerilir.

2. **`yfinance ERROR: possibly delisted (period=60d)`** — 78 tekrar
   → Aynı tickerların 60 günlük periyotta da başarısız olması.

3. **`yfinance ERROR: possibly delisted (period=10d)`** — 78 tekrar
   → Tüm periyotlarda tutarlı olarak başarısız olan semboller mevcut (muhtemelen $SUMO, $SPLK gibi delist edilmiş tickerlar).

4. **`yfinance ERROR: possibly delisted (period=100d)`** — 78 tekrar
   → Delist kontrol listesinin güncellenmesi önerilir.

5. **`Failed download: 1 ticker failed`** — 15 tekrar
   → `yfinance` toplu indirme başarısızlıkları; ağ veya kaynak kısıtlamalarından kaynaklanabilir.

**Ek bulgu:** `retrain_swing_optuna2.log` içinde `TLT` tickerı için `TypeError("'NoneType' object is not subscriptable")` hatası tespit edildi. Bu, None değer döndüren bir yfinance çağrısının sonraki adımda işlenmeden kullanılmasından kaynaklanıyor olabilir.

---

### 2. 📅 Veri Tazelik Kontrolü

| Klasör | En Son Dosya | Yaş | Durum |
|--------|-------------|-----|-------|
| `data/shortlists/` | `shortlist_fromcsv_..._20250916_1811.csv` | ~1.553 saat (~64,7 gün) | 🚨 |
| `data/suggestions/` | `suggestions_fromcsv_..._20250916_1811.csv` | ~1.553 saat (~64,7 gün) | 🚨 |

> 🚨 **KRİTİK:** Her iki veri klasöründeki son dosyalar yaklaşık **64 gün** önce güncellenmiş. Bu süre boyunca yeni tarama çalıştırılmamış görünüyor. Veri pipeline'ının çalışıp çalışmadığı kontrol edilmeli.

---

### 3. 🧪 Test Envanteri

| Metrik | Değer |
|--------|-------|
| Toplam test dosyası | 24 |
| Toplam `def test_` fonksiyonu | 466 |
| En son eklenen test dosyası | `test_db_backend.py` (30 Mar 2026) |

**Tüm test dosyaları:**

`conftest.py`, `test_alignment_helpers.py`, `test_auth.py`, `test_backtest.py`, `test_broker.py`, `test_core.py`, `test_data_fetcher.py`, `test_db_backend.py`, `test_db_repos.py`, `test_drl_integration.py`, `test_evaluate.py`, `test_explainability.py`, `test_feature_generators.py`, `test_indicators.py`, `test_llm.py`, `test_plugins.py`, `test_prometheus.py`, `test_sentry.py`, `test_signals.py`, `test_social.py`, `test_validation.py`, `test_views_integration.py`, `test_views_smoke.py`, `test_websocket_feeds.py`

> ✅ Önceki rapora göre 1 yeni test dosyası eklendi (`test_db_backend.py`) — test kapsamı genişlemeye devam ediyor.

---

### 4. 🤖 Model Artifact Kontrolü

| Metrik | Değer |
|--------|-------|
| Toplam ZIP dosyası | 40 |
| `models/best/` ZIP | 1 (`best_model.zip`, 168K, 26 Şub 2026) |
| `models/checkpoints/` ZIP | 21 |
| Model klasörü ZIP | 18 (her klasörde `model.zip` + `pipeline.json`) |
| Registry kayıtlı model | 19 |

**En son 5 model (tarih sırası ile):**

| Model | Boyut | Tarih |
|-------|-------|-------|
| `ppo_conservative_20260306_063457` | 692K | 06 Mar 2026 |
| `ppo_momentum_20260306_001305` | 692K | 06 Mar 2026 |
| `ppo_trend_20260305_233633` | 692K | 06 Mar 2026 |
| `ppo_trend_20260304_233619` | 692K | 05 Mar 2026 |
| `ppo_conservative_20260304_232440` | 692K | 05 Mar 2026 |

> ✅ Tüm model dizinlerinde hem `model.zip` hem de `pipeline.json` dosyaları mevcut. Eksik artifact tespit edilmedi.

---

### 5. ⚙️ Konfigürasyon Kontrolü

| Kontrol | Sonuç | Durum |
|---------|-------|-------|
| `.env` dosyası varlığı | Mevcut | ✅ |
| `.env.example` varlığı | Mevcut | ✅ |
| `user_settings.json` geçerlilik | Geçerli JSON | ✅ |
| `.env.example` key coverage | 11/11 key mevcut | ✅ |
| Eksik key | Yok | ✅ |

**Tüm beklenen keyler `.env`'de mevcut:**
`ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `FINPILOT_SECRET_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `MLFLOW_TRACKING_URI`, `NEWS_API_KEY`, `POLYGON_API_KEY`, `REDIS_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

> ✅ Önceki raporda 3 eksik key tespit edilmişti; bu eksiklikler giderilmiş, tüm keyler artık mevcut.

---

### 6. 🌐 API Router Envanteri

| Router | Endpoint Sayısı |
|--------|----------------|
| `trade.py` | 5 |
| `history.py` | 3 |
| `user.py` | 3 |
| `inference.py` | 2 |
| `llm.py` | 2 |
| `models.py` | 2 |
| `optuna.py` | 2 |
| `backtest.py` | 1 |
| `ensemble.py` | 1 |
| `scan.py` | 1 |
| **TOPLAM** | **22** |

---

### 7. 🔒 Güvenlik Kontrol Listesi

| Kontrol | Sonuç | Durum |
|---------|-------|-------|
| `FINPILOT_SECRET_KEY` placeholder mı? | Hayır — gerçek 64-char hex değer | ✅ |
| `requirements.txt` pinned versiyonlar | 16/29 paket `==` ile sabitlenmiş, 13 paket range (`>=x,<y`) | ⚠️ |

**Range-pinned (tam sabitlenmemiş) paketler:**

`streamlit>=1.53.0,<2.0`, `plotly>=6.5.0,<7.0`, `lxml>=6.0.0,<7.0`, `google-genai>=1.0.0,<2.0`, `duckduckgo-search>=8.1.0,<9.0`, `structlog>=25.0.0,<26.0`, `sentry-sdk>=2.31.0,<3.0`, `prometheus-client>=0.21.0,<1.0`, `openpyxl>=3.1.0,<4.0`, `reportlab>=4.2.0,<5.0`, `gspread>=6.1.0,<7.0`, `apscheduler>=3.10.0,<4.0`, `pytest-cov>=7.0.0`

> ⚠️ Range-pinning, major versiyon kırılmalarına karşı koruma sağlar; ancak yeniden üretilebilir build'ler için `==` ile tam sabitleme tercih edilir.

---

## 🚨 Eylem Gerektirenler

### Kritik (Hemen Müdahale)

1. **🚨 Veri Pipeline Durumu** — `data/shortlists/` ve `data/suggestions/` klasörlerindeki veriler yaklaşık **64 gün** güncel değil (son dosya 16 Eylül 2025). Tarama pipeline'ının (scanner.py / auto_scan_trade) neden çalışmadığı araştırılmalı.

### Orta Öncelikli Uyarılar

2. **⚠️ Delist Ticker Listesi** — `$SUMO`, `$SPLK` ve diğer muhtemelen delist edilmiş semboller tarama süreçlerinde hata üretmeye devam ediyor. Bu semboller tarama evreninden çıkarılmalı.

3. **⚠️ `TLT` NoneType Hatası** — `retrain_swing_optuna2.log` içindeki `TypeError("'NoneType' object is not subscriptable")` hatası bir veri doğrulama açığına işaret ediyor; yfinance yanıtı None olsa bile kod devam ediyor.

4. **⚠️ Requirements Pinning** — 13 paketin range-pinned olması tekrarlanabilir ortamlar açısından risk taşıyor. `pip freeze` çıktısıyla tam sabitlenmiş bir `requirements.lock` dosyası oluşturulması önerilir.

### Olumlu Gelişmeler ✅

- **Config eksik key sorunu çözüldü:** Önceki raporda 3 eksik key vardı, şimdi tüm 11 key mevcut.
- **Yeni test dosyası eklendi:** `test_db_backend.py` (30 Mar 2026) — test kapsamı artmaya devam ediyor.
- **Model eğitimi devam ediyor:** Son model 6 Mart 2026 tarihli, pipeline aktif.
- **Secret key güvenli:** `FINPILOT_SECRET_KEY` placeholder değil, gerçek değerle dolu.

---

*Rapor sonu — Sonraki otomatik kontrol: 2026-04-03*
