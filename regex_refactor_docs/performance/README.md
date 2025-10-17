# Performance Optimization Documentation

**Created**: 2025-10-14
**Status**: Phase 8.0 - Token Warehouse Infrastructure
**Parent Project**: Doxstrux Markdown Parser (post-Phase 7.6 modularization)

---

## Overview

This directory contains documentation for **performance optimizations** applied to the Doxstrux markdown parser **after** completing the zero-regex refactoring (Phases 0-7).

**Key Distinction**:
- **Phases 0-7** (parent directory): Correctness refactoring (regex → tokens)
- **Phase 8+** (this directory): Performance optimization (efficiency improvements)

Both maintain **100% baseline parity** (542/542 tests passing with byte-identical output).

---

## Current State (Phase 7.6 Complete)

### Parser Architecture
- **Core parser**: 1,944 lines (reduced from 2,900, -33%)
- **Modular extractors**: 11 specialized modules
- **Extraction pattern**: Sequential calls to `_extract_*()` methods
- **Token traversal**: Each extractor walks `self.tree` or `self.tokens` independently

### Performance Baseline (Phase 7.6)
- **Median parse time**: ~0.88ms per document
- **Total baseline run**: 479.40ms for 542 documents
- **Performance improvement**: 14% faster than Phase 7.0 (modularization)

### Current Bottleneck
**Multiple full traversals** of the same token/tree structure:
```python
structure = {
    "sections": self._extract_sections(),      # Traversal 1
    "paragraphs": self._extract_paragraphs(),  # Traversal 2
    "lists": self._extract_lists(),            # Traversal 3
    "tables": self._extract_tables(),          # Traversal 4
    "code_blocks": self._extract_code_blocks(), # Traversal 5
    "headings": self._extract_headings(),      # Traversal 6
    "links": self._extract_links(),            # Traversal 7
    "images": self._extract_images(),          # Traversal 8
    "blockquotes": self._extract_blockquotes(), # Traversal 9
    "frontmatter": self._extract_frontmatter(), # Traversal 10
    "tasklists": self._extract_tasklists(),    # Traversal 11
    "math": self._extract_math(),              # Traversal 12
}
```

**Result**: 12 independent passes over the same data structure.

---

## Phase 8: Token Warehouse Optimization

### Objective
**Single-pass token collection with precomputed indices** to eliminate redundant traversals.

### Approach
1. **TokenWarehouse**: Build indices during one pass (by_type, pairs, parents, sections)
2. **Collector Pattern**: Convert extractors to collectors that register interest in token types
3. **Routing**: Dispatch tokens to interested collectors during single traversal
4. **Query API**: O(1) lookups for common patterns (section_of, range_for, parent)

### Expected Benefits
- **2-5x speedup** on typical documents (ChatGPT estimate based on eliminating N passes)
- **Better cache locality** (single traversal = fewer cache misses)
- **Improved scalability** (large documents benefit more from precomputed indices)
- **Cleaner separation** (warehouse = read-only data, collectors = stateless)

### Non-Goals
- ❌ Async/threading (Python GIL makes this ineffective for CPU-bound work)
- ❌ Process-level parallelism within single document (overhead dominates)
- ❌ Changing parser output (100% baseline parity required)

---

## Documentation Structure (Consolidated v4.0 - 2025-10-16)

> **📊 Consolidation Summary:**
> - **Before**: 14 active markdown files (~10,649 lines, ~35-40% overlap in security docs)
> - **After**: 12 active files (~10,200 lines, <10% overlap)
> - **Latest Consolidation**: 3 security status files → 1 EXEC_SECURITY_IMPLEMENTATION_STATUS.md
> - **Archived**: 5 files total (2 from v3 + 3 security status files)
> - **Key Improvements**:
>   - Single source of truth for security implementation status
>   - Consolidated test infrastructure documentation (62 tests, 4 CI jobs)
>   - Clear separation: vulnerabilities (COMPREHENSIVE) vs. status (IMPLEMENTATION_STATUS)
>   - Eliminated 40% overlap in security documentation

---

### **Navigation Hub**

### 1. **README.md** (This File)
Entry point and navigation hub for all performance documentation.

**Contents**: Project overview, consolidation summary, file guide, quick start paths

**When to read**: First time visiting this directory or looking for a specific topic

---

### **Architecture & Design (2 files)**

### 2. **PLAN_WAREHOUSE_OPTIMIZATION_SPEC.md** (1,232 lines)
**WHAT to build** - Complete technical specification

