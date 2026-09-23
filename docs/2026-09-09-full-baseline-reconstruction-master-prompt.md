# FINPILOT — FULL BASELINE RECONSTRUCTION + RANKING COMPRESSION FORENSICS v1.0

Durum: ACTIVE
Seviye: Level A (araştırma/teşhis). **Bu prompt hiçbir ağırlık optimizasyonu, grid search, reverse-score, yeni feature, BUY/SELL çıkarımı, production değişikliği veya flag açma/kapama üretmez.**
Tetikleyici: `reports/baseline_ranking_health_2026-09-09.md` — composite_score random'dan kanıtla daha kötü (permutation p=1.000, Q1>Q5 ters ilişki, %99,78 tie), ama baseline'ın tamamı reconstruct edilemediği için "mevcut ölçülen baseline BAŞARISIZ" ile "production baseline mimarisi BAŞARISIZ" iddiaları henüz ayrıştırılamıyor.
İlişki: Bu, üç-prompt ailesinin (Review Board / Hipotez Üretimi / Araştırma Portföyü) dışında, dördüncü ve en dar-kapsamlı bir **teşhis** promptu — tek bir soruya cevap arar: *skorun içindeki bilgi mi yok, yoksa skor İNŞASI mı bilgiyi öldürüyor?*

---

## SİSTEM ROLÜ

Sen bu programın en kritik metodolojik ayrımını netleştiren bir **Ranking Forensics Denetçisi**sin:

> **IMPLEMENTED ≠ ACTIVE ≠ INFLUENTIAL ≠ PREDICTIVE ≠ WELL-CONSTRUCTED.**

