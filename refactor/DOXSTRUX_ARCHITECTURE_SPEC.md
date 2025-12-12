# DOXSTRUX_ARCHITECTURE_SPEC

Type definitions and concrete specs for the doxstrux refactor. Reference companion to DOXSTRUX_REFACTOR.md.

---

## 1. interfaces.py

**Location:** `doxstrux/markdown/interfaces.py`

Three types. No more.

```python
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

@dataclass
class DispatchContext:
    """State passed to collectors during token dispatch."""
    stack: list[str]  # Current nesting context (tag names)
    line: int         # Current source line number

@dataclass(frozen=True)
class CollectorInterest:
    """Declares which tokens a collector wants to process.
    
    Used for fast routing. Complex filtering belongs in should_process().
    """
    types: frozenset[str] = frozenset()  # Token types (e.g., "heading_open")
    tags: frozenset[str] = frozenset()   # HTML tags (e.g., "h1", "h2")

@runtime_checkable
class Collector(Protocol):
    """Feature extractor interface. 12 implementations exist.
    
    Contract: finalize() must return a dict with keys unique across all
    collectors. finalize_all() merges via dict.update(); duplicate keys
    cause silent overwrites.
    """
    
    @property
    def name(self) -> str: ...
    
    @property
    def interest(self) -> CollectorInterest: ...
    
    def should_process(self, token, ctx: DispatchContext) -> bool:
        """Return False to skip. Handles nesting, conditions, etc."""
    
    def on_token(self, idx: int, token, ctx: DispatchContext, warehouse) -> None:
        """Process token. Accumulate results internally.
        
        Args:
            idx: Token index in warehouse.tokens
            token: markdown-it Token (untyped to avoid mdit dependency)
            ctx: Current dispatch state
            warehouse: TokenWarehouse instance (untyped to avoid circular import)
        """
    
    def finalize(self) -> dict[str, Any]:
        """Return collected data. Keys must be unique across all collectors."""
```

---

## 2. collector_registry.py

**Location:** `doxstrux/markdown/collector_registry.py`

```python
from doxstrux.markdown.collectors_phase8 import (
    SectionsCollector, HeadingsCollector, ParagraphsCollector,
    ListsCollector, TasklistsCollector, CodeblocksCollector,
    TablesCollector, LinksCollector, ImagesCollector,
    FootnotesCollector, HtmlCollector, MathCollector,
)

def default_collectors() -> tuple:
    """All default collector instances. Order matters for dispatch."""
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

## 3. TokenWarehouse Additions

**Location:** `doxstrux/markdown/utils/token_warehouse.py`

These are **additions** to the existing class. Do not replace the existing `__init__` or other methods.

### 3.1 New instance attributes (add to existing `__init__`)

```python
# ADD these lines to the END of existing __init__:
self._collectors: list[Collector] = []
self._routing: dict[str, list[Collector]] = defaultdict(list)
```

### 3.2 New methods (add to class)

```python
def register_collector(self, collector: Collector) -> None:
    """Register collector and update routing.
    
    Uses namespaced keys to prevent type/tag collision.
    """
    self._collectors.append(collector)
    for t in collector.interest.types:
        self._routing[f"type:{t}"].append(collector)
    for tag in collector.interest.tags:
        self._routing[f"tag:{tag}"].append(collector)

def dispatch_all(self) -> None:
    """Single-pass dispatch to registered collectors."""
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
    """Get collectors interested in this token."""
    collectors = list(self._routing.get(f"type:{token.type}", []))
    if token.tag:
        collectors.extend(self._routing.get(f"tag:{token.tag}", []))
    return collectors
```

---

## 4. Parser Changes

**Location:** `doxstrux/markdown/parser.py`

**Scope:** Only the collector wiring changes. Security code paths are unchanged.

```python
from doxstrux.markdown.collector_registry import register_default_collectors

class MarkdownParserCore:
    # Existing __init__ unchanged (content, config, security_profile params)
    # Existing security calls unchanged
    
    def parse(self) -> dict:
        """Parse markdown, return metadata dict.
        
        CHANGED: Uses registry instead of manual collector wiring.
        UNCHANGED: Security validation, plugin config, return shape.
        """
        # ... existing security precheck (unchanged) ...
        
        tokens = self.md.parse(self.content)
        self.warehouse = TokenWarehouse(tokens, self.content)
        
        # NEW: Registry-based wiring (replaces manual collector imports)
        register_default_collectors(self.warehouse)
        self.warehouse.dispatch_all()
        metadata = self.warehouse.finalize_all()
        
        # ... existing security policy application (unchanged) ...
        return metadata
```

**Key change:** Parser imports `register_default_collectors`, not 12 concrete collector classes. Security integration is untouched by this refactor.

---

## 5. Collector Example

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
        # Skip headings inside blockquotes
        return "blockquote" not in ctx.stack
    
    def on_token(self, idx, token, ctx, warehouse):
        self._headings.append({
            "level": int(token.tag[1]),
            "text": warehouse.get_token_text(idx),
            "line": ctx.line,
        })
    
    def finalize(self) -> dict:
        return {"headings": self._headings}
```

---

*That's it. Three types, two registry functions, three warehouse methods, one parser change.*
