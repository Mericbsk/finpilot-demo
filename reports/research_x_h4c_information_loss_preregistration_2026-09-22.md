# RESEARCH-X/H4C — Information-Loss Pre-Registration (Mapping-Only)

**Tarih:** 2026-09-22
**Layer:** Research
**Level:** A (read-only research; production davranışı değişmez)
**Status:** **APPROVED / LOCKED — runner yazımı onaylı (2026-09-22)**
**Phase:** 3 — mapping information-loss measurement
**Predecessors:**
`reports/research_x_h4a_resolution_compression_2026-09-21.md`,
`reports/research_x_h4b_ranking_mapping_2026-09-21.md`

Bu belge sonuç görülmeden önce H4C'yi tek bir ölçülebilir soruya kilitler.
H4C bir runner değildir; bu dosya onaylanmadan hiçbir H4C kodu yazılmaz.

**Production ordering:** `UNKNOWN / NOT RECONSTRUCTED`
**Official production ranking resolution:** `DEFINITION_REQUIRED`

Bu iki satır bu belgenin değiştirilemez başlığıdır. H4C'nin hiçbir bölümü
bunları kaldıramaz, yumuşatamaz veya sonuçları bunlara dayandıramaz.

## 0. H4B'den devralınan kilitli sınırlar

H4B şu sınırları kanıt olarak tespit etti; H4C bunları yeniden tartışmaz:

- `ranking_score` alanı vardır ve flag'e bağlı kaynak seçimi yapılır:
  `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=1` ise `composite_score`,
  aksi halde `legacy_quality_score` (runner/repo default `0`).
- `composite_score` ile `legacy_quality_score` aynı şey değildir; ayrı
  formüllerdir. İlişki measurable (Pearson `0.887466`, Spearman
  `0.884258`) ama identity değildir.
- Canonical export `ranking_score`, `legacy_quality_score` ve
  `ranking_method` alanlarını **persist etmez**; historical production
  ordering birebir yeniden üretilemez.
- Public snapshot ve summary/alert ayrı multi-key sıralama kullanır;
  ikisinde de explicit final tie-breaker yoktur.

## 1. Tek araştırma sorusu

**RX-H4C (primary, tek claim):** Reconstruct edilebilen
`composite_score ↔ legacy_quality_score` mapping'inde ölçülebilir bilgi
kaybı var mı?

Bu sorunun kapsamı **yalnızca** iki skor değeri arasındaki matematiksel
mapping'dir: canonical export'taki `composite_score` alanı ile H4B'nin
aynı satırlardan back-compute ettiği `legacy_quality_score` historical
proxy'si. Bu mapping reconstruct edilebilir; H4C yalnızca bunu inceler.

## 2. Kapsam dışı (değiştirilemez)

H4C aşağıdakilerin **hiçbirini** ölçmez, varsaymaz veya iddia etmez:

- Historical production ordering veya herhangi bir production rank.
- `ranking_score`'un production'da gerçekte hangi kaynaktan geldiği
  (canlı process state; runner bunu ölçmedi, ölçmeyecek).
- Snapshot/summary sort-tuple'ları üzerinden bir sıralama rekonstrüksiyonu.
- Production ranking'in hatalı olduğu iddiası.
- Ranking'in outcome'a information loss yüklediği iddiası.
- Composite score'un yeniden tasarlanması gerektiği iddiası.

**Yasak çıkarım zinciri:** "legacy_quality_score yüksek → production rank
yüksek → dolayısıyla ranking information loss". Bu zincirin herhangi bir
halkasının H4C sonucuna girmesi yasaktır; runner bu zinciri kodlayamaz.

## 3. Veri ve freeze sözleşmesi

### 3.1 Girdi ve proxy

- **Canonical input:** `data/backtest_out/full_universe_enriched_eod_only.csv`
  — H4A/H4B ile aynı dosya, aynı SHA-256
  (`87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`).
- **Dedup/filter:** H4B ile birebir aynı: `label_entry_basis == "eod_close"`,
  `(symbol, scan_date)` başına tek satır (en erken lexical `scan_ts`),
  `composite_score` non-null. Beklenen n = 40,014.
- **Proxy tanımı (değiştirilemez):** `legacy_quality_score` historical proxy,
  H4B runner'ındaki `load_legacy_quality_score()` ile yüklenen mevcut
  production fonksiyonu `scanner/score_engine.py::compute_legacy_quality_score`'un
  export alanlarından (`regime`, `direction`, `score`, `atr_pct_real`, `rvol`,
  `squeeze_factor`, `lottery_factor`, `overnight_gap_factor`) back-compute
  edilmiş halidir. H4C bu fonksiyonu yeniden yazmaz, değiştirmez, aynı
  yükleme yolunu kullanır.
