# Scanner Derin Teknik Audit (Sert) — Kanıta Dayalı

**Tarih:** 2026-06-12 · **Yöntem:** `scanner/evaluate.py` (707 satır), `data_fetcher.py`, `features.py`, `earnings_blackout.py`, `catalyst.py`, `score_engine.py`, `config.py` satır-satır okuması. Her iddia dosya:satır referanslı. Nezaket değil doğruluk.

> **Uyarı:** Sistem-tasarımı denetimidir, yatırım tavsiyesi değildir.

---

## 1. EXECUTIVE VERDICT

Scanner **fonksiyonel ama mimari olarak "her şeyi tek fonksiyonda yap" hastalığına yakalanmış** ve **gizli per-symbol I/O yüzünden ölçeklenmiyor.** Çekirdek tarama (`evaluate_symbol`, 512 satırlık tek fonksiyon) discovery + scoring + risk + enrichment + earnings + sentiment + katalizör + erken-tier'ı **tek hot-path'te** birleştiriyor. OHLCV prefetch ile batch'lenmiş (iyi), ama eval içinde symbol başına **yfinance earnings takvimi + yfinance vol-regime download + altdata sentiment/onchain** çağrıları duruyor — yani "prefetch sonrası pure-pandas" iddiası (kod yorumu, satır 670) **yanlış.** Üstüne, **likidite ön-filtresi tüm pahalı işten SONRA** uygulanıyor (satır ~269-279): her tinsel penny-stock tam çok-zaman-dilimi indirilip tüm göstergeleri hesaplanıp, sonra eleniyor.

**Puan tablosu:**

| Lens | Puan | Gerekçe |
|---|---|---|
| System design | **Kötü** | 512 satırlık tanrı-fonksiyon; core/enrichment ayrımı yok |
| Data flow | **Orta** | OHLCV batch prefetch iyi; ama 2 provider karışık + side-channel fetch |
| Execution flow | **Kötü** | Pahalı iş → ucuz filtre sırası ters (prefilter inversiyonu) |
| Latency | **Kötü** | Gizli per-symbol yfinance/altdata I/O (N× network) |
| Throughput | **Orta** | ThreadPool var ama yanlış varsayımla boyutlandırılmış |
| API/I/O cost | **Kritik zayıf** | vol_regime redundant download; earnings/sentiment N+1 |
| Compute cost | **Orta** | Çoğu pandas vektörel; momentum analizi ağır ama makul |
| Correctness | **Orta-iyi** | try/except her yerde → crash yok ama sessiz-0 riski |
| Signal quality | **Kötü (kanıtlı)** | Kendi audit'i: decile_lift 0.728, edge yok |
| Operability | **Kritik zayıf** | Per-stage latency/cache-hit/filter-drop ölçümü YOK |
| Extensibility | **Orta** | Env-gated faktör deseni iyi; ama tek dosyada birikiyor |
| Failure modes | **Orta** | try/except dayanıklı ama sessiz kısmi-sonuç riski |
| Technical debt | **Yüksek** | 75+ alanlı return dict, magic number bolluğu, tanrı-fonksiyon |
| Product fitness | **Orta** | Zengin çıktı ama "değer" değil "liste"; edge kanıtsız |

**Tek cümlelik karar (bkz. §12):** Hızlı prototip olarak çalışıyor, ama **ölçeklenmeye ve edge iddiasına bugünkü haliyle güvenilmez** — çünkü ne ölçülüyor ne de doğru katmanlanmış.

---

## 2. SCANNER GERÇEKTE NE YAPIYOR?

**İddia edilen:** likit US hisselerinde çok-zaman-dilimli teknik tarama → skorlu shortlist.

