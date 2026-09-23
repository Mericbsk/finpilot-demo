# RESEARCH-X/H4D-measure — Production Ranking Resolution Measurement (Pre-Registration)

**Tarih:** 2026-09-22
**Layer:** Research
**Level:** A (read-only; measurement protocol only)
**Status:** **APPROVED / LOCKED — runner yazımı onaylı (2026-09-22)**
**Phase:** 5 — official production ranking resolution measurement
**Predecessor (kilitli tanım):**
`reports/research_x_h4d_ranking_resolution_definition_2026-09-22.md` (APPROVED/LOCKED)

Bu belge H4D-measure'ın **ölçüm protokolünü** kilitler. H4D-measure bir runner
değildir; bu dosya ayrıca incelenip kilitlenmeden hiçbir H4D-measure kodu
yazılmaz. Bu dosya yalnızca kilitli H4D tanımını girdi olarak alır.

**Bu dosya "resolution kaç?" sorusunu cevaplayacak ölçümü tanımlar;**
**"resolution yeterli mi / yetersiz mi?" sorusunu cevaplamaz.** İkinci soru
ancak ölçümden sonra ayrı bir yorumlama/decision aşamasıdır.

**NO:** production code, scanner, score, ranking, flag, scheduler, DB behavior
veya user-facing değişiklik. `production_impact = NONE`.

## 0. Kilitli tanımdan devralınan çerçeve

H4D-definition'ın kilitli hiyerarşisi bu ölçümün iskeletidir:

```
PRIMARY               = Candidate B  (production sort-tuple resolution)
SECONDARY/DIAGNOSTIC  = Candidate A  (score-space resolution, diagnostic)
OBSERVATIONAL         = Candidate C  (displayed-rank, provenance-dependent)
```

Ölçüm üç kavramı **birbirinden ayrı** ölçer; bunlar tek bir "resolution
score"a erkenden sıkıştırılmaz:

1. **Capacity** — full tuple kaç farklı anahtar kombinasyonu üretebiliyor?
2. **Collision / tie structure** — kaç observation aynı full tuple'a düşüyor?
3. **Determinism** — aynı full tuple içindeki nihai sıra declared production
   keys tarafından belirleniyor mu?

## 1. Historical reconstructability gate (önce bu)

Ölçüme başlamadan önce zorunlu bir kapı vardır. Production tuple/provenance
gerçekten reconstruct edilemiyorsa ölçüm **zorla yapılmaz**.

### 1.1 Field-presence envanteri (canonical export üzerinde)

Canonical export `data/backtest_out/full_universe_enriched_eod_only.csv`'nin
mevcut 33 kolonu içinde production sort-tuple alanlarının durumu (H4B artifact
`historical_columns` üzerinden doğrulanmıştır):

| Tuple alanı | Snapshot tuple | Summary tuple | Export'ta |
|---|---|---|---|
| `grade` | evet | — | **ABSENT** |
| `conviction_tier` | — | evet | PRESENT |
| `execution_confidence` | evet | evet | **ABSENT** |
| `conviction_prob` | evet | evet | **ABSENT** |
| `ranking_score` | (selected score kaynağı) | evet | **ABSENT** |
| `composite_score` | (fallback) | (fallback) | PRESENT |
| `legacy_quality_score` | (selected score kaynağı) | — | **ABSENT** |

### 1.2 Gate kararı (önceden kilitli)

- Snapshot tuple'ın 4 alanından 3'ü (`grade`, `execution_confidence`,
  `conviction_prob`) ve `ranking_score` export'ta **yok**.
- Summary tuple'ın 4 alanından 2'si (`execution_confidence`,
  `conviction_prob`) ve `ranking_score` **yok**.
- Dolayısıyla **full production sort tuple historical export'tan reconstruct
  edilemez.**

