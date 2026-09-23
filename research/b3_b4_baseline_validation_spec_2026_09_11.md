# FinPilot — B3/B4 Baseline Validation & Reconstruction (REGISTERED SPEC)

**Version:** 1.0 · **Registered:** 2026-09-11 · **Status:** PRE-REGISTERED · `B3_BLOCKED_BY_B2`
**Governance:** Level B (methodology registration). Meriç onaylı. Bu dosya **metodolojiyi dondurur** — B2 Exit sonrası birebir uygulanır; sonuçlara göre değiştirilmez.
**Kaynak metodoloji:** Kullanıcının B3/B4 Master Prompt'u (2026-09-11) + Meriç onaylı tek ekleme (§4.1).

> Bu bir **spec/plan** dokümanıdır — deney/veri/sonuç ÜRETMEZ. B2 Exit PASS olmadan hiçbir B3/B4 analizi başlatılmaz.

---

## 0. Ana soru

> **FinPilot mevcut baseline scoring sistemi, gelecekteki outcome'u rastgele/chance benchmark'lardan ayırt edilebilir, tekrarlanabilir ve out-of-sample bir signal taşıyor mu?**

İki aşama: **B3-A** Reconstruction & Integrity → **B3-B** Predictive Validation → **B4** Robustness/Confirmation.
**Flag'ler FROZEN.** Hiçbir flag'in predictive katkısı bu aşamada araştırılmaz. Optimization / post-hoc threshold tuning YOK.

## 1. Ön koşul — B2 EXIT (değiştirilemez)

B3 ancak `B2 EXIT = PASS` olduğunda başlar. Mevcut: 24 obs / 1 scan_date → **`B3_BLOCKED_BY_B2`**.

B2 Exit kriterleri (`gate_b2_exit_criteria_plan_2026-09-10.md`): (A) integrity her run + (B) diversity [≥5 scan_date; regime & direction her sınıf ≥%20; vol_regime 0/1/2 hepsi; alignment_ratio ≥5 unique; momentum_ratio ≥8; composite ≥20 unique] + (C) stability [3 ardışık PASS, stabil reconstruction, yeni missingness yok].

## 2. Metodoloji (dondurulmuş)

### 2.1 Data Freeze (§4)
B2 Exit PASS sonrası B3 dataset'i freeze edilir: symbols, scan_dates, observations, features, baseline inputs, outcomes, metadata. B3 başladıktan sonra dataset'e yeni observation eklenmez; yeni veri ayrı future-validation seti olarak tutulur.

### 2.1.1 — §4.1 EK (Meriç onaylı, 2026-09-11): Label integrity kontrolü
Freeze sırasında her observation için **`label_entry_basis == "eod_close"`** doğrulanır. Geçmiş bulgu: c2c_5d intraday/EOD karışıklığından kirlenmişti (EOD-only ile çözüldü, ρ=0,9829). EOD olmayan satırlar **hariç tutulur ve sayılır** (impute edilmez). Bu, c2c_5d'nin yeniden kirlenmesini önler.

