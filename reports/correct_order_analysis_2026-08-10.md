# The Correct Order — Veri → Ölçüm → Execution → Sinyal

Date: 2026-08-10
Level: A (research synthesis)
Layer: Research / strategy
Status: applied — no production, promotion, or public-surface decision

## Neden bu sıra?

Strategic Thinking Lab'in teşhisi: "Sıralamamız hep ters oldu. Biz: score →
entry → exit → portfolio → (sonra) veri kalitesi → (sonra) execution. Doğru
sıra: **veri → ölçüm → execution → ancak sonra sinyal.**"

Bu doküman her katmanın mevcut durumunu kanıtla değerlendirir ve sıradaki
somut adımı çıkarır. Bugünkü close-to-close export düzeltmesi, bu sıranın
ilk katmanının neden kritik olduğunu kanıtladı.

---

## Katman 1 — VERI (data integrity)

**Soru:** Ölçtüğümüz şey gerçek mi?

| Alt-katman | Durum | Kanıt |
|---|---|---|
| Etiket semantiği | **KAPANDI (bugün)** | `resolved_pct_t5` = MFE (max HIGH T+1..T+5), getiri değil. Kaynak: `fetch_full_universe_and_retest.py:286`. Gerçek close-to-close (`c2c_5d`) ve MAE (`mae_t5`) artık export'ta. |
| Fiyat sürekliliği | **AÇIK** | 148/2,039 sembolde %50+ tek-gün sıçrama (adjusted backfill sonrası). EODHD adjusted OHLC sağlamıyor. |
| Etiket ↔ cache tutarlılığı | **KAPANDI (bugün)** | MFE vs c2c_5d ayrışması doğrulandı (medyan +4.12% vs +0.085%). |
| Feature timestamp/age | **AÇIK** | Hangi feature hangi anda biliniyordu — lineage yok. |
| Restatement | **AÇIK** | Veri sağlayıcı tarihsel barları sessizce revize ediyor mu — ölçülmedi. |

**Bugünkü ders:** Etiket semantiği bozukken (MFE ≠ getiri) yapılan tüm
"edge" ve "kalibrasyon" analizleri ~48x şişirilmiş bir ölçüye dayanıyordu.
Veri katmanı kapanmadan üst katmanlar anlamsız.

---

## Katman 2 — ÖLÇÜM (measurement)

**Soru:** Doğru şeyi mi, doğru şekilde mi ölçüyoruz?

| Alt-katman | Durum | Kanıt |
|---|---|---|
| Etkin örneklem | **ÖLÇÜLDÜ** | 27,361 satır ≈ **620 etkin gözlem** (gün-içi korelasyon). Naive CI'lar ~44x dar. |
| Deney bütçesi | **AÇIK** | 2,520 + 3,120 konfigürasyon; toplam multiple-testing bütçesi hiç sayılmadı. |
| Null-relative standart | **KISMEN** | 3,000 immutable null run var; ama her bulguya zorunlu preflight değil. |
| Replayability | **AÇIK** | P0 score replay hâlâ INSUFFICIENT_DATA (telemetry export Level B pending). |
| İstatistiksel güç | **ÖLÇÜLDÜ** | Çoğu kohort n<200; üst score bandı n=12. |

**Bugünkü ders:** Etkin örneklem ölçümü (S1), geçmişteki "anlamlı" sonuçların
çoğunun illüzyon olduğunu gösterdi. Ölçüm katmanı, sinyal katmanından önce
gelmeli.

---

## Katman 3 — EXECUTION (tradeability)

**Soru:** Sinyal gerçek piyasada yakalanabilir mi?

| Alt-katman | Durum | Kanıt |
|---|---|---|
| Spread/impact | **YOK** | Observed spread rate %0; hiç spread verisi yok. |
| Entry drift | **ÖLÇÜLDÜ** | Medyan %0.55, p95 %5.33 — çoğu adayın beklenen edge'inden büyük. |
| İntraday path | **YOK** | Daily OHLC fill ordering'i kanıtlayamaz. |
| Capacity | **AÇIK** | Likidite snapshot'ı tarihsel outcome'lara join edilmemiş. |
| Signal half-life | **YOK** | Sinyalin ömrü hiç ölçülmedi. |

**Bugünkü ders:** Execution katmanı neredeyse tamamen boş. Daily-bar
backtest'ler "sinyal vardı" diyor ama "yakalanabilir mi?" cevapsız.

---

## Katman 4 — SİNYAL (the score itself)

**Soru:** Score ileriye dönük bilgi taşıyor mu?

**Bugünkü close-to-close etiketiyle (dürüst ölçüm) yeniden test:**

| Test | Sonuç | Yorum |
|---|---|---|
| score vs c2c_5d (realized) | ρ = **0.011** | İleri bilgi yok |
| score vs MFE (eski etiket) | ρ = -0.106 | MFE ile de yok |
| score vs mae_t5 (adverse) | ρ = +0.095 | Daha yüksek score = daha kötü adverse excursion |
| **eligible c2c_5d medyan** | **-2.39%** | Seçilen kohort **kaybediyor** |
| **rejected c2c_5d medyan** | **+0.06%** | Reddedilen kohort **kazanıyor** |
| eligible pozitif oran | **35.4%** | |
| rejected pozitif oran | **50.4%** | |

