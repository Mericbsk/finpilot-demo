# RESEARCH-X — MASTER RESEARCH ORCHESTRATOR v2

**Version:** v2.0
**Date:** 2026-09-22
**Status:** APPROVED — Meriç onayı: 2026-09-22 (Level B, research process authority)
**Layer:** Research / Governance
**Research Program:** FinPilot / FinSense Research-X
**Repository:** C:\Users\meric\Borsa
**Research Level:** A by default; Level B/C only after explicit gate approval

**Governance note:** This document is a research-process authority for future
Research-X lines. Its adoption does NOT, by itself, start any research line,
change any production behavior, reopen any frozen line, or alter any locked
historical record (per its own §10 and §62).

---

## 0. MASTER PURPOSE
Bu dokümanın amacı tek bir deney çalıştırmak değil, Research-X içindeki gelecekteki araştırmaların:

- bilimsel olarak tanımlanmasını,
- doğru estimand ile ölçülmesini,
- preregistration ile kilitlenmesini,
- deterministik olarak çalıştırılmasını,
- bağımsız olarak yeniden hesaplanmasını,
- veri/provenance sorunlarının ayrıştırılmasını,
- negatif sonuçların korunmasını,
- production'dan izole tutulmasını,
- governance kayıtlarının append-only tutulmasını
sağlayan **master araştırma orkestratörü** olmaktır.

Bu belge:

1. NS-1'i yeniden çalıştırmak için kullanılmayacaktır.
2. NS-1'in locked historical record'unu değiştirmeyecektir.
3. H4'ü yeniden açmayacaktır.
4. Yeni araştırma hatları için şablon/gate sistemi olarak kullanılacaktır.
5. Her yeni deneyin kendi preregistration'ını ve kendi verdict kriterlerini oluşturmasını zorunlu kılacaktır.

---

## 1. IMMUTABLE RESEARCH PRINCIPLES
Aşağıdaki ayrımlar korunacaktır:

```
UNKNOWN                    ≠ FALSE
NOT_SUPPORTED              ≠ DISPROVED
PROVENANCE_INSUFFICIENT    ≠ FAILURE
DESCRIPTIVE                ≠ PREDICTIVE
EXPLORATORY                ≠ CONFIRMATORY
COMPRESSION                ≠ PRODUCTION FAILURE
MFE                        ≠ REALIZED PROFIT
RATE REDUCTION             ≠ RECALL
NEGATIVE SCREEN            ≠ SHORT SIGNAL
POSITIVE SCREEN            ≠ BUY SIGNAL
INCOMPLETE RECONSTRUCTION  ≠ MODEL IS WRONG
NOT MEASURED               ≠ ZERO
```
Hiçbir sonuç, protokolün ölçmediği bir şeyi kanıtlamış gibi yorumlanmayacaktır.

---

## 2. CURRENT PROGRAM STATE

### 2.1 NS-1 STATUS
NS-1:

```
COMPLETED
LOCKED
WITH DOCUMENTED PROTOCOL DEVIATION
PRIMARY VERDICT: NO_SCREEN_SUPPORTED
PRODUCTION IMPACT: NONE
H4: UNTOUCHED
INDEPENDENT VERIFICATION: PENDING
```
NS-1 için:

- preregistration yeniden yazılmayacak,
- runner yeniden çalıştırılmayacak,
- sonuç yeniden optimize edilmeyecek,
- verdict değiştirmek amacıyla yeni analiz yapılmayacak,
- historical record silinmeyecek,
- geçmiş governance kayıtları overwrite edilmeyecek.

NS-1 için yapılabilecek ayrı çalışma:

```
INDEPENDENT RESULT VERIFICATION
```
Bu bir yeni deney değildir; amaç yalnızca mevcut sonucu bağımsız bir implementation path ile doğrulamaktır.

---

## 3. NS-1 HISTORICAL PROTOCOL DEVIATION
NS-1'de preregistration/metin seviyesinde primary estimand konusunda ambiguity bulunduğu kabul edilir.

Problem:

```
median(kept) - median(removed)
```
ile

```
median(remaining) - median(full)
```
aynı estimand değildir.

NS-1 execution sırasında ANS-1-consistent:

```
median(kept) - median(removed)
```
kullanılmıştır.

Bu karar result sonrasında geriye dönük olarak preregistration'a işlenmeyecek veya historical record değiştirilmeyecektir.

Historical record:

```
COMPLETED
WITH DOCUMENTED PROTOCOL DEVIATION
```
olarak korunacaktır.

Önerilen historical açıklama:

> Preregistration'da primary estimand wording ile ANS-1 replication contract arasında ambiguity vardı. Execution ANS-1-consistent kept-vs-removed estimandı kullandı. Bu deviation sonuç sonrasında geriye dönük olarak değiştirilmedi; historical record korunmuştur.

---

## 4. FUTURE RESEARCH RULE
Gelecekte hiçbir deney:

```
ambiguous estimand
        ↓
runner
        ↓
result
```
şeklinde ilerleyemez.

Zorunlu sıra:

```
RESEARCH QUESTION
        ↓
POPULATION
        ↓
TREATMENT / EXCLUSION DEFINITION
        ↓
ESTIMAND
        ↓
MATHEMATICAL DEFINITION
        ↓
SECONDARY METRICS
        ↓
VERDICT CRITERIA
        ↓
ESTIMAND AUDIT
        ↓
PREREGISTRATION LOCK
        ↓
RUNNER
        ↓
EXECUTION
        ↓
DETERMINISM
        ↓
INDEPENDENT VERIFICATION
        ↓
GOVERNANCE
```

---

## 5. ESTIMAND AUDIT — MANDATORY PRE-LOCK GATE
Bir deney LOCK edilmeden önce aşağıdaki kontrollerin tamamı PASS olmalıdır.

### Population
- Population explicitly defined.
- Inclusion criteria explicit.
- Exclusion criteria explicit.
- Deduplication rule explicit.
- Time period explicit.
- Data version explicit.
- Input SHA explicit.

### Treatment / Exclusion
- Treatment group explicitly defined.
- Excluded group explicitly defined.
- Kept/remaining population explicitly defined.
- Missing-data behavior explicit.

### Primary estimand
- Primary outcome explicitly named.
- Primary estimand has exactly one mathematical definition.
- Mathematical formula appears in preregistration.
- Prose definition maps exactly to formula.
- Runner maps exactly to formula.
- Verdict engine maps exactly to formula.
- Report maps exactly to formula.
- Replication claim uses same estimand.

### Comparison
- Comparison population explicitly defined.
- Matched/random comparator definition explicit.
- Null comparator definition explicit.
- Temporal comparator definition explicit.

### Decision
- Success threshold explicit.
- Failure threshold explicit.
- Required gates explicit.
- Missing evidence behavior explicit.

**Mandatory rule:** Herhangi biri FAIL ise:

```
LOCK PROHIBITED
```
veya:

```
AMBIGUITY → STOP → USER REVIEW
```
Unilateral interpretation yasaktır.

---

## 6. PROTOCOL DEVIATION RULE
Bir ambiguity execution başlamadan önce fark edilirse:

```
STOP
DO NOT RUN
DO NOT RESOLVE SILENTLY
DO NOT WRITE RESULT
```
Kullanıcı/onay gereken noktalar açıkça raporlanır.

Bir deviation execution sırasında fark edilirse:

```
STOP IF POSSIBLE
PRESERVE EXISTING ARTIFACTS
RECORD DEVIATION
DO NOT HIDE IT
```
Result sonrasında deviation fark edilirse:

```
DO NOT RETROACTIVELY EDIT PREREGISTRATION
DO NOT DELETE RESULT
DO NOT REWRITE HISTORY
```
Bunun yerine `DOCUMENTED PROTOCOL DEVIATION` olarak append-only governance kaydı oluşturulur.

---

## 7. RESEARCH LEVELS

### LEVEL A — READ-ONLY / HISTORICAL / ANALYTICAL
Amaç: mevcut veriyi analiz etmek, historical evidence değerlendirmek, mevcut runner sonuçlarını doğrulamak, yeni production davranışı oluşturmamak. Default seviyedir. Production impact: `NONE`.

### LEVEL B — INSTRUMENTATION / PROVENANCE
Amaç: future data persistence, production tuple logging, provenance, feature snapshots, execution metadata, data quality. Level B'de `signal improvement ≠ automatically assumed`. Instrumentation'ın başarısı veri kalitesidir; predictive edge değildir.

### LEVEL C — LOCKED OOS / CANDIDATE VALIDATION
Yalnızca önceki seviyeler gerekli şartları sağladığında. Burada locked OOS, candidate validation, shadow/paper/live transition gündeme gelebilir. Level C otomatik açılmaz.

---

