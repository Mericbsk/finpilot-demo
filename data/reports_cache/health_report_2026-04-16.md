# 🏥 FinPilot Günlük Sağlık Raporu — 2026-04-16

## Özet

| Metrik | Değer | Durum |
|--------|-------|-------|
| Log Hata Sayısı (aktif) | 0 aktif hata | ✅ |
| Log Hata Sayısı (arşiv) | 3.171 toplam (eski loglar) | ⚠️ |
| Startup Hatası | uvicorn bulunamadı | 🚨 |
| Veri Tazeliği — Shortlists | 0 saat (bugün güncellendi) | ✅ |
| Veri Tazeliği — Suggestions | ~1.894 saat (~79 gün) | ⚠️ |
| Test Sayısı | 23 dosya / 466 fonksiyon | ✅ |
| Model Artifact | 40 ZIP dosyası / 21 klasör | ✅ |
| Konfigürasyon | Tüm anahtarlar mevcut | ✅ |
| Güvenlik | Pinned bağımlılıklar, secret key OK | ✅ |

---

## Detaylar

### 1. Log Anomali Taraması

**Aktif loglar (api.log, web.log):**
- `api.log`: Sıfır ERROR/CRITICAL. Tüm istekler 200 OK. API sağlıklı çalışıyor.
- `web.log`: Sıfır ERROR. Next.js 16.1.6 (Turbopack) normal çalışıyor.
  - Bir Node.js deprecation uyarısı mevcut: `[DEP0060] util._extend` API deprecated, `Object.assign()` kullanılması öneriliyor (düşük öncelikli).
- `api.log`'da 3 Streamlit cache uyarısı: `No runtime found, using MemoryCacheStorageManager` (işlevsel değil, bilgi amaçlı).

**Kritik Startup Sorunu:**
- `api_startup.log`: `/usr/local/bin/python3: No module named uvicorn` — Uvicorn ortamda kurulu değil. API'nin **mevcut çalışma ortamı dışında** (örn. Makefile/bash ile doğrudan) başlatılmaya çalışıldığına işaret ediyor. API `api.log`'a göre şu an ayakta olduğundan muhtemelen farklı bir Python environment kullanılıyor; ancak bu uyumsuzluk göz ardı edilmemeli.

**Arşiv logları hata analizi (auto_scan_trade + full_scan):**
- Toplam hata sayısı: 3.171 (tümü 2-3 Mart 2026 tarihli tarama loglarında)

**Top 5 Hata Kategorisi:**

| Sıra | Hata | Adet |
|------|------|------|
| 1 | yfinance — ticker possibly delisted (Yahoo error) | ~380 |
| 2 | yfinance — generic delisted / no price data | ~68 |
| 3 | yfinance — `NoneType` subscript TypeError (download fail) | ~26 |
| 4 | yfinance — Connection timeout (LAUR) | ~5 |
| 5 | altdata — ndarray shape uyumsuzluğu, synthetic fallback | ~2 |

Tüm bu hatalar **kalıcı veya geçici olarak borsadan çıkmış (delisted) semboller** için yfinance çağrısı yapılmasından kaynaklanıyor. İşlevsel bir blokaj değil; tarayıcı bunları atlıyor. Sembol veritabanının temizlenmesi önerilir.

---

### 2. Veri Tazelik Kontrolü

