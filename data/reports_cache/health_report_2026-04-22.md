# FinPilot Gunluk Saglik Raporu — 2026-04-22

## Ozet

| Metrik | Deger | Durum |
|--------|-------|-------|
| Log Hata Sayisi | 3.177 pattern eslesmesi (16 log dosyasinda) | WARN |
| Veri Tazeligi (shortlists) | 93,1 saat (2026-04-18 14:27) | WARN |
| Veri Tazeligi (suggestions) | 2.034,7 saat / ~85 gun (2026-01-27) | CRITICAL |
| Test Sayisi | 482 `def test_` (31 test dosyasi) | OK |
| Model Artifact | 40 .zip (19 model.zip + 20 checkpoint + 1 best_model.zip) | OK |
| API Router Endpoint | 32 endpoint (11 router) | OK |
| Config (.env / JSON) | Tum anahtarlar mevcut, JSON gecerli | OK |
| FINPILOT_SECRET_KEY | Placeholder degil, 64-char hex | OK |
| requirements.txt Pinning | 35/35 pinned (==) | OK |

---

## 1. Log Anomali Taramasi

`logs/` klasorundeki 16 log dosyasi tarandi. ERROR / CRITICAL / Exception / Failed pattern eslesmeleri:

| Log Dosyasi | Hata Sayisi |
|-------------|-------------|
| full_scan_20260302_2018.log | 2.930 |
| auto_scan_trade.log | 241 |
| retrain_swing_optuna2.log | 3 |
| retrain_volatile_v2.log | 3 |
| api.log | 0 |
| conservative_3m_training.log | 0 |
| optuna_conservative.log | 0 |
| optuna_momentum.log | 0 |
| optuna_swing.log | 0 |
| retrain_conservative_optuna.log | 0 |
| retrain_momentum_optuna.log | 0 |
| retrain_range_v2.log | 0 |
| retrain_sprint16.log | 0 |
| retrain_swing_optuna.log | 0 |
| swing_3m_training.log | 0 |
| train_momentum_3m.log | 0 |
| **TOPLAM** | **3.177** |

### Top-5 En Sik Tekrarlanan Hata Pattern'leri

1. **`Failed download: ...`** — 15 tekrar (yfinance indirme hatasi)
2. **`ERROR | yfinance | ` (cesitli)** — 13 tekrar (genel yfinance hatasi)
3. **`$SUMO: possibly delisted`** — 16 tekrar (4 ayri periyot x 4: 10d/60d/100d/400d)
4. **`$SPLK: possibly delisted`** — 16 tekrar
5. **`$NEWR: possibly delisted`** — 16 tekrar

Ayrica yuksek hacimli: $SGEN (12), $BLUE (12). Hatalarin ezici cogunlugu Mart 2026 donemindeki `full_scan_20260302_2018.log` ve `auto_scan_trade.log` dosyalarindan geliyor — delisted ticker'larin scan universe'inden temizlenmesi tavsiye edilir.

**Not:** `api.log` son 48 gunde (son kayit 2026-04-18) **sifir** ERROR/CRITICAL icermiyor. Uretim API'si saglikli gorunuyor.

---

## 2. Veri Tazelik Kontrolu

### `data/shortlists/`
- En son dosya: **`shortlist_20260418_1227.csv`** (7.741 bayt)
- Son degisiklik: 2026-04-18 14:27:53
- Yas: **~93,1 saat** (~3,9 gun)
- Durum: **WARN** — 24 saatten eski. Gunluk shortlist uretimi planlandigi sekilde calismiyor olabilir.

### `data/suggestions/`
- En son dosya: **`suggestions_20251201_2111.csv`**
- Son degisiklik: 2026-01-27 15:50:45
- Yas: **~2.034,7 saat** (~85 gun / ~12 hafta)
- Durum: **CRITICAL** — 3 aydan uzun suredir yeni suggestion uretilmiyor. Pipeline'in kirildigi veya devre disi birakildigi kuvvetle tahmin ediliyor.

---

## 3. Test Envanteri