**Contents**:
- TokenWarehouse class design (indices, methods, lifecycle)
- Collector interface (registration, interest patterns, callbacks)
- Routing algorithm (single-pass dispatch)
- Query API reference (by_type, range_for, parent, section_of)
- Performance analysis and complexity breakdowns

**Cross-references**: → PLAN_WAREHOUSE_EXECUTION_PLAN.md (how to build), PLAN_SECURITY_COMPREHENSIVE.md (security), EXEC_PHASE_8_IMPLEMENTATION_CHECKLIST.md (status)

**When to read**: Before implementing warehouse infrastructure

---

### 3. **PLAN_WAREHOUSE_EXECUTION_PLAN.md** (978 lines)
**HOW to build it** - Phase-by-phase implementation roadmap

**Contents**:
- Phase 8.0-8.N step-by-step tasks
- Benchmarking gates and rollback procedures
- Migration order and per-collector checklists
- Evidence block templates

**Cross-references**: → PLAN_WAREHOUSE_OPTIMIZATION_SPEC.md (technical design), EXEC_CI_CD_INTEGRATION.md (CI gates)

**When to read**: During implementation

---

### **Security (3 files - Consolidated)**

### 4. **PLAN_SECURITY_COMPREHENSIVE.md** (2,098 lines) 🔐
**Master security guide** - Complete vulnerability catalog and mitigations

**Contents**:
- Part 1: Executive summary and navigation
- Part 2: Vulnerability catalog (15 vulnerabilities with severity ratings)
- Part 3: Attack scenarios (6 realistic attack scenarios)
- Part 4: Mitigations & patches (copy/paste ready code)
- Part 5: Deployment guide (testing, CI/CD, monitoring)

**Cross-references**: → EXEC_SECURITY_IMPLEMENTATION_STATUS.md (current status), PLAN_TOKEN_VIEW_CANONICALIZATION.md (specific pattern)

**When to read**: **START HERE** for vulnerability details and mitigation code

**Apply time**: 6 critical fixes in ~30 minutes, complete hardening in ~2.5 hours

---

### 5. **EXEC_SECURITY_IMPLEMENTATION_STATUS.md** (NEW - Consolidated) ✅
**Implementation status and test infrastructure** - Single source of truth for security status

**Consolidates**: SECURITY_GAP_ANALYSIS.md + SECURITY_BLOCKERS_ANALYSIS.md + SECURITY_TESTS_IMPLEMENTATION_SUMMARY.md

**Contents**:
- Security patterns implementation status (4 patterns: token canonicalization, URL normalization, template detection, HTML sanitization)
- Runtime patterns implementation status (4 patterns: O(N²) prevention, memory caps, nesting limits, timeout/reentrancy)
- Test infrastructure summary (62 test functions across 8 test files)
- CI/CD integration (4 jobs: PR fast gate, nightly suite, blocker validation, static analysis)
- Critical blockers status (3 HIGH, 2 MEDIUM priority with action items)
- Implementation requirements (next phase work)

**Cross-references**: → PLAN_SECURITY_COMPREHENSIVE.md (vulnerability details), EXEC_PHASE_8_IMPLEMENTATION_CHECKLIST.md (overall progress)

**When to read**: **For current status**, test infrastructure details, and remaining implementation work

**Test Coverage**: 62 test functions, 9 adversarial corpora, 4 CI jobs

---

### 6. **PLAN_TOKEN_VIEW_CANONICALIZATION.md** (751 lines)
**Specific security pattern guide** - Deep dive into token canonicalization

**Contents**:
- Supply-chain attack prevention
- Token view pattern implementation
- Performance benefits (~9% speedup)
- Test suite and validation

**Cross-references**: → PLAN_SECURITY_COMPREHENSIVE.md (context), EXEC_SECURITY_IMPLEMENTATION_STATUS.md (status)

**When to read**: When implementing token canonicalization specifically

---

### 7. **PLAN_ADVERSARIAL_TESTING_REFERENCE.md** (206 lines) 🧪
**Quick reference** - All 9 adversarial corpora and testing commands

**Contents**:
- Overview of 9 corpora (large, maps, URLs, nesting, regex, combined, template, XSS)
- Quick start commands
- Vulnerability coverage matrix (10/10 - 100% coverage)
- Expected baselines

**Cross-references**: → PLAN_SECURITY_COMPREHENSIVE.md (vulnerabilities), EXEC_SECURITY_IMPLEMENTATION_STATUS.md (test infrastructure)

**When to read**: For adversarial testing - quick reference with all commands

**Detailed docs**: See `archived/` for complete 3,263-line documentation

---

### **Status & Tracking (2 files)**

