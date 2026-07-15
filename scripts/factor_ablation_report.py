#!/usr/bin/env python3
"""Factor ablation report — which gated flag actually moves the needle?

Reads the last N days of daily scan exports (data/distribution/scan_export_*.json),
attaches each candidate's FORWARD daily prices (fetched fresh), labels every
signal with the triple-barrier method, and runs an ablation for every factor:
does the HIGH-factor bucket beat the LOW-factor bucket?

Every factor VALUE is already recorded in the exports (even for flags that are
OFF), so this measures all of them WITHOUT enabling anything live — pure,
after-the-fact analysis. Use the result to decide which flags to turn on.

Usage:
    python scripts/factor_ablation_report.py                 # last 14 days
    python scripts/factor_ablation_report.py --days 30 --horizon 10
    python scripts/factor_ablation_report.py --tp 0.08 --sl 0.04

Output: a Markdown table to stdout and to
    data/distribution/factor_ablation_<today>.md

Interpretation:
    * "edge" factor with helps=EVET  → HIGH bucket outperforms → worth enabling.
    * "fade" factor with helps=EVET  → HIGH bucket UNDERperforms → penalty is
      justified → worth enabling as a penalty.
    * helps=hayır → no clean separation on this sample → do NOT enable yet.
    * Always check n_hi / n_lo: a "helps" verdict on <~30 per bucket is noise.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scanner.edge_report import (
    ablate_all,
    build_edge_report,
    format_ablation_md,
    format_edge_report_md,
)  # noqa: E402

_EXPORT_GLOB = "data/distribution/scan_export_2*.json"


def _load_exports(days: int) -> list[dict]:
    """Return candidate records from the last ``days`` daily exports.

    Each record carries the scan date, entry price and every factor field.
    """
    cutoff = date.today() - timedelta(days=days)
    records: list[dict] = []
    for path in sorted(glob.glob(_EXPORT_GLOB)):
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"  skip {path}: {exc}", file=sys.stderr)
            continue
        scan_date = payload.get("date")
        try:
            d = datetime.strptime(scan_date, "%Y-%m-%d").date()
        except Exception:
            continue
        if d < cutoff:
            continue
        results = payload.get("results") or []
        if isinstance(results, dict):
            results = list(results.values())
        for r in results:
            sym = r.get("symbol") or r.get("ticker")
            price = r.get("price") or r.get("entry")
            if not sym or not price:
                continue
            rec = dict(r)
            rec["symbol"] = sym
            rec["entry_price"] = float(price)
            rec["scan_date"] = scan_date
            records.append(rec)
    return records


def _attach_forward_prices(records: list[dict], horizon: int) -> list[dict]:
    """Fetch forward daily OHLC for each (symbol, scan_date) via yfinance.

    Best-effort: records whose forward window cannot be fetched are dropped.
    Groups by symbol to minimise calls. Runs in the user's env (network OK).
    """
    try:
        import yfinance as yf  # type: ignore[import]
    except Exception:
        print("yfinance not available — cannot fetch forward prices.", file=sys.stderr)
        return []

    # Widest window we need per symbol.
    by_symbol: dict[str, list[dict]] = {}
    for r in records:
        by_symbol.setdefault(r["symbol"], []).append(r)

    out: list[dict] = []
    for sym, recs in by_symbol.items():
        try:
            dates = [datetime.strptime(r["scan_date"], "%Y-%m-%d").date() for r in recs]
            start = min(dates)
            end = max(dates) + timedelta(days=horizon * 2 + 7)  # buffer for weekends/holidays
            data = yf.download(
                sym,
                start=start.isoformat(),
                end=end.isoformat(),
                interval="1d",
                progress=False,
                auto_adjust=True,
            )
            if data is None or data.empty:
                continue
            closes = data["Close"].squeeze()
            highs = data["High"].squeeze()
            lows = data["Low"].squeeze()
            idx = [i.date() if hasattr(i, "date") else i for i in data.index]
        except Exception as exc:  # noqa: BLE001
            print(f"  fetch fail {sym}: {exc}", file=sys.stderr)
            continue

        for r in recs:
            d0 = datetime.strptime(r["scan_date"], "%Y-%m-%d").date()
            # forward bars are those strictly AFTER the scan date
            fwd_idx = [j for j, dd in enumerate(idx) if dd > d0][:horizon]
            if len(fwd_idx) < 2:
                continue
            r["forward_closes"] = [float(closes.iloc[j]) for j in fwd_idx]
            r["forward_highs"] = [float(highs.iloc[j]) for j in fwd_idx]
            r["forward_lows"] = [float(lows.iloc[j]) for j in fwd_idx]
            r["side"] = "long"
            out.append(r)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--days", type=int, default=14, help="lookback window of exports (default 14)")
    ap.add_argument("--horizon", type=int, default=10, help="time barrier in trading days")
    ap.add_argument("--tp", type=float, default=0.10, help="take-profit fraction")
    ap.add_argument("--sl", type=float, default=0.05, help="stop-loss fraction")
    args = ap.parse_args()

    print(f"Loading exports (last {args.days} days)…", file=sys.stderr)
    records = _load_exports(args.days)
    print(f"  {len(records)} candidate rows across the window", file=sys.stderr)
    if not records:
        print("No candidates found. Check data/distribution/scan_export_*.json.", file=sys.stderr)
        return 1

    print("Fetching forward prices…", file=sys.stderr)
    labeled = _attach_forward_prices(records, args.horizon)
    print(f"  {len(labeled)} signals with a usable forward window", file=sys.stderr)
    if not labeled:
        return 1

    tier_report = build_edge_report(
        labeled, tp_pct=args.tp, sl_pct=args.sl, max_horizon=args.horizon, group_by="tier"
    )
    ablation = ablate_all(labeled, tp_pct=args.tp, sl_pct=args.sl, max_horizon=args.horizon)

    md = (
        format_ablation_md(ablation, title=f"Factor Ablation — last {args.days} days")
        + "\n\n"
        + format_edge_report_md(tier_report, title="By early-detection tier")
        + "\n\n_Post-cost note: apply ~0.55% round-trip (RealisticBacktestCosts) to expectancy "
        "before trusting any factor. A 'helps=EVET' on <~30/bucket is noise._\n"
    )
    print(md)
    out_path = Path("data/distribution") / f"factor_ablation_{date.today().isoformat()}.md"
    try:
        out_path.write_text(md, encoding="utf-8")
        print(f"\nWritten: {out_path}", file=sys.stderr)
    except Exception as exc:  # noqa: BLE001
        print(f"write failed: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
