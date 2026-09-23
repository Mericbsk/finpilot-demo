# RESEARCH-X/H4C - Information-Loss Audit (Mapping-Only)

**Date:** 2026-09-22
**Level:** A - read-only forensic research
**Runner:** `research/research_x_h4c_information_loss_2026_09_22.py`
**Preregistration:** `reports/research_x_h4c_information_loss_preregistration_2026-09-22.md` (APPROVED / LOCKED)

**Production ordering:** `UNKNOWN / NOT RECONSTRUCTED`
**Official production ranking resolution:** `DEFINITION_REQUIRED`

## 1. Executive Result

H4C verdict: `INFORMATION_LOSS_NOT_SUPPORTED`.
No verdict asserts anything about production ranking, production ordering, or resolution. A positive verdict means observable information divergence in the mapping only, NOT that production ranking loses information.

## 2. Input Integrity

Canonical SHA-256: `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`.
Composite rows: `40014` (H4B: 40014).
Proxy calculable: `39986`; not calculable: `28` (missing by field: {'regime': 0, 'direction': 0, 'score': 0, 'atr_pct_real': 0, 'rvol': 28}).
Composite unique: `90`; proxy unique: `27050`.
Input integrity passed: `True`.

## 3. Primary Evidence - Tie-Internal Proxy Variation

Composite tie groups: `89`; tie observations: `39985`.
Median tie-group proxy std: `7.922114`; median range: `49.2595`; median distinct proxy per group: `449.5`.
Global tie-internal dispersion (group-demeaned variance): `68.461003` (std `8.274116`).

## 4. Permutation Null (scan-date-preserving)

Scheme: `scan_date_preserving_permutation`, R=`1000`, seed=`20260922`.
Null median dispersion: `348.322634`; null upper-95: `348.76881`.
Observed: `68.461003`; observed exceeds null upper-95: `False`.

Interpretation (descriptive): the observed tie-internal dispersion is far **below** the null band, not above it. Within a composite tie group the legacy proxy is actually *less* dispersed than it would be under a within-day random reassignment. This means the composite tie value does not hide extra proxy spread; the proxy's variation is driven by its own daily marginal distribution, not by differences the composite fails to capture. Hence the primary information-loss evidence is not met.

## 5. Secondary (descriptive) Metrics

Cardinality contrast: composite `90` vs proxy `27050` (reference 90 vs 27,050).
Many-to-one (descriptive only): composite->proxy median distinct `449.5`; proxy->composite median distinct `1.0`.
Monotonicity violation (auxiliary): share `0.41573`.
Round-trip uncertainty: R^2 `0.787596`, unexplained `0.212404`.
Proxy integer-valued fraction: `0.064573` (H4B ref 0.064573).

## 6. Verdict Logic

Verdict is one of INFORMATION_LOSS_SUPPORTED / INFORMATION_LOSS_NOT_SUPPORTED / INSUFFICIENT_DATA / INPUT_MISMATCH.
The primary evidence is observed tie-internal dispersion vs the permuted-null 95% upper band.
Cardinality and many-to-one are descriptive supporting evidence, not required conditions.

## 7. Scope Limits

- This audit does not reconstruct, simulate, or assert production ordering.
- A positive verdict means observable information divergence in the mapping only.
- It does not establish that production ranking loses information.
- No score, ranking, scanner, configuration, scheduler, or publication path was changed.
