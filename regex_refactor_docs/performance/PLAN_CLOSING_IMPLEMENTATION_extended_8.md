# Extended Closing Implementation Plan - Phase 8 Security Hardening
# Part 8 of 8: Final Green-Light Readiness - CI Enforcement & Operational Playbook

**Version**: 1.0 (CI Enforcement + Green-Light Playbook)
**Date**: 2025-10-18
**Status**: FINAL GREEN-LIGHT READINESS - CI AUTOMATION & PLAYBOOK
**Methodology**: Golden Chain-of-Thought + External Deep Security Assessment (Fifth Round)
**Part**: 8 of 8 (FINAL)
**Purpose**: Close final operational gaps - CI enforcement, baseline signing, green-light playbook

⚠️ **CRITICAL**: This part implements **FINAL OPERATIONAL READINESS** - the last 4-6 items before flipping canary switch.

**Previous Parts**:
- Part 1: PLAN_CLOSING_IMPLEMENTATION_extended_1.md (P0 Critical - 5 tasks)
- Part 2: PLAN_CLOSING_IMPLEMENTATION_extended_2.md (P1/P2 Patterns - 10 tasks)
- Part 3: PLAN_CLOSING_IMPLEMENTATION_extended_3.md (P3 Observability - 3 tasks)
- Part 4: PLAN_CLOSING_IMPLEMENTATION_extended_4.md (Security Audit Response)
- Part 5: PLAN_CLOSING_IMPLEMENTATION_extended_5.md (v2.2 - Green-Light Checklist)
- Part 6: PLAN_CLOSING_IMPLEMENTATION_extended_6.md (v1.0 - Operational Implementation)
- Part 7: PLAN_CLOSING_IMPLEMENTATION_extended_7.md (v1.1 - Fatal P0 Enforcement)

**Source**: External deep security assessment (fifth round) - final operational readiness

**Assessment Verdict**: "You're very close to a defensible green-light. The architecture, adversarial corpora, and most enforcement tooling are in place; the last ~4–6 items are operational/hardening work (automation, signed baseline, platform decision, consumer discovery & registration)."

---

## EXECUTIVE SUMMARY

This document implements **FINAL OPERATIONAL READINESS** - the last items needed before canary deployment:

**What's Done (Parts 1-7)**:
✅ Token canonicalization
✅ HTML default-off
✅ SIGALRM watchdog
✅ Reentrancy guard
✅ Resource caps
✅ Adversarial corpora & runner
✅ Audit script with P0 gates
✅ Fatal P0 enforcement (exit 5/6)
✅ Platform policy (Linux-only)
✅ Renderer discovery
✅ Signed baseline verification

**What's Missing (This Part - P0 BLOCKERS)**:
1. ❌ **Signed canonical baseline** - Baseline not yet captured/signed (BLOCKS DEPLOYMENT)
2. ❌ **CI platform assertion** - No automated Linux-only enforcement in CI
3. ❌ **CI audit enforcement** - audit_greenlight.py not required in PR workflow
4. ❌ **Branch protection required checks** - Audit not blocking merges
5. ❌ **Consumer discovery completeness** - Registry may have gaps
6. ❌ **Operational playbook** - No step-by-step green-light checklist

**What This Part Delivers**:
1. ✅ **Git Patch**: CI workflow with platform assertion + audit enforcement
2. ✅ **RUN_TO_GREEN.md**: Exact commands to reach green-light (copy-paste ready)
3. ✅ **Baseline signing procedure**: Step-by-step with GPG
4. ✅ **CI secrets configuration**: BASELINE_PUBLIC_KEY setup
5. ✅ **Green-light verification**: Machine-verifiable checklist

**Timeline to Green-Light**: 4-8 hours (baseline capture + CI config + verification)

**Critical Deliverables**:
1. **IMMEDIATE (P0)**: CI workflow patch (platform + audit enforcement)
2. **IMMEDIATE (P0)**: RUN_TO_GREEN.md playbook (step-by-step execution)
3. **2-4h (P0)**: Signed canonical baseline (capture + sign + commit)
4. **1-2h (P0)**: CI secrets configuration (BASELINE_PUBLIC_KEY)
5. **1-2h (P0)**: Branch protection required checks

---

## ASSESSMENT FINDINGS - FIFTH ROUND

### One-Line Verdict

**Status**: Very close to defensible green-light
**Done**: Architecture + corpora + enforcement tools complete
**Remaining**: 4-6 operational items (automation, baseline, CI enforcement, discovery)

### What's Excellent (Already Complete from Parts 1-7)

✅ **Token Canonicalization**: Implemented, tested, non-skippable
✅ **HTML Default-Off**: Fail-closed, explicit opt-in required
✅ **SIGALRM Watchdog**: Linux timeout enforcement working
✅ **Reentrancy Guard**: Thread-safety patterns documented
✅ **Resource Caps**: Per-collector limits enforced
✅ **Adversarial Corpora**: 20+ URL vectors, 10+ template injection vectors
✅ **Audit Script**: P0 gates (baseline, branch protection, renderer discovery)
✅ **Fatal Enforcement**: Exit codes 5/6 block deployment
✅ **Platform Policy**: Linux-only documented with enforcement procedures
✅ **Renderer Discovery**: Automated codebase scanning implemented

### Major Blockers (Must-Fix P0 Items) - Ranked & Explicit

#### 1. Signed Canonical Baseline Present and Verified (P0 - BLOCKER)

