# B2-1 — MISSING HISTORICAL INPUT PROVENANCE RECOVERY — PREREGISTRATION

**Status:** DRAFT v2 — NOT LOCKED. Lock = Meriç approval + SHA-256 of the locked file in decision-log BEFORE any execution. After lock: change = new version + new SHA.
**Research level:** A (provenance / reconstruction; read-only)
**Parent:** B2-0 (verdict of record INCOMPLETE — unchanged)
**Production impact:** NONE · **Production authorization:** NONE
**Out of scope:** B2-2 (conditional, separate), B2-AUTH (separate Level C line), B4 (parallel track), B2-full (not opened)
**Decision it enables:** whether a later counterfactual (B2-2) *could* use ATR / ALPHA_V2 inputs, and under which evidence class. Nothing else.

**v2 basis:** Meriç's v2 structure (2026-09-23) plus review corrections, marked **[R]**:
- [R1] corrected cache coverage figures
- [R2] granularity of the acceptance rule
- [R3] pre-seen status of R4 for ATR
- [R4] analytic R4 bound for squeeze, replacing the stale-cache "float ≥ 50M" shortcut
- [R5] squeeze-test specification (formula, tolerance, source definition)
- [R6] inventory facts vs outcome results
- [R7] a B4 note: persistence must also cover partial scans

---

## 1. Purpose
Determine which historical inputs that B2-0 needed for CONVICTION_TIERS and ALPHA_V2 can be reconstructed, from which evidence class, and with what provenance limits.

B2-1 does not:
- run any publication counterfactual;
- enable, disable or change any flag;
- modify B2-0 or its verdict.

## 2. B2-0 boundary
- B2-0 = `INCOMPLETE`.
- Independent verification = `VERIFICATION_MISMATCH / PROTOCOL INTERPRETATION AMBIGUITY`.
- CONVICTION_TIERS = `UNRESOLVED`.

Nothing in B2-1 alters these retroactively.

## 3. Recovery classes

| Class | Definition | Admissible for later Q3B-type use |
|---|---|---|
| R1 RAW_INPUT_RECONSTRUCTION | Historical raw input/cache fed into the production calculation definition | Yes (strongest); PIT reported separately |
| R2 STORED_DERIVED_OUTPUT_RECOVERY | Deterministic inversion of a locked stored output, using stored known components | Yes, as a separate, lower class; never called "stored input" |
| R3 CROSS_OUTPUT_CONSISTENCY | Agreement with a second stored encoding of the same upstream quantity | Supporting only: arithmetic/formula consistency, not provenance or PIT |
| R4 BOUNDED_INVARIANCE | The decision is identical for every value the missing input can take within its **analytically** derived feasible set | Yes, for that decision only |
| R5 EXTERNAL_RECOVERY | Data outside the locked input universe | No (provenance discovery only) |
| R6 ASSUMED / IMPUTED | Estimated or assumed value | Never. `UNKNOWN` is never coded as FALSE, 0 or an estimate |

**[R4]** R4 bounds must come only from formula domains and stored values. Stale external data (e.g. a 07-01 cache) never establishes an R4 bound.

## 4. Pre-seen evidence declaration
Before this draft was written, the following were already known:
- **R2 for ATR:** `legacy_quality_score` inversion — 1,508/1,508 threshold-resolved, 0 boundary rows (B2-0 independent verifier).
- **[R3] R4 for ATR:** In B2-0, 1,794 rows were tier-invariant to `atr_present`, and 7 published rows were ATR-dependent (original B2-0 run).

Both are labelled `PRE-SEEN / NON-BLIND` and are not blind validation. No tolerance or rule may be tuned against them.

**Blind channels** (not yet executed by anyone):
- R3 `v2_score` consistency
- the squeeze consistency test (§12)
- R4 for squeeze (§12)

**Blindness control:** The runner is written by a sub-agent with no access to:
- the B2-0 verifier JSON (it contains per-row recovered ATR),
- the B2-0 result JSON,
- this conversation's analyses.

