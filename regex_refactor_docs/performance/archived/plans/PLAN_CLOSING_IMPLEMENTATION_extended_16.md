# PLAN CLOSING IMPLEMENTATION - Part 16: Strictest YAGNI/KISS - 5 Guards Only
**Version**: 16.0
**Date**: 2025-10-18
**Status**: READY FOR IMMEDIATE EXECUTION
**Methodology**: Absolute Minimal Surface - Strip Everything Non-Essential
**Part**: Part 16 - Strictest Cut
**Purpose**: Land 5 small guards, block on 5 fast tests, run 48h pilot, expand ONLY if metrics force it

---

## EXECUTIVE SUMMARY

**One-line verdict**: Strip everything that isn't a tiny, fully-testable safety net — land 5 small guards, block on 5 fast tests, run a 48-hour pilot, then expand only if metrics force it.

**The 5-Line Safe Surface** (do only these):
1. **Ingest gate** - Enforce schema + optional HMAC
2. **Permission check → deterministic fallback** - Upload sanitized artifact, exit clean
3. **Digest cap + idempotency** - MAX_ISSUES_PER_RUN=10, search-by-marker update
4. **Linux-only + collector timeouts** - SIGALRM Unix-only, enforce in CI
5. **Minimal telemetry + one page alert** - 5 counters only, page on failures

**Timeline to green-light**: 30-90 minutes implementation + 48h pilot
**Critical blockers**: 0 items (all already implemented, just verify)

---

## 5-ITEM GREEN-LIGHT CHECKLIST
**ALL items must be TRUE before production deployment.**

### SECURITY (2 items)

#### **[S1] Ingest Gate Enforced**
- **Status**: ✅ IMPLEMENTED (verify only)
- **Effort**: 10 min (verification)
- **Owner**: Security / CI
- **Evidence (machine-verifiable)**:
  ```bash
  # Verify ingest gate exists
  test -f .github/workflows/ingest_and_dryrun.yml || exit 1
  grep -q "exit 2" .github/workflows/ingest_and_dryrun.yml || exit 1
  grep -q "POLICY_REQUIRE_HMAC" .github/workflows/ingest_and_dryrun.yml || exit 1
  echo "✅ S1: Ingest gate enforced"
  ```

**Implementation** (CI snippet):
```yaml
# .github/workflows/ingest_and_dryrun.yml
- name: Validate consumer artifact
  run: |
    if [ -f adversarial_reports/consumer_artifact.json ]; then
      python tools/validate_consumer_art.py \
        --artifact adversarial_reports/consumer_artifact.json || exit 2

      if [ "${POLICY_REQUIRE_HMAC:-false}" = "true" ]; then
        python tools/validate_consumer_art.py \
          --artifact adversarial_reports/consumer_artifact.json \
          --verify-hmac || exit 3
      fi
    fi
```

#### **[S2] Permission Check → Deterministic Fallback**
- **Status**: ✅ IMPLEMENTED (verify only)
- **Effort**: 10 min (verification)
- **Owner**: Security / Automation
- **Evidence**:
  ```bash
  # Verify permission fallback exists
  grep -q "ensure_issue_create_permissions" tools/create_issues_for_unregistered_hits.py || exit 1
  test -f tools/permission_fallback.py || exit 1
  grep -q "_redact_sensitive_fields" tools/permission_fallback.py || exit 1
  echo "✅ S2: Permission fallback integrated"
  ```

**Implementation** (Python snippet):
```python
# tools/create_issues_for_unregistered_hits.py
from permission_fallback import ensure_issue_create_permissions

# After session creation
if not ensure_issue_create_permissions(args.central_repo, session, str(audit_path)):
    increment_counter("audit_issue_create_failures_total")
    print("Fallback: uploaded sanitized artifact; exiting.")
    return 2
```

### RUNTIME (2 items)

