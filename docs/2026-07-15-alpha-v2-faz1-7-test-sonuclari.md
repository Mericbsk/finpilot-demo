# Alpha V2 Faz 1-7 Test Sonuclari

**Tarih:** 2026-07-15
**Durum:** Research-only. Production score, gate veya risk ayari degistirilmedi.

## 1. Kisa Cevap

Evet, Alpha V2 daha once tam olarak test edilmemisti.

Daha onceki calismalar iki farkli seyi birbirine karistiriyordu:

1. `score_compare.py`, 6.410 satirlik `enriched_signals_v3.csv` uzerinde Alpha V2 adiyla yazilmis offline formulu test ediyordu.
2. Yeni Faz 1-7 runner ise `full_universe_enriched.csv` icindeki mevcut ATR/RVOL/gap/composite alanlarini test ediyordu; Alpha V2 bayragini acip production V2 profilini calistirmiyordu.

Bu iki calisma production Alpha V2 replay'i degildi.

## 2. Alpha V2 Kod Kontrolu

### 2.1 Bayrak gercekten neyi aciyor?

`FINPILOT_ENABLE_ALPHA_V2=1` su alanlarda etkili:

- squeeze factor short/float agirligini `70/30` yapar;
- `risk_engine.calculate_risk_management()` icinde stop'u en fazla `1.5x ATR` yapar;
- primary TP2'yi en az `5.0x ATR` yapar.

Sentetik kontrol:

| Momentum score | V2 kapali | V2 acik |
|---:|---|---|
| 40 | stop `2.5x`, TP `6.5x` | stop `1.5x`, TP `6.5x` |
| 60 | stop `2.0x`, TP `5.5x` | stop `1.5x`, TP `5.5x` |
| 70 | stop `1.5x`, TP `5.0x` | stop `1.5x`, TP `5.0x` |

### 2.2 Kritik wiring bulgusu

`features.py` icinde Alpha V2 icin `compute_gap_factor`, `compute_rvol_factor` ve `compute_extension_factor` mevcut. Fakat `evaluate.py` icindeki `get_alpha_features()` cagrisi ve composite row construction bu uc faktoru `score_engine.compute_recommendation_score()` icine aktarmiyor.

Dolayisiyla V2'nin dokumante edilen offline formulu:

$$
4 \times short_n + 3 \times atr_n + 3 \times gap_n + 2 \times rvol_n - 1.5 \times extension_n
$$

mevcut production `composite_score` ile ayni sey degil.

Sentetik score kontrolu: ayni composite row icin Alpha V2 bayragi kapali/acik `94 -> 94`; yani flag composite skorunu degistirmiyor. Bu, gap/RVOL/extension katmaninin production score yoluna baglanmadigini gosteriyor.

## 3. Kullanilan V2 Test Runner

Yeni runner:

- `alpha_v2_research_runner.py`
- cikti: `data/backtest_out/alpha_v2/alpha_v2_results.json`
- barrier input: `data/backtest_out/alpha_v2/alpha_v2_barrier_input.csv`
- combination cikti: `data/backtest_out/alpha_v2/constrained_combinations.csv`

Kaynak artifact:

- `data/backtest_out/enriched_signals_v3.csv`
- 6.410 satir
- 1.216 sembol
- 53 tarih
- 4.680 canonical symbol-day
- 1.730 duplicate satir

V2 score source:

- `short_pit`, yoksa `short_pct`
- `atr_pct`
- `gap_pct`
- `rvol`
- `dist_52w_high`

Top-%20/top-%10 score kesmeleri locked OOS leakage olmamasi icin discovery doneminden hesaplandi:

- top-%20 cutoff: `34.0708 / 100`
- top-%10 cutoff: `47.2291 / 100`
- normalization: offline V2 score `/ 12 × 100`

Temporal split:

- discovery sonu: `2026-04-17`
- validation sonu: `2026-05-21`
- locked OOS baslangici: `2026-05-22`

## 4. Forward T+5 V2 Sonuclari

Baseline maliyet `%0.55` dusulmustur. Bu tablo execution P&L degildir.

| V2 factor | n | Coverage | Hit-rate | Mean net T+5 | Median net T+5 | PF |
|---|---:|---:|---:|---:|---:|---:|
| V2 score top-%20 | 1.161 | `%24.81` | `%54.26` | `%8.37` | `%5.30` | `6.50` |
| V2 score top-%10 | 590 | `%12.61` | `%57.29` | `%9.98` | `%6.36` | `7.10` |
| short `>=15` | 455 | `%9.72` | `%53.63` | `%10.19` | `%5.19` | `9.82` |
| ATR `>=6` | 595 | `%12.71` | `%58.99` | `%17.67` | `%6.53` | `8.31` |
| gap `>=3` | 241 | `%5.15` | `%54.77` | `%7.00` | `%5.55` | `4.77` |
| RVOL `>=2` | 359 | `%7.67` | `%39.28` | `%6.47` | `%2.69` | `5.60` |

