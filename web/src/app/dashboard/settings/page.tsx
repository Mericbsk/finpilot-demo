"use client";

import { useState } from "react";
import {
  Settings,
  Shield,
  SlidersHorizontal,
  Bell,
  BarChart3,
  Save,
  RotateCcw,
} from "lucide-react";

/* ── Default settings ──────────────────────────────────────── */
const defaultSettings = {
  /* Profile & Risk */
  riskAppetite: 3,
  portfolioSize: 10000,
  maxLossPercent: 2,
  trailingStop: true,

  /* Strategy & Market */
  scanStrategy: "hybrid",
  market: "US",
  timeframe: "1D",
  preMarket: false,
  afterHours: false,

  /* Notifications */
  telegramEnabled: false,
  telegramChatId: "",
  emailAlerts: false,
  pushNotifications: true,
  alertThreshold: 75,

  /* Technical Indicators */
  useEMA: true,
  useRSI: true,
  useMACD: true,
  useATR: true,
  useBollinger: false,
  useVWAP: true,
  emaPeriods: "9,21,50",
  rsiPeriod: 14,
  atrPeriod: 14,
};

export default function SettingsPage() {
  const [settings, setSettings] = useState(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem("finpilot_settings");
        if (stored) return { ...defaultSettings, ...JSON.parse(stored) };
      } catch {}
    }
    return defaultSettings;
  });
  const [saved, setSaved] = useState(false);
  const [tab, setTab] = useState<"risk" | "strategy" | "notifications" | "indicators">("risk");

  const update = <K extends keyof typeof defaultSettings>(key: K, value: (typeof defaultSettings)[K]) => {
    setSettings({ ...settings, [key]: value });
    setSaved(false);
  };

  const handleSave = () => {
    try { localStorage.setItem("finpilot_settings", JSON.stringify(settings)); } catch {}
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const tabs = [
    { id: "risk" as const, label: "Profile & Risk", icon: Shield },
    { id: "strategy" as const, label: "Strategy", icon: SlidersHorizontal },
    { id: "notifications" as const, label: "Notifications", icon: Bell },
    { id: "indicators" as const, label: "Indicators", icon: BarChart3 },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Settings size={20} className="text-[var(--text-secondary)]" />
            <h1 className="text-xl font-semibold text-[var(--text-primary)]">Settings</h1>
          </div>
          <p className="text-sm text-[var(--text-tertiary)]">Configure your scanning, risk, and notification preferences</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => { setSettings(defaultSettings); setSaved(false); }} className="flex items-center gap-1.5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] px-3 py-2 text-xs text-[var(--text-secondary)]">
            <RotateCcw size={14} />
            Reset
          </button>
          <button onClick={handleSave} className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] px-4 py-2 text-xs font-semibold text-black">
            <Save size={14} />
            {saved ? "Saved ✓" : "Save"}
          </button>
        </div>
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

      {/* Tab content */}
      <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-6">
        {/* ─── Risk ────────────────────────────────────── */}
        {tab === "risk" && (
          <div className="space-y-6">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">Risk Profile</h2>

            {/* Risk Appetite */}
            <div>
              <label className="mb-1 block text-xs text-[var(--text-secondary)]">Risk Appetite</label>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((v) => (
                  <button
                    key={v}
                    onClick={() => update("riskAppetite", v)}
                    className={`flex-1 rounded-lg py-2 text-xs font-medium transition-all ${
                      settings.riskAppetite === v
                        ? "bg-[var(--accent-cyan)]/15 text-[var(--accent-cyan)] ring-1 ring-[var(--accent-cyan)]/30"
                        : "bg-[var(--bg-primary)] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
                    }`}
                  >
                    {v === 1 ? "Conservative" : v === 2 ? "Moderate" : v === 3 ? "Balanced" : v === 4 ? "Aggressive" : "Very Aggressive"}
                  </button>
                ))}
              </div>
            </div>

            {/* Portfolio Size */}
            <div>
              <label className="mb-1 block text-xs text-[var(--text-secondary)]">Portfolio Size ($)</label>
              <input
                type="number"
                value={settings.portfolioSize}
                onChange={(e) => update("portfolioSize", +e.target.value)}
                className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-2.5 text-sm text-[var(--text-primary)] outline-none focus:border-[var(--accent-cyan)]"
              />
            </div>

            {/* Max Loss */}
            <div>
              <label className="mb-1 block text-xs text-[var(--text-secondary)]">Max Loss per Trade (%)</label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={0.5}
                  max={10}
                  step={0.5}
                  value={settings.maxLossPercent}
                  onChange={(e) => update("maxLossPercent", +e.target.value)}
                  className="flex-1 accent-[var(--accent-cyan)]"
                />
                <span className="w-12 text-right text-sm font-semibold text-[var(--accent-cyan)]">{settings.maxLossPercent}%</span>
              </div>
            </div>

            <Toggle label="Trailing Stop Loss" checked={settings.trailingStop} onChange={(v) => update("trailingStop", v)} />
          </div>
        )}

        {/* ─── Strategy ───────────────────────────────── */}
        {tab === "strategy" && (
          <div className="space-y-6">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">Strategy & Market</h2>

            {/* Scan Strategy */}
            <div>
              <label className="mb-1 block text-xs text-[var(--text-secondary)]">Scan Strategy</label>
              <div className="flex gap-2">
                {[
                  { id: "hybrid", label: "Hybrid (AI+DRL)" },
                  { id: "scanner", label: "Scanner Only" },
                  { id: "drl", label: "DRL Only" },
                ].map((s) => (
                  <button
                    key={s.id}
                    onClick={() => update("scanStrategy", s.id)}
                    className={`flex-1 rounded-lg py-2.5 text-xs font-medium transition-all ${
                      settings.scanStrategy === s.id
                        ? "bg-[var(--accent-cyan)]/15 text-[var(--accent-cyan)] ring-1 ring-[var(--accent-cyan)]/30"
                        : "bg-[var(--bg-primary)] text-[var(--text-tertiary)]"
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Market */}
            <div>
              <label className="mb-1 block text-xs text-[var(--text-secondary)]">Market</label>
              <select
                value={settings.market}
                onChange={(e) => update("market", e.target.value)}
                className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-2.5 text-sm text-[var(--text-primary)] outline-none"
              >
                <option value="US">US Market (NYSE/NASDAQ)</option>
                <option value="EU">European Markets</option>
                <option value="CRYPTO">Crypto</option>
              </select>
            </div>

            {/* Timeframe */}
            <div>
              <label className="mb-1 block text-xs text-[var(--text-secondary)]">Timeframe</label>
              <div className="flex gap-2">
                {["1H", "4H", "1D", "1W"].map((tf) => (
                  <button
                    key={tf}
                    onClick={() => update("timeframe", tf)}
                    className={`flex-1 rounded-lg py-2 text-xs font-medium transition-all ${
                      settings.timeframe === tf
                        ? "bg-[var(--accent-cyan)]/15 text-[var(--accent-cyan)] ring-1 ring-[var(--accent-cyan)]/30"
                        : "bg-[var(--bg-primary)] text-[var(--text-tertiary)]"
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>

            <Toggle label="Pre-Market Scan" checked={settings.preMarket} onChange={(v) => update("preMarket", v)} />
            <Toggle label="After-Hours Scan" checked={settings.afterHours} onChange={(v) => update("afterHours", v)} />
          </div>
        )}

        {/* ─── Notifications ─────────────────────────── */}
        {tab === "notifications" && (
          <div className="space-y-6">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">Notification Preferences</h2>

            <Toggle label="Telegram Alerts" checked={settings.telegramEnabled} onChange={(v) => update("telegramEnabled", v)} />

            {settings.telegramEnabled && (
              <div>
                <label className="mb-1 block text-xs text-[var(--text-secondary)]">Telegram Chat ID</label>
                <input
                  type="text"
                  placeholder="Enter your Telegram chat ID"
                  value={settings.telegramChatId}
                  onChange={(e) => update("telegramChatId", e.target.value)}
                  className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] outline-none focus:border-[var(--accent-cyan)]"
                />
              </div>
            )}

            <Toggle label="Email Alerts" checked={settings.emailAlerts} onChange={(v) => update("emailAlerts", v)} />
            <Toggle label="Push Notifications" checked={settings.pushNotifications} onChange={(v) => update("pushNotifications", v)} />

            <div>
              <label className="mb-1 block text-xs text-[var(--text-secondary)]">Alert Score Threshold</label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={50}
                  max={95}
                  step={5}
                  value={settings.alertThreshold}
                  onChange={(e) => update("alertThreshold", +e.target.value)}
                  className="flex-1 accent-[var(--accent-cyan)]"
                />
                <span className="w-12 text-right text-sm font-semibold text-[var(--accent-cyan)]">{settings.alertThreshold}</span>
              </div>
              <p className="mt-1 text-[10px] text-[var(--text-tertiary)]">Only alert when AI score ≥ {settings.alertThreshold}</p>
            </div>
          </div>
        )}

        {/* ─── Indicators ────────────────────────────── */}
        {tab === "indicators" && (
          <div className="space-y-6">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">Technical Indicators</h2>

            <div className="grid gap-3 sm:grid-cols-2">
              <Toggle label="EMA (Exponential Moving Average)" checked={settings.useEMA} onChange={(v) => update("useEMA", v)} />
              <Toggle label="RSI (Relative Strength Index)" checked={settings.useRSI} onChange={(v) => update("useRSI", v)} />
              <Toggle label="MACD" checked={settings.useMACD} onChange={(v) => update("useMACD", v)} />
              <Toggle label="ATR (Average True Range)" checked={settings.useATR} onChange={(v) => update("useATR", v)} />
              <Toggle label="Bollinger Bands" checked={settings.useBollinger} onChange={(v) => update("useBollinger", v)} />
              <Toggle label="VWAP" checked={settings.useVWAP} onChange={(v) => update("useVWAP", v)} />
            </div>

            {settings.useEMA && (
              <div>
                <label className="mb-1 block text-xs text-[var(--text-secondary)]">EMA Periods (comma-separated)</label>
                <input
                  type="text"
                  value={settings.emaPeriods}
                  onChange={(e) => update("emaPeriods", e.target.value)}
                  className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-2.5 text-sm text-[var(--text-primary)] outline-none focus:border-[var(--accent-cyan)]"
                />
              </div>
            )}

            {settings.useRSI && (
              <div>
                <label className="mb-1 block text-xs text-[var(--text-secondary)]">RSI Period</label>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min={7}
                    max={28}
                    value={settings.rsiPeriod}
                    onChange={(e) => update("rsiPeriod", +e.target.value)}
                    className="flex-1 accent-[var(--accent-cyan)]"
                  />
                  <span className="w-8 text-right text-sm font-semibold text-[var(--accent-cyan)]">{settings.rsiPeriod}</span>
                </div>
              </div>
            )}

            {settings.useATR && (
              <div>
                <label className="mb-1 block text-xs text-[var(--text-secondary)]">ATR Period</label>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min={7}
                    max={28}
                    value={settings.atrPeriod}
                    onChange={(e) => update("atrPeriod", +e.target.value)}
                    className="flex-1 accent-[var(--accent-cyan)]"
                  />
                  <span className="w-8 text-right text-sm font-semibold text-[var(--accent-cyan)]">{settings.atrPeriod}</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Toggle component ──────────────────────────────────────── */
function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex cursor-pointer items-center justify-between rounded-xl bg-[var(--bg-primary)] px-4 py-3">
      <span className="text-xs text-[var(--text-secondary)]">{label}</span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 rounded-full transition-colors ${checked ? "bg-[var(--accent-cyan)]" : "bg-[var(--border-subtle)]"}`}
      >
        <span className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${checked ? "translate-x-5" : ""}`} />
      </button>
    </label>
  );
}
