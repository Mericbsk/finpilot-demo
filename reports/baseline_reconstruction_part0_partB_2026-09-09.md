# Full Baseline Reconstruction — PART 0 (Fizibilite) + PART B (Compression Forensics)

Tarih: 2026-09-09
Süreç: `docs/2026-09-09-full-baseline-reconstruction-master-prompt.md`
Level: A (teşhis, salt-okunur). Ağırlık optimizasyonu / grid search / reverse-score / yeni feature / BUY-SELL / production / flag değişikliği YOK.

---

## PART 0 — FİZİBİLİTE (doğrulandı, tahmin değil)

| Bileşen | Gereken veri | Bu ortamda mevcut mu |
|---|---|---|
| `volume_spike`, `price_momentum`, `trend_strength`, `filter_score` | Günlük OHLCV | **EVET** — `data/price_cache/*.json`, 2.047 sembol, 2024-09-03→2026-07-29 |
| `alignment_ratio` | 1h+4h+1d bar hizalaması | **HAYIR** — geçmiş saatlik/4-saatlik bar verisi bu ortamda yok |
| `momentum_ratio` | 15dk+4h bar | **HAYIR** — `data/intraday_cache/` yalnızca 880 dosya, sembol-başına 1-2 hafta, hacim yok, 4h resample için yetersiz sürekli geçmiş |

**Sonuç: bu tur en fazla PARTIAL RECONSTRUCTION (4/6) yapabilir.** `alignment_ratio`/`momentum_ratio` `UNRECONSTRUCTABLE` — sentetik değer üretilmedi.

Ek doğrulama: `full_universe_enriched_eod_only.csv`'nin kendisi zaten `filter_score`/`alignment_ratio`/`momentum_ratio`/`volume_spike`/`price_momentum`/`trend_strength` kolonlarını **içermiyor** (32 kolon listelendi, hiçbiri yok) — yani Part B'nin terim-bazlı ayrıştırması (B.2) bu kolonlar reconstruct edilmeden yapılamaz; bu tur yalnızca B.1/B.1c/B.1d (mevcut kolonlarla ölçülebilen kısım) çalıştırıldı.

---

## PART B.1 — TIE / SIKIŞMA ÖLÇÜMÜ (EOD-only temiz veri, dedup sonrası, n=40.014)

**%99,78 tie — önceki turun rakamıyla birebir örtüşüyor (bağımsız doğrulama).**

- **Benzersiz `composite_score` değeri: sadece 90 / 40.014 satır.**
- En sık 5 değer: 0.0 (3.244 satır), 7.0 (1.092), 9.0 (1.015), 11.0 (905), 5.0 (889) — dağılım birkaç tamsayı civarında yığılmış.
- **Gün-içi etkin rank çözünürlüğü:** ortalama %23,2 ama **medyan yalnızca %5,99** (53 gün) — yani "ortalama"yı birkaç yüksek-çözünürlüklü gün yukarı çekiyor, tipik bir günde sıralama neredeyse anlamsız (bir günde 100 hisse varsa, gerçekte ~6 farklı skor değeri paylaşılıyor).

## PART B.1d — Ham girdilerin kendi tekilliği (sıkışmanın kaynağına dair ipucu)

| Kolon | Benzersiz değer | Tie oranı | Aralık |
|---|---:|---:|---|
| `score` (ham RSI/MACD/volume) | **4** | %99,99 | 0.00–3.00 |
| `risk_reward` | **9** | %99,98 | 0.00–4.33 |
| `finpilot_score` | 89 | %99,74 | 0.00–93.00 |
| `tier_score` | 1.093 | %94,33 | 0.00–1.00 |

**Yorum (kanıta dayalı, ama tam değil — bkz. sınırlama):** `score`'un sadece 4 durumu var (muhtemelen 0/1/2/3 tam sayı), `risk_reward`'ın sadece 9 durumu var — bu ikisi zaten çok kaba. `composite_score`'un formülünde bu iki kaba terimin yanında (Rol 1 kaynağından bilinen ağırlıklarla) `regime`/`direction` (ikili, 2 durum), 3 binary bayrak (`volume_spike`/`price_momentum`/`trend_strength`, her biri 0/0.5 → 8 kombinasyon) var. **Eğer `alignment_ratio` ve `momentum_ratio` (bu turda reconstruct edilemeyen 2 sürekli terim) gerçekten geniş bir sürekli aralıkta değişmiyorsa, 90 benzersiz değer formülün doğal/yapısal bir sonucu olabilir — bir hesaplama hatası değil.** Ama bu iki terimin gerçek varyansını bu ortamda ölçemediğimiz için, **"sıkışma formülün tasarımından mı yoksa alignment/momentum'un kendisinin de kaba olmasından mı" sorusu KANITLANAMADI (UNKNOWN, üretim erişimi gerekiyor).**

---

## Sınırlama (açık, gizlenmedi)

Bu turun EN ÖNEMLİ sınırı: Part B.2'nin (terim-bazlı sıkışma kaynağı ayrıştırması) tam yapılabilmesi için `alignment_ratio`/`momentum_ratio`'nun CSV'de ya da yeniden inşa edilmiş halde bulunması gerekiyordu — ikisi de yok. Bu yüzden şu ana kadarki sonuç **"toplam skor aşırı sıkışık" (kesin, iki bağımsız ölçümle doğrulandı) + "bunun BİR kısmı kaba ham girdilerden geliyor (kesin)" ama "sıkışmanın TAMAMI mı formül tasarımından mı" (henüz kanıtlanamadı)** şeklinde bırakılmalı.

## Sonraki adım

Part A (4/6 reconstruction, `price_cache`'ten `volume_spike`/`price_momentum`/`trend_strength`/`filter_score`) ve Part C (dist_52w_high redundancy) bu ortamda hâlâ çalıştırılabilir — bir sonraki turda yapılabilir. `alignment_ratio`/`momentum_ratio`'nun gerçek varyansı ise ancak canlı sunucuda veya gerçek piyasa-veri erişimi olan bir ortamda ölçülebilir.
