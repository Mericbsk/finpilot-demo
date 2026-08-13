"""Build print-ready HTML files for the ten manuscript drafts."""

from __future__ import annotations

import html
import re
from pathlib import Path

try:
    import markdown
except ImportError as exc:  # pragma: no cover - environment diagnostic
    raise SystemExit("The markdown package is required") from exc


SOURCE_DIR = Path("reports/content_series")
OUTPUT_DIR = Path("reports/content_series/html")
PAGE_RE = re.compile(r"(?=^## Page \d+ — .+$)", re.MULTILINE)


STYLE = """
@page { size: A4; margin: 16mm; @bottom-right { content: "Page " counter(page); color: #53616b; font: 9pt Georgia, serif; } }
body { color: #17202a; font-family: Georgia, serif; margin: 0; }
.book-title, .contents { break-after: page; min-height: 250mm; padding: 22mm 10mm 0; }
.book-title h1 { color: #0b5d5e; font-size: 30pt; margin-top: 30mm; }
.book-title p { font-size: 13pt; line-height: 1.6; }
.contents h2 { border-bottom: 2px solid #d08c60; color: #0b5d5e; padding-bottom: 5mm; }
.contents ol { columns: 2; column-gap: 12mm; padding-left: 7mm; }
.contents li { break-inside: avoid; font-size: 9.5pt; line-height: 1.45; margin-bottom: 2mm; }
.page { break-before: page; min-height: 250mm; }
.page h2 { border-bottom: 2px solid #d08c60; color: #0b5d5e; padding-bottom: 5mm; }
.page h3 { color: #8b4c39; margin-top: 12mm; }
.page p, .page li { font-size: 11.5pt; line-height: 1.55; }
.page blockquote { border-left: 4px solid #d08c60; padding-left: 5mm; }
.page-note { color: #53616b; font-size: 9pt; margin-top: 15mm; }
"""


def render(path: Path) -> Path:
    source = path.read_text(encoding="utf-8")
    chunks = PAGE_RE.split(source)
    intro = chunks[0]
    pages = chunks[1:]
    title_html = markdown.markdown(intro, extensions=["tables"])
    toc_items = []
    for page_number, chunk in enumerate(pages, start=1):
        heading = re.search(r"^## Page \d+ — (.+)$", chunk, re.MULTILINE)
        if heading:
            toc_items.append(f"<li>{page_number}. {html.escape(heading.group(1))}</li>")
    toc_html = "<h2>Contents</h2><ol>" + "".join(toc_items) + "</ol>"
    page_html = "\n".join(
        f'<section class="page" id="page-{page_number}">{markdown.markdown("## Page " + chunk, extensions=["tables"])}</section>'
        for page_number, chunk in enumerate(pages, start=1)
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(path.stem)}</title>
<style>{STYLE}</style></head><body>
<header class="book-title">{title_html}</header>
<nav class="contents" aria-label="Contents">{toc_html}</nav>
{page_html}
</body></html>
"""
    output = OUTPUT_DIR / f"{path.stem}.html"
    output.write_text(document, encoding="utf-8")
    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(SOURCE_DIR.glob("*.md")):
        if path.name == "source_rights_register_2026-08-10.md":
            continue
        print(f"built {render(path)}")


if __name__ == "__main__":
    main()
