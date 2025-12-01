import type { ReactNode } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  GraduationCap,
  HelpCircle,
  Info,
  Minus,
  Search,
  Share2,
  X
} from "lucide-react";
import { performanceData, DATE_RANGE_OPTIONS } from "../data/performanceData";
import type { AltBolumIpucu, GecmisSinyal, SinyalDurumu, SinyalTipi, TarihAraligi } from "../types/performance";
import { useCountUp } from "../hooks/useCountUp";
import { TelegramCtaPanel } from "./TelegramCtaPanel";

const SIGNAL_TYPES: SinyalTipi[] = ["AL", "BEKLE", "SAT"];
const STATUS_OPTIONS: SinyalDurumu[] = ["Başarılı", "Başarısız", "Açık Pozisyon"];

const statusBadgeClasses: Record<SinyalDurumu, string> = {
  Başarılı: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
  Başarısız: "bg-rose-500/10 text-rose-300 border border-rose-500/30",
  "Açık Pozisyon": "bg-amber-500/10 text-amber-300 border border-amber-500/30"
};

const formatterTL = new Intl.NumberFormat("tr-TR", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0
});

const formatterPercent = new Intl.NumberFormat("tr-TR", {
  maximumFractionDigits: 1
});

const formatterDate = new Intl.DateTimeFormat("tr-TR", {
  year: "numeric",
  month: "short",
  day: "2-digit"
});

function getNetResultClass(value: number) {
  if (value > 0) return "text-emerald-400";
  if (value < 0) return "text-rose-400";
  return "text-slate-300";
}

function getPercentBadgeTone(value: number) {
  if (value >= 70) return "text-emerald-200";
  if (value >= 60) return "text-amber-200";
  return "text-rose-200";
}

function getReturnBadgeTone(value: number) {
  if (value > 0) return "text-emerald-200";
  if (value < 0) return "text-rose-200";
  return "text-slate-200";
}

interface KpiCardConfig {
  id: string;
  label: string;
  helper: string;
  info?: string;
  target: number;
  trend: number[];
  cardClass: string;
  icon: ReactNode;
  stroke: string;
  decimals?: number;
  formatValue: (value: number) => string;
  valueClass?: (value: number) => string;
}

