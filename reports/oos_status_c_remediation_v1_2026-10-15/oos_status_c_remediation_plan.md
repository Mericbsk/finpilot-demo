# OOS Status C Remediation Plan (v1)

- Date: 2026-10-15
- Question: Investor question 4 (independence of the out-of-sample set and of the evaluation gate). Remediation of Status C from [oos_independence_audit_v1_2026-10-14](../oos_independence_audit_v1_2026-10-14/).
- Status: read-only audit. The prospective gate in section 5 is PROPOSED / NOT APPROVED.
- Restrictions observed: no sealed OOS outcome or holdout row was opened; no performance metric was computed; no production code, data, threshold, decision-log entry or historical file was changed.
- Recommendation: C. USE A NEW PROSPECTIVE EVALUATION PERIOD (section 7).
- Time convention: workstation local time is UTC+2 (verified: `frozen_at` 2026-08-05T11:31:08Z matches the local file time 13:31:08). All times below are UTC.

## 0. Method and limits

Sources: the four previous Status C reports; read-only Git history (`log`, `show`); SHA-256 of metadata and protocol files; VS Code Local History index files (`entries.json`) and their saved snapshots for the cited research files.

Limits of the new evidence:

- Local History records editor saves in the Windows user profile. It is not an audit log, is not tamper-evident, and records no reads.
- A snapshot time shows when a file was saved in the editor. It does not show when an analysis was run, and it does not capture changes made outside the editor (scripts, bulk operations). A file modification time is not proof of a freeze.
- Where earlier snapshots of planning documents were checked for known result strings, only presence counts were recorded.

## 1. Answers to the required questions

1. Why was Status C assigned? Three causes: (a) the locked-OOS set and overlapping windows were evaluated before any independent freeze, and later reused; (b) no hash-anchored freeze or access log exists for the trading-strategy OOS or the PIT holdout, and "not opened" rests on file absence or self-written timestamps; (c) several gate thresholds are non-numeric and status claims conflict. Separately, the tested offline proxy is not the production ranking.
2. Which gaps can still be resolved? Chronology of several documents (now partly resolved, section 2), the lock record of RX-CAPTURE-1-ECON (now reproducible, section 2, F12), the thresholds of the fixed-target runner (partly resolved), the status register, and the input-data inventory. Historical access cannot be resolved.
3. Which historical facts cannot be established? Who read the OOS sets and when; whether the 2026-05-21 boundary was chosen after an earlier exploration of the same data; whether any locked-OOS outcome was seen before the first recorded artifact; which fixed-target code version produced the 2026-08-05 run beyond editor evidence; the survivorship and corporate-action status of the price data; the history of the 2026-09-22 result report (no editor record).
4. Can the current OOS dataset still support an independent test? No. The 2026-05-21 locked-OOS set was evaluated on 2026-07-15 and reused in September. The PIT holdout dates lie inside periods already evaluated. The fixed-target holdout partitions are inconsistent between runs. Option B (section 4) is not available.
5. Is a new prospective evaluation period required? Yes.
6. What is the minimum safe next step? A human decision to adopt option C with a fixed freeze point, followed by the protocol and code pinning steps in section 7. Preservation of the local-history evidence (option A) should run in parallel; it does not change the answer to question 4.
7. Which decisions require human approval? See section 7.2.

## 2. Findings register

Status column: "carried" = from the previous audit, not re-verified here; "revised" = changed by this audit.

