"""Collect SEC CompanyFacts into an append-only research ledger.

Example:
    python -m research.collect_sec_companyfacts --symbol AAPL \
        --user-agent "FinPilot research contact@example.com"
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from research.sec_companyfacts import append_snapshot, fetch_companyfacts, normalize_companyfacts

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
DEFAULT_OUT = Path("data/research/sec_companyfacts.jsonl")


def fetch_ticker_map(*, user_agent: str, timeout: int = 30) -> dict[str, str]:
    from urllib.request import Request, urlopen

    request = Request(  # noqa: S310
        TICKERS_URL,
        headers={"User-Agent": user_agent, "Accept": "application/json"},
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310  # nosec B310
        payload = json.load(response)
    return {
        str(row["ticker"]).upper(): str(row["cik_str"]).zfill(10)
        for row in payload.values()
        if row.get("ticker") and row.get("cik_str") is not None
    }


def collect(symbols: list[str], *, user_agent: str, output: Path, delay: float) -> dict[str, Any]:
    """Fetch and append one SEC CompanyFacts envelope per resolved symbol."""
    if not user_agent.strip():
        raise ValueError("--user-agent is required for SEC requests")
    ticker_map = fetch_ticker_map(user_agent=user_agent)
    result: dict[str, Any] = {"collected": [], "missing_symbols": [], "failed": []}
    unique_symbols = list(dict.fromkeys(symbol.upper() for symbol in symbols))
    for index, symbol in enumerate(unique_symbols):
        cik = ticker_map.get(symbol)
        if not cik:
            result["missing_symbols"].append(symbol)
            continue
        try:
            payload = fetch_companyfacts(cik, user_agent=user_agent)
            records = normalize_companyfacts(payload, cik=cik)
            envelope = append_snapshot(output, records)
            result["collected"].append(
                {"symbol": symbol, "cik": cik, "records": envelope["record_count"]}
            )
        except Exception as exc:  # noqa: BLE001
            result["failed"].append({"symbol": symbol, "cik": cik, "error": str(exc)})
        if index + 1 < len(unique_symbols):
            time.sleep(max(0.1, delay))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", action="append", required=True)
    parser.add_argument("--user-agent", required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--delay", type=float, default=0.2)
    args = parser.parse_args()
    result = collect(args.symbol, user_agent=args.user_agent, output=args.output, delay=args.delay)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
