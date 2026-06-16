# FinPilot Tam Spektrum Analiz — Bölüm A+B: Sistem Bağlamı ve Dosya Envanteri

**Tarih:** 2026-06-12 · **Analiz:** Claude (Cowork) · **Önceki audit:** `docs/FULL_AUDIT_REPORT.md` (2026-05-23) — bu rapor onun üzerine delta + stratejik genişleme olarak inşa edilmiştir.

---

## SİSTEM BAĞLAMI BLOĞU (Bölüm A — 10 soru)

**1. Repo kök dizini ve genel yapı:** `~/Borsa` — monorepo. Python backend (FastAPI), Next.js frontend (`web/`), DRL katmanı (`drl/`), LLM agent katmanı (`agents/` + `llm/`), eğitim modülü (`academy/` + `FinanceAcademy/`), kapsamlı docs/reports/archive.

**2. Aktif ana servis/modül sayısı:** 7 çalışan servis ekseni: API (FastAPI, 21 router), Web (Next.js 16, port 3001), Scanner pipeline, Scheduler (APScheduler, 10+ job), LLM agent ekosistemi (~19 agent), Telegram bot, Academy (henüz ürüne bağlı değil). Docker tarafında: web, api, finpilot, scanner, telegram_bot, redis, postgres, prometheus, grafana.

**3. docker-compose dosyaları:** Tek dosya — `docker-compose.yml` (8.2K, son değişiklik 2026-06-11). Mayıs audit'indeki çoklu-compose sorunu çözülmüş. Makefile'da `docker-up-legacy` hedefleri hâlâ duruyor (kalıntı).

**4. Env dosyaları:** 2 adet — `.env` (gerçek, 13 anahtar: GROQ, GOOGLE, TELEGRAM, POLYGON, NEWS, ALPACA, MLFLOW, REDIS) ve `.env.example` (şablon). Çift kaynak sorunu yok.

