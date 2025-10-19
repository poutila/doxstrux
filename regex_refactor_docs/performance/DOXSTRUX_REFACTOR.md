# Doxstrux Skeleton Refactoring Plan
# Make skeleton/doxstrux a Drop-In Replacement for src/doxstrux

**Date**: 2025-10-19
**Status**: Implementation Plan Ready
**Estimated Effort**: 13-20 days (60-70% core rewrite, 3-6 day savings from existing work)
**Risk Level**: HIGH (major architectural changes)

---

## Executive Summary

This document provides a detailed, step-by-step plan to refactor `skeleton/doxstrux/` into a production-ready, drop-in replacement for `src/doxstrux/`.

**Current State**: skeleton has good scaffolding but incomplete Phase-8 TokenWarehouse implementation
**Target State**: Fully functional TokenWarehouse with O(N+M) dispatch, complete indices, baseline parity
**Approach**: 10-step surgical conversion based on architecture gap analysis

---

## 72-Hour Fast-Track Execution Plan

**For experienced developers who want rapid iteration**

This compressed timeline focuses on the critical path to achieve baseline parity quickly. Use this for proof-of-concept or when timeline is critical. Falls back to the detailed 13-20 day plan if blockers emerge.

### Day 1: Core Infrastructure (6-8 hours)
**Goal**: Complete index building + section lookup + helper methods

**Morning (3-4 hours)**:
1. Implement `_build_indices()` in `token_warehouse.py`:
   - All 5 indices: `by_type`, `pairs`, `parents`, `sections`, `_line_starts`
   - Add bidirectional pairs: `pairs` (open→close) AND `pairs_rev` (close→open)
   - Add children index: `children[parent_idx] = [child_idx...]`
   - Unicode normalization (NFC), CRLF normalization
2. Add `section_of(line)` with binary search (O(log N))

**Afternoon (3-4 hours)**:
3. Add helper methods:
   - `find_close(idx)`, `find_parent(idx)`, `find_children(idx)`
   - `tokens_between(a, b, type=None)`, `text_between(a, b)`
   - `get_line_range(start, end)`, `get_token_text(idx)`
4. Write unit tests for indices and section_of()
5. **Gate**: All index tests green before Day 2

**Expected Output**: `token_warehouse.py` complete with working indices, tests passing

---

### Day 2: Dispatch + Collector Migration (6-8 hours)
**Goal**: Single-pass O(N+M) dispatch + prove pattern with 2-3 collectors

**Morning (3-4 hours)**:
1. Implement routing table in `register_collector()`:
   - Build `self._routing: dict[str, list[Collector]]`
   - Support both type-based and tag-based routing
2. Rewrite `dispatch_all()` for single-pass:
   - One iteration over tokens
   - O(1) routing table lookup per token
   - Keep reentrancy guard + timeout protection
   - Add platform check for SIGALRM (Unix) vs thread timer (Windows)
3. Add complexity verification test

**Afternoon (3-4 hours)**:
4. Migrate 2-3 representative collectors to index-first pattern:
   - **LinksCollector**: Use `find_close()`, `text_between()`
   - **ImagesCollector**: Similar to links
   - **HeadingsCollector**: Use `sections` index
5. Ban `for tok in wh.tokens` iteration in migrated collectors
6. **Gate**: Dispatch complexity test proves O(N+M), migrated collectors pass tests

**Expected Output**: Dispatch working, 3 collectors using indices, performance verified

---

### Day 3: API Shim + Baseline Parity (8-10 hours)
**Goal**: Drop-in compatibility + baseline test fixes

**Morning (3-4 hours)**:
1. Create `markdown/parser.py` with `MarkdownParserCore` class:
   - Match src API signature exactly
   - Register all 12 collectors
   - `parse()` returns src-compatible dict
   - Add all `extract_*()` methods
2. Migrate remaining 9 collectors to index-first
3. Wire all collectors into parser

**Afternoon (4-5 hours)**:
4. Run baseline test suite:
   ```bash
   .venv/bin/python tools/baseline_test_runner.py \
       --test-dir tools/test_mds \
       --baseline-dir tools/baseline_outputs \
       --parser-module skeleton.doxstrux
   ```
5. Fix first wave of failures (focus on output structure differences)
6. Run performance smoke test
7. **Gate**: >80% baseline tests passing, no critical perf regressions

**Late Afternoon/Evening (1-2 hours)**:
8. Document blockers for remaining failures
9. Create issue list for Day 4+ work
10. **Decision Point**: If <80% parity, fall back to detailed plan

**Expected Output**: API-compatible parser, 450+ baseline tests passing, perf smoke green

---

### Post-Day 3: Iteration to 100% Parity
- Continue fixing baseline test failures systematically
- Add comprehensive unit tests (Phase C, Steps 7-8)
- Wire up CI gates (Phase D, Step 9)
- Security re-verification (Phase D, Step 10)

**Success Criteria for 72-Hour Track**:
- [ ] Indices fully populated and tested
- [ ] O(N+M) dispatch verified
- [ ] API shim compatible with src
- [ ] ≥80% baseline parity (450+/542 tests)
- [ ] Performance within 10% of src
- [ ] Clear path to 100% parity identified

---

## Prerequisites

### Environment
- Python 3.12+
- .venv with mdit-py-plugins installed
- Access to baseline test suite (542 tests)
- src/doxstrux/ for comparison reference

### Required Reading
1. **COMPARISON.md** - Architecture differences between src and skeleton
2. **Phase-8 TokenWarehouse Spec** (from verdict analysis)
3. **src/doxstrux/markdown_parser_core.py** - Current production parser

### Success Criteria
- [ ] All 542 baseline tests pass with skeleton
- [ ] Performance: O(N+M) dispatch (not O(N×M))
- [ ] API compatibility: Drop-in replacement for src parser
- [ ] Security: All src security features preserved + new Phase-8 features
- [ ] section_of() in O(log N) time via binary search

---

## Existing Assets Inventory

**Purpose**: Document what's already complete to avoid duplicate work

The skeleton directory already contains substantial Phase-8 security hardening work. This inventory shows what can be leveraged for the drop-in refactor plan.

### ✅ Existing Tests (23 files - 231KB total)

**Location**: `skeleton/tests/`

**Security Tests** (11 files):
1. `test_html_xss_end_to_end.py` (11.4KB) - XSS attack vector testing
2. `test_html_render_litmus.py` (12.7KB) - HTML rendering safety tests
3. `test_template_injection_end_to_end.py` (9.6KB) - SSTI prevention tests
4. `test_metadata_template_safety.py` (10.3KB) - Frontmatter template safety
5. `test_template_syntax_detection.py` (7.3KB) - Template syntax detection
6. `test_consumer_ssti_litmus.py` (4.5KB) - Consumer-side SSTI tests
7. `test_url_normalization_parity.py` (19.8KB) - URL normalization baseline parity
8. `test_url_normalization_consistency.py` (8.3KB) - URL normalization consistency
9. `test_adversarial_runner.py` (4.3KB) - Adversarial corpus test runner
10. `test_vulnerabilities_extended.py` (13.3KB) - Extended vulnerability tests
11. `test_malicious_token_methods.py` (3.4KB) - Token method injection protection

**Performance Tests** (3 files):
12. `test_performance_scaling.py` (7.5KB) - Parser scaling characteristics
13. `test_section_lookup_performance.py` (4.4KB) - O(log N) section_of() verification
14. `test_fuzz_collectors.py` (12.5KB) - Collector fuzzing tests

**Warehouse Tests** (2 files):
15. `test_token_warehouse.py` (7.9KB) - Basic warehouse functionality
16. `test_token_warehouse_adversarial.py` (1.7KB) - Adversarial warehouse inputs

**Collector Tests** (5 files):
17. `test_collector_timeout.py` (6.9KB) - Collector timeout protection
18. `test_collector_subprocess_isolation.py` (7.9KB) - Subprocess isolation tests
19. `test_collector_caps_end_to_end.py` (22.2KB) - Collector resource caps
20. `test_lint_collectors.py` (5.6KB) - Collector code quality checks
21. `test_dispatch_reentrancy.py` (2.2KB) - Dispatch reentrancy guard tests

**Test Infrastructure** (2 files):
22. `conftest.py` (380 bytes) - Pytest configuration
23. `__pycache__/` - Python cache directory

**Reusability**: ✅ **HIGH** - All tests are production-ready and cover critical security/performance paths. Steps 7-8 can leverage these directly.

---

### ✅ Existing Tools (6 files)

**Location**: `skeleton/tools/`

1. `benchmark_parser.py` (1.6KB) - Parser performance benchmarking
2. `collector_worker.py` (6.7KB) - Collector worker process management
3. `collector_worker_impl.py` (5.5KB) - Worker implementation
4. `generate_adversarial_corpus.py` (1.5KB) - Corpus file generator
5. `profile_collectors.py` (9.9KB) - Collector performance profiling
6. `run_adversarial.py` (3.6KB) - Adversarial test runner

**Reusability**: ✅ **MEDIUM** - Good profiling/benchmarking foundation. Step 9 needs 3 additional tools (performance regression checker, diff visualizer, coverage breakdown).

---

### ✅ Existing Policies (4 files)

**Location**: `skeleton/policies/`

1. `EXEC_ALLOW_RAW_HTML_POLICY.md` (11.8KB) - Raw HTML handling policy
2. `EXEC_COLLECTOR_ALLOWLIST_POLICY.md` (9.5KB) - Collector allowlist policy
3. `EXEC_PLATFORM_SUPPORT_POLICY.md` (13.9KB) - Platform support policy (Windows/Linux)
4. `EXEC_TEMPLATE_SSTI_PREVENTION_POLICY.md` (12.8KB) - SSTI prevention policy

**Reusability**: ✅ **HIGH** - Use as evidence for Step 10 security gap documentation. These document Phase-8 security decisions.

---

### ✅ Existing Workflows (2 files)

**Location**: `skeleton/.github/workflows/`

1. **adversarial.yml** (10.3KB) - Comprehensive adversarial testing workflow
   - PR fast gate (smoke tests <2 min)
   - Nightly full suite (all corpora)
   - Template injection tests
   - HTML/XSS tests
   - URL normalization parity tests
   - Matrix: multiple corpora, performance profiling

2. **pr-security-gate.yml** (7.5KB) - Security gate for PRs
   - Blocks PRs with security regressions
   - Enforces adversarial corpus passing

3. **README.md** (9.1KB) - Workflow documentation

**Reusability**: ✅ **HIGH** - Step 9 can integrate these into unified `skeleton_tests.yml` workflow.

---

### ⚠️ Existing Adversarial Corpora (12 files)

**Location**: `performance/adversarial_corpora/` (parent directory, not skeleton-specific)

**Existing Corpora** (maps to DOXSTRUX_REFACTOR requirements):
1. `adversarial_deep_nesting.json` → **nested_blockquotes** ✅
2. `adversarial_html_xss.json` → **html_injection** ✅
3. `adversarial_encoded_urls.json` → **malicious_uris** (partial) ⚠️
4. `adversarial_regex_pathological.json` → **redos_patterns** ✅
5. `adversarial_large.json` → **huge_code_lines** (partial) ⚠️
6. `adversarial_template_injection.json` - SSTI corpus
7. `adversarial_attrget.json` - Token method injection corpus
8. `adversarial_malformed_maps.json` - Malformed token.map corpus
9. `adversarial_encoded_urls_raw.json` - Raw URL encoding corpus
10. `adversarial_combined.json` - Combined multi-attack corpus
11. `fast_smoke.json` - Quick smoke test corpus
12. `manifest.json` - Corpus manifest

**Format**: ⚠️ **Token-based** (not markdown+expected_outcome as DOXSTRUX_REFACTOR expects)

