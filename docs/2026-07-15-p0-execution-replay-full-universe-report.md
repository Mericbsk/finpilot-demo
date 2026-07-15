# P0 Full-Universe Execution Replay

## Kapsam

Bu rapor `--universe all` ile calistirildi. Her kaynak kendi tum canonical symbol-day evreninde replay edildi; kaynak evrenleri ayni olmadigi icin bu sonuc adil A/B karsilastirmasi degil, iki artifact'in tam-kapsamli execution sonucudur.

- Legacy: 27,386 canonical symbol-day, 66 tarih
- V2: 4,680 canonical symbol-day, 53 tarih
- Ortak kesişim: 2,315 symbol-day, 650 sembol, 38 tarih
- Discovery: `<= 2026-04-17`
- Validation: `2026-04-18..2026-05-21`
- Locked OOS: `> 2026-05-21`
- Horizon: 5 bar
- Slippage: 5 bps each side
- Commission: 5 bps each side
- Notional: `$1,000`

Tum canonical symbol-day satirlari replay edildi. Yalnizca locked OOS'ta score ve veri kontrollerini gecen sinyaller trade edildi:

| Source | Replayed symbol-days | Dates | Discovery | Validation | Locked OOS | Selected trades | Selected dates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Legacy | 27,386 | 66 | 3,232 | 10,235 | 13,919 | 901 | 21 |
| V2 | 4,680 | 53 | 3,341 | 964 | 375 | 62 | 10 |

## Strategy-specific exit sonucu

Legacy `TP=2x/SL=1x ATR`, V2 `TP=5x/SL=1.5x ATR` kullanir:

| Source | N | Net expectancy | Net total P&L | Profit factor | Max drawdown |
| --- | ---: | ---: | ---: | ---: | ---: |
| Legacy | 901 | 2.0968% | $18,892.11 | 1.7778 | -589.16% |
| V2 | 62 | -0.0046% | -$2.84 | 0.9993 | -217.45% |

## V2 exit sensitivity

Ayni full V2 evreninde `n=62` trade:

| TP / SL | Net expectancy | Profit factor | Max drawdown |
| --- | ---: | ---: | ---: |
| `2x / 1x` | -0.3535% | 0.9242 | -150.57% |
| `3x / 1x` | 0.7894% | 1.1669 | -144.68% |
| `3x / 1.5x` | -1.2652% | 0.8135 | -247.39% |
| `5x / 1x` | 2.0501% | 1.4284 | -141.95% |
| `5x / 1.5x` | -0.0046% | 0.9993 | -217.45% |
| `5x / 2x` | -0.4610% | 0.9368 | -243.56% |
| `5x / 3x` | -1.1803% | 0.8586 | -284.37% |

## Sonuc

Full-universe replay'de legacy, kendi aday evreninde pozitif expectancy ve PF > 1 vermistir. V2'nin `5x/1.5x` production-aligned sonucu basabaş seviyesinde negatiftir. Ancak V2 sonucu exit profiline duyarlidir; `5x/1x` ve `3x/1x` profilleri pozitif cikmistir. Bu nedenle **V2 kesin olarak basarisizdir** veya **legacy kesin olarak ustundur** sonucu cikarilamaz.

Bu replay'in kesin olarak gosterdigi seyler:

1. Onceki `901` legacy / `62` V2 farki sadece bug degil, kaynak evrenlerinin farkindan da kaynaklanir.
2. Ham evrenlerin tamaminda V2 production-aligned exit ile breakeven civarindadir.
3. Exit secimi V2 sonucunu materially degistirmektedir.
4. V2'nin production'a alinmasi icin daha buyuk forward shadow sample'i, exit politikasinin onceden kilitlenmesi, portfoy concurrency/sizing ve short-interest coverage testi gerekir.

## Cikti

- [Full-universe JSON](../data/backtest_out/p0_execution_replay_all/p0_execution_results.json)
- [Full-universe same-exit JSON](../data/backtest_out/p0_execution_replay_all_same_exit/p0_execution_results.json)
- V2 sensitivity: `data/backtest_out/p0_all_v2_exit_sensitivity/`
- [Runner](../p0_execution_replay.py)
