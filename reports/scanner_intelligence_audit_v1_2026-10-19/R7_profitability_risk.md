# R7 - Istatistiksel Dogrulama, Karlilik ve Risk (WP-8 / WP-9)

| Alan | Deger |
|---|---|
| Baslik | R7 - Statistical Validation, Profitability and Risk |
| Versiyon | v1 |
| Tarih | 2026-10-19 |
| Durum | DRAFT - Level A arastirma ciktisi; karar degildir |
| HEAD | 93ae83c (branch `review/pending-2026-10-07`) |
| Rol | Statistical Validation, Profitability and Risk (PREFIX `PRF`) |
| Kapsam | WP-8: brut getiri dagilimi, gun-kumelenmis belirsizlik, maliyet duyarliligi, evren karsilastirmasi, brut portfoy gorunumu. WP-9: istatistiksel guvenilirlik ve OOS durumu (onceki denetimlerin ozeti + yeni eklenenler). |
| Girdiler | `data/finpilot.db` tablo `signals_archive` (SHA-256 `b64c0c5262e0d685daa1309e6293d27c208f64a6fc213b3c00e3cb896bd5f5f6`); `data/backtest_out/full_universe_enriched_labeled.csv` (SHA-256 `1C59DE39BDFFF56CED9436B4DE6555E4E8457FDB761669E41673F8BEF7730000`; sonuc kolonu yalniz scan_date <= 2025-12-31); `data/backtest_out/sector_map_full.csv` (SHA-256 `E16B840D0A456706DDD4EBDF471324079DC3AFDC7FB2F2BC5F56ECBA8707308A`); metadata: `data/backtest_out/fundamentals_sentiment_holdout.json`, `reports/fixed_target_full_universe_2026-08-0{4,5}.{md,json}`, `data/backtest_out/fixed_target_full_universe_2026-08-11.md`; PRIOR: `reports/outlier_dependence_audit_v1_2026-10-14/` (3 dosya), `reports/oos_status_c_remediation_v1_2026-10-15/oos_status_c_remediation_plan.md`, `docs/governance/decision-log.md` (L53-60, L80, L89-93, L110-121); kod: `p0_execution_replay.py`, `common_buy_accuracy.py`, `research/protocol.py`, `scripts/run_fixed_target_research.py` |

Not: Bu rapor salt-okunur bir arastirma ciktisidir. Hicbir sonuc out-of-sample (OOS) olarak etiketlenmemistir (insan karari D7, 2026-10-16). Brut getiriler net getiri veya beklenti (expectancy) degildir. Al/sat onerisi veya hedef fiyat icermez.

## Ozet

- Baseline yeniden uretildi (REPRODUCED): decided kume 5,206 sinyal, getiri = `resolved_pct_barrier` (brut bariyer, yuzde). Ortalama +0.3984 %, medyan -0.6431 %, kazanma %30.06, brut PF 1.448; skew 3.87 (F-PRF-01, F-PRF-04).
- Sinyal tarihi: `ts` arsive ekleme zamanidir; `signal_date` kullanildi (F-PRF-03). 48 gun kumesiyle (B=5000, seed 20261019) ortalama %95 CI [+0.111, +0.652], medyan CI [-0.778, -0.544]; tasarim etkisi ~7.8 (F-PRF-05).
- P0 (F-PRF-07): net toplamin %65.9'u arsive 5-145 gun gecikmeyle yazilan 1,616 satirdan (tamami `scanner_v1`, 11 gun) geliyor. Es zamanli 3,590 satirda ortalama +0.197 %, CI [-0.055, +0.461]; 0.25 pp duz maliyette negatif. Secim/geri doldurma yanliligi HYPOTHESIS.
- Kirilganlik: ust %5 net toplamin %138.5'i; ust %5 cikarilinca ortalama -0.16 %; en olumlu 10 gun cikarilinca -0.03 %. 5 USD alti 344 satir net toplamin ~%56'si; >= 5 USD satirlarda CI sifiri iceriyor (F-PRF-04/05/08).
- Maliyet duyarliligi (net degil): basabas duz maliyet 0.40 pp; CI alt siniri ~0.11 pp'de sifir; 0.55 pp'de ortalama -0.15 % (F-PRF-06). Gercek spread/dolum bilinmiyor.
- Evren karsilastirmasi NOT_MEASURABLE (F-PRF-10); brut portfoy gorunumu varsayima bagli, eszamanlilik olculemez (F-PRF-09). `resolved_pct_t5` bozuk (max +11,990 %), `resolved_pct` bariyer alaninin kopyasi (F-PRF-01/02).
- WP-9 (F-PRF-11): PRIOR coklu test (3,120 konfigurasyon; White RC p 0.28-0.74; Hansen SPA p 0.29-0.78; PBO 0.4-0.6) ve OOS durumu (bagimsiz OOS yok; D7) degismedi. Hicbir sonuc OOS olarak etiketlenmedi.
- Kilit kapsami (veri-seti mi, takvim mi) belirsiz; bu rol veri-setine ozgu yorumu uyguladi, insan karari gerekir (F-PRF-00).

## Kapsam ve yontem

- Veri kaynagi: `data/finpilot.db`, tablo `signals_archive` (5,748 satir; 11 kolon: id, symbol, ts, score, finpilot_score, payload_json, resolved_status, resolved_pct, resolved_pct_t5, resolved_pct_barrier, resolved_status_barrier). DB SHA-256 `b64c0c5262e0d685daa1309e6293d27c208f64a6fc213b3c00e3cb896bd5f5f6` (7,811,072 bayt, mtime 2026-10-19 12:08:56 yerel saat; okuma oncesi ve sonrasi hash ayni; `-wal`/`-shm` dosyasi yok). PowerShell `Get-FileHash` dosya baska bir surec tarafindan acik oldugu icin okuyamadi; hash Python ile salt-okunur `open(..., 'rb')` uzerinden alindi (PRF_01).
- Erisim: `sqlite3.connect('file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro', uri=True)` + `PRAGMA query_only=ON`. DB'de 27 tablo var; adi hold/lock/seal/partition/oos/embargo iceren tablo yok.
- Karar verilmis kume (decided set): `resolved_status_barrier IN ('resolved_win','resolved_loss') AND resolved_pct_barrier IS NOT NULL` -> n = 5,206 (PRIOR ile ayni tanim ve sayi). Disarida: 532 NULL durum, 10 `expired_win`/`expired_loss`.
- Getiri alani: `resolved_pct_barrier` (yuzde birimi, brut, sinyal basina; maliyet, boyutlandirma, kayma yok). Gerekce: F-PRF-01, F-PRF-02.
- Sinyal tarihi: `payload_json.signal_date` (F-PRF-03). Duyarlilik: `ts` tarihi (PRIOR ile karsilastirma icin) ve "sonraki ilk is gunu" oturum kumesi (hafta sonu -> Pazartesi; ABD tatilleri islenmedi).
- Belirsizlik: sinyal tarihine gore kume bootstrap; seed ve iterasyon sayisi ilgili bulguda.
- Kilit/holdout yorumu: F-PRF-00. Hicbir sonuc OOS olarak etiketlenmedi (D7, 2026-10-16).
- Arac: `C:\Users\meric\AppData\Local\Programs\Python\Python312\python.exe -B`; scriptler `scripts/PRF_*.py`, turetilmis dosyalar `data/PRF_*`.

