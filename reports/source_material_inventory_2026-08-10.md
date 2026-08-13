# Source Material Inventory for Commercial Content

Date: 2026-08-10
Status: DRAFT — research and rights review

## Finding

The Borsa workspace and the sibling `C:\Users\meric\Finsense` repository do
not contain the downloaded source books. The likely source material was found
in `C:\Users\meric\Downloads`, including PDFs about financial literacy,
strategy evidence, composite scores, data quality, DRL, and FinPilot research.
The inspected files do not expose a verified open-source or commercial licence.
The Borsa PDF set itself is primarily FinPilot's own research, grant, pitch,
business, and product documents, plus the already-generated handbook.

The repository also contains project DOCX files, but their filenames identify
them as internal FinPilot reports, plans, audits, and architecture documents.
They are not evidence of an open-source book licence.

## Classification

### Potentially reusable FinPilot-owned material

- `monetization/finpilot-handbook-why-your-backtest-is-lying.pdf`
- `grant_documents/FinSense_Sozluk_Yol_Haritasi.pdf`
- selected research reports under `reports/`
- `distribution/glossary.py`
- selected educational material under `academy/`

These can support original products if claims are checked, confidential details
are removed, and research findings retain their exploratory status.

### Internal or confidential material

- `grant_documents/*`
- `docs/FINANZPLAN_AWS_GRUENDUNGSFONDS.pdf`
- `docs/FinPilot_Pitch_Deck_*.pdf`
- internal audit, business-plan, financial-projection, and architecture files

These documents contain labels such as `Gizli`, `Vertraulich`, or `Confidential`
and must not be repackaged for Gumroad without an explicit ownership and
publication review. Investor, grant, financial, customer, and roadmap claims
also require separate freshness checks.

### Not source books

The PDFs under `.venv/` are package assets and have no relevant educational
content. They are excluded from the product inventory.

## Product opportunities from current material

1. **Market literacy deck:** an expanded bilingual deck built from the 37
   glossary terms plus original examples, misconceptions, and questions.
2. **Research integrity workbook:** exercises derived from the handbook and
   research modules: label audit, effective sample size, base-rate comparison,
   and execution-cost checks.
3. **Four-gate audit template:** a practical worksheet covering data,
   measurement, execution, and signal readiness.
4. **Case-study bundle:** selected, redacted FinPilot experiments presented as
   discovery signals and methodological lessons, not as trading proof.
5. **FinSense vocabulary expansion plan:** a free sample chapter or roadmap
   product only after the 1,500-term target and source/licence status are
   supported by actual content.

## Missing input

The likely downloaded source files are outside the workspace. To use them in a
reproducible product build, copy or explicitly register the selected files and
their source metadata. For each book or report we need:

- title and author;
- source URL or publisher record;
- licence or public-domain basis;
- edition and publication year;
- pages or chapters intended for commercial adaptation;
- whether figures, tables, quotations, and translations are permitted.

Until this register exists, the safe production method is to use the books for
background understanding only and write original explanations, examples,
exercises, and layouts. No external book is cited as a source in the current
card-deck draft. See `reports/finpilot_source_book_product_map_2026-08-10.md`
for the current product mapping and prioritisation.
