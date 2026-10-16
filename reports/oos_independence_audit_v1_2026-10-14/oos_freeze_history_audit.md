# OOS Freeze History Audit (v1)

- Date: 2026-10-14
- Scope: Phase 1 and Phase 2 of the FinPilot OOS independence and gate audit (investor question 4). Read-only.
- Status: audit record. No sealed dataset was opened. No out-of-sample evaluation was executed. No production code, data, threshold, decision-log entry or artifact was changed by this audit.
- Output directory: `reports/oos_independence_audit_v1_2026-10-14/`

## 0. Method and limits

- Repository state at capture: HEAD `3afa3f77d5487ed80b10d2776153b0e2cd377a3c` on `review/pending-2026-10-07`; 74 uncommitted entries.
- Commit chronology: `git log --follow --diff-filter=A` and `git log -S` on the files named below.
- Hashes: SHA-256 with `Get-FileHash`.
- Generation times: the `generated_at` or `created_at` fields written inside each artifact. These are self-reported by the writing script.
- File modification times are recorded but are not treated as proof of freeze or of prior inspection.
- `data/backtest_out/` is listed in `.gitignore` (line 103). Artifacts there are not anchored to commits.
- Access history: a search of `logs/` and `data/backtest_out/` for `holdout`, `locked_oos`, `LockedHoldout` and `open_once` returned no matches. No access log was found. Historical access therefore cannot be fully verified.

## 1. Candidate datasets and boundaries

| ID | Dataset and boundary | Primary paths | Hash | Earliest verifiable freeze evidence | Classification (A/B/C/D) | Used in development |
|---|---|---|---|---|---|---|
| C1 | Trading-strategy "locked OOS": rows dated after 2026-05-21 (discovery to 2026-04-17; validation 2026-04-18 to 2026-05-21) | `data/backtest_out/common_buy_accuracy/common_buy_accuracy.json`, `data/backtest_out/alpha_v2/alpha_v2_results.json`, `data/backtest_out/v2_exit_same_selection/v2_exit_same_selection_results.json`, `data/backtest_out/p0_*` | none | None documented before results. First artifacts with the boundary already contain locked-OOS results (see 2.1) | D (cannot be established as independent) | Yes; discovery, validation and OOS results computed on the same artifacts |
| C2 | Trading-strategy OOS after 2026-06-26 (chronological 70/30 cut) | `direction_context_battery_2026-09-03.md`, `direction_threshold_matrix_2026-09-03.json`, `experiment_review_board_exp1_2026-09-03.md`, `scoring_ablation_audit_2026-09-08.md`, `walk_forward_scoring_validation_2026-09-08.md`, `data/backtest_out/baseline_ranking_health_2026-09-09.json` | none | Cut declared in artifacts dated 2026-09-03 and 2026-09-08 | D | Yes; OOS n = 17,149 to 18,909 across reports |
| C3 | Trading-strategy boundary moved to 2026-07-06 | `data/backtest_out/alpha_v2_2026-08-12-e2e/alpha_v2_results.json` (`validation_end` 2026-07-06) | none | Artifact dated 2026-08-12 | D | The 2026-05-21 to 2026-07-06 span changes role from OOS to validation |
| C4 | Early split at 2026-01-01 (`IS_END`) | `backtest_signals.py`, `backtest_full_universe.py`, `analyze_enriched.py`, `score_lab_1_weights.py`, `data/backtest_out/backtest_results.json` (`walk_forward.IS_end` 2026-01-01; `n_OOS` 3005; `OOS_metrics.n` 1227) | none | None; artifact date not established in this audit | D | Yes |
| C5 | PIT / fundamentals-sentiment holdout, 2026-06-09 to 2026-06-30 | `data/backtest_out/fundamentals_sentiment_protocol.json`, `data/backtest_out/fundamentals_sentiment_holdout.json` | protocol `D8E7AC9BDC887A73D79252EB0A84BAA5ED153FC9B4263AE8C712F74E8C1A5E1B`; holdout state `38781BB8B2AC0114E5EAE5B308FDA60F2A78A8BD8B46CF97E8C1773D6A891CCC` | Self-recorded: `frozen_at` 2026-08-05T11:31:08Z, `created_at` 2026-08-05T11:31:24Z. Files git-ignored | B/C (self-timestamped, not commit-anchored) | Holdout not opened per state file. Same calendar dates were inside the C1 and C2 OOS periods |
| C6 | Fixed-target holdout (`locked_holdout_opened.json` state path) | `scripts/run_fixed_target_research.py` lines 274-277; `scripts/run_full_universe_research.py` lines 210-211; runs dated 2026-08-05 and 2026-08-11 | none | None. Runner code first committed 2026-08-06; reports first committed 2026-08-13 | D | Two runs define different partitions (see 2.6) |
| C7 | RX-CAPTURE-1 locked cohort: canonical EOD export, 54 dates, n = 34,762 | Export `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`; `reports/research_x_capture_1_preregistration_2026-09-22.md` | Prereg `d0baa61834efe06efa30dc674aa76b34881e29a06c05a1ad70627fc2b6d5036e`: see 2.7 | Hash recorded in decision log 2026-09-22; current file matches | A with limitations | Same export also used by NS-1, H4C and H4D. Not an OOS set |
| C8 | RX-CAPTURE-1-ECON protocol (economic review) | `reports/research_x_capture_1_economic_review_preregistration_2026-09-23.md` | Recorded lock hash `6B210259...`; does not match committed or working copy (see 2.8) | Claimed lock 2026-09-23; not reproducible | Claim contradicted by evidence | Result artifact `data/backtest_out/research_x_capture_1_econ_2026-09-23.json` exists; protocol version used is not established |

