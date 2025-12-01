export type TaramaStratejisi = "Normal" | "Agresif";
export type CalismaPiyasasi = "Kripto" | "Hisse" | "Forex";

export interface GelismisAyarlar {
  zamanDilimi: "Günlük" | "Haftalık" | "Aylık";
  veriKaynagi: "API1" | "API2";
  gostergeler: {
    ema: boolean;
    rsi: boolean;
    atr: boolean;
  };
}

export interface SettingsState {
  kullaniciRiskSkoru: number;
  portfoyBuyukluguUSD: number;
  maksimumKayipLimiti: number;
  taramaStratejisi: TaramaStratejisi;
  calismaPiyasasi: CalismaPiyasasi;
  telegramAktif: boolean;
  telegramId: string;
  gelismisAyarlar: GelismisAyarlar;
}

export interface SettingsStore extends SettingsState {
  setField: <K extends keyof SettingsState>(field: K, value: SettingsState[K]) => void;
  reset: () => void;
}
