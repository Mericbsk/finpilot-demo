# FinPilot — Gerçek Performans & Win Rate Analizi

**Tarih:** 2026-06-11
**Kaynak:** `data/` altındaki gerçek backtest / walk-forward / Monte Carlo / sinyal çözümleme çıktıları
**Amaç:** Pazarlama/funding belgelerindeki iddiaları, sistemin ürettiği **ham ölçüm dosyalarıyla** karşılaştırmak ve dürüst bir performans tablosu çıkarmak.

> ⚠️ **Tek cümlelik özet:** Backtest (in-sample) sonuçları parlak görünüyor, ancak **out-of-sample doğrulama (walk-forward + Monte Carlo + gerçek sinyal çözümleme) istatistiksel olarak anlamlı bir edge gösteremiyor.** Sistemin şu an kanıtlanmış bir kâr üretme yeteneği yoktur.

---

## 1. Kaynak Dosyalar ve Tarihler

| Dosya | Tarih | Ne ölçüyor | Karar |
|-------|-------|-----------|-------|
| [data/profitcore_audit.json](../../../data/profitcore_audit.json) | 2026-05-23 | Gerçek arşiv sinyallerinin 5 günlük sonuç çözümlemesi | **NO EDGE DETECTED** |
| [data/ab_stats_20260419_1345.json](../../../data/ab_stats_20260419_1345.json) | 2026-04-19 | A/B backtest (in-sample, 10.123 kayıt) | B kazandı (in-sample) |
| [data/wf_mc_20260511_1250.md](../../../data/wf_mc_20260511_1250.md) | 2026-05-11 | Walk-forward + Monte Carlo (out-of-sample) | **Overfit / şansa dayalı** |
| [data/finpilot_weekly_report_20260511_1249.md](../../../data/finpilot_weekly_report_20260511_1249.md) | 2026-05-11 | Haftalık otomatik rapor | B ek doğrulama gerektiriyor |
| [data/combined_summary_20260416_1907.json](../../../data/combined_summary_20260416_1907.json) | 2026-04-16 | 13.824 kombinasyon grid search | "S tier" (in-sample) |
| [data/drl_research_state.json](../../../data/drl_research_state.json) | son: 2026-05-11 | DRL ajan baseline metrikleri | Sharpe ~0.05, donmuş |

---

## 2. EN ÖNEMLİ BULGU — Gerçek Sinyal Çözümlemesi (profitcore_audit.json)

Bu, sistemin gerçekten ürettiği sinyallerin (arşivden) 5 gün sonraki gerçek fiyat sonuçlarıyla eşleştirildiği **tek dürüst out-of-sample testtir.** 946 arşiv sinyali, 402 kullanılabilir satır.

| Metrik | Değer | Eşik | Sonuç |
|--------|-------|------|-------|
| Hit rate (win rate) | **%36.8** | >%50 | ❌ |
| Expectancy | **-%1.75** / işlem | >0 | ❌ |
| Profit factor | **0.591** | >1.2 | ❌ |
| Decile lift | **0.728** | >1.3 | ❌ |
| Permütasyon p-değeri | **0.995** | <0.05 | ❌ |
| Verdict | **"NO EDGE DETECTED"** | — | ❌ |

### Decile paradoksu (kritik)
Skor motoru **ters çalışıyor**: en yüksek skorlu sinyaller en kötü performansı gösteriyor.

| Decile | Skor aralığı | n | Win rate | Ort. getiri |
|--------|-------------|---|----------|-------------|
| 10 (en yüksek skor) | 73–89 | 41 | **%26.8** | **-%4.99** |
| 9 | 69–73 | 40 | %30.0 | -%4.83 |
| ... | ... | ... | ... | ... |
| 3 | 51–56 | 40 | %52.5 | -%0.27 |
| 1 (en düşük skor) | 0–47 | 40 | **%70.0** | **+%7.24** |

> Skor ne kadar yüksekse getiri o kadar **düşük**. `decile_lift = 0.728 < 1` olması, skorun rastgeleden de kötü olduğu (negatif sinyal) anlamına gelir. `score_engine` veya `finpilot_score` ağırlıklandırması ters yönde çalışıyor olabilir.

---

