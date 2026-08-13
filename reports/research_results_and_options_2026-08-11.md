# Research Results and Decision Options

Date: 2026-08-11
Layer: Research / Engineering
Level: A summary; options affecting product or live behavior remain Level B/C
Status: research-only; no production promotion

## Executive result

The feasible research battery is complete for the current data slice. It did
not establish a reliable forward edge for the current score, `entry_ok`, any
TP/SL or exit profile, or the weekly 5-10% / monthly 10% performance claims.
The correct conclusion is not that every hypothesis is disproved; it is that
the available evidence is negative or insufficient and the confirmatory gates
are still closed.

Canonical detailed evidence: `reports/research_battery_full_2026-08-11.md`,
`reports/scanner_research_end_to_end_2026-08-11.md` and
`reports/data_readiness_audit_2026-08-11.md`.

## What the results say

| Area | Result | Decision meaning |
|---|---|---|
| Score/ranking | Forward association is near zero; score encodes backward extension features | Do not interpret the score as a validated probability or directional edge |
| `entry_ok` | Current eligible cohort is weaker than the descriptive rejected cohort under the declared cost scenario | Do not add an inverse rule or new veto from this result |
| TP/SL/exit | 3,120 fixed-target configurations; global reality checks are not significant and robust medians are absent | No production TP/SL or exit candidate |
| Timing | Raw means are outlier-sensitive; trimmed and next-open results are weak/negative | Do not use headline means as typical outcomes |
| Portfolio/sizing | ATR-parity reduces drawdown in exploratory tests | Risk-construction hypothesis only; it does not repair selection quality |
| Null controls | Candidate does not beat matched null families | No promotion evidence |
| Data integrity | 485/2,047 raw-cache symbols have 50%+ jump flags; PIT and immutable history are missing | Confirmatory work remains blocked |

## Confirmatory work still waiting

1. H1 Gap-Reversal
2. H2 RVOL-Inversion
3. H3 ATR-Parity Sizing

These are pre-registered hypotheses, not production proposals. They require
clean independent data or a valid reserved holdout after the P1/P2 gates pass.

## What can be done next

### Option A — Data remediation first (recommended)

Acquire/version a PIT security master, delisting and ticker-lineage data;
classify corporate actions; preserve a complete immutable bar-cache snapshot;
and obtain observed spread, slippage, impact, fill-price, ADV and timestamp
records. Re-run P1/P2, then H1/H2/H3 on independent data.

This is the only path that can turn the current HOLD state into confirmatory
evidence. It does not authorize a production rule change.

### Option B — Run exploratory diagnostics on current data

Use the existing 129,947 intraday bars for label/path diagnostics and use the
current adjusted cache for additional descriptive gap/RVOL/ATR analysis.
These runs may improve measurement and implementation readiness, but must be
marked exploratory and cannot open H1/H2/H3 or locked OOS.

### Option C — Freeze research and strengthen the product position

Keep the production scanner unchanged and frame FinPilot as a daily market
reasoning and uncertainty product. Preserve counter-evidence, calibration
limits and no-performance-claim language. This is a product-position option
and requires Level B review before publication changes.

### Option D — Open locked OOS

Not available autonomously. This is a Level C decision because it consumes a
reserved validation partition and can affect release or risk conclusions. It
must remain closed until P1/P2 and the preceding phases pass, with explicit
human approval recorded.

## Recommended order

1. Data remediation and complete snapshot preservation.
2. P1/P2 gate re-evaluation.
3. Pre-registered H1/H2/H3 confirmatory runs.
4. P3-P8 only after their prerequisites pass.
5. Locked OOS only after all gates and human approval.
6. Any product or production change as a separate Level B/C decision.

No scanner, score, ranking, entry/exit, TP/SL, portfolio, publication,
broker, risk or live behavior changed in this summary.
