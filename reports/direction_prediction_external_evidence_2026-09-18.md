# FinPilot — Yön Tahmini: Dış Kanıt ve Literatür Taraması

Master Prompt v1.0 (2026-09-18) uygulaması · Level A · Üretim/kod/veri değişikliği YOK · Tahmin üretilmedi · Ticaret iddiası yok

**Kapsam notu:** Bu rapor *dış* kanıt toplar. Hiçbir yerde "bu bizim evrenimizde çalışır" demez. FinPilot iç bulguları SABİT bağlam olarak alınmıştır, yeniden türetilmemiştir.

---

## 1. Executive Summary

1. **1-5 günlük yatay yön tahmini için güçlü, kopyalanmış, maliyet-sonrası akademik kanıt yok denecek kadar az.** Literatürdeki sağlam yön etkilerinin neredeyse tamamı **aylık-yıllık** ufuklarda.
2. Kısa ufukta belgelenmiş tek sağlam yapı **short-term reversal**, ve o da küçük hisselerde işlem maliyetiyle **ölüyor** (TIER A).
3. **En güçlü, en tekrarlanmış kısa-ufuk bulguları YÖN olarak NEGATİF.** Dikkat çeken hisseler, lottery hisseleri ve yüksek short-interest hisseleri sistematik olarak **düşük** getiri veriyor.
4. **Bu, FinPilot'ın kendi bulgusuyla birebir örtüşüyor.** Attention map'in "negatif medyan getiri" sonucu bir anomali değil — Barber/Huang/Odean/Schwarz (2022, JF) Robinhood verisinde aynı şeyi buluyor: en çok alınan hisseler 20 günde ortalama **−%4.7** anormal getiri.
5. **Bunun anlamı:** FinPilot'ın dedektörü muhtemelen gerçek ve iyi belgelenmiş bir etkiye işaret ediyor — ama **işareti "al" değil, "kaçın/sat"**.
6. Beş aday kaynaktan hiçbiri 1-5 gün ufkunda TIER A yön kanıtına sahip değil. En yakınları: **8-K olay sürüklenmesi** (TIER B) ve **LLM haber duyarlılığı** (TIER C, hızla aşınıyor).
7. Insider Form 4 kanıtı güçlü ama **12 aylık ufukta** ve **küçük hisselerde** — bizim ufkumuzla uyuşmuyor.
8. Short interest kanıtındaki asimetri gözden kaçmamalı: Boehmer ve ark. (2010) **düşük** short interest'in pozitif tarafını, yüksek short interest'in negatif tarafından **daha güçlü** buluyor.
9. McLean & Pontiff (2016, JF): yayın sonrası getiriler **%58 düşüyor**. Literatürden alınan her etkiyi bu iskonto ile okumak zorunlu.
10. Retail maliyet gerçeği: S&P 500'de ~4.5 bp/işlem, ama küçük/illikit isimlerde **round-trip 50 bp üzeri**. FinPilot'ın %1 varsayımı abartı değil, gerçekçi.
11. PEAD hâlâ var ama **zayıflıyor** ve maliyet sonrası hayatta kalıp kalmadığı **tartışmalı**.
12. 52-hafta zirvesi etkisi (George & Hwang) gerçek, ama **momentum ufkunda** (aylar) — bizim `dist_52w_high` bulgumuzla çelişmesi ufuk farkıyla açıklanabilir.
13. **Dürüst cevap:** 1-5 gün ufkunda, retail maliyetleriyle, güvenilir yön tahmini büyük ölçüde **desteklenmiyor**.
14. **Savunulabilir olan:** yön tahmini değil, **kaçınma/risk filtresi**. Bunun için hem dış TIER A kanıt hem de FinPilot iç verisi aynı yöne işaret ediyor.
15. Önerilen tek deney bu yüzden bir "al sinyali" değil, bir **negatif eleme** testi (Bölüm 7).

---