Gate sonucu (runner'ın üretmesi gereken, önceden tanımlı):

```
GATE = PROVENANCE_INSUFFICIENT
```

Bu, ölçümün başarısızlığı değil, önceden tanımlanmış geçerli bir durumdur ve
H4B'nin `UNKNOWN / NOT RECONSTRUCTED` bulgusunu bir varsayımla "çözmeye"
çalışmadığının kaydıdır.

**Preregistered expectation ≠ runner outcome (LOCKED):** Bu belgedeki
"öngörülen sonuç" ifadeleri yalnızca preregistration'ın prior expectation'ıdır.
Runner bunları önceden doğru varsayarak yazılmaz; reconstructability gate'i
gerçekten çalıştırır ve sonucu veriden üretir. Prior ile runner'ın bulduğu
gerçek outcome ayrı raporlanır. Candidate A'nın `MEASURED` olması yalnızca
mevcut `composite_score`/`score` alanlarının ölçülebilir olduğu anlamına gelir;
**"production resolution ölçüldü" anlamına kesinlikle gelmez.**

## 2. Önceden kilitlenen ölçüm sonuçları (verdict seti)

Runner yalnızca şu önceden tanımlı sonuçlardan birini üretir:

- `MEASURED` — yalnızca ilgili endpoint'in tüm tuple alanları ve provenance
  reconstruct edilebiliyorsa ve o endpoint için capacity/collision/determinism
  hesaplanabiliyorsa.
- `NOT_MEASURABLE / PROVENANCE_INSUFFICIENT` — endpoint'in full tuple'ı
  historical provenance'dan reconstruct edilemiyorsa.
- `PARTIAL` — yalnızca bazı endpoint'ler veya bazı alt-metrikler (örn. mevcut
  alanların alt-kümesi) ölçülebiliyorsa; hangi parçanın ölçülebildiği açıkça
  yazılır ve full-tuple sonucu olarak sunulmaz.
- `INPUT_MISMATCH` — canonical export SHA veya satır sözleşmesi H4A/H4B ile
  uyumsuzsa.

Endpoint başına sonuç ayrı raporlanır (snapshot / summary / score-space
diagnostic). Hiçbir `MEASURED` sonucu "resolution yeterli/yetersiz" yorumu
içermez.

## 3. Endpoint'ler ve ölçülebilirlik

### 3.1 Primary — Candidate B (production sort-tuple resolution)

- **Snapshot tuple:** `(grade, execution_confidence, conviction_prob,
  selected_score)`; `selected_score = ranking_score → legacy_quality_score →
  composite_score → score` fallback zinciri.
- **Summary tuple:** `(conviction_tier, execution_confidence,
  conviction_prob, ranking_score)`; `ranking_score` yoksa `composite_score`.
- **Öngörülen sonuç:** `NOT_MEASURABLE / PROVENANCE_INSUFFICIENT` — gerekli
  alanlar export'ta yok. Runner bunu alan-bazında kanıtıyla raporlar;
  eksik alanları impute etmez veya tuple'ı kısaltmaz.

### 3.2 Secondary / diagnostic — Candidate A (score-space resolution)

- Birim: mevcut skor alanlarının (`composite_score`, `score`) unique değer
  sayısı ve tie payı; H4A metrikleri (`unique_score_values`,
  `tie_observation_share`, `score_frequency_*`).
