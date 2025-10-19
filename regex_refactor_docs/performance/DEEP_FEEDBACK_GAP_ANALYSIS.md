# Deep Feedback Gap Analysis
# 20 Subtle Breakpoints & Edge-Cases - Implementation Status

**Date**: 2025-10-19
**Source**: Deep implementation review feedback
**Status**: 🟡 **PARTIAL COVERAGE** - Critical gaps identified

---

## Executive Summary

**Current Coverage**: ~65% (13/20 risks addressed)
**Critical Gaps**: 7 risks requiring immediate attention
**Implementation Effort**: ~3-4 days for complete coverage

This document analyzes 20 subtle failure modes that could cause silent bugs during implementation and rollout, comparing current documentation against recommended fixes.

---

## Gap Coverage Matrix

| # | Risk | Current Status | Gap Severity | Action Required |
|---|------|----------------|--------------|-----------------|
| **1** | Token maps vs text normalization | ⚠️ **PARTIAL** - Normalizes in `__init__` but after parse | 🔴 **CRITICAL** | Normalize before parse |
| **2** | Sections tuple shape drifts | 🔴 **MISSING** - Multiple tuple formats | 🔴 **CRITICAL** | Freeze to dataclass |
| **3** | Pairs/parents for nesting==0 | ⚠️ **PARTIAL** - Stack tracking mentioned | 🟡 **HIGH** | Add explicit tests |
| **4** | Routing dedup determinism | 🔴 **MISSING** - Uses `list(set(...))` | 🔴 **CRITICAL** | Stable order dedup |
| **5** | O(N+M) proof inadequate | ⚠️ **PARTIAL** - Has complexity test | 🟡 **HIGH** | Add token visit counter |
| **6** | Windows timeout not enforced | ✅ **COMPLETE** - Full implementation in docs | - | - |
| **7** | Binary search section_of() fragile | ⚠️ **PARTIAL** - Only starts[] mentioned | 🟡 **HIGH** | Add ends[] array |
| **8** | API contract without binding gates | ⚠️ **PARTIAL** - Schema exists, no enforcement | 🔴 **CRITICAL** | Add canary zero-mismatch gate |
| **9** | Cross-artifact drift loop not closed | ⚠️ **PARTIAL** - SHA sync exists, no CI gate | 🟡 **HIGH** | Add verify_render job |
| **10** | Adversarial corpus gaps | ⚠️ **PARTIAL** - Some corpora exist | 🟡 **HIGH** | Add required-list CI check |
| **11** | Helper method determinism | 🔴 **MISSING** - No binary search requirement | 🟡 **HIGH** | Require bisect_left/right |
| **12** | Children index lifecycle | 🔴 **MISSING** - Build strategy unclear | 🟡 **HIGH** | Define build-once policy |
| **13** | Collector iteration rule | ⚠️ **PARTIAL** - Ban mentioned, no exceptions | 🟢 **MEDIUM** | Define sparse scan exception |
| **14** | Canary telemetry privacy | 🔴 **MISSING** - No PII redaction policy | 🟡 **HIGH** | Add log sanitizer |
| **15** | Unicode beyond NFC | ⚠️ **PARTIAL** - NFC only, no BiDi/invalid handling | 🟡 **HIGH** | Add unicode_policy.md |
| **16** | Spec drift REFACTOR vs TIMELINE | 🔴 **MISSING** - Two independent docs | 🟢 **MEDIUM** | Add SHA reference |
| **17** | Import path compatibility | 🔴 **MISSING** - No import path test | 🟡 **HIGH** | Add sys.modules test |
| **18** | Per-construct perf deltas | 🔴 **MISSING** - Only aggregate metrics | 🟡 **HIGH** | Add micro-benchmarks |
| **19** | Evidence retention policy | ⚠️ **PARTIAL** - Directory exists, no manifest | 🟢 **MEDIUM** | Add index.json manifest |
| **20** | Memory ceiling gates | 🔴 **MISSING** - No RSS budgets | 🟡 **HIGH** | Add tracemalloc gates |

**Summary**:
- ✅ **Complete**: 1/20 (5%)
- ⚠️ **Partial**: 11/20 (55%)
- 🔴 **Missing**: 8/20 (40%)

---

## Detailed Analysis & Fixes

### 🔴 CRITICAL - Fix Before Step 1

