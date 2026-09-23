# FinPilot — Flag Evidence Matrix & Evidence Chain

**Tarih:** 2026-09-11 · **Tip:** Evidence consolidation (read-only). Yeni deney/model/predictive test ÜRETİLMEDİ.
**Temel ayrım (§34, LOCKED):** `Implemented ≠ Enabled ≠ Data Available ≠ Behaviorally Active ≠ Predictive ≠ Economic`. Hiçbir seviye bir sonrakine otomatik taşınmaz.
**Negative evidence korunur:** `NO_EFFECT` (davranış yok) ≠ `PREDICTIVE_REJECTED` (test başarısız) ≠ `NOT_TESTED`.

---

## 1. Executive Summary

- **Behaviorally active (3):** SQUEEZE, LOTTERY_FADE, OVERNIGHT_GAP — score ve rank'ı ölçülebilir değiştiriyorlar.
- **Data-inactive / behaviorally inactive (2):** EDGAR_CATALYST (catalyst_factor=0, cache boş), FRED_MACRO (multiplier no-op).
- **Predictive evidence:** Hiçbir flag'de **SUPPORTED yok.** Ablation + walk-forward'da hiçbiri baseline'ı OOS'ta tekrarlanabilir geçmedi. LOTTERY/OVERNIGHT bucket'ta negatif-seçim gösterdi ama Top-N'e dönüşmedi → **INCONCLUSIVE**, rejection değil.
- **Economic evidence:** Hiçbir flag'de **NOT_TESTED** (maliyet/slippage/portföy testi yapılmadı).
- **En büyük evidence gap:** Behaviorally-active flag'lerin (SQUEEZE/LOTTERY/OVERNIGHT) predictive değeri — ama bu, baseline'in kendisi provisional olduğu için GATE B3/B4'e bağımlı.

## 2. Evidence Matrix (ana tablo)

| Mechanism | Implemented | Enabled | Data Available | Behavioral | Meta | Ablation | Walk-Forward | Predictive | Economic | Current Status | Evidence Level |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|
| **SQUEEZE** | YES | YES | YES | ACTIVE | SUPPORTED* | NOT_SUPPORTED | NOT_SUPPORTED | NOT_TESTED | NOT_TESTED | BEHAVIORALLY_ACTIVE | **2** |
| **LOTTERY_FADE** | YES | YES | YES | ACTIVE | SUPPORTED* | INCONCLUSIVE | NOT_SUPPORTED | NOT_TESTED | NOT_TESTED | BEHAVIORALLY_ACTIVE | **2** |
| **OVERNIGHT_GAP** | YES | YES | YES | ACTIVE | SUPPORTED* | INCONCLUSIVE | NOT_SUPPORTED | NOT_TESTED | NOT_TESTED | BEHAVIORALLY_ACTIVE | **2** |
| **EDGAR_CATALYST** | YES | YES | **NO** | NO_EFFECT | NOT_TESTED | UNTESTABLE_NO_VARIANCE | UNTESTABLE | NOT_TESTED | NOT_TESTED | **DATA_INACTIVE** | **1** |
| **FRED_MACRO** | YES | YES | UNKNOWN (multiplier=1.0 no-op) | NO_EFFECT | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED | DATA_INACTIVE / BEHAVIORALLY_INACTIVE | **1** |

\* "Meta-validation SUPPORTED" = factor'un gerçek/nonzero olduğu ve descriptive pattern taşıdığı (meta_validation_audit 2026-09-08: factor data real). Bu **predictive değil** — yalnızca "veri gerçek ve davranış üretiyor" düzeyi.

## 3. Behavioral Evidence (Flag Impact Measurement 2026-09-10)

Referans: `reports/flag_impact/` · export `scan_export_latest.json` (2026-09-09, 1801 sonuç, scan_complete) · git a242b06.

| Mechanism | Score Δ Mean | Score Δ Max | Rank Changed | Mean Abs Rank Δ | Max Abs Rank Δ | Any Effect | Class |
|---|---:|---:|---:|---:|---:|---:|---|
| SQUEEZE | +0,387 | +1,49 | 1.671 | 34,4 | 223 | 1.693 | RANK_EFFECT |
| LOTTERY_FADE | −0,700 | −2,00 | 1.792 | 86,8 | 504 | 1.801 | RANK_EFFECT |
| OVERNIGHT_GAP | −0,143 | −1,00 | 1.776 | 19,4 | 407 | 1.801 | RANK_EFFECT |
| EDGAR_CATALYST | 0 | 0 | 0 | 0 | 0 | 0 | NO_EFFECT |
| FRED_MACRO | 0 | 0 | 0 | 0 | 0 | 0 | NO_EFFECT |

