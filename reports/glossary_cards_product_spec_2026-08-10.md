# Piyasa Terimleri: 37 Kart

Status: DRAFT — Level B proposal, human approval required before sale
Date: 2026-08-10
Owner: FinPilot Content

## Product idea

An original bilingual learning deck for beginner investors. Each card
introduces one market concept in plain language, shows where the concept can
mislead a reader, and ends with a question that encourages evidence-based
thinking. The deck is educational material, not a signal service or investment
recommendation.

## What we can create from the existing asset

The single source of truth is `distribution/glossary.py`. Its 37 entries give
us the term names, short Turkish and English explanations, and the existing
English card copy. The paid product should add teaching structure around that
source rather than redefine the terms:

1. **Front:** term, pronunciation or abbreviation, and a one-line prompt.
2. **Back:** Turkish explanation, English explanation, plain-language example,
   common misunderstanding, and a reflection question.
3. **Guide:** how to study the deck, a one-page risk glossary, and a short
   source note for each concept family.
4. **Digital bonus:** CSV/Anki-compatible fields so the buyer can study on a
   phone or import the deck into a spaced-repetition app.

## Proposed card families

| Family | Terms | Learning purpose |
|---|---:|---|
| Market signals | 10 | Read price, volume, gaps and market context without treating a signal as a promise. |
| Research literacy | 9 | Understand probability, calibration, base rates, lift and out-of-sample testing. |
| Market structure | 10 | See liquidity, volatility, halts, dilution and execution friction. |
| Behaviour and risk | 8 | Recognise FOMO, overtrading, drawdown and sizing decisions. |

The exact family assignment must be checked against the glossary and product
code before export; the table is a packaging proposal, not a new terminology
authority.

## Premium content layers

The deck becomes meaningfully more valuable when each card answers five
questions:

- **What is it?** A short, accurate definition.
- **Why does it matter?** The decision or observation it informs.
- **What can fool me?** A limitation, confound, or common misuse.
- **What would I measure?** A small evidence check, such as spread, base rate,
  close-to-close return, or sample size.
- **What should I ask next?** A reflection prompt rather than a trade command.

This creates original instructional value without copying a textbook chapter.
The examples should use generic, fictional numbers or clearly labelled
historical illustrations. They must not imply a guaranteed outcome or a live
recommendation.

## Source and rights policy

“Open source” is not a sufficient rights label for a book. Before any source
is used in the paid pack, record its exact title, author, URL, licence or public
domain status, edition, and intended use in a source register. The safe default
is to use sources for ideas and factual background, then write original
definitions, examples, questions, and layout. Verbatim passages, close
paraphrases, copied figures, and scans require a separate rights check and
should not enter the commercial deck without permission.

Suggested source classes:

- public-domain statistical and market-history texts;
- Creative Commons works whose licence permits commercial adaptation;
- official exchange, regulator, or filing documentation for factual terms;
- FinPilot's own research reports, cited as internal case studies with their
  exploratory status preserved.

No source list is currently present in the repository, so no external book is
claimed as a source in this draft.

## Proposed deliverables

### Starter pack — $9

- 37 bilingual cards in print-ready PDF;
- one-page quick-start guide;
- printable progress tracker.

### Complete pack — $15–19

- everything in Starter;
- Anki/CSV import file;
- expanded examples and misconception notes;
- source register and further-reading list;
- five mini exercises using fictional data.

The price is a proposal, not a publishing decision. Gumroad listing, payment,
and public release require the owner's approval.

## Sample card format

### Card 01 — Calibration / Kalibrasyon

**Front prompt:** If a model says “60%”, what should happen over many similar
cases?

**What it is:** A probability is calibrated when outcomes observed over a
comparable group are close to the probabilities stated by the model.

**Why it matters:** A probability label is useful only when its historical
frequency has been tested on data that was not used to tune the label.

**Common misunderstanding:** A calibrated 60% estimate does not mean the next
case must work, and calibration alone does not prove that the model beats a
simple base rate after costs.

**Evidence check:** Compare predicted probability buckets with realised
frequencies, report the sample size in each bucket, and compare Brier score
with a constant base-rate model.

**Reflection:** What evidence would make this probability more trustworthy,
and what would make it less useful even if it were calibrated?

**English back:** Calibration asks whether a probability means what it says.
Across many comparable cases, predictions near 60% should occur roughly 60% of
the time. It is a property of a group, not a promise about one observation.

## Production checklist

- [ ] Export terms from `distribution/glossary.py`; do not hand-maintain a
  competing term list.
- [ ] Add Turkish copy for every card and review it for meaning, not literal
  translation.
- [ ] Add one limitation and one evidence question to every card.
- [ ] Add source metadata only after licence and attribution are verified.
- [ ] Run a compliance pass for advice-like language, certainty, and implied
  performance.
- [ ] Generate PDF and Anki/CSV from the same structured content.
- [ ] Have the owner approve the product name, price, description, and release.

## Decision status

This is a Level B content-product proposal. The next implementation step can
be a research-only draft export of the 37 cards, but public sale and any claim
about the value or results of the product remain subject to human approval.
