# aws Preseed – Deep Tech Başvuru Hazırlık Paketi
**FinPilot · 22.07.2026 · Hedef: Preseed – Deep Tech (şirket henüz kurulmadı → gerçek kişi başvurusu) · Belgeler: İngilizce**

---

## 1. Hedef Program Özeti

| Parametre | Değer |
|---|---|
| Program | aws Preseed – Deep Tech (Digitalisation/ICT) |
| Hibe | Maks. **€267.000**, geri ödemesiz (= uygun maliyetlerin %80'i → toplam proje ~€334k) |
| Öz kaynak | Toplam maliyetin **≥%10'u** ortak öz kaynağı (~€33k); +%10 satış/uzun vadeli finansman olabilir |
| Süre | 1–2 yıl proje; milestone bazlı ödeme |
| Başvuru | Sürekli açık, aws Fördermanager (foerdermanager.aws.at) üzerinden |
| Karar | Ön inceleme → dış jüri önünde **pitch** → karar (jüri ~çeyrekte bir) |
| Başarı oranı | ~%25 |

**Kritik kurallar:** Başvurudan önce oluşan maliyetler fonlanmaz · Preseed şirketi başvuranın **tek şirketi** olmalı · De-minimis limiti aşılmamalı · Proje lokasyonu Avusturya · Başvuru proje başlamadan yapılmalı.

## 2. Belge Checklist'i (resmi kaynaklardan)

| ✔ | Belge | Not / Şablon |
|---|---|---|
| ☐ | **Fördermanager online başvuru formu** | Proje tanımı, tarih aralığı, lokasyon, istenen tutar, diğer destekler beyanı |
| ☐ | **Business plan / proje konsepti** | Ürün/USP, iş modeli, pazarlar, rekabet, ekip, finansal plan + **Deep Tech şartı: state-of-the-art'tan kapsamlı farklılaşma bölümü** |
| ☐ | **Integrale Planung (xlsx)** | Zorunlu aws şablonu: iş paketleri + maliyet + zaman planı → [indir](https://www.aws.at/fileadmin/user_upload/Downloads/Antrag/aws_Preseed_Integrale_Planung.xlsx) |
| ☐ | **Ekip CV'leri** | Founder + (varsa) ilk ekip/danışmanlar |
| ☐ | **Kimlik belgesi** | Pasaport/kimlik |
| ☐ | **Pitch deck** | Jüri sunumu için; aşağıdaki kurgu |
| ☐ | Öz kaynak planı | %10'un nereden geleceğinin gösterimi |
| ☐ | Referans dokümanlar | [Programmdokument](https://www.aws.at/fileadmin/user_upload/Downloads/Sonstiges/2024_Programmdokument__Preseed_Seedfinancing_en.pdf) · [Richtlinie](https://www.aws.at/fileadmin/user_upload/Downloads/Richtlinie/ab_20240101_Foerderung_von_Technologie_und_Innovation_RL.pdf) · [aws Businessplan kılavuzu](https://www.aws.at/fileadmin/user_upload/Downloads/ergaenzende_Information/Businessplan_fuer_kleine_und_mittlere_Unternehmen.pdf) |

## 3. Resmi Değerlendirme Kriterleri (Programmdokument §5.2.2) → FinPilot cevabı

1. **Innovation potential** (teknoloji sıçraması + IP stratejisi) → Doğrulama disiplinli faktör motoru + multi-agent DRL hattı; IP: know-how, veri pipeline'ı, metodoloji (aws IP Coaching ile netleştirilecek).
2. **Growth/employment** (ihracat, uluslararasılaşma, istihdam, risk finansmanı potansiyeli) → Global ürün (EN/TR/DE), ABD→AB→global pazar planı, 18 ayda 3 kişilik ekip, Series A hedefi.
3. **Environmental relevance** → Zayıf ayağımız; zorlamadan geçilir (yerel AI = düşük veri transferi gibi marjinal argümanlar abartılmamalı).
4. **Social/societal impact** → FinSense impact engine: finansal okuryazarlık laboratuvarı, AB okuryazarlık gündemi.

## 4. Business Plan İskeleti (~25 sayfa, İngilizce) — mevcut kaynak eşlemesi

| Bölüm (sayfa) | İçerik | Kaynak |
|---|---|---|
| 1. Executive Summary (2) | Yeni tanıtım metni | Tanitim_Revizyon v2 §3 |
| 2. Problem & Market (3) | Retail yatırımcı açığı, okuryazarlık, TAM/SAM/SOM güncellenmiş | NVIDIA deck s.2, s.6 (rakamlar tazelenecek) |
| 3. Product (4) | Morning Ledger × Classroom, Grade sistemi, açık karne, Reader's Desk | Master Tasarım + Uçtan Uca Plan |
| 4. Technology & **State-of-the-Art Differentiation** (5) | V2 faktör motoru, doğrulama bataryası (locked-OOS, triple-barrier, cluster-bootstrap), multi-agent DRL hattı; neden mevcut araçlardan (tarama servisleri, sinyal botları, robo-advisor) kategorik farklı | 15.07 Nihai Kontrol + backtest raporları |
| 5. Regtech/Compliance & Security (2) | Tavsiye-dili yasağı, denetlenebilirlik, GDPR, MiFID hazırlığı | Uçtan Uca Plan ilkeleri |
| 6. Business Model (2) | Freemium (ücretsiz brif → premium Full Edition → B2B API) | GTM/Funnel planları |
| 7. Competition (2) | Kategorize rakip analizi + hendek | Yeniden yazılacak |
| 8. Team & Hiring (2) | Founder + M1 ML engineer + danışmanlar; "tek şirket" beyanı | Finanzplan personel planı (küçültülmüş) |
| 9. Financial Plan (3) | Proje bütçesi (aşağıda) + 3 yıl projeksiyon (gerçekçi) | Finanzplan'dan türet, rakamları güncelle |
| 10. Impact & Growth Strategy (1) | Kriter 2+4 cevapları | — |

## 5. İş Paketi / Bütçe Taslağı (Integrale Planung'a girecek — 18 ay, toplam ~€330k)

| WP | İçerik | Süre | Tahmini maliyet |
|---|---|---|---|
| WP1 | **Truth Engine & veri bütünlüğü:** arşiv/resolver zincirinin üretimleştirilmesi, açık karne canlı | M1–M4 | €35k |
| WP2 | **Skorlama Ar-Ge:** V2 shadow validation, faktör araştırması, multi-agent DRL deney hattı | M1–M12 | €85k |
| WP3 | **Ürün:** Morning Ledger public yüzey + Reader's Desk dashboard (Next.js) | M2–M10 | €70k |
| WP4 | **FinSense Impact Engine:** otomatik ders üretimi, kalibrasyon antrenörü, kör-nokta haritası | M4–M14 | €55k |
| WP5 | **Regtech/compliance & güvenlik:** hukuki görüş, uyum katmanı, güvenlik denetimi | M3–M12 | €35k |
| WP6 | **Pazar doğrulama:** beta lansmanı, 1.000 kullanıcı, ödeme entegrasyonu | M8–M18 | €50k |
| | **Toplam** | | **~€330k** → hibe ~€264k + öz kaynak ~€33k + diğer ~€33k |

*Maliyet kalemleri: personel (founder maaşı Preseed'de uygun maliyettir + ML engineer), üçüncü taraf hizmetler (hukuk, güvenlik denetimi, tasarım), veri API'leri, altyapı.*

## 6. Pitch Deck Yeni Kurgusu (13 slayt, İngilizce)

1. **Cover** — "Institutional-grade analytics & decision-support infrastructure for retail investors" · Vienna · Preseed – Deep Tech
2. **Problem** — retail underperformance + araç uçurumu + okuryazarlık açığı (güncel kaynaklarla)
3. **Solution** — Morning Ledger × Classroom: Grade A/B/C + açık karne + öğreten yüzey (3 katman)
4. **Product demo** — Yesterday's Edition ekranı + karne şeridi
5. **Technology** — V2 faktör motoru mimarisi; DRL = Labs araştırma hattı
6. **R&D discipline (state-of-the-art farkı)** — locked-OOS, triple-barrier replay, "precision ≠ P&L" olgunluğu; rakiplerin yapmadığı şey
7. **Validation evidence** — ~30 testlik batarya bulguları + canlı karne (⚠️ önce resolver canlanmalı)
8. **Regtech/compliance by design** — tavsiye dili yok, denetlenebilirlik, gizlilik-öncelikli yerel AI
9. **Market** — güncellenmiş TAM/SAM/SOM + segmentler
10. **Business model** — freemium → premium → B2B API
11. **Team & hiring plan** — founder profili + M1 işe alımlar + danışman ağı
12. **Roadmap & vision** — "MVP'deyiz; hedef: multi-agent DRL + agent workflows + tam compliance katmanı + multi-market kişisel finansal danışman/eğitmen"
13. **The Ask** — €267k Preseed; WP özeti; milestone'lar; sonraki adım (Seedfinancing – Deep Tech zinciri + Series A)

## 7. FİNAL E-posta (İngilizce) — Strateji güncellemesi: birincil hat **Innovative Solutions**

**Alıcı:** innovativesolutions@aws.at · **Cc (opsiyonel):** deeptechanfrage@aws.at

> **Subject:** Pre-application inquiry — aws Preseed: AI-powered financial literacy platform (FinPilot, Vienna)
>
> Dear aws Preseed | Seedfinancing team,
>
> My name is Ibrahim Meriç Başak, founder of FinPilot, a Vienna-based project currently in the pre-foundation stage. FinPilot is an **interactive financial literacy platform** for retail investors: a daily "Morning Ledger" turns real, graded stock cases into micro-lessons, calibration training and personalised learning paths — and holds itself accountable through a public scorecard that records every outcome, including the misses. The engine behind it is validated with institutional-grade methods (locked out-of-sample testing, execution replay with realistic costs).
>
> We are preparing a **Preseed** application and see our innovation impact primarily in the **Education** area (Innovative Solutions). Before submitting via the Fördermanager, we would appreciate a short call — or guidance by e-mail — on four points:
> 1. **Programme line:** we read our project as Innovative Solutions (education impact); however, the underlying AI/ML engine is substantial — would aws assess it as Innovative Solutions or Deep Tech?
> 2. **Exclusion criteria:** our software provides analysis and education only — no licensed investment advice and no activity supervised by the FMA. Is our model affected by the exclusion concerning the financing sector?
> 3. **Eligibility & team:** applying as a natural person in the pre-foundation stage, as a solo founder with first hires planned within the project — any concerns we should address in the application?
> 4. **Language:** may the application documents be submitted in English?
>
> I plan to join the Infohour on 19 August as well. I would be happy to send our pitch deck in advance. Thank you very much — I look forward to your reply.
>
> Kind regards,
> Ibrahim Meriç Başak
> Founder, FinPilot · Vienna
> mericbsk@gmail.com · +43 ___ *(telefon eklenecek)*

*Not: Görüşmede aws "özünüz Deep Tech" derse, Deep Tech versiyonu deck hazır (`FinPilot_Pitch_Deck_aws_Preseed_DeepTech.pptx`); IS onayı gelirse IS versiyonu kullanılır (`FinPilot_Pitch_Deck_aws_Preseed_InnovativeSolutions.pptx`). Bütçe farkı: IS €89k/12 ay vs DT €267k/18 ay.*

## 8. Uzman Görüşmesi Soru Listesi
Deep Tech vs Innovative Solutions kararı · FMA istisnası yorumu · TRL beklentisi (prototipimiz TRL 3'ün üstünde — Preseed'e uygunluğu) · "Tek şirket" kuralının yorumu · İngilizce başvuru · Bir sonraki jüri tarihi · Founder maaşının uygun maliyet kapsamı · IP Coaching randevusu.

## 9. Aksiyon Sırası

1. **Bu hafta:** E-postayı gönder (§7) + Integrale Planung xlsx'i indir + telefon numarasını e-postaya ekle
2. **Görüşme öncesi:** Resolver/karne zincirini canlandır (en güçlü kanıtımız; şu an boş)
3. **Görüşme sonrası:** Business plan yazımı (§4 iskeleti) + Integrale Planung doldurma (§5) + deck üretimi (§6)
4. **Hedef:** Bir sonraki jüri dönemine yetişecek şekilde Fördermanager başvurusu
