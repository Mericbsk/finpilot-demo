"use client";

import { useEffect, useRef, useState } from "react";

export interface LivePriceState {
  price: number | null;
  changePct: number | null;
  connected: boolean;
  error: string | null;
}

/**
 * Streams real-time price updates for a symbol via Server-Sent Events.
 * Connects to /py-api/prices/stream/{symbol} (proxied to FastAPI).
 * Auto-reconnects after 5s on connection loss.
 */
export function useLivePrice(symbol: string | null): LivePriceState {
  const [price, setPrice] = useState<number | null>(null);
  const [changePct, setChangePct] = useState<number | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!symbol) return;

    function connect() {
      const es = new EventSource(`/py-api/prices/stream/${encodeURIComponent(symbol!)}`);
      esRef.current = es;

      es.onopen = () => {
        setConnected(true);
        setError(null);
      };

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as {
            price?: number;
            change_pct?: number;
            error?: string;
          };
          if (data.error) {
            setError(data.error);
            return;
          }
          if (data.price != null) setPrice(data.price);
          if (data.change_pct != null) setChangePct(data.change_pct);
          setError(null);
        } catch {
          // ignore malformed events
        }
      };

      es.onerror = () => {
        setConnected(false);
        es.close();
        // Reconnect after 5s
        retryRef.current = setTimeout(connect, 5000);
      };
    }

    connect();

    return () => {
      esRef.current?.close();
      esRef.current = null;
      if (retryRef.current) clearTimeout(retryRef.current);
      setConnected(false);
    };
  }, [symbol]);

  return { price, changePct, connected, error };
}
