"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Users,
  Send,
  Loader2,
  X,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  Lightbulb,
  History,
  Trash2,
} from "lucide-react";
import { apiFetch } from "@/lib/api";


const C = {
  bg: "#08080e",
  card: "#111118",
  card2: "#1a1a24",
  border: "rgba(255,255,255,0.10)",
  text1: "#f5f5f7",
  text2: "#a1a1a6",
  text3: "#6e6e73",
};

/* Role badge colors */
const ROLE_COLORS: Record<string, string> = {
  CTO: "#0a84ff",
  CPO: "#bf5af2",
  CMO: "#ff9f0a",
  "Senior Developer": "#30d158",
  "Frontend Developer": "#00d4ff",
  "AI/ML Developer": "#ff375f",
  "DevOps Engineer": "#ffd60a",
  "Growth Marketer": "#ff6961",
  "Content Strategist": "#5ac8fa",
  "Business Development": "#30b0c7",
  "Competitive Intelligence": "#ff9f0a",
  "QA/Test Engineer": "#34c759",
  "Code Reviewer": "#af52de",
  "Project Manager": "#0a84ff",
  "Customer Success": "#32d74b",
};

/* ─── Types ─────────────────────────────────────────────────────── */
interface AdvisorInfo {
  name: string;
  role: string;
  description: string;
}

interface AdvisoryResponse {
  advisor: string;
  role: string;
  question: string;
  advice: string;
  provider: string;
  latency_ms: number;
  success: boolean;
  history_used?: number;
}

interface HistoryMessage {
  role: string;
  content: string;
  ts: number;
}

/* ─── Advisor Card ──────────────────────────────────────────────── */
function AdvisorCard({
  advisor,
  onSelect,
}: {
  advisor: AdvisorInfo;
  onSelect: (a: AdvisorInfo) => void;
}) {
  const color = ROLE_COLORS[advisor.role] || "#00d4ff";
  return (
    <button
      onClick={() => onSelect(advisor)}
      style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: 12,
        padding: "14px 16px",
        textAlign: "left",
        cursor: "pointer",
        transition: "border-color 0.15s, background 0.15s",
        width: "100%",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLButtonElement).style.borderColor = color + "55";
        (e.currentTarget as HTMLButtonElement).style.background = C.card2;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLButtonElement).style.borderColor = C.border;
        (e.currentTarget as HTMLButtonElement).style.background = C.card;
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: color,
            boxShadow: `0 0 6px ${color}`,
            flexShrink: 0,
          }}
        />
        <span style={{ fontSize: 12, fontWeight: 700, color, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          {advisor.role}
        </span>
        <ChevronRight size={12} color={C.text3} style={{ marginLeft: "auto" }} />
      </div>
      <p style={{ fontSize: 12, color: C.text2, margin: 0, lineHeight: 1.45 }}>
        {advisor.description}
      </p>
    </button>
  );
}

