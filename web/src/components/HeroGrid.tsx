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

/* ─── Scan table mockup ─── */
function ScanTable() {
  const rows = [
    { sym: "NVDA", score: 87, signal: "BUY", entry: "$179.00", sl: "$168.50", tp: "$198.00", rr: "1.8", color: "text-[var(--accent-green)]" },
    { sym: "META", score: 79, signal: "BUY", entry: "$634.60", sl: "$608.00", tp: "$682.00", rr: "1.8", color: "text-[var(--accent-green)]" },
    { sym: "AAPL", score: 74, signal: "BUY", entry: "$257.10", sl: "$245.80", tp: "$275.50", rr: "1.6", color: "text-[var(--accent-green)]" },
    { sym: "MSFT", score: 52, signal: "HOLD", entry: "—", sl: "—", tp: "—", rr: "—", color: "text-[var(--text-tertiary)]" },
    { sym: "TSLA", score: 38, signal: "SELL", entry: "$386.60", sl: "$405.00", tp: "$348.00", rr: "2.1", color: "text-[var(--accent-red)]" },
  ];

  return (
    <div className="w-full rounded-xl border border-white/[0.08] bg-white/[0.015] overflow-hidden backdrop-blur-sm">
      <div className="grid grid-cols-7 gap-1 px-4 py-2.5 text-[9px] font-semibold uppercase tracking-[0.15em] text-[var(--text-tertiary)] border-b border-white/[0.06]">
        <span>Symbol</span><span className="text-center">Score</span><span className="text-center">Signal</span>
        <span className="text-right">Entry</span><span className="text-right">Stop</span><span className="text-right">Target</span><span className="text-right">R/R</span>
      </div>
      {rows.map((r, i) => (
        <motion.div
          key={r.sym}
          initial={{ opacity: 0, x: -10 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.15 + i * 0.06, duration: 0.35 }}
          className="grid grid-cols-7 gap-1 px-4 py-2 text-[11px] border-b border-white/[0.03] last:border-0 hover:bg-white/[0.03] transition"
        >
          <span className="font-semibold text-white">{r.sym}</span>
          <span className="text-center"><span className="inline-block min-w-[28px] rounded-full bg-white/[0.06] px-2 py-0.5 text-[10px] font-medium">{r.score}</span></span>
          <span className={`text-center font-bold ${r.color}`}>{r.signal}</span>
          <span className="text-right text-[var(--text-secondary)]">{r.entry}</span>
          <span className="text-right text-[var(--text-tertiary)]">{r.sl}</span>
          <span className="text-right text-[var(--text-tertiary)]">{r.tp}</span>
          <span className="text-right font-medium">{r.rr}</span>
        </motion.div>
      ))}
    </div>
  );
}

