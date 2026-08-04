"""Factor -> sentence rationale engine v3 (template-based, no LLM).

v3 (Ledger landing feedback, 2026-07-13): full-clause fragments + causal
assembly. v2's noun-phrase fragments produced choppy, hard-to-read text
("en dikkat çekeni, kurulum, teyit merdiveninin ileri aşamasında").
v3 rules:
  * Every fragment is a complete, plain-language clause that explains
    WHAT was observed and WHY it matters — readable by a non-expert.
  * Assembly is causal: opener sentence -> reason sentences joined with
    connectors -> honest closer. No semicolon chains.
  * `build_rationale_parts` additionally returns a `body` variant without
    the ticker/opener, for surfaces that already print the ticker (web).
  * Deterministic: sha1(date|ticker|salt) seeds every choice — the text
    approved at 07:50 is the text published at 08:30.
  * Context rules kept: high ATR -> cautious closer.

Hard rule unchanged: sentences are assembled ONLY from fields present in
the scan result. No number is ever generated — numbers come from the data.
All output must pass distribution.lint.
"""

from __future__ import annotations

import hashlib
from typing import Any

# ── Fragment pools ───────────────────────────────────────────────────────────
# Her rozet: anlamca eş, üslupça farklı 5 TAM CÜMLE varyantı. Sade dil,
# neden-sonuç açıklamalı. Yasak-kelime disiplinine uygun (al/sat emri yok,
# hedef fiyat yok, kesinlik yok).

