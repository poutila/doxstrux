# Cross-Platform Support Policy - Collector Timeout Enforcement

**Version**: 1.0
**Date**: 2025-10-17
**Status**: POLICY - EXPLICIT DEPLOYMENT GUIDANCE
**Scope**: All deployments of doxstrux markdown parser with collector timeout enforcement
**Source**: PLAN_CLOSING_IMPLEMENTATION.md P0-4 + External Security Analysis

---

## Executive Summary

**CRITICAL DEPLOYMENT DECISION**: Collector timeout enforcement (via SIGALRM) is **Unix-only** (Linux/macOS). Windows deployments have **limited timeout enforcement** unless subprocess isolation is implemented.

**Security Implication**: Without timeout enforcement, slow/malicious collectors can cause Denial of Service (DoS) by blocking parser indefinitely.

**Recommendation**:
- **Production deployments with untrusted inputs**: Use Linux/macOS (full timeout enforcement)
- **Trusted input deployments**: Windows acceptable with graceful degradation
- **Windows with untrusted inputs**: Requires subprocess isolation (YAGNI gate - see below)

---

## Platform Support Matrix

| Platform | Timeout Enforcement | SIGALRM Available | Production Ready (Untrusted Input) | Notes |
|----------|---------------------|-------------------|-------------------------------------|-------|
| **Linux** | ✅ Full | ✅ Yes | ✅ **Recommended** | SIGALRM-based timeout works natively |
| **macOS** | ✅ Full | ✅ Yes | ✅ **Recommended** | SIGALRM-based timeout works natively |
| **Windows** | ⚠️ Limited | ❌ No | ❌ **Not Recommended** | Graceful degradation (warning only) |
| **Windows + Subprocess Isolation** | ✅ Full | N/A | ⏳ **Pending YAGNI** | Requires implementation (8h effort) |

---

## Technical Background: SIGALRM Limitation

### Why Unix-Only?

**SIGALRM** (signal alarm) is a Unix signal mechanism for timeout enforcement:

```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Collector exceeded timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(2)  # Set 2-second timeout

try:
    slow_function()  # If this takes >2s, TimeoutError raised
    signal.alarm(0)  # Cancel alarm if completed
except TimeoutError:
    print("Function timed out")
```

**Problem**: Windows does not support SIGALRM. Calling `signal.alarm()` on Windows raises `AttributeError`.

---

### Current Implementation Behavior

**File**: `skeleton/doxstrux/markdown/utils/token_warehouse.py`

**Unix (Linux/macOS)**:
```python
PLATFORM = platform.system()
SUPPORTS_TIMEOUT = (PLATFORM in ['Linux', 'Darwin'])

if SUPPORTS_TIMEOUT:
    # SIGALRM-based timeout enforced
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    result = collector.finalize(warehouse)
    signal.alarm(0)  # Cancel alarm
```

**Windows**:
```python
if not SUPPORTS_TIMEOUT:
    # Graceful degradation: Warning only
    logger.warning(
        f"Collector timeout not enforced on {PLATFORM}. "
        "Set STRICT_TIMEOUT_ENFORCEMENT=true for subprocess isolation."
    )
    result = collector.finalize(warehouse)  # No timeout enforcement
```

**Result**: Windows deployments log warnings but do NOT kill slow collectors.

---

## Windows Deployment Options

### Option 1: Graceful Degradation (Default) ⚠️

**Configuration**:
```bash
# No environment variable needed - this is the default
# OR explicitly:
export STRICT_TIMEOUT_ENFORCEMENT=false
```

**Behavior**:
- Timeout warnings logged but NOT enforced
- Slow collectors run to completion (no kill)
- **Risk**: DoS if malicious/buggy collector blocks indefinitely

**Use Cases**:
- ✅ Development/testing on Windows
- ✅ Trusted input only (internal documents)
- ✅ Low-risk environments (non-production)
- ❌ Production with untrusted input

**Deployment Guidance**: Acceptable for non-production or trusted-input-only deployments.

---

### Option 2: Subprocess Isolation (Strict) ✅ **YAGNI GATED**

**Configuration**:
```bash
export STRICT_TIMEOUT_ENFORCEMENT=true
```

**Behavior**:
- Collectors run in isolated subprocess
- Timeout enforced via subprocess termination
- **Risk**: None (full timeout enforcement)

**Implementation Status**: ❌ **NOT IMPLEMENTED** (YAGNI gate - requires Windows deployment confirmation)

**YAGNI Requirements** (per CODE_QUALITY.json):
- Q1: Real requirement? → **Requires Windows production deployment ticket**
- Q2: Used immediately? → **Requires deployment timeline confirmation**
- Q3: Backed by data? → **Requires Windows user count or stakeholder approval**

**If Requirements Met**:
1. Create ticket: "Windows Production Deployment - Subprocess Isolation Required"
2. Get Tech Lead approval (waiver_policy)
3. Implement `tools/collector_worker.py` (8h effort)
4. Add tests: `test_subprocess_isolation_windows.py`

