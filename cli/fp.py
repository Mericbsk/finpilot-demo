"""FinPilot unified CLI — task 28.

Subcommands:
    fp scan      → run the scanner against the configured watchlist
    fp audit     → run scripts/profitcore_audit.py (T+5 outcomes)
    fp paper     → run scripts/paper_trading.py (paper trade simulator)

Registered as a console_script entry point in pyproject.toml:
    fp = "cli.fp:main"

Argparse-only (no click dep) to keep install footprint minimal.
"""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _run_script(rel_path: str, argv: list[str]) -> int:
    """Execute a project script with the given argv as if invoked directly."""
    script = _ROOT / rel_path
    if not script.exists():
        print(f"fp: script not found: {rel_path}", file=sys.stderr)
        return 2
    sys.argv = [str(script), *argv]
    try:
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def _cmd_scan(argv: list[str]) -> int:
    """Run the scanner over the default watchlist (or symbols from --symbols)."""
    ap = argparse.ArgumentParser(prog="fp scan")
    ap.add_argument(
        "--symbols",
        default="AAPL,MSFT,NVDA,GOOGL,META,AMZN,TSLA,AMD",
        help="Comma-separated tickers (default: top-8 US momentum names).",
    )
    args = ap.parse_args(argv)

    from scanner.evaluate import evaluate_symbols_parallel

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    results = evaluate_symbols_parallel(symbols)
    hits = [r for r in (results or []) if r]
    print(f"fp scan: {len(hits)}/{len(symbols)} symbols produced a signal")
    for r in hits:
        sym = r.get("symbol", "?")
        score = r.get("score", r.get("finpilot_score", "?"))
        print(f"  {sym}: score={score}")
    return 0


def _cmd_audit(argv: list[str]) -> int:
    """Run the profit-core audit (T+5 outcome resolution + decile metrics)."""
    return _run_script("scripts/profitcore_audit.py", argv)


def _cmd_paper(argv: list[str]) -> int:
    """Run the paper-trading simulator."""
    return _run_script("scripts/paper_trading.py", argv)


_COMMANDS = {
    "scan": _cmd_scan,
    "audit": _cmd_audit,
    "paper": _cmd_paper,
}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print("Usage: fp <scan|audit|paper> [args...]")
        print("\nSubcommands:")
        for name, fn in _COMMANDS.items():
            doc = (fn.__doc__ or "").strip().splitlines()[0]
            print(f"  {name:<8} {doc}")
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd not in _COMMANDS:
        print(f"fp: unknown subcommand: {cmd}", file=sys.stderr)
        return 2
    return _COMMANDS[cmd](rest)


if __name__ == "__main__":
    raise SystemExit(main())
