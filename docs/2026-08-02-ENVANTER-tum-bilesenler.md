# FinPilot + FinSense — Tam Bileşen Envanteri (yol planının zemini)

Tarih: 2026-08-02 · Yöntem: her iki reponun yapısal taraması (bileşen/modül düzeyinde eksiksiz; satır-satır değil). Durum sütunu çıkarımdır; ⚑ = derin inceleme gerekebilir.
Amaç: yol planından ÖNCE hiçbir alan atlanmadan haritayı çıkarmak.

## A) FinPilot (repo: Borsa) — ana ürün: tarama/sinyal + yayın + web

| Alan | Ne | Boyut | Durum |
|---|---|---|---|
| `scanner/` | Sinyal motoru: score_engine, finpilot_score, screener, signals, risk_engine, position_sizer, execution_policy, indicators, features, catalyst, sentiment, earnings_blackout, watch_tier, telemetry | 23 py | Canlı çekirdek |
| `agents/` | Çok-ajanlı analiz org: ceo, bull/bear_researcher, risk, analysis, backtest, research, strategy_optimizer, market/social_intelligence, advisory, alert, alpha_tracker, data_quality, feedback, performance_monitor, report, scanner, shortlist_enricher, combo_testing | 23 py | Kısmen canlı; ShortlistEnricher park |
| `core/` | Orkestrasyon + durum: pipeline (run_cycle), agent_state, agent_events, signal_events, audit_log | 34 py | Canlı |
| `distribution/` | Yayın hattı: telegram_client, broadcast, snapshot_builder, prepublish_gate, karne, rationale, glossary, concepts, lint, market_calendar, scan_contract, schema, store, jobs, maintenance, archive_bridge | 19 py | Canlı — lansmanın kalbi |
| `execution/` + `broker/` | Alpaca otonom execution: gateway, worker, reconciliation, repository, models | 6+1 py | ⚑ Level C, para-bitişik; DISTRIBUTION=0/manuel — muhtemelen kapalı/pilot |
| `api/` | FastAPI backend + routers | 35 py | Canlı |
| `web/` | Next.js: sayfalar dashboard, demo, academy, methodology, premium, api, py-api; components/hooks/lib/__tests__ | ~7 sayfa | Canlı (landing+demo canlı) |
| `auth/` | Kimlik/yetki | 9 py | Canlı ⚑ |
| `drl/` | Derin pekiştirmeli öğrenme araştırması | 45 py | Araştırma — büyük olasılıkla park |
| `research/` | Araştırma modülleri | 12 py | Araştırma/park |
| `academy/` | FinPilot-içi academy (FinSense web/publish köprüsü) | 14 py | Kısmen canlı |
| `scripts/` | Operasyon: tg_discover, publish, refresh_price_cache, backup, denetim | 56 py | Canlı ops |
| `tests/` | Test paketi | 66 py | Canlı |
| `migrations/` | Alembic DB göçleri | 4 py | Canlı |
| `llm/` | LLM router (get_router) | 9 py | Canlı |
| `cli/` | CLI | 2 py | ⚑ |
| Destek dizinleri | monitoring, reports, models, site, assets, archive, grant_documents, data, logs, backups | — | Altyapı/veri |
| **Kök deney scriptleri** | ~90 dosya: backtest_*, score_lab_*, v2_*_runner, test3-6, *_runner, precision_*, target_*, walkforward_* vb. | ~90 py | ⚑ **Dağınıklığın ana kaynağı** — çoğu tek-seferlik deney; arşivlenmeli/park |
| **Kök + docs dokümanlar** | ~30 kök plan/audit (.md+.docx) + `docs/` altında 79 md (adr, audits, governance, ops, runbooks, strategy, reports, academy, api) | ~110 belge | ⚑ Çok birikmiş; bir kısmı bayat |
| Altyapı | Dockerfile, docker-compose, render.yaml, alembic.ini, requirements-*.txt (6), Makefile, mkdocs, pyproject | — | Canlı |
| Governance | AGENTS.md, CLAUDE.md, YONERGE.md, _instructions/00-08, docs/INDEX.md, decision-log.md | — | Canlı — otorite katmanı |
| **`.finpilot/` (YENİ)** | Ortak beyin: Work Item/Handoff/Evidence şeması + handoff.py + .vscode/tasks.json | — | Bu oturumda kuruldu (Level A taslak) |

## B) FinSense (repo: Finsense) — okuryazarlık/içerik katmanı (AYRI repo)

| Alan | Ne | Durum |
|---|---|---|
| `academy/` | İçerik fabrikası: 6 agent + orchestrator + scheduler + RAG + FastAPI | Çalışır (bu oturumda onarıldı+geliştirildi) — ama **PARKING_LOT'a göre park** |

## C) Haritanın söylediği (özet)
- **Sistem tek kişiye göre çok büyük**: ~10 canlı alt-sistem (scanner, agents, core, distribution, execution, api, web, auth) + büyük araştırma yığını (drl, research, ~90 kök script) + ~110 belge.
- **Dağınıklığın iki ana kaynağı**: (1) kökteki ~90 deney scripti, (2) ~110 plan/audit dokümanı.
- **Para-bitişik ve Level C**: execution/broker — en dikkatli alan.
- Bu envanter bir yol planı için yeterli; ama yol planının kendisi lansman-sonrası bir iş (bkz. DURUM.md).
