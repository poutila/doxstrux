# Phase 8 CI/CD Integration Guide

**Version**: 1.0
**Date**: 2025-10-15
**Status**: Integration specification for Phase 8.0 deployment

---

## Overview

Phase 8 Token Warehouse integrates with the **existing CI/CD infrastructure** located at:

```
/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/ci/
```

This document describes how Phase 8 components integrate with existing CI gates and what additional validation is required.

---

## Existing CI Gates (Main Project)

**Location**: `../../tools/ci/`

### Gate G1 — No Hybrids
**File**: `ci_gate_no_hybrids.py`
**Purpose**: Ensures no legacy regex/token hybrid code paths remain

**Phase 8 Integration**:
- ✅ Token Warehouse is 100% token-based (no regex)
- ✅ All 12 collectors use pure token classification
- ✅ No `USE_TOKEN_*` or `MD_REGEX_COMPAT` flags

**Action Required**: None - warehouse already compliant

---

### Gate G2 — Canonical Pairs
**File**: `ci_gate_canonical_pairs.py`
**Purpose**: Validates test markdown files have matching `.json` specifications

**Phase 8 Integration**:
- ✅ Uses existing test corpus at `../../tools/test_mds/`
- ✅ Validates against existing baselines at `../../tools/baseline_outputs/`

**Action Required**: None - uses existing infrastructure

---

### Gate G3 — Parity
**File**: `ci_gate_parity.py`
**Purpose**: Validates parser output matches frozen baselines byte-for-byte

**Phase 8 Integration**:
```bash
# After Phase 8.0 integration, run parity gate:
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned
.venv/bin/python tools/ci/ci_gate_parity.py --profile moderate
```

**Expected Result**: All 542/542 baseline tests pass

**Critical**: Phase 8 MUST maintain byte-identical output to pass G3.

**Action Required**:
1. Run baseline parity tests after integration
2. If failures occur, investigate collector behavior
3. Never regenerate baselines without explicit approval

---

### Gate G4 — Performance
**File**: `ci_gate_performance.py`
**Purpose**: Performance regression detection (Δmedian ≤ 5%, Δp95 ≤ 10%)

**Phase 8 Expected Impact**:
- **Median parse time**: -20-30% faster (O(N) vs O(N²) text accumulation)
- **Memory usage**: -15-20% lower (circular reference cleanup)
- **p95 latency**: Stable or improved (bounded collectors)

**Action Required**:
1. Run performance gate after integration:
   ```bash
   .venv/bin/python tools/ci/ci_gate_performance.py
   ```
2. Verify performance improvements, not regressions
3. Update performance baseline if improvements are stable

---

### Gate G5 — Evidence Hash
**File**: `ci_gate_evidence_hash.py`
**Purpose**: Validates evidence blocks for non-trivial changes

**Phase 8 Integration**:
- ✅ Security patches documented in `COMPREHENSIVE_SECURITY_PATCH.md`
- ✅ Vulnerability analysis in `CRITICAL_VULNERABILITIES_ANALYSIS.md`
- ✅ Complete integration guide in `PHASE_8_SECURITY_INTEGRATION_GUIDE.md`

**Action Required**: Generate evidence blocks for Phase 8.0 PR

---

### Gate G6 — Profile & Versions
**File**: Built into `ci_gate_parity.py`
**Purpose**: Ensures baseline/profile compatibility

**Phase 8 Integration**:
- Uses `moderate` profile by default
- Validates Python version, markdown-it-py version, plugin versions

**Action Required**: None - automatically enforced

---

### Gate G7 — Security Warnings
**File**: Part of security validation
**Purpose**: No security errors; warnings allowed for `html_inline`

**Phase 8 Integration**:
- ✅ URL scheme validation via `urlparse()`
- ✅ Protocol-relative URL blocking
- ✅ Resource bounds (10K links/doc, 1M max line number)
- ✅ Timeout enforcement (5s per collector, Unix only)
- ✅ Reentrancy guard
- ✅ Memory leak prevention

