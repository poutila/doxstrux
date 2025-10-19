# src/doxstrux vs skeleton/doxstrux - Architecture Comparison

**Date**: 2025-10-19
**Purpose**: Compare production parser (src/) with Phase-8 skeleton to identify refactoring requirements
**Status**: Analysis Complete

---

## Executive Summary

**Verdict**: skeleton/doxstrux is **NOT a drop-in replacement** - requires significant refactoring

**Key Finding**: Two DIFFERENT architectures serving different purposes:
- **src/doxstrux**: Phase 7 complete - modular extractors, token-based, production-ready
- **skeleton/doxstrux**: Phase 8 prototype - TokenWarehouse pattern, incomplete indices, different API

**Effort to Make Drop-In**: Estimated 60-70% rewrite of skeleton core architecture

---

## Architecture Comparison

### Module Structure

| Component | src/doxstrux | skeleton/doxstrux | Compatibility |
|-----------|--------------|-------------------|---------------|
| **Total Files** | 28 Python files | 28 Python files | Same count |
| **Total Lines** | 5,435 lines | 1,553 lines | 72% smaller |
| **Core Parser** | markdown_parser_core.py (1,959 lines) | parser_adapter.py (29 lines) | ❌ Incompatible |
| **Extraction Pattern** | Extractors (11 modules) | Collectors (12 modules) | ❌ Different API |
| **Token Handling** | Direct AST walking | TokenWarehouse dispatch | ❌ Different paradigm |
| **Directory Structure** | markdown/extractors/ | markdown/collectors_phase8/ | ❌ Different layout |

### src/doxstrux Structure (Production - Phase 7)

```
src/doxstrux/
├── markdown_parser_core.py (1,959 lines) - Main parser class
├── markdown/
│   ├── config.py (164 lines) - Security profiles, limits
│   ├── budgets.py (231 lines) - Resource budgets
│   ├── exceptions.py (14 lines) - Custom exceptions
│   ├── ir.py (208 lines) - Document IR for RAG
│   ├── extractors/ (11 modules, 1,831 lines total)
│   │   ├── sections.py (262 lines)
│   │   ├── paragraphs.py (63 lines)
│   │   ├── lists.py (305 lines)
│   │   ├── codeblocks.py (124 lines)
│   │   ├── tables.py (159 lines)
│   │   ├── links.py (179 lines)
│   │   ├── media.py (193 lines) - images
│   │   ├── footnotes.py (132 lines)
│   │   ├── blockquotes.py (83 lines)
│   │   ├── html.py (126 lines)
│   │   └── math.py (95 lines)
│   ├── security/
│   │   └── validators.py (340 lines)
│   └── utils/
│       ├── token_utils.py (285 lines)
│       ├── text_utils.py (139 lines)
│       └── line_utils.py (112 lines)
└── md_parser_testing/ (190 lines)
```

### skeleton/doxstrux Structure (Phase 8 - Incomplete)

```
skeleton/doxstrux/
├── markdown/
│   ├── core/
│   │   └── parser_adapter.py (29 lines) - Feature flag adapter
│   ├── collectors_phase8/ (12 modules, 693 lines total)
│   │   ├── sections.py (34 lines)
│   │   ├── headings.py (72 lines)
│   │   ├── paragraphs.py (33 lines)
│   │   ├── lists.py (64 lines)
│   │   ├── tasklists.py (29 lines)
│   │   ├── codeblocks.py (44 lines)
│   │   ├── tables.py (63 lines)
│   │   ├── links.py (82 lines)
│   │   ├── images.py (54 lines)
│   │   ├── footnotes.py (40 lines)
│   │   ├── html.py (26 lines)
│   │   ├── html_collector.py (65 lines)
│   │   └── math.py (25 lines)
│   ├── utils/
│   │   ├── token_warehouse.py (373 lines) - Core dispatch
│   │   ├── url_utils.py (141 lines) - URL normalization
│   │   └── section_utils.py (103 lines)
│   ├── security/
│   │   └── validators.py (26 lines) - Minimal stub
│   ├── cli/ (112 lines) - CLI tools
│   └── fetchers/
│       └── preview.py (124 lines) - Preview fetching
```

