# Scoring Ablation & Causal Validation — Sonuç Raporu

**Tarih:** 2026-09-08 · **Prompt:** Scoring Ablation Master Prompt v1.0
**Level:** A — READ-ONLY RESEARCH (hiçbir production/kod/flag/veri değiştirilmedi)
**Dataset:** `data/backtest_out/full_universe_enriched_eod_only.csv` (EOD-only etiketler — c2c_5d bütünlük düzeltmesi uygulanmış)
**Split:** Kronolojik 70/30 · kesim 2026-06-26 · dev n=19.141, OOS n=17.149
**Artifact:** `data/backtest_out/scoring_ablation_2026-09-08.json` · `reports/scoring_ablation_results_2026-09-08.csv` · `reports/scoring_component_leaderboard_2026-09-08.csv`

---

## Executive Summary

Dört flag-kapılı component test edildi. Sonuç: **hiçbiri OOS'ta baseline'ı anlamlı biçimde iyileştirmiyor** ve bazıları kötüleştiriyor. Catalyst **UNVALIDATED** (veri boş, factor=0.0). Lottery ve overnight negatif-seçim davranışı bucket analizinde doğrulandı ama bu, skora katkıya çevrilmiyor.

**En önemli bulgu:** Flag'ler skoru %83,5 satırda değiştiriyor (meta-audit) ama bu değişiklik **predictive değer üretmiyor** — IMPLEMENTED ≠ ACTIVE ≠ INFLUENTIAL ≠ PREDICTIVE ayrımı doğrulandı.

---

## Baseline Tanımı

`scanner/score_engine.py` formülü (flag'ler kapalı):

```
BASE = 2·regime + 2·direction + 0.5·score + 1.5·filter_score
     + 2·alignment_ratio + vol_regime_weight·momentum_ratio
     + 0.5·(volume_spike + price_momentum + trend_strength)
```

Component katkıları (koddan doğrulandı): Squeeze +0…+1.5 · Lottery −0…−2.0 · Overnight −0…−1.0 · Catalyst −1.5…+1.5.

---

## Leaderboard (Dev → OOS)

| Model | Dev Spearman | Dev Top-20 mean | OOS Spearman | OOS Top-20 mean | OOS Top-20 hit |
|---|---:|---:|---:|---:|---:|
| **baseline** | -0,0021 | +9,06 | -0,0235 | -5,05 | 0,35 |
| **+squeeze** | -0,0221 | +9,06 | -0,0339 | -3,91 | 0,50 |
| **+lottery** | +0,0211 | +1,78 | **+0,0548** | +0,83 | 0,55 |
| **+overnight** | +0,0190 | +4,57 | +0,0093 | -2,85 | 0,40 |
| **+catalyst** | -0,0256 | +9,06 | -0,0150 | -3,91 | 0,50 |
| **full** | -0,0005 | +7,46 | +0,0488 | +0,72 | 0,50 |

**Okuma:** OOS Top-20 hit rate'i baseline 0,35'ten lottery 0,55'e çıkıyor — ama bu küçük örneklem ve tek bölünme. Spearman her yerde ≈0 (sıralama gücü yok). Dev→OOS tutarlılığı yok (baseline dev +9,06 → OOS -5,05).

---

## Bucket Analizi (dev, 5g getiri — quintile ortalaması)

| Component | Q1 (düşük) | Q3 | Q5 (yüksek) | Yorum |
|---|---|---|---|---|
| **squeeze** | +0,76 | +2,25 | (düşük varyasyon) | Zayıf pozitif, monoton değil |
| **lottery** | +1,59 | +2,53 | **-0,33** | Yüksek lottery → daha kötü ✓ (negatif-seçim doğrulandı) |
| **overnight** | +2,24 | +2,34 | **-1,75** | Yüksek overnight → daha kötü ✓ (negatif-seçim doğrulandı) |
| **catalyst** | — | — | — | Yetersiz varyasyon (hep 0.0) |

**Lottery ve overnight'ın cezalandırıcı tasarımı bucket'ta doğrulanıyor** (yüksek değer → düşük getiri). Ama bu, onları skora eklemenin sıralamayı iyileştirdiği anlamına gelmiyor — Top-20 metrikleri bunu göstermiyor.

---

## Component-by-Component Kararlar

| Component | Karar | Gerekçe |
|---|---|---|
| **Squeeze** | **UNVALIDATED** | Skora katkı var ama Top-20/OOS iyileştirmesi yok; bucket zayıf-pozitif ama monoton değil |
| **Lottery** | **MODIFY (öneri)** | Negatif-seçim bucket'ta doğrulandı (yüksek→kötü) ama skora katkı Top-20'de tutarsız; weight fazla olabilir |
| **Overnight** | **MODIFY (öneri)** | Aynı: negatif-seçim doğrulandı ama OOS Top-20 -2,85 |
| **Catalyst** | **UNVALIDATED** | Veri boş (cache=0.0); değerlendirilemez. Veri hattı onarımı şart |
| **Full** | **UNVALIDATED** | Kombinasyon OOS'ta baseline'dan iyi ama tek bölünme + küçük örneklem |

**Hiçbir component KEEP değil.** Hiçbir component DISABLE değil (lottery/overnight'ın negatif-seçim sinyali gerçek). Kod değiştirilmedi — yalnızca öneri.

---

## Sınırlamalar

- Tek kronolojik bölünme (70/30); walk-forward değil.
- Catalyst değerlendirilemedi (factor=0.0, cache boş) — veri hattı onarımı ayrı iş.
- Top-20 küçük örneklem; dev→OOS istikrarsızlığı yüksek.
- Squeeze bucket varyasyonu düşük (çoğu satır 0'a yakın).

## Negatif Bulgular (saklanmadı)

- Baseline bile OOS'ta Top-20 hit 0,35 — skor sıralaması genel olarak zayıf.
- Hiçbir component baseline'ı OOS'ta anlamlı iyileştirmiyor.
- Full model kombinasyonu tek bölünmede iyi görünüyor ama tekrarlanabilirlik yok.

---

## Son Cümleler (karar formatı)

> "Based on the available evidence, **Squeeze** is **UNVALIDATED** because it perturbs the score but shows no OOS ranking improvement."
> "Based on the available evidence, **Lottery** is **MODIFY** because its negative-selection signal is real in buckets but its score contribution is inconsistent in Top-N."
> "Based on the available evidence, **Overnight** is **MODIFY** because its negative-selection signal is real in buckets but OOS Top-20 is negative."
> "Based on the available evidence, **Catalyst** is **UNVALIDATED** because the factor data is empty (cache regression); it cannot be evaluated until the pipeline is repaired."
> "Based on the available evidence, the **Full model** is **UNVALIDATED** because the apparent OOS gain rests on a single split and small Top-N sample."

---

## Önerilen Sonraki Deney

**Component-ablation matched-control:** her component için aynı gün aynı büyüklükte rastgele kontrol grubuyla karşılaştırma (mevcut test bunu yapmıyor). Bu, "component seçimi rastgeleden iyi mi?" sorusunu yanıtlar. Ayrıca: walk-forward (tek bölünme değil) + catalyst veri hattı onarımı.

---

## Governance

- READ-ONLY: hiçbir production kodu, `.env`, flag, DB, cache değiştirilmedi.
- Locked OOS NOT_OPENED.
- Dataset: EOD-only (c2c_5d bütünlük düzeltmesi).
- Pre-registration: split/metrics/decision-rules sonuçlardan önce script docstring'inde sabitlendi.
- Negatif bulgular raporlandı.
