# RUN_TO_GREEN.md

---
```yaml
document_id: "run-to-green-playbook"
version: "2.0"
date: "2025-10-18"
status: "production-ready"
purpose: "Canonical runbook for Phase 8 canary deployment"
required_checks:
  - Pre-merge Safety Checks
  - adversarial-smoke
  - token-canonicalization
  - url-parity-smoke
required_metrics:
  - audit_issue_create_failures_total
  - audit_fp_marked_total
  - collector_timeouts_total
  - parse_p99_ms
```
---

This playbook captures the exact minimal steps to reach a defensible "green light" for the Phase 8 parser/warehouse rollout.

Follow the steps in order. Run commands from the repository root. Replace environment variables and secret names with your org's equivalents.

---

## Configuration Variables (Fill Before Running)

**⚠️ REQUIRED: Set these variables before executing commands**

```bash
# Organization & Repository
export OWNER="my-org"
export REPO="parser"
export CENTRAL_REPO="security/audit-backlog"

# Infrastructure
export PUSHGATEWAY_URL="https://pushgateway.example"
export PROMETHEUS_URL="https://prometheus.example"

# GPG/KMS (for baseline signing)
export SIGNER_KEY_ID="YOUR_GPG_KEY_ID"  # Or KMS key alias

# Adversarial Testing
export SMOKE_CORPUS="adversarial_corpora/fast_smoke.json"
```

---

## Quick Prerequisites

**SRE / Owner Requirements**:
- Dedicated baseline signing key (prefer HSM/KMS)
- If using GPG locally:
  ```bash
  # Import private key (for signing step only - DO NOT COMMIT PRIVATE KEY)
  gpg --import /path/to/private-sign-key.asc

  # Export public key (safe to commit)
  gpg --export --armor "${SIGNER_KEY_ID}" > baselines/baseline_pubkey.asc
  ```

**🔒 SECURITY WARNING**:
> **NEVER commit or store private signing keys in the repo, CI secrets, or artifacts.**
> Only the *public* key or verifier material should be checked into the repo.
> Private keys MUST remain in KMS/HSM or an offline keyring with restricted access.

**CI Secrets Required**:
- `BASELINE_PUBLIC_KEY`: ASCII-armored public key (safe to store)
- `GITHUB_TOKEN`: Actions provides this by default (ensure branch protection read permission)

**Artifact Retention Policy**:
> Fallback artifacts (`adversarial_reports/fallback_*.json`) MUST be uploaded as GitHub Actions artifacts or to a private S3 bucket with ACL restricted to security & SRE teams only. **Retention: 7 days**, then auto-delete. Never commit artifacts containing raw code snippets to the repository.

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
cat baselines/metrics_baseline_v1.json | jq '.metrics, .thresholds' || exit 1

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

**Sign Baseline** (KMS Production / GPG Fallback):

**Option 1: KMS Signing (Production Recommended)**:
```bash
# Sign baseline with AWS KMS (preferred for production)
aws kms sign \
    --key-id alias/baseline-signing-key \
    --message fileb://baselines/metrics_baseline_v1.json \
    --message-type RAW \
    --signing-algorithm RSASSA_PKCS1_V1_5_SHA_256 \
    --output text \
    --query Signature | base64 -d > baselines/metrics_baseline_v1.json.sig

# Verify signature (STRICT - must exit 0)
aws kms verify \
    --key-id alias/baseline-signing-key \
    --message fileb://baselines/metrics_baseline_v1.json \
    --message-type RAW \
    --signing-algorithm RSASSA_PKCS1_V1_5_SHA_256 \
    --signature fileb://baselines/metrics_baseline_v1.json.sig || exit 1

# Expected: "SignatureValid": true
```

**Option 2: GPG Signing (Local Dev / Fallback)**:
```bash
# Sign with dedicated GPG key (offline preferred)
gpg --armor \
    --output baselines/metrics_baseline_v1.json.asc \
    --detach-sign baselines/metrics_baseline_v1.json || exit 1

# Verify signature locally (STRICT - must exit 0)
gpg --batch --verify \
    baselines/metrics_baseline_v1.json.asc \
    baselines/metrics_baseline_v1.json || exit 1

# Expected: "Good signature from ..." with exit code 0
```

