# FinPilot Proje Yönetimi — Değerlendirme + Sağ-Boyutlu İşletim Modeli
Durum: TASLAK (karar bekliyor) · 2026-08-03 · Layer: 05-governance · Eskalasyon: Level A (analiz)
Girdi: Kullanıcının "şirket gibi yönet / FinPilot OS / departman + CEO / ikinci beyin / feature-freeze / haftalık tek odak" önerisi.
Yöntem: Öneriyi **projede zaten var olan** yönetişim varlıklarıyla karşılaştırdım (kanıt: mevcut dosyalar).

---

## 0. Tek paragraf hüküm

Teşhisin **%100 doğru**: proje tek kişinin beyninde tutulamayacak kadar büyüdü ve asıl hastalık
kapsam genişlemesi. Ama önerdiğin **yapının ~%80'i zaten kurulu** (otorite haritası, decision-log,
ADR, PARKING_LOT, escalation, envanter, yol haritası, hatta bir CTO due-diligence ve `.finpilot/`
ortak-beyin). Dahası: senin **kendi CTO Due Diligence'ın (2026-08-02)** aynı teşhise varmış ve
önerinin bir kısmına — "web Control Center kurma", "yeni sistem açma", "30 gün yönetim altyapısı" —
**açıkça karşı çıkmış.** Yani gerçek risk şu: *"FinPilot OS'u inşa etmek"* kapsam-genişlemesi
hastalığının **bir sonraki nüksü** olur. Boğulmanın çaresi daha çok yapı değil; **disiplin + çıkarma +
lansmanı bitirme.** Aşağıda önerinin hangi parçasını al, hangisini ertele, ve mevcut varlıklarla
kurulacak **ince** işletim modelini veriyorum.

---

## 1. Önerin vs Gerçek (kanıtlı eşleme)

| Önerin | Projede zaten var olan (kanıt) | Boşluk | Hüküm |
|---|---|---|---|
| Şirket/departman + her departmana CEO | `docs/INDEX.md` manifest'te `owner`+`applies_to` (governance/research/content/…); `ENVANTER-tum-bilesenler.md` | Sahip etiketleri eksiksiz değil | **Hafif al**: sahip/sınır etiketle; kurumsal simülasyon KURMA |
| Living documentation (CEO/Vision/Roadmap/Decisions/Architecture/…) | INDEX.md + decision-log.md (37KB) + `docs/adr/` + `2026-07-31-genel-yol-haritasi` + CTO-DD + PROJE-HIKAYESI | manifest 3 "gap" işaretliyor: architecture, product-rules, risk-policy | **Boşlukları doldur** (3 tek-sayfalık); 11 yeni kök dosya AÇMA (daha çok dağınıklık) |
| Her ajanın kendi hafızası | per-dizin `CLAUDE.md` + skills + `.finpilot/` ortak-beyin (bu oturum) | Kullanım oturmamış | **Mevcudu kullan**; hafıza-sistemi İNŞA ETME |
| İkinci beyin (Decisions/Lessons/Standards/Patterns/Open Q) | decision-log + ADR + `_instructions/00-core` (standartlar) | Lessons/Patterns dağınık | **Çoğu var**; tek "Açık Sorular" sayfası eklenebilir |
| Feature-freeze ("problem yazılmadan özellik yok") | `PARKING_LOT.md` ("lansmana kadar dokunulmayacak fikirler") + escalation Level B gerekçe şartı | Kural var, **uygulanmıyor** | ✅ **EN İYİ FİKİR — zaten iskelesi var; UYGULA** |
| Haftalık tek-departman odağı | Yok (formalize değil) | — | ✅ **En ucuz-en yüksek değer yeni alışkanlık** (CTO-DD "tek cephe" ile aynı) |
| FinPilot OS / CEO Dashboard (uygulama) | — | — | ⛔ **ERTELE** — CTO-DD açıkça "Control Center kurma" diyor; yerine tek-sayfa markdown |
| 30 gün yalnız yönetim altyapısı | — | — | ⛔ **REDDET** — lansmanı geciktirir; ince PM'i lansmana PARALEL yürüt |

**Okuma:** İstediğin şeylerin çoğu kurulu; eksik olan **yapı değil, disiplin ve bitirme**.

---

## 2. Kuzey yıldızı (kendi belgelerinden — planı bu belirler)

Proje yönetimi estetik değil; şu üç gerçeğe hizmet etmeli (hepsi kendi dokümanlarında yazılı):
1. **Edge kanıtlanmadı.** `2026-07-31-genel-yol-haritasi` §0: ölçülen pencerede sinyaller pozitif edge
   üretmedi (piyasadan ve kontrol grubundan kötü). Bu, her aşağı-akış yatırımı gating'liyor.
