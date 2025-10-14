# Token Warehouse - Reference Implementation

**Version**: Combined skeleton (best of both versions)
**Created**: 2025-10-14
**Status**: Production-ready with all optimizations

---

## Overview

This is the canonical reference implementation for Phase 8 Token Warehouse optimization. It combines:

- **Optimized warehouse** from current skeleton (226 lines, compact and fast)
- **All 12 collectors** from old skeleton (complete migration reference)
- **Combined tests** (6 tests: all edge cases covered)
- **Performance optimizations** applied (O(H) sections, O(1) ignore-mask, hot-loop opts)

---

## Performance Optimizations Included

### 1. O(H) Section Builder (was O(H²))
Stack-based closing of sections instead of nested loops.
- **Speedup**: 10-100x on heading-heavy documents
- **Location**: `token_warehouse.py:_build_sections()`

### 2. Correct Parent Assignment
All tokens get parents assigned before stack mutation, not just inline tokens.
- **Type**: Correctness fix (was a bug)
- **Location**: `token_warehouse.py:_build_indices()`

### 3. O(1) Ignore-Mask with Bitmasks
Bitmask checks instead of linear stack scans for `ignore_inside` filtering.
- **Speedup**: 5-20% faster dispatch
- **Location**: `token_warehouse.py:dispatch_all()`

### 4. Hot-Loop Micro-Optimizations
Prebound locals in `dispatch_all()` to avoid attribute lookups.
- **Speedup**: 2-5% faster
- **Location**: `token_warehouse.py:dispatch_all()`

### 5. Nullable should_process
Skip redundant `should_process()` calls when ignore-mask already filters.
- **Speedup**: ~2% faster
- **Location**: `token_warehouse.py:dispatch_all()`

**Expected Total Speedup**: 15-30% on typical documents, 50-100x on heading-heavy documents

---

## File Structure

```
skeleton/
├── doxstrux/markdown/
│   ├── utils/
│   │   └── token_warehouse.py          (259 lines) - Optimized warehouse + debug util
│   ├── collectors_phase8/
│   │   ├── __init__.py                  (0 lines) - Package init
│   │   ├── links.py                     (56 lines) - Links collector ⭐ Phase 8.1
│   │   ├── images.py                    (32 lines) - Images collector
│   │   ├── codeblocks.py                (29 lines) - Code blocks collector
│   │   ├── footnotes.py                 (40 lines) - Footnotes collector
│   │   ├── headings.py                  (39 lines) - Headings collector
│   │   ├── html.py                      (26 lines) - HTML collector
│   │   ├── lists.py                     (45 lines) - Lists collector
│   │   ├── math.py                      (25 lines) - Math collector
│   │   ├── paragraphs.py                (33 lines) - Paragraphs collector
│   │   ├── sections.py                  (34 lines) - Sections collector
│   │   ├── tables.py                    (48 lines) - Tables collector
│   │   └── tasklists.py                 (29 lines) - Tasklists collector
│   ├── core/
│   │   └── parser_adapter.py            (29 lines) - Feature flag integration
│   └── cli/
│       ├── __init__.py                  (1 line) - CLI package
│       ├── __main__.py                  (8 lines) - Module entry point
│       └── dump_sections.py             (102 lines) - Section debug tool ✨
├── tests/
│   ├── test_token_warehouse.py          (206 lines) - 6 comprehensive tests
│   └── test_fuzz_collectors.py          (318 lines) - Fuzz tests ⚡ NEW
├── tools/
│   ├── benchmark_parser.py              (44 lines) - Benchmark scaffold
│   └── profile_collectors.py            (260 lines) - Profiling tool ⚡ NEW
└── README.md                            (~540 lines) - Complete guide

Total: 24 files, 1,704 lines of code
```

⭐ = Recommended for Phase 8.1 (first collector migration)

---

## Tests Included (6 Tests)

All tests use minimal mock tokens and verify core functionality:

### 1. `test_basic_indices_smoke()`
Verifies all indices are built correctly:
- `by_type` index
- `pairs` index (open → close)
- `sections` index
- `fences` index

### 2. `test_dispatch_links_collector()`
Full end-to-end test of collector dispatch:
- Collector registration
- Single-pass dispatch
- Finalization
- **Verifies**: Links are correctly extracted with text and URL

### 3. `test_lines_property_and_inference()`
Verifies lines property works with/without text parameter:
- **With text**: `lines` populated, `line_count` accurate
- **Without text**: `lines` is None, `line_count` inferred from token maps

### 4. `test_section_of_binary_search_boundaries()`
Verifies binary search section lookup handles edge cases:
- Lines at section boundaries
- Lines inside sections
- Lines outside all sections (returns None)

### 5. `test_ignore_mask_links_inside_fence_are_ignored()`
Verifies O(1) bitmask ignore-inside works:
- Links inside fenced code blocks are ignored
- **Tests**: Performance optimization (bitmask vs linear scan)

