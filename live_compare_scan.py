#!/usr/bin/env python3
"""
FinPilot - Canlı Karşılaştırma Scripti
=======================================
Uploaded scan CSV'sindeki hisseleri Yahoo Finance üzerinden canlı fiyatlarla
karşılaştırır ve top 10 / top 25 / hepsi için rapor üretir.

KULLANIM:
    pip install yfinance pandas tabulate
    python live_compare_scan.py scan_2026-05-full-976489fa.csv

ÇIKTI:
    live_report_TOP10.csv
    live_report_TOP25.csv
    live_report_ALL.csv
    live_report_SUMMARY.txt
"""
import sys
import time
from pathlib import Path

try:
    import pandas as pd
    import yfinance as yf
except ImportError as e:
    print(f"Eksik bağımlılık: {e}\nÇözüm: pip install yfinance pandas tabulate")
    sys.exit(1)


def load_scan(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.rename(columns={"Change%": "ChangePct", "R/R": "RR",
                            "Entry OK": "EntryOK", "HQ Signal": "HQSignal"})
    df["ScanPrice"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
    df["Stop"] = pd.to_numeric(df["Stop"], errors="coerce")
    df["TP"] = pd.to_numeric(df["TP"], errors="coerce")
    df = df.dropna(subset=["ScanPrice", "Score"])
    return df.sort_values("Score", ascending=False).reset_index(drop=True)


def fetch_live_prices(symbols: list[str], batch_size: int = 50) -> dict[str, float]:
    """Batch fetch via yfinance. Returns symbol -> last_price."""
    out: dict[str, float] = {}
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        print(f"  Fetching {i + 1}-{i + len(batch)} / {len(symbols)} ...", flush=True)
        try:
            data = yf.download(
                tickers=" ".join(batch),
                period="1d",
                interval="1m",
                progress=False,
                threads=True,
                group_by="ticker",
            )
            for sym in batch:
                try:
                    if len(batch) == 1:
                        last = data["Close"].dropna().iloc[-1]
                    else:
                        last = data[sym]["Close"].dropna().iloc[-1]
                    out[sym] = float(last)
                except Exception:
                    pass
        except Exception as e:
            print(f"    batch failed: {e}")
        time.sleep(0.5)
    return out


def classify(row) -> str:
    """Pozisyonun TP / Stop bandındaki yerini sınıflandırır."""
    p, stop, tp = row["LivePrice"], row["Stop"], row["TP"]
    if pd.isna(p):
        return "NO_DATA"
    if p >= tp:
        return "TP_HIT"
    if p <= stop:
        return "STOP_HIT"
    band = tp - stop
    if band <= 0:
        return "INVALID"
    progress = (p - stop) / band
    if progress >= 0.66:
        return "NEAR_TP"
    if progress >= 0.33:
        return "MID"
    return "NEAR_STOP"


def build_report(df: pd.DataFrame, live: dict[str, float]) -> pd.DataFrame:
    df = df.copy()
    df["LivePrice"] = df["Symbol"].map(live)
    df["DeltaPct"] = (df["LivePrice"] - df["ScanPrice"]) / df["ScanPrice"] * 100
    df["UpsideToTPPct"] = (df["TP"] - df["LivePrice"]) / df["LivePrice"] * 100
    df["RiskToStopPct"] = (df["Stop"] - df["LivePrice"]) / df["LivePrice"] * 100
    df["State"] = df.apply(classify, axis=1)
    cols = ["Symbol", "Score", "Signal", "ScanPrice", "LivePrice",
            "DeltaPct", "Stop", "TP", "UpsideToTPPct", "RiskToStopPct", "State"]
    return df[cols].round(3)


def summarize(df: pd.DataFrame, label: str) -> str:
    n = len(df)
    have = df["LivePrice"].notna().sum()
    if not have:
        return f"\n=== {label} ===\n  No live data fetched.\n"
    d = df.dropna(subset=["LivePrice"])
    avg_delta = d["DeltaPct"].mean()
    pos = (d["DeltaPct"] > 0).sum()
    neg = (d["DeltaPct"] < 0).sum()
    tp_hit = (d["State"] == "TP_HIT").sum()
    stop_hit = (d["State"] == "STOP_HIT").sum()
    near_tp = (d["State"] == "NEAR_TP").sum()
    near_stop = (d["State"] == "NEAR_STOP").sum()
    mid = (d["State"] == "MID").sum()
    top_winner = d.loc[d["DeltaPct"].idxmax()]
    top_loser = d.loc[d["DeltaPct"].idxmin()]
    return (
        f"\n=== {label} (n={n}, live={have}) ===\n"
        f"  Avg delta vs scan: {avg_delta:+.2f}%\n"
        f"  Positive: {pos} ({pos * 100 / have:.1f}%), Negative: {neg} ({neg * 100 / have:.1f}%)\n"
        f"  TP hit: {tp_hit}, Near TP: {near_tp}, Mid: {mid}, Near Stop: {near_stop}, Stop hit: {stop_hit}\n"
        f"  Best mover: {top_winner['Symbol']} {top_winner['DeltaPct']:+.2f}% (live {top_winner['LivePrice']:.2f})\n"
        f"  Worst mover: {top_loser['Symbol']} {top_loser['DeltaPct']:+.2f}% (live {top_loser['LivePrice']:.2f})\n"
    )


def main():
    if len(sys.argv) < 2:
        print("Kullanim: python live_compare_scan.py <scan.csv>")
        sys.exit(1)
    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Bulunamadi: {csv_path}")
        sys.exit(1)

    print(f"[1/3] Loading scan: {csv_path}")
    scan = load_scan(str(csv_path))
    print(f"      Loaded {len(scan)} symbols, score range {scan['Score'].min()} - {scan['Score'].max()}")

    top10 = scan.head(10)
    top25 = scan.head(25)
    allsymbols = scan

    print("\n[2/3] Fetching live prices from Yahoo Finance...")
    live = fetch_live_prices(allsymbols["Symbol"].tolist())
    print(f"      Got live quotes for {len(live)} / {len(allsymbols)} symbols")

    print("\n[3/3] Building reports...")
    reports = {
        "TOP10": build_report(top10, live),
        "TOP25": build_report(top25, live),
        "ALL":   build_report(allsymbols, live),
    }
    out_dir = csv_path.parent
    for label, df in reports.items():
        path = out_dir / f"live_report_{label}.csv"
        df.to_csv(path, index=False)
        print(f"      Wrote {path}")

    summary = (
        "FinPilot Live Comparison Report\n"
        "================================\n"
        + summarize(reports["TOP10"], "TOP 10")
        + summarize(reports["TOP25"], "TOP 25")
        + summarize(reports["ALL"], "ALL")
    )
    summary_path = out_dir / "live_report_SUMMARY.txt"
    summary_path.write_text(summary)
    print(f"      Wrote {summary_path}")
    print(summary)


if __name__ == "__main__":
    main()
