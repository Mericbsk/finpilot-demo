# FinPilot — Merkezi Karar Logu

_CLAUDE.md Bölüm 3 formatı: her önemli karar buraya, dağınık dosyalara gömülmez._

[2026-08-13] — FinPilot/Finsense repo ve doküman hijyeni denetimi tamamlandı ve bağımsız doğrulandı (Level A; migration pending — Meriç onayı bekliyor)
Layer: Governance / Engineering / Content / Research
Level: A (salt-okunur audit ve öneri); önerilen taşıma/rename Level B, silme/geri-dönüşsüz işlem Level C
Bağlam: `docs/2026-08-06-DOSYA-DUZENI-MASTER-PROMPT.md` master prompt'uyla üretilen denetim (`reports/repo_document_hygiene_audit_2026-08-13.md`) ikinci bir yürütücü (Cowork) tarafından kanıta karşı doğrulandı. Ölçümler birebir teyit edildi: Borsa kök 81 py / 30 md, Finsense 33 py / 37 md; `Finsense/academy/export_lessons.py`, `Borsa/archive/FinanceAcademy/academy/seed_content.py`, `Borsa/api/routers/academy.py:37` (`from academy.orchestrator import`) ve `scripts/publish_web.py` mevcut ve doğrulandı.
Bulgu: (P0) `docs/INDEX.md` makine-manifestindeki `academy-content` authority'si repo-qualified DEĞİL; Borsa `academy/` (7 py, API runtime) ile Finsense `academy/` (33 py, içerik fabrikası + export) AYRI kod/veri sınırlarında yaşıyor. Reviewer notu: bu yalnız doküman belirsizliği değil, iki paralel academy kod tabanı arasında KOD KAYMASI (drift) riski; 33-e-7 kapasite asimetrisi Finsense'in kanonik, Borsa/academy'nin eski köprü olduğunun güçlü (kesin değil) sinyalidir. Bu bir bakım/governance borcudur ama LANSMAN BLOKÖRÜ DEĞİLDİR (web /academy statik `academy_lessons.json` artifact'ini okur). Root sprawl (81 kök py, ~37 research adayı; 30+ doküman) migration adayıdır; hiçbir dosya 'dead' ilan edilmedi (seed_content_en = aktif ama ayrı workflow).
Değişiklik: Hiçbir dosya taşınmadı/silinmedi/yeniden adlandırılmadı. Denetim raporu + fazlı migration önerisi hazırlandı (Faz 0 = lansman sırasında yalnız karar hazırlığı; Faz 1 = lansman sonrası onaylı git mv batch'leri).
Etki: Üretim scanner/distribution/execution/broker/web-runtime/publish davranışı DEĞİŞMEDİ. Academy authority/cutover kararı VERİLMEDİ. `web/public/academy_lessons.json` release-artifact olarak kabul edildi.
Durum: pending — Meriç onayı bekliyor. En yüksek öncelikli tek karar: Academy authority'yi repo-qualified netleştirmek (bridge retained vs cutover) — lansman sonrası. Bu kayıt migration/authority değişikliği DEĞİLDİR.
Kanıt: reports/repo_document_hygiene_audit_2026-08-13.md; docs/2026-08-06-DOSYA-DUZENI-MASTER-PROMPT.md; docs/INDEX.md; Borsa/api/routers/academy.py:37; Finsense/academy/export_lessons.py; scripts/publish_web.py.

---

[2026-08-13] — 5-yeni-soru fizibilite taraması: Soru-2 (485 flagged sembol sınıflandırması) için ucuz bir ayırt-edici bulundu (%56'sı yuvarlak split-oranına uyuyor); Soru-5 (abstention bağımsız-veri retest) TAKVİM-ENGELLİ (mevcut veri zaten train/calib/valid'in tamamını tüketmiş); Soru-1/3/4 dış-veri veya insan-zamanı gerektiriyor, bu oturumdan yapılamaz (Level A, fizibilite+ilk-bulgu)
Layer: Research / data
Level: A
Bağlam: Meriç'in onayladığı 5 yeni-soru listesinden ("sürpriz", "485-sembol sınıflandırması", "execution/capacity", "kullanıcı-gerçeği", "abstention bağımsız-veri") hangisinin bu oturumdan, ek veri/insan olmadan ilerletilebileceği tarandı.
1) SORU 5 (abstention bağımsız-veri) — BLOCKED, takvim: `production_candidate_validation_2026-08-12.json/abstention_independent_split` train=40+calibration=16+validation=25=81 gün kullanmış; `full_universe_enriched.csv`'nin c2c_5d-dolu tarih aralığı (2025-09-11→2026-07-31, 82 gün) BUNU NEREDEYSE TAMAMEN KAPSIYOR. Şu an genuinely-yeni (train/calib/valid'de hiç kullanılmamış) bir tarih aralığı YOK — 5-günlük ileri-getiri hesaplanabilmesi için takvimin ilerlemesi (haftalar) gerekiyor. Bu, sabırla beklenmesi gereken bir kapı, bugün zorla açılamaz.
2) SORU 2 (485 sembol sınıflandırması) — İLK UCUZ AYIRT-EDİCİ bulundu: her flagged sembolün en-büyük tek-günlük sıçraması, yuvarlak split-oranlarına (2x,3x,...,100x, log-ölçekli %12 tolerans) ne kadar yakın diye test edildi. Sonuç: 272/485 (%56,1) yuvarlak-orana uyuyor (örn. YHC +10.608%≈100x, COOK +5.469%≈50x) — muhtemelen GERÇEK ama fiyat-cache'inde AYARLANMAMIŞ reverse-split. Kalan 213/485 (%43,9) hiçbir yuvarlak orana uymuyor (örn. FFAI +1.542.757%, MIMI +1.027.400%, EDBL +190.809%) — muhtemelen VERİ-HATASI/bad-print, gerçek bir corporate-action değil. Bu, tam-kesin bir sınıflandırma DEĞİL (yalnız en-büyük sıçramaya bakıyor, provider-seviyesi doğrulama yok) ama ucuz bir ilk-ayrıştırma: %56'lık kısım "düzeltilebilir" (split-adjust), %44'lük kısım muhtemelen "sadece dışlanabilir" (veri-hatası, düzeltilecek gerçek bir olay yok).
3) SORU 1 (sürpriz/event) ve SORU 3 (execution/capacity) — BLOCKED, dış-veri: event-feed / observed spread-ADV-fill verisi bu ortamda yok, `full_universe_enriched.csv`'de de yok (grep doğrulandı: `dollar_adv`/`spread_bps` gibi alanlar tarihsel export'ta YOK — yalnız CANLI shortlist'te var, geriye-dönük değil).
4) SORU 4 (PR1/PR7 kullanıcı görüşmesi) — BLOCKED, insan-zamanı: script hazır (`reports/user_research_kit_2026-08-10.md`), yalnız Meriç'in görüşme yapması gerekiyor.
Karar: Bu turda yalnız Soru-2'nin ucuz ayırt-edicisi ilerletildi (bulgu yukarıda, EXPLORATORY — provider-seviyesi doğrulama olmadan kesin sınıflandırma sayılmaz). Diğer 4 soru resmi olarak BLOCKED (2'si dış-veri, 1'i insan-zamanı, 1'i takvim) — bu oturumdan daha fazla ilerletilemez, sahte-ilerleme üretilmeyecek.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ.
Kanıt: bu turun bağımsız script'i (kaydedilmedi, çıktı yukarıda); `data/backtest_out/price_cache_integrity_audit_2026-08-11.json`; `data/backtest_out/production_candidate_validation_2026-08-12.json/abstention_independent_split`.

---

[2026-08-13] — KONTROL TURU #6: repo-durumu + decision-log bütünlüğü + CANLI SHORTLIST'İN KENDİSİYLE DOĞRUDAN AMPİRİK TEYİT — `ranking_score`=`legacy_quality_score` satır-satır birebir eşit (`ranking_method`="legacy_quality"), ayrıca `score_component_breakdown`/`score_component_total`/`recommendation_score` alanları CANLI ÇIKTIDA ZATEN VAR — "export'a eklenmeli" önerisi "yeni alan hesapla"dan "zaten hesaplanan alanı research pipeline'a bağla"ya düşürüldü (Level A, kontrol)
Layer: Research / governance
Level: A
Bağlam: Meriç'in "tekrar kontrolleri sağla, nelere baktık/ne yapmalıyız/nelere dikkat etmeliyiz" talebiyle rutin bir bütünlük+doğrulama turu yapıldı.
1) DECISION-LOG BÜTÜNLÜĞÜ: 824 satır, bugünün (08-12) 8 girdisi de sırayla ve bozulmadan mevcut (grep ile doğrulandı) — üzerine yazma/çakışma yok.
2) REPO DURUMU: son ~40 dakikada yalnız rutin canlı-tarama çıktıları değişmiş (`data/distribution/scan_export_*partial*.json`, `data/shortlists/shortlist_202608 13_*.csv` — 2-5 dakikada bir yeni dosya, canlı scanner aktif çalışıyor). `reports/`/`research/` altında YENİ dosya yok — paralel süreç şu an duraklamış görünüyor.
3) EK DOĞRULAMA (fırsatçı, bu turda bulundu): en-güncel canlı shortlist (`data/shortlists/shortlist_20260813_1146.csv`, 198 satır, GERÇEK üretim çıktısı) doğrudan okundu. Sonuç: HER satırda `ranking_score` == `legacy_quality_score` (birebir, örn. RRR: ikisi de 57,073; CZR: ikisi de 65,631) ve `ranking_method` sütunu her satırda literal `"legacy_quality"` string'i taşıyor. Bu, önceki iki girdideki (.env dosyası + Meriç'in container-içi kontrolü) bulguyu ÜÇÜNCÜ, EN GÜÇLÜ kanıt-katmanıyla (doğrudan canlı veri, kod/config çıkarımı değil) doğruluyor. `composite_score` alanı da aynı satırlarda mevcut ama `legacy_quality_score`'dan sistematik olarak farklı (bazı satırlarda büyük fark, örn. HWKN: composite=3 vs legacy=11,14) — gün-içi rank-korelasyonun yüksek (0,867) olması satır-satır aynı oldukları anlamına gelmiyor.
4) YENİ, ÖNEMLİ-UCUZLAŞTIRICI BULGU: canlı shortlist CSV'sinde `score_component_breakdown`, `score_component_total`, `recommendation_score`, `score_input`, `score_feature_flags` alanları ZATEN MEVCUT (üretim zaten hesaplıyor ve yazıyor). Önceki girdide ("Score yeniden-tasarım önceliklendirmesi") bunu "export'a eklenmesi gerekiyor" (yeni instrümantasyon) olarak önermiştim — YANLIŞ ÇERÇEVE: iş, YENİ bir hesaplama eklemek değil, ZATEN CANLIDA ÜRETİLEN bu alanları `full_universe_enriched.csv`'yi besleyen araştırma pipeline'ına (`research/score_replay.py` veya eşdeğeri) DAHİL ETMEK. Bu, tahmin edilenden çok daha ucuz bir data-repair kalemi.
Karar: Hiçbir üretim/araştırma-sonucu değişmedi; bu tur salt doğrulama ve önceki önerinin maliyet-tahminini düzeltme. Güncellenmiş öncelik: `research/score_replay.py`'ye (veya export-üreten script'e) canlı shortlist/scan_export JSON'larından `ranking_score`,`legacy_quality_score`,`score_component_breakdown`,`score_component_total` alanlarını JOIN eden bir adım eklemek — yeni hesaplama gerekmiyor, sadece zaten-var-olan veriyi araştırma export'una taşımak.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ.
Kanıt: `data/shortlists/shortlist_20260813_1146.csv` (bu turda okundu, 198 satır); decision-log grep-bütünlük kontrolü (bu turda).

---

[2026-08-12] — CANLI SUNUCUDA TEYİT EDİLDİ (Meriç): finpilot_api container'ında `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0` → `legacy_composite_ranking_enabled()`→`False` → `ranking_score`=`legacy_quality_score` KESİNLEŞTİ; "KRİTİK DÜZELTME/BÜYÜK BULGU" zincirinin son açık maddesi kapandı (Level A, kanıt-teyidi)
Layer: Research / product / governance
Level: A
Bağlam: Bu oturumun kod-seviyesi bulgusu (`ranking_score`'un `.env` dosyasına göre `legacy_quality_score`'a eşit olduğu, dolayısıyla canlı ürünün Grade A/B/C sıralamasının `composite_score` değil `legacy_quality_score` kullandığı) tek bir sınırlamayla bırakılmıştı: repo-dosyası (`.env`) seviyesinde doğrulandı ama ÇALIŞAN sürecin kendi ortam-değişkeni bu oturumdan sorgulanamamıştı. Meriç, `finpilot_api` container'ında doğrudan kontrol edip `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0` ve `legacy_composite_ranking_enabled()→False` sonucunu bildirdi.
Sonuç: Zincir artık UÇTAN UCA kesinleşti: canlı Grade A/B/C sıralaması ve web-context sıralaması (`distribution/snapshot_builder.py:99-116,179,408`) → `ranking_score` → `legacy_quality_score` (atr_pct+rvol+squeeze+lottery+overnight birleşimi) → bu oturumda geriye-dönük backfill+test edildi (`ranking_score_backfill_test.py`) → composite_score ile aynı "forward-bilgi yok" verdiktini veriyor (rho=+0,02, CI 0'ı içeriyor) AMA composite_score'un aksine seçimi rastgeleden ölçülebilir-kötü DEĞİL, nötr (medyan +0,33 vs rastgele +0,28).
Karar: "Score'un forward-öngörü gücü yok" sonucu artık canlı ürünün GERÇEKTEN kullandığı alan için de tam teyitli — bu program tarihinin en önemli dış-geçerlilik (external validity) boşluğu kapandı. "Seçim aktif zarar veriyor" iddiası ise composite_score'a özgü kalıyor; canlı ranking_score için bu iddia YOK (nötr sonuç). Bu ayrım, gelecekteki her türlü ürün/iletişim kararında (örn. "FinPilot'un mevcut sıralaması rastgeleden kötü mü" sorusuna cevap verirken) referans alınmalı.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ — bu yalnızca hangi alanın hangi bulguyla ilişkilendirileceğine dair bir doğrulama.
Kanıt: Meriç'in canlı `finpilot_api` container kontrolü (bu turda bildirildi); önceki 2 girdi (`scanner/evaluate.py`/`score_engine.py`/`distribution/snapshot_builder.py` kod-izi + `ranking_score_backfill_test.py` sonuçları).

---

[2026-08-12] — ranking_score/legacy_quality_score GERİYE-DÖNÜK BACKFILL VE TEST EDİLDİ (ek veri gerekmedi) — merkezi bulgu SARSILMADI, tersine İKİ BAĞIMSIZ SKOR FORMÜLÜYLE DE teyit edildi; composite_score'un rastgeleden ÖLÇÜLEBİLİR DERECEDE KÖTÜ olması ranking_score'da YOK (Level A, araştırma — önceki "kritik düzeltme" girdisinin kapanışı)
Layer: Research / quant
Level: A
Bağlam: Önceki girdide ("KRİTİK DÜZELTME/BÜYÜK BULGU") tespit edilen boşluk — canlı ürünün asıl kullandığı `ranking_score`/`legacy_quality_score` alanının hiç test edilmemiş olması — Meriç'in "bedava, mevcut veriyle" ilkesiyle hemen kapatıldı: `ranking_score_backfill_test.py`. `scanner/score_engine.py::compute_legacy_quality_score` formülü BİREBİR (satır-satır) kopyalanarak, mevcut export kolonlarıyla (regime, direction, score, atr_pct_real, rvol, squeeze_factor, lottery_factor, overnight_gap_factor — hepsi zaten export'ta) her satır için geriye-dönük hesaplandı. Yeni veri/backfill-altyapısı gerekmedi.
Sonuçlar (43.279 satır, 81 gün):
  **Test A (composite_score ile ne kadar aynı?):** gün-içi Spearman(legacy_quality_score, composite_score)=+0,867 (t=+97,2, n_gün=47, composite_score dolu olduğu satırlarda) — YÜKSEK KORELE. İki skor pratikte çoğunlukla AYNI adayları üst sıraya taşıyor.
  **Test B (c2c_5d ile forward-korelasyon, composite_score'la AYNI metodoloji):** legacy_quality_score ort-rho=+0,0195 (t=+0,94, boot-CI=[-0,042,+0,084], null-ort=-0,016) → **ÖLÜ**, composite_score ile TAM AYNI VERDİKT (composite_score: rho=-0,0277, t=-1,10, CI 0'ı içeriyor, aynı şekilde ölü). **Merkezi bulgu ("score'un forward-bilgisi yok") artık İKİ BAĞIMSIZ, YÜKSEK-KORELE AMA FORMÜL OLARAK FARKLI skor değişkeniyle teyitli — daha da sağlam.**
  **Test C (top-10 portföy, medyan-bazlı — KONTROL TURU #5 dersi uygulanarak ortalama DEĞİL medyan birincil alındı):** legacy_quality_score top-10 gün-medyanlarının-medyanı=+0,333 vs rastgele=+0,278 (istatistiksel olarak ayrışamaz, ~aynı) vs composite_score=-0,567 (rastgeleden daha kötü, önceki bulguyla tutarlı). Yani: composite_score seçimi RASTGELEDEN ÖLÇÜLEBİLİR DERECEDE KÖTÜ (bilinen bulgu), ama legacy_quality_score/ranking_score seçimi rastgeleden ne iyi ne kötü — NÖTR. (NOT: ortalama-bazlı ilk hesap legacy_quality_score için yanıltıcı şekilde pozitif çıkmıştı — +4,37% — bu, tam da KONTROL TURU #5'te öğrenilen mean/outlier-hassasiyeti örneği; medyana geçince kayboldu, doğru sonuç budur.)
Karar: Programın "score'un forward-öngörü gücü yok" merkezi sonucu GEÇERLİ ve şimdi iki bağımsız formülle DAHA GÜÇLÜ. Tek gerçek fark: composite_score'un seçimi aktif-olarak-rastgeleden-kötü iken, ranking_score/legacy_quality_score'un seçimi sadece bilgisiz (rastgeleyle aynı) — bu ayrım küçük ama pratik: eğer canlı ürün gerçekten legacy_quality_score/ranking_score kullanıyorsa (Meriç'in .env-teyidi hâlâ bekleniyor), "seçim aktif zarar veriyor" iddiası composite_score'a özgü kalır, ranking_score'a genellenemez. Kalan tek açık iş: Meriç/canlı-erişimli tarafın `.env`'deki `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING` değerini canlı süreçte teyit etmesi.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ.
Kanıt: `ranking_score_backfill_test.py` (bu turda yazıldı, repo köküne kondu); ek bash-tek-satır medyan-kontrolü (bu turda, kaydedilmedi, çıktı yukarıda).

---

[2026-08-12] — KRİTİK DÜZELTME/BÜYÜK BULGU: canlı ürünün GERÇEK sıralama alanı `composite_score` DEĞİL, `ranking_score`'dur (şu an = `legacy_quality_score`, `.env`'deki `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0` nedeniyle) — bu alan `full_universe_enriched.csv`'de HİÇ YOK ve bu programın 2 yıllık tarihinde HİÇBİR deney tarafından test edilmemiş; önceki girdideki "atr/rvol canlı formülde yok" iddiam bu yüzden YANLIŞTI, düzeltiliyor (Level A, kod-denetimi + öz-düzeltme)
Layer: Research / product / governance
Level: A
Bağlam: Meriç'in önceki girdideki iki "sürpriz" bulguya ("atr/rvol/dist_52w_high/risk_reward canlı formülde yok" ve "ağırlık-bütçesinin %60'ı test edilmemiş") daha derin bakma isteğiyle `scanner/evaluate.py` incelendi.
KOD-ZİNCİRİ (satır 661-724, 814-818): `evaluate.py`, HER taranan aday için ÜÇ farklı skor hesaplıyor ve HEPSİNİ döndürüyor: `composite_score` (=`compute_recommendation_strength`, benim şimdiye kadar test ettiğim alan), `legacy_quality_score` (=`compute_legacy_quality_score` — regime/direction/raw_score/**atr_pct**/**rvol**/squeeze/lottery/overnight'ı birleştiren AYRI bir formül), ve `ranking_score` = `_composite_score if legacy_composite_ranking_enabled() else _legacy_quality_score`. `legacy_composite_ranking_enabled()` → `os.environ.get("FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING","0")=="1"`. `.env` dosyasında bu değişken **`0`** — yani bugün `ranking_score` = `legacy_quality_score`'a EŞİT.
CANLI ÜRÜNDE HANGİSİ KULLANILIYOR: `distribution/snapshot_builder.py:99-116,179,408` — HEM "web context" satırları (`measurable.sort(key=_sort_key)`, satır 179) HEM de asıl GRADE A/B/C adayları (`graded.sort(key=_sort_key)`, satır 408) `_sort_key()` ile sıralanıyor; bu fonksiyon skoru `row.get("ranking_score") or row.get("legacy_quality_score") or row.get("composite_score") or row.get("score")` fallback-zinciriyle seçiyor — yani `ranking_score` (=`legacy_quality_score`) DOLU olduğu sürece BİRİNCİL alan, `composite_score` yalnız fallback. `distribution/prepublish_gate.py:37` de `ranking_score`'u zorunlu alan olarak listeliyor.
SONUÇ (kritik): `full_universe_enriched.csv`'de `ranking_score` VEYA `legacy_quality_score` kolonu YOK (header doğrulandı: yalnız `score`,`composite_score`,`finpilot_score` var). `research/score_replay.py` da bu alanı hesaplamıyor (grep, sıfır eşleşme). Yani: reverse-ranking, extension/exhaustion, Mirror Analysis, P0-P3, bu oturumun score-backward-looking bulgusu, score_component_decomposition.py — BU PROGRAMDAKİ HER TEK SCORE-DENEYİ, canlı ürünün asıl kullandığı alanı DEĞİL, ikincil/fallback bir alanı test etmiş.
ÖZ-DÜZELTME: Önceki girdideki "en-umut-verici 4 bileşen (atr/rvol/dist_52w_high/risk_reward) canlı formülde HİÇ YOK" iddiam YANLIŞTI — `atr_pct` ve `rvol` zaten `legacy_quality_score` içinde (1,5× ve 1,5× ağırlıkla) kullanılıyor VE bu, `ranking_score` aracılığıyla muhtemelen ŞU AN CANLI ÜRÜNÜN GERÇEKTEN KULLANDIĞI skor. `dist_52w_high` ve `risk_reward` hâlâ hiçbir skor formülünde yok (bu kısım doğru kalıyor).
ÖNEMLİ SINIRLAMA: `.env`'in canlı çalışan süreçle bire-bir aynı olduğu bu turda dosya-seviyesinde doğrulandı (repo'daki 5 farklı script `load_dotenv(ROOT/".env")` ile bu dosyayı yüklüyor) ama ÇALIŞAN sürecin ortam-değişkenlerini (systemd/process-env) bu turda DOĞRUDAN sorgulamadım — bu son %5'lik doğrulama BLOCKED (canlı sunucuya erişim bu oturumda yok).
Karar: Bu, programın en yüksek-öncelikli data-repair kalemi olarak yeniden sıralanmalı — Meriç'in önceki 2 sorusundan (soru 1: ranking_score backfill, soru 2: score_component_breakdown export) BİRİNCİSİ artık BİRİNCİ ÖNCELİK: (a) `.env`'in canlı sunucudaki gerçek değeriyle bu bulgunun doğrulanması (Meriç veya canlı-erişimi-olan taraf), (b) `research/score_replay.py`'ye `legacy_quality_score`/`ranking_score`'u hesaplayıp export'a ekleyen bir adım eklenmesi, (c) TÜM geçmiş score-negatif bulgularının `ranking_score` ile TEKRAR test edilmesi — mevcut "score bilgi taşımıyor" sonucu `composite_score` için EVIDENCE seviyesinde kalıyor ama `ranking_score`/`legacy_quality_score` için hâlâ test edilmemiş/UNKNOWN.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ — bu turda salt kod-okuma yapıldı. Ama bu bulgu DOĞRULANIRSA, bu programın "score'un forward-bilgisi yok" sonucunun canlı ürüne UYGULANABİLİRLİĞİ ciddi şekilde sorgulanır hale gelir.
Kanıt: `scanner/evaluate.py:661-724,814-818`, `scanner/score_engine.py:193-222,238-240`, `distribution/snapshot_builder.py:99-116,179,408`, `distribution/prepublish_gate.py:37`, `.env:56` (`FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0`), `research/score_replay.py` (grep, ranking_score/legacy_quality_score için sıfır eşleşme).

---

[2026-08-12] — Score yeniden-tasarım önceliklendirmesi: gerçek üretim formülü (`scanner/score_engine.py::compute_recommendation_score`) koduyla istatistiksel decomposition eşleştirildi — catalyst_factor AKTİF-AMA-ÖLÜ-FEATURE (bug), squeeze/overnight_gap istatistiksel-ölü-ama-canlı-ağırlıklı, lottery_factor tek gerçek sinyal ve zaten aktif; en-umut-verici 4 bileşen (atr/rvol/dist_52w_high/risk_reward) CANLI FORMÜLDE HİÇ YOK; canlı formülün ağırlık-bütçesinin ~%60'ı (alignment_ratio/momentum_ratio/filter_score/regime/direction/3-binary) export'ta kolon olmadığı için HİÇ TEK-TEK TEST EDİLEMEMİŞ (Level A, araştırma+kod-denetimi)
Layer: Research / quant
Level: A
Bağlam: Meriç'in "score yeniden tasarlanırsa ne atılır ne tutulur" sorusuna somut cevap için `scanner/score_engine.py:99-190` (`compute_recommendation_score`, gerçek üretim ağırlıkları) okundu ve `score_component_decomposition.py`'nin istatistiksel sonuçlarıyla satır-satır eşleştirildi. `.env` dosyası kontrol edildi: `FINPILOT_ENABLE_SQUEEZE_FACTOR=1`, `FINPILOT_ENABLE_EDGAR_CATALYST=1`, `FINPILOT_ENABLE_LOTTERY_FADE=1`, `FINPILOT_ENABLE_OVERNIGHT_GAP=1` — dördü de CANLI AKTİF (env-gated ama açık).
Bulgular:
1) **catalyst_factor: AKTİF AĞIRLIK (±1,5×macro_mult) AMA VERİ-KATMANI KIRIK** — tam-evrende sabit `''`/`'0.0'` (önceden bilinen bulgu, bu turda kod-seviyesinde kesinleşti: `_catalyst_enabled()`=True olduğu halde `compute_catalyst_factor`'ün çıktısı hep sıfır). Ayrıca lottery_penalty'yi "catalyst>0.3 ise %50'ye kadar hafiflet" mantığı da bu yüzden HİÇBİR ZAMAN tetiklenmiyor — ölü feature, sadece kendi ağırlık-slotunu değil, lottery-relief mekanizmasını da devre dışı bırakıyor.
2) **overnight_gap_factor: AKTİF AĞIRLIK (-1,0) AMA İSTATİSTİKSEL OLARAK ÖLÜ** (t=-1,19, CI 0'ı içeriyor) — canlıda gerçek bir ceza uyguluyor ama bu cezanın forward-getiriyle ilişkisi kanıtlanamadı.
3) **squeeze_factor: AKTİF AĞIRLIK (+0-1,5×macro_mult) AMA GÜVENİLMEZ ÖLÇÜM** — boot-CI 0'ı dışlıyor gibi görünüyor ama n_gün=23 (ince) ve null-kontrolü kendisi sıfırdan uzak (+0,0338) — ne kanıtlanmış-pozitif ne kanıtlanmış-ölü, ÖLÇÜLEMEZ durumda.
4) **lottery_factor: AKTİF AĞIRLIK (-2,0) VE TEK BONFERRONI-HAYATTA-KALAN GERÇEK SİNYAL** — formülde zaten doğru yönde kullanılıyor, değişiklik gerekmiyor (yalnız ağırlık-büyüklüğünün optimize olup olmadığı ayrı bir soru, test edilmedi).
5) **YAPISAL SÜRPRİZ:** decomposition'da en-umut-verici (yalnız-konvansiyonel, t=3,1-4,1) 4 bileşen — `atr`, `rvol`, `dist_52w_high`, `risk_reward` — canlı `compute_recommendation_score` formülünde HİÇ DOĞRUDAN TERİM OLARAK YOK. Bunlar yalnızca KULLANILMAYAN `compute_legacy_quality_score` (farklı bir 0-100 formülü, `legacy_composite_ranking_enabled()` ile kapalı) içinde mevcut. Yani formülün en-umut-verici sinyalleri şu an canlı skora hiç girmiyor.
6) **EN ÖNEMLİ BOŞLUK:** canlı formülün ağırlık-bütçesinin büyük kısmı (`raw_score`×0,5, `filter_score`×1,5, `alignment_ratio`×2,0, `momentum_ratio`×1,5-2,5, `regime`/`direction`×2,0+2,0, `volume_spike`/`price_momentum`/`trend_strength`×0,5+0,5+0,5 — toplam ~10-12 puanlık bir bütçenin çoğu) `full_universe_enriched.csv` export'unda AYRI KOLON OLARAK YOK, dolayısıyla bu decomposition'da (ve bilinen hiçbir önceki deneyde) TEK TEK TEST EDİLEMEDİ. Şu ana kadar test edilen her şey ya bu terimlerin ÖNCEDEN-TOPLANMIŞ hali (`score`, `composite_score` — ölü çıktı) ya da toplamın dışındaki ek-katman feature'lardı (lottery/gap/squeeze/catalyst).
Karar: Bu bir üretim-değişikliği DEĞİL, yalnız bir önceliklendirme haritası. Eğer/ne zaman score yeniden tasarlanırsa: (a) catalyst_factor'ün veri-katmanı onarılmalı veya ağırlık+relief-mantığı kaldırılmalı; (b) overnight_gap_factor ağırlığı test-sonuçlarıyla uyumlu şekilde küçültülmeli/kaldırılmalı; (c) squeeze_factor daha uzun bir pencerede yeniden ölçülmeli (şu an yetersiz-güç); (d) lottery_factor korunmalı; (e) EN YÜKSEK ÖNCELİK: `score_component_breakdown()`'ın (zaten kodda var, satır 253-302) her bir alanını (alignment_ratio, momentum_ratio, filter_score, regime, direction, volume_spike, price_momentum, trend_strength) araştırma export'una AYRI KOLON olarak eklemek — bu, formülün en büyük ağırlık-payını taşıyan ve HİÇ test edilmemiş kısmını nihayet ölçülebilir kılar. Bu, önceki tüm score-decomposition çalışmalarının neden eksik kaldığının kök-nedenidir.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ — bu turda salt kod-okuma ve envanter eşleştirmesi yapıldı, hiçbir dosya/config/ağırlık değiştirilmedi.
Kanıt: `scanner/score_engine.py:29-73,99-190,253-302`, `.env:33-41` (bu turda okundu), `score_component_decomposition.py` çıktısı (önceki girdi).

