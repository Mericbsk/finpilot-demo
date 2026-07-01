#!/usr/bin/env python3
"""EODHD teshis: EOD + FUNDAMENTALS (float/short) calisiyor mu?  -> ciktiyi Claude'a yapistir."""

import json
import os

try:
    import requests
except ImportError:
    raise SystemExit("pip install requests")

ROOT = os.path.dirname(os.path.abspath(__file__))


def load_env():
    env = {}
    for line in open(os.path.join(ROOT, ".env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


key = load_env().get("EODHD_API_KEY", "")
print("EODHD_API_KEY .env'de:", ("VAR (len=%d, son4=%s)" % (len(key), key[-4:])) if key else "YOK")

# bozuk (bos) fiyat cache temizle
cache = os.path.join(ROOT, "data", "price_cache")
bad = 0
if os.path.isdir(cache):
    for fn in os.listdir(cache):
        fp = os.path.join(cache, fn)
        try:
            if os.path.getsize(fp) < 5 or json.load(open(fp)) == []:
                os.remove(fp)
                bad += 1
        except Exception:
            try:
                os.remove(fp)
                bad += 1
            except Exception:
                pass
print("Temizlenen bos fiyat cache:", bad)

# 1) EOD testi
r = requests.get(
    "https://eodhd.com/api/eod/AAPL.US",
    params={
        "api_token": key,
        "fmt": "json",
        "from": "2024-01-01",
        "to": "2026-12-31",
        "period": "d",
    },
    timeout=30,
)
print("\n[1] EOD AAPL -> HTTP", r.status_code, "| yanit:", r.text[:120].replace("\n", " "))
try:
    js = r.json()
    if isinstance(js, list) and js:
        print("    bar sayisi:", len(js), " en yeni tarih:", js[-1]["date"])
except Exception:
    pass

# 2) FUNDAMENTALS testi (float/short) - kucuk-float ornek: GME
for sym in ["AAPL", "GME"]:
    fr = requests.get(
        f"https://eodhd.com/api/fundamentals/{sym}.US", params={"api_token": key}, timeout=30
    )
    print(
        f"\n[2] FUNDAMENTALS {sym} -> HTTP",
        fr.status_code,
        "| yanit:",
        fr.text[:100].replace("\n", " "),
    )
    if fr.status_code == 200:
        try:
            ss = (fr.json() or {}).get("SharesStats", {}) or {}
            print(
                "    SharesFloat:",
                ss.get("SharesFloat"),
                " ShortPercentFloat:",
                ss.get("ShortPercentFloat"),
                " ShortPercentOutstanding:",
                ss.get("ShortPercentOutstanding"),
            )
        except Exception as e:
            print("    parse hatasi:", e)

print("\n>>> Ikisi de HTTP 200 ve fundamentals'ta SharesFloat/ShortPercent DOLU ise: hazir.")
print(
    ">>> EOD 200 ama fundamentals 401/403 ise: planinda 'Fundamentals Data' eklentisi yok demektir."
)
