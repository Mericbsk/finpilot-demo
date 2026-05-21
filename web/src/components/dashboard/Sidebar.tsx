"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ScanSearch,
  BrainCircuit,
  FlaskConical,
  LineChart,
  GraduationCap,
  Star,
  Clock,
  Settings,
  User,
  ChevronLeft,
  ChevronRight,
  Brain,
  Wallet,
  Network,
  Building2,
  Users,
  ShieldCheck,
  Gauge,
} from "lucide-react";
import { useState } from "react";

const C = {
  card: "#111118",
  cardHover: "#1a1a24",
  secondary: "#111118",
  text1: "#f5f5f7",
  text2: "#a1a1a6",
  text3: "#6e6e73",
  border: "rgba(255,255,255,0.12)",
  cyan: "#00d4ff",
  blue: "#0a84ff",
  cyanBg: "rgba(0,212,255,0.12)",
};

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Overview" },
  { href: "/dashboard/scanner", icon: ScanSearch, label: "Scanner" },
  { href: "/dashboard/analysis", icon: BrainCircuit, label: "AI Analysis" },
  { href: "/dashboard/ai-lab", icon: FlaskConical, label: "AI Lab" },
  { href: "/dashboard/drl", icon: Brain, label: "DRL Agents" },
  { href: "/dashboard/portfolio", icon: Wallet, label: "Portfolio" },
  { href: "/dashboard/backtest", icon: LineChart, label: "Backtest" },
  { href: "/dashboard/finsense", icon: GraduationCap, label: "FinSense" },
  { href: "/dashboard/agent", icon: Network, label: "AI Agents" },
  { href: "/dashboard/advisory", icon: Users, label: "Advisory" },
  { href: "/dashboard/autonomy", icon: ShieldCheck, label: "Autonomy" },
  { href: "/dashboard/calibration", icon: Gauge, label: "Calibration" },
  { href: "/dashboard/watchlist", icon: Star, label: "Watchlist" },
  { href: "/dashboard/history", icon: Clock, label: "History" },
];

const bottomItems = [
  { href: "/dashboard/settings", icon: Settings, label: "Settings" },
  { href: "/dashboard/profile", icon: User, label: "Profile" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  const isActive = (href: string) =>
    href === "/dashboard" ? pathname === href : pathname.startsWith(href);

  return (
    <aside
      className={`fixed left-0 top-0 z-40 flex h-screen flex-col transition-all duration-300 ${
        collapsed ? "w-[68px]" : "w-[220px]"
      }`}
      style={{ backgroundColor: C.secondary, borderRight: `1px solid ${C.border}` }}
    >
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 px-4" style={{ borderBottom: `1px solid ${C.border}` }}>
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
          style={{ background: `linear-gradient(to bottom right, ${C.cyan}, ${C.blue})` }}
        >
          <span className="text-xs font-bold" style={{ color: "#000" }}>F</span>
        </div>
        {!collapsed && (
          <span className="text-sm font-semibold" style={{ color: C.text1 }}>
            FinPilot
          </span>
        )}
      </div>

      {/* Main nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        <div className="space-y-0.5">
          {navItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors"
                style={{
                  backgroundColor: active ? C.cyanBg : "transparent",
                  color: active ? C.cyan : C.text2,
                }}
              >
                <item.icon size={18} className="shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Bottom nav */}
      <div className="px-2 py-3" style={{ borderTop: `1px solid ${C.border}` }}>
        <div className="space-y-0.5">
          {bottomItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors"
                style={{
                  backgroundColor: active ? C.cyanBg : "transparent",
                  color: active ? C.cyan : C.text2,
                }}
              >
                <item.icon size={18} className="shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="mt-2 flex w-full items-center justify-center rounded-lg py-1.5 transition-colors"
          style={{ color: C.text3 }}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </aside>
  );
}