| ID | Claim under review | Evidence examined in this audit | Evidence still missing | Problem type | Resolvable without OOS outcomes |
|---|---|---|---|---|---|
| F01 | 2026-05-21 locked-OOS set reused after its evaluation (R1). Status: carried | Previous report; reuse documented in September artifacts (not re-read) | None for the fact | Contradictory: reused evaluation set | No. Cannot be repaired retrospectively |
| F02 | Boundary chosen after seeing results (R2, C1). Status: revised (partly) | Boundary text present in the first editor snapshot of the score-formula report, saved 16:07:04Z. The first OOS artifact, common_buy_accuracy.json, was generated 16:52:02Z. Git first contains the boundary at 18:18:03Z (commit db065bf). The test plan with locked-OOS wording was first saved 14:09:49Z | Any record of analysis of the same data before 14:09Z; the reason for the boundary value | Partly resolved; prior exploration unrecorded | Partly (documentation only) |
| F03 | Exit profile ranked on the locked OOS (R3). Status: carried | v2_exit runner first saved 17:37:17Z; its artifact generated 17:37:26Z; ranking document committed 18:18:03Z | Editor history of the ranking document (not checked) | Sequence conflict | No, for independence. Ordering can be checked |
| F04 | Gate defined after results (R4, G2 to G3). Status: revised (partly) | Gate text present in the test-plan snapshot saved 14:09:49Z: "lift > 1 or positive expectancy", three time slices, median rule, random baseline and minimum n referenced without numbers, and "locked OOS yalnızca bir kez açılmalıdır" | Numeric random baseline, minimum n and failure threshold; no snapshot before 14:09:49Z | Partly resolved (text chronology improved; numeric gaps remain) | Partly |
| F05 | 2026-06-26 cut reused; 2026-07-06 boundary moved (C2, C3). Status: carried | Previous report | Not applicable | Repartition after evaluation | No |
| F06 | 2026-01-01 IS_END split (C4). Status: carried | Not checked in this audit | Artifact date; editor history of the scripts | Unresolved historical fact | Possibly (history check not yet done) |
| F07 | PIT holdout is frozen (C5, R9, R10). Status: carried, with added detail | `pit_research_pipeline.py` first saved 11:31:03Z, five seconds before `frozen_at` 11:31:08Z; `fundamentals_sentiment_pilot.py` first saved 11:11:57Z. `created_at` is 11:31:24Z. Both timestamps come from code first saved that day. Hashes reproduced: protocol D8E7AC9B…, state 38781BB8…. File git-ignored. Holdout dates 2026-06-09 to 06-30 lie inside periods already evaluated | Independent freeze record; access record | Unresolved; prior exposure | No |
| F08 | Fixed-target thresholds committed after the 2026-08-05 run (R5, G11 to G13). Status: revised | Editor snapshot saved 2026-08-04 13:19:40Z already contains FDR alpha, minimum DSR, minimum period n and the holdout-state check. No editor save occurs between that snapshot and 2026-08-06 11:05:25Z. Commit 09429f2 is at 10:31:17Z | Proof that the 2026-08-05 run used that snapshot (inference only, unless the file changed outside the editor) | Earlier "after the run" claim revised: thresholds predate the run in editor history | Partly |
| F09 | Fixed-target holdout is "not opened" (C6, R6, R7). Status: carried | `locked_holdout_opened.json` absent. `LockedHoldoutGuard` appears only in research/protocol.py and tests. Runners only check the default path | Access log; any read record | Historical access unverifiable; guard not enforced | No, for history. Yes, prospectively |
| F10 | Two runs define different holdout partitions (C6). Status: carried | Previous report (2022 / 0 / 22,709 versus 14,515 / 11,588 / 269) | Explanation for the difference | Documented inconsistency | No |
| F11 | RX-CAPTURE-1 lock (C7, R12, R13). Status: verified | Decision-log hash d0baa618… equals the editor snapshot saved 21:12:03Z (first draft 20:58:42Z) and the current file (24,320 bytes). The result report has modification time 21:31:25Z and no editor history | Dataset freeze; independence | Lock verified; dataset not an OOS set | Lock: done. Independence: No |
| F12 | RX-CAPTURE-1-ECON lock contradicted (C8, R11). Status: revised | Decision-log hash 6b210259… equals the editor snapshot saved 12:49:07Z (v0.3-LOCKED, 11,741 bytes, CRLF line endings). The working copy (modified 11:12:24Z on 2026-10-09, 11,522 bytes, LF line endings) is identical after normalizing line endings (SHA-256 of normalized text c794055932… in both). The committed version (e0e7b38) is v0.1-DRAFT | Git-anchored lock; reason for the line-ending change | Previously "contradicted". Now reproducible from local history. The 2026-10-09 change is a line-ending change, not a content change (verified at byte level) | Largely yes |
| F13 | Median degenerate for RX candidates (R14). Status: carried | Decision-log entries; previous report | None | Documented methodological limit | Prospectively |
| F14 | Multiple comparisons (R15). Status: carried | 3,120 configurations and 1,012 FDR discoveries (previous report; counts not re-verified) | Family-wise control on any OOS set | Documented selection pressure | No, historically |
| F15 | Tested method differs from production (R16). Status: carried | Offline proxy `alpha_v2_offline_score_v1`; evidence matrix PARTIAL; decision-log entries "NOT RECONSTRUCTED" and "Formula equivalence remains unproven" | Production ranking and equivalence test | Unresolved; code work required | No. Requires reconstruction |
| F16 | Data versions, corporate actions and survivorship (R17 to R19). Status: carried | Input files and modification times listed in the previous report | Data version per artifact; vendor history; delisting records | Unrecorded historical facts | Partly |
| F17 | Contradictory status claims (R8). Status: carried | Previous report | None | Documentation contradiction | Yes (update the status register) |
| F18 | Access policy postdates the evaluations (R22). Status: verified | Orchestrator v2 first editor save 2026-09-22 20:21:12Z; committed b780b10 on 2026-09-23 11:43:45Z. All evaluations in the record run 2026-07-15 to 2026-09-09 | None | Chronology | No, historically. The policy can be adopted now |
| F19 | Decision-log gap, 2026-08-10 (R20). Status: carried | Previous report | None | Unrecorded decisions | No |
| F20 | Overlapping observations (R21). Status: carried | 5,748 rows on 4,318 symbol-days (previous report) | A deduplication rule | Methodological | Yes (prospective rule) |

