"""Factor -> sentence rationale engine v2 (template-based, no LLM).

v2 (Hafta-1 E1): variant pools + deterministic selection + context rules.
  * 9 badges x 5 variants x 2 languages — same meaning, different voice.
  * Deterministic: sha1(date|ticker) seeds every choice — the text you
    approve at 07:50 is the text published at 08:30; re-runs are identical.
  * Sentence skeletons rotate (list / emphasis / context-first).
  * Context rules: high ATR -> cautious closer; Grade C -> subdued opener.

Hard rule unchanged: sentences are assembled ONLY from fields present in the
scan result. No number is ever generated — numbers come from the data.
All output must pass distribution.lint.
"""

from __future__ import annotations

import hashlib
from typing import Any

# ── Fragment pools ───────────────────────────────────────────────────────────
# Her rozet: anlamca eş, üslupça farklı 5 varyant. Yasak-kelime disiplinine
# uygun (al/sat yok, hedef yok, kesinlik yok).

_FRAGMENTS: dict[str, dict[str, list[str]]] = {
    "squeeze": {
        "tr": [
            "short oranı yüksek (squeeze potansiyeli)",
            "açığa satış pozisyonları belirgin şekilde birikmiş",
            "short tarafı kalabalık — yukarı hareketlerde yakıt olabilir",
            "yüksek short interest profili taşıyor",
            "açıkta kalan short pozisyonlar dikkat çekici seviyede",
        ],
        "en": [
            "elevated short interest (squeeze potential)",
            "short positioning is notably crowded",
            "a heavy short base that can fuel sharp upside moves",
            "carries a high short-interest profile",
            "outstanding short positions sit at eye-catching levels",
        ],
    },
    "catalyst": {
        "tr": [
            "yakın tarihli bir katalizör/dosyalama var",
            "taze bir kurumsal gelişme (dosyalama) kayıtlarda",
            "yeni bir haber/katalizör izi taşıyor",
            "güncel bir SEC dosyalaması sinyale eşlik ediyor",
            "somut bir olay akışı (katalizör) mevcut",
        ],
        "en": [
            "a recent catalyst/filing is present",
            "a fresh corporate development sits on the record",
            "carries the trace of a new catalyst",
            "a current SEC filing accompanies the setup",
            "concrete event flow (a catalyst) is in play",
        ],
    },
    "rvol": {
        "tr": [
            "hacim ivmesi ortalamanın üzerinde",
            "işlem hacmi normalinin belirgin üstünde akıyor",
            "hacimde olağan dışı bir canlanma var",
            "göreli hacim (RVOL) yükselmiş durumda",
            "para akışı son günlere göre hızlanmış",
        ],
        "en": [
            "volume acceleration above average",
            "turnover is running clearly above its norm",
            "an unusual pickup in trading volume",
            "relative volume (RVOL) is elevated",
            "money flow has quickened versus recent days",
        ],
    },
    "gap": {
        "tr": [
            "güne belirgin bir fiyat boşluğuyla başladı",
            "açılışta dikkat çekici bir gap oluştu",
            "önceki kapanışın uzağında bir açılış yaptı",
            "fiyat, gapli bir açılışla güç gösterdi",
            "seans dışı akış açılışta boşluk bıraktı",
        ],
        "en": [
            "opened with a notable price gap",
            "a striking gap formed at the open",
            "opened well away from the prior close",
            "showed strength with a gapped open",
            "overnight flow left a gap at the open",
        ],
    },
    "momentum": {
        "tr": [
            "kısa vadeli momentum güçlü",
            "son günlerin fiyat eğilimi yukarı yönlü ve diri",
            "kısa vade ivmesi pozitif seyrediyor",
            "fiyat davranışı süregelen bir güç gösteriyor",
            "yakın dönem momentum okuması olumlu",
        ],
        "en": [
            "strong short-term momentum",
            "recent price action is lively and upward-leaning",
            "near-term impulse reads positive",
            "price behaviour shows persistent strength",
            "the short-horizon momentum read is favourable",
        ],
    },
    "volume": {
        "tr": [
            "hacim sıçraması görüldü",
            "işlem hacmi ani bir sıçrama yaptı",
            "hacim tarafında belirgin bir patlama var",
            "alışılmışın üstünde bir hacim günü yaşıyor",
            "hacim, katılımın gerçek olduğunu söylüyor",
        ],
        "en": [
            "a volume spike was observed",
            "turnover jumped abruptly",
            "a clear burst on the volume side",
            "trading an outsized-volume session",
            "volume suggests the participation is real",
        ],
    },
    "contraction": {
        "tr": [
            "sıkışma sonrası genişleme sinyali veriyor",
            "daralan fiyat aralığı yerini genişlemeye bırakıyor",
            "uzun süredir sıkışan fiyat menzili açılıyor",
            "yay gibi sıkışmış aralık gevşemeye başladı",
            "range daralması sonrası ilk genişleme işaretleri",
        ],
        "en": [
            "signals expansion after contraction",
            "a narrowing range is giving way to expansion",
            "a long-compressed price range is opening up",
            "the coiled range has started to release",
            "first signs of expansion after range compression",
        ],
    },
    "regime": {
        "tr": [
            "genel piyasa rejimi destekleyici",
            "piyasa geneli bu tür kurulumlara elverişli",
            "makro rejim arka planı olumlu",
            "geniş piyasa koşulları rüzgarı arkadan veriyor",
            "rejim okuması setup ile aynı yönde",
        ],
        "en": [
            "the broad market regime is supportive",
            "market-wide conditions favour this kind of setup",
            "the macro-regime backdrop is constructive",
            "broad conditions provide a tailwind",
            "the regime read points the same way as the setup",
        ],
    },
    "early_tier": {
        "tr": [
            "erken-yakalama merdiveninde üst basamakta",
            "kurulum, teyit merdiveninin ileri aşamasında",
            "erken sinyal zinciri üst üste doğrulanmış",
            "WATCH→CONFIRM merdiveninde yol almış durumda",
            "aşamalı teyit sisteminde üst kademeye ulaştı",
        ],
        "en": [
            "high on the early-detection ladder",
            "the setup sits at an advanced confirmation stage",
            "the early-signal chain has stacked confirmations",
            "well progressed on the WATCH→CONFIRM ladder",
            "reached the upper rungs of the staged-confirmation system",
        ],
    },
}