## 8. H4 FREEZE
H4 tamamen frozen/closed'dur. Aşağıdaki zincir yeniden açılmayacaktır:

```
H4A → CLOSED / COMPRESSION_SUPPORTED
H4B → CLOSED / MAPPING_DEPENDS_ON_ADDITIONAL_INPUTS
H4C → CLOSED / INFORMATION_LOSS_NOT_SUPPORTED
H4D-definition → CLOSED / DEFINITION_LOCKED
H4D-measure → CLOSED / PROVENANCE_INSUFFICIENT
```
Özellikle: H4C negative result "information loss yok" anlamına gelmez; yalnızca test edilen specific mechanism desteklenmemiştir. Ayrıca score compression ile production ranking failure aynı şey değildir.

H4 için yeni experiment açılması yasaktır. Production provenance ihtiyacı varsa bu `NEW LEVEL-B RESEARCH LINE` olarak tanımlanmalıdır.

---

## 9. NEW RESEARCH LINE CREATION
Yeni bir araştırma hattı başlamadan önce oluşturulacaktır:

```
Research ID
Research Question
Why now?
Known evidence
Unknowns
Dependencies
Input data
Population
Primary estimand
Secondary metrics
Null model
Comparator
Temporal validation
Failure criteria
Verdict criteria
Production impact
Governance requirements
```
Örnek ID'ler: `RX-NS-1`, `RX-CAPTURE-1`, `RX-REDUNDANCY-1`, `RX-FEATURE-ORTHOGONALITY-1`, `RX-PROVENANCE-1`. Research ID benzersiz olmalıdır.

---

## 10. NO AUTOMATIC EXPERIMENT CASCADE
Bir deney PASS veya FAIL olduğunda sonraki deney otomatik başlamaz. Örneğin `NS-1 FAIL`, "Phase 2 automatically starts" anlamına gelmez; `ANS-1 positive`, "buy signal" anlamına gelmez; `MFE positive`, "exit strategy validated" anlamına gelmez. Her yeni research line ayrı preregistration ister.

---

## 11. PRIMARY / SECONDARY / EXPLORATORY SEPARATION
Her deneyde metrikler üç sınıfa ayrılacaktır:

- **Primary:** Önceden kilitlenmiş ana estimand.
- **Secondary:** Destekleyici ölçümler.
- **Exploratory:** Hipotez üretmek için kullanılan ölçümler.

Exploratory sonuçlar `SUPPORTED PRIMARY RESULT` olarak raporlanamaz.

---

## 12. NEGATIVE-SCREEN RESEARCH TEMPLATE
NS-1 benzeri gelecekteki negative-screen araştırmalarında minimum ayrım:

```
screening value ≠ buy signal ≠ short signal
```
Örneğin `big-loser rate reduction` ile `loser recall` ayrı raporlanacaktır.

---

## 13. LOSER RECALL DEFINITION
Eğer "loser capture" araştırılıyorsa, `big_loser := c2c_5d <= -10%` gibi eşik preregistration'da kilitlenmelidir. Sonra:

```
loser_recall = true_big_losers_excluded / all_true_big_losers
```
Bu, `loser rate reduction` ile aynı değildir. Örneğin big-loser rate'in 22.2% → 3.5% gözlenmesi ~84% relative reduction anlamına gelebilir; ama tek başına 84% loser recall kanıtı değildir.

---

## 14. VERDICT ENGINE
Verdict kriterleri araştırma-spesifik olacaktır. Master orchestrator herhangi bir araştırmaya otomatik olarak `SCREEN_SUPPORTED` veya `FAIL` kriteri dayatmayacaktır. Her preregistration şunları açıkça tanımlamalıdır:

```
PRIMARY PASS / PRIMARY FAIL / SECONDARY PASS / SECONDARY FAIL /
TEMPORAL PASS / TEMPORAL FAIL / INSUFFICIENT DATA / INPUT MISMATCH /
PROTOCOL DEVIATION
```
NS-1 gibi bir screening experiment için, eğer preregistration gerektiriyorsa şunlar birlikte gate olabilir: median improvement + statistical confidence + matched-random comparison + null-shuffle comparison + temporal replication + big-loser non-degradation. Ancak bu gate başka research line'lara otomatik taşınamaz.

---

