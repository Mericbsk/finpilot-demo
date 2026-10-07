# 🧭 DURUM — neredeyim, sırada ne var (tek harita)

_Kural: bu dosya kafamın dışındaki tek "neredeyim" haritasıdır. Her sabah nabız buraya bakar; her Pazartesi elle güncellenir. Tam bileşen envanteri: `docs/2026-08-02-ENVANTER-tum-bilesenler.md`._

---

## ⭐ Ürün hattı önceliği: LANSMAN
Kaynak: `LAUNCH_CHECKLIST.md` · Kritik metrik: **10 ardışık işlem günü brif** →
**seri kırık** — son `sent` brif 2026-09-09 (`distribution.db`, 23 Eyl kontrolü). Seri 0'dan yeniden başlar.
"Bunu yapmak lansmanı bugün ilerletiyor mu?" sorusu **ürün hattındaki** işleri sıralar.

### Bu haftanın tek işi (ürün hattı — her Pazartesi doldur)
> **Brif zincirini yeniden çalışır hâle getir:** tam tarama → tam export → `job_draft` → yayın.
> - Bilinen: son brif 09-09. Gözlem: 09-10'dan beri yalnız `_partial_` export var; `job_draft` eksik export'tan brif üretmez.
> - Aday darboğaz: `prefetch.repair` (22 Eyl ölçümü, süre payı ~%82–87) — **neden olduğu doğrulanmadı.**
> - Bu bir operasyon/mühendislik işidir (Level A/B); araştırma preregistration'ı gerektirmez.
> - Sonra: seriyi 0→10 · karne dolu yayın · mobil 3-cihaz landing testi (Impressum/Datenschutz Level C hukuk kapısı).
>
> Ürün vaadi edge kanıtı değil; dürüst karneli, öğreten sabah bültenidir. Edge kanıtlanmış gibi ima edilmez.

> Edge ölçümü arka planda pasif olarak birikmeye devam eder. Evren büyütme,
> donanım ve ağır web yatırımı edge kanıtına kadar parktadır.

## 🔬 Paralel hat: Araştırma / Yönetişim — lansmanın ön koşulu değil
- **B4** provenance persistence spesifikasyonu (partial scan/export dahil; uygulama ayrı yetki ister)
- **B2-AUTH** yayın kapısı yetki incelemesi (Level C; CONVICTION_TIERS, ALPHA_V2; veri gerektirmez)
- **B2-1** eksik tarihsel girdi provenance'ı (DRAFT v2, kilitli değil) · B2-2 koşullu · B2-full açılmadı

**Kural:** Araştırma ürünü yalnızca şu üç durumda bloklar: ürün davranışı açıkça o sonuca bağlıysa, production
davranışı değişecekse veya bir Level C kararı bunu açıkça gerektiriyorsa. Araştırma sonucu production'ı kendiliğinden
değiştirmez. Tam metin: decision-log, 2026-09-23.

## 💶 Paralel hat: Finansman / Fonlama
- **Durum:** aktif
- Pitch deck / bütçe / başvuru dokümanları: hazırlanmış, gerektiğinde güncellenecek
- Hedef: uygun hibe, destek ve finansman fırsatlarına başvuru
- Bu hat ürün hattının öncelik sırasını değiştirmez; ayrı planlanır.
- Ayrıntılı başvuru takvimi ve program bazlı durum bu dosyada tutulmaz.

---

## ✅ Aktif (yalnız lansman-kritik — LAUNCH_CHECKLIST'ten)
- Brif zincirini onar → seriyi 0'dan başlat (hedef 10)
- Demo her gün taze snapshot (köprü onarıldı; "her gün" kanıtı seriyle)
- Karne dolu yayın (ilk dolu yayın bekleniyor)
- Mobil 3-cihaz landing testi
- İçerik "insan yazmış" kalitesi (variety raporu + 3 dış okuyucu)
- ≥25 kanal takipçisi + ≥10 beta kullanıcı · ≥15 feedback

## 🅿️ Park (lansman-sonrası — PARKING_LOT + bu oturum)
- **FinSense onarımları / içerik fabrikası** (Finsense repo) — süreli park doldu; yeniden önceliklendirme kararı bekliyor — otomatik başlamaz
- **Buzz / Control Center + `/ops` + tasarım promptları** — bu oturumun ürünü, ama PARK (lansman-sonrası v2)
- `.finpilot/` ortak-beyin protokolü — kuruldu; kullanımı hafif tut, geliştirmesi park
- Ledger×Classroom kod uygulaması · ShortlistEnricher · DRL/alt-data araştırma
- Tauri masaüstü · kullanıcıya-özel alert
- Kökteki ~90 deney scripti — lansman sonrası arşivle

## 🚧 Bilinen takıntı/temizlik (lansman sonrası)
- Kök dağınıklığı: ~90 script + ~110 doküman → arşiv/park
- `execution/` + `broker/` (Level C, para-bitişik) — dokunma, insanda

---
_Not: yol planının tamamı (tüm sistemi düzenleme) lansmandan SONRA. Ürün hattında tek yol lansman; araştırma hattı yukarıdaki kuralla paralel yürür._
