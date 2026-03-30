# 🏥 FinPilot Günlük Sağlık Raporu — 2026-03-29

> Otomatik olarak üretilmiştir. Rapor tarihi: 29 Mart 2026, 22:05 CEST

---

## Özet

| Metrik | Değer | Durum |
|--------|-------|-------|
| Log Hata Satırı | 3.177 | ⚠️ |
| Log CRITICAL | 0 | ✅ |
| Log Exception/Traceback | 0 | ✅ |
| Veri Tazeliği (shortlists) | ~1.469 saat (~61 gün) | 🚨 |
| Veri Tazeliği (suggestions) | ~1.469 saat (~61 gün) | 🚨 |
| Test Dosyası | 23 | ✅ |
| Test Fonksiyonu | 466 | ✅ |
| Model Artifact (ZIP) | 40 ZIP dosyası | ✅ |
| Registry Kayıtlı Model | 19 | ✅ |
| `.env` Varlığı | Mevcut | ✅ |
| `user_settings.json` | Geçerli JSON | ✅ |
| `.env` Eksik Key | 3 key eksik | ⚠️ |
| Toplam API Endpoint | 22 | ✅ |
| Secret Key Güvenliği | Placeholder değil | ✅ |
| Requirements Pinning | Tüm paketler kısıtlı | ✅ |

---

## Detaylar

### 1. 🔍 Log Anomali Taraması

**Taranan log dosyaları:** `logs/*.log` (toplam 19 `.log` dosyası)

En son değiştirilen dosyalar:
- `retrain_swing_optuna2.log` — 07 Mar 2026
- `retrain_conservative_optuna.log` — 06 Mar 2026
- `retrain_swing_optuna.log` — 06 Mar 2026
- `retrain_momentum_optuna.log` — 06 Mar 2026
- `optuna_conservative.log` — 05 Mar 2026

**Hata Özeti:**

| Kategori | Sayı |
|----------|------|
| Toplam hata satırı (ERROR/CRITICAL/Exception/Failed) | 3.177 |
| CRITICAL | 0 |
| Exception / Traceback | 0 |
| Hata içeren dosya sayısı | 4 |

**Top-5 Tekrarlayan Hata Paterni:**

1. **`Failed to fetch real altdata for <TICKER>: Data must be 1-dimensional, got ndarray of shape (24, 1) instead`** — 2.679 tekrar
   → Altdata fetch'te ndarray shape uyumsuzluğu; sistem sentetik veriye fallback yapıyor. `full_scan_20260302_2018.log` içinde yoğunlaşıyor. `altdata.py:68`'de `FutureWarning` da eşlik ediyor (`'H'` frekans kısayolu deprecated).

2. **`Failed download: 1 ticker failed`** — 15 tekrar
   → `yfinance` indirme başarısızlıkları. `full_scan_20260302_2018.log` kaynaklı.

3. **`yfinance ERROR: possibly delisted; no price data found`** — ~8 tekrar
   → `$AMODW`, `$ESGLW`, `$RNWWW`, `$WLDSW` tickerları muhtemelen delist edilmiş.

4. **`TypeError: 'NoneType' object is not subscriptable`** — 2 tekrar
   → `AMD` (`retrain_volatile_v2.log`) ve `TLT` (`retrain_swing_optuna2.log`) için yfinance download sırasında NoneType hatası.

5. **`FutureWarning: 'H' is deprecated`** — 45 tekrar
   → `altdata.py:68`'de `pd.date_range` veya resample'da kullanılan `'H'` frekans string'i, gelecekteki pandas sürümlerinde kaldırılacak.

---

### 2. 📅 Veri Tazelik Kontrolü

| Klasör | En Yeni Dosya | Yaş | Durum |
|--------|---------------|-----|-------|
| `data/shortlists/` | `shortlist_fromcsv_suggestions_..._20250916_1811.csv` | ~1.469 saat (~61 gün) | 🚨 |
| `data/suggestions/` | `suggestions_fromcsv_suggestions_..._20250916_1811.csv` | ~1.469 saat (~61 gün) | 🚨 |

> **Not:** Tüm shortlist ve suggestion dosyalarının zaman damgası `Jan 27 15:50` (2026). Bu, dosyaların son 24 saat içinde güncellenmediğini gösteriyor. Shortlist/suggestion pipeline'ı çalışmıyor olabilir veya bu veriler harici bir süreçle güncellenmektedir.

---

### 3. 🧪 Test Envanteri

| Metrik | Değer |
|--------|-------|
| Test dosyası sayısı | 23 |
| Toplam `def test_` fonksiyonu | 466 |
| En son eklenen test dosyası | `test_db_backend.py` (26 Mar 2026, 20:59) |

**Test fonksiyonu dağılımı (Top-10):**

| Dosya | Test Sayısı |
|-------|-------------|
| `test_social.py` | 40 |
| `test_core.py` | 38 |
| `test_validation.py` | 37 |
| `test_llm.py` | 32 |
| `test_prometheus.py` | 31 |
| `test_auth.py` | 31 |
| `test_websocket_feeds.py` | 30 |
| `test_signals.py` | 23 |
| `test_plugins.py` | 23 |
| `test_sentry.py` | 22 |

