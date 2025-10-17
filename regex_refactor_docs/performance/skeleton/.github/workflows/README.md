# CI/CD Workflows - Phase 8 Security Hardening

**Status**: Reference Implementation
**Purpose**: Drop-in CI workflows for production repository
**Security Level**: P0 (CRITICAL)

---

## Overview

This directory contains CI/CD workflow configurations that enforce Phase 8 security hardening requirements. These workflows prevent security regressions by blocking PRs that introduce normalization bypass vulnerabilities.

**Key Principle**: **Security gates before merge, not after deployment.**

---

## Available Workflows

### 1. `pr-security-gate.yml` - URL Normalization Parity Enforcement (P0)

**Purpose**: Enforce URL normalization parity across collectors and fetchers

**Triggers**:
- Pull requests to `main`, `develop`, `release/**` branches
- Changes to security-critical files:
  - `src/doxstrux/markdown/utils/url_utils.py`
  - `src/doxstrux/markdown/security/validators.py`
  - `src/doxstrux/markdown/collectors_phase8/**`
  - `src/doxstrux/markdown/fetchers/**`
  - `tests/test_url_normalization_parity.py`

**Success Criteria** (from PLAN_CLOSING_IMPLEMENTATION.md P0-1):
1. ✅ All 14 parity tests pass (`test_url_normalization_parity.py`)
2. ✅ Exactly 1 `normalize_url` definition exists (`utils/url_utils.py`)
3. ✅ All collectors import from `url_utils.py` (not local implementations)
4. ✅ No dangerous URL patterns in diff (protocol-relative, `javascript:`, etc.)

**Failure Behavior**:
- PR blocked from merging
- Comment added to PR with failure details
- Security audit skipped (depends on parity tests passing)

**Artifacts**:
- `parity-test-results.xml` (JUnit format)
- `htmlcov/` (Coverage report)
- Retention: 30 days

---

## Integration Guide

### Step 1: Copy Workflow to Production

```bash
# From project root:
cp -r regex_refactor_docs/performance/skeleton/.github/workflows/ .github/
```

### Step 2: Update File Paths

If your project structure differs from the skeleton, update paths in `pr-security-gate.yml`:

```yaml
paths:
  # Update these paths to match your production structure
  - 'src/doxstrux/markdown/utils/url_utils.py'
  - 'src/doxstrux/markdown/collectors_phase8/**'
  # ... etc
```

### Step 3: Configure Branch Protection Rules

**GitHub UI Steps**:

1. Navigate to: **Settings > Branches > Branch protection rules**
2. Click **Add rule**
3. Configure:

   **Branch name pattern**: `main` (repeat for `develop`, `release/**`)

   **Protect matching branches**:
   - ✅ **Require status checks to pass before merging**
   - ✅ **Require branches to be up to date before merging**
   - ✅ **Status checks that are required**:
     - `URL Normalization Parity Tests`
     - `Security Audit`
   - ✅ **Do not allow bypassing the above settings**
   - ✅ **Require linear history** (optional, recommended)

4. Click **Create** or **Save changes**

**Result**: PRs cannot merge without passing all security gates.

---

### Step 4: Test the Workflow

**Create a test PR**:

```bash
# Create test branch
git checkout -b test/security-gate

# Make a benign change (trigger workflow)
echo "# Test PR" >> README.md
git add README.md
git commit -m "test: Verify security gate workflow"
git push origin test/security-gate
```

**Expected Behavior**:
1. GitHub Actions runs `pr-security-gate.yml`
2. All 14 parity tests pass
3. Security audit runs
4. ✅ Comment appears on PR: "URL Normalization Parity: PASSED"
5. PR shows green checkmark (can merge)

**Test a failure scenario** (optional):

```bash
# Introduce duplicate normalize_url (should fail)
echo "def normalize_url(url): return url" >> src/doxstrux/markdown/test_dup.py
git add src/doxstrux/markdown/test_dup.py
git commit -m "test: Introduce duplicate normalize_url (should fail)"
git push origin test/security-gate
```

**Expected Behavior**:
1. Workflow runs
2. ❌ "Verify single normalize_url definition" check fails
3. ❌ Comment appears on PR: "URL Normalization Parity: FAILED"
4. PR blocked from merging (red ❌)

---

## Workflow Details

### Job 1: `url-normalization-parity` (CRITICAL)

**Steps**:

1. **Checkout code** - Full history for diff analysis
2. **Set up Python 3.12** - with pip cache
3. **Install dependencies** - Install main + dev dependencies
4. **Run parity tests** - 14 tests, hard fail on error
5. **Upload test results** - JUnit XML + coverage HTML
6. **Check diff for dangerous URLs** - Protocol-relative, `javascript:`, etc.
7. **Verify single normalize_url** - Exactly 1 definition (DRY principle)
8. **Verify collectors import** - All collectors use `url_utils.normalize_url`
9. **Comment on PR** - Success/failure notification

