"use client";

import { useEffect } from "react";

const S = {
  bg: "#000000",
  card: "#111118",
  text1: "#f5f5f7",
  text2: "#a1a1a6",
  red: "#ff453a",
  cyan: "#00d4ff",
  border: "rgba(255,255,255,0.12)",
};

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[FinPilot Error]", error);
  }, [error]);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: S.bg,
        padding: 24,
      }}
    >
      <div
        style={{
          background: S.card,
          border: `1px solid ${S.border}`,
          borderRadius: 16,
          padding: 40,
          maxWidth: 480,
          width: "100%",
          textAlign: "center",
        }}
      >
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: "50%",
            background: "rgba(255,69,58,0.15)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 20px",
            fontSize: 28,
          }}
        >
          ⚠
        </div>
        <h2
          style={{
            color: S.text1,
            fontSize: 22,
            fontWeight: 600,
            margin: "0 0 8px",
          }}
        >
          Something went wrong
        </h2>
        <p
          style={{
            color: S.text2,
            fontSize: 14,
            margin: "0 0 24px",
            lineHeight: 1.5,
          }}
        >
          {error.message || "An unexpected error occurred. Please try again."}
        </p>
        <button
          onClick={reset}
          style={{
            background: S.cyan,
            color: "#000",
            border: "none",
            borderRadius: 10,
            padding: "10px 28px",
            fontSize: 14,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Try Again
        </button>
      </div>
    </div>
  );
}
