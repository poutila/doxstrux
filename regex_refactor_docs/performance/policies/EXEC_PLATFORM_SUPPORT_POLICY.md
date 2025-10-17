# Platform Support Policy

**Version**: 1.0
**Date**: 2025-10-16
**Source**: CLOSING_IMPLEMENTATION.md lines 795-1065

---

## Collector Timeout Enforcement

### Supported Platforms (Full Enforcement) ✅

**Linux** (SIGALRM-based):
- Timeout enforcement: ENABLED
- Mechanism: SIGALRM signal (Unix standard)
- Default timeout: 2 seconds (configurable)
- Status: ✅ FULLY SUPPORTED

**macOS** (SIGALRM-based):
- Timeout enforcement: ENABLED
- Mechanism: SIGALRM signal (Unix standard)
- Default timeout: 2 seconds (configurable)
- Status: ✅ FULLY SUPPORTED

### Limited Support (Graceful Degradation) ⚠️

**Windows**:
- Timeout enforcement: DISABLED (graceful degradation)
- Mechanism: Warning logged, no enforcement
- Risk: Slow/malicious collectors can cause DoS
- Status: ⚠️ LIMITED SUPPORT (graceful degradation only)

**Root Cause**: Windows has no SIGALRM equivalent signal.

---

## Windows Deployment Options

### Option 1: Graceful Degradation (Default) ⚠️

**Configuration**:
```bash
# Default behavior
STRICT_TIMEOUT_ENFORCEMENT=false
```

**Behavior**:
- Timeout warnings logged but NOT enforced
- Collectors run to completion (no time limit)
- Suitable for **trusted collector code only**

**Use Case**: Development/testing environments with known-good collectors

**Risk**: Slow collectors can cause DoS on Windows deployments

**Example Log**:
```
WARNING: Collector timeout not enforced on Windows.
Set STRICT_TIMEOUT_ENFORCEMENT=true for subprocess isolation.
```

---

### Option 2: Subprocess Isolation (Strict Mode) 🚧

**Configuration**:
```bash
# Strict enforcement (requires implementation)
STRICT_TIMEOUT_ENFORCEMENT=true
```

**Status**: 🚧 **NOT IMPLEMENTED** (pending YAGNI waiver)

**Behavior**: Raises `NotImplementedError` until implemented

**YAGNI Waiver Required**:
Per CODE_QUALITY.json, subprocess isolation requires:
- [ ] Ticket ID documenting Windows deployment requirement
- [ ] Tech Lead approval
- [ ] Concrete data (user count, deployment plan)

**Current Decision**: DEFERRED until Windows production deployment confirmed

**Effort Estimate**: 8 hours (design + implementation + testing)

---

### Option 3: Linux-Only Deployment (Recommended) ✅

**Policy**: Deploy on Linux for production, Windows for dev/test only

**Advantages**:
- ✅ Full timeout enforcement (SIGALRM)
- ✅ No over-engineering (KISS principle)
- ✅ Industry standard (most production deployments are Linux)

**Disadvantages**:
- ❌ Limits deployment flexibility (no Windows production)

**Recommendation**: Use this option until Windows production requirement confirmed.

---

## Platform Detection

### Runtime Detection (Automatic)

The system automatically detects the platform at runtime:

```python
import platform

PLATFORM = platform.system()  # 'Linux', 'Darwin', 'Windows'
SUPPORTS_SIGALRM = (PLATFORM in ['Linux', 'Darwin'])
SUPPORTS_TIMEOUT = SUPPORTS_SIGALRM
```

### Configuration Variables

**Environment Variables**:
- `COLLECTOR_TIMEOUT_SECONDS`: Timeout duration (default: 2)
- `STRICT_TIMEOUT_ENFORCEMENT`: Strict mode on Windows (default: false)

**Examples**:
```bash
# Unix: Use 5-second timeout
export COLLECTOR_TIMEOUT_SECONDS=5
.venv/bin/python -m pytest skeleton/tests/

# Windows: Enable strict mode (raises NotImplementedError)
set STRICT_TIMEOUT_ENFORCEMENT=true
.venv\bin\python -m pytest skeleton\tests\
```

---

## Testing

### Unix (Linux/macOS)

```bash
# All timeout tests should pass
.venv/bin/python -m pytest \
  regex_refactor_docs/performance/skeleton/tests/test_collector_timeout.py -v
```

**Expected Output**:
```
test_collector_timeout_unix_sigalrm PASSED
test_collector_timeout_error_isolation PASSED
test_collector_timeout_configurable PASSED

3 passed in 0.X seconds
```

### Windows

```bash
# Timeout tests skip or warn (graceful degradation)
set STRICT_TIMEOUT_ENFORCEMENT=false
.venv\bin\python -m pytest ^
  regex_refactor_docs\performance\skeleton\tests\test_collector_timeout.py -v
```

**Expected Behavior**:
- Tests skip with message: "Timeout not supported on Windows"
- OR warnings logged: "Collector timeout not enforced on Windows"

---

## Security Implications

### Unix Deployments (Full Protection) ✅

