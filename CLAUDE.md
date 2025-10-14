# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL - PYTHON ENVIRONMENT

**NEVER use system python (`python`, `python3`) - ALWAYS use `.venv/bin/python`:**

System python is **OFF LIMITS** because it lacks required dependencies (mdit-py-plugins, etc.). Using system python produces **silently incorrect results** - the code runs but produces wrong output because optional dependencies fail silently.

**Example of silent failure:**
- System python runs `generate_baseline_outputs.py` without errors
- But mdit-py-plugins are missing, so tables/footnotes/tasklists are parsed incorrectly
- Baselines are generated with wrong structure - CORRUPTED DATA
- No error thrown - failure is silent and undetectable until parity tests fail

**CORRECT usage (ALWAYS):**
```bash
.venv/bin/python tools/generate_baseline_outputs.py
.venv/bin/python tools/baseline_test_runner.py
.venv/bin/python tools/ci/ci_gate_parity.py
```

**WRONG usage (NEVER):**
```bash
python3 tools/generate_baseline_outputs.py  # ❌ Creates corrupted baselines
python tools/baseline_test_runner.py        # ❌ Wrong test results
```

## ⚠️ CRITICAL - IMMUTABLE DIRECTORIES

**NEVER EDIT without explicit human approval:**

1. **`/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/baseline_outputs/`**
   - Contains frozen baseline JSON files (542 files)
   - Ground truth for regression testing
   - ANY modification breaks parity testing
   - **MUST be generated with `.venv/bin/python` ONLY**
   - To regenerate: Requires completed phase + human approval

2. **`/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/test_mds/`**
   - Contains test markdown files (542 files)
   - Test corpus for parser validation
   - Modifications invalidate all baselines
   - Changes require human approval only

3. **`/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/mds.zip`**
   - Compressed backup of test corpus
   - Do not modify or regenerate

**These directories are read-only. Ask for human approval before ANY changes.**

## Project Overview

**Doxstrux** is a comprehensive markdown enrichment and parsing library designed for both human users and AI systems. It provides robust markdown parsing with security-first design, extracting structured data from markdown documents while maintaining content integrity.

## Core Architecture

### Modular Parser Design (Phase 7 Complete)
The parser has been fully modularized into focused, single-responsibility components. The core parser (`src/doxstrux/markdown_parser_core.py`) is now **1944 lines** (down from 2900, **-33% reduction**) and delegates to specialized extractor modules:

- **MarkdownParserCore**: Main parser class using markdown-it-py as the parsing engine
- **Security-first design**: Three security profiles (strict, moderate, permissive) with content size limits, plugin validation, and prompt injection detection
- **Universal recursion engine**: Single-pass document parsing with configurable recursion depth limits
- **Pure token-based extraction**: Phase 6 - zero regex, all classification from markdown-it AST tokens
- **Modular extractors**: Phase 7 - 11 specialized extractor modules with clean dependency injection

### Key Design Principles
1. **Extract everything, analyze nothing**: Parser focuses on structural extraction, not semantic analysis
2. **No file I/O in core**: Parser accepts content strings, not file paths
3. **Plain dict outputs**: No Pydantic models in the core parser (keeps it lightweight)
4. **Security layered throughout**: Size limits, plugin validation, HTML sanitization, link scheme validation
5. **Single responsibility**: Each extractor handles one markdown element type
6. **Dependency injection**: Extractors receive parser methods as parameters (no tight coupling)

### Module Structure (Phase 7 - Modularized)
```
src/doxstrux/
├── markdown_parser_core.py          # Core parser (1944 lines) - orchestrates extraction
├── markdown/
│   ├── __init__.py
│   ├── config.py                    # Security profiles and configuration
│   ├── budgets.py                   # Resource budgets and limits
│   ├── exceptions.py                # Custom exception classes
│   ├── ir.py                        # Document IR for RAG chunking
│   ├── extractors/                  # Modular extractors (Phase 7.5 & 7.6)
│   │   ├── __init__.py
│   │   ├── sections.py              # Sections & headings (Phase 7.6.1)
│   │   ├── paragraphs.py            # Paragraphs (Phase 7.6.2)
│   │   ├── lists.py                 # Lists & tasklists (Phase 7.6.3)
│   │   ├── codeblocks.py            # Code blocks (Phase 7.6.4)
│   │   ├── tables.py                # Tables (Phase 7.6.5)
│   │   ├── links.py                 # Links (Phase 7.6.6)
│   │   ├── media.py                 # Images (Phase 7.5.1)
│   │   ├── footnotes.py             # Footnotes (Phase 7.5.2)
│   │   ├── blockquotes.py           # Blockquotes (Phase 7.5.3)
│   │   └── html.py                  # HTML blocks & inline (Phase 7.5.4)
│   ├── security/
│   │   ├── __init__.py
│   │   └── validators.py            # Security validation functions
│   └── utils/
│       ├── __init__.py
│       ├── line_utils.py            # Line slicing utilities
│       ├── text_utils.py            # Text extraction utilities
│       └── token_utils.py           # Token walking utilities
└── md_parser_testing/               # Testing utilities
    ├── __init__.py
    ├── json_utils.py                # JSON serialization helpers
    └── testing_md_parser.py         # Test harness
```

