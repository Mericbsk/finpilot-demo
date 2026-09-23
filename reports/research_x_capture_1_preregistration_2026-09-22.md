# RESEARCH-X / RX-CAPTURE-1

## Capture & Exit Battery — Pre-Registration Draft
**Research ID:** RX-CAPTURE-1
**Version:** v1.0-LOCKED
**Date:** 2026-09-22
**Research Level:** A
**Status:** APPROVED / LOCKED — Meriç approval 2026-09-22. Estimand audit (§52a) PASS.
**Production Impact:** NONE
**H4:** FROZEN / UNTOUCHED

> This file is LOCKED. Rules, estimand, cost model, exit families, temporal
> split, concentration criteria, multiple-comparison method and the verdict
> engine cannot change from this point. Runner and execution follow §53.

---

## 1. PURPOSE
Bu araştırmanın amacı, zaten seçilmiş ve selection tarafı sabitlenmiş bir historical cohort içinde gözlenen 5 günlük Maximum Favorable Excursion (MFE)'nin ne kadarının:

1. önceden tanımlanmış,
2. path-aware,
3. future-information kullanmayan,
4. transaction-cost/slippage varsayımlarını içeren,
5. deterministic olarak uygulanabilir

exit kuralları tarafından yakalanabileceğini ölçmektir.

Araştırma:

> **"MFE'nin ne kadarı teorik olarak gözlenmiş?"**

sorusundan farklı olarak:

> **"MFE'nin ne kadarı önceden tanımlı bir exit mekanizmasıyla ex-ante olarak capture edilebilirdi?"**

sorusunu test eder.

---

## 2. NON-GOALS
Bu araştırma:

- yeni stock-selection kuralı aramaz,
- composite score'u değiştirmez,
- ranking'i değiştirmez,
- scanner davranışını değiştirmez,
- yeni feature seçmez,
- buy signal üretmez,
- short signal üretmez,
- production strategy seçmez,
- en iyi exit parametresini post-hoc aramaz,
- H4'ü yeniden açmaz,
- locked OOS açmaz.

Özellikle `MFE > 0` → `profit realizable` ve `capture > 0` → `production-ready strategy` anlamlarına GELMEZ.

---

## 3. SCIENTIFIC QUESTION
Primary research question:

> **Fixed historical selection cohort üzerinde, önceden tanımlanmış path-aware exit kuralları 5 günlük MFE'nin maliyet sonrası anlamlı bir bölümünü capture edebilir mi?**

Secondary questions:

1. Capture hangi exit family'lerinde oluşuyor?
2. Capture median ve tail davranışında nasıl dağılıyor?
3. Sonuç birkaç gün/sembol tarafından mı taşınıyor?
4. Transaction costs sonucu ne kadar değiştiriyor?
5. First-touch mantığı ile end-of-horizon sonuçları arasındaki fark nedir?
6. Farklı exit kuralları aynı MFE'yi mi yakalıyor, yoksa farklı path'lerden mi faydalanıyor?
7. Sonuç farklı zaman dönemlerinde aynı işareti koruyor mu?

---

## 4. PREVIOUS EVIDENCE
Mevcut historical evidence:

- `resolved_pct_t5` MFE olarak export'ta mevcut.
- `mae_t5` mevcut.
- Current historical cohort yaklaşık 34,762 observation içermektedir.
- MFE export coverage mevcut cohort'ta tamdır.
- `price_cache` yaklaşık 2,047 sembol için günlük OHLCV sağlamaktadır.
- `price_cache` 2024-09 sonrası historical path reconstruction için kullanılabilir.
- Önceki TP/SL bataryaları robust ekonomik destek üretmemiştir.
- High-RVOL / first-touch dahil bazı önceki exit araştırmaları maliyet sonrası desteklenmemiştir.

Bu sonuçlar RX-CAPTURE-1'in prior evidence'ıdır. Ancak `previous TP/SL NOT_SUPPORTED`, `all possible path-aware exits NOT_SUPPORTED` sonucunu önceden zorunlu kılmaz; MFE'nin yüksek olması da `exit rule supported` anlamına gelmez.

---

## 5. FIXED SELECTION PRINCIPLE
RX-CAPTURE-1'de selection değişken değildir. Selection cohort `LOCKED` olarak kabul edilir. Exit araştırması `selection = fixed / exit = variable` şeklinde yapılacaktır. Selection değiştirilecekse `NEW RESEARCH LINE` gerekir.

---