**data/shortlists/**
- Toplam: 121 CSV dosyası
- En son dosya: `shortlist_20260416_1249.csv`
- Son güncelleme: 2026-04-16 14:49 (0 saat önce)
- Durum: ✅ Taze

**data/suggestions/**
- Toplam: 63 dosya
- En son dosya: `suggestions_fromcsv_...nasdaq_screener_..._20250916_1314.csv`
- Son güncelleme: 2026-01-27 15:50 (~1.894 saat = ~79 gün önce)
- Durum: ⚠️ **Eski veri** — 24 saat eşiğinin çok üzerinde. Suggestions klasörü güncellenmemiş.

---

### 3. Test Envanteri

- **Toplam test dosyası:** 23 adet
- **Toplam test fonksiyonu:** 466 adet

**Dosya başına dağılım:**

| Dosya | Test |
|-------|------|
| test_social.py | 40 |
| test_validation.py | 37 |
| test_core.py | 38 |
| test_auth.py | 31 |
| test_prometheus.py | 31 |
| test_llm.py | 32 |
| test_websocket_feeds.py | 30 |
| test_sentry.py | 22 |
| test_backtest.py | 22 |
| test_data_fetcher.py | 21 |
| test_broker.py | 18 |
| test_db_repos.py | 17 |
| test_views_smoke.py | 16 |
| test_evaluate.py | 14 |
| test_indicators.py | 19 |
| test_plugins.py | 23 |
| test_signals.py | 23 |
| test_db_backend.py | 8 |
| test_views_integration.py | 8 |
| test_drl_integration.py | 5 |
| test_feature_generators.py | 5 |
| test_explainability.py | 3 |
| test_alignment_helpers.py | 3 |

- **En son eklenen test dosyası:** `test_db_backend.py` (2026-04-03, 8 test)

---

### 4. Model Artifact Kontrolü

- **ZIP dosyası sayısı:** 40 adet
  - `models/best/best_model.zip` (168 KB, 2026-02-26)
  - `models/checkpoints/`: 20 ZIP (ppo_balanced + ppo_production serisi)
  - Adlandırılmış model klasörleri: 19 adet (her biri `model.zip` + metadata içeriyor)
- **registry.json:** Geçerli, 19 kayıtlı model girişi
- **Boyut aralığı:** 176 KB – 7.1 MB (model karmaşıklığına göre değişiyor)
- **En güncel model:** `ppo_conservative_20260306_063457` (2026-03-06 07:34)
- **Eksik model:** Yok — tüm kayıtlı modellerin ZIP dosyaları mevcut ✅

---

### 5. Konfigürasyon Kontrolü

| Dosya | Durum |
|-------|-------|
| `.env` | ✅ Mevcut (28 satır, 12 anahtar) |
| `user_settings.json` | ✅ Geçerli JSON (9 anahtar) |
| `.env` vs `.env.example` uyumu | ✅ Tüm 11 anahtar mevcut |

`user_settings.json` içeriği: `risk_score`, `portfolio_size`, `max_loss_pct`, `strategy`, `market`, `telegram_active`, `telegram_id`, `timeframe`, `indicators` — tüm alanlar sağlıklı.

`.env`'de `.env.example`'a ek olarak `CACHE__REDIS_ENABLED` anahtarı bulunuyor (normal, ek konfigürasyon).

---

### 6. API Router Envanteri

`api/routers/` altında **10 aktif router dosyası**, toplam **28 endpoint**:

| Router | Endpoint Sayısı |
|--------|----------------|
| trade.py | 5 |
| history.py | 4 |
| models.py | 4 |
| optuna.py | 4 |
| inference.py | 2 |
| llm.py | 2 |
| scan.py | 2 |
| user.py | 3 |
| backtest.py | 1 |
| ensemble.py | 1 |
| **Toplam** | **28** |

---

### 7. Güvenlik Kontrol Listesi

| Kontrol | Sonuç |
|---------|-------|
| `FINPILOT_SECRET_KEY` placeholder mı? | ✅ HAYIR — gerçek değer set edilmiş |
| `requirements.txt` pinned versiyonlar | ✅ 62/62 paket sabitlenmiş (`==` versiyonlama) |

`requirements.txt` içindeki hiçbir paket sürüm sabitleme olmadan (`>=`, `~=` vb.) tanımlanmamış. Bu iyi bir güvenlik ve yeniden üretilebilirlik pratiğidir.

---

## Eylem Gerektirenler

### 🚨 Kritik

1. **Uvicorn bulunamadı (api_startup.log):** `/usr/local/bin/python3: No module named uvicorn` hatası, standart Python ortamında uvicorn kurulu değil. API'nin farklı bir virtual environment içinden çalıştığı anlaşılıyor ancak bu tutarsızlık deployment güvenilirliğini tehdit ediyor. `Makefile` veya `start.sh` içindeki Python path kontrolü önerilir. Çözüm: `pip install uvicorn` doğru environment için veya `start.sh`'in doğru venv'i aktive ettiğinden emin olunması.

### ⚠️ Uyarı

2. **Suggestions verisi eskimiş (~79 gün):** `data/suggestions/` klasöründeki en yeni dosya Ocak 2026'ya ait. Bu klasörün yenilenmesi için bir ETL işi veya elle güncelleme gerekiyor. Suggestions pipeline'ı (CSV'den yükleme) çalışmıyor olabilir.

3. **Delisted semboller tarayıcıda:** yfinance loglarında SPLK, NEWR, SUMO, SGEN, BLUE gibi borsadan çıkmış (delisted) semboller tekrar tekrar sorgulanıyor. `data/dictionary_v2.json` veya sembol veritabanından bu semboller temizlenmelidir. Bu, tarama sürelerini önemli ölçüde kısaltacaktır.

### ℹ️ Bilgi

4. **Node.js DEP0060 uyarısı:** `util._extend` deprecated. Next.js web paketi bu uyarıyı üretiyor. Güncel bir Node.js/Next.js versiyonuna geçildiğinde otomatik düzelecektir (düşük öncelikli).

5. **Streamlit cache uyarısı:** `api.log`'da 3 adet Streamlit "No runtime" uyarısı var. Bu, API context'inde import edilen bir Streamlit modülünden kaynaklanıyor. Streamlit kütüphanesi API koduna bağımlılık olarak dahil edilmemeli; modüler ayrım sağlanmalıdır.

---

*Rapor otomatik olarak oluşturulmuştur — 2026-04-16 (FinPilot Health Bot)*
