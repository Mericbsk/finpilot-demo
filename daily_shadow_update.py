#!/usr/bin/env python3
"""
daily_shadow_update.py — Her tarama sonrası tek komut:
  1) price_cache'i tazele (refresh_price_cache.py; ağ yoksa atlanır)
  2) gölge skor kartını üret (shadow_scorecard: çoklu benchmark SPY/IWM/QQQ)
  3) ÇOK-PENCERE geçmişine bir satır ekle (data/shadow/scorecard_history.jsonl)
  4) (ops) Telegram admin'e tek satır özet ping

Amaç: pencereleri kendiliğinden biriktirmek. Her gün bir satır → birkaç hafta
sonra çok-pencere/çok-rejim edge kanıtı. Skor kartı overwrite edilir ama geçmiş
JSONL append-only birikir.

Local çalışır (sandbox'ta ağ yok → refresh atlanır, skorlama yine çalışır).
Kullanım:
  python daily_shadow_update.py
  python daily_shadow_update.py --no-refresh --control 800
Scan sonrası otomatik tetik: distribution.jobs.maybe_run_shadow_scorecard_after_scan
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from datetime import UTC, datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HISTORY = "data/shadow/scorecard_history.jsonl"
HORIZONS = [1, 3, 5, 10, 20]
BENCHMARKS = ["SPY", "IWM", "QQQ"]


def _refresh_cache(timeout: int = 900) -> str:
    """Best-effort: refresh_price_cache.py'yi çalıştır. Ağ/anahtar yoksa sorun değil."""
    if not os.path.exists("refresh_price_cache.py"):
        return "refresh script yok — atlandı"
    try:
        r = subprocess.run(
            [sys.executable, "refresh_price_cache.py"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
        return f"refresh çalıştı: {tail[0]}"
    except subprocess.TimeoutExpired:
        return "refresh timeout (kısmi olabilir)"
    except Exception as exc:  # pragma: no cover
        return f"refresh atlandı ({type(exc).__name__})"


def _score(control_n: int):
    """shadow_scorecard fonksiyonlarını içeri alıp skorla; agg + kapsam döndür."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("ss", "shadow_scorecard.py")
    ss = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ss)

    all_rows = ss.load_ledger(ss.LEDGER, include_control=True)
    elig, ctrl, seen = [], [], set()
    for r in all_rows:
        s = r.get("symbol")
        d = (r.get("timestamp") or "")[:10]
        if not s or not d:
            continue
        if r.get("selection_eligible") or r.get("entry_ok"):
            if (s, d) not in seen:
                seen.add((s, d))
                elig.append(r)
        else:
            ctrl.append(r)
    if control_n and len(ctrl) > control_n:
        ctrl = random.Random(3).sample(ctrl, control_n)

    scored = []
    for r in elig + ctrl:
        res = ss.score_signal(r, horizons=HORIZONS, benchmark_symbols=BENCHMARKS)
        if res and res.get("_status") == "scored":
            scored.append(res)

    meta = {
        "scored": sum(1 for s in scored if not s.get("is_control")),
        "pending": 0,
        "no_cache": 0,
        "no_atr": 0,
        "control": bool(control_n),
        "benchmarks": BENCHMARKS,
        "benchmark_horizon": 5,
    }
    if not scored:
        return ss, None, meta, elig
    agg = ss.summarize(scored)
    agg["horizons"] = ss.summarize_horizons(scored, HORIZONS)
    agg["benchmarks"] = ss.summarize_benchmarks(scored, BENCHMARKS)
    ss.write_md(agg, meta, horizons=HORIZONS)
    return ss, agg, meta, elig


def _append_history(agg, elig) -> dict:
    """Çok-pencere geçmişine bir satır ekle (append-only)."""
    dates = sorted({(r.get("timestamp") or "")[:10] for r in elig if r.get("timestamp")})
    b = agg.get("benchmarks", {})
    sel = b.get("selected", {})
    ctl = b.get("control", {})
    row = {
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "signals_from": dates[0] if dates else None,
        "signals_to": dates[-1] if dates else None,
        "selected_n": sel.get("n"),
        "control_n": ctl.get("n"),
        "sel_raw_median_5": sel.get("raw_median"),
        "ctl_raw_median_5": ctl.get("raw_median"),
        "sel_iwm_excess_5": (sel.get("IWM") or {}).get("median"),
        "ctl_iwm_excess_5": (ctl.get("IWM") or {}).get("median"),
        "sel_spy_excess_5": (sel.get("SPY") or {}).get("median"),
        "sel_qqq_excess_5": (sel.get("QQQ") or {}).get("median"),
    }
    os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
    with open(HISTORY, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _notify(row: dict) -> None:
    """Best-effort Telegram admin özeti (yapılandırma yoksa sessiz)."""
    try:
        from distribution.telegram_client import notify_admin

        notify_admin(
            "📊 Gölge skor kartı güncellendi\n"
            f"Sinyal penceresi: {row['signals_from']} → {row['signals_to']}\n"
            f"Seçilen n={row['selected_n']} | ham medyan 5g {row['sel_raw_median_5']}\n"
            f"IWM excess: seçilen {row['sel_iwm_excess_5']} vs kontrol {row['ctl_iwm_excess_5']}"
        )
    except Exception:  # pragma: no cover - bildirim işi bozmaz
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-refresh", action="store_true", help="price_cache tazelemeyi atla")
    ap.add_argument("--control", type=int, default=800, help="Kontrol grubu örneklem (0=kapalı)")
    ap.add_argument("--no-notify", action="store_true", help="Telegram ping atma")
    args = ap.parse_args()

    print("1) Cache tazeleme:", "(atlandı)" if args.no_refresh else _refresh_cache())
    ss, agg, meta, elig = _score(args.control)
    if agg is None:
        print("2) Skorlama: henüz olgun sinyal yok (price_cache güncel mi?).")
        return
    print(f"2) Skorlandı: seçilen n={meta['scored']}")
    row = _append_history(agg, elig)
    print("3) Geçmişe eklendi:", HISTORY)
    print(
        f"   pencere {row['signals_from']}→{row['signals_to']} | "
        f"seçilen ham medyan {row['sel_raw_median_5']} | "
        f"IWM excess: seçilen {row['sel_iwm_excess_5']} vs kontrol {row['ctl_iwm_excess_5']}"
    )
    if not args.no_notify:
        _notify(row)
        print("4) Telegram ping denendi (yapılandırma varsa gitti).")


if __name__ == "__main__":
    main()
