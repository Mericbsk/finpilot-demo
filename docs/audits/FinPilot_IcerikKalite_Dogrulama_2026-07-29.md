# FinPilot — İÇERİK/YAYIN KALİTESİ: DOĞRULAMA (Faz 1) + ÇÖZÜM (Faz 2) + BAĞIMSIZ GÖRÜŞ
Layer: 04-content + 01-product · 2026-07-29 · Kaynak: FinPilot_Icerik_Kalite_OnArastirma_2026-07-28

## ⚠️ META-BULGU (önce oku)
Bu oturumda **bash ile oluşturduğum bazı dosyalar senin diskinde YOK** (yasal sayfalar, daha önce run_bot.py). Muhtemel neden: mount senkron / commit'lenmeme. Sonuç: "kod eklendi" iddiaları **repo'da doğrulanmalı** ve **git'e commit'lenmeli**. Denetim gerçeği: yasal sayfalar şu an mevcut DEĞİL.

---

## FAZ 1 — DOĞRULAMA TABLOSU (yaklaşık → GERÇEK sayı)
| # | Bulgu | Yöntem | Sonuç | Gerçek kanıt |
|---|---|---|---|---|
| T1 | Rationale havuz-tabanlı, LLM değil | rationale.py oku | **Doğrulandı (kısmi)** | Docstring: "template-based, no LLM". AMA havuz BÜYÜK (~215 fragment, kombinatoryal) → formülleşme riski "küçük havuz" değil, **orta**. E8 varyant raporu kontrol ediyor. |
| T2 | prob_band boşsa "veri birikiyor" | kod+veri | **Kısmen** | Kod bunu yapıyor; karne olgunlaştıkça azalır. Son N brifte kaç kez göründüğü **loglanmadı** (ölçülmedi). |
| T3 | Tek-yönlü, etkileşim yok | bot kodu | **Doğrulandı** | `telegram_bot_runner.py`'de sendPoll/inline_keyboard/anket YOK; yalnız komutlar (/start /feedback /today /premium /help). |
| T4 | Expired geçmişi zayıflatıyor | distribution.db | **Doğrulandı — TAM SAYI** | **11 expired**, 8 tarih (07-13→22); **6 sent**. Yani ~2 haftada teslim 6, kaçan 11. |
| W1 | Metodoloji sayfası yok, Colophon kırık link | route+kod | **Doğrulandı (düzeltmeyle)** | `/methodology` route YOK; Colophon'da link DEĞİL, bir **TODO yorumu** var. Yani "kırık link" değil, "planlı, henüz yok". |
| W2 | academy ~1/5, 39 draft | academy.db | **Doğrulandı — GERÇEK farklı** | **6 published / 73 draft / 79 toplam** (rapor 5/39 = BAYAT). Web'de `academy_lessons.json`=**1 ders**. Darboğaz üretim değil, **yayınlama+export**. |
| W3 | title hâlâ "AI-Powered Stock Intelligence" | layout.tsx | **Doğrulandı** | `title: "FinPilot — AI-Powered Stock Intelligence"` (aynen). |
| W4 | Yasal sayfalar yok (kod eklendi bekliyor) | route | **Doğrulandı — HÂLÂ YOK** | /impressum, /datenschutz, /nutzungsbedingungen route'ları **mevcut değil** (bu oturum eklemem persist etmemiş). |
| W5 | EN/DE tüketimi belirsiz | analytics | **Test Edilmedi** | Analytics/trafik verisi yok → **ölçülmedi**, veri olmadan doğrulanamaz. |
| W6 | Erişilebilirlik doğrulanmadı | Lighthouse/axe | **Test Edilmedi** | Canlı site taraması sandbox'tan yapılamaz → senin makinende Lighthouse/axe koş. |

**Özet:** 4 doğrulandı · 3 kısmen/düzeltmeyle · 2 test edilmedi · 1 gerçek-sayı düzeltmesi (akademi 39→73 draft).

---

## FAZ 2 — ÇÖZÜM (gerçek kanıtla güncellenmiş öncelik)
### Öncelik 1 — Metodoloji sayfası [Level B]
BULGU: yok; Colophon TODO. ÇÖZÜM: "nasıl tarıyoruz / nasıl doğruluyoruz / karne nasıl hesaplanır" sayfası (locked-OOS, triple-barrier, overall expectancy). KANIT: route canlı + Colophon linki açık + lint temiz. FAYDA: güven + hibe (trustworthy AI) + kırık-referans kapanır. EFOR: Düşük. SEVİYE: B (yeni kamuya iddia → lint).

