"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  ArrowLeft,
  BookOpen,
  Bookmark,
  BookmarkCheck,
  Globe,
  Link2,
  Lightbulb,
  AlertTriangle,
  Layers,
  Tag,
  ExternalLink,
  Brain,
} from "lucide-react";
import { C } from "@/lib/stockData";

const purple = "#a78bfa";

interface DictEntry {
  slug: string;
  term: string;
  term_en?: string;
  term_de?: string;
  definition: string;
  definition_en?: string;
  example?: string;
  example_en?: string;
  category: string;
  level: string;
  related?: string[];
  formula?: string;
  tags?: string[];
  synonyms?: string[];
  difficulty_score?: number;
  source?: string;
  simple_explanation?: string;
  why_important?: string;
  common_mistake?: string;
  finpilot_usage?: string[];
}

function levelColor(level: string): { color: string; bg: string } {
  const l = level.toLowerCase();
  if (l.includes("başlangıç")) return { color: C.green, bg: "rgba(48,209,88,0.12)" };
  if (l.includes("orta")) return { color: C.cyan, bg: "rgba(0,212,255,0.12)" };
  if (l.includes("ileri")) return { color: C.yellow, bg: "rgba(255,214,10,0.12)" };
  if (l.includes("uzman")) return { color: purple, bg: "rgba(167,139,250,0.12)" };
  return { color: C.text3, bg: "rgba(255,255,255,0.05)" };
}

const FINPILOT_PAGE_LABELS: Record<string, { label: string; href: string }> = {
  scanner: { label: "Tarayıcı", href: "/dashboard/scanner" },
  analysis: { label: "Analiz", href: "/dashboard/analysis" },
  portfolio: { label: "Portföy", href: "/dashboard/portfolio" },
  "ai-lab": { label: "AI Lab", href: "/dashboard/ai-lab" },
  backtest: { label: "Backtest", href: "/dashboard/backtest" },
};

