"use client";

import { useState, useEffect, useCallback } from "react";
import {
  User,
  Wallet,
  Shield,
  LogOut,
  Mail,
  Globe,
  Camera,
  Lock,
  Edit3,
  TrendingUp,
  TrendingDown,
  Loader2,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { companyNames } from "@/lib/stockData";

/* ── Types ──────────────────────────────────────────────────── */
interface Position {
  symbol: string;
  qty: number;
  avg_entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pl: number;
  unrealized_plpc: number;
}

interface AccountInfo {
  equity: number;
  cash: number;
  portfolio_value: number;
}

export default function ProfilePage() {
  const [tab, setTab] = useState<"profile" | "portfolio" | "security">("profile");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [language, setLanguage] = useState("en");
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState("");

  /* Portfolio state */
  const [account, setAccount] = useState<AccountInfo | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioError, setPortfolioError] = useState<string | null>(null);

  /* Load user settings from backend */
  useEffect(() => {
    fetch("/py-api/user/settings")
      .then((r) => r.json())
      .then((data) => {
        const s = data.settings || {};
        setName(s.name || "User");
        setEmail(s.email || "");
        setLanguage(s.language || "en");
      })
      .catch(() => {
        /* Use defaults */
        setName("User");
      });
  }, []);

  /* Save profile to backend */
  const handleSave = useCallback(async () => {
    setSaving(true);
    setSaveMsg("");
    try {
      const res = await fetch("/py-api/user/settings", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "default",
          settings: { name, email, language },
        }),
      });
      if (res.ok) {
        setSaveMsg("Saved ✓");
        setEditing(false);
      } else {
        setSaveMsg("Save failed");
      }
    } catch {
      setSaveMsg("Save failed");
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMsg(""), 2000);
    }
  }, [name, email, language]);

  /* Load portfolio from Alpaca */
  const loadPortfolio = useCallback(async () => {
    setPortfolioLoading(true);
    setPortfolioError(null);
    try {
      const [accRes, posRes] = await Promise.allSettled([
        fetch("/py-api/trade/account"),
        fetch("/py-api/trade/positions"),
      ]);
      if (accRes.status === "fulfilled" && accRes.value.ok) {
        setAccount(await accRes.value.json());
      } else {
        setPortfolioError("Alpaca not connected. Configure API keys in Settings.");
      }
      if (posRes.status === "fulfilled" && posRes.value.ok) {
        const pos = await posRes.value.json();
        setPositions(Array.isArray(pos) ? pos : []);
      }
    } catch {
      setPortfolioError("Failed to load portfolio");
    } finally {
      setPortfolioLoading(false);
    }
  }, []);

  useEffect(() => {
    if (tab === "portfolio") loadPortfolio();
  }, [tab, loadPortfolio]);

  const plan = "Pro";
  const joinDate = "2024-09-15";

  const tabs = [
    { id: "profile" as const, label: "Profile", icon: User },
    { id: "portfolio" as const, label: "Portfolio", icon: Wallet },
    { id: "security" as const, label: "Security", icon: Shield },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Profile header card */}
      <div className="flex items-center gap-5 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-6">
        <div className="relative">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-blue)] text-2xl font-bold text-black">
            {name.split(" ").map((n) => n[0]).join("")}
          </div>
          <button className="absolute -bottom-1 -right-1 flex h-7 w-7 items-center justify-center rounded-full border-2 border-[var(--bg-card)] bg-[var(--bg-primary)] text-[var(--text-tertiary)] hover:text-[var(--accent-cyan)]">
            <Camera size={12} />
          </button>
        </div>
        <div className="flex-1">
          <h1 className="text-lg font-semibold text-[var(--text-primary)]">{name || "User"}</h1>
          <p className="text-sm text-[var(--text-tertiary)]">{email || "—"}</p>
          <div className="mt-1 flex items-center gap-3">
            <span className="rounded-full bg-[var(--accent-cyan)]/10 px-2.5 py-0.5 text-[10px] font-bold text-[var(--accent-cyan)]">{plan}</span>
            <span className="text-[10px] text-[var(--text-tertiary)]">Member since {joinDate}</span>
          </div>
        </div>
        <button className="flex items-center gap-1.5 rounded-xl border border-[var(--border-subtle)] px-3 py-2 text-xs text-[var(--accent-red)]">
          <LogOut size={14} />
          Sign Out
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2.5 text-xs font-medium transition-all ${
              tab === t.id ? "bg-[var(--bg-primary)] text-[var(--accent-cyan)]" : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
            }`}
          >
            <t.icon size={14} />
            {t.label}
          </button>
        ))}
      </div>

      {/* ─── Profile Tab ──────────────────────────────── */}
      {tab === "profile" && (
        <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">Personal Information</h2>
            <button onClick={() => setEditing(!editing)} className="flex items-center gap-1.5 text-xs text-[var(--accent-cyan)]">
              <Edit3 size={12} />
              {editing ? "Cancel" : "Edit"}
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-xs text-[var(--text-secondary)]">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={!editing}
                className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-2.5 text-sm text-[var(--text-primary)] outline-none disabled:opacity-50 focus:border-[var(--accent-cyan)]"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-[var(--text-secondary)]">Email</label>
              <div className="flex items-center gap-2">
                <Mail size={14} className="text-[var(--text-tertiary)]" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={!editing}
                  className="flex-1 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-2.5 text-sm text-[var(--text-primary)] outline-none disabled:opacity-50 focus:border-[var(--accent-cyan)]"
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-[var(--text-secondary)]">Language</label>
              <div className="flex items-center gap-2">
                <Globe size={14} className="text-[var(--text-tertiary)]" />
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  disabled={!editing}
                  className="flex-1 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-2.5 text-sm text-[var(--text-primary)] outline-none disabled:opacity-50"
                >
                  <option value="en">English</option>
                  <option value="tr">Türkçe</option>
                  <option value="de">Deutsch</option>
                </select>
              </div>
            </div>
            {editing && (
              <div className="flex items-center gap-3">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] px-6 py-2.5 text-xs font-semibold text-black disabled:opacity-50"
                >
                  {saving && <Loader2 size={12} className="animate-spin" />}
                  Save Changes
                </button>
                {saveMsg && <span className="text-xs text-[var(--accent-green)]">{saveMsg}</span>}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─── Portfolio Tab ────────────────────────────── */}
      {tab === "portfolio" && (
        <div className="space-y-4">
          {portfolioLoading ? (
            <div className="flex h-48 items-center justify-center">
              <Loader2 size={24} className="animate-spin text-[var(--accent-cyan)]" />
            </div>
          ) : portfolioError ? (
            <div className="flex h-48 flex-col items-center justify-center gap-3 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)]">
              <AlertCircle size={32} className="text-[var(--text-tertiary)]" />
              <p className="text-sm text-[var(--text-tertiary)]">{portfolioError}</p>
              <Link href="/dashboard/portfolio" className="text-xs text-[var(--accent-cyan)]">
                Go to Portfolio page →
              </Link>
            </div>
          ) : (
            <>
              {/* Summary */}
              {account && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] px-4 py-3">
                    <div className="text-[11px] text-[var(--text-tertiary)]">Portfolio Value</div>
                    <div className="text-lg font-semibold text-[var(--text-primary)]">
                      ${(account.portfolio_value || account.equity || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] px-4 py-3">
                    <div className="text-[11px] text-[var(--text-tertiary)]">Cash Balance</div>
                    <div className="text-lg font-semibold text-[var(--accent-cyan)]">
                      ${(account.cash || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] px-4 py-3">
                    <div className="text-[11px] text-[var(--text-tertiary)]">Unrealized P&L</div>
                    <div className="text-lg font-semibold" style={{ color: positions.reduce((s, p) => s + (p.unrealized_pl || 0), 0) >= 0 ? "var(--accent-green)" : "var(--accent-red)" }}>
                      {positions.reduce((s, p) => s + (p.unrealized_pl || 0), 0) >= 0 ? "+" : ""}
                      ${positions.reduce((s, p) => s + (p.unrealized_pl || 0), 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>
              )}

              {/* Positions */}
              {positions.length > 0 ? (
                <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)]">
                  <div className="border-b border-[var(--border-subtle)] px-5 py-3">
                    <h2 className="text-sm font-semibold text-[var(--text-primary)]">Open Positions ({positions.length})</h2>
                  </div>
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-[var(--border-subtle)] text-left text-[10px] text-[var(--text-tertiary)]">
                        <th className="px-5 py-2.5">Symbol</th>
                        <th className="px-3 py-2.5">Shares</th>
                        <th className="px-3 py-2.5">Avg Cost</th>
                        <th className="px-3 py-2.5">Current</th>
                        <th className="px-3 py-2.5">P&L</th>
                        <th className="px-3 py-2.5">Return</th>
                      </tr>
                    </thead>
                    <tbody>
                      {positions.map((p) => (
                        <tr key={p.symbol} className="border-b border-[var(--border-subtle)] last:border-0">
                          <td className="px-5 py-3">
                            <span className="font-semibold text-[var(--text-primary)]">{p.symbol}</span>
                            <span className="ml-1 text-[10px] text-[var(--text-tertiary)]">{companyNames[p.symbol] || ""}</span>
                          </td>
                          <td className="px-3 py-3 text-[var(--text-secondary)]">{p.qty}</td>
                          <td className="px-3 py-3 text-[var(--text-secondary)]">${Number(p.avg_entry_price).toFixed(2)}</td>
                          <td className="px-3 py-3 text-[var(--text-primary)]">${Number(p.current_price).toFixed(2)}</td>
                          <td className="px-3 py-3">
                            <span className="flex items-center gap-0.5" style={{ color: p.unrealized_pl >= 0 ? "var(--accent-green)" : "var(--accent-red)" }}>
                              {p.unrealized_pl >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                              {p.unrealized_pl >= 0 ? "+" : ""}${Number(p.unrealized_pl).toFixed(2)}
                            </span>
                          </td>
                          <td className="px-3 py-3 font-medium" style={{ color: (p.unrealized_plpc || 0) >= 0 ? "var(--accent-green)" : "var(--accent-red)" }}>
                            {(p.unrealized_plpc || 0) >= 0 ? "+" : ""}{((p.unrealized_plpc || 0) * 100).toFixed(2)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="flex h-32 flex-col items-center justify-center gap-2 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)]">
                  <Wallet size={24} className="text-[var(--text-tertiary)]" />
                  <p className="text-sm text-[var(--text-tertiary)]">No open positions</p>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ─── Security Tab ─────────────────────────────── */}
      {tab === "security" && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-6">
            <h2 className="mb-4 text-sm font-semibold text-[var(--text-primary)]">Change Password</h2>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs text-[var(--text-secondary)]">Current Password</label>
                <div className="flex items-center gap-2">
                  <Lock size={14} className="text-[var(--text-tertiary)]" />
                  <input type="password" placeholder="••••••••" className="flex-1 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] outline-none focus:border-[var(--accent-cyan)]" />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs text-[var(--text-secondary)]">New Password</label>
                <input type="password" placeholder="••••••••" className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] outline-none focus:border-[var(--accent-cyan)]" />
              </div>
              <div>
                <label className="mb-1 block text-xs text-[var(--text-secondary)]">Confirm Password</label>
                <input type="password" placeholder="••••••••" className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] outline-none focus:border-[var(--accent-cyan)]" />
              </div>
              <button className="rounded-xl bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] px-6 py-2.5 text-xs font-semibold text-black">
                Update Password
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-6">
            <h2 className="mb-2 text-sm font-semibold text-[var(--text-primary)]">Two-Factor Authentication</h2>
            <p className="mb-3 text-xs text-[var(--text-tertiary)]">Add an extra layer of security to your account</p>
            <button className="rounded-xl border border-[var(--accent-cyan)]/30 bg-[var(--accent-cyan)]/10 px-4 py-2.5 text-xs font-semibold text-[var(--accent-cyan)]">
              Enable 2FA
            </button>
          </div>

          <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6">
            <h2 className="mb-2 text-sm font-semibold text-[var(--accent-red)]">Danger Zone</h2>
            <p className="mb-3 text-xs text-[var(--text-tertiary)]">Permanently delete your account and all data</p>
            <button className="rounded-xl border border-[var(--accent-red)]/30 bg-[var(--accent-red)]/10 px-4 py-2.5 text-xs font-semibold text-[var(--accent-red)]">
              Delete Account
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
