/**
 * Runtime proxy for the Python FastAPI backend.
 *
 * Replaces the build-time next.config.ts rewrite so that API_HOST is read at
 * request time instead of being frozen into the routes manifest during `next build`.
 *
 * Any request to  /py-api/<rest>
 * is forwarded to  ${API_HOST}/api/v1/<rest>
 *
 * NOTE: This intentionally uses Node's built-in `http`/`https` modules
 * instead of the global `fetch` API. Node's fetch is backed by `undici`,
 * which has its OWN internal headersTimeout/bodyTimeout (default 300_000ms
 * = 5min) completely separate from any AbortController timeout. Long scans
 * (200-symbol batches with yfinance fallback retries) can take 3-8 minutes
 * server-side, so the backend doesn't send response headers until it's
 * fully done — which exceeds undici's default 5min headersTimeout and
 * throws "fetch failed" / "HeadersTimeoutError" even though our own
 * timeout budget (below) hasn't been reached yet. A custom undici Agent to
 * override this turned out to be unreliable too: Next.js's
 * standalone-output file tracing does not reliably bundle the `undici`
 * npm package into the production image's node_modules, causing
 * "Cannot find module 'undici'" at runtime. Using core `http`/`https`
 * directly avoids both problems (no bundling risk, full control over the
 * socket idle timeout).
 */

import { NextRequest, NextResponse } from "next/server";
import http from "node:http";
import https from "node:https";

const API_HOST = process.env.API_HOST ?? "https://finpilot-api-i745.onrender.com";

async function proxy(req: NextRequest, params: { path: string[] }): Promise<NextResponse> {
  const rest = params.path.join("/");
  const search = req.nextUrl.search ?? "";
  const targetUrl = new URL(`${API_HOST}/api/v1/${rest}${search}`);
  const client = targetUrl.protocol === "https:" ? https : http;

  // Forward all headers except host (causes TLS/SNI mismatch on the backend)
  const headers: Record<string, string> = {};
  req.headers.forEach((value, key) => {
    if (key.toLowerCase() !== "host") headers[key] = value;
  });

  let body: Buffer | undefined;
  if (req.method !== "GET" && req.method !== "HEAD") {
    body = Buffer.from(await req.arrayBuffer());
  }

  // Timeout: 620 s for scan. Batches are now up to 200 symbols (BATCH_SIZE in
  // scanner/page.tsx); Alpaca bulk prefetch + per-symbol eval (with yfinance
  // fallback retries for symbols not covered by Alpaca) can take 3-8 min at
  // that scale. Backend's own _SCAN_TIMEOUT_SECONDS is 600s, so give the
  // proxy a small margin above that instead of aborting first.
  const isScan = rest === "scan" || rest.startsWith("scan/");
  const timeoutMs = isScan ? 620_000 : 20_000;

  return new Promise<NextResponse>((resolve) => {
    const upstreamReq = client.request(
      targetUrl,
      {
        method: req.method,
        headers,
        // Socket idle timeout — replaces undici's hardcoded 300s headers
        // timeout with our own scan-aware budget.
        timeout: timeoutMs,
      },
      (upstreamRes) => {
        if (upstreamRes.statusCode === 204) {
          upstreamRes.resume();
          resolve(new NextResponse(null, { status: 204 }));
          return;
        }
        const chunks: Buffer[] = [];
        upstreamRes.on("data", (chunk: Buffer) => chunks.push(chunk));
        upstreamRes.on("end", () => {
          const responseHeaders = new Headers();
          for (const [key, value] of Object.entries(upstreamRes.headers)) {
            if (["transfer-encoding", "connection", "keep-alive"].includes(key.toLowerCase())) {
              continue;
            }
            if (Array.isArray(value)) {
              for (const v of value) responseHeaders.append(key, v);
            } else if (value !== undefined) {
              responseHeaders.set(key, value);
            }
          }
          resolve(
            new NextResponse(Buffer.concat(chunks), {
              status: upstreamRes.statusCode ?? 502,
              statusText: upstreamRes.statusMessage,
              headers: responseHeaders,
            }),
          );
        });
        upstreamRes.on("error", (err) => {
          console.error(`[py-api proxy] Response stream error for ${targetUrl}:`, err);
          resolve(
            NextResponse.json(
              { detail: "Backend unreachable", target: targetUrl.toString() },
              { status: 502 },
            ),
          );
        });
      },
    );

    upstreamReq.on("timeout", () => {
      upstreamReq.destroy(new Error("Proxy request timed out"));
    });

    upstreamReq.on("error", (err) => {
      const isTimeout = err.message.includes("timed out") || err.message.includes("timeout");
      if (!isTimeout) {
        console.error(`[py-api proxy] Failed to reach ${targetUrl}:`, err);
      }
      resolve(
        NextResponse.json(
          { detail: "Backend unreachable", target: targetUrl.toString() },
          { status: 502 },
        ),
      );
    });

    if (body) upstreamReq.end(body);
    else upstreamReq.end();
  });
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
