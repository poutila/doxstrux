# AI Assistant User Manual for Doxstrux

This manual is the definitive reference for AI assistants working with the doxstrux codebase. It was written by an AI assistant for AI assistants - every detail matters because **I will need to use this**.

---

## Table of Contents

1. [Critical Rules - Read First](#1-critical-rules---read-first)
2. [Project Overview](#2-project-overview)
3. [Project Structure](#3-project-structure)
4. [Public API](#4-public-api)
5. [Security Model](#5-security-model)
6. [Configuration](#6-configuration)
7. [Testing Infrastructure](#7-testing-infrastructure)
8. [Development Workflow](#8-development-workflow)
9. [Architecture Decisions](#9-architecture-decisions)
10. [Common Pitfalls](#10-common-pitfalls)
11. [Quick Reference](#11-quick-reference)

---

## 1. Critical Rules - Read First

### 1.1 Python Environment (MANDATORY)

**NEVER use system python. ALWAYS use `.venv/bin/python`.**

```bash
# CORRECT - Use this always
.venv/bin/python tools/generate_baseline_outputs.py
.venv/bin/python tools/baseline_test_runner.py
.venv/bin/python -m pytest

# WRONG - Will produce silently corrupted output
python3 tools/generate_baseline_outputs.py
python tools/baseline_test_runner.py
```

**Why this matters**: System python lacks `mdit-py-plugins`. The code runs without errors but produces **wrong output** because optional dependencies fail silently. Tables, footnotes, and tasklists will be parsed incorrectly. Baselines generated with system python are **corrupted** - undetectable until parity tests fail.

### 1.2 Immutable Directories (READ-ONLY)

These directories must NEVER be edited without explicit human approval:

| Directory | Contents | Why Protected |
|-----------|----------|---------------|
| `tools/baseline_outputs/` | 542 frozen baseline JSON files | Ground truth for regression testing |
| `tools/test_mds/` | 542 test markdown files | Test corpus - changes invalidate all baselines |
| `tools/mds.zip` | Compressed backup | Archive integrity |

**To modify**: Stop. Ask for human approval. Explain the change and its impact on all 542 baseline tests.

### 1.3 Clean Table Principle

No work ships until fully correct:

- No unresolved TODOs, placeholders, or speculative comments
- No silent exceptions - all errors raise unconditionally
- No temporary band-aids masking root causes
- No "needs to be checked later" deferrals

**Silent Exception Ban**:

```python
# FORBIDDEN - conditional raise
except Exception as e:
    if strict:
        raise SpecLoadError(spec_path, e) from e
    errors.append((spec_path, e))  # Swallowed!

# REQUIRED - unconditional raise
except Exception as e:
    raise SpecLoadError(spec_path, e) from e
```

### 1.4 No Weak Tests

Tests must assert meaningful behavior, not just existence:

```python
# WEAK - Avoid
def test_parser_exists():
    assert hasattr(module, 'MarkdownParserCore')

# STRONG - Required
def test_parser_extracts_headings():
    parser = MarkdownParserCore("# Hello\n## World")
    result = parser.parse()
    assert len(result["structure"]["headings"]) == 2
    assert result["structure"]["headings"][0]["level"] == 1
    assert result["structure"]["headings"][0]["text"] == "Hello"
```

---

## 2. Project Overview

**Doxstrux** is a markdown structure extraction library designed for RAG pipelines and AI preprocessing.

| Attribute | Value |
|-----------|-------|
| Version | 0.2.1 |
| Python | 3.12+ (strict requirement) |
| License | MIT |
| Test Coverage | 80% minimum enforced |
| Baseline Tests | 542 (100% must pass) |

### Core Philosophy

1. **Extract everything, analyze nothing** - Parser extracts structure, not meaning
2. **Security-first design** - Three profiles (strict/moderate/permissive)
3. **No file I/O in core** - Parser accepts content strings, not file paths
4. **Plain dict outputs** - No Pydantic models in core
5. **Zero regex in parser** - All parsing via markdown-it token AST

---

## 3. Project Structure

```
doxstrux/
├── src/doxstrux/
│   ├── __init__.py              # Public exports
│   ├── api.py                   # parse_markdown_file() - MAIN ENTRY POINT
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
├── tests/                       # pytest tests (80% coverage required)
├── tools/
│   ├── baseline_test_runner.py  # Parity testing
│   ├── test_feature_counts.py   # Feature validation
│   ├── baseline_outputs/        # 542 frozen baselines (READ-ONLY)
│   └── test_mds/                # 542 test files (READ-ONLY)
├── pyproject.toml
├── CLAUDE.md                    # Development guide
└── SECURITY.md                  # Security documentation
```

---

## 4. Public API

### 4.1 Main Entry Point

```python
from doxstrux import parse_markdown_file

result = parse_markdown_file(
    "document.md",                    # Path or string
    config={"allows_html": False},    # Optional config
    security_profile="moderate"       # strict/moderate/permissive
)
```

**This is the ONLY function users should call.** It handles:
- File reading with robust encoding detection
- Security validation
- Full structure extraction

### 4.2 Return Structure

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
            "quarantined": bool
        }
    },
    "content": {
        "raw": str,
        "lines": list[str]
    },
    "structure": {
        "sections": list[dict],
        "headings": list[dict],
        "paragraphs": list[dict],
        "lists": list[dict],
        "tasklists": list[dict],
        "tables": list[dict],
        "code_blocks": list[dict],
        "links": list[dict],
        "images": list[dict],
        "blockquotes": list[dict],
        "footnotes": dict,
        "html_blocks": list[dict],
        "html_inline": list[dict],
        "math": dict
    },
    "mappings": {
        "line_to_type": dict  # Line number -> "prose" or "code"
    }
}
```

### 4.3 Public Exports

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

### 4.4 Internal Parser (Advanced Use Only)

```python
from doxstrux.markdown_parser_core import MarkdownParserCore

# Direct usage - NOT recommended for normal use
parser = MarkdownParserCore(content_string, security_profile="moderate")
result = parser.parse()

# Class methods
features = MarkdownParserCore.get_available_features()
validation = MarkdownParserCore.validate_content(content, "strict")
```

---

## 5. Security Model

### 5.1 Three Security Profiles

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

**Note on Injection Scan Chars**: Strict scans MORE characters (stricter security = more thorough scanning).

### 5.2 Security Validations

All validations are **fail-closed** - suspicious content is blocked, not logged:

1. **Content size limits** - Prevents resource exhaustion
2. **Recursion depth limits** - Prevents stack overflow
3. **Node/cell budgets** - Prevents memory bombs
4. **Link scheme validation** - Blocks `javascript:`, `vbscript:`, `data:text/html`
5. **BiDi control detection** - Detects text direction manipulation
6. **Confusable character detection** - Detects homograph attacks
7. **HTML sanitization** - Filters dangerous tags
8. **Script tag detection** - Blocks `<script>` tags
9. **Event handler detection** - Blocks `onclick`, `onerror`, etc.
10. **Prompt injection detection** - Scans for injection patterns

### 5.3 Embedding Blocking

The `embedding_blocked` flag is set when content is too risky for RAG:

```python
result["metadata"]["security"]["embedding_blocked"]  # True = don't embed
```

Triggers:
- Script tags detected
- Disallowed link schemes
- Style-based JavaScript injection
- Prompt injection (strict profile only via quarantine)

### 5.4 Prompt Injection Detection

```python
from doxstrux.markdown.security.validators import check_prompt_injection

result = check_prompt_injection(text, profile="strict")
# result.suspected: bool (True if injection OR error)
# result.reason: "pattern_match", "validator_error", "no_match"
# result.pattern: Optional[str] (matched pattern)
```

**Detected patterns include**:
- "ignore previous instructions"
- "disregard previous instructions"
- "system: you are a"
- "pretend you are"
- "act as if"
- "bypass your instructions"

---

## 6. Configuration

### 6.1 Parser Config

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

### 6.2 Available Plugins by Profile

| Plugin | Strict | Moderate | Permissive |
|--------|--------|----------|------------|
| table | Yes | Yes | Yes |
| strikethrough | No | Yes | Yes |
| front_matter | Yes | Yes | Yes |
| tasklists | Yes | Yes | Yes |
| footnote | No | Yes | Yes |
| deflist | No | No | Yes |

---

## 7. Testing Infrastructure

### 7.1 Test Types

| Type | Command | Purpose |
|------|---------|---------|
| Unit Tests | `pytest` | 80% coverage required |
| Parity Tests | `python tools/baseline_test_runner.py` | 542/542 must pass |
| Feature Tests | `python tools/test_feature_counts.py` | ~94.5% expected |

### 7.2 Baseline Testing System

**Purpose**: Ensure parser output is byte-for-byte identical across refactoring.

**Components**:

1. **SSOT Test Pairs** (`tools/test_mds/`):
   - 542 markdown files with 542 JSON specifications
   - Organized in 32 categories (edge_cases, security, encoding, etc.)

2. **Frozen Baselines** (`tools/baseline_outputs/`):
   - 542 verified parser outputs
   - Read-only (chmod a-w)
   - Ground truth for comparison

3. **Parity Test**:
   - Compares current output to frozen baselines
   - Byte-by-byte JSON comparison
   - 100% pass rate required (542/542)

### 7.3 Running Tests

```bash
# Full pytest suite
.venv/bin/python -m pytest

# With coverage
.venv/bin/python -m pytest --cov=src/doxstrux --cov-report=html

# Parity tests (542 baselines)
.venv/bin/python tools/baseline_test_runner.py \
    --test-dir tools/test_mds \
    --baseline-dir tools/baseline_outputs

# Feature count tests
.venv/bin/python tools/test_feature_counts.py --test-dir tools/test_mds

# Fast subset (single category)
bash tools/run_tests_fast.sh 01_edge_cases
```

### 7.4 Expected Results

| Test | Expected | Notes |
|------|----------|-------|
| pytest | All pass | 80% coverage required |
| Parity | 542/542 (100%) | Zero tolerance |
| Feature counts | ~512/542 (94.5%) | 30 Pandoc failures OK |

---

## 8. Development Workflow

### 8.1 Setup

```bash
git clone https://github.com/doxstrux/doxstrux.git
cd doxstrux
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 8.2 Pre-Commit Checklist

Before committing any changes:

1. **Run pytest**: `.venv/bin/python -m pytest` (must pass)
2. **Check coverage**: Ensure 80% minimum
3. **Run type checking**: `mypy src/doxstrux` (must pass)
4. **Run linting**: `ruff check --fix src/ tests/`
5. **If parser changed**:
   - Run parity: `python tools/baseline_test_runner.py` (must be 542/542)
   - Run features: `python tools/test_feature_counts.py`
6. **Update CHANGELOG.md**

### 8.3 Modifying Parser Behavior

If you need to change parser output:

1. Understand the change is intentional and improves correctness
2. Run parity tests - they will fail
3. **Request human approval** to regenerate baselines
4. Regenerate: `.venv/bin/python tools/generate_baseline_outputs.py`
5. Verify new baselines are correct
6. Make baselines read-only: `chmod -R a-w tools/baseline_outputs/`

---

## 9. Architecture Decisions

### 9.1 Zero Regex in Parser

**Why**: Eliminates ReDoS (Regular Expression Denial of Service) vulnerabilities.

**How**: All parsing uses markdown-it-py's token-based AST:

```python
# Instead of regex like r'^#{1,6}\s+(.*)$'
# We use token types:
if token.type == "heading_open":
    level = int(token.tag[1])  # h1 -> 1, h2 -> 2
```

**Exception**: ~10 regex patterns retained in `security/validators.py` for:
- Prompt injection detection
- BiDi control character detection
- Input is truncated per profile before regex applied

### 9.2 Modular Extractors

**Why**: Single responsibility, easier testing, maintainability.

**Pattern**: All 11 extractors follow this structure:

```python
def extract_<element>(
    tree: Any,
    process_tree_func: Callable,  # Dependency injection
    <other_helpers>,
) -> list[dict]:
    """Extract <element> with metadata."""
    elements = []

    def processor(node, ctx, level):
        if node.type == "<element_type>":
            ctx.append({
                "id": f"<element>_{len(ctx)}",
                "start_line": node.map[0] if node.map else None,
                # ... fields
            })
            return False  # Don't recurse into element
        return True  # Continue recursion

    process_tree_func(tree, processor, elements)
    return elements
```

### 9.3 No File I/O in Core

**Why**: Separation of concerns.

- `MarkdownParserCore` accepts content strings only
- `parse_markdown_file()` (in `api.py`) handles file I/O
- Encoding detection is handled by `encoding.py`

### 9.4 Plain Dict Outputs

**Why**: Lightweight, flexible, easy JSON serialization.

- No Pydantic models in core parser
- Simple dict structures
- Direct JSON serialization for baselines

### 9.5 Fail-Closed Security

**Why**: Security errors must never be silently ignored.

- All validation errors raise exceptions
- No "strict mode" toggles
- Suspicious content blocks embedding via `embedding_blocked` flag

---

## 10. Common Pitfalls

### 10.1 Using System Python

**Symptom**: Baselines appear to generate successfully but parity tests fail later.

**Cause**: System python lacks `mdit-py-plugins`.

**Fix**: Always use `.venv/bin/python`.

### 10.2 Modifying Baselines Without Approval

**Symptom**: `git status` shows changes in `tools/baseline_outputs/`.

**Cause**: Accidentally edited or regenerated baselines.

**Fix**: `git checkout tools/baseline_outputs/`. Request approval before regenerating.

### 10.3 Introducing Regex in Parser

**Symptom**: Code review flags regex pattern in parser module.

**Cause**: Misunderstanding zero-regex architecture.

**Fix**: Use token-based extraction. Regex only allowed in `security/validators.py`.

### 10.4 Silent Exception Handling

**Symptom**: Test passes but behavior is wrong.

**Cause**: Exception caught and logged instead of raised.

**Fix**: Always re-raise exceptions. No conditional error handling.

```python
# WRONG
except Exception as e:
    logger.warning(f"Ignoring: {e}")
    return default_value

# RIGHT
except Exception as e:
    raise ProcessingError(f"Failed: {e}") from e
```

### 10.5 Non-Deterministic Output

**Symptom**: Same input produces different JSON on different runs.

**Cause**: Unsorted set/dict iteration.

**Fix**: Always sort collections before JSON serialization:

```python
# WRONG
{"items": list(my_set)}

# RIGHT
{"items": sorted(list(my_set))}
```

### 10.6 Wrong Security Profile

**Symptom**: User input bypasses security checks.

**Cause**: Using "permissive" for untrusted input.

**Fix**:
- `strict` - Untrusted user input
- `moderate` - Standard trusted documents (default)
- `permissive` - Fully trusted internal documents

---

## 11. Quick Reference

### 11.1 Essential Commands

```bash
# Parse a file
.venv/bin/python -c "from doxstrux import parse_markdown_file; print(parse_markdown_file('README.md'))"

# Run tests
.venv/bin/python -m pytest

# Run with coverage
.venv/bin/python -m pytest --cov=src/doxstrux

# Parity tests (542 baselines)
.venv/bin/python tools/baseline_test_runner.py --test-dir tools/test_mds --baseline-dir tools/baseline_outputs

# Type checking
mypy src/doxstrux

# Linting
ruff check --fix src/ tests/
```

### 11.2 Key Files

| File | Purpose |
|------|---------|
| `src/doxstrux/api.py` | Public entry point |
| `src/doxstrux/markdown_parser_core.py` | Core parser |
| `src/doxstrux/markdown/config.py` | Security profiles (SSOT) |
| `src/doxstrux/markdown/security/validators.py` | Security validation |
| `tools/baseline_test_runner.py` | Parity testing |
| `CLAUDE.md` | Development guide |

### 11.3 Dependencies

**Core**:
- `markdown-it-py>=4.0.0` - Parsing engine
- `mdit-py-plugins>=0.5.0` - Extended features
- `pyyaml>=6.0.2` - YAML frontmatter
- `charset-normalizer>=3.4.2` - Encoding detection

**Dev**:
- `pytest>=8.4.1`
- `pytest-cov>=6.2.1`
- `mypy`, `ruff`, `black`, `bandit`, `vulture`

### 11.4 Status

| Metric | Value |
|--------|-------|
| Version | 0.2.1 |
| Python | 3.12+ |
| Test Coverage | 80%+ |
| Baseline Tests | 542/542 passing |
| Core Parser Lines | 1,973 |
| Regex in Parser | 0 (10 in security only) |
| Extractors | 11 modules |

---

## Final Notes

This manual is written by an AI assistant who will use it. Every detail is here because it matters:

1. **Always `.venv/bin/python`** - System python corrupts silently
2. **Never edit baselines** - Ask human approval first
3. **No silent exceptions** - All errors must raise
4. **No regex in parser** - Token-based only
5. **Test everything** - 80% coverage, 542/542 parity

When in doubt, read `CLAUDE.md`. When still in doubt, ask.
