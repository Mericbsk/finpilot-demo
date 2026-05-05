# 🏥 FinPilot Günlük Sağlık Raporu — 2026-04-03

> **Son güncelleme:** 2026-04-03 (otomatik çalıştırma — ikinci run)
> Kaynak dizin: `Borsa/` | Kontrol edilen: Loglar, veri tazeliği, testler, modeller, konfigürasyon, API router'lar, güvenlik

---

## Özet

| Metrik | Değer | Durum |
|--------|-------|-------|
| Log Hata Sayısı | 3.174 hata (4 log dosyasında) | ⚠️ |
| Veri Tazeliği — Shortlists | 1.578 saat (≈65 gün) | 🚨 |
| Veri Tazeliği — Suggestions | 1.578 saat (≈65 gün) | 🚨 |
| Test Sayısı | 466 test / 24 dosya (incl. conftest) | ✅ |
| Model Artifact | 40+ ZIP dosyası mevcut | ✅ |
| Config (.env) | Tüm key'ler mevcut, geçerli | ✅ |
| API Endpoint | 27 endpoint / 10 router | ✅ |
| Güvenlik | Secret key değiştirilmiş, kısmen pinned | ⚠️ |

---

## Detaylar

### 1. 📋 Log Anomali Taraması

Tarama yapılan log dosyaları ve hata sayıları:

| Dosya | Hata Sayısı |
|-------|-------------|
| `full_scan_20260302_2018.log` | 2.930 |
| `auto_scan_trade.log` | 241 |
| `retrain_swing_optuna2.log` | 3 |
| `retrain_volatile_v2.log` | 3 |
| Diğer log dosyaları | 0 |
| **TOPLAM** | **3.177** |

**Top-5 Hata Kategorisi:**

1. **"No data found, symbol may be delisted"** — 320 tekrar
   Etkilenen semboller: `$SUMO`, `$SPLK`, `$NEWR`, `$SGEN`, `$BLUE` ve 30+ diğer ticker. Bunlar muhtemelen delisted veya birleşme/satın alma geçirmiş şirketler.

2. **yfinance ERROR: $SUMO** — 16 tekrar
   SUMO Logic delisted olmuş olabilir (Cisco tarafından satın alındı).

3. **yfinance ERROR: $SPLK** — 16 tekrar
   Splunk, Cisco tarafından satın alındı, delisted.

4. **TypeError: `'NoneType' object is not subscriptable`** — 15 tekrar
   `retrain_swing_optuna2.log`: TLT için veri çekme hatası
   `retrain_volatile_v2.log`: AMD için veri çekme hatası
   yfinance veri döndürmediğinde `None` kontrolü yapılmıyor.

5. **"Failed download" (yfinance)** — 15 tekrar
   Muhtemelen delisted semboller veya geçici bağlantı kopmaları.

> **Öneri:** Delisted sembolleri shortlist/tarama listesinden temizlemek, yfinance çağrılarında `None` kontrolü eklemek hata sayısını dramatik düşürecektir.

---

### 2. 📅 Veri Tazelik Kontrolü

**`data/shortlists/`**
- En yeni dosya: `shortlist_20251201_2111.csv` (filesystem stamp: 27 Ocak 2026)
- Gerçek içerik tarihi: 2025-12-01
- Bugüne göre yaş: **~65 gün** (1.578 saat)
- 🚨 **24 saat eşiğinin çok üzerinde — kritik veri eskimesi**

**`data/suggestions/`**
- En yeni dosya: `suggestions_20251201_2111.csv` (filesystem stamp: 27 Ocak 2026)
- Gerçek içerik tarihi: 2025-12-01
- Bugüne göre yaş: **~65 gün** (1.578 saat)
- 🚨 **24 saat eşiğinin çok üzerinde — kritik veri eskimesi**

> **Öneri:** Scanner'ın otomatik çalışmadığı veya çıktıları kaydedilmediği anlaşılıyor. `auto_scan_trade.log` incelenmesi ve scheduler kontrolü önerilir.

