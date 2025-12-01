import type { ChangeEvent } from "react";
import { useMemo } from "react";
import { Info } from "lucide-react";
import { useSettingsStore } from "../store/settingsStore";
import type { SettingsStore } from "../types/settings";

export function PortfolioInput() {
  const { portfoy, maxLoss, riskScore, setField } = useSettingsStore((state: SettingsStore) => ({
    portfoy: state.portfoyBuyukluguUSD,
    maxLoss: state.maksimumKayipLimiti,
    riskScore: state.kullaniciRiskSkoru,
    setField: state.setField
  }));

  const potentialLoss = useMemo(() => (portfoy * maxLoss) / 100, [portfoy, maxLoss]);
  const kellySuggestion = useMemo(() => {
    const scaled = Math.min(Math.max(riskScore / 10, 0.1), 1);
    return Math.round(scaled * 100) / 100;
  }, [riskScore]);

  const handlePortfolioChange = (event: ChangeEvent<HTMLInputElement>) => {
    setField("portfoyBuyukluguUSD", Number(event.target.value));
  };

  return (
    <section className="space-y-4">
      <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="space-y-2">
          <label htmlFor="portfolio-input" className="text-sm font-semibold text-slate-300">
            Portföy Büyüklüğü (USD)
          </label>
          <input
            id="portfolio-input"
            type="number"
            min={0}
            step={100}
            value={portfoy}
            onChange={handlePortfolioChange}
            className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-pilot-primary focus:ring-2 focus:ring-pilot-primary/30"
          />
          <p className="text-xs text-slate-500">Pozisyon önerileri ve risk hesapları bu tutar üzerinden yapılır.</p>
        </div>
        <div className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-5 text-sm text-slate-200">
          <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-400">
            <span>Maksimum Kayıp Limiti</span>
            <span
              className="flex h-6 w-6 items-center justify-center rounded-full border border-slate-700 bg-slate-900/80 text-slate-400"
              title="Seçtiğin risk seviyesine göre portföyünde kabul edilebilir maksimum kaybı gösterir."
            >
              <Info className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex min-w-[120px] flex-1 flex-col justify-between rounded-xl border border-slate-700 bg-slate-950/80 px-4 py-3 shadow-inner">
              <span className="text-[10px] uppercase tracking-wide text-slate-500">Yüzde</span>
              <span className="text-2xl font-semibold text-emerald-300">%{maxLoss.toFixed(1)}</span>
            </div>
            <div className="flex min-w-[140px] flex-1 flex-col justify-between rounded-xl border border-slate-700 bg-slate-950/80 px-4 py-3 shadow-inner">
              <span className="text-[10px] uppercase tracking-wide text-slate-500">Tutar</span>
              <span className="text-2xl font-semibold text-slate-100">${potentialLoss.toLocaleString("tr-TR", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>
            </div>
          </div>
          <p className="text-xs text-slate-400">
            Portföyünün <span className="font-semibold text-emerald-200">%{maxLoss.toFixed(1)}</span> kısmını riske atmış olursun. Stop-Loss ve Take-Profit seviyelerini bu limitte kurgula.
          </p>
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <span className="rounded-full border border-pilot-primary/40 bg-pilot-primary/10 px-2 py-1 font-semibold text-pilot-primary-foreground">
              Kelly Önerisi: {Math.round(kellySuggestion * 100)}%
            </span>
            <span>Risk skoru: {riskScore}/10</span>
          </div>
        </div>
      </div>
    </section>
  );
}
