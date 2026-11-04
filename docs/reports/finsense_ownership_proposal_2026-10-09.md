# FinSense Academy Ownership Boundary — Decision Proposal

**Date:** 2026-10-09  
**Status:** Proposal only; pending human decision  
**Layer:** Engineering and product ownership  
**Level:** B; no ownership or publication authority is changed here

## Decision required

Choose whether Borsa's Academy surface continues to consume a static artifact produced by FinSense, or whether that cross-repository bridge is retired and replaced through a separately approved architecture decision. FinSense's internal choice of file-based releases over its legacy SQLite content is not, by itself, a decision about ownership between the two repositories.

## Verified boundary

- Borsa's authority map describes Academy content as produced by FinSense and consumed as `web/public/academy_lessons.json` (`docs/index.md`, human-readable row and `academy-content` manifest entry). The manifest's `authority_path` is the unqualified value `academy`.
- The Borsa decision log records the bridge-versus-cutover question as pending; no later approval was found during this review.
- Borsa's web Academy reads the static JSON artifact. Its publish helper can commit and push that artifact, so choosing a producer also affects the release boundary.
- FinSense documents file-based, manifest-verified releases as canonical within FinSense and SQLite as a derived/read-only path. Its legacy JSON exporter remains disabled; the optional worker hook catches and logs that disabled-export failure.
- No approved canonical lesson/release, cross-repository generator contract, authenticated human release proof, or current bridge publication was established in this review.

## Options

### A. Retain the static bridge contract temporarily

Keep `web/public/academy_lessons.json` as the Borsa consumer interface, but do not enable the legacy SQLite exporter or generate/publish an artifact in this proposal. Any future producer must read only a verified FinSense release manifest, preserve release hashes and locale parity, and pass a separately approved publication gate. Record the exact producer, owner, artifact schema, freshness rule, and rollback procedure before implementation.

This minimizes immediate consumer disruption, but leaves a stale-artifact risk until an approved producer and freshness check exist. Retaining the path does not authorize a release.

### B. Retire the cross-repository bridge

Stop treating the FinSense repository as the producer for Borsa's Academy artifact. Before removing the consumer or changing its runtime/build contract, approve the new ownership boundary, decide what Borsa will serve instead, and verify compatibility, release, and rollback behavior. No replacement source or implementation is selected here.

This can remove ambiguous cross-repository ownership, but may make the current Academy surface empty or incompatible until the replacement is designed and released.

## Recommendation for human consideration

Prefer Option A as a temporary *contract-only* state: preserve the existing static consumer path, keep SQLite-to-JSON export disabled, and make no artifact or publication changes. This is a proposal, not an approved decision. The bridge must not be described as operationally complete until an authenticated, manifest-bound producer and release gate are demonstrated.

## Approval and implementation gates

Human approval must identify the selected option, canonical owner, producer, artifact schema/version, freshness behavior, release approver, and rollback owner. Any later authority-map or live web/publish-chain edit requires its own applicable approval and validation. Do not migrate content, inspect or modify real databases, open secrets, run agents, publish, deploy, or change canonical paths as part of this proposal.

## Evidence references

- Borsa `docs/index.md` and `docs/governance/decision-log.md`.
- Borsa `web/src/app/academy/page.tsx` and `scripts/publish_web.py`.
- FinSense `FINSENSE_BUILD_KIT_ADOPTION.md`, `academy/worker.py`, and `academy/export_lessons.py`.
- FinSense `AGENTS.md` and `academy/content_store.py`.