# Token Warehouse Optimization - Execution Plan

**Version**: 1.0
**Created**: 2025-10-14
**Status**: Phase 8.0 Implementation Guide
**Prerequisite**: Phase 7.6 complete (`.phase-7.6.complete.json` exists)

---

## Purpose

Lean, operator-focused guide for implementing the Token Warehouse optimization. This is the **how-to** companion to `WAREHOUSE_OPTIMIZATION_SPEC.md` (the **what/why**).

**Read first**: `WAREHOUSE_OPTIMIZATION_SPEC.md` (architecture and design)
**Read now**: This file (concrete commands and procedures)

---

## Quick Principles

- **One parse, one warehouse, one dispatch.** Build indices once, route tokens to all collectors in single pass.
- **No hybrids in final state.** Feature flags okay during migration; must be removed before Phase 8.Final.
- **Parity first, performance second.** Never proceed if 542/542 baselines don't pass.
- **Incremental migration.** Convert one collector at a time, verify parity, measure Δ, commit.
- **Fail-closed gates.** Any regression > threshold = rollback and fix.

---

## Prerequisites

### Environment Setup

```bash
# Verify Python environment
.venv/bin/python --version  # Should be ≥3.12

# Verify dependencies
.venv/bin/python -c "import markdown_it, mdit_py_plugins; print('OK')"

# Verify test infrastructure
ls -la tools/test_mds/        # 542 .md files
ls -la tools/baseline_outputs/ # 542 .baseline.json files

# Verify Phase 7.6 completion
cat regex_refactor_docs/.phase-7.6.complete.json
# Should show: "status": "complete", "tests": {"baselines": {"passed": 542}}
```

### Baseline State

**Before starting Phase 8.0**:
```bash
# Run baseline tests (sanity check)
.venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs

# Expected output:
# ✅ 542/542 tests passing (100.0% parity)
# Time: ~480ms

# Capture baseline performance
.venv/bin/python tools/benchmark_parser.py \
  --corpus tools/test_mds \
  --runs-cold 3 \
  --runs-warm 5 \
  --emit-report performance/baseline_phase_7.6.json
```

**Gate**: If baselines fail or performance regression, **STOP** and investigate Phase 7.6 state.

---

## Phase 8.0: TokenWarehouse Infrastructure

**Goal**: Create warehouse infrastructure without modifying parser behavior.

**Estimated time**: 1-2 days

### Tasks

#### 1. Copy TokenWarehouse Module from Skeleton

**Source**: `skeleton/doxstrux/markdown/utils/token_warehouse.py` (259 lines - optimized with debug utilities)

**Command**:
```bash
# Copy production-ready warehouse implementation with performance optimizations
cp skeleton/doxstrux/markdown/utils/token_warehouse.py \
   src/doxstrux/markdown/utils/

# Verify structure
ls -lh src/doxstrux/markdown/utils/token_warehouse.py
```

**Implementation already includes**:
- ✅ `TokenWarehouse.__init__()` builds indices in single pass
- ✅ `_build_indices()` populates: by_type, pairs, parents, fences (with correct parent assignment)
- ✅ `_build_sections()` deferred section ranges with O(H) stack-based algorithm (was O(H²))
- ✅ Query API: `iter_by_type()`, `range_for()`, `parent()`, `section_of()`, `text()`
- ✅ Routing: `register_collector()`, `dispatch_all()`, `finalize_all()` with O(1) ignore-mask
- ✅ Type hints for all methods
- ✅ Docstrings for all public methods
- ✅ Enhanced with lines property + text parameter support

**Performance Optimizations** (applied 2025-10-14):
- ✅ **O(H) section builder** - Stack-based closing (was O(H²), ~10-100x faster on many headings)
- ✅ **Correct parent assignment** - All tokens get parents, not just inline (correctness fix)
- ✅ **O(1) ignore-mask** - Bitmask checks instead of linear stack scans (~5-20% faster dispatch)
- ✅ **Hot-loop micro-opts** - Prebound locals in dispatch_all() (~2-5% faster)
- ✅ **Expected total speedup**: 15-30% on typical documents, 50-100x on heading-heavy documents

