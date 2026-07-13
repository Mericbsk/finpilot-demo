import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Masthead from "@/components/ledger/Masthead";
import EditionArticle from "@/components/ledger/EditionArticle";
import DailyDouble from "@/components/ledger/DailyDouble";
import Newsroom from "@/components/ledger/Newsroom";
import LedgerStrip from "@/components/ledger/LedgerStrip";
import HowItsMade from "@/components/ledger/HowItsMade";
import ClassroomPreview from "@/components/ledger/ClassroomPreview";
import EditorialStance from "@/components/ledger/EditorialStance";
import FullEditionTeaser from "@/components/ledger/FullEditionTeaser";
import Colophon from "@/components/ledger/Colophon";
import SectionHeading from "@/components/ledger/SectionHeading";
import { C } from "@/components/ledger/_ledgerColors";
import { getLedgerSnapshot } from "@/lib/ledgerSnapshot";
import { LanguageProvider } from "@/lib/i18n/LanguageContext";

export default function Home() {
  const snap = getLedgerSnapshot();
  const dateLabel = snap
    ? new Date(snap.date).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" })
    : "No edition yet";

  return (
    <LanguageProvider>
      <Navbar />
      <main className="ledger pt-12">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <Masthead
            dateLabel={dateLabel}
            editionNo={snap?.edition_no}
            universe={snap?.universe ?? 0}
            byGrade={snap?.karne?.by_grade}
          />

          <section className="py-14">
            <SectionHeading textKey="section.yesterdaysEdition" />
            <EditionArticle
              dateLabel={dateLabel}
              contextLine={snap?.context_line}
              candidates={snap?.candidates ?? []}
            />
          </section>

          {(snap?.concept || snap?.candidates?.[0]) && (
            <section className="border-t py-14" style={{ borderColor: C.rule }}>
              <SectionHeading textKey="section.dailyDouble" />
              <DailyDouble concept={snap?.concept} candidate={snap?.candidates?.[0]} />
            </section>
          )}

          <section className="border-t py-14" style={{ borderColor: C.rule }}>
            <SectionHeading textKey="section.insideNewsroom" />
            <Newsroom />
          </section>

          <section className="border-t py-14" style={{ borderColor: C.rule }}>
            <SectionHeading textKey="section.ledgerStrip" />
            <LedgerStrip karne={snap?.karne ?? null} />
          </section>

          <section className="border-t py-14" style={{ borderColor: C.rule }}>
            <SectionHeading textKey="section.howItsMade" />
            <HowItsMade configSha={snap?.config_sha} />
          </section>

          <section className="border-t py-14" style={{ borderColor: C.rule }}>
            <SectionHeading textKey="section.classroom" />
            <ClassroomPreview />
          </section>
        </div>

        <div className="my-4">
          <EditorialStance />
        </div>

        <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
          <FullEditionTeaser />
        </div>

        <Colophon />
      </main>
      <Footer />
    </LanguageProvider>
  );
}
