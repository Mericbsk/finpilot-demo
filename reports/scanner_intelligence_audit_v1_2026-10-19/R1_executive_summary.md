# R1 - Executive Summary

Version: v1; Date: 2026-10-19; Status: DRAFT / qualified audit synthesis.
Layer: research; Level A reporting. Recommendations are not approved changes.
Sources: R0 and R2-R12 in this folder; recorded source HEAD 93ae83c with a dirty worktree.

## Decision in One Paragraph

**Profitability and production-selection advantage are not established. Prioritize measurement validity over another score, strategy or speed rewrite.** The audit reproduces the historical gross accounting numbers, but identifies a signal-time/ingestion-time mismatch in the outcome resolver, incomplete historical rank reconstruction, heterogeneous source semantics and missing execution economics. It also exposes an audit-process scope exception: contributors used inconsistent protected-period interpretations. Further outcome calculations must stop until human review resolves access scope. The detailed recommendation categories and five-job plan are in [R12](R12_final_decision_matrix.md).

## Strongest Findings

| Finding | Evidence status | Meaning / limit |
|---|---|---|
| Historical 5,206 stored barrier labels: mean +0.398424%, median -0.64315%; removing best 5% gives -0.161478% | REPRODUCED, R0 EVI-03 | Gross stored-label arithmetic only; no costs, capital or realized fills |
| Top-1% concentration was described using archive dates, not two trading days | REPRODUCED / CONTRADICTED wording, R0 and R10 B1 | One of the two archive dates is Sunday; signal dates differ |
| Resolver prioritizes `ts` when opening the outcome window, while entry comes from the signal payload | SUPPORTED code / REPRODUCED approximate replay, R6 ENX-08 and R10 B11 | Late ingestion can shift labels; adjustment size is not a certified corrected return |
| Publication ordering uses grade/confidence/probability and a conditional rank key, not necessarily composite score | SUPPORTED, R5 and R10 B3 | Depends on flags and fallback values; actual historical production order is not fully reconstructible |
| IEX and fallback volume can feed the same liquidity/ADV rules | SUPPORTED, R3 and R10 B4 | Mixed definitions may alter gates; unmatched-period volume comparison is not a precise market-share measurement |
| NaN clamp can produce upper-bound score values | REPRODUCED mechanism, R4 and R10 B5 | Production incidence and economic impact remain HYPOTHESIS |
| Timeout responses can precede successful workers and omit persistence | MEASURED / SUPPORTED, R8 PERF-13 | Three of 94 observed 200-symbol requests hit 600s; no full-universe causal timing claim |
| Repair requests all real timeframes again and the library price lookup may add a history path | SUPPORTED, R8 and R10 B8 | Optimization candidate, not a measured speedup; library caching affects actual HTTP count |
| Daily-report write lacks local authentication and safe date-path validation | SUPPORTED static security finding, R10 B6 | No exploit or live write was attempted; deployed exposure not verified |

## What Is Working

Stored TP/SL-derived return arithmetic is reproducible. Some score-component accounting is conditionally consistent with stored flags and macro breakdowns. Worker/request records distinguish HTTP completion from worker lifetime. Independent review corroborated important code findings and qualified others. None of these observations proves that selection produces tradable economic value.

## What We Cannot Yet Answer

- Whether the actual production ranking beats eligible-unselected stocks or a simple matched baseline.
- Whether signal/reference prices were executable after the signal became knowable, or what spread, gap, latency and fill costs would be.
- What an investable portfolio earns with overlapping positions and capital constraints.
- Whether any historical positive result generalizes to an untouched prospective sample.
- How much a particular optimization causally reduces current full-universe latency without changing decisions.

## Critical Audit Limitation

R6, R7 and R9 did not share one approved interpretation of the protected-period boundary. Preserve their artifacts, but do not promote their new outcome statistics or interaction discoveries into strategy evidence. R10's precautionary <=2026-05-20 results have a different cohort (5,126) from the reproduced historical aggregate (5,206). D7's historical OOS disqualification is not permission to access locked data. This report neither approves the differing interpretations nor claims that every brief requirement was completed. See R12 sections 1 and 6.

The independent consistency review also found estimator/cohort qualifications, reconstruction differences and R11's inaccurate blind-independence statement. R12 section 5 records them explicitly; prior reports are retained as evidence rather than silently rewritten.

## Three Highest-Value Research Opportunities

1. Establish timestamp-valid, price-basis-valid outcome labels with control replay before using archive returns for new decisions.
2. Capture actual decision provenance and compare selection against eligible-unselected controls under an approved prospective protocol.
3. Test missing-only repair and redundant fetch removal on frozen responses, then separately authorized bounded timing with unchanged decisions.

The five-job, 30-day plan adds access governance and execution economics to these priorities; see R12 section 3. No thresholds, score weights, risk limits, provider feeds or live flags should change on the strength of this audit alone.

## Report Index

| Report | Purpose |
|---|---|
| [R0](R0_evidence_inventory.md) | Prior-research inventory, protected experiments and reproduced historical claims |
| [R2](R2_architecture_map.md) | Architecture, module/decision flow and production-vs-research paths |
| [R3](R3_data_quality_lineage.md) | Data quality, lineage, sources and missingness |
| [R4](R4_formula_feature_registry.md) | Formula registry and boundary behavior |
| [R5](R5_flags_scoring_ranking.md) | Flags, score accounting and conditional ordering |
| [R6](R6_entry_exit_audit.md) | Entry/exit conventions; scope exception applies |
| [R7](R7_profitability_risk.md) | Gross accounting and economic gaps; scope exception applies |
| [R8](R8_scanner_performance.md) | Timing, worker/request lifecycle and candidate bottlenecks |
| [R9](R9_interactions_dependencies.md) | Dependencies and exploratory interactions; scope exception applies |
| [R10](R10_red_team.md) | Independent challenge and restricted-cohort verification |
| [R11](R11_hypothesis_backlog.md) | Draft hypotheses; post-red-team synthesis, not independent confirmation |
| [R12](R12_final_decision_matrix.md) | Recommendation matrix, scope controls and 30-day plan |

## Delivery and Integrity Checks

- R0-R12 are present (13 reports including the additional R0 inventory). Links in the new R1/R12 reports and all eight requested recommendation categories passed a focused check.
- Start record: external temporary file `fp_audit_2026_10_19_pre.txt`; this contains porcelain status and two diff hashes, not a full file-content manifest.
- End comparison before the audit receipt: HEAD remained 93ae83c. Two additional paths outside the audit folder appeared in status: `.github/instructions/content.instructions.md` and `docs/index.md`, consistent with separately observed Academy ownership work. Attribution is not independently proven; neither was reverted.
- Both working-tree and staged diff hashes failed to match the saved start record. Therefore byte-for-byte integrity and unchanged staging are **UNRESOLVED**, not PASS. The start hash-generation method and concurrent edits require review. A matching status line alone does not prove matching contents.
- No new outcome calculation was run during synthesis/consistency review. No live scan, provider call, broker action, restart, production fix, commit or push was performed in this continuation. Prior role-specific calculations and their scope exceptions remain disclosed above.
- Synthesis is delivered with qualifications. Research validity and integrity gates remain open; this is not an unqualified completion or release certificate.