## 3. Evidence gap matrix

Candidates:

- C1: trading-strategy locked OOS (boundary 2026-05-21). Sources: common_buy_accuracy.json, v2_exit_same_selection_results.json, test plan, score-formula report.
- C5: PIT / fundamentals-sentiment holdout (2026-06-09 to 06-30). Sources: fundamentals_sentiment_protocol.json, fundamentals_sentiment_holdout.json.
- C6: fixed-target holdout. Sources: run_fixed_target_research.py, fixed-target artifacts of 2026-08-05 and 2026-08-11.
- C7: RX-CAPTURE-1 (declared not an OOS set; lock only). Source: research_x_capture_1_preregistration_2026-09-22.md.
- C8: RX-CAPTURE-1-ECON. Source: research_x_capture_1_economic_review_preregistration_2026-09-23.md.

Codes: V = VERIFIED. P = PARTIALLY VERIFIED. N = NOT VERIFIED (includes items not checked in this audit). X = CONTRADICTED by evidence. NE = known not to exist (documented absence, or a verified absence of wiring or of a recorded value).

| # | Item | C1 | C5 | C6 | C7 | C8 |
|---|---|---|---|---|---|---|
| A | Candidate OOS dataset identified | V | V | V | V (not OOS) | P |
| B | Hash or equivalent integrity record | NE | P | NE | V | V |
| C | Freeze timestamp supported by evidence | P | N | N | P | P |
| D | Dataset boundary documented | V | V | X | V | N |
| E | Historical access or inspection history | N | N | N | P | N |
| F | Strategy version fixed before evaluation | X | N | P | P | P |
| G | Evaluation protocol available | P | P | P | V | V |
| H | Evidence that protocol predates outcome inspection | P | X | P | P | P |
| I | Primary metric defined | P | N | P | V | V |
| J | Acceptance threshold defined | P | N | P | V | V |
| K | Failure threshold defined | NE | N | NE | P | P |
| L | Inconclusive-result rule defined | P | N | N | N | N |
| M | Transaction-cost assumptions defined | P | N | P | V | P |
| N | Position-sizing rules defined | NE | N | N | N | N |
| O | Conditions for opening the evaluation set defined | P | P | P | P | N |
| P | Procedure for recording the final result defined | P | N | P | V | P |

