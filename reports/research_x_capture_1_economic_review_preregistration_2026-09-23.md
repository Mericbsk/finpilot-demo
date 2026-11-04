# RESEARCH-X / RX-CAPTURE-1-ECON — Economic & Robustness Review (Pre-Registration Draft)

**Research ID:** RX-CAPTURE-1-ECON
**Version:** v0.3-LOCKED
**Date:** 2026-09-23
**Research Level:** B (economic/robustness evaluation of a CAPTURE_SUPPORTED result)
**Status:** APPROVED / LOCKED — Meriç approval 2026-09-23. Estimand audit PASS.
  This is a protocol lock, NOT a judgment on B1's outcome. Locked items cannot
  change during runner implementation; any change = protocol deviation / new
  research decision.
**Production Impact:** NONE
**Parent:** RX-CAPTURE-1 (CLOSED/VERIFIED) — this is a NEW Level B line, not a reopening.
**H4:** FROZEN / UNTOUCHED

---

## 0. SCOPE — bu bir Level B ekonomik/robustness değerlendirmesidir, production kararı değil

RX-CAPTURE-1'de E1 +3% ve +5% sabit-hedef çıkışlar kilitli tarihsel kohortta
maliyet-sonrası pozitif medyan capture üretti (CAPTURE_SUPPORTED, bağımsız
doğrulama PASS). Bu hat şu soruyu sorar:

> **CAPTURE_SUPPORTED bulgusu, gerçekçi maliyet/likidite/yürütme ve temporal
> sağlamlık altında ekonomik ve operasyonel olarak uygulanabilirliği test etmeye
> değer mi?**

Bu hat şu soruyu SORMAZ ve cevaplamaz:

> "+3/+5% production'da kullanılmalı mı?" — bu ayrı ve daha sonraki bir Level B/C
> karardır.

**Do-not-infer (kilitli):** `CAPTURE_SUPPORTED ≠ production approval`;
`VERIFICATION_PASS ≠ strategy approval`. Bu hat production çıkış kuralı önermez.

---

## 1. Araştırma sorusu

> Önceden kilitlenmiş E1 +3%/+5% çıkış adayları, (a) gerçekçi maliyet/slippage
> senaryoları, (b) temporal robustness (yeni/ek dönem), ve (c) likidite/kapasite
> kısıtları altında pozitif net capture'ı koruyor mu?

Secondary: E1_t3'ün medyan dejenerasyonu ve E1_t5'in late-period zayıflaması
(1.556→0.117) daha geniş maliyet/zaman koşullarında nasıl davranıyor?

## 2. Neden şimdi / mevcut kanıt
- E1_t3: medyan net +2.45pp (0.55%), stress +2.0pp (1.00%); hit %61.5; medyan dejenere.
- E1_t5: medyan net +1.136pp, stress +0.686pp; hit %42.9; dejenere değil; early 1.556 / late 0.117.
- Bağımsız doğrulama VERIFICATION_PASS. Determinism byte-stabil.

## 3. Bilinen eksiklikler (audit'ten; bunlar bu hattın test ettiği sınırlar)
- Spread/slippage gözlemi %0 (veri borcu — CRITICAL).
- Tek tarihsel pencere (54 gün, 2026-05→08); OOS kapalı.
- Likidite/ADV/kapasite tarihsel verisi yok.
- Corporate-action / survivorship sınırları.

## 4. Tasarlanan ölçüm eksenleri (DRAFT — kilitlenecek)
1. **Maliyet sağlamlığı:** net capture'ı bir dizi maliyet seviyesinde (örn. 0.25%→2.0%)
   yeniden hesapla; pozitifliğin hangi maliyet eşiğinde kırıldığını ölç (breakeven cost).
   NOT: bu yeni bir sinyal arama değil; kilitli E1 parametreleriyle yalnızca maliyet
   duyarlılığıdır.
2. **Temporal robustness:** mevcut pencerede alt-dönem dayanıklılığı + (varsa) yeni
   birikmiş veri üzerinde replikasyon. E1_t5'in zayıflamasını ayrıca incele.
3. **Likidite/kapasite proxy:** mevcut veriyle mümkün olan en iyi proxy (örn.
   fiyat×hacim) ile capture'ın likidite koşullu davranışı; veri yoksa `NOT_MEASURABLE`
   raporla, impute etme.
4. **Kuyruk/tail:** medyan dejenere olduğunda (E1_t3) mean + dağılım + big-loss
   davranışını ayrı raporla.

## 5. Estimand / ambiguity — EXACT MATHEMATICAL DEFINITIONS (locked at lock)

NS-1 + RX-CAPTURE-1 dersleri gereği her eksen için tek matematiksel tanım kilitli.

### 5.1 Notasyon
- `i` = valid (non-ambiguous) gözlem; entry `E_i` = export `price` (T0=scan_date).
- `G_i` = gross exit return (RX-CAPTURE-1 kilitli E1 kuralları, değişmez):
  `G_i = (exit_price_i - E_i)/E_i × 100`.
