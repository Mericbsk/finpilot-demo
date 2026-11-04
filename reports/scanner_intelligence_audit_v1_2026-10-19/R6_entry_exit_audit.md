# R6 - Giris ve Cikis Mekanigi Denetimi (Entry/Exit Audit)

- Versiyon: v1
- Tarih: 2026-10-19
- Durum: DRAFT - Level A arastirma ciktisi; karar degildir
- HEAD: 93ae83c (branch `review/pending-2026-10-07`); calisma agaci kirli (kullanici + diger ajanlar), dokunulmadi
- Rol: Execution and Market Microstructure - entry and exit audit (brief WP-6, WP-7, WP-8 maliyet kismi); PREFIX `ENX`
- Kapsam: giris sinyali olusumu, fiyat tanimlari, cikis mekanigi, gunluk bar yol istatistikleri (yalniz kilitli olmayan veri), maliyet bilesenleri, PRIOR kanit ozeti, test edilebilir hipotezler
- Girdiler: kod (`scanner/`, `core/`, `api/`, `research/`), `data/finpilot.db` (salt-okunur, `mode=ro` + `PRAGMA query_only=ON`), yerel gunluk OHLCV onbellegi (SHA-256 asagida), PRIOR raporlar (Bulgu PRIOR bolumu)
- Kanit etiketleri: MEASURED, REPRODUCED, SUPPORTED, HYPOTHESIS, UNRESOLVED, NOT_MEASURABLE, CONTRADICTED
- D7 (2026-10-16): hicbir mevcut veri seti out-of-sample sayilmaz; bu rapordaki hicbir sonuc OOS degildir.

## Ozet

Brief'in 7 teslimatinin tamami ele alindi; eksik kalan kontroller "Sinirlamalar" bolumunde.

- **Giris (ENX-02, ENX-03):** `entry_ok` = gunluk bar RSI/hacim/MACD 3/3 + rejim + yon + likidite + piyasa guvenligi + bilanco karartmasi. Coklu-zaman-dilimi hizalamasi kapida yok; `watch_tier.py:12` aksini yaziyor (CONTRADICTED). Sinyal fiyati son 15m `Close`; kapanmis/olusmakta bar ayrimi yok (SUPPORTED/UNRESOLVED). Likidite kapisi istisnada acik kaliyor.
- **Arsiv zamani (ENX-01, ENX-08):** `ts` satirlarin %31.6'sinda sinyal gunu degil (MEASURED). Cozucu once `ts`'yi capa aliyor; saklanan etiketler capa-farkli alt kumede `ts` capasiyla %98.3, sinyal-tarihi capasiyla %69.1 yeniden uretiliyor (REPRODUCED, P0).
- **Cozucu (ENX-05, ENX-06):** giris = `payload.entry_price`; 21 islem gunu; TP-oncelikli ayni-bar kurali; gap'te bile seviye fiyatindan cikis; yfinance `auto_adjust=True`. Watchlist performans raporu farkli pencere kullaniyor (SUPPORTED).
- **Populasyon (ENX-11):** arsivde yalniz 6 satir `entry_ok=True`; 591 tekrar satir; ardisik sinyallerin %81.6'si 7 gun icinde (MEASURED, P0).
- **Cikis (ENX-07, ENX-09):** uretim yolu gunluk Yang-Zhang sigma x momentum-kademe carpanlari; trailing/kismi/ters-sinyal cikisi uretimde yok. Arsiv geometrisi (stop medyani 0.313 gunluk ATR; R/R 2.0 kumesi %36.8) mevcut formulle uyumsuz gorunuyor (MEASURED + HYPOTHESIS).
- **Yol (ENX-10, gunluk yaklasim):** ilk temas %74.9 ilk seansta; kayiplarin %32.7'si gap-through-stop (acilis-bazli medyan -0.746 puan ek); kazanclarin %12.6'si ayni-bar belirsiz.
- **Maliyet/icra (ENX-04, ENX-12, ENX-13):** 14 emir, 0 dolum; spread verisi yok; maliyet kurallari birbirinden farkli. Net sonuc olculemez (NOT_MEASURABLE). $2 alti satirlarda stop medyani <= 9 tick.
- Hicbir sonuc OOS degildir (D7); tum getiriler brut ve maliyetsizdir.

## Kapsam ve yontem

- **Salt-okunur:** kod okuma (`scanner/`, `core/`, `api/`, `distribution/`, `scripts/resolve_open_signals.py`); iki script (`scripts/ENX_probe.py`, `scripts/ENX_paths.py`); DB `mode=ro` + `PRAGMA query_only=ON`. Ag cagrisi, scanner calistirma, uretim/veri yazimi yok.
- **Kilit politikasi:** `docs/governance/decision-log.md:53-60` (D7: 2026-05-21 locked OOS ve PIT holdout OOS sayilmaz) ve `reports/oos_status_c_remediation_v1_2026-10-15/oos_status_c_remediation_plan.md:61-63` (C1 locked OOS sinir 2026-05-21; C5 PIT holdout 2026-06-09..06-30; C6 fixed-target holdout, bolumler tutarsiz). Sonuc ve yol istatistikleri yalniz `payload.signal_date <= 2026-05-21` satirlarinda (5,687) hesaplandi; sonrasi 61 satir yalniz sayildi; PIT penceresinde arsiv satiri 0. C6 farkli veri setinde tanimli; bu arsivle kesisimi UNRESOLVED. `watchlist_signals` sonuc durumlari (cogu 2026-05-21 sonrasi) raporlanmadi.
- **Yaklasim:** gunluk bar; intrabar sira bilinmiyor; tum getiriler brut ve maliyetsiz; "net" veya "beklenti" ifadesi kullanilmadi; hicbir sonuc OOS degil.

## Bulgular

### B1 Giris sinyali olusumu (brief 10.1)

#### ENX-02 - `entry_ok` kapisi gunluk bar kosullarina dayaniyor; `timeframe_aligned` hesaplaniyor ama kapida kullanilmiyor

