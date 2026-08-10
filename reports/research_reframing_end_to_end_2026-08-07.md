# FinPilot Research Reframing - Uctan Uca Durum Raporu

Tarih: 2026-08-07
Kapsam: research-only, tarihsel veri, production degisikligi yok
Karar seviyesi: Level A arastirma ve kanit kaydi; herhangi bir canli kural,
risk, yayin veya promotion karari degildir.

## Yonetici Ozeti

Kontrollu arastirma programinin ilk yeni dilimi olan `Timing and Drift Study
v1` tamamlandi. Kod ve sentetik sozlesme testleri gecerli cikti; ancak
canonical price cache icindeki fiyat serileri bazi sembollerde split/ayarlama
suresizligi tasidigi icin timing getirileri ekonomik kanit olarak kullanilamaz.

Bu nedenle program sonucu:

**NO-GO / promotion yok / veri onarimi olmadan sonraki ekonomik kapilar
acilamaz.**

Bu sonuc, gelecekte edge olamayacagini soylemez. Yalnizca mevcut canonical
export + cache ikilisinin giris zamani, forward return ve benchmark-relative
return sorularini karar-grade bicimde cevaplamadigini gosterir.

## Veri Kimligi

- Girdi: `data/backtest_out/full_universe_enriched.csv`
- CSV SHA-256: `38b981b372571a01b727d6a51f3fd8b918a770f7a53e552ef55e1629c142e896`
- Tarih araligi: `2025-09-11..2026-07-13`
- Cache: `data/price_cache/`
- Timing artifact: `data/backtest_out/timing_drift_study_2026-08-07.json`
- Refreshed timing artifact: `data/backtest_out/timing_drift_study_2026-08-07_refreshed.json`
- Cache integrity artifact: `data/backtest_out/price_cache_integrity_audit_2026-08-07.json`
- Raw satir: `53,859`
- Symbol-day dedup: `27,386`
- Resolved: `27,322`
- Kisa forward path: `64`
- Yuklenen sembol: `1,932`
- Benchmark cache coverage: `SPY=available`, `IWM=available`
- Absolute entry drift median: `%0.552486`
- Absolute entry drift p95: `%5.331135`

Cache integrity audit, `2,039` sembolun `485` tanesinde tek gunluk `%50+`
kapanis degisimi tespit etti. En buyuk gozlemler arasinda `FFAI` `%1,542,757`,
`MIMI` `%1,027,400` ve `EDBL` `%190,809` bulunuyor. Bunlarin kurumsal aksiyon,
reverse split veya veri adjustment'i olup olmadigi metadata olmadan
ayristirilamaz; dolayisiyla bu seriler raw forward return icin temiz kabul
edilmedi.

`python refresh_price_cache.py --report-only` kontrolunde `134` eligible
sinyalin `91` tanesi (`%67.9`) bes gunluk ileri yol icin cozulabilir durumda;
pipeline'in `%90` kabul esigi gecilmedi. Bu nedenle historical refresh ve
timing yeniden kosusu bu oturumda tamamlanmis sayilmadi.

EODHD erisimiyle `python refresh_price_cache.py --sleep 0.2` kosuldu: `78/78`
sembol basarili, `568` yeni bar eklendi ve coverage `%82.1` oldu. Yenilenen
artifact ayni `27,322` resolved gozlemi verdi; bes gunluk `signal_close`
ortalama `%21.109304`, medyan `%0.414815`, SPY-relative medyan
`-%0.352630` olarak kaldi. Bunun nedeni yenilemenin incremental olmasi ve
historical anomalili barlarin geriye donuk adjustment backfill almamis
olmasidir. Dolayisiyla timing kapisi hala `PARTIAL / data-quality stop`tur.

Historical backfill adimi eligible shadow-ledger kapsaminda tamamlandi. Raw
cache `close` degerleri korunarak EODHD `adjusted_close` metadata'si integrity
audit'in isaretledigi 8 eligible sembol icin yeniden cekildi; `3,339` bar
degisti, `0` hata ve `0` bos yanit kaydedildi. Kanit:
`data/backtest_out/adjusted_cache_backfill_2026-08-07.json`.
Backfill sonrasi tum cache uzerinde `adjusted_close` integrity audit'i
`148/2,039` sembolde hala `%50+` tek gunluk degisim buldu:
`data/backtest_out/price_cache_adjusted_integrity_audit_2026-08-07.json`.
Bu sonuc raw anomalilerin bir kismini azaltir, fakat adjusted serinin temiz
oldugunu kanitlamaz. EODHD adjusted open/high/low alanlari saglamadigi icin
adjusted `next_open`, intraday high/low, MAE/MFE ve executable tradeability
sonuclari uretilmedi; timing artifact'i raw OHLC diagnostigi olarak kalir.

Dedup anahtari `(symbol, scan_date)` ve secim kurali en erken `scan_ts`dir.
`direction` alaninin canonical scanner'da short yonu olmadigi dogrulandi; timing
calismasi bu alani yalnizca diagnostik bullish gate olarak saklar ve getiriyi
ters cevirmez. Benchmark cikarmasi ayni tarihli baslangic noktasindan yapilan
basit subtraction'dir; beta-neutral alpha degildir.

## Timing Bulgusu ve Veri Kalitesi Kapisi

Runner su giris noktalarini ve ufuklari hesaplar: `signal_close`, `next_open`,
`next_close`; `1, 2, 3, 5, 10` gun. `next_close` icin cikis, giris barinin
ayni kapanisi degil, sonraki kapanistan sonraki kapanistir. Bu sozlesme
`tests/test_timing_drift_study.py` icinde sentetik testlerle korunur.