### 8. **EXEC_PHASE_8_IMPLEMENTATION_CHECKLIST.md** (1,121 lines) ✅
**Master status tracker** - Complete implementation progress (100% complete)

**Contents**:
- Executive summary (status, completion percentage)
- Security domain (4 items - all complete)
- Runtime domain (5 items - all complete)
- Implementation tools and code

**Cross-references**: → SECURITY_GAP_ANALYSIS.md (security details), EXEC_GREEN_LIGHT_ROLLOUT_CHECKLIST.md (production readiness)

**When to read**: For implementation status and remaining work

**Status**: All critical (P0) items complete, production-ready

---

### 9. **EXEC_GREEN_LIGHT_ROLLOUT_CHECKLIST.md** (461 lines)
**Production rollout plan** - 4-phase deployment with safety gates

**Contents**:
- Phase 1: Pre-flight checks (security, adversarial, baseline, CI/CD, docs)
- Phase 2: Canary deployment (0% → 5% → 100% over 48h)
- Phase 3: Post-rollout validation (baselines, load tests, security audit)
- Phase 4: Residual risk register
- Emergency rollback procedure

**Cross-references**: → EXEC_PHASE_8_IMPLEMENTATION_CHECKLIST.md (prerequisites), EXEC_PRODUCTION_MONITORING_GUIDE.md (metrics), EXEC_CI_CD_INTEGRATION.md (CI gates)

**When to read**: Before production deployment

---

### **Infrastructure & Operations (3 files)**

### 10. **EXEC_CI_CD_INTEGRATION.md** (380 lines) 🔗
**CI/CD integration guide** - Connects Phase 8 to main project infrastructure

**Contents**:
- Integration with existing CI gates at `../../tools/ci/`
- Gate G1-G7 (existing): No hybrids, canonical pairs, parity, performance, evidence
- Gate P1-P3 (Phase 8): Adversarial corpus, vulnerability tests, fuzz testing
- GitHub Actions workflows (implemented in `.github/workflows/adversarial.yml`)
- Performance monitoring and rollback

**Cross-references**: → EXEC_GREEN_LIGHT_ROLLOUT_CHECKLIST.md (deployment), PLAN_ADVERSARIAL_TESTING_REFERENCE.md (testing)

**When to read**: Before CI/CD integration

**Key Reference**: Main project CI/CD at `../../tools/ci/`

---

### 11. **EXEC_PRODUCTION_MONITORING_GUIDE.md** (679 lines)
**Metrics and monitoring** - Complete observability strategy

**Contents**:
- Core metrics (parse_time, collector_timeouts, collector_errors, memory, document_size, security_validations)
- Alert thresholds (P0 critical, P1 warning with Prometheus rules)
- Instrumentation code (Python metrics collection)
- Grafana dashboard templates
- Load testing configuration
- Capacity planning

**Cross-references**: → EXEC_GREEN_LIGHT_ROLLOUT_CHECKLIST.md (deployment phases)

**When to read**: Before production deployment for monitoring setup

---

### 12. **LIBRARIES_NEEDED.md** (241 lines) 📦
**Dependency documentation** - Complete dependency listing

**Summary**: **Zero new dependencies** required

**Contents**:
- Runtime dependencies (markdown-it-py - already in project)
- Testing dependencies (pytest - already in project)
- Security testing (tracemalloc, weakref, gc - stdlib only)
- Virtual environment usage (**critical**: always use `.venv/bin/python`)
- Quick check commands

**When to read**: Before installation or troubleshooting

---

### 7. **PLAN_SECURITY_COMPREHENSIVE.md** 🔐 **[CONSOLIDATED]**
**Complete unified security guide** - merges 7 previous security documents into single authoritative reference.

**Replaces**: DEEP_VULNERABILITIES_ANALYSIS.md, CRITICAL_VULNERABILITIES_ANALYSIS.md, ATTACK_SCENARIOS_AND_MITIGATIONS.md, SECURITY_HARDENING_CHECKLIST.md, SECURITY_QUICK_REFERENCE.md, COMPREHENSIVE_SECURITY_PATCH.md, PHASE_8_SECURITY_INTEGRATION_GUIDE.md

**Contents**:
- **Part 1: Executive Summary** - Quick start guide and navigation
- **Part 2: Vulnerability Catalog** - 15 vulnerabilities with severity ratings
  - Security domain (8): XSS, SSRF, supply-chain, URL normalization, SSTI, timing, HTML injection, confusables
  - Runtime domain (7): O(N²), stack overflow, bitmask fragility, heap fragmentation, TOCTOU, memory amplification, blocking I/O
