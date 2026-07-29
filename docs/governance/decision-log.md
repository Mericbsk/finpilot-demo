# FinPilot — Merkezi Karar Logu
_CLAUDE.md Bölüm 3 formatı: her önemli karar buraya, dağınık dosyalara gömülmez._
_Not (düzeltildi 2026-07-29): docs/INDEX.md 2026-07-24'te zaten gerçek indekse dönüştürülmüştü; bu satır o tarihten sonra güncellenmemiş bayat bir notu tekrarlıyordu. 2026-07-29'da INDEX.md'ye ayrıca makine-okunur bir manifest eklendi (bkz. aşağıdaki girdi)._

---

[2026-07-29] - Otorite-haritasi gocu: lint guard (Level A uygulandi) + INDEX.md manifest / .github rewrite (Level B pending)
Baglam: Kullanici `docs/2026-07-29-otorite-haritasi-gocu-plani.md` planini
onayladi ve "neler olusturmamiz gerekiyor" diye sordu. Uygulamadan once repo'nun
gercek governance yuzeyi okundu (varsayimla degil): `docs/INDEX.md` VE
`docs/governance/decision-log.md` zaten VARDI (plan taslaginin "ikisi de yok"
iddiasi yanlisti); INDEX.md 2026-07-24'te zaten gercek otorite haritasina
donusturulmustu, ama bu logun ust notu bunu yansitmiyordu (yukarida duzeltildi).
`_instructions/01-governance.md`, `05-escalation.md`, `08-security.md` hala
Status: DRAFT (CORE-006 onayi bekliyor); yalniz `00-core.md` ACTIVE. Kok
klasorler `00-strategy…06-releases` ve `_instructions/core-rules.yaml`
dogrulandi — gercekten yok. `.github/instructions/*.md` (7 dosya) sadece
`applyTo` degil, govde metninde de (mission.md, composite-score.md,
entry-exit-rules.md, architecture.md, glossary.md, risk-policy.md) hic var
olmamis dosyalara atif veriyordu; bunlar ICAT EDILMEDI (CORE-004), gercek
yollara veya acik "gap" notuna cevrildi.
Karar (Level A — uygulandi, otonom, izole, salt-okunur guard):
`scripts/lint_authority_map.py` olusturuldu; `docs/INDEX.md`'deki manifesti ve
`.github/instructions/*.md` applyTo alanlarini gercek agacla karsilastirir.
Calistirildi: 7/7 hayalet applyTo hatasi tespit etti, duzeltme sonrasi
`lint_authority_map: OK (0 errors, 0 warnings)`.
Karar (Level B — uygulandi, Merric onayi bekliyor, KAPANMADI):
(a) `docs/INDEX.md`'ye JSON manifest eklendi (15 entry; strategy,
product-rules, engineering-architecture, risk-policy, releases acikca
`status: gap` isaretlendi — icat edilmedi); (b) bu logun ust notu duzeltildi;
(c) `.github/copilot-instructions.md` yeniden yazildi — hayalet klasor
haritasi silindi, `docs/INDEX.md`'ye referans verildi, `core-rules.yaml`
referansi kaldirildi (CORE-003: 00-core.md'yi kopyalamak yerine referans);
(d) 7 `.github/instructions/*.md` dosyasinin `applyTo` + govde referanslari
gercek yollara veya acik gap notlarina cevrildi; (e) `CLAUDE.md` v3.0→v3.1:
Startup Sequence'e docs/INDEX.md + decision-log adimlari eklendi, Governance
bolumundeki dosya referanslari tam yola cevrildi (changelog eklendi).
Etki alani: yalnizca dokumantasyon/AI-talimat dosyalari
(`.github/**`, `CLAUDE.md`, `docs/INDEX.md`, bu log, yeni `scripts/
lint_authority_map.py`). Scanner/distribution/api/web PRODUCTION kodu
davranissal olarak DEGISMEDI.
Sinir: `AGENTS.md` DRAFT→APPROVED degisikligi yapilmadi (Level C, yalniz
Merric). `_instructions/01-governance.md/05-escalation.md/08-security.md`
DRAFT durumu degistirilmedi. `core-rules.yaml` OLUSTURULMADI (CORE-003:
00-core.md'yi tekrar etmemek icin referans kaldirmayi tercih ettik; alternatif
"olustur" secenegi Merric onayina birakildi). Yeni "gap" olarak isaretlenen
otorite dokumanlari (mission.md, composite-score.md, entry-exit-rules.md,
architecture.md, risk-policy.md) bu kararla OLUSTURULMADI/ONAYLANMADI.
Operasyonel bulgu: bu oturumda `.github/copilot-instructions.md`, `CLAUDE.md`
ve bu logun kendisi, diskteki degisiklik dogrulandiktan SONRA, editorde acik
eski-icerikli sekme/otokaydetme kaynakli goruntu ile SESSIZCE eski haline
donduruldu; ayni edit ikinci kez uygulanarak kurtarildi. Kok neden dogrulanamadi
ama YONERGE.md M1 (OneDrive/AV dosya guvenligi riski) ile tutarli — izlenmesi
gereken acik bir operasyonel risk olarak buraya kaydedildi.
Kanit: `python scripts/lint_authority_map.py` -> `OK (0 errors, 0 warnings)`.
Durum: Level A uygulandi ve dogrulandi; Level B degisiklikler diskte hazir
ancak commit/push edilmedi, Merric onayi olmadan "kapandi" sayilmaz.

[2026-07-29] - Scanner kirilma/regresyon kok neden forensic analizi + Bolum 3-Ek (Level A uygulandi + Level B pending)
Baglam: Kullanici talebiyle scanner/distribution yayin zincirinin tekrar tekrar
"harden/restore/repair" commit'i almasinin (07-17, 07-23, 07-24, 07-27x2, 07-28)
yapisal kok nedeni arastirildi (git log, requirements.txt, render.yaml/.env,
ci.yml, tests/ incelemesi).
Dogrulanan bulgular: (1) main dalina dogrudan push, CI kapi degil sonradan
dogrulama; (2) render.yaml ile .env.example arasinda iki bagimsiz elle
senkronize env kaynagi (9 FINPILOT_ENABLE_*/FRED_*/SEC_EDGAR_* bayragindan
render.yaml'da sadece 1'i var); (3) yfinance pinlenmemis (bilinen kirilgan
veri-kaynagi bagimliligi) + duckduckgo-search cakisan cift satir; (4)
scanner/data_fetcher.py'de genis kapsamli sessiz exception yutma; (5)
tests/test_scanner_contract.py fixture yoksa skipTest ile sessizce geciyordu;
(6) EN KRITIK: tests/test_ranking_guard.py, scanner.evaluate._execution_contract
import ediyordu — bu fonksiyon 07-15'te (2c60744) scanner.execution_policy.
execution_contract'a tasinmis ama test guncellenmemis; ImportError butun pytest
collection'ini 14 gundur (6+ sonraki commit boyunca) durduruyordu.
Karar: FinPilot_UcaUca_Uygulama_Plani_2026-07-24.md'ye "BOLUM 3-EK" eklendi
(Bolum 3 yeniden acilmadan, bulgular kayda gecirildi). Level A kalemleri
UYGULANDI: (a) test_ranking_guard.py import+assertion duzeltildi (davranis
degismedi, sadece dogru sembole baglandi — tier siniflandirmasi elle
dogrulandi), (b) test_scanner_contract.py skipTest -> fail, (c) ci.yml
--cov=distribution eklendi, (d) requirements.txt yfinance==1.4.1 pinlendi +
yinelenen duckduckgo-search satiri silindi.
Etki alani: tests/test_ranking_guard.py, tests/test_scanner_contract.py,
.github/workflows/ci.yml, requirements.txt. Scanner/distribution PRODUCTION
kodu davranissal olarak degismedi — sadece test/CI/bagimlilik katmani.
Sinir: render.yaml/.env birlestirme (3E.7), dry-run zorunlulugu (3E.8), erken
uyari sistemi (3E.9) Level B — Merric onayi bekliyor, henuz uygulanmadi.
Kanit: bu oturumdaki forensic analiz + pytest tam-suit calistirma sonucu
(asagida ayri girdi olarak eklenecek).
Durum: Level A kismi uygulandi; Level B kismi pending.

[2026-07-29] - Scanner kirilma/regresyon kok neden forensic analizi + Bolum 3-Ek DOGRULAMA sonucu (Level A dogrulandi, 2 yeni Level B/C bulgu)
Baglam: Bir onceki 07-29 kaydindaki 4 Level A degisiklikten sonra tam pytest
suit calistirildi (734 passed, 15 failed, 6 skipped, 380.81s,
--cov-fail-under=70 uygulanarak).
Dogrulanan sonuclar:
(1) test_ranking_guard.py fix ONAYLANDI — collection artik 0 hata (once: 1
collection error, tum suit durmustu). Hedeflenen 4 dosyanin (test_ranking_guard,
test_scanner_contract, test_distribution, test_prepublish_gate) 47 testi ayrica
izole calistirildi: 47 passed.
(2) YENI BULGU — 15 test kirmizi, hicbiri bu oturumda degistirilen 4 dosyayla
ilgili degil (test_evaluate.py, test_catalyst.py, test_squeeze_factor.py,
test_full_universe_robustness.py, test_new_endpoints.py, test_content_layer.py,
test_api_runtime.py, test_prometheus.py, scanner_rollout/test_runtime_baseline.py).
Dogrulandi: bunlar 07-15'ten beri collection hatasi yuzunden gorunmez olan,
onceden var olan olasi regresyonlar (orn. compute_recommendation_score beklenen
disi skor, dedup_symbol_day() policy kwarg'i kabul etmiyor). Olasi, test
edilmeli: her biri ayri kok-neden gerektirir — bu oturumda DUZELTILMEDI (kapsam
disi, tek tek incelenmeden production kodu degistirilmedi).
(3) YENI BULGU — --cov-fail-under=70 esigi FAIL (gercek: 43.47%). Esik
2026-03-30'da (a9f65923) 30'dan 70'e cikarilmis. Dogrulandi (hesaplandi):
distribution/ modulu kendi icinde ~63% kapsaniyor, ortalamayi dusuren o degil —
drl/ altinda binlerce satir %0 kapsanan modul (data_loader.py, ensemble_router.py,
inference.py, specialists.py vb.) asil neden. Yani bu oturumdaki --cov=distribution
eklemesi (3E.3) bu FAIL'e neden OLMADI — hesaplama distribution dahil/haric
karsilastirmasi ile dogrulandi (~%42 -> ~%43, iyilesme yonunde). Olasi, test
edilmeli: gercek CI ortaminda (GitHub Actions) bu esik hic gecmis mi yoksa
yakinda mi bozulmus — bu ortamdan GitHub Actions calisma gecmisine erisilemedi
(repo'da PR yok, direkt main'e push), dogrulanamadi.
Karar: FinPilot_UcaUca_Uygulama_Plani_2026-07-24.md Bolum 3-Ek tablosuna 3E.11
(15 test hatasi triyaji, Level B, onay bekliyor) ve 3E.12 (coverage esigi
politika karari, Level B/C, karar bekliyor) eklendi. 3E.5 gercek sonucla
guncellendi. 3E.6 (git tag) notu: 15 kirmizi test varken "stable" etiketi
yaniltici olur, 3E.11 triyaj edilmeden atilmamali.
Etki alani: sadece dokumantasyon (plan + decision-log). Hicbir production veya
test kodu bu adimda degistirilmedi.
Sinir: 3E.7 (render/env), 3E.8 (dry-run), 3E.9 (erken uyari), 3E.11 (15 test
triyaji), 3E.12 (coverage esigi karari) hepsi Level B/C — Meric onayi bekliyor.
git add/commit/push YAPILMADI — bu da ayri onay gerektirir.
Durum: Level A bolumu dogrulanarak kapatildi; 5 Level B/C kalemi (3E.7-3E.9,
3E.11, 3E.12) pending.

[2026-07-28] - Donanim arastirmasi gereksinim fazi (Level B/C, pending)
Baglam: FinPilot icin 7/24 yerel AI ve agent altyapisi donanim arastirmasi
baslatildi. Repository incelemesi, API/scheduler/veri akisi CPU-I/O agirlikli;
genel Ollama modeli `qwen2.5:3b`, Academy modeli `qwen2.5:7b` ve varsayilan
execution modu `dry_run` oldugunu gosterdi.
Karar onerisi: Gereksinim matrisi
`reports/hardware_research_requirements_20260728.md` icinde kayda alinsin.
Model boyutu, context/concurrency, butce, hedef ortam, uptime/RPO-RTO ve
paper/DRL kapsami netlesmeden GPU, sistem veya satin alma onerisi
kesinlestirilmesin.
Sinir: Bu kayit satin alma, butce, yeni servis/queue mimarisi, deployment,
paper/live execution veya runtime davranisi onaylamaz.
Durum: pending - Level B onerisi ve Level C insan karari bekleniyor.

[2026-07-28] - Karsilastirmali strateji test raporu (Level A)
Baglam: Kullanici talebiyle tum arastirma fazlarinin proxy, path-aware,
orneklem, maliyet, sonuc ve guven seviyesi acisindan tek raporda
karsilastirilmasi istendi.
Karar: `reports/strategy_comparative_test_report_20260728.md` olusturuldu.
Close-to-close proxy ile path-aware execution ayrimi korunacak; kucuk pozitif
alt gruplar aday olarak kalacak; ana V2 path-aware locked-OOS sonucu NO EDGE
olarak raporlanacak; spread/impact ve bos walk-forward fold'lari
`insufficient_data` olarak kalacak.
Sinir: Bu kayit yeni scanner, entry, exit, score, sizing, risk, portfolio,
paper/live veya scheduler kurali onaylamaz.
Kanıt: Karsilastirmali rapor ve altinda listelenen phase artifact'lari.
Durum: Uygulandi; arastirma raporu olarak kaydedildi.

[2026-07-28] - Sequential strategy research execution (Level A)
Context: The council-recommended research sequence was executed without
changing production behavior. The run covered input manifest, deterministic
contracts, entry/ranking, path-aware exits and costs, finite-slot portfolio
screens, calibration, regime diagnostics, and walk-forward availability.
Decision: Store outputs under
`data/backtest_out/research_start_20260727/` and report proxy labels,
path-aware labels, cost assumptions, sample sizes, and missing-data verdicts
separately. Preserve all current scanner, entry, exit, sizing, risk, paper,
live, and scheduler rules.
Evidence: `reports/strategy_scenario_test_results_20260727.md` and the phase
artifacts referenced there. Focused deterministic suite: 62 passed. The main
V2 path-aware locked-OOS execution remained approximately flat (n=62,
-0.0046% net expectancy, PF 0.9993); small ATR/RVOL subsets remain hypotheses
only. Spread/impact and a valid walk-forward test fold remain unavailable.
Status: applied as research execution and reporting only; no Level B/C change
approved.

[2026-07-28] — Sohbet içi yayın önizlemesi ve açık onay akışı (Level B, pending)
Bağlam: Tarama export'u tam olsa bile Telegram ve web yayını dış yan etkili işlemler. İçerik önce insan tarafından burada görülmeden yayınlanmamalı.
Değişiklik önerisi: `scripts/preview_publish.py` yalnızca gate kontrolü, Telegram taslağı ve web public görünümü üretir; queue, Telegram API, published snapshot ve deploy hook çağırmaz. Açık `YAYINLA` onayından sonra `scripts/publish_now.py --yes` çalıştırılır.
Etki alanı: `scripts/preview_publish.py`, `docs/ops/YAYIN_ONIZLEME_ONAY_AKISI_20260728.md`. Scanner, product, risk, sizing, entry/exit ve live strateji kuralları değişmedi.
Durum: pending — Level B; canlı yayın akışı için Meriç onayı bekleniyor.

[2026-07-27] — Strategy red-team audit follow-up (Level B, pending)
Bağlam: `reports/strategy_red_team_audit_20260727.md`, mevcut strateji kanıtlarında iki kritik sınır tespit etti: 2026-05-05 walk-forward/Monte Carlo raporundaki negatif veya zayıf OOS sonuçları ile 2026-05-11 haftalık raporundaki izlenebilirliği eksik pozitif sonuç uzlaştırılmamış; ayrıca `resolved_pct_t5 >= 5%` close-to-close proxy'si path-aware execution/P&L kanıtı değildir.
Öneri: P0 olarak rapor reconciliation, locked-OOS yeniden üretimi ve forward OHLC/path-aware execution replay; P1 olarak liquidity/cost, survivorship/missingness, rejim-sektör yoğunlaşması ve calibration testleri; P2 olarak kullanılmayan model bileşenleri ile operasyonel state persistence incelemesi yürütülsün.
Sınır: Bu kayıt onaylanmış strateji değişikliği değildir. `/01-product/*`, scanner weights, entry/exit, sizing, leverage, risk policy ve live execution değiştirilmedi. Eksik veri `insufficient_data` olarak raporlanmalı; default veya sıfır değerle tamamlanmamalı.
Sahip / kanıt / kapı: Araştırma sahibi atanacak; her test dataset hash, tarih aralığı, row count, canonical symbol-day politikası, cost assumption, label türü, trade count ve missingness paydasını kaydedecek. İnsan onayı ve karar günlüğünde açık bir uygulama kaydı olmadan hiçbir P0/P1/P2 önerisi canlı kurala dönüşmeyecek.
Durum: pending — Level B; karar ve uygulama için Meriç onayı bekleniyor.

[2026-07-27] — Araştırma canonical symbol-day politikası (Level A)
Bağlam: `full_universe_robustness.py` aynı symbol-day içindeki ilk CSV satırını seçiyor, bu da sonucu dosya sırasına bağımlı kılıyordu. Ayrıca hedef metadata'sı close-to-close alanını peak-touch gibi tanımlıyordu.
Değişiklik: Varsayılan canonical seçim `earliest scan_ts` oldu; `latest` duyarlılık seçeneği eklendi ve hedef metadata'sı `resolved_pct_t5 >= 5%` close-to-close proxy olarak düzeltildi. Araştırma çıktısında politika ve veri sınırı kaydediliyor.
Etki alanı: `full_universe_robustness.py`, `tests/test_full_universe_robustness.py`.
Durum: uygulandı; scanner, product kuralları ve live execution değiştirilmedi. İlk araştırma koşusu `data/backtest_out/research_start_20260727/` altında üretildi.

[2026-07-24] — Karne penceresi 30 gün (Karar A)
Bağlam: Karne DB-fallback'i kuruldu; 5 günlük pencerede örneklem çok küçük (B n=9).
Değişiklik: FINPILOT_KARNE_WINDOW_DAYS=30 (.env + .env.example). Öncesi: sabit 5 gün (API varsayılanı).
Etki alanı: distribution/karne.py, snapshot karne alanı, web LedgerStrip.
Durum: uygulandı.

[2026-07-24] — Masthead ana istatistiği süreç sayısına dönüşür (Karar B)
Bağlam: Dürüst karne dolduğunda canlı ağırlıklı isabet ~%2 çıkacak; "%68 backtested" ile aynı vitrinde duramaz, çıplak %2 de tek başına yanıltıcı/yıkıcı.
Değişiklik: Masthead'de oran yerine şeffaflık/süreç sayısı ("5.700+ pick publicly tracked since Sep 2025" formunda); grade bazlı isabet oranları yalnız LedgerStrip'te, pencere etiketiyle. Öncesi: karne boşken etiketli backtest oranı, doluysa canlı ağırlıklı oran.
Etki alanı: web Masthead.tsx (+ i18n metinleri), LedgerStrip, distribution/karne.py (tracked_total).
Durum: uygulandı (2026-07-24, Bölüm 4 — canlı sayı: 5.719 → "5,700+").

[2026-07-24] — DE dili kalır (eski "DE'yi gizle" önerisi geçersiz)
Bağlam: 07-23 ReAudit "DE anahtarı içeriksiz" diyordu; 24 Tem audit'i DE rationale'lerin snapshot'ta üretildiğini ve translations.ts DE bloğunun dolu olduğunu buldu.
Değişiklik: DE dil seçeneği kalır; aday metinleri artık rationale_i18n üzerinden üç dilde de gerçek içerik gösterir.
Etki alanı: web dil anahtarı, EditionArticle, DailyDouble.
Durum: uygulandı.

[2026-07-24] — Boş çekirdek DB tabloları resmen emekli (Karar C)
Bağlam: signals, scan_results, buy_signals aylardır boş; üretim zinciri JSON-export üzerinden akıyor. execution_intents/events/controls Alpaca planı kâğıtta olduğu için hiç kullanılmadı.
Değişiklik: Bu tablolar "emekli" statüsünde — şema KALIR, silinmez, yeni kod bunlara yazmaz/okumaz. Alpaca oto-execution işi resmen başlarsa execution_* tabloları geri açılır.
Etki alanı: core/database şeması (dokunulmadı), gelecekteki geliştirmelerin veri-yolu tercihi.
Durum: uygulandı (kayıt kararı; kod değişikliği gerekmiyor).

[2026-07-24] — Bölüm sırası değişikliği: 0→1→3, Bölüm 2 yarın sabaha
Bağlam: Bölüm 2'nin kanıtları (süre logu, seri sayacı, alarm testi) zaten sabah yayınından çıkacak; beklemek yerine Bölüm 3 sigortaları öne alındı.
Değişiklik: Uygulama planındaki 0→1→2→3 sırası fiilen 0→1→3→(2+4) oldu.
Etki alanı: FinPilot_UcaUca_Uygulama_Plani_2026-07-24.md takvimi.
Durum: uygulandı (Meriç onayı, 2026-07-24).

[2026-07-24] — regime_weights ve DRL_gate resmen PARK (Karar D)
Bağlam: FINPILOT_ENABLE_REGIME_WEIGHTS ve FINPILOT_DRL_GATE ikisi de skoru değiştiren deneysel özellikler; DRL placeholder feature'larla çalışıyor (üretim-dışı), hiçbiri backtest'le doğrulanmadı (Bölüm 8 audit).
Değişiklik: Her ikisi de PARKED. Varsayılan kapalı kalır (=0). Backtest ile kanıtlanmadan lansman öncesi AÇILMAZ. Kod/şema durur, silinmez; geri dönülebilir.
Etki alanı: core/regime_weights.py, core/scheduler.py DRL veto yolu, skorlama davranışı (değişmiyor).
Durum: uygulandı (Meriç onayı, 2026-07-24) — kod değişikliği gerekmiyor, bayrak zaten 0.

[2026-07-24] — Otomatik bakım işleri erken tek pencereye toplandı (Karar E)
Bağlam: Zamanlanmış cron işleri gün içine dağılmıştı ve calibration + daily_ops İKİSİ de 23:30 UTC'deydi (çakışma). Manuel yayın (~14:00) ve piyasa (13:30) ile de zamansal yakınlık riski.
Değişiklik: Tüm sabit-saatli bakım işleri erken sessiz pencereye (UTC 05:00–05:55, Viyana ~07:00) alındı ve kademelendi:
  - Günlük: calibration 05:00 · daily_ops 05:10
  - Pazar: research_pipeline 05:20 · ceo_report 05:40
  - Pazartesi: calibration_retrain 05:20 · resolve_open_signals 05:35 · edge_report 05:55
Aynı gün içinde iki iş aynı dakikada değil; 23:30 çakışması yok; hepsi piyasa+manuel yayından çok önce. Interval işleri (main_cycle/eval/reconcile/drift/auto_approve) coalesce+max_instances=1 ile korunuyor, dokunulmadı.
Etki alanı: core/scheduler.py CronTrigger saatleri.
Durum: uygulandı (Meriç onayı, 2026-07-24; py_compile geçti).

[2026-07-28] — Bakım penceresi 12:00 Europe/Vienna'ya taşındı (Karar E güncelleme)
Bağlam: Karar E'de pencere 05:00 UTC (07:00 Viyana) idi; kullanıcı bakım penceresinin 12:00 Viyana'da olmasını istedi (aktif iş gününün başı, US açılışı 15:30 Viyana ve manuel yayından önce).
Değişiklik: 7 cron işi UTC yerine timezone="Europe/Vienna" + hour=12 ile (DST-güvenli), kademeli:
  Günlük: calibration 12:00 · daily_ops 12:10 · Pazar: research 12:20 · ceo 12:40 · Pazartesi: calibration_retrain 12:20 · resolve 12:35 · edge 12:55. Aynı gün içinde çakışma yok.
Ayrıca: telegram_bot_runner.py `telegram_config` import hatası düzeltildi (scripts/'ten çalışınca repo kökü sys.path'e ekleniyor + run_bot.py PYTHONPATH veriyor).
Etki alanı: core/scheduler.py, scripts/telegram_bot_runner.py, scripts/run_bot.py.
Durum: uygulandı (Meriç onayı, 2026-07-28; py_compile geçti).

[2026-07-28] — Level-B denetim: 5 KIRMIZI BAYRAK açıldı (pending, P0)
Kaynak: docs/audits/FinPilot_LevelB_IsPlani_Yayin_Audit_2026-07-28.md
Statü: AÇIK — her biri sorumlu+tarih atanana dek açık kalır.
  P0-a) Yasal sayfalar (Impressum + Datenschutz + AGB) YOK — Avusturya yasal zorunluluğu. Sahip: —, Tarih: —
  P0-b) SMTP sızan şifre rotate edilmedi (güvenlik). Sahip: —, Tarih: —
  P0-c) Traction ~0 (tg_users=1, feedback=0) — gerçek davet + teslim serisi. Sahip: —, Tarih: —
  P0-d) Premium/Stripe hiç test edilmedi (gelir=0). Sahip: —, Tarih: —
  P0-e) Site mesajı "AI stock" (compliance+repositioning riski) → literacy çerçevesi. Sahip: —, Tarih: —
