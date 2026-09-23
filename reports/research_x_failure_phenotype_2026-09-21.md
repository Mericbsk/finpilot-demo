# RESEARCH-X — Loser / Failure Phenotype Audit (READ-ONLY, DESCRIPTIVE)

**Tarih:** 2026-09-21 · **Level:** A (read-only; production/veri değiştirilmedi)
**Tetikleyici:** Meriç — "hangisinin düşeceğini bilmek / ters açı / modelin düşmanları"
**Tip:** **PHASE 1 — Phenotype discovery.** Yeni skor YOK, model YOK, threshold optimizasyonu YOK, feature mining to "explain" YOK. Descriptive.
**Artifact:** `data/backtest_out/research_x_failure_phenotype_2026-09-21.json`

---

## 1. Amaç

FinPilot'ın **hangi koşullarda yanıldığını** anatomik olarak çıkarmak. "Hangi hisse yükselecek?" yerine: **"High-score verdiği halde düşenler neye benziyor? Low-score iken büyük yükselenler neye benziyor?"**

Cohort tanımı (point-in-time safe): score median'a göre scan_date içinde HIGH/LOW; outcome c2c_5d.

## 2. Cohort dağılımı (34.762 satır)

| Cohort | n | Anlam |
|---|---:|---|
| HS_WINNER | 8.574 | yüksek skor, yükseldi |
| LS_LOSER | 8.781 | düşük skor, düştü |
| HS_NORMAL_LOSER | 7.273 | yüksek skor, düştü (küçük) |
| LS_NORMAL_WINNER | 6.644 | düşük skor, yükseldi (küçük) |
| **HS_BIG_LOSER** | **1.831** | **yüksek skor ama ≤−10%** ← modelin düşmanı |
| **LS_BIG_WINNER** | **1.659** | **düşük skor ama ≥+10%** ← modelin kör noktası |

## 3. En kritik bulgu — INVERTED PATTERN OBSERVED — descriptive

| Metrik | High-score | Low-score |
|---|---:|---:|
| Big-loser (≤−10%) rate | %10,4 | %11,1 |
| **Big-winner (≥+10%) rate** | **%7,3** | **%9,7** |

> **Düşük skorlu hisseler, yüksek skorlu hisselerden DAHA SIK büyük kazanan üretiyor (%9,7 vs %7,3)** — ve big-loser oranı neredeyse aynı. Bu, daha önceki "high score → daha düşük getiri / overextension" hipoteziyle **tutarlı**: skor yukarı çıktıkça upside yakalanma oranı **düşüyor**.

**Bu yalnızca descriptive bir gözlem** — bir pre-registered hypothesis sonucu değil. Confidence interval, effect significance, score-outcome monotonicity, chronological replication ve future-OOS validation henüz yok. Bu nedenle production ranking'in tersine eğimli olduğu söylenemez; gözlem yalnızca önceden kilitlenmiş bir Phase 2 testi hak ediyor.

## 4. Failure phenotype (HS_BIG_LOSER vs HS_WINNER)

| Feature | HS_BIG_LOSER median | HS_WINNER median | Baseline median |
|---|---:|---:|---:|
| **atr_pct_real** | **7,92** | 3,72 | 4,76 |
| **dist_52w_high** | **0,76** | 0,89 | 0,74 |
| **lottery_factor** | **0,59** | 0,31 | 0,42 |
| **price** | **21,7** | 55,9 | 27,5 |
| rvol | 0,87 | 0,89 | 0,83 |
| vol_regime | 2,0 | 2,0 | 2,0 |