---

### 3. 🧪 Test Envanteri

- **Toplam test dosyası:** 23 adet
- **Toplam test fonksiyonu (`def test_`):** 466 adet
- **Son eklenen test dosyası:** `test_db_backend.py` (2 Nisan 2026, 10:23)

**Test dosyaları (son değiştirilme sırasına göre):**

| Dosya | Son Değiştirilme |
|-------|-----------------|
| `test_db_backend.py` | 2 Nisan 2026 |
| `test_drl_integration.py` | 26 Mart 2026 |
| `test_auth.py` | 26 Mart 2026 |
| `test_db_repos.py` | 26 Mart 2026 |
| `test_sentry.py` | 10 Mart 2026 |
| `test_prometheus.py` | 10 Mart 2026 |
| `test_llm.py` | 10 Mart 2026 |
| `test_broker.py` | 10 Mart 2026 |
| `test_data_fetcher.py` | 10 Mart 2026 |
| `test_evaluate.py` | 10 Mart 2026 |
| `test_views_smoke.py` | 10 Mart 2026 |
| `test_views_integration.py` | 10 Mart 2026 |
| Diğer 11 dosya | 19-24 Şubat 2026 |

---

### 4. 🤖 Model Artifact Kontrolü

ZIP dosyaları mevcut — model kataloğu sağlıklı:

| Model | Boyut | Son Güncelleme |
|-------|-------|---------------|
| `best/best_model.zip` | 166 KB | 26 Şubat 2026 |
| `ppo_conservative_20260306_063457/model.zip` | 705 KB | 6 Mart 2026 |
| `ppo_momentum_20260306_001305/model.zip` | 705 KB | 6 Mart 2026 |
| `ppo_trend_20260305_233633/model.zip` | 705 KB | 6 Mart 2026 |
| `rppo_swing_20260304_220401/model.zip` | 7,1 MB | 4 Mart 2026 |
| `rppo_swing_20260302_212140/model.zip` | 7,1 MB | 2 Mart 2026 |
| `ppo_trend_20260304_*/model.zip` (3 varyant) | 270–705 KB | 4 Mart 2026 |
| `checkpoints/` (11 ZIP) | toplam 3,3 MB | Şubat 2026 |
| Diğer PPO modelleri | ~270 KB | Şubat–Mart 2026 |

**Toplam ZIP sayısı:** 40+ dosya
**En son model:** `ppo_conservative_20260306_063457` (6 Mart 2026)
✅ Model artifact'ları eksiksiz ve mevcut.

> **Not:** En son model güncellemesi 27 gün önce. Aktif retraining'in durumu `registry.json` üzerinden izlenebilir.

---

### 5. ⚙️ Konfigürasyon Kontrolü

| Kontrol | Sonuç |
|---------|-------|
| `.env` dosyası var mı? | ✅ Mevcut (806 bytes, 27 Mart 2026) |
| `user_settings.json` geçerli JSON? | ✅ Geçerli |
| `.env.example` var mı? | ✅ Mevcut |
| Tüm example key'ler .env'de var mı? | ✅ Tüm 11 key mevcut |

