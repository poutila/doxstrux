# Bugs and Drifts Analysis

Deep analysis of doxstrux package. Issues categorized by severity.

**Analysis Date:** 2025-12-10
**Package Version:** 0.2.1
**Sources:** Internal analysis + External code review validation
**Note:** Commit SHA should be recorded when fixes begin to track drift

---

## CRITICAL BUGS

### 1. Path Traversal False Positive on All HTTPS URLs [RESOLVED]

**Status:** ✅ Fixed in NO_SILENTS Phase 1.1
**Fix:** Replaced pattern-based check with `urlparse()` approach per SECURITY_KERNEL_SPEC.md §6.2

**File:** `markdown_parser_core.py:1645-1662`

**Problem:** The `//` pattern matches every `https://` URL, flagging legitimate links as path traversal attacks.

```python
patterns = [
    ...
    "//",        # BUG: matches https://example.com
    "\\\\",
    ...
]
```

**Impact:** Every HTTPS link triggers:
- `warnings: [{type: "path_traversal", ...}]`
- `has_dangerous_content: True`
- Potential embedding rejection

**Verified:**
```python
>>> p._check_path_traversal("https://example.com")
True  # FALSE POSITIVE
```

---

### 2. Silent Exception Swallowing (Rule Violation) [RESOLVED]

**Status:** ✅ Fixed in NO_SILENTS Phase 1.2
**Fix:** Removed bare `except Exception: pass` from `_build_mappings()`

**File:** `markdown_parser_core.py:1535`

```python
except Exception:
    pass
```

**Problem:** Bare `except Exception: pass` in `_build_mappings()` silently swallows all errors.

**Violates:** `.claude/rules/CLEAN_TABLE_PRINCIPLE.md` - "No silent exceptions"

---

### 3. Documented Fail-Open in Security Code [RESOLVED]

**Status:** ✅ Fixed in NO_SILENTS Phase 1.3
**Fix:** `check_prompt_injection()` now returns `PromptInjectionCheck(suspected=True, reason="validator_error")` on errors (fail-closed)

**File:** `markdown/security/validators.py:301-303`

```python
except Exception:
    # On regex timeout or error, return False (fail-open for this check)
    pass
```

**Problem:** Prompt injection check explicitly fails open on error. An attacker could trigger an exception to bypass detection.

**Violates:** CLEAN_TABLE_PRINCIPLE - "All exceptions must raise unconditionally"

---

## HIGH SEVERITY DRIFTS

### 4. README Documents Non-Existent API

**File:** `README.md:82-97`

**Documented:**
```python
doc_ir = DocumentIR.from_parse_result(result)
chunks = doc_ir.chunk(policy)
```

**Reality:**
- `DocumentIR.from_parse_result()` does NOT exist
- `DocumentIR.chunk()` does NOT exist
- Actual API: `parser.to_ir(source_id="test.md")`

**Fix Options:**
1. Implement `@classmethod from_parse_result()` and `def chunk()` with tests
2. Rewrite README to show actual API and mark IR chunking as "planned"

---

### 5. README Claims "Zero Regex" - Actually 19 Patterns (Reducible to 14)

**File:** `README.md:121`

**Claim:** "Regex Count: 0 (zero-regex architecture)"

**Reality:** 19 `re.compile()` or `re.sub()` calls:
- 13 in `validators.py` (security patterns)
- 3 in `config.py` (HTML detection)
- 3 in `sections.py` (`slugify_base()` function)

These are intentionally retained (`# REGEX RETAINED (§6 Security)`), but claim is misleading.

#### Regex Reduction Analysis

**Can remove 5 patterns (-26%):**

| Location | Pattern | Replacement |
|----------|---------|-------------|
| `sections.py` | `r"[\s/]+"` | `c.isspace() or c == '/'` loop |
| `sections.py` | `r"[^\w-]"` | `c.isalnum() or c in '-_'` loop |
| `sections.py` | `r"-+"` | `while '--' in s: s.replace()` |
| `validators.py` | `_URL_SCHEME_RE` | `str.find(':')` + char validation |
| `validators.py` | `_DATA_URI_RE` | `str.find(',')` + split |

