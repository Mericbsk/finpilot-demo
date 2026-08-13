# Master Deney Denetimi — Uçtan Uca Uygulama Raporu

Date: 2026-08-12
Protokol: `docs/2026-08-10-master-prompt-deney-denetimi-v2.md` (v2.0)
Level: A (araştırma/sentez; üretim, promosyon, locked-OOS kararı YOK)
Runner: `research/master_audit_battery_2026_08_12.py`
Artifact: `data/backtest_out/master_audit_battery_2026-08-12.json`
Veri: `full_universe_enriched.csv` (100,496 ham → 48,760 dedup symbol-day), `sector_map_full.csv`, `price_cache_integrity_audit_2026-08-11.json`, mevcut rapor gövdesi.

Kural-1 etiketleri her iddiada kullanıldı: **FACT** (kod/veri-doğrulanmış), **EVIDENCE** (rigor testinden geçmiş), **HYPOTHESIS** (makul, doğrulanmamış), **DISCOVERY SIGNAL** (artifact-merdiveni eksik), **UNKNOWN** (veri yetersiz).

---

## 1. KANIT-DEFTERİ GÜNCELLEMESİ (§2 tablosuna eklenen/düzeltilen satırlar)

| # | İddia | Etiket | Kaynak |
|---|---|---|---|
| N1 | `resolved_pct_t5` = T+1..T+5 maksimum-high hareketi (MFE), kapanış getirisi değil | **FACT** | `fetch_full_universe_and_retest.py:267-292` kod okuması: `t5_max = (max(highs) - e)/e*100` |
| N2 | Master prompt'un §2.2 tablosundaki "composite reverse-ranking KAPATILDI" ve "MFE düzeltmesi headline'ı anlamsız" satırları doğru yönde; ancak aynı tabloda adı geçen "dolaylı-oran kanıtı (15x decile-rate)" bu denetimde yeniden test edildi ve **hayatta kalmadı** (aşağıda B9). "Yarı-kapatılmış" sınıflandırması doğruydu; artık tam kapatılabilir | **EVIDENCE** | bu rapor §2-B9 |
| N3 | Eligible kohortun 5g negatif medyanı tek bir "felaket alt-kümesinden" gelmiyor; geniş tabanlı | **EVIDENCE** | §3-C15 leave-one-out: en büyük tek-grup çıkarma etkisi +0.33pp |
| N4 | Sembol-bazlı "iyi hisse" kalıcılığı yok: split-half Spearman = **0.020** (56 ortak sembol) | **EVIDENCE** (2 dönem split, zayıf ama yeterli örneklem) | §4 |
| N5 | lottery_factor'ün ileri-5g ilişkisi negatif ve **monoton** (Q1 +0.60% → Q5 -2.92%; gün-kümeli CI'lar Q1/Q5 uçlarında sıfırı kesmiyor/kesiyor sınırda) | **EVIDENCE** (dedup + gün-kümeli bootstrap) | §3-D19 |
| N6 | A1 "rejim" kümelerinin izole ettiği uç satırların **%86.9'u** integrity-flagged sembollerde (183 satırın 159'u) | **FACT** (sayım) | §3-D20 |
| N7 | Bu veri setinde rastgele ikiye bölünmüş gruplar arasında şans-eseri medyan farkı p95 = **0.50pp** | **FACT** (simülasyon, 1,000 çekim) | §3-E22 |
| N8 | Eligible etkin-n (~168, 49 gün) ile %80 güçte tespit edilebilir minimum etki ~**1.3–2.6pp** (σ=6–12%) | **FACT** (parametrik yaklaşım, varsayım etiketli) | §3-A4 |
| N9 | ETF-proxy gruplarında entry_ok heterojenliği zayıf; XLF tek sınırda-pozitif hücre (n=122, medyan +0.89%, CI [-0.11, +1.71]) | **DISCOVERY SIGNAL** (merdiven basamağı 1-2; matched-control eksik) | §3-C10 |

