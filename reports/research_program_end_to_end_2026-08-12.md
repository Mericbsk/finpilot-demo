# FinPilot Research Program End-to-End Run

## Scope and boundary

This is a Level A research-only execution record for the current FinPilot
workspace. The run used the available full-universe export, price cache and
sector artifacts. It did not modify scanner, score, ranking, entry/exit, risk,
portfolio, publication, broker, paper/live or locked-OOS behavior.

The available export contains `100,496` raw rows, about `1,970` symbols and
roughly 81 scan dates. Results below are traceable to the dated artifacts
listed in each section. The standard diagnostic cost assumption was `0.55%`
where the runner supported costs. Close-to-close five-day labels overlap and
are not executable portfolio P&L.

## Execution status

### Completed with current data

- Data readiness and price-cache integrity audits.
- Scanner battery v2 and candidate pipeline.
- 1,000-permutation negative control.
- Budget battery for single strategies and combinations with `$10,000`.
- Decision context, similar-case and abstention diagnostics.
- Production-candidate validation, including ATR-parity and random controls.
- Stability, concentration and capacity diagnostics.
- Decision-quality and honest-score calibration experiments.
- Barrier TP/SL and holding-path grid.
- Timing drift, score replay, pre-rise path, winner anatomy and daily pre-rise hypothesis batteries.
- Strategic laboratory and ten-perspectives laboratory.
- High-RVOL deep audit and full-universe expanding-threshold audit.
- Alpha v2 and phase 1-7 root research runners.
- Root full-universe backtest.

### Partial or diagnostic-only

- Strategic lab: 17 experiments completed, 1 invalidation-exit experiment partial.
- Pre-rise path: only 237 resolved rows across 16 dates; not generalizable to the full universe.
- Score replay: replay artifact generated, but source fields do not provide complete persisted component provenance.
- Barrier grid: 378 viable configurations were enumerated; top configurations are selection-sensitive and are not confirmatory evidence.
- Alpha v2 / phase 1-7: outputs contain extreme means and `-100%` drawdown in places, indicating unresolved price/outcome integrity and overlap effects.

### Blocked by prerequisites

- P1 data reliability: BLOCKED. There is no immutable prior cache snapshot, point-in-time universe/delisting record or corporate-action reconciliation.
- P2 label and execution: BLOCKED. Observed spread, slippage, impact, ADV, fill ordering and intraday execution inputs are unavailable.
- P3-P8 gated phases: NOT OPENED because prerequisites are not passed.
- P9 robustness and locked validation: BLOCKED; locked OOS remains NOT OPENED.
- SEC companyfacts and adjusted-cache backfill: not run because external credentials and timestamped source data are unavailable.

## Main findings

### 1. `entry_ok` is not validated as a return selector

The root backtest measured `entry_ok=True` at `42.5%` hit rate and lift `1.021`
versus the full-universe base hit rate of `41.6%`. This is a weak descriptive
difference, not evidence for production promotion.

Source: `data/backtest_out/backtest_full_universe_2026-08-12-e2e.json`.

### 2. Eligible candidates remain weak after risk construction

In production-candidate validation, eligible equal-weight median daily return
was `-0.602%`, while ATR-parity improved it to `-0.313%`. Max drawdown improved
from `-65.26%` to `-51.70%` and daily Sharpe from `0.060` to `0.116`. This
supports ATR-parity as a risk-construction research candidate, not as a proven
alpha rule.

Source: `data/backtest_out/production_candidate_validation_2026-08-12-e2e.json`.

### 3. Abstention is more promising than score promotion, but remains exploratory

The calibration-frozen abstention diagnostic produced a validation abstain rate
of `21.6%`. Active validation rows had median `c2c_5d` of `-0.047%`, compared
with `-3.185%` for abstained rows. This supports investigating evidence-quality
gating, but it is not yet a trading or publication rule.

Source: `data/backtest_out/production_candidate_validation_2026-08-12-e2e.json`.

