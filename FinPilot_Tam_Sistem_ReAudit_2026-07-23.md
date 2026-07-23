# FinPilot / FinSense — TAM SİSTEM RE-AUDIT & REALIGNMENT
**Tarih:** 2026-07-23 · **Sürüm:** 1.0 · **Önceki audit:** FinPilot_Tam_Sistem_Audit_2026-07-03.md
**Yöntem:** Bu rapor kopya değildir — repo, veri dosyaları, DB durumu ve tüm dokümanlar 23 Temmuz günü yeniden, kanıta dayalı denetlendi. Her bulgu bir aksiyonla biter.

---

## 1. YÖNETİCİ ÖZETİ

Sistem 3 Temmuz'dan bu yana **çok büyük yol aldı**: dağıtım katmanı sıfırdan kuruldu, ilk gerçek brif 10 Temmuz'da yayınlandı, taramalar 22 Temmuz'a kadar **her işlem günü** koştu, rationale motoru v3 (akıcı dil) canlıda, TR+EN çift snapshot üretiliyor, akademi sözlüğü web'e export edildi, `/academy` sayfası var. Parçalar tek tek iyi.

**Ama bütün, parçaların gerisinde.** Beş kritik kopukluk var:

1. **Canlı sitede compliance ihlali (P0):** Landing'in "Inside the Newsroom" mock bölümleri BUY/SELL/HOLD, Entry/Stop/Target, Stop-Loss/Kelly gösteriyor. Kendi lint kurallarımızın yasakladığı dil, kendi vitrinimizde.
2. **Web 13 gün bayat (P0):** Snapshot'lar 22 Temmuz'a kadar her gün üretilmiş; ama `web/public/demo_snapshot.json` hâlâ **10 Temmuz**. Snapshot→web köprüsü 10 Temmuz'dan beri kopuk. DoD#4 fiilen başarısız.
3. **Karar verildi, uygulanmadı (P0):** 17 Temmuz'da "cron'u kapat, elle tek-komut yayına geç" kararı yazıldı (WEB_VE_MANUEL_YAYIN_PLANI). Bugün: `publish_now.py` **yok**, `FINPILOT_ENABLE_DISTRIBUTION` hâlâ **1**. Sistem iki felsefe arasında askıda — cron da tam çalışmıyor, manuel akış da kurulmadı.
4. **Veri bütünlüğü (P0):** `distribution.db` bozuk görünüyor (son yazma 16 Tem) → onay/yayın geçmişi, edition sayacı doğrulanamıyor. `scan_export_latest.json`, `snapshot_latest.json`, `demo_snapshot.json` yerel kopyalarında NUL-kuyruk bozulması var. YONERGE §5'in istediği "bütünlük-kapılı okuyucu" kodda yok. `backups/` klasörü **boş** — E6 yedek job'u fiilen çalışmamış.
5. **"Tek doğruluk kaynağı" üç tane (P0-doküman):** LAUNCH_CHECKLIST, YONERGE ve 6-haftalık plan üçü de kendini SSoT ilan ediyor; otomasyon felsefesinde birbirleriyle çelişiyorlar. PARKING_LOT ise fiilen delinmiş durumda (Ledger tasarımı "lansman sonrası" diyor; çoktan canlıda).