/* ─── Ask Dialog ────────────────────────────────────────────────── */
function AskDialog({
  advisor,
  onClose,
}: {
  advisor: AdvisorInfo;
  onClose: () => void;
}) {
  const color = ROLE_COLORS[advisor.role] || "#00d4ff";
  const [question, setQuestion] = useState("");
  const [context, setContext] = useState("");
  const [response, setResponse] = useState<AdvisoryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<HistoryMessage[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const res = await apiFetch(`/api/v1/advisory/${advisor.name}/history?limit=10`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data.messages || []);
      }
    } catch {
      /* silent */
    } finally {
      setHistoryLoading(false);
    }
  }, [advisor.name]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const clearHistoryServer = async () => {
    try {
      await apiFetch(`/api/v1/advisory/${advisor.name}/history`, { method: "DELETE" });
      setHistory([]);
    } catch {
      /* silent */
    }
  };

  const submit = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError("");
    setResponse(null);
    try {
      const res = await apiFetch(`/api/v1/advisory/${advisor.name}`, {
        method: "POST",
        body: JSON.stringify({ question: question.trim(), context_str: context.trim(), symbols: [] }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data: AdvisoryResponse = await res.json();
      setResponse(data);
      setQuestion("");
      fetchHistory();
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.75)",
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        style={{
          background: "#13131c",
          border: `1px solid ${color}33`,
          borderRadius: 16,
          padding: 24,
          width: "100%",
          maxWidth: 600,
          maxHeight: "85vh",
          overflowY: "auto",
          boxShadow: `0 0 40px ${color}22`,
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: color, boxShadow: `0 0 8px ${color}` }} />
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: C.text1 }}>{advisor.role}</div>
              <div style={{ fontSize: 11, color: C.text3 }}>{advisor.description}</div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", cursor: "pointer", color: C.text3, padding: 4 }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Question input */}
        <div style={{ marginBottom: 12 }}>
          <label style={{ fontSize: 11, color: C.text3, display: "block", marginBottom: 6 }}>Soru</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={`${advisor.role} danışmanına sorunuzu yazın...`}
            rows={3}
            style={{
              width: "100%",
              background: "#0a0a0f",
              border: `1px solid ${C.border}`,
              borderRadius: 8,
              padding: "10px 12px",
              color: C.text1,
              fontSize: 13,
              resize: "vertical",
              boxSizing: "border-box",
              outline: "none",
              fontFamily: "inherit",
            }}
            onKeyDown={(e) => { if (e.key === "Enter" && e.ctrlKey) submit(); }}
          />
        </div>

        {/* Optional context */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontSize: 11, color: C.text3, display: "block", marginBottom: 6 }}>
            Bağlam (isteğe bağlı)
          </label>
          <textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Ek bağlam, kod parçası, piyasa verisi..."
            rows={2}
            style={{
              width: "100%",
              background: "#0a0a0f",
              border: `1px solid ${C.border}`,
              borderRadius: 8,
              padding: "8px 12px",
              color: C.text2,
              fontSize: 12,
              resize: "vertical",
              boxSizing: "border-box",
              outline: "none",
              fontFamily: "inherit",
            }}
          />
        </div>

        {/* Submit button */}
        <button
          onClick={submit}
          disabled={loading || !question.trim()}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            background: loading || !question.trim() ? "rgba(255,255,255,0.05)" : `${color}22`,
            border: `1px solid ${loading || !question.trim() ? C.border : color + "55"}`,
            borderRadius: 8,
            padding: "9px 18px",
            color: loading || !question.trim() ? C.text3 : color,
            fontSize: 13,
            fontWeight: 600,
            cursor: loading || !question.trim() ? "not-allowed" : "pointer",
            marginBottom: 16,
          }}
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          {loading ? "Yanıt alınıyor..." : "Sor (Ctrl+Enter)"}
        </button>

        {/* Error */}
        {error && (
          <div style={{ display: "flex", alignItems: "flex-start", gap: 8, background: "rgba(255,69,58,0.1)", border: "1px solid rgba(255,69,58,0.3)", borderRadius: 8, padding: "10px 12px", marginBottom: 16 }}>
            <AlertCircle size={14} color="#ff453a" style={{ flexShrink: 0, marginTop: 1 }} />
            <span style={{ fontSize: 12, color: "#ff453a" }}>{error}</span>
          </div>
        )}

        {/* History block (sliding window) */}
        {(history.length > 0 || historyLoading) && (
          <div
            style={{
              background: "#0e0e18",
              border: `1px solid ${C.border}`,
              borderRadius: 10,
              padding: 12,
              marginBottom: 16,
              maxHeight: 240,
              overflowY: "auto",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 8,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <History size={12} color={C.text3} />
                <span style={{ fontSize: 11, color: C.text3, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Geçmiş ({history.length})
                </span>
              </div>
              {history.length > 0 && (
                <button
                  onClick={clearHistoryServer}
                  title="Geçmişi sil"
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    color: C.text3,
                    padding: 2,
                    display: "flex",
                    alignItems: "center",
                  }}
                >
                  <Trash2 size={12} />
                </button>
              )}
            </div>
            {historyLoading && (
              <div style={{ fontSize: 11, color: C.text3 }}>Yükleniyor…</div>
            )}
            {history.map((m, i) => {
              const isUser = m.role === "user";
              return (
                <div
                  key={i}
                  style={{
                    fontSize: 12,
                    color: isUser ? C.text1 : C.text2,
                    background: isUser ? "rgba(255,255,255,0.03)" : "transparent",
                    padding: "6px 10px",
                    borderLeft: `2px solid ${isUser ? color + "55" : "transparent"}`,
                    marginBottom: 4,
                    whiteSpace: "pre-wrap",
                    lineHeight: 1.5,
                  }}
                >
                  <span style={{ fontSize: 10, color: C.text3, marginRight: 6 }}>
                    {isUser ? "Sen" : advisor.role}:
                  </span>
                  {m.content}
                </div>
              );
            })}
          </div>
        )}

        {/* Response */}
        {response && (
          <div style={{ background: "#0e0e18", border: `1px solid ${color}33`, borderRadius: 10, padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
              <CheckCircle2 size={14} color="#30d158" />
              <span style={{ fontSize: 12, color: C.text2 }}>
                {response.provider} · {Math.round(response.latency_ms)}ms
              </span>
            </div>
            <div style={{ fontSize: 13, color: C.text1, lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
              {response.advice}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Main Page ─────────────────────────────────────────────────── */
export default function AdvisoryPage() {
  const [advisors, setAdvisors] = useState<AdvisorInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<AdvisorInfo | null>(null);

  const fetchAdvisors = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/v1/advisory/`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setAdvisors(await res.json());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAdvisors(); }, [fetchAdvisors]);

  return (
    <div style={{ background: C.bg, minHeight: "100vh", color: C.text1, padding: "24px 20px" }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
          <Users size={22} color="#bf5af2" />
          <h1 style={{ fontSize: 22, fontWeight: 700, color: C.text1, margin: 0 }}>Advisory Panel</h1>
        </div>
        <p style={{ fontSize: 13, color: C.text2, margin: 0 }}>
          15 uzman danışman agent — stratejik sorularınızı yanıtlar
        </p>
      </div>

      {/* Info banner */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, background: "rgba(191,90,242,0.08)", border: "1px solid rgba(191,90,242,0.2)", borderRadius: 10, padding: "10px 16px", marginBottom: 24 }}>
        <Lightbulb size={14} color="#bf5af2" />
        <span style={{ fontSize: 12, color: C.text2 }}>
          Bir danışman seçin, sorunuzu yazın — yapay zeka uzman perspektifinden yanıt verir.
        </span>
      </div>

      {loading && (
        <div style={{ display: "flex", alignItems: "center", gap: 10, color: C.text2 }}>
          <Loader2 size={18} className="animate-spin" /> Danışmanlar yükleniyor…
        </div>
      )}

      {error && (
        <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#ff453a", fontSize: 13 }}>
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {!loading && !error && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
            gap: 12,
          }}
        >
          {advisors.map((a) => (
            <AdvisorCard key={a.name} advisor={a} onSelect={setSelected} />
          ))}
        </div>
      )}

      {selected && (
        <AskDialog advisor={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
