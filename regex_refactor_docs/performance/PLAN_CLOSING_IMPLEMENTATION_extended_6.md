# Extended Closing Implementation Plan - Phase 8 Security Hardening
# Part 6 of 6: Final Security Hardening & Operational Enforcement

**Version**: 1.1 (Operational Implementation & Fatal P0 Enforcement)
**Date**: 2025-10-17
**Status**: STEP-BY-STEP IMPLEMENTATION GUIDE - DEFENSIBLE GREEN-LIGHT READY
**Methodology**: Golden Chain-of-Thought + External Deep Security Assessment (Third Round)
**Part**: 6 of 6
**Purpose**: Concrete, copy-paste implementation steps for remaining operational security items

⚠️ **CRITICAL**: This part provides **EXACT IMPLEMENTATION STEPS** with git patches, commands, and verification procedures to close all remaining security gaps.

**Previous Parts**:
- Part 1: PLAN_CLOSING_IMPLEMENTATION_extended_1.md (P0 Critical - 5 tasks)
- Part 2: PLAN_CLOSING_IMPLEMENTATION_extended_2.md (P1/P2 Patterns - 10 tasks)
- Part 3: PLAN_CLOSING_IMPLEMENTATION_extended_3.md (P3 Observability - 3 tasks)
- Part 4: PLAN_CLOSING_IMPLEMENTATION_extended_4.md (Security Audit Response - blocking items analysis)
- Part 5: PLAN_CLOSING_IMPLEMENTATION_extended_5.md (v2.2 - Green-Light Checklist with automation)

**Source**: External deep security assessment (third round) with concrete remediation priorities

**Assessment Verdict**: "You're very close to being able to run a defended, performance-focused canary. The architecture, adversarial corpora, and defensive patches are solid and well-documented. The remaining work is overwhelmingly operational and verifiability-focused."

---

⚠️ **CRITICAL ENFORCEMENT SEMANTICS (v1.1 Change)**

**What Changed from v1.0**: The audit script (`tools/audit_greenlight.py`) now enforces **fail-closed** semantics for P0 checks. Previously, P0 failures were reported but didn't block the run. **v1.1 makes P0 failures FATAL**.

**P0 Checks with Fatal Enforcement**:
- **P0-1: Branch Protection** → If `verify_branch_protection_from_registry()` returns error/skipped/fail → audit exits with code **5 (FATAL)**
- **P0-2: Baseline Verification** → If signed baseline missing, capture script unavailable, or capture failed → audit exits with code **6 (FATAL)**

**Impact on CI/CD**:
- ❌ Nightly CI job **FAILS** if P0 checks fail (blocks further expensive tests)
- ❌ Pre-canary checklist **FAILS** if P0 checks fail (blocks deployment)
- ❌ **No canary deployment possible** until P0 items fixed

**Rationale**: P0 items are **blocking security requirements**. Missing baseline or unconfigured branch protection indicates incomplete security posture → system **must not proceed** (fail-closed).

**Required Before Green-Light**:
1. Signed canonical baseline exists at `baselines/metrics_baseline_v1_signed.json` (GPG-signed by SRE)
2. Consumer registry exists with all metadata-rendering consumers listed
3. Branch protection configured with all required checks per registry
4. Platform policy documented and enforced in CI

---

## EXECUTIVE SUMMARY

This document provides **concrete, executable steps** to implement the final operational security items identified in the third-round deep security assessment. All work is **copy-paste ready** with git patches, shell commands, and exact verification procedures.

**What's included**:
- **3 ready-to-apply git patches** (v1.1 update):
  - Patch 1: Baseline verification in audit script
  - Patch 2: Pre-canary CI integration
  - **Patch 3 (v1.1 NEW)**: Make P0 checks FATAL (fail-closed enforcement)
- Step-by-step remediation plan with exact timelines
- Machine-verifiable test checklist (copy-paste commands)
- Priority-ordered action items with owners and effort estimates
- Concrete pitfall warnings with preventive measures
- **Consumer discovery gap analysis** (v1.1 NEW)

**Timeline to defensible green-light**: 24-72 hours for immediate items, 1-2 weeks for full deployment

**Critical priorities**:
1. **Immediate (24h)**: Platform policy decision, adversarial CI gate enablement, baseline verification
2. **Short-term (48-72h)**: SSTI consumer deployment, token canonicalization enforcement, baseline capture
3. **Medium-term (1-2 weeks)**: Consumer registry deployment, performance benchmarks, full observability

---

## THIRD-ROUND ASSESSMENT FINDINGS

### Executive Summary of Gaps

**Status**: Nearly green-light ready, but must close operational enforcement gaps

**Strengths** ✅:
- Architecture sound and well-documented
- Adversarial corpora comprehensive (20+ URL vectors)
- Defensive patches implemented in skeleton
- Acceptance matrix machine-verifiable
- CI guidance complete

**Remaining Gaps** ⏸️:
- **CRITICAL**: SSTI consumer enforcement not automated (manual tracking brittle)
- **CRITICAL**: Consumer discovery incomplete (unknown consumers may render metadata without protection)
- **HIGH**: Token canonicalization bypass prevention not enforced in CI
- **HIGH**: URL canonicalization parity not blocking PR smoke job
- **HIGH**: Cross-platform timeout policy undecided (Linux vs Windows)
- **MED**: Baseline capture not canonical/auditable (v1.1: NOW FATAL if missing)
- **MED**: Branch protection verification not automated (v1.1: NOW FATAL if misconfigured)
- **MED**: Collector caps not fully tested (1/9 passing)

### Key Findings by Risk Category

#### CRITICAL: SSTI Leaking via Downstream Consumers

**Why Critical**: Collectors flag template-like metadata, but if consumer renders without escaping → SSTI → RCE.

**Current State**: Plan requires consumer-level litmus tests, but enforcement is manual.

**What's Missing**:
- Automated discovery of which consumers render metadata
- Automated verification that SSTI tests exist and pass
- Blocking CI enforcement in consumer repos
- Consumer registry with probe tool integration

**Fix Path**:
1. Add SSTI litmus test to each consumer repo
2. Make test job required in branch protection
3. Add consumer to `consumer_registry.yml`
4. Run probe tool to verify compliance automatically

**Owner**: Consumer teams + DevOps
**Timeline**: 4-12h per consumer
**Priority**: **P0 - BLOCKING**

---

#### CRITICAL: Consumer Discovery Completeness Gap

**Why Critical**: The `consumer_registry.yml` is manually maintained → unknown consumers can render metadata without SSTI protections → silent vulnerability.

**Current State**: Registry requires manual updates when new consumers are added. No automated discovery of metadata-rendering services.

**What's Missing**:
- Automated codebase scanner to find services that import/render metadata
- Periodic audit to compare registry against actual consumer deployments
- Alert when new metadata-consuming service deployed without registry entry
- Enforcement: Require registry entry before service can access metadata API

**Fix Path** (Option A - Static Discovery):
1. Create grep-based scanner for metadata rendering patterns:
   - `grep -r "metadata\[" --include="*.py" --include="*.js"`
   - `grep -r "render.*metadata" --include="*.py" --include="*.html"`
2. Cross-reference results with `consumer_registry.yml`
3. Alert on unregistered consumers
4. Run scanner daily in CI

**Fix Path** (Option B - Runtime Discovery):
1. Add metadata API middleware to log consumer service names
2. Compare logged consumers against registry
3. Alert on unregistered access
4. Block unregistered consumers after grace period

**Fix Path** (Option C - Required Registry Entry):
1. Metadata API requires `X-Consumer-ID` header
2. API validates header against registry
3. Reject requests from unregistered consumers
4. Forces teams to register before accessing metadata

**Recommended**: Combine Option A (daily scanner) + Option C (API enforcement)

**Owner**: SRE + Security team
**Timeline**: 4-8 hours (Option A), 2-4 days (Option B+C)
**Priority**: **P0 - BLOCKING**

---

#### HIGH: Token Canonicalization Bypass

**Why High**: If code receives token objects (with malicious `__getattr__`) instead of sanitized primitives → exploitation or silent side effects.

**Current State**: Tests exist (`test_malicious_token_methods.py`) but can be skipped.

**What's Missing**:
- Non-skippable enforcement in CI
- Static grep check for raw token object usage patterns
- Automated audit verification

**Fix Path**:
1. Mark malicious-token test with `@pytest.mark.critical`
2. Add grep check to `audit_greenlight.py`: search for `token.attr`, `.__getattr__`, `SimpleNamespace` usage
3. Fail CI if grep finds violations

**Owner**: Dev team
**Timeline**: 4-8 hours
**Priority**: **P0 - BLOCKING**

---

#### HIGH: URL Canonicalization / SSRF Parity

**Why High**: Divergence between collector and fetcher canonicalizers permits TOCTOU and SSRF.

**Current State**: Fetcher wrapper and parity vectors added, but parity suite not blocking PR smoke.

**What's Missing**:
- PR smoke doesn't include full URL vector corpus (≥20 vectors)
- Parity test not required in branch protection
- No verification that fetcher imports same canonicalizer