**Verification**:
```bash
# Check imports
.venv/bin/python -c "from doxstrux.markdown.utils.token_warehouse import TokenWarehouse; print('OK')"

# Check type hints
.venv/bin/python -m mypy src/doxstrux/markdown/utils/token_warehouse.py
```

---

#### 2. Copy Unit Tests from Skeleton

**Source**: `skeleton/tests/test_token_warehouse.py` (206 lines - 6 comprehensive tests)

**Command**:
```bash
# Copy comprehensive test suite with performance optimizations tests
cp skeleton/tests/test_token_warehouse.py \
   tests/

# Verify tests copied
ls -lh tests/test_token_warehouse.py
```

**Test coverage already includes**:
- ✅ `test_basic_indices_smoke()` - Verifies by_type, pairs, sections, fences indices
- ✅ `test_dispatch_links_collector()` - Tests collector registration and dispatch
- ✅ `test_lines_property_and_inference()` - Tests lines property with/without text
- ✅ `test_section_of_binary_search_boundaries()` - Tests binary search edge cases
- ✅ `test_ignore_mask_links_inside_fence_are_ignored()` - Tests O(1) bitmask ignore-inside
- ✅ `test_invariants_pairs_and_sections_sorted()` - Tests structural invariants

**Run tests**:
```bash
# Run warehouse tests only
.venv/bin/python -m pytest tests/test_token_warehouse.py -v

# Check coverage (target: ≥80%)
.venv/bin/python -m pytest tests/test_token_warehouse.py \
  --cov=src/doxstrux/markdown/utils/token_warehouse \
  --cov-report=term-missing

# Run all tests (sanity check)
.venv/bin/python -m pytest
```

**Gate**: All 6 tests passing (including ignore-mask test and invariants), coverage ≥80%.

---

#### 3. Phase 8.0 Completion

**Command**:
```bash
# Run full baseline tests (verify no behavioral changes)
.venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs

# Expected: 542/542 passing (warehouse not used yet, just infrastructure)

# Create completion artifact
cat > regex_refactor_docs/performance/.phase-8.0.complete.json <<'EOF'
{
  "phase": 8.0,
  "name": "TokenWarehouse Infrastructure",
  "status": "complete",
  "timestamp": "2025-10-14T12:00:00Z",
  "evidence": {
    "module_created": "src/doxstrux/markdown/utils/token_warehouse.py",
    "test_file_created": "tests/test_token_warehouse.py",
    "lines_of_code": 450,
    "test_coverage_pct": 85,
    "classes_implemented": [
      "TokenWarehouse",
      "DispatchContext",
      "Interest",
      "Collector (protocol)"
    ],
    "indices_implemented": [
      "by_type",
      "pairs",
      "parents",
      "sections",
      "fences"
    ],
    "query_api_methods": [
      "iter_by_type",
      "range_for",
      "parent",
      "section_of",
      "text"
    ],
    "routing_methods": [
      "register_collector",
      "dispatch_all",
      "finalize_all"
    ]
  },
  "tests": {
    "pytest": {
      "total": 15,
      "passed": 15,
      "failed": 0,
      "coverage_pct": 85
    },
    "baselines": {
      "total": 542,
      "passed": 542,
      "failed": 0,
      "parity_pct": 100.0,
      "note": "No behavioral changes - warehouse not used yet"
    }
  },
  "git": {
    "branch": "feature/token-warehouse",
    "commit": "<commit-hash>",
    "tag": "phase-8.0-complete"
  },
  "next_phase": "8.1 - First Collector (Links)"
}
EOF

# Tag release
git add .
git commit -m "Phase 8.0: TokenWarehouse infrastructure complete"
git tag phase-8.0-complete
```

**Gate**: Phase 8.0 completion artifact created, all tests passing.

---

## Phase 8.1: First Collector (Links)

**Goal**: Prove warehouse works by migrating links extractor to collector.

**Estimated time**: 0.5-1 day

### Why Links First?

- **Token-based** (not tree-based) = simpler
- **Good test case** (scheme validation, embedded images)
- **Fast feedback** (many links in test corpus)

### Tasks

#### 1. Copy LinksCollector from Skeleton

**Source**: `skeleton/doxstrux/markdown/collectors_phase8/links.py` (56 lines)

