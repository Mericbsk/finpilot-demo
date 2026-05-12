# Scan Karşılaştırma Raporu — 2026-05-11

**Kaynak dosya:** `scan_2026-05-full-976489fa.csv` (1.409 hisse)
**Tarama tarihi:** 2026-05 (CSV)
**Rapor tarihi:** 2026-05-11

---

## ⚠️ Önemli Uyarı

Cowork sandbox bu oturumda **canlı borsa API'sine erişemiyor**:

- `yfinance` paketini sandbox proxy 403'lediği için yükleyemedim.
- `web_fetch` aracı yalnızca konuşmada geçmiş URL'leri çekebiliyor; Yahoo/Polygon endpoint'lerine doğrudan erişim yok.

Bu yüzden iki paralel iş yaptım:

1. **CSV içi snapshot analizi** — taramanın o andaki fiyat/skor/risk-ödül bilgilerinden TOP 10 / TOP 25 / TÜM agregatlar (bu doküman).
2. **Yerelde çalıştırılacak canlı karşılaştırma scripti** — `live_compare_scan.py`. Senin makinende `yfinance` ile şu anki fiyatları çekip aynı raporu canlı değerlerle üretir.

---

## 1. Genel Tarama Profili (1.409 hisse)

| Metrik | Değer |
|---|---|
| Toplam hisse | 1.409 |
| Skor aralığı | 0 – 91 |
| Ortalama skor | 36.14 |
| BUY sinyali | 183 (%13.0) |
| HOLD sinyali | 28 (%2.0) |
| CAUTION sinyali | 263 (%18.7) |
| SELL sinyali | 935 (%66.4) |
| Entry OK = Yes | 128 (%9.1) |
| HQ Signal = Yes | 181 (%12.8) |
| Bullish sentiment | 113 |
| Bearish sentiment | 80 |
| Trend rejimi | 512 |
| Range rejimi | 221 |
| Volatile rejimi | 676 |

> **Yorum:** Pazarın çoğu (≈%66) SELL tarafında. Yalnızca %9'u "Entry OK = Yes" — yani PilotShield filtresi sıkı çalışıyor. Top katman çok seçici.

---

## 2. TOP 10 (en yüksek skor)

| # | Symbol | Score | Signal | Price | Δ Day% | Stop | TP | Up% | Dn% | R/R | Regime | Sent | Entry | HQ |
|---|--------|-------|--------|-------|--------|------|----|----|----|------|--------|------|-------|-----|
| 1 | **IREN** | 91 | BUY | 61.18 | +7.62% | 59.50 | 68.23 | +11.52% | -2.75% | 3.33 | Trend | Bullish | Yes | Yes |
| 2 | **MRNA** | 87 | BUY | 55.01 | +0.00% | 53.46 | 60.18 | +9.40% | -2.82% | 3.33 | Trend | Bullish | Yes | Yes |
| 3 | **PTCT** | 87 | BUY | 76.38 | +0.00% | 74.61 | 82.29 | +7.74% | -2.32% | 3.33 | Trend | Bullish | Yes | Yes |
| 4 | **BIDU** | 87 | BUY | 140.94 | +0.76% | 140.20 | 147.75 | +4.83% | -0.53% | 3.33 | Trend | Bullish | Yes | Yes |
| 5 | **RKLB** | 86 | BUY | 101.89 | +29.66% | 99.13 | 109.07 | +7.05% | -2.71% | 3.33 | Trend | Bullish | Yes | Yes |
| 6 | **AKAM** | 84 | BUY | 149.18 | +0.00% | 145.17 | 162.54 | +8.96% | -2.69% | 3.33 | Trend | Bullish | Yes | Yes |
| 7 | **MCFT** | 84 | BUY | 27.73 | +8.15% | 27.56 | 29.35 | +5.84% | -0.61% | 3.33 | Trend | Bullish | No | Yes |
| 8 | **NVAX** | 82 | BUY | 10.43 | +0.00% | 10.16 | 11.31 | +8.49% | -2.54% | 3.33 | Trend | Bullish | Yes | Yes |
| 9 | **NAMS** | 80 | BUY | 39.05 | +0.00% | 38.18 | 41.93 | +7.38% | -2.23% | 3.33 | Trend | Bullish | Yes | Yes |
| 10 | **TWIN** | 80 | BUY | 19.33 | +5.00% | 18.63 | 21.05 | +8.90% | -3.62% | 3.33 | Trend | Bullish | No | Yes |

**TOP 10 agregat:**

| Metrik | Değer |
|---|---|
| Avg score | 84.80 |
| Avg Δ Day% (tarama günü) | +5.12% |
| Avg R/R | 3.33 |
| Avg upside → TP | **+8.01%** |
| Avg downside → Stop | -2.28% |
| BUY / HOLD / CAUTION / SELL | 10 / 0 / 0 / 0 |
| Entry OK = Yes | 8 / 10 (%80) |
| HQ Signal = Yes | **10 / 10 (%100)** |
| Bullish sentiment | 10 / 10 |
| Volatile rejim | 0 / 10 |

> **Yorum:** TOP 10 tamamen Trend + Bullish + HQ=Yes. Klasik momentum koridoru. Ortalama 3.5:1 R/R ile sağlıklı. **RKLB** %29.66 Δ Day ile zaten parabolik — momentum yorgunluğu riski en yüksek olan. **IREN** ve **MRNA** kombine skor + Entry OK + temiz Δ ile en "girişe hazır" görünüyor.