## 2. Kanıt Tablosu

| Sinyal | Tier | Etki büyüklüğü | Ufuk | Dönem/Piyasa | Maliyet sonrası | Aşınma |
|---|---|---|---|---|---|---|
| **Attention → negatif getiri** (Barber, Huang, Odean, Schwarz 2022, JF) | **A** | En çok alınan hisseler **−%4.7** anormal | 20 gün | 2018-2020, ABD Robinhood | Short tarafı maliyetli; *kaçınma* olarak maliyetsiz | Yeni, aşınma ölçülmedi |
| **MAX / lottery etkisi** (Bali, Cakici, Whitelaw 2011, JFE) | **A** | En düşük-en yüksek MAX decile farkı **>%1/ay** | 1 ay | 1962-2005, NYSE/AMEX/NASDAQ | Değerlendirilmedi (aylık, düşük devir) | Yayın sonrası aşınma bekleniyor |
| **Short-term reversal** (Jegadeesh 1990; de Groot, Huij, Zhou 2012) | **A** | Ham etki güçlü; net **30-50 bp/hafta** ama YALNIZCA büyük hisselerde + düşük devirle | 1 hafta | ABD | **Geniş evrende maliyet etkiyi yiyor** | Bilinen |
| **Insider alım (Form 4)** (Lakonishok & Lee 2001; Seyhun) | **A** | En yoğun alım decile ~**%5** fark; küçük hisselerde ~%7.4 | **12 ay** | 1975-1995, ABD | Uzun ufuk → düşük devir, maliyet toleranslı | Post-2000 zayıflama rapor edildi |
| **Short interest (yüksek → negatif)** (Boehmer, Huszár, Jordan 2010, JFE) | **A** | Negatif anormal getiri, ama yazarların kendi ifadesiyle "geçici ve ekonomik önemi tartışmalı" | Haftalar-aylar | ABD | Short maliyeti + borçlanma ücreti | — |
| **Short interest (DÜŞÜK → pozitif)** (aynı çalışma) | **A** | Pozitif anormal getiri, **mutlak değerce daha büyük**; bilgi yavaş fiyatlanıyor | Haftalar-aylar | ABD | Long taraf → retail'e uygun | — |
| **PEAD** (Ball & Brown 1968; Bernard & Thomas 1989) | **A→B** | Tarihsel güçlü, **magnitüd düşüyor**, bazı örneklemlerde anlamsızlığa kadar | Günler-3 ay | ABD | **Tartışmalı** — bazı çalışmalar maliyet sonrası yok olduğunu, bazıları kaldığını buluyor | Belgelenmiş düşüş |
| **8-K olay sürüklenmesi** (Lerman & Livnat 2010, RASt) | **B** | Bazı item kodlarında beklenen yönde anlamlı drift | **90 güne kadar** | 2004 sonrası ABD | Ölçülmedi | — |
| **LLM haber duyarlılığı** (Lopez-Lira & Tang 2023, SSRN 4412788) | **C** | Ertesi-gün long-short anlamlı Sharpe | **1 gün** | 2021-2023 ABD | Ölçüm sınırlı | **Yazarlar aşınma raporluyor**: LLM benimsenmesi arttıkça getiri düşüyor |
| **52-hafta zirvesi momentumu** (George & Hwang 2004, JF) | **A** | Geçmiş getirilerin öngörü gücünü **domine ediyor**; uzun vadede tersine dönmüyor | **6-12 ay** | ABD + uluslararası | Aylık devir → tolere edilebilir | McLean-Pontiff kapsamında |
| **Gece/gün-içi ayrışması** (Lou, Polk, Skouras) | **B** | Gece ve gün-içi getiriler zıt işaretli kalıcı yapı | Günlük | ABD | Gece pozisyonu = gap riski | UNVERIFIED (bu turda birincil kaynak doğrulanamadı) |
| **Overnight gap mean-reversion S&P 500** (MDPI 2019) | **D** | İddia: %51.47 p.a., Sharpe 2.38 | Gün-içi | S&P 500 | "maliyet sonrası" iddiası | **ŞÜPHELİ** — düşük hakemlik eşiği, bağımsız replikasyon yok |
| **Yayın sonrası aşınma** (McLean & Pontiff 2016, JF) | **A** | **OOS −%26, yayın sonrası −%58** | — | 97 değişken | — | Meta-bulgu |