**Must keep 14 patterns** (security-critical):
- 10 prompt injection patterns (need `\s+` whitespace matching)
- 3 HTML detection (`_STYLE_JS_PAT`, `_META_REFRESH_PAT`, `_FRAMELIKE_PAT`)
- 1 raw content scan (`_DISALLOWED_SCHEMES_RAW_RE`)

**Regex-free `slugify_base()` implementation (verified):**
```python
def slugify_base(text: str) -> str:
    s = unicodedata.normalize("NFKD", text).lower()
    result = []
    for c in s:
        if c.isspace() or c == '/':
            result.append('-')
        elif c.isalnum() or c == '-' or c == '_':
            result.append(c)
    s = ''.join(result)
    while '--' in s:
        s = s.replace('--', '-')
    return s.strip('-') or 'untitled'
```

**Suggested Fix:**
1. Implement regex-free versions for the 5 removable patterns
2. Change README wording to:
> "Zero-regex markdown parsing. Security validation retains 14 regex patterns for threat detection."

---

### 6. ChunkPolicy API Drift

**README shows:**
```python
respect_boundaries=['heading', 'section']  # List
```

**Actual:**
```python
respect_boundaries=True  # Bool
```

---

### 7. Project URLs Point to Wrong Repository

**File:** `pyproject.toml:49-54`

```toml
Homepage = "https://github.com/doxstrux/doxstrux"
Repository = "https://github.com/doxstrux/doxstrux.git"
Issues = "https://github.com/doxstrux/doxstrux/issues"
Changelog = "https://github.com/doxstrux/doxstrux/blob/main/CHANGELOG.md"
```

**Actual repo:** `github.com/poutila/doxstrux`

All PyPI links are 404.

---

### 8. SECURITY.md Advisory URL Broken

**File:** `SECURITY.md:166`

```markdown
GitHub Security Advisories: https://github.com/doxstrux/doxstrux/security/advisories
```

Points to non-existent repository. Users following security guidance get 404.

---

### 9. Test Count Contradiction in Same File

**File:** `README.md`

- Line 120: `"Tests: 95/95 pytest passing + 542/542 baseline tests passing"`
- Line 163: `"All changes must pass 63 pytest tests"`

Cannot both be true. Self-contradicting documentation.

---

## MEDIUM SEVERITY

### 10. Version Mismatch (Multiple Files)

| File | Version |
|------|---------|
| `pyproject.toml` | `0.2.1` |
| `markdown/__init__.py` | `0.2.0` |
| `SECURITY.md` (line 188) | `0.2.0` |
| `SECURITY.md` (line 171) | `"v0.2.0"` |

---

### 11. Empty Root `__init__.py`

**File:** `src/doxstrux/__init__.py`

Users cannot do:
```python
from doxstrux import MarkdownParserCore  # Fails
```

Must know internals:
```python
from doxstrux.markdown_parser_core import MarkdownParserCore
```

---

### 12. Missing `py.typed` Marker

`pyproject.toml` declares it in package-data but file doesn't exist. Type checkers won't recognize package as typed.

---

### 13. Subpackage `__init__.py` Files Have No Exports

**Files:**
- `markdown/extractors/__init__.py`
- `markdown/utils/__init__.py`
- `markdown/security/__init__.py`

All have docstrings but no re-exports. Users must import from individual modules.

---

### 14. Duplicate Constants (Drift Risk) [RESOLVED]

**Status:** ✅ Fixed in NO_SILENTS Phase 1.4
**Fix:** Removed `MAX_DATA_URI_SIZE` dict from `budgets.py`. Added `get_max_data_uri_size()` and `get_max_injection_scan_chars()` helpers that read from SSOT (`SECURITY_PROFILES` in config.py)

**Files:** `budgets.py` vs `config.py`