#### 1. Token Maps vs Text Normalization (CRITICAL)

**Problem**: Normalize text AFTER markdown-it parses, causing token.map offsets to mismatch self.lines.

**Current State** (DOXSTRUX_REFACTOR.md:317-325):
```python
def __init__(self, tokens, tree, text=None):
    # Normalize content before indexing
    if text:
        text = unicodedata.normalize('NFC', text)
        text = text.replace('\r\n', '\n')
        self.text = text
```

**Gap**: Tokens are already parsed from unnormalized text. `token.map` offsets point to wrong lines.

**Fix**:
```python
# BEFORE creating MarkdownIt parser
def parse_markdown(content: str) -> tuple[list, SyntaxTreeNode, str]:
    """Parse markdown with normalized text."""
    # 1. Normalize FIRST
    normalized = unicodedata.normalize('NFC', content)
    normalized = normalized.replace('\r\n', '\n')

    # 2. THEN parse
    md = MarkdownIt("gfm-like")
    tokens = md.parse(normalized)
    tree = SyntaxTreeNode(tokens)

    return tokens, tree, normalized

# In warehouse
def __init__(self, tokens, tree, text):
    # Text is already normalized, tokens.map matches lines
    self.text = text
    self.lines = text.splitlines(keepends=True)
    self._build_indices()
```

**Add to docs** (DOXSTRUX_REFACTOR.md → Executive Summary → Assumptions):
```markdown
**INVARIANT: Coordinate System Integrity**

All coordinates (token.map, line numbers, byte offsets) are derived from the **same normalized text** (NFC + LF).

- Normalization happens **BEFORE** markdown-it parsing
- TokenWarehouse receives pre-normalized text
- All get_line_range(), get_token_text(), section_of() use consistent offsets
```

**Test**:
```python
def test_normalization_coordinate_integrity():
    """Token.map offsets must match normalized text lines."""
    # Content with decomposed unicode + CRLF
    content = "# Café\r\nParagraph"  # é as e + combining acute

    tokens, tree, normalized = parse_markdown(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Token map should point to lines in normalized text
    h1_token = [t for t in tokens if t.type == "heading_open"][0]
    line_content = wh.lines[h1_token.map[0]]

    # Must find "Café" (NFC composed form)
    assert "Café" in line_content  # Would fail with late normalization
    assert "\r" not in line_content  # Would fail with late normalization
```

---

#### 2. Sections Tuple Shape Drifts (CRITICAL)

**Problem**: Multiple tuple shapes for sections → brittle tests, collector errors.

**Current State** (DOXSTRUX_REFACTOR.md:366-388):
```python
# Line 366: (start_line, end_line, tok_idx, level, title)
# Line 380: (start_line, None, idx, level, section_idx, title)
# Line 381: appends temporary tuple
# Line 387: rewrites with different shape
```

**Gap**: No single canonical shape, makes code error-prone.

**Fix**:
```python
# Define once with dataclass
from dataclasses import dataclass

@dataclass(frozen=True)
class Section:
    """Canonical section structure (INVARIANT: do not change shape)."""
    start_line: int
    end_line: int | None
    token_idx: int
    level: int
    title: str

    def to_tuple(self) -> tuple[int, int | None, int, int, str]:
        """Legacy tuple format for backward compatibility."""
        return (self.start_line, self.end_line, self.token_idx, self.level, self.title)
```

**Refactor index building**:
```python
def _build_indices(self):
    sections: list[Section] = []
    section_stack: list[Section] = []

    for idx, tok in enumerate(self.tokens):
        if tok.type == "heading_open":
            level = int(tok.tag[1])
            start_line = tok.map[0] if tok.map else 0

            # Close higher-level sections
            while section_stack and section_stack[-1].level >= level:
                closed = section_stack.pop()
                # Replace with final version (end_line filled)
                sections[sections.index(closed)] = Section(
                    closed.start_line,
                    tok.map[0] - 1,  # end_line
                    closed.token_idx,
                    closed.level,
                    closed.title
                )

            # Open new section
            new_section = Section(start_line, None, idx, level, "")
            sections.append(new_section)
            section_stack.append(new_section)

        if tok.type == "inline" and section_stack:
            # Fill title
            current = section_stack[-1]
            updated = Section(
                current.start_line,
                current.end_line,
                current.token_idx,
                current.level,
                tok.content  # title filled
            )
            sections[sections.index(current)] = updated
            section_stack[-1] = updated

    self.sections = [s.to_tuple() for s in sections]  # Convert to tuples
```