- **Part 3: Attack Scenarios** - 6 realistic attack scenarios with step-by-step exploitation
- **Part 4: Mitigations & Patches** - Copy/paste ready code for all 15 vulnerabilities
- **Part 5: Deployment Guide** - Testing, CI/CD integration, monitoring, incident response

**When to read**: **START HERE** for all security concerns - single source of truth.

**Size**: ~2,500 lines (comprehensive unified reference)

**Apply time**: 6 critical fixes in ~30 minutes, complete hardening in ~2.5 hours

---

### 8. **EXEC_PHASE_8_IMPLEMENTATION_CHECKLIST.md** ✅ **[CONSOLIDATED v2.0]**
**Complete implementation tracking and status** - merges 4 previous status documents into single checklist.

**Replaces**: EXEC_PHASE_8_IMPLEMENTATION_CHECKLIST.md (v1.0), CRITICAL_REMAINING_WORK.md, DEEP_FEEDBACK_GAP_ANALYSIS.md, IMPLEMENTATION_COMPLETE.md

**Contents**:
- **Part 1: Executive Summary** - Current status (95% complete)
- **Part 2: Security Domain** - 4 critical security items (all complete ✅)
  - Static collector linting (detect blocking I/O)
  - Cross-stage URL tests (prevent TOCTOU)
  - Template syntax detection (prevent SSTI)
  - Adversarial CI gate (P1 operational)
- **Part 3: Runtime Domain** - 5 runtime items
  - Synthetic scaling tests (detect O(N²)) ✅
  - HTML/SVG XSS litmus tests (optional, 40 min)
  - Timeout wrapper (optional, 20 min)
  - Confusable detection (optional, 30 min)
  - Baseline tracking (optional, 15 min)
- **Part 4: Implementation Tools** - Complete working code and tests

**When to read**: For implementation status and remaining work tracking.

**Size**: ~1,100 lines (complete implementation guide)

**Status**: All critical (P0) items complete, only optional enhancements remain

---

### 9. **DOCUMENTATION_CONSOLIDATION_ANALYSIS.md**
Analysis of documentation overlaps and consolidation recommendations.

**Contents**:
- Complete file inventory (22 files analyzed)
- Overlap cluster identification (3 major clusters)
- Consolidation recommendations (22 → 12 files)
- Before/after comparison

**When to read**: For understanding documentation consolidation decisions.

**Result**: Successfully consolidated 11 files into 2 comprehensive documents (45% reduction in redundancy)

---

### 10. **PLAN_ADVERSARIAL_TESTING_REFERENCE.md** 🧪 **[QUICK REFERENCE]**
Quick reference for adversarial corpus testing - covers all 9 corpora and testing infrastructure.

**Contents**:
- Overview of 9 adversarial JSON corpora (large, maps, URLs, attrGet, nesting, regex, combined, template, XSS)
- Quick start commands (run single, run all, pytest)
- Vulnerability coverage matrix (10/10 vulnerabilities - 100% coverage)
- CI integration examples
- Expected performance baselines
- Defensive patches applied
- Troubleshooting guide

**When to read**: **START HERE** for adversarial testing - quick reference with all essential information.

**Coverage**: 10/10 vulnerabilities, 100% coverage achieved

**Complete Details**: See `archived/ADVERSARIAL_CORPUS_IMPLEMENTATION.md` (999 lines), `archived/ADVERSARIAL_TESTING_GUIDE.md` (1382 lines), `archived/TEMPLATE_XSS_ADVERSARIAL_COMPLETE.md` (882 lines) for comprehensive documentation

---

### 12. **.phase-8.0.template.json**
Completion artifact template for Phase 8.0.

**Purpose**: Mechanically gate Phase 8.1 until warehouse infrastructure passes all gates.

**Schema**: Extends parent directory's phase completion schema with performance deltas.

---

### 9. **skeleton/** (Canonical Reference Implementation)
Production-ready skeleton with **all optimizations**, **complete collector set**, **security hardening**, and **debug utilities**.

**Contents**:
- `doxstrux/markdown/utils/token_warehouse.py` (307 lines) - Optimized warehouse + security + debug
- `doxstrux/markdown/security/validators.py` (179 lines) - URL normalization utility 🔐 **NEW**
- `doxstrux/markdown/collectors_phase8/*.py` (12 collectors, 436 lines) - All collectors ready
- `doxstrux/markdown/core/parser_adapter.py` (29 lines) - Feature flag integration
- `doxstrux/markdown/cli/dump_sections.py` (102 lines) - Section debug CLI tool
- `tests/test_token_warehouse.py` (206 lines) - 6 comprehensive tests
- `tools/benchmark_parser.py` (44 lines) - Performance measurement scaffold
- `README.md` (~530 lines) - Complete integration guide

