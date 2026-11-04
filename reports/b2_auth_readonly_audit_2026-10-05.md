# B2-AUTH - Salt-okunur denetim ve insan karar paketi

Date: 2026-10-05 | Version: 1.0 | Owner: research / governance
Layer: Governance, Product authorization, Engineering, Content, Risk & Compliance
Audit execution: Level A. Authorization and compliance decisions: Level C, PENDING.
Status: AUDIT_DELIVERED / HUMAN_DECISION_PENDING. Production action: NONE.
This is evidence and a decision proposal, NOT a new authority or publication permission.

## 1. Karar ozeti

**Oneri:** toplu flag enable/disable yapma; once D1-D7 kararlarini ayri kaydet.
Denetim tamamlanmasi, flag'lerin bilimsel olarak dogrulanmasi veya yayin izni degildir.

- Kullanici, B2-AUTH salt-okunur denetimini ve sonraki bagimlilik kararinin
  gecerliligini acikca onayladi. Kilitli B2-0 section 9 tarihsel kalir ve otomatik
  distribution engeli degildir. Bu aciklama yayin izni vermez.
- Ilk envanter 360, son CLI kontrolu 361 kaynak dosyasi; 22 ENABLE flag'i ve
  3 iliskili kontrol incelendi. Worktree gozlemler arasi degisebilir.
  Yerel dosyada ENABLE grubunda 14 ON, 4 OFF, 4 UNSET var.
- Bugunku uretim surecinin flag degerleri UNKNOWN. Yerel dosya, audit kabugu,
  tarama artifact'i, snapshot sureci ve uzak servis birbirine esit varsayilmadi.
- B2-0 verdict of record INCOMPLETE; verification mismatch metodolojik kaynak
  sinifi belirsizligidir. CONVICTION etkisini bu denetim yeniden siniflandirmadi.
- Secilmis 8 kilitli artifact SHA_MATCH. Kapali deney veya counterfactual kosulmadi.
- Yerel son gonderim 2026-09-09T11:42:18Z; latest snapshot ve web dosyasi 09-09.
  Bunlar uzak Telegram/Vercel/Render durumunun bugunku denetimi degildir.
- 10-05 CSV sayimi: 11 dosya, 1,612 satir, 1,601 benzersiz sembol.
  Ayrica onceki onizlemenin 9 batch'i 1,601 satir / 1,601 benzersiz sembol.
  Batch birlesimi tek bir tam tarama veya yayin kaniti degildir.
- P0: yerel scanner ekraninda yonlendirici islem-sinyali dili goruldu.
  P0: sabit grade degerleriyle kalibrasyon/yeniden-kalibrasyon iddialari arasinda
  mevcut kanit boslugu var. Otomatik uyumluluk onayi veya metin degisikligi yok.

Authority pointers: [YONERGE](../YONERGE.md),
[core](../_instructions/00-core.md), [authority map](../docs/INDEX.md),
[decision log](../docs/governance/decision-log.md).
Onayli bagimlilik aciklamasi sicilde 2026-10-05 B2-AUTH opening entry'dedir.
Onceki program ayrimi sicilde 2026-09-23 research-program restructuring entry'dedir.

## 2. Kapsam ve yontem

Karar sorusu: hangi flag/kontrol hangi kullanici yuzeyini veya yayin kapisini
etkiler; bu davranis icin hangi acik yetki ve provenance kaniti bulunur?
Predictive basari, getiri, yeni esik veya optimal flag kombinasyonu sorulmadi.

Uygulama: [stdout-only toplayici](../scripts/b2_auth_readonly_audit.py).
Tarama kapsami scanner/, distribution/, api/, core/, scripts/, web/src/ ve
kokteki Python dosyalari. Python AST, literal os.getenv/os.environ.get/subscript
okumalarini isaretler; yorum, atama ve ilgisiz .get() okuyucu sayilmaz.
Alias desteklenir; dinamik anahtarlar, dinamik scope/shadowing ve Python-disi
okumalar icin tam semantik ispat sunulmaz. Dosya bulunmasi branch'in calistigini
ispatlamaz. Kaynak dosyalari hash'lenir; uretim modulleri import edilmez.

.env dotenv_values(interpolate=False) ile okunur; ortama yuklenmez.
Yalniz kapsam flag adlari ve 0/1/UNSET/non-binary-redacted durumu cikar.
Secrets, kullanici kimlikleri, mesaj icerikleri ve diger ortam degerleri basilmaz.
Audit process degerleri bu kosuda UNSET; uretim sureci gibi sunulmaz.

SQLite mode=ro&immutable=1 ve query_only ile okundu; ensure_tables(),
distribution_status(), publish, preview builder veya uretim endpoint'i cagrilmadi.
Okuma aninda distribution.db WAL yoktu. WAL olsaydi immutable okuma yalniz base
file kaniti sayilacakti. Eszamanli islemler nedeniyle bu, tum servisler icin
transactional bir zaman-kesiti degildir; tarih/sayim ve hash'ler gozlem anina aittir.