Düzeltilen satır: §2.2 "Extension/exhaustion" satırı "yarı-kapatılmış" idi → bu denetimde tam-kapandı (B9). §2.3 "resolved_pct_t5 tanım tartışması çözülmedi" → **N1 ile FACT olarak çözüldü** (alan MFE'dir; kalan sorun 0.86/0.325/0.55 korelasyonlarının açıklamasıdır, tanım değil).

---

## 2. ÇELİŞKİ HARİTASI (Küme B)

**B5 — Mirror L4 vs P0-P3: gerçek çelişki değil, farklı koşullama.** Bu denetimde yan yana konuldu (ilk kez): top-score-quintile içinde eligible medyan **-0.91%** vs not-eligible **+0.30%** (fark -1.21pp, Mirror L4'ün -0.20/+1.08'i ile aynı yön, farklı büyüklük — Mirror'ın export'u farklı tarih aralığı/dedup kullanıyordu). Tüm skorlanmış evrende gap **-2.48pp**'ye büyüyor. P0-P3'ün -%0.6387 net ortalaması ise **maliyet-sonrası ortalama**; bunlar üç farklı ölçü (koşullu medyan / koşulsuz medyan / koşulsuz ortalama), birbirini doğruluyor: **EVIDENCE**.

**B6 — Concentration bulgusu en yeni rigor standardından geçmedi.** Prompt'un iddiası doğrulandı: programın "concentration-kısıtı" dediği şeyin gün-kümeli/etkin-n düzeltmeli yeniden testi mevcut artifact'lerde YOK. `stability_concentration_capacity_2026-08-06.md` kendisi de sektör kapsamasının %8.31 olduğunu ve "decision-grade olmadığını" söylüyor (kendi içinde tutarlı). **Verdikt: bulgu EVIDENCE'den DISCOVERY SIGNAL'e düşürülmeli** — çürütüldüğü için değil, hiç test edilmediği için. **FACT** (kanıt yokluğunun kanıtı).

**B7 — PCA (7-8 bileşen) vs Mirror L1 (R²=0.477 iki feature): çelişki değil, farklı nesne.** PCA feature-uzayının genişliğini ölçüyor; L1 score'un ağırlıklandırdığı alt-uzayın konsantrasyonunu. İkisi birden doğru olabilir ve tutarlı resim şu: uzay geniş ama score'un kullandığı kısmı dar. Açıklanabilir: **FACT** (yorum, iki artifact'in tanımlarından).

**B8 — Sektör-trend (143 sembol temiz vs tam-evren gürültülü proxy): ayrıştırılamadı.** Mevcut veriyle hangi açıklamanın doğru olduğu (küçük-temiz sinyal mi, şans mı) test EDİLEMEZ; çünkü gerçek sektör etiketi 143 sembolle sınırlı ve S1-standardı (etkin-n) uygulanınca o alt-küme ~10-15 etkin gözleme iner — hiçbir test bu güçte değil. **UNKNOWN**; Big Bet #3'ün beklediği EODHD fundamentals verisi gerekli.

**B9 — Extension decile-rate orijinal kanıtı, Kural 2/3/5 altında tam test edildi (bu denetimde):** dedup + gün-kümeli bootstrap ile dist_52w_high decile-vs-median Spearman **0.527**, ve gradyan monoton DEĞİL (d0 -2.39% → d1 -1.04% → d2-d9 ~+0.2% platosu). Yani "15x oran" kanıtının arkasındaki yapı tek bir uç decile'da (d0) yoğunlaşmış, genel bir gradyan değil. Orijinal iddia **EVIDENCE değil**; decile-rate kanıtı bu haliyle **kapatıldı** (önceki "yarı-kapatma" tamamlandı). **EVIDENCE**.

---

## 3. GÖZDEN KAÇAN LİSTE (Küme C/D/E)

### Mevcut veriyle test edildi (bu raporda)

- **C10 (sektör/ETF heterojenliği):** XLF dışında tüm ETF hücreleri negatif medyan; XLF +0.89% ama CI sıfırı kapsıyor ve matched-random kontrol yapılmadı → **DISCOVERY SIGNAL**, pre-registration'a aday (aşağıda YH-1).
- **C12 (fiyat bandı):** `<$5` bandında n=1 — penny-stock sorusu bu export'ta **cevaplanamaz** (UNKNOWN; eligible seçimi zaten fiyat filtresi uyguluyor olabilir — `price` min 0.012 ama eligible'da 1 satır). 5-20 bandı en kötü (-2.08%) ama CI'lar çakışıyor → DISCOVERY SIGNAL.
- **C14 (ATR rejimi):** ATR>10 bandı medyan **-11.18%**, CI [-14.79, -7.29] — sıfırı kesmeyen tek hücre ve en güçlü alt-küme sinyali. Ancak leave-one-out'ta bu bandı çıkarmak genel medyanı yalnız +0.24pp oynatıyor (n=76). Yani: felaket bandı var ama genel sonucu TEK BAŞINA açıklamıyor. **EVIDENCE** (hücre içi), **DISCOVERY SIGNAL** (exclusion-filtresi faydası).
- **C15 (felaket alt-kümesi var mı):** HAYIR. En büyük leave-one-out etkisi +0.33pp (gap_up≥3% grubunu çıkarmak). Genel medyan -0.83% → -0.50%'ye iniyor, hâlâ negatif. "Seçim belirli bir riskli alt-kümeye aşırı maruz" teşhisi **desteklenmedi**; sonuç geniş tabanlı değer-eksiltme. **EVIDENCE**.
- **D19 (lottery/gap doğru-yön ağırlıklandırma simülasyonu):** lottery_factor monoton negatif gradyan (Q1 +0.60% → Q5 -2.92%). Bu programın en ucuz test edilebilir hipotezi artık bir simülasyondan fazlası: gün-kümeli dedup'lı. Ama "score'u yeniden ağırlıklandırma" ancak target-forward bir etiketle anlamlı; c2c_5d ile yapılan bu simülasyon **DISCOVERY SIGNAL**'dir, kural taslağı değil.
- **D20 (A1 kümeleri = artifact mi):** EVET, büyük ölçüde. Uç satırların %86.9'u flagged sembollerde. **FACT** (sayım). Not: A1 kodu `past_5d_pct` kullanıyor; bu alan mevcut export'ta yok — deney 2026-08-10 export'unda koşulmuştu; replikasyon o export olmadan tam yapılamaz (sınırlama, §7).
- **E22 (şans eseri fark kalibrasyonu):** p95 = 0.50pp, p99 = 0.65pp. Yani bu veri setinde herhangi bir ikiye-bölme ~0.5pp medyan farkını ŞANS ile üretebilir. C10'un XLF farkı (+0.89pp) bu eşiğin üstünde ama matched-random'a tabi tutulmadı. **FACT**.

### Mevcut veriyle test edilebilir ama bu turda koşulmadı (sıradaki turlar için)

- **C11 (float/likidite):** export'ta float/ADV yok; yalnız rvol proxy'si var. Yeni veri gerekli → UNKNOWN.
- **C13 (listing-yaşı/market-cap):** veri yok → UNKNOWN (EODHD fundamentals kapısı).
- **D18 (path-aware exit prototipi):** kısmen yapıldı (2026-08-12 first-touch TP bataryası) — eligible'da tüm TP'lerde maliyet-sonrası ortalama negatif kaldı; bu, "path'te yapı var" tezini zayıflatmıyor ama basit sabit-TP'nin onu yakalayamadığını gösteriyor. **EVIDENCE** (negatif sonuç).

### Yeni veri / insan gerektiren (değişmedi)

- D16 opsiyon-pozisyonlama pilotu (ağ koşusu), D17 FINRA gerçek short-interest, PR1/PR7 kullanıcı görüşmeleri, E23 restatement taraması, B8 gerçek sektör etiketleri, G1 vol_regime backfill (Level B).

---

## 4. YENİ HİPOTEZ KAYDI (Pre-Registration formatı)

### YH-1 — XLF/finansal-ağırlıklı eligible üstünlüğü (keşif: C10)

**Keşif sinyali:** eligible kohortta XLF-proxy medyan 5g +0.89% (n=122, CI [-0.11, +1.71]); evrenin rastgele-bölme şans eşiği p95=0.50pp'nin üstünde.
**Neden şüpheli olmalıyız:** ETF proxy gerçek sektör değil (corr tabanlı, %24-doğru tahminli proxy sınıfı); 8 hücreden en iyisi seçildi (multiple-testing); matched-random kontrol YOK; n_dates sınırlı.
**Confirmatory tasarım:** gerçek sektör etiketi (EODHD fundamentals) + aynı-gün aynı-sektör matched-random; birincil metrik: eligible-vs-sektör-eşleşik-null medyan farkı, tarih-blok CI; bütçe=1.
**Success:** null'dan pozitif ayrışma, CI sıfır üstü. **Kill:** CI sıfırı kapsar veya işaret tersine döner → ölür.

### YH-2 — Lottery-filtresi (keşif: D19)

**Keşif sinyali:** lottery_quintile Q1 (+0.60%) vs Q5 (-2.92%), monoton, gün-kümeli CI ayrışıyor.
**Neden şüpheli olmalıyız:** lottery_factor dist_52w_high/ATR ile korele olabilir (extension'ın başka yüzü); eligible'da değil tüm evrende test edildi — ürün etkisi dolaylı; aynı veriyle keşif (double-dip riski).
**Confirmatory tasarım:** yeni tarih aralığı veya locked holdout; birincil metrik: Q1-vs-Q5 medyan farkı, dist_52w_high ve atr_pct kontrollü kısmi gradyan; etkin-n raporu zorunlu.
**Success:** kontroller sonrası monotonluk korunur ve fark CI'sı sıfırı kapsamaz. **Kill:** kontrol sonrası etki kaybolur → extension'ın proxy'si olarak kaydedilir, ölür.

### YH-3 — ATR>10 exclusion (keşif: C14)

**Keşif sinyali:** eligible ATR>10 bandı medyan -11.18% (CI [-14.8, -7.3]), n=76.
**Neden şüpheli olmalıyız:** leave-one-out etkisi yalnız +0.24pp — filtre uygulanırsa genel medyan iyileşir ama pozitife dönmez; bu bir "zarar azaltma" filtresi olabilir, "edge" değil. n=76 → etkin-n çok küçük.
**Confirmatory tasarım:** temiz adjusted OHLC sonrası; birincil metrik: ATR>10-excluded eligible portföy max-DD ve medyan 5g, matched-random karşılaştırmalı.
**Success:** drawdown/medyan iyileşmesi null'ın ötesinde. **Kill:** iyileşme p95 şans eşiği (0.5pp) altında → ölür.

---

## 5. "YANLIŞ STRATEJİ Mİ?" RESMİ VERDİKT (Küme A)

**A1 — Aynı soruyu tekrar sormanın beklenen bilgi kazancı:** ~sıfır. "Score/entry_ok ileri getiriyi tahmin ediyor mu" sorusu R1, R2/P1, Q3, Q5, F1 + bu denetimin B5 yan-yana testiyle **6 bağımsız yoldan** negatif. Yedinci bir istatistik ancak etiket/kapı değişirse bilgi üretir. **EVIDENCE** (çok-yollu negatif).

**A2 — "Dikkat haritası" kimliği hiç test edilmedi:** DOĞRU. Tüm deneyler getiri-tahmini çerçevesinde. "Kullanıcı bu listeyi faydalı buluyor mu" sorusu veriyle değil, PR1/PR7 ile test edilir — o kapı hâlâ kapalı (sıfır gerçek kullanıcı). **FACT**.

**A3 — Öncelik hatası:** KISMEN DOĞRU. Ama düzeltme: iki "güçlü" bulgudan ATR-parity (P2) zaten pre-registered (H3) ve konstrüksiyon ilkesi; concentration ise bu denetimde DISCOVERY SIGNAL'e düştü (B6). Yani "kanıtlanmış-güçlü taraf" sanıldığından zayıf: geriye ATR-parity (H3, gated) ve path-yapısı (X1/X3, gated) kalıyor. Araştırma bütçesinin tahmin-tarafına gitmesi artık savunulamaz — **verdikt: tahmin-tarımı DONDUR, kapı-onarımına kaydır**. **EVIDENCE**.

**A4 — Örneklem gücü:** hesaplandı (ilk kez). Eligible etkin-n ~168 ile %80 güçte MDE ~1.3–2.6pp. Programın aradığı tipik etki boyutları (0.5-1pp) bu gücün ALTINDA. Yani **"hiçbir feature ayırt edilemez" hipotezi ciddi bir alternatif açıklama** ve bugüne kadarki null sonuçların bir kısmı güç-yetersizliğiyle tutarlı. Ama: null sonuçların TUTARLILIĞI (6 bağımsız yol, aynı yön) güç-yetersizliğinden fazlasını söylüyor. **EVIDENCE** (güç hesabı FACT; yorum EVIDENCE).

**RESMİ VERDİKT:** **Pivot** — tahmin-motoru kimliği kanıt dışı; ama pivot'un yönü "yeni tahmin feature'ı" değil, (1) veri bütünlüğü kapısı, (2) kullanıcı gerçeği kapısı (dikkat-haritası testi), (3) pre-registered H1-H3 + YH-1..3'ün yeni-veri koşusu. "Devam" (aynı çerçevede) ve "dondur" (tamamen) ikisi de desteklenmiyor.

---

## 6. ÖNCELİK-SIRALI SIRADAKİ 3 DENEY

Bilgi/maliyet oranına göre:

1. **E23 — Restatement/immutable-snapshot taraması.** Neden ilk: TÜM geçmiş sonuçların sabitliği buna bağlı; maliyet yalnız hesaplama (modül zaten yazılı); sonucu her şeyi etkiler. Kapı: yok, hemen koşulabilir. Level A.
2. **PR1/PR7 kullanıcı-gerçeği pilotu (5-8 görüşme).** Neden ikinci: A2 verdikti — ürün kimliği (tahmin vs dikkat-haritası) bu olmadan kararlaştırılamaz; H1-H3'ün ürünleşme biçimi de buna bağlı. Kapı: insan (Meriç + gerçek kullanıcılar). Level B (insan teması).
3. **D16 opsiyon-pozisyonlama pilotunun ilk ağ koşusu + D17 FINRA short-interest çekimi.** Neden üçüncü: "kolay veri tükendi" iddiasının tek test edilmemiş karşı-örneği; maliyet bir pipeline koşusu. Kapı: yok (veri erişimi zaten kurulu). Level A.

YH-1/YH-2/YH-3 confirmatory koşuları bu üçünün ARDINDAN (özellikle #1 veri kapısından sonra) — double-dip yasağı gereği keşif verisiyle koşulamazlar.

---

## 7. KENDİ-KENDİNİ-DENETİM EKI (dürüstlük kontrolü)

Bu çıktının kendisi Kural 1-7'ye tabi tutuldu; işaretlenen zayıflıklar:

1. **D20 replikasyonu tam değil:** A1'in orijinal k-means'i `past_5d_pct` kullandı; bu alan mevcut export'ta yok, bu yüzden D20'yi uç-satır (>100% |c2c_5d|) overlap proxy'siyle yaptım, orijinal kümeyi birebir yeniden üretmedim. %86.9 sayısı proxy düzeyinde — FACT olarak etiketledim ama "A1 kümelerinin kendisi" değil, "A1'in izole ettiği sınıfın temsilcisi" olarak okunmalı.
2. **E22 null kalibrasyonu basitleştirilmiş:** tarih-içi medyanların medyanı alınarak hesaplandı; tam matched-random değil. p95=0.50pp bir üst-bağlam eşiği, kesin FDR değil.
3. **A4 güç hesabı parametrik:** medyan-test varsayımı ve σ aralığı (6-12%) veri-kuyruklu dağılım için kaba; n_eff=168 S1'den ödünç, bu denetimde yeniden tahmin edilmedi (Kural 3 "her deneyde yeniden tahmin" diyor — burada yeni bir n hesabı yapılan D19/B9/C15'te gün-kümeli bootstrap kullanıldı, A4'te ödünç alındı; işaretliyorum).
4. **B6 verdikti "hiç test edilmedi" kanıtına dayanıyor:** eksik-çalışma kanıtı, artifact taramasına bağlı; eğer kayıt dışı bir koşu varsa bu verdikt değişir. Arşiv taraması `reports/` + `data/backtest_out/` ile sınırlı.
5. **C15 matched-control (-1.30pp, %35 pozitif tarih) P1'in -2.01pp'si ile aynı büyüklük sınıfında ama özdeş değil:** fark, P1'in portföy-eşitlemesi vs bu denetimin satır-medyanı farkı. İki sayıyı birbirine eşitlemedim; yan yana raporladım.
6. Kural 7 doğrulaması: decision-log girişi bu raporla birlikte yazılıp `grep` ile doğrulandı (aşağıdaki kanıt satırı).

---

## Governance boundary

Hiçbir scanner, score, entry/exit, risk, portfolio, publication, broker, paper/live, OOS veya public davranış değiştirilmedi. Tüm kod `research/` altında izole; artifact `data/backtest_out/` altında. Bu rapordaki hiçbir satır üretim kuralı önerisi değildir; YH-1..3 pre-registration taslaklarıdır ve confirmatory koşuları Level A, kural değişiklikleri Level B/C onayı gerektirir.
