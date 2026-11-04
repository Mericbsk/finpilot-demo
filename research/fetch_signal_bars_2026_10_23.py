"""Read-only price fetch for the signal outcome evaluation (2026-10-23).

Downloads raw daily OHLCV bars (2026-04-01 .. today) for the symbols listed in
data/signal_eval_symbols_2026-10-23.txt and writes one JSON file per symbol
to data/price_cache_signal_eval_2026-10-23/.

It does NOT touch data/price_cache/, the database, or any production code.

Run from the repo root (PowerShell), inside the running api container:
    Get-Content research\\fetch_signal_bars_2026_10_23.py | docker compose exec -T api python -
"""

from __future__ import annotations

import json
from pathlib import Path

import yfinance as yf

# Inside the api container ./data is mounted at /app/data; otherwise use repo data/.
_CONTAINER_DATA = Path("/app/data")
DATA = _CONTAINER_DATA if _CONTAINER_DATA.is_dir() else Path.cwd() / "data"
SYMBOLS_FILE = DATA / "signal_eval_symbols_2026-10-23.txt"
OUT_DIR = DATA / "price_cache_signal_eval_2026-10-23"
START = "2026-04-01"
BATCH = 50


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    symbols = [s.strip() for s in SYMBOLS_FILE.read_text().splitlines() if s.strip()]
    written, empty = 0, []
    for i in range(0, len(symbols), BATCH):
        chunk = symbols[i : i + BATCH]
        df = yf.download(
            chunk, start=START, interval="1d", auto_adjust=False,
            group_by="ticker", progress=False, threads=True, timeout=30,
        )
        for sym in chunk:
            try:
                sub = df[sym] if len(chunk) > 1 else df
                sub = sub.dropna(subset=["Open", "High", "Low", "Close"])
            except Exception:
                empty.append(sym)
                continue
            if sub.empty:
                empty.append(sym)
                continue
            bars = [
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": float(r["Open"]), "high": float(r["High"]),
                    "low": float(r["Low"]), "close": float(r["Close"]),
                    "volume": float(r.get("Volume", 0) or 0),
                }
                for idx, r in sub.iterrows()
            ]
            (OUT_DIR / f"{sym}.json").write_text(json.dumps(bars), encoding="utf-8")
            written += 1
        print(f"{min(i + BATCH, len(symbols))}/{len(symbols)} done")
    print(f"written: {written}, no data: {len(empty)}")
    if empty:
        print("no data:", ", ".join(empty))


if __name__ == "__main__":
    main()
