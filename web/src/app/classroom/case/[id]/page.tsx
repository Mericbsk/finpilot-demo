"use client";

/**
 * /classroom/case/[id] — VS-01 Phase 5 + Phase 6.
 *
 * Context -> Direction -> Probability -> Reason -> Review -> Commit -> Locked
 * -> (on refresh, once resolved) Outcome Reveal. One page, client-side state
 * machine — deliberately not separate routes (§5.2). No calibration, no AI,
 * no score, no Thinking Profile — this is only: read what happened, commit
 * to a direction, and later see what actually happened against exactly that
 * commitment. N=1 here; nothing is aggregated or judged.
 *
 * Route param: fetches the case directly via GET /finsense/case/{id} (Phase 8
 * content expansion — multiple cases can be open at once now, so this no
 * longer assumes "today's" case is the only one). Null/404 renders the same
 * empty state as "no case available" rather than silently loading a
 * different case.
 *
 * Outcome reveal (Phase 6): checked once when the locked state loads and once
 * after a fresh commit — deliberately no polling (§ Phase 6 spec). If the
 * case isn't resolved yet, GET /outcome 404s and the UI shows "Waiting for
 * outcome"; a later refresh checks again.
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getCase,
  predictCase,
  getOutcome,
  type FinSenseCase,
  type FinSensePrediction,
  type FinSenseOutcome,
  type Direction,
} from "@/lib/finsenseApi";
import { C } from "@/components/ledger/_ledgerColors";

type Step =
  | "loading"
  | "error"
  | "empty"
  | "context"
  | "direction"
  | "probability"
  | "reason"
  | "review"
  | "locked";

const PROBABILITY_OPTIONS = [50, 60, 70, 80, 90];
const REASON_MIN_LENGTH = 20; // matches PredictRequest.reason min_length on the server

/** "case-003-wmt-2026-05-19" -> "003" — display label only, mirrors /classroom's helper. */
function caseNumberLabel(caseId: string): string {
  const parts = caseId.split("-");
  return parts[1] ?? "";
}

function StepLabel({ children }: { children: React.ReactNode }) {
  return (
    <p
      className="font-ledger-mono text-[10px] uppercase tracking-widest"
      style={{ color: C.gold }}
    >
      {children}
    </p>
  );
}

function ContinueButton({
  onClick,
  disabled,
  children = "Continue →",
}: {
  onClick: () => void;
  disabled?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="mt-8 font-ledger-mono text-xs uppercase tracking-widest underline disabled:no-underline disabled:opacity-40"
      style={{ color: disabled ? C.inkSoft : C.gold }}
    >
      {children}
    </button>
  );
}

