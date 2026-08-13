# The Honest Quant Research Handbook
## Backtest'iniz Neden Yalan Söylüyor: 40 Deneyin Anatomisi

**FinPilot Research Team · 2026-08-10**
**Version 1.0 · DRAFT**

---

> Bu el kitabı, iki yıllık bir quant araştırma programının en acı verici — ve en
> öğretici — bulgularını toplar. Tek bir strateji önermez. Tek bir "edge"
> iddia etmez. Bunun yerine, kendi sistemimizi 40+ deneyden geçirerek
> öğrendiğimiz şeyi paylaşır: **bir backtest'in size yalan söylemesinin kaç
> yolu olduğunu ve her birini nasıl yakalayacağınızı.**
>
> Her bölüm gerçek bir hatayı, onu yakalayan testi ve çıkan dersi anlatır.
> Hiçbir sayı "kanıtlanmış edge" olarak sunulmaz; hepsi "bu tuzağa düşmeyin"
> olarak sunulur.

---

## Bölüm 1 — Etiket Yalanı: MFE ≠ Getiri

**Hata:** İki yıl boyunca `resolved_pct_t5` alanını "5 günlük getiri" olarak
kullandık. Kaynak koddan doğruladık: bu alan 5 gün içindeki **maksimum HIGH**
(MFE — maximum favorable excursion), kapanış-kapanış getiri değil.

**Kanıt:** Aynı 27,386 sembol-günde yalnızca etiketi değiştirdik:

| Kohort | MFE medyan | Gerçek getiri (c2c_5d) medyan |
|---|---|---|
| Seçilen | +4.08% | **-0.19%** |
| Reddedilen | +3.58% | **+0.41%** |

MFE ile seçim "kazanıyor" görünüyordu; dürüst getiri ile **kaybediyor**.
İşaret tamamen tersine döndü.

**Ders:** Her etiketin semantiğini kaynak koddan doğrulayın. "resolved"
kelimesi "gerçekleşen getiri" demek değildir. MFE "bir noktada yukarı gitti
mi?"yi ölçer; "5 gün sonra nerede?"yi değil. İkisi farklı sorular; birini
diğerinin yerine kullanmak tüm analizi geçersiz kılar.

**Kontrol:** `fetch_full_universe_and_retest.py:286` — etiketin ne ürettiğini
kaynak koddan okuyun, dokümantasyondan değil.

---

## Bölüm 2 — Örneklem Yalanı: 27,000 Satır ≈ 620 Gözlem

**Hata:** 27,361 satırlık bir veri setini "büyük örneklem" sandık.

**Kanıt:** Aynı gün taranan semboller birbirinden bağımsız değil — aynı piyasa
gününü paylaşıyorlar. Tarih-blok bootstrap ile etkin örneklem büyüklüğünü
ölçtük: **27,361 satır ≈ 620 etkin gözlem.** Naive güven aralıkları ~44x
düşük belirsizlik gösteriyordu.

**Ders:** Satır sayısı ≠ bilgi. Gün-içi korelasyon, aynı sembolün ardışık
sinyalleri ve rejim yoğunlaşması etkin örneklemi dramatik biçimde küçültür.
Her istatistiksel iddianın yanına "kaç **bağımsız** gözlem?" yazın.

**Kontrol:** Tarih-blok bootstrap (satırları değil, günleri yeniden örnekle).
Etkin örneklem oranını raporlayın.

---

## Bölüm 3 — Skor Yalanı: Tahminci Değil, Ayna

**Hata:** Composite score'un ileriye dönük bilgi taşıdığını varsaydık.

**Kanıt:** Beş bağımsız test:
- Score geçmiş 5 günle ρ=0.376, gelecek 5 günle ρ=0.013 (geriye bakıyor).
- En güçlü kodladığı feature: 52-hafta-yükseğe uzaklık (ρ=0.667) — yani
  "ne kadar uzamış olduğu".
- Olasılığa çevrilince base rate'ten **kötü** (negatif Brier skill).
- Tersine çevirmek (fade) kaybediyor — ayna bile değil.
- En iyi score bandı içinde seçim katmanı **tersine seçim** yapıyor.

**Ders:** Bir skor "ne olacak?"ı değil "ne oldu?"yu ölçüyor olabilir — ve
bunu anlamanın tek yolu, skoru geçmiş ve gelecek getiriyle ayrı ayrı
korele etmektir. Yüksek skor ≠ yüksek gelecek getiri.

**Kontrol:** Spearman(score, past_return) vs Spearman(score, forward_return).
İlki ikincisinden büyükse, skorunuz bir ayna.

---

## Bölüm 4 — Seçim Yalanı: Counterfactual'ı Yenemeyen Seçim

**Hata:** "Seçici" olduğumuzu varsaydık — en iyi adayları seçtiğimizi.

