# FinPilot — MASTER TASARIM ŞABLONU
## "The Morning Ledger × The Open Classroom" — Tek Bütün, Tek Landing, Claude Design'a Yapıştır-Çalıştır

**Tarih:** 2026-07-05 · Şablon 1 + Şablon 3'ün resmi birleşimi. Supersedes: 3'lü şablon dosyasındaki ayrı sürümler.

**Birleşim mantığı (ne nereden geliyor):**

| Katman | Kaynak | Ne alındı |
|---|---|---|
| Görsel deri + ton | Morning Ledger | Gazete estetiği: serif başlıklar, mürekkep laciverti, altın Grade A mührü, künye/kolofon disiplini, kenar-notu (margin note) mekaniği |
| Ürün omurgası + öğrenme | Open Classroom (Şablon 3 aynen) | Daily Double köprüsü, kalibrasyon antrenörü, kör-nokta haritası, vaka dosyaları, iki öğrenme yolu, sonuç-damgası döngüsü |
| Metafor evliliği | Yeni | "Okuyan gazete": her sayı hem haber hem ders; arşiv = geçmiş sayılar = vaka dosyaları; FinSense = gazetenin okul eki |

Sistemle birebir eşleşme: kartlar `demo_snapshot.json` alanlarını kullanır (grade, prob_band, badges, rationale, karne.by_grade, toplam_aday_bugun, config_sha); terimler `terms.ts` sözlüğünden; sonuç damgaları signals_archive'den; kalibrasyon dili Truth Engine felsefesinden. Compliance: BUY/SELL yok, hedef fiyat yok, getiri vaadi yok, disclaimer her ekranda.

---

## ↓↓↓ CLAUDE DESIGN'A YAPIŞTIRILACAK BLOK ↓↓↓