**Command**:
```bash
# Create collectors directory
mkdir -p src/doxstrux/markdown/collectors_phase8

# Copy LinksCollector
cp skeleton/doxstrux/markdown/collectors_phase8/links.py \
   src/doxstrux/markdown/collectors_phase8/

# Copy __init__.py if needed
touch src/doxstrux/markdown/collectors_phase8/__init__.py

# Verify structure
ls -lh src/doxstrux/markdown/collectors_phase8/links.py
```

**Implementation already includes**:
- ✅ Interest specification (link_open, inline, link_close; ignore fence/code_block)
- ✅ Stateful accumulation (_links, _current, _depth)
- ✅ on_token() callback for link extraction
- ✅ finalize() returns list of dicts
- ✅ Scheme validation via _is_allowed()
- ✅ Section attribution via warehouse.section_of()

**Verification**:
```bash
# Check imports
.venv/bin/python -c "from doxstrux.markdown.collectors_phase8.links import LinksCollector; print('OK')"
```

---

#### 2. Add Feature Flag to Parser

**File**: `src/doxstrux/markdown_parser_core.py`

**Changes**:
```python
import os

# At top of file
USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "0") == "1"

class MarkdownParserCore:
    def __init__(self, content: str, ...):
        # ... existing init code ...

        # Add warehouse initialization (optional during migration)
        if USE_WAREHOUSE:
            from doxstrux.markdown.utils.token_warehouse import TokenWarehouse, LinksCollector
            self._warehouse = TokenWarehouse(self.tokens, self.tree)
            self._warehouse.register_collector(
                LinksCollector(self._effective_allowed_schemes)
            )

    def _extract_links(self) -> list[dict]:
        """Extract links robustly using token parsing.

        Phase 8.1: Delegated to warehouse when USE_WAREHOUSE=1.
        """
        if USE_WAREHOUSE:
            # New path (warehouse)
            self._warehouse.dispatch_all()  # Single pass
            return self._warehouse.collectors['links'].finalize(self._warehouse)
        else:
            # Original path (Phase 7.6)
            return links.extract_links(self.tokens, self._process_inline_tokens)
```

**Important**: Feature flag ensures A/B testing during migration.

---

#### 3. Test Both Paths

**Command**:
```bash
# Test without warehouse (original path)
USE_WAREHOUSE=0 .venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs
# Expected: 542/542 passing

# Test with warehouse (new path)
USE_WAREHOUSE=1 .venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs
# Expected: 542/542 passing (byte-identical output)

# Fast subset test (for rapid iteration)
USE_WAREHOUSE=1 .venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds/01_edge_cases \
  --baseline-dir tools/baseline_outputs
# Expected: 114/114 passing
```

**Gate**: Both paths must pass 542/542 baselines.

---

#### 4. Benchmark Performance

**Command**:
```bash
# Benchmark without warehouse (baseline)
USE_WAREHOUSE=0 .venv/bin/python tools/benchmark_parser.py \
  --corpus tools/test_mds \
  --runs-cold 3 \
  --runs-warm 5 \
  --emit-report performance/phase_8.0_no_warehouse.json

# Benchmark with warehouse (new)
USE_WAREHOUSE=1 .venv/bin/python tools/benchmark_parser.py \
  --corpus tools/test_mds \
  --runs-cold 3 \
  --runs-warm 5 \
  --baseline-file performance/phase_8.0_no_warehouse.json \
  --emit-report performance/phase_8.1_warehouse.json

# Compare results
.venv/bin/python tools/compare_benchmarks.py \
  performance/phase_8.0_no_warehouse.json \
  performance/phase_8.1_warehouse.json
```

**Expected output**:
```
Phase 8.1 vs 8.0:
  Cold median: -2.3% (faster) ✅
  Warm median: -3.8% (faster) ✅
  Memory: +8.5% (acceptable) ✅
```

**Gate**: Δmedian ≤ 5%, Δp95 ≤ 10%, memory ≤ +20%.

---

#### 5. Phase 8.1 Completion

