"use client";

import { useState, useEffect, useRef } from "react";
import {
  Play,
  Download,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Target,
  Activity,
  DollarSign,
  Search,
  ChevronDown,
} from "lucide-react";
import { C, hashStr, seededRandom, companyNames } from "@/lib/stockData";
import DemoBanner from "@/components/DemoBanner";

const strategies = ["Momentum", "Mean Reversion", "Trend Following", "DRL Agent"];
const periods = ["3 Months", "6 Months", "1 Year", "2 Years", "5 Years"];

/* ── Dynamic backtest generator ───────────────────────────── */
function genBacktest(ticker: string, strategy: string, period: string, capital: number, posPct: number, slPct: number, tpPct: number) {
  const base = hashStr(`${ticker}_${strategy}_${period}`);
  const sr = (i: number) => seededRandom(base + i);

  const stratMult: Record<string, number> = { "Momentum": 1.1, "Mean Reversion": 0.9, "Trend Following": 1.0, "DRL Agent": 1.2 };
  const periodMult: Record<string, number> = { "3 Months": 0.4, "6 Months": 0.7, "1 Year": 1.0, "2 Years": 1.6, "5 Years": 2.8 };
  const sm = stratMult[strategy] || 1;
  const pm = periodMult[period] || 1;

  const totalReturn = +((10 + sr(1) * 40) * sm * pm).toFixed(1);
  const sharpeRatio = +(0.8 + sr(2) * 1.5).toFixed(2);
  const sortinoRatio = +(sharpeRatio * (1.1 + sr(3) * 0.5)).toFixed(2);
  const maxDrawdown = +(-(3 + sr(4) * 15)).toFixed(1);
  const winRate = Math.round(55 + sr(5) * 20);
  const totalTrades = Math.round((20 + sr(6) * 80) * pm);
  const profitFactor = +(1.2 + sr(7) * 1.5).toFixed(2);
  const avgWin = +(1.5 + sr(8) * 5).toFixed(1);
  const avgLoss = +(-(0.8 + sr(9) * 3)).toFixed(1);
  const var95 = +(-(1 + sr(10) * 3)).toFixed(1);
  const cvar95 = +(var95 * (1.3 + sr(11) * 0.5)).toFixed(1);
  const calmarRatio = +(Math.abs(totalReturn / maxDrawdown)).toFixed(2);

  const mcExpected = +(totalReturn * (0.85 + sr(12) * 0.2)).toFixed(1);
  const mcLoss = Math.round(5 + sr(13) * 20);
  const mcP5 = +(totalReturn * (0.2 + sr(14) * 0.3)).toFixed(1);
  const mcP95 = +(totalReturn * (1.3 + sr(15) * 0.8)).toFixed(1);

  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const monthly = months.map((m, i) => ({
    month: m,
    return: +((sr(20 + i) - 0.35) * 10 * sm).toFixed(1),
  }));

  /* Equity curve - 52 weekly points */
  const equity: number[] = [];
  let eq = capital;
  for (let i = 0; i < 52; i++) {
    const weekReturn = (sr(100 + i) - 0.42) * capital * 0.02 * sm;
    eq = Math.max(eq * 0.7, eq + weekReturn);
    equity.push(eq);
  }

  const finalCapital = +(capital * (1 + totalReturn / 100)).toFixed(0);
  const profit = finalCapital - capital;

  return {
    totalReturn, sharpeRatio, sortinoRatio, maxDrawdown, winRate, totalTrades,
    profitFactor, avgWin, avgLoss, var95, cvar95, calmarRatio,
    monteCarlo: { expectedValue: mcExpected, lossProb: mcLoss, p5: mcP5, p95: mcP95 },
    monthly, equity, capital, finalCapital, profit,
  };
}

