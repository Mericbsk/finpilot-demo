import TheWire from "./TheWire";
import EditorialBoard from "./EditorialBoard";
import FactCheckingDesk from "./FactCheckingDesk";
import { C } from "./_ledgerColors";

/** S3.5 "Inside the Newsroom" — reskinned proof/mockup section (see plan's
 * S3.5 addition). Illustrative data, not live snapshot data (see per-file notes). */
export default function Newsroom() {
  return (
    <div className="space-y-14">
      <div>
        <h3 className="mb-4 font-ledger-serif text-xl font-bold" style={{ color: C.ink }}>
          The Wire
        </h3>
        <p className="mb-3 border-l-2 pl-3 font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.gold, borderColor: C.gold }}>
          Illustrative process example — not today&apos;s live scan
        </p>
        <p className="mb-4 text-sm" style={{ color: C.inkSoft }}>
          A visual example of how a research feed can be read: what stood out, the Grade, and the reason.
        </p>
        <TheWire />
      </div>

      <div>
        <h3 className="mb-4 font-ledger-serif text-xl font-bold" style={{ color: C.ink }}>
          The Editorial Board
        </h3>
        <p className="mb-4 text-sm" style={{ color: C.inkSoft }}>
          The production Grade comes from published scanner rules and eligibility checks. Separate PPO
          models are research artifacts, validated before any future use.
        </p>
        <EditorialBoard />
      </div>

      <div>
        <h3 className="mb-4 font-ledger-serif text-xl font-bold" style={{ color: C.ink }}>
          Fact-Checking Desk
        </h3>
        <p className="mb-4 text-sm" style={{ color: C.inkSoft }}>
          The methodology explains how published research is checked, what the scorecard can show,
          and where evidence is still insufficient.
        </p>
        <FactCheckingDesk />
      </div>
    </div>
  );
}
