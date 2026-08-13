# FinPilot Source Material to Product Map

Date: 2026-08-10
Status: DRAFT — Level B proposal

## Important distinction

The additional files were found in `C:\Users\meric\Downloads`, not inside
the Borsa or Finsense repositories. They are not open-source books based on
the available metadata. Most are FinPilot-branded research prompts, reports,
plans, or generated educational drafts. No commercial licence is visible in
the inspected PDFs.

We can still create commercial products from material owned by FinPilot, but
only after removing confidential claims and checking authorship, sources, and
publication rights. The product should contain original writing, examples,
exercises, diagrams, and layout. We should not sell the source PDFs as-is or
present their literature summaries as independently verified evidence without
checking the references.

## Source map

| Source material | What it contains | Product opportunity | Status / caution |
|---|---|---|---|
| `Finansal Okuryazarlık Eğitim Sözlüğü İçin Kapsamlı.pdf` | 46-page glossary and platform design prompt: relationships, learning levels, practical exercises, multilingual structure | **Finansal Okuryazarlık Öğrenme Atlası**: beginner-to-intermediate learning path, concept map, 10-minute lessons, card prompts | Strong packaging source; not a licensed book. Avoid claiming 1,500+ finished terms when the actual pack is smaller. |
| `Explainable_AI_Financial_Literacy.pdf` | Explainability and financial-literacy direction | **AI'ı Okuma Rehberi**: what a model can explain, what it cannot prove, uncertainty and human review | Inspect full text and sources before use; current extraction yielded no reliable text. |
| `Kanıtlanmış ve Mit Statüsündeki Online Trading Stratejileri...pdf` | Evidence-versus-myth comparison across momentum, trend, factors, reversal, indicators, and pattern claims | **Strateji Efsaneleri ve Kanıt**: 30 myth/evidence cards plus a test worksheet | High commercial value, but every literature claim needs reference verification and careful non-advice language. |
| `FinPilot Composite Score Framework 2.0 Dünya Literatürü ile Tasarım.pdf` | Score dimensions: expected return, risk, uncertainty, regime, implementability, factor crowding | **Skor Nasıl Okunur?**: score decomposition workbook and explainability cards | Must clearly separate proposed architecture from validated FinPilot performance. |
| `FinPilot Composite Score Mimarisi.pdf` | Detailed composite-score architecture and regime-adaptive decision concepts | **Composite Score Lab**: build a toy score from fictional data and audit its failure modes | Educational/research-only; never turn the document's architecture into an implied live edge. |
| `FinPilot için %50–%100+ Günlük Hisse Patlamaları...pdf` | Tail-event mechanisms: squeeze, gamma, halts, catalysts, dilution, microstructure, lottery-like outcomes | **Extreme Moves Field Guide**: mechanism cards, risk map, post-event case worksheet | Must lead with rarity, execution risk, and loss asymmetry; no “how to catch 100% moves” framing. |
| `FinPilot Financial Data Integration.pdf` and data-source guides | Market, options, alternative-data and data-quality categories | **Data Quality for Investors**: source comparison matrix, latency checklist, restatement and survivorship exercises | Strong B2B/advanced product; provider claims and prices become stale quickly. |
| `FinPilot_Research_Program_3.1_Uctan_Uca_Plan.md.pdf` | IC/ICIR, CPCV, PBO, DSR, SPA, FDR and research workflow | **Quant Research Workflow Workbook**: preregistration, experiment registry, null controls, gate checklist | Best fit with the existing Honest Quant Handbook and audit-template upsell. |
| `FinPilot_Backtest_Metodoloji_ve_Analiz_Raporu.pdf` | Backtest design, metrics, validation and interpretation | **Backtest Inspection Workbook**: label, sample, benchmark, cost and reproducibility checks | Reconcile with the corrected MFE/c2c findings before publication. |
| `FinPilot_Automated_Discipline.pdf` | Process discipline and automation direction | **Trading Process Journal**: pre-commitment, review, decision log, mistake taxonomy | Keep it educational; no promise that discipline produces returns. |
| `Paper trading yapacak Deep Reinforcement Learning.pdf` and `Adaptive_Alpha_Platform.pdf` | DRL algorithms, paper-trading architecture, adaptive-alpha concepts | **Advanced Research Notes: DRL in Markets** or a technical mini-course | Not a beginner card deck. Research-only positioning; source references need validation. |

## Recommended product ladder

### 1. Free lead magnet: 10-card financial literacy sampler

Use the existing glossary plus five new concepts from the learning atlas:
base rate, calibration, liquidity, drawdown, and position sizing. Each card
should include one misconception and one question. This is an email-capture
asset, not the main paid product.

### 2. First paid product: Financial Literacy Learning Atlas — $19–29

Package the wider material instead of stopping at 37 cards:

- 60–80 concept cards grouped by learning level;
- a visual relationship map: price, volume, risk, evidence, behaviour;
- 12 short exercises with fictional numbers;
- Turkish and English terminology;
- PDF plus Anki/CSV export;
- source register and “what this does not prove” notes.

The original 37 terms remain the foundation, while the additional concepts
come from the FinSense learning plan and are reviewed against code/research
authorities before release.

### 3. Higher-value product: Strategy Myths and Evidence — $29–49

Thirty cards, each with:

- the claim;
- the mechanism people propose;
- what evidence would support it;
- what commonly invalidates a backtest;
- a small test design;
- a conclusion label: established, mixed, exploratory, or unsupported.

This product is differentiated by teaching the buyer how to check a claim,
not by selling a list of “winning strategies.”

### 4. Professional product: Quant Research Gate Workbook — $49–99

Build directly on the four-gate protocol:

- Gate 1 data contract and feature lineage;
- Gate 2 effective sample size, null preflight, and experiment budget;
- Gate 3 spread, drift, half-life, intraday path, and capacity;
- Gate 4 preregistration and confirmatory reporting;
- printable audit sheets and a fillable evidence register.

This is the strongest bridge to research-audit consulting and is more valuable
than a raw report bundle.

### 5. Advanced technical product: Research Notes on Adaptive Alpha and DRL — $39–79

This should be a separate technical audience product. It can cover PPO, DQN,
SAC, walk-forward evaluation, reward design, regime drift, and paper-trading
telemetry. It must explicitly state that a model architecture is not evidence
of a profitable trading edge.

## What not to sell

- a bundle of the original PDFs without a rights and confidentiality review;
- grant, investor, financial projection, or internal audit documents;
- “proven strategy” claims based only on generated literature summaries;
- a guide promising 50–100% daily winners;
- any product implying that FinPilot has a validated live trading edge;
- copied book chapters, scanned pages, copied charts, or close translations.

## Next production step

The highest-leverage next artifact is not a 37-card export. It is a structured
content dataset for the **Financial Literacy Learning Atlas** with 60–80
concept records and these fields:

`slug`, `level`, `term_tr`, `term_en`, `plain_definition_tr`,
`plain_definition_en`, `why_it_matters`, `common_mistake`, `evidence_check`,
`reflection_question`, `source_refs`, `rights_status`, `review_status`.

That dataset can generate the card PDF, Anki/CSV package, web lessons, and
future newsletter content from one reviewed source. Public release remains a
Level B decision pending human approval and rights review.
