# FinPilot Analiz & Sinyal Çıktıları

## Developer Alignment Notları

### 1. Progressive Disclosure Zinciri

- **Neden?** Kullanıcı kitlesi heterojen: acemi yatırımcı hızlı karar isterken, uzman kullanıcı detay ve doğrulama arıyor. Zincirimizi katmanlı kurarak her profili tek ekranda tatmin ediyoruz.
- **Nasıl?**
  1. Grid kartı ve TL;DR ile saniyeler içinde sezgisel karar.
  2. Collapsible bloklarla merak duygusunu karşılayan “hikâye katmanı”.
  3. Modal sekmeleri sayesinde derin teknik veri ve algoritma şeffaflığı.
- **Beklenen etki:** Kullanıcının ekrandan çıkma ihtiyacı azalır, çünkü bilgi seviyesine göre ilerleyebileceği hazır bir patika var.

### 2. TL;DR’nin Karar Motoru Rolü

- **Neden?** Pilot testlerde kullanıcıların büyük çoğunluğu tek cümlelik özetle karar veriyor; bu alan güvenin ilk temeli.
- **Nasıl?** TL;DR her kartta ve sağ panelde renk kodlu, tek cümlelik ve aksiyon çağrısı barındıracak: “Apple güçlü nakit akışıyla AL sinyali veriyor.”
- **Beklenen etki:** Kullanıcılar önce güven hisseder, ardından isterlerse detay için motivasyon oluşur. TL;DR’yi zayıf bırakmak, tüm zinciri düşürür.

### 3. Grid – Tablo – Grafik Üçlüsü

- **Neden?** Bilgiyi üç öğrenme stiline aynı anda sunmak: hızlı sezgisel, analitik, görsel.
- **Nasıl?**
  - Grid kartı: Öneri listesi, trend etiketi ve güven puanı ile “hızlı tarama”.
  - Gelişmiş tablo: Filtresi olan, sıralanabilir metrik seti → “analitik derinleşme”.
  - Grafik alanı: Mum grafiği + sinyal noktaları → “görsel kanıt”.
- **Beklenen etki:** Tek ekranda üç persona: karar verici, analist, grafik odaklı trader’a aynı anda hizmet.

### 4. Analiz Hikâyesi Kartı

- **Neden?** Kullanıcıya sadece veri değil, ikna edici bir anlatı sunmak istiyoruz; FinPilot’un farkı burada.
- **Nasıl?**
  - ✅/🛑/🎯/⚔️ başlıkları duygusal çerçeve kurar (güç, risk, fırsat, karar).
  - Tooltip’li terimler FinSense sözlüğünü tetikler; kullanıcı öğrenirken ikna olur.
  - R/R özeti matematiksel güvence sağlar: “Stop 173 / Take 194 → 2.7 R/R.”
- **Beklenen etki:** Kullanıcı kendini yatırım koçuyla konuşur gibi hisseder; sadece “AL/SAT” değil, hikâyenin nedenini de anlar.

### 5. CTA Stratejisi

- **Neden?** Kullanıcıyı güven → niyet → aksiyon → premium köprüsü ile ilerletmek.
- **Nasıl?**
  - Kart içindeki küçük CTA (“Detayı gör”) modal’a taşır; merak tetikleyicisi.
  - Modal’ın aksiyon sekmesindeki büyük CTA (“Pozisyonu ayarla”) gerçek işlemi başlatır.
  - Sayfa sonunda yer alan “Ücretsiz Portföy Analizi” butonu, demo’dan ücretli servise doğal geçiştir.
- **Beklenen etki:** Kullanıcıyı çok erken satışa zorlamadan, önce güven sonra dönüşüm sağlayan funnel.

---

## Hızlı Özet Cümlesi

> “FinPilot’un ana ekranı, kullanıcıya önce güven, sonra hikâye, en sonunda aksiyon sunan bir ikna motorudur.”

---

## Bu Notlar Nasıl Kullanılabilir?

1. **Sprint Kickoff:** Bu beş maddeyi okuyup, her ekibin (frontend, backend, ürün) kendi deliverable’ını bu hikâyeye bağlamasını isteyin.
2. **Daily Stand-up:** Bir maddeyi seçip “Bugün bu zincirin neresine katkı yapıyorum?” sorusuyla tur atın.
3. **QA / Demo:** TL;DR’nin anlaşılır olması, tooltip’lerin çalışması gibi soruları checklist’e ekleyin; sadece fonksiyonel test değil, anlatı testi yapın.
4. **Yeni ekip üyesi onboarding’i:** “Analiz Hikâyesi Kartı”nın neden var olduğunu açmak için ilk okunacak belge olarak paylaşın.
