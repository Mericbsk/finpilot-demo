# High-RVOL Deep Audit

## Conclusion

The previous `$10,000` high-RVOL result is not robust evidence of a usable
return strategy. It is dominated by four validation dates and extreme row
outcomes in a short, overlapping `c2c_5d` sample.

## What created the nominal result?

The validation period contains 14 selected dates and 496 selected rows.
Under equal-weighting, the four largest date-level net returns were:

| Date | Rows | Portfolio net return | Row median | Row maximum |
|---|---:|---:|---:|---:|
| 2026-07-22 | 37 | `+153.52%` | `-2.26%` | `+5,800.38%` |
| 2026-07-16 | 64 | `+133.79%` | `-1.46%` | `+8,652.03%` |
| 2026-07-20 | 51 | `+93.05%` | `-0.99%` | `+3,778.79%` |
| 2026-07-21 | 74 | `+51.16%` | `-0.94%` | `+4,067.42%` |

These four dates represented `103.35%` of the total date-level net-return
sum. The row medians on all four dates were negative even though their means
were strongly positive. This is a classic concentration and tail-sensitivity
warning, not evidence that most high-RVOL observations performed well.

## Stress tests from `$10,000`

| Audit scenario | Equal-weight final | ATR-parity final |
|---|---:|---:|
| Original 14-date compounding | `$147,297` | `$20,822` |
| Remove four largest positive dates | `$8,516` | `$9,847` |
| Every fifth validation date only | `$8,712` | `$9,894` |
| Clip each row outcome to `[-50%, +50%]` | `$7,807` | `$9,540` |
| Clip each row outcome to `[-20%, +20%]` | `$7,930` | `$9,471` |

The equal-weight headline result disappears under every basic robustness
check. ATR-parity limits concentration, but it does not establish positive
return: the robustness scenarios remain below the initial `$10,000`.

The selected rows include 11 outcomes above `+50%` and 12 below `-50%`.
Several individual outcomes exceed `+3,000%`, which is also consistent with
the repository's previously documented price-integrity concerns. This audit
does not determine whether each jump is a corporate action, stale price,
cache issue or genuine tradable return; immutable prior snapshots and
corporate-action provenance are still missing.

## What the result does and does not say

The data supports only the following narrow statement: high-RVOL happened to
coincide with a small set of extreme positive outcome rows during this
validation block. It does **not** support a high-RVOL entry rule, a dollar
return promise, a capacity claim, or a product performance claim.

The audit also uses overlapping five-day outcomes. The every-fifth-date
sensitivity is a rough non-overlap proxy, not a replacement for a properly
constructed non-overlapping event portfolio. No observed fills, spreads,
turnover, ADV, capacity or locked OOS are available.

## Decision

High-RVOL is downgraded from a nominal budget leader to an exploratory
data-quality/risk-context candidate. It may be shown as context such as
“activity is unusually high; outcome evidence is tail-sensitive,” but it must
not be presented as a positive selector or expected-return estimate.

## Traceability

- Runner: `research/high_rvol_deep_audit_2026_08_12.py`
- Artifact: `data/backtest_out/high_rvol_deep_audit_2026-08-12.json`
- Source: `data/backtest_out/full_universe_enriched.csv`
- Focused test: `tests/test_high_rvol_deep_audit_2026_08_12.py`
- Parent budget artifact: `data/backtest_out/budget_return_battery_2026-08-12.json`
- Production change: `false`; locked OOS: `not_opened`
