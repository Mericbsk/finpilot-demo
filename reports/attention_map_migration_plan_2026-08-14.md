# FinPilot Dikkat Haritası Pivotu — Uçtan Uca Uygulama Planı

Date: 2026-08-14
Level: B (ürün değişikliği; Meriç onayı gerekli)
Status: DRAFT — onay bekliyor
Authority: `docs/governance/decision-log.md` (pivot kaydı), `reports/attention_map_research_2026-08-14.md` (kanıt)

---

## 0. Neden Bu Pivot?

| Kanıt | Kaynak |
|---|---|
| Score/entry_ok ileri getiriyi tahmin etmiyor (6 bağımsız yol) | Master Audit |
| Canlı sıralama alanı (ranking_score) daha da kötü | Ranking Score Re-test |
| entry_ok rastgele seçimden daha kötü | Winner Anatomy |
| Hiçbir feature zaman-içi tutarlı değil | F3 Stability |
| Olağandışılık tespiti çalışıyor (lift 1.26-2.4x, precision %62) | Attention Map Research |

**Sonuç:** "Tahmin motoru" çerçevesi kanıtlanamadı. "Dikkat haritası" çerçevesi kanıtlandı. Pivot, ürünün kanıtla uyumlu hale gelmesi.

---

## 1. Mevcut Sistem Haritası

### Yayın yüzeyleri

| Yüzey | Dosya | Ne yapıyor | Değişiklik gerekli mi? |
|---|---|---|---|
| Landing page | `web/src/app/page.tsx` | EditionArticle, DailyDouble, Newsroom, LedgerStrip | **Evet** — "candidate" → "attention" dili |
| Demo page | `web/src/app/demo/page.tsx` | Snapshot candidates, grade, score, entry_ok | **Evet** — tamamen yeniden çerçeve |
| Methodology | `web/src/app/methodology/page.tsx` | "How we scan, grade, verify" | **Evet** — metodoloji açıklaması güncellenmeli |
| Premium page | `web/src/app/premium/page.tsx` | "Morning candidates", "Grade B" | **Evet** — ürün vaadi değişiyor |
| Classroom | `web/src/app/classroom/page.tsx` | Grade-guessing oyunu | **Evet** — oyun mekaniği değişebilir |
| Dashboard | `web/src/app/dashboard/` | agent, ai-lab, analysis, backtest | **Kısmen** — dashboard internal, public değil |
| Telegram | `distribution/templates.py` | Grade emoji, prob_band, candidate list | **Evet** — mesaj formatı değişiyor |
| Snapshot builder | `distribution/snapshot_builder.py` | Grade A/B/C, ranking_score, candidate selection | **Evet** — çekirdek değişiklik |
| Prepublish gate | `distribution/prepublish_gate.py` | Contract validation | **Evet** — yeni contract alanları |
| Glossary | `distribution/glossary.py` | Terim tanımları | **Evet** — yeni terimler |
| Scanner | `scanner/evaluate.py` | composite_score, legacy_quality_score, ranking_score, entry_ok | **Hayır** — hesaplama aynı, sunum değişiyor |
| API | `api/routers/` | scan, history, execution | **Kısmen** — yeni endpoint'ler |

### Veri akışı

```
Scanner (evaluate.py)
  → entry_ok, composite_score, ranking_score, ATR, RVOL, gap, dist_52w, lottery, squeeze
    → Snapshot Builder (snapshot_builder.py)
      → Grade A/B/C, ranking, candidate selection
        → Prepublish Gate (prepublish_gate.py)
          → Web (page.tsx, demo/page.tsx)
          → Telegram (templates.py)
          → API (distribution.py)
```

**Değişiklik noktası:** Snapshot Builder — candidate selection yerine attention scoring.

---

## 2. Yeni Çekirdek: Attention Score

### Tanım

Her taranan hisse için bir **Attention Score** hesapla (0-100):

```
Attention Score = weighted sum of unusualness flags
```

**Formül (dondurulmuş, kanıt-tabanlı):**

| Flag | Eşik | Ağırlık | Kanıt |
|---|---|---:|---|
| Big Gap | \|gap\| ≥ 3% | 25 | Lift 1.59x (en yüksek) |
| Volatility Spike | ATR ≥ 6% | 25 | Lift 1.55x |
| Volume Spike | RVOL ≥ 2.0 | 15 | Lift 1.26x |
| Far from High | dist_52w < 0.3 | 15 | Lift 1.48x |
| High Lottery | lottery ≥ 0.6 | 10 | Lift 1.51x |
| Squeeze | squeeze ≥ 0.5 | 10 | Lift 1.27x |

**Attention Tier:**
- **High Attention (🔴):** score ≥ 50 (birden fazla flag aktif)
- **Watch (🟡):** score 25-49 (tek flag aktif)
- **Normal (⚪):** score < 25 (olağan)

### Önemli kurallar

