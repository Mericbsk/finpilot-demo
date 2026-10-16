# Net Expectancy Evidence Inventory (v1)

- Date: 2026-10-14
- Scope: Phases 0-4 of the FinPilot net trade expectancy investigation (read-only)
- Status: research audit. No production code, scanner, ranking, threshold, database row, publication or out-of-sample set was changed or opened.
- Output directory: `reports/net_expectancy_audit_v1_2026-10-14/`

## 0. Governance and state record

- Git HEAD: `3afa3f77d5487ed80b10d2776153b0e2cd377a3c` on branch `review/pending-2026-10-07`.
- Working tree: 74 porcelain entries. One pre-existing staged entry was not touched. No commit or push was made.
- Access method: SQLite URI with `mode=ro` and `PRAGMA query_only=ON`. The application `Database()` class was not initialized. No write was performed.
- Live database caveat: `data/finpilot.db` was locked by a running process when hashing was attempted, so no snapshot SHA-256 exists. Its modification time at capture was 2026-10-14 16:45 local. Counts below are time-stamped observations and are not reproducible from a frozen snapshot.

Input SHA-256 hashes captured for this audit:

| File | SHA-256 |
|---|---|
| `distribution/karne.py` | `40749445F8FDEA299F3570E43A572517305B25C6480BCF0861713032D456AB00` |
| `scripts/resolve_open_signals.py` | `9E4EFA491DCA9A9D12B65446468ABF0CF94D2C9D3D4C3035D6EFEA8E1A8D7014` |
| `core/paper_portfolio.py` | `CA58F2FAD7DD27DD2BE8F3A649997FCABAF8A8B29419D9DC60EBE3011E9A7EB0` |
| `scanner/evaluate.py` | `0EB9446D8A7A9509722AC5CCFF6944B415CA864DCF680B1A7DBFCB7972651B3D` |
| `scripts/backtest.py` | `5F8D704A371DE7E8F9CE9A1B309C8D066BAFB5E0096C2920B3F7507C51329308` |
| `data/backtest_out/fixed_target_full_universe_2026-08-11.json` | `35DADBC9F312202EBEE4A5B25C98058CEB0269E86CD0E4C1E20B77B70BEB2C0B` |
| `data/backtest_out/v2_exit_same_selection/v2_exit_same_selection_results.json` | `AAEE18BE191B737F63E4BDEC7CC8A6106723854E5EA26DFB2612259BA44E06AF` |
| `docs/governance/decision-log.md` | `043DE612C1FB5010506AA71B1E8220117A763BCF7229E9E8875D99AF8CFC5839` |

## 1. Origin of the reported figures

| Reported figure | Where it appears | Recomputed value (2026-10-14) | Source of calculation | Verified meaning |
|---|---|---|---|---|
| +0.40% expectancy per trade | Public karne / ledger, pitch deck spec, Morning Ledger strategy, launch plan | +0.3984% (decided rows only); +0.4014% (decided plus expired) | `distribution/karne.py`, `_overall_from_archive` (lines 79-108) | Mean of archived barrier-label returns. Gross. No cost term. |
| 5,206 signals | Same surfaces | 5,206 decided rows (1,565 wins, 3,641 losses) | Same function | Decided archived signal rows, not unique trades, not all archived signals. |
| 30.1% hit rate | Same surfaces | 30.06% (1,565 / 5,206) | Same function | Share of decided rows that reached take-profit before stop-loss. |
| 3.36x win/loss asymmetry | Same surfaces | 3.369 (average win +4.2825% / average loss -1.2711%) | Same function | Ratio of mean win distance to mean loss distance. Documents round this to 3.36; the recomputed value rounds to 3.37. Minor, but should be corrected at source. |

Arithmetic check: 0.3006 x 4.2825 + 0.6994 x (-1.2711) = +0.398 percent. The reported figure is internally consistent with the stored labels.

### 1.1 Derivation chain

1. The scanner writes a signal with `entry_price`, `take_profit` and `stop_loss` into `signals_archive.payload_json`.
2. `scripts/resolve_open_signals.py` (lines 221-270) reads daily OHLC bars from yfinance with `auto_adjust=True`.
   - Entry is the stored `entry_price` (signal-time price).
   - Bars are considered only after the signal date.
   - If the day's High is at or above take-profit, the outcome is `resolved_win` with return `(TP - entry) / entry`.
   - Otherwise, if the day's Low is at or below stop-loss, the outcome is `resolved_loss` with return `(SL - entry) / entry`.
   - The take-profit test is evaluated before the stop-loss test on the same bar.
   - If neither is hit within 21 trading days, the outcome is `expired_win` or `expired_loss` at the final close.
3. The resulting values are stored in `resolved_pct_barrier` and `resolved_status_barrier` (lines 113-114).
4. `distribution/karne.py` aggregates only rows whose status is `resolved_win` or `resolved_loss`, and whose `resolved_pct_barrier` is not null. Expired rows are excluded from the published figure.