function buildSparklinePoints(data: number[], width = 120, height = 36) {
  if (!data.length) {
    return `0,${height}`;
  }
  if (data.length === 1) {
    return `0,${height / 2}`;
  }
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const step = width / (data.length - 1);

  return data
    .map((value, index) => {
      const x = index * step;
      const y = height - ((value - min) / range) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

function Sparkline({ data, stroke }: { data: number[]; stroke: string }) {
  const width = 120;
  const height = 36;
  const points = buildSparklinePoints(data, width, height);

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      className="w-full"
      role="presentation"
      aria-hidden="true"
    >
      <polyline
        points={points}
        fill="none"
        stroke={stroke}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={0.9}
      />
    </svg>
  );
}

function KpiCard({ config }: { config: KpiCardConfig }) {
  const { decimals = 1 } = config;
  const animatedValue = useCountUp(config.target, {
    duration: 900,
    format: (value) => Number(value.toFixed(decimals))
  });

  const displayValue = config.formatValue(animatedValue);
  const valueTone = config.valueClass ? config.valueClass(config.target) : "";

  return (
    <article
      className={`relative flex h-full flex-col overflow-hidden rounded-2xl border px-6 py-6 shadow-inner transition-shadow hover:shadow-lg hover:shadow-pilot-primary/10 ${config.cardClass}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase tracking-wide text-slate-200/80">{config.label}</span>
            {config.info ? (
              <span
                className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-white/10 bg-white/10 text-[10px] text-slate-100"
                title={config.info}
              >
                <Info className="h-3 w-3" aria-hidden="true" />
              </span>
            ) : null}
          </div>
          <p className={`mt-2 text-3xl font-semibold ${valueTone}`}>{displayValue}</p>
        </div>
        <span className="rounded-full border border-white/20 bg-white/10 p-2 text-white shadow-inner" aria-hidden="true">
          {config.icon}
        </span>
      </div>
      <p className="mt-4 text-xs text-slate-200/70">{config.helper}</p>
      <div className="mt-6">
        <Sparkline data={config.trend} stroke={config.stroke} />
      </div>
    </article>
  );
}

const strategyKeywordStyles: Record<string, string> = {
  "Yeşil sinyalleri": "text-emerald-300 font-semibold",
  "R/R Oranına": "text-cyan-300 font-semibold",
  "R/R > 2.0": "text-cyan-300 font-semibold",
  "R/R": "text-cyan-300 font-semibold",
  "Stop-Loss": "text-rose-300 font-semibold",
  "Take-Profit": "text-emerald-300 font-semibold",
  "AL": "text-emerald-200 font-semibold"
};

function highlightStrategySentence(sentence: string) {
  let html = sentence;
  Object.entries(strategyKeywordStyles).forEach(([keyword, className]) => {
    const pattern = new RegExp(keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "g");
    html = html.replace(pattern, `<span class="${className}">${keyword}</span>`);
  });
  return html;
}

const categorizeTips = (tips: AltBolumIpucu[]) => {
  const sorted = [...tips].sort((a, b) => a.oncelik - b.oncelik);
  const primary = sorted.find((item) => item.tip === "STRATEJI_HATIRLATMA") ?? sorted[0] ?? null;
  const secondary = sorted.filter((item) => item !== primary);
  return { primary, secondary };
};

function getDateRangeDays(range: TarihAraligi) {
  switch (range) {
    case "Son 30 Gün":
      return 30;
    case "Son 90 Gün":
      return 90;
    default:
      return null;
  }
}

export function PerformanceSection() {
  const [dateRange, setDateRange] = useState<TarihAraligi>("Son 30 Gün");
  const [symbolQuery, setSymbolQuery] = useState<string>("");
  const [selectedTypes, setSelectedTypes] = useState<Record<SinyalTipi, boolean>>({
    AL: true,
    BEKLE: true,
    SAT: true
  });
  const [selectedStatus, setSelectedStatus] = useState<Record<SinyalDurumu, boolean>>({
    Başarılı: true,
    Başarısız: true,
    "Açık Pozisyon": true
  });
  const [activeSignal, setActiveSignal] = useState<GecmisSinyal | null>(null);
  const [shareFeedback, setShareFeedback] = useState<string | null>(null);

  const shareSummary = useMemo(
    () =>
      [
        "FinPilot Performans Özeti",
        `• Başarı Oranı: ${formatterPercent.format(performanceData.kpi.basariOraniYuzde)}%`,
        `• Ortalama Net Getiri: ${formatterPercent.format(performanceData.kpi.ortalamaNetGetiriYuzde)}%`,
        `• Net P&L: ${formatterTL.format(performanceData.kpi.netKarZararUSD)}`,
        `• Toplam sinyal: ${performanceData.gecmisSinyaller.length}`
      ].join("\n"),
    []
  );

  const handleShareClick = useCallback(async () => {
    const summary = shareSummary;
    try {
      if (typeof navigator !== "undefined" && "share" in navigator) {
        const shareNavigator = navigator as Navigator & {
          share?: (data: ShareData) => Promise<void>;
        };
        if (shareNavigator.share) {
          await shareNavigator.share({
            title: "FinPilot Performans Özeti",
            text: summary
          });
          setShareFeedback("Paylaşım gönderildi");
          return;
        }
      }

      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(summary);
        setShareFeedback("Özet panoya kopyalandı");
        return;
      }

      setShareFeedback("Paylaşmak için tarayıcı desteği gerekli");
    } catch (error) {
      setShareFeedback("Paylaşım tamamlanamadı");
    }
  }, [shareSummary]);

  useEffect(() => {
    if (!shareFeedback) {
      return;
    }
    const timeout = window.setTimeout(() => {
      setShareFeedback(null);
    }, 3000);
    return () => window.clearTimeout(timeout);
  }, [shareFeedback]);

  const { primary: primaryTip, secondary: secondaryTips } = useMemo(
    () => categorizeTips(performanceData.altBolumIpuclari),
    []
  );

  const infoTips = useMemo(
    () => secondaryTips.filter((tip) => tip.tip !== "EGITIM_CTA"),
    [secondaryTips]
  );

  const ctaTip = useMemo(
    () => secondaryTips.find((tip) => tip.tip === "EGITIM_CTA") ?? null,
    [secondaryTips]
  );

  const checklistItems = performanceData.pilotChecklist;

  const uniqueSymbols = useMemo(() => {
    return Array.from(new Set(performanceData.gecmisSinyaller.map((item) => item.sembol))).sort();
  }, []);

  const filteredSignals = useMemo(() => {
    const rangeDays = getDateRangeDays(dateRange);
    const now = new Date();
    const msInDay = 1000 * 60 * 60 * 24;
    const needle = symbolQuery.trim().toLowerCase();

    return performanceData.gecmisSinyaller.filter((signal) => {
      if (rangeDays !== null) {
        const signalDate = new Date(signal.tarih);
        const diffInDays = (now.getTime() - signalDate.getTime()) / msInDay;
        if (diffInDays > rangeDays) {
          return false;
        }
      }

      if (needle && !signal.sembol.toLowerCase().includes(needle)) {
        return false;
      }

      if (!selectedTypes[signal.sinyal]) {
        return false;
      }

      if (!selectedStatus[signal.durum]) {
        return false;
      }

      return true;
    });
  }, [dateRange, selectedStatus, selectedTypes, symbolQuery]);

  const needsRRReminder = useMemo(
    () => filteredSignals.some((signal) => signal.rrOrani < 2),
    [filteredSignals]
  );

  const kpiCards: KpiCardConfig[] = [
    {
      id: "win-rate",
      label: "Başarı Oranı",
      helper: "Son dönem sinyallerin doğruluk oranı",
      info: "FinPilot pilotlarının hedefi yüzde 70 ve üzeri başarı oranıdır.",
      target: performanceData.kpi.basariOraniYuzde,
      trend: performanceData.kpi.basariOraniTrend.map((value) => value * 100),
      cardClass: "border-emerald-500/30 bg-gradient-to-br from-emerald-500/15 via-emerald-500/5 to-slate-950 text-emerald-50",
      icon:
        performanceData.kpi.basariOraniYuzde >= 60 ? (
          <ArrowUpRight className="h-5 w-5" />
        ) : (
          <ArrowDownRight className="h-5 w-5" />
        ),
      stroke: "#34d399",
      decimals: 0,
      formatValue: (value) => `${formatterPercent.format(value)}%`,
      valueClass: getPercentBadgeTone
    },
    {
      id: "avg-return",
      label: "Ortalama Net Getiri",
      helper: "Kazanan işlemlerin ortalama getirisi",
      info: "Pozitif değerler momentum gücünü teyit eder.",
      target: performanceData.kpi.ortalamaNetGetiriYuzde,
      trend: performanceData.kpi.ortalamaNetGetiriTrend,
      cardClass: "border-cyan-500/30 bg-gradient-to-br from-cyan-500/15 via-cyan-500/5 to-slate-950 text-cyan-50",
      icon:
        performanceData.kpi.ortalamaNetGetiriYuzde > 0 ? (
          <ArrowUpRight className="h-5 w-5" />
        ) : performanceData.kpi.ortalamaNetGetiriYuzde < 0 ? (
          <ArrowDownRight className="h-5 w-5" />
        ) : (
          <Minus className="h-5 w-5" />
        ),
      stroke: "#22d3ee",
      decimals: 1,
      formatValue: (value) => `${formatterPercent.format(value)}%`,
      valueClass: getReturnBadgeTone
    },
    {
      id: "net-pnl",
      label: "Toplam Net P&L",
      helper: "Tüm işlemlerden elde edilen toplam sonuç",
      info: "Negatif getiriler risk limitlerini gözden geçirmen gerektiğini gösterir.",
      target: performanceData.kpi.netKarZararUSD,
      trend: performanceData.kpi.netKarZararTrend,
      cardClass: "border-indigo-500/30 bg-gradient-to-br from-indigo-500/15 via-indigo-500/5 to-slate-950 text-indigo-50",
      icon:
        performanceData.kpi.netKarZararUSD > 0 ? (
          <ArrowUpRight className="h-5 w-5" />
        ) : performanceData.kpi.netKarZararUSD < 0 ? (
          <ArrowDownRight className="h-5 w-5" />
        ) : (
          <Minus className="h-5 w-5" />
        ),
      stroke: "#818cf8",
      decimals: 0,
      formatValue: (value) => formatterTL.format(value),
      valueClass: getReturnBadgeTone
    }
  ];

  const handleTypeToggle = (type: SinyalTipi) => () => {
    setSelectedTypes((prev) => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  const handleStatusToggle = (status: SinyalDurumu) => () => {
    setSelectedStatus((prev) => ({
      ...prev,
      [status]: !prev[status]
    }));
  };

  return (
    <section className="mx-auto w-full max-w-6xl space-y-8 rounded-3xl border border-slate-800 bg-slate-950/80 p-8 shadow-2xl shadow-pilot-primary/10 backdrop-blur">
      <header className="flex flex-col gap-4 text-slate-200 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-pilot-primary">FinPilot</p>
          <h2 className="text-3xl font-semibold">Performans &amp; Geçmiş</h2>
          <p className="max-w-xl text-sm text-slate-400">
            Sistemin nasıl çalıştığını net rakamlarla keşfet. KPI kutuları güven verir, geçmiş sinyal tablosu şeffaflığı destekler.
          </p>
        </div>
        <div className="flex flex-col items-start gap-2 text-left md:items-end md:text-right">
          <button
            type="button"
            onClick={handleShareClick}
            className="inline-flex items-center gap-2 rounded-full border border-pilot-primary/40 bg-pilot-primary/15 px-4 py-2 text-xs font-semibold text-pilot-primary-foreground transition hover:border-pilot-primary hover:bg-pilot-primary/25 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/60"
          >
            <Share2 className="h-4 w-4" />
            Performansı Paylaş
          </button>
          <p className="text-xs text-slate-500">
            Güncel veri kümesi: {performanceData.gecmisSinyaller.length} sinyal · {new Date().getFullYear()} yılı
          </p>
          {shareFeedback ? (
            <span className="text-[11px] font-semibold text-emerald-300" aria-live="polite">
              {shareFeedback}
            </span>
          ) : null}
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        {kpiCards.map((card) => (
          <KpiCard key={card.id} config={card} />
        ))}
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-100">Geçmiş Sinyaller</h3>
            <p className="text-sm text-slate-400">Filtreleri kullanarak istediğin dönem ve enstrümanların performansını incele.</p>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-4">
          <label className="space-y-2 text-sm text-slate-200">
            <span className="text-xs uppercase tracking-wide text-slate-400">Tarih Aralığı</span>
            <select
              value={dateRange}
              onChange={(event) => setDateRange(event.target.value as TarihAraligi)}
              className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-pilot-primary focus:ring-2 focus:ring-pilot-primary/40"
            >
              {DATE_RANGE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2 text-sm text-slate-200 md:col-span-2">
            <span className="text-xs uppercase tracking-wide text-slate-400">Sembol Ara</span>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                list="symbol-options"
                value={symbolQuery}
                onChange={(event) => setSymbolQuery(event.target.value)}
                placeholder="örn. AAPL, TSLA"
                className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2 pl-9 pr-3 text-sm outline-none focus:border-pilot-primary focus:ring-2 focus:ring-pilot-primary/40"
              />
              <datalist id="symbol-options">
                {uniqueSymbols.map((symbol) => (
                  <option key={symbol} value={symbol}>
                    {symbol}
                  </option>
                ))}
              </datalist>
            </div>
          </label>

          <div className="space-y-2 text-sm text-slate-200">
            <span className="text-xs uppercase tracking-wide text-slate-400">Sinyal Tipi</span>
            <div className="flex flex-wrap gap-2">
              {SIGNAL_TYPES.map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={handleTypeToggle(type)}
                  className={`rounded-full border px-3 py-1 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/60 ${
                    selectedTypes[type]
                      ? "border-pilot-primary bg-pilot-primary/20 text-pilot-primary-foreground"
                      : "border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-600 hover:text-slate-200"
                  }`}
                  aria-pressed={selectedTypes[type] ? "true" : "false"}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2 text-sm text-slate-200 md:col-span-4">
            <span className="text-xs uppercase tracking-wide text-slate-400">Sinyal Sonucu</span>
            <div className="flex flex-wrap gap-2">
              {STATUS_OPTIONS.map((status) => (
                <button
                  key={status}
                  type="button"
                  onClick={handleStatusToggle(status)}
                  className={`rounded-full px-3 py-1 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/60 ${
                    selectedStatus[status]
                      ? statusBadgeClasses[status]
                      : "border border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-600 hover:text-slate-200"
                  }`}
                  aria-pressed={selectedStatus[status] ? "true" : "false"}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 space-y-4">
          <div className="hidden overflow-hidden rounded-2xl border border-slate-800 md:block">
            <table className="min-w-full divide-y divide-slate-800 text-sm">
              <thead className="bg-slate-900/80 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3 text-left">Tarih</th>
                  <th className="px-4 py-3 text-left">Sembol</th>
                  <th className="px-4 py-3 text-left">Sinyal</th>
                  <th className="px-4 py-3 text-left">R/R Oranı</th>
                  <th className="px-4 py-3 text-left">Kapanış ($)</th>
                  <th className="px-4 py-3 text-left">Net Getiri %</th>
                  <th className="px-4 py-3 text-left">Durum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 bg-slate-950/40 text-slate-200">
                {filteredSignals.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-sm text-slate-500">
                      Bu filtreler için kayıt bulunamadı. Kriterleri genişleterek yeniden dene.
                    </td>
                  </tr>
                ) : (
                  filteredSignals.map((signal) => (
                    <tr
                      key={signal.id}
                      className="cursor-pointer transition-colors hover:bg-slate-900/60"
                      onClick={() => setActiveSignal(signal)}
                    >
                      <td className="px-4 py-3">{formatterDate.format(new Date(signal.tarih))}</td>
                      <td className="px-4 py-3 font-semibold">{signal.sembol}</td>
                      <td className="px-4 py-3">
                        <span className="rounded-full border border-slate-700 bg-slate-900/50 px-2 py-1 text-xs font-semibold text-slate-200">
                          {signal.sinyal}
                        </span>
                      </td>
                      <td className="px-4 py-3">{signal.rrOrani.toFixed(1)}</td>
                      <td className="px-4 py-3">{signal.kapanisFiyati.toFixed(2)}</td>
                      <td className={`px-4 py-3 font-semibold ${getNetResultClass(signal.netGetiriYuzdesi)}`}>
                        {formatterPercent.format(signal.netGetiriYuzdesi)}%
                      </td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2 py-1 text-xs font-semibold ${statusBadgeClasses[signal.durum]}`}>
                          {signal.durum}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="space-y-3 md:hidden">
            {filteredSignals.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-950/60 px-4 py-6 text-center text-sm text-slate-400">
                Bu filtreler için kayıt bulunamadı. Kriterleri genişleterek yeniden dene.
              </div>
            ) : (
              filteredSignals.map((signal) => (
                <button
                  key={signal.id}
                  type="button"
                  onClick={() => setActiveSignal(signal)}
                  className="w-full rounded-2xl border border-slate-800 bg-slate-950/70 p-4 text-left shadow-sm transition hover:border-pilot-primary/40 hover:bg-slate-900/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/60"
                  aria-label={`${signal.sembol} sinyali detayını aç`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-slate-500">
                        {formatterDate.format(new Date(signal.tarih))}
                      </p>
                      <p className="mt-1 text-lg font-semibold text-slate-100">{signal.sembol}</p>
                    </div>
                    <span className={`rounded-full px-2 py-1 text-[11px] font-semibold ${statusBadgeClasses[signal.durum]}`}>
                      {signal.durum}
                    </span>
                  </div>
                  <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-slate-300">
                    <span className="inline-flex items-center gap-1 rounded-full border border-slate-700 bg-slate-900/60 px-2.5 py-1 font-semibold text-slate-200">
                      {signal.sinyal}
                    </span>
                    <span className="inline-flex items-center gap-1 rounded-full bg-slate-900/80 px-2.5 py-1 font-semibold">
                      R/R {signal.rrOrani.toFixed(1)}
                    </span>
                    <span className="inline-flex items-center gap-1 rounded-full bg-slate-900/80 px-2.5 py-1 font-semibold">
                      ${signal.kapanisFiyati.toFixed(2)}
                    </span>
                  </div>
                  <div className="mt-4 flex items-center justify-between text-sm">
                    <p className="line-clamp-2 pr-4 text-slate-300">{signal.tldr}</p>
                    <span className={`text-base font-semibold ${getNetResultClass(signal.netGetiriYuzdesi)}`}>
                      {formatterPercent.format(signal.netGetiriYuzdesi)}%
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-inner shadow-pilot-primary/10">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-xl font-semibold text-slate-100">Pilot&apos;un Aksiyon Kontrol Listesi</h3>
            <p className="text-sm text-slate-400">
              Analiz sonrası hangi adımları atacağını saniyeler içinde hatırla. FinSense bu panelde seninle birlikte.
            </p>
          </div>
          {ctaTip?.baglanti ? (
            <a
              href={ctaTip.baglanti.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-pilot-primary/40 bg-pilot-primary/15 px-4 py-2 text-xs font-semibold text-pilot-primary-foreground transition-colors hover:border-pilot-primary hover:bg-pilot-primary/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/60"
            >
              <GraduationCap className="h-4 w-4" />
              {ctaTip.baglanti.etiket}
            </a>
          ) : null}
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <div className="space-y-6">
            {primaryTip ? (
              <article className="relative overflow-hidden rounded-3xl border border-emerald-500/30 bg-gradient-to-br from-emerald-500/20 via-emerald-500/5 to-slate-950 p-6 shadow-[0_20px_60px_-35px_rgba(16,185,129,0.8)]">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs uppercase tracking-wide text-emerald-300/80">Eylemsel Basitleştirme</span>
                    <h4 className="mt-2 text-2xl font-semibold text-emerald-100">{primaryTip.baslik}</h4>
                  </div>
                  <CheckCircle2 className="h-7 w-7 text-emerald-300" aria-hidden="true" />
                </div>
                <p
                  className="mt-4 text-sm leading-relaxed text-slate-100"
                  dangerouslySetInnerHTML={{ __html: highlightStrategySentence(primaryTip.icerik) }}
                />
                {primaryTip.baglanti ? (
                  <a
                    href={primaryTip.baglanti.url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-emerald-200/80 underline-offset-4 hover:underline"
                  >
                    FinSense · {primaryTip.baglanti.etiket}
                  </a>
                ) : null}
              </article>
            ) : null}

            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
              <h4 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-300">
                <HelpCircle className="h-4 w-4 text-pilot-primary" />
                Uçuş Öncesi Kontrol Listesi
              </h4>
              <ul className="mt-4 space-y-4">
                {checklistItems.map((item) => (
                  <li
                    key={item.id}
                    className="flex gap-3 rounded-2xl border border-slate-800/60 bg-slate-900/80 p-4 transition hover:border-emerald-400/40 hover:bg-slate-900"
                  >
                    <span className="mt-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-300">
                      <CheckCircle2 className="h-4 w-4" />
                    </span>
                    <div className="space-y-1 text-sm">
                      <p className="font-semibold text-slate-100">{item.icerik}</p>
                      {item.aciklama ? <p className="text-xs text-slate-400">{item.aciklama}</p> : null}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
              <h4 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-300">
                <Info className="h-4 w-4 text-pilot-primary" />
                Yardım &amp; İpuçları
              </h4>
              <ul className="mt-4 space-y-3">
                {infoTips.map((tip) => {
                  const icon = tip.tip === "AKSIYON_IPUCU" ? <Info className="h-4 w-4" /> : <HelpCircle className="h-4 w-4" />;
                  const shouldHighlight = needsRRReminder && tip.baslik.includes("R/R");
                  return (
                    <li
                      key={tip.baslik}
                      className={`group rounded-2xl border border-slate-800/60 bg-slate-950/60 p-4 transition hover:border-pilot-primary/30 hover:bg-slate-900/70 ${
                        shouldHighlight ? "ring-1 ring-emerald-400/40" : ""
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="mt-1 inline-flex h-7 w-7 items-center justify-center rounded-full bg-pilot-primary/10 text-pilot-primary-foreground">
                          {icon}
                        </span>
                        <div className="space-y-2 text-sm">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-semibold text-slate-100">{tip.baslik}</p>
                            {shouldHighlight ? (
                              <span className="rounded-full bg-emerald-500/25 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-100">
                                Şimdi kontrol et
                              </span>
                            ) : null}
                          </div>
                          <p className="text-xs leading-relaxed text-slate-400 group-hover:text-slate-200">{tip.icerik}</p>
                          {tip.baglanti ? (
                            <a
                              href={tip.baglanti.url}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-[11px] font-semibold text-pilot-primary underline-offset-4 hover:underline"
                            >
                              {tip.baglanti.etiket}
                            </a>
                          ) : null}
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>

            {ctaTip && !ctaTip.baglanti ? (
              <div className="rounded-2xl border border-pilot-primary/40 bg-pilot-primary/10 p-5 text-sm text-slate-100">
                <div className="flex items-start gap-3">
                  <GraduationCap className="h-5 w-5 text-pilot-primary" />
                  <div className="space-y-1">
                    <p className="font-semibold">{ctaTip.baslik}</p>
                    <p className="text-xs text-slate-200/80">{ctaTip.icerik}</p>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="mt-10">
        <TelegramCtaPanel />
      </div>

      {activeSignal ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 py-8">
          <div className="relative w-full max-w-xl rounded-3xl border border-slate-800 bg-slate-950 p-6 shadow-2xl">
            <button
              type="button"
              onClick={() => setActiveSignal(null)}
              className="absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-700 bg-slate-900 text-slate-400 transition-colors hover:border-slate-500 hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pilot-primary/60"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Detayı kapat</span>
            </button>
            <div className="space-y-5">
              <header>
                <p className="text-xs uppercase tracking-wide text-pilot-primary">Sinyal Özeti</p>
                <h4 className="mt-1 text-2xl font-semibold text-slate-100">
                  {activeSignal.sembol} · {formatterDate.format(new Date(activeSignal.tarih))}
                </h4>
                <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
                  <span className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 font-semibold text-slate-200">
                    {activeSignal.sinyal} Sinyali
                  </span>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusBadgeClasses[activeSignal.durum]}`}>
                    {activeSignal.durum}
                  </span>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${getNetResultClass(activeSignal.netGetiriYuzdesi)}`}>
                    Net {formatterPercent.format(activeSignal.netGetiriYuzdesi)}%
                  </span>
                </div>
              </header>
              <p className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 text-sm text-slate-200">{activeSignal.tldr}</p>
              <div className="space-y-2 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-400">
                  <span>Grafik Kesiti</span>
                  <span>RR: {activeSignal.rrOrani.toFixed(1)} · Kapanış: ${activeSignal.kapanisFiyati.toFixed(2)}</span>
                </div>
                <div className="h-40 rounded-xl border border-dashed border-slate-700 bg-slate-950/70 text-center text-xs uppercase tracking-wide text-slate-600">
                  <div className="flex h-full flex-col items-center justify-center gap-1">
                    <span>Mum grafiği burada gösterilecek</span>
                    <span className="text-[10px] text-slate-500">({activeSignal.grafikNotu ?? "Eğilim notu mevcut"})</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}