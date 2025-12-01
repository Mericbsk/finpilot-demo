export type SinyalTipi = "AL" | "BEKLE" | "SAT";

export type SinyalDurumu = "Başarılı" | "Başarısız" | "Açık Pozisyon";

export type TarihAraligi = "Son 30 Gün" | "Son 90 Gün" | "Tüm Zamanlar";

export interface PerformanceMetrics {
  basariOraniYuzde: number;
  basariOraniTrend: number[];
  ortalamaNetGetiriYuzde: number;
  ortalamaNetGetiriTrend: number[];
  netKarZararUSD: number;
  netKarZararTrend: number[];
}

export interface GecmisSinyal {
  id: string;
  tarih: string; // ISO date string
  sembol: string;
  sinyal: SinyalTipi;
  rrOrani: number;
  kapanisFiyati: number;
  netGetiriYuzdesi: number;
  durum: SinyalDurumu;
  tldr: string;
  grafikNotu?: string;
}

export type AltBolumIpucuTipi = "STRATEJI_HATIRLATMA" | "AKSIYON_IPUCU" | "EGITIM_CTA";

export interface AltBolumIpucu {
  tip: AltBolumIpucuTipi;
  baslik: string;
  icerik: string;
  oncelik: number;
  terimEslestirme?: string[];
  baglanti?: {
    etiket: string;
    url: string;
  };
}

export interface PilotChecklistAdimi {
  id: string;
  icerik: string;
  aciklama?: string;
}

export interface PerformanceDataset {
  kpi: PerformanceMetrics;
  gecmisSinyaller: GecmisSinyal[];
  altBolumIpuclari: AltBolumIpucu[];
  pilotChecklist: PilotChecklistAdimi[];
}
