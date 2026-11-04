# B2-T Technical Synthetic Validation - Scope Proposal v1

Date: 2026-10-05. Layer: Research. Level: B.
Status: PROPOSED / APPROVAL_PENDING / NOT RUN.
This is a Level B decision, awaiting approval.

## Decision Boundary

The user requested progress even if missing B2-1 evidence cannot be closed.
Proceeding with the same B2-1 without its required gates conflicts with
[approved V3](b2_1_provenance_recovery_preregistration_DRAFT_v3_2026-10-05.md),
sections 7.2, 8, 9 and 12. This proposal reports that conflict; it does not
waive a gate, change V3, authorize execution or supersede B2-1.

B2-1 remains METHODOLOGY APPROVED / LOCK BLOCKED / NOT RUN. Missing historical
evidence has not been proved permanently unavailable; it has not been supplied
or established within the accessed scope. The 2547 unresolved records remain
unresolved for requiredness and authorization.

## Separate Question

B2-T asks whether a separately scoped technical implementation handles artificial
values, precision, feasible domains and malformed inputs consistently under a
declared present-day runtime. It does not ask what the September scan used,
whether historical inputs can be recovered, or whether an OFF publication would
have differed. This is not the B2-1 scientific suite moved before its LOCK.

Mathematical/source-definition references remain the historical definition commit
`ff9658aa189d8ff0cbb9f3a0fecddab8a50b5b35` and V3 sections 5.2-5.4.
Do not duplicate or amend formulas here. Any mismatch between these references
must be surfaced before implementation, never resolved by tuning expectations.

## Proposed Allowed Scope

- A separate technical implementation and T-prefixed test IDs, not a B2-1 runner.
- Artificial fixtures only; freeze concrete tuples, oracle basis, expected outcomes and hashes before their first evaluation.
- Precision/rounding, saturation, complete feasible-domain containment, joint-domain bounds, malformed/missing inputs and deterministic encodings.
- Pin and hash the actual execution interpreter and dependencies. Present-day runtime agreement is not historical runtime identity.
- Declare authoring NON_BLIND_ENGINEERING and verification NOT_INDEPENDENT. This session has pre-seen context; no VERIFIED_ISOLATED or VERIFIED_UNSEEN claim.
- Record actual access restrictions and their limitations. No prompt promise, temporary directory or new agent is promoted to technical isolation evidence.

## Prohibited Scope

- No September export rows, caches, shortlist/report contents, original research results or real expected verdicts as numerical inputs.
- No real recovery, real-data consistency comparison, financial risk or position-size calculation, performance assessment or imputation.
- No production module execution/import, network refresh, secrets access, environment flag changes, DB/cache mutation, publication or deployment.
- No translation of B2-T PASS into B2-1 synthetic PASS, input authorization, historical identity, LOCK readiness, independent verification or production permission.

## Execution And Receipt

First obtain explicit approval of this separate versioned scope in the decision
log. Scope approval would authorize preparing only the listed technical artifacts;
it would not authorize a real B2-1 run or a change to any risk/security policy.

Before any numerical test evaluation, record a B2-T-only frozen manifest of
implementation, reviewed artificial fixtures/expected outcomes, suite, actual
runtime/dependencies, permitted inputs and new output location. Reference hashes
externally without a self-hash cycle. Unapproved inputs and side effects remain
forbidden; do not treat development access as a blind boundary.

Report TECHNICAL_PASS / TECHNICAL_FAIL / NOT_RUN with case-level diagnostics and
actual runtime/access limitations. A required-case failure stops that version's
acceptance. Repairs require a new frozen version; retain original failures rather
than changing expected values to obtain PASS. No independent scientific receipt
is issued by a self-check or deterministic rerun.

## Current Delivery

Only this scope proposal is delivered. Implementation, fixtures, suite and B2-T
runtime manifest are not delivered; no numerical evaluation has occurred.
The existing 18 preparation tests are metadata checks, not B2-T results.
Approval of B2-T remains pending. B2-1 V3 and all frozen preparation artifacts
are unchanged. Historical lineage/runtime, member authorization, staging,
restricted actors, isolation and human B2-1 LOCK remain outstanding.

Evidence: [existing handoff](b2_1_prelock_handoff_v1_2026-10-05.json),
[closure baseline](b2_1_lock_closure_evidence_audit_v1_2026-10-05.md),
[decision log](../docs/governance/decision-log.md).
