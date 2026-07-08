#!/usr/bin/env python3
"""TEST 3 — Cikis rafinesi: sabit vs ATR-trailing vs kademeli. Intraday cache (intraday_stop_test'ten)."""

import csv
import datetime as dt
import json
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
bd = os.path.join(ROOT, "data", "backtest_out")
CSVP = os.path.join(bd, "enriched_signals_v3.csv")
if not os.path.exists(CSVP):
    CSVP = os.path.join(bd, "enriched_signals_v2.csv")
CACHE = os.path.join(ROOT, "data", "intraday_cache")
try:
    import requests
except ImportError:
    requests = None


def env():
    e = {}
    for line in open(os.path.join(ROOT, ".env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return e


E = env()
KID = E.get("ALPACA_API_KEY", "")
SEC = E.get("ALPACA_SECRET_KEY", "")


def ff(x):
    try:
        return float(x)
    except Exception:
        return None


def bars_for(sym, sd):
    d0 = dt.date.fromisoformat(sd[:10])
    start = (d0 + dt.timedelta(days=1)).isoformat()
    end = (d0 + dt.timedelta(days=8)).isoformat()
    cf = os.path.join(CACHE, f"{sym}_{start}_{end}.json")
    if os.path.exists(cf):
        try:
            return json.load(open(cf))
        except Exception:
            return []
    if not requests or not KID:
        return []
    url = f"https://data.alpaca.markets/v2/stocks/{sym}/bars"
    hdr = {"APCA-API-KEY-ID": KID, "APCA-API-SECRET-KEY": SEC}
    out = []
    page = None
    while True:
        p = {
            "timeframe": "15Min",
            "start": start + "T00:00:00Z",
            "end": end + "T23:59:00Z",
            "limit": 10000,
            "adjustment": "raw",
            "feed": "iex",
        }
        if page:
            p["page_token"] = page
        try:
            r = requests.get(url, headers=hdr, params=p, timeout=30)
        except Exception:
            break
        if r.status_code != 200:
            break
        j = r.json()
        for b in j.get("bars", []) or []:
            out.append((b["t"], b["h"], b["l"], b["c"], b["o"]))
        page = j.get("next_page_token")
        if not page:
            break
    os.makedirs(CACHE, exist_ok=True)
    json.dump(out, open(cf, "w"))
    time.sleep(0.1)
    return out


def sim_fixed(entry, atr, bars, sm=1.5, tm=5.0):
    stop = entry - sm * atr
    tp = entry + tm * atr
    for _t, h, lo, _c, _o in bars:
        if lo <= stop:
            return -sm
        if h >= tp:
            return tm
    return (bars[-1][3] - entry) / atr if bars else 0


def sim_trail(entry, atr, bars, trail=1.5, init=1.5):
    stop = entry - init * atr
    peak = entry
    for _t, h, lo, _c, _o in bars:
        if lo <= stop:
            return (stop - entry) / atr
        if h > peak:
            peak = h
            stop = max(stop, peak - trail * atr)
    return (bars[-1][3] - entry) / atr if bars else 0


def sim_scale(entry, atr, bars, tp1=2.0, trail=1.5, init=1.5):
    stop = entry - init * atr
    peak = entry
    half = False
    realized = 0.0
    for _t, h, lo, _c, _o in bars:
        if not half and h >= entry + tp1 * atr:
            realized += 0.5 * tp1
            half = True
            stop = max(stop, entry)  # kalan icin stop'u girise cek
        if lo <= stop:
            return realized + (0.5 if half else 1.0) * ((stop - entry) / atr)
        if h > peak:
            peak = h
            stop = max(stop, peak - trail * atr)
    return realized + (0.5 if half else 1.0) * ((bars[-1][3] - entry) / atr if bars else 0)


rows = list(csv.DictReader(open(CSVP)))


def sh(r):
    s = r.get("short_pit")
    s = ff(s) if s not in (None, "") else ff(r.get("short_pct"))
    return s if s is not None else 0.0


sel = [
    r
    for r in rows
    if sh(r) >= 15
    and (ff(r.get("atr_pct")) or 0) >= 4
    and ff(r.get("entry"))
    and ff(r.get("atr_pct"))
]
print(f"BASE kapi sinyal: {len(sel)} (intraday cache'i olanlar islenir)")
F = []
T = []
S = []
done = 0
for r in sel:
    sym = r["symbol"]
    entry = ff(r["entry"])
    atr = (ff(r["atr_pct"]) / 100) * entry
    if atr <= 0:
        continue
    bars = bars_for(sym, r["signal_date"])
    if not bars:
        continue
    F.append(sim_fixed(entry, atr, bars))
    T.append(sim_trail(entry, atr, bars))
    S.append(sim_scale(entry, atr, bars))
    done += 1
    if done % 50 == 0:
        print(f"  {done} islendi...")
if done < 20:
    print(f"Yetersiz intraday ({done}). Once intraday_stop_test.py cache'ini olustur.")
    raise SystemExit
import statistics as st


def rep(name, xs):
    print(
        f"  {name:22s} beklenti {st.mean(xs):+.3f}R  win% {sum(1 for x in xs if x>0)/len(xs)*100:.0f}  medyan {st.median(xs):+.2f}R"
    )


print(f"\n=== CIKIS YONTEMLERI (n={done}, R cinsinden) ===")
rep("Sabit (1.5stop/5TP)", F)
rep("ATR-trailing (1.5)", T)
rep("Kademeli (yari@2R+trail)", S)
print("\n>>> En yuksek beklenti hangisiyse cikis mantigi o olmali.")
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
