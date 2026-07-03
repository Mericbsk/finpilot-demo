# FinPilot — Tam Sistem Audit ve Sonraki Faz Tasarımı

**Tarih:** 2026-07-03 · **Supersedes:** `docs/audit-2026-06-12/` (delta üzerine inşa edildi) · **Kapsam:** 16 katman, kod + rapor + veri düzeyinde doğrulanmış
**Kanıt tabanı:** repo kodu (scanner/, core/, agents/, api/, web/), git geçmişi (19 Haz – 3 Tem), `FinPilot_Scanner_Backtest_Raporu.docx` (30 Haz), `FinPilot_Sinyal_Kalitesi_ve_Konviksiyon_Raporu.docx` (2 Tem), `profitcore_audit` (20 Haz), 12 Haziran tam-spektrum audit, `docs/HIBE_FON_DEGERLENDIRME.md` (Nisan).

> Varsayımlar açıkça `[VARSAYIM]` olarak işaretlendi. Bu bir sistem-tasarım denetimidir, yatırım tavsiyesi değildir.

---

## 1. YÖNETİCİ ÖZETİ

FinPilot, 12 Haziran audit'inden bu yana **sıçrama yaptı**: EODHD fundamentals + haber katalizörü, FINRA nokta-zamanlı short verisi, Alpha-v2 skor faktörleri, erken-yakalama tier merdiveni, konviksiyon tier sistemi (A/B/C), watchlist tier-başarı takibi ve 1812 sembollük tam-evren taraması devreye girdi. Scanner fazı **amacına ulaştı**: sistem artık sinyal üretmekle kalmıyor, ürettiğini ölçüyor.

Ama audit'in ana bulgusu şu: **sistemin artık bir "edge yok" problemi değil, bir "hangi ölçüme inanacağız" problemi var.** Üç ölçüm sistemi üç farklı hikâye anlatıyor:

| Ölçüm | Tarih | Sonuç | Hikâye |
|---|---|---|---|
| Scanner Backtest (signals_archive, 5070 sinyal) | 30 Haz | Skor OOS lift **0.99** (p=0.81), precision tavanı ~%32 | "Ham skorun edge'i yok" |
| Konviksiyon Raporu (6410 sinyal, 53 gün) | 2 Tem | Kompozit skor kalibre; elit kova **%73** (≥5%), top-3/gün %62 | "Seçici olursak isabet yüksek" |
| profitcore_audit (n=602 işlem) | 20 Haz | PF 1.028, beklenti +%0.1/işlem, p=0.705 | "Kâr olarak edge ≈ sıfır" |

Bu üçü çelişmiyor — **farklı şeyleri ölçüyorlar** (5 günde ≥%5 hareket yakalama ≠ maliyet sonrası kâr; 53 günlük pencere ≠ 8 aylık pencere; short/gap faktörleri yalnız son dönemde mevcut). Fakat tek bir kanonik doğruluk motoru olmadığı için, %74'lük precision rakamının "işlem edge'i" olarak okunması an meselesi. **Bu, sistemin şu anki 1 numaralı riski: sahte güven.**

**Net kararlar (özet):**
1. **P0 — Truth Engine:** Tek kanonik, maliyet-farkında, walk-forward, config-versiyonlu Edge Report. Diğer her şey buna tabi.
2. **P0 — Skor sözlüğü birleştirme:** `score` + `tier` (WATCH/SETUP/TRIGGER/CONFIRM) + `conviction_tier` (A/B/C) = üç ayrı dil. Kullanıcıya tek "Signal Grade" olarak birleştirilmeli.
3. **P1 — Decision Surface:** "Günün en iyi 3'ü" ürün yüzeyi (konviksiyon raporunun top-3 %62 bulgusu doğrudan ürünleşebilir).
4. **P1 — Catalyst Intelligence:** %32→%40+ precision tavanını kıracak eksik veri (RVOL geçmişi, borrow fee, IV, catalyst tagging) + shortlist-scope LLM açıklaması.
5. **Dondur:** DRL (research preview etiketiyle), dekoratif agent'lar (CEO/bull/bear), canlı execution.
6. **Hibe:** Anlatı "sinyal satıcısı" değil, **"dürüst-ölçüm metodolojili, açıklanabilir piyasa-istihbarat copilot'u"**. Sistemin en güçlü Ar-Ge hikâyesi zaten kurduğun doğrulama kültürü.

Ticari katman hâlâ ≈ 0 (waitlist endpoint'i var, JSON dosyasına yazıyor; bülten/Beehiiv entegrasyonu kodda yok). 12 Haziran planındaki V6 (bülten) hattı başlamamış. Teknik olgunluk ile dağıtım arasındaki makas **büyümeye devam ediyor** — bu hibe başvurusunda "traction" sorusunun hâlâ en zayıf cevabı.

---

## 2. FİNPİLOT'UN BUGÜNKÜ GERÇEK DURUMU

**Ne var (kod düzeyinde doğrulandı):**
- **Scanner:** 1812 sembol tam evren, batch=200, Alpaca bulk + retry + client reuse, aşama-bazlı zamanlama logları (1 Tem). Kapsam %12→%80+ (23 Haz fix'i).
- **Faktör seti:** squeeze (FINRA short), EDGAR catalyst, FRED makro rejim, lottery/overnight fade, vol-regime momentum, EODHD fundamentals + haber — hepsi env-flag'li ve `.env`'de **açık** durumda.
- **Erken yakalama:** `watch_tier.py` WATCH→SETUP→TRIGGER→CONFIRM merdiveni + triple-barrier etiketleme (`labeling.py`), 28/28 test.
- **Konviksiyon:** `compute_conviction` (A/B/C + kalibre olasılık), `evaluate.py`'a env-gated bağlı, skoru değiştirmiyor, etiketliyor (doğru tasarım).
- **Kapalı döngü:** signals_archive (5719 kayıt) → outcome reconciler → günlük kalibrasyon + haftalık retrain → Pazartesi Edge Report cron'u → watchlist tier-başarı panelleri (3 Tem). **Bu, sistemin ilk gerçek "ölç-öğren" döngüsü ve en değerli varlığı.**
- **Ops:** APScheduler 4 kova + 6 always-on job, watchdog sarmalayıcı, quality-gate (degraded-mode Redis flag'i), rate limiter, tracing.
- **Yüzey:** Next.js dashboard 15+ sayfa, FastAPI ~24 router, Telegram alert hattı, paper portfolio (Redis), auto-approve (p_win ≥ 0.65), academy router (Haz 24).

**Ne yok / doğrulanamadı:**
- Kullanıcı: 0 dış kullanıcı `[VARSAYIM — repo'da aksine kanıt yok]`. Bülten entegrasyonu yok. Landing/waitlist minimal.
- Kâr kanıtı: profitcore beklentisi +%0.1/işlem; maliyet sonrası ≈ negatif.
- Canlı hazırlık: kill-switch, max-loss politikası, broker soyutlaması eksik; `broker/` iskelet.
- Gözlemleme: Prometheus/Grafana kapalı, Sentry boş — 12 Haziran bulgusu **aynen duruyor**.
- DRL: en yeni model Mart; `wf_validation_report.txt` train reward'ı `-1.86e16` gibi bozuk değerlerle "ROBUST" damgalıyor — **ölçüm borusu sessizce kırık ve yanlış güven üretiyor** (bkz. Katman 6).

**12 Haziran P0'larının durumu:** Auth regresyonu ✅ kapandı (test yeşil, baseline güncel). Academy duplikasyonu ✅ (FinanceAcademy → archive, router açıldı). Skor/Edge Report ✅ cron'da. Landing/waitlist ⚠️ minimal endpoint var, dağıtım yok. **3.5 / 4 — teknik disiplin iyi işliyor; işlemeyen tek şey ticari adımlar.**

---

## 3. ANA PRENSİPLER AUDIT SONUCU (Katman 1: Ürün Amacı)

**A) Rol:** Sistemin var oluş gerekçesi. Tüm mimari kararların türediği yer.

**B) Şu anki durum:** FinPilot'un kimliği hâlâ **üç ruh arasında bölünmüş**:
1. *Agresif getiri makinesi* ("haftalık %10" hedefi — 23 Haziran raporu bunu kendi verinle çürüttü),
2. *Trading copilot / karar-destek* (konviksiyon tier'ları, watchlist, "günün en iyi 3'ü" — fiili geliştirme yönü),
3. *Eğitim + araştırma platformu* (Academy, FinSense, bülten vizyonu — planlarda var, üründe zayıf).

Temmuz commit'leri fiilen 2 numarayı seçmiş: tier başarı oranı takibi, konviksiyon rozetleri, kalibre olasılıklar. **Ama bu seçim hiçbir kanonik dokümanda yazılı değil.** README hâlâ "AI-powered recommendations + DRL" anlatıyor; hibe dokümanları hâlâ "19 DRL modeli" ile açılıyor.

**C) Güçlü yanlar:** "Önce ölç, sonra iddia et" kültürü yerleşmiş (edge-testi-geçmeden-merge-yok kuralı, dürüstlük notları raporlarda). Bu, çoğu retail-trading projesinde olmayan bir olgunluk. Çekirdek döngü artık gerçek: **tara → derecelendir → izle → sonucu ölç → yeniden kalibre et.**

**D) Zayıflıklar:** Tek cümlelik değer önerisi yok. "Her şeyi yapan sistem" riski gerçekleşmiş durumda: 15+ dashboard sayfası, 20+ agent, 7 LLM provider, DRL, Academy, Telegram, paper trading — ama 0 kullanıcı. Feature sprawl, odak eksikliğinin belirtisi değil sebebi.

