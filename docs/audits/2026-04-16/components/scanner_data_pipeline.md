# Scanner & Data Pipeline Özeti

## Teknik Tanım

Piyasa verisini çekip indikatör ve sinyal üreten quant veri hattıdır. Sonuçlar shortlist dosyaları olarak saklanır ve API üzerinden sunulur.

## Durum

**Kısmen çalışıyor.** Kod tabanı olgun ve route entegrasyonu mevcut. Ancak bu denetimde dış veri bağımlı tam yük testi yapılmadı.

## Öne Çıkan Fonksiyonlar

- `scanner/data_fetcher.py`
- `scanner/indicators.py`
- `scanner/signals.py`
- `scanner/evaluate.py`
- `api/routers/scan.py`

## Ana Bulgular

- Cache stratejisi iyi tasarlanmış.
- Shortlist staleness kontrolü mevcut.
- `print` ve logger birlikte kullanılıyor.
- Dış veri sağlayıcıları için contract testleri eksik.

## Güvenlik / Uyumluluk

- PII düşük.
- En büyük risk veri kalitesi ve dış kaynak sürekliliği.

## Performans / Ölçek

- Thread pool ve cache olumlu.
- Provider rate limit ve büyük batch taramalar risk yaratabilir.

## Puan

| Kriter | Puan |
|--------|------|
| Stabilite | 7 |
| Güvenlik | 6 |
| Performans | 7 |
| Test | 7 |
| Bakım | 6 |
| Teknik Borç | 6 |
| **Toplam** | **6.6 / 10 — B** |

## İlk 3 Aksiyon

1. Tüm veri hattı loglarını standardize et.
2. Dış veri schema contract testleri ekle.
3. Scan başarısızlık oranı ve stale shortlist metriklerini görünür hale getir.

## Tekrarlama Notu

- **Ne nedir:** Teknik analiz ve sembol değerlendirme motorudur.
- **Nasıl çalışır:** veri çekilir, zenginleştirilir, skorlanır ve shortlist yazılır.
- **Nasıl test edilir:** geçerli/geçersiz sembol, stale data, rate limit ve parallel scan senaryoları çalıştırılır.
- **Bir sonraki değerlendirme için not:** cache hit oranı ve sağlayıcı hata oranı izlenmelidir.
