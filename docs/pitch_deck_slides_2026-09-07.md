# FinPilot × FinSense — Sunum (13 Slayt)
**Üretim tarihi:** 2026-09-07 · **Kaynak:** `pitch_deck_presentation_spec_2026-09-07.md` v1.0
**Omurga:** "We are not asking capital to prove that our system works. We are using capital to find out, under real market conditions, whether it actually does."

---
---

# SLIDE 1 — FinPilot

## Building the AI Trading Engine of the Future

Viyana merkezli · Tek kurucu · Finansal zeka şirketi
Meriç Başak · 2026

---

---
---

# SLIDE 2 — Why Now: The Future of Trading

## Piyasalar algoritmikleşiyor — bir sonraki aşama emir otomasyonu değil

**Algıla → Anla → Seç → Riskle → Yürüt → Öğren**

3 trend bir araya geliyor:
1. **AI** — reasoning, ajanlar, otonom iş akışları artık mümkün
2. **Markets** — daha hızlı, daha veri yoğun, daha algoritmik
3. **Infrastructure** — büyük fonların veri+compute altyapısı artık küçük ekiplerin erişiminde

> Solo founder ≠ solo company. Lean by design, not alone by necessity.
> — Carta 2025: tek-kurucu oranı %23,7 → %36,3 **[V]**

---
---

# SLIDE 3 — What We Have: 5,216 Historical Signals

## A Measured Signal Hypothesis

| Metrik | Değer |
|---|---:|
| Hit rate | **%30,16** |
| Historical mean (barrier-based expectancy) | **+%0,40** |
| Medyan getiri | **-%0,64** |
| Ortalama kazanç | **+%4,28** |
| Ortalama kayıp | **-%1,27** |
| Asimetri | **3,36×** |

> **Why is the mean positive while the median is negative?**
> Because the median reflects our **current exit architecture**, not the market's ceiling. The payoff structure is asymmetric by design — small controlled losses, occasional outsized captures. The gap between what we capture and what the market offers is the research opportunity (see next slide).

**What this does NOT mean:**
- Gerçekleşmiş yatırım getirisi değildir
- Gerçek para ile işlem yapılmamıştır
- Bağımsız OOS doğrulaması bekliyor

*[V] signals_archive.resolved_pct_barrier · 2026-09-02 canlı sorgu*

---
---

# SLIDE 4 — What Did We Actually Discover?

## Capture vs MFE

### SOL — What the system captured (5,216 signals)

| Getiri aralığı | Sayı | Oran |
|---|---:|---:|
| < -%10 | 5 | %0,10 |
| -%10 – -%5 | 48 | %0,92 |
| -%5 – %0 | 3.590 | %68,83 |
| %0 – %2 | 446 | %8,55 |
| %2 – %5 | 699 | %13,40 |
| %5 – %10 | 329 | %6,31 |
| %10 – %20 | 79 | %1,51 |
| ≥%20 | 20 | %0,38 |

Maksimum: **%49,29** (barrier/TP-SL yapısal sınırı)

### SAĞ — What the market offered (ayrı çalışma, 46,581)

- Ortalama MFE: **%4,83** vs yakalanan **+%0,37**
- **111 observations reached ≥100% MFE** (%0,24)

> **Market opportunity → Current capture**

> 111 sinyal tepe noktasında +%100'ü aştı — ama sistem barrier'da çıktığı için yakalanan ortalama +%0,37. **Aradaki fark bizim roadmap'imiz.**

*MFE ≠ yakalanan getiri. İki panel ayrı dataset; birleştirilmez. Kuyruk temizlendi (split artefaktları hariç).*

---
---

# SLIDE 5 — What Doesn't Work? — Red Team Results

## Negatif sonuçları yayınlıyoruz — ürünün temeli bu

- Skor ↔ ileri getiri: **rho = 0,013–0,019** — neredeyse ilişkisiz
- Brier skill: **-0,019 / -0,030** — bazı testlerde rastgeleden kötü
- Adverse selection: eligible **-%0,35/-%0,49** vs rejected **+%1,45/+%0,07**
- Outlier dependence: üst %1 çıkarılınca **+%1,40 → -%0,37**
- 3.120 TP/SL konfigürasyonunda küresel kanıt yok; **locked OOS kasıtlı olarak kapalı tutuldu (by design)**

> ### RED TEAM
> **We actively tried to disprove our own signal.**
> **8 independent direction-prediction approaches failed.**
> — `decision-log.md` (2026-09-03), `experiment_review_board_exp1_2026-09-03.md`

*[V] 11 Ağustos 2026 sentezi · 48.727 path · CPCV/PBO/White RC/Hansen SPA*

---
---

# SLIDE 6 — The Opportunity: Better Decision Architecture

## The Opportunity Is Not More Signals — It's Better Decisions

**Signal → Entry → Regime → Position → Exit → Execution**

> The market sometimes moves substantially in our favor. The current architecture does not consistently capture that movement.
> — MFE %4,83 vs captured +%0,37

Sorun sinyal keşfi değil, **karar mimarisi**.

---
---

# SLIDE 7 — Where Funding Goes: €10K → Capabilities

## "We are not buying hardware. We are buying capabilities."

