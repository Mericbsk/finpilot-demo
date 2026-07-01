#!/usr/bin/env python3
"""
TARIHSEL SHORT-INTEREST TESHIS
==============================
Amac: sinyal GUNUNDEKI gercek (nokta-zamanli) short interest'i kullanabilir miyiz?
Simdiye kadar 'guncel' short kullandik (bugunku deger). Titiz test icin tarihsel lazim.

Bu script hangi kaynagin ISE YARADIGINI TEST eder (varsaymaz), sonuclari yazdirir:
  1) EODHD fundamentals SharesStats (guncel) — calisiyor mu?
  2) EODHD olasi tarihsel short uc noktalari — 200 mu 404 mu?
  3) Yol haritasi: yoksa FINRA bi-weekly short interest (bedava, tarihsel).

Kullanim:  pip install requests ; python historical_short_check.py
Ciktiyi Claude'a yapistir.
"""

import os

ROOT = os.path.dirname(os.path.abspath(__file__))
try:
    import requests
except ImportError:
    raise SystemExit("pip install requests")


def env():
    e = {}
    for line in open(os.path.join(ROOT, ".env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return e


key = env().get("EODHD_API_KEY", "")
print("EODHD anahtari:", "VAR" if key else "YOK")
SYM = "GME"


def probe(label, url, params):
    try:
        r = requests.get(url, params=params, timeout=25)
        body = r.text[:120].replace("\n", " ")
        print(f"  [{label}] HTTP {r.status_code} | {body}")
        return r
    except Exception as ex:
        print(f"  [{label}] HATA {ex!r}")
        return None


print("\n=== 1) EODHD fundamentals SharesStats (guncel short) ===")
r = probe(
    "fundamentals",
    f"https://eodhd.com/api/fundamentals/{SYM}.US",
    {"api_token": key, "filter": "SharesStats"},
)
if r is not None and r.status_code == 200:
    try:
        ss = r.json()
        print(
            "    SharesFloat:",
            ss.get("SharesFloat"),
            " ShortPercentFloat:",
            ss.get("ShortPercentFloat"),
            " ShortInterest tarihi/alanlari:",
            {k: ss.get(k) for k in ss if "hort" in k.lower() or "Date" in k},
        )
    except Exception as e:
        print("    parse:", e)

print("\n=== 2) EODHD olasi TARIHSEL short uc noktalari (deneme) ===")
probe(
    "short-interest v1",
    f"https://eodhd.com/api/short-interest/{SYM}.US",
    {"api_token": key, "fmt": "json"},
)
probe(
    "technical/short",
    f"https://eodhd.com/api/technical/{SYM}.US",
    {"api_token": key, "function": "short_interest", "fmt": "json"},
)
probe(
    "fundamentals full (Outstanding tarihsel?)",
    f"https://eodhd.com/api/fundamentals/{SYM}.US",
    {"api_token": key, "filter": "outstandingShares::quarterly"},
)

print("\n=== 3) FINRA bi-weekly short interest (bedava, tarihsel alternatif) ===")
# FINRA consolidated short interest — ornek dosya listesi (indirilebilir .txt)
probe(
    "FINRA short-interest API",
    "https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest",
    {"limit": 1},
)

print("\n>>> KARAR:")
print("  - EODHD SharesStats DOLU ama tek nokta (guncel) ise: tarihsel yok, mevcut yaklasim kalir.")
print("  - short-interest ucu 200 + tarih serisi donuyorsa: nokta-zamanli teste gecebiliriz.")
print(
    "  - Hicbiri yoksa: FINRA bi-weekly dosyalari (settlement tarihli) ile yaklasik tarihsel kurulur (daha fazla emek)."
)
print(
    "Bu ciktinin TAMAMINI Claude'a yapistir; ben sonuca gore nokta-zamanli test scriptini yazarim."
)