**Genel sağlık skoru: 54/100** (gerekçesi Bölüm 11'de). 3 Temmuz'a göre üretim kabiliyeti arttı, tutarlılık azaldı.

---

## 2. AUDIT KAPSAMI + TARİHÇE HARİTASI

### 2.1 Audit history map
| Tarih | Ne denetlendi/üretildi | Sonuç |
|---|---|---|
| 07-03 | İlk tam audit + 5 strateji dokümanı (GTM, WebMVP, TgBot, Funnel, FinSense) | P0: tek Grade dili kararı |
| 07-05 | 6-haftalık iş planı + Hafta-1 yönergesi + uçtan uca ürün planı | Tasarım donduruldu, DoD 10 madde |
| 07-05→10 | E0–E8 kod denetimleri (test süitleri) | İlk gerçek brif 07-10'da yayında |
| 07-13 | Landing/Vercel denetimi + Morning Ledger dönüşüm planı | main birleştirildi, plan yazıldı |
| 07-17 | (ayrı oturum) Kırılma analizi → YONERGE + manuel yayın kararı | **Uygulaması eksik kaldı** |
| 07-20 | (ayrı oturum) İçerik yol haritası (enricher+akademi) | Akademi JSON'ları web'e export |
| **07-23** | **BU RAPOR** — tam yeniden denetim | — |

### 2.2 Bayat (stale) doküman listesi
- **PARKING_LOT.md** — "Ledger×Classroom kod uygulaması lansman sonrası İLK iş" diyor; landing çoktan Ledger'a dönüştü ve canlıda. Ayrıca "FinSense fabrika onarımı dokunulmaz" diyor; 07-20 yol haritası akademiyi web'e bağlamayı Faz 2-3 yaptı. **Fiilen delinmiş.**
- **LAUNCH_CHECKLIST.md** — Hafta-1 kapı maddeleri (3 günlük prova, bekçi/yedek testi, 30 örnek onayı) hâlâ boş; ama takvimde Hafta-3'teyiz. H1.5 (Ledger dönüşümü) hiç işlenmedi. M4 notu "GitHub 23 Haz'da" diyor — eskidi.
- **FinPilot_Hafta1_Yonerge_2026-07-05.md** — cron zinciri (07:15/07:50/08:30) merkezli; 07-17 manuel kararıyla çelişiyor. Supersede notu yok.
- **FinPilot_Landing_MorningLedger_Plani_2026-07-13.md** — plan G1-G3 hiç işaretlenmedi; landing başka bir yoldan (kullanıcı uygulaması) canlıya çıktı. Kapanış durumu belirsiz.
- **web/src/lib/i18n/translations.ts yorum bloğu** — "EN snapshot web için ayrı yayınlanır" iddiası kod gerçeğiyle uyumsuz (EN snapshot üretiliyor ama web OKUMUYOR).
- **FinPilot_Tam_Sistem_Audit_2026-07-03.md** — tarihi değer; "güncel durum" olarak okunmamalı. Arşive.

### 2.3 Hiç audit edilmemiş bileşenler
Render API deploy'u + SMTP/waitlist maili (07-17'de kuruldu) · `ShortlistEnricherAgent` (yerel qwen2.5:3b) · akademi→web export pipeline'ı (`academy_lessons.json`, `dictionary.json`, `/academy` sayfası) · `telegram_bot_runner.py`'nin manuel akıştaki geleceği · Finsense repo'nun üretim durumu (07-03 tasarım dokümanından beri) · Stripe/premium mekaniği (test bile edilmedi — DoD#9).

### 2.4 Son değişikliklerin etki haritası (07-13 → 07-23)
```
Kullanıcı Ledger landing'i uyguladı ─► compliance mock'ları canlıya taşındı (P0-1)
07-17 manuel-yayın kararı ─► uygulanmadı ─► cron/env/dok çelişkisi (P0-3)
                          └► bot_runner'ın rolü belirsizleşti
Sözleşme regresyonu + onarımı ─► 07-22 snapshot sağlıklı (A/B/C, rozetler, ~%75 band)
rationale v3 ─► TR+EN akıcı metin canlı ─► ama web hâlâ 07-10 metnini gösteriyor
partial/full export ayrımı ─► KISMEN kuruldu (dosya adları ✓, latest-guard kanıtı zayıf)
akademi export ─► web/public'te ✓ ─► /academy var; landing Classroom bağlantısı denetlenmedi
```

---

## 3. BİLEŞEN ENVANTERİ ve BİLEŞEN BAZLI DENETİM

Şablon: Amaç/Güncellik/Tutarlılık/Bağlantı/Kanıt/Risk → **Aksiyon**. (Sahip: M=Meriç, C=Claude, O=ortak)

### A. Ürün/sistem bileşenleri