---

## 3. Beş Aday Kaynak Kartı

### 1) Short interest (ΔSI) — `finra_cache`, iki haftada bir, 2017-2026

```
DIŞ YÖN KANITI      : TIER A (Boehmer, Huszár, Jordan 2010, JFE 96:80-97)
                      Yüksek SI → negatif, ama "geçici, ekonomik önemi tartışmalı".
                      DÜŞÜK SI + yoğun işlem → pozitif, mutlak değerce DAHA BÜYÜK.
REPLİKASYON         : Replike edilmiş (Asquith, Desai/Ramesh, Akbas 2017 hattı)
MALİYET HASSASİYETİ : Short tarafı retail için pahalı (borçlanma + short maliyeti).
                      LONG tarafı (düşük SI) retail'e uygun — az konuşulan taraf.
BİZDEKİ VERİ        : Yeterli-ish. İki haftalık frekans 1-5 gün ufku için KABA.
VERİ BOŞLUĞU        : Günlük SI yok; days-to-cover ve borçlanma ücreti yok.
FİZİBİLİTE          : ORTA
NET KARAR           : TEST-CAREFULLY — ama LONG/düşük-SI tarafını test et,
                      yüksek-SI short tarafını değil. Ufuk uyumsuzluğu ana risk.
```

### 2) Insider alımı (Form 4) — `edgar_cache`, buy/sell parse gerekiyor

```
DIŞ YÖN KANITI      : TIER A ama UFUK UYUMSUZ.
                      Lakonishok & Lee (2001): ~%5/12 ay, küçük hisselerde ~%7.4.
                      Seyhun: %4.3 / 300 gün. ALIMLAR bilgilendirici, SATIŞLAR DEĞİL.
REPLİKASYON         : Güçlü, çok kez replike
MALİYET HASSASİYETİ : 12 aylık ufuk → düşük devir → maliyet toleransı YÜKSEK
BİZDEKİ VERİ        : Kısmi — edgar_cache var ama buy/sell ayrıştırması yazılmamış
VERİ BOŞLUĞU        : Form 4 transaction code parse (P=alım, S=satış), tutar, rol
FİZİBİLİTE          : YÜKSEK (veri elimizde, sadece parser lazım)
NET KARAR           : DEPRIORITIZE (1-5 gün için) / PURSUE (eğer ufku uzatırsak)
                      >> Bu, ufku değiştirme kararının en güçlü argümanı.
```

### 3) 8-K maddi olaylar — `edgar_cache`, ton sınıflandırma gerekiyor

```
DIŞ YÖN KANITI      : TIER B (Lerman & Livnat 2010, Review of Accounting Studies)
                      Tüm item'lar anormal hacim/volatilite; BAZI item'lar
                      beklenen yönde 90 güne kadar anlamlı drift.
REPLİKASYON         : Tek ana çalışma hattı; item bazında heterojen
MALİYET HASSASİYETİ : ÖLÇÜLMEDİ — literatürde net maliyet analizi bulunamadı
BİZDEKİ VERİ        : Kısmi — edgar_cache var, item-kod sınıflandırması yok
VERİ BOŞLUĞU        : Item kodu ayrıştırma + ton sınıflandırma. NOT: arXiv 2607.08346
                      item-kod taksonomisinin heterojen olduğunu, tek item'ın çok
                      farklı ekonomik öneme sahip olayları kapsadığını belirtiyor.
FİZİBİLİTE          : ORTA
NET KARAR           : TEST-CAREFULLY — kısa ufukta drift gösteren TEK yapısal aday.
                      Ama item-bazında ayrıştırma yapılmadan test edilirse gürültü olur.
```

