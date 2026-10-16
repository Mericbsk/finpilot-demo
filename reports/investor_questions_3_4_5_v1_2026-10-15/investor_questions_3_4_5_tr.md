# Yatırımcı Soruları 3, 4 ve 5: Birleşik Rapor (Türkçe)

- Tarih: 15.10.2026
- Dil: Türkçe taslak. Almanca sürüm, bu metnin onayından sonra hazırlanacak.
- Durum: İç inceleme taslağı. Yatırımcıya gönderilmez. Gönderme ve genel yüzeylerdeki düzeltmeler insan kararıdır (Level C).
- Kaynak raporlar:
  - [investor_question_3_decision.md](../net_expectancy_audit_v1_2026-10-14/investor_question_3_decision.md)
  - [investor_question_4_answer_de.md](../oos_independence_audit_v1_2026-10-14/investor_question_4_answer_de.md)
  - [investor_question_5_answer_de.md](../outlier_dependence_audit_v1_2026-10-14/investor_question_5_answer_de.md)

## 1. Yönetici özeti

| Soru | Konu | Sonuç | Yatırımcıya verilebilecek ifade |
|---|---|---|---|
| 3 | Trade başına net beklenen getiri | Mevcut kanıtla güvenilir biçimde belirlenemiyor | Net bir ölçü yok. +%0,40 yalnızca brüt ve maliyetsiz bir ölçü |
| 4 | Kilitli out-of-sample veri ve değerlendirme kapısı | Bağımsızlık ve kapı kanıtlanmadı (Durum C) | Bağımsız doğrulama iddia edilmez. Değerlendirme hazır değil |
| 5 | En iyi %1 ve %5 çıkarımı ve uygulanabilirlik | Sonuçlar aykırı değerlere ve uygulama varsayımlarına duyarlı (Sonuç 2). Uygulanabilirlik kanıtlanmadı | Sağlamlık ve uygulanabilirlik iddia edilmez |

Ortak mesaj: Mevcut kanıt bir kârlılık ya da uygulanabilirlik kanıtı sunmuyor. Bu bir kanıtsızlık beyanıdır. Kötü performansın kanıtı da değildir.

## 2. Soru 3: Trade başına net beklenen getiri

Soru (özet): Spread, slippage ve ücretler sonrası trade başına beklenen getiri nedir?

Cevap: Mevcut kanıtla güvenilir biçimde belirlenemiyor. Ölçülmüş bir net ölçü yok. +%0,40 brüt bir ölçü, net değil.

Ölçülmüş bulgular:

- 5.206 sonuçlanmış sinyal, 12.09.2025 ile 09.09.2026 arasında. İsabet oranı %30,1. Ortalama kazanç +%4,28, ortalama kayıp −%1,27. Brüt beklenen getiri sinyal başına +%0,40.
- Medyan −%0,64. Pozitif beklenen getiri, birkaç büyük sonuca dayanıyor.
- En iyi %5 çıkarıldığında beklenen getiri −%0,16.
- 5.748 arşiv satırı 4.318 sembol-güne karşılık geliyor. Sinyaller örtüşüyor.
- Mart 2026 sonuçlanmış sinyallerin %48'ini içeriyor.
- Gerçekleşen işlem yok. Broker kaydında 11 emir var, hiçbiri gerçekleşmedi.

Model ve varsayımlar:

- Sonuçlar günlük kurslara dayanıyor. Giriş sinyal fiyatından, çıkış kâr al veya zarar durdur seviyesinden yapılıyor. Bu uygulamalar ideal ve gözlemlenmiş değil.
- Aynı gün hem kâr al hem zarar durdur seviyesi değerse kâr al kabul ediliyor.
- 0,20 %, 0,55 % ve 1,00 % işlem maliyeti senaryo varsayımıdır, ölçüm değildir. Varsayıma göre net beklenen getirinin işareti değişiyor.

Bilinmeyen veya mevcut olmayan:

- Ölçülmüş alış-satış farkı (spread) ve slippage
- Broker faturasındaki ücretler, borsa ve denetim ücretleri
- Ödünç alma maliyeti, döviz çevrimi ve piyasa etkisi
- Pozisyon büyüklükleri ve değer başına kapasite
- Önceden belirlenmiş eşiklerle, dokunulmamış bir out-of-sample dönem (bkz. Soru 4)

Söylenemeyecekler:

- Trade başına net getiri
- Ölçünün gerçekleşen sonuçlarla örtüştüğü
- Ölçünün maliyetler dahil doğrulandığı
- Otomatik veya kâğıt üzerindeki işlemlerin sonucu kanıtladığı

Gerekli sonraki adımlar:

1. Kurs serilerinin kontrolü: bölünme ve temettü düzeltmesi, aykırı değerler, özellikle 01.03. ve 03.03.2026.
2. Tanımlı bir ortamda, alış-satış fiyatı, dolum zamanı, fiyat ve ücretlerin işlem anında kaydı.
3. Her maliyet türü için tek kaynağı olan, belgelenmiş bir maliyet modeli.
4. Önceden kayıtlı, değerlendirmeye kadar dokunulmamış bir test dönemi ve belirlenmiş eşikler.
5. Gerçekleşen işlem varsa broker faturalarıyla karşılaştırma.

