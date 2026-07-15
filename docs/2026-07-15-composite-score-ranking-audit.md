# FinPilot — Composite Score, Ranking ve Giriş/Çıkış Skorları Audit

**Tarih:** 2026-07-15
**Kapsam:** Composite score, raw/entry score, FinPilot score, conviction ranking, strategy selection, exit logic ve full-universe backtest
**Girdi:** `data/backtest_out/full_universe_enriched.csv`
**Audit scripti:** `composite_score_audit.py`
**Sonuç artifact'i:** `data/backtest_out/composite_score_audit.json`
**Durum:** Research-only; canlı scoring ve execution davranışı değiştirilmemiştir.

> Sert sonuç: mevcut yapı tek bir ranking sistemi değil, farklı aşamalarda çalışan birden fazla skor/etiket dilidir. Composite skor açıklanabilir bir additive formula olsa da, mevcut full-universe sonuçlarında monoton ranking edge'i kanıtlanmamıştır. Production'da ayrıca gerçek bir `exit_score` karar yüzeyi bulunmamaktadır.

## 1. Executive Summary

1. **Composite score eligibility skoru değildir.** `entry_ok` upstream hard gate'lerden sonra belirlenir; composite daha sonra hesaplanır ve esas olarak ranking, sizing ve raporlama için kullanılır.
2. **Raw score ile composite farklı sorular soruyor.** Raw score `0-3` aralığında RSI/volume/MACD confirmation'ıdır ve `entry_ok` için tam `3` gerekir. Composite score ise regime, direction, filter, alignment, momentum ve opsiyonel faktörlerin additive toplamıdır.
3. **Composite monotonic değil.** On decile için adjacent hit-rate artış oranı yalnızca **%44,4**. Composite decile hit-rate'leri `%37,77` ile `%43,86` arasında dağılır; en üst decile `%42,34` ile tabanın yalnızca sınırlı üzerindedir.
4. **Yüksek composite cutoff'ları seçici ama kırılgan.** `composite >=58` yalnızca `%6,37` coverage ve `%40,37` hit-rate verir. `>=80` `%0,20` coverage ve `%50,46` hit-rate üretir; bu küçük örnek, ranking edge'i kanıtlamaz.
5. **Entry gate işlem kalitesini göstermiyor.** Barrier testinde `entry_ok` cohort'u `PF 0,91`, expectancy `-0,184%`; tüm evren `PF 1,29`, expectancy `+0,475%`. Bu sonuç gate'in mutlaka zararlı olduğunu değil, mevcut gate'in seçtiği cohort'un execution-style testte üstün olmadığını gösterir.
6. **ATR/RVOL bileşimi hareket yakalıyor olabilir, fakat composite kanıtı değildir.** `ATR6+RVOL2` barrier cohort'u `PF 2,58` ve expectancy `+5,924%` görünür; MFE `%33,26` ve median return `-4,56%` outlier/path dependence alarmıdır.
7. **FinPilot score şu an bağımsız skor değildir.** DRL ağırlığı `0.0`; DRL yoksa FinPilot score composite pass-through'dur.
8. **Exit score yoktur.** Çıkışlar momentum tier'ına göre ATR/Yang-Zhang stop/TP ve time-exit ile yönetilir. Score decay, exit-score update loop ve exit-score telemetry yoktur.

**Go/No-Go:** Composite ağırlıklarını, `entry_ok` gate'ini veya yeni cutoff'ları production'da değiştirmek için kanıt yetersizdir. Önce canonical score contract, component telemetry, point-in-time replay ve locked OOS barrier/execution test gerekir.

## 2. Score Taxonomy