**Threat Model**: Malicious/slow collector attempts DoS
- **Protection**: SIGALRM kills collector after 2 seconds
- **Result**: Attack BLOCKED
- **CVSS Impact**: None (DoS prevented)

### Windows Deployments (Limited Protection) ⚠️

**Option 1: Graceful Degradation (Default)**
- **Threat Model**: Malicious/slow collector attempts DoS
- **Protection**: None (warning only)
- **Result**: Attack SUCCEEDS (DoS possible)
- **CVSS Impact**: 5.3 (Medium) - DoS vulnerability

**Mitigation**: Only deploy untrusted collectors on Linux/macOS

**Option 3: Linux-Only (Recommended)**
- **Threat Model**: Same as Unix
- **Protection**: Full SIGALRM enforcement
- **Result**: Attack BLOCKED

---

## Deployment Decision Matrix

| Scenario | Recommended Option | Timeout Enforcement | Risk |
|----------|-------------------|---------------------|------|
| **Production (untrusted inputs)** | Option 3 (Linux-only) | ✅ FULL | LOW |
| **Production (trusted collectors)** | Option 1 (graceful) | ⚠️ NONE | MEDIUM |
| **Development/Testing** | Option 1 (graceful) | ⚠️ NONE | LOW |
| **Windows production required** | Option 2 (subprocess) | 🚧 TBD | TBD |

---

## Future Implementation: Subprocess Isolation

### YAGNI Decision Tree

**Question 1**: Is Windows production deployment a real requirement?
- ❓ Status: UNKNOWN (awaiting user confirmation)
- 📝 Action: Create ticket with deployment plan

**Question 2**: Will it be used immediately?
- ❓ Status: UNKNOWN (no Windows deployment date)
- 📝 Action: Document timeline

**Question 3**: Is there concrete data?
- ❓ Status: NO (no Windows user count, no tickets)
- 📝 Action: Gather user metrics

**Question 4**: Can it be deferred?
- ✅ Status: YES (Linux-only deployment viable)
- 📝 Decision: DEFER until Q1-Q3 pass

### Implementation Blocker

**Current Status**: NOT IMPLEMENTED

**Blocker**: CODE_QUALITY.json YAGNI gate
- No Windows production ticket
- No user count data
- No immediate requirement

**Unblock Steps**:
1. Create ticket: "Deploy doxstrux on Windows production servers"
2. Document user count / deployment plan
3. Obtain Tech Lead approval
4. Implement `tools/collector_worker.py` (8h effort)

**Placeholder**:
```python
def _run_collector_in_subprocess(self, collector, timeout_seconds):
    """Subprocess isolation for Windows timeout enforcement."""
    raise NotImplementedError(
        "Subprocess isolation not yet implemented. "
        "Requires YAGNI waiver (Windows deployment ticket). "
        "See CODE_QUALITY.json waiver_policy."
    )
```

---

## Configuration Examples

### Production (Linux)
```bash
# Full enforcement, 2-second timeout
export COLLECTOR_TIMEOUT_SECONDS=2
export STRICT_TIMEOUT_ENFORCEMENT=false  # Not needed on Linux
```

### Production (Windows - Graceful)
```bash
# Warning only, no enforcement
set COLLECTOR_TIMEOUT_SECONDS=2
set STRICT_TIMEOUT_ENFORCEMENT=false
```

### Production (Windows - Strict) 🚧
```bash
# Raises NotImplementedError (not yet implemented)
set STRICT_TIMEOUT_ENFORCEMENT=true
```

---

## Monitoring and Alerts

### Unix Deployments

**Metrics to Track**:
- Collector timeout events (count)
- Collector names hitting timeout
- Timeout duration trends

**Alerts**:
```json
{
  "event": "collector_timeout",
  "collector": "links",
  "timeout_seconds": 2,
  "platform": "Linux",
  "timestamp": "2025-10-16T12:34:56Z"
}
```

### Windows Deployments (Graceful)

**Metrics to Track**:
- Collector execution time (no limit)
- Slow collector warnings
- Platform detection (Windows count)

**Alerts**:
```json
{
  "event": "timeout_not_enforced",
  "collector": "links",
  "platform": "Windows",
  "warning": "SIGALRM not available",
  "timestamp": "2025-10-16T12:34:56Z"
}
```

---

## References

- **CLOSING_IMPLEMENTATION.md**: P0-4 specification (lines 795-1065)
- **SECURITY_IMPLEMENTATION_STATUS.md**: Run-D timeout status (lines 162-200)
- **test_collector_timeout.py**: Platform-aware timeout tests
- **CODE_QUALITY.json**: YAGNI waiver policy

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-16 | Initial policy (P0-4 implementation) |

---

**Last Updated**: 2025-10-16
**Owner**: Platform Team
**Review Cycle**: Quarterly (or when Windows deployment planned)
**Next Review**: 2026-01-16

---

## Summary

**Recommendation**: Deploy on Linux for production, use Windows for dev/test only.

**Rationale**:
- ✅ KISS principle (no over-engineering)
- ✅ Full timeout enforcement
- ✅ Industry standard
- ✅ No YAGNI violations

**Windows Support Status**: Graceful degradation (warnings only) until production requirement confirmed.