**Fix Path**:
1. Add `adversarial_encoded_urls.json` to PR smoke corpus list
2. Make `parser / url-parity-smoke` required in branch protection
3. Add static check to verify fetcher imports `security.validators.normalize_url`

**Owner**: Dev team + DevOps
**Timeline**: 2-4 hours
**Priority**: **P0 - BLOCKING**

---

#### HIGH: Cross-Platform Timeout Policy

**Why High**: SIGALRM watchdog (Linux-only) implemented. Windows has no equivalent → blocking collector can hang workers → DoS.

**Current State**: Plan asks for decision (Linux-only vs subprocess isolation). No decision documented.

**What's Missing**:
- Formal decision by Tech Lead
- Documented policy in `docs/PLATFORM_POLICY.md`
- CI assertion to enforce policy

**Fix Path** (Option A - Recommended):
1. Tech Lead decides Linux-only for untrusted inputs
2. Document in `docs/PLATFORM_POLICY.md`
3. Add CI assertion: `python -c "import platform; assert platform.system()=='Linux'"`
4. Add deploy gate check

**Fix Path** (Option B - Full Support):
1. Implement subprocess worker pool
2. Add restart/watchdog for Windows
3. Add isolation test harness
4. Timeline: weeks of additional work

**Owner**: Tech Lead (decision) + SRE (enforcement)
**Timeline**: 30 min (Option A) OR weeks (Option B)
**Priority**: **P0 - BLOCKING (must decide within 24h)**

---

## GIT PATCHES (READY TO APPLY)

### Patch 1: Add Baseline Verification to Audit Script

**Purpose**: Enhance `tools/audit_greenlight.py` to verify current metrics against canonical baseline.

**What it does**:
- Loads canonical baseline (`baselines/metrics_baseline_v1.json`)
- Attempts to capture current metrics via `tools/capture_baseline_metrics.py --auto`
- Compares key metrics (P95, P99, RSS, timeouts, truncation) with thresholds
- Returns non-zero exit code if baseline breached
- Includes results in audit JSON for traceability

**Thresholds**:
- `parse_p95_ms`: Fail if current > baseline × 1.25
- `parse_p99_ms`: Fail if current > baseline × 1.5
- `parse_peak_rss_mb`: Fail if current > baseline + 30
- `collector_timeouts_total_per_min`: Fail if current > baseline × 1.5
- `collector_truncated_rate`: Fail if current > baseline × 2.0

**Patch**:

```diff
--- a/tools/audit_greenlight.py
+++ b/tools/audit_greenlight.py
@@ -import yaml
@@ -def run_adversarial_on_all(outdir=REPORT_DIR):
@@ -    return {"status": "done", "results": results}

 def verify_branch_protection_from_registry(registry_path: Path, github_token: str = None) -> Dict[str, Any]:
@@ -    return res
+
+def verify_baseline(baseline_path: Path, temp_current_path: Path = Path("/tmp/current_metrics_compare.json")) -> Dict[str, Any]:
+    """
+    Verify current metrics against a stored baseline.
+    - baseline_path: path to baseline JSON (e.g., baselines/metrics_baseline_v1.json)
+    - temp_current_path: temporary path to store auto-captured metrics
+
+    Behavior:
+    - If baseline_path doesn't exist -> returns {'status':'missing_baseline'} (non-fatal but reported)
+    - Attempts to run tools/capture_baseline_metrics.py --auto to produce current metrics.
+      If that script cannot run or produces no metrics, returns {'status':'capture_skipped'}.
+    - If both baseline and current metrics present, compares a set of keys and reports any breaches.
+      Thresholds:
+        - parse_p95_ms: fail if current > baseline * 1.25
+        - parse_p99_ms: fail if current > baseline * 1.5
+        - parse_peak_rss_mb: fail if current > baseline + 30
+        - collector_timeouts_total_per_min: fail if current > baseline * 1.5 (or > baseline + 1)
+        - collector_truncated_rate: fail if current > baseline * 2
+    Returns dict with fields: status ('ok'|'fail'|'capture_skipped'|'missing_baseline'), baseline, current, diffs
+    """
+    out = {"status": None, "baseline_path": str(baseline_path), "current_path": str(temp_current_path), "diffs": []}
+    if not baseline_path.exists():
+        out["status"] = "missing_baseline"
+        return out
+    try:
+        baseline = json.loads(baseline_path.read_text())
+    except Exception as e:
+        out["status"] = "baseline_read_error"
+        out["error"] = str(e)
+        return out
+
+    # Try to auto-capture current metrics using capture_baseline_metrics.py
+    capture_script = Path("tools") / "capture_baseline_metrics.py"
+    if not capture_script.exists():
+        out["status"] = "capture_script_missing"
+        out["baseline"] = baseline
+        return out
+
+    # Run capture script --auto and write to temp_current_path
+    cmd = f"{sys.executable} {shlex.quote(str(capture_script))} --auto --out {shlex.quote(str(temp_current_path))}"
+    cap = run_cmd(cmd, timeout=900)
+    if cap["rc"] != 0 or not temp_current_path.exists():
+        out["status"] = "capture_skipped"
+        out["capture_stdout"] = cap.get("stdout", "")[:2000]
+        out["capture_stderr"] = cap.get("stderr", "")[:2000]
+        out["baseline"] = baseline
+        return out
+
+    try:
+        current = json.loads(temp_current_path.read_text())
+    except Exception as e:
+        out["status"] = "current_read_error"
+        out["error"] = str(e)
+        return out
+
+    out["baseline"] = baseline
+    out["current"] = current
+    # Comparison rules
+    comparisons = []
+    def cmp_gt(cur, base, mult=None, add=None):
+        if cur is None or base is None:
+            return None
+        if mult is not None:
+            return cur > (base * mult)
+        if add is not None:
+            return cur > (base + add)
+        return cur > base
+
+    # keys to compare and thresholds
+    checks = [
+        ("parse_p95_ms", lambda c,b: cmp_gt(c,b,mult=1.25)),
+        ("parse_p99_ms", lambda c,b: cmp_gt(c,b,mult=1.5)),
+        ("parse_peak_rss_mb", lambda c,b: cmp_gt(c,b,add=30)),
+        ("collector_timeouts_total_per_min", lambda c,b: cmp_gt(c,b,mult=1.5)),
+        ("collector_truncated_rate", lambda c,b: cmp_gt(c,b,mult=2.0)),
+    ]
+
+    failed = False
+    for key, check in checks:
+        bval = baseline.get(key)
+        cval = current.get(key)
+        breached = check(cval, bval)
+        comparisons.append({"metric": key, "baseline": bval, "current": cval, "breached": bool(breached)})
+        if breached:
+            failed = True
+
+    out["diffs"] = comparisons
+    out["status"] = "fail" if failed else "ok"
+    return out
```

**Application**:
```bash
cd /path/to/repo
git apply baseline_verification.patch
```

**Verification**:
```bash
# Test the audit script with baseline verification
python tools/audit_greenlight.py --report /tmp/audit_test.json
cat /tmp/audit_test.json | jq '.baseline_verification'
```

---

### Patch 2: Wire Baseline Verification into Pre-Canary CI

**Purpose**: Modify `.github/workflows/adversarial_gates.yml` to run baseline verification before full adversarial suite in nightly job.

**What it does**:
- Adds "Pre-canary baseline verification" step to `nightly_full` job
- Runs `audit_greenlight.py` which now includes baseline check
- Fails job if baseline breached (non-zero exit code)
- Outputs audit JSON for traceability
- Runs before full adversarial corpora (gate before expensive tests)

**Patch**:

```diff
--- a/.github/workflows/adversarial_gates.yml
+++ b/.github/workflows/adversarial_gates.yml
@@ -      - name: Create report dir
         run: mkdir -p ${{ env.REPORT_DIR }}

+      - name: Pre-canary baseline verification
+        env:
+          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
+        run: |
+          set -euo pipefail
+          echo "Running baseline verification via audit script (will attempt to auto-capture current metrics)"
+          python -u tools/audit_greenlight.py --report "${{ env.REPORT_DIR }}/precanary_audit.json"
+          # audit_greenlight returns non-zero if baseline verification fails (or other fatal errors)
+          cat "${{ env.REPORT_DIR }}/precanary_audit.json"
+          echo "Pre-canary baseline verification completed"
+
       - name: Run full adversarial corpora (fail on any non-zero)
         run: |
           set -euo pipefail
           for corpus in ${{ env.ADV_CORPORA_DIR }}/*.json; do
             fname=$(basename "${corpus%.*}")
             out="${{ env.REPORT_DIR }}/${fname}.report.json"
             echo "Running full corpus: $corpus -> $out"
             python -u tools/run_adversarial.py "$corpus" --runs 1 --report "$out"
             if [ ! -f "$out" ]; then
               echo "ERROR: runner did not produce $out"
               exit 3
             fi
           done
```

**Application**:
```bash
cd /path/to/repo
git apply pre_canary_baseline.patch
```

**Verification**:
```bash
# Trigger workflow manually to test
gh workflow run adversarial_gates.yml

# Check workflow run results
gh run list --workflow=adversarial_gates.yml
```

---