| Kalem | Ne | Maliyet |
|---|---|---:|
| Yerel donanım | NVIDIA DGX Spark / ASUS GX10 (GB10, 128GB) | ~€4.700 |
| Canlı veri | Polygon.io Advanced (4 ay pilot) | ~€730 |
| Bulut compute | RunPod (burst/yedek, 4 ay) | ~€200 |
| Execution/izleme | Hetzner VPS (12 ay) | ~€120 |
| Broker veri | IBKR (12 ay) | ~€150 |
| Şirket kaydı + muhasebe | Einzelunternehmen (WKO) | ~€500 |
| Yazılım lisansları | — (12 ay) | ~€150 |
| Runway/tampon | — | ~€3.450 |
| **TOPLAM** | | **€10.000** |

- Compute → faster research, larger simulations, local AI inference
- Data → real-time validation, realistic execution modelling
- Cloud → scalable experiments, continuous paper trading

> **"We are buying better data to find out whether the signal is real — before anyone's capital depends on it."**

*[S] Örnek dağılım — kesin tur değil. Kaynak: Polygon, RunPod, NVIDIA, Hetzner, IBKR (2026)*

---
---

# SLIDE 8 — The Data Advantage: Reducing Unknowns

## The goal is not "more data". The goal is fewer unknowns.

**Bugünkü stack (doğrulanmış):**
- yfinance — ücretsiz, gecikmeli fiyat
- EODHD — fundamentals (flag-gated)
- SEC EDGAR — catalyst pipeline (pilot-validated; full-universe refresh in progress)

**Hedef — üç seviye:**

| Seviye | İçerik |
|---|---|
| **LEVEL 1 — Market Truth** | tick, intraday, corporate actions, volume/liquidity |
| **LEVEL 2 — Market Context** | news, fundamentals, analyst revisions, volatility |
| **LEVEL 3 — Execution Truth** | spread, slippage, latency, fills, transaction costs |

---
---

# SLIDE 9 — From Signal to Autonomous Trading

## Data → Regime → Strategy → Meta-Ranker → Risk → Execution → Learning

> **Backtest performance becomes meaningful only after execution costs, slippage and out-of-sample behavior are validated.**

Her aşama bir audit artifact yazar. Herhangi bir gün, sinyal→kanıt→karar→sonuç zinciriyle tekrar oynatılabilir.

---
---

# SLIDE 10 — 12-Month GO/NO-GO Roadmap

**Ay 0-3 — Altyapı + Araştırma:** veri, donanım, backtesting, execution engine
**Ay 3-6 — Doğrulama:** walk-forward, OOS, maliyet+slippage, paper trading

## Ay 6 — GO/NO-GO KAPISI

🟢 **GO** if: pozitif net expectancy (maliyet sonrası) · kabul edilebilir drawdown · OOS geçti · rejimler arası istikrar · paper/live tutarlılık

🔴 **NO-GO** if: edge OOS'ta kaybolur · maliyetler expectancy'yi siler · istikrarsızlık sürer · drawdown kabul edilemez

> **No additional trading capital deployed.**

**Ay 6-9:** Gözetimli canlı (küçük sermaye, insan onayı)
**Ay 9-12:** Kademeli otonomi — *"Toward autonomy — not blind autonomy."*

---
---

# SLIDE 11 — FinSense: The Longer-Term Platform

### *(Parallel track — not part of this raise)*

**İki ürün, tek teknoloji:**

**FinPilot Trading Intelligence** → near-term: research, validation, trading engine, cash-flow potential
↓ *Shared: AI reasoning · financial intelligence · agent architecture · calibration/learning*
**FinSense** → long-term: consumer financial reasoning, financial education, scalable SaaS

**Büyüme senaryosu [S — illüstratif]:**
- Yıl 1: Pilot + erken benimseyenler
- Yıl 2: Ürün-pazar uyumu
- Yıl 3 (senaryo): 40-50K kullanıcı → 50.000 × €12 × 12 = **€7,2M ARR potansiyeli**

> *This is a scenario, not a forecast.* Medyan abonelik ~€13/ay, yıl-1 retention <%30 (RevenueCat 2026).

---
---

# SLIDE 12 — What We Know / What We Don't Know Yet

| We Know | We Don't Know Yet |
|---|---|
| 5,216 historical signals tested | Live profitability |
| Historical asymmetry observed | True execution edge |
| Large MFE events exist (separate study) | How much MFE is realistically capturable |
| Several approaches failed | Which regime-specific approach wins |
| Current scoring has weaknesses | Robust OOS performance |
| Research infrastructure exists | Long-term autonomous performance |

> **The purpose of this investment is to answer the right column.**

---
---

# SLIDE 13 — The Opportunity

> "We are not trying to build another stock screener. We are building an AI system that can observe markets, reason about opportunities, manage risk, execute decisions and learn from outcomes."

## FinPilot — From financial data to autonomous financial intelligence.

> Başarılı olursak: doğrulanmış, küçük ölçekli bir gelir kalemi kazanırız. Olmazsa: disiplinli şekilde denemiş, öğrenmiş ve sermayeyi korumuş oluruz. Her adım, açık raporlamayla ilerler.

---

> **"We are not asking capital to prove that our system works. We are using capital to find out, under real market conditions, whether it actually does."**