### 4) Haber duyarlılığı — `news_cache` (skor anlamı belirsiz, ~0.99 sabit)

```
DIŞ YÖN KANITI      : TIER C (Lopez-Lira & Tang 2023, SSRN 4412788 / arXiv 2304.07619)
                      GPT tabanlı başlık skoru ertesi-gün getiriyi öngörüyor,
                      geleneksel sözlük yöntemlerini yeniyor.
                      Tetlock (2007) hattı TIER A ama etki aylık ve zayıf.
REPLİKASYON         : Yeni; bağımsız replikasyon sınırlı
MALİYET HASSASİYETİ : Günlük devir → maliyet baskısı YÜKSEK
AŞINMA UYARISI      : Yazarların KENDİ bulgusu — LLM benimsenmesi arttıkça
                      strateji getirisi düşüyor. 2023'teki etki 2026'da aynı olmayabilir.
BİZDEKİ VERİ        : BOZUK — skor ~0.99 sabit, varyans yok, anlamı belirsiz
VERİ BOŞLUĞU        : Ham başlık metni + kendi skorlamamız. Mevcut skor kullanılamaz.
FİZİBİLİTE          : DÜŞÜK (mevcut haliyle) / ORTA (ham metinle yeniden kurulursa)
NET KARAR           : DEPRIORITIZE — veri bozuk, etki aşınıyor, maliyet baskısı yüksek.
                      Önce news_cache'in neden sabit olduğu teşhis edilmeli (DATA_REPAIR).
```

### 5) float / short_pct seviyesi — `fundamentals_cache` (snapshot, point-in-time DEĞİL)

```
DIŞ YÖN KANITI      : Seviye olarak ZAYIF. Literatürdeki etki DEĞİŞİM (ΔSI) ve
                      short-squeeze koşullarında; statik seviyede yön kanıtı zayıf.
REPLİKASYON         : —
MALİYET HASSASİYETİ : —
BİZDEKİ VERİ        : YAPISAL SORUNLU — snapshot, point-in-time değil.
                      >> Bu, geriye dönük testte LOOK-AHEAD BIAS demektir.
VERİ BOŞLUĞU        : Point-in-time float/short geçmişi
FİZİBİLİTE          : DÜŞÜK
NET KARAR           : KILL (mevcut veriyle). Point-in-time olmadan yapılacak her
                      test kendini kandırır. Bu bir öncelik sorunu değil,
                      bir veri-geçerliliği sorunu.
```

---

## 4. Kill List — bu ufukta çalışmadığı belgelenen / bizde test edilemeyecek olanlar

| Bırakılacak | Neden |
|---|---|
| **Geniş evrende short-term reversal** | TIER A: maliyet etkiden büyük (de Groot/Huij/Zhou 2012; Avramov ve ark. 2006). Sadece büyük-cap + düşük devirle yaşıyor. Bizim evrenimiz küçük hisse ağırlıklı. |
| **float/short_pct seviyesi (snapshot)** | Point-in-time değil → look-ahead bias. Test edilemez. |
| **Mevcut haliyle news_cache** | Skor ~0.99 sabit, varyans yok. Sinyal değil, sabit. |
| **Insider Form 4, 1-5 gün ufkunda** | Kanıt 12 aylık ufukta. Ufku değiştirmeden anlamsız. |
| **Yüksek short-interest'i LONG sinyali sanmak** | Literatür tam tersi yönde. Squeeze istisnai koşul, kural değil. |
| **"Attention = al" yorumu** | TIER A kanıt bunun tersini söylüyor (−%4.7 / 20 gün). |
| **MDPI tarzı yüksek-Sharpe gap iddiaları** | TIER D. Bağımsız replikasyon yok. Bu tür iddialar bu programda zaten bir kez (composite reverse-ranking) artefakt çıktı. |

