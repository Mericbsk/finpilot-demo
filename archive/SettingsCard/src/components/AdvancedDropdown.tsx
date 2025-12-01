import { useState } from "react";
import type { ChangeEvent } from "react";
import { ChevronDownIcon } from "lucide-react";
import { useSettingsStore } from "../store/settingsStore";
import type { GelismisAyarlar, SettingsStore } from "../types/settings";

const TIMEFRAMES: GelismisAyarlar["zamanDilimi"][] = ["Günlük", "Haftalık", "Aylık"];
const DATA_SOURCES: GelismisAyarlar["veriKaynagi"][] = ["API1", "API2"];

export function AdvancedDropdown() {
  const [open, setOpen] = useState(false);
  const { advanced, setField } = useSettingsStore((state: SettingsStore) => ({
    advanced: state.gelismisAyarlar,
    setField: state.setField
  }));

  const updateAdvanced = (value: GelismisAyarlar) => setField("gelismisAyarlar", value);

  const handleTimeframeChange = (event: ChangeEvent<HTMLSelectElement>) => {
    updateAdvanced({ ...advanced, zamanDilimi: event.target.value as GelismisAyarlar["zamanDilimi"] });
  };

  const handleSourceChange = (event: ChangeEvent<HTMLSelectElement>) => {
    updateAdvanced({ ...advanced, veriKaynagi: event.target.value as GelismisAyarlar["veriKaynagi"] });
  };

  const handleIndicatorToggle = (indicator: keyof GelismisAyarlar["gostergeler"]) => () => {
    updateAdvanced({
      ...advanced,
      gostergeler: {
        ...advanced.gostergeler,
        [indicator]: !advanced.gostergeler[indicator]
      }
    });
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60">
      <button
        type="button"
        onClick={() => setOpen((prevOpen) => !prevOpen)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-slate-200"
        aria-expanded={open ? "true" : "false"}
      >
        Gelişmiş Ayarlar
        <ChevronDownIcon className={`h-4 w-4 transition-transform ${open ? "rotate-180" : "rotate-0"}`} />
      </button>
      {open ? (
        <div className="space-y-4 border-t border-slate-800 px-4 py-4 text-sm">
          <div className="grid gap-3 md:grid-cols-2">
            <label className="space-y-1">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Zaman Dilimi</span>
              <select
                value={advanced.zamanDilimi}
                onChange={handleTimeframeChange}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-pilot-primary focus:ring-2 focus:ring-pilot-primary/30"
              >
                {TIMEFRAMES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Veri Kaynağı</span>
              <select
                value={advanced.veriKaynagi}
                onChange={handleSourceChange}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-pilot-primary focus:ring-2 focus:ring-pilot-primary/30"
              >
                {DATA_SOURCES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <fieldset className="space-y-2">
            <legend className="text-xs font-semibold uppercase tracking-wide text-slate-400">Göstergeler</legend>
            <div className="grid gap-2 md:grid-cols-3">
              {(Object.keys(advanced.gostergeler) as Array<keyof GelismisAyarlar["gostergeler"]>).map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={handleIndicatorToggle(key)}
                  className={`rounded-lg border px-3 py-2 text-left text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/60 ${
                    advanced.gostergeler[key]
                      ? "border-pilot-primary bg-pilot-primary/10 text-slate-100"
                      : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                  }`}
                >
                  {key.toUpperCase()}
                </button>
              ))}
            </div>
          </fieldset>
        </div>
      ) : null}
    </div>
  );
}