Raw bes gunluk `signal_close` ortalamasi `%21.109304`, medyani `%0.414815`dir;
bu iki sayi arasindaki fark tek basina outlier riskini gosterir. En uc bes
gunluk gozlemler arasinda `EDBL` icin `%173,900`, `INLF` icin `%13,474.468`
ham oran gorulmustur. Bu gozlemler `data/price_cache/` serilerindeki split veya
fiyat ayarlama surekliligi kontrol edilmeden ekonomik return olarak
yorumlanamaz.

Benchmark-relative sonuclar da bu sorunu cozmez: bes gunluk
`signal_close_minus_SPY` medyani `-%0.352630`, `signal_close_minus_IWM`
medyani `-%0.090715`dir. Bunlar beta-neutral sonuclar degildir ve fiyat serisi
kalitesi onarilmadan alpha kaniti sayilmaz.

Gate sonucu: **PARTIAL / data-quality stop**. Coverage ve indeksleme
dogrulandi; fiyat surekliligi ve executable return kontrati dogrulanmadi.

## Onceki Kanitlerle Birlikte Durum

Onceki uctan uca kosu ile bu dilim birlikte okundugunda:

| Soru | Durum | Kanit |
| --- | --- | --- |
| `entry_ok` maliyet-sonrasi avantaj uretiyor mu? | `FAIL` | `reports/end_to_end_experiment_summary_2026-08-07.md`; aday net ortalama `-%0.638710` |
| Matched null'dan ayrisiyor mu? | `DIAGNOSTIC ONLY` | `data/backtest_out/end_to_end_negative_controls_2026-08-07.json`; 1,000/family |
| Score bandlari monoton mu? | `FAIL/PARTIAL` | `data/backtest_out/end_to_end_score_calibration_2026-08-07.json` |
| Barrier/fixed-target liderleri outlier-stable mi? | `FAIL` | `data/backtest_out/end_to_end_entry_exit_sweep_2026-08-07/`; median ve capped mean sorunlu |
| Portfolio incremental lift var mi? | `NOT ESTABLISHED` | `data/backtest_out/end_to_end_portfolio_2026-08-07/`; en iyi konfigurasyon yaklasik basa bas |
| Timing giris noktasi ve drift olculebilir mi? | `PARTIAL` | `data/backtest_out/timing_drift_study_2026-08-07.json`; cache continuity stop |
| Intraday tradeability kaniti var mi? | `NOT OPENED` | Intraday OHLCV, fill, spread ve impact yok |
| Regime transferi karar-grade mi? | `UNKNOWN` | PIT ve yeterli transfer protokolu yok |
| Feature information diversity olculdu mu? | `NOT OPENED` | Bagimsiz feature timestamp/age ve stable outcome contracti yok |
| Locked OOS / shadow / paper-live acildi mi? | `NOT OPENED` | Governance kilidi korunuyor |

## Kontrollu Program Kararlari

1. **Timing v1:** Tamamlandi, fakat data-quality stop nedeniyle ekonomik gate
   acilmadi.
2. **Cache refresh:** EODHD ile `78/78` hedef sembol yenilendi ve `568` bar
   eklendi. Gelecek yenilemelerde `adjusted_close` korunuyor. Eligible
   historical backfill tamamlandi (`8` sembol, `3,339` bar), ancak adjusted
   OHLC path'i ve tum-cache continuity gate'i tamamlanmadi.
3. **Matched random control:** Onceki `entry_ok` null ailesi mevcut; timing
   serisi temizlenmeden yeni bir timing null'u promotion kaniti olarak
   kosulmayacak.
4. **Daily path tradeability:** Intraday veri olmadigi icin yalnizca daily
   MAE/MFE diagnostigi mumkun; executable tradeability iddiasi acilmayacak.
5. **Opportunity taxonomy, regime interaction, information diversity, entry
   policy, limited exit sensitivity ve portfolio incremental lift:**
   `NOT OPENED` veya mevcut eski artifactlarla `PARTIAL`; timing/cost data
   contracti onarilmadan yeni genis arama yapilmayacak.
6. **Production boundary:** scanner, score, entry/exit, risk, portfolio,
   broker, shadow, OOS ve public davranista degisiklik yapilmadi.

## Gerekli Veri Onarimi

Bir sonraki research kosusundan once asgari olarak sunlar gereklidir:

- split/adjustment rejimi belgelenmis, tek fiyat bazinda tutarli OHLC serisi;
- recorded scan price ile cache close arasindaki drift icin reason code;
- benchmark ve candidate icin ayni adjustment standardi;
- forward high/low ve daily path lineage;
- historical ADV, spread, impact ve fill telemetry;
- PIT sector/regime uyeligi ve feature timestamp/age;
- locked validation ayrimi ve degismez input hash.

Bu alanlar gelmeden `raw mean`, simple benchmark subtraction veya outlierli
forward return herhangi bir strategy edge, alpha, No-Trade veya promotion
kararina donusturulemez.

## Sonuc

Mevcut kanit programi tekrar uretilebilir deney kosma kapasitesini
gosteriyor; fakat tradeable, maliyet-sonrasi ve regime-stable edge
gostermiyor. Timing calismasi bu sonuca yeni bir performans iddiasi eklememis,
tam tersine canonical cache'in ekonomik yorum icin once temizlenmesi gereken
bir veri kalitesi kapisi oldugunu ortaya koymustur.
