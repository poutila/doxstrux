# Production Monitoring & Metrics Guide

**Version**: 1.0
**Date**: 2025-10-16
**Status**: Production-Ready

---

## Overview

This guide documents the monitoring and metrics strategy for the TokenWarehouse Phase 8 deployment. It provides concrete metrics, alerting thresholds, and dashboards for production operation.

**Purpose**: Enable rapid detection and diagnosis of performance/security issues in production.

---

## Core Metrics

### 1. Parse Time Metrics

**Metric Name**: `doxstrux_parse_time_ms`
**Type**: Histogram
**Labels**: `document_type`, `security_profile`
**Description**: Time to parse a document (end-to-end)

**Key Percentiles**:
- **p50** (median): Typical parse time
- **p95**: 95th percentile (catches slow cases)
- **p99**: 99th percentile (catches outliers)

**Baseline Values** (from Phase 7 regression suite):
```
p50:  ~50ms  (small docs, <10KB)
p50: ~200ms  (medium docs, 10-100KB)
p50: ~500ms  (large docs, 100KB-1MB)

p95:  ~100ms (small)
p95:  ~400ms (medium)
p95: ~1000ms (large)

p99:  ~200ms (small)
p99:  ~800ms (medium)
p99: ~2000ms (large)
```

**Alert Thresholds**:
```yaml
- alert: ParseTimeP99High
  expr: histogram_quantile(0.99, doxstrux_parse_time_ms) > (baseline_p99 * 2)
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Parse time p99 is 2x baseline"
    description: "{{ $value }}ms (baseline: {{ baseline_p99 }}ms)"

- alert: ParseTimeP99Critical
  expr: histogram_quantile(0.99, doxstrux_parse_time_ms) > (baseline_p99 * 4)
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Parse time p99 is 4x baseline - likely ReDoS or hang"
```

---

### 2. Collector Timeout Metrics

**Metric Name**: `doxstrux_collector_timeouts_total`
**Type**: Counter
**Labels**: `collector_name`, `document_type`
**Description**: Total collector timeouts (indicates hanging collectors)

**Baseline**: 0 timeouts (with 2s default timeout)

**Alert Thresholds**:
```yaml
- alert: CollectorTimeoutRateHigh
  expr: rate(doxstrux_collector_timeouts_total[5m]) > 0.001  # 0.1% of requests
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Collector timeout rate > 0.1%"
    description: "Collector {{ $labels.collector_name }} timing out on {{ $labels.document_type }}"

- alert: CollectorTimeoutRateCritical
  expr: rate(doxstrux_collector_timeouts_total[5m]) > 0.01  # 1% of requests
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Collector timeout rate > 1% - possible DoS attack"
```

---

### 3. Collector Error Metrics

**Metric Name**: `doxstrux_collector_errors_total`
**Type**: Counter
**Labels**: `collector_name`, `error_type`
**Description**: Total collector errors (exceptions)