**Coverage sınırı (§9):** 1.801 sembol universe üzerinde ölçüm; **1.508'i tam score_input'lu, 293'ünde reconstruction mümkün değildi ve imputation yapılmadı.** Behavioral sonuç full-universe perfect coverage iddiası DEĞİL.

## 4. Predictive Evidence

| Mechanism | Ablation (EOD 70/30, c2c_5d) | Walk-Forward (4 pencere, c2c_1d) |
|---|---|---|
| SQUEEZE | OOS spearman −0,034 (baseline −0,024'ten kötü); 0 pencere iyi | 0/3 better |
| LOTTERY_FADE | OOS spearman +0,055 ama tutarsız (bucket negatif-seçim, Top-N tutmuyor) | 0/3 better |
| OVERNIGHT_GAP | OOS spearman +0,009, tutarsız | 1/3 better |
| EDGAR_CATALYST | UNTESTABLE_NO_VARIANCE (catalyst_factor=0) | UNTESTABLE |
| FRED_MACRO | NOT_TESTED | NOT_TESTED |

**Sonuç:** Hiçbir flag'de predictive **SUPPORTED yok.** LOTTERY/OVERNIGHT **INCONCLUSIVE** (negatif-seçim sinyali var ama Top-N/OOS'a dönüşmüyor) — bu `PREDICTIVE_REJECTED` değil, `INCONCLUSIVE`. Catalyst **NOT_TESTED** (veri yok). **Gerçek anlamda PREDICTIVE_VALIDATION hiçbirinde yapılmadı** — ablation/walk-forward baseline-component testiydi, flag'in forward-return'e katkısını izole ölçen matched-control yok.

## 5. Economic Evidence

