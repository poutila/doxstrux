# Module Boundaries and Dependencies

**Phase 7 Modularization**
**Version**: 0.2.0
**Status**: In Progress (Task 7.1 complete)

---

## Dependency Graph

```
exceptions (no dependencies)
    ↑
config (depends on: exceptions)
    ↑
utils (depends on: exceptions)
    ↑
extractors (depends on: utils, exceptions)
    ↑
ir (depends on: extractors, utils, exceptions)
    ↑
core (depends on: ir, extractors, security, utils, config, exceptions)
    ↑
[Backward-compatible façade at src/doxstrux/markdown_parser_core.py]
```

**Rule**: Dependencies flow in **one direction only** (bottom to top). No circular dependencies allowed.

---

## Module Responsibilities

### `exceptions.py`
**Purpose**: Error hierarchy
**Dependencies**: None
**Exports**:
- `MarkdownSecurityError`
- `MarkdownSizeError`
- `MarkdownPluginError`

**责任**: Define all custom exceptions. No logic, just error classes.

---

### `config.py`
**Purpose**: Security profiles and configuration constants
**Dependencies**: `exceptions`
**Exports**:
- `SECURITY_PROFILES` - Dict of profile configurations
- `_STYLE_JS_PAT` - CSS injection pattern
- `_META_REFRESH_PAT` - Meta refresh pattern
- `_FRAMELIKE_PAT` - Frame-like tags pattern
- `_BIDI_CONTROLS` - BiDi control characters list

**Responsibility**: Single source of truth for all configuration. No logic.

---

### `budgets.py`
**Purpose**: Resource limits and budgets
**Dependencies**: `config`
**Exports**:
- `NodeBudget` - Track node counts
- `CellBudget` - Track table cell counts
- `URIBudget` - Track URI counts

**Responsibility**: Enforce resource limits during parsing.

---

### `utils/` Package

#### `utils/token_utils.py`
**Purpose**: Token traversal and manipulation
**Dependencies**: None (only markdown-it-py)
**Exports**:
- `walk_tokens_iter()` - Recursive token traversal
- `collect_text_between_tokens()` - Extract text between markers
- `extract_code_blocks()` - Extract code block content
- `TokenAdapter` - Unified token interface

**Responsibility**: Generic token operations. No parser-specific logic.

#### `utils/line_utils.py`
**Purpose**: Line slicing and manipulation
**Dependencies**: None
**Exports**:
- `slice_lines()` - Slice lines by range
- `build_line_offsets()` - Build line offset map

**Responsibility**: Pure functions for line manipulation.

#### `utils/text_utils.py`
**Purpose**: Text extraction from tokens
**Dependencies**: None (only markdown-it-py)
**Exports**:
- `collect_text_segments()` - Collect text from token tree
- `extract_text_from_inline()` - Extract from inline tokens
- `has_child_type()` - Check for child token types

**Responsibility**: Pure functions for text extraction.

---

### `security/` Package

#### `security/validators.py`
**Purpose**: Security validation functions
**Dependencies**: `config`, `exceptions`
**Exports**:
- `validate_url_scheme()` - Check URL schemes
- `detect_bidi_controls()` - Detect BiDi manipulation
- `detect_confusables()` - Detect homograph attacks
- `validate_content_size()` - Check size limits

**Responsibility**: Stateless validation functions. Return bool or raise exceptions.

#### `security/policies.py`
**Purpose**: Security policy application
**Dependencies**: `validators`, `config`, `exceptions`
**Exports**:
- `apply_security_policy()` - Apply profile-based policies
- `check_html_allowed()` - Check HTML permission
- `sanitize_html()` - Sanitize HTML if needed

**Responsibility**: Apply security profiles. Coordinate validators.

#### `security/unicode.py`
**Purpose**: Unicode security detection
**Dependencies**: `config`
**Exports**:
- `BIDI_CONTROLS` - BiDi control characters
- `check_bidi()` - Check for BiDi controls
- `check_confusables()` - Check for confusable chars

**Responsibility**: Unicode-specific security checks.

---

### `extractors/` Package

Each extractor is a separate module with pattern:

```python
def extract(token, context: dict) -> dict:
    """
    Extract feature from token.

    Args:
        token: markdown-it token
        context: Parser context (lines, config, etc.)

    Returns:
        Dict with extracted data
    """
```

#### `extractors/sections.py`
**Exports**: `extract_sections()`
**Extracts**: Heading hierarchy, section structure

#### `extractors/paragraphs.py`
**Exports**: `extract_paragraph()`
**Extracts**: Paragraph content and metadata

#### `extractors/lists.py`
**Exports**: `extract_list()`, `extract_list_item()`
**Extracts**: Ordered and unordered lists with nesting

#### `extractors/codeblocks.py`
**Exports**: `extract_code_block()`, `extract_code_fence()`
**Extracts**: Fenced and indented code blocks

#### `extractors/tables.py`
**Exports**: `extract_table()`
**Extracts**: Table structure, headers, rows, cells

#### `extractors/media.py`
**Exports**: `extract_image()`
**Extracts**: Images with alt text, URLs, titles

