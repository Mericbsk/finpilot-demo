# P0 Nokta-Zamanli Replay ve Execution P&L Raporu

## Protokol

`p0_execution_replay.py` her canonical symbol-day kaydini replay'e alir. Score cut yalnizca discovery doneminden ogrenilir; discovery ve validation donemlerinde trade secilmez. Execution P&L yalnizca locked OOS'ta tum reject kosullarini gecen sinyaller icin hesaplanir.

- Canonical symbol-day: en erken timestamp
- Discovery: `<= 2026-04-17`
- Validation: `2026-04-18..2026-05-21`
- Locked OOS: `> 2026-05-21`
- Forward path: sinyal gununden sonraki 5 bar
- Stop-first same-bar tie rule
- One-way slippage: `5 bps`
- One-way commission: `5 bps`
- Fixed notional: `$1,000`
- Entry drift limiti: `%50`

Exit profilleri:

- Legacy: `TP=2x ATR`, `SL=1x ATR`
- V2-aligned: `TP=5x ATR`, `SL=1.5x ATR`

## Tum sinyal gunleri kapsami

Ilk cross-universe kiyas metodolojik olarak uygun degildi. Duzenlenmis replay iki artifact'in ortak canonical symbol-day kesisimini kullanir:

| Universe metric | Value |
| --- | ---: |
| Legacy canonical symbol-days | 27,386 |
| V2 canonical symbol-days | 4,680 |
| Common canonical symbol-days | 2,315 |
| Common symbols | 650 |
| Common dates | 38 |

Her iki source icin de bu 2.315 kaydin tamami replay edilmis ve 38 tarihin tamami kapsanmistir. Ancak locked OOS kurali nedeniyle discovery ve validation satirlari trade edilmeyip reject olarak kaydedilmistir.

| Source | Replayed symbol-days | Replayed dates | Discovery | Validation | Locked OOS | Selected trades | Selected dates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Legacy | 2,315 | 38 | 1,425 | 683 | 207 | 61 | 5 |
| V2 | 2,315 | 38 | 1,425 | 683 | 207 | 28 | 5 |

Bu nedenle cevap: **evet, common-universe icindeki tum sinyal gunleri replay'den gecirildi; hayir, tum gunlerde trade acilmadi.** Trade sonucu sadece locked OOS secimlerinin sonucudur.

## Onceki sonucun duzeltilmesi

Ilk P0 raporundaki `901` legacy islemi ile `62` V2 islemi farkli artifact evrenlerinden geliyordu. Ayrica V2, Alpha V2 risk profiline uymayan `2x/1x` exit ile kosulmustu. Bu nedenle eski **"legacy favors, V2 negative"** sonucu definitive evidence olarak geri cekilmistir.

## Locked OOS execution-P&L

### Ayni exit ile secim etkisi

Iki aday arasindaki secim farkini izole etmek icin her ikisine de legacy baseline `TP=2x ATR, SL=1x ATR` uygulanmistir.

| Source | N | TP rate | SL rate | Win rate | Net expectancy | Net total P&L | Profit factor | Max drawdown |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Legacy `legacy_quality` | 61 | 54.10% | 26.23% | 60.66% | 2.8707% | $1,751.14 | 3.1451 | -42.04% |
| V2 `v2_confirmation` | 28 | 42.86% | 50.00% | 46.43% | 2.2864% | $640.18 | 1.7629 | -57.77% |

### Strategy-specific exit profili

Legacy kendi baseline exit'ini, V2 ise production risk davranisina yakin `TP=5x ATR, SL=1.5x ATR` profilini kullanmistir.

| Source | N | Net expectancy | Net total P&L | Profit factor |
| --- | ---: | ---: | ---: | ---: |
| Legacy `legacy_quality` | 61 | 2.8707% | $1,751.14 | 3.1451 |
| V2 `v2_confirmation` | 28 | 4.0208% | $1,125.83 | 2.1819 |

### V2 exit sensitivity

Tum satirlar common universe, locked OOS ve `n=28` V2 islemi kullanir.

| V2 TP / SL | Net expectancy | Profit factor | TP rate | SL rate |
| --- | ---: | ---: | ---: | ---: |
| `2x / 1x` | 2.2864% | 1.7629 | 42.86% | 50.00% |
| `3x / 1x` | 3.7777% | 2.2605 | 28.57% | 50.00% |
| `3x / 1.5x` | 3.4969% | 2.0658 | 28.57% | 28.57% |
| `5x / 1x` | 4.3016% | 2.3796 | 7.14% | 50.00% |
| `5x / 1.5x` | 4.0208% | 2.1819 | 7.14% | 28.57% |
| `5x / 2x` | 4.4625% | 2.2783 | 10.71% | 10.71% |
| `5x / 3x` | 4.6348% | 2.3966 | 10.71% | 3.57% |

One-way slippage `5 bps -> 10 bps` stresinde strategy-specific kosu legacy icin `2.7679%`, V2 icin `3.9168%` net expectancy ve sirasiyla `3.0092` / `2.1345` PF verdi.

## Kanit ve production karari

- Ayni exit ile legacy daha yuksek expectancy ve PF verdi; V2 de pozitiftir.
- V2-aligned exit ile V2 expectancy legacy'den yuksek, fakat PF ve drawdown daha zayiftir.
- V2 sample'i `n=28`, legacy sample'i `n=61`; strateji siralamasi istatistiksel olarak hassastir.
- Bu bir portfoy replay'i degildir; concurrency, sizing, liquidity impact ve complete signal coverage ayrica test edilmelidir.

Sonuc: **ilk cross-universe P0 sonucu gecersizdir; common-universe execution evidence exit profiline duyarlidir ve V2'nin kesin olarak reddedilmesini desteklemez.** V2 composite score, score wiring, short-interest freshness/coverage, drawdown ve daha buyuk forward shadow sample'i tamamlanana kadar production'a alinmamalidir. Bu NO-GO karari V2'nin bu replay'de negatif olmasina dayanmamaktadir.

## Cikti dosyalari

- [p0_execution_replay.py](../p0_execution_replay.py)
- [scanner/telemetry.py](../scanner/telemetry.py)
- [Corrected common-universe JSON](../data/backtest_out/p0_execution_replay_common/p0_execution_results.json)
- [Same-exit JSON](../data/backtest_out/p0_execution_replay_common_same_exit/p0_execution_results.json)
- V2 exit sensitivity: `data/backtest_out/p0_v2_exit_sensitivity/`
