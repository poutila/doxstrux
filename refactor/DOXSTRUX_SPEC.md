# DOXSTRUX_SPEC

Single source of truth for the doxstrux parser/warehouse/collector/registry wiring and contracts.

---

## 1. Problem

`MarkdownParserCore` is a 2075-line God Object with 49 methods. Key violations:

| Principle | Issue |
|-----------|-------|
| SRP | 8 responsibilities in one class |
| OCP | Extractors hardcoded, no registry |
| DIP | Parser imports 11 concrete modules |

**Goal:** Split the God Object. Parser orchestrates; warehouse owns tokens and dispatch; collectors extract features; registry wires them together.

**Non-goal:** Full DIP purity. We accept that the registry is tightly coupled to concrete collector modules. This is the *only* place where that coupling is allowed.

---

## 2. Target Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Parser (MarkdownParserCore)                            │
│  Orchestrates: markdown-it → warehouse → collectors     │
├─────────────────────────────────────────────────────────┤
│  Registry (collector_registry.py)                       │
│  Knows which collectors to register. Single edit point. │
│  Tightly coupled to collector modules (by design).      │
├─────────────────────────────────────────────────────────┤
│  Warehouse (TokenWarehouse)                             │
│  Owns tokens, topology, text slicing, dispatch loop.    │
├─────────────────────────────────────────────────────────┤
│  Collectors (collectors_phase8.*)                       │
│  Single-purpose extractors. Implement Collector.        │
│  (Set defined by default_collectors() in registry)      │
└─────────────────────────────────────────────────────────┘
```

---

## 3. interfaces.py

**Location:** `doxstrux/markdown/interfaces.py`

```python
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

@dataclass
class DispatchContext:
    """State passed to collectors during token dispatch."""
    stack: list[str]  # Current nesting context (tag names)
    line: int         # Source line number (best-effort; see Line Semantics below)

@dataclass(frozen=True)
class CollectorInterest:
    """Declares which tokens a collector wants to process.
    
    Used for fast routing only. Complex filtering belongs in should_process().
    """
    types: frozenset[str] = frozenset()  # Token types (e.g., "heading_open")
    tags: frozenset[str] = frozenset()   # HTML tags (e.g., "h1", "h2")

@runtime_checkable
class Collector(Protocol):
    """Feature extractor interface.
    
    INTENTIONALLY WEAK: This protocol only standardises registration surface
    (name, interest) and output (finalize). It does NOT protect warehouse
    usage — collectors are trusted to call warehouse methods correctly.
    
    If you want type safety for warehouse calls, that's a future enhancement.
    
    Key contract: finalize() must return a dict with keys unique across all
    collectors. Duplicate keys raise RuntimeError in finalize_all().
    """
    
    @property
    def name(self) -> str: ...
    
    @property
    def interest(self) -> CollectorInterest: ...
    
    def should_process(self, token, ctx: DispatchContext) -> bool:
        """Return False to skip this token."""
    
    def on_token(self, idx: int, token, ctx: DispatchContext, warehouse) -> None:
        """Process token. Accumulate results internally."""
    
    def finalize(self) -> dict[str, Any]:
        """Return collected data. Keys must be unique across all collectors."""
```

---

## 4. collector_registry.py

**Location:** `doxstrux/markdown/collector_registry.py`

**Trade-off:** This module is tightly coupled to the concrete collector layout. That's intentional — we moved the coupling here so the parser doesn't have it. If collectors are reorganised into submodules, this file and `collectors_phase8/__init__.py` must be updated together.

**Requirement:** `doxstrux.markdown.collectors_phase8` must export all collector classes at package level.

```python
from doxstrux.markdown.collectors_phase8 import (
    SectionsCollector, HeadingsCollector, ParagraphsCollector,
    ListsCollector, TasklistsCollector, CodeblocksCollector,
    TablesCollector, LinksCollector, ImagesCollector,
    FootnotesCollector, HtmlCollector, MathCollector,
)

def default_collectors() -> tuple:
    """All default collector instances."""
    return (
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
    )

def register_default_collectors(warehouse) -> None:
    """Register all default collectors with the warehouse."""
    for collector in default_collectors():
        warehouse.register_collector(collector)