## 6. INPUT DATA
Primary historical input: `data/backtest_out/full_universe_enriched_eod_only.csv`
Expected locked SHA: `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`
Bu SHA değişirse `INPUT_MISMATCH` ve execution durdurulur.

Secondary/path input: `data/price_cache/` — path data version ve kapsamı execution öncesinde hash/manifest ile kaydedilecektir.

---

## 7. POPULATION
Population: historical export, required selection fields available, valid `c2c_5d`, valid scan date, valid symbol, deduplicated `(symbol, scan_date)`.
Exact final population `MUST BE MEASURED AND FROZEN BEFORE LOCK`. Expected reference `n ≈ 34,762`; expected n, actual locked n'nin yerine geçmez.

---

## 8. DEDUPLICATION — MUST BE EXPLICIT
NS-1 verification sırasında bulunan definition debt nedeniyle deduplication semantics açıkça kilitlenecektir.

Canonical rule: `one row per (symbol, scan_date)`.
Tie handling açıkça tanımlanmalıdır. Önerilen canonical specification:

```
sort by: scan_date ASC, symbol ASC, scan_ts ASC, original_row_position ASC
drop_duplicates(subset=["symbol","scan_date"], keep="first")
```
Böylece earliest lexical `scan_ts` ve duplicate `scan_ts` durumunda original row position deterministic olur. Bu tanım lock öncesinde ayrıca audit edilmelidir.

---

## 9. PERCENTILE DEFINITION
NS-1 independent verification sırasında görülen floating-point boundary farkı nedeniyle percentile method açıkça kilitlenecektir. `quantile_method = [TO BE LOCKED]` hem runner, hem independent verifier, hem report tarafından aynı mathematical definition ile uygulanacaktır. `<=` / `<` boundary semantics de açıkça yazılacaktır.

---

## 10. TIME BOUNDARY
Her observation için `T0 = scan_date`. Exit path `T+1 → T+5` ile sınırlıdır. T0 sonrasında ortaya çıkan bilgi T0 kararında kullanılamaz. Exit rule `ex-ante definable` olmalıdır.

---

## 11. LOOK-AHEAD RULE
Bir exit decision için kullanılan bilgi `available_at_or_before_decision_time` olmalıdır. Yasaklar: future high/low/close/volume, future realized MFE/MAE, future ranking/signal/regime. Ancak bunlar `OUTCOME / EVALUATION` olarak kullanılabilir.

---

## 12. PRIMARY OUTCOME (locked definition)
Primary estimand: **median of per-position net capture** over valid observations:

```
NC_i = GrossExitReturn_i - Cost_i
primary_estimand = Median( { NC_i : i in valid observations } )
```

**Entry/exit price convention (locked):** T0 = scan_date; entry price = export
`price` field (scan-day price; existing `entry_drift <= 0.5` check preserved).
Forward path = T+1..T+5 daily OHLC from `price_cache`. If no exit rule triggers,
exit = T+5 close. GrossExitReturn_i = (exit_price_i - entry_price_i)/entry_price_i
in percent.

**Same-day ambiguity (locked, per section 25):** if within one daily bar both
`high >= target` and `low <= stop` and true intraday order is unknown, that
observation is EXCLUDED from that candidate's primary estimate (stop-first is
NOT assumed). This is a deliberate departure from the prior barrier battery's
"stop-first same-bar tie" convention; noted in the estimand audit. Therefore the
primary estimand is the median over that candidate's VALID (non-ambiguous)
observations; ambiguous count and excluded fraction are mandatory reported.

`capture_ratio_i = NC_i / MFE_i` is reported ONLY where `MFE_i > 0`; it is a
secondary normalized metric and NEVER the primary (small-MFE denominator blow-up).

**Terminology (locked):** MFE = opportunity envelope; exit return = rule-realized
outcome. The primary result is never phrased as "we captured X% of MFE".

---

## 13. CAPTURE RATIO
Secondary normalized metric: `capture_ratio = net_capture_pct_5d / MFE`. `MFE <= 0` observation'larda ratio `NA`. Ratio primary outcome'un yerine geçmez.

---

## 14. GROSS VS NET
Her exit family için `gross capture` ve `net capture` ayrı raporlanacaktır; `gross edge` ile `economic edge` ayrılabilir.

---

## 15. COST MODEL (locked semantics)
Verified against `research/full_universe_barrier_backtest.py` (lines 335-338,
366-368): the 0.55 figure is **percentage points per round-trip position**,
subtracted directly from expectancy (`cost_adjusted = expectancy - 0.55`). It is
NOT per-turnover and NOT per-leg. RX-CAPTURE-1 inherits this exact semantic.

