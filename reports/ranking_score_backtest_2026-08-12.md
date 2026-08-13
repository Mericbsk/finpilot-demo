# Ranking-Score Kritik Düzeltmesi ve Re-Test Sonuçları

Date: 2026-08-12
Level: A (araştırma; üretim değişikliği YOK)
Tetikleyici: Kullanıcının kod-takibi bulgusu — canlı ürünün `composite_score` değil `ranking_score` kullandığı

## Kod-seviyesi doğrulama (Kural 4)

| İddia | Doğrulama | Kaynak |
|---|---|---|
| Üç ayrı skor var | **FACT** | `scanner/evaluate.py:663-818` — `composite_score`, `legacy_quality_score`, `ranking_score` ayrı ayrı hesaplanıyor |
| `ranking_score` = `legacy_quality_score` (flag=0 iken) | **FACT** | `scanner/evaluate.py:722-723` — `_ranking_score = _composite_score if legacy_composite_ranking_enabled() else _legacy_quality_score` |
| Flag .env'de 0 | **FACT** | `.env:56` — `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0` |
| Yayın sıralaması `ranking_score`'a göre | **FACT** | `distribution/snapshot_builder.py:108-110` — `row.get("ranking_score") or row.get("composite_score")` |
| Export'ta `ranking_score` kolonu yok | **FACT** | `full_universe_enriched.csv` kolon listesi |
| Formül | **FACT** | `scanner/score_engine.py:193-226` — base + 1.5*ATR + 1.5*RVOL + 0.5*squeeze - 1.5*lottery - 1.0*overnight |

**Sınırlama:** Canlı sunucunun çalışan sürecinin ortam değişkenine erişim yok; yalnızca repo `.env` dosyası doğrulandı. 5 script `load_dotenv` kullanıyor ama canlı süreç bu dosyayı yüklüyor mu kesin değil. **Meriç/canlı-sunucu erişimi olan biri teyit etmeli.**

## Geriye-dönük hesaplama

`legacy_quality_score` formülü `full_universe_enriched.csv` üzerinde satır-satır hesaplandı (48,760 satır). Sonuç: `ranking_score` aralığı -20.0 ile 82.7 arasında (0-100 nominal ölçek dışına taşabiliyor, formül doğal sonucu).

## Re-test sonuçları: Üç skor yan yana

| Metrik | ranking_score (canlı) | composite_score | finpilot_score |
|---|---|---|---|
| n (5d getiri olan) | 43,323 | 39,466 | 32,582 |
| Spearman fwd 5d | **-0.032** | -0.017 | +0.011 |
| Spearman fwd 1d | +0.004 | +0.007 | +0.011 |
| Top-quintile gap (eligible − not) | **-2.69pp** | -1.84pp | -1.21pp |
| P1 matched (eligible − random) | **-1.30pp** | -2.53pp | -3.49pp |
| Eligible median 5d | **-0.83%** | -2.46% | -2.42% |
| Decile monotonicity | **-0.576** | -0.455 | +0.526 |

### Skorlar arası korelasyon

- ranking ↔ composite: **ρ = 0.758**
- ranking ↔ finpilot: **ρ = 0.742**

## Yorum

### 1. Ana negatif bulgular ranking_score'da da geçerli — hatta daha kötü

- **İleri korelasyon negatif:** ranking_score'un 5g ileri getiri ile Spearman'ı **-0.032** — composite_score'un -0.017'sinden daha negatif. Yani canlı ürünün kullandığı skor, ileriye dönük bilgi taşımak şöyle dursun, hafifçe **ters** yönde.
- **Top-quintile gap en kötü:** -2.69pp (composite'te -1.84pp, finpilot'ta -1.21pp). Canlı sıralama, en iyi bantta bile eligible'ı daha kötü seçiyor.
- **Decile monotonicity negatif:** -0.576. En yüksek decile medyanı **-0.35%** — en düşük decile'dan kötü. Skor arttıkça sonuç kötüleşiyor.

### 2. Ama "hiç test edilmemiş alan" iddiası düzeltilmeli

Ranking_score ile composite_score arasında ρ=0.758 korelasyon var. Yani composite_score üzerinde yapılan testler **tamamen alakasız değil** — %58 ortak varyans taşıyorlar. Ama %42'lik fark var ve bu fark önemli: ranking_score **daha kötü** bir forward predictor.

### 3. "Score backward-looking" bulgusu güçleniyor

ranking_score'un formülü backward-looking bileşenleri (ATR, RVOL) **pozitif**, forward-looking bileşenleri (lottery, overnight) **negatif** ağırlıklandırıyor. Ama forward korelasyonu yine de negatif. Bu, "backward-looking ağırlıkları doğru yönde olsa bile sonuç değişmiyor" demek — sorun formülün yönünde değil, bu feature'ların kendisinde.

### 4. Ürün kimliği açısından

Canlı ürünün kullandığı sıralama alanı:
- İleri getiriyi tahmin etmiyor (ρ ≈ -0.03)
- En iyi decile'ı en kötü performans gösterenler arasından seçiyor
- Eligible seçimi rastgele reddedilenden 1.30pp daha kötü

Bu, "sıralama katmanı değer eksiltiyor" bulgusunu **güçlendiriyor**, zayıflatmıyor.

## Sonuç

| Soru | Cevap |
|---|---|
| Önceki bulgular ranking_score'da da geçerli mi? | **Evet, hatta daha kötü** |
| Composite_score testleri tamamen alakasız mıydı? | Hayır — %58 ortak varyans var, ama ranking_score ayrıca ve daha kötü test edilmeli |
| Canlı ürünün sıralaması değer üretiyor mu? | **Hayır** — mevcut kanıtla desteklenmiyor |
| Bir sonraki adım ne? | `.env` flag'i canlı sunucuda teyit et + ranking_score'u export'a kalıcı ekle (Level B) |

## Governance

- Hiçbir production/scanner/score/entry-exit/publish davranışı değiştirilmedi.
- Locked OOS NOT_OPENED.
- `ranking_score`'u export'a eklemek ve scanner export pipeline'ını güncellemek **Level B** kararı gerektirir.
- `.env` flag'inin canlı sunucuda teyidi **Meriç veya sunucu erişimi olan biri** tarafından yapılmalı.
