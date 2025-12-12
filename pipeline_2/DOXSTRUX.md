# Doxstrux

**Markdown structure extraction for RAG pipelines.**

```
pip install doxstrux
```

| Attribute | Value |
|-----------|-------|
| Version | 0.2.1 |
| Python | 3.12+ |
| License | MIT |

---

## 1. Overview

Doxstrux parses markdown into structured output optimized for RAG:

```python
from doxstrux import parse_markdown_file, chunk_document, ChunkPolicy

# Parse
result = parse_markdown_file("doc.md", security_profile="strict")

# Chunk
chunks = chunk_document(result, ChunkPolicy(target_tokens=500))

# Use chunks for embedding
for chunk in chunks:
    print(f"{chunk.chunk_id}: {chunk.section_path}")
```

**Core Philosophy:**

1. **Extract everything, analyze nothing** — Parser extracts structure, not meaning
2. **Security-first** — Three profiles with fail-closed validation
3. **No file I/O in core** — Parser accepts content strings
4. **Plain dict outputs** — No Pydantic in core
5. **Zero regex in parser** — Token-based AST only

---

## 2. Parser API

### 2.1 Main Entry Point

```python
from doxstrux import parse_markdown_file

result = parse_markdown_file(
    "document.md",                    # Path
    config={"allows_html": False},    # Optional
    security_profile="moderate"       # strict/moderate/permissive
)
```

### 2.2 Public Exports

```python
from doxstrux import (
    parse_markdown_file,     # Main entry point
    chunk_document,          # Chunking function
    ChunkPolicy,             # Chunking configuration
    Chunk,                   # Output chunk
    DocumentIR,              # IR for advanced use
    DocNode,                 # Document tree node
    PromptInjectionCheck     # Security check result
)
```

### 2.3 Internal Parser (Advanced)

```python
from doxstrux.markdown_parser_core import MarkdownParserCore

parser = MarkdownParserCore(content_string, security_profile="moderate")
result = parser.parse()
```

---

## 3. Parser Output

The parser returns a plain dict:

```python
{
    "metadata": {
        "source_path": str,
        "encoding": {"detected": str, "confidence": float},
        "security": {
            "profile_used": str,
            "warnings": list,
            "prompt_injection_in_content": bool,
            "embedding_blocked": bool,
            "quarantined": bool,
            "quarantine_reasons": list,
            "embedding_block_reason": str | None
        }
    },
    "content": {
        "raw": str,
        "lines": list[str]
    },
    "structure": {
        "sections": list[dict],      # Hierarchical with spans
        "headings": list[dict],
        "paragraphs": list[dict],    # With word_count, section_id
        "lists": list[dict],
        "tasklists": list[dict],
        "tables": list[dict],        # With is_ragged, is_pure
        "code_blocks": list[dict],   # With language
        "links": list[dict],         # With scheme validation
        "images": list[dict],
        "blockquotes": list[dict],
        "footnotes": dict,
        "html_blocks": list[dict],
        "html_inline": list[dict],
        "math": dict
    },
    "mappings": {
        "line_to_type": dict,        # Line → "prose" or "code"
        "prose_lines": list[int],
        "code_lines": list[int],
        "code_blocks": list[dict]
    }
}
```

### 3.1 Section Structure

```python
{
    "id": "section_methodology",
    "level": 3,
    "title": "Methodology",
    "slug": "methodology",
    "start_line": 15,
    "end_line": 33,
    "start_char": 286,
    "end_char": 562,
    "parent_id": "section_background",
    "child_ids": [],
    "raw_content": "### Methodology\n\n- Item one\n...",
    "text_content": "Item one. Item two. Item three..."  # Cleaned
}
```

### 3.2 Paragraph Structure

```python
{
    "id": "para_0",
    "text": "This is the introduction...",
    "start_line": 7,
    "end_line": 8,
    "section_id": "section_introduction",
    "word_count": 10,
    "has_links": False,
    "has_emphasis": True,
    "has_code": False
}
```

### 3.3 Code Block Structure

```python
{
    "id": "code_0",
    "type": "fenced",
    "language": "python",
    "content": "def hello():\n    return 'world'",
    "start_line": 21,
    "end_line": 26,
    "section_id": "section_methodology"
}
```

