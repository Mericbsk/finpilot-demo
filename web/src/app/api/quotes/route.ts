import { NextRequest, NextResponse } from "next/server";

/* ── Yahoo Finance via v8/spark (batch) + v8/chart (detail) ── */
const SPARK_URL = "https://query2.finance.yahoo.com/v8/finance/spark";
const CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart";
const UA = "Mozilla/5.0 (compatible; FinPilot/1.0)";

interface CacheEntry {
  price: number;
  change: number;
  prevClose: number;
  high: number;
  low: number;
  volume: number;
  ts: number;
}

const cache = new Map<string, CacheEntry>();
const CACHE_TTL = 30_000; // 30 seconds

/* ── Batch fetch via spark endpoint ────────────────────────── */
async function fetchSpark(symbols: string[]): Promise<Record<string, { price: number; prevClose: number }>> {
  const out: Record<string, { price: number; prevClose: number }> = {};
  try {
    const url = `${SPARK_URL}?symbols=${symbols.join(",")}&range=1d&interval=1d`;
    const resp = await fetch(url, { headers: { "User-Agent": UA }, signal: AbortSignal.timeout(8000), cache: "no-store" });
    if (!resp.ok) return out;
    const data = await resp.json();
    // Yahoo may return flat {SYM: {...}} or nested {spark: {result, error}}
    const entries = data?.spark ? {} : data;
    if (data?.spark?.error) return out; // e.g. "Number of symbols needs to be <= 20"
    for (const [sym, info] of Object.entries(entries) as [string, { close?: number[]; chartPreviousClose?: number }][]) {
      const closes = info.close ?? [];
      const price = closes.length > 0 ? closes[closes.length - 1] : 0;
      const prevClose = info.chartPreviousClose ?? price;
      if (price > 0) out[sym] = { price, prevClose };
    }
  } catch { /* swallow */ }
  return out;
}

/* ── Detail fetch via chart endpoint (for high/low/volume) ── */
async function fetchChart(sym: string): Promise<{ high: number; low: number; volume: number } | null> {
  try {
    const url = `${CHART_URL}/${encodeURIComponent(sym)}?interval=1d&range=1d`;
    const resp = await fetch(url, { headers: { "User-Agent": UA }, signal: AbortSignal.timeout(8000), cache: "no-store" });
    if (!resp.ok) return null;
    const data = await resp.json();
    const meta = data?.chart?.result?.[0]?.meta;
    if (!meta) return null;
    return {
      high: meta.regularMarketDayHigh ?? 0,
      low: meta.regularMarketDayLow ?? 0,
      volume: meta.regularMarketVolume ?? 0,
    };
  } catch { return null; }
}

export async function GET(req: NextRequest) {
  const symbolsParam = req.nextUrl.searchParams.get("symbols") ?? "";
  const detail = req.nextUrl.searchParams.get("detail") === "1"; // single-ticker detail mode
  const symbols = symbolsParam
    .split(",")
    .map((s) => s.trim().toUpperCase())
    .filter(Boolean)
    .slice(0, 500);

  if (symbols.length === 0) {
    return NextResponse.json({ error: "symbols parameter required" }, { status: 400 });
  }

  const now = Date.now();
  const result: Record<string, { price: number; change: number; prevClose: number; high: number; low: number; volume: number }> = {};
  const toFetch: string[] = [];

  for (const sym of symbols) {
    const cached = cache.get(sym);
    if (cached && now - cached.ts < CACHE_TTL) {
      result[sym] = { price: cached.price, change: cached.change, prevClose: cached.prevClose, high: cached.high, low: cached.low, volume: cached.volume };
    } else {
      toFetch.push(sym);
    }
  }

  if (toFetch.length > 0) {
    // Use detail (chart) for single ticker, spark for batch
    if (detail && toFetch.length === 1) {
      const sym = toFetch[0];
      try {
        const url = `${CHART_URL}/${encodeURIComponent(sym)}?interval=1d&range=1d`;
        const resp = await fetch(url, { headers: { "User-Agent": UA }, signal: AbortSignal.timeout(8000), cache: "no-store" });
        if (resp.ok) {
          const d = await resp.json();
          const meta = d?.chart?.result?.[0]?.meta;
          if (meta) {
            const price = Math.round((meta.regularMarketPrice ?? 0) * 100) / 100;
            const prevClose = Math.round((meta.chartPreviousClose ?? price) * 100) / 100;
            const change = prevClose > 0 ? Math.round(((price - prevClose) / prevClose) * 10000) / 100 : 0;
            const high = Math.round((meta.regularMarketDayHigh ?? 0) * 100) / 100;
            const low = Math.round((meta.regularMarketDayLow ?? 0) * 100) / 100;
            const volume = meta.regularMarketVolume ?? 0;
            const entry = { price, change, prevClose, high, low, volume };
            cache.set(sym, { ...entry, ts: now });
            result[sym] = entry;
          }
        }
      } catch { /* swallow */ }
    } else {
      // Batch via spark (Yahoo allows max 20 symbols per request)
      for (let i = 0; i < toFetch.length; i += 10) {
        const batch = toFetch.slice(i, i + 10);
        const sparkData = await fetchSpark(batch);
        for (const sym of batch) {
          const sd = sparkData[sym];
          if (sd && sd.price > 0) {
            const price = Math.round(sd.price * 100) / 100;
            const prevClose = Math.round(sd.prevClose * 100) / 100;
            const change = prevClose > 0 ? Math.round(((price - prevClose) / prevClose) * 10000) / 100 : 0;
            const entry = { price, change, prevClose, high: 0, low: 0, volume: 0 };
            cache.set(sym, { ...entry, ts: now });
            result[sym] = entry;
          }
        }
      }
    }
  }

  return NextResponse.json(result, {
    headers: { "Cache-Control": "public, s-maxage=15, stale-while-revalidate=30" },
  });
}