İç not (dağıtılmaz): +%0,40 ölçüsü kamuya açık yüzeylerde beklenen getiri olarak görünüyor. Brüt hesaplandığı ve ideal uygulama varsaydığı belirtilmiyor. Bu sunumun değiştirilmesi bir insan kararıdır (Level C) ve bu rapor bunu uygulamaz.

## 3. Soru 4: Kilitli out-of-sample veri seti ve değerlendirme kapısı

Soru (özet): Kanıtlanabilir biçimde kilitli ve dokunulmamış bir out-of-sample veri seti ve önceden belirlenmiş bir değerlendirme kapısı var mı?

Cevap (Durum C): Bağımsızlık veya kapı kanıtlanmadı.

Kısa cevap: Ticaret stratejisi için kanıtlanabilir biçimde kilitli ve dokunulmamış bir out-of-sample veri seti yok. Sayısal eşiklerle önceden belirlenmiş bir değerlendirme kapısı belgelenmemiş. RX-CAPTURE-1 kaydı hash ile doğrulanıyor, ancak diğer araştırma hatlarıyla aynı veri setini kullandığı için bağımsız değil.

1. Dondurma zamanı:

- Ticaret stratejisi, sınır 21.05.2026: kanıtlanamıyor. Depodaki en eski kayıt, sınır sonrası sonuçları zaten içeren 15.07.2026 16:52 UTC tarihli bir artefakt.
- Ayrı holdout, 09.06. ile 30.06.2026 (temel ve haber faktörleri): zaman damgası 05.08.2026 11:31 UTC. Skript tarafından yazıldı, sürüm kontrolüyle korunmadı.
- RX-CAPTURE-1, ön kayıt: karar günlüğünde 22.09.2026 tarihli kayıt, hash mevcut dosyayla eşleşiyor. İlk sürüm kontrolü kaydı 23.09.2026.

2. Dondurmayı ne kanıtlıyor:

- Yalnızca RX-CAPTURE-1 için hash ve karar günlüğü kaydı doğrulandı.
- Dosya zaman damgaları ve skriptin kendi yazdığı zaman damgaları tek başına dondurmayı kanıtlamaz.

3. Test dönemi kullanıldı mı:

- Evet. 21.05.2026 sonrası dönem 15.07.2026'da değerlendirildi (seçime bağlı 44 veya 62 gözlem). 26.06.2026'dan itibaren Eylül 2026'da 17.149 ile 18.909 gözlemle birkaç değerlendirme daha yapıldı.
- Test dönemi dokunulmamış değil. Holdout bu dönemlerle örtüşüyor.

4. Kapı önceden belirlenmiş miydi:

- Ticaret stratejisi: kanıtlanmadı. Test planı, sonuçlarla aynı commit'te kaydedildi.
- Belgelenmiş eşikler (sınırlamalarıyla): Kaldıraç (lift) 1'in üzerinde olmalı veya maliyet sonrası beklenen getiri pozitif olmalı. Güven aralığı tamamen rastgele tabanın altında kalmamalı. Aynı işaret en az üç zaman diliminde görülmeli. Medyan negatifse sonuç yalnızca ortalamaya dayanmamalı.
- Sabit tutma süreli araştırma koşuları: FDR eşiği 0,05, düzeltilmiş Sharpe en az 0,95, dönem başına en az 50 gözlem, eğitim ve doğrulamada net getirinin ortalaması ve medyanı pozitif. Bu değerler 06.08.2026'da koda kaydedildi, 05.08.2026 koşusundan sonra.
- Holdout için sayısal eşik yok.
- RX-CAPTURE-1: birincil büyüklük net yakalama medyanı. Bu medyan incelenen adaylar için anlamını yitirmiş, çünkü çoğu gözlem sabit hedef seviyeye hemen ulaşıyor. Eşikler değişmeden belgelenmiş, ama yalnızca sınırlı anlam taşıyor.

5. Bağımsız olarak kontrol edilemeyenler:

- Test veri seti için erişim kayıtları yok. Holdout'a erişim teknik olarak zorunlu değil. Koruma sınıfı yalnızca testlerde kullanılıyor.
- Eşiklerin sonuçlara bakılarak seçilmediği depodan dışlanamaz.
- Üretim sıralaması tam olarak yeniden kurulamadı. Test edilen değerlendirme yöntemi bir yaklaşım, üretimdekiyle aynı değil.
- Birden fazla girdi veri sürümü var. Bunlardan biri, düzeltme öncesinde alınmış 15.07.2026 yedeği.
- RX-CAPTURE-1-ECON ön kaydı, kaydedilmiş hash ile kanıtlanamıyor. Sürümü bu nedenle kesin olarak belirlenmiş değil.

6. Değerlendirme hazır mı:

