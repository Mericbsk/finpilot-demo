import { TERMS } from "@/lib/terms";
import { C } from "./_ledgerColors";

const PREVIEW_TERMS = ["squeeze", "calibration", "risk-reward"];

/** S6 "Classroom Preview" — 3 static lesson cards drawn from the same
 * glossary that powers MarginNote, plus the calibration promise. */
export default function ClassroomPreview() {
  const cards = PREVIEW_TERMS.map((key) => TERMS[key]).filter(Boolean);

  return (
    <div>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        {cards.map((t) => (
          <div key={t.slug} className="border p-6" style={{ borderColor: C.rule }}>
            <h3 className="font-ledger-serif text-lg font-bold" style={{ color: C.ink }}>
              {t.name}
            </h3>
            <p className="mt-2 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
              {t.short}
            </p>
          </div>
        ))}
      </div>
      <p className="mt-8 text-center text-sm italic" style={{ color: C.inkSoft }}>
        Every grade we print is calibrated: of the candidates we mark &ldquo;~70%&rdquo;, about 70%
        should actually move. The full scorecard — and the classroom behind it — publishes as the
        history builds.
      </p>
    </div>
  );
}