**Phase 7 Achievements**:
- ✅ Core parser reduced by 33% (2900 → 1944 lines)
- ✅ 11 specialized extractor modules created
- ✅ 100% baseline test parity maintained (542/542 tests passing)
- ✅ Clean dependency injection pattern throughout
- ✅ Zero behavioral changes (byte-for-byte output identical)

### Security Features
The parser implements multi-layered security:

**Security Profiles** (via `security_profile` parameter):
- `strict`: 100KB max, 2K lines, limited plugins
- `moderate`: 1MB max, 10K lines, standard plugins (default)
- `permissive`: 10MB max, 50K lines, all plugins

**Security Validations**:
- Content size and line count limits
- Recursion depth limits (50-150 depending on profile)
- Plugin whitelist enforcement
- Prompt injection pattern detection
- HTML sanitization via bleach (when available)
- Link scheme validation (http/https/mailto/tel only)
- BiDi control character detection
- Confusable character detection (homograph attacks)

## Common Development Commands

### Setup
```bash
# Create virtual environment using uv (preferred) or standard venv
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or: .venv\Scripts\activate  # On Windows

# Install dependencies
pip install -e .
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_specific.py

# Run with verbose output
pytest -v

# Check test coverage (enforces 80% minimum per pyproject.toml)
pytest --cov=src/doxstrux --cov-report=term-missing

# Test coverage analysis tool
python scripts/test_coverage_tool.py
python scripts/test_coverage_tool.py --ci  # For CI/CD with exit codes
```

### Code Quality
```bash
# Type checking with mypy (strict mode enabled)
mypy src/doxstrux

# Linting with ruff
ruff check src/ tests/

# Auto-fix with ruff
ruff check --fix src/ tests/

# Format with black
black src/ tests/

# Security scan with bandit
bandit -r src/doxstrux

# Check for unused code
vulture src/doxstrux
```

### Running the Parser
```bash
# Basic usage
python main.py  # Parses README.md by default

# Use as a library
python -c "from src.doxstrux.markdown_parser_core import MarkdownParserCore; parser = MarkdownParserCore('# Hello\\nworld'); print(parser.parse())"
```

## Testing Standards

### Test File Organization
- Test files must be named `test_<module_name>.py`
- Test files mirror source directory structure
- Minimum 80% code coverage required (enforced by pytest config)
- Exclude `__init__.py` and `__version__.py` from coverage requirements

### Test Utilities
The `scripts/` directory contains several testing utilities:
- `test_coverage_tool.py`: Comprehensive coverage analysis (recommended)
- `run_tests.py`: Test runner
- `validate_all_test_files.py`: Validate test file structure

### Baseline Regression Testing

During refactoring (especially the zero-regex migration), parser output must remain **byte-for-byte identical** to frozen baselines to ensure no behavioral changes.

**Baseline Testing Procedure**:
1. **SSOT Test Pairs**: `tools/test_mds/` contains 542 markdown files with corresponding `.json` test specifications
2. **Frozen Baselines**: `tools/baseline_outputs/` contains verified parser outputs (read-only, 542 `.baseline.json` files)
3. **Verification**: Parser outputs are compared byte-by-byte against frozen baselines
4. **Requirement**: 100% pass rate (542/542 tests) with identical output

**Quick Commands**:
```bash
# Run parity tests (byte-by-byte comparison against baselines)
python tools/baseline_test_runner.py --test-dir tools/test_mds --baseline-dir tools/baseline_outputs

# Run feature count tests (validates parser extracts correct features)
python tools/test_feature_counts.py --test-dir tools/test_mds

# Quick subset test (fast iteration during development)
bash tools/run_tests_fast.sh 01_edge_cases
```

**Baseline Policy**:
- Baselines in `tools/baseline_outputs/` are **read-only** and **frozen**
- Any parser output change triggers parity test failure
- Baselines can only be regenerated when intentional parser improvements are verified
- See `tools/README.md` for complete baseline testing documentation

## Important Patterns and Conventions

### Extractor Pattern (Phase 7)

All extractors follow a consistent pattern for maintainability and testability:

**Function-Based Interface**:
```python
def extract_<element>(
    tree: SyntaxTreeNode,           # markdown-it AST
    process_tree_func: Callable,    # Universal recursion engine
    find_section_id_func: Callable, # Section lookup helper
    get_text_func: Callable,        # Text extraction helper
    # ... other parser methods as needed
) -> list[dict]:
    """Extract <element> with metadata.

    Returns:
        List of dicts with structure-specific fields
    """
    elements = []

    def processor(node, ctx, level):
        if node.type == "<element_type>":
            # Extract element data
            element_data = {
                "id": f"<element>_{len(ctx)}",
                "start_line": node.map[0] if node.map else None,
                # ... element-specific fields
            }
            ctx.append(element_data)
            return False  # Don't recurse into this element
        return True  # Continue recursion

    process_tree_func(tree, processor, elements)
    return elements
```