2. **Traction ~0.** CTO-DD §14/§18: 0 ödeyen, ~0 gerçek kullanıcı; lansman 2/10.
3. **Asıl borç odakta, kodda değil.** CTO-DD genel özet: "En büyük teknik borç kodda değil, **odakta**."

Sonuç: PM sisteminin **tek işi** enerjiyi (a) edge kanıtı, (b) lansman, (c) ilk kullanıcılar üstünde
tutmak; org-şeması yapmak değil. Yönetim inşaatı bu üçünden çalıyorsa, hastalığın kendisidir.

---

## 3. Sağ-boyutlu işletim modeli (asıl uygulanacak — minimal)

Yeni bir OS değil; **mevcut varlıklara ince bir disiplin katmanı.** Yedi öğe:

**3.1 — Tek kontrol yüzeyi (uygulama değil, tek sayfa).**
`LAUNCH_CHECKLIST.md`'i (zaten "durum panosu" otoritesi) **tek giriş noktası** yap: en üstte
"BUGÜN TEK İŞ" + "BU HAFTA TEK CEPHE" + mevcut dokümanlara linkler (INDEX, roadmap, decision-log,
PARKING_LOT). Yeni dosya yok — var olanı zenginleştir.

**3.2 — Haftalık ritim (tek cephe kuralı).**
Pazartesi: **1 stratejik + 1 operasyonel** cephe seç (fazlası yasak). Cuma: 15 dk gözden geçir →
kararları decision-log'a bir satır. "Aynı anda tek cephe" (CTO-DD altın kuralı).

**3.3 — Feature-freeze KAPISI (uygula, kurma).**
Kural: hiçbir yeni özellik/sistem, "**bu, mevcut lansmanın hangi problemini çözüyor?**" bir cümlede
yazılmadan başlamaz. Yazılamıyorsa → `PARKING_LOT.md`. (İskele hazır; eksik olan uygulama.)

**3.4 — Yalnız işaretli SSoT boşluklarını doldur (ucuz, tek-sayfa).**
manifest'in "gap" dediği üçü, dokunulduğunda birer tek-sayfaya indir: `architecture.md` (modül
sınırları), `product-rules.md` (composite score/eşikler — şu an yalnız kodda), `risk-policy.md`.
11 dosyalık yeni ağaç AÇMA.

**3.5 — Taslak governance'ı onayla (30 dk, sistemi açar).**
`_instructions/` 01-governance, 05-escalation, 08-security **hâlâ "draft, Meriç onayı bekliyor"**;
otorite manifesti de öyle. Bunları ratify et → yönetişim sistemi "taslak" olmaktan çıkıp bağlayıcı olur.

**3.6 — Çıkarma sprinti (lansmandan SONRA, 1 hafta) — CTO-DD'den.**
~90 kök script → `experiments/`; 23 ajan → çekirdek **4-5** (scan→analiz→risk→rationale→publish),
gerisi park; ölü kod sil; gerçek CI. Bu, "karmaşıklığı yönet" isteğinin **somut** karşılığı.

**3.7 — Ajan-başı kapsam (mevcutla).**
Bana/araçlara iş verirken **modülü adıyla çağır** ("Ledger web", "distribution", "academy") →
per-dizin `CLAUDE.md` + skills zaten o bağlamı yüklüyor. Yeni hafıza altyapısı gerekmez.

---

## 4. Somut takvim (sağ-boyutlu — lansman ana ray, PM ince paralel)

PM ritüeli haftada ~2-3 saat; ana enerji lansmanda. "Tek cephe" örnek 4 hafta:

```
HAFTA 1  Cephe: ÖLÇÜM (edge kanıtı)     PM: 3.1 kontrol yüzeyi + 3.5 governance onay (30 dk)
         → P0.1 çok-pencere biriktir; P0.2 karne EOD göçü kararı
HAFTA 2  Cephe: DAĞITIM tek-kaynak      PM: 3.2 haftalık ritim başlat; 3.3 feature-freeze kapısı
         → web ↔ Render snapshot; deploy/env doğrula
HAFTA 3  Cephe: KREDİBİLİTE/LANSMAN      PM: 3.4 architecture.md (dokununca) tek-sayfa
         → newsroom mockup temizliği; ilk 3 kullanıcı onboarding testi
HAFTA 4  Cephe: aws IMPACT anlatısı      PM: Cuma retro → decision-log
         → FinSense public + positioning (koşut)
LANSMAN SONRASI (1 hafta)  Cephe: ÇIKARMA sprinti (3.6)  → script arşiv, ajan kes, CI, ölü kod
```

