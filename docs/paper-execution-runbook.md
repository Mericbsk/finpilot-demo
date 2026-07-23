# FinPilot Paper Execution Runbook

## Safety defaults

`FINPILOT_EXECUTION_MODE` defaults to `dry_run`. The only mode that can call Alpaca is `paper_execution`, and the broker client is constructed with `paper=True`. A signal carrying `environment=live` is rejected by the gateway.

The execution worker is opt-in through the Compose `execution` profile. Do not set `FINPILOT_EXECUTION_MODE=paper_execution` until paper credentials, a dedicated database, and the kill-switch procedure have been verified.

## Local dry run

```powershell
$env:FINPILOT_EXECUTION_MODE = "dry_run"
python -m pytest tests/test_execution_gateway.py tests/test_reconciliation.py -q
```

Submit a scanner-shaped signal through the protected API route after authentication:

```text
POST /api/v1/execution/signals
```

The gateway persists an `execution_intents` row and an `execution_events` row, but it does not call Alpaca in `dry_run` or `paper_shadow`.

## Paper execution

Use a dedicated paper database and paper credentials. Start the API and worker explicitly:

```powershell
$env:FINPILOT_DB_PATH = "C:\Users\meric\Borsa\data\finpilot-paper.db"
$env:FINPILOT_EXECUTION_MODE = "paper_execution"
docker compose --profile execution up -d --build api execution
```

Before sending signals:

1. `GET /api/v1/execution/status`
2. Confirm `mode` is `paper_execution`.
3. Confirm the account is the intended Alpaca paper account.
4. Keep the kill switch enabled while checking credentials and positions.
5. Send one eligible signal for one symbol.
6. Verify the intent, `client_order_id`, broker order, and reconciliation event.

Enable new entries only through the API:

```text
POST /api/v1/execution/kill-switch
{"enabled": false, "reason": "single-symbol paper test"}
```

Re-enable it immediately after the test:

```text
POST /api/v1/execution/kill-switch
{"enabled": true, "reason": "paper test complete"}
```

## Operational endpoints

- `POST /api/v1/execution/signals`: consume one scanner contract.
- `GET /api/v1/execution/status`: show mode, kill switch, and open intents.
- `POST /api/v1/execution/kill-switch`: block or allow new entries.
- `POST /api/v1/execution/reconcile`: perform a REST snapshot reconciliation in `paper_execution` mode.

## State and recovery

- Alpaca is the source of truth for actual orders, fills, and positions.
- `execution_intents` is the source of truth for FinPilot decision intent.
- `execution_events` is append-only audit history.
- The deterministic `client_order_id` prevents a retry from creating a second entry order.
- A timeout is recorded as `unknown`; the worker must reconcile before retrying.
- A broker order missing from the snapshot moves the local intent to `unknown` and raises an audit event.

## Go/no-go gates

Paper execution remains NO-GO when any of the following is true:

- The environment is not explicitly `paper`.
- The kill switch state cannot be read.
- The database is unavailable.
- The broker snapshot cannot be reconciled.
- An unexpected broker position exists.
- Duplicate order detection is unverified.
- Partial-fill behavior is untested.
- The strategy has not completed a locked forward shadow period.

Live trading is not implemented by this runbook. It requires a separate design review, credentials, database, service, and explicit approval.