### 4. High RVOL is an outlier/data-quality context signal, not a positive selector

The expanding all-universe run learned q90 only from prior dates. High-RVOL
eligible ended the diagnostic `$10,000` scenario at `$9,160`, while the
high-RVOL all and rejected cohorts produced implausible `$73.0M` and `$106.5M`
paths. Their row medians were `0.000%`, while means were dominated by extreme
observations. High RVOL is therefore rejected as a return promise.

Source: `reports/high_rvol_full_universe_2026-08-12.md` and its JSON artifact.

### 5. Score, gap, ATR and barrier winners are not yet trustworthy production candidates

Several full-universe runners report large positive means or p-values for gap,
ATR, RVOL and barrier combinations. The same run also reports `-100%` drawdown
and extreme close-to-close outcomes, while the price-cache audit found 485 of
2,047 symbols with a median largest absolute close jump of `173.57513%` above
the `50%` flag threshold. These results require price provenance, corporate
action classification, non-overlapping labels and execution costs before they
can support a product rule.

Sources: `data/backtest_out/price_cache_integrity_audit_2026-08-12-e2e.json`,
`data/backtest_out/full_universe_barrier_backtest_2026-08-12-e2e/`,
`data/backtest_out/alpha_v2_2026-08-12-e2e/`, and the root backtest artifact.

## Opportunity ranking

1. **Evidence-quality veto/abstention:** highest near-term research value; it reduces false confidence without claiming return prediction.
2. **ATR-parity sizing:** promising for drawdown control, but requires clean prices and observed execution before any proposal.
3. **Rejected-row taxonomy:** split stale prices, corporate actions, illiquidity, news gaps and genuine momentum rather than treating rejection as one class.
4. **Matched, non-overlapping conditional studies:** test gap/RVOL/ATR only after data repair and against same-date controls.
5. **Execution and capacity layer:** add spread, slippage, ADV, fill ordering and turnover before any `$10,000` scenario is interpreted economically.

## Final status

The current-data portion of the research program has been run end to end as far
as the available evidence permits. The evidence does not justify a production
selector, expected-return promise or live/paper rollout. The honest completion
state is:

## Validation record

- Alpha v2 focused regression plus all dated research tests: `47 passed`.
- All 18 dated `-e2e` JSON artifacts parsed successfully.
- Workspace diagnostics for changed files: no errors.
- The full repository suite has four unrelated failures: Prometheus port-in-use
	edge case, scheduler watchdog timing, and two scanner-rollout runtime-baseline
	expectations. They were not changed because they are outside this research
	task's ownership boundary.

- P0: COMPLETED
- P1/P2: BLOCKED
- P3-P8: NOT OPENED behind prerequisites
- P9 / locked OOS: BLOCKED / NOT OPENED
- Production change: `false`

This report is a research finding, not a production approval.# FinPilot Research Program: Uçtan Uca Durum ve Sonuç

Tarih: 2026-08-12
Katman: Research / Engineering
Seviye: Level A research-only
Production değişikliği: Yok

## Yönetici özeti

Mevcut veriyle teknik olarak çalıştırılabilir araştırma bataryası uçtan uca tamamlandı, son focused regression suite `44/44` geçti ve tüm sonuçlar tek bir program durumu içinde toplandı. Bu, 220 planlı testin 220'sinin koşulduğu anlamına gelmez. Gated programın kuralı gereği veri ve execution önkoşulları geçilmediği için sonraki fazlar açılmadı.

En güvenilir sonuç şudur: mevcut `finpilot_score` ve `entry_ok` ileriye dönük, maliyet sonrası ve benchmark'a göre doğrulanmış bir edge göstermedi. TP/SL, exit ve target aramalarında robust production adayı çıkmadı. Üretime en yakın fikirler yön tahmini değil; ATR-parity risk konstrüksiyonu, veri kalitesi veto/uyarı katmanı ve evidence-quality/abstention katmanıdır. Bunların hiçbiri henüz canlı kural değildir.

