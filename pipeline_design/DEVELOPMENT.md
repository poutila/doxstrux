# Development Guide

Rules for AI assistants and developers working with doxstrux. Every rule exists because violating it caused real problems.

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
```

**Why:** System python lacks `mdit-py-plugins`. Code runs without errors but produces wrong output. Tables, footnotes, and tasklists parse incorrectly. Baselines generated with system python are corrupted.

### 1.2 Immutable Directories (READ-ONLY)

Never edit without human approval:

| Directory | Contents | Why Protected |
|-----------|----------|---------------|
| `tools/baseline_outputs/` | 542 frozen baselines | Ground truth |
| `tools/test_mds/` | 542 test files | Changes invalidate baselines |

**To modify:** Stop. Ask human approval. Explain impact on 542 tests.

### 1.3 Clean Table Principle

No work ships until fully correct:

- No unresolved TODOs or placeholders
- No silent exceptions — all errors raise unconditionally
- No temporary band-aids
- No "check later" deferrals

```python
# FORBIDDEN
except Exception as e:
    if strict:
        raise SpecLoadError(spec_path, e) from e
    errors.append((spec_path, e))  # Swallowed!

# REQUIRED
except Exception as e:
    raise SpecLoadError(spec_path, e) from e
```

### 1.4 No Weak Tests

```python
# WEAK
def test_parser_exists():
    assert hasattr(module, 'MarkdownParserCore')

# STRONG
def test_parser_extracts_headings():
    parser = MarkdownParserCore("# Hello\n## World")
    result = parser.parse()
    assert len(result["structure"]["headings"]) == 2
    assert result["structure"]["headings"][0]["text"] == "Hello"
```

---

## 2. Testing

### 2.1 Test Types

| Type | Command | Pass Criteria |
|------|---------|---------------|
| Unit | `.venv/bin/python -m pytest` | 80% coverage |
| Parity | `.venv/bin/python tools/baseline_test_runner.py` | 542/542 (100%) |
| Features | `.venv/bin/python tools/test_feature_counts.py` | ~512/542 |

### 2.2 Running Tests

```bash
# Unit tests
.venv/bin/python -m pytest

# With coverage
.venv/bin/python -m pytest --cov=src/doxstrux

# Parity tests
.venv/bin/python tools/baseline_test_runner.py \
    --test-dir tools/test_mds \
    --baseline-dir tools/baseline_outputs

# Feature tests
.venv/bin/python tools/test_feature_counts.py
```

### 2.3 Baseline System

**Purpose:** Parser output is byte-for-byte identical across refactoring.

- 542 markdown test files in `tools/test_mds/`
- 542 frozen JSON baselines in `tools/baseline_outputs/`
- Parity test compares current output to baselines
- 100% pass rate required

---

## 3. Workflow

### 3.1 Setup

```bash
git clone https://github.com/doxstrux/doxstrux.git
cd doxstrux
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3.2 Pre-Commit Checklist

1. `.venv/bin/python -m pytest` — must pass
2. Check 80% coverage
3. `mypy src/doxstrux` — must pass
4. `ruff check --fix src/ tests/`
5. If parser changed: run parity (542/542)
6. Update CHANGELOG.md

### 3.3 Modifying Parser Output

1. Confirm change is intentional
2. Run parity tests — they will fail
3. **Request human approval** to regenerate
4. `.venv/bin/python tools/generate_baseline_outputs.py`
5. Verify new baselines
6. `chmod -R a-w tools/baseline_outputs/`

---

## 4. Common Pitfalls

### Using System Python

**Symptom:** Baselines generate but parity fails later.

**Fix:** Always `.venv/bin/python`.

### Modifying Baselines

**Symptom:** `git status` shows `tools/baseline_outputs/` changes.

**Fix:** `git checkout tools/baseline_outputs/`. Get approval first.

### Regex in Parser

**Symptom:** Code review flags regex.

**Fix:** Use token-based extraction. Regex only in `security/validators.py`.

### Silent Exceptions

**Symptom:** Test passes, behavior wrong.

**Fix:** Always re-raise. No conditional handling.

### Non-Deterministic Output

**Symptom:** Same input, different JSON.

**Fix:** Sort collections before serialization.

```python
# WRONG
{"items": list(my_set)}

# RIGHT
{"items": sorted(list(my_set))}
```

---

## 5. Architecture Notes

### Zero Regex in Parser

All parsing uses markdown-it-py tokens. ~10 regex patterns only in `security/validators.py` for injection detection.

```python
# Instead of regex r'^#{1,6}\s+(.*)$'
if token.type == "heading_open":
    level = int(token.tag[1])
```

### Modular Extractors

11 extractors, single responsibility, dependency injection.

### Fail-Closed Security

All validation errors raise. No toggles.

---

## 6. Quick Reference

```bash
# Parse
.venv/bin/python -c "from doxstrux import parse_markdown_file; print(parse_markdown_file('README.md'))"

# Tests
.venv/bin/python -m pytest
.venv/bin/python -m pytest --cov=src/doxstrux

# Parity
.venv/bin/python tools/baseline_test_runner.py

# Type check
mypy src/doxstrux

# Lint
ruff check --fix src/ tests/
```

### Key Files

| File | Purpose |
|------|---------|
| `src/doxstrux/api.py` | Public entry point |
| `src/doxstrux/markdown_parser_core.py` | Core parser |
| `src/doxstrux/markdown/config.py` | Security profiles |
| `tools/baseline_test_runner.py` | Parity testing |

---

## 7. Summary

1. **Always `.venv/bin/python`** — System python corrupts silently
2. **Never edit baselines** — Ask approval first
3. **No silent exceptions** — All errors raise
4. **No regex in parser** — Token-based only
5. **Test everything** — 80% coverage, 542/542 parity
