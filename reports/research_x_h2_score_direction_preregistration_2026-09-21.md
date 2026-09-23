# RESEARCH-X/H2 — Score-Direction Pre-Registration (H2a/H2b/H2c)

**Tarih:** 2026-09-21
**Layer:** Research
**Level:** A (read-only research; production davranışı değişmez)
**Status:** **LOCKED BEFORE EXECUTION**
**Phase:** 2 — score/outcome direction measurement
**Predecessor:** `reports/research_x_failure_phenotype_2026-09-21.md`

Bu belge sonuç görülmeden önce H2'yi üç ölçülebilir alt soruya ayırır. Amaç,
median high/low split'teki descriptive farkı daha ayrıntılı score quantile'ları,
kronolojik fold'lar ve scan-date eşleştirmeli random control ile ölçmektir.
Bu belge production score'u değiştirmez ve ters score üretmez.

## 1. İddia sınırı

Bu preregistration şu üç soruyu test eder:

- **RX-H2a (primary):** Daha yüksek score quantile'ı, daha düşük `c2c_5d`
  median ile monoton biçimde ilişkili mi?
- **RX-H2b (secondary):** Daha yüksek score quantile'ı,
  `c2c_5d >= +10%` big-winner oranını düşürüyor mu?
- **RX-H2c (secondary, yönsüz):** Score quantile seviyesi,
  `c2c_5d <= -10%` big-loser oranı ve negatif-getiri oranıyla nasıl
  ilişkilidir?

**RX-H2d bu koşunun konusu değildir.** H2a/H2b/H2c sonuçları, tie-resolution
ve canlı `ranking_score` ile `composite_score` eşlemesi çözülmeden
"production ranking inverted" sonucuna dönüştürülmeyecek.

Bu testin geçmesi veya kalması aşağıdakilerin hiçbirini ifade etmez:

- `new_score = -composite_score`
- düşük score'u olumlu işlem sinyali olarak kullanmak
- yüksek score'u negatif/short sinyali olarak kullanmak
- production ranking, scanner, flag, entry/exit veya kullanıcı yüzeyi değişikliği

## 2. Veri ve freeze sözleşmesi

### 2.1 Girdi

- **Canonical input:** `data/backtest_out/full_universe_enriched_eod_only.csv`
- **Score exposure:** `composite_score` — `score` veya `ranking_score` yerine
  bu alan test edilir.
- **Primary outcome:** `c2c_5d`.
- **Required provenance:** `label_entry_basis == "eod_close"`.
- **Expected historical window:** 2026-05 through 2026-07-31. Runner gerçek
  min/max tarihleri ayrıca kaydeder; tarihler yoksa fold kaydırılmaz.

Satırlar `scan_date` ve `symbol` ile sıralanır; aynı `(symbol, scan_date)`
çiftlerinden ilk satır tutulur. `composite_score`, `c2c_5d`, `scan_date` veya
`symbol` eksik satırlar; `label_entry_basis` EOD olmayan satırlar; sentetik,
impute edilmiş, winsorize edilmiş veya sonradan düzeltilmiş satırlar analize
alınmaz. Eksikliği gidermek için yeni veri üretilmez.

Bu dosya EOD-only etiket bütünlüğü için seçilmiştir. Etiket hedefi hâlâ
historical split-sample araştırma hedefidir; bu çalışma gerçek future-OOS
validation olarak adlandırılmayacaktır.

### 2.2 Score freeze

- Production composite formülü ve o tarihteki score alanı yeniden fit edilmez.
- Feature ağırlığı, flag, threshold, tie-break veya score dönüşümü eklenmez.
- `composite_score` float değerleri yeniden hesaplanmaz ve yuvarlanmaz.
- `ranking_score` ile `composite_score` eşit varsayılmaz; bu ayrım H2d kapısıdır.

## 3. Önceden kilitlenen quantile yöntemi

Her chronological fold için score quantile sınırları yalnızca **train
window'ındaki `composite_score` değerlerinden** hesaplanır:

- empirical `q20`, `q40`, `q60`, `q80`
- Q1: `score <= q20`
- Q2: `q20 < score <= q40`
- Q3: `q40 < score <= q60`
- Q4: `q60 < score <= q80`
- Q5: `score > q80`

Bunlar **beş hedef-eş-frekanslı score quantile bandıdır**. Test window'ında
quantile sınırları yeniden hesaplanmaz; bu nedenle test outcome'ları sınırları
etkilemez. Testteki gerçek bin sayıları ayrıca raporlanır.

Ties için önceden kilitli kural:

- Aynı score değerleri quantile sınırında bölünmez.
- Duplicate boundary, empty bin veya dengesiz test bin'i düzeltilmez.
- Symbol alfabetik sırası, hash, random jitter veya outcome tabanlı tie-break
  kullanılmaz.
- Her fold'da train unique-score sayısı, boundary duplicate durumu, test bin
  sayıları ve boundary score'larına denk gelen test satır oranı raporlanır.
- Beş binin tamamı dolu değilse fold sonuçları yine tablo olarak raporlanır,
  fakat fold **primary monotonicity verdict** için `INSUFFICIENT_TIE_RESOLUTION`
  olarak işaretlenir; başka quantile/threshold seçilmez.

Önceki baseline audit'inde raporlanan yüksek tie oranı bu tasarımın bilinen
sınırlamasıdır: score-bucket sonucu otomatik olarak ranking-resolution veya
production ranking kanıtı değildir.

## 4. Chronological walk-forward tasarımı

Score yeniden fit edilmez; "train" yalnızca score dağılımından önceden
belirlenmiş quantile sınırlarını üretmek ve tarih sırasını korumak içindir.
Outcome testte ölçülür.

| Fold | Train window | Test window | Kullanım |
|---|---|---|---|
| F1 | 2026-05-01–2026-05-31 | 2026-06-01–2026-06-30 | erken train / geç test |
| F2 | 2026-05-01–2026-06-30 | 2026-07-01–2026-07-31 | genişleyen train / geç test |

Takvim aralığında satır bulunmayan günler sessizce eklenmez. Her fold için
minimum koşul: en az 5 distinct test `scan_date` ve beş quantile bandının
tamamında en az bir test satırı. Bu koşul sağlanmazsa fold `INSUFFICIENT_DATA`
olarak raporlanır ve fold seçilerek genel sonuç üretilmez.

Bu iki fold aynı historical artifact'in split-sample kontrolüdür. **True
future-OOS değildir**; yeni veri ancak 2026-07-31 sonrasından geldiğinde ayrı
bir future-OOS replikasyonu olarak kaydedilebilir.

## 5. Endpoint'ler

### 5.1 Primary endpoint — RX-H2a

Her test fold'unda Q1, Q2, Q3, Q4 ve Q5 için:

- `n`
- median `c2c_5d`
- Q1 minus Q5 median contrast
- dört adjacent median comparison'ın kaçında beklenen inverse yön
  (`Q1 >= Q2 >= Q3 >= Q4 >= Q5`) gözlendiği
- beş bin median'ı ile quantile ordinal'i arasındaki Spearman rho

Beklenen yön Q1'den Q5'e doğru median'ın düşmesidir. Monotonicity yalnızca
tek bir bin veya yalnızca Q1/Q5 farkıyla değil, beş bin tablosunun tamamıyla
raporlanır.

### 5.2 Secondary endpoints — RX-H2b / RX-H2c

Her quantile ve fold için:

- `P(c2c_5d < 0)`
- `P(c2c_5d <= -10)` — big-loser oranı
- `P(c2c_5d >= +10)` — big-winner oranı
- mean `c2c_5d`
- median `c2c_5d` (primary tabloyla birlikte)

`c2c_5d` değerleri dataset'te yüzde puan olarak tutuluyorsa eşikler `-10` ve
`+10` olarak uygulanır; oranlar ve dönüşümler sessizce yeniden ölçeklenmez.

H2b için beklenen yön Q1 big-winner oranının Q5'ten yüksek olmasıdır. H2c
önceden yön varsaymaz; big-loser ve negatif-getiri gradyanları raporlanır,
ancak sonuç görüldükten sonra yönlü hipotez yazılmaz.

## 6. Belirsizlik ve matched-control

### 6.1 Date-block bootstrap

- Her fold'da distinct `scan_date` blok olarak kullanılır.
- `B = 2,000`, fixed seed; fold seed'leri script içinde sabittir.
- Tarihler replacement ile örneklenir, tarihin tüm satırları birlikte taşınır.
- Quantile labels ve train-derived boundaries bootstrap içinde yeniden
  hesaplanmaz.
- Primary Q1-minus-Q5 median contrast için percentile %95 CI raporlanır.
- Mean, big-winner, big-loser ve negative-rate contrast'ları için aynı
  date-block CI yöntemi kullanılır.

Beş günlük etiketlerin yakın tarihler arasında overlap edebileceği açıkça
raporlanır; date-block bootstrap bu bağımlılığı azaltır, ortadan kaldırmaz.

### 6.2 Scan-date matched randomized score ordering

Her test fold'unda her `scan_date` içinde:

1. Gerçek quantile label sayıları Q1–Q5 için sabitlenir.
2. Aynı satırlar üzerinde quantile label'ları outcome'a bakmadan random
   permute edilir.
3. Gerçek score-ordering ile aynı tarih kompozisyonu ve aynı bin büyüklükleri
   korunur.
4. `R = 1,000` fixed-seed tekrar ile Q1-minus-Q5 median ve big-winner
   contrast null dağılımları üretilir.

Primary one-sided random-control p-value, observed inverse contrast kadar veya
ondan daha uç null contrast'ların `(1 + count) / (R + 1)` oranıdır. H2c yönsüz
olduğu için yalnızca iki taraflı CI ve dağılım raporlanır. Random control
gerçek score bilgisini yok ederek cross-sectional market composition'ın tek
başına sonucu üretip üretemeyeceğini ölçer; production score'u yeniden
sıralamaz.

### 6.3 Multiple-testing ve yorum

- H2a tek primary claim'dir; primary contrast, iki fold tutarlılığı, CI ve
  matched-control birlikte raporlanır.
- H2b ve H2c secondary'dir; her ikisi için ham effect, CI ve random-control
  sonucu verilir. Secondary p-value kullanılırsa iki secondary claim arasında
  Holm düzeltmesi uygulanır.
- Tek bir olumlu quantile veya tek bir fold, H2a-c için genel destek sayılmaz.
- Effect size, CI, bin counts, unique-score ve tie-resolution olmadan
  significance iddiası yazılmaz.

## 7. Önceden kilitlenen verdict mantığı

### RX-H2a

**SUPPORTED** yalnızca şu koşulların tamamı sağlanırsa verilebilir:

- F1 ve F2 `OK` ve tie-resolution koşulu geçerli,
- her iki fold'da Q1-minus-Q5 median contrast beklenen yönde,
- her iki fold'da date-block %95 CI sıfırı dışarıda,
- her iki fold'da matched randomized ordering için primary p-value `< 0.05`,
- adjacent median comparisons ve pooled tablo inverse yönün tek bir uç bin
  etkisi olmadığını gösteriyor.

Bu koşullardan biri eksikse sonuç `PARTIAL`, `NOT_SUPPORTED` veya
`INSUFFICIENT_DATA` olarak ayrıştırılır; hangi koşulun eksik olduğu yazılır.
`PARTIAL`, production veya H2d desteği değildir.

### RX-H2b

Big-winner oranı için iki fold'da beklenen inverse yön, effect size, CI ve
matched-control birlikte raporlanır. H2b, H2a geçse bile ayrı secondary
sonuçtur; H2a'nın yerine geçmez.

### RX-H2c

Big-loser ve negative-rate gradyanları yönsüz secondary sonuçtur. Sonuç
`high-score failure` veya `low-score blind spot` anlatısını destekleyebilir,
ama tek başına failure predictor, short signal veya production veto değildir.

## 8. Negative-result policy ve sonraki kapı

- H2a başarısız olursa: **score-direction signal not established**; score ters
  çevrilmez.
- H2b başarısız, H2a başarılı olursa: median ilişki ile big-winner olasılığı
  ayrıştırılır; geniş "inverted ranking" iddiası yapılmaz.
- H2c karışık olursa: big-loser oranı için yönlü sonuç icat edilmez.
- H2a-c sonucu ne olursa olsun `ranking_score` ile `composite_score` eşitliği
  çözülmeden H2d açılmaz.
- H2d için ayrı bir preregistration ve gerekirse ayrı Level B kararı gerekir;
  bu dosya production değişikliği yetkisi vermez.

## 9. Beklenen artifact'ler

Bu preregistration sonradan değiştirilmeden aşağıdaki runner ile uygulanır:

- Runner: `research/research_x_h2_score_direction_2026_09_21.py`
- JSON: `data/backtest_out/research_x_h2_score_direction_2026-09-21.json`
- Sonuç raporu: `reports/research_x_h2_score_direction_2026-09-21.md`

Runner preregistration metnindeki fold, quantile, control, seed, bootstrap ve
verdict kurallarını değiştiremez. Sonuç raporu bu belgeye göre yazılır;
veri yetersizliği veya negatif sonuç geçerli sonuçlardır.

## Governance

- Research / Level A / read-only.
- `scanner/`, `distribution/`, `api/`, web, score formülü, flag, scheduler,
  DB ve user-facing surface değiştirilmez.
- Yeni score, reverse score, threshold optimization, post-hoc subgroup veya
  production recommendation üretilmez.
- Bu test historical split-sample'dır; true future-OOS olarak sunulmaz.
- H2d ve herhangi bir production/publish kararı bu kaydın kapsamı dışındadır.