1. **Yön yok.** Attention Score "bu hisseye bak" diyor, "bu hisse yükselecek" demiyor.
2. **Grade A/B/C kaldırılıyor.** Yerine Attention Tier (High/Watch/Normal) geliyor.
3. **Probability band kaldırılıyor.** "~60% çalıştı" ifadesi artık kullanılmayacak — çünkü kanıtlanmadı.
4. **entry_ok kaldırılıyor.** Yerine Attention Score ≥ 25 geliyor.
5. **Score gösterilmiyor.** Kullanıcı "neden bu hisse dikkat çekici" görüyor, ham skoru değil.

---

## 3. Değişiklik Listesi

### 3.1 Scanner (evaluate.py) — DEĞİŞİKLİK YOK

Scanner'ın hesapladığı feature'lar aynı kalıyor. Sadece snapshot builder'da nasıl sunuldukları değişiyor.

### 3.2 Snapshot Builder (snapshot_builder.py) — ÇEKIRDEK DEĞİŞİKLİK

**Mevcut:** `_grade_of()` → Grade A/B/C, `_sort_key()` → ranking_score

**Yeni:** `_attention_score()` → 0-100, `_attention_tier()` → High/Watch/Normal

```python
def _attention_score(row: dict) -> int:
    """Compute attention score from unusualness flags. Not predictive."""
    score = 0
    if abs(row.get("gap_pct", 0) or 0) >= 3:
        score += 25
    if (row.get("atr_pct_real") or 0) >= 6:
        score += 25
    if (row.get("rvol") or 0) >= 2.0:
        score += 15
    if (row.get("dist_52w_high") or 1.0) < 0.3:
        score += 15
    if (row.get("lottery_factor") or 0) >= 0.6:
        score += 10
    if (row.get("squeeze_factor") or 0) >= 0.5:
        score += 10
    return score

def _attention_tier(score: int) -> str:
    if score >= 50: return "high"
    if score >= 25: return "watch"
    return "normal"
```

**Sıralama:** Attention Score'a göre (yüksek → düşük). Eşitlik durumunda ATR'a göre.

**Candidate selection:** `selection_eligible` yerine `attention_score >= 25` kullanılacak.

### 3.3 Prepublish Gate (prepublish_gate.py) — CONTRACT GÜNCELLEMESİ

Yeni zorunlu alanlar:
- `attention_score` (int, 0-100)
- `attention_tier` ("high" | "watch" | "normal")
- `attention_reasons` (list of active flags)

Kaldırılan zorunlu alanlar:
- `conviction_prob` (kanıtlanmadı)
- `prob_band` (kanıtlanmadı)

Korunan alanlar:
- `symbol`, `price`, `atr_pct_real`, `rvol`, `gap_pct`, `dist_52w_high`, `lottery_factor`, `squeeze_factor`

### 3.4 Web — Landing Page (page.tsx)

**Mevcut:** EditionArticle → candidates (Grade A/B/C, prob_band)

**Yeni:** EditionArticle → attention_items (Attention Tier, reasons)

**Değişiklik:**
- `candidates` → `attention_items`
- `grade` → `attention_tier`
- `prob_band` → kaldırıldı
- `rationale` → `attention_reasons` (insan dilinde: "Yüksek volatilite + büyük gap")

**Yeni bileşen:** `AttentionMap.tsx` — günlük dikkat haritası görseli

### 3.5 Web — Demo Page (demo/page.tsx)

**Mevcut:** Grade A/B/C, score, entry_ok, stop_loss, take_profit

**Yeni:** Attention Tier, attention_reasons, unusualness_metrics

