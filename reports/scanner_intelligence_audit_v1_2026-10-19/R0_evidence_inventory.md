# R0 - Arastirma Kanit Envanteri (Research Evidence Inventory)

- Surum: v1
- Tarih: 2026-10-19
- Durum: DRAFT - Level A arastirma ciktisi; karar degildir
- Tamamlanma: COMPLETE (kapsam sinirli; 4 backbone envanter yalniz tablo-satiri grep'i ile tarandi, "fixed_target 2026-08-11" raporu bulunmadi - bkz. Sinirlamalar)
- HEAD: 93ae83c (branch review/pending-2026-10-07); calisma agaci kirli, dokunulmadi
- Rol: Research Evidence Inventory (WP-0 evidence trail; brief bolum 2.1-2.3), PREFIX `EVI`
- Kapsam: (1) bolum 2.1 sayisal iddialarinin kaynak izi; (2) onceki arastirma durum tablosu; (3) bolum 2.2 sorunlarinin izi; (4) kilitli / on-kayitli deney kayit defteri
- Girdiler: `data/finpilot.db` (salt-okunur, `mode=ro` + `PRAGMA query_only=ON`), bu klasordeki `data/EVI_01_archive_provenance.json`, `data/EVI_02_payload_universe.json`, onceki rapor basliklari/ozetleri ve `docs/governance/decision-log.md` girdileri (asagida tek tek atifli)

## Ozet

- Brief 2.1'in alti sayisal iddiasi (5,206 sinyal; ortalama +0.398424%; medyan -0.64315%; top-1% haric +0.189646%; top-5% haric -0.161478%; top-1% = 52) bugunku `data/finpilot.db` (SHA-256 `b64c0c52...f5f6`) uzerinde REPRODUCED (EVI_01, EVI_03). Tanim: `resolved_status_barrier` win/loss satirlari, getiri = saklanan brut `resolved_pct_barrier`; net degil, expectancy degil.
- "48'i iki islem gununde" CONTRADICTED (EVI-F01): iki tarih arsive yazilma (`ts`) tarihleri, biri Pazar (2026-03-01); `signal_date`'e gore 52 satir 9 tarihe dagiliyor (en buyukleri 27 / 10 / 9). Ayni ifade DL:67'de "signal dates" olarak da gecmis.
- "~1,800 Nasdaq evreni" kismen CONTRADICTED (EVI-F02): preset birlesimi 1,812 sembol, NASDAQ 1,504 / NYSE 270 / AMEX 37 / ARCA 1; arsiv 1,017 sembol; point-in-time evren kaydi bulunmadi.
- Arsivde uretim siralamasi yeniden kurulamaz (EVI-F03): `finpilot_score` tamamen NULL, `score` 65 degerli ve 5,132/5,206 satir gun-ici esit.
- "Locked OOS: NOT_OPENED" ifadeleri (MRI, RGA:158) DL:79/103/105, RGA:64 ve D7 ile CONTRADICTED (EVI-F04); D7'ye gore mevcut hicbir set OOS degil.
- B2 tablosunda 41 arastirma satiri: yon tahmini, H2, H4, NS-1, TP/SL grid, high-RVOL vb. kapali/reddedilmis; acik kalanlar B2-1 (LOCK BLOCKED), B3 (WAITING_FOR_DATA), H1-H3, fade teyidi, funnel shadow, tarama Faz 1/3 canli olcumu. RX-CAPTURE-1-ECON kilit kaydi PRIOR olarak celisik (DL:79).
- B4 kayit defterinde 19 kalem; kilitli veri acilmadi, kilitli bolumde sonuc hesaplanmadi.

<!-- OZET-END -->

## Kapsam ve yontem

- Salt-okunur envanter. SQLite yalniz `file:...finpilot.db?mode=ro` + `PRAGMA query_only=ON`; ag/provider cagrisi, docker, tarama, yayin script'i yok. Yazilan dosyalar yalniz bu rapor, `scripts/EVI_03_verify.py` ve `data/EVI_03_verify.json` (EVI_01/02 onceki turdan, yeniden kosulmadi).
- EVI_03 yalniz daha once yayinlanmis agregatlari ve metadata sayimlarini (tarih, haftanin gunu, kaynak model, skor tekilligi) yeniden hesaplar; yeni getiri bolmesi yapmaz. Kilitli/holdout bolumlerde hicbir sonuc hesaplanmadi.
- Onceki bulgular PRIOR olarak atiflidir (dosya:satir; satirlar `read_file` veya grep ciktisinda okundu). B2'deki "kanit seviyesi" bu rolun yargisidir; onceki raporlarin etiketleri tirnak icindedir. D7 (DL:46) geregi hicbir sonuc OOS olarak etiketlenmez.
- Kisaltmalar: MRI = `reports/MASTER_RESEARCH_INVENTORY_2026-09-10.md`; RGA = `reports/research_governance_audit_2026-09-23.md`; DL = `docs/governance/decision-log.md`; ODB / OTS / OLC = B1'de tanimli outlier raporlari.

<!-- YONTEM-END -->

## Bulgular

### B1. Bolum 2.1 iddialari - provenance tablosu

Kaynak kisaltmalari (PRIOR, satirlar grep ciktisinda okundu): ODB = `reports/outlier_dependence_audit_v1_2026-10-14/outlier_dependence_baseline.md`; OTS = `reports/outlier_dependence_audit_v1_2026-10-14/top_1pct_top_5pct_sensitivity.md`; OLC = `reports/outlier_dependence_audit_v1_2026-10-14/liquidity_and_cost_sensitivity.md`. Bu calisma: EVI_01 = `data/EVI_01_archive_provenance.json` (2026-10-19T10:22Z), EVI_02 = `data/EVI_02_payload_universe.json` (10:23Z), EVI_03 = `data/EVI_03_verify.json` (10:30Z, `scripts/EVI_03_verify.py`).

Ortak tanim: birim = `signals_archive` satiri, `resolved_status_barrier` IN (`resolved_win`, `resolved_loss`) ve `resolved_pct_barrier` NOT NULL (ODB:12; EVI_03 ayni filtre). Getiri = `resolved_pct_barrier`: sinyal basina saklanan brut bariyer getirisi; kazancta take_profit/entry - 1, kayipta stop_loss/entry - 1 (ODB:13; EVI_01 `decided_barrier_formula_check` 5,206/5,206 satir 0.05 pp icinde). Maliyet dusulmemis; net degil; expectancy degil. `ts` araligi 2025-09-12..2026-05-22 (EVI_01). Veri: `data/finpilot.db` SHA-256 `b64c0c5262e0d685daa1309e6293d27c208f64a6fc213b3c00e3cb896bd5f5f6`, 7,811,072 bayt; EVI_01 ve EVI_03 anlarinda ayni hash.

| # | Iddia (brief 2.1) | PRIOR kaynak | Bu calismadaki deger (kaynak) | Etiket | Celiski / not |
|---|---|---|---|---|---|
| 1 | 5,206 sinyal | ODB:12, ODB:20 | 5,206 (EVI_01 `n_decided`; EVI_03 `n_decided_barrier`) | REPRODUCED | Tanima duyarli: `resolved_status` IN (win, loss) ile 5,452 satir (EVI_03); tablo toplami 5,748; `resolved_status_barrier` NULL 532 (EVI_01). `ts` ayina gore dagilim: 2025-09 1,579; 2025-10 474; 2025-11 6; 2025-12 6; 2026-01/02 0; 2026-03 2,495; 2026-04 177; 2026-05 469 (EVI_01). |
| 2 | ~1,800 sembollu Nasdaq evreni | Bu iddia icin sayisal PRIOR kaynak bu calismada bulunmadi; en yakin artefakt `web/public/stock_presets.json` (SHA-256 `4e300c194d2d87129af2abd45c7ae5793ae684f32f497d8280a068fa02529e36`, mtime 2026-06-10) | preset birlesimi 1,812 sembol (EVI_01, EVI_02); `symbols` tablosuna gore NASDAQ 1,504, NYSE 270, AMEX 37, ARCA 1 (EVI_02); `symbol_lists` preset_1500 1,449 + iwm_300m 366 (EVI_02). Karar verilmis arsiv: 1,017 farkli sembol, 953'u preset birlesiminde (EVI_01) | CONTRADICTED (kismen) | Evren tek borsa degil. Karar satirlarinin borsa dagilimi: NASDAQ 3,657; NYSE 1,236; ARCA 257; `symbols`'ta yok 51; AMEX 4; OTC 1 (EVI_02). Sinyal anindaki (point-in-time) evren kaydi bulunmadi; preset dosyasi arsiv doneminden sonra degismis (EVI-F02). |
| 3 | Ortalama brut ~ +0.40% | OTS:15 (+0.3984%); OLC:64, OLC:71 | +0.398424% (EVI_01, EVI_03) | REPRODUCED | 0.20 pp sabit maliyet varsayimiyla +0.1984% (PRIOR OLC:65). 575/5,206 (%11.0) sonuc saklanan gunluk fiyatlarla yeniden uretilemiyor; denenen hicbir konvansiyon tum satirlari uretmiyor (PRIOR ODB:56-57). |
| 4 | Medyan ~ -0.64% | ODB:25 (-0.6431%); OTS:15 | -0.64315% (EVI_01, EVI_03) | REPRODUCED | Iki-degerli bariyer yapisi; isabet orani 0.3006, ort. kazanc +4.2825, ort. kayip -1.2711 (EVI_01). |
| 5 | Top-1% cikarilinca ~ +0.19% | OTS:16 (+0.1896%, n=5,154) | +0.189646%, n=5,154, k=52 (EVI_03); kesim degeri +13.2075 (EVI_01) | REPRODUCED | Tanim: `resolved_pct_barrier` azalan sirada ilk floor(0.01 x 5,206) = 52 satir (ODB:63); cikarilanlarin tamami kazanc (EVI_01). |
| 6 | Top-5% cikarilinca ~ -0.16% | OTS:17 (-0.1615%, n=4,946) | -0.161478%, n=4,946, k=260 (EVI_03); kesim +6.3477 (EVI_01) | REPRODUCED | Ayni tanim (ODB:64); medyan -0.6799 (EVI_03). |
| 7 | Top 1% = 52 sinyal; 48'i iki islem gununde | ODB:63 (k=52) | `ts` tarihine gore 2026-03-03 (Tue) 27 + 2026-03-01 (Sun) 21 = 48 (EVI_03 `top1_ts_dates`); payload `signal_date`'e gore 2026-03-03 27, 2026-02-12 10, 2026-02-17 9, diger 6 tarih 1'er (EVI_03 `top1_signal_dates`) | 52 ve 48: REPRODUCED (`ts` bazinda); "iki islem gunu": CONTRADICTED | 2026-03-01 Pazar; bu satirlarda `ts` islem gunu degil arsive yazilma zamani (EVI-F01). Top-1% kaynak modeli: scanner_v1 48, scanner_v2 2, scanner_import 1, scanner_shortlist 1 (EVI_03). Ayni iki `ts` tarihi tum karar satirlarinin %46.5'ini (2,421) tasiyor; top-1%'te pay %92.3 (EVI_03). |

<!-- B1-END -->

### B2. Onceki arastirma durum tablosu (bolum 2.3)

Kaynak kisaltmalari (PRIOR): MRI = `reports/MASTER_RESEARCH_INVENTORY_2026-09-10.md` (okunan satirlar 1-215); DL = `docs/governance/decision-log.md` (satirlar grep ile okundu). "Kanit seviyesi" bu rolun yargisidir; onceki raporlarin kendi etiketleri ayrica tirnak icinde verilir. "Tekrar" sutunu: script ve girdinin varligi bu turda dogrulandiysa "var", dogrulanmadiysa "kontrol edilmedi".

| Tema | Research ID / artefakt | Soru | Yontem / veri | Sonuc (PRIOR) | Kanit seviyesi | Tekrar | Sinirlama | Sonraki adim |
|---|---|---|---|---|---|---|---|---|
| Baseline reconstruction | `full_baseline_reconstruction_compression_forensics_2026-09-09.md` | Gecmis uretim siralamasi yeniden kurulabilir mi? | Forensik; tarihsel export'lar | "NOT_FULLY_RECONSTRUCTED historically; FORWARD CAPTURE ENABLED"; 6 ara girdi persist edilmiyordu (MRI s.1 tablo, s.3 madde 5) | SUPPORTED (bu calismanin EVI-F03 arsiv olcumu ile tutarli) | kontrol edilmedi | Tarihsel multi-TF OHLCV kayip (MRI s.6) | B3 spec'e gore ileriye donuk kayit birikimi |
| Baseline reconstruction | `research/b3_b4_baseline_validation_spec_2026_09_11.md` (B3/B4) | Baseline dogrulama metodolojisi | Dondurulmus spec | "SPEC REGISTERED 2026-09-11 (BLOCKED_BY_B2)" (MRI s.4) | UNRESOLVED (calistirilmadi) | kontrol edilmedi | B2 cesitlilik esigi tanimsiz ("keyfi yeterli threshold'u YOK", MRI s.4) | B2 birikim kriterinin insanca tanimlanmasi |
| Score/ranking | `baseline_ranking_health_2026-09-09.md` | composite_score siralamasi rastgeleden iyi mi? | Kantil/rank analizi | "FAILED (PROVISIONAL)"; Q1 > Q5 ters iliski, Agustos'ta kararsiz (MRI s.1, s.3 madde 4) | HYPOTHESIS (provisional; reconstruction eksik) | kontrol edilmedi | Baseline uretim durumu eksikken uretildi (MRI s.3 madde 6) | B3/B4 sonrasi yeniden test |
| Score/ranking | Compression bulgusu (baseline health + forensics) | Skor cozunurlugu yeterli mi? | Tekil deger / tie sayimi | 90 unique / 40k satir, %99.78 tie, gun-ici medyan cozunurluk ~%6; skor yalniz son ~57 gunde tanimli; composite ~ dist_52w_high ~0.64 (MRI s.3 madde 1-3) | SUPPORTED (arsivde benzer: EVI-F03) | kontrol edilmedi | Farkli veri seti (40k satir) - bu calismanin 5,206 satiriyla ayni degil | Resmi uretim siralama tanimi (DEFINITION_REQUIRED) |
| Score/ranking | RESEARCH-X H2 (`research_x_h2_score_direction_2026-09-21.md` + prereg) | Skor yonu getiriyle iliskili mi? | On-kayitli split-sample | "H2a NOT_SUPPORTED; H2b secondary directional; H2c mixed; H2d DEFERRED" (MRI s.1) | HYPOTHESIS (tanimlayici) | kontrol edilmedi | Tarihsel split; uretim skoru degil | H2d ertelenmis kalem |
| Score/ranking | RESEARCH-X H4A / H4B / H4C | Cozunurluk sikismasi; siralama eslemesi; bilgi kaybi | H4B forensik + deterministik rerun; H4C on-kayit | H4A: resmi uretim siralama cozunurlugu "DEFINITION_REQUIRED" (MRI s.3 madde 7). H4B: "ranking guard 8 passed ... deterministic rerun confirmed" (DL:1252). H4C: "NOT_STARTED -> PREREG_LOCKED" (DL:1239) | H4B: SUPPORTED (eslemeye dair); H4C: UNRESOLVED | H4B: script+json DL:1252'de listeli, bu turda varligi kontrol edilmedi | Hicbir verdict uretim siralamasi hakkinda degil (DL:1239) | H4C kosum durumunu raporundan dogrulamak |
| Flag instrumentation / B2 | GATE B1 / GATE B2 (`gate_b1_live_instrumentation_2026_09_09.md`, `gate_b2_manual_2026_09_09.md`) | Canli skor/rank birebir yakalanabiliyor mu? | Canli yol instrumentation | B1 "PASS" 8/8 exact; B2 "PASS-WITH-WARNINGS" 24 gozlem, tek gun, 8 sembol (MRI s.2 madde 10-11, s.4) | SUPPORTED (yakalama dogrulugu icin); karlilik icin NOT_MEASURABLE | kontrol edilmedi | Cok kucuk orneklem; B2 birikimi "devam ediyor" | B2 -> surekli instrumentation karari (MRI s.5 #5, bekliyor) |
| Flags / ablation | `meta_validation_audit_2026-09-08.md`, `scoring_ablation_audit_2026-09-08.md`, `walk_forward_scoring_validation_2026-09-08.md` | 9 flag skoru/getiriyi etkiliyor mu? | Meta-validation, ablation, walk-forward | Flag'ler skoru %83.5 degistiriyor, getiriyi tahmin etmiyor; hicbir komponent KEEP degil; walk-forward 0/3 (MRI s.1, s.2 madde 3-5) | HYPOTHESIS (baseline provisional iken uretildi, MRI s.3 madde 6) | kontrol edilmedi | "OOS" etiketi D7 sonrasi gecersiz (bkz. B4) | Flag karari "DEFERRED/BLOCKED BY BASELINE FAILURE" (DL:1871) |
| Entry/exit | `hgen_h3_fade_2026-09-03.md` (opening-range fade) | Acilis araligi fade kurali | Kesif verisi (698 gozlem, DL:1936) | "CONFIRMATORY_CANDIDATE" %59.9 brut, gun-kumelenmis, %1 maliyette negatif (MRI s.1) | HYPOTHESIS | kontrol edilmedi | Cherry-pick riski "HIGH" (DL:1936) | Yeni veriyle tek-atis teyit (MRI s.5 #4) |
| Regime | `experiment_review_board_exp1_2026-09-03.md` (H1 Regime x Tier) | Rejim x kademe getiri farki | Review board | "FAIL/STOP" (MRI s.2 Donem 4) | SUPPORTED (red icin) | kontrol edilmedi | - | KEEP_AS_IS (kapali) |
| Rejected hypotheses | Direction prediction (`direction_context_battery_2026-09-03.md`, `direction_threshold_matrix_2026-09-03.md`) | Yon tahmini mumkun mu? | 8+ yontem | "KILL" (MRI s.1) | SUPPORTED (red icin) | kontrol edilmedi | Ayni tarihsel veri ailesi | Yeniden acilmamali (DO_NOT_CHANGE) |
| Data coverage | Catalyst factor (`catalyst_refresh_2026-09-03.md`) | Catalyst verisi kullanilabilir mi? | EDGAR cache dolumu | "UNVALIDATED - DATA-UNAVAILABLE" (cache regrese) (MRI s.1) | UNRESOLVED | kontrol edilmedi | Dual-writer regresyonu (MRI s.5 #2) | Cache onarimi karari bekliyor |
| Data coverage / leakage | `c2c_5d_label_entry_basis_2026-09-03.md` | c2c_5d etiket butunlugu | EOD-only + `label_entry_basis` | "SOLVED" (MRI s.1) | SUPPORTED | kontrol edilmedi | - | KEEP_AS_IS |
| Descriptive | `attention_map_research_2026-08-14.md` | Olagandisi davranis haritasi | 5 ay tanimlayici | "VALIDATED-DESCRIPTIVE-RESEARCH" lift 1.7-3.3x, predictive degil (MRI s.1) | SUPPORTED (yalniz tanimlayici) | kontrol edilmedi | Yon/getiri iddiasi yok | ANS-1 on-kayit onerisi (DL:1783) |
| Proposed, not implemented | MRI s.5 bekleyen kararlar | - | - | Flag karari; catalyst cache; FinSense loop; fade teyidi; B2 -> surekli instrumentation; compression cozumu (float skor / tie-breaking) "Hipotez" (MRI s.5) | UNRESOLVED (karar bekliyor) | - | Level B/C | Insan karari |
| Scanner performance profiling | `reports/scan_performance_audit_2026-10-18.md` + `research/scan_performance_audit_2026_10_18.py` | Tarama neden uzun? | Offline JSONL analizi; `data/distribution/scan_timing.jsonl` SHA-256 `008c66b0...16b9` (DL:8) | 416 tamamlanmis 200-sembol kaydi: medyan `total_s` 321.38 s, p95 534.99 s; 5 satirlik kohortta `prefetch.repair` medyan 305.025 s, ratio-of-medians %90.61; tam evren uctan uca "NOT MEASURED" (DL:9-10) | SUPPORTED (200-sembol partileri icin); tam evren NOT_MEASURABLE (henuz) | script + snapshot hash DL'de; varligi kontrol edilmedi | Asama kirilimi yalniz 5 satir; 411 vs 416 uzlasmamis; Sep 23 notunda medyan/ortalama karisikligi (DL:10) | Canli Faz 1/3 olcumu insan onayi bekliyor |
| Scanner performance profiling | `research/scanner_perf_baseline_2026_10_17.py` (Faz 0) | Fallback sayisi sureyle iliskili mi? | 411 parti, gozlemsel | Medyan toplam 318 s; parti basina medyan 60 yfinance fallback; r=0.48 (n=411, gozlemsel) (DL:22) | HYPOTHESIS (nedensel degil) | kontrol edilmedi | API bellek %98.65 iken canli olcum yapilmadi (DL:23) | Izole kosum (Faz 1) |
| Funnel recall | `research/funnel_recall_retest_2026_10_16.py` (Block 2.0) | On-filtre top-K adaylari kaciriyor mu? | 25 gun canli shortlist birlesimi | filter_score ile %40 genislik: top-25 ve top-50 recall %100; filter_score olmadan %40: %100 / %98, %30: %84 (DL:35) | HYPOTHESIS (in-sample, iyimser; DL:36) | kontrol edilmedi | Populasyon dogrulanmis 1,812 evren degil; zaman/maliyet olculmedi | Shadow mode (Block 2.2) insan karari |
| Funnel recall | `research/funnel_recall_test_2026_09_23.py`, `research/funnel_overlap_test_2026_09_23.py` (DL:894) | Gunluk-only on-filtre tam skorun ilk-50'sini yakalar mi? | `full_universe_enriched_eod_only.csv`, 57 gun, 40,014 satir, gun basi medyan 860 sembol (DL:895) | ilk-N ortusme: ilk-10 %20, ilk-25 %32, ilk-50 %41; rastgeleye gore 6.8x-16x; sinirda tie yogunlugu %0.4-1.0 (DL:903-905); recall@K: %10 -> %62, %20 -> %76, %30 -> %90, %40 -> %98, %50 -> %100 (DL:909); hiz projeksiyonu "ESTIMATED" (DL:913-917) | HYPOTHESIS (in-sample; projeksiyon olcum degil; projeksiyondaki 274.6 s DL:10'a gore medyan degil ortalama) | DL'de script adlari; varligi kontrol edilmedi | 10-16 retest farkli populasyon (canli shortlist birlesimi, 25 gun) | Shadow mode (Block 2.2) |
| Outlier / ekonomik | `reports/outlier_dependence_audit_v1_2026-10-14/` | Sonuc uc degerlere bagli mi? | Arsiv + onbellek gunluk bar replay | +0.40 / -0.64 / +0.19 / -0.16 (B1); top-5% isaretli getiri toplaminin %138.5'i (DL:67 "net sum" ifadesi; toplanan degerler brut); replay 4,631/5,206 eslesme; giris = sinyal gunu kapanisi, ertesi acilis medyan +2.0% (top-1%) / +4.0% (top-5%) yukarida; gap-aware cikista eslesen satir ort. +0.44% -> -0.06% (DL:67) | REPRODUCED (B1 alti satir); diger kalemler SUPPORTED (PRIOR) | EVI_03 ile ana agregatlar yeniden uretildi | Zaman dilimi dogrulanmamis; spread/intraday veri yok (DL:67) | EVI-F01 tarih yorumu duzeltmesi |
| Cost/slippage | `reports/net_expectancy_audit_v1_2026-10-14/` | Net beklenti olculebilir mi? | `distribution/karne.py` `_overall_from_archive` reproduksiyonu | +0.3984% brut bariyer etiketi; net beklenti "not measurable"; `alpaca_orders` 11 emir 0 fill; maliyet konvansiyonlari 0-100 bps arasi celisiyor; `resolved_pct_t5` -96%..+11,991% (DL:91) | SUPPORTED; `resolved_pct_t5` araligi REPRODUCED (EVI_01: min -96.2144, max 11990.9096, n=5,213) | kontrol edilmedi | DB o gun kilitli, snapshot hash yok (DL:93) | Maliyet konvansiyonu karari (insan) |
| OOS / leakage | `reports/oos_independence_audit_v1_2026-10-14/` | Hicbir OOS seti dondurulmus muydu? | Hash + kronoloji | Dogrulanabilir dondurma yok; 2026-05-21 siniri ve sonuclari ayni artefaktta (2026-07-15) ilk kez; PIT holdout kendinden zaman damgali, git-ignored; `LockedHoldoutGuard` hicbir runner tarafindan cagrilmiyor; RX-CAPTURE-1-ECON kilit kaydi celisik (DL:79) | SUPPORTED (PRIOR; bu turda yeniden dogrulanmadi) | kontrol edilmedi | Erisim logu yok (DL:79) | EVI-F04; D7 prospektif tanim |
| OOS / leakage | OOS usage audit (DL:99-110) | Temiz tarihsel holdout var mi? | Rapor/artefakt taramasi | En az 6 OOS siniri; 2026-01-01 sonrasi her pencere en az bir artefaktta degerlendirilmis; fixed-target kurali 2026-08-06'da, 2026-08-05 raporundan sonra commit edilmis (DL:103-105) | SUPPORTED (PRIOR) | - | Script-script kosum denetimi degil (DL:106) | D7 sonrasi prospektif kayit |
| OOS / governance | D7 insan karari (DL:42-50) | OOS tanimi | Insan karari | Mevcut setler (2026-05-21 locked OOS ve PIT holdout dahil) OOS sayilmaz; sayisal esikler veri olusmadan konmaz (DL:46) | Karar (kanit degil) | - | Uygulama NOT_EXECUTED (DL:50) | Prospektif protokolun yazilmasi |
| Proposed, not implemented | Pozisyon tavani celiskisi (DL:67) | Hedef pozisyon buyuklugu nedir? | Kod okumasi (PRIOR) | `scanner/position_sizer.py` %15 vs `core/config.py` 0.2; arastirma notional 1,000 USD; buyukluk tanimsiz | UNRESOLVED (bu turda kod okunmadi) | - | Insan karari bekliyor | Level C (pozisyon buyuklugu) |
| Score/ranking | RESEARCH-X H4C sonucu / H4D-measure / H4A | Kompozit ties bilgi sakliyor mu; uretim siralama cozunurlugu olculebilir mi? | On-kayitli; canonical export SHA-256 `87541cc5...73ad` | H4C `INFORMATION_LOSS_NOT_SUPPORTED` (DL:3174); H4D-measure `CLOSED / PROVENANCE_INSUFFICIENT`, uretim sort-tuple NOT_MEASURABLE (DL:3208); H4A `COMPRESSION_SUPPORTED` (DL:3343); H4 "FROZEN/CLOSED" (RGA:17, RGA:56) | SUPPORTED (proxy duzeyinde); uretim siralamasi NOT_MEASURABLE | DL'de runner + JSON hash'leri listeli; varligi kontrol edilmedi | Proxy, uretim siralamasi degil | Uretim sort-tuple persistence (RGA:117, Level B) |
| Negative screen | ANS-1 (DL:3161) ve NS-1 (DL:3216-3256) | Dikkat haritasi / kurallar negatif eleme olarak calisir mi? | On-kayitli; NS-1 populasyon n=34,762 (DL:3252) | ANS-1 "SUPPORTED" (2026-09-18): medyan iyilesme +2.62pp, block-bootstrap %95 CI [+0.16, +3.86], null-shuffle p=0.000, big-loser orani %22.2 -> %3.5 (DL:3165); ANS-2 opportunity-cost, ANS-3 temporal "PARTIAL" (DL:3219); NS-1 overall `NO_SCREEN_SUPPORTED` (NS-A NOT_SUPPORTED, NS-B3/NS-C PARTIAL), bagimsiz dogrulama `VERIFICATION_PASS` (DL:3230, DL:3252) | NS-1: SUPPORTED (red icin); ANS-1: HYPOTHESIS (tarihsel, in-sample; ANS-3 zamansal PARTIAL; ANS-1 uzerine kurulan resmi NS-1 bataryasi eleme desteklemedi) | NS-1 runner/JSON hash'leri DL:3235'te | Ayni tarihsel export; yeni donem yok (RGA:81) | B5 negative-screen production BLOCKED (RGA:118) |
| Entry/exit, MFE/MAE/path | RX-CAPTURE-1 capture & exit battery (DL:3259-3287) | Sinyal sonrasi hareket yakalanabilir mi (cikis kurallari)? | On-kayitli; canonical export | E1_t3/E1_t5 `CAPTURE_SUPPORTED`, E0 `CAPTURE_NOT_SUPPORTED` (DL:3343); dogrulamada E1_t3 "median net primary +2.45pp, stress +2.0pp, first-touch hit share 61.5%" (DL:3284; "net" protokolun maliyet semantigi, gerceklesmis net degil) | HYPOTHESIS (tarihsel, ekonomik kapi eksik: "spread %0 (veri borcu)" RGA:113-114) | DL'de runner/JSON/verifier hash'leri | D7: tarihsel set OOS degil | Gercek maliyet/likidite verisi |
| Cost/slippage | RX-CAPTURE-1-ECON (DL:3348-3381) | Maliyet/saglamlik altinda yakalama korunuyor mu? | On-kayitli ekonomik inceleme | Overall `FURTHER_VALIDATION_SUPPORTED`; E1_t3 FURTHER_VALIDATION_SUPPORTED, E1_t5 INCONCLUSIVE; breakeven 1.75, temporal sign INCONSISTENT, "mean net @0.55" = -0.841163pp (varsayilan maliyet senaryosu; gerceklesmis net degil) (DL:3369, DL:3379) | CONTRADICTED (kilit kaydi, DL:79); sonuc HYPOTHESIS | DL'de hash'ler | Kilit hash'i ne commit'li v0.1-DRAFT ne 2026-10-09 calisma kopyasiyla eslesiyor (DL:79) | Kilit kaydinin insanca duzeltilmesi (DL:83) |
| Flag instrumentation / B2 | B2-0 (DL:3385-3421) | Flag'lerin kullaniciya etkisi ve konfigurasyon provenance'i | On-kayitli (LOCKED v2) | TOTAL `INCOMPLETE`; bagimsiz dogrulama `VERIFICATION_MISMATCH` (tek yorum farki); verdict of record INCOMPLETE, cozum B2-1'e ertelendi (DL:3397, DL:3413, DL:3421) | UNRESOLVED | DL'de prereg + trace hash'leri | Bazi flag'ler NOT_RECONSTRUCTIBLE (DL:3397) | B2-1 |
| Flag instrumentation / B2 | B2-1 / B2-T / B2-N / B2-AUTH (DL:3459-3725) | Provenance kurtarma | Taslak v3 + yapay teknik test | B2-1 DRAFT / LOCK BLOCKED / NOT RUN (DL:3509, DL:3548); B2-T v1 yapay kapsamda 28/28 TECHNICAL_PASS, NOT_INDEPENDENT (DL:3623); B2-N "conditional diagnostics, not B2-1 scientific recovery" (DL:3725) | UNRESOLVED (bilimsel test kosulmadi) | B2-T frozen bundle (DL:3588); hash'i bu turda yakalanmadi | Teknik PASS bilimsel kanit degil | B2-1 LOCK on-kosullari |
| Rejected hypotheses | RGA s.D kapali hatlar (RGA:56-66) | - | - | RX-H2 NOT_SUPPORTED; direction prediction NOT_SUPPORTED; S1 short interest REJECTED; High-RVOL REJECTED (tail-driven); TP/SL grid ZERO ROBUST CONFIGS; reverse-ranking/extension-cap artefakt; ranking-score backtest composite'ten kotu; V2 path-aware locked-OOS NO EDGE (n=62) | SUPPORTED (red icin; PRIOR) | kontrol edilmedi | Hepsi ayni tarihsel veri ailesinde; D7 sonrasi hicbiri OOS degil | DO_NOT_CHANGE (yeniden acmadan once yeni on-kayit) |
| Incomplete research | RGA:47; B3 (RGA:80) | +5% hedefin gec-donem zayiflamasi (1.556 -> 0.117) kalici mi? B2 -> B3 cesitlilik | - | Acik soru (RGA:47); B3 `WAITING_FOR_DATA` "2 gun/8 sembol" (RGA:80, RGA:116) | UNRESOLVED | - | - | Prospektif veri birikimi |
| Proposed, not implemented | P0 conviction-grade prereg DRAFT (DL:3456) | Grade olasilik kapanisi | Taslak | DRAFT, uygulanmadi; ifade karari Level C (DL:481) | UNRESOLVED | - | - | Insan karari |
| Score/ranking | Score calibration (Brier) (DAI:80) | Skor olasilik olarak kalibre mi? | Brier skill | "Brier skill -0,019/-0,030 - rastgeleden kotu" (2026-08-11) | SUPPORTED (red icin; PRIOR) | kontrol edilmedi | Tarihsel | D4 ifade karari ile tutarli kullanilmali (DL:46) |
| Entry/exit | Fixed-target grid E13 (RTR:51) | TP/SL gridinde saglam kazanan var mi? | 3,120 konfig; White RC + Hansen SPA + CPCV | WRC p=0,74, SPA p=0,78, PBO=0,6 -> "Rejected (robust kazanan yok)" | SUPPORTED (red icin) | kontrol edilmedi | Fixed-target kurali rapordan sonra commit edilmis (DL:105) | Yeni grid aramasi "STOP" (RTR:193) |
| Rejected hypotheses | Red-team E3/E4/E5/E6/E8/E10 (RTR:41-48) | Ters siralama, extension cap, concentration/ATR-parity, catastrophe subset, high-RVOL | Matched-random, permutasyon, blok-bootstrap | Hepsi "Rejected"; E6'da rastgele kontrolde de ayni iyilesme (0,365 -> 0,801); E10'da 4 gun %103'u acikliyor; E8 ayni gun geri cekildi | SUPPORTED (red icin; PRIOR) | kontrol edilmedi | Ayni `full_universe_enriched` ailesi | DO_NOT_CHANGE |
| Rejected hypotheses | `entry_ok` (RTR:192; MVA:177) | entry_ok uretim avantaji saglar mi? | - | "STOP" / "KILL - adverse selection" | SUPPORTED (red icin; PRIOR). Arsivde `entry_ok` yalniz 2,065 satirda, 2,059 False / 6 True (EVI_02) | - | - | - |
| Data coverage | Restatement detector (SRCI:69); 485 isaretli sembol (RTR:199); V0 `resolved_pct_t5` <-> cache (RTR:143, RTR:200) | Veri butunlugu | - | Restatement detector "BLOCKED" (immutable bar-cache snapshot yok); 485 sembol "DATA_REPAIR"; V0 korelasyonu icin uc celisen sayi (0,86 / 0,325 / 0,55) | UNRESOLVED; `resolved_pct_t5` bozuklugu REPRODUCED (EVI-F05) | - | - | Tek dondurulmus implementasyon |
| Proposed, not implemented / validation durumu | Abstention veto (RTR:198); H1/H2/H3 (RTR:202); MVA dogrulama matrisi (MVA:114-118) | - | - | Abstention "CONFIRMATORY_CANDIDATE"; H1-H3 "BLOCKED"; MVA: descriptive VALIDATED (40,834 satir), direction/OOS/production/economic hepsi hayir ("Maliyet modeli yok") | UNRESOLVED | - | MVA:116 "Locked OOS NOT_OPENED" (EVI-F04) | Bagimsiz veri (D7 prospektif) |

<!-- B2-END -->

### B3. Bolum 2.2 izleme

| Konu (brief 2.2) | Onceki calisma neyi cevapladi | Acik kalan | Yeni calisma ne katar |
|---|---|---|---|
| Uretim siralamasinin tekrar uretilemezligi | Tarihsel reconstruction "NOT_FULLY_RECONSTRUCTED", 6 ara girdi persist edilmemis (MRI s.1, s.3 madde 5); ileriye donuk yakalama GATE B1 8/8 exact, B2 24 gozlem (MRI s.2 madde 10-11); uretim sort-tuple `NOT_MEASURABLE / PROVENANCE_INSUFFICIENT` (DL:3208); OOS testlerinde "offline proxy; production ranking ... not reconstructed" (DL:79). Bu calisma: arsivde `finpilot_score` 5,206/5,206 NULL, `score` 65 farkli deger (EVI-F03); sonuc replay'inde 575/5,206 uyumsuzluk (PRIOR ODB:56) | B2 birikim esigi tanimsiz; B3 `WAITING_FOR_DATA` (RGA:80); son tie-breaker ve girdi sirasi provenance'i (DL:3208) | Surekli capture karari sonrasi B3 spec ile karsilastirma; arsiv `score` ile payload `score` / kaynak model eslemesi (yalniz metadata) |
| Genis vs temizlenmis veri seti | Genis setler: `full_universe_enriched_eod_only.csv` 57 gun / 40,014 satir (DL:895); NS-1 populasyonu 34,762 (DL:3252); OOS n 17,149-18,909 (DL:103). Yayin/arsiv seti: 5,206 karar satiri (B1). Arsiv icinde tanim duyarliligi 5,748 / 5,452 / 5,206 (EVI_03); kurtarilmis CSV 5,719 satir / 5,114 karar, durum ve getiri DB ile birebir (EVI_01); legacy JSON 55 dosya, 5,794 kayit, 5,719'u DB'de (EVI_01). Cakisan sinyaller: 5,748 satir 4,318 sembol-gunde (DL:91; EVI_01 `all_distinct_symbol_days`=4,318 ile REPRODUCED); karar satirlari 3,795 sembol-gun (EVI_01) | Arsiv sinyalinin genis setteki karsiligi (sembol + `signal_date` join) olculmedi; `resolved_pct_t5` kullanilamaz (EVI_01) | Join kapsama orani; tekillestirilmis birimde B1 agregatlarinin duyarliligi (kilitli olmayan veride) |
| Tarihsel kapsam / zaman penceresi | Kompozit yalniz son ~57 gunde tanimli (MRI s.3 madde 2); c2c_5d dolu aralik 2025-09-11 -> 2026-07-31 (82 gun) train/calib/valid'de tukenmis (DL:2007); 2026-01-01 sonrasi her pencere en az bir artefaktta degerlendirilmis (DL:105). Bu calisma: arsivde 2026-01/02'de karar satiri yok, 2025-11/12'de 6'sar (EVI_01); `ts` != `signal_date` 1,792 satir (EVI-F01) | `ts` yazan kod; sinyal zaman dilimi dogrulanmamis (DL:67); 2026-03 scanner_v1 toplu yaziminin niteligi | `signal_date` bazli yeniden indeksleme; D7 prospektif pencere |
| Siralama esitlikleri / dusuk cozunurluk | Kompozit 90 unique / 40k, %99.78 tie, gun-ici medyan cozunurluk ~%6 (MRI s.3 madde 1); H4A `COMPRESSION_SUPPORTED`, H4C `INFORMATION_LOSS_NOT_SUPPORTED` (DL:3343, DL:3174); funnel sinirinda tie yogunlugu %0.4-1.0 (DL:905). Bu calisma: arsiv `score` 5,132/5,206 satir gun-ici esit (EVI-F03) | Resmi uretim siralama cozunurlugu "DEFINITION_REQUIRED" (MRI s.3 madde 7) | Canli capture'da tie-breaker kaydi; float skor / tie-breaking onerisi (MRI s.5 #6) yalniz on-kayitli testle |
| Provider / cache / fallback yavasligi | 411 parti: medyan toplam 318 s, medyan 60 yfinance fallback, r=0.48 gozlemsel (DL:22); 5 satirlik kohortta `prefetch.repair` medyan 305.025 s, ratio-of-medians %90.61 (DL:9); tam evren uctan uca NOT MEASURED (DL:10); funnel hiz projeksiyonu ESTIMATED (DL:913-917) | Asama kirilimi cogu kayitta yok (DL:22); Faz 1/3 canli olcum NOT RUN (DL:28); nedensellik | Insan onayli izole pencerede donmus set ile Faz 1; fallback sayisinin kontrollu manipulasyonu |
| Kanitlanmamis skor degisiklikleri | 9 flag skoru %83.5 degistiriyor ama getiriyi tahmin etmiyor; ablation KEEP yok; walk-forward 0/3 (MRI s.1, s.2); B2-0 `INCOMPLETE`, bazi flag'ler NOT_RECONSTRUCTIBLE (DL:3397); flag karari "DEFERRED/BLOCKED BY BASELINE FAILURE" (DL:1871) | Hangi flag konfigurasyonunun hangi tarihte uretimde aktif oldugu (B2-1 LOCK BLOCKED, DL:3548); D7 sonrasi onceki "OOS" walk-forward sonuclari OOS sayilmaz | B2-1 provenance kurtarma; ileriye donuk capture ile on-kayitli flag-on/off karsilastirmasi |

<!-- B3-END -->

### B4. Kilitli / on-kayitli deney kayit defteri

Kaynak: DL satirlari (grep ciktisinda okundu), RGA = `reports/research_governance_audit_2026-09-23.md`. Hash'ler DL'de kayitli degerlerdir; bu turda dosyalara karsi yeniden hesaplanmadi (istisna: EVI_01'in hash'ledigi iki `data/backtest_out` dosyasi). Kilitli veri bolumu acilmadi; hicbir satir icin sonuc hesaplanmadi.

| ID | Artefakt | Kayitli hash (DL) | Tarih | Durum | Kosuldu / acildi mi |
|---|---|---|---|---|---|
| Canonical export (RESEARCH-X girdisi) | (yol DL:1241'de "canonical export") | `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad` | 2026-09-21/22 | NS-1, RX-CAPTURE-1, ECON dogrulamalarinda "verified unchanged" (DL:3256, DL:3287, DL:3382) | Girdi seti; D7'ye gore OOS degil (DL:46) |
| H4C prereg | `reports/research_x_h4c_information_loss_preregistration_2026-09-22.md` | sonuc JSON `f4b0b552...e762` (DL:3178) | 2026-09-22 | PREREG_LOCKED -> `INFORMATION_LOSS_NOT_SUPPORTED` | Kosuldu |
| H4D definition | `reports/research_x_h4d_ranking_resolution_definition_2026-09-22.md` | `cbd3812c...7499` (DL:3189) | 2026-09-22 | APPROVED/LOCKED (tanim) | Sonuc icermez |
| H4D-measure prereg | `reports/research_x_h4d_measure_preregistration_2026-09-22.md` | `9eb331c3...657b` (DL:3200); sonuc JSON `83198076...ab0c` (DL:3211) | 2026-09-22 | `CLOSED / PROVENANCE_INSUFFICIENT` | Kosuldu |
| NS-1 prereg | `reports/research_x_ns1_negative_screen_preregistration_2026-09-22.md` | `9e53d407...6838` (DL:3223); sonuc JSON `0d0402f5...165c`; dogrulama JSON `e54344b6...02a7` (DL:3235, DL:3256) | 2026-09-22 | `NO_SCREEN_SUPPORTED`, `VERIFICATION_PASS` | Kosuldu |
| RX-CAPTURE-1 prereg | `reports/research_x_capture_1_preregistration_2026-09-22.md` | `d0baa618...036e` (DL:3266); sonuc JSON `c6ab1521...e73e`; dogrulama `135a6a97...6085` (DL:3277, DL:3287) | 2026-09-22 | CAPTURE_SUPPORTED (E1), VERIFICATION_PASS; prereg 2026-10-14'te "hash-verified unchanged" (DL:79) | Kosuldu |
| RX-CAPTURE-1-ECON prereg | `reports/research_x_capture_1_economic_review_preregistration_2026-09-23.md` | `6b210259...12fb` (DL:3363); sonuc JSON `04a43868...7afd`; dogrulama `9b8b5b86...dcf5` (DL:3373, DL:3382) | 2026-09-23 | FURTHER_VALIDATION_SUPPORTED; kilit iddiasi CONTRADICTED (DL:79) | Kosuldu |
| Research Governance Controller spec v1 | `docs/governance/research_governance_controller_spec_v1.md` | `a3ea327b...b19b` (DL:3317) | 2026-09-23 | Locked (governance spec); testler 7/7, 9/9 PASS (DL:3333, DL:3343) | Deney degil |
| B2-0 prereg (LOCKED v2) | `reports/b2_0_flag_user_facing_impact_preregistration_2026-09-23.md` | `fe4ceab1...33c0` (DL:3391) | 2026-09-23 | INCOMPLETE / VERIFICATION_MISMATCH (DL:3421) | Kosuldu |
| B2-1 prereg | `reports/b2_1_provenance_recovery_preregistration_DRAFT_v3_2026-10-05.md` | `6745641a...eaf0` "draft identity only, NOT LOCK" (DL:3510); onceki taslak `0ae40a66...4c4e` (DL:3430) | 2026-10-05 | Metodoloji onayli (DL:3522); LOCK BLOCKED (DL:3548) | Kosulmadi |
| B2-T v1 | B2-T frozen bundle (DL:3588) | bu turda yakalanmadi | 2026-10-05/06 | 28/28 TECHNICAL_PASS, yapay kapsam (DL:3623) | Kosuldu (yapay) |
| P0 conviction-grade prereg | `reports/p0_conviction_grade_probability_closure_audit_preregistration_DRAFT_2026-09-23.md` | `59327b57...3b36` (DL:3456) | 2026-09-23 | DRAFT | Kosulmadi |
| 2026-05-21 "locked OOS" | `common_buy_accuracy.json` (DL:79) | dondurma kaydi yok (DL:79) | sinir 2026-05-21; sonuclar ilk kez 2026-07-15T16:52:02Z | Sonuclar raporlanmis: locked_oos n=44 (DL:79), n=62 TP5/SL1 +2.0501% (DL:103); RGA:64 "CLOSED / NO EDGE (n=62)"; D7: OOS sayilmaz (DL:46) | ACILMIS (sonuclar mevcut) |
| PIT holdout 2026-06-09..06-30 | state file "not_opened" (DL:103); muhtemel artefaktlar `data/backtest_out/fundamentals_sentiment_protocol.json` SHA-256 `d8e7ac9b...1e5b` (mtime 2026-08-05 13:31:08 yerel) ve `fundamentals_sentiment_holdout.json` SHA-256 `38781bb8...1ccc` (228 bayt, 13:31:24 yerel) (EVI_01; icerik okunmadi) | DL'de hash yok; "self-timestamped (2026-08-05 11:31 UTC), git-ignored" (DL:79) | 2026-08-05 | Daha once degerlendirilmis donemlerle cakisiyor (DL:79); D7: OOS sayilmaz | NOT_OPENED kaydi; eslesme HYPOTHESIS (UTC+2 varsayimiyla zaman tutarli) |
| Fixed-target holdout | open-state dosyasi | yok ("absent", DL:79) | 2026-08 | `LockedHoldoutGuard` hicbir runner tarafindan cagrilmiyor; erisim logu yok (DL:79); kural raporundan sonra commit edilmis (DL:105) | Belirlenemez (NOT_MEASURABLE) |
| H1-H3 prereg | `reports/preregistration_three_hypotheses_2026-08-10.md` (MRI s.2) | bu turda yakalanmadi | 2026-08-10 | "Kapi 4, pre-registered H1-H3 hala kilitli" (DL:2222) | Kosulmadi (DL:2222 aninda) |
| ANS-1 | DL:3161 | bu turda yakalanmadi | 2026-09-18 | "SUPPORTED (Level A, pre-registered, read-only)" | Kosuldu |
| B3/B4 spec | `research/b3_b4_baseline_validation_spec_2026_09_11.md` (MRI s.4) | bu turda yakalanmadi | 2026-09-11 | SPEC REGISTERED, BLOCKED_BY_B2 | Kosulmadi |
| D7 prospektif OOS | `reports/oos_status_c_remediation_v1_2026-10-15/` (Option C) | - | 2026-10-16 | Kabul edildi; esik yok, veri yok (DL:46) | Veri henuz olusmadi |

<!-- B4-END -->

### Bulgu kayitlari (EVI-Fxx)

#### EVI-F01 - Top-1% yogunlasmasi iki islem gunu degil; iki arsiv-yazim tarihi ve tek kaynak model (scanner_v1)

- Priority: P0 (validity) - zaman alanina dayali her bolme (OOS, rejim, tarih kumelemesi) `ts` ile yapilirsa satirlar yanlis doneme duser.
- file:function:lines: veri bulgusu; `ts` alanini yazan kod satiri bu turda dogrulanmadi (UNRESOLVED).
- Data source: `data/finpilot.db` (SHA-256 `b64c0c52...f5f6`), `signals_archive.ts`, `payload_json.signal_date`, `payload_json.source_model`.
- Method/command: `scripts/EVI_03_verify.py` (top-k = `resolved_pct_barrier` azalan; tarih sayimi; `datetime` ile haftanin gunu); EVI_01/EVI_02 alanlari.
- Result: 52 top-1% satirin 48'i `ts` = 2026-03-01 (Sun, 21) veya 2026-03-03 (Tue, 27). `signal_date`'e gore ayni satirlar 2026-03-03 (27), 2026-02-12 (10), 2026-02-17 (9) ve 6 tekil tarihe dagiliyor. 5,206 karar satirinin 1,792'sinde `ts` tarihi != `signal_date` (EVI_01); fark (gun): -1:176, 5:225, 7:90, 12:487, 14:224, 17:298, 18:186, 128:12, 135:6, 136:12, 144:40, 145:36 (EVI_02). 2026-03 `ts` ayinin 2,495 satirinin tamami scanner_v1 (EVI_03). `signal_date` de temiz islem gunu degil: Sun 800, Sat 227 satir (EVI_02).
- n: 52 (top-1%); 5,206 (karar satiri).
- Label: MEASURED (arsiv metadatasi); brief'teki "iki islem gunu" ifadesi CONTRADICTED. Ayni ifade PRIOR kayitta da var: DL:67 (2026-10-14 outlier kaydi) bu tarihleri "two signal dates (2026-03-01 and 2026-03-03)" diye niteliyor; payload `signal_date`'e gore bu da CONTRADICTED. Ayni kayittaki "bu tarihler haric ortalama +0.13%" degeri bu turda yeniden uretilmedi.
- Limitations: sonuclarin dogrulugunu degil yalniz zaman metadatasini olcer; iki tarih zaten karar satirlarinin %46.5'ini tasidigi icin yogunlasmanin bir kismi taban oran etkisidir (EVI_03).
- Alternative explanations: (a) 2026-02/03 sinyal tarihlerinde gercek piyasa olayi kumelenmesi; (b) scanner_v1 icin geriye donuk toplu yazim (backfill) ve farkli giris konvansiyonu; (c) tekrarlanan sembol-gunler: karar satirlarinin 1,815'i tekrar eden sembol-gun gruplarinda, farkli sembol-gun 3,795 (EVI_01; sembol-gun tanimi EVI_01 scriptinde, bu turda yeniden okunmadi).
- Next step: `ts` yazan kodu git log/blame ile 2026-03-01..03 civarinda izlemek; `entry_price`'i `signal_date` ve `ts` kapanislariyla kilitli olmayan veride karsilastirmak; sembol-gun tekillestirmesiyle yogunlasmayi yeniden olcmek.
- Suggested category: RESEARCH_NEXT.

#### EVI-F02 - "~1,800 Nasdaq evreni" iddiasi karma-borsa preset birlesimi; arsivin sinyal-anindaki evreni kayitli degil

- Priority: P1 (economic-evaluation blocker) - evren tanimi taban oran, survivorship ve kapsam yorumunu belirler.
- file:function:lines: `web/public/stock_presets.json` (veri dosyasi; kod satiri yok).
- Data source: `web/public/stock_presets.json` SHA-256 `4e300c19...9e36` (mtime 2026-06-10); `data/finpilot.db` tablolari `symbols`, `symbol_lists`, `signals_archive`.
- Method/command: EVI_01, EVI_02 (preset birlesimi, `symbols.exchange` eslemesi).
- Result: preset birlesimi 1,812 sembol; NASDAQ 1,504, NYSE 270, AMEX 37, ARCA 1. Karar verilmis arsivde 1,017 farkli sembol; 953'u bugunku preset birlesiminde; 51 satirin sembolu `symbols` tablosunda yok.
- n: 1,812 sembol; 1,017 arsiv sembolu; 5,206 satir.
- Label: MEASURED (sayimlar); "Nasdaq evreni" etiketi CONTRADICTED (kismen).
- Limitations: borsa bilgisi bugunku `symbols` tablosundan; sinyal tarihindeki listeleme durumu bilinmiyor.
- Alternative explanations: "Nasdaq" ifadesi Alpaca varlik listesinin cogunluguna (1,504/1,812) atifla kullanilmis olabilir.
- Next step: tarihli evren anlik goruntusu (point-in-time) kaydinin olup olmadigini kod/raporlarda aramak; yoksa kayit eksigi olarak belgelemek.
- Suggested category: NEEDS_MORE_DATA.

#### EVI-F03 - Arsivdeki `score` dusuk cozunurluklu, `finpilot_score` tamamen NULL; uretim siralamasi arsivden yeniden kurulamaz

- Priority: P1 (economic-evaluation blocker) - top-N / siralama ekonomisi arsiv uzerinden degerlendirilemez.
- file:function:lines: veri bulgusu (`signals_archive.score`, `signals_archive.finpilot_score`).
- Data source: `data/finpilot.db` (SHA-256 `b64c0c52...f5f6`).
- Method/command: `scripts/EVI_03_verify.py` (`value_profile`, `within_day_ties`).
- Result: 5,206 karar satirinda `score` 65 farkli deger; en sik 1.0 (2,697), 0.0 (1,056), 2.0 (892), 3.0 (116), 7.6 (39); %98.19 tam sayi degerli; aralik 0-89. Ayni `ts` gununde baska bir satirla ayni skoru paylasan satir: 5,132/5,206 (37 `ts` gunu). `finpilot_score` 5,206/5,206 NULL.
- n: 5,206.
- Label: MEASURED (arsiv icerigi). Uretimdeki canli siralama davranisi: NOT_MEASURABLE (bu tablodan).
- Limitations: `score` olceginin kaynak modele gore farklilasip farklilasmadigi ve payload icindeki `score` anahtarinin kolonla ayni olup olmadigi bu turda olculmedi.
- Alternative explanations: kolon kompozit skor degil, kademe/sayac tipi bir alan olabilir; kompozit skor payload veya baska tabloda olabilir.
- Next step: kaynak model bazinda `score` ve payload `score` karsilastirmasi (yalniz metadata).
- Suggested category: RESEARCH_NEXT.

#### EVI-F04 - Master envanterdeki "Locked OOS: NOT_OPENED" ifadesi 2026-10-14 OOS denetimleri ve D7 ile celisiyor

- Priority: P0 (validity) - envanteri "tek referans otoritesi" olarak okuyan her rol, tarihsel setleri hala OOS sanabilir.
- file:function:lines: `reports/MASTER_RESEARCH_INVENTORY_2026-09-10.md` s.1 tablo "Locked OOS | NOT_OPENED" satiri ve s.6 ilk madde (okundu); `docs/governance/decision-log.md` DL:46 (D7), DL:79-80, DL:103-105.
- Data source: dokumanlar (veri dosyasi yok).
- Method/command: `read_file` MRI 1-215; `read_file` DL 1-110.
- Result: MRI s.1 ve s.6 "NOT_OPENED" diyor; DL:79 "No trading-strategy out-of-sample set has a verifiable freeze" ve DL:103 locked-OOS n=62 sonuclarini (TP5/SL1 +2.0501%, TP5/SL1.5 -0.0046%) kaydediyor; DL:105 "no historical window qualifies as an untouched holdout"; D7 (DL:46) mevcut setlerin OOS sayilmayacagini karara bagliyor. MRI'nin s.3 madde 7 ile 2026-09-21'de guncellendigi goruluyor, ancak OOS satiri guncellenmemis.
- n: 1 dokuman satiri; 3 DL kaydi.
- Label: CONTRADICTED (MRI ifadesi); celisinin kendisi DL:80 ve DL:104'te zaten CORE-005 olarak raporlanmis. Ek: `reports/research_governance_audit_2026-09-23.md` kendi icinde de celisik: RGA:64 "V2 path-aware locked-OOS -> CLOSED / NO EDGE (n=62)" ile RGA:158 "LOCKED_OOS = NOT_OPENED" (grep ciktisinda okundu). Ayni bayat ifade `reports/meta_validation_audit_2026-09-08.md` MVA:116'da da var ("VALIDATED - OOS | Locked OOS NOT_OPENED").
- Limitations: OOS denetimlerinin bulgulari bu turda artefakt duzeyinde yeniden dogrulanmadi (PRIOR).
- Alternative explanations: "NOT_OPENED" yalniz belirli bir dosya (ornegin fixed-target open-state dosyasi, DL:79 "absent") icin kastedilmis olabilir; MRI bunu ayirt etmiyor.
- Next step: MRI satirina "superseded by D7 / 2026-10-14 audits" notu (Level B dokuman degisikligi; insan onayi).
- Suggested category: FIX_CANDIDATE.

#### EVI-F05 - `resolved_pct_t5` alani kullanilamaz; uc degerler arsivde hala mevcut

- Priority: P1 (economic-evaluation blocker) - t5 alanina dayanan her ortalama anlamsiz.
- file:function:lines: veri bulgusu (`signals_archive.resolved_pct_t5`).
- Data source: `data/finpilot.db` (SHA-256 `b64c0c52...f5f6`).
- Method/command: EVI_01 `alt_field_resolved_pct_t5_all_nonnull` ve `alt_field_resolved_pct_t5_on_decided`.
- Result: tum NULL-olmayanlarda n=5,213, ortalama +13.660876%, medyan -1.2797%, min -96.2144%, max +11,990.9096%; karar satirlarinda n=5,204, ortalama +13.68255%. PRIOR DL:91 ayni araligi (-96%..+11,991%, 166 satir +-50% disinda) raporlamis; RTR:143 V0 korelasyonu icin uc celisen sayi (0,86 / 0,325 / 0,55) kaydediyor.
- n: 5,213.
- Label: REPRODUCED (aralik ve ortalama); nedeni UNRESOLVED.
- Limitations: +-50% disi satir sayisi bu turda yeniden sayilmadi.
- Alternative explanations: bolunme/ters bolunme duzeltmesi eksik fiyat serileri (RTR:199 "485 flagged sembol" ile iliskili olabilir; dogrulanmadi).
- Next step: alanin hangi yuzeylerde/raporlarda kullanildiginin envanteri; kullanilmamasi gerektiginin belgelenmesi.
- Suggested category: FIX_CANDIDATE.

<!-- FINDINGS-END -->

## Dogru calisan kisimlar

- Bariyer etiketi kendi tanimiyla tutarli: 5,206/5,206 satirda saklanan `resolved_pct_barrier` TP/entry-1 veya SL/entry-1 ile 0.05 pp icinde (EVI_01). Karar satirlarinda `resolved_status` = `resolved_status_barrier` ve `resolved_pct` = `resolved_pct_barrier` (5,206/5,206, EVI_01).
- Arsiv kopyalari tutarli: kurtarilmis CSV'nin (SHA-256 `a48eab6c...59a0`) 5,114 karar satiri durum ve getiri olarak DB ile birebir (EVI_01).
- Onceki outlier raporunun sayilari 4 ondalikta yeniden uretildi (B1); DB hash'i EVI_01 ve EVI_03 arasinda degismedi.
- NS-1, RX-CAPTURE-1 ve ECON icin on-kayit + hash + bagimsiz dogrulama zinciri kayitli (DL:3256, DL:3287, DL:3382); 2026-10-14 denetimleri celiskileri CORE-005 olarak acikca raporlamis (DL:80, DL:104, DL:10). Bu, surec kaydinin varligidir; karlilik kaniti degildir.

<!-- DOGRU-END -->

## Cevaplanamayan sorular

1. `ts` alanini 2026-03-01 ve 2026-03-03'te hangi kod/surec yazdi; 2026-03 scanner_v1 2,495 satiri canli sinyal mi, geriye donuk kosum mu? (UNRESOLVED)
2. "~1,800 Nasdaq evreni" ifadesinin birincil kaynagi bu turda bulunamadi. (UNRESOLVED)
3. 575/5,206 replay uyumsuzlugunun nedeni (PRIOR ODB:56'da da acik). (UNRESOLVED)
4. Arsiv `score` olceginin kaynak model bazinda anlami (0-3 tamsayi agirlikli, max 89). (UNRESOLVED)
5. ANS-1 "SUPPORTED" ile NS-1 `NO_SCREEN_SUPPORTED` arasindaki iliskinin resmi yorumu. (UNRESOLVED)
6. H1-H3, ANS-1, B2-T ve B3/B4 spec hash'leri bu turda yakalanmadi. (UNRESOLVED)
7. Net beklenti: gerceklesmis fill yok (`alpaca_orders` bugun 14 satir, 0 fill; EVI_02; DL:91'de 11 emir). (NOT_MEASURABLE)
8. Hedef pozisyon buyuklugu ve pozisyon tavani celiskisi (DL:67) - Level C insan karari.

<!-- SORU-END -->

## Sinirlamalar

- Butce sinirli okuma: backbone envanterlerden MRI (satir 1-215) okundu, RGA grep ile tarandi. `reports/scanner_research_complete_inventory_2026-08-11.md` (SRCI), `reports/decision_architecture_research_inventory_2026-09-07.md` (DAI), `reports/meta_validation_audit_2026-09-08.md` (MVA) ve `reports/red-team-scientific-review-2026-08-12.md` (RTR) tam okunmadi; yalniz durum kelimesi iceren tablo satirlari tek bir grep ile alindi (40 eslesme). Bu dosyalardaki diger kalemler B2'de eksik olabilir.
- DL'den okunan araliklar: 1-110, 886-918 ve grep eslesmeleri; kesilmis (truncated) grep satirlarinin kalan kismi okunmadi.
- B1 disindaki PRIOR sayilar bu turda bagimsiz yeniden uretilmedi. B4 hash'leri DL'de kayitli degerlerdir, dosyalara karsi yeniden hesaplanmadi; "Tekrar" sutununda script/girdi varligi cogunlukla kontrol edilmedi.
- `data/finpilot.db` canli bir dosya (mtime 2026-10-19T12:08:56 yerel); sonuclar SHA-256 `b64c0c52...f5f6` icin gecerli. Kod satiri okunmadi; kod duzeyindeki iddialar PRIOR'dur.
- D7 geregi tum sayilar tarihsel/in-sample veya tanimlayicidir; hicbiri OOS degildir. Rapor ASCII Turkce yazildi.

<!-- SINIR-END -->

## Ek: komutlar

1. Onceki rol ciktilari okundu (yeniden calistirilmadi): `data/EVI_01_archive_provenance.json` (uretim 2026-10-19T10:22:09Z, `scripts/EVI_01_archive_provenance.py`), `data/EVI_02_payload_universe.json` (10:23:29Z, `scripts/EVI_02_payload_universe.py`).
2. grep (regex) `5[,.]?206|1[,.]?8\d\d|0\.40|0\.64|0\.19|0\.16|top.?1%|top.?5%|...` -> `reports/outlier_dependence_audit_v1_2026-10-14/**/*.md` (24 eslesme, 5 dosya).
3. `& "C:\Users\meric\AppData\Local\Programs\Python\Python312\python.exe" -B reports\scanner_intelligence_audit_v1_2026-10-19\scripts\EVI_03_verify.py` -> `data/EVI_03_verify.json` (SQLite `mode=ro` + `PRAGMA query_only=ON`; DB SHA-256 calisma oncesi/sonrasi ayni: `b64c0c52...f5f6`).
4. `read_file` MRI 1-215; `read_file` DL 1-110 ve 886-918.
5. grep (DL): basliklar `^\[2026-[0-9-]+\].*(NS-1|ANS-?[1-3]|RX-CAPTURE|...|seal)` (55 eslesme); hash kayitlari `(?i)(prereg|locked|lock hash|holdout|sealed|protocol).{0,200}\b[0-9a-f]{64}\b` (25); sonuc satirlari `^(Verdict|Result|Results|Outcome|Status): .*(SUPPORTED|...)` (44); `RX-CAPTURE|NS-1|...|sealed` (268, ilk 80 gosterildi); `ANS-[23]|...|recall [0-9]+%` (7).
6. grep (RGA): `->|CLOSED|NO EDGE|OPEN|BLOCKED` (31 eslesme).
7. grep (SRCI, DAI, MVA, RTR): `^\|.*(STOP|BLOCKED|DATA_REPAIR|CONFIRMATORY_CANDIDATE|PRODUCT_MVP|KILL|REJECTED|NOT_SUPPORTED|CRITICAL CONTRADICTION|VALIDATED)` (40 eslesme, 4 dosya).
8. `git -C C:\Users\meric\Borsa --no-optional-locks status --porcelain=v1 -uall` (2026-10-19, rapor sonu): toplam 113 kayit; denetim klasorunde 24 (bu rolun 7'si: bu rapor, `data/EVI_01..03_*.json`, `scripts/EVI_01..03_*.py`); klasor disi 89 kayit, `%TEMP%\fp_audit_2026_10_19_pre.txt` on-goruntusuyle fark yok.

<!-- EK-END -->

<!-- END -->
