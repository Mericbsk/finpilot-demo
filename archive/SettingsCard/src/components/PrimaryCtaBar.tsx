import { useMemo } from "react";
import { CheckCircle2, Loader2, Rocket } from "lucide-react";
import { useCtaStore } from "../store/ctaStore";

export function PrimaryCtaBar() {
  const { contract, primaryStatus, triggerPrimary } = useCtaStore((state) => ({
    contract: state.contract,
    primaryStatus: state.primaryStatus,
    triggerPrimary: state.triggerPrimary
  }));

  const { label, helper, Icon } = useMemo(() => {
    switch (primaryStatus) {
      case "loading":
        return {
          label: "Tarama yapılıyor...",
          helper: "PilotShield senin için fırsatları tarıyor",
          Icon: Loader2
        };
      case "completed":
        return {
          label: "Tarama tamamlandı – Yeniden başlat",
          helper: "Son taramayı gözden geçir, hazır olduğunda tekrar başlat",
          Icon: CheckCircle2
        };
      default:
        return {
          label: contract.ana.etiket,
          helper: "Saniyeler içinde kişiselleştirilmiş sinyaller al.",
          Icon: Rocket
        };
    }
  }, [contract.ana.etiket, primaryStatus]);

  const isLoading = primaryStatus === "loading";

  return (
    <div className="sticky top-6 z-40 mx-auto w-full max-w-6xl px-4 sm:px-6">
      <div className="relative overflow-hidden rounded-3xl border border-pilot-primary/30 bg-slate-950/90 shadow-[0_25px_90px_-35px_rgba(14,165,233,0.6)]">
        <div className="pointer-events-none absolute -inset-10 animate-pulse bg-[radial-gradient(circle_at_top,_rgba(14,116,144,0.25),_transparent_55%)] blur-3xl" aria-hidden="true" />
        <div className="relative flex flex-col gap-4 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-pilot-primary">FinPilot</p>
            <p className="mt-2 text-lg font-semibold text-slate-100">Kokpitini aktive et, taramayı başlat.</p>
            <p className="text-sm text-slate-400">{helper}</p>
          </div>
          <div className="flex flex-col items-start gap-2 sm:items-end">
            <button
              type="button"
              onClick={triggerPrimary}
              disabled={isLoading}
              className="group inline-flex items-center gap-3 rounded-full bg-gradient-to-r from-pilot-primary via-sky-500 to-pilot-primary px-6 py-3 text-sm font-semibold text-pilot-primary-foreground shadow-lg shadow-pilot-primary/30 transition-all hover:shadow-[0_20px_50px_-20px_rgba(14,165,233,0.8)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/60 disabled:cursor-not-allowed disabled:opacity-80"
            >
              <span className="relative flex h-10 w-10 items-center justify-center rounded-full bg-white/15 text-white">
                <Icon className={`h-5 w-5 ${isLoading ? "animate-spin" : ""}`} aria-hidden="true" />
                <span className="absolute inset-0 rounded-full border border-white/20" aria-hidden="true" />
              </span>
              <span className="pr-1 text-left uppercase tracking-wide">
                {label}
              </span>
            </button>
            <span className="text-xs text-slate-400" aria-live="polite">
              {primaryStatus === "loading" ? "PilotShield tarıyor" : primaryStatus === "completed" ? "Son tarama 3 sn sürdü" : "Hazır olduğunda başlat"}
            </span>
          </div>
        </div>
        <div className="pointer-events-none absolute inset-x-6 bottom-0 h-1 overflow-hidden rounded-full bg-slate-800/80" aria-hidden="true">
          <div
            className={`h-full origin-left transform rounded-full bg-gradient-to-r from-pilot-primary via-sky-400 to-pilot-primary transition-transform duration-500 ease-out ${
              primaryStatus === "loading"
                ? "animate-cta-progress"
                : primaryStatus === "completed"
                  ? "scale-x-100"
                  : "scale-x-0"
            }`}
          />
        </div>
      </div>
    </div>
  );
}
