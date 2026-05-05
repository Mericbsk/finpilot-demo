# Legacy Streamlit Surface Özeti

## Teknik Tanım

Eski nesil Streamlit arayüzü ve bağlı `views/` modülleridir. Hâlâ ciddi bir kod hacmi ve iş mantığı içerir.

## Durum

**Kısmen çalışıyor / legacy.** Dosyalar yerinde duruyor; root Dockerfile ve compose içinde etkisi sürüyor. Modern runtime’ın parçası değil.

## Öne Çıkan Dosyalar

- `streamlit_app.py`
- `views/`
- `tests/test_views_smoke.py`

## Ana Bulgular

- Legacy yüzey CI ve Docker’da hâlâ aktif varsayım.
- `openpyxl` eksikliği view smoke testlerini kırıyor.
- Plansız bırakıldığında modernleşmeyi sürekli yavaşlatır.

## Güvenlik / Uyumluluk

- Eski state/auth kalıpları modern web güvenliğinden sapabilir.
- Export ve kullanıcı akışları için audit görünürlüğü sınırlı.

## Performans / Ölçek

- Primary runtime olmamalı.
- Sadece internal/admin araç olarak tutulacaksa açıkça ayrıştırılmalı.

## Puan

| Kriter | Puan |
|--------|------|
| Stabilite | 4 |
| Güvenlik | 4 |
| Performans | 4 |
| Test | 6 |
| Bakım | 3 |
| Teknik Borç | 3 |
| **Toplam** | **4.0 / 10 — C** |

## İlk 3 Aksiyon

1. Legacy yüzeyin destek durumunu resmi olarak ilan et.
2. Modernleşecek ve kalacak parçalar için migration matrix çıkar.
3. CI/Docker’dan legacy zorunluluğunu kontrollü biçimde ayır.

## Tekrarlama Notu

- **Ne nedir:** Projenin önceki nesil UI katmanıdır.
- **Nasıl çalışır:** Streamlit views bileşenlerini render eder ve eski iş akışlarını taşır.
- **Nasıl test edilir:** import smoke, export smoke ve temel navigation senaryoları koşulur.
- **Bir sonraki değerlendirme için not:** bu yüzeyin kaderi netleşmeden teknik borç azalmaz.