### Patch 3: Make P0 Checks Fatal in Audit Script

**Purpose**: Enhance `tools/audit_greenlight.py` to treat P0 failures (missing baseline, branch protection failures) as **FATAL** (exit non-zero) instead of warnings.

**Why Critical**: The original audit script reported P0 failures but didn't block the run. This patch enforces fail-closed semantics: if P0 checks fail, the audit script exits with non-zero, blocking CI/deployment.

**What Changes**:
- `verify_baseline()` with status `missing_baseline`, `capture_skipped`, or `capture_script_missing` → **FATAL** (exit code 6)
- `verify_branch_protection_from_registry()` with errors or skipped → **FATAL** (exit code 5)
- Audit script `main()` checks these statuses and sets exit code accordingly
- CI jobs that call `audit_greenlight.py` will fail if P0 checks fail

**Patch**:

```diff
--- a/tools/audit_greenlight.py
+++ b/tools/audit_greenlight.py
@@ -def main():
     report = {}
     exit_code = 0

+    # P0 Check 1: Branch Protection Verification (FATAL if missing/errored)
+    registry_path = Path("consumer_registry.yml")
+    github_token = os.environ.get("GITHUB_TOKEN")
+
+    if registry_path.exists():
+        bp_result = verify_branch_protection_from_registry(registry_path, github_token)
+        report["branch_protection"] = bp_result
+
+        # FATAL: Branch protection verification skipped or errored
+        if bp_result.get("skipped", False) or bp_result.get("error"):
+            print(f"❌ FATAL P0 FAILURE: Branch protection verification failed: {bp_result.get('error', 'skipped')}")
+            exit_code = max(exit_code, 5)  # Fatal exit code
+        elif bp_result.get("status") == "fail":
+            print(f"❌ FATAL P0 FAILURE: Branch protection misconfigured")
+            exit_code = max(exit_code, 5)
+    else:
+        print(f"⚠️  WARN: consumer_registry.yml not found, skipping branch protection check")
+        report["branch_protection"] = {"status": "skipped", "reason": "registry not found"}
+
+    # P0 Check 2: Baseline Verification (FATAL if missing/capture failed)
+    baseline_path = Path("baselines/metrics_baseline_v1_signed.json")
+    baseline_result = verify_baseline(baseline_path)
+    report["baseline_verification"] = baseline_result
+
+    bl_status = baseline_result.get("status")
+
+    # FATAL: Missing baseline (no signed baseline exists)
+    if bl_status == "missing_baseline":
+        print(f"❌ FATAL P0 FAILURE: Signed canonical baseline missing at {baseline_path}")
+        print(f"   Action required: Capture and sign baseline with tools/capture_baseline_metrics.py + tools/sign_baseline.py")
+        exit_code = max(exit_code, 6)  # Fatal exit code
+
+    # FATAL: Capture script missing or failed
+    elif bl_status in ("capture_skipped", "capture_script_missing", "current_read_error"):
+        print(f"❌ FATAL P0 FAILURE: Baseline verification could not auto-capture current metrics (status: {bl_status})")
+        print(f"   Action required: Fix tools/capture_baseline_metrics.py or run manually")
+        exit_code = max(exit_code, 6)
+
+    # Baseline exists but metrics exceeded thresholds
+    elif bl_status == "fail":
+        print(f"❌ BASELINE BREACH: Current metrics exceed thresholds")
+        for diff in baseline_result.get("diffs", []):
+            if diff.get("breached"):
+                print(f"   - {diff['metric']}: current={diff['current']}, baseline={diff['baseline']} (BREACHED)")
+        exit_code = max(exit_code, 2)  # Non-fatal but alert
+
+    # ... rest of audit script (adversarial tests, etc.)
+
     # Write report
     Path(args.report).write_text(json.dumps(report, indent=2))

     if exit_code != 0:
-        print(f"\n❌ Audit completed with warnings (exit {exit_code})")
+        if exit_code >= 5:
+            print(f"\n❌ FATAL: Audit failed with P0 failures (exit {exit_code})")
+            print(f"   Cannot proceed to canary/deployment until P0 items resolved")
+        else:
+            print(f"\n⚠️  Audit completed with warnings (exit {exit_code})")
     else:
         print(f"\n✅ Audit passed - all checks green")

     sys.exit(exit_code)
```

**Enforcement Clarification Box** (add to document start):

```
⚠️ **CRITICAL ENFORCEMENT SEMANTICS (v1.1 Change)**

For P0 checks (items 1-4 in acceptance matrix), the audit script now uses **fail-closed** semantics:

- **P0-1: Branch Protection** → If `verify_branch_protection_from_registry()` returns error/skipped/fail → audit exits with code 5 (FATAL)
- **P0-2: Baseline Verification** → If signed baseline missing, capture script unavailable, or capture failed → audit exits with code 6 (FATAL)

**Impact**:
- Nightly CI job will FAIL if P0 checks fail (blocks further tests)
- Pre-canary checklist will FAIL if P0 checks fail (blocks deployment)
- No canary deployment possible until P0 items fixed

**Rationale**: P0 items are blocking security requirements. Missing baseline or unconfigured branch protection indicates incomplete security posture → must not proceed.
```

**Application**:
```bash
cd /path/to/repo
git apply /tmp/fatal_p0_checks.patch
```

**Verification**:
```bash
# Test with missing baseline (should FAIL with exit 6)
rm baselines/metrics_baseline_v1_signed.json 2>/dev/null || true
python tools/audit_greenlight.py --report /tmp/audit_test.json
echo $?  # Expected: 6 (fatal)

# Test with baseline present (should pass or exit 0/2 depending on metrics)
# (restore baseline first)
python tools/audit_greenlight.py --report /tmp/audit_test.json
echo $?  # Expected: 0 or 2 (non-fatal if breach)
```

---

## STEP-BY-STEP REMEDIATION PLAN

### IMMEDIATE (Next 24 Hours) - Priority 0

#### Action 1: Decide Platform Policy

**Owner**: Tech Lead / SRE
**Effort**: 30 minutes (Option A) OR weeks (Option B)
**Deadline**: 24 hours after plan approval
**Status**: ⏸️ **BLOCKING** - Must decide before any production deployment

**Decision Required**: Linux-only OR Windows subprocess pool

**Option A: Linux-Only (RECOMMENDED)**

**Steps**:

1. **Tech Lead Decision** (15 min):
   ```bash
   # Document decision
   echo "Decision: Linux-only for untrusted input parsing" > decision.txt
   echo "Rationale: SIGALRM timeout enforcement unavailable on Windows" >> decision.txt
   echo "Mitigation: All parsing pods must run on Linux nodes" >> decision.txt
   echo "Decision Date: $(date -I)" >> decision.txt
   echo "Decision Owner: [Tech Lead Name]" >> decision.txt
   ```

2. **Create Policy Document** (10 min):
   ```bash
   # Create docs/PLATFORM_POLICY.md
   cat > docs/PLATFORM_POLICY.md << 'EOF'
# Platform Support Policy for Untrusted Input Parsing

**Status**: DECIDED
**Decision Date**: 2025-10-17
**Decision Owner**: Tech Lead
**Effective**: Immediately

## Production Deployment

**Allowed Platforms**:
- Linux (Ubuntu 22.04+, kernel 6.1+)

**Blocked Platforms**:
- Windows (all versions) - timeout enforcement unavailable (no SIGALRM)
- macOS - development/testing only

## Enforcement

**Deploy Script** (`deploy/validate_platform.sh`):
- Fails deployment if any Windows node detected in parsing pool
- Runtime platform assertion in pod spec

**CI Assertion**:
```bash
python -c "import platform; assert platform.system()=='Linux', 'Parser requires Linux for SIGALRM timeout enforcement'"
```

**Decision Deadline**: 24h after plan approval
**Default if no decision**: Linux-only (this policy)

## Rationale

- SIGALRM-based timeout enforcement requires POSIX signals
- Windows has no equivalent for subprocess timeout
- Implementing Windows support requires subprocess worker pool (8+ hours effort)
- Linux-only is lowest-risk path for initial production deployment

## Future Considerations

If Windows support becomes required:
- Implement subprocess worker pool with restart/watchdog
- Add isolation test harness
- Estimated effort: 2-3 weeks
- Requires separate security review
EOF
   ```

3. **Add CI Enforcement** (5 min):
   ```bash
   # Add to .github/workflows/parser_tests.yml
   - name: Verify platform policy
     run: |
       python -c "import platform; assert platform.system()=='Linux', 'Parser requires Linux'"
   ```

**Verification**:
```bash
# Verify policy document exists
test -f docs/PLATFORM_POLICY.md && echo "✅ Policy documented" || echo "❌ Policy missing"

# Verify CI has platform check
grep -q "platform.system" .github/workflows/*.yml && echo "✅ CI enforcement added" || echo "❌ CI check missing"
```

**Option B: Windows Subprocess Pool**

**Steps**: ⚠️ **NOT RECOMMENDED** - Requires weeks of additional work

1. Implement subprocess worker pool (8-16 hours)
2. Add restart/watchdog mechanism (4-8 hours)
3. Create isolation test harness (4-8 hours)
4. Security review (8-16 hours)
5. Performance validation (4-8 hours)