**E) Akla gelmeyen kriter:** *Kimlik borcu* — sistem ne olduğuna karar vermedikçe her yeni modül üç vizyona birden hizmet etmeye çalışıyor ve üçünü de sulandırıyor. Hibe değerlendiricisi ve kullanıcı aynı karışıklığı görecek.

**F) Etki:** Bu katman düzelmeden UI, hibe anlatısı ve roadmap kararları rastgele kalır. **P0.**

**G) Karar: YENİDEN YAZ** (kod değil, tanım). Önerilen ideal tanım:

> **"FinPilot, ABD small/mid-cap evreninde büyük fiyat hareketlerini erken yakalayan; her sinyalini kalibre olasılık, konviksiyon derecesi ve gerekçeyle sunan; ve kendi isabetini kullanıcıya açık biçimde ölçen bir piyasa-istihbarat copilot'udur."**

Korunacak prensipler: dürüst ölçüm, env-gated deney disiplini, shortlist-scope LLM, açıklanabilirlik. Emekliye ayrılacak prensipler: "haftalık %10", "tam otomatik para makinesi", "DRL ana bileşendir".

**H) Eylem:** 7 gün — README + tek cümle değer önerisi yeniden yaz; `docs/VISION.md` (1 sayfa) oluştur, tüm roadmap'ler ona bağlansın. 30 gün — dashboard'u bu tanıma göre budama listesi. 90 gün — hibe dokümanları bu anlatıya taşınır.

---

## 4. BÖLÜM BÖLÜM TAM SİSTEM AUDIT

### Katman 2 — Sistem Mimarisi

**A) Rol:** ~25.000 satır Python (scanner+core+agents+llm) + Next.js web + FastAPI api. Katmanlar: data → scanner → score → core(pipeline/scheduler) → api → web.

**B) Durum:** Modüler monolit. 12 Haziran'daki tespitler büyük ölçüde geçerli; scheduler konsolidasyonu (9 job → 4 kova, S16-12) ve legacy rollback flag'i **iyi mühendislik örneği**. Registry `audit_registry()` ile kod↔metadata drift'ini test ediyor — nadir görülür bir öz-denetim deseni.

**C) Güçlü:** Sorumluluk ayrımı scanner içinde iyi (features/labeling/watch_tier/score_engine/evaluate ayrık ve test edilebilir). Env-flag disiplini + "ablation'sız merge yok" kuralı. Pre-commit/ruff/mypy kurulu.

**D) Zayıf:**
- **Tanrı dosyaları büyümeye devam ediyor:** `core/scheduler.py` 1379 satır (Haziran'da 1247), `scanner/data_fetcher.py` 1151, `scanner/evaluate.py` 690. `evaluate.py` fiilen ikinci bir orkestratör oldu — early tier, conviction, squeeze, catalyst, lottery hepsi orada birleşiyor.
- **Research code ↔ product code ayrımı yok:** kökte 15+ tek-seferlik analiz script'i (`score_lab_*`, `fetch_squeeze_and_analyze.py`, `signal_quality_lab.py`, `backtest_v2_extra.py`...). Ruff'tan hariç tutulmuşlar — yani kalite kapısının dışında yaşıyorlar. Bunlar `research/`'e taşınmalı ve çıktıları versiyonlanmalı.
- **Hidden coupling:** Alpaca entegrasyonu `data_fetcher` içinde, `broker/` soyutlaması bypass'lı (Haziran bulgusu, duruyor). Redis üç ayrı yerde ayrı ayrı bağlanıyor (quality_gate, paper_portfolio, calibration) — tek bağlantı modülü yok.
- **SQLite tek nokta:** scheduler + API + script'ler aynı `finpilot.db`'ye yazıyor; ölçekle "database is locked" garanti.

**E) Gizli kriter — config kombinatoriği:** 9+ `FINPILOT_ENABLE_*` flag'i var ve `.env`'de 7'si açık. **Backtest hangi flag kombinasyonuyla koştu? Canlı hangi kombinasyonla koşuyor?** Bu eşleşme hiçbir yerde kayıt altında değil. Flag'ler deney güvenliği için doğruydu; ama artık "hangi konfigürasyon valide edildi" sorusuna cevap veren bir **experiment/config manifest** gerekiyor (reproducibility eksikliği).

**F) Etki:** Truth Engine kurulacaksa config-versiyonlama onun ön şartı. **P1** (manifest kısmı P0'a bitişik).

**G) Karar: GÜÇLENDİR** (yeniden tasarlama yok — modül sınırları temelde doğru).

**H) Eylem:** 7g — `data/scan_config_manifest.json`: her scan çıktısına aktif flag seti + kod versiyonu (git sha) damgala. 30g — kök analiz script'lerini `research/labs/`'e taşı; `evaluate.py`'ı stage-pipeline'a böl. 90g — Redis/DB erişimini tek modüle indir; broker soyutlamasını ya tamamla ya sil.

### Katman 3 — Veri Katmanı

