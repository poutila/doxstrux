# Libraries Needed for Phase 8 Token Warehouse

**Version**: 1.0
**Date**: 2025-10-15
**Purpose**: Required dependencies for Phase 8.0 integration

---

## Core Runtime Dependencies

### 1. **markdown-it-py** (REQUIRED)
**Purpose**: Core markdown parsing engine
**Used by**:
- `doxstrux/markdown/cli/dump_sections.py` - CLI tool for section inspection
- Core parser integration (when integrated into main codebase)

**Install**:
```bash
pip install markdown-it-py
```

**Version**: Already in project requirements (pyproject.toml)

**Import pattern**:
```python
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
```

---

## Testing Dependencies

### 2. **pytest** (REQUIRED for testing)
**Purpose**: Test framework
**Used by**:
- `tests/test_token_warehouse.py` (6 core tests)
- `tests/test_token_warehouse_adversarial.py` (2 adversarial tests)
- `tests/test_vulnerabilities_extended.py` (10+ vulnerability tests)
- `tests/test_fuzz_collectors.py` (randomized fuzz tests)

**Install**:
```bash
pip install pytest pytest-cov
```

**Version**: Already in project dev requirements

**Import pattern**:
```python
import pytest
```

---

## Security Testing Dependencies

### 3. **tracemalloc** (Built-in, Python 3.4+)
**Purpose**: Memory profiling for security validation
**Used by**:
- `tools/run_adversarial.py` - Adversarial corpus runner (peak memory tracking)

**No install needed** - part of Python standard library

**Import pattern**:
```python
import tracemalloc
```

### 4. **weakref** (Built-in)
**Purpose**: Circular reference detection in tests
**Used by**:
- `tests/test_vulnerabilities_extended.py` - Memory leak detection tests

**No install needed** - part of Python standard library

**Import pattern**:
```python
import weakref
```

### 5. **gc** (Built-in)
**Purpose**: Garbage collector control for reference counting tests
**Used by**:
- `tests/test_vulnerabilities_extended.py` - Circular reference tests

**No install needed** - part of Python standard library

**Import pattern**:
```python
import gc
```

---

## Standard Library Dependencies (Built-in)

All of these are **included in Python 3.12+**, no installation needed:

### Core Utilities
- **`typing`** - Type hints (`Any`, `Dict`, `List`, `Tuple`, `Optional`, `Set`, `Callable`, `Protocol`)
- **`collections`** - `defaultdict` for routing tables
- **`pathlib`** - `Path` for file operations
- **`json`** - JSON serialization for adversarial corpus
- **`time`** - Performance benchmarking (`time.perf_counter()`)
- **`random`** - Fuzz testing and adversarial corpus generation
- **`argparse`** - CLI argument parsing
- **`sys`** - System operations

### Python 3.12+ Features
- **`from __future__ import annotations`** - PEP 563 postponed evaluation
- Modern type hints (used throughout)

---

## Optional Dependencies (Recommended)

### 6. **urllib.parse** (Built-in, but security-critical)
**Purpose**: URL parsing for security validation
**Used by**: Security patches in `COMPREHENSIVE_SECURITY_PATCH.md`

**CRITICAL**: When applying security patches, the `links.py` collector needs:
```python
from urllib.parse import urlparse
```

This is built-in but becomes **required** when applying Patch #1 (URL Scheme Validation).

---

## Summary: What You Need to Install

### For Development (skeleton testing):
```bash
pip install markdown-it-py pytest pytest-cov
```

### For Production (Phase 8.0 integration):
```bash
# Already in pyproject.toml:
pip install markdown-it-py
pip install mdit-py-plugins  # For footnotes, tasklists, tables

# Dev dependencies:
pip install pytest pytest-cov pytest-mock
pip install mypy ruff black bandit
```

---

## Dependency Status

| Library | Type | Status | Required For |
|---------|------|--------|--------------|
| `markdown-it-py` | Runtime | ✅ In pyproject.toml | Core parsing |
| `mdit-py-plugins` | Runtime | ✅ In pyproject.toml | Footnotes, tasklists, tables |
| `pytest` | Dev | ✅ In pyproject.toml | All tests |
| `pytest-cov` | Dev | ✅ In pyproject.toml | Coverage reports |
| `tracemalloc` | Built-in | ✅ Python 3.4+ | Memory profiling |
| `weakref` | Built-in | ✅ Python stdlib | Leak detection |
| `gc` | Built-in | ✅ Python stdlib | Reference counting tests |
| `urllib.parse` | Built-in | ✅ Python stdlib | URL validation (security patches) |
| `typing` | Built-in | ✅ Python 3.12+ | Type hints |
| `collections` | Built-in | ✅ Python stdlib | Routing tables |
| `pathlib` | Built-in | ✅ Python 3.4+ | File operations |
| `json` | Built-in | ✅ Python stdlib | Adversarial corpus |
| `time` | Built-in | ✅ Python stdlib | Benchmarking |
| `random` | Built-in | ✅ Python stdlib | Fuzz testing |

---

## No Additional Dependencies Required

**Good news**: The Phase 8 Token Warehouse has **zero new dependencies** beyond what's already in `pyproject.toml`.

All security hardening, adversarial testing, and performance profiling uses:
1. **Existing project dependencies** (`markdown-it-py`, `pytest`)
2. **Python standard library** (all built-in modules)

This keeps the security surface minimal and deployment simple.

---

## Virtual Environment Usage

**CRITICAL** (per CLAUDE.md): Always use the virtual environment:

```bash
# Correct (ALWAYS):
/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/.venv/bin/python

# Wrong (NEVER):
python3  # Missing mdit-py-plugins, produces silent failures
```

---

## Testing the Dependencies

### Quick Check:
```bash
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned

# Check runtime dependencies
.venv/bin/python -c "import markdown_it; print('✅ markdown-it-py')"
.venv/bin/python -c "import mdit_py_plugins; print('✅ mdit-py-plugins')"

# Check testing dependencies
.venv/bin/python -c "import pytest; print('✅ pytest')"

# Check standard library (should always work)
.venv/bin/python -c "import tracemalloc, weakref, gc, json, time, random; print('✅ stdlib')"
```

### Expected Output:
```
✅ markdown-it-py
✅ mdit-py-plugins
✅ pytest
✅ stdlib
```

---

## Future Considerations

### If Adding Security Enhancements:
- **bleach** (HTML sanitization) - Already in pyproject.toml, optional
- **pyyaml** (Frontmatter parsing) - Already in pyproject.toml, optional

### If Adding Performance Monitoring:
- **py-spy** (Profiler) - Not required, but useful for production profiling
- **scalene** (Memory profiler) - Not required, but useful for hotspot analysis

These are **not required** for Phase 8.0 deployment.

---

**Last Updated**: 2025-10-15
**Status**: Complete - No new dependencies needed
**Next Step**: Apply security patches from `COMPREHENSIVE_SECURITY_PATCH.md` during Phase 8.0 integration
