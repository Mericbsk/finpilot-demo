# Runbook: API /ready Probe Failing

**Severity**: P0
**Owner**: Platform team

## Symptoms

- Load balancer / K8s removes API pods from rotation.
- `/api/v1/ready` returns 503 with `status=unhealthy`.
- Customer-facing 502/504 errors.

## Diagnose

```bash
# 1. Which dependency is failing?
curl -sf http://localhost:8000/api/v1/ready | jq '.checks'

# 2. Process alive but unhealthy?
curl -sf http://localhost:8000/api/v1/live   # should always return 200

# 3. Recent logs
docker compose logs --tail=200 api
```

## Mitigate

| Failing check | Action |
|---------------|--------|
| `database` | Restart API; if persists, see DB runbook. |
| `redis` | See [redis.md](redis.md). Degraded (not unhealthy) is acceptable short-term. |
| Multiple | Roll back to last green deploy: `docker compose pull api:<previous-tag> && docker compose up -d`. |

If `/live` is also failing, the process is wedged → restart container.

## Resolve

- Add the failing dependency's metric to the on-call dashboard.
- Update PR review checklist: any new dependency must register a `health_check`.

## Escalate

- All API replicas unhealthy > 5 min → page incident commander.
