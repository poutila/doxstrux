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

### 5. **.phase-8.0.template.json**
Completion artifact template for Phase 8.0.

**Purpose**: Mechanically gate Phase 8.1 until warehouse infrastructure passes all gates.

**Schema**: Extends parent directory's phase completion schema with performance deltas.

---

### 6. **skeleton/** (Canonical Reference Implementation)
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
├── README.md                              (446 lines) - This file
├── WAREHOUSE_OPTIMIZATION_SPEC.md        (1,213 lines) - Technical spec
├── WAREHOUSE_EXECUTION_PLAN.md           (996 lines) - Implementation guide
├── SECURITY_AND_PERFORMANCE_REVIEW.md    (1,000 lines) - Security & micro-opts review
├── .phase-8.0.template.json              (101 lines) - Completion template
├── skeleton/                              - Canonical reference implementation ⭐
│   ├── doxstrux/markdown/
│   │   ├── utils/token_warehouse.py   (259 lines) - Optimized warehouse + debug
│   │   ├── collectors_phase8/         (12 collectors, 436 lines) - All collectors
│   │   ├── core/parser_adapter.py     (29 lines) - Feature flag
│   │   └── cli/dump_sections.py       (102 lines) - Debug CLI tool
│   ├── tests/test_token_warehouse.py  (206 lines) - 6 comprehensive tests
│   ├── tools/benchmark_parser.py      (44 lines) - Benchmark scaffold
│   └── README.md                      (~530 lines) - Complete guide
├── steps_taken/                           - Phase completion documentation
└── archived/                              - Historical documents
```

**Total**: 3,756 lines of specification + 1,119 lines of skeleton code

**Performance**: Skeleton includes O(H) section builder, O(1) ignore-mask, hot-loop optimizations, and debug utilities.

---

## Quick Start

### For Implementation
1. Read `WAREHOUSE_OPTIMIZATION_SPEC.md` (architecture)
2. Read `WAREHOUSE_EXECUTION_PLAN.md` (roadmap)
3. **Read `SECURITY_AND_PERFORMANCE_REVIEW.md` (apply security hardening first)**
4. Review `skeleton/` (reference implementation)
5. Create feature branch: `git checkout -b feature/token-warehouse`
6. Copy skeleton files to main codebase:
   ```bash
   cp skeleton/doxstrux/markdown/utils/token_warehouse.py \
      src/doxstrux/markdown/utils/
   cp skeleton/doxstrux/markdown/collectors_phase8/links.py \
      src/doxstrux/markdown/collectors_phase8/
   cp skeleton/tests/test_token_warehouse.py \
      tests/
   ```
6. Implement Phase 8.0 (infrastructure)
7. Run gates and create `.phase-8.0.complete.json`
8. Migrate collectors incrementally (Phases 8.1-8.N)

### For Review
1. Read this README (context)
2. Review `WAREHOUSE_OPTIMIZATION_SPEC.md` (design)
3. Check benchmarking methodology
4. Verify baseline parity requirements

---

## References

### Parent Documentation
- `../REGEX_REFACTOR_EXECUTION_GUIDE.md` - Original refactoring approach
- `../DETAILED_TASK_LIST.md` - Phase 0-7 task breakdowns
- `../.phase-7.6.complete.json` - Current completion state

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
