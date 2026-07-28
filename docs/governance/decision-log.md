# FinPilot — Merkezi Karar Logu
_CLAUDE.md Bölüm 3 formatı: her önemli karar buraya, dağınık dosyalara gömülmez._
_Not: docs/INDEX.md şu an eski bir README kopyası — gerçek "tek doğru kaynak" indeksi Bölüm 5'te kurulacak ve bu loga bağlanacak._

---

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