**Action Required**: Run security validation after integration

---

## Additional Phase 8 Validation Gates

Beyond the existing CI gates, Phase 8 requires additional validation:

### Phase 8 Gate P1 — Adversarial Corpus
**Purpose**: Validate warehouse handles adversarial inputs safely

**Location**: `skeleton/tools/run_adversarial.py`

**Run**:
```bash
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/skeleton

# Generate corpus (20K+ adversarial tokens)
python tools/generate_adversarial_corpus.py

# Run adversarial tests (5 runs for stability)
python tools/run_adversarial.py adversarial_corpus.json --runs 5 --sample 10
```

**Success Criteria**:
- ✅ No crashes or exceptions
- ✅ Median parse time < 100ms
- ✅ Peak memory < 20MB
- ✅ Collector errors logged but not fatal

---

### Phase 8 Gate P2 — Vulnerability Tests
**Purpose**: Validate all 7 critical vulnerabilities are patched

**Location**: `skeleton/tests/test_vulnerabilities_extended.py`

**Run**:
```bash
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned

# After Phase 8 integration into main codebase:
.venv/bin/python -m pytest \
  tests/test_vulnerabilities_extended.py \
  -v -s
```

**Expected**: 10+ tests, warnings for expected failures (pre-patch), no crashes

**Critical**: After applying security patches from `COMPREHENSIVE_SECURITY_PATCH.md`, all tests should show vulnerabilities are fixed.

---

### Phase 8 Gate P3 — Fuzz Testing
**Purpose**: Randomized structural integrity testing

**Location**: `skeleton/tests/test_fuzz_collectors.py`

**Run**:
```bash
.venv/bin/python -m pytest \
  tests/test_fuzz_collectors.py \
  -v --count 100
```

**Success Criteria**:
- ✅ No crashes on random inputs
- ✅ Section invariants maintained (sorted, non-overlapping)
- ✅ Pair invariants maintained (valid open/close)

---

## Integration Workflow

### Phase 8.0 Deployment Checklist

**Pre-Integration** (on skeleton):
- [ ] Run skeleton tests: `pytest skeleton/tests/test_token_warehouse.py`
- [ ] Run adversarial corpus: `skeleton/tools/run_adversarial.py`
- [ ] Review security documentation

**Integration** (merge into main codebase):
- [ ] Copy `token_warehouse.py` to `src/doxstrux/markdown/utils/`
- [ ] Copy all 12 collectors to `src/doxstrux/markdown/collectors_phase8/`
- [ ] Apply security patches from `COMPREHENSIVE_SECURITY_PATCH.md`
- [ ] Update main parser to use TokenWarehouse

**Post-Integration Validation**:
- [ ] **G3 (Parity)**: `tools/ci/ci_gate_parity.py` → Must pass 542/542
- [ ] **G4 (Performance)**: `tools/ci/ci_gate_performance.py` → Must show -20-30% improvement
- [ ] **P1 (Adversarial)**: `tools/run_adversarial.py` → No crashes, <100ms
- [ ] **P2 (Vulnerabilities)**: `pytest tests/test_vulnerabilities_extended.py` → All patched
- [ ] **P3 (Fuzz)**: `pytest tests/test_fuzz_collectors.py` → 100+ iterations pass

**Documentation Updates**:
- [ ] Update `CHANGELOG.md` with Phase 8.0 changes
- [ ] Update `README.md` with API breaking changes (finalize format)
- [ ] Add Phase 8 to project status docs

---

## CI Pipeline Integration

### GitHub Actions / GitLab CI Example

