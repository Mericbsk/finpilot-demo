# 🚀 LAUNCH CHECKLIST — DURUM PANOSU (neredeyiz)
_ROL: yalnız durum; kural koymaz (otorite haritası: docs/INDEX.md) · Kaynak plan: FinPilot_Kullaniciya_Cikis_Is_Plani_2026-07-05.md · Her Pazartesi birlikte güncellenir._
_Gerçekleme 2026-07-24 (Bölüm 5): retroaktif Hafta-1 kapı notu aşağıda; seri sayacı publish_now çıktısına bağlanacak (Bölüm 2)._

## Lansman Tanımı (10/10 şart)
- [ ] 1. 10 ardışık işlem günü kesintisiz brif yayını — SAYAÇ SIFIRLANDI 23 Tem (20-22 Tem "expired"); mevcut seri: 2 gün (23-24 Tem)
- [ ] 2. Sabah operasyonu ≤15 dk/gün — ölçüm Bölüm 2 süre loguyla başlıyor
- [~] 3. finpilot.at yeni landing + demo CANLI ✓ (13 Tem) · mobil 3-cihaz testi bekliyor
- [~] 4. Demo her gün otomatik taze snapshot — köprü ONARILDI 24 Tem (publish_now→web, kanıt: demo_snapshot date=2026-07-24); "her gün" kanıtı seri ile birlikte işlenir
- [~] 5. Karne verisi gerçek ve webde (by_grade dolu) — zincir 24 Tem'de yeniden kuruldu (DB-karne + arşiv köprüsü + resolver koşuldu); ilk dolu yayın bekleniyor (25 Tem sabah)
- [ ] 6. Brif içeriği "insan yazmış" kalitesinde (variety raporu + 3 dış okuyucu)
- [ ] 7. ≥25 kanal takipçisi + ≥10 beta dashboard kullanıcısı
- [ ] 8. ≥15 feedback + 2 Cuma ritüeli
- [ ] 9. Premium mekaniği test modunda uçtan uca kanıtlı
- [ ] 10. Kırmızı-gün prosedürü 1 kez tatbik edildi

## HAFTA 1 — İçerik + Otomasyon temeli
**Meriç:**
- [x] M1 Dosya güvenliği (OneDrive/AV) — TAMAM (2026-07-05)
- [x] M2 Güç kararı: PC her sabah ELLE açılacak (≤08:15) — catch-up mantığı bunu tolere eder
- [x] M3 DNS ✓ (helloly cPanel; www→Vercel CNAME zaten canlı; MAİL KAYITLARINA DOKUNMA; H2'de tek ekleme: api.finpilot.at A kaydı)
- [x] M4 Vercel ✓ — ana repo = github.com/Mericbsk/finpilot-demo (monorepo!); 'web' projesi www'yu tutuyor (prod deploy yok), finpilot-demo apex'i tutuyor · git multi-pack-index ONARILDI (push artık mümkün) · GitHub 23 Haz'da — H2 öncesi commit+push gerekli
- [ ] M5 VPS hesabı (Hetzner önerisi) + SSH key
- [x] M6 Kanallar kuruldu ✓ — ID keşfi: `python scripts/tg_discover.py` (bot runner kapalıyken)
- [x] M7 .env ✓ — GÜNCELLENDİ 24 Tem: DISTRIBUTION=**0** (manuel yayın kararı uygulandı; cron uyur, yayın publish_now ile) + KARNE_WINDOW_DAYS=30 · @Finpilot_Breif · eksik: PREMIUM_CHANNEL_ID (4. haftaya kadar gerekmez)

**Claude (kod):**
- [x] E0 Startup catch-up mantığı (elle-açma kararının gereği)
- [x] E1 Gerekçe motoru v2 (varyant havuzu, deterministik, bağlam kuralları)
- [x] E2 Market bağlam satırı
- [x] E3 Risk notu havuzu (10 kalıp)
- [x] E4 30 terimlik tek-kaynak sözlük + terms.ts üretici
- [x] E5 Sabah tarama job'u (07:15) + 07:40 bekçi + catch-up scan entegresi
- [x] E6 Yedek + bütünlük job'u (+ ilk restore provası)
- [x] E7 Arşiv süreklilik alarmı (22:00)
- [x] E8 Çeşitlilik test script'i + rapor

**Hafta 1 Kapısı (Pzt akşamı):**
- [ ] 3 işlem günü otomatik taslak + DM (müdahale=0)
- [ ] Variety raporu temiz + Meriç içerik onayı (30 örnek)
- [ ] Bekçi/alarm 1 kez test edildi
- [ ] Yedek + restore provası
- [ ] M3-M7 tamam

## HAFTA 2 — Canlıya taşıma _(kapı geçilince açılır)_
_Öne çekilenler (13 Tem): web deploy ✓ · domain birleştirme ✓ · main dalı güncel ✓_
_Kalanlar: M5+VPS kurulumu, api.finpilot.at A kaydı, public-API profili, Plausible+Sentry, metodoloji sayfası_
## HAFTA 3 — Prova · HAFTA 4 — Sertleştirme · HAFTA 5 — Yarı-açık · HAFTA 6 — Stabilizasyon