- `c` = varsayımsal round-trip maliyet (yüzde puanı), grid `C = {0.25,...,2.00}`.
- **Net capture:** `NC_i(c) = G_i - c`.
- **Median net capture at cost c:** `M(c) = Median({ NC_i(c) })`.
- `breakeven`: en küçük `c* ∈ C` için `M(c*) ≤ 0`. `M(c)` grid üzerinde sıfırı
  kesmiyorsa `breakeven = BETWEEN_GRID_POINTS` (interpolation YOK).

### 5.2 Primary estimand #1 — cost robustness
`breakeven_cost(family)` for family ∈ {E1+3%, E1+5%}: the locked definition above.
Report `M(c)` at every `c ∈ C`, plus gross reference `M(0)` (0.00 yalnız referans).
Verdict kapısı (§7.5): family "survives %1.00" iff `M(1.00) > 0`.

### 5.3 Primary estimand #2 — temporal sign stability
`early`/`late` = kilitli 40/20/40 split (RX-CAPTURE-1). For each period P ∈
{early, late}: `M_P(0.55)` and `M_P(1.00)`. **Sign consistency** :=
`sign(M_early(c)) == sign(M_late(c))` at both c ∈ {0.55, 1.00}. Magnitude
`|M_early - M_late|` always reported; E1_t5 weakening (1.556→0.117) re-reported.

### 5.4 Liquidity proxy estimand
`dollar_volume_proxy_i = price_i × volume_i`. Stratify valid observations into
scan_date-internal proxy quintiles; report `M(0.55)` per quintile. Result label
`LIQUIDITY_PROXY_ONLY`. If proxy unavailable for a cohort → `NOT_MEASURABLE`;
no imputation.

### 5.5 Tail / distribution
For each E1 family report median, mean, hit rate (share NC_i>0), P25, P75,
big-loss rate (`NC_i ≤ -10pp`), upper-tail contribution, and day concentration
(single-day net contribution share; `>25%` → CONCENTRATION_WARNING).

### 5.6 New-data temporal replication — eligibility gate (exact)
New-data replication runs ONLY IF, at lock time, an input artifact exists with:
(a) distinct scan_date ≥ 10 on `2026-08-06 → latest`; (b) ≥ 500 valid
observations in that window; (c) its own SHA-256 recorded; (d) same
selection/execution definitions. Else `TEMPORAL_REPLICATION = NOT_AVAILABLE`
(not FAIL / not NOT_SUPPORTED). Old cohort is never modified; old+new never
merged into a single retrospective result.

### 5.7 Ambiguity / missing
Same-day ambiguity: EXCLUDE (unchanged from RX-CAPTURE-1). Missing
cost/liquidity/path data → `NOT_MEASURABLE` / `unavailable`; never imputed.

## 6. Governance sınırları
- H4 FROZEN; RX-CAPTURE-1 CLOSED kalır; bu hat onları yeniden açmaz.
- Production impact NONE. Hiçbir çıkış kuralı üretime alınmaz.
- Herhangi bir shadow/paper/live geçiş ayrı Level C insan kararıdır.
- Bu DRAFT lock'lanmadan runner yazılmaz.

## 7. Open Decisions — Meriç Defaults (locked at review)

### 7.1 Maliyet ekseni (LOCKED DEFAULT)
Primary hypothetical round-trip cost sensitivity grid:

```
0.25% 0.50% 0.75% 1.00% 1.25% 1.50% 1.75% 2.00%
```
`0.00%` yalnızca gross/net ayrımını görünür kılan referans noktası olarak
raporlanabilir; ekonomik verdict için kullanılmaz. **Breakeven cost** = ilgili E1
ailesinin net capture medyanının sıfıra indiği maliyet eşiği. Sıfır kesişimi grid
üzerinde doğrudan gözlenmiyorsa eşik interpolation ile uydurulmaz;
`BETWEEN_GRID_POINTS` raporlanır.

`net_capture_pct = gross_exit_return_pct - assumed_round_trip_cost_pct`. Bu
maliyetler **gerçek gözlemlenmiş execution cost DEĞİLDİR**. Dolayısıyla
`ASSUMED_COST_SENSITIVITY ≠ OBSERVED_TRANSACTION_COST` ve
`BREAKEVEN_ESTIMATE ≠ REALIZED_EXECUTION_COST`. **%1.00 eşiği piyasanın gerçekçi
maliyeti olarak seçilmemiştir; önceden belirlenmiş ekonomik robustness test
seviyesidir (governance stress gate).**

### 7.2 Temporal robustness (LOCKED DEFAULT)
RX-CAPTURE-1'in mevcut bölünmesi korunur: early 40% / middle 20% (buffer) / late
40%; aynı cohort, aynı locked E1 tanımları. Primary criterion: early/late
net-capture medyan işaretleri raporlanır; sign consistency robustness ölçütü.
Magnitude difference da raporlanır. E1 +5%'in önceden gözlenen zayıflaması
(early +1.556pp / late +0.117pp) yeniden raporlanır ve gizlenmez.