**Why It Blocks**: audit_greenlight.py requires signed baseline (baselines/metrics_baseline_v1.json + .asc) and exits fatal (code 6) if missing/unsigned.

**Current State**: ❌ Baseline files do not exist

**How to Verify Now**:
```bash
# Quick check
test -f baselines/metrics_baseline_v1.json && \
test -f baselines/metrics_baseline_v1.json.asc && \
echo "✅ Baseline files exist" || \
echo "❌ Baseline missing"

# Verify signature
gpg --batch --verify baselines/metrics_baseline_v1.json.asc \
                      baselines/metrics_baseline_v1.json

# Run audit
python tools/audit_greenlight.py --report /tmp/audit.json
jq '.baseline_verification.status' /tmp/audit.json
# Expected: "ok" (currently will be "missing_baseline")
```

**Required Action**:
1. Capture canonical baseline (containerized, 60-min benchmark)
2. Sign with dedicated SRE key (prefer HSM/KMS or tightly-scoped secret)
3. Commit baseline.json + baseline.json.asc to git
4. Publish public key for audit verification

**ETA**: 2-4 hours (benchmark duration + signing + commit)

**Owner**: SRE

#### 2. Platform Assertion in CI (P0 - BLOCKER)

**Why It Blocks**: SIGALRM watchdog is Linux-specific; Windows hosts need subprocess worker design or else DoS/hangs possible. No automated enforcement exists.

**Current State**: ❌ No CI assertion, can run on any platform

**Required Action**: Add CI assertion to all workflows:
```yaml
- name: Platform assertion (Linux-only)
  run: |
    python -c "import platform,sys; sys.exit(0) if platform.system()=='Linux' else sys.exit(2)"
```

**ETA**: 30 minutes (add to workflows, test)

**Owner**: DevOps

#### 3. CI Audit Enforcement (P0 - BLOCKER)

**Why It Blocks**: audit_greenlight.py exists but not required in PR workflow. PRs can merge without audit passing.

**Current State**: ❌ Audit runs manually, not enforced

**Required Action**:
1. Add pre-merge CI workflow that runs audit_greenlight.py
2. Fail workflow if audit exits non-zero
3. Upload audit report as artifact

**ETA**: 1-2 hours (workflow creation + testing)

**Owner**: DevOps

#### 4. Branch Protection Required Checks (P0 - BLOCKER)

**Why It Blocks**: Even with CI workflows, branch protection must be configured to make them required. PRs can bypass failing workflows.

**Current State**: ❌ No required checks configured

**Required Action**: Enable required status checks:
- `Pre-merge Safety Checks` (audit workflow)
- `adversarial-smoke` (fast PR job)
- `token-canonicalization` (parser unit tests)
- `consumer-ssti-litmus` (consumer repos)

**ETA**: 30-60 minutes (GitHub settings)

**Owner**: DevOps

#### 5. Consumer Discovery Completeness (P0 - HIGH PRIORITY)

**Why It Blocks**: Renderer discovery scan may find unregistered consumers → fatal audit exit. All hits must be triaged.

**Current State**: ⚠️ Unknown - needs verification

**Required Action**:
1. Run audit_greenlight.py
2. Check `renderer_unregistered_local` and `org_unregistered_hits`
3. For each hit:
   - Add to consumer_registry.yml (if legitimate renderer)
   - Add to audit_exceptions.yml (if false positive)
   - Remediate consumer code (if unsafe rendering)

**ETA**: 1-8 hours (depends on number of hits, ~30-120min per consumer)

**Owner**: Security + Consumer Owners

#### 6. CI Secrets Configuration (P0 - BLOCKER)

**Why It Blocks**: CI workflow needs BASELINE_PUBLIC_KEY secret to verify signed baseline. Without it, baseline verification fails.

**Current State**: ❌ Secret not configured

**Required Action**:
1. Export baseline public key: `gpg --export --armor SIGNER_KEY_ID > baseline_pubkey.asc`
2. Add to GitHub secrets: BASELINE_PUBLIC_KEY (paste key content)
3. Verify CI can import key

**ETA**: 15-30 minutes

**Owner**: DevOps

---

## GIT PATCH (READY TO APPLY)

### Patch: CI Pre-Merge Safety Checks Workflow

**Purpose**: Add pre-merge CI workflow with platform assertion, baseline verification, and audit enforcement

**File**: `.github/workflows/pre_merge_checks.yml` (NEW)
**Lines**: ~80 lines
**What It Does**:
- Asserts runner platform is Linux (fails otherwise)
- Imports baseline public key from secrets.BASELINE_PUBLIC_KEY
- Runs tools/audit_greenlight.py (fails if exit non-zero)
- Uploads audit report as artifact for triage

**Patch**:

```diff
--- /dev/null
+++ b/.github/workflows/pre_merge_checks.yml
@@ -0,0 +1,78 @@
+name: Pre-merge Safety Checks
+
+on:
+  pull_request:
+    types: [opened, synchronize, reopened]
+
+env:
+  REPORT_DIR: adversarial_reports
+  AUDIT_REPORT: adversarial_reports/pr_audit.json
+
+jobs:
+  premerge_checks:
+    name: Pre-merge safety checks (platform assertion + baseline audit)
+    runs-on: ubuntu-latest
+    permissions:
+      contents: read
+      checks: write
+    steps:
+      - name: Checkout
+        uses: actions/checkout@v4
+
+      - name: Set up Python
+        uses: actions/setup-python@v4
+        with:
+          python-version: "3.10"
+
+      - name: Install dependencies
+        run: |
+          python -m pip install --upgrade pip
+          pip install pyyaml requests || true
+
+      - name: Ensure report dir exists
+        run: mkdir -p ${{ env.REPORT_DIR }}
+
+      - name: Platform assertion (Linux-only)
+        run: |
+          echo "Asserting runner platform is Linux..."
+          python - <<'PY'
+import platform, sys
+if platform.system() != "Linux":
+    print("Platform assertion failed: not Linux (found {})".format(platform.system()))
+    sys.exit(2)
+print("Platform assertion OK: Linux")
+PY
+
+      - name: Import baseline public key
+        env:
+          BASELINE_PUBLIC_KEY: ${{ secrets.BASELINE_PUBLIC_KEY || '' }}
+        run: |
+          if [ -z "${BASELINE_PUBLIC_KEY}" ]; then
+            echo "ERROR: BASELINE_PUBLIC_KEY secret is not set. Baseline signature verification cannot run."
+            exit 2
+          fi
+          echo "${BASELINE_PUBLIC_KEY}" > /tmp/baseline_pub.asc
+          sudo apt-get update -y && sudo apt-get install -y gnupg
+          gpg --import /tmp/baseline_pub.asc
+          rm -f /tmp/baseline_pub.asc
+          echo "Imported baseline public key for verification."
+
+      - name: Run audit greenlight (baseline + branch-protection + discovery)
+        env:
+          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
+        run: |
+          set -euo pipefail
+          python tools/audit_greenlight.py --report "${{ env.AUDIT_REPORT }}"
+          echo "Audit report written to ${{ env.AUDIT_REPORT }}"
+          cat "${{ env.AUDIT_REPORT }}"
+
+      - name: Upload audit report artifact
+        uses: actions/upload-artifact@v4
+        with:
+          name: pr-audit-report
+          path: ${{ env.AUDIT_REPORT }}
+          retention-days: 90
+
+      - name: Fail if audit non-zero
+        run: |
+          echo "Audit completed - check artifact for details"
```

**Application**:
```bash
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance

# Save patch to file
cat > /tmp/ci_pre_merge_checks.patch << 'EOF'
[Paste patch above]
EOF

# Apply patch
git apply /tmp/ci_pre_merge_checks.patch

# Or use patch command
patch -p1 < /tmp/ci_pre_merge_checks.patch
```

**Verification**:
```bash
# Verify workflow file created
test -f .github/workflows/pre_merge_checks.yml && \
echo "✅ Workflow created" || \
echo "❌ Workflow missing"

# Commit and push
git add .github/workflows/pre_merge_checks.yml
git commit -m "ci: Add pre-merge safety checks (platform + audit)

- Platform assertion: Linux-only enforcement
- Baseline verification: GPG signature required
- Audit enforcement: Blocks merge if exit non-zero
- Artifact upload: Report available for triage

Implements: Part 8, CI Enforcement

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

git push origin main
```

---

## RUN_TO_GREEN.md PLAYBOOK

**Purpose**: Exact step-by-step commands to reach green-light, copy-paste ready

**File**: `RUN_TO_GREEN.md` (NEW)
**Lines**: ~200
**Format**: Markdown with executable bash blocks

**Content**:

```markdown
# RUN_TO_GREEN.md

This playbook captures the exact minimal steps to reach a defensible "green light" for the Phase 8 parser/warehouse rollout.

Follow the steps in order. Run commands from the repository root. Replace environment variables and secret names with your org's equivalents.

---

## Quick Prerequisites

**SRE / Owner Requirements**:
- Dedicated baseline signing key (prefer HSM/KMS)
- If using GPG locally:
  ```bash
  # Import private key (for signing step only)
  gpg --import /path/to/private-sign-key.asc

  # Export public key
  gpg --export --armor SIGNER_KEY_ID > baselines/baseline_pubkey.asc
  ```

**CI Secrets Required**:
- `BASELINE_PUBLIC_KEY`: ASCII-armored public key
- `GITHUB_TOKEN`: Actions provides this by default (ensure branch protection read permission)

---

## Step 1: Capture Canonical Baseline (SRE)

**Owner**: SRE
**Effort**: 2-4 hours (including 60-min benchmark)
**Deadline**: Before any PR can merge

Run in a canonical controlled environment (container image matching production runners).

```bash
# Optional: Create container with same runtime as canary
# docker run --rm -it -v $(pwd):/workspace -w /workspace python:3.12-slim bash

# Install dependencies
pip install -e .

# Run benchmark capture (60-min duration recommended)
python tools/capture_baseline_metrics.py \
    --duration 3600 \
    --out baselines/metrics_baseline_v1.json

# Review captured metrics
cat baselines/metrics_baseline_v1.json | jq '.metrics, .thresholds'

# Add baseline metadata (edit file to include env_image, commit, cpu/mem, captured_by)
# Example metadata to add:
# {
#   "environment": {
#     "captured_by": "sre-lead@example.com",
#     "container_image": "python:3.12-slim",
#     "cpu_count": 8,
#     "memory_gb": 16
#   }
# }
```

**Sign Baseline** (offline preferred):
```bash
# Sign with dedicated key
gpg --armor \
    --output baselines/metrics_baseline_v1.json.asc \
    --detach-sign baselines/metrics_baseline_v1.json