## 2. Freeze records (exact evidence)

### 2.1 C1: trading-strategy locked OOS boundary (2026-05-21)

- `data/backtest_out/common_buy_accuracy/common_buy_accuracy.json`: `generated_at` 2026-07-15T16:52:02.408664Z. Declares `split` with `discovery_end` 2026-04-17, `validation_end` 2026-05-21 and `locked_oos_start_exclusive` 2026-05-21. The same file contains a `locked_oos` block: `common_buy_n` 44, `common_buy_dates` 7, `legacy_accuracy_pct` 54.5455, `v2_accuracy_pct` 45.4545, `both_correct_pct` 38.6364.
- `data/backtest_out/alpha_v2/alpha_v2_results.json`: `generated_at` 2026-07-15T16:59:19.734573Z. Contains the boundary declaration (`locked_oos_start_exclusive` at line 3778). A key search found no locked-OOS result block in this file.
- `data/backtest_out/v2_exit_same_selection/v2_exit_same_selection_results.json`: `generated_at` 2026-07-15T17:37:26.015215Z. Locked-OOS results for `tp5_sl1` (`selected_n` 92, `execution_n` 62, net expectancy +2.0501%) and `tp5_sl1_5` (net −0.0046%).
- P0 replay folders (for example `data/backtest_out/p0_execution_replay/`): file modification times 2026-07-15 18:14 to 18:42.
- `data/backtest_out/full_universe_enriched.pre_c2c_backup.csv`: modification time 2026-07-15 13:44. Name indicates a backup taken before a correction ("c2c"). The dataset was therefore modified on the same day, before these artifacts. Which version each artifact used is not recorded.
- Git: `db065bf` committed 2026-07-15 20:18:03 +0200 ("chore: save scanner research and runtime updates"). It first added `docs/2026-07-15-score-threshold-combination-test-plan.md`, `docs/2026-07-15-score-formula-comparison-report.md`, `docs/2026-07-15-p0-execution-replay-report.md` and `docs/2026-07-15-nihai-kontrol-ozet-ve-degisim-plani.md`.
- `docs/2026-07-15-nihai-kontrol-ozet-ve-degisim-plani.md` line 32, row 20: "P0 exit-sensitivity gridi | full_universe | V2 n=62 | tp5/sl1 en iyi (+%2.05)". The exit profile was ranked on the locked-OOS result.

Finding: the boundary and the first locked-OOS results appear in the same artifact (16:52:02Z). No earlier declaration of the boundary exists in the repository. The chronology therefore does not show that the boundary preceded inspection of the OOS outcomes.

### 2.2 C2: 2026-06-26 cut and September reuse

