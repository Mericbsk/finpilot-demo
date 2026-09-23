"""Generate the FinPilot pitch deck PDF from the HTML, one slide per page."""

from playwright.sync_api import sync_playwright

SRC = "file:///C:/Users/meric/Borsa/docs/pitch_deck_finpilot_2026-09-07.html"
OUT = "docs/pitch_deck_finpilot_2026-09-07.pdf"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 720})
    pg.goto(SRC, wait_until="networkidle")
    pg.wait_for_timeout(1200)
    tallest = pg.evaluate(
        "Math.max.apply(null, Array.from(document.querySelectorAll('.slide')).map(function(s){return s.scrollHeight}))"
    )
    print("tallest slide px:", tallest)
    # A4 landscape is 297mm x 210mm. Height in inches = px / 96.
    height_in = tallest / 96.0
    pg.pdf(
        path=OUT,
        width="297mm",
        height=f"{height_in:.2f}in",
        print_background=True,
        margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
    )
    b.close()

data = open(OUT, "rb").read()
print("bytes:", len(data), "pages:", data.count(b"/Type /Page"), "header:", data[:8])