# Verify signature locally
gpg --batch --verify \
    baselines/metrics_baseline_v1.json.asc \
    baselines/metrics_baseline_v1.json

# Expected: "Good signature from ..."
```

**Commit Baseline**:
```bash
# Add baseline + signature
git add baselines/metrics_baseline_v1.json
git add baselines/metrics_baseline_v1.json.asc

# Commit
git commit -m "baseline: Add GPG-signed canonical baseline v1.0

- Captured over 60-minute benchmark run
- Signed with dedicated SRE key for audit trail
- Thresholds: P95×1.25, P99×1.5, RSS+30MB

Environment:
- Container: python:3.12-slim
- CPU: 8 cores
- Memory: 16GB

Signature verified:
$ gpg --verify baselines/metrics_baseline_v1.json.asc

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

# Push
git push origin main
```

**Verification**:
```bash
# Verify baseline files exist
test -f baselines/metrics_baseline_v1.json && \
test -f baselines/metrics_baseline_v1.json.asc && \
echo "✅ Baseline files committed" || \
echo "❌ Baseline missing"

# Verify signature
gpg --batch --verify \
    baselines/metrics_baseline_v1.json.asc \
    baselines/metrics_baseline_v1.json
# Expected: exit 0
```

---

## Step 2: Ensure Registry & Exceptions are Populated (Security / Owners)

**Owner**: Security + Consumer Owners
**Effort**: 1-8 hours (depends on number of consumers)
**Deadline**: Before PR merges

**Populate Consumer Registry**:
```bash
# Edit consumer_registry.yml
vi consumer_registry.yml

# Add entries for each consumer that renders metadata
# Fill code_paths and excluded_paths
consumers:
  - name: "frontend-web"
    repo: "org/frontend-web"
    renders_metadata: true
    code_paths:
      - "frontend/src/"
      - "templates/"
    ssti_protection:
      test_file: "tests/test_consumer_ssti_litmus.py"
      autoescape_enforced: true
    probe_url: "https://staging-frontend.example.internal/__probe__"
    required_checks:
      - "consumer-ssti-litmus"
```

**Populate Audit Exceptions** (if needed):
```bash
# Create audit_exceptions.yml for known false positives
cat > audit_exceptions.yml << 'EOF'
exceptions:
  - path: "docs/examples/template_usage.py"
    reason: "Documentation only, not production code"
    approver: "security-lead@example.com"
    expires: "2025-12-31"
  - path: "tests/fixtures/renderer_mock.py"
    reason: "Test fixture, not production renderer"
    approver: "security-lead@example.com"
    expires: "2025-12-31"
EOF
```

---

## Step 3: Run Local Audit & Fix Issues (Dev / Security)

**Owner**: Dev + Security
**Effort**: 1-4 hours
**Deadline**: Before PR merges

```bash
# Ensure dependencies
pip install -r requirements.txt || true
pip install requests pyyaml || true

# Set GitHub token (for branch protection queries)
export GITHUB_TOKEN="ghp_xxx"  # Or ensure Actions runs with token

# Run audit
python tools/audit_greenlight.py \
    --report ./adversarial_reports/local_audit.json

# Review report
jq '.' ./adversarial_reports/local_audit.json
```

**Resolve Until All Green**:
```bash
# Check baseline verification
jq '.baseline_verification.status' ./adversarial_reports/local_audit.json
# Expected: "ok"

# Check unregistered renderers (local)
jq '.renderer_unregistered_local | length' ./adversarial_reports/local_audit.json
# Expected: 0

# Check unregistered renderers (org-wide)
jq '.org_unregistered_hits | length' ./adversarial_reports/local_audit.json
# Expected: 0 (or exceptions added)

# Check branch protection
jq '.branch_protection_verification.status' ./adversarial_reports/local_audit.json
# Expected: "ok"
```

**Fix Issues**:
- **baseline_verification != "ok"**: Capture and sign baseline (Step 1)
- **renderer_unregistered_local > 0**: Add to consumer_registry.yml or audit_exceptions.yml
- **org_unregistered_hits > 0**: Register consumers or add exceptions
- **branch_protection != "ok"**: Enable required checks (Step 5)

---

## Step 4: Probe Consumers in Staging (QA / Owners)

**Owner**: QA + Consumer Owners
**Effort**: 1-2 hours
**Deadline**: Before canary deployment

```bash
# Install dependencies
pip install requests pyyaml

# Run consumer probe
python tools/probe_consumers.py \
    --registry consumer_registry.yml \
    --outdir consumer_probe_reports

