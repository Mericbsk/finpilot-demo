"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import Fuse from "fuse.js";
import {
  GraduationCap,
  BookOpen,
  HelpCircle,
  Compass,
  Calculator,
  Search,
  CheckCircle,
  XCircle,
  Globe,
  Bookmark,
  BookmarkCheck,
  ChevronRight,
  Zap,
  Star,
} from "lucide-react";
import { C } from "@/lib/stockData";

/* ── Extend C with purple for FinSense ────────────────────── */
const purple = "#a78bfa";

/* ── Category merge (UI level, no JSON change) ─────────────── */
const CATEGORY_MERGE: Record<string, string> = {
  "Bankacılık": "Bankacılık ve Finans",
  "Bankacılık ve Kredi": "Bankacılık ve Finans",
  "Portföy Teorisi": "Yatırım ve Portföy",
  "Yatırım Araçları": "Yatırım ve Portföy",
  "Yatırım ve Varlık Yönetimi": "Yatırım ve Portföy",
  "Psikoloji": "Davranışsal Finans",
  "Girişimcilik": "Davranışsal Finans",
  "Emeklilik ve Sigorta": "Kişisel Finans",
  "Kredi ve Borç Yönetimi": "Kişisel Finans",
};

function normalizeCategory(cat: string): string {
  return CATEGORY_MERGE[cat] ?? cat;
}

/* ── Learning paths ────────────────────────────────────────── */
const LEARNING_PATHS = [
  { id: "baslangic-101", title: "Yatırıma Başlangıç", icon: "🌱", color: C.green, level: "Başlangıç", duration: "15 dk", termCount: 6, category: "Temel Finans Kavramları" },
  { id: "teknik-analiz-101", title: "Teknik Analiz Temelleri", icon: "📊", color: C.cyan, level: "Orta", duration: "20 dk", termCount: 8, category: "Teknik Analiz" },
  { id: "risk-yonetimi", title: "Risk Yönetimi", icon: "🛡️", color: C.yellow, level: "Orta", duration: "18 dk", termCount: 7, category: "Risk Yönetimi" },
  { id: "portfoy-teorisi", title: "Portföy Teorisi", icon: "🎯", color: purple, level: "İleri", duration: "25 dk", termCount: 7, category: "Yatırım ve Portföy" },
  { id: "turev-araclar", title: "Türev Araçlar 101", icon: "⚡", color: C.red, level: "İleri", duration: "22 dk", termCount: 6, category: "Türev Araçlar" },
  { id: "makro-101", title: "Makroekonomiye Giriş", icon: "🌍", color: C.blue, level: "Başlangıç", duration: "20 dk", termCount: 6, category: "Makroekonomi" },
];

/* ── Type for dictionary entry ────────────────────────────── */
interface DictEntry {
  slug: string;
  term: string;
  term_en?: string;
  term_de?: string;
  definition: string;
  definition_en?: string;
  definition_de?: string;
  example?: string;
  example_en?: string;
  category: string;
  level: string;
  related?: string[];
  formula?: string;
  tags?: string[];
  synonyms?: string[];
  source?: string;
  difficulty_score?: number;
  simple_explanation?: string;
  why_important?: string;
  common_mistake?: string;
  finpilot_usage?: string[];
}

/* ── Level color map ──────────────────────────────────────── */
function levelColor(level: string): { color: string; bg: string } {
  const l = level.toLowerCase();
  if (l.includes("başlangıç")) return { color: C.green, bg: "rgba(48,209,88,0.1)" };
  if (l.includes("orta")) return { color: C.cyan, bg: "rgba(0,212,255,0.1)" };
  if (l.includes("ileri")) return { color: C.yellow, bg: "rgba(255,214,10,0.1)" };
  if (l.includes("uzman")) return { color: purple, bg: "rgba(167,139,250,0.1)" };
  return { color: C.text3, bg: "rgba(255,255,255,0.05)" };
}

/* ── Category icon map ────────────────────────────────────── */
function catIcon(cat: string): string {
  const m: Record<string, string> = {
    "Temel Finans Kavramları": "💰", "Teknik Analiz": "📊", "Temel Analiz": "📈",
    "Piyasa İşleyişi": "🏛️", "Yatırım ve Portföy": "🎯", "Makroekonomi": "🌍",
    "İleri Düzey Kavramlar": "🧠", "Kişisel Finans": "💳", "Dijital Finans": "🔗",
    "Davranışsal Finans": "🧘", "Bankacılık ve Finans": "🏦",
    "Türev Araçlar": "⚡", "Risk Yönetimi": "🛡️",
    // legacy keys still in some JSON entries
    "Yatırım ve Varlık Yönetimi": "🎯", "Portföy Teorisi": "🎯",
    "Yatırım Araçları": "🎯", "Bankacılık": "🏦", "Bankacılık ve Kredi": "🏦",
    "Psikoloji": "🧘", "Girişimcilik": "🚀", "Emeklilik ve Sigorta": "🛡️",
    "Kredi ve Borç Yönetimi": "💳",
  };
  return m[cat] || "📚";
}