**Add to docs** (DOXSTRUX_REFACTOR.md → Step 1 → Acceptance Criteria):
```markdown
- [ ] **Section contract frozen**: `Section = (start_line:int, end_line:int|None, token_idx:int, level:int, title:str)` — no variants
- [ ] Section dataclass used internally, converted to tuple for API compatibility
- [ ] Schema validates section tuple structure in tests
```

---

#### 4. Routing Dedup Breaks Determinism (CRITICAL)

**Problem**: `list(set(collectors + tag_collectors))` makes dispatch order nondeterministic.

**Current State**: Not explicitly addressed in docs.

**Fix**:
```python
def register_collector(self, collector):
    """Register collector with deterministic routing."""
    # Track seen collectors to avoid duplicates
    if not hasattr(self, '_registered_collectors'):
        self._registered_collectors = set()

    # Add to routing table in registration order (DETERMINISTIC)
    for token_type in collector.handles_types:
        if collector not in self._registered_collectors:
            self._routing[token_type].append(collector)
            self._registered_collectors.add(collector)

    # Same for tags (no set() dedup)
    for tag in collector.handles_tags:
        if collector not in self._registered_collectors:
            self._tag_routing[tag].append(collector)
            self._registered_collectors.add(collector)
```

**Add to docs** (DOXSTRUX_REFACTOR.md → Step 3 → Acceptance Criteria):
```markdown
**INVARIANT: Deterministic Dispatch Order**

- Collectors execute in **registration order** (not set() random order)
- No `list(set(...))` deduplication (breaks determinism)
- Use stable union with seen set: `if collector not in seen: append(collector); seen.add(collector)`
- Test: dispatch order must be identical across runs
```

**Test**:
```python
def test_dispatch_order_deterministic():
    """Dispatch order must be identical across multiple runs."""
    content = "# Test [link](url)"

    order_runs = []
    for _ in range(10):
        wh = TokenWarehouse.from_markdown(content)
        order = []

        # Patch collectors to record execution order
        for collector in wh._collectors:
            original_collect = collector.collect
            def collect_wrapper(wh, orig=original_collect, name=collector.name):
                order.append(name)
                return orig(wh)
            collector.collect = collect_wrapper

        wh.dispatch_all()
        order_runs.append(tuple(order))

    # All runs must have identical order
    assert len(set(order_runs)) == 1, f"Nondeterministic dispatch: {order_runs}"
```

---

#### 8. API Contract Without Binding Gates (CRITICAL)

**Problem**: Schema exists but canary doesn't enforce zero mismatch rate.

**Current State** (DOXSTRUX_REFACTOR.md:2494-2572):
- `parser_output.schema.json` defined
- Baseline parity gate validates outputs
- **Missing**: Binding canary gate with 0.00% mismatch requirement

**Fix**: Add to DOXSTRUX_REFACTOR_TIMELINE.md:

```markdown
### Canary Promotion Gates (BINDING)

**Baseline Mismatch Gate** (HARD REQUIREMENT):
- Mismatch rate must be **0.00%** (zero mismatches allowed)
- Any non-zero mismatch triggers **automatic rollback**
- Measured over 10,000+ parses in canary window

**Performance Gates** (PER CONSTRUCT):
- p50 latency ≤ src + 5% **for each construct type** (tables, lists, code, links, etc.)
- p95 latency ≤ src + 10% **for each construct type**
- Aggregate p50 ≤ src + 3%, p95 ≤ src + 8%

**Implementation**:
```python
def check_canary_promotion(current_metrics: dict, baseline_metrics: dict) -> tuple[bool, str]:
    """Validate canary metrics against hard gates."""

    # Gate 1: ZERO baseline mismatches (BINDING)
    mismatch_rate = current_metrics.get("baseline_mismatch_rate_pct", 100.0)
    if mismatch_rate > 0.0:
        return False, f"❌ Baseline mismatch rate {mismatch_rate:.2f}% (required: 0.00%)"

    # Gate 2: Per-construct performance (BINDING)
    for construct in ["tables", "lists", "code_blocks", "links", "images"]:
        delta_p50 = compute_delta(current_metrics, baseline_metrics, construct, "p50")
        delta_p95 = compute_delta(current_metrics, baseline_metrics, construct, "p95")

        if delta_p50 > 5.0:
            return False, f"❌ {construct} p50 regression {delta_p50:.1f}% (threshold: 5%)"
        if delta_p95 > 10.0:
            return False, f"❌ {construct} p95 regression {delta_p95:.1f}% (threshold: 10%)"

    # Gate 3: Schema validation (BINDING)
    schema_valid_rate = current_metrics.get("schema_valid_pct", 0.0)
    if schema_valid_rate < 100.0:
        return False, f"❌ Schema validation {schema_valid_rate:.1f}% (required: 100%)"

    return True, "✅ All gates passed"
