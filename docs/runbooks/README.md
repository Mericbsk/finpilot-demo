# FinPilot Operational Runbooks

Production incident playbooks. Each runbook contains:
- **Symptoms**: how to recognise the incident
- **Diagnose**: commands and dashboards to confirm
- **Mitigate**: immediate actions to restore service
- **Resolve**: long-term fixes and follow-ups
- **Escalate**: who to page when the runbook fails

## Index

| Runbook | Page | Severity |
|---------|------|----------|
| Scheduler stalled (no eval in >2h) | [scheduler.md](scheduler.md) | P1 |
| Redis unavailable (in-memory fallback) | [redis.md](redis.md) | P1 |
| LLM provider down (advisory failures) | [llm.md](llm.md) | P2 |
| API health probe failing (/ready 503) | [api-health.md](api-health.md) | P0 |
| Win-rate dropped below 0.45 | [win-rate.md](win-rate.md) | P2 |

## Conventions

- **P0**: Customer-facing outage. Acknowledge in 5 min, mitigate in 15 min.
- **P1**: Degraded service. Acknowledge in 15 min, mitigate in 1 h.
- **P2**: Internal SLO breach. Acknowledge in 1 business day.
