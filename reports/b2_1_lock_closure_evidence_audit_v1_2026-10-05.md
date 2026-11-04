# B2-1 LOCK Closure & Evidence Audit v1

Date: 2026-10-05
Layer: Research. Level: A - non-blind custodian metadata/static-source audit.
Final readiness decision: **LOCK BLOCKED**.
Methodology: APPROVED. Study: NOT LOCKED / NOT RUN.

This is a bounded first closure delivery, not a claim that every possible archive
or transitive production dependency has been exhausted. No normative v3 change,
scientific fixture execution, real recovery, risk calculation or production action.

Authority: [approved v3 protocol](b2_1_provenance_recovery_preregistration_DRAFT_v3_2026-10-05.md).
Approval: [decision log](../docs/governance/decision-log.md).
Machine evidence: [closure audit JSON](b2_1_prelock_closure_audit_v1_2026-10-05.json).
Baseline: [frozen candidate manifest](b2_1_prelock_manifest_candidate_v1_2026-10-05.json).

## Evidence Matrix

PASS is scoped to the stated claim, not study readiness. All blocker rows remain
blocking together; they are not mutually exclusive explanations.

| Gate | Status | Supported Claim | Missing Evidence / Closure Condition |
| --- | --- | --- | --- |
| Protocol identity | PASS | Approved v3 bytes unchanged | No execution authorization inferred |
| Methodology approval | PASS | Exact v3 approval recorded | Separate exact-bundle LOCK required |
| Historical source commit | PASS | Full ff9658aa commit and source members readable/hashable | Does not identify actual scan execution |
| ATR static path | PARTIAL | Daily input, producer precision, legacy/V2 caller and stored fields traced | Provider/PIT, actual branch and runtime; full dependency review |
| Squeeze static path | PARTIAL | Provider fields, gated producer, ON/OFF branches, precision and consumers traced | Actual historical inputs, flag/cache state and execution identity |
| Risk static path | PARTIAL | Risk-to-dynamic-sizing/cap/notional/public-candidate references present | Complete branch/display-consumer review; actual effects not computed |
| Export byte identity | PASS | Selected candidate bytes match frozen export SHA | Final artifact selection and lineage review |
| Population metadata | PASS | Every row retained; exact valid symbol membership/order hash; observed boolean states counted | Does not establish historical execution identity |
| Historical population / target eligibility | PARTIAL | 1801 rows and 1801 valid distinct symbols, no duplicate/missing symbol | Protocol-target mapping and scan identity review |
| Historical execution lineage | UNKNOWN | Bounded source/archive search documented | Original export-to-run-to-commit/config records required |
| Historical runtime identity | UNKNOWN | Historical source constraint files hashed; selected history pathspecs searched | Actual historical image/dependency/runtime evidence required |
| Inventory disposition | PARTIAL | Every baseline record has classification, reason and independent allowlist status | 2547 unresolved records; path-family candidates need source review |
| Final allowlist / staging | BLOCKED | No automatic authorization | Review exact members/fields; create staged artifacts and byte hashes |
| Fixtures / executable suite | PARTIAL | Original fixture candidate preserved | Human review, frozen expectations and isolated executable suite |
| Runner implementation | BLOCKED | Protocol specifies permitted inputs/phases | Separately restricted authoring, frozen bundle and runtime |
| Verifier implementation | BLOCKED | Compute-then-compare contract exists | Separate implementation/context; runner outputs inaccessible during compute |
| Authoring/execution isolation | BLOCKED | NOT_VERIFIED, no fake canary PASS | Effective restrictions, canaries, access records and reviewer assessment |
| Human LOCK receipt | BLOCKED | No LOCK recorded | Named actors, output scope and exact accepted bundle identities |

## Closure Findings

Historical references below use git commit
`ff9658aa189d8ff0cbb9f3a0fecddab8a50b5b35`, not the current worktree.
The JSON's `code_definition_evidence` supplies exact paths, file hashes,
function identities, line numbers, local calls and round expressions.

### ATR

- The historical `evaluate_symbol` input boundary, lines 365-375, gets the `1d` frame from prefetched data or `fetch_multi_timeframe`; actual provider/input lineage is not established.
- `compute_atr_pct`, lines 186-206, uses the last 14 true ranges, previous closes and final close; its production return is rounded to four decimals. Missing/invalid production data has a zero fallback. This source behavior does NOT authorize imputing missing research inputs as zero.
- The caller at lines 682-729 passes that daily result to conviction, legacy quality and V2. `compute_legacy_quality_score` contains normalization/clipping and three-decimal output; `compute_v2_score` contains saturation and integer rounding/clipping. No formula was executed here.
- Return construction at lines 817-821 stores legacy/V2/ranking outputs. The API export payload at lines 838-857 preserves result rows; lines 941-945 serialize JSON. Publication ranking references are in the snapshot builder's `_sort_key`.
- Known-component precision evidence includes four-decimal producer returns for relative volume, lottery and overnight factors. This supports source-definition review, not historical runtime or actual row-input recovery.

### Squeeze

- `compute_squeeze_factor`, lines 115-156, reads yfinance short-percent-of-float and float-share inputs, applies component constraints and chooses the ALPHA_V2 ON or OFF weights before four-decimal rounding/clipping.
- `get_alpha_features`, lines 339-362, may return a cached value before the gated computation. Actual historical cache/flag state remains unknown.
- `evaluate_symbol`, lines 581-588, receives the factor; its score input and legacy/V2/conviction callers preserve the dependency. The OFF branch is a historical source definition, not an OFF value recovered in this audit.

### Risk Dependency Trace - No Numerical Calculation