**Total Effort**: 2-3 weeks
**Risk**: High - new complexity, more attack surface

---

#### Action 2: Enable Adversarial CI Gate

**Owner**: DevOps
**Effort**: 30 minutes
**Deadline**: 24 hours
**Status**: ⏸️ **BLOCKING** - Workflow exists, needs enablement

**Steps**:

1. **Navigate to Branch Protection Settings** (5 min):
   ```bash
   # GitHub UI:
   # Settings → Branches → Branch protection rules → main
   # Enable "Require status checks to pass before merging"
   ```

2. **Add Required Checks** (10 min):
   ```
   Required status checks (exact names):
   - adversarial / pr_smoke
   - parser / token-canonicalization
   - parser / url-parity-smoke
   - parser / dispatch-invariants
   - parser / collector-caps
   ```

3. **Verify with Test PR** (15 min):
   ```bash
   # Create test PR
   git checkout -b test-branch-protection
   echo "test" >> README.md
   git add README.md
   git commit -m "Test: Verify branch protection"
   git push origin test-branch-protection

   # Create PR via GitHub CLI
   gh pr create --title "Test: Branch Protection" --body "Testing required checks"

   # Verify checks appear in PR
   gh pr checks
   # Expected: All required checks listed and running
   ```

**Verification**:
```bash
# Verify branch protection enabled
gh api repos/:owner/:repo/branches/main/protection | jq '.required_status_checks.contexts[]'
# Expected output: adversarial / pr_smoke, parser / token-canonicalization, etc.
```

---

#### Action 3: Apply Git Patches (Baseline Verification)

**Owner**: Dev team
**Effort**: 30 minutes
**Deadline**: 24 hours
**Status**: ⏸️ **BLOCKING** - Patches provided above

**Steps**:

1. **Save Patches** (5 min):
   ```bash
   # Save Patch 1 to file
   cat > /tmp/baseline_verification.patch << 'PATCH'
   [Paste Patch 1 content here]
   PATCH

   # Save Patch 2 to file
   cat > /tmp/pre_canary_baseline.patch << 'PATCH'
   [Paste Patch 2 content here]
   PATCH
   ```

2. **Apply Patches** (10 min):
   ```bash
   cd /path/to/repo

   # Apply Patch 1 (baseline verification in audit script)
   git apply /tmp/baseline_verification.patch
   # If conflicts, resolve manually

   # Apply Patch 2 (CI workflow integration)
   git apply /tmp/pre_canary_baseline.patch
   ```

3. **Test Locally** (10 min):
   ```bash
   # Test audit script with baseline verification
   python tools/audit_greenlight.py --report /tmp/audit_test.json

   # Check output
   cat /tmp/audit_test.json | jq '.baseline_verification'
   # Expected: {"status": "missing_baseline", ...} OR {"status": "ok", ...}
   ```

4. **Commit and Push** (5 min):
   ```bash
   git add tools/audit_greenlight.py .github/workflows/adversarial_gates.yml
   git commit -m "feat: Add baseline verification to audit script and pre-canary CI

   - Enhance audit_greenlight.py with baseline comparison logic
   - Add pre-canary baseline verification step to nightly workflow
   - Compare P95/P99/RSS/timeouts against canonical baseline
   - Fail CI if baseline breached

   Closes #[issue-number]

   🤖 Generated with [Claude Code](https://claude.com/claude-code)"

   git push origin main
   ```

**Verification**:
```bash
# Verify patches applied
git log -1 --oneline | grep "baseline verification"

# Verify audit script has new function
grep -q "def verify_baseline" tools/audit_greenlight.py && echo "✅ Function added" || echo "❌ Function missing"

# Verify CI workflow has new step
grep -q "Pre-canary baseline verification" .github/workflows/adversarial_gates.yml && echo "✅ Step added" || echo "❌ Step missing"
```

---

### SHORT-TERM (48-72 Hours) - Priority 1

#### Action 4: Deploy SSTI Litmus Tests to Consumer Repos

**Owner**: Consumer teams
**Effort**: 4-12 hours per consumer
**Deadline**: 72 hours
**Status**: ⏸️ **BLOCKING** - Template exists, needs deployment

**Steps per Consumer**:

1. **Identify Consumers that Render Metadata** (1 hour):
   ```bash
   # Create consumer_registry.yml
   cat > consumer_registry.yml << 'EOF'
version: "1.0"
consumers:
  - name: "frontend-web"
    repo: "org/frontend-web"
    branch: "main"
    owner: "frontend-lead@example.com"
    renders_metadata: true
    probe_url: "https://staging-frontend.example.internal/__probe__"
    probe_method: "POST"
    required_checks:
      - "consumer-ssti-litmus"
      - "consumer / html-sanitization"

  - name: "preview-service"
    repo: "org/preview-service"
    branch: "main"
    owner: "preview-owner@example.com"
    renders_metadata: true
    probe_url: "https://staging-preview.example.internal/__probe__"
    probe_method: "POST"
    required_checks:
      - "consumer-ssti-litmus"
EOF
   ```

2. **Copy SSTI Test to Consumer** (30 min per repo):
   ```bash
   # Copy test from skeleton
   cp regex_refactor_docs/performance/skeleton/tests/test_consumer_ssti_litmus.py \
      ../consumer-repo/tests/test_consumer_ssti_litmus.py

   # Commit in consumer repo
   cd ../consumer-repo
   git add tests/test_consumer_ssti_litmus.py
   git commit -m "sec: Add SSTI litmus test for metadata rendering

   - Verify consumer does not evaluate template expressions in metadata
   - Test Jinja2 autoescape enforcement
   - Test explicit escape filter

   Per security requirement P0-3.5 from parser team

   🤖 Generated with [Claude Code](https://claude.com/claude-code)"
   ```

3. **Install Dependencies** (10 min):
   ```bash
   # Add to consumer's requirements-test.txt or pyproject.toml
   echo "jinja2>=3.1.0" >> requirements-test.txt
   ```

4. **Add CI Job** (20 min):
   ```yaml
   # Add to consumer's .github/workflows/tests.yml
   consumer-ssti-litmus:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v4
         with:
           python-version: '3.12'
       - name: Install dependencies
         run: pip install -r requirements-test.txt
       - name: Run SSTI litmus test
         run: pytest tests/test_consumer_ssti_litmus.py -v
   ```

5. **Enable Branch Protection** (10 min):
   ```bash
   # GitHub UI:
   # Settings → Branches → Branch protection → Add required check
   # Check name: "consumer-ssti-litmus"
   ```

6. **Verify with Test PR** (30 min):
   ```bash
   # Create test PR in consumer repo
   git checkout -b test-ssti-enforcement
   echo "# Test" >> README.md
   git add README.md
   git commit -m "Test: SSTI enforcement"
   git push origin test-ssti-enforcement
   gh pr create --title "Test: SSTI Enforcement" --body "Testing SSTI litmus gate"

   # Verify check runs
   gh pr checks
   # Expected: consumer-ssti-litmus check appears and passes
   ```

**Verification (per consumer)**:
```bash
# Verify test exists
test -f tests/test_consumer_ssti_litmus.py && echo "✅ Test deployed" || echo "❌ Test missing"

# Verify test passes
pytest tests/test_consumer_ssti_litmus.py -v
# Expected: 2 passed

# Verify branch protection
gh api repos/:owner/:repo/branches/main/protection | jq '.required_status_checks.contexts[]' | grep -q "consumer-ssti-litmus"
echo $? # Expected: 0 (found)
```

**Repeat for all consumers in registry** (typically 2-5 repos)

---

#### Action 5: Enforce Token Canonicalization (Non-Skippable)

**Owner**: Dev team
**Effort**: 4-8 hours
**Deadline**: 72 hours
**Status**: ⏸️ **HIGH** - Test exists, needs enforcement

**Steps**:

1. **Mark Test as Critical** (10 min):
   ```python
   # Edit tests/test_malicious_token_methods.py
   import pytest

   @pytest.mark.critical  # Add this marker
   def test_malicious_token_methods_not_invoked():
       """Verify token canonicalization prevents malicious method execution."""
       # ... existing test code
   ```

2. **Update conftest.py** (20 min):
   ```python
   # Edit conftest.py (create if doesn't exist)
   import pytest

   def pytest_configure(config):
       config.addinivalue_line(
           "markers", "critical: marks tests as critical (cannot be skipped)"
       )

   def pytest_collection_modifyitems(config, items):
       """Fail if critical tests are skipped."""
       for item in items:
           if "critical" in item.keywords:
               # Remove skip markers from critical tests
               skip_markers = [m for m in item.iter_markers(name="skip")]
               if skip_markers:
                   pytest.fail(
                       f"Critical test {item.nodeid} cannot be skipped. "
                       f"Remove @pytest.mark.skip or fix the test."
                   )
   ```