**Current Status**: Raises `NotImplementedError` if `STRICT_TIMEOUT_ENFORCEMENT=true` on Windows.

---

### Option 3: Linux-Only Deployment (Recommended) ✅

**Configuration**: Deploy only on Linux/macOS servers

**Behavior**:
- Full SIGALRM timeout enforcement
- No platform-specific workarounds needed
- **Risk**: None

**Use Cases**:
- ✅ Production deployments (untrusted input)
- ✅ Cloud deployments (Linux containers)
- ✅ Docker/Kubernetes (Linux-based)

**Deployment Guidance**: **Recommended for all production deployments with untrusted input.**

---

## Deployment Decision Tree

```
START: Do you need to deploy on Windows?
  ↓
  NO → Use Linux/macOS (Option 3) → ✅ DONE
  ↓
  YES → Is input from untrusted sources?
    ↓
    NO → Use graceful degradation (Option 1) → ✅ DONE
    ↓
    YES → Do you have Windows deployment ticket + Tech Lead approval?
      ↓
      NO → STOP: Document Linux-only requirement, deploy on Linux (Option 3)
      ↓
      YES → Implement subprocess isolation (Option 2) → ✅ DONE (8h effort)
```

---

## Configuration Reference

### Environment Variables

| Variable | Values | Default | Purpose |
|----------|--------|---------|---------|
| `COLLECTOR_TIMEOUT_SECONDS` | Integer (1-300) | `2` | Timeout per collector (seconds) |
| `STRICT_TIMEOUT_ENFORCEMENT` | `true`, `false` | `false` | Enforce timeout on Windows via subprocess |

**Example Configuration**:

**Linux/macOS (default)**:
```bash
# No configuration needed - SIGALRM works automatically
# Optional: Adjust timeout
export COLLECTOR_TIMEOUT_SECONDS=5
```

**Windows (graceful degradation)**:
```bash
# Default behavior - warnings only
export STRICT_TIMEOUT_ENFORCEMENT=false
```

**Windows (strict enforcement - NOT YET IMPLEMENTED)**:
```bash
# Raises NotImplementedError until subprocess isolation implemented
export STRICT_TIMEOUT_ENFORCEMENT=true
```

---

## Testing Guidance

### Platform-Aware Tests

**File**: `skeleton/tests/test_collector_timeout.py`

**Unix-Only Tests**:
```python
import platform
import pytest

PLATFORM = platform.system()
SUPPORTS_TIMEOUT = (PLATFORM in ['Linux', 'Darwin'])

@pytest.mark.skipif(not SUPPORTS_TIMEOUT, reason="Timeout not supported on Windows")
def test_collector_timeout_enforced():
    """Verify timeout kills slow collector (Unix only)."""
    # Test SIGALRM-based timeout
    # Expected: Collector killed after 2 seconds
    pass
```

**Windows-Only Tests**:
```python
@pytest.mark.skipif(SUPPORTS_TIMEOUT, reason="Test only for Windows graceful degradation")
def test_windows_timeout_warning():
    """Verify Windows logs warning instead of enforcing timeout."""
    import logging
    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse

    # Setup slow collector
    # Expected: Warning logged, collector runs to completion
    with pytest.warns(UserWarning, match="Collector timeout not enforced"):
        result = wh.dispatch_all()
```

---

### Running Tests by Platform

**Linux/macOS**:
```bash
# All tests run (including timeout enforcement tests)
.venv/bin/python -m pytest skeleton/tests/test_collector_timeout.py -v
```

**Windows**:
```bash
# Timeout enforcement tests skipped automatically
.venv/bin/python -m pytest skeleton/tests/test_collector_timeout.py -v
# Expected output: "SKIPPED: Timeout not supported on Windows"
```

---

## README Documentation

**Update README.md** to document platform support:

```markdown
## Platform Support

### Supported Platforms

- **Linux**: Full support (recommended for production)
- **macOS**: Full support (recommended for production)
- **Windows**: Limited support (development/testing only)

### Platform-Specific Limitations

**Windows Limitation**: Collector timeout enforcement uses SIGALRM, which is Unix-only. On Windows:
- Timeouts log warnings but are NOT enforced
- Suitable for development/testing or trusted input only
- **NOT recommended for production with untrusted input**

**Production Deployment**: Use Linux or macOS for deployments processing untrusted markdown input.

### Configuration

**Adjust timeout duration**:
```bash
export COLLECTOR_TIMEOUT_SECONDS=5  # Default: 2 seconds
```

**Enable strict enforcement on Windows** (requires subprocess isolation):
```bash
export STRICT_TIMEOUT_ENFORCEMENT=true
# NOTE: Raises NotImplementedError until subprocess isolation implemented
```

See `skeleton/policies/EXEC_PLATFORM_SUPPORT_POLICY.md` for detailed guidance.
```

---

## Subprocess Isolation Implementation (YAGNI Gated)

### Current Status: NOT IMPLEMENTED