- **Kapsam satırları:** Yalnızca proxy'nin hesaplanabildiği satırlar.
  H4B'de bu 39,986/40,014 idi; 28 satır `rvol` eksikliğinden düşer.
  H4C aynı exclusion'ı uygular; eksik satırları impute etmez.

### 3.2 Freeze

- Composite ve legacy formülleri, ağırlıkları, flag'ler, threshold'lar
  yeniden fit edilmez.
- Production ordering için herhangi bir tie-breaker, rank ataması veya
  sıralama simülasyonu **yapılmaz** — H4C sıralama üretmez.
- Yeni veri üretilmez; eksik `rvol` tahmin edilmez.
- Bu çalışma historical split-sample bile değildir; iki alan arası
  deskriptif mapping analizidir. Predictive veya economic claim içermez.

## 4. Önceden kilitlenen ölçümler

Tüm ölçümler `(composite_score, legacy_proxy)` satır çiftleri üzerindedir.
Hiçbiri production ordering'e referans vermez.

### 4.1 Primary endpoint — mapping bilgi kaybı

- **Cardinality contrast:** `unique(composite_score)` vs `unique(legacy_proxy)`.
  H4A/H4B referans değerleri: 90 vs 27,050. Runner bunları yeniden hesaplar
  ve artifact'la karşılaştırır.
- **Many-to-one profili:** Her `legacy_proxy` değerine map olan distinct
  `composite_score` sayısının dağılımı (median, max); her `composite_score`
  değerine map olan distinct `legacy_proxy` sayısının dağılımı.
- **Monotonicity violation:** `composite_A < composite_B` iken
  `legacy_proxy_A > legacy_proxy_B` olan sıralı çift payı (yalnızca iki skor
  arasında, production rank anlamı yüklenmeden). Bu mapping'in yönsel yapısını
  anlatan yardımcı metriktir; information-loss iddiasının ana kanıtı değildir.
- **Round-trip belirsizliği:** `composite → proxy → composite` için her
  composite değerinin proxy üzerinden açıklanan varyans payı ve açıklanamayan
  pay (yalnızca deskriptif; hiçbir "düzeltme" önerilmez).

### 4.2 Tie-internal proxy dispersion (primary kanıt metriği)

**TIE_INTERNAL_PROXY_VARIATION:** Aynı `composite_score` değerine sahip
gözlemler (tie group) içinde `legacy_proxy`'nin aldığı değerlerin dağılımı.

- Her composite tie group için: proxy std, proxy range (max-min), distinct
  proxy count.
- Gözlenen özet: tie group'ları arasında median std, median range, ve
  global tie-internal dispersion (tüm tie satırlarında group-demeaned proxy
  varyansı).

Bu metrik composite'ın proxy'deki farklılıkları ayırt edemediğini gösteren
conditional dispersion ölçüsüdür ve information-loss iddiasının **ana
kanıtıdır**. Monotonicity'den ayrı raporlanır.

### 4.3 Secondary endpoints (yönsüz, deskriptif)

- Score-frequency entropy / HHI / effective-count her iki skor için ayrı ayrı
  (H4A'nın `score_frequency_*` metodolojisi ile aynı formüller).
- Tarih başına (scan_date) aynı cardinality/tie metrikleri; gün bazında
  dalgalanma raporu. Günlerle production davranışı ilişkilendirilmez.
- Proxy'nin `integer_valued_fraction` karşılaştırması (H4B referans:
  `0.064573`) — proxy'nin de composite gibi integer-collapse yaşamadığının
  deskriptif teyidi.

## 5. Belirsizlik ve kontroller

- **Determinism:** Runner iki kez çalışır; JSON ve rapor SHA-256 birebir
  aynı olmalı. Farklılık = fail, sonuç raporlanmaz.