---

[2026-08-12] — Soru 7 + Soru 10 (bedava, mevcut-veri): score 14 bileşene ayrıştırıldı, Bonferroni-eşiği (|t|>4,56) geriye uygulandı — lottery_factor TEK Bonferroni-hayatta-kalan; composite/finpilot_score'un HAM KENDİSİ bile konvansiyonel eşiği geçemiyor; 4 bileşen (atr/rvol/dist_52w_high/risk_reward) yalnız konvansiyonel |t|>2'de, EXPLORATORY (Level A, araştırma)
Layer: Research / quant
Level: A
Bağlam: Meriç'in "sadece bedava, mevcut veriyle hesaplanabilen kısımlarına (soru 7, soru 10) birkaç saat ayır" talebiyle, red-team raporunun Soru 7 (score bileşen-ayrıştırması) ve Soru 10'u (geriye-dönük global-FDR) birleştiren `score_component_decomposition.py` yazıldı ve çalıştırıldı. Ek veri gerekmedi — mevcut `full_universe_enriched.csv` (dedup, c2c_5d dolu 43.323 satır/82 gün) üzerinde `lottery_gap_reweight_test.py`'nin AYNI metodolojisi (gün-içi Fama-MacBeth rank-korelasyon + null-shuffle kontrol + blok-bootstrap CI) 14 numerik score-bileşenine tek-tek uygulandı.
Sonuçlar (Bonferroni eşiği |t|>4,56, m≈9.754):
  **Bonferroni-hayatta-kalan (tek):** lottery_factor (t=-6,60, boot-CI=[-0,286,-0,133], zaten bilinen bulgunun bu bağımsız-turda TEKRAR teyidi).
  **Sadece konvansiyonel |t|>2'de (Bonferroni'de DEĞİL, EXPLORATORY etiketiyle):** atr (t=+4,09), rvol (t=+3,76), dist_52w_high (t=+3,14), risk_reward (t=+3,50) — dördü de pozitif yönde (yüksek değer=daha iyi forward-getiri). squeeze_factor boot-CI'si 0'ı dışlıyor ama n_gün=23 (ince) ve null-kontrolü kendisi sıfırdan uzak (+0,0338) — GÜVENİLMEZ, ayrı not edildi.
  **Ölü (CI 0'ı içeriyor):** ham `score` (t=-1,91), `composite_score` (t=-1,08), `finpilot_score` (t=-0,88), `overnight_gap_factor` (t=-1,19, önceki bulgunun teyidi), `atr_pct_real`, `gap_pct`, `tier_score`.
  `catalyst_factor` ve `sentiment` yetersiz-veri (n_gün<8) — ölçülemedi.
ÖNEMLİ BULGU: composite_score/finpilot_score'un KENDİSİ (tüm bileşenlerin toplamı) bile konvansiyonel |t|>2 eşiğini geçemiyor — yani score'un içindeki hiçbir güçlü bileşen toplamda görünür kalmıyor, zayıf bileşenler (bazıları zıt yönlü: atr/rvol/dist_52w_high POZİTİF ama score'un kendisi negatif-eğilimli) birbirini götürüyor. Bu, "tek sayıda çok kavramı sahte birleştirme" teşhisini (red-team raporu §1-C) doğrudan destekliyor.
Karar: 4 EXPLORATORY adayın (atr/rvol/dist_52w_high/risk_reward) her biri kendi başına m≈9.754'lük evrende beklenen-şans-pozitifinin İÇİNDE — hiçbiri "bulgu" ilan edilmemeli, ancak bağımsız/yeni veriyle pre-registered test için aday olabilirler. lottery_factor'ün Bonferroni-hayatta-kalan tekliği bir kez daha teyit edildi.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ.
Kanıt: `score_component_decomposition.py` (bu turda yazıldı, repo köküne kondu, tam çıktı bu turda üretildi).

---

[2026-08-12] — BAĞIMSIZ RED-TEAM BİLİMSEL İNCELEME tamamlandı: `reports/red-team-scientific-review-2026-08-12.md` — 10-bölümlü zorunlu format, final decision ledger (çoğu başlık STOP/BLOCKED/DATA_REPAIR); ayrıca bugünkü (08-12) 10+ yeni script/rapor decision-log'a HİÇ girmemiş — 6. kayıt-boşluğu örneği, Meriç'e bildiriliyor (Level A, red-team/governance)
Layer: Research / governance
Level: A
Bağlam: Meriç, kapsamlı bir "Research Red Team + Scientific Review Board" promptu verdi — amaç yeni kural önermek değil, hangi eski sonuçların güvenilir/geçersiz/tekrar/veri-bağımlı olduğunu ve doğru problem tanımını ortaya çıkarmak. `docs/governance/decision-log.md` (734 satır, tam okundu) + paralel sürecin 08-12 tarihli 6 anahtar raporu (`master_audit_application`, `research_program_end_to_end`, `production_candidate_validation`, `high_rvol_deep_audit`, `correct_order_protocol`, `winner_anatomy`) tam okunup bu oturumun kendi rigor-tarihiyle (reverse-ranking, extension/exhaustion, concentration/ATR-parity, lottery_factor, global-FDR, felaket-alt-kümesi düzeltmesi) çapraz-doğrulandı.
Bulgular (rapor kendi içinde tam gerekçeli):
1) Score'un geçmişi-ölçme/geleceği-ölçmeme bulgusu artık 6+ bağımsız yoldan EVIDENCE seviyesinde, tartışmasız.
2) Concentration-limit/ATR-parity'nin "score'a özgü değil, generic portföy-matematiği" sonucu İKİ BAĞIMSIZ YÖNTEMLE (benim rigor_upgrade_concentration_atr.py'm VE paralel sürecin production_candidate_validation'ındaki 100-rastgele-kontrolü) ayrı ayrı doğrulandı — programın en sağlam çift-teyitli bulgusu.
3) "Eligible-rejected farkı kaç puan" sorusunun 5 farklı ölçümde 5 farklı, birbirine indirgenemeyen sayı verdiği (Ç3) tespit edildi — yön tutarlı, büyüklük şu an INSUFFICIENT_DATA.
4) `reports/high_rvol_deep_audit_2026-08-12.md` (paralel süreç) programın metodolojik olarak en iyi-yapılmış tekil artifact'i olarak öne çıkarıldı — kendi "pozitif" $10.000 bulgusunu 5 stres-testiyle (4-en-büyük-günü-çıkar, her-5.-günü-al, ±%50/±%20 winsorize) kendi eliyle çökertti.
5) YÖNETİŞİM: bugünkü (08-12) 10+ yeni script (`high_rvol_*` serisi, `production_candidate_validation`, `decision_context_battery`, `budget_return_battery`, `research_program_end_to_end`, `master_audit_battery`, `hypothesis_ladder_battery`) ve eşdeğer sayıda rapor decision-log'a HİÇ girmemiş (grep ile doğrulandı, bu raporun kendi 2 girdisi hariç sıfır 2026-08-12 eşleşmesi) — CLAUDE.md Bölüm 3'ün en az 6. kez tekrarlanan ihlali.
6) DOSYA-HİJYENİ: `reports/research_program_end_to_end_2026-08-12.md` içinde İngilizce ve Türkçe İKİ TAM RAPOR ayrı bir başlık/ayraç olmadan art arda eklenmiş (satır 135'te "...production approval.# FinPilot Research Program..." şeklinde kesintisiz birleşmiş) — muhtemelen iki ayrı yazma-turu üst-üste append edilmiş, veri kaybı yok ama okunabilirlik/izlenebilirlik sorunu.
Karar: Rapor Level A (araştırma/metodoloji), hiçbir üretim kuralı önermiyor. Final decision ledger'daki başlıkların çoğu STOP/BLOCKED/DATA_REPAIR; iki kalem CONFIRMATORY_CANDIDATE (abstention) / PRODUCT_MVP (PR1/PR7 + Reasoning-Platform testi) olarak işaretlendi. Meriç'e açıkça bildirilmesi gereken governance-bulgusu: Madde 5 (kayıt-boşluğu) ve Madde 6 (dosya-hijyeni) — ikisi de Level A sınırında ama tekrarlayan bir süreç-zayıflığına işaret ediyor.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Bu girdi yalnız bu raporun varlığını ve governance-bulgularını kayda geçiriyor.
Kanıt: `reports/red-team-scientific-review-2026-08-12.md` (tam rapor); bu turun grep sonuçları (`^\[2026-08-1[12]\]` deseni, decision-log.md üzerinde).

---

[2026-08-12] — KONTROL TURU #5 (kendi-kendini-denetim): dünkü "felaket alt-kümesi doğrulandı" iddiam (Madde 4) MEAN/OUTLIER ARTEFAKTIYDI — median-bazlı yeniden test tersini gösteriyor; `reports/master_audit_application_2026-08-12.md`'nin (paralel süreç) çelişen C15/N3 bulgusu doğrulandı ve D20/%86.9 sayısı bağımsız olarak yeniden üretildi (Level A, öz-düzeltme)
Layer: Research / governance
Level: A
Bağlam: Meriç "master_audit_application_2026-08-12.md — kontrolleri sağla" dedi. Bu rapor (paralel süreç, `research/master_audit_battery_2026_08_12.py` çalıştırarak üretilmiş) benim dünkü [2026-08-12] "4 AÇIK İPUCU" girdimdeki Madde-4 sonucuyla DOĞRUDAN ÇELİŞİYORDU: ben "felaket alt-kümesi doğrulandı" dedim (148 flagged sembolü çıkarınca eligible-rejected farkı anlamsızlaşıyor), rapor N3/C15'te "HAYIR, geniş-tabanlı, en büyük leave-one-out etkisi +0.33pp" diyor. Kendi iddiama uyguladığım aynı şüphecilik standardını uyguladım: yeniden hesapladım.

BULUNAN KÖK-NEDEN: Benim testim GÜN-KÜMELİ ORTALAMALARIN ORTALAMASI'nı kullanıyordu (block-bootstrap CI, mean-of-daily-means). Bu istatistik, tek bir aşırı-uç satıra (örn. EDBL +154.445%, INLF +9.146% — ikisi de flagged) karşı SON DERECE hassas, özellikle flagged-eligible alt-kümesi gibi ince örneklemlerde (n=28 satır/20 gün, günde ~1.4 satır). Rapor MEDYAN (day-clustered median + date-block bootstrap) kullanıyor — aşırı-uçlara karşı doğal olarak dirençli. Kendi verimle her iki istatistiği yan yana yeniden hesapladım:
  - Eski liste (148, 2026-08-07) ile: flagged-eligible gün-medyanlarının-medyanı=+0.108 (yaklaşık sıfır) AMA gün-ortalamalarının-ortalaması=-3.066 (çok negatif). non-flagged-eligible: medyan=-1.050 (negatif!) ama ortalama=+1.862 (pozitif!). **Ortalama ve medyan TERS YÖNDE.**
  - Ayrıca daha da önemlisi: `data/backtest_out/price_cache_integrity_audit_2026-08-11.json` diye YENİ, DAHA GENİŞ bir bütünlük-taraması var (485 flagged sembol, 2026-08-07'deki 148'in TAMAMINI kapsıyor + 337 yeni) — ben dünkü testimde BAYATLAMIŞ 148-listeyi kullanmışım. Yeni listeyle de aynı ters-yön deseni tekrarlanıyor: flagged(485)-eligible medyan=-0.235, non-flagged-eligible medyan=-1.179 (flagged DAHA AZ negatif, non-flagged DAHA NEGATİF — tam benim iddiamın tersi).
  - Tüm eligible (49 gün, filtresiz): pooled-medyan=-0.832, gün-medyanlarının-medyanı=-0.884 (ikisi de negatif, rapor'un overall_eligible_median=-0.834 ile eşleşiyor ✓) — ama gün-ortalamalarının-ortalaması=+1.839 (POZİTİF). rejected: medyan≈0/+0.30, ortalama=+5.80.
SONUÇ: eligible-vs-rejected medyan-bazlı fark GERÇEK VE NEGATİF (rapor ile ben aynı yönde-hemfikiriz), ama bunun "148/485 flagged sembolden geldiği" iddiam YANLIŞTI — flagged alt-kümesinin kendi medyanı sıfıra YAKIN, negatifliği non-flagged (temiz) kısım taşıyor. Benim dünkü mean-bazlı testim, ince örneklemde aşırı-uç bir-iki satırın ortalamayı sürüklemesiyle YANLIŞ YÖNDE bir sonuç üretmiş.

BAĞIMSIZ DOĞRULAMA (rapor'un başka iki iddiası): D20 (%86.9 örtüşme) kendi kodumla yeniden üretildi: |c2c_5d|>100 olan 183 satırdan 159'u (485-listede) flagged = %86.85 ≈ rapor'un %86.9'u — **FACT, teyit edildi**. E22 (null-kalibrasyon p95=0.50pp) basit rastgele-yarı-bölme simülasyonumla (farklı metodoloji, 1000 çekim, gün-bloksuz) p95=0.83pp verdi — aynı büyüklük-sınıfında, rapor kendi §7-madde-2'sinde bunun "basitleştirilmiş, tam matched-random değil" olduğunu zaten itiraf ediyor; çelişki yok.

Karar: Dünkü [2026-08-12] "4 AÇIK İPUCU" girdisinin Madde-4 sonucu ("felaket-alt-kümesi doğrulandı") GERİ ÇEKİLİYOR. Doğru sonuç `master_audit_application_2026-08-12.md`'nin N3/C15'i: eligible-kohortun negatifliği GENİŞ TABANLI, tek bir flagged-sembol alt-kümesine indirgenemez. Aksiyon önerisi de buna göre değişir: "148/485 sembolü filtrelemek yeterli düzeltmedir" iddiası YANLIŞ; scanner-çıkışı filtresi (madde 4'teki Level-B önerisi) veri-kalitesi için hâlâ makul ama eligible-negatifliğini ÇÖZMEYECEK. Ayrıca: bundan sonraki tüm alt-küme/felaket testlerinde MEDYAN (gün-kümeli, blok-bootstrap) birincil istatistik olsun, ORTALAMA yalnız ikincil/duyarlılık-kontrolü olarak raporlansın — ince örneklemde ortalama tek bir aşırı-uca karşı güvenilmez. `price_cache_integrity_audit_2026-08-11.json` (485 sembol) artık güncel referans; 2026-08-07/148-listesi BAYAT sayılmalı.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ. `finpilot-4-open-leads-2026-08-12.md` (memory) ve bu logdaki dünkü girdi bu turda düzeltiliyor; script'lerin kendisi (rigor_upgrade_concentration_atr.py, lottery_gap_reweight_test.py, catastrophe_subset_test.py) silinmedi/değiştirilmedi — sadece catastrophe_subset_test.py'nin YORUMU düzeltiliyor, Madde 1-3 (concentration/ATR-parity rigor'dan düşmesi, lottery_factor'ün hayatta kalması, global-FDR hesabı) bu düzeltmeden ETKİLENMİYOR ve geçerliliğini koruyor.
Kanıt: bu turda yazılan doğrulama script'i (yukarıdaki komutlar, bu oturumda); `reports/master_audit_application_2026-08-12.md` §1(N3,N6), §3(C15,D20,E22); `research/master_audit_battery_2026_08_12.py:137-174,244-255`; `data/backtest_out/master_audit_battery_2026-08-12.json` (C15_disaster_subset, D20_artifact_clusters); `data/backtest_out/price_cache_integrity_audit_2026-08-11.json` (485 flagged, eskisinin süperseti).

---

[2026-08-12] — 4 AÇIK İPUCU KOŞTURULDU: concentration/ATR-parity rigor'dan DÜŞTÜ, lottery_factor rigor'dan GEÇTİ (tek hayatta kalan), global-FDR hesaplandı, "eligible kaybediyor" bulgusu felaket-alt-kümesi (148 flagged sembol) çıkarılınca KAYBOLDU (Level A, araştırma)
Layer: Research / measurement
Level: A
Bağlam: Meriç'in kendi önerdiğim 4 açık-ipucu listesini ("1. pozitif bulgular hiç aynı süzgeçten geçmedi, 2. lottery/gap ipucu hiç takip edilmedi, 3. global multiple-testing hiç uygulanmadı, 4. felaket-alt-kümesi testi hiç koşulmadı") onaylayıp "bunlara odaklanalım ne yapmak lazım" talebiyle dördünü de fiilen çalıştırma isteği. Üç yeni script yazıldı ve çalıştırıldı: `rigor_upgrade_concentration_atr.py`, `lottery_gap_reweight_test.py`, `catastrophe_subset_test.py`.

MADDE 0 (script yazarken tesadüfen bulunan, önceden fark edilmemiş kusur): `edge_recheck.csv` DEDUP EDİLMEMİŞ — 53.754 satır ama sadece 27.323 essiz (symbol,scan_date) anahtarı (13.062 tekrarlı anahtar, çoğu intraday-tekrar-tarama). Dedup'siz top-10 günlerin %68'inde (38/56) AYNI SEMBOL 2 kez top-10'a giriyor → o sembolün getirisi günlük portföy-ortalamasında çift sayılıyor. `concentration_portfolio_test.py`/`atr_sizing_test.py`'nin ŞİMDİYE KADAR bildirdiği TÜM sayılar bu kusurla üretilmiş. Dedup, `full_universe_enriched.csv`'deki en-erken-scan_ts satırının composite_score'una eşleştirerek yapıldı (13.062 tekrarlı anahtarın %85'i / 11.142'si tam eşleşti; kalan %15 için min-composite_score deterministik fallback — belirtilmiş bir sınırlama).

MADDE 0.5 (Madde 1 ile Madde 4'ün kesişimi): |c2c5_net|>100 olan 124 satırın 93'ü (%75) 148 price-integrity-flagged sembolle çakışıyor (örn. EDBL +154.445%, INLF +9.146% — muhtemelen ayarlanmamış reverse-split/veri hatası, gerçek getiri değil). Bu satırlar filtrelenmeden çalışan matched-random kontrol (Madde 1) günlük ortalamayı +25%'e kadar şişiriyordu — kendisi bir felaket-alt-kümesi kontaminasyon örneği. Tüm Madde-1 testleri bu 148 sembol dışlanarak yeniden koşuldu.

MADDE 1 — Concentration-limit ve ATR-parity RIGOR'DAN DÜŞTÜ (reverse-ranking ve extension/exhaustion'a katılıyor): Dedup + felaket-alt-kümesi-filtresi + blok-bootstrap CI (blok=5 işlem günü, otokorelasyon için — c2c5_net 5-günlük İLERİ getiri, ardışık günler örtüşüyor) + matched-random kontrol sonrası:
  (a) Score-seçimli kısıtlı-kısıtsız fark: +0.26 (n_gün=51, naive-t=+0.88, boot-CI=[-0.26,+0.86] → 0'ı İÇERİYOR, anlamsız).
  (b) Rastgele-seçimli (matched-random) kısıtlı-kısıtsız fark: -0.02 (boot-CI=[-0.27,+0.18], anlamsız) — yani sektör-tavanı RASTGELE bir portföyde de aynı büyüklükte (aslında biraz negatif) fark yaratıyor.
  (c) İnteraksiyon testi (score_fark - rastgele_fark): +0.29, boot-CI=[-0.27,+1.01] → 0'ı içeriyor → **"kısıtlama score'a özgü değil, generic çeşitlendirme etkisi"** doğrulandı istatistiksel olarak.
  (d) ATR-ters-ağırlık vs eşit-ağırlık: hem kısıtlı hem kısıtsızda CI 0'ı içeriyor (anlamsız). Permütasyon-kontrolü (ATR değerleri o günün isimleri arasında karıştırılıp yeniden hesaplanan ağırlıklı getiri) ile gerçek-ATR arasındaki interaksiyon da anlamsız (boot-CI 0'ı içeriyor) → ATR'nin SPESİFİK bilgisi ayırt edilemiyor, ağırlık-dağılımı varyansından ayrışmıyor.
  SONUÇ: Big-Bet-1'in "concentration-kısıtı riski yarıya indirdi" ve "ATR-parity Sharpe/drawdown iyileştirdi" iddiaları — hiçbiri gün-kümeli+blok-bootstrap+matched-random süzgecinden GEÇMEDİ. `finpilot-big-bet-1-findings.md` HYPOTHESIS seviyesine düşürülmeli.

MADDE 2 — lottery_factor RIGOR'DAN GEÇTİ (programın TEK hayatta kalan pozitif bulgusu), overnight_gap_factor GEÇMEDİ: Kaynak-kod semantiği doğrulandı (`scanner/features.py`: lottery_factor "higher = more lottery-like = stronger FADE expectation"; overnight_gap_factor "reversal pressure" — ikisi de negatif-ağırlıklı kullanılacak şekilde tasarlanmış). Fama-MacBeth tarzı gün-içi rank-korelasyon (n=30 gün, 2026-06-15→07-31, full_universe_enriched.csv dedup):
  lottery_factor vs c2c_5d: ort-rho=-0.204, naive-t=-6.60, boot-CI=[-0.282,-0.136] → **0'ı İÇERMİYOR, ANLAMLI** (null/karıştırılmış-kontrol: rho≈+0.001, referans).
  overnight_gap_factor vs c2c_5d: ort-rho=-0.048, naive-t=-1.19, boot-CI=[-0.123,+0.014] → 0'ı içeriyor, ANLAMSIZ.
  Portföy testi (top-10, n=30 gün): composite_score ile seçim ort-c2c_5d=-1.58 (score AKTİF OLARAK ZARAR VERİYOR, rastgeleden bile kötü); composite - lottery - gap (z-skorlu alt_score) ile seçim ort-c2c_5d=+0.08; rastgele seçim ort-c2c_5d=+2.68. alt-orig farkı=+1.66 (boot-CI=[+0.81,+2.54] → ANLAMLI, lottery/gap cezası gerçek bir iyileştirme). AMA alt_score hâlâ rastgeleden anlamlı derecede KÖTÜ (alt-rand=-2.60, boot-CI=[-4.00,-1.41] → ANLAMLI). SONUÇ: lottery_factor gerçek, doğrulanmış, zayıf bir ileri-bilgi taşıyor ve onu kullanmak composite_score'un zararını KISMEN azaltıyor — ama composite_score'un diğer bileşenleri hâlâ o kadar zararlı ki düzeltilmiş score bile rastgele seçimin altında kalıyor.

MADDE 3 — Global multiple-testing/FDR (geriye-dönük, kaba hesap): m≈9.754 toplam test edilen konfigürasyon (2.520 barrier-grid + 3.120 fixed-target + 4.000 weight-search + 74 iki-faktör-kombo + ~40 bu-yaz). Düzeltmesiz alpha=0.05'te BEKLENEN şans-eseri "anlamlı" sonuç sayısı: ~488. Bonferroni-düzeltilmiş eşik: alpha=5.13e-6, karşılığı iki-yönlü |t|>4.56 (konvansiyonel |t|>2 eşiğinin ÇOK altında kalan bulgular güvenilmez demektir). Q4 null-feature noise-floor referansı (|rho|=0.011 @ p95, tek-test) m=9.754 test üzerinden EN AZ BİR kez aşılması pratikte kesindir (olasılık ≈1). SONUÇ: bu ölçekte, düzeltilmemiş "|t|>2" veya "p<0.05" ile flaglenen HER bulgu a-priori şüpheli sayılmalı; programın 2 yıllık tarihinde flaglenen düzinelerce "pozitif" bulgudan (reverse-ranking, extension/exhaustion, MFE-headline'lar, concentration-limit, ATR-parity) sadece BİRİNİN (lottery_factor, Madde 2) global-ölçekli süzgeçten geçmesi, ~488 beklenen şans-pozitifine karşı ÇOK düşük bir gerçek-bulgu oranıyla tutarlı.

MADDE 4 — "Felaket alt-kümesi" hipotezi DOĞRULANDI: eligible (entry_ok=True) kohortunun negatif bulgusu GENEL DEĞİL, küçük bir veri-bütünlüğü-sorunlu alt-kümeye aşırı-maruziyet. full_universe_enriched.csv dedup, c2c_5d + entry_ok dolu 43.323 satır/82 gün:
  Adım 1 (filtresiz): eligible-rejected = -3.40, boot-CI=[-8.11,-0.91] → 0'ı İÇERMİYOR, ANLAMLI (önceki "eligible kaybediyor" anlatısını gün-kümeli+blok-bootstrap ile teyit ediyor).
  Adım 2: eligible içinde flagged (148 sembolden, sadece 28 satır/1094 = %2,6) vs non-flagged — flagged-eligible ort=-3.07 ama n çok ince (20 gün, günde ~1.4 satır), kendi başına CI 0'ı içeriyor (yetersiz güç).
  Adım 3 (KARAR VERİCİ): 148 flagged sembol HEM eligible HEM rejected'ten çıkarılınca (eligible'ın %2,6'sı, rejected'in %6,3'ü) → eligible-rejected farkı +0.39, boot-CI=[-3.03,+2.30] → 0'ı İÇERİYOR, **ANLAMSIZLAŞTI**.
  Adım 5 (çift-temiz, +penny-stock<$5 de çıkarılmış — ama penny-stock eligible'da pratikte yok, n=1): eligible-rejected=+0.08, boot-CI=[-3.19,+1.89], anlamsız.
  SONUÇ: eligible kohortunun sadece %2,6'sı (fiyat-bütünlüğü bozuk 148 sembolden) TÜM istatistiksel anlamlılığı taşıyıyor. Bu, "seçim (entry_ok) değer eksiltiyor" sonucunu "seçim, veri-bütünlüğü bozuk küçük bir alt-kümeye aşırı-maruz kalıyor; bu alt-küme temizlenince score'un net etkisi rastgeleden İSTATİSTİKSEL OLARAK AYRIŞAMIYOR (ne pozitif ne kanıtlanmış-negatif)" sonucuna çeviriyor — daha ucuz, daha aksiyon-alınabilir bir düzeltme (scanner çıkışında 148 sembolü filtrele) ama AYNI ZAMANDA "score net-pozitif" iddiasını da desteklemiyor.

Karar: Dört madde de araştırma/ölçüm bulgusu (Level A, üretim değişikliği yok). Önerilen takip kararları (Meriç onayı gerekir, Level B): (i) 148 flagged sembolü scanner/backtest pipeline'ından kalıcı olarak filtrele (Madde 4); (ii) composite_score'a lottery_factor+overnight_gap_factor negatif-ağırlıklı düzeltme ekle (Madde 2) — ama bunun kendi başına score'u net-pozitif YAPMADIĞI açıkça belirtilerek; (iii) `finpilot-big-bet-1-findings.md`'deki concentration-limit/ATR-parity iddiaları HYPOTHESIS'e düşürülsün (Madde 1); (iv) gelecekte "|t|>2" tek başına "bulgu" ilan edilmesin, Madde-3'ün m-düzeltmesi (|t|>4.56 veya BH-FDR) referans alınsın.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ — bu turda sadece ölçüm/analiz yapıldı, hiçbir kod/config canlıya dokunmadı.
Kanıt: `rigor_upgrade_concentration_atr.py`, `lottery_gap_reweight_test.py`, `catastrophe_subset_test.py` (üçü de bu turda yazıldı, repo köküne kondu, tam çıktıları bu turda üretildi); `scanner/features.py:392-471` (lottery/gap semantiği); `data/backtest_out/price_cache_adjusted_integrity_audit_2026-08-07.json` (148 flagged sembol).

---

[2026-08-11] — KONTROL TURU #4: PARKING_LOT ihlali tespit edildi — "Ledger×Classroom" kod uygulaması (parkta, "lansman sonrası İLK iş" sözü) canlı landing'e (page.tsx) zaten girmiş; ayrıca 2026-08-11 çalışması decision-log'a hiç girmemiş (5. kayıt-boşluğu örneği) (Level A, kontrol)
Layer: Governance / product
Level: A
Bağlam: Meriç'in "tekrar kontrolleri sağla" talebiyle bağımsız bir denetim turu daha yapıldı — repo dosya-durumu (mtime taraması), decision-log bütünlüğü ve son 24-48 saatte üretilmiş-ama-kayıtsız iş tarandı.
Bulgular:
1) PARKING_LOT İHLALİ (yeni, önceden kayıtlı değildi): `PARKING_LOT.md` "Ledger×Classroom tasarımının kod uygulaması"nı "lansman sonrası İLK iş — söz" diyerek parkta tutuyor. `docs/strategy/Morning_Ledger_Urun_Stratejisi_Konsolide_2026-08-05.md` bunu "VİZYON — DONDURULDU" statüsünde dondurmuş ve kendi metninde "bu belge kod, public içerik... değiştirmez" diyor. Ama gerçek repo durumu tersini gösteriyor: `web/src/components/ledger/ClassroomPreview.tsx` (mtime 2026-08-11 14:29, yeni dosya) canlı landing'e (`web/src/app/page.tsx:9,69`) `<ClassroomPreview>` olarak eklenmiş ve render ediliyor; `DailyDouble.tsx` (mtime 2026-08-10 13:00) aynı sayfada "section.dailyDouble"/"section.classroom" başlıklarıyla canlı. `docs/strategy/FinSense_MVP_Gap_Audit_2026-08-11.md` bunu kendi metninde doğruluyor: "Bugün değiştirdiğim ClassroomPreview.tsx/DailyDouble.tsx... Bugünkü Calibration v0 (Borsa web, ClassroomPreview.tsx) bunun ilk, küçük, kalıcı-olmayan örneği." AGENTS.md tanımıyla bu Level B (web canlı yüzeyi) bir değişiklik — decision-log'da bunu onaylayan/kaydeden hiçbir girdi yok (tam-dosya grep: "ClassroomPreview", "DailyDouble" [tek eski/farklı-bağlamlı referans satır 506], "Calibration v0", "Thinking Mirror" için sıfır ilgili sonuç). Deploy/canlılık durumu bu turda doğrulanamadı (git komutu zaman aşımına uğradı, repo büyük) — ama kod repo'da ve sayfa ağacında mevcut ve derleniyor durumda.
2) YENİ KAYIT-BOŞLUĞU (5. örnek — DURUM.md'nin bilinen örüntüsünün devamı): `reports/research_battery_consolidated_2026-08-11.md`, `docs/strategy/FinSense_MVP_Gap_Audit_2026-08-11.md`, tüm `reports/content_series/` (10 bölümlük "10x40" içerik serisi + HTML + `source_rights_register_2026-08-10.md`), `reports/honest_quant_handbook_2026-08-10.md` + `_distribution_2026-08-10.md`, `reports/glossary_cards_product_spec_2026-08-10.md`, `reports/source_material_inventory_2026-08-10.md`, `reports/finpilot_source_book_product_map_2026-08-10.md` — hiçbiri decision-log'da yok (tam-dosya grep, sıfır eşleşme). `research_battery_consolidated_2026-08-11.md` kendi başlığında "Level A for isolated diagnostics" diyor — sınıflandırma muhtemelen doğru ama yine de kayıt zorunluluğu (CLAUDE.md Bölüm 3) uygulanmamış.
3) DOSYA-SIRALAMA BÜTÜNLÜĞÜ: `decision-log.md` (~654 satır) kronolojik değil — satır 1-183 (KONTROL TURU zinciri, hepsi 2026-08-10) dosyanın BAŞINA eklenmiş, satır 184-653 ise genelde append-sırasında (07-31→...→08-10) ilerliyor. Bu, önceki turlarda "kilitsiz eşzamanlı yazma riski" olarak işaretlenen bulgunun somut kanıtı — iki farklı yazma alışkanlığı (prepend vs append) aynı dosyada karışmış, ama veri kaybı/çakışma gözlenmedi.
4) DURUM.md / LAUNCH_CHECKLIST.md sayıları hâlâ 7 Ağustos'ta doğrulanmış hâliyle duruyor (seri 4/10, 3-6 Ağu) — 11 Ağustos'a kadar canlı DB'ye karşı yeniden doğrulanmamış; 4 günlük bir bayatlık, kritik değil ama not edilir.
Karar: Bulgular yalnız kayıt/rapor; bu turda kod/dosya değişikliği YAPILMADI (Level A sınırı korundu). Madde 1 (PARKING_LOT ihlali) Meriç'e açıkça bildirilmeli — governance-kritik bir çelişki (CLAUDE.md: "report conflicts immediately"; "Never... overwrite governance without approval"). Karar Meriç'e ait: (a) ClassroomPreview/DailyDouble landing'den geri alınsın mı yoksa retroaktif Level B onayı mı verilsin, (b) madde 2'deki kayıtsız işler toplu bir "kayıt-boşluğu kapatma" girdisiyle mi işlensin.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ. Web canlı yüzeyi (landing) muhtemelen ETKİLENDİ (madde 1) — bu turda salt tespit, geri alma/onay işlemi yapılmadı.
Kanıt: `web/src/components/ledger/ClassroomPreview.tsx` (mtime 2026-08-11 14:29), `web/src/app/page.tsx:3-11,46-70`, `PARKING_LOT.md:4`, `docs/strategy/Morning_Ledger_Urun_Stratejisi_Konsolide_2026-08-05.md:1-9`, `docs/strategy/FinSense_MVP_Gap_Audit_2026-08-11.md:22,33`, tam-dosya grep sonuçları (bu turda).

---

[2026-08-11] — Yayın serisi canlı DB'ye karşı yeniden doğrulandı: kesintisiz, 4/10 → 7/10 büyümüş; DURUM.md/LAUNCH_CHECKLIST.md güncellendi (Level A, dokümantasyon)
Layer: Documentation / governance
Level: A
Bağlam: Meriç'in "yayın kesintisiz sürüyor kontrol et" talebiyle `distribution.broadcast.publish_streak()` canlı `data/distribution.db`'ye karşı çalıştırıldı (2026-08-07'deki doğrulamanın aynı yöntemle tekrarı).
Bulgular: `broadcast_queue` sorgusu (`kind LIKE 'daily%'`, `status='sent'`) ardışık şu tarihleri gösteriyor: 3, 4, 5, 6, 7, 10, 11 Ağustos (8-9 Ağu haftasonu, market_calendar tarafından atlanıyor — seriyi kırmıyor). `publish_streak()` **7** döndürdü. En son sent kayıt bugüne (2026-08-11) ait — günün brifi zaten yayınlanmış. Seri kırılmadı; 7 Ağu'daki önceki doğrulamadan (4/10) bu yana 3 gün daha kesintisiz eklenmiş.
Değişiklik: `DURUM.md` "⭐ Bu 6 haftanın TEK önceliği" bölümü 4/10 → 7/10 ve güncel tarih/kanıt notuyla güncellendi. `LAUNCH_CHECKLIST.md` madde 1 aynı sayı + "3 gün kaldı" notuyla güncellendi.
Etki: Yalnız iki durum dosyasındaki sayı/not metni değişti. Scanner/distribution/skor/risk/canlı yayın davranışı DEĞİŞMEDİ — salt dokümantasyon düzeltmesi (2026-08-07 girdisiyle aynı desen, Level A).
Kanıt: `python3 -c "from distribution.broadcast import publish_streak; print(publish_streak())"` → 7; `broadcast_queue` GROUP BY sorgusu (bu turda, sonuç yukarıda).

---

[2026-08-10] — KONTROL TURU #3 (kendi-kendini-denetim): önceki girdideki "dördüncü kez tekrarlandı" iddiam kesin değildi — grep ile satır-satır yeniden sayıldı; ayrıca decision-log/protocol-dosyası bütünliği ve repo eşzamanlılığı doğrulandı (Level A, öz-düzeltme)
Layer: Research / governance
Level: A
Bağlam: "Kontrolleri sağla" talebi ikinci kez geldiğinde, önceki kendi iddiamı da denetime tabi tuttum (aynı şüphecilik kuralı bana da uygulanmalı).
1) BÜTÜNLÜK: `docs/governance/decision-log.md` ve `reports/correct_order_protocol_2026-08-10.md` son yazdığım hâliyle sağlam, üzerine yazma/çakışma yok. Repo'da bu turda yeni değişiklik yok (mtime'lar önceki turdakiyle aynı) — paralel süreç şu an duraklamış görünüyor.
2) ÖZ-DÜZELTME — "dördüncü kez tekrarlandı" iddiam ABARTILIYDI: Her rapor dosyasının kendi metni `grep`lendi. Gerçek durum: (a) `evidence_matrix_v1_2026-08-07.md` decision-log'un "2026-08-06 tarihli" 4 farklı girdisine atıf yapıyor — decision-log'da [2026-08-06] TARİHLİ HİÇBİR GİRDİ YOK (doğrulandı) → GERÇEK, dosya-içi YANLIŞ ATIF (1. örnek, daha önce fark edilmemiş, Aug-07'den). (b) `correct_order_analysis_2026-08-10.md` "Export değişikliği Level B olarak uygulandı (decision-log)" diyor, o an decision-log'da yoktu → GERÇEK, dosya-içi YANLIŞ ATIF (2. örnek). (c) `correct_order_protocol_2026-08-10.md`'nin KENDİ METNİ "Kapı kapanma kriterleri decision-log'a girer" gibi İLERİYE-DÖNÜK KURAL cümleleri kullanıyor, "zaten girdi" diye bir iddia YOK — kullanıcının ilettiği trace-log'daki "Level B pending olarak decision-log'da" cümlesi bir SOHBET-ÖZETİ ifadesiydi, dosyanın kendi metninde değildi. (d) Strategic Lab / 10-Perspective / Mirror Analysis / Pre-registration / User-research-kit dosyaları decision-log'a HİÇ ATIFTA BULUNMUYOR — bunlar "yanlış iddia" değil, sade "kayıt-boşluğu" (girilmemiş ama girileceğini de iddia etmemiş).
Düzeltilmiş sayım: kanıtlanmış dosya-içi yanlış decision-log atfı = 2 (evidence_matrix_v1, correct_order_analysis), + 1 sohbet-seviyesi yanlış durum-iddiası (protokol için, dosyanın kendisinde değil) = toplam 3 doğrulanmış örnek, "4" değil. Kayıt-boşluğu (atıfsız-eksik) ayrı ve daha geniş bir kategori (Strategic Lab vb. + şimdi de evidence_matrix'in ATIF ETTİĞİ ama var olmayan 2026-08-06 girdileri).
Karar: Önceki "dördüncü kez" ifadesi düzeltildi — abartılıydı. Genel bulgu (bu araştırma hattında decision-log referanslarının güvenilmez olduğu, doğrulanmadan kullanılmaması gerektiği) DEĞİŞMEDİ, sadece kesin sayı düzeltildi. Bu, kendi iddialarıma da başkalarının iddialarına uyguladığım aynı doğrulama standardını uygulama örneği.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Onaylanan protokol ve 5-işlik liste geçerliliğini koruyor, bu girdi yalnız önceki girdideki bir sayısal/dilsel abartıyı düzeltiyor.
Kanıt: bu turun grep sonuçları (yukarıda alıntılandı).

---

[2026-08-10] — "Veri→Ölçüm→Execution→Sinyal" 4-kapı protokolü ONAYLANDI (Meriç, bu turda); Kapı 1.1 durumu düzeltildi; eşzamanlı-süreç koordinasyonu netleştirildi (Level B onay + Level A düzeltme)
Layer: Research / governance
Level: B (protokol onayı) + A (durum düzeltmesi + süreç netliği)
Bağlam: `reports/correct_order_protocol_2026-08-10.md` (dört kapı: Veri/Ölçüm/Execution/Sinyal, her biri somut kapanma kriterleriyle) Meriç tarafından bu turda ONAYLANDI. Onayla birlikte iki düzeltme yapıldı:
1) KAPI 1.1 DURUM DÜZELTMESİ: Protokol dosyasında 1.1 ("Etiket semantiği doğrulanmış") "✅ KAPANDI" olarak işaretlenmişti. Bu, ETİKET TANIMI için doğru (resolved_pct_t5=MFE kod-seviyesinde doğrulandı, c2c_5d/mae_t5 export'ta) ama bu etiketle üretilen İLK İKİ headline-sayı (-2.39%/+0.06% ve matched +0.50/-0.61) "KONTROL TURU"/"KONTROL TURU #2" girdilerinde gün-kümeli+dedup+matched-random testten GEÇMEDİ (t~-0.86, t~-0.01, ikisi de anlamsız). Protokolün kendi diliyle bu iki sayı "bulgu" değil "keşif sinyali"dir. 1.1'in durumu buna göre "KAPANDI (tanım) / keşif-sinyali (ilk analizler)" olarak düzeltildi (`correct_order_protocol_2026-08-10.md` içinde de düzeltildi).
2) EŞZAMANLI-SÜREÇ KOORDINASYONU: Bu repo üzerinde bu oturumla PARALEL çalışan başka bir süreç var (muhtemelen Meriç'in ayrı bir Claude Code oturumu) — son ~40 dakikada `fetch_full_universe_and_retest.py`, `full_universe_enriched.csv`, `correct_order_analysis_2026-08-10.md`, `correct_order_protocol_2026-08-10.md` bu süreç tarafından üretildi/değiştirildi. Aynı decision-log.md dosyasına her iki taraf da yazıyor — şu ana kadar çakışma olmadı (her tur öncesi dosya durumu kontrol edildi) ama kilitsiz eşzamanlı yazma riski gerçek. AYRICA: bu paralel sürecin ürettiği 4 rapordan (Strategic Lab, Mirror Analysis, correct_order_analysis, correct_order_protocol) HİÇBİRİ kendi iddia ettiği decision-log girdisini gerçekten yazmamıştı — bu turda dördüncü kez doğrulandı (grep, sıfır eşleşme). Bu artık tek-seferlik değil, o sürecin sistemik bir alışkanlığı: rapor içinde "decision-log'a girdi" cümlesi bir niyet/formalite olarak yazılıyor, gerçek yazma adımı atlanıyor.
Karar: Protokol onaylandı, bu haftalık 5 iş (1.3 lineage şeması, 1.4 restatement pilotu, 2.2 deney-bütçesi defteri, 2.3 null-preflight zorunlu-gate, 3.2 signal half-life) başlatılabilir. Koordinasyon için önerilen kural: hangi taraf decision-log'a yazacaksa, YAZMADAN ÖNCE dosyayı taze okusun (iki taraf da bunu yapıyor gibi görünüyor, şimdilik çakışma yok) VE "girdi" iddiasını yalnızca gerçekten yazdıktan sonra rapor metnine koysun (yazmadan önce değil) — bu, tekrarlayan "iddia edilen ama yok" örüntüsünü kapatır.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Sinyal katmanı (Kapı 4, pre-registered H1-H3) hâlâ kilitli — Kapı 1-3 kapanana ve kullanıcı-gerçeği (PR1/PR7) netleşene kadar.
Kanıt: `reports/correct_order_protocol_2026-08-10.md` (düzeltilmiş hâli), bu turun grep-doğrulaması.

---

[2026-08-10] — KONTROL TURU #2: "confound-kontrollü" eşleştirilmiş MFE-vs-c2c karşılaştırması (+0.50/-0.61) da gün-kümeli teste tabi tutulunca anlamsız çıktı — confound-kontrolü doğruydu, gün-kümeleme atlanmıştı (Level A, kontrol)
Layer: Research / governance
Level: A
Bağlam: Önceki "KONTROL TURU" girdisinin ardından, paralel süreç bir takip analiziyle export-büyümesi confound'unu kontrol etti: eski∩yeni export'un kesişimindeki AYNI 27.386 sembol-gününde, yalnız etiket değiştirilerek (MFE vs c2c_5d) eligible-rejected farkı hesaplandı — MFE ile +0.50 (seçim "kazanıyor"), c2c_5d ile -0.61 (seçim "kaybediyor"), işaret tam tersine dönüyor. Bu, veri-büyümesi confound'unu doğru şekilde kontrol ediyor (iyi metodolojik içgüdü) — AMA satır-bazlı (978 eligible satırı vs 33-42binlik rejected satırı, aynı-gün-korelasyonu hesaba katılmadan) medyan karşılaştırması, bu programın tekrarlayan uyarısına (S1, gün-kümeleme olmadan "anlamlı" illüzyon) yine tabi.
Bu turda AYNI eşleştirilmiş alt-kümede (proxy: scan_date≤2026-07-13, dedup'lu, gün-kümeli, matched-random-kontrollü) bağımsızca yeniden test edildi:
- MFE (resolved_pct_t5): eligible-rejected paired fark = **-0.060, t~-0.01 — ANLAMSIZ** (raporun "+0.50 kazanıyor" iddiası gün-kümelemede kaybolan bir satır-bazlı artefakt; gerçekte MFE'de neredeyse sıfır fark var).
- c2c_5d (dürüst): eligible-rejected paired fark = **-2.190, t~-0.86 — ANLAMSIZ** (yön negatif/tutarlı ama istatistiksel olarak sağlam değil; raporun "-0.61 kaybediyor, confound-suz kanıt" iddiası bu barı geçmiyor).
Karar: Confound-kontrolü (export-büyümesi ayrıştırması) doğru ve değerli bir adımdı, korunuyor. Ama "işaret tam tersine dönüyor, confound-suz temiz kanıt" çerçevesi ABARTILI — çünkü gün-kümeleme adımı (bu programın S1 bulgusunun bizzat kendisinin gerektirdiği) atlanmış. Genel yön (eligible zayıf) hâlâ P1/Mirror-L4/P0-P3 üçlüsüyle destekleniyor; bu spesifik eşleştirilmiş-karşılaştırma kendi başına "kanıtlanmış" sayılmamalı — programın üçüncü kez tekrarlayan örüntüsü (çarpıcı satır-bazlı sayı → gün-kümelemede erir).
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. "correct_order_analysis" raporunun sonuç-cümlesi ("tek düzeltme iki-yıllık anlatıyı tersine çevirdi") bu iki ayrı kontrol turuyla da desteklenmiyor; doğru çerçeve "düzeltme yönü teyit ediyor ama kendi başına henüz istatistiksel olarak sağlam değil."
Kanıt: bu turun bağımsız kontrol scripti (kaydedilmedi, çıktı yukarıda satır satır).

---

[2026-08-10] — KONTROL TURU: export sessizce büyümüş (53.859→100.496 satır, 66→85 gün); "correct_order" raporunun -%2.39/+%0.06 iddiası bu oturumun kendi rigor-standardıyla (dedup+gün-kümeli+matched-random+outlier) ANLAMSIZ çıktı — henüz doğrulanmış sayılmaz (Level A, kontrol)
Layer: Research / governance
Level: A
Bağlam: Kullanıcı talebiyle ("kontrolleri sağla") önceki turun bulgusu ve genel repo durumu bağımsızca yeniden denetlendi.
1) REPO-DURUM KONTROLÜ: `full_universe_enriched.csv` bu oturum içinde sessizce büyümüş — 53.859→100.496 ham satır, 66→85 farklı scan_date, tarih aralığı 2025-09-11..2026-07-13'ten 2025-09-11..2026-08-05'e uzamış. composite_score kapsamı önceki turda bulunan 39 günden (2026-05-06→07-13) 58 güne (2026-04-27→08-05) genişlemiş — "composite_score sadece 39 gün" bulgusu artık GÜNCEL DEĞİL, sayı büyüdü ama nitel sonuç aynı kalıyor (composite_score hâlâ 85 günün tamamını kapsamıyor, en-eski ~58 gün hâlâ boş). Bu oturumdaki ESKİ export üzerinde hesaplanan tüm sayılar (reverse_ranking_closure.py, extension_cap_test.py, iki batarya) artık dosyanın GÜNCEL hâliyle bire-bir yeniden üretilemez — anlık görüntü değişti. decision-log/memory'deki eski sayılar geçerliliğini korur (o anki dosya durumunu doğru yansıtıyorlardı) ama "güncel dosya durumu" olarak okunmamalı.
2) BAĞIMSIZ DOĞRULAMA — "correct_order_analysis" raporunun -%2.39/+%0.06 iddiası: Bu sayı için hiçbir kayıtlı script/artifact bulunamadı (yalnız `fetch_full_universe_and_retest.py` ve onun testi var, ikisi de bu karşılaştırmayı yapmıyor) — az önceki "0.325" ile aynı türde izlenemeyen-sayı sorunu. Bu turda dedup (en-erken-scan_ts) + gün-kümeli + matched-random-kontrol + outlier-farkındalığıyla (bu oturumun standart rigor'u) bağımsızca yeniden hesaplandı, YENİ (büyümüş) export üzerinde:
   - Ham (outlier dahil): eligible medyan -1.523% (n_gün=49, n_obs=1094, ort +1.839 — ort/medyan arası büyük fark, outlier-etkisi), rejected medyan +2.223% (n_gün=82, n_obs=42.229). Paired gün-kümeli fark: eligible-rejected = -3.402, SE=2.063, t~-1.65 → **ANLAMSIZ**. eligible vs random-kontrol (2 seed) de anlamsız (t~-0.13, -0.67).
   - Outlier-kapsanmış (|c2c_5d|≤%100): eligible medyan -1.523% (değişmedi), rejected medyan +0.311% (düştü). Paired fark: **YÖN TERSİNE DÖNÜYOR** (+1.250, t~+0.62, hâlâ anlamsız).
   Sonuç: "correct_order" raporunun "sonuç hemen değişti, seçim kaybediyor" çerçevesi, bu oturumun kendi rigor-standardına (dedup/gün-kümeli/matched-random — reverse-ranking'i ve extension/exhaustion'ı kapatan AYNI standart) tabi tutulduğunda DOĞRULANMIYOR. Yön (eligible zayıf) hâlâ genel tabloyla (P1, Mirror L4, P0-P3) tutarlı ama BU SPESİFİK sayı/iddia kendi başına istatistiksel olarak sağlam değil ve outlier-hassas.
Karar: "-%2.39/+%0.06" rakamı decision-log'daki önceki girdide (VERİ KATMANI DÜZELTMESİ) AKTARILDIĞI HALİYLE bırakılıyor (o an rapor edilen şekliyle kayıt altında) ama bu girdiyle DOĞRULANMAMIŞ/anlamsız olarak işaretleniyor — gelecekte biri bu sayıyı "kanıtlanmış" diye kullanmasın.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Genel yön-bulgusu (eligible zayıf/rastgeleyi geçemiyor) hâlâ 3 diğer bağımsız kanıtla (P1, Mirror L4, P0-P3) destekleniyor; sadece bu tek sayı/iddia zayıflatıldı.
Kanıt: bu turun bağımsız kontrol scripti (kaydedilmedi, sonuç yukarıda satır satır); `data/backtest_out/full_universe_enriched.csv` (güncel mtime 2026-08-10 15:13).

---

[2026-08-10] — VERİ KATMANI DÜZELTMESİ: resolved_pct_t5'in MFE (getiri değil) olduğu kod-seviyesinde doğrulandı; export'a gerçek c2c_1d/c2c_5d/mae_t5 eklendi; dürüst etiketle eligible<rejected bulgusu ÇOK DAHA SERT çıktı (Level A/B karışık — export değişikliği + araştırma bulgusu)
Layer: Research / data
Level: A (bulgu) + B (export şeması değişikliği — aşağıda not)
Bağlam: Önceki turda V0/resolved_pct_t5 korelasyonunun üç ayrı ölçümde üç farklı sayı verdiği (0.86/0.325/0.55) tespit edilmiş, kök-neden araştırması başlatılmıştı. Kod-seviyesi denetim (`fetch_full_universe_and_retest.py:294`) kesin cevabı verdi: `resolved_pct_t5 = (max(highs[T+1..T+5]) - entry)/entry*100` — bu bir MAX-FAVORABLE-EXCURSION (MFE) hesabı, close-to-close GETİRİ değil. Üç farklı korelasyon sayısı bu yüzden "hata" değildi — üçü de MFE'yi (yapısal olarak c2c'den ≥ olan, farklı örneklemlerde farklı oranda ayrışan bir büyüklük) bir getiriyle kıyaslıyordu. Bu, 2026-07-31 kararındaki "resolved_pct_t5 MFE-bozuk" bulgusunun kod-seviyesinde tam teyidi (üçüncü bağımsız doğrulama).
NOT (süreç/eşzamanlılık): Bu düzeltme, bu oturumun kendi script'i tarafından değil, REPO ÜZERİNDE EŞZAMANLI ÇALIŞAN başka bir süreç tarafından yapıldı (`fetch_full_universe_and_retest.py`, `full_universe_enriched.csv`, `reports/correct_order_analysis_2026-08-10.md` hepsi bu turda, dakikalar içinde değişti — muhtemelen Meriç'in paralel bir Claude Code oturumu). Bu üçüncü kez tekrarlanan bir örüntü: `reports/correct_order_analysis_2026-08-10.md`'nin kendi "Governance boundary" bölümü "export değişikliği Level B olarak uygulandı (decision-log)" diyor, ama decision-log'da bu değişikliğe dair HİÇBİR girdi yoktu (grep ile doğrulandı) — Strategic Lab/10-Perspective/Mirror-Analysis/Pre-registration'da da aynı boşluk vardı.
Bulgular (yeni export'un c2c_5d alanıyla, dürüst getiri):
- score vs c2c_5d (gerçek getiri): ρ=0.011 — ileri bilgi yok (önceki R1'in ρ=0.013'üyle tutarlı, farklı örneklem/tarih ile bağımsız teyit).
- score vs mae_t5 (adverse-excursion): ρ=+0.095 — yüksek score, DAHA KÖTÜ adverse excursion ile ilişkili (ters yönde, kötüye işaret).
- **eligible c2c_5d medyanı: -%2.39 | rejected c2c_5d medyanı: +%0.06.** Pozitif-oran: eligible %35.4 vs rejected %50.4.
- Bu, MFE-etiketiyle GÖRÜNMEYEN bir bulgu — MFE "5 gün içinde bir noktada yukarı gitti mi" ölçer, gerçek 5-gün-sonu durumunu değil. Dürüst ölçümle, seçim katmanının zararı ÖNCEDEN SANILANDAN DAHA BÜYÜK.
- Bu sayı, bu oturumun kendi bulgularıyla (reverse_ranking_closure.py, Mirror Analysis L4: eligible -%0.20 vs not-eligible +%1.08 üst-quintile içinde) AYNI YÖNDE ama farklı büyüklükte — beklenen, çünkü farklı dedup/örneklem/pencere kullanıyorlar. Yön tutarlılığı (eligible her zaman kötü) şu an DÖRT bağımsız ölçümde var: P1 (battery-1, -2.01pp), Mirror L4 (-0.20% vs +1.08%), bu turun c2c_5d'si (-2.39% vs +0.06%), ve entry_ok'un kendi P0-P3 end-to-end testi (-0.6387%, 2026-08-07).
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Araştırma-export şeması (`full_universe_enriched.csv`, yeni kolonlar c2c_1d/c2c_5d/mae_t5) değişti — bu dosya yalnız research/ tüketiyor, canlı sisteme bağlı değil, dolayısıyla bu oturumun sınıflandırma alışkanlığıyla Level A sayılır; ilgili rapor "Level B" demiş, bu tutarsızlık not edilmiştir, üretim etkisi olmadığından pratik sonucu değiştirmiyor.
Sıradaki somut adımlar (raporun kendi sıralaması, "veri→ölçüm→execution→sinyal"): (1) 148 işaretli sembolün fiyat-sürekliliği onarımı (AÇIK), (2) feature timestamp/age lineage (AÇIK), (3) restatement dedektörü (AÇIK), (4) deney-bütçesi defteri (AÇIK), (5) zorunlu null-preflight (KISMEN), (6) replayable telemetry/P0 score-replay (AÇIK, Level B bekliyor), (7) spread/ADV toplama (YOK), (8) signal half-life (YOK) — sinyal katmanına (pre-registered H1-H3) yalnız bunlardan sonra + kullanıcı-gerçeği kapısından (PR1/PR7) sonra geçilecek.
Kanıt: `fetch_full_universe_and_retest.py` (satır 294-320), `data/backtest_out/full_universe_enriched.csv` (yeni kolonlar), `reports/correct_order_analysis_2026-08-10.md`.

---

[2026-08-10] — BÜYÜK KAYIT-BOŞLUĞU: 2026-08-04..08-10 arası onlarca deney + formal evidence-gate matrisi (PASS/FAIL/NOT_OPENED) hiç decision-log'a girmemiş; ayrıca V0 (resolved_pct_t5↔cache korelasyonu) üç bağımsız ölçümde üç farklı sayı veriyor (Level A, kayıt+tutarsızlık-tespiti)
Layer: Research / governance
Level: A
Bağlam: Bu oturumda "hepsini sıraya al, herşeyi dene" talebi üzerine tam envanter çıkarıldı. `reports/evidence_matrix_v1_2026-08-07.md`, `reports/end_to_end_experiment_summary_2026-08-07.md`, `reports/mirror_analysis_2026-08-10.md`, `reports/preregistration_three_hypotheses_2026-08-10.md`, `reports/user_research_kit_2026-08-10.md` ve bunlara bağlı `research/`, `tests/`, `data/backtest_out/` altındaki 2026-08-04..08-10 tarihli çıktılar — hiçbiri decision-log'da yok (grep ile doğrulandı, sıfır eşleşme). Bu, CLAUDE.md Bölüm 3'ün ("her önemli karar buraya girer") tekrarlayan biçimde ihlal edildiği anlamına geliyor — tek seferlik değil, en az 5 farklı tarihte.
Bulunan (önceden bilinmeyen) içerik özeti:
- FORMAL EVIDENCE-GATE MATRİSİ (2026-08-07) zaten var: PASS/FAIL/UNKNOWN/INSUFFICIENT_DATA/NOT_OPENED/PARTIAL sözlüğüyle 17 kapı tanımlı. Sonuç: "Discovery PASS, ama Economic-validation FAIL (maliyet %0.55→%1.00 pozitiften negatife döndü), Distribution-robustness FAIL, Rejection-quality FAIL (%41.79 yanlış-red oranı — bu oturumun kendi bulgusuyla aynı yönde), Locked-OOS NOT_OPENED, Execution/Capacity INSUFFICIENT_DATA/UNKNOWN." Genel sonuç zaten "NO-GO/promotion yok" olarak kayıtlı.
- MIRROR ANALYSIS (2026-08-10) bu oturumdaki "score backward-looking" bulgusunu DAHA DA sertleştiriyor: L4 bulgusu — en yüksek score-quintile İÇİNDE bile eligible medyan -%0.20 vs not-eligible +%1.08. Yani sorun "iyi score, kötü seçim" değil; score-bandının kendisi bilgi taşımıyor VE entry_ok o bandın içinde de kötüyü seçiyor. Ayrıca "fade the score" sentez-testi de reddedildi (follow +%0.77 vs fade -%0.89 top-decile medyan) — skoru ters çevirmek de çözüm değil.
- PRE-REGISTRATION (2026-08-10) 3 hipotezi (H1 gap-reversal, H2 rvol-inversion, H3 ATR-parity) zaten dondurmuş — "İKİ KAPI açılmadan (veri-bütünlüğü E2/V0 + kullanıcı-gerçeği PR1/PR7) confirmatory koşu YAPILMAYACAK" kuralıyla. Bu, HARKing/multiple-testing'i önlemek için.
- USER RESEARCH KIT (2026-08-10) zaten yazılmış — PR1 (12 görüşme scripti), PR7 (AI-ikame testi), PR2 (5 positioning-varyantı) hazır, yalnız Meriç'in gerçek kullanıcılarla çalıştırması gerekiyor.
TUTARSIZLIK TESPİTİ (bu turda, "ufak ihtimalleri atlama" talebiyle bulundu): resolved_pct_t5 ↔ cache-türetilmiş fwd-5g-getiri korelasyonu ÜÇ farklı ölçümde ÜÇ farklı sayı veriyor: (a) `strategic_lab_2026-08-10.json` V0: Pearson=0.8607, n=2.000 (örneklem). (b) `preregistration_three_hypotheses_2026-08-10.md`: "korelasyon 0.325" — HİÇBİR script/artifact'te bu sayıyı üreten kod bulunamadı (izlenemiyor). (c) Bu turda bağımsızca çalıştırılan tam-popülasyon kontrolü (n=7.454, pure-python Pearson/Spearman): Pearson=0.5515, Spearman=0.6038. Üç sayı da birbirinden farklı — bu, resolved_pct_t5'in KENDİSİNİN net tanımlanmamış olduğunu (entry-price konvansiyonu, ufuk hizalaması, örneklem farkı) gösteriyor; E2/V0 kapısı şu an güvenilmez bir sayıya dayanıyor.
Ayrıca doğrulandı: `catalyst_factor` tam-evrende (53.859 satır) yalnızca `''` veya `'0.0'` değerleri alıyor — kesin ölü feature, önceki turdaki bulgunun tam-popülasyon teyidi.
Karar: (1) Bu envanter artık kayıtlı — gelecekte "biliyor musunuz" sorusu bu girdiye referans verebilir. (2) V0/resolved_pct_t5 tanımı YENİDEN NET biçimde belgelenmeli ve tek-bir-doğru-implementasyon olarak dondurulmalı, üç farklı sayı çelişkisi kapanmadan E2/V0 kapısı "kapandı" sayılamaz. (3) Pre-registration'daki H1/H2/H3'ü ÇALIŞTIRMAMA kararı bu girdiyle teyit ediliyor — kullanıcıdan açık onay gelmeden bozulmayacak.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Yeni deney yapmadan önce mevcut envanterin decision-log'a işlenmesi ve V0 tutarsızlığının çözülmesi önceliklendirildi.
Kanıt: `reports/evidence_matrix_v1_2026-08-07.md`, `reports/end_to_end_experiment_summary_2026-08-07.md`, `reports/mirror_analysis_2026-08-10.md`, `reports/preregistration_three_hypotheses_2026-08-10.md`, `reports/user_research_kit_2026-08-10.md`, `data/backtest_out/strategic_lab_2026-08-10.json` (V0 alanı), bu turun bağımsız V0 kontrolü (script kaydedilmedi, sonuç yukarıda).

---
_Not (düzeltildi 2026-07-29): docs/INDEX.md 2026-07-24'te zaten gerçek indekse dönüştürülmüştü; bu satır o tarihten sonra güncellenmemiş bayat bir notu tekrarlıyordu. 2026-07-29'da INDEX.md'ye ayrıca makine-okunur bir manifest eklendi (bkz. aşağıdaki girdi)._

[2026-08-10] — KAYIT-BOŞLUĞU KAPATILDI: iki tam deney bataryası (Strategic Lab + 10-Perspective, toplam 31 deney, 18/18+10/10 test geçti) daha önce hiç decision-log'a girmemiş — şimdi kaydediliyor + kendi bulgularımızla sentezlendi (Level A, kayıt+sentez)
Layer: Research / quant
Level: A
Bağlam: `reports/strategic_lab_experiments_2026-08-10.md` ve `reports/ten_perspectives_lab_2026-08-10.md` (+ `research/strategic_lab_2026_08_10.py`, `research/ten_perspectives_lab_2026_08_10.py`, ilgili testler) tarihi 2026-08-10 olmasına rağmen bu oturumun kendi kayıtlarında (decision-log dahil) hiç görünmüyordu — CLAUDE.md Bölüm 3'ün gerektirdiği kayıt disiplini boşluğu. Veri: `full_universe_enriched.csv` 53.859 ham satır → 27.386 dedup'lu symbol-day, 2025-09-11..2026-07-13. Yöntem: date-block bootstrap CI (1000 çekiliş), medyan/winsorize/pozitif-oran — bu oturumdaki gün-kümeli SE yaklaşımından DAHA GÜÇLÜ (gün-içi VE günler-arası otokorelasyonu birlikte hesaba katıyor).
Başlıca bulgular (batarya 1 — Strategic Lab):
- R1: score geçmiş-5g getiriyle ρ=0.376, gelecek-5g getiriyle ρ=0.013 (n=16.693) — score büyük ölçüde OLMUŞ OLANI ölçüyor.
- P1: eligible portföy, aynı-gün rastgele-rejected portföylerden medyan -2.01pp kötü, 35 günün yalnız %31'inde önde (maliyet-sonrası) — "selector" ürün-iddiası KANITSIZ.
- R2: reverse-ranking YÖNÜ tekrarlıyor (eligible -0.386% vs rejected +0.427%) ama block-CI'lar örtüşüyor — kararsız, KAPATILDI değil "kesin değil".
- S1: tam-evren etkin örneklem ~620 (27.361 satırdan, ~44x küçültme); eligible ~168 (799'dan ~4.8x). Satır-sayısına dayalı TÜM anlamlılık iddiaları yanıltıcı.
- E2/V0: |drift|≤%1 alt-kümesi medyanı -%0.39'dan +%0.52'ye taşıyor; resolved_pct_t5 vs cache korelasyonu yalnız 0.86 — veri-bütünlüğü sinyalden daha belirleyici (2026-07-31 "resolved_pct_t5 MFE-bozuk" bulgusunun üçüncü bağımsız teyidi).
- X1/X3: eligible 5g MFE medyanı +%4.26, MAE -%4.36; hold-to-horizon bu excursion'ın yalnız ~%14'ünü yakalıyor — asıl fırsat pencerede, endpoint'te değil.
- X6: naif -1×ATR invalidation-exit medyanı KÖTÜLEŞTİRİYOR (-0.63% vs -0.39%) — basit stop çözüm değil.
- E1: entry-timing maliyeti küçük (-0.12pp) — bu programın kendi entry_point_drift.py bulgusunu teyit ediyor.
- P2: aday-korelasyonu düşük (medyan 0.19) — redundancy ana sorun değil.
- P7: kayıplar zaman-kümeli (lag-1 otokorelasyon 0.23) — S1'in düşük-etkin-n bulgusunun bir nedeni.
Başlıca bulgular (batarya 2 — 10-Perspective, batarya-1'i tekrarlamıyor):
- Q3 (KRİTİK, extension/exhaustion'ı YENİDEN ÇERÇEVELİYOR): score en güçlü dist_52w_high (ρ=0.667) ve past_5d_pct (ρ=0.376) ile kodlanmış — yani EXTENSION. Ama en fazla İLERİYE-dönük bilgi taşıyan feature'lar lottery_factor (ρ=-0.110) ve overnight_gap_factor (ρ=-0.095) — İKİSİ DE NEGATİF ve score'un ağırlıklandırmasında muhtemelen ters yönde kullanılıyor.
- F1: score'un olasılık-kalibrasyonu sabit-baseline'dan KÖTÜ (Brier-skill -0.019/-0.030) — rastgeleden kötü, tahmin etmemekten daha kötü.
- Q5: eligible, SPY'a göre medyan -1.22pp (CI [-2.11,-0.23], sıfırın altında istatistiksel).
- M1/M2: yüksek-rvol eligible en kötü kohort (-%1.77); büyük gap-up'lar başarısız (-%3.04), büyük gap-down'lar sıçrıyor (+%3.05) — score'un ödüllendirdiği yön ters.
- Q1: adverse-excursion evrensel (taban %86.5, eligible %91.2) — 1-ATR stop sınıfı bu ufukta yapısal olarak kırılgan.
- catalyst_factor SABİT-SIFIR (ölü feature, score ağırlığı işgal ediyor, sıfır bilgi taşıyor).
- P2(batarya-2): ATR-parity sizing en iyi maxDD (-%15.9 vs eşit-ağırlık -%24.3) — construction, selection'dan daha güçlü bir kaldıraç.
KENDİ BULGULARIMIZLA SENTEZ (bu oturum):
- Extension/exhaustion geri-çekilmesi (yukarıdaki DÜZELTME girdisi) Q3 ile TUTARLI ve DAHA İYİ AÇIKLANIYOR: score gerçekten extension'ı kodluyor (composite_score↔dist_52w_high r=+0.663, PCA bulgusu — Q3'ün ρ=0.667'siyle bağımsız teyit) ama extension'ın kendisi ileri-getiriyi monoton bozmuyor (extension_cap_test.py Test A) çünkü asıl ileri-bilgi TAMAMEN FARKLI feature'larda (lottery/overnight-gap, negatif) — score onları yanlış yönde/hiç kullanmıyor. "Extension → mean-reversion" nedensel hikayesi yerine "score, zayıf-ama-gerçek ileri-sinyali görmezden gelip geçmişi kodluyor" daha doğru çerçeve.
- S1'in etkin-örneklem bulgusu, bu oturumdaki "anlamsız" sonuçların (reverse-ranking kapanışı, extension-cap testi) neden sistematik olarak anlamsız çıktığını açıklıyor — gün-kümeli SE bile günler-arası otokorelasyonu (P7=0.23) hesaba katmıyor, gerçek n_eff daha da küçük. Bu, önceki "anlamsız" kararları ÇÜRÜTMÜYOR (yön aynı: daha az güç → daha zor anlamlılık, tutucu kalıyor) ama "kanıtsız" ile "sıfır-etki" arasındaki farkı netleştiriyor.
- E2 (drift-filtresi medyanı tersine çeviriyor) muhtemelen bu oturumda flagledigimiz Q4 outlier günlerinin (+134%/+176%) açıklaması olabilir — ayrı doğrulanmadı, açık.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ (Level A). Programın merkezi ampirik cevabı artık şu: (1) score geçmişi ölçüyor, geleceği değil (5 bağımsız kanıt hattı: R1,R4,R10,Q3,F1,Q5); (2) seçim katmanı değer EKSİLTİYOR (P1, Q5, F1 — 3 bağımsız kanıt); (3) tek somut ileri-yapı path/exit'te (X1/X3) ve construction'da (P2-batarya2), gated behind data-integrity (E2/V0); (4) parametre-ayarı DONDURULMALI, ileri-dönük hedef olmadan.
Kanıt: `reports/strategic_lab_experiments_2026-08-10.md`, `reports/ten_perspectives_lab_2026-08-10.md`, `research/strategic_lab_2026_08_10.py`, `research/ten_perspectives_lab_2026_08_10.py`, `tests/test_strategic_lab_2026_08_10.py`, `tests/test_ten_perspectives_lab_2026_08_10.py`, `data/backtest_out/strategic_lab_2026-08-10.json`, `data/backtest_out/ten_perspectives_lab_2026-08-10.json`.

---

[2026-08-10] — DÜZELTME: Extension/exhaustion "resmi teşhis"i geri çekildi — tam-popülasyon/gün-kümeli doğrudan-nedensellik testi doğrulamadı (Level A, düzeltme)
Layer: Research / quant
Level: A
Bağlam: Aşağıdaki girdide "entry_ok'un resmi teşhisi" ilan edilen extension/exhaustion mekanizması, aksiyon-alınabilirliğini test etmek için `extension_cap_test.py` ile derinleştirildi (bkz. o girdideki Level-B aksiyon-önerisi). Bu, önceki bulgunun kendisini sorguladı.
Bulgular (dedup'lu, gün-kümeli, tam-popülasyon n_gün≈27.323 satır, n=25.037 extension hesaplanabilir):
- TEST A (extension-decile → GERÇEK c2c5_net, doğrudan-nedensellik): monoton bozulma YOK. En yüksek decile (en uzamış isimler) en kötü getiriyi vermiyor — ort+1.00/medyan+1.26 (pozitif), t~+1.88, hâlâ |t|>2 eşiğinin altında. Hiçbir decile anlamlı değil.
- TEST B (entry_ok=True vs False ortalama-extension farkı, gün-kümeli, tam-popülasyon): eligible ort-ext +11.53 vs rejected +1.00 ama gün-kümeli paired-fark t~+1.56 — ANLAMSIZ. (Küçük/dengesiz bir alt-örneklemde -244 gözlem- daha önce t~+3.35 görünmüştü; tam popülasyonda bu tutarlılık KAYBOLDU — reverse-ranking'te görülen aynı küçük-n kırılganlığı.)
- TEST C (extension-cap simülasyonu — eligible kümesine medyan/p70 tavanı): capped-eligible ne orijinal-eligible'dan ne rejected'ten anlamlı farklı (iki cap seviyesinde de |t|<1). Önerilen "aksiyon" (entry_ok'a extension-tavanı ekleme) gerçekleşen-getiriyi iyileştirmiyor.
- METODOLOJİK NOT: orijinal "15× decile-rate" bulgusu (`extension_exhaustion_test.py`) satır-bazlıydı, DEDUP'LANMAMIŞ 6.000-satırlık rastgele örneklemdeydi — reverse-ranking'i çökerten aynı risk (saatlik-scanner gün-içi tekrarı) bu bulguda hiç kontrol edilmemişti.
Karar: Extension/exhaustion, "entry_ok'un resmi teşhisi" statüsünden "kısmen-desteklenen ama doğrudan-nedensellik testinde doğrulanamayan hipotez"e düşürülüyor. entry_ok<rejected inversiyonunun kök-nedeni HÂLÂ AÇIK. Extension-cap Level-B aksiyon-önerisi ERTELENDİ — dayandığı temel iddia kendisi tam-popülasyon testini geçemedi.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Aşağıdaki girdideki "resmi teşhis" ifadesi bu girdiyle geçersiz kılınıyor; gelecekte referans verilirken bu düzeltme esas alınmalı.
Kanıt: `extension_cap_test.py`.

---

[2026-08-10] — Reverse-ranking RESMEN KAPATILDI (artefakt); extension/exhaustion entry_ok'un resmi teşhisi oldu (SONRADAN DÜZELTİLDİ — bkz. yukarıdaki girdi); composite_score veri-kapsamı 39-güne daraldığı bulundu (Level A, kapanış)
Layer: Research / quant
Level: A
Bağlam: Önceki iki Level-A girdisinin ("Strategic Thinking Lab: 5 deney" ve "10-Perspektif: 4 ek deney") sentez raporunda (`docs/2026-08-10-iki-belge-kapsamli-sentez.md`) belirlenen 3 "Hemen" aksiyon maddesi işlendi: (1) reverse-ranking'i kapat, (2) extension/exhaustion'ı entry_ok'un resmi teşhisi olarak geçir, (3) günlük sembol-tekrarını (414 vs 814.5) aç-kapa.
Bulgular:
- REVERSE-RANKING KAPATILDI: `reverse_ranking_closure.py` ile iki eksik giderildi — (a) `full_universe_enriched.csv`'de aynı-(symbol,scan_date) için en-erken-scan_ts dedup'ı (bkz. aşağıdaki sembol-tekrarı maddesi), (b) tek IS/OOS yerine 4 çeyreklik pencere + her pencerede gerçek matched-random-kontrol (çoklu seed). Sonuç: Q1 anlamlı (t~+3.53), Q2 anlamlı ama RANDOM da ÜST'ü geçiyor (ALT özel değil, ÜST kötü), Q3 anlamsız (t~-0.50), Q4 anlamsız + outlier-şüpheli (t~-0.16, günlük +134/+176% gibi aşırı değerler — veri-hatası şüphesi, ayrı incelenmedi). TAM DÖNEM (34 gün, dedup'lu): ALT-%20 vs ÜST-%20 t~-0.14 (anlamsız), ALT vs 3 random-seed kontrolün hepsinde de anlamsız. KARAR: bulgu dönem-özel artefakt, ARTIK "düzeltildi/sınırda" değil, RESMİ OLARAK KAPATILDI — üretime/stratejiye taşınmayacak.
- YAN-BULGU (önemli, kapsam-sınırlayıcı): Dedup sonrası `composite_score`'un `full_universe_enriched.csv`'de güvenilir-dolu olduğu aralık yalnızca 2026-05-06 → 2026-07-13 (39 işlem-günü) — bu tarihten önce boş/NaN. Bu programdaki TÜM composite_score-tabanlı testler (bu tur dahil önceki turlar) "Eylül 2025–Temmuz 2026 geneli" değil, bu dar 39-günlük pencerede çalışmış. Kapsam iddiaları bu sınırlamayla yeniden okunmalı.
- EXTENSION/EXHAUSTION RESMİ TEŞHİS: önceki turda kanıtlanan bulgu (ATR-extension deciline göre entry_ok-oranı ~15× artış: [0.0,0.4,0.5,1.4,2.1,3.9,4.3,7.5,6.8,5.3]%, + composite_score↔dist_52w_high r=+0.663) burada entry_ok'un RESMİ teşhisi olarak kayda geçiriliyor: entry_ok, tasarım/yan-etki olarak zaten-uzamış (mean-reversion'a yakın) isimleri sistematik seçiyor — eligible<rejected ve conviction A<B<C inversiyonlarının ilk somut nedensel açıklaması. Aksiyon-adayı (Level B, henüz uygulanmadı): entry_ok kriterine extension-tavanı eklemenin cohort kalitesini iyileştirip iyileştirmediği ayrı test edilmeli.
- SEMBOL-TEKRARI AÇIKLANDI: `edge_recheck.csv`'nin 53.754 satırı yalnız 27.323 benzersiz (symbol,scan_date) çift — 13.062 çift (%48) tekrarlı (max 17×, örn. NVDA 2026-05-19). Kök-neden: production scanner saatlik çalışıyor (`core/scheduler.py`, interval_minutes=60), aynı sembol/gün birden çok kez ateşleniyor, composite_score hafif kayıyor ama outcome (c2c5_net, price_cache'ten tek-seferlik) sabit kalıyor. Tekrar-sayısı ile skor/outcome arasında yön-yanlılığı yaratacak korelasyon yok (rank-r=0.032/0.026) ama örneklem-büyüklüğünü yapay şişiriyor (gerçek fırsat n=27.323, "n=53.754" değil) ve sık-ateşlenen isimleri gün-ortalamalarında aşırı-temsil ediyor. Bu turdan itibaren dedup zorunlu; geçmiş satır-bazlı analizlerin şişirilmiş n ile yapıldığı not edilmeli.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ (Level A analiz/kapanış). Reverse-ranking artık aday listesinden düşürüldü. Extension/exhaustion, entry_ok üzerinde somut bir Level-B düzeltme deneyi için temel oluşturuyor. composite_score'un 39-günlük kapsam sınırı, gelecekteki tüm composite_score-tabanlı iddiaların örneklem-genelleme diliminde açıkça belirtilmesini gerektiriyor.
Kanıt: `hemen-yapilacaklar-sonuc.md`, `reverse_ranking_closure.py`.

---

[2026-08-10] — 10-Perspektif belgesinden 4 ek deney koşuldu: extension/exhaustion mekanizması kanıtlandı, PCA-redundancy hipotezi reddedildi, reverse-ranking cluster-robust'ta DÜZELTİLDİ (Level A, bulgu)
Layer: Research / quant
Level: A
Bağlam: `docs/2026-08-10-finpilot-10-perspektif-red-team-vizyon-arastirmasi.md`'nin (10-Perspektif) Persona-1 deney listesinden 4 ek deney koşuldu, ardından bu deney + önceki Strategic Thinking Lab deneyleri (9 toplam) tek sentez raporunda birleştirildi.
Bulgular:
- EXTENSION/EXHAUSTION MEKANİZMASI KANITLANDI: ATR-extension (20g-getiri/ATR) deciline göre entry_ok(eligible)-oranı ~15× artıyor ([0.0,0.4,0.5,1.4,2.1,3.9,4.3,7.5,6.8,5.3]%) — entry_ok sistematik olarak zaten-uzamış/tükenmiş isimleri seçiyor. Bu, önceden bilinen "eligible < rejected" ve "conviction A<B<C" inversiyonlarının ilk somut nedensel açıklaması.
- PCA/FEATURE-REDUNDANCY: composite_score↔finpilot_score dışında (r=+1.000, bilinen) feature-ailesi BEKLENENİN AKSİNE çok redundant değil — %90 varyansa 7-8/11 bileşen gerekiyor. "2-3 bağımsız eksene iniyor" hipotezi (10-Perspektif Persona-1) test edilip REDDEDİLDİ. YENİ: composite_score↔dist_52w_high r=+0.663 (extension-bulgusuyla tutarlı ikinci kanıt hattı).
- REVERSE-RANKING DÜZELTMESİ (kritik): Önceki turda "IS/OOS-tutarlı en güçlü sinyal" diye raporlanan composite_score ALT-%20 (reverse) bulgusu, gün-seviyesinde (cluster-robust) yeniden test edildi. IS'te fark hâlâ pozitif/sınırda-anlamlı (n=26 gün, t~+2.22) ama OOS'ta TAMAMEN ÇÖKTÜ (n=30 gün, t~-0.15, birkaç outlier-gün varyansı yutuyor). Bulgu artık "kanıtlanmış" sayılamaz — ya matched-random+yeni-OOS-penceresiyle tekrar test edilmeli ya da artefakt olarak resmi kapatılmalı. Bu, programın kendi "aynı-gün kümelenme CI'ları şişirir" uyarısının doğrulanmış hâli.
- ATR-BAZLI SIZING: 1/ATR ters-orantılı position-sizing, concentration-kısıtlı portföyde Sharpe'ı kötüleştirdi (0.165→0.127) — beklenmedik, concentration-kısıtı hâlâ dominant tek düzeltme.
- YAN-BULGU: günlük ort. 414 benzersiz-sembole karşı 814.5 toplam-satır (~2× tekrar) — dedup/multi-timestamp etkisi incelenmedi, açık soru.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ (Level A analiz). Extension/exhaustion bulgusu entry_ok'un resmi teşhisi olarak öneriliyor; reverse-ranking bulgusu geri çekilmeli/yeniden test edilmeli.
Kanıt: `docs/2026-08-10-iki-belge-kapsamli-sentez.md`, `extension_exhaustion_test.py`, `pca_feature_redundancy.py`, `cluster_robust_and_clustering.py`, `atr_sizing_test.py`.

---

[2026-08-10] — Strategic Thinking Lab: 5 deney koşuldu — canlı-skor train/serve skew bulundu, reverse-ranking + concentration-portföy adayları (Level A, bulgu)
Layer: Research / quant / infra
Level: A
Bağlam: "FinPilot Strategic Thinking Lab v1.0" belgesindeki Experiment Factory'nin (72 deney) çalıştırılabilir alt-kümesi (5 deney) koşuldu; kalanı yeni-veri veya kullanıcı-pilotu gerektirdiği için ertelendi (triyaj: `docs/2026-08-10-big-bet-1-sonuclar.md` §0).
Bulgular:
- ATR LOOK-AHEAD AUDİT: `edge_recheck.py`'nin ATR hesabı (pencere ei-14..ei-1, giriş-öncesi) klasik gelecek-sızıntısı taşımıyor — ATR→MAE risk-bulgusu (IC −0.51) sağlam kaldı. AMA yeni bulgu: `scanner/evaluate.py:403,412-413,497-498` canlı ATR/RSI/MACD/hacim-çarpanını `df_1d/df_15m[...].iloc[-1]` ile hesaplıyor; `core/scheduler.py` ana-tarama `interval_minutes=60` ile gün-içi çalışıyor → canlı skor çoğu zaman GÜN-İÇİ PARÇALI barla üretiliyor (RVOL özellikle saat-bağımlı yanlı). Klasik look-ahead değil, train/serve skew — P0 score-replay sorununun ve entry_ok/conviction inversiyonlarının olası kök-nedenlerinden biri.
- GİRİŞ-NOKTASI TESTİ (1.400/1.926 sembol, 36.932 satır): sinyal-close/ertesi-open/ertesi-close arasında SPY-excess'te anlamlı fark yok, hiçbir noktada drift/half-life yok → "giriş-zamanlaması yanlış" hipotezi ELENDİ.
- REVERSE-RANKING: composite_score ALT-%20 (fade-adayı), hem IS (medRet −0.155 vs üst-%20 −0.647) hem OOS'ta (+1.018 vs +0.517) baseline+üst-%20'yi tutarlı geçti — programda ilk IS/OOS-tutarlı doğrudan-getiri-sinyali (matched-random-kontrol doğrulaması bekliyor; finpilot_score'daki eşdeğer test tie-artefaktı verdi, gerçek değil).
- RANDOM-ENTRY KONTROLÜ: gerçek sinyaller (n=53.754) random-entry kontrolü (n=3.000) aynı exit-mekaniğiyle her metrikte (win/medyan × tb_ret/c2c5_net) geçti → taban-sinyal-üretimi rastgeleden gerçekten iyi; sorun downstream composite-ranking'te (yukarıdaki madde ile tutarlı).
- CONCENTRATION-PORTFÖY (yaklaşık, n=52-56 gün): kısıtsız top-10 ortalama %61.79 tek-sektöre yığılıyor; max-3/sektör kısıtı volatiliteyi yarıya (7.08→3.94), CVaR5%'i yarıdan-aza (−26%→−10.5%), maxDD'yi yarıdan-aza (−49%→−22%) indirdi VE ortalama-getiriyi artırdı (+0.07%→+0.65%) — alfa gerektirmeyen, en yüksek-etkili düzeltme adayı.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ (Level A analiz). Sıradaki öneriler: canlı-skor feature-timing düzeltmesi (Level B adayı), reverse-ranking'in pre-registered matched-random doğrulaması, concentration-kısıtının tam-evrende doğrulanması, Big Bet #3 (gerçek-sektör-etiket) hâlâ bekliyor.
Kanıt: `docs/2026-08-10-finpilot-strategic-thinking-lab-v1.md`, `docs/2026-08-10-big-bet-1-sonuclar.md`, `entry_point_drift.py`, `reverse_ranking_and_random_entry.py`, `concentration_portfolio_test.py`.

---

[2026-07-31] — Opsiyon-faktörü pilotu (yeni-bilgi) hattı kuruldu (Level A, local-run bekliyor)
Layer: Research / data
Level: A
Bağlam: Roadmap v2 P1 — teknik faktörler dürüst-metrikte tükendi (IC~0); tek yeni-bilgi yolu opsiyon positioning/IV (fiyat-hacimden türetilemez). EODHD UnicornBay opsiyon geçmişi Q4-2023'ten 2.5+ yıl EOD (Greeks/IV/OI/put-call), 6.600+ ABD hissesi → sinyal penceresini (Eyl'25–Tem'26) kapsıyor.
Değişiklik: `data/eodhd_client.py`'ye `options_eod()` metodu + modül wrapper eklendi (`mp/unicornbay/options/eod`, JSON:API, 24s cache). Yeni `options_factor_pilot.py`: 6 faktör türetir (put/call OI & hacim, ATM IV, IV skew, toplam OI/hacim) → `edge_recheck` dürüst-metrik + IS/OOS rank-IC testi; modlar: `--probe` (canlı şema+plan teyidi), `--build` (resumable), `--analyze`. Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ.
Etki/Durum: uygulandı ve AĞSIZ test edildi — `py_compile` temiz; `derive_factors` sentetik kontratla doğrulandı (put/call OI 1.625, ATM IV 0.35, skew 0.09); `analyze` harness'i gerçek symbol/date + sentetik faktörle çalıştı ve rastgeleyi doğru "tutarsız" işaretledi (IS/OOS disiplini). LOCAL-RUN bekliyor (ağ + EODHD UnicornBay opsiyon eklentisi gerekir). Ön koşullar: (1) opsiyon eklentisi plan kapsamı `--probe` ile teyit; (2) alan adları ilk yanıtla doğrulanıp gerekirse `FIELD_MAP` güncellenmeli. Bir faktör IS+OOS aynı işaret & |IC|>~0.03 verirse projenin ilk gerçek lead'i olur; vermezse kolay-erişilebilir veri de tükenmiş sayılır.

---

[2026-07-31] — Edge araştırması: dürüst-metrikte tradeable alfa yok + resolved_pct_t5 P0-bozuk (Level A, bulgu)
Layer: Research / quant
Level: A
Bağlam: FINPILOT RESEARCH master prompt — "skor gerçekte neyi ölçüyor?" bilimsel olarak araştırıldı.
Bulgular (hepsi kanıtlı, IS/OOS ve dürüst metrikle):
- `edge_recheck.py` (yeni, izole) tüm evreni (53.754 satır) price_cache'ten GERÇEKLEŞEN kapanış-kapanış + triple-barrier (cost'lu) ile yeniden hesapladı.
- METRİK DENETİMİ: ATR↔resolved_pct_t5(enriched) +0.40 vs ATR↔gerçekleşen c2c +0.01. `resolved_pct_t5` MFE (en-iyi-durum) izliyor, gerçekleşen getiriyi değil → "ATR edge" %100 metrik artefaktı.
- SKOR TESTİ (dürüst): composite_score IC −0.03 (kırık), finpilot_score +0.03 (ihmal, rejim-kararsız: bull +0.055/bear −0.093), ATR ~0/negatif. Cost sonrası evren medyanı ≈0; triple-barrier −0.95.
- ARAMA: 2-faktör 74 kombo (0 stabil) + 4000-konfig ağırlık optimizasyonu (add/remove/invert/reweight, IS/OOS) → hiçbir konfig baseline'ı stabil geçmedi; IS-en iyi OOS'ta şans (%44).
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ (yalnız analiz). İKİ P0 SONUÇ: (1) `resolved_pct_t5` MFE-bozuk → bu metriğe dayanan TÜM geçmiş "edge" iddiaları yeniden temellenmeli; (2) mevcut günlük-bar faktör setinde doğrulanmış tradeable alfa YOK → ilerlemek recombination değil YENİ veri/faktör ya da değer önermesini karar-destek/eğitime kaydırma gerektirir.
Durum: uygulandı — Level A (araştırma bulgusu). Kanıt: `docs/2026-07-31-FinPilot-Research-skorun-anlami-RAPOR.md`, `edge_recheck.py`, `data/backtest_out/edge_recheck.csv`.

---

[2026-07-30] - Sinyal izleme shadow scorecard altyapısı (Level A, uygulandı)
Layer: Research / engineering
Level: A
Bağlam: `docs/2026-07-29-sinyal-izleme-gelistirme-UCTAN-UCA-plan.md` offline kontrol grubu, horizon sweep, dağılım yüzdelikleri, SPY excess return, ATR-normalize getiri, segment alanları ve risk-ayarlı özetler öngörüyor. Faz 0 kontrolünde `data/price_cache` benchmark dahil `2026-06-30` tarihinde bitiyor; mevcut 107 dedup sinyalin tamamı olgunlaşmamış kaldı.
Değişiklik (önce/sonra): Önce `shadow_scorecard.py` yalnız seçilmiş satırları ve model bariyer sonuçlarını özetliyordu; sonra kontrol satırlarını opsiyonel dahil eden, model-bağımsız ileri getiri/MFE, horizon sweep, red nedeni, ADV/veri kalite segmentleri, SPY excess return, p10/medyan/p90, Sharpe-benzeri metrik ve deterministik bootstrap aralığı üreten izole altyapı eklendi. `tests/test_shadow_scorecard.py` sentetik sözleşmeleri doğruluyor.
Etki: Scanner skorları, filtreler, entry/exit kuralları, risk boyutlandırması ve canlı Karne/web yüzeyi değişmedi. Cache yenilenene kadar gerçek performans sonucu üretilmemeli; mevcut çalışma yalnız altyapı ve veri-yeterlilik bulgusudur. Faz 4b Level B olarak bu kaydın kapsamında değildir.
Durum: uygulandı — Level A. Kanıt: `python -m pytest tests/test_shadow_scorecard.py -q` (3 passed); baseline CLI (`--dedup`) 107/107 pending.

---

[2026-07-29] — Waitlist + demo feedback endpoint'lerine Telegram admin bildirimi (Level B, uygulandı)
Layer: Engineering / product distribution
Bağlam: Web yüzü denetimi (`docs/2026-07-29-web-yuzu-DENETIM-raporu.md`) waitlist ve demo feedback formlarının gerçek ve uçtan uca bağlı olduğunu, ama yeni kayıt/yorum geldiğinde hiçbir bildirim gitmediğini kanıtladı: waitlist SMTP yapılandırılmamış (`_notify_waitlist_signup` "skipped" logluyor), feedback yalnız SQLite'a yazıyor. Sonuç: gönderimler fark edilmeden birikiyordu.
Değişiklik: `api/routers/waitlist_signup.py` (yeni `_notify_admin_telegram` helper + signup sonrası ping: e-posta/kaynak/toplam) ve `api/routers/demo_feedback.py` (feedback kaydı sonrası ping: ödeme niyeti + yorum özeti) mevcut `distribution.telegram_client.notify_admin` altyapısına bağlandı. İkisi de try/except best-effort — bildirim hatası isteği bozmaz; `notify_admin` yapılandırma yoksa False döner (raise etmez). Scanner/skor/veri saklama/mevcut SMTP akışı değişmedi (yalnız ekleme — CORE-009).
Etki: Yeni waitlist kaydı / demo yorumu anında Telegram admin'e düşer (`TELEGRAM_BOT_TOKEN`+`TELEGRAM_ADMIN_ID` gerektirir; `.env`'de mevcut). 4/4 birim testi geçti: ping içeriği doğru, boş feedback ping atmıyor, `notify_admin` patlasa bile istek OK. `py_compile` temiz. Canlı deploy yapılmadı.
Durum: uygulandı — Level B; Meriç onayı alındı (2026-07-29). Canlı deploy kararı bu kaydın kapsamında değildir.

---

[2026-07-29] — Telegram gerekçe katmanına bağlam ve izlenecek sonuç açıklaması (Level B, pending)
Layer: Content / product distribution
Bağlam: Günlük Telegram taslağı mevcut faktörleri tek tek açıklıyordu; faktörlerin birlikte neyi düşündürdüğü ve hangi gözlenebilir sonucun izleneceği yeterince açık değildi.
Değişiklik: `distribution/rationale.py` içindeki deterministik rationale üretimine rozet kombinasyonlarına dayalı sentez cümlesi eklendi. Metin sırasıyla gözlenen nedenleri, bağlamsal birleşimi ve doğrulanmamış açık soruyu ifade ediyor; TR/EN/DE çıktıları korunuyor. Scanner skoru, eşikler, risk, entry/exit ve yayın akışı değişmedi.
Etki: Telegram ve snapshot rationale metinleri daha açıklayıcı ve bağlamlı oldu; bugünkü önizleme lint'ten geçti. Web public projection artık graded adaylar ve scan-context kayıtlarında `risk_reward`, `stop_loss`, `take_profit` ve `stop_loss_percent` alanlarını dışarıda bırakıyor. Karne API'si HTTP 401 olduğunda mevcut DB fallback notu korunuyor. Canlı Telegram/web yayını yapılmadı.
Durum: uygulandı — Level B; Meriç onayı alındı (2026-07-29). Canlı yayın kararı bu kaydın kapsamında değildir.

---

[2026-07-29] - Scanner 15-hata triyaji tamamlandi (10 Level A duzeltildi, 5 Level B/C flagged) + render.yaml/.env bulgusu genisletildi
Baglam: Onceki 07-29 kayitlarindaki dogrulama kosusunda (734 passed, 15 failed)
bulunan 15 test hatasi tek tek incelendi (kullanicinin "onayliyorum" onayi
uzerine, kullanici oturumda musait degildi, "otonom calis, iyi kararlar ver"
talimati verildi).
Sonuc: 10/15 duzeltildi (Level A, sadece test katmani, production kodu
degismedi):
(1-2) test_score_engine_catalyst/squeeze_off_by_default: Faz 5 (2026-06-20,
b2bdba0) skor x0.5 dususu icin test beklentisi guncellenmemisti (3.0->1.5).
(3-5) test_defensive_strategy, test_squeeze_factor_high_short_low_float,
test_get_alpha_features_skips_squeeze_when_disabled: yerel .env'deki
FINPILOT_ENABLE_ALPHA_V2=1 testlere sizip squeeze agirligini (0.5/0.5->0.7/0.3)
ve gate'i degistiriyordu; testlere izolasyon eklendi.
(6) test_returns_none_on_insufficient_data: 2026-07-15 (2c60744)
_unavailable_result sozlesmesi icin test bayikti (None bekliyordu, artik
Tier-3 dict donuyor - kasitli, dokumante degisiklik).
(7-8) test_returns_expected_keys, test_rounds_price_to_four_decimals:
_fetch_price_sync Alpaca-once + yf.download() fallback mimarisine tasinmis,
test eski yfinance.Ticker mock hedefini kullaniyordu.
(9) test_auth_register_login_and_me_flow: KRITIK BULGU - core.config.DB_PATH
modul-seviyesi sabit, core.config ilk import edildiginde (collection
sirasinda, fixture'lardan once) donuyor. monkeypatch.setenv("FINPILOT_DB_PATH")
tek basina auth.database.Database()'e ulasmiyor (Database() no-arg cagrisi
donmus DB_PATH'i okuyor) - gercek kalici data/finpilot.db dosyasina yaziyordu,
oturumlar arasi kullanici birikip 409 Conflict'e neden oluyordu. Fix:
monkeypatch.setattr("core.config.DB_PATH", ...) eklendi.
(10) test_all_fields_present_and_lint_clean: glossary prob_band metni
"bir garanti degil" / "not a guarantee" iceriyordu - distribution/lint.py'nin
guarantee kurali negation-aware degil, "degil" ile olumsuzlanmis olsa bile
yakaliyor. Icerik 2026-07-24'te eklenmis, 07-15 collection hatasi yuzunden
gorunmezdi. FIX: icerik yeniden yazildi (linter kurali GEVSETILMEDI - CORE-002
risk&compliance kurali korundu).
5/15 kasitli duzeltilmedi: 2'si tests/test_full_universe_robustness.py
icinde (bu dosya untracked/uncommitted, baska bir es zamanli oturumun WIP'i,
dokunulmadi); 1'i test_prometheus.py port-bind zamanlamasina dayanan
environment-bagimli flaky test; 2'si scanner_rollout/test_runtime_baseline.py
: entry_ok icin score==2 + alignment_ratio>=0.66 durumunda gecerli olmasi
beklenen bir gevsetilmis giris kapisi bekliyor ama scanner/evaluate.py'de
entry_ok = bool(score == 3) sabit kodlanmis. Git log bu test dosyasinin
sadece 2026-05-05'teki dev bir "thanks" commit'inde eklendigini gosteriyor,
ilgili evaluate.py degisikligi izlenemedi - ya hic uygulanmamis planli bir
ozellik ya da gecmiste kaldirilmis bir davranis. Canli sinyal uretim
mantigini etkiledigi icin urun/quant karari gerekiyor, DOKUNULMADI.
Dogrulama: 744 passed, 5 failed, 6 skipped (once: 734/15/6), 0 collection
hatasi, 0 yeni regresyon.
3E.7 bulgusu genisletildi: yerel .env'de 18 `FINPILOT_ENABLE_*`/`FRED_*`/
`SEC_EDGAR_*` anahtari var (hepsi kisisel arastirma icin ACIK), .env.example
bunlarin hicbirini belgelemiyor, render.yaml sadece 1 tanesini iceriyor.
.env.example yorumlari bu faktorlerin coğunun "Default OFF, once shadow modda
olc" seklinde tasarlandigini gosteriyor - yani production'in bunlari
ACMAMASI kasitli/guvenli olabilir. render.yaml'a DOKUNULMADI (canli sinyal
davranisini etkileme riski, tek tarafli karar verilemez).
3E.8 (dry-run zorunlulugu) ve 3E.9 (erken uyari sistemi) incelendi ama
uygulanmadi - ikisi de canli yayin/scan pipeline'ini etkileyen, gozden
gecirme gerektiren degisiklikler.
Etki alani: tests/test_catalyst.py, tests/test_squeeze_factor.py,
tests/test_evaluate.py, tests/test_new_endpoints.py, tests/test_api_runtime.py,
distribution/glossary.py (icerik, politika degil). Commit 068f2aa, push edildi.
Not (guvenlik, bilgi amacli): render.yaml/.env karsilastirmasi sirasinda
.env icinde gercek bir FRED_API_KEY degeri goruldu; .gitignore (.env*) ve
`git log --all -- .env` ile dogrulandi - bu dosya HICBIR ZAMAN git'e commit
edilmemis, sizinti yok. Deger bu kayda veya baska hicbir committed dosyaya
yazilmadi.
Durum: 10/15 tamamlandi ve dogrulandi; 5/15 + 3E.7/3E.8/3E.9 Meric karari
bekliyor.

[2026-07-29] - Otorite-haritasi gocu: lint guard (Level A uygulandi) + INDEX.md manifest / .github rewrite (Level B pending)
Baglam: Kullanici `docs/2026-07-29-otorite-haritasi-gocu-plani.md` planini
onayladi ve "neler olusturmamiz gerekiyor" diye sordu. Uygulamadan once repo'nun
gercek governance yuzeyi okundu (varsayimla degil): `docs/INDEX.md` VE
`docs/governance/decision-log.md` zaten VARDI (plan taslaginin "ikisi de yok"
iddiasi yanlisti); INDEX.md 2026-07-24'te zaten gercek otorite haritasina
donusturulmustu, ama bu logun ust notu bunu yansitmiyordu (yukarida duzeltildi).
`_instructions/01-governance.md`, `05-escalation.md`, `08-security.md` hala
Status: DRAFT (CORE-006 onayi bekliyor); yalniz `00-core.md` ACTIVE. Kok
klasorler `00-strategy…06-releases` ve `_instructions/core-rules.yaml`
dogrulandi — gercekten yok. `.github/instructions/*.md` (7 dosya) sadece
`applyTo` degil, govde metninde de (mission.md, composite-score.md,
entry-exit-rules.md, architecture.md, glossary.md, risk-policy.md) hic var
olmamis dosyalara atif veriyordu; bunlar ICAT EDILMEDI (CORE-004), gercek
yollara veya acik "gap" notuna cevrildi.
Karar (Level A — uygulandi, otonom, izole, salt-okunur guard):
`scripts/lint_authority_map.py` olusturuldu; `docs/INDEX.md`'deki manifesti ve
`.github/instructions/*.md` applyTo alanlarini gercek agacla karsilastirir.
Calistirildi: 7/7 hayalet applyTo hatasi tespit etti, duzeltme sonrasi
`lint_authority_map: OK (0 errors, 0 warnings)`.
Karar (Level B — uygulandi, Merric onayi bekliyor, KAPANMADI):
(a) `docs/INDEX.md`'ye JSON manifest eklendi (15 entry; strategy,
product-rules, engineering-architecture, risk-policy, releases acikca
`status: gap` isaretlendi — icat edilmedi); (b) bu logun ust notu duzeltildi;
(c) `.github/copilot-instructions.md` yeniden yazildi — hayalet klasor
haritasi silindi, `docs/INDEX.md`'ye referans verildi, `core-rules.yaml`
referansi kaldirildi (CORE-003: 00-core.md'yi kopyalamak yerine referans);
(d) 7 `.github/instructions/*.md` dosyasinin `applyTo` + govde referanslari
gercek yollara veya acik gap notlarina cevrildi; (e) `CLAUDE.md` v3.0→v3.1:
Startup Sequence'e docs/INDEX.md + decision-log adimlari eklendi, Governance
bolumundeki dosya referanslari tam yola cevrildi (changelog eklendi).
Etki alani: yalnizca dokumantasyon/AI-talimat dosyalari
(`.github/**`, `CLAUDE.md`, `docs/INDEX.md`, bu log, yeni `scripts/
lint_authority_map.py`). Scanner/distribution/api/web PRODUCTION kodu
davranissal olarak DEGISMEDI.
Sinir: `AGENTS.md` DRAFT→APPROVED degisikligi yapilmadi (Level C, yalniz
Merric). `_instructions/01-governance.md/05-escalation.md/08-security.md`
DRAFT durumu degistirilmedi. `core-rules.yaml` OLUSTURULMADI (CORE-003:
00-core.md'yi tekrar etmemek icin referans kaldirmayi tercih ettik; alternatif
"olustur" secenegi Merric onayina birakildi). Yeni "gap" olarak isaretlenen
otorite dokumanlari (mission.md, composite-score.md, entry-exit-rules.md,
architecture.md, risk-policy.md) bu kararla OLUSTURULMADI/ONAYLANMADI.
Operasyonel bulgu: bu oturumda `.github/copilot-instructions.md`, `CLAUDE.md`
ve bu logun kendisi, diskteki degisiklik dogrulandiktan SONRA, editorde acik
eski-icerikli sekme/otokaydetme kaynakli goruntu ile SESSIZCE eski haline
donduruldu; ayni edit ikinci kez uygulanarak kurtarildi. Kok neden dogrulanamadi
ama YONERGE.md M1 (OneDrive/AV dosya guvenligi riski) ile tutarli — izlenmesi
gereken acik bir operasyonel risk olarak buraya kaydedildi.
Kanit: `python scripts/lint_authority_map.py` -> `OK (0 errors, 0 warnings)`.
Durum: Level A uygulandi ve dogrulandi; Level B degisiklikler diskte hazir
ancak commit/push edilmedi, Merric onayi olmadan "kapandi" sayilmaz.

[2026-07-29] - Scanner kirilma/regresyon kok neden forensic analizi + Bolum 3-Ek (Level A uygulandi + Level B pending)
Baglam: Kullanici talebiyle scanner/distribution yayin zincirinin tekrar tekrar
"harden/restore/repair" commit'i almasinin (07-17, 07-23, 07-24, 07-27x2, 07-28)
yapisal kok nedeni arastirildi (git log, requirements.txt, render.yaml/.env,
ci.yml, tests/ incelemesi).
Dogrulanan bulgular: (1) main dalina dogrudan push, CI kapi degil sonradan
dogrulama; (2) render.yaml ile .env.example arasinda iki bagimsiz elle
senkronize env kaynagi (9 FINPILOT_ENABLE_*/FRED_*/SEC_EDGAR_* bayragindan
render.yaml'da sadece 1'i var); (3) yfinance pinlenmemis (bilinen kirilgan
veri-kaynagi bagimliligi) + duckduckgo-search cakisan cift satir; (4)
scanner/data_fetcher.py'de genis kapsamli sessiz exception yutma; (5)
tests/test_scanner_contract.py fixture yoksa skipTest ile sessizce geciyordu;
(6) EN KRITIK: tests/test_ranking_guard.py, scanner.evaluate._execution_contract
import ediyordu — bu fonksiyon 07-15'te (2c60744) scanner.execution_policy.
execution_contract'a tasinmis ama test guncellenmemis; ImportError butun pytest
collection'ini 14 gundur (6+ sonraki commit boyunca) durduruyordu.
Karar: FinPilot_UcaUca_Uygulama_Plani_2026-07-24.md'ye "BOLUM 3-EK" eklendi
(Bolum 3 yeniden acilmadan, bulgular kayda gecirildi). Level A kalemleri
UYGULANDI: (a) test_ranking_guard.py import+assertion duzeltildi (davranis
degismedi, sadece dogru sembole baglandi — tier siniflandirmasi elle
dogrulandi), (b) test_scanner_contract.py skipTest -> fail, (c) ci.yml
--cov=distribution eklendi, (d) requirements.txt yfinance==1.4.1 pinlendi +
yinelenen duckduckgo-search satiri silindi.
Etki alani: tests/test_ranking_guard.py, tests/test_scanner_contract.py,
.github/workflows/ci.yml, requirements.txt. Scanner/distribution PRODUCTION
kodu davranissal olarak degismedi — sadece test/CI/bagimlilik katmani.
Sinir: render.yaml/.env birlestirme (3E.7), dry-run zorunlulugu (3E.8), erken
uyari sistemi (3E.9) Level B — Merric onayi bekliyor, henuz uygulanmadi.
Kanit: bu oturumdaki forensic analiz + pytest tam-suit calistirma sonucu
(asagida ayri girdi olarak eklenecek).
Durum: Level A kismi uygulandi; Level B kismi pending.

[2026-07-29] - Scanner kirilma/regresyon kok neden forensic analizi + Bolum 3-Ek DOGRULAMA sonucu (Level A dogrulandi, 2 yeni Level B/C bulgu)
Baglam: Bir onceki 07-29 kaydindaki 4 Level A degisiklikten sonra tam pytest
suit calistirildi (734 passed, 15 failed, 6 skipped, 380.81s,
--cov-fail-under=70 uygulanarak).
Dogrulanan sonuclar:
(1) test_ranking_guard.py fix ONAYLANDI — collection artik 0 hata (once: 1
collection error, tum suit durmustu). Hedeflenen 4 dosyanin (test_ranking_guard,
test_scanner_contract, test_distribution, test_prepublish_gate) 47 testi ayrica
izole calistirildi: 47 passed.
(2) YENI BULGU — 15 test kirmizi, hicbiri bu oturumda degistirilen 4 dosyayla
ilgili degil (test_evaluate.py, test_catalyst.py, test_squeeze_factor.py,
test_full_universe_robustness.py, test_new_endpoints.py, test_content_layer.py,
test_api_runtime.py, test_prometheus.py, scanner_rollout/test_runtime_baseline.py).
Dogrulandi: bunlar 07-15'ten beri collection hatasi yuzunden gorunmez olan,
onceden var olan olasi regresyonlar (orn. compute_recommendation_score beklenen
disi skor, dedup_symbol_day() policy kwarg'i kabul etmiyor). Olasi, test
edilmeli: her biri ayri kok-neden gerektirir — bu oturumda DUZELTILMEDI (kapsam
disi, tek tek incelenmeden production kodu degistirilmedi).
(3) YENI BULGU — --cov-fail-under=70 esigi FAIL (gercek: 43.47%). Esik
2026-03-30'da (a9f65923) 30'dan 70'e cikarilmis. Dogrulandi (hesaplandi):
distribution/ modulu kendi icinde ~63% kapsaniyor, ortalamayi dusuren o degil —
drl/ altinda binlerce satir %0 kapsanan modul (data_loader.py, ensemble_router.py,
inference.py, specialists.py vb.) asil neden. Yani bu oturumdaki --cov=distribution
eklemesi (3E.3) bu FAIL'e neden OLMADI — hesaplama distribution dahil/haric
karsilastirmasi ile dogrulandi (~%42 -> ~%43, iyilesme yonunde). Olasi, test
edilmeli: gercek CI ortaminda (GitHub Actions) bu esik hic gecmis mi yoksa
yakinda mi bozulmus — bu ortamdan GitHub Actions calisma gecmisine erisilemedi
(repo'da PR yok, direkt main'e push), dogrulanamadi.
Karar: FinPilot_UcaUca_Uygulama_Plani_2026-07-24.md Bolum 3-Ek tablosuna 3E.11
(15 test hatasi triyaji, Level B, onay bekliyor) ve 3E.12 (coverage esigi
politika karari, Level B/C, karar bekliyor) eklendi. 3E.5 gercek sonucla
guncellendi. 3E.6 (git tag) notu: 15 kirmizi test varken "stable" etiketi
yaniltici olur, 3E.11 triyaj edilmeden atilmamali.
Etki alani: sadece dokumantasyon (plan + decision-log). Hicbir production veya
test kodu bu adimda degistirilmedi.
Sinir: 3E.7 (render/env), 3E.8 (dry-run), 3E.9 (erken uyari), 3E.11 (15 test
triyaji), 3E.12 (coverage esigi karari) hepsi Level B/C — Meric onayi bekliyor.
git add/commit/push YAPILMADI — bu da ayri onay gerektirir.
Durum: Level A bolumu dogrulanarak kapatildi; 5 Level B/C kalemi (3E.7-3E.9,
3E.11, 3E.12) pending.

[2026-07-28] - Donanim arastirmasi gereksinim fazi (Level B/C, pending)
Baglam: FinPilot icin 7/24 yerel AI ve agent altyapisi donanim arastirmasi
baslatildi. Repository incelemesi, API/scheduler/veri akisi CPU-I/O agirlikli;
genel Ollama modeli `qwen2.5:3b`, Academy modeli `qwen2.5:7b` ve varsayilan
execution modu `dry_run` oldugunu gosterdi.
Karar onerisi: Gereksinim matrisi
`reports/hardware_research_requirements_20260728.md` icinde kayda alinsin.
Model boyutu, context/concurrency, butce, hedef ortam, uptime/RPO-RTO ve
paper/DRL kapsami netlesmeden GPU, sistem veya satin alma onerisi
kesinlestirilmesin.
Sinir: Bu kayit satin alma, butce, yeni servis/queue mimarisi, deployment,
paper/live execution veya runtime davranisi onaylamaz.
Durum: pending - Level B onerisi ve Level C insan karari bekleniyor.

[2026-07-28] - Karsilastirmali strateji test raporu (Level A)
Baglam: Kullanici talebiyle tum arastirma fazlarinin proxy, path-aware,
orneklem, maliyet, sonuc ve guven seviyesi acisindan tek raporda
karsilastirilmasi istendi.
Karar: `reports/strategy_comparative_test_report_20260728.md` olusturuldu.
Close-to-close proxy ile path-aware execution ayrimi korunacak; kucuk pozitif
alt gruplar aday olarak kalacak; ana V2 path-aware locked-OOS sonucu NO EDGE
olarak raporlanacak; spread/impact ve bos walk-forward fold'lari
`insufficient_data` olarak kalacak.
Sinir: Bu kayit yeni scanner, entry, exit, score, sizing, risk, portfolio,
paper/live veya scheduler kurali onaylamaz.
Kanıt: Karsilastirmali rapor ve altinda listelenen phase artifact'lari.
Durum: Uygulandi; arastirma raporu olarak kaydedildi.

[2026-07-28] - Sequential strategy research execution (Level A)
Context: The council-recommended research sequence was executed without
changing production behavior. The run covered input manifest, deterministic
contracts, entry/ranking, path-aware exits and costs, finite-slot portfolio
screens, calibration, regime diagnostics, and walk-forward availability.
Decision: Store outputs under
`data/backtest_out/research_start_20260727/` and report proxy labels,
path-aware labels, cost assumptions, sample sizes, and missing-data verdicts
separately. Preserve all current scanner, entry, exit, sizing, risk, paper,
live, and scheduler rules.
Evidence: `reports/strategy_scenario_test_results_20260727.md` and the phase
artifacts referenced there. Focused deterministic suite: 62 passed. The main
V2 path-aware locked-OOS execution remained approximately flat (n=62,
-0.0046% net expectancy, PF 0.9993); small ATR/RVOL subsets remain hypotheses
only. Spread/impact and a valid walk-forward test fold remain unavailable.
Status: applied as research execution and reporting only; no Level B/C change
approved.

[2026-07-28] — Sohbet içi yayın önizlemesi ve açık onay akışı (Level B, pending)
Bağlam: Tarama export'u tam olsa bile Telegram ve web yayını dış yan etkili işlemler. İçerik önce insan tarafından burada görülmeden yayınlanmamalı.
Değişiklik önerisi: `scripts/preview_publish.py` yalnızca gate kontrolü, Telegram taslağı ve web public görünümü üretir; queue, Telegram API, published snapshot ve deploy hook çağırmaz. Açık `YAYINLA` onayından sonra `scripts/publish_now.py --yes` çalıştırılır.
Etki alanı: `scripts/preview_publish.py`, `docs/ops/YAYIN_ONIZLEME_ONAY_AKISI_20260728.md`. Scanner, product, risk, sizing, entry/exit ve live strateji kuralları değişmedi.
Durum: pending — Level B; canlı yayın akışı için Meriç onayı bekleniyor.

[2026-07-27] — Strategy red-team audit follow-up (Level B, pending)
Bağlam: `reports/strategy_red_team_audit_20260727.md`, mevcut strateji kanıtlarında iki kritik sınır tespit etti: 2026-05-05 walk-forward/Monte Carlo raporundaki negatif veya zayıf OOS sonuçları ile 2026-05-11 haftalık raporundaki izlenebilirliği eksik pozitif sonuç uzlaştırılmamış; ayrıca `resolved_pct_t5 >= 5%` close-to-close proxy'si path-aware execution/P&L kanıtı değildir.
Öneri: P0 olarak rapor reconciliation, locked-OOS yeniden üretimi ve forward OHLC/path-aware execution replay; P1 olarak liquidity/cost, survivorship/missingness, rejim-sektör yoğunlaşması ve calibration testleri; P2 olarak kullanılmayan model bileşenleri ile operasyonel state persistence incelemesi yürütülsün.
Sınır: Bu kayıt onaylanmış strateji değişikliği değildir. `/01-product/*`, scanner weights, entry/exit, sizing, leverage, risk policy ve live execution değiştirilmedi. Eksik veri `insufficient_data` olarak raporlanmalı; default veya sıfır değerle tamamlanmamalı.
Sahip / kanıt / kapı: Araştırma sahibi atanacak; her test dataset hash, tarih aralığı, row count, canonical symbol-day politikası, cost assumption, label türü, trade count ve missingness paydasını kaydedecek. İnsan onayı ve karar günlüğünde açık bir uygulama kaydı olmadan hiçbir P0/P1/P2 önerisi canlı kurala dönüşmeyecek.
Durum: pending — Level B; karar ve uygulama için Meriç onayı bekleniyor.

[2026-07-27] — Araştırma canonical symbol-day politikası (Level A)
Bağlam: `full_universe_robustness.py` aynı symbol-day içindeki ilk CSV satırını seçiyor, bu da sonucu dosya sırasına bağımlı kılıyordu. Ayrıca hedef metadata'sı close-to-close alanını peak-touch gibi tanımlıyordu.
Değişiklik: Varsayılan canonical seçim `earliest scan_ts` oldu; `latest` duyarlılık seçeneği eklendi ve hedef metadata'sı `resolved_pct_t5 >= 5%` close-to-close proxy olarak düzeltildi. Araştırma çıktısında politika ve veri sınırı kaydediliyor.
Etki alanı: `full_universe_robustness.py`, `tests/test_full_universe_robustness.py`.
Durum: uygulandı; scanner, product kuralları ve live execution değiştirilmedi. İlk araştırma koşusu `data/backtest_out/research_start_20260727/` altında üretildi.

[2026-07-24] — Karne penceresi 30 gün (Karar A)
Bağlam: Karne DB-fallback'i kuruldu; 5 günlük pencerede örneklem çok küçük (B n=9).
Değişiklik: FINPILOT_KARNE_WINDOW_DAYS=30 (.env + .env.example). Öncesi: sabit 5 gün (API varsayılanı).
Etki alanı: distribution/karne.py, snapshot karne alanı, web LedgerStrip.
Durum: uygulandı.

[2026-07-24] — Masthead ana istatistiği süreç sayısına dönüşür (Karar B)
Bağlam: Dürüst karne dolduğunda canlı ağırlıklı isabet ~%2 çıkacak; "%68 backtested" ile aynı vitrinde duramaz, çıplak %2 de tek başına yanıltıcı/yıkıcı.
Değişiklik: Masthead'de oran yerine şeffaflık/süreç sayısı ("5.700+ pick publicly tracked since Sep 2025" formunda); grade bazlı isabet oranları yalnız LedgerStrip'te, pencere etiketiyle. Öncesi: karne boşken etiketli backtest oranı, doluysa canlı ağırlıklı oran.
Etki alanı: web Masthead.tsx (+ i18n metinleri), LedgerStrip, distribution/karne.py (tracked_total).
Durum: uygulandı (2026-07-24, Bölüm 4 — canlı sayı: 5.719 → "5,700+").

[2026-07-24] — DE dili kalır (eski "DE'yi gizle" önerisi geçersiz)
Bağlam: 07-23 ReAudit "DE anahtarı içeriksiz" diyordu; 24 Tem audit'i DE rationale'lerin snapshot'ta üretildiğini ve translations.ts DE bloğunun dolu olduğunu buldu.
Değişiklik: DE dil seçeneği kalır; aday metinleri artık rationale_i18n üzerinden üç dilde de gerçek içerik gösterir.
Etki alanı: web dil anahtarı, EditionArticle, DailyDouble.
Durum: uygulandı.

[2026-07-24] — Boş çekirdek DB tabloları resmen emekli (Karar C)
Bağlam: signals, scan_results, buy_signals aylardır boş; üretim zinciri JSON-export üzerinden akıyor. execution_intents/events/controls Alpaca planı kâğıtta olduğu için hiç kullanılmadı.
Değişiklik: Bu tablolar "emekli" statüsünde — şema KALIR, silinmez, yeni kod bunlara yazmaz/okumaz. Alpaca oto-execution işi resmen başlarsa execution_* tabloları geri açılır.
Etki alanı: core/database şeması (dokunulmadı), gelecekteki geliştirmelerin veri-yolu tercihi.
Durum: uygulandı (kayıt kararı; kod değişikliği gerekmiyor).

[2026-07-24] — Bölüm sırası değişikliği: 0→1→3, Bölüm 2 yarın sabaha
Bağlam: Bölüm 2'nin kanıtları (süre logu, seri sayacı, alarm testi) zaten sabah yayınından çıkacak; beklemek yerine Bölüm 3 sigortaları öne alındı.
Değişiklik: Uygulama planındaki 0→1→2→3 sırası fiilen 0→1→3→(2+4) oldu.
Etki alanı: FinPilot_UcaUca_Uygulama_Plani_2026-07-24.md takvimi.
Durum: uygulandı (Meriç onayı, 2026-07-24).

[2026-07-24] — regime_weights ve DRL_gate resmen PARK (Karar D)
Bağlam: FINPILOT_ENABLE_REGIME_WEIGHTS ve FINPILOT_DRL_GATE ikisi de skoru değiştiren deneysel özellikler; DRL placeholder feature'larla çalışıyor (üretim-dışı), hiçbiri backtest'le doğrulanmadı (Bölüm 8 audit).
Değişiklik: Her ikisi de PARKED. Varsayılan kapalı kalır (=0). Backtest ile kanıtlanmadan lansman öncesi AÇILMAZ. Kod/şema durur, silinmez; geri dönülebilir.
Etki alanı: core/regime_weights.py, core/scheduler.py DRL veto yolu, skorlama davranışı (değişmiyor).
Durum: uygulandı (Meriç onayı, 2026-07-24) — kod değişikliği gerekmiyor, bayrak zaten 0.

[2026-07-24] — Otomatik bakım işleri erken tek pencereye toplandı (Karar E)
Bağlam: Zamanlanmış cron işleri gün içine dağılmıştı ve calibration + daily_ops İKİSİ de 23:30 UTC'deydi (çakışma). Manuel yayın (~14:00) ve piyasa (13:30) ile de zamansal yakınlık riski.
Değişiklik: Tüm sabit-saatli bakım işleri erken sessiz pencereye (UTC 05:00–05:55, Viyana ~07:00) alındı ve kademelendi:

- Günlük: calibration 05:00 · daily_ops 05:10
- Pazar: research_pipeline 05:20 · ceo_report 05:40
- Pazartesi: calibration_retrain 05:20 · resolve_open_signals 05:35 · edge_report 05:55

Aynı gün içinde iki iş aynı dakikada değil; 23:30 çakışması yok; hepsi piyasa+manuel yayından çok önce. Interval işleri (main_cycle/eval/reconcile/drift/auto_approve) coalesce+max_instances=1 ile korunuyor, dokunulmadı.
Etki alanı: core/scheduler.py CronTrigger saatleri.
Durum: uygulandı (Meriç onayı, 2026-07-24; py_compile geçti).

[2026-07-28] — Bakım penceresi 12:00 Europe/Vienna'ya taşındı (Karar E güncelleme)
Bağlam: Karar E'de pencere 05:00 UTC (07:00 Viyana) idi; kullanıcı bakım penceresinin 12:00 Viyana'da olmasını istedi (aktif iş gününün başı, US açılışı 15:30 Viyana ve manuel yayından önce).
Değişiklik: 7 cron işi UTC yerine timezone="Europe/Vienna" + hour=12 ile (DST-güvenli), kademeli:
  Günlük: calibration 12:00 · daily_ops 12:10 · Pazar: research 12:20 · ceo 12:40 · Pazartesi: calibration_retrain 12:20 · resolve 12:35 · edge 12:55. Aynı gün içinde çakışma yok.
Ayrıca: telegram_bot_runner.py `telegram_config` import hatası düzeltildi (scripts/'ten çalışınca repo kökü sys.path'e ekleniyor + run_bot.py PYTHONPATH veriyor).
Etki alanı: core/scheduler.py, scripts/telegram_bot_runner.py, scripts/run_bot.py.
Durum: uygulandı (Meriç onayı, 2026-07-28; py_compile geçti).

[2026-07-28] — Level-B denetim: 5 KIRMIZI BAYRAK açıldı (pending, P0)
Kaynak: docs/audits/FinPilot_LevelB_IsPlani_Yayin_Audit_2026-07-28.md
Statü: AÇIK — her biri sorumlu+tarih atanana dek açık kalır.

- P0-a) Yasal sayfalar (Impressum + Datenschutz + AGB) YOK — Avusturya yasal zorunluluğu. Sahip: —, Tarih: —
- P0-b) SMTP sızan şifre rotate edilmedi (güvenlik). Sahip: —, Tarih: —
- P0-c) Traction ~0 (tg_users=1, feedback=0) — gerçek davet + teslim serisi. Sahip: —, Tarih: —
- P0-d) Premium/Stripe hiç test edilmedi (gelir=0). Sahip: —, Tarih: —
- P0-e) Site mesajı "AI stock" (compliance+repositioning riski) → literacy çerçevesi. Sahip: —, Tarih: —

