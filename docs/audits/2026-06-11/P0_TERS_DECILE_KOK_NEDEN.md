# P0 Kök Neden Analizi — Ters-Decile / Skor Edge Sorunu

**Tarih:** 2026-06-11
**Tetikleyici:** [WIN_RATE_ANALIZI.md](../audits/2026-06-11/WIN_RATE_ANALIZI.md) — profitcore "NO EDGE DETECTED", decile_lift 0.728
**Yöntem:** `scanner/finpilot_score.py` + `scanner/score_engine.py` kod incelemesi + `data/signal_archive/*.json` (52 dosya) + `data/finpilot.db:signals_archive` (5.719 kayıt) doğrudan analizi + **tüm tarihsel arşivin (2025-09 → 2026-05) yfinance T+5 ile çözümlenmesi (2.163 sinyal)**

---

## 0. ⭐ TAM-TARİH ANALİZİ (en güvenilir — eski sinyaller dahil)

İlk analiz yalnızca DB'de çözülmüş 246 sinyale (tek hafta: 2026-05-12→19) dayanıyordu. Eski sinyallerin tamamı (2025-09'dan beri binlerce) DB'de hâlâ `open`. Bu yüzden **tüm arşiv BUY/TRUE sinyallerini yfinance T+5 ile yeniden çözdüm: 2.163 sinyal**.

### Şemaya göre ayrılmış sonuç (ölçek karışmasını gidererek)

**YENİ 0-100 composite (scanner_v2), n=586:**

| Quintile | Skor | n | Win % | Ort. % |
|----------|------|---|-------|--------|
| Q1 (düşük) | 11–53 | 117 | 36.8 | +0.91 |
| Q2 | 53–60 | 117 | 41.9 | +0.99 |
| Q3 | 60–62 | 117 | 37.6 | -1.64 |
| Q4 | 62–69 | 117 | 41.0 | -0.93 |
| Q5 (yüksek) | 69–89 | 118 | 36.4 | -0.68 |
| **GENEL** | | 586 | **38.7** | **-0.27** |

- `corr(score, win) = -0.022`, `corr(score, return%) = -0.072` → **sıfıra yakın, çok hafif negatif**.

**ESKİ 0-3 ham ölçek, n=1.036:** win %37.2, ort. -2.37, `corr +0.04`.

### 🔑 KRİTİK DÜZELTME
> İlk 30-günlük profitcore penceresindeki **dramatik "ters-decile" (decile_lift 0.728, monoton tersine dönüş) büyük ölçüde küçük-örneklem gürültüsüydü.** 586 düzgün-ölçekli örnekte monoton bir tersine dönüş YOK; korelasyon sadece **~sıfır** (-0.022 ila -0.072).
>
> **Doğru teşhis: skor "ters" değil, "kör" — kazananı kaybedenden ayırt etme gücü yok (edge ≈ 0).** Win rate tüm dönemler ve şemalarda tutarlı şekilde **%37–39**, ortalama getiri negatif.

### Kalan uyarı
YENİ-ölçek verinin %99'u (582/586) tek aydan (2026-05). Yani çok-dönemli edge hâlâ kanıtlanmadı; sadece "mevcut tüm veride edge yok" diyebiliriz.

---

## 1. İLK BULGULAR (dar pencere — Bölüm 0 ile rafine edildi)

### Bulgu 1 — Skorun kazananları sıralama gücü YOK
DB'deki çözülmüş sinyaller (n=246, win/loss etiketli):

| Quintile (score) | Skor aralığı | n | Win % |
|------------------|-------------|---|-------|
| Q1 (en düşük) | 0–53 | 49 | 16.3 |
| Q2 | 53–60 | 49 | 12.2 |
| Q3 | 60–62 | 49 | **26.5** |
| Q4 | 62–69 | 49 | **6.1** |
| Q5 (en yüksek) | 69–87 | 50 | 14.0 |
| **GENEL** | | 246 | **15.0** |

- `corr(score, win) = -0.099` → hafif **negatif**. En yüksek skorlu sinyaller ortalamanın altında.
- Genel win rate **%15** (37 win / 209 loss). Sinyaller para kaybettiriyor.
- profitcore'un yfinance T+5 analizi (%36.8) ile birlikte: skor monoton bir edge üretmiyor.

### Bulgu 2 — `finpilot_score` hiç hesaplanmıyor/saklanmıyor
- `signals_archive.finpilot_score` sütunu **tamamen NULL** (246/246).
- Yani `compute_finpilot_score()` üretimde sinyallere yazılmıyor; sadece ham `score` (composite) saklanıyor.
- `score_engine.compute_recommendation_score` çalışıyor ama birleşik skor katmanı atlanıyor.

### Bulgu 3 — Skorlama momentum/trend-takip ağırlıklı
`score_engine.compute_recommendation_score` ağırlıkları:
```
regime ×2 + direction ×2 + score ×1 + filter_score ×1.5
+ alignment_ratio ×2 + momentum_ratio ×2
+ volume_spike/price_momentum/trend_strength ×0.5
```
- En yüksek skorlu gerçek sinyaller (ROIV 89, ARM 87, GS 87) hepsi **"Trend+ Uyum+ Filtre 3/3"** = güçlü momentum + tam hizalama.
- Bu sinyaller T+5'te en kötü performansı veriyor → **mean-reversion**: güçlü momentumu tepeden alıp kısa vadeli geri çekilme yiyor.
- **Skor teknik olarak doğru hesaplanıyor; sadece yanlış şeyi ölçüyor** (momentum gücü ≠ 5-günlük forward getiri, bu evren/ufukta).

