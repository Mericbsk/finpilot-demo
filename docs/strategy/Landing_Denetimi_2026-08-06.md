# FinPilot Landing — Kanıta Dayalı Denetim (önceliklendirilmiş)
Durum: DENETİM · 2026-08-06 · Kaynak: canlı finpilot.at (Edition No. 11, taze çekim) + kod (layout.tsx, ledger bileşenleri, demo/page.tsx)
Not: Ölçüm gerektiren yerler **UNVERIFIED** işaretli. Bu, 40-bölümlük master prompt'un **80/20**'si — lansmanı oynatan kısım.

---

## 0. Yönetici hükmü (önce cevap)

Landing **iki kimlik arasında sıkışmış:** gövdesi dürüst, stratejiyle hizalı bir *piyasa-okuma/ledger*
ürünü; ama meta/SEO katmanı + Newsroom mockup'ı hâlâ eski *"AI stock picker + buy/sell"* döneminden.
**Çekirdek gerçekten güçlü** (dürüst karne, "gürültü basmaktansa hiçbir şey basmayız", gerçek edisyon,
methodology). Onu baltalayan **~4 dürüstlük çelişkisi** var. Bunlar temizlenirse sayfa lansmana
kredibl olur. **Yeniden tasarım erken ve gereksiz** — gereken redesign değil, **çıkarma.**

**Yayına hazır mı?** Gövde evet; ama meta "buy/sell signals" + etiketsiz mockup + kanıtsız kalibrasyon
iddiası **davetten önce düzeltilmeli** (compliance + güven). "Fix-4" sonrası → evet.

---

## 1. 5 saniye testi (canlı sayfa)

| Soru | Sonuç | Neden |
|---|---|---|
| Bu ürün nedir? | **PARTIAL** | "The FinPilot Ledger — grades + reasons, printed daily" ayırt edici; ama sekme başlığı/meta "Stock Intelligence + buy/sell" diyor → karışık sinyal |
| Kimin için? | **FAIL** | Hedef kullanıcı hiçbir yerde net değil |
| Hangi problemi çözüyor? | **PARTIAL** | İmalı ("guessing"), açık değil |
| Neden farklı? | **PASS** | "her grade, her sebep" + dürüst karne + "not a chatbot wearing a trading costume" |
| Neden ilgileneyim? / Şimdi ne yapayım? | **PASS** | "Read Today's Edition" net tek CTA |

---

## 2. Pozisyonlandırma denetimi — EN KRİTİK BULGU

**Gövde** (Market Reasoning / dürüst ledger) ile **meta/SEO** (AI stock picker + buy/sell) **çelişiyor:**
- `layout.tsx` title: *"AI-Powered Stock Intelligence"* · desc: *"Clear **buy/hold/sell signals**… **12 trained RL models**… Not an LLM wrapper — real AI"* · keywords: *buy/hold/sell, AI stock picks, algorithmic trading*.
- Bu, Google sonucu + link paylaşım kartı + sekme başlığı = ziyaretçinin **ilk izlenimi**, ve tüm "tavsiye değil / Grade dili" kimliğiyle **doğrudan çelişiyor** (compliance riski).

**Kategori önerisi (kanıtla):** Gövde zaten **Daily Market Reasoning / honest research ledger**'a
oturuyor — meta'yı buna hizala. "AI financial assistant / stock picker" = compliance riski + kalabalık;
"academy" = fazla eğitim-ürünü hissi. En güçlü: **açık-karneli günlük piyasa-okuma bülteni.**

---

## 3. Güven & kanıt denetimi (projenin en güçlü yanı — ama lekeli)

**GÜÇLÜ (koru):**
- **Ledger Strip = dürüst karne canlıda:** *5206 kapalı · %30 isabet · +%0.40 beklenti · "düşük isabet tasarım gereği, kazanan büyük/kaybeden küçük."* — kaçıranları gösteren, sektörde nadir bir güven hamlesi.
- *"Quiet tape, quiet ledger — we would rather print nothing than print noise."* — güçlü dürüstlük.
- Methodology linki + her ekranda disclaimer + /demo *"This is not a mockup… judge us with hindsight."*

**LEKELER (düzelt):**
1. **Newsroom mockup, etiketsiz, gerçek edisyonun yanında:** uydurma NVDA 87 / META 79, "Editorial Board Trend Editor %92", "walk-forward evidence · Sample window 2 years". Ziyaretçi bunu *gerçek* sanır → dürüst-karne mesajını çürütür. 🔴
2. **Kalibrasyon iddiası hem kanıtsız hem kendi karnesiyle çelişik:** Classroom *"'~60/70%' işaretlediklerimizin ~%60/70'i hareket eder"* diyor; hemen üstteki Ledger Strip *"%30 isabet"* diyor. Aynı sayfada iki zıt sayı + kanıt yok. 🔴
3. **"12 DRL models" hero istatistiği:** DRL **parked**; kanıtsız overclaim. 🔴

