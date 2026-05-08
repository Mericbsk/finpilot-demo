"use client";

import { useEffect, useRef, useState } from "react";
import { Brain, Loader2, X } from "lucide-react";
import { C } from "@/lib/stockData";

interface ExplainPanelProps {
  symbol: string;
  language?: "tr" | "en" | "de";
  onClose: () => void;
}

/**
 * Slide-over panel that streams an AI research summary for a symbol.
 * Opens an SSE connection to /py-api/llm/explain/{symbol}.
 * Renders tokens as they arrive; shows a blinking cursor while streaming.
 */
export function ExplainPanel({ symbol, language = "tr", onClose }: ExplainPanelProps) {
  const [content, setContent] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const url = `/py-api/llm/explain/${encodeURIComponent(symbol)}?language=${language}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as {
          chunk?: string;
          done?: boolean;
          error?: string;
        };
        if (data.error) {
          setError(data.error);
          setDone(true);
          es.close();
          return;
        }
        if (data.done) {
          setDone(true);
          es.close();
          return;
        }
        if (data.chunk) {
          setContent((prev) => prev + data.chunk);
          // Auto-scroll to bottom
          if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
          }
        }
      } catch {
        // ignore malformed events
      }
    };

    es.onerror = () => {
      if (!done) setError("Bağlantı kesildi");
      setDone(true);
      es.close();
    };

    return () => {
      es.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, language]);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className="fixed bottom-0 left-0 right-0 z-50 flex flex-col rounded-t-2xl sm:bottom-auto sm:left-auto sm:right-6 sm:top-16 sm:w-[480px] sm:rounded-2xl"
        style={{
          backgroundColor: C.bg,
          border: `1px solid ${C.border}`,
          maxHeight: "80vh",
          boxShadow: "0 24px 64px rgba(0,0,0,0.6)",
        }}
      >
        {/* Header */}
        <div
          className="flex shrink-0 items-center justify-between px-5 py-4"
          style={{ borderBottom: `1px solid ${C.border}` }}
        >
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-purple-400" />
            <span className="font-semibold" style={{ color: C.text1 }}>
              {symbol}
            </span>
            <span className="text-sm" style={{ color: C.text3 }}>
              AI Analiz
            </span>
            {!done && (
              <Loader2 className="h-4 w-4 animate-spin text-purple-400" />
            )}
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 transition-colors hover:bg-white/10"
            style={{ color: C.text3 }}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-5 py-4 text-sm leading-relaxed"
          style={{ color: C.text2 }}
        >
          {error ? (
            <p className="text-red-400">{error}</p>
          ) : (
            <div className="whitespace-pre-wrap font-mono text-xs">
              {content}
              {!done && (
                <span className="animate-pulse text-purple-400">▌</span>
              )}
              {done && !content && !error && (
                <span style={{ color: C.text3 }}>Yanıt alınamadı.</span>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        {done && (
          <div
            className="shrink-0 px-5 py-3 text-center text-xs"
            style={{ borderTop: `1px solid ${C.border}`, color: C.text3 }}
          >
            Analiz tamamlandı · Groq / Claude / Gemini
          </div>
        )}
      </div>
    </>
  );
}