### Bulgu 4 — Arşivde 3 farklı şema (audit gürültüsü)
| Şema | `score` anlamı | Örnek dönem | Adet |
|------|----------------|-------------|------|
| OLD (`scanner_import`) | her zaman 0.0 | 2025-09/10 | 5.722 (JSON) |
| MID (raw) | 0–3 ham sinyal | 2026-02/03 | — |
| NEW (`scanner_v2`) | 0–100 composite | 2026-05+ | 59 (JSON) |

- profitcore `extract_score` sırası `("score", "finpilot_score", "composite_score", "strength")` → her zaman `score`'u alır. Şema karışıksa uzun pencerede elma-armut karışır. (30 günlük pencerede tutarlı, ama metodolojik kırılganlık.)

### Bulgu 5 — Sonuç çözümleme (resolution) neredeyse durmuş
- `signals_archive`: 5.070 / 5.719 hâlâ `open`. Sadece 246 çözülmüş (37 win, 209 loss).
- `resolved_pct` sütunu **tamamen NULL** — yüzde getiri hiç doldurulmuyor, sadece win/loss etiketi.
- Edge ölçümü için yeterli çözülmüş örnek yok; mevcut olan da negatif.

---

## 2. KÖK NEDEN (sentez — tam-tarih ile revize)

> **Skor "ters" değil, "kör".** 2.163 tarihsel sinyalde skor↔kazanç korelasyonu ~sıfır (-0.022 ila -0.072). Skor motoru momentum/trend gücünü doğru ölçüyor ama bu metrik T+5 forward getiriyle anlamlı korele değil — ne pozitif ne güçlü negatif. Yani skor, kazananı kaybedenden ayırt edemiyor.
>
> İlk 30-günlük penceredeki "dramatik ters-decile" (decile_lift 0.728) **küçük-örneklem + karışık-şema gürültüsüydü**; geniş veride bu monotonluk kayboluyor.

Katkıda bulunan ikincil sorunlar:
1. `finpilot_score` katmanı devre dışı (NULL) → birleşik skor hiç test edilmiyor.
2. `resolved_pct` boş + çoğu sinyal `open` → ölçüm döngüsü kapanmıyor; YENİ-ölçek verinin %99'u tek aydan.
3. Çoklu arşiv şeması (0-3 vs 0-100) → tarihsel audit gürültülü.
4. Win rate tüm dönemlerde %37–39, ortalama getiri negatif → çekirdek tarama tek başına edge üretmiyor.

---

## 3. ÖNERİLEN DÜZELTMELER (öncelik sırası)

### 🔴 P0-A — Çözümlemeyi ölçeklendir, SONRA kalibre et
- **Önce veri:** Edge kararı tek-ay verisine güvenemez. `resolved_pct` çözümleme job'unu tüm `open` sinyallere uygula → çok-aylı, ≥1000 örnekli temiz set.
- **Sonra kalibrasyon:** `score_engine` ağırlıklarını walk-forward ile yeniden optimize et (momentum/alignment ağırlığını azalt, farklı ufuklar T+1/3/10 dene). Skor "kör" olduğu için yön çevirmek değil, **farklı feature'lar** gerekebilir.
- **Doğrulama:** profitcore_audit decile_lift > 1.3 + perm_p < 0.05 olana kadar tekrarla.

### 🔴 P0-B — `finpilot_score`'u sinyallere yaz
- Sinyal üretiminde `compute_finpilot_score`/`compute_recommendation_strength` sonucunu `signals_archive.finpilot_score`'a kaydet.
- Böylece iki skor (ham vs birleşik) ayrı ayrı audit edilebilir.

### 🟠 P1 — Sonuç çözümleme döngüsünü canlandır
- `resolved_pct`'i dolduran job'u (yfinance T+horizon) zamanlanmış çalıştır; `open` sinyalleri çöz.
- Hedef: haftalık otomatik profitcore, ≥500 çözülmüş örnek.

### 🟠 P1 — Arşiv şemasını tekilleştir
- Tek şema (`scanner_v2`) standardı; `score` = ham, `finpilot_score` = 0-100. profitcore `extract_score`'u tek alana sabitle.

### 🟡 P2 — Edge kanıtlanana kadar üretim iddiası yok
- Pazarlama/funding'de skor/sinyal "kârlı" denmesin (bkz. BELGE_SENKRON_RAPORU).

---

## 4. ÖZET TABLO

| # | Sorun | Kanıt (tam-tarih) | Düzeltme | Öncelik |
|---|-------|-------|----------|---------|
| 1 | Skor edge'i ≈0 (kör, ters değil) | corr -0.022/-0.072, n=586 | Veri ölçekle + yeniden kalibre | 🔴 P0-A |
| 2 | finpilot_score NULL | tümü boş | Sinyale yaz | 🔴 P0-B |
| 3 | Win rate %37-39, getiri negatif | 2.163 sinyal | Feature/ufuk revizyonu | 🔴 P0-A |
| 4 | Çoklu şema | OLD/MID/NEW | Tekilleştir | 🟠 P1 |
| 5 | Çözümleme durmuş | 5070 open, resolved_pct NULL | Job canlandır | 🟠 P1 |

---
*FinPilot P0 Kök Neden — 2026-06-11 — Kaynak: kod + signal_archive + finpilot.db*