## Program sırası

| Sıra | Program adımı | Durum | Sonuç |
|---:|---|---|---|
| 1 | Veri kimliği, canonical symbol-day deduplication, label/outcome ayrımı | TAMAMLANDI | `c2c_1d`, `c2c_5d`, `mae_t5` eklendi; MFE ile close-to-close ayrıştırıldı. |
| 2 | Feature lineage ve leakage preflight | TAMAMLANDI / SINIRLI | Forward outcome alanları feature olarak reddediliyor; strict production-score replay tam kapanmadı. |
| 3 | Null kontrolleri ve matched controls | TAMAMLANDI | `entry_ok` null ailelerinden pozitif ayrışmadı. |
| 4 | Score/ranking anlamı ve calibration | TAMAMLANDI | Score geçmiş extension'ı taşıyor; forward association yaklaşık sıfır, Brier skill negatif. |
| 5 | Entry/selection ve rejection quality | TAMAMLANDI | Eligible grup random/rejected karşılaştırmalarını geçmedi. |
| 6 | Timing, drift ve signal half-life | TAMAMLANDI / DIAGNOSTIC | Ham ortalamalar outlier-dominant; next-open ve trimmed sonuçlar zayıf. |
| 7 | TP/SL, exit ve target matrisleri | TAMAMLANDI / PROMOTION YOK | 3.120 fixed-target konfigürasyonu; global reality check anlamlı değil. |
| 8 | Portfolio, risk, sizing ve capacity | TAMAMLANDI / HYPOTHESIS | ATR-parity drawdown'ı düşürdü; execution/capacity kapısı eksik. |
| 9 | Path-aware ve pre-rise araştırması | TAMAMLANDI / LOW POWER | Intraday alt kümesi çok küçük; full-universe günlük proxy sonucu zayıf. |
| 10 | Event/state/similar-case/abstention bataryası | TAMAMLANDI / EXPLORATORY | Similar-case base-rate'i geçmedi; abstention ayrımı araştırma adayı. |
| 11 | Gated research program değerlendirmesi | TAMAMLANDI | P0 açık; P1/P2 blocked; P3-P8 not opened; P9 blocked. |

## Koşulan ana deneyler

### Score, ranking ve selection

- Strategic Lab: `18` deney; `17` completed, `1` partial.
- Ten Perspectives Lab: `13/13` completed.
- Mirror Analysis: `9/9` completed.
- Score geçmiş 5 günlük getiriyle `rho=0,376`, forward 5 günlük close-to-close ile yaklaşık `rho=0,013` ilişkili.
- Score rank'leri sticky: day-over-day `rho=0,742`.
- Score, `dist_52w_high` extension değişkenini güçlü biçimde kodluyor: `rho=0,667`.
- Out-of-sample Brier skill base-rate'e göre negatif: `-0,019` ve `-0,030`.
- Eligible portföy aynı tarih random rejected portföylerine karşı median `-2,01 pp` fark gösterdi; yalnızca `35` günün `%31`'inde pozitifti.
- SPY'a karşı median relative return `-1,22 pp`; block bootstrap CI sıfırın altında raporlandı.
- `entry_ok` güncel cost senaryosunda mean `-%1,4361`, median `-%3,3977`, positive rate `%30,16`; full comparison median `-%1,8605` ve positive rate `%39,75`.

**Karar:** Score, `entry_ok` veya inverse-score production rule adayı değil.

### Risk, portfolio ve sizing

ATR-parity exploratory çalışmasında:

- Equal-weight max drawdown: `-%24,3`
- ATR-parity max drawdown: `-%15,9`
- ATR-parity en iyi günlük Sharpe: `0,267`

Bu sonuç seçim edge'i değil, portföy konstrüksiyonu etkisidir. Eligible, rejected ve random counterfactual sepetlerde aynı protokolle doğrulanmadan production sizing kuralı yapılamaz.