## 5. Preflight A — estimand degeneracy
- **ATR estimand:** `I(atr_pct_daily ≥ 4.0)`, exactly as in `compute_conviction` (`features.py`). The exact ATR value is needed only to classify the threshold.
- **Squeeze estimand:** the ALPHA_V2-OFF squeeze value (weights 0.5/0.5), and the threshold decision `I(squeeze_off ≥ 0.5)` (`short_strong`).
- **Degeneracy risks to report:**
  - saturation `min(1, atr/6)` and `min(1, atr/4)`;
  - clipping of squeeze to [0,1];
  - 4-dp rounding of `atr_pct_daily` (`features.py:204`) and of `squeeze_factor`;
  - 3-dp `legacy_quality_score`;
  - integer `v2_score`.

## 6. Preflight B — input inventory
**[R6]** These are presence / coverage / definition facts established before lock. They are not outcome results.

**Daily ATR** (`compute_atr_pct(df_1d)` — simple mean of the last 14 TR / last close, 4-dp). The 09-09 scan used daily bars through 2026-09-08 (`feature_timestamps.1d`).

**[R1] price_cache last-bar distribution (2,047 files):**

| Last bar | Files |
|---|---|
| 2026-07-29 | 1,512 |
| 2026-07-14 | 132 |
| 2026-08-21 | 106 |
| 2026-06-30 | 36 |
| 2026-08-07 | 7 |
| other earlier dates | scattered |
| no bars / empty | 180 |

- No file reaches 2026-09-08.
- The 10 published tickers end at 08-21 or 07-29.
- `full_universe_enriched_eod_only.csv` (`atr_pct_real`) ends 2026-08-05.

→ R1 daily ATR for 09-09 is expected `NOT_FOUND`, unless the locked inventory search finds a PIT source.

**15-minute ATR:** `df_15m["atr"]` (`evaluate.py:419`), stored as the export field `atr`. It is a different quantity and never substitutes for daily ATR.

**Short/float:**
- **Production source:** yfinance `.info` `shortPercentOfFloat` / `floatShares` at scan time (`features.py:125-135`). Not stored.
- **Candidate secondary source:** `data/fundamentals_cache.json`, mtime 2026-07-01, 1,216 symbols, fields `short_pct`, `float_shares`. Its provider and definition are to be established in the inventory (possible `AVAILABLE_BUT_DIFFERENT_DEFINITION`). Not PIT-valid for 09-09 by default.

**Inventory search scope (locked):**
- `data/`, `data/backtest_out/`, `reports/`, `cache/` if present;
- git history of tracked data files.

Any newly found source is classified R1 or R5 by definition and PIT, before any value is compared.

## 7. ATR channel A — raw daily ATR
- Expected `NOT_FOUND` for 09-09.
- No 15m ATR substitution.
- No substitution of an earlier-dated ATR (e.g. 08-05).

## 8. ATR channel B — R2 inversion (pre-seen)
`legacy_quality_score = (base + 1.5·min(1,atr/6) + 1.5·rvol_n + 0.5·sq − 1.5·lot − ovn)/10·100`, rounded to 3 dp (`score_engine.py:193-222`). All non-ATR terms are stored in `score_input` (regime, direction, score, rvol_factor, squeeze_factor, lottery_factor, overnight_gap_factor).

- `atr_n ≥ 1` ⇒ `atr ≥ 6` ⇒ threshold TRUE.
- `atr_n ≤ 0` ⇒ threshold FALSE.
- Otherwise `atr = 6·atr_n`.

This gives threshold-level uniqueness; value-level uniqueness is not required.

## 9. Tolerances (analytic, fixed)
**R2:** LQS rounding ±0.0005 ⇒ ATR error ±0.0002.