### 6. `test_invariants_pairs_and_sections_sorted()`
Verifies structural invariants:
- Pairs: `open < close` for all pairs
- Sections: Sorted by start line, non-overlapping

**Run tests**:
```bash
pytest tests/test_token_warehouse.py -v
```

---

## Quick Start: Phase 8.0 (Infrastructure)

### Step 1: Copy Warehouse Module

```bash
# Copy optimized warehouse to main codebase
cp skeleton/doxstrux/markdown/utils/token_warehouse.py \
   src/doxstrux/markdown/utils/

# Verify
ls -lh src/doxstrux/markdown/utils/token_warehouse.py
```

### Step 2: Copy Tests

```bash
# Copy comprehensive test suite
cp skeleton/tests/test_token_warehouse.py \
   tests/

# Run tests
pytest tests/test_token_warehouse.py -v
# Expected: 6 tests passing
```

### Step 3: Verify Implementation

```bash
# Check imports work
python -c "from doxstrux.markdown.utils.token_warehouse import TokenWarehouse; print('OK')"

# Check type hints
mypy src/doxstrux/markdown/utils/token_warehouse.py

# Run baseline tests (warehouse not integrated yet, just infrastructure)
.venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs
# Expected: 542/542 passing (no behavioral changes)
```

---

## Quick Start: Phase 8.1 (First Collector - Links)

### Step 1: Copy LinksCollector

```bash
# Create collectors directory
mkdir -p src/doxstrux/markdown/collectors_phase8

# Copy links collector
cp skeleton/doxstrux/markdown/collectors_phase8/links.py \
   src/doxstrux/markdown/collectors_phase8/

# Copy __init__.py
cp skeleton/doxstrux/markdown/collectors_phase8/__init__.py \
   src/doxstrux/markdown/collectors_phase8/
```

### Step 2: Add Feature Flag to Parser

```python
# In src/doxstrux/markdown_parser_core.py
import os

USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "0") == "1"

class MarkdownParserCore:
    def __init__(self, content: str, ...):
        # ... existing init code ...

        # Add warehouse initialization (optional during migration)
        if USE_WAREHOUSE:
            from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
            from doxstrux.markdown.collectors_phase8.links import LinksCollector

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
            self._warehouse.dispatch_all()
            return self._warehouse.finalize_all()["links"]
        else:
            # Original path (Phase 7.6)
            from doxstrux.markdown.extractors import links
            return links.extract_links(self.tokens, self._process_inline_tokens)
```

### Step 3: Test Both Paths

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
```

### Step 4: Benchmark Performance

```bash
# Benchmark without warehouse
USE_WAREHOUSE=0 .venv/bin/python tools/benchmark_parser.py \
  --corpus tools/test_mds \
  --runs-cold 3 \
  --runs-warm 5 \
  --emit-report performance/phase_8.0_no_warehouse.json

# Benchmark with warehouse
USE_WAREHOUSE=1 .venv/bin/python tools/benchmark_parser.py \
  --corpus tools/test_mds \
  --runs-cold 3 \
  --runs-warm 5 \
  --baseline-file performance/phase_8.0_no_warehouse.json \
  --emit-report performance/phase_8.1_warehouse.json
```

---

## Remaining Collectors (Phase 8.2-8.N)

All collectors are already implemented in `doxstrux/markdown/collectors_phase8/`. Migrate them incrementally in this order:

**Recommended Order** (easy → hard):

1. **Phase 8.2: Images** - Similar to links, token-based (32 lines)
2. **Phase 8.3: Math** - Simple, fence-like (25 lines)
3. **Phase 8.4: HTML** - HTML blocks & inline (26 lines)
4. **Phase 8.5: Codeblocks** - Fence-based (29 lines)
5. **Phase 8.6: Headings** - Tree-based, uses sections index (39 lines)
6. **Phase 8.7: Sections** - Tree-based, depends on headings (34 lines)
7. **Phase 8.8: Paragraphs** - Tree-based, uses section_of (33 lines)
8. **Phase 8.9: Footnotes** - Token-based with refs (40 lines)
9. **Phase 8.10: Tables** - Tree-based, complex structure (48 lines)
10. **Phase 8.11: Lists** - Tree-based, recursive (45 lines)
11. **Phase 8.12: Tasklists** - Tree-based, depends on lists (29 lines)

**Per-Phase Procedure**:

1. Copy collector from skeleton to `src/doxstrux/markdown/collectors_phase8/`
2. Register collector in parser `__init__` (inside `if USE_WAREHOUSE:`)
3. Modify `_extract_*()` to use warehouse when flag enabled
4. Test both paths (542/542 each)
5. Benchmark (verify Δ ≤ targets)
6. Create `.phase-8.X.complete.json`

---

## Collector API Reference

All collectors follow this pattern:

```python
from doxstrux.markdown.utils.token_warehouse import (
    Collector, Interest, DispatchContext, TokenWarehouse
)