---

## 4. Security Model

### 4.1 Three Profiles

| Setting | Strict | Moderate | Permissive |
|---------|--------|----------|------------|
| Max Content Size | 100 KB | 1 MB | 10 MB |
| Max Lines | 2,000 | 10,000 | 50,000 |
| Max Tokens | 50,000 | 200,000 | 1,000,000 |
| Max Nodes | 10,000 | 50,000 | 200,000 |
| Max Table Cells | 1,000 | 10,000 | 50,000 |
| Allows HTML | No | Yes | Yes |
| Injection Scan | 4,096 chars | 2,048 chars | 1,024 chars |
| Quarantine on Injection | Yes | No | No |

**When to use each:**
- `strict` — Untrusted input, web-scraped content
- `moderate` — Trusted documents (default)
- `permissive` — Internal documents only

### 4.2 Security Validations

All validations are **fail-closed**:

1. Content size limits
2. Recursion depth limits
3. Node/cell budgets
4. Link scheme validation (blocks `javascript:`, `vbscript:`)
5. BiDi control detection
6. HTML sanitization
7. Script tag detection
8. Event handler detection
9. Prompt injection detection

### 4.3 Embedding Safety Signals

```python
security = result["metadata"]["security"]

if security["embedding_blocked"]:
    raise ValueError(security["embedding_block_reason"])

if security["quarantined"]:
    # Review or reject
    print(security["quarantine_reasons"])
```

### 4.4 Prompt Injection Detection

```python
from doxstrux.markdown.security.validators import check_prompt_injection

check = check_prompt_injection(text, profile="strict")
# check.suspected: bool
# check.reason: "pattern_match", "validator_error", "no_match"
# check.pattern: Optional[str]
```

---

## 5. Chunker

The chunker transforms parser output into embedding-ready chunks.

### 5.1 Design Philosophy

The parser already did the hard work. Sections have:
- Clean `text_content` (markdown stripped)
- Precise character/line spans
- Hierarchical parent-child relationships
- Word counts per paragraph

The chunker walks the section tree, estimates sizes, and emits chunks respecting semantic boundaries.

**Core Principles:**
1. Never split mid-paragraph
2. Never split mid-code-block
3. Respect section boundaries
4. Include section path for context
5. Stable IDs (deterministic)
6. Propagate security flags

### 5.2 ChunkPolicy

```python
@dataclass
class ChunkPolicy:
    mode: Literal["semantic", "fixed", "code_aware"] = "semantic"
    target_tokens: int = 600
    overlap_tokens: int = 60
    min_chunk_tokens: int = 100
    max_chunk_tokens: int = 1000
    respect_boundaries: bool = True
    include_code: bool = True
    include_tables: bool = True
    normalize_whitespace: bool = True
    normalize_unicode: bool = True
    token_estimator: Literal["bytes", "chars", "tiktoken"] = "bytes"
```

**Modes:**

| Mode | Description | Use Case |
|------|-------------|----------|
| `semantic` | Follow section boundaries | Documentation |
| `fixed` | Split at token count | Large text |
| `code_aware` | Separate code/prose | Technical docs |

### 5.3 Chunk Output

```python
@dataclass
class Chunk:
    chunk_id: str                    # Stable identifier
    section_path: list[str]          # ["intro", "background"]
    text: str                        # Raw text
    normalized_text: str             # Cleaned for embedding
    span: tuple[int, int] | None     # Character offsets
    line_span: tuple[int, int] | None
    token_estimate: int
    chunk_hash: str                  # SHA256 for dedup
    risk_flags: list[str]            # Security warnings
    links: list[dict]
    images: list[dict]
    meta: dict
```

### 5.4 Chunker API

```python
from doxstrux import parse_markdown_file, chunk_document, ChunkPolicy

result = parse_markdown_file("doc.md", security_profile="strict")

policy = ChunkPolicy(mode="semantic", target_tokens=500)
chunk_result = chunk_document(result, policy)

for chunk in chunk_result.chunks:
    print(f"{chunk.chunk_id}: {chunk.token_estimate} tokens")
```

### 5.5 Policy Presets

