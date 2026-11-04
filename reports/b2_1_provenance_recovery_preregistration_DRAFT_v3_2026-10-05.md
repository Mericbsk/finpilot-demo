# B2-1 v3 - Provenance recovery draft package

Date: 2026-10-05 | Version: 3.0 DRAFT | Owner: Meric / Research
Status: DRAFT / NOT LOCKED / NOT RUN
Layer: Research / Governance. Preparation: Level A. Methodological adoption and
LOCK: separate explicit human approval required; proposals remain PENDING.
Production impact: NONE. Production authorization: NONE.

## 0. Status, scope and version boundary

This is a proposed successor to [v2](b2_1_provenance_recovery_preregistration_DRAFT_2026-09-23.md),
not an amendment to a locked study or an execution permission. V2 is preserved.
The observed v2 SHA-256 matches its decision-log draft reference:
`0ae40a66b1b9d2fbc38c9ae54494e3f496dea5bb5bb31a6adf51d6e4e4704c4e`.
That value is not a B2-1 LOCK and is not an input-manifest hash.

Change proposal versus v2:

- Preserve R2 as stored-derived-output recovery, separate from raw recovery.
- Remove external-cache agreement from decision-recovery eligibility.
- Separate integrity, identity, PIT, definition, consistency and recovery claims.
- Evaluate alternative channels before concluding NOT_RECONSTRUCTIBLE.
- Use feasible intervals with explicit rounding and saturation handling, rather
  than silently treating a point inversion as an exact historical value.
- Require enforced isolation evidence; no automatic non-blind fallback.
- Specify synthetic expected outcomes and verification of epistemic claims.

Authority remains [the decision log](../docs/governance/decision-log.md),
[core rules](../_instructions/00-core.md) and the research authority mapped in
[docs/INDEX](../docs/INDEX.md). This draft does not create a new global policy.
Its proposed rules apply only if this specific study is separately approved.

B2-0 remains INCOMPLETE / VERIFICATION_MISMATCH; no retrospective reclassification.
B2-AUTH human decisions remain pending. B2-2 is conditional; B2-full is not
opened. B4 implementation, flags, publication and deployment are out of scope.
The user's preparation instruction authorizes drafting, not LOCK or real execution.
No historical outcome calculation, network refresh or recovery run accompanies
this document. No claim that a runner, isolation environment or verifier exists.

## 1. Research question

For the historical 2026-09-09 scan, which missing inputs or target decisions can
be reconstructed under the historical production definition, with which evidence
class and provenance limits? Report ATR, squeeze and risk-engine channels separately.

NOT_RECONSTRUCTIBLE is a valid completed research outcome, not an implementation
failure. Predictive performance, economic validity and production permission are
not estimands. Do not select a channel to obtain a preferred verdict.

## 2. Recovery targets and output vocabulary

| Target | Definition | Claim limit |
| --- | --- | --- |
| DAILY_ATR_PRODUCTION_VALUE | ATR(14) percentage used by production, after its four-decimal rounding | Not the unrounded ATR or the 15-minute export field |
| ATR_GE_4_DECISION | Whether the production daily ATR value is at least 4.0 | Threshold recovery does not establish an exact input |
| SQUEEZE_OFF_PRODUCTION_VALUE | Production squeeze value with OFF weights, after four-decimal rounding | Not a publication counterfactual or a new input estimate |
| SQUEEZE_OFF_GE_0_5_DECISION | Whether that stored-precision value is at least 0.5 | Invariance only for this target, not for ranking values |
| RISK_ENGINE_DEPENDENCY_TRACE | Whether historical risk fields reach membership, ordering or displayed content | Code-only trace; no numerical risk calculation |

Inspect all locked rows for inventory and integrity; report `entry_ok=True`,
`entry_ok=False`, missing and malformed eligibility separately. Recovery aggregation
uses the preregistered eligible population, not manually selected published rows.
False eligibility is NOT_REQUIRED for conviction, not a recovered false threshold.
Unknown eligibility is not silently converted to false or dropped.

## 3. Recovery channels

