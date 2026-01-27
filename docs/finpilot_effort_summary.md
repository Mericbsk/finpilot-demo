# FinPilot Effort & Roadmap Snapshot

_Last updated: 2025-10-24_

## Executive Summary
- **Scope covered**: Landing experience, global styling, CTA workflow, signal enrichment (chips, tables, mobile cards), summary panel, simple/advanced toggle, CSV ingestion, demo data, recommendation analytics, Telegram hooks, pilot/roadmap documentation.
- **Traditional effort**: ≈ **432 engineering hours** (≈ 54 person-days) across frontend, backend, data, product and QA roles.
- **LLM-accelerated result**: Same scope delivered by one founder + AI pairing at a fraction of the time/cost, creating a strong narrative for grants and investors.
- **Next horizon**: Hybrid explainability (local models + Perplexity Pro) adds ≈ 22 person-days (176–192 hours) and positions FinPilot as a transparent, evidence-backed assistant.

## Detailed Effort Breakdown
| Track | Example Deliverables | Primary Roles | Est. Days | Est. Hours |
| --- | --- | --- | --- | --- |
| **Core infrastructure** | Streamlit setup, session state helpers, CSV utilities, SettingsCard loader, Telegram wiring | Backend | 9.5 | 76 |
| **UX & interface** | Landing refactor, global CSS, status chips/table, mobile cards, summary panel, toggle, CTA flow | Frontend/UX | 21.5 | 172 |
| **Analytics & data** | Signal strength logic, summary metrics, recommendation ranking, demo datasets, advanced panel prep | Data/ML | 11.5 | 92 |
| **Product & narrative** | Copywriting, info banner, roadmap, pilot plan, grant documentation | Product/PM | 7 | 56 |
| **Quality & enablement** | QA pass, recordings, orchestration, task tracking | QA/PM | 4.5 | 36 |
| **Total** | — | — | **54** | **432** |

> _Interpretation_: A conventional three-person squad (Frontend, Backend/Data, PM/UX) would need ~4–5 weeks to reach today’s milestone. This provides a clear counterfactual showing the leverage of the LLM workflow.

### Role-Based Summary
| Role | Hours | Notes |
| --- | --- | --- |
| Backend / Integration | 76 | Session control, asset loaders, Telegram gating |
| Frontend / UX | 172 | Major CSS system, responsive layouts, interaction design |
| Data / ML | 92 | Score aggregation, chip logic, analytics feeds |
| Product / PM / Writer | 56 | Content, roadmap, pilot blueprint, grant copy |
| QA / Support | 36 | Regression checks, demo preparation |

## Hybrid Explainability Expansion
| Phase | Objective | Key Activities | Est. Days | Est. Hours |
| --- | --- | --- | --- | --- |
| **1. Local LLM + Qdrant** | Offline explainability pipeline | Ollama inference service, embeddings, prompt templates, Streamlit plumbing | 7 | 56–64 |
| **2. Perplexity Pro integration** | Source-backed insights | Prompt guard, anonymisation, rate-limit/cache layer, failure handling | 6 | 48–56 |
| **3. Dual-layer UI** | Local + sourced explanation UX | Card layout, skeleton states, user preference toggles | 5 | 40 |
| **4. Observability & prefs** | Reliability & governance | Audit logs, monitoring dashboards, user settings, regression QA | 4 | 32 |
| **Total** | — | — | **22** | **176–192** |

## LLM-Leveraged Productivity Narrative
- Prompt-driven development shortened iteration cycles (landing overhaul, chip system, toggle) from weeks to days.
- Automatic checks (`python -m py_compile panel_new.py`) + collaborative TODO tracking kept the single-developer workflow safe and auditable.
- Product copy, pilot design, and grant positioning were co-created with the same AI tooling, proving “vibe coding” goes beyond UI tweaks.

## Suggested Attachments for Grant/Evidence Pack
1. **Demo video** (simple vs. advanced walkthrough + summary panel).
2. **Architecture diagram** (current stack + upcoming hybrid explainability layers).
3. **Pilot program brief** (target testers, cadence, metrics).
4. **Feedback toolkit** (survey template + Notion/CRM board).

## Next Steps
- Finalise evidence pack assets (video, diagram, pilot report template).
- Launch the feedback loop with selected beta testers.
- Kick off Phase 1 of the hybrid explainability roadmap once funding or bandwidth allows.
