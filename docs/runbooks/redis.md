# Runbook: Redis Unavailable

**Severity**: P1
**Owner**: Platform team

## Symptoms

- `/api/v1/ready` returns `degraded` (or `unhealthy` if hard-required).
- Logs contain `agent_state: Redis UNAVAILABLE … falling back to in-memory`.
- Inter-agent feedback (`agents/feedback.py`) loses entries between restarts.
- KPI history reset to zero after API restart.

## Diagnose

```bash
# 1. Is the redis container up?
docker compose ps redis

# 2. Direct ping
docker compose exec redis redis-cli ping
# Expected: PONG

# 3. From the API container
docker compose exec api python -c "from core import agent_state; print(agent_state._redis is not None)"
```

## Mitigate

1. Restart redis:
   ```bash
   docker compose restart redis
   ```
2. Once `redis-cli ping` returns `PONG`, restart the API so it re-establishes its connection:
   ```bash
   docker compose restart api
   ```
3. Verify:
   ```bash
   curl -sf http://api:8000/api/v1/ready | jq '.checks[] | select(.name=="redis")'
   ```

## Resolve

- Check redis volume disk space: `docker compose exec redis df -h /data`.
- Inspect `redis` container logs for OOM kills or persistence errors.
- If memory pressure is the cause, increase `maxmemory` or add an eviction policy in `redis.conf`.

## Escalate

- Redis down > 30 min OR repeated restarts → page on-call.
- Data corruption (rdb/aof errors) → DBA on-call + restore from snapshot.
