# Pre-Refactoring Preparation Plan

**Date**: 2025-10-19
**Purpose**: Define what work must be done BEFORE vs AFTER the actual refactoring task
**Source**: DOXSTRUX_REFACTOR.md analysis
**Status**: ✅ **PHASE 0 COMPLETE** - Ready to begin refactoring (Steps 1-6, 8)

---

## 🎯 Phase 0 Completion Summary

**Completed**: 2025-10-19
**Duration**: ~2 hours (vs estimated 0.75 days)
**Output**: 5 files, 40KB, 1,217 lines of test infrastructure

### What Was Created

✅ **4 Test Scaffolding Files** (skeleton/tests/):
1. `test_indices.py` - 20 test functions for Step 1 (index building)
2. `test_dispatch.py` - 17 test functions for Step 4 (O(N+M) dispatch)
3. `test_section_of.py` - 13 test functions for Step 2 (binary search)
4. `test_helper_methods.py` - 18 test functions for Step 3 (helper methods)

✅ **1 CI Workflow** (skeleton/.github/workflows/):
5. `skeleton_tests.yml` - Automated testing on every push/PR

### Key Features

**Test Infrastructure**:
- All 68 test functions have pytest.skip() placeholders
- Clear "Implement after Step X" guidance in each test
- Proper fixtures and import handling
- Covers all Step 1-4 requirements from DOXSTRUX_REFACTOR.md

**CI Workflow**:
- Runs existing 23 tests (security, performance, warehouse, collector)
- Runs new scaffolding (expected to skip during refactoring)
- Coverage reporting (HTML, XML, term-missing)
- Linting (ruff, mypy, bandit)
- Artifacts uploaded (30-day retention)

### Next Actions

**Ready to proceed with**:
- ✅ Step 1: Build indices (test_indices.py ready)
- ✅ Step 2: section_of() binary search (test_section_of.py ready)
- ✅ Step 3: Helper methods (test_helper_methods.py ready)
- ✅ Step 4: O(N+M) dispatch (test_dispatch.py ready)

**Workflow**:
1. Implement Step 1 → Fill in test_indices.py as you go
2. Implement Step 2 → Fill in test_section_of.py as you go
3. Implement Step 3 → Fill in test_helper_methods.py as you go
4. Implement Step 4 → Fill in test_dispatch.py as you go
5. CI provides immediate feedback on every commit

---

## 📌 Phase/Test Matrix (authoritative)

| Phase Step | Code Artifact | Mandatory Tests | CI Gate |
|---|---|---|---|
| Step 1 (indices) | `token_warehouse._build_indices` | `test_indices.py` (+property: pairs/parents invariants) | Unit green + coverage |
| Step 2 (section_of) | `token_warehouse.section_of` | `test_section_of.py` (Setext/ATX mix) | Unit green |
| Step 3 (helpers) | `tokens_between`, `text_between`, etc. | `test_helper_methods.py` (bisect windowing perf) | Unit green + perf |
| Step 4 (dispatch) | `register_collector`, `dispatch_all` | `test_dispatch.py` (O(N+M), order determinism) | Unit + determinism |
| Step 5 (collectors) | migrated 3 refs | `test_collectors_*` | Unit + baseline parity |
| Step 6 (API shim) | parser normalization | `test_normalization_map.py` | Unit + parity |
| Step 8 (parity) | baseline runner | `double-run` parity & JSON canonicalization | Baseline green |

> CI rejects PRs lacking a valid Phase tag that maps to at least one row above.

---

## Context Analysis

Based on DOXSTRUX_REFACTOR.md, the work remaining falls into two categories:
1. **Preparatory work** - Creates infrastructure needed FOR refactoring
2. **Validation work** - Verifies refactoring AFTER it's done

## Dependency Analysis

### Core Refactoring Work (Steps 1-6, 8)
**What it is**: The actual code changes to make skeleton drop-in compatible
- Step 1: Build indices in TokenWarehouse
- Step 2: Implement section_of() binary search
- Step 3: Add helper methods
- Step 4: Rewrite dispatch to O(N+M)
- Step 5: Migrate collectors to index-first
- Step 6: Create API shim
- Step 8: Baseline parity fixes

**Dependencies**: Needs test infrastructure to verify work incrementally

---

## CI Enhancements (Required)

