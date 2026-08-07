# FinPilot — Merkezi Karar Logu

_CLAUDE.md Bölüm 3 formatı: her önemli karar buraya, dağınık dosyalara gömülmez._
_Not (düzeltildi 2026-07-29): docs/INDEX.md 2026-07-24'te zaten gerçek indekse dönüştürülmüştü; bu satır o tarihten sonra güncellenmemiş bayat bir notu tekrarlıyordu. 2026-07-29'da INDEX.md'ye ayrıca makine-okunur bir manifest eklendi (bkz. aşağıdaki girdi)._

[2026-07-31] — Opsiyon-faktörü pilotu (yeni-bilgi) hattı kuruldu (Level A, local-run bekliyor)
Layer: Research / data
Level: A
Bağlam: Roadmap v2 P1 — teknik faktörler dürüst-metrikte tükendi (IC~0); tek yeni-bilgi yolu opsiyon positioning/IV (fiyat-hacimden türetilemez). EODHD UnicornBay opsiyon geçmişi Q4-2023'ten 2.5+ yıl EOD (Greeks/IV/OI/put-call), 6.600+ ABD hissesi → sinyal penceresini (Eyl'25–Tem'26) kapsıyor.
Değişiklik: `data/eodhd_client.py`'ye `options_eod()` metodu + modül wrapper eklendi (`mp/unicornbay/options/eod`, JSON:API, 24s cache). Yeni `options_factor_pilot.py`: 6 faktör türetir (put/call OI & hacim, ATM IV, IV skew, toplam OI/hacim) → `edge_recheck` dürüst-metrik + IS/OOS rank-IC testi; modlar: `--probe` (canlı şema+plan teyidi), `--build` (resumable), `--analyze`. Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ.
Etki/Durum: uygulandı ve AĞSIZ test edildi — `py_compile` temiz; `derive_factors` sentetik kontratla doğrulandı (put/call OI 1.625, ATM IV 0.35, skew 0.09); `analyze` harness'i gerçek symbol/date + sentetik faktörle çalıştı ve rastgeleyi doğru "tutarsız" işaretledi (IS/OOS disiplini). LOCAL-RUN bekliyor (ağ + EODHD UnicornBay opsiyon eklentisi gerekir). Ön koşullar: (1) opsiyon eklentisi plan kapsamı `--probe` ile teyit; (2) alan adları ilk yanıtla doğrulanıp gerekirse `FIELD_MAP` güncellenmeli. Bir faktör IS+OOS aynı işaret & |IC|>~0.03 verirse projenin ilk gerçek lead'i olur; vermezse kolay-erişilebilir veri de tükenmiş sayılır.

---

[2026-07-31] — Edge araştırması: dürüst-metrikte tradeable alfa yok + resolved_pct_t5 P0-bozuk (Level A, bulgu)
Layer: Research / quant
Level: A
Bağlam: FINPILOT RESEARCH master prompt — "skor gerçekte neyi ölçüyor?" bilimsel olarak araştırıldı.
Bulgular (hepsi kanıtlı, IS/OOS ve dürüst metrikle):
- `edge_recheck.py` (yeni, izole) tüm evreni (53.754 satır) price_cache'ten GERÇEKLEŞEN kapanış-kapanış + triple-barrier (cost'lu) ile yeniden hesapladı.
- METRİK DENETİMİ: ATR↔resolved_pct_t5(enriched) +0.40 vs ATR↔gerçekleşen c2c +0.01. `resolved_pct_t5` MFE (en-iyi-durum) izliyor, gerçekleşen getiriyi değil → "ATR edge" %100 metrik artefaktı.
- SKOR TESTİ (dürüst): composite_score IC −0.03 (kırık), finpilot_score +0.03 (ihmal, rejim-kararsız: bull +0.055/bear −0.093), ATR ~0/negatif. Cost sonrası evren medyanı ≈0; triple-barrier −0.95.
- ARAMA: 2-faktör 74 kombo (0 stabil) + 4000-konfig ağırlık optimizasyonu (add/remove/invert/reweight, IS/OOS) → hiçbir konfig baseline'ı stabil geçmedi; IS-en iyi OOS'ta şans (%44).
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ (yalnız analiz). İKİ P0 SONUÇ: (1) `resolved_pct_t5` MFE-bozuk → bu metriğe dayanan TÜM geçmiş "edge" iddiaları yeniden temellenmeli; (2) mevcut günlük-bar faktör setinde doğrulanmış tradeable alfa YOK → ilerlemek recombination değil YENİ veri/faktör ya da değer önermesini karar-destek/eğitime kaydırma gerektirir.
Durum: uygulandı — Level A (araştırma bulgusu). Kanıt: `docs/2026-07-31-FinPilot-Research-skorun-anlami-RAPOR.md`, `edge_recheck.py`, `data/backtest_out/edge_recheck.csv`.

