# FinPilot Research — Skor Gerçekte Neyi Ölçüyor? (Bilimsel Rapor)

Sürüm: 1.0 · Tarih: 2026-07-31 · Level A (araştırma; canlıya dokunmaz)
Ekip rolü: kantitatif araştırma · Yöntem: hipotez → deney → istatistik → strateji
Veri: gölge defteri 15–30 Tem 2026 · **91 olgun seçilen sinyal + 218 kontrol (toplam 309)** · price_cache/EOD
Araçlar: numpy, pandas (scipy/sklearn YOK → ağır ML dürüstçe ertelendi, gerekçe §7)

> **Kritik bilimsel kısıt (baştan):** Örneklem küçük (n=91 seçilen) ve **tek pencere / tek rejim**
> (yumuşak-choppy Temmuz). Bu, yönlü bulgular + geniş güven aralıkları verir; ama ML model kurmaya,
> rejim-kümelemeye, deflated-Sharpe/CPCV'ye YETMEZ. Overfitting yasak (promptun kuralı). Bu yüzden bazı
> bölümler "kanıtlandı", bazıları "yetersiz veri — ertelendi" olarak işaretlidir.

---

## 0.0 — NİHAİ DÜZELTME (ayı-rejim testi + metrik denetimi) — §0.1/§0.2'deki "ATR edge"i GEÇERSİZ KILAR

Ayı-rejim testi, **`resolved_pct_t5` metriğinin bozuk olduğunu** ortaya çıkardı ve tüm "ATR edge" sonucunu çürüttü.

