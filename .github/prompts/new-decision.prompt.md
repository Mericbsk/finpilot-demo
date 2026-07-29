---
description: Draft a new decision-log.md entry for a proposed change
---

Draft a new entry for `docs/governance/decision-log.md` for the change
being discussed in this conversation. Before drafting:

1. Determine the authority layer(s) affected (per the hierarchy in
   `.github/copilot-instructions.md`).
2. Determine the escalation level (A/B/C) per `_instructions/00-core.md` CORE-007.
3. Check whether an authority document already exists for this
   concept — if yes, this entry must reference it, not restate it.
4. Check for conflicting prior entries in decision-log.md.

Output the entry using this exact format:

```
[Date] — [Decision Title] — Layer: [X] — Level: [A/B/C]
Context: [why this change is needed]
Change: [before → after]
Impact: [files/components affected]
Status: [applied (Level A only) / pending approval (Level B/C)]
```

If Level B or C, end with: "Awaiting human approval before this can
be marked as applied."