| Class | Operation | Permitted evidence claim |
| --- | --- | --- |
| R1 RAW_INPUT_RECONSTRUCTION | Recompute from identifiable historical inputs under the historical definition | Historical recovery only if identity, definition and PIT are sufficient |
| R2 STORED_DERIVED_OUTPUT_RECOVERY | Derive the feasible target set from stored production outputs and known components | Target/value recovery at the demonstrated precision; not historical raw-input identity |
| R3 CROSS_OUTPUT_CONSISTENCY | Check a second encoding against the same feasible latent value | Supporting arithmetic consistency only; cannot independently recover or rescue an unresolved target |
| R4 BOUNDED_INVARIANCE | Prove the target decision is constant across the complete admissible domain | Decision recovered by a bound; exact input unavailable |
| R5 EXTERNAL_SOURCE_CHECK | Check an external candidate with compatible definitions against stored outputs | Consistency only; never an automatic R1/R2/R4 upgrade |
| R6 ASSUMED_OR_IMPUTED | Estimate, select a convenient decomposition or fill missing values | Prohibited; not executed |

R2 is declared PRE-SEEN / NON-BLIND in the prior protocol. The prior observations
are documented in v2 section 4; this preparation does not recalculate them.
Isolation of a new runner cannot make already-seen evidence historically blind.
R3 and squeeze channels are intended to be blind, but their current blindness
and prior-access state are NOT_VERIFIED. Do not assert nobody has executed them.

The formula version proposed by v2 is git `ff9658a`. Resolve its full commit,
extract the required historical modules and verify the export call path before
LOCK. Current worktree code is not a substitute. Any definition mismatch must be
resolved before values are compared, not after a real outcome is seen.

## 4. Orthogonal evidence dimensions

For every row/channel/target, record the following independently:

| Field | Vocabulary / interpretation |
| --- | --- |
| recovery_methods | List of evaluated R1-R5 classes, including unsuccessful channels |
| recovered_target | One named target from section 2 |
| source_availability | AVAILABLE / NOT_FOUND / MISSING / NOT_APPLICABLE |
| integrity | MATCH / MISMATCH / MISSING / NOT_CHECKED |
| definition_match | PASS / FAIL / UNKNOWN / NOT_APPLICABLE |
| domain_validity | PASS / FAIL / UNKNOWN / NOT_APPLICABLE |
| temporal_validity | PASS / FAIL / UNKNOWN / NOT_APPLICABLE, with timestamp evidence |
| historical_identity | ESTABLISHED / NOT_ESTABLISHED / UNKNOWN |
| historical_input_recovered | TRUE / FALSE / UNKNOWN; FALSE means recovery was not established, not that the latent value is false |
| decision_recovered | TRUE / FALSE / UNKNOWN, separate from decision_value |
| decision_value | TRUE / FALSE / UNRESOLVED / NOT_REQUIRED |
| recovered_value | Exact-at-declared-precision value or null; never a midpoint imputation |
| feasible_set | Interval/bound descriptor, with precision and inclusivity convention |
| external_source_consistency | PASS / FAIL / NOT_TESTED / NOT_APPLICABLE |
| cross_output_consistency | PASS / FAIL / BOUNDARY / NOT_TESTED / NOT_APPLICABLE |
| pre_seen_status | PRE_SEEN_NON_BLIND / NOT_VERIFIED / VERIFIED_UNSEEN, with evidence |
| blindness_status | VERIFIED_ISOLATED / NOT_VERIFIED / FAILED, scoped to actor and phase |
| reason_codes | Explicit missing-field, rounding, identity or gate limitations |

Temporal FAIL is used only with evidence of invalid timing; absent provenance
is UNKNOWN. External value agreement can coexist with temporal FAIL or UNKNOWN.
It never establishes identity. Integrity MATCH proves unchanged bytes only.

## 5. Proposed acceptance rules

### 5.1 R1 historical recovery

Require integrity MATCH, definition PASS, domain PASS, historical identity
ESTABLISHED and sufficient PIT evidence before claiming HISTORICAL_INPUT_RECOVERED.
Value agreement alone is insufficient. A source with unknown identity or PIT is
reported with those limitations and does not satisfy this historical claim.
Do not replace daily ATR with 15-minute ATR or an earlier-date daily value.

