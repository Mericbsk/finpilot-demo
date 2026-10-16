# Outlier Dependence Audit v1: Liquidity and Cost Sensitivity

- Date: 2026-10-14
- Status: read-only audit. Pre-specified bands and cost scenarios are analytical conventions for this report. They are not policy, not a risk limit and not an approved trading parameter.
- Related: [outlier_dependence_baseline.md](outlier_dependence_baseline.md), [top_1pct_top_5pct_sensitivity.md](top_1pct_top_5pct_sensitivity.md), [execution_feasibility_audit.md](execution_feasibility_audit.md).

## 1. Inputs

- Dollar ADV: mean of (close x volume) over up to 20 sessions up to and including the signal date, from `data/price_cache`. Daily bars, historical. Source, adjustment and completeness for thinly traded names: UNVERIFIED.
- Notional sizes: 1,000 USD (research notional, illustrative) and 1,500 USD (15 % cap in `scanner/position_sizer.py` applied to the 10,000 USD default equity). Neither is an approved trading size.
- Bands (defined here, before the result was compiled): order notional as a share of 20-session dollar ADV:
  - a: up to 0.1 %
  - b: above 0.1 % up to 1 %
  - c: above 1 % up to 5 %
  - d: above 5 %

## 2. Order size versus dollar ADV

### 2.1 At 1,000 USD

| Band | Full (5,206) | Top 1 % (52) | Top 5 % (260) |
|---|---|---|---|
| a: up to 0.1 % | 4,956 (95.2 %) | 23 (44.2 %) | 185 (71.2 %) |
| b: 0.1 % to 1 % | 150 (2.9 %) | 8 (15.4 %) | 40 (15.4 %) |
| c: 1 % to 5 % | 74 (1.4 %) | 11 (21.2 %) | 18 (6.9 %) |
| d: above 5 % | 25 (0.5 %) | 10 (19.2 %) | 17 (6.5 %) |
| No usable ADV | 1 | 0 | 0 |

### 2.2 At 1,500 USD

| Band | Full (5,206) | Top 1 % (52) | Top 5 % (260) |
|---|---|---|---|
| a: up to 0.1 % | 4,890 (93.9 %) | 18 (34.6 %) | 172 (66.2 %) |
| b: 0.1 % to 1 % | 203 (3.9 %) | 10 (19.2 %) | 47 (18.1 %) |
| c: 1 % to 5 % | 79 (1.5 %) | 12 (23.1 %) | 19 (7.3 %) |
| d: above 5 % | 33 (0.6 %) | 12 (23.1 %) | 22 (8.5 %) |
| No usable ADV | 1 | 0 | 0 |

Reading: the full sample is liquid at both sizes. The top tails are not. The top-1 % share above 5 % rises from 19.2 % to 23.1 % between the two sizes.

## 3. Price level of the tails

| Entry price band | Full (5,206) | Top 1 % (52) | Top 5 % (260) |
|---|---|---|---|
| Below 1 USD | 52 (1.0 %) | 17 (32.7 %) | 31 (11.9 %) |
| 1 to 5 USD | 292 (5.6 %) | 20 (38.5 %) | 85 (32.7 %) |
| 5 USD and above | 4,862 (93.4 %) | 15 (28.8 %) | 144 (55.4 %) |

Sub-1 USD stocks are the main source of the tail. Spreads for these names are not measured. The dollar-ADV bands alone do not capture spread or price-impact cost.

## 4. Median liquidity

| Sample | Median 20-session dollar ADV |
|---|---|
| Full | 351.7 M USD |
| Top 1 % | 0.30 M USD |

## 5. Cost scenarios

Flat costs in percentage points are deducted from each signal's stored barrier return. They do not depend on size, volume or spread.

| Scenario | Source | Full | Excluding top 1 % | Excluding top 5 % |
|---|---|---|---|---|
| No cost (baseline) | stored | +0.3984 % | +0.1896 % | -0.1615 % |
| 0.20 pp | `_COST_FLAT_PCT` in `scanner/evaluate.py` (0.0020) | +0.1984 % | -0.0104 % | -0.3615 % |
| 0.55 pp | research scenario | -0.1516 % | -0.3604 % | -0.7115 % |
| 1.00 pp | research scenario | -0.6016 % | -0.8104 % | -1.1615 % |

Break-even flat cost (the cost at which the mean becomes zero):

- Full sample: about 0.40 pp.
- Excluding top 1 %: about 0.19 pp.
- Excluding top 5 %: the mean is already negative before any cost.

## 6. Cost convention caveats

- The Q3 audit (net expectancy) found cost conventions in the repository ranging from 0 to 100 bps across documents and code.
- The `core/paper_portfolio.py` header comment states 10 bps round-trip. Its code applies 5 bps slippage and 5 bps commission per side, which is 20 bps round-trip. The conflict is recorded and not resolved here.
- The 0.20 pp scanner constant is not verified as a round-trip cost for any specific venue.
- The flat scenarios omit size-dependent impact. Section 2 shows that the tails are size-sensitive, so flat costs understate tail risk for those names.

## 7. Limits

- Daily volume only. No intraday volume, no spread, no order book.
- The bands and scenarios are fixed in this report. No band or scenario was chosen after viewing its result to produce a preferred outcome.
- Historical volume may differ from volume available at the signal time and may be incomplete for thinly traded names (UNVERIFIED).
- No market-impact model is applied. Market impact is not measured.