_FRAGMENTS: dict[str, dict[str, list[str]]] = {
    "squeeze": {
        "tr": [
            "hisseye karşı açığa satış pozisyonları alışılmadık ölçüde birikmiş — fiyat yukarı dönerse bu pozisyonların kapanması hareketi hızlandırabilir",
            "açığa satış tarafı kalabalık; olası bir yükselişte bu taraf pozisyon kapatmak zorunda kalabilir, bu da hareketi büyütebilir",
            "piyasada bu hisseye karşı yüklü bir kısa pozisyon birikimi var — ani yukarı hareketlerde ek yakıt anlamına gelebilir",
            "açığa satış oranı yüksek seyrediyor; bu tür tablolarda yukarı hareketler kimi zaman kendi kendini besler",
            "kısa pozisyonlar dikkat çekici seviyede birikmiş durumda — olası bir toparlanmada bu baskı tersine dönebilir",
        ],
        "en": [
            "short positions against the stock have built up to an unusual degree — if price turns higher, their covering can accelerate the move",
            "the short side is crowded; in a rally those positions may be forced to cover, which can amplify the move",
            "there is a heavy build-up of bets against this stock — in sharp upside moves that can act as extra fuel",
            "short interest is running high; in setups like this, upward moves sometimes feed on themselves",
            "short positions sit at eye-catching levels — a recovery could turn that pressure the other way",
        ],
    },
    "catalyst": {
        "tr": [
            "yakın tarihte somut bir şirket gelişmesi (haber ya da resmi dosyalama) var; hareketin arkasında tanımlanabilir bir neden bulunuyor",
            "tabloya taze bir kurumsal gelişme eşlik ediyor — sinyal boşlukta değil, gerçek bir olaya yaslanıyor",
            "kısa süre önce resmi bir dosyalama ya da haber akışı gerçekleşti; artan ilginin somut bir dayanağı var",
            "günün sinyaline güncel bir katalizör eşlik ediyor: piyasa yeni bir bilgiyi fiyatlamaya çalışıyor",
            "arka planda yeni bir şirket gelişmesi var — bu, hareketin rastgele olmadığına dair bir ipucu",
        ],
        "en": [
            "there is a concrete recent company development (news or an official filing); the move has an identifiable cause behind it",
            "a fresh corporate development accompanies the picture — the signal isn't floating in a vacuum, it rests on a real event",
            "an official filing or news item landed recently; the pickup in interest has something tangible behind it",
            "a current catalyst accompanies today's signal: the market is working to price in new information",
            "a new development sits in the background — a hint that the move is not random",
        ],
    },
    "rvol": {
        "tr": [
            "işlem hacmi normalinin belirgin üzerinde akıyor — ilgiyi tek tük emirler değil, geniş bir katılım oluşturuyor",
            "hacim, hissenin kendi ortalamasına göre yükselmiş durumda; fiyat hareketinin arkasında gerçek işlem akışı var",
            "para akışı son günlere göre hızlanmış — bu, sinyalin yalnızca fiyat oynaması olmadığını gösteriyor",
            "göreli hacim yüksek — hissenin sıradan bir gününe göre çok daha fazla el değiştirme var",
            "işlem aktivitesi ortalamanın üstünde seyrediyor; artan ilgi çoğu zaman fiyattan önce hacimde görünür",
        ],
        "en": [
            "trading volume is running clearly above its norm — the interest comes from broad participation, not a few stray orders",
            "volume is elevated versus the stock's own average; there is real order flow behind the price move",
            "money flow has quickened compared with recent days — a sign the signal is more than a price wiggle",
            "relative volume is high — far more shares are changing hands than on an ordinary day for this stock",
            "trading activity sits above average; growing interest usually shows up in volume before it shows up in price",
        ],
    },
    "gap": {
        "tr": [
            "güne önceki kapanışın belirgin üzerinde başladı — gece boyunca biriken talebin işareti",
            "açılışta bir fiyat boşluğu (gap) oluştu — piyasa, önceki kapanış seviyesini beklemeden yukarıda işlem görmeye başladı",
            "seans dışı gelişmeler fiyatı açılışta yukarı taşıdı; bu tür açılışlar artan ilginin göstergesi olabilir",
            "önceki kapanıştan kopuk, yukarıda bir açılış yaptı — talebin gece boyunca biriktiğini düşündürüyor",
            "açılış fiyatı önceki günden belirgin şekilde ayrıştı; gün içi davranış bu yüzden yakından izlenmeye değer",
        ],
        "en": [
            "it opened well above the prior close — a sign of demand that built up overnight",
            "a price gap formed at the open — the market started trading higher without waiting around the previous closing level",
            "overnight developments carried the price up at the open; openings like this can indicate growing interest",
            "it opened detached from and above the prior close — suggesting demand accumulated through the night",
            "the opening price broke clearly away from the previous day; intraday behaviour is worth watching closely because of it",
        ],
    },
    "momentum": {
        "tr": [
            "fiyat son günlerde istikrarlı biçimde yukarı eğilimli — kısa vadeli ivme sinyalin lehine",
            "yakın dönem fiyat davranışı güçlü: geri çekilmeler sığ kalıyor, yükselişler korunuyor",
            "kısa vadeli momentum pozitif; hareket tek günlük bir sıçrama değil, süregelen bir eğilim",
            "son seansların yönü yukarı — fiyat, satış baskısından çok talebin kontrolünde görünüyor",
            "fiyat eğilimi kısa vadede diri; ivmenin korunup korunmadığı önümüzdeki günlerde netleşecek",
        ],
        "en": [
            "price has been trending steadily higher in recent days — short-term momentum works in the signal's favour",
            "recent price behaviour is strong: pullbacks stay shallow and gains are being held",
            "short-term momentum is positive; the move is an ongoing trend, not a one-day spike",
            "recent sessions point upward — price looks driven by demand rather than selling pressure",
            "the short-term price trend is lively; whether the momentum holds will become clear over the coming days",
        ],
    },
    "volume": {
        "tr": [
            "hacimde ani bir sıçrama yaşandı — katılımın gerçek olduğunun en somut işareti",
            "işlem hacmi bir anda olağanın çok üzerine çıktı; bu tür günler çoğu zaman yeni bir ilginin başlangıcıdır",
            "belirgin bir hacim patlaması var — fiyat hareketi geniş bir işlem aktivitesiyle destekleniyor",
            "bugün alışılmışın üstünde bir hacim günü yaşanıyor — piyasa bu hisseye normalden fazla dikkat ayırıyor",
            "hacim tarafında net bir canlanma var; fiyat tek başına değil, katılımla birlikte hareket ediyor",
        ],
        "en": [
            "volume spiked suddenly — the most concrete sign that the participation is real",
            "turnover jumped far above the usual level; days like this often mark the start of fresh interest",
            "there is a clear burst of volume — the price move is backed by broad trading activity",
            "it is trading an outsized-volume session today — the market is paying this stock more attention than usual",
            "the volume side shows a clear pickup; price is moving together with participation, not on its own",
        ],
    },
    "contraction": {
        "tr": [
            "fiyat uzun süredir dar bir bantta sıkışmıştı ve bu bant şimdi açılmaya başlıyor — sıkışma ne kadar uzunsa çözülme o kadar belirgin olabilir",
            "daralan fiyat aralığı yerini genişlemeye bırakıyor: yay bir süredir geriliyordu, ilk gevşeme işaretleri görüldü",
            "hisse haftalardır dar bir aralıkta el değiştiriyordu; aralığın açılması çoğu zaman yeni bir hareketin habercisidir",
            "sıkışmış fiyat menzili çözülme sinyali veriyor — bir süredir biriken enerji açığa çıkmaya başlamış olabilir",
            "uzun bir durgunluk döneminin ardından fiyat aralığı genişliyor; bu geçiş anları izlemeye değer",
        ],
        "en": [
            "price had been stuck in a narrow band for a long time and that band is now starting to open — the longer the squeeze, the more pronounced the release can be",
            "a narrowing range is giving way to expansion: the spring had been coiling for a while, and the first signs of release have appeared",
            "the stock had traded in a tight range for weeks; a range opening up is often the herald of a new move",
            "the compressed price range is signalling release — energy that built up over time may be starting to come out",
            "after a long quiet stretch the price range is widening; these transition moments are worth watching",
        ],
    },
    "regime": {
        "tr": [
            "genel piyasa ortamı bu tür kurulumları destekliyor — hisse rüzgara karşı değil, rüzgarla birlikte hareket ediyor",
            "geniş piyasa koşulları olumlu: benzer profildeki hisseler için elverişli bir dönemdeyiz",
            "piyasa geneli yükseliş tarafında; tekil sinyal, destekleyici bir arka planla birleşiyor",
            "makro ortam sinyalle aynı yönde — bu, tekil hisse hareketlerinin devam etme olasılığını artıran bir etken",
            "piyasa rejimi destekleyici okunuyor; aynı sinyal zayıf bir piyasada çok daha az anlam taşırdı",
        ],
        "en": [
            "the broad market environment supports setups like this — the stock is moving with the wind, not against it",
            "market-wide conditions are favourable: this is a friendly stretch for stocks with a similar profile",
            "the broad market leans bullish; the individual signal combines with a supportive backdrop",
            "the macro environment points the same way as the signal — a factor that improves the odds of single-stock moves carrying on",
            "the market regime reads as supportive; the same signal would mean far less in a weak market",
        ],
    },
    "early_tier": {
        "tr": [
            "sinyal tek bir güne dayanmıyor: kademeli doğrulama sistemimizde üst üste teyit almış durumda",
            "erken uyarı zincirimizde epey yol almış bir aday — ilk işaretten bu yana her kontrol basamağını geçti",
            "izleme sistemimiz bu hisseyi günlerdir takip ediyordu; sinyal erken aşamadan doğrulanmış aşamaya geçti",
            "aşamalı teyit sürecinde üst basamağa ulaştı: bu, ani bir sıçramaya değil, biriken kanıta dayanan bir sinyal",
            "sinyal zinciri adım adım güçlendi — tek günlük gürültü olma ihtimali bu yüzden daha düşük",
        ],
        "en": [
            "the signal doesn't rest on a single day: it has stacked confirmations in our staged verification system",
            "a candidate well advanced along our early-warning chain — it has cleared every checkpoint since the first flag",
            "our monitoring system had been tracking this stock for days; the signal has moved from early-stage to confirmed",
            "it reached the upper rung of the staged confirmation process: this is a signal built on accumulated evidence, not a sudden jump",
            "the signal chain strengthened step by step — which makes it less likely to be one-day noise",
        ],
    },
}

