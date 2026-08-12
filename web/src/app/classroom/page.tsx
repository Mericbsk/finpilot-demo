"use client";

/**
 * /classroom — VS-01 Phase 5, expanded Phase 8 (2026-08-12) to list multiple
 * open cases instead of assuming a single "today" case.
 *
 * The real product surface, distinct from the homepage's ClassroomPreview.tsx
 * (that stays exactly as-is — it's a separate, session-only Grade-guessing
 * widget, not this flow). This page's only job: show what's available and
 * hand off to /classroom/case/[id] to actually think one through. No
 * context, no form, no outcome — that all lives one screen in.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { listCases, type FinSenseCase } from "@/lib/finsenseApi";
import { C } from "@/components/ledger/_ledgerColors";

type LoadState = "loading" | "ready" | "empty" | "error";

/** "case-003-wmt-2026-05-19" -> "003" — purely a display label, not parsed for logic. */
function caseNumberLabel(caseId: string): string {
  const parts = caseId.split("-");
  return parts[1] ?? "";
}

export default function ClassroomPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [cases, setCases] = useState<FinSenseCase[]>([]);

  function load() {
    setState("loading");
    listCases()
      .then((list) => {
        setCases(list);
        setState(list.length > 0 ? "ready" : "empty");
      })
      .catch(() => setState("error"));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="ledger min-h-screen" style={{ background: C.paper }}>
      <div className="mx-auto max-w-[640px] px-6 py-24">
        <div className="text-center">
          <p
            className="font-ledger-mono text-[10px] uppercase tracking-widest"
            style={{ color: C.gold }}
          >
            The Thinking Mirror
          </p>
          <h1
            className="mt-3 font-ledger-serif text-3xl font-bold"
            style={{ color: C.ink }}
          >
            The Classroom
          </h1>
          <p className="mt-3 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
            Real FinPilot cases. Read what was happening, then commit to a
            direction before you know how it played out.
          </p>
        </div>

        {state === "loading" && (
          <p className="mt-10 text-center text-sm" style={{ color: C.inkSoft }}>
            Loading cases…
          </p>
        )}

        {state === "error" && (
          <div className="mt-10 text-center">
            <p className="text-sm" style={{ color: C.inkSoft }}>
              We couldn&apos;t load the cases.
            </p>
            <button
              type="button"
              onClick={load}
              className="mt-3 font-ledger-mono text-[10px] uppercase tracking-widest underline"
              style={{ color: C.gold }}
            >
              Try again
            </button>
          </div>
        )}

        {state === "empty" && (
          <p className="mt-10 text-center text-sm" style={{ color: C.inkSoft }}>
            No classroom cases are available right now.
          </p>
        )}

        {state === "ready" && (
          <div className="mt-10 space-y-4">
            {cases.map((c) => (
              <Link
                key={c.id}
                href={`/classroom/case/${c.id}`}
                className="block border p-6 transition hover:opacity-80"
                style={{ borderColor: C.rule }}
              >
                <div className="flex items-baseline justify-between">
                  <p
                    className="font-ledger-mono text-[10px] uppercase tracking-widest"
                    style={{ color: C.gold }}
                  >
                    Case #{caseNumberLabel(c.id)}
                  </p>
                  {c.my_prediction && (
                    <p
                      className="font-ledger-mono text-[10px] uppercase tracking-widest"
                      style={{ color: C.inkSoft }}
                    >
                      committed
                    </p>
                  )}
                </div>
                <p
                  className="mt-2 font-ledger-serif text-xl font-bold"
                  style={{ color: C.ink }}
                >
                  {c.asset}
                </p>
                <p
                  className="mt-2 font-ledger-mono text-[10px] uppercase tracking-widest"
                  style={{ color: C.gold }}
                >
                  {c.my_prediction ? "View your prediction →" : "Start Thinking →"}
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
