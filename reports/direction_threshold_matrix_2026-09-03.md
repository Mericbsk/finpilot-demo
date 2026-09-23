# Experiment #1 — Market Regime × Attention Tier × Forward Direction

Date: 2026-09-03
Level: A (araştırma; üretim değişikliği YOK, locked OOS NOT_OPENED)
Veri: `full_universe_enriched.csv` (40.834 temiz satır) + `data/intraday_cache` (880 dosya, ~1-2 hafta)
Script: `research/direction_threshold_matrix_2026_09_03.py` → artifact: `data/backtest_out/direction_threshold_matrix_2026-09-03.json`
Yöntem: Pre-registration (docstring, sonuçlardan önce) + kronolojik 70/30 split (kesim 2026-06-26; discovery n=21.925, OOS n=18.909)
Rejim tanımı: gün-bazlı evren medyan gap_pct, sabit eşikler (≥+0.2% strong-up, ≤-0.2% strong-down) — 81 gün: 20 up / 42 neutral / 19 down

## Soru

> Attention sinyali tek başına sadece hareket büyüklüğünü mü yakalıyor, yoksa piyasa rejimi eklendiğinde yönsel bilgi ortaya çıkıyor mu?

## H1: Rejim × Tier × Eşik matrisi — DESTEKLENMEDİ (rejim), TIER BASKIN (doğrulandı)

5g medyan getiri (discovery → OOS):

| Rejim | Normal | Watch | High |
|---|---|---|---|
| Strong Up | +0.69% → -0.11% | +1.09% → -1.66% | -3.48% → -3.08% |
| Neutral | +0.49% → +0.19% | +0.66% → **-4.43%** | -2.25% → -5.60% |
| Strong Down | +1.24% → +0.30% | +2.23% → -1.68% | +1.36% → -3.95% |

- Discovery'de strong-down günlerde attention hisseleri DAHA İYİ (rebound deseni: Watch +2.23%). **OOS'ta bu desen kalmadı** (Watch -1.68%).
- High tier matched-control her iki dönemde de açıkça negatif (share_positive 0.30/0.30/0.30 discovery; 0.18/0.26/0.02 OOS) — rejim eklemek High tier'ın negatifliğini hiçbir hücrede kaldırmıyor.
- **Baskın desen:** Tier etkisi rejim etkisinden güçlü. High tier 6 hücrenin 6'sında da OOS'ta negatif; Normal tier 6 hücrenin 4'ünde pozitife yakın. Rejim satırları arasında tutarlı monoton kayma YOK.
- Eşik dağılımı: High tier'da `<-5%` kuyruğu her rejimde en büyük kütle (discovery 26.8-45.6%, OOS 38.2-52.1%); `>=+5%` kuyruğu da Normal'den büyük ama asla sol kuyruğu geçmiyor.

**Cevap:** Rejim eklenince yönsel bilgi ortaya ÇIKMIYOR. Attention hâlâ yalnızca hareket büyüklüğü ölçüyor; tier arttıkça sol kuyruk büyüyor.

## H2: Catalyst türü / event-type — VERİ AÇIĞI + gap-yön proxy'si

- **Bulgu (veri kalitesi):** `catalyst_factor` canonical CSV'de sabit 0.0 (48.188 satır). Gerçek olay etiketi (earnings/FDA/haber) veri setinde yok → "catalyst türü yönü ayırıyor mu?" sorusu mevcut veriyle **cevaplanamaz**. Bu, veri hattı açığı olarak kaydedildi.
- Proxy (gap yönü — dikkat: gap skora girdiği için kısmi döngüsellik var):
  - Watch tier'da gap-down > gap-up her iki dönemde de (discovery: +1.00% vs -0.23%; OOS: +1.49% vs -1.61%) — işaret replike oldu.
  - Ancak matched-control: gap-down bile evrenin altında (share_positive 0.37/0.41) — yani gap-down Watch "evrene göre iyi" değil, sadece "gap-up'tan daha az kötü".
  - **Verdikt:** strict kriter altında DESTEKLENMEDİ; "gap-down Watch, gap-up Watch'tan daha az negatif" göreli eğimi replike oldu → DISCOVERY SIGNAL (kendi pre-registration'ı gerekir).

## H3: Opening-range fade tradeable mı? — DISCOVERY SIGNAL (güçlendi, ama tradeable kanıtı YOK)

- Fade kuralı (30. dakikada ilk yönün tersine gir, kapanışta çık), n=698 gap günü:
  - Win rate **%59.9**, ortalama **+0.91%**, medyan +0.51% (brüt).
- **Tradeable denemez:** spread/slippage/komisyon verisi yok; gap hisselerinde spread geniş (tipik >0.5-1% round trip) — brüt +0.91% ortalama maliyet sonrası belirsiz. Örneklem ~1-2 hafta ve 880 sembolle sınırlı; OOS ayrımı yapılamadı.
- Sonraki adım: intraday cache genişletme (Level B, veri maliyeti) + maliyet modeli + pre-registered OOS.

## H4: Intraday path hangi noktada yön bilgisi üretir? — HİÇBİR NOKTADA (gün içinde)

Gap günlerinde "şu ana kadarki hareket" ile "günün kalanı" korelasyonu:

| Dakika | n | korelasyon | aynı-işaret oranı |
|---|---:|---:|---:|
| ~30 | 711 | -0.31 | %38.7 |
| ~60 | 711 | -0.35 | %47.0 |
| ~120 | 706 | -0.26 | %43.8 |
| ~195 | 696 | -0.16 | %46.6 |

- Tüm noktalarda **negatif** korelasyon: gün içi devam sinyali yok; tersine dönüş eğilimi 30. dakikada en güçlü, gün sonuna doğru zayıflıyor.
- Yön bilgisi gün içinde üretilmiyor; üretilen tek şey fade eğilimi ve o da 195. dakikada neredeyse kayboluyor.

## H5: Attention × event type — dolaylı cevap

Gerçek event etiketi olmadığından yalnızca proxy ile: tier (attention yoğunluğu) gap yönünden bağımsız olarak baskın. High tier gap-up ve gap-down'da da negatif (OOS: -6.04% / -4.17%). Yani mevcut veri "hangi olay?" sorusunu ayırt edemiyor; "ne kadar olağandışı?" sorusunu ayırt ediyor.

## Sonuç

1. **Rejim × Tier matrisi yön üretmiyor.** Tier güçlü ve tutarlı; rejim tutarsız. "Strong-down günlerinde attention al" deseni discovery'de vardı, OOS'ta öldü.
2. **Catalyst etiketi veri açığı** — `catalyst_factor` sabit sıfır; gerçek olay türü testi için EDGAR/news join'i gerekir (Level B veri işi).
3. **Opening-range fade** %59.9 brüt win rate ile en canlı DISCOVERY SIGNAL — ama maliyetsiz varsayımıyla; tradeable ilanı için maliyet + OOS şart.
4. **Intraday path** yön üretmiyor; sadece fade'in zamanlamasını tarif ediyor.
5. Attention Map'in betimleyici ürün çerçevesi 8. bağımsız yoldan daha da güçlendi.

## Governance

- Hiçbir production/scanner/score/entry-exit/publish davranışı değiştirilmedi.
- Locked OOS NOT_OPENED.
- H1 reddedildi (strict kriter), H2 strict kriterde reddedildi ama göreli eğim DISCOVERY SIGNAL, H3 DISCOVERY SIGNAL (maliyet/OOS kapıları açık), H4 negatif bulgu.
- Yeni açık işler: (a) catalyst/event veri hattı (Level B), (b) intraday cache genişletme + fade pre-registration (Level B).
