# R12 - Final Decision Matrix

Version: v1; Date: 2026-10-19; Status: DRAFT / recommendations, not implementation decisions.
Layer: research with engineering and product implications. Level A synthesis; changes require separate approval.
Source identity: report authors recorded HEAD 93ae83c and a dirty worktree. This is not a deployed-version certificate.

## 1. Critical Scope Exception

**STOP on further outcome analysis.** R6, R7 and R9 interpreted the protected-period boundary differently. R6 includes 2026-05-21, R7 calculates new full-archive statistics under a dataset-specific interpretation, and R9 uses a later cutoff. The audit has not established human approval for these interpretations. D7's withdrawal of historical OOS status does not release access restrictions.

Do not use those new outcome slices, confidence intervals or interaction effects to choose a strategy. Preserve the artifacts as an audit trail; do not delete, rewrite or rerun them. A human must resolve the experiment access scope and assess whether protected evaluation was affected. R10 uses a precautionary signal-date cutoff of 2026-05-20; that is a restriction, not a claim that earlier data are independent or universally authorized.

The previously disclosed 5,206-row gross aggregate is reproduced as a historical accounting check only. R10's restricted cohort has 5,126 rows and must not be combined with the full-cohort denominator. Its approximately +0.25% adjusted aggregate is a mixed approximation, not a corrected baseline.

## 2. Recommendation Matrix

Confidence describes the stated finding, not profitability. Every row is a proposal, including FIX_CANDIDATE.

| ID / Priority | Category | Evidence and confidence | Expected benefit / work | Risk / dependency | Validation and production gate |
|---|---|---|---|---|---|
| M01 / P0 | DO_NOT_CHANGE | R7 F-PRF-00; cross-report access conflict; high confidence in inconsistency | Freeze new outcome analysis; obtain experiment-specific access manifest | Further exposure cannot be undone; human review required | Record authorized datasets, partitions and permitted operations before reruns; no automatic release of locks |
| M02 / P0 | FIX_CANDIDATE | R6 ENX-08; R10 B11: resolver prioritizes archive `ts`; code SUPPORTED, replay REPRODUCED within stated cohort | Separate signal and ingestion time in proposed label-v2 research | Weekend signal dates, adjusted prices, replay disagreement; M01 | Validate timestamp semantics and replay controls first; separate versioned outputs only; never overwrite archive labels; production change Level B/C |
| M03 / P0 | RESEARCH_NEXT | R6 ENX-05/10; R10 B11; high confidence in conflicting same-bar rules, execution effect unresolved | Predefine same-bar ambiguity, gap and entry conventions | Daily bars cannot reveal intrabar ordering; M01/M02 | Report all prespecified sensitivity cases, not the best one; separately approve any live exit/risk rule |
| M04 / P0 | FIX_CANDIDATE | R10 B6: unauthenticated daily-report write with unvalidated date path; SUPPORTED static finding | Propose authentication and path/date containment | No exploit was sent; deployment reachability unverified | Offline authorization/path tests, human-reviewed patch, separate release; no live write probe |
| M05 / P1 | NEEDS_MORE_DATA | R5 SCR-01/03; R10 B3; high confidence in code path, historical flags unresolved | Persist actual sort tuple, flags, inputs, time, source and universe identity | New capture is a production change; missing `atr_pct` prevents full legacy replay | Exact fixed-input replay before collection acceptance; separate Level B implementation approval |
| M06 / P1 | NOT_MEASURABLE | R7; R10 A1/A5: theoretical gross labels, no established realized net series | Separate gross labels, cost scenarios and executable returns | Spread, fills, latency, capital overlap absent | Forward execution-quality evidence and prespecified portfolio accounting; no net expectancy claim |
| M07 / P1 | RESEARCH_NEXT | R3 F-DQ-08; R10 B4; mixed IEX/yfinance volume definitions SUPPORTED | Match volume sources/windows and quantify gate disagreement | Six-stock comparison has unmatched periods, not a measured market-share ratio | Same-window comparison, source lineage and decision disagreement; feed/subscription and sizing changes need separate approval |
| M08 / P1 | FIX_CANDIDATE | R4 F-FRM-10; R10 B5; NaN clamp behavior REPRODUCED, live incidence HYPOTHESIS | Propose finite-value validation and missingness diagnostics | Guard can change scores/selections; do not presume live damage | Synthetic boundaries plus stored-input incidence, exact decision diff; Level B review before code change |
| M09 / P1 | RESEARCH_NEXT | R5 SCR-05; R7 F-PRF-10: production-ranking advantage unestablished | Compare selected with eligible-unselected and simple baselines | Reconstruction, point-in-time universe, M01/M05 and multiple testing | One prespecified primary estimand and matched cohort; prospective independent validation |
| M10 / P2 | DO_NOT_CHANGE | R4 double-counting REPRODUCED; usefulness UNRESOLVED | Investigate marginal contribution without editing weights | Shared features are expected in a nested prefilter; not proof of leakage or uselessness | Fixed-input ablation, approved outcome access, multiplicity control; no automatic flag removal |
| M11 / P2 | REMOVE_CANDIDATE | R4/R5/R11: possible redundant score information; HYPOTHESIS | Test simpler ranking as a research alternative | Failure to reject a difference does not establish equivalence | Prespecify noninferiority/equivalence margin and power; no removal until separately approved |
| M12 / P2 | DO_NOT_CHANGE | R10 A4-A6; historical grid/capture evidence does not establish robust advantage | Avoid another unrestricted parameter search | Negative evidence is sample/method-specific, not universal impossibility | Reopen only with a distinct prespecified question and new authorized evidence |
| M13 / P3 | FIX_CANDIDATE | R8 PERF-02/05/07; R10 B8: all-timeframe repair and extra history path SUPPORTED | Test missing-timeframe-only fetch and removal of redundant price lookup | Library cache means calls are not one-for-one HTTP requests; changed coverage may change decisions | Frozen-response offline equivalence, then separately authorized bounded live timing; zero decision differences for pure optimization |
| M14 / P3 | REPLACE_CANDIDATE | R8 PERF-13: three 600s timeouts among 94 observed 200-symbol requests; MEASURED | Evaluate durable job ownership/result retrieval instead of request-owned completion | Coordinator preparation is not live certification; cancellation semantics matter | Timeout/disconnect/retry/restart fixtures plus controlled observation; no activation in this audit |
| M15 / P3 | KEEP_AS_IS | R8 log reconstruction and R5 conditional accounting checks | Preserve useful observability and existing safety gates while evaluating alternatives | Tests/log consistency do not establish strategy quality | Continue contract tests; retain full/partial, freshness, risk and publication gates |

