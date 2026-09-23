# DATA_REPAIR Teşhisi — c2c_5d bütünlüğü & catalyst_factor

Date: 2026-09-03
Level: A (teşhis; üretim değişikliği YOK; düzeltme önerileri Level B)
Tetikleyici: Experiment Review Board (2026-09-03) iki DATA_REPAIR kararı
Veri: `full_universe_enriched.csv` (SHA-256 e3b18355...) + `data/price_cache/*.json` (400 sembol) + `data/edgar_cache` (1.127) + `data/catalyst_cache.json`

---

## 1. c2c_5d bütünlüğü — KÖK NEDEN BULUNDU (FACT)

**Önceki açık iş:** CSV'deki `c2c_5d` ile price_cache'ten hesaplanan gerçek 5g kapanış getirisi korelasyonu ρ=0.845; beklenen ~1.0, kök neden bilinmiyordu.

**Bu teşhis (3.000 eşleşmiş satır):**

| Grup | n | Korelasyon | Medyan mutlak sapma | >5pp sapma |
|---|---:|---:|---:|---:|
| Gün-sonu taramaları (≥15:30) | 9.128 | **0.9829** | 0.07pp | %0.51 |
| Gün-içi taramaları (<15:30) | 5.214 | 0.9173 | 1.16pp | **%5.70** |

**Kanıt zinciri:**
- Büyük sapmaların (>5pp) %79'u gün içi saatlerde (13:30–14:30) taranmış; genel popülasyonda bu saatlerin payı %25 (FACT).
- CSV `price` alanı genelde gün kapanışına yakın (medyan sapma %0.27) ama sapmalı satırlarda günün **açılışına** daha yakın (medyan %2.11) — yani bu satırlarda giriş fiyatı intraday bir fiyat (FACT, gözlemsel).
- Tek gerçek kurumsal-aksiyon vakası: `USB 2025-09-12` (csv_price $359.87 vs bar close $49.13; oran 7.32 — ters split kalıntısı). 75 büyük sapmanın yalnızca 2'si split-benzeri (%2.7) (FACT).
- Takvim etkisi yok: 5 ileri bar hep 7/8/10 takvim günü, normal dağılım (FACT).

**Sonuç (INTERPRETED, yüksek güven):** Anomalinin ana sürücüsü split DEĞİL, **scan_ts heterojenliği**. Scanner gün içinde (13:30–14:30) ateşlendiğinde etiket intraday fiyattan hesaplanıyor; gün-sonu taramalarında etiket temiz (ρ=0.98). ρ=0.845 ölçümü karışık popülasyonun ortalamasıydı.

**Düzeltme önerisi (Level B — onay gerekir, henüz uygulanmadı):**
1. Etiket hesabını yalnızca EOD taramalarıyla (scan_ts ≥ 15:30) sınırla veya intraday satırları etiketleme dışında tut. Tek başına bu filtre etiket güvenilirliğini 0.92→0.98'e taşır.
2. `scanner/labeling.py`'ye `label_entry_basis` alanı ekle (`eod_close` / `intraday`) — provenance zorunlu.
3. Kurumsal aksiyon bekçisi: |csv_price / bar_close − 1| > %20 satırları otomatik flag (USB tipi vakalar; n≈%0.07).

**Kırılma tanımı:** Düzeltme sonrası EOD-olmayan satırlarda >5pp sapma oranı %1'in üstünde kalırsa teşhis yeniden açılır.

---

## 2. catalyst_factor = 0.0 — KÖK NEDEN ZİNCİRİ BULUNDU (FACT)

Canonical CSV'de 48.188 satırın tamamı 0.0. Üç katmanlı neden:

1. **Feature flag kapalı:** `FINPILOT_ENABLE_EDGAR_CATALYST` ortam değişkeni tanımsız → `scanner.catalyst.edgar_enabled()` = `False` → `compute_catalyst_factor()` kısa devre yapıp hep 0.0 döndürüyor (FACT — kod + runtime testi).
2. **Cache pratikte boş:** `data/catalyst_cache.json` son refresh 2026-09-02; yalnızca **8 sembol** ve **8'i de 0.0** (FACT). Evren ~1.800–2.000 sembol.
3. **EDGAR ham verisi mevcut ve zengin:** `data/edgar_cache/` altında 1.127 CIK submission dosyası var; örnek içerik `["8-K","10-Q","4","144","SCHEDULE 13G/A"]` formları ve tarihleri — yani ham olay verisi duruyor, skorlayıcı boru hattı çalıştırılmıyor (FACT).

**Düzeltme önerisi (Level B — onay gerekir, henüz uygulanmadı):**
1. `refresh_catalyst_cache` işini tüm evren için zamanlanmış görev olarak kur (mevcut fonksiyon; `_RATE_LIMIT_SLEEP` ile SEC dostu). Hedef kapsam: evren sembollerinin ≥%90'ı.
2. Refresh sonrası kalite kapısı: nonzero oran, form dağılımı (8-K/10-Q/4...), güncellik — artifact olarak raporla.
3. Ancak bundan sonra `FINPILOT_ENABLE_EDGAR_CATALYST=1` **değerlendirilebilir** — flag açmak production skor davranışını değiştirir (score_engine'de lottery offset + watch_tier'da fresh_catalyst kolu) → **Level B onayı + canlı gölge koşu şart.** Bu teşhis flag'i açmadı.

**Bilinmeyen (UNKNOWN):** `_score_filings`'in gerçek filing listelerinde dağılımı ölçülmedi (cache şeması fonksiyonun beklediği dict formatında değil; teşhis sırasında doğrudan doğrulanamadı). Refresh öncesi scorer uyumluluğu ayrıca test edilmeli.

---

## Governance

- İki madde de **teşhis** olarak tamamlandı; **hiçbir düzeltme uygulanmadı** (düzeltmeler Level B).
- Hiçbir scanner/score/publish davranışı değişmedi; flag'lere dokunulmadı.
- Locked OOS NOT_OPENED.
- Sonraki adım insan onayı ister: (a) labeling EOD filtresi + provenance alanı, (b) catalyst refresh görevi + kalite kapısı.
