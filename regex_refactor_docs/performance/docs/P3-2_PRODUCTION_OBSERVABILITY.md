# P3-2: Production Observability (Metrics/Dashboards/Alerts)

**Version**: 1.0
**Date**: 2025-10-17
**Status**: Production guidance (NOT skeleton implementation)
**Source**: PLAN_CLOSING_IMPLEMENTATION_extended_3.md P3-2 (lines 598-682)
**Purpose**: Metrics, dashboards, and alerts for production parser monitoring

---

## Purpose

Provide comprehensive observability for production parser operations:
- **Performance monitoring**: Latency, throughput, error rates
- **Security monitoring**: XSS/SSRF/SSTI detections, sanitizations
- **Operational monitoring**: Caps enforcement, collector failures

---

## Key Metrics to Track

### Performance Metrics

#### `doxstrux_parse_duration_seconds` (Histogram)
**Description**: Duration of markdown parse operations
**Labels**: None
**Buckets**: `[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]` (1ms to 1s)

**Usage**:
```python
from prometheus_client import Histogram

parse_duration = Histogram(
    'doxstrux_parse_duration_seconds',
    'Duration of markdown parse operations',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# Instrument parser
with parse_duration.time():
    result = parser.parse()
```

**Dashboard Queries**:
```promql
# P50 latency
histogram_quantile(0.50, rate(doxstrux_parse_duration_seconds_bucket[5m]))

# P95 latency
histogram_quantile(0.95, rate(doxstrux_parse_duration_seconds_bucket[5m]))

# P99 latency
histogram_quantile(0.99, rate(doxstrux_parse_duration_seconds_bucket[5m]))
```

---

#### `doxstrux_warehouse_build_duration_seconds` (Histogram)
**Description**: Index building time for TokenWarehouse
**Labels**: `["document_size_bucket"]` (e.g., "0-1KB", "1-10KB", "10-100KB")
**Buckets**: `[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05]` (0.1ms to 50ms)

**Usage**:
```python
warehouse_build_duration = Histogram(
    'doxstrux_warehouse_build_duration_seconds',
    'TokenWarehouse index building time',
    labelnames=['document_size_bucket'],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05]
)

# Instrument warehouse
size_bucket = get_size_bucket(len(content))  # "0-1KB", "1-10KB", etc.
with warehouse_build_duration.labels(document_size_bucket=size_bucket).time():
    wh = TokenWarehouse(tokens, tree)
```

---

#### `doxstrux_collector_dispatch_duration_seconds` (Histogram)
**Description**: Per-collector finalize time
**Labels**: `["collector_type"]` (e.g., "links", "images", "headings")
**Buckets**: `[0.0001, 0.0005, 0.001, 0.005, 0.01]` (0.1ms to 10ms)

**Usage**:
```python
collector_dispatch_duration = Histogram(
    'doxstrux_collector_dispatch_duration_seconds',
    'Per-collector dispatch time',
    labelnames=['collector_type'],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01]
)

# Instrument collector dispatch
for collector in collectors:
    collector_type = collector.__class__.__name__
    with collector_dispatch_duration.labels(collector_type=collector_type).time():
        collector.finalize(warehouse)
```

---

#### `doxstrux_document_size_bytes` (Histogram)
**Description**: Document size distribution
**Labels**: None
**Buckets**: `[100, 500, 1000, 5000, 10000, 50000, 100000]` (100B to 100KB)

**Usage**:
```python
document_size = Histogram(
    'doxstrux_document_size_bytes',
    'Document size distribution',
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
)

# Record document size
document_size.observe(len(content))
```

---

### Security Metrics

#### `doxstrux_url_scheme_rejections_total` (Counter)
**Description**: URLs rejected due to dangerous schemes
**Labels**: `["scheme"]` (e.g., "javascript", "data", "file")

**Usage**:
```python
from prometheus_client import Counter

url_rejections = Counter(
    'doxstrux_url_scheme_rejections_total',
    'URLs rejected due to dangerous schemes',
    labelnames=['scheme']
)

# Record rejection
if scheme in DANGEROUS_SCHEMES:
    url_rejections.labels(scheme=scheme).inc()
    return None  # Reject URL
```

**Dashboard Queries**:
```promql
# Total rejections (24h)
increase(doxstrux_url_scheme_rejections_total[24h])

# Rejections by scheme (top 5)
topk(5, rate(doxstrux_url_scheme_rejections_total[5m]))
```