### 2.2 Reconstruction (§5-7)
Stored production score vs reconstructed (persisted `score_input`/`score_component_breakdown`). Metrikler: n_total, n_reconstructable, n_exact_match, exact_match_rate, mean/median/max abs error, n_above_tolerance. **Tolerance önceden:** production'ın kendi 3dp/2dp rounding'i (1e-2) — sonuca göre değişmez. Reconstruction üç ayrı metrikle tutulur: `component_sum_exact`, `production_rounding_reconstruction`, `max_abs_diff` (Run-2 false-positive FAIL'i önler).
- EXACT (≈100%, yalnızca bilinen rounding) → PASS
- PARTIAL → bazı input/score üretilemiyor
- FAIL → baseline mantığı güvenilir üretilemiyor → predictive sonuç yorumlanmaz.

### 2.3 Missing data (§8)
NO IMPUTATION. Eksik → `missing` tutulur. Synthetic/historical reconstruction YOK.

### 2.4 Coverage (§9)
`valid / intended` + by date / regime / direction / vol_regime. Tek subgroup aşırı ağırlıklıysa belirtilir.

### 2.5 Compression / Tie audit (§10-11)
unique scores/ranks, tie rate, largest tie group, top-N tie frequency. Yüksek tie = "görünürde ranking" riski — ayırt edilir. (Bilinen %99,78 tie bulgusu yeniden ölçülür.)

### 2.6 Leakage audit (§12)
Her input için: feature/scan/market-close/outcome/data-availability timestamp ilişkisi. Future info kullanan input → `LEAKAGE_RISK`; çözülemezse ilgili predictive sonuç güvenilir sayılmaz.

### 2.7 Baseline (§13)
Production'daki mevcut scoring mantığı **değiştirilmez**. Weights/thresholds/feature-selection/formula/ranking/flag config optimize edilmez.

### 2.8 Random comparator (§14)
Aynı universe / dates / selection count / outcome horizon. Aynı evaluation framework içinde.

### 2.9 Metrics (§15-17)
- **Primary (dondurulmuş):** `Spearman(score, future_outcome)` — horizon önceden: `c2c_1d` (primary), `c2c_5d` (secondary, ayrı raporlanır).
- Secondary: top-N return/hit, bottom-N, long-short spread, mean/median return, rank IC. Primary sonradan değiştirilemez.

### 2.10 Temporal split + Walk-forward (§18-19)
Random train/test YOK. Zaman-sıralı (EARLY→LATER OOS). B4: rolling/expanding walk-forward, her pencere bağımsız raporlanır.

### 2.11 OOS success (§20) + Uncertainty (§21) + Multiple testing (§22)
OOS > random/chance minimum; tek window kazanması yeterli değil (direction/effect/window consistency + uncertainty + top-N). 95% CI / bootstrap / permutation. Multiple-testing riski kaydedilir; en-iyi-kombinasyon sonradan seçilemez.

### 2.12 Subgroup (§23) + Stability (§24)
regime/direction/vol_regime/score-tier — **secondary/exploratory**. Subgroup başarısı tek başına PASS değil. Stability: date/regime/direction/volatility boyunca.

### 2.13 Baseline vs Random (§25)
Random baseline'dan iyi çıkarsa → `BASELINE_SIGNAL_NOT_ESTABLISHED`.

### 2.14 GO / NO-GO / BLOCKED (§26-27)
- **GO:** B2 Exit PASS + reconstruction PASS + coverage yeterli + leakage yok + baseline > chance + OOS evidence + tek window'a bağımlı değil + stabil.
- **NO-GO:** baseline ≤ random / OOS sinyal yok / material leakage / reconstruct edilemez / compression yorumu geçersiz kılıyor.
- **BLOCKED:** B2 Exit sağlanmadı → `BLOCKED_BY_B2` (NO-GO değil).

### 2.15 Flag freeze + no feature search + no post-hoc (§28-30)
SQUEEZE/LOTTERY_FADE/OVERNIGHT_GAP/EDGAR_CATALYST/FRED_MACRO **FROZEN**. Yeni feature/flag/weight/threshold/formula YOK (ortaya çıkarsa `FUTURE_RESEARCH_IDEA`). Sonuç sonrası threshold/metric/horizon/subgroup/window/outlier değişikliği YOK (yalnızca önceden tanımlı data-quality exclusion).

### 2.16 Negative result policy (§31)
Baseline random'dan ayırt edilemezse → `BASELINE_SIGNAL_NOT_ESTABLISHED` açıkça raporlanır. Bu başarısızlık değil, araştırma sonucudur.

### 2.17 Evidence level (§32) + Flag geçiş kriteri (§33) + Incremental value (§34) + Economic (§35)
Baseline predictive support almadan Level 4'e çıkamaz. Flag-level predictive ancak `BASELINE_VALIDATION = GO` sonrası, one-at-a-time, `Baseline vs Baseline+Flag` aynı OOS'ta. Economic validation ayrı gate (cost/slippage/liquidity/sizing/risk/drawdown) — B3/B4 kapsamı dışında.

## 3. Tek bakışta sonuç tablosu (B3/B4 doldurulacak)

| Gate | Result |
|---|---|
| B2 Exit | **BLOCKED_BY_B2** (şu an: 24 obs / 1 gün) |
| Reconstruction | — (B3'te) |
| Data Coverage | — |
| Leakage | — |
| Compression | — |
| Baseline vs Random | — |
| OOS | — |
| Walk-Forward | — |
| Stability | — |
| **Baseline Validation** | **— (B2 Exit bekleniyor)** |

## 4. Ana hükümler (değişmez — §39)

- Baseline sağlam değilse flag predictive testi yapılmaz.
- Baseline random'dan ayırt edilemiyorsa flag'in incremental value'su yorumlanmaz.
- Behavioral evidence ≠ predictive evidence.
- Predictive evidence ≠ economic evidence.
- Test edilmemiş mekanizma reddedilmiş değildir.
- Yetersiz veri NO-GO değildir; BLOCKED'dır.
- Sonuçlara göre metodoloji değiştirilemez.

## 5. Metodolojik kilit (§38 — atlanamaz)

```
DATA SUFFICIENCY → RECONSTRUCTION → BASELINE INTEGRITY
→ OOS PREDICTIVE VALIDATION → ROBUSTNESS → GO/NO-GO
→ FLAG INCREMENTAL VALUE → ECONOMIC VALIDATION
```

---

## Governance
- Level B (metodoloji kaydı); Meriç onaylı 2026-09-11. Production/flag/.env/scheduler değiştirilmedi; deney/veri üretilmedi.
- `B3_BLOCKED_BY_B2` — B2 diversity dolmadan başlatılmaz. Bir sonraki adım: farklı gün/koşulda B2 Run 4 (Meriç onayıyla).
- Bu spec `reports/MASTER_RESEARCH_INVENTORY_2026-09-10.md`'ye tek satırla işlenir (bakım kuralı).