**A) Rol:** Alpaca (bulk bars, birincil) + yfinance (fallback) + EODHD (fundamentals, haber) + FINRA (short) + EDGAR (catalyst) + FRED (makro). Cache: price/intraday/edgar/finra dizinleri + Redis/TTL.

**B) Durum:** 12 Haziran'a göre **en çok gelişen katman**. Nokta-zamanlı short verisi toplama başladı — konviksiyon raporunun elit kovası buna dayanıyor.

**C) Güçlü:** Provider katmanlaması doğru kurgulanmış (ucuz bulk birincil, pahalı zenginleştirme shortlist'e). Retry-backoff + client reuse + rate limiter olgun. Catalyst cache'i scheduler ön-doldurmalı — sıcak yol SEC'e hiç gitmiyor (doğru desen).

**D) Zayıf / eksik veri haritası:**

| Veri | Durum | Precision tavanına etkisi | Öncelik |
|---|---|---|---|
| Nokta-zamanlı short interest geçmişi | Sadece ~53 gün | Elit kova (n=43-52) istatistiksel olarak ince | **P0 — biriktirmeye devam, tarihsel dolgu araştır** |
| RVOL (gerçek intraday hacim geçmişi) | Kısmî | Backtest raporunda "YOK" işaretli | **P0** |
| Borrow fee / utilization | Yok | Squeeze sinyalinin kalitesini belirler | P1 |
| Options volume / IV / IV-percentile | Yok | %40 hedefi için gerekli (rapor 6. bulgu) | P1 |
| Catalyst tagging (earnings tarihi, FDA, offering tipi) | Kısmî (8-K/Form4/S-1) | Elit sinyallerin "neden"i | P1 |
| Dolar-hacim likidite filtresi | Yok (yalnız penny filtresi) | Fill gerçekliği için şart | **P0** |
| Delisting/survivorship kontrolü | Belirsiz `[VARSAYIM]` | Backtest bias'ı | P2 — doğrula |

- **Data quality monitoring:** `agents/data_quality.py` var ama şema-drift/stale-data alarmı yüzeye çıkmıyor (Prometheus kapalı olduğu için karanlıkta).
- **Vendor lock-in:** EODHD+Alpaca kombinasyonu maliyet-etkin; ama ikisi de tek API anahtarına bağlı, anahtar rotasyon/kota alarmı yok.
- **Veri lineage:** signals_archive kayıtları hangi provider/flag setiyle üretildi — damgalanmıyor (Katman 2 manifest bunu da çözer).

**E) Gizli kriter:** İki yoğun veri kümesi (Eyl-Eki 2025, Mar 2026) arasındaki **rejim farkı** (baz oran %10.8 → %20.7) tüm lift hesaplarını dönem-duyarlı yapıyor. Veri toplama sürekliliği (Kas-Ara boşluğu gibi) bir daha kesilirse walk-forward yine sakatlanır. Arşivleme job'unun kesintisizliği izlenmeli — bu bir **silent failure** adayı.

**F) Etki:** Precision tavanı veriye bağlı; scanner değil veri artık kısıt. **P0.**

**G) Karar: GÜÇLENDİR** (yeni provider ekleme değil; mevcut akışın sürekliliği + 3 eksik alan).

**H) Eylem:** 7g — dolar-hacim filtresi + arşiv-job süreklilik alarmı (basit: "son 24 saatte 0 kayıt → Telegram"). 30g — RVOL geçmişi biriktirme + borrow-fee kaynak araştırması (iborrowdesk/Fintel ücretsiz kademe). 90g — options/IV tek sembol-grubu pilotu; lineage damgası tüm arşiv kayıtlarında.

### Katman 4 — Scanner Katmanı

**A) Rol:** İlk büyük faz; evren taraması + faktör hesaplama + shortlist üretimi.

**B) Durum:** **Olgun.** 1812 sembol, ~%80+ kapsama, aşama zamanlama logları, 620s üst sınır. 23 Haziran performans denetimindeki bulguların çoğu kapatılmış (batch, retry, timing).

**C) Güçlü:** Fazlar (1-6) literatür referanslı (Bali-Cakici-Whitelaw lottery etkisi vb.) ve tek tek env-gated. Early-tier merdiveni "erken yakala, teyitle yükselt" mantığıyla alert kalitesini yapısal olarak çözüyor.

**D) Zayıf:** Soğuk-cache ilk tarama hâlâ yavaş `[VARSAYIM — timing loglarının trendi henüz raporlanmıyor]`; yfinance fallback'i hâlâ seri ve 4 req/s. GIL-bağımlı compute (pandas faktörleri) process-paralel değil. 620s timeout bir çözüm değil, semptom yönetimi.

**E) Gizli kriter:** Scanner'ın çıktısı üç ayrı sözlükte konuşuyor (score / early tier / conviction) — bkz. Katman 5. Ayrıca tarama sonuçlarının gün-içi tekrarlanabilirliği (aynı gün iki tarama aynı listeyi verir mi?) test edilmiyor — cache TTL'lere bağlı **nondeterminizm** ürün güveni için risk.

**F) Etki:** Scanner artık darboğaz değil. **P2** (bakım modu).

**G) Karar: KORU** — yeni faktör eklemeyi dondur, mevcut 6 fazın ablation sonuçları netleşene kadar.

**H) Eylem:** 7g — timing loglarından haftalık süre-trend raporu. 30g — determinizm testi (aynı input → aynı shortlist). 90g — compute'u process-pool'a taşıma yalnızca ölçüm gerektirirse.

### Katman 5 — Skorlama / Signal Engine

**A) Rol:** `score_engine.py` (kompozit, MAX 16.5) + `finpilot_score.py` (legacy shim) + `watch_tier.py` (erken merdiven) + `features.compute_conviction` (A/B/C).

**B) Durum:** Kompozit skor **kalibre** (decile'lar monoton: %8.9 → %58.7) — bu, Haziran'daki "skor ters ayrıştırıyor (decile_lift 0.728)" bulgusundan dramatik bir iyileşme ve Alpha-v2 + yeni faktörlerin işe yaradığının kanıtı. Konviksiyon katmanları AND-mantığıyla isabeti %49→%74'e taşıyor.

**C) Güçlü:** Skor artık olasılık gibi okunabiliyor (kalibrasyon). Konviksiyon tier'ı skoru DEĞİŞTİRMİYOR, etiketliyor — temiz ayrım. Ağırlık değişiklikleri commit mesajlarında gerekçeli.