export default function ClassroomCasePage() {
  const params = useParams();
  const routeCaseId = Array.isArray(params.id) ? params.id[0] : params.id;

  const [step, setStep] = useState<Step>("loading");
  const [caseData, setCaseData] = useState<FinSenseCase | null>(null);

  const [direction, setDirection] = useState<Direction | null>(null);
  const [probability, setProbability] = useState<number | null>(null);
  const [reason, setReason] = useState("");

  const [committing, setCommitting] = useState(false);
  const [commitError, setCommitError] = useState<string | null>(null);
  const [committed, setCommitted] = useState<FinSensePrediction | null>(null);

  const [outcome, setOutcome] = useState<FinSenseOutcome | null>(null);
  const [outcomeChecked, setOutcomeChecked] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!routeCaseId) {
      setStep("empty");
      return;
    }
    getCase(routeCaseId)
      .then((c) => {
        if (cancelled) return;
        if (!c) {
          setStep("empty");
          return;
        }
        setCaseData(c);
        if (c.my_prediction) {
          // Refresh-safe: already committed, skip straight to locked.
          setCommitted(c.my_prediction);
          setStep("locked");
          // Outcome is checked here on a real page load/refresh of an
          // already-committed case. No polling: one check per load.
          getOutcome(c.id)
            .then((o) => {
              if (!cancelled) setOutcome(o);
            })
            .catch(() => {
              /* outcome check failing silently falls back to "waiting" — not
                 fatal, the prediction itself already loaded fine */
            })
            .finally(() => {
              if (!cancelled) setOutcomeChecked(true);
            });
        } else {
          setStep("context");
        }
      })
      .catch(() => {
        if (!cancelled) setStep("error");
      });
    return () => {
      cancelled = true;
    };
  }, [routeCaseId]);

  async function handleCommit() {
    if (!caseData || !direction || probability === null) return;
    setCommitting(true);
    setCommitError(null);
    try {
      const prediction = await predictCase(caseData.id, {
        direction,
        probability: probability / 100,
        reason: reason.trim(),
      });
      setCommitted(prediction);
      setStep("locked");
      // Check once after committing so already-resolved cases reveal the
      // result without requiring a manual refresh. A pending outcome still
      // falls back to the normal waiting state.
      getOutcome(caseData.id)
        .then((resolvedOutcome) => setOutcome(resolvedOutcome))
        .catch(() => {
          /* a failed outcome check must not hide the committed prediction */
        })
        .finally(() => setOutcomeChecked(true));
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      if (message.includes("409")) {
        setCommitError(
          "This case already has a committed prediction for this account.",
        );
      } else {
        setCommitError("We couldn't save your prediction. Try again.");
      }
    } finally {
      setCommitting(false);
    }
  }

  return (
    <main className="ledger min-h-screen" style={{ background: C.paper }}>
      <div className="mx-auto max-w-[620px] px-6 py-16">
        <Link
          href="/classroom"
          className="font-ledger-mono text-[10px] uppercase tracking-widest underline"
          style={{ color: C.inkSoft }}
        >
          ← Classroom
        </Link>

        {step === "loading" && (
          <p className="mt-10 text-sm" style={{ color: C.inkSoft }}>
            Loading today&apos;s case…
          </p>
        )}

        {step === "error" && (
          <p className="mt-10 text-sm" style={{ color: C.inkSoft }}>
            We couldn&apos;t load this case. Try again.
          </p>
        )}

        {step === "empty" && (
          <p className="mt-10 text-sm" style={{ color: C.inkSoft }}>
            No classroom case is available today.
          </p>
        )}

        {/* ── CONTEXT ── */}
        {step === "context" && caseData && (
          <div className="mt-10">
            <StepLabel>Case #{caseNumberLabel(caseData.id)} — {caseData.asset}</StepLabel>
            <h1
              className="mt-3 font-ledger-serif text-2xl font-bold"
              style={{ color: C.ink }}
            >
              What was happening?
            </h1>
            <p className="mt-4 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
              {caseData.context}
            </p>
            <p className="mt-4 text-xs italic" style={{ color: C.inkSoft }}>
              Horizon: {caseData.horizon_days} trading days. You&apos;ll find out what
              actually happened after you commit.
            </p>
            <ContinueButton onClick={() => setStep("direction")}>
              Start thinking →
            </ContinueButton>
          </div>
        )}

        {/* ── DIRECTION ── */}
        {step === "direction" && caseData && (
          <div className="mt-10">
            <StepLabel>Case #{caseNumberLabel(caseData.id)} — {caseData.asset}</StepLabel>
            <h1
              className="mt-3 font-ledger-serif text-2xl font-bold"
              style={{ color: C.ink }}
            >
              Where do you think this goes over the stated horizon?
            </h1>
            <div className="mt-6 flex flex-col gap-3">
              {(["UP", "FLAT", "DOWN"] as Direction[]).map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDirection(d)}
                  className="border px-5 py-3 text-left font-ledger-mono text-sm uppercase tracking-widest transition"
                  style={{
                    borderColor: direction === d ? C.gold : C.rule,
                    background: direction === d ? C.gold : "transparent",
                    color: direction === d ? C.paper : C.ink,
                  }}
                >
                  {d}
                </button>
              ))}
            </div>
            <ContinueButton
              onClick={() => setStep("probability")}
              disabled={!direction}
            />
          </div>
        )}

        {/* ── PROBABILITY ── */}
        {step === "probability" && caseData && (
          <div className="mt-10">
            <StepLabel>Case #{caseNumberLabel(caseData.id)} — {caseData.asset}</StepLabel>
            <h1
              className="mt-3 font-ledger-serif text-2xl font-bold"
              style={{ color: C.ink }}
            >
              How confident are you?
            </h1>
            <div className="mt-6 flex flex-wrap gap-3">
              {PROBABILITY_OPTIONS.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setProbability(p)}
                  className="flex h-14 w-14 items-center justify-center rounded-full border-2 font-ledger-mono text-xs font-bold"
                  style={{
                    borderColor: probability === p ? C.gold : C.rule,
                    background: probability === p ? C.gold : "transparent",
                    color: probability === p ? C.paper : C.ink,
                  }}
                >
                  {p}%
                </button>
              ))}
            </div>
            <ContinueButton
              onClick={() => setStep("reason")}
              disabled={probability === null}
            />
          </div>
        )}

        {/* ── REASON ── */}
        {step === "reason" && caseData && (
          <div className="mt-10">
            <StepLabel>Case #{caseNumberLabel(caseData.id)} — {caseData.asset}</StepLabel>
            <h1
              className="mt-3 font-ledger-serif text-2xl font-bold"
              style={{ color: C.ink }}
            >
              Why?
            </h1>
            <p className="mt-2 text-sm" style={{ color: C.inkSoft }}>
              What evidence led you to this prediction?
            </p>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={5}
              className="mt-4 w-full border bg-transparent p-3 text-sm leading-relaxed outline-none"
              style={{ borderColor: C.rule, color: C.ink }}
              placeholder="What did you weigh — trend, risk/reward, sentiment, something else?"
            />
            <p className="mt-2 text-xs" style={{ color: C.inkSoft }}>
              {reason.trim().length}/{REASON_MIN_LENGTH} characters minimum
            </p>
            <ContinueButton
              onClick={() => setStep("review")}
              disabled={reason.trim().length < REASON_MIN_LENGTH}
            />
          </div>
        )}

        {/* ── REVIEW ── */}
        {step === "review" && caseData && direction && probability !== null && (
          <div className="mt-10">
            <StepLabel>Case #{caseNumberLabel(caseData.id)} — {caseData.asset}</StepLabel>
            <h1
              className="mt-3 font-ledger-serif text-2xl font-bold"
              style={{ color: C.ink }}
            >
              Your prediction
            </h1>
            <div className="mt-6 space-y-4 border p-6" style={{ borderColor: C.rule }}>
              <div>
                <StepLabel>Direction</StepLabel>
                <p className="mt-1 text-lg" style={{ color: C.ink }}>{direction}</p>
              </div>
              <div>
                <StepLabel>Confidence</StepLabel>
                <p className="mt-1 text-lg" style={{ color: C.ink }}>{probability}%</p>
              </div>
              <div>
                <StepLabel>Reason</StepLabel>
                <p className="mt-1 text-sm leading-relaxed" style={{ color: C.ink }}>
                  &ldquo;{reason.trim()}&rdquo;
                </p>
              </div>
            </div>
            <p className="mt-4 text-xs italic" style={{ color: C.inkSoft }}>
              Once committed, this prediction cannot be edited.
            </p>
            {commitError && (
              <p className="mt-3 text-xs" style={{ color: C.brick }}>
                {commitError}
              </p>
            )}
            <ContinueButton onClick={handleCommit} disabled={committing}>
              {committing ? "Committing…" : "Commit Prediction"}
            </ContinueButton>
          </div>
        )}

        {/* ── LOCKED ── */}
        {step === "locked" && caseData && committed && (
          <div className="mt-10">
            <StepLabel>Case #{caseNumberLabel(caseData.id)} — {caseData.asset}</StepLabel>
            <h1
              className="mt-3 font-ledger-serif text-2xl font-bold"
              style={{ color: C.ink }}
            >
              Your prediction
            </h1>
            <div className="mt-6 space-y-4 border p-6" style={{ borderColor: C.rule }}>
              <div>
                <StepLabel>Direction</StepLabel>
                <p className="mt-1 text-lg" style={{ color: C.ink }}>
                  {committed.direction}
                </p>
              </div>
              <div>
                <StepLabel>Confidence</StepLabel>
                <p className="mt-1 text-lg" style={{ color: C.ink }}>
                  {Math.round(committed.probability * 100)}%
                </p>
              </div>
              <div>
                <StepLabel>Reason</StepLabel>
                <p className="mt-1 text-sm leading-relaxed" style={{ color: C.ink }}>
                  &ldquo;{committed.reason}&rdquo;
                </p>
              </div>
            </div>
            <p className="mt-4 text-sm" style={{ color: C.ink }}>
              🔒 Prediction committed
            </p>
            <p className="mt-1 text-xs italic" style={{ color: C.inkSoft }}>
              You can&apos;t edit this prediction.
            </p>

            {/* ── OUTCOME REVEAL (Phase 6) ── */}
            {outcome && outcome.evaluation ? (
              <div className="mt-8 border-t pt-6" style={{ borderColor: C.rule }}>
                <StepLabel>Outcome revealed</StepLabel>
                <div className="mt-4 space-y-4 border p-6" style={{ borderColor: C.rule }}>
                  <div>
                    <StepLabel>What happened</StepLabel>
                    <p className="mt-1 text-lg" style={{ color: C.ink }}>
                      Actual direction: {outcome.actual_direction}
                    </p>
                    {outcome.actual_return_pct !== null && (
                      <p className="mt-1 text-sm" style={{ color: C.inkSoft }}>
                        Return: {outcome.actual_return_pct > 0 ? "+" : ""}
                        {outcome.actual_return_pct.toFixed(2)}%
                      </p>
                    )}
                  </div>
                  <div>
                    <StepLabel>Result</StepLabel>
                    <p
                      className="mt-1 text-lg font-bold"
                      style={{
                        color: outcome.evaluation.direction_correct ? C.sage : C.brick,
                      }}
                    >
                      {outcome.evaluation.direction_correct ? "Correct" : "Incorrect"}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <p
                className="mt-6 font-ledger-mono text-[10px] uppercase tracking-widest"
                style={{ color: C.inkSoft }}
              >
                {outcomeChecked ? "Waiting for outcome" : "Checking for outcome…"}
              </p>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