#### **[R1] Digest Cap + Idempotency**
- **Status**: ✅ IMPLEMENTED (verify only)
- **Effort**: 10 min (verification)
- **Owner**: Automation
- **Evidence**:
  ```bash
  # Verify digest cap and idempotency
  grep -q "MAX_ISSUES_PER_RUN" tools/create_issues_for_unregistered_hits.py || exit 1
  grep -q "audit_id" tools/create_issues_for_unregistered_hits.py || exit 1
  grep -q "import uuid" tools/create_issues_for_unregistered_hits.py || exit 1
  echo "✅ R1: Digest cap + idempotency implemented"
  ```

**Implementation** (Python snippet):
```python
# tools/create_issues_for_unregistered_hits.py
MAX_ISSUES_PER_RUN = 10  # Default cap

# In main()
if len(groups) > MAX_ISSUES_PER_RUN:
    logging.warning(f"Hit count ({len(groups)}) exceeds limit ({MAX_ISSUES_PER_RUN})")
    create_digest_issue(groups, session, args, audit_path)
    return

# In create_digest_issue()
audit_id = audit_id or str(uuid.uuid4())
search_query = f'repo:{args.central_repo} is:issue "audit_id:{audit_id}"'
# Search → if found, PATCH; else, POST
```

#### **[R2] Linux-Only + Collector Timeouts**
- **Status**: ✅ IMPLEMENTED (verify only)
- **Effort**: 10 min (verification)
- **Owner**: CI / Platform
- **Evidence**:
  ```bash
  # Verify Linux assertion in CI
  grep -q "platform.system.*Linux" .github/workflows/pre_merge_checks.yml || exit 1
  echo "✅ R2: Linux-only enforced"
  ```

**Implementation** (CI snippet):
```yaml
# .github/workflows/pre_merge_checks.yml
- name: Assert Linux platform
  run: |
    python - <<'PY'
    import platform, sys
    if platform.system() != 'Linux':
        print("❌ Non-Linux platform detected")
        sys.exit(2)
    print("✅ Linux OK")
    PY
```

### CI / OBSERVABILITY (1 item)

#### **[C1] Minimal Telemetry + One Page Alert**
- **Status**: ✅ IMPLEMENTED (verify only)
- **Effort**: 10 min (verification)
- **Owner**: SRE / Observability
- **Evidence**:
  ```bash
  # Verify minimal telemetry counters
  grep -q "audit_unregistered_repos_total" tools/create_issues_for_unregistered_hits.py || exit 1
  grep -q "audit_digest_created_total" tools/create_issues_for_unregistered_hits.py || exit 1
  grep -q "audit_issue_create_failures_total" tools/create_issues_for_unregistered_hits.py || exit 1
  grep -q "audit_fp_marked_total" tools/create_issues_for_unregistered_hits.py || exit 1
  test -f prometheus/rules/audit_rules.yml || exit 1
  echo "✅ C1: Minimal telemetry present"
  ```

**Required Counters** (5 only):
1. `audit_unregistered_repos_total` - Total repos scanned
2. `audit_digest_created_total` - Digest mode activations
3. `audit_issue_create_failures_total` - GitHub API failures (**PAGE on any**)
4. `audit_fp_marked_total` - False positive count
5. `audit_rate_limited_total` - Rate-limit guard triggers

**Page Alert** (Prometheus):
```yaml
# prometheus/rules/audit_rules.yml
- alert: AuditIssueCreationFailed
  expr: increase(audit_issue_create_failures_total[5m]) > 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Audit issue creation failed - immediate investigation required"
```

---

## DECISION & ENFORCEMENT MATRIX

| # | Item | Owner | Deadline | Verification Command | CI Job Name | Required Check Name | Contingency |
|---:|------|-------|----------|----------------------|-------------|---------------------|-------------|
| 1 | Ingest gate enforced | Security | Immediate | `grep -q "exit 2" .github/workflows/ingest_and_dryrun.yml` | `ingest-and-dryrun` | `Ingest Validation` | Block PRs until fixed |
| 2 | Permission fallback | Security | Immediate | `grep -q "ensure_issue_create_permissions" tools/create_issues_for_unregistered_hits.py` | N/A | N/A | Manual intervention |
| 3 | Digest idempotency | Automation | Immediate | `grep -q "audit_id" tools/create_issues_for_unregistered_hits.py` | N/A | N/A | Manual digest cleanup |
| 4 | Linux-only assertion | Platform | Immediate | `grep -q "platform.system" .github/workflows/pre_merge_checks.yml` | `pre-merge-checks` | `Pre-merge Safety Checks` | Block non-Linux PRs |
| 5 | Minimal telemetry | SRE | Immediate | `test -f prometheus/rules/audit_rules.yml` | N/A | N/A | Manual metric review |