### 5.2 R2 ATR target recovery

The proposed historical legacy definition is v2 section 8 and its historical
`compute_legacy_quality_score` implementation. Let C be its known non-ATR terms,
L the three-decimal stored score and x the normalized ATR term. Use the complete
set satisfying `L = round(10 * (C + 1.5 * x), 3)`, `0 <= x <= 1`.

Use a conservative stored-score interval `L +/- 0.0005`, widened by `1e-9`
in score units. Transform that interval into x, then intersect with [0,1].
An inverted midpoint outside [0,1] is not alone a DOMAIN_VIOLATION if the complete
rounding interval still intersects the domain. An empty feasible set is CONFLICT.

For x below saturation, ATR is `6*x`; at x=1, retain the upper tail ATR>=6,
not an exact ATR=6 claim. Intersect with the historical stored ATR precision
and nonnegative domain. Production four-decimal rounding and known-component
precision must be justified by the frozen call path. If known components cannot
be established at that precision, widen their domains using justified bounds or
report UNRESOLVED; do not treat them as exact by assumption.

ATR_GE_4_DECISION is recovered only if every feasible production ATR is >=4,
or every feasible production ATR is <4. A set crossing 4 is UNRESOLVED.
R1 conflict or R3 FAIL blocks acceptance. R3 BOUNDARY must remain visible;
it does not rescue an unresolved R2 target or establish historical identity.

### 5.3 R3 ATR supporting check

Freeze historical clipping, input normalization and Python round-half-even
semantics from `compute_v2_score`. Its integer-output interval is +/-0.5,
widened by `1e-9` in score units. Use the same candidate ATR and justified known
components as R2. Check feasibility against both output encodings, including
saturation and final [0,100] clipping; do not force an inverse where clipping
destroys uniqueness. No compatible value is FAIL; compatible boundary/clipped
cases are BOUNDARY; compatible non-boundary cases are PASS.

The v2 +/-0.08 ATR diagnostic is retained as a rounding-derived boundary warning,
not as permission to tune a tolerance or disregard an impossible joint encoding.
R3 only supports R2; shared upstream inputs do not make it independent provenance.

### 5.4 R4 squeeze bound

Use the frozen historical component domains s,f in [0,1], ON weights (0.7,0.3)
and OFF weights (0.5,0.5). For observed four-decimal ON value S, the latent ON
set is `[S-0.00005, S+0.00005]` intersected with [0,1], widened by `1e-9`
in factor units. Reject nonfinite/out-of-domain stored values; missing is not zero.

Optimize the OFF value `0.5*s + 0.5*f` across the complete joint feasible set
`0.7*s + 0.3*f` in that ON interval. Do not widen f independently while keeping
S fixed: uncertainty and the s/f constraint must remain coupled. The fixed-S
identity in v2 section 12b can be used only with this full uncertainty accounted for.

Apply production OFF rounding/clipping to the feasible set. A conservative
envelope widened by +/-0.00005 and `1e-9` is allowed for four-decimal rounding;
its implementation must be fixed before LOCK. TRUE requires the whole resulting
set >=0.5; FALSE requires the whole set <0.5; otherwise UNRESOLVED. A conservative
UNRESOLVED is preferable to an unsupported exact-boundary classification.
This recovers only the threshold, never a unique continuous OFF score by midpoint.

### 5.5 R5 external consistency

Definition check precedes comparison. Establish provider, unit (fraction versus
percent), timestamp and field meaning. Mismatched definition is NOT_APPLICABLE,
not an automatic unit conversion. Unknown definition blocks the value comparison.
With compatible definitions, apply the fixed historical formula to candidate
values; compare against stored four-decimal output using +/-0.00005 plus `1e-9`
in factor units. Report agreement and temporal/identity limits separately.

The July cache is not assumed PIT-valid for September. An R5 agreement cannot
make an unresolved squeeze target recoverable, cannot establish the historical
OFF value and cannot qualify as historical raw-input recovery. Only independently
established historical provenance can change a source's classification, before
outcome comparison, with an explicit record and protocol-compatible scope.

### 5.6 Risk-engine code-only channel