Basis for key entries:

- B, C1: no artifact hash is recorded in the repository (previous report).
- B, C5 and C8: hashes reproduced in this audit (section 2, F07 and F12).
- C, C5: the only timestamps are written by the script itself, on the day its file was first saved.
- D, C6: the two runs define different partitions.
- F, C1: the scripts that produced the first locked-OOS artifacts were first saved 16:51:40Z (common_buy_accuracy.py, second save 16:51:55Z, artifact 16:52:02Z) and 17:37:17Z (runner, artifact 17:37:26Z). Earlier development outside the editor cannot be excluded.
- F, C6: no editor save between 2026-08-04 13:19:40Z and 2026-08-06 11:05:25Z.
- H, C5: the holdout dates lie inside periods already evaluated (R9).
- K, C1 and C6: no numeric failure threshold in the test plan or the runner (previous report).
- N, C1: no sizing rule in the OOS protocol (see the Q5 audit on position sizing).
- O, C5: `human_approval_required` is true in the protocol; no approval record exists.

## 4. Remediation options

### Option A: Recover existing contemporaneous evidence

- Found in this audit (UTC): test-plan snapshot 14:09:49; score-formula report with boundary 16:07:04; common_buy_accuracy.py 16:51:40 and 16:51:55; runner v2_exit 17:37:17; RX-CAPTURE-1 lock snapshot 21:12:03; ECON lock snapshot 12:49:07; fixed-target runner snapshots 2026-08-04 13:14 to 13:19:40; PIT script 11:11:57.
- Required evidence: preserved copy of the Local History folder; hash of each snapshot; comparison with the decision-log hashes.
- Recoverable: editor-level text at save times; the exact lock text for RX-CAPTURE-1 and ECON.
- Not recoverable: read or access logs; any analysis before the first recorded save; history of the 2026-09-22 result report; any file created outside the editor.
- Leakage or prior exposure: no new exposure. The boundary snapshot showed no result-string matches (count checks only).
- Supports an independent evaluation: No. It restores the chronology of documents. It does not restore the independence of the sample, which was evaluated on 2026-07-15.
- Dependencies and blockers: retention of the local profile; human approval to copy the folder out of the profile (not executed).

### Option B: Use an existing dataset whose independence can be established

- Required evidence: proof that a window was never inspected, with access records.
- Recoverable: nothing new on the current evidence.
- Not recoverable: the prior inspection of every post-2025-09 window. The decision log (2026-10-14, OOS usage audit) records that every post-2026-01-01 window appears in at least one evaluated artifact.
- Leakage or prior exposure: high. Choosing among windows by their outcomes would itself be selection on the outcome, which is prohibited.
- Supports an independent evaluation: No.
- Dependencies and blockers: no access logs exist. Status: NOT AVAILABLE on current evidence.

### Option C: Prospective, untouched evaluation period

- Required evidence: production scoring commit pinned; protocol committed to Git before the freeze point T0; signals recorded only from T0 onward; daily hashes of an append-only archive; access events recorded by the runner guard.
- Recoverable: nothing historical. The result is an independent test if T0 precedes all data in the window and no outcome is viewed before the window closes.
- Not recoverable: nothing.
- Leakage or prior exposure: low, provided the lock precedes T0 and outcome views are blocked until the window closes. The outcome horizon is up to 21 trading days (existing barrier design), so the window takes calendar time.
- Supports an independent evaluation: Yes, conditionally on the approvals in section 7.2.
- Dependencies and blockers: the evaluated method must be the production method (F15). Execution data (spread, fills) must be logged going forward (the Q5 audit found none). The position-size definition and the cap conflict (15 % in scanner/position_sizer.py versus 0.2 in core/config.py) must be resolved.

### Option D: New dataset or future period under a preregistered protocol

