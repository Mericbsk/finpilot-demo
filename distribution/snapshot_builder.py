"""Build the daily distribution snapshot from scan results.

Input:  the enriched scan-result rows (written by api/routers/scan.py hook to
        data/distribution/scan_export_latest.json) — NOT data/daily_reports
        (legacy BUY/stop/TP language, no tier/conviction fields).
Output: versioned snapshot dict (schema.py) — the single artefact consumed by
        web demo + free brief + premium brief.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from distribution.rationale import build_rationale, extract_badges, prob_band
from distribution.scan_contract import full_scan_problems
from distribution.schema import SCHEMA_VERSION, validate_snapshot

UTC = UTC
logger = logging.getLogger(__name__)

EXPORT_DIR = Path(os.getenv("FINPILOT_DIST_DIR", "data/distribution"))
SCAN_EXPORT_LATEST = EXPORT_DIR / "scan_export_latest.json"

_GRADE_ORDER = {"A": 0, "B": 1, "C": 2}
_EXECUTION_ORDER = {"Tier 2": 0, "Tier 1": 1, "Tier 0": 2}
FREE_CANDIDATES = 2  # first N candidates are visible in the free tier
MAX_CANDIDATES = 50


def config_sha() -> str:
    """Stamp of active feature flags (+ git sha when available)."""
    flags = sorted(f"{k}={v}" for k, v in os.environ.items() if k.startswith("FINPILOT_ENABLE"))
    base = ";".join(flags)
    try:
        git = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        ).stdout.strip()
    except Exception:
        git = ""
    return hashlib.sha256(f"{git}|{base}".encode()).hexdigest()[:12] + (f"@{git}" if git else "")


def _grade_of(row: dict[str, Any]) -> str | None:
    """Map a scan row to a public Grade — the SINGLE user-facing label."""
    conv = str(row.get("conviction_tier") or "").strip().upper()
    if conv in ("A", "B", "C"):
        return conv
    tier = str(row.get("tier") or "").strip().upper()
    if tier == "CONFIRM":
        return "B"
    if tier == "TRIGGER":
        return "C"
    return None


def _sort_key(row: dict[str, Any]) -> tuple:
    grade = _grade_of(row) or "Z"
    execution = str(row.get("execution_confidence") or "Tier 0")
    try:
        prob = float(row.get("conviction_prob") or 0.0)
    except (TypeError, ValueError):
        prob = 0.0
    try:
        score = float(
            row.get("ranking_score")
            or row.get("legacy_quality_score")
            or row.get("composite_score")
            or row.get("score")
            or 0.0
        )
    except (TypeError, ValueError):
        score = 0.0
    return (_GRADE_ORDER.get(grade, 9), _EXECUTION_ORDER.get(execution, 3), -prob, -score)


def _is_true(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"true", "1", "yes"}


def _public_candidate(row: dict[str, Any]) -> bool:
    """Keep only eligible, executable, non-cap-rejected graded rows public."""
    if not _grade_of(row):
        return False
    if "selection_eligible" in row and not _is_true(row.get("selection_eligible")):
        return False
    if "execution_feasible" in row and not _is_true(row.get("execution_feasible")):
        return False
    return not row.get("position_cap_reject_reason")


# ── E3: Risk notu havuzu — koşul-öncelikli, deterministik, brif içi tekrarsız ──
_RISK_POOLS: dict[str, dict[str, list[str]]] = {
    "squeeze_lowprice": {
        "tr": [
            "yüksek short + düşük fiyat bileşimi: hareketler sert, spread geniş olabilir",
            "squeeze profili düşük fiyatlı bir hissede — oynaklık ve kayma riski birlikte gelir",
        ],
        "en": [
            "high short interest on a low-priced stock: moves can be violent, spreads wide",
            "a squeeze profile in a low-priced name — volatility and slippage arrive together",
        ],
    },
    "squeeze_highatr": {
        "tr": [
            "squeeze + yüksek volatilite: iki yön de aynı hızla işleyebilir",
            "geniş günlük aralıkla birleşen squeeze profili — tempo çok yüksek olabilir",
        ],
        "en": [
            "squeeze plus high volatility: both directions can run equally fast",
            "a squeeze profile paired with a wide daily range — the pace can be extreme",
        ],
    },
    "squeeze": {
        "tr": [
            "squeeze senaryoları iki yönlü sert hareket üretebilir",
            "short kapanışları kadar short baskısı da mümkün — iki yöne de hazırlıklı izle",
        ],
        "en": [
            "squeeze scenarios can produce sharp moves in either direction",
            "short-covering and renewed shorting are both possible — watch both ways",
        ],
    },
    "high_atr": {
        "tr": [
            "volatilite çok yüksek (geniş günlük aralık)",
            "günlük aralığı geniş — sakin bir hisse değil",
            "yüksek ATR profili: fiyat gün içinde büyük yol katedebilir",
        ],
        "en": [
            "very high volatility (wide daily range)",
            "a wide daily range — not a quiet name",
            "a high-ATR profile: price can travel far within a session",
        ],
    },
    "low_price": {
        "tr": [
            "düşük fiyatlı hisse — likidite/spread riski",
            "düşük fiyat kademesi: emir derinliği ince olabilir",
        ],
        "en": [
            "low-priced stock — liquidity/spread risk",
            "a low price tier: order-book depth can be thin",
        ],
    },
    "gap_risk": {
        "tr": [
            "gapli açılışlar kısmen geri dolabilir — ilk saatler yanıltıcı olabilir",
            "açılış boşluğu her zaman kalıcı değildir; gün içi geri çekilme olağandır",
        ],
        "en": [
            "gapped opens can partially fill — the first hours may mislead",
            "opening gaps are not always durable; intraday give-backs are common",
        ],
    },
    "catalyst_risk": {
        "tr": [
            "haber/katalizör kaynaklı hareketlerde belirsizlik yüksektir — akış değişebilir",
            "katalizör fiyatlanmış olabilir; teyit gelmezse ilgi hızla söner",
        ],
        "en": [
            "news/catalyst-driven moves carry high uncertainty — the flow can turn",
            "the catalyst may already be priced in; without follow-through, interest fades fast",
        ],
    },
    "contraction_risk": {
        "tr": [
            "sıkışma sonrası genişleme iki yöne de açılabilir — yön teyidi önemli",
        ],
        "en": [
            "post-contraction expansion can break either way — direction needs confirming",
        ],
    },
    "c_grade": {
        "tr": [
            "erken aşama profili: sinyal henüz olgunlaşmamış olabilir",
            "izleme-aşaması adayı — teyit basamakları henüz tamamlanmadı",
        ],
        "en": [
            "an early-stage profile: the signal may not be mature yet",
            "a watch-stage candidate — confirmation rungs are not complete",
        ],
    },
    "generic": {
        "tr": [
            "standart izleme riski; pozisyon disiplini okuyucuya aittir",
            "olağan piyasa riski geçerli — izleme temposunu kendi planına göre kur",
            "belirgin ek risk işareti yok; yine de karar ve risk okuyana aittir",
        ],
        "en": [
            "standard monitoring risk; position discipline rests with the reader",
            "usual market risk applies — set your monitoring pace to your own plan",
            "no salient extra risk flag; judgement and risk still rest with the reader",
        ],
    },
}


def _risk_conditions(row: dict[str, Any], grade: str) -> list[str]:
    """Uygulanabilir risk havuzları, öncelik sırasıyla (ilk eşleşen kullanılır)."""

    def num(key: str) -> float:
        try:
            return float(row.get(key) or 0.0)
        except (TypeError, ValueError):
            return 0.0

    squeeze = num("squeeze_factor") >= 0.5
    high_atr = num("atr_pct") >= 6
    low_price = 0 < num("price") < 5
    conds: list[str] = []
    if squeeze and low_price:
        conds.append("squeeze_lowprice")
    if squeeze and high_atr:
        conds.append("squeeze_highatr")
    if squeeze:
        conds.append("squeeze")
    if high_atr:
        conds.append("high_atr")
    if low_price:
        conds.append("low_price")
    if num("overnight_gap_factor") >= 0.5 or num("gap_pct") >= 1.0:
        conds.append("gap_risk")
    if num("catalyst_factor") >= 0.3:
        conds.append("catalyst_risk")
    if num("contraction_factor") >= 0.5:
        conds.append("contraction_risk")
    if grade == "C":
        conds.append("c_grade")
    conds.append("generic")
    return conds


def _risk_note(
    row: dict[str, Any],
    grade: str = "C",
    lang: str = "tr",
    date_str: str = "",
    used: set[str] | None = None,
) -> str:
    """Koşula uyan ilk havuzdan deterministik varyant; brif içinde tekrarı önler."""
    import hashlib as _h

    used = used if used is not None else set()
    ticker = str(row.get("symbol") or row.get("ticker") or "")
    seed = int(
        _h.sha1(f"{date_str}|{ticker}|risk".encode(), usedforsecurity=False).hexdigest()[:8], 16
    )
    lang = lang if lang in ("tr", "en", "de") else "en"

    for cond in _risk_conditions(row, grade):
        pool = _RISK_POOLS[cond][lang]
        for offset in range(len(pool)):
            candidate = pool[(seed + offset) % len(pool)]
            if candidate not in used:
                used.add(candidate)
                return candidate
    # tüm havuzlar tükendiyse (çok büyük brif) tekrar serbest
    return _RISK_POOLS["generic"][lang][seed % 3]


def build_snapshot(
    scan_rows: list[dict[str, Any]],
    universe: int,
    karne: dict[str, Any] | None = None,
    date_str: str | None = None,
    lang: str = "tr",
    scan_id: str | None = None,
) -> dict[str, Any]:
    date_str = date_str or datetime.now(tz=UTC).strftime("%Y-%m-%d")

    graded = [r for r in scan_rows if _public_candidate(r)]
    graded.sort(key=_sort_key)
    graded = graded[:MAX_CANDIDATES]
    candidate_tickers = sorted(
        str(r.get("symbol") or r.get("ticker") or "").upper()
        for r in graded
        if r.get("symbol") or r.get("ticker")
    )
    candidate_hash = hashlib.sha256("|".join(candidate_tickers).encode()).hexdigest()
    snapshot_id = hashlib.sha256(
        f"{date_str}|{int(universe)}|{candidate_hash}".encode()
    ).hexdigest()[:24]

    candidates: list[dict[str, Any]] = []
    grade_totals: dict[str, int] = {}
    for r in scan_rows:
        g = _grade_of(r)
        if g:
            grade_totals[g] = grade_totals.get(g, 0) + 1

    _used_risk_notes: set[str] = set()
    _used_risk_i18n: dict[str, set[str]] = {"tr": set(), "en": set(), "de": set()}
    for i, row in enumerate(graded):
        ticker = str(row.get("symbol") or row.get("ticker") or "").upper()
        if not ticker:
            continue
        grade = _grade_of(row) or "C"
        badges = extract_badges(row)
        cand: dict[str, Any] = {
            "ticker": ticker,
            "company": str(row.get("company") or row.get("name") or ""),
            "grade": grade,
            "prob_band": prob_band(float(row.get("conviction_prob") or 0.0)),
            "badges": badges,
            "rationale": build_rationale(
                ticker,
                grade,
                badges,
                lang=lang,
                context={
                    "date": date_str,
                    "atr_pct": row.get("atr_pct"),
                    "price": row.get("price"),
                },
            ),
            "premium_only": i >= FREE_CANDIDATES,
            "risk_note": _risk_note(
                row, grade=grade, lang=lang, date_str=date_str, used=_used_risk_notes
            ),
            "factor_detail": {
                k: row.get(k)
                for k in (
                    "conviction_prob",
                    "tier",
                    "tier_score",
                    "squeeze_factor",
                    "catalyst_factor",
                    "rvol_acceleration",
                    "contraction_factor",
                    "atr_pct",
                    "price",
                )
                if row.get(k) is not None
            },
        }
        _ctx = {"date": date_str, "atr_pct": row.get("atr_pct"), "price": row.get("price")}
        cand["rationale_i18n"] = {
            _L: build_rationale(ticker, grade, badges, lang=_L, context=_ctx)
            for _L in ("tr", "en", "de")
        }
        cand["risk_note_i18n"] = {
            _L: _risk_note(row, grade=grade, lang=_L, date_str=date_str, used=_used_risk_i18n[_L])
            for _L in ("tr", "en", "de")
        }
        candidates.append(cand)

    if karne is None:
        karne_out: dict[str, Any] | None = None
    else:
        karne_out = dict(karne)
        karne_out.setdefault("toplam_aday_bugun", grade_totals)
    if karne_out is None and grade_totals:
        karne_out = {"toplam_aday_bugun": grade_totals, "by_grade": {}, "window": ""}

    snap: dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "candidate_hash": candidate_hash,
        "scan_id": scan_id,
        "date": date_str,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "config_sha": config_sha(),
        "universe": int(universe),
        "scan_result_count": len(scan_rows),
        "eligible_candidate_count": len(graded),
        "candidates": candidates,
        "karne": karne_out,
        "warnings": [],
    }

    # v2 additive fields for the web Ledger landing (S1/S3) — best-effort,
    # never block the snapshot if one of these fails (they're editorial
    # flourish, not core data).
    try:
        from distribution.concepts import concept_of_the_day_struct

        snap["concept"] = concept_of_the_day_struct(lang="en" if lang == "en" else "tr")
    except Exception as exc:
        logger.debug("concept_of_the_day_struct unavailable: %s", exc)
    try:
        from distribution.market_context import build_context_line

        line = build_context_line(lang="en" if lang == "en" else "tr")
        if line:
            snap["context_line"] = line
    except Exception as exc:
        logger.debug("build_context_line unavailable: %s", exc)
    try:
        from distribution.broadcast import count_sent_editions

        snap["edition_no"] = count_sent_editions()
    except Exception as exc:
        logger.debug("count_sent_editions unavailable: %s", exc)

    if not candidates:
        snap["warnings"].append("no graded candidates today")
    if karne is None:
        snap["warnings"].append("karne unavailable — using daily totals only")

    problems = validate_snapshot(snap)
    if problems:
        raise ValueError("snapshot invalid: " + "; ".join(problems))
    return snap


def _read_json_resilient(p: Path) -> dict[str, Any]:
    """Bozuk-kuyruklu JSON'a dayanıklı okuyucu.

    Senkron/AV (OneDrive vb.) bazen dosya kuyruğunu null-dolgu ('\\x00') ya da
    'Extra data' ile bozar; bu okuyucu ilk geçerli JSON nesnesini kurtarır ki
    tüm brif/web hattı tek bozuk export yüzünden durmasın.
    """
    raw = Path(p).read_bytes().rstrip(b"\x00")
    text = raw.decode("utf-8", errors="ignore").lstrip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        obj, _end = json.JSONDecoder().raw_decode(text)
        logger.warning("scan export kuyruğu bozuktu; ilk geçerli JSON kurtarıldı: %s", p)
        return obj


def load_scan_export_record(path: Path | None = None) -> dict[str, Any]:
    """Read the complete export record, including scan completion metadata."""
    p = path or SCAN_EXPORT_LATEST
    data = _read_json_resilient(Path(p))
    if not isinstance(data, dict):
        raise ValueError("scan export must be a JSON object")
    return data


def load_scan_export(path: Path | None = None) -> tuple[list[dict[str, Any]], int, str]:
    """Read the scan export written by the /scan endpoint hook.

    Returns (rows, universe, date_str). Raises FileNotFoundError when missing.
    """
    data = load_scan_export_record(path)
    rows = data.get("results", [])
    universe = int(data.get("universe") or len(rows))
    date_str = str(data.get("date") or datetime.now(tz=UTC).strftime("%Y-%m-%d"))
    return rows, universe, date_str


def validate_scan_export(data: dict[str, Any]) -> list[str]:
    """Return reasons why an export cannot become a distribution snapshot."""
    rows = data.get("results", [])
    return full_scan_problems(rows, data.get("universe"), data.get("scan_complete"))


def save_snapshot(snap: dict[str, Any], out_dir: Path | None = None) -> Path:
    out = out_dir or EXPORT_DIR
    out.mkdir(parents=True, exist_ok=True)
    dated = out / f"snapshot_{snap['date']}.json"
    _atomic_write_json(dated, snap)
    _atomic_write_json(out / "snapshot_latest.json", snap)
    return dated


def write_snapshot(path: Path, snap: dict[str, Any]) -> None:
    """Validate and atomically write a snapshot projection."""
    problems = validate_snapshot(snap)
    if problems:
        raise ValueError("snapshot invalid: " + "; ".join(problems))
    _atomic_write_json(path, snap)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


# ── Almanca (de) risk havuzları — import anında birleştirilir ────────────────
_DE_RISK = {
    "squeeze_lowprice": [
        "hoher Short-Anteil bei niedrigem Kurs: Bewegungen können heftig, Spreads weit sein",
        "ein Squeeze-Profil in einem niedrigpreisigen Wert — Volatilität und Slippage kommen zusammen",
    ],
    "squeeze_highatr": [
        "Squeeze plus hohe Volatilität: beide Richtungen können gleich schnell laufen",
        "ein Squeeze-Profil mit weiter Tagesspanne — das Tempo kann extrem sein",
    ],
    "squeeze": [
        "Squeeze-Szenarien können scharfe Bewegungen in beide Richtungen erzeugen",
        "Short-Eindeckung und erneute Leerverkäufe sind beide möglich — beobachte beide Richtungen",
    ],
    "high_atr": [
        "sehr hohe Volatilität (weite Tagesspanne)",
        "eine weite Tagesspanne — kein ruhiger Wert",
        "ein High-ATR-Profil: der Kurs kann innerhalb einer Sitzung weit laufen",
    ],
    "low_price": [
        "niedrigpreisige Aktie — Liquiditäts-/Spread-Risiko",
        "eine niedrige Kursstufe: die Orderbuchtiefe kann dünn sein",
    ],
    "gap_risk": [
        "Gap-Eröffnungen können sich teilweise schließen — die ersten Stunden können täuschen",
        "Eröffnungslücken sind nicht immer beständig; Rücksetzer im Tagesverlauf sind normal",
    ],
    "catalyst_risk": [
        "nachrichten-/katalysatorgetriebene Bewegungen tragen hohe Unsicherheit — der Fluss kann drehen",
        "der Katalysator könnte bereits eingepreist sein; ohne Anschluss verblasst das Interesse schnell",
    ],
    "contraction_risk": [
        "eine Ausdehnung nach der Verengung kann in beide Richtungen ausbrechen — die Richtung braucht Bestätigung",
    ],
    "c_grade": [
        "ein Profil im Frühstadium: das Signal ist womöglich noch nicht ausgereift",
        "ein Kandidat in der Beobachtungsphase — die Bestätigungsstufen sind noch nicht abgeschlossen",
    ],
    "generic": [
        "Standard-Beobachtungsrisiko; Positionsdisziplin liegt beim Leser",
        "übliches Marktrisiko gilt — richte dein Beobachtungstempo nach deinem eigenen Plan",
        "kein auffälliges Zusatzrisiko; Urteil und Risiko liegen dennoch beim Leser",
    ],
}
for _c, _lst in _DE_RISK.items():
    _RISK_POOLS.setdefault(_c, {})["de"] = _lst
