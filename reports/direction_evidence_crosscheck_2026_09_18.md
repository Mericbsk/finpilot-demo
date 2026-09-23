# Direction External Evidence — FinPilot Cross-Check ("kontrolleri sağla")

**Tarih:** 2026-09-18 · **Level:** A (read-only doğrulama; production/veri değiştirilmedi)
**Girdi:** `reports/direction_prediction_external_evidence_2026-09-18.md` (dış kanıt taraması)
**Amaç:** Dış raporun FinPilot'a dair iddialarını **bizim verimizle** çapraz doğrulamak ve önerilen ANS-1 deneyinin uygulanabilirliğini kontrol etmek.

---

## 1. Ne doğrulandı

Dış raporun en kritik iddiası (§5.3): **dikkat çeken hisseler kısa ufukta düşük getiri verir** (Barber et al. 2022, JF: −%4,7/20 gün; Bali et al. 2011 lottery). FinPilot attention map'inin bunun "bağımsız bir tekrarı" olduğu iddia ediliyordu. Bunu kendi verimizle test ettim.

## 2. FinPilot verisinde çapraz doğrulama (EOD-only, descriptive)

Attention flag = `|gap_pct|≥3% OR atr_pct_real≥6%` (Big Gap OR Volatility Spike — raporla aynı tanım). 40.014 satır, attention rate %38.

### c2c_5d (5-gün forward)

| Grup | n | median | mean | big-loser (<−10%) |
|---|---:|---:|---:|---:|
| **Attention** | 13.433 | **−2,33%** | +8,94% | **%22,2** |
| **Normal** | 21.329 | **+0,30%** | +0,63% | **%3,5** |
| **Fark (normal − attention)** | | **+2,63 pp** | | **−18,7 pp** |

### c2c_1d (1-gün)

| Grup | median |
|---|---:|
| Attention | −0,77% |
| Normal | +0,02% |
| Fark | **+0,80 pp** |

**Doğrulandı:** Attention-flag'li hisseler **belirgin şekilde düşük medyan getiri** ve **~6× daha yüksek big-loser oranı** taşıyor. Bu, dış TIER A kanıtla (Barber −4,7%/20g; Bali lottery) **birebir uyumlu** ve FinPilot attention map'inin kendi bulgusuyla (−2,32% medyan) **tutarlı**.

## 3. ANS-1 uygulanabilirlik kontrolü

Dış raporun önerdiği tek deney (Attention-as-Negative-Screen) için:

| Kontrol | Durum |
|---|---|
| Attention flag'leri mevcut veriden üretilebilir mi | ✅ Evet (gap_pct + atr_pct_real, %100 nonnull) |
| c2c_5d mevcut mu | ✅ Evet (34.762 satır) |
| Yeni veri/feed gerekir mi | ✅ Hayır |
| Maliyet bariyeri | ✅ Yok (eleme = işlem değil) |
| Descriptive yön (in-sample) | ✅ Mevcut (attention → düşük medyan) |

**ANS-1 bizim evrenimizde uygulanabilir** ve descriptive ön-işaret dış kanıtla aynı yönde.

## 4. Önemli dürüstlük notları

1. **Bu çapraz kontrol descriptive/in-sample'dır** — ANS-1'in pre-registered OOS/matched-control/bootstrap testi değil. Yukarıdaki fark **yön kanıtı değil**, hipotezin bizim veride "absurd olmadığını" gösterir.
2. **Attention mean (+8,94) >> median (−2,33)** — büyük pozitif kuyruk var (bazı attention hisseleri çok yükseliyor). Negatif-eleme değeri **medyan/risk** tarafında; mean'i iyileştirmez. Raporun "eleme" çerçevesiyle tutarlı (medyan + big-loser oranı metrikleri).
3. **Dış kanıt ≠ bizim evre.** Dış rapor bunu açıkça işaretledi (§8 son satır). Benim kontrolüm bunu kısmen kapatıyor ama tam OOS değil.

## 5. Karar / Sonraki adım

- Dış raporun FinPilot bulgularını yorumu **doğru** (attention = negatif-yönlü, detection'ın "al" değil "kaçın" olduğu).
- **ANS-1 (negatif eleme) uygulanabilir ve dış kanıtla uyumlu.** Pre-registered ANS-1 deneyini (H1: eleme medyan 5-gün getiriyi iyileştirir; matched-random + null-shuffle + block-bootstrap) çalıştırmaya hazırım.

**Bu tur hiçbir production/veri/flag değiştirmedi; yalnızca dış raporu bizim verimizle çapraz doğruladı.**