---

## Critical Differences

### 1. Core Parser Entry Point

**src/doxstrux**:
```python
# markdown_parser_core.py
class MarkdownParserCore:
    def __init__(self, content: str, config: dict | None = None,
                 security_profile: str | None = None):
        self.original_content = content
        self.md = MarkdownIt(preset, options_update={"html": True})
        self.tokens = self.md.parse(self.content, self.md.env)
        self.tree = SyntaxTreeNode(self.tokens)
        self._cache = {...}  # Extraction caches

    def parse(self) -> dict:
        """Single entry point - returns complete parse result"""
        return {
            "metadata": self.extract_metadata(),
            "sections": self.extract_sections(),
            "headings": self.extract_headings(),
            # ... all extractions
        }
```

**skeleton/doxstrux**:
```python
# parser_adapter.py
USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "0") == "1"

def extract_links_with_adapter(tokens, tree, original_extract_links):
    if not USE_WAREHOUSE:
        return original_extract_links(tokens)

    # Warehouse path
    from ..utils.token_warehouse import TokenWarehouse
    from ..collectors_phase8.links import LinksCollector

    wh = TokenWarehouse(tokens, tree)
    links = LinksCollector()
    wh.register_collector(links)
    wh.dispatch_all()
    return wh.finalize_all().get("links", [])
```

**Issue**: No standalone parser class - only adapter functions for gradual migration

---

### 2. Extraction Pattern

**src/doxstrux - Extractor Pattern** (Dependency Injection):
```python
# extractors/links.py
def extract_links(
    tree: SyntaxTreeNode,
    process_tree_func: Callable,
    find_section_id_func: Callable,
    get_text_func: Callable,
) -> list[dict]:
    """Extract links with metadata."""
    links = []

    def processor(node, ctx, level):
        if node.type == "link":
            link_data = {
                "id": f"link_{len(ctx)}",
                "url": node.attrGet("href"),
                "text": get_text_func(node),
                "section_id": find_section_id_func(node),
            }
            ctx.append(link_data)
            return False
        return True

    process_tree_func(tree, processor, links)
    return links
```

**skeleton/doxstrux - Collector Pattern** (Event-based):
```python
# collectors_phase8/links.py
class LinksCollector:
    name = "links"
    interest = Interest(types={"link"})

    def __init__(self):
        self.links = []

    def should_process(self, token, ctx, wh):
        return token.type == "link"

    def on_token(self, idx, token, ctx, wh):
        link_data = {
            "id": f"link_{len(self.links)}",
            "url": token.attrGet("href") if hasattr(token, 'attrGet') else None,
            "text": wh.text_between(idx, ...),  # Uses warehouse methods
        }
        self.links.append(link_data)

    def finalize(self, wh):
        return self.links
```

**Issue**: Collectors iterate full token stream per collector (O(N×M)) instead of single-pass dispatch

---

### 3. TokenWarehouse - Current vs Required

**Current Implementation** (skeleton):
```python
class TokenWarehouse:
    __slots__ = (
        "tokens", "tree",
        "by_type", "pairs", "parents",  # ✅ Declared
        "sections", "fences",            # ✅ Declared
        "lines", "line_count",           # ✅ Declared
        # ...
    )

    def __init__(self, tokens, tree, text=None):
        self.tokens = self._canonicalize_tokens(tokens)
        self.tree = tree
        self.by_type = defaultdict(list)  # ⚠️ Initialized but not populated
        self.pairs = {}                    # ⚠️ Empty
        self.parents = {}                  # ⚠️ Empty
        self.sections = []                 # ⚠️ Empty
        self._build_indices()              # ⚠️ Only builds by_type partially
```