export default function TermDetailPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params?.slug as string;

  const [allTerms, setAllTerms] = useState<DictEntry[]>([]);
  const [entry, setEntry] = useState<DictEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [lang, setLang] = useState<"tr" | "en">("tr");
  const [saved, setSaved] = useState<string[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [aiResult, setAiResult] = useState<{ simple_explanation: string; why_important: string; common_mistake: string } | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  useEffect(() => {
    const s = JSON.parse(localStorage.getItem("finsense_saved") || "[]");
    setSaved(s);
  }, []);

  useEffect(() => {
    fetch("/dictionary.json")
      .then((r) => r.json())
      .then((data: DictEntry[]) => {
        setAllTerms(data);
        const found = data.find((t) => t.slug === slug);
        setEntry(found ?? null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [slug]);

  function toggleSave() {
    const next = saved.includes(slug)
      ? saved.filter((s) => s !== slug)
      : [...saved, slug];
    setSaved(next);
    localStorage.setItem("finsense_saved", JSON.stringify(next));
  }

  function navigateTo(relSlug: string) {
    router.push(`/dashboard/finsense/${relSlug}`);
  }

  async function handleAiExplain() {
    if (aiLoading || !slug) return;
    setAiLoading(true);
    setAiError(null);
    try {
      const res = await fetch(`/py-api/ai/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug, lang }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as { detail?: string }).detail ?? `HTTP ${res.status}`);
      }
      const data = await res.json();
      setAiResult({
        simple_explanation: data.simple_explanation,
        why_important: data.why_important,
        common_mistake: data.common_mistake,
      });
    } catch (e: unknown) {
      setAiError(e instanceof Error ? e.message : "Bir hata oluştu.");
    } finally {
      setAiLoading(false);
    }
  }

  const isSaved = saved.includes(slug);
  const lc = entry ? levelColor(entry.level) : { color: C.text3, bg: "transparent" };
  const name = lang === "en" && entry?.term_en ? entry.term_en : entry?.term ?? "";
  const definition = lang === "en" && entry?.definition_en ? entry.definition_en : entry?.definition ?? "";
  const example = lang === "en" && entry?.example_en ? entry.example_en : entry?.example ?? "";

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: 300, color: C.text3 }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>📖</div>
          <p style={{ fontSize: 13 }}>Yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (!entry) {
    return (
      <div style={{ maxWidth: 700, margin: "0 auto", padding: "40px 16px" }}>
        <button
          onClick={() => router.back()}
          style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: C.text3, background: "none", border: "none", cursor: "pointer", marginBottom: 32 }}
        >
          <ArrowLeft size={14} /> Geri
        </button>
        <div style={{ textAlign: "center", padding: 48, borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text1, marginBottom: 8 }}>Terim bulunamadı</h2>
          <p style={{ fontSize: 13, color: C.text3 }}>"{slug}" sözlükte mevcut değil.</p>
          <button
            onClick={() => router.push("/dashboard/finsense")}
            style={{ marginTop: 20, borderRadius: 10, padding: "10px 24px", fontSize: 13, fontWeight: 600, color: "#000", background: `linear-gradient(135deg, ${C.cyan}, ${C.blue})`, border: "none", cursor: "pointer" }}
          >
            Sözlüğe Dön
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 760, margin: "0 auto", padding: "0 16px 64px" }}>
      {/* Breadcrumb */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 24, fontSize: 11, color: C.text3 }}>
        <button onClick={() => router.push("/dashboard/finsense")} style={{ background: "none", border: "none", cursor: "pointer", color: C.cyan, fontSize: 11 }}>
          FinSense
        </button>
        <span>›</span>
        <button
          onClick={() => { router.push("/dashboard/finsense"); }}
          style={{ background: "none", border: "none", cursor: "pointer", color: C.text3, fontSize: 11 }}
        >
          {entry.category}
        </button>
        <span>›</span>
        <span style={{ color: C.text2 }}>{entry.term.split("(")[0].trim()}</span>
      </div>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
          <div style={{ flex: 1 }}>
            <h1 style={{ fontSize: 26, fontWeight: 700, color: C.text1, lineHeight: 1.3, marginBottom: 6 }}>
              {name}
            </h1>
            {lang === "tr" && entry.term_en && (
              <p style={{ fontSize: 13, color: C.text3 }}>
                <Globe size={11} style={{ display: "inline", marginRight: 4 }} />
                {entry.term_en}
              </p>
            )}
          </div>
          <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
            {/* TR/EN toggle */}
            <button
              onClick={() => setLang(lang === "tr" ? "en" : "tr")}
              style={{ borderRadius: 8, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: "6px 10px", fontSize: 11, fontWeight: 600, color: C.text2, cursor: "pointer" }}
            >
              {lang === "tr" ? "🇹🇷 TR" : "🇺🇸 EN"}
            </button>
            {/* Save */}
            <button
              onClick={toggleSave}
              style={{ borderRadius: 8, border: `1px solid ${isSaved ? C.yellow : C.border}`, backgroundColor: isSaved ? "rgba(255,214,10,0.08)" : C.card, padding: "6px 10px", fontSize: 11, fontWeight: 600, color: isSaved ? C.yellow : C.text3, cursor: "pointer", display: "flex", alignItems: "center", gap: 4 }}
            >
              {isSaved ? <BookmarkCheck size={13} /> : <Bookmark size={13} />}
              {isSaved ? "Kaydedildi" : "Kaydet"}
            </button>
          </div>
        </div>

        {/* Badges */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 12 }}>
          <span style={{ borderRadius: 8, backgroundColor: lc.bg, padding: "4px 10px", fontSize: 11, fontWeight: 600, color: lc.color }}>
            {entry.level}
          </span>
          <span style={{ borderRadius: 8, backgroundColor: C.primary, padding: "4px 10px", fontSize: 11, color: C.text3 }}>
            {entry.category}
          </span>
          {entry.difficulty_score !== undefined && (
            <span style={{ borderRadius: 8, backgroundColor: C.primary, padding: "4px 10px", fontSize: 11, color: C.text3 }}>
              ⚡ {entry.difficulty_score}/10
            </span>
          )}
          {entry.synonyms && entry.synonyms.length > 0 && (
            <span style={{ borderRadius: 8, backgroundColor: C.primary, padding: "4px 10px", fontSize: 11, color: C.text3 }}>
              ≈ {entry.synonyms.slice(0, 2).join(", ")}
            </span>
          )}
        </div>
      </div>

      {/* Simple explanation (if available, shown first) */}
      {entry.simple_explanation && (
        <div style={{ borderRadius: 14, padding: 20, marginBottom: 16, border: `1px solid rgba(0,212,255,0.2)`, backgroundColor: "rgba(0,212,255,0.04)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
            <Lightbulb size={13} style={{ color: C.cyan }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: C.cyan, textTransform: "uppercase", letterSpacing: "0.05em" }}>Kısaca</span>
          </div>
          <p style={{ fontSize: 14, color: C.text1, lineHeight: 1.7 }}>{entry.simple_explanation}</p>
        </div>
      )}

      {/* Main definition */}
      <div style={{ borderRadius: 14, padding: 20, marginBottom: 16, border: `1px solid ${C.border}`, backgroundColor: C.card }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <BookOpen size={13} style={{ color: C.text3 }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: C.text3, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              {entry.simple_explanation ? "Teknik Tanım" : "Tanım"}
            </span>
          </div>
          {entry.simple_explanation && (
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              style={{ fontSize: 10, color: C.cyan, background: "none", border: "none", cursor: "pointer" }}
            >
              {showAdvanced ? "Daha az göster ▲" : "Teknik detay ▼"}
            </button>
          )}
        </div>
        {(!entry.simple_explanation || showAdvanced) && (
          <p style={{ fontSize: 14, color: C.text2, lineHeight: 1.75 }}>{definition}</p>
        )}
        {entry.simple_explanation && !showAdvanced && (
          <p style={{ fontSize: 13, color: C.text3, fontStyle: "italic" }}>Teknik tanımı görmek için "Teknik detay ▼" butonuna tıklayın.</p>
        )}
      </div>

      {/* Formula */}
      {entry.formula && (
        <div style={{ borderRadius: 14, padding: 16, marginBottom: 16, border: `1px solid rgba(167,139,250,0.2)`, backgroundColor: "rgba(167,139,250,0.05)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
            <Layers size={13} style={{ color: purple }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: purple, textTransform: "uppercase", letterSpacing: "0.05em" }}>Formül</span>
          </div>
          <code style={{ fontSize: 13, color: purple, fontFamily: "monospace", lineHeight: 1.6 }}>{entry.formula}</code>
        </div>
      )}

      {/* Example */}
      {example && (
        <div style={{ borderRadius: 14, padding: 18, marginBottom: 16, border: `1px solid rgba(255,214,10,0.15)`, backgroundColor: "rgba(255,214,10,0.04)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
            <Lightbulb size={13} style={{ color: C.yellow }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: C.yellow, textTransform: "uppercase", letterSpacing: "0.05em" }}>Gerçek Örnek</span>
          </div>
          <p style={{ fontSize: 13, color: C.text2, lineHeight: 1.7, fontStyle: "italic" }}>{example}</p>
        </div>
      )}

      {/* Why important */}
      {entry.why_important && (
        <div style={{ borderRadius: 14, padding: 18, marginBottom: 16, border: `1px solid rgba(48,209,88,0.15)`, backgroundColor: "rgba(48,209,88,0.04)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
            <span style={{ fontSize: 13 }}>🎯</span>
            <span style={{ fontSize: 11, fontWeight: 700, color: C.green, textTransform: "uppercase", letterSpacing: "0.05em" }}>Neden Önemli?</span>
          </div>
          <p style={{ fontSize: 13, color: C.text2, lineHeight: 1.7 }}>{entry.why_important}</p>
        </div>
      )}

      {/* Common mistake */}
      {entry.common_mistake && (
        <div style={{ borderRadius: 14, padding: 18, marginBottom: 16, border: `1px solid rgba(255,69,58,0.2)`, backgroundColor: "rgba(255,69,58,0.04)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
            <AlertTriangle size={13} style={{ color: C.red }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: C.red, textTransform: "uppercase", letterSpacing: "0.05em" }}>Sık Yapılan Hata</span>
          </div>
          <p style={{ fontSize: 13, color: C.text2, lineHeight: 1.7 }}>{entry.common_mistake}</p>
        </div>
      )}

      {/* FinPilot usage */}
      {entry.finpilot_usage && entry.finpilot_usage.length > 0 && (
        <div style={{ borderRadius: 14, padding: 18, marginBottom: 16, border: `1px solid rgba(0,212,255,0.15)`, backgroundColor: "rgba(0,212,255,0.04)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
            <ExternalLink size={13} style={{ color: C.cyan }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: C.cyan, textTransform: "uppercase", letterSpacing: "0.05em" }}>FinPilot'ta Nerede Kullanılır?</span>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {entry.finpilot_usage.map((page) => {
              const info = FINPILOT_PAGE_LABELS[page];
              return info ? (
                <a
                  key={page}
                  href={info.href}
                  style={{ borderRadius: 8, backgroundColor: "rgba(0,212,255,0.08)", padding: "6px 12px", fontSize: 12, color: C.cyan, textDecoration: "none", border: `1px solid rgba(0,212,255,0.2)` }}
                >
                  → {info.label}
                </a>
              ) : null;
            })}
          </div>
        </div>
      )}

      {/* Tags */}
      {entry.tags && entry.tags.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 20 }}>
          <Tag size={11} style={{ color: C.text3, marginTop: 4 }} />
          {entry.tags.map((tag) => (
            <span key={tag} style={{ borderRadius: 6, backgroundColor: "rgba(255,214,10,0.07)", padding: "3px 8px", fontSize: 10, color: C.yellow }}>
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* Related terms */}
      {entry.related && entry.related.length > 0 && (
        <div style={{ borderRadius: 14, padding: 20, marginBottom: 16, border: `1px solid ${C.border}`, backgroundColor: C.card }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 14 }}>
            <Link2 size={13} style={{ color: C.text3 }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: C.text3, textTransform: "uppercase", letterSpacing: "0.05em" }}>İlgili Kavramlar</span>
          </div>
          <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))" }}>
            {entry.related.map((relSlug) => {
              const relEntry = allTerms.find((t) => t.slug === relSlug || t.term.toLowerCase() === relSlug.toLowerCase());
              const displayName = relEntry ? relEntry.term.split("(")[0].trim() : relSlug;
              return (
                <button
                  key={relSlug}
                  onClick={() => navigateTo(relEntry?.slug ?? relSlug)}
                  style={{
                    borderRadius: 10, border: `1px solid ${C.border}`, backgroundColor: C.primary,
                    padding: "10px 12px", textAlign: "left", cursor: "pointer",
                    fontSize: 11, color: C.cyan, transition: "all 0.15s",
                  }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.borderColor = C.cyan; (e.currentTarget as HTMLButtonElement).style.backgroundColor = "rgba(0,212,255,0.06)"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.borderColor = C.border; (e.currentTarget as HTMLButtonElement).style.backgroundColor = C.primary; }}
                >
                  {displayName}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* AI Explain */}
      <div style={{ borderRadius: 14, padding: 20, border: `1px solid ${aiResult ? purple + "50" : C.border}`, backgroundColor: `${purple}05`, transition: "border-color 0.3s" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
          <Brain size={14} style={{ color: purple }} />
          <span style={{ fontSize: 11, fontWeight: 700, color: purple, textTransform: "uppercase", letterSpacing: "0.05em" }}>AI Açıklayıcı</span>
        </div>

        {!aiResult && !aiLoading && (
          <>
            <p style={{ fontSize: 12, color: C.text2, marginBottom: 14 }}>
              Bu kavramı AI ile daha sade dilde açıklayın.
            </p>
            <button
              onClick={handleAiExplain}
              style={{
                display: "inline-flex", alignItems: "center", gap: 6,
                background: `${purple}18`, border: `1px solid ${purple}40`,
                color: purple, borderRadius: 8, padding: "8px 16px",
                fontSize: 12, fontWeight: 600, cursor: "pointer",
                transition: "background 0.15s",
              }}
              onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = `${purple}30`)}
              onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = `${purple}18`)}
            >
              <Brain size={13} />
              AI ile Açıkla
            </button>
          </>
        )}

        {aiLoading && (
          <p style={{ fontSize: 13, color: C.text2, animation: "pulse 1s infinite" }}>
            ✨ Açıklama üretiliyor…
          </p>
        )}

        {aiError && (
          <p style={{ fontSize: 12, color: C.red, marginTop: 8 }}>
            ⚠️ {aiError}
          </p>
        )}

        {aiResult && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 4 }}>
            {[
              { label: "💡 Sade Açıklama", text: aiResult.simple_explanation, color: C.cyan },
              { label: "🎯 Neden Önemli?", text: aiResult.why_important, color: C.green },
              { label: "⚠️ Sık Yapılan Hata", text: aiResult.common_mistake, color: C.yellow },
            ].map(({ label, text, color }) => (
              <div key={label} style={{ borderLeft: `3px solid ${color}`, paddingLeft: 12 }}>
                <p style={{ fontSize: 11, fontWeight: 700, color, margin: "0 0 4px", textTransform: "uppercase", letterSpacing: "0.04em" }}>{label}</p>
                <p style={{ fontSize: 13, color: C.text1, margin: 0, lineHeight: 1.6 }}>{text}</p>
              </div>
            ))}
            <button
              onClick={() => { setAiResult(null); setAiError(null); }}
              style={{ alignSelf: "flex-start", background: "none", border: "none", color: C.text3, fontSize: 11, cursor: "pointer", padding: 0 }}
            >
              Tekrar üret
            </button>
          </div>
        )}
      </div>

      {/* Bottom nav */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 32 }}>
        <button
          onClick={() => router.back()}
          style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: C.text3, background: "none", border: "none", cursor: "pointer" }}
        >
          <ArrowLeft size={14} /> Geri
        </button>
        <button
          onClick={() => router.push("/dashboard/finsense")}
          style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: C.cyan, background: "none", border: "none", cursor: "pointer" }}
        >
          Sözlüğe Dön <ExternalLink size={12} />
        </button>
      </div>
    </div>
  );
}