- `direction_context_battery_2026-09-03.md` line 7: "kesim 2026-06-26; discovery n=21.925, OOS n=18.909".
- `direction_threshold_matrix_2026-09-03.json` line 8: `oos_n` 18909.
- `experiment_review_board_exp1_2026-09-03.md` line 22: "Kronolojik 70/30, kesim 2026-06-26 (discovery n=21.925, OOS n=18.909)".
- `scoring_ablation_audit_2026-09-08.md` line 6: "kesim 2026-06-26 · dev n=19.141, OOS n=17.149".
- `walk_forward_scoring_validation_2026-09-08.md` line 33: window table with OOS n per window.
- `data/backtest_out/baseline_ranking_health_2026-09-09.json` line 143: `oos_n` 2225.
- Git: all of these were first committed in `b780b10` on 2026-09-23 13:43:45 +0200. Their content is dated 2026-09-03 to 2026-09-09; the commit is later.

Finding: the 2026-06-26 cut falls inside the C1 locked-OOS period (after 2026-05-21). Dates from 2026-06-26 to 2026-07-15 were therefore already evaluated in C1 before these September reports used them again.

### 2.3 C3: 2026-07-06 boundary

- `data/backtest_out/alpha_v2_2026-08-12-e2e/alpha_v2_results.json` line 3489: `validation_end` 2026-07-06, artifact dated 2026-08-12.

Finding: the same period that C1 labelled OOS is now labelled validation. The partition was changed after evaluation.

### 2.4 C4: 2026-01-01 early split

- `backtest_signals.py` line 32, `backtest_full_universe.py` line 47, `analyze_enriched.py` line 14, `score_lab_1_weights.py` line 24: `IS_END = "2026-01-01"`.
- `data/backtest_out/backtest_results.json` lines 800-832: `walk_forward.IS_end` 2026-01-01; `n_IS` 2065; `n_OOS` 3005; `OOS_metrics.n` 1227; `OOS_metrics.lift` 0.99.

Finding: a separate out-of-sample split exists in several scripts. It is not a freeze and it overlaps the C1 period. The artifact date is not established.

### 2.5 C5: PIT / fundamentals-sentiment holdout

- `data/backtest_out/fundamentals_sentiment_protocol.json`: `frozen_at` 2026-08-05T11:31:08.120095+00:00; `historical_discovery_range` 2025-09-11 to 2026-05-07; `historical_validation_range` 2026-05-08 to 2026-06-08; `locked_holdout_range` 2026-06-09 to 2026-06-30; `holdout_status` not_opened_locked_holdout. SHA-256 `D8E7AC9BDC887A73D79252EB0A84BAA5ED153FC9B4263AE8C712F74E8C1A5E1B`.
- `data/backtest_out/fundamentals_sentiment_holdout.json`: `created_at` 2026-08-05T11:31:24.565379+00:00; `status` not_opened_locked_holdout; `human_approval_required` true; `historical_cutoff` 2026-06-08; `rows` []. SHA-256 `38781BB8B2AC0114E5EAE5B308FDA60F2A78A8BD8B46CF97E8C1773D6A891CCC`.
- `.gitignore` line 103 ignores `data/backtest_out/`. `git ls-files` shows neither file is tracked.
- Code: `scripts/pit_research_pipeline.py`, `research/protocol.py` and `scripts/run_fixed_target_research.py` were first committed in `09429f2` on 2026-08-06 12:31:17 +0200.

Finding: the holdout is self-timestamped and not commit-anchored. Its dates (2026-06-09 to 2026-06-30) lie inside the C1 and C2 periods, which were already evaluated. The file records that the holdout was not opened. That is a statement by the writing script, not an access record.

### 2.6 C6: fixed-target holdout partitions

- `reports/fixed_target_full_universe_2026-08-05.md` line 12: `train_rows` 2022, `validation_rows` 0, `locked_oos_rows_unopened` 22709. First committed `ecd1f61` on 2026-08-13 11:51:10 +0200.
- `data/backtest_out/fixed_target_full_universe_2026-08-11.json`: `train_rows` 14515, `validation_rows` 11588, `locked_oos_rows_unopened` 269; `date_range` 2025-09-11 to 2026-07-09. File modification time 2026-08-11 15:04.
- The two runs use different partitions. In the 2026-08-05 run the validation partition is empty.
- `data/backtest_out/locked_holdout_opened.json` (the open-state file the runner tests for) does not exist as of 2026-10-14. Its absence is the only evidence that the holdout is unopened.

