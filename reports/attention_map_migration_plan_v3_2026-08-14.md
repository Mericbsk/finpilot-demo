# FinPilot Dikkat Haritası Pivotu — Uçtan Uca Uygulama Planı (v3, Temiz)

Date: 2026-08-14
Level: B (ürün değişikliği; Meriç onayı gerekli)
Status: DRAFT v3 — canlı CSV doğrulandı, formül tek ve net
Authority: `docs/governance/decision-log.md`, `reports/attention_map_research_2026-08-14.md`, `data/backtest_out/attention_score_validation_2026-08-14.json`

---

## 0. Kanıt

**Kaynak:** `research/attention_score_validation_2026_08_14.py` → `data/backtest_out/attention_score_validation_2026-08-14.json`

| Metrik | Değer | Kaynak |
|---|---|---|
| Matched-control p | 0.055 | `attention_score_validation_2026_08_14.py` → artifact |
| Precision | 61.8% | artifact |
| Coverage | 52.5% | artifact |
| Lift | 1.52x | artifact |
| Ay-ay lift | 1.70-3.34x | artifact — **5 ay kapsamlı** (2025-09, 2026-04/05/06/07); 2025-10/11/12 ve 2026-01/02/03 veri yetersiz (n<20) |
| Day-clustered 95% CI | [6.39, 7.54] | artifact |

**Ne ölçüyor:** Attention Score ≥ 25 olan hisseler, aynı gün rastgele hisselerden **4.29pp daha büyük |5g| hareket** gösteriyor. Yön yok, hareket var.

**Ay-ay kapsam notu:** "Ay-ay lift tutarlı" ifadesi 11 ayın değil **5 ayın** hikayesi. 2025-10/11/12 ve 2026-01/02/03'te attention grubu n<20 — veri boşluğu var. 5 ayda lift 1.70-3.34x, hepsi pozitif.

---

## 1. Attention Score Formülü

### 1.1 Export verisiyle (doğrulanmış)

```python
def attention_score(row: dict) -> int:
    score = 0
    if abs(row.get("gap_pct", 0) or 0) >= 3:       score += 25  # Big Gap
    if (row.get("atr_pct_real") or 0) >= 6:          score += 25  # Volatility Spike
    if (row.get("rvol") or 0) >= 2.0:                score += 15  # Volume Spike
    if (row.get("dist_52w_high") or 1.0) < 0.3:      score += 15  # Far from High
    if (row.get("lottery_factor") or 0) >= 0.6:      score += 10  # High Lottery
    if (row.get("squeeze_factor") or 0) >= 0.5:      score += 10  # Squeeze
    return score
```

### 1.2 Canlı scanner'da (üretim)

**Canlı CSV'de VAR olan alanlar** (`data/shortlists/shortlist_20260814_1157.csv` doğrulandı):

| Alan | Aralık | Attention flag |
|---|---|---|
| `volume_multiple` | 0.35-2.36 | ≥1.5 → +25 |
| `ann_vol_pct` | 25-75% | ≥60 → +25 |
| `lottery_factor` | 0.2-0.88 | ≥0.6 → +15 |
| `overnight_gap_factor` | 0-0.32 | ≥0.1 → +15 |
| `ema_gap_pct` | -35 to -0.7% | ≤-10 → +10 |

**Canlı CSV'de YOK olan alanlar (hesaplanmalı):**

| Alan | Nasıl | Nereden |
|---|---|---|
| `dist_52w_high` | `Close / max(High, 252)` | `scanner/features.py` — yeni |
| `gap_pct` | `(Open - prev_Close) / prev_Close * 100` | `scanner/features.py` — yeni |
| `rvol_daily` | `Volume / avg(Volume, 20)` | `scanner/features.py` — yeni |
| `squeeze_factor` | Zaten hesaplanıyor | Export'a eklenmeli |

### 1.3 Üretim formülü (canlı alanlarla)

