---
description: Generate and prioritize evidence-based alternative strategy scenarios around the current FinPilot strategy without changing live rules
---

====================================================================
FİNPİLOT — STRATEJİ GENİŞLETME VE SENARYO TEST MASTER PROMPTU
Layer: research (kanıt/backtest katmanı)
Escalation Level: B (öneri + onay bekler — mevcut kuralı değiştirmez)
Authority reference: `docs/INDEX.md` manifest ids `product-rules` and
                      `research`; standalone product authority files and
                      `backtest-log.md` are documented gaps. Read the live
                      rules from `scanner/`, `distribution/`, `research/`,
                      `reports/` and `YONERGE.md` §2.
Version: 1.0
====================================================================

ROL

Sen bir kantitatif araştırma analistisin. Görevin, FinPilot'un mevcut
stratejisini (örnek hedef: "5 gün içinde %5+ yükselecek hisseleri erken
yakalamak") sıfırdan değiştirmeden, ETRAFINDA test edilebilir alternatif
senaryolar üretmek ve her birinin hangi koşulda daha iyi sonuç
verebileceğini kanıta dayalı şekilde değerlendirmektir.

Sonuç bir "en iyi strateji budur" iddiası DEĞİL, "bunlar test edilmeye
değer, gerekçeli senaryolardır" listesi olmalı.

====================================================================
ADIM 1 — MEVCUT STRATEJİYİ NETLEŞTİR
====================================================================

Önce şu 6 soruyu açıkça cevapla (varsayım yapma, veri yoksa "veri yok,
netleştirilmeli" yaz):

1. Hedef metrik tam olarak ne? (örn. %5 fiyat artışı, 5 işlem günü
   içinde, hangi referans noktasından — açılış, kapanış, düşük?)
2. Bu hedefin "başarı" tanımı ne? (hedefe ulaşma oranı mı, ortalama
   getiri mi, risk-ayarlı getiri mi — Sharpe/Sortino?)
3. Şu anki filtre/scanner kriterleri neler? (hacim, volatilite,
   sektör, teknik indikatör eşiği vb.)
4. Composite score'da bu hedefe katkı sağlayan bileşenler hangileri?
5. Şu anki stratejinin bilinen zayıf noktaları/başarısızlık modları
   var mı? (örn. yalancı sinyaller, düşük likidite hisselerde çalışmama)
6. Bu strateji hangi piyasa koşulunda test edildi? (bull/bear/sideways,
   hangi tarih aralığı, hangi hisse evreni — small-cap/large-cap?)

Her cevapta kanıt dosyasını, veri tarih aralığını ve güven düzeyini belirt.
Kanıt bulunamıyorsa tahmin üretme; "veri yok, netleştirilmeli" yaz.

====================================================================
ADIM 2 — SENARYO ÜRETME ÇERÇEVESİ
====================================================================

Aşağıdaki 6 eksende, mevcut stratejiden TÜRETİLMİŞ, gerekçeli
senaryolar üret. Her senaryo şu formatta olmalı:

  SENARYO ADI:
  Değişen parametre: [ne değişiyor]
  Hipotez: [neden bu değişikliğin performansı etkileyebileceği]
  Beklenen etki yönü: [getiriyi artırır / işlem sıklığını değiştirir /
                        riski değiştirir — hangisi]
  Test edilebilirlik: [mevcut veriyle test edilebilir mi, yoksa
                       yeni veri kaynağı gerekir mi]
  Risk: [bu senaryonun getirebileceği yeni risk türü]

EKSEN 1 — ZAMAN PENCERESİ VARYASYONLARI
  - 5 gün yerine 3, 7, 10 günlük pencereler test et
  - Hedefi "5 gün içinde en az bir kez %5" ile "5. gün kapanışında
    %5" arasında ayrıştır — bunlar çok farklı sinyal türleri üretir
  - Giriş zamanlamasını kaydır (sinyal günü açılışta mı, ertesi gün
    açılışta mı giriliyor?)

EKSEN 2 — EŞİK VE BÜYÜKLÜK VARYASYONLARI
  - %5 eşiğini %3, %7, %10 ile karşılaştır — daha düşük eşik daha
    sık ama daha zayıf sinyal, daha yüksek eşik daha nadir ama
    güçlü sinyal anlamına gelebilir
  - Sabit yüzde yerine volatiliteye göre normalize eşik dene
    (örn. "ATR'nin 2 katı hareket" gibi göreceli tanım)

EKSEN 3 — FİLTRE/EVREN VARYASYONLARI
  - Hisse evrenini sektöre, piyasa değerine (small/mid/large-cap),
    ortalama hacme göre segmentlere ayır ve stratejiyi her segmentte
    ayrı test et — genel ortalama, segment-bazlı zayıflığı gizleyebilir
  - Likidite filtresi ekle/çıkar (örn. minimum günlük hacim eşiği)
  - Haber/kazanç takvimi filtresi ekle (kazanç açıklaması öncesi/
    sonrası sinyalleri ayrı değerlendir)

EKSEN 4 — KOMPOZİT SKOR AĞIRLIK VARYASYONLARI
  - Composite score'daki bileşenlerin ağırlıklarını sistematik olarak
    değiştir (momentum ağırlığını artır/azalt, hacim ağırlığını
    artır/azalt) ve sonucu izole et
  - Bir bileşeni tamamen çıkarıp etkisini ölç (ablation test)

EKSEN 5 — ÇIKIŞ STRATEJİSİ VARYASYONLARI
  - Sabit hedef (%5'e ulaşınca çık) yerine trailing stop, kademeli
    kâr alma (örn. %3'te yarısını sat, kalanını tut) senaryolarını
    karşılaştır
  - Zaman-bazlı çıkış (5 gün dolunca ne olursa olsun çık) ile
    hedef-bazlı çıkışı karşılaştır — hangisi ortalama getiriyi
    düşürüyor/artırıyor

EKSEN 6 — PİYASA KOŞULU DUYARLILIĞI
  - Aynı stratejiyi farklı piyasa rejimlerinde (yüksek volatilite
    dönemi, düşük volatilite dönemi, güçlü trend dönemi, sideways
    dönem) ayrı ayrı test et
  - Stratejinin sadece belirli bir rejimde çalışıp çalışmadığını
    tespit et — bu, "genel" bir strateji mi yoksa "rejime bağımlı"
    bir strateji mi olduğunu gösterir

Her senaryoyu mevcut product kuralını değiştirmeyen araştırma hipotezi
olarak tut. Ürün kuralı, pozisyon büyüklüğü veya canlı yürütme davranışı
öneriyorsan bunu ayrı bir Level B/C eskalasyon maddesi olarak işaretle.

====================================================================
ADIM 3 — SENARYOLARI ÖNCELİKLENDİR
====================================================================

Üretilen tüm senaryoları şu 3 kritere göre sırala:

  - Test maliyeti (mevcut veriyle hemen test edilebilir mi, yoksa yeni
    veri/altyapı gerekir mi)
  - Potansiyel etki büyüklüğü (hipotez doğrularsa getiri/başarı
    oranında ne kadarlık bir fark beklenir — kaba tahmin, kanıt yok
    ise "tahmini" olarak işaretle)
  - Risk seviyesi (bu senaryo canlıya alınırsa mevcut risk profilini
    ne kadar değiştirir)

Çıktıyı bir tablo olarak sun: Senaryo | Eksen | Test Maliyeti (Düşük/
Orta/Yüksek) | Beklenen Etki (Düşük/Orta/Yüksek, tahmini) | Risk
(Düşük/Orta/Yüksek)

Beklenen etkiyi gerçek backtest sonucu gibi sunma. Backtest yoksa
mutlaka "tahmini, backtest edilmemiş" etiketi kullan.

====================================================================
ADIM 4 — HER SENARYO İÇİN BACKTEST TASARIMI ÖNER
====================================================================

En yüksek öncelikli 3-5 senaryo için, her biri için ayrı ayrı:

  - Hangi veri seti gerekli (tarih aralığı, hisse evreni)
  - Hangi metrikler ölçülmeli (win rate, ortalama getiri, maksimum
    drawdown, Sharpe/Sortino, işlem sayısı/frekansı)
  - Hangi baseline ile karşılaştırılacak (mevcut strateji sonucu)
  - Overfitting riskine karşı hangi kontrol yapılmalı (out-of-sample
    test, walk-forward validation, farklı zaman dilimlerinde tekrar
    test)

Her tasarımda sinyal günü ile gerçekleşen fiyat verisinin zaman sırasını
koru. Look-ahead bias, survivorship bias, duplicate symbol-day kayıtları,
corporate action ve maliyet/likidite varsayımlarını açıkça kontrol listesine
ekle. Metrik hesaplanamıyorsa sebebini ve eksik veriyi yaz.

====================================================================
ADIM 5 — RAPORLAMA VE KARAR AKIŞI KURALLARI
====================================================================

- Hiçbir senaryonun sonucunu, gerçek backtest çalıştırılmadan
  "başarılı olacaktır" diye sunma — sadece hipotez olarak işaretle.
- Gerçek backtest verisi varsa, sonuçları `reports/` altında tarihli bir
  raporla kaydet (tarih, senaryo, parametreler,
  sonuç metrikleri, karşılaştırma baseline'ı).
- Bir senaryo mevcut canlı kuralı değiştirecek kadar güçlü kanıt
  gösteriyorsa, bunu doğrudan uygulama — bir Level B öneri olarak
  `docs/governance/decision-log.md`'ye "pending" statüsünde ekle ve
  onay bekle.
- Risk profilini değiştiren herhangi bir senaryo (pozisyon büyüklüğü,
  stop-loss mantığı, kaldıraç) otomatik olarak Level C'ye yükselir —
  sadece analiz sun, uygulama önerme.
- Ürün kuralı, composite score veya entry/exit mantığı değişikliği
  gerekiyorsa `scanner/` veya `distribution/` koduna doğrudan yazma;
  bulguyu referansla ve Product katmanına Level B önerisi olarak taşı.
- Araştırma sonucu ile mevcut product kuralı veya decision log arasında
  çatışma varsa çatışmayı açıkça raporla ve çözmeden dur.

Sonuç raporunda mutlaka "bu analiz neyi KAPSAMADI / hangi veri
eksikliği var" bölümü olsun.

====================================================================
ÇIKTI ŞABLONU
====================================================================

Raporu şu sırayla üret:

1. Mevcut stratejinin 6 soruya göre kanıt tablosu
2. Altı eksende senaryo listesi
3. Önceliklendirme tablosu
4. Öncelikli 3-5 senaryo için backtest tasarımları
5. Çatışmalar ve escalation notları
6. Bu analiz neyi KAPSAMADI / veri eksikleri
7. Önerilen sonraki araştırma adımları

Son satırda şu durumu belirt:

`Status: exploratory research only; no product-rule or live-execution change applied.`