```python
# Documentation
POLICY_DOCS = ChunkPolicy(target_tokens=600, max_chunk_tokens=1000)

# Code-heavy
POLICY_CODE = ChunkPolicy(mode="code_aware", target_tokens=400)

# PDFs (higher overlap)
POLICY_PDF = ChunkPolicy(target_tokens=500, overlap_tokens=75)
```

### 5.6 Edge Cases

**Oversized content:** Emitted with `risk_flags` warning, not split mid-unit.

**Empty sections:** Skipped.

**Security-blocked:** Raises `SecurityError` unless `policy.allow_blocked=True`.

---

## 6. Configuration

### 6.1 Parser Config

```python
config = {
    "preset": "gfm",              # "commonmark" or "gfm"
    "plugins": ["table"],
    "allows_html": False,
    "external_plugins": ["footnote", "tasklists", "front_matter"]
}
```

### 6.2 Plugins by Profile

| Plugin | Strict | Moderate | Permissive |
|--------|--------|----------|------------|
| table | Yes | Yes | Yes |
| strikethrough | No | Yes | Yes |
| front_matter | Yes | Yes | Yes |
| tasklists | Yes | Yes | Yes |
| footnote | No | Yes | Yes |
| deflist | No | No | Yes |

---

## 7. Document IR

For advanced use, convert output to a tree structure:

```python
parser = MarkdownParserCore(content)
ir = parser.to_ir(source_id="docs/intro.md")

# ir.root — DocNode tree
# ir.link_graph — Section → linked sections
# ir.security — Security metadata
# ir.frontmatter — YAML frontmatter
```

### 7.1 DocNode Schema

```python
@dataclass
class DocNode:
    id: str
    type: str           # "section", "paragraph", "code_block"
    text: str
    meta: dict
    span: tuple | None
    line_span: tuple | None
    children: list[DocNode]
```

### 7.2 Link Graph

For retrieval expansion:

```python
ir.link_graph = {
    "section_introduction": ["section_background", "section_methods"],
    "section_methods": ["section_results"],
}
```

---

## 8. Architecture

### 8.1 Project Structure

```
doxstrux/
├── src/doxstrux/
│   ├── __init__.py              # Public exports
│   ├── api.py                   # parse_markdown_file()
│   ├── markdown_parser_core.py  # Core parser
│   ├── chunker/                 # Chunking module
│   │   ├── __init__.py
│   │   ├── core.py
│   │   └── estimators.py
│   └── markdown/
│       ├── config.py            # Security profiles
│       ├── budgets.py
│       ├── exceptions.py
│       ├── ir.py
│       ├── extractors/          # 11 modules
│       ├── security/
│       │   └── validators.py
│       └── utils/
├── tests/
├── tools/
│   ├── baseline_outputs/        # 542 frozen baselines
│   └── test_mds/                # 542 test files
└── pyproject.toml
```

### 8.2 Key Decisions

**Zero Regex in Parser:** Eliminates ReDoS. All parsing uses markdown-it-py tokens. ~10 regex patterns only in `security/validators.py`.

**Modular Extractors:** 11 extractors with single responsibility.

**Fail-Closed Security:** All validation errors raise exceptions.

---

## 9. Performance

| Metric | Value |
|--------|-------|
| Parse time | ~1.02 ms/file |
| Suite time | ~550 ms (542 files) |
| Memory | Minimal (plain dict) |

---

## 10. Dependencies

**Core:**
- `markdown-it-py>=4.0.0`
- `mdit-py-plugins>=0.5.0`
- `pyyaml>=6.0.2`
- `charset-normalizer>=3.4.2`

**Dev:**
- `pytest>=8.4.1`, `pytest-cov>=6.2.1`
- `mypy`, `ruff`

---

## 11. Comparison

| Feature | Doxstrux | LangChain | Unstructured.io |
|---------|----------|-----------|-----------------|
| Structure extraction | Full hierarchy | Flat text | Generic |
| Section boundaries | Precise spans | Basic | Basic |
| Security validation | Comprehensive | None | None |
| Prompt injection | Yes | No | No |
| Embedding safety | Yes | No | No |
| Parsing method | Token AST | Regex | Regex |
| Performance | ~1ms/file | Slower | Slower |