| Skor / etiket | Aralık | Gerçek anlamı | Nerede kullanılıyor |
| --- | ---: | --- | --- |
| `score` | 0–3 | RSI, volume ve rising-positive MACD confirmation sayısı | `entry_ok` hard gate'i tam `3` ister |
| `composite_score` | 0–100 | Additive recommendation strength; fixed `MAX_RECO_SCORE=16.5` ile normalize | Ranking, regime-size multiplier, summary/alert alanı |
| `finpilot_score` | 0–100 | Scanner composite + opsiyonel DRL birleşimi | DRL ağırlığı 0 olduğu için şu an composite pass-through |
| `conviction_tier` | A/B/C | Squeeze/gap/RVOL/ATR faktörlerinin env-gated etiketi | Alert/summary ranking; composite'i değiştirmez |
| `conviction_prob` | A/B/C için 0,73/0,63/0,56 | Gözlemsel tier olasılığı | Conviction ranking sıralamasında composite'ten önce gelir |
| `momentum_score` | 0–100 | Risk engine'e verilen momentum quality değeri | Sniper/Normal/Defansif strategy tag ve ATR stop/TP tier'ı |
| `exit_score` | Yok | Production'da ayrı exit decision score yok | Exit ATR stop/TP ve time-exit ile gerçekleşir |

### Decision boundary map

```text
multi-timeframe data
  -> regime + direction + raw score + liquidity + safety/earnings
  -> entry_ok
  -> composite_score / finpilot_score / risk sizing
  -> conviction and alert ranking
  -> ATR/YZ stop, TP and time-exit
```

Bu nedenle ranking ile filtering sınırı nettir: `entry_ok` kabul/red kararıdır; composite kabul edilmiş veya değerlendirmeye alınmış sinyalleri önceliklendirir. Ancak alert/summary yollarında conviction tier ayrıca birinci sıralama anahtarı olduğu için kullanıcıya tek bir canonical ranking sunulmamaktadır.

## 3. Composite Bileşen Analizi

| Bileşen | Ağırlık / etki | Ölçtüğü şey | Sorun | Production kararı |
| --- | ---: | --- | --- | --- |
| Regime | +2 | Close > EMA200 | Direction/trend ailesiyle korele; event/reversal kaçırabilir | Risk-policy olarak tut; alpha kanıtı bekle |
| Direction | +2 | Close > EMA50 | Rejimle aynı fiyat trendini tekrar ödüllendirebilir | Ayrı katkıyı ölç; hard gate olarak shadow test |
| Raw score | `0,5 x score`, max 1,5 | RSI/volume/MACD confirmation | Ayrıca `entry_ok` için tam 3 hard gate; double-counting | Confirmation bandına indirgeme adayı |
| Filter score | `1,5 x`, max 4,5 | Volume spike, price momentum, trend strength | Teorik en büyük aktif bileşen; raw volume/trend/momentum ile çakışıyor | Component ablation zorunlu |
| Alignment | `2 x` | 1h/4h/1d trend yönü | Regime/direction/trend ile aynı trend ailesi | Tek orthogonal trend component'e indir |
| Momentum ratio | 1,5/2,0/2,5 | Vol-regime göre momentum confluence | Momentum, MACD, price momentum ve alignment ile çakışıyor | Regime-aware tutmak ancak OOS ile |
| Volume spike | +0,5 | Hacim spike | Filter score ve raw volume ile tekrar sayılabilir | Tek volume temsilcisi seç |
| Price momentum | +0,5 | Pozitif z-score momentum | Momentum ratio ile örtüşür | Ayrı horizon kanıtı yoksa çıkar |
| Trend strength | +0,5 | EMA50-EMA200 gap | Regime/direction/alignment ile örtüşür | Redundant aday |
| Sentiment | ±0,5 | FinBERT sentiment | Catalyst ile aynı event bilgisini taşıyabilir | Env-gated shadow only |
| Squeeze | +1,5 optional | Short/float squeeze potential | Fundamentals eksikliği no-op yaratır; default kapalı | Production dışı, ablation sonrası |
| Catalyst | ±1,5 optional | SEC event/catalyst | Sentiment ve gap ile double-count riski | Production dışı, PIT/OOS sonrası |
| Lottery | -2 optional | MAX/IVOL/skew fade | Catalyst ile relief interaction karmaşık | Shadow only |
| Overnight gap | -1 optional | Gap reversal pressure | Gap/catalyst/momentum ile örtüşür | Shadow only |

### Kanıt durumu