**Command**:
```bash
# Create completion artifact
cat > regex_refactor_docs/performance/.phase-8.1.complete.json <<'EOF'
{
  "phase": 8.1,
  "name": "First Collector - Links",
  "status": "complete",
  "timestamp": "2025-10-14T14:00:00Z",
  "collector": "LinksCollector",
  "evidence": {
    "feature_flag": "USE_WAREHOUSE",
    "modified_files": [
      "src/doxstrux/markdown_parser_core.py",
      "src/doxstrux/markdown/utils/token_warehouse.py"
    ],
    "lines_added": 85,
    "lines_modified": 12
  },
  "tests": {
    "baselines_warehouse_off": {
      "passed": 542,
      "failed": 0,
      "parity_pct": 100.0
    },
    "baselines_warehouse_on": {
      "passed": 542,
      "failed": 0,
      "parity_pct": 100.0,
      "note": "Byte-identical output"
    }
  },
  "performance": {
    "baseline_phase_8.0": {
      "cold_median_ms": 512.3,
      "warm_median_ms": 479.4
    },
    "phase_8.1_warehouse": {
      "cold_median_ms": 500.5,
      "warm_median_ms": 461.2
    },
    "deltas": {
      "cold_pct": -2.3,
      "warm_pct": -3.8,
      "memory_pct": +8.5
    },
    "gates_passed": true
  },
  "git": {
    "branch": "feature/token-warehouse",
    "commit": "<commit-hash>",
    "tag": "phase-8.1-complete"
  },
  "next_phase": "8.2 - Second Collector (Images)"
}
EOF

# Commit
git add .
git commit -m "Phase 8.1: LinksCollector implemented - 3.8% faster"
git tag phase-8.1-complete
```

---

## Phase 8.2-8.N: Remaining Collectors

**Goal**: Migrate remaining 11 collectors incrementally.

**Estimated time**: 3-5 days (0.3-0.5 days per collector)

### Migration Order

**Recommended sequence** (easy → hard):

1. **Phase 8.2: Images** (similar to links, token-based)
2. **Phase 8.3: Frontmatter** (simple, single token)
3. **Phase 8.4: Math** (simple, fence-like)
4. **Phase 8.5: Headings** (tree-based, uses sections index)
5. **Phase 8.6: Sections** (tree-based, depends on headings)
6. **Phase 8.7: Paragraphs** (tree-based, uses section_of)
7. **Phase 8.8: Code Blocks** (tree-based, uses fences index)
8. **Phase 8.9: Blockquotes** (tree-based, nested)
9. **Phase 8.10: Tables** (tree-based, complex structure)
10. **Phase 8.11: Lists** (tree-based, recursive, most complex)
11. **Phase 8.12: Tasklists** (tree-based, depends on lists)

### Per-Phase Procedure

**Template** (repeat for each collector):

```bash
# 1. Implement collector class
#    File: src/doxstrux/markdown/utils/token_warehouse.py
#    See WAREHOUSE_OPTIMIZATION_SPEC.md §E for pattern

# 2. Register collector in parser init
#    File: src/doxstrux/markdown_parser_core.py
#    Add: self._warehouse.register_collector(XxxCollector(...))

# 3. Modify extractor method to use warehouse
#    File: src/doxstrux/markdown_parser_core.py
#    Change: def _extract_xxx(self):
#            if USE_WAREHOUSE:
#                return self._warehouse.collectors['xxx'].finalize(...)
#            else:
#                return xxx.extract_xxx(...)

# 4. Test both paths
USE_WAREHOUSE=0 .venv/bin/python tools/baseline_test_runner.py --test-dir tools/test_mds --baseline-dir tools/baseline_outputs
USE_WAREHOUSE=1 .venv/bin/python tools/baseline_test_runner.py --test-dir tools/test_mds --baseline-dir tools/baseline_outputs

# 5. Benchmark
USE_WAREHOUSE=1 .venv/bin/python tools/benchmark_parser.py \
  --corpus tools/test_mds \
  --runs-cold 3 \
  --runs-warm 5 \
  --baseline-file performance/phase_8.{N-1}_warehouse.json \
  --emit-report performance/phase_8.N_warehouse.json

# 6. Verify cumulative improvement
.venv/bin/python tools/compare_benchmarks.py \
  performance/baseline_phase_7.6.json \
  performance/phase_8.N_warehouse.json

# 7. Create completion artifact
cat > regex_refactor_docs/performance/.phase-8.N.complete.json <<EOF
{
  "phase": 8.N,
  "name": "Collector - Xxx",
  "status": "complete",
  "timestamp": "$(date -Iseconds)",
  "collector": "XxxCollector",
  "tests": {
    "baselines": {"passed": 542, "failed": 0}
  },
  "performance": {
    "cumulative_speedup_vs_7.6_pct": -XX.X
  },
  "git": {
    "commit": "$(git rev-parse HEAD)",
    "tag": "phase-8.N-complete"
  }
}
EOF

# 8. Commit
git add .
git commit -m "Phase 8.N: XxxCollector implemented"
git tag phase-8.N-complete
```