---

[2026-07-30] - Sinyal izleme shadow scorecard altyapısı (Level A, uygulandı)
Layer: Research / engineering
Level: A
Bağlam: `docs/2026-07-29-sinyal-izleme-gelistirme-UCTAN-UCA-plan.md` offline kontrol grubu, horizon sweep, dağılım yüzdelikleri, SPY excess return, ATR-normalize getiri, segment alanları ve risk-ayarlı özetler öngörüyor. Faz 0 kontrolünde `data/price_cache` benchmark dahil `2026-06-30` tarihinde bitiyor; mevcut 107 dedup sinyalin tamamı olgunlaşmamış kaldı.
Değişiklik (önce/sonra): Önce `shadow_scorecard.py` yalnız seçilmiş satırları ve model bariyer sonuçlarını özetliyordu; sonra kontrol satırlarını opsiyonel dahil eden, model-bağımsız ileri getiri/MFE, horizon sweep, red nedeni, ADV/veri kalite segmentleri, SPY excess return, p10/medyan/p90, Sharpe-benzeri metrik ve deterministik bootstrap aralığı üreten izole altyapı eklendi. `tests/test_shadow_scorecard.py` sentetik sözleşmeleri doğruluyor.
Etki: Scanner skorları, filtreler, entry/exit kuralları, risk boyutlandırması ve canlı Karne/web yüzeyi değişmedi. Cache yenilenene kadar gerçek performans sonucu üretilmemeli; mevcut çalışma yalnız altyapı ve veri-yeterlilik bulgusudur. Faz 4b Level B olarak bu kaydın kapsamında değildir.
Durum: uygulandı — Level A. Kanıt: `python -m pytest tests/test_shadow_scorecard.py -q` (3 passed); baseline CLI (`--dedup`) 107/107 pending.

---

[2026-07-29] — Waitlist + demo feedback endpoint'lerine Telegram admin bildirimi (Level B, uygulandı)
Layer: Engineering / product distribution
Bağlam: Web yüzü denetimi (`docs/2026-07-29-web-yuzu-DENETIM-raporu.md`) waitlist ve demo feedback formlarının gerçek ve uçtan uca bağlı olduğunu, ama yeni kayıt/yorum geldiğinde hiçbir bildirim gitmediğini kanıtladı: waitlist SMTP yapılandırılmamış (`_notify_waitlist_signup` "skipped" logluyor), feedback yalnız SQLite'a yazıyor. Sonuç: gönderimler fark edilmeden birikiyordu.
Değişiklik: `api/routers/waitlist_signup.py` (yeni `_notify_admin_telegram` helper + signup sonrası ping: e-posta/kaynak/toplam) ve `api/routers/demo_feedback.py` (feedback kaydı sonrası ping: ödeme niyeti + yorum özeti) mevcut `distribution.telegram_client.notify_admin` altyapısına bağlandı. İkisi de try/except best-effort — bildirim hatası isteği bozmaz; `notify_admin` yapılandırma yoksa False döner (raise etmez). Scanner/skor/veri saklama/mevcut SMTP akışı değişmedi (yalnız ekleme — CORE-009).
Etki: Yeni waitlist kaydı / demo yorumu anında Telegram admin'e düşer (`TELEGRAM_BOT_TOKEN`+`TELEGRAM_ADMIN_ID` gerektirir; `.env`'de mevcut). 4/4 birim testi geçti: ping içeriği doğru, boş feedback ping atmıyor, `notify_admin` patlasa bile istek OK. `py_compile` temiz. Canlı deploy yapılmadı.
Durum: uygulandı — Level B; Meriç onayı alındı (2026-07-29). Canlı deploy kararı bu kaydın kapsamında değildir.

