import type { CtaContract } from "../types/cta";

export const ctaContract: CtaContract = {
  ana: {
    etiket: "Taramayı Başlat",
    ikon: "🚀",
    tip: "primary",
    konum: "stickyTop",
    durum: "idle"
  },
  ikincil: {
    etiket: "Telegram Bildirimlerini Aç",
    ikon: "🔔",
    tip: "secondary",
    konum: "bottomPanel",
    aciklama: "Sinyalleri anında almak için Telegram entegrasyonunu aç.",
    durum: "kapali"
  }
};