**Bu, dürüst etiketle gelen en sert sonuç:** Seçim katmanı (entry_ok),
gerçekleşen close-to-close getiriyle ölçüldüğünde, **rastgele reddedilen
kohorttan anlamlı şekilde daha kötü** (-2.39% vs +0.06 medyan; 35% vs 50%
pozitif oran). Bu, MFE-etiketiyle görünmeyen bir bulgu — çünkü MFE "5 gün
içinde bir noktada yukarı gitti mi?"yi ölçer, "5 gün sonra nerede?"yi değil.

---

## Sentez: Neden sıra ters oldu?

```
Bizim sıramız:        score → entry → exit → portfolio → veri → execution
                         ↑___________________________________________|
                         (en sonda fark edilen, en başta olmalıydı)

Doğru sıra:           veri → ölçüm → execution → sinyal
                         ↑
                         (bugün buraya geldik — etiket düzeltmesi)
```

**Kanıt zinciri:**
1. Veri bozukken (MFE ≠ getiri) → score "edge" gösterdi (şişirilmiş).
2. Ölçüm bozukken (etkin örneklem ~620) → sonuçlar "anlamlı" göründü.
3. Execution ölçülmeden → "sinyal var" dendi ama "yakalanabilir mi?" bilinmedi.
4. Sinyal en başa kondu → 2 yıl parametre tuning'i, sıfır cost-positive.

**Bugün veri katmanının etiket tarafı kapandı ve sonuç hemen değişti:**
eligible kohort MFE ile "hareket potansiyeli var" gibi görünüyordu; dürüst
c2c_5d ile **kaybediyor**. Bu, sıranın neden önemli olduğunun canlı kanıtı.

---

## Sıradaki somut adımlar (doğru sırada)

### Veri (kalan)
1. **Fiyat sürekliliği:** 148 işaretli sembolün adjusted OHLC onarımı.
2. **Feature lineage:** her feature için timestamp/age.
3. **Restatement dedektörü:** tarihsel bar revizyonu izleme.

### Ölçüm
4. **Deney bütçesi defteri:** toplam koşulan konfigürasyon sayısı public.
5. **Null-relative preflight:** her yeni bulguya zorunlu null kontrolü.
6. **Replayable telemetry:** P0 score replay'i kapatacak export (Level B pending).

### Execution
7. **Spread/ADV toplama başlat:** günde 3 kez bid/ask snapshot, 30 gün biriktir.
8. **Signal half-life:** sinyalin predictive gücü kaç saat/gün sürüyor.

### Sinyal (ancak yukarıdakilerden sonra)
9. **Pre-registered üç hipotez** (gap-reversal, rvol-inversion, ATR-parity) —
   temiz c2c_5d etiketiyle, yeni veriyle, null-relative. Ama önce
   kullanıcı-gerçeği kapısı (PR1/PR7).

---

## Tek cümlelik sonuç

**Veri katmanındaki tek bir etiket düzeltmesi (MFE → close-to-close), iki
yıllık "edge" anlatısını tersine çevirdi: seçilen kohort dürüst ölçümle
kaybediyor (-2.39% medyan), reddedilen kazanıyor (+0.06%).** Bu, "veri →
ölçüm → execution → sinyal" sırasının neden pazarlık edilemez olduğunun
kanıtı — ve sinyal katmanına ancak alttaki üç katman kapandıktan sonra
geçilebileceğinin gerekçesi.

## Confound kontrolü: etiket mi, veri mi?

Export yeniden üretilirken satır seti değişti (53,859 → 100,496 ham; 38 yeni
sembol, 3 hafta daha uzun tarih). "Seçim kaybediyor" sonucu etiketten mi,
yeni veriden mi? Bunu ayırmak için **aynı 27,386 sembol-günde** (eski ∩ yeni
export) yalnızca etiketi değiştirdik:

| Kohort | MFE medyan | c2c_5d medyan | MFE pozitif | c2c_5d pozitif |
|---|---|---|---|---|
| eligible | +4.08% | **-0.19%** | 87.9% | **48.8%** |
| rejected | +3.58% | **+0.41%** | 85.7% | **53.5%** |
| **fark (elig − rej)** | **+0.50** | **-0.61** | | |

**Aynı satırlar, aynı semboller, aynı tarihler — tek fark etiket.** MFE ile
seçim "+0.50 kazanıyor" görünürken, dürüst close-to-close ile "-0.61
kaybediyor". İşaret tamamen tersine dönüyor. Bu, veri değişikliği değil,
**saf etiket etkisi** — ve "veri → ölçüm → execution → sinyal" sırasının
confound'suz kanıtı. (Not: bu eşleştirilmiş analizde eligible medyan -0.19%,
tam yeni export'taki -2.39%'dan farklı — çünkü eşleştirme yalnızca eski
export'un sembol-günlerini kapsıyor; iki sayı da aynı yönü gösteriyor.)