- Required evidence: data provenance and vendor history; survivorship-free constituents; proof that no member of the team has inspected the dataset; protocol committed before any inspection.
- Recoverable: nothing historical.
- Not recoverable: any exposure already present in the team's work (the same archive was inspected in Q3 and Q5 audits).
- Leakage or prior exposure: medium to high. Selection of the dataset must not follow its results.
- Supports an independent evaluation: Conditionally, only if the dataset is untouched and fixed before inspection.
- Dependencies and blockers: data acquisition, provenance and an external approval of the dataset choice.

## 5. PROPOSED prospective evaluation gate (NOT APPROVED)

No threshold in this section is derived from a historical result. Every numeric value is marked PENDING APPROVAL and must be set by a human before T0.

| Element | Proposed content | Status |
|---|---|---|
| Strategy and code version | Production scoring commit, pinned by hash at freeze. The offline proxy `alpha_v2_offline_score_v1` is not eligible. A production-equivalence test is required before freeze | PENDING APPROVAL |
| Dataset and temporal boundary | Signals with timestamps after T0 only. T0 = the commit time of the protocol file | PENDING APPROVAL (T0 date) |
| Freeze and integrity | Protocol committed to Git before T0; SHA-256 recorded in the decision log. Daily hashes of an append-only signals archive. No writes to the frozen window | Proposed |
| Authorized access roles | Named approver (human); analyst read-only role. The runner must call a guard that writes an access event (identifier, requester, time, dataset hash) before any read | PENDING APPROVAL |
| Statistical validity criteria | Mean gross barrier return per signal; 95 % interval by cluster bootstrap over signal dates; B and seed fixed in the protocol | PENDING APPROVAL (B, seed, interval rule) |
| Economic viability criteria | Mean and median net return after declared costs; results with the top 1 % and top 5 % removed reported alongside the full sample | PENDING APPROVAL |
| Execution feasibility criteria | Spread and fill data logged from T0; participation limit against dollar volume; entry rule (next session open or other); gap-fill rule for stops and targets | PENDING APPROVAL |
| Net transaction-cost methodology | Cost components, each with a named source, declared before T0. The scanner constant (0.20 pp) and the research scenarios (0.55 pp, 1.00 pp) are not sourced per component and must not be used as the base case without approval | PENDING APPROVAL |
| Position-sizing assumptions | Intended notional defined before T0. Current sources conflict (15 % in scanner/position_sizer.py, 0.2 in core/config.py); research notional 1,000 USD is illustrative only | PENDING APPROVAL |
| Minimum sample-size rationale | Minimum number of distinct signal dates and of signals. The historical record had 37 clusters with wide intervals; the number must come from a precision calculation with a human-approved effect size | PENDING APPROVAL (no number proposed) |
| Time and regime coverage | Minimum calendar span; regime labels defined before T0 from an external index series, not from the archive | PENDING APPROVAL |
| Uncertainty methodology | Cluster bootstrap by signal date, fixed seed, reported for mean and median | PENDING APPROVAL |
| Acceptance criteria | All three criteria above must pass: statistical lower bound, economic net mean at the declared base cost, and the execution rules. Numeric bounds PENDING APPROVAL | PENDING APPROVAL |
| Failure criteria | Upper interval bound below zero, or net mean at base cost not positive. Numeric bounds PENDING APPROVAL | PENDING APPROVAL |
| Inconclusive-result criteria | Interval includes zero, or sample below the minimum. An inconclusive result does not permit a protocol change or a re-run on the same window | PENDING APPROVAL |
| Conditions for opening the window | T0 reached; code commit and protocol hash in Git; approver recorded; guard active; outcome views hidden until the window closes | Proposed |
| Rules after evaluation | No change to protocol, code, thresholds, costs or window after T0. Any change requires a new untouched window. No re-run on the same window | Proposed |
| Independent reproduction | A second person reproduces results from the snapshot hash using the committed script. Tolerance PENDING APPROVAL | PENDING APPROVAL |
| Conditions requiring a new window | Any change to protocol, code, costs or sizing; any outcome viewed before close; any data correction affecting the window; any change to the production version | Proposed |

