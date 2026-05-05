# 🏥 FinPilot Günlük Sağlık Raporu — 2026-05-05

_Otomatik üretildi · Tarama saati: 2026-05-05_

## Özet

| Metrik | Değer | Durum |
|--------|-------|-------|
| Log Hata Sayısı (api+web) | 9 (ERROR/Failed); 0 CRITICAL; 0 Exception | ⚠️ |
| Veri Tazeliği — shortlists | 21 saat | ✅ |
| Veri Tazeliği — suggestions | ~2352 saat (≈98 gün) | 🚨 |
| Test Sayısı | 27 dosya / 482 `def test_` | ✅ |
| Model Artifact | 40 ZIP, `best_model.zip` mevcut | ✅ |
| Config | `.env` ✅, `user_settings.json` ✅ valid JSON, tüm `.env.example` key'leri kapalı | ✅ |
| API Router | 11 router / 32 endpoint | ✅ |
| Güvenlik (Secret + Pin) | Secret placeholder DEĞİL, requirements 37/37 pinned | ✅ |
| Genel Durum | Çoğunlukla sağlıklı, 2 uyarı | ⚠️ |

---

## Detaylar

### 1. Log Anomali Taraması

En son değiştirilen log dosyaları (logs/ klasöründe en taze 2 dosya 18 Nisan tarihli — bu da log üretiminin yaklaşık 2 hafta önce durduğuna işaret ediyor; canlı sistem değilse bilgi amaçlıdır).

Toplam pattern sayıları:

- `logs/api.log` — ERROR: 1, CRITICAL: 0, Exception: 0, Failed: 0
- `logs/web.log` — ERROR: 8, CRITICAL: 0, Exception: 0, Failed: 4

Top-3 tekrarlanan hata (normalleştirilmiş; tarih/sayı farkları birleştirildi):

| # | Tekrar | Mesaj | Kaynak |
|---|--------|-------|--------|
| 1 | 4× | `Failed to proxy http://localhost:N/api/vN/scan Error: socket hang up` | web.log |
| 2 | 4× | `Error: socket hang up` | web.log |
| 3 | 1× | `Redis connection failed: Error N connecting to localhost:N. Connection refused.. Cache running in memory-only mode.` | api.log |

Yorum: Hatalar yapısal değil — Web → API proxy çağrılarının `/api/v1/scan` endpoint'inde zaman aşımına düşmesi tek bir tarama oturumuna ait görünüyor. Redis hatası graceful fallback ile in-memory cache'e dönmüş. Kritik (`CRITICAL`) veya unhandled `Exception` yok.

### 2. Veri Tazelik Kontrolü

- `data/shortlists/` — En yeni: `shortlist_20260504_2026.csv` (2026-05-04 17:26 UTC, **21 saat** öncesi). ✅ 24 saatten taze.
- `data/suggestions/` — En yeni: `suggestions_fromcsv_..._20250916_1811.csv` (2026-01-27 14:50, **~98 gün** öncesi). 🚨 Eşik aşıldı; öneri pipeline'ı uzun süredir çıktı üretmiyor.

### 3. Test Envanteri

- Test dosyası sayısı: **27** (`tests/**/test_*.py`)
- Toplam test fonksiyonu (`def test_` taraması): **482**
- En son eklenen / değiştirilen dosya: `tests/test_db_backend.py` (Apr 22, 2026 — 3593 byte)
- İkinci en yeni: `tests/scanner_rollout/test_threshold_activation.py` (Apr 22 14:40)

### 4. Model Artifact Kontrolü

- `models/` altında **40 adet** `.zip` model artifact mevcut. Eksik / 0-byte dosya yok.
- En yeni model artifact'leri:

| Boyut | Dosya | Tarih |
|------:|-------|-------|
| 0.67 MB | `models/ppo_conservative_20260306_063457/model.zip` | 2026-03-06 |
| 0.67 MB | `models/ppo_momentum_20260306_001305/model.zip` | 2026-03-06 |
| 0.67 MB | `models/ppo_trend_20260305_233633/model.zip` | 2026-03-05 |
| 7.07 MB | `models/rppo_swing_20260304_220401/model.zip` | 2026-03-04 |
| 0.67 MB | `models/ppo_trend_20260304_233619/model.zip` | 2026-03-04 |

- `models/best/best_model.zip` mevcut (165 KB, 2026-02-26). ✅
- Strateji ailesi kapsaması: `ppo_conservative`, `ppo_momentum`, `ppo_trend`, `ppo_aggressive`, `ppo_breakout`, `ppo_meanrev`, `ppo_scalper`, `ppo_range`, `rppo_swing`. Bilinen ana profillerin tamamı temsil ediliyor.

### 5. Konfigürasyon Kontrolü

- `.env` dosyası: **var** ✅
- `user_settings.json`: **geçerli JSON** ✅
- `.env.example` içindeki **11** anahtarın hepsi `.env` içinde tanımlı (`.env`'de toplam 12 anahtar — yani fazladan 1 yerel anahtar bulunuyor). Eksik anahtar: **yok**. ✅

### 6. API Router Envanteri

`api/routers/` altında 11 router dosyası. Endpoint sayıları (`@router.` decorator sayımı):

| Router | Endpoint |
|--------|---------:|
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
| user.py | 3 |
| **Toplam** | **32** |

### 7. Güvenlik Kontrol Listesi

- `FINPILOT_SECRET_KEY`: `.env.example` placeholder değeri = `your_64_character_hex_secret_here`. `.env` içindeki gerçek değer placeholder'dan **farklı**. ✅
- `requirements.txt`: 37 satır bağımlılık, **hepsi `==` ile pin'li**, unpinned yok. ✅

---

## Eylem Gerektirenler

🚨 **Yüksek**
- `data/suggestions/` 98 gündür güncellenmemiş. Suggestion pipeline'ının (cron / scheduler / ETL job) durup durmadığı kontrol edilmeli — beklenen davranış değilse aciliyet taşır.

⚠️ **Orta**
- Logs klasöründeki en taze `api.log` / `web.log` 18 Nisan 2026 tarihli; bugünden 17 gün önce. Servisler durdurulmuşsa beklenen, çalışıyorsa logging pipeline'ı kesilmiş olabilir.
- web.log'taki 8 socket-hang-up + 4 proxy fail (toplam 8 satır, aynı `/api/v1/scan` endpoint'ine düşüyor) tek oturumda yoğunlaşmış görünüyor; tekrar ederse scan endpoint'inin uzun süreli çağrılar için timeout ayarı gözden geçirilmeli.
- `models/best/best_model.zip` 26 Şubat'tan beri güncellenmemiş — yeni eğitilen `ppo_*_20260306_*` modellerinden biri "best" olarak promote edilmemiş olabilir.

✅ **Bilgi**
- Kritik hata, unpinned dependency, eksik config key veya placeholder secret yok. Güvenlik temelleri tutuyor.

---

_Rapor yolu: `data/reports_cache/health_report_2026-05-05.md`_
