# Decision Quality Experiment — 2026-08-06

## Status

Research-only. This run does not change scanner gates, score weights,
portfolio construction, public wording or execution behavior.

Authority layer: Research. Decision level: Level A for the isolated
experiment; any production No-Trade rule would be Level B/C and requires
human approval.

## Reproducibility

- Command: `python -m research.decision_quality_experiments --csv data/backtest_out/full_universe_enriched.csv --cache data/price_cache --out data/backtest_out/decision_quality_2026-08-06.json`
- Input: `data/backtest_out/full_universe_enriched.csv`
- Target: five-day triple-barrier net return greater than zero
- Barriers: take-profit `2.0 * ATR`, stop-loss `1.0 * ATR`
- Cost assumption: `0.55%` round trip
- Canonical policy: one row per symbol-day, inherited from the barrier runner
- Resolved observations: `27,125`
- Missingness and path inventory: recorded in the JSON output

## Findings

The candidate universe had `27,125` resolved observations. The descriptive
veto surface marked `26,863` as rejected and `262` as eligible.

| Group | n | Positive net rate | Mean net return | Median net return |
| --- | ---: | ---: | ---: | ---: |
| All | 27,125 | 41.70% | 0.3568% | -1.4572% |
| Rejected | 26,863 | 41.79% | 0.3695% | -1.4314% |
| Eligible | 262 | 32.82% | -0.9465% | -3.1067% |

The rejection surface does not yet demonstrate rejection quality: rejected
observations perform almost identically to the full universe. The eligible
group is small and weaker in this sample, but this is not evidence that the
inverse rule is valid; selection, missingness and feature semantics require a
separate locked evaluation.

The most selective single veto was `gap_risk` (`n=806`), with a 67.74%
counterfactual loss rate. The other vetoes ranged from 57.74% to 59.61%.
These are descriptive associations, not approved thresholds or causal
claims. Every veto has an `insufficient_data` gate at fewer than 30 rows.

The preliminary loss taxonomy classified 15,814 negative-net observations:

- weak trend: 7,854
- near 52-week high: 2,533
- high volatility: 2,068
- gap risk: 546
- unclassified: 4,614

The unclassified share is material. The taxonomy must not be used as a
decision rule until path behavior, regime, liquidity and portfolio overlap
are measured explicitly.

Independent descriptive views were measured as support/reject states. The
support-count groups were all sufficiently large, but their results were not
monotonic. The zero-support group had a high mean return (`2.9415%`) and a
38.05% positive rate, indicating likely outlier or selection effects rather
than a reliable “reject everything” signal. No model committee is promoted.

## Decision

Current evidence supports keeping this as a research instrument only. It does
not support a production No-Trade engine, a new rejection threshold, a score
change or a public claim. Next experiments should add time/regime stability,
false-rejection analysis, causal-at-decision feature checks, sector and
correlation concentration, and a locked evaluation split.

Artifact: `data/backtest_out/decision_quality_2026-08-06.json`
Implementation: `research/decision_quality_experiments.py`
Tests: `tests/test_decision_quality_experiments.py`