---

## 5. Reconciliation — dört zorunlu soru

### 5.1 Hareket ≠ Yön. Kısa ufukta UP/DOWN ayıran, maliyet sonrası pozitif beklentili bir sinyal var mı?

**Kısa cevap: Genel olarak hayır — ve literatür bizim bulduğumuz yönü destekliyor.**

Kısa ufukta güçlü ve tekrarlanmış olan yapıların yönü **negatif**: dikkat (Barber ve ark. 2022, −%4.7/20 gün), lottery/MAX (Bali ve ark. 2011, >%1/ay ters yönde), yüksek short interest (Boehmer ve ark. 2010). Pozitif tarafta kısa ufukta elde kalan tek şey short-term reversal, o da küçük hisselerde maliyetle ölüyor.

Yani: **"büyük hareket edecek" tespiti ile "yukarı gidecek" tespiti arasındaki boşluk, literatürde de kapatılamamış.** Bu bizim başarısızlığımız değil, alanın durumu. FinPilot'ın 8 bağımsız yön testinin başarısız olması, dış kanıtla **tutarlı** bir sonuç.

### 5.2 `dist_52w_high` çelişkisi

George & Hwang (2004) etkisi **6-12 aylık momentum ufkunda**, ve bir **cross-sectional sıralama** sinyali olarak çalışıyor. Bizim bulgumuz (composite ile 0.64 korelasyon, non-monotonik/ters) **1-5 gün ufkunda** ve **redundancy** ölçümü.

İki olası açıklama, ikisi de test edilmemiş:
- **Ufuk farkı:** etki aylarda var, günlerde yok. Literatürle çelişmiyoruz, farklı şeyi ölçüyoruz.
- **Yapısal redundancy:** `dist_52w_high` bizim composite'imizin içinde zaten dolaylı olarak kodlanmış (0.64), dolayısıyla ek bilgi taşımıyor — bu, etkinin yokluğu değil, **ölçümün çift sayması** olabilir.

**Karar: ÇELİŞKİ YOK, UFUK UYUMSUZLUĞU VAR.** Literatürü bizim sonucumuzu çürütmek için kullanamayız, tersi de geçerli.

### 5.3 Negatif medyan problemi — dikkat çeken hisseler gerçekten düşük mü getiriyor?

**EVET, ve bu TIER A kanıtla destekleniyor.** Bu, raporun en net sonucu.

- Barber, Huang, Odean, Schwarz (2022, *Journal of Finance*): Robinhood'da en yoğun alınan hisseler **20 günde ortalama −%4.7 anormal getiri**.
- Barber & Odean (2008, *RFS*): yatırımcılar dikkat çeken hisselerin **net alıcısı** oluyor — sinyalin yönünden bağımsız olarak.
- Bali, Cakici, Whitelaw (2011, *JFE*): lottery benzeri hisseler aşırı fiyatlanıyor, sonrasında düşük getiri veriyor.

**Sonuç:** FinPilot'ın attention map'i (%62.1 büyük-hareket precision, 1.7-3.3× lift, medyan getiri −%2.32, büyük-kaybeden oranı %39.4 vs %15.1) literatürdeki **attention/lottery aşırı-fiyatlama** olgusunun bağımsız bir tekrarı gibi görünüyor.

**Bunun ürün anlamı:** dedektör bozuk değil. **Yanlış yöne okunuyor.** Bu bir *long* sinyali değil, bir *kaçınma/short* sinyali.

⚠️ Uyarı: "short sinyali" demek "short al" demek değil. Short tarafı retail için borçlanma ücreti, sınırsız risk ve locate sorunları taşır. **Savunulabilir kullanım: portföyden ELEME.**

### 5.4 Fade sorusu — açılış aralığı fade'i retail maliyetiyle yaşıyor mu?

