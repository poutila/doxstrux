# Doxstrux Reference

**Doxstrux** is a markdown structure extraction library designed for RAG pipelines and AI preprocessing.

| Attribute | Value |
|-----------|-------|
| Version | 0.2.1 |
| Python | 3.12+ |
| License | MIT |

---

## 1. Core Philosophy

1. **Extract everything, analyze nothing** — Parser extracts structure, not meaning
2. **Security-first design** — Three profiles (strict/moderate/permissive)
3. **No file I/O in core** — Parser accepts content strings, not file paths
4. **Plain dict outputs** — No Pydantic models in core
5. **Zero regex in parser** — All parsing via markdown-it token AST

---

## 2. Public API

### 2.1 Main Entry Point

```python
from doxstrux import parse_markdown_file

result = parse_markdown_file(
    "document.md",                    # Path or string
    config={"allows_html": False},    # Optional config
    security_profile="moderate"       # strict/moderate/permissive
)
```

This is the **only function users should call**. It handles file reading with encoding detection, security validation, and full structure extraction.

### 2.2 Public Exports

```python
from doxstrux import (
    parse_markdown_file,     # Main entry point
    DocumentIR,              # IR for RAG chunking
    DocNode,                 # Document tree node
    ChunkPolicy,             # Chunking configuration
    Chunk,                   # Output chunk
    PromptInjectionCheck     # Security check result
)
```

### 2.3 Internal Parser (Advanced Use)

```python
from doxstrux.markdown_parser_core import MarkdownParserCore

parser = MarkdownParserCore(content_string, security_profile="moderate")
result = parser.parse()

# Class methods
features = MarkdownParserCore.get_available_features()
validation = MarkdownParserCore.validate_content(content, "strict")
```

---

## 3. Output Structure

The parser returns a plain dict with this structure:

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
        "sections": list[dict],      # Hierarchical sections with spans
        "headings": list[dict],      # Flat heading list
        "paragraphs": list[dict],    # With word_count, section_id
        "lists": list[dict],
        "tasklists": list[dict],
        "tables": list[dict],        # With is_ragged, is_pure flags
        "code_blocks": list[dict],   # With language detection
        "links": list[dict],         # With scheme validation
        "images": list[dict],
        "blockquotes": list[dict],
        "footnotes": dict,
        "html_blocks": list[dict],
        "html_inline": list[dict],
        "math": dict
    },
    "mappings": {
        "line_to_type": dict,        # Line number → "prose" or "code"
        "prose_lines": list[int],
        "code_lines": list[int],
        "code_blocks": list[dict]    # Language + line spans
    }
}
```

### 3.1 Section Structure (Key for Chunking)

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
    "text_content": "Item one. Item two. Item three..."  # Cleaned prose
}
```

### 3.2 Paragraph Structure

```python
{
    "id": "para_0",
    "text": "This is the introduction paragraph...",
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

### 4.1 Three Security Profiles

| Setting | Strict | Moderate | Permissive |
|---------|--------|----------|------------|
| **Max Content Size** | 100 KB | 1 MB | 10 MB |
| **Max Lines** | 2,000 | 10,000 | 50,000 |
| **Max Tokens** | 50,000 | 200,000 | 1,000,000 |
| **Recursion Depth** | 50 | 100 | 150 |
| **Max Nodes** | 10,000 | 50,000 | 200,000 |
| **Max Table Cells** | 1,000 | 10,000 | 50,000 |
| **Allows HTML** | No | Yes | Yes |
| **Allows Data URI** | No | Yes | Yes |
| **Max Data URI Size** | 0 | 10 KB | 100 KB |
| **Injection Scan Chars** | 4,096 | 2,048 | 1,024 |
| **Quarantine on Injection** | Yes | No | No |
| **Strip All HTML** | Yes | No | No |

**Profile Selection:**
- `strict` — Untrusted user input, web-scraped content
- `moderate` — Standard trusted documents (default)
- `permissive` — Fully trusted internal documents

### 4.2 Security Validations

All validations are **fail-closed** (suspicious content is blocked, not logged):

1. Content size limits — Prevents resource exhaustion
2. Recursion depth limits — Prevents stack overflow
3. Node/cell budgets — Prevents memory bombs
4. Link scheme validation — Blocks `javascript:`, `vbscript:`, `data:text/html`
5. BiDi control detection — Detects text direction manipulation
6. Confusable character detection — Detects homograph attacks
7. HTML sanitization — Filters dangerous tags
8. Script tag detection — Blocks `<script>` tags
9. Event handler detection — Blocks `onclick`, `onerror`, etc.
10. Prompt injection detection — Scans for injection patterns

### 4.3 Embedding Safety Signals

```python
# Check before embedding in RAG
if result["metadata"]["security"]["embedding_blocked"]:
    reason = result["metadata"]["security"]["embedding_block_reason"]
    raise ValueError(f"Document blocked: {reason}")

if result["metadata"]["security"]["quarantined"]:
    reasons = result["metadata"]["security"]["quarantine_reasons"]
    # Review or reject
```

**Embedding Block Triggers:**
- Script tags detected
- Disallowed link schemes (`javascript:`, etc.)
- Style-based JavaScript injection
- Event handlers (`onclick`, `onerror`)

**Quarantine Triggers:**
- Ragged tables (data may be corrupted)
- Long footnotes (>512 chars)
- Prompt injection detected

### 4.4 Prompt Injection Detection

```python
from doxstrux.markdown.security.validators import check_prompt_injection

