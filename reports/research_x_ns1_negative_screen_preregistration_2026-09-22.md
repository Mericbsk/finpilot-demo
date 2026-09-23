# RESEARCH-X/NS-1 — Negative-Screen Battery (Pre-Registration)

**Tarih:** 2026-09-22
**Layer:** Research
**Level:** A (read-only; measurement protocol only)
**Status:** **APPROVED / LOCKED — Meriç onayı: 2026-09-22.** Bu dosya
kilitlidir; kural, eşik, kontrol, temporal sözleşme ve verdict seti bu
noktadan sonra değiştirilemez.
**Phase:** Faz 1 — negatif eleme hattı (master scientific state audit sonrası
ilk araştırma adımı)
**Öncüller (değiştirilmez, açılmaz):**
- ANS-1 `SUPPORTED` ([reports/ans1_attention_negative_screen_2026-09-18.md](ans1_attention_negative_screen_2026-09-18.md))
- ANS-2 fırsat maliyeti ([reports/ans2_opportunity_cost_2026-09-18.md](ans2_opportunity_cost_2026-09-18.md))
- ANS-3 temporal `PARTIAL` ([reports/ans3_temporal_replication_2026_09_21.md](ans3_temporal_replication_2026_09_21.md))
- Failure phenotype descriptive ([reports/research_x_failure_phenotype_2026-09-21.md](research_x_failure_phenotype_2026-09-21.md)) — RX-H1 burada **HYPOTHESIS** olarak listelendi; bu pre-reg onu ilk kez formalleştirir.

**Bu dosya "negatif eleme kuralları kalan evreni iyileştiriyor mu?" sorusunu
kilitler. "Bu kurallar üretime girsin mi?" sorusunu cevaplamaz** — ikincisi
sonuç sonrası ayrı bir Level B kararıdır.

**NO:** production code, scanner, score, ranking, flag, scheduler, DB veya
user-facing değişiklik. `production_impact = NONE`. H4 hattı FROZEN kalır;
bu çalışma H4'ün devamı veya yeniden açılması değildir.

## 0. İsimlendirme notu (Ç6 dersi)

Bu hat **NS** (Negative Screen) öneki kullanır. `H1`/`H2`/`H3` önekleri bu
repoda iki farklı hipotez ailesinde kullanılmıştır (Research-X H2 vs 2026-08-10
pre-reg H2); isim çakışmasını önlemek için bu aile `NS-1` olarak adlandırılır.

## 1. Araştırma sorusu

> Önceden kilitlenmiş, scan_date-içi göreli eleme kurallarıyla belirli
> adayların çıkarılması, kalan evrenin `c2c_5d` dağılımını (medyan ve
> big-loser kuyruğu) matched-random ve null-shuffle kontrollerini geçecek
> şekilde iyileştiriyor mu — ve bu iyileşme temporal olarak tekrarlanıyor mu?

**Eleme kanıtı ≠ al sinyali ≠ short sinyali.** Elelenen hisselerin düşeceği
iddia edilmez; yalnızca kalan evrenin istatistikleri ölçülür.

## 2. Hipotezler (formal)

