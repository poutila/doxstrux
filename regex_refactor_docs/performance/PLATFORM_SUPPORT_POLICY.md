# Platform Support Policy - Untrusted Markdown Parsing

**Version**: 1.0
**Date**: 2025-10-18
**Status**: PRODUCTION POLICY
**Owner**: Tech Lead / SRE

---

## Executive Summary

**Decision**: Doxstrux untrusted markdown parsing is **Linux-only** in production.

**Rationale**: Windows subprocess isolation requires significant engineering effort (8+ hours) with limited ROI for current deployment targets (all Linux-based).

**Impact**: Windows users can still use Doxstrux, but with **trusted inputs only** (no untrusted/adversarial markdown).

---

## Background

Doxstrux uses `signal.SIGALRM` for timeout enforcement during untrusted markdown parsing to prevent infinite loops and DoS attacks. This signal is **POSIX-only** and not available on Windows.

**Two options for Windows support**:

1. **Subprocess Worker Pool** (8+ hours engineering effort)
   - Spawn worker processes with `multiprocessing`
   - Use `TerminateProcess()` on Windows for timeout enforcement
   - Requires process pool management, IPC, error handling
   - Adds complexity and maintenance burden

2. **Linux-Only Policy** (0 hours engineering effort)
   - Enforce `platform.system() == 'Linux'` assertion in CI/deploy
   - Document Windows limitation
   - Defer Windows support to future ticket (if demand arises)

**Decision**: **Option 2** (Linux-only) based on:
- All production deployments are Linux-based (AWS/GCP/Azure VMs, containers, serverless)
- No current demand for Windows untrusted parsing
- YAGNI principle: don't build it until needed
- Can revisit if Windows deployment becomes required

---

## Policy Details

### Supported Platforms

**Production (Untrusted Inputs)**:
- ✅ Linux (Ubuntu 20.04+, RHEL 8+, Amazon Linux 2+)
- ❌ Windows (not supported for untrusted inputs)
- ❌ macOS (POSIX-compliant, but not tested/supported in production)

**Development/Testing (Trusted Inputs)**:
- ✅ Linux
- ✅ macOS (for local development)
- ✅ Windows (for local development with trusted markdown only)

### Enforcement

**CI/CD**:
- Production deploy jobs **MUST** assert `platform.system() == 'Linux'`
- Deployment to non-Linux platforms **MUST** fail with clear error message

**Runtime**:
- Parser initialization **MAY** include platform assertion in strict security mode
- Parser documentation **MUST** state Linux-only requirement for untrusted inputs

**Example CI Assertion**:
```yaml
- name: Verify Linux platform
  run: |
    python -c "import platform; assert platform.system() == 'Linux', 'Production deployment requires Linux for untrusted markdown parsing'"
```

---

## Trade-offs Accepted

### Trade-off 1: Windows Users Must Use Trusted Inputs Only

**Impact**: Windows developers/users cannot parse untrusted markdown locally

**Mitigation**:
- Provide clear documentation of limitation
- Recommend using WSL2 (Windows Subsystem for Linux) for untrusted parsing
- Provide Docker image for cross-platform testing

### Trade-off 2: Future Windows Support Requires Refactoring

**Impact**: If Windows support becomes required, we must implement subprocess worker pool (8+ hours)

**Mitigation**:
- Document implementation path in this policy
- Treat as separate project ticket (not urgent)
- Can defer indefinitely if no demand

### Trade-off 3: macOS Not Officially Supported

**Impact**: macOS is POSIX-compliant and would work, but we don't test/support it in production

**Mitigation**:
- Allow for local development (POSIX signals work)
- Don't advertise as production-supported
- Recommend Linux VMs/containers for production

---

## Future Work (Deferred)

If Windows support becomes required (ticket created only if demand arises):

**Implementation Path**:
1. Create `src/doxstrux/markdown/runtime/worker_pool.py`
2. Implement process pool with configurable size (default: 4 workers)
3. Use `multiprocessing.Queue` for IPC
4. Implement timeout via `Process.join(timeout=N)` + `Process.terminate()`
5. Add fallback for Windows: `TerminateProcess()` via `ctypes`
6. Write tests: `tests/test_worker_pool_isolation.py`
7. Update CI to test on Windows runners
8. Update documentation

**Estimated Effort**: 8-12 hours

**Priority**: P3 (only if demand from production Windows deployments)

---

## Documentation Requirements

All user-facing documentation must include:

**README.md**:
> **Platform Support**: Doxstrux untrusted markdown parsing requires **Linux** in production. Windows/macOS users should use trusted inputs only, or run via Docker/WSL2.

**API Documentation**:
> **Security Note**: Timeout enforcement for untrusted inputs requires Linux (uses POSIX signals). Windows deployments must only parse trusted markdown.

**Deployment Guide**:
> **Production Requirements**: Deploy to Linux-based platforms only (AWS EC2, GCP Compute, Azure VMs, containers). Windows deployments are not supported for untrusted inputs.

---

## Trigger Thresholds for Reintroducing Removed Features

