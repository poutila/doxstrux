# Phase 8 Security Hardening & Performance Checklist

**Version**: 1.0
**Created**: 2025-10-15
**Source**: Deep security/performance review
**Status**: Ready for implementation

---

## Purpose

This checklist applies **surgical security hardening** and **micro-performance optimizations** to the Phase 8 Token Warehouse implementation. All changes are:

- **Zero or positive performance impact** (no tax on hot paths)
- **Runtime correctness focused** (prevent silent failures)
- **Measurable** (each item has clear test/verification)

---

## Part 1: Security (Surgical, Zero Perf Tax)

### 1.1 Scheme Allowlist at Collector Edge

**Current State**: Scheme validation may be scattered or incomplete.

**Target State**: Explicit allowlist enforced inside `LinksCollector` and `ImagesCollector` only.

**Implementation**:

```python
# In skeleton/doxstrux/markdown/collectors_phase8/links.py

ALLOWED_SCHEMES = {"http", "https", "mailto", "tel"}

class LinksCollector:
    def __init__(self, allowed_schemes: set[str] | None = None):
        self.name = "links"
        self.allowed_schemes = allowed_schemes or ALLOWED_SCHEMES
        # ... rest of init

    def _is_allowed_scheme(self, url: str) -> bool:
        """Check if URL scheme is in allowlist.

        Returns True for relative URLs (no scheme).
        """
        if ":" not in url:
            return True  # Relative URL
        scheme = url.split(":", 1)[0].lower()
        return scheme in self.allowed_schemes

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        if token.type == "link_open":
            href = token.attrGet("href") or ""
            if not self._is_allowed_scheme(href):
                # Skip this link entirely (or mark as disallowed)
                return
            # ... rest of processing
```

**Why**: Collectors are the **edge** of data ingestion. Enforce security here, not in hot dispatch loop.

**Test**:
```python
def test_links_scheme_allowlist():
    tokens = mock_tokens_with_link("javascript:alert(1)")
    wh = TokenWarehouse(tokens, None)
    col = LinksCollector(allowed_schemes={"http", "https"})
    wh.register_collector(col)
    wh.dispatch_all()
    links = wh.finalize_all()["links"]
    assert len(links) == 0  # javascript: blocked
```

**Status**: ⬜ Not implemented
**Estimated time**: 15 minutes
**Priority**: HIGH (security)

---

### 1.2 HTML Boundary Documentation

**Current State**: HTML collection behavior may be ambiguous.

**Target State**: Explicit invariant documented in warehouse and collectors.

**Implementation**:

Add to `TokenWarehouse` docstring:
```python
class TokenWarehouse:
    """
    Single-pass token router with precomputed indices.

    Invariants:
    - sections sorted by start_line (strictly increasing)
    - pairs[open] = close with open < close
    - line_count == len(lines) when text provided; else inferred from token maps
    - **HTML Safety**: All HTML collected here (html_inline, html_block) is INERT DATA.
      Any rendering/presentation MUST sanitize downstream with strict allowlist.
      This layer never interprets or renders HTML.
    """
```

Add to README:
```markdown
### Security Model

**HTML Collection**: The warehouse collects `html_inline` and `html_block` tokens verbatim as
**unrendered, inert data**. It does NOT sanitize or validate HTML. Any downstream rendering MUST:

1. Use a strict allowlist sanitizer (e.g., `bleach` with minimal tags)
2. Never render HTML directly in security-sensitive contexts
3. Treat all collected HTML as untrusted user input

**Path Resolution**: The warehouse does NOT resolve file paths or access the filesystem.
All link/image URLs are collected as-is. Path validation is the responsibility of downstream consumers.
```

**Why**: Makes security boundary **explicit** and **documented**.

**Test**: Documentation review (no code changes).

**Status**: ⬜ Not implemented
**Estimated time**: 10 minutes
**Priority**: MEDIUM (documentation)

---

### 1.3 Hard Caps with Structural Invariants

**Current State**: Token/byte limits exist, but structural invariants not explicitly tested.

**Target State**: Add explicit assertions in tests to prevent accidental DoS.

**Implementation**:

```python
# In tests/test_token_warehouse.py

def test_invariants_sections_non_overlapping():
    """Verify sections are strictly non-overlapping (DoS prevention)."""
    tokens = mock_tokens_with_many_headings(100)  # Generate 100 headings
    wh = TokenWarehouse(tokens, None)

    sections = wh.sections_list()

    # Sections strictly increasing (no overlap)
    for i in range(1, len(sections)):
        _, prev_start, prev_end, _, _ = sections[i-1]
        _, curr_start, curr_end, _, _ = sections[i]
        assert prev_end < curr_start, f"Overlap: section {i-1} ends at {prev_end}, section {i} starts at {curr_start}"

def test_invariants_pairs_legal():
    """Verify pairs are legal (open < close, both valid indices)."""
    tokens = mock_tokens_with_nested_blocks(50)
    wh = TokenWarehouse(tokens, None)

    pairs = wh.pairs
    n = len(wh.tokens)

    for open_idx, close_idx in pairs.items():
        assert 0 <= open_idx < n, f"Open index {open_idx} out of bounds"
        assert 0 <= close_idx < n, f"Close index {close_idx} out of bounds"
        assert open_idx < close_idx, f"Pair ordering broken: open={open_idx}, close={close_idx}"
```

**Why**: Prevents malformed structures from causing infinite loops or O(N²) behavior.

**Test**: Run the tests above.

**Status**: ⬜ Not implemented
**Estimated time**: 20 minutes
**Priority**: HIGH (correctness)

---

### 1.4 Fault Isolation (Prod vs Test)

**Current State**: Collector errors may crash entire parse.

**Target State**: In production, catch and log collector errors; in tests, re-raise.

**Implementation**:

```python
# In token_warehouse.py

import os
import logging

RAISE_ON_COLLECTOR_ERROR = os.getenv("RAISE_ON_COLLECTOR_ERROR", "0") == "1"

class TokenWarehouse:
    def dispatch_all(self) -> None:
        # ... existing setup ...

        for i, tok in enumerate(tokens):
            # ... existing nesting logic ...

            for col in cols:
                # ... existing filter logic ...

                try:
                    col.on_token(i, tok, ctx, self)
                except Exception as e:
                    if RAISE_ON_COLLECTOR_ERROR:
                        raise  # Re-raise in test mode
                    else:
                        # Log and continue in production
                        logging.warning(
                            f"Collector {col.name} failed on token {i} (type={ttype}): {e}",
                            exc_info=True
                        )
```

**Why**: Single collector bug doesn't kill entire parse; easier debugging in production.

**Test**:
```python
def test_fault_isolation_collector_error():
    """Verify collector errors are caught in production mode."""
    class BrokenCollector:
        name = "broken"
        interest = Interest(types={"paragraph_open"})
        def should_process(self, *args): return True
        def on_token(self, *args): raise ValueError("Boom!")
        def finalize(self, wh): return []

    tokens = mock_tokens_with_paragraphs(5)
    wh = TokenWarehouse(tokens, None)
    wh.register_collector(BrokenCollector())

    # Should not raise in production mode (RAISE_ON_COLLECTOR_ERROR=0)
    wh.dispatch_all()  # Logs warning, doesn't crash
```

**Status**: ⬜ Not implemented
**Estimated time**: 15 minutes
**Priority**: MEDIUM (robustness)

---

## Part 2: Runtime Correctness (Things That Silently Rot)

### 2.1 Parent Mapping Order

**Current State**: ✅ Already correct (line 100-102 in warehouse)

```python
# Assign parent BEFORE mutating stack for this token
if open_stack:
    parents[i] = open_stack[-1]
```

**Why**: This is the **only stable rule** across weird nesting. Keep this invariant.

**Status**: ✅ Verified correct
**Action**: Add docstring to lock this rule

```python
def _build_indices(self) -> None:
    """Build all indices in single pass.

    **Invariant**: Parent assignment happens BEFORE stack mutation to ensure
    every token gets assigned to the correct parent block, even with
    unconventional nesting (e.g., inline tokens between block open/close).
    """
```

**Estimated time**: 5 minutes
**Priority**: LOW (already correct, just document)

---

### 2.2 Section Builder Complexity Lock

**Current State**: ✅ O(H) stack algorithm already implemented (lines 119-148)

**Action**: Add explicit docstring about markdown-it map convention