**Fiilen yaptığı:** `evaluate_symbol` symbol başına: (1) 4 zaman dilimi OHLCV al (prefetch varsa hazır), (2) trend/momentum/hacim skoru, (3) çok-zaman-dilimi hizalama + confluence, (4) alpha-v2 faktörleri (gap/rvol/extension/atr), (5) likidite kontrolü, (6) risk yönetimi (Yang-Zhang/ATR stop/tp), (7) **rejim tespiti**, (8) **altdata sentiment + onchain** (per-symbol), (9) **earnings blackout + proximity** (per-symbol yfinance), (10) **vol_regime** (per-symbol yfinance download), (11) katalizör (cache), (12) lottery/overnight/squeeze faktörleri, (13) kompozit skor + rejim-gate, (14) dinamik pozisyon boyutu, (15) risk-ayarlı metrikler (Sharpe/Sortino/Calmar), (16) conviction tier, (17) erken-tier. → **75+ alanlı dict.**

**Teşhis: bu bir scanner değil, "tek fonksiyona yığılmış hibrit motor."** Discovery (aday bulma), scoring, risk hesabı, enrichment (sentiment/earnings/katalizör), açıklama ve pozisyon-boyutlandırma **tek `evaluate_symbol` içinde iç içe.** Scope creep kanıtlı: bir sinyal-bulucunun Sharpe oranı ve Kelly boyutu hesaplaması gerekmez — bunlar enrichment/execution katmanının işi.

---

## 3. EN KRİTİK MİMARİ KUSURLAR

**Kusur #1 — Prefilter inversiyonu (P0).** Likidite/fiyat filtresi (`min_price=2`, `min_avg_vol=300k`) satır ~269-279'da, yani **tüm çok-zaman-dilimi fetch + tüm gösterge hesabı + momentum analizi + hizalama + confluence + alpha faktörlerinden SONRA** uygulanıyor. Ucuz eleme (`price_ok`, `avg_vol_ok` — tek OHLCV satırı yeter) en pahalı işten sonra çalışıyor. **Sonuç:** likidite tabanının altındaki her sembol için boşa harcanan tam fetch + hesap. Delisted filtresi prefetch'ten önce (satır 639, iyi) ama likidite değil.

**Kusur #2 — "Pure-pandas" yalanı + gizli per-symbol I/O (P0).** Satır 670 yorumu: *"evaluate_symbol is CPU-light after prefetch (pure pandas)"*. **Yanlış.** Eval içinde symbol başına: `get_sentiment_score`+`get_onchain_metric` (satır 319-320, altdata), `is_earnings_blackout`+`earnings_proximity` (satır 338-339, **yfinance `ticker.calendar`**, `earnings_blackout.py:36`), `get_alpha_features`→`compute_vol_regime` (satır 353 → **yfinance.download 2mo**, `features.py`). Yani prefetch OHLCV'yi batch'liyor ama eval **N× ek network çağrısı** yapıyor. Worker sayısı (`_eval_workers = min(32, max(4, total))`, satır 672) "CPU-light pandas" varsayımına göre — gerçek I/O profiline göre değil.

**Kusur #3 — Redundant veri çekme (P0).** `compute_vol_regime(symbol)` yfinance'ten 2 aylık günlük indirip yıllık vol hesaplıyor — **oysa `df_1d` (200+ günlük bar) zaten elde.** Aynı hesap `df_1d`'den tek satırda yapılabilir. 1 saat cache var ama her saatin ilk taraması N× gereksiz download ödüyor. Aynı şekilde earnings takvimi de df'te olmayan ayrı bir yfinance çağrısı.

**Kusur #4 — İki provider, karışık (P1).** OHLCV Alpaca-bulk (→ yfinance fallback) ile prefetch; ama vol_regime + earnings doğrudan yfinance per-symbol. Prefetch optimizasyonu bu yan-kanal fetch'lerle bypass ediliyor. Tek tutarlı provider soyutlaması yok.

**Kusur #5 — Tanrı-fonksiyon (P1).** `evaluate_symbol` 512 satır, 75+ çıktı alanı. Core scan ile enrichment ayrılmamış. Her yeni faktör (alpha_v2, conviction, tier) bu dosyaya ekleniyor — dosya lineer büyüyor, test izolasyonu imkânsız.

---