Nihai değerlendirme: kamuya lansman HENÜZ DEĞİL; soft-launch koşullu.

[2026-07-28] — Yayın hattı kararları (Telegram+Web ön-taraması sonrası)

- Web deploy: git commit+push (publish_web.py → WEB_PUBLISH_CMD; REQUIRE_VERCEL_DEPLOY=0). Snapshot git'te izlenir, Vercel push'ta deploy eder.
- Scan: her sabah elle scan + publish_now (oto-taslak + insan onayı). DISTRIBUTION=0 kalır.
- Kanal adı @Finpilot_Breif ("Brief" yazım hatası) ŞİMDİLİK KORUNUR — lansmana kadar takipçi sıfırlamamak için; lansman öncesi yeniden değerlendir.

Durum: uygulandı (Meriç kararı, 2026-07-28); publish_web.py eklendi.

[2026-07-29] — Tek-dokunuşla yayın DOĞRULAMA (Faz 1): plan devrede DEĞİL — KOVA C açıldı (pending, P0)
Faz 1 bulgusu: web-deploy kancası ayarsız, bot-süpervizör dosyaları eksikti, waitlist aynası/admin-key/akademi-export ayarsız, hiçbir uçtan-uca tur doğrulanmadı.
KOVA C (kapanana dek AÇIK, Faz 3 kilitli):