## Bulgular

### F-PRF-00 - Kilitli/holdout bolumleri veri-setine ozgu tanimli; `signals_archive` icin tanimli bolum yok; takvim yorumu acik degil

- Priority: P0 (validity / governance)
- file:function:lines: `p0_execution_replay.py:24-25` (`DISCOVERY_END = "2026-04-17"`, `VALIDATION_END = "2026-05-21"`); `common_buy_accuracy.py:23-24` (`LEGACY_CSV` = `full_universe_enriched.csv`, `V2_CSV` = `enriched_signals_v3.csv`), `common_buy_accuracy.py:main:79,107` (`locked_oos` = date > `VALIDATION_END`); `scripts/run_fixed_target_research.py:main:202,243,274-277` (`TemporalSplit`, `locked_oos_rows_unopened`, holdout durumu); `research/protocol.py:31,146` (`TemporalSplit`, `LockedHoldoutGuard`).
- Data source: `data/backtest_out/fundamentals_sentiment_holdout.json` (yalniz metadata: status `not_opened_locked_holdout`, `historical_cutoff` 2026-06-08, `rows: []`); `reports/fixed_target_full_universe_2026-08-05.json` dataset blogu (csv `full_universe_enriched.csv`, csv_sha256 `38b981b3...e896`, ay ve split kapsami); `docs/governance/decision-log.md` L110-121.
- Method: dosya adi taramasi (`git ls-files`, `data/`), DB tablo adlari, kod satirlari (Select-String / read_file), yalniz metadata.
- Result: (1) C1 `locked_oos` = arastirma CSV'lerinde date > 2026-05-21. (2) C6 fixed-target: 2026-08-04/05 kosularinda train 2,022 satir = 2025-09..2025-12 ay kapsamlarinin toplami (1,678+332+6+6), validation 0, locked 22,709 = 2026-04..06 toplami (1,137+11,204+10,368); 2026-08-11 kosusunda 14,515 / 11,588 / 269. Kesin sinir tarihleri artefaktlarda yok (CLI argumani). (3) C5 PIT holdout: cutoff 2026-06-08, satir listesi bos. (4) `signals_archive` icin tanimli bolum, kilit dosyasi veya kilit tablosu bulunamadi; PRIOR Q5 denetimi tum decided arsivi kullandi. (5) Metadata: 5,206 decided satirdan 32'sinin herhangi bir aday tarihi (`ts` tarihi, `added_at`, `signal_date`) 2026-05-21 sonrasinda; tum 5,748 satirdan 29'unun 2026-06-08 sonrasinda.
- n: 5,748 arsiv satiri (metadata), 5,206 decided.
- Label: SUPPORTED (bolum tanimlari); yorum UNRESOLVED.
- Limitations: C6 sinir tarihleri kayitli degil; erisim logu yok (PRIOR remediation F09/F10).
- Alternative explanations: bolumler veri-setinden bagimsiz takvim pencereleri olarak amaclanmis olabilir; o durumda 2026-04..06 tum kaynaklarda kilitli sayilir ve bu raporun arsiv analizlerinin buyuk kismi kapsam disi kalir (brief ile celisir).
- Bu denetimde uygulanan kural: bolumler veri-setine ozgu kabul edildi. Arsivde tum decided kume hesaplandi (PRIOR uygulamasi ile ayni); 32 C1-takvim satiri haric duyarlilik ayrica raporlandi. Universe CSV'de yalniz `scan_date <= 2025-12-31` kilitsiz kabul edildi (C1/C5/C6 birlesimi; C6 siniri bilinmedigi icin 2026-01-01'den itibaren kilitli varsayildi).
- Next step: insan karari - bolum kapsamini (veri-seti mi, takvim mi) acik bir manifestte kaydetmek; C6 sinir tarihlerini kayda gecirmek.
- Suggested category: FIX_CANDIDATE (governance kaydi; insan onayi gerekir)

### F-PRF-01 - `resolved_pct_barrier` brut bariyer getirisi olarak mekanik olarak tutarli; `resolved_pct` ayni degerin kopyasi

- Priority: P1
- file:function:lines: veri alanlari (`signals_archive`); payload `entry_price`, `take_profit`, `stop_loss`. Cozumleyici kodu bu rolde okunmadi.
- Data source: `data/finpilot.db` (SHA-256 yukarida).
- Method: `PRF_01_profile.py` - alan dagilimlari, durum capraz tablosu, TP/SL ile ima edilen getiri kontrolu (tolerans 0.05 pp).
- Result: `resolved_pct_barrier` n = 5,216 (5,206 decided + 10 expired); min -14.6262, p1 -5.0128, medyan -0.6424, p99 +13.1244, max +49.293, ortalama +0.4014; abs > 50: 0 satir. Birim yuzde (abs < 1 payi %38.17; `resolved_win` medyani +3.2044, `resolved_loss` medyani -0.9666). 5,206 decided satirin %100.0'unde deger = `take_profit/entry_price - 1` (win) veya `stop_loss/entry_price - 1` (loss), 0.05 pp icinde. Payload TP medyani +2.805 %, SL medyani -1.0581 % (tum satirlar). `resolved_pct` decided satirlarda `resolved_pct_barrier` ile ayni (Pearson 1.0; abs fark < 0.01 orani 1.0; n = 5,206).
- n: 5,206
- Label: REPRODUCED (PRIOR `outlier_dependence_baseline.md` §1: 5,206 satir, %100 TP/SL esitligi)
- Limitations: Saklanan etiketin piyasa fiyatlariyla uyumu bu rolde test edilmedi; PRIOR replay %88.9 eslesme buldu (575 satir uyusmuyor).
- Alternative explanations: esitlik etiket mekaniginin tutarliligini gosterir, fiyat dogrulugunu ya da gerceklesebilir dolumu gostermez.
- Next step: cozumleyicinin bar kurali ve fiyat vintage'i icin kod izleme (bu rolun kapsami disinda).
- Suggested category: KEEP_AS_IS

### F-PRF-02 - `resolved_pct_t5` imkansiz/aykiri degerler iceriyor; performans alani olarak kullanilamaz

- Priority: P0 (validity) - herhangi bir T+5 iddiasi bu alana dayaniyorsa
- file:function:lines: veri alani; hesaplayan kod bu rolde izlenmedi.
- Data source / Method: `data/finpilot.db`; `PRF_01_profile.py`.
- Result: n = 5,213; ortalama +13.6609, medyan -1.2797, min -96.2144, p1 -80.1546, p99 +54.4131, max +11,990.9096; abs > 50: 166 satir; abs > 100: 35 satir. Bariyer getirisi ile Pearson 0.2916 (n = 5,204). `resolved_win` satirlarinda araligi -21.2264..+11,990.9096; `resolved_loss` satirlarinda max +76.5835.
- n: 5,213
- Label: MEASURED (saklanan degerler)
- Limitations: nedeni (split/kurumsal islem, fiyat hatasi, birim) izlenmedi.
- Alternative explanations: ters split veya fiyat vintage farki; dusuk fiyatli hisselerde bir kismi gercek asiri hareket olabilir.
- Next step: T+5 alaninin kod ve fiyat kaynagi izlenmeli; kurumsal islem korumasi.
- Suggested category: FIX_CANDIDATE