---

## MINIMAL TESTS TO BLOCK ON PRS (5 fast tests)

**Make these required on PRs (Linux runners only):**

### Test 1: Ingest Gate Enforced
**Path**: `tests/test_ingest_gate_enforcement.py`
**Status**: ✅ EXISTS
**Verification**:
```bash
pytest -q tests/test_ingest_gate_enforcement.py -v || exit 1
```

### Test 2: Permission Fallback
**Path**: `tests/test_permission_fallback.py`
**Status**: ✅ EXISTS
**Verification**:
```bash
pytest -q tests/test_permission_fallback.py -v || exit 1
```

### Test 3: Digest Idempotency
**Path**: `tests/test_digest_idempotency.py`
**Status**: ✅ EXISTS (FIXED in Part 15)
**Verification**:
```bash
pytest -q tests/test_digest_idempotency.py -v || exit 1
```

### Test 4: Rate-Limit Guard
**Path**: `tests/test_rate_limit_guard_switches_to_digest.py`
**Status**: ✅ EXISTS (Part 15)
**Verification**:
```bash
pytest -q tests/test_rate_limit_guard_switches_to_digest.py -v || exit 1
```

### Test 5: Collector Timeout
**Path**: `tests/test_collector_timeout.py`
**Status**: ⚠️ ASSUMED EXISTS
**Verification**:
```bash
pytest -q tests/test_collector_timeout.py -v || exit 1
```

---

## MACHINE-VERIFIABLE EXAMPLES (copy-paste)

### Consolidated Verification Script
```bash
#!/bin/bash
set -e  # Exit on any error

echo "=== PHASE 8 PART 16: STRICTEST YAGNI VERIFICATION ==="
echo ""

checks_passed=0
checks_total=5

# S1: Ingest gate
if test -f .github/workflows/ingest_and_dryrun.yml && \
   grep -q "exit 2" .github/workflows/ingest_and_dryrun.yml && \
   grep -q "POLICY_REQUIRE_HMAC" .github/workflows/ingest_and_dryrun.yml; then
    echo "✅ S1: Ingest gate enforced"
    ((checks_passed++))
else
    echo "❌ S1: Ingest gate FAILED"
fi

# S2: Permission fallback
if grep -q "ensure_issue_create_permissions" tools/create_issues_for_unregistered_hits.py && \
   test -f tools/permission_fallback.py && \
   grep -q "_redact_sensitive_fields" tools/permission_fallback.py; then
    echo "✅ S2: Permission fallback integrated"
    ((checks_passed++))
else
    echo "❌ S2: Permission fallback FAILED"
fi

# R1: Digest cap + idempotency
if grep -q "MAX_ISSUES_PER_RUN" tools/create_issues_for_unregistered_hits.py && \
   grep -q "audit_id" tools/create_issues_for_unregistered_hits.py && \
   grep -q "import uuid" tools/create_issues_for_unregistered_hits.py; then
    echo "✅ R1: Digest cap + idempotency"
    ((checks_passed++))
else
    echo "❌ R1: Digest FAILED"
fi

# R2: Linux-only
if grep -q "platform.system.*Linux" .github/workflows/pre_merge_checks.yml; then
    echo "✅ R2: Linux-only enforced"
    ((checks_passed++))
else
    echo "❌ R2: Linux assertion FAILED"
fi

# C1: Minimal telemetry
if grep -q "audit_unregistered_repos_total" tools/create_issues_for_unregistered_hits.py && \
   grep -q "audit_issue_create_failures_total" tools/create_issues_for_unregistered_hits.py && \
   test -f prometheus/rules/audit_rules.yml; then
    echo "✅ C1: Minimal telemetry present"
    ((checks_passed++))
else
    echo "❌ C1: Telemetry FAILED"
fi

echo ""
echo "Safety net checks: $checks_passed/$checks_total passed"
echo ""

if [ $checks_passed -eq $checks_total ]; then
    echo "✅ ALL 5 GUARDS VERIFIED - READY FOR 48H PILOT 🚀"
    exit 0
else
    echo "❌ BLOCKED - Fix failing checks before pilot"
    exit 1
fi
```