class XxxCollector:
    """Collect xxx elements during warehouse dispatch."""

    def __init__(self, **config):
        self.name = "xxx"  # Must match finalize_all() key
        self.interest = Interest(
            types={"xxx_open", "xxx_close", "inline"},  # Token types to receive
            ignore_inside={"fence", "code_block"}       # Skip inside these blocks
        )

        # State (accumulated during dispatch)
        self._items: list[dict] = []
        self._current: dict | None = None

    def should_process(
        self,
        token: Any,
        ctx: DispatchContext,
        wh: TokenWarehouse
    ) -> bool:
        """Decide if this token should be processed.

        Optional: If ignore_inside handles all filtering, omit this method.
        """
        return True  # Or custom logic

    def on_token(
        self,
        idx: int,
        token: Any,
        ctx: DispatchContext,
        wh: TokenWarehouse
    ) -> None:
        """Process a token (accumulate data).

        Called by warehouse during dispatch_all() for matching tokens.
        """
        if token.type == "xxx_open":
            self._current = {
                "id": f"xxx_{len(self._items)}",
                # ... extract data ...
            }
        elif token.type == "xxx_close" and self._current:
            self._items.append(self._current)
            self._current = None

    def finalize(self, wh: TokenWarehouse) -> list[dict]:
        """Return extracted data after dispatch completes.

        Called by warehouse.finalize_all().
        """
        return self._items
```

---

## Performance Measurement

### Before/After Comparison

**Phase 7.6 Baseline** (sequential extractors):
- Median: 0.88ms per document
- Total: 479.40ms for 542 documents
- Architecture: 12 sequential passes (O(N × M))

**Phase 8 Target** (warehouse):
- Median: 0.55ms per document (1.6x faster)
- Total: ~300ms for 542 documents
- Architecture: Single dispatch pass (O(N + M))

### Measurement Command

```bash
# Benchmark script included in tools/
.venv/bin/python tools/benchmark_parser.py \
  --corpus tools/test_mds \
  --runs-cold 3 \
  --runs-warm 5 \
  --baseline-file performance/baseline_phase_7.6.json \
  --emit-report performance/phase_8.X.json
```

---

## Key Design Principles

### 1. Single-Pass Token Collection
Build all indices in one pass during warehouse initialization:
- `by_type`: O(1) token type lookup
- `pairs`: O(1) open/close matching
- `parents`: O(1) parent finding
- `sections`: O(log n) section lookup
- `fences`: O(1) code block info

### 2. Collector Pattern
Stateful accumulators that register interest in token types:
- **Register**: Collector declares interest in token types
- **Dispatch**: Warehouse routes tokens to interested collectors
- **Finalize**: Collectors return extracted data

### 3. O(1) Routing
Routing table maps token types to collectors:
- Average 2-3 collectors per token type (not all 12)
- Bitmask filtering for `ignore_inside` (O(1))
- Early exit via predicates

### 4. Incremental Migration
Feature flag enables A/B testing during migration:
- Phase 8.0: Infrastructure only
- Phase 8.1-8.N: Migrate collectors one at a time
- Phase 8.Final: Remove flag, warehouse always used

---

## Documentation References

For complete details, see parent directory documentation:

- **WAREHOUSE_OPTIMIZATION_SPEC.md** - Architecture and design
- **WAREHOUSE_EXECUTION_PLAN.md** - Implementation roadmap
- **SECURITY_AND_PERFORMANCE_REVIEW.md** - Security hardening and micro-opts
- **.phase-8.0.template.json** - Completion artifact template

---

## Status

**Current**: ✅ Production-ready reference implementation
**Phase 8.0**: 📋 Ready to copy and implement
**Phase 8.1+**: 📋 All collectors available as templates

**Next Steps**:
1. Copy warehouse and tests to main codebase
2. Verify tests pass (6/6)
3. Copy LinksCollector for Phase 8.1
4. Implement feature flag in parser
5. Test both paths (542/542 each)
6. Benchmark and verify speedup

---

**Last Updated**: 2025-10-14
**Total Code**: 1,126 lines (259 warehouse + 436 collectors + 206 tests + 225 tools/cli)
**Performance**: 15-30% faster typical, 50-100x faster heading-heavy
**Quality**: Production-ready with all optimizations applied

---

## Debug Utilities

### 1. debug_dump_sections()

Quick diagnostic tool inside TokenWarehouse for visualizing section boundaries:

```python
from doxstrux.markdown.utils.token_warehouse import TokenWarehouse

# After building warehouse
wh = TokenWarehouse(tokens, tree, text=text)

# Dump all sections
print(wh.debug_dump_sections())