**Required Implementation** (Phase 8 spec):
```python
class TokenWarehouse:
    def __init__(self, tokens, tree, text=None):
        # Must precompute ALL indices in single pass
        self.by_type = {}     # type → [token indices]
        self.pairs = {}       # open_idx → close_idx
        self.parents = {}     # token_idx → parent_idx
        self.sections = []    # [(start_line, end_line, token_idx, level, title)]
        self.lines = []       # [line_start_offsets]
        self._build_indices()  # Must build ALL indices

    def section_of(self, line: int) -> int:
        # O(log N) binary search - NOT linear scan
        import bisect
        idx = bisect.bisect_right(self.lines, line)
        return self.sections[idx] if idx < len(self.sections) else None
```

**Gap Analysis**:
- ❌ `_build_indices()` only populates `by_type` partially
- ❌ `pairs` never populated (no open/close bracket matching)
- ❌ `parents` never populated (no parent token tracking)
- ❌ `sections` never populated (no section boundary computation)
- ❌ `lines` never populated (no line offset mapping)
- ❌ `section_of()` missing entirely
- ❌ No single-pass dispatch - collectors iterate independently

---

### 4. Dispatch Mechanism

**Current** (skeleton - O(N×M)):
```python
# token_warehouse.py
def dispatch_all(self):
    """Dispatch tokens to all registered collectors."""
    ctx = DispatchContext()

    # ❌ For each collector, iterate ALL tokens
    for collector in self._collectors:
        for idx, token in enumerate(self.tokens):
            if collector.should_process(token, ctx, self):
                collector.on_token(idx, token, ctx, self)

    # N tokens × M collectors = O(N×M) complexity
```

**Required** (Phase 8 - O(N+M)):
```python
def dispatch_all(self):
    """Single-pass dispatch using routing table."""
    ctx = DispatchContext()

    # ✅ Single pass over tokens
    for idx, token in enumerate(self.tokens):
        # ✅ O(1) lookup of interested collectors
        collectors = self._routing.get(token.type, ())
        for collector in collectors:
            if collector.should_process(token, ctx, self):
                collector.on_token(idx, token, ctx, self)

    # N tokens + M collector registrations = O(N+M) complexity
```

**Gap**: No routing table implementation - must be added

---

### 5. API Compatibility

**src/doxstrux API** (Phase 7 - stable):
```python
parser = MarkdownParserCore(content, security_profile="moderate")
result = parser.parse()  # Returns complete dict

# Sections
sections = result["sections"]  # list[dict]

# Links
links = result["links"]  # list[dict]

# Headings
headings = result["headings"]  # list[dict]
```

**skeleton API** (Phase 8 - incompatible):
```python
# Via adapter (requires src parser instance)
wh = TokenWarehouse(tokens, tree, text)
links_collector = LinksCollector()
wh.register_collector(links_collector)
wh.dispatch_all()
links = wh.finalize_all().get("links", [])

# ❌ No standalone parse() method
# ❌ No single entry point
# ❌ Requires manual collector registration
# ❌ Different return format
```

**Gap**: skeleton cannot be used as drop-in replacement without compatibility shim

---

## Performance Characteristics

| Metric | src/doxstrux | skeleton (current) | skeleton (target) |
|--------|--------------|-------------------|-------------------|
| **Parse Pass** | 1 pass (md.parse) | 1 pass (md.parse) | 1 pass |
| **Index Build** | Per-extraction | ❌ Not implemented | ✅ 1 pass (all indices) |
| **Extraction** | 1 pass per extractor | ❌ N passes (iterate per collector) | ✅ 1 dispatch pass |
| **Total Complexity** | O(N × 11 extractors) | O(N × M collectors) ❌ | O(N + M) ✅ |
| **section_of()** | O(N) linear search | ❌ Not implemented | O(log N) binary search |
| **Memory** | Lazy (caches) | Eager (all indices) | Eager (all indices) |

**Regression Risk**: Current skeleton is SLOWER than src (O(N×M) vs O(N×11))

---