**Expected Error Types**:
- `TimeoutError`: Collector exceeded timeout (see metric #2)
- `RuntimeError`: Reentrancy guard triggered
- `MemoryError`: OOM during collection
- `Exception`: Other errors

**Alert Thresholds**:
```yaml
- alert: CollectorErrorRateHigh
  expr: rate(doxstrux_collector_errors_total{error_type!="TimeoutError"}[5m]) > 0.001
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Collector error rate > 0.1%"
    description: "Collector {{ $labels.collector_name }} erroring with {{ $labels.error_type }}"
```

---

### 4. Memory Usage Metrics

**Metric Name**: `doxstrux_parse_peak_rss_mb`
**Type**: Histogram
**Labels**: `document_type`, `document_size_bucket`
**Description**: Peak RSS memory during parse (MB)

**Baseline Values**:
```
Small docs (<10KB):   p99 < 50MB
Medium docs (10-100KB): p99 < 100MB
Large docs (100KB-1MB): p99 < 200MB
```

**Alert Thresholds**:
```yaml
- alert: ParseMemoryP99High
  expr: histogram_quantile(0.99, doxstrux_parse_peak_rss_mb{document_size_bucket="small"}) > 100
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Parse memory p99 is 2x baseline for small docs"

- alert: ParseMemoryP99Critical
  expr: histogram_quantile(0.99, doxstrux_parse_peak_rss_mb) > 500
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Parse memory p99 > 500MB - possible memory amplification attack"
```

---

### 5. Document Size Distribution

**Metric Name**: `doxstrux_document_size_bytes`
**Type**: Histogram
**Labels**: None
**Description**: Distribution of document sizes processed

**Purpose**: Detect unusual traffic patterns (e.g., sudden spike in large docs)

**Alert Thresholds**:
```yaml
- alert: LargeDocumentSpike
  expr: rate(doxstrux_document_size_bytes_bucket{le="1000000"}[5m]) > (baseline_rate * 3)
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "3x increase in large document processing"
    description: "Possible DoS attempt via large documents"
```

---

### 6. Security Validation Failures

**Metric Name**: `doxstrux_security_validation_failures_total`
**Type**: Counter
**Labels**: `validation_type`, `security_profile`
**Description**: Documents rejected by security validation

**Validation Types**:
- `size_limit`: Document too large
- `line_count`: Too many lines
- `nesting_depth`: Nesting too deep
- `token_count`: Too many tokens
- `template_syntax`: Template injection detected
- `prompt_injection`: Prompt injection pattern detected

**Alert Thresholds**:
```yaml
- alert: SecurityValidationFailureSpike
  expr: rate(doxstrux_security_validation_failures_total[5m]) > 0.01  # 1% of requests
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Security validation failure rate > 1%"
    description: "Validation {{ $labels.validation_type }} failing on {{ $labels.security_profile }} profile"
```

---

## Instrumentation Code

### Python Metrics (Prometheus)

```python
from prometheus_client import Counter, Histogram
import time
import tracemalloc

# Define metrics
parse_time_ms = Histogram(
    'doxstrux_parse_time_ms',
    'Parse time in milliseconds',
    ['document_type', 'security_profile'],
    buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
)

collector_timeouts = Counter(
    'doxstrux_collector_timeouts_total',
    'Total collector timeouts',
    ['collector_name', 'document_type']
)

collector_errors = Counter(
    'doxstrux_collector_errors_total',
    'Total collector errors',
    ['collector_name', 'error_type']
)

parse_peak_rss_mb = Histogram(
    'doxstrux_parse_peak_rss_mb',
    'Peak RSS memory during parse (MB)',
    ['document_type', 'document_size_bucket'],
    buckets=[10, 25, 50, 100, 200, 500, 1000]
)

document_size_bytes = Histogram(
    'doxstrux_document_size_bytes',
    'Document size in bytes',
    buckets=[1000, 10000, 100000, 1000000, 10000000]
)

security_validation_failures = Counter(
    'doxstrux_security_validation_failures_total',
    'Security validation failures',
    ['validation_type', 'security_profile']
)


# Instrumentation wrapper
def parse_with_metrics(content: str, document_type: str = "markdown", security_profile: str = "moderate"):
    """Parse document with metrics collection."""
    start_time = time.time()
    tracemalloc.start()

    try:
        # Record document size
        document_size_bytes.observe(len(content))

        # Parse document
        from doxstrux.markdown_parser_core import MarkdownParserCore
        parser = MarkdownParserCore(content, security_profile=security_profile)
        result = parser.parse()

        # Record parse time
        duration_ms = (time.time() - start_time) * 1000
        parse_time_ms.labels(
            document_type=document_type,
            security_profile=security_profile
        ).observe(duration_ms)

        # Record peak memory
        current, peak = tracemalloc.get_traced_memory()
        peak_mb = peak / (1024 * 1024)
        size_bucket = get_size_bucket(len(content))
        parse_peak_rss_mb.labels(
            document_type=document_type,
            document_size_bucket=size_bucket
        ).observe(peak_mb)

        tracemalloc.stop()

        return result

    except Exception as e:
        tracemalloc.stop()

        # Record security validation failures
        if "too large" in str(e).lower() or "exceeds" in str(e).lower():
            security_validation_failures.labels(
                validation_type="size_limit",
                security_profile=security_profile
            ).inc()

        raise


def get_size_bucket(size_bytes: int) -> str:
    """Classify document size into bucket."""
    if size_bytes < 10000:
        return "small"
    elif size_bytes < 100000:
        return "medium"
    else:
        return "large"
```

---

## Grafana Dashboard

### Dashboard JSON Template

```json
{
  "dashboard": {
    "title": "Doxstrux TokenWarehouse Production Metrics",
    "panels": [
      {
        "title": "Parse Time (p50/p95/p99)",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(doxstrux_parse_time_ms_bucket[5m]))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(doxstrux_parse_time_ms_bucket[5m]))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(doxstrux_parse_time_ms_bucket[5m]))",
            "legendFormat": "p99"
          }
        ]
      },
      {
        "title": "Collector Timeout Rate (per second)",
        "targets": [
          {
            "expr": "rate(doxstrux_collector_timeouts_total[5m])",
            "legendFormat": "{{ collector_name }}"
          }
        ]
      },
      {
        "title": "Collector Error Rate (per second)",
        "targets": [
          {
            "expr": "rate(doxstrux_collector_errors_total[5m])",
            "legendFormat": "{{ collector_name }} - {{ error_type }}"
          }
        ]
      },
      {
        "title": "Memory Usage (p99)",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, rate(doxstrux_parse_peak_rss_mb_bucket[5m]))",
            "legendFormat": "{{ document_size_bucket }}"
          }
        ]
      },
      {
        "title": "Security Validation Failure Rate",
        "targets": [
          {
            "expr": "rate(doxstrux_security_validation_failures_total[5m])",
            "legendFormat": "{{ validation_type }}"
          }
        ]
      }
    ]
  }
}
```

---

## Log-Based Monitoring

### Structured Logging Format

```python
import logging
import json

logger = logging.getLogger("doxstrux")

def log_parse_event(
    event_type: str,
    document_size: int,
    parse_time_ms: float,
    collector_errors: list = None,
    **kwargs
):
    """Log structured parse event."""
    log_entry = {
        "event_type": event_type,
        "timestamp": time.time(),
        "document_size": document_size,
        "parse_time_ms": parse_time_ms,
        "collector_errors": collector_errors or [],
        **kwargs
    }

    logger.info(json.dumps(log_entry))


# Example usage
log_parse_event(
    event_type="parse_complete",
    document_size=len(content),
    parse_time_ms=duration_ms,
    collector_errors=[
        {"collector": "html", "error": "TimeoutError"}
    ]
)
```

### Log Queries (Splunk/ELK)

**Query 1: Find documents with collector timeouts**
```
event_type="parse_complete" AND collector_errors{}.error="TimeoutError"
| stats count by collector_errors{}.collector
```

**Query 2: Find slow parses (p99 outliers)**
```
event_type="parse_complete" AND parse_time_ms > 2000
| sort -parse_time_ms
| head 100
```

**Query 3: Memory usage spike detection**
```
event_type="parse_complete"
| timechart avg(peak_rss_mb) as avg_mem, perc99(peak_rss_mb) as p99_mem
| where p99_mem > 500
```

---

## Alerting Strategy

### Alert Severity Levels

**Critical (P0)**: Immediate response required
- Parse time p99 > 4x baseline (likely DoS/ReDoS)
- Collector timeout rate > 1% (DoS attack)
- Memory usage > 500MB p99 (memory amplification)

**Warning (P1)**: Investigate within 1 hour
- Parse time p99 > 2x baseline
- Collector timeout rate > 0.1%
- Security validation failure rate > 1%

**Info (P2)**: Review during business hours
- Parse time p95 > 1.5x baseline
- Any collector errors (non-timeout)

### Alert Response Playbook

**Alert**: `ParseTimeP99Critical`

**Steps**:
1. Check Grafana dashboard - which document types are slow?
2. Check logs for recent slow parses (query 2 above)
3. Identify pattern - specific document type, size, or content?
4. If ReDoS suspected:
   - Enable rate limiting for large documents
   - Consider emergency rollback
5. Investigate collector performance (check timeout metrics)

**Alert**: `CollectorTimeoutRateCritical`

**Steps**:
1. Identify which collector is timing out (check metrics label)
2. Check logs for timeout patterns (query 1 above)
3. If widespread:
   - Possible DoS attack - enable rate limiting
   - Consider reducing `COLLECTOR_TIMEOUT_SECONDS` to fail faster
4. If isolated to one collector:
   - Disable collector temporarily
   - Investigate collector implementation

---

## Performance Regression Detection

### Baseline Comparison Script

```python
#!/usr/bin/env python3
"""
Compare current metrics against baseline.

Usage:
    python tools/check_performance_regression.py \
        --baseline tools/baseline_metrics.json \
        --current /path/to/prometheus/metrics
"""
import json
import sys
from pathlib import Path


def load_baseline(baseline_path: Path) -> dict:
    """Load baseline metrics."""
    return json.loads(baseline_path.read_text())


def query_current_metrics() -> dict:
    """Query current metrics from Prometheus."""
    # TODO: Implement Prometheus query
    # Example:
    # import requests
    # response = requests.get("http://prometheus:9090/api/v1/query", params={
    #     "query": "histogram_quantile(0.99, doxstrux_parse_time_ms_bucket)"
    # })
    # return response.json()
    pass


def compare_metrics(baseline: dict, current: dict) -> list:
    """Compare current metrics against baseline."""
    issues = []

    # Check parse time p99
    for doc_type in ["small", "medium", "large"]:
        baseline_p99 = baseline["parse_time_ms"][doc_type]["p99"]
        current_p99 = current["parse_time_ms"][doc_type]["p99"]

        if current_p99 > baseline_p99 * 1.5:
            issues.append({
                "metric": "parse_time_ms",
                "doc_type": doc_type,
                "baseline": baseline_p99,
                "current": current_p99,
                "ratio": current_p99 / baseline_p99,
                "severity": "warning" if current_p99 < baseline_p99 * 2 else "critical"
            })

    return issues


def main():
    baseline = load_baseline(Path("tools/baseline_metrics.json"))
    current = query_current_metrics()
    issues = compare_metrics(baseline, current)

    if issues:
        print("Performance regressions detected:")
        for issue in issues:
            print(f"  [{issue['severity']}] {issue['metric']} ({issue['doc_type']}): "
                  f"{issue['current']}ms vs {issue['baseline']}ms baseline "
                  f"({issue['ratio']:.2f}x)")
        sys.exit(1)
    else:
        print("No performance regressions detected")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

---

## Load Testing

### Load Test Configuration

```yaml
# locust_config.py
from locust import HttpUser, task, between

class DoxstruxUser(HttpUser):
    wait_time = between(1, 5)

    @task(10)  # 10x weight - small docs are most common
    def parse_small_document(self):
        with open("test_corpus/small_doc.md", "r") as f:
            content = f.read()

        self.client.post("/parse", json={
            "content": content,
            "security_profile": "moderate"
        })

    @task(5)  # 5x weight
    def parse_medium_document(self):
        with open("test_corpus/medium_doc.md", "r") as f:
            content = f.read()

        self.client.post("/parse", json={
            "content": content,
            "security_profile": "moderate"
        })

    @task(1)  # 1x weight - large docs are rare
    def parse_large_document(self):
        with open("test_corpus/large_doc.md", "r") as f:
            content = f.read()

        self.client.post("/parse", json={
            "content": content,
            "security_profile": "strict"
        })


# Run load test:
# locust -f locust_config.py --host=https://api.example.com --users=100 --spawn-rate=10
```

---

## Capacity Planning

### Resource Estimates

**Small Document** (<10KB):
- Parse time: ~50ms (p50)
- Memory: ~20MB (p50)
- CPU: ~10% of 1 core (0.1 vCPU)

**Medium Document** (10-100KB):
- Parse time: ~200ms (p50)
- Memory: ~50MB (p50)
- CPU: ~40% of 1 core (0.4 vCPU)

**Large Document** (100KB-1MB):
- Parse time: ~500ms (p50)
- Memory: ~100MB (p50)
- CPU: ~80% of 1 core (0.8 vCPU)

### Scaling Targets

**Baseline**: 1000 requests/second (small docs)

**Capacity**:
- **Small docs** (70% of traffic): 1000 req/s = 50 vCPU, 20GB RAM
- **Medium docs** (25% of traffic): 250 req/s = 100 vCPU, 12GB RAM
- **Large docs** (5% of traffic): 50 req/s = 40 vCPU, 5GB RAM

**Total**: ~200 vCPU, 40GB RAM for 1000 req/s

**Auto-scaling trigger**:
- Scale up: CPU > 70% for 2 minutes
- Scale down: CPU < 30% for 10 minutes

---

## Next Steps

1. **Implement metrics collection** in production code
2. **Deploy Prometheus** and configure scraping
3. **Create Grafana dashboard** from template
4. **Set up alerts** in PagerDuty/OpsGenie
5. **Run load tests** to establish baseline
6. **Document runbooks** for each alert

---

**Last Updated**: 2025-10-16
**Owner**: Platform Team
**Review Frequency**: Quarterly