**D) Zayıf:**
- **Üç sözlük problemi (bu katmanın P0'ı):** Kullanıcı aynı satırda `score=14.2`, `tier=TRIGGER`, `conviction_tier=B`, `conviction_prob=0.61` görüyor. Hangisi karar? Ranking engine (sıralama) ile threshold engine (eşik/etiket) ayrışmalı, kullanıcıya **tek Grade** (örn. A+/A/B/C + olasılık) sunulmalı.
- Confidence vs probability ayrımı yarı-var: `conviction_prob` kalibre ama n=43'lük kovalarda güven aralığı gösterilmiyor. %74 ± kaç?
- Ağırlıkların bir kısmı hâlâ el-ayarı (`_SQUEEZE_WEIGHT=1.5`, `_LOTTERY_WEIGHT=2.0`) — ablation'la doğrulanması commit kültüründe var ama sonuçlar tek dosyada toplanmıyor.
- Rejim farkındalığı kısmî: FRED makro rejimi faktör olarak var; ama tier eşikleri rejime göre uyarlanmıyor (backtest raporu 4. bulgu: Range rejimi Up/Trend'i geçiyor — bu bilgi henüz skora geri beslenmedi).

**E) Gizli kriter — hedef değişkeni tanımı:** "≥%5 hareket" **yön ve maliyet içermiyor**. 5 günde ±%5 oynayan bir hisseyi yakalamak ile ondan para kazanmak arasında spread/slippage/giriş zamanlaması var. Skor "hareket dedektörü" olarak kalibre; "kâr dedektörü" olarak kalibre DEĞİL (profitcore PF 1.028 bunu söylüyor). Bu ayrım her raporda ve UI'da açıkça yazılmalı — yoksa sahte doğruluk.

**F) Etki:** Decision Surface ve hibe anlatısı bu katmanın netliğine bağlı. **P0.**

**G) Karar: GÜÇLENDİR + BASİTLEŞTİR** (tek Grade; shim'leri sil — Haziran kararıydı, hâlâ duruyor).

**H) Eylem:** 7g — UI'da tek Grade gösterimi tasarla; `finpilot_score.py` shim'ini kaldır. 30g — Grade = f(kalibre olasılık, konviksiyon faktör sayısı, rejim) tek fonksiyonda; güven aralığı (Wilson) ekle. 90g — rejim-uyarlanabilir eşikler (Range/Trend ayrı tier eşiği) ablation ile.

### Katman 6 — Backtest / Validation (→ TRUTH ENGINE)

**A) Rol:** signals_archive + outcome_reconciler + calibration + edge_report cron'u + triple-barrier labeling + iki büyük backtest raporu.

**B) Durum:** Parçalar var ve tek tek kaliteli; **bütün yok.** Sistemin en kritik açığı burada.

**C) Güçlü:** Raporlardaki dürüstlük disiplini örnek düzeyde ("bu özellikler arşivde YOK ve test edilemedi", "umut verici, kesin kanıtlanmamış", scipy yoksa z-testi ile devam). Triple-barrier + Pazartesi otomatik Edge Report zinciri (retrain → resolve → edge) doğru sıralanmış. IS/OOS ayrımı yapılıyor.

**D) Zayıf:**
- **Kanonik doğruluk tanımı yok:** ≥%5 hareket (backtest raporu) vs ≥%5/≥%10 precision (konviksiyon) vs PF/beklenti (profitcore) vs triple-barrier sonucu — dört ayrı "başarı" tanımı. Hepsi meşru ama hiyerarşi tanımsız. Önerilen hiyerarşi: (1) maliyet-sonrası beklenti/işlem [nihai], (2) kalibre olasılık isabeti [ara], (3) hareket-yakalama lift'i [ham].
- **Maliyet/slippage/fill hiçbir hedefte yok.** `slippage_tracker.py` core'da mevcut ama backtest'lere bağlı değil. Small-cap + gap açılışlarında fill gerçekliği sonucu %20-40 değiştirebilir `[VARSAYIM — ölçülmeli]`.
- **Elit kova n'leri küçük** (43-52) ve tek rejim döneminde yoğun. Konviksiyon raporu 53 günlük — mevsimsellik/rejim genellemesi yapılamaz. Rapor bunu söylüyor; ürün yüzeyi (badge'ler) söylemiyor.
- **Walk-forward konviksiyon kombinasyonları için hiç yapılmadı** (backtest raporu bunu ham skor için yaptı).
- **DRL doğrulama borusu kırık:** `wf_validation_report.txt` train reward `-1.86e16` gösterip "✓ ROBUST" damgalıyor. Bu, sistemin kendi içinde ürettiği **canlı bir sahte-güven örneği** — sayı üreten ama anlam üretmeyen doğrulama. DRL'yi dondurma kararının kanıtı olarak da kullanılabilir.

**E) Gizli kriter — label leakage ve as-of doğruluğu:** Short/fundamental verisi zenginleştirmesi arşive sonradan mı yazılıyor, sinyal anında mı? "Nokta-zamanlı" iddiası konviksiyon raporunda var (iyi); ama arşiv şemasında `as_of` damgası zorunlu alan değil `[VARSAYIM — şema doğrulanmalı]`. Sonradan-yazma bir kez bile karışırsa tüm elit kova şüpheli hale gelir.

**F) Etki:** Bu katman düzelmeden hiçbir üst-katman iddiası (ürün, hibe, canlı) savunulamaz. **P0 — sistemin bir numaralı önceliği.**

**G) Karar: YENİDEN TASARLA** (birleştirerek): `truth/` modülü — labeling + calibration + edge_report + slippage + config-manifest tek çatı, tek haftalık rapor, tek metrik hiyerarşisi.

**H) Eylem:** 7g — Edge Report'a maliyet-sonrası beklenti sütunu + config-manifest damgası ekle; as-of alanını şemada zorunlu yap. 30g — konviksiyon tier'ları için walk-forward (aylık pencere); Wilson güven aralıkları; DRL wf raporunu düzelt veya emekliye ayır. 90g — "truth/" birleşik modül; 12 haftalık kesintisiz Edge Report serisi = hibe/yatırımcı kanıt paketi.

### Katman 7 — Alert / Watchlist / Decision Support

**A) Rol:** watchlist router (+servis DB'si), Telegram alerts, history sayfası, tier/conviction performans panelleri (3 Tem).

**B) Durum:** 12 Haziran'dan bu yana ikinci en çok gelişen katman. Sinyal→watchlist→sonuç→başarı-oranı zinciri UI'da görünür hale geldi.

**C) Güçlü:** Tier/conviction başarı panelleri = kullanıcıya dürüst karne. Konviksiyon raporundaki "ATMAK yerine ETİKETLE + günlük tavan" kararı alert-fatigue'i tasarımla çözüyor. Quality-gate degraded modda BUY alert'lerini bastırıyor — güvenli varsayılan.

**D) Zayıf:**
- **Günlük tavan (Tier A hepsi + B'den en iyi 5) raporda önerildi ama alert hattında zorlandığı doğrulanamadı** `[VARSAYIM — kod referansı bulunamadı]`. 121 sinyal/gün üretimi sürerken tavan yoksa fatigue devam eder.
- "Bugün neden bunu izlemeliyim?" cevabı kısmî: rozetler var (squeeze/catalyst), tek-paragraf gerekçe yok. LLM'in doğru yeri tam burası (shortlist-scope).
- Triage/urgency yok: Tier A sinyali sabah 9'da mı geldi 15:45'te mi — aciliyet farkı alert'e yansımıyor.
- Telegram tek kanal, fallback/teslimat ölçümü yok (Haziran bulgusu duruyor).
- watchlist.py router şişmeye devam ediyor (1019 → +55 satır).

**E) Gizli kriter:** Watchlist başarı panelleri **survivorship'e açık** — kullanıcı yalnız eklediklerini görüyor; eklemediği Tier A'ların sonucu gösterilmezse "sistemin karnesi" değil "benim seçimlerimin karnesi" olur. İkisi ayrı gösterilmeli.

