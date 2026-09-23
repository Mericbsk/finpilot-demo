# Notebook Prompt — FinPilot × FinSense Sunum Üretimi

**Amaç:** Bu prompt, `docs/pitch_deck_presentation_spec_2026-09-07.md` (v1.0) ile birlikte bir slayt üretim aracına (notebook) verilir. Spec'i tek gerçek kaynak olarak oku; bu prompt görsel dili, tonu ve anlatı ivmesini tanımlar.

---

## GÖREV

`docs/pitch_deck_presentation_spec_2026-09-07.md` dosyasındaki 13-slayt spesifikasyonunu, aşağıdaki görsel/anlatı kurallarıyla **etkileyici, yatırımcı-facing bir sunum** olarak üret. Spec'teki hiçbir kuralı ihlal etme — özellikle dört rakam ayrımı, [V]/[S]/[C]/[A] etiketleri, "do not say" listeleri ve omurga cümle.

---

## GÖRSEL DİL

- **Tema:** Koyu zemin, tek vurgu rengi (elektrik mavisi veya zümrüt yeşili), geniş beyaz boşluk. Finansal-teknik ama soğuk değil — "kanıt sunan laboratuvar" hissi.
- **Tipografi:** Başlıklar büyük ve kısa (max 8 kelime). Veri tabloları monospace değil, temiz sans-serif. Her rakamın etiketi ([V]/[S]/[C]/[A]) küçük bir köşe işareti olarak görsel olarak korunur — silinmez.
- **Veri görselleri:** Slide 4 dağılımı için yatay bar chart (barrier-captured), MFE için ayrı renkli tek karşılaştırma çubuğu (offered vs captured). İki panel asla aynı eksende birleşmez.
- **Ikonlar:** Minimal, tek çizgi. Her slaytta en fazla bir görsel vurgu.

## ANLATI İVMESİ

Sunum "geleceğimiz ve potansiyelimiz" hissini **rakamlar üzerinden** taşımalı — ama yalnızca ölçülmüş/doğrulanmış rakamlarla. Kullanılabilir gerçek momentum rakamları (2026-09-07 repo/DB sorgusu, hepsi [V]):

- **89 araştırma raporu** üretildi (`reports/*.md`)
- **23 ajan** çalışır durumda (`agents/`)
- **5.216 tarihsel sinyal** çözümlendi
- **1.812 sembol** günlük evren, 1.801 satır/gün
- **12 akademi domain'i, 69 modül** tanımlı
- **96 ders** üretildi (8 yayında, 88 draft — FinSense DB)

Bu rakamlar "nereden geldiğimizi" gösterir. "Nereye gittiğimizi" gösterenler ise spec'teki forward-looking bölümler (Slide 10 GO/NO-GO, Slide 11 FinSense senaryosu, Slide 12 bilgi haritası).

**Kritik kural:** Bu momentum rakamlarını Slide 3-5'teki çekirdek bulgularla (5.216, +%0,40, MFE) **karıştırma.** Momentum rakamları ayrı bir "traction/velocity" bağlamında kullanılır — örn. Slide 2'nin "Why Now" genişlemesi veya Slide 12'nin "We Know" sütununu destekleyen bir köşe notu. Asla "işte trading performansımız" olarak sunma.

## YASAKLAR (spec'i tekrarlar)

- ①5,216 ②+%0,40 ③46,581 ④111 — asla görsel olarak birleşmez
- 111 asla "%100 kazanan hisse" değil
- +%0,40 asla "profit/performance" değil
- "Garanti/kesin/kanıtlanmış edge" yasak
- Verilmeyen sayı EKLEME; eksikse "TBD"
- Haftalık/aylık sabit getiri hedefi yasak
- Catalyst/EDGAR kapsamı iddiası YASAK (cache şu an 8 sembol/0 — regresyon, düzeltilene kadar)
- **Medyan (-%0,64) SİLİNMEZ** — Slide 3'te "current exit architecture" bağlamıyla yeniden çerçevelenir; yatırımcı sorarsa tabloda bulunmalı
- Slide 5 "locked OOS" satırı "kasıtlı olarak kapalı tutuldu (by design)" olarak yumuşatıldı
- Slide 11 FinSense = "Parallel track — not part of this raise" etiketli

## VERİ BÜTÜNLÜĞÜ NOTU (sunuma girmez, çalışma kaydı)

`data/catalyst_cache.json` 2026-09-07 11:28'de 1.801-sembol/548-nonzero halinden 8-sembol/0-nonzero haline geriledi (üzerine yazıldı). Bu, Slide 8'deki "SEC EDGAR pipeline universe-wide refreshed" iddiasını şu an desteklemiyor. Slide 8'i üretirken EDGAR satırını **yumuşat**: "pipeline built and validated on a pilot; full-universe refresh in progress" — ya da satırı "TBD" bırak. Doğru değerler geri yüklendiğinde güncellenir.

## ÇIKTI

13 slayt. Her slayt: başlık + ana mesaj + veri (etiketli) + görsel + dipnot + kaynak. Spec'in yapısal akışını (PAST→PRESENT→FUTURE→VISION) koru. Son slaytta omurga cümleyi tekrarla.

---

**Omurga (spine):**
> "We are not asking capital to prove that our system works. We are using capital to find out, under real market conditions, whether it actually does."
