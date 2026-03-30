# 🏥 FinPilot Günlük Sağlık Raporu — 2026-03-27

> **Rapor oluşturuldu:** 2026-03-27 (Otomatik zamanlanmış görev)
> **Proje:** `/sessions/lucid-bold-cray/mnt/Borsa`

---

## Özet

| Metrik | Değer | Durum |
|--------|-------|-------|
| Log Hata Sayısı | 3.177 satır | ⚠️ Yüksek (beklenen yfinance hataları) |
| Veri Tazeliği (shortlists) | ~1.413 saat (~59 gün) | 🚨 Çok Eski |
| Veri Tazeliği (suggestions) | ~1.413 saat (~59 gün) | 🚨 Çok Eski |
| Test Sayısı | 466 fonksiyon / 23 dosya | ✅ |
| Model Artifact (ZIP) | 40 dosya | ✅ |
| Config (.env varlığı) | Mevcut | ✅ |
| Config (eksik key'ler) | FINPILOT_SECRET_KEY, REDIS_URL | 🚨 |
| user_settings.json | Geçerli JSON | ✅ |
| API Endpoint Toplamı | 22 endpoint / 10 router | ✅ |
| Güvenlik (SECRET_KEY) | .env'de eksik | 🚨 |
| requirements.txt | Range pin kullanılıyor | ⚠️ |

---

## Detaylar

### 1. 🔍 Log Anomali Taraması

**Toplam hata satırı dağılımı:**

| Log Dosyası | ERROR/CRITICAL/Exception/Failed |
|---|---|
| `full_scan_20260302_2018.log` | 2.930 |
| `auto_scan_trade.log` | 241 |
| `retrain_volatile_v2.log` | 3 |
| `retrain_swing_optuna2.log` | 3 |
| Diğer tüm .log dosyaları | 0 |
| **Toplam** | **3.177** |

**CRITICAL ve Exception:** Hiçbir log dosyasında CRITICAL veya Exception seviyesinde giriş bulunmadı. ✅

**Top-5 En Sık Tekrarlanan Hata Paterni:**

1. **"Failed download"** — 15 tekrar (yfinance indirme hatası)
2. **"ERROR | yfinance |"** — 13 tekrar (genel yfinance hata başlığı)
3. **$SUMO delisted** — 16 tekrar (4 farklı period × 4) — muhtemelen listeden çıkmış hisse
4. **$SPLK delisted** — 16 tekrar — muhtemelen listeden çıkmış hisse
5. **$NEWR delisted** — 16 tekrar — muhtemelen listeden çıkmış hisse

**Ek bulgular:**
- `retrain_volatile_v2.log`: `['AMD']: TypeError("'NoneType' object is not subscriptable")` — AMD verisi için NoneType hatası
- `retrain_swing_optuna2.log`: `['TLT']: TypeError("'NoneType' object is not subscriptable")` — TLT için aynı hata

**Yorum:** Hataların büyük çoğunluğu yfinance aracılığıyla delisted (listeden çıkmış) hisselerin verilerinin çekilmeye çalışılmasından kaynaklanıyor. Bu hatalar kritik değil ancak tarama listesinin güncellenmesi önerilir. SUMO, SPLK, NEWR, SGEN, BLUE sembolleri kontrol edilmeli.

---

### 2. 📅 Veri Tazelik Kontrolü

| Klasör | En Yeni Dosya | Yaş |
|---|---|---|
| `data/shortlists/` | `shortlist_20251201_2111.csv` | ~1.413 saat (~59 gün) |
| `data/suggestions/` | `suggestions_20251201_2111.csv` | ~1.413 saat (~59 gün) |

**⚠️ Uyarı:** Her iki klasördeki veriler de 24 saatten çok daha eski — yaklaşık **59 gün** önce güncellenmiş. Bu, aktif tarama/öneri döngüsünün çalışmadığına ya da çıktıların farklı bir konuma yazıldığına işaret edebilir.

- Shortlist dosya sayısı: 74 CSV
- Suggestions dosya sayısı: 61 CSV
- Son içerik tarihi (dosya adından): Aralık 2025

---

### 3. 🧪 Test Envanteri

| Metrik | Değer |
|---|---|
| Toplam test dosyası | 23 |
| Toplam `def test_` sayısı | **466** |
| Son eklenen/değiştirilen | `test_db_backend.py` (26 Mar 2026, 20:59) |

**Dosya bazlı dağılım:**

| Dosya | Test Sayısı |
|---|---|
| test_social.py | 40 |
| test_core.py | 38 |
| test_validation.py | 37 |
| test_llm.py | 32 |
| test_auth.py | 31 |
| test_prometheus.py | 31 |
| test_websocket_feeds.py | 30 |
| test_backtest.py | 22 |
| test_sentry.py | 22 |
| test_signals.py | 23 |
| test_plugins.py | 23 |
| test_data_fetcher.py | 21 |
| test_indicators.py | 19 |
| test_broker.py | 18 |
| test_db_repos.py | 17 |
| test_views_smoke.py | 16 |
| test_evaluate.py | 14 |
| test_drl_integration.py | 5 |
| test_db_backend.py | 8 |
| test_views_integration.py | 8 |
| test_feature_generators.py | 5 |
| test_explainability.py | 3 |
| test_alignment_helpers.py | 3 |

---

### 4. 🤖 Model Artifact Kontrolü

**ZIP Dosyaları:** 40 adet ✅

| Konum | Açıklama |
|---|---|
| `models/best/best_model.zip` | 169 KB, 26 Şubat 2026 |
| `models/checkpoints/` | 11× ppo_balanced + 11× ppo_production checkpoints |
| `models/ppo_*/` | 17 PPO model dizini |
| `models/rppo_*/` | 2 RPPO model dizini (Swing, ~7.1 MB her biri) |

**Model dizinleri özeti:**

- En yeni model: `ppo_conservative_20260306_063457` (6 Mart 2026)
- En büyük dizinler: `rppo_swing_20260302_212140` ve `rppo_swing_20260304_220401` (7.1 MB her biri)
- Registry: `models/registry.json` — 19 model kaydı mevcut

**Eksik model:** Yok. Tüm dizinler için artifact mevcut. ✅

---

### 5. ⚙️ Konfigürasyon Kontrolü

| Dosya | Durum |
|---|---|
| `.env` | ✅ Mevcut |
| `.env.example` | ✅ Mevcut |
| `user_settings.json` | ✅ Geçerli JSON |

**.env.example'daki key'lerin .env'de karşılanma durumu:**

| Key | .env'de var mı? |
|---|---|
| ALPACA_API_KEY | ✅ |
| ALPACA_SECRET_KEY | ✅ |
| FINPILOT_SECRET_KEY | 🚨 **EKSİK** |
| GOOGLE_API_KEY | ✅ |
| GROQ_API_KEY | ✅ |
| MLFLOW_TRACKING_URI | ✅ |
| NEWS_API_KEY | ✅ |
| POLYGON_API_KEY | ✅ |
| REDIS_URL | 🚨 **EKSİK** |
| TELEGRAM_BOT_TOKEN | ✅ |
| TELEGRAM_CHAT_ID | ✅ |

**user_settings.json anahtarları:** `risk_score`, `portfolio_size`, `max_loss_pct`, `strategy`, `market`, `telegram_active`, `telegram_id`, `timeframe`, `indicators` — JSON yapısı sağlıklı.

---

### 6. 🔌 API Router Envanteri

**Router dosyası:** `api/routers/` içinde 10 router

| Router Dosyası | Endpoint Sayısı |
|---|---|
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
| **Toplam** | **22 endpoint** |

---

### 7. 🔒 Güvenlik Kontrol Listesi

| Kontrol | Sonuç |
|---|---|
| `FINPILOT_SECRET_KEY` .env'de var mı? | 🚨 **HAYIR — EKSİK** |
| Placeholder değer mi? | N/A (.env'de tanımlı değil) |
| `requirements.txt` pinned versiyonlar | ⚠️ Kısmi — range pin kullanıyor (`>=x,<y`) |

**requirements.txt notu:** Dosya "pinned for reproducibility" olarak işaretlenmiş ancak `==` yerine `>=x,<y` aralık pin kullanıyor. Bu, minor/patch versiyonlarının değişmesine neden olabilir. Kritik değil ama `==` ile tam sabitleme önerilir.

---

## 🚨 Eylem Gerektirenler

### Kritik (Hemen Müdahale)

1. **`FINPILOT_SECRET_KEY` .env dosyasına eklenmeli.**
   Bu key JWT token imzalama / uygulama güvenliği için kritik. .env.example'daki placeholder `your_64_character_hex_secret_here` gerçek bir değerle değiştirilip `.env`'e eklenmeli.

2. **`REDIS_URL` .env dosyasına eklenmeli.**
   Redis bağlantısı için gerekli. Eksik olması cache/queue sistemlerinin çalışmamasına yol açabilir.

3. **Veri tazeliği sorunu — shortlists ve suggestions ~59 gün güncellenmemiş.**
   `data/shortlists/` ve `data/suggestions/` klasörlerindeki son dosyalar Aralık 2025'e ait. Tarama/öneri pipeline'ının çalışıp çalışmadığı kontrol edilmeli.

### Uyarı (Kısa Vadeli)

4. **Delisted hisse sembolleri tarama listesinden çıkarılmalı.**
   SUMO, SPLK, NEWR, SGEN, BLUE sembolleri delisted görünüyor. Shortlist'lerden kaldırılması gereksiz yfinance hata üretimini azaltır.

5. **AMD ve TLT için `NoneType` hatası incelenmeli.**
   `retrain_volatile_v2.log` ve `retrain_swing_optuna2.log` dosyalarındaki TypeError, data pipeline'ında None dönen bir veri kaynağına işaret ediyor.

6. **requirements.txt strict pin'e geçilmeli.**
   Reproducibility için `>=x,<y` yerine `==x.y.z` kullanımı önerilir.

---

*Rapor otomatik olarak oluşturuldu. Herhangi bir sorun için proje sahibine başvurun.*
