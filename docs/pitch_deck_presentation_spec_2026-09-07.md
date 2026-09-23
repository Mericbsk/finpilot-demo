# FinPilot × FinSense — Presentation-Generation Specification

**Sürüm:** 1.0 · **Tarih:** 2026-09-07 · **Amaç:** Notebook/slayt üretim aracına ham girdi
**Level:** A (içerik spesifikasyonu; üretim aracına verilecek, production kod değil)

---

## ÜST KURALLAR (Notebook'a talimat)

1. **CORE INVESTMENT THESIS (tüm sunumun omurgası):**
   > "We are not asking capital to prove that our system works. We are using capital to find out, under real market conditions, whether it actually does."

2. **Dört rakam birbirinden asla görsel olarak birleşmeyecek:**
   - ① `5,216` — ana sinyal arşivi (signals_archive, barrier-captured)
   - ② `+0.40%` — bu dataset'in historical mean / barrier-based expectancy
   - ③ `46,581` — ayrı full-universe araştırma (farklı konfigürasyon grid'i)
   - ④ `111` — ayrı MFE araştırmasında ≥%100 tepeyi gören kayıt sayısı
   > **NEVER visually combine these datasets.**

3. **111 kayıt asla "%100 kazanan hisse" olarak adlandırılmayacak.**
   - Doğru: "111 observations reached ≥100% MFE in a separate study."
   - Yanlış: "111 stocks returned 100%."

4. **+0,40% hiçbir yerde "profit", "return generated" veya "performance" diye sunulmayacak.** "Historical mean / barrier-based expectancy result" olarak kalacak.

5. **8 başarısız yaklaşım yalnızca Red Team kutusunda** kullanılacak, kaynağı: `decision-log.md` (2026-09-03 girdisi) + `reports/experiment_review_board_exp1_2026-09-03.md`.

6. **Hiçbir slaytta verilmeyen sayı/istatistik EKLEMEYİN.** Eksikse "TBD" yazın, uydurmayın.

7. **"Garanti", "kesin", "kanıtlanmış edge" yasak.** "Hipotez", "senaryo", "gözlemlendi", "test ediliyor" dili korunacak.

8. **Etiket sistemi:** `[V]` Verified (doğrulanmış veri) · `[S]` Scenario (senaryo/illüstrasyon) · `[C]` Concept (kavramsal/henüz deneysel) · `[A]` Artifact (kaynak dosya/DB referansı). Her rakam etiketini taşır; Notebook bunu görsel olarak korur.

9. **Trading içerikli her slaytta zımni not:** "Geçmiş performans gelecekteki sonucun göstergesi değildir."

10. **Haftalık/aylık sabit getiri yüzdesi hedefi hiçbir yerde kullanılmayacak.**

---

## YAPISAL AKIŞ

| Bölüm | Slaytlar | Soru |
|---|---|---|
| **PAST** | 3–5 | What did we observe? |
| **PRESENT** | 6–9 | What do we know, what don't we know, what infrastructure is missing? |
| **FUTURE** | 10–12 | What happens if validation succeeds? |
| **VISION** | 13 | Why can this become more than a trading bot? |

Psikolojik akış: **Evidence → Failure → Knowledge Gap → Capital → Validation → Autonomy → Bigger Vision**

---

## SLIDE 1 — Kapak

**Başlık:** FinPilot
**Alt başlık:** Building the AI Trading Engine of the Future
**Mesaj:** Viyana merkezli, tek kurucu, finansal zeka şirketi. Meriç Başak · 2026.
**Veri:** Yok. **[C]**
**Görsel:** Logo, tek cümle, tarih. Minimal.
**Do not say:** Herhangi bir performans iddiası.

---

## SLIDE 2 — Why Now: The Future of Trading

**Ana mesaj:** Piyasalar algoritmikleşiyor; bir sonraki aşama emir otomasyonu değil, algıla→anla→seç→riskle→yürüt→öğren döngüsü.
**Veri:**
- Carta 2025: tek-kurucu oranı %23,7 → %36,3 **[V]** — ama "tek kişilik unicorn" değil; "Solo founder ≠ solo company. Lean by design, not alone by necessity."
**Görsel:** Market Data → AI Reasoning → Strategy Selection → Risk Engine → Execution → Learning akış diyagramı.
**Kaynak:** fi.co "The One-Person Unicorn" (2026), Carta 2025 Solo Founders Report **[A]**
**Do not say:** "Tek kişi her şeyi yapar" — kritik noktalarda dış uzman desteği var.

---

## SLIDE 3 — What We Have: 5,216 Historical Signals

**Başlık:** 5,216 Historical Signals: A Measured Signal Hypothesis
**Ana mesaj:** Asimetrik getiri yapısı gözlemlendi — doğrulama gerektiren bir hipotez.
**Veri (hepsi [V], signals_archive.resolved_pct_barrier, 2026-09-02 canlı sorgu) [A]:**

| Metrik | Değer | Etiket |
|---|---:|---|
| Hit rate | **%30,16** | [V] |
| Historical mean (barrier-based expectancy) | **+%0,40** | [V] |
| Medyan getiri | **-%0,64** | [V] |
| Ortalama kazanç | **+%4,28** | [V] |
| Ortalama kayıp | **-%1,27** | [V] |
| Asimetri | **3,36×** | [V] |

**Medyan açıklaması (slaytta yer almalı — medyan SİLİNMEZ, yeniden çerçevelenir):**
> "Why is the mean positive while the median is negative? Because the median reflects our **current exit architecture**, not the market's ceiling. The payoff structure is asymmetric by design — small controlled losses, occasional outsized captures. The gap between what we capture and what the market offers is the research opportunity (see Slide 4)."

---

## SLIDE 4 — What Did We Actually Discover? — Capture vs MFE

**Tasarım (kritik):** İki panel, birbirine KARIŞTIRILMAYACAK.

### SOL PANEL — ① 5,216: What did the system actually capture?
Barrier-captured dağılım **[V]** [A: `data/finpilot.db` canlı sorgu 2026-09-02]:

| Aralık | Sayı | Oran |
|---|---:|---:|
| < -%10 | 5 | %0,10 |
| -%10 – -%5 | 48 | %0,92 |
| -%5 – %0 | 3.590 | %68,83 |
| %0 – %2 | 446 | %8,55 |
| %2 – %5 | 699 | %13,40 |
| %5 – %10 | 329 | %6,31 |
| %10 – %20 | 79 | %1,51 |
| ≥%20 | 20 | %0,38 |

Maksimum gözlem: **%49,29** — hiçbir kayıt %50'yi geçmiyor (barrier/TP-SL yapısal sınırı).

### SAĞ PANEL — ③ 46,581 + ④ 111: What did the market offer?
Ayrı çalışma, farklı konfigürasyon **[V ama ayrı dataset]** [A: `data/backtest_out/full_universe_barrier_results.json`]:
- Ortalama MFE: **%4,83** vs yakalanan ortalama **+%0,37**
- **111 observations reached ≥100% MFE** (46.080 etiketli satırda %0,24) **[V]**
- MFE = Maximum Favorable Excursion (piyasanın lehimize gittiği en uzak nokta)

### ARA — Büyük ok
**Market opportunity → Current capture**

**Mesaj:** "The market moved significantly in our favor. Our current exit architecture captured only a fraction of that movement."

**Gap notu (sağ panelin altına, küçük):**
> "111 sinyal tepe noktasında +%100'ü aştı — ama sistem barrier'da çıktığı için yakalanan ortalama +%0,37. Aradaki fark bizim roadmap'imiz."

**Do not say:** "111 stocks returned 100%", "we caught +100%". MFE ≠ yakalanan getiri.
**Dipnot:** İki panel ayrı dataset; görsel olarak birleştirilmez. **[A]** ayrı dataset uyarısı. Kuyruk temizlenmiştir (split/veri artefaktı flag'li satırlar hariç tutuldu — integrity audit).

---

## SLIDE 5 — What Doesn't Work? — Red Team Results

**Ana mesaj:** Negatif sonuçları yayınlıyoruz — ürünün temeli bu.
**Veri (hepsi [V], 11 Ağustos 2026 sentezi, 48.727 path, CPCV/PBO/White RC/Hansen SPA) [A: `reports/scanner_research_synthesis_10_perspectives_2026-08-11.md`]:**
- Skor ↔ ileri getiri: rho = 0,013–0,019 **[V]**
- Brier skill: **-0,019 / -0,030** (rastgeleden kötü) **[V]**
- Adverse selection: eligible -%0,35/-%0,49 vs rejected +%1,45/+%0,07 **[V]**
- Outlier dependence: üst %1 çıkarılınca +%1,40 → **-%0,37** **[V]**
- 3.120 TP/SL konfigürasyonunda küresel bir kanıt oluşmadı; **locked out-of-sample gate kasıtlı olarak kapalı tutuldu** (disiplinli doğrulama tasarımı gereği) **[V]**

**RED TEAM KUTUSU (kaynaklı):**
> "We actively tried to disprove our own signal. **8 independent direction-prediction approaches failed.**"
> Kaynak: `docs/governance/decision-log.md` (2026-09-03), `reports/experiment_review_board_exp1_2026-09-03.md` **[A]**

**Do not say:** "8" sayısını bu kaynak olmadan genelleştirme.

---

## SLIDE 6 — The Opportunity: Better Decision Architecture

**Başlık:** The Opportunity Is Not More Signals — It's Better Decisions
**Ana mesaj:** Sorun sinyal keşfi değil, karar mimarisi.
**Veri:** Yok (kavramsal) **[C]**
**Görsel:** Signal → Entry → Regime → Position → Exit → Execution akışı; MFE farkını (%4,83 vs +%0,37) bu akışa bağla.
**Mesaj:** "The market sometimes moves substantially in our favor. The current architecture does not consistently capture that movement."

---

## SLIDE 7 — Where Funding Goes: €10K → Capabilities

**Başlık:** €10,000 — "Donanım Odaklı Doğrulama" (DGX Spark ile) **[S — örnek dağılım, kesin tur değil]**

| Kalem | Ürün/Hizmet | Süre | Maliyet |
|---|---|---|---:|
| Yerel donanım | NVIDIA DGX Spark / ASUS GX10 (GB10, 128GB) | tek seferlik | ~€4.700 |
| Canlı veri | Polygon.io Advanced (gerçek zamanlı, 20+ yıl) | 4 ay (pilot) | ~€730 |
| Bulut compute | RunPod (burst/yedek) | 4 ay | ~€200 |
| Execution/izleme sunucusu | Hetzner VPS | 12 ay | ~€120 |
| Broker veri eklentisi | IBKR | 12 ay | ~€150 |
| Şirket kaydı + muhasebe | Einzelunternehmen (WKO) | tek seferlik+1yıl | ~€500 |
| Yazılım/araç lisansları | — | 12 ay | ~€150 |
| Runway/tampon | — | — | ~€3.450 |
| **TOPLAM** | | | **€10.000** |

**Çerçeve:** "We are not buying hardware. We are buying capabilities."
- €4.7K Compute → faster research, larger simulations, local AI inference
- €730 Data → real-time validation, realistic execution modelling
- €200 Cloud → scalable experiments, continuous paper trading
- Research+deployment → OOS validation, paper trading, supervised live

**Kilit mesaj (birebir):** "We are buying better data to find out whether the signal is real — before anyone's capital depends on it."
**Kaynak:** Polygon.io, Databento, RunPod, Lambda Labs, NVIDIA, Hetzner, IBKR fiyatlandırma (2026) **[A]**
**Do not say:** "trading için para", "garantili getiri yatırımı".

---

## SLIDE 8 — The Data Advantage: Reducing Unknowns

**Başlık:** The goal is not "more data". The goal is fewer unknowns.
**Veri (bugünkü stack [V], repo-doğrulanmış):**
- yfinance (ücretsiz, gecikmeli) **[V]**
- EODHD (fundamentals, `FINPILOT_ENABLE_FUNDAMENTALS` flag'i arkasında) **[V]**
- SEC EDGAR pipeline (catalyst, universe-wide refreshed, flag-gated OFF) **[V]**

**Hedef veri — üç seviye:**
- **LEVEL 1 — Market Truth:** tick, intraday, corporate actions, volume/liquidity
- **LEVEL 2 — Market Context:** news, fundamentals, analyst revisions, volatility
- **LEVEL 3 — Execution Truth:** spread, slippage, latency, fills, transaction costs

**Kaynak:** `scanner/features.py`, `.env` konfigürasyonu **[A]**

---

## SLIDE 9 — From Signal to Autonomous Trading

**Ana mesaj:** Kavramsal pipeline.
**Görsel:** Data → Regime → Strategy → Meta-Ranker → Risk → Execution → Learning
**Dipnot (kritik):** "Backtest performance becomes meaningful only after execution costs, slippage and out-of-sample behavior are validated."
**Veri:** Yok **[C]**
**Do not say:** "backtest = live", "geçmiş performans geleceği gösterir".

---

## SLIDE 10 — 12-Month GO/NO-GO Roadmap

**Ana mesaj:** Objektif kapı; NO-GO senaryosu görünür.
**Veri:** Yok (yol haritası) **[C]**

**Ay 0-3:** Altyapı + araştırma (veri, donanım, backtesting, execution engine)
**Ay 3-6:** Doğrulama (walk-forward, OOS, maliyet+slippage, paper trading)

### AY 6 — GO/NO-GO KAPISI
🟢 **GO** if: pozitif net expectancy (maliyet sonrası), kabul edilebilir drawdown, OOS geçti, rejimler arası istikrar, paper/live tutarlılık
🔴 **NO-GO** if: edge OOS'ta kaybolur, maliyetler expectancy'yi siler, istikrarsızlık sürer, drawdown kabul edilemez
> **NO-GO altında: "No additional trading capital deployed."**

**Ay 6-9:** Gözetimli canlı (küçük sermaye, insan onayı)
**Ay 9-12:** Kademeli otonomi — "Toward autonomy — not blind autonomy."

---

## SLIDE 11 — FinSense: The Longer-Term Platform *(Parallel track — not part of this raise)*

**Çerçeve:** İki ürün, tek teknoloji. Trading finansmanından bağımsız paralel hat. **Bu slayt yatırım talebinin parçası değildir; vizyon genişlemesi olarak sunulur.**
**Yapı:**
- **FinPilot Trading Intelligence** — near-term: research, validation, trading engine, cash-flow potential
- **Shared technology** — AI reasoning, financial intelligence, agent architecture, calibration/learning
- **FinSense** — long-term: consumer financial reasoning, financial education, scalable SaaS

**Büyüme senaryosu (küçük kutu, [S]):**
- Yıl 1: Pilot + erken benimseyenler
- Yıl 2: Ürün-pazar uyumu + büyüme
- Yıl 3 (senaryo): 40.000-50.000 ödeyen kullanıcı hedefi
- Matematik: 50.000 × €12/ay × 12 = **€7,2M yıllık gelir potansiyeli (illüstratif senaryo)** **[S]**

**Zorunlu uyarı (silinmeyecek):** Tüketici aboneliklerinde medyan ~€13/ay, yıl-1 elde tutma <%30, üst çeyrek %80 büyürken alt çeyrek %33 küçülüyor (RevenueCat 2026). *"This is a scenario, not a forecast."* **[V — benchmark]**
**Kaynak:** RevenueCat "State of Subscription Apps 2026" **[A]**

---

## SLIDE 12 — What We Know / What We Don't Know Yet ⭐

**Bu slayt deck'in en güçlü konsepti.**

| We Know | We Don't Know Yet |
|---|---|
| 5,216 historical signals tested **[V]** | Live profitability **[C]** |
| Historical asymmetry observed **[V]** | True execution edge **[C]** |
| Large MFE events exist (separate study) **[V]** | How much MFE is realistically capturable **[C]** |
| Several approaches failed **[V]** | Which regime-specific approach wins **[C]** |
| Current scoring has weaknesses **[V]** | Robust OOS performance **[C]** |
| Research infrastructure exists **[V]** | Long-term autonomous performance **[C]** |

**Mesaj:** "The purpose of this investment is to answer the right column."

---

## SLIDE 13 — The Opportunity (Kapanış)

**Ana mesaj:**
> "We are not trying to build another stock screener. We are building an AI system that can observe markets, reason about opportunities, manage risk, execute decisions and learn from outcomes."

**FinPilot** — From financial data to autonomous financial intelligence.

**Kapanış cümlesi (ton belirleyici):**
> "Başarılı olursak: doğrulanmış, küçük ölçekli bir gelir kalemi kazanırız. Olmazsa: disiplinli şekilde denemiş, öğrenmiş ve sermayeyi korumuş oluruz. Her adım, açık raporlamayla ilerler."

**Omurga (tekrar, Slide 1'den beri):**
> "We are not asking capital to prove that our system works. We are using capital to find out, under real market conditions, whether it actually does."

---

## KAYNAK / ETİKET ÖZETİ

| Etiket | Anlam | Örnekler |
|---|---|---|
| **[V]** Verified | Doğrulanmış veri/sonuç | Slide 3 metrikleri, Slide 4 dağılım, Slide 5 negatif bulgular, Slide 8 stack |
| **[S]** Scenario | Senaryo/illüstrasyon | Slide 7 €10K dağılım, Slide 11 €7,2M |
| **[C]** Concept | Kavramsal/deneysel | Slide 2, 6, 9, 10, 12 sağ sütun, Slide 13 |
| **[A]** Artifact | Kaynak dosya/DB | signals_archive, full_universe_barrier_results.json, decision-log, experiment_review_board |

## DÖRT RAKAM AYRIMI (tasarım kuralı)

① **5,216** — signals_archive (barrier-captured karne)
② **+%0,40** — bu dataset'in historical mean
③ **46,581** — ayrı full-universe barrier araştırması
④ **111** — ayrı MFE araştırmasında ≥%100 tepe gören kayıtlar
> Bu dört rakam aynı görselde birleşmez. Slide 4'te sol/sağ panellerle ayrılır.