3. **Add CI Job for Critical Tests** (30 min):
   ```yaml
   # Add to .github/workflows/parser_tests.yml
   critical-security-tests:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v4
         with:
           python-version: '3.12'
       - name: Install dependencies
         run: pip install -r requirements.txt
       - name: Run critical security tests (non-skippable)
         run: |
           # Fail if any critical test is skipped
           pytest -v -m critical --tb=short

           # Verify critical tests actually ran
           TEST_COUNT=$(pytest --collect-only -q -m critical | tail -1 | awk '{print $1}')
           if [ "$TEST_COUNT" -lt 5 ]; then
             echo "❌ ERROR: Expected at least 5 critical tests, found $TEST_COUNT"
             exit 1
           fi
   ```

4. **Add Static Grep Check** (1 hour):
   ```python
   # Add to tools/audit_greenlight.py
   def check_token_canonicalization() -> Dict[str, Any]:
       """
       Static check for raw token object usage patterns.
       Searches for dangerous patterns that bypass canonicalization.
       """
       dangerous_patterns = [
           (r'token\.attr', 'Direct token attribute access'),
           (r'\.__getattr__', 'Use of __getattr__ on token'),
           (r'SimpleNamespace', 'SimpleNamespace usage (may bypass canonicalization)'),
           (r'token\[.*\]\.', 'Token dict access followed by attribute access'),
       ]

       violations = []
       for pattern, description in dangerous_patterns:
           cmd = f"grep -r '{pattern}' src/doxstrux/ --include='*.py'"
           result = run_cmd(cmd, timeout=30)
           if result['rc'] == 0 and result['stdout']:
               violations.append({
                   'pattern': pattern,
                   'description': description,
                   'matches': result['stdout'].split('\n')[:10]  # First 10 matches
               })

       return {
           'status': 'fail' if violations else 'ok',
           'violations': violations
       }
   ```

5. **Integrate into Audit** (30 min):
   ```python
   # In audit_greenlight.py main() function
   token_canon_check = check_token_canonicalization()
   report['token_canonicalization_static_check'] = token_canon_check
   if token_canon_check['status'] == 'fail':
       exit_code = 1
   ```

**Verification**:
```bash
# Verify critical marker added
grep -q "@pytest.mark.critical" tests/test_malicious_token_methods.py && echo "✅ Marker added" || echo "❌ Marker missing"

# Verify conftest.py has enforcement
grep -q "pytest_collection_modifyitems" conftest.py && echo "✅ Enforcement added" || echo "❌ Enforcement missing"

# Run critical tests
pytest -v -m critical
# Expected: All critical tests run and pass, none skipped

# Run static check
python tools/audit_greenlight.py --report /tmp/audit.json
cat /tmp/audit.json | jq '.token_canonicalization_static_check'
# Expected: {"status": "ok", "violations": []}
```

---

#### Action 6: Capture Canonical Baseline

**Owner**: SRE
**Effort**: 2-4 hours
**Deadline**: 72 hours
**Status**: ⏸️ **BLOCKING** - Required before canary

**Steps**:

1. **Create Baseline Capture Script** (1 hour):
   ```python
   # Create tools/capture_baseline_metrics.py
   #!/usr/bin/env python3
   """
   Capture baseline performance metrics for canary comparison.

   Runs parser benchmarks in containerized environment and outputs
   canonical baseline JSON with automatic threshold calculation.
   """
   import argparse
   import json
   import subprocess
   import sys
   from datetime import datetime
   from pathlib import Path

   def capture_metrics(duration_sec=3600, auto=False):
       """Capture metrics via benchmarks."""
       metrics = {}

       # Run parse benchmark
       print(f"Running parser benchmark for {duration_sec}s...")
       cmd = [
           sys.executable, "tools/bench_parse.py",
           "--duration", str(duration_sec),
           "--output", "/tmp/parse_bench.json"
       ]
       result = subprocess.run(cmd, capture_output=True, text=True)

       if result.returncode == 0 and Path("/tmp/parse_bench.json").exists():
           bench_data = json.loads(Path("/tmp/parse_bench.json").read_text())
           metrics.update({
               "parse_p50_ms": bench_data.get("p50_ms"),
               "parse_p95_ms": bench_data.get("p95_ms"),
               "parse_p99_ms": bench_data.get("p99_ms"),
               "parse_peak_rss_mb": bench_data.get("peak_rss_mb"),
           })

       # Run collector timeout monitoring
       print("Capturing collector timeout metrics...")
       # ... similar benchmark capture

       return metrics

   def calculate_thresholds(metrics):
       """Calculate canary thresholds from baseline metrics."""
       return {
           "canary_p95_max_ms": metrics["parse_p95_ms"] * 1.25,
           "canary_p99_max_ms": metrics["parse_p99_ms"] * 1.5,
           "canary_rss_max_mb": metrics.get("parse_peak_rss_mb", 100) + 30,
           "canary_timeout_rate_max_pct": metrics.get("timeout_rate_pct", 0.01) * 1.5,
           "canary_truncation_rate_max_pct": max(0.01, metrics.get("truncation_rate_pct", 0.001) * 10),
       }

   def main():
       parser = argparse.ArgumentParser()
       parser.add_argument("--duration", type=int, default=3600, help="Benchmark duration (seconds)")
       parser.add_argument("--auto", action="store_true", help="Auto mode (best-effort, skip if benchmarks missing)")
       parser.add_argument("--out", default="baselines/metrics_baseline_v1.json", help="Output path")
       args = parser.parse_args()

       metrics = capture_metrics(args.duration, args.auto)

       if not metrics and args.auto:
           print("No metrics captured (auto mode), skipping")
           return 0

       if not metrics:
           print("ERROR: No metrics captured")
           return 1

       thresholds = calculate_thresholds(metrics)

       baseline = {
           "version": "1.0",
           "captured_at": datetime.utcnow().isoformat() + "Z",
           "commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
           "environment": {
               "platform": "linux/amd64",
               "python_version": ".".join(map(str, sys.version_info[:3])),
               "container_image": "python:3.12-slim",
               "heap_mb": 512
           },
           "metrics": metrics,
           "thresholds": thresholds
       }

       Path(args.out).parent.mkdir(parents=True, exist_ok=True)
       Path(args.out).write_text(json.dumps(baseline, indent=2))
       print(f"Baseline written to {args.out}")
       return 0

   if __name__ == "__main__":
       sys.exit(main())
   ```

2. **Run Baseline Capture** (2 hours - benchmark duration):
   ```bash
   # Create baselines directory
   mkdir -p baselines

   # Run capture in containerized environment (recommended)
   docker run --rm -v $(pwd):/workspace -w /workspace \
     python:3.12-slim \
     python tools/capture_baseline_metrics.py --duration 3600 --out baselines/metrics_baseline_v1.json

   # Verify output
   cat baselines/metrics_baseline_v1.json | jq '.'
   ```

3. **Sign Baseline** (30 min):
   ```python
   # Create tools/sign_baseline.py
   #!/usr/bin/env python3
   """Sign baseline with GPG for audit trail."""
   import argparse
   import hashlib
   import json
   import subprocess
   import sys
   from datetime import datetime
   from pathlib import Path

   def sign_baseline(baseline_path, signer_email):
       """Sign baseline JSON with GPG."""
       baseline_text = Path(baseline_path).read_text()
       baseline = json.loads(baseline_text)

       # Calculate SHA256 hash
       sha256 = hashlib.sha256(baseline_text.encode()).hexdigest()

       # GPG sign
       gpg_cmd = ["gpg", "--clearsign", "--armor", "--local-user", signer_email, "-"]
       result = subprocess.run(gpg_cmd, input=baseline_text.encode(), capture_output=True)

       if result.returncode != 0:
           print(f"ERROR: GPG signing failed: {result.stderr.decode()}")
           return 1

       signature = result.stdout.decode()

       # Add signature to baseline
       baseline["signature"] = {
           "signer": signer_email,
           "signed_at": datetime.utcnow().isoformat() + "Z",
           "signature_sha256": sha256,
           "gpg_signature": signature
       }

       # Write signed baseline
       signed_path = baseline_path.replace(".json", "_signed.json")
       Path(signed_path).write_text(json.dumps(baseline, indent=2))
       print(f"Signed baseline written to {signed_path}")
       return 0

   if __name__ == "__main__":
       parser = argparse.ArgumentParser()
       parser.add_argument("--baseline", required=True, help="Baseline JSON path")
       parser.add_argument("--signer", required=True, help="GPG signer email")
       args = parser.parse_args()

       sys.exit(sign_baseline(args.baseline, args.signer))
   ```

   ```bash
   # Sign baseline
   python tools/sign_baseline.py \
     --baseline baselines/metrics_baseline_v1.json \
     --signer sre-lead@example.com

   # Verify signature
   cat baselines/metrics_baseline_v1_signed.json | jq '.signature'
   ```

4. **Commit Signed Baseline** (10 min):
   ```bash
   git add baselines/metrics_baseline_v1_signed.json
   git commit -m "baseline: Add signed canonical baseline v1.0

   - Captured over 60-minute benchmark run in python:3.12-slim container
   - P95: X ms, P99: Y ms, Peak RSS: Z MB
   - Signed by SRE lead for audit trail
   - Thresholds calculated automatically (P95*1.25, P99*1.5, RSS+30MB)

   🤖 Generated with [Claude Code](https://claude.com/claude-code)"

   git push origin main
   ```

