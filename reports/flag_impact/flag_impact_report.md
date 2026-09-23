# FLAG IMPACT AUDIT — Mevcut Son Export Üzerinde Davranışsal Ölçüm

**Tarih:** 2026-09-10 · **Tip:** Observability / measurement only. Predictive test / backtest / OOS / optimizasyon YOK.
**Level:** A (read-only; production kod/flag/.env/ranking değiştirilmedi).
**Prensip:** "Bu flag bugün mevcut export üzerinde sistemi davranışsal olarak etkiliyor mu, ne ölçüde?" — predictive değer iddiası YOK.

---

## Scope

```
Export:      data/distribution/scan_export_latest.json
             (date 2026-09-09, run_id 20260909T111531, universe 1812 → 1801 sonuç,
              scan_complete=true) — son TAM export; 09-10 dosyaları _partial_ olduğu için elendi
Commit:      a242b06
Symbols:     1801
Measurement: 2026-09-10T15:39:48Z
Script:      research/flag_impact_measurement_2026_09_10.py
```

## Repo notu
Prompt `C:\Users\meric\Finsense` diyordu; gerçek FinPilot repo **`C:\Users\meric\Borsa`**. Flag'ler `scanner/score_engine.py`'de.

## §4 — Flag kapsamı (koddan doğrulandı)

**§4'teki liste (filter_score, alignment_ratio, momentum_ratio, volume_spike, price_momentum, trend_strength) FLAG DEĞİL** — bunlar env-gate'i olmayan, sürekli açık baseline input'ları. → **NOT_A_FLAG**, ablation'dan çıkarıldı.

**Gerçek env-gated skor flag'leri** (score_engine.py):
`FINPILOT_ENABLE_SQUEEZE_FACTOR`, `FINPILOT_ENABLE_EDGAR_CATALYST`, `FINPILOT_ENABLE_LOTTERY_FADE`, `FINPILOT_ENABLE_OVERNIGHT_GAP`, `FINPILOT_ENABLE_FRED_MACRO` (multiplier). `.env`: ilk dördü + FRED = 1 (ON); LEGACY_COMPOSITE_RANKING=0.

## OFF/ON semantics (§8, koddan)
- OFF = gated faktör 0 katkı (env-gate). ON = faktör production ağırlığıyla aktif. Production kodu karar verir; tahmin yok.
- **Reconstruction doğrulaması:** `recompute(all-ON, sentiment=None)` == stored `recommendation_score` → **1508/1508 EXACT** (n=1508; 293 satırda score_input eksik). Sentiment=None ile production birebir.

## Data integrity (§19)
```
OFF/ON same universe:   PASS (1801 == 1801)
duplicate symbols:      0
missing score_input:    293 satır (score_input alanı yok — bu satırlarda flag faktörü de yok;
                        coverage etkisi olarak raporlandı, impute edilmedi)
Synthetic data:         0
Imputation:             0
Historical reconstruction: 0
Yeni scan / yeni veri:  YOK (mevcut export kullanıldı)
```

## Main result (flag-ON vs all-OFF baseline)

| Flag | Score Δ Mean | Score Δ Max | Rank Changed | Mean Abs Rank Δ | Max Abs Rank Δ | Any Effect | Classification |
|---|---:|---:|---:|---:|---:|---:|---|
| **SQUEEZE** | +0,387 | +1,49 | 1671 | 34,4 | 223 | 1693 | **RANK_EFFECT** |
| **LOTTERY_FADE** | −0,700 | −2,00 | 1792 | 86,8 | 504 | 1801 | **RANK_EFFECT** |
| **OVERNIGHT_GAP** | −0,143 | −1,00 | 1776 | 19,4 | 407 | 1801 | **RANK_EFFECT** |
| **EDGAR_CATALYST** | 0,000 | 0,00 | 0 | 0,0 | 0 | 0 | **NO_EFFECT** |
| **FRED_MACRO** | 0,000 | 0,00 | 0 | 0,0 | 0 | 0 | **NO_EFFECT** |

*Rank sign convention (§11): `rank_delta = rank_on − rank_off`; negatif = iyileşti.*
*Score-change tolerance: 0,01 (production 3dp rounding ile uyumlu; FP noise elenir).*

## Symbol-level changes (en çok etkilenenler — örnek)
`reports/flag_impact/flag_impact_symbol_level.csv` (5.295 satır) — yalnızca score veya rank değişen semboller.

## Interpretation (flag başına)