Son kontrolde en yeni kaynak [partial publication](../distribution/partial_publication.py)
idi. Dar kaynak okumasi ayri partial snapshot path'i, scope/coverage metadata'si
ve yazim fonksiyonu gosterdi; hicbiri cagrilmadi. Bu eszamanli kaynak icin runtime,
queue entegrasyonu veya insan publication yetkisi bu raporla dogrulanmis degildir.
Mevcut full-export kabul kapisi kaniti partial edition'a otomatik aktarilmaz;
D6 herhangi bir yeni partial yayin yetkisi vermez. Flag sayilari ve manifest'teki
28 hash son kontrolde degismedi. Collector tekrarlanabilirligi ayni son worktree
uzerinde kontrol edildi; worktree'nin denetim boyunca sabit kaldigi iddia edilmez.

Paylasilan `http://127.0.0.1:3001/dashboard/scanner` sekmesi yalniz read_page ile
okundu. Tiklama, reload, login, scan veya export yapilmadi. Ekranda 401 olayi ve
oturum acilmamis durum goruldu. Bu lokal arayuz gozlemidir, uretim runtime kaniti degil.

Yetki aramasi: tum mevcut decision-log, ilgili 07-24 PARK karari, 08-12 runtime
kaydi, 09-08 scoring raporlari, 09-21 geri cekme/runtime kayitlari ve 09-23 B2/P0
kararlari; YONERGE ve kaynak call-site'lari. Butun tarihsel sohbetler, uzak env
panelleri veya bagimsiz insan arsivi denetlenmedi. Bu nedenle NOT_LOCATED,
UNAUTHORIZED veya NOT_PERFORMED ile es anlamli degildir.

## 3. Bulgular - oncelik sirasiyla