```

---

## 5. TokenWarehouse Additions

**Location:** `doxstrux/markdown/utils/token_warehouse.py`

**Constraint:** Do not change the TokenWarehouse constructor signature. Only add `_collectors` and `_routing` to its existing `__init__`.

### 5.1 Existing Surface (collectors may use these)

Collectors are allowed to call these existing methods/properties. Their signatures and semantics must not change:

```python
@property
def tokens(self) -> Sequence[Token]: ...

def get_token_text(self, idx: int) -> str:
    """Returns text content for token at index."""

def find_close(self, open_idx: int) -> int | None:
    """Returns index of matching close token, or None."""

def find_parent(self, idx: int) -> int | None:
    """Returns index of parent token, or None."""

def text_between(self, start: int, end: int) -> str:
    """Returns concatenated text content in range [start, end)."""

def section_of(self, idx: int) -> int | None:
    """Returns section index (int) containing token, or None if not in a section."""
```

If any of these change signature or semantics, collector code will break.

### 5.2 New Attributes (add to existing `__init__`)

```python
from collections import defaultdict
from doxstrux.markdown.interfaces import Collector, DispatchContext

# ADD to END of existing __init__:
self._collectors: list[Collector] = []
self._routing: dict[str, list[Collector]] = defaultdict(list)
```

### 5.3 New Methods

```python
def register_collector(self, collector: Collector) -> None:
    """Register collector under type and tag keys.
    
    A collector MAY register for both types AND tags (broader matching).
    Most collectors will use only one. Both patterns are valid.
    """
    self._collectors.append(collector)
    for t in collector.interest.types:
        self._routing[f"type:{t}"].append(collector)
    for tag in collector.interest.tags:
        self._routing[f"tag:{tag}"].append(collector)

def dispatch_all(self) -> None:
    """Single-pass dispatch to registered collectors.
    
    Observable contract:
    - Each token is visited exactly once, in order.
    - For each token, each interested collector is called at most once,
      even if it registered interest in both the token's type AND tag.
    - ctx.stack tracks nesting; ctx.line tracks source position (best-effort).
    """
    ctx = DispatchContext(stack=[], line=0)
    for idx, token in enumerate(self.tokens):
        ctx.line = (token.map[0] if token.map else ctx.line)
        if token.nesting == 1:
            ctx.stack.append(token.tag or token.type)
        
        for collector in self._get_collectors_for(token):
            if collector.should_process(token, ctx):
                collector.on_token(idx, token, ctx, self)
        
        if token.nesting == -1 and ctx.stack:
            ctx.stack.pop()

def finalize_all(self) -> dict:
    """Merge results from all collectors.
    
    Raises RuntimeError if collectors produce duplicate keys.
    """
    result = {}
    for collector in self._collectors:
        data = collector.finalize()
        overlap = set(result) & set(data)
        if overlap:
            raise RuntimeError(
                f"Collector '{collector.name}' produced duplicate keys: {overlap}"
            )
        result.update(data)
    return result

def _get_collectors_for(self, token) -> list[Collector]:
    """Get collectors interested in this token, deduplicated.
    
    Observable contract: Returns each interested collector at most once.
    Implementation note: Currently dedupes via id(); this is not part of
    the contract and may change.
    """
    seen: set[int] = set()
    result: list[Collector] = []
    for c in self._routing.get(f"type:{token.type}", []):
        if id(c) not in seen:
            seen.add(id(c))
            result.append(c)
    if token.tag:
        for c in self._routing.get(f"tag:{token.tag}", []):
            if id(c) not in seen:
                seen.add(id(c))
                result.append(c)
    return result
```

### 5.4 Line Semantics

`ctx.line` provides **best-effort source line tracking**:

- If `token.map` exists, `ctx.line` = first line of that token's source range
- If `token.map` is None, `ctx.line` = last known line (inherited from previous token)

Collectors should treat `ctx.line` as approximate. It's suitable for diagnostics and section mapping, not precise source reconstruction.

---

## 6. Parser Changes

**Location:** `doxstrux/markdown/parser.py`

**Scope:** Only the collector wiring changes. Security, caching, metadata, and tree-building logic remain exactly as-is.

```python
from doxstrux.markdown.collector_registry import register_default_collectors

