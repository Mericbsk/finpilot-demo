# GATE B2 — Exit Criteria & Run 4-N Plan (PRE-REGISTERED)

**Tarih:** 2026-09-10 · **Level:** B (observability/measurement) · **Mode:** MANUAL
**Prensip:** MEASURE FIRST. CHANGE NOTHING. Predictive test YOK. `.env`/scheduler YOK.
**Amaç:** "Birkaç run daha yapalım" belirsizliği yerine, B2'yi **hangi koşulda kapatacağımızı önceden** tanımlamak. Keyfi sample-size threshold'u YOK (§25) — diversity/stability kriterleri var.

---

## 1. Mevcut birikim (2026-09-10 audit)

| Metrik | Değer |
|---|---|
| Runs | 3 (B1 + B2 Run2 + Run3) |
| Total observations | 24 |
| Unique scan_date | **1** (2026-09-09) ⚠️ |
| Unique symbols | 8 |
| regime | True 21 / False 3 |
| direction | True 18 / False 6 |
| vol_regime | 1:12 / 2:12 (0 yok) |
| filter_score | 1:18 / 0:4 / 2:2 |
| alignment_ratio | 2 unique (0.50, 1.00) |
| momentum_ratio | 6 unique (0–1) |
| composite_score | 12 unique (30–73) |
| score | 2 unique (1, 2) |
| distinct flag-state snapshot | 1 (hepsi OFF) |

**Gap'ler (B3 için yeterli çeşitlilik DEĞİL):**
- Tek gün → **time/regime diversity yok**
- alignment_ratio sadece 2 değer → continuous input'un gerçek varyansı bilinmiyor
- vol_regime=0 (low-vol) hiç yok
- regime/direction baskın "True" → bear/False tarafı zayıf
- Tek flag-state → flag değişimi gözlenmedi

## 2. PRE-REGISTERED B2 EXIT CRITERIA

B2 ancak **aşağıdakilerin TÜMÜ** sağlanınca "DATA READY" der (§30). Keyfi sayı değil, **stability + diversity** kriterleri:

### A. Integrity (her run'da zorunlu — mevcut B2 protokolü)
- record coverage %100 (veya unavailable açıklamalı)
- field coverage %100, null açıklamalı
- raw fidelity 0 failure
- score/rank non-regression delta = 0
- reconstruction exact (rounding-toleranced)
- duplicate / overwrite / synthetic / imputation = 0

### B. Diversity (B3 reconstruction'ın anlamlı olması için)
| Boyut | Minimum hedef | Şu an |
|---|---|---|
| Distinct scan_date | **≥ 5 farklı gün** | 1 ❌ |
| regime True/False | her ikisi ≥ %20 | False %12.5 ❌ |
| direction True/False | her ikisi ≥ %20 | False %25 ⚠️ |
| vol_regime 0/1/2 | her üçü de gözlenmiş | 0 yok ❌ |
| alignment_ratio unique | **≥ 5 distinct değer** | 2 ❌ |
| momentum_ratio unique | ≥ 8 distinct değer | 6 ⚠️ |
| composite_score unique | ≥ 20 distinct | 12 ⚠️ |

