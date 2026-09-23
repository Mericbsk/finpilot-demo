# ANS-2 — Attention Negative-Screen OPPORTUNITY COST: PRE-REGISTERED

**Tarih:** 2026-09-18 · **Level:** A (read-only; production/veri değiştirilmedi)
**Öncül:** ANS-1 (SUPPORTED). **Soru:** "Eleme'nin downside faydası, pozitif-kuyruk fırsat maliyetini aşıyor mu?"
**Pre-registration:** `research/ans2_opportunity_cost_2026_09_18.py` (sonuçlardan önce sabitlendi)
**Artifact:** `data/backtest_out/ans2_opportunity_cost_2026-09-18.json`

---

## 1. Verdict

```
ANS-2 = MIXED
```

**Median iyileşiyor ama mean DÜŞÜYOR ve pozitif kuyruk büyük ölçüde kayboluyor.** ANS-1'in "medyan/risk faydası" gerçek — ama **fırsat maliyeti çok büyük**: elenen attention grubu, evrenin **en uç pozitif hareketlerinin çoğunu** içeriyor.

## 2. Profil karşılaştırması (c2c_5d)

| Metrik | ALL (34.762) | ATTENTION (13.433) | KEPT/elem (21.329) |
|---|---:|---:|---:|
| **median** | −0,155 | **−2,33** | **+0,30** |
| mean | +3,84 | +8,94 | **+0,63** |
| p5 / p10 | −15,4 / −10,5 | −21,5 / −16,3 | −8,6 / −6,0 |
| p90 / p95 | +8,9 / +13,7 | +13,2 / +20,9 | +7,1 / +10,1 |
| **std** | 154,9 | **248,3** | **16,2** |
| big-loser (<−10%) | %10,7 | **%22,2** | **%3,5** |
| big-winner (>+10%) | %8,5 | **%13,8** | %5,1 |
| **top-5% mean** | +112,1 | **+256,5** | **+18,3** |
| top-1% mean | +482,9 | +1.157,9 | +40,3 |

## 3. Opportunity Cost (kritik)

| Metrik | Değer | Yorum |
|---|---:|---|
| Median kazancı (eleme) | +0,45 pp | küçük (ANS-1'in +2,62'si attention-vs-normal'dı; all-vs-kept daha küçük) |
| Big-loser kaldırıldı | %22,2 → (attention'da) | downside faydası GERÇEK |
| **Big-winner kaybedildi** | %13,8 (attention'da) | **upside maliyeti GERÇEK** |
| **Top-5% mean kaybı** | **−93,8 pp** (112,1 → 18,3) | **büyük kazananlar eleniyor** |
| **Mean değişimi** | **−3,21 pp** (3,84 → 0,63) | **mean DÜŞÜYOR** |
| Tail EV (|ret|>10) | 42,0 → 17,1 | uç hareketler yok oluyor |

**Kritik bulgu:** Eleme, **negatif kuyruğu** (%22,2 big-loser) kaldırıyor AMA **pozitif kuyruğu da** kaldırıyor (top-5% mean 112→18, mean −3,21pp). Attention hisseleri **yüksek-dispersiyon** taşıyor (std 248 vs 16) — hem en kötü hem en iyi sonuçlar orada.

## 4. Neden MIXED (SUPPORTED değil)

Pre-registered mantık: `mean_change < 0 VEYA top5_lost >= 5.0` → MIXED. İkisi de tetiklendi (mean −3,21, top5_lost 93,8).

**Yorum:**
- **Medyan/risk açısından:** eleme faydalı (ANS-1 doğru).
- **Beklenen-değer (mean) açısından:** eleme **zararlı** — attention grubunun büyük pozitif kuyruğu mean'i yukarı çekiyordu; onu elemek mean'i düşürüyor.
- **Bu "bedava öğle yemeği" değil** — downside'ı azaltırken upside'ı feda ediyorsunuz.

## 5. Ürün anlamı (dürüst)

ANS-1 + ANS-2 birlikte:
- **Risk-koruma / medyan-iyileştirme** isteyen bir kullanıcı için: eleme mantıklı olabilir (daha az felaket).
- **Beklenen-getiri / büyük-kazanan** isteyen için: eleme **zararlı** — attention hisseleri tam da büyük hareketleri üreten yer.

**Bu, attention map'i "kaçın" DEĞİL, "yüksek-volatilite / yüksek-risk / yüksek-uç-hareket" olarak etiketlemeyi destekler.** Ne körü körüne ele, ne körü körüne al — **kullanıcının risk iştahına bağlı bir ayrım.**

## 6. Ne kanıtlanmadı

- "Eleme ekonomik olarak net pozitif" — **HAYIR** (mean düşüyor).
- "Eleme kötü" — **HAYIR** (medyan ve big-loser iyileşiyor).
- Doğru cevap **risk-hedefi-bağımlı** — tek bir evrensel cevap yok.

## 7. Sonraki adım

- **ANS-3 temporal replication** (yeni zaman dilimi) — ANS-1+ANS-2'nin robustness'ı.
- **Ürün:** attention map'i "yüksek-volatilite uyarısı" olarak çerçevele (risk-seeking vs risk-averse ayrımı) — Level B ürün kararı.
- **Araştırma:** "attention içinde hangi alt-grup büyük-kazananı üretiyor?" (ayrı soru; mining riski — pre-register gerekir).

## Governance
- Read-only; production/veri değiştirilmedi. Pre-registered; negatif/karma sonuç dürüstçe raporlandı; cherry-pick yok (hem downside hem upside gösterildi). MIXED = geçerli ve bilgilendirici sonuç.
