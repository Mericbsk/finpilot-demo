# S1 — Short-Interest Change (ΔSI) Direction Test

**Tarih:** 2026-09-18 · **Level:** A (read-only araştırma; hiçbir production/veri değiştirilmedi)
**Pre-registration:** `research/s1_short_interest_direction_2026_09_18.py` docstring (sonuçlardan önce sabitlendi)
**Aday:** S1 (direction_signal_source_scouting_2026_09_18.md) · **Dataset:** EOD-only, target c2c_1d
**Artifact:** `data/backtest_out/s1_short_interest_direction_2026-09-18.json`

---

## 1. Executive Summary

> **ΔSI (short-interest değişimi) 1-günlük yön taşımıyor.** Primary metrik Spearman(ΔSI_pct, c2c_1d) = **+0,0015** (gürültü). Quintile'lar monoton değil. Squeeze leg (aşırı SI + SI artışı) **negatif** (−0,30, hit %45,6). Walk-forward 3 pencerede de sıfır/negatif.

**Görünür pozitif sinyal (random control'da top-quintile %99,7 percentile) tamamen outlier + stale-data artefaktı** — winsorize/fresh-only yapınca kayboluyor. **H0 reddedilemedi; H1a ve H1b ikisi de desteklenmedi.**

## 2. Veri & Kapsam

- Toplam EOD satır: 40.014 · ΔSI'lı satır: **29.554 (%73,9 coverage)** · 1.156 sembol
- FINRA bi-weekly; **SI lag medyan = 17 gün** (önemli sınır — aşağıda)
- As-of join (lookahead yok): her scan_date için ≤ o gün bilinen en son ΔSI

## 3. Primary Result (Spearman)

| Metrik | Değer | Yorum |
|---|---:|---|
| Spearman(ΔSI_pct, c2c_1d) | **+0,0015** | gürültü |
| Spearman(ΔSI_raw, c2c_1d) | +0,0046 | gürültü |
| Pearson | +0,0004 | gürültü |

## 4. Quintile (ΔSI_pct → c2c_1d)

| Quintile | n | mean | median | hit |
|---|---:|---:|---:|---:|
| Q1 (SI en çok düşen) | 5.917 | +0,60 | −0,12 | 0,471 |
| Q2 | 5.918 | +3,17 | −0,16 | 0,468 |
| Q3 | 5.901 | +0,05 | −0,05 | 0,489 |
| Q4 | 5.929 | +0,02 | 0,00 | 0,497 |
| Q5 (SI en çok artan) | 5.889 | +6,65 | −0,14 | 0,468 |

**Non-monotonic.** Q5'in +6,65 mean'i **medyan −0,14 ve hit %46,8** ile çelişiyor → outlier kuyruğu. Winsorize edince Q5 mean **−0,29**'a düşer (ters döner). Q2'nin +3,17'si de aynı outlier etkisi.

## 5. Squeeze Leg (H1b)

Aşırı SI (top decile) + pozitif ΔSI:
- n=1.942 · mean **−0,296** · hit **%45,6** · (rest mean +2,26)

**Squeeze hipotezi desteklenmedi** — aşırı short + artan short daha kötü, daha iyi değil.

## 6. Random Control (görünür sinyal = artefakt)

Top-ΔSI-quintile vs aynı-gün random: real +6,62 vs random +1,93, **percentile %99,7** — görünürde güçlü. **AMA** bu, Q5'in outlier kuyruğunun aynısı; winsorize/fresh-only ile kayboluyor. Penny/aşırı-getiri hisseleri hem yüksek ΔSI hem yüksek |c2c_1d| üretiyor (yanıltıcı ortak nedensellik).

## 7. Walk-Forward (zaman içinde tutarlılık)

| Pencere | OOS n | Spearman | SI lag medyan |
|---|---:|---:|---:|
| W2 | 1.828 | −0,002 | 5 gün |
| W3 | 1.514 | −0,010 | 11 gün |
| W4 | 2.217 | −0,015 | 16 gün |

Sıfır/negatif, pencereden pencereye tutarsız. **SI lag arttıkça (stale data) sinyal daha da zayıflıyor** — bi-weekly gecikme sinyali öldürüyor olabilir.

## 8. Robustness

- **Winsorized quintiles:** [−0,11, −0,23, −0,11, −0,02, −0,29] → tamamen düz/negatif.
- **Fresh-only (SI lag ≤14 gün):** n=12.687, Spearman +0,0056 — hâlâ gürültü. Fresh top-quintile mean +0,04 vs rest +0,47 (ters).

## 9. Negatif Bulgular (saklanmadı)

1. ΔSI 1-günlük yön taşımıyor (Spearman ≈ 0).
2. Squeeze leg negatif (beklenen ters).
3. Görünür pozitif sinyal outlier/stale artefaktı.
4. Bi-weekly gecikme (medyan 17 gün) sinyali öldürüyor olabilir.

## 10. Sınırlamalar

- **Stale data:** FINRA 2026-06-15'te bitiyor; research 2026-08-05'e gidiyor → son haftalarda SI stale (medyan lag 17 gün).
- **Coverage:** %73,9 (1.156/1.968 sembol) — SI'sız semboller hariç.
- **Yalnızca 1 gün horizon (c2c_1d)** — ΔSI belki daha uzun horizon'da çalışır (bi-weekly veri 1-gün için çok kaba olabilir).

## 11. Sonuç / Karar

```
S1 (ΔSI) = REJECTED (1-gün horizon)
```
Bu `NOT_TESTED` değil — gerçekten test edildi ve destek bulunamadı. **Ama dikkat:** bu yalnızca **1-gün c2c_1d** üzerinde. ΔSI bi-weekly doğası gereği 1-gün için çok kaba olabilir; **5-gün (c2c_5d) ayrı bir soru** olurdu (bu çalışmada test edilmedi — kapsam dışı).

## 12. Sonraki aday (scouting planına göre)

| Aday | Sonuç |
|---|---|
| **S1 ΔSI** | ❌ REJECTED (1d) |
| S2 Insider (Form 4) | sıradaki — ama alım/satım parse **data work** gerekir |
| S4 News sentiment | veri var ama skor anlamı belirsiz (0,99 sabit — önce doğrula) |
| S3 8-K events | ton sınıflandırma gerekir |
| S5 float/short_pct | snapshot — zayıf |

**Multiple-testing notu (§Bonferroni):** 5 aday × metrik → tek başına p<0,05 yeterli değildi; zaten anlamlı sonuç yok.

**Dürüst kapanış:** S1'in 1-gün yön taşımadığı kanıtlandı. Bu değerli — bu kaynağı 1-gün yön için eledik. "ΔSI daha uzun horizon'da (5d) çalışır mı?" ayrı bir pre-registered soru olarak açık.

## Governance
- Read-only; hiçbir production/veri/flag değiştirilmedi. Pre-registered; negatif sonuç raporlandı. Cherry-pick yok (Q5 outlier'ı açıkça gösterildi, gizlenmedi).
