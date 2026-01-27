import { useMemo, useState } from "react";
import { ArrowUpRight, BellRing, Info, X } from "lucide-react";
import { useCtaStore } from "../store/ctaStore";

const QR_PATTERN: number[][] = [
  [1, 1, 1, 1, 1, 0, 1],
  [1, 0, 0, 0, 1, 1, 0],
  [1, 0, 1, 0, 1, 0, 1],
  [1, 0, 0, 0, 1, 1, 0],
  [1, 1, 1, 1, 1, 0, 1],
  [0, 1, 0, 1, 0, 1, 0],
  [1, 0, 1, 0, 1, 0, 1]
];

export function TelegramCtaPanel() {
  const { contract, secondaryStatus, setSecondaryStatus } = useCtaStore((state) => ({
    contract: state.contract,
    secondaryStatus: state.secondaryStatus,
    setSecondaryStatus: state.setSecondaryStatus
  }));

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showWhy, setShowWhy] = useState(false);

  const statusLabel = useMemo(() => (secondaryStatus === "aktif" ? "Aktif" : "Kapalı"), [secondaryStatus]);

  const handleOpen = () => {
    setIsModalOpen(true);
    if (secondaryStatus !== "aktif") {
      setSecondaryStatus("aktif");
    }
  };

  const handleClose = () => {
    setIsModalOpen(false);
  };

  return (
    <section className="relative overflow-hidden rounded-3xl border border-slate-800 bg-slate-950/85 p-6 shadow-inner shadow-pilot-primary/15">
      <div className="absolute -inset-2 bg-gradient-to-br from-pilot-primary/20 via-transparent to-transparent blur-2xl" aria-hidden="true" />
      <div className="relative flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-pilot-primary/30 bg-pilot-primary/10 px-3 py-1 text-xs font-semibold text-pilot-primary-foreground">
            <BellRing className="h-3.5 w-3.5" />
            {contract.ikincil.etiket}
            <span className={`ml-2 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide ${
              secondaryStatus === "aktif"
                ? "bg-emerald-500/15 text-emerald-200"
                : "bg-slate-800/80 text-slate-300"
            }`}
            >
              {statusLabel}
            </span>
          </div>
          <p className="text-lg font-semibold text-slate-100">Telegram entegrasyonunu aç, sinyaller anında cebine düşsün.</p>
          <p className="text-sm text-slate-400">{contract.ikincil.aciklama}</p>
          <button
            type="button"
            onClick={() => setShowWhy((value) => !value)}
            className="inline-flex items-center gap-2 text-xs font-semibold text-pilot-primary underline-offset-4 hover:underline"
            aria-expanded={showWhy ? "true" : "false"}
          >
            Neden?
            <Info className="h-3.5 w-3.5" />
          </button>
          {showWhy ? (
            <p className="max-w-md text-xs leading-relaxed text-slate-300">
              Telegram entegrasyonu ile sinyalleri anında alırsınız, fırsat kaçmaz.
            </p>
          ) : null}
        </div>
        <div className="flex flex-col items-start gap-4 md:items-end">
          <button
            type="button"
            onClick={handleOpen}
            className="inline-flex items-center gap-2 rounded-full border border-pilot-primary/40 bg-pilot-primary/20 px-5 py-2 text-sm font-semibold text-pilot-primary-foreground transition-colors hover:border-pilot-primary hover:bg-pilot-primary/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/60"
          >
            <span aria-hidden="true" className="text-lg">
              {contract.ikincil.ikon}
            </span>
            {contract.ikincil.etiket}
            <ArrowUpRight className="h-4 w-4" />
          </button>
          <p className="text-[11px] text-slate-500">Tarama tamamlandıktan sonra sinyaller otomatik gönderilir.</p>
        </div>
      </div>

      {isModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
          <div className="relative w-full max-w-lg rounded-3xl border border-slate-800 bg-slate-950 p-6 shadow-2xl">
            <button
              type="button"
              onClick={handleClose}
              className="absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-700 bg-slate-900 text-slate-400 transition-colors hover:border-slate-500 hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/60"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Telegram modalını kapat</span>
            </button>
            <div className="space-y-5">
              <header className="space-y-2 text-slate-200">
                <div className="inline-flex items-center gap-2 rounded-full border border-pilot-primary/40 bg-pilot-primary/10 px-3 py-1 text-xs font-semibold text-pilot-primary-foreground">
                  <BellRing className="h-3.5 w-3.5" />
                  Telegram Bildirimleri
                </div>
                <h3 className="text-2xl font-semibold">FinPilot'u Telegram'a Bağla</h3>
                <p className="text-sm text-slate-400">
                  QR kodu tarayarak veya linke tıklayarak FinPilot Telegram botunu aktive et. İlk girişte sana özel sinyal akışını açıyoruz.
                </p>
              </header>
              <div className="flex flex-col gap-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-5 md:flex-row md:items-center md:justify-between">
                <div className="grid grid-cols-7 gap-1 rounded-xl bg-slate-200 p-4 shadow-inner">
                  {QR_PATTERN.map((row, rowIndex) =>
                    row.map((cell, cellIndex) => (
                      <span
                        key={`${rowIndex}-${cellIndex}`}
                        className={`h-4 w-4 rounded ${cell ? "bg-slate-900" : "bg-slate-100"}`}
                      />
                    ))
                  )}
                </div>
                <div className="space-y-3 text-sm text-slate-200">
                  <div className="rounded-full border border-slate-700 bg-slate-900/80 px-3 py-1 text-xs uppercase tracking-wide text-slate-400">
                    Alternatif
                  </div>
                  <a
                    href="https://t.me/fnpilotbot"
                    target="_blank"
                    rel="noreferrer noopener"
                    className="inline-flex items-center gap-2 rounded-full bg-pilot-primary px-4 py-2 text-sm font-semibold text-pilot-primary-foreground transition hover:bg-pilot-primary/90"
                  >
                    Botu Aç
                    <ArrowUpRight className="h-4 w-4" />
                  </a>
                  <p className="text-xs text-slate-400">
                    QR kodu taratmak istemiyorsan linke tıklayarak da bağlanabilirsin. Telegram'da @fnpilotbot seni karşılayacak.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
