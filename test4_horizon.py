#!/usr/bin/env python3
"""TEST 4 — Tutma suresi. EODHD gunluk bar; base kapi icin T+1/3/5/10 max-favorable + close precision."""

import csv
import json
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
bd = os.path.join(ROOT, "data", "backtest_out")
CSVP = os.path.join(bd, "enriched_signals_v3.csv")
if not os.path.exists(CSVP):
    CSVP = os.path.join(bd, "enriched_signals_v2.csv")
CACHE = os.path.join(ROOT, "data", "daily_cache_h")
os.makedirs(CACHE, exist_ok=True)
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


def daily(sym):
    cf = os.path.join(CACHE, f"{sym}.json")
    if os.path.exists(cf):
        try:
            return json.load(open(cf))
        except Exception:
            return []
    r = requests.get(
        f"https://eodhd.com/api/eod/{sym}.US",
        params={
            "api_token": KEY,
            "fmt": "json",
            "from": "2025-08-01",
            "to": "2026-07-01",
            "period": "d",
        },
        timeout=30,
    )
    out = (
        [(b["date"], ff(b.get("high")), ff(b.get("close"))) for b in r.json()]
        if r.status_code == 200
        else []
    )
    out.sort()
    json.dump(out, open(cf, "w"))
    time.sleep(0.1)
    return out


rows = [r for r in csv.DictReader(open(CSVP)) if ff(r.get("resolved_pct_t5")) is not None]


def sh(r):
    s = r.get("short_pit")
    s = ff(s) if s not in (None, "") else ff(r.get("short_pct"))
    return s if s is not None else 0.0


sel = [r for r in rows if sh(r) >= 15 and (ff(r.get("atr_pct")) or 0) >= 4 and ff(r.get("entry"))]
print(f"BASE kapi: {len(sel)} sinyal; EODHD gunluk cekiliyor...")
H = [1, 3, 5, 10]
maxfav = {h: [] for h in H}
closeret = {h: [] for h in H}
done = 0
for r in sel:
    bars = daily(r["symbol"])
    if not bars:
        continue
    idx = {d: i for i, (d, _, _) in enumerate(bars)}
    d0 = r["signal_date"][:10]
    di = idx.get(d0)
    if di is None:
        for i, (d, _, _) in enumerate(bars):
            if d >= d0:
                di = i
                break
    if di is None:
        continue
    e = ff(r["entry"]) or bars[di][2]
    if not e or e <= 0:
        continue
    for h in H:
        fwd = bars[di + 1 : di + 1 + h]
        if len(fwd) < 1:
            continue
        maxfav[h].append((max(b[1] for b in fwd if b[1]) - e) / e * 100)
        closeret[h].append((fwd[-1][2] - e) / e * 100)
    done += 1
    if done % 50 == 0:
        print(f"  {done}...")
if done < 20:
    print(f"Yetersiz ({done}).")
    raise SystemExit


def pct(xs, thr):
    return sum(1 for x in xs if x >= thr) / len(xs) * 100 if xs else 0


print(f"\n=== TUTMA SURESI (n~{done}) — MAX-FAVORABLE ve CLOSE precision ===")
print(f"{'ufuk':>6}{'>=5% maxfav':>13}{'>=10% maxfav':>14}{'>=5% close':>12}{'ort close%':>12}")
for h in H:
    import statistics as st

    print(
        f"T+{h:<4}{pct(maxfav[h],5):>12.1f}%{pct(maxfav[h],10):>13.1f}%{pct(closeret[h],5):>11.1f}%{(st.mean(closeret[h]) if closeret[h] else 0):>11.2f}%"
    )
print(
    "\n>>> max-favorable secicilik icin; close ise GERCEK tutma getirisi. Optimal ufuk: close-getiri tepe yaptigi yer."
)
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
