# Fix Issues Plan

Issues identified from external code review, validated against codebase.

## Issue 1: Empty Root `__init__.py` [RESOLVED]

**File:** `src/doxstrux/__init__.py`

**Problem:** Users cannot do `from doxstrux import MarkdownParserCore`. They must know internal structure.

**Fix:**
```python
"""Doxstrux - Markdown parsing for RAG pipelines."""

from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.ir import DocumentIR, DocNode, ChunkPolicy, Chunk

__all__ = ["MarkdownParserCore", "DocumentIR", "DocNode", "ChunkPolicy", "Chunk"]
__version__ = "0.2.1"
```

**Effort:** 5 min

---

## Issue 2: Version Mismatch [RESOLVED]

**Files:**
- `pyproject.toml` → `0.2.1`
- `src/doxstrux/markdown/__init__.py` → `0.2.0`

**Problem:** Version drift between package metadata and module.

**Fix Options:**

A) Single-source from `__init__.py`:
- Set version in `src/doxstrux/__init__.py`
- Use `importlib.metadata` or dynamic versioning in pyproject.toml

B) Manual sync (simpler):
- Update `src/doxstrux/markdown/__init__.py` to `0.2.1`
- Remove redundant `__version__` from submodule, keep only in root

**Recommended:** Option B - update markdown/__init__.py to 0.2.1, consider removing submodule version entirely.

**Effort:** 5 min

---

## Issue 3: Missing `py.typed` Marker [RESOLVED]

**Problem:** `pyproject.toml` declares `py.typed` in package-data but file doesn't exist. Users can't get type checking benefits.

**Fix:**
```bash
touch src/doxstrux/py.typed
```

Empty file is sufficient as a PEP 561 marker.

**Effort:** 1 min

---

## Issue 4: Path Traversal False Positive on URLs [RESOLVED]

**File:** `src/doxstrux/markdown_parser_core.py` lines 1645-1662

**Problem:** Pattern `"//"` matches every `https://` URL, causing false positives.

**Current code:**
```python
patterns = [
    "../", "..\\",
    ...
    "//",        # <-- BUG: matches https://
    "\\\\",
    ...
]
```

**Fix:** Check `//` only at path start or after decode, not in scheme:

```python
def _check_path_traversal(self, url: str) -> bool:
    # ... existing decode logic ...

    # Extract path component for traversal checks
    try:
        parsed = urllib.parse.urlparse(decoded)
        path_to_check = parsed.path
    except:
        path_to_check = decoded

    # Only check path component, not full URL with scheme
    traversal_patterns = [
        "../", "..\\",
        "..%2f", "..%5c",
        "%2e%2e/", "%2e%2e\\",
        "%2e%2e%2f", "%2e%2e%5c",
        "%252e%252e",
        "..;", "..//",
    ]

    # UNC/protocol patterns - check on original decoded URL
    protocol_patterns = [
        "file://", "file:\\",
    ]

    # Double-slash only suspicious at path start (not in scheme)
    if path_to_check.startswith("//") or path_to_check.startswith("\\\\"):
        return True

    for pattern in traversal_patterns:
        if pattern in path_to_check.lower():
            return True

    for pattern in protocol_patterns:
        if decoded.lower().startswith(pattern):
            return True

    return False
```

**Effort:** 15 min (includes testing)

---

## Issue 5: md_parser_testing Distribution [RESOLVED]

**Files:** `src/doxstrux/md_parser_testing/`

**Problem:** Test utilities included in distribution with hardcoded paths that won't exist for users.

**Fix Options:**

A) Exclude from wheel:
```toml
# pyproject.toml
[tool.setuptools.packages.find]
where = ["src"]
include = ["doxstrux*"]
exclude = ["doxstrux.md_parser_testing*"]
```

B) Move to `tests/` directory (outside src)

**Recommended:** Option A - exclude from distribution.

**Effort:** 5 min

---

## Verification Checklist

After fixes, verify:

- [x] `from doxstrux import MarkdownParserCore` works ✅
- [x] `python -c "import doxstrux; print(doxstrux.__version__)"` shows 0.2.1 ✅
- [x] `py.typed` exists and is included in wheel ✅
- [x] `https://example.com` does not trigger path traversal warning ✅ (Phase 1.1)
- [x] `../etc/passwd` still triggers path traversal warning ✅ (Phase 1.1)
- [x] 542 baseline tests still pass ✅
- [ ] mypy recognizes package as typed (not verified)

---

## Priority Order

1. **Issue 4** (path traversal bug) - Security false positive, high impact
2. **Issue 1** (empty __init__) - UX, high visibility
3. **Issue 2** (version mismatch) - Correctness
4. **Issue 3** (py.typed) - Type checking support
5. **Issue 5** (test module) - Clean distribution

---

## Total Effort

~30 minutes for all fixes + verification.
