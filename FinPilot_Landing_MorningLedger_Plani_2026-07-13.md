# LANDING → "THE MORNING LEDGER" DÖNÜŞÜM PLANI
## Claude Design çıktısının uçtan uca çalışan, her gün kendini güncelleyen landing'e dönüşümü

**Tarih:** 2026-07-13 · **Kapsam istisnası kaydı:** İş Planı'nın tasarım-dondurma kuralına sınırlı istisna — yalnız PUBLIC yüzey (landing + /demo). Dashboard "Reader's Desk" V2'si DONUK kalır (lansman sonrası sözü geçerli).
**Zaman kutusu:** 3 iş günü kod + 1 onay seansı. **Dokunulmaz:** sabah prova ritüeli (07:00-09:00 arası bu işe hiç bakılmaz; brif zinciri her şeyden önce gelir).

---

## 0. NEDEN GÜVENLE YAPABİLİYORUZ

Bu bir "sıfırdan tasarım" değil — Claude Design çıktısı bizim Master Şablon'dan üretildi; S1-S8 bölüm yapısı, token'lar ve bileşen sözlüğü zaten dokümante. Veri tarafı da hazır: sayfanın "canlı" kısmı (Yesterday's Edition + karne şeridi) **bugün üretimde olan** `demo_snapshot.json`'dan beslenecek — yani tasarım değişiyor, boru hattı aynı kalıyor.

**Meriç'ten tek ön hazırlık (5 dk):** Claude Design'daki dosyayı indir (`FinPilot Morning Ledger.dc.html`) ve `C:\Users\meric\Borsa\design_ref\` klasörüne koy. Birebir renk/spacing/font değerlerini oradan çıkaracağım — "aşağı yukarı benzer" değil, beğendiğinin aynısı olsun.

## 1. HEDEF MİMARİ (Next.js içinde)

```
web/src/
├── app/
│   ├── page.tsx                → YENİDEN: Ledger landing (S1-S8)
│   ├── demo/page.tsx           → RESTYLE: "Yesterday's Edition" tam sayfası (aynı deri)
│   └── globals.css             → +Ledger token'ları (ink, gold, sage, brick, amber-live)
├── components/ledger/          → YENİ, izole bileşen seti (mevcut bileşenlere dokunmaz)
│   ├── Masthead.tsx            (serif başlık + dateline + çift çizgi)
│   ├── GradeSeal.tsx           (mühür: gold A / steel B / gray C)
│   ├── EditionArticle.tsx      (dünün brifi, editoryal dizgi + drop-cap)
│   ├── MarginNote.tsx          (TermCard'ın gazete-dipnotu evrimi; içerik terms.ts'ten)
│   ├── LedgerStrip.tsx         (karne tablosu + sage/brick heat-strip)
│   ├── HowItsMade.tsx          (4 sütunlu Scan→Grade→Verify→Teach)
│   ├── ClassroomPreview.tsx    (3 ders kartı + kalibrasyon vaadi — statik v1)
│   ├── FullEditionTeaser.tsx   (S7; Stripe env boşken "opens after scorecard")
│   └── Colophon.tsx            (waitlist + disclaimer kolofonu)
└── fonts: next/font/google → Fraunces (serif) + Inter (mevcut) + JetBrains Mono
```

Eski landing bileşenleri (HeroGrid vb.) silinmez; `page.tsx` yenisine döner, eskiler ölü kod olarak kalır ve lansman sonrası temizlenir (geri dönüş sigortası).

## 2. "HER GÜN KENDİNİ GÜNCELLEYEN" FORMAT — veri sözleşmesi + otomasyon

### 2a. Snapshot v1.1 (geriye uyumlu, +3 alan)
`snapshot_builder`'a eklenecek alanlar (landing'in editoryal ihtiyaçları):
- `concept: {name, line}` — günün kavramı (Daily Double önizlemesi + brif zaten üretiyor)
- `edition_no: int` — "Edition No. 4" künye satırı (broadcast_queue'daki sent sayısından türetilir)
- `context_line: str` — rejim/VIX satırı (market_context zaten üretiyor; snapshot'a da yazılır)
Web tipi güncellenir; eski alanlar aynen kalır → mevcut demo kırılmaz.

### 2b. Günlük güncelleme otomasyonu (kritik tasarım kararı)
Bugünkü boşluk: `demo_snapshot.json` lokalde her yayında güncelleniyor ama Vercel'e ancak git push'la gidiyor. Çözüm — **iki aşamalı, bugün 1. aşama:**

**Aşama 1 (bu planla gelir — VPS'siz çalışır):** `scripts/publish_web.py` — yalnız `web/public/demo_snapshot.json`'ı `git add/commit/push` eder (main'e, tek dosya, mesaj: "chore: daily edition YYYY-MM-DD"). `job_publish` başarılı yayından sonra bunu `FINPILOT_WEB_PUBLISH_CMD` üzerinden çağırır → Vercel ~60 sn'de yeni sayıyı basar. Korumalar: sadece o dosya staged'se push; değişiklik yoksa sessiz çık; push hatasında admin DM ("web sayısı güncellenemedi — site dünkü sayıda kaldı, tarih damgası bunu dürüstçe gösterir").

**Aşama 2 (H2, VPS ile):** landing snapshot'ı `api.finpilot.at/public/snapshot`'tan fetch eder → rebuild'siz anlık güncelleme; publish_web devre dışı kalır. Kod bugünden buna hazır yazılır (fetch URL'i env'den: `NEXT_PUBLIC_SNAPSHOT_URL || "/demo_snapshot.json"`).

## 3. SAYFA PLANI — S1-S8 (master şablona sadık, canlı verili)

| Bölüm | İçerik | Veri kaynağı |
|---|---|---|
| S1 Masthead+Hero | "FINPILOT" serif künye, dateline (bugünün tarihi + "Markets open in Xh" sayacı), başlık "1,800 stocks read before your coffee.", 2 CTA | statik + `Date()` |
| S2 Yesterday's Edition | Dünün brifi makale dizgisiyle: drop-cap lede (context_line), 3 aday GradeSeal + MarginNote'lu | snapshot v1.1 |
| S3 Daily Double | Ders kartı ↔ vaka kartı + çizilen köprü | snapshot.concept + candidates[0] |
| S4 Ledger Strip | Grade tablosu + heat-strip + "worst week" pull-quote (v1: karne varsa göster, yoksa dürüst boş-durum) | snapshot.karne |
| S5 How It's Made | 4 sütun + config-sha "print run" rozeti | statik + snapshot.config_sha |
| S6 Classroom Preview | 3 statik ders kartı + kalibrasyon vaadi | terms.ts |
| S7 Full Edition | Gazete-aboneliği çerçevesi; Stripe env boş → "founding run opens after the 4-week scorecard" | env |
| S8 Colophon | Waitlist formu (mevcut uç), Telegram, metodoloji linki, disclaimer | mevcut API |

/demo: aynı derinin tam-sayfa sürümü (S2'nin genişletilmişi + feedback formu korunur). Mevcut Grade/karne/feedback mantığı aynen taşınır — sadece giydirme değişir.

## 4. İŞ SIRASI (3 gün — her gün 09:00 sonrası, prova kutsal)

**G1 (Salı):** design_ref'ten token çıkarımı → globals.css + fontlar → Masthead, GradeSeal, EditionArticle, MarginNote → S1+S2 çalışır halde (gerçek snapshot'la, lokal).
**G2 (Çarşamba):** S3-S8 + LedgerStrip + Colophon → /demo restyle → snapshot v1.1 (builder+tip) → mobil geçiş (bottom-sheet MarginNote, tek kolon).
**G3 (Perşembe):** publish_web.py + job_publish bağlantısı → `npm run build` + yasak-kelime taraması → **senin görsel onay seansın** (Claude Design referansıyla yan yana; "şurası farklı" dediklerin aynı gün düzelir) → commit+push → canlı.
**Kapı:** Perşembe akşamı zaten Hafta-1 kapısı — ikisi aynı seansta: prova 3/3 + yeni landing canlı.

## 5. KABUL KRİTERLERİ
- [ ] Görsel: Claude Design referansıyla yan yana ≥%95 sadakat (senin onayın ölçüt)
- [ ] Canlı veri: S2/S3/S4 gerçek snapshot'tan; tarih damgası doğru; snapshot yoksa/eskiyse dürüst durum metinleri
- [ ] Günlük döngü: yayın → publish_web → Vercel'de yeni sayı ≤5 dk (1 kez uçtan uca test)
- [ ] Mobil: 3 cihaz, margin-note bottom-sheet çalışıyor (DoD #3'ü de kapatır)
- [ ] Compliance: yasak-kelime taraması temiz; disclaimer kolofonu her sayfada
- [ ] `npm run build` sıfır hata; eski sayfalar bozulmadı (dashboard smoke)

## 6. RİSKLER / KURALLAR
- **Kapsam sızması:** Dashboard'a, Classroom tam sürümüne, yeni backend uca DOKUNULMAZ. "Şunu da ekleyelim" → PARKING_LOT.
- **Prova çakışması:** 07:00-09:00 kod yok, push yok. G kunlerinde build kırmızıysa push edilmez — canlı site asla yarım kalmaz (Vercel zaten atomik: build geçmeyen deploy yayınlanmaz).
- **Font/perf:** Fraunces + Inter next/font ile self-host (CLS yok); heat-strip saf CSS (JS grafik kütüphanesi eklenmez).
- **Git hijyeni:** günlük snapshot commit'leri main'i kirletir görünebilir — mesaj standardı ("chore: daily edition") + H2'de Aşama-2'ye geçince tamamen kalkar.

---
**Onayınla:** Sen `design_ref\FinPilot Morning Ledger.dc.html` dosyasını koyar koymaz G1'e başlarım. Bu plan LAUNCH_CHECKLIST'e "H1.5 — Landing Ledger dönüşümü" olarak işlenecek.