```python
def _build_sections(self) -> None:
    """Build section ranges from headings using O(H) stack algorithm.

    **Invariant**: markdown-it token.map is [start_incl, end_excl].
    To create inclusive section ranges, we close previous section at (start - 1).

    Example:
        Heading 1 at line 0 (map=[0,1])
        Heading 2 at line 5 (map=[5,6])
        → Section 1: [0, 4] (inclusive, closed at 5-1=4)
        → Section 2: [5, end] (inclusive)

    Complexity: O(H) where H = number of headings (single pass with stack).
    """
```

**Status**: ⬜ Docstring missing
**Estimated time**: 5 minutes
**Priority**: MEDIUM (documentation)

---

### 2.3 Binary section_of() Correctness

**Current State**: ✅ Already using `bisect_right` (lines 166-176)

**Action**: Verify `_section_starts` is rebuilt if sections changes (currently built once in `_build_sections` - GOOD)

**Invariant to document**:
```python
def _build_sections(self) -> None:
    # ... after building sections ...

    # INVARIANT: _section_starts must stay in sync with sections.
    # Rebuild whenever sections list changes (currently immutable after init - good).
    self._section_starts = [s for _, s, _, _, _ in self.sections]
```

**Status**: ✅ Correct, needs docstring
**Estimated time**: 5 minutes
**Priority**: LOW (already correct)

---

### 2.4 Fence Inventory Explicit Format

**Current State**: Fences stored as tuple, but format not explicitly documented.

**Action**: Make format explicit in type hint and docstring

```python
# Line 63 in warehouse
self.fences: List[Tuple[int, int, str, str]] = []  # EXISTING

# Add docstring:
"""
Fence inventory: List[(start_incl, end_excl, lang, raw_info)]

- start_incl: Starting line (inclusive)
- end_excl: Ending line (EXCLUSIVE, per markdown-it convention)
- lang: Parsed language identifier (stripped)
- raw_info: Original info string (with whitespace)

Example:
    ```python  # Line 10-13
    → (10, 13, "python", "python")