/* ── Tabs ──────────────────────────────────────────────────── */
const TABS = [
  { id: "Keşfet", icon: Star },
  { id: "Sözlük", icon: BookOpen },
  { id: "Quiz", icon: HelpCircle },
  { id: "Stratejiler", icon: Compass },
  { id: "Hesapla", icon: Calculator },
];

const PAGE_SIZE = 30;

/* ── Strategy data ─────────────────────────────────────────── */
const strategies = [
  {
    name: "Momentum Yatırımı", icon: "🚀",
    description: "Yükselen hisseler yükselmeye devam eder, düşenler düşmeye devam eder varsayımına dayanır.",
    howItWorks: "Son 3-6-12 ay performansı en iyi hisseleri al. Momentum zayıfladığında (RSI sapma, MACD bearish cross) sat.",
    connection: "FinPilot'un scanner'ı RSI, Moving Average ve Z-Score kullanarak yüksek momentum hisseleri gerçek zamanlı tespit eder.",
    relatedSlugs: ["goreceli-guc-endeksi", "macd", "z-score"],
  },
  {
    name: "Ortalamaya Dönüş", icon: "🔄",
    description: "Fiyatlar aşırı hareketlerden sonra tarihsel ortalamasına döner. Aşırı satımda al, aşırı alımda sat.",
    howItWorks: "Ortalamadan anlamlı sapma gösteren hisseleri tespit et (Z-Score, Bollinger Bands). Dönüş sinyali geldiğinde gir.",
    connection: "FinPilot'un Z-Score ve Bollinger Band takibi ortalamaya dönüş fırsatlarını otomatik işaretler.",
    relatedSlugs: ["z-score", "bollinger-bantlari", "goreceli-guc-endeksi"],
  },
  {
    name: "Trend Takibi", icon: "📈",
    description: "Mevcut piyasa trendinin yönünde işlem yap. Trende karşı işlem yapma.",
    howItWorks: "Fiyat SMA200 üstündeyken al (uptrend). Altına düştüğünde sat/nakit kal. Regime detection ile doğrula.",
    connection: "FinPilot'un Regime Detection modülü piyasaları otomatik Trend/Volatile/Range olarak sınıflar.",
    relatedSlugs: ["moving-average", "trend", "support"],
  },
  {
    name: "DRL Agent Stratejisi", icon: "🤖",
    description: "Deep Reinforcement Learning ajanları piyasa rejimlerine göre adaptif strateji uygular.",
    howItWorks: "PPO/SAC/TD3 ajanları trend, volatil ve range rejimlerinde farklı stratejiler uygular. Ensemble voting ile konsensüs sağlanır.",
    connection: "FinPilot AI Lab'daki 3 DRL ajanı her hisse için bağımsız oylama yapar, %87+ doğruluk oranıyla.",
    relatedSlugs: [],
  },
  {
    name: "Değer Yatırımı", icon: "💎",
    description: "İçsel değerinin altında işlem gören hisselere uzun vadeli yatırım. Warren Buffett yaklaşımı.",
    howItWorks: "Düşük P/E, yüksek marjin, güçlü bilanço. Fundamental analiz ile undervalued hisseleri tespit et.",
    connection: "FinPilot Analysis sayfasında Fundamental tab'ında P/E, Debt/Equity, Revenue Growth metrikleri gösterilir.",
    relatedSlugs: [],
  },
];