- **PRIMARY cost:** 0.55% round-trip per position (Cost_i = 0.55).
- **STRESS cost:** 1.00% round-trip per position (Cost_i = 1.00).
- No slippage/cost double-counting: the single round-trip figure is the whole
  cost; a separate slippage term is NOT added.
- Both scenarios always reported; post-hoc favorable cost selection forbidden.

---

## 16. EXIT FAMILY DESIGN (finite, locked before run)
Exit families are a finite, pre-registered battery — NOT a grid. Parameters come
from literature/trading convention, NOT from looking at this dataset's outcomes
(post-hoc optimization forbidden).

- **E0 — Hold-to-horizon baseline:** exit at T+5 close.
- **E1 — Fixed target:** three pre-locked candidates: +3%, +5%, +10%.
- **E2 — ATR trailing:** three pre-locked candidates: 1.5 ATR, 2.0 ATR, 3.0 ATR
  (ATR from the export `atr_pct_real` field at T0; trailing stop = highest close
  since entry minus k*ATR, checked on each T+1..T+5 close).
- **E3 — Partial exit (locked):** 50% of the position exits at a fixed +3%
  target; the remaining 50% exits at T+5 close (no trailing). Total position
  net capture = 0.5*NC_first + 0.5*NC_second, single round-trip cost applied once.

Family membership is fixed at lock; no post-hoc family splitting to evade the
multiple-comparison correction. Exact family set and parameters `MUST BE LOCKED
BEFORE EXECUTION`.

---

## 17. NO GRID SEARCH
Yasaktır: 100 thresholds, 50 ATR multipliers, 20 trailing values, best parameter/subgroup/day selection. Araştırma `finite predefined battery` olmalıdır. Parametreler `LOCKED BEFORE RUN`.

---

## 18. PARAMETER COUNT
Exit family başına parameter sayısı mümkün olduğunca sınırlı tutulacaktır. Amaç `scientific question` olup `optimization surface` oluşturmak değildir. Çok geniş parameter battery gerekiyorsa `NEW RESEARCH LINE` olarak ayrı preregistration yapılmalıdır.

---

## 19. PRIMARY SUCCESS CRITERIA
RX-CAPTURE-1'in primary verdict kriterleri lock öncesinde matematiksel olarak tanımlanacaktır. Önerilen minimum gate — bir exit family ancak tamamı sağlanırsa primary support alabilir:

```
1. net_capture median > 0
2. predefined CI excludes 0
3. result survives predefined cost model
4. result is not driven by a tiny number of days
5. result has predefined temporal replication support
6. result is reproduced by independent implementation
```
Bir kriter karşılanmazsa `CAPTURE_NOT_SUPPORTED` veya uygun ara state. Exact threshold'lar lock öncesinde belirlenecektir.

---

## 20. MFE CAPTURE IS NOT ENOUGH
Bir rule `captures positive MFE` gösterse bile primary support otomatik verilmez. Net return, distribution, median, tail, cost, temporal stability, day concentration birlikte değerlendirilir.

---

## 21. TEMPORAL VALIDATION (locked)
Chronological population split: **early = first 40% / middle = middle 20%
(descriptive buffer) / late = last 40%**.
Primary temporal requirement: a candidate's primary estimand is supported in
early AND remains same-signed in late.
**Minimum temporal evidence (locked):** early >= 20 distinct scan days, late >=
20 distinct scan days, AND >= 100 valid observations per primary period. If any
fails: `INSUFFICIENT_TEMPORAL_EVIDENCE`. Note: current cohort has ~54 c2c_5d
days, so 40/40 gives ~21 days per end; the locked threshold is checked against
the measured locked n, with no slack — if unmet, that is a valid result.

---

## 22. DAY-CLUSTERED ROBUSTNESS (locked)
Daily clustering is required. Minimum reports: day-level distribution; top-1 /
top-3 / top-5 day contribution to total net capture; day-clustered bootstrap.
**Concentration warning (locked):** if any single scan day contributes > 25% of a
candidate's total net P&L contribution -> `CONCENTRATION_WARNING` (a separate
state; warning != automatic failure). A `4 days drive 90% of capture` structure
is reported explicitly; tail-driven result may be `NOT ROBUST` per the locked
verdict engine.

---

## 23. SYMBOL CONCENTRATION
`symbol concentration` raporlanacaktır: top symbols, top 1%, top 5%, contribution to total capture (gerekirse).

