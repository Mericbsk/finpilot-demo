#!/usr/bin/env python3
"""
SQUEEZE SETUP TESTI — float + short interest cek, mevcut fiyat ozellikleriyle birlestir, analiz et.
====================================================================================================
Zaten cekilmis olan data/backtest_out/enriched_signals.csv'yi (RVOL/ATR/gap dolu) KULLANIR;
fiyat verisini YENIDEN cekmez. Sadece eksik float + short_pct'yi ekler.

Kaynak secenekleri:
  --source yfinance   (VARSAYILAN, anahtar GEREKMEZ; EODHD 401 sorununu atlar)  ->  pip install yfinance
  --source eodhd      (CALISAN EODHD anahtari gerekir; .env: EODHD_API_KEY)      ->  pip install requests

Uyari: float/short GUNCEL degerdir (sinyal gunundeki tarihsel degil). Float/short aylik yavas
degistigi icin ilk-yaklasim olarak kabul edilebilir; raporda 'yaklasik' diye isaretlenir.

Kullanim:
  pip install yfinance
  python fetch_squeeze_and_analyze.py                 # yfinance
  python fetch_squeeze_and_analyze.py --source eodhd  # EODHD
"""

import argparse
import csv
import json
import math
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
ENR = os.path.join(ROOT, "data", "backtest_out", "enriched_signals.csv")
FCACHE = os.path.join(ROOT, "data", "fundamentals_cache.json")
OUT = os.path.join(ROOT, "data", "backtest_out")
MINN = 30


def load_env():
    env = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = load_env()


def ff(x):
    try:
        return float(x)
    except:
        return None


# ---------------- fundamentals kaynaklari ----------------
def fund_yfinance(sym):
    import yfinance as yf

    try:
        info = yf.Ticker(sym).info or {}
    except Exception:
        return dict(float_shares=None, short_pct=None)
    fl = info.get("floatShares") or info.get("sharesOutstanding")
    sp = info.get("shortPercentOfFloat")
    if sp is not None:
        sp = sp * 100 if sp < 1.5 else sp  # 0.15 -> 15%
    return dict(float_shares=fl, short_pct=sp)


def fund_eodhd(sym):
    import requests

    key = ENV.get("EODHD_API_KEY", "")
    if not key:
        raise SystemExit("EODHD_API_KEY yok.")
    try:
        r = requests.get(
            f"https://eodhd.com/api/fundamentals/{sym}.US", params={"api_token": key}, timeout=30
        )
        if r.status_code != 200:
            if sym == "AAPL":
                print(f"  [EODHD uyari] HTTP {r.status_code}: {r.text[:80]}")
            return dict(float_shares=None, short_pct=None)
        j = r.json()
        ss = j.get("SharesStats", {}) or {}
        sp = ss.get("ShortPercentFloat") or ss.get("ShortPercent")
        if sp is not None:
            sp = ff(sp)
            sp = sp * 100 if (sp is not None and sp < 1.5) else sp
        return dict(float_shares=ff(ss.get("SharesFloat")), short_pct=sp)
    except Exception:
        return dict(float_shares=None, short_pct=None)


def get_fundamentals(syms, source):
    cache = {}
    if os.path.exists(FCACHE):
        try:
            cache = json.load(open(FCACHE))
        except Exception:
            cache = {}
    fn = fund_yfinance if source == "yfinance" else fund_eodhd
    for i, s in enumerate(syms, 1):
        if s in cache:
            continue
        cache[s] = fn(s)
        time.sleep(0.15)
        if i % 25 == 0:
            print(f"  {i}/{len(syms)} sembol fundamentals...")
            json.dump(cache, open(FCACHE, "w"))
    json.dump(cache, open(FCACHE, "w"))
    return cache