- Boundary band: `|atr − 4.0| < 0.0002`, plus a floating-point margin fixed at `1e-9`.
- Rows inside the band are `UNRESOLVED`.
- Recovered `atr_n` outside `[−1e-9, 1+1e-9]` is a `DOMAIN_VIOLATION` (formula/input mismatch) → `CONFLICT` for that row.

**R3:** `v2_score = round(30·gap + 30·rvol + 25·min(1,atr/4) + 15·sq)`, clipped to [0,100] (`score_engine.py:225-235`).

- Integer rounding (Python round-half-even) ⇒ ±0.5 on the 25-point term ⇒ ATR ±0.08.
- Rows with `|atr_R2 − 4.0| < 0.08` are `CROSS_OUTPUT_CONSISTENCY_BOUNDARY`.
- Rows where the ATR term is clipped by v2's [0,100] bound are also BOUNDARY.

## 10. Non-tautological validation
Re-feeding the R2 value into `legacy_quality_score` is not evidence (it is circular). The valid checks are:
- domain validity;
- threshold uniqueness;
- R3 agreement outside its band;
- R1 agreement if R1 exists.

## 11. ATR acceptance rule (locked)
**[R2]** Granularity: row level, aggregated to the dataset level for the decision.

For each row with `entry_ok = True` (the only rows where conviction reads ATR), the ATR threshold state is `ELIGIBLE` iff all four hold:
1. R2 threshold-unique (not in the R2 band);
2. no DOMAIN_VIOLATION;
3. R3 ≠ FAIL (R3 BOUNDARY is allowed and is reported);
4. no R1 value disagrees (R1 absence is allowed and reported as a provenance limitation).

Rows with `entry_ok = False` need no ATR (conviction returns `('',0.0)`) and are reported separately.

**Dataset-level status:**
- `RECOVERABLE` ⇔ every `entry_ok` row is ELIGIBLE.
- `PARTIALLY_RECOVERABLE` ⇔ at least one row is ELIGIBLE and at least one is not; the full row list is reported.
- `NOT_RECONSTRUCTIBLE` ⇔ no row is ELIGIBLE.
- `CONFLICT` ⇔ any DOMAIN_VIOLATION or any R3 FAIL outside the band.

The evidence class of every ELIGIBLE row is recorded: `R2` or `R2+R3`.

## 12. ALPHA_V2 — squeeze channel
**Production formula at ff9658a** (`features.py:137-156`):
- `short_comp = min(1, short_pct/0.20)` if `short_pct > 0`, else 0.
- `float_comp = max(0, 1 − float_shares/50e6)` if `float_shares > 0`, else 0.
- `squeeze = round(clip01(w_s·short_comp + w_f·float_comp), 4)`.
- Weights: ALPHA_V2 ON → (0.7, 0.3); OFF → (0.5, 0.5).

**12a. Consistency test (blind, R5-assisted)** — **[R5]**
- For each row whose symbol is in `fundamentals_cache.json`, compute the ON-weights squeeze from the cached `short_pct` and `float_shares` using the formula above.
- Compare with the stored `squeeze_factor`: match ⇔ `|diff| ≤ 0.00005` (4-dp rounding).
- Result per row: `CONSISTENT`, `INCONSISTENT` or `NOT_IN_CACHE`.
- A match means the cached inputs are consistent with the scan-time output. It is not PIT proof. Rows are labelled `R5_CONSISTENT` and cannot be upgraded to R1.
- The cache's field definitions must first be checked against the yfinance semantics (fraction vs percent). If they differ, the test is `NOT_APPLICABLE`.

**12b. R4 analytic bound (blind)** — **[R4]**
Given stored S = 0.7s + 0.3f with s, f ∈ [0,1]:
- feasible f ∈ `[max(0,(S−0.7)/0.3), min(1, S/0.3)]` (widened by ±0.00005 for rounding);
- `squeeze_off = (5/7)·S + (2/7)·f`.

The threshold decision `I(squeeze_off ≥ 0.5)` is `R4_DETERMINED` iff it is the same at both ends of the f interval; otherwise `R4_UNDETERMINED`. This uses only the formula domain and the stored S.

