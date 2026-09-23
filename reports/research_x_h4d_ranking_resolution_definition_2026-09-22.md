# RESEARCH-X/H4D — Production Ranking Resolution Definition (Definition-Only)

**Tarih:** 2026-09-22
**Layer:** Research / Product-boundary (definition)
**Level:** A (read-only; definition only — no measurement, no code)
**Status:** **APPROVED / LOCKED — definition kilitli (2026-09-22)**
**Phase:** 4 — official production ranking resolution definition
**Predecessors:**
`reports/research_x_h4a_resolution_compression_2026-09-21.md`,
`reports/research_x_h4b_ranking_mapping_2026-09-21.md`,
`reports/research_x_h4c_information_loss_2026-09-22.md`

Bu belge bir **tanım** preregistration'ıdır. H4D bir runner değildir ve bu
haliyle hiçbir sayı üretmez. Amacı, H4B'nin `DEFINITION_REQUIRED` olarak
bıraktığı kavramı — *official production ranking resolution* — ölçülebilir
şekilde tanımlamak ve kilit altına almaktır. Ölçüm, ayrı bir H4D-measure
preregistration ve ayrı onay gerektirir.

**Bu dosya hiçbir production rank, ordering veya score üretmez.**
**Bu dosya hiçbir score, ranking, scanner veya publication değişikliği önermez.**

## 0. H4B'nin bıraktığı tanım boşluğu

H4B, official production ranking resolution'ı `DEFINITION_REQUIRED` olarak
bıraktı ve gerekçesini kaydetti:

> "The export has a composite score but no persisted ranking score, and the
> code uses a multi-key publication tuple with no explicit final tie-breaker."

Bu boşluğun üç bileşeni vardır; H4D'nin tanımı üçünü de ayrı ayrı ele
almalıdır:

1. **Alan belirsizliği:** Hangi skor alanı "production ranking skoru"dur?
   (`composite_score`, `ranking_score`, `legacy_quality_score` — export'ta
   `ranking_score` persist edilmiyor.)
2. **Sort-tuple belirsizliği:** Production ordering tek bir skordan değil,
   multi-key sort tuple'ından gelir. Resolution hangi tuple düzeyinde ölçülür?
3. **Tie-breaker yokluğu:** Snapshot ve summary sıralamasında explicit final
   tie-breaker yoktur; eşit anahtarlı satırlar input order'a kalır. Resolution
   tanımı bu durumu nasıl hesaba katar?

## 1. Tek tanım sorusu

**RX-H4D (tek claim):** "Official production ranking resolution" tam olarak ne
demektir ve hangi ölçülebilir birim/metrik üzerinden tanımlanır?

Bu soru **yalnızca tanımdır**. "Resolution kaçtır?" veya "resolution yetersiz
mi?" gibi değer/verdict soruları H4D kapsamı dışındadır.

## 2. Kapsam dışı (değiştirilemez)

H4D aşağıdakilerin **hiçbirini** yapmaz:

- Hiçbir skor, rank, ordering veya resolution **değeri** hesaplamaz.
- Production ordering'i reconstruct etmez veya simüle etmez.
- Historical ranking'i "doğru" veya "yanlış" olarak nitelemez.
- Tie-breaker **eklenmesini** önermez; yalnızca tie-breaker yokluğunun tanımı
  nasıl etkilediğini belgeler.
- H2/H4A/H4B/H4C'nin verdict'lerini yeniden açmaz veya değiştirmez.
- Hiçbir production kodu, flag, formül, scanner, scheduler veya user-facing
  yüzey değiştirmez.

## 3. Tanım adaylarının envanteri (LOCKED hiyerarşi)

H4D, resolution'ın hangi **birim** üzerinde tanımlanabileceğini haritalar ve
hiyerarşiyi kilitler. Kilitli roller:

- **PRIMARY — Candidate B (Sort-tuple resolution).**
- **SECONDARY / DIAGNOSTIC — Candidate A (Score-space resolution).**
- **OBSERVATIONAL ENDPOINT / PROVENANCE-DEPENDENT — Candidate C
  (Displayed-rank resolution).**

