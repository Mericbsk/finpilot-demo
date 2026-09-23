# Walk-Forward + Matched-Control + Rank-Displacement — Scoring Validation

**Tarih:** 2026-09-08 · **Prompt:** Walk-Forward Master Prompt v1.0
**Level:** A — READ-ONLY RESEARCH (hiçbir production/kod/flag/veri değiştirilmedi; hiçbir weight optimize edilmedi)
**Dataset:** `data/backtest_out/full_universe_enriched_eod_only.csv` (EOD-only) · Target: `c2c_1d` (1D)
**Pre-registration:** 4 pencere sonuçlardan önce tanımlandı (W1 04-01→05-01, W2 04-22→05-22, W3 05-13→06-12, W4 06-03→07-03; her biri 70/30 kronolojik)
**Artifacts:** `walk_forward_scoring_results_2026-09-08.csv` · `rank_displacement_results_2026-09-08.csv` · `matched_control_results_2026-09-08.csv` · `component_validation_leaderboard_2026-09-08.csv` · `data/backtest_out/walk_forward_scoring_2026-09-08.json`

---

## 1. Executive Summary

4 walk-forward penceresi çalıştırıldı. **Hiçbir component OOS'ta baseline'ı tekrarlanabilir biçimde geçmiyor.** Baseline'in kendisi zayıf (Spearman ≈ 0, Top-20 hit %55–75 ama tutarsız). Rank-displacement ve matched-control çoğu pencerede **yetersiz örnekle bloke oldu** (component'ler çoğu satırı aynı sıralamada bırakıyor — etki var ama az).

**En önemli bulgu:** Component'ler skoru değiştiriyor (meta-audit: %83,5) ama bu değişiklik **sıralamada anlamlı bilgi taşımıyor.** Rank-displacement büyük ölçüde "neutral" kümede yoğunlaşıyor — component'ler çoğu hissenin sırasını zar zor değiştiriyor.

---

## 2. Walk-Forward Sonuçları (OOS Top-20 vs Baseline)

| Component | OOS pencerelerde baseline'dan iyi | Aynı | Kötü | Ortalama Δ | Karar |
|---|---|---|---|---:|---|
| **Squeeze** | 0/3 | 2 | 1 | -0,21 | **UNVALIDATED** |
| **Lottery** | 0/3 | 2 | 1 | -0,49 | **UNVALIDATED** |
| **Overnight** | 1/3 | 2 | 0 | +0,16 | **UNVALIDATED** |
| **Catalyst** | 0/3 | 3 | 0 | 0,00 | **UNVALIDATED — DATA UNAVAILABLE** |
| **Full** | 0/3 | 2 | 1 | -0,73 | **UNVALIDATED** |

*W1 yetersiz örneklemle bloke (oos_n=1). 3 geçerli pencere.*

## 3. Baseline Health

| Pencere | OOS n | Top-20 mean | Top-20 hit | Spearman |
|---|---:|---:|---:|---:|
| W2 | 1.265 | +1,19 | 0,55 | -0,0065 |
| W3 | 1.595 | -0,11 | 0,55 | +0,0374 |
| W4 | 5.593 | +2,24 | 0,75 | -0,0204 |

**Baseline kendi başına zayıf ve tutarsız:** Spearman ≈0 her yerde; Top-20 hit %55–75 ama W3 negatif. **COMPONENT VALIDATION CONFIDENCE = LOW** — zayıf baseline üzerine component ekleyerek güçlü production ranking iddiası yapılamaz.

## 4. Rank Displacement

Component'ler çoğu hisseyi **"neutral"** kümede bırakıyor (|rank_delta|<5). Güçlü displacement (|Δ|≥20) nadirdir. Lottery W4'te: strong_down (aşağı itilenler) mean +1,48/hit %59,4; strong_up (yukarı itilenler) mean +0,43/hit %55,3 — **beklenenin tersi** (aşağı itilenler daha iyi performans gösterdi), ama tek pencere ve küçük fark.

## 5. Matched-Control & Random-Control