Kodda bulunmak bir bileşenin edge taşıdığını kanıtlamaz. Mevcut artifact component-level `filter_score`, `alignment_ratio` ve `momentum_ratio` taşımadığı için bu bileşenlerin tek tek marginal lift'i ölçülememiştir. Bu eksiklik doğrudan auditability problemidir.

## 4. Ağırlık Analizi

### Teorik dominance

- **En yüksek kapasite:** `filter_score x1,5`, max katkı `4,5`.
- **Sonraki:** momentum ratio max `2,5`, regime `2`, direction `2`, alignment `2`.
- **Raw score:** hard gate etkisi composite içindeki `1,5` max katkısından daha büyüktür; asıl dominance eligibility aşamasındadır.
- **Opsiyonel faktörler:** squeeze `+1,5`, catalyst `±1,5`, lottery `-2`, overnight `-1`; default kapalı olmaları nedeniyle canlı default distribution'ı etkilemezler.

Bu, **theoretical weight capacity** analizidir; gerçek feature distribution ve variance olmadığı için empirical contribution değildir. En dominant üç familya: filter/momentum, trend familyası (regime-direction-alignment), ve raw score'un upstream hard-gate etkisi.

### En zayıf üç bileşen

- Tek başına +0,5 olan volume spike, price momentum ve trend strength; ancak küçük ağırlıklarına rağmen aynı bilgiyi daha büyük bileşenlerle tekrar ediyor olabilirler.
- FinPilot/DRL layer: DRL weight `0.0`, dolayısıyla bağımsız katkı yok.
- Conviction: score component değil; label/ranking key. Gözlemsel olasılıkların calibration curve'u olmadan kesin confidence gibi sunulması risklidir.

### Weight stability ve öneri

Ağırlıklar kod yorumlarında audit/backtest tarihlerine referans verse de canonical locked OOS weight registry ve contribution attribution bu yüzeyde görünmüyor. Sabit ağırlıklar ancak orthogonal feature set ve ayrı OOS kanıtı varsa korunmalı. Dinamik ağırlıklar şu aşamada daha iyi seçenek değildir; önce sabit baseline'ın replay/OOS stabilitesi kanıtlanmalıdır.

## 5. Ranking Açıklanabilirlik Durumu

### Mevcut güçlü taraf

Composite formula additive ve kaynak koddan elle hesaplanabilir. Bu black-box değildir.

### Açıklanabilirlik boşlukları

- Her satırda component contribution breakdown yok.
- `entry_ok=False` için canonical `reject_reason[]` yok.
- Alert ranking conviction probability sonra composite ile yapılıyor; composite rank ile alert rank aynı değil.
- `finpilot_score`, composite ile aynı olduğunda kullanıcıya ayrı bir skor gibi görünebilir.
- Rank 1'in rank 2'den farkı kullanıcıya normalized delta ve component driver olarak sunulmuyor.
- Sizing multiplier score bandına göre değişiyor, fakat bu bir ranking/quality score değil.

### Gerekli audit log alanları

`score_components`, `component_contributions`, `score_before_optional_factors`, `score_after_penalties`, `rank_key`, `rank_position`, `candidate_pool_size`, `reject_reason[]`, `conviction_source`, `score_timestamp`, `feature_age`, `data_quality`, `regime_at_entry`, `exit_reason`.

## 6. Score-Performance İlişkisi

### Full-universe composite deciles

| Decile | Composite aralığı | Hit-rate | Mean T+5 | Median T+5 | Lift vs base |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0–3 | %42,72 | %14,32 | %3,79 | 1,058 |
| 2 | 3–8 | %43,86 | %9,59 | %4,19 | 1,086 |
| 3 | 8–13 | %42,23 | %12,72 | %3,94 | 1,046 |
| 4 | 13–21 | %39,00 | %8,46 | %3,45 | 0,966 |
| 5 | 21–30 | %38,12 | %7,64 | %3,40 | 0,944 |
| 6 | 30–38 | %37,77 | %5,95 | %3,28 | 0,935 |
| 7 | 38–45 | %39,12 | %6,68 | %3,33 | 0,968 |
| 8 | 45–51 | %40,54 | %6,49 | %3,69 | 1,004 |
| 9 | 51–56 | %38,23 | %6,71 | %3,53 | 0,947 |
| 10 | 56–93 | %42,34 | %6,88 | %3,90 | 1,048 |