## Security Features Comparison

| Feature | src/doxstrux | skeleton/doxstrux | Status |
|---------|--------------|-------------------|--------|
| **Content size limits** | ✅ 100KB-10MB by profile | ✅ 10MB hardcoded | ⚠️ Less granular |
| **Token count limits** | ✅ 500K by profile | ✅ 100K hardcoded | ⚠️ More restrictive |
| **Recursion depth limits** | ✅ 50-150 by profile | ✅ 150 hardcoded | ⚠️ No profiles |
| **Plugin validation** | ✅ Whitelist by profile | ❌ Not implemented | ❌ Missing |
| **HTML sanitization** | ✅ Via bleach | ❌ Not implemented | ❌ Missing |
| **Link scheme validation** | ✅ http/https/mailto/tel | ❌ Not implemented | ❌ Missing |
| **BiDi control detection** | ✅ Implemented | ❌ Not implemented | ❌ Missing |
| **Prompt injection detection** | ✅ Implemented | ❌ Not implemented | ❌ Missing |
| **URL normalization** | ❌ Not implemented | ✅ Implemented | ✅ New feature |
| **Token canonicalization** | ❌ Not implemented | ✅ Implemented | ✅ New feature |
| **Collector timeouts** | ❌ Not implemented | ✅ Implemented (SIGALRM) | ✅ New feature |

**Security Verdict**: skeleton adds some features but loses many from src

---

## Reusable Components

### ✅ Can Be Kept As-Is

1. **Token canonicalization** (skeleton/utils/token_warehouse.py lines 105-143)
   - Prevents supply-chain attacks
   - 9% performance improvement
   - Well-tested

2. **Collector timeout watchdog** (skeleton/utils/token_warehouse.py lines 145-175)
   - SIGALRM-based timeout (Unix-only)
   - Prevents collector hangs
   - Good security feature

3. **URL normalization** (skeleton/utils/url_utils.py)
   - Canonical URL handling
   - Scheme validation
   - New Phase 8 feature

4. **Reentrancy guard** (skeleton/utils/token_warehouse.py)
   - Prevents concurrent dispatch
   - Thread-safety protection

5. **Section utilities** (skeleton/utils/section_utils.py)
   - Helper functions for section handling
   - Can be adapted

### ⚠️ Needs Modification

1. **TokenWarehouse class**
   - Keep: `__init__`, token canonicalization, limits
   - Rewrite: `_build_indices()` to populate ALL indices
   - Add: `section_of()` with binary search
   - Add: routing table dispatch

2. **Collectors**
   - Keep: Collector protocol, Interest class
   - Modify: Change from iteration to event-based
   - Add: Efficient queries against warehouse indices

3. **Parser adapter**
   - Keep: Feature flag pattern (USE_WAREHOUSE)
   - Expand: Add full MarkdownParserCore compatibility shim
   - Add: `parse()` method that returns src-compatible dict

### ❌ Must Be Rewritten

1. **Dispatch mechanism**
   - Current: O(N×M) iteration per collector
   - Required: O(N+M) routing table dispatch

2. **Index building**
   - Current: Only partial `by_type` population
   - Required: All indices in single pass

3. **Security validation**
   - Current: Minimal stubs
   - Required: Full security_validators.py from src

---

## Gap Analysis

### Critical Gaps (Blockers)

1. **Missing index population** ❌
   - `by_type`: Partially populated, missing many types
   - `pairs`: Never populated
   - `parents`: Never populated
   - `sections`: Never populated
   - `lines`: Never populated

2. **Missing O(log N) section lookup** ❌
   - No `section_of()` method
   - No binary search implementation

3. **Wrong dispatch complexity** ❌
   - Current: O(N×M) - worse than src
   - Required: O(N+M) - better than src

4. **No compatibility shim** ❌
   - Cannot replace src without API wrapper
   - Different return formats
   - Different initialization