## 15. OPPORTUNITY COST
Bir exclusion/screening araştırmasında yalnızca "what was removed?" ölçülmeyecektir; ayrıca "what was lost?" ölçülmelidir. Gerekiyorsa preregister edilecektir: top-5% opportunity cost, top-decile opportunity cost, positive-tail preservation, mean, median, tail EV. Screening başarısı `loser reduction` ile sınırlı değildir.

---

## 16. MATCHED RANDOM CONTROL
Screening research'te mümkün olduğunda `R ≥ predefined` matched-random control kullanılacaktır. Random comparator aynı scan_date yapısını, aynı population constraints'i ve aynı exclusion budget'i mümkün olduğunca korumalıdır. Seed preregistration'da kilitlenmelidir.

---

## 17. NULL-SHUFFLE
Feature-based screening araştırmalarında null model açıkça tanımlanmalıdır. Örneğin `within-scan_date permutation` kullanılıyorsa scan_date, population ve sample size korunmalı; feature distribution mümkün olduğunca korunmalı. Permutation yöntemi execution sonrasında değiştirilmemelidir.

---

## 18. BLOCK BOOTSTRAP
Financial time-series yapısında observation-level IID varsayımı otomatik kabul edilmeyecektir. Preregistration'da `block unit`, `B`, `seed`, `CI level`, `two-sided / one-sided` tanımlanmalıdır. Day-clustered veya uygun zaman blokları tercih edilir.

---

## 19. MULTIPLE COMPARISON
Bir primary family birden fazla rule içeriyorsa `family definition` önceden yapılmalıdır. Örneğin `{A, B3, C, UNION}` tek family ise adjustment yöntemi (Bonferroni / Holm / FDR) preregistration'da `before execution` seçilmelidir.

---

## 20. TEMPORAL VALIDATION
Bir discovery result için zaman içinde tekrarlanabilirlik ayrı gate'tir. Örneğin `early 50% / middle 20% buffer / late 30%` gibi bölme önceden kilitlenebilir. Temporal validation `same sign + predefined minimum evidence` gerektiriyorsa bu önceden yazılmalıdır. Post-hoc window selection yasaktır.

---

## 21. INPUT INTEGRITY
Her deney için kaydedilecektir: absolute input path, file SHA-256, row count, column list, date range, dedup rule, expected n, actual n, n tolerance. Örneğin `|Δn| > 1% → INPUT_MISMATCH` gibi sınır ancak preregistration'da tanımlanmışsa uygulanır. Input mismatch `experiment failure` değil, `execution validity problem` olarak raporlanır.

---

## 22. DATA VERSION FREEZE
Bir araştırma çalıştırılırken kullanılan input dataset `SHA-256 LOCKED` olmalıdır. Dataset değişirse `NEW INPUT VERSION` olarak kaydedilir. Eski result yeni dataset ile sessizce overwrite edilemez.

---

## 23. MISSING DATA
Missing data policy önceden tanımlanacaktır. Örneğin: `required field missing → do not impute → do not silently exclude → follow preregistered rule`. Missingness `random / systematic / date-dependent / symbol-dependent / regime-dependent` olabilir; mümkün olduğunda missingness distribution ayrıca raporlanır.

---

## 24. PIT / LEAKAGE AUDIT
Her historical research line için "Was feature known at scan time?" sorusu zorunludur. Gerekirse incelenir: timestamp, publication timestamp, market availability, look-ahead window, data revision, survivorship, future OHLCV contamination. PIT güvence altına alınmamış feature `predictive evidence` olarak sunulamaz.

---

## 25. RUNNER DEVELOPMENT RULE
Runner `AFTER PREREGISTRATION LOCK` geliştirilecektir. Amaç runner'ın protocol'e uyması, hidden optimization içermemesi, verdict'ü değiştirmek için tasarlanmamasıdır. Runner yazarken `hangi sonuç çıkarsa çıksın` aynı implementation kullanılmalıdır.

---

## 26. RUNNER CODE REVIEW
Runner execution öncesi ayrı review yapılmalıdır. `Reviewer ≠ Runner author` olması tercih edilir. Kontrol: estimand formula, population, dedup, random seed, bootstrap, permutation, CI, multiple comparison, temporal split, missing policy, verdict logic, artifact writing.

---

## 27. STATIC / DRY RUN
Real execution'dan önce `dry run` yapılmalıdır. Kontrol: paths, columns, types, n, date range, seed, artifact directory, schema. Dry run `NO RESULT INTERPRETATION` içermemelidir.

---

