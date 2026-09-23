# Winner Anatomy — EXP-01 + EXP-02 Sonuçları

Tarih: 2026-08-13 · Statü: Level A (keşif, üretim değişikliği yok) · Veri: `data/backtest_out/full_universe_enriched.csv`

## Metodoloji notu

`c2c_5d` (temiz close-to-close 5-günlük getiri) kullanıldı, `resolved_pct_t5` değil — ikincisi daha önce MFE-kirli olduğu kanıtlanmıştı (`finpilot-score-backward-looking-central-finding`). Bucket'lar: control (tüm evren) ve W0 (negatif) → W5 (%10+) arası 5 winner grubu.

**Temizlik:** 100.496 satırdan başlandı → (symbol,scan_ts) dedupe sonrası 76.027 (24.469 tam-mükerrer satır bulundu, farklı `source_file`'larda aynı sinyal tekrar kaydedilmiş, c2c_5d hepsinde aynıydı — güvenle silindi) → c2c_5d dolu 64.454 → |c2c_5d|>%100 olan 237 satır **veri hatası olarak dışlandı** (örnek: 2025-09-12'de CAT/BA/RTX/LMT/NOC/DE/BKNG/DE fiyatı hepsi 37.63 gösteriyor — açık bir pipeline hatası, gerçek fiyat değil). Nihai n=64.217, tarih aralığı 2025-09-11 → 2026-07-31.

**Önemli eksiklik:** `squeeze_factor`/`catalyst_factor` %45.7 NaN, `lottery_factor`/`overnight_gap_factor` %42.4 NaN, `tier_score` %57.1 NaN, `finpilot_score` %28.2 NaN. Bu kolonlar muhtemelen scanner'ın iki farklı sürümünde hesaplanmış — tüm evrende değil, alt kümede güvenilir. Aşağıdaki bulgular bu kolonlar için sadece dolu-olan alt kümeyi yansıtıyor.

## Bucket büyüklükleri

| Bucket | n | Tanım |
|---|---:|---|
| W0_negative | 31.276 | c2c_5d < 0% |
| W1_0to1 | 5.510 | 0–1% |
| W2_1to3 | 8.216 | 1–3% |
| W3_3to5 | 6.039 | 3–5% |
| W4_5to10 | 7.199 | 5–10% |
| W5_10plus | 5.977 | 10%+ |

## Bulgular

**1) composite_score / finpilot_score — düz, ayırt etmiyor.** Medyan composite_score: control 29, W0 29, W1 31, W2 29, W3 29, W4 26, W5 27. En büyük kazananlar (W5) en büyük kaybedenlerden (W0) daha düşük skorlu. `finpilot-score-backward-looking-central-finding`'i bu bağımsız veri setinde de doğruluyor — score'un forward-return ayırt ediciliği yok.

**2) entry_ok / vol_regime — U-şekli, yön değil oynaklık filtresi olabilir.** `entry_ok` lift'i: W0(kaybeden)=1.15x, W1-W4=0.76-0.84x, W5(en büyük kazanan)=1.13x. `vol_regime=2` (yüksek oynaklık) oranı da aynı U-şeklini gösteriyor: W0=%80.8, W1=%60.9 (en düşük), sonra W2→W5 arası tekrar yükseliyor (%93.2'ye kadar). **Yorum:** `entry_ok` ve yüksek-oynaklık rejimi, "kazanç" değil "büyük hareket" (her iki yönde) ile ilişkili olabilir. Bu, yön tahmininden çok risk/oynaklık filtresi olarak okunmalı — `[INFERENCE]`, doğrulanmadı.

**3) dist_52w_high — beklenmedik ters-U.** 52 haftalık zirveye yakınlık, W1'de (küçük kazananlar) en yüksek (0.870 — zirveye en yakın), sonra W2→W5 boyunca **monoton azalıyor**, W5'te (%10+ kazananlar) 0.644'e düşüyor — kayıp grubundan (W0=0.749) bile daha uzak. Yani en büyük 5 günlük kazançlar, zaten zirvede olan hisselerden değil, zirveden uzak (muhtemelen daha ucuz/daha oynak) hisselerden geliyor. `[HYPOTHESIS]` — mekanik bir etki olabilir (düşük fiyatlı/uzak hisseler yüzde olarak daha kolay büyük hareket eder), ayrıştırılmadı.

**4) mae_t5 — sağlık kontrolü, beklendiği gibi.** Kazanç arttıkça maksimum ters hareket küçülüyor (W0: -7.29, W5: -1.46) — bu büyük ölçüde tanımsal (kazanan zaten fazla düşmemiş olmalı), yeni bilgi değil ama pipeline'ın mantıklı çalıştığını doğruluyor.

**5) RVOL — en üst dilimde hafif, tutarlı lift.** RVOL'un en üst %10'luk dilimi (>1.66x) kayıp grubunda (W0) %10, orta gruplarda %7.8-8.8, ama W5'te (%10+ kazanç) %14.9'a çıkıyor (~1.5x lift). Zayıf ama yön tutarlı bir sinyal — dose-response net değil (orta bucket'larda düşüyor, sadece en uçta yükseliyor).

**6) atr_pct_real — U-şekli, W5'te en yüksek.** Control 4.53%, W1'de en düşük (3.18%), W5'te en yüksek (6.54%). Kısmen tanımsal (büyük %hareket = yüksek gerçekleşen oynaklık) ama scan-anı ATR'sinin de benzer paterni taşıyıp taşımadığı ayrı test gerektirir.

## Genel değerlendirme

Hiçbir feature (composite_score dahil) net, tek-yönlü bir "kazanan imzası" göstermiyor. En ilginç iki ipucu: (a) entry_ok/vol_regime'in yön değil oynaklık ayırt ediyor olma ihtimali, (b) büyük kazançların 52-haftalık zirveden uzak isimlerden gelmesi. İkisi de `[HYPOTHESIS]` seviyesinde — sonraki adım bunları ayrı ayrı, matched-control ile (örn. dist_52w_high'ı fiyat/likidite için kontrol ederek) derinleştirmek, yeni feature eklemeye geçmeden önce.

**Yapılmadı (kapsam dışı bırakıldı, sonraki tur):** opportunity-type kümeleme (EXP-03), rejim-katmanlama (EXP-04, gerçek sektör etiketi evrenin sadece ~%24'ünde var), extension/timing (EXP-05), false-negative (EXP-06), early-path (EXP-07).