### F-PRF-03 - `ts` sinyal tarihi degil, arsive ekleme zamani; satirlarin %31.65'inde `signal_date` farkli (cogunlukla 5-18 gun once)

- Priority: P0 (validity) - gun-duzeyi analizler (kumeleme, gun yogunlasmasi, hafta-gunu)
- file:function:lines: veri alanlari (`ts`, payload `signal_date`, `added_at`, `source_model`).
- Data source / Method: `data/finpilot.db`; `PRF_01_profile.py` - payload tarih alanlari ile `ts` tarihinin karsilastirmasi, hafta-gunu dagilimlari.
- Result: payload `signal_date` kapsami %100; `ts` tarihine esit %68.35 (3,929 / 5,748). Fark (`signal_date` - `ts` tarihi, gun; en sik 8): 0: 3,929; -12: 496; -17: 300; -14: 228; -5: 228; -18: 191; +1: 179; -7: 90. Payload `added_at` (kapsam %99.5) `ts` ile ayni tarih (%100) -> `ts` = arsive ekleme zamani. `ts` tarihi hafta-gunu: Pazar 2,129, Sali 1,129, Pazartesi 831, Carsamba 660, Persembe 427, Cuma 375, Cumartesi 197. `signal_date` hafta-gunu: Sali 1,939, Carsamba 841, Pazar 808, Pazartesi 781, Persembe 740, Cuma 412, Cumartesi 227. `ts` bicimi karisik: 2,658 satirda saat dilimi eki var, digerleri naive; 559 satirda `T` ayraci yok. `source_model`: scanner_v1 2,531; scanner_import 2,065; scanner_v2 564; scanner_shortlist 559 (decided disi satirlar dahil).
- Secim: gun-duzeyi analizlerde `signal_date` kullanildi (acik adli alan, %100 kapsam; `ts` toplu ice aktarimlarda sinyal gununu temsil etmiyor). `signal_date`'te de 1,035 hafta sonu satiri var; bu nedenle "sonraki ilk is gunu" oturum kumesi duyarlilik olarak eklendi.
- PRIOR'a etkisi: PRIOR (`outlier_dependence_baseline.md` §3, `top_1pct_top_5pct_sensitivity.md` §4, §6) gun yogunlasmasini, hafta-gunu dagilimini ve 37 kumeyi `ts` tarihine gore raporladi (Pazar %40.4; 2026-03-01 ve 2026-03-03 = 2,421 satir). Bu yogunlasmanin bir kismi ice aktarim tarihinden kaynaklaniyor olabilir; decided kume uzerindeki etkisi asagidaki bulgularda olculdu.
- n: 5,748 (tum satirlar, metadata)
- Label: MEASURED (alan karsilastirmasi); "`ts` = ekleme zamani" cikarimi SUPPORTED (`added_at` esitligi)
- Limitations: `signal_date`'in kendisinin ne zaman yazildigi bilinmiyor; naive `ts` degerlerinin saat dilimi bilinmiyor; oturum eslemesinde ABD tatilleri yok.
- Alternative explanations: farki 0 olan %68'lik kisimda `ts` tarama zamani olabilir; +1 gunluk farklar saat dilimi kaymasi olabilir.
- Next step: arsiv yazma yolunda sinyal tarihi ile ekleme zamaninin ayri kolonlarda tutulmasi ve geriye donuk ice aktarilan satirlarin isaretlenmesi.
- Suggested category: FIX_CANDIDATE

### F-PRF-04 - Baseline yeniden uretildi; dagilim cok carpik, ortalama sag kuyruga bagli

- Priority: P1
- file:function:lines: veri alani `resolved_pct_barrier`; hesap `scripts/PRF_02_analysis.py:summ,main`.
- Data source: `data/finpilot.db` (SHA-256 `b64c0c52...f5f6`).
- Method: decided kume (5,206), r = `resolved_pct_barrier`; ust kuyruk = r'ye gore azalan stabil siralamada ilk floor(p x n) satir.
- Result:

| Metrik | Deger |
|---|---|
| n | 5,206 (1,017 sembol; 48 `signal_date` 2025-09-12..2026-05-22; 37 `ts` tarihi; 46 giris oturumu) |
| Ortalama / medyan | +0.3984 % / -0.6431 % |
| Toplam | +2,074.19 pp |
| Std / skew / asiri basiklik | 3.593 / 3.8666 / 31.7473 |
| Kazanma orani (r > 0 = `resolved_win`) | %30.06 |
| Ortalama kazanc / kayip | +4.2825 % / -1.2711 % |
| Brut profit factor | 1.4482 |

| Ornek | n | Ortalama | Medyan | PF | Ortalama %95 CI (signal_date kume) |
|---|---|---|---|---|---|
| Tam | 5,206 | +0.3984 | -0.6431 | 1.4482 | [+0.1110, +0.6524] (B=5000) |
| Ust %1 haric (52) | 5,154 | +0.1896 | -0.6511 | 1.2112 | [-0.0353, +0.4176] (B=2000) |
| Ust %5 haric (260) | 4,946 | -0.1615 | -0.6799 | 0.8274 | [-0.3668, +0.0399] (B=2000) |

| Kuyruk | k | Kesim degeri | Net toplam payi |
|---|---|---|---|
| Ust %1 | 52 | +13.2075 | %52.88 |
| Ust %5 | 260 | +6.3477 | %138.51 |
| Ust %10 | 520 | +4.4199 | %204.73 |
| Alt %1 | 52 | -5.0193 | -%17.10 |
| Alt %5 | 260 | -2.7444 | -%52.06 |
| Alt %10 | 520 | -2.1068 | -%81.93 |

- n: 5,206
- Label: REPRODUCED (PRIOR `outlier_dependence_baseline.md` bolum 2 ve `top_1pct_top_5pct_sensitivity.md` bolum 2-3: ortalama, medyan, kazanma orani, ortalama kazanc/kayip, PF, ust %1/%5 haric ortalamalar ve kuyruk paylari ayni). Skew, basiklik, %10 kuyruklar, alt kuyruklar ve signal_date kume CI'lari MEASURED (yeni).
- Limitations: brut simule bariyer etiketleri; ideal dolum; ortusen sinyaller (F-PRF-09).
- Alternative explanations: sag kuyruk dusuk fiyatli isimlerde yogun (F-PRF-08; PRIOR likidite raporu).
- Next step: on-kayitli degerlendirmede medyan ve kuyruk-haric ortalama birincil metriklerle birlikte raporlanmali.
- Suggested category: RESEARCH_NEXT