**A1. Scanner + sözleşme (evaluate_symbol)** — Sahip: C
Amaç geçerli. 07-22 tam taramasında sözleşme alanları dolu (grade A/B/C ayrışıyor, badges dolu, prob_band ~%75) → regresyon onarımı **kanıtlı**. Ama: `company` alanı hâlâ boş; `universe=200` (YONERGE 1812 bekliyor — tam evren mi taranıyor belirsiz); YONERGE §2'nin istediği "yazma anında şema doğrulaması + contract test" kodda görünmüyor. Risk: sözleşme yine sessizce kırılır. **Aksiyon: contract-test dosyası + export'ta zorunlu alan kontrolü (P1); universe politikası netleşsin (200'lük batch mi, 1812 tam mı — YONERGE ile kod aynı dili konuşsun).**

**A2. Distribution katmanı (snapshot/lint/queue/telegram)** — Sahip: C
Kod sağlam, testli; v3 rationale + TR/EN çift snapshot üretimi canlı. Ama `distribution.db` bozuk/bayat (son yazma 07-16, "malformed") → onay-yayın zinciri 17 Tem'den beri **karanlıkta**; `edition_no` sayacı bu DB'ye bağlı. `snapshot_latest.json`/`scan_export_latest.json` NUL-bozulmalı. YONERGE §5 bütünlük kapısı (date==bugün ∧ universe==beklenen ∧ tek-JSON) **kodda yok**. **Aksiyon: (P0) Windows'ta DB integrity_check + gerekiyorsa yeniden kur; bütünlük-kapılı reader; atomic-write'a fsync/verify eklenmesi.**

**A3. Rationale motoru v3** — Sahip: C
Bu oturumda yazıldı, canlıda çalıştığı 07-22 snapshot'ıyla kanıtlı ("NBIS, bugünkü listenin en üst sırasında. Açığa satış tarafı kalabalık; …" — akıcı, nedensellikli). Kalan iki hata: `_cap` TR kuralını EN'e de uyguluyor → "İts …" (WEB_VE_MANUEL P1.3'te düzeltme yazılı, uygulanmadı); `prob_band:"—"` web cümlesini kırıyor (fallback metni UI'da yok). **Aksiyon: _cap(lang) yaması + web band-fallback (P1, küçük).**

**A4. Web — Ledger landing + /demo** — Sahip: O
UI zengin ve tema güçlü. Üç kırmızı bulgu: (1) **TheWire/EditorialBoard/FactCheckingDesk** mock verisi BUY/SELL/Entry/Stop/Target/Kelly içeriyor — kendi lint felsefemizin canlı ihlali; (2) veri **07-10'da donmuş** (13 gün); (3) dil karışımı — EN şablon + TR rationale; `snapshot_en_latest.json` üretiliyor ama web'in tek kaynağı TR `demo_snapshot.json`; DE anahtarı içeriksiz. Ayrıca Masthead'de "68% backtested win rate" ön sayfada — dipnotlu ama karne boşken vitrin iddiası olarak ağır. **Aksiyon: (P0) üç mock bileşenin Grade-dili reskini; (P0) snapshot→web köprüsü; (P1) EN/TR gösterim mantığı; (P2) 68% iddiasını karne dolana kadar "Ledger Strip"e taşı.**

**A5. Karne / doğruluk zinciri (outcome→by_grade)** — Sahip: C
`karne.by_grade` **hâlâ boş** — hafıza notuyla tutarlı (signals_archive 2026-05-22'de donmuş, resolver ölü). DoD#5 ve "dürüst karne" ürün vaadinin kalbi burası; web'in en ikna edici bileşeni (LedgerStrip) bu yüzden boş. **Aksiyon: resolver'ı diriltme işi resmen Hafta-planına girsin (P1 → DoD#5 kritik yolu).**

**A6. Scheduler + otomasyon** — Sahip: C
E0/E5 catch-up mimarisi kuruldu; ama 07-17 kararıyla artık **istenmeyen** mimari olabilir. Env hâlâ =1: cron job'ları kayıtlıysa sabahları çalışmaya çalışıyor. Snapshot'lar üretilmiş ama Telegram/web'e akış kanıtı yok → zincirin yarısı çalışıyor. **Aksiyon: (P0) KARAR NETLEŞSİN — ya manuel plan uygulanır (publish_now.py + flag=0) ya karar iptal edilir. İkisi arası yasak.**

**A7. Telegram bot runner** — Sahip: C
Manuel akışta gereksizleşiyor (onay=komut). Şu an rolü belirsiz. **Aksiyon: A6 kararına bağlı — manuelse "yalnız /start /today public komutları" moduna küçült ya da kapat (P2).**

**A8. Akademi/FinSense entegrasyonu** — Sahip: O
`academy_lessons.json` + `dictionary.json` + `/academy` sayfası var — 07-20 yol haritası Faz 2-3'ün ilk adımları atılmış. Ama bu, PARKING_LOT'un "FinSense'e dokunma" kuralını deliyor ve 6-haftalık tek-odak ilkesiyle gerilimde. Kanıt: lansman DoD'sinde akademi maddesi YOK. **Aksiyon: (P1) kapsam kararı — akademi entegrasyonu ya resmen plana alınır (hangi haftaya?) ya lansman sonrasına yazılır. Sessiz kapsam büyümesi bitmeli.**

**A9. Enricher (yerel AI)** — Sahip: C
Yazılmış, snapshot'a bağlanmamış. Lint'ten geçme zorunluluğu dokümante (✓). Lansman DoD'sinde yok. **Aksiyon: A8 ile aynı kapsam kararına tabi (P2).**

### B. Stratejik/operasyonel

**B1. 6-haftalık iş planı** — Takvimden sapma var: Hafta-1 kapısı (Pzt akşamı) hiç resmen geçilmedi; prova hiç koşulmadı ama sistem fiilen 6 iş günü üst üste snapshot üretti (07-14→22) — yani kapının RUHU kısmen sağlandı, KAYDI yok. **Aksiyon: (P1) kapı denetimi retroaktif yapılsın; takvim 23 Tem gerçekliğine göre yeniden çizilsin.**
**B2. GTM/Funnel/FreeToPaid** — İçerik geçerli; tarih varsayımları (4-hafta karne → premium) karne ölü olduğu için kayıyor. Supersede gerekmiyor, tarih revizyonu yeter (P2).
**B3. Hibe/aws** — Hafıza notu net: Temmuz-2026 konumlandırması onaylı, NVIDIA-deck rakamları asla kullanılmaz. Park halinde, çelişki yok (P3).

### C. Dokümantasyon — bkz. Bölüm 7. **D. Governance** — bkz. Bölüm 5/10.

---

## 4. SİNERJİ MATRİSİ

| Bileşen A | Bileşen B | İlişki | Not |
|---|---|---|---|
| Scanner sözleşmesi | Snapshot/rationale | **Güçlendirir** (onarıldı) | 07-22 kanıtlı; contract-test yoksa kırılgan |
| Snapshot üretimi | Web gösterimi | **KOPUK** | 9 günlük snapshot birikti, web 07-10'da |
| Snapshot (EN) | Web dil anahtarı | **Habersiz** | EN üretiliyor, web tüketmiyor — aynı amaca iki kör parça |
| YONERGE kuralları | Kod gerçeği | **Çelişir** | Bütünlük kapısı, contract-test, 1812-smoke yazılı ama kodda yok |
| 07-17 manuel kararı | Scheduler/env | **Çelişir** | Karar dokümante, uygulama sıfır |
| Ledger tasarımı | Lint felsefesi | **Çelişir** | Mock bölümler yasak dili basıyor |
| Karne (boş) | Masthead %68 iddiası | **Zayıflatır** | Kanıtsız vitrin iddiası ürün dürüstlük anlatısını baltalar |
| Akademi export | ClassroomPreview/DailyDouble | **Bağlanmalı** | JSON'lar hazır, landing bileşenleriyle bağı denetlenmedi |
| Rationale v3 | Telegram şablonları | **Güçlendirir** | Aynı motor, tek ses |
| dist_live_test/publish akışı | distribution.db | **Kırık temel** | DB bozuksa onay zinciri ve edition_no güvenilmez |
| PARKING_LOT | Fiili iş akışı | **Ölü kural** | Delinen kural, kural disiplinini de öldürür |
| Backup job (E6) | backups/ klasörü | **Sahte güven** | Job yazıldı, klasör boş — koruma yok |

---

## 5. ÇELİŞKİ ve ÇIKMAZ LİSTESİ

1. **Felsefi (en büyük):** "Tam otomatik cron + catch-up" (Hafta-1 mimarisi, kod) vs "elle tek-komut, cron sustur" (07-17 kararı). İkisi de yarım. **Kazanmalı:** 07-17 manuel kararı — çünkü fiili işletme gerçeği (PC elle açılıyor, timing baskısı) onu doğruladı. Cron kodu silinmez, flag'le uyur.
2. **SSoT çatışması:** Üç doküman kendine "tek doğruluk kaynağı" diyor. **Çözüm:** rol ayrımı — YONERGE=nasıl çalışırız (ops), LAUNCH_CHECKLIST=neredeyiz (durum), 6-haftalık plan=nereye gidiyoruz (strateji; tarih revizyonuyla). Bölüm 9'da işlendi.
3. **Compliance:** lint kuralları ↔ canlı mock içerik. **Kazanmalı:** lint — istisnasız, mock/örnek veri dahil. ("Illustrative" etiketi ihlali meşrulaştırmaz; GTM §9 dış yüzeyin TAMAMI der.)
4. **Veri çelişkisi:** `universe` tanımı — YONERGE "1812 tam evren", fiili export 200, Masthead "1.800+ stocks scanned" gösteriyor ama snapshot'tan 200 gelirse "200+" yazar. Tek tanım gerek.
5. **Zaman çelişkisi:** 6-haftalık plan Hafta-3'te "prova" der; 07-20 yol haritası aynı haftalara enricher/akademi fazları koyar. Aynı kaynak (Claude+Meriç saatleri) iki plana yazılmış.
6. **Kayıt çelişkisi:** translations.ts yorumu "EN snapshot web için yayınlanıyor" der; web kodu tek TR dosya okur. Dokümantasyon kod-gerçeğinden kopuk.
7. **Süreç çelişkisi:** YONERGE "Claude büyük/kritik dosyaları doğrudan düzenlemez, snippet verir" der; önceki oturumlar (bu dahil) doğrudan düzenledi. **Kazanmalı:** YONERGE kuralı — bundan sonra üretim-kritik dosyalarda snippet+Meriç-uygular modeli; istisna: yeni/izole dosyalar.

---

## 6. TEKNİK / STRATEJİK BORÇ

| # | Borç | Risk | Düzeltme maliyeti | Düzeltilmezse | Öncelik |
|---|---|---|---|---|---|
| 1 | Bütünlük-kapısız JSON okuma/yazma (NUL-bozulma sessiz geçer) | Bayat/bozuk veri yayını | Küçük (30-40 satır) | Bir sabah bozuk brif yayınlanır | **P0** |
| 2 | distribution.db bozuk + backups/ boş | Onay/yayın tarihçesi kaybı | Orta | Edition sayacı, karne kayıtları gider | **P0** |
| 3 | publish_now.py yok, flag=1 | İki sistem çakışması | Küçük (script hazır, dokümanda) | Çift DM / hiç DM sorunları sürer | **P0** |
| 4 | Contract-test yok (YONERGE §2 yazılı, kod yok) | Sessiz regresyon tekrarı | Orta | 07-14 krizi tekrarlanır | P1 |
| 5 | Karne resolver ölü (05-22'den beri) | DoD#5 imkânsız | Büyük | Ürünün güven vaadi boş kalır | P1 |
| 6 | "İts" _cap hatası + band "—" kırık cümle | Görünür kalite hatası | Çok küçük | Özensizlik algısı | P1 |
| 7 | Landing plan dosyaları kapanış durumsuz (G1-G3, H1.5) | İzlenebilirlik kaybı | Çok küçük | "Ne bitti?" belirsizliği büyür | P2 |
| 8 | telegram_bot_runner rolü belirsiz | Ölü kod çalışır durumda | Küçük | Kafa karışıklığı, çift onay riski | P2 |
| 9 | Kök dizinde 17 .md, versiyon hiyerarşisi yok | Karar kalitesi düşer | Küçük | Her oturum yanlış dokümana bakar | P2 |
| 10 | @Finpilot_Breif yazım hatası | Marka | Küçük ama linkler kırılır | Kalıcılaşır | P3 |

Dokümante edilmemiş kararlar (artık kayıtlı): Render API'ye geçiş · SMTP/waitlist maili · akademi web-export'u · v3 rationale'in canlıya alınması · landing'in kullanıcı eliyle uygulanması.

---

## 7. DOSYA ve DOKÜMANTASYON DÜZENİ ÖNERİSİ

```
Borsa/
├── README.md
├── YONERGE.md                  ← OPS SSoT (nasıl çalışırız)
├── LAUNCH_CHECKLIST.md         ← DURUM SSoT (neredeyiz)
├── PARKING_LOT.md              ← güncellenmiş haliyle
└── docs/
    ├── INDEX.md                ← her bileşen için "tek doğru kaynak" tablosu
    ├── strategy/               ← 6-haftalık plan (tarih-revize) · GTM · Funnel · İçerik yol haritası
    ├── ops/                    ← WEB_VE_MANUEL_YAYIN_PLANI (uygulanınca YONERGE'ye gömülür)
    └── archive/2026-07/        ← 07-03 audit · Hafta1 yönergesi · MorningLedger planı ·
                                   Master tasarım · WebMVP/TgBot spec'leri · 3x şablon dokümanı
```
Kurallar: her doküman başına `Durum: AKTİF | UYGULANIYOR | ARŞİV` + `Supersedes/Superseded-by` satırı · aynı konuda ikinci doküman açmak yasak, mevcuda bölüm eklenir · runtime çıktıları (factor_ablation_*.md) `reports/` altına, data/ içinde doküman durmaz.

---

## 8. ÖNCELİKLENDİRME (P0 → P3)

| Öncelik | İş | Sorumlu | Efor | Fayda |
|---|---|---|---|---|
| **P0-1** | Landing mock bileşenlerinden al/sat dilini söküp Grade-dili reskini (TheWire→Grade/P-Band/Factors; EditorialBoard→A/B/C oyu; FactCheckingDesk→"Compliance Gate"+dipnotlu walk-forward) | C (snippet) + M (uygula) | ½ gün | Canlı compliance riski biter |
| **P0-2** | Yayın kararını UYGULA: `publish_now.py` + `FINPILOT_ENABLE_DISTRIBUTION=0` + günlük 2-adım ritüel | C+M | ½ gün | Tek akış, çakışma biter |
| **P0-3** | Snapshot→web köprüsü publish_now içine (demo_snapshot.json güncelle + bütünlük doğrula + git push tek dosya) | C | ½ gün | Web her gün taze — DoD#4 |
| **P0-4** | Windows'ta: `PRAGMA integrity_check` → distribution.db onar/yeniden kur; E6 backup'ı gerçekten çalıştır + backups/ doğrula | M (C komut verir) | 1-2 saat | Tarihçe ve sayaçlar güvene alınır |
| **P0-5** | Bütünlük-kapılı okuyucu/yazıcı (date/universe/tek-JSON + NUL kontrolü; aykırıysa YÜKSEK SESLE hata) | C | ½ gün | Sessiz bozulma sınıfı kapanır |
| **P1-1** | EN/TR web gösterimi: dil anahtarına göre doğru rationale (+ "İts" _cap yaması + band "—" fallback) | C | ½ gün | Dil karmaşası biter |
| **P1-2** | Contract-test + export şema zorunluluğu | C | ½ gün | Regresyon sigortası |
| **P1-3** | Karne resolver diriltme planı (signals_archive 05-22'den çözümleme) | C | 1-2 gün | DoD#5 yolu açılır |
| **P1-4** | LAUNCH_CHECKLIST + takvim revizyonu (retroaktif Hafta-1 kapısı, H1.5 kaydı, yeni hafta sayacı) | O | 1 saat | Durum SSoT gerçeğe döner |
| **P2** | Kapsam kararı: akademi/enricher hangi haftada? · bot_runner küçült · dosya düzeni (Bölüm 7) · Masthead %68'i karneye bağla · plan dosyalarına kapanış durumu | O | 1 gün | Odak + düzen |
| **P3** | Breif→Brief handle · kozmetik cila · DE içerik kararı | M | — | Marka |

---

## 9. REALIGNMENT PLANI

**R1 — Rol netliği (bugün):** YONERGE=ops anayasası · LAUNCH_CHECKLIST=durum panosu · docs/strategy=yön. Üç dokümanın başına bu rol yazılır; diğer her şey arşiv/referans. INDEX.md "hangi soruya hangi doküman" tablosunu tutar.
**R2 — Tek yayın akışı (bu hafta):** P0-2+P0-3 birlikte: sabah → tam tarama → `publish_now.py --yes` → Telegram + web aynı snapshot_id. Cron uyur (silinmez). Bot runner yalnız public komutlar. Hafta-1 yönergesindeki cron bölümüne "SUPERSEDED by YONERGE §6+WEB_VE_MANUEL" damgası.
**R3 — Compliance temizliği (bu hafta):** P0-1 + kural: **mock/örnek veri de lint'ten geçer**. YONERGE §12'ye 8. kırmızı çizgi: "Örnek/mock içerik dahi yasak dil içeremez."
**R4 — Veri bütünlüğü (bu hafta):** P0-4+P0-5. Ek kural (YONERGE §5'e): her yazma sonrası geri-okuma doğrulaması; NUL/çift-JSON tespitinde admin DM.
**R5 — Dil bütünlüğü (gelecek hafta):** P1-1. Karar: DE ya tam içerik alır ya anahtar gizlenir — yarım dil yok.
**R6 — Takvim gerçeklemesi (Pazartesi ritüeli):** P1-4; 6-haftalık plan tarihleri 23-Tem tabanına kaydırılır; akademi/enricher kapsam kararı aynı toplantıda verilir ve PARKING_LOT güncellenir.
**Kontrol sorusu:** "Bu audit'ten sonra sistem daha tutarlı mı?" — Ancak R1-R4 kapanırsa EVET. Rapor tek başına hiçbir şeyi hizalamaz.

---

## 10. SÜREKLİLİK MEKANİZMASI

- **Haftalık (Pzt, 20 dk):** LAUNCH_CHECKLIST + PARKING_LOT + "geçen hafta hangi doküman yalan söyledi?" sorusu.
- **60 günde bir:** bu şablonla tam re-audit (sıradaki: **2026-09-21**).
- **Değişiklik tetikleyicileri:** scanner sözleşmesi değişti → YONERGE §2 + contract-test + snapshot-test birlikte güncellenir · yeni yüzey (web bileşeni/kanal) → lint kapsam kontrolü · yeni "karar dokümanı" → uygulanma tarihi ve sahibi yazılmadan geçerli sayılmaz (uygulanmayan karar = çelişki üretir; 07-17 dersi).
- **Audit log formatı** (docs/INDEX.md altına): `tarih · ne denetlendi · bulgu sayısı (P0/P1) · ne değişti · onaylayan`.
- **"Karar → uygulama" kuralı:** her karar dokümanının sonunda zorunlu blok: *Uygulama sahibi / hedef tarih / doğrulama kanıtı*. Boşsa karar sayılmaz.

---

## 11. GENEL SAĞLIK SKORU: **54/100**

| Boyut | Skor | Gerekçe (kanıt) |
|---|---|---|
| Motor/scanner | 70 | 07-22 sözleşmeli, ayrışan grade'ler; contract-test yok, company boş |
| Distribution kodu | 65 | Test süitleri + v3 canlı; DB bozuk, bütünlük kapısı yok |
| Web ürünü | 45 | UI güçlü; compliance ihlali + 13 gün bayat veri + dil karışımı |
| Veri bütünlüğü | 30 | 4 bozuk dosya, boş backups/, doğrulanamayan DB |
| Doküman/governance | 45 | Zengin ama 3 SSoT çatışması, 2 uygulanmamış karar, delinmiş parking |
| Operasyonel süreklilik | 60 | 6 iş günü kesintisiz snapshot (güçlü!); Telegram/web akışı kanıtsız |
| **Ağırlıklı genel** | **54** | Üretim kabiliyeti ↑, bütünsel tutarlılık ↓ — sistem "en bozuk köprüsü kadar" |

**Tek cümle:** Parçalar 3 Temmuz'dan beri belirgin güçlendi; şimdi işin tamamı köprüleri onarmak — snapshot→web, karar→uygulama, kural→kod. Önümüzdeki 5 iş günü yalnız P0 listesine harcanırsa skor 70+ bandına çıkar ve lansman sayacı gerçekten işlemeye başlar.
