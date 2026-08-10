"""Tam tarama bittikten sonra (TUM batch'ler toplandiktan sonra) TEK kez cagrilan
ozet uretici: kural-tabanli aday havuzu + LLM ile "en yuksek basari olasilikli"
<=10 hisseyi secme + her biri icin tez/etiket/risk + kullanici-dostu, tier-gruplu
Telegram digest'i (tek gonderim).

Cagiran: api/routers/scan.py::summarize_scan()  (POST /scan/summarize)

Env:
  FINPILOT_ENABLE_SCAN_LLM_SUMMARY=1 (varsayilan) -> LLM secimi/tezleri
  FINPILOT_ALERT_ON_SCAN=1 (varsayilan)           -> Telegram digest
  FINPILOT_ALERT_MAX_PER_RUN=10 (varsayilan)      -> secilecek adet
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)

_TIER_LABEL = {"A": "🅰️ ELİTE", "B": "🅱️ GÜÇLÜ", "C": "🅲 ORTA"}
_TIER_ORDER = {"A": 0, "B": 1, "C": 2, "": 3}
_EXECUTION_ORDER = {"Tier 2": 0, "Tier 1": 1, "Tier 0": 2}


def _rank(item: tuple[str, dict]) -> tuple[int, int, float, float]:
    r = item[1]
    return (
        _TIER_ORDER.get(str(r.get("conviction_tier", "") or ""), 3),
        _EXECUTION_ORDER.get(str(r.get("execution_confidence", "Tier 0")), 3),
        -float(r.get("conviction_prob", 0.0) or 0.0),
        -float(r.get("ranking_score", r.get("composite_score", 0.0)) or 0.0),
    )


def build_candidate_pool(out: dict, max_candidates: int = 25) -> list[tuple[str, dict]]:
    cand = [
        (s, r)
        for s, r in out.items()
        if isinstance(r, dict)
        and r.get(
            "selection_eligible", r.get("entry_ok") or r.get("conviction_tier") in ("A", "B", "C")
        )
        and not r.get("position_cap_reject_reason")
    ]
    cand.sort(key=_rank)
    return cand[:max_candidates]


def _brief(symbol: str, r: dict) -> dict:
    return {
        "symbol": symbol,
        "tier": r.get("conviction_tier", ""),
        "conviction_prob": round(float(r.get("conviction_prob", 0.0) or 0.0), 3),
        "score": r.get("composite_score"),
        "price": r.get("price"),
        "stop": r.get("stop_loss"),
        "tp": r.get("take_profit"),
        "risk_reward": r.get("risk_reward"),
        "momentum_3d_pct": r.get("momentum_3d_pct"),
        "fundamental_score": r.get("fundamental_score"),
        "news_catalyst_score": r.get("news_catalyst_score"),
        "news_sentiment": r.get("news_sentiment"),
        "squeeze_factor": r.get("squeeze_factor"),
        "regime": r.get("regime"),
    }


def _parse_json(content: str) -> dict | None:
    m = re.search(r"\{.*\}", content.strip(), re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _fallback(cands: list[tuple[str, dict]], n: int) -> dict:
    top = []
    for sym, r in cands[:n]:
        prob = float(r.get("conviction_prob", 0.0) or 0.0)
        top.append(
            {
                "symbol": sym,
                "confidence": round(prob * 100) if prob else 50,
                "thesis": "Yuksek konviksiyon (volatilite + short/gap) — kural-tabanli secim.",
                "tag": "Momentum",
                "risk": "LLM devre disi; tez otomatik.",
            }
        )
    return {"top": top, "overall_note": "", "market_mood": "Notr", "llm_used": False}


def llm_select_top(cands: list[tuple[str, dict]], n: int = 10) -> dict:
    if not cands:
        return {
            "top": [],
            "overall_note": "Bugun kaliteli AL sinyali cikmadi.",
            "market_mood": "Notr",
            "llm_used": False,
        }
    if os.environ.get("FINPILOT_ENABLE_SCAN_LLM_SUMMARY", "1") != "1":
        return _fallback(cands, n)

    briefs = [_brief(s, r) for s, r in cands]
    try:
        from llm import get_router  # noqa: PLC0415
        from llm.base import LLMMessage, LLMRole  # noqa: PLC0415

        lines = [
            f"{b['symbol']}: tier={b['tier'] or '-'} guven≈%{int(b['conviction_prob'] * 100)} "
            f"skor={b['score']} fiyat={b['price']} R/R={b['risk_reward']} "
            f"3g_momentum={b['momentum_3d_pct']}% squeeze={b['squeeze_factor']} "
            f"haber_katalizor={b['news_catalyst_score']} sentiment={b['news_sentiment']} "
            f"fund={b['fundamental_score']} rejim={'Boga' if b['regime'] else 'Diger'}"
            for b in briefs
        ]
        prompt = (
            f"Asagida bugunku taramadan {len(briefs)} aday AL sinyali var. Gorevin: basari "
            f"olasiligi (dogru yakalama) en yuksek en fazla {n} taneyi SEC, zayiflari ELE, "
            "ve HER biri icin kisa Turkce tez yaz.\n\n"
            + "\n".join(lines)
            + "\n\nSADECE gecerli JSON dondur (baska metin yok):\n"
            '{"market_mood": "Riskli|Notr|Istahli", '
            '"overall_note": "2-3 cumle Turkce genel degerlendirme: gunun temasi, piyasa havasi, kac kaliteli firsat", '
            '"top": [{"symbol":"XXX","confidence":0-100,'
            '"thesis":"tek cumle Turkce tez (neden one cikiyor)",'
            '"tag":"Katalist|Squeeze|Momentum|Teknik|Fundamental",'
            '"risk":"kisa Turkce risk/dikkat notu"}]}\n'
            "Kurallar: confidence=senin verdigin basari olasiligi (0-100). thesis kisa ve somut. "
            "Kesin al-sat tavsiyesi verme, olasilik dili kullan (‘guclu aday’, ‘~%70 ihtimal’)."
        )
        resp = get_router().generate_messages(
            messages=[
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content="Sen FinPilot'un kidemli sinyal analistisisin. Kisa, net, Turkce, SADECE JSON.",
                ),
                LLMMessage(role=LLMRole.USER, content=prompt),
            ],
            temperature=0.3,
            max_tokens=1100,
        )
        parsed = _parse_json(getattr(resp, "content", "") or "")
        if parsed and parsed.get("top"):
            valid = {b["symbol"] for b in briefs}
            top = [t for t in parsed["top"] if isinstance(t, dict) and t.get("symbol") in valid][:n]
            if top:
                return {
                    "top": top,
                    "overall_note": parsed.get("overall_note", ""),
                    "market_mood": parsed.get("market_mood", "Notr"),
                    "llm_used": True,
                }
        logger.warning("scan_summary: LLM JSON gecersiz, fallback")
    except Exception as exc:  # noqa: BLE001
        logger.warning("scan_summary: LLM secimi basarisiz: %s", exc)
    return _fallback(cands, n)


def _enrich_top(top: list[dict], out: dict) -> list[dict]:
    """LLM seciminine tarama verisini (fiyat/stop/tp/rr/tier) ekle."""
    enriched = []
    for t in top:
        sym = t.get("symbol")
        r = out.get(sym, {}) if isinstance(out, dict) else {}
        tier = r.get("conviction_tier", "")
        enriched.append(
            {
                "symbol": sym,
                "tier": tier,
                "tier_label": _TIER_LABEL.get(tier, ""),
                "confidence": t.get("confidence"),
                "thesis": t.get("thesis") or t.get("reason") or "",
                "reason": t.get("thesis") or t.get("reason") or "",  # geriye uyum
                "tag": t.get("tag") or "",
                "risk": t.get("risk") or "",
                "price": r.get("price"),
                "stop": r.get("stop_loss"),
                "tp": r.get("take_profit"),
                "rr": r.get("risk_reward"),
            }
        )
    enriched.sort(key=lambda x: (_TIER_ORDER.get(x["tier"], 3), -(x.get("confidence") or 0)))
    return enriched


def format_telegram_digest(summary: dict, top: list[dict]) -> str:
    """Kullanici-dostu, tier-gruplu, mobil-taranabilir Türkçe digest."""
    ts = datetime.now().strftime("%d %b %Y, %H:%M")
    total = summary.get("total_scanned", 0)
    mood = summary.get("market_mood", "")
    mood_emoji = {"Riskli": "🔴", "Notr": "🟡", "Nötr": "🟡", "Istahli": "🟢", "İştahlı": "🟢"}.get(
        mood, ""
    )
    head = [
        "🤖 *FinPilot — Günlük Tarama*",
        f"📅 {ts}  ·  🔍 {total:,} tarandı → *{len(top)} fırsat*",
    ]
    if mood:
        head.append(f"{mood_emoji} Piyasa havası: *{mood}*")
    note = summary.get("overall_note", "")
    if note:
        head.append(f"\n📊 {note}")
    if not top:
        head.append("\n💤 Bugün öne çıkan kaliteli fırsat yok.")
        return "\n".join(head)

    lines = list(head)
    cur = None
    for t in top:
        if t["tier"] != cur:
            cur = t["tier"]
            lines.append(f"\n{t['tier_label'] or '📌 DİĞER'}")
            lines.append("━━━━━━━━━━━━")
        conf = t.get("confidence")
        conf_txt = f"~%{int(conf)} güven" if conf is not None else ""
        tag = f" · {t['tag']}" if t.get("tag") else ""
        lines.append(f"🔹 *{t['symbol']}*  {conf_txt}{tag}")
        if t.get("thesis"):
            lines.append(f"   💡 {t['thesis']}")
        px, stop, tp, rr = t.get("price"), t.get("stop"), t.get("tp"), t.get("rr")
        if px is not None:
            lvl = f"   🎯 Giriş {px} · Stop {stop} · Hedef {tp}"
            if rr:
                lvl += f" · R/R {rr}"
            lines.append(lvl)
        if t.get("risk"):
            lines.append(f"   ⚠️ {t['risk']}")

    lines.append("\n_Bunlar olasılık tahminidir; yatırım tavsiyesi değildir._")
    return "\n".join(lines)


def send_final_alert(summary: dict, top: list[dict], out: dict) -> bool:
    # The distribution queue is the only publication path that carries the
    # snapshot identity and human approval. Keep the legacy direct alert off
    # unless it is explicitly enabled for diagnostics.
    if os.environ.get("FINPILOT_ENABLE_SCAN_SUMMARY_ALERT", "0") != "1":
        return False
    if os.environ.get("FINPILOT_ALERT_ON_SCAN", "1") != "1":
        return False
    try:
        from telegram_alerts import TelegramNotifier  # noqa: PLC0415

        msg = format_telegram_digest(summary, top)
        if len(msg) > 3900:
            msg = msg[:3800] + "\n…"
        return bool(TelegramNotifier()._send_message(msg))
    except Exception as exc:  # noqa: BLE001
        logger.warning("scan_summary: telegram gonderimi basarisiz: %s", exc)
        return False


def summarize_full_scan(out: dict, max_candidates: int = 25, top_n: int = 10) -> dict:
    """Tum batch'ler bittikten sonra frontend'in TEK kez cagirdigi ozet."""
    try:
        top_n = int(os.environ.get("FINPILOT_ALERT_MAX_PER_RUN", str(top_n)))
    except ValueError:
        pass

    cands = build_candidate_pool(out, max_candidates)
    n_entry = sum(1 for r in out.values() if isinstance(r, dict) and r.get("entry_ok"))
    n_rejected = sum(
        1
        for r in out.values()
        if isinstance(r, dict) and not r.get("selection_eligible", r.get("entry_ok", False))
    )
    n_cap_rejected = sum(
        1 for r in out.values() if isinstance(r, dict) and r.get("position_cap_reject_reason")
    )
    nA = sum(1 for _, r in cands if r.get("conviction_tier") == "A")
    nB = sum(1 for _, r in cands if r.get("conviction_tier") == "B")
    nC = sum(1 for _, r in cands if r.get("conviction_tier") == "C")

    sel = llm_select_top(cands, top_n)
    top = _enrich_top(sel["top"], out)

    summary = {
        "total_scanned": len(out),
        "buy_signals": n_entry,
        "rejected": n_rejected,
        "position_cap_rejected": n_cap_rejected,
        "candidates_considered": len(cands),
        "tier_A": nA,
        "tier_B": nB,
        "tier_C": nC,
        "market_mood": sel.get("market_mood", "Notr"),
        "overall_note": sel.get("overall_note", ""),
        "top": top,
        "llm_used": sel["llm_used"],
    }
    summary["alert_sent"] = send_final_alert(summary, top, out)
    return summary
