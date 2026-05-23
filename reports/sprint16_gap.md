# Sprint 16 — Audit Remediation Gap Report

**Sprint odak:** Master Prompt audit (reports/audit_2026.md) çıktısının "Bugün (5 iş)" + "Bu hafta (10 iş)" bloklarını uygulamak. Tema: **görünürlük → sadeleştirme → kalite kapısı**.

---

## Tamamlanan (Today bloğu)

### S16-01 — Root artifact temizliği ✅
Silinen dosyalar (toplam ~185 KB):
- `top10_scan.csv`, `top25_scan.csv`, `all_scan_sorted.csv`, `wfo_grid_search_results.csv` (artifact CSV'ler)
- `scanner.py` (standalone wrapper — `scanner/` paketi ana giriş)
- `demo_standalone.py` (public Streamlit demo — entegre değil)
- `live_compare_scan.py` (ad-hoc karşılaştırma utility'si)
- `telegram_test.py` (test scratchpad — `tests/` dışında)

**Yan etki yok:** scheduler/api/agents bu dosyaları import etmiyor. `pyproject.toml` per-file ignore listesinden de eski referans temizlenmeli (separate task).

### S16-02 — Audit raporu ✅
`reports/audit_2026.md` (14-section, ~12 KB) commit edildi. Karar kaydı.

### S16-03 — Auto-approve persistence gap ✅
Bu dokümanın "Bilinen Açıklar" bölümüne taşındı (bkz. aşağı).

### S16-04 — Champion edge API endpoint ✅
`api/routers/closed_loop.py` içine `GET /api/v1/loop/champion/edge` eklendi.
Dönüş: champion metadata + son 30g rolling Brier + paper PnL (eğer veri varsa).

### S16-05 — Requirements env-mapping ✅
`DEPENDENCIES.md` zaten 6 profile için detaylı kurulum talimatı içeriyordu (CORE, OBSERVABILITY, ETL, RL, ALTDATA, FULL). Ek dokümantasyona gerek yok — sadece pyproject extras'a göç (S16-08) önerilir.

---

## Bilinen Açıklar (This week + bu ay'a taşınanlar)

### Açık 1: Auto-approve persistence yok (S14 carry-over)
`_run_auto_approve_job` çağrıldığında `signal.auto_approved=True` ve `auto_approve_p_win=X.XXXX` in-memory işaretleniyor — **Redis veya SQLite'a yazılmıyor.** Restart → tüm onaylar kaybolur, ardından gelen reconcile job duplicate "yeni sinyal" olarak işler.

**Çözüm seçenekleri:**
- A) Redis hash `kpi:auto_approved:<symbol>:<cycle>` → `{p_win, ts}` TTL=72h
- B) `kpi_tracker.record_signal()` extension: `set_auto_approved(symbol, cycle, p_win)`
- C) Feature kaldır — manuel approval queue zaten var (`closed_loop.py /pending`)

Öncelik: **P0 (riski yüksek).**

### Açık 2: Calibration refit telemetrisi (S16-07)
`refit_with_gate()` `audit_log` yazıyor ama sadece **decision + ham metrikleri** içeriyor; `ece_before/after` ve `brier_before/after` **karşılaştırmalı** payload yok. "Refit zarar verdi mi?" sorusu cevaplanmıyor.

**Çözüm:** `refit_with_gate` içinde refit öncesi + sonrası ECE ve Brier'i hesaplayıp `audit_log.record(payload={"ece_before":..., "ece_after":..., "brier_before":..., "brier_after":..., "decision":...})` yaz.

Öncelik: **P0.**

### Açık 3: Champion edge dashboard tile (S16-06)
API endpoint var (S16-04 ile eklendi) ama frontend tile yok. `web/src/app/dashboard/calibration/page.tsx` veya yeni `edge/page.tsx` içine consume eden component eklenmeli.

Öncelik: **P1.**