**.env.example key listesi (tümü .env'de karşılıklı):**
`ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `FINPILOT_SECRET_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `MLFLOW_TRACKING_URI`, `NEWS_API_KEY`, `POLYGON_API_KEY`, `REDIS_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

---

### 6. 🌐 API Router Envanteri

| Router Dosyası | Endpoint Sayısı |
|----------------|-----------------|
| `trade.py` | 5 |
| `history.py` | 4 |
| `models.py` | 4 |
| `optuna.py` | 4 |
| `inference.py` | 2 |
| `llm.py` | 2 |
| `user.py` | 3 |
| `backtest.py` | 1 |
| `ensemble.py` | 1 |
| `scan.py` | 1 |
| **TOPLAM** | **27** |

Son güncellenen router'lar: `history.py`, `optuna.py`, `models.py` (2 Nisan 2026).

---

### 7. 🔒 Güvenlik Kontrol Listesi

| Kontrol | Durum |
|---------|-------|
| `FINPILOT_SECRET_KEY` placeholder değerinde mi? | ✅ Değiştirilmiş (güvenli) |
| `requirements.txt` pinned versiyonlar | ⚠️ Karma — kısmen pinned |

**requirements.txt versiyonlama detayı:**
- Tam sabitlenmiş (`==`): 16 paket (pandas, numpy, yfinance, requests, groq vb.)
- Aralık belirtilmiş (`>=`, `<`): 13 paket (streamlit, plotly, lxml vb.)
- Toplam bağımlılık: ~29 paket

> **Öneri:** `streamlit>=1.53.0,<2.0.0` gibi geniş aralıklar üretim ortamında beklenmedik davranışlara yol açabilir. Kritik paketlerin tam versiyonu sabitlenmeli (`pip freeze > requirements.lock` kullanımı düşünülebilir).

---

## 🚨 Eylem Gerektirenler

### KRİTİK

1. **Veri eskimesi (65+ gün):** `data/shortlists/` ve `data/suggestions/` klasörlerindeki veriler son 2 aydan beri güncellenmemiş. Scanner'ın neden çalışmadığı veya çıktıların neden kaydedilmediği araştırılmalı. Prod ortamında bu durum stale sinyal üretilmesine yol açar.

### UYARI

2. **Delisted sembol kirliliği:** Log dosyalarında toplam 3.177 hata var, büyük çoğunluğu delisted/birleşmiş şirketler ($SUMO, $SPLK, $NEWR vb.) nedeniyle. Bu semboller aktif tarama listesinden çıkarılmalı.

3. **TypeError: NoneType hatası:** `retrain_swing_optuna2.log` (TLT) ve `retrain_volatile_v2.log` (AMD) için yfinance `None` döndürdüğünde uygulama None check yapmadan indekslemeye çalışıyor. Guard clause eklenmeli.

4. **requirements.txt karma pinning:** 13 paket aralıklı versiyon kullanıyor. Reproducibility açısından tam sabitlenmesi önerilir.

### BİLGİ

5. **En son model 27 gün önce:** Son retraining 6 Mart 2026. Piyasa koşulları değiştiyse model kalibrasyon güncellemesi değerlendirilebilir.

---

---

### Kontrol Edilen Delisted Semboller (56 Adet)

Aşağıdaki semboller log dosyalarında "possibly delisted" hatası veriyor ve tarama listesinden temizlenmesi önerilen tickerlar:

`$ACCD`, `$ADAP`, `$ADVM`, `$AKRO`, `$AMEH`, `$AMODW`, `$ANTM`, `$AREBW`, `$ARVL`, `$ASTR`, `$ATXS`, `$AVDL`, `$BLUE`, `$CLR`, `$CMA`, `$CMPO`, `$DCFC`, `$ESGLW`, `$ETNB`, `$FFIE`, `$FGIWW`, `$FREYR`, `$FSR`, `$GIPRW`, `$GOEV`, `$HES`, `$LVGO`, `$MAXR`, `$MMC`, `$MOBBW`, `$MRO`, `$MRUS`, `$NEWR`, `$NKLA`, `$NOVA`, `$ONEM`, `$ORCC`, `$PTRA`, `$PXD`, `$RIDE`, `$RNWWW`, `$RVSNW`, `$SBNY`, `$SENEB`, `$SGEN`, `$SKX`, `$SPLK`, `$SQ`, `$SUMO`, `$SWN`, `$VERV`, `$VLNC`, `$VORB`, `$WHLRL`, `$WLDSW`, `$WLTW`

---

*Rapor otomatik olarak oluşturulmuştur — FinPilot Daily Health Bot | 2026-04-03 (ikinci run)*
