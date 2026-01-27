# Prometheus Metrics Integration

* Status: Accepted
* Deciders: FinPilot Development Team
* Date: 2025-01-20

## Context

As FinPilot moves toward production deployment, we need:

1. **Visibility**: Understanding system behavior in real-time
2. **Alerting**: Automated notification when issues occur
3. **Capacity Planning**: Data for scaling decisions
4. **SLO Tracking**: Measuring reliability commitments

The team evaluated several monitoring solutions.

## Decision

Integrate Prometheus metrics with the following architecture:

### Components

1. **PrometheusExporter**: Converts internal metrics to Prometheus format
2. **MetricsServer**: HTTP server exposing `/metrics` endpoint
3. **MetricsRegistry**: Centralized metric storage (existing)
4. **Grafana Dashboards**: Visualization layer

### Metrics Categories

| Category | Metrics |
|----------|---------|
| Business | scans_total, signals_generated, match_rate |
| Performance | scan_duration_p50/p95/p99, api_latency |
| Resources | active_connections, memory_usage |
| Errors | error_rate, failed_scans |

### Endpoints

- `/metrics` - Prometheus scrape endpoint
- `/health` - Liveness check
- `/ready` - Readiness check

### Implementation

```python
from core.prometheus_exporter import start_metrics_server

# Start metrics server on port 8000
start_metrics_server(port=8000)

# Access: http://localhost:8000/metrics
```

## Consequences

### Positive

* **Industry Standard**: Prometheus is the de-facto standard for cloud-native monitoring
* **Query Language**: PromQL enables complex queries and aggregations
* **Ecosystem**: Rich ecosystem of exporters, dashboards, alerting
* **Pull Model**: Prometheus scrapes metrics, simplifying firewall config
* **Efficient**: Minimal overhead per metric

### Negative

* **Additional Service**: Requires running Prometheus server
* **Storage**: Metrics data grows over time (configured retention)
* **Learning Curve**: PromQL has a learning curve

### Neutral

* Metrics endpoint adds ~1MB memory overhead
* Prometheus scrape interval (15s default)

## Metrics Format

```text
# HELP finpilot_scans_total Total number of market scans executed
# TYPE finpilot_scans_total counter
finpilot_scans_total{strategy="momentum"} 142
finpilot_scans_total{strategy="swing"} 89

# HELP finpilot_scan_duration_seconds Scan duration histogram
# TYPE finpilot_scan_duration_seconds histogram
finpilot_scan_duration_seconds_bucket{le="0.1"} 15
finpilot_scan_duration_seconds_bucket{le="0.5"} 120
finpilot_scan_duration_seconds_bucket{le="1.0"} 180
finpilot_scan_duration_seconds_bucket{le="+Inf"} 200
finpilot_scan_duration_seconds_sum 95.7
finpilot_scan_duration_seconds_count 200
```

## Alternatives Considered

### Option 1: StatsD

UDP-based metrics collection.

**Pros:**
* Simple protocol
* Low overhead
* Fire-and-forget

**Cons:**
* Requires aggregation server (Graphite, Datadog)
* UDP can lose data
* Less rich ecosystem

**Verdict**: Rejected due to data loss risk and ecosystem

### Option 2: OpenTelemetry

Vendor-neutral observability framework.

**Pros:**
* Unified traces, metrics, logs
* Vendor-neutral
* Growing adoption

**Cons:**
* More complex setup
* Still maturing
* Heavier dependency

**Verdict**: Deferred - may migrate later for unified observability

### Option 3: Cloud Provider Native

AWS CloudWatch, GCP Stackdriver, Azure Monitor.

**Pros:**
* No additional infrastructure
* Integrated with cloud services
* Managed service

**Cons:**
* Vendor lock-in
* Cost at scale
* Less flexible queries

**Verdict**: Rejected due to vendor lock-in

## Grafana Dashboard

Created dashboard at `monitoring/grafana/dashboards/finpilot-dashboard.json`:

- **System Overview**: Health status, scan counts, signal counts
- **Scanner Metrics**: Scan rate, duration percentiles
- **ML/DRL Metrics**: Training progress, inference time
- **Auth & Security**: Auth attempts, rate limit activity

## References

* [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
* [Four Golden Signals](https://sre.google/sre-book/monitoring-distributed-systems/)
* [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
* [ADR-0004: Sentry Integration](0004-sentry-integration.md)