**Production Recommendation**: Use KMS/HSM-backed signing for production baselines to avoid ad-hoc key management risks. GPG signing is acceptable for local development and testing.

**Commit Baseline**:
```bash
# Add baseline + signature (PUBLIC KEY ONLY - NEVER PRIVATE KEY)
git add baselines/metrics_baseline_v1.json
git add baselines/metrics_baseline_v1.json.asc
git add baselines/baseline_pubkey.asc  # Public key safe to commit

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

**Verification** (Machine-Readable):
```bash
# Verify baseline files exist (exit 1 on failure)
test -f baselines/metrics_baseline_v1.json || { echo "❌ Baseline JSON missing"; exit 1; }
test -f baselines/metrics_baseline_v1.json.asc || { echo "❌ Baseline signature missing"; exit 1; }
echo "✅ Baseline files committed"

# Verify signature (STRICT - exit 1 on failure)
gpg --batch --verify \
    baselines/metrics_baseline_v1.json.asc \
    baselines/metrics_baseline_v1.json || { echo "❌ Signature verification failed"; exit 1; }
echo "✅ Signature verified"
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

# Generate audit_id for traceability
export AUDIT_ID="audit-$(date +%s)-$(uuidgen | cut -d- -f1)"
echo "Audit ID: ${AUDIT_ID}"

# Run audit with audit_id
python tools/audit_greenlight.py \
    --report "./adversarial_reports/local_audit_${AUDIT_ID}.json" || exit 1

# Review report
jq '.' "./adversarial_reports/local_audit_${AUDIT_ID}.json"
```

**Resolve Until All Green** (Deterministic Checks):
```bash
# Check baseline verification (exit 1 on failure)
STATUS=$(jq -r '.baseline_verification.status' "./adversarial_reports/local_audit_${AUDIT_ID}.json")
if [ "$STATUS" != "ok" ]; then
    echo "❌ Baseline verification failed: $STATUS"
    exit 1
fi
echo "✅ Baseline verification: ok"

# Check unregistered renderers (local) - must be 0
UNREGISTERED_LOCAL=$(jq '.renderer_unregistered_local | length' "./adversarial_reports/local_audit_${AUDIT_ID}.json")
if [ "$UNREGISTERED_LOCAL" -ne 0 ]; then
    echo "❌ Found $UNREGISTERED_LOCAL unregistered local renderers"
    exit 1
fi
echo "✅ Unregistered local renderers: 0"

# Check unregistered renderers (org-wide) - must be 0
UNREGISTERED_ORG=$(jq '.org_unregistered_hits | length' "./adversarial_reports/local_audit_${AUDIT_ID}.json")
if [ "$UNREGISTERED_ORG" -ne 0 ]; then
    echo "❌ Found $UNREGISTERED_ORG unregistered org-wide hits"
    exit 1
fi
echo "✅ Unregistered org-wide hits: 0"

# Check branch protection
BP_STATUS=$(jq -r '.branch_protection_verification.status' "./adversarial_reports/local_audit_${AUDIT_ID}.json")
if [ "$BP_STATUS" != "ok" ]; then
    echo "❌ Branch protection verification failed: $BP_STATUS"
    exit 1
fi
echo "✅ Branch protection: ok"
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

**⚠️ NOTE**: `tools/probe_consumers.py` must exist before running this step.

```bash
# Install dependencies
pip install requests pyyaml

# Run consumer probe
python tools/probe_consumers.py \
    --registry consumer_registry.yml \
    --outdir consumer_probe_reports || exit 1

# Inspect reports
ls consumer_probe_reports/
cat consumer_probe_reports/*.json | jq '.'

# Check for violations (STRICT - exit 1 if any found)
VIOLATIONS=$(cat consumer_probe_reports/*.json | jq 'select(.evaluated == true or .reflected == true)' | wc -l)
if [ "$VIOLATIONS" -ne 0 ]; then
    echo "❌ Found $VIOLATIONS probe violations"
    cat consumer_probe_reports/*.json | jq 'select(.evaluated == true or .reflected == true)'
    exit 1
fi
echo "✅ No probe violations detected"
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

**Required Workflow Files**:
- `.github/workflows/pre_merge_checks.yml` → job: `Pre-merge Safety Checks`
- `.github/workflows/adversarial_smoke.yml` → job: `adversarial-smoke` (if exists)
- Tests must include: `token-canonicalization`, `url-parity-smoke`

**Required Checks for Parser Repo**:
- `Pre-merge Safety Checks` (workflow from Phase 8)
- `adversarial-smoke` (fast adversarial PR job)
- `token-canonicalization` (parser unit tests)
- `url-parity-smoke` (URL normalization tests)

**GitHub UI**:
```
1. Go to: Settings → Branches → Branch protection rules → main
2. Add required status checks:
   - Pre-merge Safety Checks
   - adversarial-smoke (if workflow exists)
   - token-canonicalization
   - url-parity-smoke
