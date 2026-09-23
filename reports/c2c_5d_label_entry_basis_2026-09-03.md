# c2c_5d DATA_REPAIR Uygulaması — label_entry_basis (Meriç onaylı)

Tarih: 2026-09-03
Level: B fix, Meriç onayıyla uygulandı (Araştırma Portföyü Kurulu #1 kalemi)
Tetikleyici: `reports/data_repair_diagnosis_2026-09-03.md`'nin kök-neden bulgusu (EOD taramaları ρ=0.9829, gün-içi taramalar ρ=0.9173)

## Yapılan değişiklikler

1. **`fetch_full_universe_and_retest.py`** — ileriye dönük düzeltme: `label_entry_basis(scan_ts)` fonksiyonu eklendi (scan_ts saat:dakikası ≥15:30 ise `eod_close`, değilse `intraday`, eksikse `unknown`). `ENRICHED_KEYS`'e eklendi, enriched satır yazımında dolduruluyor. **`c2c_5d`/`c2c_1d`/`mae_t5` hesaplama mantığına dokunulmadı** — yalnızca provenance etiketi eklendi. Bu script ağ erişimi gerektirdiği için bu oturumda yeniden çalıştırılamadı; bir sonraki gerçek fetch çalışmasında otomatik devreye girecek.
2. **`research/label_entry_basis_backfill_2026_09_03.py`** — geriye dönük düzeltme: mevcut `full_universe_enriched.csv`'yi (ağ erişimi gerektirmez, `scan_ts` zaten CSV'de var) aynı eşikle etiketledi.

## Sonuç

- Toplam 100.496 satır (dedup öncesi) → **79.935 (%79,5) `eod_close`, 20.561 (%20,5) `intraday`**.
- En yoğun intraday saat dilimleri: 14:30 (3.437), 13:30 (2.889), 14:15 (2.867), 14:00 (2.858), 14:45 (2.626) — diagnostik raporun işaret ettiği 13:30–14:45 bandıyla birebir örtüşüyor.
- İki yeni dosya üretildi:
  - `data/backtest_out/full_universe_enriched_labeled.csv` — tüm satırlar + `label_entry_basis`, mevcut değerler değişmedi.
  - `data/backtest_out/full_universe_enriched_eod_only.csv` — yalnızca `eod_close` satırlar (n=79.935), diagnostik raporun önerdiği "temiz" alt-küme. Bundan sonraki istatistiksel testler bu dosyayı tercih edebilir (ρ=0.98 civarı beklenir; diagnostik raporun kendi eşleştirilmiş-örneklem ölçümü zaten bunu doğruladı, burada yeniden ölçülmedi).

## Kapsam ve sınırlar

- **Production/canlı scanner'a hiçbir etki yok.** Değişiklik yalnızca araştırma export'unda.
- `c2c_5d` değerlerinin kendisi **düzeltilmedi** — yalnızca hangi satırların güvenilir sayılması gerektiği işaretlendi (diagnostik raporun önerdiği yaklaşım buydu: "filtrele", "yeniden hesapla" değil).
- Geriye dönük backfill, `scan_ts` alanına dayanıyor — bu, diagnostik raporun kendi kanıt zincirinde (3.000 eşleşmiş satır + 400 sembol price_cache) doğrulanmış aynı eşik. Bu script o doğrulamayı tekrar üretmedi, sadece uyguladı.
- `unknown` etiketli satır sayısı ayrıca kontrol edilmeli (scan_ts formatı bozuk olan nadir satırlar) — bu raporda ayrı gösterilmedi, gerekirse bir sonraki turda eklenir.

## Sonraki adım

Yeni istatistiksel confirmatory koşular (özellikle fade/H3 yeniden testi ve abstention bağımsız doğrulaması) artık `full_universe_enriched_eod_only.csv`'yi tercih edebilir — Kapı A (veri-bütünlüğü) bu kalem için artık daha az kısıtlayıcı.