```
Design a complete, production-grade website + web application called
"FinPilot — The Morning Ledger". One unified product with two fused souls:

SOUL 1 (the skin): a calm, editorial morning newspaper for the stock market.
SOUL 2 (the spine): a learning-first classroom where every concept is taught
with this morning's real market data.

The fusion premise: "The newspaper that teaches you to read it."
Every daily edition is simultaneously the news (real graded stock candidates)
and the lesson (the concept that explains today's top candidate). The archive
of past editions doubles as the case-file library. The paper grades itself
publicly (open scorecard) and teaches the reader to grade themselves the same
way (calibration trainer).

PRODUCT FACTS (bind the design to these):
- Engine scans 1,800+ US stocks every morning at 07:45 Vienna time.
- Candidates get a single research Grade: A (rare, ~1/day, gold), B (strong,
  steel blue), C (watch-stage, warm gray) with a calibrated probability band
  ("candidates with this profile moved ≥5% within 5 days ~65% of the time").
- Each candidate card carries: ticker, company, grade seal, probability
  sentence, 2-4 factor badges (short interest, gap, RVOL, catalyst, momentum,
  contraction, regime, early-tier), a 2-sentence plain-language rationale,
  and (premium) a risk note.
- An OPEN scorecard tracks every outcome including misses (hit = ≥5% move in
  5 days), per grade: e.g. "A: 67% of 21 · B: 55% of 118 · C: 41% of 264".
- FinSense = the learning system: 12 domains, 2 tracks (Investor Path /
  Trader's Discipline Path), 120+ glossary terms, lessons built from real
  archived cases (5,000+ resolved signals — every example is real, dated,
  graded before the outcome was known).
- Distribution: free daily brief (1-2 candidates) on Telegram 08:30; premium
  "Full Edition" (€9/mo, founding print run of 20 at €99/yr price-locked,
  14-day unconditional refund) = all candidates + full reasons + risk notes.
- STRICT compliance: never the words BUY/SELL, never price targets, stops,
  position sizes or profit promises. Persistent colophon line on every
  screen: "Research & education. Not investment advice. Past results do not
  guarantee future results."

═══════════════ BRAND SYSTEM ═══════════════
- Canvas: deep ink navy #0B0F1A with a barely-visible paper-grain texture.
  Cards/surfaces #121826, hairline borders (white at 8%), 10px radius.
- Ink & accents:
  · Chalk cream #F2EAD8 — primary text (warm, readable, bookish).
  · Editorial gold #E8C468 — Grade A seal, primary CTAs, masthead rules.
  · Steel blue #7FA6C9 — Grade B; dusty violet #A99AC6 — FinSense/learning
    identity (every learning element carries a violet tick or underline).
  · LIVENESS SYSTEM (from the classroom soul): everything LIVE/today glows
    faintly amber #E9B872 (soft outer glow, 12% opacity); everything
    ARCHIVED is neutral ink. Readers learn the color rule in seconds:
    amber = happening now, ink = on the record.
  · Outcomes: sage green #7FB58A (hit) / soft brick #C97F7F (miss) — calm,
    never casino red/green.
- Typography: headlines & pull-quotes in an elegant serif ("Fraunces" or
  "Source Serif 4"); body/UI in "Inter" 17px base; tickers, numbers,
  timestamps in "JetBrains Mono". Newspaper details: smallcaps section
  labels, thin double rules under section heads, drop-cap on the daily lede.
- Motion: restrained. 200ms fades; the ONLY two flourishes: (1) the Daily
  Double bracket draws itself in 400ms, (2) outcome stamps press onto past
  editions with a 250ms scale-settle. No bounce, no confetti — completion
  rewards are one quiet sentence of real praise.

═══════════════ INFORMATION ARCHITECTURE ═══════════════
Top masthead nav (newspaper style, thin, sticky):
1. Today's Edition (product home)  2. Past Editions (archive = case files)
3. The Ledger (open scorecard)  4. The Classroom (FinSense)
5. Full Edition (premium)  — plus a small reader avatar with streak dots
   and "reading level" (mastery) shown as a tiny violet progress tick.
Landing page is separate (below) and routes into these.

═══════════════ SCREEN 0 — LANDING PAGE (single, complete) ═══════════════
Build this as one scrolling page with 8 sections:

S1 · MASTHEAD HERO: "FINPILOT" serif smallcaps masthead, dateline "Vienna ·
    Tuesday, July 7 2026 · Markets open in 2h 14m", thin double rule.
    Headline (serif, large): "1,800 stocks read before your coffee."
    Subhead: "Three graded candidates a morning, each with its reasons, a
    public scorecard we can't hide from — and a classroom that teaches you
    to read it all yourself." Two CTAs: gold "Read yesterday's edition"
    (primary) + quiet "Get the daily edition on Telegram · 08:30 · free".
S2 · YESTERDAY'S FRONT PAGE (proof, not promise): the actual previous
    edition rendered as an editorial article — dateline, one-line market
    context lede with drop-cap, then the top candidate as a news item:
    ticker monogram block, gold wax-seal Grade A stamp top-right, italic
    probability sentence, 2-sentence rationale where the financial terms
    (short interest, gap) carry fine dotted underlines. Hovering/tapping an
    underlined term opens a MARGIN NOTE in the right gutter (desktop) /
    bottom sheet (mobile): 60-word plain explanation, violet accent, and
    "full lesson in the Classroom →". Label above the section: "Yesterday's
    Edition — real, dated, frozen. Judge us with hindsight."
S3 · THE DAILY DOUBLE (the fusion signature): two linked cards, side by
    side, joined by a hand-drawn-style bracket that draws itself on scroll:
    left card violet-ticked "Today's Lesson — Relative Volume, 3 minutes";
    right card amber-glowing "Today's Case — $EXAS, Grade A". Bracket label:
    "today's lesson appears in today's market →". One line under it:
    "Every morning, the concept and the candidate arrive together. That's
    how you actually learn." CTA: "See how the Classroom works".
S4 · THE LEDGER STRIP (trust): elegant small table — "Grade A: 67% of 21 ·
    B: 55% of 118 · C: 41% of 264 (last 8 weeks)" + a calendar heat-strip of
    sage/brick dots + the pull-quote: "Last bad week: June 23–27, Grade B
    hit 2 of 9. It's on the record." Footnote glyph → methodology.
S5 · HOW IT'S MADE (4 steps, newspaper column style): Scan → Grade →
    Verify → Teach. Each a short column with a small engraving-style icon.
    Include the trust detail: "every edition carries its print-run stamp
    (config #cbe5cf) — reproducible research."
S6 · THE CLASSROOM PREVIEW: three lesson cards (whiteboard-sketch icons,
    violet underlines) + one line about the two tracks (Investor Path /
    Trader's Discipline) + the calibration promise: "The engine keeps a
    scorecard. You'll keep one too — we teach you to know how sure you
    really are." Small blind-spot-map thumbnail as a teaser.
S7 · FULL EDITION (subscription, newspaper framing): thin free edition vs
    thick full edition shown as two folded-paper mockups; founding print
    run of 20 · €99/yr price-locked · €9/mo after · 14-day unconditional
    refund; classifieds-style small-type FAQ (4 questions incl. "Is this
    investment advice? — No. Research and education; decisions are yours.")
S8 · COLOPHON FOOTER: waitlist email field ("The full dashboard opens by
    invitation"), Telegram link, methodology, imprint/privacy, and the
    permanent disclaimer set like a newspaper colophon.

═══════════════ SCREEN 1 — TODAY'S EDITION (app home, daily loop) ═══════════════
- Reads like the day's paper, structured like the classroom's daily loop:
  a) Greeting dateline: "Good morning — day 12 of your reading streak."
     (streak = a quiet row of filled ink dots; adult tone, no flames).
  b) THE DAILY DOUBLE at top (same bracket component as landing, now live):
     lesson card (violet, 3-min, mastery ring) ⌐ bracket ¬ case card
     (amber glow, today's top candidate with grade seal + margin-note terms).
  c) The full brief as an article: remaining candidates as news items,
     each with margin-note terms; free tier sees 1-2 items + an honest
     ledger line: "The system flagged 7 candidates today; you're reading 2.
     The Full Edition carries them all." (transparency-as-upsell, no blur
     tricks).
  d) "Yesterday — what happened?" closing card: yesterday's candidate with
     its outcome stamped (sage HIT / brick MISS / ink OPEN) + one serif
     reflection question ("The gap filled by Wednesday — which factor
     weakened first?") + confidence slider answer (see calibration).
  e) Right rail: mini Ledger + "today's term" glossary box.
- Colophon bar bottom, always.

═══════════════ SCREEN 2 — PAST EDITIONS (archive = case files) ═══════════════
- A timeline of folded editions (folder-meets-newspaper cards), newest
  amber, all others ink. Each opens the full edition as printed that day,
  with OUTCOME STAMPS pressed on each candidate ("HIT ≥5%", "MISS", "OPEN")
  and the original rationale preserved verbatim — "what we said that
  morning" is sacred, never edited.
- Study affordance: any past edition can be opened in "Classroom mode" —
  outcomes hidden, a scrub slider reveals the 5 days after, and the reader
  answers "watch / skip / study more?" with a confidence % before the
  reveal. This is the archive-as-simulator: 5,000 real cases, zero fiction.

═══════════════ SCREEN 3 — THE LEDGER (open scorecard) ═══════════════
- Full-page ledger: monthly report cards per grade; calendar heat-strip;
  the pinned "worst week" incident report (date, what failed, what changed)
  presented with newspaper correction-notice typography — maturity as brand.
- Calibration made visible: for each grade, a horizontal probability tape
  showing the CLAIMED band as a shaded zone and the ACTUAL hit-rate needle
  on or off that zone. Caption: "When the needle sits inside the shade,
  the probability was honest. That's calibration."
- Beneath, the mirror: "Your ledger" — the reader's own confidence-vs-
  accuracy chart from lesson answers, drawn in the same tape language.
  Line: "The paper grades itself. So do you."

═══════════════ SCREEN 4 — THE CLASSROOM (FinSense, full Template-3 spine) ═══════════════
- Two shelves: "Investor Path" and "Trader's Discipline Path" — module
  cards (12 domains) with whiteboard-sketch icons, mastery rings, and
  knowledge-prerequisite locks ("unlocks after Risk Basics") — never
  paywall locks on learning. A hand-drawn metro-map line connects modules;
  the reader's position is a small ink avatar.
- LESSON PAGE (the workhorse, three beats):
  1) EXPLAIN — 90-second read, whiteboard diagram, coral "common
     misconception" box ("everyone believes this at first").
  2) SHOW (amber = real) — an embedded dated case from the archive with the
     5-day scrub slider; trust line: "Every example is real, dated, and was
     graded before the outcome was known."
  3) TRY — one scenario question + the CONFIDENCE SLIDER (50–95%): the
     calibration trainer. Completion = quiet violet check + one sentence:
     "You can now read a squeeze setup unaided."
- BLIND-SPOT MAP: concept constellation sized by how often each concept
  appears in editions, colored by personal mastery (sage/ink/coral);
  "your three most expensive blind spots" each with a 3-minute fix CTA.
- Glossary: print-style three-column index; each term opens the same
  margin-note card grown into a full entry (definition → real dated
  example "as seen in the June 12 edition" → misconception → 3-question
  quiz set like a crossword corner).

═══════════════ SCREEN 5 — FULL EDITION (premium) ═══════════════
- Same as landing S7 expanded: side-by-side edition mockups, feature table
  (candidates/day, full rationale, risk notes, watch updates, weekly deep
  dive), founding print-run counter (real, fixed at 20), Stripe-link
  buttons in gold, refund + cancel-anytime lines, teacher-voice FAQ.

═══════════════ SIGNATURE COMPONENTS (reuse everywhere) ═══════════════
1. GRADE SEAL — wax-seal-inspired circular stamp (gold/steel/gray) with the
   letter embossed; small version for lists, large for lead candidates.
2. MARGIN NOTE — the FinSense fusion atom: dotted-underline term → gutter
   note (desktop) / bottom sheet (mobile), violet tick, "full lesson →".
3. DAILY DOUBLE BRACKET — hand-drawn bracket tying lesson↔case; draws on
   entry; vertical variant on mobile.
4. OUTCOME STAMP — pressed rubber-stamp (sage HIT / brick MISS / ink OPEN)
   with date; slight rotation (-3°), press-settle animation.
5. PROBABILITY TAPE — horizontal 0–100% tape with claimed-band shading,
   base-rate tick, and (in Ledger) the actual needle. One visual language
   for engine honesty AND reader calibration.
6. CONFIDENCE SLIDER — 50–95% serif-numbered slider used in lessons and
   yesterday-reflections; feeds "Your ledger".
7. COLOPHON BAR — persistent thin disclaimer, newspaper-colophon type.

═══════════════ STATES ═══════════════
- Market closed: "No edition today — markets closed (Independence Day).
  A perfect morning for the Classroom →" (lesson suggestion; the paper
  never fakes news).
- No candidates: "Today's best candidate is patience. We'd rather print
  nothing than invent something." + the day's lesson still arrives (the
  Daily Double degrades gracefully to a Single).
- Loading: a folding-paper shimmer, "Printing this morning's edition…".
- First-visit onboarding: 3 serif questions (goal: invest/trade/learn ·
  minutes per morning · experience) → picks the track and the first lesson.
- Mobile: single column; masthead condenses to "FP" monogram; margin notes
  become bottom sheets; bracket goes vertical; bottom tab bar (Edition /
  Archive / Ledger / Classroom).
```

---

**Not (uygulama tarafı):** Bu master şablon beğenildiğinde geçiş planı hazır — mevcut `demo/page.tsx` S2'nin (Yesterday's Front Page) çekirdeğidir; TermCard → Margin Note'a, Scorecard → Ledger Strip'e evrilir; Daily Double, brif snapshot'ı + `concepts.py` günün-kavramı eşleşmesinden beslenir (içerik hattı zaten her gün ikisini birlikte üretiyor). Landing S1-S8, `page.tsx` + HeroGrid'in yerini alır.
