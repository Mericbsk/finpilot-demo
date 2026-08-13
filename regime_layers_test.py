#!/usr/bin/env python3
"""
regime_layers_test.py — 3-KATMANLI REJİM testi (Level A araştırma).

Kavram: mevcut tek `regime` = yalnız SEMBOL trendi. Gerçek "uyum" üç katman:
  M (market)  : SPY 50-SMA üstü mü (bull/bear) — edge_recheck.regime'den
  S (sektör)  : sembolün sektör ETF'i — S_trend (200-SMA üstü) + S_rs (SPY'ye göre 60g güç)
  Y (sembol)  : sembol kendi trendinde mi — enriched.regime (True/False)

Test ettiğimiz: hizalama honest getiri/kazanç/RİSK'i segmentliyor mu; ve
"sembol-yükseliyor ama market/sektör desteksiz" (yalancı hizalama) tam-hizalıdan kötü mü.

Veri: sector_cache.json (143 sembol, gerçek Yahoo sektörü) → 11 SPDR ETF eşlemesi.
Metrik: edge_recheck honest (c2c5_net, mae5, atr_pct), IS/OOS scan_date medyanı.
"""

from __future__ import annotations

import bisect
import csv
import json
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PD = "data/price_cache"
SEC_MAP = {  # Yahoo sektör adı → SPDR sektör ETF
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Industrials": "XLI",
    "Energy": "XLE",
    "Basic Materials": "XLB",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
    "Communication Services": "XLC",
}


def load_series(sym):
    b = sorted(json.load(open(f"{PD}/{sym}.json")), key=lambda x: x["date"])
    dates = [x["date"] for x in b]
    close = [x["close"] for x in b]
    return dates, close


def sma(close, i, n):
    return statistics.mean(close[i - n : i]) if i >= n else None


class ETF:
    def __init__(self, sym):
        self.dates, self.close = load_series(sym)

    def asof(self, d):
        # son işlem günü <= d
        i = bisect.bisect_right(self.dates, d) - 1
        return i if i >= 0 else None

    def signals(self, d):
        i = self.asof(d)
        if i is None or i < 200:
            return None
        c = self.close[i]
        s50, s200 = sma(self.close, i, 50), sma(self.close, i, 200)
        r60 = (c / self.close[i - 60] - 1) if i >= 60 else None
        return {"close": c, "s50": s50, "s200": s200, "r60": r60}