### Gap, RVOL ve path

Keşif sonuçları:

- Gap-up `>=3%`: 5 günlük median `-%3,04`, pozitif oran `%29,4`, `n=85`.
- Gap-down `>=3%`: 5 günlük median `+%3,05`, pozitif oran `%66,7`, `n=51`.
- High-RVOL eligible tercili: median `-%1,77`, pozitif oran `%38,7`.
- Low-RVOL grubu: median `+%0,68`, pozitif oran `%54,3`.
- Pre-rise intraday close-location 5 günlük lift `+9,29 pp`, fakat validation'da yalnızca `3` selected satır.
- Intraday path gate sonrası yalnızca `237` satır, `93` sembol ve `16` tarih kaldı.
- Full-universe daily-proxy pre-rise 5 günlük matched-control farkı `+0,194 pp`, `p≈0,056`; maliyet sonrası medyanlar negatif kaldı.

**Karar:** Gap-reversal, RVOL-inversion ve close-location yalnızca pre-registered/exploratory hipotezlerdir. Bunlardan production entry sinyali çıkarılmadı.

### TP/SL, exit ve timing

- Fixed-target protokolü `3.120` konfigürasyon test etti.
- White Reality Check `p=0,7413`.
- Hansen SPA `p=0,7761`.
- CPCV/PBO `0,6`.
- Seçilmiş en iyi mean-net kombinasyonların medianları robust değildi; target-cap, horizon ve outlier etkisi mevcut.
- Günlük `-1 ATR` invalidation proxy'si medianı iyileştirmedi ve adayların yaklaşık `%90`'ını durdurdu.
- Signal-close raw mean `6,8838%` olsa da median `%0`, trimmed mean `-0,0290%`; toplam katkının `%108`'i top `%5` outlier'lardan geldi.
- Daily half-life: day-1 median `+%0,0311`; day-5 median `-%0,6711`.

**Karar:** TP/SL, exit veya headline mean sonuçlarından production kuralı çıkarılmadı.

### Event/state/similar-case/abstention

Yeni batarya `100.496` ham ve `43.323` canonical satır üzerinde çalıştı:

- Train/validation: `21.869` / `21.454` satır; `57` / `25` tarih.
- Features: gap, RVOL, ATR, 52-week distance, score.
- State'ler: ordinary, gap_down, gap_up, high_activity, extended_up.
- Similar-case: `k=25`, train-only median/IQR standardization.
- 1 günlük MAE: base-rate `%6,1676`, similar-case `%6,2531`.
- 5 günlük MAE: base-rate `%12,3902`, similar-case `%12,6930`.
- Abstention oranı: `%25,0023`.
- Aktif grup 5 günlük medianı `-%0,09395`; abstain grubu `-%3,16054`.

**Karar:** Similar-case ana hipotezi desteklenmedi. Abstention/evidence-quality ayrımı bağımsız veriyle tekrar test edilebilecek bir aday olarak kaldı; production veto veya score değildir.

## Gated program: ne koşuldu, ne açılamadı?

Manifest: `data/backtest_out/gated_research_program_2026-08-12.json`
Planlanan toplam: `220` test
Priority listesi: `25` test

| Faz | Test | Durum | Neden |
|---|---:|---|---|
| P0 Research protocol | 12 | COMPLETED | Export, split, lineage ve null kontrolleri mevcut. |
| P1 Data reliability | 30 | BLOCKED | PIT listing/delisting, corporate-action feed ve immutable prior cache yok. |
| P2 Label and execution | 26 | BLOCKED | Observed spread/slippage/impact, ADV-conditioned fill ve execution kaydı yok. |
| P3 Baselines/target semantics | 20 | NOT_OPENED | P2 prerequisite blocked. |
| P4 Score decomposition | 28 | NOT_OPENED | P3 açılmadı. |
| P5 Entry setup families | 30 | NOT_OPENED | P4 açılmadı. |
| P6 Eligibility decomposition | 18 | NOT_OPENED | P5 açılmadı. |
| P7 Exit/holding/risk | 20 | NOT_OPENED | P6 açılmadı. |
| P8 Portfolio/risk/capacity | 16 | NOT_OPENED | P7 açılmadı. |
| P9 Robustness/locked validation | 20 | BLOCKED | Önceki fazlar geçmeden locked OOS açılmaz. |