| ID | Seviye | Bulgu / kanit | Karar etkisi |
| --- | --- | --- | --- |
| F01 | P0 | Yerel browser scanner'da yonlendirici sinyal basligi; [scanner mapping](../web/src/app/dashboard/scanner/page.tsx#L268) ve [summary ureticisi](../scanner/scan_summary.py#L98) ayni dil ailesini uretiyor | Uyumluluk incelemesi D1; flag veya metin kendiliginden degismez. Uzak yayin kanitlanmadi |
| F02 | P0 | [_CONV_PROB sabitleri](../scanner/features.py#L179), [glossary kalibrasyon iddiasi](../distribution/glossary.py#L23), [grade aciklamasi](../distribution/glossary.py#L151), [brief tarihsel oran dili](../distribution/templates.py#L105) | C1/C2/C3 onceki karar notuna bagli; kalibre predictive olasilik kaniti sunulamaz |
| F03 | P1 | Bugunku calisan API/container flag haritasi, build/tree ve config fingerprint'i bu denetimde yok | D2; .env ON = runtime ON veya yetkili ON sonucu yasak |
| F04 | P1 | [config_sha](../distribution/snapshot_builder.py#L38) snapshot surecinin FINPILOT_ENABLE prefix'li ortamini ve git kisa SHA'sini hash'ler; non-flag config, dirty tree, scan sureci ve moduller kapsam disi | Hash eslesmesi tam runtime rekonstruksiyonu degildir; D2/D3 |
| F05 | P1 | broadcast_queue ve tg_delivery_log config_sha saklamiyor; [queue_metadata](../distribution/jobs.py#L247) da tasimiyor | Mesaj, karar, snapshot ve scan konfigurasyonu arasindaki zincir eksik; B4 girdisi D3 |
| F06 | P1 | ALPHA_V2 hem squeeze uretimi hem risk alanlarini kontrol ediyor; bu girdiler tarihsel olarak tam sakli degil | Yalniz composite ablation sonucuyla enable karari verilemez; D4 |
| F07 | P1 | Lottery/overnight composite flag'leri [legacy kalite fonksiyonunun](../scanner/score_engine.py#L193) ungated girdilerini tamamen kesmez | OFF = yayindaki faktor etkisi OFF degil; D4 icin kaynak-kanal ayrimi gerekir |
| F08 | P1 | SHADOW_SCORECARD [subprocess baslatip cache/skor karti gunceller](../distribution/jobs.py#L610) | Skor degistirmemesi read-only/risksiz oldugunu ispatlamaz; veri-yazim yetkisi D5 |
| F09 | P1 | Yerel export/snapshot/web 09-09; bugunku batch'ler eksik evren; queue pending=0, approved=0, sent=23 | Yeni yayin izni/bugun gonderildi sonucu yok; D6 operasyon kaniti ayri |
| F10 | P1 | Controller full-state listesinde ECON/B2 yok; PROGRAM_STATE hardcoded alanlar tasiyor | Bos conflict listesi denetim PASS degil; ayri Level B D7 |
| F11 | P2 | [ranking_method](../scanner/evaluate.py#L833) override branch'inden bagimsiz sabit etiket | Override acilacaksa metadata dogrulugu ayrica gerekli; bugun override actigina kanit yok |
| F12 | P2 | EARLY_TIER/FUNDAMENTALS/NEWS icin kapsamda literal flag reader yok | Flag'i kaldirmak/temizlemek ayri konfig karari; ilgili feature ailesi tamamen yok denemez |

F01/F02 bir uretim degisikligine donusturulmedi. Risk & Compliance konularinda
AI kendisi yeni istisna, yayin engeli veya izin tanimlamaz; insan karari gerekir.
Finding onceligi bu audit'in triage'idir, yeni risk politikasi degildir.

## 4. Flag ve yetki matrisi

Asagidaki adlar FINPILOT_ENABLE_ prefix'i kisaltilarak yazilmistir.
Default, kaynakta gorulen literal default'tur. UNSET efektif OFF ispatlamaz;
host/container env, API loader ve cache etkileri ayri incelenmelidir.
Yetki ifadeleri audit kanit sinifidir, yeni resmi lifecycle/authority state degildir.

| Flag | Local / default | Sahip kaynak | Davranis kanali | Bulunan yetki kaniti |
| --- | --- | --- | --- | --- |
| ALPHA_V2 | 1 / 0 | [features](../scanner/features.py#L172), [risk engine](../scanner/risk_engine.py#L204) | Squeeze girdisi, grade/ranking dolayli bagimlilik, risk alanlari | Flag-specific enable onayi bu incelemede NOT_LOCATED; B2 kaynak boslugu biliniyor |
| CONVICTION_TIERS | 1 / 0 | [features](../scanner/features.py#L183) | Grade/prob; entry_ok sonrasi etiketleme | Grade urun sozlesmesinde var; bu, calibration veya her deployment icin enable onayi degil |
| EXECUTION_POLICY | 1 / 0 | [execution policy](../scanner/execution_policy.py#L32) | ADV yoksa feasible/selection karari | Sozlesme alanlari YONERGE section 2; enable kaydi NOT_LOCATED; risk yetkisi ayri |
| PORTFOLIO_ADV_LIMIT | 1 / 1 | [execution policy](../scanner/execution_policy.py#L36) | Notional cap/reject; public eligibility | Default ON; flag-specific enable kaydi NOT_LOCATED; default ile insan onayi karistirilmaz |
| LEGACY_COMPOSITE_RANKING | 0 / 0 | [score engine](../scanner/score_engine.py#L238) | ranking_score kaynagi | YONERGE legacy quality kuralina uyumlu dosya durumu; 08-12 runtime OFF insan kaydi tarihsel |
| SQUEEZE_FACTOR | 1 / 0 | [features](../scanner/features.py#L415), [score engine](../scanner/score_engine.py#L34) | Girdi uretimi + composite; ALPHA_V2 alternatifi var | Enable onayi NOT_LOCATED; composite/published etkisi ayrilmali |
| LOTTERY_FADE | 1 / 0 | [score engine](../scanner/score_engine.py#L62) | Composite ceza; legacy girdi ayri | Tarihsel arastirma bulgulari var, flag-specific deployment onayi NOT_LOCATED |
| OVERNIGHT_GAP | 1 / 0 | [score engine](../scanner/score_engine.py#L73) | Composite ceza; legacy girdi ayri | Ayni: arastirma enable yetkisi degil |
| EDGAR_CATALYST | 1 / 0 | [catalyst](../scanner/catalyst.py#L64), [score engine](../scanner/score_engine.py#L45) | Kaynak/cache + composite/catalyst relief + bilgi endpoint'i | 09-03 cache refresh karari flag'i ACMADI; genel enable kaydi NOT_LOCATED |
| FRED_MACRO | 1 / 0 | [score engine](../scanner/score_engine.py#L89), [macro](../core/macro_regime.py#L50) | Macro/carpi ve market-context ailesi | Enable kaydi NOT_LOCATED; endpoint/macronun branch calismasi ispatlanmadi |
| DISTRIBUTION | 0 / 0 | [jobs](../distribution/jobs.py#L44) | Draft/publish/scheduler | YONERGE insan onayli queue yolu; [manual script](../scripts/publish_now.py#L23) process-local 1. Audit yeni yayin yetkisi vermez |
| PREMIUM_BRIEF | UNSET / 0 | [jobs](../distribution/jobs.py#L258) | Premium draft olusturma | Enable kaydi NOT_LOCATED; premium yayin/erisim ayri karar |
| SCAN_LLM_SUMMARY | 1 / 1 | [summary](../scanner/scan_summary.py#L106) | Summary top secimi, metin ve LLM confidence | Flag-specific onay ve confidence validation NOT_LOCATED; public Grade ile ayni estimand degil |
| SCAN_SUMMARY_ALERT | 0 / 0 | [summary](../scanner/scan_summary.py#L239) | Snapshot queue disinda dogrudan Telegram yolu | Queue/human approval politikasi var; dogrudan yayin icin ozel yetki NOT_LOCATED |
| LEGACY_SIGNAL_ALERTS | 0 / 0 | [scheduler](../core/scheduler.py#L1009) | Legacy alert ailesi | Queue politikasi var; istisna enable yetkisi NOT_LOCATED |
| SHADOW_SCORECARD | 1 / 0 | [jobs](../distribution/jobs.py#L610) | Subprocess/cache/skor karti | 08-05 izole altyapi/test kaydi var; surekli production writer enable onayi ayri |
| EODHD_BARS | UNSET / 0 | [fetcher](../scanner/data_fetcher.py#L1043) | Bar saglayici secimi, anahtar da gerekli | 09-10 implementasyon default OFF; bugunku activation onayi NOT_LOCATED |
| SENTIMENT | UNSET / 0 | [sentiment](../scanner/sentiment.py#L48) | Sentiment kaynagi/skor/metin ailesi, anahtar da gerekli | Enable kaydi NOT_LOCATED |
| REGIME_WEIGHTS | UNSET / 0 | [weights](../core/regime_weights.py#L40) | Deneysel agirlik kanali | EXPLICIT PARK POLICY FOUND: 07-24 Karar D |
| EARLY_TIER | 1 / reader yok | [watch-tier referansi](../scanner/watch_tier.py#L158) | Literal flag reader bulunmadi | Enable yetkisi NOT_LOCATED; davranis yorum satirindan cikartilmadi |
| FUNDAMENTALS | 1 / reader yok | [features aciklamasi](../scanner/features.py#L598) | Literal flag reader bulunmadi | Enable yetkisi NOT_LOCATED; feature fonksiyonunun varligi reader degil |
| NEWS | 1 / reader yok | Kaynak AST/isim envanteri | Literal flag reader bulunmadi | Enable yetkisi NOT_LOCATED |

Iliskili kontroller:

| Kontrol | Local / default | Kanit / karar |
| --- | --- | --- |
| FINPILOT_DRL_GATE | UNSET / 0 | [scheduler](../core/scheduler.py#L696); 07-24 Karar D ile PARK; runtime UNKNOWN |
| FINPILOT_INSTRUMENT_BASELINE | UNSET / 0 | [instrumentation](../scanner/instrumentation.py#L57); implementasyon/test PASS = surekli calisma ispatlamaz |
| FINPILOT_ALERT_ON_SCAN | 1 / 1 | [summary](../scanner/scan_summary.py#L245); dogrudan gonderim icin SCAN_SUMMARY_ALERT da gerekli |

## 5. Uctan uca bagimlilik haritasi

1. **Tarama:** data kaynaklari -> features/risk -> entry_ok -> conviction ->
   execution/selection -> ranking kaynagi -> satir export'u.
2. **Grade uyeligi:** [public candidate](../distribution/snapshot_builder.py#L123)
   grade, selection_eligible, execution_feasible ve cap-reject alanlarini kullanir.
   Grade icin conviction_tier, yoksa tier CONFIRM/TRIGGER fallback'i vardir.
   Tarihsel 09-09 export'unda tier yoktur; genel OFF etkisi her dataset'e genellenmez.
3. **Siralama:** [sort key](../distribution/snapshot_builder.py#L99) grade,
   execution, probability ve ranking alanlarini kullanir. Sadece composite degil.
   Sayisal 0 icin truthy fallback ve son tie/input-order provenance'i de ayri borctur;
   H4 yeniden acilmadi, gecmis tuple tahmin edilmedi.
4. **Metin:** [rationale](../distribution/rationale.py),
   [prob-band](../distribution/rationale.py), [templates](../distribution/templates.py)
   ve [glossary](../distribution/glossary.py). Summary LLM output'u ile bu
   deterministic snapshot rationale yolu ayni sey degildir.
5. **Draft:** [job_draft](../distribution/jobs.py#L155) distribution gate,
   guncel tarih ve export completeness'i kontrol eder; queue'ya snapshot identity ekler.
6. **Insan karari:** [broadcast.decide](../distribution/broadcast.py#L111)
   pending -> approved/rejected. Queue state, tum flag konfigurasyonunun bilimsel
   veya yonetisim onayi anlamina gelmez.
7. **Publish:** [job_publish](../distribution/jobs.py#L283) approved-unsent,
   snapshot identity ve delivery uzerinden ilerler; web push basarili gonderime bagli.
   Bu fonksiyonlar bu denetimde CAGIRILMADI.
8. **Alternatif yuzey:** dashboard scanner API satirlarini ayri mapping ile gosterir;
   [risk alanlari](../web/src/app/dashboard/scanner/page.tsx#L303) snapshot aday
   metinleriyle ayni kapsam degildir. LLM/direct-alert/legacy-alert yollarinin
   kapsam, onay ve dil denetimi ayri tutulmalidir.

## 6. Provenance ve gunluk durum

09-09 snapshot stamp: a5e0d8b7c9d5@ff9658a.
Bugunku yerel FINPILOT_ENABLE extract'i tarihsel ff9658a ile hash'lendiginde
ff924d235a31@ff9658a; yalniz belgelenmis manual-process DISTRIBUTION=1 farki
hesaba katilinca a5e0d8b7c9d5@ff9658a elde edildi. Gercek env degistirilmedi;
kombinasyon aramasi veya counterfactual deney degil, belgelenmis damga uzlastirmasidir.
Sonuc HASH_EQUALITY_ONLY: host, scan ortaminin tumu veya temiz tree ispatlanmaz.

API [elle env loader](../api/main.py#L17) mevcut; kabuktan gelen degeri ezmez.
publish_now dotenv kullanir ve distribution'i process-local ezer. Docker compose
env_file + environment kullanir. Render deklarasyonu ayri env kaynagidir;
uzak panel degerleri bu audit'te okunmadi. API loader ile dotenv'in mevcut ENABLE
extract'i arasinda fark bulunmadi; gelecekte quote/interpolation/duplicate handling
semantigi ayni varsayilamaz. 09-21 'env yuklenmiyor' iddiasi sicilde zaten GERI
CEKILMIS; bugunku audit bu geri cekmeyi teyit eder, yeni kok-neden iddiasi degil.
09-21 insan runtime kaydinda 18 flag adi gorulmesi her birinin degerini veya
10-05 runtime state'ini ispatlamaz; 08-12 ranking OFF teyidi de tarihsel kayittir.

Yerel 09-09 latest ve published export: scan_complete=true, universe=1812,
1,801 satir / 1,801 benzersiz sembol. Grade A=3, B=4, C=3.
1,508 satirda dort score_feature_flags=true, 293 template satirinda alan yok/null.
Bu dort flag icin tarama-artifact gozlemidir; ALPHA/CONVICTION/full environment
kaniti degil. atr_pct_daily ve config_sha yok; ranking alanlari mevcut; tier yok.

TR/EN latest snapshot ve web dosyasinda date, snapshot_id, candidate_hash,
scan_id ve config_sha metadata'si ayni; aday sayisi 10, web_context 10.
Bu audit tam mesaj/aday-icerigi reconstruction yapmadi, metadata eslesmesi kontrol etti.
Yerel queue: expired=12, rejected=3, sent=23; pending/approved satiri yok.
delivery/queue config_sha kolonlari yok. Uzak teslimat kanali yeniden sorgulanmadi.

10-05 onizleme batch'leri: Grade B=1, C=1; diger 1,599 satir gradesiz.
11 CSV'nin tumunde ranking/conviction/execution alanlari mevcut, fakat
atr_pct_daily, scan_id, config_sha, raw short_interest/float_shares kolonlari yok.
Kolon varligi tum satirlarin non-null veya semantik olarak dogru oldugunu ispatlamaz.
Bugunku .env'de FULL_UNIVERSE_SIZE/MIN_FULL_SCAN_RATIO/MIN_USABLE_SCAN_RATIO
override'i tanimli degil. [Completeness kontrolu](../distribution/scan_contract.py)
kaynak default'larinda 1,601 benzersiz sonuc minimum full-result sayisini karsilamaz;
runtime override UNKNOWN. Ekrandaki onizleme veya tarih etiketi bunu tam export yapmaz.
Burada yeni gate, tolerans indirimi, full export yazimi veya yayin yapilmadi.

## 7. Bilimsel kanit siniri ve kapali hatlar

Kaynaklar: [09-08 ablation](scoring_ablation_audit_2026-09-08.md),
[09-08 walk-forward](walk_forward_scoring_validation_2026-09-08.md),
[09-23 flag-impact addendum](flag_impact/flag_impact_report_ADDENDUM_2026-09-23.md),
[B2-0 raporu](b2_0_flag_user_facing_impact_report_2026-09-23.md), decision log.
09-08 arastirmalari canonical EOD-only dataset uzerinde kendi split/hedefleriyle
composite ailesini inceler; exact historical public Grade tuple'inin predictive
dogrulamasi degildir. Korelasyon, dis akademik kanit veya kod test PASS'i,
flag deployment yetkisi ya da calibrated probability kaniti yerine kullanilmaz.
Eski ozetin 'default OFF vs local ON = muhtemelen kasitsiz drift' yorumu
yetki/niyet kaniti degildir. 'Shadow risksiz' yorumu cache yazimlarini kapsamaz.

| Hat | Korunan kayit | Bu audit'in yaptigi |
| --- | --- | --- |
| H4 | FROZEN / CLOSED; historical tuple provenance insufficient | Olcum veya yeniden acma yok |
| NS-1 | Sicilde kapali; kendi protokol/verification sinirlari var | Rerun veya verdict transferi yok |
| RX-CAPTURE-1 | Sicilde kapali; production approval degil | Exit kuralini production'a tasima yok |
| B1 / ECON | Overall FURTHER_VALIDATION_SUPPORTED; E1_t5 INCONCLUSIVE | Hash kontrolu, ekonomik kanit upgrade'i yok |
| B2-0 | INCOMPLETE / VERIFICATION_MISMATCH (source-class interpretation) | Kilitli belge/runner/result degismedi |
| B2-1 | DRAFT v2, NOT LOCKED | Recovery deneyi calismadi |
| B2-2 | CONDITIONAL | Counterfactual acilmadi |
| B2-full | NOT OPENED | Bu audit ile otomatik acilmadi |
| B4 provenance | SPEC OPEN, implementation ayri izin | D3 girdileri; implementasyon yok |
| P0 Grade audit | DRAFT; C1/C2/C3 karar notu var | Yeni calibration deneyi veya sayisal deger degisikligi yok |

B1 mevcut sonuclarinda pozitif medianla birlikte her iki mean @0.55 negatiftir;
E1_t5 stress temporal reversal vardir. Gercek maliyet, liquidity ve replication
bosluklari kapanmadi. [B1 raporu](research_x_capture_1_econ_2026-09-23.md)
bir ekonomik/production dogrulama degildir; verification'in tum verdict gate'lerini
ve provenance'i kapsadigi bu audit'te iddia edilmedi. Median-degeneracy yorumunu
E1_t5'e genelleyen metin ve +3 breakeven etiketi buradan duzeltilmedi.
'Locked OOS hic acilmadi' controller/envanter genellemesi ayri tarihsel V2
path-aware kaydiyla ayni scope degil; bu audit OOS acmadi veya yeniden olcmedi.

## 8. Insan karar paketi - tamamami PENDING

Asagidakiler oneridir. Bu is Level C kararlar icerir ve AI tarafindan uygulanamaz.
Karar sahibi Meric. Uygulama sahipleri rol olarak onerilir; atanmis kisi/tarih yok.
Secenek secilmeden tarih veya yetki varmis gibi kayit yapilmaz.

| ID | Insan karari | Onerilen yol / alternatif | Uygulama ve kapanis kaniti |
| --- | --- | --- | --- |
| D1 | Scanner/summary ve grade-probability metinlerinin uyumluluk kapsami | Onceki [C1/C2/C3 notuyla](p0_grade_wording_level_c_decision_note_2026-09-23.md) birlikte, kanittan guclu metinleri ayri onayli degisiklikle duzelt; sayisal grade sabitlerini audit oncesi otomatik degistirme. Alternatif: hangi metnin hangi gerekceyle kalacagini acikca kaydet | Product/content owner; onayli diff, TR/EN/DE tum yuzey envanteri, lint/render/snapshot testleri. Uyumluluk istisnasini AI yaratamaz |
| D2 | Bugunku runtime flag haritasini ve rollout yetkisini nasil belgeleyecegiz? | Yetkili operator gercek API/container PID/build/tree ve yalniz allowlisted 0/1 flag degerlerini salt-okunur toplasin. Yeni surecte python/os.getenv veya .env okumak ana sureci ispatlamaz | Operations owner; tarih, host rol etiketi, deployment SHA/tree, flag haritasi, override kaynagi. Secrets veya tum env dump YOK; bu audit restart/deploy yapmaz |
| D3 | B4 persistence kapsaminda hangi provenance alanlari zorunlu? | Scan-time config fingerprint ve source/build/tree; gunluk ATR ve raw squeeze girdilerinin PIT kaynagi; ranking tuple/tie-order; queue/delivery config baglantisi | Engineering owner; ayri onayli B4 spec, privacy/security inceleme, schema/contract tests, gelecekteki tek-run trace. Gecmis kayip girdileri uydurma veya H4 reopen YOK |
| D4 | Her davranissal flag'in retention/enable/disable yetkisi | Tekil scope+gerekce+kanit+operator+rollback+review tarihiyle karar; toplu dokuz-flag karari verme. CONVICTION/ALPHA unresolved kaynaklar ve risk kontrolleri ayri. Kullaniciya gorunen metin duzeltmesi her zaman yeni predictive deney gerektirmez | Product/risk owner; her flag icin explicit decision entry, ilgili diff/contract test ve gerekiyorsa ayri kilitli arastirma. B2-1/B2-2 otomatik kosmaz |
| D5 | Shadow/LLM/direct-alert yollarinin operasyon yetkisi | Shadow'u data-writer olarak kaydet; kaynak/cache yan etkisini izle. LLM confidence'i calibrated Grade ile esitleme. Queue disi gonderim istisnasi varsa acik insan onayi ve identity/security/lint kapsamiyla tanimla | Ops/content owner; veri-yazim kapsam ve backout, scheduler/subprocess provenance, metin-kapi kaniti. Bu audit hicbir yola activation vermedi |
| D6 | Yeni edition icin operasyon kabul kapisi | Mevcut yetkili yayin akisi altinda guncel, tek-run, complete export ve insan edition onayi kanitlarini getir. Eski B2 hukumunden otomatik engel veya bu rapordan otomatik izin turetme | Operations owner; current-date export, universe/unique/usable, snapshot+candidate hash, queue karar kaydi, delivery identity, web artifact eslesmesi. Mevcut gate'i dusurme/--force tavsiyesi YOK |
| D7 | Controller scope/hardcoded state borcu | ECON/B2 lifecycle ve explicit log/artifact provenance'i icin ayri Level B duzeltme onerisi; bos conflict listesini global PASS sayma | Tooling owner; approval, source-of-truth reconciliation tests, sha mismatch/conflict/lock-order testleri; controller authority uretmez |

Kapanis iki farkli durumdur:

- **Audit delivery:** kaynak/kanit matrisi, insan karar paketi, kontrollu collector
  testleri ve preserved SHA kontrolleri tamamlandi.
- **Governance closure:** D1-D7 icin kabul/ret/defer karari, uygulama sahibi,
  tarih/review tarihi ve gerekiyorsa uygulama kaniti sicile kaydedilmeli.
  Bugun HUMAN_DECISION_PENDING. Authority B2-AUTH CLOSED veya production approved
  sonucunu bu rapor tek basina uretemez.

## 9. Dogrulama ve yeniden uretim

```powershell
python -B scripts/b2_auth_readonly_audit.py
python -B -m pytest tests/test_b2_auth_readonly_audit.py -q -o addopts='' -p no:cacheprovider
python -m ruff check scripts/b2_auth_readonly_audit.py tests/test_b2_auth_readonly_audit.py
python -B scripts/research_governance_controller.py --json
```

Collector fixture testleri: 7 PASS. Odaklar: literal reader sinifi, aliases,
yorum/atama dislama, nonbinary/interpolation redaction, .env'yi yuklememe,
determinism, kaynak/import/yazim yapmama, log mention != authorization,
parse-error gorunurlugu ve associated control kapsami.
Bu, test edilen fixture'larin uyumudur; tum uretim branch'lerinin veya
yetkilendirmelerin bagimsiz verification PASS'i degildir. Lint PASS; editor
diagnostics new script/tests icin hata gostermedi. Yeni paket kurulmadi.

Controller kosusu v0.2-READONLY; 7 full-state line, bos conflict listesi.
ECON/B2 coverage yok. Hardcoded PROGRAM_STATE ve result-presence -> CLOSED
mantigi nedeniyle lifecycle/authorization karari controller'a birakilmadi.

SQLite tekrar-okuma SQL'i (yalniz immutable/read-only connection):

```sql
SELECT status, COUNT(*) FROM broadcast_queue GROUP BY status;
SELECT kind, brief_date, sent_at FROM broadcast_queue
WHERE status='sent' ORDER BY sent_at DESC LIMIT 3;
SELECT MAX(ts) FROM tg_delivery_log WHERE ok=1;
PRAGMA table_info(broadcast_queue);
PRAGMA table_info(tg_delivery_log);
```

Git worktree baslangicta dirty idi; main origin/main'den 3 commit ilerideydi.
Baska kullanici degisiklikleri korunuyor. Commit, push, deploy, flag/env,
snapshot/CSV/cache/DB degisikligi bu audit tarafindan yapilmadi.
Audit ciktilari: bu rapor, yeni collector ve test dosyasi; sicile ek kayitlar.
Runtime veriler git'e alinmadi. Audit ve testler ayni ajan tarafindan yazildi;
bagimsiz reviewer onayi bu raporla verilmis sayilmaz.

## 10. Integrity manifest - gozlem anina ait secilmis kanit

locked_hashes, sicildeki beklenen degerlerle eslesen **secilmis 8** dosyadir;
'butun kilitli arastirmalar denetlendi' iddiasi degildir. source_hashes bugunku
worktree kanitidir; deployed-code hash'i degildir. Kalici otorite degil.

```json
{
  "locked_hashes": {
    "reports/b2_0_flag_user_facing_impact_preregistration_2026-09-23.md": "fe4ceab1294a2799f034e4d4cc1c0f27b55ef1378d8ff577960c181f7a2133c0",
    "data/backtest_out/b2_0_flag_user_facing_impact_2026-09-23.json": "4585361e8eac395fa6ef382889a59cc20acff9f9ab0dfcb0f60b5d16c0313925",
    "data/backtest_out/b2_0_independent_verification_2026-09-23.json": "d76eec3d522b7ba076473d8d73e18dd70833ad5609d85d67a958a560afd037ca",
    "reports/research_x_capture_1_economic_review_preregistration_2026-09-23.md": "6b210259b4dbaac4d3e2df64faaaf34f700a1b80a1b283dbb479ea27fdb212fb",
    "data/backtest_out/research_x_capture_1_econ_2026-09-23.json": "04a43868e794ec871d41fea4389316c6f425a177184b8229a1332c2309467afd",
    "data/backtest_out/rx_capture_1_econ_independent_verification_2026-09-23.json": "9b8b5b86c93eedad802a520d20b9ee3608896f77a67e6b7ea385611e95a9dcf5",
    "docs/governance/research_governance_controller_spec_v1.md": "a3ea327b47f489f59867cf463b2efd2b0c59c9e0923a49ecdb27836a7e0bb19b",
    "data/backtest_out/full_universe_enriched_eod_only.csv": "87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad"
  },
  "source_hashes": {
    "api/main.py": "f9d013db199b10d006c5bebf47b1837aa9e0dd1306e61c86ad80c3ce206cdc63",
    "scanner/features.py": "2ce4f067785d43f32214678c85dde57a8f11341889e04886abcc5f221c88c2f6",
    "scanner/evaluate.py": "4313a22dea0fcdf4a44603b1bde3cbb9aba2bbdb9d67af85e80539ae355c2754",
    "scanner/score_engine.py": "9455d5205eb476261373700a71252062b44f85f209ebb1d693fc677151ba4a3f",
    "scanner/risk_engine.py": "c6719f2779ac65e5ee0dc42d38fdae2599cf859b4d6ccb32cc59d32ebdf44cd9",
    "scanner/execution_policy.py": "d1597fcdb0c0c526adb0414e962773ce1cb46de154b1b1da7a328d3cb302b6a9",
    "scanner/scan_summary.py": "512e528c04ff23636a1a030a4c8520a1138f94e28058894b088c1003b6e2c18a",
    "scanner/instrumentation.py": "ac3443467fbeea9a23b584c8be00c33779c9487ab8498c24877a264767c7055e",
    "distribution/snapshot_builder.py": "47b92eaa8115b500b13f4023f0cc27afbc60a206610f5f86a2cb8268ca292552",
    "distribution/scan_contract.py": "dc0d04d4d572d925b771412cad55f6682ffdb1b79eda4d0798803fd5a7eec5c8",
    "distribution/jobs.py": "52df5978371a04242a63b449978dff85841c98c2969ede98b27a8f07dd0cb7aa",
    "distribution/templates.py": "d4d1c77d030730efaa715696afa31b81cc50d5df9da3e790ae0571e39b64ee24",
    "distribution/glossary.py": "9a863163cec2ec1877de6201ec9702c77ca9621f3e19676c4dcec16454042b8b",
    "distribution/rationale.py": "3302bca9f29ce4ed2ed63fb54eda9ef551f10c7f6d0d530a6db0362f9f31c3c2",
    "distribution/broadcast.py": "323480ac37ab85c1de0ab55a50b5b29d54229a1a9a882dc99a6b6dd483e3eb07",
    "distribution/prepublish_gate.py": "13f27e65e834e108a263cd028f6f0a1156abd18d74671ae54bbc7a76addb4960",
    "scripts/publish_now.py": "0e954e6149ec1c18d7afe4bf88e12cb0210a0221f1d3986e13d25aa979e60446",
    "core/scheduler.py": "82a2590fc9f436dd5c57bc4d4a1d10190689c2de6806d215778456a4a9d98cec",
    "web/src/app/dashboard/scanner/page.tsx": "f32283b732c73bec7a1f0cb850db715a005716b3cb2d31b7c01d9d40cf436cc0",
    "scripts/research_governance_controller.py": "b841d4fced2a6f1f83bb4a0d10fd0651fca9a10af0adf7dae6fcb22da027c7e5"
  }
}
```

Confidence: HIGH kaynak/kolon/hash gozlemleri; MEDIUM sinirli kayit taramasinda
yetki bulunmamasi; UNKNOWN bugunku uzak runtime, deployment, bilimsel
calibration ve ekonomik uygulanabilirlik. Bu belirsizlikler gizlenmedi.

## 11. Son durum

AUDIT_DELIVERED. HUMAN_DECISION_PENDING. B2-AUTH governance closure NOT_GRANTED.
No flag action. No publication. No experiment. No locked-document amendment.
Next authorized action is human review of D1-D7, not an automatic next research run.
