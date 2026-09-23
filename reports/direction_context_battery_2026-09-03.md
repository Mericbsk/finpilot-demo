# Direction-Context Battery — "Attention yönü bağlamla koşullanabilir mi?"

Date: 2026-09-03
Level: A (araştırma; üretim değişikliği YOK, locked OOS NOT_OPENED)
Veri: `full_universe_enriched.csv` (40.834 temiz satır) + `sector_map_full.csv` + `data/intraday_cache` (880 dosya)
Script: `research/direction_context_battery_2026_09_03.py` → artifact: `data/backtest_out/direction_context_battery_2026-09-03.json`
Yöntem: Pre-registration (script docstring, sonuçlardan önce yazıldı) + kronolojik 70/30 split (kesim: 2026-06-26; discovery n=21.925, OOS n=18.909)

## Araştırma Sorusu

Attention Map hareket büyüklüğünü yakalıyor ama yönü yakalayamıyor. Bağlam (piyasa rejimi, sektör yoğunlaşması, açılış aralığı) yönü koşullayabilir mi?

## Sonuç Tablosu

| Hipotez | Discovery | OOS | Verdikt |
|---|---|---|---|
| H1a: `regime` kolonu yönü koşullar | Ters işaret (regime=True +0.22% < regime=False +0.60%); matched-control şans düzeyi | Aynı ters işaret (-4.70% vs -3.10%) | **DESTEKLENMEDİ** |
| H1b: breadth rejimi yönü koşullar | Ters işaret (down-gün attention +1.79% > up-gün +0.19%); matched-control null | Sıralama tuttu ama matched-control null (share_positive 0.20/0.00) | **DESTEKLENMEDİ** |
| H2: sektör kümesi yönü koşullar | Clustered +0.48% vs isolated -2.49% | **Tersine döndü:** clustered -3.83% vs isolated -2.00% | **DESTEKLENMEDİ** |
| H3: ilk-30dk yönü günü öngörür | match rate %39.7 (n=698) — %50'nin ALTINDA | OOS yok (cache ~1-2 hafta) | **REDDEDİLDİ** (tersine DISCOVERY SIGNAL) |

## Bulgular

1. **H1a/H1b:** Ne scanner'ın kendi `regime` bayrağı ne de gün-bazlı evren breadth'i (medyan gap_pct) attention hisselerinin 5g yönünü koşullamıyor. Discovery'de gözlenen küçük farklar matched-control'de şans düzeyinde ve OOS'ta işaret korunsa bile etki attention'a özgü değil (tüm evren aynı yönde hareket ediyor).
2. **H2:** Küme içi aynı-yön payı %67.5 (discovery) / %71.2 (OOS) — sektör günleri tanımsal olarak birlikte hareket ediyor, ama bu tarama anında yön bilgisi ÜRETMİYOR: clustered vs isolated farkı discovery ile OOS arasında tersine döndü. Not: `>=3` eşiği çok gevşek (attention satırlarının %98'i "clustered" çıktı; isolated n=128/38).
3. **H3:** Gap günlerinde ilk 30 dakikanın yönü günün geri kalanıyla yalnızca %39.7 uyumlu — yani devam değil **tersine dönüş** eğilimi. n=698 ile %39.7, binom se ~%1.9 altında anlamlı biçimde %50'nin altında. Bu yeni bir DISCOVERY SIGNAL'dir ("opening-range fade"); kural olabilmesi için kendi pre-registration'ı ve gerçek OOS'u gerekir. Intraday cache yalnızca ~1-2 haftayı kapsıyor; genişletme Level B.

## Yorum

Üç bağımsız bağlam katmanı da yönü kurtarmadı. Bu, "yön bu özellik uzayında yok" bulgusunu 7. bağımsız yoldan güçlendiriyor. Attention Map'in ürün çerçevesi (betimleyici, yönsüz) bu sonuçla daha da sağlamlaştı: yön vaadi ekleme girişimleri veri tarafından desteklenmiyor.

Olası tek canlı ipucu: H3'ün tersine çıkması (açılış fade'i). Ancak bu bile üründe "yön" olarak değil, en fazla "gap sonrası ilk hareket genelde terslenir" şeklinde betimleyici bir akademi/risk notu olarak kullanılabilir — o da kendi doğrulamasını gerektirir.

## Governance

- Hiçbir production/scanner/score/entry-exit/publish davranışı değiştirilmedi.
- Locked OOS NOT_OPENED.
- H1/H2/H3 sonuçları: hipotezler **desteklenmedi/reddedildi** — pre-registration disiplini gereği bu da raporlanmış sonuçtur.
- H3 tersine bulgusu: DISCOVERY SIGNAL; confirmatory test ayrı ve pre-registered olmalı.
