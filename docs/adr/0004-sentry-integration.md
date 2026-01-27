# Sentry Error Tracking Integration

* Status: Accepted
* Deciders: FinPilot Development Team
* Date: 2025-01-20

## Context

Production error visibility was limited:

1. Errors logged to files but not easily searchable
2. No aggregation of similar errors
3. No alerting for error spikes
4. Stack traces lost without proper capture
5. No correlation with user actions

## Decision

Integrate Sentry for error tracking with the following implementation:

### Components

1. **SentryClient**: Wrapper class for Sentry SDK
2. **track_errors_sentry**: Decorator for automatic error capture
3. **Breadcrumbs**: User action trail for debugging
4. **Performance Monitoring**: Transaction tracing

### Configuration

```python
from core.monitoring import sentry_client

# Initialize (reads from SENTRY_DSN env var)
sentry_client.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment="production",
    traces_sample_rate=0.1  # 10% of transactions
)

# Capture exception
try:
    risky_operation()
except Exception as e:
    sentry_client.capture_exception(e)
```

### Decorator Usage

```python
from core.monitoring import track_errors_sentry

@track_errors_sentry(reraise=True)
def scan_market(ticker: str):
    # Errors automatically captured to Sentry
    pass
```

### Context Enrichment

- User ID attached to events
- Custom tags (strategy, market, ticker)
- Breadcrumbs for action trail
- Performance transactions

## Consequences

### Positive

* **Real-time Alerts**: Slack/email notification on new errors
* **Error Aggregation**: Similar errors grouped automatically
* **Stack Traces**: Full context captured with local variables
* **Release Tracking**: Errors linked to deployments
* **Issue Assignment**: Assign errors to team members

### Negative

* **External Dependency**: Relies on Sentry service availability
* **Cost**: Paid plans required for higher volume
* **Data Privacy**: Error data sent to third party (configurable)

### Neutral

* ~10KB additional memory for SDK
* Minimal latency impact (async sending)

## Alternatives Considered

### Option 1: Self-hosted ELK Stack

Elasticsearch, Logstash, Kibana.

**Pros:**
* Full control over data
* No third-party dependency
* Unified logs and errors

**Cons:**
* High operational overhead
* Significant infrastructure cost
* Complex setup

**Verdict**: Rejected due to operational complexity

### Option 2: Rollbar

Similar error tracking service.

**Pros:**
* Good Python support
* Similar features to Sentry

**Cons:**
* Less mature ecosystem
* Smaller community
* Less integration options

**Verdict**: Rejected - Sentry has better Python support

### Option 3: Cloud Provider (AWS X-Ray, etc.)

Cloud-native error tracking.

**Pros:**
* Integrated with cloud infrastructure
* Managed service

**Cons:**
* Vendor lock-in
* Less feature-rich
* Cloud-specific

**Verdict**: Rejected due to vendor lock-in

## Implementation Details

### Graceful Degradation

If Sentry is not configured, the system continues normally:

```python
class SentryClient:
    def capture_exception(self, error):
        if not self._initialized:
            logger.debug("Sentry not configured, skipping")
            return None
        return sentry_sdk.capture_exception(error)
```

### Environment Configuration

| Env Var | Description | Default |
|---------|-------------|---------|
| SENTRY_DSN | Sentry project DSN | None |
| SENTRY_ENVIRONMENT | Environment name | development |
| SENTRY_RELEASE | Release/version tag | Auto-detected |
| SENTRY_TRACES_SAMPLE_RATE | Performance sampling | 0.1 |

### What Gets Captured

- Unhandled exceptions
- Decorated function errors
- Manual captures
- Performance transactions (sampled)

### What's Filtered

- PII (configured scrubbing)
- Passwords
- API keys
- Database queries (optional)

## Test Coverage

22 tests covering:
- Client initialization
- Exception capture
- Message capture
- Tag/context setting
- Decorator behavior
- Graceful degradation

## References

* [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
* [Sentry Best Practices](https://docs.sentry.io/product/sentry-basics/guides/)
* [ADR-0003: Prometheus Metrics](0003-prometheus-metrics.md)