---

## 24. PATH-AWARE FIRST TOUCH
First-touch exit araştırılıyorsa `T+1 ... T+5` günlük OHLC path'i üzerinden `first target touch / first stop touch / same-day ambiguity` tanımlanmalıdır. Günlük OHLC `high/low/close` aynı gün içinde hem target hem stop seviyesini gördüğünde execution ordering varsayımı açıkça belirtilmelidir. Bu varsayım `LOCK REQUIRED` ve sonucu etkileyebilecekse sensitivity olarak ayrıca raporlanmalıdır.

---

## 25. SAME-DAY AMBIGUITY
Aynı bar içinde hem `high >= target` hem `low <= stop` ise ve gerçek intraday order bilinmiyorsa `DO NOT ASSUME FAVORABLE ORDER`. Exact convention lock edilmelidir (örn. `conservative stop-first` veya `ambiguous → excluded`). Bu seçim post-hoc yapılamaz.

---

## 26. PARTIAL EXIT
Partial exit kullanılıyorsa `fraction / target / remaining position / remaining exit / maximum horizon` önceden kilitlenmelidir. Partial exit sonucu `capture` olarak raporlanır; MFE'nin tamamıymış gibi sunulmaz.

---

## 27. PRIMARY / SECONDARY METRICS
**Primary:** `net_capture_pct_5d` (veya lock öncesi kesinleştirilecek primary estimand).
**Secondary:** gross_capture_pct, capture_ratio, median, mean, hit rate, MFE, MAE, big-loss rate, tail capture, max adverse excursion, holding duration.
**Diagnostic:** day concentration, symbol concentration, regime, price bucket, ATR bucket, MFE bucket. Diagnostic metrics hypothesis generation içindir.

---

## 28. BIG-LOSS REPORTING
Capture araştırması selection araştırması değildir; yine de risk distribution raporlanmalıdır. `c2c_5d <= -10%` gibi mevcut locked definition kullanılacaksa exact threshold preregistration'a yazılmalıdır. Exit rule'un `big-loss reduction` sağlaması ayrıca raporlanabilir ama `screening value` ile karıştırılmamalıdır.

---

## 29. OPPORTUNITY COST
Exit rule yalnızca kayıpları azaltıyorsa yeterli değildir; `positive tail preserved?` sorusu incelenmelidir. Örn. top-5% MFE contribution, top-decile outcome, positive-tail realization raporlanabilir.

---

## 30. BASELINE
En az bir baseline: `hold-to-T+5` veya mevcut locked historical baseline kullanılmalıdır. Exit strategy bununla karşılaştırılır. Baseline definition `LOCK REQUIRED`.

---

## 31. NO POST-HOC BASELINE
Baseline sonucu görüldükten sonra `baseline değiştirmek` yasaktır.

---

## 32. RANDOM / NULL CONTROL (locked decision)
Random seed locked: `seed = 20260922`. Block-bootstrap: `B = 2000`, 5-day
consecutive-date blocks (ANS-1/H4 contract), percentile CI at the Holm-adjusted
level.
**Random control decision (locked):** NOT USED for this capture/exit line, and
the reason is recorded here: a null-shuffle tests whether a FEATURE carries
signal. RX-CAPTURE-1 has no feature/signal to shuffle — selection is LOCKED and
the exit rule is a deterministic function of the price path, so there is no
flag to permute. The day-clustered block bootstrap already supplies the
null/sampling distribution for the median estimand. Had a random control been
used, seed/R/mechanism/block would have been locked here; it is deliberately
absent, with justification.

---

## 33. MULTIPLE COMPARISON (locked)
The primary exit family is a `predefined set` (E0 baseline + E1 + E2 + E3
candidates). Adjustment method: **Holm correction, family-wise** (stronger than
Bonferroni for a finite candidate set while preserving family-wise error
control). Family count and membership are fixed at lock. "Best exit" cannot be
selected post-hoc and declared a statistical winner.

---

## 34. ECONOMIC GATE
Primary economic result `NET` olmalıdır. Gross-positive fakat net-negative sonuç `ECONOMIC_NOT_SUPPORTED` olarak değerlendirilebilir; bu classification exact verdict protocol'ünde lock edilecektir.

---