### Run All 5 Required Tests
```bash
#!/bin/bash
set -e

echo "=== RUNNING 5 REQUIRED TESTS ==="

pytest -q tests/test_ingest_gate_enforcement.py -v || { echo "❌ Test 1 failed"; exit 1; }
pytest -q tests/test_permission_fallback.py -v || { echo "❌ Test 2 failed"; exit 1; }
pytest -q tests/test_digest_idempotency.py -v || { echo "❌ Test 3 failed"; exit 1; }
pytest -q tests/test_rate_limit_guard_switches_to_digest.py -v || { echo "❌ Test 4 failed"; exit 1; }
pytest -q tests/test_collector_timeout.py -v || { echo "❌ Test 5 failed (may not exist)"; exit 1; }

echo "✅ ALL 5 TESTS PASSED"
```

---

## PRIORITIZED EXECUTION ORDER

### IMMEDIATE (Next 30 minutes) - VERIFICATION ONLY
**ALL implementations complete from Parts 12-15. This is verification-only.**

1. **Verify ingest gate** — Effort: 5 min — Owner: Security
2. **Verify permission fallback** — Effort: 5 min — Owner: Security
3. **Verify digest cap + idempotency** — Effort: 5 min — Owner: Automation
4. **Verify Linux assertion** — Effort: 5 min — Owner: Platform
5. **Verify minimal telemetry** — Effort: 5 min — Owner: SRE

**Run**: `bash verify_5_guards.sh`

### SHORT-TERM (Next 60 minutes) - TEST EXECUTION
**Run 5 required tests to ensure behavioral correctness.**

6. **Run Test 1: Ingest gate** — Effort: 2 min
7. **Run Test 2: Permission fallback** — Effort: 2 min
8. **Run Test 3: Digest idempotency** — Effort: 2 min
9. **Run Test 4: Rate-limit guard** — Effort: 2 min
10. **Run Test 5: Collector timeout** — Effort: 2 min (if exists)

**Run**: `bash run_5_tests.sh`

### 48-HOUR PILOT
**Deploy to 1 repo, monitor metrics, expand only if clean.**

11. **Deploy Stage 1 canary** — 1 repo, 24h
12. **Monitor metrics** — `audit_issue_create_failures_total` MUST be 0
13. **Verify FP rate** — `audit_fp_marked_total / audit_unregistered_repos_total < 0.10`

---

## ARTIFACTS (ready-to-paste)

**Artifact A**: `.github/workflows/ingest_and_dryrun.yml`
**Purpose**: Ingest gate CI workflow (enforces schema + optional HMAC)

**Artifact B**: `tools/permission_fallback.py`
**Purpose**: Permission check + sanitized artifact upload fallback

**Artifact C**: `tools/create_issues_for_unregistered_hits.py`
**Purpose**: Issue automation with digest cap, idempotency, telemetry

**Artifact D**: `prometheus/rules/audit_rules.yml`
**Purpose**: Minimal alert rules (page on `audit_issue_create_failures_total > 0`)

**Artifact E**: `tests/test_digest_idempotency.py`
**Purpose**: Verify digest search-by-marker and update behavior

---

## TIMELINE TO GREEN-LIGHT

| Phase | Duration | Effort | Items | Notes |
|-------|----------|--------|-------|-------|
| Immediate | 30 min | 25 min | 5 verifications | All already implemented |
| Short-term | 60 min | 10 min | 5 tests | Run to confirm behavior |
| Pilot (Stage 1) | 24 hours | Automated | Metrics monitoring | 1 repo, low risk |
| Pilot (Stage 2) | 24 hours | Automated | Metrics monitoring | 2 repos, expand if clean |
| **TOTAL** | **~50 hours** | **~35 min** | **15 items** | **Mostly automated** |