Trace the frozen risk-engine fields into public membership, sorting, cap/notional
and displayed content. Record source references and NONE / PRESENT / UNRESOLVED
per dependency. Do not compute actual values, transmit an order, choose position
sizes or execute distribution code. Content impact is not added to the B2-0 estimand.

## 6. Input manifest template - deliberately incomplete

One byte artifact has one ID/hash and may have several role references. Historical
artifact, recovery source, code definition and stored output are not interchangeable.
The template below is not a valid LOCK manifest: actual paths, SHA values, inventory
and provenance assertions are intentionally unset. Filling metadata is not a real
recovery run; deriving target values or testing real consistency before LOCK is prohibited.

```json
{
  "schema_version": 1,
  "study": "B2-1",
  "protocol_version": "3.0-DRAFT",
  "status": "TEMPLATE_NOT_LOCKABLE",
  "locked": false,
  "execution_authorized": false,
  "real_execution_performed": false,
  "proposed_historical_commit_short": "ff9658a",
  "historical_commit_full": null,
  "protocol_sha256": null,
  "manifest_sha256": null,
  "artifacts": [
    {
      "id": "historical_scan_export",
      "roles": ["historical_artifact", "stored_output"],
      "path": null,
      "staged_relative_path": "inputs/historical_scan_export.json",
      "sha256": null,
      "required": true,
      "scope": "2026-09-09 complete scan; all rows, including error/template rows",
      "date_range": ["2026-09-09", "2026-09-09"],
      "source_timestamp": null,
      "allowed_fields": ["symbol", "entry_ok", "score_input", "legacy_quality_score", "v2_score", "squeeze_factor", "conviction_tier", "feature_timestamps", "scan_id"],
      "integrity": "NOT_CHECKED",
      "historical_identity": "UNKNOWN",
      "temporal_validity": "UNKNOWN",
      "definition_match": "UNKNOWN"
    },
    {
      "id": "raw_cache_inventory",
      "roles": ["recovery_source"],
      "path": null,
      "staged_relative_path": "inputs/raw_cache_inventory.json",
      "sha256": null,
      "required": true,
      "scope": "all candidates found by the frozen inventory search; explicit absent-source evidence allowed",
      "date_range": null,
      "source_timestamp": null,
      "allowed_fields": ["source_id", "path", "sha256", "provider", "definition", "available_at", "observation_date", "availability"],
      "inventory_complete": false,
      "members": [],
      "integrity": "NOT_CHECKED",
      "historical_identity": "UNKNOWN",
      "temporal_validity": "UNKNOWN",
      "definition_match": "UNKNOWN"
    },
    {
      "id": "external_fundamentals_candidate",
      "roles": ["recovery_source"],
      "path": "data/fundamentals_cache.json",
      "staged_relative_path": "inputs/external_fundamentals_candidate.json",
      "sha256": null,
      "required": false,
      "scope": "R5 candidate only; no pre-lock value comparison",
      "date_range": null,
      "source_timestamp": null,
      "allowed_fields": ["symbol", "short_pct", "float_shares", "provider", "timestamp"],
      "integrity": "NOT_CHECKED",
      "historical_identity": "UNKNOWN",
      "temporal_validity": "UNKNOWN",
      "definition_match": "UNKNOWN"
    },
    {
      "id": "historical_code_definitions",
      "roles": ["code_definition"],
      "path": null,
      "staged_relative_path": "definitions/historical_code_manifest.json",
      "sha256": null,
      "required": true,
      "scope": "full historical commit; features, evaluate, score_engine, risk_engine and publication dependency definitions",
      "date_range": null,
      "source_timestamp": null,
      "allowed_fields": ["commit", "path", "sha256", "symbols", "call_path", "precision"],
      "inventory_complete": false,
      "members": [],
      "integrity": "NOT_CHECKED",
      "historical_identity": "UNKNOWN",
      "temporal_validity": "NOT_APPLICABLE",
      "definition_match": "UNKNOWN"
    }
  ],
  "role_indices": {
    "historical_artifact": ["historical_scan_export"],
    "recovery_source": ["raw_cache_inventory", "external_fundamentals_candidate"],
    "code_definition": ["historical_code_definitions"],
    "stored_output": ["historical_scan_export"]
  },
  "inventory_search": {
    "roots": ["data", "data/backtest_out", "reports", "cache_if_present"],
    "git_history": "tracked data files; exact revision range to be filled before lock",
    "revision_range": null,
    "completed": false,
    "classify_before_value_comparison": true
  },
  "blind_execution": {
    "status": "NOT_VERIFIED",
    "non_blind_fallback_authorized": false,
    "isolation_evidence_sha256": null,
    "runner_bundle_sha256": null,
    "verifier_bundle_sha256": null,
    "runtime_and_dependency_manifest_sha256": null,
    "synthetic_suite_sha256": null,
    "synthetic_gate": "NOT_RUN"
  }
}
```