**Key Features**:
- ✅ All precomputed indices (by_type, pairs, parents, sections, fences)
- ✅ Single-pass routing with dispatch_all()
- ✅ O(1) query API (O(log n) for section_of via binary search)
- ✅ All 12 collectors implemented (ready for Phase 8.1-8.N)
- ✅ Debug utilities (debug_dump_sections() + CLI tool)
- ✅ 6 comprehensive tests (merged from both versions)

**Performance Optimizations** (applied 2025-10-14):
- ✅ **O(H) section builder** - Stack-based closing (was O(H²), ~10-100x faster on many headings)
- ✅ **Correct parent assignment** - All tokens get parents, not just inline (correctness fix)
- ✅ **O(1) ignore-mask** - Bitmask checks instead of linear stack scans (~5-20% faster dispatch)
- ✅ **Hot-loop micro-opts** - Prebound locals in dispatch_all() (~2-5% faster)
- ✅ **Nullable should_process** - Skip redundant calls (~2% faster)
- ✅ **Expected total speedup**: 15-30% on typical documents, 50-100x on heading-heavy documents

**Security Hardening** (applied 2025-10-15) 🔐 **NEW**:
- ✅ **Token view canonicalization** - Prevents supply-chain attacks via malicious getters (~9% faster + safer)
- ✅ **URL normalization utility** - Centralized scheme validation prevents SSRF/XSS bypasses
- ✅ **MAX_TOKENS/MAX_BYTES guards** - Prevents memory amplification DoS (100K tokens / 10MB limit)
- ✅ **MAX_NESTING enforcement** - Prevents stack overflow (150 depth limit)
- ✅ **Deterministic routing** - sorted() ensures consistent bit assignment across processes
- ✅ **Map normalization** - Clamps negative/inverted map values (already present)
- ✅ **Error isolation** - Collector exceptions don't crash dispatch (already present)
- ✅ **Comprehensive unit tests** - URL validation test suite included

**When to use**: Copy files to main codebase for Phase 8.0+ implementation.

**Total**: 24 files, 1,305 lines of production-ready code

---

## Phase Completion Tracking

### Phase 8.0: TokenWarehouse Infrastructure
**Status**: 📋 Specification ready, implementation pending

**Completion Criteria**:
- ✅ TokenWarehouse class implemented with all indices
- ✅ Routing algorithm passes unit tests
- ✅ Query API verified against manual traversal
- ✅ No behavioral changes (542/542 baseline parity)
- ✅ Performance neutral or positive (Δmedian ≤ 5%)

**Artifact**: `.phase-8.0.complete.json` (created when gates pass)

---

### Phase 8.1-8.N: Collector Migration
**Status**: ⏳ Blocked until Phase 8.0 complete

**Incremental Migration Order** (TBD based on complexity):
1. Links/Images (token-based, good starting point)
2. Headings/Sections (tree-based, requires parent tracking)
3. Code blocks/Tables (block-based, benefits from pairs index)
4. Lists/Tasklists (nested structures, most complex)

**Per-Phase Completion Criteria**:
- ✅ Extractor converted to collector
- ✅ Original extractor removed (no hybrids)
- ✅ 100% baseline parity maintained
- ✅ Performance improvement measured (negative Δ = faster)

---

## Testing Strategy

### Baseline Parity (Non-Negotiable)
**Command**:
```bash
.venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs
```

**Gate**: 542/542 tests passing with byte-identical JSON output.

---

### Performance Benchmarking

**Command** (from parent directory):
```bash
.venv/bin/python tools/benchmark_parser.py \
  --corpus tools/test_mds \
  --runs-cold 3 \
  --runs-warm 5 \
  --baseline-file performance/baseline_phase_7.6.json \
  --emit-report performance/phase_8.X.json
```

**Gates**:
- **Median Δ**: Must be ≤ -10% (faster) or explain regression
- **P95 Δ**: Must be ≤ -5% (faster) or explain regression
- **Memory**: No significant increase (tracemalloc check)

**Note**: Negative deltas = improvement (faster is better).

---

### Unit Tests (Warehouse-Specific)

**New test file**: `tests/test_token_warehouse.py`

**Coverage**:
- Index building (by_type, pairs, parents, sections)
- Query API (iter_by_type, range_for, parent, section_of)
- Edge cases (empty tokens, nested structures, missing data)
- Collector registration and dispatch

**Target**: ≥80% coverage (project standard).

---

## Performance Measurement Methodology

### Cold vs. Warm Runs
- **Cold runs**: Parser instantiation + parse (measures total overhead)
- **Warm runs**: Parse only (measures extraction efficiency)

