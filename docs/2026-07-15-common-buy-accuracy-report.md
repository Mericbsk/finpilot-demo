# Legacy + V2 Ortak AL Dogruluk Raporu

## Tanim

**Ortak AL**, ayni canonical `(symbol, date)` kaydinda hem legacy `legacy_quality` hem de V2 `v2_confirmation` score'unun discovery doneminde ogrenilen top-%10 cut'i gecmesi olarak tanimlandi. Target: `resolved_pct_t5 >= 5%`.

Bu analiz ortak canonical evrende yapildi:

- Legacy canonical: 27,386 symbol-day
- V2 canonical: 4,680 symbol-day
- Common: 2,315 symbol-day, 650 sembol, 38 tarih
- Legacy cut: `55.214831`
- V2 cut: `32.747840`

## Sonuclar

| Donem | Ortak AL | Tarih | Legacy dogruluk | V2 dogruluk | Ikisi birlikte dogru |
| --- | ---: | ---: | ---: | ---: | ---: |
| Tum donemler, in-sample dahil | 270 | 31 | 57.41% | 54.44% | 51.11% |
| Discovery sonrasi | 210 | 19 | 56.19% | 50.95% | 48.10% |
| Locked OOS | 44 | 7 | 54.55% | 45.45% | 38.64% |

Discovery donemi threshold ogrenmek icin kullanildigi icin ilk satir in-sample'dir. Production kararinda locked OOS satiri esas alinmalidir.

## Yorum

Ortak AL sinyalleri iki modelin ayni hisseyi ayni gunde secmesidir. Bu, model agreement'i olcer; tek basina execution P&L veya portfolio sonucu degildir. Locked OOS'ta 44 ortak AL icin legacy'nin `resolved_pct_t5` hedefini tutturma orani `%54.55`, V2'nin `%45.45`, ikisinin ayni anda dogru olma orani `%38.64` oldu.

Bu metrik `resolved_pct_t5` favorable-move target'idir. Gercek trade sonucu icin ortak AL satirlari ayrica V2'nin `TP=5x ATR / SL=1.5x ATR` barrier'i ve slippage/commission ile replay edilmelidir.

## Ciktilar

- [JSON sonuclar](../data/backtest_out/common_buy_accuracy/common_buy_accuracy.json)
- [Ortak AL satirlari](../data/backtest_out/common_buy_accuracy/common_buy_signals.csv)
- [Olcum scripti](../common_buy_accuracy.py)