_DEFAULT_BODY = {
    "tr": [
        "bileşik skoru bugünkü taramanın üst diliminde yer aldı — tek bir faktör değil, genel tablo güçlü",
        "birden fazla ölçütün toplamında günün ortalamasının belirgin üzerinde puan aldı",
        "faktörlerin bileşimi onu bugünkü evrende üst sıralara taşıdı",
    ],
    "en": [
        "its composite score landed in the top slice of today's sweep — the overall picture is strong, not just one factor",
        "across multiple measures combined, it scored clearly above today's average",
        "the mix of factors carried it into the upper ranks of today's universe",
    ],
}

# Opener: ticker'lı tam cümle. Web gövde-varyantında kullanılmaz.
_OPENERS: dict[str, dict[str, list[str]]] = {
    "A": {
        "tr": [
            "Bugünün en güçlü adayı {t}.",
            "Sabah taramasının zirvesinde {t} var.",
            "{t}, bugünkü listenin en üst sırasında.",
        ],
        "en": [
            "Today's strongest candidate is {t}.",
            "{t} sits at the top of this morning's sweep.",
            "{t} holds the highest spot on today's list.",
        ],
    },
    "B": {
        "tr": [
            "{t} bugünkü taramada öne çıktı.",
            "{t}, günün dikkat çeken adaylarından.",
            "{t} bugün güçlü bir profille listede.",
        ],
        "en": [
            "{t} stood out in today's scan.",
            "{t} is one of the day's notable candidates.",
            "{t} makes today's list with a strong profile.",
        ],
    },
    "C": {
        "tr": [
            "{t} bugün radara girdi.",
            "{t}, erken aşamada bir aday olarak listede.",
            "{t} izleme listesine yeni eklendi.",
        ],
        "en": [
            "{t} entered the radar today.",
            "{t} is on the list as an early-stage candidate.",
            "{t} was newly added to the watch list.",
        ],
    },
}