**Why both**: Warehouse adds initialization cost but reduces extraction cost.

---

### Metrics to Track
1. **Median parse time** (primary metric - robust to outliers)
2. **P95 parse time** (catches worst-case regressions)
3. **Memory usage** (tracemalloc peak MB)
4. **Initialization time** (warehouse building overhead)

---

### Regression Definition
**Performance regression** = Any phase where:
- Median Δ > +5% (slower) **OR**
- P95 Δ > +10% (slower) **OR**
- Memory increase > +20%

**Response**: Rollback phase, profile hotspots, fix, re-measure.

---

## Rollback Procedure

If any phase fails gates:

1. **Revert Git**:
   ```bash
   git reset --hard phase-8.{X-1}-complete
   ```

2. **Delete Phase Artifact**:
   ```bash
   rm .phase-8.X.complete.json
   ```

3. **Verify Baseline**:
   ```bash
   .venv/bin/python tools/baseline_test_runner.py --test-dir tools/test_mds --baseline-dir tools/baseline_outputs
   ```
   Expected: 542/542 passing

4. **Analyze Failure**:
   - Profile with `cProfile` or `py-spy`
   - Check index sizes (memory overhead)
   - Review routing logic (dispatch efficiency)

5. **Fix and Retry**:
   - Apply fix
   - Re-run benchmarks
   - Re-attempt phase

---

## Integration with Existing Infrastructure

### Compatibility with Phase 7.6
- ✅ Extractor modules remain (no breaking changes initially)
- ✅ Warehouse is **opt-in** during migration (feature flag for A/B testing)
- ✅ Baseline outputs unchanged (byte-identical)
- ✅ Cache system (`self._cache`) remains functional

### Migration Path
**Hybrid mode** (during migration):
```python
# Feature flag for gradual rollout
USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "0") == "1"

if USE_WAREHOUSE:
    # Build warehouse once
    self._warehouse = TokenWarehouse(self.tokens, self.tree)

    # Use collectors where migrated
    structure = {
        "links": self._warehouse.collect_links(),  # Migrated
        "images": self._warehouse.collect_images(), # Migrated
        "sections": self._extract_sections(),       # Not migrated yet
        # ...
    }
else:
    # Original path (Phase 7.6)
    structure = {
        "sections": self._extract_sections(),
        "paragraphs": self._extract_paragraphs(),
        # ...
    }
```

**Final state** (all collectors migrated):
```python
# Build warehouse once
self._warehouse = TokenWarehouse(self.tokens, self.tree)

# Single dispatch pass
structure = self._warehouse.collect_all()
```

---

## Directory Structure

