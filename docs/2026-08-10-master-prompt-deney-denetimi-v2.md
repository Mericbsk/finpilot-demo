# FINPILOT — TÜM DENEYLERİN KAPSAMLI DENETİMİ VE STRATEJİ SORGULAMASI
## Master Research Prompt v2.0 — "Gözden Kaçanı Bul, Yanlışı Göster, Yeni Soruyu Sor"

Statü: Level A (araştırma/sentez, üretim kararı değil). Bu belge bir deney değil,
**deneylerin kendisini denetleyen bir denetim protokolüdür.**

---

## 0. NEDEN BU BELGE VAR

Bu programda 40'tan fazla deney koşuldu, resmi bir evidence-gate matrisi kuruldu,
dört-kapılı bir araştırma protokolü onaylandı, ve bu süreçte EN AZ ÜÇ kez aynı hata
tekrarlandı: heyecan verici bir bulgu ilk bakışta güçlü göründü, ikinci bakışta
(gün-kümeleme/dedup/matched-random) çöktü. Bu üçüncü kez olduğunda bile, düzeltmenin
KENDİSİ abartılı sunuldu ("tek düzeltme iki yıllık anlatıyı tersine çevirdi") ve o
abartı da ayrı bir kontrol turunda düzeltilmek zorunda kaldı.

Bu, tek bir kişinin/sürecin hatası değil — **yapının kendisinin ürettiği bir
örüntü.** Heyecan, doğrulamadan önce geliyor. Bu belgenin amacı, bu örüntüyü
KIRACAK bir okuma disiplini dayatmak: her iddiayı önce şüpheyle karşıla, sonra
kanıtla, hiçbir zaman sırayı değiştirme.

Bu belge ayrıca şu üç ek amaca hizmet eder:
1. **Gözden kaçanı bulmak** — 40+ deney arasında hiç sorulmamış sorular var mı?
2. **Çelişkiyi göstermek** — farklı bataryaların/turların birbirini tutmayan
   sonuçları var mı, varsa neden?
3. **Stratejiyi sorgulamak** — belki sorun parametre değil, sorduğumuz SORU. Belki
   yanlış yere bakıyoruz.

---

## 1. ZORUNLU KURALLAR (bu programın kanla öğrendiği dersler — atlanamaz)

Bu kuralları uygulamayan hiçbir çıktı kabul edilmez:

**Kural 1 — Kanıt-etiketi zorunlu.** Her iddia şu etiketlerden birini taşımalı:
`FACT` (kod/veri-doğrulanmış, tartışmasız), `EVIDENCE` (istatistiksel destek var,
rigor-testinden geçti), `HYPOTHESIS` (makul ama doğrulanmamış), `DISCOVERY SIGNAL`
(ilk-bakış bulgu, artifact-merdiveninin hiçbir basamağını geçmedi), `UNKNOWN`
(bilmiyoruz, veri yetersiz). "Bulgu" (`finding`) kelimesi yalnız `EVIDENCE`
etiketli iddialar için kullanılabilir.

**Kural 2 — Artifact-merdiveni zorunlu.** Yeni bir kalıp/ilişki bulduğunda, dört
basamağı sırayla geçmeden "bulgu" diyemezsin: (1) satır-bazlı bölünme, (2)
gün-kümeli SE, (3) dedup + çoklu-zaman-bloğu, (4) matched-random-kontrol. Bir
basamağı atlarsan, çıktın otomatik olarak `DISCOVERY SIGNAL`dir.

**Kural 3 — Etkin-örneklem zorunlu.** Satır sayısı raporlama YASAK, yalnız etkin-n
(gün-kümeli/blok-bootstrap ile hesaplanmış) raporlanır. Bu programda etkin-n,
ham satır sayısının ~1/44'ü çıktı (27.361 → ~620). Bu oranı her yeni deneyde
yeniden tahmin et, sabit kabul etme.