3. Save changes
```

**GitHub CLI** (Using Variables):
```bash
gh api repos/${OWNER}/${REPO}/branches/main/protection \
    -X PUT \
    -F required_status_checks[strict]=true \
    -F required_status_checks[contexts][]=Pre-merge Safety Checks \
    -F required_status_checks[contexts][]=token-canonicalization \
    -F required_status_checks[contexts][]=url-parity-smoke || exit 1
```

**Consumer Repos** (where applicable):
```bash
# For each consumer repo with renders_metadata: true
CONSUMER_REPO="frontend-web"
gh api repos/${OWNER}/${CONSUMER_REPO}/branches/main/protection \
    -X PUT \
    -F required_status_checks[strict]=true \
    -F required_status_checks[contexts][]=consumer-ssti-litmus || exit 1
```

**Verification** (Deterministic):
```bash
# Verify required checks configured (exit 1 on failure)
CHECKS=$(gh api repos/${OWNER}/${REPO}/branches/main/protection | jq -r '.required_status_checks.contexts[]')

echo "$CHECKS" | grep -q "Pre-merge Safety Checks" || { echo "❌ Missing: Pre-merge Safety Checks"; exit 1; }
echo "$CHECKS" | grep -q "token-canonicalization" || { echo "❌ Missing: token-canonicalization"; exit 1; }
echo "$CHECKS" | grep -q "url-parity-smoke" || { echo "❌ Missing: url-parity-smoke"; exit 1; }

echo "✅ All required checks configured"
```

---

## Step 6: Configure CI Secrets (DevOps)

**Owner**: DevOps
**Effort**: 15-30 minutes
**Deadline**: Before CI workflow runs

**Export Public Key** (NEVER EXPORT PRIVATE KEY):
```bash
# Export baseline public key (safe to commit/share)
gpg --export --armor "${SIGNER_KEY_ID}" > /tmp/baseline_pubkey.asc || exit 1

# Verify key exported
cat /tmp/baseline_pubkey.asc | head -1 | grep -q "BEGIN PGP PUBLIC KEY BLOCK" || { echo "❌ Invalid key format"; exit 1; }
echo "✅ Public key exported"
```

**Add to GitHub Secrets**:
```
1. Go to: Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: BASELINE_PUBLIC_KEY
4. Value: Paste entire content of /tmp/baseline_pubkey.asc
5. Click "Add secret"
```

**Verification** (Deterministic):
```bash
# Verify secret exists (exit 1 on failure)
gh secret list | grep -q "BASELINE_PUBLIC_KEY" || { echo "❌ Secret not found"; exit 1; }
echo "✅ BASELINE_PUBLIC_KEY secret configured"
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

**Verify Checks Run** (Deterministic):
```bash
# Wait for checks to complete
sleep 30

# Check PR status (exit 1 if any check fails)
gh pr checks || { echo "❌ PR checks failed"; exit 1; }
echo "✅ All PR checks passed"

# Verify audit report artifact uploaded
RUN_ID=$(gh run list --workflow=pre_merge_checks.yml --limit 1 --json databaseId --jq '.[0].databaseId')
if [ -z "$RUN_ID" ]; then
    echo "❌ No workflow run found"
    exit 1
fi

# Download audit report
gh run download "$RUN_ID" --name pr-audit-report --dir /tmp/pr-audit || { echo "⚠️ No audit artifact (may not be generated)"; }
if [ -f /tmp/pr-audit/pr_audit.json ]; then
    cat /tmp/pr-audit/pr_audit.json | jq '.'
    echo "✅ Audit report downloaded"
fi
```

**Canary Deployment**:
After PR merges and all checks pass:

```bash
# Start canary with low traffic (adjust replicas as needed)
kubectl scale deployment/parser-canary --replicas=1 || exit 1

# Verify canary pods running
kubectl wait --for=condition=ready pod -l app=parser-canary --timeout=300s || { echo "❌ Canary pods not ready"; exit 1; }
echo "✅ Canary pods ready"

# Monitor metrics (15-30 minutes):
# - collector_timeouts_total (no >50% increase)
# - parse_p99_ms (<= baseline * 1.5)
# - collector_truncated_total (no unexpected spike)
# - adversarial_failure_total (must be zero)

# Check metrics (if Prometheus accessible)
if curl -s "${PROMETHEUS_URL}/api/v1/query?query=collector_timeouts_total" >/dev/null 2>&1; then
    TIMEOUTS=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=collector_timeouts_total" | jq -r '.data.result[0].value[1]')
    echo "Collector timeouts: ${TIMEOUTS}"

    P99=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=parse_p99_ms" | jq -r '.data.result[0].value[1]')
    echo "Parse P99: ${P99}ms"
else
    echo "⚠️ Prometheus not accessible - manual metric verification required"
fi
```

**If Canary Alarms Trigger** → Follow Step 8 (Rollback)

---

## Step 8: Canary Rollback (Runbook)

**Owner**: SRE
**Trigger**: Any canary alarm (timeout spike, P99 breach, adversarial failure)
**Deadline**: Immediate

**Safe Rollback Procedure** (Deterministic):
```bash
set -e  # Exit on any error

# 1. Scale down canary instances immediately
kubectl scale deployment/parser-canary --replicas=0 || exit 1
echo "✅ Canary scaled to 0"

# 2. Revert to previous stable version
kubectl rollout undo deployment/parser-service || exit 1
echo "✅ Rolled back to previous version"

# 3. Wait for stable pods to be ready
kubectl wait --for=condition=ready pod -l app=parser-service --timeout=300s || { echo "❌ Rollback failed - pods not ready"; exit 1; }
echo "✅ Stable pods ready"

# 4. Verify stable version running
STABLE_PODS=$(kubectl get pods -l app=parser-service -o json | jq '.items | length')
if [ "$STABLE_PODS" -eq 0 ]; then
    echo "❌ No stable pods running after rollback"
    exit 1
fi
echo "✅ Verified $STABLE_PODS stable pod(s) running"

# 5. Verify traffic routing to stable version only
kubectl get service parser-service -o yaml | grep -q "version: canary" && { echo "⚠️ WARNING: Traffic still routing to canary"; }
```

**Post-Rollback**:
```bash
# 6. Collect and preserve audit reports
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p incident_reports/${TIMESTAMP}
cp adversarial_reports/*.json incident_reports/${TIMESTAMP}/ || true
echo "✅ Audit reports preserved in incident_reports/${TIMESTAMP}/"

# 7. Create incident ticket
gh issue create \
    --repo "${OWNER}/${REPO}" \
    --title "P0: Canary rollback - $(date +%Y-%m-%d)" \
    --body "Canary rollback triggered at $(date).

Audit reports: incident_reports/${TIMESTAMP}/
Audit ID: ${AUDIT_ID}

Next steps:
1. Review audit reports for failures
2. Triage failing adversarial vectors
3. Fix root cause
4. Retest in staging
5. Retry canary deployment" \
    --label "P0,canary-rollback" \
    --assignee "@sre-lead,@security-lead" || exit 1

echo "✅ Incident ticket created"

# 8. Triage failing adversarial vectors
echo "Failed adversarial vectors:"
cat incident_reports/${TIMESTAMP}/*.json | jq '.failures' 2>/dev/null || echo "No failures found in audit reports"
```

---

## Useful Commands (Summary)

```bash
# Run PR audit (as CI does) with audit_id
export AUDIT_ID="audit-$(date +%s)-$(uuidgen | cut -d- -f1)"
python tools/audit_greenlight.py --report "adversarial_reports/pr_audit_${AUDIT_ID}.json" || exit 1

# Probe consumers (if tool exists)
python tools/probe_consumers.py \
    --registry consumer_registry.yml \
    --outdir consumer_probe_reports || exit 1

# Run small adversarial smoke (if tool exists)
python -u tools/run_adversarial.py \
    "${SMOKE_CORPUS}" \
    --runs 1 \
    --report /tmp/adv_smoke.json || exit 1

# Run parity & token tests (must be non-skippable)
pytest -q tests/test_url_normalization_parity.py || exit 1
pytest -q tests/test_malicious_token_methods.py || exit 1

# Check exit code deterministically
if [ $? -eq 0 ]; then
    echo "✅ Tests passed"
else
    echo "❌ Tests failed"
    exit 1
fi
```