/* ─── Ensemble voting ─── */
function EnsembleVoting() {
  const agents = [
    { name: "Trend Agent", vote: "BUY", conf: 92, weight: 0.50, color: "var(--accent-green)" },
    { name: "Range Agent", vote: "HOLD", conf: 61, weight: 0.20, color: "var(--text-tertiary)" },
    { name: "Volatility Agent", vote: "BUY", conf: 74, weight: 0.30, color: "var(--accent-green)" },
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
        <span className="text-xs font-bold text-[var(--accent-green)]">Consensus: BUY</span>
        <span className="text-[10px] text-[var(--accent-green)]/70">88% confidence</span>
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
            <span className="text-[11px] text-[var(--text-secondary)]">Now scanning 1,500+ symbols daily</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-[72px] font-bold tracking-tight text-white leading-[1.06]">
            AI that reads the market<br />
            <span className="bg-gradient-to-r from-[var(--accent-cyan)] via-[var(--accent-blue)] to-[var(--accent-purple)] bg-clip-text text-transparent">
              so you don&apos;t have to.
            </span>
          </h1>

          <p className="mt-6 text-base sm:text-lg text-[var(--text-secondary)] max-w-2xl mx-auto leading-relaxed">
            FinPilot scans 1,500+ stocks, runs 12 trained reinforcement learning models,
            and delivers clear buy/hold/sell signals with built-in risk management.
            Not an LLM wrapper — real AI, real decisions.
          </p>

          <div className="mt-10 flex items-center justify-center gap-4">
            <a
              href="/demo"
              className="rounded-full bg-[var(--accent-blue)] px-7 py-3 text-sm font-semibold text-white hover:brightness-110 transition shadow-lg shadow-[var(--accent-blue)]/20"
            >
              Try Demo →
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
            { num: "1,500+", label: "Symbols tracked" },
            { num: "12", label: "DRL models" },
            { num: "3", label: "Expert agents" },
            { num: "68%", label: "Historical win rate" },
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
                desc: "Every day, FinPilot scans 1,500+ symbols across volume, trend, RSI, MACD, Bollinger Bands, and 6 more technical indicators.",
                accent: "var(--accent-cyan)",
              },
              {
                step: "02",
                title: "Analyze",
                desc: "Three specialized DRL agents — Trend, Range, and Volatility — independently evaluate each opportunity and vote on the final decision.",
                accent: "var(--accent-blue)",
              },
              {
                step: "03",
                title: "Decide",
                desc: "You get a clear signal with entry price, stop-loss, target, position size, and risk score. No noise, just the decision point.",
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
                  1,500+ symbols.<br />Every single day.
                </h3>
                <p className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed max-w-md">
                  Volume spikes, trend shifts, RSI divergences, MACD crossovers —
                  our scanner catches them all so you never miss an opportunity.
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
                <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--accent-green)] mb-3">Risk Shield</div>
                <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                  Every trade has<br />a safety net.
                </h3>
                <p className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed max-w-md">
                  ATR-based stop-loss, Kelly criterion position sizing, and risk scoring
                  on every signal. Know your risk before you enter.
                </p>
                <div className="mt-7 grid grid-cols-2 gap-3">
                  {[
                    { label: "Stop-Loss", val: "$168.50", sub: "ATR-based", icon: "🛡️" },
                    { label: "Target", val: "$198.00", sub: "R/R 1.8", icon: "🎯" },
                    { label: "Position Size", val: "12%", sub: "Kelly criterion", icon: "📊" },
                    { label: "Risk Score", val: "Low", sub: "0.3 / 1.0", icon: "✅" },
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
                <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--accent-blue)] mb-3">AI Ensemble</div>
                <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                  12 models. 3 experts.<br />One decision.
                </h3>
                <p className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed max-w-md">
                  PPO-trained deep reinforcement learning models grouped into three regime-specific agents.
                  They vote independently — no single point of failure.
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
                <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--accent-blue)] mb-3">Battle-Tested</div>
                <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                  We don&apos;t guess.<br />We backtest.
                </h3>
                <p className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed max-w-md">
                  Walk-forward optimization, 1,000 Monte Carlo simulations, and rigorous performance metrics
                  on every strategy before it goes live.
                </p>
                <div className="mt-7 space-y-3">
                  {[
                    { label: "Sharpe Ratio", val: "1.24", bar: 62 },
                    { label: "Win Rate", val: "68%", bar: 68 },
                    { label: "Max Drawdown", val: "12.4%", bar: 24 },
                    { label: "Profit Factor", val: "2.1×", bar: 70 },
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
                    <span className="text-sm">🛡️</span>
                    <span className="text-[11px] font-semibold text-[var(--accent-cyan)]">PilotShield</span>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                    Kelly criterion sizing, ATR stops, and hard position limits.
                    Risk management is automatic and cannot be overridden.
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
            FinPilot doesn&apos;t wrap an LLM.<br />
            <span className="text-[var(--text-secondary)]">
              It runs its own trained reinforcement learning models that learn from market data — not from prompts.
            </span>
          </h2>
          <div className="mt-10 flex flex-wrap justify-center gap-3">
            {["PPO Training", "HMM Regime Detection", "Ensemble Voting", "Kelly Sizing", "Monte Carlo Validation", "Telegram Alerts"].map((tag) => (
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
            Ready to stop guessing?
          </h2>
          <p className="mt-4 text-base text-[var(--text-secondary)] max-w-md mx-auto">
            Try the live demo with real scanner data — no sign-up required.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4 flex-wrap">
            <a
              href="/demo"
              className="rounded-full bg-[var(--accent-blue)] px-8 py-3.5 text-sm font-semibold text-white hover:brightness-110 transition shadow-lg shadow-[var(--accent-blue)]/20"
            >
              Try Demo →
            </a>
            <a
              href="http://localhost:8501"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-full border border-white/[0.12] px-8 py-3.5 text-sm font-medium text-[var(--text-secondary)] hover:text-white hover:border-white/[0.25] transition"
            >
              Open Dashboard
            </a>
          </div>
          <p className="mt-8 text-[11px] text-[var(--text-tertiary)]">
            1,500+ symbols · 12 DRL models · 4 strategy modes · Telegram alerts · 3 languages
          </p>
        </motion.div>

      </div>
    </section>
  );
}
