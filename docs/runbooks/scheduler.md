# Runbook: Scheduler Stalled

**Severity**: P1
**Owner**: Platform team

## Symptoms

- Prometheus alert `SchedulerNoRecentRun` (last `scheduler_last_run_timestamp_seconds` > 2h ago).
- KPI dashboard shows no fresh signals; `agent_state` returns stale scan data.
- API endpoint `/api/v1/agent/scheduler/last_run` reports a timestamp > 2h old.

## Diagnose

```bash
# 1. Is the scheduler thread alive?
docker compose exec api python -c "from core.scheduler import get_scheduler; print(get_scheduler().is_running())"

# 2. Last successful run + error trail
curl -sf http://api:8000/api/v1/agent/scheduler/status | jq

# 3. Container logs (last 200 lines)
docker compose logs --tail=200 api | grep -iE "scheduler|apscheduler|error"
```

## Mitigate

1. **Restart scheduler thread only** (preserves API):
   ```bash
   curl -X POST http://api:8000/api/v1/agent/scheduler/restart \
        -H "Authorization: Bearer $ADMIN_TOKEN"
   ```
2. If endpoint not responsive, restart the container:
   ```bash
   docker compose restart api
   ```
3. Verify within 60s:
   ```bash
   curl -sf http://api:8000/api/v1/agent/scheduler/last_run | jq .last_run
   ```

## Resolve

- Inspect `logs/api.log` for unhandled exceptions in any agent step (scanner/research/backtest/monitor).
- If the failure repeats for the same step, disable that agent via `agents.{name}.enabled=false` in `core/config.py` and open a bug.
- Check upstream data provider (yfinance / Polygon) — an extended outage can wedge the scheduler.

## Escalate

- 2 failed restarts in 30 min → page on-call engineer.
- Data provider outage > 1 h → notify CEO agent advisory team.