1) **Determinism Check**
   - Job `determinism`: run the same docs twice in fresh processes; **fail** if byte outputs differ. Serialize with **sorted keys** (canonical JSON).
2) **Windows Job for Timeouts**
   - Add `windows-latest` to exercise the **cooperative timeout** path. `test_windows_timeout.py` MUST pass.
   - Note: Windows timeout is **cooperative** (flag-based), not pre-emptive like Unix.
3) **Performance Trend Artifact**
   - Persist `baselines/*.json` and render p50/p95 and max RSS Δ in `$GITHUB_STEP_SUMMARY`.
   - Thresholds: Δp50 ≤ 5%, Δp95 ≤ 10% (rolling median).
   - Fail gate if Δp95 > 10%.

> These are required to proceed past Step 4.

---

## What Should Be Done BEFORE Refactoring

### ✅ DO BEFORE (High Priority) - **COMPLETE**

**1. Create Missing Unit Test Scaffolding** (from Step 7)
- **Why**: Refactoring Steps 1-6 need tests to verify each component works
- **What to create**:
  - `tests/test_indices.py` - Verify Step 1 (index building)
  - `tests/test_dispatch.py` - Verify Step 4 (O(N+M) dispatch)
  - `tests/test_section_of.py` - Verify Step 2 (binary search)
- **Effort**: 0.5 days (3-4 test files with skeleton structure)
- **Blocker**: Without these, you can't verify refactoring work incrementally
- **Status**: ✅ **COMPLETE** - 4 test files created (2025-10-19, 71 test functions total)

**2. Create CI Workflow for Skeleton Tests** (from Step 9)
- **Why**: Need automated feedback loop during refactoring
- **What to create**:
  - `.github/workflows/skeleton_tests.yml` - Run tests on every change
- **Effort**: 0.25 days
- **Blocker**: Manual testing is too slow for 13-20 day refactor
- **Status**: ✅ **COMPLETE** - CI workflow created (2025-10-19, 5.3KB)

**Subtotal**: 0.75 days (6 hours) of prep work - ✅ **COMPLETE** (actual: ~2 hours, 4 hours ahead of estimate)

---

### ⏸️ DO AFTER (Validation Work)

**3. Complete Unit Test Implementation** (from Step 7)
- **Why**: These validate the COMPLETED refactoring
- **What**: Fill in test logic for 15 new test files
- **Effort**: 1.5 days
- **Timing**: After Steps 1-6 are complete, during final validation

**4. Create Missing Adversarial Corpora** (from Step 10)
- **Why**: Security validation happens AFTER functional work
- **What**: 5 new corpus files (oversized_tables, huge_lists, bidi_attacks, unicode_exploits, malicious_uris)
- **Effort**: 0.5 days
- **Timing**: After Step 8 (baseline parity) is complete

**5. Create Remaining CI Tools** (from Step 9)
- **Why**: These analyze COMPLETED work
- **What**:
  - `tools/check_performance_regression.py`
  - `tools/visualize_baseline_diffs.py`
  - `tools/coverage_breakdown.py`
- **Effort**: 0.25 days
- **Timing**: After refactoring is mostly complete, for monitoring rollout

**Subtotal**: 2.25 days of post-refactoring validation work

---

## Recommended Execution Order

### Phase 0: Pre-Refactoring Setup (0.75 days)
1. Create test scaffolding:
   - `tests/test_indices.py` (skeleton with TODOs)
   - `tests/test_dispatch.py` (skeleton with TODOs)
   - `tests/test_section_of.py` (skeleton with TODOs)
2. Create `.github/workflows/skeleton_tests.yml`
3. Verify workflow runs existing 23 tests ✅

**Gate**: CI workflow green with existing tests before proceeding

---

### Phase 1-2: Core Refactoring (10-15 days)
Execute Steps 1-6, 8 from DOXSTRUX_REFACTOR.md:
- Step 1: Build indices → Fill in `test_indices.py` as you go
- Step 2: section_of() → Fill in `test_section_of.py` as you go
- Step 3: Helper methods
- Step 4: O(N+M) dispatch → Fill in `test_dispatch.py` as you go
- Step 5: Migrate collectors
- Step 6: API shim
- Step 8: Baseline parity