- C1) FINPILOT_WEB_PUBLISH_CMD ayarsız → web yayını çalışmaz. Sahip: —, Tarih: —
- C2) Bot-süpervizör dosyaları eksikti → run_bot.py+start_bot.bat YENİDEN OLUŞTURULDU (bu oturum); startup+gözlem: —
- C3) WAITLIST_WEBHOOK_URL ayarsız → veri kaybı riski. Sahip: —, Tarih: —
- C4) SMTP rotasyonu doğrulanamadı (güvenlik P0). Sahip: —, Tarih: —
- C5) Uçtan-uca tam tur doğrulanmadı → kabul kriteri karşılanmadı. Sahip: —, Tarih: —

[2026-07-29] — Gerçek-makine doğrulama bulguları (kullanıcı denetimi) + kararlar
Bulgular: (1) .env'de FINPILOT_REQUIRE_VERCEL_DEPLOY İKİ KEZ (=1 ve =0) — çelişki; (2) bot süreçleri zaten çalışıyor (run_bot + telegram_bot_runner) → startup çift-bot/409 riski; (3) DB'ler journal_mode kontrolü yapılmadan hardening YAPILMADI (doğru); (4) komut satırında bir kimlik görüldü → rotasyon önerildi.
KARARLAR:

- REQUIRE_VERCEL_DEPLOY = **0** (tek satır; =1 SİLİNECEK). Neden: git-push deploy tetikler, ayrı hook yok; =1 publish'i "başarısız" sayar. (kod: _push_snapshot_to_web)
- Bot: startup'a eklemeden önce TEK poller garanti edilecek (Telegram 409 riski).
- DB hardening: yalnız journal_mode=wal ise + süreçler durdurulunca (aksi halde atla; büyük olasılıkla zaten delete).
- Kullanıcı Level B/C kapılarında (git push, gerçek yayın, SMTP, Sheet) açık onay olmadan İLERLEMEDİ — governance'a uygun, onaylandı.

