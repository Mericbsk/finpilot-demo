# Web Yüzü — Envanter ve Yol Haritası

Sürüm: 1.0 · Durum: DRAFT (analiz — Level A) · Tarih: 2026-07-29
Amaç: Kamuya açık web yüzeyinin gerçek durumunu (gerçek veri / mockup / statik / orphan / kopuk)
tek tabloda görmek ve üç hedefi — **kredibilite, FinSense'i kamuya açma, kazanım funnel'ı** — bunun
üstünde sıralamak.

---

## 1. Envanter — kamuya açık rotalar

| Rota | Ne | Veri kaynağı | Durum |
|---|---|---|---|
| `/` (landing) | Ana **Ledger** (finansal gazete) | `getLedgerSnapshot()` — server-side, Render `/api/v1/distribution/snapshot`'ı dener, **o endpoint YOK** → statik dosyaya düşer | ⚠ Kısmen mockup (aşağı bak) |
| `/demo` | Ledger detay (adaylar + scorecard) | Client `fetch("/demo_snapshot.json")` — **statik dosya** (bilinen bayatlık sorunu, 17 Tem) | ✅ Gerçek ama farklı yol |
| `/methodology` | Kamuya açık metodoloji iddiası | Statik metin (Level B, "past performance" uyarısı zorunlu) | ✅ Compliance-hassas |
| `/premium` | Fiyat/abonelik | Stripe env link'leri | ✅ ama funnel zayıf |
| `/academy` | Finance Academy | `fetch("/academy_lessons.json")` | ✅ |
| `/dashboard/finsense` | FinSense sözlük/terim | Dashboard içi | ⛔ **Public değil** (giriş gerekiyor) |

## 2. Landing Ledger bileşenleri (kredibilite mercek)

| Bileşen | Veri | Durum |
|---|---|---|
| Masthead, EditionArticle, DailyDouble, LedgerStrip, ClassroomPreview | snapshot (props) | ✅ Gerçek |
| **Newsroom** | snapshot props ama içerik | ⚠ **"illustrative data, not live"** — landing'de CANLI yayında |
| HowItsMade, EditorialStance, FullEditionTeaser, Colophon | statik | ✅ (tasarım/anlatı) |

**Orphan bileşenler** (yazılmış ama hiçbir sayfada render edilmiyor): `TheWire` (⚠ mockup),
`FactCheckingDesk`, `EditorialBoard` (⚠ mockup), `GradeSeal`, `MarginNote`. → ölü kod ya da yarım kalmış.

## 3. Üç hedef ekseninde tespitler

### A. Kredibilite
1. **Mockup, gerçek sayfada canlı:** `Newsroom` landing'de "illustrative" veriyle yayında. Gerçek
   tarama verisiyle sahte veri yan yana → en çok güveni bu bozar.
2. **İki farklı veri yolu:** landing `getLedgerSnapshot` (server → Render endpoint), `/demo` client
   `fetch(/demo_snapshot.json)` (statik). Aynı snapshot, iki yol → içerik ayrışabilir. (Dağıtım-zinciri
   planındaki `/api/v1/distribution/snapshot` endpoint'i bunu tek yola indirir.)
3. **Orphan/yarım bileşenler** repo'da duruyor — ya bitir ya kaldır.

### B. FinSense'i kamuya açma
4. FinSense yalnız `/dashboard/finsense` altında — giriş gerektiriyor. Oysa konumlandırma (impact
   engine / AWS Deep Tech) tam da bunun **public** olmasını istiyor. Şu an dağıtım kanalı değil, kapalı sözlük.

### C. Kazanım funnel'ı
5. **Cross-link zayıf:** `/premium` yalnız `/`'a geri link veriyor; landing→premium veya demo→premium
   net bir yol yok. `/methodology → /demo` var (iyi). Ziyaretçi demo'yu görüp premium'a nasıl geçecek belirsiz.
6. **Tek CTA teması dağınık:** Telegram brief (demo), waitlist (`/#waitlist`), Stripe (premium) — üç ayrı
   çağrı, tek funnel değil.

## 4. Yol haritası (hepsi — sıralı)

### Faz 1 — Kredibilite (en ucuz yüksek-etki) · Level A/B
- `Newsroom`'u ya gerçek `snapshot`'a bağla ya landing'den geçici kaldır (mockup canlıda kalmasın).
- Landing ve `/demo`'yu **tek veri yoluna** indir: dağıtım planındaki `/api/v1/distribution/snapshot`
  endpoint'i canlı olunca ikisi de oradan okusun (statik dosya fallback).
- Orphan bileşenleri (TheWire, FactCheckingDesk, EditorialBoard, GradeSeal, MarginNote) karara bağla:
  bitir veya sil (repo sağlığı).

### Faz 2 — FinSense public · Level B
- Giriş-gerektirmeyen public `/finsense` (veya landing'e gömülü terim-keşif): SEO + impact + içerik dağıtımı.
- Mevcut dashboard FinSense'inden public-güvenli bir sürüm türet (yasak dil filtresi, salt-okunur).
- Ledger'daki `BadgeWithTerm` / terim linklerini bu public FinSense'e bağla (içerik ağı).

### Faz 3 — Funnel / touchpoints · Level A/B
- Tek birincil CTA belirle (öneri: Telegram brief) ve her public sayfada tutarlı yerleştir.
- Net yol kur: landing → demo (kanıt) → premium (dönüşüm); `/premium`'a demo ve landing'den görünür CTA.
- Bir "touchpoint haritası" çiz: her sayfanın giren/çıkan linkleri; kopuk geçişleri kapat.

## 5. Nereden başla (bugün)
En mantıklı ilk hamle **Faz 1**: `Newsroom` mockup'ını kaldır/bağla + tek veri yolu. Bu, "gerçek veri
diyen sayfada sahte bölüm" çelişkisini bitirir ve diğer iki hedefin (FinSense, funnel) üstüne kurulacağı
güvenilir zemini kurar. İstersen Faz 1'i somut değişiklik önerileriyle (diff) açayım.

---

**Not (governance):** Public yüzey değişiklikleri YONERGE §12 (yasak dil: al/sat/hedef) ve `/methodology`
"past performance" kuralına tabi; üretim-kritik yüzey değişikliği Level B (Meriç onayı). Bu belge Level A analiz.
