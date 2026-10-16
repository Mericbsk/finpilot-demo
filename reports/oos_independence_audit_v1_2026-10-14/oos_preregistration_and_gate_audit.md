# OOS Preregistration and Gate Audit (v1)

- Date: 2026-10-14
- Scope: Phase 3 (gate reconstruction), Phase 4 (baseline reconstruction) and Phase 5 (access policy) of the OOS independence audit.
- Companion files: `oos_freeze_history_audit.md`, `oos_independence_risk_register.md`.
- Status: audit record. Thresholds below are quoted from sources. Missing thresholds are not invented.

## 1. Classification legend

- HP: historically preregistered (exact text predates the evaluation, with verifiable evidence).
- UC: existing threshold with uncertain chronology (text exists; commit or creation time is after the first result artifacts, or not verifiable).
- PC: needs prospective approval (not yet defined).
- POST-HOC: defined after outcomes were inspected, per repository evidence.

## 2. Trading-strategy gate (test plan and fixed-target runner)

### 2.1 Requirement inventory

| # | Requirement | Exact wording or value | Source | Version or commit | Chronology | Class |
|---|---|---|---|---|---|---|
| G1 | Discovery and validation boundaries | discovery `<= 2026-04-17`; validation `2026-04-18..2026-05-21`; locked OOS `> 2026-05-21` | `docs/2026-07-15-score-formula-comparison-report.md` line 12; `data/backtest_out/v2_exit_same_selection/v2_exit_same_selection_results.json` methodology | `db065bf` 2026-07-15 20:18:03 +0200 | Boundary declared in artifacts 16:52Z (`common_buy_accuracy.json`) together with OOS results. Commit after the first OOS artifacts | UC |
| G2 | One-time opening | "Tüm eşik ve kombinasyon seçimleri yalnızca train/validation'da yapılmalı; locked OOS yalnızca bir kez açılmalıdır." | `docs/2026-07-15-score-threshold-combination-test-plan.md` section 7.1 | `db065bf` 2026-07-15 | Committed after locked-OOS results were produced the same day (17:37Z and 18:14Z) | UC |
| G3 | Primary acceptance (either/or) | "Locked OOS lift > 1 veya maliyet sonrası expectancy pozitif" | test plan section 7.3 | `db065bf` | UC (as G2) | UC |
| G4 | Confidence requirement | "OOS confidence interval tamamen rastgele tabanın altında değil" (random baseline not defined numerically) | test plan section 7.3 | `db065bf` | UC; random baseline and CI method not specified | UC; numeric value missing |
| G5 | Time-slice consistency | "En az 3 zaman diliminde aynı yönlü sonuç" | test plan section 7.3 | `db065bf` | UC | UC |
| G6 | Inconclusive or negative median | "Median return negatifse mean sonucu tek başına kabul edilmemeli" | test plan section 7.3 | `db065bf` | UC | UC |
| G7 | Minimum sample size | Test plan section 5 references "minimum n" but gives no number | test plan section 5 | `db065bf` | Number missing | PC |
| G8 | Regime coverage | Regime list (Bull, Bear, Sideways, High-volatility, Low-volatility, Market benchmark) with no pass threshold | test plan section 7.2 | `db065bf` | Thresholds missing | PC |
| G9 | Cost scenarios | "0, düşük, orta ve stres maliyet senaryosu" (no numeric values in plan) | test plan section 6 | `db065bf` | Numeric values appear only in later research files (0.55%, 1.00%) | PC for values; UC for the names |
| G10 | Multiple-testing control | FDR, HAC, CPCV/PBO, White Reality Check, Hansen SPA named in evidence matrix | `reports/evidence_matrix_v1_2026-08-07.md` row "Statistical integrity" | `95b1f8c` 2026-08-07 11:16:54 +0200 | Named; no single mandatory gate | PC |
| G11 | Fixed-target FDR level | `--fdr-alpha` default 0.05 | `scripts/run_fixed_target_research.py` argparse block (about lines 430-445) | `09429f2` 2026-08-06 12:31:17 +0200 | Code committed after the 2026-08-05 report; committed report `ecd1f61` 2026-08-13 | UC |
| G12 | Fixed-target deflated Sharpe | `--min-dsr` default 0.95; qualification requires `dsr >= min_dsr` | same file, qualification block (lines 285-300) | `09429f2` | UC | UC |
| G13 | Fixed-target minimum observations | `--min-period-n` default 50; train and validation `n >= min_period_n` | same | `09429f2` | UC | UC |
| G14 | Fixed-target sign and median rule | Gross mean and median `> 0`; train and validation mean and median net `> 0`; cost-positive at declared scenarios | same file lines 285-300 | `09429f2` | UC | UC |
| G15 | Fixed-target holdout gate | Final verdict string: `none_qualified_locked_holdout_not_opened`; no numeric holdout pass threshold in code | `data/backtest_out/fixed_target_full_universe_2026-08-11.json` `qualification.final_verdict` | artifact 2026-08-11 15:04 | No holdout threshold defined | PC |
| G16 | Failure thresholds | Not defined numerically for the trading-strategy OOS | test plan; fixed-target runner | - | Missing | PC |