"""
```

**Status**: ⬜ Documentation missing
**Estimated time**: 5 minutes
**Priority**: MEDIUM (prevents off-by-one errors)

---

### 2.5 Collector Ordering & Idempotence

**Current State**: ✅ Already freezing routing to tuples (line 184)

```python
self._routing[ttype] = tuple([*prev, collector]) if prev else (collector,)
```

**Action**: Also freeze `_collectors` to tuple after registration closes

```python
class TokenWarehouse:
    def __init__(self, ...):
        # ... existing init ...
        self._collectors: List[Collector] = []  # Mutable during registration
        self._registration_closed = False  # NEW

    def register_collector(self, collector: Collector) -> None:
        if self._registration_closed:
            raise RuntimeError("Cannot register collectors after dispatch_all() called")
        # ... existing registration ...

    def dispatch_all(self) -> None:
        if not self._registration_closed:
            self._collectors = tuple(self._collectors)  # Freeze
            self._registration_closed = True
        # ... existing dispatch ...
```

**Why**: Prevents accidental mutation and ensures deterministic ordering.

**Status**: ⬜ Not implemented
**Estimated time**: 10 minutes
**Priority**: LOW (nice-to-have for determinism)

---

## Part 3: Raw Speed (Measurable Wins)

### 3.1 Hot Loop - Already Optimized ✅

**Current State**: Lines 193-226 already have:
- ✅ Local variable binding (`tokens`, `routing`, `open_types`, etc.)
- ✅ O(1) ignore-mask with bitmasks
- ✅ Nullable `should_process` (line 223-225)
- ✅ Early exits

**Status**: ✅ Complete
**Action**: None needed (best practices already applied)

---

### 3.2 SoA (Structure of Arrays) - Optional

**When to apply**: Only if profiling shows token attribute access is bottleneck (unlikely).

**Implementation** (DEFERRED until profiling):

```python
# Add to TokenWarehouse.__init__()
def __init__(self, tokens, tree, text=None):
    # ... existing init ...

    # SoA optimization (only if profiling warrants it)
    if os.getenv("USE_SOA_CACHE", "0") == "1":
        self._type_ids: List[int] = []
        self._nesting_vals: List[int] = []
        self._map_starts: List[int] = []
        self._map_ends: List[int] = []
        self._intern_types: Dict[str, int] = {}

        for tok in tokens:
            ttype = getattr(tok, "type", "")
            if ttype not in self._intern_types:
                self._intern_types[ttype] = len(self._intern_types)
            self._type_ids.append(self._intern_types[ttype])
            self._nesting_vals.append(getattr(tok, "nesting", 0))
            m = getattr(tok, "map", None) or (0, 0)
            self._map_starts.append(m[0])
            self._map_ends.append(m[1])
```

**Status**: ⬜ Deferred (profile first)
**Estimated time**: 1 hour (if needed)
**Priority**: LOW (only if profiler says so)

---

### 3.3 Pre-size Collector Outputs

**Implementation**:

```python
# In collectors (e.g., links.py, headings.py)

class LinksCollector:
    def __init__(self, ...):
        # ... existing init ...
        self._links: list[dict] | None = None  # Lazy init

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        # Lazy init on first use (now we have access to wh)
        if self._links is None:
            # Pre-size based on index count
            n_link_open = len(wh.by_type.get("link_open", []))
            self._links = [None] * n_link_open  # Pre-allocate
            self._link_idx = 0

        # ... rest of logic, filling self._links[self._link_idx] ...

    def finalize(self, wh: TokenWarehouse) -> list[dict]:
        if self._links is None:
            return []
        # Strip unfilled slots (if any early exits happened)
        return [x for x in self._links if x is not None]
```

**Why**: Avoids repeated list resizing (minor win, ~2-5% on link-heavy docs).

**Status**: ⬜ Not implemented
**Estimated time**: 20 minutes
**Priority**: LOW (micro-optimization)

---

### 3.4 Text Accumulation with list.join

**Current pattern** (ANTI-PATTERN):
```python
text = ""
for tok in tokens:
    text += tok.content  # BAD: O(N²) string copies
```

**Correct pattern**:
```python
buf = []
for tok in tokens:
    buf.append(tok.content)
text = "".join(buf)  # GOOD: O(N) single allocation
```

**Action**: Audit all collectors for += on strings in loops.

**Status**: ⬜ Needs audit
**Estimated time**: 15 minutes
**Priority**: MEDIUM (common performance bug)

---

## Part 4: Style & Maintainability

### 4.1 Intent-Revealing Names

**Changes**:
- `stack` → `open_types` ✅ (already done, line 196)
- `current_mask` → `open_mask` ✅ (already done, line 198)
- `_mask_map` → `type_to_maskbit` ❌ (NOT done)

**Action**:
```python
# Rename in TokenWarehouse
self._mask_map → self.type_to_maskbit
self._collector_masks → self.collector_ignore_masks
```

**Status**: ⬜ Not applied
**Estimated time**: 10 minutes
**Priority**: LOW (readability)

---

### 4.2 Invariants at Top of Class

**Current State**: Some invariants in docstring (line 36-42), but not complete.

**Action**: Expand docstring with all invariants

```python
class TokenWarehouse:
    """
    Single-pass token router with precomputed indices.

    **Structural Invariants**:
    1. sections: Sorted by start_line (strictly increasing), non-overlapping
    2. pairs: Legal pairings only (open < close, both valid indices)
    3. parents: All tokens except top-level have parent assigned
    4. line_count: Equals len(lines) when text provided, else inferred from max(token.map[1])

    **Security Invariants**:
    5. HTML: All html_inline/html_block collected as INERT DATA (not rendered)
    6. Paths: No filesystem access; URLs/paths collected verbatim

    **Performance Characteristics**:
    - Index building: O(N) where N = token count
    - Section building: O(H) where H = heading count
    - dispatch_all(): O(N × C_avg) where C_avg ≈ 2-3 collectors/token
    - section_of(): O(log H) via binary search
    """
```

**Status**: ⬜ Needs expansion
**Estimated time**: 10 minutes
**Priority**: MEDIUM (living documentation)

---

### 4.3 Small Public Surface

**Current API** (lines 151-176):
- ✅ `iter_by_type()`
- ✅ `range_for()`
- ✅ `parent()`
- ✅ `section_of()`
- ✅ `sections_list()`
- ✅ `fences_list()`
- ✅ `register_collector()`
- ✅ `dispatch_all()`
- ✅ `finalize_all()`
- ✅ `debug_dump_sections()`

**Action**: Mark everything else as private (prefix with `_`).

**Status**: ✅ Already done (only public methods exposed)

---

### 4.4 Tests That Catch Regressions

**Required test cases**:

```python
def test_no_headings_empty_sections():
    """Documents without headings should have empty sections list."""
    tokens = mock_tokens_no_headings()
    wh = TokenWarehouse(tokens, None)
    assert wh.sections_list() == []
    assert wh.section_of(0) is None
    assert wh.section_of(100) is None

def test_links_inside_fences_ignored():
    """Links inside code fences should be ignored by LinksCollector."""
    tokens = mock_tokens_fence_with_link()
    wh = TokenWarehouse(tokens, None)
    col = LinksCollector()
    wh.register_collector(col)
    wh.dispatch_all()
    links = wh.finalize_all()["links"]
    assert len(links) == 0  # Link ignored (inside fence)

def test_mixed_newlines():
    """Mixed \n and \r\n should produce same section boundaries."""
    text_unix = "# H1\n\nPara\n\n## H2\n"
    text_win = "# H1\r\n\r\nPara\r\n\r\n## H2\r\n"

    wh1 = TokenWarehouse(parse(text_unix), None, text=text_unix)
    wh2 = TokenWarehouse(parse(text_win), None, text=text_win)

    # Same section structure (line numbers may differ due to \r\n)
    assert len(wh1.sections_list()) == len(wh2.sections_list())

def test_fuzz_random_headings():
    """Randomized heading levels should never produce overlapping sections."""
    for _ in range(100):  # 100 random docs
        tokens = generate_random_headings(n=20, max_level=6)
        wh = TokenWarehouse(tokens, None)
        sections = wh.sections_list()

        # Verify non-overlap
        for i in range(1, len(sections)):
            _, prev_start, prev_end, _, _ = sections[i-1]
            _, curr_start, curr_end, _, _ = sections[i]
            assert prev_end < curr_start

        # Verify binary search correctness
        for i, (_, start, end, _, _) in enumerate(sections):
            for line in range(start, end + 1):
                assert wh.section_of(line) == f"section_{i}"
```

**Status**: ⬜ Not implemented
**Estimated time**: 1 hour
**Priority**: HIGH (prevents regressions)

---

### 4.5 Minimal Feature Flags

**Recommended flags**:
- ✅ `USE_WAREHOUSE` (already exists, for A/B testing during migration)
- 🆕 `RAISE_ON_COLLECTOR_ERROR` (from item 1.4)
- ❌ No more flags unless backed by perf data

**Status**: Partially complete
**Action**: Add `RAISE_ON_COLLECTOR_ERROR` (see item 1.4)

---

## Implementation Priority

### Must-Have (Before Phase 8.1)
1. ✅ 1.1: Scheme allowlist in collectors
2. ✅ 1.3: Structural invariant tests
3. ✅ 2.4: Fence format documentation
4. ✅ 4.4: Regression test suite (no-headings, fences, fuzz)

### Should-Have (Before Phase 8.Final)
5. ✅ 1.2: HTML boundary documentation
6. ✅ 1.4: Fault isolation
7. ✅ 2.2: Section builder docstring
8. ✅ 3.4: Text accumulation audit
9. ✅ 4.2: Complete invariants docstring

### Nice-to-Have (Future optimization)
10. ⬜ 2.5: Freeze collectors tuple
11. ⬜ 3.2: SoA cache (only if profiler says so)
12. ⬜ 3.3: Pre-size collector outputs
13. ⬜ 4.1: Rename `_mask_map` → `type_to_maskbit`

---

## Verification Commands

After implementing each item:

```bash
# Run regression tests
pytest tests/test_token_warehouse.py -v

# Run baseline parity
.venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs

# Profile hot loops
python tools/profile_collectors.py

# Or with scalene (more detailed):
scalene -m tools.profile_collectors
```

---

## Completion Checklist

- [ ] All MUST-HAVE items implemented
- [ ] All SHOULD-HAVE items implemented
- [ ] Regression tests pass (100%)
- [ ] Baseline parity maintained (542/542)
- [ ] Profile confirms no perf regression
- [ ] Documentation updated (invariants, security model)

---

**Last Updated**: 2025-10-15
**Status**: Ready for implementation
**Estimated Total Time**: 4-6 hours

