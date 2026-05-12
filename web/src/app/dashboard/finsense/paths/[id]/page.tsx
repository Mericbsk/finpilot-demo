"use client";
import { useState, useEffect, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Circle,
  ChevronRight,
  Trophy,
} from "lucide-react";
import { C } from "@/lib/stockData";

const purple = "#a78bfa";

/* ── Category merge (mirrors page.tsx) ──────────────────────── */
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

/* ── Learning paths (mirrors page.tsx) ──────────────────────── */
const LEARNING_PATHS = [
  { id: "baslangic-101", title: "Yatırıma Başlangıç", icon: "🌱", color: C.green, level: "Başlangıç", duration: "15 dk", category: "Temel Finans Kavramları" },
  { id: "teknik-analiz-101", title: "Teknik Analiz Temelleri", icon: "📊", color: C.cyan, level: "Orta", duration: "20 dk", category: "Teknik Analiz" },
  { id: "risk-yonetimi", title: "Risk Yönetimi", icon: "🛡️", color: C.yellow, level: "Orta", duration: "18 dk", category: "Risk Yönetimi" },
  { id: "portfoy-teorisi", title: "Portföy Teorisi", icon: "🎯", color: purple, level: "İleri", duration: "25 dk", category: "Yatırım ve Portföy" },
  { id: "turev-araclar", title: "Türev Araçlar 101", icon: "⚡", color: C.red, level: "İleri", duration: "22 dk", category: "Türev Araçlar" },
  { id: "makro-101", title: "Makroekonomiye Giriş", icon: "🌍", color: C.blue, level: "Başlangıç", duration: "20 dk", category: "Makroekonomi" },
];

/* ── Level ordering ──────────────────────────────────────────── */
const LEVEL_ORDER: Record<string, number> = {
  Başlangıç: 0,
  Orta: 1,
  İleri: 2,
  Uzman: 3,
};

const LEVEL_COLOR: Record<string, string> = {
  Başlangıç: C.green,
  Orta: C.yellow,
  İleri: C.cyan,
  Uzman: C.purple,
};

interface DictEntry {
  slug: string;
  term: string;
  term_en?: string;
  definition: string;
  category: string;
  level: string;
  tags?: string[];
  simple_explanation?: string;
  difficulty_score?: number;
}

