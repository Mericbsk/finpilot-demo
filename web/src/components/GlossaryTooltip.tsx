"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { C } from "@/lib/stockData";

interface DictEntry {
  slug: string;
  term: string;
  definition: string;
  level: string;
  category: string;
}

let _cache: DictEntry[] | null = null;

async function fetchDictionary(): Promise<DictEntry[]> {
  if (_cache) return _cache;
  const r = await fetch("/dictionary.json");
  _cache = await r.json();
  return _cache as DictEntry[];
}

interface GlossaryTooltipProps {
  slug: string;
  children: React.ReactNode;
}

export function GlossaryTooltip({ slug, children }: GlossaryTooltipProps) {
  const [entry, setEntry] = useState<DictEntry | null>(null);
  const [visible, setVisible] = useState(false);
  const [position, setPosition] = useState<"above" | "below">("above");
  const triggerRef = useRef<HTMLSpanElement>(null);
  const loadedRef = useRef(false);

  async function load() {
    if (loadedRef.current) return;
    loadedRef.current = true;
    const terms = await fetchDictionary();
    const found = terms.find((t) => t.slug === slug);
    if (found) setEntry(found);
  }

  function handleMouseEnter() {
    load();
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setPosition(rect.top > 160 ? "above" : "below");
    }
    setVisible(true);
  }

  return (
    <span
      ref={triggerRef}
      style={{ position: "relative", display: "inline" }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={() => setVisible(false)}
    >
      <span
        style={{
          color: "rgba(167,139,250,0.9)",
          borderBottom: "1px dashed rgba(167,139,250,0.4)",
          cursor: "help",
        }}
      >
        {children}
      </span>

      {visible && entry && (
        <span
          style={{
            position: "absolute",
            [position === "above" ? "bottom" : "top"]: "calc(100% + 6px)",
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 9999,
            width: 240,
            borderRadius: 12,
            border: `1px solid rgba(167,139,250,0.25)`,
            backgroundColor: "#16161e",
            boxShadow: "0 8px 32px rgba(0,0,0,0.6)",
            padding: 12,
            display: "block",
            pointerEvents: "auto",
          }}
        >
          {/* Arrow */}
          <span
            style={{
              position: "absolute",
              [position === "above" ? "bottom" : "top"]: -5,
              left: "50%",
              transform: "translateX(-50%)",
              width: 8,
              height: 8,
              backgroundColor: "#16161e",
              border: `1px solid rgba(167,139,250,0.25)`,
              borderTop: position === "above" ? "none" : undefined,
              borderBottom: position === "below" ? "none" : undefined,
              borderLeft: "none",
              borderRight: "none",
              rotate: position === "above" ? "45deg" : "-135deg",
            }}
          />
          <span style={{ fontSize: 12, fontWeight: 700, color: C.text1, display: "block", marginBottom: 4 }}>
            {entry.term.split("(")[0].trim()}
          </span>
          <span style={{ fontSize: 11, color: C.text3, display: "block", lineHeight: 1.5, marginBottom: 8 }}>
            {entry.definition.slice(0, 90)}{entry.definition.length > 90 ? "…" : ""}
          </span>
          <Link
            href={`/dashboard/finsense/${entry.slug}`}
            style={{ fontSize: 10, color: "rgba(167,139,250,0.9)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: 3 }}
          >
            FinSense&apos;te aç <ExternalLink size={9} />
          </Link>
        </span>
      )}
    </span>
  );
}
