# FINPILOT — DEEP RESEARCH MASTER PROMPT
## Direction Prediction: External Evidence & Literature Scouting
**Version:** 1.0 · **Date:** 2026-09-18 · **Type:** Deep internet/literature research (evidence gathering ONLY)
**Governance:** Level A. No production/code/data change. No prediction produced. No trading claim.

---

## 0. CONTEXT — What we already know (DO NOT re-litigate)

FinPilot has ALREADY established, on its own 40,834-row universe (2025-09-11 → 2026-08-05, US equities):

- **Direction prediction failed 8+ independent ways** (regime, breadth, sector, tier, momentum, intraday path, Regime×Tier matrix, threshold matrix). All NOT SUPPORTED.
- **Baseline composite score vs forward return: Spearman ≈ +0.047, worse than random** (provisional — baseline reconstruction was incomplete).
- **Attention map (descriptive):** gap/volatility flags → 62.1% big-move precision, 1.7–3.3× lift, 5 months. **BUT it detects MOVEMENT, not DIRECTION.** Unusual stocks move more (|5d ret| 7.0% vs 3.3%) yet have NEGATIVE median return (−2.32%) and higher big-loser rate (39.4% vs 15.1%).
- **Opening-range fade:** 59.9% gross win BUT day-clustered (54.2% insignificant), top-5% removal drops mean to 0.20%, and NEGATIVE at 1% round-trip cost. Cherry-pick risk HIGH (discovered and tested on same 698 obs).
- **Feature flags (squeeze/lottery/overnight):** behaviorally active (change scores) but NOT predictive.
- **No persisted component is predictive** (all |Spearman| ≤ 0.05).

**The core unsolved problem:** We can detect THAT a stock will move (attention), but not WHICH WAY (direction). This deep-research task asks: **what does the external evidence base say actually carries DIRECTIONAL signal for retail-horizon (1-5 day) US equities — and is any of it feasible with data we can realistically obtain?**

---

## 1. PRIMARY RESEARCH QUESTION

> **For short-horizon (1–5 day) US equity direction, which signals/data sources have credible, replicated, out-of-sample evidence of directional predictive power — and what are the realistic effect sizes, costs, and data requirements?**

Secondary questions:
1. Which signals are DOCUMENTED to fail at this horizon (so we stop wasting effort)?
2. What is the smallest realistic edge a retail-scale system can capture after costs?
3. Which of our 5 candidate sources (short interest, insider Form 4, 8-K events, news sentiment, float/short_pct) has the STRONGEST peer-reviewed directional evidence?
4. What data do the strongest-evidence signals require that we do NOT currently have?

---

## 2. SCOPE — What to research

### A. Academic literature (peer-reviewed + SSRN working papers)
Research the directional evidence for:
- **Short interest** (level + change) — Desai, Ramesh, Thiagarajan, Balachandran (2002); Asquith et al.; Boehmer et al. Effect size, horizon, decay.
- **Insider trading (Form 4)** — Jaffe (1974); Lakonishok & Lee (2001); Seyhun. Insider buys vs sells asymmetry.
- **PEAD (post-earnings-announcement drift)** — Ball & Brown (1968); Bernard & Thomas. Current strength at 1-5 day horizon post-2010.
- **News sentiment** — Tetlock (2007); Tetlock, Saar-Tsechansky, Macskassy (2008). LLM-era sentiment (2023+) vs older dictionary methods.
- **Overnight vs intraday returns** — Lou, Polk, Skouras (2019) "tug of war"; Abdi et al. overnight/intraday decomposition.
- **Short-term reversal** — Jegadeesh (1990); Lehmann (1990). 1-week reversal strength today.
- **52-week high / momentum** — George & Hwang (2004). But note: our data showed dist_52w_high redundant + non-monotonic — reconcile.
- **Lottery/MAX effect** — Bali, Cakici, Whitelaw (2011). Direction of the effect and its robustness.
- **Short squeezes** — conditions under which high short interest reverses UP.

### B. Practitioner / quant-blog evidence (label clearly as non-peer-reviewed)
- Quantpedia, Alpha Architect, SSRN practitioner summaries, academic-quant crossover blogs.
- Realistic retail-achievable edges and their capacity/cost limits.

### C. Meta-evidence on decay
- McLean & Pontiff (2016) "Does Academic Research Destroy Stock Return Predictability?" — post-publication decay.
- Which anomalies survive transaction costs at retail scale.

---

## 3. EVIDENCE STANDARDS (MANDATORY)

For EVERY claim, classify the evidence tier:

