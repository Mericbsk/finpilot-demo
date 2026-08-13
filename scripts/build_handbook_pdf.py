"""Convert the handbook Markdown to print-ready HTML (ledger typography)."""

from __future__ import annotations

import pathlib

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
MD = ROOT / "reports" / "honest_quant_handbook_2026-08-10.md"
OUT = ROOT / "reports" / "honest_quant_handbook_2026-08-10.html"

CSS = """
@page { margin: 2.2cm; size: A4; }
body { font-family: Georgia, 'Times New Roman', serif; color: #1a1a1a; line-height: 1.65; max-width: 680px; margin: 0 auto; padding: 40px 20px; font-size: 11.5pt; }
h1 { font-size: 22pt; border-bottom: 2px solid #1a1a1a; padding-bottom: 8px; margin-top: 0; }
h2 { font-size: 15pt; margin-top: 36px; border-bottom: 1px solid #999; padding-bottom: 4px; page-break-after: avoid; }
h3 { font-size: 12pt; margin-top: 24px; page-break-after: avoid; }
blockquote { border-left: 3px solid #888; margin: 16px 0; padding: 8px 16px; color: #444; font-style: italic; background: #f7f5f0; }
table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 10.5pt; }
th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
th { background: #f0ede6; }
code { font-family: 'Courier New', monospace; background: #f4f4f4; padding: 1px 4px; font-size: 10pt; }
pre { background: #f4f4f4; padding: 12px; overflow-x: auto; font-size: 9.5pt; page-break-inside: avoid; }
hr { border: none; border-top: 1px solid #ccc; margin: 32px 0; }
ul, ol { padding-left: 24px; }
li { margin-bottom: 4px; }
strong { color: #000; }
"""


def main() -> None:
    md_text = MD.read_text(encoding="utf-8")
    body = markdown.markdown(md_text, extensions=["tables", "toc", "fenced_code"])
    html = (
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">\n'
        "<title>The Honest Quant Research Handbook</title>\n"
        f"<style>{CSS}</style></head><body>\n{body}\n</body></html>"
    )
    OUT.write_text(html, encoding="utf-8")
    print(f"HTML written: {OUT} ({len(html)} chars)")


if __name__ == "__main__":
    main()