result = check_prompt_injection(text, profile="strict")
# result.suspected: bool (True if injection OR error — fail-closed)
# result.reason: "pattern_match", "validator_error", "no_match"
# result.pattern: Optional[str]
```

Detected patterns include: "ignore previous instructions", "disregard previous instructions", "system: you are a", "pretend you are", "act as if", "bypass your instructions", "override your instructions"

---

## 5. Configuration

### 5.1 Parser Config

```python
config = {
    "preset": "gfm",              # "commonmark" or "gfm"
    "plugins": ["table"],          # Builtin plugins
    "allows_html": False,          # HTML handling
    "external_plugins": [          # External plugins
        "footnote",
        "tasklists",
        "front_matter"
    ]
}
```

### 5.2 Available Plugins by Profile

| Plugin | Strict | Moderate | Permissive |
|--------|--------|----------|------------|
| table | Yes | Yes | Yes |
| strikethrough | No | Yes | Yes |
| front_matter | Yes | Yes | Yes |
| tasklists | Yes | Yes | Yes |
| footnote | No | Yes | Yes |
| deflist | No | No | Yes |

---

## 6. Document IR (for RAG)

The parser can convert output to a Document IR optimized for chunking:

```python
parser = MarkdownParserCore(content)
ir = parser.to_ir(source_id="docs/intro.md")

# ir.root — DocNode tree
# ir.link_graph — Section → linked sections
# ir.security — Security metadata
# ir.frontmatter — YAML frontmatter
```

### 6.1 IR Schema

Schema version: `md-ir@1.0.0`

```python
@dataclass
class DocNode:
    id: str
    type: str           # "section", "paragraph", "code_block", etc.
    text: str           # Content text
    meta: dict          # Element-specific metadata
    span: tuple | None  # (start_char, end_char)
    line_span: tuple | None  # (start_line, end_line)
    children: list[DocNode]
```

### 6.2 Link Graph

For retrieval expansion:

```python
ir.link_graph = {
    "section_introduction": ["section_background", "section_methods"],
    "section_methods": ["section_results"],
    ...
}
```

---

## 7. Architecture

### 7.1 Project Structure

```
doxstrux/
├── src/doxstrux/
│   ├── __init__.py              # Public exports
│   ├── api.py                   # parse_markdown_file() — MAIN ENTRY
│   ├── markdown_parser_core.py  # Core parser (1973 lines)
│   └── markdown/
│       ├── config.py            # Security profiles (SSOT)
│       ├── budgets.py           # Resource limits
│       ├── exceptions.py        # Custom exceptions
│       ├── ir.py                # Document IR for RAG
│       ├── extractors/          # 11 modular extractors
│       │   ├── sections.py
│       │   ├── paragraphs.py
│       │   ├── lists.py
│       │   ├── codeblocks.py
│       │   ├── tables.py
│       │   ├── links.py
│       │   ├── media.py
│       │   ├── footnotes.py
│       │   ├── blockquotes.py
│       │   ├── html.py
│       │   └── math.py
│       ├── security/
│       │   └── validators.py    # Security validation
│       └── utils/
│           ├── encoding.py      # Robust encoding detection
│           ├── line_utils.py
│           ├── text_utils.py
│           └── token_utils.py
├── tests/
├── tools/
│   ├── baseline_test_runner.py
│   ├── test_feature_counts.py
│   ├── baseline_outputs/        # 542 frozen baselines (READ-ONLY)
│   └── test_mds/                # 542 test files (READ-ONLY)
└── pyproject.toml
```

### 7.2 Key Design Decisions

**Zero Regex in Parser:**
Eliminates ReDoS vulnerabilities. All parsing uses markdown-it-py's token-based AST. ~10 regex patterns retained only in `security/validators.py` for prompt injection/BiDi detection.

**Modular Extractors:**
Each of 11 extractors follows a single-responsibility pattern with dependency injection for testability.

**No File I/O in Core:**
`MarkdownParserCore` accepts content strings only. File I/O handled by `api.py`.

**Fail-Closed Security:**
All validation errors raise exceptions. No "strict mode" toggles.

---

## 8. Dependencies

**Core:**
- `markdown-it-py>=4.0.0` — Parsing engine
- `mdit-py-plugins>=0.5.0` — Extended features
- `pyyaml>=6.0.2` — YAML frontmatter
- `charset-normalizer>=3.4.2` — Encoding detection

**Dev:**
- `pytest>=8.4.1`, `pytest-cov>=6.2.1`
- `mypy`, `ruff`, `black`, `bandit`, `vulture`

---

## 9. Performance

| Metric | Value |
|--------|-------|
| Parse time (avg) | ~1.02 ms/file |
| Total suite time | ~550 ms (542 files) |
| Memory overhead | Minimal (plain dict) |
| Startup time | ~200 ms |

---

## 10. Comparison with Alternatives

| Feature | Doxstrux | LangChain | Unstructured.io |
|---------|----------|-----------|-----------------|
| Structure extraction | Full hierarchy | Flat text | Generic |
| Section boundaries | Precise spans | Basic splits | Basic |
| Security validation | Comprehensive | None | None |
| Prompt injection detection | Yes | No | No |
| Embedding safety flags | Yes | No | No |
| Token-based parsing | Yes | Regex-based | Regex-based |
| Performance | ~1ms/file | Slower | Slower |
| Dependencies | Minimal | Heavy | Heavy |