Nihai değerlendirme: kamuya lansman HENÜZ DEĞİL; soft-launch koşullu.

[2026-07-28] — Yayın hattı kararları (Telegram+Web ön-taraması sonrası)
- Web deploy: git commit+push (publish_web.py → WEB_PUBLISH_CMD; REQUIRE_VERCEL_DEPLOY=0). Snapshot git'te izlenir, Vercel push'ta deploy eder.
- Scan: her sabah elle scan + publish_now (oto-taslak + insan onayı). DISTRIBUTION=0 kalır.
- Kanal adı @Finpilot_Breif ("Brief" yazım hatası) ŞİMDİLİK KORUNUR — lansmana kadar takipçi sıfırlamamak için; lansman öncesi yeniden değerlendir.
Durum: uygulandı (Meriç kararı, 2026-07-28); publish_web.py eklendi.

[2026-07-29] — Tek-dokunuşla yayın DOĞRULAMA (Faz 1): plan devrede DEĞİL — KOVA C açıldı (pending, P0)
Faz 1 bulgusu: web-deploy kancası ayarsız, bot-süpervizör dosyaları eksikti, waitlist aynası/admin-key/akademi-export ayarsız, hiçbir uçtan-uca tur doğrulanmadı.
KOVA C (kapanana dek AÇIK, Faz 3 kilitli):
  C1) FINPILOT_WEB_PUBLISH_CMD ayarsız → web yayını çalışmaz. Sahip: —, Tarih: —
  C2) Bot-süpervizör dosyaları eksikti → run_bot.py+start_bot.bat YENİDEN OLUŞTURULDU (bu oturum); startup+gözlem: —
  C3) WAITLIST_WEBHOOK_URL ayarsız → veri kaybı riski. Sahip: —, Tarih: —
  C4) SMTP rotasyonu doğrulanamadı (güvenlik P0). Sahip: —, Tarih: —
  C5) Uçtan-uca tam tur doğrulanmadı → kabul kriteri karşılanmadı. Sahip: —, Tarih: —