**Kural 4 — Etiket-anlamı kod-seviyesinde doğrulanmadan kullanılamaz.**
`resolved_pct_t5`'in MFE (getiri değil) olduğu kod okunarak bulundu, isimden değil.
Her yeni alan için aynısını yap: isme güvenme, üreten kodu oku.

**Kural 5 — Dedup zorunlu.** Aynı (symbol, scan_date) için birden fazla satır varsa
(saatlik tarama nedeniyle vardı, %48 oranında), analiz öncesi en-erken-scan_ts'e
indir. Dedup'lanmamış hiçbir sayı raporlanamaz.

**Kural 6 — Kendi kendini denetle.** Yeni bir "kesin/çarpıcı" cümle yazdığında,
onu da Kural 1-5'e tabi tut ÖNCE yayınla değil. Bu programda heyecanlı-cümle
yazıp-sonra-düzeltme üç kez oldu; dördüncüsü olmasın.

**Kural 7 — decision-log gerçekten yazılmalı.** "Kaydedildi" demek, kaydetmek
değildir. Yazdıktan sonra `grep` ile doğrula, iddia etmeden önce değil.

---

## 2. KANIT DEFTERİ — ŞU ANA KADAR NE BİLİYORUZ (denetimin başlangıç noktası)

Aşağıdaki tablo bu programın birikmiş durumu. Denetimin görevi bunu SIFIRDAN
tekrar üretmek değil — üstüne inşa etmek, çatlak aramak, boşluk doldurmak.

### 2.1 Ayakta kalan (EVIDENCE seviyesi)

| Bulgu | Kanıt | Kaynak |
|---|---|---|
| ATR → adverse-excursion (MAE) ilişkisi | IC ~ -0.51, regime-dayanıklı, look-ahead-audit'ten sağlam çıktı | 2026-07-31, edge_recheck.py |
| Concentration-kısıtı (max-K/sektör) | Volatilite/CVaR/maxDD ~yarıya iniyor, ortalama getiri de artıyor | Strategic Lab P1(batarya1) |
| ATR-parity sizing | maxDD -%24.3→-%15.9, en iyi Sharpe | 10-Perspective P2(batarya2) |
| Score geçmişi ölçüyor, geleceği değil | past-5g ρ=0.376, ileri ρ=0.013, R1/R4/R10/A1/A2/A4 ile 5 bağımsız yoldan teyitli | Strategic Lab + Mirror Analysis |
| Score'un ana bileşenleri backward-looking | dist_52w_high ρ=0.667, past_5d_pct ρ=0.376 | Mirror Analysis L1, Q3 |
| Seçim katmanı (entry_ok) değer eksiltiyor | 3 bağımsız kontrol: rastgele-red'e karşı (-2.01pp), aynı score-bandı içinde (-0.20 vs +1.08), SPY'a karşı (-1.22pp, CI<0) | P1, Mirror L4, Q5 |
| Entry-timing sorun değil | 3 giriş noktasında (signal-close/next-open/next-close) drift yok | entry_point_drift.py, E1 |
| resolved_pct_t5 = MFE, getiri değil | kod-seviyesinde doğrulandı (`fetch_full_universe_and_retest.py:294`) | 2026-07-31 keşif, 2026-08-10 kod-teyidi |
| Etkin örneklem ~44x küçük | 27.361→~620 (evren), 799→~168 (eligible) | S1, date-block bootstrap |
| Günlük sembol-tekrarı %48 | saatlik scanner kaynaklı, yön-yanlılığı yok ama n şişiriyor | Task 21 |
| catalyst_factor ölü | tüm 53.859+ satırda sabit 0.0/boş | extension_cap_test.py + kod-teyidi |
| Rejection-katmanı karar-kalitesi kanıtsız | 26.863 reddedilenin %41.79'u counterfactual pozitif | end_to_end_decision_quality (2026-08-07) |
| Score kalibrasyonu rastgeleden kötü | Brier-skill negatif (F1, -0.019/-0.030) | Mirror Analysis F1 |