### F-PRF-05 - Gun-kumelenmis belirsizlik: ortalama CI'si sifiri dislar, medyan CI'si tamamen negatif; en olumlu 10 gun cikarilinca ortalama negatif

- Priority: P1
- file:function:lines: `scripts/PRF_02_analysis.py:cluster_boot,loo_days`.
- Method: kume bootstrap (kumeler yerine koyarak yeniden orneklenir; yuzdelik CI); seed 20261019; B = 5000 (tam ornek), 2000 (alt ornekler). Kume tanimlari: `signal_date` (birincil), sonraki is gunu oturumu, `ts` tarihi (PRIOR uyumu). Leave-one-day-out ve "en olumlu k gunu cikar" (gunler sonuca gore secildi; post-hoc kirilganlik tanisi, test degil).
- Result:

| Kume | Kume sayisi | Ortalama %95 CI | Medyan %95 CI | Bootstrap ortalama <= 0 payi |
|---|---|---|---|---|
| signal_date | 48 | [+0.1110, +0.6524] | [-0.7782, -0.5438] | %0.32 |
| sonraki oturum | 46 | [+0.1181, +0.6546] | [-0.8003, -0.5388] | %0.16 |
| ts tarihi | 37 | [+0.0692, +0.5614] | [-0.7937, -0.5087] | %0.52 |
| ts tarihi, B=2000, seed 20261014 (PRIOR tekrari) | 37 | [+0.0629, +0.5606] | - | %0.45 |

  iid SE 0.0498; signal_date kume bootstrap SE 0.139 -> tasarim etkisi 7.79 (oturum 7.72). Leave-one-signal_date-out ortalama araligi: +0.3228 (2026-02-12 cikarilinca, 298 satir) .. +0.4549 (2026-03-01, 332 satir); tek bir gun isareti degistirmiyor. En olumlu k signal_date cikarilinca ortalama: k=1 +0.3228, k=2 +0.2472, k=3 +0.1595, k=5 +0.0747, k=10 -0.0349 (n=3,326); medyan tum k icin -0.59..-0.64. `ts` kumelerinde 2026-03-01 (1,948 satir) cikarilinca +0.2611; k=10 -0.0239. Gun basina satir: min 6, medyan 50, max 487; en buyuk iki signal_date satirlarin %18.44'u (`ts` tarihinde %46.5).
- n: 5,206; 48 kume
- Label: MEASURED; PRIOR CI [+0.064, +0.565] yaklasik REPRODUCED ([+0.0629, +0.5606]; fark muhtemelen RNG uygulamasindan).
- Limitations: 48 kume az; ayni sembol farkli gunlerde tekrar ediyor (F-PRF-09) -> kumeler arasi bagimsizlik zayif, CI'lar muhtemelen dar. Az kumede percentile bootstrap kapsami garanti etmez.
- Alternative explanations: pozitif ortalama birkac buyuk olumlu gune (2026-02-12, 2026-03-03, 2026-02-17) ve geri doldurulmus satirlara (F-PRF-07) bagli.
- Next step: on-kayitli protokolde kume tanimi ve minimum kume sayisi sabitlenmeli (PRIOR remediation bolum 5 onerisi ile uyumlu).
- Suggested category: NEEDS_MORE_DATA

### F-PRF-06 - Maliyet duyarliligi (cost-sensitivity, net degil): ortalama 0.3984 pp duz maliyette sifirlanir; CI alt siniri ~0.11 pp'de sifira iner

- Priority: P1
- file:function:lines: `scripts/PRF_02_analysis.py:main` (cost_sensitivity).
- Method: her sinyalden sabit gidis-donus maliyeti c dusuldu; CI = signal_date kume CI'si - c (sabit kaydirma). Gercek spread, dolum, kayma ve komisyon bilinmiyor; senaryolar maliyet modeli degildir.
- Result:

| c (pp) | Ortalama - c | Medyan - c | Ortalama %95 CI - c | PF (c sonrasi) | r > c payi |
|---|---|---|---|---|---|
| 0.00 | +0.3984 | -0.6431 | [+0.1110, +0.6524] | 1.4482 | %30.06 |
| 0.10 | +0.2984 | -0.7431 | [+0.0110, +0.5524] | 1.3112 | %30.06 |
| 0.25 | +0.1484 | -0.8931 | [-0.1390, +0.4024] | 1.1395 | %30.04 |
| 0.55 | -0.1516 | -1.1932 | [-0.4390, +0.1024] | 0.8811 | %29.41 |
| 1.00 | -0.6016 | -1.6431 | [-0.8890, -0.3476] | 0.6227 | %28.20 |

  Basabas duz maliyet (ortalama icin) = 0.3984 pp. Es zamanli alt kumede (F-PRF-07) ortalama 0.25 pp'de negatif (-0.0529).
- n: 5,206
- Label: MEASURED (senaryo aritmetigi); 0.55 ve 1.00 pp satirlari PRIOR `liquidity_and_cost_sensitivity.md` bolum 5 ile ayni (REPRODUCED).
- Limitations: maliyet boyut, spread ve fiyattan bagimsiz varsayildi; PRIOR likidite raporuna gore kuyruk isimlerinin cogu dusuk ADV'li -> duz maliyet kuyruk icin gercek maliyeti muhtemelen dusuk gosterir.
- Alternative explanations: yok (aritmetik).
- Next step: kaynakli maliyet bilesenleri ve ileriye donuk spread/dolum logu (PRIOR remediation bolum 5).
- Suggested category: NEEDS_MORE_DATA

### F-PRF-07 - Pozitif ortalamanin %65.9'u arsive 5-145 gun gecikmeyle yazilan satirlardan geliyor (geri doldurma riski)

- Priority: P0 (validity)
- file:function:lines: veri alanlari `ts`, payload `signal_date`, `source_model`; `scripts/PRF_02_analysis.py:main` (lag_days, lag_subsets).
- Method: lag = `ts` tarihi - `signal_date` (gun). Kovalar: -1..1 (es zamanli) ve >= 5; decided kumede 2..4 gunluk lag yok.
- Result: decided kumede lag dagilimi: -1: 176; 0: 3,414; 5: 225; 7: 90; 12: 487; 14: 224; 17: 298; 18: 186; 128: 12; 135: 6; 136: 12; 144: 40; 145: 36. lag >= 5 olan 1,616 satirin tamami `scanner_v1` (11 signal_date). Es zamanli 3,590 satir: scanner_import 2,065, scanner_v1 879, scanner_shortlist 554, scanner_v2 92.