Forward sonuclarda max drawdown bircok cohort'ta `-%100` seviyesine geliyor. Bu nedenle mean/PF yuksekligi tek basina kabul edilmedi.

## 5. Execution-Style Barrier

Barrier konfigurasyonu:

- TP `2x ATR`
- SL `1x ATR`
- horizon `3/5` gun
- max entry drift `%50`
- ATR cap `%100`
- baseline round-trip cost `%0.55`
- stop-first same-bar tie

### 5.1 Genis V2 OOS: 2026-01-01 sonrasi

Artifact: `data/backtest_out/alpha_v2/barrier/`

| Cohort | n | Gross exp. | Cost-adjusted exp. | Median | PF |
|---|---:|---:|---:|---:|---:|
| All | 4.198 | `-%0.059` | `-%0.609` | `-%2.448` | `0.98` |
| V2 score `>=34` | 1.558 | `%0.551` | `%0.001` | `-%3.723` | `1.16` |
| V2 score `>=47` | 712 | `%1.394` | `%0.844` | `-%3.320` | `1.41` |
| gap `>3` | 226 | `%1.428` | `%0.878` | `-%0.634` | `1.54` |
| ATR6+RVOL2 | 83 | `%0.701` | `%0.151` | `-%6.317` | `1.15` |

### 5.2 Locked OOS: 2026-05-22 sonrasi

Artifact: `data/backtest_out/alpha_v2/barrier_locked_oos/`

| Cohort | n | Gross exp. | Cost-adjusted exp. | Median | PF |
|---|---:|---:|---:|---:|---:|
| All | 301 | `%0.050` | `-%0.501` | `-%1.910` | `1.02` |
| V2 score `>=34` | 127 | `-%0.408` | `-%0.958` | `-%3.941` | `0.90` |
| V2 score `>=47` | 77 | `%0.199` | `-%0.351` | `-%3.859` | `1.05` |
| gap `>3` | 29 | `-%1.676` | `-%2.226` | `-%5.547` | `0.59` |
| ATR6+RVOL2 | 12 | `-%1.152` | `-%1.702` | `-%6.197` | `0.80` |

Locked OOS'ta V2 score kesmeleri maliyet sonrasi negatif veya sifira cok yakin. `ATR6+RVOL2` de bu V2 kohortunda negatif ve n=12 ile yetersizdir.

## 6. Faz Durumu

| Faz | Alpha V2 durumu |
|---|---|
| Faz 1 replay | Partial. V2 input artifact'i var; production V2 component/reject telemetry yok |
| Faz 2 quality | Partial. Canonicalization ve ATR cap var; corporate action/spread/ADV yok |
| Faz 3 thresholds | Forward ve barrier threshold testleri tamamlandi |
| Faz 4 combinations | Family-constrained 2-5 combination taramasi tamamlandi; bootstrap/FDR yok |
| Faz 5 4-6 combinations | Exploratory; locked OOS gate gecilmedi |
| Faz 6 costs | `%0.55` post-hoc barrier expectancy subtraction var; spread/impact yok |
| Faz 7 locked OOS | Calisti; V2 score ve ATR/RVOL adaylari maliyet sonrasi pozitif kalmadi |

## 7. Nihai Karar

Alpha V2'nin offline factor fikri forward T+5 tablosunda secicilik gosteriyor. Ancak:

1. Bu offline formul production `composite_score` ile ayni implementasyon degil.
2. Alpha V2 bayragi production composite'i degistirmiyor.
3. Locked execution OOS'ta V2 score top-%20 ve top-%10 maliyet sonrasi negatif.
4. ATR6+RVOL2 V2 locked OOS'ta negatif ve kucuk-n.
5. Production V2 risk override'i yalnizca stop davranisini degistiriyor; 70+ sniper tier'inda etkisi zaten yok.
6. Corporate action, spread, dollar ADV, impact ve point-in-time component telemetry eksik.

**Karar: Alpha V2 icin de production NO-GO.**

Alpha V2 acilacaksa once iki ayri is yapilmali:

- V2 gap/RVOL/extension/short formulu production score yoluna acikca baglanmali veya bu faktorlerin yalnizca research oldugu belgelenmeli.
- Bu wiring sonrasinda yeni production artifact'i ile Faz 1-7 replay yeniden uretilmeli; mevcut `enriched_signals_v3.csv` sonucu production V2 kaniti sayilmamali.

Canliya alinabilecek bir Alpha V2 threshold, weight veya stop/TP degisikligi bu testten cikmadi.
