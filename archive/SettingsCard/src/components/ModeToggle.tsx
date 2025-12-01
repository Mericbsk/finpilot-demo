import { useCallback, useMemo } from "react";
import { STRATEGY_DATA } from "../data/strategyData";
import { useSettingsStore } from "../store/settingsStore";
import type { SettingsStore, TaramaStratejisi } from "../types/settings";

export function ModeToggle() {
  const { current, setField } = useSettingsStore((state: SettingsStore) => ({
    current: state.taramaStratejisi,
    setField: state.setField
  }));

  const handleSelect = useCallback(
    (value: TaramaStratejisi) => () => {
      setField("taramaStratejisi", value);
    },
    [setField]
  );

  const cards = useMemo(
    () =>
      STRATEGY_DATA.map((meta) => ({
        ...meta,
        active: meta.tip === current
      })),
    [current]
  );

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-1">
        <span className="text-sm font-semibold uppercase tracking-wide text-slate-300">Tarama Stratejisi</span>
        <p className="text-xs text-slate-500">Sinyal motorunu yatırım tarzına göre kişiselleştir.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {cards.map((card) => (
          <article
            key={card.tip}
            className={`group relative overflow-hidden rounded-2xl border p-5 transition-all focus-within:ring-2 focus-within:ring-pilot-primary/60 ${
              card.active
                ? "border-pilot-primary bg-pilot-primary/10 shadow-lg shadow-pilot-primary/10"
                : "border-slate-800 bg-slate-900/70 hover:border-slate-700 hover:bg-slate-900"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <span className="mt-1 inline-flex h-10 w-10 items-center justify-center rounded-full bg-slate-950 text-2xl">
                  {card.ikon}
                </span>
                <div className="space-y-1">
                  <span className="text-xs uppercase tracking-wide text-slate-400">{card.tip === "Normal" ? "Güven" : "Hız"}</span>
                  <h3 className="text-lg font-semibold text-slate-100">{card.baslik}</h3>
                  <p className="text-sm text-slate-400">{card.aciklama}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleSelect(card.tip)}
                aria-pressed={card.active}
                className={`rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-wide transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/70 ${
                  card.active
                    ? "border-pilot-primary bg-pilot-primary/20 text-pilot-primary-foreground"
                    : "border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500"
                }`}
              >
                {card.active ? "Seçildi" : "Seç"}
              </button>
            </div>
            <p className="mt-4 text-xs text-slate-400">
              {card.mikroOgrenme}
            </p>
            <div className="mt-5 flex flex-wrap items-center gap-4 text-xs text-slate-400">
              <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-2">
                <span className="text-[11px] uppercase tracking-wide text-slate-500">Örnek Sinyal</span>
                <span className="text-sm font-semibold text-slate-100">
                  {card.ornekSinyal.sembol} · {card.ornekSinyal.sinyal}
                </span>
                <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[11px] font-semibold text-emerald-300">
                  R/R {card.ornekSinyal.rrOrani.toFixed(1)}
                </span>
              </div>
              <button
                type="button"
                onClick={handleSelect(card.tip)}
                className="inline-flex items-center gap-2 text-[11px] font-semibold text-pilot-primary underline-offset-4 transition-colors hover:underline"
              >
                {card.cta}
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