---

### 4. 🤖 Model Artifact Kontrolü

**ZIP Dosyaları:** 40 adet (tüm model dizinlerinde mevcut)

| Kategori | Dosya Sayısı |
|----------|--------------|
| Üretim model dizinleri (`ppo_*`, `rppo_*`) | 19 |
| Checkpoint ZIP'ler | 20 |
| Best model | 1 |
| **Toplam** | **40** |

**Registry kayıtlı model sayısı:** 19 ✅

**Son güncellenen modeller:**

| Model | Boyut | Tarih |
|-------|-------|-------|
| `ppo_conservative_20260306_063457` | 700K | 06 Mar 2026 |
| `ppo_momentum_20260306_001305` | 700K | 06 Mar 2026 |
| `ppo_trend_20260305_233633` | 700K | 06 Mar 2026 |
| `rppo_swing_20260304_220401` | 7.1M | 04 Mar 2026 |
| `ppo_trend_20260304_233619` | 700K | 05 Mar 2026 |

> Tüm model dizinlerinde `model.zip` mevcut. Eksik artifact yok ✅

---

### 5. ⚙️ Konfigürasyon Kontrolü

| Kontrol | Sonuç | Durum |
|---------|-------|-------|
| `.env` dosyası var mı? | Evet | ✅ |
| `user_settings.json` geçerli JSON | Evet | ✅ |
| `.env.example` ile key karşılaştırması | 3 eksik key | ⚠️ |

**`.env`'de eksik olan key'ler (`.env.example`'da mevcut):**

| Eksik Key | Açıklama |
|-----------|----------|
| `MLFLOW_TRACKING_URI` | MLflow experiment tracking adresi |
| `REDIS_URL` | Redis cache/queue bağlantısı |
| `ALPACA_SECRET_KEY` | Alpaca broker secret key (`ALPACA_API_KEY` var fakat secret key eksik) |

> `ALPACA_SECRET_KEY` eksikliği özellikle kritik olabilir — broker bağlantısı çalışmıyor olabilir.

---

### 6. 🛣️ API Router Envanteri

**Router dosyası sayısı:** 10 (+ `__init__.py`)

| Router | Endpoint Sayısı |
|--------|-----------------|
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
| **Toplam** | **22** |

---

### 7. 🔐 Güvenlik Kontrol Listesi

| Kontrol | Sonuç | Durum |
|---------|-------|-------|
| `FINPILOT_SECRET_KEY` placeholder değil | 64 karakterli hex değer kullanılıyor | ✅ |
| `requirements.txt` version kısıtlamaları | Tüm 29 paket kısıtlı (== veya >=x,<y) | ✅ |

**requirements.txt detayı:**
- Exact pin (`==`): 16 paket — `pandas`, `numpy`, `yfinance`, `requests`, `pydantic`, `pyjwt`, `bcrypt`, `cryptography`, `groq`, `anthropic`, `alpaca-py`, `pytest` vb.
- Range pin (`>=x.y,<z.0`): 13 paket — `streamlit`, `plotly`, `sentry-sdk`, `prometheus-client`, `gspread` vb.
- Hiç kısıtlanmamış paket: **0** ✅

---

## 🚨 Eylem Gerektirenler

### Kritik (hemen müdahale)

1. **🚨 Veri Pipeline Durmuş** — `data/shortlists/` ve `data/suggestions/` klasörlerindeki veriler **~61 gündür güncellenmemiş** (son güncelleme: 27 Ocak 2026). Bu veri ile yapılan tarama ve öneri sonuçları güncel olmayacaktır. Shortlist/suggestion üretim pipeline'ı kontrol edilmeli ve yeniden başlatılmalıdır.

### Uyarı (yakın vadede müdahale)

2. **⚠️ `ALPACA_SECRET_KEY` Eksik** — `.env` dosyasında `ALPACA_SECRET_KEY` tanımlı değil. Broker bağlantısı (canlı/paper trading) çalışmıyor olabilir.

3. **⚠️ `REDIS_URL` ve `MLFLOW_TRACKING_URI` Eksik** — Cache/kuyruk servisleri ve MLflow takip devre dışı olabilir.

4. **⚠️ `altdata.py:68` FutureWarning** — `pandas` frekans kısayolu `'H'` deprecated; `'h'` olarak güncellenmeli.

5. **⚠️ `altdata.py` ndarray Shape Hatası** — 2.679 kez tekrarlayan `(24, 1)` shape uyumsuzluğu düzeltilmeli; altdata gerçek veri yerine sentetik fallback kullanıyor.

6. **⚠️ Delist Tickers** — `$AMODW`, `$ESGLW`, `$RNWWW`, `$WLDSW` tickerları yfinance'ten veri çekemiyor; tarama listelerinden çıkarılması önerilir.

### Bilgi (takip edilmeli)

7. **ℹ️ Son Model Güncellemesi 23+ Gün Önce** — En yeni model 06 Mart 2026 tarihli; retrain planlanıyorsa zaman gelmiş olabilir.

---

*Rapor `/sessions/compassionate-serene-fermi/mnt/Borsa/data/reports_cache/health_report_2026-03-29.md` olarak kaydedildi.*
