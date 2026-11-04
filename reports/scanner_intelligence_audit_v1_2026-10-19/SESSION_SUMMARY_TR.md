# Oturum Teslimi ve Yonetici Ozeti

Tarih: 2026-10-19. Surum: v1. Durum: sinirlari belirtilmis arastirma sentezi; uygulama karari degildir.
Katman: arastirma / muhendislik. Seviye: A raporlama; urun, risk ve canli degisiklikler icin ayri onay gerekir.

## 1. Dosyalar Nerede?

Tum yollar [session_file_manifest.csv](session_file_manifest.csv) icinde, depo kokune gore yazildi. Mutlak yol elde etmek icin `C:\Users\meric\Borsa\` oneki kullanilir.

| Grup | Dosya sayisi | Aciklama |
|---|---:|---|
| 19 Ekim denetim raporlari | 13 | R0 envanteri ve istenen R1-R12 |
| 19 Ekim analiz betikleri | 23 | Mimari, veri, formuller, skor, execution, istatistik ve red-team |
| 19 Ekim turetilmis kanitlar | 42 | CSV, JSON ve metin ciktilari; kaynak uretim verisi degil |
| Onceki oturum asamalari | 23 | 14-18 Ekim yatirimci/OOS/aykiri deger raporlari ve performans arastirmasi |
| Bu teslim | 2 | Yol manifesti ve bu Turkce ozet |
| Toplam | 103 | Varligi kontrol edilen proje dosyalari |

Liste kapsam siniri: onceki asamalar oturum gecmisi ve disk varligiyla eslestirildi; dosya zamanlari tek basina yazarlik kaniti sayilmadi. Manifest kriptografik butunluk belgesi veya Git commit listesi degildir. `audit_package_scope_exception` isareti ilgili analizin sonuc kapsaminda acik inceleme oldugunu belirtir; diger dosyalarda bu isaretin olmamasi otomatik kullanim izni vermez.

Yeni olusturulmayan, fakat bu oturumda guncellenen karar gunlugu manifestte yeni dosya olarak sayilmadi: [docs/governance/decision-log.md](../../docs/governance/decision-log.md). Degisiklikler ile yeni dosyalar birbirinden ayridir.

Depo disi baslangic kaydi: `C:\Users\meric\AppData\Local\Temp\fp_audit_2026_10_19_pre.txt`. Gecici oldugu icin 103 proje dosyasina dahil degildir. Araclarin otomatik terminal loglari, Python bytecode dosyalari, runtime tarama ciktilari ve diger oturumlarin eszamanli Academy calismalari bu arastirma teslim listesine alinmadi.

## 2. Yonetim Icin Ana Sonuc

**FinPilot'in karli oldugu veya mevcut siralamanin islem avantaji sagladigi henuz gosterilmis degil. Bu, sistemin kesinlikle avantajsiz oldugu anlamina da gelmiyor. En buyuk engel, verdigimiz kararlarin tarihsel olarak ne oldugunu ve sonuclarinin nasil hesaplandigini guvenilir bicimde yeniden kuramamak.**

Bu nedenle bir sonraki yatirim yeni skor, daha fazla bayrak veya genis bir parametre aramasi olmamali. Once zaman/veri/etiket dogrulugu, gercek uretim sirasi kaydi ve uygulanabilir maliyetler netlesmeli. Ayrintili oneriler [R12](R12_final_decision_matrix.md), ilk sentez [R1](R1_executive_summary.md) icindedir.

## 3. Gercekten Neyi Dogruladik?

### Tarihsel rakamlar yeniden uretilebiliyor; anlamlari sinirli

[R0](R0_evidence_inventory.md), onceki 5.206 karar satirinda saklanan brut bariyer getirilerini yeniden uretti: ortalama +%0,398424, medyan -%0,64315. En iyi %1 cikarilinca ortalama +%0,189646; en iyi %5 cikarilinca -%0,161478.

Bu hesaplar ucret, spread, kayma, gercek dolum veya sermaye tahsisi icermiyor. Bunlar tarihsel etiket muhasebesi; net islem beklentisi veya portfoy getirisi degil. Pozitif ortalama sag kuyruga duyarli; bu tek basina secim becerisini ne kanitlar ne de curutur.

Onceki "en iyi 52 sinyalin 48'i iki islem gununde" ifadesi duzeltildi: bunlar iki arsive yazilma tarihi. Tarihlerden biri Pazar. Gercek sinyal tarihleriyle dagilim farkli. Bu, tarih alanlarinin ekonomik yorumdan once denetlenmesi gerektigini gosteriyor.

### Bazi teknik mekanizmalar islev goruyor

Saklanan hedef/stop oranlariyla bariyer getiri aritmetigi tutarli. Isci ve HTTP istegi gozlemleri zaman asimi sonrasi calisan isi ayirt edebiliyor. Saklanan bayrak ve bilesenlerle kompozit skorun kosullu muhasebe kontrolu yapilabiliyor. Ancak bunlar ham veriden birebir uretim replay'i veya strateji basarisi degil.

## 4. En Kritik Gecerlilik Sorunu: Sonuc Penceresinin Tarihi

[R6](R6_entry_exit_audit.md) ve [R10 B11](R10_red_team.md), cozumleyicinin pencere baslangicinda payload sinyal tarihinden once arsiv `ts` alanini kullandigini gosteriyor. Giris fiyati ise sinyal payload'indan geliyor. Gec arsivlenen satirlarda fiyat ile degerlendirme penceresi farkli gunlere ait olabiliyor.

Bu, hata yonunde guclu bir kod bulgusudur. Red-Team'in yerel gunluk-bar replay'i mekanizmayi destekliyor; fakat fiyat vintaji ve kontrol uyusmazligi nedeniyle hesaplanan duzeltme kesin bir yeni getiri serisi degildir. "Duzeltince sistemin getirisi su olur" demek icin erken.

Ek olarak ayni gunluk barda iki bariyerin gorulmesi halinde iki etiketleyici farkli oncelik kullaniyor. Gunluk OHLC verisinden gercek temas sirasi bilinemez. Gap halinde teorik seviye fiyatindan cikis ile ilk uygulanabilir fiyat da ayni sey degildir.

## 5. Puanlama ile Secim Ayni Sey Degil

[R5](R5_flags_scoring_ranking.md) onemli bir yonetim farkini ortaya koyuyor: kompozit skoru iyilestirmek, yayinlanan aday sirasini mutlaka degistirmiyor.

Kod yolunda sira once grade, sonra execution confidence, conviction probability ve rank anahtarina dayaniyor. Varsayilan bayrak durumunda `ranking_score`, `legacy_quality_score` oluyor; bayrak ve sifir/fallback degerleri bu yorumu degistirebilir. Incelenen 20.298 Ekim satirinda iki alan esit; bu tum tarihsel canli konfigurasyonun sertifikasi degil.

Kompozitteki esitlikler cok olsa da gercek yayin anahtarinda ayni sorun otomatik olarak varsayilamaz. Shortlist CSV satir sirasi da rank degil; islerin tamamlanma sirasi olabilir. Ayrica UI ilk-10, LLM ozeti ve dagitim listesi farkli secim yuzeyleri kullaniyor.

Yonetim sonucu: hangi skoru iyilestirdigimiz kadar, hangi kullanici kararini degistirdigimizi de tanimlamaliyiz. Test edilen offline skorla canli secimin ayni oldugu varsayilamaz.

## 6. Formuller ve Veri Kalitesi

[R4](R4_formula_feature_registry.md) 30 formul kaydetti. Hacim, momentum ve trend bayraklari hem `filter_score` icinde hem tekil terim olarak kullaniliyor. Bu tekrar kodda dogrulandi; kasitli agirliklandirma olabilir, faydasizligin kaniti degil. Katkiyi secim ve maliyet sonrasi sonuc duzeyinde ayri test etmek gerekir.

NaN kenetleme kalibi ust sinir skoru uretebiliyor. Mekanizma yeniden uretildi; canli satirlarda ne siklikta oldugu ve ekonomik etkisi henuz kanitlanmadi. Kod sinir hatasi ile gerceklesmis portfoy zarari ayri iddialardir.

[R3](R3_data_quality_lineage.md), incelenen 20261016T224443 export'unda 1.801 satirin 1.518'inin skorlanmis, 283'unun `unavailable` iskelet oldugunu kaydediyor. Skorlananlarin hepsi `partial`; spread verisi yok. Dolayisiyla "1.801 sonuc" ile "1.801 tam verili ve islem yapilabilir hisse" ayni degil.

Alpaca IEX hacmi ile yfinance yedek hacmi ayni kapilarda kullanilabiliyor. Bu, likidite ve ADV degerlerinin kaynakla degisebilmesi demek. Alti hisselik, farkli pencereli karsilastirma IEX'in kesin pazar payini veya tum hisselerde yanlis eleme oranini olcmez.

Ek sorunlar: import aninda sabitlenen TTL, DST/tatil bilmeyen saat penceresi, kapanmamis bar olasiligi ve tarihsel replay icin point-in-time olmayan cache'ler. Bunlar farkli oncelikte arastirma/dogrulama adaylari; otomatik toplu mimari degisiklik gerekcesi degil.

## 7. Tarama Neden Hala Uzun?

[R8](R8_scanner_performance.md), 18 Ekim snapshot'indaki 416 tamamlanmis 200-sembol kaydinda medyan 321,38 sn ve p95 534,99 sn sonucunu yeniden uretiyor. Bu batch suresi; tam evren uctan uca sure olcumu degil.

16 Ekim restart sonrasi gozlenen 26 batch'te belirgin hiz kazanci gosterilmiyor. Once/sonra sembol ve repair yuku degistigi icin bu, paralel onarimin zararli veya etkisiz oldugunu nedensel olarak kanitlamaz.

Kod seviyesinde iki somut aday var: yalniz bir zaman dilimi eksikken tum gercek zaman dilimlerini yeniden istemek ve fiyat sorgusunun kutuphane icinde ek `history()` yoluna girmesi. Kutuphane cagrisi ile gercek ag indirmesi birebir sayilamaz; cache bunu degistirebilir.

Gozlenen 94 adet 200-sembol isteginin 3'u 600 saniyede zaman asimina ugrarken iscileri sonra basariyla bitmis. Sonuclarin kalici yazimi bundan etkileniyor. Bu, yalniz hiz degil veri butunlugu sorunu. Cozum timeout'u keyfi buyutmek degil; is sahipligi, sonuc teslimi ve sabit girdili profiling ile belirlenmeli.

## 8. Ekonomik Avantaj Icin Eksikler

Gercek secim becerisi icin ayni anda bilinebilir ve uygulanabilir secilmeyen hisselerle adil karsilastirma yok. Gercek dolum fiyatlari, spread/kayma, gecikme, eszamanli pozisyonlar ve sermaye kullanimiyla kurulmus guvenilir portfoy serisi de yok. Bu nedenle net beklenti, risk ayarli net performans ve olceklenebilirlik su anda belirlenemiyor.

Onceki genis TP/SL aramalari ve medyan-odakli hedef yakalama sonuclari yeni bir karli strateji iddiasini desteklemiyor. Bunlar tum olasi stratejilerin imkansiz oldugunu gostermez; ayni veride daha fazla arama yapmanin degerini dusurur.

Huni testi de sadece mevcut skorla ortusmeyi gosterdi. Tam evren kapsami ve gercek gunluk-veri bagimsizligi dogrulanmadi; aktivasyon veya hiz kazanci kaniti sayilmamali. Bir alt skorda hedef skorun bileseninin bulunmasi tek basina leakage degildir; asil soru o bilginin ilk asamada gercekten mevcut olup olmadigidir.

## 9. Denetimin Kendi Sinirlari

R6/R7/R9 kilit kapsaminda farkli yorumlar kullandi. Bu raporlardaki yeni sonuc dilimleri ve etkilesim istatistikleri karar kaniti olarak kullanilmiyor; erisim kapsami insan incelemesine acik. D7'nin tarihsel OOS iddiasini kaldirmasi, kilitli verilere erisim izni degildir.

Baslangic kaydi sadece Git durumu ve diff hash'lerini iceriyor. Son karsilastirmada hash'ler eslesmedi; eszamanli Academy degisiklikleri de vardi. Bu nedenle tam butunluk veya staged alanin degismedigi iddiasi yok. Kayitlar silinmedi ve kullanici degisiklikleri geri alinmadi.

Raporlar arasindaki orneklem, varsayilan bayrak ve estimator farklari [R12 bolum 5](R12_final_decision_matrix.md#5-interpretation-controls) icinde aciklandi. %99,88 kosullu skor uyumu ile %11,8 varsayilan-bayrak uyumu celisen ayni testler degil. Tam brief'in her maddesi icin olcum tamamlanmis degil; eksikler acikca korunuyor.

## 10. Onumuzdeki 30 Gun: Bes Is

| Sira | Is | Karari etkileyen teslim | Durma kosulu |
|---|---|---|---|
| 1 | Erisim ve kanit sozlesmesi | Hangi veri/bolumde hangi analiz yetkili? | Belirsiz izinle yeni outcome hesabi yok |
| 2 | Tarih ve fiyat tabani dogru etiket-v2 | Kontrol replay'i ve surumlu duyarlilik sonuclari | Kontrol uyusmazligi aciklanmadan duzeltilmis getiri yok |
| 3 | Gercek karar kaydi tasarimi | Run, evren, bayrak, veri kaynagi, rank anahtari ve bilesenlerle birebir replay | Eksik alanlarla uretim esdegerligi iddiasi yok |
| 4 | Secim ve ekonomi protokolu | Secilen/secilmeyen ve basit baseline'lar; gozlenen maliyet ile senaryo ayrimi | Adil kontrol veya fill verisi yoksa NOT_MEASURABLE |
| 5 | Sinirli performans deneyi | Donmus girdide karar farki olmadan repair optimizasyonu ve yetkili zamanlama | Karar/veri kapsami farki veya kaynak baskisinda dur |

Bu takvim oneridir; yeni esik, kaynak kotasi veya uretim degisikligi onayi degildir. Risk limitleri, pozisyon buyuklugu, TP/SL, skor agirliklari, huni/koordinator aktivasyonu ve yayin yolu bu kanitla otomatik degistirilmemeli.

## 11. Okuma Sirasi ve Oturum Durumu

Yonetim: bu dosya -> [R12 karar matrisi](R12_final_decision_matrix.md) -> [R10 Red-Team](R10_red_team.md).
Teknik ekip: [R2 mimari](R2_architecture_map.md) -> [R3 veri](R3_data_quality_lineage.md) -> [R5 skor ve siralama](R5_flags_scoring_ranking.md) -> [R8 performans](R8_scanner_performance.md).
Hipotezler: [R11](R11_hypothesis_backlog.md); bunlar bulgu veya uygulanmis karar degil.

Oturumun daha onceki muhendislik asamasinda 93ae83c yerel commit'i ve 16 Ekim API restart'i yapilmisti. Sonraki arastirma denetimi ve bu teslim adiminda uretim kodu degistirilmedi, yeni canli tarama/broker islemi/yayin/push yapilmadi. Bu ayrim, "butun oturum salt okunurdu" gibi yanlis bir genellemeyi onler.