_DEFAULT_BODY = {
    "tr": [
        "kompozit skoru bugünkü evrende üst dilimde",
        "bugünün taramasında üst yüzdelik dilime yerleşti",
        "genel faktör bileşimi günün ortalamasının üzerinde",
    ],
    "en": [
        "composite score in the top decile of today's universe",
        "placed in the upper percentile of today's sweep",
        "overall factor mix sits above today's average",
    ],
}

_OPENERS: dict[str, dict[str, list[str]]] = {
    "A": {
        "tr": [
            "Bugünün en yüksek konviksiyonlu adayı:",
            "Günün öne çıkanı:",
            "Bu sabahki taramanın zirvesi:",
        ],
        "en": [
            "Today's highest-conviction candidate:",
            "The standout of the morning:",
            "Top of this morning's sweep:",
        ],
    },
    "B": {
        "tr": ["Güçlü aday:", "Dikkate değer bir kurulum:", "Sağlam bir çok-faktör profili:"],
        "en": ["Strong candidate:", "A setup worth attention:", "A solid multi-factor profile:"],
    },
    "C": {
        "tr": ["İzleme adayı:", "Erken aşamada bir aday:", "Radara yeni giren:"],
        "en": ["Watch candidate:", "An early-stage candidate:", "New on the radar:"],
    },
}

_CLOSERS = {
    "tr": [
        "Bu bir izleme adayıdır; karar ve risk yönetimi okuyucuya aittir.",
        "İzleme amaçlıdır — değerlendirme ve risk tamamen senin kontrolünde.",
        "Aday statüsündedir; ne yapılacağına her zaman okuyan karar verir.",
    ],
    "en": [
        "This is a watch candidate; decisions and risk management remain yours.",
        "For monitoring only — judgement and risk stay fully in your hands.",
        "Candidate status only; what to do with it is always the reader's call.",
    ],
}

_CAUTION_CLOSERS = {
    "tr": [
        "Günlük aralığı geniş — izlerken tempoyu buna göre ayarlamak gerekir; karar okuyucuya aittir.",
        "Hareketli bir profil: iki yön de hızlı işleyebilir. İzleme adayıdır; karar senin.",
        "Volatilitesi yüksek bir aday — temkinli izleme gerektirir; risk yönetimi okuyana aittir.",
    ],
    "en": [
        "Its daily range is wide — pace your monitoring accordingly; the decision is yours.",
        "A fast-moving profile: both directions can run quickly. Watch candidate; your call.",
        "A high-volatility candidate — it asks for careful monitoring; risk stays with the reader.",
    ],
}


def _seed_int(date_str: str, ticker: str, salt: str = "") -> int:
    h = hashlib.sha1(f"{date_str}|{ticker}|{salt}".encode(), usedforsecurity=False).hexdigest()
    return int(h[:8], 16)