- **NS-H1 (birincil):** En az bir eleme kuralı, kalan evrenin medyan
  `c2c_5d`'sini block-bootstrap adjusted CI sıfırı dışarıda bırakacak şekilde
  iyileştirir ve matched-random + null-shuffle kontrollerini geçer —
  **ve** aynı anda big-loser (≤−10%) oranını artırmaz (bozulmasına izin
  verilmez; §6'daki verdict tanımına zorunlu kapı olarak girer).
- **NS-H2 (birincil, temporal):** NS-H1'i geçen kural erken ve geç
  yarılarda aynı işaretli iyileşme gösterir (ANS-3'teki temporal kırılganlık
  dersi nedeniyle ayrı hipotez).
- **NS-H3 (ikincil, deskriptif):** İyileşme, big-loser (≤−10%) oranını
  düşürürken top-%5 kuyruk fırsat maliyeti sınırlı kalır. Bu her zaman
  birlikte raporlanır (ANS-2 disiplini); "kabul edilebilir fırsat maliyeti"
  bu dosyada tanımlanmaz — o bir ürün kararıdır (Level B).

## 3. Eleme kuralları (kilitli; eşikler değiştirilemez)

Tüm percentile eşikleri **scan_date içi** hesaplanır (point-in-time safe;
mutlak eşik ayarlaması yoktur). `p80(x)` = o scan_date'teki 80. percentile.

| Kural | Tanım | Dayanak |
|---|---|---|
| **NS-A** (replikasyon) | `\|gap_pct\| >= 3` VEYA `atr_pct_real >= 6` | ANS-1'in kilitli tanımı, birebir |
| **NS-B3** (birincil yeni) | 4 koşuldan **≥3'ü** sağlanıyor: `atr_pct_real >= p80`, `lottery_factor >= p80`, `price <= p20`, `dist_52w_high <= p20` | Failure phenotype'teki dört yönün **önceden tanımlı çoğunluk kuralı** (RX-H1'in formalleşmesi) |
| **NS-C** | `lottery_factor >= p80` | Lottery bucket negatif-seçim bulgusu |
| **NS-UNION** | NS-A VEYA NS-B3 | Kombinasyon etkisi |

NS-B3'ün ≥3/4 formu, failure phenotype'in dört yönünü tek kuralda birleştiren
önceden seçilmiş bir çoğunluk kuralıdır; NS-B4 tam kesişim olarak
ikincil/deskriptif tutulur. NS-B4'ün düşük örneklemde `INSUFFICIENT_DATA`
üretmesi beklenebilir; ancak bu beklenti **NS-B3'ün seçilme gerekçesi değildir**
ve sonuç sonrası kural değişikliğine gerekçe oluşturmaz.

İkincil/deskriptif kollar (karar verdirmez, Bonferroni dışı, yalnız rapor):
- **NS-B4** — 4 koşulun tamamı (strict intersection; küçük n beklenir).
- NS-B3'ün 4 tek-koşul kolu (hangi koşulun taşıdığını görmek için).
- `price >= 5 USD` robustness kolu (penny-outlier duyarlılığı).

**Birincil test ailesi = {NS-A, NS-B3, NS-C, NS-UNION}** → aile-içi Bonferroni:
kural başına adjusted CI seviyesi %98.75 (=%100 − 5/4). %95 CI da raporlanır;
SUPPORT kararı yalnız adjusted CI ile verilir. Bu düzeltme yalnız bu aileye
uygulanır; geçmiş verdict'leri yeniden kalibre etmez (global FDR borcu ayrı
bir araştırma borcu olarak kayıtlıdır).

## 4. Veri ve input sözleşmesi

- **Input:** `data/backtest_out/full_universe_enriched_eod_only.csv`,
  SHA-256 `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`
  (runner başlangıcında yeniden doğrulanır).
- **Dedup:** kanonik sözleşme — `(symbol, scan_date)` başına tek satır, en
  erken lexical `scan_ts` (H4A/H4B/H4C/H4D ile aynı).
- **Filtre:** `composite_score` non-null VE `c2c_5d` non-null. Beklenen
  n ≈ 34.762 (ANS-1/failure-phenotype ile aynı popülasyon); |Δn| > %1 ise
  `INPUT_MISMATCH`.
- **Outcome (birincil):** `c2c_5d`. İkincil deskriptif: `c2c_1d`.
- **Missing politikası:** bir kuralın gerektirdiği alan eksikse o satır o
  kural tarafından **elenemez** (konservatif: evrende kalır) ve
  `excluded_from_rule_missing_field` olarak sayılır. İmpute yok.

## 5. Metodoloji (kilitli)

ANS-1 protokolüyle birebir aynı kontroller:

1. **Birincil metrik:** kalan evrenin medyan `c2c_5d` iyileşmesi (pp),
   eleme sonrası vs tam evren.
2. **Kontroller (her kural için):**
   - (a) **matched-random:** her scan_date'ten aynı sayıda rastgele satır
     çıkar; R=300, seed=20260922. Gerçek eleme, matched dağılımın 50.
     percentilinden iyi olmalı.
   - (b) **null-shuffle:** eleme bayrağı scan_date içinde karıştırılır;
     R=300, seed=20260922.
   - (c) **date-block bootstrap:** gün bloklu, B=2000; adjusted CI
     (%98.75, aile Bonferroni) sıfırı dışarıda bırakmalı.
3. **İkincil metrikler (her zaman birlikte raporlanır):** big-loser oranı
   (≤−10%) değişimi, hit-rate değişimi, mean değişimi, **top-%5 kuyruk
   fırsat maliyeti** (ANS-2 metodolojisi), |ret|>10 tail-EV değişimi.
4. **Loser recall (secondary descriptive; verdict kriterine GİRMEZ):**
   `loser_recall = (kural tarafından elenen gerçek big-loser satır sayısı) /
   (evrendeki tüm gerçek big-loser satır sayısı)`; gerçek big-loser tanımı
   kesinlikle `c2c_5d <= -10%`. Bu metrik "kalan evren iyileşti mi?"
   sorusundan farklı olarak "gerçek kaybedenlerin yüzde kaçı yakalandı?"
   sorusunu ölçer; her kural için raporlanır ancak hiçbir verdict'i
   etkilemez.
5. **Temporal replikasyon (ANS-3 sözleşmesi):** kronolojik unique
   scan_date'ler → erken %50 / orta %20 (buffer; yalnız deskriptif,
   SUPPORT kararına girmez) / geç %30. Destek kararı erken ve geç
   yarıların **aynı işaretli** olmasını gerektirir. Aynı işaret, aynı
   büyüklük demek değildir: raporda her kural için zorunlu olarak
   `early_effect_pp`, `late_effect_pp` ve `early/late effect ratio`
   ayrı ayrı raporlanır; verdict'e post-hoc büyüklük eşiği eklenmez.