---

## Owners & Contact Points

| Role | Owner | Responsibility |
|------|-------|----------------|
| **Tech Lead** | @tech-lead | Platform policy decision |
| **SRE** | @sre-lead | Baseline capture/signing, monitoring/alerts, rollback |
| **DevOps** | @devops-lead | CI secrets, branch protection, artifact retention |
| **Security** | @security-lead | Registry audit, exceptions, probe verification |
| **Consumer Owners** | @consumer-teams | SSTI litmus tests, probe response |

**Update this section with exact contacts and SLAs for triage.**

---

## Green-Light Verification Checklist

Before declaring green-light, verify ALL items pass:

### P0 Checklist (MUST PASS)

**[P0-1] Signed Baseline Exists & Audit Green**:
```bash
# Verify baseline signature (exit 1 on failure)
gpg --batch --verify \
    baselines/metrics_baseline_v1.json.asc \
    baselines/metrics_baseline_v1.json || exit 1

# Run audit
export AUDIT_ID="audit-$(date +%s)-$(uuidgen | cut -d- -f1)"
python tools/audit_greenlight.py --report "/tmp/audit_${AUDIT_ID}.json" || exit 1

# Verify audit status (exit 1 on failure)
STATUS=$(jq -r '.baseline_verification.status' "/tmp/audit_${AUDIT_ID}.json")
if [ "$STATUS" != "ok" ]; then
    echo "❌ Baseline verification failed: $STATUS"
    exit 1
fi
echo "✅ P0-1: Baseline verified"
```

**[P0-2] Consumer Probe: No Reflection/SSTI** (if tool exists):
```bash
# Run probe
python tools/probe_consumers.py \
    --registry consumer_registry.yml \
    --report /tmp/probe.json || exit 1

# Verify no violations (exit 1 on failure)
VIOLATIONS=$(jq '.violations | length' /tmp/probe.json 2>/dev/null || echo "0")
if [ "$VIOLATIONS" -ne 0 ]; then
    echo "❌ Found $VIOLATIONS probe violations"
    jq '.violations' /tmp/probe.json
    exit 1
fi
echo "✅ P0-2: No probe violations"
```

**[P0-3] PR-Smoke Parity Tests (Blocking)**:
```bash
# Run tests (exit 1 on failure)
pytest -q tests/test_url_normalization_parity.py || { echo "❌ URL parity tests failed"; exit 1; }
pytest -q tests/test_malicious_token_methods.py || { echo "❌ Token tests failed"; exit 1; }
echo "✅ P0-3: Parity tests passed"
```

**[P0-4] Renderer Discovery Audit**:
```bash
# Check unregistered renderers (exit 1 if any found)
UNREGISTERED_LOCAL=$(jq '.renderer_unregistered_local | length' "/tmp/audit_${AUDIT_ID}.json")
UNREGISTERED_ORG=$(jq '.org_unregistered_hits | length' "/tmp/audit_${AUDIT_ID}.json")

if [ "$UNREGISTERED_LOCAL" -ne 0 ] || [ "$UNREGISTERED_ORG" -ne 0 ]; then
    echo "❌ Found unregistered renderers: local=$UNREGISTERED_LOCAL, org=$UNREGISTERED_ORG"
    exit 1
fi
echo "✅ P0-4: No unregistered renderers"
```

**[P0-5] Platform Assertion in CI**:
```bash
# Verify workflow file exists
test -f .github/workflows/pre_merge_checks.yml || { echo "❌ Workflow missing"; exit 1; }

# Verify platform assertion step present
grep -q "platform.system()" .github/workflows/pre_merge_checks.yml || { echo "❌ Platform assertion missing"; exit 1; }

echo "✅ P0-5: Platform assertion configured"
```

**[P0-6] Branch Protection Required Status Checks**:
```bash
# Verify required check configured
CHECKS=$(gh api repos/${OWNER}/${REPO}/branches/main/protection | jq -r '.required_status_checks.contexts[]')

echo "$CHECKS" | grep -q "Pre-merge Safety Checks" || { echo "❌ Missing required check"; exit 1; }

echo "✅ P0-6: Branch protection configured"
```