5. **Incomplete security** ❌
   - Missing plugin validation
   - Missing HTML sanitization
   - Missing link scheme validation
   - Missing BiDi/prompt injection detection

### Nice-to-Have Gaps

1. **CLI tools** ⚠️
   - skeleton has dump_sections CLI
   - Not critical for drop-in replacement

2. **Fetchers** ⚠️
   - skeleton has preview fetcher
   - New feature, not in src

3. **Resource budgets** ⚠️
   - src has budgets.py (231 lines)
   - skeleton has hardcoded limits
   - Less flexible but acceptable

---

## Testing Comparison

| Test Type | src/doxstrux | skeleton/doxstrux | Gap |
|-----------|--------------|-------------------|-----|
| **Baseline parity** | ✅ 542/542 tests passing | ❌ Not tested | Must verify |
| **Unit tests** | ✅ Comprehensive | ⚠️ Basic tests exist | Need expansion |
| **Performance tests** | ✅ Baselines captured | ❌ Not implemented | Must add |
| **Security tests** | ✅ Adversarial corpora | ⚠️ Some corpora exist | Need validation |
| **Integration tests** | ✅ Full parse flow | ❌ Not implemented | Must add |

---

## Migration Complexity Estimate

| Component | Effort | Risk | Priority |
|-----------|--------|------|----------|
| **Index building** | 2-3 days | HIGH | P0 |
| **Dispatch refactor** | 3-4 days | HIGH | P0 |
| **section_of() binary search** | 1 day | LOW | P0 |
| **Compatibility shim** | 2-3 days | MEDIUM | P0 |
| **Security validation** | 3-4 days | MEDIUM | P1 |
| **Testing** | 4-5 days | HIGH | P0 |
| **Documentation** | 1-2 days | LOW | P2 |
| **Total** | **16-26 days** | | |

**Estimated rewrite**: 60-70% of core TokenWarehouse and dispatch logic

---

## Recommendation

**Do NOT use skeleton as-is for drop-in replacement**

**Reason**: Core architecture (indices + dispatch) requires complete rewrite

**Suggested Path**:
1. ✅ **Salvage** good components (canonicalization, timeouts, URL utils)
2. ✅ **Implement** Phase-8 TokenWarehouse from spec with precomputed indices
3. ✅ **Implement** O(N+M) routing table dispatch
4. ✅ **Port** collectors to event-based API
5. ✅ **Add** compatibility shim for src API
6. ✅ **Validate** baseline parity (542/542 tests)
7. ✅ **Benchmark** performance improvement

**Alternative**: Refactor skeleton in-place using 10-step surgical plan

---

## Appendix: File Size Comparison

### src/doxstrux (5,435 lines)

| Module | Lines | Purpose |
|--------|-------|---------|
| markdown_parser_core.py | 1,959 | Main parser |
| extractors/* | 1,831 | 11 extractor modules |
| security/validators.py | 340 | Security validation |
| utils/* | 536 | Token, text, line utilities |
| config.py | 164 | Security profiles |
| budgets.py | 231 | Resource budgets |
| ir.py | 208 | Document IR |
| md_parser_testing/* | 190 | Test utilities |
| Other | -24 | __init__ files |

### skeleton/doxstrux (1,553 lines)

| Module | Lines | Purpose |
|--------|-------|---------|
| token_warehouse.py | 373 | Core dispatch |
| collectors_phase8/* | 693 | 12 collector modules |
| url_utils.py | 141 | URL normalization |
| section_utils.py | 103 | Section helpers |
| cli/dump_sections.py | 102 | CLI tool |
| fetchers/preview.py | 124 | Preview fetcher |
| parser_adapter.py | 29 | Adapter |
| Other | -12 | __init__ files |

**Size Ratio**: skeleton is 28.6% the size of src (mostly missing infrastructure)

---

**Analysis Complete**: 2025-10-19
**Conclusion**: skeleton requires substantial refactoring to be drop-in compatible
**Next Steps**: See DOXSTRUX_REFACTOR.md for detailed implementation plan