### 2.2 Kapatılan / geri çekilen (yanlış-alarm, ders çıkarılmış)

| İddia | Ne oldu | Ders |
|---|---|---|
| Composite-score reverse-ranking | Satır-bazlı güçlü → gün-kümelide IS sınırda/OOS çöktü → dedup+çeyreklik+matched-random'da tam-dönem anlamsız → KAPATILDI | Artifact-merdiveninin 4 basamağının hepsi gerekli, 1-2 basamak yeterli değil |
| Extension/exhaustion "resmi teşhis"i | 15x decile-rate → tam-popülasyon gün-kümeli doğrudan-getiri testinde monoton değil, eligible-vs-rejected extension farkı anlamsız, cap-simülasyonu iyileştirme göstermedi → hipoteze geri düşürüldü | Dolaylı-oran kanıtı (rate-by-decile), doğrudan-nedensellik kanıtı (decile-by-return) DEĞİLDİR |
| "-2.39%/+0.06%" (MFE→c2c düzeltmesinin headline sayısı) | Satır-bazlı çarpıcı → gün-kümelide t~-0.86, anlamsız | Veri-katmanı düzeltmesi doğru olabilir, headline-sayısı hâlâ kendi rigor-testini geçmeli |
| Matched "+0.50/-0.61" (confound-kontrollü versiyon) | Confound-ayrıştırması doğruydu ama gün-kümeleme atlanmış, t~-0.01/-0.86 anlamsız | İyi bir kontrol adımı (confound-ayrıştırma) kendi başına yeterli rigor değildir |
| "İki yıllık edge anlatısı" ifadesi | Üç kez tekrarlandı, hiçbir zaman kaynaklanmadı — program verisi <1 yıl | Rhetorik-iddialar da Kural 1'e tabi |
| Sektör-trend regime katmanı (143 sembol) | Gerçek-sektör etiketiyle OOS-tutarlı görünüyordu, ama tam-evren replikasyonunda (%24-doğru proxy) IS/OOS işareti tutarsız çıktı | Küçük-temiz-örneklemde çalışan bir bulgu, gürültülü-proxy'li tam-evrende otomatik doğrulanmaz |

### 2.3 Kapatılmamış / henüz kapanmamış açık kapılar (protokolün kendi listesi)

