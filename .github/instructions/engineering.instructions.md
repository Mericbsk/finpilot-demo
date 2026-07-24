---
applyTo: "02-engineering/**"
description: Architecture, execution system, event flow
---

# Engineering Instructions

Authority reference: `/02-engineering/architecture.md`.

- Preserve the existing event-driven architecture. Introducing a new
  execution pattern, queueing model, or data flow is **Level B** —
  propose and wait for approval, do not implement directly.
- Any change touching live execution, order routing, or position
  sizing logic is automatically **Level C** — analysis only.
- If a change requires modifying composite score or entry/exit logic,
  stop and check `/01-product/*` first — that layer owns the rule,
  this layer only owns the implementation. Do not silently reinterpret
  a product rule while implementing it.
- Apply the Minimal Change Principle strictly: no drive-by refactors,
  no renaming unrelated to the task, no dependency upgrades unless
  explicitly requested.
- Every architectural decision (new service, new dependency, changed
  data model) must get a decision-log.md entry, tagged Layer 5.
- Write code that matches existing style/conventions in the same
  module. If no convention exists, default to the most common pattern
  already present in `/02-engineering/`.
- Never hardcode secrets, API keys, or credentials. If one is found in
  existing code, flag it as a **Level C security issue** immediately,
  do not attempt to fix it yourself without approval.