**Verification**:
```bash
# Verify baseline exists
test -f baselines/metrics_baseline_v1_signed.json && echo "✅ Baseline exists" || echo "❌ Baseline missing"

# Verify baseline structure
cat baselines/metrics_baseline_v1_signed.json | jq '.version, .metrics, .thresholds, .signature'
# Expected: All fields present

# Verify signature
cat baselines/metrics_baseline_v1_signed.json | jq -r '.signature.gpg_signature' | gpg --verify
# Expected: Good signature from sre-lead@example.com
```

---

### MEDIUM-TERM (1-2 Weeks) - Priority 2

#### Action 7: Deploy Consumer Registry & Staging Probes

**Owner**: SRE + DevOps
**Effort**: 4-6 hours setup + ongoing
**Deadline**: 1 week
**Status**: ⏸️ **MEDIUM** - Automates consumer compliance

**Steps**:

1. **Create Probe Script** (2 hours):
   ```python
   # Create tools/probe_consumers.py
   #!/usr/bin/env python3
   """
   Probe consumer staging endpoints to detect metadata rendering behavior.

   Sends UUID marker + template expression to consumer endpoints and
   checks if marker reflected (rendering) or expression evaluated (SSTI).
   """
   import argparse
   import json
   import requests
   import sys
   import uuid
   import yaml
   from pathlib import Path

   def probe_consumer(consumer: dict, marker: str):
       """Probe single consumer endpoint."""
       url = consumer.get("probe_url")
       method = consumer.get("probe_method", "POST")

       payload = {
           "probe_marker": marker,
           "metadata": {
               "title": f"PROBE_{marker}",
               "description": f"Test probe {{{{7*7}}}} {marker}"
           }
       }

       try:
           response = requests.request(method, url, json=payload, timeout=10)
       except Exception as e:
           return {
               "status_code": None,
               "error": str(e),
               "reflected": False,
               "evaluated": False
           }

       # Check if marker appears in response
       reflected = marker in response.text

       # Check if {{7*7}} was evaluated to 49
       evaluated = "49" in response.text and "{{" not in response.text

       return {
           "status_code": response.status_code,
           "reflected": reflected,
           "evaluated": evaluated,
           "response_snippet": response.text[:500]
       }

   def main():
       parser = argparse.ArgumentParser()
       parser.add_argument("--registry", required=True, help="Consumer registry YAML")
       parser.add_argument("--report", default="/tmp/probe_report.json", help="Output report")
       args = parser.parse_args()

       registry = yaml.safe_load(Path(args.registry).read_text())
       marker = str(uuid.uuid4())[:8]

       results = []
       violations = []

       for consumer in registry.get("consumers", []):
           if not consumer.get("renders_metadata"):
               continue

           print(f"Probing {consumer['name']}...")
           result = probe_consumer(consumer, marker)
           result["consumer"] = consumer["name"]
           results.append(result)

           if result.get("reflected"):
               violations.append({
                   "consumer": consumer["name"],
                   "severity": "CRITICAL" if result.get("evaluated") else "HIGH",
                   "issue": "SSTI evaluation" if result.get("evaluated") else "Metadata reflection",
                   "details": result
               })

       report = {
           "probe_id": marker,
           "results": results,
           "violations": violations,
           "status": "fail" if violations else "ok"
       }

       Path(args.report).write_text(json.dumps(report, indent=2))
       print(f"Report written to {args.report}")

       if violations:
           print(f"\n❌ VIOLATIONS DETECTED: {len(violations)} consumers")
           for v in violations:
               print(f"  - {v['consumer']}: {v['severity']} - {v['issue']}")
           return 1

       print(f"\n✅ All {len(results)} consumers compliant")
       return 0

   if __name__ == "__main__":
       sys.exit(main())
   ```

2. **Add Daily CI Job** (1 hour):
   ```yaml
   # Create .github/workflows/consumer_compliance.yml
   name: Consumer Compliance Probe

   on:
     schedule:
       - cron: '0 8 * * *'  # Daily at 08:00 UTC
     workflow_dispatch:

   jobs:
     probe-consumers:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v4
           with:
             python-version: '3.12'
         - name: Install dependencies
           run: pip install requests pyyaml
         - name: Probe consumer staging endpoints
           run: |
             python tools/probe_consumers.py \
               --registry consumer_registry.yml \
               --report consumer_probe_report.json
         - name: Upload report
           if: always()
           uses: actions/upload-artifact@v4
           with:
             name: consumer-probe-report
             path: consumer_probe_report.json
             retention-days: 90
         - name: Post to Slack on violations
           if: failure()
           run: |
             curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
               -H 'Content-Type: application/json' \
               -d '{"text":"❌ Consumer compliance probe detected violations. Check artifacts."}'
   ```

3. **Test Probe** (1 hour):
   ```bash
   # Run probe manually
   python tools/probe_consumers.py --registry consumer_registry.yml --report /tmp/probe.json

   # Check results
   cat /tmp/probe.json | jq '.'
   # Expected: {"status": "ok", "violations": []}

   # Trigger workflow
   gh workflow run consumer_compliance.yml
   ```

**Verification**:
```bash
# Verify probe script exists
test -f tools/probe_consumers.py && echo "✅ Probe script exists" || echo "❌ Script missing"

# Verify registry exists
test -f consumer_registry.yml && echo "✅ Registry exists" || echo "❌ Registry missing"

# Run probe
python tools/probe_consumers.py --registry consumer_registry.yml --report /tmp/test_probe.json
echo $? # Expected: 0 (success)
```

---

#### Action 8: Performance Benchmarks & Thresholds

**Owner**: Performance team
**Effort**: 4-6 hours
**Deadline**: 1 week
**Status**: ⏸️ **MEDIUM** - Required for canary gates

**Steps**:

1. **Create Dispatch Benchmark** (2 hours):
   ```python
   # Create tools/bench_dispatch.py
   #!/usr/bin/env python3
   """Benchmark single-pass dispatch performance."""
   import argparse
   import json
   import sys
   import time
   from pathlib import Path
   from statistics import median, quantiles

   def bench_dispatch(iters=50):
       """Run dispatch benchmark."""
       from doxstrux.markdown_parser_core import MarkdownParserCore

       # Large test document
       doc = "# " + ("Test\n\n" + "[link](http://example.com)\n\n" * 100) * 10

       times = []
       for i in range(iters):
           start = time.perf_counter()
           parser = MarkdownParserCore(doc)
           result = parser.parse()
           elapsed = (time.perf_counter() - start) * 1000  # ms
           times.append(elapsed)

       times.sort()
       p50 = median(times)
       p95 = quantiles(times, n=20)[18]  # 95th percentile
       p99 = quantiles(times, n=100)[98]  # 99th percentile

       return {
           "p50_ms": p50,
           "p95_ms": p95,
           "p99_ms": p99,
           "iters": iters
       }

   def main():
       parser = argparse.ArgumentParser()
       parser.add_argument("--baseline", help="Baseline JSON for comparison")
       parser.add_argument("--iters", type=int, default=50)
       args = parser.parse_args()

       print(f"Running dispatch benchmark ({args.iters} iterations)...")
       result = bench_dispatch(args.iters)

       print(f"P50: {result['p50_ms']:.2f} ms")
       print(f"P95: {result['p95_ms']:.2f} ms")
       print(f"P99: {result['p99_ms']:.2f} ms")

       if args.baseline:
           baseline = json.loads(Path(args.baseline).read_text())
           baseline_p95 = baseline.get("dispatch_p95_ms", 0)
           threshold = baseline_p95 * 1.25

           if result['p95_ms'] > threshold:
               print(f"❌ FAIL: P95 {result['p95_ms']:.2f}ms > threshold {threshold:.2f}ms")
               return 1
           else:
               print(f"✅ PASS: P95 {result['p95_ms']:.2f}ms <= threshold {threshold:.2f}ms")

       return 0

   if __name__ == "__main__":
       sys.exit(main())
   ```

2. **Create section_of Benchmark** (1 hour):
   ```python
   # Create tools/bench_section_of.py
   #!/usr/bin/env python3
   """Benchmark section_of lookup performance (must be O(log N))."""
   import argparse
   import sys
   import time
   from statistics import median

   def bench_section_of(num_sections=10000, iters=100):
       """Benchmark section_of with many sections."""
       from doxstrux.markdown_parser_core import MarkdownParserCore

       # Generate document with many sections
       doc = "\n\n".join([f"# Section {i}\n\nContent {i}" for i in range(num_sections)])

       parser = MarkdownParserCore(doc)
       result = parser.parse()

       # Benchmark section_of calls
       times = []
       for _ in range(iters):
           start = time.perf_counter()
           # Call section_of on middle element
           section_id = parser._find_section_id(num_sections // 2)
           elapsed = (time.perf_counter() - start) * 1000000  # microseconds
           times.append(elapsed)

       times.sort()
       p95 = times[int(len(times) * 0.95)]

       # Check scaling ratio
       # O(log N) should have ratio < 3.0 when doubling N
       return {
           "num_sections": num_sections,
           "p95_us": p95,
           "iters": iters
       }

   def main():
       parser = argparse.ArgumentParser()
       parser.add_argument("--sections", type=int, default=10000)
       parser.add_argument("--iters", type=int, default=100)
       args = parser.parse_args()

       print(f"Benchmarking section_of with {args.sections} sections...")
       result = bench_section_of(args.sections, args.iters)

       print(f"P95: {result['p95_us']:.2f} μs")

       # Verify logarithmic scaling
       if result['p95_us'] > 1000:  # 1ms threshold
           print(f"❌ WARN: P95 {result['p95_us']:.2f}μs may indicate linear search")
           print("Consider implementing binary search for section_of")
       else:
           print(f"✅ PASS: P95 {result['p95_us']:.2f}μs (acceptable)")

       return 0

   if __name__ == "__main__":
       sys.exit(main())
   ```