**Kanıt 1 — Temiz, geniş, kapanış-kapanış, piyasa-nötr kesit (price_cache, 17.331 gözlem, 219 sembol, 2024-09→2026-07):**
ATR rank-IC **bull −0.063 / bear −0.021** (ikisi de ~sıfır-negatif). ATR üst-%10 ham 5g medyan **bull −1.62 / bear −1.86**.
→ ATR edge **hiçbir rejimde yok** (enriched'deki +0.35 replike olmadı).

**Kanıt 2 — Metrik denetimi (599 enriched satırı temiz yeniden hesaplandı):**
| Ölçüm | Medyan | ATR ile rank-IC |
|---|--:|--:|
| `resolved_pct_t5` (enriched) | 3.34 | **+0.404** |
| temiz **kapanış-kapanış** 5g | **0.16** | **+0.011 (SIFIR)** |
| temiz **MFE** (en-iyi-durum) | 3.79 | +0.454 |
`resolved` ↔ MFE korelasyon **0.74** (kapanış-kapanış'a 0.53). → **`resolved_pct_t5` gerçekleşen getiri değil, en-iyi-durum (MFE/tepe) ölçüyor.**

**Teşhis:** Yüksek-ATR isimler daha geniş aralıklı → tepe-excursion'ları mekanik olarak yüksek. "ATR +0.35 edge",
bu **best-case-yanlı metrikten** doğan bir **artefakt**. Gerçekleşen (tradeable) kapanış-kapanış getiride ATR'nin
gücü **sıfır**. Yani §0.1/§0.2'deki "ATR = güçlü edge" **REDDEDİLİR.**

**P0 METODOLOJİ BULGUSU:** `resolved_pct_t5` MFE-yanlı. Bu metriğe dayanan **TÜM geçmiş backtest sonuçları**
(aylar önceki "ATR sağlam edge" dahil) **potansiyeli ölçmüş, yakalananı değil** — hepsi yeniden değerlendirilmeli.

**NİHAİ DURUM:** Şu an **doğrulanmış, tradeable bir edge YOK** — ne skorda (IC≈0), ne ATR'de (temiz IC≈0, ayıda negatif).
Bu deflasyonist ama değerli: araştırma, sahte bir edge'i (ATR-ağırlıklı sıralama) canlıya almaktan **kurtardı**.

**Yön:** (1) sonuç metriğini her yerde **gerçekleşen kapanış-kapanış veya gerçekçi-execution triple-barrier**'a
çevir; (2) tüm edge araştırmasını düzeltilmiş metrikle **tekrar** koş; (3) dürüst tradeable edge küçük/sıfırsa
değer önermesini buna göre konumlandır (ör. eğitim/FinSense — aws impact hattı).

---

## 0.0.1 — EDGE TEKRAR-KOŞU (düzeltilmiş metrik, tüm veri n=53.754) — skor testi dahil

`edge_recheck.py` her (symbol, scan_date) için price_cache'ten **dürüst** sonuç üretti:
gerçekleşen kapanış-kapanış (`c2c5`), cost'lu (`c2c5_net`), triple-barrier TP2/SL1 cost'lu (`tb_ret`), ve referans MFE.

**Metrik medyanları:** c2c5 **+0.48** · **c2c5_net −0.02** (cost sonrası ≈ başabaş) · **tb_ret −0.95** (negatif) · mfe5 +4.24.

**rank-IC — skorlar/ATR, hedef metriğe göre:**

| Özellik | c2c5 (dürüst) | tb_ret (barrier,net) | mfe5 (best-case/BOZUK) |
|---|--:|--:|--:|
| score | −0.018 | −0.019 | +0.084 |
| **composite_score** | **−0.028** | −0.021 | −0.117 |
| **finpilot_score** | **+0.034** | +0.048 | −0.070 |
| **atr_pct** | **−0.020** | **−0.100** | **+0.496** |

**Kesin kanıt:** ATR IC **mfe5'te +0.50**, ama **dürüst c2c5'te −0.02.** → "ATR edge" **%100 MFE artefaktıydı.**
`resolved_pct_t5` = mfe5'i izliyordu.

**SKOR TESTİ (istenen — düzeltilmiş metrikle):**
- **composite_score: EDGE YOK / kırık** — dürüst IC −0.028 (tüm metriklerde ~0/negatif). Teyitli.
- **finpilot_score: ihmal edilebilir** — dürüst IC +0.034 (n=29.608'de sıfırdan farklı ama ekonomik olarak önemsiz),
  ve **rejimde kararsız**: bull +0.055 / bear −0.093 (işaret değiştiriyor).
- **atr_pct: dürüst getiride edge yok** (−0.02); triple-barrier'da **negatif** (−0.10, sıkı stop whipsaw'u); decile
  merdiveni monoton değil, **en yüksek ATR decile'ı EN KÖTÜ** (medyan −1.41).

**NİHAİ VERDİKT (tüm araştırma programının dürüst sonucu):**
> Düzeltilmiş, gerçekleşen, cost-sonrası getiride **hiçbir skor (composite/finpilot) ve ATR tradeable edge
> göstermiyor.** Önceki tüm "edge"ler `resolved_pct_t5`'in best-case (MFE) yanlılığından doğan artefaktlardı.
> Cost sonrası evren medyanı ≈ 0; triple-barrier negatif. **Şu an kanıtlanmış bir hisse-seçim alfası yok.**

**Stratejik sonuç:** (1) `resolved_pct_t5`'i her yerde gerçekleşen/triple-barrier ile değiştir (P0);
(2) tüm geçmiş "edge" iddialarını bu metrikle yeniden temelle; (3) değer önermesini "kazanan seçiyoruz"dan
**karar-destek / eğitim (FinSense, aws impact hattı)**'na kaydır — çünkü tradeable alfa kanıtı yok.

---

## 0.0.2 — KOMBİNATORYAL KRİTER ARAMASI (IS/OOS, dürüst metrik) — "bir kombo işe yarar mı?"

**İstek:** finpilot/composite içindeki kriterleri + eşikleri farklı kombinasyonlarla, tüm evrende dene.
**Disiplin:** dürüst `c2c5_net`; eşikler yalnız **IS**'ten (look-ahead yok); zaman-bölünmüş **IS (Eyl'25–14 May'26) / OOS (14 May–Tem'26)**; her kombo iki dönemde de bakılır.

- **Tek-değişkenli dürüst IC:** hepsi ~0; en belirginler NEGATİF (lottery −0.098, tier_score −0.084, overnight_gap −0.074, risk_reward −0.058). Pozitifler önemsiz (gap +0.029, rvol +0.025).
- **Kombo taraması (tek + 2-faktör eşik kuralları, n≥100 IS & ≥50 OOS → 74 kombo):**
  - **IS'te anlamlı pozitif (>0.3) kombo: 0/74.**
  - OOS'ta baseline'ı (+0.44) geçen: 32/74 ≈ **%43 (şans seviyesi).**
  - OOS "kazananları" (`atr>hi & risk_reward<lo` OOS +1.56 vb.) **hepsi IS'te NEGATİF** (−2.1…−3.1) → **IS/OOS tutarsız = gürültü**, gerçek edge değil.
  - Hiçbir kombo iki dönemde birden pozitif değil.

**Sonuç:** Mevcut kriter/faktör setinde, dürüst-metrikte, **stabil (IS+OOS tutarlı) hiçbir kombinasyon baseline'ı geçmiyor.**
Görünen OOS-kazananlar overfitting/şans; forward'da kalmaz. Daha çok kombinasyon denemek (3-4 faktör, ince eşik)
yalnız **daha çok yalancı-pozitif** üretir (faktörlerin dürüst IC'si ~0 iken kombinasyon bilgi yaratmaz).

- **Geniş ağırlık-optimizasyonu (4000 konfig — bileşen ekle/çıkar/ters-çevir/ağırlık değiştir, gün-içi z-skor, IS/OOS):**
  en iyi konfigin IS üst-decile getirisi yalnız **+0.15** (≈ düz); IS-en iyi 50 konfig OOS'ta baseline'ı **22/50 = %44** geçti (**şans seviyesi**). Hiçbir ağırlık/bileşen kombinasyonu IS/OOS-tutarlı edge üretmedi. → **Sıfır-IC faktörlerin ağırlıklı toplamı da sıfır-IC'dir.**

**Bunun anlamı:** Sorun eşik/kombinasyon/ağırlık ayarı değil — **girdi faktörlerinde tradeable bilgi yok.** İlerlemek için
recombination değil, **gerçekten YENİ bir faktör/veri** (ör. intraday mikroyapı, order-flow, alternatif veri) gerekir;
ya da değer önermesi alfa-dışına (karar-destek/eğitim) taşınır.

---

## 0. (SÜPERSEDED — §0.0 düzeltti) TÜM-VERİ — bu bölüm aşağıdaki 91-pencere sonucunu GEÇERSİZ KILAR

Kullanıcı uyarısı üzerine ("neden 91? tüm veriyle yap") analiz **tüm veriye** taşındı:
`data/backtest_out/full_universe_enriched.csv` — **53.859 satır, 66 gün, Eyl 2025 – Tem 2026, ÇOK REJİM,
`resolved_pct_t5` %100 dolu.** Sonuç, 91-sinyallik tek Temmuz penceresini **TERSİNE ÇEVİRDİ.** Bilimsel
dürüstlük gereği önceki "skor anti-prediktif / tükeniş ölçüyor" sonucu **REDDEDİLİR** — doğru sonuç budur.

**Doğru bulgular (rank-IC vs resolved_pct_t5; medyan tabanlı — uç değere bağışık, max +16866% var):**

| Bulgu | Kanıt | Yorum |
|---|---|---|
| **ATR/volatilite = güçlü, MONOTON, rejim-dayanıklı edge** | IC **+0.348** (n=53.856); decile medyan **0.86→8.54 monoton**; üst-%10 **+8.54** vs alt-%10 **+0.86** (7.7 puan); regime True **+0.40** / False **+0.28** | Projenin "ATR sağlam edge" tezini **DOĞRULAR** |
| composite_score kırık | IC **−0.009** (≈0) | Bilgi yok — teyitli |
| finpilot_score zayıf-pozitif | IC **+0.039** (seçilende +0.201); decile düz | Az bilgi, temiz edge değil |
| 52-hafta zirve yakınlığı ikincil edge | dist_52w_high IC **−0.159**, monoton | Zirveye yakın → daha iyi (George-Hwang 2004, 52-week-high momentum) |
| **Seçilen (entry_ok, n=1725) skor POZİTİF** | score +0.075, finpilot +0.201, ATR +0.294 | **Anti-prediktif DEĞİL** |

**Rejim testi (Part 5 artık ÇÖZÜLDÜ):** ATR edge her iki rejimde de güçlü pozitif (+0.28/+0.40) → **dayanıklı,
rejime bağlı bir istisna değil.** Skorlar rejimde işaret değiştirmiyor.

**Peki 91-pencere neydi?** Geç-Temmuz ~3 haftalık **temsili olmayan, negatif bir dilim** (canlı gölge). 10 aylık
resmin içinde normal bir **drawdown penceresi**. Tek-pencereden "skor ters" sonucu **küçük-örneklem hatasıydı**;
tüm veri düzeltti. (Aşağıdaki 91-analiz denetim izi için korunur, ama **birincil sonuç DEĞİL.**)

**Düzeltilmiş nihai öneri:** Skoru ağır ML ile yeniden kurmaya gerek yok — **edge zaten ATR/volatilitede**
(güçlü, monoton, rejim-dayanıklı). Yön: (1) sıralamayı **ATR-ağırlıklı** yap ve composite'i emekliye ayır
(legacy_quality zaten bunu yapıyordu), (2) **52-hafta-zirve yakınlığını** ikincil faktör ekle, (3) canlı
Temmuz zayıflığını **rejim-drawdown** olarak izle (otomasyon biriktiriyor).
**Dürüst uyarı:** genel medyan resolved +3.45 = bull-dönemi beta'sı içeriyor; ATR-IC **kesitsel (rank)** olduğu
için beta-ötesi gerçek sıralama becerisidir, ama mutlak +8.5%'in içinde piyasa driftı var → **cost/slippage +
beta düşülmüş net edge ayrıca ölçülmeli** (bir sonraki adım).

---

## 0.1 — TAM-VERİ TAMAMLANMIŞ BÖLÜM SONUÇLARI (Part 3/4/6/8/11)

**PART 8 — Zaman-içi kararlılık (aylık rank-IC, en kritik robustluk testi):**

| Özellik | Ay | Ort. IC | std | Pozitif-ay % | Aralık |
|---|--:|--:|--:|--:|--|
| **atr_pct_real** | 6 | **+0.369** | 0.10 | **%100** | +0.21 … +0.55 |
| dist_52w_high | 6 | −0.107 | 0.09 | %17 (tutarlı negatif) | −0.20 … +0.07 |
| finpilot_score | 3 | −0.011 | 0.03 | %33 | — |
| score | 6 | −0.031 | 0.03 | %17 | — |

→ **ATR edge HER AYDA pozitif (6/6)** — güçlü, kararlı, tesadüf değil. Skorların IC'si sıfır civarı/kararsız.

**PART 6/1 — Kısmi değer (çok-değişkenli standardize β, n=51.910, winsorize):**
`atr_pct_real +0.599` ≫ `gap_pct +0.113` · `dist_52w_high −0.118` · `rvol +0.025` · **`score +0.019` (≈0)**.
→ **ATR baskın; composite/score, ATR'nin ÜSTÜNE neredeyse HİÇ bilgi katmıyor.** İkincil: gap, 52-hafta-zirve.

**PART 4 — Çıkış / tutuş:** 1g medyan +0.04 (poz %51) → 5g medyan +3.45 (poz %86). ATR üst-%10'da: 1g **0.00** → 5g **+8.54**.
→ **ATR edge'i ~5 günlük tutuş İSTER** (1 günde yok). Temmuz'daki "kısalt" önerisi yalnız o kötü pencere içindi; tam veride ters.

**PART 3 — Giriş (scanner kapısı naif ATR'yi yeniyor mu?):**
| Seçim | n | 5g medyan | Poz% |
|---|--:|--:|--:|
| **naif ATR üst-%10** | 5.386 | **+8.54** | 81 |
| entry_ok=True (scanner) | 1.725 | +4.18 | 89 |
| tüm evren (baseline) | 53.859 | +3.45 | 86 |
→ **Basit "ATR üst-%10" kuralı, karmaşık scanner seçimini MEDYAN getiride ikiye katlıyor** (+8.54 vs +4.18). Scanner baseline'ı ancak azıcık geçiyor. Projenin "sadelik kazanır" dersi bir kez daha doğrulandı. (Scanner isabet oranı biraz yüksek — 89 vs 81 — ama getiri çok düşük.)

**PART 5 — Rejim:** ATR edge her iki `regime` değerinde de pozitif (+0.28 / +0.40) → dayanıklı. *Ama tüm dönem bull; bear testi hâlâ yok.*

**PART 7 — Skor yeniden kurulumu:** Gereksiz. Kısmi-β analizi ATR dışındaki her şeyin ~sıfır katkı verdiğini gösterdi → karmaşık ML değil, **ATR-ağırlıklı basit sıralama** doğru cevap. (sklearn yok; ayrıca n/rejim ML için yetersizdi — dürüstçe ertelendi.)

**PART 11 — NİHAİ ÖNERİ (tam-veri, robustluk-kontrollü):**
1. **Sıralamayı ATR/volatilite-ağırlıklı yap; composite'i emekliye ayır** — güven **YÜKSEK** (IC +0.37, 6/6 ay, β +0.60). Karmaşıklık düşük.
2. **~5 gün tut** — edge 5g'de olgunlaşıyor, 1g'de yok. Güven yüksek.
3. **İkincil faktör: gap + 52-hafta-zirve yakınlığı** — orta güven.
4. **Net edge'i ölç:** +8.54 medyan **bull-beta + uç değer içerir**; cost/slippage (yüksek-ATR'de spread geniş) + beta düşülmüş **net** edge ayrı ölçülmeli. Risk-ayarlı (yalnız medyan değil) bak.
5. **Bear testi eksik** — tüm dönem bull; otomasyon farklı rejim biriktirene kadar "bull'da kanıtlı" de.
**Beklenen Sharpe/CAGR:** rapor edilemez (net/cost-sonrası + out-of-sample bear yok) — uydurulmaz.

---

## 0.2 — NET EDGE: cost + piyasa-nötr (asıl para kazandırır mı?)

**Yöntem:** her sinyalin getirisinden **aynı-gün evren medyanı** çıkarıldı (piyasa yönü nötrlendi),
uç değerler ±%50 kırpıldı (gerçekçi TP proxy + +16866% artefaktı bastırmak), sonra **%0.5 round-trip cost** düşüldü.

| Grup | n | Ham medyan | Piyasa-nötr medyan | Nötr (cap±50) | **Nötr − cost** | Poz% |
|---|--:|--:|--:|--:|--:|--:|
| Tüm evren | 53.856 | 3.45 | 0.00 | 2.20 | 1.70 | 49.9 |
| entry_ok (scanner) | 1.725 | 4.18 | 0.36 | 3.17 | **2.67** | 53.7 |
| **ATR üst-%10** | 5.411 | 8.36 | **4.88** | 8.40 | **+7.90** | 68.2 |
| ATR alt-%10 | 5.348 | 0.88 | −2.24 | −1.74 | −2.24 | 15.2 |

**ATR decile → piyasa-nötr excess medyan:** [−2.24, −1.14, −0.91, −0.3, 0.25, 0.67, 1.15, 2.1, 2.9, **4.88**] — **monoton.**

**Cevap:** ATR edge **sadece bull-beta DEĞİL** — aynı-gün medyanından arındırıldıktan (piyasa yönü çıkarıldıktan)
**ve** cost düşüldükten sonra da pozitif ve monoton (net **+7.90**, %68 pozitif). Bu **kesitsel gerçek beceri.**
Ve naif ATR (+7.90) yine scanner'ı (+2.67) ikiye katlıyor.

**AMA dürüst 3 uyarı (kritik):**
1. **Vol-beta ≠ arındırıldı.** Gün-medyanı demean piyasa **yönünü** çıkarır ama **volatilite-beta**'yı çıkarmaz.
   Yüksek-ATR = yüksek-beta; ve dönem **bull** (aylık medyanlar +1.6…+5.8 hep pozitif). Yani bu edge büyük ölçüde
   "yükselen piyasada yüksek-vol daha çok kazanır" — **ayı/risk-off rejiminde tersine dönebilir.** Rejim-koşullu.
2. **Veri kalitesi P0:** Mart 2026 dilimi medyan **−99.01** → bozuk veri artefaktı; temizlenmeli, sonucu kirletir.
3. **İyimserlik payı:** ±%50 cap ve %0.5 cost iyimser; gerçek TP/SL daha az yakalar, yüksek-ATR'de spread daha geniş.
   Yine de +7.90 net, %1-2 cost'ta bile pozitif kalır — büyüklük sağlam, ama mutlak rakam şişkin.

**Net verdikt:** ATR edge **gerçek ve cost'a dayanıklı**, ama **bull-koşullu bir yüksek-volatilite maruziyeti** —
canlıya güvenmeden önce **ayı-rejim testi ŞART** (otomasyon rejim biriktiriyor). Skor/scanner bu edge'e **değer katmıyor**;
sade ATR-üst-decile daha iyi.

---

## (SÜPERSEDED — §0 bunu geçersiz kıldı) 91-PENCERE ANALİZİ — Skor neyi ölçüyor?

**Bulgu (istatistiksel olarak anlamlı):** FinPilot skoru — özellikle **v2** — bu pencerede **süreklilik
(continuation) değil, tükeniş/aşırı-uzama (exhaustion/overextension)** ölçüyor ve **anti-prediktif**.
Yani yüksek skor → daha kötü 5-günlük getiri. Kanıtlar:

1. **v2 skoru ↔ 5g getiri rank-IC = −0.36** (n=309, %95 GA [−0.45, −0.27], permütasyon **p<0.001**). Güçlü, anlamlı **negatif**.
2. **legacy_quality IC = −0.14** (GA [−0.25, −0.03], **p=0.013**) — daha zayıf ama anlamlı negatif.
3. **Volatilite (ATR) IC = −0.26, gerçekleşmiş vol IC = −0.24** (ikisi de **p<0.001**) — yüksek oynaklık bu pencerede **daha kötü** (backtest boğa döneminde pozitifti → **rejime bağlı**, evrensel edge değil).
4. **Giriş-öncesi 5g koşu (pre5) IC = −0.16** (**p=0.002**) — sinyal, **yeni fırlamış** isimleri seçiyor; onlar geri dönüyor (kısa-vadeli reversal).
5. **Tutuş decay'i:** gün1 medyan ≈ **−0.04** (nötr) → gün5 **−4.84** → gün10 **−12.0**. Zarar tutuşla birikiyor.
6. **Asimetri:** MFE5 medyan **+3.66** vs MAE5 medyan **−8.28** — aşağı yön, yukarı yönden ~2.3× sert.

**Ekonomik yorum:** Bu, klasik **kısa-vadeli reversal** (Jegadeesh 1990; Lehmann 1990): çok-yeni
kazanç/hacim/volatilite fırlaması yaşayan (özellikle küçük-cap) isimler sonraki günlerde geri döner.
v2'nin "short-ağır squeeze + gap + RVOL − extension" tarifi tam da **aşırı-uzamayı** yüklüyor;
yumuşak/mean-reverting rejimde bu geri döner.

**Ama tek rejim.** Kısa-vadeli reversal choppy rejimde baskındır; güçlü trend rejiminde momentum-devamı
baskın olup bu IC'ler **pozitife dönebilir**. O yüzden strateji **rejim-koşullu** olmalı; çok-rejim
kanıtı (otomasyon biriktiriyor) olmadan kural değiştirilmez.

---

## PART 1 & 6 — SKOR VE ÖZELLİK ANALİZİ (ne ölçüyor?)

**Yöntem:** rank-IC (Spearman) her özellik ↔ 5g getiri; bootstrap %95 GA; permütasyon p (2000 iter).
Hem seçilen-içi (n=91) hem tüm örneklem kesitsel (n=309, daha güçlü).

**Tüm örneklem (n=309) — 5g getiriyi yordama gücü:**

| Özellik | rank-IC | %95 GA | p | Yorum |
|---|--:|--|--:|---|
| **score_v2** | **−0.364** | [−0.45, −0.27] | **<0.001** | Güçlü anti-prediktif |
| **atr_pct** | **−0.261** | [−0.38, −0.15] | **<0.001** | Yüksek vol → kötü (bu rejim) |
| **rvol20** | **−0.244** | [−0.34, −0.14] | **<0.001** | Gerçekleşmiş vol → kötü |
| **pre5** | **−0.164** | [−0.28, −0.05] | **0.002** | Aşırı-uzama teyidi |
| **score_legacy** | **−0.144** | [−0.25, −0.03] | **0.013** | Zayıf anti-prediktif |
| dollar_adv | −0.117 | [−0.24, 0.00] | 0.037 | Marjinal |
| gap | −0.039 | [−0.17, 0.08] | 0.492 | Anlamsız |
| rvol | −0.026 | [−0.14, 0.08] | 0.658 | Anlamsız |
| dist_ema20 | −0.045 | [−0.17, 0.07] | 0.437 | Anlamsız |

**Kabul/Ret:** "Skor süreklilik ölçüyor" hipotezi **REDDEDİLDİ** (v2 IC anlamlı negatif). "Skor aşırı-uzama/
tükeniş ölçüyor" hipotezi **KABUL** (v2, ATR, rvol20, pre5 anlamlı negatif; hepsi oynaklık/fırlama ekseninde).
Gap/rvol/dist_ema **bilgi taşımıyor** (bu pencerede). Doğrusal-dışı/rejim/sektör bağımlılığı: **test edilemedi**
(tek rejim, n küçük) → §5.

---

## PART 2 — RANKING DOĞRULAMA (yön ters mi?)

legacy_quality tercili → 5g medyan (seçilen): **düşük −0.87 · orta −5.96 · yüksek −6.26.**
Monotonik: yüksek skor **daha kötü**. Ranking yönü bu pencerede **ters çalışıyor**.
Reverse/percentile/z-score dönüşümleri: yön aynı kalır (monoton negatif); asıl mesele ölçek değil **işaret**.
**Öneri (koşullu):** yüksek-skoru "al" değil; rejime göre **fade** veya **ranking-inversiyonu** aday.
Ama tek pencere → §8 çoklu-test uyarısı: kural değiştirmeden önce çok-rejim.

---

## PART 3 & 4 — GİRİŞ / ÇIKIŞ (tutuş süresi kritik)

**Tutuş decay'i (seçilen medyan getiri):** fwd1 **−0.04** (poz %48) · fwd2 −0.95 · fwd3 −1.50 ·
fwd5 **−4.84** (poz %21) · fwd10 −12.0 (n=23). → **Ne kadar uzun tutarsan o kadar kötü.**
Gün-1 ≈ başabaş; zarar 2–10. günde birikiyor.

**Uygulanabilir (bu pencerede yüksek güven):** tutuşu **kısalt** (1–2 gün / intraday çıkış) — reversal'ı
atlar. *Not:* gün-1 hâlâ hafif negatif (poz %48) → bu **pozitif edge değil**, sadece hasarı önler.
Tam giriş menüsü (VWAP/Donchian/opening-range/intraday) **günlük barla test edilemez** → intraday veri gerekir (ertelendi).

**Çıkış:** ATR-stop 1× bar-içi-önce-stop MFE'yi (+3.66) yakalayamadan MAE'ye (−8.28) takılıyor →
sıkı stop whipsaw. Kısa zaman-stopu (1–2 gün) mevcut bariyerden iyi görünüyor; formal exit-grid çok-rejim ister.

---

## PART 5 — PİYASA REJİMİ — **YETERSİZ VERİ (ERTELENDİ)**

Elimizdeki veri ~3 hafta ve **tek rejim** (yumuşak/choppy). Bull/bear/sideways/high-low-vol kümelemesi
**yapılamaz** — tek gözlemle rejim-bağımlılık ölçülemez. **Bu, projenin bir numaralı boşluğu.**
Bulguların (skor anti-prediktif, ATR negatif) **rejime bağlı olduğu güçlü olasılık** (backtest boğa
döneminde ATR pozitifti). Otomasyon (`daily_shadow_update.py`) her tarama bir satır biriktiriyor →
birkaç hafta/ay sonra rejim-koşullu IC hesaplanabilir. **Kural değişikliği bu kanıta kadar bekler.**

---

## PART 7 — SKOR YENİDEN KURULUMU (ML) — **YETERSİZ VERİ (ERTELENDİ)**

n=91 seçilen (veya 309 toplam) ile XGBoost/LightGBM/NN/LambdaMART fit etmek **overfitting tiyatrosu**
olur (promptun açık yasağı). scipy/sklearn de sandbox'ta yok. Bu aşamada **yapılmaz.**
Yapılabilecek dürüst asgari (gelecekte, veri büyüyünce): tek-değişkenli IC'lerle **basit doğrusal/parçalı**
skor + bootstrap CV. Şimdilik kanıt: mevcut composite/v2 **anti-prediktif**; en sağlam ilk adım karmaşık
model değil, **skoru rejim-koşullu kullanmak / işaretini düzeltmek** (§2, §11).

---

## PART 8 — İSTATİSTİKSEL DOĞRULAMA

- **Permütasyon testleri:** yukarıdaki p-değerleri (2000 iter) — v2/atr/rvol20/pre5/legacy anlamlı; gap/rvol/dist değil.
- **Bootstrap %95 GA:** her IC için raporlandı; anlamlıların GA'sı sıfırı içermiyor.
- **Çoklu-test uyarısı:** 9 özellik test edildi; Bonferroni-benzeri kabaca eşik ~0.006. v2 (p<0.001),
  atr (p<0.001), rvol20 (p<0.001) **düzeltme sonrası da anlamlı**; pre5 (0.002) sınırda anlamlı;
  legacy (0.013) ve dollar_adv (0.037) çoklu-test sonrası **zayıflar**.
- **Walk-forward / CPCV / deflated-Sharpe / PBO:** tek pencere → **yapılamadı** (ertelendi, §5).
- **Sonuç:** en sağlam istatistiksel iddia — **v2 skoru ve oynaklık (ATR/rvol20) bu pencerede 5g getiriyle
  anlamlı NEGATİF ilişkili.** Diğerleri zayıf/anlamsız.

---

## PART 9 — AKADEMİK LİTERATÜR

- **Kısa-vadeli reversal** (Jegadeesh 1990; Lehmann 1990): 1-hafta-1-ay ölçeğinde geçmiş kazananlar geri
  döner — bizim pre5/ATR/reversal imzamızla **birebir uyumlu**.
- **Momentum** (Jegadeesh & Titman 1993): 3–12 ay ölçeğinde devam eder; bizim 1–5 gün ölçeğimiz momentum
  değil reversal bölgesi → skorun kısa-vadede yordama yönü bu yüzden ters olabilir.
- **Düşük-volatilite anomalisi** (Ang ve ark. 2006; Baker ve ark. 2011): yüksek-vol hisseler uzun vadede
  düşük getiri — ATR'nin negatif IC'siyle tutarlı.
- **Adaptive Markets Hypothesis** (Lo 2004): edge'ler rejime göre değişir → tek-rejim bulgusunu evrensel sayma.
- **Meta-labeling** (López de Prado 2018): birincil sinyalin "işlem almaya değer mi" ikinci-model kararı →
  §12'de doğru gelecek yön (veri büyüyünce).
Her biri şunu söylüyor: **sinyalimiz büyük olasılıkla bir kısa-vadeli-reversal dedektörü**; momentum gibi
kullanmak yön hatası. Doğru kullanım: rejim-koşullu ve/veya fade + kısa tutuş.

---

## PART 10 & 12 — DENEYSEL / EDGE-KEŞİF (yapılabilenler)

- **Reverse / düşük-skor seç:** düşük-tercil −0.87 vs yüksek-tercil −6.26 → skoru terslemek "en kötüyü"
  önlüyor ama **pozitif edge yaratmıyor** (düşük hâlâ ~−0.9, tek pencere, in-sample). Umut verici ipucu, kanıt değil.
- **ATR-normalize momentum / vol-normalize pullback:** ham ATR negatif; **normalize** varyantlar mantıklı
  bir sonraki test (veri büyüyünce). Şu an tek-pencere sinyali zayıf.
- **Meta-labeling / conformal / online-learning / RL / HMM rejim-switch:** kavramsal olarak **doğru yön**
  (skor "işlem al" değil "aşırı-uzama var" diyor → ikinci bir model "bu fade edilir mi" karar verebilir);
  ama **veri + altyapı gerektirir** (n çok küçük) → ertelendi, otomasyon zeminini kuruyor.

---

## PART 11 — NİHAİ ÖNERİ (yalnız kanıtın desteklediği; güven etiketli)

| Öneri | Dayanak | Güven | Karmaşıklık |
|---|---|---|---|
| **Skoru "süreklilik/al" olarak kullanma** — v2 anti-prediktif | IC −0.36, p<0.001 | **Yüksek** (bu rejim) | Düşük |
| **Tutuşu kısalt (1–2 gün / intraday)** — decay 1→5→10 günde birikiyor | monoton decay | **Yüksek** (bu rejim) | Düşük |
| **Skoru rejim-koşullu kullan / işaretini rejime göre çevir** | AMH + tek-rejim bulgusu | Orta | Orta |
| **ATR/vol'ü tek başına edge sayma** — rejime bağlı | IC −0.26, p<0.001 (burada) vs boğada pozitif | Orta | Düşük |
| **Fade/short adayı olarak test et** (yüksek-skoru sat) | reversal imzası | Orta-düşük (in-sample) | Orta |
| **Çok-rejim veri biriktir → sonra ML/meta-label** | §5/§7 boşluğu | — | Yüksek |

**Beklenen Sharpe/CAGR/DD:** **rapor edilemez** — tek pencere, out-of-sample yok. Herhangi bir sayı
uydurma olur. Robustluk skoru: **düşük** (tek rejim). En sağlam tek cümle: *"Skor, kısa-vadeli aşırı-uzamayı
anlamlı biçimde ölçüyor ama yönü ters; doğru kullanım rejim-koşullu + kısa tutuş + muhtemelen fade — ve bu
çok-rejim veriyle doğrulanmadan üretime alınmaz."*

---

## ZORUNLU KURALLARA UYUM
- Backtest kârı için optimize edilmedi; **robustluk** önceliklendi.
- Kanıtsız hiçbir "daha iyi" iddiası yok; her sayı GA + p ile.
- Belirsizlik açıkça raporlandı (tek rejim, küçük n, çoklu-test).
- Basit > karmaşık: ML yerine "skoru doğru kullan" önerildi.
- Yeniden üretilebilir: `data/shadow/research_dataset.csv` + bu betikler.

## KAPSAM DIŞI / SONRAKİ
- Rejim kümeleme, walk-forward, CPCV, deflated-Sharpe, ML skor, meta-labeling, conformal — **çok-rejim veri**
  bekliyor (otomasyon biriktiriyor). İntraday giriş kuralları (VWAP/ORB) **intraday veri** bekliyor.
- Bir sonraki somut deney (veri ~2–3 kat olunca): rejim-koşullu IC + skor-inversiyon out-of-sample + kısa-tutuş exit-grid.