Finding: no freeze record exists for C6. "Not opened" rests on a file-existence check. The protection class `LockedHoldoutGuard` (see the gate audit) is not used by the runners.

### 2.7 C7: RX-CAPTURE-1 preregistration (documented, hash-verified)

- `reports/research_x_capture_1_preregistration_2026-09-22.md`: header `Version v1.0-LOCKED`, `Status APPROVED / LOCKED - Meriç approval 2026-09-22`. Line 54 states "locked OOS açmaz" (does not open the locked OOS). Current SHA-256 `d0baa61834efe06efa30dc674aa76b34881e29a06c05a1ad70627fc2b6d5036e`, equal to the hash recorded in the decision log (match).
- Result JSON `data/backtest_out/research_x_capture_1_2026-09-22.json`: SHA-256 `c6ab1521577183a4c103ca51740ceafc99767cfe5f43f8e212c159cb0c96e73e` (matches the recorded value).
- Result report `reports/research_x_capture_1_2026-09-22.md`: SHA-256 `3bcad0086dda80247dd908c3b536e1ae21573f4455028e0c62796e6eaea26b1c` (matches).
- File modification times: 2026-09-22 23:12:03 (prereg), 23:31:25 (result and report).
- Git: the prereg, result and decision-log entries were first committed in `b780b10` on 2026-09-23 13:43:45 +0200, after the 2026-09-22 execution.

Finding: content identity is established for these files. The commit chronology is later than the events they record. The 54-date cohort is the same export used by NS-1, H4C and H4D (SHA-256 `87541cc5...`), so it is not independent of earlier research lines.

### 2.8 C8: RX-CAPTURE-1-ECON (lock claim contradicted)

- Committed version (`e0e7b38`, 2026-09-23 13:45:54 +0200): header "Version: v0.1-DRAFT", "Status: DRAFT - NOT LOCKED. Requires Meriç approval." SHA-256 of the committed content `9def385a96f71ba7ca0df5abf4110ecb9546ba8f93bec197ab94d2d8bc20eec5`.
- Working copy: "Version: v0.3-LOCKED", "Status: APPROVED / LOCKED - Meriç approval 2026-09-23". Modified 2026-10-09 13:12:24. Current SHA-256 `c794055932dec2ec9ccffac5cfed1e5c58094fad761614e96d036f62bc1cf404`. Git status `M`; diff: 143 insertions, 14 deletions.
- Decision log entry for the lock (2026-09-23) records SHA-256 `6b210259b4dbaac4d3e2df64faaaf34f700a1b80a1b283dbb479ea27fdb212fb`. This matches neither the committed version nor the working copy.
- Result artifact `data/backtest_out/research_x_capture_1_econ_2026-09-23.json` exists. The protocol version it used is not recorded.
- Note: `scan_export_latest.json` and `snapshot_latest.json` also carry modification time 2026-10-09 13:12:24. A bulk file operation at that time is possible. The cause is not established.

Finding: the claim that the economic-review protocol was locked on 2026-09-23 is contradicted by the repository. The file content at the recorded lock hash cannot be reproduced.

## 3. Classification summary

| Class | Meaning | Candidates |
|---|---|---|
| A. Documented freeze | Documented before results with verifiable content | C7 (hash match; commit chronology later) |
| B. Inferred from Git or metadata | Freeze inferred from commit dates or file metadata | C1 boundary declaration chronology (partial), C5 timestamps |
| C. Undocumented claim | Claimed sealed without evidence | C6 "not opened" (file absence only) |
| D. Cannot be established as independent | Dataset used in development or overlapping evaluated periods | C1, C2, C3, C4, C5 overlap, C6 |
| Contradicted by evidence | Claim conflicts with file content | C8 |

## 4. Access evidence

- No access log for any candidate was found.
- The state file for the fixed-target holdout does not exist (checked 2026-10-14).
- Multiple artifacts report locked-OOS results (section 5 of the risk register). Those results prove that OOS periods were evaluated; they do not show who evaluated them or when, beyond the artifact timestamps.
- Historical access cannot be fully verified.