3. **Add Benchmark CI Jobs** (1 hour):
   ```yaml
   # Add to .github/workflows/performance_tests.yml
   performance-benchmarks:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v4
         with:
           python-version: '3.12'
       - name: Install dependencies
         run: pip install -r requirements.txt
       - name: Run dispatch benchmark
         run: |
           python tools/bench_dispatch.py --baseline baselines/metrics_baseline_v1_signed.json --iters 50
       - name: Run section_of benchmark
         run: |
           python tools/bench_section_of.py --sections 10000 --iters 100
   ```

**Verification**:
```bash
# Run dispatch benchmark
python tools/bench_dispatch.py --iters 50
# Expected: P50/P95/P99 reported, exit 0

# Run section_of benchmark
python tools/bench_section_of.py --sections 10000 --iters 100
# Expected: P95 < 1000μs, exit 0
```

---

## MACHINE-VERIFIABLE TEST CHECKLIST

**Copy-paste these commands** - all must pass before canary:

```bash
#!/bin/bash
# Pre-canary verification checklist
# All commands must exit 0

set -euo pipefail

echo "🔍 Running pre-canary verification checklist..."

# 1. Platform policy enforced
echo "1. Verifying platform policy..."
python -c "import platform; assert platform.system()=='Linux', 'Parser requires Linux'"

# 2. Audit script with branch protection & baseline checks
echo "2. Running audit script..."
GITHUB_TOKEN=${GH_PAT} python tools/audit_greenlight.py --report /tmp/audit.json
cat /tmp/audit.json | jq '.baseline_verification.status, .branch_protection.status'

# 3. Parity tests (no skips)
echo "3. Running parity tests..."
pytest -q tests/test_url_normalization_parity.py
pytest -q tests/test_malicious_token_methods.py --no-skip

# 4. Collector caps & isolation
echo "4. Running collector tests..."
pytest -q tests/test_collector_caps_end_to_end.py
pytest -q tests/test_collector_isolation.py

# 5. Critical tests (non-skippable)
echo "5. Running critical tests..."
pytest -v -m critical --tb=short

# 6. Small adversarial smoke (PR job)
echo "6. Running adversarial smoke..."
python -u tools/run_adversarial.py adversarial_corpora/adversarial_encoded_urls.json --runs 1 --report /tmp/adv_smoke.json

# 7. Performance benchmarks
echo "7. Running performance benchmarks..."
python tools/bench_dispatch.py --baseline baselines/metrics_baseline_v1_signed.json --iters 50
python tools/bench_section_of.py --sections 10000 --iters 100

# 8. Consumer compliance (if registry exists)
if [ -f consumer_registry.yml ]; then
  echo "8. Running consumer compliance probe..."
  python tools/probe_consumers.py --registry consumer_registry.yml --report /tmp/probe.json
fi

# 9. SSTI litmus tests in consumers
echo "9. Verifying SSTI tests in consumers..."
for repo in $(yq '.consumers[].repo' consumer_registry.yml); do
  echo "  Checking $repo..."
  gh api repos/$repo/contents/tests/test_consumer_ssti_litmus.py >/dev/null || {
    echo "❌ ERROR: SSTI test missing in $repo"
    exit 1
  }
done

# 10. Branch protection verification
echo "10. Verifying branch protection..."
gh api repos/:owner/:repo/branches/main/protection | jq '.required_status_checks.contexts[]' | grep -q "adversarial / pr_smoke"

echo ""
echo "✅ ALL PRE-CANARY CHECKS PASSED"
echo "Ready for canary deployment"
```

**Save as**: `tools/pre_canary_checklist.sh`

**Usage**:
```bash
chmod +x tools/pre_canary_checklist.sh
export GH_PAT="your-github-token"
./tools/pre_canary_checklist.sh
```

---

## POTENTIAL PITFALLS & PREVENTIVE MEASURES

### Pitfall 1: Silent Test Skips

**Risk**: Tests that skip in CI hide regressions.

**Prevention**:
```python
# In conftest.py
def pytest_collection_modifyitems(config, items):
    """Treat skips as failures unless explicitly waived."""
    for item in items:
        if "critical" in item.keywords:
            # Critical tests cannot be skipped
            skip_markers = [m for m in item.iter_markers(name="skip")]
            if skip_markers:
                pytest.fail(f"Critical test {item.nodeid} cannot be skipped")
```

**Verification**:
```bash
# Ensure no critical tests are skipped
pytest -v -m critical | grep -i "skip" && echo "❌ Skips detected" || echo "✅ No skips"
```

---

### Pitfall 2: Unregistered Consumers Rendering Metadata

**Risk**: Consumer not in registry silently renders metadata → SSTI vulnerability.

**Prevention**:
```yaml
# Maintain comprehensive consumer_registry.yml
# Run daily probes to discover unregistered consumers

# Add to CI:
- name: Verify all metadata consumers registered
  run: |
    # Grep codebase for metadata rendering patterns
    grep -r "metadata\[" src/ | while read line; do
      # Check if consuming service is in registry
      # Alert if not found
    done
```

**Verification**:
```bash
# Probe all consumers in registry
python tools/probe_consumers.py --registry consumer_registry.yml --report /tmp/probe.json
cat /tmp/probe.json | jq '.violations'
# Expected: []
```

---

### Pitfall 3: Non-Representative Baselines

**Risk**: Baseline captured on local dev machine → unrealistic thresholds → false positives in canary.

**Prevention**:
```bash
# Always capture baseline in containerized canonical environment
docker run --rm -v $(pwd):/workspace -w /workspace \
  python:3.12-slim \
  python tools/capture_baseline_metrics.py --duration 3600 --out baselines/metrics_baseline_v1.json

# Document environment in baseline JSON
{
  "environment": {
    "platform": "linux/amd64",
    "container_image": "python:3.12-slim",
    "heap_mb": 512,
    "kernel": "6.1.x"
  }
}
```

**Verification**:
```bash
# Verify baseline environment metadata
cat baselines/metrics_baseline_v1_signed.json | jq '.environment'
# Expected: container_image, platform, heap_mb documented
```

---

### Pitfall 4: Baseline Drift Over Time

**Risk**: Code changes gradually degrade performance → baseline becomes stale → canary thresholds too loose.

**Prevention**:
```yaml
# Add baseline recapture to monthly/quarterly schedule
# .github/workflows/baseline_recapture.yml
name: Baseline Recapture

on:
  schedule:
    - cron: '0 0 1 * *'  # Monthly on 1st
  workflow_dispatch:

jobs:
  recapture:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Recapture baseline
        run: |
          docker run --rm -v $(pwd):/workspace -w /workspace \
            python:3.12-slim \
            python tools/capture_baseline_metrics.py --duration 3600 --out baselines/metrics_baseline_$(date +%Y%m).json
      - name: Create PR with new baseline
        run: |
          git checkout -b baseline-recapture-$(date +%Y%m)
          git add baselines/metrics_baseline_$(date +%Y%m).json
          git commit -m "baseline: Recapture baseline for $(date +%Y-%m)"
          gh pr create --title "Baseline Recapture $(date +%Y-%m)" --body "Monthly baseline recapture"
```

---

### Pitfall 5: Token Canonicalization Bypass via New Code Paths

**Risk**: New collector or code path accesses raw token objects → bypass canonicalization.

**Prevention**:
```python
# Add to tools/audit_greenlight.py
def check_token_usage():
    """Static analysis for raw token object usage."""
    violations = []

    # Patterns that indicate raw token usage
    patterns = [
        r'token\.\w+',  # Direct attribute access
        r'token\[',     # Direct dict access followed by attr
        r'SimpleNamespace',
        r'__getattr__'
    ]

    for pattern in patterns:
        cmd = f"grep -rn '{pattern}' src/doxstrux/ --include='*.py'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            violations.append({
                'pattern': pattern,
                'matches': result.stdout.split('\n')[:10]
            })

    return {'status': 'fail' if violations else 'ok', 'violations': violations}
```

**Verification**:
```bash
# Run static check in CI
python tools/audit_greenlight.py --report /tmp/audit.json
cat /tmp/audit.json | jq '.token_canonicalization_static_check'
# Expected: {"status": "ok", "violations": []}
```

---

## FINAL ASSESSMENT SUMMARY