#### 7.2.1 Yeni veri temporal replication
Lock anında mevcut veri RX-CAPTURE-1 son tarihinden (`2026-08-05`) sonra yeterli
yeni gözlem sağlıyorsa `2026-08-06 → latest available` ayrı bir temporal
replication olarak değerlendirilebilir. Ancak: yeni veri ayrı input artifact olarak
SHA-256 ile kilitlenir; mevcut cohort değiştirilmez; eski+yeni sonuçlar
tek retrospective sonuca birleştirilmez; yeni dönem ayrı raporlanır;
selection/execution tanımları değişmez; veri yetersizse replication yapılmaz.
Yeterli değilse `TEMPORAL_REPLICATION = NOT_AVAILABLE` (FAIL/NOT_SUPPORTED
değildir). Locked OOS yeniden açılmaz; RX-CAPTURE-1 değiştirilmez.

### 7.3 Likidite / kapasite proxy (LOCKED DEFAULT)
Veri izin verdiği ölçüde `dollar_volume_proxy = price × volume` kullanılabilir.
Amaç: capture'ın düşük hacimli gözlemlerde yoğunlaşıp yoğunlaşmadığını incelemek.
Ancak `price × volume ≠ bid-ask spread ≠ realized slippage ≠ market impact ≠
executable capacity`. Sonuç etiketi `LIQUIDITY_PROXY_ONLY`. Gerçek
spread/slippage yokluğunda `OBSERVED_LIQUIDITY_COST = NOT_MEASURABLE` ve
`EXECUTION_CAPACITY = NOT_MEASURABLE` korunur. Proxy bulunamayan cohort'ta
imputation yapılmaz.

### 7.4 Tail / distribution robustness (LOCKED DEFAULT)
E1 +3%'ün median-degeneration özelliği nedeniyle median tek başına yeterli
sayılmaz. Her E1 ailesi için raporlanır: median, mean, hit rate, P25, P75,
lower-tail/big-loss rate, upper-tail contribution, day concentration. Pozitif
medyan + pozitif toplam etkinin az gün/gözlemden gelmesi açıkça işaretlenir.
RX-CAPTURE-1 concentration kuralı korunur: `>25% net contribution from one day →
CONCENTRATION_WARNING` (otomatik NOT_SUPPORTED değil, ama robustness yorumunun
parçası).

### 7.5 Economic / Robustness verdict criteria (LOCKED DEFAULT)
Bu hat production approval VERMEZ. Primary B1 verdict yalnızca üç sınıftan biri:

```
FURTHER_VALIDATION_SUPPORTED
FURTHER_VALIDATION_NOT_SUPPORTED
INCONCLUSIVE
```

**FURTHER_VALIDATION_SUPPORTED** ancak tamamı sağlanırsa: (1) en az bir locked E1
ailesi (+3%/+5%) için %1.00 varsayımsal maliyette pozitif median net capture
korunur; (2) sonuç yalnızca %0.00-0.50 gibi düşük maliyetlerde pozitif kalmaz;
(3) early/late aynı yönde kalır veya ters yön açıkça ayrı robustness limitation
olarak sınıflandırılır; (4) sonuç tamamen tekil gün/küçük tail tarafından
açıklanmaz; (5) liquidity proxy yapılmış veya `NOT_MEASURABLE` açıkça raporlanmış.
Bu verdict YALNIZCA "further validation is justified" der; şunları İFADE ETMEZ:
`PRODUCTION_APPROVED / TRADING_RULE_APPROVED / ECONOMICALLY_PROVEN /
EXECUTION_FEASIBLE / CAPACITY_PROVEN`.

**FURTHER_VALIDATION_NOT_SUPPORTED:** (a) E1 +3% ve +5% tamamı %1.00 varsayımsal
maliyette negatifleşirse; (b) temporal finding sistematik ve tutarlı tersine
dönerse; (c) sonuçların büyük bölümü concentration/tail artifact'ıysa; (d)
liquidity proxy sonuçların yalnızca aşırı düşük hacimli gözlemlerden geldiğine
güçlü descriptive evidence verirse. Bu "strategy is disproven" DEMEZ; mevcut
evidence'ın ileri validation için yeterli destek sağlamadığını söyler.

**INCONCLUSIVE:** yetersiz temporal veri, yetersiz liquidity, effective-N ciddi
düşüş, primary metrikler ciddi çelişki, veya breakeven grid yorumlanamazsa.
`UNKNOWN ≠ NOT_SUPPORTED` korunur.

### 7.6 Production boundary (LOCKED)
B1'in hiçbir sonucu otomatik tetiklemez: production activation, shadow, paper,
live, exit-rule deployment, parameter/scanner/score/ranking/feature change.
`FURTHER_VALIDATION_SUPPORTED` olsa bile sonraki adım ayrı Level-B/C governance
kararıdır. **Production Impact remains NONE.**

---

**Status:** DRAFT — Level B proposal. Awaiting Meriç review. No runner, no execution,
no production change.
