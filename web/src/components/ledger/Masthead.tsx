"use client";

import { useEffect, useState } from "react";
import { C } from "./_ledgerColors";
import { useLanguage } from "@/lib/i18n/LanguageContext";

interface MastheadProps {
  dateLabel: string;
  editionNo?: number;
  universe: number;
  /** Grade -> {n, hit_rate} from snapshot.karne.by_grade, when compiled. */
  byGrade?: Record<string, { n?: number; hit_rate?: number | string }>;
}

function useMarketCountdown() {
  const [label, setLabel] = useState<string | null>(null);
  useEffect(() => {
    const tick = () => {
      // US markets: 9:30am–4:00pm America/New_York. Rough client-side estimate;
      // good enough for an editorial flourish, not a trading signal.
      const now = new Date();
      const ny = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
      const open = new Date(ny);
      open.setHours(9, 30, 0, 0);
      const close = new Date(ny);
      close.setHours(16, 0, 0, 0);
      if (ny < open) {
        const diffH = (open.getTime() - ny.getTime()) / 3_600_000;
        setLabel(`Markets open in ${diffH.toFixed(1)}h`);
      } else if (ny <= close) {
        setLabel("Markets are open");
      } else {
        setLabel("Markets are closed");
      }
    };
    tick();
    const id = setInterval(tick, 60_000);
    return () => clearInterval(id);
  }, []);
  return label;
}

/** S1 masthead: serif banner, dateline, live market-hours line, circulation stats. */
export default function Masthead({ dateLabel, editionNo, universe, byGrade }: MastheadProps) {
  const marketLabel = useMarketCountdown();
  const { t } = useLanguage();

  // Live weighted hit-rate across graded candidates, when the scorecard has
  // actually compiled (see Masthead's win-rate stat below). Falls back to a
  // clearly-labelled backtest figure — never presented as a live claim
  // unless it's backed by real karne.by_grade data.
  let liveWinRate: number | null = null;
  if (byGrade && Object.keys(byGrade).length > 0) {
    let weightedSum = 0;
    let totalN = 0;
    for (const stats of Object.values(byGrade)) {
      const n = Number(stats.n) || 0;
      const hr = typeof stats.hit_rate === "number" ? stats.hit_rate : Number(stats.hit_rate);
      if (n > 0 && Number.isFinite(hr)) {
        weightedSum += hr * n;
        totalN += n;
      }
    }
    if (totalN > 0) liveWinRate = weightedSum / totalN;
  }

  const winRateStat = liveWinRate != null
    ? { num: `${Math.round(liveWinRate * 100)}%`, label: t("masthead.statWinRateLive") }
    : { num: "68%", label: t("masthead.statWinRateBacktest") };

  const stats = [
    { num: universe > 0 ? `${universe.toLocaleString("en-US")}+` : "—", label: t("masthead.statScanned") },
    { num: "12", label: t("masthead.statModels") },
    { num: "3", label: t("masthead.statAgents") },
    winRateStat,
  ];

  return (
    <header className="border-b-4 pb-6 pt-10 text-center" style={{ borderColor: C.ink }}>
      <p className="font-ledger-mono text-[11px] uppercase tracking-[0.3em]" style={{ color: C.inkSoft }}>
        {dateLabel}
        {editionNo ? ` · Edition No. ${editionNo}` : ""}
        {marketLabel ? ` · ${marketLabel}` : ""}
      </p>
      <h1 className="mt-3 font-ledger-serif text-6xl font-black tracking-tight sm:text-7xl" style={{ color: C.ink }}>
        {t("masthead.title")}
      </h1>
      <p className="mx-auto mt-4 max-w-xl text-base italic" style={{ color: C.inkSoft }}>
        {t("masthead.tagline")}
      </p>

      <div className="mt-8 flex items-center justify-center gap-4">
        <a
          href="/demo"
          className="rounded-none border-2 px-7 py-2.5 text-sm font-semibold uppercase tracking-widest transition hover:opacity-80"
          style={{ borderColor: C.ink, background: C.ink, color: C.paper }}
        >
          {t("masthead.ctaRead")}
        </a>
        <a
          href="#how-its-made"
          className="rounded-none border-2 px-7 py-2.5 text-sm font-medium uppercase tracking-widest transition hover:opacity-70"
          style={{ borderColor: C.ink, color: C.ink }}
        >
          {t("masthead.ctaHowItsMade")}
        </a>
      </div>

      {/* Circulation numbers. `universe` and (when compiled) the win-rate are
          real snapshot data; DRL-model/agent counts are fixed architecture
          facts, not claims. If the scorecard hasn't compiled yet, the
          win-rate is explicitly labelled "Backtested" (research result) —
          never presented as if it were a live production metric. */}
      <div className="mt-10 flex flex-wrap justify-center gap-x-10 gap-y-4 border-t pt-8" style={{ borderColor: C.rule }}>
        {stats.map((s) => (
          <div key={s.label} className="text-center">
            <div className="font-ledger-mono text-2xl font-bold" style={{ color: C.ink }}>
              {s.num}
            </div>
            <div className="mt-1 text-[10px] uppercase tracking-widest" style={{ color: C.inkSoft }}>
              {s.label}
            </div>
          </div>
        ))}
      </div>
      {liveWinRate == null && (
        <p className="mt-3 text-[10px] italic" style={{ color: C.inkSoft }}>
          {t("masthead.winRateFootnote")}
        </p>
      )}
    </header>
  );
}
