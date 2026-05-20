# Runbook: Win-Rate Dropped Below 0.45

**Severity**: P2
**Owner**: Strategy / Quant team

## Symptoms

- Prometheus alert `WinRateDegraded`.
- Agent Hub KPI dashboard shows 7-day win-rate < 0.45.
- User complaints about bad signals on Telegram / advisory chat.

## Diagnose

```bash
# 1. Per-agent win-rate
curl -sf http://api:8000/api/v1/kpi/per_agent | jq

# 2. Recent failed signals
curl -sf http://api:8000/api/v1/history/signals?limit=50 | jq '[.[] | select(.outcome=="loss")]'

# 3. Backtest vs live divergence
curl -sf http://api:8000/api/v1/backtest/last | jq .summary
```

## Mitigate

1. **Pause auto-Telegram alerts** for entry signals while investigating:
   - Set `TELEGRAM_AUTO_ENTRY=false` and restart API.
2. **Tighten signal threshold** temporarily:
   - `core/config.py` → `scanner.signal_threshold = 4` (from default 3).
3. **Switch to conservative scanner preset**:
   ```bash
   curl -X POST http://api:8000/api/v1/agent/scanner/preset?name=conservative
   ```

## Resolve

- Walk-forward optimization on the most recent regime (run S6-3 UI when available).
- DRL retraining if PPO model is stale (> 14 days old).
- Update advisory CTO/CPO weekly review to flag the drop.

## Escalate

- Win-rate < 0.40 for 3 consecutive days → strategy lead + product owner sync.