**Missing Corpora** (5 required by DOXSTRUX_REFACTOR):
- ❌ `oversized_tables.json` (1000+ rows/100+ cols)
- ❌ `huge_lists.json` (10K items, 50+ nesting levels)
- ❌ `bidi_attacks.json` (BiDi control characters)
- ❌ `unicode_exploits.json` (NUL bytes, overlong UTF-8, surrogates)
- ⚠️ `malicious_uris.json` (complete with javascript:, data:, file: schemes)

**Reusability**: ⚠️ **MEDIUM** - Existing corpora are valuable but:
1. Format conversion needed (token-based → markdown+expected_outcome)
2. 5 corpus types missing
3. Step 10 needs to create/convert corpora

---

### 📊 Effort Savings Summary

| Component | Original Estimate | Existing | Remaining Work | Savings |
|-----------|-------------------|----------|----------------|---------|
| Unit Tests (Step 7) | 3-4 days (38 tests) | 23 tests ✅ | 15 tests | **~50%** |
| Adversarial Corpora (Step 10) | 2 days (9 files) | 10 files ✅ | 5 files + format | **~40%** |
| CI Workflows (Step 9) | 1 day | 2 workflows ✅ | Merge + 3 gates | **~30%** |
| Tools (Step 9) | 0.5 days | 6 tools ✅ | 3 tools | **0%** (different tools) |
| **Total Savings** | **6.5-7.5 days** | **41 files done** | **~3-4 days** | **~45%** |

**Revised Timeline**: 16-26 days → **13-20 days** (3-6 day savings from existing work)

---

## Phase A: Core Infrastructure (Steps 1-3)
**Duration**: 6-10 days
**Priority**: P0 - CRITICAL
**Risk**: HIGH - Architectural changes

---

### Step 1: Implement Complete Index Building

**Goal**: Populate ALL TokenWarehouse indices in single pass

**Current State** (skeleton/utils/token_warehouse.py):
```python
def _build_indices(self):
    # ❌ Only partially populates by_type
    # ❌ pairs, parents, sections, lines never populated
    for idx, tok in enumerate(self.tokens):
        self.by_type[tok.type].append(idx)
```

**Target State** (Phase-8 spec with enhancements):
```python
def __init__(self, tokens, tree, text=None):
    # ... existing init code ...

    # Normalize content before indexing (CRITICAL for correct line offsets)
    if text:
        import unicodedata
        # Unicode NFC normalization (composed form)
        text = unicodedata.normalize('NFC', text)
        # CRLF → LF normalization
        text = text.replace('\r\n', '\n')
        self.text = text
        self.lines = text.splitlines(keepends=True)

    # Initialize ALL indices
    self.by_type = defaultdict(list)
    self.pairs = {}  # open_idx → close_idx
    self.pairs_rev = {}  # close_idx → open_idx (NEW: bidirectional)
    self.parents = {}  # token_idx → parent_idx
    self.children = defaultdict(list)  # parent_idx → [child_idx...] (NEW)
    self.sections = []
    self._line_starts = []

    self._build_indices()

def _build_indices(self):
    """Build ALL indices in single pass: by_type, pairs, parents, children, sections, lines"""
    stack = []  # Track nesting for pairs/parents
    current_section = None
    section_stack = []

    for idx, tok in enumerate(self.tokens):
        # 1. Populate by_type
        self.by_type[tok.type].append(idx)

        # 2. Build pairs (bidirectional: open ↔ close)
        if tok.nesting == 1:  # Opening token
            stack.append(idx)
        elif tok.nesting == -1:  # Closing token
            if stack:
                open_idx = stack.pop()
                self.pairs[open_idx] = idx  # forward
                self.pairs_rev[idx] = open_idx  # reverse (NEW)
                self.parents[idx] = open_idx

        # 3. Track parents (all tokens → their container)
        if stack:
            parent_idx = stack[-1]
            self.parents[idx] = parent_idx
            # 3a. Build children index (NEW)
            self.children[parent_idx].append(idx)

        # 4. Build sections (heading boundaries)
        if tok.type == "heading_open":
            level = int(tok.tag[1])  # h1 → 1, h2 → 2, etc.
            start_line = tok.map[0] if tok.map else None

            # Close previous sections at same/higher level
            while section_stack and section_stack[-1][3] >= level:
                sect = section_stack.pop()
                # Update end_line for closed section
                end_line = tok.map[0] - 1 if tok.map else None
                self.sections[sect[4]] = (sect[0], end_line, sect[2], sect[3], sect[5])

            # Open new section
            section_idx = len(self.sections)
            title = ""  # Will be filled from next inline token
            self.sections.append((start_line, None, idx, level, section_idx, title))
            section_stack.append((start_line, None, idx, level, section_idx, title))

        # 5. Fill section titles
        if tok.type == "inline" and section_stack:
            last_sect = section_stack[-1]
            title = tok.content
            self.sections[last_sect[4]] = (last_sect[0], last_sect[1], last_sect[2], last_sect[3], title)
            section_stack[-1] = (last_sect[0], last_sect[1], last_sect[2], last_sect[3], last_sect[4], title)

    # 6. Close remaining open sections at end of document
    for sect in section_stack:
        end_line = self.line_count - 1
        self.sections[sect[4]] = (sect[0], end_line, sect[2], sect[3], sect[5])

    # 7. Build line start offsets for text slicing
    if self.lines:
        offset = 0
        self._line_starts = [0]
        for line in self.lines[:-1]:  # All but last
            offset += len(line)
            self._line_starts.append(offset)
```

**Files to Modify**:
- `skeleton/doxstrux/markdown/utils/token_warehouse.py` (lines 91-120)

