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
$ gpg --verify baselines/metrics_baseline_v1.json.asc"

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

**[P0-1] Signed Baseline Exists & Audit Green**:
```bash
gpg --batch --verify \
    baselines/metrics_baseline_v1.json.asc \
    baselines/metrics_baseline_v1.json

python tools/audit_greenlight.py --report /tmp/audit.json

jq '.baseline_verification.status' /tmp/audit.json
# Expected: "ok"
```

**[P0-2] Consumer Probe: No Reflection/SSTI**:
```bash
python tools/probe_consumers.py \
    --registry consumer_registry.yml \
    --report /tmp/probe.json

jq '.status, .violations' /tmp/probe.json
# Expected: status == "ok", violations == []
```

**[P0-3] PR-Smoke Parity Tests (Blocking)**:
```bash
pytest -q tests/test_url_normalization_parity.py
pytest -q tests/test_malicious_token_methods.py
# Expected: rc 0, no skips
```

**[P0-4] Renderer Discovery Audit**:
```bash
python tools/audit_greenlight.py --report /tmp/audit.json

jq '.renderer_unregistered_local, .org_unregistered_hits' /tmp/audit.json
# Expected: both empty arrays []
```

**[P0-5] Platform Assertion in CI**:
```bash
# Verify workflow file exists
test -f .github/workflows/pre_merge_checks.yml && \
echo "✅ PASS" || echo "❌ FAIL"

# Verify platform assertion step present
grep -q "platform.system()" .github/workflows/pre_merge_checks.yml && \
echo "✅ PASS" || echo "❌ FAIL"
```

**[P0-6] Branch Protection Required Status Checks**:
```bash
gh api repos/:owner/:repo/branches/main/protection | \
jq '.required_status_checks.contexts[] | select(. == "Pre-merge Safety Checks")'

# Expected: "Pre-merge Safety Checks"
```

**[P0-7] Metrics & Alerts Configured**:
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