## 28. REAL EXECUTION
Execution sırasında yasaktır: `NO PARAMETER OPTIMIZATION`, `NO THRESHOLD SEARCH`, `NO POST-HOC RULE CHANGE`, `NO DATASET SWAP`, `NO SILENT EXCLUSION`. Runner `single declared protocol` uygulamalıdır.

---

## 29. DETERMINISM
Her experiment mümkün olduğunca iki kez çalıştırılmalıdır. Karşılaştırılacak: JSON SHA, report SHA, primary metrics, secondary metrics, verdict, sample counts, randomization summaries. Tam deterministic değilse `EXPECTED_NONDETERMINISM` açıkça belgelenmelidir.

---

## 30. INDEPENDENT RESULT VERIFICATION
Bu master orchestrator'un zorunlu kalite katmanıdır. Independent verification `same data + same locked protocol + different implementation path` kullanmalıdır; mümkünse different code, different calculation path, different data loading logic tercih edilir. Runner'ın JSON çıktısını okuyup aynısını tekrar yazmak `INDEPENDENT VERIFICATION` sayılmaz.

---

## 31. INDEPENDENT VERIFICATION CHECKLIST
Minimum karşılaştırma: Population n, Excluded n, Kept n, Primary metric, Primary delta, 95% CI, Adjusted CI, Matched-random result, Null-shuffle result, Big-loser rate, Big-loser delta, Loser recall, Opportunity cost, Early effect, Late effect, Final verdict inputs. Sonuç `VERIFICATION_PASS / VERIFICATION_DISCREPANCY / VERIFICATION_INCONCLUSIVE` olabilir.

---

## 32. INDEPENDENT VERIFICATION DISCREPANCY
Fark varsa: `DO NOT AVERAGE`, `DO NOT PICK THE FAVORITE`, `DO NOT EDIT ONE RESULT UNTIL MATCHES`. Bunun yerine `DISCREPANCY INVESTIGATION` açılır. Olası nedenler ayrıştırılır: dedup, missing policy, seed, bootstrap, formula, floating point, population, date split, implementation bug.

---

## 33. THREE-LAYER VALIDATION
Her ciddi research line için üç ayrı katman raporlanmalıdır:

- **Layer 1 — Mathematical:** Formula doğru mu?
- **Layer 2 — Computational:** Runner formula'yı doğru uyguluyor mu?
- **Layer 3 — Scientific:** Sonuç gerçekten hypothesis'i test ediyor mu?

Örneğin `Layer 1 PASS / Layer 2 PASS / Layer 3 NOT_SUPPORTED` tamamen geçerli bir sonuçtur.

---

## 34. STATISTICAL SANITY CHECK
Her experiment sonunda kontrol edilir: sample sizes, missingness, distribution, outliers, bootstrap stability, randomization stability, temporal concentration, day clustering, symbol clustering, tail concentration. Özellikle `positive mean + negative median` gibi durumlar ayrıca açıklanmalıdır; bunlar otomatik olarak contradiction değildir.

---

## 35. TAIL CONCENTRATION
Bir sonuç `mean positive` olsa bile `median negative` ise tail concentration araştırılmalıdır. Ayrıca gerekirse raporlanır: number of days driving result, number of symbols driving result, top 1%, top 5%, top 10%.

---

## 36. NO-OPTIMIZATION RULE
Discovery sonucu görüldüğünde otomatik yapılamaz: threshold tweak, combination search, parameter grid, best-window selection, best-subgroup selection. Yeni optimization araştırması `NEW PREREGISTERED RESEARCH LINE` olmalıdır.

---

## 37. FAILURE PHENOTYPE
Bir rule başarısız olduğunda araştırma burada bitmek zorunda değildir. Ancak failure phenotype `EXPLANATORY / HYPOTHESIS GENERATION` olarak sınıflandırılır. Örneğin high ATR, high lottery, low price, far from 52w high gibi özellikler gözlenebilir; bunlar `causal mechanism` olarak ilan edilmez.

---

## 38. REDUNDANCY RESEARCH
Örneğin `composite_score ≈ dist_52w_high` gibi bir ilişki `SUSPECT` olarak kalabilir. Correlation tek başına `causal redundancy` kanıtı değildir. İleri test için önceden tanımlanmış yöntemlerden biri kullanılabilir: incremental IC, partial association, mutual information, ablation, orthogonal residual signal.

---

## 39. FEATURE VALUE
Bir feature'ın `behaviorally active` olması `predictive` olduğu anlamına gelmez. Ayrım ayrı raporlanır: score delta, rank delta, coverage, prediction, economic value.

