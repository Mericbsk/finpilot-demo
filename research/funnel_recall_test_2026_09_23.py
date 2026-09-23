"""HUNI TASARIM PARAMETRESI: recall@K

Ortusme testi gosterdi ki gunluk-only ilk-N, tam skorun ilk-N'ini tam yakalamiyor.
AMA huni boyle calismak ZORUNDA DEGIL: 1. asama GENIS bir aday havuzu (K) secer,
2. asama o havuza tam veri cekip GERCEK ilk-N'i belirler.

Dogru soru: tam skorun ilk-N'ini yakalamak icin K ne kadar genis olmali?
  recall@K = |gunluk_topK  kesisim  tam_topN| / N
"""

import csv
import random
import statistics
from collections import defaultdict

SRC = "data/backtest_out/full_universe_enriched_eod_only.csv"
RNG = random.Random(20260923)
MAX_RECO = 16.5


def f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def daily_only_score(r):
    s = 0.0
    s += 2.0 if str(r.get("regime")).strip().lower() == "true" else 0.0
    s += 2.0 if str(r.get("direction")).strip().lower() == "true" else 0.0
    s += (f(r.get("score")) or 0.0) * 0.5
    s += (f(r.get("squeeze_factor")) or 0.0) * 1.5
    s += (f(r.get("catalyst_factor")) or 0.0) * 1.5
    s -= (f(r.get("lottery_factor")) or 0.0) * 2.0
    s -= (f(r.get("overnight_gap_factor")) or 0.0) * 1.0
    s += (f(r.get("sentiment")) or 0.0) * 0.5
    return round(max(0.0, min(100.0, (s / MAX_RECO) * 100.0)))


best = {}
with open(SRC, encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        k = (r["symbol"], r["scan_date"])
        ts = r.get("scan_ts", "")
        if k not in best or ts < best[k][0]:
            best[k] = (ts, r)

by_day = defaultdict(list)
for _, r in best.values():
    cs = f(r.get("composite_score"))
    if cs is None:
        continue
    by_day[r["scan_date"]].append((r["symbol"], cs, daily_only_score(r)))

sizes = [len(v) for v in by_day.values()]
print(
    f"gun: {len(by_day)}   gun-basi evren: medyan {statistics.median(sizes):.0f}"
    f"  (min {min(sizes)}, max {max(sizes)})"
)


def ranked(items, idx):
    dec = [(it[idx], RNG.random(), it[0]) for it in items]
    dec.sort(key=lambda t: (-t[0], t[1]))
    return [t[2] for t in dec]


for N in (25, 50):
    print(f"\n{'='*66}\nHEDEF: tam skorun ilk-{N}'i\n{'='*66}")
    print(f"{'K (evrenin %)':>16} {'K (sembol)':>12} {'recall@K':>12} {'kacan':>8}")
    for frac in (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50):
        recalls, ks = [], []
        for _day, items in by_day.items():
            if len(items) < N * 4:
                continue
            K = max(N, int(len(items) * frac))
            full_rank = ranked(items, 1)
            daily_rank = ranked(items, 2)
            target = set(full_rank[:N])
            pool = set(daily_rank[:K])
            recalls.append(len(target & pool) / N)
            ks.append(K)
        if not recalls:
            continue
        med_recall = statistics.median(recalls)
        print(
            f"{frac*100:>14.0f}% {statistics.median(ks):>12.0f}"
            f" {100*med_recall:>11.0f}% {N - med_recall*N:>7.1f}"
        )