- **Öngörülen sonuç:** `MEASURED` (alanlar mevcut). Bu yalnızca diagnostic'tir;
  production ordering resolution'ı olarak sunulmaz (`score resolution ≠
  production ordering resolution`).

### 3.3 Observational — Candidate C (displayed-rank / final-order)

- Yalnızca provenance izin verdiği yerde. Historical export final input order
  ve explicit final tie-breaker içermediği için:
- **Öngörülen sonuç:** `NOT_MEASURABLE / PROVENANCE_INSUFFICIENT`.
  Canlı ölçüm gerekirse ayrı Level B kapsamındadır; bu runner yapmaz.

## 4. Ölçüm tanımları (ölçülebilen parçalar için kilitli)

Yalnızca reconstruct edilebilen endpoint/alt-metrikler için geçerlidir:

- **Capacity:** distinct full-tuple kombinasyon sayısı; tuple başına distinct
  alt-alan kombinasyonları. Raporlanır: `distinct_tuple_count`,
  `tuple_cardinality_ratio = distinct_tuple_count / observation_n`.
- **Collision / tie structure:** aynı full tuple'a düşen observation sayısının
  dağılımı; `full_tie_observation_share`, `tie_group_count`,
  `max_tie_group_size`, tie-group size buckets (H4A metodolojisi).
- **Tie concentration:** gün bazında ve global tie payı; H4A'nın
  `daily_resolution` yaklaşımı.
- **Determinism:** aynı full tuple içinde nihai sıranın declared keys
  tarafından belirlenip belirlenmediği. Explicit final tie-breaker olmadığından,
  full-tie group'larında determinism `UNDETERMINED_AT_FINAL_TIE` olarak
  raporlanır; bu bir defect değildir, tanım gereğidir (H4D lock).

## 5. Veri, normalizasyon ve null politikası

- **Input:** `data/backtest_out/full_universe_enriched_eod_only.csv`, SHA-256
  `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`; H4A/H4B
  ile birebir aynı dedup/filter (`eod_close`, `(symbol, scan_date)` başına tek
  satır, en erken lexical `scan_ts`, `composite_score` non-null, n = 40,014).
- **Snapshot vs summary ayrımı:** iki tuple ayrı tanımlanır ve asla tek tuple'a
  birleştirilmez.
- **Tuple normalization / type handling:** her alan için tip sabitlenir
  (categorical string, numeric float); `None`/`NaN` değerler ayrı bir
  `NULL_BUCKET` kategorisine konur, sessizce 0 veya "" yapılmaz.
- **Missing/null politikası:** bir tuple alanı eksikse o satır o endpoint için
  ölçüm dışıdır ve `excluded_due_to_missing_field` olarak sayılır; impute
  edilmez. Bir alan tüm export'ta yoksa o endpoint `NOT_MEASURABLE` olur.

## 6. Belirsizlik, randomization ve multiple-testing

- **Permutation/randomization:** Bu ölçüm deskriptif kapasite/tie yapısı
  ölçtüğü için bir null model **gerekmez**. Hiçbir permuted-null veya
  istatistiksel anlamlılık testi uygulanmaz; bunlar H4C tarzı bir nedensel
  soruya aittir ve burada kapsam dışıdır. (Eğer ileride "tie yapısı rastgele
  mi?" sorusu sorulursa, o ayrı bir preregistration olur.)
- **Multiple-testing:** Hipotez testi yapılmadığından multiple-testing
  düzeltmesi uygulanmaz. Tüm metrikler deskriptif raporlanır; p-value üretilmez.
- **Determinism/reproducibility:** Runner iki kez çalışır; JSON ve rapor
  SHA-256 birebir aynı olmalı. Farklılık = fail, sonuç raporlanmaz. Herhangi
  bir randomness kullanılırsa (kullanılmamalı) fixed seed zorunludur.

## 7. Negative / ölçülemez sonuç politikası

- `NOT_MEASURABLE / PROVENANCE_INSUFFICIENT` ve `PARTIAL` geçerli ve
  raporlanabilir sonuçlardır; "ölçmek" için tuple kısaltılmaz, alan impute
  edilmez, provenance uydurulmaz.
- `MEASURED` bir endpoint bile "resolution yeterli" anlamına gelmez; bu dosya
  yalnızca değeri raporlar.
- Verdict ne olursa olsun composite formülü, legacy formülü, tuple tanımı,
  flag, scanner, ranking, scheduler veya user-facing yüzey değiştirilmez.
- Bu dosya hiçbir production değişikliğine yetki vermez.

## 8. H4D-measure'ın cevaplamadığı sorular

- "Resolution yeterli mi / yetersiz mi?" — kapsam dışı; ölçüm sonrası ayrı
  yorumlama/decision aşaması.
- "Resolution'ı artırmak için tie-breaker eklenmeli mi?" — kapsam dışı;
  Level B ürün kararı.
- "Production ranking doğru mu?" — kapsam dışı; H4B/H4C sınırları geçerli.

## 9. Beklenen artifact'ler (onaydan önce üretilmez)

- Runner: `research/research_x_h4d_measure_2026_09_22.py`
- JSON: `data/backtest_out/research_x_h4d_measure_2026-09-22.json`
- Sonuç raporu: `reports/research_x_h4d_measure_2026-09-22.md`

Runner bu belgedeki input population, snapshot/summary ayrımı, tuple field
tanımları, normalization, null politikası, capacity/collision/determinism
ölçümleri, reconstructability gate, verdict seti ve determinism kurallarını
değiştiremez.

## Governance

- Research / Level A / read-only / measurement protocol. Bu dosya draft'tır;
  runner yazımı bu dosyanın Meriç onayından ve ayrı kilidinden sonradır.
- `scanner/`, `distribution/`, `api/`, web, score formülleri, flag'ler,
  scheduler, DB ve user-facing surface değiştirilmez.
- H2/H4A/H4B/H4C/H4D-definition olduğu gibi kalır; H4D-measure bunları
  yeniden açmaz.
- Karar, onaylandığında `docs/governance/decision-log.md`'ye Level A
  measure-preregistration-lock kaydı olarak yazılır (disk, salt-eklemeli).