## 4. NEDEN YAVAŞ? (kök neden)

| # | Belirti | Teknik kök neden | Nasıl doğrulanır | Etki | Çözüm |
|---|---|---|---|---|---|
| 1 | Tarama süresi sembol sayısıyla süper-lineer | Likidite prefilter en sonda → elenmesi gereken semboller de tam işleniyor | Universe'ün %X'i likidite-altı say; onlara harcanan fetch+compute süresini logla | Yüksek | Prefilter'ı prefetch ÖNCESİNE al (fiyat/hacim/mktcap) |
| 2 | Prefetch hızlı ama toplam yavaş | Eval içinde per-symbol yfinance (earnings+vol_regime) + altdata (sentiment+onchain) → N× network | Eval'i cProfile/py-spy ile profille; network vs pandas süresini ayır | Yüksek | vol_regime'i df_1d'den hesapla; earnings/sentiment'i batch/prefetch veya cache-önden |
| 3 | Her saatin ilk taraması diğerlerinden yavaş | vol_regime + earnings 1h/6h cache → cache-cold ilk tarama N× download | İki ardışık taramanın süresini kıyasla | Orta | Cache'i scheduler job'la önden doldur (catalyst gibi) |
| 4 | Thread sayısı arttıkça beklenen hızlanma gelmiyor | Worker sizing "pure pandas" varsayımına göre; gerçek iş I/O-bound + GIL | Worker=8 vs 32 ile süre kıyası | Orta | I/O'yu asyncio'ya al veya eval'i gerçekten pandas-only yap |
| 5 | Momentum analizi ağır | `analyze_price_momentum` çoklu-pencere z-score + dinamik kuantil her sembol her scan | Bu fonksiyonun tek-symbol süresini ölç | Düşük-orta | Vektörelleştir / pencere sonuçlarını önbellekle |

**Ayrım (özel kural):** Bu bir **I/O + orchestration** problemi, compute değil. Compute (pandas) büyük ölçüde makul. Sorun: (a) yanlış sırada filtre (orchestration), (b) hot-path'te gizli network (I/O), (c) redundant fetch (I/O). CPU değil.

---

## 5. VERİ KULLANIM KUSURLARI

| Veri | Kullanım | Konum | Doğru mu? |
|---|---|---|---|
| Daily OHLCV | Trend/skor/momentum/risk çekirdeği | Prefetch (Alpaca/yf) | ✅ Doğru katman |
| Intraday 15m/1h/4h | Hizalama + confluence + ATR | Prefetch | ✅ ama 4 zaman dilimi her sembol — pahalı; hizalama için 1h+4h yeter mi? sorgula |
| Relative volume | volume_spike + alpha_rvol | df_1d'den | ✅ |
| Gap / premarket | compute_gap_factor | df_1d'den | ⚠️ gerçek premarket değil, günlük gap proxy |
| Float / short | squeeze_factor | features (yfinance .info, **gated OFF**) | ⚠️ Stale proxy; çekirdekte değil |
| Earnings/event | blackout + proximity | **per-symbol yfinance calendar** | ❌ Yanlış katman — hot-path network, enrichment olmalı |
| News/catalyst | catalyst_factor | Cache dosyası (scheduler doldurur) | ✅ **Doğru desen** (tek örnek) |
| Options/IV/OI | — | Yok | ❌ Eksik |
| Sentiment/social | get_sentiment_score | **per-symbol altdata, hot-path** | ❌ Yanlış katman |
| vol_regime | momentum ağırlığı | **per-symbol yfinance download** | ❌ Redundant — df_1d'den hesaplanmalı |
| Sector context | sector_rs | `get_alpha_features(symbol)` **sector=None** → hep 0.0 | ❌ Fiilen ölü (hiç sektör geçilmiyor) |
| Regime | detect_market_regime | per-symbol df_1d | ⚠️ Sembol-bazlı rejim; piyasa rejimi bir kez hesaplanmalı |