| Alt kume | n | Gun | Ortalama | Ortalama %95 CI (B=2000) | Medyan | Kazanma | PF | Net toplam payi |
|---|---|---|---|---|---|---|---|---|
| lag -1..1 | 3,590 | 37 | +0.1971 | [-0.0551, +0.4610] | -0.6052 | %26.13 | 1.2406 | %34.1 (707.56 pp) |
| lag >= 5 | 1,616 | 11 | +0.8457 | [+0.3281, +1.2470] | -0.8725 | %38.80 | 1.8102 | %65.9 (1,366.64 pp) |

  Es zamanli alt kumede duz maliyet sonrasi ortalama: 0.10 -> +0.0971; 0.25 -> -0.0529; 0.55 -> -0.3529; 1.00 -> -0.8029. PRIOR'in iki `ts` tarihi (2026-03-01, 2026-03-03; 2,421 satir) 13 farkli signal_date iceriyor (2025-10-07..2026-03-03); 805'i lag 0, kalani lag 5-145. Aylik (signal_date): 2026-02 1,510 satir, ortalama +0.8827; PRIOR'in `ts` ayina gore "2026-03" (2,495 satir, +0.657; bu rolde ayni deger yeniden uretildi) olarak raporladigi kume buyuk olcude Subat 2026 sinyalleri.
- n: 5,206
- Label: MEASURED (lag ve alt kume istatistikleri); "satirlar sonuc bilindikten sonra secilerek yazildi" yorumu HYPOTHESIS.
- Limitations: payload, ekleme aninda sonucun bilinip bilinmedigini kaydetmiyor; lag >= 5 kumesi yalniz 11 gun ve tek kaynak modeli.
- Alternative explanations: farkli donem/rejim (Subat 2026), farkli model surumu (`scanner_v1`), toplu ice aktarimin sinyalleri secimsiz kopyalamis olmasi (o durumda yanlilik yok).
- Next step: ice aktarim kaynagini ve filtresini kod/veri uzerinden izlemek; geriye donuk yazilan satirlari isaretlemek; ekonomik iddialarda es zamanli satirlari ayri raporlamak (oneri, karar degil).
- Suggested category: FIX_CANDIDATE

### F-PRF-08 - Alt kirilimlar (betimsel): pozitif ortalama 5 USD alti satirlarda ve `scanner_v1` / Subat 2026 kumesinde yogun; >= 5 USD satirlarda CI sifiri iceriyor

- Priority: P2 (model kalitesi); ekonomik yorum icin P1
- file:function:lines: `scripts/PRF_02_analysis.py:split_table`; sektor icin `data/backtest_out/sector_map_full.csv` (statik harita; SHA-256 Ek'te).
- Method: her grup icin n, gun, ortalama, medyan, kazanma, PF, signal_date kume CI (B=2000, seed 20261019); n < 30 gruplar ozetlenmedi. 8 boyut, ~50 grup; coklu karsilastirma duzeltmesi yok -> yalniz betimsel.
- Result (secili gruplar):

| Boyut / grup | n | Gun | Ortalama | Medyan | Kazanma | PF | Ortalama %95 CI |
|---|---|---|---|---|---|---|---|
| giris fiyati < 1 USD | 52 | 6 | +9.0006 | +7.7481 | %63.46 | 6.458 | [+4.5665, +9.7964] |
| giris fiyati 1-5 USD | 292 | 18 | +2.3695 | -1.6393 | %45.55 | 2.3255 | [+1.5804, +2.8904] |
| giris fiyati >= 5 USD | 4,862 | 48 | +0.1880 | -0.6419 | %28.77 | 1.2274 | [-0.0466, +0.4386] |
| `source_model` scanner_import | 2,065 | 19 | +0.0606 | -0.5022 | %25.62 | 1.112 | [-0.0627, +0.1783] |
| `source_model` scanner_v1 | 2,495 | 14 | +0.6565 | -1.0314 | %32.34 | 1.5546 | [+0.1285, +1.0452] |
| `source_model` scanner_shortlist | 554 | 12 | +0.4698 | -0.7698 | %35.74 | 1.576 | [-0.0409, +0.9871] |
| `source_model` scanner_v2 | 92 | 3 | +0.5517 | -0.6079 | %33.70 | 1.4794 | [-1.9979, +1.8130] |
| `signal` alan degeri `WATCH` | 2,776 | 25 | +0.6867 | -0.9835 | %34.19 | 1.6049 | [+0.2389, +1.0090] |
| `signal` alan degeri `TRUE` | 1,326 | 19 | +0.0619 | -0.4937 | %26.17 | 1.1086 | [-0.1051, +0.2163] |
| `signal` alan degeri `FALSE` | 739 | 18 | +0.0581 | -0.5183 | %24.63 | 1.1193 | [-0.0589, +0.1746] |
| `signal` alan degeri `BUY` (saklanan etiket) | 365 | 26 | +0.1171 | -0.8409 | %23.84 | 1.1188 | [-0.4580, +0.9025] |
| ay 2025-09 | 1,579 | 12 | +0.0424 | -0.5183 | %24.95 | 1.077 | [-0.1164, +0.2006] |
| ay 2025-10 | 580 | 10 | +0.1556 | -0.4199 | %33.79 | 1.3391 | [+0.0868, +0.2584] |
| ay 2026-02 | 1,510 | 6 | +0.8827 | -1.0068 | %37.22 | 1.8017 | [+0.3476, +1.2944] |
| ay 2026-03 | 879 | 3 | +0.3088 | -1.1856 | %20.48 | 1.2143 | [-0.9949, +1.0319] |
| ay 2026-04 | 177 | 4 | +0.3841 | -0.7207 | %35.59 | 1.5681 | [-0.4599, +1.4074] |
| ay 2026-05 | 469 | 11 | +0.5182 | -0.7624 | %35.39 | 1.5548 | [-0.0429, +1.0437] |
| `regime` `True` | 2,807 | 43 | +0.1694 | -0.6092 | %29.14 | 1.2228 | [-0.0216, +0.3961] |
| `regime` `False` | 1,755 | 41 | +0.6499 | -0.6046 | %33.33 | 1.7648 | [+0.1358, +1.1187] |

  Fiyat bandi katkisi (n x ortalama, yuvarlanmis degerlerden turetildi): < 1 USD ~468.0 pp, 1-5 USD ~691.9 pp, >= 5 USD ~914.1 pp -> 5 USD alti 344 satir (%6.6) net toplamin ~%55.9'u. `regime` alani karisik kodlu (`True` 2,807, `False` 1,755, `0` 347, `1` 205, `Trend` 55, `Range` 37; kaynak modele gore farkli sozluk) -> tek bir rejim degiskeni olarak yorumlanamaz. Sektor (statik ETF haritasi): XLI 1,860 satir +0.5672 [+0.1758, +0.9933]; XLC 1,157 +0.4640 [+0.1996, +0.7201]; XLV 740 +0.1912 [-0.1437, +0.5314]; XLF 700 -0.0043 [-0.2906, +0.3598]; XLRE 134 -0.3394 [-0.6691, -0.0656]; diger gruplar <= 230 satir. 2025-11 ve 2025-12 aylari 6'sar satir (ozetlenmedi).
- n: 5,206
- Label: MEASURED (betimsel); gruplar arasi farklarin kalici oldugu iddiasi icin destek yok (coklu karsilastirma, az gun).
- Limitations: ay, kaynak modeli ve lag kovasi birbirine karisik (confounded); sektor haritasi zaman-noktasi degil; bir grupta 3-6 gun olan CI'lar guvenilmez.
- Alternative explanations: fiyat bandi etkisi likidite/spread maliyetiyle birlikte gider (PRIOR: ust %1'in medyan 20 seans dolar ADV'si 0.30 M USD); ay etkisi donem etkisi olabilir.
- Next step: `regime` alaninin tek sozluge normalize edilmesi (veri kalitesi); fiyat bandina gore maliyetli duyarlilik on-kayitli yapilmali.
- Suggested category: RESEARCH_NEXT

### F-PRF-09 - Bagimsizlik zayif; brut portfoy gorunumu kucuk ve varsayima bagli

- Priority: P1
- file:function:lines: `scripts/PRF_02_analysis.py:portfolio,main`; cikti `data/PRF_daily_cohorts.csv`.
- Method: (a) tekrar/ortusme sayimlari; (b) sembol yogunlasmasi; (c) signal_date kohortlari: her gun esit agirlikli ortalama r, tarih sirasiyla; toplamsal kumulatif (pp) ve f payi ile bilesik seri (f = 1.0, 0.2, 0.1). Varsayim: kohortlar ardisik ve ortusmesiz; maliyet yok.
- Result: ayni (symbol, signal_date) tekrari 585 satir; ayni sembolun onceki 7 takvim gunu icinde de sinyali olan satir 3,651 (%70.13). Ilk 10 sembol satirlarin %7.55'i, net toplamin %32.23'u (PRIOR ile ayni); sembol HHI 0.0027. Kohort serisi: 48 gun; satir/gun min 6, medyan 50, max 487; en buyuk 5 gun satirlarin %34.86'si. Kohort ortalamalarinin ortalamasi +0.2742 (medyan +0.2478; sinyal agirlikli +0.3984'ten dusuk); pozitif kohort payi %64.58; en kotu kohort 2026-05-18 -1.9979 (11 sinyal), en iyi 2026-04-16 +1.9413 (50 sinyal). Toplamsal kumulatif +13.16 pp, maksimum dusus 2.70 pp. Bilesik: f=1.0 son carpan 1.1389, MDD %2.70; f=0.2 1.0266, MDD %0.54; f=0.1 1.0132, MDD %0.27.
- n: 5,206 sinyal; 48 kohort
- Label: MEASURED (brut, varsayima bagli); eszamanli acik pozisyon sayisi NOT_MEASURABLE (arsivde cikis tarihi yok).
- Limitations: tutma suresi yok; kohortlar zaman icinde ortusur; kohort ici korelasyon ve 2025-12 -> 2026-02 boslugu modelde yok; 48 noktalik seriden MDD istikrarsiz; bu degerler gerceklesmis getiri, risk limiti veya pozisyon boyutu onerisi degildir.
- Alternative explanations: dusuk MDD, gun-ici esit agirligin kuyruklari yumusatmasindan ve az kohorttan kaynaklanabilir.
- Next step: cozumleyicinin cikis tarihini/bar indeksini arsive yazmasi (eszamanlilik ve portfoy simulasyonu icin on kosul).
- Suggested category: NEEDS_MORE_DATA