[2026-07-29] — Gerçek-makine doğrulama bulguları (kullanıcı denetimi) + kararlar
Bulgular: (1) .env'de FINPILOT_REQUIRE_VERCEL_DEPLOY İKİ KEZ (=1 ve =0) — çelişki; (2) bot süreçleri zaten çalışıyor (run_bot + telegram_bot_runner) → startup çift-bot/409 riski; (3) DB'ler journal_mode kontrolü yapılmadan hardening YAPILMADI (doğru); (4) komut satırında bir kimlik görüldü → rotasyon önerildi.
KARARLAR:
  - REQUIRE_VERCEL_DEPLOY = **0** (tek satır; =1 SİLİNECEK). Neden: git-push deploy tetikler, ayrı hook yok; =1 publish'i "başarısız" sayar. (kod: _push_snapshot_to_web)
  - Bot: startup'a eklemeden önce TEK poller garanti edilecek (Telegram 409 riski).
  - DB hardening: yalnız journal_mode=wal ise + süreçler durdurulunca (aksi halde atla; büyük olasılıkla zaten delete).
  - Kullanıcı Level B/C kapılarında (git push, gerçek yayın, SMTP, Sheet) açık onay olmadan İLERLEMEDİ — governance'a uygun, onaylandı.
Durum: kararlar kayıtlı; uygulama kullanıcının açık onayıyla, kendi makinesinde.

[2026-07-29] — İçerik/kalite doğrulama (Faz 1): gerçek sayılar + pending Level B/C
Gerçek sayılar: akademi 6 published/73 draft (rapor 5/39 = bayat); expired=11 (8 tarih); title hâlâ "AI-Powered Stock Intelligence"; yasal sayfalar HÂLÂ YOK (persist etmemiş); metodoloji route yok; bot anketi yok.
META: sandbox'ta oluşturulan bazı dosyalar diske ulaşmadı → her değişiklik git commit gerektirir.
Pending (Level B/C): metodoloji sayfası(B) · akademi yayın hattı(B) · positioning/title(B) · karşı-görüş satırı(B) · yasal sayfalar(C, yeniden oluştur+commit+avukat) · içerik takvimi(B) · evergreen SEO(B).
Bağımsız görüş: 1 numaralı kalite hamlesi = kesintisiz teslim (tutarlılık); akademi darboğazı yayınlama; okuyucu yokken içerik-zenginliği erken optimizasyon.