```
TÜM MECHANISM'LER: ECONOMIC_VALIDATION = NOT_TESTED
```
Transaction cost / slippage / fees / liquidity / position sizing / drawdown / portfolio-level test hiçbir flag için yapılmadı. (Fade'in %1 maliyette negatif olduğu ayrı çalışmada biliniyor ama bu flag bazlı değil, strategy bazlı.)

## 6. Evidence Chain — Mechanism by Mechanism

```
SQUEEZE:   Implemented → Enabled → Data ✓ → Behaviorally ACTIVE
           → score Δ +0.387, rank 1671 → Predictive ? → Economic ?
LOTTERY_FADE: Implemented → Enabled → Data ✓ → Behaviorally ACTIVE (en güçlü)
           → score Δ −0.700, rank 1792, mean-abs-rank 86.8 → Predictive ? → Economic ?
OVERNIGHT_GAP: Implemented → Enabled → Data ✓ → Behaviorally ACTIVE
           → score Δ −0.143, rank 1776 → Predictive ? → Economic ?
EDGAR_CATALYST: Implemented → Enabled → Data ✗ (catalyst_factor=0, cache boş)
           → Behaviorally NO_EFFECT → Predictive UNKNOWN → Economic UNKNOWN
FRED_MACRO: Implemented → Enabled → Data ? (multiplier 1.0 no-op)
           → Behaviorally NO_EFFECT → Predictive UNKNOWN → Economic UNKNOWN
```

## 7. Known vs Unknown

| Mechanism | KNOWN | UNKNOWN |
|---|---|---|
| SQUEEZE | implemented, enabled, data var, behaviorally active, score+rank etkisi | predictive, walk-forward robustness, economic |
| LOTTERY_FADE | implemented, enabled, data var, behaviorally **en güçlü**, bucket'ta negatif-seçim | predictive (Top-N), walk-forward, economic |
| OVERNIGHT_GAP | implemented, enabled, behaviorally active | predictive, robustness, economic |
| EDGAR_CATALYST | implemented, enabled, **data yok**, behaviorally inactive | veri gelince predictive, economic |
| FRED_MACRO | implemented, enabled, multiplier no-op | veri/regime bağımlılığı, predictive, economic |

## 8. Evidence Gaps (en büyük)

1. **Predictive value of behaviorally-active flags** (SQUEEZE/LOTTERY/OVERNIGHT) — ama baseline provisional olduğu için GATE B3/B4'e bağımlı.
2. **Catalyst data pipeline** — single-writer/regresyon onarımı olmadan hiçbir şey test edilemez.
3. **Economic layer hiç yok** — tüm flag'ler için.
4. **FRED data/regime koşulu** — multiplier ne zaman 1.0'dan sapar bilinmiyor.

## 9. Research Priority (evidence gap'e göre — predictive varlığı varsayılmadan)

- **PRIORITY 1 (behaviorally active + predictive eksik):** LOTTERY_FADE, SQUEEZE, OVERNIGHT_GAP → ama **GATE B3/B4 baseline validation'ı bekler** (baseline provisional iken flag predictive testi anlamsız).
- **PRIORITY 2 (data-inactive):** EDGAR_CATALYST (önce data-integrity), FRED_MACRO (multiplier koşulu).
- **PRIORITY 3 (sufficiently validated):** **NONE.**

## 10. Governance / Limitations

- **Single-export limitation:** Behavioral ölçüm tek gün/tek export (2026-09-09); zaman-içi tekrarlanabilirlik bu çalışmanın kapsamı dışında.
- **Coverage:** 293/1801 satır score_input eksik (impute edilmedi).
- **Tie/compression:** %99,78 tie bulgusu geçerli — score etkisi rank etkisine dönüşmeyebilir; ayrı tutuldu.
- **Reconstruction limitation:** Baseline NOT_FULLY_RECONSTRUCTED (geçmiş); forward capture B1/B2 ile mümkün.
- **Behavioral ≠ Predictive ≠ Economic** ayrımı korundu (§34).
- **Üretilmeyen iddialar (§27):** "works / profitable / predicts winners / useless / does not work" — hiçbiri kullanılmadı.
- Production/flag/.env/DB/scheduler değiştirilmedi; yeni scan/veri toplanmadı; synthetic/imputation/backfill YOK; commit/push yapılmadı.

---

## §32 — Final 7 Soru

1. **Hangi flag davranış üretiyor?** SQUEEZE, LOTTERY_FADE, OVERNIGHT_GAP.
2. **Hangi flag implemented/enabled ama data yüzünden aktif değil?** EDGAR_CATALYST (data yok), FRED_MACRO (multiplier no-op).
3. **Hangi flag'lerin predictive evidence'ı var?** **Hiçbiri** (SUPPORTED yok; LOTTERY/OVERNIGHT INCONCLUSIVE).
4. **Hangi flag'lerin predictive evidence'ı yok?** Hepsi — bazıları NOT_TESTED, bazıları INCONCLUSIVE.
5. **Hangi flag'ler economic validation'a ulaşmış?** **Hiçbiri** (NOT_TESTED).
6. **En büyük evidence gap?** Behaviorally-active flag'lerin predictive değeri (baseline provisional'a bağımlı) + economic layer'ın tamamen yokluğu.
7. **Sonraki mantıklı gate?** **GATE B3/B4** — önce baseline'in kendisi predictive mi netleşmeli; flag predictive testi ancak sağlam bir baseline üzerinde anlamlı. Flag-bazlı predictive/economic test ondan sonra.

## §36 — Tek bakışta kanıt haritası

```
                 BEHAVIORAL   PREDICTIVE    ECONOMIC
SQUEEZE              ✓            ?             ?
LOTTERY_FADE         ✓            ?             ?
OVERNIGHT_GAP        ✓            ?             ?
EDGAR_CATALYST       ✗            ?             ?
FRED_MACRO           ✗            ?             ?
```
✓ = o seviyede kanıt destekli · ✗ = o seviyede aktif/kanıt yok · ? = test edilmedi/bilinmiyor

## §35 — Final Gate

```
FLAG_EVIDENCE_MATRIX = PASS
```
Tüm aktif flag'ler tespit edildi; mechanism mapping doğrulandı; behavioral evidence kaynaklandırıldı; meta/ablation/walk-forward/predictive/economic katmanları tarandı; unknown'lar açıkça işaretlendi; behavioral/predictive/economic ayrımı korundu; production/.env değişmedi; yeni scan yapılmadı; synthetic/imputation yok.

**EVIDENCE_GAP kayıtlı:** predictive (tüm flag'ler), economic (tüm flag'ler), catalyst data, FRED regime koşulu.