Kural: bir hafta bir cephe. Başka cepheye "küçük bir dokunuş" bile yok (tek cephe disiplini).

---

## 5. Tek-sayfa şablonlar (kopyala-kullan, hepsi küçük)

**A) Kontrol yüzeyi başlığı (LAUNCH_CHECKLIST.md en üstüne):**
```
## 🎯 BUGÜN TEK İŞ: <...>
## 🧭 BU HAFTA TEK CEPHE: <...>   (stratejik: <...> · operasyonel: <...>)
Linkler: INDEX.md · genel-yol-haritasi · decision-log · PARKING_LOT
Kapılar: edge kanıtı [○] · legal [○] · SMTP rotasyon [○] · bot tek-poller [○]
```

**B) Feature-freeze kapısı (yeni fikir gelince):**
```
Fikir: <...>
Bu LANSMANIN hangi problemini çözüyor? <bir cümle — yazılamıyorsa → PARKING_LOT>
Seviye: A/B/C · Hangi cepheyi bozar? <...> · Karar: BAŞLA / PARK
```

**C) Haftalık retro (Cuma, decision-log'a 1 blok):**
```
Hafta <n> · Cephe: <...> · İlerleme: <...> · Öğrenilen: <...>
Gelecek hafta tek cephe: <...> · Park edilen dürtüler: <...>
```

---

## 6. Ne sonuç elde ederiz (dürüst beklenti)

| Adım | Sonuç | Güven |
|---|---|---|
| Tek kontrol yüzeyi + haftalık tek cephe | "Her şeyi aynı anda tutma" yükü biter; her gün tek net iş | Yüksek |
| Feature-freeze uygulaması | Kapsam-genişlemesi **kaynağında** durur (asıl hastalık) | Yüksek |
| Taslak governance onayı | Yönetişim "taslak"tan bağlayıcıya geçer; ajanlar tutarlı | Yüksek |
| SSoT gap doldurma (dokununca) | "3 ay sonraki sen nereden başlayacağını bulur" | Orta-Yüksek |
| Çıkarma sprinti (lansman sonrası) | ~90 script + 23 ajan borcu erir; bakım yükü düşer | Yüksek (CTO-DD ile hizalı) |
| **FinPilot OS inşası (önerilmiyor)** | Enerjiyi lansmandan çeker = hastalığın nüksü | — (bu yüzden ERTELENDİ) |

**Net:** Disiplin + çıkarma, sıfır yeni yazılım, lansman-öncelikli. Karmaşıklık **yönetilir hale gelir**
çünkü büyümesini durdurur ve fazlasını budarsın — yeni bir katman ekleyerek değil.

---

## 7. Yapma listesi (kendi CTO-DD'nin §F'iyle aynı — pekiştirme)
- ⛔ Şimdi FinPilot OS / web CEO Dashboard **kurma** (uygulama). Tek-sayfa markdown yeter.
- ⛔ 11 yeni kök yönetim dosyası açma — mevcut ~110 belgeye eklemek dağınıklığı artırır.
- ⛔ Yeni ajan/sistem ekleme; aksine 23→5'e indir (park).
- ⛔ 30 günü yönetim altyapısına ayırma; lansman ana ray kalsın.
- ⛔ Departman simülasyonu (her departmana ayrı CEO) — tek kişilik operasyonda tören yükü.
- ✅ Yap: haftalık tek cephe, feature-freeze uygula, taslak governance onayla, boşlukları dokununca doldur, lansman sonrası çıkarma sprinti.

---

## 8. Açık kararlar (senden)
1. Bu ince modeli benimsiyor musun (yeni OS yerine)?
2. Taslak `_instructions/` (governance/escalation/security) + otorite manifestini **onaylıyor musun** (Level B)? Onay = 30 dk, sistemi açar.
3. Bu haftanın **tek cephesi** ne? (öneri: ÖLÇÜM/edge kanıtı — her şeyin kapısı.)

_İlgili otoriteler: `docs/INDEX.md`, `docs/governance/decision-log.md`, `docs/2026-08-02-CTO-TEKNIK-DUE-DILIGENCE.md`, `docs/2026-07-31-genel-yol-haritasi-ve-oncelikler.md`, `PARKING_LOT.md`, `LAUNCH_CHECKLIST.md`._