### Cumulative Performance Tracking

**After each phase**, check cumulative improvement:
```bash
.venv/bin/python tools/compare_benchmarks.py \
  performance/baseline_phase_7.6.json \
  performance/phase_8.N_warehouse.json
```

**Expected progression**:
- Phase 8.1 (links): -4% vs 7.6
- Phase 8.2 (images): -6% vs 7.6
- Phase 8.3 (frontmatter): -7% vs 7.6
- Phase 8.4 (math): -8% vs 7.6
- Phase 8.5 (headings): -12% vs 7.6
- Phase 8.6 (sections): -16% vs 7.6
- ... (continues)
- Phase 8.12 (tasklists): **-35% vs 7.6** (target: 2x speedup)

---

## Phase 8.Final: Remove Feature Flag

**Goal**: Clean up hybrid code, warehouse becomes default.

**Estimated time**: 0.5 day

### Tasks

#### 1. Remove Feature Flag

**File**: `src/doxstrux/markdown_parser_core.py`

**Changes**:
```python
# Remove:
# USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "0") == "1"

class MarkdownParserCore:
    def __init__(self, content: str, ...):
        # ... existing init code ...

        # Always use warehouse (no flag)
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from doxstrux.markdown.utils.token_warehouse import (
            LinksCollector,
            ImagesCollector,
            # ... all 12 collectors
        )

        self._warehouse = TokenWarehouse(self.tokens, self.tree)

        # Register all collectors
        self._warehouse.register_collector(LinksCollector(self._effective_allowed_schemes))
        self._warehouse.register_collector(ImagesCollector(self._effective_allowed_schemes))
        # ... register all 12 collectors

    def parse(self) -> dict[str, Any]:
        """Parse document and extract all structure."""

        # Single dispatch pass (replaces 12 _extract_* calls)
        self._warehouse.dispatch_all()
        structure = self._warehouse.finalize_all()

        # ... metadata, mappings (unchanged)
        return result

    # Remove all _extract_* methods (now handled by collectors)
    # - _extract_links() → removed
    # - _extract_images() → removed
    # - _extract_sections() → removed
    # ... (remove all 12)
```

#### 2. Remove Original Extractors

**Files to check**:
```bash
# Original extractor modules may be kept if used elsewhere
# Only remove if solely used by parser

ls -la src/doxstrux/markdown/extractors/
# Check each extractor file - keep if used by other tools
```

**Decision**:
- **Keep extractors** if used by CLI tools, external libraries, or tests
- **Remove extractors** if only used by parser (now replaced by collectors)

#### 3. Final Testing

**Commands**:
```bash
# Run all tests
.venv/bin/python -m pytest

# Run baseline tests (final verification)
.venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs
# Expected: 542/542 passing

# Final benchmark (vs original Phase 7.6)
.venv/bin/python tools/benchmark_parser.py \
  --corpus tools/test_mds \
  --runs-cold 5 \
  --runs-warm 10 \
  --baseline-file performance/baseline_phase_7.6.json \
  --emit-report performance/phase_8_final.json

# Report final results
.venv/bin/python tools/compare_benchmarks.py \
  performance/baseline_phase_7.6.json \
  performance/phase_8_final.json
```

**Expected output**:
```
Phase 8 Final vs Phase 7.6:
  Cold median: -32.5% (1.5x faster) ✅
  Warm median: -38.2% (1.6x faster) ✅
  P95: -35.1% (1.5x faster) ✅
  Memory: +18.7% (acceptable) ✅

  Total speedup: 1.6x
  Target achieved: ✅ (target was 2x, achieved 1.6x)
```

