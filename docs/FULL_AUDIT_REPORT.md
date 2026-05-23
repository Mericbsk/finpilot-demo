# FinPilot — Uçtan Uca Repo Denetimi

**Tarih:** 2026-05-23
**Denetçi:** Claude Opus 4.7
**Kapsam:** Tüm repo — frontend, backend, ML/DRL, altyapı, testler, scriptler, döküman
**Yöntem:** Statik analiz + import tarama + LOC sayımı + canlı audit çıktısı + paralel ajan keşfi
**Önceki rapor:** `docs/audits/2026-04-16/` (bu rapor onu supersede eder)

---

## İçindekiler

1. Yönetici Özeti
2. Tam Dosya Sistemi Haritası
3. Klasör ve Dosya Bazlı Analiz
4. Çalışan / Çalışmayan / Gereksiz Tablosu
5. Modül Bağlantı Haritası
6. Tekrar ve Redundancy Bulguları
7. Darboğaz ve Yavaşlık Analizi
8. Ürün Değeri Sınıflandırması
9. Optimizasyon Tablosu
10. Sadeleştirme Kararları
11. Otonomi Olgunluk Değerlendirmesi
12. Doğru Sorular Çerçevesi
13. Hedef Repo Yapısı
14. Execution Roadmap
15. Son Karar

---

## 1) YÖNETİCİ ÖZETİ

**Genel durum:** Repo çok katmanlı ve büyük (1.6 GB toplam, ~21K LOC çekirdek `core/`, 20 router, 19 agent, 54 script, 70 test, 3 farklı frontend katmanı). Profit Core'un audit'i 2026-05-23'te **NO EDGE / ters skor (decile_lift=0.728, p=0.995)** verdi — yani ürün, feature'lardan değil **ölçüm + sadeleştirme**den yararlanacak durumda.