**Hayır, ikna edici kanıt bulunamadı.**

- Akademik hat (de Groot/Huij/Zhou 2012) net: temel reversal stratejisinin kârı geniş evrende işlem maliyetinden **küçük**. Yaşadığı yer büyük-cap + düşük devir.
- Gap/fade özelinde bulduğum tek "maliyet sonrası pozitif" iddia bir **MDPI** makalesi (%51.47 p.a., Sharpe 2.38) — **TIER D**, bağımsız replikasyon yok, bu tür Sharpe iddiaları bu literatürde kural olarak replike olmuyor.
- Maliyet gerçeği bunu destekliyor: S&P 500'de ~4.5 bp/işlem, ama **küçük/illikit isimlerde round-trip 50 bp üzeri**. FinPilot'ın kullandığı %1 varsayımı abartılı değil.

**Sonuç: FinPilot'ın kendi bulgusu (brüt %59.9 ama %1 maliyette negatif) dış kanıtla TUTARLI.** Fade'in CONFIRMATORY_CANDIDATE statüsü korunmalı; dış literatür onu terfi ettirmiyor.

---

## 6. Veri Boşluğu Listesi

| İhtiyaç | Hangi sinyal için | Şu anki durum | Zorluk |
|---|---|---|---|
| Form 4 transaction-code parse (P/S, tutar, rol) | Insider alımı | edgar_cache var, parser yok | **DÜŞÜK** |
| 8-K item kodu + ton sınıflandırma | Olay sürüklenmesi | edgar_cache var, sınıflandırma yok | ORTA |
| Ham haber başlık metni | LLM duyarlılığı | news_cache skoru bozuk (~0.99 sabit) | ORTA |
| Point-in-time float / short_pct geçmişi | float/short seviyesi | Sadece snapshot → look-ahead | **YÜKSEK** |
| Günlük (iki-haftalık değil) short interest | ΔSI kısa ufuk | FINRA iki haftada bir yayınlıyor | **YAPISAL — çözülemez** |
| Gerçekleşen işlem maliyeti / spread verisi | Her maliyet-sonrası test | Yok; %1 varsayımı kullanılıyor | ORTA |

---

## 7. Önerilen TEK Deney (ön-kayıt taslağı)

Literatürün en güçlü (TIER A) ve FinPilot iç verisiyle **en uyumlu** sonucu, dikkat/lottery hisselerinin düşük getiri verdiğidir. Test edilecek şey bu yüzden bir al-sinyali değil, bir **eleme filtresi**.

```
DENEY ADI    : Attention-as-Negative-Screen (ANS-1)

HİPOTEZ (H1) : Attention-flag'li hisselerin portföyden ELENMESİ, elenmemiş
               duruma göre medyan 5-günlük getiriyi İYİLEŞTİRİR.

YÖN          : Önceden belirlendi — POZİTİF iyileşme bekleniyor.
               (Barber ve ark. 2022 ve Bali ve ark. 2011'den türetilmiş,
                bizim verimizden değil. Bu bir DIŞ-kaynaklı hipotez —
                mühürlenmiş-keşif ihlali değil.)

BİRİNCİL ÖLÇÜT: Elenmemiş evren medyan c2c_5d − elenmiş evren medyan c2c_5d
                (gün-kümelenmiş, block-bootstrap CI, blok=5, B=5000)

İKİNCİL       : büyük-kaybeden oranı (<-%10) farkı; hit-rate farkı

KONTROL       : (a) eşleştirilmiş-rastgele eleme (aynı sayıda hisseyi rastgele ele)
                (b) null-shuffle (flag'leri karıştır)
                Gerçek eleme her iki kontrolü de aşmalı.

BAŞARI EŞİĞİ  : medyan iyileşme > 0 VE block-bootstrap %95 CI sıfırı içermiyor
                VE eşleştirilmiş-rastgele kontrolünü aşıyor
                VE global çoklu-test eşiğini geçiyor (m_total mevcut bütçeye +1)

KILL KRİTERİ  : Yukarıdakilerden HERHANGİ BİRİ sağlanmazsa → NOT SUPPORTED.
                Eşik sonradan gevşetilmez. Alt-dilim aranmaz.

MALİYET NOTU  : Bu test MALİYET GEREKTİRMEZ — eleme bir işlem değil.
                Fade/short testlerinin aksine maliyet bariyeri YOK.
                >> Bu, onu tüm adaylar arasında en ucuz ve en dürüst test yapıyor.

VERİ          : Mevcut. Yeni feed GEREKMİYOR.

NE KANITLAMAZ : "Kâr edilir" demez. Yalnızca "bu hisseleri elemek
                sonucu iyileştiriyor mu" sorusunu cevaplar.
```