**Channel status:**
- `RECOVERABLE` (threshold level) ⇔ every `entry_ok` row is R4_DETERMINED or R5_CONSISTENT.
- Otherwise `PARTIALLY_RECOVERABLE` or `NOT_RECONSTRUCTIBLE`, with the row list.

Continuous `squeeze_off` values (which feed `legacy_quality_score` and `v2_score`) are recoverable only for R5_CONSISTENT rows. This is reported separately.

## 13. ALPHA_V2 — risk-engine channel (code trace only)
Inputs: 15m ATR (`atr`), price, stop/TP multipliers (`risk_engine.py:~190-217`), and `position_size = 1000` (`risk_engine.py:217`).

The trace must establish whether stop/TP/risk_reward reach any of:
- `_public_candidate` fields;
- `_sort_key` fields;
- `position_cap` requested notional (expected `1000 × price`).

Classification:
- `MEMBERSHIP_IMPACT`: `NONE` / `PRESENT`.
- `DISPLAYED_CONTENT_IMPACT`: `NONE` / `PRESENT` — snapshot metrics, risk_note and rationale fields that display stop_loss, take_profit or risk_reward.

DISPLAYED_CONTENT_IMPACT is outside the B2-0 estimand and is not added to B2-0. It is reported as an input to B2-AUTH.

No data values are computed for this channel.

## 14. Synthesis
Separate statuses are reported for:
- ATR (CONVICTION);
- ALPHA_V2 squeeze;
- ALPHA_V2 risk-engine.

There is no single combined verdict. One channel's status never determines another's.

## 15. Explicitly not done
- No O1/O2/O3 counterfactual.
- No all-OFF.
- No free-tier delta.
- No flag change.
- No `.env` change.
- No threshold or tolerance tuning.
- No imputation.
- No arbitrary short/float decomposition.
- No use of external data as a locked input.
- No modification of B2-0 artifacts.

## 16. Integrity
- Input SHA manifest: to be filled at lock and verified at run (MATCH / MISMATCH / MISSING).
- Any mismatch or missing artifact → `CONFLICT`; the affected channel is not executed.
- Also `CONFLICT`: an unexplained formula mismatch, or any tolerance change after lock.
- Two byte-identical runs are required.

## 17. Final states (per channel)
`RECOVERABLE` · `PARTIALLY_RECOVERABLE` · `NOT_RECONSTRUCTIBLE` · `PROVENANCE_INSUFFICIENT` · `CONFLICT`

The evidence class (R1–R4, R5-assisted) and PIT status are always attached.

**Recovery never implies:** predictive validity, economic validity, production correctness, user-facing impact, or authorization.

## 18. Related tracks (recorded, not part of B2-1)
- **B4** (parallel; specification now, implementation needs separate authorization). Persist the fields actually used on the scan→export→snapshot→publish path, determined by code trace, including:
  - `atr_pct_daily`, 15m `atr`;
  - scan-time `short_pct` / `float_shares` with source and timestamp;
  - the `_sort_key` tuple and final rank;
  - `config_sha` on `broadcast_queue`;
  - the scan-process flag state.

  **[R7]** Persistence must also cover partial scans and exports. Since 2026-09-09, only `_partial_` exports exist.
- **B2-AUTH** (Level C): publication-gate authorization review — dependency map, authorization records, provenance sufficiency, displayed-content dependencies. No automatic flag change.
- **B2-2** (conditional): opened only if governance still needs a locked counterfactual after B2-1 and B2-AUTH.

## 19. Lock criteria
All of the following must hold:
- §3–§14 fixed;
- pre-seen evidence declared (§4);
- blindness control specified (§4);
- inventory search scope locked (§6);
- tolerances analytic (§9);
- acceptance rules fixed (§11, §12);
- risk-engine channel is code-only (§13);
- the manifest SHA list is filled (§16);
- no outcome result was used to set any rule. Inventory facts are allowed ([R6]).
