# FinPilot — İki Belgenin Deney Sonuçları: Kapsamlı Sentez ve Yol Haritası

Sürüm: 1.0 · Tarih: 2026-08-10 · Statü: Level A (araştırma, üretim değişikliği yok)
Kaynak belgeler: `2026-08-10-finpilot-10-perspektif-red-team-vizyon-arastirmasi.md` (10-Perspektif) ve `2026-08-10-finpilot-strategic-thinking-lab-v1.md` (Strategic Thinking Lab) + bu iki turda koşulan **9 deney** (5+4).

---

## 1. İKİ BELGENİN ORTAK ÇEKİRDEĞİ

İki belge bağımsız yazıldı ama aynı kanıt tabanından (§0) çıktı ve ikisi de aynı üç önceliğe yakınsadı:
1. **Getiri-hedefinden risk-hedefine pivot** (tek kanıtlanmış, rejim-dayanıklı bulgu: ATR→MAE).
2. **Giriş-zamanlaması + bariyersiz drift diagnostiği** (hiç ölçülmemiş temel boşluk).
3. **Gerçek-sektör-etiketiyle koşullu-edge doğrulaması** (tek OOS-tutarlı ipucu, ama %24-doğru proxy'yle test edilebildi).

Strategic Thinking Lab bunlara ek olarak **Foundational Integrity** kavramını getirdi (ATR look-ahead audit) ve **Collision-protokolüyle** (support/attack/modify/test/kill) daha sert bir çapraz-sorgulama uyguladı. 10-Perspektif belgesi ise **davranışsal, ürün ve gelecek-vizyonu** eksenlerinde daha derindi (Grade-inversiyonu, kategori-alternatifleri, "iyi-sinyal vs iyi-trade" ayrımı).

---

## 2. KOŞULAN 9 DENEY — TOPLU SONUÇ TABLOSU

| # | Deney | Hangi belge/madde | Sonuç | Statü |
|---|---|---|---|---|
| 1 | ATR look-ahead kod-audit'i | STL Big Bet #1a | Klasik gelecek-sızıntısı YOK; ama canlı-skor gün-içi-parçalı-bar kullanıyor (train/serve skew) — YENİ bulgu | ATR-MAE **sağlam**, yeni altyapı-sorunu bulundu |
| 2 | 3-giriş-noktası + bariyersiz drift | 10P Persona-1 #2/#4, STL Big Bet #1b | SPY-excess 3 noktada da düz/sıfıra-yakın, hiç half-life yok | Giriş-zamanlaması hipotezi **ELENDİ** |
| 3 | Reverse-ranking (composite_score) | 10P Persona-1 #8 | Satır-bazlı: IS+OOS'ta ALT-%20 üstün. **Gün-bazlı cluster-robust'ta OOS çöktü** (t~-0.15), IS sınırda kaldı (t~+2.22) | **DÜZELTİLDİ** — artık IS/OOS-tutarlı sayılamaz |
| 4 | Random-entry vs gerçek-sinyal | STL Exit-experiment #8 | Gerçek sinyaller random-entry'yi win+medyanda tutarlı geçti | Taban-sinyal-üretiminde **zayıf-gerçek bilgi var** |
| 5 | Concentration-kısıtlı portföy | 10P Persona-6, STL Portfolio #1 | Kısıtsız top-10 ort. %61.79 tek-sektöre yığılıyor; max-3/sektör kısıtı riski yarıya indirip getiriyi artırdı | **En güçlü, alfa-gerektirmeyen bulgu** (küçük-n) |
| 6 | Extension/exhaustion mekanizması | 10P Persona-1 #3 | ATR-extension deciline göre entry_ok-oranı ~15× artıyor (en-uzamış isimler sistematik seçiliyor) | **entry_ok inversiyonunun mekanizması bulundu** |
| 7 | PCA/feature-redundancy | 10P Persona-1 #9 | composite↔finpilot dışında aile ÇOK redundant değil (%90 varyansa 7-8/11 bileşen gerekiyor); composite↔dist_52w_high r=+0.66 (YENİ) | "2-3 eksene iniyor" hipotezi **YANLIŞ ÇIKTI**, düzeltildi |
| 8 | Cluster-robust + aynı-gün kümelenme | STL Ranking-experiment #4, #19 | (bkz. #3) + ICC ölçümü outlier-dominant, güvenilmez; günlük ort. 414 benzersiz-sembole karşı 814.5 satır (2× tekrar) — ayrı flag | Metodolojik uyarı doğrulandı + yeni dedup-sorusu açıldı |
| 9 | ATR-bazlı position-sizing | 10P Persona-6, STL Portfolio #2 | 1/ATR ağırlıklandırma Sharpe'ı KÖTÜLEŞTİRDİ (kısıtlı: 0.165→0.127) — beklenmedik | Naif ATR-sizing **işe yaramadı** (concentration-kısıtı hâlâ dominant) |

---

## 3. NE ÖĞRENDİK — DÖRT KATEGORİDE

### (A) SAĞLAMLAŞAN
- **ATR→MAE risk-bulgusu** (IC −0.51) look-ahead-audit'ten sağlam çıktı.
- **Concentration-kısıtı** yeni deneyle de teyit edildi — programın en net "ücretsiz" iyileştirmesi.
- **Taban-sinyal-üretimi rastgeleden gerçekten iyi** (random-entry testi) — sorun taban-tespitte değil, ranking'te.

### (B) ELENEN
- **Giriş-zamanlaması hipotezi** ("edge sinyal-close'da var, açılışta kayboluyor") — hiçbir noktada drift yok, temiz null.
- **"Feature-ailesi 2-3 eksene iniyor"** — PCA bunu desteklemedi, yalnız composite/finpilot çifti mükerrer.
- **Naif ATR-ters-sizing'in otomatik-fayda sağlayacağı varsayımı** — Sharpe'ı kötüleştirdi.

### (C) DÜZELTİLEN (en önemlisi)
- **Reverse-ranking composite_score bulgusu** geçen turda "IS/OOS-tutarlı en güçlü sinyal" diye raporlanmıştı. Cluster-robust (gün-seviyesi) testte **OOS'taki tutarlılık kayboldu** — birkaç outlier-gün varyansı yutuyor. Bu, tam da Strategic Thinking Lab'ın "aynı-gün kümelenme standart hataları şişiriyor" uyarısının (deney #7/#10) doğrulanmış hâli. **Ders:** satır-bazlı IS/OOS-tutarlılık tek başına yeterli kanıt değil; kümelenme kontrol edilmeden hiçbir yeni bulguya güvenilmemeli.

### (D) YENİ BULUNAN (hiçbir belgede yoktu)
- **Canlı-skor train/serve skew:** `scanner/evaluate.py` gün-içi parçalı-bar kullanıyor, `core/scheduler.py` saatlik çalışıyor. P0 score-replay sorununun ve entry_ok/conviction-inversiyonunun olası kök-nedeni.
- **Extension/exhaustion mekanizması kanıtlandı:** entry_ok, ATR-extension'a göre sistematik olarak en-uzamış isimleri seçiyor (15× oran-farkı) — inversiyonun "neden"i artık bir hipotez değil, gözlenmiş bir mekanizma.
- **composite_score ↔ dist_52w_high r=+0.66** — skorun zirveye-yakınlıkla güçlü korelasyonu, extension-bulgusuyla tutarlı bir ikinci kanıt hattı.
- **Günlük sembol-tekrarı sorusu** (414 vs 814.5) — dedup/multi-timestamp politikasının sonuçları nasıl etkilediği hiç incelenmedi, yeni açık soru.

---

## 4. GÜNCELLENMİŞ BIG BET DURUMU (her iki belgeden)

| Bahis | Kaynak | Önceki statü | Şimdi |
|---|---|---|---|
| Risk/Kalibrasyon Pivotu | Her ikisi | Test-öncesi | **İlerlemeye hazır** — ATR-bulgusu iki ayrı denetimden (look-ahead + bu tur) sağlam çıktı |
| Foundational Integrity (giriş-zamanlaması) | STL | Test-öncesi | **Tamamlandı, hipotez elendi** — sorun zamanlama değil |
| Gerçek-Sektör Doğrulaması | Her ikisi | Veri-bekliyor | **Değişmedi** — hâlâ tek büyük açık deney, yeni veri (EODHD fundamentals) gerekiyor |
| entry_ok Fade-Adayı | 10P | Hipotez | **Kısmen aydınlandı** — mekanizma (extension) bulundu ama fade-yönü ayrı, matched-random+cluster-robust doğrulaması gerekiyor (reverse-ranking dersinden sonra bu şart) |
| Concentration/POQ | Her ikisi | Hipotez | **Güçlü kanıt, iki bağımsız deneyle teyitli** — sıradaki adım tam-evren/uzun-pencere doğrulaması |
| Feature-basitleştirme (PCA) | 10P | Hipotez | **Reddedildi** — basitleştirme gerekçesi zayıf, composite/finpilot dışında aile bilgi taşıyor |

---

## 5. GENEL SIRADAKİ ADIMLAR (öncelik sırasıyla)

**Hemen (düşük-maliyet, yüksek-EV, sıfır-yeni-veri):**
1. Reverse-ranking bulgusunu **tamamen kapat** — ya matched-random-kontrol + daha uzun/başka bir OOS penceresiyle tekrar dene, ya da "artefakt, terk edildi" diye resmi olarak kapat. Şu an yarım-kalmış, yanlış-güven riski taşıyor.
2. Extension/exhaustion bulgusunu **entry_ok'un resmi teşhisi** olarak decision-log'a/dokümana geçir — bu, programın "neden inversiyon var" sorusuna verdiği ilk somut cevap.
3. Günlük sembol-tekrarı (414 vs 814.5) sorusunu hızlıca aç-kapa — dedup-politikası sonuçları çarpıtıyor mu, yoksa meşru-çoklu-sinyal mi.

**Orta-vadede (yeni veri veya altyapı gerektiriyor):**
4. Canlı-skor'un feature-timing'ini düzelt (yalnız önceki-gün-kapanışına-kadar veri) — Level B, mühendislik-kararı.
5. Concentration-kısıtını **tam-evrende, çok-daha-uzun bir pencerede** (n=52-56 gün küçük) tekrar-doğrula; bulgu güçlü ama örneklem küçük.
6. Gerçek-sektör-etiketiyle (EODHD fundamentals) tam-evren sektör-trend testini bitir — programın tek kalan büyük açık sorusu.

**Ürün/kullanıcı-tarafı (kod-deneyi değil, bu iki turda koşulamadı):**
7. Kullanıcı-motivasyon-anketi, Grade-açık/kapalı pilotu, kalibrasyon-eğrisi-gösterimi — hâlâ bekliyor, gerçek kullanıcı-etkileşimi gerektiriyor.

**Değişmeyen disiplin-kuralı:** Bu iki tur, aynı zamanda kendi uyarısını kanıtladı — yeni bir "ilginç" bulgu (reverse-ranking) ilk bakışta güçlü görünüp ikinci-bakışta (cluster-robust) çöktü. Sıradaki hiçbir yeni bulgu, gün-seviyesi/kümelenme-kontrollü doğrulamadan "kanıtlanmış" sayılmamalı.