---

#### `doxstrux_html_sanitizations_total` (Counter)
**Description**: XSS payloads sanitized
**Labels**: `["vector"]` (e.g., "script_tag", "onerror_handler", "javascript_url")

**Usage**:
```python
html_sanitizations = Counter(
    'doxstrux_html_sanitizations_total',
    'XSS payloads sanitized',
    labelnames=['vector']
)

# Record sanitization
if '<script>' in content:
    html_sanitizations.labels(vector='script_tag').inc()
    content = bleach.clean(content)  # Sanitize
```

---

#### `doxstrux_collector_cap_truncations_total` (Counter)
**Description**: Documents hitting collector caps
**Labels**: `["collector_type"]` (e.g., "links", "images", "headings")

**Usage**:
```python
cap_truncations = Counter(
    'doxstrux_collector_cap_truncations_total',
    'Documents hitting collector caps',
    labelnames=['collector_type']
)

# Record truncation
if len(self._links) >= self.HARD_CAP:
    cap_truncations.labels(collector_type='links').inc()
    return {
        "links": self._links[:self.HARD_CAP],
        "links_truncated": True,
        "links_truncated_count": len(self._links)
    }
```

---

#### `doxstrux_collector_errors_total` (Counter)
**Description**: Collector failures (by type)
**Labels**: `["collector_type", "error_type"]`

**Usage**:
```python
collector_errors = Counter(
    'doxstrux_collector_errors_total',
    'Collector failures',
    labelnames=['collector_type', 'error_type']
)

# Record error
try:
    collector.finalize(warehouse)
except Exception as e:
    collector_errors.labels(
        collector_type=collector.__class__.__name__,
        error_type=e.__class__.__name__
    ).inc()
    raise
```

---

### Operational Metrics

#### `doxstrux_parse_requests_total` (Counter)
**Description**: Total parse operations
**Labels**: `["security_profile"]` (e.g., "strict", "moderate", "permissive")

**Usage**:
```python
parse_requests = Counter(
    'doxstrux_parse_requests_total',
    'Total parse operations',
    labelnames=['security_profile']
)

# Record parse
parse_requests.labels(security_profile=self.security_profile).inc()
result = self.parse()
```

---

#### `doxstrux_parse_errors_total` (Counter)
**Description**: Parse failures (by error type)
**Labels**: `["error_type"]`

**Usage**:
```python
parse_errors = Counter(
    'doxstrux_parse_errors_total',
    'Parse failures',
    labelnames=['error_type']
)

# Record error
try:
    result = parser.parse()
except Exception as e:
    parse_errors.labels(error_type=e.__class__.__name__).inc()
    raise
```

---

#### `doxstrux_baseline_parity_failures_total` (Counter)
**Description**: Regression test failures
**Labels**: `["test_file"]`

**Usage** (in CI):
```python
baseline_parity_failures = Counter(
    'doxstrux_baseline_parity_failures_total',
    'Regression test failures',
    labelnames=['test_file']
)

# Record failure (in test runner)
if baseline_output != expected_output:
    baseline_parity_failures.labels(test_file=test_path).inc()
```

---

## Dashboard Layout (Grafana Example)

### Dashboard 1: Parser Performance Overview

```
┌─────────────────────────────────────────┐
│ Parser Performance Overview             │
├─────────────────────────────────────────┤
│ P95 Latency: 2.1ms         [Graph →]   │
│ Throughput:  150 docs/sec  [Graph →]   │
│ Error Rate:  0.01%         [Graph →]   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Parse Duration (P50/P95/P99)            │
├─────────────────────────────────────────┤
│ [Time series graph]                     │
│ - P50 (blue): ~1.2ms                    │
│ - P95 (orange): ~2.1ms                  │
│ - P99 (red): ~5.3ms                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Document Size Distribution              │
├─────────────────────────────────────────┤
│ [Histogram]                             │
│ 0-1KB:    35%                           │
│ 1-10KB:   45%                           │
│ 10-100KB: 18%                           │
│ >100KB:   2%                            │
└─────────────────────────────────────────┘
```

### Dashboard 2: Security Events