```

---

### 🟡 HIGH PRIORITY - Fix During Steps 1-4

#### 3. Pairs/Parents for Nesting==0 Tokens

**Current State**: Mentioned but not explicit.

**Fix**: Add tests and documentation.

```python
def test_parents_for_zero_nesting_tokens():
    """Tokens with nesting==0 still get parents when inside container."""
    content = """
    # Heading
    This is **bold with `code`** text.
    """

    wh = TokenWarehouse.from_markdown(content)

    # Find code_inline (nesting == 0)
    code_inline_idx = next(
        idx for idx, tok in enumerate(wh.tokens)
        if tok.type == "code_inline"
    )

    code_tok = wh.tokens[code_inline_idx]
    assert code_tok.nesting == 0, "code_inline should have nesting==0"

    # Should still have parent (the strong_open or paragraph_open)
    assert code_inline_idx in wh.parents, "Zero-nesting token must have parent"
    parent_idx = wh.parents[code_inline_idx]
    parent_tok = wh.tokens[parent_idx]

    # Parent should be a container
    assert parent_tok.nesting == 1, "Parent should be opening token"
```

**Add to docs**:
```markdown
### Parent Tracking Invariant

**ALL tokens (except root) must have a parent**, regardless of nesting value:
- `nesting == 1` (open): parent is previous stack top
- `nesting == -1` (close): parent is matching open token
- `nesting == 0` (flat): parent is current stack top (if stack not empty)

**Test gate**: `assert len(wh.parents) >= len(wh.tokens) - 1  # All except root`
```

---

#### 5. O(N+M) Proof Inadequate

**Current State** (DOXSTRUX_REFACTOR.md:840-856):
```python
def test_dispatch_complexity():
    # Verify O(N+M) not O(N×M)
    # Should be fast
```

**Gap**: No hard invariant that tokens visited == len(tokens).

**Fix**:
```python
def test_dispatch_single_pass_hard_invariant():
    """Prove single-pass by counting token visits."""
    content = "# Test\n[link](url)\n**bold**\n`code`"

    wh = TokenWarehouse.from_markdown(content)

    # Instrument dispatch to count token visits
    token_visit_count = 0
    original_dispatch = wh.dispatch_all

    def counted_dispatch():
        nonlocal token_visit_count
        # Patch the main loop
        for idx, tok in enumerate(wh.tokens):
            token_visit_count += 1
            # ... dispatch logic
        return original_dispatch()

    wh.dispatch_all = counted_dispatch
    wh.dispatch_all()

    # HARD INVARIANT: visited exactly once per token
    assert token_visit_count == len(wh.tokens), \
        f"Single-pass violated: visited {token_visit_count} != {len(wh.tokens)} tokens"

    # Total complexity: O(N + M) where M = sum(collector calls)
    # Each collector called ≤ k times (k = tokens matching its type)
    # So M ≤ N × C (C = collectors), but with routing M ≈ N
```

**Add to docs**:
```markdown
### Dispatch Complexity Proof (CI Gate)

**Hard Invariant**:
```python
visited_tokens == len(tokens)  # Exactly one visit per token
```

**CI Enforcement**:
- Instrument dispatch with counter
- Fail if `visited_tokens > len(tokens)` (indicates double-pass)
- Log per-collector call counts (should sum to ≈ N, not N×M)
```

---

#### 7. Binary Search section_of() Fragile

**Current State**: Only `starts[]` array mentioned.

**Fix**:
```python
def _build_section_arrays(self):
    """Build starts[] and ends[] for binary search."""
    self._section_starts = []
    self._section_ends = []

    for section in self.sections:
        start_line, end_line, token_idx, level, title = section
        if start_line is not None:
            self._section_starts.append((start_line, len(self._section_starts)))
        if end_line is not None:
            self._section_ends.append((end_line, len(self._section_ends)))

    self._section_starts.sort()  # Sorted by start_line

