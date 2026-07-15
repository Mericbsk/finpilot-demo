# FinPilot — Filtre Eşikleri ve False-Negative Audit

**Tarih:** 2026-07-15
**Kapsam:** Production scanner eşikleri, threshold sensitivity, favorable-move recall ve reddedilen güçlü setup kohortları
**Girdi:** `data/backtest_out/full_universe_enriched.csv`
**Audit scripti:** `threshold_false_negative_audit.py`
**Sonuç artifact'i:** `data/backtest_out/threshold_false_negative_audit.json`
**Durum:** Research-only; canlı scanner davranışı değiştirilmemiştir.

> Bu raporda “false negative”, `resolved_pct_t5 >= 5%` hareket hedefini sağlayan fakat `entry_ok=False` olan gözlemdir. Bu, otomatik olarak kârlı bir işlemin kaçırıldığı anlamına gelmez; spread, slippage, fill, stop/TP yolu ve corporate-action kalitesi bu artifact'te ölçülmemiştir.

## 1. Yönetici Özeti

1. Full-universe artifact'te **53.859** gözlem ve **20.811** favorable mover vardır; taban oranı **%38,64**.
2. Favorable mover'ların **20.067'si (`%96,42`) `entry_ok=False`** durumundadır. Bu hedefe göre canlı gate recall'i yaklaşık **%3,58**'dir. Bu güçlü bir recall alarmıdır; fakat üretim replay'i ile birebir eşleştiği kanıtlanmadan doğrudan canlı davranış teşhisi olarak okunmamalıdır.
3. En sert görünen proxy, **raw score >=3**: bu eşik yalnızca **%4,35 coverage** ve **%4,80 favorable-mover recall** üretir. `score >=3` seçiminin hit-rate'i **%42,56** olsa da, olumlu hareketlerin çoğunu dışarıda bırakır.
4. **ATR >=6** hareket yakalama açısından belirgindir: **%22,74 coverage**, **%59,60 hit-rate**, **%35,08 recall**. Bu, ATR'nin hareket filtresi olabileceğini gösterir; maliyet-sonrası işlem edge'i göstermez.
5. **Gap >=3**: **%5,99 coverage**, **%55,03 hit-rate**, **%8,52 recall**. **RVOL >=2**: **%7,97 coverage**, **%44,79 hit-rate**, **%9,24 recall**. Eşikler seçicidir ancak recall düşüktür.
6. `ATR>=6 AND RVOL>=2` ve `ATR>=6 AND gap>=3` bileşimleri reddedilmiş favorable mover'lar içinde sırasıyla **771** ve **1.038** gözlem içerir. Bunlar güçlü bir araştırma kohortudur; production gate önerisi değildir.
7. Sonuç: yeni ATR/RVOL/gap gate'i eklenmemeli. Önce production replay, point-in-time veri doğrulaması, symbol-day clustered OOS test ve maliyetli barrier/execution backtest yapılmalıdır.

## 2. Eşik Envanteri

### 2.1 Production hard gates

| Eşik / kural | Kod yüzeyi | Durum | False-negative riski |
|---|---|---|---|
| Veri geçmişi: 15m >=15, 1h >=10, 4h >=15, 1d >=50 | `scanner/evaluate.py` | Enforced | Yeni listelenen veya veri eksik semboller |
| Rejim: daily close > EMA200; kısa geçmişte fallback | `scanner/evaluate.py` | Enforced | Erken breakout, reversal, event-driven hareket |
| Direction: daily close > EMA50 | `scanner/evaluate.py` | Enforced | EMA hizalanmadan başlayan hareket |
| Raw score: RSI 30–70 + volume > median x1,2 + rising positive MACD; `entry_ok` score == 3 ister | `scanner/evaluate.py` | Enforced, fixed | Sıcak momentum, RSI >70, iki-of-üç setup |
| Fiyat >= $2,00 | `scanner/evaluate.py`, `scanner/config.py` | Enforced | Düşük fiyatlı ama likit/asimetrik setup |
| 10-day average volume >=300.000 share | `scanner/evaluate.py`, `scanner/config.py` | Enforced | Share-volume dollar liquidity ve spread'i ölçmez |
| Earnings blackout: -2/+1 gün | `scanner/evaluate.py`, `scanner/earnings_blackout.py` | Enforced when lookup succeeds | Earnings sonrası continuation; operasyonel risk kontrolüdür |
| Günlük drawdown >=%3 | `scanner/risk_engine.py`, `scanner/evaluate.py` | Enforced, state yoksa fail-open | Günlük fırsatları bilinçli olarak kapatır; alpha eşiği değildir |

### 2.2 Production scoring/reporting eşikleri