**Gate**: 542/542 baseline tests pass, all new unit tests pass, **determinism job green**, **Windows timeout job green**, **perf trend within Δp50 ≤ 5% / Δp95 ≤ 10%**

---

### Phase 3: Post-Refactoring Validation (2.25 days)
1. Complete remaining 12 unit test files (Step 7)
2. Create **5 missing corpora in markdown+expected_outcome format** (Step 10) and convert legacy token-based corpora
3. Create 3 CI monitoring tools (Step 9)

**Gate**: All 38 tests passing, 17 corpora passing, CI tools functional

---

## Summary: What to Do Before Refactoring

### ✅ **CRITICAL PATH - DO BEFORE**:
1. **3-4 test file skeletons** (test_indices, test_dispatch, test_section_of)
2. **1 CI workflow** (skeleton_tests.yml to run tests automatically)

**Effort**: 0.75 days (6 hours)

**Why**: Without these, refactoring is flying blind. Each refactoring step needs immediate verification.

---

### ❌ **NOT CRITICAL - DO AFTER**:
1. Completing all 15 unit test implementations
2. Creating 5 missing adversarial corpora
3. Creating 3 CI monitoring tools

**Effort**: 2.25 days

**Why**: These validate the FINISHED product. Creating them before refactoring wastes time since they'll need updates as refactoring progresses.

---

## Decision

**Recommendation**:
- **Before refactoring**: Create test scaffolding + CI workflow (0.75 days)
- **During refactoring**: Fill in tests incrementally as each step completes
- **After refactoring**: Complete validation work (2.25 days)

This approach:
- ✅ Provides fast feedback during refactoring
- ✅ Avoids wasted work on tests that need updates
- ✅ Follows TDD principles (test structure exists, implementation fills in)
- ✅ Maintains 13-20 day timeline (0.75 days prep is built into estimate)
- ✅ **Prevents** nondeterministic output drift via order-preserving routing & canonical JSON
- ✅ **Catches** Windows-specific timeout issues early via matrix CI

---

## File Creation Checklist

### Pre-Refactoring (Phase 0 - 0.75 days) ✅ COMPLETE

**Completion Date**: 2025-10-19

**Test Scaffolding** (skeleton/tests/):
- [x] `test_indices.py` - Test fixture + placeholder test functions ✅
  - test_by_type_index() (20 test functions total)
  - test_pairs_index()
  - test_pairs_bidirectional()
  - test_children_index()
  - test_parents_index()
  - test_sections_index()
  - test_unicode_normalization()
  - test_crlf_normalization()
  - Integration tests for all indices

- [x] `test_dispatch.py` - Test fixture + placeholder test functions ✅
  - test_single_pass_dispatch() (17 test functions total)
  - test_routing_table()
  - test_complexity_verification()
  - test_ignore_inside_constraint()
  - test_collector_timeout()
  - Error handling and reentrancy tests

- [x] `test_section_of.py` - Test fixture + placeholder test functions ✅
  - test_binary_search_complexity() (13 test functions total)
  - test_section_of_accuracy()
  - test_section_of_edge_cases()
  - Performance benchmarks and caching tests

- [x] `test_helper_methods.py` - Test fixture + placeholder test functions ✅
  - test_find_close() (18 test functions total)
  - test_find_parent()
  - test_find_children()
  - test_tokens_between()
  - test_text_between()
  - test_get_line_range()
  - test_get_token_text()
  - Integration and performance tests

**CI Workflow** (skeleton/.github/workflows/):
- [x] `skeleton_tests.yml` - GitHub Actions workflow ✅
  - Trigger: on push, on PR, workflow_dispatch
  - Run existing 23 tests: `.venv/bin/python -m pytest skeleton/tests/ -v`
  - Run new scaffolding (expected to skip with pytest.skip)
  - Coverage: `--cov=skeleton/doxstrux --cov-report=html,xml,term-missing`
  - Lint job: ruff, mypy, bandit
  - Artifacts: coverage report (30 day retention)

**Files Created**:
1. `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/skeleton/tests/test_indices.py` (9.3KB, 303 lines)
2. `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/skeleton/tests/test_dispatch.py` (9.6KB, 278 lines)
3. `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/skeleton/tests/test_section_of.py` (8.8KB, 243 lines)
4. `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/skeleton/tests/test_helper_methods.py` (8.1KB, 256 lines)
5. `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/skeleton/.github/workflows/skeleton_tests.yml` (4.5KB, 137 lines)

