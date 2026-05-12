"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  BookmarkCheck,
  Trash2,
  ArrowLeft,
  BookOpen,
  Bookmark,
} from "lucide-react";
import { C } from "@/lib/stockData";

const purple = "#a78bfa";

interface DictEntry {
  slug: string;
  term: string;
  term_en?: string;
  definition: string;
  category: string;
  level: string;
  tags?: string[];
  simple_explanation?: string;
  why_important?: string;
}

const LEVEL_COLOR: Record<string, string> = {
  Başlangıç: C.green,
  Orta: C.yellow,
  İleri: C.cyan,
  Uzman: C.purple,
};

export default function SavedPage() {
  const router = useRouter();
  const [allTerms, setAllTerms] = useState<DictEntry[]>([]);
  const [saved, setSaved] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  // Load dictionary
  useEffect(() => {
    fetch("/dictionary.json")
      .then((r) => r.json())
      .then((data: DictEntry[]) => {
        setAllTerms(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Load saved slugs from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem("finsense_saved");
      setSaved(raw ? JSON.parse(raw) : []);
    } catch {
      setSaved([]);
    }
  }, []);

  const savedTerms = allTerms.filter((t) => saved.includes(t.slug));

  function removeSaved(slug: string) {
    const next = saved.filter((s) => s !== slug);
    setSaved(next);
    localStorage.setItem("finsense_saved", JSON.stringify(next));
  }

  function clearAll() {
    setSaved([]);
    localStorage.removeItem("finsense_saved");
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
      {/* Header */}
      <div
        style={{
          maxWidth: 1100,
          margin: "0 auto",
        }}
      >
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
          <span style={{ color: purple, fontWeight: 600, fontSize: 14 }}>
            Kaydedilenler
          </span>
        </div>

        {/* Title row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 32,
            flexWrap: "wrap",
            gap: 16,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 14,
                background: `${purple}22`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <BookmarkCheck size={24} color={purple} />
            </div>
            <div>
              <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>
                Kayıtlı Terimlerim
              </h1>
              <p style={{ color: C.text2, fontSize: 14, margin: "4px 0 0" }}>
                {loading
                  ? "Yükleniyor…"
                  : `${savedTerms.length} terim kaydedildi`}
              </p>
            </div>
          </div>

          {savedTerms.length > 0 && (
            <button
              onClick={clearAll}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                color: C.red,
                background: `${C.red}15`,
                border: `1px solid ${C.red}40`,
                borderRadius: 10,
                padding: "8px 16px",
                fontSize: 13,
                cursor: "pointer",
                fontWeight: 500,
                transition: "background 0.15s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.background = `${C.red}25`)
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.background = `${C.red}15`)
              }
            >
              <Trash2 size={14} />
              Tümünü Temizle
            </button>
          )}
        </div>

        {/* Empty state */}
        {!loading && savedTerms.length === 0 && (
          <div
            style={{
              textAlign: "center",
              padding: "80px 24px",
              borderRadius: 20,
              background: C.card,
              border: `1px solid ${C.border}`,
            }}
          >
            <Bookmark size={48} color={C.text3} style={{ marginBottom: 16 }} />
            <h2
              style={{
                fontSize: 20,
                fontWeight: 600,
                color: C.text1,
                marginBottom: 8,
              }}
            >
              Henüz kayıtlı terim yok
            </h2>
            <p style={{ color: C.text2, marginBottom: 28, maxWidth: 400, margin: "0 auto 28px" }}>
              Sözlük sekmesinde terimlerin üzerindeki{" "}
              <BookmarkCheck
                size={14}
                color={purple}
                style={{ verticalAlign: "middle" }}
              />{" "}
              ikonuna basarak buraya ekleyebilirsiniz.
            </p>
            <button
              onClick={() => router.push("/dashboard/finsense")}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                background: purple,
                color: "#fff",
                border: "none",
                borderRadius: 12,
                padding: "12px 24px",
                fontSize: 14,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              <BookOpen size={16} />
              Sözlüğe Git
            </button>
          </div>
        )}

        {/* Terms grid */}
        {savedTerms.length > 0 && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
              gap: 16,
            }}
          >
            {savedTerms.map((t) => (
              <div
                key={t.slug}
                style={{
                  background: C.card,
                  border: `1px solid ${C.border}`,
                  borderRadius: 16,
                  padding: "20px",
                  cursor: "pointer",
                  transition: "border-color 0.2s, transform 0.15s",
                  position: "relative",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = purple;
                  e.currentTarget.style.transform = "translateY(-2px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = C.border;
                  e.currentTarget.style.transform = "translateY(0)";
                }}
                onClick={() =>
                  router.push("/dashboard/finsense/" + t.slug)
                }
              >
                {/* Remove button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeSaved(t.slug);
                  }}
                  style={{
                    position: "absolute",
                    top: 14,
                    right: 14,
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    color: C.text3,
                    padding: 4,
                    borderRadius: 6,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    transition: "color 0.15s",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.color = C.red)
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.color = C.text3)
                  }
                  title="Kaydı kaldır"
                >
                  <Trash2 size={14} />
                </button>

                {/* Level badge */}
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    color: LEVEL_COLOR[t.level] ?? C.text3,
                    background: `${LEVEL_COLOR[t.level] ?? C.text3}18`,
                    padding: "3px 8px",
                    borderRadius: 6,
                    marginBottom: 10,
                    display: "inline-block",
                  }}
                >
                  {t.level}
                </span>

                {/* Term name */}
                <h3
                  style={{
                    fontSize: 16,
                    fontWeight: 700,
                    margin: "8px 0 6px",
                    paddingRight: 24,
                    lineHeight: 1.3,
                  }}
                >
                  {t.term}
                </h3>
                {t.term_en && (
                  <p
                    style={{
                      fontSize: 12,
                      color: C.text3,
                      margin: "0 0 10px",
                    }}
                  >
                    {t.term_en}
                  </p>
                )}

                {/* Simple explanation or definition */}
                <p
                  style={{
                    fontSize: 13,
                    color: C.text2,
                    lineHeight: 1.55,
                    margin: 0,
                    display: "-webkit-box",
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                >
                  {t.simple_explanation ?? t.definition}
                </p>

                {/* Category tag */}
                <div
                  style={{
                    marginTop: 14,
                    fontSize: 11,
                    color: C.text3,
                  }}
                >
                  {t.category}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
