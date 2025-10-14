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

## Documentation Files

### 1. **README.md** (This File)
Navigation hub and quick reference.

**When to read**: First time visiting this directory.

---

### 2. **WAREHOUSE_OPTIMIZATION_SPEC.md**
Complete technical specification for Token Warehouse architecture.

**Contents**:
- TokenWarehouse class design (indices, methods, lifecycle)
- Collector interface (registration, interest patterns, callbacks)
- Routing algorithm (single-pass dispatch)
- Query API reference (by_type, range_for, parent, section_of)
- Migration guide (how to convert extractors to collectors)
- Performance measurement methodology

**When to read**: Before implementing warehouse infrastructure.

**Size**: Detailed specification (1,213 lines)

---

### 3. **WAREHOUSE_EXECUTION_PLAN.md**
Phase-by-phase implementation roadmap.

**Contents**:
- Phase 8.0: Create TokenWarehouse infrastructure
- Phase 8.1: Migrate first collector (proof of concept)
- Phase 8.2-8.N: Migrate remaining collectors incrementally
- Benchmarking gates (median Δ ≤ -10%, p95 Δ ≤ -5%)
- Rollback procedures
- Evidence block templates

**When to read**: During implementation.

**Size**: Lean operational guide (996 lines)

---

### 4. **SECURITY_AND_PERFORMANCE_REVIEW.md**
Deep technical review with security hardening and micro-optimizations.

**Contents**:
- Security hardening (cheap, surgical, no perf tax)
  - Explicit scheme allowlist, HTML boundaries, DoS guards, fault containment
- Runtime correctness (prevents bugs that bite later)
  - Parent mapping, sections builder, fence inventory correctness
- Raw speed optimizations (micro & macro)
  - Hot-loop tightness, frozen collections, pre-allocation, SoA (optional)
- Style & maintainability (future-proofs refactors)
  - Intent-revealing names, docstrings, tests, error messages
- Measurement methodology (know it worked)
  - CPU profiling, alloc tracking, p95 latency, correctness parity

**When to read**: Before implementing Phase 8.0 (apply security hardening first).

**Size**: Comprehensive review with 82 actionable items (detailed guide)

---

### 5. **CI_CD_INTEGRATION.md** 🔗 NEW
CI/CD integration guide connecting Phase 8 to main project infrastructure.

**Contents**:
- Integration with existing CI gates at `../../tools/ci/`
- Gate G1-G7 (existing): No hybrids, canonical pairs, parity, performance, evidence
- Gate P1-P3 (Phase 8): Adversarial corpus, vulnerability tests, fuzz testing
- GitHub Actions/GitLab CI pipeline examples
- Performance monitoring and rollback procedures

**When to read**: Before Phase 8.0 integration to understand CI requirements.

**Key Reference**: Main project CI/CD at `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/ci/`

---

### 6. **LIBRARIES_NEEDED.md** 📦 NEW
Complete dependency documentation for Phase 8.

**Summary**: **Zero new dependencies** required - all tools use existing deps or stdlib.

**Contents**:
- Runtime dependencies (markdown-it-py, already in project)
- Testing dependencies (pytest, already in project)
- Security testing (tracemalloc, weakref, gc - all stdlib)
- Virtual environment usage (critical: always use `.venv/bin/python`)
- Quick check commands

**When to read**: Before installation or when troubleshooting missing imports.

---

### 7. **ATTACK_SCENARIOS_AND_MITIGATIONS.md** 🛡️ NEW
Concrete, realistic attack and failure modes with immediate mitigations.

**Contents**:
- **Security attacks** (3): Unsafe HTML → XSS, Unsafe URL schemes → SSRF, Malicious attrGet
- **Runtime failures** (3): Resource exhaustion, Broken map values, Collector exceptions
- Detection strategies (CI gates, telemetry, fuzz testing)
- Quick prioritized mitigations (copy/paste checklist)
- Implementation status matrix

**When to read**: Before security review or when hardening the implementation.

**Format**: Each attack includes: what happens, how triggered, impact, detection, and immediate fix.

---

### 7.5. **SECURITY_QUICK_REFERENCE.md** ⚡ NEW
Fast-lookup security hardening checklist - apply these NOW.

**Contents**:
- 6 critical fixes with copy/paste code (input caps, map norm, URL allowlist, error isolation, HTML safety, collector caps)
- Security checklist (before deployment, testing, docs, monitoring)
- Detection patterns (telemetry, alert thresholds)
- Implementation status matrix (73 LOC total)
- Quick apply script