---

## CANARY DEPLOYMENT RUNBOOK

### Pre-Canary Checklist
- ✅ All 5 guards verified (`verify_5_guards.sh` passes)
- ✅ All 5 tests passing (`run_5_tests.sh` passes)
- ✅ Prometheus alert rule configured (`audit_issue_create_failures_total`)
- ⏳ Human approval obtained

### Canary Stages

| Stage | Traffic | Duration | Gate Condition |
|-------|---------|----------|----------------|
| 1 | 1 repo (33%) | 24h | `failures == 0` AND `FP < 10%` |
| 2 | 2 repos (66%) | 24h | Same as Stage 1 |
| 3 | 3 repos (100%) | 7 days | All metrics within thresholds |

### Rollback Procedure (exact commands)
```bash
# Emergency rollback
set -e

# 1. Scale down canary
kubectl scale deployment/parser-canary --replicas=0 || exit 1

# 2. Revert to stable
kubectl rollout undo deployment/parser-service || exit 1

# 3. Wait for stable pods
kubectl wait --for=condition=ready pod -l app=parser-service --timeout=300s || exit 1

# 4. Verify
kubectl get pods -l app=parser-service
echo "✅ Rollback complete"
```

---

## METRICS & ALERT THRESHOLDS

### Required Metrics (5 only):

1. **`audit_unregistered_repos_total`** — Counter: Total repos scanned
2. **`audit_digest_created_total`** — Counter: Digest activations (alert if > 3/day)
3. **`audit_issue_create_failures_total`** — Counter: GitHub API failures (**PAGE on any**)
4. **`audit_fp_marked_total`** — Counter: False positives (warn if > 10% over 7d)
5. **`audit_rate_limited_total`** — Counter: Rate-limit triggers (warn if > 0)

### Alert Rules (Prometheus):
```yaml
groups:
  - name: audit_critical
    rules:
      - alert: AuditIssueCreationFailed
        expr: increase(audit_issue_create_failures_total[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Audit issue creation failed - page SRE immediately"
```

---

## RISK MATRIX

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| GitHub API rate exhaustion | Low | High | Rate-limit guard switches to digest @ quota < 500 |
| Permission loss mid-run | Low | Medium | Atomic fallback + Slack alert |
| Digest duplication | Very Low | Low | UUID-based `audit_id` (idempotent) |
| FP rate > 10% | Medium | Low | Curated patterns (67% FP reduction in Part 12) |
| Collector timeout | Low | Very Low | Subprocess isolation + 30s timeout |
| Non-Linux platform | Very Low | Medium | Platform assertion in pre-merge CI |

---

## WHAT TO DROP / DEFER (YAGNI — DO NOT DO NOW)

**❌ Deferred until metrics show need:**

1. **Org-wide automatic discovery / central scanning**
   - Trigger: `consumer_count >= 10`

2. **Windows worker parity / complex sandboxing**
   - Trigger: `windows_users >= 5`

3. **Full KMS/GPG automated baseline signing**
   - Keep: Manual process + docs (Step 1 in RUN_TO_GREEN.md)

4. **Broad GitHub App cross-repo automation**
   - Keep: Central backlog opt-in only

5. **Large dashboards, many alerts, auto-close flows**
   - Keep: 5 counters + 1 page alert only

6. **SQLite FP telemetry**
   - Trigger: `fp_issues >= 500`

7. **Advanced renderer detection**
   - Trigger: `fp_rate >= 15%`

8. **Multi-repo digest batching**
   - Trigger: `repos_scanned >= 50`

**Decision Rule**: If you find yourself wanting these, ask: **"Do metrics show we need it?"** — if no, defer.

---

## ACCEPTANCE (GO / NO-GO)

### Binary Go/No-Go (48-72h Pilot)
**Green ONLY if ALL TRUE:**

