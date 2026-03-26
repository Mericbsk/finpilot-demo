"use client";

import { Search, Bell, Globe } from "lucide-react";
import { useState } from "react";

const C = {
  card: "#111118",
  primary: "#0a0a10",
  text1: "#f5f5f7",
  text3: "#6e6e73",
  border: "rgba(255,255,255,0.12)",
  cyan: "#00d4ff",
  blue: "#0a84ff",
};

export default function TopBar() {
  const [search, setSearch] = useState("");

  return (
    <header
      className="sticky top-0 z-30 flex h-14 items-center justify-between px-6 backdrop-blur-xl"
      style={{ backgroundColor: `${C.primary}cc`, borderBottom: `1px solid ${C.border}` }}
    >
      {/* Search */}
      <div className="relative w-full max-w-md">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: C.text3 }} />
        <input
          type="text"
          placeholder="Search stocks, features..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg py-1.5 pl-9 pr-3 text-xs outline-none"
          style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, color: C.text1 }}
        />
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        <button className="relative rounded-lg p-2 transition-colors" style={{ color: C.text3 }}>
          <Bell size={16} />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full" style={{ backgroundColor: C.cyan }} />
        </button>
        <button className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs transition-colors" style={{ color: C.text3 }}>
          <Globe size={14} />
          EN
        </button>
        <div
          className="flex h-7 w-7 items-center justify-center rounded-full text-[10px] font-bold"
          style={{ background: `linear-gradient(to bottom right, ${C.cyan}, ${C.blue})`, color: "#000" }}
        >
          U
        </div>
      </div>
    </header>
  );
}
