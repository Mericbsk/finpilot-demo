"use client";

import { motion } from "framer-motion";

/* ─── Animation helpers ─── */
const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.12, duration: 0.7, ease: "easeOut" as const },
  }),
};

/* ─── Daily brief mockup (research framing — no buy/sell, no targets) ─── */
function ScanTable() {
  const rows = [
    { sym: "EXAS", grade: "A", band: "~65%", factors: "high short + gap", color: "text-[var(--accent-green)]" },
    { sym: "RXRX", grade: "B", band: "~60%", factors: "volume accel + catalyst", color: "text-[var(--accent-cyan)]" },
    { sym: "IONQ", grade: "B", band: "~55%", factors: "contraction \u2192 expansion", color: "text-[var(--accent-cyan)]" },
    { sym: "SOUN", grade: "C", band: "~45%", factors: "momentum, watch stage", color: "text-[var(--text-tertiary)]" },
    { sym: "PLUG", grade: "C", band: "~40%", factors: "regime supportive", color: "text-[var(--text-tertiary)]" },
  ];

  return (
    <div className="w-full rounded-xl border border-white/[0.08] bg-white/[0.015] overflow-hidden backdrop-blur-sm">
      <div className="grid grid-cols-4 gap-1 px-4 py-2.5 text-[9px] font-semibold uppercase tracking-[0.15em] text-[var(--text-tertiary)] border-b border-white/[0.06]">
        <span>Symbol</span><span className="text-center">Grade</span><span className="text-center">{"\u2265"}5% in 5d*</span><span className="text-right">Aligned factors</span>
      </div>
      {rows.map((r, i) => (
        <motion.div
          key={r.sym}
          initial={{ opacity: 0, x: -10 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.15 + i * 0.06, duration: 0.35 }}
          className="grid grid-cols-4 gap-1 px-4 py-2 text-[11px] border-b border-white/[0.03] last:border-0 hover:bg-white/[0.03] transition"
        >
          <span className="font-semibold text-white">{r.sym}</span>
          <span className={`text-center font-bold ${r.color}`}>{r.grade}</span>
          <span className="text-center text-[var(--text-secondary)]">{r.band}</span>
          <span className="text-right text-[var(--text-tertiary)]">{r.factors}</span>
        </motion.div>
      ))}
      <div className="px-4 py-1.5 text-[8px] text-[var(--text-tertiary)] border-t border-white/[0.04]">
        *historical frequency of a {"\u2265"}5% move within 5 days for this profile {"\u2014"} research grade, not advice
      </div>
    </div>
  );
}

/* ─── Factor alignment (explainable grade breakdown) ─── */
function EnsembleVoting() {
  const agents = [
    { name: "Short interest", vote: "ALIGNED", conf: 82, weight: 0.35, color: "var(--accent-green)" },
    { name: "Volume acceleration", vote: "ALIGNED", conf: 74, weight: 0.35, color: "var(--accent-green)" },
    { name: "Market regime", vote: "NEUTRAL", conf: 55, weight: 0.30, color: "var(--text-tertiary)" },
  ];

  return (
    <div className="space-y-2.5">
      {agents.map((a, i) => (
        <motion.div
          key={a.name}
          initial={{ opacity: 0, x: 14 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 + i * 0.08, duration: 0.35 }}
          className="flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] px-4 py-3"
        >
          <div className="h-2 w-2 rounded-full shrink-0" style={{ background: a.color }} />
          <span className="text-xs font-semibold text-white w-28">{a.name}</span>
          <div className="flex-1 h-1 rounded-full bg-white/[0.06] overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              whileInView={{ width: `${a.conf}%` }}
              viewport={{ once: true }}
              transition={{ delay: 0.4 + i * 0.1, duration: 0.7 }}
              className="h-full rounded-full"
              style={{ background: a.color }}
            />
          </div>
          <span className="text-[10px] text-[var(--text-tertiary)] w-8 text-right">{a.conf}%</span>
          <span className={`text-[10px] font-bold w-10 text-right`} style={{ color: a.color }}>{a.vote}</span>
        </motion.div>
      ))}
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.5, duration: 0.4 }}
        className="flex items-center justify-between rounded-lg bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/20 px-4 py-2.5"
      >
        <span className="text-xs font-bold text-[var(--accent-green)]">Combined grade: A</span>
        <span className="text-[10px] text-[var(--accent-green)]/70">calibrated ~65% (5d, {"\u2265"}5%)</span>
      </motion.div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════ */