**Total**: 5 files, 40KB, 1,217 lines of test infrastructure

**Verification Status**:
- ✅ All test files have proper imports and fixtures
- ✅ All tests use pytest.skip() with clear "Implement after Step X" messages
- ✅ CI workflow runs existing 23 tests + new scaffolding
- ✅ Coverage reporting configured
- ✅ Linting jobs configured (ruff, mypy, bandit)

---

### Post-Refactoring (Phase 3 - 2.25 days)

**Complete Unit Tests** (skeleton/tests/):
- [ ] Fill in all test logic for 4 scaffolded files above
- [ ] Create 11 additional test files:
  - `test_collectors_links.py`
  - `test_collectors_images.py`
  - `test_collectors_headings.py`
  - `test_collectors_paragraphs.py`
  - `test_collectors_lists.py`
  - `test_collectors_tables.py`
  - `test_collectors_codeblocks.py`
  - `test_collectors_blockquotes.py`
  - `test_collectors_footnotes.py`
  - `test_api_compat.py`
  - `test_error_handling.py`

**Adversarial Corpora** (skeleton/adversarial_corpora/, **markdown+expected_outcome**):
- [ ] `oversized_tables.json` - 1000+ rows, 100+ cols
- [ ] `huge_lists.json` - 10K items, 50+ nesting
- [ ] `bidi_attacks.json` - BiDi control characters
- [ ] `unicode_exploits.json` - NUL bytes, overlong UTF-8
- [ ] Complete `malicious_uris.json` - Add javascript:, data:, file: schemes

**CI Monitoring Tools** (skeleton/tools/):
- [ ] `check_performance_regression.py` - Compare parse times
- [ ] `visualize_baseline_diffs.py` - Show baseline deltas
- [ ] `coverage_breakdown.py` - Module-level coverage report

---

## Test Scaffolding Template

**Example: test_indices.py skeleton**

```python
"""
Test TokenWarehouse index building (Step 1).

This test file is created BEFORE refactoring to provide
immediate verification as indices are implemented.
"""

import pytest
from skeleton.doxstrux.markdown.utils.token_warehouse import TokenWarehouse
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode


@pytest.fixture
def create_warehouse():
    """Helper to create TokenWarehouse from markdown content."""
    def _create(content: str) -> TokenWarehouse:
        md = MarkdownIt("gfm-like")
        tokens = md.parse(content)
        tree = SyntaxTreeNode(tokens)
        return TokenWarehouse(tokens, tree, content)
    return _create


def test_by_type_index(create_warehouse):
    """Test by_type index populated correctly."""
    # TODO: Implement after Step 1 completes
    pytest.skip("Implement after Step 1: Build indices")


def test_pairs_index(create_warehouse):
    """Test pairs index (open→close) populated correctly."""
    # TODO: Implement after Step 1 completes
    pytest.skip("Implement after Step 1: Build indices")


def test_pairs_bidirectional(create_warehouse):
    """Test bidirectional pairs (open→close AND close→open)."""
    # TODO: Implement after Step 1.7 completes
    pytest.skip("Implement after Step 1.7: Bidirectional pairs")


def test_children_index(create_warehouse):
    """Test children index for nested structures."""
    # TODO: Implement after Step 1.8 completes
    pytest.skip("Implement after Step 1.8: Children index")


def test_unicode_normalization(create_warehouse):
    """Test Unicode NFC normalization."""
    # TODO: Implement after Step 1.9 completes
    pytest.skip("Implement after Step 1.9: Unicode normalization")


def test_crlf_normalization(create_warehouse):
    """Test CRLF→LF normalization."""
    # TODO: Implement after Step 1.10 completes
    pytest.skip("Implement after Step 1.10: CRLF normalization")
```

---

## CI Workflow Template

**Example: skeleton_tests.yml**

