import { NextRequest, NextResponse } from "next/server";

/**
 * GET /api/quotes?symbols=AAPL,MSFT,...
 *
 * Proxies to the Python FastAPI backend (/api/v1/quotes) which uses
 * yfinance for real-time quotes. This avoids Yahoo Finance IP/UA blocks
 * that affect direct browser or Node.js fetch calls.
 */

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8001";

export async function GET(req: NextRequest) {
  const symbolsParam = req.nextUrl.searchParams.get("symbols") ?? "";
  if (!symbolsParam.trim()) {
    return NextResponse.json({ error: "symbols parameter required" }, { status: 400 });
  }

  try {
    const upstream = await fetch(
      `${BACKEND_URL}/api/v1/quotes?symbols=${encodeURIComponent(symbolsParam)}`,
      { signal: AbortSignal.timeout(15_000), cache: "no-store" },
    );
    if (!upstream.ok) {
      return NextResponse.json({}, { status: upstream.status });
    }
    const data = await upstream.json();
    return NextResponse.json(data, {
      headers: { "Cache-Control": "public, s-maxage=15, stale-while-revalidate=30" },
    });
  } catch {
    return NextResponse.json({});
  }
}