**En sert bulgu:** `sector_rs` çağrısı `get_alpha_features(symbol)` ile sektör argümanı olmadan yapılıyor → `compute_sector_rs("")` erken 0.0 dönüyor. Yani **sektör göreli-güç özelliği kodda var ama fiilen hep 0** — ölü kod, çıktı alanı olarak duruyor.

---

## 6. ALGORİTMA / FİLTRE / RANKING KUSURLARI

- **Giriş kapısı heuristik yığını:** `entry_ok = score==3` (RSI 30-70 + hacim>med×1.2 + MACD histogram artan) — üç gecikmeli gösterge AND'i. Alpha-v2 modu (gated) bunu gap/rvol/atr tetikleyicisine çeviriyor ("lift 1.49, recall %60" yorumu, satır 240) — ama bu iddia backtest-içi, out-of-sample doğrulaması gösterilmemiş.
- **Kompozit skor edge üretmiyor (kanıtlı):** Profit Core audit decile_lift 0.728 (ters). Skor "anormal görüneni" topluyor, alpha'yı değil.
- **Ranking açıklanabilir ama gerekçesiz ağırlıklı:** `score_engine` sabit ağırlıklar (regime 2, direction 2, alignment×2, momentum×{2.5/2/1.5}...) — bu ağırlıklar barrier-audit'le kısmen kalibre ama çoğu sezgisel ("heuristic debt").
- **Yapısal körlük:** Likidite tabanı ($2, 300k) mikro-kap patlamalarını dışlıyor; options/OFI yok → squeeze/gamma setup'ları görünmez; sektör-relative fiilen ölü → izole spike filtresi çalışmıyor. Yani araştırma dosyalarının hedeflediği patlama-öncesi setup'ları **yapısal olarak göremiyor.**

---

## 7. GÜÇLÜ YÖNLER (yalnızca gerçek olanlar)

- **OHLCV batch prefetch** (`prefetch_symbols_multi_timeframe`, max_workers=10) — OHLCV tarafında N+1'i çözmüş; doğru desen.
- **Katalizör cache deseni** (`catalyst.py`: scheduler önden doldurur, hot-path yalnız okur) — **sistemdeki en doğru veri-katmanı deseni**; earnings/sentiment de tam olarak bunu taklit etmeli.
- **Env-gated faktör deseni** — yeni sinyaller (squeeze/lottery/overnight/alpha_v2/tier) canlı skoru bozmadan eklenebiliyor; ölçüm-önce disiplinine uygun.
- **Dayanıklı hata yönetimi** — her aşama try/except; tek sembol/tek alan patlaması taramayı çökertmiyor (ama sessiz-0 riski, §8).
- **Delisted prefilter** — prefetch öncesi eleme (satır 639) doğru konumda.
- **Volatilite-ölçekli risk** (Yang-Zhang/ATR stop-tp) — sabit yüzde kullanmıyor; sağlam.

Bunlar korunmalı; refactor bunları bozmadan yapılmalı.

---

## 8. FAILURE MODES VE GİZLİ TEKNİK BORÇ