## 3. Five Research Jobs for the Next 30 Days

This is a proposed schedule, not authorization to spend provider quota or alter production. Owner assignments require human acceptance.

| Window / Job | Why / uncertainty resolved | Required data and dependencies | Success evidence | Stop condition / next decision |
|---|---|---|---|---|
| Days 1-4: access and evidence contract | Prevent further protected-data reuse; make all later tests interpretable | Experiment manifests, provenance, prior access history; human owner | Explicit dataset/partition permissions and immutable input identities | Ambiguous permissions: stop outcomes; decides which studies may proceed |
| Days 4-10: label and price-time validity | Determine whether archive outcomes describe the intended signal | Authorized price snapshots, signal/ingestion times, replay control; job 1 | Explain control mismatches and publish versioned sensitivity results with coverage | Timestamp or price basis unresolved: no corrected-return claim; informs label-v2 proposal |
| Days 7-16: forward decision/quality capture design | Make production rank and data-source effects reconstructible | Actual sort fields, flags, `atr_pct`, closed-bar time, source/volume identity | Reviewed schema and fixed-input exact-replay demonstration; collection requires approval | Missing fields/authorization: keep design-only; informs Level B capture change |
| Days 15-24: selection and economics protocol | Separate selection skill from volatility and exit mechanics | Jobs 1-3; eligible-unselected controls, entry/fill/spread information | One locked primary test; explicit cost scenarios vs observed costs; adequacy assessment | No fair control or execution evidence: NOT_MEASURABLE; informs prospective evaluation, not release |
| Days 10-30: bounded performance experiment | Quantify redundant-fetch benefit without changing selection | Frozen 200 symbols/responses, image/flag/cache identity, stage timing; quota approval for live work | Offline zero decision diff; live paired timing/coverage/resource evidence if authorized | Any unexplained decision drift, quota pressure or resource risk: stop; informs optimization proposal |

No success threshold is silently adopted. Numeric OOS/economic acceptance thresholds remain subject to the recorded human decisions. R11's proposed values are draft protocol ideas only.

## 4. Answers to the Strategic Questions

- **A - What works:** additive score accounting can be conditionally checked; gross stored barrier arithmetic is reproducible; worker/request observability exposes timeouts. These are technical/accounting results, not economic edge.
- **B - Excess complexity:** repeated feature contributions, multiple score/rank surfaces and redundant fetch paths merit investigation. Their removal is not justified merely by code duplication.
- **C - Missing:** reproducible production rank history, point-in-time source/flag identity, reliable entry/exit labels, matched controls, realized execution costs and portfolio accounting.
- **D - Potentially wrong:** resolver date precedence, conflicting same-bar policies, NaN clamps and unvalidated report paths have direct code evidence; their live incidence/impact differs and is not universally measured.
- **E - Re-research:** timestamp-valid labels, actual rank vs matched controls, volume-source gate effects, simple noninferior rank and missing-only repair; see R11 cards with scope gates above.
- **F - Deprioritize:** broad TP/SL grid search and median-only capture claims have adverse prior evidence; event/meta-label/regime models are mainly data-blocked, not disproved.
- **G - Main bottleneck:** trustworthy evaluation of what the production system selected and when. For runtime, repair is a historical sampled bottleneck; a current causal full-universe profile is missing.
- **H - Profitability unknowns:** executable entry, gap fills, spread/slippage, concurrent capital allocation and independent prospective evidence remain missing.
- **I - Thirty-day focus:** only the five jobs in section 3, validity before optimization/strategy search.
- **J - Do not change yet:** risk limits, sizing, TP/SL, score weights, universe, provider feeds, funnel activation, coordinator flags, publication and holdout rules.

## 5. Interpretation Controls

R4's 11.8% default-flag reconstruction and R5's 99.88% stored-flag/macro-breakdown reconstruction answer different questions; neither proves raw-data production replay. Composite ties do not imply ties in the actual public sort tuple. R8's throttle lower bound is not an attribution of runtime, and its summary mixes an HL point estimate with a median-difference interval; do not pair them as one estimator. R11 uses R10 and is post-red-team synthesis, not an independent blind assessment. HYP-02 describes six combinations, not four; HYP-07 needs an equivalence design, not a nonsignificance claim. These discrepancies are surfaced, not silently resolved.

## 6. Completion Boundary

R0-R12 form a research evidence package, not a complete profitable-system certification. R0 identifies incomplete inventory coverage. Some requirements are NOT_MEASURABLE or blocked, and the scope exception in section 1 prevents unqualified completion. No production fix, live scan, provider call, broker action, OOS opening, deployment, commit or push is authorized by this report.