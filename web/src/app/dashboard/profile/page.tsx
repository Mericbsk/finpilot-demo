"use client";

import { useState } from "react";
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
} from "lucide-react";
import DemoBanner from "@/components/DemoBanner";

/* ── Sample user data ──────────────────────────────────────── */
const user = {
  name: "Alex Morgan",
  email: "alex@finpilot.ai",
  plan: "Pro",
  joinDate: "2024-09-15",
  language: "en",
  avatar: null as string | null,
};

const portfolio = {
  cashBalance: 24750.0,
  totalValue: 87320.5,
  dayPnl: 1240.8,
  dayPnlPct: 1.44,
  positions: [
    { ticker: "NVDA", shares: 15, avgPrice: 118.5, currentPrice: 142.5, pnl: 360.0, pnlPct: 20.25 },
    { ticker: "AAPL", shares: 25, avgPrice: 185.2, currentPrice: 198.7, pnl: 337.5, pnlPct: 7.29 },
    { ticker: "MSFT", shares: 10, avgPrice: 420.0, currentPrice: 445.2, pnl: 252.0, pnlPct: 6.0 },
    { ticker: "TSLA", shares: 8, avgPrice: 192.0, currentPrice: 178.3, pnl: -109.6, pnlPct: -7.14 },
    { ticker: "AMZN", shares: 12, avgPrice: 180.0, currentPrice: 193.5, pnl: 162.0, pnlPct: 7.5 },
  ],
};

export default function ProfilePage() {
  const [tab, setTab] = useState<"profile" | "portfolio" | "security">("profile");
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);
  const [language, setLanguage] = useState(user.language);
  const [editing, setEditing] = useState(false);

  const tabs = [
    { id: "profile" as const, label: "Profile", icon: User },
    { id: "portfolio" as const, label: "Portfolio", icon: Wallet },
    { id: "security" as const, label: "Security", icon: Shield },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <DemoBanner />
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
          <h1 className="text-lg font-semibold text-[var(--text-primary)]">{name}</h1>
          <p className="text-sm text-[var(--text-tertiary)]">{email}</p>
          <div className="mt-1 flex items-center gap-3">
            <span className="rounded-full bg-[var(--accent-cyan)]/10 px-2.5 py-0.5 text-[10px] font-bold text-[var(--accent-cyan)]">{user.plan}</span>
            <span className="text-[10px] text-[var(--text-tertiary)]">Member since {user.joinDate}</span>
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
              <button className="rounded-xl bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] px-6 py-2.5 text-xs font-semibold text-black">
                Save Changes
              </button>
            )}
          </div>
        </div>
      )}

      {/* ─── Portfolio Tab ────────────────────────────── */}
      {tab === "portfolio" && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-4 gap-3">
            <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] px-4 py-3">
              <div className="text-[11px] text-[var(--text-tertiary)]">Total Value</div>
              <div className="text-lg font-semibold text-[var(--text-primary)]">${portfolio.totalValue.toLocaleString()}</div>
            </div>
            <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] px-4 py-3">
              <div className="text-[11px] text-[var(--text-tertiary)]">Cash Balance</div>
              <div className="text-lg font-semibold text-[var(--accent-cyan)]">${portfolio.cashBalance.toLocaleString()}</div>
            </div>
            <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] px-4 py-3">
              <div className="text-[11px] text-[var(--text-tertiary)]">Day P&L</div>
              <div className="flex items-center gap-1 text-lg font-semibold text-[var(--accent-green)]">
                <TrendingUp size={16} />
                +${portfolio.dayPnl.toLocaleString()}
              </div>
            </div>
            <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] px-4 py-3">
              <div className="text-[11px] text-[var(--text-tertiary)]">Day Return</div>
              <div className="text-lg font-semibold text-[var(--accent-green)]">+{portfolio.dayPnlPct}%</div>
            </div>
          </div>

          {/* Positions */}
          <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)]">
            <div className="border-b border-[var(--border-subtle)] px-5 py-3">
              <h2 className="text-sm font-semibold text-[var(--text-primary)]">Open Positions</h2>
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
                {portfolio.positions.map((p) => (
                  <tr key={p.ticker} className="border-b border-[var(--border-subtle)] last:border-0">
                    <td className="px-5 py-3 font-semibold text-[var(--text-primary)]">{p.ticker}</td>
                    <td className="px-3 py-3 text-[var(--text-secondary)]">{p.shares}</td>
                    <td className="px-3 py-3 text-[var(--text-secondary)]">${p.avgPrice}</td>
                    <td className="px-3 py-3 text-[var(--text-primary)]">${p.currentPrice}</td>
                    <td className="px-3 py-3">
                      <span className="flex items-center gap-0.5" style={{ color: p.pnl >= 0 ? "var(--accent-green)" : "var(--accent-red)" }}>
                        {p.pnl >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                        {p.pnl >= 0 ? "+" : ""}${p.pnl.toFixed(0)}
                      </span>
                    </td>
                    <td className="px-3 py-3 font-medium" style={{ color: p.pnlPct >= 0 ? "var(--accent-green)" : "var(--accent-red)" }}>
                      {p.pnlPct >= 0 ? "+" : ""}{p.pnlPct}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