- **Matched-control:** Tüm pencerelerde bloke — "few treated" / "no matched dates" / "insufficient". Component displacement'i o kadar küçük ki |rank_delta|≥20 olan treated grubu 20 satıra ulaşmıyor. **WEAK CONTROL — component'lerin sıralama müdahalesi ölçülecek kadar büyük değil.**
- **Random-control:** W1'de yetersiz; diğer pencerelerde component Top-20 vs aynı-gün random karşılaştırması anlamlı fark üretmedi.

## 6. Catalyst

**UNVALIDATED — DATA UNAVAILABLE.** Factor tüm satırlarda 0.0 (cache boş). Pipeline ayrı teknik problem (çift-yazıcı + regresyon, meta-audit).

## 7. Negatif Bulgular (saklanmadı)

- Hiçbir component OOS'ta baseline'ı tekrarlanabilir geçmiyor.
- Baseline kendisi zayıf (Spearman ≈0).
- Rank-displacement çoğu satırda neutral — component etkisi sıralamada minimal.
- Matched/random control büyük ölçüde yetersiz örnekle bloke.
- Catalyst değerlendirilemedi.

## 8. Sınırlamalar

- W1 bloke (oos_n=1) — 3 geçerli pencere.
- Tek gün (c2c_1d) hedefi; 5D ayrı raporlanmadı bu çalışmada.
- Displacement küçük → matched-control güçsüz.
- Rejim analizi: vol_regime mevcut ama pencere başına örneklem küçük; ayrı raporlanmadı (tutarsızlık riski).

## 9. Final Component Table

| Component | Score Impact | Predictive | Walk-Forward | Matched Ctrl | Rank Displacement | OOS | Karar |
|---|---|---|---|---|---|---|---|
| Squeeze | Var | Yok | 0/3 better | Bloke | Minimal | Tutarsız | **UNVALIDATED** |
| Lottery | Var | Zayıf bucket | 0/3 better | Bloke | Ters (tek pencere) | Tutarsız | **UNVALIDATED** |
| Overnight | Var | Yok | 1/3 better | Bloke | Minimal | Tutarsız | **UNVALIDATED** |
| Catalyst | Yok (veri) | — | — | — | — | — | **UNVALIDATED — DATA UNAVAILABLE** |
| Full | Var | Yok | 0/3 better | Bloke | Minimal | Tutarsız | **UNVALIDATED** |

## 10. Final Decisions (format)

> "Based on the available evidence, **Squeeze** is **UNVALIDATED** because it perturbs the score but shows no repeatable OOS ranking improvement across walk-forward windows."
> "Based on the available evidence, **Lottery** is **UNVALIDATED** because its bucket-level negative-selection signal does not survive walk-forward Top-N comparison (0/3 windows better)."
> "Based on the available evidence, **Overnight** is **UNVALIDATED** because its single positive window (1/3) is not repeatable and displacement is minimal."
> "Based on the available evidence, **Catalyst** is **UNVALIDATED** because factor data is empty (pipeline regression); it cannot be evaluated."
> "Based on the available evidence, the **Full model** is **UNVALIDATED** because no component individually improves OOS and the combination shows no repeatable advantage."

## 11. Önerilen Sonraki Deney

**Baseline methodology araştırması** — component validation'dan önce baseline ranking'in kendisi random'dan iyi mi sorusu (Part 36). Zayıf baseline üzerine component eklemek ikinci plandadır. Ayrıca: catalyst veri hattı onarımı; daha uzun yoğun dönemle daha güçlü walk-forward.

## 12. Governance kaydı (öneri — otomatik eklenmedi)

`docs/governance/decision-log.md` için: tarih 2026-09-08, test=walk-forward+matched-control+rank-displacement, dataset=EOD-only, methodology=pre-registered 4 window, sonuç=hiçbir component OOS'ta baseline'ı geçmiyor + baseline zayıf, decision=hepsi UNVALIDATED, limitations=W1 bloke/küçük displacement, next=baseline methodology + catalyst onarımı.

---

## Governance

- READ-ONLY: hiçbir production/kod/flag/veri/ağırlık değiştirilmedi; hiçbir optimizasyon yapılmadı.
- Locked OOS NOT_OPENED.
- Pre-registration: pencereler ve metrikler sonuçlardan önce sabitlendi.
- Negatif bulgular raporlandı.