```
performance/
├── README.md                                (700 lines) - This file [UPDATED v2]
├── PLAN_WAREHOUSE_OPTIMIZATION_SPEC.md          (1,232 lines) - Technical spec
├── PLAN_WAREHOUSE_EXECUTION_PLAN.md             (978 lines) - Implementation guide
├── SECURITY_AND_PERFORMANCE_REVIEW.md      (1,238 lines) - Deep security review
├── PLAN_SECURITY_COMPREHENSIVE.md               (2,098 lines) - 🔐 **[CONSOLIDATED]** Unified security guide
├── SECURITY_GAP_ANALYSIS.md                (725 lines) - Implementation status (NEW)
├── PLAN_TOKEN_VIEW_CANONICALIZATION.md          (751 lines) - Security pattern guide
├── EXEC_PHASE_8_IMPLEMENTATION_CHECKLIST.md     (1,113 lines) - ✅ **[CONSOLIDATED v2.0]** Complete status
├── PLAN_ADVERSARIAL_TESTING_REFERENCE.md        (~200 lines) - 🧪 **[QUICK REF]** Adversarial testing
├── EXEC_CI_CD_INTEGRATION.md                    (380 lines) - CI/CD integration 🔗
├── LIBRARIES_NEEDED.md                     (241 lines) - Dependencies 📦
├── .phase-8.0.template.json                (101 lines) - Completion template
├── adversarial_corpora/                   - 🧪 Adversarial test corpus (9 JSON files)
│   ├── manifest.json                      - Corpus catalog
│   ├── adversarial_large.json             - Large token corpus (5k tokens)
│   ├── adversarial_malformed_maps.json    - Malformed map entries
│   ├── adversarial_encoded_urls.json      - Encoded/tricky URLs
│   ├── adversarial_attrget.json           - Token with attrGet sentinel
│   ├── adversarial_deep_nesting.json      - Deep nesting (2000 levels)
│   ├── adversarial_regex_pathological.json - Pathological inline content
│   ├── adversarial_combined.json          - Combined multi-vector corpus
│   ├── adversarial_template_injection.json - Template injection vectors
│   └── adversarial_html_xss.json          - HTML/XSS attack vectors
├── warehouse_phase8_patched/             - Security-hardened warehouse 🔒
│   ├── doxstrux/markdown/
│   │   ├── utils/token_warehouse.py   (290 lines) - Patched + hardened
│   │   └── collectors_phase8/links.py (78 lines) - Patched + safe URL validation
│   ├── tests/
│   │   ├── test_token_warehouse_adversarial.py (38 lines)
│   │   └── test_vulnerabilities_extended.py (380 lines) - 10+ vulnerability tests
│   └── tools/
│       ├── generate_adversarial_corpus.py (37 lines)
│       └── run_adversarial.py (90 lines) - Adversarial runner
├── skeleton/                              - Canonical reference implementation ⭐
│   ├── doxstrux/markdown/
│   │   ├── utils/token_warehouse.py   (307 lines) - Optimized warehouse + security + debug
│   │   ├── security/
│   │   │   ├── __init__.py            (5 lines) - Security module init 🔐
│   │   │   └── validators.py          (179 lines) - URL normalization utility 🔐
│   │   ├── collectors_phase8/         (12 collectors, 436 lines) - All collectors
│   │   ├── core/parser_adapter.py     (29 lines) - Feature flag
│   │   └── cli/dump_sections.py       (102 lines) - Debug CLI tool
│   ├── tests/
│   │   ├── test_token_warehouse.py    (206 lines) - 6 comprehensive tests
│   │   └── test_fuzz_collectors.py    (318 lines) - Fuzz tests ⚡
│   ├── tools/
│   │   ├── benchmark_parser.py        (44 lines) - Benchmark scaffold
│   │   └── profile_collectors.py      (260 lines) - Profiling tool ⚡
│   └── README.md                      (~640 lines) - Complete guide
├── steps_taken/                           - Phase completion documentation
└── archived/                              - 📦 Archived documentation (16 files)
    ├── ATTACK_SCENARIOS_AND_MITIGATIONS.md
    ├── COMPREHENSIVE_SECURITY_PATCH.md
    ├── CRITICAL_VULNERABILITIES_ANALYSIS.md
    ├── DEEP_FEEDBACK_GAP_ANALYSIS.md
    ├── DEEP_VULNERABILITIES_ANALYSIS.md
    ├── IMPLEMENTATION_COMPLETE.md
    ├── PHASE_8_SECURITY_INTEGRATION_GUIDE.md
    ├── SECURITY_HARDENING_CHECKLIST.md
    ├── SECURITY_QUICK_REFERENCE.md
    ├── CRITICAL_REMAINING_WORK.md (v2 consolidation)
    ├── SECURITY_DOCUMENTATION_SUMMARY.md (v2 consolidation)
    ├── DOCUMENTATION_AUDIT.md (v2 consolidation)
    ├── DOCUMENTATION_CONSOLIDATION_ANALYSIS.md (v2 consolidation)
    ├── ADVERSARIAL_CORPUS_IMPLEMENTATION.md (v2 consolidation)
    ├── ADVERSARIAL_TESTING_GUIDE.md (v2 consolidation)
    └── TEMPLATE_XSS_ADVERSARIAL_COMPLETE.md (v2 consolidation)
```

**Documentation Consolidation** (2025-10-15 - v2.0):
- **Before**: 22 files, ~16,000 lines (significant overlap)
- **After**: 11 active files, 2 major consolidated documents, 16 archived files
- **Reduction**: ~50% reduction in redundancy
- **Key Consolidations**:
  - 7 security docs → PLAN_SECURITY_COMPREHENSIVE.md (~2,500 lines)
  - 4 status docs → EXEC_PHASE_8_IMPLEMENTATION_CHECKLIST.md v2.0 (~1,100 lines)
  - 3 adversarial docs → PLAN_ADVERSARIAL_TESTING_REFERENCE.md (~200 lines quick ref)

**Total**: ~10,000 lines of active specification + 2,457 lines of skeleton code + 9 adversarial corpus files

**Performance**: Skeleton includes O(H) section builder, O(1) ignore-mask, hot-loop optimizations, token view canonicalization (+9% speedup), debug utilities, and comprehensive test/profiling suite.

