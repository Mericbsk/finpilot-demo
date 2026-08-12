# FinSense — Calibration Specification v1
Durum: LOCKED (2026-08-11) · Belge 02 — Belge 00 (Architecture Contract) altında durur.
Soru: **Prediction ve outcome'dan nasıl ölçüm çıkarıyoruz?**

---

## 1. Üç seviye — isimler bağlayıcı

| Seviye | Ad | Ne zaman aktif | İçerik | Bugünkü durum |
|---|---|---|---|---|
| v0 | **Calibration Interaction v0** | Şimdi, canlı | Oturum-içi guess/reveal, kalıcı değil | `ClassroomPreview.tsx` — CANLI |
| v1 | **Calibration Engine v1** | N≥1 → N≥10 | persistent prediction + probability + objective outcome + evaluation | YOK, bu belge onu tanımlıyor |
| v2 | **Calibration Intelligence v2** | N≥20-30 | Brier, calibration gap, bucket reliability | YOK |
| v3 | (gelecek) | — | error taxonomy, reasoning analysis, adaptive | YOK |

**"Engine" kelimesi yalnız v1+ için kullanılır.** v0 bir UI etkileşimidir, ölçüm motoru değildir — bu isimlendirme kilitlidir (Contract §22).

## 2. Girdi (Prediction)

VS-01 minimum alan seti:

```text
direction     UP | DOWN | FLAT     — zorunlu
probability   preset: 50/60/70/80/90%  — zorunlu
reason        50–300 karakter      — opsiyonel
```

`alternative` alanı **v1'e ertelendi**, VS-01'de yok.

## 3. Çıktı — Evaluation (per-prediction, deterministik)

```text
direction_correct   : bool
binary_outcome      : 0 | 1
probability_error   : |p - y|  (basit v0 formu)
```

## 4. Brier Score — formül, ama N≥20-30'a kadar gösterilmez

$$ Brier = \frac{1}{N}\sum_{i=1}^{N}(p_i-y_i)^2 $$

`p_i` = kullanıcının probability'si, `y_i` = gerçekleşen binary outcome. N=1'de bu sayı hesaplanabilir ama **kullanıcıya profil olarak sunulmaz** — bkz. §6 sample-size kuralı.

## 5. Accuracy ≠ Calibration — tek skora indirilmez

- **Direction accuracy**: genel isabet oranı.
- **Calibration**: "70% dediklerimin gerçekten ~%70'i çıktı mı" — bucket bazlı, farklı bir soru.

İkisi tek bir "skor"da birleştirilmez (Contract §26) — kullanıcıya her ikisi ayrı ayrı gösterilir, gösterilecek kadar veri varsa.

## 6. Sample-size gating (bağlayıcı)

| N | Gösterilen |
|---|---|
| N < 5 | Hiçbir calibration profili yok. Yalnız: "This prediction was evaluated." |
| N = 5–9 | "Early signal" etiketiyle, düşük güven vurgusu |
| N ≥ 10 | Confidence bucket'ları (50-59/60-69/70-79/80-89/90-100) gösterilebilir |
| N ≥ 20-30 | Brier score, calibration gap |

VS-01'de kullanıcı tipik olarak N=1 olacağı için **bu belgenin §4'ü kod olarak var ama UI'da görünmez** — bilinçli tasarım, "istatistiksel gerçek" gibi sunmama ilkesi (Contract §25).

## 7. Calibration Gap (v2)

```text
gap = average_confidence − observed_accuracy
```

Örnek: %76 ortalama güven − %70 gözlenen doğruluk = **+6pp**. Sunum: *"Your confidence is currently 6 points above your observed accuracy"* — asla *"you are overconfident"* gibi kişisel/tanı diliyle değil (Contract §67, Belge 1 §3'teki "psikolojik tanı sistemi değil" ilkesiyle aynı).

## 8. Açıkça v1'e/v2'ye ertelenenler

- Brier dashboard (v2, N≥20-30 sonrası)
- Confidence bucket görselleştirme (v1, N≥10 sonrası)
- Error taxonomy (v3)
- AI reasoning-pattern analizi (v3, deterministik katman oturana kadar asla)
- `alternative` alanı (v1)

## 9. AI'nin bu spesifikasyondaki sınırı

AI calibration hesaplamaz, outcome belirlemez, score uydurmaz. AI yalnız (v3'te) reasoning metnini yorumlar — Contract §30-31, değişmez kural.

---

_Bu belge Contract §22-26, §42, §57'nin uygulanabilir hâlidir. Yeni bir sayı/eşik icat etmez — hepsi Contract'tan._
