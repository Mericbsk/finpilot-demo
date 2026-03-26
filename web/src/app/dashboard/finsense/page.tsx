"use client";

import { useState, useEffect, useMemo } from "react";
import {
  GraduationCap,
  BookOpen,
  HelpCircle,
  Compass,
  Calculator,
  Search,
  ChevronDown,
  CheckCircle,
  XCircle,
  Globe,
  Tag,
  Link2,
} from "lucide-react";
import { C, hashStr } from "@/lib/stockData";

/* ── Extend C with purple for FinSense ────────────────────── */
const purple = "#a78bfa";

/* ── Type for dictionary entry ────────────────────────────── */
interface DictEntry {
  term: string;
  definition: string;
  example?: string;
  category: string;
  level: string;
  related?: string[];
  term_en?: string;
  definition_en?: string;
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
    "Piyasa İşleyişi": "🏛️", "Yatırım ve Varlık Yönetimi": "🎯", "Makroekonomi": "🌍",
    "İleri Düzey Kavramlar": "🧠", "Kredi ve Borç Yönetimi": "💳", "Dijital Finans": "🔗",
    "Psikoloji": "🧘", "Bankacılık": "🏦", "Girişimcilik": "🚀", "Emeklilik ve Sigorta": "🛡️",
  };
  return m[cat] || "📚";
}

/* ── Tabs ──────────────────────────────────────────────────── */
const tabList = ["Dictionary", "Quiz", "Strategies", "Calculators"];

/* ── Strategy data ─────────────────────────────────────────── */
const strategies = [
  {
    name: "Momentum Yatırımı", icon: "🚀",
    description: "Yükselen hisseler yükselmeye devam eder, düşenler düşmeye devam eder varsayımına dayanır.",
    howItWorks: "Son 3-6-12 ay performansı en iyi hisseleri al. Momentum zayıfladığında (RSI sapma, MACD bearish cross) sat.",
    connection: "FinPilot'un scanner'ı RSI, Moving Average ve Z-Score kullanarak yüksek momentum hisseleri gerçek zamanlı tespit eder.",
  },
  {
    name: "Ortalamaya Dönüş", icon: "🔄",
    description: "Fiyatlar aşırı hareketlerden sonra tarihsel ortalamasına döner. Aşırı satımda al, aşırı alımda sat.",
    howItWorks: "Ortalamadan anlamlı sapma gösteren hisseleri tespit et (Z-Score, Bollinger Bands). Dönüş sinyali geldiğinde gir.",
    connection: "FinPilot'un Z-Score ve Bollinger Band takibi ortalamaya dönüş fırsatlarını otomatik işaretler.",
  },
  {
    name: "Trend Takibi", icon: "📈",
    description: "Mevcut piyasa trendinin yönünde işlem yap. Trende karşı işlem yapma.",
    howItWorks: "Fiyat SMA200 üstündeyken al (uptrend). Altına düştüğünde sat/nakit kal. Regime detection ile doğrula.",
    connection: "FinPilot'un Regime Detection modülü piyasaları otomatik Trend/Volatile/Range olarak sınıflar.",
  },
  {
    name: "DRL Agent Stratejisi", icon: "🤖",
    description: "Deep Reinforcement Learning ajanları piyasa rejimlerine göre adaptif strateji uygular.",
    howItWorks: "PPO/SAC/TD3 ajanları trend, volatil ve range rejimlerinde farklı stratejiler uygular. Ensemble voting ile konsensüs sağlanır.",
    connection: "FinPilot AI Lab'daki 3 DRL ajanı her hisse için bağımsız oylama yapar, %87+ doğruluk oranıyla.",
  },
  {
    name: "Değer Yatırımı", icon: "💎",
    description: "İçsel değerinin altında işlem gören hisselere uzun vadeli yatırım. Warren Buffett yaklaşımı.",
    howItWorks: "Düşük P/E, yüksek marjin, güçlü bilanço. Fundamental analiz ile undervalued hisseleri tespit et.",
    connection: "FinPilot Analysis sayfasında Fundamental tab'ında P/E, Debt/Equity, Revenue Growth metrikleri gösterilir.",
  },
];