**En kritik bulgular:**
1. Skor pipeline'ı 3 katlı (`signals.signal_score_row` → `score_engine.compute_recommendation_score` → `finpilot_score.compute_finpilot_score`). `score_engine.py` ve `risk_engine.py` üretimde **hiç çağrılmıyor**.
2. 3 farklı frontend birlikte yaşıyor (`web/` Next.js — gerçek ürün; `views/` sadece `.pyc` — ölü; `public_website/` Ocak'tan beri kıpırdamamış — marketing fosili).
3. `web/` 1.6 GB — node_modules 918 MB.
4. DRL katmanı 8 hafta+ donmuş. `models/best/best_model.zip` Şubat 26'dan beri güncellenmemiş, 17 PPO klasörü çürüyor.
5. 20 router'dan 13'ü test'siz (agent, advisory, scan, trade dahil).
6. 32 script ölü (Şubat–Mart, Makefile'da yok).
7. Audit raporu duplikasyonu: `data/profitcore_audit.json`, `docs/audits/2026-04-16/`, `reports/audit_2026.md`, bu dosya — hangisi otoriter belli değil.
8. `core/`'da 9 orphan modül (621 LOC `exceptions.py`, 682 LOC `i18n.py`, 788 LOC `social.py`, 824 LOC `websocket_feeds.py` — kimse import etmiyor) → ~5K LOC ölü kütle.

**Doğru sadeleştirme yönü:** Önce ölç → orphan modülleri arşivle → 3 skor fonksiyonunu 1'e indir → 3 frontend'i 1'e indir → DRL'yi dondur → docs/site/ tek kaynak yap.

---

## 2) TAM DOSYA SİSTEMİ HARİTASI

| Yol | Tür | Amaç | Kritik? | Aktif? | Not |
|---|---|---|---|---|---|
| `core/` (35 dosya, ~13K LOC, 1.6M) | Çekirdek | Skor, KPI, kalibrasyon, scheduler | ✓ | Kısmen | 9 dosya orphan |
| `scanner/` (11 dosya, ~2.7K LOC) | Sinyal | Tarama + skor | ✓ | Evet | 3 paralel skor fn |
| `drl/` (35 dosya, ~10K LOC, 1.4M) | RL | Specialist ensemble | ⚠ | Dondu | 8+ hafta dokunulmadı |
| `api/` (29 dosya, 612K) | FastAPI | 20 router | ✓ | Evet | 13 router test'siz |
| `agents/` (19 dosya, 360K) | LLM agent | Advisory, CEO, research | ✓ | Evet | Tümü çağrılıyor |
| `web/` (1.6 GB) | Next.js 16 | Gerçek ürün UI | ✓ | Evet | node_modules 918M |
| `views/` (1.3M) | Streamlit | Sadece .pyc | ✗ | Ölü | Source silinmiş |
| `public_website/` (104K) | Statik HTML | Marketing | ⚠ | Dormant | Ocak'tan beri sabit |
| `tests/` (70 dosya, 4.2M) | Pytest | 664 test, 4 known fail | ✓ | Evet | Coverage düşük |
| `scripts/` (54 dosya, 952K) | CLI util | Audit, train, paper | ⚠ | %30 aktif | 32 ölü |
| `docs/` (1.3M, 35 MD) | Markdown | Roadmap, ADR, runbook | ⚠ | Kısmen | Tekrarlı dosyalar |
| `site/` (7.6M) | mkdocs build | Statik doc | ⚠ | 18g eski | Build artifact |
| `models/` (25M, 18 PPO) | RL weights | Eğitilmiş model | ⚠ | Stale | `best/` Şubat'tan sabit |
| `logs/` (2.8M) | Run logları | tensorboard, paper, eval | ⚠ | Kısmen | tensorboard Şubat |
| `data/` (17M) | Sinyal/ticker | signal_archive, db, tickers | ✓ | Evet | 51 JSON, db 308K |
| `reports/` (12M) | Backtest çıktısı | Markdown rapor | ⚠ | Kısmen | Eski |
| `monitoring/` (35K) | Grafana | Dashboard JSON | ⚠ | Belirsiz | Çalışıyor mu? |
| `migrations/` (49K) | Alembic | DB versiyon | ✓ | Evet | 5 dosya |
| `auth/` (524K) | JWT | Login, RBAC | ✓ | Evet | Tests var |
| `llm/` (184K) | LLM client | OpenAI/Ollama wrap | ✓ | Evet | |
| `broker/` (52K) | Order/exec | Tek dosya | ⚠ | Stub | İskelet |
| `research/` (90K) | Notebook/exp | Ad-hoc | ⚠ | Manuel | |
| `grant_documents/` (4.2M) | PDF/HTML | NVIDIA pitch, AWS fund | ⚠ | İş kritik | Yanlış yerde |
| Root `telegram_*.py` (3 dosya) | Bildirim | TG bot/alert | ⚠ | Bilinmiyor | Test yok |
| `output.log`, `.docker_build.log` | Log | Generated | ✗ | Sil | Repo'ya commit olmamalı |
| `site/` | Build | mkdocs çıktısı | ✗ | Sil | gitignore |

---

## 3) KLASÖR VE DOSYA BAZLI ANALİZ

| Bileşen | Amaç | Kullanım | Risk | Karar |
|---|---|---|---|---|
| `core/scheduler.py` (1191) | APScheduler döngüsü | 4h önce dokunuldu | Yüksek — tek nokta | SIMPLIFY (paket) |
| `core/monitoring.py` (1212) | Health + watchdog | Aktif | Şişti | SIMPLIFY (paket) |
| `core/calibration.py` (599) | Isotonic kalibre | api/closed_loop | Düşük | KEEP |
| `core/cache.py` (828) | Redis + LRU + Streamlit | Streamlit kalmadı | Orta | SIMPLIFY (streamlit sil) |
| `core/exceptions.py` (621) | Custom exc | **0 import** | — | ARCHIVE |
| `core/i18n.py` (682) | Çeviri | **0 import** | — | ARCHIVE |
| `core/social.py` (788) | Sosyal sentiment | **0 import** | — | ARCHIVE |
| `core/plugins.py` (719) | Plugin sistemi | **0 import** | — | ARCHIVE |
| `core/websocket_feeds.py` (824) | Live feed | Monitor-only | — | FREEZE |
| `core/session_state.py` | Streamlit session | Streamlit ölü | — | REMOVE |
| `core/logging.py` | Log config | Orphan | — | MERGE (config'e) |
| `core/validation.py` | Validate util | Orphan | — | ARCHIVE |
| `core/tracing.py` | OTel | Orphan | — | FREEZE |
| `scanner/score_engine.py` (60) | Reco score | Üretimde çağrılmıyor | — | MERGE → finpilot_score |
| `scanner/risk_engine.py` (61) | Risk yönetimi | Çağrılmıyor | — | MERGE → evaluate |
| `scanner/features.py` (124) | Volatility/RS | Pipeline'da yok | — | WIRE veya REMOVE |
| `scanner/earnings_blackout.py` (116) | Earnings block | Çağrılmıyor | — | REMOVE |
| `scanner/finpilot_score.py` | Ana skor | api/scan ✓ | Yüksek | KEEP — Ana yer |
| `drl/inference.py` (707) | DRL inference | 4d önce, ama _W_DRL=0 | — | FREEZE (bağlı değil) |
| `drl/backtest_engine.py` (1038) | Vektörel BT | 8w stale | — | FREEZE |
| `drl/ensemble_router.py` (808) | Specialist router | 8w stale | — | FREEZE |
| `drl/specialists.py` (713) | Specialist policies | 8w stale | — | FREEZE |
| `drl/report_generator.py` (754) | DRL rapor | 3mo stale | — | ARCHIVE |
| `views/` (sadece pyc) | Streamlit UI | Source yok | — | REMOVE |
| `scripts/*.bak` | Bozuk yedek | — | — | REMOVE |
| `scripts/drl_autopilot_patched.py` | "patched" duplicate | — | — | MERGE orijinaline |
| `output.log`, `.docker_build.log` | Log dosyaları | — | — | REMOVE + gitignore |
| `models/best/best_model.zip` | "Best" model | Şubat'tan sabit | Yüksek (yanıltıcı) | Pointer ekle |
| `models/ppo_*` (17 klasör) | Eski training | Hiçbiri "best" değil | Disk | PRUNE — 3 en yeni hariç |

---

## 4) ÇALIŞAN / ÇALIŞMAYAN / GEREKSİZ TABLOSU

| Bileşen | Durum | Kanıt | Etki | Karar |
|---|---|---|---|---|
| `web/` Next.js | Çalışıyor | `/py-api/` proxy aktif, 24 page | Yüksek | KEEP |
| `views/` Streamlit | Ölü | Sadece `__pycache__` | — | REMOVE |
| `public_website/` | Dormant | Last touch 2025-01-27 | Düşük | MOVE ayrı repo |
| `api/main.py` + 20 router | Çalışıyor | Tüm router import ediliyor | Yüksek | KEEP |
| `scanner/finpilot_score` | Çalışıyor (ters!) | Audit: decile_lift=0.728 | Yüksek | KEEP + FIX |
| `scanner/score_engine` | Kopuk | Çağrılmıyor | — | MERGE |
| `scanner/risk_engine` | Kopuk | Hiç çağrılmıyor | — | MERGE/REMOVE |
| `scanner/features` | Kopuk | Pipeline'da yok | — | WIRE veya REMOVE |
| `scanner/earnings_blackout` | Kopuk | — | — | REMOVE |
| `core/{exceptions, i18n, social, plugins, validation, tracing, session_state}` | Orphan | 0 import | — | ARCHIVE (~5K LOC) |
| `core/websocket_feeds` | Yarı | Sadece monitor | — | FREEZE |
| `core/calibration` | Çalışıyor | closed_loop kullanır | Yüksek | KEEP |
| `core/kpi_tracker` | Çalışıyor | Outcome storage | Yüksek | KEEP |
| `core/outcome_reconciler` | Çalışıyor | Multi-horizon t1/t5/t20 | Yüksek | KEEP |
| `core/scheduler` | Çalışıyor | 4h önce edit | Yüksek | SIMPLIFY |
| `drl/inference` | Bağlı değil | _W_DRL=0 | Düşük | FREEZE |
| `drl/{backtest,specialists,ensemble}` | Donmuş | 8w stale | — | FREEZE |
| `agents/*` (16 agent) | Çalışıyor | api/agent.py orchestrator | Yüksek | KEEP |
| `scripts/profitcore_audit` | Çalışıyor | Bugün üretildi | Yüksek | KEEP + COMMIT |
| `scripts/{smoke,docker_smoke,safe_commit}` | Çalışıyor | Makefile | Yüksek | KEEP |
| `scripts/*.bak` | Bozuk | — | — | REMOVE |
| `scripts/drl_autopilot_patched` | Duplicate | — | — | MERGE |
| Scripts 32 stale | Ölü | Şub-Mar, Makefile'da yok | — | ARCHIVE |
| `tests/` 664 test | Kısmen | 4 known fail (PRE_EXISTING) | Yüksek | KEEP |
| `models/best/best_model.zip` | Eski | Şubat sabit | Yüksek (yanıltıcı) | REPLACE veya pointer |
| `models/ppo_*` 17 klasör | Stale | Şubat-Mart | Disk | PRUNE → 3 |
| `logs/tensorboard/PPO_*` | Stale | Şubat | — | ARCHIVE |
| `monitoring/grafana` | Belirsiz | Çalışıyor mu? | Orta | DOĞRULA |
| `output.log`, `.docker_build.log`, `.coverage` | Çöp | Generated | — | REMOVE + gitignore |
| `broker/` | Stub | İskelet | Düşük | KEEP (planlı) |
| `telegram_*.py` (root) | Bilinmiyor | Test yok | Orta | DOĞRULA → `core/notifier/` |

---

## 5) MODÜL BAĞLANTI HARİTASI

**Üretim veri akışı:**
```
data/tickers + yfinance
   → scanner.data_fetcher.fetch()           [sync I/O, Redis+LRU cache]
   → scanner.indicators.add_indicators()
   → scanner.signals.evaluate_symbols_parallel()
        ├→ signals.signal_score_row()        (skor-1: gözlem)
        ├→ finpilot_score.compute_finpilot_score()  (skor-2: ANA, _W_DRL=0)
        │     └→ score_engine.compute_recommendation_score()  (skor-3: reco)
        ├→ scanner.evaluate.evaluate_symbol()
        └→ core.kpi_tracker.record_signal()
   → data/signal_archive/*.json
   → core.outcome_reconciler  [HORIZONS: t1, t5, t20]
   → core.kpi_tracker.update_outcome()
   → core.calibration (isotonic)
   → api/routers/* → web/py-api/* (Next.js proxy)
```

**Kontrol akışı:**
```
core.scheduler (APScheduler)
   ├→ agents/scanner_agent
   ├→ agents/market_intelligence
   ├→ agents/backtest_agent
   ├→ agents/performance_monitor
   ├→ agents/data_quality
   ├→ agents/strategy_optimizer
   ├→ agents/report_agent
   └→ agents/advisory
```

**Kopuk noktalar:**
1. `drl/inference.py` → `scanner/finpilot_score.py` (**_W_DRL=0, fiilen kopuk**)
2. `scanner/{features, risk_engine, earnings_blackout}` → **kimse import etmiyor**
3. `scanner/score_engine.py` → runtime'da çağrılmıyor (`finpilot_score` ayrı formül)
4. `core/websocket_feeds.py` → sadece monitor referansı, üretim dışı
5. `views/` → sadece pyc, source yok
6. `telegram_*.py` (root) → scheduler/api'den import izi doğrulanmadı
7. `models/best/best_model.zip` → kim yükler, ne zaman güncellenir belli değil
8. AlphaTracker `weighted_score` → dashboard arasındaki bağlantı eksik (plan item 5)

---

## 6) TEKRAR VE REDUNDANCY BULGULARI

| Tekrar alanı | Sorun | Öneri |
|---|---|---|
| 3 skor fonksiyonu | Otorite belirsiz, audit ters çıktı | Tek fn: `finpilot_score`. Diğerleri merge/remove. |
| 3 frontend | Tek ürün, 3 fosil | `web/` = ürün. `views/` REMOVE. `public_website/` → marketing repo. |
| 2 evolution timeline | Aynı doküman | `_OLD.md` sil. |
| 2 professional analysis | Versiyon karmaşası | Tek dosya + git history. |
| 2 project analysis | Aynı sunum | Tek dosya. |
| 4 audit artifact | Otoriter belirsiz | `docs/audits/YYYY-MM-DD/` standardı. Bu dosya tek otoriter. |
| 2 drl_autopilot | "patched" merge edilmemiş | Merge + sil. |
| 2 regime detector | İsim benzer, kapsam farklı | Net naming: `market_regime` vs `volatility_regime`. |
| Çoklu launcher | bat, sh, fp, Makefile | Tek Makefile + `fp` wrapper. |
| `site/` + `docs/` | Build artifact commit'lenmiş | `site/` → gitignore, CI'da üret. |
| `reports/` + `data/daily_reports/` | İki rapor dizini | Tek: `data/daily_reports/` runtime, `reports/` arşiv. |

---

## 7) DARBOĞAZ VE YAVAŞLIK ANALİZİ

| Alan | Neden yavaş | Etki | Çözüm |
|---|---|---|---|
| `scanner/data_fetcher.py` (733) | `yf.download()` blocking, ThreadPool var ama fetch'te kullanılmıyor | Tarama süresi | Fetch'i ThreadPool'a al |
| `core/cache.py` (828) | Redis + LRU + Streamlit 3 katmanlı | Cache miss debug zor | Streamlit kolunu sil |
| `core/scheduler.py` (1191) | 8+ agent job tek dosyada | Bakım zor | `core/jobs/*.py` modülleri |
| `core/monitoring.py` (1212) | Health + watchdog + prom export birlikte | Şişme | `monitoring/` paketi |
| Skor pipeline | 3 fonksiyon ardışık | Mikro yavaşlık + okuma yükü | 1 fonksiyon |
| `web/` build | 918 MB node_modules | Docker image şişer | Multi-stage + standalone |
| Test | 664 test, seri | CI süresi | pytest-xdist + markers |
| `data/signal_archive/*.json` (51 dosya) | Her gün JSON + audit okur | Disk + parse | SQLite tek tablo |
| `models/` 25M, 17 PPO | Çoğu eski | Disk | 3 en yeni, gerisi archive |
| `core/audit.py` + `audit_log.py` + `data/logs/audit/` + `docs/audits/` | 4 yerde audit | Karışıklık | Tek pipeline |

---

## 8) ÜRÜN DEĞERİ SINIFLANDIRMASI

| Bileşen | Ürün değeri | Bakım yükü | Karar |
|---|---|---|---|
| `scanner/` + `core/kpi_tracker` + `calibration` + `outcome_reconciler` | **Core product** | Orta | KEEP — sadeleştir |
| `web/dashboard` | **Core product** | Orta | KEEP |
| `api/routers/{scan, watchlist, history, closed_loop, advisory, agent}` | **Core product** | Düşük | KEEP |
| `agents/{alpha_tracker, advisory, scanner_agent, performance_monitor}` | Important support | Orta | KEEP |
| `core/scheduler` | Important support | Yüksek (1191 LOC) | SIMPLIFY |
| `auth/` + JWT | Important support | Düşük | KEEP |
| `core/monitoring` + `prometheus_exporter` | Important support | Orta | SIMPLIFY |
| `drl/` katmanı | **Premature complexity** (_W_DRL=0) | Yüksek (10K LOC) | FREEZE → `experimental/drl/` |
| `core/{social, i18n, plugins, exceptions, validation, tracing, session_state}` | **Yok** | Yüksek (~5K LOC orphan) | ARCHIVE |
| `views/` Streamlit | Yok (ölü) | — | REMOVE |
| `public_website/` marketing | Pazarlama | Düşük | MOVE |
| `grant_documents/` (NVIDIA, AWS) | İş kritik | Düşük | KEEP → `business/` |
| `docs/` tekrarlı pitch | Düşük (tekrar) | Düşük | MERGE |
| `models/` 17 PPO | Düşük (kullanılmıyor) | Disk | PRUNE → 3 |
| `scripts/` 32 stale | Yok | Orta | ARCHIVE |
| `site/` mkdocs build | Düşük (CI üretir) | — | REMOVE + gitignore |
| `broker/` stub | Nice-to-have | Düşük | KEEP |
| `telegram_*.py` (root) | Bilinmiyor | Belirsiz | DOĞRULA → `core/notifier/` |

---

## 9) OPTİMİZASYON TABLOSU

| Bileşen | Optimize alan | Beklenen fayda | Ölçüm | Efor | Öncelik |
|---|---|---|---|---|---|
| `scanner/finpilot_score` | Component ablasyonu | Decile lift 0.728 → ≥1.3 | `profitcore_audit.py` | 1g | P0 |
| Skor pipeline | 3→1 fonksiyon | Okunabilirlik | LOC -120 | 2s | P0 |
| `views/` REMOVE | Ölü kod | Repo temizliği | klasör boyutu | 5dk | P0 |
| Root çöpü REMOVE | output.log, .docker_build.log | Repo kirlilik | dosya sayısı | 5dk | P0 |
| `core/` orphan arşiv | ~5K LOC | Bakım yükü | LOC | 30dk | P1 |
| `drl/` → `experimental/` | Sahiplik netleşmesi | Konsept netliği | klasör | 1s | P1 |
| `models/` prune | -20M disk | Disk + Docker | du -sh | 30dk | P1 |
| Duplicate docs merge | Karışıklık | Okunabilirlik | dosya sayısı | 1s | P1 |
| `site/` gitignore | Build artifact | Repo boyutu | git size | 1s | P1 |
| `core/scheduler` paketi | 1191→400 main | Bakım | LOC | 1g | P2 |
| `core/monitoring` paketi | 1212→400 main | Bakım | LOC | 1g | P2 |
| `core/cache` streamlit sil | LOC -200 | Bakım | LOC | 1s | P2 |
| `data_fetcher` ThreadPool | Tarama süresi -%40 | Benchmark | süre | 1g | P2 |
| `signal_archive` JSON→SQLite | I/O + audit hızı | Audit run | süre | 3s | P2 |
| Test pytest-xdist | CI -%60 | CI süresi | dakika | 1s | P2 |
| Web multi-stage Docker | 1.6G → ~300M | Docker build | image boyutu | 4s | P2 |
| `models/best/` pointer | Yanlış model riski | Güvenilirlik | dosya | 2s | P2 |
| Audit cron + Grafana | L3 olgunluk | Otomasyon | dashboard | 1g | P2 |
| AlphaTracker → dashboard | Plan item 5 | Özellik tamamlama | UI | 2s | P2 |
| Component ablation script | Hangi feature kötü | Edge bulma | decile lift | 1g | P1 |

---

## 10) SADELEŞTİRME KARARLARI

| Karar | Bileşen | Gerekçe |
|---|---|---|
| KEEP | `scanner/finpilot_score`, `core/{kpi_tracker, calibration, outcome_reconciler, scheduler, config, database}`, `api/routers/*`, `agents/*`, `web/`, `tests/`, `auth/` | Core product zinciri |
| SIMPLIFY | `core/scheduler` (modülerleş), `core/monitoring` (paketle), `core/cache` (streamlit sil) | Şişti, bakım zor |
| MERGE | `score_engine`+`risk_engine`+`features` → `finpilot_score`/`evaluate`; duplicate docs | Duplikasyon |
| FREEZE | `drl/` → `experimental/drl/`; `core/websocket_feeds`; `models/ppo_*` (3 hariç) | Şu an kullanılmıyor |
| ARCHIVE | `core/{exceptions, i18n, social, plugins, validation, tracing, session_state}`; 32 stale script; `logs/tensorboard`; eski docs | Orphan / çürük |
| REMOVE | `views/`, `output.log`, `.docker_build.log`, `scripts/*.bak`, `scanner/earnings_blackout`, `site/`; `public_website/` → ayrı repo | Ölü / yük |

---

## 11) OTONOMİ OLGUNLUK DEĞERLENDİRMESİ

| Seviye | Tanım | Durumuz | Eksik |
|---|---|---|---|
| 0 | Manuel, dağınık | — | — |
| 1 | Temel otomasyon (scheduler var) | ✓ geçildi | — |
| **2** | **Modüler ama kopuk** | **← BURDAYIZ** | DRL kopuk, 3 skor fn, orphan modüller, audit kapalı döngü değil |
| 3 | Ölçülen + kontrollü | Hedef | Decile lift sürekli ölçüm, calibration cron, ablation, regression gate |
| 4 | Kontrollü self-improving | Sonraki | Online feedback → weight güncelleme, regime-aware, drift detection |
| 5 | Denetimli düşük-müdahale | İlerisi | Self-tuning + insan onayı + rollback |

**L3'e geçmek için:**
1. `profitcore_audit` haftalık cron + Grafana panel
2. Component ablation tablosu
3. Score regression gate (lift <1.2 → deploy blok)
4. Calibration auto-retrain (MAE>0.10)
5. Feature distribution drift (PSI)

---

## 12) DOĞRU SORULAR ÇERÇEVESİ

### scanner/
**Tanı:** Hangi component decile inversiyonunu sürüklüyor? `signal_score_row` ile `finpilot_score` aynı sıralamayı üretiyor mu? `risk_engine` neden bağlı değil?
**Optimize:** `data_fetcher` ThreadPool kazanımı ne? Indicator hesaplama cacheable mi?
**Evrim:** Regime-aware scoring, self-calibrating eşik, feature importance feedback loop.

### core/
**Tanı:** Orphan modüllerin geçmişi neden var? `scheduler` watchdog gerçek timeout'ta job kill ediyor mu? `calibration` MAE'si şu an ne?
**Optimize:** `monitoring.py` 1212 LOC parçalama; `cache.py` streamlit kolu.
**Evrim:** `plugins.py` gerçekten lazım mı yoksa premature?

### drl/
**Tanı:** `inference.py` 4d önce fresh — neden, `_W_DRL=0` iken? `models/best` kim güncellemeli? Specialist ensemble bir signal'a ne ekliyor?
**Optimize:** Şu an kullanılmıyor → önce edge kanıtla.
**Evrim:** DRL'i geri açmadan önce skor edge'i kanıtlanmalı.

### api/
**Tanı:** 13 router niçin test'siz? `/loop/*` endpoint'leri outcome güncelliyor mu? `agent` router hata toleransı?
**Optimize:** Auth middleware tek dependency'ye çek.
**Evrim:** OpenAPI versiyonlama, rate limiting per-user.

### agents/
**Tanı:** `alpha_tracker.weighted_score` nereye yazılıyor? `ceo.py` API'ye gerek var mı? `feedback.py` feedback nereye depoluyor?
**Optimize:** Agent'ların ortak LLM client pool'u.
**Evrim:** Agent karar tracing (her advisory → kanıt zinciri).

### web/
**Tanı:** `/py-api/` proxy'de ölü endpoint var mı? Dashboard `agent-hub` 16 agent'ı görüyor mu? 918M'dan kaç paket üründe?
**Optimize:** Multi-stage Dockerfile, standalone output.
**Evrim:** Real-time WebSocket, PWA offline.

### scripts/
**Tanı:** Son 30 günde hangi script'ler çalıştı? Kim tetikliyor (cron yok)?
**Optimize:** `fp` CLI altında subcommand; 32 stale arşivle.
**Evrim:** Script'ler → API endpoint (audit, retrain).

### tests/
**Tanı:** 4 known fail neden çözülmedi? Coverage gerçek %?
**Optimize:** pytest-xdist, marker-based selection.
**Evrim:** Property-based testing skor fn için, snapshot test'ler.

### data/
**Tanı:** `signal_archive` 51 JSON — neden DB'ye yazılmıyor? `daily_reports/` vs `reports/` farkı?
**Optimize:** JSON → SQLite.
**Evrim:** S3/blob soğuk arşiv.

### docs/
**Tanı:** 35 MD'den kaç tanesi son 60 günde güncellendi?
**Optimize:** Tekrarlı pitch → tek `business/` klasör.
**Evrim:** ADR disiplini — sadece `docs/adr/` yeni karar.

---

## 13) HEDEF REPO YAPISI

```
finpilot/
├── core/                    # 13K → 8K LOC (orphan'lar arşivlendi)
│   ├── kpi_tracker.py
│   ├── calibration.py
│   ├── outcome_reconciler.py
│   ├── config.py
│   ├── database.py
│   ├── cache.py             # streamlit kolu silindi
│   ├── monitoring/          # eski monitoring.py paketlendi
│   │   ├── health.py
│   │   ├── watchdog.py
│   │   └── prometheus.py
│   ├── scheduler/           # eski scheduler.py paketlendi
│   │   ├── runtime.py
│   │   └── jobs/
│   └── notifier/            # telegram_*.py buraya
├── scanner/                 # 11 → 6 dosya
│   ├── data_fetcher.py
│   ├── indicators.py
│   ├── signals.py
│   ├── evaluate.py
│   ├── finpilot_score.py    # TEK skor fonksiyonu
│   └── config.py
├── agents/
├── api/
├── auth/
├── llm/
├── broker/
├── web/                     # node_modules gitignore
├── data/
│   ├── signal_archive.db    # JSON yerine SQLite
│   ├── tickers/
│   ├── daily_reports/
│   └── audit/
├── tests/
├── scripts/                 # 54 → 12 (Makefile'dan çağrılanlar)
│   ├── profitcore_audit.py
│   ├── component_ablation.py
│   ├── smoke_test.py
│   ├── daily_inference.py
│   ├── paper_trading.py
│   ├── weekly_report.py
│   └── docker_smoke.sh
├── docs/
│   ├── adr/
│   ├── runbooks/
│   ├── audits/YYYY-MM-DD/   # tek standart
│   ├── architecture.md
│   └── api/
├── experimental/            # FREEZE alanı
│   ├── drl/                 # eski drl/
│   ├── websocket_feeds.py
│   └── plugins.py
├── archive/                 # checkout edilebilir ama aktif değil
│   ├── core_legacy/
│   ├── scripts_legacy/
│   └── docs_legacy/
├── business/                # eski grant_documents/
│   ├── pitch/
│   └── grants/
├── monitoring/
├── migrations/
├── models/
│   ├── best/                # pointer mekanizması
│   └── current/
├── pyproject.toml
├── Makefile
├── docker-compose.yml
├── Dockerfile
├── README.md
└── fp                       # tek CLI launcher
```

---

## 14) EXECUTION ROADMAP

### Bugün
1. Audit commit: `scripts/profitcore_audit.py` + `data/profitcore_audit.json` + `scanner/score_engine.py`
2. `views/` sil
3. Root çöpü: `output.log`, `.docker_build.log`, `scripts/*.bak`
4. Duplicate docs merge: `EVOLUTION_TIMELINE_OLD.md` sil, `PROFESSIONAL_ANALYSIS_*` birleştir
5. `models/ppo_*` prune: 3 en yeni hariç `archive/models_legacy/`

### Bu hafta
6. Component ablation script (`scripts/component_ablation.py`)
7. `core/` orphan arşivle: `exceptions, i18n, social, plugins, validation, tracing, session_state`
8. `scanner/{score_engine, risk_engine, earnings_blackout}` sil veya merge
9. 3 skor fonksiyonu → 1 (`finpilot_score` kazanır)
10. Agent / advisory / scan / trade router için happy-path test
11. AlphaTracker `weighted_score` → dashboard (plan item 5)
12. `drl/` → `experimental/drl/`
13. `site/` gitignore + remove from git
14. `data/signal_archive/*.json` → SQLite migration
15. `telegram_*.py` → `core/notifier/` taşı + doğrula

### Bu ay
16. `core/scheduler.py` → `core/scheduler/` paketi
17. `core/monitoring.py` → `core/monitoring/` paketi
18. `core/cache.py` streamlit kolu kaldır
19. `scripts/` 54 → 12
20. `models/best/` pointer mekanizması
21. Calibration retrain cron (haftalık, MAE>0.10)
22. `profitcore_audit` Grafana panel
23. `/api/v1/profitcore/metrics` endpoint
24. Component correlation matrix
25. Risk engine portfolio DD gate
26. `outcomes_horizon` SQLite tablo (T+3/T+5/T+10)
27. `public_website/` ayrı repo
28. `fp` CLI subcommand'lar (`fp scan`, `fp audit`, `fp paper`)
29. pytest-xdist + markers
30. Web Docker multi-stage

### 90 gün (L3 olgunluk)
31. Decile lift sürekli ölçüm + regression gate (lift <1.2 → deploy blok)
32. Score v2: ablation sonucuna göre yeniden ağırlıklandırılmış formül
33. DRL geri açma kararı: edge kanıtlanırsa `_W_DRL` tekrar test
34. Calibration drift dashboard + auto-retrain
35. Feature store sadeleştirmesi
36. Self-improving loop: outcome → calibration → weight feedback → audit → score (haftalık döngü)
37. Test coverage hedefi: %70
38. Repo size hedefi: <500 MB
39. Pitch dokümantasyonu konsolide: `business/` tek otoriter
40. ADR disiplini: yeni karar = yeni ADR dosyası

---

## 15) SON KARAR

### En kritik 20 bulgu
1. Skor **ters çalışıyor** (decile_lift=0.728, p=0.995)
2. 3 skor fonksiyonu, otorite yok
3. DRL pipeline kopuk (`_W_DRL=0`)
4. `core/`'da ~5K LOC orphan
5. `views/` sadece pyc — ölü
6. `web/` 1.6 GB (node_modules 918M)
7. `models/best/` Şubat'tan sabit — yanıltıcı
8. 32 script ölü
9. 13 router test'siz (scan, advisory, agent, trade)
10. `site/` build artifact commit'lenmiş
11. Duplicate audit raporları 4 yerde
12. Duplicate pitch/timeline dosyaları
13. `scheduler.py` 1191 LOC tek dosya
14. `monitoring.py` 1212 LOC tek dosya
15. `data_fetcher.py` blocking yfinance
16. `signal_archive/` JSON-only, 51 ayrı dosya
17. `output.log`, `.docker_build.log` commit'te
18. `public_website/` yanlış repo'da
19. Audit cron'da yok (manuel)
20. Component ablation yok

### En gereksiz 20 yük
`views/`, `output.log`, `.docker_build.log`, `scripts/*.bak`, `scanner/earnings_blackout.py`, `core/exceptions.py`, `core/i18n.py`, `core/social.py`, `core/plugins.py`, `core/validation.py`, `core/tracing.py`, `core/session_state.py`, `docs/FINPILOT_EVOLUTION_TIMELINE_OLD.md`, duplicate professional analysis, duplicate project analysis, `site/` (build artifact), `logs/tensorboard/PPO_*` (Şubat), `models/ppo_*` (14 stale), `scripts/drl_autopilot_patched.py`, `core/cache` streamlit kolu

### En değerli 20 korunması gereken
`scanner/finpilot_score.py`, `core/kpi_tracker.py`, `core/calibration.py`, `core/outcome_reconciler.py`, `core/scheduler.py`, `core/database.py`, `api/main.py`, `api/routers/scan.py`, `api/routers/watchlist.py`, `api/routers/history.py`, `api/routers/closed_loop.py`, `api/routers/advisory.py`, `api/routers/agent.py`, `agents/alpha_tracker.py`, `agents/advisory.py`, `agents/scanner_agent.py`, `web/src/app/dashboard/`, `tests/test_score_contract.py`, `scripts/profitcore_audit.py`, `docs/adr/`

### En hızlı etki yaratacak 20 iyileştirme
1. `views/` REMOVE
2. Root çöpü REMOVE
3. Duplicate doc MERGE
4. `models/` PRUNE
5. `core/` orphan ARCHIVE
6. Skor 3→1
7. `site/` gitignore
8. `scripts/*.bak` REMOVE
9. `drl/` → `experimental/`
10. `signal_archive` JSON→SQLite
11. `data_fetcher` ThreadPool fetch
12. `cache.py` streamlit kolu sil
13. Component ablation script
14. Audit cron + Grafana panel
15. 13 router için test
16. AlphaTracker → dashboard
17. `scheduler` modülerleş
18. Web multi-stage Docker
19. `models/best/` pointer
20. `fp` tek CLI

### Doğru sadeleştirme yaklaşımı (3 prensip)
1. **Önce ölç, sonra sil.** Silmeden önce import çağrılarını gör. Orphan kanıtlandıysa `archive/` altına taşı.
2. **Bir kopya bulunca otoriteyi seç, diğerlerini sil.** Skor → `finpilot_score`, Frontend → `web/`, Audit → `docs/audits/YYYY-MM-DD/`.
3. **Şu an kullanılmayan ama yarın lazım olabilecek → `experimental/`.** DRL bunun en net örneği.

**L3 olgunluğa tek geçit:** Decile lift sürekli ölçüm + regression gate + ablation-driven simplification. Yeni feature eklemeden önce mevcut feature'ların kanıtlanması zorunlu.
