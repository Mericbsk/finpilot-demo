# Sprint 10 — Gap Report (Partial — research skeleton complete)
_Tarih: 2026-05-21_

## Tamamlanan

- [x] **research/ klasörü iskelet** — 3 modül oluşturuldu ve doğrulandı
  - `research/__init__.py` — modül tanımı
  - `research/walkforward.py` — WalkForwardCV: 12-fold, 24m train / 6m val, Brier+win_rate per fold
  - `research/sweep.py` — Optuna multi-objective sweep (Brier+PF), `optuna_conservative_results.json` seed desteği
  - `research/registry.py` — Champion/challenger SQLite registry; `auto_promote_best()` ile otomatik promosyon
  - Doğrulama: tüm import'lar ve fonksiyonlar çalışıyor ✓

## Sprint 10'da Kalan (Sıradaki)

- [ ] **Live P&L tile** — dashboard ana ekranına equity curve tile
- [ ] **Slippage + fee modeli** — paper portfolio'ya bağlanacak
- [ ] **/dashboard/calibration sayfası** — Brier + ECE + decile lift tile
- [ ] **Auto-disable** — quality breach durumunda strateji devre dışı bırakma

## Metrik Kontrolleri

| Modül | Özellik | Durum |
|-------|---------|-------|
| research/walkforward.py | 12-fold WF | ✅ |
| research/sweep.py | Optuna multi-obj | ✅ |
| research/registry.py | SQLite champion/challenger | ✅ |
| registry auto_promote | Challenger → Champion | ✅ |
| Seed trial loading | optuna_conservative_results.json | ✅ (graceful fallback) |