## 35. MFE DATA CONSISTENCY AUDIT
Execution öncesi `resolved_pct_t5` tanımının `MFE` olduğu kaynak/hesap zinciri yeniden doğrulanmalıdır. Önceki auditlerde MFE `mean ≈ 14.34% / median ≈ 4.18%` gözlendi. Ancak eski raporlarda farklı MFE population/summary değerleri bulunduğu için `MFE VERSION RECONCILIATION` lock öncesi zorunludur. Eski `46,080 / 0.24%` ve yeni `46,581 / +0.37%` gibi farklı capture/MFE özetleri aynı metric sanılarak birleştirilmeyecektir.

---

## 36. PRICE CACHE AUDIT
`price_cache` için lock öncesi kontrol edilmelidir: symbol count, date coverage, missing days, duplicate dates, OHLC validity, corporate-action treatment. Özellikle `T+1 ... T+5` coverage hesaplanmalıdır.

---

## 37. DATA SUFFICIENCY
Gerekli future path data eksikse `NO IMPUTATION` uygulanacaktır. Eksik path `unavailable` olarak raporlanmalıdır; eksikliği sonradan favorable assumption ile doldurmak yasaktır.

---

## 38. SURVIVORSHIP
Path data coverage yalnızca mevcut symbol dosyalarına dayanıyorsa `survivorship limitation` raporlanmalıdır. Delisted symbols eksikse sonuç `historical universe fully representative` olarak sunulamaz.

---

## 39. CORPORATE ACTIONS
Split/dividend adjustment `LOCK REQUIRED` olmalıdır. Price cache ile export aynı price basis'te değilse `INPUT_MISMATCH` veya `DATA_CONVENTION_MISMATCH` oluşturulmalıdır.

---

## 40. INDEPENDENT IMPLEMENTATION
Final result'tan sonra `different implementation path` zorunludur (tercihen different data loader / path traversal / aggregation). Independent verifier runner JSON üzerinden result-copy yapamaz.

---

## 41. DISCREPANCY PROTOCOL
Her discrepancy `DETECT → ISOLATE → CLASSIFY → ROOT CAUSE → IMPACT ON PRIMARY VERDICT` şeklinde incelenir. Yasak: average / ignore / force-match / rewrite history.

---

## 42. VERIFICATION STATES
`VERIFICATION_PASS / VERIFICATION_DISCREPANCY / VERIFICATION_INCONCLUSIVE`. Primary result etkilenmiyorsa discrepancy yine raporlanmalıdır.

---

## 43. DETERMINISM
Runner iki kez çalıştırılmalıdır; aynı input/seed/protocol/environment ile sonuçlar karşılaştırılır. JSON/report SHA farklıysa fark açıklanmalıdır.

---

## 44. ARTIFACTS
Beklenen: RX-CAPTURE-1 preregistration, runner, result JSON, report, independent verification script+JSON, hash manifest, governance entry. Runner ve result `LOCK sonrası` üretilir.

---

## 45. PRODUCTION SAFETY
Bu research line boyunca scanner/score/ranking/flags/database/scheduler/publication `unchanged` olmalıdır. Production impact `NONE`.

---

## 46. H4 SAFETY
Bu araştırma H4A/H4B/H4C/H4D dosyalarını değiştirmeyecektir. H4 result'ları RX-CAPTURE-1'in hypothesis'ine evidence olarak kullanılmayacaktır.

---

## 47. FAILURE STATES / VERDICT ENGINE (locked logic)
The verdict engine is an evidence gate, NOT an optimizer that picks "the best
exit". A candidate is `CAPTURE_SUPPORTED` only if ALL of the following hold:

```
1. primary median net capture > 0
2. Holm-adjusted CI excludes 0
3. holds under PRIMARY cost (0.55%)
4. STRESS cost (1.00%) result also reported
5. early and late same-signed
6. minimum temporal evidence met (>=20 days, >=100 obs per period)
7. no concentration failure (>25% single-day contribution triggers WARNING,
   and the verdict cannot be SUPPORTED while a warning is unresolved)
8. same-day ambiguity excluded fraction within the predefined bound
9. independent implementation reproduces the result (VERIFICATION_PASS)
```
Other states: `CAPTURE_PARTIAL` (primary improvement present but temporal
replication insufficient, concentration warning, stress degradation, or another
predefined secondary gate fails) / `CAPTURE_NOT_SUPPORTED` (primary CI contains
zero or median net capture <= 0) / `CAPTURE_UNSTABLE` (primary positive but
day-concentration, temporal reversal, or cost sensitivity makes it unstable) /
`INSUFFICIENT_DATA` / `INPUT_MISMATCH` / `PROTOCOL_DEVIATION` /
`VERIFICATION_INCONCLUSIVE`.

---

