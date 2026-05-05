/**
 * Shared user settings helper.
 * Reads from localStorage (fast, sync) with backend as the source of truth.
 * Other pages import `loadSettings()` to get the latest saved values.
 */

export const SETTINGS_KEY = "finpilot_settings";

export interface UserSettings {
  riskAppetite: number;       // 1-5
  portfolioSize: number;      // USD
  maxLossPercent: number;     // % per trade
  trailingStop: boolean;
  scanStrategy: string;       // hybrid | momentum | value | growth
  market: string;             // US | EU | Global
  timeframe: string;          // 1D | 4H | 1H
  preMarket: boolean;
  afterHours: boolean;
  telegramEnabled: boolean;
  telegramChatId: string;
  emailAlerts: boolean;
  pushNotifications: boolean;
  alertThreshold: number;
  useEMA: boolean;
  useRSI: boolean;
  useMACD: boolean;
  useATR: boolean;
  useBollinger: boolean;
  useVWAP: boolean;
  emaPeriods: string;
  rsiPeriod: number;
  atrPeriod: number;
}

export const defaultSettings: UserSettings = {
  riskAppetite: 3,
  portfolioSize: 10000,
  maxLossPercent: 2,
  trailingStop: true,
  scanStrategy: "hybrid",
  market: "US",
  timeframe: "1D",
  preMarket: false,
  afterHours: false,
  telegramEnabled: false,
  telegramChatId: "",
  emailAlerts: false,
  pushNotifications: true,
  alertThreshold: 75,
  useEMA: true,
  useRSI: true,
  useMACD: true,
  useATR: true,
  useBollinger: false,
  useVWAP: true,
  emaPeriods: "9,21,50",
  rsiPeriod: 14,
  atrPeriod: 14,
};

/** Read settings synchronously from localStorage. Falls back to defaults. */
export function loadSettings(): UserSettings {
  if (typeof window === "undefined") return defaultSettings;
  try {
    const stored = localStorage.getItem(SETTINGS_KEY);
    if (stored) return { ...defaultSettings, ...JSON.parse(stored) };
  } catch {}
  return defaultSettings;
}

/**
 * Map market setting to currency symbol.
 * US → $, EU → €, default → $
 */
export function getCurrencySymbol(market: string): string {
  if (market === "EU") return "€";
  return "$";
}

/**
 * Map riskAppetite (1-5) to a minimum score threshold (0-100).
 * Higher risk appetite → lower threshold → more signals shown.
 */
export function riskToMinScore(riskAppetite: number): number {
  const map: Record<number, number> = { 1: 80, 2: 70, 3: 60, 4: 45, 5: 30 };
  return map[riskAppetite] ?? 60;
}

/**
 * Map scanStrategy string to backtest strategy label.
 */
export function settingsStrategyToBacktest(scanStrategy: string): string {
  const map: Record<string, string> = {
    hybrid: "Hybrid",
    momentum: "Momentum",
    value: "Value",
    growth: "Growth",
    dividend: "Dividend",
  };
  return map[scanStrategy.toLowerCase()] ?? "Hybrid";
}
