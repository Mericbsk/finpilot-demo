# ANS-3 — Temporal Replication of ANS-1: PRE-REGISTERED

**Tarih:** 2026-09-21 · **Level:** A (read-only; production/veri değiştirilmedi)
**Öncül:** ANS-1 (SUPPORTED) + ANS-2 (MIXED). **Soru:** ANS-1 sonucu zaman içinde tekrarlanıyor mu — **değişmeyen threshold'larla**?
**Pre-registration:** `research/ans3_temporal_replication_2026_09_21.py` (sonuçlardan önce sabitlendi)
**Artifact:** `data/backtest_out/ans3_temporal_replication_2026-09-21.json`

---

## 1. Önemli dürüstlük notu (sınır)

Research EOD verisi **2026-05-06 → 07-31** (c2c_5d, 54 gün). **Gerçek gelecek veri YOK.** Bu yüzden "temporal replication" burada = aynı seti **çakışmayan iki kronolojik yarıya** bölüp etkinin **ikisinde de** tutup tutmadığını ölçmek. Bu bir **stability/replication kontrolü**, gerçek future-OOS değil. (Gerçek gelecek penceresi 2026-07-31 sonrası yeni veri gerektirir.)

## 2. Verdict

```
ANS-3 = PARTIAL
```

Etki **geç dönemde** güçlü ve anlamlı, **erken dönemde** zayıf ve istatistiksel olarak belirsiz. İki yarı birden geçmedi → **PARTIAL** (REPLICATED değil, NOT_REPLICATED değil).

## 3. Sonuçlar (threshold'lar ANS-1'le AYNI — hiçbir ayar yapılmadı)

| Dönem | n | att% | att median | nor median | **Median iyileşme** | Bootstrap %95 CI | Null p | PASS |
|---|---:|---:|---:|---:|---:|---|---:|:--:|
| **FULL** | 34.762 | 38,6 | −2,33 | +0,30 | **+2,62** | [+0,16, +3,86] ✓ | 0,000 | ✅ |
| **EARLY** (05-06→06-23) | 12.413 | 39,5 | −0,70 | +0,32 | **+1,02** | [−2,00, +2,58] ✗ | 0,000 | ❌ |
| **LATE** (06-24→07-31) | 22.349 | 38,2 | −3,21 | +0,29 | **+3,50** | [+1,10, +6,00] ✓ | 0,000 | ✅ |

**Matched-random:** her üçünde de real_percentile=1.0 (eleme etkisi rastgele eleme değil).

## 4. Yorum (dürüst)

- **Gözlenen median iyileşme late yarıda early'den büyük** (+3,50 vs +1,02). **Ama bu iki nokta bir trend/interaction testi değildir** — veri, bunun zamansal güçlenme mi, rejim bileşimi mi, volatilite farkı mı, yoksa örnekleme varyasyonu mu olduğunu **henüz kanıtlamaz.** Bu bir **hipotez/olası açıklama** seviyesindedir, kanıtlanmış mekanizma değil.
- **Early dönem CI sıfırı içeriyor** ([−2,00, +2,58]) → erken dönemde etki istatistiksel olarak belirsiz (daha az veri + daha dar etki).
- **Big-loser oranı iki dönemde de attention'da belirgin yüksek** (early %19,4 / late %23,8 vs normal %4/%3,2) → **downside-risk yoğunlaşması her iki dönemde de tutarlı** (en stabil bulgu).
- Median iyileşme erken dönemde zayıf ama **işaret aynı yönde** (+).

## 5. Sınıflandırma (Meriç'in kuralı)

> "Research-period evidence supported, temporal replication **PARTIAL** — etki geç dönemde güçlü, erken dönemde belirsiz; downside-tail yoğunlaşması her ikisinde de tutarlı."

Bu:
- ANS-1'i **silmiyor** (full + late PASS)
- ama **"her dönemde eşit güçlü" değil** — regime/zaman bağımlılığı var

## 6. Attention evidence ledger (güncel)

```
Unusual movement detection      SUPPORTED
Future movement magnitude       SUPPORTED
Negative-screen / median        ANS-1 SUPPORTED (full); ANS-3 PARTIAL (zaman-bağımlı)
Downside-tail concentration     SUPPORTED + zaman-tutarlı (her iki yarıda da)
Opportunity cost                MATERIAL (ANS-2 MIXED)
Net economic value              NOT PROVEN
Buy / Short signal              NOT PROVEN
Portfolio-level value           NOT PROVEN
Temporal robustness             PARTIAL (late güçlü, early belirsiz)
Production recommendation       NOT APPROVED
```

## 7. Sonraki adım

- **Gerçek future-OOS:** 2026-07-31 sonrası yeni veri biriktiğinde ANS-1 prosedürünü aynen çalıştır (gerçek temporal replication).
- **ANS-4** (alt-grup upside/downside ayrımı): ancak pre-registration + feature-freeze + subgroup-önceden-tanım ile. Mining riski yüksek.
- **Ürün:** Attention Map = "high-dispersion / tail-risk-and-opportunity detector" etiketi en kanıt-uyumlu çerçeve. Production Level B/C ayrı.

## Governance
- Read-only; production/veri değiştirilmedi. Pre-registered; threshold'lar değişmedi; negatif/kısmi sonuç dürüstçe raporlandı. Gerçek future-OOS olmadığı açıkça belirtildi (split-sample replication).