### F-PRF-10 - Secilen-evren karsilastirmasi kilitsiz yerel veride NOT_MEASURABLE

- Priority: P1
- file:function:lines: `scripts/PRF_03_universe.py:main,compare`; kilit tanimlari F-PRF-00.
- Data source: `data/backtest_out/full_universe_enriched_labeled.csv` (SHA-256 `1C59DE39BDFFF56CED9436B4DE6555E4E8457FDB761669E41673F8BEF7730000`, 32,219,143 bayt); arsiv `data/finpilot.db`.
- Method: once yalniz metadata (tarih, satir, `label_entry_basis`); sonuc kolonu `c2c_5d` yalniz `scan_date <= 2025-12-31` satirlari icin parca parca filtrelenerek tutuldu. Getiri tanimi iki grupta da CSV `c2c_5d` (bariyer degil). Gunluk karsilastirma icin gun basina >= 20 secilmemis evren satiri sarti.
- Result: CSV 100,496 satir, 2025-09-11..2026-08-05; ay dagilimi 2025-09 7,902; 2025-10 492; 2025-11 6; 2025-12 6; 2026-03 1; 2026-04 1,716; 2026-05 20,290; 2026-06 23,826; 2026-07 46,056; 2026-08 201. `label_entry_basis`: eod_close 79,935, intraday 20,561. Kilitsiz pencere: 8,406 satir, 19 tarih, 2,081 tekil sembol-gun (EOD payi %98.7; 1,351 EOD tekrar grubunda `c2c_5d` farki 0). Pencerede arsiv decided satiri 2,171 (24 signal_date; 2,094 tekil sembol-gun); CSV'de bulunan 1,259 (EOD 1,253). Gun basina >= 20 secilmemis EOD evren satiri olan tek gun 2025-09-15 (secilen 111, evren 319); `liquidity_ok` evreninde 0 gun. O gunde secilenlerin `c2c_5d` medyani +0.947, evren medyani +2.6068; ayni gun evren medyanina gore fazlalik medyani -1.6598 (%31.53 pozitif); tek gun oldugu icin genellenemez. `c2c_5d` kilitsiz pencerede kirli: ortalama +13.5967, medyan +0.5421, max +14,368.35, abs > 100: 26 satir. Eslesen 1,253 secili EOD satirinda bariyer ortalamasi +0.0509, `c2c_5d` ortalamasi +1.3764.
- n: 1 gun (karsilastirma); 2,171 secili satir (metadata)
- Label: NOT_MEASURABLE
- Limitations: CSV'de bariyer getirisi yok; kilitsiz pencerede evren genisligi yok (bu donemde CSV buyuk olcude taranan kisa listeyi iceriyor); 2026 tarihleri C1/C5/C6 nedeniyle kapsam disi tutuldu.
- Eksik olanlar: (1) kilitsiz ve bildirilmis bir pencere; (2) ayni tarihlerde genis ve uygunluk filtresi kayitli evren anlik goruntusu; (3) secilmemis isimler icin ayni TP/SL kurali ve fiyat replay'i ile bariyer etiketi; (4) kurumsal islem duzeltmeli temiz T+5 getirisi; (5) secim anindaki uygunluk bayraklari.
- Alternative explanations: -
- Next step: ileriye donuk pencerede (PRIOR remediation secenek C) gunluk uygun evren anlik goruntusu ve ayni bariyer kuraliyla etiketleme.
- Suggested category: NOT_MEASURABLE

### F-PRF-11 - WP-9: istatistiksel guvenilirlik ve OOS durumu (PRIOR ozeti + yeni eklenenler)

