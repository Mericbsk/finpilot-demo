# Sprint 9 — Gap Report
_Tarih: 2026-05-21_

## Tamamlanan

- [x] **compute_decile_lift()** — `core/kpi_tracker.py`'a eklendi
  - `n_deciles=10` (default), sinyalleri score'a göre sıralar → win rate per bucket
  - Doğrulama: top decile lift=2.22×, bottom=0.0 (20 sinyallik test verisi)
  - Gelecekte: calibration dashboard tile ve champion/challenger karşılaştırması için kullanılacak

- [x] **Multi-horizon reconciler (T+1/T+5/T+20)** — `core/outcome_reconciler.py` tamamen yeniden yazıldı
  - `HORIZONS = [("t1",1,24), ("t5",5,120), ("t20",20,480)]`
  - T+1 → birincil KPI metrikleri (win_rate, profit_factor) — `record_outcome()` çağrısı
  - T+5/T+20 → sinyale `outcome_t5`, `outcome_t20` alanları eklenir (kalibrasyon için)
  - `reconcile_all_horizons()` → tek çağrıda 3 horizon; scheduler bunu kullanıyor
  - Doğrulama: boş signal store ile crash etmiyor; keys=['t1','t5','t20'] ✓

- [x] **Scheduler güncellendi** — `core/scheduler.py`
  - `_run_reconcile_job()` artık `reconcile_all_horizons()` kullanıyor (eski: `reconcile_open_signals()`)

## Beklenmeyen Bulgular

- HOLD_DAYS önceden 5 idi (T+5), ama birincil horizon T+1 olmalıydı (günlük close en hızlı KPI kapanışı)
  - Düzeltildi: T+1 artık primary horizon
- T+5/T+20 sinyal üzerinde ayrı field olarak saklanıyor, `record_outcome` kirletilmiyor

## Sprint 10'a Taşınanlar

- APScheduler günlük refit_with_gate job kontrolü (CronTrigger 23:30 UTC)
- research/ klasörü iskelet: sweep.py, walkforward.py, registry.py
- Live P&L dashboard tile

## Metrik Kontrolleri

| Özellik | Önceki | Şimdi |
|---------|--------|-------|
| Reconciler horizons | Tek (T+5) | **T+1 (primary) + T+5 + T+20** |
| Decile lift | Yok | **compute_decile_lift() eklendi** |
| Reconcile job | reconcile_open_signals | **reconcile_all_horizons** |
