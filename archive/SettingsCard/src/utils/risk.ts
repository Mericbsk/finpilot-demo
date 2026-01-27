export type RiskCategory = "Düşük" | "Dengeli" | "Yüksek";

interface RiskInsight {
  label: RiskCategory;
  description: string;
  colorClass: string;
  accentColor: string;
}

const RISK_PROFILES: Array<{ max: number; insight: RiskInsight }> = [
  {
    max: 3,
    insight: {
      label: "Düşük",
      description: "Sermaye koruması öncelikli, stoplar sıkı tutulur.",
      colorClass: "text-emerald-300",
      accentColor: "#22c55e"
    }
  },
  {
    max: 7,
    insight: {
      label: "Dengeli",
      description: "Risk ve ödül dengesi, trend fırsatlarını kovalarsın.",
      colorClass: "text-amber-300",
      accentColor: "#facc15"
    }
  },
  {
    max: 10,
    insight: {
      label: "Yüksek",
      description: "Volatiliteyi seviyor, agresif hedefleri zorluyorsun.",
      colorClass: "text-rose-300",
      accentColor: "#ef4444"
    }
  }
];

export function getRiskInsight(score: number): RiskInsight {
  const profile = RISK_PROFILES.find((entry) => score <= entry.max) ?? RISK_PROFILES[RISK_PROFILES.length - 1];
  return profile.insight;
}

export function calculateMaxLossPercent(score: number): number {
  const clampedScore = Math.min(Math.max(score, 1), 10);
  // Linear map 1-10 score to 3%-25% max loss
  const minPercent = 3;
  const maxPercent = 25;
  const percent = minPercent + ((clampedScore - 1) / 9) * (maxPercent - minPercent);
  return Math.round(percent * 10) / 10; // single decimal precision
}

export function getSliderGradientFill(score: number): string {
  const percent = ((Math.min(Math.max(score, 1), 10) - 1) / 9) * 100;
  const fillPercent = Math.max(percent, 1);
  return `linear-gradient(90deg, #22c55e 0%, #facc15 50%, #ef4444 100%) 0 / ${fillPercent}% 100% no-repeat, rgba(15,23,42,0.7)`;
}