### Açık 4: requirements → pyproject extras (S16-08)
`pyproject.toml` şu an sadece `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest]` içeriyor; `[project]` ve `[project.optional-dependencies]` yok. 6 requirements dosyası birleştirilirse:

```toml
[project]
name = "finpilot"
dependencies = [...]  # requirements.txt içeriği

[project.optional-dependencies]
observability = [...]
etl = [...]
rl = [...]
altdata = [...]
demo = [...]
```

Sonra `pip install -e ".[observability,rl]"` tek komutla çoklu profile kurar.

**Risk:** docker-compose, Dockerfile, CI workflow'lar hâlâ `requirements*.txt` referansları içerebilir. Migrate öncesi grep şart.

Öncelik: **P2 (operasyonel iyileştirme, kritik değil).**

### Açık 5: Feature flags — drl/lgbm_ranker/regime_weights (S16-09)
Üç modül de tam yazıldı ama:
- `drl/`: `FINPILOT_DRL_GATE=0` default, scheduler'da try/except — pratik olarak zaten flag var. **Action:** README + audit log'a "default OFF" notu, gerçek edge raporlanana kadar.
- `research/lgbm_ranker.py`: import edilmiyor, `rank_signals()` hiç çağrılmıyor. **Action:** `FINPILOT_ENABLE_LGBM_RANKER` env değişkeni; scanner/evaluate.py içinden opt-in consumer ekle.
- `core/regime_weights.py`: `get_active_weights()` var, tüketici yok. **Action:** `FINPILOT_ENABLE_REGIME_WEIGHTS` env değişkeni; scoring'e wire et veya archive.

Öncelik: **P1 (ölü kod = bakım yükü).**

### Açık 6: Dashboard 17 → 5 sayfa (S16-10)
17 sayfanın 12'si gerçek kullanım analytics'i olmadan production'da. Önerilen ana nav:
- Scanner / Portfolio / History / Calibration / Settings

Lab altına (env `NEXT_PUBLIC_ENABLE_LAB=1` veya `?lab=1`):
- agent-hub, ai-lab, advisory, autonomy, finsense, drl, strategies, backtest, analysis, watchlist, agent

**Risk:** Bazı sayfalar mevcut kullanıcılar için olabilir; analytics olmadan körlemesine kapama yapma. Önerilen middle-ground: nav'dan kaldır ama route'ları bırak.

Öncelik: **P2.**

### Açık 7: 3 → 1 LLM provider (S16-11)
`llm/router.py` claude/gemini/groq arasında failover. Gerçek failover loglarında tetiklendi mi belli değil. Önerilen:
- Default `claude`, fallback disable
- Redis cache TTL=1h key=`hash(prompt+model)`
- gemini/groq provider dosyaları repo'da kalsın ama router referansı kaldır

Öncelik: **P2.**

### Açık 8: Scheduler 9 → 4 job (S16-12)
Birleştirme önerisi:
- **Job 1 (hourly):** main cycle (CEO orchestrator) — değişmez
- **Job 2 (hourly):** eval + reconcile (her ikisi de outcome-driven)
- **Job 3 (6-saatlik):** calibration + drift detection (calibration zaten drift sonrası tetikleniyor; aynı job içinde sıralı koş)
- **Job 4 (haftalık):** research pipeline + weekly report + CEO Telegram (Pazar 02:00 → 08:00 zinciri)

**Risk:** Watchdog timeout'lar her job için ayrıydı; birleşince tek bir job hang ederse tümü etkilenir. Çözüm: per-step timeout decoratör.

Öncelik: **P1.**

### Açık 9: Test coverage CI badge (S16-13)
`pytest --cov` çağırma + README badge. `.github/workflows/` dizinindeki workflow güncellenecek. Hedef başlangıç: **%40 coverage** (gerçekçi); 90 günde **%60**.

Öncelik: **P2 (kalite görünürlüğü).**