## 6. Verdict seti (kural başına; önceden kilitli)

- `SCREEN_SUPPORTED` — adjusted CI sıfır dışında + matched-random ve
  null-shuffle geçildi + erken/geç aynı işaret + **big-loser (≤−10%) oranı
  artmadı** (medyan iyileşirken kuyruk riskini artıran bir kural destek
  kazanamaz).
- `SCREEN_PARTIAL` — havuzlanmış adjusted CI sıfır dışında ama yalnızca bir
  yarıda belirgin (ANS-3 deseni).
- `SCREEN_UNSTABLE` — erken/geç işaretleri zıt.
- `SCREEN_NOT_SUPPORTED` — adjusted CI sıfırı içeriyor veya kontroller
  geçilemedi.
- `INSUFFICIENT_DATA` — elenen n < 500 veya elenen gün sayısı < 20
  (önceden kilitli eşikler; NS-B4 için muhtemel sonuç).
- `INPUT_MISMATCH` — SHA veya popülasyon sözleşmesi uyuşmazlığı.

**Hiçbir verdict üretim filtresi önerisi içermez.** `SCREEN_SUPPORTED` dahi
yalnızca "bu eleme kuralı tarihsel örneklemde kalan evreni iyileştirdi" der;
üretim elemesi ayrı Level B kararıdır.

## 7. Belirsizlik, randomization, determinism

- Randomness yalnız matched-random ve null-shuffle'da; seed=20260922 sabit.
- Runner iki kez çalışır; JSON ve rapor SHA-256 birebir aynı olmalı.
  Fark = fail, sonuç raporlanmaz.
- Negatif/karışık sonuçlar geçerli çıktılardır; eşik, kural veya popülasyon
  sonuç gördükten sonra değiştirilmez (post-hoc ayar yasağı).

## 8. Bu çalışmanın cevaplamadığı sorular

- Eleme kurallarının üretime alınıp alınmaması (Level B).
- Kalan evren içinde sıralama/alım kuralı (bu hat seçim motoru değildir).
- Çıkış/yakalama problemi (Faz 2 — ayrı hat, ayrı pre-reg).
- Üretim ranking resolution'ı (H4 FROZEN; burada açılmaz).
- Fundamental/catalyst/liquidity feature'ları (tarihsel veride yok;
  Faz 4 instrumentation kapsamı).

## 9. Beklenen artifact'ler (onaydan önce üretilmez)

- Runner: `research/research_x_ns1_negative_screen_2026_09_22.py`
- JSON: `data/backtest_out/research_x_ns1_negative_screen_2026-09-22.json`
- Rapor: `reports/research_x_ns1_negative_screen_2026-09-22.md`

Runner bu dosyadaki kural tanımlarını, eşikleri, kontrolleri, temporal
sözleşmeyi, verdict setini ve determinism kurallarını değiştiremez.

## Governance

- Research / Level A / read-only / measurement protocol. Bu dosya
  **DRAFT**'tır; runner yazımı Meriç onayı ve bu dosyanın
  `APPROVED / LOCKED` yapılmasından sonradır.
- `scanner/`, `distribution/`, `api/`, web, score formülleri, flag'ler,
  scheduler, DB ve user-facing surface değiştirilmez.
- H2/H4A/H4B/H4C/H4D olduğu gibi kalır; ANS-1/2/3 sonuçları yeniden
  açılmaz (NS-A yalnızca replikasyon koludur).
- Karar, onaylandığında `docs/governance/decision-log.md`'ye Level A
  preregistration-lock kaydı olarak yazılır (disk, salt-eklemeli) —
  H4C/H4D emsalinde olduğu gibi kayıt **lock anında** atılır; bu DRAFT
  aşamasında decision-log'a yazılmaz.
