import type { ChangeEvent } from "react";
import { useMemo } from "react";
import { calculateMaxLossPercent, getRiskInsight } from "../utils/risk";
import { useSettingsStore } from "../store/settingsStore";
import type { SettingsStore } from "../types/settings";

export function RiskSlider() {
  const { skor: riskScore, setField } = useSettingsStore((state: SettingsStore) => ({
    skor: state.kullaniciRiskSkoru,
    setField: state.setField
  }));

  const insight = useMemo(() => getRiskInsight(riskScore), [riskScore]);
  const maxLossPercent = useMemo(() => calculateMaxLossPercent(riskScore), [riskScore]);
  const handleRiskChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextScore = Number(event.target.value);
    const nextMaxLoss = calculateMaxLossPercent(nextScore);
    setField("kullaniciRiskSkoru", nextScore);
    setField("maksimumKayipLimiti", nextMaxLoss);
  };

  return (
    <section id="risk-profile" className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <label htmlFor="risk-slider" className="block text-sm font-semibold uppercase tracking-wide text-slate-300">
            Risk İştahı
          </label>
          <span className="text-xs text-slate-500">Skor: {riskScore}/10</span>
        </div>
        <div className="text-right">
          <span className={`block text-sm font-semibold ${insight.colorClass}`}>{insight.label}</span>
          <span className="text-xs text-slate-400">{insight.description}</span>
        </div>
      </div>
      <input
        id="risk-slider"
        type="range"
        min={1}
        max={10}
        step={1}
        value={riskScore}
        onChange={handleRiskChange}
        className="risk-slider h-3 w-full appearance-none rounded-full"
        aria-valuetext={`${insight.label} risk seviyesi`}
        aria-label="Risk iştahı"
      />
      <div className="flex justify-between text-[11px] uppercase tracking-wide text-slate-500">
        <span>Düşük</span>
        <span>Dengeli</span>
        <span>Yüksek</span>
      </div>
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 px-4 py-3 text-xs text-slate-300">
        <p>
          Seçilen seviye ile önerilen maksimum kayıp limiti: <span className="font-semibold text-emerald-300">%{maxLossPercent.toFixed(1)}</span>. Bu değer portföy büyüklüğüne göre otomatik hesaplanır.
        </p>
      </div>
    </section>
  );
}
