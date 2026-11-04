# P0 — CONVICTION / GRADE PROBABILITY VERIFICATION — CLOSURE AUDIT — PREREGISTRATION

**Status:** DRAFT v0.1 — NOT LOCKED. Lock = Meriç approval + SHA-256 of the locked file in decision-log before any outcome is computed.
**Level:** A (read-only measurement)
**Production impact:** NONE · **Production authorization:** NONE

**Nature:** This is the closure audit of an existing P0, not a new research line (CORE-008):
- **2026-06-12** — `docs/audit-2026-06-12/19-scanner-test-defteri.md:67`: conviction tier lab = "Geliştirici iddiası — doğrulanmadı; 2A'da conviction n_hi=0 (ölçülemedi)".
- **2026-07-03** — `FinPilot_Tam_Sistem_Audit_2026-07-03.md:420`: "Konviksiyon WF'siz → Konviksiyon Raporu v2: walk-forward + Wilson CI" = **P0**.
- **2026-09-23** — found not completed. Decision-log entry "P0 CLOSURE GAP IDENTIFIED".

**Question:** Do the Grade A/B/C probability statements show historical calibration for a defined outcome? Beyond the baseline of the same volatility band, do they carry incremental information?

**Decisions this enables** (all separate Level C decisions; nothing is applied automatically):
- the probability-label decision (C2),
- the numeric-claim decision,
- input to B2-AUTH.

---

## 1. Claim provenance (pre-lock facts)

| Item | Fact |
|---|---|
| Constants | `scanner/features.py:179` `_CONV_PROB = {"A": 0.73, "B": 0.59, "C": 0.52}`. No recalibration mechanism in production code |
| Tier rule | `compute_conviction` (`features.py:209-237`): short_strong, gap_strong/present, rvol_present, atr_present |
| Introduced | commit `0d30ae1`, 2026-07-02 ("add conviction-tier signal quality gate") |
| Lab source | `FinPilot_Sinyal_Kalitesi_ve_Konviksiyon_Raporu.docx` (SHA-256 `5960df561c4c8d04397a7683b082e1a4ffae884ec2fd5f59e4ced76426ec38ef`), summarised in the 07-03 audit as "6410 sinyal, 53 gün … elit kova %73 (≥5%)" |
| User-facing claim | `distribution/templates.py:105` "geçmişte bu profildekilerin {band}'i 5 günde ≥%5 hareket etti" · `distribution/glossary.py:23-25` (prob_band: "calibrated range … reached their target … recalibrated as outcomes accumulate") · `glossary.py:151-153` ("kalibre olasılık") · `glossary.py:161` (calibration definition) |
| Available population | Dated full/published scan exports 2026-07-05 → 2026-09-09: 39 dates, all with `conviction_tier`. Graded rows across all scans (counts, not outcomes): **A = 9, B = 47, C = 35** |

**Status of the lab:** hypothesis-development evidence. In-sample, with thresholds and constants set on the same data. It is not calibration evidence.

**Candidate OOS status of the audit window:** The constants were deployed on 07-02 and the audit window starts on 07-05. So 07-05 → 09-09 is out-of-sample relative to the lab **iff** both hold:
- the lab window ended on or before 2026-07-02;
- the tier rule and constants were unchanged throughout the window.

Gate A verifies both.

## 2. Pre-seen declaration
- The in-sample lab figures (73/59/52) are known.
- The agent has seen the 09-09 snapshot karne `by_grade`: A n=1 (hit 0), B n=1 (hit 0). This uses a different window and possibly a different hit definition. It is pre-seen but not used.
- No calibration outcome for the audit window has been computed by anyone.
- The runner is written by a sub-agent with no access to prior analyses. It receives only this prereg and the manifest inputs.

## 3. Gate A — Claim definition

Two claims are defined separately:
- **Claim L (lab):** the outcome the 73/59/52 numbers measured. Established from the lab docx (and any lab code or data it references).
- **Claim U (user):** what the brief and glossary text say.

Dimensions fixed for each claim:
- **event:** touch vs close vs MFE;
- **direction:** up / absolute;
- **threshold:** 5%;
- **horizon:** trading vs calendar days;
- **reference price:** scan price / T0 close / T+1 open;
- **censoring:** how missing bars are handled;
- **population:** all scanned vs published vs entry_ok;
- **tier-rule version.**

**Gate A outcomes:**
- `CLAIM_DEFINED` — L is fully determined.
- `CLAIM_TEXT_MISMATCH` — U differs from L on any dimension. This is recorded as a verdict component. It does **not** stop the audit; calibration is then tested against L.
- `NOT_MEASURABLE` — L cannot be determined from the artifacts. Calibration is then tested only against two pre-specified literal readings of U, labelled as such and not as the lab claim:
  - **U1** = upward touch ≥ +5% within T+1..T+5 trading days, using the scan price as reference (glossary reading);
  - **U2** = |touch| ≥ 5% in either direction (literal reading of "hareket etti").

