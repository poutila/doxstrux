# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Docpipe** is a comprehensive markdown enrichment and parsing library designed for both human users and AI systems. It provides robust markdown parsing with security-first design, extracting structured data from markdown documents while maintaining content integrity.

## Core Architecture

### Single-File Parser Design
The heart of this project is `src/docpipe/markdown_parser_core.py` (3660 lines), which implements a self-contained markdown parser with:
- **MarkdownParserCore**: Main parser class using markdown-it-py as the parsing engine
- **Security-first design**: Three security profiles (strict, moderate, permissive) with content size limits, plugin validation, and prompt injection detection
- **Universal recursion engine**: Single-pass document parsing with configurable recursion depth limits
- **Content context awareness**: Via `ContentContext` class for distinguishing prose from code blocks

### Key Design Principles
1. **Extract everything, analyze nothing**: Parser focuses on structural extraction, not semantic analysis
2. **No file I/O in core**: Parser accepts content strings, not file paths
3. **Plain dict outputs**: No Pydantic models in the core parser (keeps it lightweight)
4. **Security layered throughout**: Size limits, plugin validation, HTML sanitization, link scheme validation

### Module Structure
```
src/docpipe/
├── markdown_parser_core.py    # Core parser (3660 lines)
├── content_context.py          # Context mapping (prose vs code blocks)
├── json_utils.py              # JSON serialization helpers
├── sluggify_util.py           # Slug generation utilities
├── help.py                    # Interactive help system for users and AI
└── __init__.py                # Package exports
```

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
pytest --cov=src/docpipe --cov-report=term-missing

# Test coverage analysis tool
python scripts/test_coverage_tool.py
python scripts/test_coverage_tool.py --ci  # For CI/CD with exit codes
```

### Code Quality
```bash
# Type checking with mypy (strict mode enabled)
mypy src/docpipe

# Linting with ruff
ruff check src/ tests/

# Auto-fix with ruff
ruff check --fix src/ tests/

# Format with black
black src/ tests/

# Security scan with bandit
bandit -r src/docpipe

# Check for unused code
vulture src/docpipe
```

### Running the Parser
```bash
# Basic usage
python main.py  # Parses README.md by default

# Use as a library
python -c "from src.docpipe.markdown_parser_core import MarkdownParserCore; parser = MarkdownParserCore('# Hello\\nworld'); print(parser.parse())"
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

## Important Patterns and Conventions

### Parser Initialization
```python
from src.docpipe.markdown_parser_core import MarkdownParserCore

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

### Content Context
```python
from src.docpipe.content_context import ContentContext

# Distinguish prose from code blocks
context = ContentContext(content)
for i, line in enumerate(context.lines):
    if context.is_prose_line(i):
        # Process as markdown
        pass
    elif context.is_code_line(i):
        # Skip or handle as code
        pass
```

### Available Features Check
```python
features = MarkdownParserCore.get_available_features()
# Returns: {"bleach": bool, "yaml": bool, "footnotes": bool, "tasklists": bool, "content_context": bool}
```

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
- **Package metadata**: Version 0.2.0, Python >=3.12
- **Test configuration**: 80% minimum coverage, strict markers
- **Type checking**: Strict mypy configuration
- **Linting**: Ruff with comprehensive rule selection
- **Entry point**: `docpipe` CLI command (future)

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
- `src/docpipe/test_files/test_mds/`: Core test files
- `src/docpipe/test_files/test_mds/md_stress_mega/`: Stress test files with pandoc features, overlapping structures, mixed encoding, and math-heavy content

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

### Content Context Implementation
The `ContentContext` class implements sophisticated code block detection:
- Fenced code blocks (``` or ~~~)
- Indented code blocks (4 spaces or tab)
- Handles blank lines within code blocks
- Conservative detection to avoid false positives from list continuations
