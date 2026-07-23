# aws Preseed | Seedfinancing — Detaylı Araştırma ve Yol Haritası
**FinPilot için · 22.07.2026 · Kaynak: aws.at (güncel program sayfaları)**

---

## 1. Program Yapısı (2026 Güncel)

aws (Austria Wirtschaftsservice), Preseed | Seedfinancing programını **iki hat × iki modül** olarak yürütüyor:

| Modül | Hat | Maks. Hibe | Gender Bonus ile | Geri Ödeme | Aşama |
|---|---|---|---|---|---|
| **Preseed** | Innovative Solutions | €89.000 | €100.000 | Geri ödemesiz | Proof of Concept (kuruluş öncesi / ticaret siciline kayıttan ≤6 ay) |
| **Preseed** | Deep Tech | €267.000 | €300.000 | Geri ödemesiz | PoC/Prototip, tipik TRL 3 |
| **Seedfinancing** | Innovative Solutions | €356.000 | €400.000 | Geri ödemesiz | PoC mevcut → pazara giriş (kuruluştan ≤5 yıl) |
| **Seedfinancing** | Deep Tech | €889.000 | €1.000.000 | **Kâr/exit durumunda faizsiz geri ödemeli** (9–12 yıl) | Prototip → pazar, tipik TRL 6 (kuruluştan ≤5 yıl, başvuru ≤54 ay) |

**Ortak koşullar:**
- Fonlama oranı: uygun maliyetlerin **%80'i** (gender bonus ile %90)
- **Toplam maliyetin en az %10'u** (gelecekteki) ortakların öz kaynağından karşılanmalı; ilave %10 satış/uzun vadeli finansmandan gelebilir
- Başvuru: **sürekli açık** (deadline yok), aws Fördermanager üzerinden online
- Karar: **jüri toplantıları, genelde çeyrekte bir** → iki aşamalı değerlendirme, süreç aylar alabilir
- Ödeme: **milestone bazlı taksitler**
- Başarı oranı: Innovative Solutions ~%20, Deep Tech ~%25
- Gender bonus: hibe onayı anında **>%25 hisseye sahip kadın ortak** gerektirir

---

## 2. FinPilot Hangi Hat / Modüle Uyuyor?

### Öneri: **Deep Tech hattı** (Digitalisation/ICT kategorisi)

**Gerekçe:**
- Innovative Solutions hattı, inovasyonun etkisinin şu alanlardan birinde olmasını **şart koşuyor**: çeşitlilik/eşitlik, çevre/iklim, sağlık/bakım, **eğitim**, mobilite, kentsel gelişim. FinPilot ancak "finansal okuryazarlık/eğitim" (FinSense Academy / Ledger Classroom açısı) üzerinden zorlama bir uyum sağlar.
- Innovative Solutions **açık istisna** içeriyor: *"FMA (Finanzmarktaufsicht) denetimine tabi finans sektörü iş alanları ve crowdfunding platformları fonlanmaz."* FinPilot analiz yazılımı olarak (lisanslı yatırım danışmanlığı değil) muhtemelen FMA denetimi dışında, ama bu gri alan jüride aleyhe çalışır.
- Deep Tech hattı DRL/ML tabanlı sistem için doğal ev: "Digitalisation, ICT" açıkça sayılıyor, sektör kısıtı ve etki alanı şartı yok.

**Deep Tech'te kritik eşikler (jürinin arayacakları):**
1. **Teknoloji sıçraması:** "incremental" değil, ciddi bilimsel/teknolojik zorluk. DRL tabanlı sinyal üretimi + walk-forward doğrulama metodolojisi bu şekilde çerçevelenmeli. "Bir LLM API'sini saran ürün" izlenimi elenme sebebidir.
2. **IP / giriş bariyeri:** Patent, lisans veya **diğer fikri mülkiyet biçimleriyle korunan** ayırt edici teknoloji pozisyonu. Yazılımda patent zorsa: trade secret stratejisi, tescilli veri setleri/pipeline, model mimarisi know-how'ı belgelenmeli. aws'nin ücretsiz **IP Coaching** hizmeti (12 saate kadar) başvuru öncesi kullanılabilir.
3. **Büyüme potansiyeli:** "Önümüzdeki yıllarda birkaç milyon € ciro ve **≥€5M finansman turları** gerçekçi olmalı." Finanzplan'daki Series A/B kurgusu bunu destekliyor — güncellenmeli.
4. **Bağımsızlık:** Başka şirketlerin payı ≤%24,9; salt finansal yatırımcılar ≤%50.