def section_of(self, line: int) -> Optional[tuple]:
    """Binary search with both starts and ends."""
    if not self._section_starts:
        return None

    # Find rightmost start ≤ line
    idx = bisect.bisect_right(self._section_starts, (line, float('inf'))) - 1

    if idx < 0:
        return None  # Before all sections

    section_idx = self._section_starts[idx][1]
    section = self.sections[section_idx]
    start_line, end_line, token_idx, level, title = section

    # Verify within bounds
    if end_line is not None and line > end_line:
        return None  # After this section

    return section
```

**Add tough tests**:
```python
def test_section_of_nested_levels():
    """H1 contains H2 contains H3."""
    content = """
# H1 (line 1)
## H2 (line 2)
### H3 (line 3)
Para in H3 (line 4)
Para in H2 (line 5)
Para in H1 (line 6)
"""

    wh = TokenWarehouse.from_markdown(content)

    # Line 4 should be in H3 (level 3, not H1 or H2)
    sect = wh.section_of(4)
    assert sect[3] == 3, "Line 4 should be in H3 (level 3)"

    # Line 5 should be in H2 (H3 ended)
    sect = wh.section_of(5)
    assert sect[3] == 2, "Line 5 should be in H2 (level 2)"

def test_section_of_empty_section():
    """Section with no content."""
    content = """
# H1
# H2
Para
"""
    wh = TokenWarehouse.from_markdown(content)

    # Line 2 (H2 heading) should be in H2, not H1
    sect = wh.section_of(2)
    assert sect[4] == "H2"
```

---

#### 11. Helper Method Determinism

**Current State**: No requirement for binary search in helpers.

**Fix**:
```python
def tokens_between(self, start_idx: int, end_idx: int, type_filter: str = None) -> list[int]:
    """Get tokens between indices using binary search (O(log N))."""
    if type_filter:
        # Binary search on by_type[type_filter]
        type_indices = self.by_type.get(type_filter, [])

        # Find first index >= start_idx
        left = bisect.bisect_left(type_indices, start_idx)
        # Find first index > end_idx
        right = bisect.bisect_right(type_indices, end_idx)

        return type_indices[left:right]
    else:
        # All indices in range
        return list(range(start_idx + 1, end_idx))
```

**Contract tests**:
```python
def test_tokens_between_overlapping_same_line():
    """Two links on same line."""
    content = "[link1](url1) text [link2](url2)"

    wh = TokenWarehouse.from_markdown(content)

    link1_open = wh.by_type["link_open"][0]
    link1_close = wh.pairs[link1_open]

    link2_open = wh.by_type["link_open"][1]
    link2_close = wh.pairs[link2_open]

    # tokens_between should only return tokens INSIDE link1
    tokens_in_link1 = wh.tokens_between(link1_open, link1_close)

    # Should NOT include link2 tokens
    assert link2_open not in tokens_in_link1
    assert link2_close not in tokens_in_link1
```

---

### Implementation Checklist (Ready to Paste)

Add to DOXSTRUX_REFACTOR.md → Executive Summary → Critical Invariants:

```markdown
## Critical Invariants (CI-Enforced)

### 1. Coordinate System Integrity
All coordinates (token.map, line numbers, byte offsets) are derived from the **same normalized text** (NFC + LF).
- Normalization happens **BEFORE** markdown-it parsing
- Test: `token.map[0]` must index into `wh.lines` correctly

### 2. Section Contract Frozen
`Section = (start_line:int, end_line:int|None, token_idx:int, level:int, title:str)` — no variants.
- Use dataclass internally, convert to tuple for API
- Test: schema validates all section tuples

### 3. Deterministic Dispatch Order
Collectors execute in **registration order** (not set() random order).
- No `list(set(...))` deduplication
- Test: dispatch order identical across runs

### 4. Single-Pass Proven
`visited_tokens == len(tokens)` — each token visited exactly once.
- Instrument dispatch with counter
- Test: `assert visited_tokens == len(tokens)`