Taban favorable-mover oranı `%38,64`'tür. Skor yükseldikçe monotonic improvement yoktur. Özellikle 1–3. decile'ların 8–10. decile'larla yarışması, composite'in mevcut haliyle güvenilir quality ranking olmadığını gösterir.

### Raw score ve entry

- Raw score `0`: `%32,10` hit-rate.
- Raw score `1`: `%39,34`.
- Raw score `2`: `%39,07`.
- Raw score `3`: `%42,56`, fakat yalnızca `%4,35` coverage.
- `entry_ok=True`: `%43,13` fixed-horizon hit-rate.
- `entry_ok=False`: `%38,49`.

Entry ayrımı fixed-horizon harekette yalnızca sınırlı lift verir. Bu, gate'in execution riskini azaltmadığını ispatlamaz; yalnızca bu artifact ve hedefte güçlü ayrışma göstermediğini belirtir.

### Calibration

Composite score şu an olasılık olarak kalibre değildir. `58` veya `70` gibi skorlar doğrudan win probability anlamına gelmez. Decile hit-rate'leri ve sabit cutoff sonuçları kalibrasyon eğrisinin monoton olmadığını gösteriyor; isotonic/logistic calibration ancak locked OOS üzerinde yapılmalıdır.

## 7. Entry/Exit Score Analizi

### Entry score usefulness

Raw score entry gate'inde gerçek etkili skor benzeri yapıdır. Ancak `score==3` şartı favorable-mover recall'ını çok düşürür. Composite sonradan hesaplandığı için composite'in entry admission utility'si yoktur; yalnızca kabul edilen/raporlanan satırları sıralar veya sizing'i etkiler.

### Exit score usefulness

Production'da ayrı `exit_score` yoktur. Exit behavior:

- momentum tier'ına göre stop/TP multiplier seçimi,
- ATR veya Yang-Zhang volatility ile fiyat seviyeleri,
- research barrier'da TP-first / SL-first / time exit,
- aynı bar TP ve SL durumunda stop-first konservatif kural.

Bu nedenle exit score usefulness ölçülemez. Exit kararının skora bağlı olduğunu söylemek yanlış olur. Score decay, trade boyunca exit score güncellemesi, score aging ve “entry high / exit low” state machine'i bulunmamaktadır.

### Strategy selection

`momentum_score >=70` Sniper, `<50` Defansif, `50–69` Normal strateji tag'ini seçer. Bu değer composite recommendation score ile kavramsal olarak benzer olsa da ayrı risk-engine input'udur; entry/exit skor contract'ı değildir.

## 8. Redundancy ve Double-Counting

| Redundant aile | Çakışan bilgiler | Risk | Sadeleştirme |
| --- | --- | --- | --- |
| Trend | regime, direction, trend_strength, EMA gap, alignment | Aynı bullish state birkaç kez ödüllenir | Tek trend state + bir orthogonal alignment feature |
| Momentum | raw MACD, price_momentum, momentum_ratio, confluence | Fiyat hareketi farklı isimlerle tekrar sayılır | Horizon bazlı tek momentum familyası |
| Volume | raw volume x1,2, volume_spike, RVOL | Aynı hacim patlaması score'u şişirir | RVOL veya normalized volume tek temsilci |
| Event | catalyst, sentiment, overnight gap, squeeze | Aynı event continuation birden fazla boost alır | Event source'larını ayrı report, tek calibrated factor |
| Score vocabularies | raw score, composite, finpilot, conviction | Kullanıcıda çoklu “kalite” algısı yaratır | Bir canonical rank + ayrı risk/label alanları |

Redundant feature'ların gerçek etkisi component-level artifact eksikliği nedeniyle doğrudan ablate edilememiştir; bu da P0 telemetry ihtiyacını güçlendirir.

## 9. Overfit ve Calibration Riskleri