**Değişiklik:**
- `grade` → `attention_tier`
- `score` → kaldırıldı (kullanıcı ham skoru görmüyor)
- `entry_ok` → kaldırıldı
- `stop_loss`, `take_profit` → kaldırıldı (trade sinyali değil)
- `attention_reasons` → yeni (hangi flag'ler aktif)

### 3.6 Web — Methodology Page

**Mevcut:** "How we scan, grade, verify and score"

**Yeni:** "How we detect unusual market activity"

**Değişiklik:** Metodoloji açıklaması tamamen yeniden yazılacak:
- "We don't predict which stocks will go up"
- "We detect which stocks are behaving unusually"
- "Unusual ≠ good. Unusual = worth watching."

### 3.7 Telegram (templates.py)

**Mevcut:** Grade emoji (🟢🔵⚪), prob_band, candidate list

**Yeni:** Attention emoji (🔴🟡⚪), attention_reasons, attention list

**Yeni mesaj formatı:**
```
🔴 Yüksek Dikkat: NBIS
   ATR=13.3%, Gap=-4.8%, RVOL=1.54
   Bu hisse olağandışı hareket gösteriyor.

🟡 İzleme: FCEL
   ATR=13.3%, Gap=-6.3%
   Yüksek volatilite tespit edildi.
```

### 3.8 Glossary (glossary.py)

**Yeni terimler:**
- `attention_score`: "Bir hissenin olağandışı davranış seviyesi — tahmin değil, dikkat ölçümü"
- `attention_tier`: "Dikkat seviyesi: yüksek / izleme / normal"
- `unusualness`: "Hissenin kendi geçmişine veya evrene göre sapması"

**Güncellenen terimler:**
- `grade`: "Kaldırıldı — yerine attention_tier"
- `conviction_prob`: "Kaldırıldı — kanıtlanmadı"
- `entry_ok`: "Kaldırıldı — yerine attention_score >= 25"

### 3.9 API (distribution.py)

**Yeni endpoint:** `GET /api/v1/attention/{date}`

```json
{
  "date": "2026-08-14",
  "universe": 1812,
  "attention_count": 25,
  "high_attention_count": 13,
  "items": [
    {
      "symbol": "NBIS",
      "price": 183.01,
      "attention_score": 65,
      "attention_tier": "high",
      "attention_reasons": ["volatility_spike", "big_gap"],
      "metrics": {
        "atr_pct": 13.3,
        "gap_pct": -4.8,
        "rvol": 1.54
      }
    }
  ]
}
```

---

## 4. Uygulama Sırası

### Faz 1: Çekirdek (1-2 gün)

1. `snapshot_builder.py`'e `_attention_score()` ve `_attention_tier()` ekle
2. `prepublish_gate.py`'e yeni contract alanları ekle
3. `glossary.py`'e yeni terimler ekle
4. Unit testler yaz

### Faz 2: Web (2-3 gün)

5. `page.tsx` — EditionArticle'ı attention_items'a çevir
6. `demo/page.tsx` — Attention Tier gösterimi
7. `methodology/page.tsx` — metodoloji açıklaması güncelle
8. Yeni `AttentionMap.tsx` bileşeni

### Faz 3: Telegram + API (1 gün)

9. `templates.py` — yeni mesaj formatı
10. `distribution.py` — yeni endpoint

### Faz 4: Doğrulama (1 gün)

11. Prepublish gate testi
12. End-to-end snapshot testi
13. Web görsel testi
14. Telegram mesaj testi

### Faz 5: Göç (1 gün)

15. Feature flag ile eski/yeni sistem arasında geçiş
16. Rollback planı hazır
17. Meriç onayı ile canlıya al

---

## 5. Rollback Planı

**Feature flag:** `FINPILOT_ENABLE_ATTENTION_MAP=0` (default: eski sistem)

**Rollback adımları:**
1. Flag'i 0'a çek
2. Eski snapshot formatı geri yükle
3. Web ve Telegram eski formata döner
4. Veri kaybı yok — her iki format da saklanıyor

---

## 6. Başarı Kriterleri

| Metrik | Hedef | Ölçüm |
|---|---|---|
| Attention precision | ≥60% | Flag edilen hisselerin %60'ı gerçekten büyük hareket yapmalı |
| Coverage | ≥50% | Tüm büyük hareketlerin %50'si yakalanmalı |
| Kullanıcı kafa karışıklığı | 0 | "Bu hisse yükselecek mi?" sorusu gelmemeli |
| Compliance | PASS | Hiçbir "al/sat" dili, hiçbir "tahmin" iddiası |

---

## 7. Riskler

| Risk | Önlem |
|---|---|
| Kullanıcı hâlâ "tahmin" bekliyor | Her mesajda "bu bir tahmin değil" uyarısı |
| Attention Score yanlış kalibre | İlk hafta gölge modda çalıştır, sonra canlıya al |
| Eski kullanıcılar Grade'i özlüyor | Geçiş döneminde her iki formatı göster |
| Compliance "dikkat" ifadesini sorguluyor | Glossary'de "dikkat ≠ tavsiye" açıkça yazılmalı |

---

## 8. Onay Gerektiren Kararlar

| # | Karar | Level | Kim |
|---|---|---|---|
| 1 | Attention Score formülü (ağırlıklar) | B | Meriç |
| 2 | Grade A/B/C'nin kaldırılması | B | Meriç |
| 3 | entry_ok'un kaldırılması | B | Meriç |
| 4 | Telegram mesaj formatı değişikliği | B | Meriç |
| 5 | Canlıya geçiş | C | Meriç |

---

## 9. Zaman Çizelgesi

| Gün | İş |
|---|---|
| 1-2 | Çekirdek (snapshot_builder, prepublish_gate, glossary) |
| 3-4 | Web (landing, demo, methodology) |
| 5 | Telegram + API |
| 6 | Doğrulama + test |
| 7 | Gölge modda canlı test |
| 8 | Meriç onayı → canlı geçiş |

---

**Bu plan Level B'dir — Meriç onayı olmadan uygulanamaz. Hiçbir kod değişikliği yapılmadı. Locked OOS açılmadı.**