**F) Etki:** Bu katman, scanner çıktısını ürün yapan yer. **P1 (en yüksek ürün ROI'si).**

**G) Karar: GÜÇLENDİR** — "Günün En İyi 3'ü" sabah brifi bu katmanın çatısı olsun (top-3 %62 bulgusu doğrudan ürün).

**H) Eylem:** 7g — günlük tavanı alert hattında zorla; sistem-geneli tier karnesi (watchlist'ten bağımsız). 30g — sabah brifi sayfası + Telegram özeti: Top-3 + Grade + 2 cümle gerekçe. 90g — urgency skoru + çok-adımlı alert (WATCH sessiz, TRIGGER bildirir, CONFIRM çaldırır).

### Katman 8 — Agent Yapısı ve Otomasyon

**A) Rol:** 23 agent dosyası, registry (6 katman, statü: active/advisory/planned), scheduler'a bağlı ana döngü.

**B) Durum:** İki sınıf net ayrışıyor: **iş yapan agent'lar** (scanner_agent, data_quality, alert_agent, backtest_agent, outcome/performance izleme) ve **konsept/dekoratif agent'lar** (ceo, bull/bear researcher, social_intelligence, strategy_optimizer — LLM rol-sarmalayıcıları).

**C) Güçlü:** `audit_registry()` kod↔metadata drift denetimi. Watchdog + compose-jobs deseni. Statü etiketleri (advisory/planned) dürüst.

**D) Zayıf:** Dekoratif agent'lar bakım maliyeti + LLM maliyeti üretiyor, karar zincirine ölçülmüş katkıları yok (hiçbirinin çıktısı outcome ile ilişkilendirilmiyor). CEO haftalık raporu kim okuyor? (0 kullanıcı → sen). Golden-set yok: LLM agent çıktılarının kalite regresyonu yakalanamaz. Human-in-the-loop sınırı belirsiz: auto-approve (p_win≥0.65) yarı-otonom karar veriyor ama bunun denetim izi (hangi approve neye yol açtı) yüzeyde değil.

**E) Gizli kriter:** Agent'lar **hibe anlatısında güçlü görünme aracı** olabilir ("multi-agent AI system") ama teknik DD'de tam tersi etki yapar: değerlendirici 23 agent'tan 15'inin prompt-sarmalayıcı olduğunu görürse bütün iddia zayıflar. Az ama ölçülmüş agent daha savunulabilir.

**F) Etki:** P2 (sistemi bozmuyor ama dikkat dağıtıyor + maliyet).

**G) Karar: BASİTLEŞTİR** — pipeline agent'ları KORU; dekoratifleri `advisory-frozen` statüsüne çek (kod dursun, cron'dan çık, LLM çağrısı yapmasın).

**H) Eylem:** 7g — registry'de frozen statüsü + cron'dan çıkarma. 30g — kalan her agent için "çıktısı hangi karara girer" satırı registry'ye. 90g — alert_agent + data_quality için golden-set testleri.

### Katman 9 — AI / LLM Katmanı

**A) Rol:** 7 provider (Claude/Groq/Gemini/Ollama/FinBERT/mock) + router; agent'ların metin üretimi; 29 Haziran yerel-AI planı (uygulanmadı).

**B) Durum:** Altyapı hazır, kullanım stratejisi dağınık. Yerel-AI planındaki ilkeler doğru (LLM sıcak döngüde asla; shortlist-scope; JSON yapılı çıktı; enjeksiyon deseni) — ama plan raftadır.

**C) Güçlü:** Router + provider soyutlaması temiz; headroom compression var; FinBERT gibi görev-özel model seçeneği akıllıca.

**D) Zayıf:** LLM'in değer kattığı yer (sinyal gerekçesi, sabah brifi, haber-catalyst özeti) henüz üründe değil; değer katmadığı yer (bull/bear tartışması, CEO raporu) cron'da. Prompt governance yok: promptlar kodda gömülü, versiyonsuz. Hallucination guardrail'i yok: LLM'in ürettiği gerekçe, faktör verisiyle çelişirse yakalanmıyor (basit kural: gerekçe yalnız mevcut faktör alanlarından cümle kurabilir — template-constrained generation).
- Maliyet/latency ölçümü panelde yok (Haziran bulgusu duruyor).

**E) Gizli kriter:** Yerel LLM **hibe için Ar-Ge puanı** (on-device AI, veri egemenliği, GDPR) + **maliyet sıfırlama** ikilisini aynı anda sağlıyor — ama CPU'da 7B yavaş. Doğru çerçeve: küçük model (3B) triage + bulut model derin analiz; "yerel-öncelikli hibrit" anlatısı.

**F) Etki:** P1 — Decision Surface'in açıklama katmanı buna bağlı.

**G) Karar: GÜÇLENDİR (dar kapsamla)** — tek kullanım senaryosuyla başla: Top-3 sinyal gerekçesi.

**H) Eylem:** 7g — `ollama list` envanteri + tek prompt: sinyal→2 cümle gerekçe (JSON, faktör-kısıtlı). 30g — sabah brifi üretimi cron'a; prompt'lar `llm/prompts/` altında versiyonlu. 90g — golden-set + gerekçe-faktör tutarlılık denetimi.

### Katman 10 — Execution / Paper Trading / Live Readiness

**A) Rol:** paper_portfolio (Redis, aç/kapa/equity), position_sizer + risk_engine (scanner/), slippage_tracker, auto-approve job, broker/ iskeleti.

**B) Durum:** Paper katmanı çalışıyor; canlı hazırlık **yok ve şimdilik olmamalı**.

**C) Güçlü:** Paper portfolio sade ve yeterli. Auto-approve eşiği (p_win≥0.65) kalibre olasılığa bağlanmış — mantık doğru. Quality-gate degraded modda sinyal bastırıyor.

**D) Zayıf — dürüst canlı-hazırlık skoru: 3/10.** Kill switch yok. Max-loss/gün politikası kodda yok. Broker soyutlaması iskelet. Slippage tracker'ın verisi karara bağlanmıyor. Auto-approve'un denetim izi zayıf. Edge maliyet-sonrası kanıtlanmadı (Katman 6) — **canlıya çıkma tartışması matematiksel olarak erken.**

**E) Gizli kriter — regülasyon:** Otomatik emir ileten bir sistem Avusturya/AB'de (MiFID II) bambaşka bir yükümlülük sınıfına girer. "Karar-destek + paper simülasyon" konumu hibe ve hukuk açısından güvenli bölge; "auto-trading" kelimesi başvuru dosyasında **hiç geçmemeli**.

**F) Etki:** P2 (şu an bilinçli olarak durdurulmuş olması gereken katman).

**G) Karar: GEÇİCİ OLARAK DURDUR** (canlı yolu); paper'ı KORU ve Decision Surface'e bağla (sanal "Top-3'ü otomatik paper-al" modu — truth engine için ekstra veri üretir).

**H) Eylem:** 7g — auto-approve denetim log'u (kim/ne/niçin). 30g — "paper-auto-top3" modu: her gün Top-3'ü sanal al, 5 gün tut, sonuçları Edge Report'a besle. 90g — canlı-hazırlık kontrol listesi dokümanı (kill switch, max-loss, broker) — uygulaması edge kanıtına şartlı.

### Katman 11 — UI / Desktop / Workflow

