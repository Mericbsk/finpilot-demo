# Runbook: LLM Provider Down

**Severity**: P2
**Owner**: Advisory team

## Symptoms

- `/api/v1/advisory/{persona}` POST returning 5xx or timing out (>30s).
- Logs contain `groq.APIError`, `openai.APIError`, or `httpx.ReadTimeout` from `llm/` modules.
- Advisory chat UI shows "AI yanıtı alınamadı" toast.

## Diagnose

```bash
# 1. Confirm provider status
curl -I https://api.groq.com/openai/v1/models  # or relevant provider

# 2. API logs
docker compose logs --tail=100 api | grep -iE "llm|groq|openai|api error"

# 3. Recent advisory call durations
curl -sf "http://api:8000/api/v1/metrics" | grep llm_request_duration_seconds
```

## Mitigate

1. **Switch primary provider** (if multi-provider configured):
   ```bash
   docker compose exec api python -c "from llm import set_primary; set_primary('openai')"
   ```
2. **Enable cached/fallback responses** by setting env `LLM_FALLBACK=cache` and restarting API.
3. **Disable LLM in MarketIntelligence** to prevent advisory cascade failure:
   - Edit `agents/market_intelligence.py` config or set `MARKET_INTEL_USE_LLM=false`.

## Resolve

- Track the provider's status page; subscribe to incident notifications.
- If outage > 2h, post user-facing banner via the advisory frontend.
- Review timeout/retry settings in `llm/client.py` (default: 30s timeout, 2 retries).

## Escalate

- Total LLM outage > 1 h → notify product owner.
- Cost spike (rate limit retries) → finance team.