export default function HeroGrid() {
  return (
    <section className="relative overflow-hidden">

      {/* ── Background glow ── */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute top-[-20%] left-1/2 -translate-x-1/2 w-[800px] h-[600px] rounded-full bg-[var(--accent-cyan)]/[0.04] blur-[120px]" />
        <div className="absolute top-[30%] right-[-10%] w-[400px] h-[400px] rounded-full bg-[var(--accent-blue)]/[0.03] blur-[100px]" />
      </div>

      <div className="relative px-4 sm:px-6 max-w-[1200px] mx-auto">

        {/* ════════════════ HERO ════════════════ */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          custom={0}
          className="pt-20 sm:pt-32 pb-6 text-center"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-1.5 mb-8">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent-green)] animate-pulse" />
            <span className="text-[11px] text-[var(--text-secondary)]">Scanning 1,800+ US stocks every morning</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-[72px] font-bold tracking-tight text-white leading-[1.06]">
            1,800 stocks scanned.<br />
            <span className="bg-gradient-to-r from-[var(--accent-cyan)] via-[var(--accent-blue)] to-[var(--accent-purple)] bg-clip-text text-transparent">
              3 candidates. Reasons included.
            </span>
          </h1>

          <p className="mt-6 text-base sm:text-lg text-[var(--text-secondary)] max-w-2xl mx-auto leading-relaxed">
            FinPilot is a research tool that flags stocks with unusual move potential — each
            candidate graded with a calibrated probability, an explanation, and an open
            scorecard you can check yourself. The decision is always yours.
          </p>

          <div className="mt-10 flex items-center justify-center gap-4">
            <a
              href="/demo"
              className="rounded-full bg-[var(--accent-blue)] px-7 py-3 text-sm font-semibold text-white hover:brightness-110 transition shadow-lg shadow-[var(--accent-blue)]/20"
            >
              See yesterday&apos;s brief →
            </a>
            <a
              href="#features"
              className="rounded-full border border-white/[0.12] px-7 py-3 text-sm font-medium text-[var(--text-secondary)] hover:text-white hover:border-white/[0.25] transition"
            >
              See How It Works
            </a>
          </div>
        </motion.div>

        {/* ════════════════ STATS BAR ════════════════ */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          custom={2}
          className="flex flex-wrap justify-center gap-x-8 sm:gap-x-14 gap-y-4 py-10 sm:py-14 border-b border-white/[0.06]"
        >
          {[
            { num: "1,800+", label: "Stocks scanned daily" },
            { num: "A/B/C", label: "Single research grade" },
            { num: "08:30", label: "Daily brief, one message" },
            { num: "Open", label: "Public scorecard" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-2xl sm:text-3xl font-bold text-white">{s.num}</div>
              <div className="text-[11px] text-[var(--text-tertiary)] mt-1 uppercase tracking-wider">{s.label}</div>
            </div>
          ))}
        </motion.div>

        {/* ════════════════ HOW IT WORKS — 3 steps ════════════════ */}
        <div className="py-16 sm:py-24">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-80px" }}
            custom={0}
            className="text-center mb-14"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
              Three steps. Zero guesswork.
            </h2>
            <p className="mt-3 text-sm text-[var(--text-secondary)] max-w-lg mx-auto">
              From raw market data to actionable signals — fully automated.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                step: "01",
                title: "Scan",
                desc: "Every morning, FinPilot scans 1,800+ US stocks across volume, volatility, short-interest, gap and catalyst patterns.",
                accent: "var(--accent-cyan)",
              },
              {
                step: "02",
                title: "Grade",
                desc: "Independent factors combine into a calibrated probability. Each candidate gets a single research Grade — A, B or C. Grade A is rare by design.",
                accent: "var(--accent-blue)",
              },
              {
                step: "03",
                title: "Verify",
                desc: "Every candidate's outcome is measured and published in the open scorecard — including the misses. You judge us on the record, not the pitch.",
                accent: "var(--accent-purple)",
              },
            ].map((s, i) => (
              <motion.div
                key={s.step}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-60px" }}
                custom={i}
                className="relative rounded-2xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-8 hover:border-white/[0.12] transition-colors group"
              >
                <div
                  className="text-[64px] font-black leading-none opacity-[0.06] absolute top-6 right-6 select-none"
                  style={{ color: s.accent }}
                >
                  {s.step}
                </div>
                <div
                  className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-sm font-bold mb-5"
                  style={{ background: `color-mix(in srgb, ${s.accent} 15%, transparent)`, color: s.accent }}
                >
                  {s.step}
                </div>
                <h3 className="text-xl font-bold text-white mb-2">{s.title}</h3>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>

        {/* ════════════════ FEATURE CARDS — 2×2 grid ════════════════ */}
        <div id="features" className="pb-6">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-80px" }}
            custom={0}
            className="text-center mb-12"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
              Built different.
            </h2>
            <p className="mt-3 text-sm text-[var(--text-secondary)] max-w-lg mx-auto">
              Not another dashboard. A system that thinks.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5 mb-4 sm:mb-5">

            {/* Card 1: Smart Scanner */}
            <motion.div
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-60px" }}
              custom={0}
              className="group relative rounded-2xl border border-white/[0.06] bg-gradient-to-b from-[#0d1117] to-[#080b10] p-8 sm:p-10 hover:border-[var(--accent-cyan)]/20 transition-all duration-500 overflow-hidden"
            >
              {/* Glow on hover */}
              <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[var(--accent-cyan)]/[0.04] to-transparent pointer-events-none" />
              <div className="relative">
                <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--accent-cyan)] mb-3">Smart Scanner</div>
                <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                  1,800+ stocks.<br />Every single morning.
                </h3>
                <p className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed max-w-md">
                  Volume acceleration, range contraction, short-interest, gaps and filings —
                  the scanner condenses the whole market into a short, graded daily brief.
                </p>
                <div className="mt-7">
                  <ScanTable />
                </div>
              </div>
            </motion.div>

            {/* Card 2: Risk Shield */}
            <motion.div
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-60px" }}
              custom={1}
              className="group relative rounded-2xl border border-white/[0.06] bg-gradient-to-b from-[#0d1117] to-[#080b10] p-8 sm:p-10 hover:border-[var(--accent-green)]/20 transition-all duration-500 overflow-hidden"
            >
              <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[var(--accent-green)]/[0.04] to-transparent pointer-events-none" />
              <div className="relative">
                <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--accent-green)] mb-3">Honest Measurement</div>
                <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                  Every claim has<br />a scorecard.
                </h3>
                <p className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed max-w-md">
                  Every candidate&apos;s outcome is recorded and measured against the market&apos;s
                  base rate. The scorecard is public — including the weeks we were wrong.
                </p>
                <div className="mt-7 grid grid-cols-2 gap-3">
                  {[
                    { label: "Calibration", val: "Weekly", sub: "probability vs reality", icon: "🎯" },
                    { label: "Base rate", val: "Always", sub: "lift over no-filter", icon: "📏" },
                    { label: "Outcomes", val: "5,000+", sub: "archived & resolved", icon: "🗂️" },
                    { label: "Misses", val: "Shown", sub: "bad weeks included", icon: "🪞" },
                  ].map((m, i) => (
                    <motion.div
                      key={m.label}
                      initial={{ opacity: 0, scale: 0.92 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ delay: 0.2 + i * 0.06, duration: 0.35 }}
                      className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 text-center hover:bg-white/[0.04] transition"
                    >
                      <div className="text-lg mb-1.5">{m.icon}</div>
                      <div className="text-base font-bold text-white">{m.val}</div>
                      <div className="text-[10px] text-[var(--text-tertiary)] mt-1">{m.label}</div>
                      <div className="text-[9px] text-[var(--text-tertiary)]">{m.sub}</div>
                    </motion.div>
                  ))}
                </div>
                {/* FinSense teaser */}
                <div className="mt-5 rounded-xl border border-[var(--accent-purple)]/15 bg-[var(--accent-purple)]/[0.04] px-5 py-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm">🎓</span>
                    <span className="text-[11px] font-semibold text-[var(--accent-purple)]">FinSense Academy</span>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                    100+ term glossary, interactive quizzes, and a compound interest calculator.
                    Learn as you invest.
                  </p>
                </div>
              </div>
            </motion.div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5 mb-4 sm:mb-5">

            {/* Card 3: AI Ensemble */}
            <motion.div
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-60px" }}
              custom={0}
              className="group relative rounded-2xl border border-white/[0.06] bg-gradient-to-b from-[#10111a] to-[#080b10] p-8 sm:p-10 hover:border-[var(--accent-blue)]/20 transition-all duration-500 overflow-hidden"
            >
              <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[var(--accent-blue)]/[0.04] to-transparent pointer-events-none" />
              <div className="relative">
                <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--accent-blue)] mb-3">Explainable Grades</div>
                <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                  Independent factors.<br />One transparent grade.
                </h3>
                <p className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed max-w-md">
                  Short-interest, volume acceleration, gaps, catalysts and market regime are
                  scored independently and combined into a calibrated probability — every
                  factor visible, nothing hidden behind a black box.
                </p>
                <div className="mt-7">
                  <EnsembleVoting />
                </div>
              </div>
            </motion.div>

            {/* Card 4: Battle-Tested */}
            <motion.div
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-60px" }}
              custom={1}
              className="group relative rounded-2xl border border-white/[0.06] bg-gradient-to-b from-[#10111a] to-[#080b10] p-8 sm:p-10 hover:border-[var(--accent-blue)]/20 transition-all duration-500 overflow-hidden"
            >
              <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[var(--accent-blue)]/[0.04] to-transparent pointer-events-none" />
              <div className="relative">
                <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--accent-blue)] mb-3">Validation-First</div>
                <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                  We don&apos;t guess.<br />We measure.
                </h3>
                <p className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed max-w-md">
                  In-sample vs out-of-sample splits, walk-forward checks and weekly edge
                  reports. A factor that fails validation never reaches your brief.
                </p>
                <div className="mt-7 space-y-3">
                  {[
                    { label: "Archived signals", val: "5,000+", bar: 85 },
                    { label: "Edge report", val: "Weekly", bar: 70 },
                    { label: "Out-of-sample", val: "Always", bar: 90 },
                    { label: "Config-stamped", val: "Every run", bar: 80 },
                  ].map((m, i) => (
                    <motion.div
                      key={m.label}
                      initial={{ opacity: 0 }}
                      whileInView={{ opacity: 1 }}
                      viewport={{ once: true }}
                      transition={{ delay: 0.2 + i * 0.06, duration: 0.4 }}
                      className="flex items-center gap-3"
                    >
                      <span className="text-[11px] text-[var(--text-tertiary)] w-28 shrink-0">{m.label}</span>
                      <div className="flex-1 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          whileInView={{ width: `${m.bar}%` }}
                          viewport={{ once: true }}
                          transition={{ delay: 0.4 + i * 0.08, duration: 0.8, ease: "easeOut" }}
                          className="h-full rounded-full bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)]"
                        />
                      </div>
                      <span className="text-xs font-semibold text-white w-14 text-right">{m.val}</span>
                    </motion.div>
                  ))}
                </div>
                {/* PilotShield badge */}
                <div className="mt-6 rounded-xl border border-[var(--accent-cyan)]/15 bg-[var(--accent-cyan)]/[0.04] px-5 py-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm">🔬</span>
                    <span className="text-[11px] font-semibold text-[var(--accent-cyan)]">Methodology, open</span>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                    How grades are computed, what they measure and what they don&apos;t —
                    documented on the demo page next to the scorecard. Judge the record, not the pitch.
                  </p>
                </div>
              </div>
            </motion.div>
          </div>
        </div>

        {/* ════════════════ DIFFERENTIATOR ════════════════ */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-60px" }}
          custom={0}
          className="py-16 sm:py-20 text-center border-t border-b border-white/[0.06]"
        >
          <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-[var(--accent-cyan)] mb-6">What makes us different</p>
          <h2 className="text-2xl sm:text-4xl font-bold text-white tracking-tight max-w-3xl mx-auto leading-snug">
            Most tools sell certainty.<br />
            <span className="text-[var(--text-secondary)]">
              FinPilot sells calibrated probabilities and publishes its own scorecard — including the misses.
            </span>
          </h2>
          <div className="mt-10 flex flex-wrap justify-center gap-3">
            {["Calibrated Probability", "Point-in-Time Data", "Regime Awareness", "Open Scorecard", "Out-of-Sample Validation", "Daily Telegram Brief"].map((tag) => (
              <span
                key={tag}
                className="rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-1.5 text-[11px] text-[var(--text-secondary)]"
              >
                {tag}
              </span>
            ))}
          </div>
        </motion.div>

        {/* ════════════════ FINAL CTA ════════════════ */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-40px" }}
          custom={0}
          className="py-20 sm:py-28 text-center"
        >
          <h2 className="text-3xl sm:text-5xl font-bold text-white tracking-tight">
            See yesterday&apos;s brief. Judge for yourself.
          </h2>
          <p className="mt-4 text-base text-[var(--text-secondary)] max-w-md mx-auto">
            Real scan output, dated and frozen — no sign-up required. Today&apos;s edition
            arrives on Telegram every morning at 08:30.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4 flex-wrap">
            <a
              href="/demo"
              className="rounded-full bg-[var(--accent-blue)] px-8 py-3.5 text-sm font-semibold text-white hover:brightness-110 transition shadow-lg shadow-[var(--accent-blue)]/20"
            >
              See yesterday&apos;s brief →
            </a>
            <a
              href="#waitlist"
              className="rounded-full border border-white/[0.12] px-8 py-3.5 text-sm font-medium text-[var(--text-secondary)] hover:text-white hover:border-white/[0.25] transition"
            >
              Join the beta waitlist
            </a>
          </div>
          <p className="mt-8 text-[11px] text-[var(--text-tertiary)]">
            1,800+ stocks daily · graded candidates · open scorecard · daily Telegram brief
          </p>
          <p className="mt-4 text-[10px] text-[var(--text-tertiary)] max-w-xl mx-auto">
            FinPilot is a research and education tool; it does not provide investment advice.
            Past performance does not guarantee future results.
          </p>
        </motion.div>

      </div>
    </section>
  );
}
