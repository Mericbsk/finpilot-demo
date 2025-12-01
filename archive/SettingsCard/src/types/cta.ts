export type PrimaryCtaStatus = "idle" | "loading" | "completed";

export type SecondaryCtaStatus = "kapali" | "aktif";

export type CtaType = "primary" | "secondary";

export type CtaLocation = "stickyTop" | "bottomPanel";

export interface BaseCtaConfig {
  etiket: string;
  ikon: string;
  tip: CtaType;
  konum: CtaLocation;
  aciklama?: string;
}

export interface PrimaryCtaConfig extends BaseCtaConfig {
  tip: "primary";
  konum: "stickyTop";
  durum: PrimaryCtaStatus;
}

export interface SecondaryCtaConfig extends BaseCtaConfig {
  tip: "secondary";
  konum: "bottomPanel";
  durum: SecondaryCtaStatus;
}

export interface CtaContract {
  ana: PrimaryCtaConfig;
  ikincil: SecondaryCtaConfig;
}
