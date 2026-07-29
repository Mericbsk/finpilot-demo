---
description: Run the quarterly repository governance health check
---

Run the quarterly health check using `docs/INDEX.md`,
`docs/governance/decision-log.md` and `_instructions/00-core.md`
CORE-005/CORE-011/CORE-015. There is no standalone
`quarterly-health-check.md`; do not invent one. Produce a report covering:

1. **Authority conflicts** — any concept with 2+ files claiming to be
   the authority source. List file pairs and the conflicting content.
2. **Pending Level B/C decisions** — list every decision-log.md entry
   still marked "pending," with age in days since it was proposed.
3. **Terminology drift** — any term used in `scanner/`, `distribution/`,
   `api/`, `core/`, `web/src/`, `research/` or `reports/` that doesn't match
   `distribution/glossary.py`.
4. **Retrospective silent conflicts** — scan recent decision-log.md
   entries for any case where a conflict appears to have been resolved
   without being explicitly flagged at the time.
5. **Security findings** — any hardcoded secrets, keys, or credentials
   found anywhere in the repository, masked in the output.
6. **Repository health score** — for each of clarity, maintainability,
   consistency, traceability, documentation quality, give a short
   qualitative rating (Good / Needs Attention / Critical) with one
   sentence of justification each. Do not invent a numeric score
   without justifying it.

Do not fix any issue automatically. Only report. Findings requiring
action must be tagged with the correct escalation level (A/B/C) per
`_instructions/00-core.md` CORE-007.