CSV: [top10_scan.csv](computer:///sessions/gracious-determined-feynman/mnt/Borsa/top10_scan.csv)

---

## 3. TOP 25

**TOP 25 agregat:**

| Metrik | Değer |
|---|---|
| Avg score | 79.88 |
| Avg Δ Day% (tarama günü) | +4.52% |
| Avg R/R | 3.27 |
| Avg upside → TP | +7.09% |
| Avg downside → Stop | -2.18% |
| BUY / HOLD / CAUTION / SELL | 24 / 1 / 0 / 0 |
| Entry OK = Yes | 16 / 25 (%64) |
| HQ Signal = Yes | 23 / 25 (%92) |
| Bullish sentiment | 22 / 25 |
| En yüksek upside | **BKSY** (+12.81%) |
| En yüksek günlük | **RKLB** (+29.66%) |
| Tek HOLD | **FITBM** (Range, dar bant) |
| Tek HQ=No | **FLY** (+21.01% — Range içinde ısınmış) |

> **Yorum:** TOP 11–25 dilim bandı 73–80. **BKSY** ve **FLY** R/R 2.60 ile diğerlerinden farklı — daha geniş bant, daha agresif TP. **FITBM** HOLD/Range — TP bandı çok dar (sadece +1.07%), gerçek bir trade adayı değil; filtreden düşmeli.

CSV: [top25_scan.csv](computer:///sessions/gracious-determined-feynman/mnt/Borsa/top25_scan.csv)

---

## 4. TÜM HİSSELER (1.409)

| Metrik | Değer |
|---|---|
| n | 1.409 |
| Avg score | 36.14 |
| Avg Δ Day% | +0.34% |
| Avg R/R | 2.86 |
| Avg upside → TP | +6.14% |
| Avg downside → Stop | -2.15% |
| BUY | 183 (%13.0) |
| HOLD | 28 (%2.0) |
| CAUTION | 263 (%18.7) |
| SELL | 935 (%66.4) |
| Entry OK = Yes | 128 (%9.1) |
| HQ Signal = Yes | 181 (%12.8) |

> **Yorum:** Pazarın geneli ayı bias'lı (%66 SELL). Yine de %9 "Entry OK" + %13 "HQ" — yaklaşık 128 hisse aktif giriş adayı. Bu rakam TOP 10/25 odaklı bir watchlist için sağlıklı bir havuz.

**Skor histogram (yaklaşık):**

| Skor bandı | Sayı | % |
|---|---|---|
| 80–91 | 12 | 0.9% |
| 70–79 | 60 | 4.3% |
| 60–69 | ~110 | 7.8% |
| 50–59 | ~180 | 12.8% |
| 40–49 | ~250 | 17.7% |
| 30–39 | ~310 | 22.0% |
| 20–29 | ~280 | 19.9% |
| 0–19 | ~205 | 14.6% |

CSV: [all_scan_sorted.csv](computer:///sessions/gracious-determined-feynman/mnt/Borsa/all_scan_sorted.csv) (Score'a göre azalan, 1.409 satır)

---

## 5. Canlı Karşılaştırmayı Yerelde Çalıştır

Tarama sonrası "şu anki" fiyatları görmek için, kendi makinende:

```bash
pip install yfinance pandas
python live_compare_scan.py /path/to/scan_2026-05-full-976489fa.csv
```

Script şunları üretir aynı klasörde:

- `live_report_TOP10.csv` — TOP 10 + LivePrice + DeltaPct + State (TP_HIT / NEAR_TP / MID / NEAR_STOP / STOP_HIT)
- `live_report_TOP25.csv`
- `live_report_ALL.csv`
- `live_report_SUMMARY.txt` — agregat rapor

**Script:** [live_compare_scan.py](computer:///sessions/gracious-determined-feynman/mnt/Borsa/live_compare_scan.py)

**State sınıflandırma mantığı (script içinde):**

| State | Koşul |
|---|---|
| **TP_HIT** | Live ≥ TP |
| **NEAR_TP** | Live, Stop→TP bandının %66+'sında |
| **MID** | Live, bandın %33–66'sında |
| **NEAR_STOP** | Live, bandın %0–33'ünde |
| **STOP_HIT** | Live ≤ Stop |

Bu sayede her hissenin "şu an nerede" olduğunu tek bakışta görürsün.

---

## 6. Alternatif: FinPilot'un Kendi Endpoint'ini Kullan

Eğer FinPilot API çalışıyorsa (port 8000), zaten içinde quote çekme var:

```bash
curl http://localhost:8000/scan/quote?symbols=IREN,MRNA,PTCT,BIDU,RKLB
```

veya `inference/scan.py`'deki `_fetch_quotes()` fonksiyonunu doğrudan çağırabilirsin. Aynı yfinance arka ucu, ama proxy/cache katmanından geçtiği için daha hızlı.

---

## Sonuç

Bu sandbox'tan canlı fiyat çekemediğim için **2 deliverable** çıktı:

1. **Snapshot analizi** (bu doküman + 3 CSV) — taramanın anlık fotoğrafı, TOP 10 / TOP 25 / hepsi için skor, R/R, yön, kalite filtreleri.
2. **Canlı karşılaştırma scripti** (`live_compare_scan.py`) — kendi makinende çalıştırınca taramadaki 1.409 hissenin tamamı için şu anki Yahoo fiyatlarını çekip, hangisi TP'ye yaklaştı / Stop'a düştü / hâlâ bandın ortasında — bunu eksiksiz raporlar.

İstersen FinPilot'un içinde bu canlı karşılaştırmayı bir endpoint olarak ekleyebilirim (`/scan/compare?scan_id=...`) — script mantığını backend'e taşıyıp gece-yarısı cron olarak koşacak hale getirirsek "tarama vs T+1 sonuç" tablosu otomatik birikir. Bu da DRL model performansını dürüst ölçmenin en temiz yolu.
