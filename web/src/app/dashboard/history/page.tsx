"use client";

import { useState, useEffect } from "react";
import {
  Clock,
  Calendar,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  TrendingDown,
  Target,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import DemoBanner from "@/components/DemoBanner";

/* ── Generate 14 days of history (fallback mock) ──────────── */
const signalsList = ["BUY", "SELL", "HOLD", "CAUTION"] as const;
const tickers = ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "AMD", "AVGO", "CRM", "PLTR", "COIN"];

function makeDay(daysAgo: number) {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  const stocks = tickers
    .sort(() => Math.random() - 0.5)
    .slice(0, 4 + Math.floor(Math.random() * 4))
    .map((t) => {
      const score = 30 + Math.floor(Math.random() * 65);
      const signal = score >= 75 ? "BUY" : score >= 55 ? "HOLD" : score >= 40 ? "CAUTION" : "SELL";
      const price = 80 + Math.random() * 400;
      const change = -6 + Math.random() * 12;
      const tp1Hit = Math.random() > 0.4;
      const slHit = !tp1Hit && Math.random() > 0.6;
      return {
        ticker: t,
        score,
        signal,
        price: +price.toFixed(2),
        change: +change.toFixed(2),
        tp1Hit,
        slHit,
        confidence: 60 + Math.floor(Math.random() * 35),
      };
    });
  return {
    date: d.toISOString().split("T")[0],
    label: d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" }),
    scanned: 8 + Math.floor(Math.random() * 6),
    buyCount: stocks.filter((s) => s.signal === "BUY").length,
    successRate: 55 + Math.floor(Math.random() * 35),
    stocks,
  };
}

interface DayData {
  date: string;
  label: string;
  scanned: number;
  buyCount: number;
  successRate: number;
  stocks: { ticker: string; score: number; signal: string; price: number; change: number; tp1Hit: boolean; slHit: boolean; confidence: number }[];
}

function convertAPISignals(signals: Record<string, unknown>[]): DayData[] {
  // Group signals by date
  const byDate = new Map<string, typeof signals>();
  for (const s of signals) {
    const ts = String((s as Record<string, unknown>).timestamp || "").split("T")[0];
    if (!ts) continue;
    if (!byDate.has(ts)) byDate.set(ts, []);
    byDate.get(ts)!.push(s);
  }
  const days: DayData[] = [];
  for (const [date, sigs] of byDate) {
    const d = new Date(date);
    const stocks = sigs.map((s: Record<string, unknown>) => {
      const score = Number(s.score || s.ai_score || 50);
      const signal = String(s.signal || (score >= 75 ? "BUY" : score >= 55 ? "HOLD" : "CAUTION"));
      return {
        ticker: String(s.symbol || ""),
        score,
        signal,
        price: Number(s.price || 0),
        change: 0,
        tp1Hit: s.status === "tp_hit",
        slHit: s.status === "sl_hit",
        confidence: Number(s.confidence || 0) * 100 || 70,
      };
    });
    days.push({
      date,
      label: d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" }),
      scanned: stocks.length,
      buyCount: stocks.filter((s) => s.signal === "BUY").length,
      successRate: stocks.length > 0 ? Math.round(stocks.filter((s) => s.tp1Hit).length / stocks.length * 100) : 0,
      stocks,
    });
  }
  return days.sort((a, b) => b.date.localeCompare(a.date)).slice(0, 14);
}

const history = Array.from({ length: 14 }, (_, i) => makeDay(i));

function SignalBadge({ signal }: { signal: string }) {
  const m: Record<string, { color: string; bg: string }> = {
    BUY: { color: "var(--accent-green)", bg: "rgba(48,209,88,0.1)" },
    SELL: { color: "var(--accent-red)", bg: "rgba(255,69,58,0.1)" },
    HOLD: { color: "var(--accent-cyan)", bg: "rgba(0,212,255,0.1)" },
    CAUTION: { color: "#ffd60a", bg: "rgba(255,214,10,0.1)" },
  };
  const c = m[signal] || m.HOLD;
  return <span className="rounded-full px-2 py-0.5 text-[10px] font-bold" style={{ color: c.color, backgroundColor: c.bg }}>{signal}</span>;
}

