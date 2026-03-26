"use client";

/* ================================================================
   SKELETON COMPONENTS — Loading placeholders for dashboard pages
   ================================================================ */

const S = {
  card: "#111118",
  shimmer: "#1a1a24",
  border: "rgba(255,255,255,0.08)",
};

const pulseKeyframes = `
@keyframes skeletonPulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}
`;

function Pulse({ style }: { style?: React.CSSProperties }) {
  return (
    <div
      style={{
        background: S.shimmer,
        borderRadius: 6,
        animation: "skeletonPulse 1.5s ease-in-out infinite",
        ...style,
      }}
    />
  );
}

/* ── Card Skeleton ───────────────────────────────────────── */
export function CardSkeleton({ count = 4 }: { count?: number }) {
  return (
    <>
      <style>{pulseKeyframes}</style>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(240px,1fr))", gap: 16 }}>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            style={{
              background: S.card,
              border: `1px solid ${S.border}`,
              borderRadius: 14,
              padding: 20,
            }}
          >
            <Pulse style={{ width: "60%", height: 14, marginBottom: 12 }} />
            <Pulse style={{ width: "40%", height: 28, marginBottom: 16 }} />
            <Pulse style={{ width: "80%", height: 10 }} />
          </div>
        ))}
      </div>
    </>
  );
}

/* ── Table Row Skeleton ──────────────────────────────────── */
export function TableRowSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <>
      <style>{pulseKeyframes}</style>
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr 1fr 0.5fr",
              gap: 12,
              padding: "12px 16px",
              background: S.card,
              borderRadius: i === 0 ? "10px 10px 0 0" : i === rows - 1 ? "0 0 10px 10px" : 0,
              borderBottom: i < rows - 1 ? `1px solid ${S.border}` : "none",
            }}
          >
            <Pulse style={{ height: 14 }} />
            <Pulse style={{ height: 14, width: "70%" }} />
            <Pulse style={{ height: 14, width: "50%" }} />
            <Pulse style={{ height: 14, width: "60%" }} />
            <Pulse style={{ height: 14, width: "40%" }} />
          </div>
        ))}
      </div>
    </>
  );
}

/* ── Chart Skeleton ──────────────────────────────────────── */
export function ChartSkeleton({ height = 280 }: { height?: number }) {
  return (
    <>
      <style>{pulseKeyframes}</style>
      <div
        style={{
          background: S.card,
          border: `1px solid ${S.border}`,
          borderRadius: 14,
          padding: 20,
          height,
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <Pulse style={{ width: 120, height: 16 }} />
          <Pulse style={{ width: 80, height: 16 }} />
        </div>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 6, height: "60%", paddingTop: 16 }}>
          {Array.from({ length: 12 }).map((_, i) => (
            <Pulse
              key={i}
              style={{
                flex: 1,
                height: `${30 + ((i * 37) % 70)}%`,
                borderRadius: "4px 4px 0 0",
              }}
            />
          ))}
        </div>
        <Pulse style={{ width: "100%", height: 8, marginTop: 12 }} />
      </div>
    </>
  );
}