**Core Parser Delegation**:
```python
def _extract_<element>(self) -> list[dict]:
    """Extract <element> from document.

    Phase 7.X: Delegated to extractors/<element>.py
    """
    return <element>.extract_<element>(
        self.tree,
        self.process_tree,
        self._find_section_id,
        self._get_text
    )
```

**Key Characteristics**:
- **No classes**: Pure functions for simplicity
- **Dependency injection**: Receive parser methods as parameters
- **No state**: Extractors are stateless (state lives in parser)
- **Plain dicts**: Return simple dict structures, no Pydantic
- **Caching**: Handled at parser level via `self._cache`
- **Recursion safety**: Use depth limits to prevent stack overflow

**Example - Lists Extractor**:
```python
# src/doxstrux/markdown/extractors/lists.py
def extract_lists(
    tree: Any,
    process_tree_func: Any,
    extract_list_items_func: Any,
    find_section_id_func: Any
) -> list[dict]:
    """Extract regular lists (excludes task lists)."""
    lists = []

    def list_processor(node, ctx, level):
        if node.type in ["bullet_list", "ordered_list"]:
            items = extract_list_items_func(node)
            list_data = {
                "id": f"list_{len(ctx)}",
                "type": "bullet" if node.type == "bullet_list" else "ordered",
                "items": items,
                # ... more fields
            }
            ctx.append(list_data)
            return False
        return True

    process_tree_func(tree, list_processor, lists)
    return lists
```

### Parser Initialization
```python
from src.doxstrux.markdown_parser_core import MarkdownParserCore

# Basic usage
parser = MarkdownParserCore(content)

# With security profile
parser = MarkdownParserCore(content, security_profile="strict")

# With custom config
parser = MarkdownParserCore(
    content,
    config={
        "preset": "gfm",  # or "commonmark"
        "plugins": ["table", "strikethrough"],
        "allows_html": False
    },
    security_profile="moderate"
)
```

### Security Validation
```python
# Quick validation without full parsing
result = MarkdownParserCore.validate_content(content, security_profile="strict")
if not result["valid"]:
    print(f"Issues: {result['issues']}")
```

### Available Features Check
```python
features = MarkdownParserCore.get_available_features()
# Returns: {"bleach": bool, "yaml": bool, "footnotes": bool, "tasklists": bool}
```

**Note**: `ContentContext` was removed in Phase 6. Prose/code classification is now derived directly from AST code blocks in `mappings` dict returned by `parse()`.

## Dependencies

### Core Dependencies
- `markdown-it-py`: Markdown parsing engine
- `bleach`: HTML sanitization
- `pyyaml`: YAML frontmatter support
- `mdit-py-plugins`: Additional markdown features (footnotes, tasklists)

### Optional Dependencies
All optional dependencies gracefully degrade:
- If `bleach` unavailable, HTML sanitization is skipped
- If `yaml` unavailable, frontmatter extraction is disabled
- If plugins unavailable, they're tracked in `parser.unavailable_plugins`

### Development Dependencies
- `pytest`, `pytest-cov`, `pytest-asyncio`, `pytest-mock`: Testing
- `mypy`: Type checking (strict mode)
- `ruff`, `black`: Linting and formatting
- `bandit`, `safety`: Security scanning
- `vulture`: Dead code detection

## Configuration Files

### pyproject.toml
- **Package metadata**: Version 0.2.1, Python >=3.12
- **Test configuration**: 80% minimum coverage, strict markers
- **Type checking**: Strict mypy configuration
- **Linting**: Ruff with comprehensive rule selection
- **Entry point**: `doxstrux` CLI command (future)

### Security Configuration
- Bandit excludes test directories
- Vulture ignores test files and common patterns (model_config, metadata, field_validator)

## Known Constraints

1. **Python Version**: Requires Python 3.12+ (uses modern type hints)
2. **Recursion Depth**: Maximum 50-150 levels depending on security profile
3. **Content Size**: 100KB-10MB depending on security profile
4. **Test Coverage**: Minimum 80% coverage enforced
5. **Type Safety**: Strict mypy mode - all functions must have type annotations

## Working with Test Files

The repository includes extensive test markdown files in:
- `src/doxstrux/test_files/test_mds/`: Core test files
- `src/doxstrux/test_files/test_mds/md_stress_mega/`: Stress test files with pandoc features, overlapping structures, mixed encoding, and math-heavy content

When adding tests:
1. Mirror the source directory structure
2. Use `test_` prefix for test files
3. Ensure coverage meets 80% threshold
4. Run `python scripts/test_coverage_tool.py` to verify

## Special Notes

### Workspace Dependencies
This project has a workspace dependency on `ptool` located at `../PTOOL_SERENA`. This is configured in `pyproject.toml` under `[tool.uv.sources]`.

### Script Organization
- `scripts/`: Development and testing utilities (see `scripts/README.md`)
- `test_scripts/`: Ad-hoc testing scripts (not part of main test suite)