**Security**: Complete multi-layered security documentation + production-ready security implementations:
- ✅ Token view canonicalization implementation (supply-chain attack prevention + 9% speedup)
- ✅ URL normalization utility with comprehensive test suite (SSRF/XSS prevention)
- 6 immediate attack scenarios (XSS, SSRF, DoS) with copy/paste fixes
- 9 deep vulnerabilities (supply-chain, normalization, SSTI, O(N²), etc.)
- Quick reference guide (6 critical fixes, ~30 min apply time)
- 3 security domains covered (injection, resource exhaustion, correctness)

**Integration**: CI/CD integration guide references main project infrastructure at `../../tools/ci/` (5 CI gates + 3 Phase 8 gates)

---

## Quick Start

### For Implementation
1. **Read `EXEC_PHASE_8_IMPLEMENTATION_CHECKLIST.md` (actionable checklist)** ✅ **START HERE**
   - Consolidated v2.0 - includes all status, remaining work, and implementation tools
2. **Read `PLAN_SECURITY_COMPREHENSIVE.md` (complete security guide)** 🔐 **CRITICAL**
   - Consolidated - all 15 vulnerabilities, mitigations, and deployment in one place
3. Read `PLAN_WAREHOUSE_OPTIMIZATION_SPEC.md` (architecture)
4. Read `PLAN_WAREHOUSE_EXECUTION_PLAN.md` (roadmap)
5. **Read `EXEC_CI_CD_INTEGRATION.md` (understand CI gate requirements)** 🔗
6. Check `LIBRARIES_NEEDED.md` (verify dependencies - zero new deps!)
7. Review `skeleton/` (reference implementation with all security hardening)
8. Create feature branch: `git checkout -b feature/token-warehouse`
9. Copy skeleton files to main codebase:
    ```bash
    cp skeleton/doxstrux/markdown/utils/token_warehouse.py \
       src/doxstrux/markdown/utils/
    cp skeleton/doxstrux/markdown/security/validators.py \
       src/doxstrux/markdown/security/
    cp skeleton/doxstrux/markdown/collectors_phase8/links.py \
       src/doxstrux/markdown/collectors_phase8/
    cp skeleton/tests/test_token_warehouse.py \
       tests/
    ```
10. Apply security patches from `PLAN_SECURITY_COMPREHENSIVE.md` Part 4 (copy/paste ready)
11. Run CI gates (G1-G7 + P1-P3) per `EXEC_CI_CD_INTEGRATION.md`
12. Create `.phase-8.0.complete.json`
13. Migrate collectors incrementally (Phases 8.1-8.N)

### For Review
1. Read this README (context)
2. Review `PLAN_WAREHOUSE_OPTIMIZATION_SPEC.md` (design)
3. Check benchmarking methodology
4. Verify baseline parity requirements

---

## References

### Parent Documentation
- `../REGEX_REFACTOR_EXECUTION_GUIDE.md` - Original refactoring approach
- `../REGEX_REFACTOR_POLICY_GATES.md` - CI/CD gates and policy (G1-G7)
- `../DETAILED_TASK_LIST.md` - Phase 0-7 task breakdowns
- `../.phase-7.6.complete.json` - Current completion state

### Main Project CI/CD
- `../../tools/ci/ci_gate_parity.py` - Baseline parity validation (G3)
- `../../tools/ci/ci_gate_performance.py` - Performance regression detection (G4)
- `../../tools/ci/ci_gate_no_hybrids.py` - No hybrid code paths (G1)
- `../../tools/ci/ci_gate_canonical_pairs.py` - Test corpus validation (G2)
- `../../tools/ci/ci_gate_evidence_hash.py` - Evidence block validation (G5)

### Related Code
- `src/doxstrux/markdown_parser_core.py:378` - Current `parse()` method
- `src/doxstrux/markdown/extractors/` - Current extractor modules
- `src/doxstrux/markdown/utils/token_utils.py` - Token traversal utilities

### External Design Input
- ChatGPT conversation (2025-10-14) - Token Warehouse architecture proposal

---

## Version History

- **2025-10-14**: Initial documentation framework created
- **Phase 8.0**: Pending (infrastructure)
- **Phase 8.1-8.N**: Pending (collector migration)

---

## Status Summary

**Current Phase**: 8.0 (Specification complete, implementation pending)

**Next Steps**:
1. Review PLAN_WAREHOUSE_OPTIMIZATION_SPEC.md
2. Review PLAN_WAREHOUSE_EXECUTION_PLAN.md
3. Implement TokenWarehouse class
4. Run Phase 8.0 gates
5. Create `.phase-8.0.complete.json`

**Estimated Timeline**: 2-3 days for Phase 8.0, 5-7 days for full migration

---

**Last Updated**: 2025-10-14
**Maintained By**: Doxstrux development team
**Status**: 📋 Ready for implementation