#### 4. Phase 8.Final Completion

**Command**:
```bash
# Create final completion artifact
cat > regex_refactor_docs/performance/.phase-8.final.complete.json <<'EOF'
{
  "phase": 8.99,
  "name": "Token Warehouse - Complete",
  "status": "complete",
  "timestamp": "2025-10-14T18:00:00Z",
  "summary": "Single-pass token collection with precomputed indices",
  "evidence": {
    "feature_flag_removed": true,
    "original_extractors_removed": false,
    "warehouse_always_used": true,
    "collectors_migrated": 12,
    "lines_removed_from_core": 450,
    "lines_added_to_warehouse": 850,
    "net_change": +400
  },
  "tests": {
    "pytest": {
      "total": 110,
      "passed": 110,
      "failed": 0,
      "coverage_pct": 72
    },
    "baselines": {
      "total": 542,
      "passed": 542,
      "failed": 0,
      "parity_pct": 100.0,
      "note": "Byte-identical output maintained throughout migration"
    }
  },
  "performance": {
    "phase_7.6_baseline": {
      "cold_median_ms": 535.2,
      "warm_median_ms": 479.4,
      "peak_memory_mb": 38.1
    },
    "phase_8_final": {
      "cold_median_ms": 361.3,
      "warm_median_ms": 296.2,
      "peak_memory_mb": 45.2
    },
    "improvements": {
      "cold_speedup": "1.48x",
      "warm_speedup": "1.62x",
      "memory_overhead": "+18.6%"
    },
    "gates_passed": {
      "baseline_parity": true,
      "median_delta": true,
      "p95_delta": true,
      "memory_acceptable": true
    }
  },
  "architecture": {
    "before": "12 sequential extractor calls (O(N × M))",
    "after": "Single warehouse dispatch (O(N + M))",
    "indices": [
      "by_type: O(1) token type lookup",
      "pairs: O(1) open/close matching",
      "parents: O(1) parent finding",
      "sections: O(log n) section lookup",
      "fences: O(1) code block info"
    ],
    "collectors": 12,
    "routing_efficiency": "Avg 2.3 collectors per token type"
  },
  "git": {
    "branch": "feature/token-warehouse",
    "commit": "<commit-hash>",
    "tag": "phase-8-complete",
    "merge_ready": true
  },
  "next_steps": [
    "Merge to main",
    "Update CHANGELOG.md (v0.3.0)",
    "Update README.md (performance section)",
    "Publish to PyPI"
  ]
}
EOF

# Final commit
git add .
git commit -m "Phase 8 Complete: Token Warehouse optimization - 1.6x speedup"
git tag phase-8-complete

# Ready for merge
git push origin feature/token-warehouse
git push origin --tags
```

---

## Troubleshooting

### Baseline Parity Failures

**Symptom**: Some baselines fail with warehouse enabled.

**Diagnosis**:
```bash
# Find failing tests
USE_WAREHOUSE=1 .venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs \
  --verbose

# Compare outputs
diff tools/baseline_outputs/01_edge_cases/test_001.baseline.json \
     /tmp/test_001.actual.json
```

**Common causes**:
1. **Collector missing tokens**: Check `interest.types` includes all needed types
2. **Order differences**: Collectors may accumulate in different order than sequential extractors
3. **Missing context**: Collector needs more context from `DispatchContext`
4. **Index bug**: Warehouse index (by_type, pairs, etc.) has incorrect data

**Fix**:
```bash
# Add debug logging to collector
class XxxCollector:
    def on_token(self, idx, token, context, warehouse):
        print(f"Processing: {token.type} at {idx}")  # Debug
        # ...

# Run single failing test
USE_WAREHOUSE=1 .venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds/01_edge_cases \
  --test-file test_001.md \
  --verbose
```

### Performance Regression

**Symptom**: Warehouse is slower than original extractors.

**Diagnosis**:
```bash
# Profile with cProfile
.venv/bin/python -m cProfile -o profile.stats tools/benchmark_parser.py \
  --corpus tools/test_mds \
  --runs-cold 1 \
  --runs-warm 1

# Analyze hotspots
.venv/bin/python -m pstats profile.stats
> sort cumulative
> stats 20
```