---

[2026-07-29] — Telegram gerekçe katmanına bağlam ve izlenecek sonuç açıklaması (Level B, pending)
Layer: Content / product distribution
Bağlam: Günlük Telegram taslağı mevcut faktörleri tek tek açıklıyordu; faktörlerin birlikte neyi düşündürdüğü ve hangi gözlenebilir sonucun izleneceği yeterince açık değildi.
Değişiklik: `distribution/rationale.py` içindeki deterministik rationale üretimine rozet kombinasyonlarına dayalı sentez cümlesi eklendi. Metin sırasıyla gözlenen nedenleri, bağlamsal birleşimi ve doğrulanmamış açık soruyu ifade ediyor; TR/EN/DE çıktıları korunuyor. Scanner skoru, eşikler, risk, entry/exit ve yayın akışı değişmedi.
Etki: Telegram ve snapshot rationale metinleri daha açıklayıcı ve bağlamlı oldu; bugünkü önizleme lint'ten geçti. Web public projection artık graded adaylar ve scan-context kayıtlarında `risk_reward`, `stop_loss`, `take_profit` ve `stop_loss_percent` alanlarını dışarıda bırakıyor. Karne API'si HTTP 401 olduğunda mevcut DB fallback notu korunuyor. Canlı Telegram/web yayını yapılmadı.
Durum: uygulandı — Level B; Meriç onayı alındı (2026-07-29). Canlı yayın kararı bu kaydın kapsamında değildir.

---