Hayır. Güvenilir bir değerlendirme için gerekenler:

1. Erişimden önce hash ile kaydedilmiş, sayısal başarı, başarısızlık ve belirsizlik kriterleri içeren yeni bir protokol.
2. Verileri dondurmadan sonra oluşan ve daha önceki hiçbir değerlendirmede kullanılmamış bir test dönemi.
3. Sorumlu bir kişinin belgelenmiş onayı.
4. Erişim kaydı ve teknik olarak zorunlu tek seferlik açılış.

Özet: Yapılan değerlendirmeler belgelenebilir. Bağımsız, önceden kilitlenmiş bir testin yapıldığı kanıtlanamıyor. Ticaret stratejisinin out-of-sample doğrulaması hakkında bir beyan yapılamaz.

## 4. Soru 5: En iyi %1 ve %5 çıkarımı ve uygulanabilirlik

Soru (özet): En iyi %1 ve %5 işlem getiriye göre çıkarıldığında performans nasıl değişiyor? Bu işlemler, hacim ve spread açısından, hedeflenen pozisyon büyüklüklerinde uygulanabilir miydi?

Cevap: Sonuç 2. Sonuçlar aykırı değerlere ve uygulama varsayımlarına duyarlı. Uygulanabilirlik kanıtlanmadı.

Temel değerler (5.206 sonuçlanmış sinyal, brüt, maliyetsiz, ideal uygulama):

- Ortalama +%0,40, medyan −%0,64, isabet oranı %30,06.
- En iyi %1 (52 sinyal) çıkarılınca: ortalama +%0,19 (−0,21 puan), medyan −%0,65.
- En iyi %5 (260 sinyal) çıkarılınca: ortalama −%0,16, işaret değişiyor. Medyan −%0,68.
- En iyi %1, net toplamın %52,9'unu oluşturuyor. En iyi %5 ise %138,5'ini.
- Tarihe göre kümelenmiş %95 aralık (37 tarih): tüm örneklem [+%0,06; +%0,56], en iyi %5 hariç [−%0,42; +%0,05].
- En iyi %1'in 52 sinyalinin 48'i 01.03. ve 03.03.2026'da. Bu günler çıkarılınca ortalama +%0,13, medyan −%0,54.

Maliyet etkisi (sinyal başına sabit maliyet, puan):

| Maliyet | Tüm örneklem | En iyi %5 hariç |
|---|---|---|
| 0,20 | +%0,20 | −%0,36 |
| 0,55 | −%0,15 | −%0,71 |
| 1,00 | −%0,60 | −%1,16 |

Uygulanabilirlik:

- 1.000 USD büyüklükte emirlerin %95,2'si, son 20 işlem gününün dolar hacminin %0,1'inin altında.
- En iyi %1'de 52 sinyalin 10'u (%19,2) bu hacmin %5'ini aşıyor. 52 sinyalin 17'si 1 USD'nin altındaki hisseler.
- Giriş fiyatı, sinyal gününün kapanışı. Sonraki açılış, en iyi %1 için medyan %2,0, en iyi %5 için %4,0 daha yüksek.
- Kâr al veya zarar durdur seviyesinin boşlukla atlanması durumunda (duyarlılık), 4.631 eşleşen sinyalde ortalama +%0,44'ten −%0,06'ya düşüyor.

Ölçülen ve ölçülmeyen:

- Ölçülen: günlük işlem hacmi (tarihsel).
- Ölçülmeyen: alış-satış farkı (spread), alış ve satış fiyatları, emir defteri, gün içi kurslar.

Doğrulanmamış:

- Sinyal zaman damgalarının saat dilimi (en sık 09:00 ve 21:45). Bu olmadan giriş fiyatının işlem yapılabilir olup olmadığı kontrol edilemiyor.
- Arşiv sonuçlarının 575 / 5.206 kısmı (%11,0), kayıtlı günlük kurslardan yeniden üretilemiyor. Nedeni belirlenmedi.
- 01.03. ve 03.03.2026 sinyallerinin zamanında mı yoksa sonradan mı yazıldığı.
- Evrenin hayatta kalma yanlılığı (survivorship).

## 5. Ortak sınırlar

- Üç yanıt da taslak. Hiçbiri gönderilmedi.
- Tüm sorularda "robust", "ausführbar", "bewiesen", "Netto-Rendite", "unabhängig validiert" gibi ifadeler kullanılmamalı.
- Kamuya açık yüzeylerdeki +%0,40 ifadesi düzeltilmedi. Bu karar size ait (Level C).
- RX-CAPTURE-1-ECON kaydındaki hash çelişkisi düzeltilmedi.
- Bu rapor hiçbir veriyi, eşiği, kapıyı veya kodu değiştirmedi.

## 6. Onay ve sonraki adım

1. Bu Türkçe metni inceleyin. Düzeltme gerekiyorsa belirtin.
2. Onayınızdan sonra aynı yapıda Almanca sürüm hazırlanır (taslak olarak).
3. Gönderme kararı sizde.