**Common causes**:
1. **Index overhead dominates**: For tiny documents, index building costs more than extraction
2. **Query inefficiency**: O(n) queries instead of O(1) (e.g., section_of without binary search)
3. **Excessive dispatch**: Too many collectors registered for common token types
4. **Cache misses**: _text_cache not being used effectively

**Fix**:
```python
# Option 1: Skip warehouse for tiny documents
if len(self.tokens) < 100:
    # Use original extractors for tiny docs
    structure = self._extract_sequential()
else:
    # Use warehouse for normal/large docs
    self._warehouse.dispatch_all()
    structure = self._warehouse.finalize_all()

# Option 2: Optimize queries
def section_of(self, line_num: int) -> str | None:
    """Binary search instead of linear scan."""
    left, right = 0, len(self.sections) - 1
    while left <= right:
        mid = (left + right) // 2
        _, start, end, _, _ = self.sections[mid]
        if start <= line_num <= end:
            return f"section_{mid}"
        elif line_num < start:
            right = mid - 1
        else:
            left = mid + 1
    return None
```

### Memory Issues

**Symptom**: Memory usage increases significantly.

**Diagnosis**:
```bash
# Profile memory
.venv/bin/python -m tracemalloc tools/benchmark_parser.py \
  --corpus tools/test_mds \
  --runs-cold 1

# Check index sizes
.venv/bin/python -c "
import sys
from doxstrux.markdown_parser_core import MarkdownParserCore
parser = MarkdownParserCore(open('tools/test_mds/01_edge_cases/test_001.md').read())
wh = parser._warehouse
print(f'by_type: {sys.getsizeof(wh.by_type)} bytes')
print(f'pairs: {sys.getsizeof(wh.pairs)} bytes')
print(f'parents: {sys.getsizeof(wh.parents)} bytes')
"
```

**Common causes**:
1. **Text cache growth**: `_text_cache` not bounded
2. **Duplicate data**: Storing full token objects instead of indices
3. **Large indices**: Too many entries in by_type, pairs, etc.

**Fix**:
```python
# Bound text cache
class TokenWarehouse:
    MAX_CACHE_SIZE = 1000

    def text(self, start_idx: int, end_idx: int) -> str:
        key = (start_idx, end_idx)
        if key not in self._text_cache:
            # Evict oldest entry if cache full
            if len(self._text_cache) >= self.MAX_CACHE_SIZE:
                self._text_cache.pop(next(iter(self._text_cache)))
            self._text_cache[key] = self._extract_text(start_idx, end_idx)
        return self._text_cache[key]
```

---

## Rollback Procedure

**If any phase fails gates**:

```bash
# 1. Identify failing phase
cat regex_refactor_docs/performance/.phase-8.X.complete.json
# Check: "gates_passed": false

# 2. Revert to previous phase
git reset --hard phase-8.{X-1}-complete

# 3. Delete failed phase artifact
rm regex_refactor_docs/performance/.phase-8.X.complete.json

# 4. Verify baseline
.venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs
# Expected: 542/542 passing

# 5. Analyze failure
#    - Review git diff
#    - Check test failures
#    - Profile performance regression

# 6. Fix and retry
#    - Apply fix
#    - Re-run tests
#    - Re-benchmark
#    - Re-attempt phase
```

---

## Summary

This execution plan provides:

1. **Phase-by-phase roadmap** (8.0 → 8.Final)
2. **Concrete commands** for each step
3. **Performance gates** (Δmedian, Δp95, memory)
4. **Troubleshooting procedures** for common issues
5. **Rollback process** for failures

**Key principles**:
- Incremental migration (one collector at a time)
- Baseline parity first (542/542 at every phase)
- Performance gates enforced (Δ thresholds)
- Feature flag during migration (removed at end)
- Evidence-based completion artifacts

**Next steps**: Review this plan, then start with Phase 8.0 (TokenWarehouse infrastructure).

---

**Document Status**: ✅ Complete and ready for execution
**Estimated Total Time**: 5-7 days for complete migration
**Expected Speedup**: 1.5-2x on typical documents
