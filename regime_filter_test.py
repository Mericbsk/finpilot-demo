#!/usr/bin/env python3
"""
PIYASA REJIM FILTRESI TESTI (SPY + VIX, EODHD)
==============================================
Her sinyal gununu SPY-rejimi (bull/bear: SPY>EMA200) ve VIX seviyesine gore
siniflandirir; base kapinin (short>=15 & ATR>=4) precision'ini rejime gore olcer.
Amac: risk-off gunleri atlayarak isabeti yukseltmek.

Kaynak: EODHD (paid) — SPY.US ve VIX.INDX gunluk. Anahtar .env'de.
Kullanim:  python regime_filter_test.py   -> ciktinin TAMAMINI yapistir.
"""

import csv
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
bd = os.path.join(ROOT, "data", "backtest_out")
CSVP = os.path.join(bd, "enriched_signals_v3.csv")
if not os.path.exists(CSVP):
    CSVP = os.path.join(bd, "enriched_signals_v2.csv")
try:
    import requests
except ImportError:
    raise SystemExit("pip install requests") from None


def env():
    e = {}
    for line in open(os.path.join(ROOT, ".env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return e


KEY = env().get("EODHD_API_KEY", "")


def ff(x):
    try:
        return float(x)
    except Exception:
        return None


def eod(sym):
    r = requests.get(
        f"https://eodhd.com/api/eod/{sym}",
        params={
            "api_token": KEY,
            "fmt": "json",
            "from": "2024-06-01",
            "to": "2026-12-31",
            "period": "d",
        },
        timeout=30,
    )
    print(f"  [{sym}] HTTP {r.status_code}", "" if r.status_code == 200 else r.text[:80])
    if r.status_code != 200:
        return []
    return [(b["date"], ff(b.get("close"))) for b in r.json() if b.get("close") is not None]


print("SPY + VIX cekiliyor (EODHD)...")
spy = eod("SPY.US")
vix = eod("VIX.INDX")
if not spy:
    print("!! SPY cekilemedi — anahtar/erisim. Cikiliyor.")
    raise SystemExit
spy.sort()


# EMA200
def ema(series, n):
    k = 2 / (n + 1)
    out = {}
    e = None
    for d, c in series:
        e = c if e is None else c * k + e * (1 - k)
        out[d] = e
    return out


spy_ema = ema(spy, 200)
spy_close = dict(spy)
vix_close = dict(vix)
spy_dates = [d for d, _ in spy]
vix_dates = sorted(vix_close)


def prior(dates, mp, d):
    prev = [x for x in dates if x <= d]
    return mp[prev[-1]] if prev else None


rows = [r for r in csv.DictReader(open(CSVP)) if ff(r.get("resolved_pct_t5")) is not None]


def sh(r):
    s = r.get("short_pit")
    s = ff(s) if s not in (None, "") else ff(r.get("short_pct"))
    return s if s is not None else 0.0


for r in rows:
    r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0
    r["y10"] = 1 if ff(r["resolved_pct_t5"]) >= 10 else 0
    d = r["signal_date"][:10]
    sc = prior(spy_dates, spy_close, d)
    se = prior(spy_dates, spy_ema, d)
    r["bull"] = (sc > se) if (sc and se) else None
    r["vix"] = prior(vix_dates, vix_close, d) if vix_dates else None

base = [r for r in rows if sh(r) >= 15 and ff(r.get("atr_pct") or 0) >= 4]


def P(sub, k):
    return sum(r[k] for r in sub) / len(sub) if sub else 0


print(
    f"\nBASE kapi n={len(base)} precision >=5% {P(base,'y5')*100:.1f}% >=10% {P(base,'y10')*100:.1f}%"
)
cov = sum(1 for r in base if r["bull"] is not None)
print(
    f"SPY rejim kapsami: {cov}/{len(base)}  | VIX kapsami: {sum(1 for r in base if r['vix'] is not None)}/{len(base)}"
)


def seg(name, cond):
    sub = [r for r in base if cond(r)]
    if len(sub) < 20:
        print(f"  {name:26s} n={len(sub)} (yetersiz)")
        return
    print(
        f"  {name:26s} n={len(sub):>4} >=5% {P(sub,'y5')*100:5.1f}%  >=10% {P(sub,'y10')*100:5.1f}%"
    )


print("\n=== SPY REJIMI ===")
seg("Bull (SPY>EMA200)", lambda r: r["bull"] is True)
seg("Bear (SPY<EMA200)", lambda r: r["bull"] is False)
print("=== VIX SEVIYESI ===")
seg("VIX < 18 (sakin)", lambda r: r["vix"] is not None and r["vix"] < 18)
seg("VIX 18-25 (normal)", lambda r: r["vix"] is not None and 18 <= r["vix"] < 25)
seg("VIX >= 25 (risk-off)", lambda r: r["vix"] is not None and r["vix"] >= 25)
print("=== KOMBINE FILTRE ===")
seg("Bull & VIX<25", lambda r: r["bull"] is True and (r["vix"] or 99) < 25)
seg("Bull & VIX<20", lambda r: r["bull"] is True and (r["vix"] or 99) < 20)

print(
    "\n>>> Bir rejim segmenti base'den belirgin YUKSEKSE, o rejim-disi gunleri atlamak precision'i artirir."
)
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
