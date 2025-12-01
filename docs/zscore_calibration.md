# Z-Skoru Kalibrasyon Güncellemesi

Bu not, FinPilot panelinde eklenen adaptif z-skoru iyileştirmelerini ve önerilen doğrulama adımlarını özetler.

## Öne Çıkan Yenilikler

- **Segment bazlı preset'ler:** 10 günlük ortalama hacme göre semboller `Yüksek`, `Orta` ve `Düşük` likidite segmentlerine ayrılıyor. Segment eşiklerine göre varsayılan z-skoru limitleri (±σ) otomatik seçiliyor.
- **Dinamik eşik kalibrasyonu:** Z-skoru eşikleri, seçilen rolling pencere içindeki getiri dağılımının %`q` yüzdelik değerinden türetiliyor. Varsayılan pencere 60 gün, varsayılan yüzdelik %97.5.
- **UI açıklamaları:** Sinyal kartlarında ve tablo chip'lerinde yeni "Z · ±σ" rozetleri yer alıyor. Tooltip, hareketin kaç sigma olduğunu, segmenti ve dinamik kalibrasyon detayını açıklıyor.

## Panelden Kontrol

Yan panelde yeni "Z-Skoru Ayarları" bloğu eklenmiştir.

| Ayar | Açıklama | Varsayılan |
| ---- | -------- | ---------- |
| Lookback Penceresi | Z-skoru ortalama/std hesaplanırken kullanılacak süre | 60 gün |
| Dinamik Pencere | Rolling dağılım örnekleri | 60 gün |
| Dinamik Z-eşiği | Aktif olduğunda yüzdelik temelli adaptif eşik kullanılır | Açık |
| Dinamik Eşik Yüzdesi | Z-eşiği için kullanılan yüzdelik (örn. 0.975 ≈ %97.5) | 0.975 |
| Likidite bazlı presetler | Hacme göre ±σ eşikleri otomatik seç | Açık |

> **İpucu:** Lookback değerini 20, 60 ve 120 olarak değiştirip shortlist sonuçlarını karşılaştırarak hızlı bir gözlemsel analiz yapabilirsiniz.

## Hızlı Backtest Yol Haritası

1. `backtest.py` içindeki `SimpleBacktest` sınıfını kullanın.
1. Komut satırından iki koşu yaparak statik ve dinamik z-eşiği senaryolarını kıyaslayın:

```powershell
python backtest.py --start 2023-01-01 --end 2024-01-01 --no-dynamic --lookback 60
python backtest.py --start 2023-01-01 --end 2024-01-01 --dynamic-window 60 --quantile 0.975
```

> İpucu: `--segment-presets/--no-segment-presets`, `--alpha` ve `--aggressive` bayraklarıyla rejim duyarlılığını, dinamik ağırlığı ve eşik sıkılığını hızlıca karşılaştırabilirsiniz.

1. Sonuçları Sharpe, Sortino ve hit ratio bazında kıyaslayın.

## Varsayılan Segment Eşikleri

| Segment | Ortalama hacim koşulu | Z-Eşik (±σ) |
| ------- | --------------------- | ----------- |
| Yüksek hacim | ≥ 1,000,000 | 2.0 |
| Orta hacim | 300,000 – 1,000,000 | 1.6 |
| Düşük hacim | ≤ 300,000 | 1.4 |

Gelecekte HMM tabanlı rejim tespiti devreye girdiğinde bu değerler otomatik olarak rejim bazında da ayarlanabilir.

## Sonraki Adımlar

- `backtest.py`'ye komut satırı parametreleri eklenerek dinamik/statik eşik karşılaştırması otomasyona bağlanmalı.
- Segment eşikleri regresyon veya grid-search ile optimize edilip `docs/` klasöründe sonuç raporu paylaşılmalı.
- Tooltip metinleri çoklu dil desteği için `i18n` yapısına taşınabilir.