**A) Rol:** Next.js dashboard (15+ sayfa: scanner, watchlist, history, portfolio, calibration, drl, ai-lab, finsense, academy...), landing (page.tsx), demo modu; 23 Haziran tek-tık masaüstü planı (uygulanmadı).

**B) Durum:** Research-aracı görünümü: her modülün sayfası var, kullanıcı yolculuğu yok.

**C) Güçlü:** TierBadge/ConvictionBadge + performans panelleri gerçek karar-destek elemanları. Demo modu var. Statik export (`web/out`) üretiliyor — paketlemeye hazır.

**D) Zayıf:** İlk açılışta kullanıcı ne görmeli sorusunun cevabı yok — sabah brifi ("bugün ne izlemeliyim + dünün karnesi") giriş ekranı olmalı. 15+ sayfa cognitive load; drl/ai-lab/autonomy sayfaları 0-kullanıcı ürününde vitrin karmaşası. Docker-bağımlı başlatma tek-tık hedefini bloke ediyor (23 Haz raporu geçerli). Time-to-value: yeni kullanıcının ilk "aha"sı kaç dakika? Ölçülmüyor; muhtemelen >30 dk `[VARSAYIM]`.

**E) Gizli kriter:** Masaüstü-first doğru (hedef kullanıcı aktif trader, çoklu ekran); mobil yalnız alert-görüntüleme olarak gerekir (Telegram bunu zaten karşılıyor). Tauri > Electron (boyut/bellek) — plandaki tercih doğru.

**F) Etki:** P1 — ilk dış kullanıcı testi bu katmandan geçiyor.

**G) Karar: BASİTLEŞTİR + GÜÇLENDİR** — sayfa sayısını azalt, sabah-brifi merkezli akış kur.

**H) Eylem:** 7g — navigasyonu 5 ana sayfaya indir (Brif, Scanner, Watchlist, Karne, Ayarlar); drl/ai-lab'ı "Labs" altına gizle. 30g — sabah brifi ana ekran. 90g — Tauri paketleme pilotu (production build + sidecar).

### Katman 12 — Performance / Teknik Borç

**Durum ve karar (özet):** Scanner performansı kapatıldı (Katman 4). Kalan borçlar: tanrı dosyaları (scheduler 1379, data_fetcher 1151, watchlist router 1074, auth/database 1410), 6 requirements dosyası, coverage bilinmiyor/CI gate yok, kök research script'leri lint dışı, mkdocs site drift'i. Hiçbiri ürünü bugün durdurmuyor; ama **truth/config manifest işleri bu dosyalara dokunacak** — refactor'u o işlerle birlikte yap, ayrı "temizlik sprinti" açma. **Karar: GÜÇLENDİR (fırsatçı refactor). P2.** 30g — coverage ölçümü + CI gate (%60 taban); requirements'ı pyproject'e tekille. 90g — scheduler'ı job-registry desenine böl.

### Katman 13 — Güvenlik / Güvenilirlik / Hata Toleransı

**Durum:** Auth P0 kapandı (test yeşil), `.env` git'e girmemiş (doğrulandı), pre-existing failures 3'e inmiş (514 pass) — ciddi iyileşme.
**Kalan riskler:** (1) SQLite eşzamanlılığı — scheduler+API+script aynı DB; kilitlenme riski büyüyor; WAL modu + tek-yazar deseni veya Postgres kararı 90 güne alınmalı. (2) Sessiz job ölümü — watchdog var ama job-run geçmişi hiçbir yüzeyde yok (Haziran bulgusu **duruyor**; sabit öneri: dashboard'a Sistem Sağlığı kartı). (3) Telegram tek-kanal, teslimat ölçümsüz. (4) API anahtarları tek `.env`'de, rotasyon/kota alarmı yok. (5) Sentry boş — hata toplama kapalı.
**Karar: GÜÇLENDİR. P1.** 7g — Sistem Sağlığı kartı (job-run tablosu kendi DB'sinden, Grafana'sız). 30g — SQLite WAL + yazar tekilleştirme; Sentry aç. 90g — Postgres go/no-go kararı.

### Katman 14 — Ürünleşme / Monetizasyon / Kullanıcı Değeri

**Durum:** 12 Haziran'ın V6→V7→V10 zinciri **hiç başlamadı** (Beehiiv/bülten kodu yok, waitlist JSON-dosya endpoint'i minimal). Teknik faz (scanner) bilinçli önceliklendirildi — anlaşılır; ama 90 günlük planın ticari yarısı artık 3 hafta geride.
**Kritik gerçek:** Konviksiyon raporu ilk kez **paketlenebilir bir ürün nesnesi** üretti: "Günün En İyi 3'ü, kalibre olasılık + gerekçeyle, geçmiş karnesi açık". Bu, bülten (V6) ve copilot (V7) vizyonlarının kesişimi ve mevcut kodla 2-4 hafta mesafede.
**Gizli kriter:** Track-record sayfası (sistem-geneli tier karnesi, Katman 7) aynı zamanda en güçlü pazarlama varlığı — "bize inanmayın, karneye bakın". Az sayıda rakip bunu dürüstçe yapıyor.
**Karar: GÜÇLENDİR — tek ürün nesnesi (Top-3 brifi) + tek kanal (bülten veya Telegram public) seç, gerisini erteleme listesine yaz. P1.** 30g — Top-3 brifi otomatik üretim + 10 tanıdık beta. 90g — public karne sayfası + waitlist'ten beta daveti.

### Katman 15 — Avusturya Hibe / Ar-Ge Uygunluğu

Ayrıntı Bölüm 8'de; katman kararı: **YENİDEN TASARLA (anlatıyı).** Nisan dosyası ("19 DRL modeli, 493 test, Sharpe 0.057, €750K aws") bugünkü sistemle **çelişiyor** ve teknik DD'de zarar verir: DRL modelleri bayat + doğrulama borusu kırık, Sharpe 0.057 zayıf bir kanıt, test sayısı değişti. Buna karşılık bugünkü sistemin gerçek Ar-Ge değeri Nisan'da yoktu: kalibre olasılık motoru, triple-barrier truth zinciri, nokta-zamanlı veri disiplini, dürüst Edge Report kültürü. Hibe dosyası bu yeni omurga üzerine yeniden yazılmalı.

### Katman 16 — Sonraki Faz ve Yol Haritası

Bölüm 7 ve 11'de birleştirildi (aşağıda).

---

## 5. EN KRİTİK 10 PROBLEM

1. **Sahte-güven riski / metrik hiyerarşisi yok (P0):** %74 precision "hareket yakalama"dır, kâr değildir; profitcore PF 1.028. Tek kanonik, maliyet-sonrası doğruluk tanımı şart.
2. **Config-kombinasyon izlenebilirliği yok (P0):** 9+ env flag; hangi backtest hangi flag setiyle koştu kayıtsız. Reproducibility kırık.
3. **Üç skor sözlüğü (P0):** score / early-tier / conviction aynı anda; kullanıcı ve gelecekteki sen için karar dili belirsiz.
4. **Elit kova istatistiği ince (P0):** n=43-52, 53 gün, tek rejim. Ürün rozetleri güven aralığı göstermiyor.
5. **Maliyet/likidite backtest'te yok (P0):** dolar-hacim filtresi ve slippage hiçbir doğruluk hesabına girmiyor; small-cap'te sonuç değiştirir.
6. **DRL doğrulama borusu kırık (P1):** `-1.86e16` reward → "ROBUST". Bayat Mart modelleri hâlâ üründe; hibe DD'sinde en savunmasız nokta.
7. **Ticari katman 0 (P1):** bülten/beta/track-record başlamadı; teknik-ticari makas açılıyor; hibe "traction" sorusu cevapsız.
8. **Job-run görünürlüğü yok (P1):** watchdog var, geçmiş yüzeyde yok; haftalık kalibrasyon sessiz ölebilir. Prometheus/Sentry kapalı.
9. **SQLite çok-yazarlı tek nokta (P1):** scheduler+API+script'ler; ölçekle kilitlenme garantili.
10. **Hibe dosyası bayat ve çelişkili (P1):** Nisan anlatısı (DRL-merkezli) bugünkü sistemin en zayıf parçasını vitrine koyuyor.