---

## 40. FLAGS
Feature flags için minimum state: `NOT_TESTED / DATA_INACTIVE / BEHAVIORALLY_ACTIVE / PREDICTIVE_TESTED / PREDICTIVE_SUPPORTED / PREDICTIVE_NOT_SUPPORTED / SHUTDOWN_CANDIDATE`. Bir flag'in rank'ı değiştirmesi `predictive evidence` değildir.

---

## 41. ECONOMIC VALIDATION
Statistical significance tek başına production viability değildir. Gerektiğinde incelenmelidir: transaction costs, slippage, spread, turnover, capacity, ADV, execution delay, borrow, fees. Bir edge `gross` olarak görünüyorsa `net` olarak da test edilmelidir.

---

## 42. OOS GOVERNANCE
Locked OOS `DO NOT OPEN` — unless: preregistration locked, training/discovery fully separated, validation criteria locked, data boundary frozen, governance approval exists. OOS açıldıktan sonra `DO NOT TOUCH` kuralı geçerlidir.

---

## 43. PRODUCTION IMPACT GATE
Her experiment sonunda açıkça `PRODUCTION_IMPACT = NONE` veya izin verilen başka değer yazılmalıdır. Level A default `NONE`. Production değişikliği için ayrıca `shadow → paper → validation → governance approval → production` gibi ayrı süreç gerekir.

---

## 44. ARTIFACT INTEGRITY
Her research line mümkün olduğunca üretmelidir: preregistration, runner, result JSON, report MD, logs, input SHA, output SHA, governance entry. SHA değerleri birbirleriyle ilişkilendirilmelidir.

---

## 45. REPORT STRUCTURE
Her final report minimum içermelidir:

```
1. Executive Result        9. Random Controls       17. What We Know
2. Research Question      10. Null Model            18. What We Don't Know
3. Locked Protocol        11. Temporal Validation   19. What Is Not Supported
4. Input Integrity        12. Opportunity Cost      20. Do-Not-Infer
5. Population             13. Failure Analysis      21. Production Impact
6. Primary Estimand       14. Independent Verif.    22. Final Verdict
7. Primary Result         15. Statistical Sanity    23. Governance Record
8. Secondary Results      16. Limitations
```

---

## 46. WHAT WE KNOW / DON'T KNOW
Her sonuç iki ayrı bölümde raporlanmalıdır: WHAT WE KNOW (yalnızca doğrudan evidence ile desteklenenler) ve WHAT WE DON'T KNOW (evidence bulunmayan ama karar açısından önemli olanlar). Bu iki bölüm birleştirilmeyecektir.

---

## 47. DO-NOT-INFER
Her experiment sonunda en az birkaç açık non-inference yazılmalıdır. Örnek:

```
Observed screening effect ≠ future predictive signal
Big-loser rate reduction ≠ loser recall
Positive MFE ≠ realizable profit
Feature activity ≠ predictive value
Historical correlation ≠ causal mechanism
Descriptive temporal stability ≠ locked OOS validation
Statistical improvement ≠ economic profitability
```

---

## 48. RESEARCH DEBT
Her experiment sonunda açık debt listesi tutulmalıdır. Kategoriler: PROVENANCE, RECONSTRUCTION, DATA, STATISTICAL, VALIDATION, DEFINITION, GOVERNANCE. Debt yeni experiment'larla gizlenmemelidir.

---

## 49. GOVERNANCE
Research governance `APPEND-ONLY` olmalıdır. Eski decision log kayıtları `overwrite / delete / rewrite` edilmez. Bir hata veya yeni bilgi varsa `NEW RECORD` eklenir.

---

## 50. DECISION LOG ENTRY
Her önemli research line sonunda kaydedilmelidir: research_id, date, status, verdict, protocol_version, input_sha, result_sha, report_sha, production_impact, verification_status, deviation_status, next_allowed_action.

---

## 51. NS-1 RETROSPECTIVE AUDIT
NS-1 için bundan sonraki master-level action: `NOT RERUN / NOT AMENDED / NOT RE-OPTIMIZED`. Yalnızca `INDEPENDENT RESULT VERIFICATION` yapılabilir.

Kontrol listesi:

