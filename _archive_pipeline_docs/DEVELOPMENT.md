# Development Guide

This guide is for AI assistants and developers working with the doxstrux codebase. Every rule exists because violating it caused real problems.

---

## 1. Critical Rules

### 1.1 Python Environment (MANDATORY)

**NEVER use system python. ALWAYS use `.venv/bin/python`.**

```bash
# CORRECT
.venv/bin/python tools/generate_baseline_outputs.py
.venv/bin/python -m pytest

# WRONG — produces silently corrupted output
python3 tools/generate_baseline_outputs.py
python tools/baseline_test_runner.py
```

**Why:** System python lacks `mdit-py-plugins`. The code runs without errors but produces **wrong output** because optional dependencies fail silently. Tables, footnotes, and tasklists will be parsed incorrectly. Baselines generated with system python are corrupted — undetectable until parity tests fail.

### 1.2 Immutable Directories (READ-ONLY)

These directories must NEVER be edited without explicit human approval:

| Directory | Contents | Why Protected |
|-----------|----------|---------------|
| `tools/baseline_outputs/` | 542 frozen baseline JSON files | Ground truth for regression testing |
| `tools/test_mds/` | 542 test markdown files | Test corpus — changes invalidate all baselines |
| `tools/mds.zip` | Compressed backup | Archive integrity |

**To modify:** Stop. Ask for human approval. Explain the change and its impact on all 542 baseline tests.

### 1.3 Clean Table Principle

No work ships until fully correct:

- No unresolved TODOs, placeholders, or speculative comments
- No silent exceptions — all errors raise unconditionally
- No temporary band-aids masking root causes
- No "needs to be checked later" deferrals

**Silent Exception Ban:**

```python
# FORBIDDEN — conditional raise
except Exception as e:
    if strict:
        raise SpecLoadError(spec_path, e) from e
    errors.append((spec_path, e))  # Swallowed!

# REQUIRED — unconditional raise
except Exception as e:
    raise SpecLoadError(spec_path, e) from e
```

### 1.4 No Weak Tests

Tests must assert meaningful behavior, not just existence:

```python
# WEAK — Avoid
def test_parser_exists():
    assert hasattr(module, 'MarkdownParserCore')

# STRONG — Required
def test_parser_extracts_headings():
    parser = MarkdownParserCore("# Hello\n## World")
    result = parser.parse()
    assert len(result["structure"]["headings"]) == 2
    assert result["structure"]["headings"][0]["level"] == 1
    assert result["structure"]["headings"][0]["text"] == "Hello"
```

---

## 2. Testing Infrastructure

### 2.1 Test Types

| Type | Command | Purpose | Pass Criteria |
|------|---------|---------|---------------|
| Unit Tests | `.venv/bin/python -m pytest` | Coverage | 80% minimum |
| Parity Tests | `.venv/bin/python tools/baseline_test_runner.py` | Regression | 542/542 (100%) |
| Feature Tests | `.venv/bin/python tools/test_feature_counts.py` | Validation | ~512/542 (94.5%) |

### 2.2 Baseline Testing System

**Purpose:** Ensure parser output is byte-for-byte identical across refactoring.

**Components:**

1. **SSOT Test Pairs** (`tools/test_mds/`): 542 markdown files with specifications, organized in 32 categories

2. **Frozen Baselines** (`tools/baseline_outputs/`): 542 verified parser outputs, read-only, ground truth

3. **Parity Test**: Compares current output to frozen baselines, byte-by-byte JSON comparison, 100% pass rate required

### 2.3 Running Tests

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

### 2.4 Expected Results

| Test | Expected | Notes |
|------|----------|-------|
| pytest | All pass | 80% coverage required |
| Parity | 542/542 (100%) | Zero tolerance |
| Feature counts | ~512/542 (94.5%) | 30 Pandoc failures OK |

---

## 3. Development Workflow

### 3.1 Setup