### 1.2 Denominator and count history

| Population | Count | Note |
|---|---|---|
| Total `signals_archive` rows (2026-10-14) | 5,748 | Date range of `ts`: 2025-09-12 to 2026-09-09 |
| Decided rows (`resolved_win` + `resolved_loss`) | 5,206 | Used by karne overall |
| Expired rows (`expired_win` + `expired_loss`) | 10 | Excluded by karne |
| Unresolved rows (NULL status) | 532 | Excluded |
| Distinct symbol-days across all archived rows | 4,318 | Overlapping signals are not de-duplicated by karne |
| Decided plus expired | 5,216 | Matches the 5,216 count quoted in the 2026-08-05 documentation |
| First decided-or-expired signal per symbol-day | 3,802 | Used for overlap sensitivity |

Other counts quoted in internal documents (5,719 in the 2026-07-28 audit; 5,206 and 5,216 in August; 5,748 in the 2026-10-09 receipt) are explained by the archive growing over time and by different inclusion rules. They are not independent samples.

### 1.3 Public and investor-facing use (to be reviewed by a human)

- `docs/strategy/Landing_Denetimi_2026-08-06.md`: landing ledger strip states "5206 kapali - %30 isabet - +%0.40 beklenti".
- `docs/strategy/Morning_Ledger_Urun_Stratejisi_Konsolide_2026-08-05.md`: "beklenti +%0.40/islem".
- `docs/pitch_deck_presentation_spec_2026-09-07.md`: "+0.40% ... barrier-based expectancy".
- `docs/ops/Lansman_Yurutme_Plani_2026-08-05.md`: headline proposal "beklenti +%0.40/islem".

These surfaces describe the figure as expectancy without stating that it is gross, excludes costs and uses ideal barrier fills. Changing any public or investor wording is a human decision (Level C) and is not performed by this audit.

## 2. Evidence level classification (Phases 2 and 3)

| Level | Status | Available evidence | Records | Date coverage | Missing or limiting fields | Reproducible |
|---|---|---|---|---|---|---|
| 1. Signal evidence | Met | Archived scanner signals with entry, take-profit, stop-loss in payload | 5,748 rows; 4,318 symbol-days; all 5,206 decided rows have complete payloads | 2025-09-12 to 2026-09-09 | Selection rule for archive inclusion not documented | Yes, for the live DB state at capture time |
| 2. Forward-price evidence | Met with integrity warnings | Daily OHLC from yfinance; `resolved_pct_t5` (5,213 non-null) and barrier labels (5,216) | As above | As above | Adjusted-price history was not frozen; 08-12 gate reported 148 symbols with large jumps in adjusted-close audits | Partly; no frozen price snapshot |
| 3. Rule-based simulation | Partially met | Explicit per-signal TP, SL and 21-trading-day expiry | 5,216 barrier outcomes | As above | No position sizing; equal weight per signal; no portfolio constraint; daily bars only; same-bar TP-first convention | Yes, given the same DB state and bars |
| 4. Execution-aware backtest | Not met | Assumed slippage and commission in separate research runs only | Research runs 2026-07-15 and 2026-08-11 | 2025-09 to 2026-07 | No observed spread, no fills, no fill ordering, no intraday prices, no defensible execution price | Research artifacts exist; costs are assumptions |
| 5. Actual execution | Not met | `alpaca_orders` table with 11 rows: 10 PENDING_NEW, 1 ACCEPTED | 11 orders; 0 fills | No fill timestamps | `filled_price`, `filled_qty` and `filled_at` are all null. `trades`, `positions`, `execution_events`, `execution_intents`, `execution_controls`, `portfolios` all contain 0 rows. `logs/slippage_tracker.json` does not exist. Redis paper keys matching `*paper*`: 0 | Not applicable |

Highest evidence level currently supported: Level 3 (partial). The archive supports a rule-based, gross, per-signal barrier simulation. It does not support execution-aware or realized trading results.

### 2.1 Three separate performance questions

- Track A, signal quality (gross forward-price statistics only): Available. Gross barrier expectancy +0.40% on decided rows, median -0.64%. T+5 close statistics exist but are not usable until the price data is audited (section 5).
- Track B, hypothetical trade expectancy: Partially defined. The archived signals carry explicit entry, take-profit, stop-loss and horizon rules. Position sizing, portfolio construction and an execution model are not defined for the archive. `buy_signals` (position sizes) contains 0 rows.
- Track C, actual executed trade expectancy: Not established. Eleven broker orders exist without any fill. No realized P&L can be reconstructed from the available records.

## 3. Evidence summary for the investor question

- Gross barrier expectancy is reproducible from stored labels.
- No measured transaction cost exists in the archive, the labels or the broker tables.
- No realized net expectancy exists.
- Concentration and outlier effects are material (see the calculation spec and readiness matrix).

