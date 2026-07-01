#!/usr/bin/env python3
"""
SEC CATALYST TESTI (EDGAR, bedava) — 8-K / Form 4 edge olcumu
==============================================================
enriched_signals_v2.csv'deki her sinyal icin, sinyal gununden ONCEKI birkac gunde
SEC dosyalamasi (8-K materyal olay / Form 4 insider islem) var miydi bakar ve
catalyst VAR/YOK gruplarinin gercek >=%5 / >=%10 yakalama oranini kiyaslar.

Kaynak (anahtar GEREKMEZ, sadece User-Agent):
  https://www.sec.gov/files/company_tickers.json   (symbol -> CIK)
  https://data.sec.gov/submissions/CIK##########.json  (dosyalama gecmisi)

SEC kurali: User-Agent'ta iletisim (email) olmali; saniyede <=10 istek.

Kullanim:
  pip install requests
  python sec_catalyst_test.py --email seninmail@ornek.com
  (email vermezsen jenerik UA kullanilir; SEC yine de cevap verir.)
"""

import argparse
import csv
import datetime as dt
import json
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
CSVP = os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v2.csv")
CACHE = os.path.join(ROOT, "data", "edgar_cache")
os.makedirs(CACHE, exist_ok=True)
try:
    import requests
except ImportError:
    raise SystemExit("pip install requests")


def ff(x):
    try:
        return float(x)
    except:
        return None


def load_cik_map(ua):
    cf = os.path.join(CACHE, "tickers.json")
    if os.path.exists(cf):
        data = json.load(open(cf))
    else:
        r = requests.get(
            "https://www.sec.gov/files/company_tickers.json", headers={"User-Agent": ua}, timeout=30
        )
        r.raise_for_status()
        data = r.json()
        json.dump(data, open(cf, "w"))
    m = {}
    for _, v in data.items():
        m[v["ticker"].upper()] = str(v["cik_str"]).zfill(10)
    return m


def get_filings(cik, ua):
    cf = os.path.join(CACHE, f"sub_{cik}.json")
    if os.path.exists(cf):
        try:
            return json.load(open(cf))
        except Exception:
            pass
    r = requests.get(
        f"https://data.sec.gov/submissions/CIK{cik}.json", headers={"User-Agent": ua}, timeout=30
    )
    if r.status_code != 200:
        json.dump({}, open(cf, "w"))
        return {}
    j = r.json()
    recent = j.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    out = [(f, d) for f, d in zip(forms, dates, strict=False)]
    json.dump(out, open(cf, "w"))
    time.sleep(0.12)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default="")
    ap.add_argument("--window", type=int, default=3, help="sinyal oncesi kac gun icinde dosyalama")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    ua = f"FinPilot backtest {args.email or 'contact@example.com'}"

    rows = [r for r in csv.DictReader(open(CSVP)) if ff(r.get("resolved_pct_t5")) is not None]
    if args.limit > 0:
        rows = rows[: args.limit]
    cikmap = load_cik_map(ua)
    print(f"Sinyal: {len(rows)}  CIK eslesen sembol sayisi (evrensel): {len(cikmap)}")

    # sembol bazli dosyalama cache
    filings = {}
    syms = sorted({r["symbol"] for r in rows})
    miss = 0
    for i, s in enumerate(syms, 1):
        cik = cikmap.get(s.upper())
        if not cik:
            filings[s] = []
            miss += 1
            continue
        filings[s] = get_filings(cik, ua)
        if i % 50 == 0:
            print(f"  {i}/{len(syms)} sembol EDGAR...")
    print(f"CIK bulunamayan sembol: {miss}/{len(syms)}")

    def has(sym, sd, kinds):
        d0 = dt.date.fromisoformat(sd[:10])
        lo = (d0 - dt.timedelta(days=args.window)).isoformat()
        hi = sd[:10]
        for f, d in filings.get(sym, []):
            if lo <= d <= hi and any(f.startswith(k) for k in kinds):
                return True
        return False

    def rate(sub, thr):
        return sum(1 for r in sub if ff(r["resolved_pct_t5"]) >= thr) / len(sub) if sub else 0

    base5 = rate(rows, 5)
    base10 = rate(rows, 10)
    print(f"\nBaz oran: >=5% {base5*100:.1f}%  >=10% {base10*100:.1f}%  (n={len(rows)})")

    def report(name, kinds):
        yes = [r for r in rows if has(r["symbol"], r["signal_date"], kinds)]
        no = [r for r in rows if r not in yes]
        if len(yes) < 20:
            print(f"\n{name}: n={len(yes)} (yetersiz)")
            return
        h5 = rate(yes, 5)
        h10 = rate(yes, 10)
        print(f"\n{name}  (sinyal oncesi {args.window} gun): n={len(yes)}")
        print(f"  >=5%:  {h5*100:5.1f}%  lift {h5/base5 if base5 else 0:.2f}")
        print(f"  >=10%: {h10*100:5.1f}%  lift {h10/base10 if base10 else 0:.2f}")

    report("8-K (materyal olay)", ["8-K"])
    report("Form 4 (insider islem)", ["4"])
    report("8-K VEYA Form 4", ["8-K", "4"])
    print(
        "\n>>> lift belirgin >1 ise catalyst faktoru skora eklenmeli (score_engine catalyst zaten var)."
    )
    print("Bu ciktinin TAMAMINI Claude'a yapistir.")


if __name__ == "__main__":
    main()
