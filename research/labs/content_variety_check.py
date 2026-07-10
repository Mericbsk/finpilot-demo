"""Hafta-1 E8 — brif içerik çeşitliliği denetimi (kapı kanıtı).

Simüle N gün x M aday üretir; raporlar:
  * birebir tekrar eden tam gerekçe sayısı (hedef: 0, aynı gün-aynı hisse hariç)
  * ardışık günlerde aynı hisseye üretilen metnin farklılaşması
  * lint ihlalleri (hedef: 0)
  * kalıp (skeleton/opener/closer) dağılımı

Kullanım:  python research/labs/content_variety_check.py [gün=10]
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from distribution import lint
from distribution.rationale import build_rationale, extract_badges

TICKERS = ["EXAS", "RXRX", "IONQ", "SOUN", "PLUG", "QS"]
PROFILES = [
    {"squeeze_factor": 0.9, "gap_pct": 2.0, "volume_spike": True, "atr_pct": 5.0},
    {"catalyst_factor": 0.6, "rvol_acceleration": 0.5, "atr_pct": 7.0},
    {"contraction_factor": 0.8, "price_momentum": True, "atr_pct": 4.0},
    {"tier": "CONFIRM", "regime": True, "volume_spike": True, "atr_pct": 6.5},
    {"squeeze_factor": 0.7, "tier": "TRIGGER", "atr_pct": 3.0, "price": 4.2},
    {"momentum_bias": "bullish", "rvol_acceleration": 0.3, "atr_pct": 5.5},
]
GRADES = ["A", "B", "B", "C", "C", "C"]


def main(days: int = 10) -> int:
    start = date(2026, 7, 6)
    all_texts: list[tuple[str, str, str]] = []  # (date, ticker, text)
    lint_fails = 0

    for d in range(days):
        day = (start + timedelta(days=d)).isoformat()
        for ticker, profile, grade in zip(TICKERS, PROFILES, GRADES, strict=False):
            badges = extract_badges(profile)
            for lang in ("tr", "en"):
                text = build_rationale(
                    ticker,
                    grade,
                    badges,
                    lang=lang,
                    context={
                        "date": day,
                        "atr_pct": profile.get("atr_pct"),
                        "price": profile.get("price"),
                    },
                )
                if lint.check_text(text):
                    lint_fails += 1
                    print(f"  LINT FAIL [{day} {ticker} {lang}]: {text}")
                all_texts.append((day, f"{ticker}|{lang}", text))

    # 1) Determinizm: aynı gün+hisse iki kez üretilirse aynı metin mi?
    t1 = build_rationale("EXAS", "A", ["squeeze", "gap"], "tr", {"date": "2026-07-06"})
    t2 = build_rationale("EXAS", "A", ["squeeze", "gap"], "tr", {"date": "2026-07-06"})
    det_ok = t1 == t2

    # 2) Gün-değişince farklılaşma: aynı hisse ardışık günlerde kaç kez birebir aynı?
    by_key: dict[str, list[str]] = {}
    for _day, key, text in all_texts:
        by_key.setdefault(key, []).append(text)
    consecutive_repeats = sum(
        1 for texts in by_key.values() for a, b in zip(texts, texts[1:], strict=False) if a == b
    )

    # 3) Havuz kapsamı
    uniq = len({t for _, _, t in all_texts})

    print(f"\n— İÇERİK ÇEŞİTLİLİK RAPORU ({days} gün × {len(TICKERS)} aday × 2 dil) —")
    print(f"toplam metin: {len(all_texts)} | benzersiz: {uniq}")
    print(f"determinizm (aynı gün→aynı metin): {'OK' if det_ok else 'FAIL'}")
    print(f"ardışık gün birebir tekrar: {consecutive_repeats} (hedef 0)")
    print(f"lint ihlali: {lint_fails} (hedef 0)")

    ok = det_ok and consecutive_repeats == 0 and lint_fails == 0
    print("SONUÇ:", "✅ GEÇTİ" if ok else "❌ KALDI")
    return 0 if ok else 1


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    raise SystemExit(main(days))