**Implementation Subtasks**:
- [ ] 1.1: Add stack-based pair tracking (open/close tokens)
- [ ] 1.2: Add parent tracking (all tokens → container)
- [ ] 1.3: Add section boundary detection (heading levels)
- [ ] 1.4: Add section title extraction (inline content)
- [ ] 1.5: Add line offset calculation (_line_starts)
- [ ] 1.6: Handle edge cases (unclosed sections, missing maps)
- [ ] 1.7: **Build bidirectional pairs** - Both `pairs[open]=close` AND `pairs_rev[close]=open` for reverse lookups
- [ ] 1.8: **Build children index** - `children[parent_idx] = [child_idx...]` for nested table/list logic
- [ ] 1.9: **Unicode normalization (NFC)** - Normalize content before indexing to handle composed/decomposed chars
- [ ] 1.10: **CRLF normalization** - Convert `\r\n → \n` before building line offsets
- [ ] 1.11: **Tab handling policy** - Preserve tabs as-is (don't expand) unless collectors explicitly need column widths (tables)

**Acceptance Criteria**:
- [ ] `by_type` contains ALL token types from document
- [ ] `pairs` maps all opening tokens to corresponding closing tokens
- [ ] **`pairs_rev` maps all closing tokens back to opening tokens** (bidirectional)
- [ ] **`children` maps parent tokens to list of child token indices**
- [ ] `parents` maps every token to its containing token
- [ ] `sections` contains tuples: (start_line, end_line, token_idx, level, title)
- [ ] `_line_starts` contains byte offsets for each line
- [ ] **Content is Unicode NFC normalized before indexing**
- [ ] **CRLF sequences normalized to LF before line offset calculation**
- [ ] Single pass over tokens (no redundant iterations)

**Testing**:
```bash
# Unit test
.venv/bin/python -m pytest tests/test_token_warehouse_indices.py -v

# Expected: Test passes verifying all 5 indices populated correctly
```

**Test File** (`tests/test_token_warehouse_indices.py`):
```python
def test_by_type_populated():
    content = "# Hello\n\nWorld [link](url)"
    wh = create_warehouse(content)
    assert "heading_open" in wh.by_type
    assert "paragraph_open" in wh.by_type
    assert "link_open" in wh.by_type
    assert len(wh.by_type["heading_open"]) > 0

def test_pairs_populated():
    content = "# Hello"
    wh = create_warehouse(content)
    # Find heading_open index
    open_idx = wh.by_type["heading_open"][0]
    # Should have corresponding heading_close
    assert open_idx in wh.pairs
    close_idx = wh.pairs[open_idx]
    assert wh.tokens[close_idx].type == "heading_close"

def test_sections_populated():
    content = "# Title\n\nContent\n\n## Subtitle"
    wh = create_warehouse(content)
    assert len(wh.sections) == 2  # 2 headings
    sect0 = wh.sections[0]
    assert sect0[3] == 1  # Level 1
    assert sect0[4] == "Title"  # Title extracted

def test_pairs_bidirectional():
    """Test bidirectional pairs (NEW)"""
    content = "# Hello"
    wh = create_warehouse(content)
    open_idx = wh.by_type["heading_open"][0]
    close_idx = wh.pairs[open_idx]

    # Test reverse lookup
    assert close_idx in wh.pairs_rev
    assert wh.pairs_rev[close_idx] == open_idx

def test_children_index():
    """Test children index for nested structures (NEW)"""
    content = "- Item 1\n  - Nested item"
    wh = create_warehouse(content)

    # Find parent list
    list_open_idx = wh.by_type["bullet_list_open"][0]

    # Should have children
    assert list_open_idx in wh.children
    assert len(wh.children[list_open_idx]) > 0

def test_unicode_normalization():
    """Test Unicode NFC normalization (NEW)"""
    # Composed vs decomposed é
    content_composed = "café"  # NFC (single code point)
    content_decomposed = "café"  # NFD (e + combining accent)

    wh1 = create_warehouse(content_composed)
    wh2 = create_warehouse(content_decomposed)

    # Both should normalize to same form
    assert wh1.text == wh2.text

def test_crlf_normalization():
    """Test CRLF normalization (NEW)"""
    content_crlf = "Line 1\r\nLine 2\r\n"
    content_lf = "Line 1\nLine 2\n"

    wh1 = create_warehouse(content_crlf)
    wh2 = create_warehouse(content_lf)

    # Both should have identical line offsets
    assert wh1._line_starts == wh2._line_starts
    assert wh1.text == wh2.text  # CRLF converted to LF
```

**Estimated Effort**: 2-3 days
**Risk**: MEDIUM (complex logic, edge cases)

---

### Step 2: Implement section_of() with Binary Search

**Goal**: Add O(log N) line → section lookup

**Current State**:
- No `section_of()` method exists

**Target State**:
```python
def section_of(self, line: int) -> Optional[Tuple[int, int, int, int, str]]:
    """Find section containing given line number in O(log N) time.

    Args:
        line: Line number (0-indexed)

    Returns:
        Section tuple (start_line, end_line, token_idx, level, title) or None
    """
    if not self.sections:
        return None

    # Binary search for section containing line
    import bisect

    # Build searchable list of (start_line, section_index)
    if not hasattr(self, '_section_starts_sorted'):
        self._section_starts_sorted = [(s[0], i) for i, s in enumerate(self.sections)]
        self._section_starts_sorted.sort(key=lambda x: x[0])

    # Find rightmost section starting at or before line
    idx = bisect.bisect_right([s[0] for s in self._section_starts_sorted], line)
    if idx == 0:
        return None  # Line before first section

    section_idx = self._section_starts_sorted[idx - 1][1]
    section = self.sections[section_idx]

    # Verify line is within section boundaries
    if section[1] is not None and line > section[1]:
        return None  # Line after section end

    return section
```

**Files to Modify**:
- `skeleton/doxstrux/markdown/utils/token_warehouse.py` (add new method after `_build_indices`)

**Implementation Subtasks**:
- [ ] 2.1: Add `section_of()` method signature
- [ ] 2.2: Build sorted section starts on first call (lazy init)
- [ ] 2.3: Implement bisect_right for binary search
- [ ] 2.4: Validate line is within section boundaries
- [ ] 2.5: Handle edge cases (no sections, line out of range)

**Acceptance Criteria**:
- [ ] `section_of(line)` returns correct section in O(log N) time
- [ ] Returns None for lines outside any section
- [ ] Handles edge cases (empty doc, no headings, line 0)
- [ ] Performance: <1ms for 10K line document

**Testing**:
```python
def test_section_of_binary_search():
    content = "# Intro\n\nLine 2\n\n## Section 2\n\nLine 5"
    wh = create_warehouse(content)

    # Line 0: in "Intro" section
    sect = wh.section_of(0)
    assert sect[4] == "Intro"

    # Line 2: still in "Intro"
    sect = wh.section_of(2)
    assert sect[4] == "Intro"

    # Line 5: in "Section 2"
    sect = wh.section_of(5)
    assert sect[4] == "Section 2"

def test_section_of_performance():
    # 10K line document with 100 sections
    content = "\n\n".join([f"# Section {i}\n\nContent" for i in range(100)])
    wh = create_warehouse(content)

    import time
    start = time.time()
    for line in range(0, 10000, 100):
        wh.section_of(line)
    elapsed = time.time() - start
    assert elapsed < 0.001  # <1ms for 100 lookups
```

**Estimated Effort**: 1 day
**Risk**: LOW (well-defined algorithm)

---

### Step 3: Implement Routing Table & Single-Pass Dispatch

**Goal**: Change from O(N×M) to O(N+M) dispatch complexity

**Current State** (skeleton):
```python
def dispatch_all(self):
    """❌ O(N×M) - Each collector iterates all tokens"""
    ctx = DispatchContext()
    for collector in self._collectors:
        for idx, token in enumerate(self.tokens):
            if collector.should_process(token, ctx, self):
                collector.on_token(idx, token, ctx, self)
```

**Target State** (Phase-8):
```python
def register_collector(self, collector: Collector) -> None:
    """Register collector and build routing table entry."""
    self._collectors.append(collector)

    # Build routing: token_type → list of interested collectors
    for token_type in collector.interest.types:
        if token_type not in self._routing:
            self._routing[token_type] = []
        self._routing[token_type].append(collector)

    # Also support tag-based routing
    for tag in collector.interest.tags:
        tag_key = f"tag:{tag}"
        if tag_key not in self._routing:
            self._routing[tag_key] = []
        self._routing[tag_key].append(collector)

def dispatch_all(self):
    """✅ O(N+M) - Single pass with routing table lookup."""
    # Guard against reentrancy
    if self._dispatching:
        raise RuntimeError("Warehouse already dispatching (reentrancy not allowed)")

    self._dispatching = True
    try:
        ctx = DispatchContext()

        # Single pass over all tokens
        for idx, token in enumerate(self.tokens):
            # O(1) lookup of interested collectors
            collectors = self._routing.get(token.type, [])

            # Also check tag-based routing if token has tag
            if hasattr(token, 'tag') and token.tag:
                tag_collectors = self._routing.get(f"tag:{token.tag}", [])
                collectors = list(set(collectors + tag_collectors))  # Deduplicate

            # Dispatch to all interested collectors
            for collector in collectors:
                # Check ignore_inside constraint
                if collector.interest.ignore_inside:
                    if any(t in ctx.stack for t in collector.interest.ignore_inside):
                        continue

                # Check predicate filter if provided
                if collector.interest.predicate:
                    if not collector.interest.predicate(token, ctx, self):
                        continue

                # Check collector's should_process
                if collector.should_process(token, ctx, self):
                    # Apply timeout protection
                    try:
                        with self._collector_timeout(self.COLLECTOR_TIMEOUT_SECONDS):
                            collector.on_token(idx, token, ctx, self)
                    except TimeoutError:
                        self._collector_errors.append((collector.name, "timeout", idx))
                        if RAISE_ON_COLLECTOR_ERROR:
                            raise
                    except Exception as e:
                        self._collector_errors.append((collector.name, str(e), idx))
                        if RAISE_ON_COLLECTOR_ERROR:
                            raise

            # Update context for nesting tracking
            if token.nesting == 1:  # Open
                ctx.stack.append(token.type)
            elif token.nesting == -1:  # Close
                if ctx.stack and ctx.stack[-1] == token.type.replace("_close", "_open"):
                    ctx.stack.pop()

            # Update line tracking
            if hasattr(token, 'map') and token.map:
                ctx.line = token.map[0]

    finally:
        self._dispatching = False
```

**Platform-Specific Timeout Implementation** (NEW):
```python
import sys
import platform
from contextlib import contextmanager

# Platform detection
IS_UNIX = platform.system() in ('Linux', 'Darwin')  # Linux or macOS
IS_WINDOWS = platform.system() == 'Windows'

class TokenWarehouse:
    COLLECTOR_TIMEOUT_SECONDS = 5

    def __init__(self, tokens, tree, text=None):
        # ... existing init ...
        self._timeout_available = IS_UNIX  # SIGALRM only on Unix

    @contextmanager
    def _collector_timeout(self, seconds):
        """Cross-platform timeout protection for collectors."""
        if IS_UNIX:
            # Use SIGALRM on Unix (most reliable)
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Collector timeout after {seconds}s")

            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)  # Cancel alarm
                signal.signal(signal.SIGALRM, old_handler)

        elif IS_WINDOWS:
            # Use threading.Timer on Windows (fallback)
            import threading

            timeout_event = threading.Event()
            timed_out = [False]

            def timeout_trigger():
                timed_out[0] = True
                # Note: Can't raise exception in different thread
                # Collector must check timeout_event periodically (limitation)

            timer = threading.Timer(seconds, timeout_trigger)
            timer.start()
            try:
                yield
                if timed_out[0]:
                    raise TimeoutError(f"Collector timeout after {seconds}s")
            finally:
                timer.cancel()

        else:
            # No timeout support on unknown platforms - just yield
            yield
```

**Windows Limitation Note**:
Thread-based timeout on Windows cannot forcefully interrupt running code (unlike SIGALRM). Collectors on Windows must be well-behaved and complete quickly. This is acceptable because:
1. Most collectors complete in <100ms
2. Infinite loops in collectors are bugs, not expected behavior
3. Windows deployments are typically dev/test, not production (Linux)

For production Windows deployment (if needed), consider:
- Adding collector runtime checks (poll timeout_event)
- Using multiprocessing instead of threading (can kill processes)

**Files to Modify**:
- `skeleton/doxstrux/markdown/utils/token_warehouse.py` (lines 1-50 for timeout code, 200-250 for dispatch)

**Implementation Subtasks**:
- [ ] 3.1: Modify `register_collector()` to build routing table
- [ ] 3.2: Add tag-based routing support
- [ ] 3.3: Rewrite `dispatch_all()` with single token pass
- [ ] 3.4: Add O(1) routing table lookups
- [ ] 3.5: Implement ignore_inside constraint checking
- [ ] 3.6: Add context tracking (stack, line)
- [ ] 3.7: Keep timeout protection and error handling
- [ ] 3.8: **Add platform detection** - Check for Unix (SIGALRM available) vs Windows
- [ ] 3.9: **Implement thread-based timeout fallback** - For Windows compatibility where SIGALRM unavailable
- [ ] 3.10: **Test matrix coverage** - Ensure tests pass on both Linux and Windows platforms

**Acceptance Criteria**:
- [ ] Single pass over tokens (exactly N iterations)
- [ ] Routing table lookup is O(1) per token
- [ ] Total complexity: O(N + M) where N=tokens, M=collectors
- [ ] **Timeout protection works on Linux (SIGALRM) and Windows (thread timer)**
- [ ] **Platform detection correctly identifies Unix vs Windows**
- [ ] Reentrancy guard functional
- [ ] ignore_inside constraints work correctly

**Testing**:
```python
def test_dispatch_single_pass():
    """Verify dispatch only iterates tokens once."""
    content = "# Hello\n\n[Link](url)"
    wh = create_warehouse(content)

    # Mock collector that tracks calls
    call_count = {"on_token": 0, "tokens_seen": set()}

    class TrackingCollector:
        name = "tracker"
        interest = Interest(types={"heading_open", "link_open"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            call_count["on_token"] += 1
            call_count["tokens_seen"].add(idx)

        def finalize(self, wh):
            return {}

    wh.register_collector(TrackingCollector())
    wh.dispatch_all()

    # Should only see heading_open and link_open (2 tokens)
    assert call_count["on_token"] == 2
    assert len(call_count["tokens_seen"]) == 2

def test_dispatch_performance():
    """Verify O(N+M) complexity."""
    # Create document with 1000 tokens
    content = "\n\n".join([f"# Section {i}" for i in range(100)])
    wh = create_warehouse(content)

    # Register 10 collectors
    collectors = [create_simple_collector(f"col{i}") for i in range(10)]
    for col in collectors:
        wh.register_collector(col)

    # Measure dispatch time
    import time
    start = time.time()
    wh.dispatch_all()
    elapsed = time.time() - start

    # Should be fast (O(N+M) not O(N×M))
    assert elapsed < 0.1  # <100ms for 1000 tokens × 10 collectors
```

**Estimated Effort**: 3-4 days
**Risk**: HIGH (major architectural change, affects all collectors)

---

## Phase B: API Migration (Steps 4-6)
**Duration**: 5-8 days
**Priority**: P0 - CRITICAL
**Risk**: MEDIUM - Compatibility concerns

---

### Step 4: Refactor Collectors to Use Warehouse Indices

**Goal**: Change collectors from iteration to index queries

**Current State** (collectors iterate tokens):
```python
class LinksCollector:
    def on_token(self, idx, token, ctx, wh):
        # ❌ Collectors must iterate to find related tokens
        for i, tok in enumerate(wh.tokens):
            if tok.type == "link_close":
                # Process...
```

**Target State** (collectors query indices):
```python
class LinksCollector:
    def on_token(self, idx, token, ctx, wh):
        # ✅ Use O(1) index lookups
        if token.type == "link_open":
            # Get corresponding close via pairs index
            close_idx = wh.pairs.get(idx)
            if close_idx:
                close_token = wh.tokens[close_idx]
                # Extract link text from inline tokens between open/close
                inline_indices = wh.by_type.get("inline", [])
                text_tokens = [i for i in inline_indices if idx < i < close_idx]
                link_text = " ".join(wh.tokens[i].content for i in text_tokens)

                # Extract URL from open token attributes
                url = token.attrGet("href") if hasattr(token, 'attrGet') else None

                self.links.append({"url": url, "text": link_text, "line": ctx.line})
```

**Files to Modify**:
All collector modules in `skeleton/doxstrux/markdown/collectors_phase8/`:
- links.py
- images.py
- sections.py
- paragraphs.py
- lists.py
- tables.py
- codeblocks.py
- footnotes.py
- html.py
- math.py
- headings.py
- tasklists.py

**Implementation Subtasks**:
- [ ] 4.1: Audit all collectors for iteration patterns
- [ ] 4.2: Replace iteration with `wh.by_type[...]` queries
- [ ] 4.3: Use `wh.pairs[idx]` for matching open/close
- [ ] 4.4: Use `wh.parents[idx]` for container lookup
- [ ] 4.5: Add helper methods to warehouse for common queries
- [ ] 4.6: Update collector tests

**Helper Methods to Add**:
```python
# Add to TokenWarehouse class
def tokens_between(self, start_idx: int, end_idx: int, type_filter: Optional[str] = None) -> List[int]:
    """Get token indices between start and end."""
    if type_filter:
        return [i for i in self.by_type.get(type_filter, []) if start_idx < i < end_idx]
    return list(range(start_idx + 1, end_idx))

def text_between(self, start_idx: int, end_idx: int) -> str:
    """Extract text content between two token indices."""
    inline_indices = self.tokens_between(start_idx, end_idx, "inline")
    return " ".join(self.tokens[i].content for i in inline_indices if hasattr(self.tokens[i], 'content'))

def find_close(self, open_idx: int) -> Optional[int]:
    """Find closing token for opening token (alias for pairs lookup)."""
    return self.pairs.get(open_idx)

def find_parent(self, token_idx: int) -> Optional[int]:
    """Find parent container token (alias for parents lookup)."""
    return self.parents.get(token_idx)
```

**Acceptance Criteria**:
- [ ] No collectors iterate `wh.tokens` directly
- [ ] All collectors use index queries (by_type, pairs, parents)
- [ ] Helper methods simplify common patterns
- [ ] Collector tests pass
- [ ] Performance: Collector execution time reduced

**Testing**:
```python
def test_collectors_use_indices():
    """Verify collectors query indices not iterate."""
    content = "# Title\n\n[Link](url)\n\n![Image](img.png)"
    wh = create_warehouse(content)

    # Patch tokens to detect iteration
    iteration_detected = {"flag": False}
    original_iter = wh.tokens.__iter__

    def detect_iteration():
        iteration_detected["flag"] = True
        return original_iter()

    wh.tokens.__iter__ = detect_iteration

    # Register collectors and dispatch
    wh.register_collector(LinksCollector())
    wh.register_collector(ImagesCollector())
    wh.dispatch_all()

    # Should NOT have iterated tokens
    assert not iteration_detected["flag"], "Collectors should use indices not iterate"
```

**Estimated Effort**: 2-3 days
**Risk**: MEDIUM (affects all collectors, potential bugs)

---

### Step 5: Create Compatibility Shim for src API

**Goal**: Make skeleton drop-in compatible with src/doxstrux API

**Current State**:
- No standalone parser class
- Only adapter functions for specific extractors
- Different return format

**Target State**:
```python
# skeleton/doxstrux/markdown/parser.py (NEW FILE)
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from .utils.token_warehouse import TokenWarehouse
from .collectors_phase8 import *

class MarkdownParserCore:
    """Drop-in replacement for src/doxstrux/markdown_parser_core.MarkdownParserCore

    API-compatible wrapper around TokenWarehouse + collectors.
    """

    def __init__(self, content: str, config: dict | None = None, security_profile: str | None = None):
        self.original_content = content
        self.config = config or {}
        self.security_profile = security_profile or "moderate"

        # Initialize markdown-it parser (same as src)
        preset = self.config.get("preset", "commonmark")
        self.md = MarkdownIt(preset, options_update={"html": True})

        # Parse and create tree
        self.tokens = self.md.parse(content)
        self.tree = SyntaxTreeNode(self.tokens)

        # Create warehouse
        self.warehouse = TokenWarehouse(self.tokens, self.tree, content)

        # Register all collectors
        self._register_collectors()

        # Cache for parse results
        self._parse_cache = None

    def _register_collectors(self):
        """Register all Phase-8 collectors."""
        from .collectors_phase8 import (
            SectionsCollector, HeadingsCollector, ParagraphsCollector,
            ListsCollector, TasklistsCollector, CodeblocksCollector,
            TablesCollector, LinksCollector, ImagesCollector,
            FootnotesCollector, HtmlCollector, MathCollector
        )

        collectors = [
            SectionsCollector(),
            HeadingsCollector(),
            ParagraphsCollector(),
            ListsCollector(),
            TasklistsCollector(),
            CodeblocksCollector(),
            TablesCollector(),
            LinksCollector(),
            ImagesCollector(),
            FootnotesCollector(),
            HtmlCollector(),
            MathCollector(),
        ]

        for collector in collectors:
            self.warehouse.register_collector(collector)

    def parse(self) -> dict:
        """Parse and return results in src-compatible format.

        Returns:
            dict with keys: sections, headings, paragraphs, lists, links, images, etc.
        """
        if self._parse_cache is not None:
            return self._parse_cache

        # Dispatch all collectors
        self.warehouse.dispatch_all()

        # Finalize and collect results
        results = self.warehouse.finalize_all()

        # Map to src API format
        self._parse_cache = {
            "metadata": self.extract_metadata(),
            "sections": results.get("sections", []),
            "headings": results.get("headings", []),
            "paragraphs": results.get("paragraphs", []),
            "lists": results.get("lists", []),
            "task_lists": results.get("tasklists", []),
            "code_blocks": results.get("codeblocks", []),
            "tables": results.get("tables", []),
            "links": results.get("links", []),
            "images": results.get("images", []),
            "footnotes": results.get("footnotes", []),
            "html_blocks": results.get("html", []),
            "math": results.get("math", []),
        }

        return self._parse_cache

    def extract_metadata(self) -> dict:
        """Extract document metadata (frontmatter, etc.)."""
        # Check if front_matter plugin populated env
        if hasattr(self.md, 'env') and 'front_matter' in self.md.env:
            return self.md.env['front_matter']
        return {}

    # Compatibility methods matching src API
    def extract_sections(self) -> list:
        return self.parse()["sections"]

    def extract_headings(self) -> list:
        return self.parse()["headings"]

    def extract_paragraphs(self) -> list:
        return self.parse()["paragraphs"]

    def extract_lists(self) -> list:
        return self.parse()["lists"]

    def extract_links(self) -> list:
        return self.parse()["links"]

    def extract_images(self) -> list:
        return self.parse()["images"]

    # ... (other extract_* methods)

    @classmethod
    def validate_content(cls, content: str, security_profile: str = "moderate") -> dict:
        """Quick validation without full parsing - src API compatibility."""
        # Delegate to TokenWarehouse limits check
        try:
            from .utils.token_warehouse import MAX_BYTES, MAX_TOKENS
            if len(content) > MAX_BYTES:
                return {"valid": False, "issues": [f"Content exceeds {MAX_BYTES} bytes"]}
            return {"valid": True, "issues": []}
        except Exception as e:
            return {"valid": False, "issues": [str(e)]}
```

**Files to Create**:
- `skeleton/doxstrux/markdown/parser.py` (NEW - 300-400 lines)
- `skeleton/doxstrux/__init__.py` (UPDATE - export MarkdownParserCore)

**Implementation Subtasks**:
- [ ] 5.1: Create parser.py with MarkdownParserCore class
- [ ] 5.2: Implement `__init__()` matching src signature
- [ ] 5.3: Implement `parse()` returning src-compatible dict
- [ ] 5.4: Add all `extract_*()` methods for API compatibility
- [ ] 5.5: Add `validate_content()` class method
- [ ] 5.6: Export from __init__.py

**Acceptance Criteria**:
- [ ] `from skeleton.doxstrux import MarkdownParserCore` works
- [ ] `parser = MarkdownParserCore(content); result = parser.parse()` works
- [ ] Return dict structure matches src exactly
- [ ] All `extract_*()` methods functional
- [ ] Can replace `from src.doxstrux import MarkdownParserCore` with `from skeleton.doxstrux import MarkdownParserCore` with zero code changes

**Testing**:
```python
def test_api_compatibility():
    """Verify skeleton API matches src exactly."""
    from skeleton.doxstrux import MarkdownParserCore

    content = "# Title\n\n[Link](url)"

    # Should match src API
    parser = MarkdownParserCore(content, security_profile="moderate")
    result = parser.parse()

    # Check structure
    assert "sections" in result
    assert "headings" in result
    assert "links" in result
    assert isinstance(result["sections"], list)

    # Check extract methods
    sections = parser.extract_sections()
    assert isinstance(sections, list)

    links = parser.extract_links()
    assert len(links) == 1
    assert links[0]["url"] == "url"

def test_drop_in_replacement():
    """Test that skeleton can replace src with no changes."""
    content = "# Hello\n\nWorld"

    # This should work identically to src
    from skeleton.doxstrux import MarkdownParserCore
    parser = MarkdownParserCore(content)
    result = parser.parse()

    # Verify baseline parity would pass
    assert "sections" in result
    assert len(result["sections"]) > 0
```

**Estimated Effort**: 2-3 days
**Risk**: LOW (wrapper pattern, well-defined interface)

---

### Step 6: Add lines Property for Text Slicing

**Goal**: Provide efficient text extraction by line ranges

**Current State**:
- `self.lines` exists (list of line strings)
- No line offset mapping

**Target State**:
```python
# Add to TokenWarehouse.__init__
def __init__(self, tokens, tree, text=None):
    # ... existing code ...

    # Build line start offsets for O(1) slicing
    self._line_starts = []
    if self.lines:
        offset = 0
        self._line_starts = [0]
        for line in self.lines[:-1]:
            offset += len(line)
            self._line_starts.append(offset)

def get_line_range(self, start_line: int, end_line: int) -> str:
    """Extract text for line range in O(1) time.

    Args:
        start_line: Starting line (0-indexed)
        end_line: Ending line (inclusive, 0-indexed)

    Returns:
        Text content for line range
    """
    if not self.lines or not self._line_starts:
        return ""

    if start_line < 0 or end_line >= len(self.lines):
        return ""

    # Use precomputed line starts for efficient slicing
    start_offset = self._line_starts[start_line]
    end_offset = self._line_starts[end_line] + len(self.lines[end_line])

    # Reconstruct from lines
    return "".join(self.lines[start_line:end_line + 1])

def get_token_text(self, token_idx: int) -> str:
    """Extract text for a token's line range.

    Args:
        token_idx: Token index

    Returns:
        Text content for token's lines
    """
    token = self.tokens[token_idx]
    if not hasattr(token, 'map') or not token.map:
        return ""

    start_line, end_line = token.map
    return self.get_line_range(start_line, end_line - 1)  # map[1] is exclusive
```

**Files to Modify**:
- `skeleton/doxstrux/markdown/utils/token_warehouse.py` (add methods)

**Implementation Subtasks**:
- [ ] 6.1: Build `_line_starts` in `__init__` (already in Step 1)
- [ ] 6.2: Add `get_line_range()` method
- [ ] 6.3: Add `get_token_text()` method
- [ ] 6.4: Add `text_between()` method (from Step 4)

**Acceptance Criteria**:
- [ ] `get_line_range(start, end)` returns correct text
- [ ] `get_token_text(idx)` extracts token content
- [ ] O(1) performance (uses precomputed offsets)
- [ ] Handles edge cases (out of range, missing maps)

**Testing**:
```python
def test_line_range_extraction():
    content = "Line 0\nLine 1\nLine 2\nLine 3"
    wh = create_warehouse(content)

    # Extract single line
    text = wh.get_line_range(0, 0)
    assert text == "Line 0\n"

    # Extract range
    text = wh.get_line_range(1, 2)
    assert text == "Line 1\nLine 2\n"

def test_token_text_extraction():
    content = "# Heading\n\nParagraph text"
    wh = create_warehouse(content)

    # Find heading_open token
    heading_idx = wh.by_type["heading_open"][0]
    text = wh.get_token_text(heading_idx)
    assert "Heading" in text
```

**Estimated Effort**: 1 day
**Risk**: LOW (straightforward implementation)

---

## Performance & Memory Optimization

**When to apply**: After Steps 1-6 complete, before or during Phase C validation

This section provides practical optimization guidance to ensure skeleton achieves production-grade performance and memory characteristics.

### Memory Optimization Techniques

#### 1. Use `__slots__` on Small Classes
**Problem**: Python's default `__dict__` per instance adds ~56 bytes overhead
**Solution**: Define `__slots__` for frequently-created small objects

```python
# Before (high memory)
class DispatchContext:
    def __init__(self):
        self.stack = []
        self.line = 0
        self.data = {}

# After (optimized)
class DispatchContext:
    __slots__ = ('stack', 'line', 'data')

    def __init__(self):
        self.stack = []
        self.line = 0
        self.data = {}
```

**Apply to**:
- `DispatchContext` (created once per parse)
- Any collector internal state classes
- Entry/record classes if used

**Expected savings**: 40-50% memory reduction on small objects

---

#### 2. Store Indices (ints) Not Token Objects
**Problem**: Storing token references prevents garbage collection and increases memory
**Solution**: Store integer indices, lookup tokens on demand

```python
# Before (stores references)
self.heading_tokens = []
for tok in tokens:
    if tok.type == "heading_open":
        self.heading_tokens.append(tok)  # Reference kept

# After (stores indices)
self.heading_indices = []
for idx, tok in enumerate(tokens):
    if tok.type == "heading_open":
        self.heading_indices.append(idx)  # Just int

# Lookup on demand
heading_tok = self.tokens[self.heading_indices[0]]
```

**Apply to**:
- ALL indices in TokenWarehouse (`by_type`, `pairs`, `parents`, etc.)
- Collector internal tracking

**Expected savings**: 60-70% memory reduction for large documents

---

#### 3. Lazy-Build Rarely Used Structures
**Problem**: Building all indices upfront wastes memory for unused features
**Solution**: Build on first access with caching

```python
class TokenWarehouse:
    def __init__(self, tokens, tree, text=None):
        # ... core indices always built ...
        self._children_cache = None  # Lazy

    @property
    def children(self):
        """Build children index on first access (lazy)"""
        if self._children_cache is None:
            self._children_cache = defaultdict(list)
            for idx, parent_idx in self.parents.items():
                self._children_cache[parent_idx].append(idx)
        return self._children_cache
```

**Apply to**:
- `children` index (not all collectors need it)
- Any collector-specific caches

**Trade-off**: Slight CPU cost on first access, but saves memory when unused

---

### Performance Optimization Techniques

#### 4. Hot Spot: Optimize `text_between()` with Binary Search
**Problem**: Filtering `by_type['inline']` for range `[start, end]` is O(N) per call
**Solution**: Use binary search on sorted index positions

```python
def text_between(self, start_idx: int, end_idx: int) -> str:
    """Extract text content between two token indices - OPTIMIZED"""
    import bisect

    # Get all inline token indices (sorted by definition)
    inline_indices = self.by_type.get("inline", [])

    if not inline_indices:
        return ""

    # Binary search for first inline >= start_idx
    left = bisect.bisect_left(inline_indices, start_idx)
    # Binary search for last inline < end_idx
    right = bisect.bisect_left(inline_indices, end_idx)

    # Extract text from inline tokens in range
    text_parts = []
    for idx in inline_indices[left:right]:
        tok = self.tokens[idx]
        if hasattr(tok, 'content') and tok.content:
            text_parts.append(tok.content)

    return " ".join(text_parts)
```

**Impact**: O(N) → O(log N + K) where K = inlines in range
**Expected speedup**: 10-100x for large documents with many links/images

---

#### 5. Tab Handling Policy
**Problem**: Expanding tabs to spaces is expensive and rarely needed
**Solution**: Preserve tabs as-is unless collector explicitly needs column widths

```python
# DON'T expand tabs globally (expensive)
# text = text.expandtabs(4)  # ❌

# DO preserve tabs
self.text = text  # Tabs kept as \t

# Collectors that need column widths (tables) expand locally:
def extract_table_cell(self, token_idx):
    text = self.wh.get_token_text(token_idx)
    # Expand tabs only for this cell
    text = text.expandtabs(4)
    return {"text": text, "width": len(text)}
```

**Trade-off**: Simpler, faster, but table collectors must handle tabs

---

### Profiling & Measurement

#### Memory Profiling
```bash
# Profile memory usage during parse
.venv/bin/python -m memory_profiler skeleton/doxstrux/markdown/utils/token_warehouse.py

# Expected output: Memory usage by line
# Look for spikes > 10MB on small docs (indicates leak or inefficiency)
```

#### CPU Profiling
```bash
# Profile hot spots
.venv/bin/python -m cProfile -o dispatch.prof \
    -c "from skeleton.doxstrux import MarkdownParserCore; \
        p = MarkdownParserCore(open('test.md').read()); \
        p.parse()"

# Analyze
python -m pstats dispatch.prof
# Commands: sort cumtime, stats 20  (show top 20 functions)
```

**Hot spots to watch**:
- `_build_indices()` should be <5% of total time
- `dispatch_all()` should be 30-50% (it does the real work)
- `text_between()` calls should be <10% total (if higher, optimize)

---

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Parse 1MB doc** | <100ms median | Use `capture_baseline_metrics.py` |
| **Memory overhead** | ≤ src + 10% | Compare RSS before/after parse |
| **Dispatch complexity** | O(N+M) verified | Count token iterations (must be exactly N) |
| **section_of() lookup** | <1ms for 10K lines | Binary search benchmark |
| **Index build time** | <5% of parse time | cProfile analysis |

---

### When Optimizations Backfire (Anti-Patterns)

❌ **Don't prematurely optimize**:
- Get baseline parity first (Step 8)
- Profile to find real hot spots
- Only optimize if measurable impact >5%

❌ **Don't over-cache**:
- Caching every lookup wastes memory
- Only cache if access pattern is >3x repeated

❌ **Don't break API for speed**:
- Maintain src compatibility
- Optimize internals, not interfaces

---

## Phase C: Validation (Steps 7-8)
**Duration**: 5-6 days
**Priority**: P0 - CRITICAL
**Risk**: HIGH - Quality gate

---

### Step 7: Comprehensive Unit Tests

**Goal**: Ensure all components work correctly in isolation

**Existing Work**: ✅ **23 test files already exist** (see Existing Assets Inventory)

**Test Categories**:

**7.0: Leverage Existing Tests** (✅ COMPLETE - No Work Needed)

The skeleton already has 23 production-ready test files (231KB):

**Security Coverage** (11 tests):
- XSS/HTML injection protection
- SSTI (Server-Side Template Injection) prevention
- URL normalization baseline parity
- Malicious token method injection
- Frontmatter template safety

**Performance Coverage** (3 tests):
- `test_performance_scaling.py` - Parser scaling characteristics
- `test_section_lookup_performance.py` - **O(log N) section_of() already verified** ✅
- `test_fuzz_collectors.py` - Collector fuzzing

**Warehouse Coverage** (2 tests):
- `test_token_warehouse.py` - Basic functionality
- `test_token_warehouse_adversarial.py` - Adversarial inputs

**Collector Coverage** (5 tests):
- Timeout protection, subprocess isolation, resource caps
- Reentrancy guard (dispatch protection)
- Collector code quality

**Action**: ✅ Run existing tests to verify they pass:
```bash
.venv/bin/python -m pytest skeleton/tests/ -v
# Expected: All 23 test files pass
```

---

**7.1: Create Missing Index Tests** (`tests/test_indices.py` - NEW)
```python
def test_by_type_index():
    # Test all token types indexed correctly
    pass

def test_pairs_index():
    # Test all open/close pairs matched
    pass

def test_parents_index():
    # Test parent relationships correct
    pass

def test_sections_index():
    # Test section boundaries correct
    pass

def test_nested_structures():
    # Test deeply nested content
    pass
```

**7.2: Dispatch Tests** (`tests/test_dispatch.py`)
```python
def test_single_pass_dispatch():
    # Verify exactly one iteration over tokens
    pass

def test_routing_table():
    # Verify O(1) collector lookup
    pass

def test_ignore_inside_constraint():
    # Test collectors skip content inside certain tokens
    pass

def test_collector_timeout():
    # Verify timeout protection works
    pass

def test_dispatch_errors():
    # Test error handling and collection
    pass
```

**7.3: Collector Tests** (`tests/test_collectors_*.py`)
- One test file per collector
- Test index queries not iteration
- Test output format matches src
- Test edge cases (empty, malformed)

**7.4: API Compatibility Tests** (`tests/test_api_compat.py`)
```python
def test_parse_method():
    # Test parse() returns src-compatible dict
    pass

def test_extract_methods():
    # Test all extract_*() methods work
    pass

def test_validate_content():
    # Test validation class method
    pass
```

**7.5: Performance Tests** (`tests/test_performance.py`)
```python
def test_dispatch_complexity():
    # Verify O(N+M) not O(N×M)
    pass

def test_section_of_performance():
    # Verify O(log N) binary search
    pass

def test_large_document():
    # Test 10MB document under limit
    pass
```

**Files to Create** (15 new test files):

**Core Tests** (5 files):
- `tests/test_indices.py` - Test all 5 indices (by_type, pairs, pairs_rev, parents, children, sections)
- `tests/test_dispatch.py` - Single-pass dispatch, routing table, O(N+M) verification
- `tests/test_section_of.py` - Binary search verification (may already exist as test_section_lookup_performance.py ✅)
- `tests/test_api_compat.py` - API compatibility with src parser
- `tests/test_performance.py` - Comprehensive performance suite (may overlap with test_performance_scaling.py ✅)

**Collector Tests** (6 files - focus on index usage):
- `tests/test_collectors_links.py` - Links collector using indices
- `tests/test_collectors_images.py` - Images collector using indices
- `tests/test_collectors_sections.py` - Sections collector using indices
- `tests/test_collectors_paragraphs.py` - Paragraphs collector
- `tests/test_collectors_lists.py` - Lists collector
- `tests/test_collectors_tables.py` - Tables collector

**Note**: Remaining 6 collectors (headings, tasklists, codeblocks, footnotes, html, math) may be adequately covered by existing security tests.

**Files Already Exist** (✅ 23 tests):
- ~~All other test files~~ ✅ COMPLETE (see Section 7.0)

**Acceptance Criteria**:
- [ ] ✅ 23 existing tests pass unchanged
- [ ] 15 new test files created and passing
- [ ] **Total: 38 test files** (23 existing + 15 new)
- [ ] 100% code coverage for token_warehouse.py
- [ ] All 12 collectors have test coverage (via existing + new tests)
- [ ] Performance tests verify complexity improvements
- [ ] API compatibility tests pass

**Testing Command**:
```bash
# Run all tests (existing + new)
.venv/bin/python -m pytest skeleton/tests/ -v --cov=skeleton/doxstrux --cov-report=term-missing

# Expected: 38 test files, ~200+ test functions
```

**Estimated Effort**: 1-2 days (was 3-4, now 50% less due to 23 existing tests)
**Risk**: LOW (systematic test creation)

---

### Step 8: Baseline Parity & Performance Tests

**Goal**: Verify skeleton produces identical output to src for all 542 baseline tests

**Test Setup**:
```bash
# Use existing baseline test suite
.venv/bin/python tools/baseline_test_runner.py \
    --test-dir tools/test_mds \
    --baseline-dir tools/baseline_outputs \
    --parser-module skeleton.doxstrux
```

**Expected Failures** (initially):
- Output format differences (field names, ordering)
- Missing features (if collectors incomplete)
- Performance regressions (if O(N+M) not achieved)

**Fix Approach**:
1. Run baseline tests, capture failures
2. For each failure:
   - Compare skeleton output vs src output
   - Identify difference (missing field, wrong value, etc.)
   - Fix collector or warehouse code
   - Rerun test
3. Iterate until 542/542 pass

**Performance Benchmarks**:
```bash
# Capture performance baseline
.venv/bin/python tools/capture_baseline_metrics.py \
    --duration 60 \
    --parser-module skeleton.doxstrux \
    --out baselines/skeleton_perf_baseline.json

# Compare with src
.venv/bin/python tools/compare_performance.py \
    baselines/src_perf_baseline.json \
    baselines/skeleton_perf_baseline.json
```

**Acceptance Criteria**:
- [ ] 542/542 baseline tests pass (100%)
- [ ] Output format matches src exactly
- [ ] Parse median time ≤ src + 5%
- [ ] Parse p95 time ≤ src + 10%
- [ ] Memory usage ≤ src + 10%
- [ ] Dispatch is O(N+M) verified

**Estimated Effort**: 2-3 days
**Risk**: HIGH (integration issues may surface)

---

## Phase D: Production Readiness (Steps 9-10)
**Duration**: 3-4 days
**Priority**: P1 - Important
**Risk**: MEDIUM - Operational

---

### Step 9: CI Integration

**Goal**: Add skeleton tests to CI pipeline

**Existing Work**: ✅ **2 workflows already exist** (see Existing Assets Inventory)

---

**9.0: Leverage Existing Workflows** (✅ COMPLETE - Reuse)

**Existing**: `skeleton/.github/workflows/adversarial.yml` (10.3KB)
- PR fast gate (smoke tests <2 min)
- Nightly full suite
- Template injection tests (`test_template_injection_end_to_end.py`)
- HTML/XSS tests (`test_html_xss_end_to_end.py`)
- URL normalization tests (`test_url_normalization_parity.py`)
- Performance profiling matrix

**Existing**: `skeleton/.github/workflows/pr-security-gate.yml` (7.5KB)
- Blocks PRs with security regressions
- Enforces adversarial corpus passing

**Action**: ✅ Keep these workflows as-is for Phase-8 security testing

---

**9.1: Create Unified Workflow** (NEW - Merge + Extend)

**GitHub Actions Workflow** (`.github/workflows/skeleton_tests.yml` - NEW):
```yaml
name: Skeleton Tests

on:
  pull_request:
    paths:
      - 'skeleton/doxstrux/**'
      - 'tests/test_*.py'
  push:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - name: Run unit tests
        run: |
          .venv/bin/python -m pytest tests/ -v --cov=skeleton/doxstrux

  baseline-parity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - name: Run baseline tests
        run: |
          .venv/bin/python tools/baseline_test_runner.py \
            --test-dir tools/test_mds \
            --baseline-dir tools/baseline_outputs \
            --parser-module skeleton.doxstrux \
            --output-json /tmp/baseline_results.json
      - name: Visualize failures (if any)
        if: failure()
        run: |
          # Pretty-print JSON deltas for failed tests
          .venv/bin/python tools/visualize_baseline_diffs.py \
            --results /tmp/baseline_results.json \
            --format github-annotations \
            --max-diffs 20
      - name: Upload diff report
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: baseline-diffs
          path: /tmp/baseline_diffs/

  performance-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - name: Performance test
        run: |
          .venv/bin/python tools/capture_baseline_metrics.py \
            --duration 60 \
            --parser-module skeleton.doxstrux \
            --out /tmp/perf.json
      - name: Check performance regression
        run: |
          # Fail if median > 5% slower than src
          python tools/check_performance_regression.py \
            baselines/src_perf_baseline.json \
            /tmp/perf.json \
            --median-threshold 5 \
            --p95-threshold 10

  adversarial-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - name: Run adversarial corpus tests
        run: |
          # Run all 9 required adversarial corpora
          for corpus in adversarial_corpora/*.json; do
            echo "Testing: $corpus"
            .venv/bin/python tools/test_adversarial.py \
              --corpus $corpus \
              --parser-module skeleton.doxstrux \
              --fail-fast
          done
      - name: Verify corpus coverage
        run: |
          # Ensure all 9 required corpus types exist
          required=(
            "oversized_tables" "huge_lists" "nested_blockquotes"
            "huge_code_lines" "html_injection" "bidi_attacks"
            "malicious_uris" "unicode_exploits" "redos_patterns"
          )
          for corpus_type in "${required[@]}"; do
            if [ ! -f "adversarial_corpora/${corpus_type}.json" ]; then
              echo "ERROR: Missing required corpus: ${corpus_type}.json"
              exit 1
            fi
          done

  coverage-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - name: Run tests with coverage
        run: |
          .venv/bin/python -m pytest tests/ \
            --cov=skeleton/doxstrux/markdown/utils/token_warehouse \
            --cov=skeleton/doxstrux/markdown/collectors_phase8 \
            --cov-report=term-missing \
            --cov-report=json:/tmp/coverage.json \
            --cov-fail-under=80
      - name: Coverage breakdown
        run: |
          # Show per-file coverage
          .venv/bin/python tools/coverage_breakdown.py \
            --coverage-json /tmp/coverage.json \
            --min-threshold 80
      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: /tmp/coverage.json
```

**Files to Create** (4 new files):

**Workflows** (1 file):
- `.github/workflows/skeleton_tests.yml` - Unified workflow (merges adversarial.yml jobs + adds baseline/perf/coverage gates)

**Tools** (3 files):
- `tools/check_performance_regression.py` - Compare perf baselines, fail if >5% slower
- **`tools/visualize_baseline_diffs.py`** - Pretty-print JSON deltas for failed tests
- **`tools/coverage_breakdown.py`** - Show per-file coverage percentages

**Files Already Exist** (✅ 8 files):
- ~~`.github/workflows/adversarial.yml`~~ ✅ COMPLETE (10.3KB, keep as-is)
- ~~`.github/workflows/pr-security-gate.yml`~~ ✅ COMPLETE (7.5KB, keep as-is)
- ~~`skeleton/tools/benchmark_parser.py`~~ ✅ COMPLETE
- ~~`skeleton/tools/profile_collectors.py`~~ ✅ COMPLETE
- ~~`skeleton/tools/run_adversarial.py`~~ ✅ COMPLETE (rename to test_adversarial.py or keep as-is)
- ~~`performance/tools/capture_baseline_metrics.py`~~ ✅ COMPLETE (in parent dir)
- Plus 2 other skeleton tools (collector workers, corpus generator)

**Acceptance Criteria**:
- [ ] ✅ Existing adversarial.yml continues to run (PR fast gate, nightly suite)
- [ ] ✅ Existing pr-security-gate.yml continues to run
- [ ] Unit tests run on every PR (all 38 tests: 23 existing + 15 new)
- [ ] Baseline parity tests run on skeleton changes
- [ ] **Baseline failures show JSON diffs** (field added/removed/changed)
- [ ] Performance gates block regression >5%
- [ ] **Adversarial gate runs corpora** (leverage existing adversarial.yml)
- [ ] **Coverage gate enforces ≥80% on token_warehouse and collectors**
- [ ] Tests pass on Ubuntu (Linux-only for SIGALRM)

**Estimated Effort**: 0.5 days (was 1 day, now 50% less due to existing workflows)
**Risk**: LOW (standard CI setup)

---

### Step 10: Security Re-Verification

**Goal**: Ensure all security features from src are preserved + new Phase-8 features work

**Existing Work**: ✅ **4 policy docs + 12 corpora already exist** (see Existing Assets Inventory)

---

**10.0: Leverage Existing Security Documentation** (✅ COMPLETE)

**Existing Policies** (`skeleton/policies/`):
1. `EXEC_ALLOW_RAW_HTML_POLICY.md` (11.8KB) - Documents raw HTML handling decisions
2. `EXEC_COLLECTOR_ALLOWLIST_POLICY.md` (9.5KB) - Documents collector allowlist approach
3. `EXEC_PLATFORM_SUPPORT_POLICY.md` (13.9KB) - Documents Windows/Linux support (covers SIGALRM fallback)
4. `EXEC_TEMPLATE_SSTI_PREVENTION_POLICY.md` (12.8KB) - Documents SSTI prevention strategy

**Action**: ✅ **Reference these in SECURITY_GAPS.md** as evidence of Phase-8 security work

**Existing Corpora** (`performance/adversarial_corpora/`):
- 12 corpus files covering XSS, SSTI, URL encoding, deep nesting, ReDoS, etc.
- See Section 10.4 for mapping to required corpus types

---

**Security Checklist**:

**10.1: Resource Limits**
- [ ] Content size limits enforced (MAX_BYTES)
- [ ] Token count limits enforced (MAX_TOKENS)
- [ ] Nesting depth limits enforced (MAX_NESTING)
- [ ] Timeout protection works (SIGALRM)

**10.2: Input Validation**
- [ ] ~~Plugin validation~~ (not in skeleton - document as missing)
- [ ] ~~HTML sanitization~~ (not in skeleton - document as missing)
- [ ] ~~Link scheme validation~~ (not in skeleton - document as missing)
- [ ] ~~BiDi control detection~~ (not in skeleton - document as missing)

**10.3: Phase-8 Security Features**
- [x] Token canonicalization prevents supply-chain attacks
- [x] Reentrancy guard prevents concurrent dispatch
- [x] Collector timeout prevents DoS
- [x] URL normalization prevents bypass attacks

**10.4: Adversarial Testing**

**Required Adversarial Corpus Types**:

Each corpus file should include an `expected_outcome` field to define pass/fail criteria.

1. **Oversized Tables** (`adversarial_corpora/oversized_tables.json`)
   - Tables with 1000+ rows
   - Tables with 100+ columns
   - Cells with 10KB+ content
   - **Expected**: Parser handles without crash, enforces resource limits

2. **10K-Item Lists** (`adversarial_corpora/huge_lists.json`)
   - Bullet lists with 10,000 items
   - Nested lists 50+ levels deep
   - Mixed ordered/unordered nesting
   - **Expected**: Nesting depth limit enforced, no stack overflow

3. **Deeply Nested Blockquotes** (`adversarial_corpora/nested_blockquotes.json`)
   - Blockquotes nested 50-100 levels
   - Blockquotes containing lists, tables, code
   - **Expected**: MAX_NESTING (150) enforced, clean error message

4. **Code Fences with Huge Lines** (`adversarial_corpora/huge_code_lines.json`)
   - Single code line with 100KB characters
   - Code blocks with 10K lines
   - Malformed fence delimiters
   - **Expected**: MAX_BYTES enforced, no regex catastrophic backtracking

5. **HTML/Script Injection** (`adversarial_corpora/html_injection.json`)
   - `<script>` tags in inline HTML
   - `javascript:` scheme in links
   - `data:` URIs with embedded payloads
   - `file:` scheme attempts
   - **Expected**: Scheme validation rejects malicious URIs, HTML sanitized (if bleach available)

6. **BiDi Control Characters** (`adversarial_corpora/bidi_attacks.json`)
   - U+202E (RIGHT-TO-LEFT OVERRIDE) in text
   - U+200F (RIGHT-TO-LEFT MARK) in links
   - Homograph attacks (lookalike chars)
   - **Expected**: BiDi chars detected and flagged (Phase 9 feature, document gap if missing)

7. **Malicious URIs** (`adversarial_corpora/malicious_uris.json`)
   - `javascript:alert(1)` in links
   - `data:text/html,<script>` payloads
   - `file:///etc/passwd` local file access
   - SSRF attempts: `http://localhost:6379/`
   - **Expected**: Only http/https/mailto/tel schemes allowed

8. **Unicode Exploits** (`adversarial_corpora/unicode_exploits.json`)
   - NUL bytes (U+0000) in content
   - Overlong UTF-8 sequences
   - Surrogate pairs (U+D800-U+DFFF)
   - Non-characters (U+FFFE, U+FFFF)
   - **Expected**: NFC normalization applied, invalid UTF-8 rejected

9. **ReDoS Patterns** (`adversarial_corpora/redos_patterns.json`)
   - Catastrophic backtracking patterns (if any regex remaining)
   - Nested quantifiers: `(a+)+b` with many `a`s
   - Alternation explosion: `(a|b|c|...){100}`
   - **Expected**: No regex in Phase-8 parser (token-based), but test URL parsers

**Corpus File Format**:
```json
{
  "corpus_name": "oversized_tables",
  "version": "1.0",
  "test_cases": [
    {
      "id": "table_1000_rows",
      "description": "Table with 1000 rows should hit MAX_TOKENS limit",
      "markdown": "| Col1 | Col2 |\n|------|------|\n...",
      "expected_outcome": {
        "type": "error",
        "error_type": "ResourceLimitExceeded",
        "message_contains": "MAX_TOKENS"
      }
    },
    {
      "id": "table_100_cols",
      "description": "Table with 100 columns should parse successfully",
      "markdown": "| C1 | C2 | ... | C100 |\n|---|---|...",
      "expected_outcome": {
        "type": "success",
        "assertions": {
          "tables_count": 1,
          "columns_count": 100
        }
      }
    }
  ]
}
```

**Existing Corpora Mapping**:

✅ **Corpora that already exist** (10 files map to requirements):
1. ✅ `adversarial_deep_nesting.json` → **nested_blockquotes**
2. ✅ `adversarial_html_xss.json` → **html_injection**
3. ⚠️ `adversarial_encoded_urls.json` → **malicious_uris** (partial - add javascript:, data:, file:)
4. ✅ `adversarial_regex_pathological.json` → **redos_patterns**
5. ⚠️ `adversarial_large.json` → **huge_code_lines** (partial - verify 100KB single line coverage)
6. Plus 7 additional corpora (SSTI, attrget, malformed_maps, combined, fast_smoke, manifest, encoded_urls_raw)

❌ **Missing Corpora** (5 files to create):
1. ❌ `oversized_tables.json` - 1000+ rows, 100+ cols
2. ❌ `huge_lists.json` - 10K items, 50+ nesting levels
3. ❌ `bidi_attacks.json` - BiDi control characters (U+202E, U+200F)
4. ❌ `unicode_exploits.json` - NUL bytes, overlong UTF-8, surrogates, non-characters
5. ⚠️ Complete `malicious_uris.json` - Add missing javascript:, data:, file: schemes

⚠️ **Format Conversion Needed**:
- Existing corpora use **token-based** format
- Required format: **markdown + expected_outcome**
- Either: Create new versions OR convert existing files

**Test Runner**:
```bash
# Run all adversarial corpora (existing + new)
for corpus in adversarial_corpora/*.json; do
    echo "Testing: $corpus"
    .venv/bin/python tools/test_adversarial.py \
        --corpus $corpus \
        --parser-module skeleton.doxstrux \
        --verbose
done

# Expected: All corpora pass with documented expected outcomes
# Existing: 12 corpus files ✅
# To create: 5 new corpus files ❌
```

**Security Gap Documentation** (`SECURITY_GAPS.md`):
```markdown
# Security Features Not Ported from src

The following security features from src/doxstrux are NOT in skeleton:

1. Plugin validation by security profile
2. HTML sanitization via bleach
3. Link scheme validation (only http/https/mailto/tel)
4. BiDi control character detection
5. Prompt injection pattern detection

**Recommendation**: Port these features in Phase 9 (post drop-in)
```

**Acceptance Criteria**:
- [ ] ✅ Existing 4 policy docs referenced in SECURITY_GAPS.md
- [ ] ✅ Existing 12 corpus files continue to pass
- [ ] 5 new corpus files created (or existing converted to markdown+expected_outcome format)
- [ ] All Phase-8 security features functional
- [ ] Resource limits prevent DoS
- [ ] Token canonicalization tested
- [ ] **Total: 17 adversarial corpora** (12 existing + 5 new)
- [ ] Security gaps documented

**Estimated Effort**: 1 day (was 2 days, now 50% less due to 12 existing corpora + 4 policy docs)
**Risk**: MEDIUM (security gaps exist, must document)

---

## Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Baseline parity fails** | HIGH | HIGH | Incremental fixing, compare outputs carefully |
| **Performance regression** | MEDIUM | HIGH | Profile dispatch, verify O(N+M), optimize hotspots |
| **Collector bugs** | MEDIUM | MEDIUM | Thorough unit tests per collector |
| **API incompatibility** | LOW | HIGH | Strict adherence to src API in compatibility shim |
| **Security gaps** | LOW | MEDIUM | Document gaps, plan Phase 9 for missing features |

### Timeline Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Underestimated effort** | MEDIUM | MEDIUM | Add 20% buffer to estimates |
| **Blocked by src bugs** | LOW | MEDIUM | Document and work around, file issues |
| **Test failures cascade** | MEDIUM | HIGH | Fix systematically, don't skip tests |

### Quality Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Incomplete index building** | HIGH | HIGH | Extensive edge case testing |
| **Routing table bugs** | MEDIUM | HIGH | Formal verification of dispatch logic |
| **Memory leaks** | LOW | MEDIUM | Profile memory usage on large docs |

---

## YAGNI/KISS Guardrails

**Purpose**: Keep scope tight, reduce risk, ship faster

These guardrails enforce the "You Aren't Gonna Need It" and "Keep It Simple, Stupid" principles to prevent scope creep and maintain focus on the critical path to baseline parity.

### Scope Restrictions

#### 1. Don't Expand CLI/Fetchers Until Parity is Green
**Rationale**: CLI and fetcher modules are nice-to-have features that distract from core parser work.

**Prohibited** (until 542/542 baseline tests pass):
- ❌ Adding new CLI commands or flags
- ❌ Implementing HTTP/file fetchers
- ❌ Building interactive CLI features
- ❌ Adding configuration file support beyond what exists

**Allowed** (after parity green):
- ✅ Minimal CLI for testing/debugging
- ✅ Simple file-to-stdout parser script

**Enforcement**: Code review blocks PRs adding CLI/fetcher features before baseline parity

---

#### 2. Don't Intermix Security Upgrades with Dispatch/Index Refactors
**Rationale**: Mixing architectural changes with security features makes debugging harder and increases risk.

**Sequential approach** (strictly ordered):
1. **Phase A-B** (Steps 1-6): Complete indices + dispatch + API shim
2. **Phase C** (Steps 7-8): Achieve baseline parity + performance gates
3. **Phase D, Step 10**: Port missing security validators (Phase 9 follow-up)

**Prohibited during Steps 1-8**:
- ❌ Adding HTML sanitization (bleach integration)
- ❌ Adding BiDi control detection
- ❌ Adding prompt injection pattern matching
- ❌ Adding link scheme allow-lists

**Why**: These are security *enhancements* from src. Focus on functional parity first, security parity second.

**Enforcement**: Security validator ports are deferred to a separate Phase 9 branch

---

#### 3. Land Parity First, Validators as Phase 9 Follow-Up
**Rationale**: Baseline parity proves skeleton can replace src functionally. Security gaps are documented and addressed after.

**Phase 8 Goal** (this plan):
- Achieve 100% baseline parity (542/542 tests)
- Maintain existing Phase-8 security features (canonicalization, timeouts, reentrancy guard)
- Document security gaps explicitly (SECURITY_GAPS.md)

**Phase 9 Goal** (future work):
- Port HTML sanitization
- Port BiDi control detection
- Port prompt injection detection
- Port link scheme validation
- Add security profiles (strict/moderate/permissive)

**Why separate phases**:
- Parity is binary (pass/fail), security is continuous (more is better)
- Parity blocks production deployment, security gaps are acceptable if documented
- Allows parallel work: one team on parity, another on security

---

### Anti-Patterns to Avoid

#### ❌ Feature Creep
**Example**: "While fixing dispatch, let's also add streaming parser support"
**Problem**: Doubles scope, delays parity, introduces new failure modes
**Fix**: Create GitHub issue for streaming, finish parity first

#### ❌ Gold Plating
**Example**: "Let's make the routing table use a trie instead of dict for faster lookups"
**Problem**: Premature optimization, no evidence dict is slow
**Fix**: Profile first, optimize only if >5% impact

#### ❌ "Just One More Thing"
**Example**: "We're at 541/542 tests passing, let's quickly add that missing collector feature"
**Problem**: "Quick" features often cascade into multi-day debugging
**Fix**: Debug the 1 failing test, hit 100%, then add features

#### ❌ Perfectionism
**Example**: "Let's refactor all collectors to use inheritance hierarchy before shipping"
**Problem**: Refactoring working code delays deployment, introduces bugs
**Fix**: If collectors work and tests pass, ship it

---

### Decision Framework

When considering adding a feature/optimization during Steps 1-10, ask:

1. **Does this block baseline parity?**
   - Yes → Do it now (critical path)
   - No → Defer to Phase 9+

2. **Does this fix a failing test?**
   - Yes → Do it now (gate blocker)
   - No → Defer or drop

3. **Is there proof this is a bottleneck?**
   - Yes (profiler shows >5% time) → Optimize
   - No → Defer

4. **Does this simplify the code?**
   - Yes (removes lines, reduces complexity) → Do it
   - No (adds abstraction, generalization) → Defer

---

### Enforcement Mechanisms

**Code Review Checklist**:
- [ ] PR is on critical path (Steps 1-10)
- [ ] PR does not add CLI/fetcher features
- [ ] PR does not mix security validators with dispatch/index work
- [ ] PR includes tests for changes
- [ ] PR does not introduce new abstractions without justification

**Branch Protection**:
- Require 1 approval for PRs
- Require CI gates green (parity, perf, coverage)
- Block merge if "scope creep" label applied

**Weekly Reviews**:
- Review open PRs for scope drift
- Close issues marked "Phase 9" during Phase 8 work
- Remind team: "Parity first, features later"

---

### Success Story (Example)

**Scenario**: Team is at Step 5 (API shim), 80% baseline parity (434/542 tests).

**Temptation**: "Let's add streaming parser API now since we're touching the shim"

**YAGNI Response**:
1. **Block**: Streaming is not needed for parity
2. **Document**: Create issue #123 "Add streaming API (Phase 9+)"
3. **Focus**: Fix remaining 108 failing baseline tests
4. **Result**: Hit 542/542 parity 3 days later, ship skeleton to prod
5. **Follow-up**: After prod deployment, revisit streaming in Phase 9

**Outcome**: Shipped 2 weeks earlier by avoiding scope creep

---

## Success Metrics

### Functional Metrics
- [ ] 542/542 baseline tests pass (100%)
- [ ] All 12 collectors functional
- [ ] API compatibility: 100% src methods work
- [ ] **38 unit tests** total (✅ 23 existing + 15 new)

### Performance Metrics
- [ ] Dispatch complexity: O(N+M) verified
- [ ] section_of(): O(log N) verified
- [ ] Parse median: ≤ src + 5%
- [ ] Parse p95: ≤ src + 10%

### Quality Metrics
- [ ] Unit test coverage: ≥80%
- [ ] No critical security regressions (✅ 11 security tests existing)
- [ ] CI gates all green (✅ 2 workflows existing, 1 unified workflow to create)
- [ ] Documentation complete (✅ 4 policy docs existing)
- [ ] **17 adversarial corpora** total (✅ 12 existing + 5 new)

---

## Rollout Plan

### Phase 1: Feature Flag Testing (Week 1-2)
```python
# Enable skeleton via environment variable
USE_SKELETON = os.getenv("USE_SKELETON_PARSER", "0") == "1"

if USE_SKELETON:
    from skeleton.doxstrux import MarkdownParserCore
else:
    from src.doxstrux import MarkdownParserCore
```

### Phase 2: Canary Deployment (Week 3-4)
- Deploy skeleton to 1% of production traffic
- Monitor metrics (parse time, errors, memory)
- Compare outputs with src for parity

### Phase 3: Gradual Rollout (Week 5-8)
- Increase to 10%, 25%, 50%, 100%
- Monitor at each step
- Rollback plan: Set USE_SKELETON=0

### Phase 4: Deprecate src (Week 9+)
- Mark src/doxstrux as deprecated
- Move src → src_legacy
- Promote skeleton → src

---

## Rollback Procedures

### If Baseline Tests Fail
```bash
# Identify failures
.venv/bin/python tools/baseline_test_runner.py --parser-module skeleton.doxstrux > failures.txt

# Rollback specific collector
git checkout HEAD~1 skeleton/doxstrux/markdown/collectors_phase8/links.py

# Retest
.venv/bin/python -m pytest tests/test_collectors_links.py
```

### If Performance Regression
```bash
# Identify slow component
.venv/bin/python -m cProfile -o profile.stats tools/baseline_test_runner.py
python -m pstats profile.stats

# Optimize dispatch or index building
# Retest performance
.venv/bin/python tools/capture_baseline_metrics.py --duration 60
```

### If Production Issues
```bash
# Immediate rollback via feature flag
export USE_SKELETON_PARSER=0

# Or revert commit
git revert <commit-hash>
git push
```

---

## Definition of Done

**skeleton/doxstrux is considered a drop-in replacement when**:

- [ ] All 542 baseline tests pass (100%)
- [ ] API is 100% compatible with src (can replace import with zero changes)
- [ ] Performance is O(N+M) for dispatch (verified)
- [ ] Performance is ≤ src + 5% median, ≤ src + 10% p95
- [ ] All 12 collectors functional and tested
- [ ] Security features preserved (with documented gaps)
- [ ] CI gates green (unit, baseline, performance)
- [ ] Documentation complete (API, architecture, migration)
- [ ] Feature flag tested in production (1% canary successful)

---

## Cross-Artifact Integrity (Render Sync)

**Purpose**: Ensure rendered artifacts (JSON, MD) never drift from YAML source.

### SHA256 Synchronization

Every rendered artifact embeds the SHA256 hash of its source YAML:

```json
{
  "render_meta": {
    "source_file": "DETAILED_TASK_LIST_template.yaml",
    "schema_version": "1.0.0",
    "sha256_of_yaml": "abc123...",
    "rendered_utc": "2025-10-19T04:50:00Z"
  }
}
```

**CI Verification** (`.github/workflows/verify_render.yml`):
```bash
# Re-render from YAML
python tools/render_task_templates.py --strict

# Compare SHA256 hashes
YAML_SHA=$(sha256sum DETAILED_TASK_LIST_template.yaml | awk '{print $1}')
JSON_SHA=$(jq -r '.render_meta.sha256_of_yaml' DETAILED_TASK_LIST_template.json)

if [ "$YAML_SHA" != "$JSON_SHA" ]; then
  echo "❌ Render drift detected - JSON out of sync with YAML"
  exit 1
fi
```

**Enforcement**: CI blocks merges if rendered files don't match source.

---

## Parser Output Contract (API Compatibility)

**Purpose**: Define stable API contract for parser outputs to prevent silent breakage.

### Schema Definition

`schemas/parser_output.schema.json` defines the top-level structure returned by `MarkdownParserCore.parse()`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Parser Output Contract",
  "type": "object",
  "required": ["sections", "headings", "links", "version"],
  "properties": {
    "sections": { "type": "array", "items": { "$ref": "#/$defs/section" } },
    "headings": { "type": "array", "items": { "$ref": "#/$defs/heading" } },
    "paragraphs": { "type": "array", "items": { "$ref": "#/$defs/paragraph" } },
    "links": { "type": "array", "items": { "$ref": "#/$defs/link" } },
    "images": { "type": "array", "items": { "$ref": "#/$defs/image" } },
    "lists": { "type": "array", "items": { "$ref": "#/$defs/list" } },
    "code_blocks": { "type": "array", "items": { "$ref": "#/$defs/code_block" } },
    "tables": { "type": "array", "items": { "$ref": "#/$defs/table" } },
    "footnotes": { "type": "array", "items": { "$ref": "#/$defs/footnote" } },
    "blockquotes": { "type": "array", "items": { "$ref": "#/$defs/blockquote" } },
    "html_blocks": { "type": "array", "items": { "$ref": "#/$defs/html_block" } },
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" }
  },
  "$defs": {
    "section": {
      "type": "object",
      "required": ["id", "heading_id", "start_line", "end_line", "level"],
      "properties": {
        "id": { "type": "string" },
        "heading_id": { "type": "string" },
        "start_line": { "type": "integer" },
        "end_line": { "type": "integer" },
        "level": { "type": "integer", "minimum": 1, "maximum": 6 }
      }
    },
    "heading": {
      "type": "object",
      "required": ["id", "text", "level", "start_line"],
      "properties": {
        "id": { "type": "string" },
        "text": { "type": "string" },
        "level": { "type": "integer", "minimum": 1, "maximum": 6 },
        "start_line": { "type": "integer" }
      }
    },
    "link": {
      "type": "object",
      "required": ["id", "text", "url", "start_line"],
      "properties": {
        "id": { "type": "string" },
        "text": { "type": "string" },
        "url": { "type": "string" },
        "title": { "type": ["string", "null"] },
        "start_line": { "type": "integer" },
        "is_normalized": { "type": "boolean" }
      }
    }
  }
}
```

**Baseline Parity Gate**:
```bash
# Validate every baseline output against schema
for baseline in tools/baseline_outputs/*.baseline.json; do
  python -m jsonschema -i "$baseline" schemas/parser_output.schema.json || exit 1
done
```

**Benefits**:
- Catch API breakage before it reaches production
- Self-documenting contract for downstream consumers
- Versioned schema evolution (semver)

---

## Task Result Schema & Post-Rollback Verification

**Purpose**: Standardize task execution outputs and rollback verification.

### Task Result Schema

`schemas/task_result.schema.json` defines standard format for task execution outputs:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Task Execution Result",
  "type": "object",
  "required": ["task_id", "status", "stdout", "stderr", "return_code", "timestamp"],
  "properties": {
    "task_id": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+$" },
    "status": { "enum": ["success", "failed", "skipped"] },
    "stdout": { "type": "string" },
    "stderr": { "type": "string" },
    "return_code": { "type": "integer" },
    "duration_sec": { "type": "number", "minimum": 0 },
    "timestamp": { "type": "string", "format": "date-time" },
    "artifacts": {
      "type": "array",
      "items": { "type": "string" }
    },
    "meta": {
      "type": "object",
      "properties": {
        "executor": { "type": "string" },
        "environment": { "type": "string" },
        "hostname": { "type": "string" },
        "git_commit": { "type": "string" }
      }
    }
  }
}
```

**Usage**:
```bash
# Emit result after task completion
python tools/emit_task_result.py 1.2 success "Tests passed" "" 0 45.3 build/output.json

# Validate result
python -m jsonschema -i evidence/results/task_1.2.json schemas/task_result.schema.json
```

### Post-Rollback Verification Criteria

Each task with rollback steps should define verification criteria:

```yaml
tasks:
  - id: "1.2"
    name: "Migrate LinksCollector to index-first"
    rollback:
      - "git revert $(git log -1 --format='%H')"
      - "pip install -e ."
    post_rollback_criteria:
      - "Repository state matches HEAD~1"
      - "All baseline tests pass (542/542)"
      - "No orphaned imports or references to removed code"
      - "CI gates green (G1-G5)"
```

**Enforcement**:
```bash
# After rollback, verify criteria
for criterion in "${post_rollback_criteria[@]}"; do
  verify_criterion "$criterion" || {
    echo "❌ Post-rollback verification failed: $criterion"
    exit 1
  }
done
```

**Benefits**:
- Standardized rollback safety net
- Prevents "half-rolled-back" states
- Auditable rollback history

---

## Windows Timeout Semantics

**Purpose**: Handle platform differences in timeout implementation.

### Platform Detection

```python
import platform
import signal
from threading import Timer

def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == "Windows"

def set_timeout(func, timeout_sec: float):
    """Set timeout with platform-appropriate mechanism."""
    if is_windows():
        # Windows: Use threading.Timer (no SIGALRM)
        timer = Timer(timeout_sec, _timeout_handler)
        timer.start()
        try:
            result = func()
        finally:
            timer.cancel()
        return result
    else:
        # Unix: Use signal.SIGALRM
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(int(timeout_sec))
        try:
            result = func()
        finally:
            signal.alarm(0)
        return result

def _timeout_handler(*args):
    """Raise timeout exception."""
    raise TimeoutError("Operation exceeded timeout")
```

### Timeout Policy

**Default Timeouts**:
- **Per-collector timeout**: 5 seconds (configurable)
- **Total parse timeout**: 30 seconds (configurable)
- **CI timeout**: 60 seconds (hard limit)

**Configuration**:
```python
# Per-collector timeout
collector = LinksCollector(timeout_sec=5)

# Total parse timeout
parser = MarkdownParserCore(content, parse_timeout_sec=30)

# Disable timeouts (testing only)
parser = MarkdownParserCore(content, parse_timeout_sec=None)
```

**Windows Limitations**:
- Threading-based timeouts are **not interruptible** (function must complete or check cancellation flag)
- SIGALRM not available on Windows
- Timeout accuracy: ±100ms (vs ±1ms on Unix)

**Mitigation**:
```python
class CollectorTimeout:
    """Context manager for collector timeouts with platform awareness."""

    def __init__(self, timeout_sec: float):
        self.timeout_sec = timeout_sec
        self.is_windows = platform.system() == "Windows"
        self.timer = None
        self.timed_out = False

    def __enter__(self):
        if self.is_windows:
            # Windows: Start timer that sets flag
            self.timer = Timer(self.timeout_sec, self._set_timeout_flag)
            self.timer.start()
        else:
            # Unix: Use SIGALRM
            signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(int(self.timeout_sec))
        return self

    def __exit__(self, *args):
        if self.is_windows:
            if self.timer:
                self.timer.cancel()
        else:
            signal.alarm(0)

    def check_timeout(self):
        """Collector must call this periodically on Windows."""
        if self.is_windows and self.timed_out:
            raise TimeoutError("Collector exceeded timeout")

    def _set_timeout_flag(self):
        self.timed_out = True

    def _timeout_handler(self, *args):
        raise TimeoutError("Collector exceeded timeout")
```

**Collector Implementation** (Windows-compatible):
```python
def collect(self, wh: TokenWarehouse) -> list[dict]:
    """Collect links with timeout protection."""
    with CollectorTimeout(self.timeout_sec) as timeout_ctx:
        links = []

        for idx, tok in enumerate(wh.by_type.get("link_open", [])):
            # Periodically check timeout on Windows
            if idx % 100 == 0:
                timeout_ctx.check_timeout()

            # ... extract link data
            links.append(link_data)

        return links
```

**Testing**:
```python
def test_timeout_windows_compatible():
    """Test timeout works on both Unix and Windows."""
    content = "[link](" + "x" * 1_000_000 + ")"  # Slow to parse

    parser = MarkdownParserCore(content, parse_timeout_sec=1)

    with pytest.raises(TimeoutError):
        parser.parse()
```

**Documentation**:
- All timeout values documented in `PLATFORM_SUPPORT_POLICY.md`
- Windows limitations noted in README.md
- CI tests run on both Linux and Windows runners

---

## Appendix: Command Reference

### Development Commands
```bash
# Run all tests
.venv/bin/python -m pytest tests/ -v

# Run specific test
.venv/bin/python -m pytest tests/test_indices.py::test_by_type_index -v

# Check coverage
.venv/bin/python -m pytest tests/ --cov=skeleton/doxstrux --cov-report=html

# Run baseline tests
.venv/bin/python tools/baseline_test_runner.py \
    --test-dir tools/test_mds \
    --baseline-dir tools/baseline_outputs \
    --parser-module skeleton.doxstrux

# Performance test
.venv/bin/python tools/capture_baseline_metrics.py \
    --duration 60 \
    --parser-module skeleton.doxstrux \
    --out baselines/skeleton_perf.json

# Compare performance
.venv/bin/python tools/compare_performance.py \
    baselines/src_perf.json \
    baselines/skeleton_perf.json
```

### Debugging Commands
```bash
# Profile dispatch
.venv/bin/python -m cProfile -o dispatch.prof \
    -c "from skeleton.doxstrux import MarkdownParserCore; p = MarkdownParserCore(open('test.md').read()); p.parse()"

# Analyze profile
python -m pstats dispatch.prof

# Memory profiling
.venv/bin/python -m memory_profiler skeleton/doxstrux/markdown/utils/token_warehouse.py

# Check index population
.venv/bin/python -c "
from skeleton.doxstrux.markdown.utils.token_warehouse import TokenWarehouse
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

content = open('test.md').read()
md = MarkdownIt()
tokens = md.parse(content)
tree = SyntaxTreeNode(tokens)
wh = TokenWarehouse(tokens, tree, content)

print(f'by_type: {len(wh.by_type)} types')
print(f'pairs: {len(wh.pairs)} pairs')
print(f'parents: {len(wh.parents)} parents')
print(f'sections: {len(wh.sections)} sections')
"
```

---

**Plan Complete**: 2025-10-19
**Total Estimated Effort**: 13-20 days (3-6 day savings from existing work)
**Phases**: 4 (A: Infrastructure, B: API, C: Validation, D: Production)
**Steps**: 10 (detailed surgical conversion)
**Existing Assets Leveraged**: 23 tests + 6 tools + 4 policies + 2 workflows + 12 corpora (~45% effort reduction)
**Status**: Ready for implementation approval
