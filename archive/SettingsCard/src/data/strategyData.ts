import type { TaramaStratejisi } from "../types/settings";

export interface StrategyMeta {
  tip: TaramaStratejisi;
  ikon: string;
  baslik: string;
  aciklama: string;
  mikroOgrenme: string;
  cta: string;
  ornekSinyal: {
    sembol: string;
    sinyal: string;
    rrOrani: number;
  };
}

export const STRATEGY_DATA: StrategyMeta[] = [
  {
    tip: "Normal",
    ikon: "⚖️",
    baslik: "Dengeli Strateji",
    aciklama: "Teknik + temel analizle istikrarlı sinyaller.",
    mikroOgrenme: "Risk ve getiri arasında denge kurar; daha yüksek kazanma oranına odaklanır.",
    cta: "İstikrarlı sinyalleri gör",
    ornekSinyal: {
      sembol: "AAPL",
      sinyal: "AL",
      rrOrani: 2.5
    }
  },
  {
    tip: "Agresif",
    ikon: "⚡",
    baslik: "Momentum Stratejisi",
    aciklama: "Trendleri erken yakala, daha yüksek volatilite.",
    mikroOgrenme: "Kısa vadeli fırsatları hedefler; dalgalanma (volatilite) yüksektir.",
    cta: "Trend fırsatlarını yakala",
    ornekSinyal: {
      sembol: "TSLA",
      sinyal: "AL",
      rrOrani: 3.8
    }
  }
];
