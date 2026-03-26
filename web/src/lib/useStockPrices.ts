"use client";
import { useState, useEffect, useRef, useCallback } from "react";

export interface LiveQuote {
  price: number;
  change: number;      // percent
  prevClose: number;
}

type QuoteMap = Record<string, LiveQuote>;

/* Global in-memory cache shared across all hook instances */
const globalCache: QuoteMap = {};

const REFRESH_MS = 30_000; // 30 seconds

async function fetchQuotes(symbols: string[]): Promise<QuoteMap> {
  if (symbols.length === 0) return {};
  const merged: QuoteMap = {};
  // Split into batches of 100 to avoid URL length limits
  for (let i = 0; i < symbols.length; i += 100) {
    const batch = symbols.slice(i, i + 100);
    try {
      const resp = await fetch(`/api/quotes?symbols=${batch.join(",")}`);
      if (!resp.ok) continue;
      const data: QuoteMap = await resp.json();
      for (const [sym, q] of Object.entries(data)) {
        globalCache[sym] = q;
        merged[sym] = q;
      }
    } catch { /* skip batch */ }
  }
  return merged;
}

/**
 * Hook: fetches real-time stock prices from /api/quotes
 * Returns cached data immediately, refreshes in background.
 */
export function useStockPrices(symbols: string[]) {
  const [data, setData] = useState<QuoteMap>(() => {
    const init: QuoteMap = {};
    for (const s of symbols) {
      if (globalCache[s]) init[s] = globalCache[s];
    }
    return init;
  });
  const [loading, setLoading] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Stable key without mutating the original array
  const symbolsKey = [...symbols].sort().join(",");

  const doFetch = useCallback(async () => {
    if (symbols.length === 0) { setLoading(false); return; }
    const result = await fetchQuotes(symbols);
    if (Object.keys(result).length > 0) {
      setData((prev) => ({ ...prev, ...result }));
    }
    setLoading(false);
  }, [symbolsKey]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setLoading(true);
    doFetch();

    intervalRef.current = setInterval(doFetch, REFRESH_MS);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [doFetch]);

  return { data, loading };
}