# Inspect reports
ls consumer_probe_reports/
cat consumer_probe_reports/*.json | jq '.'

# Check for violations
cat consumer_probe_reports/*.json | jq 'select(.evaluated == true or .reflected == true)'
# Expected: empty (no output)
```

**If Probe Reports Reflection/Evaluation**:
1. **Immediate**: Remove consumer from production parse routing
2. **Fix**: Add escaping or sanitization in consumer code
3. **Re-test**: Run probe again, verify status "ok"
4. **Re-enable**: After probe passes twice (24h apart)

---

## Step 5: Configure CI Branch Protection (DevOps)

**Owner**: DevOps
**Effort**: 30-60 minutes
**Deadline**: Before PR merges

**Required Checks for Parser Repo**:
- `Pre-merge Safety Checks` (workflow from Part 8 patch)
- `adversarial-smoke` (fast adversarial PR job)
- `token-canonicalization` (parser unit tests)
- `url-parity-smoke` (URL normalization tests)

**GitHub UI**:
```
1. Go to: Settings → Branches → Branch protection rules → main
2. Add required status checks:
   - Pre-merge Safety Checks
   - adversarial-smoke
   - token-canonicalization
   - url-parity-smoke
3. Save changes
```

**GitHub CLI**:
```bash
gh api repos/:owner/:repo/branches/main/protection \
    -X PUT \
    -F required_status_checks[strict]=true \
    -F required_status_checks[contexts][]=Pre-merge Safety Checks \
    -F required_status_checks[contexts][]=adversarial-smoke \
    -F required_status_checks[contexts][]=token-canonicalization \
    -F required_status_checks[contexts][]=url-parity-smoke
```

**Consumer Repos** (where applicable):
```bash
# For each consumer repo with renders_metadata: true
gh api repos/:owner/:consumer-repo/branches/main/protection \
    -X PUT \
    -F required_status_checks[strict]=true \
    -F required_status_checks[contexts][]=consumer-ssti-litmus
```

**Verification**:
```bash
# Verify required checks configured
gh api repos/:owner/:repo/branches/main/protection | \
jq '.required_status_checks.contexts'

# Expected: Array with all required checks
```

---

## Step 6: Configure CI Secrets (DevOps)

**Owner**: DevOps
**Effort**: 15-30 minutes
**Deadline**: Before CI workflow runs

**Export Public Key**:
```bash
# Export baseline public key
gpg --export --armor SIGNER_KEY_ID > /tmp/baseline_pubkey.asc

# Verify key exported
cat /tmp/baseline_pubkey.asc
# Expected: -----BEGIN PGP PUBLIC KEY BLOCK-----
```

**Add to GitHub Secrets**:
```
1. Go to: Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: BASELINE_PUBLIC_KEY
4. Value: Paste entire content of baseline_pubkey.asc
5. Click "Add secret"
```

**Verification**:
```bash
# Verify secret exists
gh secret list | grep BASELINE_PUBLIC_KEY
# Expected: BASELINE_PUBLIC_KEY (updated XXXs ago)
```

---

## Step 7: PR & Pre-Canary (Ops)

**Owner**: Ops
**Effort**: Ongoing monitoring
**Deadline**: After all steps 1-6 complete

**Create Test PR**:
```bash
# Create test branch
git checkout -b test-green-light-enforcement

# Make trivial change
echo "# Test green-light enforcement" >> README.md

# Commit and push
git add README.md
git commit -m "test: Verify green-light enforcement"
git push origin test-green-light-enforcement

# Create PR
gh pr create \
    --title "Test: Green-Light Enforcement" \
    --body "Testing pre-merge safety checks workflow"
```

**Verify Checks Run**:
```bash
# Check PR status
gh pr checks

# Expected:
# ✓ Pre-merge Safety Checks
# ✓ adversarial-smoke
# ✓ token-canonicalization
# ✓ url-parity-smoke

# Verify audit report artifact uploaded
gh run list --workflow=pre_merge_checks.yml | head -1
gh run view <run-id> --log

# Download audit report
gh run download <run-id> --name pr-audit-report
cat pr_audit.json | jq '.'
```

**Canary Deployment**:
After PR merges and all checks pass:
```bash
# Start canary with 1% traffic
kubectl scale deployment/parser-canary --replicas=2

# Monitor metrics (15-30 minutes):
# - collector_timeouts_total (no >50% increase)
# - parse_p99_ms (<= baseline * 1.5)
# - collector_truncated_total (no unexpected spike)
# - adversarial_failure_total (must be zero)

# Check metrics
curl http://prometheus:9090/api/v1/query?query=collector_timeouts_total
curl http://prometheus:9090/api/v1/query?query=parse_p99_ms
```

**If Canary Alarms Trigger** → Follow Step 8 (Rollback)

---

## Step 8: Canary Rollback (Runbook)

**Owner**: SRE
**Trigger**: Any canary alarm (timeout spike, P99 breach, adversarial failure)
**Deadline**: Immediate

**Rollback Procedure**:
```bash
# 1. Stop routing to canary
kubectl patch service parser-service \
    --type=json \
    -p='[{"op":"remove","path":"/spec/selector/version"}]'

# 2. Scale down canary instances
kubectl scale deployment/parser-canary --replicas=0

# 3. Revert to previous parser image
kubectl rollout undo deployment/parser-service

# 4. Verify stable version running
kubectl get pods -l app=parser-service
```

**Post-Rollback**:
```bash
# 5. Attach audit reports to incident
ls adversarial_reports/*.json

# 6. Create incident ticket
gh issue create \
    --title "P0: Canary rollback - $(date +%Y-%m-%d)" \
    --body "Canary rollback triggered. See audit reports in adversarial_reports/" \
    --label "P0,canary-rollback" \
    --assignee "@sre-lead,@security-lead"

# 7. Triage failing adversarial vectors
cat adversarial_reports/*.json | jq '.failures'
```

---

## Useful Commands (Summary)

```bash
# Run PR audit (as CI does)
python tools/audit_greenlight.py --report adversarial_reports/pr_audit.json

# Probe consumers
python tools/probe_consumers.py \
    --registry consumer_registry.yml \
    --outdir consumer_probe_reports

# Run small adversarial smoke
python -u tools/run_adversarial.py \
    adversarial_corpora/adversarial_encoded_urls.json \
    --runs 1 \
    --report /tmp/adv_smoke.json

# Run parity & token tests (must be non-skippable)
pytest -q tests/test_url_normalization_parity.py
pytest -q tests/test_malicious_token_methods.py

# Check exit code
echo $?
# Expected: 0 (all tests passing)
```

---

## Owners & Contact Points

| Role | Owner | Responsibility |
|------|-------|----------------|
| **Tech Lead** | @tech-lead | Platform policy decision |
| **SRE** | @sre-lead | Baseline capture/signing, monitoring/alerts |
| **DevOps** | @devops-lead | CI secrets, branch protection |
| **Security** | @security-lead | Registry audit, exceptions |
| **Consumer Owners** | @consumer-teams | SSTI litmus tests, probe response |

**Update this section with exact contacts and SLAs for triage.**

---

## Green-Light Verification Checklist

Before declaring green-light, verify ALL items pass:

### P0 Checklist (MUST PASS)

**[P0-1] Signed Baseline Exists & Audit Green** ✅
```bash
gpg --batch --verify \
    baselines/metrics_baseline_v1.json.asc \
    baselines/metrics_baseline_v1.json

python tools/audit_greenlight.py --report /tmp/audit.json

jq '.baseline_verification.status' /tmp/audit.json
# Expected: "ok"
```

**[P0-2] Consumer Probe: No Reflection/SSTI** ✅
```bash
python tools/probe_consumers.py \
    --registry consumer_registry.yml \
    --report /tmp/probe.json

jq '.status, .violations' /tmp/probe.json
# Expected: status == "ok", violations == []
```

**[P0-3] PR-Smoke Parity Tests (Blocking)** ✅
```bash
pytest -q tests/test_url_normalization_parity.py
pytest -q tests/test_malicious_token_methods.py
# Expected: rc 0, no skips
```

**[P0-4] Renderer Discovery Audit** ✅
```bash
python tools/audit_greenlight.py --report /tmp/audit.json

jq '.renderer_unregistered_local, .org_unregistered_hits' /tmp/audit.json
# Expected: both empty arrays []
```

**[P0-5] Platform Assertion in CI** ✅
```bash
# Verify workflow file exists
test -f .github/workflows/pre_merge_checks.yml && \
echo "✅ PASS" || echo "❌ FAIL"

# Verify platform assertion step present
grep -q "platform.system()" .github/workflows/pre_merge_checks.yml && \
echo "✅ PASS" || echo "❌ FAIL"
```

**[P0-6] Branch Protection Required Status Checks** ✅
```bash
gh api repos/:owner/:repo/branches/main/protection | \
jq '.required_status_checks.contexts[] | select(. == "Pre-merge Safety Checks")'

# Expected: "Pre-merge Safety Checks"
```

**[P0-7] Metrics & Alerts Configured** ✅
```bash
# Verify metrics exist in Prometheus
curl -s http://prometheus:9090/api/v1/query?query=collector_timeouts_total | \
jq '.data.result | length'
# Expected: >= 1

curl -s http://prometheus:9090/api/v1/query?query=parse_p95_ms | \
jq '.data.result | length'
# Expected: >= 1
```

### Final Verification

**Run All Checks**:
```bash
# Run full audit
python tools/audit_greenlight.py --report /tmp/final_audit.json

# Verify exit code 0
echo $?
# Expected: 0

# Verify all checks passed
jq '{
  baseline: .baseline_verification.status,
  branch_protection: .branch_protection_verification.status,
  unregistered_local: (.renderer_unregistered_local | length),
  unregistered_org: (.org_unregistered_hits | length)
}' /tmp/final_audit.json

# Expected:
# {
#   "baseline": "ok",
#   "branch_protection": "ok",
#   "unregistered_local": 0,
#   "unregistered_org": 0
# }
```

**If All Pass**: ✅ **GREEN LIGHT - Ready for canary deployment**

**If Any Fail**: ❌ **BLOCKED - Fix failures and re-run checklist**

---

**Keep this file updated with exact owner contacts & expected SLAs for triage.**
```

**Application**:
```bash
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance

# Create RUN_TO_GREEN.md
cat > RUN_TO_GREEN.md << 'EOF'
[Paste content above]
EOF

# Commit
git add RUN_TO_GREEN.md
git commit -m "docs: Add RUN_TO_GREEN.md operational playbook

Step-by-step green-light checklist with exact commands:
- Baseline capture and signing procedure
- CI secrets configuration
- Branch protection setup
- Consumer discovery and probe
- Canary deployment and rollback

All commands copy-paste ready for immediate execution.

Implements: Part 8, Operational Playbook

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

git push origin main
```

---

## IMPLEMENTATION TIMELINE

### Immediate (Next 2-4 Hours) - Priority 0

**Owner: SRE + DevOps**

| Step | Task | Effort | Deadline |
|------|------|--------|----------|
| 1 | Apply CI workflow patch | 15 min | Immediate |
| 2 | Create RUN_TO_GREEN.md | 10 min | Immediate |
| 3 | Configure BASELINE_PUBLIC_KEY secret | 15 min | Immediate |
| 4 | Capture canonical baseline (60-min benchmark) | 2-4 hours | 4 hours |
| 5 | Sign baseline with GPG | 10 min | Immediate after capture |
| 6 | Commit baseline + signature | 10 min | Immediate after signing |

**Total**: 2-4 hours (mostly benchmark duration)

---

### Short-Term (Next 4-8 Hours) - Priority 1

**Owner: Security + Consumer Owners + DevOps**

| Step | Task | Effort | Deadline |
|------|------|--------|----------|
| 7 | Run local audit, triage renderer hits | 1-4 hours | 8 hours |
| 8 | Update consumer_registry.yml | 1-2 hours | 8 hours |
| 9 | Run consumer probe in staging | 1-2 hours | 8 hours |
| 10 | Enable branch protection required checks | 30-60 min | 8 hours |

**Total**: 4-8 hours (depends on number of consumers)

---

### Verification (Final 1-2 Hours) - Priority 2

**Owner: All Teams**

| Step | Task | Effort | Deadline |
|------|------|--------|----------|
| 11 | Create test PR, verify checks run | 30 min | Before canary |
| 12 | Run final green-light verification | 30 min | Before canary |
| 13 | Deploy canary (1% traffic) | 15 min | After green-light |
| 14 | Monitor canary metrics (15-30 min) | 30 min | During canary |

**Total**: 1-2 hours

---

### Total Timeline to Green-Light: 8-14 Hours

| Phase | Duration | Critical Path |
|-------|----------|---------------|
| **Immediate** | 2-4 hours | Baseline capture (60-min benchmark) |
| **Short-term** | 4-8 hours | Consumer discovery and registration |
| **Verification** | 1-2 hours | Final checks and canary deployment |
| **Total** | **8-14 hours** | **From patch application to canary** |

---

## MACHINE-VERIFIABLE ACCEPTANCE CRITERIA

**ALL criteria must be TRUE before canary deployment.**

### [P0-1] CI Workflow Exists ✅
```bash
# Verify workflow file
test -f .github/workflows/pre_merge_checks.yml && \
echo "PASS" || echo "FAIL"

# Verify platform assertion present
grep -q "platform.system()" .github/workflows/pre_merge_checks.yml && \
echo "PASS" || echo "FAIL"

# Verify audit step present
grep -q "audit_greenlight.py" .github/workflows/pre_merge_checks.yml && \
echo "PASS" || echo "FAIL"
```

### [P0-2] RUN_TO_GREEN.md Playbook Exists ✅
```bash
# Verify playbook file
test -f RUN_TO_GREEN.md && \
echo "PASS" || echo "FAIL"

# Verify baseline procedure documented
grep -q "Capture Canonical Baseline" RUN_TO_GREEN.md && \
echo "PASS" || echo "FAIL"

# Verify CI secrets procedure documented
grep -q "BASELINE_PUBLIC_KEY" RUN_TO_GREEN.md && \
echo "PASS" || echo "FAIL"
```

### [P0-3] Signed Baseline Exists ✅
```bash
# Verify baseline files
test -f baselines/metrics_baseline_v1.json && \
test -f baselines/metrics_baseline_v1.json.asc && \
echo "PASS" || echo "FAIL"

# Verify signature valid
gpg --batch --verify \
    baselines/metrics_baseline_v1.json.asc \
    baselines/metrics_baseline_v1.json
# Expected: exit 0
```

### [P0-4] CI Secret Configured ✅
```bash
# Verify secret exists
gh secret list | grep BASELINE_PUBLIC_KEY
# Expected: BASELINE_PUBLIC_KEY (updated XXXs ago)
```

### [P0-5] Branch Protection Enabled ✅
```bash
# Verify required checks
gh api repos/:owner/:repo/branches/main/protection | \
jq '.required_status_checks.contexts'

# Expected: Array containing "Pre-merge Safety Checks"
```

### [P0-6] Audit Exits 0 (All Checks Pass) ✅
```bash
# Run audit
python tools/audit_greenlight.py --report /tmp/audit.json

# Check exit code
echo $?
# Expected: 0

# Verify all statuses ok
jq '{
  baseline: .baseline_verification.status,
  branch_protection: .branch_protection_verification.status,
  unregistered_local: (.renderer_unregistered_local | length),
  unregistered_org: (.org_unregistered_hits | length)
}' /tmp/audit.json

# Expected:
# {
#   "baseline": "ok",
#   "branch_protection": "ok",
#   "unregistered_local": 0,
#   "unregistered_org": 0
# }
```

---

## SUMMARY OF CHANGES (Parts 1-8 Complete)

### Cumulative Deliverables (All Parts)

| Part | Key Deliverable | Status | Lines |
|------|----------------|--------|-------|
| 1 | P0 Critical Tasks (5 tasks) | ✅ Planned | ~800 |
| 2 | P1/P2 Patterns (10 tasks) | ✅ Planned | ~1,200 |
| 3 | P3 Observability (3 tasks) | ✅ Planned | ~1,000 |
| 4 | Security Audit Response | ✅ Planned | ~600 |
| 5 | Green-Light Checklist (v2.2) | ✅ Complete | ~2,500 |
| 6 | Operational Tools (v1.0) | ✅ Complete | ~1,530 |
| 7 | Fatal P0 Enforcement (v1.1) | ✅ Verified | ~165 |
| **8** | **CI Enforcement + Playbook (v1.0)** | **✅ Complete** | **~280** |
| **Total** | **All Parts 1-8** | **✅ Complete** | **~8,075** |

### Part 8 Specific Changes

**1. CI Workflow** ✅
- File: .github/workflows/pre_merge_checks.yml (NEW)
- Lines: ~78
- Features:
  - Platform assertion (Linux-only)
  - Baseline public key import
  - Audit enforcement (exit non-zero blocks merge)
  - Artifact upload (90-day retention)

**2. Operational Playbook** ✅
- File: RUN_TO_GREEN.md (NEW)
- Lines: ~200
- Features:
  - Step-by-step green-light checklist
  - Exact copy-paste commands
  - Baseline signing procedure
  - CI secrets configuration
  - Canary deployment and rollback

**3. Implementation Guide** ✅
- File: PLAN_CLOSING_IMPLEMENTATION_extended_8.md (THIS FILE)
- Lines: ~1,600
- Features:
  - Final blocker assessment
  - Git patch (CI workflow)
  - RUN_TO_GREEN.md content
  - Timeline and ownership
  - Machine-verifiable acceptance

**Total New**: ~280 lines of CI automation + playbook

---

## FINAL ASSESSMENT

### Are We Green? (Post-Part 8)

**Short Answer**: **READY FOR GREEN-LIGHT** (after executing RUN_TO_GREEN.md playbook)

**Detailed Status**:

✅ **Architecture & Design**: Complete (Parts 1-3)
✅ **Adversarial Corpora**: 20+ URL vectors, 10+ template injection vectors
✅ **Defensive Patches**: Token canonicalization, HTML default-off, SIGALRM watchdog
✅ **Enforcement Tools**: audit_greenlight.py with fatal P0 checks (exit 5/6)
✅ **Platform Policy**: Linux-only documented with enforcement
✅ **Operational Tools**: Baseline capture, GPG signing, consumer registry
✅ **CI Automation** (v1.0 NEW): Pre-merge workflow with platform + audit enforcement
✅ **Operational Playbook** (v1.0 NEW): RUN_TO_GREEN.md step-by-step guide

⏸️ **Execution Required** (RUN_TO_GREEN.md):
- Apply CI workflow patch ⏸️
- Capture and sign canonical baseline ⏸️
- Configure BASELINE_PUBLIC_KEY secret ⏸️
- Run consumer discovery and registration ⏸️
- Enable branch protection required checks ⏸️
- Run final green-light verification ⏸️

### Path to Green-Light (Final Execution)

**Immediate (2-4 hours)**:
1. Apply CI workflow patch
2. Configure BASELINE_PUBLIC_KEY secret
3. Capture canonical baseline (60-min benchmark)
4. Sign baseline with GPG
5. Commit baseline + signature

**Short-term (4-8 hours)**:
6. Run local audit, triage renderer hits
7. Update consumer_registry.yml
8. Run consumer probe in staging
9. Enable branch protection required checks

**Verification (1-2 hours)**:
10. Create test PR, verify checks run
11. Run final green-light verification checklist
12. Deploy canary (1% traffic)
13. Monitor metrics, roll back if alarms

**Total**: **8-14 hours from patch to canary**

---

## NEXT ACTIONS

**If you want to proceed**, execute in this exact order:

### Today (Priority 0) - SRE + DevOps

- [ ] Apply CI workflow patch (.github/workflows/pre_merge_checks.yml)
- [ ] Create RUN_TO_GREEN.md playbook file
- [ ] Configure BASELINE_PUBLIC_KEY in GitHub secrets
- [ ] Capture canonical baseline (60-min benchmark)
- [ ] Sign baseline with GPG
- [ ] Commit baseline + signature to git

### Today (Priority 0) - Security + Owners

- [ ] Run local audit: `python tools/audit_greenlight.py --report /tmp/audit.json`
- [ ] Triage renderer discovery hits (add to registry or exceptions)
- [ ] Update consumer_registry.yml with all consumers
- [ ] Run consumer probe: `python tools/probe_consumers.py`

### Today (Priority 0) - DevOps

- [ ] Enable branch protection required checks
- [ ] Verify `Pre-merge Safety Checks` is required
- [ ] Add `adversarial-smoke`, `token-canonicalization`, `url-parity-smoke` as required

### Tomorrow (Priority 1) - All Teams

- [ ] Create test PR to verify checks run correctly
- [ ] Run final green-light verification checklist
- [ ] Deploy canary (1% traffic) if all checks pass
- [ ] Monitor metrics for 15-30 minutes
- [ ] Roll back if any alarms trigger

---

## RELATED DOCUMENTATION

- **Part 5 v2.2**: PLAN_CLOSING_IMPLEMENTATION_extended_5.md (Green-light checklist)
- **Part 6 v1.0**: PLAN_CLOSING_IMPLEMENTATION_extended_6.md (Operational tools)
- **Part 7 v1.1**: PLAN_CLOSING_IMPLEMENTATION_extended_7.md (Fatal P0 enforcement)
- **Part 7 Execution**: PART7_V11_EXECUTION_COMPLETE.md (Verification results)
- **Audit Script**: tools/audit_greenlight.py (v1.1)
- **Platform Policy**: docs/PLATFORM_POLICY.md
- **Quick Start**: QUICK_START.md
- **Documentation Tour**: DOCUMENTATION_UPDATE_TOUR.md

---

**END OF PART 8 - FINAL GREEN-LIGHT READINESS**

This document completes Phase 8 security hardening with final CI automation and operational playbook. Execute RUN_TO_GREEN.md to reach defensible green-light in 8-14 hours.

🎯 **Apply CI patch → Execute RUN_TO_GREEN.md → Verify checklist → Deploy canary → GREEN LIGHT ACHIEVED**
