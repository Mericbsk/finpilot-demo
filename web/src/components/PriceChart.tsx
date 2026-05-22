"use client";

import { useEffect, useRef, useState } from "react";
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  type IChartApi,
} from "lightweight-charts";

interface OHLCVBar {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface EMAPoint {
  time: string;
  value: number;
}

interface OHLCVResponse {
  bars: OHLCVBar[];
  ema20: EMAPoint[];
}

interface PriceChartProps {
  symbol: string;
  height?: number;
}

const API_BASE = "/py-api";

export default function PriceChart({ symbol, height = 260 }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /* â”€â”€ Init chart once on mount â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const chart = createChart(el, {
      width: el.clientWidth,
      height,
      layout: {
        background: { color: "transparent" },
        textColor: "#8e8ea0",
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.04)" },
        horzLines: { color: "rgba(255,255,255,0.04)" },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.08)" },
      timeScale: {
        borderColor: "rgba(255,255,255,0.08)",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    const ro = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.resize(containerRef.current.clientWidth, height);
      }
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [height]);

  /* â”€â”€ Fetch + rebuild series when symbol changes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(
      `${API_BASE}/history/ohlcv?symbol=${encodeURIComponent(symbol)}&period=3mo&interval=1d`
    )
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<OHLCVResponse>;
      })
      .then((data) => {
        if (cancelled || !chartRef.current) return;
        const c = chartRef.current;

        // Remove existing series by removing all panes except the first,
        // then clear the main pane by replacing series.
        // Simplest: recreate via removing & re-adding series.
        const sorted = [...data.bars].sort((a, b) =>
          a.time < b.time ? -1 : a.time > b.time ? 1 : 0
        );

        const candle = c.addSeries(CandlestickSeries, {
          upColor: "#30d158",
          downColor: "#ff453a",
          borderUpColor: "#30d158",
          borderDownColor: "#ff453a",
          wickUpColor: "#30d158",
          wickDownColor: "#ff453a",
        });

        const volumePane = c.addPane();
        volumePane.setStretchFactor(0.25);
        const volume = volumePane.addSeries(HistogramSeries, {
          priceFormat: { type: "volume" },
        });

        const ema = c.addSeries(LineSeries, {
          color: "#0a84ff",
          lineWidth: 1,
          lastValueVisible: false,
          priceLineVisible: false,
        });

        candle.setData(
          sorted.map((b) => ({
            time: b.time,
            open: b.open,
            high: b.high,
            low: b.low,
            close: b.close,
          }))
        );

        volume.setData(
          sorted.map((b) => ({
            time: b.time,
            value: b.volume,
            color:
              b.close >= b.open
                ? "rgba(48,209,88,0.4)"
                : "rgba(255,69,58,0.4)",
          }))
        );

        ema.setData(data.ema20 ?? []);

        c.timeScale().fitContent();
        setLoading(false);
      })
      .catch((e: Error) => {
        if (cancelled) return;
        setError(e.message);
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [symbol]);

  return (
    <div
      className="relative w-full"
      style={{ height: `${height}px` }} // eslint-disable-line react/forbid-component-props
    >
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} /> {/* eslint-disable-line react/forbid-component-props */}
      {loading && (
        <div
          className="absolute inset-0 flex items-center justify-center text-xs"
          style={{ color: "#8e8ea0" }} // eslint-disable-line react/forbid-component-props
        >
          Loading chartâ€¦
        </div>
      )}
      {!loading && error && (
        <div
          className="absolute inset-0 flex items-center justify-center text-xs"
          style={{ color: "#ff453a" }} // eslint-disable-line react/forbid-component-props
        >
          Chart unavailable
        </div>
      )}
    </div>
  );
}