- **Sessiz-0 / sessiz kısmi sonuç:** Her aşama try/except → bir sembol için earnings/sentiment/vol_regime network fail olursa alan sessizce 0/varsayılan olur, skor "başarılı" görünür ama eksik girdiyle hesaplanır. Loglar debug seviyesinde → operatör fark etmez. **"Scan başarılı görünüp anlamsız output döner" senaryosu gerçek.**
- **Provider yavaşlarsa:** yfinance earnings/vol_regime yavaşlarsa 32 thread'in her biri bloklanır; timeout politikası eval-içi çağrılarda görünmüyor → tarama süresi provider'a rehin.
- **Stale cache riski:** vol_regime 1h, earnings 6h cache — piyasa saatlerinde earnings tarihi değişirse 6 saat eski karar.
- **Teknik borç:** 512 satır tanrı-fonksiyon; 75+ alan return dict; magic number bolluğu (min_score 3, ×1.2, ×0.5, DD %3, worker 32, TTL'ler); ölü `sector_rs`; ölü `is_premium_symbol` (yorumda "no-op" kabul edilmiş ama alan hâlâ dönülüyor); iki paralel skor kavramı (score vs composite vs conviction vs tier — dört ayrı "iyilik" ölçüsü).

---

## 9. EKSİK ÖLÇÜM / TELEMETRY (en sert bölüm)

Kanıt: `evaluate_symbols_parallel` yalnız iki log üretiyor — "Prefetching N symbols" ve "complete N/M results". **Yok olanlar:** total scan latency, per-stage latency (fetch vs momentum vs risk vs enrichment), per-provider latency (Alpaca vs yfinance vs altdata), per-symbol cost, cache hit-rate (vol_regime/earnings/catalyst), rate-limit impact, fail/timeout ratio, **filter drop-off** (hangi filtre kaç sembol eliyor), ranking stability, false-positive ratio, missed-opportunity.

**Verdict:** Bu sistem **ölçülmüyor; tahmin edilerek kurcalanıyor.** "3.7x hızlanma" gibi commit iddiaları per-stage profil olmadan yapılmış. İyileştirmenin önce-şartı: (1) her stage'e `time.perf_counter` + yapılandırılmış log, (2) filter drop-off sayaçları, (3) cache hit-rate, (4) per-provider latency histogramı → dashboard "Scanner Sağlığı" kartı. Ölçüm kurulmadan yapılan her optimizasyon kör.

---

## 10. İYİLEŞTİRME PLANI (P0/P1/P2/P3)

**P0 — Derhal (yanlış mimari + kör nokta):**
1. **Prefilter'ı öne al:** universe → fiyat/hacim/mktcap/delisted ucuz elemesi → SONRA prefetch+eval. Likidite-altı semboller hiç fetch edilmesin. *(Yüksek etki / düşük efor)*
2. **vol_regime'i df_1d'den hesapla** — yfinance download'ı kaldır. *(Yüksek etki / düşük efor)*
3. **Per-stage + per-provider latency + filter drop-off telemetry** ekle. Ölçüm olmadan gerisi kör. *(Yüksek etki / orta efor)*
4. **Sessiz-0 guard:** enrichment fail olduğunda alanı "eksik" işaretle (0 değil), skoru "eksik-girdi" etiketle. *(Orta / düşük)*

**P1 — Yüksek değer:**
5. **Earnings + sentiment'i cache-önden-doldur** (catalyst deseni): scheduler job doldurur, hot-path yalnız okur → per-symbol yfinance/altdata I/O hot-path'ten çıkar. *(Yüksek / orta)*
6. **Ölü sector_rs'i ya düzelt (sektör geç) ya kaldır.** *(Orta / düşük)*
7. **Piyasa rejimini bir kez hesapla** (per-symbol değil) — scan başında bir defa, tüm sembollere paylaştır. *(Orta / düşük)*
8. **Edge Report'u tier/faktör bazında çalıştır** (zaten inşa edildi, `scanner/edge_report.py`) → hangi kural gerçekten katkı veriyor ölç. *(Yüksek / orta)*

**P2 — Orta vadeli mimari:**
9. **Core scan ↔ enrichment ayrımı:** `evaluate_symbol`'ü ikiye böl — `scan_core` (ucuz, pandas-only: trend/momentum/skor/likidite) + `enrich` (sentiment/earnings/risk-metrik/tier, yalnız çekirdeği geçenlere). *(Yüksek / yüksek)*
10. **Feature store / precompute:** vol_regime, sector_rs, squeeze, earnings → offline hesaplanıp okunur. Online sadece OHLCV-türevi. *(Yüksek / yüksek)*
11. **Tek provider soyutlaması** (Alpaca-birincil, yfinance-yalnız-fallback, yan-kanal fetch yok). *(Orta / orta)*

**P3 — Sonra:**
12. Açıklanabilir çıktı ("neden öne çıktı" + confidence), UI tier rozeti, FinSense öğretici bağlantısı. *(Orta / orta)*

**Etki/zorluk matrisi:**
- **High impact / low effort (ÖNCE):** #1 prefilter, #2 vol_regime, #4 sessiz-0, #6 sector_rs, #7 rejim-bir-kez.
- **High impact / high effort:** #3 telemetry, #5 cache-önden, #9 core/enrich ayrımı, #10 feature store.
- **Low impact / low effort:** magic number → config.
- **Low impact / high effort:** tam event-driven pipeline (şimdilik gereksiz).

---

## 11. MEVCUT vs OLMASI GEREKEN

| Alan | Mevcut Durum | Olması Gereken | Açık |
|---|---|---|---|
| Universe selection | Delisted elenir; likidite EN SONDA | Fiyat/hacim/mktcap/delisted PREFETCH öncesi | Prefilter inversiyonu (P0) |
| Data fetch | OHLCV batch + per-symbol yfinance/altdata yan-kanal | Tek provider, tüm veri prefetch/cache | Gizli N+1 (P0) |
| Caching | vol_regime 1h, earnings 6h, catalyst dosya | Hepsi scheduler-önden-doldurulmuş | Cache-cold ilk-scan cezası (P1) |
| Feature computation | Hot-path'te (vol_regime yfinance dahil) | Offline feature store + online yalnız OHLCV-türevi | Redundant compute+fetch (P2) |
| Filtering order | Pahalı→ucuz (ters) | Ucuz→pahalı (kademeli) | Kök yavaşlık (P0) |
| Ranking | Sabit-ağırlık kompozit, edge yok | Edge-ölçülü, ablation-doğrulanmış | Heuristic debt (P1) |
| Enrichment | Core ile iç içe (tek fonksiyon) | Ayrı katman, yalnız çekirdeği geçene | Tanrı-fonksiyon (P2) |
| Observability | 2 log satırı | Per-stage/provider latency + drop-off + cache-hit | "Kör kurcalama" (P0) |
| Fault tolerance | try/except sessiz-0 | Eksik-girdi işaretli, alarmlı | Sessiz yanlış sonuç (P0) |
| Scan latency | Ölçülmüyor | Bütçeli + izlenen | Ölçüm yok |
| Signal quality | decile_lift 0.728 (edge yok) | Ablation-doğrulanmış pozitif beklenti | Kanıtlı zayıf |
| Extensibility | Env-gated iyi ama tek dosyada | Katmanlı + feature store | Birikim borcu |

---

## 12. SON KARAR: BU SCANNER BUGÜNKÜ HALİYLE NE KADAR GÜVENİLİR?

**Operasyonel güvenilirlik: orta.** try/except sayesinde çökmüyor, sonuç üretiyor — ama sessiz-0 nedeniyle **"başarılı ama eksik-girdiyle hesaplanmış" sonuç** üretebiliyor ve bunu operatör göremiyor (telemetry yok).

**Performans güvenilirliği: düşük.** Prefilter inversiyonu + gizli per-symbol I/O + redundant vol_regime download yüzünden sembol sayısıyla kötü ölçekleniyor; "hızlı" iddiaları ölçümsüz.

**Sinyal güvenilirliği: düşük (kanıtlı).** Kendi audit'i edge bulamadı (decile_lift 0.728). Skor "anormal görüneni" topluyor, kanıtlı alpha'yı değil.

**Karar:** Scanner bir **çalışan prototip** — araştırma/paper için kullanılabilir, ama **(a) ölçeklenmeye, (b) edge iddiasına, (c) sessiz-hata yokluğuna güvenilmez.** Önce ölçüm (P0-#3) + prefilter (P0-#1) + vol_regime fix (P0-#2) + sessiz-0 guard (P0-#4) yapılmadan hiçbir "hızlandık/iyileştik" iddiası doğrulanamaz. İyi haber: kusurların çoğu **yüksek-etki/düşük-efor** ve mimari deseni (catalyst cache, env-gated faktör, batch prefetch) doğru yöne işaret ediyor — yani düzeltilebilir, yeniden-yazım gerektirmez.
