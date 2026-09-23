# Day-1 Confirmation Matrix ve Delayed Entry — Araştırma Raporu

Date: 2026-08-14
Level: A (araştırma; üretim değişikliği YOK)
Veri: `full_universe_enriched.csv`, 40,729 temiz satır (price≥$1, |c2c_1d|≤50%, |c2c_5d|≤100%)
Kurallar: dedup, artifact filtreleme, matched-control farkındalığı

## Araştırma Sorusu

> "FinPilot'un en iyi entry'si sinyal anında mı (T0), yoksa ilk piyasa teyidi sonrasında mı (T+1)?"

---

## 1. Day-1 → Day-5 Return Matrix

| D1 Bucket | n | D5 Median | D5 Mean | D5 +5% | D5 +10% | D5 <-5% |
|---|---:|---:|---:|---:|---:|---:|
| <-3% | 6,490 | **-5.38%** | -5.86% | 11.0% | 5.2% | **52.2%** |
| -3 to -1% | 7,644 | -1.57% | -1.55% | 11.9% | 4.5% | 24.6% |
| -1 to 0% | 6,807 | -0.12% | -0.12% | 11.9% | 4.3% | 13.9% |
| 0 to 1% | 6,535 | +0.53% | +0.65% | 14.6% | 4.6% | 10.7% |
| 1 to 2% | 4,484 | +1.48% | +1.67% | 22.0% | 7.6% | 10.4% |
| 2 to 3% | 2,757 | +2.14% | +2.05% | 28.0% | 10.0% | 12.0% |
| 3 to 5% | 3,003 | +3.41% | +3.59% | **40.5%** | 16.9% | 11.1% |
| >5% | 3,009 | **+6.71%** | +7.53% | **56.9%** | **37.4%** | 12.5% |

**EVIDENCE:** Güçlü monoton ilişki. İlk gün ne kadar iyi olursa, 5 günlük sonuç o kadar iyi. Ama bu **momentum persistence**, yeni bir sinyal değil.

---

## 2. Confirmation Premium

### T0 Setup (entry_ok) vs T+1 Confirmed

| Grup | n | 5d Median | Premium |
|---|---:|---:|---:|
| T0 Setup (entry_ok) | 1,094 | -0.85% | — |
| T1 Confirmed (D1≥+1%) | 357 | **+1.51%** | **+2.35pp** |
| T1 Flat (0≤D1<1%) | 160 | +0.67% | +1.51pp |
| T1 Failed (D1<0%) | 577 | -3.77% | -2.93pp |

**EVIDENCE:** Day-1 confirmation, entry_ok kohortunda **+2.35pp** iyileşme sağlıyor. Ama bu, "Day-1 iyi gidenler zaten iyi" demek — momentum persistence'ın bir yansıması.

### Tüm Evren (entry_ok'dan bağımsız)

| Grup | n | 5d Median | +5% Rate |
|---|---:|---:|---:|
| D1 ≥ +2% | 8,769 | **+3.63%** | **42.2%** |
| D1 < -1% | 14,134 | **-2.90%** | 11.5% |
| Flat (-1 to +2%) | 17,826 | +0.42% | 15.4% |

---

## 3. KRITIK KEŞIF: Confirmation Premium Tersine mi?

### Decomposition: İlk gün mü, kalan 4 gün mü?

| Grup | D1 Median | D5 Median | Remaining 4d | Capture% |
|---|---:|---:|---:|---:|
| All | -0.03% | +0.05% | +0.04% | — |
| **D1 ≥ +2%** | **+3.87%** | +3.63% | **-0.65%** | **106.7%** |
| D1 ≥ +1% | +2.72% | +2.73% | -0.34% | 99.7% |
| D1 0-1% | +0.43% | +0.46% | +0.10% | 94.1% |
| D1 < 0% | -1.83% | -1.66% | +0.20% | 110.6% |

**EVIDENCE:** Day-1 ≥+2% yapan hisselerin 5 günlük getirisinin **%106.7'si** ilk günde gerçekleşiyor — kalan 4 gün **negatif** (-0.65%). Yani:

> **"T+1'e kadar bekle, en iyi kısmı kaçırırsın."**

Ama aynı zamanda:

> **"T+1'e kadar bekle, en kötü loserlardan kaçınırsın."**

Bu bir **trade-off**, bir "premium" değil.

---

## 4. Delayed Entry Analizi

| Strateji | n | Median | Mean | +5% Rate |
|---|---:|---:|---:|---:|
| T0 all (baseline) | 40,729 | +0.05% | +0.00% | 19.8% |
| T+1 all | 40,729 | +0.04% | +0.05% | 18.2% |
| T+1 confirmed (D1≥1%) | 13,253 | **-0.34%** | -0.52% | 19.3% |
| T+1 strong (D1≥2%) | 8,769 | **-0.65%** | -0.89% | 20.9% |
| T+1 skip if failed | 20,232 | -0.06% | -0.30% | 17.1% |

