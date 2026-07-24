# BÖLÜM 4 RAPORU — Web ve Dil Bütünlüğü
**Tarih:** 2026-07-24 · **Plan:** UcaUca_Uygulama_Plani Bölüm 4 · **Durum: KAPI ONAYI BEKLİYOR**
**Yöntem:** Önce salt-okunur audit (istenen sıra), sonra uygulama, sonra tip/test doğrulaması.

## AUDIT BULGULARI (uygulamadan önce)

**Zaten çözülmüş çıkanlar (eski plan maddeleri güncel değildi):**
- `_cap` "İts" hatası → kodda `_cap(s, lang)` dil-duyarlı hali mevcut; bugünkü EN rationale doğru ("RIOT makes today's list…"). Kapalı.
- `prob_band:"—"` web kırılması → `/demo` sayfasında fallback zaten var (`c.prob_band !== "—"` kontrolü). Kapalı.
- FactCheckingDesk → compliance temiz: Grade dili, "not an instruction to trade" dipnotu; al/sat kalıntısı yok. Kapalı.
- Masthead %68 → kodda yok; mevcut kod "karne doluysa canlı oran, değilse '—'" idi. (Karar B yine de uygulandı — aşağıda.)
- DE "içeriksiz" notu → GÜNCEL DEĞİL: snapshot her adayda tr/en/de rationale taşıyor, translations.ts DE bloğu dolu. **Yeni karar: DE kalır** (decision-log'a işlendi).

**Gerçek kopukluk (audit'in ana bulgusu):**
Snapshot her adayda `rationale_i18n{tr,en,de}` taşıyor ama web'de bu alan HİÇBİR yerde okunmuyordu — EditionArticle ve DailyDouble düz TR `rationale` basıyordu. Yani dil anahtarı UI metinlerini çeviriyor, ürünün kalbi olan aday gerekçeleri hep Türkçe kalıyordu. EN sorunu "ayrı EN snapshot'ı tüket" değil, "eldeki alanı kullan"mış — yarım gün yerine yarım saatlik iş.

**Ölü kod:** `Hero.tsx` + `HeroGrid.tsx` (BUY/SELL/Entry mock'lu) hiçbir dosyada import edilmiyor. `dashboard/backtest/page.tsx:37` API yokken RASTGELE üretilmiş winRate gösteriyor (demo fallback — dashboard giriş korumalı, lansman yüzeyi değil).

## YAPILANLAR

1. **Aday metinleri dil anahtarına bağlandı:** `ledgerSnapshot.ts`'e `candidateRationale(c, lang)` yardımcısı + `rationale_i18n/risk_note_i18n/tracked_total` tip alanları; `EditionArticle` ve `DailyDouble` artık aktif dile göre tr/en/de gerekçe basıyor (fallback: düz rationale).
2. **Karar B uygulandı:** `karne.py` artık `tracked_total` (signals_archive sayısı — canlı: 5.719) taşıyor; Masthead'in oran istatistiği yerine "Picks publicly tracked: 5,700+" süreç istatistiği geldi (yüzlüğe yuvarlanır, üç dilde çeviri eklendi). Oranlar yalnız LedgerStrip'te, pencere etiketiyle.
3. **translations.ts bayat yorum bloğu** kod gerçeğine eşitlendi (ReAudit 2.2'nin işaretlediği kayıt çelişkisi kapandı).
4. **Karar C kaydı:** decision-log'a işlendi (boş tablolar emekli). Merkezi `docs/governance/decision-log.md` kuruldu — bugünün 6 kararı formatta kayıtlı. (Not: docs/INDEX.md eski bir README kopyası çıktı — gerçek indeks Bölüm 5 işi.)

**Doğrulama:** `npx tsc --noEmit` TEMİZ · Python testleri 20 passed (tracked_total regresyonsuz) · karne canlı çıktısı: `tracked_total: 5719, B{n:36}, C{n:23}`.

## KAPI İÇİN SENİN ADIMLARIN

1. **Yerel görsel test:** `cd web; npm run dev` → ana sayfada dil değiştirici ile TR/EN/DE geçişinde aday gerekçelerinin DEĞİŞTİĞİNİ gör; Masthead'de "—" yerine yarın sabah yayından sonra "5,700+ Picks publicly tracked" gelecek (karne snapshot'a girince).
2. **Ölü kod temizliği (onaylıyorsan):**
   ```powershell
   git rm web/src/components/Hero.tsx web/src/components/HeroGrid.tsx
   ```
   (İçlerinde yasak dil mock'u var; kullanılmıyorlar. Silmek istemezsen dokunma, karar senin — ama repo'da yasak-dil örneği taşımaya devam ederler.)
3. **Commit+push** (Bölüm 1+3 commit'ini yaptıysan üstüne, yapmadıysan hepsi birlikte):
   ```powershell
   git add distribution/karne.py web/src docs/governance docs/reports
   git commit -m "Bolum 4: aday metinleri dil anahtarina baglandi, Masthead surec istatistigi (Karar B), karar logu"
   git push
   ```
4. **Vercel deploy + canlı kontrol:** deploy sonrası finpilot.at'ta üç dilde geçiş + mobil 3-cihaz testi (DoD#3 açık ucu).

## Kapı kriteri
Kod+tip doğrulaması ✓ · yerel görsel test ⏳ · ölü kod kararı ⏳ · commit+deploy ⏳ · mobil test ⏳.
**Sonraki:** yarın sabah tek ritüel → Bölüm 1+3 kapıları kapanır + Bölüm 2 işlenir (expired alarm + süre logu + seri sayacı) → ardından Bölüm 5 (doküman/sözlük; INDEX.md gerçek indekse dönüşür).
