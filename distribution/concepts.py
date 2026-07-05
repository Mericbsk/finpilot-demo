"""'Günün kavramı' rotation — 12 core terms, shared with web ⓘ cards.

Content lives here (single source); web/src/lib/terms.ts mirrors it for the
demo page. When the FinSense content factory ships its content pack, this
module reads from the pack instead.
"""

from __future__ import annotations

from datetime import date

SITE = "https://www.finpilot.at"

# slug, TR name, one-line TR definition (brief-friendly)
TERMS: list[tuple[str, str, str]] = [
    (
        "short-interest",
        "Short Interest",
        "Bir hissede açığa satılmış pay oranı; yüksekse ani yukarı hareketlerde 'squeeze' yakıtı olabilir.",
    ),
    (
        "short-squeeze",
        "Short Squeeze",
        "Açığa satanların zararı kapatmak için alım yapmak zorunda kalması — fiyatı hızla yukarı iter.",
    ),
    (
        "gap",
        "Gap (Fiyat Boşluğu)",
        "Bir günün kapanışı ile ertesi günün açılışı arasındaki fiyat sıçraması; güçlü haber/akış işaretidir.",
    ),
    (
        "rvol",
        "RVOL (Göreli Hacim)",
        "Bugünkü hacmin normal hacme oranı; 1.5+ ise hissede olağan dışı ilgi var demektir.",
    ),
    (
        "atr",
        "ATR (Ortalama Gerçek Aralık)",
        "Hissenin günlük tipik hareket genişliği; yüksek ATR = yüksek fırsat VE yüksek risk.",
    ),
    (
        "calibration",
        "Kalibrasyon",
        "Bir olasılık tahmininin gerçek frekansla örtüşmesi; '%60' diyorsak gerçekten ~%60 çıkmalı.",
    ),
    (
        "base-rate",
        "Baz Oran",
        "Hiçbir filtre olmadan olayın gerçekleşme sıklığı; her sinyal bu tabana karşı ölçülür.",
    ),
    (
        "regime",
        "Piyasa Rejimi",
        "Piyasanın genel modu (trend/yatay, risk-on/risk-off); aynı sinyal farklı rejimde farklı çalışır.",
    ),
    (
        "catalyst",
        "Katalizör",
        "Fiyatı hareket ettirebilecek somut olay: bilanço, FDA kararı, 8-K dosyalaması, büyük sözleşme.",
    ),
    (
        "liquidity",
        "Likidite",
        "Hisseyi fiyatı bozmadan alıp satabilme kolaylığı; düşük likidite = geniş spread + kayma riski.",
    ),
    (
        "drawdown",
        "Drawdown",
        "Tepe noktadan dip noktaya yaşanan kayıp; risk disiplininin ana ölçüsü.",
    ),
    (
        "position-sizing",
        "Pozisyon Boyutlandırma",
        "Tek bir işleme sermayenin ne kadarının ayrılacağı kararı; uzun vadeli hayatta kalmanın anahtarı.",
    ),
]


def concept_of_the_day(d: date | None = None) -> str:
    """Deterministic daily rotation -> brief line."""
    d = d or date.today()
    slug, name, definition = TERMS[d.toordinal() % len(TERMS)]
    return f"*{name}* — {definition}"
