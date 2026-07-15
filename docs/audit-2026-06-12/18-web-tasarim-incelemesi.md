# FinPilot Ledger — Canlı Web Tasarımı Detaylı İnceleme

**Tarih:** 2026-07-14 · **Kapsam:** "The FinPilot Ledger" landing page (`web/src/app/demo/page.tsx` + `web/src/components/ledger/*`) + açıklama motoru (`distribution/rationale.py`). Ekran görüntüleri + kod incelemesi.

> Bu bir ürün/mesajlaşma ve uyum incelemesidir, yatırım tavsiyesi değildir.

---

## 0. ÖNCE: NE İYİ (kontrol)

- **Açıklama motoru zaten v3'e yükseltilmiş** (`rationale.py`, 2026-07-13 "Ledger landing feedback"). Yeni metin parçaları **sade, nedensel, AL/SAT içermiyor** — doğru yön. Örnek (hacim): *"işlem hacmi normalinin belirgin üzerinde akıyor — ilgiyi tek tük emirler değil, geniş bir katılım oluşturuyor."* Bu kaliteli.
- Kartlar doğru register kullanıyor: **"Grade B", "izleme adayı", "karar ve risk sana aittir", "araştırma hedefi, kâr vaadi değil"**.
- Dürüst uyarılar mevcut: %68 win-rate'in yanında yıldız notu, "Costs, slippage and timing are not included."
- **45/45 birim testi geçiyor** (scanner düzeltmeleri + sentiment sağlam).

**Ama:** sayfa **iki çelişen dil kullanıyor** ve gösterilen içeriğin bir kısmı bayat/eksik. Üç ana sorun aşağıda.

---

## 1. KRİTİK — İKİ ÇELİŞEN REGISTER (AL/SAT sorunu)

Sayfanın üstü ve kartları "**not / izleme adayı / tavsiye değil**" derken, **"INSIDE THE NEWSROOM"** bölümü tam tersini yapıyor: açık **BUY/SELL/HOLD, Consensus: BUY, Entry/Stop/Target, Stop-Loss, R/R**. Bu hem sayfa içinde çelişki hem de **uyum (regülasyon) kırmızı bayrağı** — çünkü hedef fiyat + stop + "BUY" = yatırım tavsiyesi görünümü. Kaynaklar (hepsi hardcoded mock):

| Bileşen | Sorunlu içerik | Konum |
|---|---|---|
| `TheWire.tsx` | `signal: "BUY"/"SELL"/"HOLD"` + `Entry/Stop/Target/R/R` sütunları | satır 13-18, 30-31, 52 |
| `EditorialBoard.tsx` | `vote: "BUY"`, `Consensus: BUY` | satır 13-15, 55 |
| `FactCheckingDesk.tsx` | `Stop-Loss $168.50`, `Target $198.00`, `R/R 1.8` | satır 12-13 |

**Somut düzeltme — Ledger diline çevir (BUY/SELL yok):**

**`TheWire.tsx`** → "SIGNAL" sütunu **"GRADE"** olsun; BUY→**B**, SELL→**C / kaçın**, HOLD→**—**. Entry/Stop/Target/R/R sütunlarını **public sayfadan kaldır** (bunlar "işlem emri" izlenimi verir); yerlerine tek bir "**Neden**" chip'i veya "araştırma bandı (örnek, öneri değil)" koy. Örnek satır: `NVDA · Grade B · "hacim ve momentum aynı yönde"`. (Sayısal seviyeler yalnız giriş-yapılmış dashboard'da, disclaimer + kullanıcı bağlamıyla kalsın.)

**`EditorialBoard.tsx`** → "oy" yerine "okuma":
- "Trend Editor: BUY 92%" → **"Trend okuması: güçlü (92%)"**
- "Range Editor: HOLD 61%" → **"Bant okuması: nötr (61%)"**
- "Volatility Editor: BUY 74%" → **"Oynaklık okuması: elverişli (74%)"**
- "Consensus: BUY 88%" → **"Birleşik okuma: yüksek uyum (Grade B, %88)"**

**`FactCheckingDesk.tsx`** → "Stop-Loss / Target" ifadelerini kaldır veya **"örnek risk bandı / araştırma hedefi — öneri değildir"** olarak, görünür disclaimer'la yeniden çerçevele. "Risk Shield" kavramı iyi; sorun spesifik $ hedef/stop'un tavsiye gibi durması.