**Neden bu deney:** Tek adayda hem (a) TIER A dış kanıt var, hem (b) FinPilot iç verisi aynı yöne işaret ediyor, hem (c) yeni veri gerekmiyor, hem (d) **işlem maliyeti bariyeri yok** — ki bu son madde, programın diğer tüm adaylarını (fade, reversal, short) öldüren şeydi.

---

## 8. Güven Düzeyleri

| İfade | Güven | Dayanak |
|---|---|---|
| Dikkat çeken hisseler kısa ufukta düşük getiri verir | **YÜKSEK** | TIER A, JF 2022, büyük örneklem |
| Lottery/MAX hisseleri aşırı fiyatlanır | **YÜKSEK** | TIER A, JFE 2011, 43 yıllık örneklem |
| Geniş evrende kısa-vadeli reversal maliyetle ölür | **YÜKSEK** | TIER A, çoklu çalışma |
| Yayınlanan etkiler ~%58 aşınır | **YÜKSEK** | TIER A, JF 2016, 97 değişken |
| Insider alımı bilgilendiricidir | **YÜKSEK ama ufuk 12 ay** | TIER A |
| 8-K item'ları kısa ufuk drift taşır | **ORTA** | TIER B, tek çalışma hattı, item-heterojen |
| LLM haber duyarlılığı ertesi-gün öngörür | **DÜŞÜK-ORTA** | TIER C, yeni, yazarların kendisi aşınma raporluyor |
| Gap fade retail maliyetiyle yaşar | **ÇOK DÜŞÜK** | Yalnızca TIER D iddia |
| **Bu etkilerin FinPilot evreninde geçerli olduğu** | **BİLİNMİYOR** | Hiçbiri bizim verimizde test edilmedi |

> Son satır kritik: bu raporun tamamı **başkalarının verisi** hakkındadır. Hiçbiri FinPilot evreninde doğrulanmış sayılamaz.

---

## 9. Mevcut Governance Kararlarıyla Etkileşim

Bu tur hiçbir sınıflandırmayı değiştirmez. Gözlemler:

- **Attention map — VALIDATED-DESCRIPTIVE-RESEARCH:** korunuyor. Bu rapor onu "yön tahmincisi" yapmıyor; aksine **negatif yönlü** okunması gerektiğine dair dış kanıt ekliyor. Yeniden sınıflandırma önerilmiyor; §7 deneyi bunu test edecek.
- **Opening-range fade — CONFIRMATORY_CANDIDATE:** korunuyor. Dış literatür terfi gerekçesi sağlamıyor; üç koşul yerinde kalıyor.
- **Feature flag kararı — DEFERRED:** korunuyor. Ancak `lottery_factor`'ın negatif yönü artık **dış TIER A kanıtla uyumlu** (Bali ve ark. 2011) — bu, onu "kaldırılacak" değil, "doğru yönde çalışıyor olabilir" sütununa taşır. Karar yine de baseline çözülene kadar ertelenmiş.
- **Catalyst — UNVALIDATED / DATA PIPELINE REGRESSION:** korunuyor, bu tur dokunmadı.