**File**: `tools/collector_worker.py` (skeleton placeholder)

```python
"""
Subprocess-based collector isolation for cross-platform timeout enforcement.

YAGNI STATUS: NOT IMPLEMENTED
BLOCKED BY: No Windows deployment requirement (CODE_QUALITY.json Q1 fails)

When to implement:
1. User confirms Windows production deployment (Q1: Real requirement ✅)
2. User has immediate Windows deployment plan (Q2: Used immediately ✅)
3. Concrete Windows user count/ticket (Q3: Backed by data ✅)

Effort: 8 hours (design + implementation + testing)
"""

def run_collector_isolated(collector, warehouse_state, timeout_seconds):
    """
    Run collector in subprocess with timeout.

    THIS IS A PLACEHOLDER. Do not implement without YAGNI waiver.
    """
    raise NotImplementedError("Subprocess isolation pending YAGNI waiver")
```

### Implementation Checklist (If YAGNI Gate Passes)

**Required Steps**:
1. [ ] Create ticket: "Windows Production Deployment - Subprocess Isolation Required"
2. [ ] Get Tech Lead approval (waiver_policy)
3. [ ] Implement subprocess isolation:
   - Serialize warehouse state
   - Run collector in subprocess with timeout
   - Deserialize results
4. [ ] Add tests: `test_subprocess_isolation_windows.py`
5. [ ] Test on Windows platform
6. [ ] Update this policy document with implementation details

**Estimated Effort**: 8 hours

---

## Monitoring & Alerts

### Production Metrics

**Linux/macOS Deployments**:
```yaml
metrics:
  - name: collector_timeout_total
    type: counter
    labels: [collector_name, platform]
    description: "Number of collectors killed due to timeout"

  - name: collector_duration_seconds
    type: histogram
    labels: [collector_name, platform]
    description: "Collector execution duration"
```

**Grafana Alerts**:
```yaml
alerts:
  - alert: CollectorTimeoutSpike
    expr: rate(collector_timeout_total[1m]) > 0.01
    for: 1m
    labels:
      severity: P0
    annotations:
      summary: "Collector timeout rate > 1% for 1 minute"

  - alert: WindowsTimeoutWarningSpike
    expr: rate(windows_timeout_warning_total[5m]) > 10
    for: 5m
    labels:
      severity: P1
    annotations:
      summary: "Windows timeout warnings increasing (may indicate slow collectors)"
```

**Windows Deployments**:
```yaml
metrics:
  - name: windows_timeout_warning_total
    type: counter
    labels: [collector_name]
    description: "Number of timeout warnings on Windows (not enforced)"
```

---

## Security Implications

### Linux/macOS (Full Enforcement) ✅

**Threat Model**:
- ✅ Malicious collector blocked by timeout
- ✅ Buggy collector (infinite loop) killed
- ✅ Resource exhaustion prevented

**Risk Level**: ✅ **Low** - Full timeout protection

---

### Windows (Graceful Degradation) ⚠️

**Threat Model**:
- ⚠️ Malicious collector NOT blocked by timeout
- ⚠️ Buggy collector (infinite loop) NOT killed
- ⚠️ Resource exhaustion possible

**Risk Level**: ⚠️ **Medium** - DoS risk on untrusted input

**Mitigation**:
- Use only for trusted input
- Document "Linux-only for production" requirement
- Monitor `windows_timeout_warning_total` metric

---

## References

- **PLAN_CLOSING_IMPLEMENTATION.md**: P0-4 specification (lines 889-973)
- **External Security Analysis**: Platform support requirements (Section B.1)
- **CODE_QUALITY.json**: YAGNI enforcement rules
- **skeleton/tests/test_collector_timeout.py**: Platform-aware timeout tests

---

## Evidence Anchors

| Claim ID | Statement | Evidence | Status |
|----------|-----------|----------|--------|
| CLAIM-PLATFORM-POLICY | Platform support documented | This document | ✅ Complete |
| CLAIM-SIGALRM-UNIX | SIGALRM is Unix-only | Technical background section | ✅ Documented |
| CLAIM-WINDOWS-GRACEFUL | Windows graceful degradation implemented | token_warehouse.py code | ✅ Verified |
| CLAIM-YAGNI-GATE | Subprocess isolation YAGNI gated | YAGNI section + CODE_QUALITY.json | ✅ Enforced |

---

## Decision Log

| Date | Decision | Rationale | Approved By |
|------|----------|-----------|-------------|
| 2025-10-17 | Linux/macOS recommended for production | SIGALRM Unix-only limitation | Security Team |
| 2025-10-17 | Windows graceful degradation acceptable for trusted input | KISS principle, no over-engineering | Platform Team |
| 2025-10-17 | Subprocess isolation YAGNI gated | No confirmed Windows deployment requirement | Tech Lead |

---

**Document Status**: Complete
**Last Updated**: 2025-10-17
**Version**: 1.0
**Next Review**: When Windows production deployment is confirmed