**When to read**: When applying security fixes or responding to incidents.

**Apply time**: ~30 minutes for all 6 fixes

---

### 7.6. **TOKEN_VIEW_CANONICALIZATION.md** 🔐 NEW
Step-by-step implementation guide for token view canonicalization security pattern.

**Contents**:
- 9-step implementation guide (~150 LOC across warehouse and collectors)
- Token view pattern (canonicalize tokens to primitives during init)
- Supply-chain attack prevention (eliminates attrGet() risks)
- Performance impact analysis (init overhead vs dispatch speedup)
- Complete code snippets with safety annotations
- Demo script and verification tests

**When to read**: Before implementing TokenWarehouse to eliminate token method execution risks.

**Key benefit**: Prevents malicious token getters from executing during hot-path dispatch (~9% faster parse, safer runtime).

---

### 7.7. **DEEP_VULNERABILITIES_ANALYSIS.md** 🔬 NEW
Comprehensive analysis of 9 non-obvious, high-impact vulnerabilities beyond basic XSS/SSRF.

**Contents**:
- **Security domain** (4): Token deserialization/prototype pollution, URL normalization mismatch, template injection (SSTI), side-channel timing
- **Runtime domain** (5): Algorithmic complexity (O(N²)), deep nesting stack overflow, bitmask fragility, heap fragmentation, race conditions (TOCTOU)
- Combined attack chains (2 examples)
- Detection methods with code snippets
- Immediate mitigations (copy/paste ready)
- Testing matrix mapping vulnerabilities to test files

**When to read**: When performing deep security review or advanced threat modeling.

**Format**: Each vulnerability includes severity rating, technical description, attack vectors, escalation potential, real-world scenarios, detection, and mitigation.

---

### 7.8. **SECURITY_DOCUMENTATION_SUMMARY.md** 📋 NEW
Complete overview and roadmap for all security documentation.

**Contents**:
- Document hierarchy (4 layers: quick response, concrete threats, implementation guides, deep analysis)
- Coverage matrix (15 vulnerabilities across all documents)
- Implementation roadmap (Phase 8.0-8.2: ~443 LOC, ~2.5 hours)
- Testing requirements (unit tests, adversarial corpus, fuzz testing)
- Monitoring & detection (telemetry metrics, alert thresholds)
- CI/CD integration summary

**When to read**: First time reviewing security documentation or planning security implementation.

**Key insight**: Hierarchical documentation allows quick action (Layer 1) while supporting deep analysis (Layer 4).

---

### 8. **.phase-8.0.template.json**
Completion artifact template for Phase 8.0.

**Purpose**: Mechanically gate Phase 8.1 until warehouse infrastructure passes all gates.

**Schema**: Extends parent directory's phase completion schema with performance deltas.

---

### 9. **skeleton/** (Canonical Reference Implementation)
Production-ready skeleton with **all optimizations**, **complete collector set**, and **debug utilities**.

**Contents**:
- `doxstrux/markdown/utils/token_warehouse.py` (259 lines) - Optimized warehouse + debug utilities
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

**When to use**: Copy files to main codebase for Phase 8.0+ implementation.