### 3.1 Candidate A — Score-space resolution (SECONDARY / DIAGNOSTIC)

Resolution, tek bir skor alanının ayırt etme kapasitesi olarak tanımlanır.
Birim: seçili skor alanının unique değer sayısı ve tie payı.

- H4A metrikleri yeniden kullanılır: `unique_score_values`,
  `tie_observation_share`, `score_frequency_*`, `nominal_integer_scale_values`.
- **Ölçer:** bir skor alanının kendi başına ne kadar ayrıştırdığını.
- **Ölçemez:** production ordering'in kendisini (sort tuple'ı ve tie-breaker'ı
  hesaba katmaz). H4A'nın composite için yaptığı budur.
- **Rol (LOCKED):** Secondary/diagnostic. `score resolution ≠ production
  ordering resolution` ayrımını korumak için tutulur; compression bulgularının
  yanlış yorumlanmasını engeller.

### 3.2 Candidate B — Sort-tuple resolution (PRIMARY)

Resolution, production'un kullandığı tam sort tuple'ının ayırt etme
kapasitesi olarak tanımlanır. Birim: tuple'ın ürettiği distinct sıralama
anahtarı sayısı ve tuple-eşitlik (full-key tie) payı.

- Snapshot tuple: `(grade, execution_confidence, conviction_prob, selected_score)`.
- Summary tuple: `(conviction_tier, execution_confidence, conviction_prob, ranking_score)`.
- **Ölçer:** production sıralama mantığının tuple düzeyinde kaç ayrı konum
  ürettiğini.
- **Ölçemez:** final tie-breaker olmadığından, tuple-eşit satırların nihai
  sırasını. Bu düzey hâlâ input order'a bağımlıdır.
- **Rol (LOCKED):** PRIMARY. Soru artık "bir skor kaç değer üretiyor" değil,
  "production'ın gerçekten kullandığı sıralama anahtarı kaç ayrıştırılmış
  sıralama anahtarı üretiyor". Production ranking davranışsal olarak multi-key
  tuple ise, official resolution tek skor alanına bağlanamaz.

### 3.3 Candidate C — Displayed-rank resolution (OBSERVATIONAL / PROVENANCE-DEPENDENT)

Resolution, kullanıcıya gösterilen nihai sıranın (1..N) ayırt ediciliği olarak
tanımlanır. Birim: tarih başına distinct final-rank sayısı.

- **Ölçer:** kullanıcının gördüğü gerçek sıralamayı.
- **Ölçemez / engel:** H4B'nin tespit ettiği gibi explicit final tie-breaker
  ve historical input-order provenance olmadan bu, historical export'tan
  **reconstruct edilemez**. Candidate C ancak yeni canlı ölçümle tanımlanabilir;
  bu da H4D-measure'ın konusu olur, H4D-definition'ın değil.

- **Ölçemez / engel:** H4B'nin tespit ettiği gibi explicit final tie-breaker
  ve historical input-order provenance olmadan bu, historical export'tan
  **reconstruct edilemez**. Candidate C ancak yeni canlı ölçümle tanımlanabilir;
  bu da H4D-measure'ın konusu olur, H4D-definition'ın değil.
- **Rol (LOCKED):** Observational endpoint / future validation.
  `STATUS = provenance-dependent`. Primary metric değildir; canlı ölçüm
  gerekiyorsa ayrı H4D-measure/Level B kapsamında ele alınır.

## 4. Kilitlenen tanım (DEFINITION LOCK)

Official production ranking resolution şu hiyerarşiyle tanımlanır:

```
PRIMARY UNIT
= production sort-tuple resolution
    (Candidate B: full production sort tuple)

SECONDARY UNIT
= score-space resolution of the declared ranking-score field
    (Candidate A; diagnostic)

OBSERVATIONAL ENDPOINT
= displayed-rank resolution
    (Candidate C; provenance-dependent)
```

**Score-field hiyerarşisi (LOCKED):**

```
Official ranking resolution
        |
        +-- PRIMARY: full production sort tuple
        |              +-- score fields
        |              +-- categorical/tier fields
        |              +-- confidence/probability fields
        |
legacy_quality_score
        |
        +-- named score-field candidate / diagnostic
```