- `MAX_RECO_SCORE=16.5` ve high-score threshold `58`, eski score ceiling ve percentile davranışını korumak üzere ayarlanmıştır; yeni OOS edge kanıtı değildir.
- Bear boost `30–55`, high-score suppression `>58` ve Bull/Bear multiplier'ları geçmiş audit segmentlerine dayanır; regime drift riski vardır.
- Optional factor weights `+1,5/-2/+1` çok sayıda ablation ve threshold seçimi sonrası oluştuğu için selection bias riski taşır.
- Composite score decile monotonicity düşük olduğu için score cutoff hacking şüphesi vardır.
- En yüksek cutoff'larda küçük n bulunur: `composite>=80` yalnızca 109 satırdır.
- Aynı symbol/date tekrarları bağımsız gözlem sayılamaz; cluster bootstrap veya symbol-day dedup gerekir.
- T+5 favorable movement ile execution P&L aynı değildir; barrier'da median returns negatifken mean expectancy pozitif görülebilir.

## 10. Backtest Sonuçları

### Fixed-horizon ranking

Full universe: 53.859 satır, 1.932 unique symbol, 66 scan date. Composite decile'ları monotonic değil; yüksek skor bucket'ları orta bucket'lardan güvenilir biçimde ayrışmıyor.

### Execution-style barrier test

Config: `TP=1.5xATR`, `SL=0.75xATR`, horizon `3d`, stop-first same-bar tie.

| Cohort | n | Win-rate | Expectancy | Median | PF | MFE | MAE | Avg bars |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| All | 46.644 | %44,81 | %0,475 | -%0,50 | 1,29 | %5,20 | -%3,18 | 2,15 |
| `entry_ok` | 1.683 | %39,16 | -%0,184 | -%1,89 | 0,91 | %3,95 | -%3,87 | 2,01 |
| `ATR>=4` | 20.770 | %43,52 | %0,651 | -%1,73 | 1,25 | %8,45 | -%4,86 | 2,18 |
| `ATR>=6` | 10.385 | %41,57 | %0,684 | -%2,76 | 1,20 | %12,08 | -%6,25 | 2,22 |
| `ATR6+entry_ok` | 368 | %30,71 | -%1,448 | -%4,98 | 0,66 | %6,29 | -%7,39 | 1,78 |
| `ATR6+RVOL2` | 1.032 | %41,76 | %5,924 | -%4,56 | 2,58 | %33,26 | -%7,83 | 1,93 |

`ATR6+RVOL2` sonucu güçlü görünür fakat mean/median ayrışması, yüksek MFE ve negatif median/outcome path'i outlier ve barrier sensitivity alarmıdır. Bu sonuç composite score'un başarısı değil, ayrı bir research interaction sonucudur.

### Metrik boşlukları

Mevcut full-universe CSV score ile MFE, MAE ve hold-time'ı aynı satırda taşımıyor. Barrier grid aggregate sonuç veriyor fakat composite-score predicate'leri yok. Bu nedenle score-vs-MFE/MAE/hold-time ve score-specific cost-adjusted PF henüz tam test edilmemiştir.

## 11. Cutoff ve Threshold Önerileri

| Cutoff | Gözlem | Karar |
| --- | --- | --- |
| `score ==3` | %4,35 coverage, %42,56 hit-rate | Hard BUY gate olarak değil confirmation bandı olarak shadow test |
| `composite >=58` | %6,37 coverage, %40,37 hit-rate | Quality cutoff olarak kanıtlanmadı |
| `composite >=70` | %1,07 coverage, %43,77 hit-rate | Küçük/fragile; production cutoff değil |
| `composite >=80` | %0,20 coverage, %50,46 hit-rate | n=109; overfit riski yüksek |
| Conviction A/B/C | Label/ranking | Olasılık calibration ve OOS olmadan confidence cutoff değil |
| Exit cutoff | Yok | Yeni exit score icat edilmemeli; önce lifecycle telemetry |

Sabit cutoff yerine quantile/adaptive cutoff ancak önce score'un OOS'ta monotonic veya en azından stable rank separation gösterdiği kanıtlanırsa test edilmelidir. Şu anda adaptive cutoff, zayıf baseline'ı gizleme riski taşır.

## 12. Yeniden Tasarım Planı