| Eşik | Değer | Gerçek etkisi |
|---|---:|---|
| Volume spike | 1,5x | Feature/composite; `entry_ok` gate'i değil |
| Momentum z base | 1,5 | Adaptive feature; segment/dynamic katmanı ile 1,1–3,0 aralığı |
| Liquidity momentum segmenti | high 2,0; mid 1,6; low 1,4 | Momentum feature'ı; doğrudan entry gate değil |
| Timeframe alignment | >=0,67 | Feature çıktısı; config'teki `min_alignment_ratio` entry kararında uygulanmıyor |
| Momentum confluence | >=0,50 | Feature çıktısı; entry gate değil |
| Composite high-score bandı | >58 | Regime x position-size suppression; entry cutoff değil |
| Bear boost bandı | 30–55 | Position sizing multiplier; entry eligibility değil |

### 2.3 Optional feature thresholds

- Squeeze pivotleri: short interest `%20`, float `50M`; env-gated.
- Conviction: short güçlü `squeeze_factor >=0,5`, gap güçlü `>=0,6`, gap mevcut `>=0,2`, RVOL mevcut `>=0,25`, ATR mevcut `>=4%`; env-gated label, score'u değiştirmez.
- Catalyst, lottery fade, overnight gap ve squeeze composite katkıları env-gated'dir; default kapalı olduklarında production entry gate'i değildir.

### 2.4 Research-only threshold'lar

`ATR >=4 OR gap >=3 OR RVOL >=2` strict gate proxy'si, A/B/C conviction tier kuralları, `ATR>=6`, `RVOL>=2`, `gap>=3` ve composite threshold sweeps backtest/research yüzeyindedir. Bunlar canlı scanner kuralı olarak kabul edilmemelidir.

## 3. Threshold Sensitivity

| Proxy | Threshold | Coverage | Hit-rate (`T+5 >=5%`) | Favorable-mover recall |
|---|---:|---:|---:|---:|
| Price | >=2 | %89,39 | %37,22 | %86,09 |
| Raw score | >=3 | %4,35 | %42,56 | %4,80 |
| ATR | >=4 | %44,96 | %55,78 | %64,90 |
| ATR | >=6 | %22,74 | %59,60 | %35,08 |
| ATR | >=10 | %6,31 | %60,44 | %9,88 |
| Gap | >=1 | %21,25 | %48,66 | %26,77 |
| Gap | >=3 | %5,99 | %55,03 | %8,52 |
| RVOL | >=1,5 | %16,79 | %42,80 | %18,59 |
| RVOL | >=2 | %7,97 | %44,79 | %9,24 |
| Squeeze | >=0,5 | %4,48 | %50,75 | %5,89 |

Bu tablo “en yüksek hit-rate en iyi eşiktir” şeklinde yorumlanmamalıdır. Örneğin ATR>=10 hit-rate'i ATR>=6'dan biraz yüksek olsa da favorable movers'ın yalnızca %9,88'ini yakalar. Eşik seçimi precision, recall, günlük kapasite ve execution P&L birlikte değerlendirilerek yapılmalıdır.

## 4. False-Negative Kohortları

| Reddedilen favorable-mover kohortu | Gözlem | Tüm favorable mover'lara payı |
|---|---:|---:|
| `entry_ok=False` | 20.067 | %96,42 |
| Rejim proxy'si false | 10.465 | %50,29 |
| Direction proxy'si false | 9.980 | %47,96 |
| Raw score <3 | 19.813 | %95,20 |
| Liquidity proxy'si false | 11.863 | %56,99 |
| ATR>=6 ve entry reddedilmiş | 7.049 | %33,87 |
| Gap>=3 ve entry reddedilmiş | 1.663 | %7,99 |
| RVOL>=2 ve entry reddedilmiş | 1.816 | %8,73 |
| ATR>=6 ve (gap>=3 veya RVOL>=2), entry reddedilmiş | 1.612 | %7,75 |

Bu kohortlar örtüşebilir; yüzdeler toplanmamalıdır. CSV'de her reddin tam ara nedenleri bulunmadığı için rejim, direction, score ve liquidity atıfları **proxy** niteliğindedir.

## 5. Kaba Filtreler: Güvenli mi, Kör mü?

- **Rejim ve direction:** Bunlar risk-policy olarak anlaşılır; favorable-movement hedefinde rejim kohortu tabandan iyi değildir. Event-driven continuation, reversal ve short-covering setup'larını dışlayabilir.
- **Price/volume:** Spread, dollar volume, ADV, market impact ve halt davranışı yoktur. Bu nedenle güvenli liquidity filtresi oldukları kanıtlanmamıştır.
- **Earnings blackout:** Operasyonel risk azaltır; alpha filtresi olarak sınıflandırılmamalıdır. Earnings sonrası hareketleri ayrıca ölçmek gerekir.
- **Raw score ==3:** En büyük recall alarmıdır. “Gerekli ama yeterli değil” confirmation olarak ayrı raporlanması, tek başına BUY gate olmaktan daha savunulabilirdir.