class MarkdownParserCore:
    # __init__ UNCHANGED
    # Security/plugin configuration UNCHANGED
    
    def parse(self) -> dict:
        # ... existing security precheck (UNCHANGED) ...
        # ... existing token parsing (UNCHANGED) ...
        
        self.warehouse = TokenWarehouse(...)  # UNCHANGED args
        
        # --- NEW (replaces manual collector wiring) ---
        register_default_collectors(self.warehouse)
        self.warehouse.dispatch_all()
        metadata = self.warehouse.finalize_all()
        # --- END NEW ---
        
        # ... existing security policy (UNCHANGED) ...
        # ... existing metadata assembly (UNCHANGED) ...
        return metadata
```

**Constraint:** Do not simplify or restructure `parse()` beyond swapping collector wiring. This is a surgical change.

---

## 7. Collector Example

```python
class HeadingsCollector:
    name = "headings"
    interest = CollectorInterest(
        types=frozenset({"heading_open"}),
        tags=frozenset({"h1", "h2", "h3", "h4", "h5", "h6"}),
    )
    
    def __init__(self):
        self._headings = []
    
    def should_process(self, token, ctx: DispatchContext) -> bool:
        return "blockquote" not in ctx.stack
    
    def on_token(self, idx, token, ctx, warehouse):
        self._headings.append({
            "level": int(token.tag[1]),
            "text": warehouse.get_token_text(idx),  # Uses existing method
            "line": ctx.line,
        })
    
    def finalize(self) -> dict:
        return {"headings": self._headings}
```

---

## 8. Execution Steps

*These steps describe how the architecture was introduced. Once the refactor is complete, they remain as guidance for similar future changes but are not a live migration plan.*

### Step 0 — Baseline (required before any code changes)

Create golden tests that exercise:

| Category | Requirement |
|----------|-------------|
| **Per-collector** | One test per collector in `default_collectors()`. Must assert specific structure, not just non-empty. E.g. Headings: exact levels/text/line for a known input. |
| **Complex collectors** | Tables, Lists, and Html collectors need at least one edge-case test each (e.g. nested lists, table with colspan, mixed HTML/markdown). |
| **Nesting** | Lists in lists, tables with headings, blockquotes with code |
| **Security** | One doc that triggers security flags. Assert both keys AND critical values (e.g. `blocked=True`, at least one issue code) match pre-refactor output. |
| **End-to-end** | One rich document exercising multiple collectors. Assert on combined `parse()` output: number of sections, heading texts, presence of expected links/tables. |

**Exit:** Every collector in `default_collectors()` has at least one anchored test. Complex collectors have edge-case coverage. One end-to-end golden test exists. Security values are pinned.

### Step 1 — Add infrastructure

1. Add `interfaces.py` (DispatchContext, CollectorInterest, Collector)
2. Add `collector_registry.py` (default_collectors, register_default_collectors)
3. Add TokenWarehouse methods (register_collector, dispatch_all, finalize_all, _get_collectors_for)
4. Add `_collectors` and `_routing` attributes to TokenWarehouse.__init__

**Exit:** New code exists. No behaviour change yet. All existing tests pass.

### Step 2 — Wire parser

Replace manual collector wiring in `MarkdownParserCore.parse()` with:
```python
register_default_collectors(self.warehouse)
self.warehouse.dispatch_all()
metadata = self.warehouse.finalize_all()
```

**Constraint:** No other changes to parse(). Security logic untouched.

**Exit:** Parser no longer imports concrete collectors. All tests pass including security metadata test.

### Step 3 — Conform collectors

Update each collector to implement Collector protocol (name, interest, should_process, on_token, finalize).

**Guardrails:**
- No algorithmic changes; only signature/ctx wiring
- Each collector's golden test must still pass
- Diff review: confirm only wiring changes, not logic rewrites

**Exit:** All 12 collectors conform. All tests pass.

---

## 9. Current API (must remain compatible)

```python
MarkdownParserCore(content: str, *, config: dict | None = None, security_profile: str | None = None)
parse(self) -> dict
```

---

## 10. References

| Document | Purpose |
|----------|---------|
| DOXSTRUX_SOLID_ANALYSIS.md | Pre-refactor diagnosis (archived) |

---

*This is the single source of truth for parser/warehouse/collector/registry wiring and contracts. If code matches this spec, that wiring and those contracts are correct.*
