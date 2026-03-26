"use client";

import { useEffect } from "react";

const S = {
  card: "#111118",
  text1: "#f5f5f7",
  text2: "#a1a1a6",
  cyan: "#00d4ff",
  border: "rgba(255,255,255,0.12)",
};

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[Dashboard Error]", error);
  }, [error]);

  return (
    <div style={{ padding: 32, display: "flex", justifyContent: "center" }}>
      <div
        style={{
          background: S.card,
          border: `1px solid ${S.border}`,
          borderRadius: 16,
          padding: 32,
          maxWidth: 420,
          width: "100%",
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontSize: 36,
            marginBottom: 16,
          }}
        >
          ⚠
        </div>
        <h3 style={{ color: S.text1, fontSize: 18, fontWeight: 600, margin: "0 0 8px" }}>
          Page Error
        </h3>
        <p style={{ color: S.text2, fontSize: 13, margin: "0 0 20px", lineHeight: 1.5 }}>
          {error.message || "This page encountered an error."}
        </p>
        <button
          onClick={reset}
          style={{
            background: S.cyan,
            color: "#000",
            border: "none",
            borderRadius: 8,
            padding: "8px 24px",
            fontSize: 13,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Retry
        </button>
      </div>
    </div>
  );
}