# ---------------- istatistik ----------------
def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def ztest(sa, na, sb, nb):
    if na == 0 or nb == 0:
        return None
    pp = (sa + sb) / (na + nb)
    se = (pp * (1 - pp) * (1 / na + 1 / nb)) ** 0.5
    return 1.0 if se == 0 else 2 * (1 - ncdf(abs((sa / na - sb / nb) / se)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["yfinance", "eodhd"], default="yfinance")
    args = ap.parse_args()

    if not os.path.exists(ENR):
        raise SystemExit(f"Once fetch_and_retest.py ile {ENR} olusturulmali.")
    rows = list(csv.DictReader(open(ENR)))
    print(f"enriched satir: {len(rows)}")
    syms = sorted({r["symbol"] for r in rows})
    print(f"{len(syms)} sembol icin float+short cekiliyor (kaynak={args.source})...")
    fund = get_fundamentals(syms, args.source)

    # birlestir
    for r in rows:
        fd = fund.get(r["symbol"], {})
        r["float_shares"] = fd.get("float_shares")
        r["short_pct"] = fd.get("short_pct")

    # kaydet v2
    keys = [
        "src",
        "id",
        "symbol",
        "signal_date",
        "entry",
        "score",
        "rr",
        "regime",
        "resolved_pct_t5",
        "resolved_pct_1d",
        "gap_pct",
        "rvol",
        "atr_pct",
        "dist_52w_high",
        "float_shares",
        "short_pct",
    ]
    with open(os.path.join(OUT, "enriched_signals_v2.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in keys})

    # ---- analiz ----
    def yv(r):
        v = ff(r.get("resolved_pct_t5"))
        return None if v is None else (1 if v >= 5 else 0)

    def y10(r):
        v = ff(r.get("resolved_pct_t5"))
        return None if v is None else (1 if v >= 10 else 0)

    valid = [r for r in rows if yv(r) is not None]
    N = len(valid)
    base5 = sum(yv(r) for r in valid) / N
    base10 = sum(y10(r) for r in valid) / N

    covF = sum(1 for r in valid if ff(r.get("float_shares")) is not None)
    covS = sum(1 for r in valid if ff(r.get("short_pct")) is not None)
    print(f"\n=== KAPSAM ===  float: {covF}/{N}   short_pct: {covS}/{N}")
    if covF < MINN and covS < MINN:
        print("!! Fundamentals cekilemedi (kaynak/anahtar sorunu). Yukaridaki uyariya bak.")
        return
    # dagilim ipucu
    fls = [ff(r.get("float_shares")) for r in valid if ff(r.get("float_shares"))]
    sps = [ff(r.get("short_pct")) for r in valid if ff(r.get("short_pct")) is not None]
    if fls:
        fls_s = sorted(fls)
        import statistics as st

        print(
            f"float(median): {st.median(fls_s)/1e6:.1f}M  | <10M: {sum(1 for x in fls if x<10e6)}  <20M: {sum(1 for x in fls if x<20e6)}"
        )
    if sps:
        print(
            f"short%(median): {sorted(sps)[len(sps)//2]:.1f}  | >=10%: {sum(1 for x in sps if x>=10)}  >=15%: {sum(1 for x in sps if x>=15)}  >=20%: {sum(1 for x in sps if x>=20)}"
        )

    def metric(name, fn, recs=None, ykey=yv, base=None):
        recs = recs or valid
        base = base5 if base is None else base
        sub = [r for r in recs if fn(r)]
        if len(sub) < MINN:
            return None
        h = sum(ykey(r) for r in sub) / len(sub)
        ctrl = [r for r in recs if not fn(r)]
        p = (
            ztest(sum(ykey(r) for r in sub), len(sub), sum(ykey(r) for r in ctrl), len(ctrl))
            if ctrl
            else None
        )
        return dict(name=name, n=len(sub), hit=h, lift=h / base if base else None, p=p)

    def show(title, items, base):
        print(f"\n=== {title} (baz %{base*100:.1f}) ===")
        print(f"{'sinyal':34s}{'n':>6}{'hit%':>7}{'lift':>6}{'p':>9}")
        for m in items:
            if m:
                print(
                    f"{m['name']:34s}{m['n']:>6}{m['hit']*100:>7.1f}{(m['lift'] or 0):>6.2f}{(m['p'] if m['p'] is not None else 0):>9.4f}"
                )

    F = {
        "float<10M": lambda r: (ff(r.get("float_shares")) or 9e18) < 10e6,
        "float<20M": lambda r: (ff(r.get("float_shares")) or 9e18) < 20e6,
        "float<50M": lambda r: (ff(r.get("float_shares")) or 9e18) < 50e6,
        "short>=10%": lambda r: (ff(r.get("short_pct")) or -1) >= 10,
        "short>=15%": lambda r: (ff(r.get("short_pct")) or -1) >= 15,
        "short>=20%": lambda r: (ff(r.get("short_pct")) or -1) >= 20,
        "RVOL>=3": lambda r: (ff(r.get("rvol")) or 0) >= 3,
        "ATR%>=4": lambda r: (ff(r.get("atr_pct")) or 0) >= 4,
    }
    # tekli
    show("SQUEEZE TEK-SINYAL (>=5%)", [metric(k, F[k]) for k in F], base5)
    # >=10% hedefi (squeeze buyuk hareket icin)
    show("SQUEEZE TEK-SINYAL (>=10%)", [metric(k, F[k], ykey=y10, base=base10) for k in F], base10)

    # squeeze kombinasyonlari (master prompt Setup 2)
    print("\n=== SQUEEZE KOMBINASYONLARI ===")

    def comb(name, fn, ykey=yv, base=None):
        m = metric(name, fn, ykey=ykey, base=base)
        if m:
            print(
                f"  {name:40s} n={m['n']:>4} hit%={m['hit']*100:>5.1f} lift={m['lift']:.2f} p={(m['p'] or 0):.4f}"
            )
        else:
            print(f"  {name:40s} yetersiz n (<{MINN})")

    for tgt, yk, bs in [("5%", yv, base5), ("10%", y10, base10)]:
        print(f" hedef >= {tgt}:")
        comb("float<20M + short>=15%", lambda r: F["float<20M"](r) and F["short>=15%"](r), yk, bs)
        comb(
            "float<20M + short>=15% + RVOL>=3",
            lambda r: F["float<20M"](r) and F["short>=15%"](r) and F["RVOL>=3"](r),
            yk,
            bs,
        )
        comb(
            "float<20M + short>=15% + ATR%>=4",
            lambda r: F["float<20M"](r) and F["short>=15%"](r) and F["ATR%>=4"](r),
            yk,
            bs,
        )
        comb("short>=20% + ATR%>=4", lambda r: F["short>=20%"](r) and F["ATR%>=4"](r), yk, bs)

    # walk-forward (en iyi squeeze kurali)
    IS = [r for r in valid if (r.get("signal_date") or "") < "2026-01-01"]
    OOS = [r for r in valid if (r.get("signal_date") or "") >= "2026-01-01"]
    bIS = sum(yv(r) for r in IS) / len(IS) if IS else float("nan")
    bOOS = sum(yv(r) for r in OOS) / len(OOS) if OOS else float("nan")
    print(f"\n=== WALK-FORWARD squeeze (IS baz%{bIS*100:.1f} | OOS baz%{bOOS*100:.1f}) ===")
    for name, fn in [
        ("float<20M + short>=15%", lambda r: F["float<20M"](r) and F["short>=15%"](r)),
        ("short>=20% + ATR%>=4", lambda r: F["short>=20%"](r) and F["ATR%>=4"](r)),
    ]:
        mi = metric(name, fn, IS, yv, bIS)
        mo = metric(name, fn, OOS, yv, bOOS)
        if mi and mo:
            ok = mo["lift"] and mo["lift"] > 1.3 and mo["p"] is not None and mo["p"] < 0.05
            print(
                f"  {name:34s} IS lift={mi['lift']:.2f}  OOS lift={mo['lift']:.2f} p={(mo['p'] or 0):.4f}  {'DAYANDI' if ok else 'zayif'}"
            )
        else:
            print(f"  {name:34s} yetersiz n")
    print(f"\nYazildi: {OUT}/enriched_signals_v2.csv  (float+short eklendi)")
    print("Bu ciktinin TAMAMINI Claude'a yapistir.")


if __name__ == "__main__":
    main()