### 2.2 Observations

- Two thresholds are numeric and in code: FDR alpha 0.05 and deflated Sharpe 0.95. Both were committed on 2026-08-06, after the 2026-08-05 run artifacts were generated.
- The fixed-target run of 2026-08-05 has an empty validation partition (`validation_rows` 0). The validation requirement in G13 and G14 could not have been applied to that run.
- The 2026-08-11 run has a validation partition of 11,588 rows and a holdout of 269 rows. The partitions differ between runs, so "the" holdout is not a single fixed set.
- The OR-condition in G3 accepts either a lift above 1 or a positive cost-adjusted expectancy. Two alternative criteria weaken the gate unless a primary metric is named.
- No numeric failure threshold exists for the trading-strategy OOS (G16).

## 3. Primary and secondary metrics in the RX-CAPTURE-1 gate (documented)

- Source: `reports/research_x_capture_1_preregistration_2026-09-22.md` (v1.0-LOCKED; SHA-256 `d0baa61834efe06efa30dc674aa76b34881e29a06c05a1ad70627fc2b6d5036e`, verified against the decision-log record). Decision-log entry "[2026-09-22] - RESEARCH-X/RX-CAPTURE-1 capture & exit battery preregistration locked (Level A)".
- Primary estimand: `Median(NC_i)` over valid observations, `NC_i = GrossExitReturn_i - Cost_i`. Cost: 0.55% primary, 1.00% stress (round-trip).
- Ambiguous same-day observations: excluded (locked convention). Ambiguity count and excluded fraction are mandatory.
- Temporal: early 40%, middle 20% buffer, late 40%; minimum evidence `>= 20` distinct days and `>= 100` valid observations per primary period.
- Concentration: any single scan day above 25% of a candidate's net P&L blocks SUPPORTED.
- Multiple comparisons: Holm family-wise. Seed 20260922; block bootstrap B = 2000, 5-day blocks.
- Verdict for SUPPORTED: all nine gates pass, including "independent verification PASS".
- Documented methodology finding (decision-log, 2026-09-22 result entry): the median degenerates for E1_t3 and E1_t5 because more than 50% of valid observations hit the fixed target on first touch.
- Classification: HP for the threshold text and the lock. The primary metric is known to be degenerate for the candidates it evaluates. The lock is not contradicted; its discriminating power is limited.

## 4. RX-CAPTURE-1-ECON gate (lock contradicted)

- Committed version (`e0e7b38`): "Version: v0.1-DRAFT", "DRAFT - NOT LOCKED".
- Working copy (modified 2026-10-09 13:12:24): "Version: v0.3-LOCKED".
- Decision-log lock record (2026-09-23) cites SHA-256 `6b210259...`, which matches neither version.
- Decision-log economic-review result (2026-09-23) reports `FURTHER_VALIDATION_SUPPORTED` with "MEDIAN-VS-MEAN DIVERGENCE": positive primary median and negative mean net capture (E1_t3 mean -0.832 pp, E1_t5 mean -0.841 pp at 0.55%). The gate therefore did not establish economic support by the mean.
- Classification: contradicted for the lock claim; the threshold text in the working copy cannot be linked to a verifiable lock.

## 5. Preregistered hypotheses H1-H3 (not run)

- Source: `reports/preregistration_three_hypotheses_2026-08-10.md`. Header "Date: 2026-08-10", "Status: pre-registered, NOT to be run until the two gates below open".
- First Git commit: `ecd1f61` on 2026-08-13 11:51:10 +0200 (three days after the header date).
- Success and kill criteria are qualitative and CI-based: success requires "null'dan anlamlı pozitif ayrışma, CI sıfırın üstünde"; kill when "CI sıfırı kapsıyorsa veya yön tersine dönerse".
- Classification: UC for chronology; no numeric pass threshold. These hypotheses were not evaluated under OOS in the repository.

## 6. Baseline reconstruction (Phase 4)