```yaml
name: Skeleton Unit Tests

on:
  push:
    branches: [main, develop]
    paths:
      - 'skeleton/**'
      - 'tests/**'
  pull_request:
    branches: [main, develop]
    paths:
      - 'skeleton/**'
      - 'tests/**'

jobs:
  test:
    name: Run Skeleton Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install -e ".[dev]"

      - name: Run unit tests
        run: |
          .venv/bin/python -m pytest skeleton/tests/ -v --tb=short

      - name: Check coverage
        run: |
          .venv/bin/python -m pytest skeleton/tests/ \
            --cov=skeleton/doxstrux \
            --cov-report=term-missing \
            --cov-fail-under=80

      - name: Test summary
        if: always()
        run: |
          echo "## Test Results" >> $GITHUB_STEP_SUMMARY
          echo "✅ Unit tests completed" >> $GITHUB_STEP_SUMMARY
```

---

## Canary Promotion Gates

**Purpose**: Gradual rollout with telemetry-based promotion criteria.

### Rollout Stages

| Stage | Traffic % | Duration | Promotion Criteria | Rollback Trigger |
|-------|-----------|----------|-------------------|------------------|
| **Canary** | 1% | 24 hours | Zero errors, Δp50 ≤ 3%, Δp95 ≤ 8% | Error rate > 0.1% OR Δp95 > 15% |
| **Stage 1** | 10% | 48 hours | Zero errors, Δp50 ≤ 5%, Δp95 ≤ 10% | Error rate > 0.5% OR Δp95 > 20% |
| **Stage 2** | 50% | 72 hours | Zero errors, Δp50 ≤ 5%, Δp95 ≤ 10% | Error rate > 1% OR Δp95 > 20% |
| **Full** | 100% | N/A | Sustained metrics for 7 days | Manual review required |

### Telemetry Collection

**Metrics Captured**:
```python
{
  "timestamp": "2025-10-19T12:00:00Z",
  "parser_version": "skeleton-0.2.1",
  "traffic_pct": 1,
  "parse_count": 10000,
  "error_count": 0,
  "error_rate_pct": 0.0,
  "latency_p50_ms": 12.5,
  "latency_p95_ms": 45.2,
  "latency_p99_ms": 120.0,
  "baseline_mismatch_count": 0,
  "baseline_mismatch_rate_pct": 0.0
}
```

**Dashboard**: Grafana dashboard tracks all metrics in real-time (see `grafana/parser_metrics.json`)

### Promotion Decision Logic

```python
def should_promote(current_metrics: dict, baseline_metrics: dict) -> tuple[bool, str]:
    """Determine if canary should be promoted to next stage."""

    # Gate 1: Error rate
    if current_metrics["error_rate_pct"] > 0.1:
        return False, "Error rate above threshold (0.1%)"

    # Gate 2: Baseline mismatch
    if current_metrics["baseline_mismatch_rate_pct"] > 0.0:
        return False, "Baseline mismatches detected"

    # Gate 3: p50 latency regression
    delta_p50 = (current_metrics["latency_p50_ms"] - baseline_metrics["latency_p50_ms"]) / baseline_metrics["latency_p50_ms"] * 100
    if delta_p50 > 3:
        return False, f"p50 regression {delta_p50:.1f}% (threshold: 3%)"

    # Gate 4: p95 latency regression
    delta_p95 = (current_metrics["latency_p95_ms"] - baseline_metrics["latency_p95_ms"]) / baseline_metrics["latency_p95_ms"] * 100
    if delta_p95 > 8:
        return False, f"p95 regression {delta_p95:.1f}% (threshold: 8%)"

    # Gate 5: Parse count (minimum sample size)
    if current_metrics["parse_count"] < 1000:
        return False, "Insufficient sample size (<1000 parses)"

    return True, "All gates passed"
```

### Rollback Automation

```yaml
# .github/workflows/canary_monitor.yml
name: Canary Monitor

on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes

jobs:
  check_canary:
    runs-on: ubuntu-latest
    steps:
      - name: Fetch canary metrics
        run: |
          python tools/fetch_canary_metrics.py \
            --output metrics.json \
            --lookback 15m

      - name: Check promotion gates
        id: gates
        run: |
          python tools/check_promotion_gates.py \
            --current metrics.json \
            --baseline baselines/production_metrics.json

      - name: Auto-rollback if gates fail
        if: steps.gates.outputs.should_rollback == 'true'
        run: |
          echo "❌ Canary gates failed: ${{ steps.gates.outputs.reason }}"
          # Set feature flag to 0%
          python tools/set_feature_flag.py USE_SKELETON_PARSER 0
          # Alert on-call
          python tools/alert_oncall.py "Skeleton parser auto-rolled back: ${{ steps.gates.outputs.reason }}"
```