**Timeout**: 10 minutes
**Failure Mode**: Hard fail (continue-on-error: false)

---

### Job 2: `security-audit` (Depends on Job 1)

**Purpose**: Run additional security tools (Bandit, Safety)

**Steps**:

1. **Run Bandit** - Python security linter (medium/high severity only)
2. **Run Safety** - Dependency vulnerability scanner
3. **Upload reports** - JSON artifacts for review

**Timeout**: 5 minutes
**Failure Mode**: Soft fail (continue-on-error: true, reports only)

---

## Maintenance

### Updating Test Count

If parity tests are added/removed, update the PR comment template in `pr-security-gate.yml`:

```yaml
- name: Comment on PR (Success)
  if: success()
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.createComment({
        body: '✅ **URL Normalization Parity: PASSED**\n\nAll 14 parity tests passed. SSRF/XSS prevention verified.'
        # Update "14" to actual test count
      })
```

### Adding New Collectors

If a new collector handles URLs, update the verification step:

```yaml
- name: Verify collectors import from url_utils
  run: |
    collectors=(
      "src/doxstrux/markdown/collectors_phase8/links.py"
      "src/doxstrux/markdown/collectors_phase8/images.py"
      "src/doxstrux/markdown/collectors_phase8/NEW_COLLECTOR.py"  # Add here
    )
    # ... verification logic
```

---

## Troubleshooting

### Issue: Workflow not triggering

**Cause**: File paths in `on.pull_request.paths` don't match changed files

**Fix**: Update `paths:` filter in `pr-security-gate.yml`

```yaml
paths:
  - 'src/doxstrux/**'  # Broader match
```

---

### Issue: Tests pass locally but fail in CI

**Cause 1**: Missing dependencies in CI

**Fix**: Verify `pyproject.toml` includes all test dependencies:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    # ... all test dependencies
]
```

**Cause 2**: Python version mismatch

**Fix**: Update workflow to match production Python version:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'  # Match your production version
```

---

### Issue: False positive in "Check for dangerous URL patterns"

**Cause**: Legitimate URL in comments/docstrings matches regex

**Fix**: Adjust regex in workflow or exclude specific files:

```yaml
- name: Check for dangerous URL patterns in diff
  run: |
    git diff origin/main...HEAD -- 'src/doxstrux/**' \
      | grep -v "tests/" \  # Exclude tests
      | grep -E '(//[a-zA-Z]|javascript:|data:)' && \
      exit 1 || true
```

---

## Security Implications

### Why This Workflow is Critical

**Attack Vector** (TOCTOU Bypass):

1. **Attacker submits markdown** with malicious URL:
   ```markdown
   [Click me](//attacker.com/steal-credentials)
   ```

2. **Collector A normalizes** URL using `normalize_url_v1()`:
   ```python
   # Collector rejects protocol-relative URLs
   result = normalize_url_v1("//attacker.com")  # Returns None
   ```

3. **Fetcher B normalizes** URL using `normalize_url_v2()`:
   ```python
   # Fetcher accepts protocol-relative URLs (INCONSISTENT!)
   result = normalize_url_v2("//attacker.com")  # Returns "https://attacker.com"
   ```

4. **Result**: SSRF vulnerability - fetcher accesses attacker-controlled URL

**Prevention**: This workflow enforces **single source of truth** for URL normalization, preventing TOCTOU bypass.

---

### Severity: P0 (CRITICAL)

- **CVSS Score**: 8.6 (High)
- **Attack Complexity**: Low (trivial to exploit)
- **Impact**: Server-Side Request Forgery (SSRF), credential theft, internal network access
- **Mitigation**: Enforce parity via CI gate (this workflow)

---

## References

- **PLAN_CLOSING_IMPLEMENTATION.md**: P0-1 specification (URL normalization parity)
- **test_url_normalization_parity.py**: 14 litmus tests (skeleton/tests/)
- **EXEC_TEMPLATE_SSTI_PREVENTION_POLICY.md**: SSTI prevention (P0-3.5)
- **EXEC_PLATFORM_SUPPORT_POLICY.md**: Platform support (P0-4)

---

## Evidence Anchors

| Claim ID | Statement | Evidence | Status |
|----------|-----------|----------|--------|
| CLAIM-CI-GATE | CI gate enforces parity | pr-security-gate.yml | ✅ Complete |
| CLAIM-BRANCH-PROTECTION | Branch protection configured | Integration guide Section 3 | ✅ Documented |
| CLAIM-ZERO-TOLERANCE | 1 failed test blocks PR | Hard fail in workflow | ✅ Enforced |

---

**Document Status**: Complete
**Last Updated**: 2025-10-17
**Version**: 1.0
**Next Review**: After first production integration