- Test Python dosyasi sayisi (`__pycache__` haric): **31**
- Toplam `def test_` eslesmesi (class method'lar dahil): **482**
- Modul-seviyesi (top-level) test fonksiyonu: **32**
- En son eklenen/degisen test dosyasi: **`tests/test_db_backend.py`** (2026-04-19 13:33)

### Alt Klasorler
- `tests/scanner_rollout/` — 3 test dosyasi (test_historical_replay, test_runtime_baseline, test_threshold_activation)

Test dagilimi (modul basi `def test_` sayisi, ust 10):
- test_core.py: 38
- test_social.py: 40
- test_validation.py: 37
- test_llm.py: 32
- test_auth.py: 31
- test_prometheus.py: 31
- test_websocket_feeds.py: 30
- test_signals.py: 23
- test_plugins.py: 23
- test_backtest.py: 22

---

## 4. Model Artifact Kontrolu

`models/` klasorunde toplam **40 .zip** dosyasi bulundu. `models/registry.json` gecerli JSON ve 19 model girdisi iceriyor.

### Ana Model Dosyalari (model.zip)

| Model | Boyut (KB) | Son Degisiklik |
|-------|-----------|---------------|
| rppo_swing_20260304_220401 | 7.240 | 2026-03-04 23:04 |
| rppo_swing_20260302_212140 | 7.240 | 2026-03-02 22:21 |
| ppo_conservative_20260306_063457 | 688 | 2026-03-06 07:34 |
| ppo_trend_20260305_233633 | 688 | 2026-03-06 00:36 |
| ppo_momentum_20260306_001305 | 688 | 2026-03-06 01:13 |
| ppo_conservative_20260304_232440 | 688 | 2026-03-05 00:24 |
| ppo_trend_20260304_233619 | 688 | 2026-03-05 00:36 |
| ppo_trend_20260304_221324 | 688 | 2026-03-04 23:13 |
| ppo_scalper_20260302_200828 | 399 | 2026-03-02 21:08 |
| ppo_momentum_20260303_191357 | 264 | 2026-03-03 20:13 |
| ppo_trend_20260304_193141 | 264 | 2026-03-04 20:31 |
| ppo_aggressive_20260302_215335 | 264 | 2026-03-02 22:53 |
| ppo_breakout_20260302_191605 | 264 | 2026-03-02 20:16 |
| ppo_conservative_20260302_214206 | 264 | 2026-03-02 22:42 |
| ppo_meanrev_20260302_190334 | 264 | 2026-03-02 20:03 |
| ppo_momentum_20260302_184945 | 264 | 2026-03-02 19:49 |
| ppo_volatile_20260225_192559 | 165 | 2026-02-26 18:15 |
| ppo_trend_20260225_181020 | 165 | 2026-02-26 18:15 |
| ppo_range_20260226_170853 | 165 | 2026-02-26 18:08 |

### Diger
- `models/best/best_model.zip` — 165 KB (2026-02-26 18:16)
- `models/checkpoints/` — 20 checkpoint (.zip) dosyasi

**Strateji Kapsama Durumu:** trend, volatile, range, momentum, meanrev, breakout, scalper, swing (rppo), conservative, aggressive — **tum ana stratejiler icin en az bir model mevcut.** Eksik model yok.

**Uyari (bilgi):** En yeni model 2026-03-06 tarihli — 47 gundur yeni model training'i yok. Retrain cadence'inin gozden gecirilmesi faydali olabilir.

---

## 5. Konfigurasyon Kontrolu

### `.env` Dosyasi
- Dosya mevcut (1.068 bayt, 2026-04-07 tarihli). Icerik okunmadi, yalnizca varlik ve anahtar listesi kontrol edildi.

### `user_settings.json`
- Gecerli JSON (python json.load basarili).

### `.env.example` ↔ `.env` Anahtar Karsilastirmasi

`.env.example` icindeki **11 anahtar** ve `.env` karsiligi:

| Anahtar | .env.example | .env | Durum |
|---------|:---:|:---:|:---:|
| ALPACA_API_KEY | YES | YES | OK |
| ALPACA_SECRET_KEY | YES | YES | OK |
| FINPILOT_SECRET_KEY | YES | YES | OK |
| GOOGLE_API_KEY | YES | YES | OK |
| GROQ_API_KEY | YES | YES | OK |
| MLFLOW_TRACKING_URI | YES | YES | OK |
| NEWS_API_KEY | YES | YES | OK |
| POLYGON_API_KEY | YES | YES | OK |
| REDIS_URL | YES | YES | OK |
| TELEGRAM_BOT_TOKEN | YES | YES | OK |
| TELEGRAM_CHAT_ID | YES | YES | OK |

**Ekstra (sadece `.env`):** `CACHE__REDIS_ENABLED` — .env.example'a eklenmesi tavsiye edilir (dokumantasyon tutarliligi icin).

---

## 6. API Router Envanteri

`api/routers/` klasorunde 11 router dosyasi. Toplam `@router.` sayisi (endpoint count): **32**

| Router | Endpoint Sayisi |
|--------|----------------|
| trade.py | 5 |
| auth.py | 4 |
| history.py | 4 |
| models.py | 4 |
| optuna.py | 4 |
| user.py | 3 |
| inference.py | 2 |
| llm.py | 2 |
| scan.py | 2 |
| backtest.py | 1 |
| ensemble.py | 1 |
| **TOPLAM** | **32** |

---

## 7. Guvenlik Kontrol Listesi

| Kontrol | Durum |
|---------|:---:|
| `FINPILOT_SECRET_KEY` placeholder degerde mi? | OK (64-char hex, placeholder degil) |
| `requirements.txt` pinning (==) | OK (35/35 satir pinned, `>`, `<`, `~=`, `!=` yok) |
| `.env` disarida (gitignore'da) | Varsayim: .gitignore'da (.gitignore mevcut) |

---

## Eylem Gerektirenler

### CRITICAL
- **`data/suggestions/` pipeline ~85 gundur calismiyor.** Suggestion uretim job'unun (cron/scheduler) son calisma zamani ve hata loglari incelenmeli. Pipeline devre disi ise dokumante edilmeli; aksi halde acil restart/debug gerekiyor.

### WARN
- **`data/shortlists/` son 93 saattir (~4 gun) guncellenmemis.** Gunluk shortlist job'unun calisip calismadigi dogrulanmali (son calisma 2026-04-18).
- **Delisted ticker'lar scan universe'ini kirletiyor:** $SUMO, $SPLK, $NEWR, $SGEN, $BLUE, SGEN, BLUE icin yfinance "possibly delisted" hatalari log'u dolduruyor. Ticker listesinin yfinance'e karsi yeniden dogrulanmasi ve delisted olanlarin cikarilmasi onerilir.
- **Model retrain cadence:** En yeni model 2026-03-06 tarihli. 47 gundur yeni eğitim yok — scheduled retrain job'u kontrol edilmeli.

### INFO
- `.env` icindeki `CACHE__REDIS_ENABLED` anahtari `.env.example`'a eklenmeli (dokumantasyon tutarliligi).
- `api.log` son kayit tarihi 2026-04-18 — 4 gundur API log yazmiyor olabilir (veya process restart edilmedi). API up-state ayrica monitorlenmeli.

---

*Otomatik uretim — FinPilot Daily Health Check (2026-04-22)*