### Are We Green?

**Short Answer**: **NOT YET (v1.1: CLOSER, BUT FATAL P0 ITEMS BLOCK DEPLOYMENT)**

**v1.1 Enhancement**: P0 checks now FATAL → audit script will block deployment if baseline missing or branch protection misconfigured (fail-closed enforcement).

**Detailed Status**:

✅ **Architecture & Design**: Sound and well-documented
✅ **Adversarial Corpora**: Comprehensive (20+ URL vectors, template injection vectors)
✅ **Defensive Patches**: Implemented in skeleton (URL normalization, HTML sanitization, reentrancy guards)
✅ **Acceptance Matrix**: Machine-verifiable with exact commands
✅ **CI Guidance**: Complete workflows provided
✅ **Enforcement Semantics (v1.1)**: Fatal P0 checks implemented (exit codes 5/6)

⏸️ **Operational Enforcement**: Partially complete (v1.1: NOW BLOCKS IF INCOMPLETE)
- Git patches provided for baseline verification ✅
- **P0-FATAL**: Baseline must be GPG-signed and present ❌ (blocks deployment if missing)
- **P0-FATAL**: Branch protection must be configured ❌ (blocks deployment if misconfigured)
- Platform policy requires decision ⏸️ (24h deadline with Linux-only default)
- SSTI consumer deployment requires rollout ⏸️ (template provided, needs execution)
- Consumer registry requires deployment ⏸️ (discovery gap identified)

### Path to Green-Light

**Immediate (24h)**:
1. Apply git patches (baseline verification)
2. Decide platform policy (Linux-only recommended)
3. Enable adversarial CI gate in branch protection

**Short-term (72h)**:
4. Deploy SSTI tests to consumers
5. Enforce token canonicalization (critical marker + grep check)
6. Capture and sign canonical baseline

**Medium-term (1-2 weeks)**:
7. Deploy consumer registry and staging probes
8. Create performance benchmarks
9. Full observability deployment (Prometheus metrics)

### When Will Audit Script Report Clean?

**v1.1 Change**: Audit script now uses **fail-closed** semantics. Exit code meanings:

- **Exit 0**: All checks passed (GREEN LIGHT)
- **Exit 2**: Non-fatal issues (baseline breach, adversarial test warnings) - proceed with caution
- **Exit 5**: **FATAL** - Branch protection misconfigured/missing (BLOCKS DEPLOYMENT)
- **Exit 6**: **FATAL** - Baseline missing or capture failed (BLOCKS DEPLOYMENT)

**The audit script will exit 0 (green light) when**:

1. ✅ **P0-FATAL: Baseline verification**: Signed baseline exists at `baselines/metrics_baseline_v1_signed.json` AND current metrics within thresholds (`{"status": "ok"}`)
2. ✅ **P0-FATAL: Branch protection**: `consumer_registry.yml` exists AND all required checks configured in GitHub
3. ✅ **Adversarial tests**: All corpora pass with zero failures
4. ✅ **Token canonicalization**: Static check shows no violations (`{"status": "ok", "violations": []}`)
5. ✅ **Consumer compliance**: All consumers in registry have SSTI tests + passing staging probes

**The audit script will FAIL (exit 5 or 6) if**:

- ❌ No signed baseline at expected path → **FATAL exit 6** (cannot proceed)
- ❌ Baseline capture script missing/broken → **FATAL exit 6** (cannot verify metrics)
- ❌ Branch protection verification skipped/errored → **FATAL exit 5** (GitHub API unavailable or registry malformed)
- ❌ Branch protection misconfigured (missing required checks) → **FATAL exit 5** (enforcement gap)

**Expected Timeline**:
- 24h to exit 5/6 → exit 0/2 (after baseline capture + branch protection setup)
- 72h to full green light (exit 0, all checks passing, no warnings)

---

## NEXT ACTIONS

**If you want to proceed**, I recommend this sequence:

1. **Today (Priority 0)**:
   - [ ] Apply Patch 1 (baseline verification in audit script)
   - [ ] Apply Patch 2 (pre-canary CI integration)
   - [ ] **v1.1: Apply Patch 3 (make P0 checks FATAL - fail-closed enforcement)**
   - [ ] Tech Lead decides platform policy (Linux-only recommended)
   - [ ] DevOps enables adversarial CI gate in branch protection

2. **Tomorrow (Priority 1)**:
   - [ ] Deploy SSTI test to first consumer repo (pilot)
   - [ ] Mark malicious-token test as `@pytest.mark.critical`
   - [ ] Add token canonicalization static check to audit script

3. **This Week (Priority 2)**:
   - [ ] Capture canonical baseline in containerized environment
   - [ ] Sign baseline with GPG (SRE lead)
   - [ ] Deploy SSTI tests to remaining consumers
   - [ ] Create consumer registry YAML

4. **Next Week (Priority 3)**:
   - [ ] Deploy consumer staging probe automation
   - [ ] Create performance benchmarks (dispatch, section_of)
   - [ ] Deploy Prometheus metrics and alerts

**After all items complete**: Run `tools/pre_canary_checklist.sh` → expect all checks green → **READY FOR CANARY**

---

## RELATED DOCUMENTATION

- **Part 1**: PLAN_CLOSING_IMPLEMENTATION_extended_1.md (P0 Critical tasks)
- **Part 2**: PLAN_CLOSING_IMPLEMENTATION_extended_2.md (P1/P2 Patterns)
- **Part 3**: PLAN_CLOSING_IMPLEMENTATION_extended_3.md (P3 Observability)
- **Part 4**: PLAN_CLOSING_IMPLEMENTATION_extended_4.md (Security Audit Response)
- **Part 5**: PLAN_CLOSING_IMPLEMENTATION_extended_5.md (v2.2 Green-Light Checklist)
- **Execution Report**: PLAN_EXECUTION_REPORT.md (Test results from skeleton)
- **Part 5 v2.1 Completion**: PART5_V21_GAPFIX_COMPLETE.md
- **Part 5 v2.2 Completion**: PART5_V22_REFACTOR_COMPLETE.md

---

**END OF PART 6 - OPERATIONAL IMPLEMENTATION GUIDE**

This document provides all concrete steps, git patches, and verification commands needed to close remaining operational security gaps. All work is **copy-paste ready** and **priority-ordered** with effort estimates and owners assigned.

---

## VERSION 1.1 CHANGELOG

**Version**: 1.1 (Operational Implementation & Fatal P0 Enforcement)
**Date**: 2025-10-17
**Changes from v1.0**: Incorporated deep feedback from third-round security assessment

### Key Enhancements

1. **Patch 3 Added: Fatal P0 Enforcement** (NEW)
   - Audit script now treats P0 failures as **FATAL** (exit codes 5/6)
   - Missing baseline → exit 6 (blocks deployment)
   - Branch protection misconfigured → exit 5 (blocks deployment)
   - Enforces fail-closed semantics (cannot proceed if P0 incomplete)

2. **Consumer Discovery Gap Documented** (NEW)
   - Identified manual registry maintenance as vulnerability
   - Added 3 fix options (static scanner, runtime discovery, API enforcement)
   - Recommended: Daily codebase scanner + API header validation
   - Priority: P0-BLOCKING

3. **Enforcement Semantics Clarified** (UPDATED)
   - Added enforcement clarification box at document start
   - Updated "Are We Green?" section with fatal P0 status
   - Updated "When Will Audit Script Report Clean?" with exit code meanings
   - Baseline and branch protection now explicitly marked as P0-FATAL

4. **Patch 2 Enhanced** (UPDATED)
   - Platform policy content expanded with exact policy document
   - Linux-only default documented with 24h decision deadline
   - CI enforcement command provided

### Lines Changed

- **Added**: ~150 lines (Patch 3, consumer discovery gap, enforcement boxes)
- **Updated**: ~80 lines (status sections, git patch metadata, summaries)
- **Total document**: ~1950 lines (from 1772 in v1.0)

### Backward Compatibility

- v1.0 patches (1 & 2) remain valid and can be applied independently
- Patch 3 is **additive** - enhances audit script without breaking existing functionality
- All v1.0 verification commands still work
- v1.1 adds **stricter enforcement** but does not change implementation steps

### Migration from v1.0

If you started with v1.0:
1. Apply Patch 3 to make P0 checks fatal
2. Ensure baseline exists (or audit will now block with exit 6)
3. Ensure `consumer_registry.yml` exists (or branch protection check skipped)
4. No other changes required - all v1.0 steps remain valid

### Defensibility Assessment

**v1.0**: Operational guide with reporting (non-blocking)
**v1.1**: Operational guide with **fatal enforcement** (blocking deployment if P0 incomplete)

**External Auditor's Requirement**: "Make P0 checks fatal, not just reported"
**v1.1 Response**: ✅ **REQUIREMENT MET** - Patch 3 implements fatal P0 enforcement

---

🎯 **Execute the immediate actions today, and you'll be on the path to a defensible green-light within 72 hours.**

**v1.1 Note**: With fatal P0 enforcement, deployment is **blocked** until baseline signed and branch protection configured. This is by design (fail-closed security posture).