Before LOCK, enumerate every inventory/code member with its path, hash, role,
field definition, timestamp basis and allowed use. A directory name or mtime alone
is not provenance. Record optional absence explicitly; required integrity failure
stops the affected channel, and an incomplete core manifest blocks the study.

Search the v2 inventory scope including tracked data history, with exact revision
range and handling of untracked/dirty files recorded. Inventory work may inspect
metadata/schema/source definitions, not compute recovery outcomes. Keep research
result files found in reports/backtest_out out of the blind bundle. A separate
non-blind custodian performs inventory and staging; the runner does not crawl the repo.

Do not put secrets, personal identifiers, full environment dumps or unrelated
message content in the manifest. No current-data download or cache overwrite.
If the enriched EOD CSV is proposed as a source, record its actual date range:
it is not automatically a September daily-ATR input or an R1 source.

Avoid a self-hash cycle: the external manifest's own SHA and the protocol SHA
are recorded in the LOCK receipt, not inserted into the bytes they hash. At
finalization remove these two null self/reference placeholders from the manifest
and attach both hashes in the receipt after the immutable protocol and manifest
are finalized. This is preparation only; the template above has no lock identity.

## 7. Blind Execution Contract

### 7.1 Allowed artifacts and phases

The runner may read only the finalized normative protocol, its manifest, staged
historical production artifacts, enumerated historical definitions, implementation
bundle, pinned runtime/dependencies and synthetic fixtures with synthetic expected
outcomes. Synthetic expected outcomes are not expected real-data verdicts.
Only member-level hashed files may be mounted; a directory-wide data/reports mount
does not satisfy the allowlist. Preserve full population membership; no selected
real rows or post-result evidence chosen to make a conclusion pass.

The runner must not access B2-0 research result JSON, independent verifier output,
prior B2-1 results, decision-log interpretations, conversation/transcripts, actual
expected verdicts or manually selected outcome evidence. Original v2 contains
pre-seen observations and is a review reference, not an automatic runner input.
Normative rules and evidence-class definitions belong in the approved protocol;
review conversation is not a runner briefing.

### 7.2 Enforced isolation, not a prompt promise

A human-authorized custodian must provide an isolated filesystem/process boundary
with no host-workspace mount, git object store, editor/MCP workspace access, secrets,
network or inherited research context. A newly spawned agent with unrestricted
workspace tools is not VERIFIED_ISOLATED. Access restrictions must cover both
runner authoring and execution, not only a subprocess launched afterwards.
Do not provision containers, accounts or ACL changes as part of this draft.

Evidence must include bundle hashes, effective mounts/permissions, runtime identity,
allowlist read checks, forbidden-path/network access failures and scoped access
records. No logs containing secret contents. VERIFIED_ISOLATED is a claim supported
by these checks and reviewer assessment, not proof against every possible attack.

Status is VERIFIED_ISOLATED only when these checks pass; absent evidence is
NOT_VERIFIED; a successful forbidden access or known leakage is FAILED.
NOT_VERIFIED or FAILED blocks a claimed blind run under this draft. No automatic
NON_BLIND_EXECUTION fallback: any such alternative needs a separately approved,
versioned pre-lock scope. The prior R2 PRE_SEEN_NON_BLIND label is never erased.

### 7.3 Outputs and verification separation

Runner writes only a new designated research output directory. It cannot modify
inputs, production state or historical outputs. Its own newly computed in-memory
result may be serialized; earlier outputs are not inputs. The second reproducibility
run starts without access to the first run's outputs. A custodian compares bytes.

