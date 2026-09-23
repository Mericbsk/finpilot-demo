# catalyst_factor DATA_REPAIR Uygulaması — Evren-Çaplı Refresh Denemesi (Meriç onaylı)

Tarih: 2026-09-03
Level: B fix, Meriç onayıyla denendi ("Evet, kur")
Tetikleyici: `reports/data_repair_diagnosis_2026-09-03.md` — EDGAR ham verisi var ama skorlayıcı boru hattı çalıştırılmıyor.

## Yapılan

`research/catalyst_universe_refresh_2026_09_03.py` yazıldı ve çalıştırıldı: yerel `data/edgar_cache/tickers.json` (10.433 şirket, symbol→CIK) ve `data/edgar_cache/sub_*.json` (1.127 CIK dosyası) kullanılarak `scanner/catalyst.py::_score_filings` ile **bire bir aynı** ağırlıklarla (kaynak kopyalandı, mantık değiştirilmedi) evren-çaplı bir `data/catalyst_cache.json` üretildi. **`FINPILOT_ENABLE_EDGAR_CATALYST` flag'i açılmadı** — onaylanan kapsamın dışında bırakıldı.

## Dürüst sonuç — hedef karşılanmadı, nedeni net

| Metrik | Değer | Hedef |
|---|---:|---:|
| Evren | 1.926 sembol | — |
| Skorlanan | 1.199 (%62,25) | ≥%90 |
| **Kapı geçti mi** | **HAYIR** | — |
| CIK eşleşmesi yok | 51 sembol | — |
| Coverage gap (CIK var, yerel dosya/ağ yok) | 676 sembol | — |
| Son 7 günde en az 1 dosyalaması olan | **0 / 1.199** | — |
| Nonzero (bu yüzden) | 0 / 1.199 | — |

**İki ayrı sorun, ikisi de bu ortamın (sandbox) fiziksel kısıtı, kod hatası değil:**

1. **Kapsam %62,25, %90 değil** — çünkü yerel `edgar_cache/`'te yalnızca 1.127 CIK dosyası var, evrenin geri kalanı (676 sembol) için canlı SEC ağına (`data.sec.gov`) erişim gerekiyor. Bu ortamda denedim: `data.sec.gov` bağlantısı **proxy 403 ile reddedildi** (doğrulandı). Bu semboller için cache'e **0.0 yazılmadı** — "bilinmiyor" olarak boş bırakıldı, sessiz yanlışlık üretilmedi.
2. **Tazelik 0/1.199** — yerel cache dosyaları geçmişte bir kerelik dump edilmiş (en yeni kayıtlar 2026-05 civarı), bugüne (2026-09-03) göre 7 günlük pencerenin tamamı dışında kalıyor. Yani boru hattı **doğru çalışıyor** (test edildi, mantık sağlam) ama girdisi bayat — bu yüzden bugün için hesaplanan her `catalyst_factor` dürüstçe 0.0.

## Ne anlama geliyor

Boru hattının kendisi artık çalışır durumda ve doğrulandı (kod-seviyesinde, gerçek veriyle). Ama bu ortamın ağ erişimi olmadığından **gerçek, güncel bir evren-çaplı refresh burada tamamlanamaz.** Bunu tamamlamak için script'in ağ erişimi olan bir ortamda (canlı sunucu veya Meriç'in kendi makinesi) çalıştırılması gerekiyor — orada hem kapsam %90'a çıkar hem de tazelik gerçek olur.

## Kapsam ve sınırlar

- Production'a hiçbir etki yok — `FINPILOT_ENABLE_EDGAR_CATALYST` dokunulmadı, flag kapalı kaldığı sürece `compute_catalyst_factor()` zaten hep 0.0 döndürüyor.
- `data/catalyst_cache.json` üzerine yazıldı (eski hali: 8 sembol, hepsi 0.0 — zaten bilgi taşımıyordu, kayıp önemsiz).
- Script tekrar kullanılabilir: ağ erişimi olan bir ortamda çalıştırıldığında hem yerel cache'i hem canlı SEC ağını otomatik birleştirecek şekilde tasarlanmadı (bu script yalnızca yerel-öncelikli, ağ denemesi eklenmedi çünkü bu ortamda test edilemiyordu) — **bir sonraki adım**, ağ erişimi olan ortamda canlı fetch fallback'ini de ekleyip gerçek bir koşu yapmak.

## Sonraki adım

Bu script'i (veya `scanner/catalyst.py::refresh_catalyst_cache`'in kendisini, yerel-cache-öncelikli hale getirilmiş versiyonunu) canlı sunucuda ya da ağ erişimi olan bir makinede çalıştırmak — o zaman hem %90 kapsam hem gerçek tazelik mümkün olur. Ancak bundan sonra `FINPILOT_ENABLE_EDGAR_CATALYST=1` **değerlendirilebilir** (ayrı Level B onayı + gölge koşu şart — bu teşhis/deneme flag'i açmadı).