**Kanıt:** Seçilen kohortu, aynı gün rastgele reddedilen adaylardan oluşan
portföylerle karşılaştırdık (counterfactual portfolio). Seçim, rastgele
seçimden **daha kötü** çıktı (medyan fark -2.01pp, günlerin %31'inde önde).

**Ders:** Seçim katmanınızın değerini ancak counterfactual ile ölçebilirsiniz.
"Seçtiklerim iyi performans gösterdi" yeterli değil — "seçmediklerimden daha
iyi mi?" sorusu gerekli.

**Kontrol:** Her gün, seçilen N aday yerine reddedilenlerden rastgele N aday
seçin. 200 tekrar. Seçiminiz rastgeleyi yenemiyorsa, seçim katmanınız değer
üretmiyor.

---

## Bölüm 5 — Kalibrasyon Yalanı: Base Rate'ten Kötü

**Hata:** Skoru olasılığa çevirip "kalibre" dedik.

**Kanıt:** Out-of-sample Brier skill vs sabit base-rate tahmincisi: **-0.019**
(P(positive)) ve **-0.030** (P(beats cost)). Negatif skill = model, hiçbir
şey bilmeyen base rate'ten daha kötü.

**Ders:** Kalibrasyon eğrisi çizmek yeterli değil; modelinizin base rate'i
geçip geçmediğini ölçün. Brier skill score bunu tek sayıda verir.

**Kontrol:** Brier(model) vs Brier(base_rate). Skill = 1 - model/base.
Negatifse model zararlı.

---

## Bölüm 6 — Çoklu-Test Yalanı: 5,640 Konfigürasyonun Şansı

**Hata:** 2,520 barrier + 3,120 fixed-target konfigürasyonu koşup "en iyi"
sonucu raporladık.

**Kanıt:** En yüksek ortalamalı profillerde medyan negatif (örn. %94.7
ortalama / -%7.66 medyan) — outlier-driven. Hiçbir konfigürasyon hem
dönem-stabil hem maliyet-sonrası pozitif çıkmadı.

**Ders:** N konfigürasyon koşuyorsanız, en iyi sonucun şans eseri çıkma
olasılığı artar. Deney bütçesi tutun: toplam kaç konfigürasyon koşuldu,
kaçı anlamlı çıktı, beklenen şans oranı ne?

**Kontrol:** Deney bütçesi defteri (experiment registry). Her bulguya
"bu, N denemenin kaçıncısı?" etiketi.

---

## Bölüm 7 — Execution Yalanı: Sinyal Var, Yakalanabilir mi?

**Hata:** Daily-bar backtest'te "sinyal vardı" dedik.

**Kanıt:** Observed spread rate %0 — hiç spread verisi yok. Entry drift
medyan %0.55, p95 %5.33 — çoğu adayın beklenen edge'inden büyük. İntraday
OHLCV yok; fill ordering kanıtlanamaz.

**Ders:** Backtest'te sinyal olması, gerçek piyasada yakalanabilir olduğu
anlamına gelmez. Spread, slippage, market impact ve sinyal ömrü ayrı
katmanlar — ve hepsi sinyal katmanından önce gelmeli.

**Kontrol:** Sinyal → executable fiyat arasındaki drift'i ölçün. Drift >
beklenen edge ise, sinyal yok demektir.

---

## Bölüm 8 — Doğru Sıra: Veri → Ölçüm → Execution → Sinyal

**Sentez:** Tüm bu yalanlar aynı kökten geliyor — sırayı ters kurduk.

```
Yanlış:  score → entry → exit → portfolio → (sonra) veri → (sonra) execution
Doğru:   veri → ölçüm → execution → sinyal
```

Her katman bir kapıdır. Alt kapı açıksa, üst katmandaki hiçbir sonuç "bulgu"
sayılmaz — yalnızca "keşif sinyali" (discovery signal).

**Dört kapı:**
1. **Veri:** Etiket semantiği, fiyat sürekliliği, feature lineage, restatement.
2. **Ölçüm:** Etkin örneklem, deney bütçesi, null-relative preflight, replay.
3. **Execution:** Spread/impact, signal half-life, intraday path, capacity.
4. **Sinyal:** Ancak 1+2+3 kapalıysa confirmatory koşu.

---

## Ek A — Araç Seti (açık kaynak)

Bu el kitabındaki her kontrol, çalışan kod olarak mevcut:
- `feature_lineage.py` — feature provenance + leakage denetimi
- `restatement_detector.py` — sessiz tarihsel revizyon tespiti
- `null_preflight_gate.py` — finding vs discovery signal verdicti
- `experiment_registry.py::budget_report` — deney bütçesi defteri
- `signal_half_life.py` — sinyal ömrü ölçümü

## Ek B — Kontrol Listesi

Yeni bir backtest sonucu görmeden önce sorun:
- [ ] Etiketin semantiği kaynak koddan doğrulandı mı?
- [ ] Etkin örneklem büyüklüğü raporlandı mı?
- [ ] Skor geçmiş mi yoksa gelecek mi ölçüyor?
- [ ] Seçim counterfactual'ı yeniyor mu?
- [ ] Model base rate'i geçiyor mu (Brier skill)?
- [ ] Deney bütçesi biliniyor mu?
- [ ] Execution (spread/drift) ölçüldü mü?

---

*Bu el kitabı FinPilot Research Team'in 2025–2026 araştırma programından
derlenmiştir. Hiçbir yatırım tavsiyesi içermez. Tüm sayılar araştırma
bağlamında ve kendi veri setimizde geçerlidir; genelleştirilemez.*
