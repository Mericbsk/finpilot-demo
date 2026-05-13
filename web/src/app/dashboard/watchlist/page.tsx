"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  Star,
  Plus,
  X,
  Download,
  Play,
  TrendingUp,
  TrendingDown,
  Search,
  BarChart3,
  ExternalLink,
  RefreshCw,
  Eye,
  Trash2,
  Target,
  CheckCircle2,
  XCircle,
  Clock,
  BookmarkX,
  AlertTriangle,
  Activity,
  Bookmark,
  History,
  ChevronDown,
  ChevronRight,
  SlidersHorizontal,
  MessageSquare,
  Tag,
  Zap,
} from "lucide-react";
import { C, hashStr, seededRandom, genStock, companyNames, genSparkline, withLivePrice } from "@/lib/stockData";
import { useStockPrices } from "@/lib/useStockPrices";
import { getCurrencySymbol } from "@/lib/userSettings";
import DemoBanner from "@/components/DemoBanner";

/* ══════════════════════════════════════════════════════════════
   SINYAL TAKİP — types & helpers
══════════════════════════════════════════════════════════════ */
type LifecycleStatus = "new" | "watching" | "active" | "resolved_win" | "resolved_loss" | "expired" | "cancelled";

interface TrackedSignal {
  id: string;
  symbol: string;
  signal: string;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  score: number;
  regime: string;
  sentiment: string;
  risk_reward: number;
  reason: string;
  explanation: string;
  added_at: string;
  signal_date: string;
  status_lifecycle: LifecycleStatus;
  notes: string;
  tags: string[];
  source_model: string;
  current_price: number;
  change_pct: number;
  pnl_pct: number;
  status: "On Track" | "Stop Hit" | "TP Hit" | "Watching" | "Pending";
}

const LIFECYCLE_CONFIG: Record<LifecycleStatus, { label: string; color: string; bg: string; icon: React.ReactNode; pulse?: boolean }> = {
  new:           { label: "Yeni",         color: "#0a84ff", bg: "rgba(10,132,255,0.15)",   icon: <Zap size={10} />, pulse: true },
  watching:      { label: "İzleniyor",    color: C.cyan,    bg: "rgba(0,212,255,0.12)",    icon: <Eye size={10} /> },
  active:        { label: "Aktif",        color: C.green,   bg: "rgba(48,209,88,0.15)",    icon: <CheckCircle2 size={10} /> },
  resolved_win:  { label: "Başarılı ✓",  color: "#ffd60a", bg: "rgba(255,214,10,0.15)",   icon: <Target size={10} /> },
  resolved_loss: { label: "Başarısız ✗", color: C.red,     bg: "rgba(255,69,58,0.15)",    icon: <XCircle size={10} /> },
  expired:       { label: "Süresi Doldu",color: C.text3,   bg: "rgba(161,161,166,0.12)",  icon: <Clock size={10} /> },
  cancelled:     { label: "İptal",        color: "#636366", bg: "rgba(99,99,102,0.15)",    icon: <X size={10} /> },
};

function LifecycleBadge({ status }: { status: LifecycleStatus }) {
  const c = LIFECYCLE_CONFIG[status] ?? LIFECYCLE_CONFIG.watching;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "3px 8px", borderRadius: 6, fontSize: 10, fontWeight: 700, background: c.bg, color: c.color, whiteSpace: "nowrap" }}>
      {c.icon} {c.label}
    </span>
  );
}