- **Priority:** P2 (model quality)
- **Konum:** `scanner/evaluate.py:evaluate_symbol:228-756` - 236-237 (`daily_dd_breached(threshold=0.03)` ise `None`), 252-253 (asgari bar: 15m>=15, 1h>=10, 4h>=15, 1d>=50), 258-270 (`regime = Close > ema200`, 200 bar yoksa ema50; `direction = Close > ema50`), 275-290 (`score` 0-3, hepsi `df_1d.iloc[-1]`/`iloc[-2]`: RSI 30-70; `Volume > 1.2*vol_med20`; `macd_hist > 0` ve artan), 345-347 (`check_timeframe_alignment(df_1h, df_4h, df_1d)`), 352-361 (`core_signal = regime and direction and score>=3`; `entry_ok = score == 3`), 371-384 (likidite: `min_price` varsayilan 2.0 [`Close.iloc[-1]`], `min_avg_vol` varsayilan 300,000 [`vol_avg10`]), 430-432 (`CURRENT_MARKET_STATUS["safe"]`), 443-447 (bilanco karartmasi `days_before=2, days_after=1`), 589-594 (`selection_eligible = entry_ok and execution_feasible`).
- **Veri kaynagi:** kod (calisma kopyasi, HEAD 93ae83c uzerinde; bu dosyanin HEAD'e gore kirli olup olmadigi Ek git status ciktisinda).
- **Yontem:** kaynak okuma (Ek C1 pencereleri + `scanner/evaluate.py` 114-351 okumasi).
- **Sonuc:** `entry_ok` atanan/degistirilen satirlar 88, 361, 369, 384, 431, 446 (574 ve 593 yalniz okur); hicbiri `timeframe_aligned`/`alignment_ratio` kullanmiyor (345-347'de hesaplanip ciktiya tasiniyor). Buna karsin `scanner/watch_tier.py:12` yorumu `entry_ok`'u "full multi-timeframe alignment" olarak tanimliyor ve `scanner/signals.py:492-493` `entry_ok` satirlarina "Trend+ Uyum+" metni uretiyor. Likidite kapisi istisnada acik kaliyor (373-374 ve 379-380: `except` sonrasi `price_ok = True`, `avg_vol_ok = True`); bilanco karartmasi istisnada sessizce atlaniyor (449-450 `except: pass`).
- **n:** kod izi (sayim yok)
- **Label:** SUPPORTED (kod izi; uretim davranisi olculmedi). `watch_tier.py:12` iddiasi: CONTRADICTED.
- **Sinirlamalar:** `get_setting`, `CURRENT_MARKET_STATUS`, `execution_contract` esikleri calisma zamani konfigurasyonuna bagli; config/`.env` okunmadi.
- **Alternatif aciklamalar:** hizalama siralama/secim katmaninda (`score_engine`, `watch_tier`) kullaniliyor olabilir; "Uyum" baska bir uyumu kastediyor olabilir.
- **Sonraki adim:** forward instrumentation kayitlarinda `entry_ok=True` iken `timeframe_aligned=False` orani; istisna-acik kapilarin kac kez tetiklendigini loglayan gozlem (Level B).
- **Onerilen kategori:** FIX_CANDIDATE (belge/metin hizalamasi) + RESEARCH_NEXT
- **Risk & Compliance notu (karar degil):** `scanner/signals.py:493` `entry_ok` satirlari icin "Alınır: ..." kalibi uretiyor; YONERGE §12 yasak-dil kapsamina denk dusebilir. Hangi yuzeye ulastigi bu rolde dogrulanmadi (UNRESOLVED).

#### ENX-03 - Sinyal fiyati ve zamani 15 dakikalik serinin son satirindan aliniyor; kapanmis/olusmakta bar ayrimi kodda yok

- **Priority:** P0 (validity)
- **Konum:** `scanner/evaluate.py:evaluate_symbol` 292 (`last_price = df_15m["Close"].iloc[-1]`), 293 (`atr_val = df_15m["atr"].iloc[-1]`), 279-288 (`df_1d.iloc[-1]` skor), 579 (`_signal_timestamp = df_15m.index[-1]`), 626 (`"price": round(last_price, 4)`), 633 (`"timestamp": _signal_timestamp`); `_feature_contract:155-225` yalniz zaman damgasi/yas hesaplar (174-178), bar dusurmez.
- **Veri kaynagi:** kod; PRIOR `reports/c2c_5d_label_entry_basis_2026-09-03.md:14`.
- **Yontem:** kaynak okuma.
- **Sonuc:** "signal price" = cikti alani `price` = son 15m barin `Close` degeri (arsivde `payload.entry_price`, bkz. ENX-05). Gun ici taramada `df_1d.iloc[-1]` ve `df_15m.iloc[-1]` olusmakta olan bar olabilir; gunluk hacim kosulu kismi gun hacmiyle degerlendirilir. `evaluate.py` icinde son bari atan mantik yok. PRIOR: research export'ta 20,561/100,496 satir (%20.5) intraday tarama (PRIOR).
- **n:** kod izi
- **Label:** SUPPORTED (kod); kapali/olusmakta durum uretimde: UNRESOLVED (saglayici davranisi ve tarama saati).
- **Sinirlamalar:** `scanner/data_fetcher.py` (1,758 satir) icinde `[:-1]|incomplete|partial|forming|is_closed|completed|drop_last|last_bar|in.progress|still open` aramasi yalniz Alpaca kismi-gecmis onarimi ve thread tamamlama satirlarini buldu; son-bar dusurme mantigi bulunmadi (desen aramasi, kapsamli degil; Ek C2 K bolumu).
- **Alternatif aciklamalar:** veri saglayici yalniz kapanmis bar donduruyor olabilir; EOD taramada sorun dogmaz.
- **Sonraki adim:** ayni sembol-gun icin intraday vs EOD taramada `score`/`entry_ok` degisim orani (forward kayit).
- **Onerilen kategori:** RESEARCH_NEXT

#### ENX-04 - Sinyal sonrasi akis kodda var (watchlist, Telegram, p_win>=0.65 otomatik onay, kagit pozisyon); gerceklesmis dolum kaydi yok

- **Priority:** P1 (economic-evaluation blocker)
- **Konum:** `api/routers/scan.py:229-253` (entry_ok/`selection_eligible` satirlari watchlist'e; 286-295 `entry_price = price`, `stop_loss`, `take_profit`, `risk_reward`); `core/scheduler.py:1013` (Telegram, `was_alert_sent`); `core/scheduler.py:_run_auto_approve_job:371-461` (390-391 `calibrated_probability(score) >= 0.65`; 400-410 `open_position(direction="BUY", entry_price=sig.price or close)`); `core/scheduler.py:run_cycle_once:752-768` (ikinci kagit pozisyon yolu); `core/paper_portfolio.py:31` (`data/paper_portfolio.json`); `api/routers/execution.py:52` (`FINPILOT_EXECUTION_MODE` varsayilan `dry_run`).
- **Veri kaynagi:** `data/finpilot.db` (SHA ENX-01'de); `data/` isim listesi.
- **Yontem:** salt-okunur tablo sayimlari (Ek C1).
- **Sonuc:** `alpaca_orders` 14 satir (side `buy` 14; status `OrderStatus.PENDING_NEW` 13, `OrderStatus.ACCEPTED` 1); `execution_intents`, `execution_events`, `trades`, `positions`, `outcomes_horizon`, `signals`, `buy_signals` 0 satir; `watchlist_signals` 1,158 satir. `data/` ust duzeyinde `paper_portfolio.json` yok. Otomatik onay `signals_archive` degil `core.kpi_tracker._load_all_signals` kaynagini okur.
- **n:** tablo satir sayilari yukarida
- **Label:** MEASURED (sayimlar, dosya yoklugu); akis: SUPPORTED (kod)
- **Sinirlamalar:** Redis/KPI deposu okunmadi (servis cagrisi yasak); `FINPILOT_EXECUTION_MODE` degeri `.env` okunmadan dogrulanamaz (brief gozlemi: `dry_run`).
- **Alternatif aciklamalar:** kagit pozisyonlar Redis'te olabilir; PRIOR (decision-log 2026-10-14 net expectancy kaydi) "Redis paper keys count is 0".
- **Sonraki adim:** dolum olmadan "realised fill" ve "first executable price" tanimsiz (ENX-05 tablosu).
- **Onerilen kategori:** NEEDS_MORE_DATA

#### ENX-11 - Arsiv populasyonu `entry_ok` populasyonu degil; tekrarlayan/cakisan sinyaller ayiklanmiyor

- **Priority:** P0 (validity)
- **Konum:** `data/finpilot.db:signals_archive.payload_json`; dedup aramasi `scanner/`, `core/`, `api/`, `distribution/` (Ek C1 `DEDUP`: yalniz `core/scan_coordinator.py:95-264` API-is dedupe ve `distribution/archive_bridge.py:10` gunluk idempotans); okuyan `scripts/ENX_paths.py:main` (M ve G bolumleri).
- **Veri kaynagi:** `data/finpilot.db` SHA-256 `b64c0c5262e0d685daa1309e6293d27c208f64a6fc213b3c00e3cb896bd5f5f6`.
- **Yontem:** payload anahtar kohortlari; `(symbol, signal_date)` tekrar sayimi; sembol bazinda ardisik farkli sinyal tarihleri arasi takvim gunu (Ek C2). Sonuc etiketi kullanilmadi.
- **Sonuc:** kohortlar: `entry_ok` anahtari olmayan 3,654; `entry_ok` anahtarli 2,065 (False 2,059, True 6); `grade` anahtarli 29. Ayni `(symbol, signal_date)` icin >1 satir: 468 grup, 591 fazla satir (194 grupta seviyeler ozdes). Ardisik farkli sinyal tarihleri arasi: <=1 gun %33.3 (1,342/4,033), <=7 gun %81.6, <=14 gun %83.7. `entry_price < 2.0` satirlari 142 (tamami `entry_ok` anahtari olmayan kohortta, %3.9); `entry_ok` kapisindaki `min_price` 2.0 varsayilaniyla tutarsiz. Sinyal tarihi ay dagilimi: 2025-09 1,579; 2025-10 580; 2025-11 6; 2025-12 6; 2026-02 1,533; 2026-03 892; 2026-04 179; 2026-05 944; 2026-07 8; 2026-08 11; 2026-09 10 (2026-01 ve 2026-06 yok).
- **n:** 5,748
- **Label:** MEASURED
- **Sinirlamalar:** hangi yazicinin hangi kohortu urettigi kodla eslestirilmedi; `entry_ok` anahtarinin yoklugu `entry_ok=False` anlamina gelmeyebilir.
- **Alternatif aciklamalar:** arsiv bilincli olarak watchlist/conviction-tier adaylarini da kapsiyor olabilir (`api/routers/scan.py:641` aday havuzu "entry_ok VEYA conviction_tier A/B/C").
- **Sonraki adim:** karne/kamu metriklerinde populasyon tanimi (hangi kohort, tekrarlar dahil mi) acik yazilmali; tekrar-ayiklanmis (symbol, signal_date) varyanti raporlanmali.
- **Onerilen kategori:** FIX_CANDIDATE

<!-- B1 -->

### B2 Fiyat tanimlari ve sonuc cozucu (brief 10.2)

#### ENX-01 - `signals_archive.ts` sinyal tarihi degildir: satirlarin %31.6'sinda `payload_json.signal_date` farkli gun

- **Priority:** P0 (validity)
- **Konum:** `data/finpilot.db` -> `signals_archive.ts` ve `signals_archive.payload_json["signal_date"]`; okuyan: `scripts/ENX_probe.py:run_c`
- **Veri kaynagi:** `data/finpilot.db` (7,811,072 bayt), SHA-256 `b64c0c5262e0d685daa1309e6293d27c208f64a6fc213b3c00e3cb896bd5f5f6`; okuma aninda `-wal`/`-shm`/`-journal` yok.
- **Yontem:** tum satirlarda `str(payload["signal_date"])[:10] == str(ts)[:10]` karsilastirmasi; `ts` saat ve hafta-gunu dagilimi (Ek C1).
- **Sonuc:** `signal_date` 5,748/5,748 satirda var. Esit 3,929; farkli 1,819 (%31.6). Ornek: `ts=2026-03-01T21:45:10` iken `signal_date=2026-02-17`. `ts` saat kumeleri: 09:00 (2,065), 21:45 (1,970), 21:54 (256), 19:45 (173), 13:59 (171). `ts` hafta gunu: Pzt 831, Sal 1,129, Car 660, Per 427, Cum 375, Cmt 197, Paz 2,129 (hafta sonu 2,326 = %40.5). `ts` bicimi karisik (ofsetli `2025-09-12T09:00:00+00:00`, ofsetsiz `2026-03-01T21:45:10.631481`).
- **n:** 5,748
- **Label:** MEASURED
- **Sinirlamalar:** `signal_date` yalniz gun cozunurlugunde; gun ici sinyal saati payload'da cogu satirda yok (`date` anahtari yalniz 29 satirda). Hangi job'un hangi satiri yazdigi bu adimda ayrilmadi.
- **Alternatif aciklamalar:** `ts` toplu yazim/geri-doldurma zamani olabilir (`data/signals_archive_recovered_20260703.csv` mevcut); Pazar yogunlugu haftalik toplu yazim ile tutarli; saat dilimi belirtilmemis.
- **Sonraki adim:** yol/sonuc analizlerinde `payload.signal_date` kullanilmali; `ts` anlaminin (archive-write) sozlesmede yazilmasi; ayri `signal_ts` alani onerisi (Level B).
- **Onerilen kategori:** FIX_CANDIDATE

#### ENX-05 - Arsiv sonuc cozucusu: giris = `payload.entry_price`, TP-oncelikli gunluk bar bariyeri, seviye fiyatindan cikis; pencere once `ts` tarihine baglaniyor

- **Priority:** P0 (validity)
- **Konum:** `core/scheduler.py:_run_resolve_open_signals_job:192-212` (docstring: haftalik Pazartesi 03:00 UTC; 202 `resolve_run(horizon=5, dry_run=False)`); `scripts/resolve_open_signals.py`: 86 (`ORDER BY ts`, yalniz NULL/new/open/watching/unresolvable satirlar secilir), 116 (`resolved_pct = COALESCE(resolved_pct, :pct_barrier)`; ayni UPDATE `resolved_status`'u bariyer durumuyla ezer), `_resolve_symbol:166`, 195 (`yfinance.download(..., auto_adjust=True)`), 221-223 (giris/TP/SL = payload alanlari), 226 (ayri T+5 kapanis etiketi), 240-242 (pencere: capa tarihinden SONRAKI ilk 21 islem gunu), 244-262 (her barda once `high >= TP` -> `resolved_win` @TP [253], sonra `low <= SL` -> `resolved_loss` @SL [259]), 268-270 (isabet yoksa pencerenin son kapanisi -> `expired_win`/`expired_loss`), `run:305`, 331 (`"signal_date": _parse_ts(row["ts"]) or _parse_ts(payload.get("signal_date"))`), 332 (`entry_price` payload'dan). 35-36 `MAX_BARRIER_DAYS=30`, `TRADING_DAY_APPROX=1.4` tanimli; okunan kodda kullanimi gorulmedi.
- **Veri kaynagi:** kod; durum sayimlari `data/finpilot.db` (ENX-01 SHA).
- **Yontem:** kaynak okuma (`read_file` 1-420) + satir dogrulama (`grep_search`, Ek C3).
- **Sonuc (mekanik):** (1) Giris bazi = arsivlenen `entry_price` (tarama anindaki son 15m `Close`, ENX-03); sonraki acilis veya ilk islem yapilabilir fiyat kullanilmiyor. (2) Seviyeler = payload `take_profit`/`stop_loss` (ENX-07 formulu). (3) Ufuk = 21 islem gunu; T+5 ayri etiket. (4) Seri = cozum anindaki yfinance gunluk barlar, `auto_adjust=True` (temettu/bolunme duzeltmeli) iken giris/seviyeler sinyal anindaki ham fiyatlar. (5) Ayni bar belirsizligi: TP once kontrol edilir -> ikisi de ayni barda ise kazanc yazilir. (6) Bosluk (gap) gecisi: SL altinda acilista bile SL fiyatindan, TP ustunde acilista TP fiyatindan kayit. (7) Capa: `ts` ayristirilabildigi surece `ts` tarihi kullanilir; `payload.signal_date` yalniz yedek -> ENX-01'deki 1,819 satirda pencere sinyal gununden farkli gunde baslar (olcum ENX-08). (8) Pencere 21 bardan kisa ise (is erken calistiysa) dongu `else` dalina duser ve mevcut son kapanisla `expired_*` yazilir; satir bir daha secilmez (86'daki filtre). Gozlenen: `resolved_status_barrier` `expired_win` 8, `expired_loss` 2 (Ek C1).
- **n:** kod izi; durum sayimlari 5,748 satir
- **Label:** SUPPORTED (kod izi); erken-expiry etkisinin buyuklugu UNRESOLVED (cozum anindaki "bugun" bilinmiyor).
- **Sinirlamalar:** yfinance verisi bu denetimde cekilmedi (ag yasak); yerel `data/price_cache` farkli vintage/duzeltme olabilir.
- **Alternatif aciklamalar:** `ts` cogu satirda sinyal gunune esit (3,929/5,748); fark yalniz toplu/gec yazilan satirlarda olusur.
- **Sonraki adim:** capa olarak `payload.signal_date` kullanan, acilis-bazli giris ve gap-farkinda cikis secenekli salt-okunur yeniden etiketleme (Level A arastirma); uretim degisikligi Level B.
- **Onerilen kategori:** FIX_CANDIDATE

#### ENX-06 - Kullaniciya gosterilen seviyeler cozucu ile ayni kaynaktan; fakat en az iki ayri degerlendirici farkli pencere kullaniyor

- **Priority:** P1 (economic-evaluation blocker)
- **Konum:** `scanner/signals.py:build_reason:477-511` (493: `entry_ok` metninde `SL`/`TP` = `stop_loss`/`take_profit`); `api/routers/scan.py:286-295` (watchlist'e ayni `price`/`stop_loss`/`take_profit`); `api/routers/watchlist.py:_evaluate_signal_sync:826-` (847-852 pencere `added_at` gununden itibaren DAHIL, 870 `candles[:days]`, 878 TP kontrolu 887 SL kontrolunden once, cikis seviye fiyatindan); `distribution/karne.py:82-90` (kullaniciya donuk "karne" `resolved_pct_barrier`'i yalniz `resolved_win`/`resolved_loss` icin toplar; `expired_*` haric); `core/outcome_reconciler.py` (128 ve 273 `entry_price = sig["price"]`, 73 cikis bari `after.iloc[0]` yoksa `df.iloc[-1]`, 145-149 kagit pozisyon kapama).
- **Veri kaynagi:** kod.
- **Yontem:** kaynak okuma (Ek C1 grep/pencereler; `watchlist.py` 822-912 okumasi).
- **Sonuc:** Gosterilen TP/SL ile cozucunun kullandigi TP/SL ayni zincirden gelir (risk_engine -> tarama ciktisi -> watchlist -> arsiv payload). Pencere tanimlari farkli: cozucu capa gununden SONRAKI 21 bar (ENX-05), watchlist performans raporu `added_at` gunu DAHIL `days` bar; ikisi de TP-oncelikli. Trailing, kismi cikis, zaman-bazli erken cikis veya ters-sinyal cikisi uretim yolunda bulunmadi (Ek C1 `EXIT` grep: `trailing` yalniz `market_data.py` "trailingPE/EPS" alanlari).
- **n:** kod izi
- **Label:** SUPPORTED
- **Sinirlamalar:** `_evaluate_signal_sync` cagri noktasi ve `days` degeri okunmadi; `outcome_reconciler` tam akisi K bolumunde (Ek C2) dogrulaniyor.
- **Alternatif aciklamalar:** farkli pencereler farkli urun sorularina (anlik takip vs karne) bilincli olarak hizmet ediyor olabilir.
- **Sonraki adim:** tek bir "outcome contract" (capa, giris bazi, ufuk, ayni-bar ve gap kurali) yazili hale getirilmeli; tum degerlendiriciler ona baglanmali (Level B).
- **Onerilen kategori:** FIX_CANDIDATE

#### ENX-08 - Saklanan bariyer etiketleri `ts`-capali pencereyle yeniden uretiliyor; sinyal-tarihi capasiyla uyum dusuk

- **Priority:** P0 (validity)
- **Konum:** `scripts/resolve_open_signals.py:331` (capa), 240-270 (kural); replika `scripts/ENX_paths.py:parse_ts`, `replay`.
- **Veri kaynagi:** `data/finpilot.db` (SHA ENX-11); `data/price_cache/*.json` 1,118 dosya, aggregate SHA-256 `3789326fd5e6b7cef2f1fef5b95893f295d0f98d8f17541b792e504793c37078` (dosya bazinda `data/ENX_price_cache_manifest.csv`); 592 gecersiz bar atlandi.
- **Yontem:** yalniz kilitli olmayan bolum (`payload.signal_date <= 2026-05-21`), gecerli seviyeli satirlar. Cozucu kurali (capadan sonraki ilk 21 bar; TP-oncelikli; seviye fiyatindan cikis; 21 bar dolarsa kapanisla expiry) iki capayla yeniden oynatildi: (a) `payload.signal_date`; (b) cozucu replikasi `_parse_ts(ts) or signal_date`. Saklanan `resolved_status_barrier` ile karsilastirildi (`incomplete`/`nodata` haric). Ek C2.
- **Sonuc:** capa farki (b)-(a), tum satirlar: 0 gun 3,929; 4-7 gun 318; 8-14 gun 724; >14 gun 597; negatif 180 (medyan 0, p90 17 gun). Eslesme: (a) 4,080/5,183 = %78.7; (b) 4,605/5,183 = %88.8. Capa farkli alt kume: (a) 1,244/1,799 = %69.1; (b) 1,769/1,799 = %98.3. Capa ayni alt kume: 2,836/3,384 = %83.8.
- **n:** 5,183 karsilastirilabilir satir
- **Label:** REPRODUCED (saklanan etiketlerin `ts` capasiyla uretildigi)
- **Sinirlamalar:** yerel cache ile cozucunun yfinance `auto_adjust=True` serisi ayni vintage/duzeltme degil; capa-ayni alt kumedeki %16.2 uyumsuzluk aciklanmadi. Gunluk bar; gun ici sira bilinmiyor.
- **Alternatif aciklamalar:** capa farki toplu yazim tarihlerinde kumelenir; tarih kumelenmesi uyumsuzlukla karisabilir.
- **Sonraki adim:** `signal_date` capali paralel arastirma etiketi; capa-ayni alt kumede uyumsuzluk kok-neden analizi (duzeltme, vintage, erken expiry).
- **Onerilen kategori:** FIX_CANDIDATE

#### ENX-05 eki - Fiyat tanimlari (brief 10.2)

| Kavram | Uretimdeki karsiligi | Konum | Label |
|---|---|---|---|
| Signal price | tarama ciktisi `price` = son 15m `Close` | `scanner/evaluate.py:292`, `:626` | SUPPORTED |
| Reference price | watchlist/arsiv `entry_price` = `price` | `api/routers/scan.py:286`; payload 5,748/5,748 | MEASURED (varlik) |
| Assumed entry (cozucu) | `payload.entry_price`; close(d0)'a gore medyan 0.000%, mutlak fark <= %0.1 yalniz %33.8 | `scripts/resolve_open_signals.py:221`, `:332`; ENX-10 | SUPPORTED + MEASURED |
| First executable price | tanimli degil; hicbir degerlendirici sonraki acilisi kullanmiyor; sonraki acilis entry'ye gore medyan +0.117% (p10 -2.015, p90 +2.215) | ENX-10 | NOT_MEASURABLE (tanim yok) |
| Estimated fill | yalniz model/backtest: `core/backtest.py:1062`, `core/slippage_tracker.py:305`, `core/paper_portfolio.py:149-152` | kod | SUPPORTED (sinyal/sonuc yolunda kullanilmiyor) |
| Realised fill | `alpaca_orders.filled_price` 0/14; `trades`, `positions` 0 | DB | NOT_MEASURABLE |
| Exit price (cozucu) | TP veya SL seviyesi (gap'te de), expiry'de 21. bar kapanisi | `scripts/resolve_open_signals.py:253-270` | SUPPORTED |

<!-- B2 -->

### B3 Cikis mekanigi (brief 11, 11.1)

#### ENX-07 - Uretim TP/SL formulu: gunluk Yang-Zhang sigma x momentum-kademe carpani; 15m ATR yalniz yedek yol; trailing/kismi/ters-sinyal cikisi yok

- **Priority:** P1 (economic-evaluation blocker)
- **Konum:** `scanner/evaluate.py:396-406` (`len(df_1d) >= 21` ve OHLC varsa `calculate_risk_management_yz(price=last_price, df=df_1d, momentum_score)`; aksi halde `calculate_risk_management(price, atr_val=15m ATR veya 0.01)`); `scanner/risk_engine.py:yang_zhang_vol:82-145` (20 bar, k=0.34, gunluk sigma x son kapanis; hata halinde 0.01 x kapanis); `calculate_risk_management_yz:147-172` (ayni carpanlar); `calculate_risk_management:173-233` (190-198: momentum_score >= 70 stop 1.5 / tp2 5.0; < 50 stop 2.5 / tp2 6.5; aksi stop 2.0 / tp2 5.5; 204-210 `FINPILOT_ENABLE_ALPHA_V2=1` ise stop <= 1.5, tp2 >= 5.0; 216 `take_profit = tp2`); `momentum_score` = 0.4 RSI-olcegi + 0.3 MACD>0 + 0.3 yon (`scanner/evaluate.py:386-394`).
- **Veri kaynagi:** kod; tutarlilik icin ENX-09 olcumleri.
- **Yontem:** kaynak okuma; `scanner/` grep (Ek C3); arastirma dosyalarinda cikis kalibi sayimi (Ek C1 H bolumu).
- **Sonuc:** SL = price - m_s x sigma_YZ, TP = price + m_t x sigma_YZ. Giris kapisi 50 gunluk bar istedigi icin (252-253) YZ yolu varsayilan; 15m ATR yolu pratikte yalniz OHLC eksikse. tp1/tp3 hesaplaniyor fakat cozucu ve watchlist yalniz `take_profit` (tp2) kullaniyor. Trailing, kismi cikis, cozucunun 21 gun expiry'si disinda zaman cikisi ve ters-sinyal cikisi uretim kodunda bulunmadi. Arastirmada: `research/score_lab_2_exits.py` bu kaliplarla 0 eslesme; trailing yalniz `research/research_x_capture_1_2026_09_22.py` (4) ve `test3_exit.py` (2); zaman/ufuk kaliplari 38 dosyada; `research/full_universe_barrier_backtest.py:209-210` `tp_pct=max(tp_mult*atr_fraction, 0.01)`, `sl_pct=max(sl_mult*atr_fraction, 0.005)`, 317 varsayilan ufuk 3,5 gun, 335/366-368 gidis-donus maliyet parametresi. Tutarlilik: mevcut YZ yolu stop'u en az 1.5 x gunluk sigma_YZ uzakliga koyar; arsivde stop medyani 0.313 gunluk ATR (ENX-09). Gunluk sigma ile ATR'nin ayni buyukluk mertebesinde oldugu varsayimiyla arsiv seviyeleri mevcut YZ yoluyla tutarsiz, 15m-ATR tabanli seviyelerle buyukluk olarak uyumlu gorunuyor.
- **n:** kod izi; tutarlilik icin 5,673 satir
- **Label:** SUPPORTED (formul ve cikis turleri); arsiv seviyelerinin kaynak formulu: HYPOTHESIS
- **Sinirlamalar:** arsiv satirlari icin sigma_YZ hesaplanmadi; YZ yolunun devreye girdigi tarih (`git blame`) kontrol edilmedi; `FINPILOT_ENABLE_ALPHA_V2` degeri okunmadi.
- **Alternatif aciklamalar:** R/R 2.0 kumesi eski `TP=2x/SL=1x ATR` profilinden gelebilir (PRIOR P0 replay `docs/2026-07-15-p0-execution-replay-full-universe-report.md:27`).
- **Sonraki adim:** d0'da sigma_YZ ve 15m-ATR vekiliyle stop/sigma oranlarinin {1.5, 2.0, 2.5} carpanlarina oturma payi (ENX-H9); `git blame scanner/evaluate.py` 396-406.
- **Onerilen kategori:** RESEARCH_NEXT

#### ENX-09 - Arsivlenen TP/SL geometrisi: stop medyani gunluk ATR'nin 0.31 kati; R/R kumeleri mevcut carpanlarla kismen uyumlu; payload `risk_reward` %44.3 sifir

- **Priority:** P1 (economic-evaluation blocker)
- **Konum:** `scanner/risk_engine.py:calculate_risk_management:173-233` (190-198 carpanlar; 204-210 `FINPILOT_ENABLE_ALPHA_V2`; 212-216 seviyeler, `take_profit = tp2`; 218-220 R/R); arsiv `payload.entry_price/take_profit/stop_loss`; `scripts/ENX_paths.py:main` G ve P bolumleri.
- **Veri kaynagi:** `data/finpilot.db` (SHA ENX-11); ATR icin `data/price_cache` (ENX-08 aggregate SHA), yalniz kilitli olmayan satirlar.
- **Yontem:** stop% = (entry-SL)/entry, TP% = (TP-entry)/entry, R/R = TP%/stop%; gunluk ATR14 = sinyal gunune (d0) kadar 14 barin ortalama True Range'i.
- **Sonuc:** gecerli seviye 5,746/5,748. Stop% medyan 1.058 (p10 0.446, p90 2.703); TP% medyan 2.805; R/R medyan 2.597. R/R (1 ondalik) kumeleri: 2.0 (2,112), 2.6 (1,687), 3.3 (1,181), 3.4 (211), 2.7 (135). Okunan `risk_engine` kodunun uretebilecegi R/R: alpha_v2 kapali {3.33, 2.75, 2.6}, acik {3.33, 3.67, 4.33}; 2.0 kumesi (%36.8) bu fonksiyonla uretilemez, 2.75 nadir. Payload `risk_reward` 2,532/5,719 (%44.3) satirda 0. Kilitli olmayan 5,676 satirda: gunluk ATR14 medyan %3.457; stop mesafesi gunluk ATR biriminde medyan 0.313 (p10 0.216, p90 0.464), TP 0.778; stop < 0.5 ATR %92.7, < 1.0 ATR %99.3.
- **n:** 5,746 (geometri); 5,676 (ATR birimi)
- **Label:** MEASURED (geometri); 2.0 kumesinin kaynagi: UNRESOLVED (ENX-07)
- **Sinirlamalar:** ATR basit ortalama TR; seviyeler 2 ondaliga yuvarli (`risk_engine.py:224-228`), R/R kumeleri hafif dagilir.
- **Alternatif aciklamalar:** arsiv farkli kod surumlerinin (eski 2x/1x ATR profili) ciktilarini karistiriyor olabilir.
- **Sonraki adim:** her arsiv satirina seviye-formulu surumu/provenance alani (Level B); karne metriklerinin formul surumune gore ayrilmasi.
- **Onerilen kategori:** RESEARCH_NEXT

<!-- B3 -->

### B4 Olculen yol istatistikleri (gunluk bar yaklasimi)

#### ENX-10 - Gunluk bar yol istatistikleri (kilitli olmayan bolum; yaklasik): ilk temas cogunlukla 1. seansta, gap-through ve ayni-bar belirsizligi yaygin

- **Priority:** P1 (economic-evaluation blocker)
- **Konum:** `scripts/ENX_paths.py:main` P bolumu; satir bazinda `data/ENX_paths_rows.csv`.
- **Veri kaynagi:** `data/finpilot.db` (SHA ENX-11); `data/price_cache` (ENX-08 aggregate SHA, 1,118 dosya).
- **Yontem:** `payload.signal_date <= 2026-05-21` ve gecerli seviyeler (5,685); d0 = `signal_date` gunu veya oncesindeki son bar; giris bazi = `payload.entry_price`; MFE/MAE = d1..dk high/low; gap = open(d1); run-up = close(d0)/close(d0-k)-1; bariyer yeniden oynatmasi `signal_date` capali (ENX-08). 9 satir bar eksikligi nedeniyle disarida; hesaplanan 5,676.
- **Sonuc (yuzde):**

| Metrik | n | p10 | p25 | medyan | p75 | p90 | ort. |
|---|---:|---:|---:|---:|---:|---:|---:|
| entry vs close(d0) | 5,676 | -1.302 | -0.382 | 0.000 | 0.269 | 1.146 | 2.890 |
| sonraki acilis gap vs entry | 5,676 | -2.015 | -0.747 | 0.117 | 0.914 | 2.215 | 0.053 |
| sonraki acilis gap vs close(d0) | 5,676 | -1.593 | -0.451 | 0.059 | 0.645 | 1.484 | 0.077 |
| MFE 1 seans | 5,676 | -0.558 | 0.359 | 1.419 | 3.045 | 5.549 | 2.092 |
| MAE 1 seans | 5,676 | -4.844 | -2.703 | -1.111 | -0.111 | 0.756 | -1.749 |
| MFE 5 seans | 5,673 | 0.158 | 1.195 | 3.191 | 6.394 | 11.991 | 6.097 |
| MAE 5 seans | 5,673 | -10.949 | -6.209 | -3.211 | -1.198 | -0.018 | -4.629 |
| MFE 10 seans | 5,671 | 0.468 | 1.810 | 4.539 | 9.448 | 18.346 | 12.083 |
| MAE 10 seans | 5,671 | -15.129 | -9.125 | -4.518 | -2.004 | -0.449 | -6.545 |
| run-up 5 seans (sinyal oncesi) | 5,676 | -5.827 | -2.085 | 0.675 | 3.951 | 9.116 | 1.539 |
| run-up 20 seans (sinyal oncesi) | 5,676 | -14.051 | -4.000 | 1.929 | 8.906 | 19.957 | 5.868 |

  Oranlar: d0 = `signal_date` (islem gunu) %80.9; |entry/close(d0)-1| <= %0.1: %33.8, <= %1: %75.6; sonraki acilis entry'den >%2 yukari %11.4, >%2 asagi %10.1. d1 `low <= SL` %51.8; d1 `high >= TP` %27.1; TP ve SL ayni d1 barinda %4.2 (240/5,676). Yeniden oynatma: kayip 3,534, kazanc 2,125, expiry 15, eksik 2; ilk temas 1. barda 4,238/5,659 = %74.9. Belirsiz (TP ve SL ayni temas barinda; TP-oncelikli kural kazanc yazar): kazanclarin 267/2,125 = %12.6'si; saklanan kazanc olup yeniden oynatmada da kazanc olanlarin 117/1,225 = %9.6'si. Gap-through-stop (acilis <= SL): kayiplarin 1,155/3,534 = %32.7'si; acilis-bazli eksi SL-bazli getiri medyan -0.746 puan (ort. -1.899, p10 -3.035). Gap-through-TP (acilis >= TP; cozucu TP fiyatini yazar): kazanclarin 497/2,125 = %23.4'u.
- **n:** 5,676 (payload `entry_ok=True` alt kumesi yalniz 6 satir; ayri yorumlanmadi)
- **Label:** MEASURED (gunluk bar yaklasimi); gercek gun ici siralama ve dolum: NOT_MEASURABLE
- **Sinirlamalar:** gunluk bar; intrabar sira bilinmiyor; cache vintage/duzeltme karisik; ortalamalar uc degerlere duyarli (MFE10 ort. 12.083 vs medyan 4.539); satirlar cakisan sinyaller icerir (ENX-11); tum degerler brut, maliyetsiz.
- **Alternatif aciklamalar:** giris bazi gun ici fiyat oldugundan (ENX-03) d1 oncesi ayni-gun hareketi olcumun disinda kaliyor; MFE1 p10'un negatif olmasi d1'in giris altinda acilip kalmasindan.
- **Sonraki adim:** 15m `data/intraday_cache` ile ayni-bar belirsiz satirlarin sirasinin (kapsama izin verdigi olcude) cozulmesi; acilis-bazli giris ve gap-farkinda cikis duyarlilik etiketi (B7).
- **Onerilen kategori:** RESEARCH_NEXT

<!-- B4 -->

### B5 Maliyet ve icra (brief 12.1)

#### ENX-12 - Dusuk fiyatli satirlarda stop mesafesi birkac tick; fiyata bagli spread varsayimi stop'un buyuk kesrine denk gelir (betimsel)

- **Priority:** P1 (economic-evaluation blocker)
- **Konum:** arsiv payload seviyeleri; `scripts/ENX_paths.py:main` G bolumu.
- **Veri kaynagi:** `data/finpilot.db` (SHA ENX-11).
- **Yontem:** stop mesafesi $ / 0.01 = tick sayisi (varsayim: $0.01 kotasyon adimi; $1 alti hisselerde daha kucuk adim mumkun); "1 tick" senaryosu yalniz betimsel, olculmus spread degil.
- **Sonuc:**

| Giris fiyati ($) | n | medyan stop % | medyan stop (tick) | stop < 10 tick | 1 tick / fiyat % (medyan) | 1 tick / stop (medyan) |
|---|---:|---:|---:|---:|---:|---:|
| < 1 | 59 | 5.102 | 2.8 | %98.3 | 1.818 | 0.357 |
| 1-2 | 83 | 3.333 | 5.0 | %86.7 | 0.680 | 0.200 |
| 2-5 | 260 | 2.561 | 9.0 | %58.8 | 0.280 | 0.111 |
| 5-10 | 209 | 2.231 | 15.5 | %23.0 | 0.140 | 0.065 |
| 10-50 | 1,203 | 1.440 | 35.0 | %8.1 | 0.037 | 0.029 |
| >= 50 | 3,932 | 0.869 | 160.3 | %0.5 | 0.006 | 0.006 |

- **n:** 5,746
- **Label:** MEASURED (geometri); spread etkisi HYPOTHESIS (spread verisi yok)
- **Sinirlamalar:** gercek bid/ask, kotasyon adimi ve dolum yok; tick varsayimi $1 alti icin kaba.
- **Alternatif aciklamalar:** dusuk fiyatli satirlar az (402 satir < $5); ortalama metrikleri yine de etkileyebilir (PRIOR: outlier audit top %1'in 17/52'si < $1).
- **Sonraki adim:** fiyat-kovasina bagli spread senaryosu (ornek: max(1 tick, X bps)) ile duyarlilik; kova bazinda ayri raporlama (B7).
- **Onerilen kategori:** RESEARCH_NEXT

#### ENX-13 - Maliyet bilesenleri: model kodu var, gozlenmis maliyet/dolum verisi yok; kurallar birbirinden farkli

- **Priority:** P1 (economic-evaluation blocker)
- **Konum / sonuc:**

| Bilesen | Konum | Deger / mekanik | Kullanim |
|---|---|---|---|
| Spread | `scanner/evaluate.py:_feature_contract:180-194` (df_15m `spread_bps`/`spread_pct` veya bid/ask) | yoksa `spread_source="missing"`; `scanner/execution_policy.py:62-69` yalniz uyari, `execution_feasible = adv_available or not execution_policy_enabled()` | etiket; cozucu/karne kullanmiyor |
| Sabit gidis-donus | `scanner/evaluate.py:68` `_COST_FLAT_PCT = 0.0020` | %0.20 (yedek) | yalniz `net_expected_return`/`edge_label` (`_compute_cost_labels:114-152`) |
| Dinamik kayma + Kyle lambda + komisyon + gap | `core/slippage_tracker.py:257-267, 291-306, 340-345` | alis %0.20, satis %0.15, lambda 0.10 x katilim, $1.50/taraf, overnight gap %0.10; `round_trip_cost_pct(position_usd=3000)` | etiket + backtest |
| Backtest sabitleri | `core/backtest.py:954-955, 1062, 1130` | komisyon %0.1, kayma %0.05; fill = price x (1 +/- slippage_rate) | yalniz backtest |
| Kagit portfoy | `core/paper_portfolio.py:37, 39, 149-152, 167` | yorum "10 bps round-trip"; kod faktoru giris ve cikista uygular, `cost_bps = cost_factor*2*10,000` | kagit P&L (dosya yok, ENX-04) |
| Market impact | `core/slippage_tracker.py` Kyle lambda | varsayilan 0.10, kalibrasyon kaydi yok | olculmus degil |
| Borc (borrow) | bulunmadi | - | uretim yonu `BUY` (`core/scheduler.py:405`) |
| Borsa/regulasyon ucreti, kismi dolum | COST grep dosya listesinde ayri modul yok (tum eslesmeler incelenmedi) | - | UNRESOLVED |
| Gerceklesmis dolum | `alpaca_orders` 14 emir (`limit_bracket`, `day`; limit ve stop 14/14 dolu); `filled_price`/`filled_qty`/`filled_at` 0/14; olusturma 2026-06-09..2026-10-16 | - | NOT_MEASURABLE |

- **Veri kaynagi:** kod; `data/finpilot.db` (SHA ENX-11).
- **Yontem:** grep + kaynak okuma (Ek C1, C2 K bolumu, C3); SQL sayimlari (Ek C2 X bolumu).
- **n:** 14 emir; kod izi
- **Label:** SUPPORTED (kod); MEASURED (dolum sayimlari); gercek maliyet NOT_MEASURABLE
- **Sinirlamalar:** `core/slippage_tracker.py:343` (cikis kaymasi) ve `core/paper_portfolio.py:38` (`SLIPPAGE_BPS`) okunmadi; cikis kaymasi `sell_slippage_pct` ise `round_trip_cost_pct` varsayilani %0.55 olur (HYPOTHESIS). PRIOR: decision-log 2026-10-14 net-expectancy kaydi maliyet kurallarinin 0/10/20/25-30/50/55/100 bps arasinda degistigini yaziyor.
- **Alternatif aciklamalar:** farkli kurallar farkli amaclara (etiket, backtest, kagit) bilincli hizmet ediyor olabilir.
- **Sonraki adim:** tek maliyet sozlesmesi (fiyat-kovasina bagli spread + komisyon + gap kurali) ve gozlemlenmis spread/dolum verisi (Level B veri isi).
- **Onerilen kategori:** NEEDS_MORE_DATA

<!-- B5 -->

### B6 PRIOR kanit ozeti (yeniden calistirilmadi)

Etiket: PRIOR (yeniden calistirilmadi; satirlar Ek C1 F bolumunde okundu).

| PRIOR artefakt | Alinti (ozet) | Kilit/OOS durumu | Bu rapordaki rolu |
|---|---|---|---|
| `reports/entry_quality_experiment_2026-08-06.md:54-61, 70-71` | 5 gunluk bariyer: `entry_ok` n=799, TP %25.91, SL %53.19, brut 0.107%, maliyet-sonrasi -0.443%; `score_2` n=7,465 brut 1.351%; `resolved_pct_t5` "favorable-movement field" | 125: gelecekte locked-OOS ayrimi oneriyor; holdout sonucu degil | `entry_ok` profilinin ayri bir ustunlugu gozlenmemis (tanimlayici) |
| `reports/c2c_5d_label_entry_basis_2026-09-03.md:14-18` | 100,496 satirin 79,935'i `eod_close`, 20,561'i intraday | kilit ifadesi yok | ENX-03 |
| `reports/pre_rise_path_battery_2026-08-11.md:52-60` | dusuk kapsamli kesifsel; nedensel degil | 60: "Locked OOS was not opened" | cerceve |
| `docs/2026-08-13-winner-anatomy-exp05-real-first-touch-path.md:17-22, 28, 34` | first-touch (TP/SL 2/2): `entry_ok=True` n=1,847 medyan MFE +3.58%, MAE -5.38%, SL-ilk %62.0, ort. -0.53% (maliyet oncesi); 34: close5 vs c2c_5d uyumsuzlugu acik | kilit ifadesi yok; veri seti kilitli pencereyi de kapsayan tum donem; holdout sonucu degil | ENX-10 ile ayni yonde (erken stop temasi) |
| `reports/high_rvol_raw_ohlc_exit_gate_2026-08-12.md:15, 17` | spread/ADV/kayma/impact/dolum sirasi BLOCKED; 55 bps yalniz diagnostik | 17: locked OOS NOT OPENED | ENX-13 |
| `docs/2026-07-15-p0-execution-replay-full-universe-report.md:12, 18, 27` | Legacy `TP=2x/SL=1x ATR`, V2 `TP=5x/SL=1.5x ATR`; islemler yalniz locked OOS (> 2026-05-21) icinde | sonuclar locked-OOS sonuclari; D7 geregi OOS sayilmaz; performans degerleri burada tekrarlanmadi (yalniz n: Legacy 901, V2 62) | R/R 2.0 kumesi icin aday kaynak (ENX-09) |
| `reports/research_x_capture_1_2026-09-22.md:5-16, 20-25` | n=34,762, 54 tarih; E0, E1_t10, E2, E3 `CAPTURE_NOT_SUPPORTED`; E1_t3, E1_t5 `CAPTURE_SUPPORTED_PENDING_VERIFICATION`, medyan hedefe cokuyor (20-25) | prereg kilidi dogrulanmis (decision-log 2026-10-14), veri seti OOS degil (D7) | cikis arastirmasinin mevcut durumu |

<!-- B6 -->

### B7 Test edilebilir giris/cikis hipotezleri (brief 10.3; calistirilmadi)

Etiket: HYPOTHESIS (calistirilmadi). D7 geregi gecmis veride sonuclar kesifsel; dogrulayici calisma yalniz Option C (ileriye donuk) tanimli yeni veride.

| ID | Soru | Onceden belirlenmis metrik | Girdi |
|---|---|---|---|
| ENX-H1 | Bariyer etiketi `payload.signal_date` capasiyla yeniden uretilirse durum dagilimi ve brut bariyer getirisi ne kadar degisir? | durum uyumu %; ortalama ve medyan farki; tarih-blok bootstrap %95 GA | ENX-01, ENX-08 |
| ENX-H2 | Giris bazi sonraki acilis olursa (first executable vekili) SL-ilk orani ve medyan brut getiri nasil degisir? | fark (puan); tarih-blok bootstrap GA | ENX-10 |
| ENX-H3 | Gap-farkinda cikis (SL gap'inde acilis fiyati, TP gap'inde acilis fiyati) toplu brut getiriyi ne kadar degistirir? | etkilenen islem payi; ortalama/medyan fark | ENX-10 (%32.7 / %23.4) |
| ENX-H4 | Ayni-bar belirsiz satirlar 15m intraday veriyle siralandiginda kazancin ne kadari kayba doner? | cozulebilen pay (kapsama); donusen pay | ENX-10; `data/intraday_cache` kapsami dogrulanmadi |
| ENX-H5 | Stop genisligi (gunluk ATR birimi) ile 1. seansta SL temasi arasinda monoton iliski var mi? | stop_atr ondaliklarina gore d1 SL-temas orani; Spearman | ENX-09, ENX-10 |
| ENX-H6 | Sinyal oncesi 20 seans run-up'in ust beslisi daha derin MAE5 ve daha yuksek SL-ilk orani gosteriyor mu? | beslik tablosu; Spearman | ENX-10 |
| ENX-H7 | Fiyat-kovasina bagli spread senaryosunda (ornek: her tarafta max(1 tick, 10 bps) yari-spread) hangi kovalarda maliyet stop mesafesinin %25'ini asiyor? | kova bazinda pay; brut-eksi-senaryo medyan | ENX-12 |
| ENX-H8 | `(symbol, signal_date)` tekrar ayiklama + 5 seans bekleme kurali toplu metrikleri (n, ortalama, medyan, isabet) ne kadar degistirir? | fark ve n | ENX-11 |
| ENX-H9 | Arsiv seviyeleri hangi formulden? d0'da sigma_YZ ve 15m-ATR vekiline gore stop/sigma oranlari {1.5, 2.0, 2.5} carpanlarina (+/-%5) oturuyor mu? | eslesme payi formul basina | ENX-07, ENX-09 |

<!-- B7 -->

<!-- BULGULAR-SONU -->

## Dogru calisan kisimlar

- `signals_archive` 5,748 satirin tamaminda payload `entry_price`, `take_profit`, `stop_loss`, `signal_date` var; `ts` ve `signal_date` ayristirma hatasi 0 (Ek C2). Seviye gecerliligi 5,746/5,748.
- Cozucu kendi kuraliyla icsel olarak tutarli: capa-farkli alt kumede `ts` capasiyla %98.3 yeniden uretim (ENX-08).
- `data/price_cache` 2,047 dosyanin tamami JSON olarak ayristi (0 hata); kullanilan 1,118 dosyada 592 gecersiz bar atlandi.
- `execution_policy` eksik spread'i gizlemiyor (uyari + tier); `_feature_contract` eksik alanlari listeliyor.
- `alpaca_orders`'taki 14 emrin tamami `limit_bracket` (limit ve stop dolu).
- Otomatik onay `is_degraded()` ile korunuyor (`core/scheduler.py:378-380`).
- Alinti yapilan kod dosyalarinin hicbiri `git status`'ta yok; HEAD 93ae83c ile ayni (Ek C4).

## Cevaplanamayan sorular

- Gerceklesmis dolum, kayma ve spread (veri yok).
- Uretimde `df_15m`/`df_1d` son barinin kapanmis olup olmadigi (saglayici davranisi).
- `FINPILOT_EXECUTION_MODE` ve `FINPILOT_ENABLE_ALPHA_V2` gercek degerleri (`.env` okunmadi).
- Arsiv kohortlarini hangi yazicinin urettigi ve R/R 2.0 kumesinin kaynagi.
- Cozucunun calistigi tarihler (erken expiry etkisi) ve yfinance vintage'i.
- C6 fixed-target holdout tarih araligi.
- Gun ici TP/SL sirasi (gunluk bar ile cozulmez).
- Watchlist lifecycle sonuclarinin cozucu ile uyumu (kilit nedeniyle olculmedi).

## Sinirlamalar

- Gunluk bar; intrabar sira bilinmiyor; ayni-bar belirsizlik yalniz sayilabilir.
- `data/price_cache` vintage/duzeltme karisik (195 dosyada `adjusted_close`); cozucunun yfinance `auto_adjust=True` serisinden farkli.
- Kilitli bolum (61 satir) haric; sonuclar OOS degil (D7); arsiv 2025-09..2026-05 agirlikli, 2026-01 ve 2026-06 bos.
- Tum getiriler brut ve maliyetsiz; cakisan sinyaller dahil.
- Butce nedeniyle yapilmayanlar: arsiv icin sigma_YZ karsilastirmasi, `git blame`, `core/paper_portfolio.py:38` ve `core/slippage_tracker.py:343` okumasi, COST grep eslesmelerinin tamami.
- Paylasilan terminal: iki script de `DONE_ENX` ile tamamlandi; kesinti veya yabanci cikti gorulmedi.

## Ek: komutlar

- **C1** `New-Item -ItemType Directory -Force -Path <audit>\data | Out-Null; & C:\Users\meric\AppData\Local\Programs\Python\Python312\python.exe -B <audit>\scripts\ENX_probe.py > <audit>\data\ENX_probe_console.txt 2>&1` -> cikti `data/ENX_probe_out.txt` (1,426 satir, son satir `DONE_ENX`, `EXIT=0`). Icerik: kod grep (scanner/core/api/distribution, 120 py), fonksiyon indeksleri ve kaynak pencereleri, salt-okunur DB metadata, `data/` isim listesi, lock/holdout dosya-adi taramasi, PRIOR rapor alintilari, price_cache yapisi.
- **C2** `& C:\Users\meric\AppData\Local\Programs\Python\Python312\python.exe -B <audit>\scripts\ENX_paths.py > <audit>\data\ENX_paths_console.txt 2>&1` -> `data/ENX_paths_out.txt` (284 satir, `DONE_ENX`, `EXIT=0`), `data/ENX_paths_rows.csv` (5,676 satir), `data/ENX_price_cache_manifest.csv` (1,118 dosya). Bolumler: X (icra tablolari), M (metadata), G (geometri), P (yol, yalniz `signal_date <= 2026-05-21`), K (kod dogrulama).
- **C3** Dogrudan okuma/grep: `docs/governance/decision-log.md:53-121`; `reports/oos_status_c_remediation_v1_2026-10-15/` grep `seal|locked|holdout|quarantin|freeze`; `**/*.py` grep holdout/OOS sinirlari (`research/protocol.py:35-41`, `target_formula_discovery.py:21`, `target_return_optimization.py:23`); `scripts/resolve_open_signals.py:1-420` + satir grep; `scanner/evaluate.py:114-351`, `395-404`; `api/routers/watchlist.py:822-912`; `scanner/risk_engine.py:82-172`, `173-200`; `core/slippage_tracker.py:257-264`; `scanner/**` grep `calculate_risk_management_yz|_mult`.
- **C4** `git -C C:\Users\meric\Borsa status --porcelain=v1 -uall` (salt-okunur): 158 giris; bu rolun 9 yeni yolu yalniz denetim klasorunde (`R6_entry_exit_audit.md`, `scripts/ENX_probe.py`, `scripts/ENX_paths.py`, `data/ENX_*` 6 dosya); alintilanan kod dosyalari listede yok; staged `MM web/public/demo_snapshot.json` dokunulmadi; `HEAD=93ae83c`.

<!-- END -->