export default function HistoryPage() {
  const [history, setHistory] = useState<DayData[]>(() => Array.from({ length: 14 }, (_, i) => makeDay(i)));
  const [expanded, setExpanded] = useState<string | null>(null);
  const [apiSource, setApiSource] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/py-api/history/signals?days=14")
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((result) => {
        if (result.signals?.length > 0) {
          const converted = convertAPISignals(result.signals);
          if (converted.length > 0) {
            setHistory(converted);
            setApiSource(result.source);
          }
        }
        setLoading(false);
        setExpanded((prev) => prev ?? history[0]?.date ?? null);
      })
      .catch(() => { setLoading(false); });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!expanded && history.length > 0) setExpanded(history[0].date);
  }, [history, expanded]);

  const totalScanned = history.reduce((a, d) => a + d.scanned, 0);
  const totalBuys = history.reduce((a, d) => a + d.buyCount, 0);
  const avgSuccess = (history.reduce((a, d) => a + d.successRate, 0) / history.length).toFixed(0);

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <DemoBanner connected={!!apiSource} />
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <Clock size={20} className="text-[var(--accent-cyan)]" />
          <h1 className="text-xl font-semibold text-[var(--text-primary)]">Signal History</h1>
        </div>
        <p className="text-sm text-[var(--text-tertiary)]">
          Daily signal timeline — last 14 days
          {apiSource && (
            <span style={{ color: "var(--accent-green)", marginLeft: 8, fontSize: 11 }}>● {apiSource === "database" ? "DB" : "Cache"}</span>
          )}
          {!apiSource && !loading && (
            <span style={{ color: "#ffd60a", marginLeft: 8, fontSize: 11 }}>⚠ Demo Data</span>
          )}
        </p>
      </div>

      {/* Aggregate stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Days Tracked", value: history.length, color: "var(--text-primary)" },
          { label: "Total Scanned", value: totalScanned, color: "var(--accent-cyan)" },
          { label: "Total BUY Signals", value: totalBuys, color: "var(--accent-green)" },
          { label: "Avg Success Rate", value: `${avgSuccess}%`, color: "var(--accent-green)" },
        ].map((s, i) => (
          <div key={i} className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] px-4 py-3">
            <div className="text-[11px] text-[var(--text-tertiary)]">{s.label}</div>
            <div className="text-lg font-semibold" style={{ color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Timeline */}
      <div className="space-y-2">
        {history.map((day) => {
          const isOpen = expanded === day.date;
          return (
            <div key={day.date} className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] transition-all">
              {/* Day header */}
              <button
                onClick={() => setExpanded(isOpen ? null : day.date)}
                className="flex w-full items-center justify-between px-5 py-4"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--accent-cyan)]/10">
                    <Calendar size={16} className="text-[var(--accent-cyan)]" />
                  </div>
                  <div className="text-left">
                    <div className="text-sm font-semibold text-[var(--text-primary)]">{day.label}</div>
                    <div className="text-[11px] text-[var(--text-tertiary)]">{day.date}</div>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <div className="text-[10px] text-[var(--text-tertiary)]">Scanned</div>
                    <div className="text-xs font-medium text-[var(--text-primary)]">{day.scanned}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] text-[var(--text-tertiary)]">BUY</div>
                    <div className="text-xs font-medium text-[var(--accent-green)]">{day.buyCount}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] text-[var(--text-tertiary)]">Success</div>
                    <div className="text-xs font-medium" style={{ color: day.successRate >= 70 ? "var(--accent-green)" : day.successRate >= 50 ? "var(--accent-cyan)" : "var(--accent-red)" }}>
                      {day.successRate}%
                    </div>
                  </div>
                  {isOpen ? <ChevronUp size={16} className="text-[var(--text-tertiary)]" /> : <ChevronDown size={16} className="text-[var(--text-tertiary)]" />}
                </div>
              </button>

              {/* Expanded stock signals */}
              {isOpen && (
                <div className="border-t border-[var(--border-subtle)] px-5 py-4">
                  <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {day.stocks.map((s) => (
                      <div key={s.ticker} className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] p-3">
                        <div className="mb-1.5 flex items-center justify-between">
                          <span className="text-xs font-semibold text-[var(--text-primary)]">{s.ticker}</span>
                          <SignalBadge signal={s.signal} />
                        </div>
                        <div className="mb-1.5 flex items-baseline gap-2">
                          <span className="text-sm font-bold text-[var(--text-primary)]">${s.price}</span>
                          <span className="flex items-center gap-0.5 text-[10px] font-medium" style={{ color: s.change >= 0 ? "var(--accent-green)" : "var(--accent-red)" }}>
                            {s.change >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                            {s.change >= 0 ? "+" : ""}{s.change}%
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="h-1 flex-1 rounded-full bg-[var(--bg-card)]">
                            <div className="h-1 rounded-full" style={{
                              width: `${s.score}%`,
                              backgroundColor: s.score >= 75 ? "var(--accent-green)" : s.score >= 50 ? "var(--accent-cyan)" : "var(--accent-red)"
                            }} />
                          </div>
                          <span className="text-[10px] text-[var(--text-secondary)]">{s.score}</span>
                        </div>
                        <div className="mt-2 flex gap-2 text-[10px]">
                          {s.tp1Hit && (
                            <span className="flex items-center gap-0.5 text-[var(--accent-green)]"><Target size={10} /> TP1 Hit</span>
                          )}
                          {s.slHit && (
                            <span className="flex items-center gap-0.5 text-[var(--accent-red)]"><AlertTriangle size={10} /> SL Hit</span>
                          )}
                          <span className="text-[var(--text-tertiary)]">Conf: {s.confidence}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
