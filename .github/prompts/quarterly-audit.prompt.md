---
description: Run the quarterly repository governance health check
---

Run the quarterly health check per `/05-governance/quarterly-health-check.md`
and `/00-core.md` CORE-005/CORE-011/CORE-015. Produce a report covering:

1. **Authority conflicts** — any concept with 2+ files claiming to be
   the authority source. List file pairs and the conflicting content.
2. **Pending Level B/C decisions** — list every decision-log.md entry
   still marked "pending," with age in days since it was proposed.
3. **Terminology drift** — any term used in `/01-product`, `/02-engineering`,
   or `/03-research` that doesn't match `/04-content/glossary.md`.
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
`/00-core.md` CORE-007.