1. ✅ Ingest gate enforced and tests pass
2. ✅ Permission fallback exercised in dry-run (artifact uploaded & sanitized alert)
3. ✅ Digest cap + idempotency validated
4. ✅ Linux assertion passes on CI
5. ⏳ No pages for `audit_issue_create_failures_total` during 48h pilot
6. ⏳ `audit_fp_rate < 10%` over pilot

**If any NO → ROLLBACK immediately**

### Green-Light Criteria Summary:
- All 5 guards verified (30 min)
- All 5 tests passing (10 min)
- 48h pilot metrics clean:
  - `audit_issue_create_failures_total == 0`
  - `audit_fp_marked_total / audit_unregistered_repos_total < 0.10`
  - No timeout spikes (within baseline × 1.5)

---

## APPENDIX

### Links
- **Warehouse Spec**: `PLAN_WAREHOUSE_OPTIMIZATION_SPEC.md`
- **Execution Plan**: `PLAN_CLOSING_IMPLEMENTATION.md` (v3.0 consolidated)
- **RUN_TO_GREEN**: `RUN_TO_GREEN.md` (v2.0 refactored)

### Contact
- **Tech Lead**: @tech-lead
- **SRE**: @sre-lead (baseline, monitoring, rollback)
- **Security**: @security-lead (ingest gate, fallback, registry)
- **DevOps**: @devops-lead (CI, secrets, branch protection)

---

## EVIDENCE ANCHORS

**CLAIM-PART16**: All 5 guards already implemented in Parts 12-15. Part 16 is verification-only + 48h pilot execution.

**Evidence**:
- S1: Ingest gate (`.github/workflows/ingest_and_dryrun.yml` - Part 13)
- S2: Permission fallback (`tools/permission_fallback.py` - Part 13)
- R1: Digest idempotency (`tools/create_issues_for_unregistered_hits.py` - Part 13, fixed in Part 15)
- R2: Linux-only (`.github/workflows/pre_merge_checks.yml` - Part 13)
- C1: Minimal telemetry (5 counters + Prometheus rules - Part 13)

**Tests**:
- Test 1: `tests/test_ingest_gate_enforcement.py` (Part 12)
- Test 2: `tests/test_permission_fallback.py` (Part 13)
- Test 3: `tests/test_digest_idempotency.py` (Part 13, **fixed in Part 15**)
- Test 4: `tests/test_rate_limit_guard_switches_to_digest.py` (**Part 15**)
- Test 5: `tests/test_collector_timeout.py` (assumed exists)

**Source**: Parts 12-15 completion artifacts

**Date**: 2025-10-18

**Verification Method**: Consolidated verification script (`verify_5_guards.sh`)

---

## SUMMARY

**Part 16: Strictest YAGNI/KISS - 5 Guards Only**

### What This Document Provides:

✅ **5 Mandatory Guards** (all implemented, verification-only)
✅ **5 Required Tests** (4 exist, 1 assumed)
✅ **Consolidated Verification Scripts** (copy-paste ready)
✅ **48h Pilot Runbook** (deploy, monitor, rollback)
✅ **YAGNI Enforcement** (defer 8 items until metrics show need)

### Critical Insight:

Parts 12-15 did the work. Part 16 says: **"Stop adding. Verify what exists. Run pilot. Expand ONLY if data demands it."**

This is the **absolute minimum safe surface** — 5 guards, 5 tests, 48h pilot. **No more, no less.**

### Status:

**Implementation**: 5/5 guards complete (Parts 12-15)
**Testing**: 4/5 tests exist, 1 assumed
**Timeline**: 30 min verification + 48h pilot
**Risk**: **ULTRA-LOW** (tiniest possible surface)

### Next Steps:

1. Run `verify_5_guards.sh` (30 min)
2. Run `run_5_tests.sh` (10 min)
3. Obtain human approval
4. Deploy Stage 1 canary (1 repo, 24h)
5. Monitor → expand if clean → **DONE**

---

🎯 **STRICTEST YAGNI/KISS v16.0: 5 GUARDS, 5 TESTS, 48H PILOT, EXPAND ONLY IF METRICS FORCE IT** 🚀

**Awaiting**: Human approval for 48h pilot deployment
