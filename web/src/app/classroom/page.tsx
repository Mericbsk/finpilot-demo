"use client";

/**
 * /classroom — VS-01 Phase 5.
 *
 * The real product surface, distinct from the homepage's ClassroomPreview.tsx
 * (that stays exactly as-is — it's a separate, session-only Grade-guessing
 * widget, not this flow). This page's only job: tell the user today's case
 * exists and hand them off to /classroom/case/[id] to actually think it
 * through. No context, no form, no outcome — that all lives one screen in.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { getCaseToday, type FinSenseCase } from "@/lib/finsenseApi";
import { C } from "@/components/ledger/_ledgerColors";

type LoadState = "loading" | "ready" | "empty" | "error";

export default function ClassroomPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [caseData, setCaseData] = useState<FinSenseCase | null>(null);

  useEffect(() => {
    let cancelled = false;
    setState("loading");
    getCaseToday()
      .then((c) => {
        if (cancelled) return;
        if (c) {
          setCaseData(c);
          setState("ready");
        } else {
          setState("empty");
        }
      })
      .catch(() => {
        if (!cancelled) setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="ledger min-h-screen" style={{ background: C.paper }}>
      <div className="mx-auto max-w-[560px] px-6 py-24 text-center">
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
          Today&apos;s Classroom
        </h1>

        {state === "loading" && (
          <p className="mt-8 text-sm" style={{ color: C.inkSoft }}>
            Loading today&apos;s case…
          </p>
        )}

        {state === "error" && (
          <div className="mt-8">
            <p className="text-sm" style={{ color: C.inkSoft }}>
              We couldn&apos;t load this case.
            </p>
            <button
              type="button"
              onClick={() => {
                setState("loading");
                getCaseToday()
                  .then((c) => setState(c ? (setCaseData(c), "ready") : "empty"))
                  .catch(() => setState("error"));
              }}
              className="mt-3 font-ledger-mono text-[10px] uppercase tracking-widest underline"
              style={{ color: C.gold }}
            >
              Try again
            </button>
          </div>
        )}

        {state === "empty" && (
          <p className="mt-8 text-sm" style={{ color: C.inkSoft }}>
            No classroom case is available today.
          </p>
        )}

        {state === "ready" && caseData && (
          <div className="mt-10 border p-8" style={{ borderColor: C.rule }}>
            <p
              className="font-ledger-mono text-[10px] uppercase tracking-widest"
              style={{ color: C.gold }}
            >
              Case #001
            </p>
            <p
              className="mt-2 font-ledger-serif text-xl font-bold"
              style={{ color: C.ink }}
            >
              {caseData.asset}
            </p>
            <p className="mt-3 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
              {caseData.my_prediction
                ? "You already have a committed prediction on this case."
                : "One real case. Read what was happening, then commit to a direction before you know how it played out."}
            </p>
            <Link
              href={`/classroom/case/${caseData.id}`}
              className="mt-6 inline-block font-ledger-mono text-xs uppercase tracking-widest underline"
              style={{ color: C.gold }}
            >
              {caseData.my_prediction ? "View your prediction →" : "Start Thinking →"}
            </Link>
          </div>
        )}
      </div>
    </main>
  );
}