---

## 4. Şekil/kalite kusurları (gövde)
- **SHOP paragrafı iki kez birebir** (Yesterday's Edition + Daily Double "Today's Case") — kopya.
- **Classroom** = 3 sözlük tanımı (squeeze/kalibrasyon/risk-getiri), vaka-dersi değil — "reasoning" vaadinin altında kalıyor.
- Hero istatistikleri ("3 Expert agents" / "12 DRL models") ürün-diliyle değil, eski teknik-övünme diliyle.

---

## 5. UNVERIFIED (araç/cihaz gerektirir — uydurmuyorum)
- **Performans (LCP/CLS/INP), bundle, font/görsel maliyeti:** ölçülmedi → sen PageSpeed/Lighthouse çalıştır.
- **Erişilebilirlik (WCAG kontrast/klavye/odak/alt-metin):** otomatik+manuel test gerek.
- **Mobil 3-cihaz render:** lansman planı madde 3 — henüz doğrulanmadı.
- **Rakip analizi:** bu denetimde web araştırması yapmadım (istersen ayrı tur).

---

## 6. KEEP / CHANGE / REMOVE

**KEEP:** Ledger/gazete metaforu · dürüst Ledger Strip (karne) · "rather print nothing than noise" ·
How It's Made (sade dil) · "not a chatbot wearing a trading costume" · disclaimer'lar · /demo dürüstlüğü + 3 soru.

**CHANGE:** meta/title/keywords → reasoning/eğitim/karne dili, buy-sell çıkar · hero "12 DRL models" → gerçek ·
kalibrasyon iddiası → karneyle tutarlı ya da kaldır · SHOP kopyasını tekille · hero'ya "kimin için + hangi problem" tek satır.

**REMOVE / LABEL:** Newsroom mockup → ya net *"örnek — canlı veri değil, süreç gösterimi"* etiketle, ya kaldır.

---

## 7. Fırsat haritası (P0→P3)

**P0 — Kritik (dürüstlük/compliance; ucuz, yüksek güven):**
1. Meta/SEO'yu düzelt (buy/sell + stock-picker + "12 DRL" çıkar). Dosya: `web/src/app/layout.tsx`.
2. Kalibrasyon iddiasını karneyle tutarlı yap ya da kaldır (ClassroomPreview + landing metni).
3. Newsroom mockup'ı etiketle/kaldır.
4. Hero "12 DRL models" istatistiğini gerçekle değiştir.

**P1 — Yüksek etki (netlik):** hero'da "kimin için + hangi problem" · SHOP kopyasını tekille ·
Classroom'u tek gerçek vaka-dersine derinleştir (akademideki 6 yayınlı dersten).

**P2 — Orta:** mobil doğrulama (UNVERIFIED) · görsel ritim/whitespace · "60+ readers" iddiasını gerçek waitlist sayısıyla teyit et.

**P3 — Deney (TEST FIRST, şimdi değil):** tam redesign yönleri · hero A/B · CTA varyantları.

---

## 8. Son üç liste

**DO NOW** (davetten önce, ~1 commit): P0'ın 4 maddesi — hepsi dürüstlük/compliance, ucuz, güveni artırır.

**TEST FIRST** (deney olmadan yapma): tam görsel redesign · hero mesajını komple değiştirme · yeni bölüm ekleme · CTA sayısını çoğaltma.

**DO NOT DO** (stratejiyi zayıflatır): "buy/sell / accuracy / edge / dünyanın en iyisi" diline dönüş ·
mockup'ı gerçekmiş gibi tutma · kanıtsız kalibrasyon/DRL iddiaları · PMF öncesi büyük redesign/dashboard yatırımı.

---

## 9. §40'a cevap — "AI finans ürünü mü, yeni kategori mi?"
Şu an **arada.** Gövde yeni kategoriye (dürüst piyasa-okuma) ait; meta + mockup + kalibrasyon iddiası
onu eski "AI stock picker"a geri çekiyor. **Kategoriye geçiş için redesign gerekmez — P0'daki 4 eski
kalıntıyı ÇIKARMAK yeter.** Çıkarma, bu sayfayı dürüst-reasoning kategorisine taşıyan tek hamle.

_İlgili: `Morning_Ledger_Urun_Stratejisi_Konsolide`, `Lansman_Yurutme_Plani`, `web/src/app/layout.tsx`, `web/src/components/ledger/Newsroom.tsx` + `ClassroomPreview.tsx`._
