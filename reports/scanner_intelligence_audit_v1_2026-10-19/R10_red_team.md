# R10 - Red-Team Incelemesi (WP-13): onceki performans/gecerlilik iddialarinin bagimsiz elestirisi ve celismeli dogrulama

| Alan | Deger |
|---|---|
| Baslik | R10 Red-Team Incelemesi |
| Versiyon | v1 |
| Tarih | 2026-10-19 |
| Durum | DRAFT - Level A arastirma ciktisi; karar degildir |
| HEAD | 93ae83c (branch review/pending-2026-10-07); kirli calisma agaci ve staged web/public/demo_snapshot.json dokunulmadi |
| Rol | Independent Red-Team Reviewer (brief WP-13), PREFIX RT |
| Kapsam | Faz A: onceki arastirma, decision log ve yatirimci/pitch materyalindeki en kritik iddialarin elestirisi. Faz B: B1-B10 iddialarinin ham kod ve veriden bagimsiz yeniden turetilmesi. Tamamen salt-okunur. |
| Girdiler | data/finpilot.db (mode=ro + PRAGMA query_only=ON), scanner/, distribution/, api/routers/scan.py, core/, docs/governance/decision-log.md, docs/pitch_deck_*, data/backtest_out/fixed_target_full_universe_2026-08-11.md, git (salt-okunur) |
| Katman / seviye | Research ciktisi (reports/**), Level A; hedef dosya yalnizca bu rapor + RT_ script/veri dosyalari |
| Kanit etiketleri | MEASURED, REPRODUCED, SUPPORTED, HYPOTHESIS, UNRESOLVED, NOT_MEASURABLE, CONTRADICTED |
| OOS notu | D7 (2026-10-16) geregi hicbir sonuc out-of-sample olarak etiketlenmez. |
| Devam notu | Onceki kosu ag hatasiyla durdu. 2026-10-19 devam kosusu: A3/A4 satir atiflari guncel dosyaya gore duzeltildi, A4'teki DSR ifadesi duzeltildi, A8 basligi A7 olarak numaralandi, A5-A6 ve Faz B (B1-B11) eklendi. Sonuc istatistikleri yalniz sinyal tarihi <= 2026-05-20 icin (on-tedbir; 2026-05-21 dahil degil). Durum: tamamlandi, PARTIAL degil. |

## Ozet

Faz B: 11 iddianin 8'i VERIFIED, 3'u PARTIALLY VERIFIED (B3, B4, B5); NOT VERIFIED veya CONTRADICTED yok (tablo: Faz B > Hukum tablosu). Sonuc istatistikleri yalniz sinyal tarihi <= 2026-05-20 penceresinde (W) hesaplandi; hicbiri OOS degildir (D7).

En onemli yeni bulgu (B2 + B11): arsivdeki 1.616 gec yazilmis karar satirinin (hepsi tek partide, `ts` 2026-03-01 21:45) bariyer etiketi sinyal tarihinden degil `ts`'den baslayan pencereyle uretilmis (scripts/resolve_open_signals.py:331). Ayni onbellek kuraliyla bu satirlarin brut ortalamasi +%0,868'den (ts-bazli) +%0,403'e (sinyal-bazli) iner; W ortalamasi (+%0,395) yaklasik +%0,25'e iner (karisik, kesin olmayan tahmin). Zamaninda yazilmis satirlarda brut ortalama +%0,203, gun-kumelenmis %95 GA [-0,093; +0,499]. Tum rakamlar brut barrier etiketidir; net veya beklenti degildir.

Faz A'nin en etkili 5 elestirisi:

1. A1 + B2 + B11: "+%0,40 beklenti" brut ve maliyetsiz; W'de toplam brut getirinin %67,5'i 2026-03-01 partisindeki gec satirlardan geliyor; bu satirlarin etiket penceresi yazim tarihinden basliyor ve yazim aninda sonuclarin %97,96'si zaten belirlenmisti (onbellek replay'i, yaklasik).
2. A5: RX-CAPTURE-1 E1_t3 medyani hedef - maliyet ile ozdes (2,45 = 3,0 - 0,55); isabet payi %50'nin uzerindeyken medyan ve medyan-breakeven tanim geregi pozitiftir; ortalama net -0,832pp. ECON'un "BETWEEN_GRID_POINTS" etiketi kendi "grid'de sifiri gecmez" ifadesiyle tutarsiz.
3. A6: ANS-1 SUPPORTED ile NS-1/NS-A SCREEN_NOT_SUPPORTED ayni nokta tahminine (2,624845pp) ve ayni 34.762 satir / 54 gunluk ornege dayaniyor; aile-duzeyi %98,75 GA sifiri iceriyor. ANS-1 on-kaydi git'te sonuclarla ayni commit'te (b780b10) ilk kez gorunuyor; "OOS-disiplinli" ifadesi kendi "in-sample" notuyla celisiyor.
4. A4: fixed-target "en yuksek medyan" tablosunun 25 satiri da medyan %10,000'da esit; siralama esitlik sirasina bagli. Aile duzeyinde WRC p 0,741, SPA p 0,776, PBO 0,6. Brief'teki en iyi konfigurasyon (ATR>=3, TP %10, 2xATR stop, h=10) tablonun ilk satiri degil; celiski raporlandi, cozulmedi.
5. A7: 2026-05-21 "locked OOS" sinirinin sonuclardan once donduruldugu dogrulanamiyor (decision-log.md:90); D7 (decision-log.md:57) mevcut setleri OOS saymiyor; pitch slaydindaki "locked OOS kasitli olarak kapali tutuldu (by design)" (docs/pitch_deck_slides_2026-09-07.md:104) bu kayitla celisiyor.

## Faz A

Her iddia icin brief bolum 17 sorulari kisa satirlarla yanitlanir. PRIOR = repoda onceden var olan artefakt/kayit; yeniden olcum yapilmadiysa etiket PRIOR'a dayanir.

### A1 - Arsiv ortalamasi brut +%0,40 (signals_archive, decided satirlar)

- Iddia/kaynak: decision-log.md:78 ve :102 (n=5,206 decided satir, ortalama +%0,40, medyan -%0,64, isabet %30,06; brut, maliyetsiz, ideal barrier fill). Yatirimci yuzeyi: docs/pitch_deck_finpilot_2026-09-07.html:97 "Tarihsel ortalama (barrier-tabanli beklenti) +%0,40" [V] etiketiyle; ayni dosya :96 isabet "%30,16" ve :117 "5.216 sinyal" (decision log ile n ve isabet farkli; farkli anlik goruntu olabilir - HYPOTHESIS). Etiket: SUPPORTED (PRIOR); bagimsiz yeniden hesap Faz B1/B2.
- Gecerli oldugu varsayimlar: (1) `ts` sinyal tarihidir; (2) her satir sonuc bilinmeden arsive girmistir; (3) ayni barda TP, SL'den once test edilir (decision-log.md:102); (4) giris = sinyal gunu kapanisi (decision-log.md:78); (5) sifir maliyet, boyutlama yok, ortusen sinyaller korunur (decision-log.md:102: 5,748 satir / 4,318 sembol-gun).
- Tersine ceviren tek varsayim: kuyrugun dahil edilmesi. decision-log.md:78: ust %5 (260 satir) cikarilinca ortalama -%0,16; ust %5 net toplamin %138,5'i (PRIOR).
- Baseline adaleti: baseline yok; sifir referansi kullanilmis. Yuksek oynakli hisselerde TP/SL asimetrisi mekanik olarak pozitif ortalama uretebilir (HYPOTHESIS); ayni gun secilmeyen hisselerle barrier karsilastirmasi raporlanmamis.
- Sizinti riski: `ts` yazim zamani ise ve satirlar sinyal tarihinden gunler sonra eklendiyse, secim sonuc bilgisiyle yapilmis olabilir (Faz B1/B2'de olculdu).
- Az gune yogunlasma: decision-log.md:78: ust %1'in 48/52'si iki "sinyal tarihi"nde (2026-03-01 ve 2026-03-03). 2026-03-01 Pazar gunudur; bu, kullanilan tarihin piyasa gunu degil yazim gunu olabilecegine isaret eder (Faz B1).
- Sonuca gore secilmis metrik: medyan negatifken ortalama "beklenti" olarak sunulmus (pitch :97); decision-log.md:69 ve :103 bunu brut/maliyetsiz oldugu belirtilmeden sunulan beklenti olarak isaretliyor -> "beklenti" ifadesi CONTRADICTED (PRIOR).
- Raporlanmamis denemeler: arsive giris kurallarinin (esik, grade) zaman icindeki degisimi bilinmiyor - NOT_MEASURABLE bu rolde.
- Maliyet: sifir; net beklenti olculemez (decision-log.md:102).
- Secilmeyen hisseler: karsilastirma yok - UNRESOLVED.
- Uretim esdegerligi: alpaca_orders 11 emir / 0 fill; gerceklesen islem yok (decision-log.md:102).
- Alternatif aciklama: pozitif ortalama birkac gunluk olay kumelenmesi + gec ekleme + barrier mekaniginden dogabilir; secim becerisi gerektirmez.
- Dogrulama yontemi: (a) yalniz yazim gunu = sinyal gunu olan satirlarla gun-kumelenmis CI; (b) ayni gun, ayni ATR desilinde secilmeyen evrene ayni barrier kurali (matched-random); (c) gap-aware giris + maliyet senaryolari; (d) en buyuk gunler haric duyarlilik.

### A2 - Conviction olasiliklari (`_CONV_PROB`) ve "calibrated" ifadesi

- Iddia/kaynak: scanner/features.py:179 `_CONV_PROB = {"A": 0.73, "B": 0.59, "C": 0.52}`; yorum :176-178 "Sinyal kalitesi labi (2026-06, n=6410): skor kalibre ... conviction_prob = o tier'in gozlemlenen >=%5 isabeti (tahmin)"; tier mantigi :223-237; env kapisi :182-183 ve :221-222 (`FINPILOT_ENABLE_CONVICTION_TIERS`, varsayilan "0"). distribution/glossary.py:24-25 "A calibrated range ... recalibrated as outcomes accumulate"; :152-153 "calibrated probability". Etiket: SUPPORTED (kod okundu).
- Gecerli oldugu varsayimlar: 2026-06 lab orneginde (n=6410) olculen tier frekanslarinin gelecege tasinabilmesi; ">=%5" olayinin ufku ve metrigi (kapanis mi, MFE mi) kodda tanimli degil.
- Tersine ceviren tek varsayim: tier esiklerinin oranlarin olculdugu ayni ornekte secilmis olmasi (in-sample). Bagimsiz ornekte oranlar dusebilir - HYPOTHESIS.
- Baseline adaleti: ayni gun tier'siz evrenin >=%5 oranina gore lift raporlanmamis.
- Sizinti: lab orneginin tarih araligi ve esik secim sureci kodda yok - NOT_MEASURABLE.
- Az gune yogunlasma: raporlanmamis - UNRESOLVED.
- Sonuca gore secilmis metrik: yorum :177 iki esik (>=%5 %73, >=%10 %69) veriyor; esik secim gerekcesi yok.
- Raporlanmamis denemeler: denenen tier kombinasyonu sayisi kayitli degil - UNRESOLVED.
- Maliyet: olasilik tanimi maliyetten bagimsiz; uygulanamaz.
- Uretim esdegerligi: sozluk sabit; features.py icinde guncelleyen yol yok (repo geneli kontrol Faz B notlarinda). "recalibrated as outcomes accumulate" (glossary.py:25) bu fonksiyon icin kodla desteklenmiyor - CONTRADICTED (bu fonksiyon kapsaminda). Env bayragi kapaliyken prob 0.0 (:221-222); .env okunmadigindan uretim durumu NOT_MEASURABLE.
- Alternatif aciklama: 0.73/0.59/0.52 bir kalibrasyon egrisi degil, tek bir in-sample frekans tablosudur.
- Dogrulama yontemi: dondurulmus tier tanimiyla ileriye donuk veride reliability diagram + Brier/ECE; ayni gun eslestirilmis tier'siz kontrol; olay tanimi (ufuk, metrik) once commit edilir. Arsivdeki tier-bazli gozlenen oran Faz B notlarinda (MEASURED, tanim farki not edilerek).

### A3 - "48.727 path" sentezi ve CPCV/PBO/White RC/Hansen SPA atfi (pitch deck)

- Iddia/kaynak: docs/pitch_deck_slides_2026-09-07.md:111 "*[V] 11 Agustos 2026 sentezi · 48.727 path · CPCV/PBO/White RC/Hansen SPA*" (Slide 5 "What Doesn't Work"); ayni slayt :104 "3.120 TP/SL konfigurasyonunda kuresel kanit yok; locked OOS kasitli olarak kapali tutuldu (by design)". Kaynak artefakt data/backtest_out/fixed_target_full_universe_2026-08-11.md: :5 `3120` konfigurasyon; :9 "`100440` raw, `48727` canonical, `26372` path-resolved"; :18 "CPCV/PBO: `0.6` across `10` paths"; :19 White RC p 0.7413; :20 Hansen SPA p 0.7761. Etiket: negatif sonuc olarak SUPPORTED; "48.727 path" etiketi CONTRADICTED.
- Tespit: 48,727 path sayisi degil kanonik satir sayisidir; path-resolved satir 26,372; CPCV 10 path ile calismis ve PBO 0,6. Slayt bu kaniti dogru yonde (kuresel kanit yok) kullaniyor, fakat orneklem/path sayisini yanlis aktariyor ve [V] (verified) etiketi tasiyor.
- Gecerli oldugu varsayimlar: zaman bloklarinin dengeli olmasi. Kaynak :11 ay kapsami: 2026-05 = 11,342 ve 2026-06 = 11,588 satir; toplam 26,372'nin %86,9'u (bu raporda elle toplandi); 2025-11 ve 2025-12 yalniz 6'sar satir; 2026-01..03 yok.
- Tersine ceviren tek varsayim: dogrulama bolumu tek aydir (:12 validation_rows 11,588 = :11'deki 2026-06 sayisi); ":21 Gross + train/validation stable: 130" tek-ay rejimine bagli.
- Baseline adaleti: WRC/SPA benchmark tanimi okunmadi - UNRESOLVED.
- Sizinti: bu deneyde locked_oos_rows_unopened 269 (:12, 2026-07 satirlari) ve "not opened by runner" (:23); ancak slayttaki "by design kapali" genellemesi, decision-log.md:114-115'te baska artefaktlarda raporlanan locked-OOS sonuclariyla CONTRADICTED (PRIOR).
- Az gune yogunlasma: %86,9 iki ay; gun bazi dagilim raporlanmamis.
- Sonuca gore secilmis metrik: "Highest-Median Configurations" (:25) medyana gore siralar; medyan TP'ye doyar (A4).
- Raporlanmamis denemeler: 3,120 konfigurasyon acikca raporlanmis; ancak 2026-08-05 tarihli onceki fixed-target raporu ve sonradan commit edilen niteleme kurali (decision-log.md:116, PRIOR) ayni ailenin onceki denemeleridir.
- Maliyet: ":13 Observed transaction costs: `insufficient_data`; cost values below are scenarios".
- Secilmeyen hisseler: kural-kural karsilastirmasi; secilmeyenle karsilastirma yok.
- Uretim esdegerligi: yok (":4 research-only").
- Alternatif aciklama: tum kapilar ayni iki aylik rejimi olcuyor olabilir; "kuresel kanit yok" sonucu da bu rejime ozgu olabilir.
- Dogrulama yontemi: slayt etiketinin kaynakla birebir eslestirilmesi (satir vs path, CPCV path=10, PBO=0,6 yazilmasi); leave-one-month-out tekrari; benchmark tanimi ile WRC/SPA yeniden calistirma.

### A4 - Fixed-target "en iyi" konfigurasyon (2026-08-11)

- Iddia/kaynak: data/backtest_out/fixed_target_full_universe_2026-08-11.md:25-29 ilk satir `ATR>=6|tp=10.00%|atr_stop=2|h=20`: n=9103, ortalama %0.589, medyan %10.000, train ve validation medyan %10.000, HAC p 0.055914, DSR 1.000000; :30-33 diger satirlar da medyan %10.000 ve DSR 0.000000. Etiket: tablo SUPPORTED (okundu); konfigurasyon ustunlugu NOT VERIFIED. Celiski (CORE-005, cozulmedi): bu rolun brief'i en iyi konfigurasyonu `ATR>=3|tp10|stop2|h10` olarak veriyor; artefaktta `ATR>=3|tp=10.00%|atr_stop=2|h=10` en yuksek medyan tablosunda (:29-53) yok, yalniz 130'luk "gross + train/validation stable" (:57) ve 129'luk cost-positive (:58) listelerinde var (RT_out_2.txt). Tablonun 25 satirinin tamami medyan %10.000 ile esit; "en iyi" secimi esitlik sirasina bagli.
- Gecerli oldugu varsayimlar: medyanin konfigurasyonlari ayirt etmesi; ATR>=%6 ve 2x ATR stop (>= %12 uzaklik) ile TP %10 ayni barda cakisirsa uygulanan siralama (bu raporda okunmadi - UNRESOLVED).
- Tersine ceviren tek varsayim: estimand. Medyan TP seviyesine doyuyor (birden cok satirda %10.000) -> siralama bilgisiz; ortalama %0.589 ve HAC p 0.056 (%5'te anlamsiz). RX-CAPTURE-1 kaydi ayni "MEDIAN DEGENERACY" sorununu belgeliyor (decision-log.md:3285).
- Baseline adaleti: ayni evrende rastgele giris + ayni TP/SL kontrolu tabloda yok.
- Sizinti: niteleme kurali 2026-08-06'da, 2026-08-05 raporundan sonra commit edilmis (decision-log.md:116, PRIOR).
- Az gune yogunlasma: A3'teki iki ay yogunlugu (%86,9) burada da gecerli.
- Sonuca gore secilmis metrik: medyan siralamasi doymus. Duzeltme: onceki taslaktaki "DSR yalniz ilk satirda 1.0" ifadesi yanlisti; DSR 1.000000 sekiz satirda (:29, :35, :36, :41, :42, :46, :47, :51), :34'te 0.999514, :43'te 0.065072, kalan 15 satirda 0. Tablo ici en yuksek ortalama `ATR>=4|tp=10.00%|atr_stop=2|h=20` %1.198, HAC p 0.000000 (:46); tekil p-degerleri 3.120 denemeye gore ayarlanmamis. FDR 1.012 kesif (:17) ile aile-duzeyi WRC/SPA (:19-20) ayni anda raporlanmis; farkli null tanimlari aciklanmamis - UNRESOLVED.
- Raporlanmamis denemeler: aile 3,120 konfigurasyon; PBO 0,6, WRC p 0,741, SPA p 0,776 (:18-20) -> en iyinin sanstan ayrilamadigi.
- Maliyet: gozlenmemis (:13).
- Secilmeyen hisseler: ATR<6 alt kumesine ayni kural karsilastirmasi yok.
- Uretim esdegerligi: yok. Ayrica ayni ozellik ailesi (ATR>=%6 / |gap|>=%3) ANS-1'de negatif tarama olarak kullaniliyor (A6): ayni ozelligin iki hatta zit yonlu kullanimi.
- Alternatif aciklama: yuksek oynaklik + 20 bar ufuk -> +%10'a dokunma olasiligi mekanik olarak yuksek; dokunma oranini olcen medyan secim becerisi gostermez.
- Dogrulama yontemi: ortalama + kuyruk metrikleriyle siralama; ayni ATR desilinde rastgele giris; ayni-bar belirsizligi icin kotumser (SL-once) kural; leave-one-month-out.

### A5 - RX-CAPTURE-1 (2026-09-22) ve ECON incelemesi (2026-09-23)

- Iddia/kaynak: reports/research_x_capture_1_2026-09-22.md:5 (n=34.762, 54 tarih); :10-11 E1_t3 medyan net %2,45 ve E1_t5 %1,13587 -> CAPTURE_SUPPORTED_PENDING_VERIFICATION. reports/research_x_capture_1_econ_2026-09-23.md:5 Overall FURTHER_VALIDATION_SUPPORTED; :9 E1_t3 breakeven BETWEEN_GRID_POINTS. decision-log.md:94 ECON kaydini "contradicted" olarak listeliyor (hangi kismi: bu rolde okunmadi - UNRESOLVED). Etiket: hedef artefakti SUPPORTED; capture ustunlugu NOT VERIFIED.
- Varsayim ve tersine ceviren tek varsayim: estimand = medyan. Isabet payi %50'yi asinca medyan net = hedef - maliyet olur (capture :20-26; 2,45 = 3,0 - 0,55). Ortalama net iki aday icin de negatif (econ :15-16: -0,832pp, -0,841pp); ortalama estimand'i ile hukum tersine doner.
- Hedef artefakti: medyan, maliyet %3'un altinda kaldikca tanim geregi pozitif; gercek medyan-breakeven %3,0 (hedef) ve grid disinda. "median never crosses zero on the grid" (econ :24) ile "BETWEEN_GRID_POINTS" (econ :9) birbiriyle tutarsiz -> etiket CONTRADICTED.
- Baseline / secilmeyen: E0 (T+5 tut) ayni secimle (capture :43-47), adil fakat o da medyanla; secim LOCKED oldugu icin secilmeyen hisselerle karsilastirma yok.
- Sizinti / bagimsizlik: ayni kanonik 54 gunluk EOD export (n=34.762) NS-1'de (reports/research_x_ns1_negative_screen_2026-09-22.md:6) ve ANS-1'de (ayni n) kullaniliyor; yeni veride tekrar NOT_AVAILABLE (econ :40-41); D7 geregi OOS degil.
- Gun yogunlasmasi: E3 tek gun payi %39,4, E2 %28,6 / %27,4 (capture :36-39); 54 tarihte 5 gunluk blok bootstrap ~11 blok -> GA kirilgan; E1_t5 erken/gec isaret tutarsiz (econ :32-34).
- Sonuca gore metrik / denemeler: medyan dejenerasyonu sonradan fark edildi (capture :18 "post-hoc") ama hukum korundu; 8 aday Holm ile ayarli, fakat onceki TP/SL bataryalari (decision-log.md:3273; A4'teki 3.120 konfigurasyon) aileye dahil degil.
- Maliyet / uretim: %0,55 ve %1,00 varsayim, gozlenen spread/slippage yok (econ :39-40); uretim esdegerligi yok (econ :46-50).
- Alternatif aciklama: yuksek oynaklikli kohortta T+1..T+5 icinde +%3'e dokunma mekanik olarak yaygin (isabet payi ~%61,5, econ :27); kuyruk kayiplari ortalamayi negatife ceker.
- Dogrulama: ortalama, kirpilmis ortalama, isabet payi ve kuyrukla hukum; ayni gun ve ayni ATR desilinde rastgele giris ile ayni cikis kurali; gun-kumelenmis GA; dondurma sonrasi yeni veri.

### A6 - ANS-1 (2026-09-18) ve NS-1 (2026-09-22) negatif tarama

- Iddia/kaynak: reports/ans1_attention_negative_screen_2026-09-18.md:13 ANS-1 = SUPPORTED; :26 medyan iyilesme +2,62pp; :37 blok-bootstrap %95 GA [+0,16; +3,86]; bayrak = abs(gap) >= %3 VEYA ATR >= %6 (decision-log.md:3175). reports/research_x_ns1_negative_screen_2026-09-22.md:8 Overall NO_SCREEN_SUPPORTED; :14 NS-A (ANS-1'in birebir tekrari) ayni nokta tahmini 2,624845pp, ayarli %98,75 GA [-0,24; 4,57] -> SCREEN_NOT_SUPPORTED; :35 ANS-1 hukmu "yeniden acilmadi". Etiket: ANS-1 SUPPORTED NOT VERIFIED (ayni veride daha muhafazakar aralik sifiri iceriyor).
- Tersine ceviren tek varsayim: aralik yontemi / estimand. Ayni nokta tahmini aile-duzeyi ayarla sifiri kapsiyor (NS-1 :37-44). Ortalama ile: attention grubunun ortalamasi +8,94, medyani -2,33 (ANS-1 :46); bu grubu cikarmak evren ortalamasini dusurebilir (normal grup ortalamasi raporlanmamis - UNRESOLVED).
- On-kayit: ANS-1 :5 on-kaydi runner docstring'ine dayandiriyor; runner, ANS-1 raporu ve NS-1 on-kayit/rapor dosyalari git'e ilk kez ayni commit'te girmis (b780b10, 2026-09-23 13:43:45 +0200; RT_out_2.txt); ANS-1 JSON artefakti git'te izlenmiyor. Sonuclardan once dondurma git ile dogrulanamaz - NOT VERIFIED.
- OOS ifadesi: ANS-1 :47 "pre-registered OOS-disiplinli kontrol" derken :61 "In-sample universe (2026-05->08)" diyor; D7 ile birlikte "OOS" niteligi CONTRADICTED.
- Bagimsizlik / gun yogunlasmasi: ANS-1, NS-1 ve RX-CAPTURE-1 ayni 54 gunluk export'u paylasir (n=34.762); ANS-1 :47'deki "uc bagimsiz katman" ayni ornege dayanir. NS-B3 etkisi yalniz erken yarida anlamli (NS-1 :46-50).
- Raporlanmamis denemeler: NS-1 calismasi sirasinda estimand degistirildi (ilk taslak median(kept)-median(full), sonra kept-removed; decision-log.md:3241) - belgelenmis ama ek bir deneme yolu.
- Maliyet / secilmeyen: eleme islem maliyeti tasimaz (ANS-1 :45) ama pozitif kuyrugu kacirma maliyeti olculmedi (:46, :63); matched-random ve null-shuffle kontrolleri var (:38-39), medyan uzerinde.
- Uretim esdegerligi: yok; urun konumlandirmasi Level B (:57, :68). Ayni ATR >= %6 ozelligi fixed-target'ta pozitif secim filtresi (A4, artefakt :29): iki hatta zit yonlu kullanim.
- Alternatif aciklama: yuksek oynaklik/gap hisseleri saga carpik; eleme "kotu hisseleri" degil carpikligi cikarir; medyan iyilesir, ortalama kotulesebilir.
- Dogrulama: kalan evrenin ortalama ve kirpilmis ortalamasi + kuyruk firsat maliyeti; tek aile-duzeyi aralikla tek hukum; dondurulmus kuralla yeni tarihlerde ileriye donuk test.

### A7 - 2026-05-21 "locked OOS" durumu (onceki taslakta A8 numarasiyla yazildi)

- Iddia/kaynak: Agustos belgeleri "Locked OOS NOT_OPENED" derken Temmuz/Eylul artefaktlari locked-OOS sonuclari raporluyor (n=62; TP5/SL1 +%2,0501, TP5/SL1.5 -%0,0046) (decision-log.md:91, :114-115). decision-log.md:90: 2026-05-21 siniri ve sonuclari ilk kez birlikte common_buy_accuracy.json'da (2026-07-15T16:52:02Z, locked_oos n=44); cikis profilleri locked-OOS sonucuna gore siralanmis; test-plan kapilari sonra commit edilmis. D7 (decision-log.md:53, :57): mevcut hicbir veri seti OOS sayilmaz. Etiket: CONTRADICTED (PRIOR; "kilitli/dokunulmamis" niteligi kayitlarin kendisiyle celisiyor).
- Gecerli oldugu varsayimlar: sinirin sonuclardan once dondurulmasi, erisim kaydi, tek kullanim.
- Tersine ceviren tek varsayim: dondurma zamani; sinir ve sonuc ayni artefaktta ilk kez gorunuyorsa "kilitli" niteligi tasinamaz.
- Baseline adaleti: TP5/SL1 (+%2,05) ile TP5/SL1.5 (-%0,005) arasindaki fark kucuk orneklemde cikis parametresine asiri duyarlilik gosteriyor (PRIOR rakamlar).
- Sizinti: cikis profili locked-OOS sonucuna gore secilmis (decision-log.md:90) -> secim sizintisi.
- Az gune yogunlasma: n=62 icin gun dagilimi raporlanmamis - UNRESOLVED.
- Sonuca gore secilmis metrik: iki TP/SL profili arasinda sonuca gore secim.
- Raporlanmamis denemeler: en az alti farkli OOS siniri (decision-log.md:114) -> coklu yol (forking paths).
- Maliyet: kayitta belirtilmemis - UNRESOLVED.
- Secilmeyen hisseler: karsilastirma raporlanmamis - UNRESOLVED.
- Uretim esdegerligi: test edilen yontem offline proxy; uretim siralamasi yeniden kurulmamis (decision-log.md:90).
- Alternatif aciklama: pozitif sonuc tek-parametre secimi ve n=62 varyansiyla aciklanabilir.
- Dogrulama yontemi: ileriye donuk, once commit edilen (hash + zaman damgasi) protokol; erisim logu; runner'larda zorunlu holdout erisim korumasi (repo icindeki varligi bu kosuda dogrulanmadi); o zamana kadar "OOS" etiketi kullanilmaz (D7). D7 metni decision-log.md:57 madde (5)'te dogrulandi: "existing sets, including the 2026-05-21 locked OOS and the PIT holdout, are not treated as out-of-sample". Artefakt metadata kontrolu bu kosuda yapilmadi (NOT_MEASURABLE). Bu raporda signals_archive'in sinyal tarihi > 2026-05-20 olan 111 satiri sonuc istatistiklerinden dislandi (RT_out_2.txt).

## Faz B

### Hukum tablosu

| # | Iddia (kisa) | Hukum | Kanit (tek satir) |
|---|---|---|---|
| B1 | `ts` arsiv yazim zamani; ust %1 iki `ts` gununde, ~9 sinyal gunune yayili | VERIFIED | `ts` = payload `added_at` (5.719/5.719); migrate:39; W'de ust %1 (k=51): 47/51 iki `ts` gunu, 9 sinyal gunu (45/51 uc sinyal gunu) |
| B2 | ~1.616 gec satir toplamin ~%65,9'u; zamaninda ~+%0,197, GA sifiri icerir | VERIFIED (W) | 1.616 satir, hepsi `ts` 2026-03-01 21:45; W payi %67,5, PRIOR payda ile %65,9; zamaninda +%0,203 [-0,093; +0,499] |
| B3 | Sira = grade, execution_confidence, conviction_prob, ranking_score (= legacy) | PARTIALLY VERIFIED | snapshot_builder.py:99-116; evaluate.py:605-607 env bayragina bagli (varsayilan legacy); `or` zinciri composite'e dusebilir |
| B4 | Alpaca `feed="iex"`; hacim likiditesi IEX-yalniz | PARTIALLY VERIFIED | data_fetcher.py:872 dogru; yfinance yedegi konsolide hacim karistirir; uretim bayragi NOT_MEASURABLE |
| B5 | NaN -> 100; NaN ATR% azami legacy bileseni; uretime ulasir mi | PARTIALLY VERIFIED | score_engine.py:393 ve :209/:212 mekanizmasi dogru; konum features.py:198 degil; uretim olusumu HYPOTHESIS |
| B6 | POST /scan/daily-report: dogrulanmamis `date` ile yol, auth yok | VERIFIED (statik) | scan.py:902, :911-919; `require_auth` yok (karsi :325) |
| B7 | 600 s zaman asimi: worker surer, sonuc yazilmaz | VERIFIED (statik) | scan.py:488-513 (eski yol); :413-447, :457 ve scan_coordinator.py:186-191 (koordineli yol) |
| B8 | Onarim 3 zaman dilimini yeniden ceker; fast_info.last_price limiter disi ek indirme | VERIFIED (statik) | data_fetcher.py:1215-1237, :431-436, :446-447; yfinance 1.4.1 quote.py:246-255, :129-132 |
| B9 | 3 bayrak hem filter_score (x1,5) hem tekil (x0,5) | VERIFIED | evaluate.py:299; score_engine.py:130, :143-145, :261-265 |
| B10 | `_kelly_reduced_cycle` yazilir, okunmaz | VERIFIED (literal arama) | scheduler.py:937 tek eslesme; deger 3; dinamik erisim dislanamadi |
| B11 | Resolver pencereyi `ts`'den baslatir, giris sinyal-ani | VERIFIED | resolve_open_signals.py:331-334, :240-242; replay uyumu ts-bazli %98,4 / sinyal-bazli %68,8 |

### B1 - signals_archive.ts yazim zamani mi, sinyal tarihi mi?

- Hukum: VERIFIED.
- Kod: scripts/migrate_signal_archive_to_sqlite.py:39 `ts = added_at or signal_date or fallback`; distribution/archive_bridge.py:55 `ts = datetime.now(tz=UTC)`, :53 ve :69 `signal_date` = snapshot tarihi. `ts` tanim geregi yazim zamanidir.
- Veri (tum satirlar, sonuc-bagimsiz; RT_out_2.txt): 5.748 satir; `ts` ile payload `added_at` 5.719/5.719 satirda dakikasina kadar ayni. Gecikme (`ts` tarihi - sinyal tarihi): 0 gun 3.929, 5-145 gun 1.639, -1 gun 180. `ts` haftanin gunu: Pazar 2.129, Cumartesi 197. Not: `signal_date` de hafta sonuna dusebiliyor (Pazar 808, Cumartesi 227); sinyal tarihi her zaman islem gunu degil.
- Ust %1 (W: sinyal tarihi <= 2026-05-20, karar satiri n=5.126, k=51): 47/51 iki `ts` gununde (2026-03-03: 26; 2026-03-01, Pazar: 21); 9 farkli sinyal gunu, fakat 45/51 uc sinyal gununde (2026-03-03: 26, 2026-02-12: 10, 2026-02-17: 9). Tam orneklemdeki 52 satir rakami PRIOR (decision-log.md:78); orada "signal dates" denen iki tarih `ts` tarihleridir (etiket hatasi).
- Ek bulgu: `ts` saati 09:00 olan 2.065 satirin tamami gecikme 0 ve sinyal tarihinin 09:00'i (2025-09/10 dosyalari, hafta sonu tarihleri dahil; RT_out_3.txt). Bu yapay bir damga olabilir; gecikme 0 gercek zamanli arsivlemeyi kanitlamaz (HYPOTHESIS).

### B2 - Gec arsivlenen satirlar ve ekleme mekanizmasi

- Hukum: VERIFIED (W icinde; tam orneklem paydasi PRIOR).
- W karar satirlari (karne tanimi resolved_win/resolved_loss, distribution/karne.py:89; n=5.126, 46 sinyal gunu): ortalama +%0,395, medyan -%0,642, isabet %30,04; gun-kumelenmis %95 GA [0,118; 0,673] (CR), [0,114; 0,656] (kume bootstrap).
- Gec (5-145 gun): n=1.616 (iddia ile ayni), 11 sinyal gunu, ortalama +%0,846, GA [0,406; 1,285]. W'de toplam brut getiri payi 1.366,64 / 2.025,30 = %67,5. PRIOR tam orneklem paydasi (5.206 x 0,3984 ~ 2.074,1; decision-log.md:102) ile 1.366,64 / 2.074,1 = %65,9 -> iddia ile tutarli (pay REPRODUCED, payda PRIOR).
- Zamaninda (gecikme 0): n=3.382, 32 gun, ortalama +%0,203 (iddia +%0,197, tam orneklem), medyan -%0,598; GA [-0,093; +0,499] (CR), [-0,050; +0,495] (kume bootstrap) -> sifiri icerir. Gecikme -1: n=128, ortalama -%0,228 (RT_b2_groups.csv).
- Ekleme mekanizmasi: 1.639 gec satirin tamami tek partide, `ts` = 2026-03-01 21:45 (Pazar), sinyal tarihleri 2025-10-07..2026-02-24 (11 gun). Eski JSON arsivinde (data/signal_archive/<sinyal_tarihi>.json, 55 dosya) ayni parti 1.970 kayit (`added_at` 2026-03-01T21:45; 331'i 2026-03-01 dosyasinda, gecikme 0). Tabloya 2026-05-23 tasimasiyla girdi (commit 1ade01f; migrate:39 `ts = added_at`, :81 INSERT OR IGNORE). Eski zincir "watchlist API POST /archive -> JSON -> migrate" (archive_bridge.py:4-5; guncel endpoint api/routers/watchlist.py:760). `signal_archive` iceren ilk git commit'i a815cf2 (2026-05-13), partiden sonra; partiyi ureten kod git'te yok -> UNRESOLVED. Dosya mtime'lari 2026-05-23T07:54 (sonradan yeniden yazilmis; ozgun yazim zamani kanitlanamaz).
- Sonuc bilgisi: yazim aninda bu satirlarin %97,96'si sinyal-tarihi bazinda bariyerine zaten degmisti (onbellek, yaklasik) -> secim sonuc bilgisiyle yapilmis olabilir (olasilik SUPPORTED); fiilen yapildigi NOT_MEASURABLE. Gozlem: pencere duzeltilince gec satirlarin ortalamasi (+%0,403) zamaninda satirlarin ayni onbellek replay'ine (+%0,356) yakin; gec satir fazlaliginin buyuk kismi pencere kaymasiyla (B11) aciklaniyor, ek secim etkisine dair guclu iz yok (HYPOTHESIS).

### B3 - Yayinlanan aday sirasi

- Hukum: PARTIALLY VERIFIED.
- distribution/snapshot_builder.py:99-116 `_sort_key` = (grade sirasi, execution_confidence sirasi, -conviction_prob, -skor); skor = `ranking_score or legacy_quality_score or composite_score or score` (:106-115); yayin sirasi :408 `graded.sort(key=_sort_key)`.
- scanner/evaluate.py:605-607: `ranking_score` = composite_score eger `legacy_composite_ranking_enabled()`, aksi halde legacy_quality_score; scanner/score_engine.py:238-240 bayrak FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING, varsayilan "0". Varsayilanda composite sirayi belirlemez; bayrak 1 ise belirler. Uretim .env okunmadi -> NOT_MEASURABLE (decision-log.md:1260 gozlenen varsayilan 0, PRIOR).
- Ek: `or` zinciri ranking_score ve legacy 0.0/None ise composite_score'a duser (:108-111); conviction tier bayragi kapaliyken prob 0.0 (features.py:221-222) ve grade `tier` alanindan gelir (snapshot_builder.py:91-95); son esitlik kirici yok (decision-log.md:1260).

### B4 - Alpaca feed='iex'

- Hukum: PARTIALLY VERIFIED (kod yolu dogru; evrensellik degil).
- scanner/data_fetcher.py:867-874 `StockBarsRequest(..., feed="iex", ...)` (`_prefetch_alpaca_bulk`, :805); dosyadaki tek feed ayari (:872).
- Hacim kullanan kurallar: evaluate.py:283 (hacim > vol_med20 x 1,2), :302-304 volume_multiple, :199-204 dollar_adv = 20 gun Close x Volume ortalamasi -> position_cap (:614-617), :376-377 `vol_avg10 >= min_avg_vol (300.000)` likidite kapisi (:381-384).
- Kosul: Alpaca'dan gelen barlarda hacim IEX-yalnizdir; eksik sembol/zaman dilimleri yfinance ile (konsolide hacim) doldurulur (data_fetcher.py:1201-1206, :1221-1237) -> ayni taramada karisik hacim tanimi. Alpaca'nin uretimde etkin olup olmadigi env'e bagli (data_fetcher.py:252) -> NOT_MEASURABLE. IEX payi repoda olculmemis; yon: IEX hacmi <= konsolide hacim -> likidite kapisi daha siki, dollar_adv dusuk (HYPOTHESIS, buyukluk olculmedi).

### B5 - NaN girdilerin skorlara etkisi

- Hukum: PARTIALLY VERIFIED (mekanizma dogru; iddiadaki konum ve uretim olusumu kismen).
- scanner/score_engine.py:393 `max(0.0, min(100.0, (score / effective_max_reco_score()) * 100.0))`: Python'da `min(100.0, nan)` = 100.0 -> 100 doner (RT_out_2.txt NAN SEMANTICS); :395 yalniz TypeError/ValueError/ZeroDivisionError yakalar.
- NaN ATR%: scanner/features.py:186-206 `compute_atr_pct`, son 15 barda High/Low/onceki Close NaN ise NaN dondurur (istisna yok). Azami bilesen score_engine.py:209 `max(0.0, min(1.0, value / scale))` ile olusur: NaN -> 1,0; :212 ve :218 `1.5 * atr` = azami 1,5 puan (0-100 olcekte +15). Iddiadaki "features.py ~198" NaN'in uretildigi dongu; ekleme score_engine.py:209-218'de.
- Uretime ulasabilir mi: alignment_ratio ve momentum_ratio korumasiz `float()` (score_engine.py:131, :141); squeeze ve lottery `or 0.0` NaN'i yakalamaz (NaN truthy) ve `max(0, min(1, nan))` = 1,0 (:161-162, :173-174; bayraklar acikken). Veri: yfinance tekil yolunda `dropna()` (data_fetcher.py:515); toplu yollarda yalniz tum-NaN veya Close-NaN satirlar dusuruluyor (:986, :1012, :1016, :1065, :1103) -> High/Low NaN satirlar kalabilir. Uretimde gozlenmedi -> HYPOTHESIS.

### B6 - POST /scan/daily-report yol ve auth

- Hukum: VERIFIED (yalniz statik analiz; hicbir HTTP istegi gonderilmedi).
- api/routers/scan.py:911-912 `@router.post("/scan/daily-report")` `def save_daily_report(req: DailyReportRequest)`: `Depends(require_auth)` yok (karsilastirma: /scan :322-325). Router yalniz prefix ile ekli (api/main.py:362); uygulama `http` middleware'i yalniz metrik toplar (api/main.py:303-325).
- :902 `date: str = Field(..., description="YYYY-MM-DD")`: desen veya validator yok; :915 `_REPORTS_DIR / f"{req.date}.json"`, :918 `open(..., "w")`. `..` iceren veya mutlak yol olan `date` ile data/daily_reports disina `.json` uzantili dosya yazimi mumkun (pathlib'de sag taraf mutlaksa taban atilir). OWASP A01 (Broken Access Control / path traversal). GET /scan/daily-report/{date} (:948-957) ayni desenle okur (yol parametresi; siddet daha dusuk, dogrulanmadi).
- Oneri (uygulanmadi, Level B): `[0-9]{4}-[0-9]{2}-[0-9]{2}` desen dogrulamasi, `resolve()` sonrasi taban dizin kontrolu, `require_auth`.

### B7 - /scan 600 s zaman asimi davranisi

- Hukum: VERIFIED (statik).
- Eski yol (`_run_scan`, api/routers/scan.py:461-513): `asyncio.wait_for(loop.run_in_executor(...), timeout=_SCAN_TIMEOUT_SECONDS)` (:488-499), `_SCAN_TIMEOUT_SECONDS = 600` (:38); zaman asiminda 504 (:500-506). Executor is parcacigi iptal edilemez ve calismaya devam eder; kalici yazim (`_persist_shortlist`, `_persist_shadow_ledger`, `_persist_distribution_export`, :601-610) yalniz `_complete_scan` icindedir ve o yalniz basarili await sonrasi cagrilir (:513).
- Koordineli yol (`scan_coordinator.enabled()`, :329-330): `wait_for(shield(future))` (:413-415) -> 504 (:421-424); `finally` icinde `handle.detach()` (:446-447) -> bekleyen kalmazsa `job.cancelled` (core/scan_coordinator.py:186-191; FINPILOT_SCAN_COOP_CANCEL varsayilan "1", :265). Worker degerlendirmeyi bitirir, `check_cancelled()` (scan.py:457) ScanCancelled atar, `_complete_scan` cagrilmaz.
- Not: ScanRequest symbols max_length=500 (:54); 200 sembol tarayici parti boyutu (:654). PRIOR: decision-log.md:835-836 ayni riski kaydediyor. Hangi yolun uretimde etkin oldugu env'e bagli (NOT_MEASURABLE).

### B8 - Onarim yolu ve yfinance fast_info.last_price

- Hukum: VERIFIED (statik; ag cagrisi yapilmadi).
- Onarim: scanner/data_fetcher.py:1171-1206 once zaman dilimi bazinda toplu doldurma (`_bulk_yf_download`, :1202); hala yetersiz semboller (`remaining`, :1215-1219) icin `repair_symbol` -> `fetch_multi_timeframe(symbol, timeframes=timeframes)` (:1223-1228) tum gercek zaman dilimlerini (15m, 1h, 1d; 4h turetilir; :582-586, :678-682) yeniden ceker, yalniz yetersiz olanlari degistirir (:1232-1237). Iddia bu sembol bazli yol icin dogru; tum semboller icin degil.
- Rate limiter: her `fetch()` (:409; `fetch_with_indicators` -> `fetch`, :568) tek token bekler (`get_bucket("yfinance", ...).wait(timeout=5.0)`, :431-436; zaman asiminda yine devam eder, :427-429). Ardindan `tkr.fast_info` ve `getattr(info, "last_price", None)` (:446-447), sonra `tkr.history(...)` (:455). Kurulu yfinance 1.4.1 (yerel metadata): `FastInfo.last_price` -> `_get_1y_prices()` -> `self._tkr.history(period="1y", ...)` ve `get_history_metadata()` (site-packages/yfinance/scrapers/quote.py:246-255, :129-132). Onbellek iskalamasi basina limiter'in saydigi 1 token'a karsilik en az 2 history indirmesi.

### B9 - Composite score cift sayim

- Hukum: VERIFIED.
- scanner/evaluate.py:299 `filter_score = int(volume_spike) + int(price_momentum) + int(trend_strength)`; scanner/score_engine.py:130 `filter_score * 1.5`, :143-145 her bayrak ayrica +0.5; `score_component_breakdown` :261-265 ayni. MAX_RECO_SCORE = 16,5 (:24) yorumu ikisini de iceriyor (:18-20). Her bayrak 2,0/16,5 (%12,1); uc bayrak birlikte 6,0/16,5 (%36,4). Yorum :128-129 agirligi bilincli gosteriyor; cift sayim tanim geregi var.

### B10 - _kelly_reduced_cycle anahtari

- Hukum: VERIFIED (literal arama kapsaminda).
- data/scanner_config.json ust anahtarlari: `_kelly_reduced_cycle` (= 3) ve `kelly_fraction` (RT_out_1.txt; baska deger yazdirilmadi).
- Yazan: core/scheduler.py:937 (`_cycle_count + 1`, drawdown dalinda :912-939). Okuyan: repo genelinde (top-level data/ ve reports/ haric kod ve dokuman) tek eslesme yazici satir; git pickaxe 87138db (2026-06-12) ve 77bf5d3 (2026-06-16). api/, core/, scanner/, distribution/, scripts/, agents/ altinda scanner_config.json gecen tek dosya core/scheduler.py (:800-821 optimizer yazimi, :921-939); dosyanin runtime okuyucusu da bulunamadi (RT_out_3.txt). Dinamik yol kurulumu dislanamadi (UNRESOLVED, dusuk).

### B11 - Resolver pencere tabani (`ts` ve sinyal tarihi)

- Hukum: VERIFIED (kod + replay).
- Kod: scripts/resolve_open_signals.py:331 `"signal_date": _parse_ts(row["ts"]) or _parse_ts(payload.get("signal_date"))` -> `ts` once gelir; :332-334 giris/TP/SL payload'dan; :240-242 pencere = tarihi > signal_date olan ilk 21 bar; :253-262 ayni barda TP once; :190-196 yfinance `auto_adjust=True` (duzeltilmis fiyatla ham giris/TP/SL karsilastirmasi - ayri risk, buyukluk olculmedi).
- Etkilenen karar satirlari (W): 1.616 (gecikme 5-145) + 128 (gecikme -1; pencere sinyal gununun barini da icerir) = 1.744; tum satirlarda sonuc-bagimsiz 1.639 + 180 = 1.819.
- Giris fiyati sinyal-ani: gec satirlarda medyan abs(giris / kapanis - 1) sinyal gununde %0,41 (%73,9'u %1 icinde), `ts` gununde %4,64 (%11,9) (RT_out_3.txt; onbellek kapanislari, yaklasik).
- Replay (gunluk bar onbellegi, yaklasik; RT_b11_replay.csv): gec satirlarda saklanan etiketler ts-bazli replay ile %98,4, sinyal-bazli ile %68,8 uyumlu -> saklanan etiketler ts-bazli uretilmis. %92,0'si `ts` sonrasi ilk barda cozuluyor (fiyat yazim aninda zaten bariyer otesinde). Ayni onbellek kuraliyla ortalama: ts-bazli +%0,868, sinyal-bazli +%0,403 (fark 0,465pp); isabet %39,9 ve %32,6; gecisler: saklanan win -> sinyal-bazli loss 301, loss -> win 201. Kontrol (gecikme 0) uyumu %83,8 (onbellek ile saklanan etiket arasindaki taban uyumsuzluk; 30 gun takvim siniri sonucu degistirmedi).
- Yon: ts-bazli etiketleme gec satirlarin brut ortalamasini yukari ceker. Yaklasik etki: W toplamindan 1.616 x 0,465 = 751 cikarilirsa W ortalamasi +%0,395'ten ~+%0,25'e iner (onbellek farki saklanan etiketlere uygulanmis karisik tahmin; kesin degil).

## Kritik varsayimlar

- B1, B2 ve B11 analizleri payload `signal_date`'in gercek sinyal tarihi oldugunu varsayar; hafta sonuna dusen 1.035 sinyal tarihi bu varsayimi zayiflatir.
- Replay gunluk bar onbellegiyle yapildi; saklanan etiketler yfinance `auto_adjust=True` indirmeleriyle uretildi; kontrol grubunda uyum %83,8. Bu nedenle mutlak replay sayilari yaklasiktir; karsilastirmalar ayni onbellek icinde (ts-bazli ve sinyal-bazli) yapildi.
- Sonuc istatistikleri yalniz sinyal tarihi <= 2026-05-20 (W); tam orneklem rakamlari PRIOR.
- Gun-kumelenmis GA'da kume = sinyal tarihi; 11-46 kume; normal yaklasim ve kume bootstrap birlikte raporlandi; az kume sayisinda GA olmasi gerekenden dar olabilir.

## Alternatif aciklamalar

- Arsivin pozitif brut ortalamasi: pencere kaymasi (B11), tek gunluk olay kumelenmesi (2026-03-03: ust %1'in 26 satiri) ve barrier asimetrisi birlikte aciklayabilir; secim becerisi gerektirmez.
- Gec satir fazlaligi (B2): buyuk olcude pencere kaymasi; kalan fark (+%0,403 ve +%0,356, ayni onbellek) gurultu sinirinda.
- Capture ve negatif tarama (A5, A6): medyan doymasi ve saga carpiklik; ayni 54 gunluk ornek.
- Fixed-target (A4): yuksek oynaklik ve uzun ufukla TP'ye dokunma olasiliginin mekanik artisi.

## Cozulmemis riskler

- 2026-03-01 partisini ureten kod git'te yok; 09:00 damgali 2.065 satirin (2025-09/10) gercek yazim zamani bilinmiyor.
- Resolver `auto_adjust=True` ile ham giris/TP/SL karsilastirmasi (B11): bolunme/temettu sonrasi etiket hatasinin buyuklugu olculmedi.
- POST /scan/daily-report yol enjeksiyonu ve auth eksigi (B6): Level B duzeltme bekliyor; GET varyanti dogrulanmadi.
- Uretim env bayraklari (Alpaca, coordinator, legacy composite ranking, conviction tiers) okunamadi (.env yasak) -> B3, B4, B7 uretim etkisi NOT_MEASURABLE.
- decision-log.md:94'te "contradicted" denen RX-CAPTURE-1-ECON kaydinin hangi kismi oldugu bu rolde okunmadi.
- Brief ile artefakt arasindaki "en iyi konfigurasyon" celiskisi (A4) cozulmedi.

## Sinirlamalar

- Salt-okunur calisma; ag/HTTP, docker, scanner veya publish calistirilmadi; .env ve sirlar okunmadi; data/ altina yazilmadi.
- Faz A belgeleri satir numarasiyla okundu; artefakt JSON'lari yeniden hesaplanmadi (fixed-target JSON yalniz anahtar duzeyinde acildi).
- Replay yaklasiktir (gunluk bar, ayni-bar sirasi bilinmez, TP-once kurali resolver ile ayni).
- Onceki kosunun A1-A3 bulgulari korundu; yalniz guncel dosyaya gore satir atiflari duzeltildi.
- Hicbir sonuc OOS olarak etiketlenmedi (D7); tum getiriler brut barrier etiketidir.

## Ek: komutlar

- scripts/RT_1_extract.py -> data/RT_out_1.txt (satir numarali kod/dokuman alintilari, sema, payload anahtarlari, git pickaxe). PowerShell `>` UTF-16 yazdigi icin ayni dosya ASCII'ye donusturuldu.
- scripts/RT_2_verify.py -> data/RT_out_2.txt, data/RT_b2_groups.csv, data/RT_b11_replay.csv (`cmd /c` yonlendirmesi).
- scripts/RT_3_followup.py -> data/RT_out_3.txt.
- Git (salt-okunur): `git log --all -S` ile "INSERT INTO signals_archive", "INSERT OR IGNORE INTO signals_archive", signals_archive, signal_archive, `_kelly_reduced_cycle`; dosya bazli `git log --all --date=iso -- <yol>`; `git ls-files`; `git rev-parse HEAD`; `git status --porcelain=v1 -uall`.
- SQLite: `file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro` + `PRAGMA query_only=ON`.
- Uc script de `DONE_RT` ile bitti; KeyboardInterrupt veya yabanci cikti yok.
- git status: bu rolun yeni yollari yalniz denetim klasorunde (R10_red_team.md, scripts/RT_1..3, data/RT_out_1..3.txt, data/RT_b2_groups.csv, data/RT_b11_replay.csv); web/public/demo_snapshot.json dokunulmadi.

<!-- END -->