```
TIER A — Peer-reviewed, replicated, out-of-sample, post-cost
TIER B — Peer-reviewed but in-sample / pre-cost / single-era
TIER C — SSRN working paper / practitioner backtest (not peer-reviewed)
TIER D — Blog/anecdote/marketing claim (weakest)
```

For EVERY directional claim, extract if available:
- effect size (e.g., bps/day, t-stat, Sharpe, win-rate)
- horizon (1d / 5d / 1mo)
- sample period + market (US? other?)
- whether it survives transaction costs
- whether it decayed post-publication
- data requirement (what feed is needed)

**Never blend academic + practitioner + FinPilot-internal into one unlabeled claim.**

---

## 4. CANDIDATE SOURCE SCORING

For each of our 5 candidates, produce an evidence card:

```
SOURCE: <name>
DIRECTIONAL EVIDENCE (external): TIER + effect size + horizon + era
REPLICATION STATUS: replicated / single-study / contested
COST SENSITIVITY: survives retail costs?
DATA WE HAVE: sufficient / partial / missing
DATA GAP: what we'd need to add
FEASIBILITY FOR FINPILOT: HIGH / MEDIUM / LOW
NET VERDICT: PURSUE / TEST-CAREFULLY / DEPRIORITIZE / KILL
```

Candidates:
1. Short interest (ΔSI) — finra_cache (bi-weekly, 2017-2026)
2. Insider buying (Form 4) — edgar_cache (needs buy/sell parse)
3. 8-K material events — edgar_cache (needs tone classification)
4. News sentiment — news_cache (score meaning unclear, ~0.99 constant)
5. float/short_pct level — fundamentals_cache (snapshot, not point-in-time)

---

## 5. CRITICAL RECONCILIATION TASKS

These are REQUIRED — do not skip:

1. **Movement ≠ Direction.** Our attention map proves we can detect big moves but they skew NEGATIVE. Find external evidence on whether ANY short-horizon signal separates UP-moves from DOWN-moves with positive expectancy after costs — or whether short-horizon direction is dominated by noise/fees at retail scale.

2. **Reconcile dist_52w_high.** George & Hwang say 52w-high momentum carries signal; our data shows dist_52w_high is redundant with composite (0.64) and non-monotonic/inverted. Is the literature effect at a different horizon, or does it not survive in our universe?

3. **The negative-median problem.** Our unusual stocks have negative median return. Is there documented evidence that high-attention retail names systematically underperform (attention/lottery overpricing — Barber & Odean, Da, Engelberg)? If so, detection may be a SHORT/avoid signal, not a long signal.

4. **The fade question.** Our opening-range fade showed 59.9% gross but negative-after-cost. Find external evidence on opening-range reversal/fade at retail cost levels — does ANYONE show it surviving realistic retail costs?

---

## 6. DELIVERABLES

Produce a single report with:

1. **Executive summary** (≤ 15 lines) — the honest answer to "does any short-horizon retail direction signal work, and which should FinPilot test?"
2. **Evidence table** — every signal × tier × effect size × horizon × cost-survival × era
3. **5 candidate cards** (per §4)
4. **Kill list** — signals documented to fail at our horizon (so we stop)
5. **Reconciliation answers** (per §5, all 4)
6. **Data gap list** — what feeds we'd need to add for the strongest signals
7. **Recommended next experiment** — ONE, pre-registered, with explicit hypothesis + falsification criterion
8. **Confidence levels** — state uncertainty explicitly; distinguish "strong external evidence" from "we haven't tested it on our universe"

---

## 7. HARD CONSTRAINTS

- **No fabricated citations.** If you cannot verify a source, mark it UNVERIFIED.
- **No directional claim without a tier label.**
- **No "this will be profitable" language.** Only "has documented evidence of X effect size at Y horizon, which may/may not survive our costs."
- **Distinguish:** external evidence (their data) vs FinPilot evidence (our data). Never claim external evidence validates our universe.
- **Negative result is valid.** If the honest answer is "short-horizon retail direction is mostly noise after costs," say so clearly.
- **FinPilot internal results are FIXED context** — do not re-derive them; cite them as given.

---

## 8. SUCCESS CRITERION

This research succeeds if it produces a **clear, tier-labeled map** of which short-horizon direction signals have credible external evidence, which of our 5 candidate data sources map to them, and ONE concrete pre-registered next experiment. It FAILS if it produces vague optimism or unlabeled claims.

**The honest answer may be: "At 1-5 day horizon with retail costs, reliable direction prediction is largely unsupported; the defensible edges are X, Y (small, specific)." If so, that is the deliverable.**
