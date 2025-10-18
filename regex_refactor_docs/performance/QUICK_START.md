# Quick Start - Phase 8 Security Hardening

**Purpose**: Fast onboarding guide for Phase 8 reference implementations
**Location**: All files in `regex_refactor_docs/performance/`
**Status**: ✅ Ready for production adoption

---

## 30-Second Overview

Phase 8 security hardening is **complete** in the performance/ directory with:

✅ **7 planning documents** - Complete implementation guides
✅ **5 operational tools** - Audit, baseline, signing, registry
✅ **3 execution reports** - Verification and compliance
✅ **Fatal P0 enforcement** - Exit codes 5/6 block deployment
✅ **Platform policy** - Linux-only with CI enforcement

**Total**: ~1,681 lines of operational code, production-ready

---

## Essential Files (Must Read)

### 1. Green-Light Checklist (Start Here)
**File**: `PLAN_CLOSING_IMPLEMENTATION_extended_5.md`
**Lines**: ~2,500
**Read Time**: 20 minutes

**What It Contains**:
- 18 acceptance criteria (P0/P1/P2/P3)
- Exact verification commands
- Timeline: 24.5 hours total effort
- Success metrics

**Why Read First**: Tells you exactly what must pass before deployment

---

### 2. Operational Tools Guide
**File**: `PLAN_CLOSING_IMPLEMENTATION_extended_6.md`
**Lines**: ~3,000
**Read Time**: 30 minutes

**What It Contains**:
- 6 actions with step-by-step implementation
- Tool specifications (audit, baseline, signing)
- Consumer registry design
- Timeline: 24-72 hours

**Why Read Second**: Shows you how to implement enforcement

---

### 3. Fatal Enforcement Guide
**File**: `PLAN_CLOSING_IMPLEMENTATION_extended_7.md`
**Lines**: ~1,600
**Read Time**: 20 minutes

**What It Contains**:
- 2 critical patches (exit codes + platform policy)
- Machine-verifiable acceptance
- Timeline: 48-72 hours

**Why Read Third**: Ensures P0 checks actually block deployment

---

## Essential Tools (Must Use)

### 1. Green-Light Audit Script
**File**: `tools/audit_greenlight.py`
**Lines**: 490
**Language**: Python 3.12+

**Quick Usage**:
```bash
# Run audit (blocks deployment if P0 fails)
python tools/audit_greenlight.py --report /tmp/audit.json

# Check exit code
echo $?
# 0 = GREEN LIGHT
# 5 = Branch protection failed (FATAL)
# 6 = Baseline missing/failed (FATAL)
```

**Exit Codes**:
- **0**: All checks passed ✅ **DEPLOY**
- **2**: Warnings (baseline breach) ⚠️ Proceed with caution
- **5**: Branch protection misconfigured ❌ **BLOCKS DEPLOYMENT**
- **6**: Baseline missing/unsigned ❌ **BLOCKS DEPLOYMENT**

---

### 2. Baseline Capture Tool
**File**: `tools/capture_baseline_metrics.py`
**Lines**: 278

**Quick Usage**:
```bash
# Capture 60-min baseline
python tools/capture_baseline_metrics.py \
    --duration 3600 \
    --out baselines/metrics_baseline_v1.json

# Auto mode (for audit integration)
python tools/capture_baseline_metrics.py \
    --auto \
    --out /tmp/current_metrics.json
```

**When to Run**: Once initially, then monthly

---

### 3. Baseline Signing Tool
**File**: `tools/sign_baseline.py`
**Lines**: 305

**Quick Usage**:
```bash
# Sign baseline with GPG
python tools/sign_baseline.py \
    --baseline baselines/metrics_baseline_v1.json \
    --signer sre-lead@example.com

# Verify signature
python tools/sign_baseline.py \
    --verify baselines/metrics_baseline_v1_signed.json
```

**Requirements**: GPG installed (`apt-get install gnupg`)

---

### 4. Consumer Registry
**File**: `consumer_registry.yml`
**Lines**: 270
**Format**: YAML

**Quick Edit**:
```yaml
consumers:
  - name: "my-service"
    repo: "org/my-service"
    renders_metadata: true
    ssti_protection:
      test_file: "tests/test_ssti_litmus.py"
      autoescape_enforced: true
    probe_url: "https://staging.example.com/__probe__"
    required_checks:
      - "consumer-ssti-litmus"
```

