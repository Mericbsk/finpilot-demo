"""HUNI RECALL RETEST (2026-10-16) - offline, uretime dokunmaz.

Plan 2.0: gunluk-only skor filter_score dahil, canli shortlist ciktisi uzerinde.
Tam skor: composite_score. Gunluk-only skor: Eylul formulu (+ filter_score*1.5 varyanti).
recall@K = |gunluk_topK kesisim tam_topN| / N

Sinir: shortlist dosyalari tam 1812 evreni degil, taramada kaydedilen adaylari icerir.
Sonuc bu evrene ozgudur; tam evren recall'i olarak okunmaz.
"""

import csv
import glob
import os
import random
import re
import statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_GLOB = os.path.join(ROOT, "data", "shortlists", "shortlist_2026*.csv")
NAME_RE = re.compile(r"shortlist_(\d{8})_(\d{4})\.csv$")
NEEDED = (
    "symbol", "composite_score", "filter_score", "regime", "direction", "score",
    "squeeze_factor", "catalyst_factor", "lottery_factor", "overnight_gap_factor", "sentiment",
)
MAX_RECO = 16.5
K_FRACS = (0.10, 0.20, 0.30, 0.40, 0.50, 0.75, 1.00)
NS = (25, 50)


def f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def daily_raw(r, use_filter):
    s = 0.0
    s += 2.0 if str(r.get("regime")).strip().lower() == "true" else 0.0
    s += 2.0 if str(r.get("direction")).strip().lower() == "true" else 0.0
    s += (f(r.get("score")) or 0.0) * 0.5
    s += (f(r.get("squeeze_factor")) or 0.0) * 1.5
    s += (f(r.get("catalyst_factor")) or 0.0) * 1.5
    s -= (f(r.get("lottery_factor")) or 0.0) * 2.0
    s -= (f(r.get("overnight_gap_factor")) or 0.0) * 1.0
    s += (f(r.get("sentiment")) or 0.0) * 0.5
    if use_filter:
        s += (f(r.get("filter_score")) or 0.0) * 1.5
    return s


def load():
    best = {}
    skipped = defaultdict(int)
    for path in glob.glob(SRC_GLOB):
        m = NAME_RE.search(os.path.basename(path))
        if not m:
            continue
        d = m.group(1)
        day = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        stamp = d + m.group(2)
        with open(path, encoding="utf-8", errors="replace", newline="") as fh:
            rd = csv.DictReader(fh)
            if not rd.fieldnames or any(c not in rd.fieldnames for c in NEEDED):
                skipped["schema_files"] += 1
                continue
            for r in rd:
                sym = (r.get("symbol") or "").strip()
                if not sym:
                    continue
                if f(r.get("composite_score")) is None or f(r.get("filter_score")) is None:
                    skipped["blank_score_rows"] += 1
                    continue
                k = (day, sym)
                if k not in best or stamp < best[k][0]:
                    best[k] = (stamp, r)
    return best, skipped


def build_days(best, use_filter):
    by_day = defaultdict(list)
    for (day, sym), (_, r) in best.items():
        by_day[day].append((sym, f(r["composite_score"]), daily_raw(r, use_filter)))
    return by_day


def run(by_day, use_filter, rng):
    label = "filter_score DAHIL" if use_filter else "filter_score HARIC (Eylul)"
    days = {d: v for d, v in by_day.items() if len(v) >= 4 * min(NS)}
    pools = [len(v) for v in days.values()]
    print(f"\n{'=' * 70}\n{label}: gun={len(days)}  havuz medyan={statistics.median(pools):.0f}"
          f" (min {min(pools)}, max {max(pools)})\n{'=' * 70}")
    for N in NS:
        print(f"\nHEDEF tam skorun ilk-{N}'i")
        print(f"{'K (havuz %)':>12} {'K medyan':>10} {'recall medyan':>14} {'kacan (ort)':>12}")
        for frac in K_FRACS:
            recalls, ks = [], []
            for items in days.values():
                if len(items) < 4 * N:
                    continue
                K = max(N, int(len(items) * frac))
                full = sorted(items, key=lambda t: (-t[1], rng.random()))
                daily = sorted(items, key=lambda t: (-t[2], rng.random()))
                target = {t[0] for t in full[:N]}
                pool = {t[0] for t in daily[:K]}
                recalls.append(len(target & pool) / N)
                ks.append(K)
            if not recalls:
                continue
            med = statistics.median(recalls)
            print(f"{frac * 100:>11.0f}% {statistics.median(ks):>10.0f}"
                  f" {100 * med:>13.0f}% {N - statistics.mean(recalls) * N:>12.1f}")


def main():
    best, skipped = load()
    print(f"kayit (gun, sembol): {len(best)}  atlanan: {dict(skipped)}")
    rng = random.Random(20261016)
    run(build_days(best, True), True, rng)
    run(build_days(best, False), False, rng)


if __name__ == "__main__":
    main()