[2026-07-29] - Scanner 15-hata triyaji tamamlandi (10 Level A duzeltildi, 5 Level B/C flagged) + render.yaml/.env bulgusu genisletildi
Baglam: Onceki 07-29 kayitlarindaki dogrulama kosusunda (734 passed, 15 failed)
bulunan 15 test hatasi tek tek incelendi (kullanicinin "onayliyorum" onayi
uzerine, kullanici oturumda musait degildi, "otonom calis, iyi kararlar ver"
talimati verildi).
Sonuc: 10/15 duzeltildi (Level A, sadece test katmani, production kodu
degismedi):
(1-2) test_score_engine_catalyst/squeeze_off_by_default: Faz 5 (2026-06-20,
b2bdba0) skor x0.5 dususu icin test beklentisi guncellenmemisti (3.0->1.5).
(3-5) test_defensive_strategy, test_squeeze_factor_high_short_low_float,
test_get_alpha_features_skips_squeeze_when_disabled: yerel .env'deki
FINPILOT_ENABLE_ALPHA_V2=1 testlere sizip squeeze agirligini (0.5/0.5->0.7/0.3)
ve gate'i degistiriyordu; testlere izolasyon eklendi.
(6) test_returns_none_on_insufficient_data: 2026-07-15 (2c60744)
_unavailable_result sozlesmesi icin test bayikti (None bekliyordu, artik
Tier-3 dict donuyor - kasitli, dokumante degisiklik).
(7-8) test_returns_expected_keys, test_rounds_price_to_four_decimals:
_fetch_price_sync Alpaca-once + yf.download() fallback mimarisine tasinmis,
test eski yfinance.Ticker mock hedefini kullaniyordu.
(9) test_auth_register_login_and_me_flow: KRITIK BULGU - core.config.DB_PATH
modul-seviyesi sabit, core.config ilk import edildiginde (collection
sirasinda, fixture'lardan once) donuyor. monkeypatch.setenv("FINPILOT_DB_PATH")
tek basina auth.database.Database()'e ulasmiyor (Database() no-arg cagrisi
donmus DB_PATH'i okuyor) - gercek kalici data/finpilot.db dosyasina yaziyordu,
oturumlar arasi kullanici birikip 409 Conflict'e neden oluyordu. Fix:
monkeypatch.setattr("core.config.DB_PATH", ...) eklendi.
(10) test_all_fields_present_and_lint_clean: glossary prob_band metni
"bir garanti degil" / "not a guarantee" iceriyordu - distribution/lint.py'nin
guarantee kurali negation-aware degil, "degil" ile olumsuzlanmis olsa bile
yakaliyor. Icerik 2026-07-24'te eklenmis, 07-15 collection hatasi yuzunden
gorunmezdi. FIX: icerik yeniden yazildi (linter kurali GEVSETILMEDI - CORE-002
risk&compliance kurali korundu).
5/15 kasitli duzeltilmedi: 2'si tests/test_full_universe_robustness.py
icinde (bu dosya untracked/uncommitted, baska bir es zamanli oturumun WIP'i,
dokunulmadi); 1'i test_prometheus.py port-bind zamanlamasina dayanan
environment-bagimli flaky test; 2'si scanner_rollout/test_runtime_baseline.py
: entry_ok icin score==2 + alignment_ratio>=0.66 durumunda gecerli olmasi
beklenen bir gevsetilmis giris kapisi bekliyor ama scanner/evaluate.py'de
entry_ok = bool(score == 3) sabit kodlanmis. Git log bu test dosyasinin
sadece 2026-05-05'teki dev bir "thanks" commit'inde eklendigini gosteriyor,
ilgili evaluate.py degisikligi izlenemedi - ya hic uygulanmamis planli bir
ozellik ya da gecmiste kaldirilmis bir davranis. Canli sinyal uretim
mantigini etkiledigi icin urun/quant karari gerekiyor, DOKUNULMADI.
Dogrulama: 744 passed, 5 failed, 6 skipped (once: 734/15/6), 0 collection
hatasi, 0 yeni regresyon.
3E.7 bulgusu genisletildi: yerel .env'de 18 `FINPILOT_ENABLE_*`/`FRED_*`/
`SEC_EDGAR_*` anahtari var (hepsi kisisel arastirma icin ACIK), .env.example
bunlarin hicbirini belgelemiyor, render.yaml sadece 1 tanesini iceriyor.
.env.example yorumlari bu faktorlerin coğunun "Default OFF, once shadow modda
olc" seklinde tasarlandigini gosteriyor - yani production'in bunlari
ACMAMASI kasitli/guvenli olabilir. render.yaml'a DOKUNULMADI (canli sinyal
davranisini etkileme riski, tek tarafli karar verilemez).
3E.8 (dry-run zorunlulugu) ve 3E.9 (erken uyari sistemi) incelendi ama
uygulanmadi - ikisi de canli yayin/scan pipeline'ini etkileyen, gozden
gecirme gerektiren degisiklikler.
Etki alani: tests/test_catalyst.py, tests/test_squeeze_factor.py,
tests/test_evaluate.py, tests/test_new_endpoints.py, tests/test_api_runtime.py,
distribution/glossary.py (icerik, politika degil). Commit 068f2aa, push edildi.
Not (guvenlik, bilgi amacli): render.yaml/.env karsilastirmasi sirasinda
.env icinde gercek bir FRED_API_KEY degeri goruldu; .gitignore (.env*) ve
`git log --all -- .env` ile dogrulandi - bu dosya HICBIR ZAMAN git'e commit
edilmemis, sizinti yok. Deger bu kayda veya baska hicbir committed dosyaya
yazilmadi.
Durum: 10/15 tamamlandi ve dogrulandi; 5/15 + 3E.7/3E.8/3E.9 Meric karari
bekliyor.

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

- P0-a) Yasal sayfalar (Impressum + Datenschutz + AGB) YOK — Avusturya yasal zorunluluğu. Sahip: —, Tarih: —
- P0-b) SMTP sızan şifre rotate edilmedi (güvenlik). Sahip: —, Tarih: —
- P0-c) Traction ~0 (tg_users=1, feedback=0) — gerçek davet + teslim serisi. Sahip: —, Tarih: —
- P0-d) Premium/Stripe hiç test edilmedi (gelir=0). Sahip: —, Tarih: —
- P0-e) Site mesajı "AI stock" (compliance+repositioning riski) → literacy çerçevesi. Sahip: —, Tarih: —