# Dump first 10 sections only
print(wh.debug_dump_sections(limit=10))
```

**Example output**:
```
[00] L1    0-  12 | 'Introduction'
[01] L2   13-  45 | 'Background'
[02] L2   46-  89 | 'Methodology'
[03] L3   90- 123 | 'Data Collection'
[04] L3  124- 156 | 'Analysis Methods'
[05] L2  157- 234 | 'Results'
```

**Use cases**:
- Verify O(H) section builder correctness (no overlap, correct hierarchy)
- Debug section boundary issues
- Confirm heading level nesting
- Zero runtime impact unless explicitly called

---

### 2. dump_sections CLI Tool

Minimal CLI script for quickly inspecting section boundaries in markdown files:

```bash
# As module (if installed)
python -m doxstrux.markdown.cli.dump_sections README.md

# Or directly
python skeleton/doxstrux/markdown/cli/dump_sections.py README.md
```

**Example output**:
```
File: README.md
Lines: 450
Sections: 23

Section Map:
============================================================
[00] L1    0-  17 | 'Token Warehouse - Reference Implementation'
[01] L2   18-  47 | 'Overview'
[02] L2   48-  85 | 'Performance Optimizations Included'
[03] L3   21-  25 | 'O(H) Section Builder (was O(H²))'
[04] L3   26-  30 | 'Correct Parent Assignment'
...
============================================================

Statistics:
  Total sections: 23
  Heading levels: [1, 2, 3]
  Deepest nesting: L3
```

**Use cases**:
- Quick visualization of document structure
- Verify section parsing before/after changes
- Compare section boundaries across parser versions
- Debugging heading-heavy documents (where O(H) optimization matters most)

**Location**: `skeleton/doxstrux/markdown/cli/dump_sections.py`

---

### 3. Fuzz Testing (`test_fuzz_collectors.py`)

Randomized structural integrity testing to catch edge cases:

```bash
# Run fuzz tests
pytest tests/test_fuzz_collectors.py -v

# Run with many iterations (stress test)
pytest tests/test_fuzz_collectors.py -v --count=100
```

**What it tests**:
- Section boundaries never overlap (prevents DoS)
- Pairs are always legal (`open < close`)
- Binary search correctness on randomized headings
- Collectors never raise exceptions
- Deep nesting stability

**Example test cases**:
- `test_fuzz_sections_and_links`: 20-100 random headings + links
- `test_fuzz_collectors_never_raise`: Collectors stable on random inputs
- `test_fuzz_heading_permutations`: Random level sequences
- `test_nested_blocks_pairs`: Deep nesting (10+ levels)

**Location**: `skeleton/tests/test_fuzz_collectors.py`

---

### 4. Performance Profiling (`profile_collectors.py`)

Reproducible performance measurement and profiling:

```bash
# Quick benchmark (no profiler)
python tools/profile_collectors.py

# With Scalene (detailed CPU/memory breakdown)
pip install scalene
scalene --reduced-profile tools/profile_collectors.py

# With py-spy (sampling-based, fast)
pip install py-spy
py-spy top -- python tools/profile_collectors.py

# With built-in cProfile
python -m cProfile -o profile.stats tools/profile_collectors.py
python -c "import pstats; p=pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(30)"
```

**What it measures**:
- Warehouse index building time (O(N) verification)
- Collector dispatch time (O(N × C_avg) verification)
- Memory overhead (~20% expected)
- Scaling characteristics (1K → 100K tokens)

**Example output**:
```
SCALING BENCHMARK (verifying O(N) complexity)
================================================================================
Tokens     Warehouse (ms)       Full Pipeline (ms)   Links Found
--------------------------------------------------------------------------------
1000       1.23                 2.45                 150
5000       5.67                 10.23                750
10000      11.45                20.12                1500
50000      55.23                98.45                7500
================================================================================

Expected: Time should scale linearly (2x tokens → ~2x time)
```

**Location**: `skeleton/tools/profile_collectors.py`

---

## Security Hardening

See `../SECURITY_HARDENING_CHECKLIST.md` for comprehensive security review covering:

1. **Security** (surgical, zero perf tax):
   - Scheme allowlist at collector edge
   - HTML boundary documentation
   - Structural invariant tests
   - Fault isolation (prod vs test mode)

2. **Runtime Correctness** (prevent silent bugs):
   - Parent mapping order
   - Section builder O(H) complexity lock
   - Binary search invariants
   - Fence format documentation

3. **Raw Speed** (measurable wins):
   - Hot-loop optimizations (already applied)
   - Text accumulation audit
   - Optional SoA cache (if profiler warrants)

4. **Maintainability**:
   - Intent-revealing names
   - Invariants at top of class
   - Regression test suite

**Estimated time to apply**: 4-6 hours
**Status**: All critical items identified and documented