## 4. Transaction-cost inventory (Phase 4)

Classification key: A = historically measured; B = supported by an external fee schedule; C = estimated from a documented model; D = assumed for scenario analysis; E = missing.

| Cost component | Where found | Value found | Classification | Notes |
|---|---|---|---|---|
| Bid-ask spread | Evidence matrix, RX audit | Observed spread rate 0% | E | No bid/ask history in any table. `spread_bps` appears only as a CLI argument in a research protocol script. |
| Entry and exit slippage | `core/paper_portfolio.py` | 5 bps per side ("one-way market impact estimate") | D | Applied on entry and exit. |
| Slippage (backtest) | `scripts/backtest.py` | `slippage_bps=10.0` | D | Per-side or round-trip definition not documented. |
| Slippage (tracker) | `core/slippage_tracker.py` | Tracker file `logs/slippage_tracker.json` | E | File does not exist, so no measured fills. |
| Commission | `core/paper_portfolio.py` | 5 bps per side ("broker commission per side") | D | No broker fee schedule or statement found. |
| Commission (backtest) | `scripts/backtest.py` | `commission_bps=5.0` | D | Definition not documented. |
| Round-trip flat cost (scanner) | `scanner/evaluate.py` line 68 | 0.20% round-trip ("retail fallback") | D | Used for cost labels. |
| Round-trip flat cost (research) | Research runs | 0.25-0.30% low, 0.55% baseline, 1.00% stress, 0.50% (PIT) | D | Scenario values, not measured. |
| Exchange and regulatory fees | Not found | None | E | |
| Borrow costs (short side) | Not found | None | E | |
| Currency conversion | Not found | None | E | Relevant if the investor-facing figure is in another currency. |
| Market impact | `core/paper_portfolio.py` | 5 bps per side estimate | D | No volume- or size-dependent model. |
| Order timing | Not found | None | E | Daily bars only. |
| Position size | `scripts/backtest.py`, research runs | Research notional 1,000 USD | D | Archive has no sizing. |
| Liquidity constraint | Scanner threshold | 10-day average share volume at least 300,000 | D | Share volume, not dollar volume. Does not measure spread or capacity. |
| Capacity | Scanner export field | `portfolio_capacity_unknown` | E | |

### 4.1 Cost inconsistencies that must be resolved before any net figure

- `core/paper_portfolio.py` header comment states "10 bps round-trip". The code applies 5 + 5 bps on both entry and exit, and records `cost_bps = 20` for a round trip. The comment and the code disagree.
- The realized-cost conventions differ across repositories: 0 bps (archive labels), 20 bps (scanner flat, research v2 exit test, paper code), 25-30 bps (low scenario), 50 bps (PIT), 55 bps (research baseline), 100 bps (research stress). No single documented model exists.
- `core/config.py` line 131 sets `transaction_cost` default 0.001 (10 bps) for the DRL configuration. This is a separate convention.

## 5. Data integrity observations

- `resolved_pct_t5` contains implausible values. Minimum -96.21%, maximum +11,990.91% (DXST, 2026-03-03). 166 rows have absolute value above 50%, 35 rows above 100%. Mean 13.66%, median -1.28%. Extremes concentrate on a few dates: 2026-03-01 (34 rows), 2026-03-03 (24), 2025-10-05 (9), 2025-10-06 (8), 2025-09-18 (8), 2025-09-16 (8). This is treated as a data-integrity defect, not as performance.
- Barrier returns are bounded by the take-profit and stop-loss distances, so they do not have this extreme-value problem. They still depend on the same underlying bars.
- 2026-03-03 contains 473 decided rows with mean +1.03% and median -1.47%. Excluding that date changes the decided-only mean from +0.398% to +0.335%.
- Every decided row has positive entry, take-profit and stop-loss values (5,206 of 5,206).
- The archive's latest timestamp is 2026-09-09. Whether archiving stopped or simply has no newer signals is unverified.
- Adjusted-close audits in the 2026-08-12 gate reported 148 symbols with large jumps. Whether the archive labels are affected is unverified.
- `scripts/resolve_open_signals.py` uses `auto_adjust=True` while entry prices are stored at signal time. Corporate actions inside the horizon could create a mismatch. Magnitude is unverified.

## 6. Unverified items

- Snapshot hash of `data/finpilot.db` (file locked during capture).
- Whether `signals_archive` contains all scanner signals or only published or eligible picks. Selection rule not documented.
- Reconstruction of the production ranking logic that generated each archived signal.
- Redis-held paper trading history. Current paper keys: 0. Earlier state cannot be verified.
- Whether the 11 `alpaca_orders` rows correspond to a paper or a live account. Environment field is not populated.
- Quantities in `alpaca_orders` are not validated (for example, one order is for 5,234 shares). Sizing basis unknown.
- The sign and size of any stop-gap effect on losses. The resolver uses the stop level even when the day opens below it.