## 6. EN KRİTİK 10 GÜÇLÜ TARAF

1. **Kapalı ölç-öğren döngüsü:** sinyal → outcome → kalibrasyon → edge report → UI karnesi. Çoğu retail-fintech'te yok.
2. **Kalibre skor:** decile'lar monoton (%8.9→%58.7); skor olasılık olarak okunabiliyor — Haziran'daki negatif-edge bulgusundan gerçek dönüş.
3. **Konviksiyon AND-katmanları:** %49→%63→%72→%74 merdiveni; "az ama doğru" ürün tezinin ampirik temeli.
4. **Dürüst raporlama kültürü:** eksik veriyi işaretleme, IS/OOS ayrımı, "kanıtlanmamış" etiketi — hibe ve DD'de en büyük koz.
5. **Nokta-zamanlı veri disiplini** (FINRA short, EDGAR cache ön-doldurma, as-of bilinci) — sektörde nadir titizlik.
6. **Env-gated deney disiplini** + "ablation'sız merge yok" kuralı — araştırma güvenliği kurumsallaşmış.
7. **Ops olgunluğu:** watchdog'lu scheduler kovaları, quality-gate degraded modu, rate limiter, retry-backoff.
8. **Scanner ölçeği çözüldü:** 1812 sembol, %80+ kapsama, timing logları — bu faz gerçekten bitti.
9. **Registry öz-denetimi:** `audit_registry()` kod↔metadata drift testi — mimari hijyen refleksi.
10. **Literatür-bağlı faktör tasarımı** (lottery/MAX etkisi, PEAD, squeeze mekaniği) — "deep-tech" iddiasına gerçek malzeme.

## 7. SCANNER SONRASI EN MANTIKLI 3 GELİŞTİRME ALANI

Sekiz aday değerlendirildi. Sıralama ve gerekçe:

| # | Alan | Neden şimdi | Çarpan |
|---|---|---|---|
| **1** | **Truth Engine** (validation birleştirme: maliyet-sonrası metrik, walk-forward konviksiyon, config manifest, güven aralıkları) | Diğer her kararın (ürün, hibe, canlı) doğruluk zemini; parçalar zaten var, birleştirme işi | Tüm katmanları güçlendirir; sahte-güven riskini kapatır |
| **2** | **Decision Surface** (Top-3 sabah brifi + günlük tavan zorlaması + sistem-geneli karne + LLM gerekçesi) | Konviksiyon raporu ürün nesnesini hazır verdi (top-3 %62); watchlist panelleri altyapıyı kurdu; ilk dış kullanıcı buradan gelir | Scanner'ı ürüne çevirir; hibe "prototype+traction" kanıtı üretir |
| **3** | **Catalyst & Data Intelligence** (dolar-hacim, RVOL geçmişi, borrow fee, catalyst tagging, IV pilotu) | Precision tavanı (%32 ham / %60-74 elit) artık veri-kısıtlı; raporun kendi 6. bulgusu | Elit kovayı büyütür (n↑, güven↑); Ar-Ge anlatısını besler |

**Neden bu sıra:** 2, 1'siz olursa güvenilmez sayılar satarsın; 3, 1'siz olursa yeni verinin katkısını ölçemezsin. 1 → 2 → 3 tek mantıklı topoloji; pratikte 1 ve 2 paralel yürüyebilir (2'nin karne bileşeni 1'in çıktısını tüketir).