## 6. Corrections to the previous audit and to dependent documents

These are corrections of statements in the previous Status C report and in the German draft answer for question 4. None has been applied. Changes to investor wording are human decisions (Level C).

1. RX-CAPTURE-1-ECON (previous C8 and R11): the statement "the lock hash cannot be reproduced" is incorrect. The hash is reproduced from the editor snapshot of 2026-09-23 12:49:07Z. The working copy differs only in line endings. The lock is still not Git-anchored; the committed version is v0.1-DRAFT.
2. Test plan (previous R4): the statement "the gate was defined after the results" is partly superseded. The gate text exists in the snapshot saved 14:09:49Z, before the first OOS artifact (16:52:02Z). Numeric gaps remain.
3. Earliest declaration of the boundary (previous answer to question 4, section 1): the statement that the earliest reference is the artifact of 16:52 UTC is incomplete. The first Git-tracked reference is commit db065bf (18:18:03Z). Outside the repository, the editor history holds the boundary in a snapshot saved 16:07:04Z. Both facts should be stated.
4. Fixed-target thresholds (previous R5): the statement that the thresholds were committed after the 2026-08-05 run is superseded in its chronology. The thresholds appear in the editor snapshot of 2026-08-04. Commit 09429f2 is later, as stated.
5. The answer to question 4 states that the test plan was saved in the same commit as the results of the same day. Git supports that for commit db065bf. The editor history shows the test plan existed from 14:09:49Z, before the first OOS artifact (16:52:02Z). Both facts should be stated, and the wording revised by a human.
6. The answer to question 4 states that the ECON pre-registration cannot be verified by its stored hash. That statement is superseded by F12.

## 7. Recommendation and human decisions

### 7.1 Choice

C. USE A NEW PROSPECTIVE EVALUATION PERIOD.

Reasons:

- The existing sets cannot support an independent test. The reuse (F01), the overlap (F07) and the method mismatch (F15) are verified, and documents cannot repair them.
- Option A improves the chronology of several documents (F02, F04, F08, F12) but does not change the answer to question 4. It should run in parallel as preservation of evidence.
- Option B is not available on current evidence.
- Option D is possible but carries higher prior-exposure risk and needs provenance that does not exist yet.
- The evidence is adequate to choose C. The protocol parameters are not yet determined, so their approval is required before any window opens.

### 7.2 Decisions requiring human approval

1. Adopt option C, and set the freeze point T0.
2. Select the production scoring commit and approve the production-equivalence test (F15).
3. Set every PENDING APPROVAL value in section 5, including sample size, interval rule, failure and inconclusive bounds, and the cost base case.
4. Define the intended position size and resolve the cap conflict.
5. Approve the access roles, the approver, and the guard implementation (code change, Level B).
6. Approve preservation of the VS Code Local History evidence (copy out of the profile), and decide whether it is cited in investor material.
7. Approve the corrections in section 6, and the wording of any revised answer to question 4 (Level C).
8. Decide whether a decision-log entry is recorded for this plan. No entry was added in this audit, per the instruction to create only this report.

### 7.3 Minimum safe next step

1. Preserve the evidence listed in section 4, option A (human approval).
2. Correct the statements in section 6 in the status register and the draft answer (human approval).
3. Fix the protocol and the production commit before T0, then open the window only when all section 5 items are approved and recorded.

## 8. Not established

- Who read the locked-OOS, PIT or fixed-target sets, and when.
- Whether any analysis of the 2026-05-21 boundary data preceded the first editor saves on 2026-07-15.
- Which code version produced the 2026-08-05 fixed-target run, beyond the inference in F08.
- Survivorship, corporate-action treatment and data vintage (F16).
- Whether the production ranking matches the tested proxy (F15).
- Whether the 2026-09-22 result report existed in its final form before the lock snapshot (no editor record; modification time only).