- **SQUEEZE:** Skoru **yukarı** itiyor (+0,39 ort). 1.402 sembolde skor, 1.671 sembolde rank değişiyor. Davranışsal olarak aktif ve ranking'i oynatıyor.
- **LOTTERY_FADE:** En güçlü davranışsal etki. Skoru **aşağı** çekiyor (−0,70 ort, max −2,0). 1.792 sembolde rank değişiyor, ortalama rank sıçraması 86,8 — en büyük rank etkisi bu flag'de.
- **OVERNIGHT_GAP:** Skoru hafif aşağı (−0,14), 1.776 sembolde rank değişiyor. Aktif ama daha zayıf.
- **EDGAR_CATALYST:** **NO_EFFECT.** `catalyst_factor` score_input'ta 0 (cache boş/regrese) → flag açık olmasına rağmen davranışsal olarak hiçbir şey değiştirmiyor. **IMPLEMENTED ≠ ACTIVE ≠ INFLUENTIAL**'ın canlı örneği.
- **FRED_MACRO:** **NO_EFFECT** — multiplier şu an 1.0 (veya gated faktörler devrede değil).

## Important caveats (§23)

1. **Behavioral effect ≠ predictive value ≠ economic value** (§25). Bu ölçüm yalnızca "flag pipeline'da davranışsal olarak etkili mi" der; forward-return tahmini YAPMAZ.
2. **Coverage:** 293/1801 satırda `score_input` eksik → bu sembollerde flag etkisi ölçülemedi (catalyst/lottery skor-değişmez sayısı 293 ile çakışıyor). Bu bir **veri kapsamı** sınırı.
3. **Tie/compression:** Daha önceki bulgu (%99,78 tie) burada da geçerli — score değişse bile bazı rank'lar tie nedeniyle değişmeyebilir; bu yüzden score etkisi ve rank etkisi ayrı raporlandı.
4. **293 eksik score_input** satırı ranking'i etkiliyor olabilir (flag-OFF baseline'da bu satırlar da sıralanıyor).
5. Ölçüm tek export/tek güne ait (2026-09-09) — zaman içinde tekrarlanabilirlik bu çalışmanın kapsamı dışında.

## Son 7 sorunun cevabı (§26)

1. **Son export:** `scan_export_latest.json` (2026-09-09, 1801 sonuç, scan_complete). 09-10 `_partial_` dosyaları elendi.
2. **Kaç symbol ölçüldü:** 1.801 (1.508'i tam score_input'lu; 293'ü score_input eksik).
3. **Her flag'in score delta'sı:** SQUEEZE +0,387 · LOTTERY_FADE −0,700 · OVERNIGHT_GAP −0,143 · EDGAR_CATALYST 0 · FRED_MACRO 0.
4. **Kaç sembolün rank'ı değişti:** SQUEEZE 1.671 · LOTTERY_FADE 1.792 · OVERNIGHT_GAP 1.776 · EDGAR_CATALYST 0 · FRED_MACRO 0.
5. **En etkili flag:** **LOTTERY_FADE** (en büyük score ve rank etkisi; rank mean-abs 86,8, max 504).
6. **Etkisiz flag var mı:** Evet — **EDGAR_CATALYST** (catalyst_factor=0, veri yok) ve **FRED_MACRO** (multiplier 1.0) davranışsal olarak sıfır etki.
7. **Sonraki gate için anlamı:** Bu ölçüm flag'lerin **davranışsal etkisini** doğruladı ama **predictive değerlerini DEĞİL**. Flag kararı (Level B/C) için bu, mevcut meta-validation/ablation/walk-forward kanıt zincirini **tamamlayıcı** bir behavioral katman. Predictive validation hâlâ GATE B4.

## Gate

```
FLAG_IMPACT_MEASUREMENT = PASS
```
(export doğru tespit edildi; OFF/ON reproducible; aynı universe; score+rank delta hesaplandı; affected count üretildi; data integrity PASS; synthetic/imputation=0; production'a dokunulmadı)

## Reproducibility (§20)
export_path + export run_id + git_commit a242b06 + measurement_ts + script + score_tolerance=0,01 + rank method (composite desc) + flag semantics (env-gate) kaydedildi → `flag_impact_summary.json`.

## Governance
- Level A read-only. Production scoring/ranking/flag/.env/DB/scheduler değiştirilmedi. Yeni scan/veri toplanmadı; mevcut export kullanıldı. Synthetic/imputation/backfill YOK. Commit/push yapılmadı.
- Flag kararı bu çalışmayla OTOMATIK değişmez; bu yalnızca behavioral measurement. Predictive claim YOK.