/* Signal Detail Drawer */
function SignalDrawer({ item, onClose, onLifecycleChange, onNoteChange, onDelete }: {
  item: TrackedSignal;
  onClose: () => void;
  onLifecycleChange: (id: string, status: LifecycleStatus) => void;
  onNoteChange: (id: string, notes: string, tags: string[]) => void;
  onDelete: (symbol: string) => void;
}) {
  const [notes, setNotes] = useState(item.notes ?? "");
  const [tagsInput, setTagsInput] = useState((item.tags ?? []).join(", "));
  const [saving, setSaving] = useState(false);
  const [savedOk, setSavedOk] = useState(false);

  const saveNote = async () => {
    setSaving(true);
    const tags = tagsInput.split(",").map((t) => t.trim()).filter(Boolean);
    try {
      const res = await fetch(`/py-api/watchlist/${item.id}/note`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes, tags }),
      });
      if (res.ok) {
        onNoteChange(item.id, notes, tags);
        setSavedOk(true);
        setTimeout(() => setSavedOk(false), 2000);
      }
    } catch { /* silent */ }
    finally { setSaving(false); }
  };

  const changeLifecycle = async (newStatus: LifecycleStatus) => {
    try {
      const res = await fetch(`/py-api/watchlist/${item.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status_lifecycle: newStatus }),
      });
      if (res.ok) onLifecycleChange(item.id, newStatus);
    } catch { /* silent */ }
  };

  const pnlColor = item.pnl_pct > 0 ? C.green : item.pnl_pct < 0 ? C.red : C.text3;

  return (
    <div style={{ position: "fixed", top: 0, right: 0, bottom: 0, width: 380, background: "#1a1a1f", borderLeft: `1px solid ${C.border}`, zIndex: 200, display: "flex", flexDirection: "column", overflowY: "auto" }}>
      {/* Header */}
      <div style={{ padding: "18px 20px 14px", borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 20, fontWeight: 800, color: C.text1 }}>{item.symbol}</span>
            <span style={{ padding: "2px 8px", borderRadius: 5, fontSize: 11, fontWeight: 700, background: item.signal === "BUY" ? "rgba(48,209,88,0.15)" : item.signal === "SELL" ? "rgba(255,69,58,0.15)" : "rgba(255,214,10,0.15)", color: item.signal === "BUY" ? C.green : item.signal === "SELL" ? C.red : "#ffd60a" }}>{item.signal}</span>
          </div>
          <div style={{ fontSize: 11, color: C.text3, marginTop: 2 }}>{companyNames[item.symbol] ?? ""}</div>
        </div>
        <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: C.text3, padding: 4 }}><X size={18} /></button>
      </div>

      <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 18, flex: 1 }}>
        {/* Lifecycle */}
        <div>
          <div style={{ fontSize: 11, color: C.text3, marginBottom: 8, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>Durum</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {(Object.keys(LIFECYCLE_CONFIG) as LifecycleStatus[]).map((s) => {
              const c = LIFECYCLE_CONFIG[s];
              const active = item.status_lifecycle === s;
              return (
                <button key={s} onClick={() => changeLifecycle(s)}
                  style={{ display: "flex", alignItems: "center", gap: 4, padding: "4px 10px", borderRadius: 6, fontSize: 10, fontWeight: 700, cursor: "pointer", border: active ? `1.5px solid ${c.color}` : `1px solid ${C.border}`, background: active ? c.bg : "transparent", color: active ? c.color : C.text3 }}>
                  {c.icon} {c.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Price info */}
        <div style={{ background: C.card, borderRadius: 12, padding: "14px 16px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            {[
              { label: "Giriş", value: item.entry_price > 0 ? `$${item.entry_price.toFixed(2)}` : "—", color: "#ffd60a" },
              { label: "Güncel", value: item.current_price > 0 ? `$${item.current_price.toFixed(2)}` : "—", color: C.cyan },
              { label: "Stop", value: item.stop_loss > 0 ? `$${item.stop_loss.toFixed(2)}` : "—", color: C.red },
              { label: "Hedef (TP)", value: item.take_profit > 0 ? `$${item.take_profit.toFixed(2)}` : "—", color: C.green },
            ].map((r) => (
              <div key={r.label}>
                <div style={{ fontSize: 10, color: C.text3 }}>{r.label}</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: r.color }}>{r.value}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 12, display: "flex", gap: 12 }}>
            <div>
              <div style={{ fontSize: 10, color: C.text3 }}>P&L</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: pnlColor }}>{item.pnl_pct >= 0 ? "+" : ""}{item.pnl_pct.toFixed(2)}%</div>
            </div>
            <div>
              <div style={{ fontSize: 10, color: C.text3 }}>Değişim</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: item.change_pct >= 0 ? C.green : C.red }}>{item.change_pct >= 0 ? "+" : ""}{item.change_pct.toFixed(2)}%</div>
            </div>
            <div>
              <div style={{ fontSize: 10, color: C.text3 }}>Skor</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: item.score >= 70 ? C.green : item.score >= 50 ? "#ffd60a" : C.text2 }}>{item.score > 0 ? Math.round(item.score) : "—"}</div>
            </div>
          </div>
          {item.entry_price > 0 && item.stop_loss > 0 && item.take_profit > 0 && <PriceProgressBar item={item} />}
        </div>

        {/* Signal info */}
        <div>
          <div style={{ fontSize: 11, color: C.text3, marginBottom: 8, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>Sinyal Detayı</div>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 8, fontSize: 12 }}>
            <div><span style={{ color: C.text3 }}>Regime: </span><strong style={{ color: C.text1 }}>{item.regime || "—"}</strong></div>
            <div><span style={{ color: C.text3 }}>Sentiment: </span><strong style={{ color: C.text1 }}>{item.sentiment || "—"}</strong></div>
            <div><span style={{ color: C.text3 }}>R/R: </span><strong style={{ color: C.cyan }}>{item.risk_reward > 0 ? `1:${item.risk_reward.toFixed(1)}` : "—"}</strong></div>
            <div><span style={{ color: C.text3 }}>Model: </span><strong style={{ color: C.text2 }}>{item.source_model || "—"}</strong></div>
          </div>
          {item.reason && <div style={{ fontSize: 12, color: C.text2, marginBottom: 6 }}><span style={{ color: C.text3 }}>Sebep: </span>{item.reason}</div>}
          {item.explanation && <div style={{ fontSize: 12, color: C.text2, lineHeight: 1.6 }}><span style={{ color: C.text3 }}>Açıklama: </span>{item.explanation}</div>}
        </div>

        {/* Notes */}
        <div>
          <div style={{ fontSize: 11, color: C.text3, marginBottom: 8, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>Notlar</div>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Bu sinyal hakkında notunuzu yazın…"
            rows={4}
            style={{ width: "100%", background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 12px", fontSize: 12, color: C.text1, resize: "vertical", outline: "none", boxSizing: "border-box" }}
          />
          <div style={{ marginTop: 8 }}>
            <div style={{ fontSize: 10, color: C.text3, marginBottom: 4 }}>Etiketler (virgülle ayırın)</div>
            <input
              type="text"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              placeholder="breakout, high-vol, watchlist"
              style={{ width: "100%", background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: "8px 12px", fontSize: 12, color: C.text1, outline: "none", boxSizing: "border-box" }}
            />
          </div>
          <button onClick={saveNote} disabled={saving}
            style={{ marginTop: 10, width: "100%", padding: "9px", borderRadius: 10, border: "none", background: savedOk ? "rgba(48,209,88,0.2)" : C.cyan, color: savedOk ? C.green : "#000", fontWeight: 700, fontSize: 12, cursor: "pointer" }}>
            {savedOk ? "✓ Kaydedildi" : saving ? "Kaydediliyor…" : "Kaydet"}
          </button>
        </div>

        {/* Metadata */}
        <div style={{ fontSize: 11, color: C.text3, display: "flex", flexDirection: "column", gap: 4 }}>
          <div>Eklenme: {new Date(item.added_at).toLocaleString("tr-TR")}</div>
          <div>ID: <span style={{ fontFamily: "monospace", fontSize: 10 }}>{item.id}</span></div>
        </div>

        {/* Delete */}
        <button onClick={() => { onDelete(item.symbol); onClose(); }}
          style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6, padding: "10px", borderRadius: 10, border: "1px solid rgba(255,69,58,0.3)", background: "rgba(255,69,58,0.07)", color: C.red, fontWeight: 600, fontSize: 12, cursor: "pointer" }}>
          <Trash2 size={13} /> Sinyali Kaldır
        </button>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: TrackedSignal["status"] }) {
  const cfg: Record<TrackedSignal["status"], { label: string; icon: React.ReactNode; bg: string; color: string }> = {
    "On Track": { label: "On Track", icon: <CheckCircle2 size={11} />, bg: "rgba(48,209,88,0.15)", color: C.green },
    "TP Hit":   { label: "TP Hit",   icon: <Target size={11} />,       bg: "rgba(255,214,10,0.15)", color: C.yellow },
    "Stop Hit": { label: "Stop Hit", icon: <XCircle size={11} />,      bg: "rgba(255,69,58,0.15)",  color: C.red },
    "Watching": { label: "Watching", icon: <Eye size={11} />,           bg: "rgba(0,212,255,0.12)",  color: C.cyan },
    "Pending":  { label: "Pending",  icon: <Clock size={11} />,         bg: "rgba(161,161,166,0.12)",color: C.text2 },
  };
  const c = cfg[status] ?? cfg["Pending"];
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "3px 8px", borderRadius: 6, fontSize: 11, fontWeight: 600, background: c.bg, color: c.color }}>
      {c.icon}{c.label}
    </span>
  );
}

function PriceProgressBar({ item }: { item: TrackedSignal }) {
  const min = Math.min(item.stop_loss, item.current_price || item.entry_price, item.entry_price) * 0.995;
  const max = Math.max(item.take_profit, item.current_price || item.entry_price, item.entry_price) * 1.005;
  const range = max - min;
  if (range <= 0) return null;
  const pct = (v: number) => Math.max(0, Math.min(100, ((v - min) / range) * 100));
  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ position: "relative", height: 6, background: "rgba(255,255,255,0.08)", borderRadius: 3 }}>
        <div style={{ position: "absolute", left: `${pct(item.stop_loss)}%`, width: `${pct(item.entry_price) - pct(item.stop_loss)}%`, height: "100%", background: `${C.red}40`, borderRadius: 3 }} />
        <div style={{ position: "absolute", left: `${pct(item.entry_price)}%`, width: `${pct(item.take_profit) - pct(item.entry_price)}%`, height: "100%", background: `${C.green}40`, borderRadius: 3 }} />
        <div style={{ position: "absolute", left: `${pct(item.stop_loss)}%`, top: -4, width: 2, height: 14, background: C.red }} title={`Stop: $${item.stop_loss}`} />
        <div style={{ position: "absolute", left: `${pct(item.entry_price)}%`, top: -4, width: 2, height: 14, background: C.yellow }} title={`Entry: $${item.entry_price}`} />
        <div style={{ position: "absolute", left: `${pct(item.take_profit)}%`, top: -4, width: 2, height: 14, background: C.green }} title={`TP: $${item.take_profit}`} />
        {item.current_price > 0 && (
          <div style={{ position: "absolute", left: `calc(${pct(item.current_price)}% - 5px)`, top: -3, width: 12, height: 12, borderRadius: "50%", background: C.cyan, border: "2px solid #000", zIndex: 2 }} title={`Now: $${item.current_price}`} />
        )}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 5, fontSize: 10, color: C.text3 }}>
        <span style={{ color: C.red }}>STOP ${item.stop_loss.toFixed(2)}</span>
        <span style={{ color: C.yellow }}>GİRİŞ ${item.entry_price.toFixed(2)}</span>
        <span style={{ color: C.cyan }}>ŞİMDİ ${item.current_price > 0 ? item.current_price.toFixed(2) : "—"}</span>
        <span style={{ color: C.green }}>TP ${item.take_profit.toFixed(2)}</span>
      </div>
    </div>
  );
}

function SinyalTakipTab() {
  const [items, setItems] = useState<TrackedSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshedAt, setRefreshedAt] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [drawerItem, setDrawerItem] = useState<TrackedSignal | null>(null);
  const [collapsedDates, setCollapsedDates] = useState<Set<string>>(new Set());
  const [lifecycleFilter, setLifecycleFilter] = useState<string>("ALL");

  const fetchList = useCallback(async (silent = false) => {
    if (!silent) setLoading(true); else setRefreshing(true);
    try {
      const res = await fetch("/py-api/watchlist/today");
      if (!res.ok) throw new Error();
      const data = await res.json();
      setItems(data.items ?? []);
      setRefreshedAt(data.refreshed_at ?? null);
    } catch { /* silent */ }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => {
    fetchList();
    const id = setInterval(() => fetchList(true), 60_000);
    return () => clearInterval(id);
  }, [fetchList]);

  const removeItem = async (symbol: string) => {
    try {
      await fetch(`/py-api/watchlist/${symbol}`, { method: "DELETE" });
      setItems((prev) => prev.filter((i) => i.symbol !== symbol));
    } catch { /* silent */ }
  };

  const clearAll = async () => {
    if (!confirm("Tüm sinyal kaydı silinsin mi?")) return;
    await fetch("/py-api/watchlist/clear", { method: "DELETE" });
    setItems([]);
  };

  const handleLifecycleChange = (id: string, status: LifecycleStatus) => {
    setItems((prev) => prev.map((i) => i.id === id ? { ...i, status_lifecycle: status } : i));
    setDrawerItem((prev) => prev && prev.id === id ? { ...prev, status_lifecycle: status } : prev);
  };

  const handleNoteChange = (id: string, notes: string, tags: string[]) => {
    setItems((prev) => prev.map((i) => i.id === id ? { ...i, notes, tags } : i));
    setDrawerItem((prev) => prev && prev.id === id ? { ...prev, notes, tags } : prev);
  };

  const toggleDate = (date: string) => {
    setCollapsedDates((prev) => {
      const s = new Set(prev);
      if (s.has(date)) s.delete(date); else s.add(date);
      return s;
    });
  };

  // Filter by lifecycle
  const filteredItems = items.filter((i) => {
    if (lifecycleFilter === "ALL") return true;
    return i.status_lifecycle === lifecycleFilter;
  });

  // Group by signal_date (today first)
  const today = new Date().toISOString().slice(0, 10);
  const grouped = new Map<string, TrackedSignal[]>();
  for (const item of filteredItems) {
    const date = item.signal_date ?? item.added_at?.slice(0, 10) ?? "—";
    if (!grouped.has(date)) grouped.set(date, []);
    grouped.get(date)!.push(item);
  }
  const sortedDates = Array.from(grouped.keys()).sort((a, b) => b.localeCompare(a));

  const onTrack  = items.filter((i) => i.status === "On Track").length;
  const tpHit    = items.filter((i) => i.status === "TP Hit").length;
  const stopHit  = items.filter((i) => i.status === "Stop Hit").length;
  const avgPnl   = items.length > 0 ? items.reduce((s, i) => s + i.pnl_pct, 0) / items.length : 0;
  const todayCount = grouped.get(today)?.length ?? 0;

  if (loading) return <div style={{ textAlign: "center", padding: 60, color: C.text2 }}>Yükleniyor…</div>;

  if (items.length === 0) return (
    <div style={{ textAlign: "center", padding: "60px 20px", color: C.text3, display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
      <BookmarkX size={44} style={{ opacity: 0.4 }} />
      <p style={{ fontSize: 15, color: C.text2 }}>Sinyal takip listesi boş</p>
      <p style={{ fontSize: 12 }}>
        <strong style={{ color: C.cyan }}>Scanner</strong> sayfasında tarama yaptıktan sonra
        satır başındaki <strong style={{ color: C.cyan }}>+</strong> ikonuna veya
        <strong style={{ color: C.cyan }}> Watchlist&apos;e Ekle</strong> butonuna basın.
      </p>
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Today summary bar */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        {[
          { label: "BUGÜN",     value: todayCount,  color: C.cyan },
          { label: "TOPLAM",    value: items.length, color: C.text1 },
          { label: "ON TRACK",  value: onTrack,      color: C.green },
          { label: "TP HIT",    value: tpHit,        color: "#ffd60a" },
          { label: "STOP HIT",  value: stopHit,      color: C.red },
          { label: "ORT. P&L",  value: `${avgPnl >= 0 ? "+" : ""}${avgPnl.toFixed(2)}%`, color: avgPnl >= 0 ? C.green : C.red },
        ].map((s) => (
          <div key={s.label} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 16px" }}>
            <div style={{ fontSize: 10, color: C.text3 }}>{s.label}</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: s.color }}>{s.value}</div>
          </div>
        ))}
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          {refreshedAt && <span style={{ fontSize: 10, color: C.text3, alignSelf: "center" }}>{new Date(refreshedAt).toLocaleTimeString("tr-TR")}</span>}
          <button onClick={() => fetchList(true)} disabled={refreshing} style={{ display: "flex", alignItems: "center", gap: 5, borderRadius: 10, border: `1px solid ${C.border}`, background: C.card, padding: "6px 12px", fontSize: 12, color: C.cyan, cursor: "pointer", fontWeight: 600 }}>
            <RefreshCw size={13} style={{ animation: refreshing ? "spin 1s linear infinite" : "none" }} /> Yenile
          </button>
          <button onClick={clearAll} style={{ display: "flex", alignItems: "center", gap: 5, borderRadius: 10, border: "1px solid rgba(255,69,58,0.3)", background: "rgba(255,69,58,0.08)", padding: "6px 12px", fontSize: 12, color: C.red, cursor: "pointer", fontWeight: 600 }}>
            <Trash2 size={13} /> Temizle
          </button>
        </div>
      </div>

      {/* Lifecycle filter */}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
        <SlidersHorizontal size={13} style={{ color: C.text3 }} />
        {[
          { key: "ALL", label: `Tümü (${items.length})` },
          { key: "new", label: "Yeni" },
          { key: "watching", label: "İzleniyor" },
          { key: "active", label: "Aktif" },
          { key: "resolved_win", label: "Başarılı" },
          { key: "resolved_loss", label: "Başarısız" },
          { key: "expired", label: "Süresi Doldu" },
          { key: "cancelled", label: "İptal" },
        ].map((f) => (
          <button key={f.key} onClick={() => setLifecycleFilter(f.key)}
            style={{ padding: "4px 11px", borderRadius: 8, fontSize: 11, fontWeight: 600, cursor: "pointer", border: "none", background: lifecycleFilter === f.key ? C.cyan : "rgba(255,255,255,0.07)", color: lifecycleFilter === f.key ? "#000" : C.text2 }}>
            {f.label}
          </button>
        ))}
      </div>

      {/* Date grouped list */}
      {sortedDates.map((date) => {
        const dateItems = grouped.get(date) ?? [];
        const isToday = date === today;
        const collapsed = collapsedDates.has(date) && !isToday;
        const dateLabel = isToday ? "Bugün" : new Date(date + "T00:00:00").toLocaleDateString("tr-TR", { day: "numeric", month: "long", year: "numeric" });

        return (
          <div key={date} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden" }}>
            {/* Date header */}
            <div
              onClick={() => toggleDate(date)}
              style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 16px", borderBottom: collapsed ? "none" : `1px solid ${C.border}`, cursor: "pointer", background: isToday ? "rgba(0,212,255,0.04)" : "transparent" }}
            >
              {collapsed ? <ChevronRight size={14} style={{ color: C.text3 }} /> : <ChevronDown size={14} style={{ color: C.text3 }} />}
              <span style={{ fontSize: 13, fontWeight: 700, color: isToday ? C.cyan : C.text1 }}>{dateLabel}</span>
              <span style={{ fontSize: 11, color: C.text3, marginLeft: 2 }}>— {dateItems.length} sinyal</span>
              {isToday && <span style={{ marginLeft: 4, padding: "2px 7px", borderRadius: 5, fontSize: 10, fontWeight: 700, background: "rgba(0,212,255,0.15)", color: C.cyan }}>BUGÜN</span>}
            </div>

            {!collapsed && (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: C.primary }}>
                      {["HİSSE", "SİNYAL", "DURUM", "LİFECYCLE", "GİRİŞ", "GÜNCEL", "P&L", "DEĞ%", "STOP", "TP", "SKOR", "EKLENDİ", ""].map((h) => (
                        <th key={h} style={{ padding: "10px 12px", textAlign: "left", color: C.text3, fontSize: 11, fontWeight: 600, borderBottom: `1px solid ${C.border}`, whiteSpace: "nowrap" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {dateItems.map((item) => (
                      <>
                        <tr
                          key={item.id ?? item.symbol}
                          style={{ borderBottom: `1px solid ${C.border}`, background: item.status === "Stop Hit" ? "rgba(255,69,58,0.04)" : item.status === "TP Hit" ? "rgba(255,214,10,0.04)" : "transparent", cursor: "pointer" }}
                          onClick={() => setExpanded(expanded === (item.id ?? item.symbol) ? null : (item.id ?? item.symbol))}
                        >
                          <td style={{ padding: "11px 12px" }}>
                            <div style={{ fontWeight: 700 }}>{item.symbol}</div>
                            <div style={{ fontSize: 10, color: C.text3 }}>{companyNames[item.symbol] ?? ""}</div>
                          </td>
                          <td style={{ padding: "11px 12px" }}>
                            <span style={{ padding: "2px 8px", borderRadius: 5, fontSize: 11, fontWeight: 700, background: item.signal === "BUY" ? "rgba(48,209,88,0.15)" : item.signal === "SELL" ? "rgba(255,69,58,0.15)" : "rgba(255,214,10,0.15)", color: item.signal === "BUY" ? C.green : item.signal === "SELL" ? C.red : "#ffd60a" }}>{item.signal}</span>
                          </td>
                          <td style={{ padding: "11px 12px" }}><StatusBadge status={item.status} /></td>
                          <td style={{ padding: "11px 12px" }}><LifecycleBadge status={item.status_lifecycle ?? "watching"} /></td>
                          <td style={{ padding: "11px 12px", fontWeight: 600 }}>{item.entry_price > 0 ? `$${item.entry_price.toFixed(2)}` : "—"}</td>
                          <td style={{ padding: "11px 12px", fontWeight: 600 }}>{item.current_price > 0 ? `$${item.current_price.toFixed(2)}` : "—"}</td>
                          <td style={{ padding: "11px 12px" }}>
                            {item.pnl_pct !== 0 ? (
                              <span style={{ color: item.pnl_pct > 0 ? C.green : C.red, fontWeight: 600, display: "inline-flex", alignItems: "center", gap: 3 }}>
                                {item.pnl_pct > 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                                {item.pnl_pct > 0 ? "+" : ""}{item.pnl_pct.toFixed(2)}%
                              </span>
                            ) : <span style={{ color: C.text3 }}>—</span>}
                          </td>
                          <td style={{ padding: "11px 12px", color: item.change_pct >= 0 ? C.green : C.red, fontWeight: 500 }}>{item.change_pct >= 0 ? "+" : ""}{item.change_pct.toFixed(2)}%</td>
                          <td style={{ padding: "11px 12px", color: C.red, fontSize: 12 }}>{item.stop_loss > 0 ? `$${item.stop_loss.toFixed(2)}` : "—"}</td>
                          <td style={{ padding: "11px 12px", color: C.green, fontSize: 12 }}>{item.take_profit > 0 ? `$${item.take_profit.toFixed(2)}` : "—"}</td>
                          <td style={{ padding: "11px 12px", fontWeight: 700, color: item.score >= 70 ? C.green : item.score >= 50 ? "#ffd60a" : C.text2 }}>{item.score > 0 ? Math.round(item.score) : "—"}</td>
                          <td style={{ padding: "11px 12px", color: C.text3, fontSize: 11, whiteSpace: "nowrap" }}>{new Date(item.added_at).toLocaleString("tr-TR", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })}</td>
                          <td style={{ padding: "11px 12px" }} onClick={(e) => e.stopPropagation()}>
                            <div style={{ display: "flex", gap: 4 }}>
                              <button onClick={(e) => { e.stopPropagation(); setDrawerItem(item); }} style={{ background: "none", border: "none", cursor: "pointer", color: C.cyan, padding: "4px 6px", borderRadius: 6, display: "flex", alignItems: "center" }} title="Detay"><MessageSquare size={13} /></button>
                              <button onClick={() => removeItem(item.symbol)} style={{ background: "none", border: "none", cursor: "pointer", color: C.red, padding: "4px 6px", borderRadius: 6, display: "flex", alignItems: "center" }}><Trash2 size={13} /></button>
                            </div>
                          </td>
                        </tr>
                        {expanded === (item.id ?? item.symbol) && (
                          <tr key={`${item.id}-exp`}>
                            <td colSpan={13} style={{ padding: "0 12px 12px", background: "#1c1c22" }}>
                              <div style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${C.border}`, borderRadius: 10, padding: "12px 14px", fontSize: 12, color: C.text2, lineHeight: 1.6 }}>
                                <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 6 }}>
                                  <div><span style={{ color: C.text3 }}>Regime:</span> <strong style={{ color: C.text1 }}>{item.regime || "—"}</strong></div>
                                  <div><span style={{ color: C.text3 }}>Sentiment:</span> <strong style={{ color: C.text1 }}>{item.sentiment || "—"}</strong></div>
                                  <div><span style={{ color: C.text3 }}>R/R:</span> <strong style={{ color: C.cyan }}>{item.risk_reward > 0 ? `1:${item.risk_reward.toFixed(1)}` : "—"}</strong></div>
                                  <div><span style={{ color: C.text3 }}>Model:</span> <strong style={{ color: C.text2 }}>{item.source_model || "—"}</strong></div>
                                </div>
                                {item.reason && <div style={{ marginBottom: 4 }}><span style={{ color: C.text3 }}>Sebep: </span>{item.reason}</div>}
                                {item.explanation && <div style={{ marginBottom: 6 }}><span style={{ color: C.text3 }}>Açıklama: </span>{item.explanation}</div>}
                                {item.notes && <div style={{ marginBottom: 4, color: C.cyan }}><MessageSquare size={11} style={{ display: "inline", marginRight: 4 }} />{item.notes}</div>}
                                {item.tags && item.tags.length > 0 && (
                                  <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
                                    {item.tags.map((t) => <span key={t} style={{ padding: "2px 7px", borderRadius: 5, fontSize: 10, background: "rgba(255,255,255,0.06)", color: C.text2 }}>{t}</span>)}
                                  </div>
                                )}
                                {item.entry_price > 0 && item.stop_loss > 0 && item.take_profit > 0 && <PriceProgressBar item={item} />}
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      })}

      {/* Drawer overlay */}
      {drawerItem && (
        <>
          <div onClick={() => setDrawerItem(null)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 199 }} />
          <SignalDrawer
            item={drawerItem}
            onClose={() => setDrawerItem(null)}
            onLifecycleChange={handleLifecycleChange}
            onNoteChange={handleNoteChange}
            onDelete={removeItem}
          />
        </>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   GEÇMİŞ TAB
═══════════════════════════════════════════════════════════════ */
interface ArchiveDateEntry {
  date: string;
  count: number;
  source: "archive" | "live";
}

function GecmisTab() {
  const [dates, setDates] = useState<ArchiveDateEntry[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [historyItems, setHistoryItems] = useState<TrackedSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [histLoading, setHistLoading] = useState(false);
  const [page, setPage] = useState(1);
  const LIMIT = 50;

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/py-api/watchlist/dates");
        if (res.ok) {
          const data = await res.json();
          setDates(data.dates ?? []);
          if (data.dates?.length) setSelectedDate(data.dates[0].date);
        }
      } catch { /* silent */ }
      finally { setLoading(false); }
    })();
  }, []);

  useEffect(() => {
    if (!selectedDate) return;
    setHistLoading(true);
    setPage(1);
    (async () => {
      try {
        const res = await fetch(`/py-api/watchlist/history?date=${selectedDate}&page=1&limit=${LIMIT}`);
        if (res.ok) {
          const data = await res.json();
          setHistoryItems(data.items ?? []);
        }
      } catch { /* silent */ }
      finally { setHistLoading(false); }
    })();
  }, [selectedDate]);

  const goToDate = (dir: -1 | 1) => {
    const idx = dates.findIndex((d) => d.date === selectedDate);
    const next = idx + dir;
    if (next >= 0 && next < dates.length) setSelectedDate(dates[next].date);
  };

  if (loading) return <div style={{ textAlign: "center", padding: 60, color: C.text2 }}>Yükleniyor…</div>;

  if (dates.length === 0) return (
    <div style={{ textAlign: "center", padding: "60px 20px", color: C.text3, display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
      <History size={44} style={{ opacity: 0.4 }} />
      <p style={{ fontSize: 15, color: C.text2 }}>Henüz arşiv kaydı yok</p>
      <p style={{ fontSize: 12 }}>Sinyal takibi yaptıkça günlük kayıtlar burada görünecek.</p>
    </div>
  );

  const selIdx = dates.findIndex((d) => d.date === selectedDate);
  const selEntry = dates[selIdx];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Date selector */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: "14px 18px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <button onClick={() => goToDate(-1)} disabled={selIdx <= 0}
            style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 8, padding: "5px 10px", color: selIdx <= 0 ? C.text3 : C.text1, cursor: selIdx <= 0 ? "default" : "pointer", fontSize: 14 }}>←</button>
          <select value={selectedDate ?? ""} onChange={(e) => setSelectedDate(e.target.value)}
            style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: "6px 12px", fontSize: 13, color: C.text1, cursor: "pointer", outline: "none" }}>
            {dates.map((d) => (
              <option key={d.date} value={d.date}>{d.date} ({d.count} sinyal){d.source === "live" ? " — Bugün" : ""}</option>
            ))}
          </select>
          <button onClick={() => goToDate(1)} disabled={selIdx >= dates.length - 1}
            style={{ background: "none", border: `1px solid ${C.border}`, borderRadius: 8, padding: "5px 10px", color: selIdx >= dates.length - 1 ? C.text3 : C.text1, cursor: selIdx >= dates.length - 1 ? "default" : "pointer", fontSize: 14 }}>→</button>
          {selEntry && (
            <span style={{ fontSize: 12, color: C.text3, marginLeft: 8 }}>
              {selEntry.count} sinyal · {selEntry.source === "live" ? <span style={{ color: C.cyan }}>Canlı</span> : "Arşiv"}
            </span>
          )}
        </div>
      </div>

      {/* History table */}
      {histLoading ? (
        <div style={{ textAlign: "center", padding: 40, color: C.text2 }}>Yükleniyor…</div>
      ) : historyItems.length === 0 ? (
        <div style={{ textAlign: "center", padding: 40, color: C.text3 }}>Bu tarih için kayıt bulunamadı.</div>
      ) : (
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
              <thead>
                <tr style={{ background: C.primary }}>
                  {["HİSSE", "SİNYAL", "DURUM", "LİFECYCLE", "GİRİŞ", "GÜNCEL", "P&L", "STOP", "TP", "SKOR", "MODEL", "EKLENDİ"].map((h) => (
                    <th key={h} style={{ padding: "10px 11px", textAlign: "left", color: C.text3, fontSize: 10, fontWeight: 600, borderBottom: `1px solid ${C.border}`, whiteSpace: "nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {historyItems.map((item, idx) => (
                  <tr key={item.id ?? idx} style={{ borderBottom: `1px solid ${C.border}` }}>
                    <td style={{ padding: "10px 11px", fontWeight: 700 }}>{item.symbol}</td>
                    <td style={{ padding: "10px 11px" }}>
                      <span style={{ padding: "2px 7px", borderRadius: 5, fontSize: 10, fontWeight: 700, background: item.signal === "BUY" ? "rgba(48,209,88,0.15)" : "rgba(255,69,58,0.15)", color: item.signal === "BUY" ? C.green : C.red }}>{item.signal}</span>
                    </td>
                    <td style={{ padding: "10px 11px" }}><StatusBadge status={item.status} /></td>
                    <td style={{ padding: "10px 11px" }}><LifecycleBadge status={item.status_lifecycle ?? "watching"} /></td>
                    <td style={{ padding: "10px 11px" }}>{item.entry_price > 0 ? `$${item.entry_price.toFixed(2)}` : "—"}</td>
                    <td style={{ padding: "10px 11px" }}>{item.current_price > 0 ? `$${item.current_price.toFixed(2)}` : "—"}</td>
                    <td style={{ padding: "10px 11px", color: item.pnl_pct > 0 ? C.green : item.pnl_pct < 0 ? C.red : C.text3, fontWeight: 600 }}>{item.pnl_pct !== 0 ? `${item.pnl_pct > 0 ? "+" : ""}${item.pnl_pct.toFixed(2)}%` : "—"}</td>
                    <td style={{ padding: "10px 11px", color: C.red }}>{item.stop_loss > 0 ? `$${item.stop_loss.toFixed(2)}` : "—"}</td>
                    <td style={{ padding: "10px 11px", color: C.green }}>{item.take_profit > 0 ? `$${item.take_profit.toFixed(2)}` : "—"}</td>
                    <td style={{ padding: "10px 11px", fontWeight: 700, color: item.score >= 70 ? C.green : item.score >= 50 ? "#ffd60a" : C.text2 }}>{item.score > 0 ? Math.round(item.score) : "—"}</td>
                    <td style={{ padding: "10px 11px", color: C.text3 }}>{item.source_model || "—"}</td>
                    <td style={{ padding: "10px 11px", color: C.text3, whiteSpace: "nowrap" }}>{new Date(item.added_at).toLocaleString("tr-TR", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   PERFORMANS RAPORU TAB
═══════════════════════════════════════════════════════════════ */
interface PerfSignal {
  symbol: string;
  signal: string;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  score: number;
  regime: string;
  risk_reward: number;
  added_at: string;
  outcome: "TP_HIT" | "STOP_HIT" | "OPEN" | "NO_DATA" | "NO_DATE" | "ERROR";
  pnl_pct: number;
  exit_price: number;
  exit_at: string | null;
}

interface SignalTypeBreakdown {
  signal: string;
  count: number;
  tp_count: number;
  stop_count: number;
  open_count: number;
  tp_rate: number;
  avg_pnl: number;
}

interface PerfReport {
  days: number;
  total: number;
  tp_hit: number;
  stop_hit: number;
  open: number;
  other: number;
  tp_rate: number;
  stop_rate: number;
  closed_rate: number;
  avg_pnl: number;
  avg_pnl_tp: number;
  avg_pnl_stop: number;
  signals: PerfSignal[];
  by_type: SignalTypeBreakdown[];
  evaluated_at: string;
}

const PERIOD_OPTIONS = [
  { days: 1, label: "1 Günlük" },
  { days: 2, label: "2 Günlük" },
  { days: 5, label: "1 Haftalık" },
  { days: 10, label: "2 Haftalık" },
  { days: 21, label: "1 Aylık" },
];

function OutcomeBadge({ outcome }: { outcome: PerfSignal["outcome"] }) {
  const cfg: Record<PerfSignal["outcome"], { label: string; color: string; bg: string; icon: React.ReactNode }> = {
    TP_HIT:   { label: "TP Vurdu",   color: C.green,  bg: "rgba(48,209,88,0.15)",   icon: <Target size={11} /> },
    STOP_HIT: { label: "Stop Vurdu", color: C.red,    bg: "rgba(255,69,58,0.15)",   icon: <XCircle size={11} /> },
    OPEN:     { label: "Açık",       color: C.cyan,   bg: "rgba(0,212,255,0.12)",   icon: <Clock size={11} /> },
    NO_DATA:  { label: "Veri Yok",   color: C.text3,  bg: "rgba(161,161,166,0.1)",  icon: <AlertTriangle size={11} /> },
    NO_DATE:  { label: "Tarih Yok",  color: C.text3,  bg: "rgba(161,161,166,0.1)",  icon: <AlertTriangle size={11} /> },
    ERROR:    { label: "Hata",       color: C.text3,  bg: "rgba(161,161,166,0.1)",  icon: <AlertTriangle size={11} /> },
  };
  const c = cfg[outcome] ?? cfg.ERROR;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "3px 8px", borderRadius: 6, fontSize: 11, fontWeight: 600, background: c.bg, color: c.color }}>
      {c.icon} {c.label}
    </span>
  );
}

/* Donut chart — simple SVG */
function DonutChart({ tp, stop, open, total }: { tp: number; stop: number; open: number; total: number }) {
  if (total === 0) return null;
  const r = 44, cx = 56, cy = 56, stroke = 14;
  const circ = 2 * Math.PI * r;
  const slices = [
    { value: tp,   color: C.green,  label: "TP" },
    { value: stop, color: C.red,    label: "Stop" },
    { value: open, color: C.cyan,   label: "Açık" },
    { value: total - tp - stop - open, color: C.text3, label: "Diğer" },
  ].filter((s) => s.value > 0);
  let offset = 0;
  const paths = slices.map((s) => {
    const pct = s.value / total;
    const dash = pct * circ;
    const gap = circ - dash;
    const el = (
      <circle
        key={s.label}
        cx={cx} cy={cy} r={r}
        fill="none"
        stroke={s.color}
        strokeWidth={stroke}
        strokeDasharray={`${dash} ${gap}`}
        strokeDashoffset={-offset}
        style={{ transform: "rotate(-90deg)", transformOrigin: `${cx}px ${cy}px` }}
      />
    );
    offset += dash;
    return el;
  });
  return (
    <svg width={112} height={112}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={stroke} />
      {paths}
      <text x={cx} y={cy - 5} textAnchor="middle" fill={C.text1} fontSize={18} fontWeight={700}>{total}</text>
      <text x={cx} y={cy + 14} textAnchor="middle" fill={C.text3} fontSize={10}>sinyal</text>
    </svg>
  );
}

function PerformansRaporuTab() {
  const [days, setDays] = useState(1);
  const [report, setReport] = useState<PerfReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [outcomeFilter, setOutcomeFilter] = useState<string>("ALL");
  const [sortBy, setSortBy] = useState<"pnl_pct" | "score" | "added_at">("added_at");
  const [sortDir, setSortDir] = useState<"desc" | "asc">("desc");

  const fetchReport = useCallback(async (d: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/py-api/watchlist/performance?days=${d}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: PerfReport = await res.json();
      setReport(data);
    } catch {
      setError("Rapor yüklenemedi — API bağlantısı kontrol edin");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchReport(days); }, [days, fetchReport]);

  const toggleSort = (col: typeof sortBy) => {
    if (sortBy === col) setSortDir((d) => d === "desc" ? "asc" : "desc");
    else { setSortBy(col); setSortDir("desc"); }
  };

  const signals = report?.signals ?? [];
  const filtered = signals
    .filter((s) => outcomeFilter === "ALL" || s.outcome === outcomeFilter)
    .sort((a, b) => {
      let diff = 0;
      if (sortBy === "pnl_pct") diff = a.pnl_pct - b.pnl_pct;
      else if (sortBy === "score") diff = a.score - b.score;
      else diff = new Date(a.added_at).getTime() - new Date(b.added_at).getTime();
      return sortDir === "desc" ? -diff : diff;
    });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

      {/* ── Dönem seçici ─── */}
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ fontSize: 12, color: C.text3, marginRight: 4 }}>Hedef süresi:</span>
        {PERIOD_OPTIONS.map((p) => (
          <button
            key={p.days}
            onClick={() => { setDays(p.days); }}
            style={{
              padding: "7px 16px", borderRadius: 10, fontSize: 12, fontWeight: 600, cursor: "pointer", border: "none",
              background: days === p.days ? C.cyan : "rgba(255,255,255,0.07)",
              color: days === p.days ? "#000" : C.text2,
              transition: "background 0.15s",
            }}
          >
            {p.label}
          </button>
        ))}
        <button
          onClick={() => fetchReport(days)}
          disabled={loading}
          style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 5, borderRadius: 10, border: `1px solid ${C.border}`, background: C.card, padding: "7px 14px", fontSize: 12, color: C.cyan, cursor: "pointer", fontWeight: 600 }}
        >
          <RefreshCw size={13} style={{ animation: loading ? "spin 1s linear infinite" : "none" }} />
          {loading ? "Hesaplanıyor…" : "Yenile"}
        </button>
      </div>

      {error && (
        <div style={{ background: "rgba(255,69,58,0.1)", border: "1px solid rgba(255,69,58,0.3)", borderRadius: 12, padding: "14px 18px", color: C.red, fontSize: 13 }}>
          {error}
        </div>
      )}

      {loading && !report && (
        <div style={{ textAlign: "center", padding: 60, color: C.text2, fontSize: 13 }}>
          Fiyat geçmişi alınıyor… Bu işlem biraz sürebilir
        </div>
      )}

      {report && !loading && report.total === 0 && (
        <div style={{ textAlign: "center", padding: "60px 20px", color: C.text3, display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
          <Activity size={44} style={{ opacity: 0.3 }} />
          <p style={{ fontSize: 15, color: C.text2 }}>Henüz sinyal kaydı yok</p>
          <p style={{ fontSize: 12 }}>Scanner&apos;da tarama yaptıktan sonra <strong style={{ color: C.cyan }}>Sinyalleri Kaydet</strong> butonuna basın</p>
        </div>
      )}

      {report && report.total > 0 && (
        <>
          {/* ── Özet kartlar ── */}
          <div style={{ display: "grid", gridTemplateColumns: "112px repeat(5, 1fr)", gap: 12, alignItems: "start" }}>
            {/* Donut */}
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: 16, display: "flex", justifyContent: "center" }}>
              <DonutChart tp={report.tp_hit} stop={report.stop_hit} open={report.open} total={report.total} />
            </div>

            {/* TP Hit */}
            <div style={{ background: "rgba(48,209,88,0.07)", border: "1px solid rgba(48,209,88,0.2)", borderRadius: 14, padding: "16px 20px" }}>
              <div style={{ fontSize: 11, color: C.text3, marginBottom: 6 }}>TP Vurma Oranı</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: C.green }}>{report.tp_rate}%</div>
              <div style={{ fontSize: 12, color: C.text2 }}>{report.tp_hit} sinyal</div>
              <div style={{ fontSize: 11, color: C.text3, marginTop: 6 }}>Ort. Getiri: <span style={{ color: C.green }}>+{report.avg_pnl_tp.toFixed(2)}%</span></div>
            </div>

            {/* Stop Hit */}
            <div style={{ background: "rgba(255,69,58,0.07)", border: "1px solid rgba(255,69,58,0.2)", borderRadius: 14, padding: "16px 20px" }}>
              <div style={{ fontSize: 11, color: C.text3, marginBottom: 6 }}>Stop Vurma Oranı</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: C.red }}>{report.stop_rate}%</div>
              <div style={{ fontSize: 12, color: C.text2 }}>{report.stop_hit} sinyal</div>
              <div style={{ fontSize: 11, color: C.text3, marginTop: 6 }}>Ort. Kayıp: <span style={{ color: C.red }}>{report.avg_pnl_stop.toFixed(2)}%</span></div>
            </div>

            {/* Açık */}
            <div style={{ background: "rgba(0,212,255,0.07)", border: "1px solid rgba(0,212,255,0.2)", borderRadius: 14, padding: "16px 20px" }}>
              <div style={{ fontSize: 11, color: C.text3, marginBottom: 6 }}>Hâlâ Açık</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: C.cyan }}>{report.open}</div>
              <div style={{ fontSize: 12, color: C.text2 }}>sinyal</div>
              <div style={{ fontSize: 11, color: C.text3, marginTop: 6 }}>{days} günde kapanmadı</div>
            </div>

            {/* Ort PnL */}
            <div style={{ background: report.avg_pnl >= 0 ? "rgba(48,209,88,0.07)" : "rgba(255,69,58,0.07)", border: `1px solid ${report.avg_pnl >= 0 ? "rgba(48,209,88,0.2)" : "rgba(255,69,58,0.2)"}`, borderRadius: 14, padding: "16px 20px" }}>
              <div style={{ fontSize: 11, color: C.text3, marginBottom: 6 }}>Ortalama P&amp;L</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: report.avg_pnl >= 0 ? C.green : C.red }}>{report.avg_pnl >= 0 ? "+" : ""}{report.avg_pnl.toFixed(2)}%</div>
              <div style={{ fontSize: 12, color: C.text2 }}>tüm sinyaller</div>
              <div style={{ fontSize: 11, color: C.text3, marginTop: 6 }}>Toplam {report.total} sinyal</div>
            </div>

            {/* Karar Oranı */}
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: "16px 20px" }}>
              <div style={{ fontSize: 11, color: C.text3, marginBottom: 6 }}>Karar Oranı</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: C.yellow }}>{report.closed_rate}%</div>
              <div style={{ fontSize: 12, color: C.text2 }}>{report.tp_hit + report.stop_hit} karar verildi</div>
              <div style={{ fontSize: 11, color: C.text3, marginTop: 6 }}>TP veya Stop vuruldu</div>
            </div>
          </div>

          {/* ── Signal type breakdown ── */}
          {report.by_type && report.by_type.length > 0 && (
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden" }}>
              <div style={{ padding: "12px 16px", borderBottom: `1px solid ${C.border}` }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: C.text1 }}>Signal Type Performansı</span>
              </div>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={{ background: C.primary }}>
                    {["TİP", "TOPLAM", "TP", "STOP", "AÇIK", "TP ORANI", "ORT. P&L"].map((h) => (
                      <th key={h} style={{ padding: "10px 14px", textAlign: "left", color: C.text3, fontSize: 10, fontWeight: 600, borderBottom: `1px solid ${C.border}` }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {report.by_type.map((row) => (
                    <tr key={row.signal} style={{ borderBottom: `1px solid ${C.border}` }}>
                      <td style={{ padding: "10px 14px" }}>
                        <span style={{ padding: "2px 8px", borderRadius: 5, fontSize: 11, fontWeight: 700, background: row.signal === "BUY" ? "rgba(48,209,88,0.15)" : row.signal === "SELL" ? "rgba(255,69,58,0.15)" : "rgba(255,214,10,0.15)", color: row.signal === "BUY" ? C.green : row.signal === "SELL" ? C.red : "#ffd60a" }}>{row.signal}</span>
                      </td>
                      <td style={{ padding: "10px 14px", fontWeight: 600 }}>{row.count}</td>
                      <td style={{ padding: "10px 14px", color: C.green }}>{row.tp_count}</td>
                      <td style={{ padding: "10px 14px", color: C.red }}>{row.stop_count}</td>
                      <td style={{ padding: "10px 14px", color: C.text2 }}>{row.open_count}</td>
                      <td style={{ padding: "10px 14px", fontWeight: 700, color: row.tp_rate >= 60 ? C.green : row.tp_rate >= 40 ? "#ffd60a" : C.red }}>{row.tp_rate.toFixed(1)}%</td>
                      <td style={{ padding: "10px 14px", fontWeight: 700, color: row.avg_pnl >= 0 ? C.green : C.red }}>{row.avg_pnl >= 0 ? "+" : ""}{row.avg_pnl.toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* ── Sinyal tablosu ── */}
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden" }}>
            {/* Filtre */}
            <div style={{ display: "flex", gap: 8, padding: "12px 16px", borderBottom: `1px solid ${C.border}`, flexWrap: "wrap", alignItems: "center" }}>
              <span style={{ fontSize: 11, color: C.text3 }}>Filtre:</span>
              {[
                { key: "ALL",      label: `Tümü (${report.total})` },
                { key: "TP_HIT",   label: `TP Vurdu (${report.tp_hit})` },
                { key: "STOP_HIT", label: `Stop Vurdu (${report.stop_hit})` },
                { key: "OPEN",     label: `Açık (${report.open})` },
              ].map((f) => (
                <button
                  key={f.key}
                  onClick={() => setOutcomeFilter(f.key)}
                  style={{
                    padding: "4px 12px", borderRadius: 8, fontSize: 11, fontWeight: 600, cursor: "pointer", border: "none",
                    background: outcomeFilter === f.key ? C.cyan : "rgba(255,255,255,0.07)",
                    color: outcomeFilter === f.key ? "#000" : C.text2,
                  }}
                >
                  {f.label}
                </button>
              ))}
              <span style={{ marginLeft: "auto", fontSize: 10, color: C.text3 }}>
                {report.evaluated_at ? `Hesaplandı: ${new Date(report.evaluated_at).toLocaleString("tr-TR")}` : ""}
              </span>
            </div>

            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ background: C.primary }}>
                    {[
                      { key: null,       label: "HİSSE" },
                      { key: null,       label: "SİNYAL" },
                      { key: null,       label: "SONUÇ" },
                      { key: "added_at", label: "EKLENME" },
                      { key: null,       label: "GİRİŞ" },
                      { key: null,       label: "STOP" },
                      { key: null,       label: "HEDEF" },
                      { key: null,       label: "ÇIKIŞ FİYATI" },
                      { key: null,       label: "ÇIKIŞ TARİHİ" },
                      { key: "pnl_pct",  label: "P&L %" },
                      { key: "score",    label: "SKOR" },
                    ].map((col) => (
                      <th
                        key={col.label}
                        onClick={() => col.key && toggleSort(col.key as typeof sortBy)}
                        style={{
                          padding: "10px 12px", textAlign: "left", color: sortBy === col.key ? C.cyan : C.text3,
                          fontSize: 11, fontWeight: 600, borderBottom: `1px solid ${C.border}`,
                          whiteSpace: "nowrap", cursor: col.key ? "pointer" : "default",
                        }}
                      >
                        {col.label} {col.key === sortBy ? (sortDir === "desc" ? "↓" : "↑") : ""}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((s) => (
                    <tr
                      key={`${s.symbol}-${s.added_at}`}
                      style={{
                        borderBottom: `1px solid ${C.border}`,
                        background:
                          s.outcome === "TP_HIT" ? "rgba(48,209,88,0.04)" :
                          s.outcome === "STOP_HIT" ? "rgba(255,69,58,0.04)" : "transparent",
                      }}
                    >
                      <td style={{ padding: "10px 12px", fontWeight: 700 }}>{s.symbol}</td>
                      <td style={{ padding: "10px 12px" }}>
                        <span style={{ padding: "2px 8px", borderRadius: 5, fontSize: 11, fontWeight: 700, background: s.signal === "BUY" ? "rgba(48,209,88,0.15)" : s.signal === "SELL" ? "rgba(255,69,58,0.15)" : "rgba(255,214,10,0.15)", color: s.signal === "BUY" ? C.green : s.signal === "SELL" ? C.red : C.yellow }}>{s.signal}</span>
                      </td>
                      <td style={{ padding: "10px 12px" }}><OutcomeBadge outcome={s.outcome} /></td>
                      <td style={{ padding: "10px 12px", color: C.text3, fontSize: 11, whiteSpace: "nowrap" }}>
                        {new Date(s.added_at).toLocaleString("tr-TR", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })}
                      </td>
                      <td style={{ padding: "10px 12px", fontWeight: 600 }}>{s.entry_price > 0 ? `$${s.entry_price.toFixed(2)}` : "—"}</td>
                      <td style={{ padding: "10px 12px", color: C.red, fontSize: 12 }}>{s.stop_loss > 0 ? `$${s.stop_loss.toFixed(2)}` : "—"}</td>
                      <td style={{ padding: "10px 12px", color: C.green, fontSize: 12 }}>{s.take_profit > 0 ? `$${s.take_profit.toFixed(2)}` : "—"}</td>
                      <td style={{ padding: "10px 12px", fontWeight: 600, color: s.outcome === "TP_HIT" ? C.green : s.outcome === "STOP_HIT" ? C.red : C.text2 }}>
                        {s.exit_price > 0 ? `$${s.exit_price.toFixed(2)}` : "—"}
                      </td>
                      <td style={{ padding: "10px 12px", color: C.text3, fontSize: 11 }}>
                        {s.exit_at ?? (s.outcome === "OPEN" ? "Açık" : "—")}
                      </td>
                      <td style={{ padding: "10px 12px" }}>
                        {s.pnl_pct !== 0 ? (
                          <span style={{ color: s.pnl_pct > 0 ? C.green : C.red, fontWeight: 700, display: "inline-flex", alignItems: "center", gap: 3 }}>
                            {s.pnl_pct > 0 ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                            {s.pnl_pct > 0 ? "+" : ""}{s.pnl_pct.toFixed(2)}%
                          </span>
                        ) : <span style={{ color: C.text3 }}>—</span>}
                      </td>
                      <td style={{ padding: "10px 12px", fontWeight: 700, color: s.score >= 70 ? C.green : s.score >= 50 ? C.yellow : C.text2 }}>
                        {s.score > 0 ? Math.round(s.score) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/* ── Mini sparkline (14 days) ──────────────────────────────── */
function Sparkline({ ticker }: { ticker: string }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  if (!mounted) return <svg width="80" height="32" viewBox="0 0 80 32" style={{ display: "block" }} />;
  const pts = genSparkline(ticker, 14);
  const mn = Math.min(...pts);
  const mx = Math.max(...pts);
  const range = mx - mn || 1;
  const last = pts[pts.length - 1];
  const first = pts[0];
  const color = last >= first ? C.green : C.red;
  const points = pts.map((p, i) => `${(i / 13) * 80},${32 - ((p - mn) / range) * 28}`).join(" ");
  return (
    <svg width="80" height="32" viewBox="0 0 80 32" style={{ display: "block" }}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ── Signal badge ──────────────────────────────────────────── */
function SignalBadge({ signal }: { signal: string }) {
  const m: Record<string, { color: string; bg: string }> = {
    BUY: { color: C.green, bg: "rgba(48,209,88,0.12)" },
    SELL: { color: C.red, bg: "rgba(255,69,58,0.12)" },
    HOLD: { color: C.cyan, bg: "rgba(0,212,255,0.12)" },
    CAUTION: { color: C.yellow, bg: "rgba(255,214,10,0.12)" },
  };
  const c = m[signal] || m.HOLD;
  return (
    <span
      style={{
        color: c.color,
        backgroundColor: c.bg,
        borderRadius: 9999,
        padding: "2px 8px",
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: 0.5,
      }}
    >
      {signal}
    </span>
  );
}

/* ── Default watchlist ─────────────────────────────────────── */
const defaultTickers = ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN"];
const popularStocks = ["GOOGL", "META", "AMD", "AVGO", "CRM", "PLTR", "COIN", "UBER"];
const WATCHLIST_KEY = "finpilot_watchlist";
export default function WatchlistPage() {
  const [activeTab, setActiveTab] = useState<"hisselerim" | "sinyal-takip" | "gecmis" | "performans-raporu">("hisselerim");
  const [tickers, setTickers] = useState<string[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem(WATCHLIST_KEY);
        if (stored) { const arr = JSON.parse(stored); if (Array.isArray(arr) && arr.length) return arr; }
      } catch {}
    }
    return defaultTickers;
  });
  const [allSymbols, setAllSymbols] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [dropOpen, setDropOpen] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanDone, setScanDone] = useState(false);
  const [scanPct, setScanPct] = useState(0);
  const [hovered, setHovered] = useState<string | null>(null);
  const [scanResults, setScanResults] = useState<Record<string, { score: number; signal: string }>>({});
  const [currency, setCurrency] = useState("$");
  const dropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("finpilot_settings");
      if (stored) setCurrency(getCurrencySymbol(JSON.parse(stored).market || "US"));
    } catch {}
  }, []);

  /* Load 1,542 symbols */
  useEffect(() => {
    fetch("/stock_presets.json")
      .then((r) => r.json())
      .then((d: { presets: { symbols: string[] }[] }) => {
        const set = new Set<string>();
        d.presets.forEach((p) => p.symbols.forEach((s) => set.add(s)));
        setAllSymbols(Array.from(set).sort());
      })
      .catch(() => {});
  }, []);

  /* Outside-click close dropdown */
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) setDropOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  /* Live prices */
  const { data: live } = useStockPrices(tickers);

  /* Derived watchlist data — merge scan results */
  const watchlist = tickers.map((t) => {
    const base = withLivePrice(genStock(t), live[t]);
    const sr = scanResults[t];
    if (sr) {
      return { ...base, score: sr.score, signal: sr.signal };
    }
    return base;
  });

  /* Filtered dropdown */
  const filtered = search.length >= 1
    ? allSymbols.filter((s) => s.startsWith(search.toUpperCase()) && !tickers.includes(s)).slice(0, 40)
    : [];

  /* Add / Remove */
  const addTicker = (sym: string) => {
    const s = sym.trim().toUpperCase();
    if (s && !tickers.includes(s)) {
      const next = [...tickers, s];
      setTickers(next);
      try { localStorage.setItem(WATCHLIST_KEY, JSON.stringify(next)); } catch {}
    }
    setSearch("");
    setDropOpen(false);
  };
  const removeTicker = (sym: string) => {
    const next = tickers.filter((t) => t !== sym);
    setTickers(next);
    try { localStorage.setItem(WATCHLIST_KEY, JSON.stringify(next)); } catch {}
  };

  /* Scan watchlist — REAL API */
  const runScan = async () => {
    if (scanning || tickers.length === 0) return;
    setScanning(true);
    setScanDone(false);
    setScanPct(0);
    try {
      setScanPct(20);
      const res = await fetch("/py-api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbols: tickers }),
      });
      setScanPct(80);
      if (res.ok) {
        const data = await res.json();
        const results: Record<string, { score: number; signal: string }> = {};
        for (const [sym, d] of Object.entries(data)) {
          const r = d as Record<string, unknown>;
          const sc = Math.max(Number(r.filter_score ?? 0), Number(r.score ?? 0));
          const normalized = r.composite_score != null
            ? Number(r.composite_score)
            : Math.round((sc / 4) * 100);
          const signal = normalized >= 70 ? "BUY" : normalized >= 45 ? "HOLD" : normalized >= 25 ? "CAUTION" : "SELL";
          results[sym] = { score: normalized, signal };
        }
        setScanResults(results);
      }
      setScanPct(100);
      setScanDone(true);
    } catch {
      /* silent */
    } finally {
      setScanning(false);
    }
  };

  /* Export CSV */
  const exportCSV = () => {
    const header = "Ticker,Name,Price,Change%,Score,Signal\n";
    const rows = watchlist.map((w) => `${w.ticker},${w.name},${w.price},${w.change},${w.score},${w.signal}`).join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "watchlist.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  /* Summary stats */
  const buyCount = watchlist.filter((w) => w.signal === "BUY").length;
  const avgScore = watchlist.length ? Math.round(watchlist.reduce((a, w) => a + w.score, 0) / watchlist.length) : 0;
  const gainers = watchlist.filter((w) => w.change > 0).length;

  const summaryCards = [
    { label: "Tracked", value: watchlist.length, color: C.text1 },
    { label: "Buy Signals", value: buyCount, color: C.green },
    { label: "Avg Score", value: avgScore, color: C.cyan },
    { label: "Gainers", value: gainers, color: C.green },
  ];

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", flexDirection: "column", gap: 24 }}>
      <DemoBanner connected={Object.keys(live).length > 0} />

      {/* ── Tabs ──────────────────────────────────────────── */}
      <div style={{ display: "flex", gap: 4, borderBottom: `1px solid ${C.border}`, paddingBottom: 0 }}>
        {([
          { key: "hisselerim",         label: "★ Hisselerim",           icon: <Star size={14} /> },
          { key: "sinyal-takip",      label: "📅 Sinyal Takip",          icon: <Eye size={14} /> },
          { key: "gecmis",            label: "🗂 Geçmiş",               icon: <History size={14} /> },
          { key: "performans-raporu", label: "📊 Performans",            icon: <BarChart3 size={14} /> },
        ] as const).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              display: "flex", alignItems: "center", gap: 6,
              padding: "10px 18px", fontSize: 13, fontWeight: 600,
              background: "none", border: "none", cursor: "pointer",
              color: activeTab === tab.key ? C.cyan : C.text2,
              borderBottom: activeTab === tab.key ? `2px solid ${C.cyan}` : "2px solid transparent",
              marginBottom: -1,
              transition: "color 0.15s",
            }}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "sinyal-takip" && <SinyalTakipTab />}
      {activeTab === "gecmis" && <GecmisTab />}
      {activeTab === "performans-raporu" && <PerformansRaporuTab />}
      {activeTab === "hisselerim" && (<>
      {/* ── Header ─────────────────────────────────────────── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Star size={20} color={C.yellow} />
            <h1 style={{ fontSize: 20, fontWeight: 600, color: C.text1, margin: 0 }}>Watchlist</h1>
          </div>
          <p style={{ fontSize: 13, color: C.text3, margin: "4px 0 0" }}>Track your favorite stocks and get alerts</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={exportCSV}
            style={{
              display: "flex", alignItems: "center", gap: 6, borderRadius: 12,
              border: `1px solid ${C.border}`, background: C.card,
              padding: "8px 14px", fontSize: 12, color: C.text2, cursor: "pointer",
            }}
          >
            <Download size={14} /> Export CSV
          </button>
          <button
            onClick={runScan}
            disabled={scanning}
            style={{
              display: "flex", alignItems: "center", gap: 6, borderRadius: 12, border: "none",
              background: scanning ? C.card : `linear-gradient(135deg, ${C.cyan}, ${C.blue})`,
              padding: "8px 16px", fontSize: 12, fontWeight: 600,
              color: scanning ? C.text2 : "#000",
              cursor: scanning ? "default" : "pointer",
            }}
          >
            {scanning ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
            {scanning ? `Scanning… ${scanPct}%` : "Scan Watchlist"}
          </button>
        </div>
      </div>

      {/* Progress bar */}
      {scanning && (
        <div style={{ height: 3, borderRadius: 2, background: "rgba(255,255,255,0.06)" }}>
          <div style={{ height: 3, borderRadius: 2, width: `${scanPct}%`, background: `linear-gradient(90deg, ${C.cyan}, ${C.blue})`, transition: "width 0.3s" }} />
        </div>
      )}
      {scanDone && (
        <div style={{ background: "rgba(48,209,88,0.08)", border: "1px solid rgba(48,209,88,0.25)", borderRadius: 12, padding: "10px 16px", fontSize: 12, color: C.green, fontWeight: 500 }}>
          ✓ Scan complete — {watchlist.length} stocks analyzed
        </div>
      )}

      {/* ── Add Symbol (searchable dropdown) ───────────────── */}
      <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, background: C.card, padding: 20 }}>
        <h2 style={{ fontSize: 13, fontWeight: 600, color: C.text1, margin: "0 0 12px" }}>Add Symbols</h2>
        <div style={{ display: "flex", gap: 12, position: "relative" }} ref={dropRef}>
          <div style={{ flex: 1, position: "relative" }}>
            <Search size={14} style={{ position: "absolute", left: 12, top: 11, color: C.text3 }} />
            <input
              type="text"
              placeholder="Search from 1,542 stocks…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setDropOpen(true); }}
              onFocus={() => { if (search.length >= 1) setDropOpen(true); }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && search.trim()) addTicker(search);
              }}
              style={{
                width: "100%", borderRadius: 12, border: `1px solid ${C.border}`,
                background: C.primary, padding: "10px 14px 10px 34px", fontSize: 13,
                color: C.text1, outline: "none", boxSizing: "border-box",
              }}
            />
            {/* Dropdown */}
            {dropOpen && filtered.length > 0 && (
              <div
                style={{
                  position: "absolute", top: 44, left: 0, right: 0, maxHeight: 240,
                  overflowY: "auto", background: "#16161e", border: `1px solid ${C.border}`,
                  borderRadius: 12, zIndex: 50,
                }}
              >
                {filtered.map((s) => (
                  <button
                    key={s}
                    onClick={() => addTicker(s)}
                    style={{
                      display: "flex", alignItems: "center", justifyContent: "space-between",
                      width: "100%", padding: "8px 14px", fontSize: 12, color: C.text1,
                      background: "transparent", border: "none", cursor: "pointer", textAlign: "left",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = C.cardHover)}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    <span style={{ fontWeight: 600 }}>{s}</span>
                    <span style={{ color: C.text3, fontSize: 11 }}>{companyNames[s] || ""}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <button
            onClick={() => { if (search.trim()) addTicker(search); }}
            style={{
              display: "flex", alignItems: "center", gap: 6, borderRadius: 12, border: "none",
              background: "rgba(0,212,255,0.1)", padding: "10px 16px", fontSize: 12,
              fontWeight: 500, color: C.cyan, cursor: "pointer", whiteSpace: "nowrap",
            }}
          >
            <Plus size={14} /> Add
          </button>
        </div>

        {/* Quick add */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 12, alignItems: "center" }}>
          <span style={{ fontSize: 10, color: C.text3 }}>Quick add:</span>
          {popularStocks.filter((s) => !tickers.includes(s)).map((s) => (
            <button
              key={s}
              onClick={() => addTicker(s)}
              style={{
                borderRadius: 6, background: C.primary, border: `1px solid ${C.border}`,
                padding: "2px 8px", fontSize: 10, color: C.text2, cursor: "pointer",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = C.cyan)}
              onMouseLeave={(e) => (e.currentTarget.style.color = C.text2)}
            >
              + {s}
            </button>
          ))}
        </div>
      </div>

      {/* ── Summary Cards ──────────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        {summaryCards.map((c) => (
          <div
            key={c.label}
            style={{
              borderRadius: 12, border: `1px solid ${C.border}`, background: C.card,
              padding: "12px 16px", transition: "border-color 0.2s, background 0.2s",
              ...(hovered === `sum-${c.label}` ? { borderColor: C.borderHover, background: C.cardHover } : {}),
            }}
            onMouseEnter={() => setHovered(`sum-${c.label}`)}
            onMouseLeave={() => setHovered(null)}
          >
            <div style={{ fontSize: 11, color: C.text3 }}>{c.label}</div>
            <div style={{ fontSize: 20, fontWeight: 600, color: c.color, marginTop: 2 }}>{c.value}</div>
          </div>
        ))}
      </div>

      {/* ── Watchlist Grid ─────────────────────────────────── */}
      {watchlist.length === 0 ? (
        <div style={{ textAlign: "center", padding: 40, color: C.text3, fontSize: 13 }}>
          No stocks in your watchlist. Add some above!
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 12 }}>
          {watchlist.map((w) => {
            const isHov = hovered === w.ticker;
            return (
              <div
                key={w.ticker}
                style={{
                  borderRadius: 16, border: `1px solid ${isHov ? C.borderHover : C.border}`,
                  background: isHov ? C.cardHover : C.card, padding: 16,
                  transition: "all 0.2s", cursor: "default",
                }}
                onMouseEnter={() => setHovered(w.ticker)}
                onMouseLeave={() => setHovered(null)}
              >
                {/* Top row */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div>
                      <a
                        href={`/dashboard/analysis?symbol=${w.ticker}`}
                        style={{ fontSize: 14, fontWeight: 600, color: C.text1, textDecoration: "none" }}
                        onMouseEnter={(e) => (e.currentTarget.style.color = C.cyan)}
                        onMouseLeave={(e) => (e.currentTarget.style.color = C.text1)}
                      >
                        {w.ticker}
                        <ExternalLink size={10} style={{ marginLeft: 4, opacity: 0.5, verticalAlign: "middle" }} />
                      </a>
                      <div style={{ fontSize: 11, color: C.text3 }}>{w.name}</div>
                    </div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <SignalBadge signal={w.signal} />
                    <button
                      onClick={() => removeTicker(w.ticker)}
                      style={{
                        borderRadius: 6, padding: 4, background: "transparent", border: "none",
                        color: C.text3, cursor: "pointer",
                        opacity: isHov ? 1 : 0, transition: "opacity 0.2s",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = C.red)}
                      onMouseLeave={(e) => (e.currentTarget.style.color = C.text3)}
                    >
                      <X size={12} />
                    </button>
                  </div>
                </div>

                {/* Price + sparkline row */}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                    <span style={{ fontSize: 18, fontWeight: 700, color: C.text1 }}>{currency}{w.price.toFixed(2)}</span>
                    <span style={{ display: "flex", alignItems: "center", gap: 3, fontSize: 12, fontWeight: 500, color: w.change >= 0 ? C.green : C.red }}>
                      {w.change >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                      {w.change >= 0 ? "+" : ""}{w.change.toFixed(2)}%
                    </span>
                  </div>
                  <Sparkline ticker={w.ticker} />
                </div>

                {/* Score bar */}
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ flex: 1, height: 4, borderRadius: 2, background: "rgba(255,255,255,0.06)" }}>
                    <div
                      style={{
                        height: 4, borderRadius: 2,
                        width: `${w.score}%`,
                        background: w.score >= 75 ? C.green : w.score >= 50 ? C.cyan : C.red,
                        transition: "width 0.5s",
                      }}
                    />
                  </div>
                  <span style={{ fontSize: 10, fontWeight: 500, color: C.text2 }}>{w.score}/100</span>
                </div>

                {/* Quick actions on hover */}
                <div
                  style={{
                    display: "flex", gap: 6, marginTop: 10,
                    opacity: isHov ? 1 : 0, transition: "opacity 0.2s",
                    pointerEvents: isHov ? "auto" : "none",
                  }}
                >
                  <a
                    href={`/dashboard/analysis?symbol=${w.ticker}`}
                    style={{
                      display: "flex", alignItems: "center", gap: 4, borderRadius: 8,
                      background: "rgba(0,212,255,0.08)", padding: "4px 10px",
                      fontSize: 10, color: C.cyan, textDecoration: "none", fontWeight: 500,
                    }}
                  >
                    <BarChart3 size={10} /> Analysis
                  </a>
                  <a
                    href={`/dashboard/backtest?symbol=${w.ticker}`}
                    style={{
                      display: "flex", alignItems: "center", gap: 4, borderRadius: 8,
                      background: "rgba(10,132,255,0.08)", padding: "4px 10px",
                      fontSize: 10, color: C.blue, textDecoration: "none", fontWeight: 500,
                    }}
                  >
                    <Play size={10} /> Backtest
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}
      </>)}
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
