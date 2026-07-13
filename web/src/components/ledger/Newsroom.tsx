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
        <p className="mb-4 text-sm" style={{ color: C.inkSoft }}>
          A sample of the daily scan feed — every symbol, scored and priced before the open.
        </p>
        <TheWire />
      </div>

      <div>
        <h3 className="mb-4 font-ledger-serif text-xl font-bold" style={{ color: C.ink }}>
          The Editorial Board
        </h3>
        <p className="mb-4 text-sm" style={{ color: C.inkSoft }}>
          Three specialised agents vote independently before a grade goes to print — no single
          point of failure.
        </p>
        <EditorialBoard />
      </div>

      <div>
        <h3 className="mb-4 font-ledger-serif text-xl font-bold" style={{ color: C.ink }}>
          Fact-Checking Desk
        </h3>
        <p className="mb-4 text-sm" style={{ color: C.inkSoft }}>
          Every call is stress-tested before it&apos;s printed — risk shield rules on one side,
          walk-forward backtest results on the other.
        </p>
        <FactCheckingDesk />
      </div>
    </div>
  );
}