#### `extractors/links.py`
**Exports**: `extract_link()`
**Extracts**: Links with validation

#### `extractors/footnotes.py`
**Exports**: `extract_footnote_ref()`, `extract_footnote_block()`
**Extracts**: Footnote references and content

#### `extractors/blockquotes.py`
**Exports**: `extract_blockquote()`
**Extracts**: Blockquote content

#### `extractors/html.py`
**Exports**: `extract_html_block()`, `extract_html_inline()`
**Extracts**: HTML content with security checks

**Common Pattern**: All extractors:
- Accept `token` and `context`
- Return dict with extracted data
- No side effects
- No dependencies on other extractors

---

### `ir.py`
**Purpose**: Document Intermediate Representation
**Dependencies**: `exceptions`, `utils`
**Exports**:
- `DocumentIR` - Main IR class
- `DocNode` - Node in document tree
- `ChunkPolicy` - Chunking policy
- `Chunk` - Individual chunk
- `ChunkResult` - Chunking result

**Responsibility**: Provide clean IR for RAG pipelines. Boundary between parser and chunker.

---

### `normalize.py`
**Purpose**: Text normalization
**Dependencies**: `utils`
**Exports**:
- `normalize_whitespace()` - Normalize whitespace
- `normalize_unicode()` - Normalize to NFC
- `redact_urls()` - Redact URLs for privacy

**Responsibility**: Text normalization operations.

---

### `serialize.py`
**Purpose**: Output serialization
**Dependencies**: `ir`
**Exports**:
- `to_dict()` - Convert IR to dict
- `to_json()` - Convert IR to JSON
- `to_markdown()` - Convert IR back to markdown (future)

**Responsibility**: Serialize IR to various formats.

---

### `core.py`
**Purpose**: Main parser orchestrator
**Dependencies**: All modules
**Lines**: <200 (slim orchestrator)
**Exports**:
- `MarkdownParser` - Main parser class (slim version)

**Responsibility**:
- Orchestrate parsing pipeline
- Delegate to extractors
- Apply security policies
- Build IR
- Return results

**NOT responsible for**:
- Actual extraction logic (delegates to extractors)
- Security validation (delegates to security/)
- Utility operations (delegates to utils/)

---

## Import Rules

### ✅ CORRECT (Absolute Imports)

```python
from doxstrux.markdown.exceptions import MarkdownSecurityError
from doxstrux.markdown.config import SECURITY_PROFILES
from doxstrux.markdown.utils.token_utils import walk_tokens_iter
from doxstrux.markdown.extractors.sections import extract_sections
```

### ❌ WRONG (Relative Imports)

```python
from .exceptions import MarkdownSecurityError  # NO!
from ..config import SECURITY_PROFILES  # NO!
from .utils.token_utils import walk_tokens_iter  # NO!
```

---

## Backward Compatibility

### Façade Pattern

The existing `src/doxstrux/markdown_parser_core.py` will remain as a **façade**:

```python
from doxstrux.markdown.core import MarkdownParser

class MarkdownParserCore(MarkdownParser):
    """
    Backward-compatible façade for the modular parser.

    Preserves the original API while delegating to modular implementation.
    """
    pass
```

This ensures:
- ✅ Existing code continues to work
- ✅ `from doxstrux.markdown_parser_core import MarkdownParserCore` still works
- ✅ No breaking changes for users

---

## Testing Strategy

### After Each Module Move/Extract:

1. **Unit tests**: `pytest` (63/63 must pass)
2. **Baseline tests**: All 542 baseline tests must pass
3. **CI gates**: G1-G5 must all pass
4. **No behavior change**: Output must be byte-for-byte identical

### Module-Specific Tests:

Each new module should have:
- Unit tests for its public functions
- Integration tests with the full parser
- Edge case coverage

---

## Migration Path

**Phase 7 Tasks**:

1. ✅ **Task 7.1**: Create namespace structure (THIS TASK)
2. **Task 7.2**: Move existing modules (exceptions, document_ir, security_validators, token_replacement_lib)
3. **Task 7.3**: Extract line & text utilities
4. **Task 7.4**: Extract configuration & budgets
5. **Task 7.5**: Extract simple extractors (media, footnotes, blockquotes, html)
6. **Task 7.6**: Extract complex extractors (sections, paragraphs, lists, codeblocks, tables, links)
7. **Task 7.7**: Extract security & normalization
8. **Task 7.8**: Create façade & slim core
9. **Task 7.9**: Phase 7 validation & completion

**Rule**: Test after EVERY task. No exceptions.

---

## Benefits of This Architecture

### Maintainability
- Each module has single responsibility
- Easy to locate code
- Changes isolated to specific modules

### Testability
- Each module can be tested independently
- Clear interfaces make mocking easy
- Unit tests are focused

### Extensibility
- New extractors easy to add
- Security policies pluggable
- IR can evolve independently

### Performance
- Lazy loading possible
- Code splitting for web use
- Smaller files faster to load

---

**Status**: Task 7.1 complete - Namespace structure ready
**Next**: Task 7.2 - Move existing modules into new structure
**Target**: Complete Phase 7 before making repository public
