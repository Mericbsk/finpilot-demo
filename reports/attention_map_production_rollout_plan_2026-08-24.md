# FinPilot Dikkat Haritası — Üretim Göçü: Aşamalı Uygulama Planı

Date: 2026-08-24
Level: B (ürün değişikliği; Meriç onayı olmadan hiçbir faz başlamaz)
Status: DRAFT — onay bekliyor
Authority: `docs/2026-08-15-master-prompt-finpilot-attention-map.md` (görev tanımı),
`reports/attention_map_migration_plan_v3_2026-08-14.md` (ürün planı ve formüller — tek otorite,
bu belge formülü KOPYALAMAZ, oraya atıf yapar), `docs/governance/decision-log.md`,
`_instructions/00-core.md`, `_instructions/05-escalation.md`, `YONERGE.md` §12.

Bu belge bir **uygulama/rollout planıdır**; ürün formülü ve tier tanımları v3 planında yaşar.
Çelişki durumunda v3 + decision-log kazanır (CORE-003, CORE-005).

---

## 0. Adım 0 Doğrulama Özeti (2026-08-24 — kod ve veri gerçeği)

Her satır bu turda grep/dosya okumasıyla doğrulandı; plan varsayımına güvenilmedi.

| # | İddia / Beklenti | Doğrulanan gerçek | Durum |
|---|---|---|---|
| 1 | §2.1 scanner helper'ları var | `scanner/features.py:266` `compute_dist_52w_high`, `:285` `compute_gap_pct`, `:304` `compute_rvol_daily` mevcut | EVIDENCE — uygulanmış (Level B onay hâlâ pending) |
| 2 | §2.1 export alanları evaluate.py'de | `scanner/evaluate.py:823-826` return dict'ine `dist_52w_high`, `gap_pct`, `rvol_daily`, `squeeze_factor` ekli | EVIDENCE — kodda var |
| 3 | Yeni alanlar canlı export'a ulaştı | `data/shortlists/shortlist_20260824_1536.csv` başlığında 4 alan da **YOK** (squeeze_factor yalnızca `score_input` JSON blobu içinde). Yazar `scanner/data_fetcher.py:1430` `save_scan_results` → `df.to_csv` projeksiyonsuz; demek ki yukarı akış DataFrame'i bu kolonları taşımıyor (veya CSV, §2.1 öncesi kodla üretildi — satır timestamp'leri 2026-08-21). Kök neden henüz bilinmiyor | **GAP — Faz A'nın konusu** |
| 4 | Faz 1c (formül eşdeğerliği) ölçüldü | `data/backtest_out/attention_score_formula_overlap_2026-08-14.json`: `comparable_rows=0`, `missing_live_columns=["squeeze_factor"]`, korelasyon=null. Validator `LIVE_SHORTLIST`'i 08-14 CSV'sine sabitlemiş | **KANITLANMADI — Faz C'nin konusu** |
| 5 | Price cache shortlist kapsamı | `refresh_price_cache.py --shortlist` bayrağı mevcut ve decision-log'a göre Meriç onaylı (Level B, applied). Ama canlı fetch hiç koşulmamış: 12 validator sembolünden 11'i hâlâ `2026-07-29`'da (`LX` 2026-08-14 — 08-15 izole tanı testinden) | **AÇIK İŞ — Faz B'nin konusu** |
| 6 | Faz 2+ (snapshot/schema/web/Telegram) | `distribution/` ve `web/src/` altında `attention` referansı yok | EVIDENCE — hiç başlanmadı, doğru durum |
| 7 | Üretim ranking davranışı | Değişmedi; `ranking_score = legacy_quality_score` (2026-08-12/13 decision-log). Bu planın hiçbir fazı bayrak açılmadan buna dokunmaz | EVIDENCE |
| 8 | Bekleyen ikincil işler | `docs/2026-08-15-bekleyen-ikincil-isler-kapsamli-plan.md` (FinSense Deney 2/3, close5_real/c2c_5d) bu planın **kapsamı dışında** | Not |

Tespit edilen küçük governance tutarsızlığı (raporlanıyor, sessizce düzeltilmiyor — CORE-005):
`--shortlist` decision-log girdisinin tarihi `2026-08-14` ama içeriği 2026-08-15'teki cache
teşhis oturumuna atıf yapıyor. Tarih düzeltmesi ayrı bir Level A işidir; bu plana bağımlı değil.

---

## 1. Hedef ve Kesin Sınırlar (Adım 1)

**Hedef:** "Hangi hisse yükselecek?" tahmin çerçevesinden, kanıt tabanlı "hangi hisse
olağandışı davranıyor?" (dikkat/anomali) çerçevesine üretim geçişini tamamlamak.

**S1 — Tahmin dili yasağı:** Bu sistem yön/getiri tahmini DEĞİLDİR ve öyle sunulamaz.
Kullanıcıya-görünür hiçbir metinde (mock ve taslak dahil) "al", "sat", "hedef fiyat",
"yükselecek" ve türevleri geçemez (YONERGE §12 — kırmızı çizgi, veto yetkisi Layer 2).

**S2 — Kanıtsız rakam yasağı:** Hiçbir istatistiksel iddia (korelasyon, precision, lift,
p-değeri, coverage) üretim koduna veya kullanıcı metnine, kendi script'im + kayıtlı JSON/CSV
artifact'ı olmadan giremez. Offline/araştırma ölçümü ile üretim-verisi ölçümü her zaman ayrı
etiketlenir; export-formülü kanıtı (v3 §0) üretim formülüne (v3 §1.3) otomatik genellenemez.

**S3 — Onay kapıları:** Üretim davranışını (sıralama, seçim, kullanıcı deneyimi) değiştiren her
adım açık insan onayında durur. Kod yazmak/test etmek/bayrak TANIMLAMAK serbest; bayrağı AÇMAK,
şema/sözleşme değiştirmek, kullanıcı metnini yayınlamak her seferinde ayrı onaydır (05-escalation:
yayın kararı Level C).

**S4 — Geri alınabilirlik:** Yeni davranış tek bir feature flag ile açılıp kapanabilmeli
(`FINPILOT_ENABLE_ATTENTION_MAP`, varsayılan `0`). Eski davranışa dönüş veri kaybı olmadan
mümkün olmalı; şema göçü additive yürür, eski alanların kaldırılması ayrı ve sonraki bir karardır.

**S5 — Kanıt etiketi disiplini:** Bu plandan üretilen her belgede iddialar
`EVIDENCE` / `INFERENCE` / `HYPOTHESIS` / `DISCOVERY SIGNAL` olarak işaretlenir.
Kanıtlanmamış hiçbir şey kanıtlanmış gibi sunulmaz.

---

## 2. Aşamalı Plan (Adım 2)

### Faz A — Export yüzeyi boşluğunun kapatılması (§2.1'in gerçek tamamlanması)

- **Ne:** Bugünkü shortlist CSV'sinde 4 yeni kolonun neden görünmediğinin kök-neden analizi
  (adaylar: CSV'yi üreten yukarı-akış DataFrame projeksiyonu; taramanın §2.1 öncesi kod/süreçle
  koşulması; farklı export yolu). Kök neden bulunur, minimal düzeltme uygulanır.
  Ardından `distribution/scan_contract.py` ve `prepublish_gate`'in ek kolonlara toleransı
  doğrulanır (additive kolonlar sözleşmeyi bozmamalı — bozuyorsa BU DURUR ve raporlanır).
- **Değişecek dosyalar:** kök-nedene bağlı — aday `scanner/data_fetcher.py` veya export'u
  besleyen çağıran + `tests/` altında yeni export-kontrat testi.
- **KESİNLİKLE dokunulmayacak:** `distribution/*`, `web/*`, `api/*`, mevcut kolonların
  adı/anlamı/sırası, ranking/entry mantığı, `score_engine.py`.
- **Kanıt tanımı:** yeni koşulan bir taramanın CSV başlığında 4 kolonun görünmesi + doluluk
  oranı raporu + ilgili testlerin geçmesi + prepublish gate'in güncel export'ta PASS vermesi.
- **Bağımlılık:** yok (ilk faz). **Onay noktası:** bu planın onayı yeterlidir; alan eklemesi
  additivedir ve kullanıcı yüzeyini değiştirmez. Kök neden "sözleşme alanı silme/rename"
  gerektirirse iş DURUR ve Level C'ye yükselir.

### Faz B — Price cache'in shortlist kapsamıyla canlı yenilenmesi

- **Ne:** `python refresh_price_cache.py --shortlist` gerçek ağla koşulur (ağ bu ortamda
  2026-08-15'te kanıtlandı). 12 validator sembolünün tamamının güncellendiği dosya okunarak
  doğrulanır (tool "başarılı" demesine değil, `last_date` ve mtime'a bakılır).
- **Değişecek dosyalar:** yok (bayrak zaten onaylı ve applied). Yalnız `data/price_cache/*`
  (gitignored) güncellenir.
- **KESİNLİKLE dokunulmayacak:** script mantığı, varsayılan kapsam.
- **Kanıt tanımı:** 12/12 sembolde `last_date` >= son işlem günü; komut çıktısında
  `fetched>0` ve `added>0` (boş/no-op sayımı artık ayrışık); yeniden okuma ile teyit.
- **Bağımlılık:** yok. **Onay noktası:** yok (onaylı bayrağın ilk koşusu; EODHD kotası
  tüketimi not edilir).

### Faz C — Faz 1c: formül doğrulaması üretim verisiyle

- **Ne (C1 — eşdeğerlik):** overlap validator genelleştirilir (hardcoded 08-14 CSV'si yerine
  en-güncel/parametrik shortlist), Faz A+B çıktılarıyla yeniden koşulur. Artifact:
  `comparable_rows>0`, Spearman korelasyon, exact-score agreement.
- **Ne (C2 — üretim formülü sonuç doğrulaması):** v3 §1.3 üretim formülüyle skorlanan yeni
  taramalar biriktikçe ileri |5g| hareket karşısında precision/coverage/lift + aynı-gün
  matched-control ölçülür. **n yetersizse sonuç "bekliyor" olarak işaretlenir; kanıtlanmamış
  rakam üretilmez, tahmin doldurulmaz.** (Yeni alanlar en erken Faz A sonrası taramalarda
  var olacağından C2 için yeterli örneklem günler alabilir — bu açıkça raporlanır.)
- **Değişecek dosyalar:** `research/attention_score_formula_overlap_2026_08_14.py`
  (parametrik girdi; orijinal artifact korunur, yeni tarihli artifact yazılır) +
  yeni validator script'i (C2 için) + `data/backtest_out/` artifact'leri.
- **KESİNLİKLE dokunulmayacak:** üretim kodu (scanner/distribution/web/api), kilitli OOS.
- **Kanıt tanımı:** `data/backtest_out/attention_score_formula_overlap_<tarih>.json` içinde
  comparable_rows>0 ve raporlanmış metrikler; C2 için ayrı dated artifact veya "yetersiz-n"
  hüküm satırı.
- **Bağımlılık:** Faz A + Faz B. **Onay noktası:** C sonuçları Meriç'e sunulup onaylanmadan
  Faz D'ye geçilmez. Formüller örtüşmüyorsa DURULUR, çelişki raporlanır (CORE-005) — sessizce
  bir taraf seçilmez.

### Faz D — Dağıtım katmanı: bayrak arkasında snapshot/schema/gate

- **Ne:** `FINPILOT_ENABLE_ATTENTION_MAP` (default `0`) tanımlanır. Bayrak açıkken
  `snapshot_builder` attention alanlarını (v3 §1.4 tier + score + reasons) üretir; şema göçü
  **additive** yapılır (yeni alanlar eklenir; `grade`/`prob_band` kaldırılması bu fazda
  YAPILMAZ — ayrı karar); `prepublish_gate` her iki modu da doğrular.
- **Değişecek dosyalar:** `distribution/snapshot_builder.py`, `distribution/schema.py`,
  `distribution/prepublish_gate.py`, ilgili testler.
- **KESİNLİKLE dokunulmayacak:** `web/public/demo_snapshot.json` (canlı artifact), Telegram
  gönderim yolları, API canlı cevapları, `distribution/jobs.py` yayın akışı, bayrak kapalıyken
  hiçbir canlı çıktının baytı.
- **Kanıt tanımı:** her iki bayrak durumunda test paketi yeşil; flag=1 ile üretilen dry-run
  snapshot (yayınlanmaz) şemayı geçer; flag=0 ile mevcut canlı snapshot üzerinde gate PASS;
  iki modun snapshot diff'i artifact olarak kaydedilir.
- **Bağımlılık:** Faz C onayı. **Onay noktası:** D diff'i + kanıt paketi Meriç onayı olmadan
  Faz E başlamaz.

### Faz E — Kullanıcı yüzeyleri: çerçeve ve dil göçü (hazırlık bayrak kapalıyken; yayın ayrı onay)

- **Ne:** web (landing/demo/methodology/dashboard), Telegram şablonları, `distribution/glossary.py`
  (tek kaynak — türevler üretici script'le) ve API sözleşme dokümanı anomali çerçevesine göçer.
  Tahmin çağrıştıran terminoloji (grade/prob_band sunumu, "olasılık", "beklenen getiri" dili)
  envanteri çıkarılır ve kaldırılır; S1 yasaklı-dil denetimi tüm değişen yüzeylerde koşulur.
- **Değişecek dosyalar:** `web/src/**`, `distribution/templates.py`, `distribution/glossary.py`
  (+ `scripts/gen_terms_ts.py` türetimi), ilgili testler.
- **KESİNLİKLE dokunulmayacak:** canlı `web/public/demo_snapshot.json`, gönderilmiş Telegram
  kayıtları, locked OOS, `scanner/` skor mantığı.
- **Kanıt tanımı:** değişen dosyalarda yasaklı-terim grep raporu = sıfır isabet; web build/test
  yeşil; glossary türetme çıktısı diff'i; yayın öncesi önizleme (yerel render) kanıtı.
- **Bağımlılık:** Faz D. **Onay noktası:** canlı web push'u ve Telegram şablon aktivasyonu
  Level C'dir — ayrı Meriç onayı olmadan hiçbiri yayınlanmaz.

### Faz F — Gölge koşu ve rollback provası

- **Ne:** eski ve yeni boru hattı bayrakla paralel koşulur (öneri: 10 işlem günü — mevcut
  seri-sayacı pratiğiyle uyumlu); günlük karşılaştırma artifact'i birikir. Rollback provası:
  flag 1→0→1 geçişinde snapshot bütünlüğünün korunduğu test ortamında gösterilir.
- **Değişecek dosyalar:** gölge koşu script'i (yeni, `research/` veya izole job) +
  `data/backtest_out/attention_shadow_*.jsonl`.
- **KESİNLİKLE dokunulmayacak:** canlı yayın kararları, kanal gönderimleri.
- **Kanıt tanımı:** günlük JSONL satırları + özet rapor + rollback prova kaydı.
- **Bağımlılık:** Faz E onayı. **Onay noktası:** gölge raporu Meriç'e sunulur; Faz G ancak
  bunun üzerine açılır.

### Faz G — Canlıya geçiş (Level C)

- **Ne:** Açık insan onayı ile bayrak açılır; izleme ve ilk-gün doğrulaması yapılır;
  decision-log "applied" olarak güncellenir. Bu faza AI kendi kararıyla GEÇEMEZ.

---

## 3. Bağımlılık ve Onay Matrisi

| Faz | Bağımlı olduğu | Üretim davranışı değişir mi? | Onay noktası |
|---|---|---|---|
| A | — | Hayır (additive export kolonu) | Bu planın onayı |
| B | — | Hayır (gitignored cache) | Yok (onaylı bayrağın koşusu) |
| C | A + B | Hayır (research/) | **C sonucu onaylanmadan D yok** |
| D | C onayı | Hayır (bayrak kapalı) | **D diff'i onaylanmadan E yok** |
| E | D | Hazırlık hayır; yayın EVET | **Yayın Level C — ayrı onay** |
| F | E onayı | Hayır (gölge) | **Gölge raporu onayı** |
| G | F + tüm kanıtlar | EVET | **Level C — açık insan onayı** |

## 4. Rollback Planı

1. Tek anahtar: `FINPILOT_ENABLE_ATTENTION_MAP=0` → eski davranışa tam dönüş.
2. Şema additive kalır: rollback'te veri kaybı yok; eski alanlar göç boyunca üretilmeye devam eder.
3. Snapshot/shortlist artifact'leri tarihlidir; önceki günün artifact'ine dönmek dosya kopyasıdır.
4. Telegram/web eski şablonları git geçmişinde; dönüş `git revert` + bayrak kapatma.
5. Rollback provası Faz F'de test ortamında kanıtlanmadan Faz G açılmaz.

## 5. "Bitti" Tanımı (Adım 5'in beş koşulu — kanıt eşlemesi)

1. Üretim formülü gerçek üretim verisiyle bağımsız doğrulandı → Faz C1+C2 artifact'leri.
2. Tüm kullanıcı yüzeyleri yeni çerçeveyle tutarlı, eski tahmin dili yok → Faz E grep/build/önizleme kanıtı.
3. Rollback mekanizması test edildi ve çalıştığı gösterildi → Faz F prova kaydı.
4. Üretime geçiş için açık insan onayı alındı → Faz G decision-log "applied" girdisi.
5. Karar kaydı güncel ve tutarlı → her fazın sonunda formatına uygun girdi.

Bu beş koşuldan biri eksikse durum "devam ediyor" olarak raporlanır; "bitti" denmez.

## 6. Açık Engeller ve Riskler

- **E1:** Export boşluğunun kök nedeni bilinmiyor (Faz A). Kök neden sözleşme alanı
  silme/rename gerektirirse faz durur, Level C'ye yükselir.
- **E2:** C2 örneklem birikimi günler alır; hafta sonu/tatil taramaları uzatır. n yetersizliği
  "bekliyor" olarak raporlanır, doldurulmaz.
- **E3:** P1/P2 veri-kalite kapıları BLOCKED (2026-08-11/12 decision-log). Attention Map getiri
  iddiasi taşımadığından bu kapılar pivotu bloklamaz; ama hiçbir yüzeyde performans/sonuç
  dili kullanılamayacağı için S1 denetimi kritik kalır.
- **E4:** Overlap validator'ın hardcoded `LIVE_SHORTLIST`'i (Faz C1'de genelleştirilecek).
- **E5:** 08-24 CSV'sinin satır timestamp'leri 2026-08-21 — tarama/export tazeliği Faz A'da
  ayrıca teyit edilir (bayat export ile "yeni kolonlar yok" sonucu karıştırılmamalı).
- **E6 (kapsam dışı, takipte):** Karne API `401 Unauthorized` (2026-08-13 girdisi) —
  bu pivotu bloklamaz, operasyonel iş olarak ayrı kalır.

## 7. Kapsam Dışı

- FinSense Deney 2/3 ve close5_real/c2c_5d kök-neden avı → `docs/2026-08-15-bekleyen-ikincil-isler-kapsamli-plan.md`.
- Eğitim/içerik serisi (10×40) → `reports/finpilot_10x40_content_series_2026-08-10.md`.
- Locked OOS — bu planın hiçbir fazında açılmaz.

---

**Bu plan Level B'dir — Meriç onayı olmadan Faz A dahil hiçbir faz başlamaz. Onay yalnızca
Faz A+B+C'nin (üretim davranışını değiştirmeyen işler) başlamasını sağlar; D, E, F ve G her
seferinde kendi onay noktasında durur.**