Şu ana kadar zincirin ilk 4 halkası test edildi (flag'ler implemented+active+influential ama predictive değil). **Bu prompt 5. halkayı test eder: skor iyi inşa edilmiş mi, yoksa doğru bilgiyi taşısa bile yapısal olarak (sıkıştırma, yuvarlama, eksik bileşen) kaybediyor mu?**

Temel ilke:

> **"Skoru nasıl iyileştiririz" sorma. "Skor neden yanlış sıralıyor" sor.** Bu iki soru karıştırılırsa (örn. ağırlık denemesi, reverse-score), sonuç yeni bir HARKing/multiple-testing turu olur — programın 9.781 test bütçesine yeni, kontrolsüz denemeler eklenir.

---

## PART 0 — FİZİBİLİTE KAPISI (ZORUNLU, İLK ADIM, SONUÇLARDAN ÖNCE)

Reconstruction'a başlamadan önce, hangi bileşenin gerçekten yeniden inşa edilebilir olduğunu **veri erişilebilirliğine göre** belirle — bu bir tahmin değil, dosya sistemi kontrolüdür:

| Bileşen | Gereken veri | Bu ortamda mevcut mu? |
|---|---|---|
| `volume_spike`, `price_momentum`, `trend_strength`, `filter_score` | Günlük OHLCV (`df_1d`) | **EVET** — `data/price_cache/*.json`, 2.047 sembol, 2024-09-03→2026-07-29, tam OHLCV+volume |
| `alignment_ratio` | 1 saatlik + 4 saatlik + günlük çok-zaman-dilimli bar hizalaması | **HAYIR** — bu ortamda 1h/4h geçmiş bar verisi yok |
| `momentum_ratio` | 15 dakikalık + 4 saatlik bar | **KISMEN/HAYIR** — `data/intraday_cache/*.json` yalnızca 880 dosya, sembol-başına 1-2 hafta, 15dk bar var ama 4h resample'ı için yeterli sürekli geçmiş yok, hacim de yok |

**Sonuç (bu turda doğrulandı, tahmin değil):** 4/6 eksik bileşen (`volume_spike`, `price_momentum`, `trend_strength`, `filter_score`) **tam reconstruct edilebilir** (evren-çapı, ~2.047 sembol). 2/6 bileşen (`alignment_ratio`, `momentum_ratio`) **bu ortamda yapısal olarak reconstruct edilemez** — gerçek çok-zaman-dilimli geçmiş intraday veri, canlı sunucu veya piyasa veri sağlayıcısı erişimi gerektirir.

**Zorunlu etiketleme kuralı:** Bu iki bileşen olmadan üretilecek herhangi bir "full reconstruction" sonucu **PARTIAL RECONSTRUCTION (4/6)** olarak etiketlenmeli, "FULL" denemez. Raporun kendisi bu sınırı en üstte, kalın harfle belirtmeli.

---

## PART A — PARTIAL FULL-INPUT RECONSTRUCTION (4/6 bileşen)

### A.1 — Yeniden hesapla
`scanner/features.py::analyze_price_momentum`, `check_volume_spike`, `check_trend_strength` fonksiyonlarını **BİREBİR AYNI** (kaynak kopyalanır, mantık değiştirilmez — bu programın standart disiplini) kullanarak, `full_universe_enriched_eod_only.csv`'deki (temiz alt-küme, 2026-09-03 DATA_REPAIR sonrası) her `(symbol, scan_date)` için `data/price_cache/<symbol>.json`'dan `df_1d`'yi kur, 3 bileşeni + `filter_score`'u yeniden hesapla.

### A.2 — Karşılaştır
CSV'de zaten var olan (varsa) değerlerle satır-satır karşılaştır. Uyuşmazlık oranını raporla — bu, mevcut export'un kendisinin doğru hesaplandığını doğrular ya da bir ek veri-bütünlüğü sorunu ortaya çıkarır.

### A.3 — Kapsam raporu
Kaç `(symbol, date)` çifti `price_cache`'te bulunamadı (sembol yok / tarih aralığı dışı) — bu, "reconstruction kapsamı" olarak ayrı raporlanır, gizlenmez.

### A.4 — `alignment_ratio` / `momentum_ratio` için YAPILMAYACAKLAR
Bu iki bileşen İÇİN sentetik/proxy değer ÜRETİLMEZ (örn. "günlük veriden kabaca tahmin edelim" gibi bir kısayol YASAK — bu, sessizce yeni bir hipotez icat etmek olur). Bu iki bileşen raporun her yerinde `UNRECONSTRUCTABLE (bu ortamda)` olarak işaretlenir.

---

## PART B — RANKING COMPRESSION FORENSICS (ek veri gerekmez, mevcut CSV'den tam çalıştırılabilir)

Ağırlık denemesi YOK. Sadece **mevcut** `composite_score`'un neden bu kadar tie/sıkışmış olduğunu ölç:

### B.1 — Tekillik/tie ölçümü
- Toplam benzersiz `composite_score` değeri / toplam satır.
- Gün-içi (aynı `scan_date`) benzersiz skor sayısı / o günkü satır sayısı — **etkin rank çözünürlüğü**.
- Tie'ların skor dağılımındaki yoğunlaştığı bölge (histogram) — sıkışma tek bir bölgede mi (örn. orta-skor) yoksa evrensel mi?

### B.2 — Sıkışmanın kaynağını izle
Skor formülünün (`compute_recommendation_score`) her bir terimi için, **ham (continuous) değer** ile **skora eklenen değer**i ayrı ayrı hesapla:
- `regime`/`direction`: zaten binary (2.0/0.0) — bunlar zaten 2 değerli, sıkışmaya katkısı yapısal ve kaçınılmaz.
- `score` (RSI/MACD/volume raw, ×0.5): kaynağı 0-3 arası muhtemelen tamsayı — kaç farklı değer alıyor?
- `filter_score` (×1.5): 0-3 arası tamsayı (3 binary'nin toplamı) — kaç farklı değer alıyor?
- `alignment_ratio` (×2.0), `momentum_ratio` (vol-regime'e göre ×1.5-2.5): bunlar continuous olmalı — CSV'de gerçekten continuous mı, yoksa zaten yuvarlanmış/quantize mi geliyor?
- `volume_spike`/`price_momentum`/`trend_strength` (her biri +0.5 binary): yapısal olarak 3 bileşenin YALNIZCA 8 kombinasyonu var.

**Beklenen bulgu yönü (önceden yazılan, sonuç değil, hipotez):** Toplam skorun büyük kısmı ikili (binary) terimlerden geliyorsa, sürekli (continuous) terimlerin payı küçükse, sıkışma "yanlış hesaplama" değil **formülün kendi tasarımının** doğal bir sonucu olabilir — bu ayrımı yapmadan "compression = bug" demek yanlış olur.

### B.3 — Etkin bilgi kapasitesi
Kaç bit'lik bilgi taşıyabilecek bir formül (kaç farklı olası çıktı kombinasyonu var, teorik olarak) vs kaç farklı değer GERÇEKTE gözlemleniyor. İkisi arasındaki fark, "veri sıkışması" (birçok hisse aynı ham değerlere sahip) ile "formül sıkışması" (formülün kendisi az sayıda çıktı üretebilir) arasında ayrım yapar.

---

## PART C — OVEREXTENSION / TERSLİK ARAŞTIRMASI (yalnızca AÇIKLAMA, reverse-score ÜRETME)

Q1 (+8,26) vs Q5 (+0,15) ters ilişkisi için:

### C.1 — `dist_52w_high` redundancy hipotezini test et
composite_score ↔ dist_52w_high korelasyonu (0,638) zaten bulunmuş. Sor: composite_score'un yüksek olması, büyük ölçüde dist_52w_high'ın yüksek olması (yani hisse 52 hafta zirvesine yakın) anlamına mı geliyor? Eğer öyleyse, ve dist_52w_high'ın kendisi zaten (bu programda ayrı test edilmiş) forward-return ile **zayıf/ters** ilişkiliyse, composite_score'un tersliği kendi redundancy'sinden miras kalmış olabilir.

### C.2 — Mekanistik hipotez, kanıtla
"Yüksek composite_score = 52w-high'a yakın + güçlü momentum sinyalleri = potansiyel overextension/exhaustion" hipotezini (bu programda önceden var olan bir hipotez — bkz. `finpilot-big-bet-1-findings.md`'deki "extension/exhaustion" izleği) MEVCUT veriyle tekrar test et: yüksek composite_score alt-grubunda `dist_52w_high` dağılımı gerçekten sıkışık mı (hepsi 52w-high'a çok yakın)?

### C.3 — YAPILMAYACAK
Bu bölümden "o zaman skoru tersine çeviririz" sonucu ÇIKARILMAZ. Amaç sadece AÇIKLAMA — hangi mekanizmanın tersliği ürettiğini anlamak, düzeltmeyi önermek değil.

---

## PART D — HORIZON AYRIŞTIRMASI (1D/3D/5D)

Mevcut `c2c_1d`/`c2c_5d` (ve varsa ara horizonlar) için B ve C'deki analizleri ayrı ayrı tekrarla — **yeni bir "en iyi horizon" optimizasyonu değil**, sadece "sorun her horizonda aynı mı, yoksa ufuk-bağımlı mı" sorusuna cevap.

---

## YASAKLAR (ZORUNLU, TÜM BÖLÜMLER İÇİN)

- Ağırlık optimizasyonu / grid search **YOK**.
- Reverse-score veya yeni bir composite formül üretmek **YOK**.
- Yeni feature eklemek **YOK**.
- BUY/SELL veya herhangi bir eyleme geçirilebilir çıkarım **YOK**.
- Production/scanner/flag değişikliği **YOK**.
- `alignment_ratio`/`momentum_ratio` için sentetik/tahmini değer üretmek **YOK** — UNRECONSTRUCTABLE etiketiyle bırak.
- Bu çalışmanın SONUCU olumluysa (skor gerçekten sıkışma/redundancy yüzünden bilgi kaybediyorsa) bile, "o zaman şimdi mimariyi değiştirelim" denmez — bu, **ayrı bir pre-registration** ile Level B/C onayı gerektirir.

---

## GOVERNANCE

- decision-log satırı: `[TARİH] - Full Baseline Reconstruction (Part 0-D): <özet> (Level A, teşhis)`
- Level: A. Hiçbir üretim/flag kararı bu promptun çıktısı olarak ALINAMAZ.
- Bu çalışma BAŞARILI olursa (yani skor construction'da somut bir kayıp mekanizması bulunursa) bile, sıradaki adım "mimari yeniden tasarım için AYRI bir pre-registration" — bu promptun kapsamında değil.

---

## SON RAPOR FORMATI

```
## PART 0 — FİZİBİLİTE
Reconstruct edilebilir: [...] / Reconstruct edilemez (UNRECONSTRUCTABLE): [...]

## PART A — PARTIAL RECONSTRUCTION (4/6)
Kapsam: n_satır, n_sembol-bulunamadi
Uyuşmazlık oranı (CSV vs yeniden hesaplanan)

## PART B — COMPRESSION FORENSICS
Tie oranı, gün-içi etkin rank çözünürlüğü, terim-bazlı sıkışma kaynağı

## PART C — OVEREXTENSION
dist_52w_high redundancy testi sonucu, mekanistik aciklama (kanit'a dayali)

## PART D — HORIZON
1D/3D/5D karşılaştırması

## SONUÇ
"Bilgi feature'larda yok" mu, yoksa "score construction'da kayboluyor" mu — hangisi, ne kanıtla?

## SONRAKI ADIM
(Bu prompt kapsamında ÖNERİ YOK — yalnızca "ayrı pre-registration gerekiyor mu" notu)
```
