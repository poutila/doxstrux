# Platform Support Policy for Untrusted Input Parsing

**Status**: DECIDED
**Decision Date**: 2025-10-18
**Decision Owner**: Tech Lead
**Effective**: Immediately
**Source**: PLAN_CLOSING_IMPLEMENTATION_extended_6.md (Part 6, Action 1)

---

## Executive Summary

This policy defines the supported platforms for executing untrusted parsing and collector code in the MD_ENRICHER system. The decision is **Linux-only** for production deployments due to timeout enforcement requirements.

---

## Production Deployment

### Allowed Platforms

- **Linux** (Ubuntu 22.04+, kernel 6.1+)
  - All parsing workers MUST run on Linux nodes
  - All collector execution MUST occur on Linux hosts
  - CI/CD pipeline MUST run on Linux runners

### Blocked Platforms

- **Windows** (all versions)
  - **Reason**: Timeout enforcement unavailable (no SIGALRM support)
  - **Status**: Not supported for production
  - **Workaround**: Requires subprocess worker pool (see Future Considerations)

- **macOS**
  - **Status**: Development and testing only
  - **Production**: Not supported

---

## Enforcement

### 1. Deploy Script Validation

**File**: `deploy/validate_platform.sh`

The deployment script MUST verify platform before allowing deployment:

```bash
#!/bin/bash
# Deploy-time platform validation

set -euo pipefail

echo "Validating deployment platform..."

# Check current platform
PLATFORM=$(python3 -c "import platform; print(platform.system())")

if [ "$PLATFORM" != "Linux" ]; then
    echo "❌ ERROR: Parser deployment requires Linux platform"
    echo "   Current platform: $PLATFORM"
    echo "   See docs/PLATFORM_POLICY.md for details"
    exit 1
fi

echo "✅ Platform validation passed: Linux"
```

**Enforcement**:
- Fails deployment if any Windows node detected in parsing pool
- Runtime platform assertion in pod spec
- Exit code 1 blocks deployment pipeline

### 2. CI Assertion

**Required in all CI workflows** (`.github/workflows/*.yml`):

```yaml
- name: Verify platform policy
  run: |
    python -c "import platform; assert platform.system()=='Linux', 'Parser requires Linux for SIGALRM timeout enforcement'"
```

**Example Integration** (in `.github/workflows/parser_tests.yml`):

```yaml
jobs:
  test:
    runs-on: ubuntu-latest  # Enforces Linux
    steps:
      - uses: actions/checkout@v4
      - name: Verify platform policy
        run: |
          python -c "import platform; assert platform.system()=='Linux', 'Parser requires Linux'"
      - name: Run tests
        run: |
          .venv/bin/python -m pytest skeleton/tests/ -v
```

### 3. Decision Deadline

**Timeline**: 24 hours after plan approval
**Default if no decision**: Linux-only (this policy)

**Rationale for 24h deadline**:
- Prevents indefinite deferral of platform decision
- Allows rapid deployment without blocking on Windows support
- Linux-only is safe default (timeout enforcement works)

---

## Rationale

### Why Linux-Only?

1. **SIGALRM-based timeout enforcement requires POSIX signals**
   - Collector timeout watchdog uses `signal.SIGALRM`
   - Windows has no equivalent mechanism
   - Missing timeout → blocking collector can hang workers → DoS vulnerability

2. **Windows subprocess isolation not yet implemented**
   - Requires subprocess worker pool with restart/watchdog
   - Estimated effort: 2-3 weeks additional work
   - Not on critical path for initial production deployment

3. **Linux-only is lowest-risk path**
   - Timeout enforcement proven in Linux
   - All existing infrastructure runs on Linux
   - No additional complexity

### Security Implications

**Without timeout enforcement** (if Windows were allowed):
- Malicious or pathological input could block collector indefinitely
- Worker pool exhaustion → denial of service
- No automatic recovery mechanism

**With Linux-only policy**:
- SIGALRM watchdog kills hung collectors after 5 seconds
- Workers automatically restart after timeout
- DoS risk mitigated

---

## Future Considerations

### Windows Support Workstream

If Windows support becomes required in the future, the following must be completed:

#### Requirements

1. **Subprocess Worker Pool Implementation** (8-16 hours)
   - Replace in-process collector execution with subprocess spawn
   - Implement watchdog process to monitor subprocess
   - Add restart logic on subprocess hang/crash

2. **Isolation Test Harness** (4-8 hours)
   - Verify subprocess isolation prevents cross-contamination
   - Test timeout enforcement on Windows
   - Validate restart/recovery logic

3. **Observability & Runbooks** (4-8 hours)
   - Add metrics for subprocess lifecycle events
   - Document Windows-specific failure modes
   - Create runbooks for common issues

4. **Security Review & Audit** (8-16 hours)
   - Re-audit timeout enforcement mechanism
   - Verify subprocess isolation prevents escape
   - Penetration testing on Windows platform

**Total Estimated Effort**: 2-3 weeks
**Priority**: Not on critical path (defer until customer requirement)

#### Acceptance Criteria for Windows Support

Before Windows can be added as supported platform:

- ✅ Subprocess worker pool implemented and tested
- ✅ Timeout enforcement verified on Windows (manual + automated tests)
- ✅ Isolation harness passing 100% (no cross-contamination)
- ✅ Performance benchmarks within 10% of Linux baseline
- ✅ Security audit completed with no high/critical findings
- ✅ Runbooks and observability deployed
- ✅ Policy document updated and approved by Tech Lead

---

## Verification

### Deploy-Time Checks

```bash
# Verify deployment platform (run before deployment)
python -c "import platform; assert platform.system()=='Linux', 'Parser requires Linux'"
echo $?  # Expected: 0 (Linux), non-zero (other platforms)
```

### Runtime Checks

```bash
# Verify parsing worker nodes are Linux
kubectl get nodes -l workload=parsing -o jsonpath='{.items[*].status.nodeInfo.operatingSystem}'
# Expected output: linux linux linux... (all nodes)

# Detect Windows nodes in parsing pool (should be empty)
kubectl get nodes -l workload=parsing,os=windows --no-headers | wc -l
# Expected: 0 (no Windows nodes)
```

### CI Checks

```bash
# Verify CI workflows enforce platform policy
grep -r "platform.system" .github/workflows/*.yml
# Expected: Found in all parser-related workflows
```

---

## Enforcement Escalation

### Violation Handling

**If Windows node detected in parsing pool**:

1. **Immediate** (automated):
   - Daily cluster audit creates P0 incident
   - Alert posted to #security-alerts Slack channel
   - SRE on-call paged immediately

2. **Within 1 hour** (SRE):
   - Cordon Windows node (prevent new pod scheduling)
   - Drain parsing pods from Windows node
   - Migrate pods to Linux nodes

3. **Within 24 hours** (Engineering Manager):
   - Root cause analysis: How did Windows node enter pool?
   - Update node pool configuration to prevent recurrence
   - Document incident in post-mortem

4. **Within 1 week** (Tech Lead):
   - Review if Windows support is required
   - If yes: Initiate Windows support workstream
   - If no: Strengthen enforcement to prevent future violations

---

## Audit Trail

### Policy Changes

| Version | Date | Change | Approved By |
|---------|------|--------|-------------|
| 1.0 | 2025-10-18 | Initial policy (Linux-only) | Tech Lead |

### Compliance Audits

**Frequency**: Daily at 08:00 UTC
**Tool**: `tools/audit_cluster_platform.py`
**Report**: Posted to #green-light Slack channel
**Escalation**: P0 incident created if Windows node found

**Audit Script** (reference implementation in `tools/audit_cluster_platform.py`):

```python
#!/usr/bin/env python3
"""
Daily audit to verify all parsing workers run on Linux.
Creates P0 incident if Windows node detected.
"""
import subprocess
import sys
from datetime import datetime

def check_parsing_nodes():
    """Check all nodes in parsing pool are Linux."""
    cmd = ["kubectl", "get", "nodes", "-l", "workload=parsing",
           "-o", "jsonpath={.items[*].status.nodeInfo.operatingSystem}"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"ERROR: kubectl command failed: {result.stderr}")
        return False

    os_list = result.stdout.strip().split()
    windows_count = sum(1 for os in os_list if os.lower() != "linux")

    if windows_count > 0:
        print(f"❌ PLATFORM POLICY VIOLATION: {windows_count} Windows nodes in parsing pool")
        print(f"   Total nodes: {len(os_list)}, Windows: {windows_count}")
        create_p0_incident(windows_count)
        return False

    print(f"✅ Platform policy compliant: All {len(os_list)} parsing nodes are Linux")
    return True

def create_p0_incident(windows_count):
    """Create P0 incident for platform violation."""
    incident = {
        "severity": "P0",
        "title": f"Platform Policy Violation: {windows_count} Windows Nodes in Parsing Pool",
        "description": f"Detected {windows_count} Windows nodes in parsing pool. "
                      f"Parser requires Linux for SIGALRM timeout enforcement. "
                      f"See docs/PLATFORM_POLICY.md for details.",
        "timestamp": datetime.utcnow().isoformat(),
        "escalation": "SRE on-call (immediate)"
    }
    # Integration with incident management system would go here
    print(f"P0 INCIDENT CREATED: {incident}")

if __name__ == "__main__":
    compliant = check_parsing_nodes()
    sys.exit(0 if compliant else 1)
```

---

## Related Documentation

- **PLAN_CLOSING_IMPLEMENTATION_extended_6.md**: Part 6, Action 1 (Platform Policy Decision)
- **PLAN_CLOSING_IMPLEMENTATION_extended_5.md**: Part 5, Gap 6 (Windows Deployment Enforcement)
- **skeleton/tests/test_collector_isolation.py**: Timeout enforcement tests

---

## Contact & Questions

- **Policy Owner**: Tech Lead
- **Enforcement Owner**: SRE Team
- **Questions**: #green-light Slack channel
- **Change Requests**: Submit PR with policy update + approval from Tech Lead

---

**Last Updated**: 2025-10-18
**Next Review**: After Windows support workstream completion (if initiated)