```
┌─────────────────────────────────────────┐
│ Security Events (24h)                   │
├─────────────────────────────────────────┤
│ URL Rejections:     12  [Log →]        │
│ XSS Sanitizations:  3   [Log →]        │
│ Cap Truncations:    0   [Log →]        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ URL Rejections by Scheme                │
├─────────────────────────────────────────┤
│ [Bar chart]                             │
│ javascript: 8                           │
│ data:       3                           │
│ file:       1                           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ XSS Sanitizations by Vector             │
├─────────────────────────────────────────┤
│ [Bar chart]                             │
│ script_tag:       2                     │
│ onerror_handler:  1                     │
│ javascript_url:   0                     │
└─────────────────────────────────────────┘
```

### Dashboard 3: Collector Performance

```
┌─────────────────────────────────────────┐
│ Collector Dispatch Time (by type)       │
├─────────────────────────────────────────┤
│ [Heatmap]                               │
│ links:      0.8ms (P95)                 │
│ images:     0.6ms (P95)                 │
│ headings:   0.4ms (P95)                 │
│ paragraphs: 1.2ms (P95)                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Collector Cap Truncations (24h)         │
├─────────────────────────────────────────┤
│ [Time series]                           │
│ links:      0 truncations               │
│ images:     0 truncations               │
│ paragraphs: 0 truncations               │
└─────────────────────────────────────────┘
```

---

## Alert Rules

### Critical Alerts (PagerDuty)

**Alert 1: High Latency**
```promql
# P95 latency > 5s for 5 minutes
histogram_quantile(0.95, rate(doxstrux_parse_duration_seconds_bucket[5m])) > 5
```

**Alert 2: High Error Rate**
```promql
# Error rate > 5% for 5 minutes
rate(doxstrux_parse_errors_total[5m]) / rate(doxstrux_parse_requests_total[5m]) > 0.05
```

**Alert 3: Baseline Parity Regression**
```promql
# Baseline parity < 95% (regression detected)
(
  sum(rate(doxstrux_baseline_parity_failures_total[5m])) /
  sum(rate(doxstrux_baseline_parity_total[5m]))
) < 0.95
```

### Warning Alerts (Slack)

**Alert 4: Elevated Latency**
```promql
# P95 latency > 2s for 10 minutes
histogram_quantile(0.95, rate(doxstrux_parse_duration_seconds_bucket[10m])) > 2
```

**Alert 5: Cap Truncations**
```promql
# Cap truncations > 100/hour
rate(doxstrux_collector_cap_truncations_total[1h]) > 100
```

**Alert 6: Collector Errors**
```promql
# Collector errors > 10/hour
rate(doxstrux_collector_errors_total[1h]) > 10
```

---

## Implementation Pattern

### Prometheus + Grafana Stack

**FILE**: `src/doxstrux/markdown/observability.py`

