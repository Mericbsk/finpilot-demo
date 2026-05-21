# Sprint 8 — Gap Report
_Tarih: 2026-05-21_

## Tamamlanan

- [x] **DRL weight zeroed** — `scanner/finpilot_score.py`: `_W_DRL = 0.0`, `_W_SCANNER = 1.0`
  - Kanıt: `grep "_W_DRL" scanner/finpilot_score.py` → `_W_DRL = 0.0`
  - DRL artık skoru etkilemiyor; stale cache'den gelen 0.5 confidence noise gitti
- [x] **R/R fix** — `core/scheduler.py` L380–394:
  - `record_signal` artık `entry_price <= 0` ve `direction != "BUY"` kontrol SONRASINDA çağrılıyor
  - R/R formülü: `max_return / abs(max_drawdown)` sıfır bölme güvenliği + `_max_dd > 0` guard
- [x] **Per-job watchdog** — `core/scheduler.py`: `_make_watchdog_job()` tüm APScheduler job'larına sarıldı
  - Timeout: 600 saniye; hang durumunda Telegram alert
- [x] **Calibration cron fix** — günde 1 kez saat 23:30 UTC (NASDAQ kapanış sonrası), IntervalTrigger(hours=24) → CronTrigger
- [x] **Sentry docs** — `.env.example`'a SENTRY_DSN, SENTRY_ENVIRONMENT, SENTRY_RELEASE eklendi
  - Sentry kodu zaten `core/monitoring.py` ve `api/main.py`'de mevcut ve çalışır durumda

## Yarım Kalan / Manuel Gereken

- [ ] **SENTRY_DSN yapılandırması**: Gerçek DSN'i `.env` dosyasına eklemek kullanıcı işlemi
  - https://sentry.io → free account → project → DSN kopyala
- [ ] **Cherry-pick (reflog commit'leri)**: Git reflog'da 4 commit var (`964d4ec` R/R, `9e491ec` kalibrasyon)
  - Bu sprint'te doğrudan fix uygulandı; cherry-pick'e gerek kalmadı

## Beklenmeyen Bulgular

- Sentry zaten tam entegre: `monitoring.py` SentryClient + `api/main.py` lifespan init — sadece DSN eksikti
- `record_signal` price/direction gate bug: doğrulandı ve düzeltildi
- APScheduler calibration job IntervalTrigger(hours=24) idi → saat 23:30'a sabitlendi

## Sprint 9'a Taşınanlar

- Outcome reconciler T+5 ve T+20 horizon desteği
- `compute_decile_lift()` fonksiyonu (`core/kpi_tracker.py`)
- Live P&L tile (dashboard)

## Metrik Kontrolleri

| Metrik | Önceki | Şimdi |
|--------|--------|-------|
| DRL weight | 0.40 | **0.00** |
| Skor formülü | 0.6·scanner + 0.4·DRL·agreement | **1.0·scanner** |
| R/R hesabı | ZeroDivisionError riski, SELL sinyaller kaydediliyordu | Güvenli, sadece BUY |
| Calibration job | Her 24 saatte bir (keyfi saat) | **Her gün 23:30 UTC** |
| Watchdog | Yok | **600s timeout + Telegram alert** |
