import type { ChangeEvent } from "react";
import { Navigation, ShieldCheck } from "lucide-react";
import type { SettingsStore } from "../types/settings";
import { useSettingsStore } from "../store/settingsStore";
import { RiskSlider } from "./RiskSlider";
import { PortfolioInput } from "./PortfolioInput";
import { ModeToggle } from "./ModeToggle";
import { NotificationSwitch } from "./NotificationSwitch";
import { AdvancedDropdown } from "./AdvancedDropdown";

const MARKETS: SettingsStore["calismaPiyasasi"][] = ["Kripto", "Hisse", "Forex"];

export function SettingsCard() {
  const { market, reset, setField } = useSettingsStore((state: SettingsStore) => ({
    market: state.calismaPiyasasi,
    reset: state.reset,
    setField: state.setField
  }));

  const handleMarketChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setField("calismaPiyasasi", event.target.value as SettingsStore["calismaPiyasasi"]);
  };

  return (
    <article className="mx-auto max-w-4xl rounded-3xl border border-slate-800 bg-slate-950/80 shadow-2xl shadow-pilot-primary/5 backdrop-blur">
      <header className="flex flex-col gap-6 border-b border-slate-800 px-6 py-6 md:flex-row md:items-start md:justify-between">
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <span className="mt-1 inline-flex h-10 w-10 items-center justify-center rounded-full border border-pilot-primary/40 bg-pilot-primary/10 text-pilot-primary">
              <Navigation className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-pilot-primary">FinPilot</p>
              <h1 className="text-3xl font-semibold text-slate-50">Riskini Belirle, Sinyallerini Al</h1>
            </div>
          </div>
          <p className="max-w-xl text-sm text-slate-300">
            Portföyünü ve risk iştahını ayarla, FinPilot sana en uygun sinyalleri göstersin. Yeniysen, FinSense seni adım adım yönlendirir.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href="#risk-profile"
              className="inline-flex items-center gap-2 rounded-full bg-pilot-primary px-5 py-2 text-sm font-semibold text-pilot-primary-foreground transition-transform hover:translate-y-[-1px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/60"
            >
              Risk Profilini Belirle
            </a>
            <a
              href="https://finsense.ai/baslangic"
              target="_blank"
              rel="noreferrer noopener"
              className="inline-flex items-center gap-2 rounded-full border border-slate-700 px-5 py-2 text-sm font-semibold text-slate-200 transition-colors hover:border-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/40"
            >
              FinSense ile öğren
            </a>
          </div>
        </div>
        <div className="flex w-full flex-col gap-4 md:w-auto md:max-w-xs">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 text-sm text-slate-200 shadow-inner">
            <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-400">
              <span>Örnek Sinyal</span>
              <span className="inline-flex items-center gap-1 text-emerald-300">
                <ShieldCheck className="h-4 w-4" /> PilotShield
              </span>
            </div>
            <div className="mt-3 space-y-2">
              <div className="flex items-baseline justify-between">
                <p className="text-lg font-semibold text-slate-100">AAPL · AL</p>
                <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs font-semibold text-emerald-300">R/R 2.7</span>
              </div>
              <p className="text-xs text-slate-400">Stop-Loss: $182.40 · Take-Profit: $205.10</p>
              <p className="text-[11px] text-slate-500">Momentum güçlü, bilanço sonrası yükseliş.</p>
            </div>
          </div>
          <button
            type="button"
            onClick={reset}
            className="inline-flex items-center justify-center rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-200 transition-colors hover:border-slate-700 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/50"
          >
            Varsayılana Dön
          </button>
        </div>
      </header>
      <div className="space-y-6 px-6 py-8">
        <RiskSlider />
        <ModeToggle />
        <label className="space-y-2" htmlFor="market-select">
          <span className="block text-sm font-semibold uppercase tracking-wide text-slate-300">Piyasa Seçimi</span>
          <select
            id="market-select"
            value={market}
            onChange={handleMarketChange}
            className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3 py-3 text-sm text-slate-200 outline-none focus:border-pilot-primary focus:ring-2 focus:ring-pilot-primary/40"
          >
            {MARKETS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <PortfolioInput />
        <NotificationSwitch />
        <AdvancedDropdown />
      </div>
    </article>
  );
}