Durum: kararlar kayıtlı; uygulama kullanıcının açık onayıyla, kendi makinesinde.

[2026-07-29] — İçerik/kalite doğrulama (Faz 1): gerçek sayılar + pending Level B/C
Gerçek sayılar: akademi 6 published/73 draft (rapor 5/39 = bayat); expired=11 (8 tarih); title hâlâ "AI-Powered Stock Intelligence"; yasal sayfalar HÂLÂ YOK (persist etmemiş); metodoloji route yok; bot anketi yok.
META: sandbox'ta oluşturulan bazı dosyalar diske ulaşmadı → her değişiklik git commit gerektirir.
Pending (Level B/C): metodoloji sayfası(B) · akademi yayın hattı(B) · positioning/title(B) · karşı-görüş satırı(B) · yasal sayfalar(C, yeniden oluştur+commit+avukat) · içerik takvimi(B) · evergreen SEO(B).
Bağımsız görüş: 1 numaralı kalite hamlesi = kesintisiz teslim (tutarlılık); akademi darboğazı yayınlama; okuyucu yokken içerik-zenginliği erken optimizasyon.

---

[2026-08-02] — FinPilot-native Control Center, Claude Cowork ve repo-native ortak beyin önerisi
Layer: Engineering / Operations / Agent Coordination
Level: B
Bağlam: Meriç'in ajanların ne yaptığını, blokajları, bekleyen onayları ve kanıt özetlerini tek yüzeyde izleyeceği bir yönetim kokpiti bulunmuyor. VS Code ana mühendislik ortamı olmasına rağmen ortak Work Item/Handoff task yüzeyi ve workspace konfigürasyonu da yok. GitHub Copilot, Claude Code, Claude Cowork ve FinPilot ürün ajanları aynı proje üzerinde çalışsa da geliştirme ve araştırma işi için ortak `work_item_id`, sahiplik, devir, kanıt ve onay geçişi sözleşmesi bulunmuyor. Mevcut Redis agent state/events kısa ömürlü; signal events ise finansal sinyal yaşam döngüsüne özel. Mevcut Next.js dashboard, auth context, otonomi onay/audit yüzeyi ve FastAPI admin endpoint kalıpları FinPilot-native bir kontrol merkezi için yeniden kullanılabilir.
Değişiklik (önce/sonra): v0.3 taslağında Buzz Meriç'in Control Cockpit'i olarak önerilmişti. Önerilen v0.4 modelinde FinPilot web uygulamasındaki ayrı ve default-deny `/ops` alanı Meriç'in Control Center'ı; VS Code Engineering Workbench; repo kalıcı Shared Brain / Source of Truth; GitHub Copilot ve Claude Code tek-owner kurallı kod yürütücüleri; Claude Cowork kaynaklı araştırma, doküman/korpus ve operasyon yürütücüsüdür. Work Item + Handoff + Evidence araç-bağımsız sözleşmedir. Control Center önce read-only projeksiyon ve raporlarla açılır; geri yazma yalnız temiz pilot ve ayrı onay sonrasında kimlik doğrulanmış, allowlist'li intent olarak değerlendirilir. Buzz ana cockpit değildir; yalnız ihtiyaç kanıtlanırsa bildirim adaptörü olabilir. Ayrıntılı taslak ve fazlar `docs/2026-08-02-ortak-beyin-handoff-buzz-claude-yol-plani.md` içindedir. Bu kayıt uygulama veya mimari onay değildir.
Etki: Onaylanırsa yeni şema/CLI, `/ops` layout ve ekranları, Control API/projector/reconciler, kontrol panoları ve raporlar, `.vscode/tasks.json`, sınırlı extension önerileri, Copilot/Claude Code/Claude Cowork protokolü ve CI evidence köprüsü eklenir. Controlled intent ve Local Agent Bridge ayrı ve ayrıca onaylanan kapılardır. Scanner, distribution, publish, risk, secrets, deploy ve broker/emir davranışı bu öneriyle değişmez; bu alanlar mevcut insan kapılarında kalır ve Control Center tarafından çağrılamaz.
Durum: pending — Level B; Meriç mimari onayı bekleniyor. Uygulama yapılmadı.