### C. Stability
- Son 3 run üst üste integrity PASS
- Reconstruction exact rate sabit (run-to-run drift yok)
- Missingness pattern stabil (yeni run'larda yeni missing türü çıkmıyor)

**B2 EXIT ≠ "yeterince veri var" (sezgisel). B2 EXIT = A+B+C sağlandı.**

## 3. RUN 4-N PLANI (her run ayrı onay)

```
Run N:
  1. READ-ONLY pre-run audit (§32) — git/.env/version/prior-hash
  2. Meriç onayı (her run)
  3. process-local FINPILOT_INSTRUMENT_BASELINE=1
  4. evaluate_symbols_parallel(onaylı sembol seti) — production path
  5. append-only persist (YENI run_id; eski artifact'lara dokunma)
  6. flag OFF'a dön (.env değişmez)
  7. §33 18-maddelik post-run integrity audit
  8. Bu planın exit kriterlerine karşı durum raporu
```

### Symbol seti kuralı (§09)
- Mevcut 8 likit sembol (AAPL MSFT NVDA TSLA AMZN GOOGL META AMD) onaylı.
- **Diversity için genişletme** (ör. farklı vol_regime/price bandı yakalamak için 20 sembole) **ayrı onay** gerektirir — kendi başıma genişletmem.

### Zamanlama kuralı
- Aynı gün tekrar run **time diversity katmaz** (aynı scan_date). Farklı günlerde run daha değerli.
- Market koşulu değişkenken (vol_regime=0 görülen bir gün) run, vol_regime=0 coverage'ı doldurur.

## 3b. KARAR (2026-09-10, Meriç) — Run 4 bugün ÇALIŞTIRILMAYACAK

**Karar:** WAIT → farklı gün/koşul. Run 4 bugün **yapılmayacak**.

**Gerekçe:** B2'nin amacı artık "kaç kayıt" değil, "production state'i yeterince farklı koşulda gözlemledik mi". Mevcut 24 observation **tek scan_date (2026-09-09)** ve dar state aralığında. Aynı gün 8→16→24 obs, aynı piyasa koşulunu tekrar örnekler → B3'e marjinal katkısı düşük.

**Run 4 bugün yapılsaydı:** integrity/append-only/provenance/reconstruction'a yeni kanıt verirdi AMA **state diversity'ye neredeyse hiç katkısı olmazdı** → B2 exit'e anlamlı yaklaştırmazdı. Araştırma kaynağını korumak için beklemek daha güçlü seçim.

**Beklenen değerli koşullar (üretmek için sistem DEĞİŞTİRİLMEZ; piyasa doğal verdiğinde yakalanır):**
- `vol_regime = 0` (low-vol)
- `regime = False` (bear)
- `direction = False`
- daha farklı `alignment_ratio` ve composite dağılımı

**Symbol seti:** 8 sembol **sabit** kalır (AAPL MSFT NVDA TSLA AMZN GOOGL META AMD). Gerekçe: değişen şey sembol evreni değil, **zaman/piyasa koşulu** → diversity'nin kaynağı temiz izlenir. **20'ye genişletme DONDURULDU** — ayrı Level B karar; ancak "8 symbols × farklı günler" yetersiz kalırsa tekrar gündeme gelir.

**Sonraki adım:** Birkaç farklı gün sonrası diversity fotoğrafını tekrar çıkar → "production state'ler B3 reconstruction testini anlamlı sınayacak kadar çeşitli mi?" → evetse GATE B3 (ayrı onay), değilse B2 devam.

## 3c. KARAR (2026-09-21, Meriç) — Run 4 yapıldı; 8 sembol FROZEN; Run 5 kuralı

**Run 4 sonucu (2026-09-21):** PASS (reports/gate_b2_run4_2026_09_21.md). 4 run / 32 obs. **B2 overall = NOT YET (FAIL değil)** — integrity/reproducibility/fidelity/reconstruction/append-only hepsi PASS; **time/regime/volatility diversity INSUFFICIENT.**

**Meriç kilitleri (bu kararla):**
- **8 sembol FROZEN** (genişletme YOK bu aşamada — deney koşullarını değiştirir).
- **Run 5 yalnızca gerçekten yeni işlem gününde** — "sıradaki gün" diye değil. Ön-koşul: yeni `scan_date`.
- **vol_regime=0 / regime=False ÜRETİLMEZ** — doğal gelirse kaydedilir; gelmezse "yetersiz diversity" sonucu korunur (üretmek yasak).
- **8→20 genişletme ancak:** birkaç yeni işlem günü sonrası `scan_date ≥5` ama regime/vol_regime hâlâ yetersizse → "Sabit 8 sembol mü diversity bottleneck?" **ayrı Level-B deney** olarak açılır. B2'nin devamı olarak DEĞİL — örneklem tasarımını değiştirmek B2'nin neyi ölçtüğünü belirsizleştirir.
- **Instrumentation / Production / Predictive: FROZEN.**

**İki hat temiz ayrı:** Attention → future-OOS bekleniyor (ANS-3 frozen). Scoring → aynı deney koşullarında diversity toplamaya devam.

## 4. B2'den B3'e geçiş

- B2 "DATA READY" (A+B+C) → **GATE B3 ayrı onay** ile başlar.
- B3'te reconstruction üç ayrı metrikle tutulur (sizin öneriniz): `component_sum_exact` + `production-rounding reconstruction` + `max absolute difference` → Run 2 tipi false-positive FAIL önlenir.
- B4 (Predictive Validation) ayrı gate; random control dahil.

## 5. Bu dosyanın sınırları
- Bu bir **plan/exit-kriteri** dokümanı; yeni deney/veri üretmedi.
- Hiçbir production/flag/scheduler/.env değişikliği yapmadı.
- Predictive conclusion ÜRETMEDİ.

## Governance
- Level B; read-only audit + plan. Pre-registered exit criteria.
- Her run ayrı kullanıcı onayı. `.env`/scheduler bu planın otomatik sonucu DEĞİL.