export default function LearningPathPage() {
  const params = useParams();
  const router = useRouter();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;

  const path = LEARNING_PATHS.find((p) => p.id === id);

  const [allTerms, setAllTerms] = useState<DictEntry[]>([]);
  const [completed, setCompleted] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/dictionary.json")
      .then((r) => r.json())
      .then((data: DictEntry[]) => {
        setAllTerms(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Load progress from localStorage
  useEffect(() => {
    if (!id) return;
    try {
      const raw = localStorage.getItem(`finsense_progress_${id}`);
      setCompleted(raw ? JSON.parse(raw) : []);
    } catch {
      setCompleted([]);
    }
  }, [id]);

  // Terms for this path (same category, sorted by difficulty)
  const pathTerms = useMemo(() => {
    if (!path) return [];
    return allTerms
      .filter((t) => normalizeCategory(t.category) === path.category)
      .sort(
        (a, b) =>
          (LEVEL_ORDER[a.level] ?? 0) - (LEVEL_ORDER[b.level] ?? 0)
      );
  }, [allTerms, path]);

  function toggleComplete(slug: string) {
    setCompleted((prev) => {
      const next = prev.includes(slug)
        ? prev.filter((s) => s !== slug)
        : [...prev, slug];
      localStorage.setItem(`finsense_progress_${id}`, JSON.stringify(next));
      return next;
    });
  }

  const completedCount = pathTerms.filter((t) =>
    completed.includes(t.slug)
  ).length;
  const progressPct =
    pathTerms.length > 0
      ? Math.round((completedCount / pathTerms.length) * 100)
      : 0;

  // 404
  if (!loading && !path) {
    return (
      <div
        style={{
          minHeight: "100vh",
          background: C.bg,
          color: C.text1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 16,
        }}
      >
        <p style={{ fontSize: 48 }}>🔍</p>
        <h2 style={{ fontSize: 22, fontWeight: 700 }}>Öğrenme Yolu Bulunamadı</h2>
        <button
          onClick={() => router.push("/dashboard/finsense")}
          style={{
            background: purple,
            color: "#fff",
            border: "none",
            borderRadius: 10,
            padding: "10px 22px",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          FinSense'e Dön
        </button>
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: C.bg,
        color: C.text1,
        padding: "24px",
      }}
    >
      <div style={{ maxWidth: 800, margin: "0 auto" }}>
        {/* Breadcrumb */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginBottom: 28,
          }}
        >
          <button
            onClick={() => router.push("/dashboard/finsense")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              color: C.text2,
              background: "none",
              border: "none",
              cursor: "pointer",
              fontSize: 14,
              padding: "6px 10px",
              borderRadius: 8,
              transition: "background 0.15s",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = C.cardHover)
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "none")
            }
          >
            <ArrowLeft size={16} />
            FinSense Akademi
          </button>
          <span style={{ color: C.text3 }}>/</span>
          <span
            style={{
              color: path?.color ?? purple,
              fontWeight: 600,
              fontSize: 14,
            }}
          >
            {path?.title ?? "Öğrenme Yolu"}
          </span>
        </div>

        {/* Path header */}
        {path && (
          <div
            style={{
              background: C.card,
              border: `1px solid ${path.color}40`,
              borderRadius: 20,
              padding: "28px 32px",
              marginBottom: 28,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 20,
                flexWrap: "wrap",
              }}
            >
              <div
                style={{
                  fontSize: 40,
                  width: 64,
                  height: 64,
                  background: `${path.color}18`,
                  borderRadius: 16,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                {path.icon}
              </div>
              <div style={{ flex: 1 }}>
                <h1 style={{ fontSize: 26, fontWeight: 700, margin: "0 0 6px" }}>
                  {path.title}
                </h1>
                <div
                  style={{
                    display: "flex",
                    gap: 12,
                    flexWrap: "wrap",
                    marginBottom: 20,
                  }}
                >
                  <span
                    style={{
                      fontSize: 12,
                      color: LEVEL_COLOR[path.level] ?? C.text2,
                      background: `${LEVEL_COLOR[path.level] ?? C.text2}18`,
                      padding: "3px 10px",
                      borderRadius: 8,
                      fontWeight: 600,
                    }}
                  >
                    {path.level}
                  </span>
                  <span style={{ fontSize: 12, color: C.text2 }}>
                    ⏱ {path.duration}
                  </span>
                  <span style={{ fontSize: 12, color: C.text2 }}>
                    📚 {pathTerms.length} terim
                  </span>
                </div>

                {/* Progress bar */}
                <div>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: 12,
                      color: C.text2,
                      marginBottom: 6,
                    }}
                  >
                    <span>İlerleme</span>
                    <span
                      style={{
                        color: completedCount === pathTerms.length && pathTerms.length > 0
                          ? C.green
                          : path.color,
                        fontWeight: 600,
                      }}
                    >
                      {completedCount} / {pathTerms.length} tamamlandı
                    </span>
                  </div>
                  <div
                    style={{
                      height: 6,
                      background: `${C.border}`,
                      borderRadius: 3,
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        width: `${progressPct}%`,
                        background:
                          progressPct === 100 ? C.green : path.color,
                        borderRadius: 3,
                        transition: "width 0.4s ease",
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Completion badge */}
            {completedCount === pathTerms.length && pathTerms.length > 0 && (
              <div
                style={{
                  marginTop: 20,
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  background: `${C.green}18`,
                  border: `1px solid ${C.green}40`,
                  borderRadius: 12,
                  padding: "12px 18px",
                }}
              >
                <Trophy size={20} color={C.green} />
                <span style={{ color: C.green, fontWeight: 600, fontSize: 14 }}>
                  Tebrikler! Bu öğrenme yolunu tamamladınız.
                </span>
              </div>
            )}
          </div>
        )}

        {/* Terms list */}
        {loading ? (
          <div style={{ textAlign: "center", padding: 60, color: C.text3 }}>
            Yükleniyor…
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {pathTerms.map((t, i) => {
              const done = completed.includes(t.slug);
              return (
                <div
                  key={t.slug}
                  style={{
                    background: C.card,
                    border: `1px solid ${done ? C.green + "50" : C.border}`,
                    borderRadius: 14,
                    padding: "16px 20px",
                    display: "flex",
                    alignItems: "center",
                    gap: 16,
                    opacity: done ? 0.8 : 1,
                    transition: "border-color 0.2s",
                  }}
                >
                  {/* Step number / check */}
                  <button
                    onClick={() => toggleComplete(t.slug)}
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      padding: 0,
                      flexShrink: 0,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      width: 32,
                      height: 32,
                    }}
                    title={done ? "Tamamlandı olarak işaretle" : "Tamamla"}
                  >
                    {done ? (
                      <CheckCircle2 size={24} color={C.green} />
                    ) : (
                      <div
                        style={{
                          width: 24,
                          height: 24,
                          borderRadius: "50%",
                          border: `2px solid ${C.border}`,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: C.text3,
                          fontSize: 11,
                          fontWeight: 700,
                        }}
                      >
                        {i + 1}
                      </div>
                    )}
                  </button>

                  {/* Term info */}
                  <div
                    style={{ flex: 1, cursor: "pointer" }}
                    onClick={() =>
                      router.push("/dashboard/finsense/" + t.slug)
                    }
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        flexWrap: "wrap",
                        marginBottom: 4,
                      }}
                    >
                      <span
                        style={{
                          fontWeight: 600,
                          fontSize: 15,
                          textDecoration: done ? "line-through" : "none",
                          color: done ? C.text3 : C.text1,
                        }}
                      >
                        {t.term}
                      </span>
                      <span
                        style={{
                          fontSize: 11,
                          color: LEVEL_COLOR[t.level] ?? C.text3,
                          background: `${LEVEL_COLOR[t.level] ?? C.text3}18`,
                          padding: "2px 8px",
                          borderRadius: 6,
                          fontWeight: 600,
                        }}
                      >
                        {t.level}
                      </span>
                    </div>
                    <p
                      style={{
                        fontSize: 13,
                        color: C.text2,
                        margin: 0,
                        lineHeight: 1.5,
                        display: "-webkit-box",
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden",
                      }}
                    >
                      {t.simple_explanation ?? t.definition}
                    </p>
                  </div>

                  {/* Open link */}
                  <button
                    onClick={() =>
                      router.push("/dashboard/finsense/" + t.slug)
                    }
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      color: C.text3,
                      flexShrink: 0,
                      padding: 4,
                      borderRadius: 6,
                      display: "flex",
                      alignItems: "center",
                      transition: "color 0.15s",
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.color = path?.color ?? purple)
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.color = C.text3)
                    }
                    title="Terimi aç"
                  >
                    <ChevronRight size={18} />
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* Empty state */}
        {!loading && pathTerms.length === 0 && (
          <div
            style={{
              textAlign: "center",
              padding: 60,
              background: C.card,
              borderRadius: 16,
              border: `1px solid ${C.border}`,
            }}
          >
            <BookOpen size={40} color={C.text3} style={{ marginBottom: 12 }} />
            <p style={{ color: C.text2, fontSize: 14 }}>
              Bu kategori için henüz terim bulunamadı.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