This section defines **measurable thresholds** that trigger reintroduction of features removed in Part 11 simplification. These thresholds are monitored via Prometheus metrics and trigger tickets for implementation when exceeded.

### Consumer Artifacts + HMAC Signing

**Trigger**: `consumer_count >= 10` OR `avg_org_unregistered_repos_per_run >= 5` for 7 consecutive days

**Reason**: Org-scan GitHub API quota will be exhausted with manual issue creation

**Action**: Implement consumer-driven discovery with HMAC signing (Part 10 Tier 1)

**Monitoring**:
```promql
# Alert when consumer count exceeds threshold
ALERT HighConsumerCount
  IF consumer_count >= 10
  FOR 7d
  ANNOTATIONS {
    summary = "Consumer count exceeded threshold ({{ $value }} >= 10)",
    description = "Implement consumer artifacts + HMAC signing from Part 10 Tier 1"
  }

# Alert when average unregistered repos per run is high
ALERT HighUnregisteredReposPerRun
  IF avg_over_time(org_unregistered_repos_gauge[7d]) >= 5
  FOR 7d
  ANNOTATIONS {
    summary = "Average unregistered repos per run exceeded threshold ({{ $value }} >= 5)",
    description = "GitHub API quota will be exhausted - implement consumer artifacts"
  }
```

**Implementation Ticket**: Create ticket with link to Part 10 Tier 1 implementation plan

---

### Artifact Schema Validation

**Trigger**: Manual triage workload > 1 FTE-day/week (measured via issue processing time metrics)

**Reason**: Manual validation no longer scales

**Action**: Implement JSON Schema validation (Part 10 Tier 1)

**Monitoring**:
```promql
# Alert when manual triage time exceeds threshold
ALERT HighManualTriageLoad
  IF sum(rate(issue_triage_seconds_total[7d])) > 28800  # 1 FTE-day = 8 hours = 28800 seconds
  FOR 1w
  ANNOTATIONS {
    summary = "Manual triage load exceeded 1 FTE-day/week ({{ $value }}s/week)",
    description = "Implement artifact schema validation from Part 10 Tier 1"
  }
```

**Implementation Ticket**: Create ticket with link to Part 10 Tier 1 schema validation spec

---

### SQLite FP Telemetry

**Trigger**: `FP_rate > 10%` over 30 days (measured via manual FP reports or issue labels)

**Reason**: Manual tracking cannot keep up with FP volume

**Action**: Implement SQLite telemetry + dashboard (Part 10 Tier 2)

**Monitoring**:
```promql
# Alert when false positive rate exceeds threshold
ALERT HighFalsePositiveRate
  IF (sum(rate(audit_false_positives_total[30d])) / sum(rate(audit_hits_total[30d]))) > 0.10
  FOR 30d
  ANNOTATIONS {
    summary = "False positive rate exceeded 10% ({{ $value }})",
    description = "Implement SQLite FP telemetry from Part 10 Tier 2"
  }
```

**Implementation Ticket**: Create ticket with link to Part 10 Tier 2 telemetry implementation

---

### Renderer Pattern Curation

**Trigger**: `pattern_count > 50` OR `FP_rate_per_pattern varies > 20%` over 30 days

**Reason**: Pattern set becomes unmaintainable without curation

**Action**: Implement renderer pattern curation (Part 10 Tier 2)

**Monitoring**:
```promql
# Alert when pattern count exceeds threshold
ALERT TooManyPatterns
  IF renderer_pattern_count > 50
  FOR 7d
  ANNOTATIONS {
    summary = "Renderer pattern count exceeded threshold ({{ $value }} > 50)",
    description = "Implement pattern curation from Part 10 Tier 2"
  }

# Alert when FP rate variance is high
ALERT HighFPRateVariance
  IF stddev_over_time(fp_rate_per_pattern[30d]) > 0.20
  FOR 30d
  ANNOTATIONS {
    summary = "FP rate variance exceeded 20% ({{ $value }})",
    description = "Some patterns have high FP rates - implement curation"
  }
```

**Implementation Ticket**: Create ticket with link to Part 10 Tier 2 curation spec

---

### Metric Export and Alerting

**Trigger**: Any of the above alerts fire

**Action**: Review Prometheus metrics, confirm threshold breach, create implementation ticket

**Escalation**: If multiple alerts fire simultaneously, escalate to Tech Lead for prioritization

---

## Review and Approval

**Approvers**:
- Tech Lead: ✅ Approved (defers Windows complexity)
- SRE: ✅ Approved (all production platforms are Linux)
- Security: ✅ Approved (Linux-only simplifies threat model)

**Review Date**: 2025-10-18

**Next Review**: Annually, or when Windows deployment demand arises

---

## References

- CODE_QUALITY Policy: YAGNI principle (don't build it until needed)
- Part 11 Deep Assessment: Over-engineering feedback
- Phase 8 Security Hardening: Timeout enforcement requirement

---

**Status**: ✅ APPROVED - Linux-only policy adopted
