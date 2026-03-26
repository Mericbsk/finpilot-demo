"use client";

/**
 * Banner shown on pages that display demo/mock data.
 * When the page connects to the real Python API, it hides automatically.
 */
export default function DemoBanner({
  connected = false,
  label = "Demo Data",
}: {
  connected?: boolean;
  label?: string;
}) {
  if (connected) return null;
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "6px 14px",
        borderRadius: 10,
        fontSize: 11,
        fontWeight: 600,
        color: "#ffd60a",
        backgroundColor: "rgba(255,214,10,0.08)",
        border: "1px solid rgba(255,214,10,0.18)",
        marginBottom: 12,
      }}
    >
      <span>⚠</span>
      <span>{label} — Fiyatlar ve sinyaller gerçek zamanlı değildir. Yatırım tavsiyesi değildir.</span>
    </div>
  );
}