`MAX_DATA_URI_SIZE` duplicated in both files. Currently identical but could drift:

```python
# budgets.py
MAX_DATA_URI_SIZE = {"strict": 0, "moderate": 10240, "permissive": 102400}

# config.py SECURITY_PROFILES
"max_data_uri_size": 10240  # Same values, different structure
```

---

### 15. Unused Imports

**File:** `markdown_parser_core.py`

```python
import posixpath  # Never used
import warnings   # Never used
```

---

### 16. Security Contact is Placeholder

**File:** `SECURITY.md:50`

```markdown
**Email**: security@doxstrux.example.com (replace with actual email)
```

For a "security-first" package, this undermines credibility.

---

### 17. Stale pyproject.toml Sections

**File:** `pyproject.toml:196-204`

```toml
[tool.project_paths.paths]
batchs = "src/ptool_test/batchs"

[tool.project_paths.files]
existing_file_1 = "src/ptool_test/important_file.some"
```

`src/ptool_test/` does not exist. Leftovers from another project.

---

### 18. Docpipe Naming in Tools

**File:** `tools/generate_baseline_outputs.py:3`

```python
"""
Generate Baseline Outputs for Docpipe Markdown Parser
```

Package renamed to `doxstrux` but tools still reference `Docpipe`.

---

### 19. Process Isolation Not Implemented

**Documented in:** `regex_refactor_docs/REGEX_REFACTOR_POLICY_GATES.md`

Claims strict profile runs parse in separate process via `ProcessPoolExecutor`.

**Reality:** No `ProcessPoolExecutor` in `src/`. Parser runs in-process for all profiles.

Policy docs describe aspirational architecture, not current implementation.

---

## LOW SEVERITY

### 20. Prompt Injection Only Checks First 1024 Chars

**File:** `validators.py:295`

```python
check_text = text[:1024]
```

Attacker can place injection payload after 1024 characters to bypass detection. Design decision but undocumented.

---

### 21. Major Test Gap

**Source modules:** 28 Python files
**Test files:** 6 unit test files

No unit tests for:
- `markdown_parser_core.py` (main parser)
- All 11 extractors
- `budgets.py`, `config.py`, `validators.py`

The 542 baseline tests are integration tests only.

---

### 22. md_parser_testing in Distribution

Test utilities with hardcoded paths included in wheel. Should be excluded:

```toml
# pyproject.toml
[tool.setuptools.packages.find]
exclude = ["doxstrux.md_parser_testing*"]
```

---

### 23. Generic Authors Metadata

**File:** `pyproject.toml:12-17`

```toml
authors = [
    { name = "Doxstrux Contributors", email = "doxstrux@example.com" }
]
```

Generic placeholder undermines package credibility.

---

## External Review Validation

An external code review was performed. Here's the validation:

| Claim | Status | Notes |
|-------|--------|-------|
| README API mismatch (from_parse_result, chunk) | ✅ CONFIRMED | Methods don't exist |
| URLs point to wrong repo | ✅ CONFIRMED | `doxstrux/doxstrux` is 404 |
| Version 0.2.0 vs 0.2.1 | ✅ CONFIRMED | SECURITY.md has 0.2.0 |
| requirements.txt issues | ✅ RESOLVED | Deleted by maintainer |
| Test counts 95 vs 63 | ✅ CONFIRMED | Same file, contradicting |
| Security advisory URL broken | ✅ CONFIRMED | Points to non-existent repo |
| Zero-regex imprecise | ✅ CONFIRMED | slugify_base() uses regex |
| Suspicious regex `r"]*>"` | ❌ INCORRECT | Actual: `r"<script[^>]*>"` (valid) |
| Process isolation not implemented | ✅ CONFIRMED | No ProcessPoolExecutor in src/ |
| Docpipe naming in docs | ✅ CONFIRMED | tools/ still says "Docpipe" |
| Security email placeholder | ✅ CONFIRMED | `@doxstrux.example.com` |
| project_paths non-existent | ✅ CONFIRMED | Points to `src/ptool_test/` |
| Authors metadata generic | ✅ CONFIRMED | `doxstrux@example.com` |

