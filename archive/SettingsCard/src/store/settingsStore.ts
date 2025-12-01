import { create } from "zustand";
import type { SettingsState, SettingsStore } from "../types/settings";

const DEFAULT_STATE: SettingsState = {
  kullaniciRiskSkoru: 5,
  portfoyBuyukluguUSD: 10000,
  maksimumKayipLimiti: 10,
  taramaStratejisi: "Normal",
  calismaPiyasasi: "Kripto",
  telegramAktif: false,
  telegramId: "",
  gelismisAyarlar: {
    zamanDilimi: "Günlük",
    veriKaynagi: "API1",
    gostergeler: {
      ema: true,
      rsi: false,
      atr: true
    }
  }
};

export const useSettingsStore = create<SettingsStore>((set) => {
  const setField: SettingsStore["setField"] = (field, value) =>
    set((state) => ({
      ...state,
      [field]: value
    }));

  const reset: SettingsStore["reset"] = () =>
    set(() => ({
      ...DEFAULT_STATE,
      setField,
      reset
    }));

  return {
    ...DEFAULT_STATE,
    setField,
    reset
  };
});
