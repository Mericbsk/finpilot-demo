---
applyTo: "06-releases/**"
description: Release notes, rollout logs, test results
---

# Releases Instructions

- Any content implying a production/live rollout is **Level C** —
  drafting release notes is fine, but marking a release as "shipped"
  or "live" requires recorded human approval in decision-log.md.
- Release notes must reference the specific decision-log.md entries
  and authority documents (product/engineering) that the release
  implements — never describe a change without linking its origin.
- Test results included here must be raw and unmodified; never
  round, cherry-pick, or omit failing results to make a release look
  more successful than it was.
- If a release note contradicts a prior release note (e.g., reverting
  a previously announced feature), state that explicitly — don't
  silently replace the old note.
