# Security & Adversarial PR Checklist

**Purpose**: Required checklist for PRs that modify parser, collectors, or consumer code

**Scope**: Production deployment safety

**Source**: External deep security analysis + PLAN_CLOSING_IMPLEMENTATION

---

## Required Checks (All Must Pass)

### Adversarial Testing

- [ ] **Adversarial smoke run passed** locally or in CI (`adversarial_combined.json`)
  ```bash
  python tools/run_adversarial.py adversarial_corpora/adversarial_combined.json --runs 1
  ```

- [ ] **Full adversarial CI job** (`adversarial_full.yml`) green for this branch
  - Or: nightly run succeeded for base branch
  - Check: GitHub Actions → Adversarial Full Suite

- [ ] **Malicious-token method test** passed (ensures token canonicalization)
  ```bash
  pytest skeleton/tests/test_malicious_token_methods.py -v
  ```

### SSTI Prevention

- [ ] **SSTI litmus tests** added/updated for consumer(s)
  - File: `tests/test_consumer_ssti_litmus.py` in consumer repos
  - Tests verify metadata NOT evaluated by template engine
  - Required for: Web UI, preview service, API documentation generators

- [ ] **Template syntax detection** verified in parser
  - Collector flags `contains_template_syntax` for suspicious content
  - Test: `skeleton/tests/test_adversarial_runner.py` passes

### HTML/XSS Prevention

- [ ] **If enabling `allow_html`** or raw HTML flows:
  - Sanitizer policy documented (bleach/DOMPurify configuration)
  - Litmus tests added (`test_html_render_litmus.py`)
  - Tech Lead approval obtained
  - Waiver ticket created (ID: ______)

- [ ] **HTML sanitization tests** pass
  ```bash
  pytest skeleton/tests/test_html_render_litmus.py -v
  ```

### Collector Safety

- [ ] **If running collectors in proc-mode** (subprocess isolation):
  - Module allowlist entries added
  - Collector signatures verified
  - Allowlist policy document updated

- [ ] **Collector caps enforced**
  ```bash
  pytest skeleton/tests/test_collector_caps_end_to_end.py -v
  ```

### Monitoring & Observability

- [ ] **Metrics configured** for new collectors/features:
  - `collector_timeouts_total` (counter)
  - `collector_truncated_total` (counter)
  - `parse_p99_ms` (histogram)
  - `url_scheme_rejections_total` (counter)

- [ ] **Alerts configured** (if applicable):
  - P95 latency > baseline threshold
  - Collector timeout rate > 1%
  - Sanitization failures > 0

---

## Code Quality Checks (Per CODE_QUALITY.json)

### YAGNI Compliance

- [ ] **PR_CHECK_REQ_ID**: Current requirement ID referenced
  - Ticket: ______
  - Requirement: ______

- [ ] **PR_CHECK_IMMEDIATE_USE**: Feature used immediately
  - Consumer: ______
  - Deployment timeline: ______

- [ ] **PR_CHECK_NO_SPECULATIVE**: No speculative flags/hooks/extension points
  - If speculative code added, justify: ______

- [ ] **PR_CHECK_TESTS**: Tests prove necessity (fail-before, pass-after)
  - Test file: ______
  - Failure mode demonstrated: ______

- [ ] **PR_CHECK_KISS**: Simpler alternative considered and documented
  - Alternative: ______
  - Reason for complexity: ______

---

## Platform & Cross-Platform Safety

- [ ] **Platform support verified**:
  - [ ] Linux (SIGALRM timeout works)
  - [ ] macOS (SIGALRM timeout works)
  - [ ] Windows (graceful degradation OR subprocess isolation)

- [ ] **If Windows deployment planned**:
  - Subprocess isolation implemented
  - Collector allowlist configured
  - Windows-specific tests pass

- [ ] **If Windows NOT supported**:
  - README.md updated with Linux-only restriction
  - CI fails on Windows builds (for untrusted inputs)

---

## Security Review Sign-Off

### Reviewer Checklist

- [ ] **Security Lead**: ___________  (Date: ______)
  - Reviewed adversarial test results
  - Verified SSTI prevention in consumers
  - Approved HTML sanitization configuration (if applicable)

- [ ] **Engineering Lead**: ___________  (Date: ______)
  - Reviewed code quality compliance
  - Verified YAGNI/KISS principles followed
  - Approved performance impact

- [ ] **Tech Lead** (if waiver required): ___________  (Date: ______)
  - Waiver ticket: ______
  - Justification: ______
  - Mitigation plan: ______

---

## Evidence Anchors (Golden CoT Compliance)

- [ ] All claims have evidence sources
- [ ] All quotes have line numbers
- [ ] All decisions have impact statements
- [ ] All risks have mitigations
- [ ] All tests have failure mode descriptions

---

## Pre-Merge Commands

**Run these commands before requesting final approval:**

```bash
# 1. Run full test suite
pytest skeleton/tests/ -v

# 2. Run adversarial smoke
python tools/run_adversarial.py adversarial_corpora/adversarial_combined.json --runs 1

# 3. Run malicious token test
pytest skeleton/tests/test_malicious_token_methods.py -v

# 4. Run HTML sanitization tests
pytest skeleton/tests/test_html_render_litmus.py -v

# 5. Run collector caps tests
pytest skeleton/tests/test_collector_caps_end_to_end.py -v

# 6. Verify baseline parity (no behavioral changes)
python tools/ci/ci_gate_parity.py --profile moderate

# 7. Check coverage
pytest skeleton/tests/ --cov=skeleton/doxstrux --cov-report=term-missing
```

**All commands must succeed before merge.**

---

## Rollback Plan

**If production issues occur after merge:**

1. **Immediate rollback**: Revert PR
   ```bash
   git revert <commit-hash>
   git push origin main
   ```

2. **Disable feature**: Set environment variable
   ```bash
   export DISABLE_<FEATURE>=true
   ```

3. **Incident response**: Create incident ticket
   - Ticket: ______
   - Severity: ______
   - Mitigation: ______

---

## References

- **PLAN_CLOSING_IMPLEMENTATION.md**: Master implementation plan
- **PLAN_CLOSING_IMPLEMENTATION_extended_1.md**: P0 critical tasks
- **PLAN_CLOSING_IMPLEMENTATION_extended_2.md**: P1/P2 patterns
- **PLAN_CLOSING_IMPLEMENTATION_extended_3.md**: Testing & production
- **External deep security analysis**: Adversary-minded threat assessment
- **CODE_QUALITY.json**: YAGNI/KISS/SOLID enforcement

---

**Approval Date**: ___________
**Merge Date**: ___________
**Deployed To Production**: ___________