/* ═══════════════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════════════ */
export default function FinSensePage() {
  const [activeTab, setActiveTab] = useState("Dictionary");
  const [allTerms, setAllTerms] = useState<DictEntry[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("Tümü");
  const [selectedLevel, setSelectedLevel] = useState("Tümü");
  const [lang, setLang] = useState<"tr" | "en">("tr");
  const [expandedTerm, setExpandedTerm] = useState<string | null>(null);
  const [hoverCard, setHoverCard] = useState<string | null>(null);

  /* Quiz state */
  const [quizIndex, setQuizIndex] = useState(0);
  const [quizScore, setQuizScore] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [quizDone, setQuizDone] = useState(false);
  const [quizQuestions, setQuizQuestions] = useState<
    { question: string; options: string[]; answer: number }[]
  >([]);

  /* Calculator state */
  const [initial, setInitial] = useState(10000);
  const [monthly, setMonthly] = useState(1000);
  const [rate, setRate] = useState(10);
  const [years, setYears] = useState(10);

  /* Load dictionary */
  useEffect(() => {
    fetch("/dictionary.json")
      .then((r) => r.json())
      .then((data: DictEntry[]) => setAllTerms(data))
      .catch(() => {});
  }, []);

  /* Generate quiz from terms */
  useEffect(() => {
    if (allTerms.length < 10) return;
    const shuffled = [...allTerms].sort(() => hashStr(Date.now().toString() + Math.random()) % 2 - 0.5);
    const picked = shuffled.slice(0, 10);
    const qs = picked.map((entry, qi) => {
      const correctDef = lang === "en" && entry.definition_en ? entry.definition_en : entry.definition;
      const shortDef = correctDef.length > 80 ? correctDef.slice(0, 80) + "…" : correctDef;
      const others = allTerms
        .filter((t) => t.term !== entry.term)
        .sort(() => hashStr(entry.term + qi.toString()) % 2 - 0.5)
        .slice(0, 3)
        .map((t) => {
          const d = lang === "en" && t.definition_en ? t.definition_en : t.definition;
          return d.length > 80 ? d.slice(0, 80) + "…" : d;
        });
      const answerIdx = hashStr(entry.term) % 4;
      const options = [...others];
      options.splice(answerIdx, 0, shortDef);
      const termName = lang === "en" && entry.term_en ? entry.term_en : entry.term;
      return { question: `"${termName}" nedir?`, options, answer: answerIdx };
    });
    setQuizQuestions(qs);
    setQuizIndex(0);
    setQuizScore(0);
    setSelectedAnswer(null);
    setQuizDone(false);
  }, [allTerms, lang]);

  /* Filter terms */
  const categories = useMemo(() => {
    const cats = Array.from(new Set(allTerms.map((t) => t.category))).sort();
    return ["Tümü", ...cats];
  }, [allTerms]);

  const levels = useMemo(() => {
    const lvls = Array.from(new Set(allTerms.map((t) => t.level))).sort();
    return ["Tümü", ...lvls];
  }, [allTerms]);

  const filteredTerms = useMemo(() => {
    return allTerms.filter((t) => {
      const q = searchTerm.toLowerCase();
      const matchText =
        t.term.toLowerCase().includes(q) ||
        t.definition.toLowerCase().includes(q) ||
        (t.term_en || "").toLowerCase().includes(q) ||
        (t.definition_en || "").toLowerCase().includes(q);
      const matchCat = selectedCategory === "Tümü" || t.category === selectedCategory;
      const matchLvl = selectedLevel === "Tümü" || t.level === selectedLevel;
      return matchText && matchCat && matchLvl;
    });
  }, [allTerms, searchTerm, selectedCategory, selectedLevel]);

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

  function jumpToTerm(term: string) {
    setActiveTab("Dictionary");
    setSearchTerm(term.split(" (")[0]);
    setSelectedCategory("Tümü");
    setSelectedLevel("Tümü");
  }

  /* Calculator */
  const monthlyRate = rate / 100 / 12;
  const totalMonths = years * 12;
  const futureValue =
    initial * (1 + monthlyRate) ** totalMonths +
    monthly * (((1 + monthlyRate) ** totalMonths - 1) / monthlyRate);
  const totalInvested = initial + monthly * totalMonths;
  const totalInterest = futureValue - totalInvested;

  /* Shared styles */
  const inputStyle: React.CSSProperties = {
    width: "100%", borderRadius: 8, border: `1px solid ${C.border}`,
    backgroundColor: C.primary, padding: "8px 12px", fontSize: 13, color: C.text1, outline: "none",
  };

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 16px" }}>
      {/* ── Header ──────────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <GraduationCap size={20} style={{ color: purple }} />
            <h1 style={{ fontSize: 20, fontWeight: 600, color: C.text1 }}>FinSense Academy</h1>
            <span style={{ fontSize: 11, color: C.text3, marginLeft: 8 }}>
              {allTerms.length} terim • 13 kategori
            </span>
          </div>
          {/* TR/EN toggle */}
          <button
            onClick={() => setLang(lang === "tr" ? "en" : "tr")}
            style={{
              display: "flex", alignItems: "center", gap: 6, borderRadius: 8,
              border: `1px solid ${C.border}`, backgroundColor: C.card,
              padding: "6px 12px", fontSize: 11, fontWeight: 600,
              color: C.cyan, cursor: "pointer",
            }}
          >
            <Globe size={12} />
            {lang === "tr" ? "TR 🇹🇷" : "EN 🇺🇸"}
          </button>
        </div>
        <p style={{ fontSize: 13, color: C.text3, marginTop: 4 }}>
          Finansal okuryazarlık eğitimi — interaktif sözlük, quiz ve hesap araçları
        </p>
      </div>

      {/* ── Tab bar ───────────────────────────────────────── */}
      <div
        style={{
          display: "flex", gap: 4, borderRadius: 12, backgroundColor: C.card,
          padding: 4, marginBottom: 24,
        }}
      >
        {tabList.map((t) => {
          const icons: Record<string, typeof BookOpen> = {
            Dictionary: BookOpen, Quiz: HelpCircle, Strategies: Compass, Calculators: Calculator,
          };
          const Icon = icons[t];
          return (
            <button
              key={t}
              onClick={() => setActiveTab(t)}
              style={{
                flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
                gap: 6, borderRadius: 8, padding: "8px 12px", fontSize: 12, fontWeight: 500,
                border: "none", cursor: "pointer", transition: "all 0.2s",
                backgroundColor: activeTab === t ? C.primary : "transparent",
                color: activeTab === t ? C.text1 : C.text3,
              }}
            >
              <Icon size={14} />
              {t}
            </button>
          );
        })}
      </div>

      {/* ══════════════════════════════════════════════════════
          TAB: DICTIONARY
          ══════════════════════════════════════════════════════ */}
      {activeTab === "Dictionary" && (
        <div>
          {/* Search + filters */}
          <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 200, position: "relative" }}>
              <Search size={14} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: C.text3 }} />
              <input
                type="text"
                placeholder={`${allTerms.length} terimde ara...`}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ ...inputStyle, paddingLeft: 32, borderRadius: 12, backgroundColor: C.card }}
              />
            </div>
            {/* Category filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              style={{ ...inputStyle, width: "auto", minWidth: 160, borderRadius: 12, backgroundColor: C.card }}
            >
              {categories.map((c) => (
                <option key={c} value={c} style={{ backgroundColor: C.card, color: C.text1 }}>
                  {c === "Tümü" ? "📚 Tüm Kategoriler" : `${catIcon(c)} ${c}`}
                </option>
              ))}
            </select>
            {/* Level filter */}
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              style={{ ...inputStyle, width: "auto", minWidth: 130, borderRadius: 12, backgroundColor: C.card }}
            >
              {levels.map((l) => (
                <option key={l} value={l} style={{ backgroundColor: C.card, color: C.text1 }}>
                  {l === "Tümü" ? "🎓 Tüm Seviyeler" : l}
                </option>
              ))}
            </select>
          </div>

          {/* Results count */}
          <p style={{ fontSize: 11, color: C.text3, marginBottom: 12 }}>
            {filteredTerms.length} / {allTerms.length} terim gösteriliyor
          </p>

          {/* Term cards grid */}
          <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(3, 1fr)" }}>
            {filteredTerms.map((t) => {
              const lc = levelColor(t.level);
              const isExpanded = expandedTerm === t.term;
              const termDisplay = lang === "en" && t.term_en ? t.term_en : t.term;
              const defDisplay = lang === "en" && t.definition_en ? t.definition_en : t.definition;
              return (
                <div
                  key={t.term}
                  onClick={() => setExpandedTerm(isExpanded ? null : t.term)}
                  style={{
                    borderRadius: 16, padding: 20, cursor: "pointer",
                    border: `1px solid ${hoverCard === t.term ? C.borderHover : isExpanded ? C.cyan : C.border}`,
                    backgroundColor: hoverCard === t.term ? C.cardHover : C.card,
                    transition: "all 0.2s",
                  }}
                  onMouseEnter={() => setHoverCard(t.term)}
                  onMouseLeave={() => setHoverCard(null)}
                >
                  {/* Header row */}
                  <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 8 }}>
                    <h3 style={{ fontSize: 13, fontWeight: 600, color: C.text1, flex: 1 }}>
                      {termDisplay}
                    </h3>
                    <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
                      <span style={{ borderRadius: 6, backgroundColor: C.primary, padding: "2px 6px", fontSize: 9, color: C.text3 }}>
                        {catIcon(t.category)} {t.category.length > 15 ? t.category.slice(0, 15) + "…" : t.category}
                      </span>
                      <span style={{ borderRadius: 6, backgroundColor: lc.bg, padding: "2px 6px", fontSize: 9, fontWeight: 600, color: lc.color }}>
                        {t.level}
                      </span>
                    </div>
                  </div>

                  {/* Definition */}
                  <p style={{ fontSize: 12, color: C.text2, lineHeight: 1.6, marginBottom: 8 }}>
                    {isExpanded ? defDisplay : defDisplay.length > 120 ? defDisplay.slice(0, 120) + "…" : defDisplay}
                  </p>

                  {/* Example (always show if short, or if expanded) */}
                  {t.example && (isExpanded || t.example.length < 80) && (
                    <div style={{
                      borderRadius: 8, backgroundColor: C.primary, padding: "8px 12px",
                      fontSize: 11, color: C.text3, fontStyle: "italic", marginBottom: 8,
                    }}>
                      💡 {t.example}
                    </div>
                  )}

                  {/* Expanded: EN translation + related terms */}
                  {isExpanded && (
                    <>
                      {lang === "tr" && t.term_en && (
                        <div style={{ fontSize: 11, color: C.text3, marginBottom: 8 }}>
                          <Globe size={10} style={{ display: "inline", marginRight: 4 }} />
                          EN: {t.term_en} — {t.definition_en || ""}
                        </div>
                      )}
                      {t.related && t.related.length > 0 && (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
                          <Link2 size={10} style={{ color: C.text3, marginTop: 3 }} />
                          {t.related.map((r) => (
                            <button
                              key={r}
                              onClick={(e) => { e.stopPropagation(); jumpToTerm(r); }}
                              style={{
                                borderRadius: 6, backgroundColor: "rgba(0,212,255,0.08)",
                                padding: "2px 8px", fontSize: 10, color: C.cyan,
                                border: "none", cursor: "pointer",
                              }}
                            >
                              {r}
                            </button>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              );
            })}
          </div>

          {filteredTerms.length === 0 && (
            <div style={{ textAlign: "center", padding: 48, color: C.text3 }}>
              <Search size={36} style={{ margin: "0 auto 12px", opacity: 0.5 }} />
              <p style={{ fontSize: 14 }}>Sonuç bulunamadı</p>
              <p style={{ fontSize: 11, marginTop: 4 }}>Farklı bir arama terimi veya filtre deneyin</p>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════
          TAB: QUIZ
          ══════════════════════════════════════════════════════ */}
      {activeTab === "Quiz" && (
        <div style={{ maxWidth: 640, margin: "0 auto" }}>
          {quizQuestions.length === 0 ? (
            <div style={{ textAlign: "center", padding: 48, color: C.text3 }}>
              <HelpCircle size={36} style={{ margin: "0 auto 12px" }} />
              <p>Sözlük yükleniyor...</p>
            </div>
          ) : !quizDone ? (
            <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 32 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                <span style={{ fontSize: 12, color: C.text3 }}>
                  Soru {quizIndex + 1} / {quizQuestions.length}
                </span>
                <span style={{ fontSize: 12, fontWeight: 600, color: C.cyan }}>
                  Skor: {quizScore}/{quizIndex + (selectedAnswer !== null ? 1 : 0)}
                </span>
              </div>
              {/* Progress */}
              <div style={{ height: 4, borderRadius: 2, backgroundColor: C.primary, marginBottom: 24 }}>
                <div style={{
                  width: `${((quizIndex + 1) / quizQuestions.length) * 100}%`,
                  height: 4, borderRadius: 2, backgroundColor: C.cyan, transition: "width 0.3s",
                }} />
              </div>
              <h2 style={{ fontSize: 16, fontWeight: 600, color: C.text1, marginBottom: 24 }}>
                {quizQuestions[quizIndex].question}
              </h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
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
                        width: "100%", textAlign: "left", borderRadius: 12,
                        border: `1px solid ${borderCol}`, backgroundColor: bgCol,
                        padding: "12px 20px", fontSize: 13, color: textCol,
                        cursor: selectedAnswer !== null ? "default" : "pointer",
                        transition: "all 0.2s",
                      }}
                    >
                      <span>{opt}</span>
                      {showResult && isCorrect && <CheckCircle size={16} />}
                      {showResult && isSelected && !isCorrect && <XCircle size={16} />}
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 32, textAlign: "center" }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>🎉</div>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: C.text1, marginBottom: 8 }}>Quiz Tamamlandı!</h2>
              <p style={{ fontSize: 13, color: C.text2, marginBottom: 16 }}>
                <strong style={{ color: C.cyan }}>{quizScore}</strong> / {quizQuestions.length} doğru
              </p>
              <div style={{
                fontSize: 36, fontWeight: 700, marginBottom: 24,
                color: quizScore >= 8 ? C.green : quizScore >= 5 ? C.cyan : C.red,
              }}>
                %{Math.round((quizScore / quizQuestions.length) * 100)}
              </div>
              <button
                onClick={() => {
                  setQuizIndex(0); setQuizScore(0); setSelectedAnswer(null); setQuizDone(false);
                  // Regenerate questions
                  const shuffled = [...allTerms].sort(() => Math.random() - 0.5);
                  const picked = shuffled.slice(0, 10);
                  const qs = picked.map((entry, qi) => {
                    const correctDef = lang === "en" && entry.definition_en ? entry.definition_en : entry.definition;
                    const shortDef = correctDef.length > 80 ? correctDef.slice(0, 80) + "…" : correctDef;
                    const others = allTerms.filter((t) => t.term !== entry.term)
                      .sort(() => Math.random() - 0.5).slice(0, 3)
                      .map((t) => { const d = lang === "en" && t.definition_en ? t.definition_en : t.definition; return d.length > 80 ? d.slice(0, 80) + "…" : d; });
                    const answerIdx = Math.floor(Math.random() * 4);
                    const options = [...others]; options.splice(answerIdx, 0, shortDef);
                    const termName = lang === "en" && entry.term_en ? entry.term_en : entry.term;
                    return { question: `"${termName}" nedir?`, options, answer: answerIdx };
                  });
                  setQuizQuestions(qs);
                }}
                style={{
                  borderRadius: 12, padding: "10px 24px", fontSize: 13, fontWeight: 600,
                  color: "#000", border: "none", cursor: "pointer",
                  background: `linear-gradient(135deg, ${C.cyan}, ${C.blue})`,
                }}
              >
                Tekrar Dene
              </button>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════
          TAB: STRATEGIES
          ══════════════════════════════════════════════════════ */}
      {activeTab === "Strategies" && (
        <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fill, minmax(340, 1fr))" }}>
          {strategies.map((s) => (
            <div
              key={s.name}
              style={{
                borderRadius: 16, padding: 24,
                border: `1px solid ${hoverCard === s.name ? C.borderHover : C.border}`,
                backgroundColor: hoverCard === s.name ? C.cardHover : C.card,
                transition: "all 0.2s",
              }}
              onMouseEnter={() => setHoverCard(s.name)}
              onMouseLeave={() => setHoverCard(null)}
            >
              <div style={{ fontSize: 32, marginBottom: 12 }}>{s.icon}</div>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: C.text1, marginBottom: 8 }}>{s.name}</h3>
              <p style={{ fontSize: 12, color: C.text2, lineHeight: 1.6, marginBottom: 16 }}>{s.description}</p>
              <div style={{ marginBottom: 12 }}>
                <h4 style={{ fontSize: 11, fontWeight: 600, color: C.text3, marginBottom: 4 }}>Nasıl Çalışır</h4>
                <p style={{ fontSize: 12, color: C.text2 }}>{s.howItWorks}</p>
              </div>
              <div style={{ borderRadius: 10, backgroundColor: "rgba(0,212,255,0.04)", padding: 12 }}>
                <h4 style={{ fontSize: 11, fontWeight: 600, color: C.cyan, marginBottom: 4 }}>FinPilot Bağlantısı</h4>
                <p style={{ fontSize: 11, color: C.text2 }}>{s.connection}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════
          TAB: CALCULATORS
          ══════════════════════════════════════════════════════ */}
      {activeTab === "Calculators" && (
        <div style={{ maxWidth: 720, margin: "0 auto" }}>
          <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 24 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
              <Calculator size={18} style={{ color: C.cyan }} />
              <h2 style={{ fontSize: 14, fontWeight: 600, color: C.text1 }}>Bileşik Faiz Hesaplayıcı</h2>
            </div>
            <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(2, 1fr)", marginBottom: 24 }}>
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
                  Yatırım Süresi: <strong style={{ color: C.text1 }}>{years} yıl</strong>
                </label>
                <input
                  type="range" min={1} max={30} value={years}
                  onChange={(e) => setYears(Number(e.target.value))}
                  style={{ width: "100%", accentColor: C.cyan }}
                />
              </div>
            </div>

            {/* Results */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 16 }}>
              <div style={{ borderRadius: 12, backgroundColor: C.primary, padding: 16, textAlign: "center" }}>
                <div style={{ fontSize: 10, color: C.text3, marginBottom: 4 }}>Toplam Yatırım</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: C.text1 }}>
                  ${totalInvested.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </div>
              </div>
              <div style={{ borderRadius: 12, backgroundColor: C.primary, padding: 16, textAlign: "center" }}>
                <div style={{ fontSize: 10, color: C.text3, marginBottom: 4 }}>Kazanılan Faiz</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: C.green }}>
                  ${totalInterest.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </div>
              </div>
              <div style={{ borderRadius: 12, backgroundColor: "rgba(0,212,255,0.06)", padding: 16, textAlign: "center" }}>
                <div style={{ fontSize: 10, color: C.text3, marginBottom: 4 }}>Gelecek Değer</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: C.cyan }}>
                  ${futureValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </div>
              </div>
            </div>

            {/* Growth SVG */}
            <div style={{ borderRadius: 12, backgroundColor: C.primary, padding: 16 }}>
              <p style={{ fontSize: 11, color: C.text3, marginBottom: 8 }}>Büyüme Grafiği</p>
              <svg width="100%" height="120" viewBox="0 0 500 120" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="growGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={C.cyan} stopOpacity={0.3} />
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
                  const mx = Math.max(...pts);
                  const mn = Math.min(...pts);
                  const rng = mx - mn || 1;
                  const line = pts.map((v, i) => `${(i / years) * 500},${110 - ((v - mn) / rng) * 100}`).join(" ");
                  const fill = `0,110 ${line} 500,110`;
                  return (
                    <>
                      <polygon points={fill} fill="url(#growGrad)" />
                      <polyline points={line} fill="none" stroke={C.cyan} strokeWidth="2" />
                      <text x={4} y={12} fill={C.text3} fontSize="9">
                        ${(pts[0] / 1000).toFixed(0)}K
                      </text>
                      <text x={496} y={12} fill={C.cyan} fontSize="9" textAnchor="end" fontWeight="bold">
                        ${(pts[pts.length - 1] / 1000).toFixed(0)}K
                      </text>
                    </>
                  );
                })()}
              </svg>
            </div>

            <div style={{ marginTop: 12, textAlign: "center", fontSize: 12, color: C.text3 }}>
              Paranız bileşik faiz ile <strong style={{ color: C.cyan }}>
                %{((futureValue / totalInvested - 1) * 100).toFixed(0)}
              </strong> büyüyor ({years} yıl)
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
