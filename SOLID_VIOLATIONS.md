# SOLID Violations Review: Architectural Analysis

## Executive Summary

**Overall SOLID Compliance: MODERATE (6/10)**

The codebase has a clear separation of concerns at the module level, but the core parser class is a God Object with significant SRP and DIP violations.

---

## S - Single Responsibility Principle

**Status: VIOLATION**

### The God Object: `MarkdownParserCore`

| Metric | Value | Concern |
|--------|-------|---------|
| Lines of code | 2075 | Far exceeds 300-500 line guideline |
| Methods | 49 | Multiple responsibilities |
| `_extract_*` methods | 17 | Thin wrappers over extractors |

### Responsibilities in ONE Class

1. Content normalization (`_normalize_content`)
2. Security validation (`_validate_content_security`, `_apply_security_policy`)
3. Plugin management (`_validate_plugins`, `enabled_plugins`)
4. Token parsing (`parse`, `process_tree`)
5. 17 extraction orchestrations (`_extract_sections`, etc.)
6. Metadata generation (`_extract_metadata`, `_generate_security_metadata`)
7. Caching (`_get_cached`, `_cache`)
8. IR generation (`to_ir`, `to_chunks`)

**Impact:** Changing ANY of these 8 concerns requires modifying the 2075-line file. This violates "one reason to change."

### Recommended Refactoring

```
MarkdownParserCore (orchestrator only)
├── ContentNormalizer
├── SecurityValidator
├── PluginManager
├── ExtractorRegistry  <-- All 17 _extract_* methods
├── MetadataGenerator
└── IRBuilder
```

---

## O - Open/Closed Principle

**Status: PARTIAL**

### Plugins: Well Done

```python
for plugin_config in plugins:
    if plugin_config == "strikethrough":
        self.md.use(strikethrough_plugin)
```

New plugins CAN be added via configuration.

### Extractors: Closed for Extension

Adding a new extractor requires:

1. Create new module in `extractors/`
2. Modify `markdown_parser_core.py` imports (line 26)
3. Modify `parse()` method (lines 494-506)
4. Modify `_build_mappings()` if needed

**No registry pattern:** Extractors are hardcoded, not discovered.

---

## L - Liskov Substitution Principle

**Status: NOT APPLICABLE**

The codebase uses composition over inheritance. There are no inheritance hierarchies to evaluate. This is actually a good design choice.

---

## I - Interface Segregation Principle

**Status: CONCERNED**

### Extractor Function Signatures Are Too Large

```python
# From sections.py - extract_sections requires 8 parameters!
extract_sections(
    tree,
    lines,
    process_tree_func,      # callback
    heading_level_func,     # callback
    get_text_func,          # callback
    slice_lines_raw_func,   # callback
    plain_text_in_range_func,  # callback
    span_from_lines_func,   # callback
    cache                   # shared state
)
```

**Problem:** Extractors depend on a "fat interface" - a bundle of callbacks from the parser. They're tightly coupled to `MarkdownParserCore`'s internal methods.

### Better Approach

Define a `ParserContext` protocol/dataclass that extractors receive:

```python
@dataclass
class ParserContext:
    tree: SyntaxTreeNode
    lines: list[str]
    cache: dict
    get_text: Callable
    # ...
```

---

## D - Dependency Inversion Principle

**Status: VIOLATION**

### High-Level Module Depends on Low-Level Details

```python
# markdown_parser_core.py (HIGH-LEVEL)
from doxstrux.markdown.extractors import (
    blockquotes, codeblocks, footnotes, html, links,
    lists, math, media, paragraphs, sections, tables
)
```

The core parser directly imports 11 concrete extractor modules.

### Callbacks Instead of Protocols

Extractors receive raw function references, not protocols:

```python
sections.extract_sections(
    self.tree,
    self.lines,
    self.process_tree,        # <-- direct method reference
    self._heading_level,      # <-- private method leaked
    ...
)
```

**Problem:** Can't easily swap implementations. Tight coupling.

### Recommended Fix

```python
# Define protocol
class TextExtractor(Protocol):
    def get_text(self, node: Any) -> str: ...
    def heading_level(self, node: Any) -> int: ...

# Inject abstraction
class SectionExtractor:
    def __init__(self, text_extractor: TextExtractor): ...
```

---

## Summary Table

| Principle | Status | Severity | Fix Complexity |
|-----------|--------|----------|----------------|
| S - Single Responsibility | VIOLATED | HIGH | Medium (refactor to services) |
| O - Open/Closed | PARTIAL | MEDIUM | Low (add registry) |
| L - Liskov Substitution | N/A | - | - |
| I - Interface Segregation | CONCERNED | LOW | Low (use context object) |
| D - Dependency Inversion | VIOLATED | MEDIUM | Medium (use protocols) |

---

## Is This Optimal?

### For a library with stable requirements

The current design is functional. The God Object pattern is less problematic when:

- The codebase is relatively stable
- There's a single maintainer
- Performance is prioritized over extensibility

### For long-term maintainability

The SRP and DIP violations will cause pain when:

- Adding new extraction types
- Testing extractors in isolation
- Onboarding new contributors
- Debugging across the 2075-line file

---

*Generated: 2025-12-12*