Verifier computation first uses the approved protocol and allowed inputs without
runner results. After its own computation is frozen/hash-recorded, comparison phase
may read both outputs, isolation evidence and the approval receipt. Record this
phase transition. A verifier may inspect lineage evidence for classification but
must not silently use a forbidden prior result as a numerical source.

Separate actors/implementations and access records are required before calling
verification independent. The drafter checking its own document is not independent
scientific verification. No agent is launched by this package.

## 8. Synthetic validation plan - expected outcomes, NOT RUN

Freeze fixtures, expected classifications, interval conventions and test-suite hash
before LOCK. Run the suite only after LOCK, before any real outcome calculation.
Use artificial values with no copied historical rows. Test both producer precision
and recovery precision; true ground-truth labels are separate from recovered labels.

| ID | Artificial case | Required expected outcome |
| --- | --- | --- |
| S01 | Production ATR=3.9999; C=0; stored LQS=10.000 | Ground-truth threshold FALSE; R2 threshold UNRESOLVED because score precision spans 4 |
| S02 | Production ATR=4.0000; C=0; stored LQS=10.000 | Ground truth TRUE; R2 UNRESOLVED, not exact recovery |
| S03 | Raw ATR=3.99996 rounded to four decimals | Production ATR=4.0000; production threshold TRUE; raw threshold FALSE; never substitute one target for the other |
| S04 | Raw ATR=3.9999 rounded to four decimals | Production value remains 3.9999; threshold FALSE |
| S05 | Stored LQS=9.990; C=0 | All feasible production ATR values below 4; R2 decision FALSE |
| S06 | Stored LQS=10.010; C=0 | All feasible production ATR values above 4; R2 decision TRUE |
| S07 | Production ATR=6 and ATR=8; C=0; LQS=15.000 | Same saturated output; threshold TRUE, exact ATR not recovered; upper feasible tail retained |
| S08 | Stored LQS=0; C=0 | Feasible set includes zero; no false domain conflict from a negative interval endpoint |
| S09 | Stored LQS=-0.001; C=0 | Rounding interval cannot intersect the permitted domain; CONFLICT |
| S10 | Round-half-even ties at artificial positive/negative score boundaries | Producer agrees with pinned runtime; conservative inverse contains every producer-consistent target, including ties |
| S11 | R2 interval compatible with an unclipped V2 output | R3 PASS when non-boundary; still no historical input identity |
| S12 | V2 output incompatible with every R2-feasible ATR | R3 FAIL; target acceptance blocked; CONFLICT |
| S13 | V2 saturation/clipping or ATR interval at threshold boundary | R3 BOUNDARY where compatible; no forced exact inverse or R2 rescue |
| S14 | Stored ON squeeze=0 | R4 threshold FALSE under the full rounding envelope; exact short/float inputs not claimed |
| S15 | Stored ON squeeze=1 | R4 threshold TRUE; exact OFF value or historical inputs not claimed |
| S16 | Stored ON squeeze=0.5 with multiple feasible s/f pairs | R4 UNRESOLVED; no arbitrary decomposition or midpoint OFF value |
| S17 | Stored squeeze negative, above 1, NaN or infinite | Invalid stored input is CONFLICT; no silent clipping of malformed artifact |
| S18 | Missing squeeze or ATR component | Missing remains unknown; no implicit zero; alternate admissible channels evaluated |
| S19 | External short input uses percent rather than fraction | Definition FAIL / comparison NOT_APPLICABLE; no guessed conversion |
| S20 | R5 matches stored ON output but identity absent/PIT invalid | External consistency PASS, identity NOT_ESTABLISHED, historical recovery FALSE; no continuous OFF or decision recovery from R5 alone |
| S21 | Raw source NOT_FOUND but R2 recovers the threshold | DECISION_RECOVERED; not early NOT_RECONSTRUCTIBLE |
| S22 | Raw source absent, R2 unresolved, R4 invariant | BOUNDED_RECOVERY for the target only |
| S23 | R1 and R2 disagree under established compatible definitions | CONFLICT; no preferred-source override |
| S24 | Hash mismatch, missing required member or incomplete inventory | Integrity gate STOP; no affected real channel execution |
| S25 | Forbidden path accessible or isolation evidence missing | FAILED / NOT_VERIFIED respectively; STOP, not automatic non-blind fallback |
| S26 | No eligible rows or unknown eligibility | No vacuous RECOVERABLE; explicit NO_ELIGIBLE_ROWS / eligibility limitation |
| S27 | Deterministic output with reordered object keys/nonsemantic runtime time | Canonical deterministic payload; observational timestamps outside reproducibility payload |
| S28 | Scalar outside an exact known-component domain; unknown component precision | Domain CONFLICT only if the justified full feasible set is empty; otherwise bound or UNRESOLVED |

