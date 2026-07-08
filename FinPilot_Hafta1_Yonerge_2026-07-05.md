# HAFTA 1 YÖNERGESİ — "İçerik + Otomasyon Temeli"
## Uçtan Uca Çalışma Kılavuzu: Kim, Ne, Nasıl, Hangi Sırayla, Nelere Dikkat

**Kapı (haftanın tek başarı ölçüsü):** Lokalde **3 ardışık işlem günü**, elle hiçbir müdahale olmadan, **zengin içerikli** brif taslağı üretildi ve telefonuna DM düştü + hosting hesapları hazır.
**İlke:** Bu hafta hiçbir şey internete çıkmıyor (deploy Hafta 2). Bu hafta makine, evinde kusursuz çalışmayı öğreniyor.

---

## 0. HAFTANIN RESMİ

```
SENİN HATTIN (hesaplar/ortam)            BENİM HATTIM (kod/içerik)
─────────────────────────────            ─────────────────────────
M1 Dosya güvenliği kontrolü ──┐          E1 Gerekçe motoru v2 (varyant havuzu)
M2 Bilgisayar güç ayarları    │          E2 Market bağlam satırı
M3 Domain/DNS erişim kontrolü │          E3 Risk notu havuzu (10 kalıp)
M4 Vercel hazırlığı           ├─ Çrş'ya  E4 30 terimlik tek-kaynak sözlük
M5 VPS hesabı + SSH           │  kadar   E5 Sabah tarama job'u (07:15)
M6 BotFather kanal kurulumu ──┘          E6 Yedek + bütünlük job'u
M7 .env güncellemesi (Çrş)               E7 Arşiv süreklilik alarmı
                                         E8 Çeşitlilik test script'i
        └──────────────┬─────────────────────┘
                       ▼
        PRŞ-CUM-PZT: 3 günlük otomatik prova (sen sadece DM'i izliyorsun)
                       ▼
        PZT akşamı: KAPI DENETİMİ (bölüm 5 checklist)
```

**Gün gün:**
- **Pzt-Sal:** Ben E1-E4 (içerik), sen M1-M3. Akşam 10 dk senkron.
- **Çrş:** Ben E5-E8 (otomasyon), sen M4-M6 + M7 (.env). Akşam: sistemi birlikte kuruyoruz (flag açma + ilk manuel test).
- **Prş-Cum + Pzt:** 3 günlük otomatik prova (Cmt-Paz piyasa kapalı — sayılmaz, sistemin "tatil davranışını" da görmüş oluruz).
- **Pzt akşam:** kapı denetimi → geçtiyse Hafta 2.

---

## 1. SENİN GÖREVLERİN (adım adım)

### M1 — Dosya güvenliği kontrolü ⚠️ EN ÖNEMLİSİ, İLK İŞ (Pzt, ~30 dk)
Geçen hafta 17 dosyayı kesilmiş bulduk. Kök neden büyük olasılıkla senkron/AV katmanı. Kontrol sırası:
1. **OneDrive kontrolü:** `C:\Users\meric\Borsa` OneDrive senkronunda mı? Dosya Gezgini'nde klasöre bak — dosya ikonlarında bulut/tik işareti var mı? OneDrive ayarları → Hesap → "Klasörleri yönet" → Belgeler/Masaüstü senkronu Borsa'yı kapsıyor mu?
   - **Kapsıyorsa:** ya Borsa'yı senkron dışına al (önerilen: OneDrive ayarlarından klasörü hariç tut) ya da repoyu `C:\dev\Borsa` gibi senkronsuz bir yola taşı (taşırsan bana söyle, yol referanslarını güncellerim).
2. **Antivirüs:** Windows Güvenliği → Virüs koruması → Ayarlar → **Dışlamalar** → `C:\Users\meric\Borsa` klasörünü ekle (üçüncü parti AV varsa onda da).
3. **Disk sağlığı:** Yönetici PowerShell → `chkdsk C: /scan` — hata varsa bana bildir.
4. **Kanıt:** Bittiğinde bana "M1 tamam + OneDrive durumu şu" yaz — ben CI'daki syntax-sweep ile 2 hafta izleyeceğim.