### Canonical score contract

1. `entry_eligibility`: hard safety/risk gates.
2. `entry_quality_score`: orthogonal, calibrated alpha components.
3. `rank_score`: candidate ordering için tek canonical score.
4. `risk_score`: position sizing/volatility için ayrı alan.
5. `exit_state`: score değil, lifecycle state machine; `hold`, `reduce`, `exit` gerekçesi.

### Sadeleştirilmiş v1 adayı

- Trend: regime + direction + alignment yerine tek calibrated trend familyası.
- Momentum: raw MACD/price momentum/momentum ratio/confluence yerine horizon-aware tek momentum familyası.
- Volume: raw volume ve volume spike yerine normalized RVOL tek temsilci.
- Event: catalyst/sentiment/gap/squeeze ayrı source fields; calibrated event contribution yalnızca OOS kanıtı varsa.
- Composite: contribution breakdown ve feature age ile birlikte loglanmalı.
- Exit: ATR/YZ stop/TP mevcut risk policy olarak kalmalı; ayrı exit score ancak trade lifecycle verisi toplandıktan sonra.

### Önerilerin production suitability'si

| Öneri | Etki | Risk | Zorluk | Production |
| --- | --- | --- | --- | --- |
| Component/reject telemetry | Çok yüksek auditability | Düşük | Orta | Hemen |
| Redundancy reduction | Score compression ve double-counting azalır | Alpha kaybı olabilir | Orta | Shadow first |
| Raw score soft confirmation | Recall artabilir | False positive artabilir | Orta | OOS/shadow |
| Quantile rank | Universe drift'e uyum | Calibration değişebilir | Orta | Sonra |
| Learned ranker | Nonlinear interaction | Overfit/leakage | Yüksek | En son |
| Exit score | Lifecycle ayrımı | Karmaşıklık ve yanlış timing | Yüksek | Telemetry sonrası |

## 13. P0 / P1 / P2 / P3 Aksiyon Listesi

### P0

- Her output row için `score_components`, `component_contributions` ve `reject_reason[]` logla.
- Tek canonical ranking contract belirle; conviction/composite/FinPilot sıralama önceliğini açıkça standardize et.
- Production point-in-time replay ile CSV `entry_ok` drift'ini çöz.
- Full-universe score rows'a MFE, MAE, barrier label, exit reason ve bars-to-exit ekle.

### P1

- Trend, momentum ve volume redundancy için component ablation çalıştır.
- Composite decile/top-N backtestini locked OOS ve symbol-day clustered bootstrap ile çalıştır.
- `score==3` hard gate'i strict/balanced/event shadow modlarında karşılaştır.
- Alert ranking'de conviction-first ve composite-first politikalarını aynı sample'da test et.

### P2

- Score calibration curve ve confidence interval üret.
- Regime-specific rank stability ve cutoff sensitivity ölç.
- Score freshness/decay modelini trade lifecycle verisiyle test et.
- Composite predicates'lerini barrier engine'e ekleyerek score-specific PF, MFE, MAE, hold-time hesapla.

### P3

- Ancak additive baseline stabil olduktan sonra learned ranker veya canlı DRL weighting değerlendir.
- Kullanılmayan/aynı anlamı taşıyan score vocabulary'lerini retire et.
- Exit score ancak ayrı, zaman içinde güncellenen ve outcome ile doğrulanmış bir state contract olarak tasarla.

## 14. Kanıt Sınıflandırması

**Kanıtlandı:** Composite decile ranking monotonic değil; `entry_ok` fixed-horizon ve mevcut barrier config'inde üstün değil; FinPilot score DRL kapalıyken composite pass-through; production exit score yok.
**Güçlü hipotez:** Trend, momentum ve volume ailelerinde double-counting composite'i şişiriyor; raw score hard gate olarak fazla sert olabilir.
**Kanıtlanmadı:** Composite'in cost-adjusted alpha ürettiği; yüksek composite cutoff'larının OOS'ta stabil olduğu; `ATR6+RVOL2` sonucunun composite/ranking edge'i olduğu; ayrı bir exit score'un mevcut stratejiyi iyileştireceği.