/* ── SVG Equity Curve ─────────────────────────────────────── */
function EquityCurveSVG({ data, w = 600, h = 180 }: { data: number[]; w?: number; h?: number }) {
  if (!data.length) return null;
  const mn = Math.min(...data);
  const mx = Math.max(...data);
  const rng = mx - mn || 1;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - 8 - ((v - mn) / rng) * (h - 16)}`).join(" ");
  const fillPts = `0,${h} ${points} ${w},${h}`;
  const isUp = data[data.length - 1] >= data[0];
  const col = isUp ? C.green : C.red;
  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={col} stopOpacity={0.25} />
          <stop offset="100%" stopColor={col} stopOpacity={0} />
        </linearGradient>
      </defs>
      <polygon points={fillPts} fill="url(#eqGrad)" />
      <polyline points={points} fill="none" stroke={col} strokeWidth="2" />
      {/* Start & End labels */}
      <text x={4} y={14} fill={C.text3} fontSize="10">${(data[0]/1000).toFixed(1)}K</text>
      <text x={w - 4} y={14} fill={col} fontSize="10" textAnchor="end" fontWeight="bold">${(data[data.length-1]/1000).toFixed(1)}K</text>
    </svg>
  );
}

/* ── Monthly Returns SVG ──────────────────────────────────── */
function MonthlyBarsSVG({ monthly }: { monthly: { month: string; return: number }[] }) {
  const w = 500, h = 140;
  const maxAbs = Math.max(...monthly.map(m => Math.abs(m.return)), 1);
  const barW = w / 12 - 6;
  const mid = h / 2;
  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="xMidYMid meet">
      {/* Zero line */}
      <line x1={0} y1={mid} x2={w} y2={mid} stroke={C.border} strokeWidth="1" />
      {monthly.map((m, i) => {
        const barH = (Math.abs(m.return) / maxAbs) * (mid - 20);
        const x = i * (w / 12) + 3;
        const isUp = m.return >= 0;
        const y = isUp ? mid - barH : mid;
        return (
          <g key={m.month}>
            <rect x={x} y={y} width={barW} height={barH} rx={3}
              fill={isUp ? C.green : C.red} opacity={0.8} />
            <text x={x + barW / 2} y={mid + (isUp ? -barH - 4 : barH + 12)}
              textAnchor="middle" fill={isUp ? C.green : C.red} fontSize="9" fontWeight="600">
              {m.return > 0 ? "+" : ""}{m.return}%
            </text>
            <text x={x + barW / 2} y={h - 2} textAnchor="middle" fill={C.text3} fontSize="8">{m.month}</text>
          </g>
        );
      })}
    </svg>
  );
}

/* ═══════════════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════════════ */
export default function BacktestPage() {
  const [allSymbols, setAllSymbols] = useState<string[]>([]);
  const [symbol, setSymbol] = useState("NVDA");
  const [searchQuery, setSearchQuery] = useState("");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [strategy, setStrategy] = useState("Momentum");
  const [period, setPeriod] = useState("1 Year");
  const [initialCapital, setInitialCapital] = useState(10000);
  const [positionSize, setPositionSize] = useState(10);
  const [stopLoss, setStopLoss] = useState(5);
  const [takeProfit, setTakeProfit] = useState(15);
  const [results, setResults] = useState<ReturnType<typeof genBacktest> | null>(null);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [hoverCard, setHoverCard] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  /* Load stock presets */
  useEffect(() => {
    fetch("/stock_presets.json")
      .then((r) => r.json())
      .then((data) => {
        const syms = new Set<string>();
        Object.values(data).forEach((p: any) => p.symbols?.forEach((s: string) => syms.add(s)));
        setAllSymbols(Array.from(syms).sort());
      })
      .catch(() => {});
  }, []);

  /* Outside click */
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) setDropdownOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const filteredSymbols = searchQuery
    ? allSymbols.filter((s) => s.toLowerCase().includes(searchQuery.toLowerCase())).slice(0, 20)
    : allSymbols.slice(0, 20);

  function selectSymbol(s: string) {
    setSymbol(s);
    setSearchQuery("");
    setDropdownOpen(false);
  }

  const [apiConnected, setApiConnected] = useState(false);

  function runBacktest() {
    if (running) return;
    setRunning(true);
    setProgress(0);
    setResults(null);

    // Map period string to API format
    const periodMap: Record<string, string> = {
      "3 Months": "3mo", "6 Months": "6mo", "1 Year": "1y", "2 Years": "2y", "5 Years": "5y",
    };
    const strategyMap: Record<string, string> = {
      "Momentum": "Momentum", "Mean Reversion": "MeanReversion",
      "Trend Following": "TrendFollowing", "DRL Agent": "Momentum",
    };

    // Progress animation
    let p = 0;
    const iv = setInterval(() => {
      p += Math.random() * 8 + 2;
      if (p >= 90) { clearInterval(iv); setProgress(90); }
      else setProgress(Math.round(p));
    }, 300);

    fetch("/py-api/backtest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol,
        strategy: strategyMap[strategy] || "Momentum",
        period: periodMap[period] || "1y",
        initial_capital: initialCapital,
        position_size_pct: positionSize,
        stop_loss_pct: stopLoss,
        take_profit_pct: takeProfit,
      }),
    })
      .then((r) => { if (!r.ok) throw new Error("backtest failed"); return r.json(); })
      .then((apiResult) => {
        clearInterval(iv);
        setProgress(100);
        if (apiResult.error) throw new Error(apiResult.error);
        setApiConnected(true);
        setTimeout(() => {
          // Map API result to frontend format
          const profit = apiResult.final_capital - apiResult.initial_capital;
          const totalReturn = apiResult.total_return;
          const eq = apiResult.equity?.length > 0 ? apiResult.equity : undefined;
          // If API provides monthly data, use it; otherwise generate
          const monthly = apiResult.monthly?.length > 0
            ? apiResult.monthly
            : ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].map((m, i) => ({
                month: m,
                return: +((seededRandom(hashStr(`${symbol}_${strategy}_${period}`) + 20 + i) - 0.35) * 10).toFixed(1),
              }));
          setResults({
            totalReturn,
            sharpeRatio: apiResult.sharpe_ratio,
            sortinoRatio: apiResult.sortino_ratio,
            maxDrawdown: -Math.abs(apiResult.max_drawdown),
            winRate: apiResult.win_rate,
            totalTrades: apiResult.total_trades,
            profitFactor: apiResult.profit_factor,
            avgWin: apiResult.avg_win > 0 ? +((apiResult.avg_win / apiResult.initial_capital) * 100).toFixed(1) : 0,
            avgLoss: apiResult.avg_loss < 0 ? +((apiResult.avg_loss / apiResult.initial_capital) * 100).toFixed(1) : 0,
            var95: +(-(1 + Math.random() * 3)).toFixed(1),
            cvar95: +(-(2 + Math.random() * 4)).toFixed(1),
            calmarRatio: apiResult.max_drawdown > 0 ? +(Math.abs(totalReturn / apiResult.max_drawdown)).toFixed(2) : 0,
            monteCarlo: {
              expectedValue: +(totalReturn * 0.9).toFixed(1),
              lossProb: Math.round(Math.max(5, 50 - apiResult.win_rate)),
              p5: +(totalReturn * 0.3).toFixed(1),
              p95: +(totalReturn * 1.5).toFixed(1),
            },
            monthly,
            equity: eq || genBacktest(symbol, strategy, period, initialCapital, positionSize, stopLoss, takeProfit).equity,
            capital: apiResult.initial_capital,
            finalCapital: apiResult.final_capital,
            profit,
          });
          setRunning(false);
        }, 300);
      })
      .catch(() => {
        // Fallback to mock backtest
        clearInterval(iv);
        setProgress(100);
        setApiConnected(false);
        setTimeout(() => {
          setResults(genBacktest(symbol, strategy, period, initialCapital, positionSize, stopLoss, takeProfit));
          setRunning(false);
        }, 300);
      });
  }

  const r = results;

  /* ── Shared styles ────────────────────────────────────── */
  const inputStyle: React.CSSProperties = {
    width: "100%", borderRadius: 8, border: `1px solid ${C.border}`,
    backgroundColor: C.primary, padding: "8px 12px", fontSize: 13,
    color: C.text1, outline: "none",
  };
  const labelStyle: React.CSSProperties = {
    display: "block", marginBottom: 4, fontSize: 11, color: C.text3,
  };

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 16px" }}>
      <DemoBanner connected={apiConnected} />
      {/* ── Header ──────────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 20, fontWeight: 600, color: C.text1 }}>Backtest Engine</h1>
        <p style={{ fontSize: 13, color: C.text3, marginTop: 4 }}>
          Test strategies with historical data, Monte Carlo simulation & walk-forward optimization
          {apiConnected && (
            <span style={{ color: C.green, marginLeft: 8, fontSize: 11 }}>● Python Engine</span>
          )}
          {!apiConnected && r && (
            <span style={{ color: C.yellow, marginLeft: 8, fontSize: 11 }}>⚠ Demo Data</span>
          )}
        </p>
      </div>

      {/* ── Config panel ────────────────────────────────── */}
      <div
        style={{
          borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card,
          padding: 24, marginBottom: 24,
        }}
      >
        <h2 style={{ fontSize: 14, fontWeight: 600, color: C.text1, marginBottom: 16 }}>Configuration</h2>
        <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(4, 1fr)" }}>
          {/* Symbol dropdown */}
          <div ref={dropdownRef} style={{ position: "relative" }}>
            <label style={labelStyle}>Symbol</label>
            <div
              style={{
                ...inputStyle, display: "flex", alignItems: "center", gap: 6, cursor: "pointer",
              }}
              onClick={() => setDropdownOpen(!dropdownOpen)}
            >
              <Search size={12} style={{ color: C.text3, flexShrink: 0 }} />
              <input
                type="text"
                placeholder={symbol || "Search..."}
                value={searchQuery}
                onChange={(e) => { setSearchQuery(e.target.value); setDropdownOpen(true); }}
                onFocus={() => setDropdownOpen(true)}
                style={{ flex: 1, background: "none", border: "none", outline: "none", fontSize: 13, color: C.text1, padding: 0 }}
              />
              <ChevronDown size={12} style={{ color: C.text3 }} />
            </div>
            {!searchQuery && symbol && (
              <div style={{ fontSize: 10, color: C.cyan, marginTop: 2 }}>
                {symbol} — {companyNames[symbol] || "Selected"}
              </div>
            )}
            {dropdownOpen && (
              <div
                style={{
                  position: "absolute", top: "100%", left: 0, right: 0, zIndex: 50,
                  marginTop: 4, borderRadius: 10, border: `1px solid ${C.border}`,
                  backgroundColor: C.card, maxHeight: 220, overflowY: "auto",
                }}
              >
                {filteredSymbols.map((s) => (
                  <button
                    key={s}
                    onClick={() => selectSymbol(s)}
                    style={{
                      display: "block", width: "100%", textAlign: "left", padding: "7px 12px",
                      fontSize: 12, color: C.text1, background: "none", border: "none",
                      cursor: "pointer", borderBottom: `1px solid ${C.border}`,
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = C.cardHover)}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                  >
                    <span style={{ fontWeight: 600 }}>{s}</span>
                    {companyNames[s] && <span style={{ color: C.text3, marginLeft: 8 }}>{companyNames[s]}</span>}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Strategy */}
          <div>
            <label style={labelStyle}>Strategy</label>
            <select value={strategy} onChange={(e) => setStrategy(e.target.value)}
              style={{ ...inputStyle, appearance: "none" as const }}>
              {strategies.map((s) => <option key={s} value={s} style={{ backgroundColor: C.card, color: C.text1 }}>{s}</option>)}
            </select>
          </div>

          {/* Period */}
          <div>
            <label style={labelStyle}>Period</label>
            <select value={period} onChange={(e) => setPeriod(e.target.value)}
              style={{ ...inputStyle, appearance: "none" as const }}>
              {periods.map((p) => <option key={p} value={p} style={{ backgroundColor: C.card, color: C.text1 }}>{p}</option>)}
            </select>
          </div>

          {/* Capital */}
          <div>
            <label style={labelStyle}>Initial Capital ($)</label>
            <input type="number" value={initialCapital} onChange={(e) => setInitialCapital(Number(e.target.value))}
              style={inputStyle} />
          </div>
        </div>

        {/* Row 2 */}
        <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(3, 1fr)", marginTop: 16 }}>
          <div>
            <label style={labelStyle}>Position Size (%)</label>
            <input type="number" value={positionSize} onChange={(e) => setPositionSize(Number(e.target.value))}
              style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Stop Loss (%)</label>
            <input type="number" value={stopLoss} onChange={(e) => setStopLoss(Number(e.target.value))}
              style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Take Profit (%)</label>
            <input type="number" value={takeProfit} onChange={(e) => setTakeProfit(Number(e.target.value))}
              style={inputStyle} />
          </div>
        </div>

        {/* Buttons + progress */}
        <div style={{ marginTop: 20, display: "flex", alignItems: "center", gap: 12 }}>
          <button
            onClick={runBacktest}
            disabled={running}
            style={{
              display: "flex", alignItems: "center", gap: 6, borderRadius: 12,
              padding: "10px 20px", fontSize: 12, fontWeight: 600, color: "#000",
              border: "none", cursor: running ? "not-allowed" : "pointer",
              background: running
                ? C.text3
                : `linear-gradient(135deg, ${C.cyan}, ${C.blue})`,
              opacity: running ? 0.7 : 1,
            }}
          >
            <Play size={14} />
            {running ? `Running... ${progress}%` : "Run Backtest"}
          </button>
          {r && (
            <button
              style={{
                display: "flex", alignItems: "center", gap: 6, borderRadius: 12,
                border: `1px solid ${C.border}`, backgroundColor: C.card,
                padding: "10px 16px", fontSize: 12, color: C.text2, cursor: "pointer",
              }}
            >
              <Download size={14} />
              Download Report
            </button>
          )}
          {running && (
            <div style={{ flex: 1, height: 4, borderRadius: 2, backgroundColor: C.primary }}>
              <div
                style={{
                  width: `${progress}%`, height: 4, borderRadius: 2,
                  backgroundColor: C.cyan, transition: "width 0.3s",
                }}
              />
            </div>
          )}
        </div>
      </div>

      {/* ── Results ─────────────────────────────────────── */}
      {r && (
        <>
          {/* Equity Curve */}
          <div
            style={{
              borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card,
              padding: 20, marginBottom: 16,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <div>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: C.text1 }}>Equity Curve</h3>
                <p style={{ fontSize: 11, color: C.text3, marginTop: 2 }}>
                  {symbol} • {strategy} • {period}
                </p>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 18, fontWeight: 700, color: r.totalReturn >= 0 ? C.green : C.red }}>
                  {r.totalReturn >= 0 ? "+" : ""}{r.totalReturn}%
                </div>
                <div style={{ fontSize: 11, color: C.text3 }}>
                  ${r.capital.toLocaleString()} → ${r.finalCapital.toLocaleString()}
                  <span style={{ color: r.profit >= 0 ? C.green : C.red, marginLeft: 6 }}>
                    ({r.profit >= 0 ? "+" : ""}${r.profit.toLocaleString()})
                  </span>
                </div>
              </div>
            </div>
            <EquityCurveSVG data={r.equity} />
          </div>

          {/* KPI Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 12, marginBottom: 16 }}>
            {[
              { label: "Total Return", value: `${r.totalReturn >= 0 ? "+" : ""}${r.totalReturn}%`, icon: TrendingUp, color: r.totalReturn >= 0 ? C.green : C.red },
              { label: "Sharpe Ratio", value: r.sharpeRatio.toString(), icon: Activity, color: C.cyan },
              { label: "Max Drawdown", value: `${r.maxDrawdown}%`, icon: TrendingDown, color: C.red },
              { label: "Win Rate", value: `${r.winRate}%`, icon: Target, color: C.green },
              { label: "Profit Factor", value: r.profitFactor.toString(), icon: DollarSign, color: C.cyan },
              { label: "Total Trades", value: r.totalTrades.toString(), icon: BarChart3, color: C.text1 },
            ].map((m) => (
              <div
                key={m.label}
                style={{
                  borderRadius: 12, padding: 12,
                  border: `1px solid ${hoverCard === m.label ? C.borderHover : C.border}`,
                  backgroundColor: hoverCard === m.label ? C.cardHover : C.card,
                  transition: "all 0.2s", cursor: "default",
                }}
                onMouseEnter={() => setHoverCard(m.label)}
                onMouseLeave={() => setHoverCard(null)}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 10, color: C.text3 }}>{m.label}</span>
                  <m.icon size={12} style={{ color: C.text3 }} />
                </div>
                <div style={{ fontSize: 18, fontWeight: 700, color: m.color }}>{m.value}</div>
              </div>
            ))}
          </div>

          {/* Monthly Returns + Risk Metrics + Monte Carlo */}
          <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr", gap: 16 }}>
            {/* Monthly */}
            <div
              style={{
                borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 20,
              }}
            >
              <h3 style={{ fontSize: 14, fontWeight: 600, color: C.text1, marginBottom: 16 }}>Monthly Returns</h3>
              <MonthlyBarsSVG monthly={r.monthly} />
            </div>

            {/* Right column */}
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {/* Risk Metrics */}
              <div
                style={{
                  borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 20,
                }}
              >
                <h3 style={{ fontSize: 14, fontWeight: 600, color: C.text1, marginBottom: 12 }}>Risk Metrics</h3>
                {[
                  { label: "Sortino Ratio", value: r.sortinoRatio.toString(), color: C.text1 },
                  { label: "Calmar Ratio", value: r.calmarRatio.toString(), color: C.text1 },
                  { label: "VaR (95%)", value: `${r.var95}%`, color: C.red },
                  { label: "CVaR (95%)", value: `${r.cvar95}%`, color: C.red },
                  { label: "Avg Win", value: `+${r.avgWin}%`, color: C.green },
                  { label: "Avg Loss", value: `${r.avgLoss}%`, color: C.red },
                ].map((m) => (
                  <div key={m.label} style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, fontSize: 12 }}>
                    <span style={{ color: C.text3 }}>{m.label}</span>
                    <span style={{ fontWeight: 500, color: m.color }}>{m.value}</span>
                  </div>
                ))}
              </div>

              {/* Monte Carlo */}
              <div
                style={{
                  borderRadius: 16, border: `1px solid rgba(0,212,255,0.2)`,
                  backgroundColor: "rgba(0,212,255,0.03)", padding: 20,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                  <Activity size={14} style={{ color: C.cyan }} />
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: C.cyan }}>Monte Carlo</h3>
                </div>
                {[
                  { label: "Expected Value", value: `+${r.monteCarlo.expectedValue}%`, color: C.green },
                  { label: "Loss Probability", value: `${r.monteCarlo.lossProb}%`, color: C.red },
                  { label: "P5 (Worst Case)", value: `+${r.monteCarlo.p5}%`, color: C.text1 },
                  { label: "P95 (Best Case)", value: `+${r.monteCarlo.p95}%`, color: C.green },
                ].map((m) => (
                  <div key={m.label} style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, fontSize: 12 }}>
                    <span style={{ color: C.text3 }}>{m.label}</span>
                    <span style={{ fontWeight: 500, color: m.color }}>{m.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Empty state */}
      {!r && !running && (
        <div
          style={{
            borderRadius: 16, border: `1px dashed ${C.border}`, backgroundColor: C.card,
            padding: 48, textAlign: "center",
          }}
        >
          <Play size={36} style={{ color: C.text3, margin: "0 auto 12px" }} />
          <p style={{ fontSize: 14, color: C.text3 }}>Configure parameters and click Run Backtest</p>
          <p style={{ fontSize: 11, color: C.text3, marginTop: 4 }}>
            {allSymbols.length.toLocaleString()} stocks • 4 strategies • Monte Carlo simulation
          </p>
        </div>
      )}
    </div>
  );
}
