# R3 - Veri Kalitesi ve Lineage Denetimi (Data Quality Auditor)

- Surum: v1
- Tarih: 2026-10-19
- Durum: DRAFT - Level A arastirma ciktisi; karar degildir
- HEAD: 93ae83c (branch review/pending-2026-10-07, kirli calisma agaci; dokunulmadi)
- Rol: Data Quality Auditor (brief WP-2 ve bolum 9.1 evren)
- Kapsam: saglayici/onbellek envanteri, eksik veri isleme, evren bilesimi, zaman/look-ahead, fiyat onbellegi butunlugu (PRIOR)
- Girdiler: scanner/*.py, core/*.py, research/*.py (salt-okunur); data/distribution/scan_export_latest.json; data/shortlists/shortlist_202610*.csv; data/backtest_out/price_cache_*integrity_audit*.json (PRIOR); data/finpilot.db (mode=ro)

## Ozet

En onemli bulgular (ayrinti Bulgular bolumunde):

1. F-DQ-08 (P1, MEASURED/SUPPORTED): Export `dollar_adv`, 6 buyuk hissede yerel price_cache 20 gunluk close x volume ortalamasinin %1.54-%3.85'i (medyan %2.58). Alpaca bar istegi `feed="iex"`; likidite kapisi (`liquidity_ok` False 1352/1518) ve ADV tabanli boyutlama buyuk olasilikla yalniz IEX hacmine dayanir.
2. F-DQ-03 (P1, MEASURED): Skorlanan 1518 satirin tamami `partial`; `spread_bps` ve `short_interest_timestamp` her satirda eksik; 'complete' satir 0. Spread tabanli maliyet bu veriyle degerlendirilemez.
3. F-DQ-09 (P0, MEASURED): Shortlist dosyalari 74 degil 119/113 kolon; dosya ici satir sirasi siralama degil; ANNAW/GSRFU/HAVAU/HCACU 2026-10-16 shortlist'lerinde skor-0 `unavailable` satirlar (NUAIW composite 7). Onceki gozlem varlik olarak REPRODUCED, yuksek sira olarak CONTRADICTED.
4. F-DQ-02 (P0, MEASURED): `scan_export_latest.json` = run 20261016T224443 (brief'teki 20261016T152031 degil).
5. F-DQ-04 (P2, MEASURED): `edgar_catalyst=true` iken `catalyst_factor` 1518/1518 satirda 0; sentiment kapali.
6. F-DQ-07 (P2, MEASURED): 143 satirda gunluk bar bir gun geride; 26 satirda seans-sonrasi 15m bar; `feature_age_minutes` scan anina degil sembolun son 15m barina gore.
7. F-DQ-05 (P2, MEASURED/SUPPORTED): Evren = preset_1500 + iwm_300m (1815); export'ta 119 (%6.6) warrant/unit/right/preferred/note; bu run'da top-100'de yalniz 1 (OXLCZ). Meta veri 2026-06-10 tek senkron; sessiz fallback yollari var.
8. F-DQ-06 (P1, PRIOR): price_cache'te >%50 gunluk sicrama: close 485/2047, adjusted_close 148/2047; cache dosyalari iki sema/vintaj iceriyor (F-DQ-08).
9. F-DQ-10 (P0 riski, SUPPORTED/HYPOTHESIS): SEC companyfacts `filed` tarihine gore PIT secer; makro ve katalizor onbellekleri yalniz guncel snapshot (tarihsel replay icin PIT degil).
10. F-DQ-01 (P3, SUPPORTED): Onbellek TTL'i import aninda sabitlenir; 13:30-20:00 UTC penceresi DST bilmez.

Hicbir getiri/sonuc hesaplanmadi; hicbir sonuc OOS degildir (D7).

## Kapsam ve yontem

- Yalnizca salt-okunur kod okuma (grep/read), yerel dosya analizi ve read-only SQLite.
- Ag/saglayici cagrisi, scanner calistirma, docker, publish yok. data/ altina yazim yok.
- Turetilmis ciktilar yalnizca `reports/scanner_intelligence_audit_v1_2026-10-19/data/DQ_*` altina; scriptler `scripts/DQ_*.py` / `scripts/dq_*.py`.
- Etiketler: MEASURED, REPRODUCED, SUPPORTED, HYPOTHESIS, UNRESOLVED, NOT_MEASURABLE, CONTRADICTED. Hicbir sonuc OOS olarak etiketlenmez (D7, 2026-10-16).

## Bulgular

### T1 - Saglayici ve onbellek envanteri (karar alanlari)

Yontem: kod okuma (C2). Etiket: SUPPORTED (kod varligi; uretim davranisi icin MEASURED degildir). Env bayraklarinin uretim degerleri okunmadi (gizli bilgi kurali) -> hangi opsiyonel saglayicinin fiilen acik oldugu NOT_MEASURABLE; dolayli kanit F-DQ-05'te.

| Alan / karar kullanimi | Birincil kaynak | Fallback sirasi | Onbellek / TTL | Zaman damgasi | Kanit |
|---|---|---|---|---|---|
| OHLCV 1d/1h/15m -> teknik ozellikler, `composite_score` | Alpaca `StockHistoricalDataClient.get_stock_bars` (bulk, retry) | (1) EODHD intraday: yalniz `FINPILOT_ENABLE_EODHD_BARS=1` + anahtar, 1d haric, 15m = 5m'den resample; (2) `yf.download` bulk; (3) per-symbol `yf.Ticker` (`fetch_multi_timeframe`) | `_cache_data`: Streamlit cache (varsa) -> process-ici `MemoryCache` (TTL 300/3600 s, import aninda sabit, F-DQ-01); L2 `cache_manager.set(..., l2_only=True)` | tum yollarda `tz_convert(None)` -> tz-naive UTC | scanner/data_fetcher.py:44, 193-214, 291-301, 333-397, 877-901, 1043-1051, 1092, 1166-1223 |
| Piyasa endeksi (rejim) | `yf.download(index_symbol, period="1y", interval="1d")` | yok (yalniz yfinance) | `_cache_data(ttl_seconds=CACHE_TTL_MARKET_INDEX)` | ayni | scanner/data_fetcher.py:1550-1562 |
| Evren listesi | SQLite `symbols` JOIN `symbol_lists` (list_name=universe) | liste yoksa tum `symbols` tablosu (yalniz warning); DB hatasinda 12 elemanli sabit liste | yok | `symbols.updated_at` | scanner/data_fetcher.py:1461-1467, 1486-1528 |
| SEC EDGAR katalizor | data.sec.gov submissions | `FINPILOT_ENABLE_EDGAR_CATALYST` varsayilan "0" -> kapali | `data/catalyst_cache.json` (scan oncesi refresh) | UNRESOLVED | scanner/catalyst.py:1, 15, 34-39, 63-64 |
| FRED makro rejim | api.stlouisfed.org | `FINPILOT_ENABLE_FRED_MACRO=1` + `FRED_API_KEY` yoksa kapali | `data/macro_regime.json` + process memo 3600 s | UNRESOLVED | core/macro_regime.py:1, 32-35, 49-51, 124-145 |
| Sentiment | EODHD `/api/sentiments` | scan sirasinda sembol basina ag cagrisi yok; yalniz onbellek | `data/sentiment_cache.json` | UNRESOLVED | scanner/sentiment.py:4, 34-35 |
| Genel L1/L2 onbellek | `core/cache.py` `CacheManager`: L1 `MemoryCache` (varsayilan 300 s), L2 `RedisCache` (varsayilan 3600 s) | Redis yoksa yalniz L1; ayar okunamazsa varsayilanlar | - | - | core/cache.py:291-304, 392-404, 534-547, 784-799 |

### F-DQ-01 - Piyasa-duyarli onbellek TTL'i import aninda bir kez hesaplanir; DST ve tatil bilmez

- Oncelik: P3 (performans-mimari; uzun omurlu process'te bayat intraday bar riski varsa P2)
- Konum: scanner/data_fetcher.py:_market_aware_ttl:193-210; :213-214 (`CACHE_TTL_SECONDS = _market_aware_ttl()`); :218 (`MemoryCache(default_ttl=CACHE_TTL_SECONDS)`); :408 (`@_cache_data(ttl_seconds=CACHE_TTL_SECONDS)`)
- Veri kaynagi: kod (calisma agaci, HEAD 93ae83c)
- Yontem: C2 (read_file 186-215, grep_search)
- Sonuc: (a) TTL modul import'unda hesaplanir ve dekorator argumanina baglanir; piyasa disinda baslatilan uzun omurlu bir process seans boyunca 3600 s TTL kullanir. (b) Pencere sabit 13:30-20:00 UTC; bu yalniz EDT doneminde 09:30-16:00 ET'ye esittir. EST doneminde (2026-11-01'den itibaren) 20:00-21:00 UTC seans saati 3600 s TTL alir, 13:30-14:30 UTC seans-oncesi 300 s alir. (c) Borsa tatilleri dikkate alinmaz (`datetime.utcnow()` + yalniz hafta gunu kontrolu).
- n: - (kod)
- Etiket: SUPPORTED (kod okuma). Uretimde bayat bar etkisi: HYPOTHESIS.
- Sinirlamalar: Scan'in her calismada yeni process olarak mi (CLI/cron) yoksa uzun omurlu process icinde mi kostugu dogrulanmadi; yeni process ise (a) etkisizdir.
- Alternatif aciklamalar: Scheduler her calismada modulu yeniden import ediyorsa risk (b)/(c) ile sinirlidir.
- Sonraki adim: saat enjekte edilen birim testiyle kis donemi davranisini ve scan process omrunu dogrulamak.
- Kategori: FIX_CANDIDATE (dusuk riskli) + RESEARCH_NEXT (etki olcumu)

### F-DQ-02 - `scan_export_latest.json` her calismada uzerine yazilan bir dosya; brief'teki run_id ile icerik uyusmuyor

- Oncelik: P0 (denetim gecerliligi / roller arasi yeniden uretilebilirlik)
- Konum: data/distribution/scan_export_latest.json
- Veri kaynagi: SHA-256 `013bbf3a1ae22ab2f92d2a947d978a2abba1ebb710d093363a1d5d0e60238ed9` (C1 aninda)
- Yontem: C1 (`dq_inspect_export.py`)
- Sonuc: date 2026-10-16, generated_at 2026-10-16T22:44:43.604819+00:00, run_id `20261016T224443`, universe 1812, result_count 1801, scan_complete True. Brief'te belirtilen run_id `20261016T152031` bu dosyada degildir. 1801 satirin 1518'i tam ozellik setli; 283'u yalniz `scan_status` vb. alanlari olan iskelet satirdir (anahtar kumeleri ayrik; ornek satir QRVO: `scan_status='unavailable'`, `reject_reason=['insufficient_history']`, `composite_score=0`).
- n: 1801 satir
- Etiket: MEASURED
- Sinirlamalar: Dosya 'latest' oldugu icin baska roller farkli bir anda farkli icerik okumus olabilir.
- Alternatif aciklamalar: Ayni gun iki scan kosmus (15:20 UTC ve 22:44 UTC); brief ilkini referans almis olabilir.
- Sonraki adim: Tum rol raporlarinda girdiyi run_id + SHA-256 ile sabitlemek; run-ozel arsiv dosyasi varsa onu kullanmak.
- Kategori: FIX_CANDIDATE (denetim proseduru)

### F-DQ-03 - Skorlanan satirlarin tamami 'partial': `spread_bps` ve `short_interest_timestamp` 1518/1518 satirda eksik; `data_quality_status` ayristirici degil

- Oncelik: P1 (ekonomik degerlendirme engeli: olculmus spread olmadan maliyet/uygulanabilirlik degerlendirilemez)
- Konum: scanner/evaluate.py:83 (`_unavailable_result` -> `data_quality_status='missing'`), :207-220 (`short_interest_timestamp` `df_1d.attrs`'tan), :253 (`insufficient_history`); scanner/score_engine.py:126-187 (girdiler `row.get(k, 0)` / `or 0.0` ile okunur)
- Veri kaynagi: data/distribution/scan_export_latest.json (SHA-256 013bbf3a...238ed9, run 20261016T224443)
- Yontem: C3 (`DQ_01_export_universe_shortlists.py`) -> data/DQ_01_summary.json, data/DQ_01_export_ranked.csv
- Sonuc: 283 iskelet satir: `scan_status='unavailable'` 283/283, `reject_reason=['insufficient_history']` 283/283, `composite_score=ranking_score=0`, eligible 0 -> ust siralara cikamaz. 1518 skorlu satir: `data_quality_status='partial'` 1518/1518, `data_quality_tier='Tier 1'` 1518/1518, her satirda tam 2 eksik alan {`spread_bps`, `short_interest_timestamp`}; `spread_source='missing'` 1518, `execution_warning=['missing_spread']` 1518. 'complete' satir sayisi 0 -> complete-vs-partial skor karsilastirmasi NOT_MEASURABLE. Skorlu satirlar `composite_score`: min 0, p25 6, medyan 18, p75 40, p90 54, max 84, ortalama 24.05 (133 sifir); `ranking_score` medyan 20.20, max 74.23. Top-20/50/100 ve 10 `selection_eligible` satirin %100'u 'partial' (yapisal olarak). `score_input` (18 anahtar) hic None icermez; eksik/notr degerler 0 olarak girer: `catalyst_factor` 0 = 1518/1518, `extension_factor` 1259, `rvol_factor` 857, `filter_score` 771, `alignment_ratio` 703, `gap_factor` 683, `overnight_gap_factor` 441, `momentum_ratio` 268, `score` 139, `vol_regime` 97, `squeeze_factor` 71.
- n: 1801 (1518 skorlu)
- Etiket: MEASURED
- Sinirlamalar: Tek run; export'ta 'hesaplanmis 0' ile 'eksik->0' ayirt edilemez.
- Alternatif aciklamalar: Spread ve short-interest beslemeleri bilincli olarak kapali olabilir; sifirlarin bir kismi mesru deger olabilir.
- Sonraki adim: `score_input`'ta eksik degeri null + bayrak olarak tasimak (arastirma); spread kaynagi olmadan maliyet-sonrasi hicbir degerlendirmenin yapilamayacagini diger rollerle capraz kontrol.
- Kategori: FIX_CANDIDATE (status semantigi) + NEEDS_MORE_DATA (spread/short-interest kaynagi)

### F-DQ-04 - Bayrak acik, etkin katki sifir: `edgar_catalyst=true` iken `catalyst_factor` 1518/1518 satirda 0; sentiment kapali

- Oncelik: P2 (model kalitesi; yaniltici ozellik telemetrisi)
- Konum: scanner/score_engine.py:_catalyst_enabled:44-45, :156-165 (katalizor terimi), :243-247 (`score_feature_flags` -> `_catalyst_enabled()`); scanner/evaluate.py:466-471, 536; scanner/sentiment.py:sentiment_enabled:46-48; scanner/evaluate.py:418-428
- Veri kaynagi: export (F-DQ-03); data/catalyst_cache.json (SHA-256 c8720aba...6eacc4, 164 bayt, `updated` 2026-10-18T13:57:43Z, 2 ust anahtar); data/macro_regime.json (SHA-256 82afd7b3...1ff1252, 98 bayt, `regime='neutral'`, `updated` 2026-10-18T12:00:09Z); data/sentiment_cache.json YOK
- Yontem: C3
- Sonuc: `score_feature_flags` = {edgar_catalyst: true, lottery_fade: true, overnight_gap: true, squeeze_factor: true} 1518/1518 satirda; `score_input.catalyst_factor` = 0 1518/1518 satirda. Telemetri katalizoru aktif gosterirken etkin katki sifirdir. Sentiment: `sentiment_band=None` ve `sentiment=0` 1518/1518 (ozellik kapali; onbellek dosyasi yok ile tutarli). Makro onbellek 2026-10-18'de 'neutral'.
- n: 1518
- Etiket: MEASURED (export alanlari). Neden (scan aninda bos onbellek mi, filtrelenmis basvuru tipi mi): HYPOTHESIS; 2026-10-18 onbellek boyutu (164 bayt) bos/neredeyse bos icerikle uyumlu (SUPPORTED), 2026-10-16 durumu UNRESOLVED.
- Alternatif aciklamalar: Lookback penceresinde uygun basvuru olmamasi; refresh isinin calismamasi.
- Sonraki adim: Export metadata'sina run basina katalizor kapsami (sifir-disi sembol sayisi, onbellek `updated`) eklemek; refresh loglarini salt-okunur incelemek.
- Kategori: FIX_CANDIDATE (telemetri) + RESEARCH_NEXT

### F-DQ-05 - Evren: preset_1500 + iwm_300m = 1815; export 1812/1801; turev enstrumanlar evrende, bu run'da ust siralarda degil

- Oncelik: P2 (evren gecerliligi)
- Konum: scanner/data_fetcher.py:load_symbols:1461-1467 (liste yoksa tum tablo), :1486-1528 (JOIN; DB hatasinda 12 elemanli sabit liste, NVDA iki kez -> 11 tekil); scripts/enrich_market_caps.py:7-16, 306-319, 335-364, 369-384 (preset_1500, iwm_300m, combined_2026 = birlesim); core/config.py:89
- Veri kaynagi: data/finpilot.db (SHA-256 b64c0c5262e0d685daa1309e6293d27c208f64a6fc213b3c00e3cb896bd5f5f6, 2026-10-19T10:34Z, mode=ro); export (F-DQ-02)
- Yontem: C1, C3 -> data/DQ_01_universe_classes.csv
- Sonuc: `symbols` 13,852 satir, hepsi `AssetStatus.ACTIVE` / `AssetClass.US_EQUITY`, `updated_at` tek senkron 2026-06-10T17:04Z (2026-10-19'a gore 131 gun), `market_cap` NULL 12,116/13,852. `symbol_lists`: preset_1500 1,449 + iwm_300m 366, kesisim 0, birlesim 1,815 (hepsi tradable=1); DB'de `combined_2026` listesi yok. Export'un 1801 sembolunun tamami birlesimde; birlesimde olup export'ta olmayan 14 sembol (ALGT, AMODW, AMPL, ANGI, BAERW, FGIWW, GIPRW, MOBBW, QSIAW, RNWWW, RVSNW, SENEB, WHLRL, WLDSW). 1815 -> 1812 (3) ve 1812 -> 1801 (11) dusme adimlari artefaktlardan aciklanamadi. Alpaca isim meta verisi + regex sinifi (1815): common_other 1551, adr 91, preferred 61, warrant 48, etf_fund 34, unit 12, lp_trust_units 10, debt_note 7, right 1. Sonek kurali (5 harf W/U) warrant 47/48 ve unit 12/12 yakalar, preferred 0/61 ve debt_note 0/7 yakalar. Export (1801) icinde warrant 39 + unit 12 + right 1 + preferred 61 + debt_note 6 = 119 (%6.6). Top-100'de yalniz 1 adet (OXLCZ, debt_note, sira 19, `ranking_score` 63.775); 10 eligible satir: 9 common_other + 1 adr. Izlenen semboller: NUAIW sira 1271 (`ranking_score` 8.519); ANNAW, GSRFU, HAVAU, HCACU iskelet satir (`insufficient_history`, skor 0, sira 1516-1615).
- n: 1815 evren / 1801 export
- Etiket: MEASURED (sayimlar); isim-tabanli sinif dogrulugu SUPPORTED (heuristik); sonek-tabanli sayimlar SUPPORTED
- Sinirlamalar: Isim regex'i hatali siniflama yapabilir (or. LP/trust units); siralama `ranking_score` azalan, esitlikte `composite_score`.
- Alternatif aciklamalar: 3+11 dusus scan oncesi/ici filtrelerden (ornegin veri yoklugu) kaynaklanabilir.
- Sonraki adim: Enstruman tipi filtresini isim/asset meta verisinden turetmek (Level B urun karari); `symbols` senkronunu yenilemek; sessiz fallback'leri fail-loud yapmak.
- Kategori: RESEARCH_NEXT + FIX_CANDIDATE (sessiz fallback)

### F-DQ-06 - Fiyat onbellegi butunlugu (PRIOR): close'ta 485/2047, adjusted_close'ta 148/2047 sembolde >%50 gunluk sicrama

- Oncelik: P1 (price_cache tabanli backtest getirilerinin gecerliligi)
- Konum: data/price_cache (artefaktlarin `cache` alani)
- Veri kaynagi: PRIOR data/backtest_out/price_cache_integrity_audit_2026-08-12-e2e.json (SHA-256 18ed00b66111f6f26968442ddb325c86dcd1c7237f6a030d9d8a873226b9a7a5; ..._2026-08-11.json ve ..._2026-08-11_e2e.json ile bayt-ozdes) ve price_cache_adjusted_integrity_audit_2026-08-11_e2e.json (SHA-256 eebc921c7686c396381d8746141a88c52e0c286fab672582c909fb501437435c)
- Yontem: C3 (yalniz ust duzey skaler alanlar okundu; yeniden hesaplanmadi)
- Sonuc (PRIOR): her ikisi `status='diagnostic_only'`, esik %50. `close`: symbols_scanned 2047, symbols_with_large_jumps 485 (%23.7), en buyuk mutlak sicramanin medyani %173.58. `adjusted_close`: 2047 / 148 (%7.2) / %158.79. (2026-08-07 ve -08-10 surumleri 2039 sembol, ayni 485/148.)
- n: 2047 sembol
- Etiket: PRIOR (REPRODUCED degil)
- Sinirlamalar: Artefakt 2 ay eski; 148 adjusted sicramanin gercek fiyat hareketi mi duzeltme hatasi mi oldugu ayrilmamis; price_cache'in sonradan yenilenip yenilenmedigi bilinmiyor.
- Alternatif aciklamalar: Kucuk-cap/biyoteknoloji gercek sicramalari; reverse split.
- Sonraki adim: 148 sembolu kurumsal aksiyon takvimiyle (yerel veri varsa) eslestirmek; saglayicilar arasi duzeltme tutarliligi icin F-DQ-07.
- Kategori: NEEDS_MORE_DATA + RESEARCH_NEXT

### F-DQ-07 - Bar zaman damgalari: 143 satirda gunluk bar bir gun geride (karisik tarihli ozellikler); 26 satirda seans-sonrasi 15m bar; bayatlik telemetrisi oz-referansli

- Oncelik: P2 (model kalitesi; ozellik-zaman tutarliligi)
- Konum: scanner/evaluate.py:165-178 (`feature_age_minutes` = `signal_ts - latest`), :632 (`market_status` = `CURRENT_MARKET_STATUS["reason"]`); scanner/data_fetcher.py:867-874 (Alpaca `StockBarsRequest(..., feed="iex")`, seans filtresi yok), :458-459 (yfinance `prepost=SETTINGS.get("prepost", False)`); scanner/features.py:311, 330 (hacim baseline'i `iloc[-21:-1]`, son bar haric)
- Veri kaynagi: export SHA-256 013bbf3a...238ed9 (generated_at 2026-10-16T22:44:43Z)
- Yontem: C4 (`DQ_02_time_liquidity_shortlists.py`) -> data/DQ_02_summary.json, data/DQ_02_lastbar_flags.csv
- Sonuc: `timestamp` = `feature_timestamps['15m']` 1518/1518. Son 15m bar tarihi: 2026-10-16 1504; 2026-10-15 11, -10-14 1, -10-13 1, -10-12 1 (14 bayat satir; en iyi siralar 242 KITT/10-15 ve 244 SKK/10-12, `ranking_score` 48.64; top-100'de ve eligible'da 0; ilk harf dagilimi A..W'ye yayilmis, alfabetik yogunlasma yok). 2026-10-16 son 15m bar saati: 19:45 UTC 1319 satir, digerleri daha erken (seyrek islem); 20:00-20:45 UTC (16:00-16:45 ET, kapanis sonrasi) 26 satir (or. WMT 20:00, MRVL 20:30, AMZN 20:45; en iyi sira 206; top-100/eligible 0). Son 1d bar: 2026-10-16 1374, 2026-10-15 143 (%9.4), 2026-10-12 1 -> ~130 sembolde 15m fiyat 10-16'dan, gunluk ozellikler 10-15'e kadar. `feature_age_minutes`: 15m = 0 (1518/1518), 1h medyan 45, 4h medyan 225, 1d medyan 945 / max 2385 dk -> yas, scan anina (22:44Z) degil sembolun kendi son 15m barina goredir; 4 gun bayat SKK taze sembollerle ayni profili verir. `point_in_time=True` 1518/1518 (bayat satirlar dahil); `market_status='Varsayılan'` (varsayilan yer tutucu) 1518/1518. Look-ahead: generated_at'ten sonra tarihli bar yok (max 2026-10-16T20:45).
- n: 1518
- Etiket: MEASURED (sayimlar); mekanizma (yas referansi = son 15m bar) SUPPORTED; nedenler (IEX seyrek islem, saglayici karisimi) HYPOTHESIS
- Sinirlamalar: Yalniz kapanis-sonrasi tek run; seans ici calismalarda olusan (tamamlanmamis) barin etkisi olculmedi.
- Alternatif aciklamalar: Islem durdurma/islem gormeme; gunluk barin saglayiciya gore gec yayinlanmasi.
- Sonraki adim: Scan-anina gore bayatlik (now - son bar) ve zaman dilimleri arasi tarih tutarliligi kontrolu eklemek (FIX_CANDIDATE); seans ici run'larda olusan bar kullanimini olcmek.
- Kategori: FIX_CANDIDATE (telemetri) + RESEARCH_NEXT

### F-DQ-08 - `dollar_adv` konsolide hacmin ~%2.6'si duzeyinde (IEX feed); saglayicilar arasi fiyat duzeltme konvansiyonu farkli

- Oncelik: P1 (likidite kapisi, ADV tabanli boyutlama ve kapasite degerlendirmesi engeli)
- Konum: scanner/data_fetcher.py:860-874 (`StockBarsRequest(..., feed="iex", limit=_limit)`, `adjustment` parametresi yok); :458-459 (yfinance `auto_adjust=SETTINGS.get("auto_adjust", True)`); :464-474 (TypeError'da `auto_adjust=False` ile tekrar); :966 (bulk `yf.download(..., auto_adjust=True)`); scanner/features.py:51 (`yf.download(..., auto_adjust=True)`)
- Veri kaynagi: export SHA-256 013bbf3a...238ed9; data/price_cache/{AAPL,MSFT,NVDA,TSLA,LRCX,INTC}.json (SHA-256 degerleri C6)
- Yontem: C4 (export degerleri), C5 (price_cache son 20 kayit, ortalama close x volume)
- Sonuc: export `dollar_adv` / cache 20g dolar hacmi: AAPL 387.6M / 16.00B = %2.42; MSFT 381.9M / 12.51B = %3.05; NVDA 676.7M / 24.67B = %2.74; TSLA 243.5M / 15.78B = %1.54; LRCX 123.2M / 3.20B = %3.85; INTC 287.5M / 11.87B = %2.42 (medyan %2.58; 26-65 kat fark). `adv_source='close_volume_20d'` 1518/1518; `liquidity_ok` False 1352/1518 (True grubunda min `dollar_adv` 2.64M, False grubunda max 316.5M -> kapi yalniz ADV esigi degil). Cache heterojen: AAPL/MSFT/TSLA/INTC son tarih 2026-07-29, `adjusted_close` kolonu yok; NVDA/LRCX son tarih 2026-08-21, `adjusted_close` var.
- n: 6 sembol (oran); 1518 (likidite dagilimi)
- Etiket: MEASURED (degerler); IEX-yalniz hacim atfi SUPPORTED (kod `feed="iex"` + oranin IEX hacim payi buyuklugunde olmasi); Alpaca'nin `adjustment` verilmediginde 'raw' dondurdugu HYPOTHESIS (ag yok); duzeltme farkinin ozelliklere etkisi HYPOTHESIS
- Sinirlamalar: Pencereler farkli (cache Temmuz/Agustos, export Ekim); sembol bazinda kullanilan saglayici export'ta kayitli degil.
- Alternatif aciklamalar: Bazi semboller yfinance fallback ile konsolide hacim almis olabilir (karisik baz); donemsel ADV degisimi 26-65 kat farki aciklamaz.
- Sonraki adim: Sembol bazinda bar saglayicisini export'a yazmak; `dollar_adv`i konsolide hacimden hesaplamak ya da IEX olarak etiketlemek; Alpaca `adjustment`'i acik ayarlamak (likidite kapisi semantigi degisir -> Level B).
- Kategori: FIX_CANDIDATE + RESEARCH_NEXT

### F-DQ-09 - Shortlist CSV'leri 119/113 kolonlu; satir sirasi siralama degil; izlenen turev enstrumanlar skor-0 'unavailable' satirlar

- Oncelik: P0 (kanit gecerliligi; onceki gozlemin yorumu)
- Konum: data/shortlists/shortlist_202610*.csv (125 dosya; tam SHA-256 listesi data/DQ_01_shortlist_files.csv); 2026-10-16 icin 21 dosya (_1512 ... _1820)
- Yontem: C3, C4, C5
- Sonuc: 125 dosyanin 121'i 119 kolon, 4'u 113 kolon, 0'i 74 kolon -> brief'teki "74 kolonlu shortlist" tanimi mevcut dosyalar icin CONTRADICTED (klasor yazilmaya devam ediyor; en yenisi shortlist_20261019_1308.csv). 2026-10-16 dosyalari ~198-200 satir; her birinde 12-31 `unavailable` satir (`data_quality_status='missing'`, composite 0). Dosya ici sira azalan skor degil: skor-0 satirlar 1-9. pozisyonlarda (HUBCW poz 1 ve MTEKW poz 2 _1728; FOXXW poz 2 _1514; ANNAW poz 3 _1532 ve _1750). ANNAW, GSRFU (_1813 poz 106), HAVAU (_1813 poz 107), HCACU (_1813 poz 110) yalniz composite 0 / ranking 0 / `missing` / eligible False; NUAIW `partial`, composite 7, ranking 8.642 (_1532 poz 9, _1750 poz 11). 21 dosyanin ilk 20 satiri (420 yuva): warrant 18, unit 2, right 1, preferred 9 - agirlikla skor-0 satirlar.
- n: 125 dosya / 21 dosya (2026-10-16)
- Etiket: MEASURED. Onceki gozlem: varlik olarak REPRODUCED, yuksek sira olarak CONTRADICTED.
- Sinirlamalar: Satir siralama olcutu ve dosya adindaki saat dilimi belirlenmedi.
- Alternatif aciklamalar: Dosyalar 200'luk tarama partilerinin siralanmamis ham ciktisi olabilir.
- Sonraki adim: Shortlist'ten sira cikaran analizlerde `ranking_score` ile yeniden siralamak; dosya sozlesmesini (kolon sayisi, siralama) belgelemek.
- Kategori: FIX_CANDIDATE (denetim proseduru)

### F-DQ-10 - PIT: SEC companyfacts `filed` tarihine gore secer; makro ve katalizor onbellekleri tarihsel replay icin PIT degil

- Oncelik: P0 riski (arastirma veri setlerinde look-ahead olasiligi; kanit dolayli)
- Konum: research/sec_companyfacts.py:4, 36-49 (`publication_date = observation["filed"]`, `accn`), :111-129 (`publication_date > as_of_date` atlanir; 118-121: ilk snapshot oncesi restated tarihce geri alinamaz); research/restatement_detector.py:1-9, 35, 69-83 (iki onbellek snapshot'i arasi bar degisimi); core/macro_regime.py:56 ("most recent numeric observation"), :93 (son siniflama `data/macro_regime.json`a); scanner/catalyst.py:15, 39 (tek `data/catalyst_cache.json`)
- Veri kaynagi: kod; data/catalyst_cache.json (SHA-256 c8720aba...6eacc4; `factors` dict[8], `updated` 2026-10-18T13:57Z); data/macro_regime.json (F-DQ-04)
- Yontem: C4, C5 (grep_search, file_search)
- Sonuc: SEC olgulari dosyalama tarihiyle as-of filtrelenir; restatement'lar yeni kayit olarak saklanir (SUPPORTED). `filed` gun cozunurlugunde oldugundan as-of gunu kapanis sonrasi dosyalanan olgu ayni gun "bilinen" sayilir -> karar zamani eslemesine bagli <=1 seans look-ahead riski (HYPOTHESIS). Makro (FRED son gozlem, vintage yok) ve katalizor (8 sembollu tek snapshot) yalniz guncel durumu tutar; tarihsel replay bunlari kullanirsa look-ahead olur (SUPPORTED kod; fiili kullanim UNRESOLVED). `**/pit_*` deseninde yalniz scripts/pit_research_pipeline.py bulundu (veri artefakti yok); dosya bu turda okunmadi.
- n: - (kod)
- Etiket: SUPPORTED (kod) / HYPOTHESIS (etki) / UNRESOLVED (kullanim)
- Sinirlamalar: Arastirma veri setlerinin join'leri incelenmedi; FRED revizyon buyuklugu olculmedi.
- Alternatif aciklamalar: Arastirma hatti makro/katalizoru hic kullanmiyor olabilir.
- Sonraki adim: scripts/pit_research_pipeline.py ve arastirma veri setlerinin kolon kokenini salt-okunur incelemek; SEC kabul zamani (acceptance datetime) kullanimini degerlendirmek.
- Kategori: RESEARCH_NEXT + NEEDS_MORE_DATA

## Dogru calisan kisimlar

- Tum saglayici yollarinda indeks tz-naive UTC'ye normalize edilir (scanner/data_fetcher.py:507, 900-901, 990, 1018, 1092) - SUPPORTED; export'ta `generated_at` sonrasi tarihli bar yok, 1d etiketleri 04:00 UTC (= 00:00 ET) - MEASURED. KEEP_AS_IS.
- `insufficient_history` satirlari skor 0 alir ve hic eligible olmaz (283/283) - MEASURED. KEEP_AS_IS.
- Export bolumlemesi tutarli: iskelet ve tam satir anahtar kumeleri ayrik (both=0, neither=0) - MEASURED.
- `symbol_lists` listelerinde tekrar yok; tum semboller `symbols`'ta ve tradable=1 - MEASURED.
- Opsiyonel saglayicilar (EODHD bars, EDGAR, FRED, sentiment) varsayilan KAPALI; sentiment kapaliyken `sentiment_score=None` ile notr kalir (scanner/evaluate.py:418-428; export `sentiment_band=None` 1518/1518) - SUPPORTED + MEASURED. DO_NOT_CHANGE.
- Evren SQL'i parametreli (scanner/data_fetcher.py:1486-1492) - SUPPORTED.
- SEC companyfacts as-of secimi `filed` tarihine dayanir, restatement'lar ayri kayit - SUPPORTED (F-DQ-10).
- Bu run'da top-100 ve eligible satirlarda bayat (14) veya seans-sonrasi (26) son bar yok - MEASURED.

## Cevaplanamayan sorular

- Uretim env bayraklari hangi opsiyonel saglayicilari aciyor? NOT_MEASURABLE (gizli bilgi kurali); dolayli kanit: export `score_feature_flags` (F-DQ-04).
- 1815 -> 1812 -> 1801 dusus adimlari (3 + 11 sembol) hangi filtrelerden? UNRESOLVED.
- Run 20261016T152031 artefakti nerede? UNRESOLVED (latest dosya uzerine yazilmis).
- Sembol bazinda hangi bar saglayicisi (Alpaca/EODHD/yfinance) kullanildi? Export'ta alan yok -> NOT_MEASURABLE (artefakttan).
- alpaca-py `limit` semantigi (toplam mi sayfa mi; scanner/data_fetcher.py:860-865 yorumu "page_size" varsayar) ve Alpaca varsayilan `adjustment`: UNRESOLVED (yerel kutuphane yok, ag yasak). Bayat satirlarin alfabetik dagilimi kesme hipotezini desteklemiyor (F-DQ-07).
- Seans ici run'larda olusan (tamamlanmamis) barin ozelliklere etkisi: olculmedi (UNRESOLVED).
- `earnings_proximity=0` (1421/1518) "veri yok" mu "yakin kazanc yok" mu? UNRESOLVED.
- `squeeze_factor` (0 olmayan 1447 satir) short-interest olmadan (1518/1518 eksik) nasil hesaplaniyor? UNRESOLVED (kod okunmadi).
- 148 adjusted sicramanin gercek mi hata mi oldugu: NEEDS_MORE_DATA.
- scripts/pit_research_pipeline.py ve arastirma veri setlerinin makro/katalizor join'leri: UNRESOLVED.

## Sinirlamalar

- Tek export (latest; 2026-10-16T22:44Z run); sayimlar 2026-10-19T10:34Z dosya durumunu yansitir.
- Isim-tabanli enstruman siniflamasi regex heuristigi; sonek sayimlari en fazla SUPPORTED.
- Ag yok: saglayici dokumantasyonu ve varsayilanlar dogrulanmadi.
- Ozellikler yeniden hesaplanmadi; export'ta 'sifir' ile 'eksik->sifir' ayrilamaz.
- Shortlist klasoru eszamanli yaziliyor; dosya kumesi degisebilir.
- price_cache capraz kontrolu farkli pencereler kullanir (Temmuz/Agustos vs Ekim).
- Hicbir getiri/sonuc hesaplanmadi; kilitli/holdout bolumlere dokunulmadi; D7 geregi OOS etiketi yok.
- Butce nedeniyle okunmayanlar: scripts/pit_research_pipeline.py, earnings/short-interest/squeeze kaynak kodu, scan calistirma modeli (core/scheduler.py).

## Ek: komutlar

- C1: `python.exe -B scripts/dq_inspect_export.py data/distribution/scan_export_latest.json` ve `python.exe -B scripts/dq_db_probe.py` (SQLite `mode=ro` + `PRAGMA query_only=ON`).
- C2: grep_search / read_file: scanner/data_fetcher.py (186-215, 1455-1530 ve provider/onbellek desenleri), scanner/catalyst.py, scanner/sentiment.py, core/macro_regime.py, core/cache.py.
- C3: `python.exe -B scripts/DQ_01_export_universe_shortlists.py` (2026-10-19T10:34Z; ciktilar data/DQ_01_summary.json, DQ_01_export_ranked.csv, DQ_01_universe_classes.csv, DQ_01_shortlist_files.csv).
- C4: `python.exe -B scripts/DQ_02_time_liquidity_shortlists.py` (ciktilar data/DQ_02_summary.json, data/DQ_02_lastbar_flags.csv) + PowerShell `Import-Csv` ilk-harf gruplamasi; yerel alpaca-py kaynagi bu yorumlayicida yok (limit semantigi dogrulanamadi).
- C5: PowerShell here-string -> `python.exe -B -`: data/price_cache/{AAPL,MSFT,NVDA,TSLA,LRCX,INTC}.json son 20 kayit ortalama close x volume + data/DQ_02_summary.json izleme satirlari; grep_search research/sec_companyfacts.py, research/restatement_detector.py; file_search `**/pit_*`.
- C6: `Get-FileHash -Algorithm SHA256` (data/price_cache): AAPL.json 273484f0be35c864b4fb22e3f564f6af7585d43422cfdfabfe2575e9c6c5e4dc; MSFT.json a95bfe1e9bbdbbefd4eb1eaad20e9be6fbe20825770a0ffee51157ba74d39194; NVDA.json 1dc98ed7896195929d5ca3fd3a8f440cf91c1c2ca8a5b3521db292123bc9ef6d; TSLA.json f4716c269e2aba5b6484db5fc67c15abb97724443de79938d98d175cc11f4a61; LRCX.json 3ccaeb1a9f2b89ae07a9dee00bf6d85f02118855c44345db53abf3969df7a58c; INTC.json cc9da7153f1bbcb520f9a21959da1c7e404161c17e34eda513f76476f9f8cd06.
- C7: `git -C C:\Users\meric\Borsa --no-optional-locks status --porcelain=v1 -uall`: toplam 115 kayit; denetim klasorunde 24 (bu rolun 11'i: R3 raporu, 6 adet data/DQ_*, 4 script); klasor disi 91 (diger calismalar, dokunulmadi); web/public/demo_snapshot.json durumu `MM` (bu rol dokunmadi).

<!-- END -->