**When to Update**: When adding new consumer that renders metadata

---

## Essential Policies (Must Follow)

### 1. Platform Policy
**File**: `docs/PLATFORM_POLICY.md`
**Lines**: 338
**Decision**: **Linux-only** (Windows BLOCKED)

**Key Rules**:
- ✅ Production: Linux only (Ubuntu 22.04+)
- ❌ Windows: BLOCKED (no SIGALRM timeout)
- ⚠️ macOS: Development/testing only

**CI Assertion** (add to all workflows):
```yaml
- name: Enforce platform policy
  run: |
    python -c "import platform,sys; sys.exit(0) if platform.system()=='Linux' else sys.exit(2)"
```

**Windows Support**: Requires 2-3 weeks (subprocess worker pool)

---

## 5-Minute Quickstart

### Step 1: Read Green-Light Checklist (5 min)
```bash
cat PLAN_CLOSING_IMPLEMENTATION_extended_5.md | grep "Acceptance Criteria" -A 50
```

### Step 2: Run Audit (2 min)
```bash
python tools/audit_greenlight.py --report /tmp/audit.json
echo "Exit code: $?"
```

### Step 3: Check Report (1 min)
```bash
cat /tmp/audit.json | jq '.baseline_verification.status, .branch_protection.status'
```

### Step 4: Review Platform Policy (2 min)
```bash
cat docs/PLATFORM_POLICY.md | grep -A 10 "Default Policy"
```

**Result**: You now understand critical enforcement gates

---

## 1-Hour Deep Dive

### Phase 1: Understand Acceptance Criteria (20 min)
1. Read `PLAN_CLOSING_IMPLEMENTATION_extended_5.md` (Part 3: Green-Light Checklist)
2. Note P0 items (5 critical security tasks)
3. Review machine-verifiable commands

### Phase 2: Understand Tools (20 min)
1. Read `tools/audit_greenlight.py` docstring and main()
2. Read `tools/capture_baseline_metrics.py` usage
3. Read `consumer_registry.yml` structure

### Phase 3: Understand Enforcement (20 min)
1. Read `PLAN_CLOSING_IMPLEMENTATION_extended_7.md` (Patch 1 & 2)
2. Understand exit codes (0, 2, 5, 6)
3. Review `docs/PLATFORM_POLICY.md` enforcement

**Result**: Ready to integrate tools into production

---

## Common Tasks

### Task: Add New Consumer to Registry
```bash
# Edit consumer_registry.yml
vi consumer_registry.yml

# Add entry:
consumers:
  - name: "new-service"
    repo: "org/new-service"
    renders_metadata: true
    ssti_protection:
      test_file: "tests/test_consumer_ssti_litmus.py"
      autoescape_enforced: true
    probe_url: "https://staging-new.example.com/__probe__"
    required_checks:
      - "consumer-ssti-litmus"
    owner: "team@example.com"
```

### Task: Capture New Baseline
```bash
# Capture (60-min benchmark)
python tools/capture_baseline_metrics.py \
    --duration 3600 \
    --out baselines/metrics_baseline_v2.json

# Sign
python tools/sign_baseline.py \
    --baseline baselines/metrics_baseline_v2.json \
    --signer sre-lead@example.com

# Verify
python tools/sign_baseline.py \
    --verify baselines/metrics_baseline_v2_signed.json

# Commit
git add baselines/metrics_baseline_v2*
git commit -m "baseline: Update canonical baseline to v2"
git push
```

### Task: Run Pre-Deployment Audit
```bash
# Set GitHub token (for branch protection queries)
export GITHUB_TOKEN="ghp_..."

# Run audit
python tools/audit_greenlight.py \
    --report audit_reports/audit_$(date +%Y%m%d).json \
    --registry consumer_registry.yml \
    --baseline baselines/metrics_baseline_v1_signed.json

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ GREEN LIGHT - Deploy approved"
else
    echo "❌ BLOCKED - Fix P0 failures before deployment"
fi

# Review report
cat audit_reports/audit_$(date +%Y%m%d).json | jq '.'
```