### Modül seçimi (Preseed vs Seedfinancing)
- **Şirket henüz kurulmadıysa veya sicile kayıt ≤6 ay ise** → Preseed Deep Tech (€267k, geri ödemesiz). Dikkat: *"Preseed şirketi başvuranın tek şirketi olmalı."*
- **GmbH kurulu ve prototip + backtest'ler hazırsa** (FinPilot'un durumu buna daha yakın: çalışan ürün, kapsamlı backtest raporları) → Seedfinancing Deep Tech (€889k'ya kadar, ama koşullu geri ödemeli).
- Strateji notu: Preseed geri ödemesiz olduğu için, henüz kuruluş tamamlanmadıysa **önce Preseed, sonra Seedfinancing** zinciri düşünülebilir (Seedfinancing, Preseed'in resmi devam programı).

---

## 3. Nelere Dikkat Etmeliyiz? (Eleme Sebepleri)

1. **Başvuru tarihinden önce oluşan maliyetler fonlanmaz** → proje çalışma paketlerini başvuru sonrasına planla; başvuruyu geciktirme.
2. **Incremental inovasyon reddedilir** — "mevcut çözümlere rutin ekleme" anlatısından kaçın; bilimsel zorluğu ve neden şimdiye kadar çözülemediğini anlat.
3. **AGVO/de-minimis limitleri** — daha önce alınmış kamu destekleri varsa bildir (Art. 22 AGVO €1M bütçe limiti).
4. **Solo founder riski:** Jüri "committed, competent, diverse team" arıyor. Finanzplan'daki key-hire planı (CTO/ML lead M1'de) güçlü şekilde sunulmalı; mümkünse başvuru öncesi en az bir co-founder/ilk çalışan taahhüdü göster.
5. **%10 öz kaynak kanıtı** — toplam proje maliyetinin %10'unun ortak öz kaynağıyla karşılanacağı planlanmalı ve belgelenmeli.
6. **Regülasyon çerçevesi:** "Yatırım tavsiyesi değil, analiz/karar destek yazılımı" pozisyonu net, tutarlı ve hukuken savunulabilir olmalı. Bu, uzman görüşmesinde ilk netleştirilecek konu.
7. **Proje lokasyonu Avusturya'da olmalı** (Viyana ✓).

---

## 4. Neler Sunmalıyız? (Zorunlu Belgeler)

Başvuru aws Fördermanager (foerdermanager.aws.at) üzerinden:

| Belge | Format şartı | Mevcut durumumuz |
|---|---|---|
| **Business Plan** | ~25 sayfa (±5) | Yok — Finanzplan + GTM planlarından derlenecek |
| **Structured Pitch Deck** | **aws şablonundaki yapıya göre** (Downloads alanından indirilecek) | NVIDIA Inception deck'i (Mart 2026) temel olur; aws şablonuna göre yeniden yapılandırılmalı + güncellenmiş |
| **Integrale Planung** | Çalışma paketleri + maliyet planı (aws şablonu) | Yok — Finanzplan'daki Mittelverwendung'dan türetilecek, ama iş-paketi formatında |
| **Kimlik belgesi** | — | Hazır |
| **Ekip CV'leri** | Proje ekibi | Hazırlanacak |

**Mevcut belgeler hakkında not:** `FINANZPLAN_AWS_GRUENDUNGSFONDS.md` (Nisan 2026) **aws Gründungsfonds** (equity yatırımı, €750k) için yazılmış — Preseed/Seedfinancing **hibe** programının mantığı farklı: sermaye turu anlatısı değil, **proje/çalışma paketi bazlı maliyet planı** ister. Rakamlar ve traction güncellenip format tamamen dönüştürülmeli. Backtest/metodoloji raporları (Temmuz 2026) teknoloji sıçraması kanıtı olarak ek değer taşır.

---

## 5. Uzmana Ulaşma — İzlenecek Yol

**Deep Tech hattında aws, talep üzerine birebir telefon görüşmesi sunuyor** — resmi ve beklenen ilk adım budur. Soğuk e-posta değil, programın kendi kanalı:

- **E-posta (Deep Tech ekibi):** deeptechanfrage@aws.at
- **İlgili uzman (ICT):** Dipl.-Ing. **Paul Ullmann** — Deep Technologies | ICT & Physical Sciences · +43 1 501 75-516
- Diğer Deep Tech uzmanları: Karl Schiller (-517), Karl Biedermann (-270), Dr. Raffael Wolff (-363)
- **Innovative Solutions tarafı:** innovativesolutions@aws.at · +43 1 501 75-880 (Pzt–Cum 08:30–14:30)
- **Genel bilgi:** 24h-auskunft@aws.at · +43 1 501 75-100
- **Infohour (Innovative Solutions, Almanca, MS Teams):** 19.08.2026, 10:30–12:00 — kayıt aws.at program sayfasından

**Önerilen sıra:**
1. deeptechanfrage@aws.at adresine kısa e-posta → telefon randevusu talep et (taslak aşağıda).
2. Görüşmede netleştir: (a) Deep Tech mi Innovative Solutions mı, (b) FMA istisnası bize dokunuyor mu, (c) Preseed mi Seedfinancing mi, (d) başvuru dili (DE/EN) ve jüri takvimi.
3. Görüşme sonucuna göre aws şablonlarını indir, belgeleri hazırla, Fördermanager'dan başvur.
4. Paralel: aws IP Coaching randevusu (IP stratejisi jüri için kritik).

### E-posta taslağı (Almanca)

> **Betreff:** Terminanfrage aws Preseed | Seedfinancing – Deep Tech: KI-basierte Aktienanalyse-Plattform (FinPilot, Wien)
>
> Sehr geehrte Damen und Herren,
>
> mein Name ist Ibrahim Meriç Başak, Gründer von FinPilot (Wien). FinPilot ist eine KI-gestützte Aktienanalyse-Plattform auf Basis von Deep-Reinforcement-Learning-Modellen und einem mehrstufigen Signal-Scanner. Ein funktionsfähiger Prototyp mit umfangreichen, walk-forward-validierten Backtests liegt vor.
>
> Wir bereiten eine Einreichung im Programm aws Preseed | Seedfinancing vor und würden gerne vorab in einem telefonischen Informationstermin klären:
> 1. ob unser Vorhaben der Programmlinie **Deep Tech (Digitalisierung/ICT)** oder Innovative Solutions zuzuordnen ist,
> 2. ob unser Geschäftsmodell (Analyse-Software als Entscheidungsunterstützung, keine konzessionspflichtige Anlageberatung) von den Ausschlusskriterien im Finanzierungsbereich betroffen ist,
> 3. welches Modul (Preseed bzw. Seedfinancing) zu unserem Unternehmensstatus passt.
>
> Gerne sende ich vorab unser Pitch Deck. Vielen Dank im Voraus — ich freue mich auf Ihre Rückmeldung.
>
> Mit freundlichen Grüßen
> Ibrahim Meriç Başak
> FinPilot · Wien · mericbsk@gmail.com · +43 …

*(İngilizce de kabul görür; ancak infohour'ların Almanca olması kurumsal dilin Almanca olduğunu gösteriyor — Almanca başlamak avantaj.)*

---

## 6. Önerilen Zaman Planı

| Hafta | Adım |
|---|---|
| Bu hafta | E-posta → telefon randevusu; aws şablonlarını indir |
| H1–H2 | Uzman görüşmesi; hat/modül kararı; IP Coaching talebi |
| H2–H5 | Business plan (25 s.), aws-format pitch deck, Integrale Planung (iş paketleri + maliyet), CV'ler; Finanzplan rakamlarını güncelle |
| H5–H6 | Fördermanager'dan başvuru (bir sonraki jüri dönemini yakalamak için) |
| Sonrası | Formal/içerik ön eleme → jüri pitch'i (Deep Tech'te jüri önünde sunum var) |

---

## Kaynaklar
- https://www.aws.at/en/aws-preseed-seedfinancing/
- https://www.aws.at/en/aws-preseed-innovative-solutions/
- https://www.aws.at/en/aws-seedfinancing-innovative-solutions/
- https://www.aws.at/en/aws-preseed-deep-tech/
- https://www.aws.at/en/aws-seedfinancing-deep-tech/
- Programmdokument (PDF): https://www.aws.at/fileadmin/user_upload/Downloads/Sonstiges/2024_Programmdokument__Preseed_Seedfinancing_en.pdf