## 3. In-Sample vs Out-of-Sample Çelişkisi

### 3a. A/B Backtest (in-sample, 2026-04-19) — PARLAK
- Strateji B: Precision 0.75, Recall 0.80, F1 0.78, Kâr **+$7.342**, Sharpe **8.07**
- t-test p=0.0056, Mann-Whitney p≈0, Cohen's d=0.92 → "istatistiksel olarak anlamlı"

### 3b. Walk-Forward + Monte Carlo (out-of-sample, 2026-05-11) — ÇÖKÜŞ
| Metrik | Strateji A | Strateji B |
|--------|-----------|-----------|
| OOS toplam kâr | **-$950** | **-$736.88** |
| OOS Sharpe | -74.0 | -20.5 |
| Deflated Sharpe (Bailey & de Prado) | -61.8 | **-17.1** (>0.5 olmalı) |
| Kazançlı pencere % | %0 | **%15** |
| IS/OOS korelasyon | -0.11 | **-0.36** (negatif!) |
| Monte Carlo Sharpe p | 0.195 | **0.851** |

> **Yorum:** Negatif IS/OOS korelasyonu (-0.36) ve negatif Deflated Sharpe, parametrelerin geçmiş veriye **overfit** olduğunun klasik işaretidir. In-sample kazanan strateji, out-of-sample para kaybediyor.

### 3c. Haftalık raporun kendi verdict'i (2026-05-11)
> 🟡 "Strateji B ek doğrulama gerektiriyor." DSR=-999, kazançlı pencere %0, MC p=0.08.

---

## 4. DRL Ajan Durumu (drl_research_state.json)

- En iyi 5 PPO ajanı: Sharpe **0.043–0.063** arası (hedef >0.5)
- İterasyon 8'de **donmuş**; `experiment_log: []`, `best_per_agent: {}` boş
- `next_action`: "Optuna ile dd_weight optimize et" — planlanmış ama çalıştırılmamış
- Şubat 2026'dan beri yeni model eğitimi yok (FULL_AUDIT_REPORT bulgusuyla tutarlı)

> DRL bileşeni şu an üretim kararlarına katkı sağlamıyor; deneysel aşamada ve donmuş durumda.

---

## 5. Funding Belgeleriyle Çelişki Kontrolü

| Belge | İddia | Gerçek (data/) | Durum |
|-------|-------|----------------|-------|
| HIBE_FON_DEGERLENDIRME | "Pilot Sharpe 0.057" | DRL Sharpe 0.043–0.063 | ✅ Dürüst |
| FINANZPLAN | "%8 conversion, €38 ARPU" | Canlı kullanıcı/gelir verisi yok | ⚠️ Varsayım |
| Pazarlama (genel) | "Kârlı sinyaller" | profitcore: NO EDGE | ❌ Desteklenmiyor |

> **Uyarı:** Funding/pazarlama materyallerinde "kârlı" veya "kanıtlanmış edge" iddiası kullanılmamalıdır. Mevcut dürüst konum: *"Sinyal üretim ve ölçüm altyapısı çalışıyor; edge henüz kanıtlanmadı, aktif kalibrasyon aşamasında."*

---

## 6. Sonuç ve Öneriler

1. **`score_engine` / `finpilot_score` ters-decile sorununu araştır** — en yüksek skor en kötü getiriyi veriyorsa ağırlıklar veya yön işareti hatalı olabilir (en yüksek öncelikli teknik bulgu).
2. **In-sample metrikleri pazarlamada kullanma.** Sadece out-of-sample (profitcore, walk-forward) rakamları raporla.
3. **DRL'yi dondurulmuş kabul et.** `next_action`'daki Optuna dd_weight çalışması yapılana kadar üretim iddiası yok.
4. **Edge kanıtlanana kadar otomatik trade kapalı kalsın.** Alpaca entegrasyonu paper-trading ile sınırlı tutulmalı.
5. **Tek doğruluk kaynağı:** Haftalık `profitcore_audit.json` + `wf_mc` raporları. Diğer in-sample CSV'ler "araştırma" olarak etiketlenmeli.

---
*FinPilot Performans Denetimi — 2026-06-11 — Kaynak: data/ ham çıktıları*
