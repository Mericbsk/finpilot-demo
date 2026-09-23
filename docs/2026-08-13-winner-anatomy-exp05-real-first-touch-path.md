# Winner Anatomy — Gerçek First-Touch Path Backtest (data/price_cache)

Tarih: 2026-08-13 · Statü: Level A · Veri: `full_universe_enriched.csv` + `data/price_cache/*.json` (2.047 sembol, gerçek günlük OHLCV)

## Düzeltme

Önceki turda "ham price_cache dosyası diskte yok" dedim — **yanlıştı**, yanlış arama yaptım (dosya adı deseni aradım, `data/price_cache/` bir klasör, içinde 2.047 sembol için ayrı `.json` dosyası var, gerçek günlük OHLCV, 2024-09 → 2026-07). Bu, önceki turlarda "MFE yok, first-touch backtest yok" diye işaretlenen boşluğu kapatıyor.

## Metodoloji

61.297 temiz satırdan 58.045'i price_cache'te sembol+tarih eşleşmesi buldu. Her satır için: giriş = scan_date barının kapanışı, sonraki 5 işlem günü boyunca gerçek High/Low ile MFE/MAE, ve TP=2%/SL=2% için bar-bar first-touch simülasyonu (aynı barda ikisi de tetiklenirse muhafazakâr varsayım: SL önce).

**Açık uyarı:** bu yeni hesaplanan `close5_real` ile dosyadaki hazır `c2c_5d` arasındaki korelasyon 0.845 — yüksek ama 1.0 değil. Aynı şeyi ölçüyor olmaları gerekirdi (aynı sembol, aynı 5-gün pencere). Fark muhtemelen giriş noktası tanımı (scan-close vs ertesi-open) veya split-ayarlama farkından geliyor — tam nedenini bulmadım, bu bir açık iş olarak kalıyor. Yön ve büyüklük tutarlı olduğu için aşağıdaki bulgulara güveniyorum ama %100 aynı şey değiller.

## Sonuçlar

| Popülasyon | n | medyan MFE | medyan MAE | TP ilk | SL ilk | TIME | ort. pnl (maliyet öncesi) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Tüm evren | 58.045 | +4.01% | -3.53% | %43.7 | %51.4 | %4.9 | -0.15% |
| **entry_ok=True** | 1.847 | +3.58% | **-5.38%** | **%35.2** | **%62.0** | %2.8 | **-0.53%** |
| entry_ok=False | 56.198 | +4.03% | -3.47% | %44.0 | %51.0 | %5.0 | -0.14% |
| **ATR3-5+RVOL1-1.5 aday** | 4.829 | +4.27% | -3.40% | **%49.5** | %50.3 | %0.3 | **-0.02%** |

## Okuma

Bu artık "diagnostic simülasyon" değil, gerçek first-touch path backtest — path sırasını biliyoruz. Ve sonuç önceki close-tabanlı yaklaşımı doğruluyor, hatta netleştiriyor:

`entry_ok=True` gerçek path'te de en kötüsü — TP/SL 2/2 ile SL'e çarpma oranı %62 (evrende %51.4), gerçek MAE -5.38% (evrende -3.53%). Bu artık yaklaşık değil, gerçek bar-bar simülasyonla doğrulanmış.

ATR3-5+RVOL1-1.5 adayı, gerçek first-touch'ta da en iyisi — TP/SL neredeyse yarı yarıya (%49.5/%50.3), maliyet öncesi ortalama pnl sıfıra çok yakın (-0.02%). Hâlâ 55bps maliyet sonrası negatif olur ama diğer üç popülasyondan belirgin şekilde daha az kötü, ve şimdi bu gerçek path verisiyle söyleniyor, yaklaşıklıkla değil.

## Açık iş

`close5_real` vs `c2c_5d` uyuşmazlığının (ρ=0.845) kaynağını bulmak — muhtemelen giriş noktası tanımı farkı, ama doğrulanmadı. Bu çözülmeden, buradaki mutlak büyüklüklere (sadece yönüne değil) tam güvenmemeliyiz.