**İlke:** Tüm public yüzey **tek dil** konuşmalı: **not (A/B/C) + sade neden + dürüst uyarı.** BUY/SELL/Target/Stop-Loss kelimeleri marketing sayfasında hiç geçmemeli.

---

## 2. DİL VE OLGU HATALARI

| # | Hata | Konum | Düzeltme |
|---|---|---|---|
| 2.1 | **Eksik sayı:** "moved ≥5% within 5 days about **—** of the time" — yüzde yerine tire | `demo/page.tsx:87` (`{c.prob_band}`) | `prob_band` boşsa **tüm cümleyi gizle**; ya da gerçek yüzdeyi doldur. Asla "— of the time" gösterme. |
| 2.2 | **Çelişen istatistik:** stat kartı "**160+** STOCKS SCANNED" ama kopya "**1,800** stocks read/scanned" | stats bileşeni vs `demo/page.tsx:420`, `HowItsMade.tsx:11`, `translations.ts:31` | Tek gerçek: "1.800 taranır → ~160 not alır". Kartı "**1,800 SCANNED**" veya "**160 GRADED**" diye net etiketle. |
| 2.3 | **Karışık dil:** İngilizce başlıklar + Türkçe blurb'lar aynı sayfada | tüm landing | i18n zaten var (`translations.ts`); locale'e göre **tam TR veya tam EN** ver, karıştırma. |
| 2.4 | **Bayat baskı:** gösterilen "yesterday's edition" eski **v2 jargonu** ("teyit merdiveninin ileri aşamasında") | 07-10 snapshot | v3 motoruyla **yeniden üret**; snapshot'ı güncelle. |
| 2.5 | **Kanıtlanmamış iddia:** "12 DRL models" (audit: modeller Mart'tan bayat), "3 expert agents ... vote independently" (dramatizasyon) | stats + Editorial Board | Ya somutlaştır ya yumuşat: "12 model" yerine "çok-faktörlü kalibre skor"; "bağımsız oy veren 3 uzman" yerine "3 bağımsız faktör grubu". |
| 2.6 | **%68 win-rate** öne çıkıyor; audit edge bulamadı | hero stats | Yıldız notu iyi ama daha görünür + "backtest, canlı değil" vurgusu; canlı skor birikince değiştir. |

---

## 3. AÇIKLAMA YENİDEN-YAZIMI (asıl istek: anlaşılır, nedensel, akıcı)

**İlke:** kullanıcıya dönük hiçbir metinde iç jargon olmasın (tier, merdiven, setup, rejim-okuması, confirmation-ladder). Her cümle: **sade kelime + neden önemli + dürüst kayıt.**

### Jargon → sade çeviri sözlüğü

| İç jargon (şu an görünen) | Sade karşılık (herkes anlar) |
|---|---|
| "teyit merdiveninin ileri aşamasında" | "birden fazla gösterge aynı anda olumlu — sinyal tek veriye değil, birbiriyle uyumlu birkaç işarete dayanıyor" |
| "erken-yakalama merdiveninde üst basamakta" | "sistem bu hareketi tam olgunlaşmadan erkenden fark etti" |
| "rejim okuması setup ile aynı yönde" | "genel piyasa havası da bu hisseyi destekliyor, ona karşı çalışmıyor" |
| "makro rejim arka planı olumlu" | "genel piyasa ortamı şu an bu tür hisseler için elverişli" |
| "yay gibi sıkışmış aralık gevşemeye başladı" | "fiyat bir süredir dar bir bantta sıkışmıştı; bu sıkışma şimdi çözülmeye başlıyor — çoğu zaman hareketin habercisidir" (bu metafor iyi, sadeleştirilerek korunabilir) |
| "en dikkat çekeni, kurulum" | (tamamen at — anlamsız dolgu) |

### Before / After — tam kart blurb'leri

**ATAI**
- ❌ Şu an: *"Dikkate değer bir kurulum: ATAI: en dikkat çekeni, kurulum, teyit merdiveninin ileri aşamasında; ayrıca makro rejim arka planı olumlu. Bu bir izleme adayıdır; karar ve risk yönetimi okuyucuya aittir."*
- ✅ Öneri: *"ATAI bugün öne çıktı çünkü aldığı teknik göstergelerin çoğu aynı anda olumlu — tablo kendi içinde tutarlı. Ayrıca genel piyasa havası şu an bu tür hisseler için elverişli, yani hisse akıntıya karşı değil. Bu bir izleme adayıdır, alım-satım önerisi değil; kararı ve riski sen belirlersin."*

**CRNX**
- ❌ Şu an: *"CRNX: en dikkat çekeni, yakın dönem momentum okuması olumlu; ayrıca yay gibi sıkışmış aralık gevşemeye başladı; erken-yakalama merdiveninde üst basamakta; rejim okuması setup ile aynı yönde."*
- ✅ Öneri: *"CRNX'in son günlerdeki yükseliş ivmesi güçlü. Fiyat bir süredir dar bir bantta sıkışmıştı ve bu sıkışma şimdi çözülmeye başlıyor — genellikle hareketin habercisi olan bir durum. Sistem bunu hareket tam olgunlaşmadan erkenden yakaladı ve genel piyasa yönü de aynı tarafta. Yine de bu bir izleme adayı; karar senin, öneri değil."*

**MRNA**
- ❌ Şu an: *"MRNA: en dikkat çekeni, kurulum, teyit merdiveninin ileri aşamasında; ayrıca geniş piyasa koşulları rüzgarı arkadan veriyor."*
- ✅ Öneri: *"MRNA'da birden fazla gösterge aynı anda olumlu yönde — bu, sinyalin tek bir veriye değil, birbiriyle uyumlu birkaç işarete dayandığı anlamına geliyor. Genel piyasa yönü de rüzgarı arkadan veriyor. İzleme amaçlıdır; alım-satım önerisi değildir."*

### Kart metni şablonu (3 parçalı nedensellik)
1. **Ne gördük** (sade): "hacmi normalinin üstünde / momentumu güçlü / dar banttan çıkıyor..."
2. **Neden önemli** (neden-sonuç): "...çünkü bu, ilginin gerçek olduğunu / hareketin başladığını gösterir."
3. **Dürüst kayıt** (her zaman): "İzleme adayıdır, öneri değil; karar ve risk sana aittir. Geçmiş oranlar backtest'tir, canlı garanti değil."

Bu şablon `rationale.py` v3'ün zaten yaptığı şey — **eksik olan, gösterilen sayfanın bunu kullanması** (bayat v2 yerine) ve **Newsroom bölümünün de aynı dile geçmesi.**

---

## 4. ÖNCELİKLİ AKSİYON LİSTESİ

**P0 (uyum + tutarlılık — hemen):**
1. `TheWire.tsx` / `EditorialBoard.tsx` / `FactCheckingDesk.tsx` → BUY/SELL/HOLD/Consensus/Target/Stop-Loss dilini **Grade + okuma + araştırma-bandı** diline çevir. (Sayısal seviyeleri public'ten kaldır.)
2. `demo/page.tsx:87` → `prob_band` boşsa cümleyi gizle ("— of the time" asla görünmesin).
3. Gösterilen edition'ı **v3 ile yeniden üret** (bayat jargon gitsin).

**P1 (dürüstlük + netlik):**
4. 160 vs 1.800 çelişkisini tek gerçeğe indir; stat etiketlerini netleştir.
5. Dil stratejisi: locale başına tam TR/EN (karıştırma yok).
6. "12 DRL / 3 agent / %68" iddialarını somutlaştır veya yumuşat; backtest uyarısını görünür yap.

**P2 (parlatma):**
7. Concept chip'lerine ("early tier", "regime", "contraction") sade tooltip.
8. "Why this grade?" panelini 3-parçalı şablona bağla.

---

## 5. TEK CÜMLE

Motor (rationale v3) doğru yönde ve kartlar dürüst; asıl iki iş: (a) **"Newsroom" bölümündeki AL/SAT/hedef/stop dilini** sayfanın geri kalanıyla aynı "not + sade neden + öneri değil" diline çekmek (uyum açısından kritik), ve (b) **gösterilen içeriği bayat v2 yerine sade v3 metinle** yenileyip eksik sayı/çelişen istatistik gibi ufak hataları temizlemek. Yukarıda her biri için hazır metin var — istersen doğrudan uygularım.
