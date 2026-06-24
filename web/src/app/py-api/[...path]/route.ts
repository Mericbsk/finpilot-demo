/**
 * Runtime proxy for the Python FastAPI backend.
 *
 * Replaces the build-time next.config.ts rewrite so that API_HOST is read at
 * request time instead of being frozen into the routes manifest during `next build`.
 *
 * Any request to  /py-api/<rest>
 * is forwarded to  ${API_HOST}/api/v1/<rest>
 */

import { NextRequest, NextResponse } from "next/server";

const API_HOST = process.env.API_HOST ?? "http://localhost:8001";

async function proxy(req: NextRequest, params: { path: string[] }): Promise<NextResponse> {
  const rest = params.path.join("/");
  const search = req.nextUrl.search ?? "";
  const target = `${API_HOST}/api/v1/${rest}${search}`;

  // Forward all headers except host (causes TLS/SNI mismatch on the backend)
  const headers = new Headers(req.headers);
  headers.delete("host");

  let body: BodyInit | undefined;
  if (req.method !== "GET" && req.method !== "HEAD") {
    body = await req.arrayBuffer();
  }

  // Timeout: 240 s for scan (50-symbol Alpaca+eval ≈30s, 240s gives 8× safety margin)
  const isScan = rest === "scan" || rest.startsWith("scan/");
  const timeoutMs = isScan ? 240_000 : 20_000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const upstream = await fetch(target, {
      method: req.method,
      headers,
      body,
      signal: controller.signal,
      // @ts-expect-error — Node 18+ fetch accepts duplex
      duplex: "half",
    });
    clearTimeout(timeoutId);

    const responseHeaders = new Headers(upstream.headers);
    // Strip hop-by-hop headers
    for (const h of ["transfer-encoding", "connection", "keep-alive"]) {
      responseHeaders.delete(h);
    }

    return new NextResponse(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    const isTimeout = err instanceof Error && (err.name === "AbortError" || err.message.includes("timeout") || err.message.includes("Timeout"));
    if (!isTimeout) {
      console.error(`[py-api proxy] Failed to reach ${target}:`, err);
    }
    return NextResponse.json(
      { detail: "Backend unreachable", target },
      { status: 502 },
    );
  }
}

export async function GET(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return proxy(req, await params);
}
export async function POST(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return proxy(req, await params);
}
export async function PUT(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return proxy(req, await params);
}
export async function PATCH(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return proxy(req, await params);
}
export async function DELETE(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return proxy(req, await params);
}
