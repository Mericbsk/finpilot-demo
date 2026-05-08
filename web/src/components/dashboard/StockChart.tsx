"use client";

import { useEffect, useRef, useState } from "react";
import { C } from "@/lib/stockData";

interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface ChartData {
  symbol: string;
  interval: string;
  candles: Candle[];
  sma50: { time: number; value: number }[];
}

interface Props {
  symbol: string;
  interval?: "1d" | "1h" | "4h" | "15m";
  days?: number;
  height?: number;
}

export default function StockChart({ symbol, interval = "1d", days = 90, height = 300 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!containerRef.current) return;
    let chart: import("lightweight-charts").IChartApi | null = null;
    let cancelled = false;

    setLoading(true);
    setError(null);

    const run = async () => {
      try {
        const [{ createChart, CandlestickSeries, LineSeries, ColorType }, res] = await Promise.all([
          import("lightweight-charts"),
          fetch(`/py-api/chart/${symbol}?interval=${interval}&days=${days}`),
        ]);

        if (cancelled) return;

        if (!res.ok) {
          setError(`No chart data for ${symbol}`);
          setLoading(false);
          return;
        }

        const data: ChartData = await res.json();
        if (cancelled || !containerRef.current) return;

        chart = createChart(containerRef.current, {
          width: containerRef.current.clientWidth,
          height,
          layout: {
            background: { type: ColorType.Solid, color: "transparent" },
            textColor: C.text3,
            fontSize: 11,
          },
          grid: {
            vertLines: { color: "rgba(255,255,255,0.04)" },
            horzLines: { color: "rgba(255,255,255,0.04)" },
          },
          crosshair: {
            vertLine: { color: "rgba(0,212,255,0.3)", labelBackgroundColor: C.cyan },
            horzLine: { color: "rgba(0,212,255,0.3)", labelBackgroundColor: C.cyan },
          },
          rightPriceScale: { borderColor: "rgba(255,255,255,0.08)" },
          timeScale: { borderColor: "rgba(255,255,255,0.08)", timeVisible: true },
        });

        const candleSeries = chart.addSeries(CandlestickSeries, {
          upColor: C.green,
          downColor: C.red,
          borderUpColor: C.green,
          borderDownColor: C.red,
          wickUpColor: C.green,
          wickDownColor: C.red,
        });

        candleSeries.setData(
          data.candles.map((c) => ({
            time: c.time as import("lightweight-charts").UTCTimestamp,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
          })),
        );

        if (data.sma50.length > 0) {
          const smaSeries = chart.addSeries(LineSeries, {
            color: C.yellow,
            lineWidth: 1,
            priceLineVisible: false,
          });
          smaSeries.setData(
            data.sma50.map((p) => ({
              time: p.time as import("lightweight-charts").UTCTimestamp,
              value: p.value,
            })),
          );
        }

        chart.timeScale().fitContent();

        const ro = new ResizeObserver(() => {
          if (containerRef.current && chart) {
            chart.applyOptions({ width: containerRef.current.clientWidth });
          }
        });
        ro.observe(containerRef.current);

        setLoading(false);

        return () => ro.disconnect();
      } catch {
        if (!cancelled) {
          setError("Chart unavailable");
          setLoading(false);
        }
      }
    };

    run();

    return () => {
      cancelled = true;
      chart?.remove();
    };
  }, [symbol, interval, days, height]);

  return (
    <div style={{ position: "relative", width: "100%", height }}>
      {loading && !error && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: C.text3,
            fontSize: 12,
          }}
        >
          Loading chart…
        </div>
      )}
      {error && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: C.text3,
            fontSize: 12,
          }}
        >
          {error}
        </div>
      )}
      <div ref={containerRef} style={{ width: "100%", height, opacity: loading || error ? 0 : 1 }} />
    </div>
  );
}
