"""HUNI ORTUSME TESTI (2026-09-23) — offline, uretime dokunmaz.

SORU: Gunluk-veriyle siralanan ilk N aday, TAM veriyle siralanan ilk N ile
ortusuyor mu? Ortusmuyorsa huni bir hizlandirma degil, DAVRANIS DEGISIKLIGIDIR.

YONTEM:
  tam siralama      = stored `composite_score` (uretimde intraday ILE hesaplandi)
  gunluk-only       = ayni formul, alignment_ratio/momentum_ratio/filter_score
                      terimleri OLMADAN, sonra strength%'e cevrilir
  Gun bazinda ilk-N kesisimi olculur.

KONTROL: rastgele secim. Ortusme rastgeleden anlamli derecede yuksek degilse
huni "ayni adaylari seciyor" diyemez.

TIE UYARISI: composite_score 99.78% tie orani tasiyor. Esitlikler determinist
kirilirsa (or. alfabetik) ortusme YAPAY olarak yuksek cikar. Bu yuzden esitlik
RASTGELE kiriliyor (sabit tohum) ve sinirdaki tie yogunlugu ayrica raporlaniyor.
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
    """Intraday terimleri OLMADAN skor -> strength% (0-100)."""
    s = 0.0
    s += 2.0 if str(r.get("regime")).strip().lower() == "true" else 0.0
    s += 2.0 if str(r.get("direction")).strip().lower() == "true" else 0.0
    s += (f(r.get("score")) or 0.0) * 0.5
    sq = f(r.get("squeeze_factor"))
    s += (sq or 0.0) * 1.5
    ca = f(r.get("catalyst_factor"))
    s += (ca or 0.0) * 1.5
    lo = f(r.get("lottery_factor"))
    s -= (lo or 0.0) * 2.0
    og = f(r.get("overnight_gap_factor"))
    s -= (og or 0.0) * 1.0
    se = f(r.get("sentiment"))
    s += (se or 0.0) * 0.5
    return round(max(0.0, min(100.0, (s / MAX_RECO) * 100.0)))


# dedup
best = {}
with open(SRC, encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        k = (r["symbol"], r["scan_date"])
        ts = r.get("scan_ts", "")
        if k not in best or ts < best[k][0]:
            best[k] = (ts, r)
rows = [r for _, r in best.values()]

by_day = defaultdict(list)
for r in rows:
    cs = f(r.get("composite_score"))
    if cs is None:
        continue
    by_day[r["scan_date"]].append((r["symbol"], cs, daily_only_score(r)))

print(f"gun sayisi: {len(by_day)}   toplam satir: {sum(len(v) for v in by_day.values())}")


def topn(items, key_idx, n):
    """Rastgele tie-break ile ilk n sembol kumesi."""
    dec = [(it[key_idx], RNG.random(), it[0]) for it in items]
    dec.sort(key=lambda t: (-t[0], t[1]))
    return {t[2] for t in dec[:n]}, dec


for N in (10, 25, 50):
    overlaps, randoms, tie_frac = [], [], []
    for _day, items in by_day.items():
        if len(items) < N * 3:  # anlamli secim icin yeterli evren
            continue
        full_set, full_dec = topn(items, 1, N)
        daily_set, _ = topn(items, 2, N)
        overlaps.append(len(full_set & daily_set))
        # rastgele kontrol: ayni buyuklukte rastgele kume
        rnd = set(RNG.sample([i[0] for i in items], N))
        randoms.append(len(full_set & rnd))
        # sinirdaki tie yogunlugu: N. sirada kac sembol ayni skorda
        boundary = full_dec[N - 1][0]
        tie_frac.append(sum(1 for i in items if i[1] == boundary) / len(items))
    if not overlaps:
        continue
    print(f"\n--- ilk-{N} ---   gun: {len(overlaps)}")
    print(
        f"  gunluk-only ortusmesi : medyan {statistics.median(overlaps):.1f}/{N}"
        f"  ({100*statistics.median(overlaps)/N:.0f}%)"
    )
    print(
        f"  RASTGELE kontrol      : medyan {statistics.median(randoms):.1f}/{N}"
        f"  ({100*statistics.median(randoms)/N:.0f}%)"
    )
    lift = (
        (statistics.median(overlaps) / statistics.median(randoms))
        if statistics.median(randoms)
        else float("inf")
    )
    print(f"  lift (gunluk/rastgele): {lift:.2f}x")
    print(
        f"  sinirdaki tie yogunlugu: medyan {100*statistics.median(tie_frac):.1f}% "
        f"(gun evreninin bu kadari N. sira ile AYNI skorda)"
    )
