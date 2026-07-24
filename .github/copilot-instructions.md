---
description: FinPilot repository-wide operating rules — always active for every AI agent
---

# FinPilot — Workspace Instructions (Global)

This repository is governed by `/00-core.md` (v3.0), the immutable
constitution for every AI agent working here — Claude Code, GitHub
Copilot, Cursor, Windsurf, VS Code Agent Mode, or any future FinPilot
internal agent. Read `/00-core.md` and `/_instructions/core-rules.yaml`
before starting any task, even if this file seems sufficient on its own.

## Repository map

```
/00-strategy      → mission, roadmap, growth/grant strategy
/01-product       → scanner logic, composite score, entry/exit rules
/02-engineering    → architecture, execution system, event flow
/03-research      → backtests, academic/GitHub evidence research
/04-content        → Finance Academy, glossary, user-facing docs
/05-governance     → audits, decision-log.md, risk-policy.md
/06-releases       → release notes, test results, rollout logs
/_instructions      → 00-core.md, core-rules.yaml, this folder
```

## Authority hierarchy (never violate the order)

1. Mission / Vision — `/00-strategy/mission.md`
2. Risk & Compliance — `/05-governance/risk-policy.md` (holds VETO over all layers)
3. Roadmap / Strategy — `/00-strategy/roadmap-*.md`
4. Product rules — `/01-product/*`
5. Engineering / architecture — `/02-engineering/*`
6. Content / documentation — `/04-content/*`
7. Tactical / release decisions — `/06-releases/*`

A lower layer can never override a higher layer. Layer 2 (Risk &
Compliance) can override anything, including Mission.

## Mandatory sequence for every task (no exceptions)

1. Identify which layer(s) above the task touches.
2. Classify the task as Level A, B, or C:
   - **Level A (autonomous)** — typo fixes, formatting, renaming,
     versioning, applying an already-approved rule. Apply directly,
     then log it.
   - **Level B (proposal, wait for approval)** — new product rule,
     roadmap change, new content strategy, new module. Draft only,
     state clearly: "This is a Level B decision, awaiting approval."
   - **Level C (human approval required, cannot be applied by AI)** —
     risk limits, position sizing, production/live release, API
     keys/secrets, regulatory or grant submissions. Present analysis
     only, state clearly: "This is a Level C decision and cannot be
     applied by AI."
   - Any conflict touching Layer 1 or 2 automatically escalates to
     Level C, regardless of how small it looks.
3. Locate the single authority document for the concept in question.
   Never duplicate business rules, formulas, or policy text across
   files — reference the authority file instead of copying it.
4. Check `/05-governance/decision-log.md` for prior decisions on the
   same topic before proposing anything new.
5. If a conflict is found between two documents or between a new
   request and an existing decision, STOP and report it explicitly.
   Never resolve it silently, and never pick a side without flagging
   the conflict to the user first.
6. Produce the output, explicitly stating: the layer, the level
   (A/B/C), and the target file/folder/version where it belongs.
7. For Level A actions, add an entry to
   `/05-governance/decision-log.md` immediately. For Level B/C, add an
   entry marked "pending" until human approval is recorded.

## Non-negotiable rules (from `/00-core.md`, always enforced)

- Never fabricate information. If data, metrics or evidence are
  missing, say so explicitly and ask for clarification instead of
  guessing.
- Never silently resolve conflicts between documents, decisions, or
  requirements — always surface them first.
- Never bypass, reinterpret, or soften a Risk & Compliance rule for
  any technical or product convenience.
- Never present a Level B or Level C recommendation as if it were an
  approved, final decision.
- Never duplicate an authority document's content — reference it.
- Never overwrite an authority document without explicit approval;
  version it instead (`vX.Y`, with a changelog header).
- Documentation in this repository always outranks conversational
  memory or prior chat context. If they disagree, the repository wins.
- Never hide uncertainty — state confidence level and assumptions
  explicitly when evidence is incomplete.

## Engineering baseline (applies everywhere unless a path-specific file overrides it)

- Match existing code patterns and naming conventions in the file
  being edited before introducing new ones.
- Apply the Minimal Change Principle: implement the smallest safe
  change that solves the stated problem. No unrelated refactors.
- Preserve existing architecture unless a Level B/C change explicitly
  approves a redesign.
- Every non-trivial change must be explainable and traceable — if you
  cannot explain why a change was made, it is not considered complete.

## Communication style

- Communicate like a professional engineering organization: precise,
  evidence-based, no marketing language, no unsupported claims.
- State assumptions and confidence levels explicitly rather than
  implying certainty.

For domain-specific rules, see the path-specific files in
`.github/instructions/`. Those files add detail — they never
override this file or `/00-core.md`.
