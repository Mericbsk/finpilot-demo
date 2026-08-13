# FinPilot Web — Kapsamlı İnceleme ve Rapor
### Yalnız web katmanı (Next.js) · 2026-08-06 · kanıt: dosya:satır

**Kapsam:** Sadece `web/`. Başka alana geçilmedi. Kod satır düzeyinde okundu.
**Genel web puanı: 5.5/10** — mühendislik gerçekten iyi (7-8), ama **compliance-metadata çelişkisi** ve **neredeyse sıfır test** puanı düşürüyor. Manşet bulgu: şirketin tüm kimliğini dayadığı "dürüst, tavsiye değil" ilkesi, en görünür yüzeyde (SEO metadata) çiğneniyor + uydurma bir puan var.

---

## 0. Stack ve yapı
Next.js 16.1.6 · React 19.2.3 · Tailwind 4 · TypeScript 5 · framer-motion · lightweight-charts · tanstack-table/virtual · fuse.js · sonner · vitest. `output: standalone` (Docker). Fontlar `next/font` (Source Serif + JetBrains Mono, swap).

Route'lar:
- **Public (lansman-kritik):** `/` (landing, SSR), `/demo` (CSR), `/methodology`, `/premium`, `/academy` — toplam ~1.000 satır, makul.
- **Dashboard (dondurulmuş, lansman-dışı):** 18 sayfa, **16.241 satır** — public'in ~15 katı; auth arkasında.
- **API:** `/api/quotes` (yfinance proxy), `/py-api/[...path]` (FastAPI proxy, prod-sertleştirilmiş).

---

## 1. COMPLIANCE — 3/10  ⚠️ EN KRİTİK BULGU
- **Mevcut (iyi taraf):** Ürün gövdesi kusursuz uyumlu. `demo/page.tsx:7` "Single Grade label (no BUY/SELL, no stop/TP)"; disclaimer'lar `demo:58`, `premium:17,121`, `methodology:69`, `components/ledger/TheWire.tsx:61`, i18n `translations.ts:57`. Grade disiplini bileşenlerde gerçek.
- **ZAYIF / RİSK (lansman-blokör):**
  1. `app/layout.tsx:72` — meta description + OpenGraph + Twitter kartı: **"Clear buy/hold/sell signals"**. Bu, YONERGE §12'nin ("yasak dil hiçbir yüzeye giremez") en görünür ihlali — arama sonuçlarında ve sosyal paylaşımlarda **ilk görünen metin** bu.
  2. `app/layout.tsx:33` keyword'ler: "AI stock picks", "algorithmic trading".
  3. `app/layout.tsx:101-104` — **`aggregateRating: 4.8, ratingCount: 120`**. Bu **UYDURMA** (gerçek kullanıcı ~0). JSON-LD'de sahte puan hem aldatıcı (Google cezası riski) hem de "dürüst karne" kimliğinin tam zıddı.
  4. Dashboard'da yasak dil: `dashboard/scanner:2715` "Hedef Fiyat", `dashboard/page:262` "BUY/SELL", `dashboard/analysis:71` "price target". Dashboard auth arkasında ve dondurulmuş; ama asla public/SEO'ya sızmamalı.
- **Öncelik:** **P0.** Compliance senin tek hendeğin; onu en görünür yerde çiğnemek ölümcül ironi.
- **Öneri:** Metadata dilini Grade/research'e çevir; sahte rating'i **hemen kaldır**; dashboard'ı SEO/robots'tan hariç tut; bir "compliance testi" ekle (aşağıya bak).

## 2. Güvenlik — 7/10
- **Güçlü:** `next.config.ts` olgun güvenlik başlıkları — CSP, HSTS (preload), X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy. Tek kişi projesi için nadir. `.env.local` disiplini doğru: Alpaca anahtarları frontend'de YOK (yorumla belirtilmiş); `NEXT_PUBLIC_API_URL` bilinçli kaldırılmış (same-origin proxy zorlanıyor → CORS/sızıntı yok). Secret client'a düşmüyor.
- **Zayıf:** CSP `connect-src`'te **prod'da dev artıkları** var: `http://localhost:8000/8001 ws://localhost:8001`. CSP `script-src`'te `'unsafe-inline' 'unsafe-eval'` (Next/GTM için yaygın ama XSS yüzeyini açar).
- **Öncelik:** P1. **Öneri:** localhost'ları prod CSP'den çıkar; ileride nonce tabanlı CSP.

## 3. SEO — 5/10
- **Güçlü:** Zengin metadata (title/desc/OG/Twitter/JSON-LD), `robots.ts` + `sitemap.ts` + `manifest.ts` (PWA) mevcut, `metadataBase` finpilot.at.
- **Zayıf:** (a) description'da yasak dil (§1); (b) sahte aggregateRating (§1); (c) `<html lang="en">` sabit ama içerik TR/EN — TR için yanlış hreflang/dil sinyali; OG locale yalnız `en_US`.
- **Öncelik:** P0/P1. **Öneri:** dili düzelt, yasak dili ve sahte puanı kaldır, TR için hreflang.