### Task: Enforce Platform Policy in CI
```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    runs-on: ubuntu-latest  # Enforces Linux
    steps:
      - uses: actions/checkout@v4

      # Platform assertion (MUST be first)
      - name: Enforce platform policy
        run: |
          python -c "import platform,sys; sys.exit(0) if platform.system()=='Linux' else sys.exit(2)"

      # Green-light audit (MUST pass before deploy)
      - name: Run green-light audit
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python tools/audit_greenlight.py --report audit_reports/ci_audit.json

      # Deployment proceeds only if audit exit 0
      - name: Deploy
        if: success()
        run: |
          ./deploy.sh
```

---

## Troubleshooting

### Issue: Audit exits with code 6 (missing baseline)
**Fix**:
```bash
# Capture baseline
python tools/capture_baseline_metrics.py --duration 3600 --out baselines/metrics_baseline_v1.json

# Sign baseline
python tools/sign_baseline.py --baseline baselines/metrics_baseline_v1.json --signer sre-lead@example.com

# Commit
git add baselines/metrics_baseline_v1*
git commit -m "baseline: Add canonical baseline v1"
git push

# Re-run audit
python tools/audit_greenlight.py --report /tmp/audit.json
```

### Issue: Audit exits with code 5 (branch protection)
**Fix**:
```bash
# Check which consumers have missing protection
cat /tmp/audit.json | jq '.branch_protection.violations'

# For each violation, enable required checks in GitHub:
# Settings → Branches → Branch protection rules → main
# Add required status checks: consumer-ssti-litmus, url-parity-smoke, etc.

# Or via gh CLI:
gh api repos/org/consumer-repo/branches/main/protection \
    -X PUT \
    -F required_status_checks[strict]=true \
    -F required_status_checks[contexts][]=consumer-ssti-litmus

# Re-run audit
python tools/audit_greenlight.py --report /tmp/audit.json
```

### Issue: GITHUB_TOKEN not set (branch protection skipped)
**Fix**:
```bash
# Development: Skip branch protection (non-fatal)
python tools/audit_greenlight.py --report /tmp/audit.json
# Will skip branch protection but still run other checks

# CI: Set GITHUB_TOKEN (required)
# .github/workflows/audit.yml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Full Documentation

For complete details, see:

**DOCUMENTATION_UPDATE_TOUR.md** - Complete map of all 27 files (~115,500 lines)

**Key Sections**:
- Planning Documents Tour (7 files)
- Execution Reports Tour (3 files)
- Tools & Scripts Tour (5 files)
- Policy Documents Tour (3 files)
- Reading Paths (security reviewers, DevOps, product owners)

---

## Timeline to Production

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Review** | 2-4 hours | Read docs, understand tools |
| **Copy Files** | 1-2 hours | Copy tools + docs to production |
| **Baseline** | 2-4 hours | Capture + sign baseline (60-min benchmark) |
| **CI Integration** | 2-4 hours | Add audit to deployment pipeline |
| **Consumer Registration** | 4-8 hours | Register all consumers |
| **Verification** | 1-2 hours | Run audit, verify exit 0 |
| **Total** | **12-24 hours** | **Full production deployment** |

---

## Success Criteria

Before deploying to production, verify:

✅ Audit exits with code 0 (all P0 checks passing)
✅ Baseline captured and GPG-signed
✅ Platform policy documented (Linux-only)
✅ All consumers registered in consumer_registry.yml
✅ Branch protection enabled for all consumers
✅ CI workflows include platform assertion
✅ GITHUB_TOKEN set in CI environment

**Command to Verify**:
```bash
python tools/audit_greenlight.py --report /tmp/final_audit.json && \
echo "✅ GREEN LIGHT - Ready for production" || \
echo "❌ BLOCKED - Fix P0 failures"
```

---

## Next Steps

1. **Read**: PLAN_CLOSING_IMPLEMENTATION_extended_5.md (green-light checklist)
2. **Run**: `python tools/audit_greenlight.py --report /tmp/audit.json`
3. **Review**: Exit code and report
4. **Fix**: Any P0 failures (exit 5/6)
5. **Deploy**: When audit returns 0

**Questions?** See DOCUMENTATION_UPDATE_TOUR.md for complete guide

---

**END OF QUICK START**

This quick start gets you operational with Phase 8 security hardening in **5 minutes to 1 hour** depending on depth needed.

🎯 **Start Here**: Run audit script → check exit code → fix P0 failures → deploy
