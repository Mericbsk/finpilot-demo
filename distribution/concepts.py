"""'Günün kavramı' — tek kaynak: distribution.glossary (33 terim).

API geriye uyumlu: TERMS (slug, name, line) üçlüleri + concept_of_the_day().
"""

from __future__ import annotations

from datetime import date

from distribution.glossary import GLOSSARY

SITE = "https://www.finpilot.at"

# (slug, TR name, TR line) — glossary'den türetilir
TERMS: list[tuple[str, str, str]] = [(e["slug"], e["name_tr"], e["line_tr"]) for e in GLOSSARY]


def concept_of_the_day(d: date | None = None) -> str:
    """Deterministic daily rotation -> brief line (33 gün tekrarsız)."""
    d = d or date.today()
    slug, name, definition = TERMS[d.toordinal() % len(TERMS)]
    return f"<b>{name}</b> — {definition}"


def concept_of_the_day_struct(d: date | None = None, lang: str = "tr") -> dict[str, str]:
    """Same deterministic rotation as concept_of_the_day(), structured for the
    web Ledger's S3 'Daily Double' card (name + line, no HTML markup).
    """
    d = d or date.today()
    entry = GLOSSARY[d.toordinal() % len(GLOSSARY)]
    if lang == "en":
        return {"name": entry["name_en"], "line": entry["line_en"]}
    return {"name": entry["name_tr"], "line": entry["line_tr"]}
