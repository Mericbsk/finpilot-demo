# ANS-1 — Attention-as-Negative-Screen: PRE-REGISTERED TEST

**Tarih:** 2026-09-18 · **Level:** A (read-only araştırma; production/veri değiştirilmedi)
**Hipotez kaynağı:** EXTERNAL literatür (Barber et al. 2022 JF Robinhood; Bali et al. 2011 JFE) — verimizden türetilmedi → bu bir **confirmatory** test, mined discovery değil.
**Pre-registration:** `research/ans1_attention_negative_screen_2026_09_18.py` docstring (sonuçlardan önce sabitlendi)
**Artifact:** `data/backtest_out/ans1_attention_negative_screen_2026-09-18.json`

---

## 1. Verdict

```
ANS-1 = SUPPORTED
```

Attention-flag'li hisseleri evrenden **elemek**, kalan evrenin medyan 5-gün getirisini **+2,62 pp iyileştiriyor** — ve bu iyileşme **her üç kontrolü de** (matched-random, null-shuffle, block-bootstrap) geçiyor.

## 2. Ana sonuç

| Metrik | Değer |
|---|---:|
| n (c2c_5d) | 34.762 |
| Attention oranı | %38,6 |
| Attention median | **−2,33%** |
| Normal median | **+0,30%** |
| **Median iyileşme (eleme)** | **+2,62 pp** |
| Big-loser (<−10%) — attention | **%22,2** |
| Big-loser — normal | %3,5 |
| **Big-loser azalması** | **−18,7 pp** |
| Hit rate — attention / normal | 40,0% / 53,6% |

## 3. Kontroller (hepsi PASS)

| Kontrol | Sonuç | Eşik | Durum |
|---|---|---|---|
| **Median iyileşme > 0** | +2,62 pp | >0 | ✅ |
| **Block-bootstrap %95 CI** | [+0,16, +3,86] | sıfırı dışarıda | ✅ excludes 0 |
| **Matched-random** (aynı sayı rastgele ele) | gerçek kept median 1. percentile'ın üstünde (percentile=1.0) | >0,5 | ✅ |
| **Null-shuffle** (flag'i karıştır) | p=0,000; gerçek diff null dağılımın çok üstünde | p<0,05 | ✅ |

**Dört koşul da sağlandı.** Null dağılım mean=−0,03, gerçek diff=+2,62 → flag'in kendisi anlamlı (rastgele eleme bu etkiyi üretmiyor).

## 4. Yorum (dikkatli)

- Bu **"al sinyali" DEĞİL.** ANS-1 yalnızca şunu kanıtlar: **attention-flag'li hisseleri eleme, kalan evrenin medyan/risk profilini iyileştirir.** Eleme bir işlem değildir → maliyet bariyeri yok → bu, programın maliyetle ölen diğer adaylarından (fade, reversal, short) ayrılır.
- **Negatif-eleme değeri medyan/risk tarafında:** attention mean (+8,94) >> median (−2,33) → büyük pozitif kuyruk var. Bazı attention hisseleri çok yükseliyor; bu test "büyük kazananı kaçırma" maliyetini ölçmüyor (ayrı soru).
- **Kanıt hiyerarşisi:** dış TIER A (Barber/Bali) + iç descriptive (cross-check) + şimdi **pre-registered OOS-disiplinli kontrol** → üç bağımsız katman aynı yönde.

## 5. Ne kanıtlanmadı

- "Bu hisseleri short'la kâr et" — KANITLANMADI (short maliyet/borçlanma/limitsiz risk ayrı).
- "Attention = production short sinyali" — KANITLANMADI.
- Ekonomik değer (portföy düzeyi, kapasite) — bu test eleme düzeyinde, portföy değil.

## 6. Ürün anlamı (governance'a saygılı)

Attention map'in okunması **"al" değil "kaçın/dikkat"** yönünde destekleniyor. Bu, `VALIDATED-DESCRIPTIVE-RESEARCH` sınıflandırmasını güçlendirir ama **production yüzeyine taşımak ayrı bir Level B/C karardır** (yasak dil kırmızı çizgisi — "sat/kaçın" dili bile kullanıcı metnine Level C onayı olmadan giremez).

## 7. Negatif/limits

- In-sample universe (2026-05→08); gelecekte değişebilir.
- Eleme portföy getirisi ≠ hisse bazlı medyan (portföy yapısı ayrı).
- Büyük-kazanan kuyruğu fırsat maliyeti ölçülmedi.

## 8. Sonraki adım

- **Governance:** ANS-1 sonucunu decision-log'a işle (Level A araştırma sonucu).
- **Ürün:** Attention map'i "negatif eleme / risk uyarısı" olarak konumlandırma değerlendirmesi (Level B ürün kararı).
- **Araştırma:** "büyük-kazanan kuyruğunu eleme maliyeti" ayrı soru; detection→short sinyali ekonomik fizibilitesi ayrı gate.

## Governance
- Read-only; production/veri/flag değiştirilmedi. Pre-registered; negatif-sonuç politikası aktif; cherry-pick yok (tüm kontroller açık). Confirmatory (dış-literatür kaynaklı hipotez), mined değil.