**5. README/GUIDE dosyaları:** `README.md` (2026-05-23, runtime contract dahil — güncel), `FinanceAcademy/README.md` (2026-06-09 — "8 agent" iddia ediyor, kodda 6 var), `docs/` altında 45 MD (çoğu Ocak–Mayıs arası, en az 15'i bayat), `DEPENDENCIES.md` ×2 (root 2026-01-26 + docs/ 2026-04-07 — duplicate).

**6. Aktif yazılan loglar:** `logs/api.log`, `logs/web.log`, `logs/auto_scan_trade.log`, `logs/auto_trade/` (hepsi 2026-06-11 itibarıyla canlı). PID dosyaları start.sh tarafından yönetiliyor.

**7. En son / en eski değişen modüller:** En taze: `api/`, `core/`, `data/`, `scripts/` (2026-06-12); `scanner/`, `llm/`, `web/` (06-11); `agents/` (06-11); `academy/` + `FinanceAcademy/` (06-10). En bayat aktifler: `broker/` (04-22, tek dosya), `monitoring/` (05-23), `models/` (05-23 — DRL ağırlıkları Mart'tan kalma).

**8. Testler:** `tests/` 67 dosya, son baseline: **494 pass / 4 bilinen fail / 10 skip** (`tests/PRE_EXISTING_FAILURES.md`, 2026-05-20). Son toplu çalıştırma izi: 2026-06-01 (`.coverage` 2026-05-23). Pytest markers (unit/integration/slow) + xdist kurulu.

**9. Çalışan ortam:** **Dev/local.** Tek resmi giriş `bash start.sh` (API:8000, Web:3001). Docker compose prod-benzeri stack tanımlı ama canlı prod deployment yok. Paper trading modu aktif (Alpaca paper).

**10. Finance Academy mevcut durumu:** İKİ paralel implementasyon: `academy/` (3.194 LOC, 6 agent + orchestrator + scheduler) ve `FinanceAcademy/` (1.937 LOC, standalone CLI). 12 domain tanımlı, seed içerik var. **Ancak:** `data/academy.db` ve `academy_v2.db` her ikisi 4KB (pratikte boş), API router yok → **ürüne entegre değil, aktif kullanıcı 0.**

---

## KRİTİK BAĞLAM: 23 MAYIS AUDIT'İNDEN BU YANA NE DEĞİŞTİ (43 commit)

Kapatılan eski bulgular:

| Mayıs bulgusu | Durum |
|---|---|
| 3 katlı skor pipeline | ✅ Tek public API'ye indirildi (`finpilot_score` re-export, commit 07c2e83) |
| 3 frontend | ✅ `views/` silindi, `public_website/` arşivlendi → tek frontend: `web/` |
| 9 orphan core modülü | ✅ 5'i arşivlendi (i18n, social, plugins, validation, websocket_feeds) |
| 32 ölü script | ✅ 34 script arşivlendi |
| 17 çürüyen PPO klasörü | ✅ 3 strateji modeline indirildi + `models/best/current.json` |
| Router test eksikliği | ⚠️ Kısmen — happy-path smoke testler eklendi (023a473) |
| Audit raporu duplikasyonu | ⚠️ Devam ediyor (aşağıda D.1) |

Yeni eklenenler (Mayıs sonrası): Alpaca Market Data entegrasyonu + bulk bars, sembol evreni genişletme + 34→9 preset konsolidasyonu, headroom token compression + social intelligence agent, 3.7x scanner hızlandırma, outcomes_horizon tablosu (T+3/5/10), günlük portföy DD gate (%3), haftalık kalibrasyon retrain cron, unified `fp` CLI, signals_archive SQLite migrasyonu (5.722 satır), Academy modülü (yeni — 9-10 Haziran).

**En kritik taşınan bulgu:** Profit Core audit (2026-05-23): **NO EDGE — decile_lift=0.728, p=0.995** (ters skor). Component ablation: "score & R/R harmful, regime neutral" (6e09509). Yani sinyal motorunun kanıtlanmış pozitif edge'i henüz YOK. Bu, tüm stratejik bölümlerin (F, G, vizyonlar) ana kısıtıdır.

---

## TAM DOSYA SİSTEMİ ENVANTERİ (Bölüm B)

| Yol | Tür | Amaç | Son değişiklik | Aktif mi? | Kritiklik |
|---|---|---|---|---|---|
| `start.sh` / `stop.sh` / `fp` | Shell | Resmi dev giriş noktası + yönetim CLI | 06-11 | ✅ | **P0** |
| `finpilot.bat` / `stop.bat` | Batch | Windows başlatıcı | 04-07 | ⚠️ start.sh ile senkron şüpheli | P2 |
| `Makefile` | Make | 30+ hedef (test, lint, docker) | 05-23 | ✅ | P1 |
| `docker-compose.yml` | Compose | 9 servis tanımı | 06-11 | ✅ (dev'de kullanılmıyor) | P1 |
| `Dockerfile` + `web/Dockerfile` | Docker | API + Web imajları | 05-23 | ✅ | P1 |
| `.env` / `.env.example` | Env | 13 API anahtarı | 05-06 / 05-23 | ✅ | **P0** |
| `pyproject.toml` + 6 requirements*.txt | Config | Bağımlılık yönetimi | 05-23 | ⚠️ 6 parçalı — kafa karıştırıcı | P2 |
| `api/` (31 dosya, ~6K LOC) | FastAPI | 21 router, ana backend | 06-12 | ✅ | **P0** |
| `scanner/` (11 dosya, 2.8K LOC) | Python | Tarama + sinyal + skor | 06-11 | ✅ | **P0** |
| `core/` (31 dosya, 11.8K LOC) | Python | Scheduler, cache, KPI, kalibrasyon, monitoring, backtest | 06-12 | ✅ | **P0** |
| `agents/` (20 dosya, 3.9K LOC) | LLM agents | CEO, advisory, alpha_tracker, social intel... | 06-11 | ✅ | P1 |
| `llm/` (6 dosya, 1.4K LOC) | Provider router | Groq/Gemini/Claude failover | 06-11 | ✅ | P1 |
| `drl/` (45 dosya, 12.5K LOC) | RL | PPO ensemble, backtest, optuna | 06-10 (kod) / modeller Mart | ⚠️ Modeller bayat | P1 |
| `models/` (3 PPO + registry) | Weights | DRL ağırlıkları | 05-23 | ⚠️ Mart'tan kalma ağırlıklar | P2 |
| `academy/` (13 dosya, 3.2K LOC) | Python | Self-evolving academy (6 agent) | 06-10 | ⚠️ Ürüne bağlı değil | P1 |
| `FinanceAcademy/` (20 dosya, 1.9K LOC) | Python | Academy DUPLICATE (standalone) | 06-10 | ❌ Redundant | **P0 (karar gerekli)** |
| `auth/` (9 dosya, 3.7K LOC) | Python | JWT, sessions, portfolio | 05-23 | ✅ (streamlit_session.py legacy) | P1 |
| `broker/` (1 dosya) | Python | Broker soyutlaması (iskelet) | 04-22 | ⚠️ Minimal | P2 |
| `web/` (33.6K dosya; src ~yüzlerce) | Next.js 16 | Gerçek ürün UI — dashboard 15+ sayfa | 06-11 | ✅ | **P0** |
| `tests/` (67 dosya) | Pytest | 494 pass / 4 fail / 10 skip | 06-01 | ✅ | P1 |
| `migrations/` (5 dosya) | Alembic | DB şema versiyonlama | 05-23 | ✅ | P1 |
| `data/` (943 dosya) | Veri | finpilot.db (6.9MB), signal_archive, ticker listeleri, eski raporlar | 06-12 | ✅ ama kirli (rapor çöplüğü) | P1 |
| `logs/` (59 dosya) | Log | api/web/auto_trade logları | 06-11 | ✅ | P2 |
| `monitoring/` (7 dosya) | Config | Prometheus + Grafana + alerts.yml | 05-23 | ⚠️ Compose'da var, dev'de çalışmıyor | P2 |
| `docs/` (85 dosya, 45 MD) | Belge | Roadmap, analiz, rehberler | 06-11 | ⚠️ ~%40'ı bayat | P1 |
| `reports/` (35 dosya) | Çıktı | Sprint gap raporları, audit | 05-23 | ⚠️ Tarihsel | P3 |
| `scripts/` (29 dosya) | CLI | paper trading, backtest, raporlar | 06-12 | ✅ (arşiv sonrası temiz) | P1 |
| `research/` (6 dosya) | Python | Araştırma pipeline | 05-23 | ⚠️ | P2 |
| `cli/` (2 dosya) | Python | fp CLI python tarafı | 05-23 | ✅ | P2 |
| `archive/` (59 dosya) | Arşiv | core_legacy, docs_legacy, scanner_stubs, public_website | 05-23 | ❌ (bilinçli ölü) | P3 |
| `grant_documents/` (32 dosya) | Belge | Hibe başvuru hazırlıkları (AWS Gründungsfonds vb.) | 05-05 | ⚠️ Dormant | P2 |
| `site/` (102 dosya) | Build | mkdocs çıktısı | 05-05 | ❌ Build artifact, git'te durmamalı | P3 |
| `telegram_*.py` (3 dosya, root) | Python | Telegram bot + alerts | — | ✅ ama yanlış konum (root'ta modül) | P2 |
| `.github/workflows/ci.yml` | CI | Tek workflow | 03-10 | ⚠️ 3 aydır dokunulmamış | P2 |
| `.pre-commit-config.yaml`, `.trivyignore`, `.secrets.baseline` | Güvenlik | Hook + tarama | 05-20/23 | ✅ | P2 |
| `user_settings.json`, `alembic.ini`, `mkdocs.yml`, `pyrightconfig.json` | Config | Çeşitli | — | ✅ | P2 |
| `.venv/`, `.venv-contract/`, `__pycache__`, `.mypy_cache` vb. | Cache | Araç çıktıları | — | — | P3 |

**Envanter özeti:** Repo, Mayıs audit'inden bu yana belirgin temizlenmiş. Kalan yapısal kirler: (1) Academy duplikasyonu, (2) docs/ bayatlığı, (3) data/ içinde rapor çöplüğü, (4) site/ build artifact'i, (5) root'taki telegram dosyaları, (6) 6 parçalı requirements.
