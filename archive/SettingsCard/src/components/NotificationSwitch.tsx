import type { ChangeEvent } from "react";
import { useCallback } from "react";
import { useSettingsStore } from "../store/settingsStore";
import type { SettingsStore } from "../types/settings";

export function NotificationSwitch() {
  const { enabled, chatId, setField } = useSettingsStore((state: SettingsStore) => ({
    enabled: state.telegramAktif,
    chatId: state.telegramId,
    setField: state.setField
  }));

  const handleToggle = useCallback(() => {
    setField("telegramAktif", !enabled);
  }, [enabled, setField]);

  const handleIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setField("telegramId", event.target.value);
  };

  return (
    <section className="flex items-start justify-between gap-8 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-slate-200">Telegram Bildirimleri</h3>
        <p className="text-xs text-slate-400">
          Sinyaller ve risk uyarıları Telegram üzerinden gönderilir.
        </p>
        {enabled ? (
          <label className="mt-2 block text-xs">
            <span className="mb-1 inline-block text-[11px] uppercase tracking-wide text-slate-400">
              Telegram Chat ID
            </span>
            <input
              type="text"
              value={chatId}
              onChange={handleIdChange}
              placeholder="örn. 123456789"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-pilot-primary focus:ring-2 focus:ring-pilot-primary/30"
            />
          </label>
        ) : null}
      </div>
      <button
        type="button"
        onClick={handleToggle}
        aria-pressed={enabled ? "true" : "false"}
        className={`relative inline-flex h-9 w-16 shrink-0 cursor-pointer items-center rounded-full border transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/60 ${
          enabled ? "border-pilot-primary bg-pilot-primary/20" : "border-slate-700 bg-slate-800"
        }`}
      >
        <span
          className={`absolute left-1 inline-block h-7 w-7 transform rounded-full bg-white shadow transition-transform ${
            enabled ? "translate-x-7" : "translate-x-0"
          }`}
        />
        <span className="sr-only">Telegram bildirimlerini {enabled ? "kapat" : "aç"}</span>
      </button>
    </section>
  );
}
