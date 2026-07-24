# FinPilot — GENEL SİSTEM SAĞLIĞI ÖN-TARAMASI (PRE-SCAN)
**Tarih:** 2026-07-24 · **Sürüm:** 1.0 · **Tür:** Audit ÖNCESİ keşif taraması
**İlişkili:** FinPilot_Tam_Sistem_ReAudit_2026-07-23.md (dünkü tam audit) — bu rapor onun kopyası değil; 24 Temmuz günü DB, dosya sistemi, log ve kod üzerinden **yeniden kanıt toplandı**.
**Amaç:** Bir sonraki derin audit'in nereye bakacağını, hangi soruları soracağını ve hangi verileri toplayacağını netleştirmek.

---

## 1. YÖNETİCİ ÖZETİ

**Önce iyi haber — dünkü audit'in P0'ları büyük ölçüde KAPANMIŞ (kanıtlı):**
`publish_now.py` mevcut, `FINPILOT_ENABLE_DISTRIBUTION=0` (manuel akış resmen devrede). Bugünkü tarama **tam evrende koştu** (universe=1812, taranan=1801) ve zincir uçtan uca çalıştı: scan 14:04 → snapshot 14:59 → web push 15:00 → Telegram "sent" (edition #5). `demo_snapshot.json` **bugünün tarihini** taşıyor — 13 günlük bayatlık sorunu bitmiş. `distribution.db` integrity_check **ok**, NUL bozulması taranan dosyalarda **yok**, `backups/2026-07-23/` içinde finpilot.db + distribution.db kopyaları var. Landing mock bileşenlerinde (TheWire, EditorialBoard) yasak al/sat dili grep'te **bulunamadı**; kalan tek eşleşme "not buy/sell advice" uyarı metni. Yani 23 Temmuz'daki 5 kritik kopukluğun 4'ü fiilen onarılmış görünüyor.

**En kritik 5 bulgu (bugünkü kanıtla):**

1. **Karne zinciri hâlâ ölü — sistemin güven vaadinin kalbi boş (P0-yol).** `signals_archive` son kaydı **2026-05-22** (2 aydır donuk), `outcomes_horizon=0`, `signal_events=0`, bugünkü snapshot'ta `by_grade:{}` ve `warnings:["karne unavailable"]`. `scripts/resolve_open_signals.py` var ama çalışmıyor/beslenmiyor. Asıl soru derin audit'e: **arşive yazan taraf mı öldü, çözümleyen taraf mı** — çünkü taramalar her gün koşuyor ama arşiv büyümüyor.

2. **"10 ardışık gün" sayacı kırık, seyirci 1 kişi.** `broadcast_queue`: #18–19 "sent" (23–24 Tem), ama #15–17 **"expired"** (20–22 Tem yayınlanamamış). Mevcut kesintisiz seri: **2 gün**. `tg_users=1` (admin), `waitlist=0`, `beta_invites=0`. DoD#1 ve #7 için saat sıfırdan başlıyor.

3. **Yayın saati "sabah brifi" iddiasıyla çelişiyor.** Bugünkü zincir 13:53–15:00 arasında koştu; ABD piyasası perspektifinde erken ama "Morning Ledger / sabah operasyonu ≤15 dk" hedefinin kaydı yok. Tek ölçülebilir veri: tam evren taraması son partial'ları 13:53→14:04 (≈11 dk pencere görünür, toplam süre loglanmıyor). **Performans enstrümantasyonu yok** — süreler dosya mtime'larından tahmin ediliyor.

4. **Çekirdek DB tabloları by-pass edilmiş durumda.** `signals=0`, `scan_results=0`, `buy_signals=0`, `execution_intents/events=0` — üretim zinciri tamamen JSON-export üzerinden akıyor, DB şeması ölü ağırlık. Bu bilinçli bir mimari karar mı yoksa sessiz bir kopukluk mu, kayıtlı değil. (Alpaca oto-execution planı 07-23'te yazıldı; execution tabloları bomboş — plan kâğıtta.)

5. **Doküman gerçeği yine koddan geriye düştü.** LAUNCH_CHECKLIST hâlâ "DISTRIBUTION=1" diyor (bugün 0), DoD#4 işaretsiz (bugün fiilen çalışıyor), Hafta-1 kapısı hiç kayda geçmedi. `docs/INDEX.md` + `docs/strategy/` kurulmuş ama `docs/ops/` ve `docs/archive/` yok; kökte hâlâ ~25 .md. PARKING_LOT'un "akademi export'una dokunma" kuralı fiilen delik (academy_lessons.json + /academy canlı). Dünkü audit'in R1 maddesi yarım.

**Genel sağlık: ~60/100** (dün 54). Üretim zinciri onarıldı; şimdi darboğaz **kanıt üretimi** (karne, seri, kullanıcı) ve **kayıt disiplini**.

---

## 2. BİLEŞEN ENVANTERİ VE TARAMA DURUMU

| Bileşen | Son güncelleme kanıtı | Bilinen durum | Derin audit'te bakılacak |
|---|---|---|---|
| Scanner + sözleşme (`scanner/`, 20+ modül) | scan_export 24 Tem 14:04, tam evren | **iyi** | contract-test var mı; eligible=2 seçiciliği kasıtlı mı |
| Distribution (`distribution/`, snapshot/lint/tg) | snapshot_latest 24 Tem 15:01 | **iyi** | bütünlük-kapılı reader kodda mı (P0-5 kanıtı) |
| publish_now akışı | `scripts/publish_now.py` mevcut, flag=0 | **iyi** | günlük ritüel dokümante mi; hata dalı test edildi mi |
| Web / Ledger landing (`web/`) | demo_snapshot 24 Tem, compliance temiz | **iyi-şüpheli** | FactCheckingDesk içeriği; EN snapshot'ı web tüketiyor mu; Masthead %68 |
| Karne / resolver | signals_archive maks 2026-05-22 | **ölü** | arşiv yazıcısı mı resolver mı kırık; 5719 eski kayıt çözülebilir mi |
| Execution / Alpaca (`execution/`, `broker/`) | alpaca_orders=10 (eski), intents=0 | **uykuda** | 07-23 mimari planının ilk adımı tanımlı mı |
| DRL / agents / llm (30+ modül) | loglar Mart–Mayıs | **uykuda** | lansmanla ilişkisi; ölü kod mu varlık mı |
| Academy (Borsa tarafı `academy/`) | academy_lessons.json 23 Tem (1 KB!) | **şüpheli** | export içeriği neden bu kadar küçük; 4 ders mi geliyor |
| FinSense repo | worker bugün koştu (n=6, 24 Tem); academy.db integrity **ok**; 9 ders (4 published/5 draft), 86 content_job, 302 agent_log | **çalışıyor** | .corrupt.bak geçmişi; üretim hızı hedefi; Borsa'ya export köprüsü |
| Monitoring (`monitoring/`) | prometheus/alerts 20 Mayıs'tan beri dokunulmamış | **ölü konfig** | hiç çalıştı mı; manuel akışta yeri var mı |
| Backups | tek klasör: 2026-07-23 (manuel) | **kırılgan** | E6 tekrarlayan mı, tek seferlik miydi |
| Test altyapısı | 50 test dosyası; .coverage 23 Mayıs | **belirsiz** | süit yeşil mi; contract-test kapsamı |
| Auth/kullanıcı | users=4 (test), sessions=47 | **MVP** | premium/Stripe DoD#9 hiç test edilmedi |

---

## 3. STABİLİTE BULGULARI VE RİSK HARİTASI

**Kanıtlar:** api.log'da 634 "error" satırı (çoğu 23 Tem test koşuları — ayıklanmalı); broadcast 3 kez "expired" (yayın penceresi kaçmış → sessiz başarısızlık sınıfı hâlâ yaşıyor); tek yedek klasörü; `finpilot_recovered_20260703.db` ve FinSense'te `academy.db.corrupt.bak` — **iki repo'da da DB bozulma geçmişi var**, ikisi de şu an sağlıklı ama bozulma kaynağı (muhtemelen OneDrive/AV + SQLite WAL etkileşimi) teşhis edilmedi.

**En kırılgan 5 nokta:**

1. **Tek-PC, tek-insan operasyonu** — PC açılmazsa yayın yok; "expired" kayıtları bunun kanıtı (yüksek).
2. **DB bozulma kök nedeni bilinmiyor** — iki repo'da bozulma yaşandı, tekrarlayabilir; yedek tek gün (yüksek).
3. **Karne arşiv yazıcısı sessizce ölmüş** — 2 ay kimse fark etmedi; aynı sınıftan başka sessiz ölüm olabilir (yüksek).
4. **Bütünlük-kapılı okuyucu kanıtı yok** — dosyalar bugün temiz ama kapı kodda doğrulanamadı; bir sonraki bozulmada yine sessiz geçer (orta-yüksek).
5. **Dış bağımlılıklar tekil** — tek veri sağlayıcı zinciri, tek Telegram botu, Vercel+Render ikilisi; fallback tanımsız (orta).

Risk seviyeleri: **Yüksek:** karne zinciri, yedekleme sürekliliği · **Orta:** yayın penceresi disiplini, monitoring yokluğu, api.log gürültüsü · **Düşük:** scanner sözleşmesi (bugün kanıtlı sağlam), distribution kodu.

---

## 4. PERFORMANS / HIZ DARBOĞAZ LİSTESİ

| Adım | Ölçülen/tahmini süre | Kanıt | Not |
|---|---|---|---|
| Tam evren taraması (1812) | görünür pencere ≥11 dk (13:53→14:04 partial'lar); toplam **ölçülmüyor** | dosya mtime | 1. darboğaz adayı — süre logu yok |
| Scan→snapshot | ~55 dk (14:04→14:59) | dosya mtime | 2. darboğaz: bu aralıkta ne oluyor? (LLM rationale? manuel bekleme?) Derin audit sorusu |
| Snapshot→web+TG | ~1-2 dk | 14:59→15:01 | sağlıklı |
| Backtest | veri yok (son büyük koşular Nis–May) | logs/ | lansman kritiği değil |
| Web yükleme | ölçülmedi | — | Lighthouse koşusu öneri |

**Hızlandırma önceliği:** (1) zincire adım-bazlı süre logu ekle (yarım gün, her şeyin ön koşulu); (2) 14:04–14:59 boşluğunu açıkla — otomasyon değil insan beklemesiyse sorun değil, hesaplamaysa optimize; (3) "sabah ≤15 dk" hedefi ölçülür hale gelsin. **Uyarı:** performans şu an his ile yönetiliyor; tek gerçek veri dosya saatleri.

---

## 5. BAĞLANTI SAĞLIĞI MATRİSİ

| Bileşen A | Bileşen B | Durum | Not |
|---|---|---|---|
| Scanner export | Snapshot builder | **sağlıklı** | 24 Tem uçtan uca kanıtlı, tam evren |
| Snapshot | Web (demo_snapshot) | **sağlıklı (YENİ)** | dün kopuktu, bugün aynı-gün verisi |
| Snapshot | Telegram | **sağlıklı-kırılgan** | 2 gün "sent", öncesi 3 gün "expired" |
| Karne resolver | signals_archive | **KOPUK** | arşiv 05-22'de donuk; resolver script sahipsiz |
| Karne | Web LedgerStrip | **KOPUK** | by_grade boş → en ikna edici bileşen boş |
| Günlük scan | signals_archive | **KOPUK (yeni tespit)** | scan koşuyor ama arşive yazmıyor — karnenin geleceği de yok |
| EN snapshot (snapshot_en_latest) | Web dil anahtarı | **habersiz** | EN üretiliyor (bugün de), web tüketimi doğrulanmadı |
| Scan zinciri | finpilot.db (signals/scan_results) | **kopuk/by-pass** | bilinçli mi belirsiz — kayıt yok |
| Academy export | Web /academy | **zayıf** | academy_lessons.json 1 KB — 9 dersin çok azı akıyor |
| FinSense worker | Borsa web | **manuel köprü** | export elle; otomasyon kararı verilmedi |
| glossary.py (231 girdi) | dictionary.json (293, 20 Mayıs) | **şüpheli** | iki sözlük kaynağı, senkron kanıtı yok |
| Monitoring | Her şey | **kopuk** | konfig var, çalışan sistem yok |
| Execution planı (07-23) | execution/ kodu | **kâğıtta** | intents/events=0 |

---

## 6. DENEME YAYINLARI DEĞERLENDİRMESİ

**Zaman çizelgesi (kanıt: data/distribution/ + broadcast_queue):**
İlk brif 07-10 · snapshot'lar işlem günlerinde kesintisiz üretildi: 10, 13–17, 20–24 Tem (11 işlem günü ✓) · **ama yayın (delivery) farklı hikâye:** #15–17 expired (20–22 Tem), #18–19 sent (23–24 Tem) · edition sayacı: **5** — yani 11 üretim gününün yalnızca ~5'i gerçekten yayınlandı.

**Ne çalıştı:** üretim tarafı (scan→snapshot) tatil günleri hariç hiç aksamamış — bu sistemin en güçlü kanıtı. Sözleşme onarımı sonrası (07-22+) grade ayrışması ve rozetler sağlıklı.
**Ne çalışmadı:** yayın adımı insana bağlı ve 3 kez pencereyi kaçırdı; geri bildirim döngüsü fiilen yok (tg_feedback=0, demo_feedback=0, izleyici=1).
**Yayın-canlı farkı:** "deneme yayını" şu an gerçek kullanıcısız yapılıyor — gerçek yükü, gerçek soru/şikâyeti test etmiyor. Edge-case tatbikatı (kırmızı-gün prosedürü, DoD#10) hiç yapılmadı.

**Canlıya geçiş için hâlâ eksik checklist:** kesintisiz 10 günlük *yayın* serisi (üretim değil) · karne dolu · ≥25 takipçi · premium uçtan uca test · kırmızı-gün tatbikatı · mobil 3-cihaz testi · dış okuyucu kalite turu.

---

## 7. SÖZLÜK / TERMİNOLOJİ KAPSAM HARİTASI

**Mevcut:** `distribution/glossary.py` (328 satır, ~231 girdi benzeri yapı) · `web/public/dictionary.json` (**293 terim**, ama dosya **20 Mayıs'tan** kalma) · E4 "30 terimlik tek-kaynak sözlük + terms.ts üretici" tamam işaretli · FinSense tarafında ayrıca ders/terim üretimi.

**Sorunlar:**
- **Üç ayrı sözlük kaynağı** (glossary.py, dictionary.json, FinSense corpus) — "tek-kaynak" ilkesi kâğıtta. Hangisi üretiyor, hangisi türev? Derin audit sorusu.
- dictionary.json 2 aydır güncellenmemiş; bu aralıkta eklenen kavramlar (prob_band, conviction, edition, karne/by_grade, Grade A/B/C dili, partial/full export) sözlükte var mı doğrulanmadı — **muhtemelen yok**.
- TR/EN karışımı terminoloji: kod "karne" der, web "Ledger/scorecard" der; "composite score" vs "finpilot_score" ikiliği kodda yaşıyor (`finpilot_score.py` + `score_engine.py`).
- Kullanıcı yüzeyi–iç doküman tutarlılığı hiç test edilmedi (kullanıcı yok — ama lansman öncesi tek şans şimdi).

**Genişletme önceliği:** (1) tek üretici dosya + iki türev export kuralı; (2) Temmuz kavramlarının eklenmesi; (3) her terime seviye (başlangıç/ileri) + ilişkili terim — FinSense ders köprüsüyle birleşince /academy'nin gerçek içeriği olur.

---

## 8. EKSİK / YARIM KALMIŞ ALANLAR

| # | Alan | Durum | Kritiklik | Tamamlanmazsa risk |
|---|---|---|---|---|
| 1 | Karne zinciri (arşiv yazımı + resolver + by_grade) | kod var, 2 aydır ölü | **P0-yol** | Ürünün dürüstlük vaadi kanıtsız kalır; DoD#5 imkânsız |
| 2 | Bütünlük-kapılı okuyucu/yazıcı (dünkü P0-5) | kodda kanıt bulunamadı | **P1** | Sonraki bozulma yine sessiz geçer |
| 3 | Contract-test (`tests/test_scan_contract.py`) | varlığı doğrulanmadı | **P1** | 07-14 regresyon krizi tekrarlanır |
| 4 | EN snapshot → web tüketimi | üretim ✓, tüketim ? | P1 | Yarım dil; EN kullanıcıya TR metin |
| 5 | LAUNCH_CHECKLIST güncellemesi (retroaktif kapı + DoD#4 işareti + M7 düzeltmesi) | bayat | P1 | Durum SSoT yine yalan söylüyor |
| 6 | E6 yedeğin *tekrarlayan* hale gelmesi | tek manuel yedek | P1 | Tek kopya = kopya yok |
| 7 | docs/ops + docs/archive + kök .md temizliği (dünkü Bölüm 7) | yarım | P2 | Her oturum yanlış dokümana bakma riski |
| 8 | Premium/Stripe mekaniği | hiç test edilmedi | P2 (DoD#9) | Lansman haftasında sürpriz |
| 9 | telegram_bot_runner rol kararı | belirsiz | P2 | Çift onay/ölü süreç riski |
| 10 | Kırmızı-gün prosedürü tatbikatı | hiç | P2 (DoD#10) | İlk gerçek kriz provasız yaşanır |
| 11 | Alpaca oto-execution (07-23 planı) | kâğıtta | P3 (bilinçli erteleme?) | Yok — ama plan sahipsizse çelişki üretir |
| 12 | Monitoring/alerting | ölü konfig | P3 | Sessiz ölümler (bkz. karne) tekrar eder |

---

## 9. GELİŞTİRİLMEYE AÇIK POTANSİYEL ALANLAR

| Alan | Şu anki durum | Potansiyel | Etki | Efor |
|---|---|---|---|---|
| **signals_archive'daki 5719 tarihi kayıt** | donuk veri | Geriye dönük çözümleme → karne İLK GÜNDEN dolu başlar (Eyl 2025–May 2026 track record!) | **yüksek** | orta |
| FinSense içerik motoru | çalışıyor (86 job, bugün 6 worker) | published ders sayısını 4→20+ çıkarıp /academy'yi gerçek ürüne çevirme | yüksek | orta |
| Agents katmanı (bear/bull researcher, risk_agent…) | uykuda | Brif rationale'ine "karşı görüş" satırı — içerik kalitesi farklılaştırıcı | orta | orta |
| tg_delivery_log + editions | veri birikiyor | Otomatik "bu hafta ne yayınladık" özeti → Cuma ritüeli beslemesi | orta | küçük |
| Partial export'lar (batch başına dosya) | sadece debug | Batch-bazlı süre ölçümü bedavaya çıkar (Bölüm 4 enstrümantasyonu) | orta | küçük |
| dictionary.json + GlossaryTooltip | 293 terim, bayat | Temmuz terimleriyle güncelle + ders linkleri → SEO ve retention | orta | küçük |
| DRL/backtest altyapısı | uykuda ama zengin | aws Deep Tech anlatısında "Labs" kanıtı olarak paketleme (koda dokunmadan) | orta | küçük |
| watchlist_signals (999 kayıt) | kullanımı belirsiz | Kullanıcı-özel alert temeli (PARKING_LOT'ta — lansman sonrası) | düşük-şimdilik | — |

---

## 10. GENEL SAĞLIK SKORLAMASI

| Boyut | Skor | Kritik bulgu | Öncelik |
|---|---|---|---|
| İçerik/Mantık sağlığı | 70 | Sözleşme sağlam, tam evren; eligible=2 seçiciliği incelenmedi; contract-test kanıtsız | P1 |
| Stabilite | 55 | 3× expired yayın; DB bozulma kök nedeni teşhissiz; tek yedek | P0-P1 |
| Performans/Hız | 55 | Hiç ölçülmüyor; 14:04→14:59 boşluğu açıklanmalı | P1 |
| Bağlantı sağlığı | 62 | Snapshot→web onarıldı (+); karne zinciri çift kopuk (−) | P0-yol |
| Deneme yayınları | 50 | Üretim 11/11 gün ✓, yayın ~5/11; izleyici=1; feedback=0 | P1 |
| Dokümantasyon/Sözlük | 50 | Checklist bayat; 3 sözlük kaynağı; docs/ reorg yarım | P1-P2 |
| Eksik alanlar yükü | 55 | 12 kalem, 1'i yol-kesici (karne) | — |
| Büyüme potansiyeli | 75 | 5719 kayıtlık tarihi arşiv = keşfedilmemiş en değerli varlık | fırsat |
| **GENEL** | **~60/100** | Dün 54 → bugün 60: P0 onarımları gerçek; kanıt üretimi (karne+seri+kullanıcı) yeni darboğaz | |

**Gerekçe:** Skor artışının tamamı doğrulanabilir onarımlardan geliyor (flag=0, publish_now, taze web, sağlam DB, temiz compliance grep'i). 70+ bandına geçiş üç şeye bağlı: karne zincirinin dirilmesi, 10 günlük *yayın* serisi ve checklist'in gerçeğe eşitlenmesi.

---

## 11. P0–P3 AKSİYON LİSTESİ (derin audit yol haritası)

**P0 (bu hafta — yol kesiciler):**
1. **Karne teşhisi:** günlük scan neden signals_archive'a yazmıyor? (yazıcı mı kapalı, bilinçli mi?) + `resolve_open_signals.py` 5719 tarihi kayıt üzerinde tek seferlik koşu denemesi → by_grade ilk kez dolar.
2. **Yayın serisi disiplini:** "expired" durumunda admin'e YÜKSEK SESLE bildirim (sessiz pencere kaçırma sınıfı kapansın); seri sayacı LAUNCH_CHECKLIST'e günlük işlensin.

**P1 (gelecek hafta):**
3. Bütünlük-kapılı reader'ın kodda VAR/YOK tespiti; yoksa yazılması (dünkü P0-5 tamamlanmamış sayılır).
4. Contract-test varlık kontrolü + yoksa yazımı; eligible=2 seçicilik analizi (kasıt mı, filtre hatası mı).
5. E6 yedeğin zamanlanmış/ritüelleşmiş hale getirilmesi + DB bozulma kök neden notu (OneDrive/AV dışlama kuralı).
6. Zincire süre logu (scan başlangıç/bitiş, snapshot, publish) — performans yönetimi ölçüme geçsin.
7. LAUNCH_CHECKLIST gerçekleme: DoD#4 işaretle, M7 düzelt, retroaktif Hafta-1 kapısı, seri sayacı 0'dan başlat.

**P2 (lansman öncesi):**
8. EN snapshot→web kararı (tam dil ya da anahtar gizle) · docs/ops+archive taşınması + kök temizliği · glossary tek-kaynak kararı + Temmuz terimleri · bot_runner rol kararı · premium test · kırmızı-gün tatbikatı.

**P3 (lansman sonrası / fırsat):**
9. Tarihi arşivden track-record paketi (aws anlatısına da girer) · FinSense published ders hızlandırma · agents "karşı görüş" satırı · monitoring kararı (kur ya da resmen iptal et) · Alpaca planına sahip+tarih ata ya da PARKING_LOT'a taşı.

---

## EK — Derin audit'in sorması gereken 10 soru

1. Scan→archive yazımı ne zaman, hangi commit'le durdu? (git blame `signals_archive` yazan koda)
2. 14:04→14:59 snapshot boşluğunda ne çalışıyor — insan mı, LLM mi, bekleme mi?
3. `eligible_candidate_count=2` — filtre zinciri hangi adımda 1801'i 2'ye indiriyor ve bu istenen davranış mı?
4. Bütünlük kapısı (date/universe/tek-JSON/NUL) hangi dosyada? Yoksa dünkü P0-5 neden kapalı sayıldı?
5. finpilot.db'nin boş çekirdek tabloları (signals/scan_results) resmen emekli mi edilecek, şema temizlenecek mi?
6. broadcast "expired" mantığı: pencere kaç saat, kim karar verdi, admin bilgilendirmesi neden yok?
7. dictionary.json'u en son ne üretti; glossary.py ile diff'i ne?
8. academy_lessons.json neden 1 KB — export filtresi mi, üretim mi kısıtlı?
9. Testler bugün yeşil mi? (.coverage 23 Mayıs'tan) — CI yok, son tam süit koşusu ne zaman?
10. OneDrive/AV ile SQLite WAL etkileşimi — iki bozulmanın ortak paydası bu mu, dışlama kuralı yazıldı mı?

---
_Durum: AKTİF · Bu bir ön-tarama; bulgular derin audit'te kanıt zinciriyle kapatılmalı. Sonraki tam re-audit: 2026-09-21 (dünkü ritüel takvimine göre)._