### Açık 10: Look-ahead / leakage audit script (S16-14)
`scripts/audit_lookahead.py` — backtest sinyalleri ile paper trade sonuçları arasındaki Brier farkını per-symbol / per-regime karşılaştır. Fark > %10 ise muhtemel leakage. **Edge'in gerçekliğini doğrulayan en kritik script.**

Öncelik: **P0 (edge doğruluğu için zorunlu).**

### Açık 11: LangGraph CEO → pipeline.run_cycle() (S16-15) — **DEFERRED**
Büyük refactor. Mevcut sistem çalışıyor; bir paket içinde tüm agent wrapper'larını saf fonksiyona çevirmek ve `LangGraph StateGraph`'i lineer fonksiyona indirgemek **2–4 gün** iş + risk yüksek.

**Karar:** Sprint 16 kapsamından **çıkarıldı.** Sprint 17 hedefi olarak işaretle. Önce diğer P0/P1 görevleri tamamlanmalı.

---

## Sprint 16 Skor Tablosu

| Task ID | Açıklama | Durum | Öncelik |
|---|---|---|---|
| S16-01 | Root cleanup | ✅ Done | P0 |
| S16-02 | Audit report commit | ✅ Done | P0 |
| S16-03 | Auto-approve gap dokümantasyonu | ✅ Done (bu rapor) | P0 |
| S16-04 | Champion edge API | ✅ Done | P0 |
| S16-05 | Requirements inventory | ✅ Done (DEPENDENCIES.md) | P1 |
| S16-06 | Champion edge dashboard tile | ✅ Done (calibration/page.tsx) | P1 |
| S16-07 | Calibration refit audit log (ece_before/after) | ✅ Done (core/calibration.py) | P0 |
| S16-08 | requirements → pyproject extras | ✅ Done (pyproject.toml `[project]` + extras) | P2 |
| S16-09 | Feature flags (drl/lgbm/regime_weights) | ✅ Done (docs/feature_flags.md + `is_enabled()`) | P1 |
| S16-10 | Dashboard 15 → 5 (env-gated) | ✅ Done (Sidebar: `NEXT_PUBLIC_FINPILOT_FULL_NAV`) | P2 |
| S16-11 | 3 → 1 LLM provider (env-gated) | ✅ Done (router: `FINPILOT_LLM_SINGLE_PROVIDER`) | P2 |
| S16-12 | Scheduler 9 → 4 | ✅ Done (4 buckets + `FINPILOT_SCHEDULER_LEGACY_JOBS=1` rollback) | P1 |
| S16-13 | Coverage CI badge | ✅ Done (README codecov badge; ci.yml already uploads) | P2 |
| S16-14 | Look-ahead audit script | ✅ Done (scripts/audit_lookahead.py) | P0 |
| S16-15 | LangGraph → pipeline refactor | ⏭ Sprint 17'ye ertelendi | P1 |

**Bu turun teslimi:** 14 done + 1 deferred (S16-15 → Sprint 17).

---

## Sprint 17 — Carry-over Kapatma (Quality & Persistence)

Sprint 16 açıklarından taşınan 4 item Sprint 17'de tamamlandı:

| Task ID | Açıklama | Commit | Durum |
|---|---|---|---|
| S17-01 | Auto-approve persistence (Açık 1) | `b017fd7` | ✅ Done |
| S17-02 | Test coverage %40+ (Açık 9) | `2a30471` | ✅ Done — %50 |
| S17-03 | LangGraph → `core/pipeline.run_cycle()` (S16-15) | `77b05b1` | ✅ Done |
| S17-04 | Üretim analytics sayaçları + `/analytics/summary` | `8e00d97` | ✅ Done |

**Sprint 16 açıklarının tümü kapatıldı.**

---

## Bakım Notu

`pyproject.toml` `per-file-ignores` listesinde silinen `telegram_test.py` referansı var. Sprint 16-1 takip işi olarak temizlenmeli (küçük ama gerekli).