| Surface | Static Finding | Scope / Limitation |
| --- | --- | --- |
| Raw entry eligibility | UNRESOLVED | Source-order observations alone are not complete branch closure |
| Public membership | PRESENT | Risk size feeds cap; public-candidate and candidate-pool logic read cap rejection |
| Sorting | UNRESOLVED | Inspected sort keys use grade/tier, execution, probability and ranking score; complete indirect closure not claimed |
| Cap | PRESENT | Caller passes risk position size times price into position_cap |
| Notional | PRESENT | position_cap returns requested/capped notional; no value computed |
| Intermediate displayed/brief content | PRESENT | Risk fields are stored and read into brief/snapshot metrics |
| Final public displayed content | UNRESOLVED | Free-schema stripping removes selected risk metrics; all output/renderer branches not reviewed |

Risk references: `evaluate_symbol` lines 523-534, 673-680, 731-738 and 786-790;
`position_cap` lines 95-112; candidate-pool lines 39-50; snapshot-builder
public-candidate lines 123-131; free-schema field stripping lines 103-114.
Nothing here establishes a realized financial, publication or B2-0 effect.

### Population And Export Identity

Source candidate: ordinary 2026-09-09 export, matching the previously verified
published copy. Exact bytes remain frozen; no row filtering/deduplication performed.

- Rows: 1801. Valid distinct symbols: 1801. Duplicate symbols: 0. Missing/malformed symbols: 0.
- Observed `entry_ok`: TRUE 11; FALSE 1790; MISSING 0; MALFORMED 0. These are stored population metadata, not scientific recovery results or an approved target-eligibility verdict.
- Membership SHA-256: `68a6f44fd3d5692baf5fb82de77ee772ade5d15d47dbff87c18aafea851b1146`, covering original row index, exact valid symbol and observed boolean state.
- The historical export writer can generate a fallback scan_id from the symbol universe hash (lines 840-851). A scan_id field's presence therefore does not alone prove a unique execution. This does NOT assert the actual September export used that fallback.
- A generated run_id/time is not proof of commit, config, dependencies or provider state. Scan and publication remain separate events.

### Inventory And Archive Scope

All 9617 frozen baseline records, including the previously unclassified 7220,
received a reasoned metadata disposition. Counts over the entire baseline:

| Classification | Count |
| --- | --- |
| EXTERNAL_CANDIDATE | 6578 |
| DUPLICATE_REFERENCE | 168 |
| RESEARCH_RESULT_EXCLUDED | 313 |
| OUT_OF_SCOPE | 11 |
| UNRESOLVED | 2547 |

Path-family classifications are explicitly inferences, not inspected-content,
unit/provider/PIT or historical identity proofs. Duplicates retain their references
and original protocol exclusions. `blind_bundle_allowed=false` for every record;
classification never grants final authorization. No research-result payload parsed.
This covers the old frozen inventory, not a new complete inventory of changed files.

The archive search hashed and inspected 24 current `.log`/`.jsonl` files under
`logs`, `data/logs` and `data/distribution`. Exact date text `2026-09-09` plus
scan/publication/export/scheduler keywords produced no matching leads. File identities
and search scope are in JSON. This does not establish absence in JSON snapshots,
rotated/compressed archives, databases, other roots or external CI/deployment records.
No claim about `11:42` or `DISTRIBUTION=1` was promoted to historical scan evidence.

Historical runtime constraint files were hashed. Selected lock/environment/deployment
filename patterns were searched across history reachable from the baseline HEAD;
no matching history paths were returned. Source Docker/requirements constraints
are not actual installed runtime identity. External runtime archives were not accessed.

## External Identity Receipt

| Artifact | SHA-256 |
| --- | --- |
| Closure audit JSON | `829700b264a83e4a90952374fa5a7c6c1d085ebca159e6ebb2983c152249368c` |
| Updated custodian helper | `fca83b05c8ded9f145b23b135d513efd24d0b387861134579ae8f3576a6f26c7` |
| Updated preparation tests | `e4ed0b9dc78e7ce26fad29d06f22af6916d24d0f6939b3819e0d1dfb2178da8b` |
| Unchanged normative v3 | `6745641a28a254f2ff1c8d2fb6dc2ec599b58d7685248b73a361ef46ac2feaf0` |
| Unchanged fixture candidate | `64209e6fc203cf47e07ec53ddf2613ff3399cc2c09ae7582fcc5f4ab22caeae8` |

Earlier helper/test hashes identify the earlier preparation delivery, not these
updated versions. Prior receipts, baseline manifest and protocol were not rewritten.
No manifest self-hash cycle or new scientific acceptance rule was introduced.

## Handoff And Next Required Evidence

Custodian follow-up: complete provider/precision dependency review, unresolved
source disposition, alternate roots, exact target-eligibility mapping and staged
member selection. Original scan/CI/deployment archives require access from their owner;
if required evidence remains unavailable, retain UNKNOWN rather than reconstruct it
from today's execution.

External restricted authors: implement runner and independent verifier under the
existing v3 section 7 contract. Frozen executable suite, runtime/dependency hashes,
authoring/execution restrictions, canaries, scoped access records and verifier
compute-output separation must be demonstrated there, not simulated in this session.

Human action: assign actors, review fixtures/allowlist/output scope, and approve an
exact-bundle LOCK only after all required gates close. No repeated approval of the
unchanged methodology is needed. Synthetic evaluation remains AFTER LOCK.

Validation: 13 focused metadata tests passed; ruff and Python editor diagnostics
clean. No scientific S01-S28/J01-J04 execution or recovery calculation.
Confidence: high for byte/count/static-source observations; source-use/runtime
identity and archive completeness remain unestablished. **LOCK BLOCKED**.