def _pick(seq: list[str], seed: int) -> str:
    return seq[seed % len(seq)]


def extract_badges(result: dict[str, Any]) -> list[str]:
    """Derive badge ids from a scan-result row (tolerant to missing fields)."""
    badges: list[str] = []

    def num(key: str) -> float:
        try:
            return float(result.get(key) or 0.0)
        except (TypeError, ValueError):
            return 0.0

    if num("squeeze_factor") >= 0.5:
        badges.append("squeeze")
    if num("catalyst_factor") >= 0.3:
        badges.append("catalyst")
    if num("rvol_acceleration") > 0 or result.get("volume_spike"):
        badges.append("rvol")
    if num("overnight_gap_factor") >= 0.5 or num("gap_pct") >= 1.0:
        badges.append("gap")
    if result.get("price_momentum") or str(result.get("momentum_bias", "")).lower() in (
        "bullish",
        "positive",
        "up",
    ):
        badges.append("momentum")
    if num("contraction_factor") >= 0.5:
        badges.append("contraction")
    if str(result.get("tier", "")).upper() in ("TRIGGER", "CONFIRM"):
        badges.append("early_tier")
    if result.get("regime") is True:
        badges.append("regime")

    seen: set[str] = set()
    out = []
    for b in badges:
        if b not in seen:
            seen.add(b)
            out.append(b)
    return out[:4]


def _fragments_for(badges: list[str], lang: str, date_str: str, ticker: str) -> list[str]:
    frags = []
    for b in badges:
        pool = _FRAGMENTS.get(b, {}).get(lang)
        if pool:
            frags.append(_pick(pool, _seed_int(date_str, ticker, salt=b)))
    return frags


def _assemble(ticker: str, opener: str, frags: list[str], closer: str, lang: str, seed: int) -> str:
    """3 dönüşümlü cümle iskeleti — aynı bilgiler, farklı ritim."""
    skeleton = seed % 3
    if not frags:
        body = _pick(_DEFAULT_BODY[lang], seed)
        return f"{opener} {ticker} — {body}. {closer}"

    if skeleton == 0 or len(frags) == 1:
        body = "; ".join(frags)
        return f"{opener} {ticker} — {body}. {closer}"

    if skeleton == 1:
        first, rest = frags[0], frags[1:]
        if lang == "tr":
            tail = "; ayrıca " + "; ".join(rest) if rest else ""
            return f"{opener} {ticker}: en dikkat çekeni, {first}{tail}. {closer}"
        tail = "; on top of that, " + "; ".join(rest) if rest else ""
        return f"{opener} {ticker}: most notably, {first}{tail}. {closer}"

    # skeleton == 2: bağlam-önce
    last, head = frags[-1], frags[:-1]
    if lang == "tr":
        head_txt = "; ".join(head) if head else ""
        joiner = f"{head_txt} — buna eşlik eden bir unsur daha: {last}" if head else last
        return f"{opener} {ticker} — {joiner}. {closer}"
    head_txt = "; ".join(head) if head else ""
    joiner = f"{head_txt} — with one more element alongside: {last}" if head else last
    return f"{opener} {ticker} — {joiner}. {closer}"


def build_rationale(
    ticker: str,
    grade: str,
    badges: list[str],
    lang: str = "tr",
    context: dict[str, Any] | None = None,
) -> str:
    """Assemble a 1-2 sentence rationale from validated fragments only.

    context (optional): {"date": "YYYY-MM-DD", "atr_pct": float, "price": float}
      - date  -> deterministic daily seed (approve == publish guarantee)
      - atr_pct >= 6 -> cautious closer pool
    """
    ctx = context or {}
    date_str = str(ctx.get("date") or "")
    seed = _seed_int(date_str, ticker)

    lang = "tr" if lang == "tr" else "en"
    opener = _pick(_OPENERS.get(grade, _OPENERS["C"])[lang], seed)

    try:
        high_atr = float(ctx.get("atr_pct") or 0.0) >= 6.0
    except (TypeError, ValueError):
        high_atr = False
    closer_pool = _CAUTION_CLOSERS[lang] if high_atr else _CLOSERS[lang]
    closer = _pick(closer_pool, _seed_int(date_str, ticker, salt="closer"))

    frags = _fragments_for(badges, lang, date_str, ticker)
    return _assemble(ticker, opener, frags, closer, lang, seed)


def prob_band(prob: float) -> str:
    """Calibrated probability -> honest coarse band (never false precision)."""
    if prob <= 0:
        return "—"
    pct = int(round(prob * 100 / 5.0) * 5)
    pct = max(5, min(95, pct))
    return f"~{pct}%"
