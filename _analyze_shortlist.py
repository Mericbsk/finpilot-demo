"""FinPilot Shortlist Analyzer — Faz 0 Ablation Harness

Run from repo root:
    python _analyze_shortlist.py

Faz 0 ablation report includes:
  - Top-10 signals by finpilot_score
  - Score/direction distribution
  - Decile-lift table (composite_score bucketed into 10 deciles)
  - Per-decile averages of key signal factors
  - Ters-desil / lottery diagnostic (D10 lottery > D1 lottery?)
  - Factor presence across recent shortlist files
"""

import csv
from collections import Counter
from pathlib import Path

# ── Load latest shortlist ────────────────────────────────────────────────────
data_dir = Path("data/shortlists")
files = sorted(data_dir.glob("shortlist_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)

if not files:
    print("No shortlist files found in data/shortlists/")
    raise SystemExit(1)

latest = files[0]
print(f"Analyzing: {latest.name}")

rows = list(csv.DictReader(open(latest, encoding="utf-8")))
print(f"Total rows: {len(rows)}")


def _f(row: dict, key: str, default: float = 0.0) -> float:
    """Safe float extraction from CSV row."""
    try:
        return float(row.get(key) or default)
    except (TypeError, ValueError):
        return default


# ── Top-10 signals ───────────────────────────────────────────────────────────
print("\nTop 10 by finpilot_score:")
rows_sorted = sorted(rows, key=lambda r: _f(r, "finpilot_score"), reverse=True)
for r in rows_sorted[:10]:
    sym = r["symbol"]
    score = r.get("score", "?")
    direction = r.get("direction", "?")
    entry_ok = r.get("entry_ok", "?")
    mkt = r.get("market_status", "?")
    composite = r.get("composite_score", "?")
    fp = r.get("finpilot_score", "?")
    liq = r.get("liquidity_ok", "?")
    lottery = r.get("lottery_factor", "-")
    overnight = r.get("overnight_gap_factor", "-")
    print(
        f"  {sym:6s} score={score} dir={direction} entry_ok={entry_ok} liq={liq} "
        f"composite={composite} fp={fp} lottery={lottery} overnight={overnight}"
    )

score_dist = Counter(r["score"] for r in rows)
dir_dist = Counter(r["direction"] for r in rows)
print(f"\nScore distribution: {dict(sorted(score_dist.items()))}")
print(f"Direction distribution: {dict(dir_dist)}")
print(f'entry_ok True: {sum(1 for r in rows if r["entry_ok"]=="True")}')
print(f'entry_ok False: {sum(1 for r in rows if r["entry_ok"]=="False")}')


# ── Faz 0: Decile-Lift Ablation Report ──────────────────────────────────────
def ablation_report(all_rows: list[dict]) -> None:
    """Print per-decile distribution of composite_score and key factors.

    Proxy for decile-lift until outcome data is available from
    core/horizon_outcomes_db.py. Columns:
      Composite  : avg composite_score for the decile bucket
      AlignR     : avg alignment_ratio (should rise monotonically in healthy scorer)
      MomR       : avg momentum_ratio
      Filt       : avg filter_score
      Lottery    : avg lottery_factor (should be LOW in top decile — else ters-desil)
      Catalyst   : avg catalyst_factor (should be positive in top decile)
      Overnight  : avg overnight_gap_factor
      Entry%     : % of rows with entry_ok=True

    Ters-desil diagnostic: if D10 avg lottery > D1 avg lottery by >0.05 the
    lottery fade-flag (Faz 1) is urgently needed.
    """
    scored = [r for r in all_rows if r.get("composite_score")]
    if not scored:
        print("\n[ablation] No composite_score column in shortlist — skipping decile report.")
        return

    scored.sort(key=lambda r: _f(r, "composite_score"))
    n = len(scored)
    decile_size = max(1, n // 10)

    SEP = "─" * 84
    print(f"\n{SEP}")
    print(f"Faz 0 — Decile Analysis  (n={n}, decile_size≈{decile_size})")
    print(
        f"{'Decile':>7} {'N':>4} {'Composite':>10} {'AlignR':>8} {'MomR':>7} "
        f"{'Filt':>5} {'Lottery':>8} {'Catalyst':>9} {'Overnight':>10} {'Entry%':>7}"
    )
    print(SEP)

    decile_buckets: list[list[dict]] = []
    for d in range(10):
        start = d * decile_size
        end = start + decile_size if d < 9 else n
        bucket = scored[start:end]
        decile_buckets.append(bucket)
        if not bucket:
            continue
        avg = lambda k, b=bucket: sum(_f(r, k) for r in b) / len(b)  # noqa: E731
        entry_pct = 100.0 * sum(1 for r in bucket if r.get("entry_ok") == "True") / len(bucket)
        print(
            f"  D{d+1:02d}   {len(bucket):>4} {avg('composite_score'):>10.1f} "
            f"{avg('alignment_ratio'):>8.3f} {avg('momentum_ratio'):>7.3f} "
            f"{avg('filter_score'):>5.2f} {avg('lottery_factor'):>8.4f} "
            f"{avg('catalyst_factor'):>9.4f} {avg('overnight_gap_factor'):>10.4f} "
            f"{entry_pct:>6.1f}%"
        )
    print(SEP)

    # ── Ters-desil / lottery diagnostic ─────────────────────────────────────
    top = decile_buckets[-1]
    bot = decile_buckets[0]
    top_lottery = sum(_f(r, "lottery_factor") for r in top) / max(1, len(top))
    bot_lottery = sum(_f(r, "lottery_factor") for r in bot) / max(1, len(bot))
    top_comp = sum(_f(r, "composite_score") for r in top) / max(1, len(top))
    bot_comp = sum(_f(r, "composite_score") for r in bot) / max(1, len(bot))

    print(f"\n  Diagnostic → D10 composite={top_comp:.1f}, D1 composite={bot_comp:.1f}")
    if top_lottery > bot_lottery + 0.05:
        print(
            f"  ⚠  TERS-DESİL UYARISI: D10 lottery ({top_lottery:.4f}) > "
            f"D1 lottery ({bot_lottery:.4f})\n"
            f"     Yüksek-skorlu sinyaller lottery-benzeri özellik taşıyor.\n"
            f"     Faz 1 (FINPILOT_ENABLE_LOTTERY_FADE=1) acilen aktif edilmeli."
        )
    elif top_lottery > 0:
        print(f"  ✓ Lottery dağılımı sağlıklı: D10={top_lottery:.4f} ≈ D1={bot_lottery:.4f}")
    else:
        print(
            "  ℹ  Lottery faktörü henüz hesaplanmamış "
            "(FINPILOT_ENABLE_LOTTERY_FADE=1 ile aktif edin)."
        )

    # ── Factor presence flags ────────────────────────────────────────────────
    keys = set(all_rows[0].keys()) if all_rows else set()
    flag = lambda k: "ON ✓" if k in keys and any(_f(r, k) for r in all_rows) else "OFF"  # noqa: E731
    print(
        f"\n  Factor presence in this file:\n"
        f"    lottery_factor      = {flag('lottery_factor')}\n"
        f"    catalyst_factor     = {flag('catalyst_factor')}\n"
        f"    overnight_gap_factor= {flag('overnight_gap_factor')}\n"
        f"    squeeze_factor      = {flag('squeeze_factor')}\n"
        f"    vol_regime          = {flag('vol_regime')}"
    )


ablation_report(rows)


# ── Multi-file factor presence summary ──────────────────────────────────────
def multi_file_summary(max_files: int = 8) -> None:
    """Show which factors are present across the most recent shortlist files."""
    recent = files[:max_files]
    print(f"\n{'─' * 60}")
    print(f"Recent {len(recent)} shortlist files — factor presence:")
    factor_cols = ["lottery_factor", "catalyst_factor", "overnight_gap_factor", "squeeze_factor"]
    for fp_path in recent:
        try:
            reader = csv.DictReader(open(fp_path, encoding="utf-8"))
            r0 = next(reader)
            flags = " | ".join(
                f"{k.replace('_factor','')[:8]}={'✓' if k in r0 else '✗'}" for k in factor_cols
            )
            print(f"  {fp_path.name[:50]:50s}  {flags}")
        except Exception:
            print(f"  {fp_path.name[:50]:50s}  (unreadable)")


multi_file_summary()