### M2 — Bilgisayar güç ayarları (Pzt, 10 dk) ⚠️ kritik pratik detay
Sabah 07:15 job'ının çalışması için PC'nin **uyanık** olması şart (VPS'e taşıyana dek):
- Ayarlar → Sistem → Güç → "Uyku: **Asla**" (fişe takılıyken).
- Gece kapatıyorsan: sabah 07:00'den önce açık olacak şekilde alışkanlık YA DA BIOS'tan "wake on RTC alarm" (varsa) 06:55.
- start.sh/scheduler'ın gece boyu ayakta kaldığını Çrş kurulumunda birlikte doğrulayacağız.

### M3 — Domain/DNS erişim kontrolü (Pzt-Sal, 15 dk)
- finpilot.at hangi registrar'da? Panele girebildiğini doğrula (şifre/2FA çalışıyor mu).
- DNS kayıtlarının ekran görüntüsünü al (mevcut A/CNAME kayıtları — Hafta 2'de Vercel'e yönlendireceğiz, şimdi DOKUNMA).
- Mevcut site nerede host'lu? (Hafta 2 geçiş planı için bilmem gerek.)

### M4 — Vercel hazırlığı (Çrş, 20 dk)
- vercel.com hesabına gir (eski demo projen duruyorsa adına bak, silme).
- Repo GitHub'da mı ve Vercel'in erişimi var mı kontrol et (Vercel → Add New Project → repo listede görünüyor mu — **kurma**, sadece görünürlüğü doğrula).
- Not: deploy Hafta 2; bu hafta sadece "engel var mı" tespiti.

### M5 — VPS hesabı (Çrş, 30 dk)
- **Öneri: Hetzner Cloud** (Falkenstein/Nürnberg, CX22 ~€4/ay — public-API için fazlasıyla yeter). Alternatif: Fly.io (kredi kartı yeter, sunucu yönetimi yok).
- Hesap aç + ödeme yöntemi ekle. Sunucu **kurma** — Hafta 2'de birlikte kuracağız.
- Hetzner seçersen: SSH key oluştur (PowerShell: `ssh-keygen -t ed25519` → Enter×3) ve `C:\Users\meric\.ssh\id_ed25519.pub` içeriğini Hetzner panelde "SSH Keys"e ekle.

### M6 — BotFather kanal kurulumu (Çrş, 30 dk) — adım adım
1. **Public kanal:** Telegram → Yeni Kanal → ad: "FinPilot Daily Brief" → tür: Public → kullanıcı adı önerileri (müsaitlik sırasına göre dene): `finpilot_brief`, `finpilotdaily`, `finpilot_daily`. Açıklamaya şunu yaz: *"1,800+ US stocks scanned every morning. Graded candidates with reasons + an open scorecard. Research & education — not investment advice."*
2. **Botu admin yap:** Kanal → Yönetici Ekle → mevcut botunu ara → yetkiler: **Mesaj gönder** ✓, Mesaj düzenle ✓, diğerleri kapalı olabilir.
3. **Private premium kanal:** Yeni Kanal → "FinPilot Full Edition" → Private → botu yine admin ekle (aynı + **Üye engelleme** ✓ ve **Davet linki oluşturma** ✓ yetkileriyle — otomasyonun çıkarma/davet işleri için şart).
4. **ID'leri topla:**
   - Kendi ID'n: Telegram'da `@userinfobot`a "hi" yaz → verdiği sayı = `TELEGRAM_ADMIN_ID`.
   - Kanal ID'leri: public kanal için `@finpilot_brief` yazımı yeterli (handle kullanacağız). Private kanal için: kanala bir mesaj at → o mesajı botuna forward et → bana söyle, Çrş kurulumunda ID'yi birlikte çekeriz (tek komutluk iş).
5. **Güvenlik:** bot token'ını hiçbir yere yazma/gönderme — zaten .env'de. Kanal linklerini şimdilik kimseyle paylaşma (prova bitene dek).

### M7 — .env güncellemesi (Çrş akşamı, birlikte, 10 dk)
Şu blok eklenecek (değerleri o akşam birlikte doldururuz):
```
FINPILOT_ENABLE_DISTRIBUTION=1
TELEGRAM_CHANNEL_ID=@finpilot_brief        # ya da seçilen handle
TELEGRAM_PREMIUM_CHANNEL_ID=               # Çrş akşamı birlikte
TELEGRAM_CHANNEL_LINK=https://t.me/finpilot_brief
TELEGRAM_ADMIN_ID=                         # @userinfobot'tan aldığın sayı
FINPILOT_SITE_URL=https://www.finpilot.at
```
Ardından `.env`'in bir kopyasını güvenli bir yere (şifre yöneticisi/USB) yedekle — bu dosya git'te YOK, kaybolursa tüm anahtarlar gider.

---

## 2. BENİM GÖREVLERİM (mühendislik spec'i — onayında bu sırayla kodlarım)

### E1 — Gerekçe motoru v2 (`distribution/rationale.py`) · Pzt-Sal
- **Varyant havuzu:** 9 rozet × 5 varyant × 2 dil (TR Telegram / EN web) — fragment'lar anlamca eş, üslupça farklı ("short oranı yüksek" / "açığa satış birikmiş" / "short tarafı kalabalık"...).
- **Deterministik seçim:** `seed = sha1(date+ticker)` → aynı gün aynı hisse hep aynı metin (onayladığın metin yayınlanan metindir; kaos yok), farklı gün/hisse farklı varyant.
- **Cümle iskeleti çeşitliliği:** 3 kalıp dönüşümlü: sıralama ("X; Y; Z."), vurgu ("En dikkat çekeni X — üstüne Y."), bağlam-önce ("Rejim destekleyiciyken X ve Y birleşmiş durumda.").
- **Bağlam kuralları:** atr_pct ≥6 → temkin tonu eklenir; price <5 → "düşük fiyatlı hisse" uyarısı gerekçeye değil risk notuna gider; grade C → iddiasız dil zorunlu.
- **Değişmezler:** yalnız snapshot alanlarından üretim (sayı uydurma yasak — mevcut kural), her çıktı lint'ten geçer, kapanış cümlesi ("karar senin") havuzdan 3 varyant.
- **Kabul:** E8 script'i 10 günlük simülasyonda birebir tekrar 0; 30 örneği sen okuyup "insan yazmış" onayı vereceksin (Çrş akşamı 15 dk).

### E2 — Market bağlam satırı (`distribution/templates.py` + jobs) · Sal
- Kaynak: FRED makro rejim cache'i (`core/macro_regime`) + SPY son kapanış (mevcut price cache; yoksa satır atlanır — asla uydurma).
- Format: "Rejim: risk-on · SPX dün +%0.4 · sakin makro takvim." — 1 satır, lint'li.
- Fallback zinciri: rejim yok → sadece endeks; ikisi de yok → satır tamamen atlanır (boş klişe basılmaz).

### E3 — Risk notu havuzu (`snapshot_builder._risk_note`) · Sal
- 10 kalıp: yüksek-ATR, squeeze çift yön, düşük fiyat/likidite, gap-geri-dolma, haber-belirsizliği (catalyst varsa), C-grade genel, kombinasyonlar (squeeze+düşük fiyat özel metni)...
- Kural: aynı brifte iki adaya aynı not düşmez (aday sırasına göre alternatif seçilir); hafta içi tekrar sayacı E8'de raporlanır.

### E4 — 30 terimlik tek-kaynak sözlük · Sal-Çrş
- Yeni: `distribution/glossary.py` — tek tablo: `slug, name_tr, name_en, line_tr, line_en, card_en` (30 kayıt: mevcut 12 + float, spread, PEAD, dilution/offering, market cap, sector rotation, breakout, false breakout, stop-avı değil— dikkatli: compliance uyumlu kavramlar; overtrading, FOMO, survivorship bias, lift, IS/OOS, walk-forward, volatilite rejimi, earnings drift, halt, borrow fee...).
- `concepts.py` bu tablodan beslenir (geriye uyumlu); `scripts/gen_terms_ts.py` → `web/src/lib/terms.ts` otomatik üretir; CI'a "iki dosya senkron mu" testi.
- Kabul: 30 gün tekrarsız rotasyon testi + her kartın lint'i.

### E5 — Sabah tarama job'u · Çrş ⚠️ haftanın kritik parçası
- `dist_scan` job'u: **07:15 Europe/Vienna**, yalnız işlem günleri. Uygulama: localhost API'ye mevcut yoldan `POST /scan` — 1812'lik preset, 200'lük batch'ler sıralı (mevcut davranışla aynı kod yolu → export hook'u otomatik tetiklenir; ayrı ikinci tarama mantığı YAZILMAZ).
- Zaman bütçesi: 07:15 başlar; batch başına ~60-120 sn → 07:45 hedef, 07:50 draft'a yetişir.
- **Bekçi:** 07:40'ta `dist_scan_check` — export bugünün tarihini taşımıyorsa ⚠️ acil DM ("tarama gecikti/kırıldı; brif riskte"). 07:50 draft job'u zaten bayat-veri korumalı (asla eski veri yayınlamaz).
- Sembol kaynağı: mevcut preset listesi (`data/tickers` — Çrş'da tam dosya adını doğrulayıp bağlarım); auth gerekiyorsa servis token'ı çözümü o gün netleşir.
- Kabul: 3 prova gününde elle sıfır dokunuş.

### E6 — Yedek + bütünlük job'u · Çrş
- Pazar 20:00: `finpilot.db` + `distribution.db` + `.env` hariç config → `backups/YYYY-MM-DD/` kopya + `PRAGMA integrity_check` → sonuç DM ("✅ yedek alındı, bütünlük OK" / "❌ ...").
- 14 günden eski yedekler silinir (disk). İlk çalıştırmada restore provası: yedekten kopyayı açıp tablo sayımı — runbook'a yazılır.

### E7 — Arşiv süreklilik alarmı · Çrş
- Günlük 22:00: bugün `signals_archive`/export'a kayıt düştü mü? Düşmediyse DM. (İşlem günü değilse sessiz.)

### E8 — Çeşitlilik test script'i · Çrş
- `research/labs/content_variety_check.py`: son N günün (veya simüle 10 günün) brif metinlerini üretir → rapor: birebir tekrar cümle sayısı, kalıp dağılımı, risk-notu tekrarı, lint ihlali. Kapı denetiminin kanıt dosyası budur.

---

## 3. ÇARŞAMBA AKŞAMI — BİRLİKTE KURULUM SEANSI (~45 dk)
1. M7 .env bloğunu doldur → scheduler'ı yeniden başlat (`start.sh`).
2. Private kanal ID'sini birlikte çek → .env'e ekle.
3. **Manuel uçtan uca test:** ben taslağı elle tetiklerim → telefonuna DM gelir → `ONAYLA <id>` yazarsın → mesaj kanala düşer (kanal henüz boş/özel — seyirci yok, güvenli) → web/public snapshot'ının güncellendiğini görürüz.
4. E1 çıktı onayı: 30 örnek gerekçeyi okursun; "şu üslup olmaz" dediklerini o akşam düzeltirim.
5. Prova kuralları netleşir: 3 gün boyunca tek görevin 08:00-08:20 arası DM'e bakmak. Başka hiçbir şeye dokunmuyoruz.

## 4. DİKKAT EDİLECEKLER (tuzak listesi)
- **PC uykusu** = provanın 1 numaralı düşmanı (M2).
- **Saat dilimi:** tüm cron'lar Europe/Vienna — Windows saatinin doğru ve otomatik senkron olduğunu kontrol et.
- **API kotaları:** günlük tam tarama EODHD/Alpaca çağrısı üretir — prova haftasında ekstra elle tarama yapma (kota + çifte export karışıklığı).
- **Telegram limitleri:** sorun değil (günde 1-2 mesaj) ama botla kanal arasında test spam'i yapmayalım; testler Çrş seansında toplu.
- **Bu hafta deploy yok:** Vercel/VPS'te bir şey KURULMAZ; sadece hesap/erişim hazırlığı. (Erken deploy = yarım sistemle internete çıkmak.)
- **Tatil davranışı:** Cmt-Paz sistemin sessiz kalması normaldir ve doğru davranıştır — "çalışmıyor" sanma.
- **Onaysız gün:** DM'i kaçırırsan yayın olmaz — bu hata değil, tasarım. Prova bunu da bir kez bilerek test edecek (Cum günü onayı bilinçli geciktir, uyarının geldiğini gör).

## 5. KAPI DENETİMİ (Pzt akşam, birlikte 20 dk)
- [ ] 3 işlem günü: taslak otomatik üretildi + DM geldi (broadcast_queue kayıtları)
- [ ] O 3 günde: elle müdahale = 0 (tarama dahil)
- [ ] İçerik: variety raporu temiz (tekrar=0, lint=0) + senin "insan yazmış" onayın
- [ ] Bekçi/alarm en az 1 kez test edildi (bilinçli gecikme senaryosu)
- [ ] Yedek job'u 1 kez koştu + restore provası yapıldı
- [ ] M1-M7 hepsi tamam (OneDrive kararı yazılı, kanallar kurulu, hesaplar hazır)
- [ ] `LAUNCH_CHECKLIST.md` güncellendi
→ Hepsi ✓ ise **Hafta 2: Canlıya Taşıma** başlar. Bir madde eksikse hafta uzar — kapı esnemez.

---
*Başlıyoruz dediğinde: ilk iş `LAUNCH_CHECKLIST.md` + `PARKING_LOT.md`'yi oluşturur, E1'den kodlamaya girerim. Senin ilk işin M1 (dosya güvenliği) — her şeyden önce.*