**External Review Accuracy:** ~92% (12/13 claims validated)

---

## Summary

| Severity | Count | Key Examples |
|----------|-------|--------------|
| Critical | 3 | Path traversal FP, silent exceptions, fail-open security |
| High | 6 | Non-existent API, regex claim, wrong URLs, broken advisory |
| Medium | 10 | Version mismatches, empty __init__, placeholder contacts |
| Low | 4 | Truncated checks, test gaps, unused imports |

**Total Issues: 23**

---

## Priority Fix Order

### Immediate (User-Visible Breakages)
1. **Path traversal false positive** - Security bug affecting all users
2. **Project URLs** - All PyPI links are 404
3. **README API documentation** - Code examples throw AttributeError
4. **Security advisory URL** - Security guidance leads to 404

### Clean Table Violations
5. **Silent exceptions** - Rule violation, hides bugs
6. **Fail-open security** - Contradicts fail-closed principle
7. **Test count contradiction** - Self-inconsistent docs

### Package Polish
8. **Version sync** - Align all version strings to 0.2.1
9. **Root __init__.py** - Enable clean imports
10. **py.typed marker** - Enable type checking
11. **Remove stale configs** - project_paths, docpipe refs

### Documentation Accuracy
12. **Zero-regex claim** - Reduce to 14 patterns, update wording
13. **ChunkPolicy API** - Fix parameter types in docs
14. **Process isolation** - Mark as "planned" not "implemented"

---

## Improvement Opportunities

### Regex Reduction (19 → 14)

Remove 5 non-security regex patterns:
- 3 in `slugify_base()` → string operations
- 2 in `validators.py` → string parsing

This would make "zero-regex parsing" claim more defensible, with only security patterns remaining.

---

## Runtime-Only Priority (External Review 2025-12-10)

An additional external review focused specifically on **runtime issues** (not documentation/packaging) validated this document and provided a priority list:

### Runtime Bugs (Must Fix First)

| Priority | Issue | Impact |
|----------|-------|--------|
| 1 | Path traversal `//` bug (#1) | Every HTTPS URL flagged as dangerous |
| 2 | Silent exceptions in `_build_mappings` (#2) | Real errors hidden, debugging impossible |
| 3 | Prompt injection fail-open (#3) | Attacker can bypass by triggering exception |
| 4 | README API examples (#4, #6) | `AttributeError`/`TypeError` for users |
| 5 | 1024-char injection limit (#20) | Magic number, not profile-driven |

### Runtime Verdict

> "The major runtime/security bugs that affect normal use of 0.2.1 are **already catalogued** in this document. I do not see evidence of additional, specific runtime failures beyond that."

### Where Hidden Runtime Bugs Are Most Likely

1. **Parser core** - `markdown_parser_core.py` is large and unit-untested
2. **Extractors** - 11 modules with no direct tests; subtle bugs surface only in certain document patterns
3. **Tooling scripts** - `tools/`, baseline generation affect maintainers more than users

### External Review Confidence

- All 5 critical/high runtime issues confirmed as real
- No new runtime issues identified beyond this document
- Main remaining risk: untested edge cases in parser/extractors

---

## Known Limitations of This Analysis

This document is a high-coverage catalogue of observable, high-impact drift/bugs. It is **not** a formal proof of "no more bugs."

### Hidden Risk Areas

1. **Parser Semantics**
   - 28 source modules vs 6 unit test files
   - Behavioural bugs in edge-case markdown may exist
   - 542 baseline tests are integration-only, not unit coverage

2. **CI / Tooling Wiring**
   - `.github/workflows/` not fully audited
   - `imports_preflight.py`, `scripts/*` may have wiring bugs
   - Policy docs promise features (process isolation, evidence artefacts) not yet implemented

3. **Analysis Staleness**
   - Any commits after this analysis can introduce fresh issues
   - Document should be re-validated before major releases