**[P0-7] Metrics & Alerts Configured**:
```bash
# Verify metrics exist in Prometheus (if accessible)
if curl -s "${PROMETHEUS_URL}/api/v1/query?query=collector_timeouts_total" >/dev/null 2>&1; then
    METRICS=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=collector_timeouts_total" | jq -r '.data.result | length')

    if [ "$METRICS" -eq 0 ]; then
        echo "⚠️ WARNING: No collector_timeouts_total metrics found"
    else
        echo "✅ P0-7: Metrics configured ($METRICS series)"
    fi
else
    echo "⚠️ WARNING: Prometheus not accessible - manual verification required"
fi

# Verify alert rules file exists
test -f prometheus/rules/audit_rules.yml || { echo "❌ Alert rules missing"; exit 1; }
echo "✅ P0-7: Alert rules configured"
```

### Final Verification

**Run All Checks** (Consolidated):
```bash
set -e  # Exit on any error

# Run full audit
export AUDIT_ID="audit-$(date +%s)-$(uuidgen | cut -d- -f1)"
python tools/audit_greenlight.py --report "/tmp/final_audit_${AUDIT_ID}.json" || exit 1

# Verify all checks passed (deterministic)
BASELINE_STATUS=$(jq -r '.baseline_verification.status' "/tmp/final_audit_${AUDIT_ID}.json")
BP_STATUS=$(jq -r '.branch_protection_verification.status' "/tmp/final_audit_${AUDIT_ID}.json")
UNREGISTERED_LOCAL=$(jq '.renderer_unregistered_local | length' "/tmp/final_audit_${AUDIT_ID}.json")
UNREGISTERED_ORG=$(jq '.org_unregistered_hits | length' "/tmp/final_audit_${AUDIT_ID}.json")

# Assert all conditions
[ "$BASELINE_STATUS" = "ok" ] || { echo "❌ Baseline: $BASELINE_STATUS"; exit 1; }
[ "$BP_STATUS" = "ok" ] || { echo "❌ Branch protection: $BP_STATUS"; exit 1; }
[ "$UNREGISTERED_LOCAL" -eq 0 ] || { echo "❌ Unregistered local: $UNREGISTERED_LOCAL"; exit 1; }
[ "$UNREGISTERED_ORG" -eq 0 ] || { echo "❌ Unregistered org: $UNREGISTERED_ORG"; exit 1; }

echo ""
echo "🎯 Final Audit Results:"
echo "  Baseline: $BASELINE_STATUS"
echo "  Branch Protection: $BP_STATUS"
echo "  Unregistered Local: $UNREGISTERED_LOCAL"
echo "  Unregistered Org: $UNREGISTERED_ORG"
echo "  Audit ID: $AUDIT_ID"
echo ""
echo "✅ GREEN LIGHT - Ready for canary deployment 🚀"
```

**If All Pass**: ✅ **GREEN LIGHT - Ready for canary deployment**

**If Any Fail**: ❌ **BLOCKED - Fix failures and re-run checklist**

---

## Required Metrics & Alert Rules

**Metrics to Monitor During Canary**:

| Metric | Source | Alert Threshold | Action |
|--------|--------|-----------------|--------|
| `audit_issue_create_failures_total` | `tools/create_issues_for_unregistered_hits.py` | > 0 | **PAGE immediately** |
| `audit_fp_marked_total` | FP label sync | > 10% of total | Warn, review patterns |
| `collector_timeouts_total` | Parser collectors | > 50% increase | Investigate performance |
| `parse_p99_ms` | Parser metrics | > baseline × 1.5 | Investigate regression |

**Alert Rule File**: `prometheus/rules/audit_rules.yml`

**Example Alert**:
```yaml
groups:
  - name: audit_critical
    rules:
      - alert: AuditIssueCreationFailed
        expr: audit_issue_create_failures_total > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Audit issue creation failed - immediate investigation required"
```

---

**Keep this file updated with exact owner contacts & expected SLAs for triage.**

**Document Version**: 2.0 (Refactored for Machine-Readability & Security)
**Last Updated**: 2025-10-18
**Status**: Production-Ready
