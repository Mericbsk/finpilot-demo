# B2-1 Pre-LOCK Preparation v1

Date: 2026-10-05
Layer: Research; governance receipt only, no policy change.
Level: A - metadata and artificial fixture preparation.
Status: PREPARATION DELIVERED / PREREQUISITES STILL BLOCKED / NOT LOCKED / NOT RUN.
Role: non-blind custodian, not scientific runner or independent verifier.

## Authority

The approved [v3 protocol](b2_1_provenance_recovery_preregistration_DRAFT_v3_2026-10-05.md)
remains the sole methodological authority. Its bytes were not changed.
Methodological approval is already recorded in the
[decision log](../docs/governance/decision-log.md); no repeat approval of that
unchanged text is requested here. This report does not replace a LOCK receipt.

## Delivered Evidence

- [Candidate manifest](b2_1_prelock_manifest_candidate_v1_2026-10-05.json): current source/member hashes, historical git data membership and code-definition metadata. It is a custodian inventory, NOT an approved runner allowlist.
- [Concrete fixture candidate](b2_1_synthetic_fixtures_candidate_v3_2026-10-05.json): S01-S28, expanded half-even and R2/V2/domain cases, and J01-J04 joint squeeze boundary cases. Artificial only; review pending; scientific suite NOT RUN.
- [Custodian utility](../scripts/b2_1_prepare_lock.py): stdlib-only metadata collection, AST inspection without production imports, immutable git blob hashing and create-only output.
- [Preparation tests](../tests/test_b2_1_prepare_lock.py): eight tests, including path containment, integrity versus provenance, mutation STOP, canonical encoding, no production execution and fixture structure. These are NOT scientific suite results.

The historical definition commit is
`ff9658aa189d8ff0cbb9f3a0fecddab8a50b5b35`.
History coverage is every commit reachable from frozen observed HEAD
`e0e7b382eddff247aec118d24b83a2f70a69200e`, inclusive:
326 revisions, root `745ee048f675d3a380f488f3cc98c2eb236f7503`,
84 distinct data trees and 2,042 unique historical data blobs.
Tree/member lists and revision-to-tree mapping are recorded, not inferred from dates.
These blobs were hashed, not deserialized or used for recovery calculations.

There are 43 historical scanner/distribution Python definition members.
Their AST records expose symbols, local calls and round expressions, but do not
certify transitive dependency closure or historical runtime identity.

Current inventory has 9,617 records, including 2,047 price-cache candidates,
one fundamentals candidate, 348 research-result exclusions and an absent root
cache record. With export/fixture records, 9,618 available-file references were
independently rehashed after generation; all matched. All 2,042 historical blobs
were rehashed as well; no mismatch. Duplicate file references are not unique inputs.

The ordinary and published 2026-09-09 exports have identical bytes:
SHA-256 `454dd92835201b5c019067ffd9945f6de531d07776a94b8b65164798312b2074`.
Both contain 1,801 unfiltered rows and declare a complete scan. This establishes
byte equality and population size, not lineage to the historical commit.
Scan/run identity is top-level, not a row-level scan_id field. Final field mapping
and a single selected artifact ID require review before staging.

## External Hash Receipt

These identify preparation bytes only, not LOCK authorization:

| Artifact | SHA-256 |
| --- | --- |
| Approved v3 protocol | `6745641a28a254f2ff1c8d2fb6dc2ec599b58d7685248b73a361ef46ac2feaf0` |
| Candidate manifest | `84c7879c1231aa17647a97ed818469d71a44cb919397ee6db19e6ebb705f76bb` |
| Concrete fixture candidate | `64209e6fc203cf47e07ec53ddf2613ff3399cc2c09ae7582fcc5f4ab22caeae8` |
| Custodian utility | `f62728407ea14bb82f0e5f818f0af8da32fb2044d44e25d815facae87cea6028` |
| Preparation tests | `678e6ad7cb99631f9db614f97f5e594c8ef8134c1fc118c542c9895b3756dab3` |

The manifest does not contain its own hash. The unchanged v2 SHA is
`0ae40a66b1b9d2fbc38c9ae54494e3f496dea5bb5bb31a6adf51d6e4e4704c4e`.
The compact manifest replaced only this task's oversized, unapproved generated
output after checking its exact old hash; no historical source was overwritten.

## Remaining LOCK Gates

The section 12 checklist is not satisfied yet:

1. Export lineage, definitions, justified known-component precision, full publication/risk call paths and historical runtime/dependency identity remain unverified.
2. Inventory suffix/name exclusions and alternate cache-root coverage must be reviewed; 7,220 records are still unclassified custodian-only metadata. Absence outside covered paths is not established. No candidate gains PIT or historical identity from its hash or mtime.
3. Review concrete fixtures and the conservative OFF-rounding-envelope choice; freeze an executable scientific suite under the isolated implementation. The fixture JSON hash is NOT an executable suite hash.
4. Author and freeze genuinely isolated runner and separately authored verifier implementations; their bundles do not exist in this delivery. CPython 3.12.3 and its executable hash are observed candidates only, not proof of historical runtime.
5. Demonstrate authoring AND execution isolation. Both remain NOT_VERIFIED. No container/account/ACL setup was performed and no forbidden-access test was represented as passing.
6. Assign named operator and independent verifier, approve precise output paths, stage allowed member-level files and record their projected-byte hashes. No finalized staging bundle exists.
7. Record a new explicit exact-bundle LOCK receipt only after all evidence above is accepted. Existing methodological approval is preserved but is not that receipt.

## Required External Handoff

A human-authorized custodian must supply separate clean restricted authoring
contexts for runner and verifier. This session has repository tools and prior
research context; a new agent with those same tools is not an isolation solution.
Send only the approved protocol and reviewed, member-hashed allowed material.
Do not send this custodian report, the unclassified inventory, v2 observations,
research-result bytes, decision-log interpretations, transcripts or host git store.

Before claiming isolation, retain effective mounts/permissions, runtime and
dependency hashes, allowed-read checks, harmless forbidden-path/network canary
failures and scoped access logs without secrets. Execution inputs must be read-only.
Keep the verifier compute phase unable to read runner results; freeze its own
output before opening the comparison phase. Use a fresh output-free environment
for the reproducibility run. Detailed governing rules remain in v3 section 7.

This is a concrete handoff requirement, not an instruction to install containers,
change host security controls, waive blindness or run the study now.

## Validation And Limits

Eight focused preparation tests passed; ruff and new-artifact editor diagnostics
were clean. Existing decision-log Markdown warnings were left unchanged.
The complete candidate integrity recheck passed and approved v2/v3 hashes matched.
Scientific S01-S28/J01-J04 evaluation, real recovery, independent verification,
production changes and publication were not performed. `locked=false`,
`execution_authorized=false`, `synthetic_gate=NOT_RUN`,
`blind_execution.status=NOT_VERIFIED` remain explicit in the candidate manifest.

Confidence: high for the recorded byte identities and counted covered inventory;
historical lineage/runtime, completeness outside declared coverage and genuine
independence/isolation are not established. LOCK remains BLOCKED.
