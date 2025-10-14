# Token Warehouse Optimization - Technical Specification

**Version**: 1.0
**Created**: 2025-10-14
**Status**: Phase 8.0 Specification
**Prerequisites**: Phase 7.6 complete (modular extractors)

---

## Table of Contents

- [A. Executive Summary](#a-executive-summary)
- [B. Problem Analysis](#b-problem-analysis)
- [C. Solution Architecture](#c-solution-architecture)
- [D. TokenWarehouse Design](#d-tokenwarehouse-design)
- [E. Collector Pattern](#e-collector-pattern)
- [F. Routing Algorithm](#f-routing-algorithm)
- [G. Query API](#g-query-api)
- [H. Migration Guide](#h-migration-guide)
- [I. Performance Analysis](#i-performance-analysis)
- [J. Testing Strategy](#j-testing-strategy)
- [K. Implementation Checklist](#k-implementation-checklist)

---

## A. Executive Summary

### Current Problem
The parser performs **12 independent traversals** of the token/tree structure in `parse()`, resulting in:
- **O(N × M) complexity** where N = tokens, M = extractors (12)
- **Poor cache locality** (same data accessed 12 times with other work in between)
- **Redundant lookups** (section_of, parent, type checks repeated)

### Proposed Solution
**TokenWarehouse**: Single-pass precomputed index + collector-based routing
- **O(N + M) complexity** (one pass to build indices + collectors query indices)
- **Better cache locality** (single pass over tokens, collectors use hot indices)
- **O(1) lookups** (by_type, parent, section_of via hash maps)

### Expected Impact
- **2-5x speedup** on typical documents (eliminate 11 redundant passes)
- **Better scaling** (large documents benefit more from precomputed indices)
- **Cleaner code** (collectors = stateless, warehouse = read-only)

### Non-Breaking
- ✅ **100% baseline parity** (byte-identical output)
- ✅ **Incremental migration** (extractors → collectors one at a time)
- ✅ **Backward compatible** (original extractors remain until fully migrated)

---

## B. Problem Analysis

### Current Architecture (Phase 7.6)

**File**: `src/doxstrux/markdown_parser_core.py:378-412`

```python
def parse(self) -> dict[str, Any]:
    """Parse document and extract all structure."""

    structure = {
        "sections": self._extract_sections(),      # process_tree(self.tree, ...)
        "paragraphs": self._extract_paragraphs(),  # process_tree(self.tree, ...)
        "lists": self._extract_lists(),            # process_tree(self.tree, ...)
        "tables": self._extract_tables(),          # process_tree(self.tree, ...)
        "code_blocks": self._extract_code_blocks(), # process_tree(self.tree, ...)
        "headings": self._extract_headings(),      # process_tree(self.tree, ...)
        "links": self._extract_links(),            # walk tokens (flat)
        "images": self._extract_images(),          # walk tokens (flat)
        "blockquotes": self._extract_blockquotes(), # process_tree(self.tree, ...)
        "frontmatter": self._extract_frontmatter(), # walk tokens (flat)
        "tasklists": self._extract_tasklists(),    # process_tree(self.tree, ...)
        "math": self._extract_math(),              # walk tokens (flat)
    }

    return result
```

### Performance Characteristics

**Measured** (Phase 7.6 baseline):
- **Total time**: 479.40ms for 542 documents
- **Average time**: 0.88ms per document
- **Median document**: ~1KB markdown

**Breakdown** (estimated):
- Parsing (markdown-it): ~30% (0.26ms)
- Extraction (12 passes): ~60% (0.53ms)
- Metadata/mappings: ~10% (0.09ms)

**Where time is spent**:
```
parse()                     0.88ms (100%)
├─ markdown-it parsing      0.26ms  (30%)
├─ _extract_sections()      0.08ms   (9%)  ← Tree traversal
├─ _extract_paragraphs()    0.06ms   (7%)  ← Tree traversal
├─ _extract_lists()         0.07ms   (8%)  ← Tree traversal
├─ _extract_tables()        0.04ms   (5%)  ← Tree traversal
├─ _extract_code_blocks()   0.05ms   (6%)  ← Tree traversal
├─ _extract_headings()      0.06ms   (7%)  ← Tree traversal
├─ _extract_links()         0.03ms   (3%)  ← Token walk
├─ _extract_images()        0.02ms   (2%)  ← Token walk
├─ _extract_blockquotes()   0.04ms   (5%)  ← Tree traversal
├─ _extract_frontmatter()   0.01ms   (1%)  ← Token walk
├─ _extract_tasklists()     0.05ms   (6%)  ← Tree traversal
├─ _extract_math()          0.02ms   (2%)  ← Token walk
└─ metadata/mappings        0.09ms  (10%)
```

### Bottlenecks

1. **Redundant Tree Traversals** (9 extractors)
   - Each calls `process_tree(self.tree, processor, context)`
   - Recursively visits every node in the tree
   - Same nodes visited 9 times

2. **Redundant Token Walks** (4 extractors)
   - Each iterates over `self.tokens` or walks inline tokens
   - Same token list traversed 4 times

3. **Repeated Lookups**
   - `_find_section_id(line)`: O(n) scan through sections
   - Parent finding: O(n) walk to root
   - Type checks: O(n) scan for specific token types

4. **Cache Misses**
   - Time gap between accessing same data
   - Intermediate data structures pollute cache
   - Nodes accessed in different orders by different extractors

### Why Not Async/Threads?

**Analysis** (from ChatGPT conversation):
- ❌ **No I/O** - All work is CPU-bound (token walking)
- ❌ **GIL contention** - Python's GIL serializes CPU-bound work
- ❌ **Shared state** - All extractors read `self.tree`, `self.tokens`, `self.lines`
- ❌ **Overhead dominates** - Thread/process spawning costs more than extraction

**Correct approach**: Eliminate redundant work, not parallelize it.

---

## C. Solution Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                     MarkdownParserCore                       │
│                                                              │
│  __init__():                                                │
│    1. Parse with markdown-it → self.tokens, self.tree       │
│    2. Build TokenWarehouse(self.tokens, self.tree)          │
│       → Precomputes indices (one pass)                      │
│    3. Register collectors with warehouse                     │
│                                                              │
│  parse():                                                   │
│    1. warehouse.dispatch_all()  ← Single pass!              │
│       → Routes tokens to interested collectors              │
│    2. structure = warehouse.finalize_all()                  │
│       → Collectors return extracted data                    │
│    3. Build metadata, mappings (unchanged)                  │
│    4. Return result                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      TokenWarehouse                          │
│                                                              │
│  __init__(tokens, tree):                                    │
│    • Build indices:                                         │
│      - by_type: dict[str, list[int]]                        │
│      - pairs: dict[int, int] (open → close)                 │
│      - parents: dict[int, int] (child → parent)             │
│      - sections: list[(heading_idx, start, end, level)]     │
│      - fences: list[(start, end, lang, info)]               │
│    • Initialize routing table                               │
│    • Register collectors                                    │
│                                                              │
│  dispatch_all():                                            │
│    for i, token in enumerate(tokens):                       │
│      for collector in routing[token.type]:                  │
│        if collector.interested(token, context):             │
│          collector.on_token(i, token, self)                 │
│                                                              │
│  finalize_all() -> dict[str, Any]:                          │
│    return {name: collector.finalize() for ...}              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                         Collectors                           │
│                                                              │
│  LinksCollector                                             │
│    interest: {"link_open", "link_close"}                    │
│    on_token(): Extract href, text, validate scheme          │
│    finalize(): Return list[dict] of links                   │
│                                                              │
│  HeadingsCollector                                          │
│    interest: {"heading_open", "inline", "heading_close"}    │
│    on_token(): Track level, text, line range                │
│    finalize(): Return list[dict] of headings                │
│                                                              │
│  [11 more collectors...]                                    │
└─────────────────────────────────────────────────────────────┘
```

### Complexity Analysis

**Current (Phase 7.6)**:
- **Time**: O(N × M) where N = tokens, M = 12 extractors
- **Space**: O(N) for tokens + O(M × K) for extraction buffers

**With Warehouse (Phase 8)**:
- **Time**: O(N + M × log N) - One pass + collectors query indices
- **Space**: O(N + I) where I = index overhead (~3x token count for all indices)

**Speedup**:
- **Best case**: 12x (eliminate all redundant passes)
- **Realistic**: 2-5x (some overhead from index building, dispatch logic)
- **Worst case**: 1x (very small documents where overhead dominates)

---

## D. TokenWarehouse Design

### Class Structure

**File**: `src/doxstrux/markdown/utils/token_warehouse.py` (new)

```python
from typing import Any, Callable
from collections import defaultdict
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode


class TokenWarehouse:
    """Precomputed token indices for O(1) lookups.

    Built once during parser initialization, provides fast queries
    to eliminate redundant token/tree traversals.

    Usage:
        warehouse = TokenWarehouse(tokens, tree)

        # Query by type
        for idx in warehouse.iter_by_type('link_open'):
            token = warehouse.tokens[idx]
            # ...

        # Find matching close token
        close_idx = warehouse.range_for(open_idx)

        # Find parent block
        parent_idx = warehouse.parent(token_idx)

        # Find section
        section_id = warehouse.section_of(line_num)
    """

    def __init__(self, tokens: list[Token], tree: SyntaxTreeNode):
        """Build all indices in a single pass.

        Args:
            tokens: Flat token list from markdown-it
            tree: Syntax tree (already built by markdown-it)
        """
        self.tokens = tokens
        self.tree = tree

        # Indices (built once)
        self.by_type: dict[str, list[int]] = defaultdict(list)
        self.pairs: dict[int, int] = {}  # open_idx → close_idx
        self.parents: dict[int, int] = {}  # child_idx → parent_idx
        self.sections: list[tuple[int, int, int, int, str]] = []  # (heading_idx, start, end, level, text)
        self.fences: list[tuple[int, int, str, str]] = []  # (start, end, lang, info)

        # Text cache (lazy, populated on demand)
        self._text_cache: dict[tuple[int, int], str] = {}

        # Routing table (collectors registered later)
        self._collectors: list[Collector] = []
        self._routing: dict[str, list[Collector]] = defaultdict(list)

        # Build indices
        self._build_indices()

    def _build_indices(self) -> None:
        """Single pass to build all indices.

        This is the core optimization: one traversal builds all data structures
        that extractors need, eliminating 11 redundant passes.
        """
        stack: list[int] = []  # Track open tokens for pairing
        parent_stack: list[int] = []  # Track nesting for parent relationships

        for i, token in enumerate(self.tokens):
            # Index by type
            self.by_type[token.type].append(i)

            # Track open/close pairs
            if token.nesting == 1:  # Opening token
                stack.append(i)
                parent_stack.append(i)
            elif token.nesting == -1:  # Closing token
                if stack:
                    open_idx = stack.pop()
                    self.pairs[open_idx] = i
                if parent_stack:
                    parent_stack.pop()

            # Track parent relationships
            if parent_stack and token.nesting == 0:
                self.parents[i] = parent_stack[-1]

            # Track sections (headings define sections)
            if token.type == 'heading_open':
                # Section starts at heading, ends at next heading of same/higher level
                # (computed after all headings found)
                pass  # Deferred to _build_sections()

            # Track fenced code blocks
            if token.type == 'fence':
                start_line, end_line = token.map if token.map else (None, None)
                lang = token.info.strip() if token.info else ""
                if start_line is not None and end_line is not None:
                    self.fences.append((start_line, end_line, lang, token.info or ""))

        # Build section ranges (requires all headings)
        self._build_sections()

    def _build_sections(self) -> None:
        """Build section ranges from headings (deferred index)."""
        heading_indices = self.by_type.get('heading_open', [])

        for i, heading_idx in enumerate(heading_indices):
            heading_token = self.tokens[heading_idx]
            level = self._heading_level(heading_token)
            start_line = heading_token.map[0] if heading_token.map else None

            # Find next heading of same or higher level
            end_line = None
            for next_idx in heading_indices[i+1:]:
                next_token = self.tokens[next_idx]
                next_level = self._heading_level(next_token)
                if next_level <= level:
                    end_line = next_token.map[0] - 1 if next_token.map else None
                    break

            # If no next heading, section extends to end of document
            if end_line is None and self.tokens:
                last_token = self.tokens[-1]
                end_line = last_token.map[1] if last_token.map else None

            # Extract heading text (from inline token)
            text = ""
            if heading_idx + 1 < len(self.tokens):
                inline_token = self.tokens[heading_idx + 1]
                if inline_token.type == 'inline':
                    text = inline_token.content or ""

            self.sections.append((heading_idx, start_line or 0, end_line or 0, level, text))

    def _heading_level(self, token: Token) -> int:
        """Extract heading level from token tag (h1 → 1, h2 → 2, etc.)."""
        tag = token.tag if hasattr(token, 'tag') else ""
        if tag.startswith('h') and tag[1:].isdigit():
            return int(tag[1:])
        return 1

    # Query API

    def iter_by_type(self, token_type: str) -> list[int]:
        """Get all token indices of a specific type.

        Args:
            token_type: Token type (e.g., 'link_open', 'fence', 'heading_open')

        Returns:
            List of token indices (indices into self.tokens)

        Complexity: O(1) lookup, O(k) iteration where k = result count
        """
        return self.by_type.get(token_type, [])

    def range_for(self, open_idx: int) -> int | None:
        """Find matching close token for an open token.

        Args:
            open_idx: Index of opening token

        Returns:
            Index of matching close token, or None if not paired

        Complexity: O(1)
        """
        return self.pairs.get(open_idx)

    def parent(self, token_idx: int) -> int | None:
        """Find parent token index.

        Args:
            token_idx: Index of token

        Returns:
            Index of parent token, or None if top-level

        Complexity: O(1)
        """
        return self.parents.get(token_idx)

    def section_of(self, line_num: int) -> str | None:
        """Find which section a line belongs to.

        Args:
            line_num: Line number (0-based)

        Returns:
            Section ID (e.g., 'section_0'), or None if no section

        Complexity: O(log n) with binary search, O(n) with linear scan
        """
        for i, (_, start, end, level, text) in enumerate(self.sections):
            if start <= line_num <= end:
                return f"section_{i}"
        return None

    def text(self, start_idx: int, end_idx: int) -> str:
        """Extract concatenated text from token range (memoized).

        Args:
            start_idx: Start token index
            end_idx: End token index (inclusive)

        Returns:
            Concatenated text content

        Complexity: O(1) if cached, O(n) if not cached
        """
        key = (start_idx, end_idx)
        if key not in self._text_cache:
            parts = []
            for i in range(start_idx, end_idx + 1):
                if i < len(self.tokens):
                    token = self.tokens[i]
                    if token.type == 'text' and token.content:
                        parts.append(token.content)
            self._text_cache[key] = ''.join(parts)
        return self._text_cache[key]

    # Collector registration and dispatch

    def register_collector(self, collector: 'Collector') -> None:
        """Register a collector for token dispatch.

        Args:
            collector: Collector instance with interest specification
        """
        self._collectors.append(collector)
        for token_type in collector.interest.types:
            self._routing[token_type].append(collector)

    def dispatch_all(self) -> None:
        """Single-pass token dispatch to all collectors.

        This is the core routing algorithm: one walk dispatches to all
        interested collectors, eliminating redundant traversals.
        """
        context = DispatchContext(stack=[])

        for i, token in enumerate(self.tokens):
            # Update context (track block nesting)
            if token.nesting == 1:
                context.stack.append(token.type)
            elif token.nesting == -1 and context.stack:
                context.stack.pop()

            # Dispatch to interested collectors
            collectors = self._routing.get(token.type, [])
            for collector in collectors:
                if collector.should_process(token, context, self):
                    collector.on_token(i, token, context, self)

    def finalize_all(self) -> dict[str, Any]:
        """Finalize all collectors and return extracted data.

        Returns:
            Dictionary of {extractor_name: extracted_data}
        """
        return {
            collector.name: collector.finalize(self)
            for collector in self._collectors
        }


class DispatchContext:
    """Mutable context passed during token dispatch.

    Tracks state needed by collectors (e.g., block nesting, line numbers).
    """
    def __init__(self, stack: list[str]):
        self.stack = stack  # Current block type stack
        self.line = 0       # Current line number (updated during dispatch)


class Interest:
    """Specification of what tokens a collector is interested in.

    Collectors register interests, warehouse routes matching tokens.
    """
    def __init__(
        self,
        types: set[str] | None = None,
        tags: set[str] | None = None,
        ignore_inside: set[str] | None = None,
        predicate: Callable[[Token, DispatchContext, TokenWarehouse], bool] | None = None
    ):
        """
        Args:
            types: Set of token types to match (e.g., {'link_open', 'link_close'})
            tags: Set of token tags to match (e.g., {'a', 'img'})
            ignore_inside: Skip tokens inside these block types (e.g., {'fence'})
            predicate: Custom filter function (for complex matching)
        """
        self.types = types or set()
        self.tags = tags or set()
        self.ignore_inside = ignore_inside or set()
        self.predicate = predicate
```

### Index Overhead Analysis

**Memory cost per index**:
- `by_type`: ~12 lists × avg 50 tokens/type = 600 int refs (~4.8KB)
- `pairs`: ~50 pairs × 2 ints = 100 int refs (~0.8KB)
- `parents`: ~500 tokens × 1 int = 500 int refs (~4KB)
- `sections`: ~10 sections × 5 fields = 50 refs (~0.4KB)
- `fences`: ~5 fences × 4 fields = 20 refs (~0.16KB)

**Total overhead**: ~10KB per document (vs ~50KB tokens)
**Overhead ratio**: ~20% memory increase
**Trade-off**: Acceptable for 2-5x speedup

---

## E. Collector Pattern

### Collector Interface

```python
from typing import Protocol


class Collector(Protocol):
    """Protocol for token collectors.

    Collectors are stateless processors that accumulate data
    during warehouse dispatch, then return extracted results.
    """

    name: str  # Extractor name (e.g., 'links', 'headings')
    interest: Interest  # What tokens to process

    def should_process(
        self,
        token: Token,
        context: DispatchContext,
        warehouse: TokenWarehouse
    ) -> bool:
        """Decide if this token should be processed.

        Args:
            token: Current token
            context: Dispatch context (stack, line number, etc.)
            warehouse: Warehouse (for queries)

        Returns:
            True if collector wants to process this token
        """
        ...

    def on_token(
        self,
        idx: int,
        token: Token,
        context: DispatchContext,
        warehouse: TokenWarehouse
    ) -> None:
        """Process a token (accumulate data).

        Args:
            idx: Token index
            token: Token to process
            context: Dispatch context
            warehouse: Warehouse (for queries)
        """
        ...

    def finalize(self, warehouse: TokenWarehouse) -> Any:
        """Return extracted data after dispatch completes.

        Args:
            warehouse: Warehouse (for final queries)

        Returns:
            Extracted data (list[dict], dict, etc.)
        """
        ...
```

### Example Collector: Links

```python
class LinksCollector:
    """Collect links with scheme validation."""

    def __init__(self, effective_allowed_schemes: set[str]):
        self.name = "links"
        self.interest = Interest(
            types={'link_open', 'inline', 'link_close'},
            ignore_inside={'fence', 'code_block'}
        )
        self.effective_allowed_schemes = effective_allowed_schemes

        # State (accumulated during dispatch)
        self._links: list[dict] = []
        self._current_link: dict | None = None
        self._link_depth = 0

    def should_process(self, token: Token, context: DispatchContext, warehouse: TokenWarehouse) -> bool:
        """Process links outside of code blocks."""
        return not any(block in context.stack for block in self.interest.ignore_inside)

    def on_token(self, idx: int, token: Token, context: DispatchContext, warehouse: TokenWarehouse) -> None:
        """Accumulate link data."""
        if token.type == 'link_open':
            self._link_depth += 1
            if self._link_depth == 1:  # Top-level link
                href = token.attrGet('href') or ""
                self._current_link = {
                    'id': f"link_{len(self._links)}",
                    'url': href,
                    'text': "",
                    'line': token.map[0] if token.map else None,
                    'scheme': self._extract_scheme(href),
                    'allowed': self._validate_scheme(href)
                }

        elif token.type == 'inline' and self._current_link:
            # Accumulate text content
            if token.content:
                self._current_link['text'] += token.content

        elif token.type == 'link_close':
            self._link_depth -= 1
            if self._link_depth == 0 and self._current_link:
                # Find section ID
                line = self._current_link.get('line')
                if line is not None:
                    self._current_link['section_id'] = warehouse.section_of(line)

                self._links.append(self._current_link)
                self._current_link = None

    def finalize(self, warehouse: TokenWarehouse) -> list[dict]:
        """Return collected links."""
        return self._links

    def _extract_scheme(self, url: str) -> str | None:
        """Extract URL scheme."""
        if ':' in url:
            return url.split(':', 1)[0].lower()
        return None

    def _validate_scheme(self, url: str) -> bool:
        """Check if scheme is allowed."""
        scheme = self._extract_scheme(url)
        return scheme is None or scheme in self.effective_allowed_schemes
```

### Collector Lifecycle

```
1. Registration:
   warehouse.register_collector(LinksCollector(schemes))
   warehouse.register_collector(HeadingsCollector())
   # ... 11 more collectors

2. Dispatch (single pass):
   warehouse.dispatch_all()
   ├─ For each token:
   │  ├─ Update context (stack, line)
   │  ├─ Look up collectors in routing[token.type]
   │  └─ Call collector.on_token() for interested collectors
   └─ [All collectors accumulate data during this pass]

3. Finalization:
   structure = warehouse.finalize_all()
   └─ Returns: {
        'links': [...],
        'headings': [...],
        'sections': [...],
        # ... 9 more
      }
```

---

## F. Routing Algorithm

### Dispatch Logic

```python
def dispatch_all(self) -> None:
    """Single-pass token dispatch with optimal routing.

    Time complexity: O(N × C_avg) where:
      N = token count
      C_avg = average collectors per token type (~2-3)

    This is much better than O(N × M) where M = 12 extractors,
    because routing is O(1) lookup and most tokens match few collectors.
    """
    context = DispatchContext(stack=[])

    for i, token in enumerate(self.tokens):
        # Update context (track block nesting for ignore_inside checks)
        if token.nesting == 1:
            context.stack.append(token.type)
        elif token.nesting == -1 and context.stack:
            context.stack.pop()

        # Fast lookup: only collectors interested in this token type
        collectors = self._routing.get(token.type, [])

        for collector in collectors:
            # Additional filtering (ignore_inside, custom predicates)
            if collector.should_process(token, context, self):
                collector.on_token(i, token, context, self)
```

### Routing Table Structure

**Built during collector registration**:
```python
# Example routing table after registering all collectors
self._routing = {
    'link_open': [LinksCollector],
    'link_close': [LinksCollector],
    'inline': [LinksCollector, HeadingsCollector, ParagraphsCollector],
    'heading_open': [HeadingsCollector, SectionsCollector],
    'heading_close': [HeadingsCollector, SectionsCollector],
    'fence': [CodeBlocksCollector],
    'code_block': [CodeBlocksCollector],
    'table_open': [TablesCollector],
    'table_close': [TablesCollector],
    # ... etc
}
```

**Why this is fast**:
- **O(1) lookup**: `self._routing[token.type]` is dict lookup
- **Small fan-out**: Most token types match 1-3 collectors (not all 12)
- **Early exit**: `should_process()` filters before heavy work

---

## G. Query API

### Complete API Reference

```python
class TokenWarehouse:
    """Query API for fast lookups."""

    # Type-based queries
    def iter_by_type(self, token_type: str) -> list[int]:
        """O(1) - Get all tokens of a type"""

    def iter_blocks(self, block_type: str) -> list[tuple[int, int]]:
        """O(k) - Get (open, close) pairs for block type"""

    # Structural queries
    def range_for(self, open_idx: int) -> int | None:
        """O(1) - Find matching close token"""

    def parent(self, token_idx: int) -> int | None:
        """O(1) - Find parent block token"""

    def ancestors(self, token_idx: int) -> list[int]:
        """O(depth) - Get all ancestor tokens"""

    # Section queries
    def section_of(self, line_num: int) -> str | None:
        """O(log n) - Find section for line number"""

    def sections_list(self) -> list[tuple[int, int, int, int, str]]:
        """O(1) - Get all sections (heading_idx, start, end, level, text)"""

    # Text extraction
    def text(self, start_idx: int, end_idx: int) -> str:
        """O(1) cached / O(n) uncached - Extract text from range"""

    def text_for_node(self, node_idx: int) -> str:
        """O(1) cached - Extract all text from node and children"""

    # Fence queries
    def fences_list(self) -> list[tuple[int, int, str, str]]:
        """O(1) - Get all fences (start, end, lang, info)"""
```

### Usage Examples

```python
# Example 1: Extract all links (using indices)
link_indices = warehouse.iter_by_type('link_open')
for idx in link_indices:
    token = warehouse.tokens[idx]
    href = token.attrGet('href')
    text = warehouse.text_for_node(idx + 1)  # Inline token after link_open
    print(f"Link: {text} -> {href}")

# Example 2: Find section for a link
link_line = token.map[0] if token.map else None
section_id = warehouse.section_of(link_line)
print(f"Link is in section: {section_id}")

# Example 3: Extract all code blocks (using fences)
for start, end, lang, info in warehouse.fences_list():
    code_lines = lines[start:end]  # lines = parser.lines
    print(f"Code block ({lang}): {len(code_lines)} lines")

# Example 4: Find parent heading for a paragraph
para_idx = ...  # paragraph token index
parent_idx = warehouse.parent(para_idx)
while parent_idx is not None:
    parent_token = warehouse.tokens[parent_idx]
    if parent_token.type == 'heading_open':
        level = warehouse._heading_level(parent_token)
        print(f"Paragraph is under h{level} heading")
        break
    parent_idx = warehouse.parent(parent_idx)
```

---

## H. Migration Guide

### Phase-by-Phase Migration

**Goal**: Convert extractors to collectors incrementally, maintaining baseline parity at each step.

### Phase 8.0: Infrastructure

**Reference Implementation**: `skeleton/` contains production-ready code with all performance optimizations (259 lines warehouse + 206 lines tests + 12 collectors).

**Performance Optimizations** (applied 2025-10-14):
- ✅ **O(H) section builder** - Stack-based closing (was O(H²), ~10-100x faster on many headings)
- ✅ **Correct parent assignment** - All tokens get parents, not just inline (correctness fix)
- ✅ **O(1) ignore-mask** - Bitmask checks instead of linear stack scans (~5-20% faster dispatch)
- ✅ **Hot-loop micro-opts** - Prebound locals in dispatch_all() (~2-5% faster)
- ✅ **Nullable should_process** - Skip redundant calls (~2% faster)
- ✅ **Expected total speedup**: 15-30% on typical documents, 50-100x on heading-heavy documents

**Tasks**:
1. Copy `skeleton/doxstrux/markdown/utils/token_warehouse.py` → `src/doxstrux/markdown/utils/`
2. Copy `skeleton/tests/test_token_warehouse.py` → `tests/`
3. Verify implementation:
   - TokenWarehouse class with all indices (by_type, pairs, parents, sections, fences)
   - Query API (iter_by_type, range_for, parent, section_of with binary search, text)
   - Routing (register_collector, dispatch_all, finalize_all)
   - Collector protocol and Interest class
   - Performance optimizations (O(H) section builder, O(1) ignore-mask, correct parents)
4. Run unit tests: `pytest tests/test_token_warehouse.py`
5. **Do NOT modify parser yet** (just infrastructure)

**Success Criteria**:
- ✅ All unit tests pass (6 tests: indices, dispatch, lines/section boundaries, ignore-mask, invariants)
- ✅ Warehouse builds indices correctly with O(H) complexity
- ✅ Query API returns correct results vs manual traversal
- ✅ Coverage ≥80% for token_warehouse.py

### Phase 8.1: First Collector (Links)

**Reference Implementation**: `skeleton/doxstrux/markdown/collectors_phase8/links.py` (56 lines).

**Why links first**: Token-based (not tree-based), good complexity test case.

**Tasks**:
1. Copy `skeleton/doxstrux/markdown/collectors_phase8/links.py` → `src/doxstrux/markdown/collectors_phase8/`
2. Copy `skeleton/doxstrux/markdown/core/parser_adapter.py` → `src/doxstrux/markdown/core/`
3. Add feature flag to parser: `USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "0") == "1"`
4. Modify `_extract_links()` to use adapter:
   ```python
   def _extract_links(self) -> list[dict]:
       if USE_WAREHOUSE:
           return self._warehouse.collectors['links'].finalize(self._warehouse)
       else:
           # Original implementation (Phase 7.6)
           return links.extract_links(self.tokens, self._process_inline_tokens)
   ```
4. Run baselines with flag OFF: 542/542 passing (sanity check)
5. Run baselines with flag ON: 542/542 passing (verify parity)
6. Benchmark: measure Δ with warehouse vs without

**Success Criteria**:
- ✅ 542/542 baseline parity with flag ON
- ✅ Performance neutral or positive (Δmedian ≤ 5%)
- ✅ No behavioral changes (byte-identical output)

**Rollback**: Remove collector, revert parser changes, delete flag.

### Phase 8.2-8.N: Remaining Collectors

**Order** (easy → hard):
1. **Images** (similar to links, token-based)
2. **Frontmatter** (simple, single token)
3. **Math** (simple, fence-like)
4. **Headings** (tree-based, uses sections index)
5. **Sections** (tree-based, depends on headings)
6. **Paragraphs** (tree-based, uses section_of)
7. **Code blocks** (tree-based, uses fences index)
8. **Blockquotes** (tree-based, nested)
9. **Tables** (tree-based, complex structure)
10. **Lists** (tree-based, recursive, most complex)
11. **Tasklists** (tree-based, depends on lists)

**Per-Phase Tasks**:
1. Implement collector
2. Add to warehouse registration
3. Modify corresponding `_extract_*()` method to use warehouse
4. Run baselines (542/542 passing)
5. Benchmark (measure cumulative Δ)
6. Create `.phase-8.X.complete.json`

### Phase 8.Final: Remove Feature Flag

**Tasks**:
1. Remove `USE_WAREHOUSE` flag (warehouse is now always used)
2. Remove original extractor functions (no hybrids)
3. Update `parse()` to always use warehouse:
   ```python
   def parse(self) -> dict[str, Any]:
       # Build warehouse once
       self._warehouse = TokenWarehouse(self.tokens, self.tree)

       # Register collectors
       self._warehouse.register_collector(LinksCollector(...))
       # ... 11 more

       # Single dispatch pass
       self._warehouse.dispatch_all()

       # Collect results
       structure = self._warehouse.finalize_all()

       # ... metadata, mappings (unchanged)
       return result
   ```
4. Final baseline run: 542/542 passing
5. Final benchmark: measure total speedup vs Phase 7.6

**Success Criteria**:
- ✅ All original extractors removed
- ✅ 542/542 baseline parity maintained
- ✅ Performance improvement: Δmedian ≤ -10% (2x faster target)
- ✅ Memory overhead acceptable (≤ +20%)

---

## I. Performance Analysis

### Expected Improvements

**Breakdown** (estimated):
- **Index building**: +0.05ms (new overhead)
- **Single dispatch**: -0.40ms (eliminate 11 redundant passes)
- **Query overhead**: +0.02ms (index lookups)
- **Net improvement**: -0.33ms (~37% faster)

**Result**:
- **Current**: 0.88ms per document
- **Target**: 0.55ms per document (~1.6x speedup)

### Measurement Methodology

**Benchmark script**: `tools/benchmark_parser.py` (new)

```python
import time
import tracemalloc
from pathlib import Path

def benchmark_parser(corpus_dir: Path, runs: int = 5):
    """Benchmark parser with cold + warm runs."""

    # Load test corpus
    md_files = list(corpus_dir.rglob("*.md"))

    # Cold runs (include parser init)
    cold_times = []
    for _ in range(runs):
        start = time.perf_counter()
        for md_file in md_files:
            content = md_file.read_text()
            parser = MarkdownParserCore(content)
            parser.parse()
        cold_times.append(time.perf_counter() - start)

    # Warm runs (parser already initialized)
    warm_times = []
    tracemalloc.start()
    for _ in range(runs):
        parsers = [MarkdownParserCore(f.read_text()) for f in md_files]
        start = time.perf_counter()
        for parser in parsers:
            parser.parse()
        warm_times.append(time.perf_counter() - start)
    peak_mb = tracemalloc.get_traced_memory()[1] / 1024 / 1024
    tracemalloc.stop()

    # Report
    return {
        "corpus_size": len(md_files),
        "cold_median_ms": sorted(cold_times)[len(cold_times)//2] * 1000,
        "warm_median_ms": sorted(warm_times)[len(warm_times)//2] * 1000,
        "peak_memory_mb": peak_mb
    }
```

### Performance Gates

**Failure conditions**:
- Median Δ > +5% (slower than Phase 7.6)
- P95 Δ > +10% (worst case regression)
- Memory increase > +20%

**Response to failure**:
- Profile with `cProfile` or `py-spy`
- Check index sizes (may be too large)
- Review routing logic (may have O(n) instead of O(1))
- Consider disabling warehouse for tiny documents (overhead dominates)

---

## J. Testing Strategy

### Unit Tests (Warehouse)

**File**: `tests/test_token_warehouse.py` (new)

**Coverage**:
```python
def test_index_building():
    """Verify indices are built correctly."""
    tokens = parse_sample("# Heading\n\n[link](url)")
    warehouse = TokenWarehouse(tokens, SyntaxTreeNode(tokens))

    # Check by_type index
    assert 'heading_open' in warehouse.by_type
    assert len(warehouse.by_type['heading_open']) == 1

    # Check pairs index
    heading_idx = warehouse.by_type['heading_open'][0]
    close_idx = warehouse.range_for(heading_idx)
    assert close_idx is not None

def test_section_of():
    """Verify section lookup is correct."""
    tokens = parse_sample("# S1\n\ntext\n\n## S2\n\nmore")
    warehouse = TokenWarehouse(tokens, SyntaxTreeNode(tokens))

    # Line 0: heading
    assert warehouse.section_of(0) == 'section_0'
    # Line 2: text under S1
    assert warehouse.section_of(2) == 'section_0'
    # Line 4: heading S2
    assert warehouse.section_of(4) == 'section_1'
    # Line 6: text under S2
    assert warehouse.section_of(6) == 'section_1'

def test_collector_dispatch():
    """Verify collector receives correct tokens."""
    class TestCollector:
        def __init__(self):
            self.name = "test"
            self.interest = Interest(types={'heading_open'})
            self.tokens_seen = []

        def should_process(self, token, context, warehouse):
            return True

        def on_token(self, idx, token, context, warehouse):
            self.tokens_seen.append(token.type)

        def finalize(self, warehouse):
            return self.tokens_seen

    tokens = parse_sample("# H1\n\n## H2")
    warehouse = TokenWarehouse(tokens, SyntaxTreeNode(tokens))
    collector = TestCollector()
    warehouse.register_collector(collector)
    warehouse.dispatch_all()

    assert collector.tokens_seen == ['heading_open', 'heading_open']
```

**Target coverage**: ≥80% (project standard).

### Integration Tests (Baseline Parity)

**Command**:
```bash
.venv/bin/python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs
```

**Requirement**: 542/542 tests passing at every phase.

**What this verifies**:
- Byte-identical JSON output
- No behavioral changes
- All edge cases handled

### Performance Tests

**Command**:
```bash
.venv/bin/python tools/benchmark_parser.py \
  --corpus tools/test_mds \
  --runs-cold 3 \
  --runs-warm 5 \
  --baseline-file performance/baseline_phase_7.6.json
```

**Output**:
```json
{
  "phase": "8.1",
  "corpus_size": 542,
  "cold_median_ms": 512.3,
  "warm_median_ms": 450.1,
  "peak_memory_mb": 42.5,
  "baseline": {
    "cold_median_ms": 535.2,
    "warm_median_ms": 479.4,
    "peak_memory_mb": 38.1
  },
  "deltas": {
    "cold_pct": -4.3,
    "warm_pct": -6.1,
    "memory_pct": +11.5
  }
}
```

**Gates**: All deltas within acceptable range.

---

## K. Implementation Checklist

### Phase 8.0: Infrastructure

- [ ] Create `src/doxstrux/markdown/utils/token_warehouse.py`
- [ ] Implement `TokenWarehouse` class
  - [ ] `__init__()` with index building
  - [ ] `_build_indices()` single-pass builder
  - [ ] `_build_sections()` deferred section ranges
  - [ ] Query API: `iter_by_type()`, `range_for()`, `parent()`, `section_of()`, `text()`
- [ ] Implement `DispatchContext` class
- [ ] Implement `Interest` class
- [ ] Implement `Collector` protocol
- [ ] Implement routing: `register_collector()`, `dispatch_all()`, `finalize_all()`
- [ ] Create `tests/test_token_warehouse.py`
  - [ ] Test index building
  - [ ] Test query API
  - [ ] Test collector dispatch
- [ ] Run unit tests: `pytest tests/test_token_warehouse.py`
- [ ] Achieve ≥80% coverage

### Phase 8.1: First Collector (Links)

- [ ] Implement `LinksCollector` in `token_warehouse.py`
- [ ] Add feature flag `USE_WAREHOUSE` to parser
- [ ] Modify `_extract_links()` to use warehouse when flag enabled
- [ ] Run baselines with flag OFF: verify 542/542 passing
- [ ] Run baselines with flag ON: verify 542/542 passing
- [ ] Benchmark: measure Δmedian, Δp95, memory
- [ ] Create `.phase-8.1.complete.json`

### Phase 8.2-8.N: Remaining Collectors

- [ ] Implement remaining 11 collectors (see order in §H)
- [ ] Per collector:
  - [ ] Implement collector class
  - [ ] Register with warehouse
  - [ ] Modify `_extract_*()` method
  - [ ] Run baselines (542/542)
  - [ ] Benchmark (cumulative Δ)
  - [ ] Create `.phase-8.X.complete.json`

### Phase 8.Final: Cleanup

- [ ] Remove `USE_WAREHOUSE` feature flag
- [ ] Remove original extractor functions
- [ ] Update `parse()` to always use warehouse
- [ ] Final baseline run: 542/542 passing
- [ ] Final benchmark: measure total speedup
- [ ] Create `.phase-8.final.complete.json`
- [ ] Update `CHANGELOG.md`, `README.md`

---

## Summary

This specification provides a complete roadmap for implementing the Token Warehouse optimization:

1. **Single-pass precomputed indices** eliminate 11 redundant traversals
2. **Collector-based routing** dispatches tokens to interested processors
3. **O(1) query API** provides fast lookups (by_type, parent, section_of)
4. **Incremental migration** maintains baseline parity at every step
5. **Expected 2-5x speedup** on typical documents

**Next steps**: Review this spec, then proceed to `WAREHOUSE_EXECUTION_PLAN.md` for implementation guide.

---

**Document Status**: ✅ Complete and ready for implementation
**Phase 8.0 Status**: 📋 Specification ready, implementation pending
**Estimated Implementation Time**: 5-7 days for full migration