**High-score büyük-kaybedenler** (kazanan high-score'lara kıyasla): **daha yüksek volatilite (ATR 7,9 vs 3,7), 52-hf zirvesinden daha uzak (0,76 vs 0,89), daha yüksek lottery (0,59 vs 0,31), daha düşük fiyat (21,7 vs 55,9).**

→ **Descriptive hipotez:** High-score'un *içinde* düşenler, **yüksek-volatilite + yüksek-lottery + zirveden-uzak + düşük-fiyat** profiline sahip. Yani skor yüksek olsa bile, bu alt-profil failure'a işaret ediyor olabilir. **(HYPOTHESIS — test edilmedi.)**

## 5. Blind-spot phenotype (LS_BIG_WINNER vs LS_LOSER)

| Feature | LS_BIG_WINNER median | LS_LOSER median |
|---|---:|---:|
| dist_52w_high | 0,45 | 0,51 |
| price | 5,72 | 7,55 |
| lottery_factor | 0,55 | 0,51 |
| atr_pct_real | 7,40 | 6,21 |

Düşük-skor büyük-kazananlar da yüksek-volatilite/düşük-fiyat. **Model bunları düşük skorluyor ama bir kısmı çok yükseliyor** — modelin kör noktası low-price/high-vol bölgesinde.

## 6. Kümelenme (failure clustering)

- **Big-loser top-3 gün payı: %19,2** — büyük kaybedenler belirli kötü günlere kümeleniyor (gün-bağımlı risk).
- **vol_regime=2'de big-loser oranı %13,6** vs vol_regime=0'da %1,4 → **yüksek-volatilite rejiminde failure yoğunlaşıyor** (~10× fark).
- Regime True/False big-loser oranı benzer (%10,4/%11,1) — regime tek başına ayırmıyor.

## 7. Neyi KANITLAMADIK / sınırlar

- Bunlar **descriptive**; hiçbiri pre-registered hypothesis testi değil.
- "Yüksek vol + lottery → düşer" bir **HYPOTHESIS**; OOS/matched-control test edilmedi.
- Median/IQR farkları çakışan dağılımlar olabilir; effect size / CI hesaplanmadı.
- score split median'da → "high score" göreli; production threshold değil.
- 5 score-quantile boyunca monotonicity, effect significance, chronological replication ve future-OOS validation ölçülmedi.

## 8. Önerilen pre-registered hipotezler (gelecek testler — ŞİMDİ test edilmedi)

| ID | Hipotez | Durum |
|---|---|---|
| RX-H1 | High-score içinde, yüksek ATR + yüksek lottery + `dist_52w_high` alt-profil big-loser olasılığını anlamlı artırır | HYPOTHESIS (alan adı düzeltildi; test edilmedi) |
| RX-H2a | 5 önceden tanımlı eş-frekanslı score quantile'ında daha yüksek score, daha düşük `c2c_5d` median ile monoton ilişkilidir | **PREREGISTERED; NOT RUN** |
| RX-H2b | Daha yüksek score quantile'ı, `c2c_5d >= +10%` big-winner oranını düşürür | **PREREGISTERED; NOT RUN** |
| RX-H2c | Score quantile seviyesi, `c2c_5d <= -10%` big-loser oranını nasıl etkilediğini gösterir; yön önceden varsayılmaz | **PREREGISTERED SECONDARY; NOT RUN** |
| RX-H2d | H2a/H2b/H2c birlikte production ranking'in tersine eğimli olduğu iddiasını taşıyacak kadar güçlüdür | **DEFERRED; H2a-c öncesi test edilmeyecek** |
| RX-H3 | Failure'lar vol_regime=2'de ve belirli kötü scan günlerinde kümelenir | HYPOTHESIS |

## 9. Sonraki adım (Meriç kararı)

- **PHASE 2:** Önce RX-H2a/H2b/H2c preregistration'ını uygula: 5 score quantile, chronological walk-forward ve scan-date matched-control. H2d bu sonuçlar ve tie-resolution raporu olmadan değerlendirilmeyecek.
- Mevcut Mayıs–31 Temmuz veri seti true future-OOS değildir; sonuçlar bu adlandırmayla raporlanmayacak. Score ve production formülü freeze kalacak, yeniden fit edilmeyecek.
- **Dikkat:** Bu bulgular **düşüşü önceden bilmek** için umut verici AMA descriptive. Production/short sinyali ÜRETMEZ.

## Governance
- Read-only; production/veri/flag değiştirilmedi. Yeni skor/model/eşik ÜRETİLMEDİ. Descriptive phenotype; hipotezler açıkça HYPOTHESIS olarak işaretlendi (conclusion değil). Negatif/karışık bulgular raporlandı.
