# Gumroad / Lemon Squeezy Listing — Copy-Paste Ready

---

## Product name
**Why Your Backtest Is Lying To You — The FinPilot Research Handbook**

## One-line pitch (for the product card)
40 real experiments on a live trading scanner. One honest postmortem on every way
the backtest lied to us first.

## Price
**€29** (suggested launch price; range tested €19–49 — see notes at bottom)

## Format
PDF, 14 pages. Instant download.

---

## Sales page copy

### Headline
**We ran 40 experiments on our own trading system. It doesn't have an edge. Here's
exactly how we found out — and the six mistakes that hid it for two years.**

### Subheadline
A field guide to the ways a backtest lies to the person who built it, written by the
person it happened to.

### The hook

FinPilot is a real, live US-equity scanner. We built it, scored it, ranked it into
conviction tiers, and trusted the backtest for about two years.

This summer we finally audited it properly — day-clustered significance testing,
matched-random controls, effective-sample-size correction, negative-control
preflights, the works. What we found wasn't an edge. It was:

- A label bug that had been silently grading our system on its *best five minutes*,
  not what actually happened to a position (Chapter 2).
- A sample size that was really about **1/44th** the size we thought it was, once
  same-day and day-to-day correlation were priced in (Chapter 3).
- A finding that looked like the strongest result in the whole program — and died
  in three separate, increasingly rigorous re-tests (Chapter 4).
- A selection layer that beat a coin flip and *still lost to a random draw of the
  stocks it rejected*, three different ways (Chapter 5).
- A dead feature that had been sitting in the score, doing nothing, for about two
  years, because nobody had ever checked (Chapter 7).

We wrote all of it down — including the two times we oversold our own fixes to
ourselves, and caught it.

### Who this is for

- You're building or maintaining a trading signal, scanner, or screener and you want
  to know the specific checks that would have caught our mistakes before they cost
  two years.
- You're evaluating a "smart money" or "AI-powered" trading product and want a
  concrete checklist for what a real audit looks like versus a marketing backtest.
- You do cross-sectional research on any panel data (not just finance) and want a
  short, real-world case study on effective sample size, day-clustering, and
  artifact-hunting.

### What's inside

1. The Setup — what a two-year-old, seemingly-working system actually looked like from inside
2. Mistake #1 — measuring MFE and calling it a return (and how we caught ourselves overselling the fix)
3. Mistake #2 — why 27,361 rows was really about 620 independent observations
4. Mistake #3 — the "artifact ladder": four checks a finding must survive before you trust it
5. Mistake #4 — three independent ways to prove a selection layer is *subtracting* value
6. Mistake #5 — the silent duplicate-row trap from an hourly scanner
7. Mistake #6 — catching ourselves breaking our own rule, on our own fix
8. What actually survived — the three things that held up under every test
9. A four-gate protocol you can copy for your own project
10. Closing thoughts, plus a one-page checklist and a glossary

### The promise

Every number in this handbook is checkable against our own published research log.
Nothing here is a "how we found alpha" story dressed up as humility. It's the
opposite: a real account of building something for two years, testing it properly
exactly once, and telling you precisely what broke.

### FAQ

**Is this going to teach me a trading strategy?**
No. It will teach you how to find out whether *your* trading strategy actually works,
using the exact mistakes that hid the truth from us.

**Do I need a quant/data-science background?**
Basic stats helps (what a p-value and a confidence interval are) but every concept
is explained plainly, with a real number attached, not just formulas.

**Is FinPilot still running?**
Yes — as a research-transparent decision-support product, not a "we have an edge"
signal service. This handbook is part of why that pivot happened.

### CTA button text
**Get the honest version — €29**

---

## Notes for Meriç (not part of the listing)

- Suggested price: start at **€29**. This sits between the "impulse buy" ceiling
  (~€19, less signal that the content is substantive) and the "considered purchase"
  floor (~€49, needs stronger social proof / reviews before people pay that without
  hesitation on a first-time seller with zero reviews).
- Launch-week tactic: offer it free-with-email for the first ~50 downloads (funnels
  into the consulting/audit angle from Path 1) OR go straight to paid — free-first
  gets you a mailing list faster, paid-first gets you a real willingness-to-pay
  signal faster. Given the goal this week is "which of the 5 paths is real," I'd
  lean **paid from day one** — it's the cleanest signal.
- Distribution for launch day: a short post built from Chapter 4 or Chapter 5 alone
  (the reverse-ranking story or the three-proof selection-layer story) works
  standalone on r/algotrading, r/quant, or Hacker News — post the story, link the
  handbook, don't lead with the sales pitch.