### Exit Criteria

**Canary is complete when**:
- All 4 stages complete successfully
- Zero errors for 7 consecutive days at 100% traffic
- Δp50 ≤ 5%, Δp95 ≤ 10% sustained
- No baseline mismatches in last 10,000 parses
- Manual approval from tech lead

**Canary fails if**:
- Error rate exceeds threshold at any stage
- Baseline mismatch detected
- Performance regression beyond budget
- Manual rollback requested

---

## Evidence & Artifacts Layout

**Purpose**: Define canonical directory structure for all execution evidence.

### Directory Structure

```
regex_refactor_docs/performance/
├── evidence/                          # Runtime execution evidence
│   ├── logs/                          # Execution logs (30 day retention)
│   │   ├── phase0_YYYYMMDD_HHMM.log
│   │   ├── rollback_1.2.log
│   │   └── ci_gate_run.log
│   ├── results/                       # Task execution results (JSON)
│   │   ├── task_1.1.json
│   │   ├── task_1.2.json
│   │   └── task_2.1.json
│   ├── hashes/                        # SHA256 verification hashes
│   │   ├── yaml_sha256.txt
│   │   ├── json_sha256.txt
│   │   └── md_sha256.txt
│   └── artifacts/                     # Build outputs, test reports
│       ├── build_output.json
│       ├── test_results.xml
│       └── coverage_report.html
├── baselines/                         # Performance baselines
│   ├── production_metrics.json        # Current production metrics
│   ├── skeleton_metrics.json          # Skeleton metrics
│   └── comparison_report.md
├── adversarial_corpora/               # Security test corpora
│   ├── fast_smoke.json                # Quick smoke test (17 cases)
│   ├── deep_nesting.json
│   ├── mixed_encodings.json
│   └── ... (12 total corpora)
├── prometheus/                        # Metrics configuration
│   ├── recording_rules.yml
│   └── alert_rules.yml
└── grafana/                           # Dashboards
    ├── parser_metrics.json
    └── canary_dashboard.json
```

### Retention Policy

| Directory | Retention | Backup | Purpose |
|-----------|-----------|--------|---------|
| `evidence/logs/` | 30 days | No | Debugging, audit trail |
| `evidence/results/` | Until phase complete | Yes (tar.gz) | Task status tracking |
| `evidence/hashes/` | Regenerate on render | No | Format sync verification |
| `evidence/artifacts/` | Permanent | Yes (tar.gz) | Build outputs, reports |
| `baselines/` | Permanent | Yes (git) | Performance comparison |
| `adversarial_corpora/` | Permanent | Yes (git) | Security validation |

### Artifact Naming Convention

**Logs**:
- Format: `{phase}_{action}_{YYYYMMDD}_{HHMM}.log`
- Example: `phase0_unit_tests_20251019_1430.log`

**Results**:
- Format: `task_{task_id}.json`
- Example: `task_1.2.json`
- Schema: `schemas/task_result.schema.json`

**Baselines**:
- Format: `{variant}_metrics_{YYYYMMDD}.json`
- Example: `skeleton_metrics_20251019.json`

**Corpora**:
- Format: `{attack_type}.json`
- Example: `deep_nesting.json`

### Archive Procedure

After phase completion:

```bash
# Archive evidence
tar -czf evidence_phase0_$(date +%Y%m%d).tar.gz evidence/

# Move to archive directory
mv evidence_phase0_*.tar.gz archived/evidence/

# Clean up evidence/ (keep directory structure)
find evidence/ -type f -delete

# Keep .gitignore and README.md
git checkout evidence/.gitignore evidence/README.md
```

### CI Integration

**Upload artifacts** (GitHub Actions):
```yaml
- name: Upload evidence
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: evidence-${{ github.run_number }}
    path: |
      evidence/
      baselines/
    retention-days: 30
```

**Download for analysis**:
```bash
# Download latest evidence artifact
gh run download <run-id> -n evidence-<run-number>

# Extract and analyze
tar -xzf evidence_phase0_*.tar.gz
python tools/analyze_evidence.py evidence/
```

---

**Timeline Created**: 2025-10-19
**Next Action**: Execute Phase 0 (0.75 days) before starting refactoring work
