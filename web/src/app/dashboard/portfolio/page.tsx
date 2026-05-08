"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Wallet,
  RefreshCw,
  Loader2,
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart,
  AlertCircle,
  ExternalLink,
  XCircle,
  Sliders,
} from "lucide-react";
import Link from "next/link";
import { C, companyNames } from "@/lib/stockData";
import { getCurrencySymbol } from "@/lib/userSettings";

/* ── Types ──────────────────────────────────────────────────── */
interface Position {
  symbol: string;
  qty: number;
  avg_entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pl: number;
  unrealized_plpc: number;
  change_today: number;
}

interface AccountInfo {
  equity: number;
  cash: number;
  buying_power: number;
  portfolio_value: number;
  status?: string;
}

interface Order {
  id: string;
  symbol: string;
  qty: number;
  side: string;
  type: string;
  status: string;
  submitted_at: string;
  limit_price?: number;
  filled_avg_price?: number;
}

/* ── Main Page ─────────────────────────────────────────────── */
export default function PortfolioPage() {
  const [tab, setTab] = useState<"positions" | "orders">("positions");
  const [account, setAccount] = useState<AccountInfo | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [brokerAvailable, setBrokerAvailable] = useState(false);
  const [currency, setCurrency] = useState("$");
  const [optWeights, setOptWeights] = useState<Record<string, number> | null>(null);
  const [optMetrics, setOptMetrics] = useState<Record<string, number> | null>(null);
  const [optLoading, setOptLoading] = useState(false);
  const [optError, setOptError] = useState<string | null>(null);
  const [optMethod, setOptMethod] = useState<"HRP" | "MV" | "CVaR">("HRP");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("finpilot_settings");
      if (stored) setCurrency(getCurrencySymbol(JSON.parse(stored).market || "US"));
    } catch {}
  }, []);

  /* ── Fetch all data ─────────────────────────────── */
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [accRes, posRes, ordRes] = await Promise.allSettled([
        fetch("/py-api/trade/account"),
        fetch("/py-api/trade/positions"),
        fetch("/py-api/trade/orders?status=all"),
      ]);

      if (accRes.status === "fulfilled" && accRes.value.ok) {
        const acc = await accRes.value.json();
        setAccount(acc);
        setBrokerAvailable(true);
      } else if (accRes.status === "fulfilled" && accRes.value.status === 401) {
        setBrokerAvailable(false);
        setError("Sign in from Profile > Security to access live broker data.");
      } else {
        setBrokerAvailable(false);
        setError("Alpaca broker not available. Set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env");
      }

      if (posRes.status === "fulfilled" && posRes.value.ok) {
        const pos = await posRes.value.json();
        setPositions(Array.isArray(pos) ? pos : []);
      }

      if (ordRes.status === "fulfilled" && ordRes.value.ok) {
        const ord = await ordRes.value.json();
        setOrders(Array.isArray(ord) ? ord : []);
      }
    } catch {
      setError("Failed to connect to trading API");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  /* ── Cancel order ───────────────────────────────── */
  const cancelOrder = useCallback(async (orderId: string) => {
    try {
      const res = await fetch(`/py-api/trade/orders/${orderId}`, { method: "DELETE" });
      if (res.ok) fetchData();
    } catch { /* ignore */ }
  }, [fetchData]);

  /* ── Optimize portfolio ─────────────────────────── */
  const optimizePortfolio = useCallback(async () => {
    if (positions.length < 2) return;
    setOptLoading(true);
    setOptError(null);
    setOptWeights(null);
    setOptMetrics(null);
    try {
      const res = await fetch("/py-api/trade/portfolio-optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbols: positions.map((p) => p.symbol), method: optMethod, period: "1y" }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Optimization failed");
      setOptWeights(data.weights || null);
      setOptMetrics(data.metrics && Object.keys(data.metrics).length ? data.metrics : null);
      if (data.error) setOptError(data.error);
    } catch (e) {
      setOptError(String(e));
    } finally {
      setOptLoading(false);
    }
  }, [positions, optMethod]);

  /* ── Computed ───────────────────────────────────── */
  const totalUnrealized = positions.reduce((s, p) => s + (p.unrealized_pl || 0), 0);
  const totalMarketValue = positions.reduce((s, p) => s + (p.market_value || 0), 0);

  const tabs = [
    { id: "positions" as const, label: `Positions (${positions.length})`, icon: PieChart },
    { id: "orders" as const, label: `Orders (${orders.length})`, icon: DollarSign },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Wallet size={20} style={{ color: C.cyan }} />
            <h1 className="text-xl font-semibold" style={{ color: C.text1 }}>Portfolio</h1>
          </div>
          <p className="text-sm" style={{ color: C.text3 }}>
            Alpaca Paper Trading
            {brokerAvailable ? (
              <span className="ml-2" style={{ color: C.green }}>● Connected</span>
            ) : (
              <span className="ml-2" style={{ color: C.red }}>● Not Connected</span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {positions.length >= 2 && (
            <>
              <select
                value={optMethod}
                onChange={(e) => setOptMethod(e.target.value as "HRP" | "MV" | "CVaR")}
                className="rounded-xl px-2 py-2 text-xs font-medium"
                style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, color: C.text2 }}
              >
                <option value="HRP">HRP</option>
                <option value="MV">Min-Variance</option>
                <option value="CVaR">CVaR</option>
              </select>
              <button
                onClick={optimizePortfolio}
                disabled={optLoading}
                className="flex items-center gap-1.5 rounded-xl px-3 py-2.5 text-xs font-medium"
                style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, color: C.cyan }}
              >
                {optLoading ? <Loader2 size={14} className="animate-spin" /> : <Sliders size={14} />}
                Optimize
              </button>
            </>
          )}
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-xl px-3 py-2.5 text-xs font-medium"
            style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, color: C.text2 }}
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl px-4 py-3 text-xs" style={{ backgroundColor: "rgba(255,69,58,0.1)", color: C.red }}>
          <AlertCircle size={14} />
          {error}
        </div>
      )}

      {/* Account summary */}
      {account && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[
            { label: "Portfolio Value", value: `${currency}${(account.portfolio_value || account.equity || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`, color: C.text1 },
            { label: "Cash Balance", value: `${currency}${(account.cash || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`, color: C.cyan },
            { label: "Unrealized P&L", value: `${totalUnrealized >= 0 ? "+" : ""}${currency}${totalUnrealized.toLocaleString(undefined, { minimumFractionDigits: 2 })}`, color: totalUnrealized >= 0 ? C.green : C.red },
            { label: "Buying Power", value: `${currency}${(account.buying_power || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`, color: C.text2 },
          ].map((item) => (
            <div key={item.label} className="rounded-xl p-4" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
              <div className="text-[11px]" style={{ color: C.text3 }}>{item.label}</div>
              <div className="mt-1 text-lg font-semibold" style={{ color: item.color }}>{item.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Optimisation results */}
      {(optWeights || optError) && (
        <div className="rounded-xl p-4 space-y-3" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sliders size={14} style={{ color: C.cyan }} />
              <span className="text-xs font-semibold" style={{ color: C.text1 }}>
                {optMethod} Optimal Weights
              </span>
            </div>
            <button onClick={() => { setOptWeights(null); setOptError(null); }} style={{ color: C.text3 }}>
              <XCircle size={14} />
            </button>
          </div>
          {optError && (
            <p className="text-xs" style={{ color: C.red }}>{optError}</p>
          )}
          {optWeights && (
            <div className="space-y-2">
              {Object.entries(optWeights)
                .sort(([, a], [, b]) => b - a)
                .map(([sym, w]) => (
                  <div key={sym} className="flex items-center gap-2">
                    <span className="w-16 text-xs font-medium" style={{ color: C.text2 }}>{sym}</span>
                    <div className="flex-1 rounded-full h-2 overflow-hidden" style={{ backgroundColor: C.primary }}>
                      <div
                        className="h-2 rounded-full"
                        style={{ width: `${(w * 100).toFixed(1)}%`, backgroundColor: C.cyan }}
                      />
                    </div>
                    <span className="w-12 text-right text-xs" style={{ color: C.text2 }}>
                      {(w * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
            </div>
          )}
          {optMetrics && (
            <div className="flex flex-wrap gap-4 pt-2 border-t" style={{ borderColor: C.border }}>
              {Object.entries(optMetrics).map(([k, v]) => (
                <div key={k}>
                  <div className="text-[10px]" style={{ color: C.text3 }}>{k.replace(/_/g, " ")}</div>
                  <div className="text-xs font-semibold" style={{ color: C.text1 }}>{(v as number).toFixed(4)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl p-1" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2.5 text-xs font-medium transition-all"
            style={{
              backgroundColor: tab === t.id ? C.primary : "transparent",
              color: tab === t.id ? C.cyan : C.text3,
            }}
          >
            <t.icon size={14} />
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 size={24} className="animate-spin" style={{ color: C.cyan }} />
        </div>
      ) : !brokerAvailable ? (
        <div className="flex h-64 flex-col items-center justify-center gap-3 rounded-2xl" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
          <Wallet size={40} style={{ color: C.text3 }} />
          <p className="text-sm" style={{ color: C.text3 }}>Alpaca broker not connected</p>
          <p className="text-xs" style={{ color: C.text3 }}>Add ALPACA_API_KEY and ALPACA_SECRET_KEY to your .env file</p>
          <Link
            href="/dashboard/settings"
            className="mt-2 rounded-xl px-4 py-2 text-xs font-medium"
            style={{ backgroundColor: `${C.cyan}15`, color: C.cyan }}
          >
            Go to Settings
          </Link>
        </div>
      ) : (
        <>
          {/* ─── Positions Tab ───────────────────────────── */}
          {tab === "positions" && (
            positions.length === 0 ? (
              <div className="flex h-48 flex-col items-center justify-center gap-2 rounded-2xl" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
                <PieChart size={32} style={{ color: C.text3 }} />
                <p className="text-sm" style={{ color: C.text3 }}>No open positions</p>
                <Link href="/dashboard/scanner" className="text-xs" style={{ color: C.cyan }}>
                  Open Scanner to find opportunities →
                </Link>
              </div>
            ) : (
              <div className="rounded-2xl" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left text-[10px]" style={{ borderBottom: `1px solid ${C.border}`, color: C.text3 }}>
                      <th className="px-5 py-3">Symbol</th>
                      <th className="px-3 py-3">Shares</th>
                      <th className="px-3 py-3">Avg Cost</th>
                      <th className="px-3 py-3">Current</th>
                      <th className="px-3 py-3">Market Value</th>
                      <th className="px-3 py-3">P&L</th>
                      <th className="px-3 py-3">Return</th>
                      <th className="px-3 py-3">Today</th>
                      <th className="px-3 py-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((p) => (
                      <tr key={p.symbol} style={{ borderBottom: `1px solid ${C.border}` }}>
                        <td className="px-5 py-3">
                          <div className="font-semibold" style={{ color: C.text1 }}>{p.symbol}</div>
                          <div className="text-[10px]" style={{ color: C.text3 }}>{companyNames[p.symbol] || ""}</div>
                        </td>
                        <td className="px-3 py-3" style={{ color: C.text2 }}>{p.qty}</td>
                        <td className="px-3 py-3" style={{ color: C.text2 }}>{currency}{Number(p.avg_entry_price).toFixed(2)}</td>
                        <td className="px-3 py-3" style={{ color: C.text1 }}>{currency}{Number(p.current_price).toFixed(2)}</td>
                        <td className="px-3 py-3" style={{ color: C.text1 }}>
                          {currency}{Number(p.market_value).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </td>
                        <td className="px-3 py-3">
                          <span className="flex items-center gap-0.5" style={{ color: p.unrealized_pl >= 0 ? C.green : C.red }}>
                            {p.unrealized_pl >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                            {p.unrealized_pl >= 0 ? "+" : ""}${Number(p.unrealized_pl).toFixed(2)}
                          </span>
                        </td>
                        <td className="px-3 py-3 font-medium" style={{ color: (p.unrealized_plpc || 0) >= 0 ? C.green : C.red }}>
                          {(p.unrealized_plpc || 0) >= 0 ? "+" : ""}{((p.unrealized_plpc || 0) * 100).toFixed(2)}%
                        </td>
                        <td className="px-3 py-3" style={{ color: (p.change_today || 0) >= 0 ? C.green : C.red }}>
                          {(p.change_today || 0) >= 0 ? "+" : ""}{((p.change_today || 0) * 100).toFixed(2)}%
                        </td>
                        <td className="px-3 py-3">
                          <Link
                            href={`/dashboard/analysis?symbol=${p.symbol}`}
                            className="rounded-lg px-2 py-1 text-[10px]"
                            style={{ backgroundColor: `${C.cyan}15`, color: C.cyan }}
                          >
                            <ExternalLink size={10} className="inline" /> Analyze
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {/* Total row */}
                <div className="flex items-center justify-between px-5 py-3" style={{ borderTop: `1px solid ${C.border}` }}>
                  <span className="text-xs font-medium" style={{ color: C.text3 }}>
                    Total: {positions.length} positions · Market Value: ${totalMarketValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                  <span className="text-xs font-semibold" style={{ color: totalUnrealized >= 0 ? C.green : C.red }}>
                    {totalUnrealized >= 0 ? "+" : ""}${totalUnrealized.toLocaleString(undefined, { minimumFractionDigits: 2 })} P&L
                  </span>
                </div>
              </div>
            )
          )}

          {/* ─── Orders Tab ──────────────────────────────── */}
          {tab === "orders" && (
            orders.length === 0 ? (
              <div className="flex h-48 flex-col items-center justify-center gap-2 rounded-2xl" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
                <DollarSign size={32} style={{ color: C.text3 }} />
                <p className="text-sm" style={{ color: C.text3 }}>No orders yet</p>
              </div>
            ) : (
              <div className="rounded-2xl" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left text-[10px]" style={{ borderBottom: `1px solid ${C.border}`, color: C.text3 }}>
                      <th className="px-5 py-3">Symbol</th>
                      <th className="px-3 py-3">Side</th>
                      <th className="px-3 py-3">Qty</th>
                      <th className="px-3 py-3">Type</th>
                      <th className="px-3 py-3">Status</th>
                      <th className="px-3 py-3">Limit</th>
                      <th className="px-3 py-3">Filled</th>
                      <th className="px-3 py-3">Date</th>
                      <th className="px-3 py-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((o) => {
                      const statusColor = o.status === "filled" ? C.green : o.status === "canceled" ? C.text3 : o.status === "new" || o.status === "accepted" ? C.cyan : C.yellow;
                      return (
                        <tr key={o.id} style={{ borderBottom: `1px solid ${C.border}` }}>
                          <td className="px-5 py-3 font-semibold" style={{ color: C.text1 }}>{o.symbol}</td>
                          <td className="px-3 py-3">
                            <span style={{ color: o.side === "buy" ? C.green : C.red, fontWeight: 600 }}>
                              {o.side.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-3 py-3" style={{ color: C.text2 }}>{o.qty}</td>
                          <td className="px-3 py-3" style={{ color: C.text3 }}>{o.type}</td>
                          <td className="px-3 py-3">
                            <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ backgroundColor: `${statusColor}15`, color: statusColor }}>
                              {o.status}
                            </span>
                          </td>
                          <td className="px-3 py-3" style={{ color: C.text2 }}>
                            {o.limit_price ? `${currency}${o.limit_price}` : "—"}
                          </td>
                          <td className="px-3 py-3" style={{ color: C.text1 }}>
                            {o.filled_avg_price ? `${currency}${o.filled_avg_price}` : "—"}
                          </td>
                          <td className="px-3 py-3" style={{ color: C.text3 }}>
                            {o.submitted_at ? new Date(o.submitted_at).toLocaleDateString() : "—"}
                          </td>
                          <td className="px-3 py-3">
                            {(o.status === "new" || o.status === "accepted") && (
                              <button
                                onClick={() => cancelOrder(o.id)}
                                className="rounded-lg px-2 py-1 text-[10px]"
                                style={{ backgroundColor: "rgba(255,69,58,0.1)", color: C.red }}
                              >
                                <XCircle size={10} className="inline" /> Cancel
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )
          )}
        </>
      )}
    </div>
  );
}