**PROPOSED GOVERNANCE ACTION (öneri, uygulanmadı):**
Yeni bir kanıt sınıfı eklensin: **EXTERNAL-EVIDENCE (TIER A/B/C/D)**. Şu an taksonomide dış literatür kanıtını iç bulgudan ayıran resmi bir etiket yok; bu rapordaki her iddia bu ayrımı elle taşıyor. Etiket olmadan gelecek turlarda ikisinin karışma riski yüksek.

---

## 10. Kaynaklar

Tümü bu tur içinde arama ile doğrulandı. Doğrulanamayanlar **UNVERIFIED** işaretlidir.

- Boehmer, Huszár, Jordan (2010), "The good news in short interest," *Journal of Financial Economics* 96(1):80-97 — https://www.sciencedirect.com/science/article/abs/pii/S0304405X09002402
- Akbas (2017), "Short Interest, Returns, and Unfavorable Fundamental Information," *Financial Management* — https://onlinelibrary.wiley.com/doi/10.1111/fima.12144
- Lakonishok & Lee (2001), "Are Insider Trades Informative?" — https://www.lsvasset.com/pdf/research-papers/Insider-Trades-Informative.pdf
- Seyhun, "Estimating the Returns to Insider Trading" (Wharton/Rodney White) — https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/9919.pdf
- Barber, Huang, Odean, Schwarz (2022), "Attention-Induced Trading and Returns: Evidence from Robinhood Users," *Journal of Finance* — https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13183
- Barber & Odean (2008), "All That Glitters," *Review of Financial Studies* — https://faculty.haas.berkeley.edu/odean/papers%20current%20versions/allthatglitters_rfs_2008.pdf
- Bali, Cakici, Whitelaw (2011), "Maxing out: Stocks as lotteries and the cross-section of expected returns," *JFE* — https://pages.stern.nyu.edu/~rwhitela/papers/max%20jfe11.pdf
- George & Hwang (2004), "The 52-Week High and Momentum Investing," *Journal of Finance* — https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00695.x
- de Groot, Huij, Zhou (2012), "Another look at trading costs and short-term reversal profits," *Journal of Banking & Finance* — https://www.sciencedirect.com/science/article/abs/pii/S0378426611002263
- McLean & Pontiff (2016), "Does Academic Research Destroy Stock Return Predictability?" *Journal of Finance* — https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365
- Lopez-Lira & Tang (2023), "Can ChatGPT Forecast Stock Price Movements?" SSRN 4412788 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4412788
- Lerman & Livnat (2010), "The new Form 8-K disclosures," *Review of Accounting Studies* — https://link.springer.com/article/10.1007/s11142-009-9114-7
- "Why Has PEAD Declined Over Time? The Role of Earnings News Persistence" (Columbia CEASA) — https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Events%20Page/PEAD_Declined_over_time.pdf
- "Trading frictions and the Post-earnings-announcement drift," *ScienceDirect* — https://www.sciencedirect.com/science/article/pii/S0148619524000584
- Bid-ask spread / maliyet referansı — https://equicurious.com/learn/investing-basics/market-mechanics/bid-ask-spreads-and-liquidity-in-us-equities
- **UNVERIFIED:** Lou, Polk, Skouras "tug of war" (gece/gün-içi) — bu turda birincil kaynak doğrulanamadı, TIER ataması yapılmadı.
- **TIER D / ŞÜPHELİ:** "Statistical Arbitrage with Mean-Reverting Overnight Price Gaps," *MDPI JRFM* 12(2):51 — https://www.mdpi.com/1911-8074/12/2/51

---

*Level A. Üretim kodu, `.env`, flag, cache, scheduler, DB veya mevcut governance kararı DEĞİŞTİRİLMEDİ. Tahmin üretilmedi. Hiçbir ticaret tavsiyesi verilmedi.*
