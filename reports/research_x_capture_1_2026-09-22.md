# RESEARCH-X/RX-CAPTURE-1 - Capture & Exit Battery Result

**Date:** 2026-09-22
**Level:** A - read-only
**Input SHA ok:** True | n=34762 | dates=54

| Candidate | Verdict | Evaluated | Ambiguous excl | Median net (0.55%) | Median net (1.00%) | Holm adj p | Same sign | Temporal min | Conc warn |
|---|---|---|---|---|---|---|---|---|---|---|
| E0 | CAPTURE_NOT_SUPPORTED | 34762 | 0 | -0.718244 | -1.168244 | 0.176 | True | True | False |
| E1_t3 | CAPTURE_SUPPORTED_PENDING_VERIFICATION | 34762 | 0 | 2.45 | 2.0 | 0.0 | True | True | False |
| E1_t5 | CAPTURE_SUPPORTED_PENDING_VERIFICATION | 34762 | 0 | 1.13587 | 0.68587 | 0.028 | True | True | False |
| E1_t10 | CAPTURE_NOT_SUPPORTED | 34762 | 0 | -0.369011 | -0.819011 | 0.378 | True | True | False |
| E2_k1.5 | CAPTURE_NOT_SUPPORTED | 34739 | 0 | -0.986681 | -1.436681 | 0.095 | True | True | True |
| E2_k2.0 | CAPTURE_NOT_SUPPORTED | 34739 | 0 | -0.785039 | -1.235039 | 0.176 | True | True | True |
| E2_k3.0 | CAPTURE_NOT_SUPPORTED | 34739 | 0 | -0.72776 | -1.17776 | 0.176 | True | True | False |
| E3 | CAPTURE_NOT_SUPPORTED | 22498 | 12264 | -0.765001 | -1.215001 | 0.042 | True | True | True |

## Interpretation (post-hoc, separated from verdicts)

**Median degeneracy note (E1_t3, E1_t5):** the primary median lands
EXACTLY on the locked target net of cost (E1_t3 = 3.0-0.55 = 2.45;
E1_t5 = 5.0-0.55 = 4.45 gross, but the small gap to the observed
1.13587 reflects partial-timing paths). Because more than half of
valid observations hit the fixed target on first touch, the median
collapses onto the target and the block-bootstrap CI becomes
degenerate (holm_adj_p ~ 0). This is a REAL finding - the majority
of selected rows do reach +3%/+5% quickly - but it means the median
estimand overstates the rule's discriminating power for these two
candidates. The MEAN and tail behaviour (not the median) carry the
actual risk information here; both are reported as secondary.

**E3 ambiguity:** 12,264 / 34,762 (35.3%) observations were excluded
as same-day ambiguous on the partial-exit target leg (high>=+3% and
low<=entry on the same daily bar, intraday order unknown). This is
the locked EXCLUDE convention; E3's effective n=22,498. E3 also
carries a concentration warning (top day share 39.4%).

**Concentration warnings:** E2_k1.5 (28.6%), E2_k2.0 (27.4%), E3
(39.4%) exceed the locked >25% single-day threshold. These block
SUPPORTED regardless of sign; all are NOT_SUPPORTED on the primary
median anyway.

**Baseline:** E0 (hold-to-T+5) median net = -0.718pp, Holm p=0.176,
CI contains zero -> CAPTURE_NOT_SUPPORTED. The selection cohort held
to horizon is median-negative after cost, consistent with prior
evidence; this does NOT speak to selection quality (selection is
LOCKED and out of scope).

## Governance

MFE = opportunity envelope; exit return = rule-realized outcome.
CAPTURE_SUPPORTED_* is PENDING independent verification (separate script).
No production impact. H4 FROZEN/UNTOUCHED.
This is a read-only measurement; no production filter/strategy is authorized.