```
[PASS] preregistration locked
[PASS] runner after lock
[PASS] input SHA recorded
[PASS] determinism checked
[PASS] artifact hashes
[PASS] production impact NONE
[PASS] H4 untouched
[PASS] append-only governance
[FAIL/PENDING] independent recalculation
[DOCUMENTED] estimand ambiguity/protocol deviation
```
Bu retrospective audit, NS-1 sonucunu değiştirmek amacı taşımaz.

---

## 52. FUTURE PHASE TEMPLATE — CAPTURE / EXIT
NS-1 sonrasında capture/exit araştırması yapılacaksa yeni Research ID oluşturulmalıdır (örn. `RX-CAPTURE-1`). Research question:

> Existing selected universe içinde gözlenen MFE'nin hangi kısmı önceden tanımlanmış, cost-inclusive, path-aware exit rules ile gerçekten capture edilebilir?

Bu `NEW RESEARCH` olacaktır; NS-1'in continuation sonucu olarak otomatik başlatılamaz.

---

## 53. CAPTURE / EXIT SAFETY
Selection fixed tutulmalıdır; aksi halde `selection effect + exit effect` birbirine karışır. Bu nedenle `selection LOCKED / exit variable` olmalıdır.

---

## 54. FUTURE PHASE — FEATURE ORTHOGONALITY
Yeni feature araştırmasında önce `existing feature map` çıkarılmalıdır. Sonra kullanılabilir: correlation, mutual information, incremental IC, conditional effect, ablation. Amaç `new information` olup olmadığını araştırmaktır. Yeni feature eklemek default değildir.

---

## 55. FUTURE PHASE — PROVENANCE
Historical production provenance eksikse `Level B` research line açılabilir. Örneğin future persistence'a alınabilir: production sort tuple, ranking_score, legacy_quality_score, tie-break, input order, timestamp, feature snapshot. Ama bu `H4 reopening` değildir.

---

## 56. B2 / DATA ACCUMULATION
B2 gibi instrumentation çalışmalarında başarı kriteri `data diversity / coverage / completeness / persistence` olmalıdır. B2'nin `2 days / 8 symbols` gibi düşük diversity ile B3'e geçmesi otomatik kabul edilmez. Exit criteria preregistered olmalıdır.

---

## 57. INDEPENDENT AGENT ROLES
Mümkün olduğunda roller ayrılmalıdır:

- **Agent A — Research Designer:** Question + hypothesis + estimand.
- **Agent B — Protocol Auditor:** Preregistration consistency.
- **Agent C — Runner Engineer:** Implementation.
- **Agent D — Code Reviewer:** Runner audit.
- **Agent E — Independent Verifier:** Different implementation.
- **Agent F — Scientific Reviewer:** Interpretation and inference boundaries.
- **Agent G — Governance Auditor:** Hashes, locks, decision log.

Aynı agent mümkün olduğunca bütün rollerin bağımsızlığını simüle etmemelidir.

---

## 58. FINAL SCOREBOARD
Her experiment sonunda (overall score üretmek için kullanılmaz):

| Dimension | Status |
|---|---|
| Protocol integrity | PASS / FAIL |
| Input integrity | PASS / FAIL |
| Estimand integrity | PASS / FAIL |
| Computational integrity | PASS / FAIL |
| Statistical evidence | PASS / FAIL |
| Temporal evidence | PASS / FAIL |
| Economic evidence | PASS / FAIL / N/A |
| Independent verification | PASS / PENDING / FAIL |
| Production impact | NONE / OTHER |
| Governance | PASS / FAIL |

---

## 59. NO OVERALL WINNER
Research-X `BEST RULE / BEST MODEL / BEST FEATURE / BEST STRATEGY / WINNER` şeklinde genel ranking üretmez. Farklı hypotheses farklı evidence gerektirir. Örneğin `screening supported` ile `economic edge supported` aynı şey değildir.

---

## 60. FINAL SCIENTIFIC STATE
Her research line sonunda yalnızca uygun state kullanılmalıdır:

```
SUPPORTED / NOT_SUPPORTED / MEASURED_DESCRIPTIVE /
PROVENANCE_INSUFFICIENT / NOT_RECONSTRUCTED / PROVISIONAL /
INCONCLUSIVE / EXPLORATORY / COMPLETED / LOCKED / FROZEN / CLOSED /
WITH_DOCUMENTED_PROTOCOL_DEVIATION
```
Birden fazla state gerekiyorsa hiyerarşik olarak raporlanabilir. Örneğin: `COMPLETED / WITH DOCUMENTED PROTOCOL DEVIATION / PRIMARY VERDICT: NO_SCREEN_SUPPORTED / INDEPENDENT VERIFICATION: PENDING`.