# Gerekçe cümlelerinin önüne gelebilen kısa yönlendirici (boş = doğrudan).
_LEADINS = {
    "tr": ["Nedeni şu:", "Öne çıkaran etkenler açık:", ""],
    "en": ["The reason:", "What puts it there is clear:", ""],
}

_CONNECTORS = {
    "tr": ["Ayrıca", "Üstelik", "Buna ek olarak", "Bir başka detay:"],
    "en": ["Also,", "On top of that,", "Adding to the picture,", "Another detail:"],
}

_SYNTHESIS = {
    "tr": {
        "rvol_momentum_regime": "Bu üç işaret birlikte, fiyat hareketinin yalnızca tek günlük bir sıçrama olmadığını ve destekleyici piyasa arka planında artan katılımla izlendiğini düşündürüyor; devamlılık ise henüz doğrulanmış değil.",
        "rvol_gap_momentum": "Hacim, açılış ve momentumun aynı tabloda buluşması, ilginin seans dışında başlayıp işlem aktivitesiyle sürdüğünü düşündürüyor; gap'in kalıcılığı henüz açık soru.",
        "contraction_momentum": "Daralan banttan çıkan fiyat davranışı momentumla birleşiyor; bu, hareketin yeni bir aşamaya geçtiğini düşündürüyor ancak çözülmenin kalıcılığı henüz kanıtlanmış değil.",
        "early_tier": "Aşamalı teyit ile faktörlerin aynı yönde toplanması, sinyalin tek bir ölçüme dayanmadığını gösteriyor; yine de sonraki seanslar bu tabloyu doğrulamak zorunda.",
        "regime": "Faktörlerin destekleyici rejimle birleşmesi, sinyalin piyasa arka planına karşı çalışmadığını gösteriyor; zayıf bir rejimde aynı tablo farklı okunabilir.",
        "default": "Faktörlerin birlikte görünmesi, tek bir göstergeden daha kapsamlı bir tablo sunuyor; bunun sonraki seanslarda korunup korunmayacağı henüz açık.",
    },
    "en": {
        "rvol_momentum_regime": "Together, these three signals suggest the move is more than a one-day jump and is being watched with rising participation in a supportive market backdrop; persistence is not confirmed yet.",
        "rvol_gap_momentum": "Volume, the open and momentum appearing together suggest interest began outside the session and continued through trading activity; whether the gap holds remains open.",
        "contraction_momentum": "The price emerging from a narrow range is meeting momentum; that suggests a new phase may be starting, but the release has not proved durable yet.",
        "early_tier": "Staged confirmation lining up with the factors shows the signal is not resting on one measure; the next sessions still have to validate the picture.",
        "regime": "The factors lining up with a supportive regime means the signal is not working against the market backdrop; the same picture may read differently in a weak regime.",
        "default": "The factors appearing together give a broader picture than any single indicator; whether it holds over the next sessions remains open.",
    },
    "de": {
        "rvol_momentum_regime": "Zusammen deuten diese drei Signale darauf hin, dass die Bewegung mehr als ein Sprung an einem Tag ist und bei steigender Beteiligung in einem unterstützenden Marktumfeld beobachtet wird; ihre Dauer ist noch nicht bestätigt.",
        "rvol_gap_momentum": "Dass Volumen, Eröffnung und Momentum zusammen auftreten, deutet darauf hin, dass das Interesse außerhalb der Sitzung begann und sich im Handel fortsetzte; ob das Gap hält, bleibt offen.",
        "contraction_momentum": "Das Verlassen der engen Spanne trifft auf Momentum; das kann auf eine neue Phase hindeuten, doch die Dauerhaftigkeit ist noch nicht bewiesen.",
        "early_tier": "Die gestufte Bestätigung zusammen mit den Faktoren zeigt, dass das Signal nicht auf einem einzigen Maß beruht; die nächsten Sitzungen müssen das Bild noch bestätigen.",
        "regime": "Dass die Faktoren mit einem unterstützenden Regime zusammenfallen, zeigt, dass das Signal nicht gegen den Markthintergrund arbeitet; in einem schwachen Regime könnte dasselbe Bild anders gelesen werden.",
        "default": "Die Faktoren zusammen ergeben ein breiteres Bild als ein einzelner Indikator; ob es in den nächsten Sitzungen anhält, bleibt offen.",
    },
}