`legacy_quality_score` "official ranking score budur" olarak kesinleştirilmez;
H4B'nin bulgusu (persisted `ranking_score` yok, production multi-key tuple,
legacy ilgili alan) nedeniyle o, tuple içindeki **named score-field candidate /
diagnostic** olarak konumlanır. Böylece `legacy_quality_score` ile production
ordering arasında kavramsal eşdeğerlik varsayılmaz.

**FINAL-TIE STATUS (LOCKED):**

```
RESOLUTION_UNDERSPECIFIED_AT_FINAL_TIE
```

şu durumda geçerlidir: full production sort tuple'ı aynı olan birden fazla
observation bulunduğunda, tuple bunların kendi aralarındaki nihai sırasını
belirlemiyorsa (explicit final tie-breaker yoksa), resolution o son düzeyde
fully determined değildir.

**Tie ≠ failure (LOCKED ayrım):** Bir tuple'ı paylaşan birden fazla observation
olması tek başına production sorting'in "bozuk", "yetersiz" veya defect
olduğunu göstermez. Yalnızca o group'un internal ordering'inin declared sort
keys tarafından belirlenmediğini gösterir. Resolution tanımı determinism ile
capacity'i birbirine karıştırmaz.

**HISTORICAL LIMITATION (LOCKED):** Gerekli production ordering/provenance
reconstruct edilemiyorsa, resolution'ın **değeri** ölçülmemiş/bilinmeyen kalır.
Bu bir tanım eksikliği değil, ölçüm sınırlamasıdır.

**MEASUREMENT (LOCKED):** H4D-definition'da ölçüm yasaktır; resolution değeri
ancak ayrı bir H4D-measure preregistration ve ayrı onayla ölçülür.

Bu kararlar bu belgede kilitli tanım olarak durur; hiçbiri kod veya davranış
değişikliği üretmez.

## 5. Tanımın kullanım sözleşmesi

Tanım kilitlendikten sonra:

- "Production ranking resolution" ifadesi yalnızca bu belgede tanımlanan
  birim/metrikle kullanılır.
- H4A/H4B/H4C sonuçları bu tanıma göre **yeniden etiketlenmez**; onlar kendi
  birimlerinde geçerli kalır.
- Resolution'ın bir **değeri** ancak H4D-measure (ayrı preregistration + ayrı
  onay) ile ölçülür.
- Candidate C (displayed-rank) ölçümü, gerektiğinde canlı scan'e read-only
  provenance/persist eklemeyi gerektirebilir; bu **Level B** olur, bu dosya
  ona yetki vermez.

## 6. Negative / sınırlama politikası

- Eğer üç candidate da historical export'tan ölçülemez bulunursa, bu geçerli
  bir sonuçtur: "official resolution yalnızca canlı provenance ile
  tanımlanabilir" olarak raporlanır ve Candidate C için ayrı Level B önerilir.
- Hiçbir tanım, resolution'ın "yetersiz" veya "production'ı bozduğu" iddiasını
  içermez.
- Bu dosya production değişikliğine yetki vermez.

## 7. Artifact durumu

- Bu tanım belgesi (bu dosya) — **APPROVED / LOCKED** (2026-09-22).
- H4D-definition karar özeti bu dosyanın §4'ünde kilitlidir (candidate
  hiyerarşisi + score-field hiyerarşisi + tie-breaker hükmü).
- H4D-measure preregistration: **ayrı dosya**, ancak bu H4D-definition
  onaylandıktan sonra; henüz yazılmadı ve onaylanmadı.

## Governance

- Research / Level A / read-only / definition-only. Ölçüm ve kod yok.
- `scanner/`, `distribution/`, `api/`, web, score formülleri, flag'ler,
  scheduler, DB ve user-facing surface değiştirilmez.
- H2/H4A/H4B/H4C verdict'leri olduğu gibi kalır; H4D bunları yeniden açmaz veya
  aşındırmaz.
- Karar `docs/governance/decision-log.md`'ye Level A definition-lock kaydı
  olarak yazılır (disk, salt-eklemeli).