```bash
git clone https://github.com/doxstrux/doxstrux.git
cd doxstrux
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3.2 Pre-Commit Checklist

Before committing any changes:

1. **Run pytest:** `.venv/bin/python -m pytest` (must pass)
2. **Check coverage:** Ensure 80% minimum
3. **Run type checking:** `mypy src/doxstrux` (must pass)
4. **Run linting:** `ruff check --fix src/ tests/`
5. **If parser changed:**
   - Run parity: `.venv/bin/python tools/baseline_test_runner.py` (must be 542/542)
   - Run features: `.venv/bin/python tools/test_feature_counts.py`
6. **Update CHANGELOG.md**

### 3.3 Modifying Parser Behavior

If you need to change parser output:

1. Understand the change is intentional and improves correctness
2. Run parity tests — they will fail
3. **Request human approval** to regenerate baselines
4. Regenerate: `.venv/bin/python tools/generate_baseline_outputs.py`
5. Verify new baselines are correct
6. Make baselines read-only: `chmod -R a-w tools/baseline_outputs/`

---

## 4. Common Pitfalls

### 4.1 Using System Python

**Symptom:** Baselines appear to generate successfully but parity tests fail later.

**Cause:** System python lacks `mdit-py-plugins`.

**Fix:** Always use `.venv/bin/python`.

### 4.2 Modifying Baselines Without Approval

**Symptom:** `git status` shows changes in `tools/baseline_outputs/`.

**Cause:** Accidentally edited or regenerated baselines.

**Fix:** `git checkout tools/baseline_outputs/`. Request approval before regenerating.

### 4.3 Introducing Regex in Parser

**Symptom:** Code review flags regex pattern in parser module.

**Cause:** Misunderstanding zero-regex architecture.

**Fix:** Use token-based extraction. Regex only allowed in `security/validators.py`.

### 4.4 Silent Exception Handling

**Symptom:** Test passes but behavior is wrong.

**Cause:** Exception caught and logged instead of raised.

**Fix:** Always re-raise exceptions. No conditional error handling.

```python
# WRONG
except Exception as e:
    logger.warning(f"Ignoring: {e}")
    return default_value

# RIGHT
except Exception as e:
    raise ProcessingError(f"Failed: {e}") from e
```

### 4.5 Non-Deterministic Output

**Symptom:** Same input produces different JSON on different runs.

**Cause:** Unsorted set/dict iteration.

**Fix:** Always sort collections before JSON serialization:

```python
# WRONG
{"items": list(my_set)}

# RIGHT
{"items": sorted(list(my_set))}
```

### 4.6 Wrong Security Profile

**Symptom:** User input bypasses security checks.

**Cause:** Using "permissive" for untrusted input.

**Fix:**
- `strict` — Untrusted user input, scraped content
- `moderate` — Standard trusted documents (default)
- `permissive` — Fully trusted internal documents

---

## 5. Architecture Notes

### 5.1 Zero Regex in Parser

**Why:** Eliminates ReDoS (Regular Expression Denial of Service) vulnerabilities.

**How:** All parsing uses markdown-it-py's token-based AST:

```python
# Instead of regex like r'^#{1,6}\s+(.*)$'
# We use token types:
if token.type == "heading_open":
    level = int(token.tag[1])  # h1 → 1, h2 → 2
```

**Exception:** ~10 regex patterns retained in `security/validators.py` for prompt injection detection and BiDi control character detection. Input is truncated per profile before regex applied.

### 5.2 Modular Extractors

All 11 extractors follow this pattern:

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

### 5.3 No File I/O in Core

- `MarkdownParserCore` accepts content strings only
- `parse_markdown_file()` (in `api.py`) handles file I/O
- Encoding detection handled by `encoding.py`

### 5.4 Fail-Closed Security

- All validation errors raise exceptions
- No "strict mode" toggles for error handling
- Suspicious content blocks embedding via `embedding_blocked` flag

---

## 6. Quick Reference

### 6.1 Essential Commands

```bash
# Parse a file
.venv/bin/python -c "from doxstrux import parse_markdown_file; print(parse_markdown_file('README.md'))"

# Run tests
.venv/bin/python -m pytest

# Run with coverage
.venv/bin/python -m pytest --cov=src/doxstrux

# Parity tests
.venv/bin/python tools/baseline_test_runner.py --test-dir tools/test_mds --baseline-dir tools/baseline_outputs

# Type checking
mypy src/doxstrux

# Linting
ruff check --fix src/ tests/
```

### 6.2 Key Files

| File | Purpose |
|------|---------|
| `src/doxstrux/api.py` | Public entry point |
| `src/doxstrux/markdown_parser_core.py` | Core parser |
| `src/doxstrux/markdown/config.py` | Security profiles (SSOT) |
| `src/doxstrux/markdown/security/validators.py` | Security validation |
| `tools/baseline_test_runner.py` | Parity testing |

### 6.3 Status

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

## 7. Summary

1. **Always `.venv/bin/python`** — System python corrupts silently
2. **Never edit baselines** — Ask human approval first
3. **No silent exceptions** — All errors must raise
4. **No regex in parser** — Token-based only
5. **Test everything** — 80% coverage, 542/542 parity

When in doubt, ask.