## 6. Dar Filtrelerin Dışladığı Setup'lar

1. RSI 70 üzerindeyken devam eden catalyst/momentum.
2. EMA50 veya EMA200 hizalanmadan başlayan breakout.
3. Reversal ve short-covering.
4. Düşük fiyatlı fakat gerçek dollar-liquidity'si yüksek semboller.
5. Yüksek ATR ile gelen expansion; risk boyutlandırma gerektirir, otomatik ret gerektirmeyebilir.
6. Earnings sonrası continuation.

## 7. Heuristik ve Overfit Riski

- `30–70 RSI`, `1,2x volume`, `$2`, `300k share volume`, fixed EMA gates ve `score==3` için veri içinden seçilmiş OOS kilidi görünmüyor.
- ATR/gap/RVOL taramaları aynı artifact üzerinde keşif ve değerlendirme olarak kullanılıyor; multiple-testing bias vardır.
- `T+5 >=5%` favorable move, maliyet-sonrası kârlılık değildir.
- Aynı symbol-day için tekrarlı taramalar bağımlılık yaratabilir; clustered inference gerekir.
- ATR sonucu corporate-action/outlier duyarlılığı taşıyabilir; ATR cap ve data-quality filtresi olmadan production kararı verilmemeli.

## 8. Ranking ve Threshold Birlikte Okuması

Composite score `entry_ok` sonrasında hesaplanan additive bir ranking yüzeyidir; entry eligibility ile karıştırılmamalıdır. Config'te bulunan `min_alignment_ratio`, `min_momentum_ratio` ve `min_filter_score` değerlerinin canlı `entry_ok` kararına beklenen biçimde bağlanmadığı önceki test/audit çalışmasında görülmüştür. Bu drift düzeltilmeden yeni threshold kalibrasyonu yanlış karar yüzeyinde yapılır.

## 9. Önerilen Recalibration

### P0: Önce ölçüm sözleşmesi

1. Production replay ile aynı timestamp'te aynı input'u kullan.
2. Her satırda `reject_reason[]` alanını yaz: history, regime, direction, raw_score component, price, avg_volume, earnings, market safety.
3. `min_*` config alanlarının gerçekten gate'e bağlandığını aktivasyon testleriyle doğrula.
4. Symbol-day dedup ve clustered confidence interval üret.

### P1: Recall koruyan gate tasarımı

1. Raw score'u hard gate yerine confirmation/quality bandı olarak test et.
2. Rejim ve direction için `strict`, `balanced`, `event` modlarını shadow-mode karşılaştır.
3. Price/share-volume yerine dollar ADV, spread ve estimated impact kullan.
4. Earnings blackout'u `suppress`, `size_down`, `post-earnings` modlarına ayır.

### P2: ATR/gap/RVOL araştırması

1. `ATR>=4/6`, `gap>=1/3`, `RVOL>=1,5/2` eşiklerini locked OOS'ta test et.
2. Her eşik için precision, recall, daily signal count, cost-adjusted expectancy, stop/TP path ve max drawdown raporla.
3. `ATR>=6 + RVOL>=2` ve `ATR>=6 + gap>=3` bileşimlerini interaction modeliyle doğrula; sabit gate olarak değil.
4. High-ATR outlier ve corporate-action kayıtlarını ayrı raporla.

## 10. Sonuç ve Go/No-Go

**Go:** Threshold sensitivity ve false-negative audit pipeline'ı araştırma için hazır; mevcut artifact üzerinden sonuçlar tekrar üretilebiliyor.
**No-Go:** Yeni ATR/RVOL/gap hard gate'i, raw score gevşetmesi veya composite weight değişikliği için henüz yeterli kanıt yok.
**Şartlı sonraki adım:** Production replay + reject reason telemetry + locked OOS execution backtest + shadow mode.

## 11. Kanıt Sınıflandırması

- **Kanıtlandı:** Artifact'te `entry_ok=False` favorable movers çoğunlukta; raw score>=3 ve ATR/gap/RVOL eşikleri coverage-recall tradeoff'u yaratıyor.
- **Güçlü hipotez:** Raw score, regime ve direction alpha gate'i olarak gereğinden sert olabilir.
- **Kanıtlanmadı:** Bu eşiklerin maliyet-sonrası kârlı işlemleri doğrudan kaçırdığı; ATR/gap/RVOL compound alpha olduğu; herhangi bir yeni production threshold'un OOS'ta stabil kalacağı.