```python
def attention_score(row: dict) -> int:
    score = 0
    if (row.get("volume_multiple") or 0) >= 1.5:     score += 25
    if (row.get("ann_vol_pct") or 0) >= 60:           score += 25
    if (row.get("lottery_factor") or 0) >= 0.6:       score += 15
    if (row.get("overnight_gap_factor") or 0) >= 0.1:  score += 15
    if (row.get("ema_gap_pct") or 0) <= -10:           score += 10
    if (row.get("squeeze_factor") or 0) >= 0.5:        score += 10
    return score
```

**Kritik uyarı:** Üretim formülü (§1.3) ile export formülü (§1.1) **farklı alanlar** kullanıyor. Eşdeğerliği kanıtlanmadı. Canlı formülün doğrulanması için **canlı veriyle yeniden test** gerekli (Faz 1c).

### 1.4 Attention Tier

| Score | Tier | Emoji |
|---|---|---|
| ≥50 | High | 🔴 |
| 25-49 | Watch | 🟡 |
| <25 | Normal | ⚪ |

---

## 2. Değişiklik Listesi

### 2.1 Scanner (features.py + evaluate.py)

**Yeni fonksiyonlar (`scanner/features.py`):**
- `compute_dist_52w_high(df_1d)` → `Close / max(High, 252)`
- `compute_gap_pct(df_1d)` → `(Open - prev_Close) / prev_Close * 100`
- `compute_rvol_daily(df_1d)` → `Volume / avg(Volume, 20)`

**Export'a eklenecek alanlar (`scanner/evaluate.py` return dict):**
- `dist_52w_high` (float)
- `gap_pct` (float)
- `rvol_daily` (float)
- `squeeze_factor` (float — zaten hesaplanıyor, export'a yazılmıyor)

### 2.2 Snapshot Builder (snapshot_builder.py)

- `_grade_of()` → `_attention_tier()`
- `_sort_key()` → attention_score'a göre sırala
- `Grade A/B/C` → `Attention Tier High/Watch/Normal`
- `prob_band` → kaldırıldı
- `entry_ok` → `attention_score >= 25`

### 2.3 Schema (schema.py) — v3

Yeni zorunlu alanlar: `attention_score`, `attention_tier`, `attention_reasons`
Kaldırılan: `grade`, `prob_band`

### 2.4 Prepublish Gate (prepublish_gate.py)

Schema v3'e göre doğrulama.

### 2.5 Web, Telegram, Glossary, API

- `grade` → `attention_tier`
- `prob_band` → kaldırıldı
- `entry_ok` → `attention_score >= 25`
- Yeni terimler: `attention_score`, `attention_tier`, `unusualness`

---

## 3. Zaman Çizelgesi

| Gün | İş |
|---|---|
| 1 | Faz 0: Export doğrulama **(tamamlandı ✓)** |
| 2-3 | Faz 1a: Scanner features (3 yeni fonksiyon) |
| 4 | Faz 1b: Scanner export (4 yeni alan) |
| 5 | Faz 1c: **Canlı veriyle formül doğrulama** |
| 6-8 | Faz 2: Web |
| 9 | Faz 3: Telegram + API |
| 10 | Faz 4: Doğrulama |
| 11 | Faz 5: Gölge test |
| 12 | **Meriç onayı → canlı geçiş** |

---

## 4. Onay Gerektiren Kararlar

| # | Karar | Level |
|---|---|---|
| 1 | Attention Score formülü (§1.3) | B |
| 2 | 4 yeni scanner hesaplaması | B |
| 3 | Grade A/B/C kaldırılması | B |
| 4 | entry_ok kaldırılması | B |
| 5 | Schema v3 | B |
| 6 | Canlıya geçiş | C |

---

**Bu plan Level B'dir — Meriç onayı olmadan uygulanamaz. Hiçbir kod değişikliği yapılmadı. Locked OOS açılmadı.**
