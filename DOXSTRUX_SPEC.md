# DOXSTRUX_SPEC

Architectural scaffolding for the doxstrux parser refactor.

**What this is:** A guide to the parser/warehouse/collector/registry structure — which modules exist, what they expose, and how they wire together.

**What this is not:** A formal specification. Semantic details (exact behavior of `text_between`, edge cases in collectors, security logic) are defined by the existing code and tests, not this document.

---

## 1. Problem

`MarkdownParserCore` accumulates too many responsibilities: security, plugins, parsing, extraction, metadata, caching. This makes it hard to modify any one concern without touching the others.

**Goal:** Split responsibilities. Parser orchestrates; warehouse owns tokens and dispatch; collectors extract features; registry wires them together.

**Non-goal:** Full DIP purity. The registry is tightly coupled to concrete collector modules — we moved the coupling to one file, not eliminated it.

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
    
    What this guarantees:
    - Collectors have name, interest, and the three methods below.
    - finalize_all() will raise RuntimeError on duplicate keys.
    
    What this does NOT guarantee:
    - Type safety for token or warehouse usage (both untyped).
    - Semantic correctness of collector output.
    - That collectors call only valid warehouse methods.
    
    This is barely stronger than duck typing. Collectors are trusted to
    behave correctly; this protocol only standardizes the registration
    and output interface.
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
        """Return collected data. Keys must not collide with other collectors."""
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

### 5.1 Existing Surface (collectors currently use these)

Collectors currently call these methods. Their exact semantics are defined by the existing implementation, not this document.

```python
@property
def tokens(self) -> Sequence[Token]: ...

def get_token_text(self, idx: int) -> str: ...
def find_close(self, open_idx: int) -> int | None: ...
def find_parent(self, idx: int) -> int | None: ...
def text_between(self, start: int, end: int) -> str: ...
def section_of(self, idx: int) -> int | None: ...
```

**Warning:** If you change these signatures, collector code will break. If you change their semantics, collector behavior may change in ways this spec cannot predict — the spec doesn't define what these methods do, only that collectors depend on them.

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
    
    Observable behavior:
    - Each token is visited exactly once, in order.
    - For each token, each interested collector is called at most once,
      even if it registered interest in both the token's type AND tag.
    - ctx.stack tracks nesting; ctx.line tracks source position (unreliable).
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
    
    Behavior: Returns each interested collector at most once.
    Implementation: Currently dedupes via id(); this detail may change.
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

`ctx.line` provides **unreliable** source line tracking:

- If `token.map` exists, `ctx.line` = first line of that token's source range
- If `token.map` is None, `ctx.line` = last known line (inherited)

**No invariants guaranteed.** Line numbers may be 0, may skip, may not correspond to actual source lines for synthetic tokens. 

**Collectors should not rely on `ctx.line` for control flow.** It's acceptable for diagnostics, logging, or approximate source mapping — but any logic that depends on specific line values is fragile.

---

## 6. Parser Changes

**Location:** `doxstrux/markdown/parser.py`

**Intent:** Only change the collector wiring. Security, caching, metadata, and tree-building logic should remain as-is.

**Reality check:** This spec cannot enforce that constraint. The snippet below shows the intended change; discipline and code review must ensure nothing else changes.

```python
from doxstrux.markdown.collector_registry import register_default_collectors

class MarkdownParserCore:
    # __init__ should remain unchanged
    # Security/plugin configuration should remain unchanged
    
    def parse(self) -> dict:
        # ... existing code up to warehouse creation ...
        
        self.warehouse = TokenWarehouse(...)  # keep existing args
        
        # --- Replace manual collector wiring with: ---
        register_default_collectors(self.warehouse)
        self.warehouse.dispatch_all()
        metadata = self.warehouse.finalize_all()
        # --- End replacement ---
        
        # ... existing security/metadata code should remain ...
        return metadata
```

**Warning:** This snippet is illustrative, not prescriptive. The real `parse()` likely has more structure. Don't simplify it to match this snippet.

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

Create tests that establish a baseline. These are **minimum requirements**, not a guarantee of correctness.

| Category | Requirement |
|----------|-------------|
| **Per-collector** | One test per collector in `default_collectors()`. Should assert on structure, not just non-empty. |
| **Complex collectors** | Tables, Lists, and Html need at least one edge-case test each (nested structures, mixed content). |
| **Security** | One doc that triggers security flags. Assert on key values like `blocked` and issue codes. |
| **End-to-end** | One document exercising multiple collectors. Assert on combined output structure. |

**What these tests catch:** Catastrophic breakage — collectors that stop working entirely, wiring that fails to connect.

**What these tests won't catch:** Subtle semantic drift, edge cases not covered, performance regressions, interactions between collectors.

**Exit:** Tests exist and pass. This establishes a baseline, not a safety guarantee.

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

**Intent:** No other changes to parse(). Security logic untouched. (This requires discipline; the spec cannot enforce it.)

**Exit:** Parser no longer imports concrete collectors. All tests pass.

### Step 3 — Conform collectors

Update each collector to implement Collector protocol (name, interest, should_process, on_token, finalize).

**Guardrails:**
- No algorithmic changes; only signature/ctx wiring
- Each collector's test must still pass
- Diff review: confirm only wiring changes, not logic rewrites

**Exit:** All collectors in `default_collectors()` conform. All tests pass.

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

*This document describes the intended structure. It does not formally specify semantics. Correctness ultimately depends on the code, tests, and careful review — not this spec alone.*
