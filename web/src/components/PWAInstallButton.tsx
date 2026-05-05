"use client";

import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { C } from "@/lib/stockData";

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

export default function PWAInstallButton() {
  const [prompt, setPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [installed, setInstalled] = useState(false);

  useEffect(() => {
    // Already running as installed PWA
    if (window.matchMedia("(display-mode: standalone)").matches) {
      setInstalled(true);
      return;
    }

    const handler = (e: Event) => {
      e.preventDefault();
      setPrompt(e as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", handler);

    window.addEventListener("appinstalled", () => {
      setInstalled(true);
      setPrompt(null);
    });

    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  if (installed || !prompt) return null;

  const install = async () => {
    if (!prompt) return;
    await prompt.prompt();
    const { outcome } = await prompt.userChoice;
    if (outcome === "accepted") {
      setInstalled(true);
      setPrompt(null);
    }
  };

  return (
    <button
      onClick={install}
      title="Masaüstüne Kur"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        padding: "6px 12px",
        borderRadius: 8,
        border: `1px solid ${C.border}`,
        background: "rgba(0,212,255,0.08)",
        color: C.cyan,
        fontSize: 12,
        fontWeight: 600,
        cursor: "pointer",
        transition: "background 0.2s",
        whiteSpace: "nowrap",
      }}
      onMouseEnter={(e) =>
        (e.currentTarget.style.background = "rgba(0,212,255,0.18)")
      }
      onMouseLeave={(e) =>
        (e.currentTarget.style.background = "rgba(0,212,255,0.08)")
      }
    >
      <Download size={13} />
      Uygulamayı Kur
    </button>
  );
}