Nihai değerlendirme: kamuya lansman HENÜZ DEĞİL; soft-launch koşullu.

[2026-07-28] — Yayın hattı kararları (Telegram+Web ön-taraması sonrası)

- Web deploy: git commit+push (publish_web.py → WEB_PUBLISH_CMD; REQUIRE_VERCEL_DEPLOY=0). Snapshot git'te izlenir, Vercel push'ta deploy eder.
- Scan: her sabah elle scan + publish_now (oto-taslak + insan onayı). DISTRIBUTION=0 kalır.
- Kanal adı @Finpilot_Breif ("Brief" yazım hatası) ŞİMDİLİK KORUNUR — lansmana kadar takipçi sıfırlamamak için; lansman öncesi yeniden değerlendir.

Durum: uygulandı (Meriç kararı, 2026-07-28); publish_web.py eklendi.

[2026-07-29] — Tek-dokunuşla yayın DOĞRULAMA (Faz 1): plan devrede DEĞİL — KOVA C açıldı (pending, P0)
Faz 1 bulgusu: web-deploy kancası ayarsız, bot-süpervizör dosyaları eksikti, waitlist aynası/admin-key/akademi-export ayarsız, hiçbir uçtan-uca tur doğrulanmadı.
KOVA C (kapanana dek AÇIK, Faz 3 kilitli):

- C1) FINPILOT_WEB_PUBLISH_CMD ayarsız → web yayını çalışmaz. Sahip: —, Tarih: —
- C2) Bot-süpervizör dosyaları eksikti → run_bot.py+start_bot.bat YENİDEN OLUŞTURULDU (bu oturum); startup+gözlem: —
- C3) WAITLIST_WEBHOOK_URL ayarsız → veri kaybı riski. Sahip: —, Tarih: —
- C4) SMTP rotasyonu doğrulanamadı (güvenlik P0). Sahip: —, Tarih: —
- C5) Uçtan-uca tam tur doğrulanmadı → kabul kriteri karşılanmadı. Sahip: —, Tarih: —

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

---

[2026-08-02] — FinPilot-native Control Center, Claude Cowork ve repo-native ortak beyin önerisi
Layer: Engineering / Operations / Agent Coordination
Level: B
Bağlam: Meriç'in ajanların ne yaptığını, blokajları, bekleyen onayları ve kanıt özetlerini tek yüzeyde izleyeceği bir yönetim kokpiti bulunmuyor. VS Code ana mühendislik ortamı olmasına rağmen ortak Work Item/Handoff task yüzeyi ve workspace konfigürasyonu da yok. GitHub Copilot, Claude Code, Claude Cowork ve FinPilot ürün ajanları aynı proje üzerinde çalışsa da geliştirme ve araştırma işi için ortak `work_item_id`, sahiplik, devir, kanıt ve onay geçişi sözleşmesi bulunmuyor. Mevcut Redis agent state/events kısa ömürlü; signal events ise finansal sinyal yaşam döngüsüne özel. Mevcut Next.js dashboard, auth context, otonomi onay/audit yüzeyi ve FastAPI admin endpoint kalıpları FinPilot-native bir kontrol merkezi için yeniden kullanılabilir.
Değişiklik (önce/sonra): v0.3 taslağında Buzz Meriç'in Control Cockpit'i olarak önerilmişti. Önerilen v0.4 modelinde FinPilot web uygulamasındaki ayrı ve default-deny `/ops` alanı Meriç'in Control Center'ı; VS Code Engineering Workbench; repo kalıcı Shared Brain / Source of Truth; GitHub Copilot ve Claude Code tek-owner kurallı kod yürütücüleri; Claude Cowork kaynaklı araştırma, doküman/korpus ve operasyon yürütücüsüdür. Work Item + Handoff + Evidence araç-bağımsız sözleşmedir. Control Center önce read-only projeksiyon ve raporlarla açılır; geri yazma yalnız temiz pilot ve ayrı onay sonrasında kimlik doğrulanmış, allowlist'li intent olarak değerlendirilir. Buzz ana cockpit değildir; yalnız ihtiyaç kanıtlanırsa bildirim adaptörü olabilir. Ayrıntılı taslak ve fazlar `docs/2026-08-02-ortak-beyin-handoff-buzz-claude-yol-plani.md` içindedir. Bu kayıt uygulama veya mimari onay değildir.
Etki: Onaylanırsa yeni şema/CLI, `/ops` layout ve ekranları, Control API/projector/reconciler, kontrol panoları ve raporlar, `.vscode/tasks.json`, sınırlı extension önerileri, Copilot/Claude Code/Claude Cowork protokolü ve CI evidence köprüsü eklenir. Controlled intent ve Local Agent Bridge ayrı ve ayrıca onaylanan kapılardır. Scanner, distribution, publish, risk, secrets, deploy ve broker/emir davranışı bu öneriyle değişmez; bu alanlar mevcut insan kapılarında kalır ve Control Center tarafından çağrılamaz.
Durum: pending — Level B; Meriç mimari onayı bekleniyor. Uygulama yapılmadı.