**Also verified in Gate A:**
- the lab window end date;
- the git history of `compute_conviction` and `_CONV_PROB` between 07-02 and 09-09. Any change inside the window splits the window by version.

## 4. Data
- **Population:** all main-path export rows on the 39 dates. Graded = conviction_tier ∈ {A,B,C}. A published subset (8 dates with snapshots) is reported separately.
- **Outcome prices:** one controlled EOD refresh (source fixed at lock). It covers the pre-scan window (for ATR/σ) and T+1..T+5 after each date. It is fetched once, hashed, and written to a new artifact. `price_cache` is not overwritten. Splits are handled consistently: ATR% and returns are scale-invariant under proportional adjustment.
- **Censoring:** rows without complete T+5 bars are excluded and counted per grade.
- **Shared-data note:** the same refresh may later serve B2-1 (R1 channel). The estimands and reports stay separate.

## 5. Estimands (for Claim L, or U1/U2 as above)
- **Calibration:** `q_g` = observed event rate for grade g, and `CE_g = q_g − p_g^claimed`.
- **Information value (secondary):** `Δ_g = q_g − q_matched`.
  - `q_matched` is the event rate of non-graded main-path rows on the same dates, reweighted to grade g's ATR-band distribution.
  - Daily ATR% bands are fixed: [0,2), [2,4), [4,6), [6,8), [8,12), [12,∞).
  - ATR is computed with the `compute_atr_pct` definition on refreshed bars through `feature_timestamps.1d`.
- **Analytic null (sensitivity only):** `2·(1−Φ(0.05/(σ_i·√5)))` per row, where σ_i is the 20-day daily-return standard deviation before the scan. It never replaces the empirical null.
- **Downside:** `d_g` = P(downward touch ≤ −5%, same window and reference). The diagnostic `q_g − d_g` is secondary only.

## 6. Uncertainty and effective N
- **Always reported:** N rows, N unique dates, N unique symbols, N symbol-days, censored count.
- **Confidence intervals:** naive Wilson CI (reference only); 95% day-cluster bootstrap CI as primary (resample dates; B = 10,000; seed = 20260923). Overlapping 5-day windows are acknowledged.

## 7. Verdicts (fixed; per grade g)

**Calibration:**
- `CALIBRATION_REJECTED` ⇔ the cluster CI of q_g excludes p_g^claimed.
- `CALIBRATION_CONSISTENT` ⇔ the CI contains p_g^claimed **and** the CI half-width ≤ 10pp.
- `INSUFFICIENT_POWER` ⇔ otherwise. With A ≤ 9 rows before censoring, this is the expected outcome for A; it is a valid result, not a failure.

**Information:**
- `INCREMENTAL_INFO_SUPPORTED` ⇔ the cluster CI of Δ_g > 0.
- `NO_INCREMENTAL_INFO` ⇔ the CI of Δ_g < 0.
- `INDETERMINATE` ⇔ otherwise.

**Audit status:** `P0_CLOSED_WITH_RESULT` (Gate A resolved and the audit executed) or `P0_NOT_CLOSABLE` (NOT_MEASURABLE and U readings unmeasurable, or data unavailable).

**Interpretation limits:** `CALIBRATION_CONSISTENT` ≠ "calibrated forward probability". A historical, post-deployment window is not a locked forward test.

## 8. Estimand-degeneracy check (pre-run)
1. Is the outcome fixed by the threshold? No, it is binary.
2. Can hit rate be mechanically inflated? **Yes** — volatility raises touch probability. Handled by the matched and analytic nulls.
3. Is the predictor a proxy for the outcome? **Possible** — the tier inputs (gap, rvol, ATR ≥ 4) are volatility-linked. Handled by Δ_g.
4. Is the ranking the production one? Yes — grade is the production gate.
5. Is effective N ≪ raw N? **Yes.** Handled by the cluster CI and the power rule.

## 9. Out of scope
No wording change, no flag change, no tier-threshold change, no recalibration of the constants, no production change, no merging with B2-1/B2-AUTH/RX-FORWARD. Sub-group results are descriptive only.

## 10. Integrity
- A manifest of SHA-256 values is filled at lock and hard-gated (MATCH / MISMATCH / MISSING → CONFLICT). It covers:
  - the lab docx;
  - `features.py`, `templates.py`, `glossary.py` at the tier commit and at `ff9658a`;
  - the 39 exports;
  - the EOD refresh artifact.
- Two byte-identical runs are required.
- Any rule change after lock requires a new version.

## 11. Lock criteria
- EOD source and fetch procedure fixed.
- ATR bands, bootstrap parameters, power rule and U1/U2 readings fixed.
- Manifest filled.
- Pre-seen declaration complete.
- No outcome from the audit window computed before lock.