- Evidence matrix (`reports/evidence_matrix_v1_2026-08-07.md`, row "Hypothesis identity and reproducibility"): "Full row-level live/research score equivalence is still open; the 16.0/16.5 score-ceiling discrepancy remains unresolved." Status PARTIAL.
- Decision-log entry for the H4C preregistration (2026-09-22): the header "fixes Production ordering = UNKNOWN / NOT RECONSTRUCTED".
- Decision-log entry on attention-score overlap (2026-08-14): "Formula equivalence remains unproven."
- The live `squeeze_factor` column is missing from the historical export.
- The trading-strategy tests use `alpha_v2_offline_score_v1` (`data/backtest_out/alpha_v2/alpha_v2_results.json`, generated 2026-07-15 16:59:19Z). Its formula is `4*short_n + 3*atr_n + 3*gap_n + 2*rvol_n - 1.5*extension_n`. This is an offline proxy, not the production score.

Finding: the method tested for the trading-strategy OOS is not the method used in production. The mismatch is documented by the project itself. A missing reconstruction is not proof that the strategy is ineffective, and it is not proof that the test was biased. It means the OOS test does not evaluate the production ranking.

## 7. Access policy (Phase 5)

### 7.1 Existing policy

- `docs/governance/research_x_master_orchestrator_v2.md` section 42, "OOS GOVERNANCE": "Locked OOS `DO NOT OPEN` - unless: preregistration locked, training/discovery fully separated, validation criteria locked, data boundary frozen, governance approval exists. OOS açıldıktan sonra `DO NOT TOUCH` kuralı geçerlidir." First committed `b780b10` on 2026-09-23.
- `docs/governance/research_x_master_orchestrator_v2.md` line 271: "LEVEL C - LOCKED OOS / CANDIDATE VALIDATION ... Level C otomatik açılmaz."
- `docs/governance/research_governance_controller_spec_v1.md`: "APPROVED / LOCKED - Meriç approval 2026-09-23"; "Cascade yok: her geçiş kendi insan onayını gerektirir."; "Locked research asla mutate edilmez / yeniden açılmaz."
- `research/protocol.py` lines 146-162: `LockedHoldoutGuard.open_once(experiment_id)` raises if the state file exists, then writes `experiment_id` and `opened_at`. First committed `09429f2` on 2026-08-06. Tested in `tests/test_research_protocol.py` lines 66-72.

### 7.2 Enforcement gap

- The runners do not call `LockedHoldoutGuard`. `scripts/run_fixed_target_research.py` lines 274-277 and `scripts/run_full_universe_research.py` lines 210-211 only check whether the state path exists and report `already_opened` or `not_opened`.
- The guard is used only in the test file.
- No access log exists (section 0 of the freeze history audit).
- The policy in section 42 postdates the trading-strategy OOS evaluations of July, August and September. It is not a contemporaneous rule for those evaluations.

### 7.3 Proposed prospective policy (PROPOSAL; not in force)

Each item is new and requires human approval before use.

1. Authorization: named human approver, written approval recorded in the decision log before access.
2. Freeze before access: protocol text with SHA-256; code commit hash; dataset hash of a copy taken while no service writes; date boundary; numeric thresholds for primary, secondary and failure criteria; inconclusive rule.
3. Strategy version: a single commit hash of the scoring code, to be evaluated.
4. Metrics: primary metric named; mean, median, hit rate and asymmetry reported together; full-sample figure primary; outlier sensitivities secondary.
5. Report generation: script that writes a versioned report and a hash; no manual edits.
6. Inconclusive results: reported as inconclusive; no threshold change.
7. Rerun rule: a failed evaluation is not rerun on the same set. Any rerun requires a new set.
8. New untouched set required when: the protocol changes, the code changes, the data boundary changes, or any outcome of the set has been viewed.
9. Enforcement: runners must call a guard that writes an access event (experiment identifier, requester, time, dataset hash) before any read of the set.

## 8. Gate status summary

| Gate element | Status |
|---|---|
| Discovery and validation boundaries | UC (declared with first OOS results) |
| One-time opening | UC (committed after results) |
| Primary acceptance | UC (OR-condition; undefined numeric random baseline) |
| Minimum sample size | PC (number missing) |
| Failure thresholds | PC (missing) |
| Inconclusive rule | UC (median rule only) |
| Multiple-testing control | PC (named, not mandatory) |
| Holdout gate (fixed-target) | PC (no numeric holdout threshold) |
| RX-CAPTURE-1 gate | HP (hash-verified; primary median degenerate) |
| RX-CAPTURE-1-ECON gate | Contradicted (lock hash not reproducible) |
| H1-H3 criteria | UC (qualitative; committed three days after header date) |