_CLOSERS = {
    "tr": [
        "Şimdi izlenecek soru şu: bu tablo birkaç seans boyunca korunacak mı? Bu bir izleme adayıdır; karar ve risk yönetimi okuyucuya aittir.",
        "Asıl merak noktası bundan sonra: bu ilgi devam edecek mi, yoksa kısa bir hareket olarak mı kalacak? İzleme amaçlıdır; değerlendirme ve risk tamamen senin kontrolünde.",
        "Bir sonraki bölüm henüz yazılmış değil: sinyal güçlenecek mi, zayıflayacak mı? Aday statüsündedir; ne yapılacağına her zaman okuyan karar verir.",
    ],
    "en": [
        "The question to watch now is simple: will this picture hold for several sessions? This is a watch candidate; decisions and risk management remain yours.",
        "The open question is what happens next: will the interest continue, or prove brief? For monitoring only — judgement and risk stay fully in your hands.",
        "The next chapter is not written yet: does the signal strengthen or fade? Candidate status only; what to do with it is always the reader's call.",
    ],
}

_CAUTION_CLOSERS = {
    "tr": [
        "Günlük fiyat aralığı geniş — izlerken tempoyu buna göre ayarlamak gerekir; karar okuyucuya aittir.",
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


def _cap(s: str, lang: str = "tr") -> str:
    """Capitalize a sentence using Turkish casing only for Turkish text."""
    if not s:
        return s
    first = s[0]
    if lang == "tr" and first == "i":
        return "İ" + s[1:]
    if lang == "tr" and first == "ı":
        return "I" + s[1:]
    return first.upper() + s[1:]


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


def _render_reasons(frags: list[str], lang: str, seed: int) -> str:
    """Tam cümlelerden akıcı bir gerekçe paragrafı kur (noktalı virgül zinciri yok)."""
    if not frags:
        return _cap(_pick(_DEFAULT_BODY[lang], seed), lang=lang) + "."

    leadin = _pick(_LEADINS[lang], seed)
    if leadin:
        sentences = [f"{leadin} {frags[0]}."]
    else:
        sentences = [_cap(frags[0], lang=lang) + "."]

    connectors = _CONNECTORS[lang]
    for i, frag in enumerate(frags[1:]):
        conn = connectors[(seed + i) % len(connectors)]
        if conn.endswith((":", ",")):
            sentences.append(f"{conn} {frag}.")
        else:
            sentences.append(f"{conn} {frag}.")
    return " ".join(sentences)


def _render_synthesis(badges: list[str], lang: str) -> str:
    present = set(badges)
    if {"rvol", "momentum", "regime"}.issubset(present):
        key = "rvol_momentum_regime"
    elif {"rvol", "gap", "momentum"}.issubset(present):
        key = "rvol_gap_momentum"
    elif {"contraction", "momentum"}.issubset(present):
        key = "contraction_momentum"
    elif "early_tier" in present and len(present) >= 2:
        key = "early_tier"
    elif "regime" in present and len(present) >= 2:
        key = "regime"
    else:
        key = "default"
    return _SYNTHESIS[lang].get(key, _SYNTHESIS[lang]["default"])


def build_rationale_parts(
    ticker: str,
    grade: str,
    badges: list[str],
    lang: str = "tr",
    context: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Return {"full": ..., "body": ...}.

    * full — opener sentence with the ticker + reasons + closer
             (Telegram briefs, standalone text).
    * body — reasons + closer only, for surfaces that already display the
             ticker (web cards / the Ledger's editorial lede) so the symbol
             isn't repeated twice in a row.
    """
    ctx = context or {}
    date_str = str(ctx.get("date") or "")
    seed = _seed_int(date_str, ticker)

    lang = lang if lang in ("tr", "en", "de") else "en"
    opener = _pick(_OPENERS.get(grade, _OPENERS["C"])[lang], seed).format(t=ticker)

    try:
        high_atr = float(ctx.get("atr_pct") or 0.0) >= 6.0
    except (TypeError, ValueError):
        high_atr = False
    closer_pool = _CAUTION_CLOSERS[lang] if high_atr else _CLOSERS[lang]
    closer = _pick(closer_pool, _seed_int(date_str, ticker, salt="closer"))

    frags = _fragments_for(badges, lang, date_str, ticker)
    reasons = _render_reasons(frags, lang, seed)
    synthesis = _render_synthesis(badges, lang)

    return {
        "full": f"{opener} {reasons} {synthesis} {closer}",
        "body": f"{reasons} {synthesis} {closer}",
    }


def build_rationale(
    ticker: str,
    grade: str,
    badges: list[str],
    lang: str = "tr",
    context: dict[str, Any] | None = None,
) -> str:
    """Assemble a fluent, causal 2-4 sentence rationale (full variant).

    context (optional): {"date": "YYYY-MM-DD", "atr_pct": float, "price": float}
      - date  -> deterministic daily seed (approve == publish guarantee)
      - atr_pct >= 6 -> cautious closer pool
    """
    return build_rationale_parts(ticker, grade, badges, lang=lang, context=context)["full"]


def prob_band(prob: float) -> str:
    """Calibrated probability -> honest coarse band (never false precision)."""
    if prob <= 0:
        return "—"
    pct = int(round(prob * 100 / 5.0) * 5)
    pct = max(5, min(95, pct))
    return f"~{pct}%"


# ── Almanca (de) havuzları — mevcut sözlüklere import anında birleştirilir ────
_DE_FRAGMENTS = {
    "squeeze": [
        "gegen die Aktie haben sich ungewöhnlich viele Short-Positionen aufgebaut — dreht der Kurs nach oben, kann deren Eindeckung die Bewegung beschleunigen",
        "die Short-Seite ist überfüllt; in einer Erholung könnten diese Positionen zur Eindeckung gezwungen sein, was die Bewegung verstärken kann",
        "es gibt einen hohen Bestand an Wetten gegen diese Aktie — bei kräftigen Aufwärtsbewegungen kann das als zusätzlicher Treibstoff wirken",
        "die Leerverkaufsquote ist hoch; bei solchen Konstellationen nähren sich Aufwärtsbewegungen manchmal selbst",
        "die Short-Positionen liegen auf auffälligem Niveau — eine Erholung könnte diesen Druck ins Gegenteil verkehren",
    ],
    "catalyst": [
        "es gibt eine konkrete jüngste Unternehmensentwicklung (Nachricht oder offizielle Meldung); die Bewegung hat eine identifizierbare Ursache",
        "eine frische Unternehmensnachricht begleitet das Bild — das Signal steht nicht im luftleeren Raum, sondern stützt sich auf ein reales Ereignis",
        "kürzlich gab es eine offizielle Meldung oder Nachricht; das gestiegene Interesse hat etwas Greifbares dahinter",
        "ein aktueller Katalysator begleitet das heutige Signal: der Markt versucht, neue Informationen einzupreisen",
        "im Hintergrund steht eine neue Entwicklung — ein Hinweis darauf, dass die Bewegung nicht zufällig ist",
    ],
    "rvol": [
        "das Handelsvolumen liegt deutlich über seinem Normalwert — das Interesse kommt aus breiter Beteiligung, nicht aus wenigen Einzelorders",
        "das Volumen ist gegenüber dem eigenen Durchschnitt der Aktie erhöht; hinter der Kursbewegung steht echter Orderfluss",
        "der Geldfluss hat sich gegenüber den letzten Tagen beschleunigt — ein Zeichen, dass das Signal mehr ist als ein Kurszucken",
        "das relative Volumen ist hoch — es wechseln weit mehr Aktien den Besitzer als an einem gewöhnlichen Tag",
        "die Handelsaktivität liegt über dem Durchschnitt; wachsendes Interesse zeigt sich meist zuerst im Volumen, dann im Kurs",
    ],
    "gap": [
        "die Aktie eröffnete deutlich über dem Vortagesschluss — ein Zeichen für über Nacht aufgebaute Nachfrage",
        "zur Eröffnung entstand eine Kurslücke (Gap) — der Markt handelte höher, ohne am vorherigen Schlussniveau zu verweilen",
        "Entwicklungen außerhalb der Handelszeit trugen den Kurs zur Eröffnung nach oben; solche Eröffnungen können auf wachsendes Interesse hindeuten",
        "die Eröffnung löste sich nach oben vom Vortagesschluss — das deutet auf über Nacht angesammelte Nachfrage hin",
        "der Eröffnungskurs setzte sich deutlich vom Vortag ab; das Intraday-Verhalten ist deshalb genau zu beobachten",
    ],
    "momentum": [
        "der Kurs tendiert in den letzten Tagen stetig aufwärts — das kurzfristige Momentum spricht für das Signal",
        "das jüngste Kursverhalten ist stark: Rücksetzer bleiben flach, Gewinne werden gehalten",
        "das kurzfristige Momentum ist positiv; die Bewegung ist ein anhaltender Trend, kein Ein-Tages-Sprung",
        "die letzten Sitzungen weisen nach oben — der Kurs wirkt eher von Nachfrage als von Verkaufsdruck getragen",
        "der kurzfristige Kurstrend ist lebhaft; ob das Momentum hält, zeigt sich in den kommenden Tagen",
    ],
    "volume": [
        "das Volumen ist plötzlich sprunghaft gestiegen — das konkreteste Zeichen dafür, dass die Beteiligung real ist",
        "der Umsatz sprang weit über das übliche Niveau; solche Tage markieren oft den Beginn frischen Interesses",
        "es gibt einen deutlichen Volumenschub — die Kursbewegung wird von breiter Handelsaktivität gestützt",
        "heute läuft eine Sitzung mit überdurchschnittlichem Volumen — der Markt schenkt dieser Aktie mehr Aufmerksamkeit als sonst",
        "auf der Volumenseite zeigt sich eine klare Belebung; der Kurs bewegt sich mit Beteiligung, nicht allein",
    ],
    "contraction": [
        "der Kurs steckte lange in einer engen Spanne, die sich nun zu öffnen beginnt — je länger die Verengung, desto ausgeprägter kann die Auflösung sein",
        "eine sich verengende Spanne weicht der Ausdehnung: die Feder war eine Weile gespannt, erste Anzeichen der Entladung sind da",
        "die Aktie handelte wochenlang in einer engen Spanne; das Öffnen der Spanne kündigt oft eine neue Bewegung an",
        "die komprimierte Kursspanne signalisiert eine Auflösung — die über die Zeit aufgebaute Energie könnte auszutreten beginnen",
        "nach einer langen ruhigen Phase weitet sich die Kursspanne; solche Übergangsmomente sind beobachtenswert",
    ],
    "regime": [
        "das breite Marktumfeld stützt solche Konstellationen — die Aktie bewegt sich mit dem Wind, nicht dagegen",
        "die marktweiten Bedingungen sind günstig: eine freundliche Phase für Aktien mit ähnlichem Profil",
        "der Gesamtmarkt neigt nach oben; das Einzelsignal verbindet sich mit einem unterstützenden Umfeld",
        "das Makroumfeld weist in dieselbe Richtung wie das Signal — ein Faktor, der die Chance auf Fortsetzung erhöht",
        "das Marktregime liest sich unterstützend; dasselbe Signal würde in einem schwachen Markt weit weniger bedeuten",
    ],
    "early_tier": [
        "das Signal beruht nicht auf einem einzigen Tag: es hat in unserem gestuften Prüfsystem mehrere Bestätigungen gesammelt",
        "ein Kandidat, der in unserer Frühwarnkette weit fortgeschritten ist — er hat seit dem ersten Flag jede Prüfstufe bestanden",
        "unser Überwachungssystem verfolgte diese Aktie seit Tagen; das Signal wechselte von der Früh- in die bestätigte Phase",
        "es erreichte die obere Stufe des gestuften Bestätigungsprozesses: ein Signal auf Basis angesammelter Belege, kein plötzlicher Sprung",
        "die Signalkette wurde Schritt für Schritt stärker — was ein Ein-Tages-Rauschen unwahrscheinlicher macht",
    ],
}
for _b, _lst in _DE_FRAGMENTS.items():
    _FRAGMENTS.setdefault(_b, {})["de"] = _lst

_DEFAULT_BODY["de"] = [
    "sein Composite-Score landete im oberen Bereich des heutigen Scans — das Gesamtbild ist stark, nicht nur ein einzelner Faktor",
    "über mehrere Kennzahlen hinweg lag es deutlich über dem heutigen Durchschnitt",
    "die Mischung der Faktoren trug es in die oberen Ränge des heutigen Universums",
]

_OPENERS["A"]["de"] = [
    "Der heute stärkste Kandidat ist {t}.",
    "{t} steht an der Spitze des heutigen Scans.",
    "{t} belegt den obersten Platz auf der heutigen Liste.",
]
_OPENERS["B"]["de"] = [
    "{t} stach im heutigen Scan hervor.",
    "{t} ist einer der bemerkenswerten Kandidaten des Tages.",
    "{t} steht mit einem starken Profil auf der heutigen Liste.",
]
_OPENERS["C"]["de"] = [
    "{t} tauchte heute auf dem Radar auf.",
    "{t} steht als Kandidat im Frühstadium auf der Liste.",
    "{t} wurde neu zur Beobachtungsliste hinzugefügt.",
]

_LEADINS["de"] = ["Der Grund:", "Was es dorthin bringt, ist klar:", ""]
_CONNECTORS["de"] = ["Außerdem:", "Zudem:", "Darüber hinaus:", "Ein weiteres Detail:"]
_CLOSERS["de"] = [
    "Dies ist ein Beobachtungskandidat; Entscheidung und Risikomanagement bleiben bei dir.",
    "Nur zur Beobachtung — Bewertung und Risiko liegen ganz in deiner Hand.",
    "Nur Kandidatenstatus; was daraus wird, entscheidet stets der Leser.",
]
_CAUTION_CLOSERS["de"] = [
    "Die Tagesspanne ist weit — passe dein Beobachtungstempo entsprechend an; die Entscheidung liegt bei dir.",
    "Ein schnelllebiges Profil: beide Richtungen können rasch laufen. Beobachtungskandidat; deine Entscheidung.",
    "Ein Kandidat mit hoher Volatilität — er verlangt sorgfältige Beobachtung; das Risiko bleibt beim Leser.",
]