S11-S13 must be expanded into exact synthetic tuples and expected encodings before
LOCK; labels alone are not executable fixtures. S10 and S28 require exact producer
precision cases under the pinned historical runtime. Joint S-rounding bounds must
also be tested near squeeze threshold crossings, with oracle feasible-domain checks.
The suite specification is incomplete until these concrete fixtures are reviewed
and hashed. No claim of synthetic PASS appears in this draft.

For non-boundary arithmetic use the specified margins, not a tolerance tuned on
real rows. If any required synthetic case fails: STOP. No same-locked-version
patch-and-continue; prepare a new reviewed version and a new LOCK receipt before
real execution. Any defect does not authorize changing a production threshold.

## 9. Real execution protocol - proposed, not authorized

1. Finalize definitions, inventory, fixtures, runtime, runner/verifier bundles and
   enforced isolation evidence without computing real recovery outcomes.
2. Obtain explicit Meric approval of the exact finalized protocol/manifest/bundles.
   Record SHA-256 values and execution scope in the decision log BEFORE execution.
   A draft receipt, chat agreement or file hash alone is not a LOCK.
3. In the isolated environment verify every required hash and isolation gate.
4. Execute the frozen synthetic suite. Every required case must PASS; otherwise STOP.
5. Execute all preregistered real channels on the frozen historical population.
   No network refresh, cache repair, env flag mutation, distribution import with
   side effects, production DB initializer or publication endpoint.
6. Repeat from a clean output-free environment with identical locked inputs and
   runtime. Require byte-identical canonical results; record operational timestamps
   separately. Nondeterminism stops acceptance and must be investigated openly.
7. Perform independent compute-then-compare verification under section 7.3.
8. Deliver channel results with limitations; human decisions remain separate.

Source discovery after LOCK is not permission to add a new input opportunistically.
Report it separately; a proposed expanded manifest needs versioning/review/relock
before it contributes to the locked result. Do not reopen B2-0 or closed studies.

## 10. Classification and aggregation rules

Evaluate R1, R2 applicability, R3 support, R4 applicability and R5 consistency with
separate records; raw-source absence alone does not decide the final classification.
Source incompatibility is NOT_APPLICABLE for that source, not a failed study by itself.
Missing metadata is not proof of source invalidity or a contradictory value.

Per target distinguish:

- HISTORICAL_INPUT_RECOVERED: sufficient R1 evidence for this exact claim.
- DECISION_RECOVERED: admissible R2 proves the target decision, with its non-blind
  and identity limits. Does not assert exact historical input.
- BOUNDED_RECOVERY: R4 proves target invariance, not a recovered input value.
- CONSISTENT_EXTERNAL_SOURCE: R5 agreement only, with temporal validity orthogonal.
- UNRESOLVED: a decision feasible set crosses the threshold or lacks required support.
- CONFLICT: incompatible admissible evidence, empty domain or explained protocol gate failure.
- NOT_REQUIRED: outside that target's eligible population; not a recovered result.

Per numerical target aggregate all eligible rows:

- RECOVERABLE_AT_TARGET: every eligible row has an admissible recovered target and
  no conflict; count R1/R2/R4 contributions separately. This is not input recovery.
- PARTIALLY_RECOVERABLE: at least one admissible recovered target and at least one
  unresolved row, with all row IDs and reasons retained.
- NOT_RECONSTRUCTIBLE: no eligible row has an admissible recovered target after
  all preregistered applicable channels have been evaluated; report external
  consistency separately. Do not apply this to unexecuted or blocked channels.