### Öncelik 2 — Akademi YAYINLAMA (üretim değil!) [Level B]
BULGU: **73 draft / 6 published** — içerik VAR, yayın darboğaz. ÇÖZÜM: üretim değil, **inceleme+yayın hattı** — quality_gate eşiğini gözden geçir, günde 2-3 draft'ı elle onayla→published→export. KANIT: published 6→20+; `academy_lessons.json` count 1→20+. FAYDA: SEO + retention + hibe (impact). EFOR: Orta (üretim bitti; inceleme işi). SEVİYE: B.

### Öncelik 3 — Mesaj/positioning [Level A/B]
BULGU: title "AI-Powered Stock Intelligence". ÇÖZÜM: title/description/OG → "trustworthy-AI financial literacy". KANIT: layout.tsx + canlı OG. FAYDA: compliance + repositioning tutarlılığı. EFOR: Düşük. SEVİYE: B (stratejik mesaj → positioning dokümanına da yansı).

### Öncelik 4 — Kesintisiz teslim [ref]
BULGU: 11 expired. ÇÖZÜM: → FinPilot_TekDokunusla_Yayin_Plani (aynı çözüm, tekrar üretme). SEVİYE: B.

### Öncelik 5 — Brife karşı-görüş/risk satırı [Level B]
BULGU: tek-yön; bear/bull/risk agent'ları uykuda. ÇÖZÜM: 1 "risk/karşı-görüş" satırı — **lint kapısı ZORUNLU** (tavsiye-dili riski). KANIT: örnek brifler + lint 0 ihlal. EFOR: Orta. SEVİYE: B.

### Öncelik 6 — Yasal + erişilebilirlik
Yasal: [Level C] — sayfaları YENİDEN oluştur (persist etmedi) + git commit + avukat onayı. Erişilebilirlik: [Level A] — Lighthouse/axe koş, somut düzeltme listesi.

---

## FAZ 3 — 7 EK ÖNERİNİN DEĞERLENDİRİLMESİ (ayrı Level B seti)
- İçerik takvimi & editoryal ses → **Level B** (yeni süreç) — pending.
- Evergreen SEO stratejisi → **Level B** (kaynak tahsisi) — pending.
- Paylaşılabilir istatistik kancası ("5.719 pick izlendi") → **Level A** (mevcut veriyi öne çıkar).
- Etkileşim ölçümü (yayın sayısı değil) → **Level A** (ölçüm metodolojisi).
- Dil disiplini (TR önce) → decision-log ile tutarlı (kanal/dil kararları) — onaylandı.
- Tek-ses/insan riski → gözlem, aksiyon yok, not.
- Karne dürüstlüğü pazarlama varlığı → **Level A** (çerçeveleme).

---

## BAĞIMSIZ GÖRÜŞLERİM (rapordan bağımsız)
1. **En büyük içerik hatası "derinlik" değil, TUTARLILIK: 11 kaçan gün.** Okuyucu 14 günün 6'sını alırsa güveni, az-ama-düzenli içerikten daha hızlı kaybeder. Kesintisiz teslim = 1 numaralı kalite hamlesi.
2. **Akademi darboğazı üretim DEĞİL, yayınlama:** 73 draft bekliyor, 6 published. "Daha çok içerik üret" yanlış hedef; **inceleme+yayın hattı** doğru hedef. AI dersini incelemeden yayınlamak compliance riski — hafif ama gerçek bir editoryal kapı gerek.
3. **Kontrarian uyarı: OKUYUCU YOKken içerik zenginliğine aşırı yatırım erken optimizasyondur.** tg_users=1 → içerik kalitesi şu an GÖZLEMLENMİYOR. Önce 10 gerçek okuyucu → geri bildirimleri içerik önceliğini belirlesin. Kimseye zengin içerik üretmek premature.
4. **En yüksek ROI/efor: metodoloji sayfası + title düzeltmesi** (ikisi de düşük efor, biri güven+hibe biri compliance). Bugün yapılabilir.
5. **Bot anketi ucuz kazanç:** Telegram native `sendPoll` trivial — haftalık 1 anket hem etkileşim hem içerik-yön verisi. Düşük efor.
6. **Persist sorunu bir SÜREÇ hatası:** oluşturulan dosyalar git'e commit'lenmeden "yapıldı" sayılmamalı. Her içerik/kod değişikliği `git add + commit` ile kalıcılaşmalı.

---

## BU DOĞRULAMANIN KAPSAMADIĞI
- **Analytics/trafik** (EN/DE dil dağılımı) — veri yok, ölçülmedi.
- **Canlı erişilebilirlik** (Lighthouse/axe) — sandbox'tan çalıştırılamaz; senin makinende.
- **Canlı site render** (Colophon linki, yasal sayfa görünümü) — kod var/yok doğrulandı ama canlı davranış test edilmedi.
- prob_band "veri birikiyor" mesajının brif geçmişindeki gerçek sıklığı — loglanmadı.

_Level B/C öneriler decision-log'a pending eklendi._