**EVIDENCE:** Delayed entry (T+1) T0'dan **daha kötü**. Çünkü:

1. İlk gün +2% yapanların kalan 4 günü negatif (-0.65%)
2. İlk gün +2% yapanların sadece %46.6'sı kalan 4 günde pozitif
3. İlk gün +2% yapanların sadece %28.9'u kalan 4 günde +3% üzeri

**Sonuç:** "T+1'e bekle, teyit al, sonra gir" stratejisi bu veri setinde **işe yaramıyor** — çünkü ilk gün hareketin büyük kısmını yakalıyor.

---

## 5. Day-1 Winner Continuation: Hangi +2% Devam Ediyor?

Day-1 ≥+2% yapan 8,769 hisseden:

- %46.6'sı kalan 4 günde pozitif
- %28.9'u kalan 4 günde +3% üzeri

### Devam eden vs tersine dönen Day-1 winner'lar

| Feature | Continue | Reverse | Diff |
|---|---:|---:|---:|
| ATR% | 5.09 | 5.92 | **-0.83** |
| RVOL | 0.90 | 0.86 | +0.05 |
| Dist52W | 0.73 | 0.71 | +0.02 |
| Composite Score | 26 | 28 | -2 |
| Price | $34.00 | $25.59 | **+$8.42** |
| Lottery | 0.42 | 0.49 | -0.07 |

**EVIDENCE:** Devam eden Day-1 winner'lar daha **düşük ATR'lı** ve daha **pahalı** hisseler. Tersine dönenler daha volatil ve daha ucuz. Ama farklar küçük — hiçbir feature güvenilir ayrım yapmıyor.

---

## 6. Confirmation Matrix: D1 × RVOL × ATR

### D1 × RVOL → 5d Median

| D1 \ RVOL | low | normal | high | extreme |
|---|---:|---:|---:|---:|
| neg | -1.88% | -1.19% | -1.53% | -2.44% |
| flat | +0.31% | +0.69% | +0.82% | +0.50% |
| mod | +1.20% | +1.76% | +1.50% | +1.73% |
| strong | +1.63% | +2.55% | +2.69% | +2.74% |
| extreme | +3.88% | +4.93% | +5.48% | **+6.74%** |

**EVIDENCE:** En iyi hücre **D1 extreme + RVOL extreme** (+6.74%). Ama bu, "ilk gün çok yükselmiş + çok hacimli" — momentum'un en uç noktası.

### D1 × ATR → 5d Median

| D1 \ ATR | low | med | high | extreme |
|---|---:|---:|---:|---:|
| neg | -0.44% | -1.15% | -3.04% | **-6.05%** |
| flat | +0.57% | +0.92% | +0.16% | -2.45% |
| mod | +1.62% | +1.86% | +0.57% | -0.41% |
| strong | +2.59% | +2.45% | +1.63% | -0.18% |
| extreme | +4.15% | +5.07% | +5.41% | +3.31% |

**EVIDENCE:** D1 extreme + ATR med **+5.07%** — en dengeli hücre. D1 extreme + ATR low da iyi (+4.15%). Ama D1 extreme + ATR extreme **düşüşe** geçiyor (+3.31%).

---

## 7. Sentez: "Attention → Confirmation → Entry" Çerçevesi Çalışıyor mu?

### Evet çalışan kısım

- Day-1 confirmation, entry_ok kohortunda +2.35pp iyileştiriyor
- Day-1 ≥+2% olanların %42.2'si 5 günde +5% yapıyor
- D1 × RVOL interaction monoton ve güçlü

### Hayır çalışmayan kısım

- Delayed entry (T+1) T0'dan daha kötü — ilk gün hareketin %107'sini yakalıyor
- "Teyit bekle" stratejisi en iyi kısmı kaçırıyor
- Hiçbir kombinasyon matched-control'den geçmiyor

### Asıl soru

> **"T0'da mı gir, T+1'de mi?"** — Yanlış soru.

Doğru soru:

> **"T0'da hangi hisseleri izlemeye al, T+1'de hangilerini elem?"**

Bu bir **eleme** stratejisi, bir **gecikme** stratejisi değil.

---

## 8. Önerilen Araştırma Çerçevesi

```
T0: Scan → Watchlist (tüm adaylar)
         ↓
T+1: Observe → Filter (Day-1 davranışına göre)
         ↓
    ┌────┴────┐
    ↓         ↓
  D1≥+1%   D1<0%
    ↓         ↓
  HOLD     REJECT
    ↓
  T+2..T+5: Monitor
```

Ama bu **yeni bir entry değil** — bu bir **risk yönetimi** katmanı.

---

## Governance

- Hiçbir production/scanner/score/entry-exit/publish davranışı değiştirilmedi.
- Locked OOS NOT_OPENED.
- Confirmation Premium (+2.35pp) **DISCOVERY SIGNAL** — matched-control'den geçmedi.
- Delayed entry sonuçları **EVIDENCE** — T+1 stratejisi T0'dan daha kötü.