---

[2026-08-07] — DURUM.md / LAUNCH_CHECKLIST.md seri+karne sayıları bayattı, canlı DB'ye karşı düzeltildi (Level A, dokümantasyon)
Layer: Documentation / governance
Level: A
Bağlam: Sabah nabzı sırasında DURUM.md ve LAUNCH_CHECKLIST.md'deki "10 ardışık işlem günü" sayacı (~2/10, 23-24 Tem) ve karne madde 5 durumu ("ilk dolu yayın bekleniyor, 25 Tem") 24 Temmuz'dan beri güncellenmemiş bayat notlardı. `distribution.db` (`broadcast_queue`) ve `data/distribution/snapshot_*.json` dosyalarına karşı doğrudan doğrulandı.
Bulgular: (1) `distribution.broadcast.publish_streak()` canlı DB'ye karşı çalıştırıldı → sonuç 4, 2 değil. 3-6 Ağu ardışık `sent`; seri en son 31 Tem'de kırılmış (o gün broadcast_queue'da hiç kayıt yok — taslak bile üretilmemiş), 20-22 Tem'deki eski "expired" kırılmasından ayrı, ikinci bir kopma. (2) Karne `overall` bloğu (bariyer-tabanlı beklenti +%0.40/işlem, %30.1 isabet, 3.36x asimetri, n=5206) aslında 28 Tem'den beri her yayında dolu — "ilk dolu yayın bekleniyor" notu yanlıştı, milestone zaten geçilmiş. `by_grade` ise gerçekten yeni doluyor: 3 Ağu'ya kadar boş, 4-6 Ağu'da B/C'de küçük örneklemle veri geldi (6 Ağu: B n=4, C n=2, A yok, ikisi de hit_rate 0.0 — düşük isabet/pozitif-skew profiliyle tutarlı, kırmızı bayrak değil).
Değişiklik: DURUM.md "⭐ Bu 6 haftanın TEK önceliği" bölümündeki seri metriği ~2/10 → 4/10 ve kaynak/tarih notuyla güncellendi. LAUNCH_CHECKLIST.md madde 1 (seri sıfırlanma tarihi ve mevcut seri) ve madde 5 (karne overall/by_grade ayrımı) canlı bulgularla yeniden yazıldı.
Etki: Yalnız iki durum dosyasındaki sayı/not metni değişti. Scanner/distribution/skor/risk/canlı yayın davranışı DEĞİŞMEDİ — bu salt bir dokümantasyon düzeltmesi (repository health, CORE ilkesi: "repository should become more consistent after every interaction").
Durum: uygulandı — Meriç talebiyle ("güncelle", 2026-08-07). Level A (yalnız durum dosyaları, karar/kural değişikliği yok).

[2026-08-10] - BU OTURUMUN (Copilot) GIRDILERI: kayit-boslugu duzeltmesi + Kapi-2 duzeltmesi (Level A)
Layer: Research / governance
Level: A
Context: Bu oturumda (GitHub Copilot) uretilen bulgular decision-loga "yazildi" denmesine ragmen yazilmamisti — Meric'in yakaladigi sistemik oruntu (4. kez). insert_edit_into_file araci bu dosyada tekrar tekrar basarili dondugu halde diske yazmadi; bu girdi dogrudan yazilarak kaydediliyor ve paralel surecin KONTROL TURU bulgulari dikkate alinarak duzeltiliyor.
Change: Bu oturumda uretilenler: (1) research/strategic_lab_2026_08_10.py + reports/strategic_lab_experiments_2026-08-10.md (18 deney, 17 COMPLETED + 1 PARTIAL, test 8/8); (2) research/ten_perspectives_lab_2026_08_10.py + reports/ten_perspectives_lab_2026-08-10.md (13 deney, 13/13, test 10/10); (3) research/mirror_analysis_2026_08_10.py + reports/mirror_analysis_2026-08-10.md (9 deney, 9/9, test 7/7); (4) fetch_full_universe_and_retest.py close-to-close alanlari (c2c_1d, c2c_5d, mae_t5) eklendi, export yeniden uretildi, tests/test_close_to_close_export.py 2/2; (5) reports/correct_order_analysis_2026-08-10.md ve reports/correct_order_protocol_2026-08-10.md; (6) reports/user_research_kit_2026-08-10.md (PR1/PR7/PR2) ve reports/preregistration_three_hypotheses_2026-08-10.md (H1-H3 kilitli).
KAPI-2 DUZELTMESI (Meric + paralel surec KONTROL TURU/#2): Bu oturumun headline sayilari (-2.39/+0.06 ve matched +0.50/-0.61) gun-kumeleme/etkin-orneklem standardini GECMEDI (t~-1.65 ve t~-0.86, anlamsiz). Protokolun kendi diliyle bunlar "bulgu" DEGIL, "kesif sinyali". Genel yon (eligible zayif) P1/Mirror-L4/P0-P3 uclusuyle tutarli ama bu spesifik sayilar kendi baslarina istatistiksel olarak saglam degil. "Iki yillik edge anlatisi" ifadesi kaynaksiz (program verisi <1 yil) — duzeltildi.
Evidence: Yukaridaki dosyalar; paralel surecin KONTROL TURU girdileri.
Impact: Uretim davranisi degismedi. Bu oturumun tum bulgulari Kapi-2 standardini gecmedigi icin KESIF SINYALI statüsünde; hicbiri "kanitlanmis" sayilmamali.
Status: applied - research-only; kayit-boslugu kapatildi, Kapi-2 duzeltmesi yansitildi.

[2026-08-10] - Kapi zinciri ilk 5 is uygulandi (Level A)
Layer: Research / engineering
Level: A
Context: Onaylanan 4-kapi protokolunun bu haftalik 5 isi (1.3, 1.4, 2.2, 2.3, 3.2) uygulandi. Hepsi Level A, yeni izole modul veya mevcut modulun genisletilmesi.
Change: (1.3) `research/feature_lineage.py` — her feature icin provenance sozlesmesi (knowable_at, lookback, source, leakage_risk); forward-looking alanlar (resolved_pct_t5, c2c_*, mae_t5) yuksek-leakage olarak isaretli; validate_feature_set leakage denetimi. (1.4) `research/restatement_detector.py` — ayni (symbol,date) barinin iki cache snapshoti arasinda degisimini tespit eden pilot. (2.2) `research/experiment_registry.py::budget_report` — toplam konfigürasyon + aile-bazinda harcanan sans butcesi + run-status dagilimi. (2.3) `research/null_preflight_gate.py` — aday sonucunu null dagilimina karsi degerlendirip "finding" vs "discovery_signal" (kesif sinyali) verdicti uretir; null preflight'i zorunlu-gate mantigi. (3.2) `research/signal_half_life.py` — durust c2c etiketiyle eligible kohortun gerceklesen getirisinin gün-1 vs gün-5 dagilimi.
Evidence: `tests/test_gate_modules_2026_08_10.py` 7/7; py_compile temiz. 3.2 gercek veri sonucu (yeniden uretilen export, 1,094 eligible): day1 medyan -0.28%, day5 medyan -0.83%, day1-share-of-day5 medyan 0.20 — edge gun-1'de yogunlasmiyor (cunku edge yok); "sinyal var ama gec yakalaniyor" bahanesi elendi.
Impact: Uretim davranisi degismedi. Kapi 1.3/1.4 sema+pilot, Kapi 2.2/2.3 mekanizma, Kapi 3.2 ilk olcum hazir. Kapi 1.2/1.5 (veri kaynagi) ve 3.1/3.3/3.4 (spread/intraday/capacity) hala acik ve Level B/veri-kaynagi karari gerektirir.
Status: applied - research-only gate infrastructure; no production decision.

[2026-08-10] - Durust Quant Arastirma El Kitabi paketlendi (Level A)
Layer: Product / content
Level: A
Context: Gelir yaratma analizinde Yol 3 (mevcut icerigi paketleme) secildi ve
uygulandi. 38 research raporu + 261 glossary terimi + methodology icerigi tek
bir tutarli el kitabinda birlestirildi.
Change: `reports/honest_quant_handbook_2026-08-10.md` — 8 bolum (etiket,
orneklem, skor, secim, kalibrasyon, coklu-test, execution yalani + dogru sira
sentezi) + arac seti eki + kontrol listesi. Her bolum gercek bir hatayi,
onu yakalayan testi ve cikan dersi anlatir. `reports/honest_quant_handbook_distribution_2026-08-10.md` —
satis sayfasi metni (3 baslik varyanti), fiyatlandirma (ucretsiz/e19/e39),
dagitim kanallari (Gumroad/Lemon Squeezy/Twitter/LinkedIn/HN), donusum hunisi
(el kitabi -> bulten -> danismanlik -> acik kaynak).
Evidence: El kitabindaki tum sayilar mevcut research raporlarindan derlendi;
yeni iddia yok. Kapi-2 duzeltmesi yansitildi (headline sayilar "kesif sinyali"
olarak etiketli).
Impact: Uretim davranisi degismedi. Bu bir icerik paketleme calismasidir;
yayin karari Meric'e aittir. Gelir potansiyeli: dusuk-orta (icerik satisi),
yuksek (danismanlik hunisi girisi).
Status: applied - content packaging; publishing decision pending Meric.