- Kapı 1.2 — fiyat sürekliliği (148/2.039 sembolde %50+ tek-gün sıçrama, EODHD adjusted-OHLC sağlamıyor)
- Kapı 1.3/1.4 — feature-lineage şeması + restatement-dedektörü (modül yazıldı, gerçek-veri taraması henüz eksiksiz değil)
- Kapı 1.5 — benchmark adjustment standardı (SPY/IWM karşılaştırmaları aynı adjustment'ta mı, doğrulanmadı)
- Kapı 3.1/3.3/3.4 — spread/ADV, intraday path, capacity-join — TAMAMEN BOŞ
- resolved_pct_t5 vs cache-korelasyonu tanım-tartışması hâlâ tam çözülmedi (üç farklı sayı: 0.86/0.325/0.55 — MFE-vs-c2c doğal ayrışmasıyla açıklandı ama kesin/tek bir sayı hâlâ yok)
- Gerçek-sektör-etiketiyle tam-evren doğrulaması (Big Bet #3) — hâlâ yeni veri (EODHD fundamentals) bekliyor
- Opsiyon-pozisyonlama pilotu (2026-07-31'de altyapı kuruldu) — hiç ağ-üzerinde çalıştırılmadı
- PR1/PR7/PR2 (kullanıcı görüşmeleri) — kit hazır, SIFIR gerçek kullanıcı teması
- G1 vol_regime backfill — Level B veri-kaynağı kararı bekliyor

---

## 3. DENETİMİN SORDUĞU SORULAR — BEŞ KÜME

### KÜME A — "Yanlış soruyu mu soruyoruz?" (strateji-kimliği sorgusu)

1. Bu programın 40+ deneyinin BÜYÜK ÇOĞUNLUĞU "score/entry_ok ileri getiriyi tahmin
   ediyor mu" sorusuna farklı açılardan cevap arıyor. Bu soru artık 5+ bağımsız
   yoldan "hayır" cevabını aldı. **Aynı soruyu altıncı, yedinci kez farklı bir
   istatistikle sormanın beklenen bilgi-kazancı nedir? Sıfıra yakınsa, neden hâlâ bu
   soru etrafında dönüyoruz?**
2. Eğer ürün kimliği "tahmin motoru" değilse (kanıtlı), ama "dikkat haritası" /
   "karar-destek" / "risk-yönetim aracı" ise — HİÇBİR deney bu üç alternatif kimliği
   DOĞRUDAN test etmedi. Şu ana kadarki tüm deneyler "tahmin" çerçevesinde kuruldu.
   **"Dikkat haritası olarak değer üretiyor mu" sorusuna nasıl bir deney tasarlarız
   — kullanıcı olmadan mı, olmadan test edilemez mi?**
3. Concentration-kısıtı ve ATR-parity sizing, tahmine gerek DUYMUYOR. Bunlar bu
   programın en sağlam iki bulgusu. **Neden araştırma bütçesinin (deney sayısı,
   zaman) çoğu hâlâ tahmin-tarafına gidiyor, kanıtlanmış-güçlü tarafa değil?** Bu
   bir önceliklendirme hatası mı?
4. Bu programın kendi S1 bulgusu (etkin-n ~620) göz önüne alındığında: **mevcut
   veri hacmiyle (85 gün, ~2.000 sembol) HERHANGİ bir kesitsel tahmin sinyalinin
   istatistiksel olarak tespit edilebilir olma ihtimali nedir?** Belki sorun
   "yanlış feature" değil, "bu örneklem büyüklüğüyle hiçbir feature ayırt
   edilemez" — bunu hiç hesapladık mı (power analysis)?

### KÜME B — Çelişki-avı (bataryalar arası tutarsızlıklar)

5. Mirror Analysis L4 diyor ki: en yüksek score-quintile İÇİNDE bile eligible <
   not-eligible. Ama entry_ok'un P0-P3 end-to-end testi (2026-08-07) entry_ok'un
   KENDİ net ortalamasını -%0.6387 olarak buluyor — mutlak negatif. **Bu ikisi
   birbirini doğruluyor mu, yoksa iki farklı karşılaştırma-grubu (rastgele vs
   aynı-bant) farklı büyüklükte etki mi gösteriyor? Büyüklükleri hiç yan yana
   konulmadı.**
6. Concentration-kısıtı testi n=52-56 gün (küçük-örneklem) ile yapıldı ve güçlü
   çıktı; ama S1 aynı döneme ~44x etkin-n küçültmesi uyguluyor. **Concentration
   bulgusu bu düzeltmeyle hâlâ anlamlı mı? Hiç gün-kümeli/etkin-n-düzeltmeli olarak
   yeniden test edilmedi — programın en güçlü bulgusu, en yeni rigor-standardından
   hiç geçmedi.**
7. PCA analizi "feature-ailesi 2-3 eksene inmiyor, 7-8/11 bileşen gerekiyor" diyor
   (redundancy düşük). Ama Mirror L1 "score'un R²=0.477'si sadece iki feature'dan
   (dist_52w_high, past_5d) geliyor" diyor (yüksek konsantrasyon). **Bu ikisi
   çelişiyor mu, yoksa "genel feature-ailesi" ile "score'un ağırlıklandırdığı
   alt-küme" arasında bir fark mı var? Netleştirilmedi.**
8. Sektör-trend-regime bulgusu (143 sembol, gerçek etiket) OOS'ta hayatta kaldı
   (%58 vs %44); ama tam-evren + %24-doğru proxy'de replike olmadı. **Bu, gerçek
   sinyalin küçük-temiz-örneklemde var olup büyük-gürültülü-örneklemde
   kaybolduğunu mü gösteriyor, yoksa 143-sembol bulgusunun kendisinin de
   (S1-standardıyla) bir şans-eseri olduğunu mu? Hiç ayrıştırılmadı.**
9. Extension/exhaustion'ın decile-rate kanıtı (15x) hâlâ dedup+gün-kümeli
   yeniden test EDİLMEDİ — sadece decile-by-RETURN testi yapıldı (o da anlamsız
   çıktı). **Orijinal rate-kanıtının kendisi hiç KURAL 2/3/5'e tabi tutulmadı —
   bu, kapatılan bulgular listesinde ama tam kapatılmamış, yarı-kapatılmış.**

### KÜME C — Gözden kaçan: HİSSE-BAZLI HETEROJENLİK (hiç sorulmadı)

Bu programın TAMAMI evreni tek bir havuz gibi ele aldı ("eligible" vs "rejected",
"top-20%" vs "bottom-20%"). **Hiçbir deney "hangi ALT-KÜME için bu sistem işe
yarıyor, hangisi için yaramıyor" sorusunu sormadı.** Bu, muhtemelen en büyük
kör nokta.

10. Sektör bazında: entry_ok'un başarı/başarısızlık oranı sektöre göre değişiyor mu?
    (Sektör-etiketi sınırlı olsa da 143-sembollük gerçek-etiket alt-kümesinde
    test edilebilir.)
11. Likidite/float bazında: düşük-float, yüksek-float isimlerde sonuçlar farklı mı?
    Squeeze-factor'ün gerçek anlamı düşük-float isimlerde daha güçlü olmalı —
    hiç kesişimli test edilmedi.
12. Fiyat-seviyesi bazında: penny-stock (<$5) vs orta-fiyat vs yüksek-fiyat
    isimlerde entry_ok'un performansı farklı mı? (148 flagged-sembolün çoğu
    muhtemelen düşük-fiyatlı/yüksek-oynaklıklı isimler — bu kesişim hiç
    incelenmedi.)
13. Listing-yaşı/piyasa-değeri bazında: yeni-halka-açılan, mikro-cap isimler
    sistemi mi bozuyor, yoksa gerçek sinyal mi taşıyor?
14. ATR/volatilite-rejimi bazında: yüksek-ATR isimlerde mi, düşük-ATR isimlerde mi
    entry_ok daha az kötü? (M1 bulgusu "yüksek-rvol eligible en kötü kohort"
    diyor — bu rvol için yapıldı, ATR-rejimi için sistematik yapılmadı.)
15. **En kritik soru:** entry_ok'un -%2.39 (veya hangi düzeltilmiş sayı doğruysa)
    medyanı, TÜM eligible isimlerde homojen mi, yoksa küçük bir "felaket alt-kümesi"
    (örn. 148 flagged sembol, veya belirli bir sektör, veya belirli bir fiyat-bandı)
    ortalamayı mı çekiyor? Eğer öyleyse, "seçim değer eksiltiyor" sonucu GENELDEĞİL,
    "seçim belirli bir riskli-alt-kümeye aşırı-maruz kalıyor" sonucuna dönüşür — ki
    bu ÇOK DAHA AKSİYON-ALINABİLİR bir teşhistir (basit bir exclusion-filtresi ile
    düzeltilebilir, score'un tamamen yeniden yazılmasını gerektirmez).

### KÜME D — Gözden kaçan: kullanılmayan veri ve mekanizmalar

16. Opsiyon-pozisyonlama pilotu (put/call OI, IV, skew) 2026-07-31'de kodlandı,
    hiç ağ-üzerinde koşulmadı. **Bu, "kolay-erişilebilir fiyat/hacim verisi
    tükendi" iddiasının test edilmemiş tek karşı-örneği — neden hâlâ bekliyor?**
17. FINRA short-interest verisi (gerçek, factor-proxy değil) hiç kullanılmadı —
    yalnız `squeeze_factor` proxy'si var. Gerçek short-interest verisi
    squeeze-hipotezini çok daha güçlü test edebilir.
18. Path-aware exit hedefleri (MFE-capture, time-to-event) X1/X3'te motive edildi
    ama hiç GERÇEKTEN inşa edilmedi (sadece "bunu düşünmeliyiz" seviyesinde kaldı).
    **Bu, programın en iyi-kanıtlanmış "yeni yön" fikri — neden hâlâ bir hipotez,
    bir prototip değil?**
19. Lottery_factor ve overnight_gap_factor'ün NEGATİF ileri-bilgi taşıdığı bulundu
    (Q2/Q3) — ama hiçbir deney "score'u bu iki feature'ı DOĞRU yönde ağırlıklandırarak
    yeniden inşa edersek ne olur" simülasyonunu yapmadı. Bu, en ucuz/en hızlı
    test edilebilir yeni hipotez ve hiç denenmedi.
20. Unsupervised-regime (A1) "dominant regime'ler veri-artefaktı" buldu (n=18/1/1
    kümeler) — bu kümelerin GERÇEKTEN hangi sembol/tarihler olduğu hiç açılmadı.
    148-flagged-sembol listesiyle örtüşüyor mu? Kontrol edilmedi.

### KÜME E — Gözden kaçan: süreç ve ölçüm

21. Bu programda KAÇ TOPLAM konfigürasyon/hipotez test edildi (deney-bütçesi)?
    Kabaca: 2.520 (barrier-grid) + 3.120 (fixed-target) + 4.000 (ağırlık-arama) +
    74 (2-faktör kombo) + ~40 (bu yaz) = **~9.750+ ayrı test.** Bu sayı hiçbir
    raporda TEK bir toplamda görünmedi. **9.750 testten "hiçbiri baseline'ı stabil
    geçmedi" (2026-07-31 bulgusu) sonucu, aslında GÜÇLÜ bir null-sonuç — ama kimse
    bunu "9.750 denemede sıfır" diye çerçevelemedi. Bu çerçeve, multiple-testing
    düzeltmesi açısından ne anlama geliyor?**
22. Şu ana kadarki HİÇBİR deney, "eğer rastgele 9.750 konfigürasyon denesek, kaçının
    şans eseri 'anlamlı' çıkmasını beklerdik" sorusunu (false-discovery-rate
    simülasyonu) sormadı. Q4 (10-Perspective) null-feature-injection ile buna
    yakın bir şey yaptı (p95 |ρ|=0.011) ama TÜM programın toplu deney-sayısına
    uygulanmadı.
23. Veri sağlayıcı (EODHD/Alpaca) tarihsel barları SESSİZCE REVİZE EDİYOR MU
    (restatement)? Modül yazıldı (1.4) ama gerçek-veri taraması eksiksiz
    tamamlanmadı — bu, TÜM geçmiş sonuçların ne kadar "sabit" olduğunu etkiler.

---

## 4. "NEDEN BAZI HİSSELER DAHA İYİ SONUÇ VERİYOR?" — AYRI, ÖZEL BÖLÜM

Bu soru Küme C'nin özel bir versiyonu ama tek başına bir araştırma hattı hak ediyor.
Denetim şu alt-soruları sırayla açmalı:

1. **Tanım:** "Daha iyi sonuç veren hisse" ne demek — daha sık mı entry_ok'a
   giriyor, entry_ok'a girdiğinde daha mı iyi getiri veriyor, yoksa her ikisi mi?
   Bunlar farklı sorular ve farklı cevapları olabilir.
2. **Kalıcılık testi:** Bir ismin "iyi sonuç verdiği" bir dönem, sonraki dönemde
   tekrarlıyor mu (sembol-bazlı otokorelasyon)? Yoksa her dönem farklı isimler
   "iyi" çıkıyor mu (ki bu, gerçek bir sembol-özelliği değil, gürültü olduğunu
   gösterir)?
3. **Karakteristik-ayrıştırma:** Eğer kalıcılık varsa, hangi STATİK özellik
   (sektör, piyasa-değeri, float, ortalama-ATR, listing-yaşı, ortalama-hacim) bu
   kalıcılığı açıklıyor? Bunu test etmenin doğru yolu: sembolleri bu özelliklere
   göre gruplandır, HER GRUP İÇİNDE ayrı ayrı gün-kümeli/etkin-n-düzeltmeli
   entry_ok-performansı hesapla, gruplar arası farkı matched-random-kontrolle
   karşılaştır.
4. **Alternatif açıklama (null-hipotez):** Belki "bazı hisseler daha iyi" diye
   görünen şey, sadece o hisselerin DAHA SEYREK entry_ok'a girmesi ve seyrek-giren
   isimlerin varyansının (küçük-n nedeniyle) daha yüksek olması — yani gerçek bir
   heterojenlik değil, küçük-örneklem gürültüsü. Bu, HER heterojenlik-iddiasının
   önce elenmesi gereken ilk alternatif açıklama.
5. **Aksiyon-testi:** Eğer gerçek ve kalıcı bir alt-küme bulunursa (örn. "yalnız
   orta-cap, yüksek-likidite, teknoloji-dışı sektörlerde entry_ok pozitif medyan
   veriyor"), bu alt-kümeye sistemi KISITLAMANIN (evreni küçültme) genel
   performansı iyileştirip iyileştirmediğini test et — matched-random-kontrolle,
   yeni bir zaman-penceresinde (aynı veriyle çift-batma riski var).

---

## 5. İSTENEN ÇIKTI FORMATI

Bu promptu çalıştıran denetim, aşağıdaki bölümleri ÜRETMEK ZORUNDADIR:

1. **Kanıt-defteri güncellemesi** — §2'deki tabloya eklenen/düzeltilen satırlar,
   her biri Kural 1 etiketiyle.
2. **Çelişki haritası** — Küme B'deki her soru için: çelişki gerçek mi, yoksa
   açıklanabilir mi (farklı karşılaştırma-grubu, farklı örneklem, farklı tanım)?
3. **Gözden kaçan liste** — Küme C/D/E'den hangi sorular test edilebilir durumda
   (mevcut veriyle), hangileri yeni veri gerektiriyor — ayrı ayrı işaretli.
4. **Yeni hipotez kaydı** — her yeni fikir, Pre-Registration formatında (bkz.
   `reports/preregistration_three_hypotheses_2026-08-10.md` şablonu): keşif-sinyali,
   neden-şüpheli-olmalıyız, confirmatory-tasarım, success/kill-kriteri.
5. **"Yanlış strateji mi?" resmi verdikt** — Küme A'nın 4 sorusuna doğrudan cevap:
   devam mı, pivot mu, dondur mu.
6. **Öncelik-sıralı sıradaki-3-deney listesi** — hangi 3 açık soru en yüksek
   bilgi/maliyet oranına sahip, hangi sırayla koşulmalı.
7. **Kendi-kendini-denetim eki** — bu çıktının kendisinde Kural 1-7'den hangisi
   ihlal edilmiş olabilir, dürüstçe işaretlenmiş.

---

## 6. SON KURAL

Bu belgeyi çalıştıran kim olursa olsun (insan, ajan, gelecekteki bir oturum):
**hiçbir yeni "bulgu" decision-log'a Kural 1-7 uygulanmadan girmez, ve girdiğini
iddia etmeden önce gerçekten yazıldığı `grep` ile doğrulanır.** Bu programın
ödediği en büyük bedel, heyecanın doğrulamadan önce gelmesiydi. Bu belge, o
sırayı kalıcı olarak tersine çevirmek için var.