```yaml
# .github/workflows/phase8-ci.yml
name: Phase 8 Validation

on: [pull_request, push]

jobs:
  validate-phase8:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m venv .venv
          .venv/bin/pip install -e .
          .venv/bin/pip install -e ".[dev]"

      # Existing CI gates
      - name: Gate G1 - No Hybrids
        run: .venv/bin/python tools/ci/ci_gate_no_hybrids.py

      - name: Gate G2 - Canonical Pairs
        run: .venv/bin/python tools/ci/ci_gate_canonical_pairs.py tools/test_mds

      - name: Gate G3 - Parity
        run: .venv/bin/python tools/ci/ci_gate_parity.py --profile moderate

      - name: Gate G4 - Performance
        run: .venv/bin/python tools/ci/ci_gate_performance.py

      # Phase 8 additional gates
      - name: Phase 8 Gate P1 - Adversarial Corpus
        run: |
          cd regex_refactor_docs/performance/skeleton
          python tools/generate_adversarial_corpus.py
          python tools/run_adversarial.py adversarial_corpus.json --runs 3

      - name: Phase 8 Gate P2 - Vulnerability Tests
        run: |
          .venv/bin/python -m pytest \
            tests/test_vulnerabilities_extended.py \
            -v

      - name: Phase 8 Gate P3 - Fuzz Testing
        run: |
          .venv/bin/python -m pytest \
            tests/test_fuzz_collectors.py \
            -v --count 100
```

---

## Performance Monitoring

### Key Metrics (Post-Deployment)

Track these metrics in production:

1. **Parse Time** (from G4):
   - Median: Should improve by -20-30%
   - p95: Should remain stable or improve
   - Monitor via `ci_gate_performance.py`

2. **Memory Usage**:
   - Median: Should reduce by -15-20%
   - Peak: Should be bounded (no unbounded growth)
   - Monitor via `tracemalloc` in profiling tools

3. **Collector Errors**:
   - Check `warehouse._collector_errors` after parsing
   - Should be rare (<0.01% of tokens)
   - Log and investigate any spikes

4. **Truncation Rate**:
   - Check `finalize_all()` metadata for `truncated=True`
   - If many docs hit 10K link cap, consider increasing `MAX_LINKS_PER_DOC`

---

## Rollback Plan

If Phase 8.0 integration fails:

### Immediate Rollback
```bash
# Revert to Phase 7.6
git revert <phase-8-commit-sha>
git push
```

### Identify Issues
1. Check CI gate failures (G3 parity most likely)
2. Review collector error logs
3. Run vulnerability tests to identify unfixed issues

### Fix Forward
1. Apply missing security patches
2. Fix collector behavior causing parity failures
3. Re-run full validation suite

---

## References

### Main Project CI/CD
- **Location**: `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/ci/`
- **Policy Gates**: `../../REGEX_REFACTOR_POLICY_GATES.md`
- **Execution Guide**: `../../REGEX_REFACTOR_EXECUTION_GUIDE.md`

### Phase 8 Documentation
- **This Directory**: `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/`
- **Security Patches**: `COMPREHENSIVE_SECURITY_PATCH.md`
- **Vulnerability Analysis**: `CRITICAL_VULNERABILITIES_ANALYSIS.md`
- **Integration Guide**: `PHASE_8_SECURITY_INTEGRATION_GUIDE.md`
- **Libraries**: `LIBRARIES_NEEDED.md`

### Test Infrastructure
- **Test Corpus**: `../../tools/test_mds/` (542 markdown files)
- **Baselines**: `../../tools/baseline_outputs/` (542 baseline JSON files)
- **Baseline Runner**: `../../tools/baseline_test_runner.py`

---

## Success Criteria

Phase 8.0 integration is successful when:

- ✅ All 7 existing CI gates pass (G1-G7)
- ✅ All 3 Phase 8 gates pass (P1-P3)
- ✅ Performance improved by -20-30%
- ✅ Memory usage reduced by -15-20%
- ✅ Zero parity failures (542/542 baseline tests)
- ✅ All security vulnerabilities patched
- ✅ Documentation updated

**Status**: Ready for integration after applying security patches from `COMPREHENSIVE_SECURITY_PATCH.md`

---

**Last Updated**: 2025-10-15
**Maintained By**: Doxstrux Performance & Security Team
**Integration Point**: Main project CI at `../../tools/ci/`
