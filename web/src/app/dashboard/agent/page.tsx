"use client";

import { useState } from "react";
import {
  Network,
  Play,
  Loader2,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  BarChart3,
  FileText,
  Search,
  Zap,
  Globe,
  Settings,
  Activity,
  GitBranch,
  MessageSquare,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

/* ── Types ─────────────────────────────────────────────────── */
type Task = "scan" | "analyze" | "risk" | "full" | "auto" | "research" | "backtest" | "report"
         | "market_intel" | "optimize" | "monitor" | "combo" | "advisory";

interface AgentRunResponse {
  task: string;
  symbols_requested: number;
  scan_results: Record<string, any>;
  analysis_results: Record<string, any>;
  risk_results: Record<string, any>;
  research_results: Record<string, any>;
  backtest_results: Record<string, any>;
  synthesized_picks: Array<{
    symbol: string;
    composite_confidence: number;
    scan_score: number;
    llm_confidence: number;
    backtest_win_rate: number;
    signal: string;
    entry_ok: boolean;
    price: number | null;
    stop_loss: number | null;
    take_profit: number | null;
    risk_reward: number | null;
    news_count: number;
    has_llm_report: boolean;
  }>;
  market_intel: Record<string, any>;
  optimizer_results: Record<string, any>;
  monitor_results: Record<string, any>;
  combo_results: Record<string, any>;
  advisory_result: Record<string, any>;
  report: string;
  alerts_sent: string[];
  top_symbols: string[];
  errors: string[];
}

/* ── Constants ─────────────────────────────────────────────── */
const C = {
  bg: "#000000",
  card: "#111118",
  cardHover: "#1a1a24",
  border: "rgba(255,255,255,0.10)",
  text1: "#f5f5f7",
  text2: "#a1a1a6",
  text3: "#6e6e73",
  cyan: "#00d4ff",
  blue: "#0a84ff",
  green: "#30d158",
  red: "#ff453a",
  yellow: "#ffd60a",
  cyanBg: "rgba(0,212,255,0.10)",
  blueBg: "rgba(10,132,255,0.10)",
  greenBg: "rgba(48,209,88,0.10)",
};

const TASKS: { id: Task; label: string; desc: string; icon: React.ElementType }[] = [
  { id: "auto",         label: "🚀 Otomatik",      desc: "Tüm aşamalar: Scan → Araştır → Analiz → Risk → Backtest → Sentez", icon: Sparkles   },
  { id: "scan",         label: "Tarama",         desc: "Teknik sinyal analizi",                icon: Zap         },
  { id: "full",         label: "Tam Pipeline",    desc: "Scan + LLM + Risk + Alert",           icon: Network     },
  { id: "analyze",      label: "LLM Analiz",      desc: "Yapay zeka analizi",                  icon: Search      },
  { id: "risk",         label: "Risk",            desc: "Stop / TP hesapla",                  icon: BarChart3   },
  { id: "research",     label: "Haber Araştır",   desc: "DuckDuckGo haberleri",                icon: FileText    },
  { id: "backtest",     label: "Backtest",        desc: "Geçmiş performans",                    icon: TrendingUp  },
  { id: "report",       label: "Rapor",           desc: "Markdown günlük rapor",               icon: FileText    },
  { id: "market_intel", label: "Piyasa Rejimi",   desc: "Trend/volatilite rejim tespiti",     icon: Globe       },
  { id: "optimize",     label: "Optimizer",       desc: "Grid search parametre optimizasyonu", icon: Settings    },
  { id: "monitor",      label: "Performans",      desc: "Drawdown WARN/STOP izleme",          icon: Activity    },
  { id: "combo",        label: "Kombo Test",      desc: "Sembol × Strateji matrisi",          icon: GitBranch   },
  { id: "advisory",     label: "Danışman",        desc: "15 LLM uzman görüşü",               icon: MessageSquare },
];

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

/* ── Main Component ────────────────────────────────────────── */
export default function AgentPage() {
  const [task, setTask] = useState<Task>("scan");
  const [symbolsInput, setSymbolsInput] = useState("AAPL, MSFT");
  const [kellyFraction, setKellyFraction] = useState(0.5);
  const [advisoryKey, setAdvisoryKey] = useState("cto");
  const [advisoryQuestion, setAdvisoryQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentRunResponse | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    scan: true,
    analysis: true,
    risk: true,
    research: true,
    backtest: true,
    report: true,
  });

  const toggleSection = (key: string) =>
    setExpandedSections((p) => ({ ...p, [key]: !p[key] }));

  const handleRun = async () => {
    const symbols = symbolsInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (!symbols.length && task !== "advisory") {
      toast.error("En az bir sembol girin");
      return;
    }
    if (task === "advisory" && !advisoryQuestion.trim()) {
      toast.error("Soru girin");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const res = await fetch(`${API}/api/v1/agent/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task,
          symbols: task === "advisory" ? [] : symbols,
          kelly_fraction: kellyFraction,
          ...(task === "advisory" && { advisory_key: advisoryKey, question: advisoryQuestion }),
        }),
        signal: AbortSignal.timeout(300_000),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data: AgentRunResponse = await res.json();
      setResult(data);

      if (data.errors.length) {
        toast.warning(`${data.errors.length} hata oluştu`);
      } else {
        toast.success("Agent tamamlandı");
      }
    } catch (e: any) {
      toast.error(e.message || "Bağlantı hatası");
    } finally {
      setLoading(false);
    }
  };

  const scanCount     = result ? Object.keys(result.scan_results).length : 0;
  const analysisCount = result ? Object.keys(result.analysis_results).length : 0;
  const riskCount     = result ? Object.keys(result.risk_results).length : 0;
  const researchCount = result ? Object.keys(result.research_results).length : 0;
  const backtestCount = result ? Object.keys(result.backtest_results).length : 0;
  const synthesizedCount = result?.synthesized_picks?.length ?? 0;
  const marketIntelSymbols = result?.market_intel?.symbols ? Object.keys(result.market_intel.symbols) : [];
  const optimizerSymbols   = result ? Object.keys(result.optimizer_results) : [];
  const monitorSymbols     = result?.monitor_results?.symbols ? Object.keys(result.monitor_results.symbols) : [];
  const comboTested        = result?.combo_results?.total_tested ?? 0;

  return (
    <div style={{ color: C.text1, minHeight: "100vh" }}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <div
            className="rounded-xl p-2"
            style={{ background: C.cyanBg, border: `1px solid ${C.cyan}30` }}
          >
            <Network size={22} style={{ color: C.cyan }} />
          </div>
          <h1 className="text-2xl font-bold" style={{ color: C.text1 }}>
            AI Agent Sistemi
          </h1>
        </div>
        <p style={{ color: C.text2, fontSize: 14 }}>
          Çok-ajanlı pipeline — tarama, analiz, risk, haber ve backtest
        </p>
      </div>

      {/* Config Panel */}
      <div
        className="rounded-2xl p-5 mb-6"
        style={{ background: C.card, border: `1px solid ${C.border}` }}
      >
        {/* Task selector */}
        <div className="mb-4">
          <p className="text-xs font-semibold mb-2" style={{ color: C.text3 }}>
            GÖREV SEÇ
          </p>
          <div className="flex flex-wrap gap-2">
            {TASKS.map((t) => {
              const Icon = t.icon;
              const active = task === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setTask(t.id)}
                  className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition-all"
                  style={{
                    background: active ? C.cyanBg : C.cardHover,
                    border: `1px solid ${active ? C.cyan : C.border}`,
                    color: active ? C.cyan : C.text2,
                    fontWeight: active ? 600 : 400,
                  }}
                >
                  <Icon size={14} />
                  <span>{t.label}</span>
                </button>
              );
            })}
          </div>
          <p className="text-xs mt-1" style={{ color: C.text3 }}>
            {TASKS.find((t) => t.id === task)?.desc}
          </p>
        </div>

        {/* Symbols + Kelly (not needed for advisory) */}
        {task !== "advisory" && (
        <div className="flex flex-col gap-3 sm:flex-row">
          <div className="flex-1">
            <label className="text-xs font-semibold mb-1 block" style={{ color: C.text3 }}>
              SEMBOLLER (virgülle ayır)
            </label>
            <input
              value={symbolsInput}
              onChange={(e) => setSymbolsInput(e.target.value)}
              placeholder="THYAO.IS, KCHOL.IS, AAPL"
              className="w-full rounded-xl px-4 py-2.5 text-sm outline-none"
              style={{
                background: C.cardHover,
                border: `1px solid ${C.border}`,
                color: C.text1,
              }}
            />
          </div>
          <div style={{ minWidth: 160 }}>
            <label className="text-xs font-semibold mb-1 block" style={{ color: C.text3 }}>
              KELLY FRACTION: {kellyFraction.toFixed(2)}
            </label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={kellyFraction}
              onChange={(e) => setKellyFraction(Number(e.target.value))}
              className="w-full"
              style={{ accentColor: C.cyan }}
            />
          </div>
        </div>
        )}

        {/* Advisory inputs */}
        {task === "advisory" && (
        <div className="flex flex-col gap-3">
          <div>
            <label className="text-xs font-semibold mb-1 block" style={{ color: C.text3 }}>DANİŞMAN SEÇ</label>
            <select
              value={advisoryKey}
              onChange={(e) => setAdvisoryKey(e.target.value)}
              className="rounded-xl px-3 py-2.5 text-sm outline-none"
              style={{ background: C.cardHover, border: `1px solid ${C.border}`, color: C.text1 }}
            >
              {[
                ["cto","CTO — Mimari"],
                ["cpo","CPO — Ürün"],
                ["cmo","CMO — Pazarlama"],
                ["senior_dev","Senior Dev"],
                ["frontend_dev","Frontend Dev"],
                ["ai_ml_dev","AI/ML Dev"],
                ["devops","DevOps"],
                ["growth_marketer","Growth Marketer"],
                ["content_strategist","Content Strategist"],
                ["biz_dev","Business Dev"],
                ["competitive_intel","Competitive Intel"],
                ["qa_test","QA / Test"],
                ["code_review","Code Review"],
                ["pm","Project Manager"],
                ["customer_success","Customer Success"],
              ].map(([v,l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold mb-1 block" style={{ color: C.text3 }}>SORU</label>
            <textarea
              value={advisoryQuestion}
              onChange={(e) => setAdvisoryQuestion(e.target.value)}
              placeholder="Örnek: Docker mi Kubernetes mi? Redis için hangi strateji?"
              rows={3}
              className="w-full rounded-xl px-4 py-2.5 text-sm outline-none resize-none"
              style={{ background: C.cardHover, border: `1px solid ${C.border}`, color: C.text1 }}
            />
          </div>
        </div>
        )}

        {/* Run button */}
        <button
          onClick={handleRun}
          disabled={loading}
          className="mt-4 flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold transition-all"
          style={{
            background: loading ? C.cardHover : C.cyan,
            color: loading ? C.text3 : "#000",
            cursor: loading ? "not-allowed" : "pointer",
            border: "none",
          }}
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Çalışıyor...
            </>
          ) : (
            <>
              <Play size={16} />
              Çalıştır
            </>
          )}
        </button>
      </div>

      {/* Errors */}
      {result?.errors && result.errors.length > 0 && (
        <div
          className="rounded-2xl p-4 mb-4"
          style={{
            background: "rgba(255,69,58,0.08)",
            border: `1px solid rgba(255,69,58,0.3)`,
          }}
        >
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle size={16} style={{ color: C.red }} />
            <span className="text-sm font-semibold" style={{ color: C.red }}>
              Hatalar ({result.errors.length})
            </span>
          </div>
          {result.errors.map((e, i) => (
            <p key={i} className="text-xs" style={{ color: "#ff6b6b" }}>
              • {e}
            </p>
          ))}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="flex flex-col gap-4">
          {/* Synthesized Picks (Auto mode) */}
          {synthesizedCount > 0 && (
            <ResultSection
              title={`🚀 Sentezlenmiş Tahminler (${synthesizedCount} sembol)`}
              icon={<Sparkles size={15} style={{ color: C.yellow }} />}
              expanded={expandedSections.synthesized ?? true}
              onToggle={() => toggleSection("synthesized")}
            >
              <SynthesizedTable data={result.synthesized_picks} />
            </ResultSection>
          )}
          {scanCount > 0 && (
            <ResultSection
              title={`Tarama Sonuçları (${scanCount})`}
              icon={<Zap size={15} style={{ color: C.cyan }} />}
              expanded={expandedSections.scan}
              onToggle={() => toggleSection("scan")}
            >
              <ScanTable data={result.scan_results} />
            </ResultSection>
          )}

          {/* Analysis */}
          {analysisCount > 0 && (
            <ResultSection
              title={`LLM Analiz (${analysisCount})`}
              icon={<Search size={15} style={{ color: C.blue }} />}
              expanded={expandedSections.analysis}
              onToggle={() => toggleSection("analysis")}
            >
              {Object.entries(result.analysis_results).map(([sym, a]) => (
                <AnalysisCard key={sym} symbol={sym} data={a} />
              ))}
            </ResultSection>
          )}

          {/* Risk */}
          {riskCount > 0 && (
            <ResultSection
              title={`Risk Yönetimi (${riskCount})`}
              icon={<BarChart3 size={15} style={{ color: C.yellow }} />}
              expanded={expandedSections.risk}
              onToggle={() => toggleSection("risk")}
            >
              <RiskTable data={result.risk_results} />
            </ResultSection>
          )}

          {/* Research */}
          {researchCount > 0 && (
            <ResultSection
              title={`Haber Araştırma (${researchCount} sembol)`}
              icon={<FileText size={15} style={{ color: C.green }} />}
              expanded={expandedSections.research}
              onToggle={() => toggleSection("research")}
            >
              {Object.entries(result.research_results).map(([sym, items]) => (
                <NewsCard key={sym} symbol={sym} items={items as any[]} />
              ))}
            </ResultSection>
          )}

          {/* Backtest */}
          {backtestCount > 0 && (
            <ResultSection
              title={`Backtest Sonuçları (${backtestCount})`}
              icon={<TrendingUp size={15} style={{ color: C.cyan }} />}
              expanded={expandedSections.backtest}
              onToggle={() => toggleSection("backtest")}
            >
              <BacktestTable data={result.backtest_results} />
            </ResultSection>
          )}

          {/* Market Intel */}
          {marketIntelSymbols.length > 0 && (
            <ResultSection
              title={`Piyasa Rejimi (${marketIntelSymbols.length} sembol)`}
              icon={<Globe size={15} style={{ color: C.cyan }} />}
              expanded={expandedSections.market_intel ?? true}
              onToggle={() => toggleSection("market_intel")}
            >
              <MarketIntelTable data={result.market_intel} />
            </ResultSection>
          )}

          {/* Optimizer */}
          {optimizerSymbols.length > 0 && (
            <ResultSection
              title={`Optimizer Sonuçları (${optimizerSymbols.length} sembol)`}
              icon={<Settings size={15} style={{ color: C.yellow }} />}
              expanded={expandedSections.optimizer ?? true}
              onToggle={() => toggleSection("optimizer")}
            >
              <OptimizerTable data={result.optimizer_results} />
            </ResultSection>
          )}

          {/* Monitor */}
          {monitorSymbols.length > 0 && (
            <ResultSection
              title={`Performans İzleme (${monitorSymbols.length} sembol)`}
              icon={<ShieldAlert size={15} style={{ color: C.yellow }} />}
              expanded={expandedSections.monitor ?? true}
              onToggle={() => toggleSection("monitor")}
            >
              <MonitorTable data={result.monitor_results} />
            </ResultSection>
          )}

          {/* Combo */}
          {comboTested > 0 && (
            <ResultSection
              title={`Kombo Test (${comboTested} kombinasyon)`}
              icon={<GitBranch size={15} style={{ color: C.blue }} />}
              expanded={expandedSections.combo ?? true}
              onToggle={() => toggleSection("combo")}
            >
              <ComboTable data={result.combo_results} />
            </ResultSection>
          )}

          {/* Advisory */}
          {result.advisory_result?.role && (
            <ResultSection
              title={`Danışman: ${result.advisory_result.role}`}
              icon={<MessageSquare size={15} style={{ color: C.cyan }} />}
              expanded={expandedSections.advisory ?? true}
              onToggle={() => toggleSection("advisory")}
            >
              <AdvisoryCard data={result.advisory_result} />
            </ResultSection>
          )}

          {/* Report */}
          {result.report && (
            <ResultSection
              title="Günlük Rapor"
              icon={<FileText size={15} style={{ color: C.text2 }} />}
              expanded={expandedSections.report}
              onToggle={() => toggleSection("report")}
            >
              <pre
                className="text-xs whitespace-pre-wrap leading-relaxed overflow-auto max-h-[600px]"
                style={{ color: C.text2, fontFamily: "monospace" }}
              >
                {result.report}
              </pre>
            </ResultSection>
          )}

          {/* Alerts */}
          {result.alerts_sent.length > 0 && (
            <div
              className="rounded-2xl p-4"
              style={{ background: C.greenBg, border: `1px solid ${C.green}40` }}
            >
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle size={15} style={{ color: C.green }} />
                <span className="text-sm font-semibold" style={{ color: C.green }}>
                  Telegram Bildirimleri
                </span>
              </div>
              {result.alerts_sent.map((a, i) => (
                <p key={i} className="text-xs" style={{ color: C.text2 }}>
                  • {a}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Sub-components ────────────────────────────────────────── */

function ResultSection({
  title,
  icon,
  expanded,
  onToggle,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{ background: C.card, border: `1px solid ${C.border}` }}
    >
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-4"
        style={{ background: "transparent" }}
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-semibold" style={{ color: C.text1 }}>
            {title}
          </span>
        </div>
        {expanded ? (
          <ChevronUp size={16} style={{ color: C.text3 }} />
        ) : (
          <ChevronDown size={16} style={{ color: C.text3 }} />
        )}
      </button>
      {expanded && (
        <div className="px-5 pb-5" style={{ borderTop: `1px solid ${C.border}` }}>
          <div className="pt-4">{children}</div>
        </div>
      )}
    </div>
  );
}

function SynthesizedTable({ data }: { data: Array<{
  symbol: string; composite_confidence: number; scan_score: number;
  llm_confidence: number; backtest_win_rate: number; signal: string;
  entry_ok: boolean; price: number | null; stop_loss: number | null;
  take_profit: number | null; risk_reward: number | null;
  news_count: number; has_llm_report: boolean;
}> }) {
  const signalColor = (s: string) =>
    s === "BUY" ? C.green : s === "SELL" ? C.red : s === "CAUTION" ? C.yellow : C.cyan;
  return (
    <div className="overflow-auto">
      <table className="w-full text-xs" style={{ borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ color: C.text3 }}>
            {["Sembol","Güven %","Scan","LLM","Backtest WR","Sinyal","Entry","Fiyat","Stop","TP","R/R","Haber","Rapor"].map((h) => (
              <th key={h} className="text-left pb-2 pr-3 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((p) => (
            <tr key={p.symbol} style={{ borderTop: `1px solid ${C.border}` }}>
              <td className="py-2 pr-3 font-mono font-bold" style={{ color: C.cyan }}>{p.symbol}</td>
              <td className="py-2 pr-3">
                <div className="flex items-center gap-1.5">
                  <div className="relative h-2 w-16 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.08)" }}>
                    <div
                      className="absolute left-0 top-0 h-full rounded-full"
                      style={{
                        width: `${p.composite_confidence}%`,
                        background: p.composite_confidence >= 70 ? C.green : p.composite_confidence >= 50 ? C.cyan : C.yellow,
                      }}
                    />
                  </div>
                  <span style={{ color: p.composite_confidence >= 70 ? C.green : p.composite_confidence >= 50 ? C.cyan : C.yellow, fontWeight: 700 }}>
                    {p.composite_confidence}
                  </span>
                </div>
              </td>
              <td className="py-2 pr-3">{p.scan_score}</td>
              <td className="py-2 pr-3">{p.llm_confidence}</td>
              <td className="py-2 pr-3">{p.backtest_win_rate > 0 ? `${p.backtest_win_rate}%` : "—"}</td>
              <td className="py-2 pr-3">
                <span style={{ color: signalColor(p.signal), fontWeight: 700 }}>{p.signal}</span>
              </td>
              <td className="py-2 pr-3">{p.entry_ok ? "✅" : "❌"}</td>
              <td className="py-2 pr-3">{p.price != null ? Number(p.price).toFixed(2) : "—"}</td>
              <td className="py-2 pr-3" style={{ color: C.red }}>{p.stop_loss != null ? Number(p.stop_loss).toFixed(2) : "—"}</td>
              <td className="py-2 pr-3" style={{ color: C.green }}>{p.take_profit != null ? Number(p.take_profit).toFixed(2) : "—"}</td>
              <td className="py-2 pr-3">{p.risk_reward != null ? Number(p.risk_reward).toFixed(1) : "—"}</td>
              <td className="py-2 pr-3">{p.news_count > 0 ? `📰 ${p.news_count}` : "—"}</td>
              <td className="py-2 pr-3">{p.has_llm_report ? "✅" : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ScanTable({ data }: { data: Record<string, any> }) {
  const rows = Object.entries(data);
  return (
    <div className="overflow-auto">
      <table className="w-full text-xs" style={{ borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ color: C.text3 }}>
            {["Sembol", "Fiyat", "FP Skor", "Sinyal", "Entry", "R/R", "Stop", "TP"].map((h) => (
              <th key={h} className="text-left pb-2 pr-4 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(([sym, d]) => (
            <tr key={sym} style={{ borderTop: `1px solid ${C.border}` }}>
              <td className="py-2 pr-4 font-mono font-semibold" style={{ color: C.cyan }}>
                {sym}
              </td>
              <td className="py-2 pr-4">{Number(d.price).toFixed(2)}</td>
              <td className="py-2 pr-4">
                <span
                  className="rounded px-1.5 py-0.5 font-semibold"
                  style={{
                    background: d.finpilot_score >= 50 ? C.greenBg : C.blueBg,
                    color: d.finpilot_score >= 50 ? C.green : C.blue,
                  }}
                >
                  {d.finpilot_score ?? d.composite_score ?? "—"}
                </span>
              </td>
              <td className="py-2 pr-4" style={{ color: d.direction ? C.green : C.red }}>
                {d.direction ? "▲ AL" : "▼ SAT"}
              </td>
              <td className="py-2 pr-4">{d.entry_ok ? "✅" : "❌"}</td>
              <td className="py-2 pr-4">{Number(d.risk_reward).toFixed(1)}</td>
              <td className="py-2 pr-4">{Number(d.stop_loss).toFixed(2)}</td>
              <td className="py-2 pr-4">{Number(d.take_profit).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AnalysisCard({ symbol, data }: { symbol: string; data: any }) {
  const [expanded, setExpanded] = useState(false);
  const report: string = data.report || "";
  const preview = report.slice(0, 300);
  return (
    <div
      className="rounded-xl p-4 mb-3"
      style={{ background: C.cardHover, border: `1px solid ${C.border}` }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-sm" style={{ color: C.cyan }}>
          {symbol}
        </span>
        <span className="text-xs" style={{ color: C.text3 }}>
          via {data.provider} · {Number(data.latency_ms).toFixed(0)}ms
        </span>
      </div>
      <p className="text-xs leading-relaxed whitespace-pre-wrap" style={{ color: C.text2 }}>
        {expanded ? report : preview + (report.length > 300 ? "..." : "")}
      </p>
      {report.length > 300 && (
        <button
          onClick={() => setExpanded((p) => !p)}
          className="text-xs mt-2"
          style={{ color: C.cyan }}
        >
          {expanded ? "Daha az göster" : "Tamamını göster"}
        </button>
      )}
    </div>
  );
}

function RiskTable({ data }: { data: Record<string, any> }) {
  return (
    <div className="overflow-auto">
      <table className="w-full text-xs" style={{ borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ color: C.text3 }}>
            {["Sembol", "Stop", "TP1", "TP2", "R/R", "Strateji"].map((h) => (
              <th key={h} className="text-left pb-2 pr-4 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(data).map(([sym, r]) => (
            <tr key={sym} style={{ borderTop: `1px solid ${C.border}` }}>
              <td className="py-2 pr-4 font-mono font-semibold" style={{ color: C.cyan }}>
                {sym}
              </td>
              <td className="py-2 pr-4" style={{ color: C.red }}>
                {Number(r.stop_loss).toFixed(2)}
              </td>
              <td className="py-2 pr-4" style={{ color: C.green }}>
                {Number(r.tp1 ?? r.take_profit).toFixed(2)}
              </td>
              <td className="py-2 pr-4" style={{ color: C.green }}>
                {r.tp2 ? Number(r.tp2).toFixed(2) : "—"}
              </td>
              <td className="py-2 pr-4">{Number(r.risk_reward_ratio).toFixed(1)}</td>
              <td className="py-2 pr-4" style={{ color: C.text2 }}>
                {r.strategy_tag ?? "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NewsCard({ symbol, items }: { symbol: string; items: any[] }) {
  return (
    <div className="mb-4">
      <p className="text-sm font-semibold mb-2" style={{ color: C.cyan }}>
        {symbol}
      </p>
      {items.length === 0 ? (
        <p className="text-xs" style={{ color: C.text3 }}>
          Haber bulunamadı
        </p>
      ) : (
        items.map((item, i) => (
          <div
            key={i}
            className="rounded-xl p-3 mb-2"
            style={{ background: C.cardHover, border: `1px solid ${C.border}` }}
          >
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-semibold hover:underline"
              style={{ color: C.text1 }}
            >
              {item.title}
            </a>
            <p className="text-xs mt-1 leading-relaxed" style={{ color: C.text3 }}>
              {item.body}
            </p>
            <p className="text-xs mt-1" style={{ color: C.text3 }}>
              {item.source} · {item.date}
            </p>
          </div>
        ))
      )}
    </div>
  );
}

function BacktestTable({ data }: { data: Record<string, any> }) {
  return (
    <div className="overflow-auto">
      <table className="w-full text-xs" style={{ borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ color: C.text3 }}>
            {[
              "Sembol",
              "Strateji",
              "Getiri %",
              "Yıllık %",
              "Sharpe",
              "Max DD",
              "İşlem",
              "Win %",
            ].map((h) => (
              <th key={h} className="text-left pb-2 pr-4 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(data).map(([sym, r]) => (
            <tr key={sym} style={{ borderTop: `1px solid ${C.border}` }}>
              <td className="py-2 pr-4 font-mono font-semibold" style={{ color: C.cyan }}>
                {sym}
              </td>
              <td className="py-2 pr-4" style={{ color: C.text2 }}>
                {r.strategy_name}
              </td>
              <td
                className="py-2 pr-4 font-semibold"
                style={{ color: Number(r.total_return) >= 0 ? C.green : C.red }}
              >
                {Number(r.total_return).toFixed(1)}%
              </td>
              <td
                className="py-2 pr-4"
                style={{ color: Number(r.annual_return) >= 0 ? C.green : C.red }}
              >
                {Number(r.annual_return).toFixed(1)}%
              </td>
              <td className="py-2 pr-4">{Number(r.sharpe_ratio).toFixed(2)}</td>
              <td className="py-2 pr-4" style={{ color: C.red }}>
                {Number(r.max_drawdown).toFixed(1)}%
              </td>
              <td className="py-2 pr-4">{r.total_trades}</td>
              <td className="py-2 pr-4">{(Number(r.win_rate) * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MarketIntelTable({ data }: { data: Record<string, any> }) {
  const syms = data.symbols ?? {};
  const regimeColor = (r: string) => r === "bull" ? C.green : r === "bear" ? C.red : C.yellow;
  const volColor = (v: string) => v === "high" ? C.red : v === "medium" ? C.yellow : C.green;
  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-3">
        <span className="text-xs rounded-lg px-2 py-1" style={{ background: C.cardHover, color: C.text2 }}>
          Dominant: <b style={{ color: C.cyan }}>{data.dominant_regime?.toUpperCase()}</b>
        </span>
        <span className="text-xs rounded-lg px-2 py-1" style={{ background: C.cardHover, color: C.text2 }}>
          🐂 Bull: {data.bull_count} &nbsp;🐻 Bear: {data.bear_count} &nbsp;➡ Yatay: {data.sideways_count}
        </span>
        <span className="text-xs rounded-lg px-2 py-1" style={{ background: C.cardHover, color: C.text2 }}>
          Ort. Vol: %{Number(data.avg_ann_vol_pct ?? 0).toFixed(1)}
        </span>
      </div>
      <div className="overflow-auto">
        <table className="w-full text-xs" style={{ borderCollapse: "collapse" }}>
          <thead><tr style={{ color: C.text3 }}>
            {["Sembol","Trend","Volatilite","Kümülatif %","Yıllık Vol %","RSI","Skor"].map(h=>(
              <th key={h} className="text-left pb-2 pr-4 font-medium">{h}</th>
            ))}
          </tr></thead>
          <tbody>
            {Object.entries(syms).map(([sym, s]: [string, any]) => (
              <tr key={sym} style={{ borderTop: `1px solid ${C.border}` }}>
                <td className="py-2 pr-4 font-mono font-semibold" style={{ color: C.cyan }}>{sym}</td>
                <td className="py-2 pr-4" style={{ color: regimeColor(s.trend) }}>{s.trend}</td>
                <td className="py-2 pr-4" style={{ color: volColor(s.volatility) }}>{s.volatility}</td>
                <td className="py-2 pr-4" style={{ color: Number(s.cum_return_pct)>=0 ? C.green : C.red }}>
                  {Number(s.cum_return_pct).toFixed(1)}%
                </td>
                <td className="py-2 pr-4">{Number(s.ann_vol_pct).toFixed(1)}%</td>
                <td className="py-2 pr-4">{Number(s.rsi_14).toFixed(0)}</td>
                <td className="py-2 pr-4 font-semibold" style={{ color: C.cyan }}>{s.score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.llm_comment && (
        <p className="text-xs mt-3 leading-relaxed" style={{ color: C.text2 }}>{data.llm_comment}</p>
      )}
    </div>
  );
}

function OptimizerTable({ data }: { data: Record<string, any> }) {
  return (
    <div className="overflow-auto">
      <table className="w-full text-xs" style={{ borderCollapse: "collapse" }}>
        <thead><tr style={{ color: C.text3 }}>
          {["Sembol","Metod","Sharpe","Getiri %","İşlem","Win %","En İyi Params","Test Sayısı"].map(h=>(
            <th key={h} className="text-left pb-2 pr-4 font-medium">{h}</th>
          ))}
        </tr></thead>
        <tbody>
          {Object.entries(data).map(([sym, r]: [string, any]) => (
            <tr key={sym} style={{ borderTop: `1px solid ${C.border}` }}>
              <td className="py-2 pr-4 font-mono font-semibold" style={{ color: C.cyan }}>{sym}</td>
              <td className="py-2 pr-4" style={{ color: C.text2 }}>{r.method}</td>
              <td className="py-2 pr-4 font-semibold" style={{ color: Number(r.best_sharpe)>0 ? C.green : C.text2 }}>
                {Number(r.best_sharpe).toFixed(2)}
              </td>
              <td className="py-2 pr-4" style={{ color: Number(r.best_return_pct)>=0 ? C.green : C.red }}>
                {Number(r.best_return_pct).toFixed(1)}%
              </td>
              <td className="py-2 pr-4">{r.best_trades}</td>
              <td className="py-2 pr-4">{(Number(r.best_win_rate)*100).toFixed(0)}%</td>
              <td className="py-2 pr-4" style={{ color: C.text3, fontFamily: "monospace" }}>
                {r.best_params ? JSON.stringify(r.best_params) : "—"}
              </td>
              <td className="py-2 pr-4">{r.combos_tested}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MonitorTable({ data }: { data: Record<string, any> }) {
  const syms = data.symbols ?? {};
  const stColor = (s: string) => s === "STOP" ? C.red : s === "WARN" ? C.yellow : C.green;
  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-3">
        <span className="text-xs rounded-lg px-2 py-1 font-semibold"
          style={{ background: stColor(data.portfolio_status) + "20", color: stColor(data.portfolio_status) }}>
          Portfolio: {data.portfolio_status}
        </span>
        <span className="text-xs rounded-lg px-2 py-1" style={{ background: C.cardHover, color: C.text2 }}>
          WARN: {data.total_warnings} &nbsp; STOP: {data.total_stops}
        </span>
      </div>
      <div className="overflow-auto">
        <table className="w-full text-xs" style={{ borderCollapse: "collapse" }}>
          <thead><tr style={{ color: C.text3 }}>
            {["Sembol","Durum","Mevcut DD %","Max DD %","5G Perf %","Aksiyon"].map(h=>(
              <th key={h} className="text-left pb-2 pr-4 font-medium">{h}</th>
            ))}
          </tr></thead>
          <tbody>
            {Object.entries(syms).map(([sym, s]: [string, any]) => (
              <tr key={sym} style={{ borderTop: `1px solid ${C.border}` }}>
                <td className="py-2 pr-4 font-mono font-semibold" style={{ color: C.cyan }}>{sym}</td>
                <td className="py-2 pr-4 font-semibold" style={{ color: stColor(s.status) }}>{s.status}</td>
                <td className="py-2 pr-4" style={{ color: C.red }}>{Number(s.current_drawdown_pct).toFixed(1)}%</td>
                <td className="py-2 pr-4" style={{ color: C.red }}>{Number(s.max_drawdown_pct).toFixed(1)}%</td>
                <td className="py-2 pr-4" style={{ color: Number(s.perf_5d_pct)>=0 ? C.green : C.red }}>
                  {Number(s.perf_5d_pct).toFixed(1)}%
                </td>
                <td className="py-2 pr-4" style={{ color: C.text2 }}>{s.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ComboTable({ data }: { data: Record<string, any> }) {
  const top = data.top_combos ?? [];
  const matrix = data.matrix ?? {};
  return (
    <div>
      <p className="text-xs mb-3" style={{ color: C.text2 }}>{data.summary}</p>
      {top.length > 0 ? (
        <div>
          <p className="text-xs font-semibold mb-2" style={{ color: C.text3 }}>EN İYİ KOMBİNASYONLAR</p>
          <div className="overflow-auto">
            <table className="w-full text-xs" style={{ borderCollapse: "collapse" }}>
              <thead><tr style={{ color: C.text3 }}>
                {["#","Sembol","Strateji","Sharpe","Getiri %","DD %","İşlem","Win %"].map(h=>(
                  <th key={h} className="text-left pb-2 pr-4 font-medium">{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {top.map((c: any, i: number) => (
                  <tr key={i} style={{ borderTop: `1px solid ${C.border}` }}>
                    <td className="py-2 pr-4" style={{ color: C.text3 }}>{i+1}</td>
                    <td className="py-2 pr-4 font-mono font-semibold" style={{ color: C.cyan }}>{c.symbol}</td>
                    <td className="py-2 pr-4" style={{ color: C.text2 }}>{c.strategy}</td>
                    <td className="py-2 pr-4 font-semibold" style={{ color: Number(c.sharpe)>0 ? C.green : C.text2 }}>
                      {Number(c.sharpe).toFixed(2)}
                    </td>
                    <td className="py-2 pr-4" style={{ color: Number(c.total_return_pct)>=0 ? C.green : C.red }}>
                      {Number(c.total_return_pct).toFixed(1)}%
                    </td>
                    <td className="py-2 pr-4" style={{ color: C.red }}>{Number(c.max_drawdown_pct).toFixed(1)}%</td>
                    <td className="py-2 pr-4">{c.total_trades}</td>
                    <td className="py-2 pr-4">{(Number(c.win_rate)*100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          <p className="text-xs" style={{ color: C.text3 }}>Min işlem eşiği geçen kombinasyon yok. Tüm sonuçlar:</p>
          {Object.entries(matrix).map(([sym, strategies]: [string, any]) => (
            <div key={sym} className="rounded-xl p-3" style={{ background: C.cardHover, border: `1px solid ${C.border}` }}>
              <p className="text-xs font-semibold mb-1" style={{ color: C.cyan }}>{sym}</p>
              <div className="flex flex-wrap gap-3">
                {Object.entries(strategies).map(([strat, r]: [string, any]) => (
                  <span key={strat} className="text-xs" style={{ color: C.text2 }}>
                    {strat}: {r.total_trades} işlem / Sharpe {Number(r.sharpe).toFixed(2)}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AdvisoryCard({ data }: { data: Record<string, any> }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold rounded-lg px-2 py-1"
          style={{ background: "rgba(0,212,255,0.10)", color: C.cyan }}>
          {data.role}
        </span>
        <span className="text-xs" style={{ color: C.text3 }}>
          {data.provider} · {Number(data.latency_ms ?? 0).toFixed(0)}ms
        </span>
      </div>
      {data.question && (
        <p className="text-xs mb-3 italic" style={{ color: C.text3 }}>"{data.question}"</p>
      )}
      <p className="text-xs leading-relaxed whitespace-pre-wrap" style={{ color: C.text2 }}>
        {data.advice}
      </p>
    </div>
  );
}