Data-readiness yenilemesi de aynı durumu verdi:

- P1: `BLOCKED`
- P2: `BLOCKED`
- H1/H2/H3 confirmatory: `HOLD`
- Locked OOS: `NOT_OPENED`

Bu bloklar “sonuç negatif” anlamına gelmez; ilgili sorunun doğrulanabilir biçimde test edilemediği anlamına gelir.

## Production'a dönüşme ihtimali olanlar

### 1. ATR-parity risk sizing
En kuvvetli aday; risk konstrüksiyonu olarak. Önkoşul: eligible/rejected/random sepetlerde aynı etki, cost/capacity ve turnover testi.

### 2. Veri kalite veto/uyarı katmanı
2.047 sembolün 485'inde `%50+` close-jump flag'i var. Önce corporate-action/provider sınıflandırması yapılmalı; sessiz satır silme yerine açıklanabilir quality state tercih edilmeli.

### 3. Evidence-quality / abstention state
Düşük evidence quartile'ı daha kötü 5 günlük medyanla ayrıştı. Bağımsız eşik, yeni veri ve kullanıcı testi olmadan production kararı verilemez.

### 4. Gap/RVOL risk context
Directional alpha değil, extension/reversal risk uyarısı olarak daha makul. H1/H2 bağımsız veri ve locked/independent validation olmadan açılmaz.

## Production'a dönüşmemesi gerekenler

- Mevcut composite score'un olasılık veya yön sinyali olarak yorumlanması.
- `entry_ok`'nin mevcut haliyle production edge kabul edilmesi.
- En iyi görünen fixed-target/TP/SL kombinasyonunun grid içinden seçilip canlıya alınması.
- MFE sonuçlarının endpoint P&L gibi kullanılması.
- Gap-up/gap-down veya high-RVOL keşif sonuçlarının aynı veriyle confirmatory kabul edilmesi.
- Locked OOS açılmadan production yayın veya risk kararı verilmesi.

## Gerçekten kalan işler

1. PIT security master, listing/delisting ve ticker lineage edinmek.
2. Corporate-action/provider açıklamasıyla büyük fiyat sıçramalarını sınıflandırmak.
3. Tam immutable bar-cache snapshot saklamak ve restatement detector'ı açmak.
4. Observed fill, spread, slippage, impact, ADV ve timestamp verisi toplamak.
5. P1/P2'yi yeniden değerlendirmek.
6. P1/P2 geçerse pre-registered H1/H2/H3'ü bağımsız veri veya reserved holdout üzerinde çalıştırmak.
7. Sonuçlar başarılı olursa, ayrı Level B production önerisi hazırlamak.
8. Locked OOS'u yalnızca gerekli insan onayıyla açmak.

Bu adımlar tamamlanmadan mevcut veriyle yeni alpha-family araması yapmak metodolojik olarak savunulabilir değildir.

## Doğrulama ve izlenebilirlik

- Full focused research suite: `44 passed`.
- New context battery artifact: `data/backtest_out/decision_context_battery_2026-08-12.json`.
- Refreshed data readiness: `data/backtest_out/data_readiness_audit_2026-08-12.json`.
- Gated manifest: `data/backtest_out/gated_research_program_2026-08-12.json`.
- Detailed prior synthesis: `reports/research_battery_full_2026-08-11.md`.
- Inventory: `reports/scanner_research_complete_inventory_2026-08-11.md`.
- No scanner, score, ranking, entry/exit, risk, portfolio, publication, broker, shadow, paper/live or locked-OOS behavior changed.