- Priority: P1
- Data source: PRIOR dokumanlar (yeniden hesaplanmadi): `docs/governance/decision-log.md` L89-93 (OOS bagimsizlik denetimi, 2026-10-14), L110-121 (OOS kullanim denetimi), L53-60 (2026-10-16 insan kararlari, D7 dahil; D7 icerigi brief'ten alindi); `reports/oos_status_c_remediation_v1_2026-10-15/oos_status_c_remediation_plan.md`; `reports/outlier_dependence_audit_v1_2026-10-14/` (3 dosya); fixed-target raporlari. `reports/oos_independence_audit_v1_2026-10-14/` ve `reports/net_expectancy_audit_v1_2026-10-14/` dosyalari bu rolde acilmadi; icerikleri decision-log ve yukaridaki PRIOR raporlarin atiflari uzerinden ozetlendi.
- PRIOR ozeti: (1) Hicbir trading-strategy OOS setinin sonuclari hesaplanmadan once dogrulanabilir dondurulmasi yok; 2026-05-21 siniri ve locked-OOS sonuclari ilk kez birlikte `common_buy_accuracy.json` icinde (2026-07-15T16:52:02Z; locked_oos n = 44). (2) En az alti OOS siniri var; 2026-01-01 sonrasi her pencere en az bir artefaktta degerlendirilmis; temiz tarihsel holdout yok. (3) Remediation: mevcut setler bagimsiz test desteklemez; oneri C (yeni ileriye donuk pencere); onerilen kapi NOT APPROVED; F14 3,120 konfigurasyon / 1,012 FDR kesfi; F20 5,748 satir 4,318 sembol-gunde. (4) Q3/Q5 (outlier raporlari uzerinden): maliyet konvansiyonlari 0-100 bps arasi celisik; `core/paper_portfolio.py` basligi 10 bps, kodu 20 bps; `_COST_FLAT_PCT` 0.0020 (`scanner/evaluate.py`); gerceklesmis islem yok (`alpaca_orders` 11 satir, 0 fill); replay eslesmesi %88.9.
- Coklu test baglami (PRIOR fixed-target):

| Kosu | Tarih araligi | Konfigurasyon | FDR kesfi | PBO (yol) | White RC p | Hansen SPA p | Gross + stabil | Locked holdout |
|---|---|---|---|---|---|---|---|---|
| 2026-08-04 | 2025-09-11..2026-06-30 | 3,120 | 994 | 0.5 (6) | 0.2786 | 0.3582 | 0 | not_opened |
| 2026-08-05 | 2025-09-11..2026-06-30 | 3,120 | 994 | 0.4 (15) | 0.2837 | 0.2927 | 0 | not_opened |
| 2026-08-11 | 2025-09-11..2026-07-09 | 3,120 | 1,012 | 0.6 (10) | 0.7413 | 0.7761 | 130 | not_opened |

  Okuma: WRC/SPA p-degerleri en iyi konfigurasyonun ustunlugunu desteklemiyor; PBO 0.4-0.6 asiri uyum riskini yuksek gosteriyor; 2026-08-11'deki 130 "gross + stabil" konfigurasyon 3,120 denemenin icinden secildi.
- Bu rolde yeni: (a) arsiv kumeleri `signal_date` ile yeniden tanimlandi (37 yerine 48); (b) tasarim etkisi 7.79 -> iid standart hata ~2.8 kat dar; (c) gecikmeli yazilan satirlar ve es zamanli alt kume (F-PRF-07); (d) kilit kapsami belirsizligi (F-PRF-00); (e) evren karsilastirmasinin yapilamazligi (F-PRF-10). Arsivdeki tum pencereler daha once incelendigi icin bu rolun hicbir sonucu bagimsiz dogrulama degildir.
- Label: SUPPORTED (PRIOR kaynaklar okundu, yeniden hesaplanmadi); yeni maddeler MEASURED.
- Limitations: PRIOR sayilar bu rolde yeniden dogrulanmadi (fixed-target, common_buy, Q3).
- Next step: PRIOR remediation secenek C icin insan kararlari (T0, uretim commit'i, maliyet tabani, minimum kume sayisi).
- Suggested category: NEEDS_MORE_DATA

### Ne gercekten biliyoruz (brief 13.4)

| Iddia (kaynak) | n | Tarihler | Evren | Sinyal / cikis | Maliyet | Benchmark | Bagimsizlik | Belirsizlik | Genelleme siniri | Etiket |
|---|---|---|---|---|---|---|---|---|---|---|
| Arsiv brut bariyer ortalamasi pozitif, +0.3984 %/sinyal (F-PRF-04) | 5,206 | signal_date 2025-09-12..2026-05-22 (48 gun; 2026-01 yok, 2025-11/12 6'sar satir) | scanner arsivi, 1,017 sembol, 4 kaynak modeli | payload TP (medyan +2.8 %) / SL (medyan -1.06 %) bariyeri; cozumleyici kurali dogrulanmadi (PRIOR replay %88.9) | yok (brut) | yok | dusuk: %70.1 ayni sembol 7 gun icinde; tasarim etkisi 7.8; %31.0 gecikmeli yazilmis | ortalama CI [+0.111, +0.652]; medyan CI [-0.778, -0.544] | tarihsel, OOS degil (D7); ust %5 haric ve en olumlu 10 gun haric negatif | REPRODUCED (yalniz brut) |
| Es zamanli yazilan sinyallerde pozitif ortalama (F-PRF-07) | 3,590 | 37 gun | ayni | ayni | yok | yok | ayni | ortalama CI [-0.055, +0.461] | 0.25 pp maliyette negatif | MEASURED; pozitiflik desteklenmiyor |
| Maliyet sonrasi pozitif sonuc (F-PRF-06) | 5,206 | ayni | ayni | ayni | duz 0.10-1.00 pp senaryo; gercek maliyet bilinmiyor | yok | ayni | 0.25 pp'de CI sifiri icerir | spread, dolum, etki yok | NOT_MEASURABLE (net); yalniz cost-sensitivity |
| Secim ayni gun evreninden iyi (F-PRF-10) | 1 gun (111 vs 319) | 2025-09-15 | CSV kisa liste | `c2c_5d` (bariyer degil) | yok | ayni gun evren | - | yok | tek gun | NOT_MEASURABLE |
| Brut portfoy dususu kucuk (F-PRF-09) | 48 kohort | ayni | ayni | ayni | yok | yok | kohortlar ortusur | yok | cikis tarihi yok | MEASURED (varsayima bagli); portfoy iddiasi NOT_MEASURABLE |
| Fixed-target konfigurasyonlari (PRIOR 2026-08-11: 130 gross + stabil) | konfigurasyon basina n okunmadi | 2025-09-11..2026-07-09 | `full_universe_enriched.csv` | 3,120 TP / ATR-stop / ufuk kombinasyonu | PRIOR beyan edilen senaryolar | WRC / SPA | ortusen satirlar (PRIOR F20) | WRC p 0.7413, SPA p 0.7761, PBO 0.6 | locked holdout acilmadi; coklu test | UNRESOLVED (coklu test sonrasi destek yok) |
| 2026-05-21 locked-OOS bagimsiz dogrulama (PRIOR) | locked_oos n = 44 | > 2026-05-21 | arastirma CSV'leri | `common_buy_accuracy` tanimi (hedef `resolved_pct_t5` >= 5 %) | - | - | 2026-07-15'te degerlendirildi, sonra yeniden kullanildi | - | D7: mevcut veri OOS sayilmaz | CONTRADICTED (bagimsizlik iddiasi) |

<!-- PRF-FINDINGS-ANCHOR -->

## Dogru calisan kisimlar

- Bariyer etiket mekanigi tutarli: 5,206 decided satirin %100'unde `resolved_pct_barrier` payload TP/SL seviyesine esit (F-PRF-01).
- Payload butunlugu: `entry_price`, `take_profit`, `stop_loss`, `signal_date` %100 kapsam; JSON parse hatasi 0; `id` 5,748/5,748 tekil.
- DB okumasi tutarli anlik goruntu: okuma oncesi/sonrasi SHA-256 ayni.
- PRIOR sayilari birebir yeniden uretildi: baseline, ust %1/%5 haric ortalamalar, kuyruk paylari, ilk 10 sembol paylari, `ts` ayina gore aylik tablo; PRIOR kume CI'si yaklasik.
- 32 C1-takvim satiri (herhangi bir aday tarih > 2026-05-21) cikarilinca sonuc degismiyor: n 5,174, ortalama +0.3897, medyan -0.644, PF 1.4382, CI [+0.1041, +0.6513] (47 kume, B=2000).
- CSV EOD tekrarlarinda `c2c_5d` tutarli (1,351 grup, fark 0); `label_entry_basis` saglanmis (79,935 eod_close / 20,561 intraday).

<!-- PRF-OK-ANCHOR -->

## Cevaplanamayan sorular

- Gecikmeli yazilan 1,616 satir sonuc bilindikten sonra mi secildi, yoksa toplu ice aktarim secimsiz mi? (ice aktarim sureci ve kaynak dosya izlenmeli)
- Cozumleyicinin bar/fiyat kurali nedir; PRIOR replay'deki 575 uyusmazligin nedeni nedir?
- Gercek gidis-donus maliyeti (spread, dolum, etki) nedir? Veri yok.
- Tutma suresi ve eszamanli pozisyon sayisi nedir? Arsivde cikis tarihi yok.
- Secilen sinyaller ayni gun uygun evreninden farkli mi (ayni bariyer tanimiyla)? Kilitsiz pencerede veri yok.
- Kilitli bolumler veri-setine mi takvime mi ozgu; C6 sinir tarihleri nedir? (insan karari)
- `resolved_pct_t5` bozulmasinin nedeni nedir?
- Hafta sonu `signal_date` degerleri tarama gunu mu, veri gunu mu?
- Arsivdeki kaynak modelleri (`scanner_v1`, `scanner_import`, `scanner_shortlist`, `scanner_v2`) uretim siralamasina esdeger mi? (PRIOR F15)

<!-- PRF-OPEN-ANCHOR -->

## Sinirlamalar

- Tum getiriler brut, simule bariyer sonuclaridir; gerceklesmis P&L, net getiri veya expectancy degildir.
- Hicbir sonuc OOS degildir (D7); arsivin tum pencereleri daha once incelendi.
- 48 kume az; yuzdelik bootstrap; ortusen sinyaller nedeniyle CI'lar muhtemelen dar.
- Kilit yorumu (F-PRF-00) bu rolun calisma secimidir, karar degildir.
- Alt kirilimlar coklu karsilastirma duzeltmesi olmadan betimseldir; "en olumlu k gun" analizi sonuca gore secilmistir (tani, test degil).
- `oos_independence_audit_v1_2026-10-14` ve `net_expectancy_audit_v1_2026-10-14` dosyalari acilmadi; ozetler ikincil PRIOR kaynaklara dayanir.
- Sektor haritasi statiktir (zaman-noktasi degil).
- DB baska bir surec tarafindan acikti; hash, 2026-10-19 ~11:03 UTC anlik goruntusudur.
- Paylasilan terminal: PRF_02/03'un ilk calistirma denemesinde terminal ciktisi baska bir rolun Python surecine ait bir KeyboardInterrupt izini gosterdi (dosya acilmadi); bu rolun komutu o denemede calismadi, ikinci deneme basarili oldu. O surecin kesilmesine bu komutun gonderiminin yol acmis olmasi dislanamaz.

<!-- PRF-LIMITS-ANCHOR -->

## Ek: komutlar

1. Provenance (PowerShell, salt-okunur): `git -C C:\Users\meric\Borsa rev-parse HEAD` (93ae83c0c6056593fde65c97358824207c97ec6d), `rev-parse --abbrev-ref HEAD`, `status --porcelain=v1 -uall` (baslangicta 120 satir), `Get-Item data\finpilot.db*`, `Get-FileHash` (DB icin kilit hatasi; CSV icin `1C59DE39BDFFF56CED9436B4DE6555E4E8457FDB761669E41673F8BEF7730000`), `git ls-files | Select-String 'holdout|sealed|lock|embargo|quarantin'`, `Get-ChildItem data -Recurse` ad taramasi, `Select-String docs\governance\decision-log.md 'D7|holdout|sealed'`.
2. PRIOR okuma: `Get-Content` ile `reports/outlier_dependence_audit_v1_2026-10-14/{outlier_dependence_baseline,top_1pct_top_5pct_sensitivity,liquidity_and_cost_sensitivity}.md`; `read_file` ile `reports/oos_status_c_remediation_v1_2026-10-15/oos_status_c_remediation_plan.md` ve `common_buy_accuracy.py` (1-120).
3. Kilit tanimlari: `Select-String` ile `common_buy_accuracy.py`, `research/protocol.py`, `scripts/run_fixed_target_research.py`, `p0_execution_replay.py` (`DISCOVERY_END|VALIDATION_END`), `reports/fixed_target_full_universe_2026-08-0{4,5}.md`, `data/backtest_out/fixed_target_full_universe_2026-08-11.md`; `Get-Content reports/fixed_target_full_universe_2026-08-05.json` (satir 35-62, dataset blogu); `Get-Content data/backtest_out/fundamentals_sentiment_holdout.json` (metadata).
4. `python -B scripts/PRF_01_profile.py` -> `data/PRF_profile.json` (ilk kosu `id` metin oldugu icin hata verdi; duzeltilip yeniden kosuldu).

5. `python -B scripts/PRF_02_analysis.py` -> `data/PRF_analysis.json`, `data/PRF_daily_cohorts.csv` (seed 20261019; B 5000 tam ornek, 2000 alt ornek; PRIOR tekrari B 2000 seed 20261014). Ilk deneme paylasilan terminalde calismadi (Sinirlamalar); ikinci deneme basarili.
6. `python -B scripts/PRF_03_universe.py` -> `data/PRF_universe_compare.json`.
7. `Get-FileHash data/backtest_out/sector_map_full.csv` -> `E16B840D0A456706DDD4EBDF471324079DC3AFDC7FB2F2BC5F56ECBA8707308A` (30,258 bayt).
8. Son kontrol: `git -C C:\Users\meric\Borsa status --porcelain=v1 -uall` -> 140 satir; bu role ait 8 yeni yol (rapor, `scripts/PRF_01..03`, `data/PRF_*` 4 dosya), hepsi denetim klasorunde; `git diff --cached --name-only` -> yalniz `web/public/demo_snapshot.json` (dokunulmadi).

<!-- PRF-CMDS-ANCHOR -->

<!-- END -->
