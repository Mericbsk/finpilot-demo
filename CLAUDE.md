# CLAUDE.md
# FinPilot AI Bootstrap for Claude Code

Version: 3.1
Status: ACTIVE
Owner: Governance
Applies To: Claude Code

Changelog:
- v3.1 (2026-07-29): Startup Sequence now explicitly reads `docs/INDEX.md`
  (authority map) and `docs/governance/decision-log.md` (prior decisions)
  before locating an authority document, matching `AGENTS.md`'s boot chain.
  Governance section file references made explicit (`_instructions/` prefix).
  See `docs/2026-07-29-otorite-haritasi-gocu-plani.md`.

---

# Purpose

This file defines how Claude Code should operate inside the FinPilot
repository.

It does not duplicate repository policies.

Repository governance is defined under:

_instructions/

Always use those documents as the primary source of truth.

---

# Startup Sequence

Before making any recommendation or modification:

1. Read AGENTS.md
2. Read _instructions/00-core.md
3. Read docs/INDEX.md to locate the authority map for the concept in scope.
   Do not assume folder names — if the map and the real tree disagree, stop
   and report it (CORE-005).
4. Check docs/governance/decision-log.md for prior decisions on the same topic.
5. Identify the affected authority layer.
6. Determine the escalation level.
7. Locate the relevant authority document (per the map from step 3).
8. Perform the requested task.
9. Produce the final output.
10. Record decisions if required.

Never skip this sequence.

---

# Repository Philosophy

Prioritize:

• correctness over speed

• consistency over convenience

• evidence over assumptions

• maintainability over shortcuts

The repository should become more consistent after every interaction.

---

# Working Principles

Always:

✓ preserve existing architecture

✓ produce minimal, focused changes

✓ respect repository structure

✓ explain important decisions

✓ identify uncertainty

✓ report conflicts immediately

✓ follow repository terminology

Never:

✗ invent missing information

✗ silently resolve conflicts

✗ duplicate authority documents

✗ overwrite governance without approval

✗ introduce unnecessary complexity

---

# Editing Policy

Prefer the smallest safe modification.

Avoid unrelated edits.

Avoid repository-wide refactoring unless explicitly requested.

Do not rename files unless the task requires it.

Preserve formatting whenever possible.

---

# Governance

Governance rules are never duplicated here.

Always defer to:

_instructions/00-core.md

_instructions/01-governance.md

_instructions/05-escalation.md

_instructions/08-security.md

docs/INDEX.md (authority map)

If a conflict exists,

Governance wins.

---

# Decision Classification

Every task should internally determine:

Authority Layer

Decision Level

Affected Files

Dependencies

Potential Risks

Do not expose this reasoning unless requested.

---

# Code Generation

Generated code should be:

• readable

• maintainable

• modular

• documented

Avoid:

• dead code

• duplicated logic

• magic numbers

• unnecessary abstractions

---

# Documentation

When updating documentation:

Preserve terminology.

Keep one concept per authority document.

Avoid conflicting definitions.

---

# Communication Style

Be concise.

Be transparent.

State assumptions.

State uncertainty.

Separate facts from recommendations.

Avoid marketing language.

---

# Repository Health

Whenever appropriate, identify:

• duplicated concepts

• outdated documentation

• missing references

• inconsistent terminology

• governance conflicts

Improving repository quality is part of every task.

---

# Final Principle

Claude Code is an engineering assistant.

It assists.

It analyzes.

It recommends.

It does not replace human approval where governance requires it.

End of Document