def main():
    spy = ETF("SPY")
    etfs = {e: ETF(e) for e in set(SEC_MAP.values())}
    sec = json.load(open("data/sector_cache.json"))

    # symbol regime (Y) : enriched.regime True/False, key (symbol, scan_date)
    yreg = {}
    for r in csv.DictReader(open("data/backtest_out/full_universe_enriched.csv")):
        yreg[(r["symbol"], str(r["scan_date"]))] = r.get("regime") == "True"

    rows = []
    for r in csv.DictReader(open("data/backtest_out/edge_recheck.csv")):
        s = r["symbol"]
        if s not in sec or sec[s] not in SEC_MAP:
            continue
        d = str(r["scan_date"])
        try:
            c2c = float(r["c2c5_net"])
            mae = float(r["mae5"])
            atr = float(r["atr_pct"])
        except (ValueError, KeyError):
            continue
        etf = etfs[SEC_MAP[sec[s]]]
        ssig, msig = etf.signals(d), spy.signals(d)
        if ssig is None or msig is None:
            continue
        y = yreg.get((s, d))
        if y is None:
            continue
        M = r.get("regime") == "bull"  # market: SPY 50-SMA
        S_trend = ssig["close"] >= ssig["s200"]  # sektör kendi trendinde
        S_rs = (
            ssig["r60"] is not None and msig["r60"] is not None and ssig["r60"] > msig["r60"]
        )  # sektör SPY'ye göre güçlü
        rows.append(
            {
                "date": d,
                "sym": s,
                "M": M,
                "S_trend": S_trend,
                "S_rs": S_rs,
                "Y": y,
                "align": int(M) + int(S_trend) + int(y),  # 0-3 (S=trend)
                "c2c": c2c,
                "win": c2c > 0,
                "mae": mae,
                "atr": atr,
            }
        )
    print(f"n = {len(rows)} satır (143 gerçek-sektör sembolü)")
    dates = sorted({x["date"] for x in rows})
    cut = dates[len(dates) // 2]

    def stats(sub, label):
        if not sub:
            return f"{label:38} n=0"
        w = 100 * sum(x["win"] for x in sub) / len(sub)
        ret = statistics.median(x["c2c"] for x in sub)
        mae = statistics.mean(x["mae"] for x in sub)
        return f"{label:38} n={len(sub):5d}  win%={w:5.1f}  medRet={ret:+6.2f}  MAE={mae:+6.2f}"

    print("\n=== HİZALAMA SEVİYESİ (M + S_trend + Y) → honest sonuç ===")
    for lvl in [0, 1, 2, 3]:
        print(stats([x for x in rows if x["align"] == lvl], f"hizalama {lvl}/3"))
    print(stats(rows, "TÜM (baseline)"))

    print("\n=== IS/OOS: hizalama 3/3 vs 0/3 (getiri gerçekten segmentliyor mu?) ===")
    for name, sub in [
        ("IS", [x for x in rows if x["date"] < cut]),
        ("OOS", [x for x in rows if x["date"] >= cut]),
    ]:
        print(f"-- {name} --")
        print("  " + stats([x for x in sub if x["align"] == 3], "tam-hizalı 3/3"))
        print("  " + stats([x for x in sub if x["align"] == 0], "hizasız 0/3"))

    print("\n=== H-YALANCI-HİZALAMA: sembol yükseliyor (Y_on), market/sektör ne diyor? ===")
    yon = [x for x in rows if x["Y"]]
    print(stats(yon, "TÜM Y_on (sembol bullish)"))
    print(stats([x for x in yon if x["M"] and x["S_trend"]], "  + market&sektör DESTEKLİ"))
    print(
        stats(
            [x for x in yon if not (x["M"] and x["S_trend"])],
            "  + market/sektör DESTEKSİZ (yalancı)",
        )
    )
    print(stats([x for x in yon if not x["M"]], "  + market bear (M_off)"))
    print(stats([x for x in yon if not x["S_trend"]], "  + sektör düşüş (S_trend_off)"))

    print("\n=== SEKTÖR GÖRECE GÜÇ (S_rs: sektör SPY'den güçlü) → sonuç ===")
    print(stats([x for x in rows if x["S_rs"]], "S_rs ON (güçlü sektör)"))
    print(stats([x for x in rows if not x["S_rs"]], "S_rs OFF (zayıf sektör)"))

    print("\n=== 8-KOMBO (M,S_trend,Y) — win% / medRet / MAE ===")
    for M in (True, False):
        for S in (True, False):
            for Y in (True, False):
                sub = [x for x in rows if x["M"] == M and x["S_trend"] == S and x["Y"] == Y]
                print(stats(sub, f"M={int(M)} S={int(S)} Y={int(Y)}"))

    # rank-IC: alignment → c2c (IS/OOS)
    def ic(sub):
        if len(sub) < 30:
            return None
        import statistics as st

        a = [x["align"] for x in sub]
        b = [x["c2c"] for x in sub]
        ra = _rank(a)
        rb = _rank(b)
        ma, mb = st.mean(ra), st.mean(rb)
        num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb, strict=False))
        da = sum((x - ma) ** 2 for x in ra) ** 0.5
        db = sum((y - mb) ** 2 for y in rb) ** 0.5
        return round(num / (da * db), 3) if da and db else None

    print("\n=== hizalama → c2c5_net rank-IC ===")
    print(
        f"  tüm={ic(rows)}  IS={ic([x for x in rows if x['date']<cut])}  OOS={ic([x for x in rows if x['date']>=cut])}"
    )


def _rank(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


if __name__ == "__main__":
    main()
