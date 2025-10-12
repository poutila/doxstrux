# 🏗️ Doxstrux

[![PyPI version](https://badge.fury.io/py/doxstrux.svg)](https://badge.fury.io/py/doxstrux)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Downloads](https://pepy.tech/badge/doxstrux)](https://pepy.tech/project/doxstrux)

**Document structure extraction tool** for markdown, with extensibility to PDF and HTML.

Extract hierarchical structure, metadata, and content from documents without semantic analysis. Built for RAG pipelines, documentation analysis, and AI preprocessing.

## ✨ Features

- **Zero-regex parsing**: Token-based extraction using markdown-it-py
- **Security-first design**: Three security profiles (strict/moderate/permissive)
- **Document IR**: Clean intermediate representation for RAG chunking
- **Structure extraction**: Headings, lists, tables, code blocks, links, images
- **Content integrity**: Parse without mutation, fail-closed security
- **Extensible architecture**: Ready for PDF and HTML support

## 📦 Installation

```bash
pip install doxstrux
```

## 🚀 Quick Start

```python
from doxstrux.markdown_parser_core import MarkdownParserCore

# Basic usage
content = "# Hello\n\nThis is **markdown**."
parser = MarkdownParserCore(content)
result = parser.parse()

# Access structure
print(result['structure']['headings'])
print(result['metadata']['security']['statistics'])

# With security profile
parser = MarkdownParserCore(content, security_profile='strict')
result = parser.parse()

# With custom config
parser = MarkdownParserCore(
    content,
    config={
        'preset': 'gfm',
        'plugins': ['table', 'strikethrough'],
        'allows_html': False
    },
    security_profile='moderate'
)
result = parser.parse()
```

## 🏗️ Architecture

### Core Principles

- **Extract everything, analyze nothing**: Focus on structural extraction, not semantics
- **No file I/O in core**: Parser accepts content strings, not paths
- **Plain dict outputs**: Lightweight, no heavy dependencies
- **Security layered throughout**: Size limits, plugin validation, content sanitization

### Security Profiles

| Profile | Max Size | Max Lines | Recursion Depth | Use Case |
|---------|----------|-----------|-----------------|----------|
| **strict** | 100KB | 2K | 50 | Untrusted input |
| **moderate** | 1MB | 10K | 100 | Standard use (default) |
| **permissive** | 10MB | 50K | 150 | Trusted documents |

### Document IR

Clean intermediate representation for RAG pipelines and chunking:

```python
from doxstrux.markdown.ir import DocumentIR, ChunkPolicy

# Parse to IR
parser = MarkdownParserCore(content)
result = parser.parse()
doc_ir = DocumentIR.from_parse_result(result)

# Apply chunking policy
policy = ChunkPolicy(
    max_chunk_tokens=512,
    overlap_tokens=50,
    respect_boundaries=['heading', 'section']
)
chunks = doc_ir.chunk(policy)
```

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/doxstrux

# Type checking
mypy src/doxstrux

# Linting
ruff check src/ tests/
```

## 📊 Project Status

- **Version**: 0.2.0 ✅ **Published on PyPI**
- **Python**: 3.12+
- **Test Coverage**: 70%
- **Tests**: 63/63 passing
- **Regex Count**: 0 (zero-regex architecture)
- **PyPI**: https://pypi.org/project/doxstrux/

## 🗺️ Roadmap

- [ ] **Phase 7**: Modular architecture (in progress)
- [ ] **PDF support**: Extract structure from PDF documents
- [ ] **HTML support**: Parse HTML with same IR
- [ ] **Enhanced chunking**: Semantic-aware chunking strategies
- [ ] **Performance**: Cython optimization for hot paths

## 📚 Documentation

- **Architecture**: See `CLAUDE.md` for detailed architecture notes
- **Phase 7 Plan**: See `regex_refactor_docs/DETAILED_TASK_LIST.md`
- **Testing**: See `regex_refactor_docs/REGEX_REFACTOR_POLICY_GATES.md`

## 🤝 Contributing

This project follows a phased refactoring methodology with comprehensive test gates.

1. All changes must pass 63 pytest tests
2. All changes must maintain byte-for-byte output parity (542 baseline tests)
3. Security-first: No untrusted regex, validated links, sanitized HTML
4. Type-safe: Full mypy strict mode compliance

## 📜 License

MIT License - see `LICENSE` file for details.

## 🙏 Acknowledgments

Built on:
- [markdown-it-py](https://github.com/executablebooks/markdown-it-py) - CommonMark compliant parser
- [mdit-py-plugins](https://github.com/executablebooks/mdit-py-plugins) - Extended markdown features

---

**Previous name**: docpipe (renamed to doxstrux in v0.2.0 for extensibility to PDF/HTML)
