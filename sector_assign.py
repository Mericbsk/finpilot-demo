#!/usr/bin/env python3
"""sector_assign.py — Tam evren için korelasyon-tabanlı sektör ataması (resumable).

Her sembolün günlük getirisini 11 SPDR sektör ETF'iyle korele et; en yüksek korelasyonlu
ETF'e ata. sector_cache.json'daki 143 gerçek sektörle çapraz-doğrulanabilir.
Chunk'lı: her koşu --limit yeni sembol işler, çıktıya EKLER.

  python sector_assign.py --limit 600     # tekrar çalıştır, bitene kadar
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PD = "data/price_cache"
ETFS = ["XLK", "XLV", "XLF", "XLY", "XLP", "XLI", "XLE", "XLB", "XLRE", "XLU", "XLC"]
OUT = "data/backtest_out/sector_map_full.csv"


def rets(sym):
    p = f"{PD}/{sym}.json"
    if not os.path.exists(p):
        return None
    try:
        b = sorted(json.load(open(p)), key=lambda x: x["date"])
    except Exception:
        return None
    out = {}
    for i in range(1, len(b)):
        pc = b[i - 1]["close"]
        if pc:
            out[b[i]["date"]] = b[i]["close"] / pc - 1
    return out or None


def corr(a: dict, b: dict):
    ks = a.keys() & b.keys()
    if len(ks) < 60:
        return None
    xs = [a[k] for k in ks]
    ys = [b[k] for k in ks]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=False))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx and dy else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=600)
    lim = ap.parse_args().limit
    etf_r = {e: rets(e) for e in ETFS}
    syms = sorted({r["symbol"] for r in csv.DictReader(open("data/backtest_out/edge_recheck.csv"))})
    done = set()
    exists = os.path.exists(OUT)
    if exists:
        for r in csv.DictReader(open(OUT)):
            done.add(r["symbol"])
    todo = [s for s in syms if s not in done]
    print(f"toplam {len(syms)} | bitmiş {len(done)} | kalan {len(todo)}")
    fh = open(OUT, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(fh, fieldnames=["symbol", "etf", "corr"])
    if not exists:
        w.writeheader()
    n = 0
    for s in todo[:lim]:
        sr = rets(s)
        if not sr:
            w.writerow({"symbol": s, "etf": "", "corr": ""})
            continue
        best, bc = "", -2
        for e in ETFS:
            c = corr(sr, etf_r[e])
            if c is not None and c > bc:
                bc, best = c, e
        w.writerow({"symbol": s, "etf": best, "corr": round(bc, 3) if best else ""})
        n += 1
    fh.close()
    print(f"bu koşuda {min(lim, len(todo))} işlendi, {n} atandı → {OUT}")
    print("kalan:", len(todo) - min(lim, len(todo)), "(0 ise validate)")


if __name__ == "__main__":
    main()