**Henüz erken olanlar:** Risk engine genişletme ve portfolio construction (edge kanıtı önce), canlı execution (Katman 10 — matematiksel olarak erken), tam yerel-LLM copilot (dar gerekçe-üretimiyle başla), DRL yenileme (research preview'a çekildi).

## 8. AVUSTURYA HİBE ODAĞI

**Pozisyonlama cümlesi (önerilen):**
> *"FinPilot ist ein erklärbarer KI-Copilot für Marktanalyse, der jede Signalbewertung mit kalibrierten Wahrscheinlichkeiten, Konfidenzstufen und einer offenen Erfolgsbilanz belegt — Entscheidungsunterstützung, kein Auto-Trading."*
> (Açıklanabilir AI + kalibre olasılık + açık karne; karar-desteği, auto-trading değil.)

**Şimdi odaklanılacak ilk 5 konu (başvuru gücü sırasıyla):**
1. **12 haftalık kesintisiz Edge Report serisi** — "çalışan doğrulama metodolojisi" kanıtı; Ar-Ge iddiasının omurgası (Truth Engine çıktısı).
2. **Kalibrasyon + uncertainty quantification'ı Ar-Ge dili ile paketleme** — "calibrated probabilistic signal grading for retail decision support" — FFG/aws'nin aradığı "teknik yenilik + ölçülebilirlik" formatı.
3. **Yerel-öncelikli hibrit LLM** (Ollama triage + yapılandırılmış gerekçe) — veri egemenliği/GDPR + on-device AI = Avrupa fon anlatısına birebir oturur.
4. **Küçük ama gerçek beta traction** (10-20 kullanıcı + public karne sayfası) — değerlendiricinin ilk sorusu; Top-3 brifi bunu üretir.
5. **Akademik temas** (WU/TU Wien — calibration/forecast evaluation grubu; tek danışman mektubu yeter) — konsorsiyum puanındaki 4/10'u yükseltir.

**Başvuru gücünü düşüren ilk 5 zayıflık:**
1. Nisan dosyasındaki DRL-merkezli iddialar (bayat modeller + kırık wf raporu) — DD'de çökebilir; anlatıdan çıkar veya "research track" olarak izole et.
2. 0 kullanıcı / 0 gelir — traction bölümü boş.
3. Solo founder + akademik ortak yok.
4. Şirket tüzel kişiliği belirsiz (GmbH kararı verilmemiş).
5. "Trading sinyali satışı" olarak okunma riski — regülasyon kaygısı tetikler; karar-destek/eğitim çerçevesi tutarlı kullanılmalı (Academy burada stratejik değer kazanır: "financial literacy" toplumsal etki puanı).

**Program uyumu (Nisan dosyasındaki liste hâlâ geçerli; güncel teyit gerekli `[VARSAYIM — programlar/koşullar 2026'da değişmiş olabilir, başvuru öncesi web'den teyit edilmeli]`):** Wirtschaftsagentur Wien Innovation, aws Preseed/Seedfinancing (Deep Tech çerçevesi), FFG Basisprogramm/Kleinprojekt. Yeni anlatı (açıklanabilir-AI + doğrulama metodolojisi) özellikle FFG'nin "teknik risk + sistematik çözüm" kriterine Nisan anlatısından daha iyi oturur.

## 9. GENEL TASARIM DEĞİŞİKLİK ÖNERİLERİ

**Teşhis:** Fazla parçalı (23 agent, 15+ sayfa, 6 roadmap, 4 doğruluk tanımı), research-heavy (kök script'ler, DRL, ai-lab) ve çekirdek loop'u henüz tek çatı altında ifade etmiyor.

**Yeni tasarım ilkeleri:**
1. Tek doğruluk kaynağı: her sayı Truth Engine'den gelir; UI/rapor/hibe aynı sayıyı gösterir.
2. Tek karar dili: kullanıcıya tek Grade + olasılık + gerekçe.
3. Research ↔ product fiziksel ayrımı: `research/` altında yaşar, ürün koduna PR ile girer (edge testi kanıtıyla).
4. Az modül, keskin sınır — hedef 5 çekirdek modül:

| Modül | İçerik (mevcut parçalardan) |
|---|---|
| **Data Platform** | data_fetcher, cache, FINRA/EDGAR/FRED/EODHD, lineage/as-of damgaları |
| **Signal Engine** | features, score_engine, watch_tier, conviction → tek Grade API'si |
| **Truth Engine** | labeling, calibration, edge_report, slippage, outcome_reconciler, config manifest |
| **Decision Surface** | watchlist, alerts, sabah brifi, karne, LLM gerekçe, Telegram |
| **Ops Core** | scheduler, quality_gate, health kartı, logging/tracing |

**Birleştir:** üç skor sözlüğü → Grade; dört doğruluk tanımı → metrik hiyerarşisi; 6 roadmap → tek ROADMAP.md; 2 requirements düzeni → pyproject.
**Ayır/Dondur:** DRL → `research/` (üründe "experimental" rozeti veya tamamen gizli); dekoratif agent'lar → frozen; Academy → ayrı ürün kararı (hibe anlatısında "toplumsal etki" modülü olarak kalabilir, geliştirme önceliği değil).
**Kaldır:** `finpilot_score.py` shim, `paper_validate.py.bak`, mkdocs `site/` (rebuild edilmeyecekse), kökteki bitmiş analiz script'leri (arşive).

## 10. GÜNCELLENMESİ GEREKEN PLANLAR / RAPORLAR

| Bulgu | Etkilenen Plan/Rapor | Ne Güncellenecek | Öncelik |
|---|---|---|---|
| Metrik hiyerarşisi yok; %74 ≠ kâr | Scanner_Backtest + Konviksiyon raporları | Her ikisine "maliyet-sonrası beklenti" bölümü + metrik hiyerarşi notu ekle | P0 |
| Kimlik tanımı yazılı değil | README.md, yeni docs/VISION.md | Değer önerisi tek cümle; DRL/"%10 haftalık" dili çıkar | P0 |
| Config-manifest yok | Tüm gelecek backtest raporları | "Aktif flag seti + git sha" zorunlu başlık bloğu | P0 |
| Konviksiyon WF'siz | Konviksiyon Raporu v2 | Walk-forward + Wilson CI bölümü | P0 |
| Hibe anlatısı bayat | HIBE_FON_DEGERLENDIRME.md, grant_documents/ (tümü), FINANZPLAN | Yeni pozisyonlama (Bölüm 8) ile yeniden üret; DRL iddialarını izole et | P1 |
| 6 roadmap çelişkili | ROADMAP_* (6 dosya) | Tek ROADMAP.md (bu raporun Bölüm 11'i taban); eskiler archive | P1 |
| V6 bülten başlamadı | 90-gün planı (audit-2026-06-12/08) | Bülten yerine "Top-3 brifi + public karne" olarak revize | P1 |
| DRL wf raporu kırık | wf_validation_report üretici script + DRL_* docs | Metrik düzelt veya raporu emekliye ayır; DRL_STATUS.md tekille | P1 |
| Sistem sağlığı görünmez | PAPER_TRADING_GUIDE, ops runbook'ları | Health kartı + job-run tablosu dokümante | P2 |

**Geçersizleşen varsayımlar:** "Skorun edge'i negatif" (Haziran) → artık kalibre-pozitif ama kâr-kanıtsız; "scanner yavaş" → çözüldü; "önce bülten (V6)" → Top-3 brifi daha kısa yol; "DRL ana bileşen" → research preview.
**Öne çekilecekler:** Truth Engine, Top-3 brifi, hibe dosyası yenileme. **Ertelenecekler:** canlı execution, portfolio construction, tam copilot, DRL retrain.

## 11. 30 / 90 / 180 GÜNLÜK YOL HARİTASI

**Gün 1-30 — DOĞRULUK + İLK ÜRÜN NESNESİ**
- Truth Engine v1: maliyet-sonrası beklenti sütunu, config manifest damgası, as-of zorunlu alan, Wilson CI'ları, konviksiyon walk-forward.
- Tek Grade API'si + UI'da tek rozet; günlük tavan alert hattında zorunlu.
- Sabah brifi v1 (Top-3 + gerekçe template'i, LLM'siz başlayabilir); sistem-geneli karne sayfası.
- Sistem Sağlığı kartı (job-run tablosu); Sentry aç; arşiv-süreklilik alarmı.
- Dolar-hacim filtresi; dekoratif agent'ları cron'dan çıkar.

**Gün 31-90 — KANIT + İLK KULLANICI + HİBE DOSYASI**
- Edge Report serisini kesintisiz biriktir (hedef: 8+ hafta); paper-auto-top3 modu veri üretsin.
- LLM gerekçe üretimi (yerel triage + yapılandırılmış çıktı, `llm/prompts/` versiyonlu).
- 10-20 tanıdık beta; public karne sayfası; waitlist'i gerçek DB'ye taşı.
- Hibe paketi yeniden yazımı (Bölüm 8 anlatısı) + WU/TU Wien akademik temas + GmbH/tüzel kişilik kararı.
- SQLite WAL + yazar tekilleştirme; coverage gate; RVOL/borrow-fee veri biriktirme.
- **Gün 90 karar noktası:** maliyet-sonrası beklenti pozitif mi? → Evet: paper'dan yarı-otomatik pilota tasarım başlar. Hayır: ürün tamamen "izleme + karne + eğitim" konumuna sabitlenir (bu da hibe için yeterli ve güvenli).

**Gün 91-180 — ÖLÇEK + BAŞVURU + ÜRÜN KARARI**
- Hibe başvuruları fiilen verilir (12 haftalık kanıt serisi + beta metrikleriyle).
- Tauri tek-tık masaüstü paketi (production build + sidecar).
- Options/IV pilotu; catalyst tagging v2; elit kova n>200 hedefi.
- Beta→ödeme testi (Top-3 brifi premium) veya hibe-öncelikli yolda traction büyütme — gün-90 sonucuna göre.
- Postgres go/no-go; DRL retrain yalnızca ayrı research track olarak (ürün bağımlılığı olmadan).

---
*Bu rapor `docs/audit-2026-06-12/` zincirinin devamıdır; bir sonraki audit bu dosyayı supersede etmelidir. Hazırlayan: sistem audit ajanı, 2026-07-03.*