## 4. Veri akışı — 7/10
- **Landing (SSR):** `lib/ledgerSnapshot.ts` `web/public/demo_snapshot.json`'u **diskten** render anında okur (network yok; distribution/jobs.py yayınlar). Snapshot yoksa dürüst boş-durum, crash yok. Temiz ve sağlam desen.
- **Demo (CSR):** `demo/page.tsx` `"use client"` + useEffect/useState — istemci tarafı. İlk boyama daha yavaş; Skeleton'lar var. SEO görünmez (demo için sorun değil).
- **Öncelik:** P2. **Öneri:** karışık render bilinçli; demo'da yükleme/hata durumlarını sağlam tut.

## 5. Erişilebilirlik — 5/10
- **Zayıf:** `<html lang="en">` sabit (TR içerik için yanlış). `<html className="dark">` global zorlanıyor **ama** Ledger tasarımı açık/gazete paleti (`methodology` `--ledger-ink #1a1a1a` açık zeminde koyu mürekkep). Tema çatışması riski (form kontrolleri, scrollbar, `dark:` varyantları).
- **Öncelik:** P1. **Öneri:** dili dinamikleştir; forced-dark ile açık Ledger temasını uzlaştır.

## 6. Performans — 7/10
- **Güçlü:** SSR landing + `next/font` (self-host, swap) + `standalone` çıktı + statik snapshot okuma. framer-motion/lightweight-charts ağır ama yalnız gerektiği yerde.
- **Öncelik:** P2. Lansman için yeterli; ölçüm (Lighthouse/mobil) checklist'te zaten var.

## 7. Tasarım sistemi & i18n — 7/10
- Morning Ledger bileşen ailesi (`components/ledger/*`: Masthead, EditionArticle, DailyDouble, Newsroom, LedgerStrip, HowItsMade, ClassroomPreview, Colophon) tutarlı ve ayırt edici. TR/EN i18n altyapısı (`lib/i18n`) var. 35 bileşen, temiz ayrışma.

## 8. Test — 2/10  ⚠️
- **Mevcut:** Tüm web'de **tek test dosyası** (`__tests__/dashboard-pages.test.tsx`) + setup. vitest kurulu ama kapsam ~sıfır.
- **Öncelik:** P1. **Öneri:** Public sayfalar için smoke testleri; ve **compliance testi**: render edilen public HTML'de "buy/sell/hold/hedef fiyat/aggregateRating" GEÇMEDİĞİNİ assert et. Bu, §1 ihlalinin tekrarını kalıcı engeller.

## 9. Kapsam disiplini (dashboard) — 4/10
- 18 sayfa / 16.241 satır dashboard, lansman için gereksiz ve bakım yükü; içinde yasak dil. Plan zaten "dondurulmuş" diyor.
- **Öncelik:** P2 (lansman sonrası). **Öneri:** public build'den net ayır, SEO'dan hariç tut, dondur.

---

## Öncelikli aksiyon listesi
**P0 — lansmandan ÖNCE (compliance, dürüstlük):**
1. `layout.tsx` metadata'dan "buy/hold/sell signals" dilini kaldır → Grade/research diline çevir (title, description, OG, Twitter).
2. **Sahte `aggregateRating 4.8/120`'ı sil** (veya yalnız gerçek, dürüst yapılandırılmış veri bırak).
3. Pazarlama iddialarını doğrula veya yumuşat: "12 trained RL models", "1,500+ daily", "Not an LLM wrapper — real AI".

**P1 — lansman haftası:**
4. `<html lang>` düzelt (TR/EN) + TR hreflang.
5. CSP'den localhost dev artıklarını çıkar.
6. Forced-dark ↔ açık Ledger tema çatışmasını çöz.
7. Public smoke + **compliance testi** ekle (yasak dil = build fail).

**P2/P3 — lansman sonrası:**
8. Dashboard'ı public'ten net ayır/dondur; SEO'dan hariç tut.
9. CSP nonce; demo render stratejisi; Lighthouse/mobil ölçüm.

---

## Nihai değerlendirme
Web'in mühendisliği (stack, güvenlik başlıkları, secret disiplini, proxy sertleştirmesi, Ledger tasarımı, veri akışı) tek kişi için **etkileyici** — 7-8 seviyesi. Ama iki şey bunu gölgeliyor: **(1)** compliance'ın en görünür yerde (SEO metadata) çiğnenmesi + sahte rating — ki bu senin tek hendeğin, **(2)** neredeyse sıfır test. İyi haber: ikisi de küçük, hızlı düzeltmeler (metadata + rating birkaç satır; compliance testi bir dosya). Bunlar kapanınca web lansmana **gerçekten hazır** olur.
