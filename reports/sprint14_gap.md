# Sprint 14 — Gap Report
## Tamamlanan İşler

### 1. `scanner/finpilot_score.py` — Thread-safe weight management
- `get_weights()`, `set_weights()`, `load_weights()` eklendi (`threading.Lock()` ile)
- `core/calibration.py` S13 rollback kodu artık düzgün çalışıyor (`set_weights` import hatası giderildi)

### 2. `core/calibration.py` — KS-test drift detection (`detect_drift()`)
- Son 50 skoru önceki 200 skor referansı ile karşılaştırır (`scipy.stats.ks_2samp`)
- p-value < 0.05 → `refit_with_gate()` tetiklenir + Telegram uyarısı
- `scipy` yoksa sessizce geçer (`reason: "scipy_unavailable"`)

### 3. `core/scheduler.py` — 4 yeni APScheduler jobı
| Job | Zamanlama | Amaç |
|-----|-----------|-------|
| `finpilot_drift_job` | Her 6 saatte bir | KS-test drift tespiti |
| `finpilot_ceo_report_job` | Pazar 08:00 UTC | CEO haftalık Telegram raporu |
| `finpilot_auto_approve_job` | Her 30 dakikada bir | p_win ≥ 0.65 + sistem normal → auto-approve |
| (sprint 12) `finpilot_research_pipeline_job` | Pazar 02:00 UTC | Walk-forward + Optuna + champion/challenger |

### 4. CEO Telegram raporu içeriği
- Kalibrasyon: Brier 7g/30g trend, ECE
- Model kaydı: şampiyon adı/Brier/WR, challenger sayısı
- KPI özeti: win rate, profit factor, toplam sinyal, decile lift

### 5. Auto-approve mantığı
- `is_degraded()` → True ise sistem geçer
- Her bekleyen sinyal için `calibrated_probability(score) >= 0.65` kontrolü
- Otomatik onaylanan sinyaller `auto_approved=True`, `auto_approve_p_win=X.XXXX` ile işaretlenir

## Eksikler / Sonraki Sprint

| Konu | Durum | Not |
|------|-------|-----|
| `_load_all_signals()` in kpi_tracker | Var | `update_signal_outcome` dışa aktarılmış |
| `scipy` container kurulumu | ⚠️ | Drift detection scipy gerektirir; requirements.txt'e ekle |
| `optuna` container kurulumu | ⚠️ | Sweep job optuna gerektirir; requirements.txt'e ekle |
| Auto-approve kalıcı yazma | ❌ | Şu an sinyal dict'ini in-memory değiştiriyor; kalıcı persist gerekir |
| CEO raporu "top signals" | ❌ | get_kpis() sinyallerin adlarını döndürmüyor; ileriki sprintte detaylandır |
| Weekly Optuna mini-sweep job | ❌ | research/pipeline.py içinde `run_research_pipeline()` var; Pazar 03:00 UTC için ayrı mini-sweep jobı eklenebilir |

## Sonraki Sprint (S15) Önerisi
- `requirements.txt`'e `scipy`, `optuna`, `lightgbm` ekle
- Auto-approve kalıcı persist (JSON/SQLite)
- LightGBM Layer 2 ranker PoC
- Per-regime weight set (3 regime × 10 weight)