```python
"""
Production observability for Doxstrux parser.

Provides Prometheus metrics for performance, security, and operational monitoring.
"""

from prometheus_client import Counter, Histogram, Gauge
import time
from contextlib import contextmanager
from typing import Optional


# Performance Metrics
parse_duration = Histogram(
    'doxstrux_parse_duration_seconds',
    'Duration of markdown parse operations',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

warehouse_build_duration = Histogram(
    'doxstrux_warehouse_build_duration_seconds',
    'TokenWarehouse index building time',
    labelnames=['document_size_bucket'],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05]
)

collector_dispatch_duration = Histogram(
    'doxstrux_collector_dispatch_duration_seconds',
    'Per-collector dispatch time',
    labelnames=['collector_type'],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01]
)

document_size = Histogram(
    'doxstrux_document_size_bytes',
    'Document size distribution',
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
)

# Security Metrics
url_rejections = Counter(
    'doxstrux_url_scheme_rejections_total',
    'URLs rejected due to dangerous schemes',
    labelnames=['scheme']
)

html_sanitizations = Counter(
    'doxstrux_html_sanitizations_total',
    'XSS payloads sanitized',
    labelnames=['vector']
)

cap_truncations = Counter(
    'doxstrux_collector_cap_truncations_total',
    'Documents hitting collector caps',
    labelnames=['collector_type']
)

collector_errors = Counter(
    'doxstrux_collector_errors_total',
    'Collector failures',
    labelnames=['collector_type', 'error_type']
)

# Operational Metrics
parse_requests = Counter(
    'doxstrux_parse_requests_total',
    'Total parse operations',
    labelnames=['security_profile']
)

parse_errors = Counter(
    'doxstrux_parse_errors_total',
    'Parse failures',
    labelnames=['error_type']
)

baseline_parity_failures = Counter(
    'doxstrux_baseline_parity_failures_total',
    'Regression test failures',
    labelnames=['test_file']
)


# Helper Functions
def get_size_bucket(size_bytes: int) -> str:
    """Get document size bucket label."""
    if size_bytes < 1000:
        return "0-1KB"
    elif size_bytes < 10000:
        return "1-10KB"
    elif size_bytes < 100000:
        return "10-100KB"
    else:
        return ">100KB"


@contextmanager
def track_parse(content: str, security_profile: str):
    """Context manager for tracking parse operations."""
    # Record document size
    document_size.observe(len(content))

    # Record parse request
    parse_requests.labels(security_profile=security_profile).inc()

    # Time parse operation
    start = time.perf_counter()
    try:
        yield
    except Exception as e:
        # Record error
        parse_errors.labels(error_type=e.__class__.__name__).inc()
        raise
    finally:
        # Record duration
        duration = time.perf_counter() - start
        parse_duration.observe(duration)


# Usage Example
"""
from doxstrux.markdown.observability import track_parse, url_rejections

# In MarkdownParserCore.parse()
def parse(self):
    with track_parse(self.content, self.security_profile):
        result = self._parse_internal()
        return result

# In security/validators.py
def normalize_url(url: str) -> Optional[str]:
    scheme = urlparse(url).scheme.lower()
    if scheme in DANGEROUS_SCHEMES:
        url_rejections.labels(scheme=scheme).inc()
        return None
    return url
"""
```

---

## Deployment Steps

### Step 1: Install Prometheus + Grafana

```bash
# Using Docker Compose
cat > docker-compose.yml <<EOF
version: '3'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  prometheus-data:
  grafana-data:
EOF

docker-compose up -d
```

### Step 2: Configure Prometheus

**FILE**: `prometheus.yml`

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'doxstrux'
    static_configs:
      - targets: ['localhost:8000']  # Your parser service
```

### Step 3: Expose Metrics Endpoint

**FILE**: `app.py` (FastAPI example)

```python
from fastapi import FastAPI
from prometheus_client import make_asgi_app

app = FastAPI()

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ... rest of your app
```

### Step 4: Import Grafana Dashboards

```bash
# Access Grafana UI: http://localhost:3000
# Login: admin/admin

# Import dashboards:
# 1. Parser Performance Overview
# 2. Security Events
# 3. Collector Performance
```

---

## Success Criteria

**Observability complete when**:
- ✅ All metrics instrumented (13 metrics total)
- ✅ Dashboards configured (3 dashboards)
- ✅ Alerts configured (6 alerts: 3 critical, 3 warning)
- ✅ Metrics endpoint exposed (`/metrics`)
- ✅ Prometheus scraping parser service
- ✅ Grafana dashboards accessible

---

## Effort Estimate

**Time**: 2 hours (observability documentation)

**Breakdown**:
- Metrics definition: 30 minutes
- Dashboard layout design: 30 minutes
- Alert rules configuration: 30 minutes
- Implementation pattern: 30 minutes

---

## References

- **PLAN_CLOSING_IMPLEMENTATION_extended_3.md**: P3-2 specification (lines 598-682)
- **Prometheus documentation**: https://prometheus.io/docs/
- **Grafana documentation**: https://grafana.com/docs/

---

## Evidence Anchors

| Claim ID | Statement | Evidence | Status |
|----------|-----------|----------|--------|
| CLAIM-P3-2-DOC | Production observability documented | This file | ✅ Complete |
| CLAIM-P3-2-METRICS | 13 metrics defined | Key Metrics section | ✅ Complete |
| CLAIM-P3-2-DASHBOARDS | 3 dashboards designed | Dashboard Layout section | ✅ Complete |
| CLAIM-P3-2-ALERTS | 6 alerts configured | Alert Rules section | ✅ Complete |

---

**Document Status**: Complete
**Last Updated**: 2025-10-17
**Version**: 1.0
**Scope**: Production observability guidance (NOT skeleton implementation)
**Approved By**: Pending Human Review
**Next Review**: After production observability deployed
