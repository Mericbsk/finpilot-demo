# R5 - Flags, Composite Score ve Ranking (WP-4)

- Versiyon: v1
- Tarih: 2026-10-19
- Durum: DRAFT - Level A arastirma ciktisi; karar degildir
- HEAD: 93ae83c (branch `review/pending-2026-10-07`, dirty tree; dokunulmadi)
- Rol: R5 - Flags, Composite Score and Ranking (PREFIX: SCR)
- Kapsam: production `/scan` yolunda rank ve secimi belirleyen alanlar; skor/rank/filtre/entry/exit etkileyen env flag'leri; `composite_score` yeniden uretilebilirligi; cozunurluk ve esitlikler; PRIOR monotonluk kanitlari; `data/scanner_config.json` kelly anahtarlari; onceden tanimli ablation sorulari.
- Girdiler: `scanner/evaluate.py`, `scanner/score_engine.py`, `api/routers/scan.py`, `distribution/*`, `core/scheduler.py`, `data/shortlists/shortlist_202610*.csv` (salt-okunur), `data/scanner_config.json` (salt-okunur), PRIOR raporlar (Ek'te listelenir).
- Flag gozlemi (orkestrator, 2026-10-16T13:58Z, degismis olabilir): FUNDAMENTALS=1, NEWS=1, FRED_MACRO=1, EDGAR_CATALYST=1, SQUEEZE_FACTOR=1, LOTTERY_FADE=1, SHADOW_SCORECARD=1, SCAN_LLM_SUMMARY=1, SCAN_SUMMARY_ALERT=0, FINPILOT_EXECUTION_MODE=dry_run; DISTRIBUTION / LEGACY_SIGNAL_ALERTS / LEGACY_COMPOSITE_RANKING set edilmemis.

## Ozet

- SCR-01 (P1, SUPPORTED+MEASURED): Yayin listesi `distribution/snapshot_builder.py:_sort_key:99-116` ile siralaniyor: grade (A<B<C) -> `execution_confidence` -> `conviction_prob` (tier icinde sabit) -> `ranking_score`. `ranking_score` flag set degilken `legacy_quality_score`; 120 Ekim shortlist dosyasinda 20,298/20,298 satirda esit. `composite_score` rank'i belirlemiyor; yalniz sizing, `score_floor` uyarisi ve `finpilot_score` girdisi.
- SCR-02 (P1): Gozlenen skor flag'lerinden yalniz SQUEEZE `ranking_score`'u etkiliyor; EDGAR/LOTTERY/OVERNIGHT/FRED/SENTIMENT yalniz composite'i. OVERNIGHT_GAP ve CONVICTION_TIERS gozlem listesinde yok ama Ekim verisinde aktif (MEASURED). Gozlenen `FINPILOT_ENABLE_NEWS` kod dizinlerinde referanssiz.
- SCR-03 (P2, REPRODUCED): composite saklanan bilesenlerden 17,313/17,333 (99.88%) yeniden uretildi (satir flag'leri ile); gozlenen flag setiyle 9,662/17,333 (55.7%). `legacy_quality_score` NOT_MEASURABLE (`atr_pct` persist edilmiyor).
- SCR-04 (P2, MEASURED): composite 85 farkli deger; top-50 esitlik payi medyan 0.78. `ranking_score` 11,762 farkli deger; top-10/50 esitlik payi medyan 0. Kodda acik tie-break yok; esitlikte `as_completed` sirasi.
- SCR-05 (P1, PRIOR): Skor->getiri monotonlugu PRIOR calismalarda desteklenmiyor (H2a NOT_SUPPORTED; walk-forward baseline Spearman ~0); fiili rank alani (legacy) icin ayri monotonluk kaniti bulunamadi.
- SCR-06 (P2, SUPPORTED): `scanner_config.json` kelly anahtarlarini hicbir runtime `*.py` okumuyor; 4->1 degisimi scheduler yazicisiyla tutarli; ne secimi ne sizing'i etkiliyor (yazili deger).
- SCR-07: alti onceden tanimli ablation sorusu (calistirilmadi).

## Kapsam ve yontem

- Kod izleme: hedefli `grep_search` + `read_file` ile satir dogrulama. Kod varligi veya gecen test, production davranisinin MEASURED kaniti sayilmadi.
- Veri: yalnizca `data/shortlists/shortlist_202610*.csv` salt-okunur okundu; turetilmis ciktilar `data/SCR_*` altinda.
- PRIOR raporlar yeniden calistirilmadi; yalnizca alintilandi.
- D7 (2026-10-16): hicbir sonuc out-of-sample olarak etiketlenmez. Locked/holdout/sealed bolumlerde outcome hesaplanmadi.

## Bulgular

### SCR-01 - Yayinlanan aday sirasini `composite_score` degil `_sort_key` belirliyor; `ranking_score` varsayilan olarak `legacy_quality_score`

- Priority: P1 (economic-evaluation blocker)
- Konum (her satir `read_file` ile okundu; satir no. grep ankrajli sayim):
  - `scanner/evaluate.py:evaluate_symbol:546-549` - `_composite_score = compute_recommendation_strength(...)`; `_gate_mult = regime_gate_mult(...)` yalnizca `regime_gate_mult` / `position_size_gated` alanlarina gider (718-719); rank'e girmez.
  - `scanner/evaluate.py:evaluate_symbol:565-578` - `compute_conviction(...)` yalnizca `entry_ok` iken cagrilir, aksi halde `("", 0.0)`.
  - `scanner/features.py:compute_conviction:209-237` + `_conviction_enabled:182-183` - `FINPILOT_ENABLE_CONVICTION_TIERS != "1"` iken her zaman `("", 0.0)`; `conviction_prob` tier basina sabit (`_CONV_PROB`, satir 179: A=0.73, B=0.59, C=0.52).
  - `scanner/evaluate.py:evaluate_symbol:592-594` - `selection_eligible = entry_ok and execution_feasible`.
  - `scanner/evaluate.py:evaluate_symbol:595-607` - `_ranking_score = _composite_score if legacy_composite_ranking_enabled() else _legacy_quality_score`; `scanner/score_engine.py:legacy_composite_ranking_enabled:238-240` varsayilan `"0"`.
  - `scanner/evaluate.py:evaluate_symbol:706` - `"ranking_method": "legacy_quality"` sabit yazilir; flag=1 iken `ranking_score` composite olsa da etiket degismez (telemetri tutarsizligi).
  - `scanner/evaluate.py:evaluate_symbols_parallel:761,817-826` - `as_completed` ile sonuclar tamamlanma sirasinda toplanir; sonradan siralama yok (okunan aralik 761-850).
  - `api/routers/scan.py:_persist_shortlist:139-150` - shortlist CSV `out.values()` sirasiyla yazilir; dosyadaki satir sirasi rank sirasi degildir.
  - `distribution/jobs.py:176-180,196,221` - taslak/yayin listesi `load_scan_export_record()["results"]` uzerinden `build_snapshot(...)` ile kurulur (shortlist CSV degil).
  - `distribution/snapshot_builder.py:_grade_of:86-96`, `_sort_key:99-116`, `_public_candidate:123-131`, `build_snapshot:397-409`, `MAX_CANDIDATES=50` (34), `FREE_CANDIDATES=2` (33).
- Yontem: kod izleme (`grep_search` + `read_file`), calistirma yok.
- Sonuc (kod duzeyi):
  1. Yayin filtresi `_public_candidate`: grade var (conviction_tier A/B/C; yoksa `tier` CONFIRM->B, TRIGGER->C) VE `selection_eligible` true (alan varsa) VE `execution_feasible` true (alan varsa) VE `position_cap_reject_reason` bos.
  2. Siralama anahtari `(grade A<B<C, execution_confidence Tier 2<Tier 1<Tier 0, -conviction_prob, -score)`; `score = ranking_score or legacy_quality_score or composite_score or score`. `conviction_prob` tier icinde sabit oldugundan grade icinde ayirt edici degildir; grade + execution tier icinde fiili ayirici `ranking_score` (= `legacy_quality_score`, flag set degilken).
  3. `legacy_quality_score` (`scanner/score_engine.py:compute_legacy_quality_score:193-221`) regime, direction, raw score, ATR%, RVOL, squeeze, lottery, overnight kullanir; sentiment, fundamentals, FRED macro, EDGAR catalyst, alignment/momentum_ratio, filter_score KULLANMAZ ve hicbir FINPILOT_ENABLE_* flag'ine bagli degildir (lottery/overnight cezasi flag'den bagimsiz uygulanir).
  4. Python `sort` stabil: tam esitlikte sira export'taki giris sirasina, o da `as_completed` tamamlanma sirasina baglidir (deterministik olmayan tie-break; export yazim sirasi dogrulanmadi).
  5. `or` zinciri: `ranking_score == 0.0` (falsy) ise anahtar farkli olcekli `composite_score`'a duser (olcek karisimi riski, P2).
- n: kod izleme + 20,298 satir veri destegi. Label: SUPPORTED (kod) + MEASURED (saklanan scan dosyalarinda alan esitligi); production'in tamamina genelleme yapilmaz.
- Sinirlamalar: `execution_confidence` uretimi (`scanner/execution_policy.py`) ve export yazim kodu satir satir okunmadi; `FINPILOT_ENABLE_CONVICTION_TIERS` production durumu UNKNOWN (gozlem listesinde yok).
- Alternatif aciklamalar: gozlenmeyen bir env (or. `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=1`) ranking'i composite'e cevirebilir; container env'i 2026-10-16 sonrasi degismis olabilir.
- Veri destegi (MEASURED; `scripts/SCR_r5_analysis.py main`; 120 shortlist dosyasi, n=20,298 satir; manifest SHA-256 SCR-03'te): `ranking_score == legacy_quality_score` 20,298/20,298; `ranking_method == legacy_quality` 20,298/20,298; `entry_ok` true 62, `selection_eligible` true 62; `conviction_tier` B=10, C=12, bos=20,276; `tier` kolonu yok (watch-tier fallback bu yolda devrede degil); skorlanmis 17,333 satirin tamaminda `execution_confidence == Tier 1` (sabit, ayirt edici degil); `_public_candidate` aynasindan gecen satir 22 (16 dosyada, dosya basina max 4). Bu dosyalarda sira = grade (B once C) ve grade icinde `ranking_score` (legacy); `composite_score` sirayi belirlemiyor.
- Sonraki adim: export (`load_scan_export_record`) sira/iceriginin shortlist ile ayni oldugunu salt-okunur dogrulamak; deterministik tie-break (or. ikincil anahtar `symbol`) icin Level B oneri.
- Kategori: KEEP_AS_IS (secim mantigi) + FIX_CANDIDATE (`ranking_method` sabit etiketi; `or` zinciri; deterministik tie-break).

### SCR-02 - Flag registry: gozlenen skor flag'lerinin cogu yalnizca `composite_score`'u degistiriyor; `ranking_score`'u degistiren tek gozlenen skor flag'i SQUEEZE; iki flag gozlem disi ama veride aktif

- Priority: P1
- Kaynak: `scripts/SCR_r5_analysis.py main` (statik tarama: `scanner`, `api`, `core`, `distribution`, `agents` altindaki `*.py`; tests ayri sayildi) -> `data/SCR_flag_registry.json` (21 FINPILOT_ENABLE_* flag); satir satir okunanlar asagida belirtildi. Etki kolonu yalnizca kod okumasidir.

| Flag | file:lines | Default | Etki (kod) | Production durumu | Test dosyasi (adet) |
|---|---|---|---|---|---|
| `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING` | `scanner/score_engine.py:238-240`; `scanner/evaluate.py:605-607` | 0 | "1" iken `ranking_score = composite_score` | gozlem: set degil; MEASURED: 20,298/20,298 satirda `ranking_score == legacy_quality_score` (aktif degil) | 1 |
| `FINPILOT_ENABLE_CONVICTION_TIERS` | `scanner/features.py:182-183,209-237`; `agents/alert_agent.py:111` | 0 | grade A/B/C -> yayin filtresi + birinci siralama anahtari | gozlem: UNKNOWN; MEASURED cikarim: B/C tier'li 22 satir var -> scan aninda "1" (kod kapaliyken `("", 0.0)` doner) | 1 |
| `FINPILOT_ENABLE_SQUEEZE_FACTOR` | `scanner/features.py:415-416`; `scanner/score_engine.py:33-34` | 0 | `squeeze_factor` hesaplanir -> legacy ranking (+0..5 puan), conviction `short_strong`, composite (+0..1.5 x macro) | gozlem 1; telemetri `score_feature_flags.squeeze_factor` true 17,333/17,333 | 3 |
| `FINPILOT_ENABLE_EDGAR_CATALYST` | `scanner/score_engine.py:44-45`; `scanner/catalyst.py:64` | 0 | yalniz composite (+/-1.5 x macro; lottery cezasina relief) | gozlem 1; telemetri true 17,333/17,333 | 2 |
| `FINPILOT_ENABLE_LOTTERY_FADE` | `scanner/score_engine.py:61-62` | 0 | yalniz composite (-0..2). Legacy ranking lottery cezasini flag'den BAGIMSIZ uygular (`score_engine.py:193-221`) | gozlem 1; telemetri true 17,333/17,333 | 1 |
| `FINPILOT_ENABLE_OVERNIGHT_GAP` | `scanner/score_engine.py:72-73` | 0 | yalniz composite (-0..1); legacy bagimsiz uygular | gozlem: listede YOK; MEASURED: telemetri true 17,333/17,333 -> scan aninda aktif | 1 |
| `FINPILOT_ENABLE_FRED_MACRO` | `scanner/score_engine.py:83-96`; `core/macro_regime.py:50` | 0 | squeeze/catalyst composite terimlerini carpar | gozlem 1; cikarsanan carpan ~1.00 (SCR-03) | 1 |
| `FINPILOT_ENABLE_SENTIMENT` | `scanner/sentiment.py:48` (+API key) | 0 | composite +/-0.5 | UNKNOWN (gozlenen NEWS farkli isim); V1 uyumsuzluklarinda sifirdan farkli sentiment bileseni yok | 1 |
| `FINPILOT_ENABLE_NEWS` | kod dizinlerinde referans YOK | - | bulunamadi | gozlem 1 (etkisiz olabilir; diger dizinler taranmadi) | - |
| `FINPILOT_ENABLE_FUNDAMENTALS` | `scanner/features.py:598` | ? | UNRESOLVED (satir icerigi okunmadi) | gozlem 1 | 0 |
| `FINPILOT_ENABLE_ALPHA_V2` | `scanner/features.py:162,172,415`; `scanner/risk_engine.py:204` | 0 | squeeze hesaplatir; risk_engine dali (stop/hedef?) UNRESOLVED | UNKNOWN | 2 |
| `FINPILOT_ENABLE_EXECUTION_POLICY` | `scanner/execution_policy.py:31-32,63` | 0 | `execution_feasible = adv_available or not enabled` -> `selection_eligible` | UNKNOWN | 1 |
| `FINPILOT_ENABLE_PORTFOLIO_ADV_LIMIT` | `scanner/execution_policy.py:35-36,95-111` | 1 | `position_cap_reject_reason` -> yayin filtresi | UNKNOWN (default acik) | 1 |
| `FINPILOT_ENABLE_REGIME_WEIGHTS` | `core/regime_weights.py:36,40` | 0 | scan yoluna baglantisi dogrulanmadi | UNKNOWN | 1 |
| `FINPILOT_ENABLE_EARLY_TIER` | `scanner/watch_tier.py:158` | ? | watch tier; Ekim shortlist'lerinde `tier` kolonu yok | UNKNOWN | 0 |
| `FINPILOT_ENABLE_EODHD_BARS` | `scanner/data_fetcher.py:1040,1050` | 0 | girdi veri kaynagi (dolayli) | UNKNOWN | 0 |
| `FINPILOT_ENABLE_DISTRIBUTION` | `distribution/jobs.py:49`; `core/scheduler.py:1373` | 0 | dagitim isleri | gozlem: set degil -> default 0 | 1 |
| `FINPILOT_ENABLE_LEGACY_SIGNAL_ALERTS` | `core/scheduler.py:1009` | 0 | eski alert yolu | gozlem: set degil | 0 |
| `FINPILOT_ENABLE_SHADOW_SCORECARD` | `distribution/jobs.py:809,813` | 0 | golge skor karti; rank etkisi yok | gozlem 1 | 0 |
| `FINPILOT_ENABLE_SCAN_LLM_SUMMARY` / `_SCAN_SUMMARY_ALERT` | `scanner/scan_summary.py:106` / `:243` | 1 / 0 | LLM ozeti kendi siralamasini kullanir (`scan_summary.py:30-49`); export rank'ine etkisi yok | gozlem 1 / 0 | 0 / 0 |
| `FINPILOT_ENABLE_PREMIUM_BRIEF` | `distribution/jobs.py:262` | 0 | icerik | UNKNOWN | 0 |
| Diger env: `FINPILOT_MAX_POSITION_ADV_FRACTION` | `scanner/execution_policy.py:49` | modul sabiti | cap -> reject | UNKNOWN | - |
| Diger env: `FINPILOT_MIN_FULL_SCAN_RATIO`, `FINPILOT_MIN_USABLE_SCAN_RATIO` | `distribution/scan_contract.py:15,20` | 0.9, 0.5 | export gecerliligi -> yayin kapisi | UNKNOWN | - |
| Diger env: `FINPILOT_DIST_MIN_UNIVERSE_FOR_DRAFT`, `FINPILOT_ALERT_MAX_PER_RUN`, `FINPILOT_DRL_GATE` | `distribution/jobs.py:774,815`; `agents/alert_agent.py:115`; `core/scheduler.py:696` | 100 / 5 / 0 | taslak tetigi / alert sayisi / DRL kapisi | UNKNOWN | - |

- 8.2 kisa cevap (brief metni bana verilmedi; 8.2 "flag production durumu + etki kaniti" olarak yorumlandi): (a) Yayin sirasini fiilen degistirebilen flag'ler: CONVICTION_TIERS (grade), SQUEEZE_FACTOR (legacy + grade girdisi), EXECUTION_POLICY / PORTFOLIO_ADV_LIMIT / MAX_POSITION_ADV_FRACTION (filtre), LEGACY_COMPOSITE_RANKING (set edilirse). (b) Yalniz composite'i degistirenler: EDGAR_CATALYST, LOTTERY_FADE, OVERNIGHT_GAP, FRED_MACRO, SENTIMENT. (c) Gozlenmis ama kodda referanssiz: NEWS. (d) Gozlem disi ama veride aktif: OVERNIGHT_GAP, CONVICTION_TIERS. PRIOR etki calismalari SCR-05'te.
- Label: SUPPORTED (statik kod) + MEASURED (telemetri alanlari, 2026-10-05..19 dosyalari). Test dosyasi adedi, flag adinin testte gectigini gosterir; etkinin dogrulandigini gostermez.
- Sinirlamalar: f-string ile kurulan flag adlari ve `web/`, `scripts/` disi dizinler taranmadi; scan anindaki kod surumu HEAD ile ayni varsayildi.
- Alternatif aciklama: telemetri alanlari (`score_feature_flags`) env yerine baska bir varsayilandan uretilmis olabilir; kod (`score_engine.py:243-250` civari `score_feature_flags`) env okudugu icin dusuk olasilik.
- Sonraki adim: container env'inin tam listesini (degerleri degil, yalniz flag adlari/0-1) bir insan operatorle yeniden gozlemek; NEWS ve FUNDAMENTALS'in tuketicisini salt-okunur izlemek.
- Kategori: NEEDS_MORE_DATA (production durumu) + FIX_CANDIDATE (gozlem listesi ile telemetri celiskisi raporlanmali).

### SCR-03 - `composite_score` saklanan bilesenlerden yeniden uretilebiliyor (99.88%), ama yalnizca satira yazilmis flag'lerle; gozlenen flag seti ile %55.7

- Priority: P2
- Konum: `scanner/score_engine.py:compute_recommendation_score:99-190`, `compute_recommendation_strength:378-396`, `MAX_RECO_SCORE=16.5` (24); `scanner/evaluate.py:518-549`.
- Veri: `data/shortlists/shortlist_202610*.csv` 125 dosya; en yeni 120 dosya kullanildi (`shortlist_20261005_1602.csv` .. `shortlist_20261019_1308.csv`); dosya basina SHA-256 `data/SCR_shortlist_manifest.csv` (manifest SHA-256 `de888351bedd97ee6bcc23f25602d73b5dd62f650a016c1a0e8e8d7e9fd40a48`). Sema: 3 farkli kolon seti (119 kolon: 116 dosya; 113 kolon: 4 dosya). Dosya basina satir medyan 199, max 200.
- Yontem: `score_input` / `score_component_breakdown` / `score_feature_flags` kolonlari `ast.literal_eval` ile okundu; formul HEAD kodunun aynasi (script icinde `raw_score`, `strength`). `score_input` olmayan 2,965 varsayilan satir (composite=0, ranking=0, `execution_confidence=Tier 0`) disarida -> n=17,333.
- Sonuc:
  - V0 (saklanan `recommendation_score` -> 0-100 esleme): 17,333/17,333 (100%) birebir.
  - V1 (gozlenen flag'ler: squeeze/catalyst/lottery=1, overnight=0; macro=1; sentiment yok): 9,662/17,333 (55.7%). Uyumsuzluk nedeni: `flags_differ` 7,671 (satir telemetrisinde `overnight_gap=true`), `macro_ne_1` 116; sentiment 0; aciklanamayan 0.
  - V2 (satira yazilmis flag'ler + bilesenden cikarsanan macro carpani + breakdown sentiment): composite 17,313/17,333 (99.88%); ham skor saklanan `recommendation_score` ile <=0.0015 farkla 17,333/17,333.
  - Kalan 20 uyumsuzluk: ham skor eslesirken int yuvarlama siniri (.5) etrafinda, 3 ondalikli bilesen yuvarlamasindan cikarsanan macro hatasi (HYPOTHESIS).
  - Cikarsanan macro carpani: 15,483 satirda 1.00; 0.95-1.11 arasi sapmalar kucuk faktorlu satirlarda yuvarlama ile tutarli (HYPOTHESIS; gercek FRED carpani saklanmiyor -> NOT_MEASURABLE).
  - Regime gate: composite'i degistirmez (`score_engine.py:regime_gate_mult:357-375` yalniz pozisyon carpani) -> uyumsuzluk kaynagi degil.
  - `legacy_quality_score` yeniden uretimi: NOT_MEASURABLE - `atr_pct` kalici yazilmiyor (yalniz `atr` kolonu var); test edilebilen satir 0.
- n: 17,333 satir / 120 dosya. Label: REPRODUCED (composite, satir flag'leri ile) ; MEASURED (V1 orani).
- Sinirlamalar: dosyalar <=200 satirlik parti ciktilari, tam-evren scan degil; scan anindaki kod surumu dogrulanmadi; `sentiment` bileseninin breakdown anahtar adi okunmadi (`sent` alt dizesi ile arandi).
- Alternatif aciklama: overnight telemetrisi hatali olabilir; ancak V2 eslesmesi (99.88%) telemetrinin formulle tutarli oldugunu gosterir.
- Sonraki adim: `atr_pct`'nin persist edilmesi (legacy'nin yeniden uretilebilmesi icin) Level B oneri; macro carpaninin satira yazilmasi.
- Kategori: FIX_CANDIDATE (persist eksigi) + KEEP_AS_IS (composite formulu tutarli).

### SCR-04 - `composite_score` dusuk cozunurluklu ve top-k'da yogun esitlikli; fiili rank alani (`ranking_score`) neredeyse esitliksiz

- Priority: P2
- Konum: `scanner/score_engine.py:378-396` (int 0-100); `scanner/score_engine.py:193-221` (3 ondalik); tie-break: `distribution/snapshot_builder.py:408` stabil `sort` + `scanner/evaluate.py:819` `as_completed`.
- Veri/yontem: SCR-03 ile ayni 120 dosya; esitlik payi = top-k satirlarindan degeri dosyada >=2 kez gecenlerin orani (azalan, mergesort). Dosya bazli degerler: `data/SCR_shortlist_per_file.csv`.
- Sonuc (MEASURED):

| Alan | Havuz n | Farkli deger | q0/q10/q25/q50/q75/q90/q99/q100 | Dosya basina farkli (medyan, min-max) | Top-10 esitlik payi (medyan, max) | Top-50 esitlik payi (medyan, max) |
|---|---|---|---|---|---|---|
| `composite_score` | 20,298 | 85 | 0 / 0 / 2 / 14 / 38 / 51 / 67 / 84 | 54.5 (1-68) | 0.50 (1.00) | 0.78 (0.94) |
| `ranking_score` | 20,298 | 11,762 | -7.914 / 0.0 / 6.614 / 14.596 / 35.071 / 50.808 / 62.236 / 76.359 | 165 (1-195) | 0.00 (0.60) | 0.00 (0.60) |

  - Yayin anahtari (`_sort_key` tam tuple) esitligi: public satiri olan 16 dosyanin hepsinde top-10/top-50 esitlik payi 0.
  - Top-50 kume ortusmesi (composite'e gore vs ranking'e gore): medyan 0.84 (min 0.02, max 0.94).
  - `ranking_score == 0.0` olan public satir: 0 (`or` zinciri dususu gozlenmedi).
  - q10=0 her iki alanda: 2,965 varsayilan satirin (14.6%) etkisi.
- Tie-break kurali (kod): acik ikincil anahtar yok; stabil sort giris sirasini korur, giris sirasi `as_completed` tamamlanma sirasidir -> esitlikte deterministik olmayan sira (SUPPORTED, kod). Composite'e gore siralayan tuketiciler (or. `api/routers/scan.py:258-262` `score_floor` uyarisi, `finpilot_score` girdisi `scan.py:128-133`) bu esitliklerden etkilenir.
- n: 20,298 satir / 120 dosya. Label: MEASURED (tanimsal istatistik; getiri hesabi yok).
- Sinirlamalar: dosyalar parti ciktisi; ranking max 0.60 esitlik payi muhtemelen kucuk/varsayilan-satirli dosyalardan (incelenmedi).
- Alternatif aciklama: composite'in 85 seviyesi int yuvarlamanin dogal sonucu; ranking'in esitliksizligi 3 ondalikli surekli girdilerden (ATR%, RVOL) gelir.
- Sonraki adim: composite'in bir siralama amacli kullanilmasi planlaniyorsa ham `recommendation_score` (3 ondalik) kullanimi arastirilmali (RESEARCH_NEXT).
- Kategori: KEEP_AS_IS (yayin rank'i) + RESEARCH_NEXT (composite tuketicileri).

### SCR-05 - PRIOR: skor -> sonraki getiri monotonlugu desteklenmiyor; PRIOR set cogunlukla composite/proxy uzerinde, fiili rank alani icin dogrudan test bulunamadi

- Priority: P1
- Kaynak: yalniz PRIOR raporlar (yeniden calistirilmadi); satirlar `grep_search` ile okundu. PRIOR raporlar "OOS" terimini kullaniyor; D7 (2026-10-16) uyarinca burada hicbiri out-of-sample sayilmaz.

| PRIOR kaynak (file:line) | Ifade (ozet) |
|---|---|
| `reports/research_x_h2_score_direction_2026-09-21.md:8,26` | H2a verdict `NOT_SUPPORTED`; Q1-Q5 medyan farki 0.541675, komsu ters cift 2/4, kova Spearman -0.6 |
| `reports/research_x_h4a_resolution_compression_2026-09-21.md:10,27` | `COMPRESSION_SUPPORTED` (SCR-04'teki 85 seviyeli composite ile tutarli) |
| `reports/research_x_h4b_ranking_mapping_2026-09-21.md:9,117` | `MAPPING_DEPENDS_ON_ADDITIONAL_INPUTS`; 39,986 satir, betimsel Pearson 0.887466 / Spearman 0.884258 (proxy vs composite) |
| `reports/research_x_h4c_information_loss_2026-09-22.md:13,14,42` | `INFORMATION_LOSS_NOT_SUPPORTED`; production ranking hakkinda iddia yok (satir 14); yardimci monotonluk ihlali payi 0.41573 |
| `reports/research_x_h4d_measure_2026-09-22.md:33` | Endpoint verdict bolumu var; icerik okunmadi (UNRESOLVED) |
| `reports/walk_forward_scoring_validation_2026-09-08.md:13,39` | Hicbir component baseline'i tekrarlanabilir gecmiyor; baseline Spearman ~0; Top-20 hit %55-75 tutarsiz; confidence LOW |
| `reports/scoring_ablation_audit_2026-09-08.md:13` | 4 flag-kapili component baseline'i anlamli iyilestirmiyor; catalyst UNVALIDATED (factor=0.0); lottery/overnight kova davranisi skora katkiya donusmuyor |
| `reports/feature_flag_evidence_summary_2026-09-08.md:17` | SQUEEZE: n_gun=23, null-baseline +0.0338; kanit yetersiz |
| `reports/b2_0_flag_user_facing_impact_report_2026-09-23.md:11,18,48` | Toplam verdict `INCOMPLETE`; yalniz davranissal fark; export'ta 1,508 satirda 4 skor flag'i true (SCR-02 OVERNIGHT bulgusuyla tutarli) |
| `reports/flag_impact/flag_impact_report_ADDENDUM_2026-09-23.md:37` | CONVICTION_TIERS ve ALPHA_V2 yeniden kurulamadi; "etki yok" genellemesi yapilamaz |
| `reports/baseline_score_buckets_2026-09-09.csv` | Bu rolde acilmadi (UNRESOLVED) |

- Sentez: PRIOR kanit composite (ve proxy) icin pozitif monotonlugu desteklemiyor. Yayin sirasini belirleyen `legacy_quality_score` + grade icin bu PRIOR sette ayri bir monotonluk testi bulunamadi; H4C satir 14 bunu acikca kapsam disi birakiyor. Degerlendirme ile production rank alani arasinda bosluk var (UNRESOLVED; baska bir raporda olabilir).
- Label: PRIOR. Kategori: RESEARCH_NEXT.

### SCR-06 - `data/scanner_config.json` kelly anahtarlari yalniz yaziliyor, runtime'da okunmuyor; 4->1 degisimi scheduler yazicisiyla tutarli

- Priority: P2 (risk-kontrol gecerliligi; degisiklik Risk katmani = Level C)
- Konum: `core/scheduler.py:908-939` (drawdown -> `_new_kelly = round(max(0.1, kelly_fraction * 0.70), 4)` satir 913; yazim 936-939); `core/scheduler.py:800-823` (optimizer `best_params` -> ayni dosya, `_updated_cycle` 818); `_cycle_count = 0` (36), `_cycle_count += 1` (1055); scheduler parametresi `kelly_fraction: float = 0.5` (471) -> scan'e aktarim (515); `scanner/evaluate.py:230` default 0.5, `:556-563` `calculate_dynamic_position(..., kelly_fraction)`, `:674` `kelly_fraction`, `:734` `dyn_kelly_pct`. Not: kelly blogu brief'in tahmin ettigi 790-830'da degil, 908-939'da; 790-830 optimizer yazimidir.
- Veri: `data/scanner_config.json` SHA-256 `dabb8a14ce7a608da2dae7ed470bcf28354267f2b99e7b7e90130d180b151206` (working tree); anahtarlar yalniz `kelly_fraction=0.35`, `_kelly_reduced_cycle=1`. `git diff`: yalniz `_kelly_reduced_cycle` 4->1 (+ dosya sonu newline yok); dosyaya son dokunan commit `b780b10` (2026-09-23).
- Yontem: script `repo_grep("scanner_config")` (tum `*.py`; reports/web/data/docs/site/gizli/venv haric) + `git diff/log` (salt-okunur).
- Sonuc:
  - JSON okuyucu: 0 (yalniz `core/scheduler.py` yazicilari; tests'teki eslesmeler farkli bir nesne olan `scanner.config` modulu). Kalici `kelly_fraction` ne secimi ne sizing'i etkiliyor (SUPPORTED; statik yokluk).
  - 0.35 = round(max(0.1, 0.5 x 0.70), 4): scheduler'in her seferinde 0.5 default ile calistigi (geri besleme yok, bilesik azalma yok) durumla birebir tutarli.
  - `_cycle_count` modul degiskeni, surec basinda 0 -> `_kelly_reduced_cycle=1` WARN/STOP dalinin bir surec yeniden baslatmasindan sonraki ilk dongude calistigini gosterir; HEAD'deki 4 onceki bir surecin 4. dongusu. 4->1 degisimi runtime yazicisiyla tutarli (SUPPORTED; zaman damgasi dogrulanmadi). `json.dump(indent=2)` sonda newline yazmaz -> diff'teki "No newline" ile tutarli.
  - Cagri parametresi `kelly_fraction` (dosya degil) sizing'e gider; `risk_data["position_size"]` -> `position_cap` -> `position_cap_reject_reason` -> yayin filtresi zincirine etkisi UNRESOLVED (`calculate_risk_management` argumanlari okunmadi).
- Yorum: kod yorumu ("Persist ... so the effect survives restarts", satir 921) ile davranis celisiyor: drawdown sonrasi azaltma kalici degil (CONTRADICTED, kod duzeyi).
- Label: SUPPORTED. Kategori: FIX_CANDIDATE (Level C - insan karari) ; runtime state'in git'te izlenmesi P3.

### SCR-07 - Onceden tanimli ablation sorulari (brief 8.4; calistirilmadi)

Ortak sabit kurallar: yalniz kilitli olmayan / holdout olmayan bolumler; sonuclar asla OOS etiketlenmez (D7); ayni scan satirlari ve otorite dokumanindan onceden secilmis tek bir etiket tanimi (brut getiri; net veya expectancy denmez); birincil metrik = scan-tarihi basina skor ile ileri brut getiri arasindaki Spearman, tarihlerin ortalamasi, `signal_date` kume bootstrap (B=2000, sabit seed) %95 GA; ikincil = tarih basina top-10 eksi scan medyani brut getiri. Karar kurali onceden: fark GA'si zaman bolmesinin her iki yarisinda da 0'i dislarsa "SUPPORTED", aksi halde "NOT_SUPPORTED". Public liste cok kucuk (2 haftada 22 satir) -> tum skorlanmis satirlar kullanilir. On kosul: `atr_pct` ve macro carpaninin persist edilmesi (aksi halde A2/A3 NOT_MEASURABLE).

| ID | Soru | Karsilastirma |
|---|---|---|
| A1 | Siralama alani: `legacy_quality_score` vs `composite_score` vs ham `recommendation_score` - hangisinin scan ici Spearman'i daha yuksek? | Ayni satirlar, tarih eslemeli fark |
| A2 | Legacy icindeki lottery (-1.5) ve overnight (-1.0) terimleri (flag'den bagimsiz) cikarilirsa top-10 uyeligi ve degisen isimlerin brut getirisi farkli mi? | Rank displacement + eslesik fark |
| A3 | Legacy icindeki squeeze (+0.5) terimi acik/kapali | A2 ile ayni kural |
| A4 | Grade-oncelikli siralama vs saf `ranking_score` siralamasi (`selection_eligible` satirlarda) | Top-k uyelik ve brut getiri farki |
| A5 | Composite eklentileri (EDGAR/LOTTERY/OVERNIGHT/FRED/SENTIMENT) kapali: yalniz `position_size_gated` / `score_floor` uyari dagilimi degisimi | Getiri iddiasi yok; dagilim farki |
| A6 | Deterministik ikincil anahtar (`symbol`) vs mevcut tie-break | Ayni girdi iki farkli sirada -> top-k Jaccard |

- Label: HYPOTHESIS (soru tasarimi). Kategori: RESEARCH_NEXT.

## Dogru calisan kisimlar

- Composite formulu satir telemetrisiyle tutarli: V0 17,333/17,333, V2 17,313/17,333 (REPRODUCED).
- `ranking_score`, flag default'u ile tutarli olarak 20,298/20,298 satirda `legacy_quality_score` (MEASURED).
- Yayin anahtari public satirlarda esitlik uretmedi (16 dosya) ve `or` zinciri dususu gozlenmedi (MEASURED).
- Satir telemetrisi (`score_input`, `score_component_breakdown`, `score_feature_flags`) composite denetimini mumkun kiliyor; shadow ledger reddedilen satirlari da yaziyor (`api/routers/scan.py:153-190`, SUPPORTED).

## Cevaplanamayan sorular

- `FINPILOT_ENABLE_FUNDAMENTALS` (`scanner/features.py:598`) ve `FINPILOT_ENABLE_REGIME_WEIGHTS` scan yolunda neyi degistiriyor?
- Cagri parametresi `kelly_fraction`, `position_cap` uzerinden yayin filtresini etkiliyor mu?
- Scan export'unun satir sirasi ve icerigi shortlist ile ayni mi; yayinlanan snapshot'lar `_public_candidate` aynasiyla birebir mi? (snapshot dosyalari bu rolde okunmadi)
- 2026-10-16 sonrasi container env'i; scan basina gercek FRED macro carpani.
- `legacy_quality_score` (+grade) icin skor -> ileri getiri monotonlugu (PRIOR'da bulunamadi).
- `reports/baseline_score_buckets_2026-09-09.csv` ve H4D endpoint verdict icerigi.

## Sinirlamalar

- Shortlist dosyalari <=200 satirlik parti ciktilari; 125 dosyanin en yeni 120'si; scan anindaki kod surumu HEAD varsayildi.
- Statik tarama f-string flag adlarini ve `web/`, `scripts/` dizinlerini kapsamaz.
- Getiri/outcome hesaplanmadi; hicbir sonuc OOS etiketlenmedi.
- Paylasilan terminal cakismasi: `prior` modu iki kez calistirildi; ilk denemede gorunen cikti baska bir rolun betiginin `KeyboardInterrupt` traceback'iydi (komutum o sureci kesmis olabilir - orkestratore bildirilir); ikinci denemenin dosyasi yalniz baska bir rolun ciktisini icerdi ve kullanilmadi. PRIOR satirlari bunun yerine `grep_search` ile alindi; FUNDAMENTALS / risk / regime_weights kontrolleri elde edilemedi.
- Satir numaralari grep ile dogrulanmis ankrajlardan sayildi; aralik sonlarinda +/-1 olabilir.
- Brief 8.2 / 8.4 metni bu role verilmedi; yorumlandi.

## Ek: komutlar

1. Kod izleme: `grep_search` (ranking alanlari, sort cagrilari, flag okumalari, `def` satirlari) ve `read_file` (`scanner/evaluate.py:470-720,761-850`; `scanner/score_engine.py:1-402`; `scanner/features.py:178-250`; `distribution/snapshot_builder.py:30-215,380-420`; `distribution/jobs.py:170-222`; `api/routers/scan.py:96-262`; `core/scheduler.py:796-826,880-950`).
2. `python.exe -B reports/scanner_intelligence_audit_v1_2026-10-19/scripts/SCR_r5_analysis.py main` (30.2 s) -> `data/SCR_flag_registry.json`, `data/SCR_shortlist_per_file.csv`, `data/SCR_shortlist_manifest.csv`; ayni komutta `git diff -- data/scanner_config.json` ve `git log -n 3 -- data/scanner_config.json`.
3. `... SCR_r5_analysis.py prior` (2 deneme; cikti terminal cakismasi nedeniyle kullanilmadi).
4. `grep_search` PRIOR raporlarda `verdict|sonuc|karar|conclusion|spearman|monoton|kendall`.
5. `git -C C:\Users\meric\Borsa status --porcelain=v1 -uall` (salt-okunur; sonuc donus mesajinda).

<!-- END -->