- PROVENANCE_INSUFFICIENT: required lineage/definition/eligibility evidence prevents
  evaluating the claim; not a numerical FAIL. Preserve any partial channel evidence.
- CONFLICT: any accepted-source conflict or failed protocol gate; report affected scope.

Zero eligible rows is NO_ELIGIBLE_ROWS, never vacuously RECOVERABLE_AT_TARGET.
Unknown eligibility prevents a complete-population recovery claim. Report these
as execution/coverage reasons, not new scientific success categories.
Execution state NOT_RUN / BLOCKED / COMPLETED is distinct from research classification.
Risk-engine code trace uses section 5.6, not numerical row-recovery aggregation.
There is no combined ATR+squeeze+risk verdict or automatic B2-2 opening.

## 11. Independent verification contract

The verifier checks numerical agreement AND epistemic classification:

1. Exact protocol/manifest/code/runtime identity and input inventory coverage.
2. R1/R2/R3/R4/R5 applicability, definition and evidence strength.
3. No R5 agreement promoted to historical identity or continuous OFF recovery.
4. PIT PASS/FAIL/UNKNOWN based on evidence rather than file hash or mtime alone.
5. No premature NOT_RECONSTRUCTIBLE or dropped unresolved/unknown-eligibility rows.
6. Rounding, half-even, saturation, feasible-set coverage and threshold semantics.
7. Synthetic gate, isolated authoring/execution and pre-seen declarations.
8. Reproducibility and verdict generation from frozen rules, not expected results.

Report VERIFIED_CONSISTENT / VERIFICATION_MISMATCH / VERIFICATION_INCOMPLETE with
scoped reasons; do not silently choose the preferred implementation. A mismatch
does not retrospectively modify B2-0. An independent verifier has not been assigned
or run by preparation of this document.

## 12. Failure conditions and LOCK checklist

Before LOCK all boxes must be satisfied with evidence:

- [ ] Methodological changes and exact v3 normative text explicitly approved.
- [ ] Full historical commit/call paths, definitions and precision verified.
- [ ] Manifest inventory, member hashes, temporal/identity evidence and optional absence finalized.
- [ ] Exact revision range and frozen historical population identified.
- [ ] Concrete synthetic fixtures and expected outcomes reviewed and hashed.
- [ ] Runner/verifier bundles and runtime/dependencies frozen without real outcomes.
- [ ] Authoring and execution isolation demonstrated; no unapproved non-blind fallback.
- [ ] Protocol/manifest hashes externally recorded without self-hash cycles.
- [ ] Named operator/verifier, permitted output paths and execution scope approved.

All boxes are currently unchecked. The manifest contains null required hashes;
blindness is NOT_VERIFIED; synthetic gate NOT_RUN. Therefore NOT READY TO LOCK.
Integrity mismatch/missing required input, forbidden access, invalid domains,
unexplained definition mismatch, synthetic failure, nondeterminism, real-result
tuning or access leakage cause STOP and an explicit report. No automatic repair,
silent threshold change or continuation under the same failed lock.

## 13. Reporting and preparation receipt

Future result payload must include study/protocol/manifest hashes, runtime and code
identity, row population/eligibility, per-channel evidence dimensions, feasible
sets and reason codes, coverage, synthetic gate, access/isolation evidence,
reproducibility and verification status. Separate scientific fields from operational
timestamps. Do not include personal data, secrets or transaction-direction advice.

Human-readable findings reference the frozen payload and disclose missing/blocked
channels, external consistency and pre-seen/non-blind evidence without upgrades.
An incomplete result is not relabelled a failed implementation or a production ban.
No recovery result implies predictive validity, economic viability, user-facing
impact or permission to enable a flag or publish.

Current delivery is this single draft package: manifest TEMPLATE, execution
contract PROPOSED, synthetic suite SPECIFIED_NOT_RUN, real run NOT_RUN, independent
verification NOT_PERFORMED. Preparation checks may validate document syntax,
template structure, links and unchanged v2 identity; they are not study results.
Next step: human review of this package and completion of the explicit pre-lock
gaps. No automatic lock or research cascade is authorized.
