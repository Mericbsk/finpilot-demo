"use client";

import { useState } from "react";
import { TERMS } from "@/lib/terms";
import { C } from "./_ledgerColors";

interface MarginNoteProps {
  /** Term key in TERMS (e.g. "squeeze", "catalyst"). */
  termKey: string;
  /** Visible label the reader clicks/taps (defaults to the term's display name). */
  label?: string;
}

/**
 * Newspaper-margin-note evolution of the dashboard's `TermCard`/`GlossaryTooltip`.
 * Desktop: hover/click reveals an inline footnote to the side.
 * Mobile: tap opens a bottom sheet (see .ledger-marginnote-sheet in globals.css —
 * added in the mobile pass, Phase B step 10).
 */
export default function MarginNote({ termKey, label }: MarginNoteProps) {
  const [open, setOpen] = useState(false);
  const term = TERMS[termKey];
  if (!term) return <span>{label ?? termKey}</span>;

  return (
    <span className="relative inline">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="border-b border-dotted font-semibold underline-offset-4"
        style={{ borderColor: C.gold, color: C.ink }}
        aria-expanded={open}
      >
        {label ?? term.name}
      </button>
      {open && (
        <span
          role="note"
          className="ledger-marginnote-panel absolute left-0 top-full z-20 mt-2 block w-64 rounded-sm border p-3 text-left text-[13px] leading-snug shadow-lg"
          style={{ background: C.paper, borderColor: C.rule, color: C.inkSoft }}
        >
          <span className="mb-1 block font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.gold }}>
            {term.name}
          </span>
          {term.short}
        </span>
      )}
    </span>
  );
}
