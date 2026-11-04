# R4 - Formul ve Ozellik Kaydi (Formula and Feature Registry)

- Versiyon: v1
- Tarih: 2026-10-19
- Durum: DRAFT - Level A arastirma ciktisi; karar degildir
- HEAD: 93ae83c (branch review/pending-2026-10-07; kirli calisma agaci, dokunulmadi)
- Rol: Formula and Feature Registry (brief WP-3), PREFIX: FRM
- Kapsam: uretim karar yolundaki formuller (scanner/evaluate.py, scanner/features.py, scanner/score_engine.py, scanner/position_sizer.py ve yol uzerindeki yardimcilar); ilgili tests/*; data/shortlists/shortlist_202610*.csv uzerinde yalnizca betimsel korelasyon
- Girdiler: kaynak kod (7 dosya, SHA-256 Ek'te) + scanner/indicators.py, scanner/config.py; tests/ (116 .py, metin taramasi); data/shortlists/shortlist_202610*.csv (125 dosya, birlesik SHA-256 Ek'te). Ag, DB, scanner calistirma, sonuc/getiri hesabi yok.

## Ozet

- Karar yolunda 30 formul koddan kayda gecirildi (Tablo 1); 15 bulgu: P1 x1, P2 x11, P3 x3. Hicbir sonuc OOS degildir (D7); getiri/sonuc hesaplanmadi.
- F-FRM-12 (P1, MEASURED): saklanan `composite_score` degerlerinin yalniz 1734/14711'i (%11.8) varsayilan bayrak formuluyle yeniden uretilebiliyor (max fark 18 puan). Uretimdeki bayrak durumu bilinmeden skor replay'i ve ekonomik degerlendirme guvenilir yapilamaz.
- F-FRM-04 (P2): varsayilan `ranking_score` (= `legacy_quality_score`, 15114/15114) lottery/overnight cezalarini kosulsuz uyguluyor; kompozitte ayni cezalar env ile kapali. Legacy olcegi [-25, 85]; 296 satir negatif.
- F-FRM-01 (P2, REPRODUCED): volume_spike/price_momentum/trend_strength her biri +2.0 ham (+12.12 puan), yani regime ile esit agirlik; uc bayrak `MAX_RECO_SCORE` paydasinin %36.4'u (ulasilabilir tavan 16.0'a gore %37.5).
- F-FRM-10 (P2, REPRODUCED): kenet kalibi NaN'i ust sinira esliyor (`compute_recommendation_strength(nan)`=100; NaN ATR% legacy'ye +15); uretim erisilebilirligi UNRESOLVED.
- F-FRM-06 (P2): `risk_reward` uretim verisinde yalniz 3 deger aliyor (MEASURED), YZ sigma ATR carpanlariyla kullaniliyor (sentetik ATR/YZ ~1.56), `position_size` sabit 1000.
- F-FRM-11 (P2): `MAX_RECO_SCORE`=16.5 ulasilamaz; gercek tavan 16.0 -> vol rejimine gore 97/94/91.
- F-FRM-02/08/15: iki rejim carpani uyumsuz (58 vs 62); `position_size_gated` tavansiz ve tuketicisiz; `_regime_scale` Bear x1.3 yapisal olarak etkisiz.
- Normalizasyon: canli hesapta gelecek bar kullanan taban bulunmadi; z ve hacim tabanlari t'yi iceriyor, tamamlanmamis bar etkisi UNRESOLVED; bazi esik/olasilik sabitleri sonuc verisinden in-sample turetilmis.

## Kapsam ve yontem

- Statik okuma: scanner/evaluate.py (evaluate_symbol:228-756), signals.py, features.py, score_engine.py, position_sizer.py, risk_engine.py, execution_policy.py, indicators.py, config.py.
- FRM_ast_map.py: AST ile fonksiyon satir araliklari, modul sabitleri, SHA-256 ve hedefli grep (repo modulu import edilmedi).
- FRM_probe.py: (a) satir bulucu (atif yapilan satirlar diskten okundu); (b) import aninda yalniz stdlib calistiran score_engine.py, position_sizer.py, features.py, execution_policy.py dosyalari `spec_from_file_location` ile paketsiz yuklendi; signals.py, indicators.py, risk_engine.py fonksiyonlari AST ile cikarilip izole isim alaninda calistirildi; SETTINGS = config.py DEFAULT_SETTINGS (`ast.literal_eval`); (c) FINPILOT_* bayraklari surec icinde temizlendi/ayarlandi, degerleri okunmadi; (d) tohumlu sentetik veri (P5-P8); (e) shortlist CSV'leri salt-okunur, yalniz betimsel (P12).
- api.main import edilmedi; ag, DB, docker, scanner veya publish calistirilmadi; yazim yalniz denetim klasorunde.

## Bulgular

### 1. Formul kaydi (registry)

Tablo 1 - Uretim karar yolundaki formuller (koddan; satir numaralari FRM_probe.py satir bulucusu ve FRM_ast_map.py ile diskten okundu). "Testler" sutunu P11 metin taramasidir (referans, dogrulama kaniti degildir).

| ID | Konum | Tanim | Girdiler | Birim | Normalizasyon | Pencere | Eksik/NaN | Aykiri deger | Karar asamasi | Testler | Riskler | Etiket |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R01 ham `score` | evaluate.py:evaluate_symbol:281,283,285 | 1[30<=RSI<=70] + 1[V_t > 1.2*vol_med20_t] + 1[MACDh_t>0 ve MACDh_t>MACDh_t-1] | df_1d rsi, Volume, vol_med20, macd_hist | 0-3 | yok | RSI14 Wilder, median 20 (t dahil), MACD 12/26/9 | NaN karsilastirmada False; istisna -> 0 | ikili | entry kapisi (==3), kompozit x0.5, legacy 1.5*raw/3 | dogrudan yok (inline) | hacim terimi volume_spike ile ortusur | SUPPORTED |
| R02 volume_spike | signals.py:check_volume_spike:40-58 (55) | V_t > 1.5*mean(V_t-9..t), esdeger V_t > 1.588*mean(V_t-9..t-1) | Volume, vol_avg10 | bool | yok | 10 (t dahil) | NaN/KeyError/<10 bar -> False | - | filter_score + kompozit 0.5 | test_signals.py, scanner_rollout/test_threshold_activation.py | cifte sayim (F-FRM-01) | REPRODUCED (P8) |
| R03 price_momentum | signals.py:analyze_price_momentum:62-229 (157,164,211) | h in {1,3,5} herhangi birinde z_h >= esik; z_h = (r_h,t - ort)/std0, son 60 r_h (t dahil) | Close, vol_avg10 | bool | in-sample z | 60 | bos Close -> False; std<=1e-9 -> z=0 | abs(z) <= 7.68 | filter_score + kompozit 0.5 | test_signals.py, test_threshold_activation.py | coklu karsilastirma; taban t'yi iceriyor (F-FRM-09) | REPRODUCED (P7) |
| R04 etkin z-esigi | signals.py:131,204; config.py:39,46 | clip(0.6*clip(medyan_h q0.975 abs(z_hist), 1.1, 3) + 0.4*seg, 1.1, 3); seg 2.0/1.6/1.4 | vol_avg10, z gecmisi | z | dinamik yuzdelik | 60 | aday yoksa seg | kenet [1.1, 3.0] | price_momentum | test_threshold_activation.py | `momentum_z_base` 1.5 raporlaniyor, kullanilmiyor | MEASURED-sentetik (P7) |
| R05 trend_strength | signals.py:check_trend_strength:247-268 (265) | 1[(EMA50-EMA200)/EMA200*100 >= 3.0] | ema50, ema200 | bool | % | EMA 50/200 adjust=False | <200 bar veya ema200=0 -> False | - | filter_score + kompozit 0.5 | test_signals.py | ema_gap_pct'nin esiklenmis hali | MEASURED (P12) |
| R06 filter_score | evaluate.py:299 | volume_spike + price_momentum + trend_strength | R02,R03,R05 | 0-3 | yok | - | bilesenlerden | - | kompozit x1.5 | test_p0_telemetry.py (breakdown) | cifte sayim | REPRODUCED (P1) |
| R07 regime | evaluate.py:256,269 | Close_t > EMA200_t (>=200 bar), aksi Close_t > EMA50_t | df_1d | bool | yok | EMA200/50 | istisna -> False | - | core_signal kapisi, kompozit 2.0, legacy 2.0, gate/dyn girdisi | dogrudan yok | <200 barda == direction; alignment gunluk kolu ile ayni (F-FRM-07) | SUPPORTED |
| R08 direction | evaluate.py:270 | Close_t > EMA50_t | df_1d | bool | yok | EMA50 | istisna -> False | - | kapi, kompozit 2.0, legacy 2.0, momentum_score | dogrudan yok | regime ile %83.0 esit | MEASURED (P12) |
| R09 alignment_ratio | signals.py:check_timeframe_alignment:272-324 (293,308,315) | mevcut kollarin ortalamasi: Close_1h>EMA20_1h (adjust=True), Close_4h>EMA50_4h, Close_1d>EMA200_1d; en az 2 kol | 1h, 4h, 1d | 0-1 | oran | EMA20/50/200 | <2 kol veya KeyError -> 0.0 | - | kompozit x2.0 | test_signals.py, test_runtime_baseline.py, test_threshold_activation.py | gunluk kol == regime; son gun ici bar tamamlanmamis olabilir | SUPPORTED |
| R10 momentum_ratio | signals.py:check_momentum_confluence:327-386 (358,364,381) | (1/6)*[45<=RSI15m<=65, 45<=RSI4h<=65, MACDh15m>0.01, MACDh4h>0.01, RSI15m artan, MACDh4h artan] | 15m, 4h | 0-1 (1/6 adim) | yok | RSI14, MACD | eksik sutun -> 0.0 | mutlak MACD esigi | kompozit x{2.5,2.0,1.5} | test_signals.py +2 | fiyat-birimi esik (F-FRM-05) | REPRODUCED (P5) |
| R11 vol_regime | features.py:compute_vol_regime_from_df:369-390 (383) | std(r_t-19..t)*sqrt(252): <0.15 -> 0, <0.30 -> 1, aksi 2 | df_1d Close | {0,1,2} | yillik | 20 | <21 bar -> 1 | - | momentum agirligi | test_scanner_fixes.py | satirlarin %62.7'si = 2 | MEASURED (P12) |
| R12 ema_gap_pct | evaluate.py:341 | (EMA50-EMA200)/EMA200*100 | ema50, ema200 | % | yok | - | istisna -> 0.0 | - | yalniz rapor | - | R05 ile ayni buyukluk | SUPPORTED |
| R13 volume_multiple | evaluate.py:304 | V_t / vol_avg10_t (t dahil) | Volume, vol_avg10 | oran | yok | 10 | avg<=0 -> 0.0 | - | yalniz rapor | - | rvol_daily'den farkli taban (F-FRM-03) | SUPPORTED |
| R14 liquidity_ok | evaluate.py:374,380,381 | Close_t >= min_price (2.0) ve vol_avg10_t >= min_avg_vol (300000 hisse) | df_1d | bool | yok | 10 | NaN -> False; istisna -> True (fail-open, 374/380) | - | entry kapisi | dogrudan yok | hisse bazli esik (dolar degil); fail-open | SUPPORTED |
| R15 entry_ok | evaluate.py:352,360,361 (+381, 236) | regime ve direction ve score==3 ve liquidity_ok ve market_safe ve earnings_blackout degil | R01,R07,R08,R14 | bool | - | - | bilesenlerden | - | secim kapisi | dogrudan yok | `score == 3` ile `score >= 3` ozdes (maks 3) | SUPPORTED |
| R16 composite_score | score_engine.py:compute_recommendation_score:99-190 (130,140,143), compute_recommendation_strength:378-397 (393); evaluate.py:546 | round(clip(S/16.5*100, 0, 100)); S = 2reg + 2dir + 0.5raw + 1.5filter + 2align + w_vr*mom + 0.5(vs+pm+ts) [+ env kapili terimler] | R01-R11 | 0-100 tam sayi | sabit tavan 16.5 | - | NaN -> 100 (F-FRM-10) | kenet | gate/dyn girdisi, Kelly p, gosterim | test_squeeze_factor.py, test_p0_telemetry.py, test_ranking_guard.py, test_catalyst.py, test_macro_regime.py | tavan 97/94/91 (F-FRM-11); replay %11.8 (F-FRM-12) | REPRODUCED (P1), MEASURED (P12) |
| R17 score_component_breakdown | score_engine.py:253-302 (261,263) | R16 bilesenleri ayri ayri | R16 ile ayni | ham puan | - | - | - | - | telemetri | test_p0_telemetry.py, test_score_replay.py | ikinci (kopya) uygulama; fark 0.0 | REPRODUCED (P1) |
| R18 legacy_quality_score = ranking_score | score_engine.py:compute_legacy_quality_score:193-222 (211,218); evaluate.py:595,600,605 | (2reg + 2dir + 1.5*min(raw/3,1) + 1.5*min(ATR%/6,1) + 1.5*min((rvol-1)/2,1) + 0.5sq - 1.5lot - ovn)/10*100 | raw, atr_pct, rvol, sq, lot, ovn | [-25, 85] (sq ile 90) | terim kenedi | ATR14, RVOL20 | NaN terim -> ust sinir | toplam kenetsiz | varsayilan ranking (api/routers/scan.py:1026, distribution/prepublish_gate.py:37, distribution/snapshot_builder.py:108) | test_ranking_guard.py, test_scanner_contract.py | kapisiz cezalar (F-FRM-04); ATR%'yi odullendiriyor; 296 negatif satir | MEASURED (P12), REPRODUCED (P1) |
| R19 atr_pct (gunluk) | features.py:compute_atr_pct:186-206 (198) | mean(TR_t-13..t)/Close_t*100 (basit ortalama, t dahil) | H, L, C | % | - | 14 | <15 bar -> 0.0; tek NaN -> NaN | - | legacy, conviction, v2 | 0 | indicators.atr (Wilder) ile farkli tanim; NaN yayilimi | REPRODUCED (P1) |
| R20 rvol_factor / rvol_daily | features.py:compute_rvol_factor:320-339 (330); compute_rvol_daily:304-317 (311) | rvol = V_t/mean(V_t-20..t-1); factor = clip((rvol-1)/2, 0, 1) | Volume | 0-1 / oran | lineer, pivot 3.0 | 20 (t haric) | <6 bar -> 0 | kenet | legacy (rvol = 1+2*factor), v2, conviction | 0 | vol_avg10'dan farkli taban | SUPPORTED |
| R21 lottery_factor | features.py:compute_lottery_factor:446-485 (481) | 0.30*min(maks r/0.15,1) + 0.30*min(std*sqrt(252)/0.80,1) + 0.25*clip(skew/2) + 0.15*(1-min(P/50,1)), son 21 getiri | Close | 0-1 | sabit tavan | 21 | <22 bar veya istisna -> 0 | kenet | legacy -1.5 (her zaman), kompozit -2.0 (env, varsayilan kapali) | 0 | kapi tutarsizligi (F-FRM-04) | SUPPORTED |
| R22 overnight_gap_factor | features.py:compute_overnight_gap_factor:500-539 | 0.6*min(maks gap/0.08,1) + 0.4*min(ort. pozitif gap/0.04,1), son 3 gap | Open, Close | 0-1 | sabit tavan | 3 | <4 bar -> 0 | kenet | legacy -1.0 (her zaman), kompozit (env) | 0 | ayni | SUPPORTED |
| R23 squeeze_factor | features.py:compute_squeeze_factor:115-156 | w_s*min(short%/0.20,1) + w_f*max(1-float/50M,0); (0.5,0.5), ALPHA_V2 (0.7,0.3) | yfinance .info (ag) | 0-1 | pivotlar | anlik goruntu | eksik -> 0 | kenet | kompozit (env), legacy 0.5, v2, conviction | taranmadi | point-in-time degil | SUPPORTED |
| R24 conviction / `_CONV_PROB` | features.py:compute_conviction:209-237, 179; evaluate.py:571 | A: sq>=0.5 ve gap>=0.6; B: (sq>=0.5 ve atr>=4) veya nfac>=3; C: nfac>=2; prob sabit {A .73, B .59, C .52} | sq, gap, rvol, atr% | etiket + sabit | sabit esikler | - | env kapali -> ('', 0.0) | - | gosterim/siralama (scan_summary), api | test_ranking_guard.py | olasilik sabitleri in-sample (2026-06), yeniden kalibre degil; OOS degil | SUPPORTED |
| R25 regime_gate_mult -> position_size_gated | score_engine.py:regime_gate_mult:357-375; evaluate.py:549,719 | Bear: 1.3 (30<=cs<=55), 0.5 (cs>58); Bull: 0.75 (cs>58); aksi 1.0 | regime, composite | carpan | - | - | - | - | position_size_gated (tuketici bulunamadi) | test_ranking_guard.py | `_regime_scale` ile uyumsuz (F-FRM-02); tavansiz (F-FRM-08) | REPRODUCED (P2), MEASURED (P12) |
| R26 `_regime_scale` + dyn_* | position_sizer.py:32-44, 75-201 (151,160,168); evaluate.py:556 | risk = clamp(clamp(min(0.02*s, Kelly), 0.005, 0.02)*clamp(20/annvol, 0.4, 2), 0.005, 0.02); shares = min(risk$/(P-SL), 0.15*equity/P); Kelly p = 0.30+0.35*cs/100 | composite, regime, R, ann_vol | hisse | - | - | gecersiz stop -> 0 | kenetler | dashboard (web/src/app/dashboard/scanner/page.tsx:122) | 0 | boost no-op; kalibre olmayan p; equity varsayilan 10k (F-FRM-15) | REPRODUCED (P4) |
| R27 stop_loss / take_profit / risk_reward | risk_engine.py:calculate_risk_management:173-233 (212,216,217); calculate_risk_management_yz:147-170 (168); yang_zhang_vol:82-144 (109) | SL = P - m_s*sigma_YZ*C; TP = P + m_tp2*sigma_YZ*C; R = m_tp2/m_s; kademe int(momentum_score) | P (15m Close), df_1d OHLC | fiyat / oran | - | YZ 20(+1), t dahil | hata -> sigma = 0.01*Close | - | cikti; R -> Kelly | 0 | YZ ~ ATR/1.56; R yalniz 3 deger (F-FRM-06) | MEASURED (P12), REPRODUCED (P6) |
| R28 momentum_score (risk kademesi) | evaluate.py:389,392,394 | 0.4*clip((RSI-30)/70*100, 0, 100) + 30*1[MACDh>0] + 30*direction | rsi, macd_hist, direction | 0-100 | - | - | istisna -> 50 | kenet | risk kademesi | 0 (inline) | entry satirlarinda [60, 82.9]; kademe yalniz RSI>=47.5 | REPRODUCED (replika, P6) |
| R29 position_cap / position_size | execution_policy.py:position_cap:95-113 (8,112); evaluate.py:614,671,709 | notional = min(1000*P, 0.005*dollar_ADV20); position_size = notional/P | ADV (Close*Volume 20, t dahil) | hisse / $ | - | 20 | ADV yok -> tavansiz + uyari | - | cikti | test_execution_gateway.py, test_prepublish_gate.py, test_ranking_guard.py, test_scanner_contract.py | position_size_gated tavansiz | REPRODUCED (P10) |
| R30 v2_score (golge) | score_engine.py:compute_v2_score:225-235 | round(30*gap + 30*rvol + 25*min(ATR%/4,1) + 15*sq), 0-100 | gap, rvol, atr%, sq | 0-100 | sabit pivot | - | - | kenet | golge strateji skoru | taranmadi | - | SUPPORTED |

Not: `extension_factor` (features.py:342-366) hesaplanip telemetriye yaziliyor ama hicbir skora girmiyor (F-FRM-13); karar yolunda olmadigi icin tabloda yok.

<!-- REG-APPEND -->

### 2. Dogruluk problari (brief 7.2)

**F-FRM-02 - Iki farkli rejim carpani (regime_gate_mult ve _regime_scale) farkli esiklerle iki farkli boyut alanina uygulaniyor**

- Oncelik: P2 (boyutlandirma; herhangi bir degisiklik Level C)
- Konum: scanner/score_engine.py:regime_gate_mult:357-375 (`_HIGH_SCORE_THRESH`@351=58, `_BEAR_SUPPRESS_MULT`@353=0.5, `_BULL_SUPPRESS_MULT`@354=0.75); scanner/position_sizer.py:_regime_scale:32-44 (sabit 62, Bear-suppress yok; cagri position_sizer.py:158); scanner/evaluate.py:549 (`_gate_mult = regime_gate_mult(bool(regime), _composite_score)`)
- Veri kaynagi: kaynak kod (SHA-256 Ek'te)
- Yontem: statik okuma; esik taramasi probe'u (P-tablosu)
- Sonuc: `regime_gate_mult` -> `position_size_gated`; `_regime_scale` -> `dyn_*` alanlari. Faz 5b esik dusurmesi (62->58) yalniz score_engine'de uygulanmis. Bull ve kompozit 59-62: gate 0.75 / dyn 1.0; Bear ve kompozit >62: gate 0.5 / dyn 1.0. `regime` girdisi sembolun kendi gunluk Close > EMA200 (200 bar yoksa EMA50) karsilastirmasi; docstring "market regime" diyor. `entry_ok`, `core_signal` uzerinden `regime=True` gerektirdiginden iki fonksiyonun Bear dallari yalniz `entry_ok=False` satirlarda calisabilir.
- n: N/A
- Etiket: SUPPORTED
- Sinirlamalar: tuketici taramasi (P11) yalniz api, core, distribution, web/src; P2: 46/202 (cs, rejim) kombinasyonu farkli; P12: gate 0.75 x609 vs dyn 0.75 x305 (304 satir farkli), gate 0.5 hic gorulmedi; `position_size_gated` icin tuketici bulunamadi (F-FRM-08).
- Alternatif aciklama: iki alanin farkli tuketicileri icin bilincli ayrisma olabilir; gerekce belgesi bulunamadi.
- Sonraki adim: tuketici envanteri; tek esik kaynagi karari (Level C).
- Onerilen kategori: FIX_CANDIDATE (insan karari gerekli)

**F-FRM-04 - lottery/overnight cezalari kompozitte env ile kapali, varsayilan ranking'de (legacy_quality_score) kosulsuz acik**

- Oncelik: P2 (varsayilan `ranking_score`'u dogrudan etkiler)
- Konum: scanner/score_engine.py:compute_legacy_quality_score:193-222 (`- 1.5 * lottery - overnight`, kapi yok); scanner/score_engine.py:compute_recommendation_score:99-190 (`_lottery_enabled`:61-62, `_overnight_enabled`:72-73 kapili); scanner/features.py:compute_lottery_factor:446-485, compute_overnight_gap_factor:500-539 (icsel env kapisi yok); scanner/evaluate.py:595 (`_legacy_quality_score = ...`), :605 (`_ranking_score = ...`, FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=1 degilse legacy)
- Veri kaynagi: kaynak kod
- Yontem: statik okuma; uc deger probe'u (P-tablosu)
- Sonuc: evaluate.py iki faktoru her taramada hesaplayip legacy skora geciyor. "default OFF" olarak belgelenen lottery (en fazla 15 puan) ve overnight (en fazla 10 puan) cezalari varsayilan `ranking_score`'da etkin, `composite_score`'da env kapaliyken yok. Legacy skor docstring'i "0-100 scale" diyor; formul geregi aralik [-25, 85] (squeeze acikken ust 90).
- n: N/A
- Etiket: SUPPORTED (statik) + REPRODUCED (P1: aralik [-25, 85], squeeze ile 90) + MEASURED (P12: ranking_score == legacy_quality_score 15114/15114; 296/15114 satir negatif, min -8.317, maks 76.359)
- Sinirlamalar: decision-log'da legacy cezalarina dair ayrik karar olup olmadigi bu rolde aranmadi.
- Alternatif aciklama: legacy skorda cezalarin bilincli kalici olmasi; score_engine yorumlari bunu belirtmiyor.
- Sonraki adim: decision-log taramasi; kapi semantigini belgele veya hizala (Level B).
- Onerilen kategori: FIX_CANDIDATE

**F-FRM-05 - check_momentum_confluence MACD esigi mutlak fiyat biriminde (0.01)**

- Oncelik: P2
- Konum: scanner/signals.py:check_momentum_confluence:327-386 (`macd_15m > 0.01`, `macd_4h > 0.01`)
- Veri kaynagi: kaynak kod; sentetik probe
- Yontem: statik okuma + olcek probe'u (P-tablosu)
- Sonuc: MACD histogrami fiyat biriminde; sabit 0.01 olcek-bagimli. 6 kriterin 2'si fiyat seviyesine bagli; kompozitte en fazla 2.5*2/6 = 0.83 ham puan (5.1 kompozit puan).
- n: N/A
- Etiket: REPRODUCED (P5 sentetik: ayni goreli yol, >0.01 gecme orani fiyat 2/10/50/250 icin 0.000/0.191/0.456/0.507; >0 orani her seviyede 0.527)
- Sinirlamalar: uretim dagiliminda kriterin fiyat seviyesine gore gecme orani olculmedi (15m/4h veri bu rolde okunmadi).
- Alternatif aciklama: 0.01 tasarimda "pozitiften belirgin" esigi olarak secilmis olabilir; belge yok.
- Sonraki adim: MACD/Close gibi goreli esik ile ablation (Level B).
- Onerilen kategori: FIX_CANDIDATE

**F-FRM-06 - risk_reward sembole ozgu bilgi tasimiyor; YZ sigma ATR carpanlariyla kullaniliyor; position_size sabit 1000**

- Oncelik: P2 (R-katlarina dayali ekonomik degerlendirme yapilirsa P1 adayi)
- Konum: scanner/risk_engine.py:calculate_risk_management:173-233 (`position_size = 1000` satir 217); calculate_risk_management_yz:147-170; yang_zhang_vol:82-144; scanner/evaluate.py:evaluate_symbol:228-756 (`momentum_score` blogu)
- Veri kaynagi: kaynak kod; sentetik probe
- Yontem: statik okuma + sentetik GBM probe'u (P-tablosu)
- Sonuc: (a) risk_reward = tp2_mult/stop_mult: Sniper 5.0/1.5=3.33, Normal 5.5/2.0=2.75, Defansif 6.5/2.5=2.60 (FINPILOT_ENABLE_ALPHA_V2=1 iken 3.33/3.67/4.33); sembol verisinden bagimsiz. (b) entry_ok satirlarinda direction=True ve macd_hist>0 zorunlu oldugundan momentum_score = 0.4*rsi_score + 60 ve RSI [30,70] icin [60, 82.9]; Defansif kademe ulasilamaz, kademe yalniz RSI >= 47.5 ile belirlenir. (c) `calculate_risk_management_yz` gunluk YZ sigma*Close'u ATR yerine ayni carpanlarla kullaniyor (docstring: "multipliers mirror the ATR version"); ATR/sigma orani probe'da. (d) `position_size` her sembol icin sabit 1000.
- n: N/A
- Etiket: SUPPORTED; (a) MEASURED (P12 n=14711: risk_reward yalniz 3 deger: 4.33 x11421, 3.33 x3185, 3.67 x105 = ALPHA_V2 kumesi); (c) MEASURED-sentetik (P6: ATR/YZ medyan 1.558, p10 1.459, p90 1.674, n=240; stop% YZ 2.76/3.69/4.61 vs ATR 4.55/6.06/7.58)
- Sinirlamalar: uretim cikti dosyalarinda stop mesafesi dagilimi bu rolde olculmedi.
- Alternatif aciklama: daha dar stop bilincli bir tercih olabilir (Alpha-v2 yorumu "SIKI stop" der); ancak docstring esdegerlik iddia ediyor.
- Sonraki adim: ATR ve YZ tabanli stop mesafelerini ayni gelistirme verisinde karsilastir.
- Onerilen kategori: RESEARCH_NEXT

**P-tablosu - offline problar (FRM_probe.py; saf fonksiyonlar standalone dosya yukleme veya AST cikarimi ile; scanner paketi import edilmedi; env bayraklari surec icinde temizlendi)**

| Probe | Test edilen | Yontem | Sonuc | n | Etiket |
|---|---|---|---|---|---|
| P1 | kompozit efektif agirlik, tavan, breakdown==score, NaN | score_engine.py standalone; sentetik satirlar | bayrak basina +2.0 ham / +12.12 kompozit puan; regime, direction, alignment(1.0) ayni 2.0; ham skor puani 0.5 (3.03 puan); momentum(1.0) 2.5/2.0/1.5; tum-maks satir 16.0/15.5/15.0 ham -> 97/94/91; breakdown total - score max fark 0.0 (16 bayrak kombinasyonu); `compute_recommendation_strength(nan)`=100; legacy(atr_pct=nan)=70.0 vs 55.0; `compute_atr_pct` tek NaN High -> NaN | 2400 | REPRODUCED |
| P2 | `regime_gate_mult` vs `_regime_scale` | cs 0..100 x bull/bear | 46/202 farkli: bull cs 59-62 (gate 0.75 / dyn 1.0), bear cs 59-100 (gate 0.5 / dyn 1.0) | 202 | REPRODUCED |
| P4 | `_regime_scale` etkisi | grid (cs, R, ann_vol, kelly, rejim), P=50, SL=48; bellekte `_regime_scale`=1.0 karsiti | Bear x1.3 bolgesi 0/240 degisti; Bull x0.75 bolgesi 0/320 degisti (bu gridde %15 notional tavani bagliyor); Kelly 48/1680 noktada bagliyor | 1680 | REPRODUCED (grid) |
| P5 | MACD 0.01 mutlak esik | ayni sentetik 15m yolu 4 fiyat seviyesinde | >0.01 orani 0.000/0.191/0.456/0.507 (fiyat 2/10/50/250); >0 orani her seviyede 0.527 | 550 bar x4 | REPRODUCED (sentetik) |
| P6 | YZ sigma vs Wilder ATR; R | sentetik GBM (gun ici 78 adim, sigma %2, gece %0.5), 300 gun | ATR/YZ medyan 1.558 (p10 1.459, p90 1.674); stop% YZ 2.76/3.69/4.61 vs ATR 4.55/6.06/7.58 (Sniper/Normal/Defansif); R 3.33/2.75/2.60, ALPHA_V2 3.33/3.67/4.33; position_size 1000; momentum_score replikasi RSI 47.4->69, 47.5->70 | 240 | MEASURED (sentetik) |
| P7 | z-skor siniri ve null gecme orani | `analyze_price_momentum` AST cikarimi, config.py DEFAULT_SETTINGS | %50 sicrama: z 7.392 (t-haric taban 26.77; sinir sqrt(59)=7.681); null rastgele yuruyus any-horizon 0.040/0.070/0.078 vs yalniz h=1 0.013/0.033/0.043 (yuksek/orta/dusuk likidite); etkin esik medyani 2.064/1.914/1.819 | 400/segment | MEASURED (sentetik) |
| P8 | hacim esikleri | `check_volume_spike` + indicators.py:177-178 replikasi | spike esigi onceki-9 ortalamanin 1.5882 kati (analitik 1.5*9/8.5); ham skor hacim esigi 1.2x medyan (sabit taban); `compute_rvol_factor`>0 esigi 1.0x | analitik | REPRODUCED |
| P10 | conviction ve ADV tavani | features/execution_policy standalone | `_CONV_PROB` sabit {A .73, B .59, C .52}; ADV 2e6, talep 1000x50 -> cap 10000 -> position_size 200; position_size_gated 500/750/1000/1300 (tavansiz) | ornek | REPRODUCED |
| P11 | tuketici ve test referanslari | metin taramasi | bkz. F-FRM-08, F-FRM-14 | - | MEASURED (metin) |
| P12 | saklanan bilesenler | data/shortlists/shortlist_202610*.csv | bkz. bolum 3 tablo ve F-FRM-12 | 15114 | MEASURED |

**F-FRM-08 - position_size_gated ADV tavanini atliyor ve tuketicisi bulunamadi; regime_gate_mult ciktisi fiilen kullanilmiyor**

- Oncelik: P3
- Konum: scanner/evaluate.py:549 (gate), :614 (`_position_cap = position_cap(`), :671 (`"position_size": risk_data["position_size"]`), :709 (`**_position_cap,` ayni anahtari ezer), :719 (`"position_size_gated": int(`); scanner/execution_policy.py:position_cap:95-113 (satir 112), `MAX_POSITION_ADV_FRACTION`@8=0.005; scanner/risk_engine.py:217 (`position_size = 1000`)
- Veri kaynagi: kaynak kod; P12 shortlist verisi
- Yontem: statik okuma; P10 ornegi; P11 metin taramasi (api, core, distribution, web/src)
- Sonuc: cikistaki `position_size` ADV tavanli (talep 1000*P, tavan %0.5*dollar_ADV); `position_size_gated` tavansiz 1000*gate_mult (ornek: 200 vs 1300'e kadar). `position_size_gated`, `regime_gate_mult` ve `exit_profile(` icin 0 tuketici; `dyn_shares`/`dyn_risk_pct` yalniz web/src/app/dashboard/scanner/page.tsx:122,124,330,331. Uretim verisinde gate 0.5 hic gorulmedi (1.0 x13746, 0.75 x609, 1.3 x356), `dyn_regime_scale` 0.75 x305: 304 satirda gate 0.75 iken dyn 1.0. `EXIT_PROFILES["legacy_quality"]` (execution_policy.py:12; tp 2.0 ATR, sl 1.0 ATR, 5 bar) risk_engine stop/TP carpanlarindan farkli ikinci bir cikis tanimi.
- n: 14711 (dagilim)
- Etiket: REPRODUCED (tavan ornegi) + MEASURED (dagilim) + SUPPORTED (tuketici yoklugu; scripts/ ve research/ taranmadi)
- Sinirlamalar: harici CSV/rapor tuketicileri taranmadi.
- Alternatif aciklama: alan harici analiz icin tutuluyor olabilir.
- Sonraki adim: tuketici yoksa alanin kaldirilmasi veya tavanin uygulanmasi; hangi cikis tanimi degerlendirmede esas alinacak karari (Level C).
- Onerilen kategori: REMOVE_CANDIDATE

**F-FRM-10 - NaN girdiler skor kenetlerinde ust sinira esleniyor (NaN -> 100 kompozit; NaN ATR% -> +15 legacy)**

- Oncelik: P2 (uretimde erisilebilir oldugu dogrulanirsa P0)
- Konum: scanner/score_engine.py:compute_recommendation_strength:378-397 (satir 393), compute_legacy_quality_score:193-222 (`normalized`:206-209); scanner/features.py:compute_atr_pct:186-206 (satir 198)
- Veri kaynagi: sentetik girdiler
- Yontem: P1
- Sonuc: Python'da `min(100.0, nan)` ilk argumani dondurur; `max(lo, min(hi, x))` kalibi NaN'i ust sinira esler ve istisna dogmadigi icin `except` bloklari devreye girmez. `compute_recommendation_strength(nan)`=100; momentum_ratio=nan satiri=100. `compute_atr_pct` son 14 barda tek NaN High ile NaN donduruyor (docstring "Veri yoksa 0.0"); legacy skor 55.0 -> 70.0 (tam ATR kredisi). Ayni kalip squeeze/lottery/overnight kenetlerinde de var (NaN -> 1.0).
- n: sentetik
- Etiket: REPRODUCED (saf fonksiyon); uretim erisilebilirligi UNRESOLVED
- Sinirlamalar: data_fetcher'in df_1d NaN temizligi bu rolde dogrulanmadi.
- Alternatif aciklama: upstream dropna NaN'i her zaman temizliyor olabilir.
- Sonraki adim: data_fetcher NaN yolunu dogrula; kenetlere `math.isfinite` korumasi (Level B).
- Onerilen kategori: FIX_CANDIDATE

**F-FRM-12 - Saklanan composite_score varsayilan bayrak formuluyle yeniden uretilemiyor (%11.8 eslesme)**

- Oncelik: P1 (ekonomik degerlendirme engeli: skor replay'i uretimdeki bayrak/formul durumunu bilmeyi gerektiriyor)
- Konum: scanner/score_engine.py:compute_recommendation_score:99-190 (env kapili terimler); scanner/evaluate.py:546
- Veri kaynagi: data/shortlists/shortlist_202610*.csv, 125 dosya; dosya hash'lerinin birlesik SHA-256'si d2923591baa28e277496d29c2d2426e6e0ab6e98402648ff1e9c0296b7bdd1fc; dosya bazli SHA-256: data/FRM_shortlist_schema.csv
- Yontem: P12; saklanan bilesenlerden (regime, direction, score, filter_score, alignment_ratio, momentum_ratio, uc bayrak, vol_regime) env bayraklari kapaliyken `compute_recommendation_strength` hesaplandi, saklanan `composite_score` ile karsilastirildi (abs fark < 0.5)
- Sonuc: 1734/14711 (%11.8) eslesti; max abs fark 18.0 puan (~3.0 ham puan; ornegin lottery 2.0 + overnight 1.0 veya squeeze 1.5 + catalyst 1.5 ile tutarli). Saklanan risk_reward'in yalniz ALPHA_V2 kumesinde olmasi (F-FRM-06) ve 16 satirda conviction tier bulunmasi (C x9, B x7) en az bazi env bayraklarinin uretim taramalarinda acik oldugunu destekliyor. Ciktida alignment/momentum oranlari 2 ondalik yuvarli (etki < 0.5 puan).
- n: 14711 (21105 ham satir; (symbol,timestamp) tekillestirme sonrasi 15114; bilesenleri tam 14711)
- Etiket: MEASURED (uyumsuzluk); neden UNRESOLVED
- Sinirlamalar: uretim env durumu okunmadi (secrets kurali); ayni sembol ardisik taramalarda tekrar ediyor; satir secim kurali bilinmiyor; sonuc/getiri kullanilmadi; D7 geregi OOS degil.
- Alternatif aciklama: sentiment terimi (+-0.5) veya donem icinde formul degisikligi.
- Sonraki adim: satir bazinda `score_feature_flags` ve `score_component_breakdown` telemetri alanlari ile farki bilesenlere ayir.
- Onerilen kategori: NEEDS_MORE_DATA

**F-FRM-14 - Karar yolundaki bircok saf formulun dogrudan test referansi yok**

- Oncelik: P2
- Konum: tests/ (116 .py dosyasi)
- Veri kaynagi: test kaynak metni
- Yontem: P11 substring taramasi
- Sonuc: 0 test dosyasi referansi: `calculate_dynamic_position`, `_regime_scale`, `calculate_risk_management_yz`, `yang_zhang_vol`, `compute_lottery_factor`, `compute_overnight_gap_factor`, `compute_rvol_factor`, `compute_atr_pct`. Bunlardan lottery, overnight, atr_pct ve rvol_factor varsayilan `ranking_score`'u (legacy) besliyor; risk/boyut fonksiyonlari stop/TP/R ve `dyn_*` alanlarini uretiyor. `regime_gate_mult` 1, `compute_recommendation_strength` 1, `compute_legacy_quality_score` 2 dosyada geciyor.
- n: 116 dosya
- Etiket: MEASURED (metin taramasi; referans, kapsam veya dogruluk kaniti degildir)
- Sinirlamalar: `evaluate_symbol` uzerinden dolayli testler sayilmadi.
- Alternatif aciklama: entegrasyon testleri bu fonksiyonlari dolayli kapsiyor olabilir.
- Sonraki adim: saf fonksiyonlar icin sinir/NaN birim testleri (Level A test yazimi).
- Onerilen kategori: FIX_CANDIDATE

**F-FRM-15 - _regime_scale Bear x1.3 artisi yapisal olarak etkisiz; Kelly girdileri kalibre degil**

- Oncelik: P3 (boyutlandirma; degisiklik Level C)
- Konum: scanner/position_sizer.py:_regime_scale:32-44 (satir 40), calculate_dynamic_position:75-201 (satir 151 `win_rate = _clamp(0.30 ...`, satir 160 `adjusted_risk_pct = min(base_risk_pct * reg_scale, kelly_sz)` ve ardindan [0.005, 0.02] kenedi, satir 168 vol_scale); `DEFAULT_KELLY_FRAC`@25=0.25; scanner/evaluate.py:230,763 (`kelly_fraction: float = 0.5`)
- Veri kaynagi: kaynak kod; P4 grid
- Yontem: P4 + aritmetik
- Sonuc: evaluate.py `portfolio_current_risk_pct` gecmedigi icin base_risk_pct=0.02; s=1.3 icin min(0.026, k) ardindan 0.02 tavanina kenetleme, her k icin s=1.0 ile ayni sonucu verir (P4: 0/240). Bull x0.75 yalniz %2 risk tavani, vol_scale ve %15 notional tavani baglamadiginda etkili (P4 gridinde 0/320; elle aritmetik: P=50, SL=45, ann_vol=40, cs=70 bull -> 20 vs 15 hisse). Kelly p = 0.30 + 0.35*cs/100 sabit esleme ("based on historical data" disinda kanit yok); avg_win_r sabit R (F-FRM-06). `DEFAULT_KELLY_FRAC` yorumu "half-Kelly" diyor (0.25 ceyrek); evaluate 0.5 geciyor.
- n: 1680 (grid)
- Etiket: REPRODUCED (grid) + SUPPORTED (genel aritmetik)
- Sinirlamalar: gercek stop/vol dagiliminda Bull bastirmanin etkin oldugu satir orani olculmedi.
- Alternatif aciklama: boost bilincli olarak tavanla sinirlanmis olabilir.
- Sonraki adim: etkisiz terimi kaldirma veya belgeleme karari (Level C).
- Onerilen kategori: REMOVE_CANDIDATE

<!-- PROBE-APPEND -->

### 3. Fazlalik / cifte sayim (brief 7.3)

**F-FRM-01 - volume_spike / price_momentum / trend_strength kompozitte iki kez sayiliyor**

- Oncelik: P2 (model kalitesi)
- Konum: scanner/evaluate.py:evaluate_symbol:228-756 (`filter_score = int(volume_spike) + int(price_momentum) + int(trend_strength)`); scanner/score_engine.py:compute_recommendation_score:99-190; scanner/score_engine.py:score_component_breakdown:253-302; `MAX_RECO_SCORE`@24 (yorum blogu iki terimi de listeliyor)
- Veri kaynagi: kaynak kod (score_engine.py sha256 9455d5205eb476261373700a71252062b44f85f209ebb1d693fc677151ba4a3f)
- Yontem: statik okuma + offline probe (FRM_probe.py, bkz. bolum 2 P-tablosu)
- Sonuc: her bayrak `filter_score*1.5` uzerinden 1.5 + dogrudan 0.5 = 2.0 ham puan katiyor. `MAX_RECO_SCORE=16.5` paydasiyla her bayrak 12.12 kompozit puan; uc bayrak birlikte 6.0/16.5 = %36.4. Bu, `regime` (2.0) ve `direction` (2.0) ile ayni agirlik demek. Ayrica ham `score` icindeki hacim kontrolu (Volume > 1.2*vol_med20) `volume_spike` ile ayni gunluk hacim serisinden turuyor (ucuncu hacim terimi).
- n: N/A (formul aritmetigi)
- Etiket: REPRODUCED (P1: her bayrak +2.0 ham / +12.12 kompozit puan; P12 n=14711: filter_score ile rho volume_spike 0.444, price_momentum 0.310, trend_strength 0.806)
- Sinirlamalar: agirliklarin bilincli secilip secilmedigine dair kod disi gerekce (karar kaydi) bu rolde okunmadi.
- Alternatif aciklama: ek 0.5 terimleri bilincli bir "onay bonusu" olabilir; yine de dokumante edilmis bir ablation yok.
- Sonraki adim: kilitli olmayan gelistirme verisinde bayrak-bazli marjinal katki ablation'i (RESEARCH_NEXT); agirlik degisikligi Level B.
- Onerilen kategori: RESEARCH_NEXT

**F-FRM-07 - Trend ailesi ayni gunluk Close'tan; alignment'in gunluk kolu == regime; <200 barda regime == direction**

- Oncelik: P2
- Konum: scanner/evaluate.py:evaluate_symbol:228-756 (Stage 1: `regime = c_daily > e200_daily`, 200 bar yoksa e200 yerine ema50; `direction = c_daily > e50_daily`); scanner/signals.py:check_timeframe_alignment:272-324 (gunluk kol: Close > ema200, len>=200); scanner/signals.py:check_trend_strength:247-268 ((ema50-ema200)/ema200*100 >= trend_gap_pct)
- Veri kaynagi: kaynak kod
- Yontem: statik okuma
- Sonuc: 200+ barda alignment'in gunluk kolu birebir `regime`; `regime` dogrudan 2.0 + alignment uzerinden 2.0/3 = 0.67 (4h kolu yoksa 1.0) ham puan alir. 50-199 barda `regime` ve `direction` ayni karsilastirma (Close > ema50) -> 4.0 ham puan tek kosuldan. `trend_strength`, `ema_gap_pct` ile ayni buyukluk (yalniz esiklenmis). 1h kolu `ewm(span=20)` (adjust=True varsayilan), diger EMA'lar adjust=False (indicators.py:ema).
- n: 14711 (P12): regime~direction rho 0.639 (esit %83.0), regime~alignment_ratio 0.753, trend_strength~ema_gap_pct 0.828 (esik uyumu 14702/14711)
- Etiket: SUPPORTED
- Sinirlamalar: 4h/1h kollarinin gercek mevcudiyet orani olculmedi.
- Alternatif aciklama: cok-zaman-dilimi onayi bilincli tekrar olabilir.
- Sonraki adim: regime/direction/trend_strength/alignment icin ortak bilesen analizi (gelistirme verisi).
- Onerilen kategori: RESEARCH_NEXT

**Tablo 3a - Saklanan bilesenler arasi betimsel Spearman korelasyonlari (P12)**

Veri: data/shortlists/shortlist_202610*.csv, 125 dosya (121 dosya 119 sutun, 4 dosya 113 sutun; 0 bozuk satir; 33 bilesen sutununun hepsi mevcut), birlesik SHA-256 d2923591baa28e277496d29c2d2426e6e0ab6e98402648ff1e9c0296b7bdd1fc; 21105 ham satir, (symbol,timestamp) tekillestirme sonrasi 15114. Satir sirasi kullanilmadi. Tam matris: data/FRM_shortlist_corr.csv. Sonuc/getiri sutunu kullanilmadi; ayni sembol tekrarlari nedeniyle gozlemler bagimsiz degil; D7 geregi OOS degil.

| Cift | rho | n |
|---|---|---|
| volume_spike ~ filter_score | 0.444 | 14711 |
| price_momentum ~ filter_score | 0.310 | 14711 |
| trend_strength ~ filter_score | 0.806 | 14711 |
| trend_strength ~ ema_gap_pct | 0.828 | 14711 |
| regime ~ direction | 0.639 | 14711 |
| regime ~ alignment_ratio | 0.753 | 14711 |
| direction ~ alignment_ratio | 0.585 | 14711 |
| volume_spike ~ volume_multiple | 0.516 | 14711 |
| volume_spike ~ score (ham) | 0.273 | 14711 |
| price_momentum ~ momentum_best_zscore | 0.378 | 14711 |
| composite_score ~ legacy_quality_score | 0.888 | 15114 |
| ranking_score ~ legacy_quality_score | 1.000 | 15114 |
| composite_score ~ filter_score | 0.725 | 14711 |
| composite_score ~ momentum_ratio | 0.291 | 14711 |
| legacy_quality_score ~ lottery_factor | -0.032 | 14711 |
| legacy_quality_score ~ rvol_daily | 0.261 | 14711 |
| alignment_ratio ~ momentum_ratio | 0.275 | 14711 |
| vol_regime ~ composite_score | -0.161 | 14711 |

Betimsel ek (P12, MEASURED): filter_score dagilimi 0 x8080, 1 x5918, 2 x675, 3 x38; ham score 0 x1893, 1 x7573, 2 x4847, 3 x801; regime == direction 12214/14711 (%83.0); trend_strength == 1[ema_gap_pct >= 3] 14702/14711; filter_score == bayrak toplami 14711/14711; vol_regime 2 x9222, 1 x4454, 0 x1035. Yorum: filter_score varyansinin buyuk kismi trend_strength ile ortak (rho 0.806); trend ailesi (regime, direction, alignment, trend_strength) belirgin ortak bilesen tasiyor.

**F-FRM-13 - extension_factor hesaplaniyor ama hicbir skorda kullanilmiyor; belge iddiasi kodla celisiyor**

- Oncelik: P3
- Konum: scanner/features.py:compute_extension_factor:342-366 (docstring: "so score_engine SUBTRACTS this"); features.py `_GAP_PIVOT`@166 ustundeki yorum ("Consumed by score_engine only when FINPILOT_ENABLE_ALPHA_V2=1"); scanner/evaluate.py:519-543 (`_score_input` icinde `extension_factor`, `gap_factor`, `rvol_factor`); scanner/score_engine.py tamami (398 satir) okundu
- Veri kaynagi: kaynak kod
- Yontem: statik okuma
- Sonuc: score_engine.py'de `extension_factor`, `gap_factor`, `rvol_factor` anahtarlari ve ALPHA_V2 referansi yok. extension_factor composite, legacy, v2 ve conviction'in hicbirine girmiyor; yalniz telemetri `score_input`'una yaziliyor. gap/rvol yalniz legacy (rvol), v2 ve conviction'a giriyor.
- n: N/A
- Etiket: CONTRADICTED (docstring/yorum iddiasi)
- Sinirlamalar: harici arastirma betikleri bu alani kullaniyor olabilir (taranmadi).
- Alternatif aciklama: planlanmis ama baglanmamis ozellik.
- Sonraki adim: belge duzeltme veya ozelligin kaldirilmasi (Level B).
- Onerilen kategori: REMOVE_CANDIDATE

<!-- RED-APPEND -->

### 4. Normalizasyon (brief 7.4)

**F-FRM-03 - Hacim tabanlari (vol_med20, vol_avg10) mevcut bari iceriyor; RVOL faktorleri icermiyor**

- Oncelik: P2
- Konum: scanner/indicators.py:177 (`df["vol_med20"] = vol.rolling(20).median()`), scanner/indicators.py:178 (`df["vol_avg10"] = vol.rolling(10).mean()`); karsit: scanner/features.py:compute_rvol_daily:304-317 (satir 311, `iloc[-21:-1]`), scanner/features.py:compute_rvol_factor:320-339 (satir 330, `iloc[-21:-1]`)
- Veri kaynagi: kaynak kod (features.py sha256 2ce4f067785d43f32214678c85dde57a8f11341889e04886abcc5f221c88c2f6)
- Yontem: FRM_ast_map.py grep ciktisi + read_file
- Sonuc: ham `score` hacim kontrolu V_t > 1.2*median(V_{t-19..t}), `volume_multiple` = V_t/mean(V_{t-9..t}) ve likidite kapisi `vol_avg10` mevcut bari payda/tabana dahil ediyor; `compute_rvol_factor`/`compute_rvol_daily` ise haric tutuyor. Ayni kavram (goreli hacim) iki farkli taban tanimiyla uretiliyor. Ortalama tabaninda V_t dahil edilince oran r -> 10r/(9+r) seklinde sikisir (r=2 iken 1.82). Look-ahead degil (V_t karar aninda biliniyor), fakat gunluk bar tamamlanmamissa V_t kismi olur.
- n: N/A
- Etiket: SUPPORTED (statik) + REPRODUCED (P8: volume_spike esigi onceki-9 ortalamanin 1.5882 kati; ham skor hacim esigi 1.2x medyan; rvol_factor esigi 1.0x); tamamlanmamis bar etkisi UNRESOLVED (scanner/ ve core/ altinda devam eden gunluk bari dusuren kod grep ile bulunamadi; tarama zamanlamasi bu rolde olculmedi)
- Alternatif aciklama: taramalar yalniz seans kapanisindan sonra calisiyorsa kismi bar sorunu pratikte olusmaz (`evaluate_symbols_parallel` instrumentation'a `scan_basis="EOD"` geciyor).
- Sonraki adim: tarama zaman damgalarini (scan_runs/feature_timestamps) seans saatleriyle karsilastir; taban tanimlarini tek yardimciya bagla.
- Onerilen kategori: FIX_CANDIDATE (taban birligi), NEEDS_MORE_DATA (kismi bar)

**F-FRM-09 - Momentum z-skoru tabani mevcut gozlemi iceriyor; ufuklar arasi "any" kurali**

- Oncelik: P2
- Konum: scanner/signals.py:analyze_price_momentum:62-229 (`momentum_series = close.pct_change(horizon).dropna()`, `recent_window = momentum_series.tail(baseline_window)`, `std(ddof=0)`, `positive = any(z >= z_threshold)`)
- Veri kaynagi: kaynak kod; sentetik probe
- Yontem: statik okuma + probe (P-tablosu)
- Sonuc: r_t, kendi ortalama/std tabaninin son elemani. Bu (i) |z| <= sqrt(W-1) ust sinirini getirir (Samuelson esitsizligi), (ii) buyuk sokta z'yi sikistirir, (iii) h>1 icin ust uste binen getiri serisi tabanin etkin orneklemini dusurur. Look-ahead degil (tum veriler t anina kadar). `price_momentum`, varsayilan ufuklardan herhangi birinde z >= esik ise True: coklu karsilastirma.
- n: N/A
- Etiket: REPRODUCED (P7: %50 sicramada z 7.392, t-haric taban ile 26.77, sinir sqrt(59)=7.681) + MEASURED-sentetik (P7 null rastgele yuruyus, n=400/segment: any-horizon orani 0.040/0.070/0.078 vs yalniz h=1 0.013/0.033/0.043)
- Sinirlamalar: etkin SETTINGS degerleri (pencere/esik/ufuk) config.py'den okundu, calisma zamani override'i olculmedi.
- Alternatif aciklama: dahil etme bilincli bir "shrinkage" olabilir; belge yok.
- Sonraki adim: t-haric taban ile ayni gelistirme verisinde bayrak gecme oranlarini karsilastir.
- Onerilen kategori: RESEARCH_NEXT

**Tablo 4a - Karar yolunda fiilen kullanilan normalizasyonlar**

| Normalizasyon | Konum | Taban / pencere | t dahil mi | Karar aninda mevcut mu | Not |
|---|---|---|---|---|---|
| Momentum z-skoru | signals.py:157,164 | son 60 h-ufuk getirisi, ddof=0 | evet | evet | abs(z) <= 7.68 (F-FRM-09) |
| Dinamik z-esigi | signals.py:analyze_price_momentum:62-229 (satir 204 kenet); config.py:39 | abs(z_hist) q0.975, 60 pencere, alpha 0.6, kenet [1.1, 3.0] | evet | evet | ayni pencere icinde z |
| Likidite segment esigi | signals.py:131; config.py:46 | vol_avg10 (hisse): >=1M yuksek 2.0, <=300k dusuk 1.4, aksi 1.6 | evet | evet | segment varken `momentum_z_base`=1.5 raporlaniyor ama kullanilmiyor |
| Hacim median/ortalama | indicators.py:177-178 | 20 median / 10 ortalama | evet | evet (kismi bar riski) | F-FRM-03 |
| RVOL | features.py:311, 330 | 20 ortalama | hayir | evet | |
| Kompozit 0-100 | score_engine.py:393 | sabit tavan 16.5 | - | - | ulasilabilir tavan 16.0 (F-FRM-11) |
| Legacy terimleri | score_engine.py:206-209, 211, 218 | sabit pivotlar (raw/3, ATR%/6, (rvol-1)/2), terim kenedi | - | - | toplam kenetlenmiyor: [-25, 85] (squeeze ile 90) |
| v2 terimleri | score_engine.py:compute_v2_score:225-235 | sabit pivotlar, 0-100 kenet | - | - | golge skor |
| Lottery / overnight / gap / extension | features.py:446-485, 500-539, 240-263, 342-366 | sabit tavanlar (%15 maks getiri, %80 vol, skew 2, $50; %8 gap; %5 gap; 0.90 52h) | evet | evet | |
| vol_regime | features.py:383 | 20g std*sqrt(252); 0.15/0.30 | evet | evet | |
| YZ sigma | risk_engine.py:109 | 20(+1) bar | evet | evet | ATR yerine kullaniliyor (F-FRM-06) |
| ADV | evaluate.py:_feature_contract:155-225 | Close*Volume son 20 (dropna) | evet | evet | |
| Yuzdelik sira | features.py:_percentile_rank:549-557 | contraction/rvol_acceleration | - | - | evaluate_symbol importlarinda yok; karar yolunda degil |

Sonuc: canli hesapta gelecek bar kullanan bir taban bulunmadi (tum pencereler t'de bitiyor; `shift(-k)` yok). Karar aninda mevcut olmayan bilgi riski uc noktada: (i) gunluk bar tamamlanmamissa V_t/H/L/C kismi (UNRESOLVED); (ii) `compute_squeeze_factor` yfinance `.info` anlik goruntusu, as-of tarihi yok (replay/backtest'te point-in-time degil; SUPPORTED); (iii) `_CONV_PROB` (features.py:179) ve `regime_gate_mult` esikleri (score_engine.py:347-354 sabitleri ve hemen ustundeki yorum blogu, "n=4 066 resolved signals") sonuc verisinden turetilmis sabitler; bu verilerle ortusen donemlerde degerlendirme in-sample olur (D7 ile tutarli: OOS degil).

**F-FRM-11 - MAX_RECO_SCORE=16.5 ulasilamaz; gercek tavan 16.0 ve vol rejimine gore 97/94/91**

- Oncelik: P2
- Konum: scanner/score_engine.py:24 (`MAX_RECO_SCORE`, yorum 16-23), :140 (`mom_weight`), :393 (strength), `_HIGH_SCORE_THRESH`@351
- Veri kaynagi: kaynak kod; P12 verisi
- Yontem: P1 + yorum aritmetigi
- Sonuc: yorumdaki toplam 2+2+1.5+4.5+2+2.5+0.5+0.5+0.5 = 16.0 (16.5 degil). Tum-maks satir vol_regime 0/1/2 icin 16.0/15.5/15.0 ham -> 97/94/91; 100 ulasilamaz. Uretim verisinde composite_score maks 89, satirlarin %62.7'si vol_regime=2 (tavan 91). Ayni kosul farkli vol rejimlerinde farkli puan verir; esik tabanli kararlar (`regime_gate_mult` 58) vol rejimine gore farkli yuzdelik kesimlere denk gelir.
- n: 15114 (maks), sentetik (tavan)
- Etiket: REPRODUCED (P1) + MEASURED (P12)
- Sinirlamalar: esik kaymasinin karar etkisi olculmedi.
- Alternatif aciklama: 0.5 fark eski bir terimden (yorumda gecen is_premium_symbol donemi) kalmis olabilir; belge yok.
- Sonraki adim: tavan ve esik belgelerini hizala (Level B; esik degisikligi boyutu etkiler).
- Onerilen kategori: FIX_CANDIDATE

<!-- NORM-APPEND -->

## Dogru calisan kisimlar

- `score_component_breakdown` toplami `compute_recommendation_score` ile birebir (max fark 0.0; 2400 vaka, 16 bayrak kombinasyonu) - REPRODUCED - KEEP_AS_IS.
- `filter_score` == bayrak toplami 14711/14711; `trend_strength` == 1[ema_gap_pct >= 3] 14702/14711 - MEASURED - KEEP_AS_IS.
- `ranking_score` == `legacy_quality_score` 15114/15114; varsayilan ranking yontemi kodla tutarli - MEASURED.
- indicators.py: RSI Wilder (ewm alpha=1/14, adjust=False), MACD 12/26/9, ATR Wilder (satir 113), EMA adjust=False; pencereler t'de bitiyor, `shift(-k)` yok - SUPPORTED - DO_NOT_CHANGE.
- RVOL tabanlari mevcut bari haric tutuyor (features.py:311, 330) - SUPPORTED - KEEP_AS_IS (diger hacim tabanlari icin referans).
- `analyze_price_momentum` std<=1e-9 ve bos seri korumalari, esik kenedi [1.1, 3.0] - SUPPORTED.
- `compute_vol_regime_from_df` sicak yolda ag cagrisi yapmiyor (features.py:369-390) - SUPPORTED.
- `position_cap` ADV yokken sifir-doldurma yapmiyor, None + uyari donuyor (execution_policy.py:95-113) - SUPPORTED - KEEP_AS_IS.
- `_feature_contract` ozellik zaman damgasi ve yasini kaydediyor (evaluate.py:155-225); point-in-time denetimi icin uygun - KEEP_AS_IS.

## Cevaplanamayan sorular

1. Uretim taramalarinda hangi FINPILOT_ENABLE_* bayraklari acikti (F-FRM-12, F-FRM-06)? Env okunmadi - UNRESOLVED.
2. Taramalar tamamlanmis gunluk bar uzerinde mi calisiyor (F-FRM-03)? Tarama zaman damgalari ile seans takvimi karsilastirilmadi - UNRESOLVED.
3. `get_setting` uzerinden `min_price`/`min_avg_vol` etkin degerleri (core.config yolu import edilmedi) - UNRESOLVED.
4. df_1d'de NaN High/Low/Close uretimde olusuyor mu (F-FRM-10)? - UNRESOLVED.
5. `position_size_gated`, `regime_gate_mult`, `exit_profile` icin scripts/ veya research/ tuketicisi var mi? - UNRESOLVED.
6. Bilesenlerin ekonomik katkisi / marjinal lift - NOT_MEASURABLE bu rolde (sonuc hesaplanmadi; D7).
7. `_CONV_PROB` ve Kelly p eslemesinin kalibrasyonu - NOT_MEASURABLE (kilitli olmayan sonuc verisi ve OOS tasarimi gerekir).
8. 2026-06-12 barrier audit esikleri sembol rejimiyle mi piyasa rejimiyle mi turetildi? Rapor okunmadi - UNRESOLVED.

## Sinirlamalar

- Statik okuma ve sentetik problar; sentetik sonuclar uretim dagilimini temsil etmez.
- evaluate_symbol icindeki inline formuller (momentum_score kademesi, hacim tabanlari) replika ile probe edildi; replikalar kaynak satirlarindan kuruldu ama uygulamadan sapabilir.
- Shortlist CSV'leri: satir secim kurali bilinmiyor; ayni sembol tekrarlari; korelasyonlar betimsel, bagimsizlik varsayilmadi; sonuc/getiri kullanilmadi; D7 geregi OOS degil.
- Test taramasi substring tabanli; tuketici taramasi api, core, distribution, web/src ile sinirli.
- signals.SETTINGS icin DEFAULT_SETTINGS varsayildi; calisma zamaninda `apply_aggressive_mode` degerleri degistirebilir.
- FRM_ast_map.py test-tarama bolumu KeyboardInterrupt ile kesildi (def/sabit/SHA/grep ciktisi tamdi); test taramasi FRM_probe.py P11'de tekrarlandi.
- P4 grid tek stop mesafesiyle (%4) sinirli; Bull bastirmanin gercek etkisi stop/vol dagilimina bagli.
- Diger ajanlar dosyalari eszamanli degistirebilir; analiz anindaki kod SHA-256'lari asagida. indicators.py ve config.py icin SHA-256 hesaplanmadi.

## Ek: komutlar

1. `& 'C:\Users\meric\AppData\Local\Programs\Python\Python312\python.exe' -B 'C:\Users\meric\Borsa\reports\scanner_intelligence_audit_v1_2026-10-19\scripts\FRM_ast_map.py'` (cikis 1: test-tarama bolumunde KeyboardInterrupt; onceki cikti tam)
2. `& 'C:\Users\meric\AppData\Local\Programs\Python\Python312\python.exe' -B 'C:\Users\meric\Borsa\reports\scanner_intelligence_audit_v1_2026-10-19\scripts\FRM_probe.py' 2>&1 | Out-String -Width 400` (46.3 s) -> data/FRM_probe_results.json, data/FRM_shortlist_corr.csv, data/FRM_shortlist_schema.csv
3. `git -C C:\Users\meric\Borsa status --porcelain=v1 -uall` (son kontrol)
4. read_file okumalari: scanner/evaluate.py 1-1000; scanner/score_engine.py 1-480; scanner/features.py 1-420, 430-540; scanner/position_sizer.py 1-140, 138-201; scanner/signals.py 1-390; scanner/risk_engine.py 76-233; scanner/indicators.py 1-180; scanner/execution_policy.py 1-118; scanner/config.py 1-100.

| Dosya | SHA-256 (analiz ani) |
|---|---|
| scanner/evaluate.py | 0eb9446d8a7a9509722ac5ccff6944b415ca864dcf680b1a7dbfcb7972651b3d |
| scanner/signals.py | a158efaf4379f5047becf921721ea7aa466798a0fcc3201b12756efac4bc34a4 |
| scanner/features.py | 2ce4f067785d43f32214678c85dde57a8f11341889e04886abcc5f221c88c2f6 |
| scanner/score_engine.py | 9455d5205eb476261373700a71252062b44f85f209ebb1d693fc677151ba4a3f |
| scanner/position_sizer.py | f4a60e9cb632f74fa27446849cbbaaa8147bf5687838cb575c818ecce049c304 |
| scanner/risk_engine.py | c6719f2779ac65e5ee0dc42d38fdae2599cf859b4d6ccb32cc59d32ebdf44cd9 |
| scanner/execution_policy.py | d1597fcdb0c0c526adb0414e962773ce1cb46de154b1b1da7a328d3cb302b6a9 |
| data/shortlists/shortlist_202610*.csv (125 dosya, hash birlesimi) | d2923591baa28e277496d29c2d2426e6e0ab6e98402648ff1e9c0296b7bdd1fc |

<!-- END -->