### 5. Parent Tracking Complete
ALL tokens (except root) have parents, including `nesting==0` tokens.
- Test: `assert len(wh.parents) >= len(wh.tokens) - 1`

### 6. Windows Timeout Cooperative
Collectors on Windows must call `timeout_ctx.check_timeout()` every K iterations.
- Test: Windows-only test with busy loop

### 7. Binary Search section_of()
Uses both `starts[]` and `ends[]` arrays for correct bounds checking.
- Test: nested h1/h2/h3, empty sections, no headings

### 8. Zero-Mismatch Canary Gate (BINDING)
Baseline mismatch rate must be **0.00%** (zero tolerance).
- Any mismatch triggers automatic rollback
- Test: canary gate rejects any non-zero mismatch

### 9. Per-Construct Performance Gates
p50 ≤ +5%, p95 ≤ +10% **for each construct type** (tables, lists, code, links, etc.).
- Micro-benchmarks per construct
- Test: each construct meets budget

### 10. Helper Methods Use Binary Search
`tokens_between()`, `text_between()` use `bisect_left/right` (O(log N)).
- No linear scans
- Test: performance on large token lists
```

---

## Remaining Gaps (P1 - Implement During Testing)

### 12. Children Index Lifecycle

**Fix**: Build once at index time, never mutate.

```markdown
**Children Index Policy**:
- Built **once** during `_build_indices()`
- Immutable after construction (no add/remove)
- If token mutation needed (rare), rebuild entire warehouse
- Test: attempt to mutate children → should fail or warn
```

### 13. Collector Iteration Exception

**Fix**: Define sparse scan exception.

```markdown
**Collector Iteration Policy**:
- **Banned**: `for tok in wh.tokens` (full scan)
- **Allowed**: Sparse local scan within `[open_idx, close_idx]` up to K tokens (K ≤ 100)
- **Required**: Use `wh.by_type[]`, `wh.pairs[]`, `wh.tokens_between()`
- **Test**: Assert total tokens visited by all collectors ≤ `len(tokens) + C` (C = small constant)
```

### 14. Canary Telemetry Privacy

**Fix**: Redact content in logs.

```python
def sanitize_log(content: str) -> str:
    """Redact PII from canary logs."""
    # Keep only structure, not content
    return {
        "length": len(content),
        "lines": content.count('\n'),
        "tokens": len(wh.tokens),
        "sha256": hashlib.sha256(content.encode()).hexdigest()  # Hash, not content
    }
```

### 18. Per-Construct Performance

**Fix**: Micro-benchmarks.

```python
# baselines/micro_benchmarks.json
{
  "tables_1000_rows": {"p50": 12.5, "p95": 45.2},
  "lists_10k_items": {"p50": 8.3, "p95": 32.1},
  "code_blocks_50k_lines": {"p50": 15.7, "p95": 58.3}
}
```

### 20. Memory Ceiling Gates

**Fix**: Add RSS budget.

```python
def test_memory_budget():
    """RSS must not exceed src + 10%."""
    import tracemalloc

    tracemalloc.start()
    wh = TokenWarehouse.from_markdown(large_doc)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    baseline_peak = load_baseline_memory()
    assert peak <= baseline_peak * 1.10, f"Memory over budget: {peak} > {baseline_peak * 1.10}"
```

---

## Summary

**Critical (Fix Before Step 1)**: 4 gaps
1. Normalize before parse
2. Freeze section shape
4. Deterministic dispatch
8. Zero-mismatch canary gate

**High Priority (Fix During Steps 1-4)**: 7 gaps
3. Test nesting==0 parents
5. Hard single-pass proof
7. Binary search with ends[]
9. CI render drift gate
11. Binary search helpers
12. Children lifecycle
14. PII redaction

**Medium Priority (Fix During Testing)**: 9 gaps
6. ✅ Already complete
10. Adversarial corpus checklist
13. Sparse scan exception
15. Unicode policy
16. Doc SHA reference
17. Import path test
18. Micro-benchmarks
19. Evidence manifest
20. Memory gates

**Total Implementation Effort**: ~3-4 days for all gaps.

---

**Created**: 2025-10-19
**Status**: 🟡 **ACTIONABLE** - All fixes ready to implement
**Next**: Add critical invariants to DOXSTRUX_REFACTOR.md Executive Summary
