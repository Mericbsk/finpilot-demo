"use client";

import { useState } from "react";

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-black/80 border-b border-white/[0.08]">
      <div className="mx-auto flex h-12 max-w-[1200px] items-center justify-between px-6">
        <a href="/" className="text-[15px] font-semibold tracking-tight text-white">
          Fin<span className="text-[var(--accent-cyan)]">Pilot</span>
        </a>

        <div className="hidden items-center gap-8 md:flex">
          <a href="#features" className="text-xs text-[var(--text-tertiary)] hover:text-white transition">Features</a>
          <a href="/demo" className="text-xs text-[var(--text-tertiary)] hover:text-white transition">Demo</a>
          <a
            href="/demo"
            className="text-xs px-4 py-1.5 rounded-full bg-[var(--accent-blue)] text-white font-medium hover:brightness-110 transition"
          >
            Try Demo
          </a>
        </div>

        <button
          onClick={() => setOpen(!open)}
          className="md:hidden text-white/60 p-1"
          aria-label="Menu"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            {open
              ? <><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></>
              : <><line x1="4" y1="7" x2="20" y2="7" /><line x1="4" y1="12" x2="20" y2="12" /><line x1="4" y1="17" x2="20" y2="17" /></>
            }
          </svg>
        </button>
      </div>

      {open && (
        <div className="md:hidden px-6 py-3 border-t border-white/[0.06] bg-black/95 backdrop-blur-xl space-y-2">
          <a href="#features" onClick={() => setOpen(false)} className="block text-sm text-[var(--text-tertiary)] hover:text-white">Features</a>
          <a href="/demo" onClick={() => setOpen(false)} className="block text-sm text-[var(--text-tertiary)] hover:text-white">Demo</a>
          <a href="/demo" onClick={() => setOpen(false)} className="block text-sm text-[var(--accent-blue)] pt-1">Try Demo →</a>
        </div>
      )}
    </nav>
  );
}
