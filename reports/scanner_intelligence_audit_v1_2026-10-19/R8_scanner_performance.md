# R8 - Scanner Performance (WP-10): zamanlama logu, eszamanlilik ve kod duzeyi darbogaz analizi

| Alan | Deger |
|---|---|
| Baslik | R8 - Scanner Performance (WP-10) |
| Surum | v1 |
| Tarih | 2026-10-19 |
| Durum | DRAFT - Level A arastirma ciktisi; karar degildir |
| HEAD | 93ae83c (branch `review/pending-2026-10-07`; dogrulama komutu Ek: komutlar C1) |
| Rol | Scanner Performance (WP-10), PREFIX `PERF` |
| Kapsam | `data/distribution/scan_timing.jsonl` (salt-okunur, tek bellek snapshot), `scanner/data_fetcher.py`, `core/rate_limiter.py`, `api/routers/scan.py`, `web/src/app/py-api/` proxy; onceki performans raporlari (PRIOR) |
| Girdiler | `reports/scan_performance_audit_2026-10-18.md` (+3 CSV), `reports/scan_performance_audit_2026-09-21.md`, `data/distribution/scan_timing.jsonl` (snapshot 2026-10-19T11:19:03Z; 1 929 460 bayt; 867 kayit; SHA-256 `8151086aac0d2407130aa44cf0b8b326202df70c5e0951f8835ddbc7bbffa131`), kaynak kod HEAD 93ae83c calisma agaci |
| Katman / seviye | Layer 5 (engineering) okuma; Level A salt-okunur analiz. Uretim kodu, konfig, `data/**`, decision log degistirilmedi. |

## Ozet

