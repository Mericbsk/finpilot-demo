---
applyTo: "05-governance/**"
description: Audits, decision log, risk and compliance policy
---

# Governance Instructions

Authority reference: `/05-governance/risk-policy.md` — Layer 2, holds
veto power over every other layer including Mission (Layer 1).

- Never soften, reinterpret, narrow, or work around a risk rule to
  satisfy a product, engineering, or strategy request. If a request
  conflicts with risk policy, the request must be rejected or
  escalated to Level C — never quietly adjusted to fit.
- `decision-log.md` entries must always include: date, title, layer,
  level (A/B/C), context, change (before/after), impact, status.
  No entry may be marked "applied" if it is Level B/C and lacks
  recorded human approval — it must stay "pending."
- Audits (quarterly health checks) must report, not fix. Never
  auto-resolve a conflict discovered during an audit — surface it in
  the report only, per the conflict-transparency rule in `/00-core.md`.
- If two files both claim to be the "authority" for the same concept,
  this is a **P0 finding** — report it at the top of any audit output,
  before anything else.
- Sensitive data (API keys, secrets, personal user data) must never
  appear in governance documents. If found, flag as a P0 security
  issue and mask the value in any output (e.g., "sk-***MASKED***").