---

## 61. CURRENT RESEARCH-X STATE
Bu orchestrator uygulandığında mevcut state:

```
H4                    FROZEN / CLOSED
Direction prediction  CLOSED / NOT_SUPPORTED
NS-1                  COMPLETED / LOCKED
                      WITH DOCUMENTED PROTOCOL DEVIATION
                      PRIMARY VERDICT: NO_SCREEN_SUPPORTED
                      INDEPENDENT VERIFICATION: PENDING
                      PRODUCTION IMPACT: NONE
Next research         NOT AUTOMATICALLY STARTED
```

---

## 62. DO NOT START PHASE 2 AUTOMATICALLY
Bu master orchestrator'un sonunda `DO NOT AUTO-START NEXT EXPERIMENT` kuralı vardır. Önce: (1) NS-1 independent verification tamamlanır, (2) verification sonucu governance'a append edilir, (3) NS-1 final scientific state güncellenir, (4) yeni research question ayrı tanımlanır, (5) yeni preregistration hazırlanır, (6) estimand audit yapılır, (7) kullanıcı onayı alınır, (8) lock edilir, (9) ancak bundan sonra runner oluşturulur.

---

## 63. MASTER COMPLETION CHECKLIST
Bir yeni research line "complete" sayılmadan önce:

```
[ ] Research ID created                [ ] PIT rule defined
[ ] Research question explicit         [ ] Multiple-comparison rule defined
[ ] Hypothesis explicit                [ ] Verdict criteria defined
[ ] Population explicit                [ ] Estimand audit PASS
[ ] Treatment/exclusion explicit       [ ] Preregistration LOCKED
[ ] Primary outcome explicit           [ ] Input SHA frozen
[ ] Primary estimand math defined      [ ] Runner created after lock
[ ] Secondary metrics defined          [ ] Code review completed
[ ] Comparator defined                 [ ] Dry run completed
[ ] Null defined                       [ ] Real execution completed
[ ] Temporal validation defined        [ ] Determinism checked
[ ] Missing-data rule defined          [ ] Independent recalculation completed
```
(continued: statistical sanity checked, artifacts hashed, production impact verified, governance entry appended, What We Know / Don't Know / Do-Not-Infer written, research debt recorded, final state assigned.)

Eksik maddeler varsa `COMPLETED` iddiası yapılmamalıdır.

---

## 64. FIRST ACTION FOR ANY FUTURE RESEARCH
Her yeni research line için ilk işlem `READ-ONLY PREFLIGHT` olacaktır. Preflight çıktısı: (1) existing evidence, (2) existing related experiments, (3) frozen/closed dependencies, (4) input availability, (5) provenance, (6) population, (7) potential leakage, (8) existing contradictions, (9) estimand feasibility, (10) production impact.

Preflight tamamlanmadan: `NO PREREGISTRATION LOCK / NO RUNNER / NO RESULT / NO PRODUCTION CHANGE`.

---

## 65. FINAL GOVERNANCE PRINCIPLE
Research-X'in amacı `sonuç üretmek` değil, `güvenilir bilgi üretmek`tir. Bu nedenle `negative result` başarısız araştırma değildir. Özellikle `NOT_SUPPORTED / NO_EDGE / PROVENANCE_INSUFFICIENT / NOT_RECONSTRUCTED / INCONCLUSIVE` bilimsel olarak geçerli çıktılardır. Sistem hiçbir koşulda sonucu "başarılı" göstermek için protocol, metric, population veya verdict değiştiremez.

---

## 66. MASTER CLOSING STATEMENT
Research-X'in temel çalışma sırası:

```
QUESTION → POPULATION → ESTIMAND → AUDIT → LOCK → RUN → REPRODUCE
→ VERIFY INDEPENDENTLY → INTERPRET → GOVERN
```
Ve temel karar ilkesi:

> **Önce ölçümün doğru olduğunu kanıtla; sonra sonucu yorumla; en son production etkisini düşün.**

H4 frozen kalır. NS-1 historical record korunur. NS-1 yeniden çalıştırılmaz. NS-1 için yalnızca bağımsız sonuç doğrulaması yapılabilir. Yeni research line'lar ayrı preregistration ve ayrı governance zinciriyle başlar.

**Production'a hiçbir değişiklik, yalnızca bu master orchestrator'ın varlığı nedeniyle yapılmaz.**
