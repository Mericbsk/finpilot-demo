# FinPilot Legacy ve V2 Score Formula Karsilastirmasi

## Kapsam

Bu calisma production score engine'i degistirmeden, iki mevcut research artifact'i uzerinde farkli score formul ve agirliklerini test eder:

- Legacy: `data/backtest_out/full_universe_enriched.csv`
- V2: `data/backtest_out/enriched_signals_v3.csv`
- Hedef: `resolved_pct_t5 >= 5%`
- Maliyet senaryolari: 0.00, 0.30, 0.55 ve 1.00 puan
- Canonicalizasyon: her source artifact icinde `(symbol, date)` icin en erken timestamp
- Split: discovery `<= 2026-04-17`, validation `2026-04-18..2026-05-21`, locked OOS `> 2026-05-21`

Bu rapor favorable-movement metriğini kullanir. Bu, path-dependent TP/SL execution P&L degildir.

## Denenen Formuller

### Legacy

- `legacy_existing`: artifact icindeki mevcut `composite_score`.
- `legacy_base`: regime + direction + raw score; mevcut composite'in yeniden kurulabilir cekirdek proxy'si.
- `legacy_confirmation`: cekirdege ATR, RVOL, pozitif gap ve squeeze kalite terimleri eklenir.
- `legacy_precision`: confirmation'a sentiment eklenir; lottery ve overnight risk faktorleri ceza olarak kullanilir.
- `legacy_quality`: ATR ve RVOL agirligi artirilir; lottery ve overnight cezalari korunur.

`catalyst_factor` mevcut artifact'te gozlenen satirlarda yalnizca `0.0` oldugu icin aday formulere dahil edilmedi.

### V2

- `v2_documented`: `4*short + 3*ATR + 3*gap + 2*RVOL - 1.5*extension`
- `v2_volatility_first`: ATR agirligi artirilir, short/gap agirliklari azaltılır.
- `v2_selective`: `4*short + 4*ATR + 1.5*gap + 1.5*RVOL - 2*extension`
- `v2_confirmation`: `3*short + 3*ATR + 2*gap + 2*RVOL - 2*extension`

V2 short-interest alanlari source artifact'te mevcut oldugu kadar kullanildi. Missing short degeri sifir kabul edilmedi; normalized missing policy rapor artifact'inde saklidir. Legacy ve V2 artifact'leri ayni evren degildir, bu nedenle cross-source kazanan iddiasi kurulamaz.

## Locked OOS Sonuclari

Baseline maliyet 0.55 puan uygulanmis `mean_return_pct` maliyet sonrasi forward return'dur.

| Source | Formula | N | Sinyal/gun | Precision | Recall | Mean return | Median return |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Legacy | mevcut composite | 0 | 0.00 | - | 0.00 | - | - |
| Legacy | legacy_base | 5,126 | 189.85 | 38.39% | 34.59% | 5.29% | 2.90% |
| Legacy | legacy_confirmation | 3,309 | 122.56 | 49.71% | 28.91% | 6.98% | 4.42% |
| Legacy | legacy_precision | 1,225 | 45.37 | 52.57% | 11.32% | 8.24% | 4.92% |
| Legacy | legacy_quality | 1,187 | 43.96 | 55.18% | 11.51% | 10.28% | 5.48% |
| V2 | v2_documented | 93 | 6.64 | 47.31% | 34.92% | 5.72% | 3.50% |
| V2 | v2_volatility_first | 94 | 6.71 | 45.74% | 34.13% | 4.73% | 3.17% |
| V2 | v2_selective | 77 | 5.50 | 48.05% | 29.37% | 6.42% | 3.50% |
| V2 | v2_confirmation | 92 | 6.57 | 50.00% | 36.51% | 6.22% | 4.84% |

Mevcut composite'te discovery score kesiti bulunmayan satirlar oldugu icin locked OOS threshold replay'i `n=0` verdi. Bu, mevcut composite'in artifact veri sozlesmesinin eksik oldugunu ve production'da score completeness telemetry gerektirdigini gosterir; mevcut composite'in iyi veya kotu oldugunu kanitlamaz.

## Yorum

- Legacy icin `legacy_quality`, mevcut composite ranking'ine gore daha secici ve locked OOS'ta daha yuksek precision verdi. Ancak bu sonuc henüz execution barrier ile dogrulanmadi.
- `legacy_confirmation` daha fazla sinyal verir ve precision'i korur; operasyonel trade-off olarak shadow test adayi olabilir.
- V2 icin `v2_confirmation` bu artifact/split icinde en yuksek locked OOS precision ve recall kombinasyonunu verdi. Farklar kucuk ve OOS orneklemi yalnizca 92 satirdir.
- Discovery'de daha yuksek precision, production'a otomatik aktarim gerekcesi degildir. Formul ve threshold ayni discovery doneminde secildigi icin multiple-testing riski vardir.
- Legacy ile V2 ayni artifact evreninden gelmedigi icin precision oranlari dogrudan yaristirilamaz.

## Production Karari

**NO-GO: production score engine degistirilmemeli.**

Gerekceler:

1. Locked OOS sonuclari favorable-movement hedefidir; TP/SL path, slippage, entry drift ve ayni bar stop/target kurallari henuz bu formula matrix'e baglanmamistir.
2. V2 locked OOS orneklemi kucuktur.
3. Legacy mevcut composite alaninda missingness vardir.
4. Formuller ayni artifact icinde discovery'de secildigi icin bagimsiz validation ve yeni shadow donemi gerekir.
5. Production Alpha V2 wiring'i offline V2 formulu ile halen birebir ayni degildir.

## Sonraki Gate'ler

1. `legacy_quality`, `legacy_confirmation`, `v2_documented` ve `v2_confirmation` icin barrier adapter'i ile horizon 3/5, TP 2x ATR, SL 1x ATR ve maliyet 0.55/1.00 testleri.
2. Aylik ve rejim bazli stability; minimum ay ve minimum aday sayisi kurallari.
3. Aynı point-in-time symbol-day universe uzerinde legacy/V2 intersection testi.
4. En az yeni bir locked OOS donemi veya ileriye donuk shadow test.
5. Score completeness, reject reason ve component telemetry'si production'a alinmadan formula degisikligi yapilmamasi.

## Cikti Dosyalari

- Runner: `score_formula_comparison.py`
- JSON: `data/backtest_out/score_formula_comparison/score_formula_comparison.json`
- CSV: `data/backtest_out/score_formula_comparison/score_formula_summary.csv`
