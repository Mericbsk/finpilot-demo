# FinPilot × FinSense — 3 Profesyonel Web Tasarım Şablonu
### Claude Design'da denemek için hazır, yapıştır-çalıştır tasarım brief'leri

**Tarih:** 2026-07-05 · Her şablon gerçek veri sözleşmemize bağlıdır (`demo_snapshot.json`: grade, prob_band, badges, rationale, karne) — yani beğendiğin tasarım doğrudan mevcut backend'e bağlanabilir, "uçtan uca çalışma potansiyeli" buradan gelir.
**Kullanım:** Aşağıdaki üç bloktan birini olduğu gibi kopyala, Claude Design'a yapıştır. Prompt'lar İngilizce yazıldı (tasarım araçları İngilizce brief'le belirgin şekilde daha iyi sonuç verir); her birinin başında Türkçe konsept özeti var.

Üç şablon üç farklı ruhu dener — aynı ürün, üç kimlik:

| # | Konsept | Ruh | FinSense füzyonu |
|---|---|---|---|
| 1 | **The Morning Ledger** | Sakin editoryal — "piyasanın sabah gazetesi" | Her kavram metnin içinde canlı dipnot |
| 2 | **Cockpit** | Hassas enstrüman paneli — pilot metaforu | Öğrenme = uçuş okulu; ustalık göstergeleri panelin parçası |
| 3 | **The Open Classroom** | Sıcak, öğrenme-öncelikli — "piyasadan öğren" | FinPilot brifi günün vaka çalışması olarak derste yaşar |

---
---

## ŞABLON 1 — "THE MORNING LEDGER"
**Türkçe özet:** Finans sitesi gibi değil, kaliteli bir sabah gazetesi gibi hisseden tasarım. Günün brifi baş makale; karne her sayfada görünen dürüstlük şeridi; FinSense terimler metnin içinde altı çizili canlı dipnotlar olarak yaşar. Sakinlik ve güven satar — rakip fintech'lerin neon kumarhane estetiğinin tam tersi.

```
Design a complete, production-grade marketing site + product web app called
"FinPilot — The Morning Ledger". FinPilot is a stock-market research copilot
that scans 1,800+ US stocks every morning, grades the most interesting
candidates (A/B/C) with calibrated probabilities and plain-language reasons,
and publishes an OPEN scorecard of its own hits and misses. Its learning layer,
FinSense, teaches financial concepts contextually — every term is explained
where it appears. This is decision support and education, never investment
advice; the words BUY/SELL, price targets, or profit promises must never appear.

═══ CONCEPT ═══
"The market's morning newspaper." Calm, editorial, trustworthy — the opposite
of neon fintech dashboards. Think Financial Times print elegance meets a quiet
dark-mode reading app. The daily brief is the front-page story; the scorecard
is the paper's masthead promise; learning is woven into the copy like living
footnotes.

═══ BRAND SYSTEM ═══
- Background: deep ink navy #0B0F1A with a very subtle paper-grain texture.
- Surface cards: #121826 with 1px hairline borders (#FFFFFF at 8% opacity).
- Accent: single warm gold #E8C468 used ONLY for Grade A and key CTAs;
  Grade B = muted steel blue #7FA6C9; Grade C = warm gray #9AA3B2.
- Success/miss in scorecard: sage green #7FB58A / soft brick #C97F7F
  (never aggressive red/green — this is a newspaper, not a casino).
- Typography: headlines in an elegant serif (e.g. "Fraunces" or "Source
  Serif 4"), body/UI in "Inter". Big generous line-height, max 68ch measure.
- Motion: almost none. Fades of 200ms. The calm IS the brand.

═══ INFORMATION ARCHITECTURE ═══
1. Front Page (landing) 2. Today's Brief (the product) 3. The Scorecard
4. FinSense Library 5. Premium ("Full Edition") 6. About/Methodology

═══ SCREEN 1 — FRONT PAGE ═══
- Masthead: "FINPILOT" in serif smallcaps, date line "Vienna · Tuesday,
  July 7 2026 · Markets open in 2h 14m", thin double rule under it (newspaper
  style).
- Headline block: "1,800 stocks read before your coffee." Subhead: "Three
  candidates a morning, each with its reasons — and a public scorecard we
  can't hide from."
- Below the fold: an actual rendered "front page article" = yesterday's real
  brief as editorial content: dateline, lede paragraph, then three candidate
  entries typeset like news items (see Screen 2 card spec). This section is
  labeled "Yesterday's Edition — real, frozen".
- Right rail (desktop): "The Ledger" box — scorecard summary as a small
  elegant table (Grade A: 67% of 21 · B: 55% of 118 · C: 41% of 264, window
  label) with a footnote glyph linking to methodology.
- Footer of hero: two quiet CTAs — primary gold text-button "Read yesterday's
  edition", secondary "Get the daily edition on Telegram, 08:30".
- Persistent thin disclaimer bar at page bottom (like a newspaper colophon):
  "Research & education. Not investment advice. Past results ≠ future results."

═══ SCREEN 2 — TODAY'S BRIEF (core product) ═══
- Page behaves like an article, not a dashboard. Title: "The Brief — July 7".
- Lede: one-sentence market context ("Regime: risk-on; quiet macro calendar.")
- CANDIDATE ENTRY (repeat 3x), typeset like a refined news item:
  · Ticker as a drop-cap style monogram block ($EXAS) + company name.
  · Grade appears as a wax-seal-inspired circular stamp (gold A / steel B /
    gray C) at the entry's top-right — the signature visual of this design.
  · One italic serif line: "Candidates with this profile moved ≥5% within
    five days about ~65% of the time."
  · Body: 2-sentence rationale in body type. Inside the body, financial terms
    (short interest, gap, RVOL) are set with a fine dotted underline — these
    are FINSENSE LIVING FOOTNOTES: hover/tap opens a footnote card at the
    paragraph's edge (desktop: margin note in the right gutter,真 newspaper
    style; mobile: bottom sheet) with a 60-word plain explanation + "read the
    full lesson" link. This margin-note mechanic is the FinSense fusion —
    learning lives inside the reading flow, never in a separate tab.
  · Risk note as smaller "editor's note:" line.
- After entries: "The Ledger" full-width strip — horizontal bar showing today's
  totals ("The system flagged 7 candidates today; you read 3. The full list
  is in the Full Edition.") — transparency as upsell, no dark patterns.
- End of article: byline block "Compiled by the FinPilot engine · reviewed by
  a human editor · config #cbe5cf" (the config stamp shown like a print run
  number — a trust detail).

═══ SCREEN 3 — THE SCORECARD ═══
- Full page ledger table: month by month, grade by grade; hits and misses in
  sage/brick dots forming a calendar heat-strip. Headline: "We keep score,
  including the misses." A pull-quote style callout: "Last bad week: June
  23–27, Grade B hit 2 of 9. It's on the record."
- Methodology accordion in plain language + a small "what this does NOT
  mean" box (serif italic) — compliance as brand voice.

═══ SCREEN 4 — FINSENSE LIBRARY ═══
- Presented as the paper's "Glossary & School" section: alphabetical index
  in three columns (print-style), each term opens the same footnote card
  grown into a full lesson page: definition → real example from a dated past
  brief ("as seen in the June 12 edition") → one misconception → 3-question
  quiz styled as a crossword-corner puzzle box.
- Personal progress shown as a subtle "reading level" line under the section
  title: "You've mastered 14 of 120 entries — today's suggested read: RVOL."

═══ SCREEN 5 — FULL EDITION (premium) ═══
- Newspaper subscription framing: "The Full Edition — every candidate, every
  reason, every risk note. €9/month, founding print run of 20 at €99/year,
  price locked." Comparison as two newspaper mockups side by side (thin free
  edition vs thick full edition). 14-day unconditional refund line. FAQ set
  in classifieds-style small type.

═══ STATES & DETAILS ═══
- Loading: a folding-paper shimmer, one line: "Printing this morning's
  edition…". Market-closed state: "No edition today — markets closed for
  Independence Day. Next edition Monday." Empty candidates: "Today's best
  candidate is patience. We'd rather print nothing than invent something."
- Mobile: single column, margin notes become bottom-sheets, masthead
  condenses to monogram "FP".
- Every screen includes the colophon disclaimer bar.
```

---
---

## ŞABLON 2 — "COCKPIT"
**Türkçe özet:** İsimdeki metaforu sonuna kadar kullanan tasarım: FinPilot = kokpit, kullanıcı = pilot, FinSense = uçuş okulu. Hassas enstrüman estetiği (havacılık göstergeleri, checklist disiplini), oyunlaştırılmış ama çocuksu olmayan ustalık sistemi: bilmediğin göstergenin camı "buzlu" durur, dersi bitirince netleşir. En cesur, en ürün-hissiyatlı şablon.

```
Design a complete web application called "FinPilot Cockpit" — a stock-market
research copilot with an integrated flight-school learning system (FinSense).
FinPilot scans 1,800+ US stocks each morning and grades top candidates A/B/C
with calibrated probabilities, factor badges and plain reasons; an OPEN
scorecard tracks every outcome including misses. Strictly decision-support +
education: no BUY/SELL words, no price targets, no profit promises, disclaimer
visible on every screen.

═══ CONCEPT ═══
A precision flight deck for markets. The user is the pilot; FinPilot is the
instrument panel and co-pilot voice; FinSense is flight school — and the two
are mechanically fused: instruments you haven't been trained on render
slightly FROSTED (readable but muted) with a small "training available" chip;
completing the 3-minute lesson polishes the glass permanently. Competence,
not gambling adrenaline.

═══ BRAND SYSTEM ═══
- Background: graphite cockpit black #0A0C10 with a faint brushed-metal
  vertical gradient; panels are inset cards #10141C with soft inner shadow
  (recessed instrument look) and 2px rounded bezels.
- Instrument accents: phosphor amber #FFB454 (primary, Grade A, active
  states), HUD cyan #6FD3E7 (Grade B, info), neutral #8B93A3 (Grade C).
  Scorecard hit/miss: calm green #6FBF8F / amber-red #D98A6A.
- Typography: "IBM Plex Sans" for UI, "IBM Plex Mono" for all numbers,
  tickers, timestamps (every numeral on the deck is mono — instrument DNA).
- Texture details: fine tick-marks on gauge edges, tiny engraved labels in
  8px uppercase tracking-wide, toggle switches with satisfying 150ms snap.
- Motion: needle sweeps (400ms ease-out) when gauges load; radar ping on
  scan refresh; nothing bounces, nothing floats — everything is mounted.

═══ INFORMATION ARCHITECTURE ═══
Left vertical rail (thin, icon+label): 1. Flight Deck (home) 2. Radar
(today's candidates) 3. Black Box (scorecard) 4. Flight School (FinSense)
5. Checklists 6. Full Clearance (premium). Top bar: UTC+Vienna dual clock,
market phase indicator (PRE-FLIGHT / IN-SESSION / GROUNDED), pilot avatar
with license level.

═══ SCREEN 1 — FLIGHT DECK (daily home) ═══
- Hero row of three INSTRUMENT CLUSTERS:
  a) "Morning Sweep" gauge — a half-circle dial showing 1,812 stocks swept,
     needle settling on candidates found (7); below it the timestamp
     "sweep completed 07:46".
  b) "Today's Grade Panel" — three vertical lamp indicators (A/B/C) with
     count lights: A×1 lit amber, B×2 cyan, C×4 dim.
  c) "System Integrity" — the scorecard-in-miniature: a small horizontal
     strip of the last 20 outcomes as hit/miss lamps + "calibration OK,
     last check Mon 04:00" engraved label. Clicking opens Black Box.
- Below: PRIMARY FLIGHT CARD — today's top candidate as the main instrument:
  large mono ticker $EXAS, Grade A amber seal, a linear "probability tape"
  (aviation-style horizontal tape from 0–100% with a marker at ~65% and the
  base-rate marked as a second small tick at 17% — SHOWING LIFT VISUALLY),
  factor badges as cockpit annunciator lights [SQUEEZE][GAP][RVOL] — lit
  badges are trained concepts, frosted badges show a tiny 🎓 chip.
  Co-pilot voice line beneath in italics: "High short interest plus a gap
  open — squeeze conditions. Your call, captain. Risk note: high volatility."
- FinSense fusion strip: "Pre-flight training — 3 min: Reading the RVOL
  gauge" with a progress ring showing license progress (Student → Private →
  Instrument → Commercial ratings as license levels, engraved card).
- Persistent bottom status bar: "Research instrument only — not investment
  advice. You are pilot in command." (compliance written IN the metaphor).

═══ SCREEN 2 — RADAR (all candidates) ═══
- Centerpiece: a circular radar scope (max 420px) — today's graded candidates
  as blips at radius = probability band (closer to center = higher), blip
  color by grade; sweep line rotates once on load. Hover a blip → heads-up
  readout card pins to the right with the full candidate card.
- Right column: the same candidates as a strict instrument LIST (mono table:
  TICKER | GRADE | P-BAND | FACTORS | RISK) for people who hate radars —
  toggle "SCOPE / TABLE" as a physical switch.
- Free tier sees 3 blips sharp, others as faded "restricted airspace" blips
  with count ("4 more in Full Clearance") — honest, visible, not fake-blurred.

═══ SCREEN 3 — BLACK BOX (scorecard) ═══
- Named for the flight recorder: "Every flight is recorded. Every one."
- Cockpit-voice-recorder aesthetic: a long vertical tape of dated entries,
  each with grade seal, outcome lamp (HIT ≥5% / MISS / OPEN), and the
  original reason preserved verbatim ("what we said that morning").
- Top: three analog-style calibration dials — "Grade A accuracy 67%",
  "B 55%", "C 41%" — each dial face shows the claimed probability band as a
  shaded arc and the actual needle position ON or OFF that arc. The needle
  sitting inside the shaded arc = calibration, made visible. This is the
  design's signature honesty instrument.
- A "worst week" flight report card is always pinned: date, what failed,
  what changed — presented like an incident report, badge of maturity.

═══ SCREEN 4 — FLIGHT SCHOOL (FinSense) ═══
- Hangar layout: courses as aircraft in a hangar (cards with schematic
  line-drawings): "Instruments 101" (RVOL, ATR, gaps), "Weather" (regimes,
  macro), "Emergency Procedures" (risk, position sizing, drawdowns),
  "Advanced Ratings" (calibration, base rates — the meta-skills).
- Each lesson = pre-flight briefing format: 90-second read → one real
  radar replay from the archive ("June 12, $RXRX — what did the instruments
  show? What happened in 5 days?") → 3 checklist questions → gauge unlocked
  animation (frost clears on the corresponding cockpit instrument, with a
  soft wipe — THE reward moment of the whole app).
- License progress card: current rating, next checkride, streak shown as
  "consecutive flight days" counter in mono.

═══ SCREEN 5 — CHECKLISTS ═══
- Printable/interactive discipline cards: "Morning brief checklist",
  "Before adding to watchlist", "After a losing week". Each item toggleable
  with the physical-switch component. This screen sells the real product:
  discipline. Free feature, heavily shareable.

═══ SCREEN 6 — FULL CLEARANCE (premium) ═══
- Framed as clearance level, not paywall: comparison as two cockpit layouts
  (VFR free vs IFR full: all candidates, full factor breakdowns, risk notes,
  watch updates). €9/mo, founding crew 20 seats €99/yr price-locked,
  14-day unconditional refund. Stripe payment link buttons styled as
  guarded toggle switches (flip cover + confirm).

═══ STATES ═══
- Market closed: deck in "GROUNDED" mode — instruments dimmed, message
  "Tower closed (US holiday). Next sweep Monday 07:45." Loading: needles
  sweep to position. No-candidates day: all grade lamps dark + co-pilot
  line "Clear skies, nothing worth flying today. Patience is a position."
- Mobile: rail becomes bottom tab bar; radar defaults to TABLE mode;
  primary flight card stacks. Numbers stay mono everywhere.
```

---
---

## ŞABLON 3 — "THE OPEN CLASSROOM"
**Türkçe özet:** Öğrenme-öncelikli tasarım: kapıdan FinSense girersin, FinPilot'un canlı brifi "günün vaka çalışması" olarak dersin içinde yaşar. Duolingo'nun bağlılık mekaniği + yetişkin ciddiyeti. Hibe anlatısıyla (financial literacy) en uyumlu yüz; "önce anla, sonra izle" felsefesini ekrana döker. Sıcak, davetkâr, ama asla çocuksu değil.

```
Design a complete learning-first web platform called "FinPilot Open Classroom"
that fuses a financial-literacy academy (FinSense) with a live market research
engine (FinPilot). The engine scans 1,800+ US stocks every morning and grades
candidates A/B/C with calibrated probabilities, factor badges, plain-language
reasons and an OPEN scorecard including misses. The twist: here, LEARNING is
the front door — the live brief exists inside lessons as "today's case study".
Education + research only; never BUY/SELL language, price targets or profit
promises; a friendly disclaimer is always visible.

═══ CONCEPT ═══
"Learn the market from the market." A warm, serious night-school where every
concept is taught with THIS morning's real data, and every real candidate
becomes a teachable case. Duolingo's habit mechanics with adult gravity —
progress feels like growing judgment, not collecting gems.

═══ BRAND SYSTEM ═══
- Background: warm charcoal #14161C (softer than pure black); cards in
  #1C1F28 with 12px radius and gentle 1px warm borders.
- Palette: chalk cream #F2EAD8 (primary text), teacher's green #9BC4A0
  (progress, mastery, Grade context), amber highlight #E9B872 (today/live
  elements — everything LIVE glows faintly amber, everything ARCHIVED is
  neutral: liveness as a color system), dusty violet #A99AC6 (FinSense
  identity), soft coral #D89090 for misses/mistakes (never shaming red).
- Typography: "Sora" for headings (geometric warmth), "Inter" for body,
  "JetBrains Mono" only for tickers/numbers. Slightly larger base size
  (17px) — a reading platform.
- Texture: subtle chalk-dust noise on section headers; hand-drawn-style
  underlines (SVG squiggle) for key phrases; diagrams look like clean
  whiteboard sketches (2px strokes, slightly imperfect).
- Motion: gentle. Cards rise 4px on hover; mastery ring fills with a soft
  chalk-swipe sound-feel; confetti NEVER — completion gives a quiet green
  checkmark and one sentence of real praise ("You can now read a squeeze
  setup unaided.").

═══ INFORMATION ARCHITECTURE ═══
Top nav: 1. Today (home) 2. Learning Paths 3. Market Case Files (the brief)
4. My Blind-Spot Map 5. Scorecard 6. Go Deeper (premium).

═══ SCREEN 1 — TODAY (daily loop home) ═══
- Greeting header: "Good morning, Meriç — day 12 of your streak. The market
  opens in 2h." (streak shown as a simple row of filled dots, adult tone).
- THE DAILY DOUBLE — the screen's core, two linked cards side by side:
  a) LESSON OF THE DAY (violet accent): "Relative Volume — 3 minutes" with
     a whiteboard-sketch icon and a progress ring.
  b) TODAY'S CASE FILE (amber glow = live): the real morning brief's top
     candidate as a case card — $EXAS, Grade A seal, probability sentence,
     factor chips. A connecting bracket visually TIES card (a) to card (b)
     with the label "today's lesson appears in today's market →" whenever
     the engine's top candidate actually contains the taught concept (the
     content system guarantees this pairing daily). This bracket is the
     signature fusion element of the whole design.
- Below: "Continue your path" (next 3 lessons as small cards with mastery
  rings) + "Yesterday's case — what happened?" outcome card: yesterday's
  candidate with its 5-day-later result revealed (hit/miss/open) and one
  reflection question ("The gap filled by Wednesday. Which factor weakened
  first?") — closing the learning loop with real outcomes.
- Right rail: mini scorecard ("The engine's own report card — A: 67% of 21")
  and the daily concept from the glossary.
- Footer disclaimer in teacher voice: "We teach judgment, not tips. Nothing
  here is investment advice."

═══ SCREEN 2 — LEARNING PATHS ═══
- Two tracks as two shelves: "The Investor Path" and "The Trader's
  Discipline Path" — each a horizontal shelf of module cards (12 domains:
  foundations, risk, technical, behavioral, options intro…), cards show a
  whiteboard sketch, lesson count, and a mastery ring. Locked modules show
  their prerequisite ("unlocks after Risk Basics") — knowledge locks, never
  paywall locks in learning.
- A path map line (hand-drawn style) connects modules like a metro map;
  the user's position is a small chalk avatar.

═══ SCREEN 3 — LESSON PAGE (the workhorse) ═══
- Split rhythm layout, one concept per screen-third:
  1) EXPLAIN: 90-second read, whiteboard diagram, one "common misconception"
     box in coral with a gentle "everyone believes this at first" tone.
  2) SHOW (amber = live/real): an embedded REAL example — an archived case
     file with actual dated chart ("March 14: $SOUN showed RVOL 3.2 — here's
     the day after"), interactive: a slider scrubs the 5 days AFTER, letting
     the learner feel outcome uncertainty. Archive of 5,000 resolved signals
     powers infinite real examples — say this in a small trust line:
     "Every example on this platform is real, dated, and was graded before
     the outcome was known."
  3) TRY: one scenario question ("You see this setup — watch, skip, or
     study more?") + confidence slider ("How sure are you? 50–95%") — the
     CALIBRATION TRAINER: over weeks the app shows "when you say 80% sure,
     you're right 61% of the time" on the Blind-Spot Map. This is the
     platform's unique mechanic — it teaches the exact skill the engine
     itself practices (calibration), user and machine measured the same way.
- Lesson footer: mastery ring fills; "This concept appears in 3 of this
  week's case files →" link into Market Case Files.

═══ SCREEN 4 — MARKET CASE FILES (the FinPilot brief, reframed) ═══
- The daily brief presented as a case-file folder UI: today's folder (amber,
  live) on top, past folders below in a timeline. Inside a folder: candidate
  cards (Grade seal, probability line, factor chips where every chip is a
  mini-lesson link, risk note in teacher voice) and — for past folders —
  the OUTCOME stamped across the corner (HIT ≥5% / MISS / OPEN) in honest
  ink. Free tier: 3 candidates per folder visible; a quiet line notes the
  full folder is in "Go Deeper".
- A study mechanic: "Annotate" — learners can highlight a factor chip and
  the margin explains it; annotated terms feed their Blind-Spot Map.

═══ SCREEN 5 — MY BLIND-SPOT MAP ═══
- The personal signature screen: a heat-mapped concept constellation —
  every glossary concept as a node, sized by how often it appears in cases,
  colored by the user's mastery (green mastered, neutral unseen, coral
  weak). Beneath: "Your three most expensive blind spots" (weak concepts
  that appeared most in recent case files) each with a "3-minute fix" CTA.
- Calibration corner: personal confidence-vs-accuracy chart (the same dial
  language as the engine's scorecard — human and machine, same honest
  mirror). Line: "The engine keeps a scorecard. So do you."

═══ SCREEN 6 — SCORECARD + GO DEEPER ═══
- Scorecard: same open-ledger content as the engine's record, presented as
  "the teacher grades itself" — monthly report cards, worst week pinned,
  methodology in plain words.
- Go Deeper (premium): "The full case file, every day" — all candidates,
  full factor breakdowns, risk notes, watch-updates + advanced lessons.
  €9/month or founding class of 20 at €99/year, 14-day unconditional
  refund. Framed as tuition, warm not salesy; comparison table in the
  whiteboard style.

═══ STATES ═══
- Market closed: Today screen swaps the case card for "Markets are closed —
  perfect day for the Weather module" (lesson suggestion). Empty candidates:
  "The engine found nothing worth a case file today. Lesson: most days are
  no-trade days — here's why that's a skill." Loading: chalk line draws
  across. Mobile: Daily Double stacks vertically, bracket becomes a vertical
  tie; bottom tab nav (Today / Paths / Cases / Map).
```

---

## Hangisini seçmeli? (kısa rehber)

- **Güven + Avrupa/hibe ciddiyeti + en hızlı uygulanabilirlik** → Şablon 1 (mevcut Next.js yapısına en yakın; bileşen sayısı en az).
- **Ürün kimliği + akılda kalıcılık + "vay be" etkisi** → Şablon 2 (kalibrasyon kadranı ve buzlu-cam ustalık mekaniği rakipsiz; uygulaması en emek isteyen).
- **FinSense vizyonu + financial-literacy hibe anlatısı + davranış değişimi** → Şablon 3 (Daily Double + kalibrasyon antrenörü, FinSense tasarım dokümanının ruhunu birebir ekrana taşır).

Üçü de aynı veri sözleşmesiyle çalışır; Claude Design çıktısını beğendiğinde seçileni gerçek `demo_snapshot.json` alanlarına bağlamak benim tarafımda 1-2 günlük iştir.