/* ═══════════════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════════════ */
export default function FinSensePage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("Keşfet");
  const [allTerms, setAllTerms] = useState<DictEntry[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("Tümü");
  const [selectedLevel, setSelectedLevel] = useState("Tümü");
  const [lang, setLang] = useState<"tr" | "en">("tr");
  const [hoverCard, setHoverCard] = useState<string | null>(null);
  const [saved, setSaved] = useState<string[]>([]);
  const [page, setPage] = useState(1);

  /* Quiz state */
  const [quizLevel, setQuizLevel] = useState("Tümü");
  const [quizIndex, setQuizIndex] = useState(0);
  const [quizScore, setQuizScore] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [quizDone, setQuizDone] = useState(false);
  const [quizQuestions, setQuizQuestions] = useState<
    { question: string; options: string[]; answer: number; type: "def2term" | "term2def" }[]
  >([]);

  /* Calculator state */
  const [initial, setInitial] = useState(10000);
  const [monthly, setMonthly] = useState(1000);
  const [rate, setRate] = useState(10);
  const [years, setYears] = useState(10);

  /* Load dictionary + saved */
  useEffect(() => {
    fetch("/dictionary.json")
      .then((r) => r.json())
      .then((data: DictEntry[]) => setAllTerms(data))
      .catch(() => {});
    const s = JSON.parse(localStorage.getItem("finsense_saved") || "[]");
    setSaved(s);
  }, []);

  /* Fuse instance */
  const fuse = useMemo(
    () =>
      new Fuse(allTerms, {
        keys: [
          { name: "term", weight: 2 },
          { name: "term_en", weight: 1.5 },
          { name: "slug", weight: 1.5 },
          { name: "synonyms", weight: 1.2 },
          { name: "tags", weight: 1 },
          { name: "definition", weight: 0.8 },
          { name: "definition_en", weight: 0.6 },
        ],
        threshold: 0.35,
        includeScore: true,
      }),
    [allTerms]
  );

  /* Merged category list */
  const mergedCategories = useMemo(() => {
    const cats = Array.from(new Set(allTerms.map((t) => normalizeCategory(t.category)))).sort();
    return ["Tümü", ...cats];
  }, [allTerms]);

  /* Levels */
  const levels = useMemo(() => {
    const lvls = Array.from(new Set(allTerms.map((t) => t.level))).sort();
    return ["Tümü", ...lvls];
  }, [allTerms]);

  /* Category term counts (normalized) */
  const catCounts = useMemo(() => {
    const m: Record<string, number> = {};
    for (const t of allTerms) {
      const cat = normalizeCategory(t.category);
      m[cat] = (m[cat] || 0) + 1;
    }
    return m;
  }, [allTerms]);

  /* Filtered + fuse searched terms */
  const filteredTerms = useMemo(() => {
    let results: DictEntry[] = searchTerm.trim()
      ? fuse.search(searchTerm).map((r) => r.item)
      : allTerms;
    if (selectedCategory !== "Tümü") {
      results = results.filter((t) => normalizeCategory(t.category) === selectedCategory);
    }
    if (selectedLevel !== "Tümü") {
      results = results.filter((t) => t.level === selectedLevel);
    }
    return results;
  }, [fuse, allTerms, searchTerm, selectedCategory, selectedLevel]);

  const displayedTerms = useMemo(() => filteredTerms.slice(0, page * PAGE_SIZE), [filteredTerms, page]);

  /* Featured beginner terms */
  const featuredTerms = useMemo(() => {
    return allTerms
      .filter((t) => t.level.includes("Başlangıç") || (t.difficulty_score !== undefined && t.difficulty_score <= 3))
      .sort((a, b) => (a.difficulty_score ?? 5) - (b.difficulty_score ?? 5))
      .slice(0, 6);
  }, [allTerms]);

  /* Save toggle */
  function toggleSave(slug: string) {
    const next = saved.includes(slug) ? saved.filter((s) => s !== slug) : [...saved, slug];
    setSaved(next);
    localStorage.setItem("finsense_saved", JSON.stringify(next));
  }

  /* Navigate to term detail */
  function openTerm(t: DictEntry) {
    router.push(`/dashboard/finsense/${t.slug || encodeURIComponent(t.term)}`);
  }

  /* Generate quiz */
  function generateQuiz(level: string) {
    const pool = allTerms.filter((t) => level === "Tümü" || t.level === level);
    if (pool.length < 4) return;
    const shuffled = [...pool].sort(() => Math.random() - 0.5).slice(0, 10);
    const qs = shuffled.map((entry) => {
      const useType: "def2term" | "term2def" = Math.random() > 0.5 ? "def2term" : "term2def";
      const correctDef = lang === "en" && entry.definition_en ? entry.definition_en : entry.definition;
      const shortDef = correctDef.length > 90 ? correctDef.slice(0, 90) + "…" : correctDef;
      const termName = lang === "en" && entry.term_en ? entry.term_en : entry.term;
      const wrongTerms = allTerms
        .filter((t) => t.term !== entry.term && (level === "Tümü" || t.level === level))
        .sort(() => Math.random() - 0.5)
        .slice(0, 3);
      const answerIdx = Math.floor(Math.random() * 4);
      let question: string;
      let options: string[];
      if (useType === "def2term") {
        question = `Bu tanım hangi kavrama aittir?\n"${shortDef}"`;
        const wrongOpts = wrongTerms.map((t) => lang === "en" && t.term_en ? t.term_en : t.term);
        options = [...wrongOpts];
        options.splice(answerIdx, 0, termName);
      } else {
        question = `"${termName}" nedir?`;
        const wrongOpts = wrongTerms.map((t) => {
          const d = lang === "en" && t.definition_en ? t.definition_en : t.definition;
          return d.length > 90 ? d.slice(0, 90) + "…" : d;
        });
        options = [...wrongOpts];
        options.splice(answerIdx, 0, shortDef);
      }
      return { question, options, answer: answerIdx, type: useType };
    });
    setQuizQuestions(qs);
    setQuizIndex(0);
    setQuizScore(0);
    setSelectedAnswer(null);
    setQuizDone(false);
  }

  useEffect(() => {
    if (allTerms.length > 10) generateQuiz(quizLevel);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allTerms, quizLevel, lang]);

  function handleQuizAnswer(idx: number) {
    if (selectedAnswer !== null) return;
    setSelectedAnswer(idx);
    if (idx === quizQuestions[quizIndex].answer) setQuizScore((s) => s + 1);
    setTimeout(() => {
      if (quizIndex < quizQuestions.length - 1) {
        setQuizIndex((i) => i + 1);
        setSelectedAnswer(null);
      } else {
        setQuizDone(true);
      }
    }, 1200);
  }

  /* Calculator */
  const monthlyRate = rate / 100 / 12;
  const totalMonths = years * 12;
  const futureValue =
    initial * (1 + monthlyRate) ** totalMonths +
    monthly * (((1 + monthlyRate) ** totalMonths - 1) / monthlyRate);
  const totalInvested = initial + monthly * totalMonths;
  const totalInterest = futureValue - totalInvested;

  const inputStyle: React.CSSProperties = {
    width: "100%", borderRadius: 8, border: `1px solid ${C.border}`,
    backgroundColor: C.primary, padding: "8px 12px", fontSize: 13, color: C.text1, outline: "none",
  };

  /* Shared search bar */
  function renderSearchBar(placeholder?: string) {
    return (
      <div style={{ position: "relative" }}>
        <Search size={14} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: C.text3, pointerEvents: "none" }} />
        <input
          type="text"
          placeholder={placeholder ?? `${allTerms.length} terimde ara...`}
          value={searchTerm}
          onChange={(e) => { setSearchTerm(e.target.value); if (activeTab === "Keşfet") setActiveTab("Sözlük"); setPage(1); }}
          style={{ ...inputStyle, paddingLeft: 40, borderRadius: 14, backgroundColor: C.card, fontSize: 14 }}
        />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 16px" }}>
      {/* ── Header ──────────────────────────────────────── */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <GraduationCap size={20} style={{ color: purple }} />
            <h1 style={{ fontSize: 20, fontWeight: 600, color: C.text1 }}>FinSense Academy</h1>
            <span style={{ fontSize: 11, color: C.text3, marginLeft: 8 }}>
              {allTerms.length} terim · {mergedCategories.length - 1} kategori · 3 dil
            </span>
            {saved.length > 0 && (
              <span style={{ borderRadius: 10, backgroundColor: "rgba(255,214,10,0.1)", padding: "2px 8px", fontSize: 10, color: C.yellow }}>
                <Bookmark size={9} style={{ display: "inline", marginRight: 3 }} />{saved.length} kaydedildi
              </span>
            )}
          </div>
          <button
            onClick={() => setLang(lang === "tr" ? "en" : "tr")}
            style={{ display: "flex", alignItems: "center", gap: 6, borderRadius: 8, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: "6px 12px", fontSize: 11, fontWeight: 600, color: C.cyan, cursor: "pointer" }}
          >
            <Globe size={12} />
            {lang === "tr" ? "TR 🇹🇷" : "EN 🇺🇸"}
          </button>
        </div>
      </div>

      {/* ── Tab bar ───────────────────────────────────────── */}
      <div style={{ display: "flex", gap: 4, borderRadius: 12, backgroundColor: C.card, padding: 4, marginBottom: 24 }}>
        {TABS.map(({ id, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            style={{
              flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
              gap: 6, borderRadius: 8, padding: "8px 6px", fontSize: 12, fontWeight: 500,
              border: "none", cursor: "pointer", transition: "all 0.2s",
              backgroundColor: activeTab === id ? (id === "Keşfet" ? "rgba(167,139,250,0.15)" : C.primary) : "transparent",
              color: activeTab === id ? (id === "Keşfet" ? purple : C.text1) : C.text3,
            }}
          >
            <Icon size={13} />
            {id}
          </button>
        ))}
      </div>

      {/* ══════════════════════════════════════════════════════
          TAB: KEŞFEt
          ══════════════════════════════════════════════════════ */}
      {activeTab === "Keşfet" && (
        <div>
          {/* Hero search */}
          <div style={{ textAlign: "center", padding: "32px 0 24px" }}>
            <div style={{ fontSize: 36, marginBottom: 8 }}>📚</div>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: C.text1, marginBottom: 6 }}>Ne öğrenmek istiyorsunuz?</h2>
            <p style={{ fontSize: 13, color: C.text3, marginBottom: 20 }}>{allTerms.length} finansal kavram — Türkçe, İngilizce ve Almanca</p>
            <div style={{ maxWidth: 560, margin: "0 auto" }}>
              {renderSearchBar("RSI, Bollinger, Faiz, P/E oranı...")}
            </div>
          </div>

          {/* Learning paths */}
          <div style={{ marginBottom: 32 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, color: C.text3, marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Öğrenme Yolları
            </h3>
            <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))" }}>
              {LEARNING_PATHS.map((path) => {
                const lc = levelColor(path.level);
                return (
                  <button
                    key={path.id}
                    onClick={() => { setSelectedCategory(path.category); setActiveTab("Sözlük"); }}
                    style={{
                      borderRadius: 14, padding: "16px 18px",
                      border: `1px solid ${hoverCard === path.id ? path.color + "40" : C.border}`,
                      backgroundColor: hoverCard === path.id ? path.color + "08" : C.card,
                      cursor: "pointer", textAlign: "left", transition: "all 0.2s",
                    }}
                    onMouseEnter={() => setHoverCard(path.id)}
                    onMouseLeave={() => setHoverCard(null)}
                  >
                    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
                      <span style={{ fontSize: 24 }}>{path.icon}</span>
                      <ChevronRight size={14} style={{ color: C.text3, marginTop: 4 }} />
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: C.text1, marginTop: 8, marginBottom: 4 }}>{path.title}</div>
                    <div style={{ display: "flex", gap: 6 }}>
                      <span style={{ borderRadius: 6, backgroundColor: lc.bg, padding: "2px 6px", fontSize: 9, color: lc.color }}>{path.level}</span>
                      <span style={{ borderRadius: 6, backgroundColor: C.primary, padding: "2px 6px", fontSize: 9, color: C.text3 }}>⏱ {path.duration}</span>
                      <span style={{ borderRadius: 6, backgroundColor: C.primary, padding: "2px 6px", fontSize: 9, color: C.text3 }}>{path.termCount} terim</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Category quick-access */}
          <div style={{ marginBottom: 32 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, color: C.text3, marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Kategoriler
            </h3>
            <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))" }}>
              {mergedCategories.filter((c) => c !== "Tümü").map((cat) => (
                <button
                  key={cat}
                  onClick={() => { setSelectedCategory(cat); setActiveTab("Sözlük"); }}
                  style={{
                    borderRadius: 12, padding: "12px 14px",
                    border: `1px solid ${hoverCard === cat ? C.borderHover : C.border}`,
                    backgroundColor: hoverCard === cat ? C.cardHover : C.card,
                    cursor: "pointer", textAlign: "left", transition: "all 0.15s",
                  }}
                  onMouseEnter={() => setHoverCard(cat)}
                  onMouseLeave={() => setHoverCard(null)}
                >
                  <div style={{ fontSize: 18, marginBottom: 4 }}>{catIcon(cat)}</div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: C.text1, marginBottom: 2 }}>{cat}</div>
                  <div style={{ fontSize: 10, color: C.text3 }}>{catCounts[cat] || 0} terim</div>
                </button>
              ))}
            </div>
          </div>

          {/* Featured beginner terms */}
          {featuredTerms.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <h3 style={{ fontSize: 13, fontWeight: 600, color: C.text3, marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                Başlangıç için Önerilen Kavramlar
              </h3>
              <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))" }}>
                {featuredTerms.map((t) => {
                  const lc = levelColor(t.level);
                  const name = lang === "en" && t.term_en ? t.term_en : t.term;
                  return (
                    <button
                      key={t.slug}
                      onClick={() => openTerm(t)}
                      style={{
                        borderRadius: 12, padding: "12px 14px",
                        border: `1px solid ${hoverCard === "ft-" + t.slug ? C.borderHover : C.border}`,
                        backgroundColor: hoverCard === "ft-" + t.slug ? C.cardHover : C.card,
                        cursor: "pointer", textAlign: "left", transition: "all 0.15s",
                      }}
                      onMouseEnter={() => setHoverCard("ft-" + t.slug)}
                      onMouseLeave={() => setHoverCard(null)}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: C.text1 }}>{name.split("(")[0].trim()}</span>
                        <span style={{ borderRadius: 6, backgroundColor: lc.bg, padding: "1px 5px", fontSize: 9, color: lc.color }}>{t.level}</span>
                      </div>
                      <p style={{ fontSize: 11, color: C.text3, lineHeight: 1.5 }}>
                        {t.definition.slice(0, 70)}{t.definition.length > 70 ? "…" : ""}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════
          TAB: SÖZLÜK
          ══════════════════════════════════════════════════════ */}
      {activeTab === "Sözlük" && (
        <div>
          {/* Search + filters */}
          <div style={{ display: "flex", gap: 10, marginBottom: 14, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              {renderSearchBar()}
            </div>
            <select
              value={selectedCategory}
              onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
              style={{ ...inputStyle, width: "auto", minWidth: 180, borderRadius: 12, backgroundColor: C.card }}
            >
              {mergedCategories.map((c) => (
                <option key={c} value={c} style={{ backgroundColor: "#111", color: C.text1 }}>
                  {c === "Tümü" ? "📚 Tüm Kategoriler" : `${catIcon(c)} ${c}`}
                </option>
              ))}
            </select>
            <select
              value={selectedLevel}
              onChange={(e) => { setSelectedLevel(e.target.value); setPage(1); }}
              style={{ ...inputStyle, width: "auto", minWidth: 140, borderRadius: 12, backgroundColor: C.card }}
            >
              {levels.map((l) => (
                <option key={l} value={l} style={{ backgroundColor: "#111", color: C.text1 }}>
                  {l === "Tümü" ? "🎓 Tüm Seviyeler" : l}
                </option>
              ))}
            </select>
          </div>

          {/* Results count + reset */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <p style={{ fontSize: 11, color: C.text3 }}>
              {filteredTerms.length} / {allTerms.length} terim
              {searchTerm && <> · <span style={{ color: C.cyan }}>&quot;{searchTerm}&quot;</span></>}
            </p>
            {(searchTerm || selectedCategory !== "Tümü" || selectedLevel !== "Tümü") && (
              <button
                onClick={() => { setSearchTerm(""); setSelectedCategory("Tümü"); setSelectedLevel("Tümü"); setPage(1); }}
                style={{ fontSize: 11, color: C.text3, background: "none", border: "none", cursor: "pointer" }}
              >
                Filtreleri temizle ×
              </button>
            )}
          </div>

          {/* Term cards — responsive grid */}
          <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))" }}>
            {displayedTerms.map((t) => {
              const lc = levelColor(t.level);
              const termDisplay = lang === "en" && t.term_en ? t.term_en : t.term;
              const defDisplay = lang === "en" && t.definition_en ? t.definition_en : t.definition;
              const isSaved = saved.includes(t.slug);
              return (
                <div
                  key={t.slug || t.term}
                  style={{
                    borderRadius: 14, padding: 18, cursor: "pointer",
                    border: `1px solid ${hoverCard === t.slug ? C.borderHover : C.border}`,
                    backgroundColor: hoverCard === t.slug ? C.cardHover : C.card,
                    transition: "all 0.15s", position: "relative",
                  }}
                  onMouseEnter={() => setHoverCard(t.slug)}
                  onMouseLeave={() => setHoverCard(null)}
                  onClick={() => openTerm(t)}
                >
                  {/* Save button */}
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleSave(t.slug); }}
                    style={{ position: "absolute", top: 12, right: 12, background: "none", border: "none", cursor: "pointer", color: isSaved ? C.yellow : C.text3, opacity: 0.8 }}
                  >
                    {isSaved ? <BookmarkCheck size={13} /> : <Bookmark size={13} />}
                  </button>

                  {/* Badges */}
                  <div style={{ display: "flex", gap: 4, marginBottom: 8 }}>
                    <span style={{ borderRadius: 6, backgroundColor: C.primary, padding: "2px 7px", fontSize: 9, color: C.text3 }}>
                      {catIcon(t.category)} {normalizeCategory(t.category).length > 18 ? normalizeCategory(t.category).slice(0, 18) + "…" : normalizeCategory(t.category)}
                    </span>
                    <span style={{ borderRadius: 6, backgroundColor: lc.bg, padding: "2px 7px", fontSize: 9, fontWeight: 600, color: lc.color }}>{t.level}</span>
                    {t.formula && <span style={{ borderRadius: 6, backgroundColor: "rgba(167,139,250,0.08)", padding: "2px 6px", fontSize: 9, color: purple }}>📐</span>}
                  </div>

                  {/* Term name */}
                  <h3 style={{ fontSize: 13, fontWeight: 600, color: C.text1, marginBottom: 6, paddingRight: 20 }}>
                    {termDisplay.split("(")[0].trim()}
                    {t.term_en && lang === "tr" && (
                      <span style={{ fontSize: 10, color: C.text3, fontWeight: 400, marginLeft: 6 }}>{t.term_en}</span>
                    )}
                  </h3>

                  {/* Definition snippet */}
                  <p style={{ fontSize: 12, color: C.text2, lineHeight: 1.6 }}>
                    {defDisplay.length > 110 ? defDisplay.slice(0, 110) + "…" : defDisplay}
                  </p>

                  {/* Tags */}
                  {t.tags && t.tags.length > 0 && (
                    <div style={{ display: "flex", gap: 4, marginTop: 8, flexWrap: "wrap" }}>
                      {t.tags.slice(0, 3).map((tag) => (
                        <span key={tag} style={{ borderRadius: 5, backgroundColor: "rgba(255,214,10,0.07)", padding: "1px 5px", fontSize: 9, color: C.yellow }}>#{tag}</span>
                      ))}
                    </div>
                  )}

                  {hoverCard === t.slug && (
                    <div style={{ position: "absolute", bottom: 10, right: 12, fontSize: 9, color: C.cyan, display: "flex", alignItems: "center", gap: 3 }}>
                      Detaylar <ChevronRight size={9} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Empty state */}
          {filteredTerms.length === 0 && (
            <div style={{ textAlign: "center", padding: 48, color: C.text3 }}>
              <Search size={36} style={{ margin: "0 auto 12px", opacity: 0.4 }} />
              <p style={{ fontSize: 14, marginBottom: 4 }}>Sonuç bulunamadı</p>
              <p style={{ fontSize: 11 }}>Fuse.js akıllı arama etkin — farklı bir yazım veya filtre deneyin</p>
            </div>
          )}

          {/* Load more */}
          {filteredTerms.length > displayedTerms.length && (
            <div style={{ textAlign: "center", marginTop: 24 }}>
              <button
                onClick={() => setPage((p) => p + 1)}
                style={{ borderRadius: 12, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: "10px 28px", fontSize: 12, color: C.text2, cursor: "pointer" }}
              >
                Daha fazla yükle ({filteredTerms.length - displayedTerms.length} kaldı)
              </button>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════
          TAB: QUIZ
          ══════════════════════════════════════════════════════ */}
      {activeTab === "Quiz" && (
        <div style={{ maxWidth: 640, margin: "0 auto" }}>
          {/* Level selector */}
          <div style={{ display: "flex", gap: 6, marginBottom: 20, flexWrap: "wrap" }}>
            {["Tümü", "Başlangıç", "Orta", "İleri", "Uzman"].map((l) => {
              const active = quizLevel === l;
              const lc = l === "Tümü" ? { color: C.text2, bg: C.card } : levelColor(l);
              return (
                <button
                  key={l}
                  onClick={() => setQuizLevel(l)}
                  style={{
                    borderRadius: 8, padding: "6px 14px", fontSize: 11, fontWeight: 600,
                    border: `1px solid ${active ? lc.color : C.border}`,
                    backgroundColor: active ? lc.bg : "transparent",
                    color: active ? lc.color : C.text3,
                    cursor: "pointer",
                  }}
                >
                  {l}
                </button>
              );
            })}
          </div>

          {quizQuestions.length === 0 ? (
            <div style={{ textAlign: "center", padding: 48, color: C.text3 }}>
              <HelpCircle size={36} style={{ margin: "0 auto 12px" }} />
              <p>Sözlük yükleniyor...</p>
            </div>
          ) : !quizDone ? (
            <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 28 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                <span style={{ fontSize: 11, color: C.text3 }}>Soru {quizIndex + 1} / {quizQuestions.length}</span>
                <span style={{ fontSize: 11, fontWeight: 600, color: C.cyan }}>
                  ✓ {quizScore} / {quizIndex + (selectedAnswer !== null ? 1 : 0)}
                </span>
              </div>
              <div style={{ height: 3, borderRadius: 2, backgroundColor: C.primary, marginBottom: 20 }}>
                <div style={{ width: `${((quizIndex + 1) / quizQuestions.length) * 100}%`, height: 3, borderRadius: 2, backgroundColor: C.cyan, transition: "width 0.3s" }} />
              </div>
              <p style={{ fontSize: 11, color: C.text3, marginBottom: 6 }}>
                {quizQuestions[quizIndex].type === "def2term" ? "Bu tanım hangi kavrama aittir?" : "Bu kavramın tanımı nedir?"}
              </p>
              <h2 style={{ fontSize: 14, fontWeight: 600, color: C.text1, marginBottom: 20, lineHeight: 1.6 }}>
                {quizQuestions[quizIndex].question.split("\n").pop()}
              </h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {quizQuestions[quizIndex].options.map((opt, i) => {
                  const isSelected = selectedAnswer === i;
                  const isCorrect = i === quizQuestions[quizIndex].answer;
                  const showResult = selectedAnswer !== null;
                  let borderCol = C.border;
                  let bgCol = C.primary;
                  let textCol = C.text1;
                  if (showResult && isCorrect) { borderCol = C.green; bgCol = "rgba(48,209,88,0.08)"; textCol = C.green; }
                  if (showResult && isSelected && !isCorrect) { borderCol = C.red; bgCol = "rgba(255,69,58,0.08)"; textCol = C.red; }
                  return (
                    <button
                      key={i}
                      onClick={() => handleQuizAnswer(i)}
                      disabled={selectedAnswer !== null}
                      style={{
                        display: "flex", alignItems: "center", justifyContent: "space-between",
                        width: "100%", textAlign: "left", borderRadius: 10,
                        border: `1px solid ${borderCol}`, backgroundColor: bgCol,
                        padding: "10px 16px", fontSize: 12, color: textCol,
                        cursor: selectedAnswer !== null ? "default" : "pointer", transition: "all 0.2s",
                      }}
                    >
                      <span style={{ flex: 1, lineHeight: 1.5 }}>{opt}</span>
                      {showResult && isCorrect && <CheckCircle size={15} style={{ flexShrink: 0, marginLeft: 8 }} />}
                      {showResult && isSelected && !isCorrect && <XCircle size={15} style={{ flexShrink: 0, marginLeft: 8 }} />}
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 32, textAlign: "center" }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>🎉</div>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: C.text1, marginBottom: 8 }}>Quiz Tamamlandı!</h2>
              <p style={{ fontSize: 13, color: C.text2, marginBottom: 8 }}>
                <strong style={{ color: C.cyan }}>{quizScore}</strong> / {quizQuestions.length} doğru
              </p>
              <div style={{ fontSize: 32, fontWeight: 700, marginBottom: 20, color: quizScore >= 8 ? C.green : quizScore >= 5 ? C.cyan : C.red }}>
                %{Math.round((quizScore / quizQuestions.length) * 100)}
              </div>
              <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
                <button
                  onClick={() => generateQuiz(quizLevel)}
                  style={{ borderRadius: 10, padding: "9px 20px", fontSize: 12, fontWeight: 600, color: "#000", border: "none", cursor: "pointer", background: `linear-gradient(135deg, ${C.cyan}, ${C.blue})` }}
                >
                  Tekrar Dene
                </button>
                <button
                  onClick={() => setActiveTab("Sözlük")}
                  style={{ borderRadius: 10, padding: "9px 20px", fontSize: 12, fontWeight: 600, color: C.text2, border: `1px solid ${C.border}`, backgroundColor: C.card, cursor: "pointer" }}
                >
                  Sözlüğe Git
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════
          TAB: STRATEJİLER
          ══════════════════════════════════════════════════════ */}
      {activeTab === "Stratejiler" && (
        <div style={{ display: "grid", gap: 14, gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))" }}>
          {strategies.map((s) => (
            <div
              key={s.name}
              style={{
                borderRadius: 16, padding: 22,
                border: `1px solid ${hoverCard === s.name ? C.borderHover : C.border}`,
                backgroundColor: hoverCard === s.name ? C.cardHover : C.card,
                transition: "all 0.2s",
              }}
              onMouseEnter={() => setHoverCard(s.name)}
              onMouseLeave={() => setHoverCard(null)}
            >
              <div style={{ fontSize: 28, marginBottom: 10 }}>{s.icon}</div>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: C.text1, marginBottom: 6 }}>{s.name}</h3>
              <p style={{ fontSize: 12, color: C.text2, lineHeight: 1.6, marginBottom: 14 }}>{s.description}</p>
              <div style={{ marginBottom: 12 }}>
                <h4 style={{ fontSize: 10, fontWeight: 600, color: C.text3, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>Nasıl Çalışır</h4>
                <p style={{ fontSize: 12, color: C.text2, lineHeight: 1.6 }}>{s.howItWorks}</p>
              </div>
              <div style={{ borderRadius: 10, backgroundColor: "rgba(0,212,255,0.04)", padding: "10px 12px", marginBottom: s.relatedSlugs.length > 0 ? 10 : 0 }}>
                <h4 style={{ fontSize: 10, fontWeight: 600, color: C.cyan, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>FinPilot Bağlantısı</h4>
                <p style={{ fontSize: 11, color: C.text2 }}>{s.connection}</p>
              </div>
              {s.relatedSlugs.length > 0 && (
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {s.relatedSlugs.map((slug) => {
                    const entry = allTerms.find((t) => t.slug === slug);
                    return entry ? (
                      <button
                        key={slug}
                        onClick={() => router.push(`/dashboard/finsense/${slug}`)}
                        style={{ borderRadius: 6, backgroundColor: "rgba(0,212,255,0.08)", padding: "2px 8px", fontSize: 10, color: C.cyan, border: "none", cursor: "pointer" }}
                      >
                        {entry.term.split("(")[0].trim().slice(0, 20)}
                      </button>
                    ) : null;
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════
          TAB: HESAPLA
          ══════════════════════════════════════════════════════ */}
      {activeTab === "Hesapla" && (
        <div style={{ maxWidth: 720, margin: "0 auto" }}>
          <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 24 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
              <Calculator size={18} style={{ color: C.cyan }} />
              <h2 style={{ fontSize: 14, fontWeight: 600, color: C.text1 }}>Bileşik Faiz Hesaplayıcı</h2>
            </div>
            <div style={{ display: "grid", gap: 14, gridTemplateColumns: "repeat(2, 1fr)", marginBottom: 20 }}>
              <div>
                <label style={{ display: "block", marginBottom: 4, fontSize: 11, color: C.text3 }}>Başlangıç Yatırımı ($)</label>
                <input type="number" value={initial} onChange={(e) => setInitial(Number(e.target.value))} style={inputStyle} />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 4, fontSize: 11, color: C.text3 }}>Aylık Katkı ($)</label>
                <input type="number" value={monthly} onChange={(e) => setMonthly(Number(e.target.value))} style={inputStyle} />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 4, fontSize: 11, color: C.text3 }}>Yıllık Getiri (%)</label>
                <input type="number" value={rate} onChange={(e) => setRate(Number(e.target.value))} style={inputStyle} />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 4, fontSize: 11, color: C.text3 }}>
                  Süre: <strong style={{ color: C.text1 }}>{years} yıl</strong>
                </label>
                <input type="range" min={1} max={30} value={years} onChange={(e) => setYears(Number(e.target.value))} style={{ width: "100%", accentColor: C.cyan }} />
              </div>
            </div>

            {/* Results */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 16 }}>
              {[
                { label: "Toplam Yatırım", value: `$${totalInvested.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, color: C.text1 },
                { label: "Kazanılan Faiz", value: `$${totalInterest.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, color: C.green },
                { label: "Gelecek Değer", value: `$${futureValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, color: C.cyan },
              ].map((item) => (
                <div key={item.label} style={{ borderRadius: 10, backgroundColor: C.primary, padding: 14, textAlign: "center" }}>
                  <div style={{ fontSize: 10, color: C.text3, marginBottom: 4 }}>{item.label}</div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: item.color }}>{item.value}</div>
                </div>
              ))}
            </div>

            {/* Growth SVG chart */}
            <div style={{ borderRadius: 10, backgroundColor: C.primary, padding: 14 }}>
              <p style={{ fontSize: 10, color: C.text3, marginBottom: 8 }}>Büyüme Grafiği ({years} yıl)</p>
              <svg width="100%" height="100" viewBox="0 0 500 100" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="growGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={C.cyan} stopOpacity={0.25} />
                    <stop offset="100%" stopColor={C.cyan} stopOpacity={0} />
                  </linearGradient>
                </defs>
                {(() => {
                  const pts: number[] = [];
                  for (let y = 0; y <= years; y++) {
                    const m = y * 12;
                    const v = initial * (1 + monthlyRate) ** m + monthly * (((1 + monthlyRate) ** m - 1) / monthlyRate);
                    pts.push(v);
                  }
                  const max = pts[pts.length - 1];
                  const pathD = pts.map((v, i) => `${i === 0 ? "M" : "L"} ${(i / years) * 500} ${90 - (v / max) * 80}`).join(" ");
                  const areaD = `${pathD} L 500 90 L 0 90 Z`;
                  return (
                    <>
                      <path d={areaD} fill="url(#growGrad)" />
                      <path d={pathD} fill="none" stroke={C.cyan} strokeWidth={1.5} />
                    </>
                  );
                })()}
              </svg>
            </div>

            <div style={{ marginTop: 14 }}>
              <button
                onClick={() => { setActiveTab("Sözlük"); setSearchTerm("bileşik faiz"); }}
                style={{ borderRadius: 8, border: `1px solid ${C.border}`, backgroundColor: "transparent", padding: "6px 12px", fontSize: 11, color: C.cyan, cursor: "pointer" }}
              >
                <Zap size={10} style={{ display: "inline", marginRight: 4 }} />
                Bileşik Faiz kavramını öğren
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