- Veri: `scan_timing.jsonl` snapshot'i 867 kayit (386 legacy + 481 gozlem-katmani kaydi, gozlem 2026-10-08 16:14:58 UTC'de basliyor), 0 ayristirma hatasi, SHA-256 `8151086a...a131`. 2026-10-18 raporunun sayilari ilk 820 kayitta yeniden uretildi (416 satir, median 321.38 s): REPRODUCED.
- PERF-10 (P3, SUPPORTED): 2026-10-16 13:57:32 UTC sonrasi 26 adet 200-sembol batch'te `total_s` dususu gorulmedi: post median 392.3 s, son 30 gun oncesi 376.9 s (HL +8.7 s, %95 bootstrap [-30.7, +55.3]); `yf_fallback` duzeltmeli kaydirma -14.0 s [-56.1, +23.6]. Post'ta repair yuku daha yuksek (`yf_fallback` median 100.5 vs 57.0). Karistirici etkili; kodun yuklendigi loglardan dogrulanamiyor.
- PERF-12 (P3, MEASURED/SUPPORTED): es zamanlilik seyrek (mesgul surenin %1.0'i; 21/161 is), hepsi ayni surecte; `peak_active_jobs` aralik rekonstruksiyonu ile 161/161 tutarli. Ortusen 200-sembol isler daha uzun (median 542 vs 349 s) ama uzunluk yanliligi nedensel yorumu engeller.
- PERF-13 (P0, MEASURED + SUPPORTED): gozlem donemindeki 94 adet 200-sembol API isteginin 3'u 600 s'de 504 aldi; iscileri 1.6-133.2 s sonra `ok` bitti (job_s 601-733 s); kod geregi bu batch sonuclari kalici yazilmadi.
- PERF-02/05/07 (SUPPORTED): sembol-basina repair her kalan sembol icin uc zaman dilimini de ceker (`yf_fallback` pozitif degerlerinin %96-99'u 3'un kati); her `fetch`, yfinance 1.4.1'de `fast_info.last_price` uzerinden ek bir 1 yillik `history` istegi tetikler ve bu istek token kovasinda sayilmaz; sayaclar surec-global.
- PERF-11 (ESTIMATED): 4/s, burst 8 kovasinin alt siniri median 12.6 s (`total_s`'nin %4.1'i, pre) ve 23.5 s (%6.5, post) -> kova tek basina ana sinirlayici degil.
- PERF-04/06/09 (SUPPORTED, kod): 600 s zaman asimi isciyi iptal etmez, `data_fetcher.py` icinde iptal noktasi yok; varsayilan (koordinatorsuz, loglarda %100) yolda bir surecte 16'ya kadar is; sinirsiz bellek yapisi bulunmadi, risk is basina DataFrame'ler x es zamanlilik.
- PERF-16: kalan sorular canli olcum gerektirir; Level C (insan onayi) protokolu tanimlandi, uygulanmadi.

<!-- OZET-NEXT -->

## Kapsam ve yontem

- Yalnizca salt-okunur islemler: kaynak kod okuma, `git` okuma komutlari, `scan_timing.jsonl` dosyasinin bir kez bellege alinip ayristirilmasi. Ag/provider/HTTP cagrisi, docker, scanner calistirma, publish yok.
- Turetilmis ciktilar yalnizca `reports/scanner_intelligence_audit_v1_2026-10-19/data/PERF_*` ve betikler `.../scripts/PERF_*.py` altindadir.
- Kanit etiketleri: MEASURED, REPRODUCED, SUPPORTED, HYPOTHESIS, UNRESOLVED, NOT_MEASURABLE, CONTRADICTED; teorik alt sinir hesaplari ayrica ESTIMATED olarak isaretlenir. Kod varligi veya gecen test, uretim davranisi icin MEASURED kanit sayilmaz.
- D7 (2026-10-16): hicbir mevcut veri seti out-of-sample sayilmaz; bu rapor performans (sure) verisi kullanir, getiri/sonuc hesabi yapmaz.

<!-- KAPSAM-NEXT -->

## Bulgular

### PRIOR: onceki performans raporlarinin ozeti (yeniden hesaplanmadi, yalnizca alinti)

`reports/scan_performance_audit_2026-10-18.md` (PRIOR):

- Snapshot SHA-256 `008c66b0a4849310fed31612b9a09a04caf23edb1700a34b6f54c9f9109a16b9`, 820 kayit; 593 kayitta `universe=200`, 416 kayitta `total_s`; kayitli en buyuk `universe` 200 (tam evren olcumu yok).
- Tamamlanan 200-sembol `total_s`: median 321.38 s, p95 534.99 s, aralik 37.45-590.13 s (n=416). `yf_fallback` ile Pearson r=0.478 (n=416, gozlemsel).
- `stage_timing` yalnizca 12/820 kayitta dolu; 2026-09-22 bes kosuluk kohortta `prefetch.repair` median 305.025 s, eslestirilmis kosu payi median %86.45 (aralik %78.55-%90.61). Tam evren icin darbogaz/pay/Amdahl tavani iddia edilmedi ("Status F: measurement incomplete").
- `total_s` penceresi `_t_start` -> `_t_scoring_done`; kalicilik (`persist_s`, n=130, median 0.30 s), kuyruk bekleme ve yanit tamamlanmasi pencere disinda. Gecmis %81.6 repair-payi etiketi ortalama/median tanim catismasi olarak raporlandi (CORE-005).

`reports/scan_performance_audit_2026-09-21.md` (PRIOR): o tarihte 315 kayit, 279 adet 200-sembol kaydi, hicbirinde stage event yok; median 300.44 s, p95 496.67 s; `yf_fallback`-`total_s` Pearson 0.50 (n=279); "Status F". `reports/scan_instrumentation_gaps_2026-10-18.csv` (PRIOR) acik bosluklari listeler: tam evren duvar saati, istek-duzeyi uctan uca sure, cache/seans durumu, zaman dilimi basina repair suresi, kampanya kimligi.

Bu rapor bunlari tekrar etmez; asagidaki bulgular yeni sorulara (2026-10-16 sonrasi gozlem, eszamanlilik, istek/isci suresi, kod duzeyi darbogaz, bellek, canli olcum protokolu) yoneliktir.

### PERF-01 - Saglayici sirasi ve istek bicimi (kod duzeyi)

- Oncelik: P3
- Konum: `scanner/data_fetcher.py:prefetch_symbols_multi_timeframe:1257-1380`; `scanner/data_fetcher.py:_prefetch_alpaca_bulk:805-932` (istek 849-879); `scanner/data_fetcher.py:_get_stock_bars_with_retry:287-324`; `scanner/data_fetcher.py:_repair_partial_alpaca_result:1149-1254`; `DEFAULT_TIMEFRAMES:582-586`; `MIN_HISTORY_BARS:588`.
- Veri kaynagi: kaynak kod; calisma agaci bu dosyalarda HEAD ile ayni (`git diff --stat HEAD` bos, Ek C3).
- Yontem: kod okuma + `PERF_code_scan.py` (Ek C2).
- Sonuc: (1) Alpaca toplu bar: gercek zaman dilimi basina bir `StockBarsRequest` (15m/10 gun, 1h/15 gun, 1d/300 gun; 4h, 1h'den resample), zaman dilimleri sirali (paralel degil) istenir; `feed="iex"` (872); `limit=max(10_000, len(symbols)*250)` (865; 200 sembolde 50 000); 3 deneme, uyku 0.5 s ve 1.0 s (287-288, 304-316). Bir zaman diliminde 3 deneme basarisizsa tum Alpaca sonucu atilir (`return None`, 879). (2) Alpaca basariliysa: zaman dilimi basina `MIN_HISTORY_BARS` altinda kalan semboller `alpaca_miss` olarak kaydedilir (1156-1167); EODHD yalnizca `FINPILOT_ENABLE_EODHD_BARS=1` ve anahtar varsa (1049-1052, 1179-1199); ardindan eksik semboller icin zaman dilimi basina tek `yf.download(..., threads=True)` (1202, 962-970); hala yetersiz semboller icin sembol-basina yfinance `fetch` (1215-1244). (3) Alpaca `None` donerse: tum semboller icin `yf.download` toplu (1308-1352); o da bosa duserse sembol-basina havuz (1358-1380).
- n: yok (kod)
- Etiket: SUPPORTED (kod yapisi). Hangi dalin uretimde ne siklikla calistigi bu bulguda olculmedi.
- Sinirlamalar: alpaca-py `limit` parametresinin semantigi (toplam ust sinir mi, sayfa boyu mu) offline dogrulanmadi; kod yorumu (861) "page_size, not total cap" der. Toplam ust sinir ise 15m'de 200 sembolun bar toplami 50 000'i astiginda bazi semboller eksik gorunup repair'e dusebilir: HYPOTHESIS.
- Alternatif aciklama: yok (yapisal tespit).
- Sonraki adim: API imajindaki alpaca-py surumunde sayfalama/`limit` davranisini salt-okunur kaynak okumasiyla dogrulamak; zaman dilimi basina donen bar ve sembol sayisini timing kaydina eklemek (Level B).
- Kategori: KEEP_AS_IS (zincir); RESEARCH_NEXT (`limit` semantigi).

### PERF-02 - Sembol-basina repair, eksik olmayan zaman dilimlerini de yeniden ceker

- Oncelik: P3
- Konum: `scanner/data_fetcher.py:_repair_partial_alpaca_result.repair_symbol:1221-1239`; `scanner/data_fetcher.py:fetch_multi_timeframe:636-699` (havuz 679).
- Veri kaynagi / yontem: kod okuma.
- Sonuc: `repair_symbol` her kalan sembol icin `fetch_multi_timeframe(symbol, timeframes=timeframes, ...)` cagirir (1223-1228); bu, uc gercek zaman diliminin (15m, 1h, 1d) hepsi icin `fetch` calistirir (678-681). Yalnizca yetersiz zaman dilimlerinin adayi kullanilir (1229-1237), ama yeterli olan zaman dilimleri de cekilmis olur. Alpaca toplu yolu `fetch` cache'ine yazmadigi icin (cache yalnizca `fetch` uzerinde, 408) bu ek cagrilar cache isabeti olmadan HTTP + token tuketir.
- n: yok (kod)
- Etiket: SUPPORTED (kod); uretimdeki buyukluk HYPOTHESIS (sayac semantigi icin bkz. PERF-05/PERF-10).
- Sinirlamalar: hangi zaman diliminin eksik oldugu sembol bazinda loglanmiyor; yalnizca zaman dilimi toplamlari (`alpaca_miss`) var.
- Alternatif aciklama: tum zaman dilimlerini ayni kaynaktan almak icin bilincli tasarim olabilir; ancak bir onceki adim (1202-1206) zaten karisik kaynak (Alpaca + yfinance) uretiyor, kodda bu yonde bir gerekce yorumu yok.
- Sonraki adim: Level B oneri - `repair_symbol` yalnizca eksik zaman dilimlerini istesin; once/sonra cagri sayisi kontrollu kosuda olculsun.
- Kategori: FIX_CANDIDATE

### PERF-03 - yfinance token bucket: yapilandirma, kapsam ve kati olmayan bekleme

- Oncelik: P3
- Konum: `scanner/data_fetcher.py:fetch:427-440`; `core/rate_limiter.py:TokenBucket.wait:65-82`; `core/rate_limiter.py:get_bucket:94-106`.
- Veri kaynagi / yontem: kod okuma.
- Sonuc: oran `float(os.environ.get("YFINANCE_RATE", "4"))` token/s, kapasite (burst) `float(os.environ.get("YFINANCE_BURST", "8"))` (433-434); kova adi "yfinance", surec genelinde tek; ilk `get_bucket` cagrisi parametreleri sabitler (97-98), sonraki ortam degisikligi yeniden baslatmaya kadar etkisizdir. `wait(timeout=5.0)` son tarihte `False` dondurur (76-79) fakat `fetch` donus degerini kullanmaz (436) -> en fazla 5 s bekleyip tokensiz devam eder; sinirlayici yumusak bir ust siniridir. Yalnizca sembol-basina `fetch` yolu sinirlanir; `yf.download` toplu (962-970), Alpaca ve EODHD bu kovanin disindadir. `_note_yf_fetch()` kova bekleyisinden sonra sayar (440).
- ESTIMATED alt sinir formulu: F sembol-basina cagri, her cagri token alirsa t_rl >= max(0, F - 8)/4 s (varsayilan degerlerle). Batch bazinda hesap PERF-11'de.
- n: yok (kod)
- Etiket: SUPPORTED (kod). Uretimde etkin `YFINANCE_RATE`/`YFINANCE_BURST` degeri: UNRESOLVED (`.env` kural geregi okunmadi).
- Sinirlamalar: `fetch` icinde `tkr.fast_info` / `last_price` erisimi (444-451) yfinance icinde ek HTTP istegi tetikleyebilir ve kovada sayilmaz: HYPOTHESIS (kutuphane kaynagi bu bulguda dogrulanmadi).
- Alternatif aciklama: yok.
- Sonraki adim: `rate_limit.wait` event toplamini ve `wait()` False sayisini kontrollu kosuda kaydetmek.
- Kategori: RESEARCH_NEXT

### PERF-04 - Zaman asimi semantigi: 600 s istek, 620 s proxy, iptal edilemeyen isci

- Oncelik: P3
- Konum: `api/routers/scan.py:38` (`_SCAN_TIMEOUT_SECONDS = 600`); `api/routers/scan.py:43` (`_executor`, 16 isci); `api/routers/scan.py:_run_scan:461-513` (`asyncio.wait_for(loop.run_in_executor(...), timeout=600)` 488-498, 504 yaniti 500-506); `api/routers/scan.py:_run_coordinated_scan:373-449` (`asyncio.shield` 413-414); `core/scan_coordinator.py:enabled:31-32` (varsayilan "0"); `scanner/evaluate.py:777-778,799,812` (`check_cancelled`); `web/src/app/py-api/[...path]/route.ts:55-56,64-66`.
- Veri kaynagi / yontem: kod okuma.
- Sonuc: Varsayilan (koordinatorsuz) yolda 600 s `wait_for` yalnizca beklemeyi birakir; `_executor` icindeki thread `evaluate_symbols_parallel`'i sonuna kadar calistirmaya devam eder (Python thread'i iptal edilemez); zaman asiminda `_complete_scan` (kalicilik) calismaz. Koordinator yolu (opt-in) gelecegi `shield` eder; iptal yalnizca `scanner/evaluate.py` kontrol noktalarinda (prefetch oncesi 778, prefetch sonrasi 799, sembol degerlendirme 812) isbirlikcidir; prefetch/repair icinde kontrol noktasi yok (`data_fetcher.py` icin sayim PERF-09'da). Proxy socket idle timeout 620 000 ms (56, 66) > 600 s. `_run_scan` docstring'i "5-minute timeout" der (467), sabit 600 s'dir (dokuman kaymasi).
- n: yok (kod); uretim sikligi PERF-13'te.
- Etiket: SUPPORTED (kod)
- Sinirlamalar: hangi yolun (koordinatorlu/koordinatorsuz) uretimde acik oldugu ortam degiskenine bagli; log alani `coordinator_version` ile PERF-12/13'te olculdu.
- Alternatif aciklama: yok.
- Sonraki adim: Level B - repair dongusune iptal kontrolu ve/veya varsayilan yolda kabul kontrolu (admission) degerlendirmesi.
- Kategori: FIX_CANDIDATE (Level B oneri; karar degil)

### PERF-06 - Thread havuzlari ve ic ice yapi

- Oncelik: P3
- Veri kaynagi / yontem: kod okuma + `PERF_code_scan.py` Bolum 2 (Ek C2).
- Etiket: SUPPORTED (kod); gercek thread sayisi/doygunluk olculmedi (NOT_MEASURABLE offline).

| Havuz | Konum | Boyut | Ic ice / not |
|---|---|---|---|
| API scan executor | `api/routers/scan.py:43` | 16 | Varsayilan yolda kabul kontrolu yok; ayni havuz summarize (669), analyze (713), chart (776) ile paylasiliyor |
| Koordinator | `core/scan_coordinator.py:ScanCoordinator.__init__:89-112` | `max_concurrent` (ctor varsayilani 1, kuyruk 1, kuyruk bekleme 120 s, tahmini is 480 s; 91-94) | Yalnizca `FINPILOT_SCAN_COORDINATOR=1` |
| Prefetch sembol-basina fallback | `scanner/data_fetcher.py:1368` | 10 (`scanner/evaluate.py:792`) | Her gorev `fetch_multi_timeframe` havuzu 3 -> en fazla 30 eszamanli `fetch`; yalnizca Alpaca + toplu yf basarisizsa |
| Repair | `scanner/data_fetcher.py:1243` | `min(4, kalan)` | Her gorev `fetch_multi_timeframe` havuzu `min(4, 3)=3` (1227, 679) -> is basina en fazla 12 eszamanli `fetch`, hepsi surec-genel 4/s kovasini paylasir |
| Degerlendirme | `scanner/evaluate.py:809,817` | `min(32, max(4, n))` = 200 sembolde 32 | Toplu yolda ic ice fetch yok (bkz. Dogru calisan kisimlar) |
| EODHD | `scanner/data_fetcher.py:1121,1134` | 16 | Yalnizca bayrak + anahtar |
| `yf.download` ic havuzu | `scanner/data_fetcher.py:969` (`threads=True`) | kutuphane tanimli (dogrulanmadi) | Repair toplu adimi ve toplam-hata yolu |

- Sonuc: Varsayilan yolda bir surecte 16'ya kadar tarama isi ayni anda calisabilir ve ayni yfinance kovasi ile ayni global sayaclari paylasir.
- Sonraki adim: canli protokolde (PERF-16) thread sayisi ve kuyruk bekleme alanlari.
- Kategori: KEEP_AS_IS (yapi); RESEARCH_NEXT (doygunluk)

### PERF-08 - Sembol-basina fallback'te 180 s zaman asimi tum prefetch sonucunu atar

- Oncelik: P0 (gecerlilik: sessiz bos batch riski; yalnizca nadir rejimde)
- Konum: `scanner/data_fetcher.py:prefetch_symbols_multi_timeframe:1368-1380` (`as_completed(futures, timeout=180)` 1371; iterator'un firlattigi `TimeoutError` icteki `try` (1373-1380) disinda kalir; `with ThreadPoolExecutor` cikisi calisan gorevleri bekler); `scanner/evaluate.py:788-797` (`except TimeoutError: all_data = {}`); `scanner/evaluate.py:813-815` ve `238-250` (bos sozluk -> bos cerceveler -> minimum veri kontrolu, 250).
- Veri kaynagi / yontem: kod okuma.
- Sonuc: Yalnizca Alpaca `None` + `yf.download` toplu bos rejiminde ulasilir: 180 s'de bitmeyen tek bir sembol, tamamlanmis tum sembollerin verisinin atilmasina yol acar; batch degerlendirilebilir veri olmadan devam eder. API imajlari `python:3.11-slim` kullanir (`Dockerfile:7,27`, `api/Dockerfile:2,9`; PERF-15); 3.11'de `concurrent.futures.TimeoutError` yerlesik `TimeoutError`'dur, dolayisiyla `scanner/evaluate.py:795` bunu yakalar.
- n: `result_symbols` alanli 132 adet 200-sembol batch'in hicbirinde sonuc sayisi 0 degil; `alpaca_total_failure=True` 6 batch (Ek C5, Q1 ciktisi). Yol loglarda gozlenmedi.
- Etiket: SUPPORTED (kod yolu); uretimde gerceklesme HYPOTHESIS.
- Alternatif aciklama: bilincli "kismi veriyle devam" tasarimi olabilir (log mesaji 796 "continuing with partial data" der), ancak kod kismi veriyi degil bos sozlugu kullanir -> mesaj ile davranis celisiyor.
- Sonraki adim: Level B - zaman asiminda tamamlanan sonuclari korumak; once kayit sikligini olcmek.
- Kategori: FIX_CANDIDATE

### PERF-05 - Surec-global sayaclar: `yf_fallback` semantigi ve `counters_unreliable`

- Oncelik: P0 (performans sayaclarinin gecerliligi)
- Konum: `scanner/data_fetcher.py:58-70` (`_YF_FETCH_COUNT`, `yf_fetch_count`, `reset_yf_fetch_count`); `scanner/data_fetcher.py:_note_yf_fetch:94-97`; `scanner/data_fetcher.py:fetch:440`; `scanner/data_fetcher.py:_note_alpaca_miss:173-176`; `api/routers/scan.py:_run_scan:478-483` (sifirlama); `api/routers/scan.py:_complete_scan:525` (yorum: "symbols that hit the slow yfinance fallback"); `core/scan_coordinator.py:submit_scan:301-314` (`prepare=reset_yf_fetch_count`); `core/scan_observability.py:ScanObservation.fields:117-122`.
- Veri kaynagi: `scan_timing.jsonl` snapshot (SHA-256 header'da).
- Yontem: `PERF_analysis.py` (`Q1_yf_fallback_mod3`, `Q1_GROUP_*`), kod okuma.
- Sonuc: (a) Sayac her `fetch` cagrisinda (sembol x zaman dilimi) artar; scan.py:525 yorumu "sembol" der. Pozitif `yf_fallback` degerlerinin 3'un kati olma orani: legacy %98.6 (n=292), guvenilir gozlem kaydi %96.3 (n=82), guvenilmez %88.9 (n=9); keyfi degerler icin beklenti ~%33. Bu desen, kalan her sembol icin 3 `fetch` (PERF-02) ile tutarli; `yf_fallback/3` ~ sembol-basina repair'e giren sembol sayisi (post median ~33.5, pre_all ~20). (b) Sayaclar modul-global; koordinatorsuz yolda her istek basinda sifirlanir (481), es zamanli isler birbirinin sayacini bozar; `alpaca_miss` atama ile uzerine yazilir (176). Gozlem katmani bunu isaretler: 200-sembol batch'lerde pre_obs 6/65, post 3/26 `counters_unreliable=True`; 333 legacy 200-sembol satirinda bayrak yok (yaklasik %11.1'i baska batch ile ortusuyor, PERF-12).
- n: 292 / 82 / 9 pozitif deger; 65 + 26 gozlem batch'i
- Etiket: SUPPORTED (kod + veri deseni); legacy satirlarin sayac gecerliligi UNRESOLVED.
- Sinirlamalar: cache isabeti veya ayni surecteki diger `fetch` cagrilari 3'un kati desenini bozabilir; %1-4'luk sapma bununla uyumlu ama dogrulanmadi.
- Alternatif aciklama: toplu yol ayri sayac kullanir (`_YF_BULK_*`, 117-132), deseni o uretemez.
- Sonraki adim: Level B oneri - sayaclari is basina (observation nesnesine) tasimak; scan.py:525 yorumunu duzeltmek.
- Kategori: FIX_CANDIDATE

### PERF-07 - `fetch` on-dogrulamasi her cagrida ek bir 1 yillik `history` istegi tetikliyor

- Oncelik: P3
- Konum: `scanner/data_fetcher.py:fetch:442-452` (her cagrida yeni `yf.Ticker(symbol)`; `tkr.fast_info` ve `getattr(info, "last_price", None)`); kutuphane (yerel yfinance 1.4.1): `yfinance/scrapers/quote.py:246-249` (`last_price` -> `self._get_1y_prices()`), `yfinance/scrapers/quote.py:129-131` (`self._tkr.history(period="1y", auto_adjust=False, keepna=True)`); pin `requirements.txt:13` `yfinance==1.4.1`.
- Yontem: `PERF_analysis.py` C.6/C.7 grep (Ek C5) + kod okuma.
- Sonuc: Her sembol-basina `fetch`, istenen `history()` cagrisindan once yeni Ticker uzerinde `last_price` okur; 1.4.1'de bu Ticker basina onbelleklenen bir 1 yillik gunluk `history` istegidir ve her `fetch` yeni Ticker olusturdugu icin her cagrida tekrarlanir. Kova cagri basina 1 token alir (436); ek istek kovada sayilmaz. Beklenen sonuc: sembol-basina repair'de sembol basina en az 6 Yahoo istegi (3 zaman dilimi x 2); `yf_fallback` bunun yarisini sayar. Ayni bilgi zaten bos `history()` sonucundan elde ediliyor (480-482).
- n: yok (kod)
- Etiket: SUPPORTED (uygulama kodu + pinlenmis surumun yerel kaynagi). API imajindaki kurulu surum dogrudan dogrulanmadi; uretimdeki istek sayisi/suresi HYPOTHESIS.
- Sinirlamalar: kutuphane satirlari grep ciktisidir; `_get_1y_prices` icindeki ek meta veri istekleri ve hata yollari okunmadi.
- Alternatif aciklama: on-dogrulama delisted sembol uyarisi icindir (444 yorumu); uyari degerli olabilir ama ek istek maliyeti belgelenmemis.
- Sonraki adim: Level B oneri - on-dogrulamayi kaldirma veya bayrak arkasina alma; PERF-16'da HTTP istek sayaci ile once/sonra olcum.
- Kategori: FIX_CANDIDATE

### PERF-09 - Bellek ve iptal: kod duzeyi riskler (canli ornekleme yok)

- Oncelik: P3
- Konum: `scanner/evaluate.py:789-815` (`all_data`: 200 sembol x 4 zaman dilimi gostergeli DataFrame, degerlendirme boyunca tutulur); `scanner/data_fetcher.py:_prefetch_alpaca_bulk:881,894` (`full_df` + sembol basina `.copy()`); `scanner/data_fetcher.py:_cache_data.wrapper:360-399` (L1 256 girdi; Redis L2 icin `to_dict(orient="records")` kopyasi 393-397); `core/cache.py:MemoryCache:291-335` (OrderedDict LRU, `popitem(last=False)` 334-335; sinir girdi sayisi, bayt degil); `scanner/performance.py:15,26,52,86-89` (global `_EVENTS` listesi; yalnizca `FINPILOT_SCAN_STAGE_TIMING=1` iken buyur, 18-20); `core/scan_coordinator.py:237-239` (`_jobs`/`_by_key` temizligi); `core/scan_observability.py:end_job:79-83` (`_ACTIVE_JOBS.pop`).
- Iptal: `scanner/data_fetcher.py` icinde `check_cancelled` eslesmesi 0 (C.1); `scanner/evaluate.py` kontrol noktalari 778, 799, 812, 820, 839, 847 (C.2).
- Yontem: kod okuma + grep (Ek C5).
- Sonuc: Sinirsiz bir yapi bulunmadi (93ae83c ile `_memory_cache` sinirsiz dict'ten 256 girdilik LRU'ya gecti, Ek C3). Risk, is basina gecici DataFrame'ler ile es zamanli is sayisinin carpimidir: varsayilan yolda surec basina 16'ya kadar is (PERF-06) ve zaman asimina ugrayan isciler bitene kadar (PERF-13: 133 s'ye kadar) bellegi tutar. Stage timing acikken `_EVENTS` tek global listedir; es zamanli islerin eventleri karisir ve tarama boyunca dogrusal buyur. Iptal isbirlikci oldugundan iptal edilen bir is prefetch+repair asamasini (PRIOR: Sep 22 kohortunda median 305 s) sonuna kadar calistirir.
- n: yok
- Etiket: SUPPORTED (kod yapisi); bayt cinsinden tepe bellek NOT_MEASURABLE (canli ornekleme yok).
- Sinirlamalar: `_EVENTS.clear()` (26) cagiran yer okunmadi; `add_indicators` bellek etkisi okunmadi.
- Alternatif aciklama: yok.
- Sonraki adim: PERF-16'da RSS/thread ornekleme.
- Kategori: NEEDS_MORE_DATA

### PERF-10 - 2026-10-16 13:57:32 UTC sonrasi 200-sembol batch gozlemi (karistirici etkili)

- Oncelik: P3
- Konum: `data/distribution/scan_timing.jsonl`; degisiklik `git show 93ae83c -- scanner/data_fetcher.py` (repair: `- for symbol in remaining:` -> `+ ThreadPoolExecutor(max_workers=min(4, len(remaining)))`; `_memory_cache` dict -> `MemoryCache(max_size=256)`), Ek C3/C5.
- Veri kaynagi: snapshot SHA-256 `8151086aac0d2407130aa44cf0b8b326202df70c5e0951f8835ddbc7bbffa131`; 424 tamamlanmis 200-sembol batch (legacy satirlari + is basina tek gozlem kaydi; `coordinator_version` hep bos oldugu icin yinelenme yok).
- Yontem: `PERF_analysis.py` Q1. Ayirim `total_s` tasiyan kaydin `ts`'i (tamamlanma zamani) ile. Mann-Whitney (normal yaklasim), Hodges-Lehmann (HL), median farki icin 4000 bootstrap; OLS `total_s ~ 1 + yf_fallback + post`, 2000 tabakali bootstrap; tohum 20261019; `counters_unreliable=True` satirlar OLS ve alt sinirdan cikarildi.

| Grup | n (legacy/obs) | Aralik (UTC) | total_s median [p25-p75] | seans ici / disi median (n) | yf_fallback median | yf_bulk_symbols median | alpaca_miss 15m/1h/1d median | counters_unreliable True/False/yok |
|---|---|---|---|---|---|---|---|---|
| pre_all | 398 (333/65) | 2026-08-02 .. 2026-10-16 13:05 | 316.79 [187.03-408.82] | 397.06 (87) / 297.43 (311) | 60.0 | 80.0 (n=112) | 43/35/0 (n=385) | 6/59/333 |
| pre_30d | 143 (78/65) | 2026-09-18 .. 2026-10-16 13:05 | 376.86 [282.06-443.60] | 407.04 (66) / 339.74 (77) | 57.0 | 80.0 (n=112) | 40/32/0 (n=132) | 6/59/78 |
| pre_obs_era | 65 (0/65) | 2026-10-08 16:22 .. 2026-10-16 13:05 | 342.23 [280.24-408.05] | 386.90 (23) / 317.25 (42) | 93.0 | 78.0 | 43/35/0 | 6/59/0 |
| post | 26 (0/26) | 2026-10-16 14:22 .. 2026-10-19 09:58 | 392.29 [317.48-443.76] | 406.59 (9) / 387.58 (17) | 100.5 | 81.0 | 44/36/0 | 3/23/0 |

| Karsilastirma (post - pre) | median farki (s) | %95 bootstrap | HL (s) | MWU p |
|---|---:|---|---:|---:|
| pre_all (n=398) | +75.5 | [+36.2, +110.4] | +60.4 | 0.021 |
| pre_30d (n=143) | +15.4 | [-30.7, +55.3] | +8.7 | 0.70 |
| pre_obs_era (n=65) | +50.1 | [-3.1, +94.3] | +37.9 | 0.161 |
| OLS, tum bilinen (392/23) | kaydirma +21.1 | [-13.1, +56.1] | egim 1.224 s / yf_fallback | - |
| OLS, pre_30d + post (137/23) | kaydirma -14.0 | [-56.1, +23.6] | egim 0.992 s / yf_fallback | - |

- Sonuc: Kesim sonrasi `total_s` dususu gorulmedi. Yakin donemle (pre_30d) ve `yf_fallback` duzeltmesiyle fark sifiri kapsar. Tum pre ile karsilastirmadaki +75.5 s, donem kaymasini (pre_all median 316.8 vs pre_30d 376.9) yansitiyor. Post'ta repair yuku daha agir (`yf_fallback` 100.5); `yf_bulk_requests` tum gruplarda median 2 (15m+1h; 1d eksigi gozlem doneminde 0). Gozlemsel egim, sembol-basina `fetch` cagrisi basina ~1.0-1.2 s marjinal `total_s` (repair sembolu basina ~3.0-3.7 s) ile uyumlu; post gunleri: 2026-10-16 n=18 (median 393.95 s; 9 seans ici, 9 disi), 2026-10-19 n=8 (352.57 s; hepsi seans disi).
- n: post 26; pre_30d 143; pre_obs 65; pre_all 398
- Etiket: SUPPORTED ("iyilesme gorulmedi"); nedensel etki UNRESOLVED.
- Sinirlamalar: farkli semboller, seans karisimi (post seans ici n=9), yuk, yalnizca 2 gun; API'nin 93ae83c'yi 13:57:32'de yukledigi kullanici bilgisidir: jsonl'da build/SHA alani yok ve `process_id` 7, 2026-10-08..2026-10-18 araliginda ayni (Docker PID tekrari) -> yukleme loglardan dogrulanamaz.
- Alternatif aciklamalar: (1) paralel repair Yahoo tarafinda gecikme/kisitlama nedeniyle hiz kazandirmiyor; (2) PERF-07 ek istekleri ve PERF-03 kovasi paralellik kazancini sinirliyor; (3) yeni kod post donemde yuklu degildi; (4) post'taki daha yuksek repair yuku. Bu veriyle ayristirilamaz.
- Sonraki adim: (a) offline: `total_s ~ yf_fallback x period` etkilesim modeli ve post satirlarinda `stage_timing` (`data/PERF_batches.csv`, `stage_timing_n`) incelemesi; (b) PERF-16 kontrollu kosu.
- Kategori: NEEDS_MORE_DATA

### PERF-11 - Token kovasi kaynakli teorik alt sinir (ESTIMATED)

- Oncelik: P3
- Konum: formul PERF-03 (`scanner/data_fetcher.py:fetch:427-440`, `core/rate_limiter.py:65-82`); girdi `yf_fallback` (= sembol-basina `fetch` cagrisi, PERF-05).
- Yontem: batch basina LB = max(0, yf_fallback - 8) / 4 s (kod varsayilanlari; guvenilmez isaretli satirlar haric); LB / total_s (`PERF_analysis.py` `Q1_rate_limit_lower_bound`).
- Sonuc: pre_all (n=392): LB median 12.63 s (p90 34.75, maks 52.75), LB/total_s median 0.041 (p90 0.110, maks 0.297). pre_30d (n=137): 11.50 s; 0.040 (maks 0.184). post (n=23): 23.50 s (p90 37.60, maks 43.75); 0.065 (maks 0.103). PRIOR Sep 22 kohortunun `yf_fallback` araligi 81-198 icin LB 18.25-47.5 s; ayni kohortta `prefetch.repair` median 305 s (PRIOR).
- n: 392 / 137 / 23
- Etiket: ESTIMATED. Kova tek basina `total_s`'nin median %4-7'sini aciklar; geri kalan sure cagri gecikmesi x sinirli paralellik, PERF-07 ek istekleri, Alpaca ve degerlendirme asamalari arasinda paylasilir (ayrim offline NOT_MEASURABLE).
- Sinirlamalar: uretimdeki RATE/BURST bilinmiyor (`docker-compose.yml`'da anahtar yok; `.env` okunmadi); `wait(timeout=5)` sinirin delinmesine izin verir (PERF-03); alt sinir gecikmeyi sifir varsayar; gecikme tabanli alt sinir icin cagri basina sure gerekir.
- Alternatif aciklama: yok.
- Sonraki adim: PERF-16'da `rate_limit.wait` toplami ve `fetch.request` sureleri.
- Kategori: RESEARCH_NEXT

### PERF-12 - Es zamanli isler: siklik, sayac tutarliligi ve sure iliskisi

- Oncelik: P3
- Veri kaynagi: snapshot; gozlem kayitlari (161 is: `api_scan` 112, `scanner_agent` 49).
- Yontem: `PERF_analysis.py` Q2; `job_started`/`job_finished` `ts` araliklarindan sweep-line; sayac alanlariyla capraz tablo; 200-sembol `api_scan` isleri icin MWU + HL + Spearman (2000 permutasyon).
- Sonuc:
  - Tum islerin toplam mesgul suresi 35 066.5 s; bunun 336.7 s'sinde >= 2 is aktif (%1.0). 21/161 is (%13.0) en az bir isle ortusuyor (`api_scan` %13.4, `scanner_agent` %12.2); surecler arasi ortusme 0.
  - `active_jobs_at_start` {1: 149, 2: 12}; `active_jobs_at_end` {1: 149, 2: 12}; `peak_active_jobs` {1: 140, 2: 21}; `counters_unreliable` is sonunda 21 True / 140 False, istek kaydinda 14 True / 96 False.
  - Aralik tabanli ayni-surec ortusmesi ile `peak_active_jobs > 1` 161/161 iste ayni (21 ikisi True, 140 ikisi False).
  - Legacy 200-sembol satirlarinda yaklasik aralik (`ts - total_s - persist_s`) ile 37/333 (%11.1) ortusme.
  - 200-sembol `api_scan` isleri (n=96): ortusmeyen 84 is `job_s` median 349.27 s [277.97-406.10]; ortusen 12 is median 542.21 s [465.13-579.15], maks 733.20 s; HL +185.8 s, MWU p < 0.001; Spearman(n_overlap, job_s) 0.421 ve Spearman(peak, job_s) 0.417 (permutasyon p < 0.001). `total_s`: istek-guvenilmez 9 batch median 517.62 s, guvenilir 82 batch 349.64 s.
- n: 161 is; 96 is (200-sembol); 333 legacy satir
- Etiket: siklik ve sayac tutarliligi MEASURED (log tabanli); sure iliskisi SUPPORTED (gozlemsel); nedensellik HYPOTHESIS.
- Sinirlamalar: uzun bir isin ortusme olasiligi suresiyle artar (uzunluk yanliligi); toplam ortusme suresi kisa (336.7 s) oldugundan "yavas is sonraki isle ortusur" aciklamasi "ortusme yavaslatir" kadar olasi; legacy araliklari yaklasik; `active_jobs_scope=process`.
- Alternatif aciklama: 3 zaman asimi isi (PERF-13) ortusen grupta; 733.20 s'lik is grubun maksimumu.
- Sonraki adim: PERF-16'da tek-is izolasyonu; gerekirse bilincli ikili ortusme kosulu.
- Kategori: KEEP_AS_IS (gozlem katmani); NEEDS_MORE_DATA (etki)

### PERF-13 - Istek ve isci suresi: 600 s zaman asimindan sonra biten isciler

- Oncelik: P0 (kapsam/gecerlilik: zaman asiminda batch sonucu kalici yazilmaz)
- Konum: `api/routers/scan.py:_run_scan:488-506` (`_complete_scan` yalnizca basarili beklemeden sonra, 513); `api/routers/scan.py:run_scan:323-370` (`finish_request` finally icinde); `core/scan_observability.py:end_job:76-87`, `finish_request:130-139`.
- Veri kaynagi: snapshot; `job_id` uzerinden istek/is birlestirme.
- Yontem: `PERF_analysis.py` Q3.
- Sonuc: 110 istekli is: `ok` 107, `timeout` 3 (hepsi 200 sembol, `HTTPException`, request_s 600.001-600.002 s) -> gozlem donemindeki 94 adet 200-sembol API isteginin 3'u (%3.2). Uc iscinin ucu de `job_finished|ok`: job_s 601.48 / 610.17 / 733.20 s; istek bitiminden 1.57 / 10.18 / 133.19 s sonra (istek bitisleri 2026-10-08 17:17:10, 2026-10-16 12:42:14, 2026-10-16 12:57:54 UTC). Basarili isteklerde `request_s - job_s` median 0.29 s (p90 0.65, maks 1.51; n=107); yaklasik executor kuyruk beklemesi median 0.034 s (p90 0.062). Sahipsiz `job_started` 0; isci baslamadan biten istek 0; client disconnect 0; 161 is sonunun tamami `ok`.
- Anomali: bir basarili istekte yaklasik kuyruk beklemesi -42.9 s (is basi `ts`'i istek basindan once) - duvar saati kaymasi veya kayit sirasi; UNRESOLVED.
- n: 110 istek; 3 zaman asimi
- Etiket: MEASURED (log); zaman asiminda kalicilik yapilmamasi SUPPORTED (kod); gunluk ciktiya etkisi UNRESOLVED (UI yeniden deneme davranisi okunmadi).
- Sinirlamalar: legacy donemde zaman asimi kaydi yok (`total_s` yalnizca basarili isteklerde) -> 2026-10-08 oncesi siklik NOT_MEASURABLE.
- Alternatif aciklama: yok.
- Sonraki adim: Level B oneri - zaman asiminda isciyi isbirlikci iptal etmek (PERF-04) veya sonucu kaydetmek; web scanner batch yeniden deneme mantigini okumak.
- Kategori: FIX_CANDIDATE

### PERF-14 - Cache katmanlari ve kalici fiyat/intraday cache okumasi

- Oncelik: P3
- Konum: `scanner/data_fetcher.py:_market_aware_ttl:199-210` ve `CACHE_TTL_SECONDS:213` (import aninda bir kez: ABD seans saatinde 300 s, disinda ve hafta sonu 3600 s); `scanner/data_fetcher.py:217-218` (L1 256); `scanner/data_fetcher.py:_cache_data.wrapper:360-399` (anahtar `finpilot:ohlcv:{func}:{args}:{kwargs}`, 361, tarih icermez; her cagrida `cleanup_expired()` + `cache_manager.cleanup()`, 362-367; L2 yalnizca `l2_only=True`, 375 ve 397); `core/cache.py:CacheManager:511-547`; `core/cache.py:793-796` (L2 yalnizca `settings.cache.redis_enabled` iken Redis).
- Yontem: kod okuma + grep C.1/C.2/C.4.
- Sonuc: Taramada okunabilen cache yalnizca sembol-basina `fetch` yolundadir: surec-ici L1 (256 girdi; TTL import aninda donar) ve istege bagli Redis L2. Alpaca toplu, `yf.download` toplu ve EODHD yollarinda cache yok; her batch bunlari yeniden ceker. Okunan prefetch zincirinde (408-1380) diskten kalici fiyat/intraday cache okumasi yok; `data_fetcher.py`'deki sqlite/dosya erisimleri (1434-1452, 1542, 1756) zincirin cagirmadigi fonksiyonlarda; `scanner/evaluate.py`'de parquet/csv/json/sqlite okuma eslesmesi yok. API 2026-10-16 13:57 UTC'de (Cuma, kodun seans tanimi icinde) baslatildiysa surec TTL'si 300 s'de sabitlenmistir.
- n: yok
- Etiket: SUPPORTED (kod); uretimde Redis durumu UNRESOLVED; `data/eodhd_client.py` (EODHD bayragi varsayilan kapali) kendi cache'i icin okunmadi: UNRESOLVED; L1 isabet orani loglanmadigi icin NOT_MEASURABLE.
- Sinirlamalar: `add_indicators` modulu okunmadi.
- Alternatif aciklama: yok.
- Sonraki adim: L1/L2 isabet sayaclarini PERF-16 alanlarina eklemek; TTL'nin import aninda donmasi icin Level B degerlendirme.
- Kategori: RESEARCH_NEXT

### PERF-15 - Uretim yolu ve yapilandirma kanitlari

- Oncelik: P3
- Konum: `core/scan_coordinator.py:259-265` (ortam: `FINPILOT_SCAN_MAX_CONCURRENT` "1", `FINPILOT_SCAN_QUEUE_CAPACITY` "1", `FINPILOT_SCAN_QUEUE_WAIT_S` "120", `FINPILOT_SCAN_ESTIMATED_JOB_S` "480", `FINPILOT_SCAN_DEDUPE` "1", `FINPILOT_SCAN_COOP_CANCEL` "1"); `Dockerfile:7,27` ve `api/Dockerfile:2,9` (`python:3.11-slim`); `docker-compose.yml` (aranan anahtarlar icin eslesme yok: `YFINANCE_RATE`, `YFINANCE_BURST`, `FINPILOT_SCAN_*`, `FINPILOT_ENABLE_EODHD_BARS`, `FINPILOT_DISABLE_ALPACA`, `uvicorn`, `--workers`, `mem_limit`, `cpus`); `requirements.txt:13` (`yfinance==1.4.1`), `requirements.txt:73` (`alpaca-py==0.43.2`).
- Veri kaynagi: snapshot + yapilandirma dosyalari (sir maskeli grep, Ek C5).
- Sonuc: 481 gozlem kaydinin tamaminda `coordinator_version` bos -> loglanan tum isler koordinatorsuz varsayilan yoldan gecti (kabul kontrolu ve `shield` davranisi uretimde gozlenmedi). `process_id`: 7 (2026-10-08 16:14 .. 2026-10-18 16:57, 410 kayit), 6 (2026-10-15 12:11 .. 14:11, 36), 9 (2026-10-19 09:14 .. 11:09, 35). Performans anahtarlari compose dosyasinda yok; etkin degerler `.env`'e bagli.
- n: 481 kayit
- Etiket: MEASURED (log alanlari); etkin yapilandirma UNRESOLVED.
- Sinirlamalar: alpaca-py yerelde kurulu degil; imaj icerigi dogrulanmadi.
- Alternatif aciklama: yok.
- Sonraki adim: PERF-16 alanlarina etkin yapilandirma dokumu (degerler, sir degil).
- Kategori: KEEP_AS_IS

### PERF-16 - Gerekli asgari canli olcum protokolu (insan onayi gerekli; uygulanmadi)

- Oncelik: P3 (olcum altyapisi)
- Seviye: Level C - canli provider cagrisi ve uretim veri yazimi icerir: `_complete_scan` shortlist, shadow ledger, watchlist ve distribution export yazar (`api/routers/scan.py:601-609`). AI uygulayamaz; bu yalnizca oneridir.
- Yakalanacak alanlar: (A) mevcut (gozlem acik + `FINPILOT_SCAN_STAGE_TIMING=1`): `event`, `job_id`, `request_id`, `caller`, `ts`, `universe`, `request_s`, `job_s`, `total_s`, `eval_s`, `enrich_s`, `persist_s`, `yf_fallback`, `yf_bulk_requests`, `yf_bulk_symbols`, `alpaca_miss{15m,1h,1d}`, `intraday_coverage`, `alpaca_total_failure`, `result_symbols`, `active_jobs_at_start/end`, `peak_active_jobs`, `counters_unreliable`, `coordinator_version`, `queue_wait_s`, `process_id`; stage eventleri `prefetch.alpaca`, `prefetch.repair`, `prefetch.symbol_repair`, `fetch.request`, `fetch.parse`, `rate_limit.wait`, `retry.attempt`, `retry.backoff`, `evaluation.symbol`. (B) asgari ek alanlar (kod degisikligi Level B ya da dis toplama): calisan kodun git SHA'si ve surec baslangic zamani; etkin `YFINANCE_RATE`/`YFINANCE_BURST`, Redis acik/kapali, `CACHE_TTL_SECONDS` (degerler, sir degil); sembol-basina repair'e giren sembol sayisi ve zaman dilimi basina eksikler; `wait()` False sayisi; Yahoo HTTP istek sayisi (fast_info dahil); L1/L2 isabet/iska; surec RSS, CPU zamani, thread sayisi (is basi/sonu + 5 s ornekleme); kampanya kimligi ve kosu sirasi; seans etiketi.
- Kosu sayisi: kosul basina >= 5 kosu; kosullar (1) soguk: kosu 1 oncesi surec yeniden baslatma, (2) sicak: TTL icinde hemen tekrar; ayni sabit 200-sembol listesi (SHA ile kayitli); onay varsa ek 1 tam evren zinciri (dis duvar saati ile); seans sabit tutulur veya tabakalanir.
- Izolasyon: tek is (koordinator `max_concurrent=1` veya operator teyidiyle baska tarama/`scanner_agent`/scheduler yok; her kosuda `counters_unreliable=False` kabul sarti); web UI kullanimi yok; ayni host ve kaynak limitleri; kalicilik yan etkileri icin onayli hedef (ornegin ayri `FINPILOT_DIST_DIR`; diger kalicilik adimlari icin ayri insan karari).
- On-kayitli analiz: birincil `job_s` ve `prefetch.repair`; ikincil `rate_limit.wait` toplami ve HTTP istek sayisi; kosullar arasi HL + bootstrap %95; n=5 ile en fazla SUPPORTED.
- Etiket: NOT_MEASURABLE (offline); oneridir, karar degildir.
- Kategori: NEEDS_MORE_DATA

<!-- BULGULAR-NEXT -->

## Dogru calisan kisimlar

- Gozlem katmani: `peak_active_jobs > 1` ile `job_started`/`job_finished` araliklarindan kurulan ayni-surec ortusmesi 161/161 iste ayni (MEASURED, PERF-12).
- Is yasam dongusu kayitlari eksiksiz: 161 `job_started` = 161 `job_finished`; sahipsiz is 0; isci baslamadan biten istek 0; tum is sonlari `ok` (MEASURED, PERF-13).
- API executor doymamis: `request_s - job_s` median 0.29 s, yaklasik kuyruk beklemesi median 0.034 s (MEASURED; bir -42.9 s anomalisi haric).
- 3 zaman asiminin `request_s` degerleri 600.001-600.002 s: backend siniri proxy'nin 620 s socket timeout'undan once devreye giriyor (MEASURED + `web/src/app/py-api/[...path]/route.ts:55-56,64-66` SUPPORTED).
- Koordinator yolu sayaclari is basinda sifirlar (`core/scan_coordinator.py:submit_scan:301-314`, `prepare` 206-207) ve is kayitlarini temizler (237-239) (SUPPORTED, kod; uretimde kullanilmiyor, PERF-15).
- Toplu degerlendirmede ic ice fetch yok: `evaluate_symbol` yalnizca `prefetched_data is None` iken fetch eder (`scanner/evaluate.py:238-246`); toplu yol `{}` gecirir (813-815) (SUPPORTED).
- OHLCV L1 cache sinirli LRU: `scanner/data_fetcher.py:217-218`, `core/cache.py:302-335`; 93ae83c oncesi sinirsiz dict idi (SUPPORTED, git diff).
- `TokenBucket` kilit altinda refill/tuketim yapar (`core/rate_limiter.py:49-82`) (SUPPORTED).
- Alpaca istemcisi surec genelinde tekil ve yeniden kullaniliyor (`scanner/data_fetcher.py:_get_alpaca_client:264-280`) (SUPPORTED).
- Alpaca 1d kapsami: gozlem donemindeki 91 adet 200-sembol batch'in tamaminda `alpaca_miss.1d = 0`; pre_all maksimum 8 (MEASURED). `yf_bulk_symbols` median'i 15m+1h eksik median toplamina yakin (pre_obs 78 vs 43+35; post 81 vs 44+36) - kodla tutarli (SUPPORTED, yalnizca median duzeyi).
- PRIOR yeniden uretim: ilk 820 kayitta 416 adet 200-sembol `total_s` satiri, median 321.38 s - 2026-10-18 raporuyla ayni (REPRODUCED).

<!-- DOGRU-NEXT -->

## Cevaplanamayan sorular

- API'nin 93ae83c'yi 2026-10-16 13:57:32 UTC'de yukledigi (kullanici bilgisi): loglarda build/SHA alani yok - UNRESOLVED.
- Paralel repair'in post donemde etkin olup olmadigi ve `prefetch.symbol_repair` suresi: post satirlarinin `stage_timing` icerigi bu raporda incelenmedi (`data/PERF_batches.csv` `stage_timing_n`) - UNRESOLVED.
- Etkin `YFINANCE_RATE`/`YFINANCE_BURST`, Redis, `FINPILOT_SCAN_STAGE_TIMING` degerleri - UNRESOLVED (`.env` kural geregi okunmadi).
- Cagri basina Yahoo gecikmesi, ag/CPU ayrimi, gercek HTTP istek sayisi (fast_info dahil) - NOT_MEASURABLE (offline).
- Is basina tepe bellek ve thread sayisi - NOT_MEASURABLE (canli ornekleme yok).
- alpaca-py 0.43.2 `limit` semantigi (toplam ust sinir mi) - UNRESOLVED (paket yerelde kurulu degil).
- 112 `api_scan` isine karsilik 110 istek kaydi: 2 isin istek kaydi yok - UNRESOLVED.
- Zaman asimina ugrayan batch'lerin web arayuzunde yeniden denenip denenmedigi - UNRESOLVED.
- Tam evren uctan uca suresi (PRIOR bosluk devam ediyor) - NOT_MEASURABLE bu veriyle.
- -42.9 s negatif kuyruk beklemesi anomalisi - UNRESOLVED.

<!-- CEVAP-NEXT -->

## Sinirlamalar

- Snapshot 2026-10-19T11:19:03Z'de alindi; dosya append-only ve buyuyor (on kontrolde 1 927 626 bayt, snapshot'ta 1 929 460 bayt).
- Post penceresi kucuk ve karisik (n=26, 2 gun, seans ici n=9); D7 geregi hicbir veri seti out-of-sample sayilmaz; bu rapor getiri/sonuc hesaplamaz.
- Seans etiketi kodun UTC tanimini (hafta ici 13:30-20:00) kullanir; tatil takvimi yok.
- `total_s` kalicilik/kuyrugu kapsamaz (PRIOR); `job_s` yalnizca isci suresidir.
- MWU p degerleri normal yaklasim (numpy uygulamasi; scipy importu ilk kosuda kesildi, Ek C4); bootstrap tohumu 20261019; OLS dogrusal, etkilesimsiz.
- Legacy satirlarda `counters_unreliable` yok; legacy ortusmesi yaklasik araliklarla.
- Yerel yfinance 1.4.1 pinle ayni, API imaji dogrulanmadi; alpaca-py yerelde yok.
- Canli olcum, provider/HTTP cagrisi, docker, scanner kosusu yapilmadi; kod iddialari HEAD 93ae83c icindir (calisma agaci bu dosyalarda HEAD ile ayni).
- Bazi satir numaralari (ornegin 1202, 1215, 375, 397, 480-482) okunan araliklarda grep capalarindan sayilarak belirlendi.

<!-- SINIR-NEXT -->

## Ek: komutlar

- C1 (PowerShell, salt-okunur): `git -C C:\Users\meric\Borsa rev-parse HEAD` -> `93ae83c0c6056593fde65c97358824207c97ec6d`; `rev-parse --abbrev-ref HEAD` -> `review/pending-2026-10-07`; `status --porcelain=v1 -uall` -> 120 satir (bu rapor dosyasi o anda olusturulmustu); `diff --cached --name-only` -> `web/public/demo_snapshot.json`; `Get-Item data/distribution/scan_timing.jsonl` -> 1 927 626 bayt, mtime 2026-10-19T10:09:17Z; `git log -1 93ae83c` -> 2026-10-16 15:33:33 +0200.
- C2: `python.exe -B reports/scanner_intelligence_audit_v1_2026-10-19/scripts/PERF_code_scan.py` (grep: `scanner/data_fetcher.py`, `core/rate_limiter.py`, `api/routers/scan.py`, havuzlar, timing yazicilari, proxy).
- C3: `git show --stat 93ae83c`; `git show 93ae83c -- scanner/data_fetcher.py` (ilk 90 satir); `git diff --stat HEAD -- scanner/data_fetcher.py scanner/evaluate.py core/rate_limiter.py core/scan_observability.py core/scan_coordinator.py api/routers/scan.py web/src/app/py-api` -> bos.
- C4: `python.exe -B .../scripts/PERF_analysis.py` ilk kosu: scipy importu sirasinda KeyboardInterrupt; cikti dosyasi yazilmadi; betik numpy-only yapildi.
- C5: `python.exe -B .../scripts/PERF_analysis.py` (tek bellek snapshot'i, SHA-256 `8151086aac0d2407130aa44cf0b8b326202df70c5e0951f8835ddbc7bbffa131`) ardindan salt-okunur `git status`; ciktilar `data/PERF_batches.csv` (493 batch), `data/PERF_jobs.csv` (161 is), `data/PERF_summary.json`; kod grep bolumleri C.1-C.8 (`git show 93ae83c` repair hunk dahil).
- Kod okuma (read_file): `scanner/data_fetcher.py` 195-700 ve 800-1385; `scanner/evaluate.py` 226-252 ve 770-850; `core/scan_observability.py` 1-230; `core/scan_coordinator.py` 1-200; `api/routers/scan.py` 323-620; `core/rate_limiter.py` 34-112; PRIOR raporlar.

<!-- EK-NEXT -->

<!-- END -->
