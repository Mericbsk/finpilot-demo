# 🏥 FinPilot Günlük Sağlık Raporu — 2026-04-19

## Özet

| Metrik | Değer | Durum |
|--------|-------|-------|
| Log Hata Sayısı | 9 (api:1, web:8) | ⚠️ |
| Veri Tazeliği (shortlists) | ~23 saat | ✅ |
| Veri Tazeliği (suggestions) | 82+ gün | 🚨 |
| Test Sayısı | 479 fonksiyon / 25 dosya | ✅ |
| Model Artifact | 40 ZIP (en yeni 44 gün eski) | ⚠️ |
| Config | .env + JSON geçerli | ✅ |
| API Endpoint'leri | 32 endpoint / 11 router | ✅ |
| Güvenlik (SECRET_KEY) | Gerçek 64-char hex | ✅ |
| Requirements Pinning | 36/36 pinned | ✅ |

---

## Detaylar

### 1. Log Anomali Taraması
Son log dosyaları (`logs/api.log` ve `logs/web.log`, son değişiklik **18 Nis 16:51**) tarandı. Toplam **9 anomali** pattern'i bulundu.

**Top-5 Hatalar:**

| Adet | Hata |
|------|------|
| 4 | `Failed to proxy http://localhost:8000/api/v1/scan Error: socket hang up` (web.log) |
| 4 | `Error: socket hang up` (web.log) |
| 1 | `Redis connection failed: Error 111 connecting to localhost:6379. Connection refused.. Cache running in memory-only mode.` (api.log) |

**Yorum:** Redis bağlantısı başarısız — cache memory-only mode'a düşmüş. Web tarafında API proxy scan endpoint'i socket hang up alıyor; backend'in (port 8000) scan sırasında kapandığını veya timeout olduğunu gösterir. Akut değil (log 1 gün eski), fakat Redis çalıştırılmalı.

### 2. Veri Tazelik Kontrolü

**`data/shortlists/`** → En son dosya `shortlist_20260418_1227.csv`, 18 Nis 14:27 → **~23 saat yaş** → ✅ 24 saat sınırının altında.

**`data/suggestions/`** → En son dosya `suggestions_fromcsv_*_20250916_*.csv`, 27 Oca 15:50'de son dokunuldu ama içeriği 2025-09-16 tarihli → **82+ gün yaş** → 🚨 **Kritik eskilik**. Suggestion pipeline'ı aylardır çalışmamış veya çıktılar kaybolmuş.

### 3. Test Envanteri

- Toplam test dosyası: **25** (`tests/*.py`)
- Toplam `test_` fonksiyon: **479**
- En son eklenen/güncellenen test dosyası: `tests/test_db_backend.py` (19 Nis 13:33, bugün)
- Öne çıkan diğer dosyalar: `test_api_runtime.py` (16 Nis), `test_drl_integration.py` (26 Mar)

### 4. Model Artifact Kontrolü

`models/` klasöründe **40 ZIP** dosyası var — eksik model yok. Registry (`registry.json`) 19 Nis'te güncellenmiş.

En yeni 5 model run artifact'ı:

| Tarih | Boyut | Path |
|-------|-------|------|
| 2026-03-06 07:34 | 688.6 KB | `ppo_conservative_20260306_063457/model.zip` |
| 2026-03-06 01:13 | 688.6 KB | `ppo_momentum_20260306_001305/model.zip` |
| 2026-03-06 00:36 | 688.6 KB | `ppo_trend_20260305_233633/model.zip` |
| 2026-03-05 00:36 | 688.6 KB | `ppo_trend_20260304_233619/model.zip` |
| 2026-03-05 00:24 | 688.6 KB | `ppo_conservative_20260304_232440/model.zip` |
| 2026-03-04 23:04 | 7240.0 KB | `rppo_swing_20260304_220401/model.zip` |

**Yorum:** Çıktı var ancak en yeni training run **44 gün eski** (6 Mart). Retraining cadansı duraksamış — yeni sprint run'ları yapılmıyor. ⚠️

### 5. Konfigürasyon Kontrolü

- `.env` → **VAR** (821 bytes, 7 Nis)
- `.env.example` → **VAR** (1249 bytes, 10 Mar)
- `user_settings.json` → **Geçerli JSON** ✅

**Key karşılaştırma (.env.example → .env):**

Tüm 11 key `.env`'de mevcut: `FINPILOT_SECRET_KEY`, `GROQ_API_KEY`, `GOOGLE_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `POLYGON_API_KEY`, `NEWS_API_KEY`, `MLFLOW_TRACKING_URI`, `REDIS_URL`, `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` → ✅

`.env`'de ayrıca `CACHE__REDIS_ENABLED` var (`.env.example`'da yok, dokümante edilmeli).

### 6. API Router Envanteri

11 aktif router dosyası, toplam **32 endpoint**:

| Router | Endpoint Sayısı |
|--------|-----------------|
| `trade.py` | 5 |
| `auth.py` | 4 |
| `history.py` | 4 |
| `models.py` | 4 |
| `optuna.py` | 4 |
| `user.py` | 3 |
| `inference.py` | 2 |
| `llm.py` | 2 |
| `scan.py` | 2 |
| `backtest.py` | 1 |
| `ensemble.py` | 1 |

### 7. Güvenlik Kontrol Listesi

- **`FINPILOT_SECRET_KEY`**: `.env`'deki değer gerçek 64-karakterlik hex (`5b8c9622…5255fb1`), `.env.example`'daki placeholder (`your_64_character_hex_secret_here`) ile **eşleşmiyor** → ✅ Güvenli.
- **`requirements.txt` pinning**: 36/36 bağımlılık `==` operatörü ile sabitlenmiş → ✅ Reproducibility tam.

---

## Eylem Gerektirenler

1. 🚨 **`data/suggestions/` pipeline'ı çalışmıyor** — 82+ gün eski. Suggestion üretici job/cron'un neden durduğu araştırılmalı.
2. ⚠️ **Redis down** — `logs/api.log`'ta `Connection refused` (localhost:6379). Redis container'ı/daemon'u başlatılmalı, yoksa cache performansı düşüyor (memory-only fallback).
3. ⚠️ **Web→API proxy socket hang up** — `scan` endpoint'inde 4+ hata. Backend timeout ayarları veya long-running scan sırasında worker çökmesi incelenmeli.
4. ⚠️ **Model retraining duraksamış** — en yeni run 6 Mart. Eğer planlı retraining cadansı varsa (haftalık/aylık) scheduler/MLflow job durumu kontrol edilmeli.
5. ℹ️ `.env.example`'ı `CACHE__REDIS_ENABLED` ile güncelle (drift var).

---

*Rapor yolu:* `/Borsa/data/reports_cache/health_report_2026-04-19.md`
