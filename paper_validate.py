#!/usr/bin/env python3
"""
ALPHA_V2 Paper-Trading Karnesi
==============================
Canli sistem (ALPHA_V2 acik) sinyal urettikce, son donemde COZULMUS sinyallerin
gercek >=%5 / >=%10 yakalama oranini ve baz orana gore lift'ini raporlar.

Kaynak: data/finpilot.db -> signals_archive (score + resolved_pct_t5).
Sistemin kendi cozumleyicisi resolved_pct_t5'i doldurdukca karne otomatik guncellenir.

Kullanim:  python paper_validate.py [--days 21]
"""

import argparse
import datetime as dt
import os
import sqlite3

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "data", "finpilot.db")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=21)
    a = ap.parse_args()
    cut = (dt.datetime.utcnow() - dt.timedelta(days=a.days)).strftime("%Y-%m-%d")
    c = sqlite3.connect(DB)
    rows = c.execute(
        "select ts,score,resolved_pct_t5 from signals_archive "
        "where resolved_pct_t5 is not null and substr(ts,1,10)>=?",
        (cut,),
    ).fetchall()
    if not rows:
        print(
            f"Son {a.days} gunde cozulmus sinyal yok (cut={cut}). Sistem henuz yeni sinyal cozmemis olabilir."
        )
        return
    n = len(rows)

    def rate(sub, thr):
        return sum(1 for _, _, p in sub if p >= thr) / len(sub) if sub else 0

    base5 = rate(rows, 5)
    base10 = rate(rows, 10)
    # sistemin 'sectikleri' = ust ceyrek score
    scs = sorted(r[1] or 0 for r in rows)
    q75 = scs[int(len(scs) * 0.75)]
    picks = [r for r in rows if (r[1] or 0) >= q75]
    p5 = rate(picks, 5)
    p10 = rate(picks, 10)
    print(f"=== ALPHA_V2 PAPER KARNESI (son {a.days} gun, n={n}) ===")
    print(f"Baz oran:            >=5%: {base5*100:4.1f}%   >=10%: {base10*100:4.1f}%")
    print(f"Sistem picks (ust %25 score, n={len(picks)}):")
    print(f"  >=5%:  {p5*100:4.1f}%  (lift {p5/base5 if base5 else 0:.2f})")
    print(f"  >=10%: {p10*100:4.1f}%  (lift {p10/base10 if base10 else 0:.2f})")
    verdict = (
        "IYI (lift>1.3)"
        if (base5 and p5 / base5 > 1.3)
        else ("NOTR" if base5 and p5 / base5 > 1.05 else "ZAYIF - gozden gecir")
    )
    print(f"Karar: {verdict}")
    print("Hedef: picks lift >1.3 ve zamanla stabil. <1.05 ise receteyi/flag'i tekrar degerlendir.")


if __name__ == "__main__":
    main()