## 48. WHAT WOULD COUNT AS SUPPORT?
Support için yalnızca `positive mean` yeterli değildir. Support, lock edilmiş primary criteria'nın tamamının karşılanmasına bağlıdır (örn. net median > 0 + CI excludes zero + cost-inclusive + temporal support + not concentrated + independent verification — tamamı önceden yazılmalıdır).

---

## 49. WHAT WOULD NOT COUNT AS SUPPORT?
Tek başına support değildir: MFE positive, mean positive, one profitable parameter, one profitable subgroup, one exceptional day, gross profit positive, one cost scenario, one implementation.

---

## 50. DO-NOT-INFER
Bu araştırmadan çıkarılamaz:

```
MFE > 0                → production profit
capture > 0            → strategy works
one exit family +      → optimal exit found
historical capture     → future capture guaranteed
statistical support    → execution feasibility proven
net historical support → locked OOS support
exit support           → selection support
capture ratio          → percentage of profit guaranteed
```

---

## 51. RESEARCH DEBT
Bu line için özellikle izlenecek debt: DEFINITION, DATA, PATH_RECONSTRUCTION, COST_MODEL, EXECUTION, STATISTICAL, PROVENANCE.

---

## 52. LOCK GATE
Bu preregistration ancak tamamı tamamlandıktan sonra LOCK edilebilir:

```
[ ] Research question final        [ ] First-touch ambiguity final (EXCLUDE, locked)
[ ] Population final               [ ] Missing-path policy final (NO IMPUTATION)
[ ] Dedup semantics final          [ ] Temporal split final (40/20/40 + min evidence)
[ ] Input SHA final                [ ] Concentration criteria final (>25% single day)
[ ] Price-cache manifest final     [ ] Opportunity-cost definition final
[ ] MFE definition reconciled      [ ] Multiple-comparison rule final (Holm)
[ ] Primary estimand final         [ ] Verdict engine final (9-gate, locked)
[ ] Cost model final (0.55/1.00)   [ ] Estimand audit PASS (section 52a)
[ ] Exit families final (E0-E3)    [ ] No unresolved ambiguity
[ ] Parameters final
```
Herhangi biri FAIL: `LOCK PROHIBITED`.

### 52a. ESTIMAND AUDIT (mandatory pre-lock gate, NS-1 lesson)
Before lock, a separate audit confirms ALL of: Population (exact input SHA,
exact n, dedup semantics incl. tie-handling, date range); Treatment (exit rule,
exact parameters, entry price, path window); Outcome (exact gross return
equation, exact cost equation, exact net return equation); Primary estimand
(exactly one mathematical definition; prose = formula = runner = report =
verdict); Secondary metrics (capture ratio, mean, MFE, MAE, tail, etc.);
Ambiguity (same-day target/stop, missing bars, invalid OHLC, corporate
actions); Temporal (exact split, minimum days, minimum observations);
Statistics (bootstrap, CI, multiple comparison, random seed); Verdict (math,
runner, report, verdict all measure the same quantity); Replication
(independent implementation computes the same estimand). All PASS required;
any FAIL -> `LOCK PROHIBITED` or `AMBIGUITY -> STOP -> USER REVIEW`.

---

## 53. RUNNER GATE
LOCK edilmeden `NO RUNNER / NO EXECUTION / NO RESULT`. LOCK sonrası `runner implementation → code review → dry run → execution` sırası.

---

## 54. INDEPENDENT VERIFICATION GATE
Execution tamamlandıktan sonra `independent implementation` çalıştırılmadan `final scientific closure` yapılmaz.

---

## 55. FINAL REPORT
Final report içerecektir: Executive Result, Protocol, Input, Population, MFE definition, Exit definitions, Primary result, Secondary results, Costs, Temporal results, Concentration, Opportunity cost, Failure analysis, Independent verification, Limitations, What We Know, What We Don't Know, What Is Not Supported, Do-Not-Infer, Production Impact, Final Verdict, Governance.

---

## 56. CURRENT STATUS

```
RX-CAPTURE-1
STATUS: PRE-FLIGHT COMPLETE
STATUS: READY FOR PREREGISTRATION REVIEW
LOCK: NO
RUNNER: NONE
EXECUTION: NONE
PRODUCTION IMPACT: NONE
H4: FROZEN
```

---

## 57. NEXT ALLOWED ACTION
Tek sonraki bilimsel action: `REVIEW / AMEND THIS DRAFT`. Kullanıcı onayı olmadan `LOCK / RUNNER / EXECUTION` yapılmayacaktır.
