"use client";

/**
 * Contextual ⓘ glossary card — the FinSense bridge inside FinPilot surfaces.
 * Click a badge → 60-word plain-language explanation. No navigation, no modal
 * stack; a lightweight popover that never interrupts the flow.
 */

import { useEffect, useRef, useState } from "react";
import { Info, X } from "lucide-react";
import { termForBadge, type Term } from "@/lib/terms";

export function BadgeWithTerm({ badge, label }: { badge: string; label?: string }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  const term: Term | undefined = termForBadge(badge);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  const text = label ?? badge.replace(/_/g, " ");

  return (
    <span ref={ref} className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1 rounded-full border border-white/15 bg-white/5 px-2.5 py-0.5 text-[11px] text-[var(--text-secondary,#a1a1aa)] hover:bg-white/10 transition-colors"
        aria-expanded={open}
      >
        {text}
        {term && <Info className="h-3 w-3 opacity-60" />}
      </button>
      {open && term && (
        <span className="absolute left-0 top-full z-50 mt-2 block w-72 rounded-xl border border-white/10 bg-[#111827] p-3 text-left shadow-2xl">
          <span className="mb-1 flex items-center justify-between">
            <span className="text-xs font-semibold text-white">{term.name}</span>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close">
              <X className="h-3.5 w-3.5 text-white/50 hover:text-white" />
            </button>
          </span>
          <span className="block text-[11px] leading-relaxed text-white/70">{term.short}</span>
          <span className="mt-2 block text-[10px] text-white/40">
            FinSense glossary · educational content, not advice
          </span>
        </span>
      )}
    </span>
  );
}