- **Eksik-girdi şeffaflığı:** Düşen 28 satır (veya runner'ın bulduğu sayı)
  alan bazında raporlanır; sayı H4B'den farklıysa runner durur ve
  `INPUT_MISMATCH` raporlar (sessizce devam etmez).
- **Kontrol — scan-date-preserving permutation null:** `legacy_proxy`
  değerleri her `scan_date` içinde fixed-seed ile random permute edilir
  (`R = 1,000`). Composite değerleri ve gün kompozisyonu sabit kalır; proxy'nin
  günlük marjinal dağılımı korunur; yalnızca ampirik `composite ↔ proxy`
  eşleşmesi kırılır. Her tekrarda tie-internal dispersion yeniden hesaplanır
  ve null dağılım üretilir.
  - **Neden `(symbol, scan_date)` içinde değil:** dedup sözleşmesi
    `(symbol, scan_date)` başına tek satır bırakır; bu gruplar singleton'dır
    ve içlerinde permutation değişiklik yaratmaz. Bu nedenle null, gün
    içinde tanımlanır.
  - Bu kontrol production ranking'i taklit etmez; yalnızca gözlenen
    tie-internal yapının skorların gerçek eşleşmesinden mi yoksa marjinal
    dağılımlardan mı kaynaklandığını ayırır.

## 6. Önceden kilitlenen verdict mantığı

**RX-H4C verdict yalnızca şu dört değerden biridir:**

- `INFORMATION_LOSS_SUPPORTED` — yalnızca şunların tamamı sağlanırsa:
  - **ana kanıt:** gözlenen tie-internal proxy dispersion, scan-date-preserving
    permuted-null dağılımın %95 üst bandının üzerinde,
  - cardinality contrast artifact değerleriyle uyumlu (90 vs 27,050
    civarı; ±%5 tolerans dışındaki sapma `INPUT_MISMATCH`),
  - determinism geçti,
  - input integrity geçti (satır/eksik-girdi sayıları H4B ile uyumlu).
  Many-to-one profili burada **descriptive supporting evidence**'dir;
  verdict'in gerek koşulu değildir, çünkü proxy→composite yönündeki
  compression 90-vs-27,050 cardinality farkından doğal olarak doğar.
- `INFORMATION_LOSS_NOT_SUPPORTED` — gözlenen tie-internal dispersion null
  bandı içindeyse (ana kanıt sağlanmadıysa).
- `INSUFFICIENT_DATA` — tie group'ları veya istatistiksel yapı null testi
  anlamlı kılacak kadar dolu değilse.
- `INPUT_MISMATCH` — kapsam satır sayısı, eksik-girdi sayısı veya artifact
  değerleriyle uyumsuzluk durumunda.

Hiçbir verdict production ranking, production ordering veya resolution
hakkında iddia üretmez. Verdict yalnızca iki skor arası mapping'i niteler.
`INFORMATION_LOSS_SUPPORTED` = composite_score ile legacy_quality_score
arasındaki mapping'de gözlenebilir bilgi ayrışması vardır; **production
ranking'in bilgi kaybettiği anlamına gelmez.**

## 7. Negative-result policy

- `INFORMATION_LOSS_NOT_SUPPORTED` geçerli ve raporlanabilir sonuçtur;
  "loss var" göstermek için post-hoc metrik eklenmez.
- Verdict ne olursa olsun composite formülü, legacy formülü, flag, scanner,
  ranking, scheduler veya user-facing yüzey değiştirilmez.
- Bu dosya hiçbir production değişikliğine yetki vermez. Mapping-ötesi
  herhangi bir ürün sonucu ayrı Level B kararı ve ayrı preregistration
  gerektirir.

## 8. Beklenen artifact'ler

Bu preregistration **onaylanmadan** aşağıdakilerden hiçbiri üretilmez:

- Runner: `research/research_x_h4c_information_loss_2026_09_22.py`
- JSON: `data/backtest_out/research_x_h4c_information_loss_2026-09-22.json`
- Sonuç raporu: `reports/research_x_h4c_information_loss_2026-09-22.md`

Runner bu belgedeki soruyu, kapsamı, freeze kurallarını, ölçümleri, kontrolleri
veya verdict mantığını değiştiremez. Sonuç raporu bu belgeye göre yazılır;
veri yetersizliği ve negatif sonuç geçerli sonuçlardır.

## 9. Açık kalan ve H4C'nin çözmediği konular

- Official production ranking resolution tanımı (`DEFINITION_REQUIRED`)
  bu çalışmayla çözülmez; ayrı bir tanım çalışması gerekir.
- Historical production ordering `NOT RECONSTRUCTED` kalır; H4C bunu
  değiştirmez.
- Mapping'de loss bulunsa bile bunun production outcome'a etkisi bu çalışmanın
  konusu değildir ve bu sonuçtan çıkarılamaz.

## Governance

- Research / Level A / read-only. Bu dosyanın kendisi de Level A draft'tır;
  runner yazımı bu dosyanın Meriç onayından sonradır.
- `scanner/`, `distribution/`, `api/`, web, score formülleri, flag'ler,
  scheduler, DB ve user-facing surface değiştirilmez.
- H2 `CLOSED / NOT_SUPPORTED`, H4A `CLOSED / COMPRESSION_SUPPORTED`,
  H4B `CLOSED / MAPPING_DEPENDS_ON_ADDITIONAL_INPUTS` olarak kalır; H4C
  bunları yeniden açmaz.
- Karar, onaylandığında `docs/governance/decision-log.md`'ye Level A
  preregistration-lock kaydı olarak yazılır (disk, salt-eklemeli).
