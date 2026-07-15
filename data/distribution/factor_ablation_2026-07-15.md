# Factor Ablation — last 14 days

_Baseline (all signals): n=249 · hit-rate=6% · expectancy=-1.10%_

| Faktör | yön | n_hi | n_lo | hi bek. | lo bek. | fark | katkı? |
|---|---|---|---|---|---|---|---|
| composite_score | edge | 0 | 249 | +0.00% | -1.10% | +1.10% | — |
| squeeze_factor | edge | 1 | 248 | -3.27% | -1.09% | -2.17% | hayır |
| catalyst_factor | edge | 0 | 249 | +0.00% | -1.10% | +1.10% | — |
| contraction_factor | edge | 55 | 194 | -0.73% | -1.21% | +0.47% | hayır |
| rvol_acceleration | edge | 16 | 233 | -2.85% | -0.98% | -1.87% | hayır |
| sentiment | edge | 0 | 249 | +0.00% | -1.10% | +1.10% | — |
| news_sentiment | edge | 164 | 85 | -1.61% | -0.12% | -1.49% | hayır |
| conviction_prob | edge | 0 | 249 | +0.00% | -1.10% | +1.10% | — |
| lottery_factor | fade | 52 | 197 | -1.21% | -1.07% | -0.14% | hayır |
| overnight_gap_factor | fade | 5 | 244 | -0.62% | -1.11% | +0.49% | hayır |

# By early-detection tier

_n=249 · TP=0.1 · SL=0.05 · horizon=10_

| Grup | n | TP% | SL% | Time% | Ort.Getiri | Beklenti |
|---|---|---|---|---|---|---|
| TÜMÜ | 249 | 6% | 32% | 62% | -1.10% | -1.10% |
| CONFIRM | 14 | 7% | 57% | 36% | -1.44% | -1.44% |
| NONE | 176 | 8% | 35% | 57% | -1.10% | -1.10% |
| SETUP | 4 | 0% | 100% | 0% | -5.00% | -5.00% |
| WATCH | 55 | 0% | 9% | 91% | -0.73% | -0.73% |

_Post-cost note: apply ~0.55% round-trip (RealisticBacktestCosts) to expectancy before trusting any factor. A 'helps=EVET' on <~30/bucket is noise._