---

[2026-08-07] — DURUM.md / LAUNCH_CHECKLIST.md seri+karne sayıları bayattı, canlı DB'ye karşı düzeltildi (Level A, dokümantasyon)
Layer: Documentation / governance
Level: A
Bağlam: Sabah nabzı sırasında DURUM.md ve LAUNCH_CHECKLIST.md'deki "10 ardışık işlem günü" sayacı (~2/10, 23-24 Tem) ve karne madde 5 durumu ("ilk dolu yayın bekleniyor, 25 Tem") 24 Temmuz'dan beri güncellenmemiş bayat notlardı. `distribution.db` (`broadcast_queue`) ve `data/distribution/snapshot_*.json` dosyalarına karşı doğrudan doğrulandı.
Bulgular: (1) `distribution.broadcast.publish_streak()` canlı DB'ye karşı çalıştırıldı → sonuç 4, 2 değil. 3-6 Ağu ardışık `sent`; seri en son 31 Tem'de kırılmış (o gün broadcast_queue'da hiç kayıt yok — taslak bile üretilmemiş), 20-22 Tem'deki eski "expired" kırılmasından ayrı, ikinci bir kopma. (2) Karne `overall` bloğu (bariyer-tabanlı beklenti +%0.40/işlem, %30.1 isabet, 3.36x asimetri, n=5206) aslında 28 Tem'den beri her yayında dolu — "ilk dolu yayın bekleniyor" notu yanlıştı, milestone zaten geçilmiş. `by_grade` ise gerçekten yeni doluyor: 3 Ağu'ya kadar boş, 4-6 Ağu'da B/C'de küçük örneklemle veri geldi (6 Ağu: B n=4, C n=2, A yok, ikisi de hit_rate 0.0 — düşük isabet/pozitif-skew profiliyle tutarlı, kırmızı bayrak değil).
Değişiklik: DURUM.md "⭐ Bu 6 haftanın TEK önceliği" bölümündeki seri metriği ~2/10 → 4/10 ve kaynak/tarih notuyla güncellendi. LAUNCH_CHECKLIST.md madde 1 (seri sıfırlanma tarihi ve mevcut seri) ve madde 5 (karne overall/by_grade ayrımı) canlı bulgularla yeniden yazıldı.
Etki: Yalnız iki durum dosyasındaki sayı/not metni değişti. Scanner/distribution/skor/risk/canlı yayın davranışı DEĞİŞMEDİ — bu salt bir dokümantasyon düzeltmesi (repository health, CORE ilkesi: "repository should become more consistent after every interaction").
Durum: uygulandı — Meriç talebiyle ("güncelle", 2026-08-07). Level A (yalnız durum dosyaları, karar/kural değişikliği yok).
