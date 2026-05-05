# 🏥 FinPilot Günlük Sağlık Raporu — 2026-04-10

## Özet

| Metrik | Değer | Durum |
|--------|-------|-------|
| Log Hata Sayısı (api.log) | 6 | ⚠️ |
| Log Hata Sayısı (full_scan) | 2930 | ⚠️ |
| Shortlist Tazeliği | 70 saat | ⚠️ |
| Suggestion Tazeliği | ~1748 saat (~73 gün) | 🚨 |
| Test Fonksiyon Sayısı | 466 (23 dosya) | ✅ |
| Model Artifact | 40 ZIP, 22 dizin | ✅ |
| Config (.env) | Tüm 11 key mevcut | ✅ |
| Config (JSON) | Geçerli | ✅ |
| API Endpoint Sayısı | 27 endpoint | ✅ |
| Secret Key | Özelleştirilmiş | ✅ |
| Requirements Pinning | 28/28 sabitlenmiş | ✅ |

---

## Detaylar

### 1. 📋 Log Anomali Taraması

**`api.log`** (14 KB, son değişiklik: 3 Nisan 2026)

Toplam hata satırı: **6**

| # | Hata | Sayı |
|---|------|------|
| 1 | Order failed for HOLX: take_profit.limit_price must be >= base_price + 0.01 | 2 |
| 2 | YFRateLimitError: AIIOW 4h 100d – Too Many Requests | 1 |
| 3 | YFRateLimitError: AIIOW 15m 10d – Too Many Requests | 1 |
| 4 | YFRateLimitError: SKK 1d 400d – Too Many Requests | 1 |
| 5 | YFRateLimitError: MNTS 1h 60d – Too Many Requests | 1 |

**`full_scan_20260302_2018.log`** (1.0 MB, 2 Mart 2026)

Toplam hata/uyarı satırı: **2930** (büyük çoğunluğu altdata fallback uyarıları)

Top-5 tekrarlayan hata türleri:
1. `Warning: Failed to fetch real altdata for [TICKER]: Data must be 1-dimensional, got ndarray of shape (24, 1)` — çok sayıda sembol için
2. `ERROR | yfinance |` — yfinance çekme hataları
3. `Failed download:` — başarısız indirme girişimleri (6 adet)

**`retrain_swing_optuna2.log`** (10 KB, 7 Mart 2026): **3** hata satırı

---

### 2. 📅 Veri Tazelik Kontrolü

**`data/shortlists/`**
- En yeni dosya: `shortlist_20260407_1317.csv` (7 Nisan 2026, 15:17)
- Yaş: **~70 saat** (bugüne göre)
- Durum: ⚠️ 24 saati aştı — yeni tarama gerekebilir

**`data/suggestions/`**
- En yeni dosya: `suggestions_fromcsv_...20250916_1811.csv` (27 Ocak 2026 kopyası, orijinal Eylül 2025)
- Yaş: **~1748 saat (~73 gün)**
- Durum: 🚨 KRİTİK — Suggestion verisi çok eski, öneri motoru çalışmıyor olabilir

---

### 3. 🧪 Test Envanteri

- Toplam test dosyası: **23** (conftest.py dahil)
- Toplam `def test_` fonksiyonu: **466**
- En son değiştirilen test dosyaları:
  1. `test_db_backend.py` — 3 Nisan 2026
  2. `test_drl_integration.py` — 26 Mart 2026
  3. `test_auth.py` — 26 Mart 2026

Test kapsamı sağlam görünüyor.

---

### 4. 🤖 Model Artifact Kontrolü

Toplam ZIP dosyası: **40**
Toplam model dizini: **22**

Önemli modeller:

| Model | Dosya | Boyut | Son Değişiklik |
|-------|-------|-------|----------------|
| best/best_model.zip | best_model.zip | 166 KB | 26 Şubat 2026 |
| ppo_conservative_20260306 | model.zip | 689 KB | 6 Mart 2026 |
| ppo_momentum_20260306 | model.zip | 689 KB | 6 Mart 2026 |
| checkpoints/ppo_production_100000 | .zip | — | — |
| rppo_swing_20260304 | model.zip | — | 4 Mart 2026 |

Eksik model: **YOK** ✅
Not: En son model güncelleme tarihi 6 Mart 2026 (35 gün önce). Yeni bir retrain döngüsü değerlendirilebilir.

---

### 5. ⚙️ Konfigürasyon Kontrolü

| Kontrol | Sonuç |
|---------|-------|
| `.env` dosyası mevcut | ✅ |
| `.env.example` dosyası mevcut | ✅ |
| `user_settings.json` geçerli JSON | ✅ |
| `.env.example`'daki tüm keyler `.env`'de mevcut | ✅ (11/11) |

Eksik key: **YOK**

Mevcut keyler: `FINPILOT_SECRET_KEY`, `GROQ_API_KEY`, `GOOGLE_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `POLYGON_API_KEY`, `NEWS_API_KEY`, `MLFLOW_TRACKING_URI`, `REDIS_URL`, `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`

---

### 6. 🔌 API Router Envanteri

| Router Dosyası | Endpoint Sayısı |
|---------------|-----------------|
| backtest.py | 1 |
| ensemble.py | 1 |
| history.py | 4 |
| inference.py | 2 |
| llm.py | 1 |
| models.py | 4 |
| optuna.py | 4 |
| scan.py | 2 |
| trade.py | 5 |
| user.py | 3 |
| **Toplam** | **27** |

---

### 7. 🔒 Güvenlik Kontrol Listesi

| Kontrol | Sonuç |
|---------|-------|
| `FINPILOT_SECRET_KEY` placeholder değil | ✅ (64 karakter, özelleştirilmiş) |
| `requirements.txt` pinned versiyonlar | ✅ 28/28 paket sabitlenmiş (`==`) |

---

## ⚡ Eylem Gerektirenler

### 🚨 Kritik (Hemen İncelenmeli)

1. **Suggestion Verisi Aşırı Eski**: `data/suggestions/` klasöründeki en yeni dosya ~73 gün eski (Eylül 2025 kaynaklı). Öneri motoru aktif çalışmıyor veya çıktılar bu klasöre yazılmıyor olabilir. Sürecin mevcut durumu kontrol edilmeli.

### ⚠️ Uyarılar (Bu Hafta İçinde Değerlendirilmeli)

2. **Shortlist Tazeliği**: En yeni shortlist 70 saat önce (7 Nisan 2026) oluşturulmuş. Günlük tarama cronjob'unun düzgün çalıştığı doğrulanmalı.

3. **yfinance Rate Limit Hataları**: Birden fazla sembol (AIIOW, SKK, MNTS) için rate limit hatası alınmış. yfinance istek sıklığı azaltılmalı veya ücretli veri kaynağına geçiş değerlendirilmeli.

4. **Order Failure — HOLX**: HOLX için take_profit.limit_price >= base_price + 0.01 kuralı ihlal edilmiş (2 kez). Order oluşturma mantığında fiyat doğrulama iyileştirilebilir.

5. **Altdata Shape Hatası**: Full scan sırasında çok sayıda sembol için `ndarray of shape (24, 1)` hatası alınmış. `altdata` modülündeki squeeze/reshape mantığı düzeltilmeli.

6. **Model Yenileme**: En son model 6 Mart 2026 (35 gün önce). Piyasa koşullarına göre periyodik retrain döngüsü değerlendirilebilir.

---

*Rapor oluşturulma zamanı: 2026-04-10 — FinPilot Sistem Sağlık Botu tarafından otomatik üretilmiştir.*
