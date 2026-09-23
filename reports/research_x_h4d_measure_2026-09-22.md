# RESEARCH-X/H4D-measure - Production Ranking Resolution Measurement

**Date:** 2026-09-22
**Level:** A - read-only measurement protocol
**Runner:** `research/research_x_h4d_measure_2026_09_22.py`
**Definition:** `reports/research_x_h4d_ranking_resolution_definition_2026-09-22.md` (LOCKED)
**Preregistration:** `reports/research_x_h4d_measure_preregistration_2026-09-22.md` (APPROVED/LOCKED)

This report answers **resolution kac?** only. It does **not** answer **resolution yeterli mi / yetersiz mi?**.

## 1. Reconstructability Gate

Canonical SHA-256: `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`.
Composite rows: `40014` (integrity passed: `True`).
Gate result: `PROVENANCE_INSUFFICIENT`.

The runner executed the gate on the actual export columns; it did not assume the preregistered expected outcomes.

### Snapshot tuple field presence

- `grade`: ABSENT
- `execution_confidence`: ABSENT
- `conviction_prob`: ABSENT
- `selected_score`: ABSENT

### Summary tuple field presence

- `conviction_tier`: PRESENT
- `execution_confidence`: ABSENT
- `conviction_prob`: ABSENT
- `ranking_score`: ABSENT

## 2. Endpoint Verdicts

- Snapshot sort-tuple (Candidate B, PRIMARY): `NOT_MEASURABLE / PROVENANCE_INSUFFICIENT`
- Summary sort-tuple (Candidate B, PRIMARY): `NOT_MEASURABLE / PROVENANCE_INSUFFICIENT`
- Score-space diagnostic (Candidate A, SECONDARY): `MEASURED`
- Displayed-rank (Candidate C, OBSERVATIONAL): `NOT_MEASURABLE / PROVENANCE_INSUFFICIENT`

MEASURED here means only that the present score fields are measurable; it does NOT mean production ordering resolution was measured (score resolution != production ordering resolution).

## 3. Score-Space Diagnostic (Candidate A, descriptive only)

- `composite_score`: unique=`90`, tie_share=`0.999975`, effective_count=`47.871487`
- `score`: unique=`4`, tie_share=`1.0`, effective_count=`2.222526`

## 4. Scope Limits

- Full production sort tuple is not reconstructed where fields are absent; no imputation, no tuple shortening.
- Capacity, collision/tie structure, and determinism are reported separately; never compressed into a single resolution score.
- Determinism in full-tie groups is `UNDETERMINED_AT_FINAL_TIE` (a definition consequence, not a defect).
- No production ranking, ordering, score, scanner, configuration, scheduler, or publication path was changed. production_impact = NONE.