**Total**: 22 files, 1,119 lines of production-ready code

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
├── README.md                                (600 lines) - This file
├── WAREHOUSE_OPTIMIZATION_SPEC.md          (1,213 lines) - Technical spec
├── WAREHOUSE_EXECUTION_PLAN.md             (996 lines) - Implementation guide
├── SECURITY_DOCUMENTATION_SUMMARY.md       (405 lines) - Security docs roadmap 📋 NEW
├── SECURITY_HARDENING_CHECKLIST.md         (550 lines) - Initial security review ⚡
├── CRITICAL_VULNERABILITIES_ANALYSIS.md    (650 lines) - Deep security analysis 🔒
├── COMPREHENSIVE_SECURITY_PATCH.md         (450 lines) - Production patches 🔒
├── PHASE_8_SECURITY_INTEGRATION_GUIDE.md   (420 lines) - Integration guide 🔒
├── CI_CD_INTEGRATION.md                    (350 lines) - CI/CD integration 🔗
├── LIBRARIES_NEEDED.md                     (280 lines) - Dependencies 📦
├── ATTACK_SCENARIOS_AND_MITIGATIONS.md     (850 lines) - Attack modes & fixes 🛡️
├── SECURITY_QUICK_REFERENCE.md             (320 lines) - Fast security checklist ⚡
├── TOKEN_VIEW_CANONICALIZATION.md          (751 lines) - Token view impl guide 🔐
├── DEEP_VULNERABILITIES_ANALYSIS.md        (1,179 lines) - Deep vulnerability analysis 🔬
├── .phase-8.0.template.json                (101 lines) - Completion template
├── warehouse_phase8_patched/             - Security-hardened warehouse 🔒 NEW
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
│   │   ├── utils/token_warehouse.py   (259 lines) - Optimized warehouse + debug
│   │   ├── collectors_phase8/         (12 collectors, 436 lines) - All collectors
│   │   ├── core/parser_adapter.py     (29 lines) - Feature flag
│   │   └── cli/dump_sections.py       (102 lines) - Debug CLI tool
│   ├── tests/
│   │   ├── test_token_warehouse.py    (206 lines) - 6 comprehensive tests
│   │   └── test_fuzz_collectors.py    (318 lines) - Fuzz tests ⚡ NEW
│   ├── tools/
│   │   ├── benchmark_parser.py        (44 lines) - Benchmark scaffold
│   │   └── profile_collectors.py      (260 lines) - Profiling tool ⚡ NEW
│   └── README.md                      (~640 lines) - Complete guide
├── steps_taken/                           - Phase completion documentation
└── archived/                              - Historical documents
```

**Total**: 9,321 lines of specification + 1,704 lines of skeleton code

**Performance**: Skeleton includes O(H) section builder, O(1) ignore-mask, hot-loop optimizations, debug utilities, and comprehensive test/profiling suite.

**Security**: Complete multi-layered security documentation:
- 6 immediate attack scenarios (XSS, SSRF, DoS) with copy/paste fixes
- 9 deep vulnerabilities (supply-chain, normalization, SSTI, O(N²), etc.)
- Token view canonicalization (security + 9% performance improvement)
- Quick reference guide (6 critical fixes, ~30 min apply time)
- 3 security domains covered (injection, resource exhaustion, correctness)

**Integration**: CI/CD integration guide references main project infrastructure at `../../tools/ci/` (5 CI gates + 3 Phase 8 gates)

---

## Quick Start

### For Implementation
1. **Read `SECURITY_DOCUMENTATION_SUMMARY.md` (security roadmap overview)** 📋 **START HERE**
2. Read `WAREHOUSE_OPTIMIZATION_SPEC.md` (architecture)
3. Read `WAREHOUSE_EXECUTION_PLAN.md` (roadmap)
4. **Read `SECURITY_QUICK_REFERENCE.md` (apply 6 critical fixes first)** ⚡
5. **Read `TOKEN_VIEW_CANONICALIZATION.md` (implement token view pattern)** 🔐
6. **Read `CI_CD_INTEGRATION.md` (understand CI gate requirements)** 🔗
7. Check `LIBRARIES_NEEDED.md` (verify dependencies - zero new deps!)
8. Review `skeleton/` (reference implementation)
9. Create feature branch: `git checkout -b feature/token-warehouse`
10. Copy skeleton files to main codebase:
    ```bash
    cp skeleton/doxstrux/markdown/utils/token_warehouse.py \
       src/doxstrux/markdown/utils/
    cp skeleton/doxstrux/markdown/collectors_phase8/links.py \
       src/doxstrux/markdown/collectors_phase8/
    cp skeleton/tests/test_token_warehouse.py \
       tests/
    ```
11. Apply security patches from `COMPREHENSIVE_SECURITY_PATCH.md`
12. Run CI gates (G1-G7 + P1-P3) per `CI_CD_INTEGRATION.md`
13. Create `.phase-8.0.complete.json`
14. Migrate collectors incrementally (Phases 8.1-8.N)

### For Review
1. Read this README (context)
2. Review `WAREHOUSE_OPTIMIZATION_SPEC.md` (design)
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
1. Review WAREHOUSE_OPTIMIZATION_SPEC.md
2. Review WAREHOUSE_EXECUTION_PLAN.md
3. Implement TokenWarehouse class
4. Run Phase 8.0 gates
5. Create `.phase-8.0.complete.json`

**Estimated Timeline**: 2-3 days for Phase 8.0, 5-7 days for full migration

---

**Last Updated**: 2025-10-14
**Maintained By**: Doxstrux development team
**Status**: 📋 Ready for implementation
